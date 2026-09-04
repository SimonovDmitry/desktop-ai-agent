import os
import plistlib
import subprocess
import time
import psutil
import tempfile
from UniformTypeIdentifiers import UTType
from AppKit import (NSWorkspace, NSURL, NSApplicationActivateIgnoringOtherApps, NSRunningApplication)
from ApplicationServices import AXIsProcessTrusted
from deskagent.platform.base.application import (ApplicationDocuments, ApplicationFocus, ApplicationInformation,
                                                 ApplicationInstances, ApplicationLifecycle, ApplicationPreferences,
                                                 ApplicationProcesses, ApplicationResources, ApplicationStartup)


class MacOSApplicationLifecycle(ApplicationLifecycle):
    def _get_pid_by_name(self, app_name):
        for proc in psutil.process_iter(['pid', 'name']):
            if app_name.lower() in proc.info['name'].lower():
                return proc.info['pid']
        return None

    def launch(self, app_name, arguments=None):
        cmd = ["open", "-a", app_name]
        if arguments:
            cmd.append("--args")
            cmd.extend(arguments)

        subprocess.run(cmd, check=True)

        time.sleep(0.5)
        pid = self._get_pid_by_name(app_name)
        return {"application": app_name, "pid": pid, "launched": True}

    def launch_hidden(self, app_name):
        subprocess.run(["open", "-g", "-a", app_name], check=True)
        time.sleep(0.5)
        pid = self._get_pid_by_name(app_name)
        return {"application": app_name, "pid": pid, "launched": True, "hidden": True}

    def quit(self, app_name):
        script = f'quit app "{app_name}"'
        subprocess.run(["osascript", "-e", script], check=True)
        return {"application": app_name, "quit": True}

    def force_quit(self, identifier):
        if isinstance(identifier, int) or identifier.isdigit():
            subprocess.run(["kill", "-9", str(identifier)], check=True)
        else:
            subprocess.run(["killall", identifier], check=True)
        return {"application": identifier, "terminated": True}

    def restart(self, app_name):
        self.quit(app_name)
        self.wait_for_exit(app_name, timeout=10)
        return self.launch(app_name)

    def wait_for_start(self, app_name, timeout=30):
        start_time = time.time()
        while time.time() - start_time < timeout:
            pid = self._get_pid_by_name(app_name)
            if pid:
                return {
                    "application": app_name,
                    "started": True,
                    "pid": pid,
                    "waited": round(time.time() - start_time, 2)
                }
            time.sleep(0.5)
        raise TimeoutError(f"Application {app_name} failed to start within {timeout}s")

    def wait_for_exit(self, app_name, timeout=30):
        start_time = time.time()
        while time.time() - start_time < timeout:
            if not self._get_pid_by_name(app_name):
                return {
                    "application": app_name,
                    "exited": True,
                    "waited": round(time.time() - start_time, 2)
                }
            time.sleep(0.5)
        raise TimeoutError(f"Application {app_name} failed to exit within {timeout}s")

    def launch_or_activate(self, app_name):
        workspace = NSWorkspace.sharedWorkspace()
        running_apps = workspace.runningApplications()

        target_app = next((app for app in running_apps if app.localizedName().lower() == app_name.lower()), None)

        if target_app:
            target_app.activateWithOptions_(NSApplicationActivateIgnoringOtherApps)
            return {
                "application": app_name,
                "action": "activated",
                "pid": target_app.processIdentifier()
            }
        else:
            result = self.launch(app_name)
            return {
                "application": app_name,
                "action": "launched",
                "pid": result["pid"]
            }


class MacOSApplicationInformation(ApplicationInformation):
    def _get_running_app_by_name(self, app_name):
        workspace = NSWorkspace.sharedWorkspace()
        for app in workspace.runningApplications():
            if app.localizedName().lower() == app_name.lower():
                return app
        return None

    def _get_bundle_info(self, app_path):
        plist_path = os.path.join(app_path, "Contents/Info.plist")
        if os.path.exists(plist_path):
            with open(plist_path, 'rb') as f:
                return plistlib.load(f)
        return {}

    def get_running(self):
        workspace = NSWorkspace.sharedWorkspace()
        apps = []
        for app in workspace.runningApplications():
            if app.activationPolicy() == 0:
                apps.append({
                    "name": app.localizedName(),
                    "pid": app.processIdentifier(),
                    "bundle_id": app.bundleIdentifier()
                })
        return apps

    def get_installed(self):
        try:
            cmd = ["mdfind", "kMDItemContentType == 'com.apple.application-bundle'"]
            out = subprocess.check_output(cmd, text=True).splitlines()
            apps = [{"name": os.path.basename(p).replace(".app", ""), "path": p} for p in out]
            return apps
        except Exception:
            return []

    def find(self, query, limit=10):
        all_apps = self.get_installed()
        results = [a for a in all_apps if query.lower() in a['name'].lower()]
        return results[:limit]

    def get_info(self, app_name):
        path = self.get_path(app_name)
        if not path:
            raise ValueError(f"Application {app_name} not found")

        plist = self._get_bundle_info(path)
        running_app = self._get_running_app_by_name(app_name)

        return {
            "name": app_name,
            "pid": running_app.processIdentifier() if running_app else None,
            "path": path,
            "bundle_id": plist.get("CFBundleIdentifier"),
            "version": plist.get("CFBundleShortVersionString"),
            "architecture": self.get_architecture(app_name)
        }

    def get_status(self, app_name):
        app = self._get_running_app_by_name(app_name)
        if not app:
            return {"running": False, "visible": False, "active": False, "pid": None}

        workspace = NSWorkspace.sharedWorkspace()
        active_app = workspace.frontmostApplication()

        return {
            "running": True,
            "visible": not app.isHidden(),
            "active": active_app and active_app.processIdentifier() == app.processIdentifier(),
            "pid": app.processIdentifier()
        }

    def is_running(self, app_name):
        return self._get_running_app_by_name(app_name) is not None

    def get_active(self):
        app = NSWorkspace.sharedWorkspace().frontmostApplication()
        if app:
            return {
                "name": app.localizedName(),
                "pid": app.processIdentifier(),
                "bundle_id": app.bundleIdentifier()
            }
        return None

    def get_pid(self, app_name):
        app = self._get_running_app_by_name(app_name)
        return app.processIdentifier() if app else None

    def get_path(self, app_name):
        try:
            cmd = ["mdfind", f"kMDItemFSName == '{app_name}.app'"]
            out = subprocess.check_output(cmd, text=True).strip().splitlines()
            return out[0] if out else None
        except Exception:
            return None

    def get_executable_path(self, app_name):
        path = self.get_path(app_name)
        if path:
            plist = self._get_bundle_info(path)
            exec_name = plist.get("CFBundleExecutable")
            if exec_name:
                return os.path.join(path, "Contents/MacOS", exec_name)
        return None

    def get_bundle_id(self, app_name):
        path = self.get_path(app_name)
        return self._get_bundle_info(path).get("CFBundleIdentifier") if path else None

    def get_version(self, app_name):
        path = self.get_path(app_name)
        return self._get_bundle_info(path).get("CFBundleShortVersionString") if path else None

    def get_architecture(self, app_name):
        app = self._get_running_app_by_name(app_name)
        if app:
            arch_code = app.executableArchitecture()
            return "arm64" if arch_code == 0x0100000c else "x86_64"

        exec_path = self.get_executable_path(app_name)
        if exec_path:
            out = subprocess.check_output(["lipo", "-archs", exec_path], text=True)
            return out.strip()
        return "unknown"

    def get_name_from_id(self, identifier_type, identifier):
        workspace = NSWorkspace.sharedWorkspace()

        if identifier_type == "pid":
            for app in workspace.runningApplications():
                if app.processIdentifier() == int(identifier):
                    return app.localizedName()

        elif identifier_type == "path":
            return os.path.basename(identifier).replace(".app", "")

        elif identifier_type == "bundle_id":
            try:
                cmd = ["mdfind", f"kMDItemCFBundleIdentifier == '{identifier}'"]
                path = subprocess.check_output(cmd, text=True).strip().splitlines()
                if path:
                    return os.path.basename(path[0]).replace(".app", "")
            except Exception:
                pass

        return "Unknown"


class MacOSApplicationPreferences(ApplicationPreferences):
    def get_permissions(self, app_name):
        return {
            "accessibility": self.get_accessibility_status(app_name),
            "automation": self.get_automation_status(app_name),
            "notifications": self.get_notification_status(app_name)
        }

    def get_accessibility_status(self, app_name=None):
        return bool(AXIsProcessTrusted())

    def get_automation_status(self, app_name):
        script = f'tell application "{app_name}" to get name'
        try:
            subprocess.run(["osascript", "-e", script], capture_output=True, timeout=1)
            return True
        except Exception:
            return False

    def get_notification_status(self, app_name):
        return True

    def get_default_app(self, file_type):
        workspace = NSWorkspace.sharedWorkspace()
        ext = file_type.lstrip('.')

        try:
            ut_type = UTType.typeWithFilenameExtension_(ext)
            if ut_type:
                app_url = workspace.URLForApplicationToOpenContentType_(ut_type)
                if app_url:
                    return os.path.basename(app_url.path()).replace(".app", "")
        except (ImportError, AttributeError):
            pass

        test_path = os.path.join(tempfile.gettempdir(), f"agent_check.{ext}")
        try:
            with open(test_path, 'w') as f:
                pass

            temp_url = NSURL.fileURLWithPath_(test_path)
            app_url = workspace.URLForApplicationToOpenURL_(temp_url)

            if app_url:
                app_name = os.path.basename(app_url.path()).replace(".app", "")
                return app_name
        except Exception as e:
            print(f"Error searching for the application: {e}")
        finally:
            if os.path.exists(test_path):
                os.remove(test_path)

        return "Unknown"

    def open_with(self, path, app_name):
        if not os.path.exists(path):
            raise FileNotFoundError(f"File not found: {path}")

        subprocess.run(["open", "-a", app_name, path], check=True)
        return True

    def open_app_prefs(self, app_name):
        script = f'''
        tell application "{app_name}" to activate
        tell application "System Events" to keystroke "," using command down
        '''
        subprocess.run(["osascript", "-e", script], check=True)
        return True

    def open_system_settings(self, app_name, section):
        sections = {
            "accessibility": "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility",
            "automation": "x-apple.systempreferences:com.apple.preference.security?Privacy_Automation",
            "notifications": "x-apple.systempreferences:com.apple.Notifications-Settings.extension",
            "general": "x-apple.systempreferences:com.apple.PreferenceSync.General"
        }

        url = sections.get(section.lower(), sections["general"])
        subprocess.run(["open", url], check=True)
        return True


class MacOSApplicationFocus(ApplicationFocus):
    def _get_app_by_name(self, app_name):
        workspace = NSWorkspace.sharedWorkspace()
        for app in workspace.runningApplications():
            if app.localizedName().lower() == app_name.lower():
                return app
        return None

    def activate(self, app_name):
        app = self._get_app_by_name(app_name)
        if app:
            app.activateWithOptions_(NSApplicationActivateIgnoringOtherApps)
            return {"application": app_name, "active": True}
        raise ValueError(f"Application {app_name} not found or not running")

    def hide(self, app_name):
        app = self._get_app_by_name(app_name)
        if app:
            app.hide()
            return {"application": app_name, "hidden": True}
        return {"application": app_name, "hidden": False}

    def show(self, app_name):
        app = self._get_app_by_name(app_name)
        if app:
            app.unhide()
            return {"application": app_name, "visible": True}
        return {"application": app_name, "visible": False}

    def minimize(self, app_name):
        script = f'''
        tell application "System Events"
            tell process "{app_name}"
                set value of attribute "AXMinimized" of every window to true
            end tell
        end tell
        '''
        try:
            subprocess.run(["osascript", "-e", script], check=True)
            return {"application": app_name, "minimized": True}
        except Exception:
            script_alt = f'tell application "{app_name}" to set miniaturized of every window to true'
            subprocess.run(["osascript", "-e", script_alt], check=True)
            return {"application": app_name, "minimized": True}

    def restore(self, app_name):
        script = f'''
        tell application "System Events"
            if exists process "{app_name}" then
                tell process "{app_name}"
                    set value of attribute "AXMinimized" of every window to false
                end tell
            end if
        end tell
        '''
        try:
            subprocess.run(["osascript", "-e", script], check=True)
            self.activate(app_name)
            return {"application": app_name, "restored": True}
        except Exception as e:
            self.activate(app_name)
            return {"application": app_name, "restored": "partial (activated only)"}

    def bring_to_front(self, app_name):
        return self.activate(app_name)

    def get_visibility(self, app_name):
        app = self._get_app_by_name(app_name)
        if app:
            is_hidden = app.isHidden()
            return {"visible": not is_hidden, "hidden": is_hidden}
        return {"visible": False, "hidden": True}

    def is_focused(self, app_name):
        workspace = NSWorkspace.sharedWorkspace()
        active_app = workspace.frontmostApplication()
        if active_app and active_app.localizedName().lower() == app_name.lower():
            return {"focused": True}
        return {"focused": False}


class MacOSApplicationResources(ApplicationResources):
    def _get_all_matching_processes(self, app_name):
        processes = []
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if app_name.lower() in proc.info['name'].lower():
                    processes.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return processes

    def get_cpu_usage(self, app_name):
        procs = self._get_all_matching_processes(app_name)
        total_cpu = 0.0
        for p in procs:
            try:
                total_cpu += p.cpu_percent(interval=0.1)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return round(total_cpu, 1)

    def get_memory_usage(self, app_name):
        procs = self._get_all_matching_processes(app_name)
        total_bytes = 0
        for p in procs:
            try:
                total_bytes += p.memory_info().rss
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return {
            "bytes": total_bytes,
            "mb": round(total_bytes / (1024 * 1024), 2)
        }

    def get_disk_usage(self, app_name):
        procs = self._get_all_matching_processes(app_name)
        read_bytes = 0
        write_bytes = 0
        for p in procs:
            try:
                io = p.io_counters()
                read_bytes += io.read_bytes
                write_bytes += io.write_bytes
            except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError):
                continue

        return {
            "read_bytes": read_bytes,
            "write_bytes": write_bytes
        }

    def get_resource_usage(self, app_name):
        cpu = self.get_cpu_usage(app_name)
        mem = self.get_memory_usage(app_name)
        disk = self.get_disk_usage(app_name)

        return {
            "cpu_percent": cpu,
            "memory_bytes": mem["bytes"],
            "memory_mb": mem["mb"],
            "read_bytes": disk["read_bytes"],
            "write_bytes": disk["write_bytes"]
        }

    def get_top_resource_apps(self, resource_type, limit=10):
        app_stats = {}
        for proc in psutil.process_iter(['cpu_percent']):
            try:
                proc.cpu_percent()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        time.sleep(0.1)
        for proc in psutil.process_iter(['name', 'cpu_percent', 'memory_info']):
            try:
                info = proc.info
                name = info['name']
                cpu = info.get('cpu_percent') or 0.0
                mem_info = info.get('memory_info')
                rss = mem_info.rss if mem_info else 0

                if name not in app_stats:
                    app_stats[name] = {"cpu": 0.0, "memory": 0}

                app_stats[name]["cpu"] += cpu
                app_stats[name]["memory"] += rss
            except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError):
                continue

        if resource_type.lower() == "cpu":
            sorted_apps = sorted(app_stats.items(), key=lambda x: x[1]["cpu"], reverse=True)
            result = [{"name": n, "cpu_percent": round(s["cpu"], 1)} for n, s in sorted_apps[:limit]]
        else:
            sorted_apps = sorted(app_stats.items(), key=lambda x: x[1]["memory"], reverse=True)
            result = [{"name": n, "memory_mb": round(s["memory"] / (1024 * 1024), 1)} for n, s in sorted_apps[:limit]]

        return result


class MacOSApplicationProcesses(ApplicationProcesses):

    def _find_all(self, app_name):

        found = []
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if app_name.lower() in proc.info['name'].lower():
                    found.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return found

    def get_processes(self, app_name):
        procs = self._find_all(app_name)
        result = []
        for p in procs:
            try:
                result.append({
                    "pid": p.pid,
                    "name": p.name(),
                    "cpu_percent": p.cpu_percent(interval=0.1)
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return result

    def get_main(self, app_name):
        procs = self._find_all(app_name)
        if not procs:
            return None

        procs.sort(key=lambda x: x.create_time())
        main = procs[0]
        return {"pid": main.pid, "name": main.name()}

    def get_children(self, app_name):
        main_info = self.get_main(app_name)
        if not main_info:
            return []

        try:
            main_proc = psutil.Process(main_info["pid"])
            children = main_proc.children(recursive=True)
            return [{"pid": c.pid, "name": c.name()} for c in children]
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return []

    def get_tree(self, app_name):
        main_info = self.get_main(app_name)
        if not main_info:
            return {}

        def build_node(proc):
            try:
                return {
                    "pid": proc.pid,
                    "name": proc.name(),
                    "children": [build_node(c) for c in proc.children()]
                }
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                return {"pid": proc.pid, "status": "access_denied"}

        try:
            root_proc = psutil.Process(main_info["pid"])
            return {"root": build_node(root_proc)}
        except Exception:
            return {}

    def suspend(self, app_name):
        procs = self._find_all(app_name)
        for p in procs:
            try:
                p.suspend()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return {"application": app_name, "suspended": True}

    def resume(self, app_name):
        procs = self._find_all(app_name)
        for p in procs:
            try:
                p.resume()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return {"application": app_name, "resumed": True}


class MacOSApplicationInstances(ApplicationInstances):

    def _get_apps_by_name(self, app_name):
        workspace = NSWorkspace.sharedWorkspace()
        return [app for app in workspace.runningApplications()
                if app.localizedName().lower() == app_name.lower()]

    def get_all(self, app_name):
        apps = self._get_apps_by_name(app_name)
        return [
            {
                "pid": app.processIdentifier(),
                "name": app.localizedName()
            } for app in apps
        ]

    def get_count(self, app_name):
        apps = self._get_apps_by_name(app_name)
        return len(apps)

    def activate(self, pid):
        workspace = NSWorkspace.sharedWorkspace()
        for app in workspace.runningApplications():
            if app.processIdentifier() == int(pid):
                app.activateWithOptions_(NSApplicationActivateIgnoringOtherApps)
                return {"pid": pid, "active": True}

        raise ValueError(f"Instance with PID {pid} not found")

    def quit(self, pid):
        workspace = NSWorkspace.sharedWorkspace()
        for app in workspace.runningApplications():
            if app.processIdentifier() == int(pid):
                app.terminate()
                return {"pid": pid, "quit": True}

        raise ValueError(f"Instance with PID {pid} not found")


class MacOSApplicationStartup(ApplicationStartup):
    def _get_app_path(self, app_name):
        try:
            cmd = ["mdfind", f"kMDItemFSName == '{app_name}.app'"]
            output = subprocess.check_output(cmd, text=True).strip().splitlines()
            return output[0] if output else None
        except Exception:
            return None

    def get_all(self):
        script = 'tell application "System Events" to get name of every login item'
        try:
            result = subprocess.check_output(["osascript", "-e", script], text=True).strip()
            if not result:
                return []
            return [item.strip() for item in result.split(",")]
        except Exception:
            return []

    def is_enabled(self, app_name):
        items = self.get_all()
        return any(item.lower() == app_name.lower() for item in items)

    def add(self, app_name):
        path = self._get_app_path(app_name)
        if not path:
            raise FileNotFoundError(f"Could not find the path to the application {app_name}")

        script = f'tell application "System Events" to make login item at end with properties {{path:"{path}", hidden:false}}'
        subprocess.run(["osascript", "-e", script], check=True)
        return {"application": app_name, "added": True}

    def remove(self, app_name):
        script = f'tell application "System Events" to delete login item "{app_name}"'
        try:
            subprocess.run(["osascript", "-e", script], check=True)
            return {"application": app_name, "removed": True}
        except subprocess.CalledProcessError:
            return {"application": app_name, "removed": False, "reason": "Not found"}

    def enable(self, app_name):
        if not self.is_enabled(app_name):
            return self.add(app_name)
        return {"application": app_name, "enabled": True}

    def disable(self, app_name):
        if self.is_enabled(app_name):
            return self.remove(app_name)
        return {"application": app_name, "enabled": False}


class MacOSApplicationDocuments(ApplicationDocuments):
    def _get_app_path(self, app_name):
        try:
            cmd = ["mdfind", f"kMDItemFSName == '{app_name}.app'"]
            out = subprocess.check_output(cmd, text=True).strip().splitlines()
            return out[0] if out else None
        except Exception:
            return None

    def open(self, path):
        if not os.path.exists(path):
            raise FileNotFoundError(f"File not found: {path}")

        subprocess.run(["open", path], check=True)
        return {"opened": True, "path": path}

    def open_multiple(self, paths):
        opened_files = []
        for path in paths:
            if os.path.exists(path):
                subprocess.run(["open", path], check=True)
                opened_files.append(path)

        return {
            "opened": opened_files,
            "count": len(opened_files)
        }

    def open_url_with(self, url, app_name):
        subprocess.run(["open", "-a", app_name, url], check=True)
        return {
            "opened": True,
            "url": url,
            "application": app_name
        }

    def reveal_app(self, app_name):
        path = self._get_app_path(app_name)
        if not path:
            raise ValueError(f"The {app_name} application was not found")

        subprocess.run(["open", "-R", path], check=True)
        return {"revealed": True, "path": path}

    def reveal_executable(self, app_name):
        app_path = self._get_app_path(app_name)
        if not app_path:
            raise ValueError(f"The {app_name} application was not found.")

        plist_path = os.path.join(app_path, "Contents/Info.plist")
        try:
            with open(plist_path, 'rb') as f:
                plist = plistlib.load(f)
                exec_name = plist.get("CFBundleExecutable")
                if exec_name:
                    exec_path = os.path.join(app_path, "Contents/MacOS", exec_name)
                    subprocess.run(["open", "-R", exec_path], check=True)
                    return {"revealed": True, "path": exec_path}
        except Exception as e:
            raise RuntimeError(f"Could not find the executable file: {e}")

        raise FileNotFoundError("The executable file is not defined in Info.plist")
