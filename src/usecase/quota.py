from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date
from threading import Lock
from typing import Any

from domain.models import User, ExecutionOutcome, ExecutionResult, Task
from domain.ports import Clock, QuotaContext


@dataclass(slots=True)
class _UserQuotaState:
    executed: int = 0
    last_date: date | None = None


class QuotaService:
    SINGLETON_DRY_NODE: str = "quota_eligibility_check"

    def __init__(
        self,
        users: dict[str, User],
        clock: Clock,
    ) -> None:
        self._users = users
        self._clock = clock
        self._state: dict[str, _UserQuotaState] = {}
        self._lock = Lock()

    def _get_state(self, user_name: str) -> _UserQuotaState:
        today = self._clock.now_date()
        state = self._state.get(user_name)
        if state is None or state.last_date != today:
            state = _UserQuotaState(executed=0, last_date=today)
            self._state[user_name] = state
        return state

    def check_quota(self, user_name: str) -> tuple[bool, int, int]:
        user = self._users[user_name]
        state = self._get_state(user_name)
        remaining = user.daily_quota - state.executed
        allowed = remaining > 0
        return allowed, state.executed, user.daily_quota

    def reserve_and_increment(self, user_name: str) -> tuple[bool, int, int]:
        with self._lock:
            allowed, executed, quota = self.check_quota(user_name)
            if allowed:
                state = self._get_state(user_name)
                state.executed += 1
                executed = state.executed
            return allowed, executed, quota

    def build_quota_context(self, user_name: str) -> QuotaContext:
        user = self._users[user_name]
        state = self._get_state(user_name)
        return QuotaContext(
            user_name=user_name,
            current_executed=state.executed,
            daily_quota=user.daily_quota,
            execution_date=self._clock.now_date(),
        )

    def get_quota_snapshot(self, user_name: str) -> dict[str, Any]:
        allowed, executed, quota = self.check_quota(user_name)
        return {
            "user": user_name,
            "quota": quota,
            "executed": executed,
            "remaining": max(0, quota - executed),
            "allowed": allowed,
            "date": self._clock.now_date().isoformat(),
        }