import pytest

from deskagent.actions.system.audio import (
    DecreaseVolume, GetVolume, IncreaseVolume, Mute, SetVolume, Unmute,
)
from deskagent.actions.system.clipboard import CleanClipboard, GetClipboard, SetClipboard
from deskagent.actions.system.display import (
    GetDisplays, GetDisplayBrightness, GetScreenSize, SetDisplayBrightness
)
from deskagent.actions.system.information import (
    GetBatteryStatus, GetCPUInfo, GetCPUProcesses, GetCurrentDate, GetCurrentTime,
    GetDiskInfo, GetDiskProcesses, GetMemoryProcesses, GetOSInfo, GetUptime,
    GetUserInfo, SystemInfo,
)
from deskagent.actions.system.mouse import (
    Click, DoubleClick, DragMouse, GetCursorPosition, MoveMouse, ScrollMouse,
)
from deskagent.actions.system.network import (
    CheckInternetConnection, GetDefaultGateway, GetDNS, GetHostname,
    GetIPAddress, GetNetworkInterfaces, GetNetworkStatus, GetPublicIPAddress, PingHost,
)
from deskagent.actions.system.notification import ClearAgentNotification, SendNotification
from deskagent.actions.system.power import (
    CancelShutdownComputer, LockScreen, LogoutComputer, RestartComputer,
    ShutdownComputer, SleepComputer,
)
from deskagent.actions.types import ActionCategory, RiskLevel


ALL_ACTIONS = [
    SetVolume, IncreaseVolume, DecreaseVolume, Mute, Unmute, GetVolume,
    GetClipboard, SetClipboard, CleanClipboard,
    SetDisplayBrightness, GetDisplayBrightness, GetDisplays, GetScreenSize,
    GetCPUProcesses, GetMemoryProcesses, GetDiskProcesses, GetBatteryStatus, GetUptime,
    GetCurrentTime, GetCurrentDate, SystemInfo, GetCPUInfo, GetDiskInfo, GetOSInfo, GetUserInfo,
    GetCursorPosition, MoveMouse, Click, DoubleClick, DragMouse, ScrollMouse,
    GetNetworkStatus, GetIPAddress, GetHostname, GetNetworkInterfaces, GetPublicIPAddress,
    GetDefaultGateway, GetDNS, PingHost, CheckInternetConnection,
    SendNotification, ClearAgentNotification,
    LockScreen, SleepComputer, RestartComputer, ShutdownComputer, LogoutComputer,
    CancelShutdownComputer,
]


@pytest.mark.parametrize("action_class", ALL_ACTIONS)
def test_action_has_required_metadata(action_class):
    assert isinstance(action_class.name, str) and action_class.name
    assert isinstance(action_class.description, str) and action_class.description
    assert action_class.category is ActionCategory.SYSTEM
    assert isinstance(action_class.risk_level, RiskLevel)
    assert isinstance(action_class.requires_confirmation, bool)
    assert isinstance(action_class.reversible, bool)
    assert isinstance(action_class.parameters_schema, dict)


def test_action_names_are_unique():
    names = [action.name for action in ALL_ACTIONS]
    assert len(names) == len(set(names))
