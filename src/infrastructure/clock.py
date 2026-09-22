from __future__ import annotations
from datetime import date, datetime

from domain.ports import Clock


class SystemClock:
    def now_date(self) -> date:
        return datetime.now().date()

    def now_time_str(self) -> str:
        return datetime.now().strftime("%H:%M")


class FixedClock:
    def __init__(self, fixed_datetime: datetime) -> None:
        self._fixed = fixed_datetime

    def now_date(self) -> date:
        return self._fixed.date()

    def now_time_str(self) -> str:
        return self._fixed.strftime("%H:%M")

    def advance_days(self, days: int) -> None:
        from datetime import timedelta
        self._fixed += timedelta(days=days)

    def advance_minutes(self, minutes: int) -> None:
        from datetime import timedelta
        self._fixed += timedelta(minutes=minutes)