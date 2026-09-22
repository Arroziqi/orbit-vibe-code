"""Entry point: wires User/Task/Executor/Scheduler together.

Equivalent behaviour to the original `run()` script, but modular and
configurable via plain dicts (as required by the refactor goals).
"""
import logging

from models import Task
from scheduler import Scheduler
from user_manager import UserManager

USERS_CONFIG = {
    "alice": {"quota": 3, "executed": 0},
    "bob": {"quota": 5, "executed": 0},
}

TASKS_CONFIG = [
    {"user": "alice", "time": "12:00", "action": "sync", "target": "/data/x"},
    {"user": "bob", "time": "12:00", "action": "backup", "target": "/srv/y"},
    {"user": "alice", "time": "12:00", "action": "delete", "target": "/tmp/z"},
]


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def build_scheduler() -> Scheduler:
    user_manager = UserManager.from_dict(USERS_CONFIG)
    tasks = [Task.from_dict(t) for t in TASKS_CONFIG]
    return Scheduler(user_manager=user_manager, tasks=tasks)


def main() -> None:
    configure_logging()
    scheduler = build_scheduler()
    # In production this would be called every minute by cron / a while-loop /
    # an APScheduler job. Here we force "now" for a deterministic demo run.
    scheduler.run_once(now="12:00")


if __name__ == "__main__":
    main()
