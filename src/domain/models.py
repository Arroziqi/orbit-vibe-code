from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Any


class ExecutionOutcome(str, Enum):
    EXECUTED = "executed"
    TIME_MISS = "time_miss"
    QUOTA_EXCEEDED = "quota_exceeded"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class User:
    name: str
    daily_quota: int

    def __post_init__(self) -> None:
        if self.daily_quota < 0:
            raise ValueError("daily_quota must be non-negative")


@dataclass(frozen=True, slots=True)
class Task:
    user: str
    time: str
    action: str
    target: str
    params: dict[str, Any]

    def __post_init__(self) -> None:
        if not self.time or len(self.time) != 5 or self.time[2] != ":":
            raise ValueError("time must be in HH:MM format")


@dataclass(frozen=True, slots=True)
class ExecutionResult:
    task: Task
    outcome: ExecutionOutcome
    message: str
    executed_at: date

    def to_log_dict(self) -> dict[str, Any]:
        return {
            "user": self.task.user,
            "action": self.task.action,
            "target": self.task.target,
            "outcome": self.outcome.value,
            "log_message": self.message,
            "date": self.executed_at.isoformat(),
        }