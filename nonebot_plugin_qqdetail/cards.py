import asyncio
import hashlib
import time
import unicodedata
from collections import OrderedDict
from io import BytesIO
from logging import getLogger
from pathlib import Path

import emoji
import httpx
from PIL import Image, ImageDraw, ImageFont, ImageOps, UnidentifiedImageError

logger = getLogger(__name__)
RESOURCE_DIR = Path(__file__).parent / "resources"
MAX_AVATAR_BYTES = 2 * 1024 * 1024
WIDTH, PADDING, AVATAR_SIZE, FONT_SIZE, LINE_HEIGHT = 960, 32, 200, 30, 44
TEXT_X = PADDING + AVATAR_SIZE + 28
TEXT_WIDTH = WIDTH - TEXT_X - PADDING
LINES_PER_PAGE = 24
MAX_LINES = 160


class CardRenderer:
    """Synchronous Pillow renderer; callers run it in a worker thread."""

    def __init__(self, font_path: Path | None = None):
        self.font = ImageFont.truetype(
            str(font_path or RESOURCE_DIR / "NotoSansCJKsc-Regular.otf"), FONT_SIZE
        )
        self.emoji_font = ImageFont.truetype(
            str(RESOURCE_DIR / "NotoEmoji.ttf"), FONT_SIZE
        )

    @staticmethod
    def tokens(text: str) -> list[tuple[str, bool]]:
        emojis = {part["match_start"]: part for part in emoji.emoji_list(text)}
        tokens: list[tuple[str, bool]] = []
        index = 0
        while index < len(text):
            if part := emojis.get(index):
                tokens.append((part["emoji"], True))
                index = part["match_end"]
            else:
                char = text[index]
                if unicodedata.combining(char) and tokens:
                    previous, is_emoji = tokens[-1]
                    tokens[-1] = (previous + char, is_emoji)
                else:
                    tokens.append((char, False))
                index += 1
        return tokens

    def wrap(self, lines: list[str]) -> list[list[tuple[str, bool]]]:
        wrapped = []
        for line in lines:
            for paragraph in line.split("\n"):
                current: list[tuple[str, bool]] = []
                width = 0.0
                for token, is_emoji in self.tokens(paragraph):
                    font = self.emoji_font if is_emoji else self.font
                    advance = font.getlength(token)
                    if current and width + advance > TEXT_WIDTH:
                        wrapped.append(current)
                        current, width = [], 0.0
                    current.append((token, is_emoji))
                    width += advance
                wrapped.append(current)
        if len(wrapped) > MAX_LINES:
            wrapped = wrapped[: MAX_LINES - 1]
            wrapped.append(self.tokens("…（资料较长，已截断）"))
        return wrapped

    @staticmethod
    def avatar(data: bytes | None) -> Image.Image:
        if data:
            try:
                with Image.open(BytesIO(data)) as source:
                    if source.width * source.height <= 4_000_000:
                        return ImageOps.fit(
                            source.convert("RGB"), (AVATAR_SIZE, AVATAR_SIZE)
                        )
            except (
                UnidentifiedImageError,
                OSError,
                ValueError,
                Image.DecompressionBombError,
            ):
                pass
        image = Image.new("RGB", (AVATAR_SIZE, AVATAR_SIZE), "#e0e7f0")
        draw = ImageDraw.Draw(image)
        draw.ellipse((66, 38, 134, 106), fill="#94a3b8")
        draw.rounded_rectangle((40, 116, 160, 192), radius=46, fill="#94a3b8")
        return image

    def create(self, avatar: bytes | None, lines: list[str]) -> tuple[bytes, ...]:
        rows = self.wrap(lines)
        pages = [
            rows[start : start + LINES_PER_PAGE]
            for start in range(0, len(rows), LINES_PER_PAGE)
        ] or [[]]
        avatar_image = self.avatar(avatar)
        mask = Image.new("L", (AVATAR_SIZE, AVATAR_SIZE))
        ImageDraw.Draw(mask).rounded_rectangle(
            (0, 0, AVATAR_SIZE, AVATAR_SIZE), radius=24, fill=255
        )
        results = []
        for number, page in enumerate(pages, start=1):
            height = max(AVATAR_SIZE, len(page) * LINE_HEIGHT) + PADDING * 2 + 36
            image = Image.new("RGB", (WIDTH, height), "#f8fafc")
            draw = ImageDraw.Draw(image)
            draw.rounded_rectangle(
                (2, 2, WIDTH - 3, height - 3), radius=24, outline="#94a3b8", width=3
            )
            image.paste(avatar_image, (PADDING, PADDING), mask)
            for row, tokens in enumerate(page):
                x = float(TEXT_X)
                for token, is_emoji in tokens:
                    font = self.emoji_font if is_emoji else self.font
                    draw.text(
                        (x, PADDING + row * LINE_HEIGHT),
                        token,
                        font=font,
                        fill="#1e293b",
                    )
                    x += font.getlength(token)
            draw.text(
                (TEXT_X, height - 50),
                f"QQDetail · {number}/{len(pages)}",
                font=self.font,
                fill="#64748b",
            )
            with BytesIO() as output:
                image.save(output, format="PNG")
                results.append(output.getvalue())
        return tuple(results)


class ImageService:
    """Lazy HTTP client and a bounded, content-sensitive card cache."""

    def __init__(self, font_path: Path | None = None):
        self.font_path = font_path
        self._client: httpx.AsyncClient | None = None
        self._cache: OrderedDict[str, tuple[float, tuple[bytes, ...]]] = OrderedDict()
        self._generation = 0

    async def _get_avatar(self, target_id: str) -> bytes | None:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=5, follow_redirects=True, max_redirects=3
            )
        try:
            url = f"https://q4.qlogo.cn/headimg_dl?dst_uin={target_id}&spec=640"
            async with self._client.stream("GET", url) as response:
                response.raise_for_status()
                data = bytearray()
                async for chunk in response.aiter_bytes():
                    data.extend(chunk)
                    if len(data) > MAX_AVATAR_BYTES:
                        return None
                return bytes(data)
        except httpx.HTTPError as exc:
            logger.warning(f"QQDetail avatar download failed ({type(exc).__name__})")
            return None

    async def render(self, target_id: str, lines: list[str]) -> tuple[bytes, ...]:
        generation = self._generation
        avatar = await self._get_avatar(target_id)
        digest = hashlib.sha256()
        for line in lines:
            digest.update(line.encode("utf-8"))
            digest.update(b"\0")
        digest.update(avatar or b"")
        # Include font modification metadata so replacing a custom font invalidates cards.
        if self.font_path:
            stat = self.font_path.stat()
            digest.update(f"{stat.st_mtime_ns}:{stat.st_size}".encode())
        key = digest.hexdigest()
        now = time.monotonic()
        for expired in [
            k for k, (created, _) in self._cache.items() if now - created >= 300
        ]:
            del self._cache[expired]
        if cached := self._cache.get(key):
            self._cache.move_to_end(key)
            return cached[1]
        images = await asyncio.to_thread(
            lambda: CardRenderer(self.font_path).create(avatar, lines)
        )
        if generation == self._generation:
            self._cache[key] = (time.monotonic(), images)
            self._cache.move_to_end(key)
            while len(self._cache) > 32:
                self._cache.popitem(last=False)
        return images

    async def close(self) -> None:
        self._generation += 1
        self._cache.clear()
        client, self._client = self._client, None
        if client:
            await client.aclose()
