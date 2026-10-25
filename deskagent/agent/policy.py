from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from deskagent.actions.types import RiskLevel


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool = True
    confirmation_required: bool = False
    reason: str | None = None
    dry_run: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {key: getattr(self, key) for key in self.__dataclass_fields__}


@dataclass
class PolicyConfig:
    dry_run: bool = False
    max_actions: int = 24
    allow_shell: bool = False
    confirm_risks: tuple[RiskLevel, ...] = (RiskLevel.HIGH, RiskLevel.CRITICAL)
    confirm_actions: tuple[str, ...] = ()
    allowed_applications: tuple[str, ...] = ()
    allowed_paths: tuple[str, ...] = ()
    blocked_paths: tuple[str, ...] = field(default_factory=lambda: (
        "~/.ssh", "~/.gnupg", "~/Library/Keychains", "/System", "/Library",
    ))


class ActionPolicy:
    PATH_KEYS = {"path", "file", "directory", "source", "destination", "target"}
    SHELL_NAMES = {"shell", "command", "terminal", "subprocess", "execute_process", "run_command"}
    CONFIRM_TOKENS = {"delete", "overwrite", "replace", "clear", "empty_trash", "send_message",
                      "send_mail", "submit", "publish", "purchase", "payment"}

    def __init__(self, config: PolicyConfig | None = None):
        self.config = config or PolicyConfig()

    def evaluate(self, action_class, parameters: dict, action_count=0) -> PolicyDecision:
        if action_count >= self.config.max_actions:
            return PolicyDecision(False, reason="Action limit exceeded")
        name = action_class.name.lower()
        if not self.config.allow_shell and any(token in name for token in self.SHELL_NAMES):
            return PolicyDecision(False, reason="Arbitrary shell execution is disabled")
        application = self._application(parameters)
        if application and self.config.allowed_applications:
            allowed = {item.casefold() for item in self.config.allowed_applications}
            if application.casefold() not in allowed:
                return PolicyDecision(False, reason=f"Application is not allowed: {application}")
        blocked = self._blocked_path(parameters)
        if blocked:
            return PolicyDecision(False, reason=f"Path is blocked by policy: {blocked}")
        if self.config.allowed_paths and self._outside_allowed_paths(parameters):
            return PolicyDecision(False, reason="Path is outside allowed directories")
        semantic = any(token in name for token in self.CONFIRM_TOKENS)
        if name in {"write_file", "write_text_file"}:
            semantic = parameters.get("overwrite", True)
        confirm = (action_class.requires_confirmation or action_class.risk_level in self.config.confirm_risks
                   or name in self.config.confirm_actions or semantic)
        return PolicyDecision(confirmation_required=confirm, dry_run=self.config.dry_run)

    @staticmethod
    def _application(parameters):
        for key in ("application", "app", "bundle_id"):
            value = parameters.get(key)
            if isinstance(value, str) and value:
                return value
        return None

    def _blocked_path(self, parameters):
        for value in self._paths(parameters):
            for blocked in self.config.blocked_paths:
                if self._inside(value, Path(blocked).expanduser()):
                    return str(value)
        return None

    def _outside_allowed_paths(self, parameters):
        allowed = [Path(path).expanduser().resolve() for path in self.config.allowed_paths]
        return any(not any(self._inside(path, root) for root in allowed) for path in self._paths(parameters))

    def _paths(self, value, key=""):
        if isinstance(value, dict):
            for child_key, child in value.items():
                yield from self._paths(child, child_key.lower())
        elif isinstance(value, list):
            for child in value:
                yield from self._paths(child, key)
        elif isinstance(value, str) and any(token in key for token in self.PATH_KEYS):
            yield Path(value).expanduser().resolve()

    @staticmethod
    def _inside(path: Path, root: Path) -> bool:
        try:
            path.resolve().relative_to(root.resolve())
            return True
        except ValueError:
            return False
