from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from deskagent.actions.types import RiskLevel
from deskagent.safety.guards import FilesystemGuard, ShellGuard


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool = True
    confirmation_required: bool = False
    reason: str | None = None
    reason_code: str | None = None
    dry_run: bool = False
    risk: RiskLevel = RiskLevel.LOW
    confirmation_kind: str = "none"

    def to_dict(self) -> dict[str, Any]:
        result = {key: getattr(self, key) for key in self.__dataclass_fields__}
        result["risk"] = self.risk.value
        return result


@dataclass
class PolicyConfig:
    dry_run: bool = False
    strict_mode: bool = False
    max_actions: int = 24
    allow_shell: bool = False
    shell_allowed_commands: tuple[str, ...] = ()
    shell_allow_metacharacters: bool = False
    confirm_medium: bool = False
    confirm_risks: tuple[RiskLevel, ...] = (RiskLevel.HIGH, RiskLevel.CRITICAL)
    confirm_actions: tuple[str, ...] = ()
    allowed_applications: tuple[str, ...] = ()
    allowed_paths: tuple[str, ...] = ()
    blocked_paths: tuple[str, ...] = field(default_factory=lambda: (
        "~/.ssh", "~/.gnupg", "~/.aws", "~/Library/Keychains", "/System", "/etc",
    ))


class ActionPolicy:
    """One fail-closed decision point between model output and execution."""

    CONFIRM_TOKENS = frozenset({
        "delete", "remove", "trash", "overwrite", "replace", "clear", "empty_trash",
        "send_message", "send_mail", "email", "submit", "publish", "purchase", "payment",
    })
    CRITICAL_TOKENS = frozenset({
        "camera", "webcam", "keychain", "password", "credential", "privacy",
        "screen_recording", "microphone_permission", "format_disk",
    })

    def __init__(self, config: PolicyConfig | None = None):
        self.config = config or PolicyConfig()
        self.files = FilesystemGuard(self.config.allowed_paths, self.config.blocked_paths)
        self.shell = ShellGuard(
            self.config.allow_shell,
            self.config.shell_allowed_commands,
            self.config.shell_allow_metacharacters,
        )

    def evaluate(self, action_class, parameters: dict, action_count=0) -> PolicyDecision:
        name = action_class.name.casefold()
        risk = self._effective_risk(action_class.risk_level, name, parameters)
        if action_count >= self.config.max_actions:
            return self._deny("Action limit exceeded", "ACTION_LIMIT", risk)

        shell_result = self.shell.check(name, parameters)
        if not shell_result.allowed:
            return self._deny(shell_result.reason, shell_result.code, risk)
        file_result = self.files.check(name, parameters)
        if not file_result.allowed:
            return self._deny(file_result.reason, file_result.code, risk)

        application = self._application(parameters)
        if application and self.config.allowed_applications:
            allowed = {item.casefold() for item in self.config.allowed_applications}
            if application.casefold() not in allowed:
                return self._deny(f"Application is not allowed: {application}", "APP_NOT_ALLOWED", risk)

        semantic_confirmation = any(token in name for token in self.CONFIRM_TOKENS)
        if name in {"write_file", "write_text_file"}:
            semantic_confirmation = bool(parameters.get("overwrite", True))
        medium_confirmation = risk is RiskLevel.MEDIUM and (
            self.config.strict_mode or self.config.confirm_medium
        )
        confirm = (
            action_class.requires_confirmation
            or risk in self.config.confirm_risks
            or medium_confirmation
            or name in self.config.confirm_actions
            or semantic_confirmation
            or self.shell.is_shell_action(name)
        )
        kind = "explicit_text" if risk is RiskLevel.CRITICAL else ("approve" if confirm else "none")
        return PolicyDecision(True, confirm, dry_run=self.config.dry_run, risk=risk, confirmation_kind=kind)

    @classmethod
    def _effective_risk(cls, declared: RiskLevel, name: str, parameters: dict[str, Any]) -> RiskLevel:
        if any(token in name for token in cls.CRITICAL_TOKENS):
            return RiskLevel.CRITICAL
        if ShellGuard.is_shell_action(name):
            command = str(parameters.get("command") or parameters.get("cmd") or "")
            if any(pattern.search(command) for pattern in ShellGuard.CRITICAL_PATTERNS):
                return RiskLevel.CRITICAL
            return max(declared, RiskLevel.HIGH, key=cls._risk_rank)
        if any(token in name for token in cls.CONFIRM_TOKENS):
            return max(declared, RiskLevel.HIGH, key=cls._risk_rank)
        return declared

    @staticmethod
    def _risk_rank(risk: RiskLevel) -> int:
        return list(RiskLevel).index(risk)

    @staticmethod
    def _application(parameters):
        for key in ("application", "app", "bundle_id"):
            value = parameters.get(key)
            if isinstance(value, str) and value:
                return value
        return None

    @staticmethod
    def _deny(reason: str | None, code: str | None, risk: RiskLevel) -> PolicyDecision:
        return PolicyDecision(False, reason=reason, reason_code=code, risk=risk)
