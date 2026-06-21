from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Literal

SourceName = Literal["stranger", "member", "computed"]
Transform = Callable[[Any], str | None]


@dataclass(slots=True, frozen=True)
class FieldSpec:
    key: str
    label: str
    source: SourceName = "stranger"
    suffix: str = ""
    skip_values: frozenset[Any] = field(default_factory=frozenset)
    transform: Transform | None = None
    multiline: bool = False
    wrap_width: int = 18


def sex_label(value: Any) -> str | None:
    return {"male": "男", "female": "女"}.get(str(value))


def bool_label(value: Any, label: str = "是") -> str | None:
    return label if bool(value) else None


def risk_account_label(value: Any) -> str | None:
    return bool_label(value, "有")


def opened_label(value: Any) -> str | None:
    return bool_label(value, "已开")


def vip_level(value: Any) -> str | None:
    try:
        level = int(value)
    except (TypeError, ValueError):
        return None
    return str(level) if level > 0 else None


def int_text(value: Any) -> str | None:
    try:
        return str(int(value))
    except (TypeError, ValueError):
        return None


def timestamp_date(value: Any) -> str | None:
    try:
        return datetime.fromtimestamp(int(value)).strftime("%Y-%m-%d")
    except (OSError, TypeError, ValueError):
        return None


def timestamp_year(value: Any) -> str | None:
    try:
        return datetime.fromtimestamp(int(value)).strftime("%Y年")
    except (OSError, TypeError, ValueError):
        return None


def blood_type(value: Any) -> str | None:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return {
        1: "A型",
        2: "B型",
        3: "O型",
        4: "AB型",
        5: "其他血型",
    }.get(number, f"血型{number}")


def career(value: Any) -> str | None:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    if number == 0:
        return None
    return {
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
    }.get(number, f"职业{number}")


def qq_level(value: Any) -> str | None:
    try:
        level = int(value)
    except (TypeError, ValueError):
        return None
    if level <= 0:
        return None
    parts: list[str] = []
    for label, unit in (("皇冠", 64), ("太阳", 16), ("月亮", 4), ("星星", 1)):
        count, level = divmod(level, unit)
        if count:
            parts.append(f"{label}x{count}")
    return f"{' '.join(parts)} ({value})"


def parse_home_town(value: Any) -> str | None:
    text = str(value).strip()
    if text in {"", "0-0-0"}:
        return None
    parts = text.split("-")
    if len(parts) != 3:
        return text

    country_code, province_code, _ = parts
    country_map = {
        "49": "中国",
        "250": "俄罗斯",
        "217": "法国",
        "222": "特里尔",
    }
    province_map = {
        "98": "北京",
        "99": "天津/辽宁",
        "100": "河北/上海/吉林",
        "101": "江苏/河南/山西/黑龙江/重庆",
        "102": "浙江/湖北/内蒙古/四川",
        "103": "安徽/湖南/贵州/陕西",
        "104": "福建/广东/云南/甘肃/台湾",
        "105": "江西/广西/西藏/青海/香港",
        "106": "山东/海南/陕西/宁夏/澳门",
        "107": "新疆",
    }

    country = country_map.get(country_code, f"国家/地区{country_code}")
    if country_code != "49":
        return country
    if province_code == "0":
        return country
    return province_map.get(province_code, f"{province_code}省")


def parse_birthday(info: dict[str, Any]) -> date | None:
    try:
        year = int(info.get("birthday_year"))
        month = int(info.get("birthday_month"))
        day = int(info.get("birthday_day"))
        return date(year, month, day)
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
    for name, (end_month, end_day) in ranges:
        if (month, day) <= (end_month, end_day):
            return name
    return "摩羯座"


def zodiac(year: int) -> str:
    names = ("鼠", "牛", "虎", "兔", "龙", "蛇", "马", "羊", "猴", "鸡", "狗", "猪")
    return names[(year - 2020) % 12]


FIELD_SPECS: tuple[FieldSpec, ...] = (
    FieldSpec("user_id", "QQ号"),
    FieldSpec("nickname", "昵称"),
    FieldSpec("remark", "备注"),
    FieldSpec("card", "群昵称", source="member"),
    FieldSpec("title", "群头衔", source="member"),
    FieldSpec("sex", "性别", transform=sex_label),
    FieldSpec("birthday", "生日", source="computed"),
    FieldSpec("constellation", "星座", source="computed"),
    FieldSpec("zodiac", "生肖", source="computed"),
    FieldSpec("age", "年龄", suffix="岁"),
    FieldSpec("kBloodType", "血型", transform=blood_type),
    FieldSpec("phoneNum", "电话", skip_values=frozenset({"-", ""})),
    FieldSpec("eMail", "邮箱", skip_values=frozenset({"-", ""})),
    FieldSpec(
        "homeTown",
        "家乡",
        skip_values=frozenset({"0-0-0", ""}),
        transform=parse_home_town,
    ),
    FieldSpec("address", "现居", source="computed"),
    FieldSpec(
        "makeFriendCareer", "职业", skip_values=frozenset({"0", ""}), transform=career
    ),
    FieldSpec("labels", "个性标签"),
    FieldSpec(
        "unfriendly",
        "风险账号",
        source="member",
        transform=risk_account_label,
    ),
    FieldSpec("is_robot", "机器人账号", source="member", transform=bool_label),
    FieldSpec("is_vip", "QQVIP", transform=opened_label),
    FieldSpec("is_years_vip", "年VIP", transform=opened_label),
    FieldSpec("vip_level", "VIP等级", transform=vip_level),
    FieldSpec("level", "群等级", source="member", suffix="级", transform=int_text),
    FieldSpec("join_time", "加群时间", source="member", transform=timestamp_date),
    FieldSpec("qqLevel", "QQ等级", transform=qq_level),
    FieldSpec("reg_time", "注册时间", transform=timestamp_year),
    FieldSpec("long_nick", "签名", multiline=True, wrap_width=18),
)

DEFAULT_DISPLAY_LABELS: list[str] = [field.label for field in FIELD_SPECS]
LABEL_TO_KEY: dict[str, str] = {field.label: field.key for field in FIELD_SPECS}
