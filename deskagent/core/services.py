from dataclasses import dataclass
import platform

from deskagent.platform.base.system import (SystemAudio, SystemClipboard, SystemDisplay, SystemInformation, SystemMouse,
                                            SystemNetwork, SystemNotification, SystemPower)
from deskagent.platform.macos.system import (MacOSAudio, MacOSClipboard, MacOSDisplay, MacOSInformation, MacOSMouse,
                                             MacOSNetwork, MacOSNotification, MacOSPower)


@dataclass
class SystemServices:
    audio: SystemAudio
    clipboard: SystemClipboard
    display: SystemDisplay
    information: SystemInformation
    mouse: SystemMouse
    network: SystemNetwork
    notify: SystemNotification
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
