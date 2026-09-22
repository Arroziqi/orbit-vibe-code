from __future__ import annotations
import logging
from datetime import datetime, date, timedelta
from typing import Any

import pytest

from domain.models import User, Task, ExecutionOutcome, ExecutionResult
from domain.ports import Clock, ActionStrategy, QuotaContext
from domain.registry import ActionRegistry, UnknownActionError
from domain.strategies import SyncStrategy, BackupStrategy, DeleteStrategy
from infrastructure.clock import FixedClock
from infrastructure.config import load_users, load_tasks, build_action_registry, ConfigValidationError
from infrastructure.scheduler import DailyScheduler
from usecase.executor import TaskExecutor
from usecase.quota import QuotaService


class StubStrategy(ActionStrategy):
    def __init__(
        self,
        action_name: str,
        should_fail: bool = False,
        fail_message: str = "stub failure",
    ) -> None:
        self._action_name = action_name
        self._should_fail = should_fail
        self._fail_message = fail_message

    @property
    def action_name(self) -> str:
        return self._action_name

    def validate_params(self, params: dict[str, Any]) -> None:
        pass

    def execute(self, task: Task, quota_context: QuotaContext) -> ExecutionResult:
        if self._should_fail:
            raise RuntimeError(self._fail_message)
        return ExecutionResult(
            task=task,
            outcome=ExecutionOutcome.EXECUTED,
            message=f"Stub executed for {task.user}",
            executed_at=quota_context.execution_date,
        )


class TestQuotaBoundary:
    def test_quota_zero_all_skipped(self) -> None:
        clock = FixedClock(datetime(2024, 1, 15, 12, 0))
        users = {"alice": User("alice", daily_quota=0)}
        quota = QuotaService(users, clock)
        registry = build_action_registry()
        executor = TaskExecutor(quota, registry)
        task = Task("alice", "12:00", "sync", "/data/x", {})

        result = executor.execute(task)

        assert result.outcome == ExecutionOutcome.QUOTA_EXCEEDED
        assert "exceeded quota (0/0)" in result.message

    def test_quota_exact_at_limit_skipped(self) -> None:
        clock = FixedClock(datetime(2024, 1, 15, 12, 0))
        users = {"alice": User("alice", daily_quota=2)}
        quota = QuotaService(users, clock)
        registry = build_action_registry()
        executor = TaskExecutor(quota, registry)

        task1 = Task("alice", "12:00", "sync", "/data/x", {})
        task2 = Task("alice", "12:00", "sync", "/data/y", {})
        task3 = Task("alice", "12:00", "sync", "/data/z", {})

        r1 = executor.execute(task1)
        r2 = executor.execute(task2)
        r3 = executor.execute(task3)

        assert r1.outcome == ExecutionOutcome.EXECUTED
        assert r2.outcome == ExecutionOutcome.EXECUTED
        assert r3.outcome == ExecutionOutcome.QUOTA_EXCEEDED
        assert "exceeded quota (2/2)" in r3.message

    def test_quota_one_below_executed(self) -> None:
        clock = FixedClock(datetime(2024, 1, 15, 12, 0))
        users = {"alice": User("alice", daily_quota=3)}
        quota = QuotaService(users, clock)
        registry = build_action_registry()
        executor = TaskExecutor(quota, registry)

        task = Task("alice", "12:00", "sync", "/data/x", {})
        result = executor.execute(task)

        assert result.outcome == ExecutionOutcome.EXECUTED
        snap = quota.get_quota_snapshot("alice")
        assert snap["executed"] == 1
        assert snap["remaining"] == 2


class TestDailyRollover:
    def test_counter_resets_on_new_day(self) -> None:
        clock = FixedClock(datetime(2024, 1, 15, 12, 0))
        users = {"alice": User("alice", daily_quota=1)}
        quota = QuotaService(users, clock)
        registry = build_action_registry()
        executor = TaskExecutor(quota, registry)

        task = Task("alice", "12:00", "sync", "/data/x", {})

        r1 = executor.execute(task)
        assert r1.outcome == ExecutionOutcome.EXECUTED

        r2 = executor.execute(task)
        assert r2.outcome == ExecutionOutcome.QUOTA_EXCEEDED

        clock.advance_days(1)

        r3 = executor.execute(task)
        assert r3.outcome == ExecutionOutcome.EXECUTED


class TestDeterminism:
    def test_scheduler_same_clock_same_results(self) -> None:
        fixed = datetime(2024, 1, 15, 12, 0)
        clock1 = FixedClock(fixed)
        clock2 = FixedClock(fixed)

        users = {"alice": User("alice", daily_quota=5)}
        registry = build_action_registry()

        quota1 = QuotaService(users, clock1)
        executor1 = TaskExecutor(quota1, registry)
        scheduler1 = DailyScheduler(
            tasks=[Task("alice", "12:00", "sync", "/data/x", {})],
            executor=executor1,
            clock=clock1,
        )

        quota2 = QuotaService(users, clock2)
        executor2 = TaskExecutor(quota2, registry)
        scheduler2 = DailyScheduler(
            tasks=[Task("alice", "12:00", "sync", "/data/x", {})],
            executor=executor2,
            clock=clock2,
        )

        results1 = scheduler1.run_once()
        results2 = scheduler2.run_once()

        assert len(results1) == len(results2) == 1
        assert results1[0].outcome == results2[0].outcome == ExecutionOutcome.EXECUTED


class TestSimultaneousTasks:
    def test_multiple_tasks_same_time_independent_count(self) -> None:
        clock = FixedClock(datetime(2024, 1, 15, 12, 0))
        users = {"alice": User("alice", daily_quota=2)}
        quota = QuotaService(users, clock)
        registry = build_action_registry()
        executor = TaskExecutor(quota, registry)

        tasks = [
            Task("alice", "12:00", "sync", "/data/1", {}),
            Task("alice", "12:00", "backup", "/data/2", {"compression": "gzip"}),
            Task("alice", "12:00", "delete", "/data/3", {"force": True}),
        ]

        results = [executor.execute(t) for t in tasks]

        executed = [r for r in results if r.outcome == ExecutionOutcome.EXECUTED]
        skipped = [r for r in results if r.outcome == ExecutionOutcome.QUOTA_EXCEEDED]

        assert len(executed) == 2
        assert len(skipped) == 1
        assert "exceeded quota (2/2)" in skipped[0].message


class TestConfigValidation:
    def test_invalid_task_rejected(self) -> None:
        registry = build_action_registry()
        users = load_users({"alice": {"quota": 3}})

        with pytest.raises(ConfigValidationError, match="missing 'action'"):
            load_tasks([{"user": "alice", "time": "12:00", "target": "/data"}], set(users.keys()), registry)

    def test_unknown_user_rejected(self) -> None:
        registry = build_action_registry()
        users = load_users({"alice": {"quota": 3}})

        with pytest.raises(ConfigValidationError, match="not defined in users"):
            load_tasks([{"user": "bob", "time": "12:00", "action": "sync", "target": "/data"}], set(users.keys()), registry)

    def test_unknown_action_rejected(self) -> None:
        registry = build_action_registry()
        users = load_users({"alice": {"quota": 3}})

        with pytest.raises(ConfigValidationError, match="unknown action"):
            load_tasks([{"user": "alice", "time": "12:00", "action": "unknown", "target": "/data"}], set(users.keys()), registry)

    def test_invalid_params_rejected(self) -> None:
        registry = build_action_registry()
        users = load_users({"alice": {"quota": 3}})

        with pytest.raises(ConfigValidationError, match="compression must be"):
            load_tasks(
                [{"user": "alice", "time": "12:00", "action": "backup", "target": "/data", "params": {"compression": "zip"}}],
                set(users.keys()),
                registry,
            )


class TestExtensibility:
    def test_new_action_without_touching_executor_or_scheduler(self) -> None:
        clock = FixedClock(datetime(2024, 1, 15, 12, 0))
        users = {"alice": User("alice", daily_quota=1)}
        quota = QuotaService(users, clock)
        registry = ActionRegistry()
        registry.register(SyncStrategy())
        registry.register(StubStrategy("custom_action"))

        executor = TaskExecutor(quota, registry)
        scheduler = DailyScheduler(
            tasks=[Task("alice", "12:00", "custom_action", "/data/x", {})],
            executor=executor,
            clock=clock,
        )

        results = scheduler.run_once()

        assert len(results) == 1
        assert results[0].outcome == ExecutionOutcome.EXECUTED
        assert "Stub executed" in results[0].message


class TestTraceability:
    def test_every_outcome_has_complete_log_fields(self) -> None:
        clock = FixedClock(datetime(2024, 1, 15, 12, 0))
        users = {
            "alice": User("alice", daily_quota=2),
            "bob": User("bob", daily_quota=2),
        }
        quota = QuotaService(users, clock)
        registry = build_action_registry()
        executor = TaskExecutor(quota, registry)
        scheduler = DailyScheduler(
            tasks=[
                Task("bob", "13:00", "sync", "/data/z", {}),
            ],
            executor=executor,
            clock=clock,
        )

        r1 = executor.execute(Task("alice", "12:00", "sync", "/data/x", {}))
        r2 = executor.execute(Task("alice", "12:00", "sync", "/data/y", {}))
        clock.advance_minutes(60)
        r3_results = scheduler.run_once()
        r4 = executor.execute(Task("bob", "12:00", "backup", "/data/w", {"compression": "invalid"}))

        r3 = r3_results[0] if r3_results else None

        for r in [r1, r2, r3, r4]:
            log = r.to_log_dict()
            assert "user" in log
            assert "action" in log
            assert "target" in log
            assert "outcome" in log
            assert "log_message" in log
            assert "date" in log

        assert r1.outcome == ExecutionOutcome.EXECUTED
        assert r2.outcome == ExecutionOutcome.EXECUTED
        assert r3 is not None
        assert r3.outcome == ExecutionOutcome.EXECUTED
        assert r4.outcome == ExecutionOutcome.FAILED


class TestErrorIsolation:
    def test_failing_task_does_not_stop_siblings(self) -> None:
        clock = FixedClock(datetime(2024, 1, 15, 12, 0))
        users = {"alice": User("alice", daily_quota=3)}
        quota = QuotaService(users, clock)
        registry = ActionRegistry()
        registry.register(SyncStrategy())
        registry.register(StubStrategy("bad_action", should_fail=True))

        executor = TaskExecutor(quota, registry)
        scheduler = DailyScheduler(
            tasks=[
                Task("alice", "12:00", "sync", "/data/1", {}),
                Task("alice", "12:00", "bad_action", "/data/2", {}),
                Task("alice", "12:00", "sync", "/data/3", {}),
            ],
            executor=executor,
            clock=clock,
        )

        results = scheduler.run_once()

        outcomes = [r.outcome for r in results]
        assert outcomes == [
            ExecutionOutcome.EXECUTED,
            ExecutionOutcome.FAILED,
            ExecutionOutcome.EXECUTED,
        ]