from __future__ import annotations
import logging
from typing import Any

from domain.models import Task, ExecutionResult, ExecutionOutcome
from domain.ports import ActionStrategy, QuotaContext
from domain.registry import ActionRegistry, UnknownActionError, InvalidActionParamsError
from usecase.quota import QuotaService


class TaskExecutor:
    def __init__(
        self,
        quota_service: QuotaService,
        action_registry: ActionRegistry,
        logger: logging.Logger | None = None,
    ) -> None:
        self._quota_service = quota_service
        self._registry = action_registry
        self._logger = logger or logging.getLogger(__name__)

    def execute(self, task: Task) -> ExecutionResult:
        user_name = task.user

        allowed, executed, quota = self._quota_service.reserve_and_increment(user_name)
        if not allowed:
            result = ExecutionResult(
                task=task,
                outcome=ExecutionOutcome.QUOTA_EXCEEDED,
                message=f"User {user_name} exceeded quota ({executed}/{quota})",
                executed_at=self._quota_service._clock.now_date(),
            )
            self._log_execution(result)
            return result

        try:
            strategy = self._registry.get(task.action)
        except UnknownActionError as e:
            result = ExecutionResult(
                task=task,
                outcome=ExecutionOutcome.FAILED,
                message=f"Unknown action: {e.action_name}",
                executed_at=self._quota_service._clock.now_date(),
            )
            self._log_execution(result)
            return result

        try:
            strategy.validate_params(task.params)
        except InvalidActionParamsError as e:
            result = ExecutionResult(
                task=task,
                outcome=ExecutionOutcome.FAILED,
                message=str(e),
                executed_at=self._quota_service._clock.now_date(),
            )
            self._log_execution(result)
            return result

        quota_context = self._quota_service.build_quota_context(user_name)

        try:
            result = strategy.execute(task, quota_context)
        except Exception as e:
            result = ExecutionResult(
                task=task,
                outcome=ExecutionOutcome.FAILED,
                message=f"Execution error: {e}",
                executed_at=self._quota_service._clock.now_date(),
            )

        self._log_execution(result)
        return result

    def _log_execution(self, result: ExecutionResult) -> None:
        log_data = result.to_log_dict()
        if result.outcome == ExecutionOutcome.EXECUTED:
            self._logger.info("Task executed", extra=log_data)
        elif result.outcome == ExecutionOutcome.QUOTA_EXCEEDED:
            self._logger.warning("Task quota exceeded", extra=log_data)
        elif result.outcome == ExecutionOutcome.FAILED:
            self._logger.error("Task failed", extra=log_data)
        else:
            self._logger.debug("Task time miss", extra=log_data)