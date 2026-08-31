from abc import ABC, abstractmethod


class WindowInformation(ABC):
    @abstractmethod
    def get_windows(self):
        pass

    @abstractmethod
    def get_window(self, window_id):
        pass

    @abstractmethod
    def find_windows(self, query):
        pass

    @abstractmethod
    def get_active_window(self):
        pass

    @abstractmethod
    def get_window_title(self, window_id):
        pass

    @abstractmethod
    def get_window_position(self, window_id):
        pass

    @abstractmethod
    def get_window_size(self, window_id):
        pass

    @abstractmethod
    def get_window_bounds(self, window_id):
        pass

    @abstractmethod
    def get_window_state(self, window_id):
        pass

    @abstractmethod
    def get_window_application(self, window_id):
        pass

    @abstractmethod
    def get_window_pid(self, window_id):
        pass

    @abstractmethod
    def is_window_visible(self, window_id):
        pass


class WindowFocus(ABC):
    @abstractmethod
    def activate(self, window_id):
        pass

    @abstractmethod
    def focus(self, window_id):
        pass

    @abstractmethod
    def bring_to_front(self, window_id):
        pass

    @abstractmethod
    def send_to_back(self, window_id):
        pass

    @abstractmethod
    def maximize(self, window_id):
        pass

    @abstractmethod
    def unmaximize(self, window_id):
        pass

    @abstractmethod
    def toggle_maximize(self, window_id):
        pass


class WindowPosition(ABC):
    @abstractmethod
    def move(self, window_id, dx, dy):
        pass

    @abstractmethod
    def move_to(self, window_id, x, y):
        pass

    @abstractmethod
    def center(self, window_id):
        pass

    @abstractmethod
    def center_on_display(self, window_id, display_id):
        pass

    @abstractmethod
    def move_to_display(self, window_id, display_id):
        pass

    @abstractmethod
    def snap_left(self, window_id):
        pass

    @abstractmethod
    def snap_right(self, window_id):
        pass

    @abstractmethod
    def snap_top(self, window_id):
        pass

    @abstractmethod
    def snap_bottom(self, window_id):
        pass

    @abstractmethod
    def restore_position(self, window_id):
        pass


class WindowSize(ABC):
    @abstractmethod
    def resize(self, window_id, delta_width, delta_height):
        pass

    @abstractmethod
    def resize_to(self, window_id, width, height):
        pass

    @abstractmethod
    def set_width(self, window_id, width):
        pass

    @abstractmethod
    def set_height(self, window_id, height):
        pass

    @abstractmethod
    def set_size(self, window_id, width, height):
        pass

    @abstractmethod
    def fit_to_display(self, window_id, display_id):
        pass

    @abstractmethod
    def maximize_to_display(self, window_id, display_id):
        pass

    @abstractmethod
    def restore_size(self, window_id):
        pass


class WindowState(ABC):
    @abstractmethod
    def get_state(self, window_id):
        pass

    @abstractmethod
    def set_state(self, window_id, state):
        pass

    @abstractmethod
    def minimize(self, window_id):
        pass

    @abstractmethod
    def maximize(self, window_id):
        pass

    @abstractmethod
    def restore(self, window_id):
        pass

    @abstractmethod
    def hide(self, window_id):
        pass

    @abstractmethod
    def show(self, window_id):
        pass

    @abstractmethod
    def toggle_visibility(self, window_id):
        pass

    @abstractmethod
    def toggle_state(self, window_id):
        pass


class WindowAppearance(ABC):
    @abstractmethod
    def set_always_on_top(self, window_id, enabled):
        pass

    @abstractmethod
    def remove_always_on_top(self, window_id):
        pass

    @abstractmethod
    def get_always_on_top(self, window_id):
        pass

    @abstractmethod
    def set_opacity(self, window_id, opacity):
        pass

    @abstractmethod
    def get_opacity(self, window_id):
        pass

    @abstractmethod
    def set_fullscreen(self, window_id, enabled):
        pass

    @abstractmethod
    def exit_fullscreen(self, window_id):
        pass

    @abstractmethod
    def toggle_fullscreen(self, window_id):
        pass


class WindowHierarchy(ABC):
    @abstractmethod
    def get_parent(self, window_id):
        pass

    @abstractmethod
    def get_children(self, window_id):
        pass

    @abstractmethod
    def get_owner(self, window_id):
        pass

    @abstractmethod
    def get_app_windows(self, app_name):
        pass

    @abstractmethod
    def get_hierarchy(self, window_id):
        pass


class WindowDisplay(ABC):
    @abstractmethod
    def get_window_display(self, window_id):
        pass

    @abstractmethod
    def move_to_display(self, window_id, display_id):
        pass

    @abstractmethod
    def move_to_next(self, window_id):
        pass

    @abstractmethod
    def move_to_previous(self, window_id):
        pass

    @abstractmethod
    def center_on_display(self, window_id, display_id):
        pass

    @abstractmethod
    def maximize_on_display(self, window_id, display_id):
        pass


class WindowArrangement(ABC):
    @abstractmethod
    def arrange(self, window_ids, layout):
        pass

    @abstractmethod
    def tile(self, window_ids):
        pass

    @abstractmethod
    def cascade(self, window_ids):
        pass

    @abstractmethod
    def stack(self, window_ids):
        pass

    @abstractmethod
    def arrange_app(self, app_name, layout):
        pass

    @abstractmethod
    def grid(self, window_ids, rows, columns):
        pass

    @abstractmethod
    def equalize(self, window_ids):
        pass


class WindowGroups(ABC):
    @abstractmethod
    def group(self, window_ids, group_name):
        pass

    @abstractmethod
    def ungroup(self, window_ids):
        pass

    @abstractmethod
    def get_group(self, window_id):
        pass

    @abstractmethod
    def get_all_groups(self):
        pass

    @abstractmethod
    def activate(self, group_name):
        pass

    @abstractmethod
    def arrange(self, group_name, layout):
        pass


class WindowLifecycle(ABC):
    @abstractmethod
    def close(self, window_id):
        pass

    @abstractmethod
    def close_multiple(self, window_ids):
        pass

    @abstractmethod
    def close_app_windows(self, app_name):
        pass

    @abstractmethod
    def wait_for_window(self, title, timeout=10):
        pass

    @abstractmethod
    def wait_for_close(self, window_id, timeout=10):
        pass

    @abstractmethod
    def wait_for_visibility(self, window_id, timeout=10, visible=True):
        pass

    @abstractmethod
    def wait_for_active(self, window_id, timeout=10):
        pass
