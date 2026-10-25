from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Iterable


SENSITIVE_KEYS = frozenset({
    "password", "passphrase", "token", "secret", "api_key", "authorization",
    "cookie", "private_key", "credential",
})


def redact(value: Any, key: str = "") -> Any:
    if key.casefold() in SENSITIVE_KEYS or any(token in key.casefold() for token in SENSITIVE_KEYS):
        return "***REDACTED***"
    if isinstance(value, dict):
        return {str(child_key): redact(child, str(child_key)) for child_key, child in value.items()}
    if isinstance(value, (list, tuple)):
        return [redact(child, key) for child in value]
    return value


@dataclass(frozen=True)
class ConfirmationRequest:
    confirmation_id: str
    question: str
    actions: tuple[dict[str, Any], ...]
    requires_explicit_text: bool = False
    required_phrase: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "confirmation_id": self.confirmation_id,
            "question": self.question,
            "actions": list(self.actions),
            "requires_explicit_text": self.requires_explicit_text,
            "required_phrase": self.required_phrase,
        }

    def verify(self, answer: Any) -> bool:
        if not isinstance(answer, dict):
            return bool(answer) and not self.requires_explicit_text
        if answer.get("confirmation_id") not in (None, self.confirmation_id):
            return False
        if not answer.get("approved", False):
            return False
        if self.requires_explicit_text:
            return answer.get("text") == self.required_phrase
        return True

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "ConfirmationRequest":
        return cls(
            str(value.get("confirmation_id", "")),
            str(value.get("question", "Approve actions?")),
            tuple(value.get("actions", ())),
            bool(value.get("requires_explicit_text", False)),
            value.get("required_phrase"),
        )


class PreviewBuilder:
    @classmethod
    def build(cls, calls: Iterable[dict[str, Any]]) -> ConfirmationRequest:
        actions = tuple(cls._action(call) for call in calls)
        canonical = json.dumps(actions, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
        confirmation_id = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:20]
        explicit = any(action.get("confirmation_kind") == "explicit_text" for action in actions)
        phrase = f"APPROVE {confirmation_id[-6:].upper()}" if explicit else None
        question = "Type the confirmation phrase to approve critical actions" if explicit else "Approve these actions?"
        return ConfirmationRequest(confirmation_id, question, actions, explicit, phrase)

    @staticmethod
    def _action(call: dict[str, Any]) -> dict[str, Any]:
        policy = call.get("policy", {})
        name = str(call.get("name", "unknown"))
        parameters = redact(call.get("args", {}))
        return {
            "id": call.get("id"),
            "action": name,
            "summary": PreviewBuilder._summary(name, parameters, policy.get("dry_run", False)),
            "parameters": parameters,
            "risk": policy.get("risk", "low"),
            "confirmation_kind": policy.get("confirmation_kind", "approve"),
            "dry_run": bool(policy.get("dry_run", False)),
        }

    @staticmethod
    def _summary(name: str, parameters: dict[str, Any], dry_run: bool) -> str:
        rendered = ", ".join(f"{key}={value!r}" for key, value in sorted(parameters.items()))
        prefix = "Simulate" if dry_run else "Execute"
        return f"{prefix} {name}" + (f" ({rendered})" if rendered else "")
