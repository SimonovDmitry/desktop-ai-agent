from subprocess import run, check_output
from AppKit import NSEvent, NSScreen
from AppKit import NSPasteboard, NSStringPboardType
from deskagent.actions.base import Action
import psutil
import Quartz
from AppKit import NSWorkspace
import objc
import re
import socket
import time
from datetime import datetime



class GetActiveWindow(Action):
    def __init__(self, logger=None):
        super().__init__(logger)

    def execute(self, config=None):
        # TODO переделать плохая реализация
        try:
            # 1. Получаем информацию об активном приложении (через Workspace)
            active_app = NSWorkspace.sharedWorkspace().frontmostApplication()
            app_name = active_app.localizedName()
            app_pid = active_app.processIdentifier()

            # 2. Получаем список всех окон на экране
            # kCGWindowListOptionOnScreenOnly = 1 (только видимые)
            # kCGWindowListExcludeDesktopElements = 16 (без иконок рабочего стола)
            options = Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements
            window_list = Quartz.CGWindowListCopyWindowInfo(options, Quartz.kCGNullWindowID)

            active_window_info = {}

            # 3. Ищем окно, которое принадлежит нашему активному PID
            # В списке окон самое первое окно с нужным PID обычно и есть активное
            for window in window_list:
                if window.get('kCGWindowOwnerPID') == app_pid:
                    # Некоторые окна могут быть системными или не иметь названия
                    # Слой 0 (kCGWindowLayer) обычно означает основное окно приложения
                    if window.get('kCGWindowLayer') == 0:
                        bounds = window.get('kCGWindowBounds')

                        active_window_info = {
                            "application": app_name,
                            "process_id": app_pid,
                            "window_id": window.get('kCGWindowNumber'),
                            "title": window.get('kCGWindowName', 'Unknown Title'),
                            "bounds": {
                                "x": int(bounds.get('X')),
                                "y": int(bounds.get('Y')),
                                "width": int(bounds.get('Width')),
                                "height": int(bounds.get('Height'))
                            }
                        }
                        break

            if not active_window_info:
                # Если не нашли конкретное окно, возвращаем хотя бы инфо о приложении
                return {"application": app_name, "process_id": app_pid, "status": "window_not_found"}

            print(f"--- Активное окно: {active_window_info['application']} ---")
            print(f"Заголовок: {active_window_info['title']}")
            print(f"Размеры: {active_window_info['bounds']['width']}x{active_window_info['bounds']['height']}")

            return active_window_info

        except Exception as e:
            print(f"Ошибка при получении активного окна: {e}")
            return None



# TODO


class SendNotification(Action):
    def __init__(self, logger=None):
        Action.__init__(self, logger)

    def execute(self, config=None):
        # TODO не работает
        title = config.get('title', 'DeskAgent')
        message = config.get('message', '')
        subtitle = config.get('subtitle', '')

        script = f'display notification "{message}" with title "{title}"'
        if subtitle:
            script += f' subtitle "{subtitle}"'

        try:
            run(['osascript', '-e', script], check=True)
            return {"success": True, "notification_id": None}
        except Exception:
            return {"success": False, "notification_id": None}

c = SendNotification()
print(c.execute({'subtitle': 'Network Interface', 'title': 'Network Interfaces'}))

