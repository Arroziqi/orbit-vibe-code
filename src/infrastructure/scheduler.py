from __future__ import annotations
import logging
import time
from datetime import datetime
from typing import Any

from domain.models import Task
from domain.ports import Clock
from usecase.executor import TaskExecutor


class DailyScheduler:
    def __init__(
        self,
        tasks: list[Task],
        executor: TaskExecutor,
        clock: Clock,
        tick_interval_seconds: float = 60.0,
        logger: logging.Logger | None = None,
    ) -> None:
        self._tasks = tasks
        self._executor = executor
        self._clock = clock
        self._tick_interval = tick_interval_seconds
        self._logger = logger or logging.getLogger(__name__)
        self._running = False

    def run_once(self) -> list[Any]:
        current_time = self._clock.now_time_str()
        results = []
        for task in self._tasks:
            if task.time == current_time:
                result = self._executor.execute(task)
                results.append(result)
        return results

    def start(self) -> None:
        self._running = True
        self._logger.info("Scheduler started")
        try:
            while self._running:
                self.run_once()
                time.sleep(self._tick_interval)
        except KeyboardInterrupt:
            self._logger.info("Scheduler stopped by interrupt")
        finally:
            self._running = False

    def stop(self) -> None:
        self._running = False