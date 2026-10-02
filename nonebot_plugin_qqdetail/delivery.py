import asyncio
from collections.abc import Awaitable, Callable, Sequence

from nonebot import logger
from nonebot.adapters.onebot.v11 import Bot
from nonebot_plugin_alconna import UniMessage
from nonebot_plugin_alconna.uniseg import Receipt, Target


async def build_messages(
    target_id: str,
    lines: list[str],
    render: Callable[[str, list[str]], Awaitable[tuple[bytes, ...]]] | None = None,
) -> list[UniMessage]:
    """Build text or cards without depending on the plugin's runtime objects."""
    if render:
        try:
            return [
                UniMessage.image(raw=page, mimetype="image/png")
                for page in await render(target_id, lines)
            ]
        except Exception as exc:
            logger.warning(
                f"QQDetail card rendering failed ({type(exc).__name__}); using text"
            )
    text = "\n".join(lines)
    return [
        UniMessage.text(text[start : start + 3000])
        for start in range(0, len(text), 3000)
    ]


class MessageSender:
    """Send prepared messages and manage their recall tasks."""

    def __init__(self):
        self.tasks: dict[asyncio.Task[None], str] = {}

    async def send(
        self,
        bot: Bot,
        destination: Target,
        messages: Sequence[UniMessage],
        *,
        recall_time: int,
    ) -> None:
        for message in messages:
            receipt = await message.send(target=destination, bot=bot)
            if recall_time and receipt.msg_ids:
                task = asyncio.create_task(self._recall(receipt, recall_time))
                self.tasks[task] = bot.self_id
                task.add_done_callback(self.tasks.pop)

    @staticmethod
    async def _recall(receipt: Receipt, delay: int) -> None:
        try:
            await asyncio.sleep(delay)
            await receipt.recall()
        except Exception as exc:
            logger.warning(f"QQDetail recall failed ({type(exc).__name__})")

    async def cancel(self, bot_id: str | None = None) -> None:
        tasks = [
            task
            for task, owner in self.tasks.items()
            if bot_id is None or owner == bot_id
        ]
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
