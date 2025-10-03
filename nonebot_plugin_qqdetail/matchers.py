from typing import Optional

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
from .services import QQDetailService, RateLimitService, PermissionService
from .utils import ProfileProcessor

# 获取插件配置
plugin_config = get_plugin_config(Config)

# 创建服务实例
processor = ProfileProcessor(plugin_config)
rate_limit_service = RateLimitService()
qqdetail_service = QQDetailService(plugin_config)


# 移除旧的 check_rate_limit 函数，已移至 RateLimitService


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
    
    # 检查速率限制
    rate_limit_msg = rate_limit_service.check_rate_limit(user_id, group_id, plugin_config)
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

    # 检查黑名单
    if qqdetail_service.is_in_blacklist(target_id):
        logger.info(f"[QQDetail] 调取目标 {target_id} 处于黑名单，拒绝资料调用请求。")
        await matcher.finish("资料调用请求被拒绝。")

    # 检查群聊白名单
    if group_id and not qqdetail_service.is_group_whitelisted(group_id):
        await matcher.finish(f"当前群聊(ID: {group_id})不在白名单中，请联系管理员添加。")

    # 检查权限
    if plugin_config.qqdetail_only_admin and target_id != user_id:
        is_superuser = await SUPERUSER(bot, event)
        permission_msg = await PermissionService.check_admin_permission(
            bot, user_id, group_id, plugin_config.qqdetail_only_admin, target_id, is_superuser
        )
        if permission_msg:
            await matcher.finish(permission_msg)

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
    group_id = str(event.group_id)
    target_id = str(event.user_id)

    # 检查是否为机器人自己
    if event.user_id == event.self_id:
        return

    # 检查是否应该自动获取
    if not qqdetail_service.should_auto_box_increase(group_id):
        return

    # 检查黑名单
    if qqdetail_service.is_in_blacklist(target_id):
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
    # 只处理主动退群
    if event.sub_type != "leave":
        return

    group_id = str(event.group_id)
    target_id = str(event.user_id)

    # 检查是否为机器人自己
    if event.user_id == event.self_id:
        return

    # 检查是否应该自动获取
    if not qqdetail_service.should_auto_box_decrease(group_id):
        return

    # 检查黑名单
    if qqdetail_service.is_in_blacklist(target_id):
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