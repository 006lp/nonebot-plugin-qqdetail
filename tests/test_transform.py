from nonebot_plugin_qqdetail.models import ProfileData
from nonebot_plugin_qqdetail.transform import build_display_lines


def test_build_display_lines_formats_profile() -> None:
    profile = ProfileData(
        target_id="10000",
        group_id="20000",
        stranger_info={
            "user_id": 10000,
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
        member_info={
            "card": "群名片",
            "level": 5,
        },
    )

    lines = build_display_lines(
        profile,
        [
            "QQ号",
            "昵称",
            "群昵称",
            "性别",
            "生日",
            "星座",
            "生肖",
            "现居",
            "群等级",
            "QQ等级",
        ],
    )

    assert lines == [
        "QQ号：10000",
        "昵称：测试用户",
        "群昵称：群名片",
        "性别：男",
        "生日：2020-01-25",
        "星座：水瓶座",
        "生肖：鼠",
        "现居：广东-深圳",
        "群等级：5级",
        "QQ等级：太阳x1 月亮x1 (20)",
    ]


def test_build_display_lines_skips_empty_values() -> None:
    profile = ProfileData(
        target_id="10000",
        group_id=None,
        stranger_info={"user_id": 10000, "phoneNum": "-"},
    )

    lines = build_display_lines(profile, ["QQ号", "电话", "群昵称"])

    assert lines == ["QQ号：10000"]
