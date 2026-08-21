from deskagent.actions.base import Action
from deskagent.actions.result import ActionResult
from deskagent.actions.context import ActionContext
from deskagent.actions.types import RiskLevel, ActionCategory


class GetCPUProcesses(Action):
    name = "get_cpu_processes"
    description = "Get the list of top processes sorted by CPU usage"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False

    def execute(self, context):
        try:
            processes = context.services.system.information.get_cpu_processes()
            return ActionResult(success=True, data={"processes": processes})

        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class GetMemoryProcesses(Action):
    name = "get_memory_processes"
    description = "Get the list of top processes sorted by memory usage"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False

    def execute(self, context):
        try:
            processes = context.services.system.information.get_memory_processes()
            return ActionResult(success=True, data={"processes": processes})

        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class GetDiskProcesses(Action):
    name = "get_disk_processes"
    description = "Get information about disk usage and heavy files/apps"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False

    def execute(self, context):
        try:
            disk_data = context.services.system.information.get_disk_processes()
            return ActionResult(success=True, data=disk_data)

        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class GetBatteryStatus(Action):
    name = "get_battery_status"
    description = "Get current battery percentage and charging status"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False

    def execute(self, context):
        try:
            battery = context.services.system.information.get_battery_status()
            return ActionResult(success=True, data=battery)

        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class GetUptime(Action):
    name = "get_uptime"
    description = "Get the system uptime and boot time"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False

    def execute(self, context):
        try:
            uptime = context.services.system.information.get_uptime()
            return ActionResult(success=True, data=uptime)

        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class GetCurrentTime(Action):
    name = "get_current_time"
    description = "Get the current system time"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False

    def execute(self, context):
        try:
            current_time = context.services.system.information.get_current_time()
            return ActionResult(success=True, data=current_time)

        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class GetCurrentDate(Action):
    name = "get_current_date"
    description = "Get the current system date"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False

    def execute(self, context):
        try:
            current_date = context.services.system.information.get_current_date()
            return ActionResult(success=True, data=current_date)

        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


# TODO: Реализовать общую информацию о системе
class SystemInfo(Action):
    name = "system_info"
    description = "Get comprehensive system information"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False

    def execute(self, context):
        try:
            info = context.services.system.information.system_info()
            return ActionResult(success=True, data=info)

        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


# TODO: Реализовать детальную информацию о процессоре
class GetCPUInfo(Action):
    name = "get_cpu_info"
    description = "Get detailed information about the CPU architecture and cores"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False

    def execute(self, context):
        try:
            cpu_info = context.services.system.information.get_cpu_info()
            return ActionResult(success=True, data=cpu_info)

        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


# TODO: Реализовать детальную информацию о дисковом оборудовании
class GetDiskInfo(Action):
    name = "get_disk_info"
    description = "Get detailed information about physical drives"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False

    def execute(self, context):
        try:
            disk_info = context.services.system.information.get_disk_info()
            return ActionResult(success=True, data=disk_info)

        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


# TODO: Реализовать информацию об ОС
class GetOSInfo(Action):
    name = "get_os_info"
    description = "Get detailed information about the Operating System"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False

    def execute(self, context):
        try:
            os_info = context.services.system.information.get_os_info()
            return ActionResult(success=True, data=os_info)

        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


# TODO: Реализовать информацию о текущем пользователе
class GetUserInfo(Action):
    name = "get_user_info"
    description = "Get information about the current system user"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False

    def execute(self, context):
        try:
            user_info = context.services.system.information.get_user_info()
            return ActionResult(success=True, data=user_info)

        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")