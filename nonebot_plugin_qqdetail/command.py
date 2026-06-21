from nonebot import get_driver
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, MessageEvent
from nonebot.plugin import get_plugin_config
from nonebot_plugin_alconna import Alconna, AlconnaMatch, Args, Match, on_alconna

from .config import Config
from .models import QueryFailure
from .permissions import check_query_permission
from .service import fetch_profile_data
from .targeting import resolve_target
from .transform import build_display_lines

plugin_config = get_plugin_config(Config)

qqdetail = on_alconna(
    Alconna("qqdetail", Args["target?", str]),
    aliases=plugin_config.qqdetail_command_aliases,
    use_cmd_start=True,
    priority=5,
    block=True,
)


@qqdetail.handle()
async def handle_qqdetail(
    bot: Bot,
    event: MessageEvent,
    target: Match[str] = AlconnaMatch("target"),
) -> None:
    argument = target.result if target.available else None
    resolved = resolve_target(event.user_id, event.get_message(), argument)
    if not resolved.ok:
        await qqdetail.finish(resolved.error)
        return

    target_id = resolved.target_id
    if target_id is None:
        await qqdetail.finish("无法解析查询目标")
        return

    permission = check_query_permission(
        event,
        target_id,
        only_admin=plugin_config.qqdetail_only_admin,
        protect_ids=plugin_config.qqdetail_protect_ids,
        superusers=get_driver().config.superusers,
        bot_self_id=bot.self_id,
    )
    if not permission.allowed:
        await qqdetail.finish(permission.message)
        return

    group_id = str(event.group_id) if isinstance(event, GroupMessageEvent) else None
    profile = await fetch_profile_data(bot, target_id, group_id)
    if isinstance(profile, QueryFailure):
        await qqdetail.finish(profile.message)
        return

    lines = build_display_lines(profile, plugin_config.qqdetail_display_options)
    if not lines:
        await qqdetail.finish("未获取到可展示资料")
        return

    await qqdetail.finish("\n".join(lines))
