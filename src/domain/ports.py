from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import Any, Protocol

from domain.models import ExecutionOutcome, Task, ExecutionResult


class Clock(Protocol):
    def now_date(self) -> date: ...
    def now_time_str(self) -> str: ...


class ActionStrategy(ABC):
    @property
    @abstractmethod
    def action_name(self) -> str: ...

    @abstractmethod
    def validate_params(self, params: dict[str, Any]) -> None: ...

    @abstractmethod
    def execute(
        self,
        task: Task,
        quota_context: QuotaContext,
    ) -> ExecutionResult: ...


@dataclass(frozen=True, slots=True)
class QuotaContext:
    user_name: str
    current_executed: int
    daily_quota: int
    execution_date: date