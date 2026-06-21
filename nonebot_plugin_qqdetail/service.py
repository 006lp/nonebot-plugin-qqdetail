from typing import Any

from nonebot.adapters.onebot.v11 import Bot

from .models import ProfileData, QueryFailure


async def fetch_profile_data(
    bot: Bot,
    target_id: str,
    group_id: str | None,
) -> ProfileData | QueryFailure:
    try:
        stranger_info = await bot.get_stranger_info(
            user_id=int(target_id),
            no_cache=True,
        )
    except Exception:
        return QueryFailure("无效 QQ 号或资料不可用")

    member_info: dict[str, Any] = {}
    if group_id:
        try:
            member_info = await bot.get_group_member_info(
                group_id=int(group_id),
                user_id=int(target_id),
                no_cache=True,
            )
        except Exception:
            member_info = {}

    return ProfileData(
        target_id=target_id,
        group_id=group_id,
        stranger_info=dict(stranger_info),
        member_info=dict(member_info),
    )
