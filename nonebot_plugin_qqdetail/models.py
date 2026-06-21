from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True, frozen=True)
class ProfileData:
    target_id: str
    group_id: str | None
    stranger_info: dict[str, Any]
    member_info: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class TargetResolution:
    target_id: str | None
    error: str = ""

    @property
    def ok(self) -> bool:
        return self.error == "" and self.target_id is not None


@dataclass(slots=True, frozen=True)
class QueryFailure:
    message: str


@dataclass(slots=True, frozen=True)
class PermissionResult:
    allowed: bool
    message: str = ""
