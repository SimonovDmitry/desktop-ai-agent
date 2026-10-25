"""Central safety boundary for every agent action."""

from deskagent.safety.audit import AuditLog, AuditRecord
from deskagent.safety.confirmation import ConfirmationRequest, PreviewBuilder
from deskagent.safety.guards import FilesystemGuard, ShellGuard
from deskagent.safety.limits import EmergencyStop, SafetyLimits
from deskagent.safety.policy import ActionPolicy, PolicyConfig, PolicyDecision

__all__ = [
    "ActionPolicy", "AuditLog", "AuditRecord", "ConfirmationRequest",
    "EmergencyStop", "FilesystemGuard", "PolicyConfig", "PolicyDecision",
    "PreviewBuilder", "SafetyLimits", "ShellGuard",
]
