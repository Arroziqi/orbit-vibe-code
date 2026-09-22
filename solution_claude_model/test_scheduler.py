import logging
import unittest

from executors import ExecutorFactory, UnknownActionError
from models import Task
from scheduler import Scheduler
from user_manager import QuotaExceededError, UnknownUserError, UserManager

logging.disable(logging.CRITICAL)  # keep test output clean


class TaskModelTests(unittest.TestCase):
    def test_valid_task(self):
        t = Task(user="alice", time="12:00", action="sync", target="/data/x")
        self.assertEqual(t.user, "alice")

    def test_invalid_time_raises(self):
        with self.assertRaises(ValueError):
            Task(user="alice", time="25:99", action="sync", target="/data/x")

    def test_from_dict(self):
        t = Task.from_dict({"user": "bob", "time": "09:30", "action": "backup", "target": "/x"})
        self.assertEqual(t.action, "backup")
        self.assertEqual(t.params, {})


class UserManagerTests(unittest.TestCase):
    def setUp(self):
        self.um = UserManager.from_dict({"alice": {"quota": 2, "executed": 0}})

    def test_quota_enforced(self):
        self.um.record_execution("alice")
        self.um.record_execution("alice")
        with self.assertRaises(QuotaExceededError):
            self.um.record_execution("alice")

    def test_unknown_user_raises(self):
        with self.assertRaises(UnknownUserError):
            self.um.record_execution("nobody")

    def test_reset_daily(self):
        self.um.record_execution("alice")
        self.um.reset_daily()
        self.assertEqual(self.um.get("alice").executed, 0)


class ExecutorFactoryTests(unittest.TestCase):
    def test_known_action_returns_executor(self):
        executor = ExecutorFactory.get("sync")
        # Should not raise.
        executor.execute(Task(user="a", time="00:00", action="sync", target="/t"))

    def test_unknown_action_raises(self):
        with self.assertRaises(UnknownActionError):
            ExecutorFactory.get("teleport")


class SchedulerTests(unittest.TestCase):
    def setUp(self):
        self.um = UserManager.from_dict({"alice": {"quota": 1, "executed": 0}})
        self.scheduler = Scheduler(user_manager=self.um)
        self.scheduler.add_task(Task(user="alice", time="12:00", action="sync", target="/x"))
        self.scheduler.add_task(Task(user="alice", time="12:00", action="backup", target="/y"))

    def test_second_task_blocked_by_quota(self):
        self.scheduler.run_once(now="12:00")
        # quota was 1, so only one of the two 12:00 tasks should have consumed it
        self.assertEqual(self.um.get("alice").executed, 1)

    def test_no_tasks_due(self):
        self.scheduler.run_once(now="08:00")
        self.assertEqual(self.um.get("alice").executed, 0)

    def test_unknown_user_task_is_skipped_not_fatal(self):
        self.scheduler.add_task(Task(user="ghost", time="07:00", action="sync", target="/z"))
        # should not raise
        self.scheduler.run_once(now="07:00")


if __name__ == "__main__":
    unittest.main()
