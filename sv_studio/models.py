from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Run:
    id: str
    project: str
    operation: str
    rtl_top: str
    tb_top: str
    sources: list[str]
    status: str = 'Running'
    detail: str = ''
    started: str = field(default_factory=now)
    ended: str | None = None
    commands: list[dict[str, Any]] = field(default_factory=list)
    versions: dict[str, str] = field(default_factory=dict)
    artifacts: list[str] = field(default_factory=list)
    statistics: dict[str, int] = field(default_factory=dict)
    diagnostics: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
