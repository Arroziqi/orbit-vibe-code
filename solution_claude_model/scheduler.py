"""Scheduling system: decides which tasks are due and dispatches them."""
import datetime
import logging
from typing import List, Optional

from executors import ExecutorFactory, UnknownActionError
from models import Task
from user_manager import QuotaExceededError, UnknownUserError, UserManager

logger = logging.getLogger(__name__)


class Scheduler:
    """Simple polling-style scheduler.

    Call `run_once()` on a timer (e.g. every minute via cron/while-loop) and
    it will execute every task whose `time` matches the current clock.
    """

    def __init__(self, user_manager: UserManager, tasks: Optional[List[Task]] = None):
        self.user_manager = user_manager
        self.tasks: List[Task] = tasks or []

    def add_task(self, task: Task) -> None:
        self.tasks.append(task)

    def tasks_for_user(self, user: str) -> List[Task]:
        return [t for t in self.tasks if t.user == user]

    def _due_tasks(self, now: str) -> List[Task]:
        return [t for t in self.tasks if t.time == now]

    def run_once(self, now: Optional[str] = None) -> None:
        """Run whatever is due at `now` (defaults to the current wall clock)."""
        now = now or datetime.datetime.now().strftime("%H:%M")
        due = self._due_tasks(now)
        if not due:
            logger.debug("No tasks due at %s", now)
            return
        logger.info("%d task(s) due at %s", len(due), now)
        for task in due:
            self._run_task(task)

    def _run_task(self, task: Task) -> None:
        # 1) Quota check
        try:
            self.user_manager.record_execution(task.user)
        except QuotaExceededError as exc:
            logger.warning(str(exc))
            return
        except UnknownUserError as exc:
            logger.error("Skipping task, %s", exc)
            return

        # 2) Dispatch to the right strategy
        try:
            executor = ExecutorFactory.get(task.action)
            executor.execute(task)
        except UnknownActionError as exc:
            logger.error("Skipping task %s: %s", task, exc)
        except Exception:  # defensive: one bad task must not kill the loop
            logger.exception("Unexpected error while executing task %s", task)
