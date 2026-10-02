from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from .policy import normalize_id
from .profile import DEFAULT_DISPLAY_LABELS, LABEL_TO_KEY


class Config(BaseModel):
    """NoneBot settings; all options use the qqdetail_ namespace."""

    qqdetail_only_admin: bool = False
    qqdetail_protect_ids: set[str] = Field(default_factory=set)
    qqdetail_display_options: list[str] = Field(
        default_factory=lambda: DEFAULT_DISPLAY_LABELS.copy()
    )
    qqdetail_command_aliases: set[str] = Field(
        default_factory=lambda: {"qq资料", "查qq", "查q", "box", "盒", "开盒"}
    )
    qqdetail_output_mode: Literal["image", "text"] = "image"
    qqdetail_recall_time: int = Field(default=10, ge=0)
    qqdetail_desensitize: bool = True
    qqdetail_auto_enter: bool = False
    qqdetail_auto_exit: bool = False
    qqdetail_auto_groups: set[str] = Field(default_factory=set)
    qqdetail_font_path: Path | None = None

    @field_validator("qqdetail_protect_ids", "qqdetail_auto_groups", mode="before")
    @classmethod
    def normalize_ids(cls, value: object) -> set[str]:
        if not isinstance(value, (list, tuple, set, frozenset)):
            raise ValueError("IDs must be a collection of positive numeric values")
        return {normalize_id(item) for item in value}

    @field_validator("qqdetail_display_options")
    @classmethod
    def validate_fields(cls, value: list[str]) -> list[str]:
        valid = set(LABEL_TO_KEY) | set(LABEL_TO_KEY.values())
        unknown = set(value) - valid
        if unknown:
            raise ValueError(f"Unknown profile fields: {', '.join(sorted(unknown))}")
        return list(dict.fromkeys(value))
