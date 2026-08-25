from abc import ABC, abstractmethod


class ApplicationLifecycle(ABC):
    @abstractmethod
    def launch(self, app_name, arguments=None):
        pass

    @abstractmethod
    def launch_hidden(self, app_name):
        pass

    @abstractmethod
    def quit(self, app_name):
        pass

    @abstractmethod
    def force_quit(self, identifier):
        pass

    @abstractmethod
    def restart(self, app_name):
        pass

    @abstractmethod
    def wait_for_start(self, app_name, timeout=30):
        pass

    @abstractmethod
    def wait_for_exit(self, app_name, timeout=30):
        pass

    @abstractmethod
    def launch_or_activate(self, app_name):
        pass


class ApplicationInformation(ABC):
    @abstractmethod
    def get_running(self):
        pass

    @abstractmethod
    def get_installed(self):
        pass

    @abstractmethod
    def find(self, query, limit=10):
        pass

    @abstractmethod
    def get_info(self, app_name):
        pass

    @abstractmethod
    def get_status(self, app_name):
        pass

    @abstractmethod
    def is_running(self, app_name):
        pass

    @abstractmethod
    def get_active(self):
        pass

    @abstractmethod
    def get_pid(self, app_name):
        pass

    @abstractmethod
    def get_path(self, app_name):
        pass

    @abstractmethod
    def get_executable_path(self, app_name):
        pass

    @abstractmethod
    def get_bundle_id(self, app_name):
        pass

    @abstractmethod
    def get_version(self, app_name):
        pass

    @abstractmethod
    def get_architecture(self, app_name):
        pass

    @abstractmethod
    def get_name_from_id(self, identifier_type, identifier):
        pass


class ApplicationFocus(ABC):
    @abstractmethod
    def activate(self, app_name):
        pass

    @abstractmethod
    def hide(self, app_name):
        pass

    @abstractmethod
    def show(self, app_name):
        pass

    @abstractmethod
    def minimize(self, app_name):
        pass

    @abstractmethod
    def restore(self, app_name):
        pass

    @abstractmethod
    def bring_to_front(self, app_name):
        pass

    @abstractmethod
    def get_visibility(self, app_name):
        pass

    @abstractmethod
    def is_focused(self, app_name):
        pass


class ApplicationPreferences(ABC):
    @abstractmethod
    def get_permissions(self, app_name):
        pass

    @abstractmethod
    def get_accessibility_status(self, app_name):
        pass

    @abstractmethod
    def get_automation_status(self, app_name):
        pass

    @abstractmethod
    def get_notification_status(self, app_name):
        pass

    @abstractmethod
    def get_default_app(self, file_type):
        pass

    @abstractmethod
    def open_with(self, path, app_name):
        pass

    @abstractmethod
    def open_app_prefs(self, app_name):
        pass

    @abstractmethod
    def open_system_settings(self, app_name, section):
        pass


class ApplicationResources(ABC):
    @abstractmethod
    def get_cpu_usage(self, app_name):
        pass

    @abstractmethod
    def get_memory_usage(self, app_name):
        pass

    @abstractmethod
    def get_disk_usage(self, app_name):
        pass

    @abstractmethod
    def get_resource_usage(self, app_name):
        pass

    @abstractmethod
    def get_top_resource_apps(self, resource_type, limit=10):
        pass


class ApplicationProcesses(ABC):
    @abstractmethod
    def get_processes(self, app_name):
        pass

    @abstractmethod
    def get_tree(self, app_name):
        pass

    @abstractmethod
    def get_main(self, app_name):
        pass

    @abstractmethod
    def get_children(self, app_name):
        pass

    @abstractmethod
    def suspend(self, app_name):
        pass

    @abstractmethod
    def resume(self, app_name):
        pass


class ApplicationInstances(ABC):
    @abstractmethod
    def get_all(self, app_name):
        pass

    @abstractmethod
    def get_count(self, app_name):
        pass

    @abstractmethod
    def activate(self, pid):
        pass

    @abstractmethod
    def quit(self, pid):
        pass


class ApplicationDocuments(ABC):
    @abstractmethod
    def open(self, path):
        pass

    @abstractmethod
    def open_multiple(self, paths):
        pass

    @abstractmethod
    def open_url_with(self, url, app_name):
        pass

    @abstractmethod
    def reveal_app(self, app_name):
        pass

    @abstractmethod
    def reveal_executable(self, app_name):
        pass


class ApplicationStartup(ABC):
    @abstractmethod
    def get_all(self):
        pass

    @abstractmethod
    def is_enabled(self, app_name):
        pass

    @abstractmethod
    def add(self, app_name):
        pass

    @abstractmethod
    def remove(self, app_name):
        pass

    @abstractmethod
    def enable(self, app_name):
        pass

    @abstractmethod
    def disable(self, app_name):
        pass