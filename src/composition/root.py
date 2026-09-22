from __future__ import annotations
import logging
from typing import Any

from domain.registry import ActionRegistry
from domain.strategies import SyncStrategy, BackupStrategy, DeleteStrategy
from infrastructure.clock import SystemClock
from infrastructure.config import (
    load_users,
    load_tasks,
    build_action_registry,
    ConfigValidationError,
)
from infrastructure.logging_setup import setup_logging
from infrastructure.scheduler import DailyScheduler
from usecase.executor import TaskExecutor
from usecase.quota import QuotaService


SAMPLE_USERS_CONFIG: dict[str, dict[str, Any]] = {
    "alice": {"quota": 3},
    "bob": {"quota": 5},
}

SAMPLE_TASKS_CONFIG: list[dict[str, Any]] = [
    {"user": "alice", "time": "12:00", "action": "sync", "target": "/data/x"},
    {"user": "bob", "time": "12:00", "action": "backup", "target": "/srv/y"},
    {"user": "alice", "time": "12:00", "action": "delete", "target": "/tmp/z"},
]


class Application:
    def __init__(
        self,
        users_config: dict[str, dict[str, Any]] | None = None,
        tasks_config: list[dict[str, Any]] | None = None,
        clock: SystemClock | None = None,
        log_level: int = logging.INFO,
    ) -> None:
        setup_logging(log_level)
        self._logger = logging.getLogger(__name__)

        self._clock = clock or SystemClock()
        self._action_registry = build_action_registry()

        users_cfg = users_config or SAMPLE_USERS_CONFIG
        tasks_cfg = tasks_config or SAMPLE_TASKS_CONFIG

        try:
            self._users = load_users(users_cfg)
            self._tasks = load_tasks(tasks_cfg, set(self._users.keys()), self._action_registry)
        except ConfigValidationError as e:
            self._logger.error("Configuration validation failed: %s", e)
            raise

        self._quota_service = QuotaService(self._users, self._clock)
        self._executor = TaskExecutor(self._quota_service, self._action_registry)
        self._scheduler = DailyScheduler(
            tasks=self._tasks,
            executor=self._executor,
            clock=self._clock,
            logger=self._logger,
        )

        self._logger.info(
            "Application initialized",
            extra={
                "users": list(self._users.keys()),
                "task_count": len(self._tasks),
            },
        )

    @property
    def scheduler(self) -> DailyScheduler:
        return self._scheduler

    @property
    def quota_service(self) -> QuotaService:
        return self._quota_service

    @property
    def action_registry(self) -> ActionRegistry:
        return self._action_registry

    def run_once(self) -> list[Any]:
        return self._scheduler.run_once()

    def run_forever(self) -> None:
        self._scheduler.start()


def create_app(
    users_config: dict[str, dict[str, Any]] | None = None,
    tasks_config: list[dict[str, Any]] | None = None,
    clock: SystemClock | None = None,
    log_level: int = logging.INFO,
) -> Application:
    return Application(users_config, tasks_config, clock, log_level)


def main() -> None:
    app = create_app()
    app.run_forever()


if __name__ == "__main__":
    main()