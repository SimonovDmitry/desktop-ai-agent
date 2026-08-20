from deskagent.actions.base import Action


#TODO проверить работоспособность GetNetworkStatus GetIPAddress GetHostname GetNetworkInterfaces

class GetNetworkStatus(Action):
    def __init__(self, logger=None):
        Action.__init__(self, logger)

    def execute(self, config=None):
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


class GetIPAddress(Action):
    def __init__(self, logger=None):
        Action.__init__(self, logger)

    def execute(self, config=None):
        target_iface = config.get('interface') if config else None
        addrs = psutil.net_if_addrs()

        if target_iface:
            if target_iface not in addrs:
                return {"interface": target_iface, "addresses": []}
            res = []
            for addr in addrs[target_iface]:
                if addr.family in (socket.AF_INET, socket.AF_INET6):
                    res.append({"address": addr.address, "version": 4 if addr.family == socket.AF_INET else 6})
            return {"interface": target_iface, "addresses": res}

        all_res = []
        for iface, addr_list in addrs.items():
            for addr in addr_list:
                if addr.family in (socket.AF_INET, socket.AF_INET6):
                    all_res.append({
                        "interface": iface,
                        "address": addr.address,
                        "version": 4 if addr.family == socket.AF_INET else 6
                    })
        return {"addresses": all_res}


class GetHostname(Action):
    def __init__(self, logger=None):
        Action.__init__(self, logger)

    def execute(self, config=None):
        import socket
        return {
            "hostname": socket.gethostname(),
            "fqdn": socket.getfqdn()
        }


class GetNetworkInterfaces(Action):
    def __init__(self, logger=None):
        Action.__init__(self, logger)

    def execute(self, config=None):
        hw_map = {}
        hw_out = run(['networksetup', '-listallhardwareports'], capture_output=True, text=True).stdout
        chunks = hw_out.split("Hardware Port: ")
        for chunk in chunks[1:]:
            lines = chunk.splitlines()
            if lines:
                port = lines[0].strip().lower()
                dev = [l for l in lines if "Device: " in l]
                if dev:
                    hw_map[dev[0].split(": ")[1].strip()] = port

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

            for addr in addr_list:
                if addr.family == socket.AF_INET:
                    iface_data["ipv4"].append(addr.address)
                elif addr.family == socket.AF_INET6:
                    iface_data["ipv6"].append(addr.address)
                elif addr.family == getattr(socket, 'AF_LINK', -1):
                    iface_data["mac_address"] = addr.address

            result.append(iface_data)
        return result


# TODO
class GetPublicIPAddress(Action):
    def __init__(self, logger=None):
        Action.__init__(self, logger)


#TODO
class GetDefaultGateway(Action):
    def __init__(self, logger=None):
        Action.__init__(self, logger)


#TODO
class GetDNS(Action):
    def __init__(self, logger=None):
        Action.__init__(self, logger)


#TODO
class PingHost(Action):
    def __init__(self, logger=None):
        Action.__init__(self, logger)


#TODO
class CheckInternetConnection(Action):
    def __init__(self, logger=None):
        Action.__init__(self, logger)
