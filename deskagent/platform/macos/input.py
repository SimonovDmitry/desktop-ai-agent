import subprocess
import threading
import time

import Quartz
from AppKit import (
    NSEvent,
    NSPasteboard,
    NSScreen,
    NSStringPboardType,
    NSWorkspace,
    NSApplicationActivateIgnoringOtherApps
)

from deskagent.platform.base.input import (
    InputAutomation,
    InputClipboard,
    InputGestures,
    InputHotkeys,
    InputKeyboard,
    InputMouse,
    InputSelection,
    InputShortcuts,
    InputState
)


class MacOSKeyboard(InputKeyboard):
    KEY_MAP = {
        'a': 0x00, 's': 0x01, 'd': 0x02, 'f': 0x03, 'h': 0x04, 'g': 0x05, 'z': 0x06, 'x': 0x07,
        'c': 0x08, 'v': 0x09, 'b': 0x0B, 'q': 0x0C, 'w': 0x0D, 'e': 0x0E, 'r': 0x0F, 'y': 0x10,
        't': 0x11, '1': 0x12, '2': 0x13, '3': 0x14, '4': 0x15, '6': 0x16, '5': 0x17, '9': 0x19,
        '7': 0x1A, '8': 0x1C, '0': 0x1D,

        'enter': 0x24,
        'return': 0x24,
        'tab': 0x30,
        'space': 0x31,
        'delete': 0x33,
        'backspace': 0x33,
        'escape': 0x35,
        'shift': 0x38,
        'cmd': 0x37,
        'command': 0x37,
        'option': 0x3A,
        'alt': 0x3A,
        'ctrl': 0x3B,
        'control': 0x3B
    }

    MODIFIER_MASKS = {
        'shift': Quartz.kCGEventFlagMaskShift,
        'cmd': Quartz.kCGEventFlagMaskCommand,
        'command': Quartz.kCGEventFlagMaskCommand,
        'option': Quartz.kCGEventFlagMaskAlternate,
        'alt': Quartz.kCGEventFlagMaskAlternate,
        'ctrl': Quartz.kCGEventFlagMaskControl,
    }

    def __init__(self):
        self._pressed_keys = set()
        self._current_flags = 0
        self.event_source = Quartz.CGEventSourceCreate(Quartz.kCGEventSourceStateCombinedSessionState)

    def _get_keycode(self, key):
        code = self.KEY_MAP.get(key.lower())
        if code is None:
            return None
        return code

    def press_key(self, key):
        keycode = self._get_keycode(key)
        if keycode is None: return

        key_lower = key.lower()
        if key_lower in self.MODIFIER_MASKS:
            self._current_flags |= self.MODIFIER_MASKS[key_lower]

        event = Quartz.CGEventCreateKeyboardEvent(self.event_source, keycode, True)
        Quartz.CGEventSetFlags(event, self._current_flags)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)
        self._pressed_keys.add(keycode)

    def release_key(self, key):
        keycode = self._get_keycode(key)
        if keycode is None: return

        key_lower = key.lower()
        if key_lower in self.MODIFIER_MASKS:
            self._current_flags &= ~self.MODIFIER_MASKS[key_lower]

        event = Quartz.CGEventCreateKeyboardEvent(self.event_source, keycode, False)
        Quartz.CGEventSetFlags(event, self._current_flags)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)

        if keycode in self._pressed_keys:
            self._pressed_keys.remove(keycode)

    def hold_key(self, key, duration):
        start_time = time.time()
        self.tap_key(key)

        if key.lower() not in self.MODIFIER_MASKS:
            time.sleep(0.4)

            while time.time() - start_time < duration:
                self.tap_key(key, duration=0.01)
                time.sleep(0.05)
        else:
            self.press_key(key)
            time.sleep(duration)
            self.release_key(key)

        self.release_key(key)

    def tap_key(self, key, duration=0.05):
        self.press_key(key)
        time.sleep(duration)
        self.release_key(key)

    def release_all_keys(self):
        self._current_flags = 0
        all_mods = [0x37, 0x38, 0x39, 0x3A, 0x3B, 0x3C, 0x3D, 0x3E]
        to_release = list(self._pressed_keys) + all_mods

        for code in to_release:
            ev = Quartz.CGEventCreateKeyboardEvent(None, code, False)
            Quartz.CGEventSetFlags(ev, 0)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, ev)

        flags_ev = Quartz.CGEventCreate(None)
        Quartz.CGEventSetType(flags_ev, Quartz.kCGEventFlagsChanged)
        Quartz.CGEventSetFlags(flags_ev, 0)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, flags_ev)

        self._pressed_keys.clear()
        time.sleep(0.2)

    def press_keys(self, keys):
        for key in keys:
            self.tap_key(key)

    def type_text(self, text):
        for char in text:
            event = Quartz.CGEventCreateKeyboardEvent(None, 0, True)
            Quartz.CGEventKeyboardSetUnicodeString(event, len(char.encode('utf-16-le')) // 2, char)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)

            up_event = Quartz.CGEventCreateKeyboardEvent(None, 0, False)
            Quartz.CGEventKeyboardSetUnicodeString(up_event, len(char.encode('utf-16-le')) // 2, char)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, up_event)

    def type_text_slowly(self, text, interval=0.05):
        for char in text:
            self.type_text(char)
            time.sleep(interval)

    def paste_text(self, text):
        pb = NSPasteboard.generalPasteboard()
        pb.clearContents()
        pb.setString_forType_(text, NSStringPboardType)

        self.press_key('cmd')
        self.tap_key('v')
        self.release_key('cmd')

    def copy_selection(self):
        self.press_key('cmd')
        self.tap_key('c')
        self.release_key('cmd')

    def cut_selection(self):
        self.press_key('cmd')
        self.tap_key('x')
        self.release_key('cmd')

    def select_all(self):
        self.press_key('cmd')
        self.tap_key('a')
        self.release_key('cmd')

    def delete_selection(self):
        self.tap_key('delete')

    def get_keyboard_state(self):
        return {
            "pressed_keys": list(self._pressed_keys),
            "modifiers": {
                "command": bool(self._current_flags & Quartz.kCGEventFlagMaskCommand),
                "shift": bool(self._current_flags & Quartz.kCGEventFlagMaskShift),
                "option": bool(self._current_flags & Quartz.kCGEventFlagMaskAlternate),
                "control": bool(self._current_flags & Quartz.kCGEventFlagMaskControl),
                "caps_lock": bool(self._current_flags & Quartz.kCGEventFlagMaskAlphaShift)
            }
        }


class MacOSMouse(InputMouse):
    def __init__(self):
        self.event_source = Quartz.CGEventSourceCreate(Quartz.kCGEventSourceStateCombinedSessionState)
        self.BUTTON_MAP = {
            "left": {
                "down": Quartz.kCGEventLeftMouseDown,
                "up": Quartz.kCGEventLeftMouseUp,
                "drag": Quartz.kCGEventLeftMouseDragged,
                "button": Quartz.kCGMouseButtonLeft
            },
            "right": {
                "down": Quartz.kCGEventRightMouseDown,
                "up": Quartz.kCGEventRightMouseUp,
                "drag": Quartz.kCGEventRightMouseDragged,
                "button": Quartz.kCGMouseButtonRight
            },
            "middle": {
                "down": Quartz.kCGEventOtherMouseDown,
                "up": Quartz.kCGEventOtherMouseUp,
                "drag": Quartz.kCGEventOtherMouseDragged,
                "button": Quartz.kCGMouseButtonCenter
            }
        }

    def _get_screen_height(self):
        return NSScreen.mainScreen().frame().size.height

    def _post_click_event(self, x, y, button, event_type, click_count=1):
        btn_info = self.BUTTON_MAP.get(button, self.BUTTON_MAP["left"])
        event = Quartz.CGEventCreateMouseEvent(
            self.event_source, event_type, (x, y), btn_info["button"]
        )
        Quartz.CGEventSetIntegerValueField(event, Quartz.kCGMouseEventClickState, click_count)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)

    def get_mouse_position(self):
        pos = NSEvent.mouseLocation()
        return {"x": int(pos.x), "y": int(self._get_screen_height() - pos.y)}

    def move_mouse(self, x, y):
        event = Quartz.CGEventCreateMouseEvent(
            self.event_source, Quartz.kCGEventMouseMoved, (x, y), 0
        )
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)
        return {"x": x, "y": y, "moved": True}

    def move_mouse_relative(self, dx, dy):
        curr = self.get_mouse_position()
        new_x, new_y = curr['x'] + dx, curr['y'] + dy
        return self.move_mouse(new_x, new_y)

    def click_mouse(self, button="left"):
        pos = self.get_mouse_position()
        self.mouse_down(button)
        time.sleep(0.01)
        self.mouse_up(button)
        return {"button": button, "clicked": True}

    def double_click_mouse(self, button="left"):
        pos = self.get_mouse_position()
        self._post_click_event(pos['x'], pos['y'], button, self.BUTTON_MAP[button]["down"], 1)
        self._post_click_event(pos['x'], pos['y'], button, self.BUTTON_MAP[button]["up"], 1)
        self._post_click_event(pos['x'], pos['y'], button, self.BUTTON_MAP[button]["down"], 2)
        self._post_click_event(pos['x'], pos['y'], button, self.BUTTON_MAP[button]["up"], 2)
        return {"button": button, "clicked": True, "click_count": 2}

    def triple_click_mouse(self, button="left"):
        pos = self.get_mouse_position()
        for i in range(1, 4):
            self._post_click_event(pos['x'], pos['y'], button, self.BUTTON_MAP[button]["down"], i)
            self._post_click_event(pos['x'], pos['y'], button, self.BUTTON_MAP[button]["up"], i)
        return {"button": button, "click_count": 3}

    def mouse_down(self, button):
        pos = self.get_mouse_position()
        event_type = self.BUTTON_MAP[button]["down"]
        self._post_click_event(pos['x'], pos['y'], button, event_type)
        return {"button": button, "pressed": True}

    def mouse_up(self, button):
        pos = self.get_mouse_position()
        event_type = self.BUTTON_MAP[button]["up"]
        self._post_click_event(pos['x'], pos['y'], button, event_type)
        return {"button": button, "released": True}

    def drag_mouse(self, x1, y1, x2, y2, button="left", duration=0.5):
        self.move_mouse(x1, y1)
        time.sleep(0.1)
        self.mouse_down(button)

        steps = 20
        for i in range(steps):
            curr_x = x1 + (x2 - x1) * (i / steps)
            curr_y = y1 + (y2 - y1) * (i / steps)
            event = Quartz.CGEventCreateMouseEvent(
                self.event_source, self.BUTTON_MAP[button]["drag"], (curr_x, curr_y), self.BUTTON_MAP[button]["button"]
            )
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)
            time.sleep(duration / steps)

        self.mouse_up(button)
        return {"from": {"x": x1, "y": y1}, "to": {"x": x2, "y": y2}, "dragged": True}

    def drag_mouse_relative(self, dx, dy, button="left", duration=0.5):
        curr = self.get_mouse_position()
        return self.drag_mouse(curr['x'], curr['y'], curr['x'] + dx, curr['y'] + dy, button, duration)

    def scroll_mouse(self, clicks):
        event = Quartz.CGEventCreateScrollWheelEvent(self.event_source, Quartz.kCGScrollEventUnitLine, 1, clicks)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)
        return {"clicks": clicks, "scrolled": True}

    def horizontal_scroll_mouse(self, clicks):
        event = Quartz.CGEventCreateScrollWheelEvent(
            self.event_source, Quartz.kCGScrollEventUnitLine, 2, 0, clicks
        )
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)
        return {"clicks": clicks, "scrolled": True, "direction": "horizontal"}

    def move_mouse_smoothly(self, x, y, duration=0.5):
        curr = self.get_mouse_position()
        x1, y1 = curr['x'], curr['y']
        steps = 30
        for i in range(1, steps + 1):
            t = i / steps

            target_x = x1 + (x - x1) * t
            target_y = y1 + (y - y1) * t
            self.move_mouse(target_x, target_y)
            time.sleep(duration / steps)
        return {"x": x, "y": y, "duration": duration, "moved": True}

    def get_mouse_button_state(self):
        state = NSEvent.pressedMouseButtons()
        return {
            "left": bool(state & 1),
            "right": bool(state & 2),
            "middle": bool(state & 4)
        }


class MacOSShortcuts(InputShortcuts):
    def __init__(self, keyboard_service=None):
        self.kb = keyboard_service or MacOSKeyboard()

    def _parse_and_execute(self, shortcut, press=True):
        keys = shortcut.lower().replace(" ", "").split('+')
        modifiers = [k for k in keys if k in self.kb.MODIFIER_MASKS]
        normal_keys = [k for k in keys if k not in self.kb.MODIFIER_MASKS]

        if press:
            for m in modifiers:
                self.kb.press_key(m)

            for nk in normal_keys:
                self.kb.tap_key(nk)

            for m in reversed(modifiers):
                self.kb.release_key(m)
        else:
            for k in keys:
                self.kb.release_key(k)

    def press_shortcut(self, shortcut):
        self._parse_and_execute(shortcut, press=True)
        return {"shortcut": shortcut, "executed": True}

    def release_shortcut(self, shortcut):
        self._parse_and_execute(shortcut, press=False)
        return {"shortcut": shortcut, "released": True}

    def execute_shortcut_sequence(self, shortcuts, delay=0.1):
        for s in shortcuts:
            self.press_shortcut(s)
            time.sleep(delay)
        return {"executed": len(shortcuts), "completed": True}

    def copy(self):
        return self.press_shortcut("cmd+c")

    def paste(self):
        return self.press_shortcut("cmd+v")

    def cut(self):
        return self.press_shortcut("cmd+x")

    def undo(self):
        return self.press_shortcut("cmd+z")

    def redo(self):
        return self.press_shortcut("cmd+shift+z")

    def save(self):
        return self.press_shortcut("cmd+s")

    def save_as(self, path=None):
        self.press_shortcut("cmd+shift+s")
        if path:
            time.sleep(0.5)
            self.kb.type_text(path)
        return {"save_as_triggered": True}

    def select_all(self):
        return self.press_shortcut("cmd+a")

    def find(self, text):
        self.press_shortcut("cmd+f")
        time.sleep(0.2)
        self.kb.type_text(text)
        return {"search": text, "executed": True}

    def close(self):
        return self.press_shortcut("cmd+w")

    def quit(self):
        return self.press_shortcut("cmd+q")

    def switch_application(self, application):
        workspace = NSWorkspace.sharedWorkspace()
        for app in workspace.runningApplications():
            if app.localizedName().lower() == application.lower():
                app.activateWithOptions_(NSApplicationActivateIgnoringOtherApps)
                return {"application": application, "switched": True}

        subprocess.run(["open", "-a", application])
        return {"application": application, "launched": True}


class MacOSHotkeys(InputHotkeys):
    def __init__(self, keyboard_service=None):
        self.kb = keyboard_service or MacOSKeyboard()
        self._hotkeys = {}
        self._listener_thread = None
        self._stop_event = threading.Event()

    def _parse_hotkey(self, hotkey_str):
        parts = hotkey_str.lower().replace(" ", "").split('+')
        keycode = self.kb._get_keycode(parts[-1])

        mask = 0
        for p in parts[:-1]:
            if p in self.kb.MODIFIER_MASKS:
                mask |= self.kb.MODIFIER_MASKS[p]

        return mask, keycode

    def _event_tap_callback(self, proxy, type, event, refcon):
        if type == Quartz.kCGEventKeyDown:
            keycode = Quartz.CGEventGetIntegerValueField(event, Quartz.kCGKeyboardEventKeycode)
            flags = Quartz.CGEventGetFlags(event) & (
                    Quartz.kCGEventFlagMaskCommand |
                    Quartz.kCGEventFlagMaskShift |
                    Quartz.kCGEventFlagMaskAlternate |
                    Quartz.kCGEventFlagMaskControl
            )
        return event

    def _start_listener(self):
        if self._listener_thread and self._listener_thread.is_alive():
            return

        def run_loop():
            tap = Quartz.CGEventTapCreate(
                Quartz.kCGSessionEventTap,
                Quartz.kCGHeadInsertEventTap,
                Quartz.kCGEventTapOptionListenOnly,
                Quartz.kCGEventMaskBit(Quartz.kCGEventKeyDown),
                self._event_tap_callback,
                None
            )

            if not tap:
                return

            run_loop_source = Quartz.CFMachPortCreateRunLoopSource(None, tap, 0)
            Quartz.CFRunLoopAddSource(Quartz.CFRunLoopGetCurrent(), run_loop_source, Quartz.kCFRunLoopCommonModes)
            Quartz.CGEventTapEnable(tap, True)
            Quartz.CFRunLoopRun()

        self._listener_thread = threading.Thread(target=run_loop, daemon=True)
        self._listener_thread.start()

    def register_hotkey(self, hotkey, action):
        mask, keycode = self._parse_hotkey(hotkey)
        self._hotkeys[(mask, keycode)] = action

        self._start_listener()
        return {"hotkey": hotkey, "registered": True}

    def unregister_hotkey(self, hotkey):
        try:
            mask, keycode = self._parse_hotkey(hotkey)
            if (mask, keycode) in self._hotkeys:
                del self._hotkeys[(mask, keycode)]
            return {"hotkey": hotkey, "unregistered": True}
        except:
            return {"hotkey": hotkey, "unregistered": False}

    def unregister_all_hotkeys(self):
        count = len(self._hotkeys)
        self._hotkeys.clear()
        return {"removed": count}

    def get_registered_hotkeys(self):
        return {"hotkeys_count": len(self._hotkeys)}

    def is_hotkey_registered(self, hotkey):
        mask, keycode = self._parse_hotkey(hotkey)
        return {"hotkey": hotkey, "registered": (mask, keycode) in self._hotkeys}

    def trigger_hotkey(self, hotkey):
        shortcuts = MacOSShortcuts(self.kb)
        return shortcuts.press_shortcut(hotkey)


class MacOSClipboard(InputClipboard):
    def __init__(self, keyboard_service=None):
        self.kb = keyboard_service or MacOSKeyboard()
        self.shortcuts = MacOSShortcuts(self.kb)
        self.pb = NSPasteboard.generalPasteboard()

    def _get_system_clipboard(self):
        return self.pb.stringForType_(NSStringPboardType)

    def _set_system_clipboard(self, text):
        self.pb.clearContents()
        self.pb.setString_forType_(text or "", NSStringPboardType)

    def copy_text(self):
        self.shortcuts.copy()
        time.sleep(0.15)
        text = self._get_system_clipboard()

        return {
            "copied": True,
            "text": text if text else ""
        }

    def paste_text(self, text):

        if text is None:
            return {"pasted": False, "error": "No text provided"}
        self._set_system_clipboard(text)
        self.shortcuts.paste()

        return {
            "pasted": True,
            "text_length": len(text)
        }

    def get_selected_text(self):
        old_content = self._get_system_clipboard()
        res = self.copy_text()

        return {
            "selected": True,
            "text": res["text"]
        }

    def replace_selected_text(self, text):
        return self.paste_text(text)

    def append_to_clipboard(self, text, separator=""):
        current_text = self._get_system_clipboard() or ""
        new_text = current_text + separator + text if current_text else text

        self._set_system_clipboard(new_text)

        return {
            "appended": True,
            "text_length": len(new_text)
        }

    def clear_clipboard(self):
        self.pb.clearContents()
        return {"cleared": True}


class MacOSSelection(InputSelection):
    def __init__(self):
        self.kb = MacOSKeyboard()
        self.shortcuts = MacOSShortcuts(self.kb)

    def select_all_text(self):
        self.shortcuts.press_shortcut("cmd+a")
        return {"selected": True}

    def select_text(self, start, end):
        self.kb.release_all_keys()
        time.sleep(0.1)

        self.kb.tap_key("left")
        time.sleep(0.1)
        self.kb.press_key("cmd")
        self.kb.tap_key("left")
        self.kb.release_key("cmd")
        time.sleep(0.15)

        for i in range(start):
            self.kb.tap_key("right", duration=0.001)
            if i % 50 == 0:
                time.sleep(0.01)

        time.sleep(0.1)

        self.kb.press_key("shift")
        time.sleep(0.05)
        for i in range(end - start):
            self.kb.tap_key("right", duration=0.001)
            if i % 50 == 0:
                time.sleep(0.01)
        time.sleep(0.05)
        self.kb.release_key("shift")

        self.kb.release_all_keys()
        return {"start": start, "end": end, "selected": True}

    def select_word(self):
        self.kb.release_all_keys()
        time.sleep(0.05)

        self.kb.press_key("option")
        self.kb.tap_key("left")
        self.kb.release_key("option")
        time.sleep(0.05)

        self.kb.press_key("shift")
        self.kb.press_key("option")
        self.kb.tap_key("right")
        self.kb.release_key("option")
        self.kb.release_key("shift")

        self.kb.release_all_keys()
        return {"selected": True, "unit": "word"}

    def clear_selection(self):
        self.kb.release_all_keys()
        self.kb.tap_key("right")
        return {"cleared": True}

    def select_line(self):
        self.kb.release_all_keys()
        time.sleep(0.05)

        self.kb.press_key("cmd")
        self.kb.tap_key("left")
        self.kb.release_key("cmd")
        time.sleep(0.05)

        self.kb.press_key("shift")
        self.kb.press_key("cmd")
        self.kb.tap_key("right")
        self.kb.release_key("cmd")
        self.kb.release_key("shift")

        self.kb.release_all_keys()
        return {"selected": True, "unit": "line"}

    def select_to_start(self, scope="line"):
        self.kb.release_all_keys()
        time.sleep(0.05)

        direction_key = "up" if scope == "document" else "left"

        self.kb.press_key("shift")
        self.kb.press_key("cmd")
        self.kb.tap_key(direction_key)
        self.kb.release_key("cmd")
        self.kb.release_key("shift")

        self.kb.release_all_keys()
        return {"scope": scope, "extended": True}

    def select_to_end(self, scope="line"):
        self.kb.release_all_keys()
        time.sleep(0.05)

        direction_key = "down" if scope == "document" else "right"

        self.kb.press_key("shift")
        self.kb.press_key("cmd")
        self.kb.tap_key(direction_key)
        self.kb.release_key("cmd")
        self.kb.release_key("shift")

        self.kb.release_all_keys()
        return {"scope": scope, "extended": True}

    def extend_selection(self, direction, amount, unit):
        self.kb.release_all_keys()
        time.sleep(0.05)

        modifiers = ["shift"]
        if unit == "word":
            modifiers.append("option")
        elif unit == "line" and direction in ("left", "right"):
            modifiers.append("cmd")

        for mod in modifiers:
            self.kb.press_key(mod)
        time.sleep(0.05)

        for _ in range(amount):
            self.kb.tap_key(direction, duration=0.001)
            time.sleep(0.01)

        time.sleep(0.05)
        for mod in reversed(modifiers):
            self.kb.release_key(mod)

        self.kb.release_all_keys()
        return {"direction": direction, "amount": amount, "unit": unit}


class MacOSState(InputState):
    def __init__(self):
        self.kb = MacOSKeyboard()
        self.mouse = MacOSMouse()

        self.MOD_MAP = {
            "cmd": Quartz.kCGEventFlagMaskCommand,
            "shift": Quartz.kCGEventFlagMaskShift,
            "option": Quartz.kCGEventFlagMaskAlternate,
            "control": Quartz.kCGEventFlagMaskControl,
            "caps_lock": Quartz.kCGEventFlagMaskAlphaShift
        }

    def get_keyboard_state(self):
        flags = Quartz.CGEventSourceFlagsState(Quartz.kCGEventSourceStateCombinedSessionState)
        pressed = [name for name, mask in self.MOD_MAP.items() if flags & mask]
        return {"pressed_keys": pressed}

    def get_pressed_keys(self):
        pressed = []
        for i in range(128):
            if Quartz.CGEventSourceKeyState(Quartz.kCGEventSourceStateCombinedSessionState, i):
                pressed.append(i)

        mods = self.get_keyboard_state()["pressed_keys"]
        return {"keys": pressed + mods, "count": len(pressed) + len(mods)}

    def is_key_pressed(self, key):
        key = key.lower()
        if key in self.MOD_MAP:
            flags = Quartz.CGEventSourceFlagsState(Quartz.kCGEventSourceStateCombinedSessionState)
            return {"key": key, "pressed": bool(flags & self.MOD_MAP[key])}

        if self.kb:
            keycode = self.kb._get_keycode(key)
            if keycode is not None:
                is_down = Quartz.CGEventSourceKeyState(Quartz.kCGEventSourceStateCombinedSessionState, keycode)
                return {"key": key, "pressed": bool(is_down)}
        return {"key": key, "pressed": False}

    def get_mouse_button_state(self):
        state = NSEvent.pressedMouseButtons()
        return {
            "left": bool(state & 1),
            "right": bool(state & 2),
            "middle": bool(state & 4)
        }

    def is_mouse_button_pressed(self, button):
        states = self.get_mouse_button_state()
        return {"button": button, "pressed": states.get(button.lower(), False)}

    def get_input_state(self):
        kb = self.get_keyboard_state()
        m_pos = NSEvent.mouseLocation()
        screen_h = NSScreen.mainScreen().frame().size.height

        return {
            "keyboard": {
                "pressed_keys": kb["pressed_keys"]
            },
            "mouse": {
                "position": {
                    "x": int(m_pos.x),
                    "y": int(screen_h - m_pos.y)
                },
                "buttons": self.get_mouse_button_state()
            }
        }

    def release_all_input(self):
        keys_ok = False
        mouse_ok = False

        try:
            if self.kb:
                self.kb.release_all_keys()
                keys_ok = True

            if self.mouse:
                for btn in ["left", "right", "middle"]:
                    self.mouse.mouse_up(btn)
                mouse_ok = True

            return {
                "keys_released": keys_ok,
                "mouse_buttons_released": mouse_ok
            }
        except Exception as e:
            return {"keys_released": keys_ok, "mouse_buttons_released": mouse_ok}


class MacOSGestures(InputGestures):
    def __init__(self):
        self.mouse = MacOSMouse()

    def drag_gesture(self, start_x, start_y, end_x, end_y, button="left", duration=0.5):
        result = self.mouse.drag_mouse(start_x, start_y, end_x, end_y, button, duration)
        return {"gesture": "drag", "completed": True, "details": result}

    def swipe_gesture(self, start_x, start_y, end_x, end_y, duration=0.3):
        self.mouse.move_mouse(start_x, start_y)
        time.sleep(0.05)
        self.mouse.move_mouse_smoothly(end_x, end_y, duration)
        return {"gesture": "swipe", "start": (start_x, start_y), "end": (end_x, end_y)}

    def click_and_hold(self, button="left", duration=2.0):
        self.mouse.mouse_down(button)
        time.sleep(duration)
        self.mouse.mouse_up(button)
        return {"button": button, "duration": duration, "completed": True}

    def move_and_click(self, x, y, button="left"):
        self.mouse.move_mouse(x, y)
        time.sleep(0.1)
        self.mouse.click_mouse(button)
        return {"position": {"x": x, "y": y}, "button": button, "clicked": True}

    def move_and_double_click(self, x, y, button="left"):
        self.mouse.move_mouse(x, y)
        time.sleep(0.1)
        self.mouse.double_click_mouse(button)
        return {"position": {"x": x, "y": y}, "button": button, "double_clicked": True}

    def scroll_gesture(self, direction, amount):
        if direction == "down":
            self.mouse.scroll_mouse(-amount)
        elif direction == "up":
            self.mouse.scroll_mouse(amount)
        elif direction == "left":
            self.mouse.horizontal_scroll_mouse(-amount)
        elif direction == "right":
            self.mouse.horizontal_scroll_mouse(amount)

        return {"gesture": "scroll", "direction": direction, "amount": amount}

    def multi_click_gesture(self, count, button="left", interval=0.1):
        for i in range(count):
            self.mouse.click_mouse(button)
            if i < count - 1:
                time.sleep(interval)
        return {"count": count, "completed": True}


class MacOSAutomation(InputAutomation):
    def __init__(self):
        self.kb = MacOSKeyboard()
        self.mouse = MacOSMouse()
        self._cancel_flags = {}

    def _dispatch_action(self, action):
        atype = action.get('type')

        if atype == "move_mouse":
            self.mouse.move_mouse(action['x'], action['y'])
        elif atype == "click":
            self.mouse.click_mouse(action.get('button', 'left'))
        elif atype == "double_click":
            self.mouse.double_click_mouse(action.get('button', 'left'))
        elif atype == "scroll":
            self.mouse.scroll_mouse(action['clicks'])

        elif atype == "type_text":
            self.kb.type_text(action['text'])
        elif atype == "press_key":
            self.kb.press_key(action['key'])
        elif atype == "tap_key":
            self.kb.tap_key(action['key'])
        elif atype == "press_shortcut":
            MacOSShortcuts(self.kb).press_shortcut(action['shortcut'])

    def execute_input_sequence(self, actions):
        executed = 0
        try:
            for action in actions:
                self._dispatch_action(action)
                executed += 1
            return {"completed": True, "executed": executed, "failed": 0}
        except Exception as e:
            return {"completed": False, "executed": executed, "failed": len(actions) - executed}

    def execute_input_sequence_with_delay(self, actions, delay=0.5):
        executed = 0
        for action in actions:
            self._dispatch_action(action)
            executed += 1
            if executed < len(actions):
                time.sleep(delay)
        return {"executed": executed, "completed": True}

    def wait_for_input(self, input_type="any", timeout=30):
        state_service = MacOSState()

        start_time = time.time()
        while time.time() - start_time < timeout:
            if input_type == "mouse_click":
                m_state = state_service.get_mouse_button_state()
                if any(m_state.values()): return {"triggered": True, "input_type": "mouse_click"}
            elif input_type == "key_press":
                if state_service.get_pressed_keys()["count"] > 0:
                    return {"triggered": True, "input_type": "key_press"}
            else:
                m_state = state_service.get_mouse_button_state()
                if any(m_state.values()) or state_service.get_pressed_keys()["count"] > 0:
                    return {"triggered": True, "input_type": "any"}

            time.sleep(0.1)

        raise TimeoutError("Input event not detected within timeout")

    def wait_for_key(self, key, timeout=10):
        state_service = MacOSState()

        start_time = time.time()
        while time.time() - start_time < timeout:
            if state_service.is_key_pressed(key)["pressed"]:
                return {"key": key, "pressed": True}
            time.sleep(0.1)
        raise TimeoutError(f"Key '{key}' was not pressed")

    def wait_for_mouse_click(self, button="left", timeout=10):
        state_service = MacOSState()

        start_time = time.time()
        while time.time() - start_time < timeout:
            if state_service.is_mouse_button_pressed(button)["pressed"]:
                return {"button": button, "clicked": True, "pos": self.mouse.get_mouse_position()}
            time.sleep(0.1)
        raise TimeoutError(f"Mouse click '{button}' not detected")

    def repeat_input_action(self, action, count, interval=0.2):
        for i in range(count):
            self._dispatch_action(action)
            if i < count - 1:
                time.sleep(interval)
        return {"executed": count, "completed": True}

    def cancel_input_automation(self, automation_id):
        self._cancel_flags[automation_id] = True
        return {"automation_id": automation_id, "cancelled": True}
