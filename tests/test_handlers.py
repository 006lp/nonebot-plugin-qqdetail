import pytest
from nonebot.adapters.onebot.v11 import (
    GroupDecreaseNoticeEvent,
    GroupIncreaseNoticeEvent,
    Message,
    MessageSegment,
)


@pytest.mark.parametrize(
    "command", ["/qqdetail", "/qq资料", "/查qq", "/查q", "/box", "/盒", "/开盒"]
)
async def test_self_query_aliases(
    app, message_event, command, onebot, expect_query, expect_message
):
    from nonebot_plugin_qqdetail.handlers import qqdetail

    async with app.test_matcher(qqdetail) as ctx:
        ctx.receive_event(onebot(ctx), message_event(command))
        ctx.should_pass_rule(qqdetail)
        expect_query(ctx)
        expect_message(ctx, "QQ号：20000\n昵称：测试")


async def test_mixed_targets_deduplicate_and_continue_after_denial(
    app, message_event, onebot, expect_query, expect_message
):
    from nonebot_plugin_qqdetail.handlers import qqdetail

    event = message_event(
        Message("/qqdetail 10000 ") + MessageSegment.at(40000) + " 40000 @50000 --text"
    )
    async with app.test_matcher(qqdetail) as ctx:
        ctx.receive_event(onebot(ctx), event)
        ctx.should_pass_rule(qqdetail)
        ctx.should_call_send(event, Message("QQ 10000：该用户在保护名单中"))
        for target in (40000, 50000):
            expect_query(ctx, target)
            expect_message(ctx, f"QQ号：{target}\n昵称：测试")


async def test_actual_at_without_space(
    app, message_event, onebot, expect_query, expect_message
):
    from nonebot_plugin_qqdetail.handlers import qqdetail

    async with app.test_matcher(qqdetail) as ctx:
        ctx.receive_event(
            onebot(ctx), message_event(Message("/box") + MessageSegment.at(40000))
        )
        ctx.should_pass_rule(qqdetail)
        expect_query(ctx, 40000)
        expect_message(ctx, "QQ号：40000\n昵称：测试")


@pytest.mark.parametrize(
    ("command", "error"),
    [
        ("/qqdetail @all", "目标 QQ 号必须是正整数，不能使用 @全体成员"),
        ("/qqdetail abc", "目标 QQ 号必须是正整数，不能使用 @全体成员"),
        ("/qqdetail --image --text", "--text 与 --image 不能同时使用"),
        (
            Message("/qqdetail ") + MessageSegment.at("all"),
            "目标 QQ 号必须是正整数，不能使用 @全体成员",
        ),
    ],
)
async def test_invalid_command_has_no_query(app, message_event, command, error, onebot):
    from nonebot_plugin_qqdetail.handlers import qqdetail

    event = message_event(command)
    async with app.test_matcher(qqdetail) as ctx:
        ctx.receive_event(onebot(ctx), event)
        ctx.should_pass_rule(qqdetail)
        ctx.should_call_send(event, Message(error))
        ctx.should_finished(qqdetail)


async def test_private_query(app, message_event, onebot, expect_query, expect_message):
    from nonebot_plugin_qqdetail.handlers import qqdetail

    async with app.test_matcher(qqdetail) as ctx:
        ctx.receive_event(onebot(ctx), message_event("/qqdetail --text", group_id=None))
        ctx.should_pass_rule(qqdetail)
        expect_query(ctx, group_id=None)
        expect_message(ctx, "QQ号：20000\n昵称：测试", group_id=None)


@pytest.mark.parametrize("error_send_fails", [False, True])
async def test_failed_target_does_not_abort_batch(
    app, message_event, onebot, error_send_fails, expect_query, expect_message
):
    from nonebot_plugin_qqdetail.handlers import qqdetail

    async with app.test_matcher(qqdetail) as ctx:
        ctx.receive_event(onebot(ctx), message_event("/qqdetail 40000 50000 --text"))
        ctx.should_pass_rule(qqdetail)
        expect_query(ctx, 40000, stranger=RuntimeError())
        expect_message(
            ctx,
            "QQ 40000：无效 QQ 号或资料不可用",
            exception=RuntimeError() if error_send_fails else None,
        )
        expect_query(ctx, 50000)
        expect_message(ctx, "QQ号：50000\n昵称：测试")


@pytest.mark.parametrize(
    ("command", "role", "only_admin", "error"),
    [
        ("/qqdetail 99999", "member", False, "QQ 99999：不能查询机器人自己"),
        (
            "/qqdetail 40000",
            "owner",
            True,
            "QQ 40000：当前配置仅允许 SUPERUSERS 查询他人",
        ),
    ],
)
async def test_denied_target_does_not_query_self(
    app, message_event, onebot, settings, command, role, only_admin, error
):
    from nonebot_plugin_qqdetail.handlers import qqdetail

    settings(qqdetail_only_admin=only_admin)
    event = message_event(command, role=role)
    async with app.test_matcher(qqdetail) as ctx:
        ctx.receive_event(onebot(ctx), event)
        ctx.should_pass_rule(qqdetail)
        ctx.should_call_send(event, Message(error))


def test_alconna_keeps_target_order_and_options():
    from nonebot_plugin_alconna import UniMessage
    from nonebot_plugin_alconna.uniseg import At

    from nonebot_plugin_qqdetail.handlers import qqdetail

    result = qqdetail.command().parse(
        UniMessage.text("/qqdetail 20000 ") + At("user", "30000") + " @40000 --text"
    )
    assert result.matched
    assert result.all_matched_args["targets"] == (
        "20000",
        At("user", "30000"),
        "@40000",
    )
    assert "text" in result.options


def notice(kind, user_id=20000, group_id=30000):
    cls = GroupIncreaseNoticeEvent if kind == "enter" else GroupDecreaseNoticeEvent
    return cls(
        time=1,
        self_id=99999,
        post_type="notice",
        group_id=group_id,
        user_id=user_id,
        operator_id=40000,
        notice_type="group_increase" if kind == "enter" else "group_decrease",
        sub_type="approve" if kind == "enter" else kind,
    )


@pytest.mark.parametrize(
    ("kind", "uid", "gid", "groups", "enter", "exit", "expected"),
    [
        ("enter", 20000, 30000, set(), False, False, False),
        ("enter", 20000, 30000, set(), True, False, True),
        ("leave", 20000, 30000, set(), False, True, True),
        ("kick", 20000, 30000, set(), False, True, False),
        ("kick_me", 99999, 30000, set(), False, True, False),
        ("enter", 10000, 30000, set(), True, False, False),
        ("enter", 50000, 30000, set(), True, False, False),
        ("enter", 20000, 30000, {"40000"}, True, False, False),
        ("enter", 20000, 30000, {"30000"}, True, False, True),
    ],
)
def test_notice_filters(kind, uid, gid, groups, enter, exit, expected):
    from nonebot_plugin_qqdetail.config import Config
    from nonebot_plugin_qqdetail.handlers import should_query_notice

    cfg = Config(
        qqdetail_auto_enter=enter,
        qqdetail_auto_exit=exit,
        qqdetail_auto_groups=groups,
        qqdetail_protect_ids={"50000"},
    )
    assert (
        should_query_notice(notice(kind, uid, gid), cfg, {"10000"}, "99999") is expected
    )


@pytest.mark.parametrize("kind", ["enter", "leave"])
async def test_notice_pipeline_with_missing_group_data(
    app, settings, kind, onebot, expect_query, expect_message
):
    from nonebot_plugin_qqdetail.handlers import group_notice

    settings(qqdetail_auto_enter=True, qqdetail_auto_exit=True)
    async with app.test_matcher(group_notice) as ctx:
        ctx.receive_event(onebot(ctx), notice(kind))
        ctx.should_pass_rule(group_notice)
        expect_query(ctx, member=RuntimeError())
        expect_message(ctx, "QQ号：20000\n昵称：测试")
    assert not group_notice.block


async def test_disabled_notice_makes_no_api_call(app, onebot):
    from nonebot_plugin_qqdetail.handlers import group_notice

    async with app.test_matcher(group_notice) as ctx:
        bot = onebot(ctx)
        ctx.receive_event(bot, notice("enter"))
        ctx.should_not_pass_rule(group_notice)
