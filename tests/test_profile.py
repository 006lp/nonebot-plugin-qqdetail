from datetime import date
from unittest.mock import AsyncMock

import pytest
from nonebot.adapters.onebot.v11 import ActionFailed
from pydantic import ValidationError


def test_profile_fields():
    from nonebot_plugin_qqdetail.profile import ProfileData, build_display_lines

    profile = ProfileData(
        "20000",
        {
            "nickname": "测试用户",
            "sex": "male",
            "birthday_year": 2020,
            "birthday_month": 1,
            "birthday_day": 25,
            "country": "中国",
            "province": "广东",
            "city": "深圳",
            "qqLevel": 20,
        },
        {"card": "群名片", "role": "owner", "level": 5},
    )
    expected = [
        "QQ号：20000",
        "昵称：测试用户",
        "群昵称：群名片",
        "群身份：群主",
        "性别：男",
        "生日：2020-01-25",
        "星座：水瓶座",
        "生肖：鼠",
        "现居：广东-深圳",
        "群等级：5级",
        "QQ等级：太阳x1 月亮x1 (20)",
    ]
    assert (
        build_display_lines(profile, [line.split("：", 1)[0] for line in expected])
        == expected
    )


@pytest.mark.parametrize(
    ("birthday", "expected"),
    [
        (date(2020, 1, 24), "猪"),
        (date(2020, 1, 25), "鼠"),
        (date(2024, 2, 9), "兔"),
        (date(2024, 2, 10), "龙"),
    ],
)
def test_lunar_zodiac(birthday, expected):
    from nonebot_plugin_qqdetail.profile import zodiac

    assert zodiac(birthday) == expected


def test_malformed_fields_and_unknown_flags():
    from nonebot_plugin_qqdetail.profile import (
        DEFAULT_DISPLAY_LABELS,
        ProfileData,
        build_display_lines,
    )

    profile = ProfileData(
        "20000",
        {
            "nickname": ["invalid"],
            "labels": ["开发", "游戏"],
            "is_vip": "false",
            "isBlock": "0",
            "qqLevel": {},
            "age": -1,
            "birthday_year": 2020,
            "birthday_month": 2,
            "birthday_day": 30,
            "join_time": 0,
            "kBloodType": [],
            "reg_time": 10**100,
        },
    )
    assert build_display_lines(profile, DEFAULT_DISPLAY_LABELS) == [
        "QQ号：20000",
        "个性标签：开发、游戏",
    ]


@pytest.mark.parametrize(
    ("stranger", "member", "expected"),
    [
        ({}, {"qq_level": 20}, "太阳x1 月亮x1 (20)"),
        ({"level": 16}, {"level": 9}, "太阳x1 (16)"),
        ({"qqLevel": 0}, {"qq_level": 20}, "(0)"),
        ({"qqLevel": "unknown"}, {"qq_level": 20}, "太阳x1 月亮x1 (20)"),
        ({"qqLevel": 20, "isHideQQLevel": True}, {}, "隐藏"),
    ],
)
def test_qq_level_fallback(stranger, member, expected):
    from nonebot_plugin_qqdetail.profile import ProfileData, build_display_lines

    assert build_display_lines(ProfileData("20000", stranger, member), ["QQ等级"]) == [
        f"QQ等级：{expected}"
    ]


def test_partial_member_profile():
    from nonebot_plugin_qqdetail.profile import ProfileData, build_display_lines

    profile = ProfileData(
        "20000", {}, {"nickname": "群用户", "sex": "female", "age": 22}
    )
    assert build_display_lines(profile, ["QQ号", "昵称", "性别", "年龄"]) == [
        "QQ号：20000",
        "昵称：群用户",
        "性别：女",
        "年龄：22岁",
    ]


def test_desensitization_and_opt_out():
    from nonebot_plugin_qqdetail.profile import ProfileData, build_display_lines

    profile = ProfileData(
        "20000", {"phoneNum": "13812345678", "eMail": "alice@example.com"}
    )
    assert build_display_lines(profile, ["电话", "邮箱"]) == [
        "电话：138******78",
        "邮箱：a***@example.com",
    ]
    assert build_display_lines(profile, ["电话", "邮箱"], desensitize=False) == [
        "电话：13812345678",
        "邮箱：alice@example.com",
    ]


def test_extended_public_fields_and_fixed_timezone():
    from nonebot_plugin_qqdetail.profile import ProfileData, build_display_lines

    profile = ProfileData(
        "20000",
        {
            "uid": "u_test",
            "qid": "q_test",
            "college": "测试大学",
            "pos": "工程师",
            "customStatusDescInfo": {"desc": "在线"},
            "qidian_enterprise_name": "企业",
            "isSpecialCareOpen": True,
            "login_days": 100,
        },
        {"area": "广东", "last_sent_time": 86400},
    )
    expected = [
        "UID：u_test",
        "QID：q_test",
        "地区：广东",
        "学校：测试大学",
        "职位：工程师",
        "特别关心：是",
        "自定义状态：在线",
        "企点企业：企业",
        "最后发言：1970-01-02 08:00",
        "登录天数：100天",
    ]
    assert (
        build_display_lines(profile, [line.split("：", 1)[0] for line in expected])
        == expected
    )


def test_short_phone_values_are_masked():
    from nonebot_plugin_qqdetail.profile import mask_phone

    assert mask_phone("1234") == "****"


def test_config_defaults_and_id_normalization():
    from nonebot_plugin_qqdetail.config import Config

    config = Config(
        qqdetail_protect_ids=[20000, "030000"], qqdetail_auto_groups=[40000]
    )
    assert config.qqdetail_protect_ids == {"20000", "30000"}
    assert config.qqdetail_auto_groups == {"40000"}
    assert config.qqdetail_output_mode == "image"
    assert config.qqdetail_recall_time == 10
    assert config.qqdetail_desensitize
    assert not config.qqdetail_auto_enter and not config.qqdetail_auto_exit
    assert "UID" not in config.qqdetail_display_options


@pytest.mark.parametrize(
    "kwargs",
    [
        {"qqdetail_recall_time": -1},
        {"qqdetail_output_mode": "html"},
        {"qqdetail_protect_ids": ["abc"]},
        {"qqdetail_display_options": ["不存在"]},
    ],
)
def test_config_validation(kwargs):
    from nonebot_plugin_qqdetail.config import Config

    with pytest.raises(ValidationError):
        Config(**kwargs)


@pytest.mark.parametrize(
    ("arguments", "expected"),
    [
        ([], ["10000"]),
        (["20000", "@30000", "20000"], ["20000", "30000"]),
        (["00020000"], ["20000"]),
    ],
)
def test_targets(arguments, expected):
    from nonebot_plugin_qqdetail.policy import resolve_targets

    assert resolve_targets(10000, arguments) == expected


@pytest.mark.parametrize("argument", ["abc", "0", "-1", "@all", "１２３", "123.0", ""])
def test_reject_invalid_targets(argument):
    from nonebot_plugin_qqdetail.policy import resolve_targets

    with pytest.raises(ValueError):
        resolve_targets(10000, [argument])


@pytest.mark.parametrize(
    ("sender", "target", "only_admin", "protected", "admins", "allowed"),
    [
        ("20000", "30000", False, {"30000"}, set(), False),
        ("20000", "20000", True, {"20000"}, set(), True),
        ("20000", "30000", True, set(), set(), False),
        ("10000", "30000", True, set(), {"10000"}, True),
        ("10000", "30000", True, set(), {"onebot:10000"}, True),
        ("20000", "10000", False, set(), {"10000"}, False),
        ("10000", "10000", True, set(), {"10000"}, True),
        ("20000", "99999", False, set(), set(), False),
    ],
)
def test_permission(sender, target, only_admin, protected, admins, allowed):
    from nonebot_plugin_qqdetail.policy import query_denial

    denial = query_denial(
        sender,
        target,
        only_admin=only_admin,
        protect_ids=protected,
        superusers=admins,
        bot_self_id="99999",
    )
    assert (denial is None) is allowed


@pytest.mark.parametrize(
    ("stranger", "member", "success"),
    [
        (ActionFailed(), {"nickname": "群昵称"}, True),
        ({"nickname": "昵称"}, ActionFailed(), True),
        (ActionFailed(), ActionFailed(), False),
        ({}, {}, False),
        ({"user_id": 20000}, {}, False),
        ([], None, False),
    ],
)
async def test_partial_api_failures(stranger, member, success):
    from nonebot_plugin_qqdetail.api import ProfileUnavailable, fetch_profile

    bot = AsyncMock()
    bot.call_api.side_effect = [stranger, member]
    if success:
        result = await fetch_profile(bot, "20000", "30000")
        assert result.target_id == "20000"
    else:
        with pytest.raises(ProfileUnavailable, match="资料不可用"):
            await fetch_profile(bot, "20000", "30000")
    assert bot.call_api.call_args_list[0].args == ("get_stranger_info",)
    assert bot.call_api.call_args_list[1].kwargs == {
        "group_id": 30000,
        "user_id": 20000,
        "no_cache": True,
    }


async def test_private_query_has_no_group_api():
    from nonebot_plugin_qqdetail.api import fetch_profile

    bot = AsyncMock()
    bot.call_api.return_value = {"nickname": "昵称"}
    result = await fetch_profile(bot, "20000", None)
    assert result.stranger_info["nickname"] == "昵称"
    bot.call_api.assert_awaited_once_with(
        "get_stranger_info", user_id=20000, no_cache=True
    )
