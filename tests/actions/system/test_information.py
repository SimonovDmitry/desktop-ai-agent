import pytest

from deskagent.actions.system.information import (
    GetBatteryStatus,
    GetCPUInfo,
    GetCPUProcesses,
    GetCurrentDate,
    GetCurrentTime,
    GetDiskInfo,
    GetDiskProcesses,
    GetMemoryProcesses,
    GetOSInfo,
    GetUptime,
    GetUserInfo,
    SystemInfo,
)
from tests.conftest import assert_error, assert_success


@pytest.mark.parametrize(
    ("action_class", "method", "return_value"),
    [
        (GetCPUProcesses, "get_cpu_processes", [{"pid": 1, "cpu": 10.0}]),
        (GetMemoryProcesses, "get_memory_processes", [{"pid": 1, "memory": 100}]),
        (GetDiskProcesses, "get_disk_processes", {"disk": {"percent": "50%"} }),
        (GetBatteryStatus, "get_battery_status", {"percentage": 80, "charging": True}),
        (GetUptime, "get_uptime", {"seconds": 123, "boot_time": "2025-01-01T00:00:00"}),
        (GetCurrentTime, "get_current_time", {"time": "12:34:56"}),
        (GetCurrentDate, "get_current_date", {"date": "Monday January 01"}),
        (SystemInfo, "system_info", {"os": "macOS"}),
        (GetCPUInfo, "get_cpu_info", {"cores": 8}),
        (GetDiskInfo, "get_disk_info", {"disks": []}),
        (GetOSInfo, "get_os_info", {"name": "macOS"}),
        (GetUserInfo, "get_user_info", {"name": "tester"}),
    ],
)
def test_information_action_success(context, action_class, method, return_value):
    getattr(context.services.system.information, method).return_value = return_value
    result = action_class().execute(context, {})
    assert_success(result, return_value)
    getattr(context.services.system.information, method).assert_called_once_with()


@pytest.mark.parametrize(
    ("action_class", "method"),
    [
        (GetCPUProcesses, "get_cpu_processes"),
        (GetMemoryProcesses, "get_memory_processes"),
        (GetDiskProcesses, "get_disk_processes"),
        (GetBatteryStatus, "get_battery_status"),
        (GetUptime, "get_uptime"),
        (GetCurrentTime, "get_current_time"),
        (GetCurrentDate, "get_current_date"),
        (SystemInfo, "system_info"),
        (GetCPUInfo, "get_cpu_info"),
        (GetDiskInfo, "get_disk_info"),
        (GetOSInfo, "get_os_info"),
        (GetUserInfo, "get_user_info"),
    ],
)
def test_information_action_system_error(context, action_class, method):
    getattr(context.services.system.information, method).side_effect = RuntimeError("info failed")
    result = action_class().execute(context, {})
    assert_error(result, "SYSTEM_ERROR")
