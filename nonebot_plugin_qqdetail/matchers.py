import math
from datetime import datetime, timedelta
from typing import Dict, Optional

from nonebot import get_plugin_config, logger, on_command, on_notice
from nonebot.adapters.onebot.v11 import (
    Bot,
    GroupIncreaseNoticeEvent,
    GroupDecreaseNoticeEvent,
    MessageSegment,
    Message,
)
from nonebot.matcher import Matcher
from nonebot.params import ArgPlainText, CommandArg
from nonebot.permission import SUPERUSER
from nonebot.rule import to_me

from .config import Config
from .utils import ProfileProcessor

# 获取插件配置
plugin_config = get_plugin_config(Config)

# 创建数据处理器实例
processor = ProfileProcessor(plugin_config)

# 存储用户最后一次使用命令的时间
last_command_time: Dict[str, datetime] = {}


def check_rate_limit(user_id: str, group_id: Optional[str]) -> Optional[str]:
    """检查速率限制"""
    rate_config = plugin_config.qqdetail_rate_limit_config
    
    # 如果速率为0，表示不限制
    if rate_config.time <= 0:
        return None
    
    # 检查用户是否在白名单中
    if user_id in rate_config.white_users:
        return None
    
    # 检查群聊是否在白名单中
    if group_id and group_id in rate_config.white_groups:
        return None
    
    # 检查速率限制
    user_key = f"{user_id}_{group_id or 'private'}"
    current_time = datetime.now()
    
    if user_key in last_command_time:
        last_time = last_command_time[user_key]
        time_diff = current_time - last_time
        
        if time_diff < timedelta(minutes=rate_config.time):
            remaining_minutes = rate_config.time - time_diff.total_seconds() / 60
            return f"请求过于频繁，请等待 {math.ceil(remaining_minutes)} 分钟后再试。"
    
    # 更新最后使用时间
    last_command_time[user_key] = current_time
    return None


# box 命令
box_cmd = on_command(
    "detail",
    aliases={"detail", "查询资料"},
    priority=5,
    block=True,
)


@box_cmd.handle()
async def handle_box(
    bot: Bot,
    event,
    matcher: Matcher,
    args: Message = CommandArg(),
):
    """处理 box 命令"""
    # 获取事件信息
    user_id = str(event.user_id)
    group_id = str(event.group_id) if hasattr(event, "group_id") else None
    self_id = str(event.self_id)
    
    # 检查群聊白名单
    if group_id and plugin_config.qqdetail_whitelist_groups:
        if group_id not in plugin_config.qqdetail_whitelist_groups:
            await matcher.finish(f"当前群聊(ID: {group_id})不在白名单中，请联系管理员添加。")
    
    # 检查速率限制
    rate_limit_msg = check_rate_limit(user_id, group_id)
    if rate_limit_msg:
        await matcher.finish(rate_limit_msg)
    
    # 解析目标用户
    target_id = None
    arg_text = args.extract_plain_text().strip()
    
    # 检查是否有 at
    for seg in args:
        if seg.type == "at":
            at_id = seg.data.get("qq")
            if at_id and at_id != self_id:
                target_id = str(at_id)
                break
    
    # 如果没有 at，尝试从参数中获取 QQ 号
    if not target_id and arg_text:
        if arg_text.isdigit():
            target_id = arg_text
    
    # 如果还是没有，默认查询自己
    if not target_id:
        target_id = user_id
    
    # 如果指定了其他人且仅管理员可用
    if plugin_config.qqdetail_only_admin and target_id != user_id:
        # 检查是否为超级用户
        is_superuser = await SUPERUSER(bot, event)
        if not is_superuser:
            # 检查是否为群管理员
            if group_id:
                try:
                    member_info = await bot.get_group_member_info(
                        group_id=int(group_id),
                        user_id=int(user_id)
                    )
                    if member_info.get("role") not in ["admin", "owner"]:
                        await matcher.finish(f"您(ID: {user_id})的权限不足以使用此指令。")
                except Exception as e:
                    logger.warning(f"检查管理员权限失败: {e}")
                    await matcher.finish("权限检查失败")
            else:
                await matcher.finish(f"您(ID: {user_id})的权限不足以使用此指令。")
    
    # 检查黑名单
    if target_id in plugin_config.qqdetail_box_blacklist:
        logger.info(f"[QQDetail] 调取目标 {target_id} 处于黑名单，拒绝资料调用请求。")
        await matcher.finish("资料调用请求被拒绝。")

    # 获取资料并生成图片
    image_bytes = None
    try:
        image_bytes = await processor.get_profile_image(bot, target_id, group_id)
    except ValueError as e:
        await matcher.finish(str(e))
    except Exception as e:
        logger.error(f"[QQDetail] 获取用户资料失败: {e}")
        await matcher.finish("获取用户资料失败，请稍后重试。")

    if image_bytes:
        await matcher.finish(MessageSegment.image(image_bytes))


# 入群通知处理
increase_notice = on_notice(priority=5, block=False)


@increase_notice.handle()
async def handle_increase(bot: Bot, event: GroupIncreaseNoticeEvent):
    """处理入群通知"""
    auto_config = plugin_config.qqdetail_auto_box_config
    
    # 检查是否启用自动获取
    if not auto_config.increase_box:
        return
    
    # 检查群聊白名单
    group_id = str(event.group_id)
    if auto_config.white_groups and group_id not in auto_config.white_groups:
        return
    
    # 检查是否为机器人自己
    if event.user_id == event.self_id:
        return
    
    target_id = str(event.user_id)
    
    # 检查黑名单
    if target_id in plugin_config.qqdetail_box_blacklist:
        logger.info(f"[QQDetail] 自动调取目标 {target_id} 处于黑名单，取消资料调用请求。")
        return
    
    try:
        image_bytes = await processor.get_profile_image(bot, target_id, group_id)
        await bot.send_group_msg(
            group_id=int(group_id),
            message=Message([MessageSegment.image(image_bytes)])
        )
    except Exception as e:
        logger.error(f"[QQDetail] 自动获取入群用户资料失败: {e}")


# 退群通知处理
decrease_notice = on_notice(priority=5, block=False)


@decrease_notice.handle()
async def handle_decrease(bot: Bot, event: GroupDecreaseNoticeEvent):
    """处理退群通知"""
    auto_config = plugin_config.qqdetail_auto_box_config
    
    # 检查是否启用自动获取
    if not auto_config.decrease_box:
        return
    
    # 只处理主动退群
    if event.sub_type != "leave":
        return
    
    # 检查群聊白名单
    group_id = str(event.group_id)
    if auto_config.white_groups and group_id not in auto_config.white_groups:
        return
    
    # 检查是否为机器人自己
    if event.user_id == event.self_id:
        return
    
    target_id = str(event.user_id)
    
    # 检查黑名单
    if target_id in plugin_config.qqdetail_box_blacklist:
        logger.info(f"[QQDetail] 自动调取目标 {target_id} 处于黑名单，取消资料调用请求。")
        return
    
    try:
        image_bytes = await processor.get_profile_image(bot, target_id, group_id)
        await bot.send_group_msg(
            group_id=int(group_id),
            message=Message([MessageSegment.image(image_bytes)])
        )
    except Exception as e:
        logger.error(f"[QQDetail] 自动获取退群用户资料失败: {e}")