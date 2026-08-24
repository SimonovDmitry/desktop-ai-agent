from dataclasses import dataclass
import platform

from deskagent.platform.base.audio import SystemAudio
from deskagent.platform.base.clipboard import SystemClipboard
from deskagent.platform.base.display import SystemDisplay
from deskagent.platform.base.information import SystemInformation
from deskagent.platform.base.mouse import SystemMouse
from deskagent.platform.base.network import SystemNetwork
from deskagent.platform.base.notification import SystemNotify
from deskagent.platform.base.power import SystemPower

from deskagent.platform.macos.audio import MacOSAudio
from deskagent.platform.macos.clipboard import MacOSClipboard
from deskagent.platform.macos.display import MacOSDisplay
from deskagent.platform.macos.information import MacOSInformation
from deskagent.platform.macos.mouse import MacOSMouse
from deskagent.platform.macos.network import MacOSNetwork
from deskagent.platform.macos.notification import MacOSNotification
from deskagent.platform.macos.power import MacOSPower


@dataclass
class SystemServices:
    audio: SystemAudio
    clipboard: SystemClipboard
    display: SystemDisplay
    information: SystemInformation
    mouse: SystemMouse
    network: SystemNetwork
    notify: SystemNotify
    power: SystemPower


class MacOSSystemServices(SystemServices):

    def __init__(self):
        super().__init__(
            audio=MacOSAudio(),
            clipboard=MacOSClipboard(),
            display=MacOSDisplay(),
            information=MacOSInformation(),
            mouse=MacOSMouse(),
            network=MacOSNetwork(),
            notify=MacOSNotification(),
            power=MacOSPower(),
        )


@dataclass
class Services:
    system: SystemServices


class ServicesFactory:
    @staticmethod
    def get_platform():
        system = platform.system()

        if system == "Darwin":
            return "macos"

        if system == "Windows":
            return "windows"

        raise RuntimeError(f"Unsupported platform: {system}")

    @staticmethod
    def create() -> Services:

        platform_name = ServicesFactory.get_platform()

        if platform_name == "macos":
            return Services(
                system=MacOSSystemServices()
            )

        raise RuntimeError(
            f"Unsupported platform: {platform_name}"
        )


