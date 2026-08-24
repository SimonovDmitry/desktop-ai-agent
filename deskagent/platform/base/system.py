from abc import ABC, abstractmethod


class SystemAudio(ABC):
    @abstractmethod
    def set_volume(self, volume):
        pass

    @abstractmethod
    def increase_volume(self, step=10):
        pass

    @abstractmethod
    def mute(self):
        pass

    @abstractmethod
    def decrease_volume(self, step=10):
        pass

    @abstractmethod
    def unmute(self):
        pass

    @abstractmethod
    def get_volume(self):
        pass


class SystemClipboard(ABC):
    @abstractmethod
    def get_clipboard(self):
        pass

    @abstractmethod
    def set_clipboard(self, text):
        pass

    @abstractmethod
    def clean_clipboard(self):
        pass


class SystemDisplay(ABC):
    @abstractmethod
    def set_display_brightness(self, brightness_level):
        pass

    # TODO
    @abstractmethod
    def get_display_brightness(self):
        pass

    @abstractmethod
    def get_displays(self):
        pass

    @abstractmethod
    def get_screen_size(self, display_id=1):
        pass


class SystemInformation(ABC):
    @abstractmethod
    def get_cpu_processes(self):
        pass

    @abstractmethod
    def get_memory_processes(self):
        pass

    @abstractmethod
    def get_disk_processes(self):
        pass

    @abstractmethod
    def get_battery_status(self):
        pass

    @abstractmethod
    def get_uptime(self):
        pass

    @abstractmethod
    def get_current_time(self):
        pass

    @abstractmethod
    def get_current_date(self):
        pass

    @abstractmethod
    def system_info(self):
        pass

    @abstractmethod
    def get_cpu_info(self):
        pass

    @abstractmethod
    def get_disk_info(self):
        pass

    @abstractmethod
    def get_os_info(self):
        pass

    @abstractmethod
    def get_user_info(self):
        pass


class SystemMouse(ABC):
    @abstractmethod
    def get_cursor_position(self):
        pass

    @abstractmethod
    def move_mouse(self, x, y):
        pass

    @abstractmethod
    def click(self, button="left"):
        pass

    @abstractmethod
    def double_click(self, button="left"):
        pass

    @abstractmethod
    def drag_mouse(self, x1, y1, x2, y2):
        pass

    @abstractmethod
    def scroll_mouse(self, clicks):
        pass


class SystemNetwork(ABC):
    @abstractmethod
    def get_network_status(self):
        pass

    @abstractmethod
    def get_ip_address(self, target_iface):
        pass

    @abstractmethod
    def get_hostname(self):
        pass

    @abstractmethod
    def get_network_interfaces(self):
        pass

    @abstractmethod
    def get_public_ip_address(self):
        pass

    @abstractmethod
    def get_default_gateway(self):
        pass

    @abstractmethod
    def get_dns(self):
        pass

    @abstractmethod
    def ping_host(self, host):
        pass

    @abstractmethod
    def check_internet_connection(self):
        pass


class SystemNotification(ABC):
    @abstractmethod
    def send_notification(self):
        pass

    @abstractmethod
    def clear_agent_notification(self):
        pass


class SystemPower(ABC):
    @abstractmethod
    def lock_screen(self):
        pass

    @abstractmethod
    def sleep_computer(self):
        pass

    @abstractmethod
    def restart_computer(self):
        pass

    @abstractmethod
    def shutdown_computer(self):
        pass

    @abstractmethod
    def logout_computer(self):
        pass

    @abstractmethod
    def cancel_shutdown_computer(self):
        pass