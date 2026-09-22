"""User management & daily quota control."""
import logging
from dataclasses import dataclass
from typing import Dict

logger = logging.getLogger(__name__)


class QuotaExceededError(Exception):
    """Raised when a user attempts to run a task beyond their daily quota."""


class UnknownUserError(Exception):
    """Raised when a task references a user that hasn't been registered."""


@dataclass
class User:
    name: str
    quota: int
    executed: int = 0

    def has_quota(self) -> bool:
        return self.executed < self.quota

    def consume(self) -> None:
        self.executed += 1

    def remaining(self) -> int:
        return max(self.quota - self.executed, 0)


class UserManager:
    """Owns the set of known users and enforces their execution quotas.

    Kept deliberately independent of *what* is being executed -- it only
    knows about users and counts, so it can be reused by any scheduler.
    """

    def __init__(self) -> None:
        self._users: Dict[str, User] = {}

    def add_user(self, name: str, quota: int) -> User:
        user = User(name=name, quota=quota)
        self._users[name] = user
        return user

    def get(self, name: str) -> User:
        try:
            return self._users[name]
        except KeyError as exc:
            raise UnknownUserError(f"Unknown user: {name}") from exc

    def can_execute(self, name: str) -> bool:
        return self.get(name).has_quota()

    def record_execution(self, name: str) -> None:
        """Consume one unit of quota, or raise if none is left."""
        user = self.get(name)
        if not user.has_quota():
            raise QuotaExceededError(
                f"{name} has exceeded quota ({user.executed}/{user.quota})."
            )
        user.consume()

    def reset_daily(self) -> None:
        """Call once per day (e.g. via cron/midnight job) to roll quotas over."""
        for user in self._users.values():
            user.executed = 0
        logger.info("Daily quotas reset for %d user(s).", len(self._users))

    @classmethod
    def from_dict(cls, data: Dict[str, dict]) -> "UserManager":
        """Build from the legacy-style dict:
        {'alice': {'quota': 3, 'executed': 0}, ...}
        """
        manager = cls()
        for name, info in data.items():
            user = manager.add_user(name, info.get("quota", 0))
            user.executed = info.get("executed", 0)
        return manager
