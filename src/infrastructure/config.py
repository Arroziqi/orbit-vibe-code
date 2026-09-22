from __future__ import annotations
from typing import Any

from domain.models import User, Task
from domain.registry import UnknownActionError, InvalidActionParamsError
from domain.strategies import SyncStrategy, BackupStrategy, DeleteStrategy
from domain.registry import ActionRegistry


class ConfigValidationError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(f"Config validation error: {message}")


def load_users(raw_users: dict[str, dict[str, Any]]) -> dict[str, User]:
    users: dict[str, User] = {}
    for name, data in raw_users.items():
        if not isinstance(data.get("quota"), int):
            raise ConfigValidationError(f"User '{name}': quota must be an integer")
        users[name] = User(name=name, daily_quota=data["quota"])
    return users


def load_tasks(
    raw_tasks: list[dict[str, Any]],
    known_users: set[str],
    action_registry: ActionRegistry,
) -> list[Task]:
    tasks: list[Task] = []
    for i, raw in enumerate(raw_tasks):
        if "user" not in raw:
            raise ConfigValidationError(f"Task {i}: missing 'user'")
        if raw["user"] not in known_users:
            raise ConfigValidationError(
                f"Task {i}: user '{raw['user']}' not defined in users"
            )
        if "time" not in raw:
            raise ConfigValidationError(f"Task {i}: missing 'time'")
        if "action" not in raw:
            raise ConfigValidationError(f"Task {i}: missing 'action'")
        if "target" not in raw:
            raise ConfigValidationError(f"Task {i}: missing 'target'")

        action = raw["action"]
        if not action_registry.has(action):
            raise ConfigValidationError(f"Task {i}: unknown action '{action}'")

        params = raw.get("params", {})
        strategy = action_registry.get(action)
        try:
            strategy.validate_params(params)
        except InvalidActionParamsError as e:
            raise ConfigValidationError(f"Task {i}: {e}")

        tasks.append(
            Task(
                user=raw["user"],
                time=raw["time"],
                action=action,
                target=raw["target"],
                params=params,
            )
        )
    return tasks


def build_action_registry() -> ActionRegistry:
    registry = ActionRegistry()
    registry.register(SyncStrategy())
    registry.register(BackupStrategy())
    registry.register(DeleteStrategy())
    return registry