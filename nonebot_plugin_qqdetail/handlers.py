from arclet.alconna import MultiVar, Option
from nonebot import get_driver, get_plugin_config, logger, on_notice
from nonebot.adapters import Bot as BaseBot
from nonebot.adapters.onebot.v11 import (
    Bot,
    GroupDecreaseNoticeEvent,
    GroupIncreaseNoticeEvent,
    GroupMessageEvent,
    MessageEvent,
    OneBotV11AdapterException,
)
from nonebot_plugin_alconna import AlcMatches, Alconna, Args, UniMessage, on_alconna
from nonebot_plugin_alconna.uniseg import At, AtAll, Target

from .api import ProfileUnavailable, fetch_profile
from .cards import ImageService
from .config import Config
from .delivery import MessageSender, build_messages
from .policy import INVALID_TARGET, protected_ids, query_denial, resolve_targets
from .profile import build_display_lines

config = get_plugin_config(Config)
driver = get_driver()
images = ImageService(config.qqdetail_font_path)
sender = MessageSender()

qqdetail = on_alconna(
    Alconna(
        "qqdetail",
        Args["targets", MultiVar(At | AtAll | str, "*"), ()],
        Option("--text", dest="text"),
        Option("--image", dest="image"),
    ),
    aliases=config.qqdetail_command_aliases,
    use_cmd_start=True,
    priority=5,
    block=True,
)


async def query_and_send(
    bot: Bot,
    destination: Target,
    target_id: str,
    group_id: str | None,
    *,
    output_mode: str | None = None,
    report_errors: bool = True,
) -> None:
    # Contain each target's failures, including error-message send failures.
    try:
        try:
            profile = await fetch_profile(bot, target_id, group_id)
            lines = build_display_lines(
                profile,
                config.qqdetail_display_options,
                desensitize=config.qqdetail_desensitize,
            )
            if not lines:
                raise ProfileUnavailable("未获取到可展示资料")
        except ProfileUnavailable as exc:
            if report_errors:
                await UniMessage.text(f"QQ {target_id}：{exc}").send(
                    target=destination, bot=bot
                )
            return
        mode = output_mode or config.qqdetail_output_mode
        messages = await build_messages(
            target_id, lines, images.render if mode == "image" else None
        )
        await sender.send(
            bot, destination, messages, recall_time=config.qqdetail_recall_time
        )
    except OneBotV11AdapterException as exc:
        logger.warning(f"QQDetail query or send failed ({type(exc).__name__})")


@qqdetail.handle()
async def handle_qqdetail(bot: Bot, event: MessageEvent, result: AlcMatches) -> None:
    if "text" in result.options and "image" in result.options:
        await qqdetail.finish(UniMessage.text("--text 与 --image 不能同时使用"))
    arguments = []
    for argument in result.all_matched_args.get("targets", ()):
        if isinstance(argument, AtAll) or (
            isinstance(argument, At) and argument.flag != "user"
        ):
            await qqdetail.finish(UniMessage.text(INVALID_TARGET))
        arguments.append(argument.target if isinstance(argument, At) else argument)
    try:
        targets = resolve_targets(event.user_id, arguments)
    except ValueError as exc:
        await qqdetail.finish(UniMessage.text(str(exc)))
        return
    group_id = str(event.group_id) if isinstance(event, GroupMessageEvent) else None
    destination = Target(group_id or str(event.user_id), private=group_id is None)
    mode = (
        "text"
        if "text" in result.options
        else "image"
        if "image" in result.options
        else None
    )
    for target_id in targets:
        denial = query_denial(
            str(event.user_id),
            target_id,
            only_admin=config.qqdetail_only_admin,
            protect_ids=config.qqdetail_protect_ids,
            superusers=driver.config.superusers,
            bot_self_id=bot.self_id,
        )
        if denial:
            try:
                await qqdetail.send(UniMessage.text(f"QQ {target_id}：{denial}"))
            except OneBotV11AdapterException as exc:
                logger.warning(f"QQDetail denial send failed ({type(exc).__name__})")
            continue
        await query_and_send(bot, destination, target_id, group_id, output_mode=mode)


def should_query_notice(
    event: GroupIncreaseNoticeEvent | GroupDecreaseNoticeEvent,
    cfg: Config,
    superusers: set[str],
    bot_id: str,
) -> bool:
    enabled = (
        cfg.qqdetail_auto_enter
        if isinstance(event, GroupIncreaseNoticeEvent)
        else cfg.qqdetail_auto_exit and event.sub_type == "leave"
    )
    return (
        enabled
        and (
            not cfg.qqdetail_auto_groups
            or str(event.group_id) in cfg.qqdetail_auto_groups
        )
        and str(event.user_id)
        not in protected_ids(cfg.qqdetail_protect_ids, superusers, bot_id)
    )


async def notice_rule(
    bot: Bot, event: GroupIncreaseNoticeEvent | GroupDecreaseNoticeEvent
) -> bool:
    return should_query_notice(event, config, driver.config.superusers, bot.self_id)


group_notice = on_notice(rule=notice_rule, priority=10, block=False)


@group_notice.handle()
async def handle_notice(
    bot: Bot, event: GroupIncreaseNoticeEvent | GroupDecreaseNoticeEvent
) -> None:
    await query_and_send(
        bot,
        Target(str(event.group_id)),
        str(event.user_id),
        str(event.group_id),
        report_errors=False,
    )


@driver.on_bot_disconnect
async def disconnect(bot: BaseBot) -> None:
    await sender.cancel(bot.self_id)
    if not driver.bots:
        await images.close()


@driver.on_shutdown
async def shutdown() -> None:
    await sender.cancel()
    await images.close()
