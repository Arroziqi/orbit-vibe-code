"""Data models for the task scheduling system."""
from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class Task:
    """Represents a single scheduled task belonging to a user.

    `params` is an open dictionary so new action types can carry whatever
    configuration they need without changing this class.
    """

    user: str
    time: str  # "HH:MM", 24h format
    action: str
    target: str
    params: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self._is_valid_time(self.time):
            raise ValueError(f"Invalid time format for task: {self.time!r} (expected HH:MM)")

    @staticmethod
    def _is_valid_time(value: str) -> bool:
        try:
            hh, mm = value.split(":")
            return 0 <= int(hh) <= 23 and 0 <= int(mm) <= 59
        except (ValueError, AttributeError):
            return False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """Build a Task from a plain dict, e.g. loaded from JSON/config."""
        return cls(
            user=data["user"],
            time=data["time"],
            action=data["action"],
            target=data["target"],
            params=data.get("params", {}),
        )

    def __repr__(self) -> str:
        return f"<Task user={self.user} action={self.action} target={self.target} time={self.time}>"
