from pydantic import BaseModel, Field

from .fields import DEFAULT_DISPLAY_LABELS


class Config(BaseModel):
    """Plugin configuration loaded by NoneBot."""

    qqdetail_only_admin: bool = False
    qqdetail_protect_ids: set[str] = Field(default_factory=set)
    qqdetail_display_options: list[str] = Field(
        default_factory=lambda: DEFAULT_DISPLAY_LABELS.copy()
    )
    qqdetail_command_aliases: set[str] = Field(
        default_factory=lambda: {"qq资料", "查qq", "查q"}
    )
