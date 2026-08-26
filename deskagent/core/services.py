from dataclasses import dataclass
import platform

from deskagent.platform.base.system import (SystemAudio, SystemClipboard, SystemDisplay, SystemInformation,
                                            SystemMouse, SystemNetwork, SystemNotification, SystemPower)
from deskagent.platform.macos.system import (MacOSAudio, MacOSClipboard, MacOSDisplay, MacOSInformation,
                                             MacOSMouse, MacOSNetwork, MacOSNotification, MacOSPower)
from deskagent.platform.base.application import (ApplicationLifecycle, ApplicationInformation, ApplicationFocus,
                                                 ApplicationPreferences, ApplicationResources, ApplicationProcesses,
                                                 ApplicationInstances, ApplicationDocuments, ApplicationStartup)
from deskagent.platform.macos.application import (MacOSLifecycle, MacOSInformation, MacOSFocus, MacOSInstances,
                                                  MacOSPreferences, MacOSResources, MacOSDocuments, MacOSProcesses,
                                                  MacOSStartup)


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
class ApplicationServices:
    lifecycle: ApplicationLifecycle
    information: ApplicationInformation
    focus: ApplicationFocus
    preferences: ApplicationPreferences
    resources: ApplicationResources
    processes: ApplicationProcesses
    instances: ApplicationInstances
    documents: ApplicationDocuments
    startup: ApplicationStartup


class MacOSApplicationServices(ApplicationServices):
    def __init__(self):
        super().__init__(
            lifecycle=MacOSLifecycle(),
            information=MacOSInformation(),
            focus=MacOSFocus(),
            preferences=MacOSPreferences(),
            resources=MacOSResources(),
            processes=MacOSProcesses(),
            instances=MacOSInstances(),
            documents=MacOSDocuments(),
            startup=MacOSStartup(),
        )


@dataclass
class Services:
    system: SystemServices
    application: ApplicationServices


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
                system=MacOSSystemServices(),
                application=MacOSApplicationServices()
            )

        raise RuntimeError(
            f"Unsupported platform: {platform_name}"
        )