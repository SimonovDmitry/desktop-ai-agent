from deskagent.actions.base import Action


class GetCPUUsage(Action):
    def __init__(self, logger=None):
        Action.__init__(self, logger)

    def execute(self, config):
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


class GetMemoryUsage(Action):
    def __init__(self, logger=None):
        Action.__init__(self, logger)

    def execute(self, config):
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
                pid = parts[0]
                rss_kb = parts[1]
                pmem = parts[2]
                name = parts[3]

                rss_mb = round(int(rss_kb) / 1024, 1)

                parsed_memory_list.append({
                    "pid": int(pid),
                    "memory_mb": rss_mb,
                    "memory_percent": float(pmem),
                    "name": name
                })
        return parsed_memory_list


class GetDiskUsage(Action):
    def __init__(self, logger=None):
        Action.__init__(self, logger)

    def execute(self, config):
        cmd_space = "df -h / | tail -1"
        res_space = run(cmd_space, shell=True, capture_output=True, text=True).stdout.strip().split()
        disk_info = {"total": res_space[1], "used": res_space[2],
                     "free": res_space[3], "percent": res_space[4]}

        cmd_heavy = "du -sh /Applications/* ~/* 2>/dev/null | sort -rh | head -n 10"

        result_heavy = run(cmd_heavy, shell=True, capture_output=True, text=True)
        lines = result_heavy.stdout.strip().split('\n')

        items = []
        for line in lines:
            parts = line.split('\t')
            if len(parts) == 2:
                size = parts[0].strip()
                path = parts[1].strip()
                item_type = "App" if path.startswith("/Applications") else "User File/Folder"
                name = path.split('/')[-1]

                items.append({
                    "name": name,
                    "size": size,
                    "type": item_type,
                    "full_path": path
                })

        return {"disk": disk_info, "heavy_items": items}


class GetBatteryStatus(Action):
    def __init__(self, logger=None):
        Action.__init__(self, logger)

    def execute(self, config):
        result = run(['pmset', '-g', 'batt'], capture_output=True, text=True)
        output = result.stdout


        percent_match = re.search(r'(\d+)%', output)
        charging_match = re.search(r'(AC|Battery) Power', output)

        percentage = int(percent_match.group(1)) if percent_match else None

        is_plugged = True if charging_match and charging_match.group(1) == 'AC' else False
        print(percentage, is_plugged)
        return {"percentage": percentage, "charging": is_plugged}


class GetUptime(Action):
    def __init__(self, logger=None):
        Action.__init__(self, logger)

    def execute(self, config=None):
        boot_time = psutil.boot_time()
        uptime_seconds = time.time() - boot_time
        boot_datetime = datetime.fromtimestamp(boot_time).isoformat()

        return {
            "seconds": int(uptime_seconds),
            "boot_time": boot_datetime
        }


class GetCurrentTime(Action):
    def __init__(self, logger=None):
        Action.__init__(self, logger)

    def execute(self, config):
        result = run(['date', '+%T'], capture_output=True, text=True)
        output = result.stdout.strip()
        return {"time": output}


class GetCurrentDate(Action):
    def __init__(self, logger=None):
        Action.__init__(self, logger)

    def execute(self, config):
        result = run(['date', '+%A %B %C'], capture_output=True, text=True)
        output = result.stdout.strip()
        return {"date": output}

#TODO
class SystemInfo(Action):
    def __init__(self, logger=None):
        Action.__init__(self, logger)

#TODO
class GetCPUInfo(Action):
    def __init__(self, logger=None):
        Action.__init__(self, logger)
    def execute(self, config):


# TODO
class GetDiskInfo(Action):
    def __init__(self, logger=None):
        Action.__init__(self, logger)


# TODO
class GetOSInfo(Action):
    def __init__(self, logger=None):
        Action.__init__(self, logger)

#TODO
class GetUserInfo(Action):
    def __init__(self, logger=None):
        Action.__init__(self, logger)
    def execute(self, config):


