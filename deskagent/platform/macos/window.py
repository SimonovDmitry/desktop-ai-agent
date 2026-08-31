import math
import subprocess
import time

import Quartz
from Quartz import CGPoint, CGSize
from AppKit import (NSScreen, NSWorkspace, NSApplicationActivateIgnoringOtherApps)
from ApplicationServices import (AXUIElementCreateApplication, AXUIElementCopyAttributeValue, kAXErrorSuccess,
                                 AXUIElementSetAttributeValue, AXUIElementPerformAction, AXValueCreate, AXValueGetValue,
                                 kAXErrorSuccess, kAXWindowsAttribute, kAXSubroleAttribute, kAXPositionAttribute,
                                 kAXSizeAttribute, kAXRoleAttribute, kAXRaiseAction, kAXPressAction,
                                 kAXValueCGPointType, kAXValueCGSizeType)
from deskagent.platform.base.window import (WindowAppearance, WindowArrangement, WindowDisplay, WindowFocus,
                                            WindowGroups, WindowInformation, WindowHierarchy, WindowLifecycle,
                                            WindowPosition, WindowSize, WindowState)


class MacOSInformation(WindowInformation):
    def _get_raw_window_list(self, visible_only=True):
        options = Quartz.kCGWindowListExcludeDesktopElements | Quartz.kCGWindowListOptionAll
        return Quartz.CGWindowListCopyWindowInfo(options, Quartz.kCGNullWindowID)

    def _parse_window_info(self, win):
        bounds = win.get('kCGWindowBounds', {})
        is_onscreen = win.get('kCGWindowIsOnscreen', False)

        width = int(bounds.get('Width', 0))
        height = int(bounds.get('Height', 0))

        state = "normal"
        if not is_onscreen:
            if width >= 1400 and height >= 800:
                state = "fullscreen"
            else:
                state = "minimized"

        return {
            "id": win.get('kCGWindowNumber'),
            "title": win.get('kCGWindowName', ''),
            "application": win.get('kCGWindowOwnerName', ''),
            "pid": win.get('kCGWindowOwnerPID'),
            "position": {"x": int(bounds.get('X', 0)), "y": int(bounds.get('Y', 0))},
            "size": {"width": width, "height": height},
            "visible": bool(is_onscreen) or state == "fullscreen",
            "state": state
        }

    def get_windows(self, application=None, visible_only=True):
        raw_windows = self._get_raw_window_list(visible_only)
        result = []

        for win in raw_windows:
            if win.get('kCGWindowLayer') > 100:
                continue

            parsed = self._parse_window_info(win)
            if application and application.lower() not in parsed['application'].lower():
                continue

            result.append(parsed)

        return {"windows": result, "count": len(result)}

    def get_window(self, window_id):
        raw_windows = self._get_raw_window_list(visible_only=False)
        for win in raw_windows:
            if win.get('kCGWindowNumber') == int(window_id):
                return self._parse_window_info(win)
        return None

    def find_windows(self, query):
        title_q = query.get('title')
        app_q = query.get('application')
        contains_q = query.get('title_contains')

        all_windows = self.get_windows(visible_only=False)['windows']
        filtered = []

        for win in all_windows:
            match = True
            if title_q and title_q.lower() != win['title'].lower(): match = False
            if app_q and app_q.lower() != win['application'].lower(): match = False
            if contains_q and contains_q.lower() not in win['title'].lower(): match = False

            if match: filtered.append(win)

        return {"windows": filtered, "count": len(filtered)}

    def get_active_window(self):
        active_app = NSWorkspace.sharedWorkspace().frontmostApplication()
        active_pid = active_app.processIdentifier()

        windows = self.get_windows(visible_only=True)['windows']
        for win in windows:
            if win['pid'] == active_pid:
                return {
                    "id": win['id'],
                    "title": win['title'],
                    "application": win['application']
                }
        return None

    def get_window_title(self, window_id):
        win = self.get_window(window_id)
        return {"title": win['title']} if win else None

    def get_window_position(self, window_id):
        win = self.get_window(window_id)
        return win['position'] if win else None

    def get_window_size(self, window_id):
        win = self.get_window(window_id)
        return win['size'] if win else None

    def get_window_bounds(self, window_id):
        win = self.get_window(window_id)
        if win:
            return {**win['position'], **win['size']}
        return None

    def get_window_state(self, window_id):
        win = self.get_window(window_id)
        return {"state": win['state']} if win else None

    def get_window_application(self, window_id):
        win = self.get_window(window_id)
        return {"application": win['application'], "pid": win['pid']} if win else None

    def get_window_pid(self, window_id):
        win = self.get_window(window_id)
        return {"pid": win['pid']} if win else None

    def is_window_visible(self, window_id):
        win = self.get_window(window_id)
        return {"visible": win['visible']} if win else None


class MacOSFocus(WindowFocus):
    def _get_main_window_by_pid(self, pid):
        try:
            app_ref = AXUIElementCreateApplication(int(pid))
            error, windows = AXUIElementCopyAttributeValue(app_ref, kAXWindowsAttribute, None)
            if error != kAXErrorSuccess or not windows:
                return None

            return windows[0]
        except Exception:
            return None

    def _find_button_recursive(self, element, subrole_name, depth=0):
        if depth > 5: return None

        error, children = AXUIElementCopyAttributeValue(element, "AXChildren", None)
        if error != kAXErrorSuccess or not children:
            return None

        for child in children:
            _, subrole = AXUIElementCopyAttributeValue(child, kAXSubroleAttribute, None)
            if subrole == subrole_name:
                return child

        for child in children:
            _, role = AXUIElementCopyAttributeValue(child, kAXRoleAttribute, None)
            if role in ["AXGroup", "AXToolbar", "AXUnknown"]:
                found = self._find_button_recursive(child, subrole_name, depth + 1)
                if found: return found
        return None

    def _press_window_button(self, pid, subrole):
        ax_win = self._get_main_window_by_pid(pid)
        if not ax_win: return False

        btn = self._find_button_recursive(ax_win, subrole)
        if btn:
            error = AXUIElementPerformAction(btn, kAXPressAction)
            return error == kAXErrorSuccess
        return False

    def _set_fullscreen_state(self, pid, enabled):
        ax_win = self._get_main_window_by_pid(pid)
        if ax_win:
            AXUIElementPerformAction(ax_win, kAXRaiseAction)
            time.sleep(0.1)

            error = AXUIElementSetAttributeValue(ax_win, "AXFullScreen", bool(enabled))
            return error == kAXErrorSuccess
        return False

    def _set_fullscreen_via_menu(self, pid, enter=True):
        menu_item = "Enter Full Screen" if enter else "Exit Full Screen"
        menu_item_ru = "Перейти в полноэкранный режим" if enter else "Выйти из полноэкранного режима"

        script = f'''
        tell application "System Events"
            tell (first application process whose unix id is {pid})
                set frontmost to true
                try
                    click menu item "{menu_item}" of menu 1 of menu bar item "View" of menu bar 1
                on error
                    try
                        click menu item "{menu_item_ru}" of menu 1 of menu bar item "Вид" of menu bar 1
                    on error
                        keystroke "f" using {{command down, control down}}
                    end try
                end try
            end tell
        end tell
        '''
        try:
            subprocess.run(["osascript", "-e", script], capture_output=True, timeout=5)
            return True
        except:
            return False

    def activate(self, pid):
        workspace = NSWorkspace.sharedWorkspace()
        for app in workspace.runningApplications():
            if app.processIdentifier() == int(pid):
                app.activateWithOptions_(NSApplicationActivateIgnoringOtherApps)
                ax_win = self._get_main_window_by_pid(pid)
                if ax_win:
                    AXUIElementPerformAction(ax_win, kAXRaiseAction)
                return {"pid": int(pid), "active": True}
        return None

    def focus(self, pid):
        return self.activate(pid)

    def bring_to_front(self, pid):
        return self.activate(pid)

    def minimize(self, pid):
        if self._press_window_button(pid, "AXMinimizeButton"):
            return {"pid": int(pid), "state": "minimized"}
        return {"pid": int(pid), "success": False, "error": "Button not found"}

    def restore(self, pid):
        ax_win = self._get_main_window_by_pid(pid)
        if ax_win:
            AXUIElementSetAttributeValue(ax_win, "AXMinimized", False)
        self.activate(pid)
        return {"pid": int(pid), "state": "normal"}

    def maximize(self, pid):
        if self._set_fullscreen_state(pid, True):
            return {"pid": int(pid), "state": "fullscreen"}

        if self._set_fullscreen_via_menu(pid, enter=True):
            return {"pid": int(pid), "state": "fullscreen"}

        return {"success": False, "error": "Failed to enter fullscreen"}

    def unmaximize(self, pid):
        if self._set_fullscreen_state(pid, False):
            return {"pid": int(pid), "state": "normal"}

        if self._set_fullscreen_via_menu(pid, enter=False):
            return {"pid": int(pid), "state": "normal"}

        return {"success": False, "error": "Failed to exit fullscreen"}

    def toggle_maximize(self, pid):
        ax_win = self._get_main_window_by_pid(pid)
        if ax_win:
            error, current = AXUIElementCopyAttributeValue(ax_win, "AXFullScreen", None)
            if error == kAXErrorSuccess:
                new_val = not bool(current)
                AXUIElementSetAttributeValue(ax_win, "AXFullScreen", new_val)
                return {"pid": int(pid), "state": "fullscreen" if new_val else "normal"}
        return {"success": False, "error": "Could not toggle fullscreen"}

    def send_to_back(self, pid):
        options = Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements
        window_list = Quartz.CGWindowListCopyWindowInfo(options, Quartz.kCGNullWindowID)

        other_pids = []
        for win in window_list:
            w_pid = win.get('kCGWindowOwnerPID')
            if w_pid != int(pid) and win.get('kCGWindowLayer') == 0:
                other_pids.append(w_pid)

        unique_others = list(dict.fromkeys(other_pids))
        workspace = NSWorkspace.sharedWorkspace()
        for o_pid in reversed(unique_others):
            for app in workspace.runningApplications():
                if app.processIdentifier() == o_pid:
                    app.activateWithOptions_(NSApplicationActivateIgnoringOtherApps)
                    break

        return {"pid": int(pid), "back": True}


class MacOSPosition(WindowPosition):
    def __init__(self):
        self._history = {}

    def _save_to_history(self, window_id, info):
        self._history[window_id] = (info['x'], info['y'], info['w'], info['h'])

    def _get_screen_info(self, display_id=None):
        screens = NSScreen.screens()
        if display_id is not None:
            for s in screens:
                if str(s.deviceDescription().objectForKey_("NSScreenNumber")) == str(display_id):
                    frame = s.frame()
                    visible = s.visibleFrame()
                    return frame, visible
        return screens[0].frame(), screens[0].visibleFrame()

    def _get_ax_window(self, window_id):
        options = Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements
        window_list = Quartz.CGWindowListCopyWindowInfo(options, Quartz.kCGNullWindowID)

        target_meta = None
        for win in window_list:
            if win.get(Quartz.kCGWindowNumber) == int(window_id):
                target_meta = win
                break
        if not target_meta: return None, None

        pid = target_meta.get(Quartz.kCGWindowOwnerPID)
        app_ref = AXUIElementCreateApplication(pid)
        _, windows = AXUIElementCopyAttributeValue(app_ref, kAXWindowsAttribute, None)

        if not windows: return None, None
        q_bounds = target_meta.get(Quartz.kCGWindowBounds)
        for ax_win in windows:
            _, pos_raw = AXUIElementCopyAttributeValue(ax_win, kAXPositionAttribute, None)
            if pos_raw:
                return ax_win, pid

        return windows[0], pid

    def _get_window_raw(self, window_id):
        options = Quartz.kCGWindowListExcludeDesktopElements
        window_list = Quartz.CGWindowListCopyWindowInfo(options, Quartz.kCGNullWindowID)
        for win in window_list:
            if win.get(Quartz.kCGWindowNumber) == int(window_id):
                bounds = win.get(Quartz.kCGWindowBounds, {})
                return {
                    "pid": win.get(Quartz.kCGWindowOwnerPID),
                    "x": int(bounds.get('X', 0)),
                    "y": int(bounds.get('Y', 0)),
                    "w": int(bounds.get('Width', 0)),
                    "h": int(bounds.get('Height', 0))
                }
        return None

    def _set_window_geometry(self, window_id, x=None, y=None, w=None, h=None):
        ax_win, _ = self._get_ax_window(window_id)
        if not ax_win:
            raise RuntimeError(f"Could not find AX window for ID {window_id}")

        if x is not None and y is not None:
            pos_point = CGPoint(x, y)
            pos_value = AXValueCreate(kAXValueCGPointType, pos_point)
            AXUIElementSetAttributeValue(ax_win, kAXPositionAttribute, pos_value)

        if w is not None and h is not None:
            size_struct = CGSize(w, h)
            size_value = AXValueCreate(kAXValueCGSizeType, size_struct)
            AXUIElementSetAttributeValue(ax_win, kAXSizeAttribute, size_value)

        return {"x": x, "y": y, "width": w, "height": h}

    def move(self, window_id, dx, dy):
        info = self._get_window_raw(window_id)
        if info:
            self._history[window_id] = (info['x'], info['y'], info['w'], info['h'])
            new_x, new_y = info['x'] + dx, info['y'] + dy
            self._set_window_geometry(window_id, x=new_x, y=new_y)
            return {"window_id": window_id, "position": {"x": new_x, "y": new_y}}
        return None

    def move_to(self, window_id, x, y):
        info = self._get_window_raw(window_id)
        if info:
            self._history[window_id] = (info['x'], info['y'], info['w'], info['h'])
            self._set_window_geometry(window_id, x=x, y=y)
            return {"window_id": window_id, "position": {"x": x, "y": y}}
        return None

    def center(self, window_id):
        info = self._get_window_raw(window_id)
        if info:
            self._save_to_history(window_id, info)
            _, visible = self._get_screen_info()
            new_x = int(visible.origin.x + (visible.size.width - info['w']) / 2)
            new_y = int(visible.origin.y + (visible.size.height - info['h']) / 2)
            self._set_window_geometry(window_id, x=new_x, y=new_y)
            return {"window_id": window_id, "position": {"x": new_x, "y": new_y}}
        return None

    def center_on_display(self, window_id, display_id):
        info = self._get_window_raw(window_id)
        frame, visible = self._get_screen_info(display_id)
        if info:
            self._save_to_history(window_id, info)
            new_x = int(visible.origin.x + (visible.size.width - info['w']) / 2)
            new_y = int(
                frame.size.height - visible.origin.y - visible.size.height + (visible.size.height - info['h']) / 2)

            self._set_window_geometry(window_id, x=new_x, y=new_y)
            return {"window_id": window_id, "display_id": display_id, "position": {"x": new_x, "y": new_y}}
        return None

    def move_to_display(self, window_id, display_id):
        info = self._get_window_raw(window_id)
        frame, _ = self._get_screen_info(display_id)
        if info:
            self._save_to_history(window_id, info)
            self._set_window_geometry(window_id, x=int(frame.origin.x), y=int(frame.origin.y))
            return {"window_id": window_id, "display_id": display_id}
        return None

    def snap_left(self, window_id):
        info = self._get_window_raw(window_id)
        if not info: return None

        _, visible = self._get_screen_info()
        self._save_to_history(window_id, info)

        new_x = int(visible.origin.x)
        main_h = NSScreen.screens()[0].frame().size.height
        new_y = int(main_h - visible.origin.y - visible.size.height)

        new_w = int(visible.size.width / 2)
        new_h = int(visible.size.height)

        res = self._set_window_geometry(window_id, x=new_x, y=new_y, w=new_w, h=new_h)
        return {
            "window_id": window_id,
            "position": {"x": res['x'], "y": res['y']},
            "size": {"width": res['width'], "height": res['height']}
        }

    def snap_right(self, window_id):
        info = self._get_window_raw(window_id)
        if not info: return None

        _, visible = self._get_screen_info()
        self._save_to_history(window_id, info)

        new_w = int(visible.size.width / 2)
        new_h = int(visible.size.height)
        new_x = int(visible.origin.x + new_w)

        main_h = NSScreen.screens()[0].frame().size.height
        new_y = int(main_h - visible.origin.y - visible.size.height)

        res = self._set_window_geometry(window_id, x=new_x, y=new_y, w=new_w, h=new_h)
        return {
            "window_id": window_id,
            "position": {"x": res['x'], "y": res['y']},
            "size": {"width": res['width'], "height": res['height']}
        }

    def snap_top(self, window_id):
        info = self._get_window_raw(window_id)
        _, visible = self._get_screen_info()
        if info:
            self._save_to_history(window_id, info)
            h = int(visible.size.height / 2)
            res = self._set_window_geometry(window_id, x=int(visible.origin.x), y=int(visible.origin.y),
                                            w=int(visible.size.width), h=h)
            return {"window_id": window_id, "position": {"x": res['x'], "y": res['y']},
                    "size": {"width": res['width'], "height": res['height']}}
        return None

    def snap_bottom(self, window_id):
        info = self._get_window_raw(window_id)
        _, visible = self._get_screen_info()
        if info:
            self._save_to_history(window_id, info)
            h = int(visible.size.height / 2)
            res = self._set_window_geometry(window_id, x=int(visible.origin.x), y=int(visible.origin.y + h),
                                            w=int(visible.size.width), h=h)
            return {"window_id": window_id, "position": {"x": res['x'], "y": res['y']},
                    "size": {"width": res['width'], "height": res['height']}}
        return None

    def restore_position(self, window_id):
        win_id = int(window_id)

        if win_id in self._history:
            h_x, h_y, h_w, h_h = self._history[win_id]

            try:
                self._set_window_geometry(win_id, x=h_x, y=h_y, w=h_w, h=h_h)
                return {
                    "window_id": win_id,
                    "position": {"x": h_x, "y": h_y},
                    "size": {"width": h_w, "height": h_h}
                }
            except Exception as e:
                return None
        return None


class MacOSSize(WindowSize):
    def __init__(self):
        self._size_history = {}

    def _extract_ax_value(self, ax_value, ax_type):
        if ax_type == kAXValueCGPointType:
            ok, point = AXValueGetValue(ax_value, ax_type, None)
            return (point.x, point.y) if ok else (0, 0)
        elif ax_type == kAXValueCGSizeType:
            ok, size = AXValueGetValue(ax_value, ax_type, None)
            return (size.width, size.height) if ok else (0, 0)
        return 0, 0

    def _get_ax_window(self, window_id):
        q_info = self._get_win_raw(window_id)
        if not q_info: return None, None

        app_ref = AXUIElementCreateApplication(q_info['pid'])
        error, windows = AXUIElementCopyAttributeValue(app_ref, kAXWindowsAttribute, None)

        if error != kAXErrorSuccess or not windows:
            return None, None

        for ax_win in windows:
            _, pos_ref = AXUIElementCopyAttributeValue(ax_win, kAXPositionAttribute, None)
            _, size_ref = AXUIElementCopyAttributeValue(ax_win, kAXSizeAttribute, None)

            if pos_ref and size_ref:
                ax_x, ax_y = self._extract_ax_value(pos_ref, kAXValueCGPointType)
                ax_w, ax_h = self._extract_ax_value(size_ref, kAXValueCGSizeType)

                if abs(ax_x - q_info['x']) < 5 and abs(ax_y - q_info['y']) < 5:
                    return ax_win, q_info['pid']

        return windows[0], q_info['pid']

    def _set_window_geometry(self, window_id, x=None, y=None, w=None, h=None):
        ax_win, _ = self._get_ax_window(window_id)
        if not ax_win: return {}

        if x is not None and y is not None:
            val = AXValueCreate(kAXValueCGPointType, CGPoint(x, y))
            AXUIElementSetAttributeValue(ax_win, kAXPositionAttribute, val)

        if w is not None and h is not None:
            val = AXValueCreate(kAXValueCGSizeType, CGSize(w, h))
            AXUIElementSetAttributeValue(ax_win, kAXSizeAttribute, val)

        return {"x": x, "y": y, "width": w, "height": h}

    def _get_win_raw(self, window_id):
        options = Quartz.kCGWindowListExcludeDesktopElements
        window_list = Quartz.CGWindowListCopyWindowInfo(options, Quartz.kCGNullWindowID)
        for win in window_list:
            if win.get('kCGWindowNumber') == int(window_id):
                b = win.get('kCGWindowBounds', {})
                return {
                    "pid": win.get('kCGWindowOwnerPID'),
                    "w": int(b.get('Width', 0)), "h": int(b.get('Height', 0)),
                    "x": int(b.get('X', 0)), "y": int(b.get('Y', 0))
                }
        return None

    def _apply_size(self, window_id, width, height):
        try:
            res = self._set_window_geometry(window_id, w=width, h=height)
            return res
        except Exception as e:
            raise

    def resize(self, window_id, delta_width, delta_height):
        info = self._get_win_raw(window_id)
        if info:
            self._size_history[window_id] = (info['w'], info['h'])
            new_w, new_h = max(100, info['w'] + delta_width), max(100, info['h'] + delta_height)
            res = self._set_window_geometry(window_id, w=new_w, h=new_h)
            return {"window_id": window_id, "width": res.get("width"), "height": res.get("height")}
        return None

    def fit_to_display(self, window_id, display_id):
        info = self._get_win_raw(window_id)
        if not info: return None

        screens = NSScreen.screens()
        target = screens[0]
        for s in screens:
            if str(s.deviceDescription().objectForKey_("NSScreenNumber")) == str(display_id):
                target = s
                break

        vis = target.visibleFrame()
        main_h = screens[0].frame().size.height
        new_x, new_y = int(vis.origin.x), int(main_h - vis.origin.y - vis.size.height)
        new_w, new_h = int(vis.size.width), int(vis.size.height)

        self._size_history[window_id] = (info['w'], info['h'])
        self._set_window_geometry(window_id, x=new_x, y=new_y, w=new_w, h=new_h)
        return {"window_id": window_id, "bounds": {"x": new_x, "y": new_y, "width": new_w, "height": new_h}}

    def restore_size(self, window_id):
        if window_id in self._size_history:
            w, h = self._size_history[window_id]
            self._set_window_geometry(window_id, w=w, h=h)
            return {"width": w, "height": h}
        return None

    def resize_to(self, window_id, width, height):
        info = self._get_win_raw(window_id)
        if info:
            self._size_history[window_id] = (info['w'], info['h'])
            self._apply_size(window_id, width, height)
            return {"window_id": window_id, "size": {"width": width, "height": height}}
        return None

    def set_width(self, window_id, width):
        info = self._get_win_raw(window_id)
        if info:
            self._size_history[window_id] = (info['w'], info['h'])
            self._apply_size(window_id, width, info['h'])
            return {"width": width}
        return None

    def set_height(self, window_id, height):
        info = self._get_win_raw(window_id)
        if info:
            self._size_history[window_id] = (info['w'], info['h'])
            self._apply_size(window_id, info['w'], height)
            return {"height": height}
        return None

    def set_size(self, window_id, width, height):
        return self.resize_to(window_id, width, height)

    def maximize_to_display(self, window_id, display_id):
        return self.fit_to_display(window_id, display_id)


class MacOSState(WindowState):
    def _extract_ax_point(self, ax_value):
        if ax_value is None:
            return 0, 0
        ok, point = AXValueGetValue(ax_value, kAXValueCGPointType, None)
        return (point.x, point.y) if ok else (0, 0)

    def _get_ax_element(self, window_id):
        options = Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements
        window_list = Quartz.CGWindowListCopyWindowInfo(options, Quartz.kCGNullWindowID)

        target_meta = None
        for win in window_list:
            if win.get(Quartz.kCGWindowNumber) == int(window_id):
                target_meta = win
                break

        if not target_meta: return None, None

        pid = target_meta.get(Quartz.kCGWindowOwnerPID)
        app_ref = AXUIElementCreateApplication(pid)
        error, windows = AXUIElementCopyAttributeValue(app_ref, kAXWindowsAttribute, None)

        if error != kAXErrorSuccess or not windows: return None, pid

        q_bounds = target_meta.get(Quartz.kCGWindowBounds)
        for ax_win in windows:
            _, pos_ref = AXUIElementCopyAttributeValue(ax_win, kAXPositionAttribute, None)
            ax_x, ax_y = self._extract_ax_point(pos_ref)

            if abs(ax_x - q_bounds['X']) < 10 and abs(ax_y - q_bounds['Y']) < 10:
                return ax_win, pid

        return windows[0], pid

    def _extract_ax_point(self, ax_value):
        if ax_value is None: return 0, 0
        ok, point = AXValueGetValue(ax_value, kAXValueCGPointType, None)
        return (point.x, point.y) if ok else (0, 0)

    def _get_ax_element(self, window_id):
        options = Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements
        window_list = Quartz.CGWindowListCopyWindowInfo(options, Quartz.kCGNullWindowID)

        target_meta = None
        for win in window_list:
            if win.get(Quartz.kCGWindowNumber) == int(window_id):
                target_meta = win
                break

        if not target_meta: return None, None
        pid = target_meta.get(Quartz.kCGWindowOwnerPID)
        app_ref = AXUIElementCreateApplication(pid)
        error, windows = AXUIElementCopyAttributeValue(app_ref, kAXWindowsAttribute, None)

        if error != kAXErrorSuccess or not windows: return None, pid

        q_bounds = target_meta.get(Quartz.kCGWindowBounds)
        for ax_win in windows:
            _, pos_ref = AXUIElementCopyAttributeValue(ax_win, kAXPositionAttribute, None)
            ax_x, ax_y = self._extract_ax_point(pos_ref)
            if abs(ax_x - q_bounds['X']) < 10 and abs(ax_y - q_bounds['Y']) < 10:
                return ax_win, pid

        return windows[0], pid

    def get_state(self, window_id):
        ax_win, pid = self._get_ax_element(window_id)
        if not ax_win: return "unknown"

        workspace = NSWorkspace.sharedWorkspace()
        for app in workspace.runningApplications():
            if app.processIdentifier() == pid:
                if app.isHidden(): return "hidden"
                break

        _, is_min = AXUIElementCopyAttributeValue(ax_win, "AXMinimized", None)
        if is_min: return "minimized"

        _, is_full = AXUIElementCopyAttributeValue(ax_win, "AXFullScreen", None)
        if is_full: return "fullscreen"

        return "normal"

    def minimize(self, window_id):
        ax_win, _ = self._get_ax_element(window_id)
        if ax_win:
            error, children = AXUIElementCopyAttributeValue(ax_win, "AXChildren", None)
            for child in children or []:
                _, sub = AXUIElementCopyAttributeValue(child, kAXSubroleAttribute, None)
                if sub == "AXMinimizeButton":
                    AXUIElementPerformAction(child, kAXPressAction)
                    return {"window_id": window_id, "state": "minimized"}
        return None

    def maximize(self, window_id):
        ax_win, _ = self._get_ax_element(window_id)
        if ax_win:
            error, children = AXUIElementCopyAttributeValue(ax_win, "AXChildren", None)
            for child in children or []:
                _, sub = AXUIElementCopyAttributeValue(child, kAXSubroleAttribute, None)
                if sub == "AXZoomButton":
                    AXUIElementPerformAction(child, kAXPressAction)
                    return {"window_id": window_id, "state": "maximized"}
        return None

    def restore(self, window_id):
        ax_win, pid = self._get_ax_element(window_id)
        if ax_win:
            AXUIElementSetAttributeValue(ax_win, "AXMinimized", False)
            workspace = NSWorkspace.sharedWorkspace()
            for app in workspace.runningApplications():
                if app.processIdentifier() == pid:
                    app.activateWithOptions_(1)
            return {"window_id": window_id, "state": "normal"}
        return None

    def hide(self, window_id):
        _, pid = self._get_ax_element(window_id)
        if pid:
            subprocess.run(["osascript", "-e",
                            f'tell application "System Events" to set visible of first process whose unix id is {pid} to false'])
            return {"hidden": True}
        return None

    def show(self, window_id):
        _, pid = self._get_ax_element(window_id)
        if pid:
            subprocess.run(["osascript", "-e",
                            f'tell application "System Events" to set visible of first process whose unix id is {pid} to true'])
            return {"visible": True}
        return None

    def toggle_visibility(self, window_id):
        state = self.get_state(window_id)
        return self.show(window_id) if state == "hidden" else self.hide(window_id)

    def toggle_state(self, window_id):
        return self.maximize(window_id)

    def set_state(self, window_id, state):
        if state == "minimized":
            return self.minimize(window_id)

        if state == "maximized":
            return self.maximize(window_id)

        if state == "normal":
            return self.restore(window_id)

        if state == "hidden":
            return self.hide(window_id)

        if state == "fullscreen":
            ax_win, _ = self._get_ax_element(window_id)
            if ax_win:
                AXUIElementSetAttributeValue(ax_win, "AXFullScreen", True)
                return {"window_id": window_id, "state": "fullscreen"}

        return None


class MacOSAppearance(WindowAppearance):
    def _extract_ax_point(self, ax_value):
        if ax_value is None: return 0, 0
        ok, point = AXValueGetValue(ax_value, kAXValueCGPointType, None)
        return (point.x, point.y) if ok else (0, 0)

    def _get_ax_element_with_pid(self, window_id):
        options = Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements
        window_list = Quartz.CGWindowListCopyWindowInfo(options, Quartz.kCGNullWindowID)

        target_meta = None
        for win in window_list:
            if win.get(Quartz.kCGWindowNumber) == int(window_id):
                target_meta = win
                break

        if not target_meta: return None, None

        pid = target_meta.get(Quartz.kCGWindowOwnerPID)
        app_ref = AXUIElementCreateApplication(pid)
        error, windows = AXUIElementCopyAttributeValue(app_ref, kAXWindowsAttribute, None)

        if error != kAXErrorSuccess or not windows:
            return None, pid

        q_bounds = target_meta.get(Quartz.kCGWindowBounds)
        for ax_win in windows:
            _, pos_ref = AXUIElementCopyAttributeValue(ax_win, kAXPositionAttribute, None)
            ax_x, ax_y = self._extract_ax_point(pos_ref)
            if abs(ax_x - q_bounds['X']) < 10 and abs(ax_y - q_bounds['Y']) < 10:
                return ax_win, pid

        return windows[0], pid

    def set_always_on_top(self, window_id, enabled):
        ax_win, pid = self._get_ax_element_with_pid(window_id)
        if not ax_win: return None

        level = 5 if enabled else 3
        error = AXUIElementSetAttributeValue(ax_win, "AXWindowLevel", level)

        if error == kAXErrorSuccess:
            return {"window_id": window_id, "always_on_top": enabled}

        script = f'''
        tell application "System Events"
            tell (first application process whose unix id is {pid})
                try
                    click menu item "Float on Top" of menu 1 of menu bar item "Window" of menu bar 1
                on error
                    click menu item "Поверх всех окон" of menu 1 of menu bar item "Окно" of menu bar 1
                end try
            end tell
        end tell
        '''
        subprocess.run(["osascript", "-e", script], capture_output=True)
        return {"window_id": window_id, "always_on_top": enabled, "info": "requested via script"}

    def remove_always_on_top(self, window_id):
        return self.set_always_on_top(window_id, False)

    def get_always_on_top(self, window_id):
        ax_win, _ = self._get_ax_element_with_pid(window_id)
        if ax_win:
            _, level = AXUIElementCopyAttributeValue(ax_win, "AXWindowLevel", None)
            return {"always_on_top": (level or 3) >= 5}
        return {"always_on_top": False}

    def set_opacity(self, window_id, opacity):
        ax_win, _ = self._get_ax_element_with_pid(window_id)
        if ax_win:
            val = max(0.0, min(1.0, float(opacity)))
            AXUIElementSetAttributeValue(ax_win, "AXAlphaValue", val)
            return {"window_id": window_id, "opacity": val}
        return None

    def get_opacity(self, window_id):
        ax_win, _ = self._get_ax_element_with_pid(window_id)
        if ax_win:
            _, val = AXUIElementCopyAttributeValue(ax_win, "AXAlphaValue", None)
            return {"opacity": round(float(val or 1.0), 2)}
        return {"opacity": 1.0}

    def set_fullscreen(self, window_id, enabled):
        ax_win, _ = self._get_ax_element_with_pid(window_id)
        if ax_win:
            AXUIElementSetAttributeValue(ax_win, "AXFullScreen", bool(enabled))
            return {"window_id": window_id, "fullscreen": enabled}
        return None

    def toggle_fullscreen(self, window_id):
        ax_win, _ = self._get_ax_element_with_pid(window_id)
        if ax_win:
            _, current = AXUIElementCopyAttributeValue(ax_win, "AXFullScreen", None)
            new_val = not bool(current)
            self.set_fullscreen(window_id, new_val)
            return {"window_id": window_id, "fullscreen": new_val}
        return None

    def exit_fullscreen(self, window_id):
        return self.set_fullscreen(window_id, False)


class MacOSHierarchy(WindowHierarchy):
    def _get_raw_windows(self):
        return Quartz.CGWindowListCopyWindowInfo(
            Quartz.kCGWindowListExcludeDesktopElements | Quartz.kCGWindowListOptionOnScreenOnly,
            Quartz.kCGNullWindowID
        )

    def get_parent(self, window_id):
        owner = self.get_owner(window_id)
        if not owner: return None

        script = f'''
        tell application "System Events"
            tell (first process whose unix id is {owner['pid']})
                try
                    set win to first window whose id is {window_id}
                    return id of parent of win
                end try
            end tell
        end tell
        '''
        try:
            res = subprocess.check_output(["osascript", "-e", script], text=True).strip()
            return {"parent_window_id": int(res)} if res else None
        except:
            return None

    def get_children(self, window_id):
        owner = self.get_owner(window_id)
        if not owner: return []

        script = f'''
        tell application "System Events"
            tell (first process whose unix id is {owner['pid']})
                set child_ids to id of every window whose parent's id is {window_id}
                return child_ids
            end tell
        end tell
        '''
        try:
            res = subprocess.check_output(["osascript", "-e", script], text=True).strip()
            if not res: return {"children": []}
            ids = [int(i.strip()) for i in res.split(",")]
            return {"children": ids}
        except:
            return {"children": []}

    def get_owner(self, window_id):
        wins = self._get_raw_windows()
        for win in wins:
            if win.get('kCGWindowNumber') == int(window_id):
                return {
                    "application": win.get('kCGWindowOwnerName'),
                    "pid": win.get('kCGWindowOwnerPID')
                }
        return None

    def get_app_windows(self, app_name):
        wins = self._get_raw_windows()
        app_windows = []
        for win in wins:
            if app_name.lower() in win.get('kCGWindowOwnerName', '').lower():
                bounds = win.get('kCGWindowBounds', {})
                app_windows.append({
                    "id": win.get('kCGWindowNumber'),
                    "title": win.get('kCGWindowName', 'Unknown'),
                    "position": {"x": int(bounds.get('X')), "y": int(bounds.get('Y'))},
                    "size": {"width": int(bounds.get('Width')), "height": int(bounds.get('Height'))}
                })
        return {"windows": app_windows}

    def get_hierarchy(self, window_id):
        info = None
        wins = self._get_raw_windows()
        for win in wins:
            if win.get('kCGWindowNumber') == int(window_id):
                info = {
                    "id": win.get('kCGWindowNumber'),
                    "title": win.get('kCGWindowName', ''),
                    "app": win.get('kCGWindowOwnerName')
                }
                break

        if not info: return None

        children = self.get_children(window_id).get("children", [])
        child_trees = [self.get_hierarchy(cid) for i, cid in enumerate(children)]

        return {
            "window": info,
            "children": child_trees
        }


class MacOSDisplay(WindowDisplay):
    def _get_screens_list(self):
        return sorted(NSScreen.screens(), key=lambda s: s.frame().origin.x)

    def _get_win_raw(self, window_id):
        options = Quartz.kCGWindowListExcludeDesktopElements
        window_list = Quartz.CGWindowListCopyWindowInfo(options, Quartz.kCGNullWindowID)
        for win in window_list:
            if win.get('kCGWindowNumber') == int(window_id):
                bounds = win.get('kCGWindowBounds', {})
                return {
                    "pid": win.get('kCGWindowOwnerPID'),
                    "x": int(bounds.get('X', 0)),
                    "y": int(bounds.get('Y', 0)),
                    "w": int(bounds.get('Width', 0)),
                    "h": int(bounds.get('Height', 0))
                }
        return None

    def get_window_display(self, window_id):
        info = self._get_win_raw(window_id)
        if not info: return None

        cx = info['x'] + info['w'] / 2
        cy = info['y'] + info['h'] / 2

        for screen in NSScreen.screens():
            frame = screen.frame()
            screen_x = frame.origin.x
            screen_y = NSScreen.screens()[0].frame().size.height - frame.origin.y - frame.size.height

            if (screen_x <= cx <= screen_x + frame.size.width and
                    screen_y <= cy <= screen_y + frame.size.height):
                return {"display_id": int(screen.deviceDescription().objectForKey_("NSScreenNumber"))}
        return None

    def move_to_display(self, window_id, display_id):
        info = self._get_win_raw(window_id)
        if not info: return None

        target_screen = None
        for s in NSScreen.screens():
            if str(s.deviceDescription().objectForKey_("NSScreenNumber")) == str(display_id):
                target_screen = s
                break

        if target_screen:
            visible = target_screen.visibleFrame()
            main_h = NSScreen.screens()[0].frame().size.height
            new_x = int(visible.origin.x)
            new_y = int(main_h - visible.origin.y - visible.size.height)

            script = f'''
            tell application "System Events"
                tell (first process whose unix id is {info['pid']})
                    set position of window id {window_id} to {{{new_x}, {new_y}}}
                end tell
            end tell
            '''
            subprocess.run(["osascript", "-e", script], check=True)
            return {"window_id": window_id, "display_id": display_id}
        return None

    def move_to_next(self, window_id):
        current = self.get_window_display(window_id)
        if not current: return None

        screens = self._get_screens_list()
        current_id = current['display_id']

        next_id = None
        for i, s in enumerate(screens):
            sid = int(s.deviceDescription().objectForKey_("NSScreenNumber"))
            if sid == current_id:
                next_index = (i + 1) % len(screens)
                next_id = int(screens[next_index].deviceDescription().objectForKey_("NSScreenNumber"))
                break

        if next_id:
            self.move_to_display(window_id, next_id)
            return {"window_id": window_id, "display_id": next_id}
        return None

    def move_to_previous(self, window_id):
        current = self.get_window_display(window_id)
        if not current: return None

        screens = self._get_screens_list()
        current_id = current['display_id']

        prev_id = None
        for i, s in enumerate(screens):
            sid = int(s.deviceDescription().objectForKey_("NSScreenNumber"))
            if sid == current_id:
                prev_index = (i - 1) % len(screens)
                prev_id = int(screens[prev_index].deviceDescription().objectForKey_("NSScreenNumber"))
                break

        if prev_id:
            self.move_to_display(window_id, prev_id)
            return {"window_id": window_id, "display_id": prev_id}
        return None

    def center_on_display(self, window_id, display_id):
        info = self._get_win_raw(window_id)
        if not info: return None

        for s in NSScreen.screens():
            if str(s.deviceDescription().objectForKey_("NSScreenNumber")) == str(display_id):
                visible = s.visibleFrame()
                main_h = NSScreen.screens()[0].frame().size.height

                new_x = int(visible.origin.x + (visible.size.width - info['w']) / 2)
                new_y = int(main_h - visible.origin.y - visible.size.height + (visible.size.height - info['h']) / 2)

                script = f'''
                tell application "System Events"
                    tell (first process whose unix id is {info['pid']})
                        set position of window id {window_id} to {{{new_x}, {new_y}}}
                    end tell
                end tell
                '''
                subprocess.run(["osascript", "-e", script], check=True)
                return {"window_id": window_id, "display_id": display_id, "position": {"x": new_x, "y": new_y}}
        return None

    def maximize_on_display(self, window_id, display_id):
        info = self._get_win_raw(window_id)
        if not info: return None

        for s in NSScreen.screens():
            if str(s.deviceDescription().objectForKey_("NSScreenNumber")) == str(display_id):
                visible = s.visibleFrame()
                main_h = NSScreen.screens()[0].frame().size.height

                new_x = int(visible.origin.x)
                new_y = int(main_h - visible.origin.y - visible.size.height)
                new_w = int(visible.size.width)
                new_h = int(visible.size.height)

                script = f'''
                tell application "System Events"
                    tell (first process whose unix id is {info['pid']})
                        set position of window id {window_id} to {{{new_x}, {new_y}}}
                        set size of window id {window_id} to {{{new_w}, {new_h}}}
                    end tell
                end tell
                '''
                subprocess.run(["osascript", "-e", script], check=True)
                return {"window_id": window_id, "display_id": display_id, "bounds": {"width": new_w, "height": new_h}}
        return None


class MacOSArrangement(WindowArrangement):
    def _extract_ax_val(self, ax_value, ax_type):
        if ax_value is None: return (0, 0)
        ok, val = AXValueGetValue(ax_value, ax_type, None)
        if ax_type == kAXValueCGPointType: return (val.x, val.y) if ok else (0, 0)
        return (val.width, val.height) if ok else (0, 0)

    def _get_ax_window(self, window_id):
        q_info = self._get_win_raw(window_id)
        if not q_info: return None

        app_ref = AXUIElementCreateApplication(q_info['pid'])
        _, windows = AXUIElementCopyAttributeValue(app_ref, kAXWindowsAttribute, None)
        if not windows: return None

        for ax_win in windows:
            _, pos_ref = AXUIElementCopyAttributeValue(ax_win, kAXPositionAttribute, None)
            ax_x, ax_y = self._extract_ax_val(pos_ref, kAXValueCGPointType)
            if abs(ax_x - q_info['x']) < 15:
                return ax_win
        return windows[0]

    def _apply(self, window_id, x, y, w, h):
        ax_win = self._get_ax_window(window_id)
        if not ax_win: return

        pos_val = AXValueCreate(kAXValueCGPointType, CGPoint(x, y))
        AXUIElementSetAttributeValue(ax_win, kAXPositionAttribute, pos_val)

        size_val = AXValueCreate(kAXValueCGSizeType, CGSize(w, h))
        AXUIElementSetAttributeValue(ax_win, kAXSizeAttribute, size_val)

    def _get_work_area(self):
        screen = NSScreen.screens()[0]
        vis = screen.visibleFrame()
        main_h = screen.frame().size.height
        return {
            "x": int(vis.origin.x),
            "y": int(main_h - vis.origin.y - vis.size.height),
            "w": int(vis.size.width),
            "h": int(vis.size.height)
        }

    def _get_win_raw(self, window_id):
        options = Quartz.kCGWindowListExcludeDesktopElements
        window_list = Quartz.CGWindowListCopyWindowInfo(options, Quartz.kCGNullWindowID)
        for win in window_list:
            if win.get('kCGWindowNumber') == int(window_id):
                b = win.get('kCGWindowBounds', {})
                return {
                    "pid": win.get('kCGWindowOwnerPID'),
                    "x": int(b.get('X', 0)), "y": int(b.get('Y', 0)),
                    "w": int(b.get('Width', 0)), "h": int(b.get('Height', 0))
                }
        return None

    def grid(self, window_ids, rows, columns):
        area = self._get_work_area()
        cell_w = area['w'] // columns
        cell_h = area['h'] // rows

        for i, wid in enumerate(window_ids):
            if i >= rows * columns: break
            row, col = i // columns, i % columns

            new_x = area['x'] + (col * cell_w)
            new_y = area['y'] + (row * cell_h)
            self._apply(wid, new_x, new_y, cell_w, cell_h)

        return {"arranged": True}

    def tile(self, window_ids):
        n = len(window_ids)
        if n == 0: return None
        cols = math.ceil(math.sqrt(n))
        rows = math.ceil(n / cols)
        return self.grid(window_ids, rows, cols)

    def arrange(self, window_ids, layout):
        area = self._get_work_area()
        n = len(window_ids)
        if n == 0: return None

        results = []
        for i, wid in enumerate(window_ids):
            info = self._get_win_raw(wid)
            if not info: continue

            if layout == "horizontal":
                new_w = area['w'] // n
                new_h = area['h']
                new_x = area['x'] + (i * new_w)
                new_y = area['y']
            else:
                new_w = area['w']
                new_h = area['h'] // n
                new_x = area['x']
                new_y = area['y'] + (i * new_h)

            self._apply(wid, new_x, new_y, new_w, new_h)
            results.append({"id": wid, "x": new_x, "y": new_y})

        return {"arranged": True, "windows": results}

    def cascade(self, window_ids):
        area = self._get_work_area()
        offset = 30
        results = []
        for i, wid in enumerate(window_ids):
            info = self._get_win_raw(wid)
            if not info: continue
            new_x = area['x'] + (i * offset)
            new_y = area['y'] + (i * offset)

            new_w = min(info['w'], area['w'] - (i * offset))
            new_h = min(info['h'], area['h'] - (i * offset))
            self._apply(wid, new_x, new_y, new_w, new_h)
            results.append(wid)
        return {"arranged": True}

    def stack(self, window_ids):
        area = self._get_work_area()
        new_w, new_h = int(area['w'] * 0.8), int(area['h'] * 0.8)
        new_x = area['x'] + (area['w'] - new_w) // 2
        new_y = area['y'] + (area['h'] - new_h) // 2

        for wid in window_ids:
            info = self._get_win_raw(wid)
            if info:
                self._apply(wid, new_x, new_y, new_w, new_h)
        return {"arranged": True}

    def arrange_app(self, app_name, layout):
        options = Quartz.kCGWindowListExcludeDesktopElements | Quartz.kCGWindowListOptionOnScreenOnly
        window_list = Quartz.CGWindowListCopyWindowInfo(options, Quartz.kCGNullWindowID)
        app_wids = [w.get('kCGWindowNumber') for w in window_list
                    if app_name.lower() in w.get('kCGWindowOwnerName', '').lower()
                    and w.get('kCGWindowLayer') == 0]

        if layout == "tile":
            return self.tile(app_wids)
        return self.arrange(app_wids, layout)

    def equalize(self, window_ids):
        if not window_ids: return None
        reference = self._get_win_raw(window_ids[0])
        if not reference: return None

        for wid in window_ids[1:]:
            info = self._get_win_raw(wid)
            if info:
                win_opts = Quartz.kCGWindowListExcludeDesktopElements
                w_list = Quartz.CGWindowListCopyWindowInfo(win_opts, Quartz.kCGNullWindowID)
                curr = next((w for w in w_list if w.get('kCGWindowNumber') == wid), None)
                if curr:
                    b = curr.get('kCGWindowBounds')
                    self._apply(wid, int(b['X']), int(b['Y']), reference['w'], reference['h'])

        return {"equalized": True}


class MacOSGroups(WindowGroups):
    def __init__(self):
        self._groups = {}

    def _extract_point(self, ax_value):
        if ax_value is None: return (0, 0)
        ok, point = AXValueGetValue(ax_value, kAXValueCGPointType, None)
        return (point.x, point.y) if ok else (0, 0)

    def _get_ax_window(self, window_id):
        options = Quartz.kCGWindowListExcludeDesktopElements | Quartz.kCGWindowListOptionOnScreenOnly
        window_list = Quartz.CGWindowListCopyWindowInfo(options, Quartz.kCGNullWindowID)

        target_meta = next((w for w in window_list if w.get(Quartz.kCGWindowNumber) == int(window_id)), None)
        if not target_meta: return None

        pid = target_meta.get(Quartz.kCGWindowOwnerPID)
        app_ref = AXUIElementCreateApplication(pid)
        _, windows = AXUIElementCopyAttributeValue(app_ref, kAXWindowsAttribute, None)

        if not windows: return None

        q_bounds = target_meta.get(Quartz.kCGWindowBounds)
        for ax_win in windows:
            _, pos_ref = AXUIElementCopyAttributeValue(ax_win, kAXPositionAttribute, None)
            ax_x, ax_y = self._extract_point(pos_ref)
            if abs(ax_x - q_bounds['X']) < 10:
                return ax_win
        return windows[0]

    def group(self, window_ids, group_name):
        ids = list(window_ids)
        self.ungroup(ids)

        if group_name not in self._groups:
            self._groups[group_name] = []

        self._groups[group_name].extend(ids)
        return {"group": group_name, "windows": self._groups[group_name]}

    def ungroup(self, window_ids):
        ids = list(window_ids)
        for name in list(self._groups.keys()):
            self._groups[name] = [wid for wid in self._groups[name] if wid not in ids]
            if not self._groups[name]: del self._groups[name]
        return {"ungrouped": ids}

    def get_group(self, window_id):
        for name, ids in self._groups.items():
            if int(window_id) in ids:
                return {"group": name}
        return {"group": None}

    def get_all_groups(self):

        return {"groups": [{"name": k, "windows": v} for k, v in self._groups.items()]}

    def activate(self, group_name):
        ids = self._groups.get(group_name, [])
        if not ids:
            return None

        workspace = NSWorkspace.sharedWorkspace()

        for wid in ids:
            ax_win = self._get_ax_window(wid)
            if ax_win:
                options = Quartz.kCGWindowListExcludeDesktopElements
                w_list = Quartz.CGWindowListCopyWindowInfo(options, Quartz.kCGNullWindowID)
                meta = next((w for w in w_list if w.get(Quartz.kCGWindowNumber) == wid), None)

                if meta:
                    pid = meta.get(Quartz.kCGWindowOwnerPID)
                    app = next((a for a in workspace.runningApplications() if a.processIdentifier() == pid), None)
                    if app:
                        app.activateWithOptions_(NSApplicationActivateIgnoringOtherApps)

                AXUIElementPerformAction(ax_win, kAXRaiseAction)

        return {"group": group_name, "activated": True}

    def arrange(self, group_name, layout):
        from deskagent.platform.macos.window import MacOSArrangement
        ids = self._groups.get(group_name, [])
        if ids:
            arranger = MacOSArrangement()
            return arranger.arrange(ids, layout)
        return None


class MacOSLifecycle(WindowLifecycle):
    def _extract_point(self, ax_value):
        if ax_value is None: return (0, 0)
        ok, point = AXValueGetValue(ax_value, kAXValueCGPointType, None)
        return (point.x, point.y) if ok else (0, 0)

    def _get_ax_window(self, window_id):
        options = Quartz.kCGWindowListExcludeDesktopElements | Quartz.kCGWindowListOptionOnScreenOnly
        window_list = Quartz.CGWindowListCopyWindowInfo(options, Quartz.kCGNullWindowID)

        target_meta = next((w for w in window_list if w.get(Quartz.kCGWindowNumber) == int(window_id)), None)
        if not target_meta: return None

        pid = target_meta.get(Quartz.kCGWindowOwnerPID)
        app_ref = AXUIElementCreateApplication(pid)
        _, windows = AXUIElementCopyAttributeValue(app_ref, kAXWindowsAttribute, None)

        if not windows: return None

        q_bounds = target_meta.get(Quartz.kCGWindowBounds)
        for ax_win in windows:
            _, pos_ref = AXUIElementCopyAttributeValue(ax_win, kAXPositionAttribute, None)
            ax_x, ax_y = self._extract_point(pos_ref)
            if abs(ax_x - q_bounds['X']) < 15:
                return ax_win
        return windows[0]

    def _get_win_raw(self, window_id=None, title=None):
        options = Quartz.kCGWindowListExcludeDesktopElements
        window_list = Quartz.CGWindowListCopyWindowInfo(options, Quartz.kCGNullWindowID)
        for win in window_list:
            if window_id and win.get(Quartz.kCGWindowNumber) == int(window_id):
                return win
            if title and title.lower() in win.get(Quartz.kCGWindowName, '').lower():
                return win
        return None

    def close(self, window_id):
        ax_win = self._get_ax_window(window_id)
        if not ax_win:
            raise ValueError(f"Window {window_id} was not found in the system.")

        _, children = AXUIElementCopyAttributeValue(ax_win, "AXChildren", None)
        close_btn = None
        for child in children or []:
            _, sub = AXUIElementCopyAttributeValue(child, kAXSubroleAttribute, None)
            if sub == "AXCloseButton":
                close_btn = child
                break

        if close_btn:
            AXUIElementPerformAction(close_btn, kAXPressAction)
            return {"closed": True, "window_id": window_id}

        AXUIElementPerformAction(ax_win, "AXCancel")
        return {"closed": True, "window_id": window_id, "method": "fallback_cancel"}

    def close_multiple(self, window_ids):
        results = {"closed": [], "failed": []}
        for wid in window_ids:
            try:
                self.close(wid)
                results["closed"].append(wid)
            except:
                results["failed"].append(wid)
        return results

    def close_app_windows(self, app_name):
        options = Quartz.kCGWindowListExcludeDesktopElements | Quartz.kCGWindowListOptionOnScreenOnly
        window_list = Quartz.CGWindowListCopyWindowInfo(options, Quartz.kCGNullWindowID)

        count = 0
        for win in window_list:
            if app_name.lower() in win.get('kCGWindowOwnerName', '').lower() and win.get('kCGWindowLayer') == 0:
                try:
                    self.close(win.get(Quartz.kCGWindowNumber))
                    count += 1
                except:
                    continue
        return {"closed_count": count}

    def wait_for_window(self, title, timeout=10):
        start_time = time.time()
        while time.time() - start_time < timeout:
            win = self._get_win_raw(title=title)
            if win:
                bounds = win.get('kCGWindowBounds', {})
                return {
                    "found": True,
                    "window": {
                        "id": win.get('kCGWindowNumber'),
                        "title": win.get('kCGWindowName'),
                        "position": {"x": int(bounds.get('X')), "y": int(bounds.get('Y'))}
                    }
                }
            time.sleep(0.5)
        raise TimeoutError(f"Window with title '{title}' not found within {timeout}s")

    def wait_for_close(self, window_id, timeout=10):
        start_time = time.time()
        while time.time() - start_time < timeout:
            if not self._get_win_raw(window_id=window_id):
                return {"closed": True}
            time.sleep(0.5)
        raise TimeoutError(f"Window {window_id} did not close within {timeout}s")

    def wait_for_visibility(self, window_id, timeout=10, visible=True):
        start_time = time.time()
        while time.time() - start_time < timeout:
            win = self._get_win_raw(window_id=window_id)
            if win:
                is_on_screen = bool(win.get('kCGWindowIsOnscreen'))
                if is_on_screen == visible:
                    return {"visible": is_on_screen}
            time.sleep(0.5)
        raise TimeoutError(f"Window visibility did not match '{visible}' within {timeout}s")

    def wait_for_active(self, window_id, timeout=10):
        start_time = time.time()
        workspace = NSWorkspace.sharedWorkspace()
        while time.time() - start_time < timeout:
            active_app = workspace.frontmostApplication()
            active_pid = active_app.processIdentifier()

            win = self._get_win_raw(window_id=window_id)
            if win and win.get('kCGWindowOwnerPID') == active_pid:
                return {"active": True}
            time.sleep(0.5)
        raise TimeoutError(f"Window {window_id} did not become active within {timeout}s")
