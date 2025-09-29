import io
import random
from pathlib import Path
from typing import Optional

from nonebot import logger
from PIL import Image, ImageDraw
import PIL.ImageFont as ImageFont
from PIL.ImageFont import FreeTypeFont
from typing import Union
from io import BytesIO

try:
    import emoji
    EMOJI_AVAILABLE = True
except ImportError:
    emoji = None
    EMOJI_AVAILABLE = False
    logger.warning("[QQDetail] emoji 库未安装，将无法正确处理 Emoji")

# 资源目录
RESOURCE_DIR: Path = Path(__file__).resolve().parent / "assets"
FONT_PATH: Path = RESOURCE_DIR / "可爱字体.ttf"
EMOJI_FONT_PATH: Path = RESOURCE_DIR / "NotoColorEmoji.ttf"

# 样式配置
FONT_SIZE = 35  # 字体大小
TEXT_PADDING = 10  # 文本与边框的间距
AVATAR_SIZE = None  # 头像大小（None 表示与文本高度一致）
BORDER_THICKNESS = 10  # 边框厚度
BORDER_COLOR = (38, 38, 38)  # 边框颜色 #262626
CORNER_RADIUS = 30  # 圆角大小

# 加载字体
def load_font(font_path: Path, size: int) -> Union[ImageFont.ImageFont, FreeTypeFont]:
    """加载字体，如果失败则使用默认字体"""
    try:
        return ImageFont.truetype(str(font_path), size)
    except Exception as e:
        logger.warning(f"[QQDetail] 无法加载字体 {font_path}: {e}，使用默认字体")
        return ImageFont.load_default()

# 确保资源目录存在
RESOURCE_DIR.mkdir(parents=True, exist_ok=True)

# 加载主字体
if FONT_PATH.exists():
    cute_font = load_font(FONT_PATH, FONT_SIZE)
    logger.debug(f"[QQDetail] 主字体加载: {FONT_PATH}")
else:
    logger.warning(f"[QQDetail] 字体文件不存在: {FONT_PATH}，使用默认字体")
    cute_font = ImageFont.load_default()

# 加载 Emoji 字体
emoji_font = None
if EMOJI_FONT_PATH.exists():
    emoji_font = load_font(EMOJI_FONT_PATH, FONT_SIZE)
    logger.debug(f"[QQDetail] Emoji 字体加载: {EMOJI_FONT_PATH}")
else:
    logger.warning(f"[QQDetail] Emoji 字体文件不存在: {EMOJI_FONT_PATH}")


def create_image(avatar: bytes, reply: list) -> bytes:
    """创建用户资料图片"""
    reply_str = "\n".join(reply)
    
    # 创建临时图片计算文本的宽高
    temp_img = Image.new("RGBA", (1, 1))
    temp_draw = ImageDraw.Draw(temp_img)
    
    # 将 Emoji 替换为中文字符以计算宽度
    if EMOJI_AVAILABLE:
        no_emoji_reply = "".join("一" if emoji.is_emoji(c) else c for c in reply_str)  # type: ignore[union-attr]
    else:
        no_emoji_reply = reply_str
    
    # 计算每行文本的高度
    lines = no_emoji_reply.split("\n")
    line_heights = []
    for line in lines:
        if line.strip():
            try:
                line_bbox = temp_draw.textbbox((0, 0), line, font=cute_font)
                line_height = int(line_bbox[3] - line_bbox[1])
                line_heights.append(line_height)
            except:
                line_heights.append(FONT_SIZE + 5)
        else:
            line_heights.append(FONT_SIZE + 5)
    
    # 计算整体文本高度
    text_height = sum(line_heights) + (len(lines) - 1) * 5
    text_height += TEXT_PADDING  # 底部额外边距
    
    # 计算最大文本宽度
    max_line_width = 0
    for line in lines:
        if line.strip():
            try:
                line_bbox = temp_draw.textbbox((0, 0), line, font=cute_font)
                line_width = int(line_bbox[2] - line_bbox[0])
                max_line_width = max(max_line_width, line_width + 15)
            except:
                max_line_width = max(max_line_width, len(line) * FONT_SIZE + 15)
    
    text_width = max_line_width
    img_height = text_height + 2 * TEXT_PADDING
    
    # 调整头像大小
    avatar_img = Image.open(BytesIO(avatar))
    avatar_size = AVATAR_SIZE if AVATAR_SIZE else text_height
    avatar_img = avatar_img.resize((avatar_size, avatar_size))
    img_width = avatar_img.width + text_width + 2 * TEXT_PADDING
    
    # 创建主图
    img = Image.new("RGBA", (img_width, img_height), color=(255, 255, 255, 255))
    img.paste(avatar_img, (0, (img_height - avatar_size) // 2))
    
    # 绘制文本
    _draw_multi(img, reply_str, avatar_img.width + TEXT_PADDING, TEXT_PADDING)
    
    # 添加边框
    border_img = Image.new(
        mode="RGBA",
        size=(img_width + BORDER_THICKNESS * 2, img_height + BORDER_THICKNESS * 2),
        color=BORDER_COLOR,
    )
    border_img.paste(img, (BORDER_THICKNESS, BORDER_THICKNESS))
    
    # 转换为字节
    img_byte_arr = io.BytesIO()
    border_img.save(img_byte_arr, format="PNG")
    return img_byte_arr.getvalue()


def _draw_multi(img: Image.Image, text: str, text_x: int = 10, text_y: int = 10):
    """在图片上绘制多语言文本"""
    lines = text.split("\n")
    current_y = text_y
    draw = ImageDraw.Draw(img)
    
    for line in lines:
        line_color = (
            random.randint(0, 128),
            random.randint(0, 128),
            random.randint(0, 128),
            random.randint(240, 255),
        )
        current_x = text_x
        
        # 跳过空行
        if not line.strip():
            current_y += FONT_SIZE + 5
            continue
        
        # 计算当前行的实际高度
        if EMOJI_AVAILABLE:
            no_emoji_line = "".join("一" if emoji.is_emoji(c) else c for c in line)  # type: ignore[union-attr]
        else:
            no_emoji_line = line
        
        try:
            bbox = cute_font.getbbox(no_emoji_line)
            line_height = int(bbox[3] - bbox[1]) if bbox else FONT_SIZE
            
            for char in line:
                # 判断是否为 Emoji
                is_emoji_char = EMOJI_AVAILABLE and char in emoji.EMOJI_DATA  # type: ignore[union-attr]
                
                if is_emoji_char and emoji_font:
                    draw.text((current_x, current_y), char, font=emoji_font, fill=line_color)
                    char_bbox = cute_font.getbbox("中")
                else:
                    draw.text((current_x, current_y), char, font=cute_font, fill=line_color)
                    char_bbox = cute_font.getbbox(char)
                
                # 计算字符宽度
                char_width = char_bbox[2] - char_bbox[0] if char_bbox else FONT_SIZE // 2
                
                # 检查是否超出边界
                if current_x + char_width > img.width - TEXT_PADDING:
                    current_x = text_x
                    current_y += max(line_height, FONT_SIZE) + 5
                    
                    # 重新绘制当前字符
                    if is_emoji_char and emoji_font:
                        draw.text((current_x, current_y), char, font=emoji_font, fill=line_color)
                    else:
                        draw.text((current_x, current_y), char, font=cute_font, fill=line_color)
                
                current_x += char_width
            
            # 移动到下一行
            next_y = current_y + max(line_height, FONT_SIZE) + 5
            if next_y > img.height - TEXT_PADDING:
                current_y = img.height - TEXT_PADDING - max(line_height, FONT_SIZE)
            else:
                current_y = next_y
        except Exception as e:
            logger.error(f"[QQDetail] 绘制文本时出错: {e}")
            current_y += FONT_SIZE + 5
    
    return img