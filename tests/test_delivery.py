import asyncio
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest
from nonebot.adapters.onebot.v11 import MessageSegment
from PIL import Image


async def test_render_failure_falls_back_to_text(app, onebot, expect_message):
    from nonebot_plugin_alconna.uniseg import Target

    from nonebot_plugin_qqdetail.delivery import MessageSender, build_messages

    render = AsyncMock(side_effect=OSError("font unavailable"))
    lines = ["QQ号：20000", "昵称：测试"]
    messages = await build_messages("20000", lines, render)
    render.assert_awaited_once_with("20000", lines)
    sender = MessageSender()
    async with app.test_api() as ctx:
        expect_message(ctx, "QQ号：20000\n昵称：测试")
        await sender.send(onebot(ctx), Target("30000"), messages, recall_time=0)
    assert not sender.tasks


async def test_image_send_and_recall(app, onebot, expect_message):
    from nonebot_plugin_alconna.uniseg import Target

    from nonebot_plugin_qqdetail.delivery import MessageSender, build_messages

    messages = await build_messages(
        "20000", ["QQ号：20000"], AsyncMock(return_value=(b"PNG",))
    )
    sender = MessageSender()
    async with app.test_api() as ctx:
        bot = onebot(ctx)
        expect_message(ctx, MessageSegment.image(b"PNG"))
        ctx.should_call_api("delete_msg", {"message_id": 10})
        await sender.send(bot, Target("30000"), messages, recall_time=0.01)
        await asyncio.gather(*sender.tasks)
        await asyncio.sleep(0)
    assert not sender.tasks


async def test_cancel_tasks_per_bot():
    from nonebot_plugin_qqdetail.delivery import MessageSender

    sender = MessageSender()
    receipts = [
        SimpleNamespace(recall=AsyncMock()),
        SimpleNamespace(recall=AsyncMock()),
    ]
    tasks = [asyncio.create_task(sender._recall(receipt, 1000)) for receipt in receipts]
    for task, bot_id in zip(tasks, ("1", "2")):
        sender.tasks[task] = bot_id
        task.add_done_callback(sender.tasks.pop)
    await sender.cancel("1")
    assert tasks[0].cancelled() and not tasks[1].done()
    await sender.cancel()
    assert tasks[1].cancelled() and not sender.tasks
    for receipt in receipts:
        receipt.recall.assert_not_awaited()


async def test_failed_recall_is_contained():
    from nonebot_plugin_qqdetail.delivery import MessageSender

    receipt = SimpleNamespace(recall=AsyncMock(side_effect=RuntimeError()))
    await MessageSender._recall(receipt, 0)
    receipt.recall.assert_awaited_once()


async def test_shutdown_releases_resources(monkeypatch):
    from nonebot_plugin_qqdetail import handlers

    cancel, close = AsyncMock(), AsyncMock()
    monkeypatch.setattr(handlers.sender, "cancel", cancel)
    monkeypatch.setattr(handlers.images, "close", close)
    await handlers.shutdown()
    cancel.assert_awaited_once()
    close.assert_awaited_once()


@pytest.mark.parametrize("render_cards", [False, True])
async def test_recall_disabled(render_cards, monkeypatch):
    from nonebot_plugin_alconna import UniMessage
    from nonebot_plugin_alconna.uniseg import Target

    from nonebot_plugin_qqdetail.delivery import MessageSender, build_messages

    send = AsyncMock(return_value=SimpleNamespace(msg_ids=[10]))
    monkeypatch.setattr(UniMessage, "send", send)
    render = AsyncMock(return_value=(b"PNG",)) if render_cards else None
    messages = await build_messages("20000", ["测试"], render)
    sender = MessageSender()
    await sender.send(
        SimpleNamespace(self_id="1"), Target("30000"), messages, recall_time=0
    )
    assert not sender.tasks


def test_chinese_emoji_wrap_and_pagination():
    from nonebot_plugin_qqdetail.cards import LINES_PER_PAGE, TEXT_WIDTH, CardRenderer

    renderer = CardRenderer()
    lines = ["昵称：中文测试 👩‍💻👨‍👩‍👧‍👦", "签名：" + "长中文文本" * 150]
    rows = renderer.wrap(lines)
    assert len(rows) > LINES_PER_PAGE
    assert ("👨‍👩‍👧‍👦", True) in rows[0]
    for row in rows:
        assert (
            sum(
                (renderer.emoji_font if e else renderer.font).getlength(t)
                for t, e in row
            )
            <= TEXT_WIDTH
        )
    pages = renderer.create(b"not an image", lines)
    assert len(pages) > 1
    for png in pages:
        with Image.open(BytesIO(png)) as image:
            assert image.format == "PNG" and image.width == 960
            assert image.height <= 1200


async def test_avatar_http_error_and_size_limit():
    from nonebot_plugin_qqdetail.cards import MAX_AVATAR_BYTES, ImageService

    images = ImageService()
    images._client = httpx.AsyncClient(
        transport=httpx.MockTransport(lambda request: httpx.Response(500))
    )
    assert await images._get_avatar("20000") is None
    await images.close()
    images._client = httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(200, content=b"x" * (MAX_AVATAR_BYTES + 1))
        )
    )
    assert await images._get_avatar("20000") is None
    await images.close()


async def test_content_cache_expiry_and_bounds(monkeypatch):
    from nonebot_plugin_qqdetail.cards import CardRenderer, ImageService

    images = ImageService()
    avatar = AsyncMock(return_value=b"avatar")
    monkeypatch.setattr(images, "_get_avatar", avatar)
    calls = []

    def render(self, avatar, lines):
        calls.append((avatar, lines))
        return (b"png",)

    monkeypatch.setattr(CardRenderer, "create", render)
    assert await images.render("20000", ["昵称：测试"]) == (b"png",)
    await images.render("20000", ["昵称：测试"])
    assert len(calls) == 1
    avatar.return_value = b"changed avatar"
    await images.render("20000", ["昵称：测试"])
    await images.render("20000", ["昵称：新昵称"])
    assert len(calls) == 3
    images._cache = type(images._cache)(
        (key, (created - 301, value)) for key, (created, value) in images._cache.items()
    )
    await images.render("20000", ["昵称：新昵称"])
    assert len(calls) == 4
    for index in range(40):
        await images.render("20000", [f"昵称：{index}"])
    assert len(images._cache) == 32
    await images.close()
    assert not images._cache
