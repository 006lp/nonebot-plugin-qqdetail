from collections.abc import Collection, Iterable

INVALID_TARGET = "目标 QQ 号必须是正整数，不能使用 @全体成员"


def normalize_id(value: object) -> str:
    text = str(value).strip()
    if not text.isascii() or not text.isdigit() or int(text) <= 0:
        raise ValueError("IDs must be positive numeric values")
    return str(int(text))


def resolve_targets(sender_id: int | str, arguments: Iterable[str]) -> list[str]:
    """Validate parsed targets and retain their order."""
    try:
        targets = dict.fromkeys(
            normalize_id(argument.strip().removeprefix("@")) for argument in arguments
        )
    except ValueError as exc:
        raise ValueError(INVALID_TARGET) from exc
    return list(targets) or [str(sender_id)]


def superuser_ids(superusers: Collection[str]) -> set[str]:
    return {str(uid).removeprefix("onebot:") for uid in superusers}


def protected_ids(
    protect_ids: Collection[str], superusers: Collection[str], bot_self_id: str
) -> set[str]:
    return set(protect_ids) | superuser_ids(superusers) | {bot_self_id}


def query_denial(
    sender_id: str,
    target_id: str,
    *,
    only_admin: bool,
    protect_ids: Collection[str],
    superusers: Collection[str],
    bot_self_id: str,
) -> str | None:
    """Return a denial reason; group roles do not grant query privileges."""
    if target_id == bot_self_id:
        return "不能查询机器人自己"
    if target_id == sender_id:
        return None
    admins = superuser_ids(superusers)
    if target_id in protect_ids or target_id in admins:
        return "该用户在保护名单中"
    if only_admin and sender_id not in admins:
        return "当前配置仅允许 SUPERUSERS 查询他人"
    return None
