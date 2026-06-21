from collections.abc import Collection

from nonebot.adapters.onebot.v11 import GroupMessageEvent, MessageEvent

from .models import PermissionResult


def is_group_admin(event: MessageEvent) -> bool:
    return isinstance(event, GroupMessageEvent) and event.sender.role in {
        "admin",
        "owner",
    }


def is_admin(event: MessageEvent, superusers: Collection[str]) -> bool:
    return str(event.user_id) in {
        str(user_id) for user_id in superusers
    } or is_group_admin(event)


def check_query_permission(
    event: MessageEvent,
    target_id: str,
    *,
    only_admin: bool,
    protect_ids: Collection[str],
    superusers: Collection[str],
    bot_self_id: str | None = None,
) -> PermissionResult:
    sender_id = str(event.user_id)
    protected = {str(user_id) for user_id in protect_ids}

    if bot_self_id and target_id == str(bot_self_id):
        return PermissionResult(False, "不能查询机器人自己")

    if target_id in protected and target_id != sender_id:
        return PermissionResult(False, "该用户在保护名单中")

    if only_admin and target_id != sender_id and not is_admin(event, superusers):
        return PermissionResult(False, "当前配置仅允许管理员查询他人")

    return PermissionResult(True)
