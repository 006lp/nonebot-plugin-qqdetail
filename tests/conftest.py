from itertools import count

import nonebot
import pytest
from nonebot.adapters.onebot.v11 import (
    Adapter,
    Bot,
    GroupMessageEvent,
    Message,
    PrivateMessageEvent,
)
from nonebug import NONEBOT_INIT_KWARGS
from pytest_asyncio import is_async_test

MESSAGE_IDS = count(1)


def pytest_configure(config):
    config.stash[NONEBOT_INIT_KWARGS] = {
        "driver": "~fastapi",
        "command_start": {"/"},
        "superusers": {"10000"},
        "qqdetail_output_mode": "text",
        "qqdetail_recall_time": 0,
        "log_level": "WARNING",
    }


def pytest_collection_modifyitems(items):
    for item in items:
        if is_async_test(item):
            item.add_marker(pytest.mark.asyncio(loop_scope="session"), append=False)


@pytest.fixture(scope="session", autouse=True)
async def after_nonebot_init(_nonebot_init):
    driver = nonebot.get_driver()
    driver.register_adapter(Adapter)
    assert nonebot.load_plugin("nonebot_plugin_qqdetail") is not None


@pytest.fixture
def onebot():
    def create(ctx):
        adapter = ctx.create_adapter(base=Adapter)
        # Keep the real OneBot UniSeg exporter while intercepting API calls.
        type(adapter).get_name = classmethod(lambda cls: Adapter.get_name())
        return ctx.create_bot(base=Bot, adapter=adapter, self_id="99999")

    return create


@pytest.fixture
def message_event():
    def make(message="/qqdetail", *, user_id=20000, group_id=30000, role="member"):
        message = Message(message)
        sender = {"user_id": user_id, "nickname": "测试用户"}
        if group_id is not None:
            sender["role"] = role
        event_type = GroupMessageEvent if group_id is not None else PrivateMessageEvent
        return event_type(
            time=1,
            self_id=99999,
            post_type="message",
            sub_type="normal" if group_id is not None else "friend",
            user_id=user_id,
            message_type="group" if group_id is not None else "private",
            message_id=next(MESSAGE_IDS),
            message=message,
            original_message=message,
            raw_message=str(message),
            font=0,
            sender=sender,
            **({"group_id": group_id} if group_id is not None else {}),
        )

    return make


@pytest.fixture
def expect_query():
    def expect(ctx, user_id=20000, *, group_id=30000, stranger=None, member=None):
        calls = [
            (
                "get_stranger_info",
                {"user_id": user_id, "no_cache": True},
                {"nickname": "测试"} if stranger is None else stranger,
            )
        ]
        if group_id is not None:
            calls.append(
                (
                    "get_group_member_info",
                    {"group_id": group_id, "user_id": user_id, "no_cache": True},
                    {} if member is None else member,
                )
            )
        for api, params, reply in calls:
            kwargs = (
                {"exception": reply}
                if isinstance(reply, Exception)
                else {"result": reply}
            )
            ctx.should_call_api(api, params, **kwargs)

    return expect


@pytest.fixture
def expect_message():
    def expect(ctx, message, *, group_id=30000, user_id=20000, exception=None):
        destination = (
            {"message_type": "group", "group_id": group_id}
            if group_id is not None
            else {"message_type": "private", "user_id": user_id}
        )
        kwargs = (
            {"exception": exception} if exception else {"result": {"message_id": 10}}
        )
        ctx.should_call_api(
            "send_msg", {**destination, "message": Message(message)}, **kwargs
        )

    return expect


@pytest.fixture
def settings(monkeypatch):
    from nonebot_plugin_qqdetail.handlers import config

    def set_values(**values):
        for key, value in values.items():
            monkeypatch.setattr(config, key, value)

    return set_values
