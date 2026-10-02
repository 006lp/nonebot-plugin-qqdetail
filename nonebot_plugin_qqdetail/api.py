import asyncio
from collections.abc import Mapping
from typing import Any

from nonebot import logger
from nonebot.adapters.onebot.v11 import Bot

from .profile import ProfileData


class ProfileUnavailable(Exception):
    """The profile contains no usable or selected display fields."""


async def _fetch(bot: Bot, api: str, **params: Any) -> dict[str, Any]:
    try:
        result = await asyncio.wait_for(bot.call_api(api, **params), timeout=15)
        return dict(result) if isinstance(result, Mapping) else {}
    except Exception as exc:
        # API exception bodies may include personal data.
        logger.warning(f"QQDetail {api} failed ({type(exc).__name__})")
        return {}


async def fetch_profile(bot: Bot, target_id: str, group_id: str | None) -> ProfileData:
    stranger = await _fetch(
        bot, "get_stranger_info", user_id=int(target_id), no_cache=True
    )
    member = (
        await _fetch(
            bot,
            "get_group_member_info",
            group_id=int(group_id),
            user_id=int(target_id),
            no_cache=True,
        )
        if group_id
        else {}
    )
    if not any(
        key != "user_id" and value not in (None, "", "unknown")
        for source in (stranger, member)
        for key, value in source.items()
    ):
        raise ProfileUnavailable("无效 QQ 号或资料不可用")
    return ProfileData(target_id, stranger, member)
