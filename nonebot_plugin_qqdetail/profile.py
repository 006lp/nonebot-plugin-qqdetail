import re
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone
from functools import partial
from typing import Any, Literal

from zhdate import ZhDate


@dataclass(slots=True, frozen=True)
class ProfileData:
    target_id: str
    stranger_info: dict[str, Any]
    member_info: dict[str, Any] = field(default_factory=dict)


SourceName = Literal["stranger", "member", "computed"]
Transform = Callable[[Any], str | None]
QQ_TIMEZONE = timezone(timedelta(hours=8))


@dataclass(slots=True, frozen=True)
class FieldSpec:
    key: str
    label: str
    source: SourceName = "stranger"
    transform: Transform | None = None
    suffix: str = ""


def text_value(value: Any) -> str | None:
    if isinstance(value, str):
        text = value.strip()
        return text if text not in {"", "-", "unknown"} else None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    return None


def integer(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        number = int(value)
        return number if number >= 0 and str(value).strip() == str(number) else None
    except (TypeError, ValueError, OverflowError):
        return None


def int_text(value: Any) -> str | None:
    number = integer(value)
    return str(number) if number is not None else None


def positive_text(value: Any) -> str | None:
    number = integer(value)
    return str(number) if number is not None and number > 0 else None


def sex_label(value: Any) -> str | None:
    return {"male": "男", "female": "女"}.get(str(value))


def is_true(value: Any) -> bool:
    return value is True or (
        isinstance(value, (int, str)) and value in (1, "1", "true")
    )


def flag_label(value: Any, *, label: str = "是") -> str | None:
    return label if is_true(value) else None


def role_label(value: Any) -> str | None:
    return {"owner": "群主", "admin": "管理员", "member": "成员"}.get(str(value))


def timestamp(value: Any, fmt: str) -> str | None:
    number = integer(value)
    if not number:
        return None
    try:
        return datetime.fromtimestamp(number, QQ_TIMEZONE).strftime(fmt)
    except (OSError, ValueError, OverflowError):
        return None


def blood_type(value: Any) -> str | None:
    number = integer(value)
    return {1: "A型", 2: "B型", 3: "O型", 4: "AB型", 5: "其他血型"}.get(number)


def career(value: Any) -> str | None:
    number = integer(value)
    careers = {
        1: "计算机/互联网/通信",
        2: "生产/工艺/制造",
        3: "医疗/护理/制药",
        4: "金融/银行/投资/保险",
        5: "商业/服务业/个体经营",
        6: "文化/广告/传媒",
        7: "娱乐/艺术/表演",
        8: "律师/法务",
        9: "教育/培训",
        10: "公务员/行政/事业单位",
        11: "模特",
        12: "空姐",
        13: "学生",
        14: "其他职业",
    }
    return careers.get(number)


def qq_level(value: Any) -> str | None:
    level = integer(value)
    if level is None:
        return None
    original = level
    parts = []
    for label, unit in (("皇冠", 64), ("太阳", 16), ("月亮", 4), ("星星", 1)):
        count, level = divmod(level, unit)
        if count:
            parts.append(f"{label}x{count}")
    return f"{' '.join(parts)} ({original})".strip()


def parse_home_town(value: Any) -> str | None:
    text = text_value(value)
    if not text or text == "0-0-0":
        return None
    # These codes are not unique administrative divisions. Preserve them rather
    # than inferring a province from the reference plugin's ambiguous table.
    return text


def parse_birthday(info: dict[str, Any]) -> date | None:
    parts = [integer(info.get(f"birthday_{key}")) for key in ("year", "month", "day")]
    try:
        return date(*parts) if all(part is not None for part in parts) else None
    except (TypeError, ValueError):
        return None


def constellation(month: int, day: int) -> str:
    ranges = (
        ("摩羯座", (1, 19)),
        ("水瓶座", (2, 18)),
        ("双鱼座", (3, 20)),
        ("白羊座", (4, 19)),
        ("金牛座", (5, 20)),
        ("双子座", (6, 20)),
        ("巨蟹座", (7, 22)),
        ("狮子座", (8, 22)),
        ("处女座", (9, 22)),
        ("天秤座", (10, 22)),
        ("天蝎座", (11, 21)),
        ("射手座", (12, 21)),
    )
    return next((name for name, end in ranges if (month, day) <= end), "摩羯座")


def zodiac(birthday: date) -> str | None:
    try:
        # zhdate requires naive datetimes; birthdays are calendar dates.
        lunar_year = ZhDate.from_datetime(
            datetime.combine(birthday, time.min)
        ).lunar_year
    except (TypeError, ValueError, IndexError, AttributeError, AssertionError):
        return None
    return ("鼠", "牛", "虎", "兔", "龙", "蛇", "马", "羊", "猴", "鸡", "狗", "猪")[
        (lunar_year - 2020) % 12
    ]


def labels_text(value: Any) -> str | None:
    if isinstance(value, list):
        parts = [text_value(item) for item in value]
        return "、".join(part for part in parts if part) or None
    return text_value(value)


def status_text(value: Any) -> str | None:
    if isinstance(value, dict):
        return text_value(value.get("desc")) or text_value(value.get("text"))
    return text_value(value)


FIELD_SPECS = (
    FieldSpec("user_id", "QQ号", "computed"),
    FieldSpec("uid", "UID"),
    FieldSpec("qid", "QID"),
    FieldSpec("nickname", "昵称", "computed"),
    FieldSpec("remark", "备注"),
    FieldSpec("card", "群昵称", "member"),
    FieldSpec("title", "群头衔", "member"),
    FieldSpec("role", "群身份", "member", role_label),
    FieldSpec("sex", "性别", "computed", sex_label),
    FieldSpec("birthday", "生日", "computed"),
    FieldSpec("constellation", "星座", "computed"),
    FieldSpec("zodiac", "生肖", "computed"),
    FieldSpec("age", "年龄", "computed", positive_text, "岁"),
    FieldSpec("kBloodType", "血型", transform=blood_type),
    FieldSpec("phoneNum", "电话"),
    FieldSpec("eMail", "邮箱"),
    FieldSpec("homeTown", "家乡", transform=parse_home_town),
    FieldSpec("address", "现居", "computed"),
    FieldSpec("area", "地区", "member"),
    FieldSpec("college", "学校"),
    FieldSpec("pos", "职位"),
    FieldSpec("makeFriendCareer", "职业", transform=career),
    FieldSpec("labels", "个性标签", transform=labels_text),
    FieldSpec("unfriendly", "风险账号", "member", partial(flag_label, label="有")),
    FieldSpec("is_robot", "机器人账号", "member", flag_label),
    FieldSpec("isHideQQLevel", "隐藏QQ等级", transform=flag_label),
    FieldSpec(
        "isHidePrivilegeIcon", "特权图标", transform=partial(flag_label, label="隐藏")
    ),
    FieldSpec("isBlock", "屏蔽用户", transform=flag_label),
    FieldSpec("isMsgDisturb", "免打扰", transform=flag_label),
    FieldSpec("isSpecialCareOpen", "特别关心", transform=flag_label),
    FieldSpec("isSpecialCareZone", "空间特别关心", transform=flag_label),
    FieldSpec("customStatusDescInfo", "自定义状态", transform=status_text),
    FieldSpec("qidian_enterprise_name", "企点企业"),
    FieldSpec("is_vip", "QQVIP", transform=partial(flag_label, label="已开")),
    FieldSpec("is_years_vip", "年VIP", transform=partial(flag_label, label="已开")),
    FieldSpec("vip_level", "VIP等级", transform=positive_text),
    FieldSpec("level", "群等级", "member", int_text, "级"),
    FieldSpec("qqLevel", "QQ等级", "computed"),
    FieldSpec("join_time", "加群时间", "member", partial(timestamp, fmt="%Y-%m-%d")),
    FieldSpec(
        "last_sent_time", "最后发言", "member", partial(timestamp, fmt="%Y-%m-%d %H:%M")
    ),
    FieldSpec("reg_time", "注册时间", transform=partial(timestamp, fmt="%Y年")),
    FieldSpec("login_days", "登录天数", transform=positive_text, suffix="天"),
    FieldSpec("long_nick", "签名"),
)
DEFAULT_DISPLAY_LABELS = [spec.label for spec in FIELD_SPECS if spec.key != "uid"]
LABEL_TO_KEY = {spec.label: spec.key for spec in FIELD_SPECS}


def mask_phone(value: str) -> str:
    return re.sub(
        r"\d+",
        lambda m: (
            m[0][:3] + "*" * (len(m[0]) - 5) + m[0][-2:]
            if len(m[0]) > 5
            else "*" * len(m[0])
        ),
        value,
    )


def mask_email(value: str) -> str:
    # Keep only the first local-part character, including short addresses.
    return re.sub(r"([^\s@]+)@([^\s@]+)", lambda m: m[1][:1] + "***@" + m[2], value)


def _computed(profile: ProfileData) -> dict[str, Any]:
    stranger, member = profile.stranger_info, profile.member_info
    birthday = parse_birthday(stranger)
    level = next(
        (
            value
            for value in (
                stranger.get("qqLevel"),
                stranger.get("level"),
                member.get("qq_level"),
            )
            if integer(value) is not None
        ),
        None,
    )
    address = "-".join(
        part for key in ("province", "city") if (part := text_value(stranger.get(key)))
    )
    country = text_value(stranger.get("country"))
    return {
        "user_id": profile.target_id,
        "nickname": text_value(stranger.get("nickname"))
        or text_value(member.get("nickname")),
        "sex": stranger.get("sex")
        if sex_label(stranger.get("sex"))
        else member.get("sex"),
        "age": next(
            (
                value
                for value in (stranger.get("age"), member.get("age"))
                if positive_text(value) is not None
            ),
            None,
        ),
        "birthday": birthday.isoformat() if birthday else None,
        "constellation": constellation(birthday.month, birthday.day)
        if birthday
        else None,
        "zodiac": zodiac(birthday) if birthday else None,
        "address": address
        if country == "中国" and address
        else "-".join(filter(None, (country, address))),
        "qqLevel": "隐藏"
        if is_true(stranger.get("isHideQQLevel"))
        else qq_level(level),
    }


def build_display_lines(
    profile: ProfileData, display_options: list[str], *, desensitize: bool = True
) -> list[str]:
    """One canonical field pipeline shared by card and text output."""
    enabled = {LABEL_TO_KEY.get(option, option) for option in display_options}
    sources = {
        "stranger": profile.stranger_info,
        "member": profile.member_info,
        "computed": _computed(profile),
    }
    lines = []
    for spec in FIELD_SPECS:
        if spec.key not in enabled:
            continue
        value = sources[spec.source].get(spec.key)
        text = spec.transform(value) if spec.transform else text_value(value)
        if not text:
            continue
        if desensitize:
            if spec.key == "phoneNum":
                text = mask_phone(text)
            elif spec.key == "eMail":
                text = mask_email(text)
        # Bound display size without letting control characters alter the layout.
        text = "".join(char for char in text[:4096] if char >= " " or char == "\n")
        lines.append(f"{spec.label}：{text}{spec.suffix}")
    return lines
