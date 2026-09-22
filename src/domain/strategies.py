from __future__ import annotations
from datetime import date
from typing import Any

from domain.models import ExecutionOutcome, Task, ExecutionResult
from domain.ports import ActionStrategy, QuotaContext
from domain.registry import InvalidActionParamsError


class SyncStrategy(ActionStrategy):
    @property
    def action_name(self) -> str:
        return "sync"

    def validate_params(self, params: dict[str, Any]) -> None:
        pass

    def execute(
        self,
        task: Task,
        quota_context: QuotaContext,
    ) -> ExecutionResult:
        return ExecutionResult(
            task=task,
            outcome=ExecutionOutcome.EXECUTED,
            message=f"Synced {task.target} for {task.user}",
            executed_at=quota_context.execution_date,
        )


class BackupStrategy(ActionStrategy):
    @property
    def action_name(self) -> str:
        return "backup"

    def validate_params(self, params: dict[str, Any]) -> None:
        if "compression" in params and params["compression"] not in ("gzip", "none"):
            raise InvalidActionParamsError(
                self.action_name, "compression must be 'gzip' or 'none'"
            )

    def execute(
        self,
        task: Task,
        quota_context: QuotaContext,
    ) -> ExecutionResult:
        compression = task.params.get("compression", "none")
        return ExecutionResult(
            task=task,
            outcome=ExecutionOutcome.EXECUTED,
            message=f"Backed up {task.target} for {task.user} (compression={compression})",
            executed_at=quota_context.execution_date,
        )


class DeleteStrategy(ActionStrategy):
    @property
    def action_name(self) -> str:
        return "delete"

    def validate_params(self, params: dict[str, Any]) -> None:
        if "force" in params and not isinstance(params["force"], bool):
            raise InvalidActionParamsError(
                self.action_name, "force must be a boolean"
            )

    def execute(
        self,
        task: Task,
        quota_context: QuotaContext,
    ) -> ExecutionResult:
        force = task.params.get("force", False)
        return ExecutionResult(
            task=task,
            outcome=ExecutionOutcome.EXECUTED,
            message=f"Deleted {task.target} for {task.user} (force={force})",
            executed_at=quota_context.execution_date,
        )