import re
import psutil
import time
import socket
from datetime import datetime
from subprocess import run, check_output
from AppKit import NSEvent, NSScreen, NSPasteboard, NSStringPboardType


from deskagent.platform.base.system import (SystemAudio, SystemClipboard, SystemDisplay, SystemInformation, SystemMouse,
                                            SystemNetwork, SystemNotify, SystemPower)


class MacOSAudio(SystemAudio):

    def set_volume(self, volume):
        if volume is None:
            raise ValueError('Volume level must be set')

        if not isinstance(volume, int):
            raise ValueError('Volume level must be int')

        run(["osascript", "-e", f"set volume output volume {volume}"])

    def increase_volume(self, step=10):
        if step is None:
            raise ValueError('Step must be set')

        if not isinstance(step, int):
            raise ValueError('Step must be int')

        cmd = ['osascript', '-e', 'output volume of (get volume settings)']
        volume_level = check_output(cmd).decode('utf-8').strip()
        volume_new = int(volume_level) + step
        run(["osascript", "-e", f"set volume output volume {volume_new}"])

    def mute(self):
        run(["osascript", "-e", "set volume output muted true"])

    def decrease_volume(self):
        cmd = ['osascript', '-e', 'output volume of (get volume settings)']
        volume_level = check_output(cmd).decode('utf-8').strip()
        volume_new = int(volume_level) - 10
        run(["osascript", "-e", f"set volume output volume {volume_new}"])

    def unmute(self):
        run(["osascript", "-e", "set volume output muted false"])

    def get_volume(self):
        cmd = ['osascript', '-e', 'output volume of (get volume settings)']
        volume_level = check_output(cmd).decode('utf-8').strip()
        return volume_level


class MacOSClipboard(SystemClipboard):
    def get_clipboard(self):
        pb = NSPasteboard.generalPasteboard()
        content = pb.stringForType_(NSStringPboardType)
        return content

    def set_clipboard(self, text):
        pb = NSPasteboard.generalPasteboard()
        pb.clearContents()
        pb.setString_forType_(text, NSStringPboardType)

    #TODO
    def clean_clipboard(self):
        pass


class MacOSDisplay(SystemDisplay):
    def set_display_brightness(self, brightness_level):
        if brightness_level is None:
            raise ValueError('Brightness level must be set')

        brightness_level = max(0, min(100, brightness_level))
        steps = round(brightness_level / 6.25)

        apple_script = f'''
        tell application "System Events"
            repeat 16 times
                key code 145 -- Код клавиши "Яркость вниз"
            end repeat
            repeat {steps} times
                key code 144 -- Код клавиши "Яркость вверх"
            end repeat
        end tell
        '''

        run(['osascript', '-e', apple_script], check=True)

    #TODO
    def get_display_brightness(self):
        pass

    def get_displays(self):
        screens = NSScreen.screens()
        displays_info = []

        for i, screen in enumerate(screens):
            frame = screen.frame()
            description = screen.deviceDescription()

            display_id = description.objectForKey_("NSScreenNumber")
            is_primary = (i == 0)

            if is_primary:
                name = "Built-in Display" if len(screens) == 1 else "Primary Display"
            else:
                name = f"External Display {i}"

            displays_info.append({"id": str(display_id), "name": name, "primary": is_primary,
                                  "width": int(frame.size.width), "height": int(frame.size.height),
                                  "x": int(frame.origin.x), "y": int(frame.origin.y)})
        return displays_info

    def get_screen_size(self, display_id=1):
        screens = NSScreen.screens()
        selected_screen = screens[0]
        if display_id:
            for screen in screens:
                if str(screen.deviceDescription().objectForKey_("NSScreenNumber")) == str(display_id):
                    selected_screen = screen
                    break
        size = selected_screen.frame().size
        return {"width": int(size.width), "height": int(size.height)}

    #TODO
    def set_resolution(self):
        pass


class MacOSInformation(SystemInformation):
    def get_cpu_processes(self):
        cmd = "ps -eo pid,pcpu,comm -c -r | head -n 20"
        result = run(cmd, shell=True, capture_output=True, text=True)
        output = result.stdout.strip()
        if not output:
            return []
        lines = output.split('\n')
        data_lines = lines[1:]
        parsed_processes = []
        for line in data_lines:
            parts = line.split(None, 2)
            if len(parts) == 3:
                parsed_processes.append({"pid": int(parts[0]), "cpu_percent": float(parts[1]), "name": parts[2]})
        return parsed_processes

    def get_memory_processes(self):
        cmd = "ps -eo pid,rss,pmem,comm -c -m | head -n 20"
        result = run(cmd, shell=True, capture_output=True, text=True)
        output = result.stdout.strip()
        if not output:
            return []
        lines = output.split('\n')
        data_lines = lines[1:]
        parsed_memory_list = []
        for line in data_lines:
            parts = line.split(None, 3)
            if len(parts) == 4:
                pid, rss_kb, pmem, name = parts
                rss_mb = round(int(rss_kb) / 1024, 1)
                parsed_memory_list.append({
                    "pid": int(pid), "memory_mb": rss_mb,
                    "memory_percent": float(pmem), "name": name
                })
        return parsed_memory_list

    def get_disk_processes(self):
        cmd_space = "df -h / | tail -1"
        res_space = run(cmd_space, shell=True, capture_output=True, text=True).stdout.strip().split()
        disk_info = {"total": res_space[1], "used": res_space[2], "free": res_space[3], "percent": res_space[4]}
        cmd_heavy = "du -sh /Applications/* ~/* 2>/dev/null | sort -rh | head -n 10"
        result_heavy = run(cmd_heavy, shell=True, capture_output=True, text=True)
        lines = result_heavy.stdout.strip().split('\n')
        items = []
        for line in lines:
            parts = line.split('\t')
            if len(parts) == 2:
                size, path = parts[0].strip(), parts[1].strip()
                item_type = "App" if path.startswith("/Applications") else "User File/Folder"
                items.append({"name": path.split('/')[-1], "size": size, "type": item_type, "full_path": path})
        return {"disk": disk_info, "heavy_items": items}

    def get_battery_status(self):
        result = run(['pmset', '-g', 'batt'], capture_output=True, text=True)
        output = result.stdout
        percent_match = re.search(r'(\d+)%', output)
        charging_match = re.search(r'(AC|Battery) Power', output)
        percentage = int(percent_match.group(1)) if percent_match else None
        is_plugged = True if charging_match and charging_match.group(1) == 'AC' else False
        return {"percentage": percentage, "charging": is_plugged}

    def get_uptime(self):
        boot_time = psutil.boot_time()
        uptime_seconds = time.time() - boot_time
        boot_datetime = datetime.fromtimestamp(boot_time).isoformat()
        return {"seconds": int(uptime_seconds), "boot_time": boot_datetime}

    def get_current_time(self):
        result = run(['date', '+%T'], capture_output=True, text=True)
        return {"time": result.stdout.strip()}

    def get_current_date(self):
        result = run(['date', '+%A %B %C'], capture_output=True, text=True)
        return {"date": result.stdout.strip()}

    # TODO
    def system_info(self):
        pass

    # TODO
    def get_cpu_info(self):
        pass

    # TODO
    def get_disk_info(self):
        pass

    # TODO
    def get_os_info(self):
        pass

    # TODO
    def get_user_info(self):
        pass


class MacOSMouse(SystemMouse):
    def get_cursor_position(self):
        loc = NSEvent.mouseLocation()
        screen_height = NSScreen.mainScreen().frame().size.height
        return {"x": int(loc.x), "y": int(screen_height - loc.y)}

    # TODO
    def move_mouse(self):
        pass

    # TODO
    def click(self):
        pass

    # TODO
    def double_click(self):
        pass

    # TODO
    def drag_mouse(self):
        pass

    # TODO
    def scroll_mouse(self):
        pass


class MacOSNetwork(SystemNetwork):
    def get_network_status(self):
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

    def get_ip_address(self, target_iface):
        addrs = psutil.net_if_addrs()
        if target_iface:
            if target_iface not in addrs: return {"interface": target_iface, "addresses": []}
            res = [{"address": a.address, "version": 4 if a.family == socket.AF_INET else 6}
                   for a in addrs[target_iface] if a.family in (socket.AF_INET, socket.AF_INET6)]
            return {"interface": target_iface, "addresses": res}
        all_res = []
        for iface, addr_list in addrs.items():
            for a in addr_list:
                if a.family in (socket.AF_INET, socket.AF_INET6):
                    all_res.append(
                        {"interface": iface, "address": a.address, "version": 4 if a.family == socket.AF_INET else 6})
        return {"addresses": all_res}

    def get_hostname(self):
        return {"hostname": socket.gethostname(), "fqdn": socket.getfqdn()}

    def get_network_interfaces(self):
        hw_map = {}
        hw_out = run(['networksetup', '-listallhardwareports'], capture_output=True, text=True).stdout
        chunks = hw_out.split("Hardware Port: ")
        for chunk in chunks[1:]:
            lines = chunk.splitlines()
            if lines:
                hw_map[lines[1].split(": ")[1].strip()] = lines[0].strip().lower()
        stats, addrs, result = psutil.net_if_stats(), psutil.net_if_addrs(), []
        for name, addr_list in addrs.items():
            itype = hw_map.get(name, "loopback" if name.startswith("lo") else (
                "vpn" if name.startswith("utun") else "unknown"))
            iface_data = {"name": name, "type": itype, "status": "up" if name in stats and stats[name].isup else "down",
                          "mac_address": None, "ipv4": [], "ipv6": []}
            for a in addr_list:
                if a.family == socket.AF_INET:
                    iface_data["ipv4"].append(a.address)
                elif a.family == socket.AF_INET6:
                    iface_data["ipv6"].append(a.address)
                elif a.family == getattr(socket, 'AF_LINK', -1):
                    iface_data["mac_address"] = a.address
            result.append(iface_data)
        return result

    # TODO
    def get_public_ip_address(self):
        pass

    # TODO
    def get_default_gateway(self):
        pass

    # TODO
    def get_dns(self):
        pass

    # TODO
    def ping_host(self):
        pass

    # TODO
    def check_internet_connection(self):
        pass


class MacOSNotify(SystemNotify):

    # TODO
    def send_notification(self):
        pass

    # TODO
    def clear_agent_notification(self):
        pass


class MacOSPower(SystemPower):

    def lock_screen(self):
        run(["osascript", "-e", 'tell application "System Events" to keystroke "q" using {control down, command down}'])

    def sleep_computer(self):
        run(["osascript", "-e", 'tell application "System Events" to sleep'])

    def restart_computer(self):
        run(["sudo", "shutdown", "-r", "now"], check=True)

    def shutdown_computer(self):
        run(["sudo", "shutdown", "now"], check=True)

    # TODO
    def logout_computer(self):
        pass

    # TODO
    def cancel_shutdown_computer(self):
        pass
