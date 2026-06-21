from types import SimpleNamespace

from nonebot_plugin_qqdetail.permissions import check_query_permission


class Event(SimpleNamespace):
    pass


def test_protected_target_is_denied_for_others() -> None:
    event = Event(user_id=10000)

    result = check_query_permission(
        event,
        "20000",
        only_admin=False,
        protect_ids={"20000"},
        superusers=set(),
    )

    assert not result.allowed
    assert result.message == "该用户在保护名单中"


def test_only_admin_allows_self_query() -> None:
    event = Event(user_id=10000)

    result = check_query_permission(
        event,
        "10000",
        only_admin=True,
        protect_ids=set(),
        superusers=set(),
    )

    assert result.allowed


def test_only_admin_denies_non_admin_other_query() -> None:
    event = Event(user_id=10000)

    result = check_query_permission(
        event,
        "20000",
        only_admin=True,
        protect_ids=set(),
        superusers=set(),
    )

    assert not result.allowed
    assert result.message == "当前配置仅允许管理员查询他人"


def test_only_admin_allows_superuser() -> None:
    event = Event(user_id=10000)

    result = check_query_permission(
        event,
        "20000",
        only_admin=True,
        protect_ids=set(),
        superusers={"10000"},
    )

    assert result.allowed
