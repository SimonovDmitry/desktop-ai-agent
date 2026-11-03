"""Central safety boundary for every agent action."""

from deskagent.privacy.audit import AuditLog, AuditRecord
from deskagent.privacy.confirmation import ConfirmationRequest, PreviewBuilder
from deskagent.privacy.guards import FilesystemGuard, ShellGuard
from deskagent.privacy.limits import EmergencyStop, SafetyLimits
from deskagent.privacy.policy import ActionPolicy, PolicyConfig, PolicyDecision

__all__ = [
    "ActionPolicy", "AuditLog", "AuditRecord", "ConfirmationRequest",
    "EmergencyStop", "FilesystemGuard", "PolicyConfig", "PolicyDecision",
    "PreviewBuilder", "SafetyLimits", "ShellGuard",
]
