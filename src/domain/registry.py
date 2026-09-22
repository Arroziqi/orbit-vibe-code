from __future__ import annotations
from typing import Any

from domain.ports import ActionStrategy


class ActionRegistry:
    def __init__(self) -> None:
        self._strategies: dict[str, ActionStrategy] = {}

    def register(self, strategy: ActionStrategy) -> None:
        self._strategies[strategy.action_name] = strategy

    def get(self, action_name: str) -> ActionStrategy:
        try:
            return self._strategies[action_name]
        except KeyError:
            raise UnknownActionError(action_name)

    def has(self, action_name: str) -> bool:
        return action_name in self._strategies


class UnknownActionError(Exception):
    def __init__(self, action_name: str) -> None:
        super().__init__(f"Unknown action: {action_name}")
        self.action_name = action_name


class InvalidActionParamsError(Exception):
    def __init__(self, action_name: str, message: str) -> None:
        super().__init__(f"Invalid params for action '{action_name}': {message}")
        self.action_name = action_name