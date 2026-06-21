from collections.abc import Iterable
from typing import Any

from .models import TargetResolution


def extract_at_ids(message: Iterable[Any]) -> list[str]:
    ids: list[str] = []
    for segment in message:
        if getattr(segment, "type", "") != "at":
            continue
        data = getattr(segment, "data", {})
        qq = str(data.get("qq", "")).strip()
        if qq.isdigit() and qq not in ids:
            ids.append(qq)
    return ids


def parse_qq_argument(argument: str | None) -> TargetResolution:
    if argument is None or argument.strip() == "":
        return TargetResolution(target_id=None)

    value = argument.strip()
    if value.startswith("@"):
        value = value[1:].strip()

    if not value.isdigit():
        return TargetResolution(target_id=None, error="目标 QQ 号必须是纯数字")

    return TargetResolution(target_id=value)


def resolve_target(
    sender_id: int | str,
    message: Iterable[Any],
    argument: str | None,
) -> TargetResolution:
    at_ids = extract_at_ids(message)
    if at_ids:
        return TargetResolution(target_id=at_ids[0])

    parsed = parse_qq_argument(argument)
    if parsed.error:
        return parsed

    return TargetResolution(target_id=parsed.target_id or str(sender_id))
