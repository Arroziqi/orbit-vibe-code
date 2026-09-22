"""Optional async execution version.

Useful once executors start doing real I/O (network calls, file transfer,
subprocess calls) -- tasks for different users can then run concurrently
instead of blocking one another.
"""
import asyncio
import datetime
import logging
from typing import List, Optional

from models import Task
from user_manager import QuotaExceededError, UnknownUserError, UserManager

logger = logging.getLogger(__name__)

_ASYNC_REGISTRY = {}


def register_async(action_name: str):
    def decorator(cls):
        _ASYNC_REGISTRY[action_name] = cls
        return cls

    return decorator


class AsyncBaseExecutor:
    async def execute(self, task: Task) -> None:
        raise NotImplementedError


@register_async("sync")
class AsyncSyncExecutor(AsyncBaseExecutor):
    async def execute(self, task: Task) -> None:
        logger.info("[async] Syncing data for user=%s target=%s", task.user, task.target)
        await asyncio.sleep(0)  # placeholder for real async I/O


@register_async("backup")
class AsyncBackupExecutor(AsyncBaseExecutor):
    async def execute(self, task: Task) -> None:
        logger.info("[async] Backing up user=%s target=%s", task.user, task.target)
        await asyncio.sleep(0)


@register_async("delete")
class AsyncDeleteExecutor(AsyncBaseExecutor):
    async def execute(self, task: Task) -> None:
        logger.info("[async] Deleting target=%s for user=%s", task.target, task.user)
        await asyncio.sleep(0)


class AsyncScheduler:
    def __init__(self, user_manager: UserManager, tasks: Optional[List[Task]] = None):
        self.user_manager = user_manager
        self.tasks: List[Task] = tasks or []

    def add_task(self, task: Task) -> None:
        self.tasks.append(task)

    def _due_tasks(self, now: str) -> List[Task]:
        return [t for t in self.tasks if t.time == now]

    async def run_once(self, now: Optional[str] = None) -> None:
        now = now or datetime.datetime.now().strftime("%H:%M")
        due = self._due_tasks(now)
        if not due:
            logger.debug("No tasks due at %s", now)
            return
        logger.info("%d task(s) due at %s (async)", len(due), now)
        # Run all due tasks concurrently; each one still enforces its own
        # user's quota synchronously before doing any work.
        await asyncio.gather(*(self._run_task(t) for t in due))

    async def _run_task(self, task: Task) -> None:
        try:
            self.user_manager.record_execution(task.user)
        except QuotaExceededError as exc:
            logger.warning(str(exc))
            return
        except UnknownUserError as exc:
            logger.error("Skipping task, %s", exc)
            return

        executor_cls = _ASYNC_REGISTRY.get(task.action)
        if executor_cls is None:
            logger.error("Skipping task %s: no async executor for '%s'", task, task.action)
            return

        try:
            await executor_cls().execute(task)
        except Exception:
            logger.exception("Unexpected error while executing task %s", task)
