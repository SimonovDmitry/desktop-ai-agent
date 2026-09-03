from abc import ABC, abstractmethod


class InputKeyboard(ABC):
    @abstractmethod
    def press_key(self, key):
        pass

    @abstractmethod
    def release_key(self, key):
        pass

    @abstractmethod
    def tap_key(self, key, duration=0.05):
        pass

    @abstractmethod
    def hold_key(self, key, duration):
        pass

    @abstractmethod
    def release_all_keys(self):
        pass

    @abstractmethod
    def press_keys(self, keys):
        pass

    @abstractmethod
    def type_text(self, text):
        pass

    @abstractmethod
    def type_text_slowly(self, text, interval=0.05):
        pass

    @abstractmethod
    def paste_text(self, text):
        pass

    @abstractmethod
    def copy_selection(self):
        pass

    @abstractmethod
    def cut_selection(self):
        pass

    @abstractmethod
    def select_all(self):
        pass

    @abstractmethod
    def delete_selection(self):
        pass

    @abstractmethod
    def get_keyboard_state(self):
        pass


class InputMouse(ABC):
    @abstractmethod
    def get_mouse_position(self):
        pass

    @abstractmethod
    def move_mouse(self, x, y):
        pass

    @abstractmethod
    def move_mouse_relative(self, dx, dy):
        pass

    @abstractmethod
    def click_mouse(self, button="left"):
        pass

    @abstractmethod
    def double_click_mouse(self, button="left"):
        pass

    @abstractmethod
    def triple_click_mouse(self, button="left"):
        pass

    @abstractmethod
    def mouse_down(self, button):
        pass

    @abstractmethod
    def mouse_up(self, button):
        pass

    @abstractmethod
    def drag_mouse(self, x1, y1, x2, y2, button="left", duration=0.5):
        pass

    @abstractmethod
    def drag_mouse_relative(self, dx, dy, button="left", duration=0.5):
        pass

    @abstractmethod
    def scroll_mouse(self, clicks):
        pass

    @abstractmethod
    def horizontal_scroll_mouse(self, clicks):
        pass

    @abstractmethod
    def move_mouse_smoothly(self, x, y, duration=0.5):
        pass

    @abstractmethod
    def get_mouse_button_state(self):
        pass


class InputShortcuts(ABC):
    @abstractmethod
    def press_shortcut(self, shortcut):
        pass

    @abstractmethod
    def release_shortcut(self, shortcut):
        pass

    @abstractmethod
    def execute_shortcut_sequence(self, shortcuts, delay=0.1):
        pass

    @abstractmethod
    def copy(self):
        pass

    @abstractmethod
    def paste(self):
        pass

    @abstractmethod
    def cut(self):
        pass

    @abstractmethod
    def undo(self):
        pass

    @abstractmethod
    def redo(self):
        pass

    @abstractmethod
    def save(self):
        pass

    @abstractmethod
    def save_as(self, path=None):
        pass

    @abstractmethod
    def find(self, text):
        pass

    @abstractmethod
    def close(self):
        pass

    @abstractmethod
    def quit(self):
        pass

    @abstractmethod
    def switch_application(self, application):
        pass


class InputHotkeys(ABC):
    @abstractmethod
    def register_hotkey(self, hotkey, action):
        pass

    @abstractmethod
    def unregister_hotkey(self, hotkey):
        pass

    @abstractmethod
    def unregister_all_hotkeys(self):
        pass

    @abstractmethod
    def get_registered_hotkeys(self):
        pass

    @abstractmethod
    def is_hotkey_registered(self, hotkey):
        pass

    @abstractmethod
    def trigger_hotkey(self, hotkey):
        pass


class InputClipboard(ABC):
    @abstractmethod
    def copy_text(self):
        pass

    @abstractmethod
    def paste_text(self, text):
        pass

    @abstractmethod
    def get_selected_text(self):
        pass

    @abstractmethod
    def replace_selected_text(self, text):
        pass

    @abstractmethod
    def append_to_clipboard(self, text, separator="\n"):
        pass

    @abstractmethod
    def clear_clipboard(self):
        pass


class InputSelection(ABC):
    @abstractmethod
    def select_all_text(self):
        pass

    @abstractmethod
    def select_text(self, start, end):
        pass

    @abstractmethod
    def select_word(self):
        pass

    @abstractmethod
    def select_line(self):
        pass

    @abstractmethod
    def select_to_start(self, scope="line"):
        pass

    @abstractmethod
    def select_to_end(self, scope="line"):
        pass

    @abstractmethod
    def extend_selection(self, direction, amount, unit):
        pass

    @abstractmethod
    def clear_selection(self):
        pass


class InputState(ABC):
    @abstractmethod
    def get_keyboard_state(self):
        pass

    @abstractmethod
    def get_pressed_keys(self):
        pass

    @abstractmethod
    def is_key_pressed(self, key):
        pass

    @abstractmethod
    def get_mouse_button_state(self):
        pass

    @abstractmethod
    def is_mouse_button_pressed(self, button):
        pass

    @abstractmethod
    def get_input_state(self):
        pass

    @abstractmethod
    def release_all_input(self):
        pass


class InputGestures(ABC):
    @abstractmethod
    def drag_gesture(self, start_x, start_y, end_x, end_y, button="left", duration=0.5):
        pass

    @abstractmethod
    def swipe_gesture(self, start_x, start_y, end_x, end_y, duration=0.3):
        pass

    @abstractmethod
    def click_and_hold(self, button, duration):
        pass

    @abstractmethod
    def move_and_click(self, x, y, button="left"):
        pass

    @abstractmethod
    def move_and_double_click(self, x, y, button="left"):
        pass

    @abstractmethod
    def scroll_gesture(self, direction, amount):
        pass

    @abstractmethod
    def multi_click_gesture(self, count, button="left", interval=0.1):
        pass


class InputAutomation(ABC):
    @abstractmethod
    def execute_input_sequence(self, actions):
        pass

    @abstractmethod
    def execute_input_sequence_with_delay(self, actions, delay):
        pass

    @abstractmethod
    def wait_for_input(self, input_type, timeout=30):
        pass

    @abstractmethod
    def wait_for_key(self, key, timeout=10):
        pass

    @abstractmethod
    def wait_for_mouse_click(self, button, timeout=10):
        pass

    @abstractmethod
    def repeat_input_action(self, action, count, interval):
        pass

    @abstractmethod
    def cancel_input_automation(self, automation_id):
        pass