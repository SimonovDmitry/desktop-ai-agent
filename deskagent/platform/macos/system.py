import time
import platform
import pwd
import getpass
import re
import psutil
import socket
from datetime import datetime
from urllib.request import urlopen
from subprocess import run, check_output
import ctypes
from ctypes import c_uint32, c_float, c_double
from AppKit import NSEvent, NSScreen, NSPasteboard, NSStringPboardType, NSWorkspace
from Quartz import (CGEventCreateMouseEvent, CGEventPost, kCGHIDEventTap, kCGEventMouseMoved, kCGEventLeftMouseDown,
                    kCGEventLeftMouseUp, kCGEventRightMouseDown, kCGEventRightMouseUp, kCGEventOtherMouseDown,
                    kCGEventOtherMouseUp, kCGMouseButtonLeft, kCGMouseButtonRight, kCGMouseButtonCenter,
                    CGEventCreateScrollWheelEvent, kCGScrollEventUnitLine, CGMainDisplayID, CGDisplayModeGetWidth,
                    CGDisplayCopyAllDisplayModes, CGDisplaySetDisplayMode, CGDisplayModeGetHeight,
                    CGDisplayModeGetPixelWidth, CGDisplayModeGetPixelHeight, CGDisplayModeGetRefreshRate,
                    CGDisplayModeIsUsableForDesktopGUI, kCGEventLeftMouseDragged)
from Foundation import NSUserNotification, NSUserNotificationCenter
from deskagent.platform.base.system import (SystemAudio, SystemClipboard, SystemDisplay, SystemInformation,
                                            SystemMouse, SystemNetwork, SystemNotification, SystemPower)


class MacOSSystemAudio(SystemAudio):
    def _clamp(self, value):
        return max(0, min(100, value))

    def set_volume(self, volume):
        if not isinstance(volume, (int, float)) or not 0 <= volume <= 100:
            raise ValueError('Volume level must be a number between 0 and 100')
        run(["osascript", "-e", f"set volume output volume {int(volume)}"])

    def get_volume(self):
        cmd = ['osascript', '-e', 'output volume of (get volume settings)']
        return int(check_output(cmd).decode('utf-8').strip())

    def increase_volume(self, step=10):
        current = self.get_volume()
        self.set_volume(self._clamp(current + step))

    def decrease_volume(self, step=10):
        current = self.get_volume()
        self.set_volume(self._clamp(current - step))

    def mute(self):
        run(["osascript", "-e", "set volume output muted true"])

    def unmute(self):
        run(["osascript", "-e", "set volume output muted false"])


class MacOSSystemClipboard(SystemClipboard):
    def get_clipboard(self):
        pb = NSPasteboard.generalPasteboard()
        return pb.stringForType_(NSStringPboardType)

    def set_clipboard(self, text):
        pb = NSPasteboard.generalPasteboard()
        pb.clearContents()
        pb.setString_forType_(text, NSStringPboardType)

    def clean_clipboard(self):
        pb = NSPasteboard.generalPasteboard()
        pb.clearContents()


class MacOSSystemDisplay(SystemDisplay):
    def _get_display_services(self):
        try:
            framework = ctypes.CDLL("/System/Library/PrivateFrameworks/DisplayServices.framework/DisplayServices")

            get_brightness = framework.DisplayServicesGetBrightness
            get_brightness.argtypes = [c_uint32, ctypes.POINTER(c_float)]
            get_brightness.restype = ctypes.c_int

            set_brightness = framework.DisplayServicesSetBrightness
            set_brightness.argtypes = [c_uint32, c_float]
            set_brightness.restype = ctypes.c_int

            return get_brightness, set_brightness

        except (OSError, AttributeError):
            return None, None

    def set_display_brightness(self, brightness_level):
        if not isinstance(brightness_level, (int, float)):
            raise ValueError("Brightness level must be a number")

        if not 0 <= brightness_level <= 100:
            raise ValueError("Brightness must be between 0 and 100")

        _, set_brightness = self._get_display_services()

        if set_brightness is None:
            raise NotImplementedError("DisplayServices brightness API is not available")

        display_id = CGMainDisplayID()
        value = float(brightness_level) / 100.0
        result = set_brightness(display_id, c_float(value))

        if result != 0:
            raise RuntimeError(f"DisplayServicesSetBrightness failed with code {result}")

    def get_display_brightness(self):
        get_brightness, _ = self._get_display_services()

        if get_brightness is None:
            raise NotImplementedError("DisplayServices brightness API is not available")

        display_id = CGMainDisplayID()
        brightness = c_float()
        result = get_brightness(display_id, ctypes.byref(brightness))

        if result != 0:
            raise RuntimeError(f"DisplayServicesGetBrightness failed with code {result}")

        value = max(0.0, min(1.0, brightness.value))
        return round(value * 100, 2)

    def get_displays(self):
        screens = NSScreen.screens()
        displays_info = []
        for i, screen in enumerate(screens):
            frame = screen.frame()
            description = screen.deviceDescription()
            display_id = description.objectForKey_("NSScreenNumber")
            is_primary = (i == 0)
            name = "Built-in Display" if is_primary and len(screens) == 1 else (f"Primary" if is_primary else f"External {i}")
            displays_info.append({
                "id": str(display_id), "name": name, "primary": is_primary,
                "width": int(frame.size.width), "height": int(frame.size.height),
                "x": int(frame.origin.x), "y": int(frame.origin.y)
            })
        return displays_info

    def get_screen_size(self, display_id=1):
        screens = NSScreen.screens()
        for screen in screens:
            if str(screen.deviceDescription().objectForKey_("NSScreenNumber")) == str(display_id):
                size = screen.frame().size
                return {"width": int(size.width), "height": int(size.height)}
        return {"width": int(screens[0].frame().size.width), "height": int(screens[0].frame().size.height)}


class MacOSSystemInformation(SystemInformation):
    def get_cpu_processes(self):
        cmd = "ps -eo pid,pcpu,comm -c -r | head -n 20"
        out = run(cmd, shell=True, capture_output=True, text=True).stdout.strip()
        lines = out.split('\n')[1:]
        return [{"pid": int(p[0]), "cpu": float(p[1]), "name": p[2]} for line in lines if (p := line.split(None, 2)) and len(p) == 3]

    def get_memory_processes(self):
        cmd = "ps -eo pid,rss,pmem,comm -c -m | head -n 20"
        out = run(cmd, shell=True, capture_output=True, text=True).stdout.strip()
        lines = out.split('\n')[1:]
        return [{"pid": int(p[0]), "mb": round(int(p[1])/1024,1), "percent": float(p[2]), "name": p[3]} for line in lines if (p := line.split(None, 3)) and len(p) == 4]

    def get_disk_processes(self):
        df = run("df -h / | tail -1", shell=True, capture_output=True, text=True).stdout.strip().split()
        disk_info = {"total": df[1], "used": df[2], "free": df[3], "percent": df[4]}
        du = run("du -sh /Applications/* ~/* 2>/dev/null | sort -rh | head -n 10", shell=True, capture_output=True, text=True).stdout.strip().split('\n')
        items = [{"name": p[1].split('/')[-1], "size": p[0], "type": "App" if p[1].startswith("/Applications") else "File"} for line in du if (p := line.split('\t')) and len(p) == 2]
        return {"disk": disk_info, "heavy_items": items}

    def get_battery_status(self):
        out = run(['pmset', '-g', 'batt'], capture_output=True, text=True).stdout
        pct = re.search(r'(\d+)%', out)
        is_ac = "AC Power" in out
        return {"percentage": int(pct.group(1)) if pct else None, "charging": is_ac}

    def get_uptime(self):
        boot = psutil.boot_time()
        return {"seconds": int(time.time() - boot), "boot_time": datetime.fromtimestamp(boot).isoformat()}

    def get_current_time(self):
        return {"time": datetime.now().strftime("%H:%M:%S")}

    def get_current_date(self):
        return {"date": datetime.now().strftime("%A, %B %d, %Y")}

    def get_cpu_info(self):
        brand = run(["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True, text=True).stdout.strip()
        return {
            "architecture": platform.machine(),
            "model": brand,
            "logical_cores": psutil.cpu_count(logical=True),
            "physical_cores": psutil.cpu_count(logical=False)
        }

    def get_disk_info(self):
        disks = []
        for part in psutil.disk_partitions():
            if 'cdrom' in part.opts or part.fstype == '': continue
            usage = psutil.disk_usage(part.mountpoint)
            disks.append({"device": part.device, "mount": part.mountpoint, "total": usage.total, "free": usage.free, "percent": usage.percent})
        return {"disks": disks}

    def get_os_info(self):
        v = run(["sw_vers"], capture_output=True, text=True).stdout
        return {
            "system": platform.system(),
            "version": re.search(r'ProductVersion:\s+([\d.]+)', v).group(1),
            "build": re.search(r'BuildVersion:\s+(\w+)', v).group(1),
            "architecture": platform.machine()
        }

    def get_user_info(self):
        user = getpass.getuser()
        pw = pwd.getpwnam(user)
        return {"username": user, "home": pw.pw_dir, "uid": pw.pw_uid}

    def system_info(self):
        return {
            "os": self.get_os_info(), "cpu": self.get_cpu_info(),
            "disk": self.get_disk_info(), "user": self.get_user_info(),
            "battery": self.get_battery_status(), "uptime": self.get_uptime()
        }


class MacOSSystemMouse(SystemMouse):
    def _post_event(self, event_type, x, y, button=kCGMouseButtonLeft):
        event = CGEventCreateMouseEvent(None, event_type, (x, y), button)
        CGEventPost(kCGHIDEventTap, event)

    def get_cursor_position(self):
        loc = NSEvent.mouseLocation()
        h = NSScreen.mainScreen().frame().size.height
        return {"x": int(loc.x), "y": int(h - loc.y)}

    def move_mouse(self, x, y):
        self._post_event(kCGEventMouseMoved, x, y)

    def click(self, button="left"):
        pos = self.get_cursor_position()
        btns = {
            "left": (kCGEventLeftMouseDown, kCGEventLeftMouseUp, kCGMouseButtonLeft),
            "right": (kCGEventRightMouseDown, kCGEventRightMouseUp, kCGMouseButtonRight),
            "middle": (kCGEventOtherMouseDown, kCGEventOtherMouseUp, kCGMouseButtonCenter)
        }
        down, up, b = btns.get(button, btns["left"])
        self._post_event(down, pos["x"], pos["y"], b)
        self._post_event(up, pos["x"], pos["y"], b)

    def double_click(self, button="left"):
        self.click(button)
        time.sleep(0.1)
        self.click(button)

    def drag_mouse(self, x1, y1, x2, y2):
        self.move_mouse(x1, y1)
        time.sleep(0.01)
        self._post_event(kCGEventLeftMouseDown, x1, y1, kCGMouseButtonLeft)
        time.sleep(0.01)

        self._post_event(kCGEventLeftMouseDragged, x2, y2, kCGMouseButtonLeft)
        time.sleep(0.01)
        self._post_event(kCGEventLeftMouseUp, x2, y2, kCGMouseButtonLeft)

    def scroll_mouse(self, clicks):
        event = CGEventCreateScrollWheelEvent(None, kCGScrollEventUnitLine, 1, clicks)
        CGEventPost(kCGHIDEventTap, event)


class MacOSSystemNetwork(SystemNetwork):
    def get_network_status(self):
        try:
            res = run(['scutil', '--nwi'], capture_output=True, text=True).stdout
            if "IPv4 network interface information" not in res:
                return {"connected": False, "connection_type": None, "interface": None}

            lines = res.split("IPv4 network interface information")[1].splitlines()
            iface = lines[1].split(":")[0].strip() if len(lines) > 1 else None

            if not iface:
                return {"connected": False, "connection_type": None, "interface": None}

            hw = run(['networksetup', '-listallhardwareports'], capture_output=True, text=True).stdout
            if "utun" in iface:
                ctype = "vpn"
            elif "Wi-Fi" in hw and iface in hw:
                ctype = "wifi"
            elif "Ethernet" in hw and iface in hw:
                ctype = "ethernet"
            else:
                ctype = "unknown"

            return {"connected": True, "connection_type": ctype, "interface": iface}
        except Exception:
            return {"connected": False, "connection_type": None, "interface": None}

    def get_ip_address(self, target_iface=None):
        addrs = psutil.net_if_addrs()

        def parse_addr(addr_list):
            return [
                {"address": a.address, "version": 4 if a.family == socket.AF_INET else 6}
                for a in addr_list if a.family in (socket.AF_INET, socket.AF_INET6)
            ]

        if target_iface:
            if target_iface in addrs:
                return {"interface": target_iface, "addresses": parse_addr(addrs[target_iface])}
            return {"interface": target_iface, "addresses": []}

        all_res = []
        for name, addr_list in addrs.items():
            parsed = parse_addr(addr_list)
            if parsed:
                all_res.append({"interface": name, "addresses": parsed})
        return {"all_interfaces": all_res}

    def get_hostname(self):
        return {
            "hostname": socket.gethostname(),
            "fqdn": socket.getfqdn()
        }

    def get_network_interfaces(self):
        hw_map = {}
        hw_out = run(['networksetup', '-listallhardwareports'], capture_output=True, text=True).stdout
        chunks = hw_out.split("Hardware Port: ")
        for chunk in chunks[1:]:
            lines = chunk.splitlines()
            if lines:
                port_name = lines[0].strip().lower()
                device_line = [l for l in lines if "Device: " in l]
                if device_line:
                    device_name = device_line[0].split(": ")[1].strip()
                    hw_map[device_name] = port_name

        stats = psutil.net_if_stats()
        addrs = psutil.net_if_addrs()
        result = []

        for name, addr_list in addrs.items():
            itype = hw_map.get(name, "unknown")
            if name.startswith("lo"):
                itype = "loopback"
            elif name.startswith("utun"):
                itype = "vpn"

            iface_data = {
                "name": name,
                "type": itype,
                "status": "up" if name in stats and stats[name].isup else "down",
                "mac_address": None,
                "ipv4": [],
                "ipv6": []
            }

            for a in addr_list:
                if a.family == socket.AF_INET:
                    iface_data["ipv4"].append(a.address)
                elif a.family == socket.AF_INET6:
                    iface_data["ipv6"].append(a.address)
                elif a.family == getattr(socket, 'AF_LINK', -1):
                    iface_data["mac_address"] = a.address

            result.append(iface_data)
        return result

    def get_public_ip_address(self):
        try:
            with urlopen("https://api.ipify.org", timeout=5) as r:
                return {"public_ip": r.read().decode().strip()}
        except:
            return {"public_ip": None}

    def get_default_gateway(self):
        out = run(["route", "-n", "get", "default"], capture_output=True, text=True).stdout
        match = re.search(r'gateway:\s+([\d.]+)', out)
        return {"gateway": match.group(1) if match else None}

    def get_dns(self):
        out = run(["scutil", "--dns"], capture_output=True, text=True).stdout
        servers = list(set(re.findall(r'nameserver\[\d+\]\s+:\s+([\d.]+)', out)))
        return {"servers": servers}

    def ping_host(self, host):
        res = run(["ping", "-c", "1", "-W", "1000", host], capture_output=True, text=True)
        latency = re.search(r'time=([\d.]+)\s+ms', res.stdout)
        return {"host": host, "reachable": res.returncode == 0, "latency": float(latency.group(1)) if latency else None}

    def check_internet_connection(self):
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=2).close()
            return True
        except:
            return False


class MacOSSystemNotification(SystemNotification):
    def send_notification(self, title, message, subtitle=None):
        notification = NSUserNotification.alloc().init()
        notification.setTitle_(title)
        notification.setInformativeText_(message)
        if subtitle:
            notification.setSubtitle_(subtitle)

        center = NSUserNotificationCenter.defaultUserNotificationCenter()
        center.deliverNotification_(notification)

    def clear_agent_notification(self):
        raise NotImplementedError("Clearing individual DeskAgent notifications "
                                  "is not supported by the current macOS notification backend")


class MacOSSystemPower(SystemPower):
    def lock_screen(self):
        login_framework = ctypes.CDLL(
            "/System/Library/PrivateFrameworks/login.framework/Versions/A/login"
        )

        login_framework.SACLockScreenImmediate()
        return True

    def sleep_computer(self):
        run(["osascript", "-e", 'tell application "System Events" to sleep'], check=True)

    def restart_computer(self):
        run(["osascript", "-e", 'tell application "System Events" to restart'], check=True)

    def shutdown_computer(self):
        run(["osascript", "-e", 'tell application "System Events" to shut down'], check=True)

    def logout_computer(self):
        run(["osascript", "-e", 'tell application "System Events" to log out'], check=True)

    def cancel_shutdown_computer(self):
        script = 'do shell script "killall shutdown" with administrator privileges'
        try:
            run(["osascript", "-e", script], check=True)
            return True
        except Exception as e:
            print(f"Failed to cancel shutdown: {e}")
            return False
