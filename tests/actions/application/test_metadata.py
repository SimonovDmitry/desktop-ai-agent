import pytest

from deskagent.actions.application.documents import (
    OpenDocument,
    OpenMultipleDocuments,
    OpenURLWithApplication,
    RevealApplicationExecutable,
    RevealApplicationInFileManager,
)
from deskagent.actions.application.focus import (
    ActivateApplication,
    BringApplicationToFront,
    GetApplicationFocusState,
    GetApplicationVisibility,
    HideApplication,
    MinimizeApplication,
    RestoreApplication,
    ShowApplication,
)
from deskagent.actions.application.information import (
    FindApplications,
    GetActiveApplication,
    GetApplicationArchitecture,
    GetApplicationBundleId,
    GetApplicationExecutablePath,
    GetApplicationInfo,
    GetApplicationName,
    GetApplicationPath,
    GetApplicationPID,
    GetApplicationStatus,
    GetApplicationVersion,
    GetInstalledApplications,
    GetRunningApplications,
    IsApplicationRunning,
)
from deskagent.actions.application.instances import (
    ActivateApplicationInstance,
    GetApplicationInstanceCount,
    GetApplicationInstances,
    QuitApplicationInstance,
)
from deskagent.actions.application.lifecycle import (
    ForceQuitApplication,
    LaunchApplication,
    LaunchApplicationHidden,
    LaunchApplicationWithArguments,
    LaunchOrActivateApplication,
    QuitApplication,
    RestartApplication,
    WaitForApplication,
    WaitForApplicationExit,
)
from deskagent.actions.application.preferences import (
    GetAccessibilityPermission,
    GetApplicationPermissions,
    GetAutomationPermission,
    GetDefaultApplication,
    GetNotificationPermission,
    OpenApplicationPreferences,
    OpenApplicationSystemSettings,
    OpenWithApplication,
)
from deskagent.actions.application.processes import (
    GetApplicationChildProcesses,
    GetApplicationMainProcess,
    GetApplicationProcesses,
    GetApplicationProcessTree,
    ResumeApplication,
    SuspendApplication,
)
from deskagent.actions.application.resources import (
    GetApplicationCPUUsage,
    GetApplicationDiskUsage,
    GetApplicationMemoryUsage,
    GetApplicationResourceUsage,
    GetTopResourceApplications,
)
from deskagent.actions.application.startup import (
    AddApplicationToStartup,
    DisableApplicationStartup,
    EnableApplicationStartup,
    GetLoginItems,
    IsApplicationStartupEnabled,
    RemoveApplicationFromStartup,
)

ALL_APPLICATION_ACTIONS = [
    GetRunningApplications,
    GetInstalledApplications,
    FindApplications,
    GetApplicationInfo,
    GetApplicationStatus,
    IsApplicationRunning,
    GetActiveApplication,
    GetApplicationPID,
    GetApplicationPath,
    GetApplicationExecutablePath,
    GetApplicationBundleId,
    GetApplicationVersion,
    GetApplicationArchitecture,
    GetApplicationName,
    LaunchApplication,
    LaunchApplicationWithArguments,
    LaunchApplicationHidden,
    QuitApplication,
    ForceQuitApplication,
    RestartApplication,
    WaitForApplication,
    WaitForApplicationExit,
    LaunchOrActivateApplication,
    GetApplicationPermissions,
    GetAccessibilityPermission,
    GetAutomationPermission,
    GetNotificationPermission,
    GetDefaultApplication,
    OpenWithApplication,
    OpenApplicationPreferences,
    OpenApplicationSystemSettings,
    ActivateApplication,
    HideApplication,
    ShowApplication,
    MinimizeApplication,
    RestoreApplication,
    BringApplicationToFront,
    GetApplicationVisibility,
    GetApplicationFocusState,
    GetApplicationCPUUsage,
    GetApplicationMemoryUsage,
    GetApplicationDiskUsage,
    GetApplicationResourceUsage,
    GetTopResourceApplications,
    GetApplicationProcesses,
    GetApplicationProcessTree,
    GetApplicationMainProcess,
    GetApplicationChildProcesses,
    SuspendApplication,
    ResumeApplication,
    GetApplicationInstances,
    GetApplicationInstanceCount,
    ActivateApplicationInstance,
    QuitApplicationInstance,
    GetLoginItems,
    IsApplicationStartupEnabled,
    AddApplicationToStartup,
    RemoveApplicationFromStartup,
    EnableApplicationStartup,
    DisableApplicationStartup,
    OpenDocument,
    OpenMultipleDocuments,
    OpenURLWithApplication,
    RevealApplicationInFileManager,
    RevealApplicationExecutable,
]


def test_all_application_actions_have_unique_names():
    names = [cls.name for cls in ALL_APPLICATION_ACTIONS]
    assert len(names) == len(set(names))
    assert all(names)


@pytest.mark.parametrize("action_cls", ALL_APPLICATION_ACTIONS)
def test_every_application_action_has_required_metadata(action_cls):
    action = action_cls()

    assert isinstance(action.name, str) and action.name
    assert isinstance(action.description, str) and action.description
    assert action.category is not None
    assert action.risk_level is not None
    assert isinstance(action.requires_confirmation, bool)
    assert isinstance(action.reversible, bool)
    assert isinstance(action.parameters_schema, dict)


@pytest.mark.parametrize(
    "action_cls",
    [ForceQuitApplication, SuspendApplication, AddApplicationToStartup],
)
def test_high_impact_application_actions_require_confirmation(action_cls):
    assert action_cls().requires_confirmation is True


@pytest.mark.parametrize(
    "action_cls",
    [
        LaunchApplication,
        LaunchApplicationWithArguments,
        LaunchApplicationHidden,
        QuitApplication,
        RestartApplication,
        WaitForApplication,
        WaitForApplicationExit,
        LaunchOrActivateApplication,
        ResumeApplication,
        ActivateApplication,
        HideApplication,
        ShowApplication,
        MinimizeApplication,
        RestoreApplication,
        BringApplicationToFront,
    ],
)
def test_actions_without_declared_confirmation_keep_it_disabled(action_cls):
    assert action_cls().requires_confirmation is False
