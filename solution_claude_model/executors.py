"""Task execution strategies.

Each action type ('sync', 'backup', 'delete', ...) is its own strategy
class. New actions are added by subclassing BaseExecutor and registering
with @register("name") -- the scheduler never needs to change.
"""
import logging
from abc import ABC, abstractmethod
from typing import Callable, Dict, Type

from models import Task

logger = logging.getLogger(__name__)

_REGISTRY: Dict[str, Type["BaseExecutor"]] = {}


def register(action_name: str) -> Callable[[Type["BaseExecutor"]], Type["BaseExecutor"]]:
    """Class decorator that registers an executor for a given action name."""

    def decorator(cls: Type["BaseExecutor"]) -> Type["BaseExecutor"]:
        _REGISTRY[action_name] = cls
        return cls

    return decorator


class BaseExecutor(ABC):
    """Strategy interface all task executors must implement."""

    @abstractmethod
    def execute(self, task: Task) -> None:
        ...


@register("sync")
class SyncExecutor(BaseExecutor):
    def execute(self, task: Task) -> None:
        logger.info("Syncing data for user=%s target=%s", task.user, task.target)
        # real sync logic would go here


@register("backup")
class BackupExecutor(BaseExecutor):
    def execute(self, task: Task) -> None:
        logger.info("Backing up user=%s target=%s", task.user, task.target)


@register("delete")
class DeleteExecutor(BaseExecutor):
    def execute(self, task: Task) -> None:
        logger.info("Deleting target=%s for user=%s", task.target, task.user)


class UnknownActionError(Exception):
    """Raised when a task's action has no registered executor."""


class ExecutorFactory:
    """Looks up (and allows registering) executor strategies by action name."""

    @staticmethod
    def get(action: str) -> BaseExecutor:
        executor_cls = _REGISTRY.get(action)
        if executor_cls is None:
            raise UnknownActionError(f"No executor registered for action '{action}'")
        return executor_cls()

    @staticmethod
    def register_executor(action: str, executor_cls: Type[BaseExecutor]) -> None:
        """Allow runtime/plugin registration without touching this file."""
        _REGISTRY[action] = executor_cls

    @staticmethod
    def available_actions() -> list:
        return sorted(_REGISTRY.keys())
