from nonebot_plugin_qqdetail.targeting import resolve_target


class Segment:
    def __init__(self, type_: str, data: dict[str, str]):
        self.type = type_
        self.data = data


def test_resolve_target_prefers_at() -> None:
    result = resolve_target(
        sender_id=10000,
        message=[Segment("at", {"qq": "20000"})],
        argument="30000",
    )

    assert result.ok
    assert result.target_id == "20000"


def test_resolve_target_uses_argument() -> None:
    result = resolve_target(sender_id=10000, message=[], argument="@30000")

    assert result.ok
    assert result.target_id == "30000"


def test_resolve_target_rejects_invalid_argument() -> None:
    result = resolve_target(sender_id=10000, message=[], argument="abc")

    assert not result.ok
    assert result.error == "目标 QQ 号必须是纯数字"


def test_resolve_target_defaults_to_sender() -> None:
    result = resolve_target(sender_id=10000, message=[], argument=None)

    assert result.ok
    assert result.target_id == "10000"
