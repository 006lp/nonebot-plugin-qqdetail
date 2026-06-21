import textwrap
from typing import Any

from .fields import (
    FIELD_SPECS,
    LABEL_TO_KEY,
    FieldSpec,
    constellation,
    parse_birthday,
    zodiac,
)
from .models import ProfileData


def normalize_display_keys(display_options: list[str]) -> set[str]:
    return {LABEL_TO_KEY.get(option, option) for option in display_options}


def build_display_lines(profile: ProfileData, display_options: list[str]) -> list[str]:
    enabled_keys = normalize_display_keys(display_options)
    lines: list[str] = []

    for spec in FIELD_SPECS:
        if spec.key not in enabled_keys:
            continue
        lines.extend(field_lines(spec, profile.stranger_info, profile.member_info))

    return lines


def field_lines(
    spec: FieldSpec,
    stranger_info: dict[str, Any],
    member_info: dict[str, Any],
) -> list[str]:
    if spec.source == "computed":
        return computed_lines(spec, stranger_info)

    data = stranger_info if spec.source == "stranger" else member_info
    value = data.get(spec.key)
    if value is None or value in spec.skip_values:
        return []

    text = spec.transform(value) if spec.transform else str(value)
    if not text:
        return []

    rendered = f"{spec.label}：{text}{spec.suffix}"
    if not spec.multiline:
        return [rendered]
    return textwrap.wrap(rendered, width=spec.wrap_width) or [rendered]


def computed_lines(spec: FieldSpec, stranger_info: dict[str, Any]) -> list[str]:
    birthday = parse_birthday(stranger_info)

    if spec.key == "birthday":
        return [f"{spec.label}：{birthday:%Y-%m-%d}"] if birthday else []

    if spec.key == "constellation":
        return (
            [f"{spec.label}：{constellation(birthday.month, birthday.day)}"]
            if birthday
            else []
        )

    if spec.key == "zodiac":
        return [f"{spec.label}：{zodiac(birthday.year)}"] if birthday else []

    if spec.key == "address":
        country = stranger_info.get("country")
        province = stranger_info.get("province")
        city = stranger_info.get("city")
        if country == "中国" and (province or city):
            return [f"{spec.label}：{province or ''}-{city or ''}"]
        return [f"{spec.label}：{country}"] if country else []

    return []
