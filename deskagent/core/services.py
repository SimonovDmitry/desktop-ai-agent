from dataclasses import dataclass
import platform

from deskagent.platform.base.system import (
    SystemAudio, SystemClipboard, SystemDisplay, SystemInformation,
    SystemMouse, SystemNetwork, SystemNotification, SystemPower
)
from deskagent.platform.base.application import (
    ApplicationLifecycle, ApplicationInformation, ApplicationFocus,
    ApplicationPreferences, ApplicationResources, ApplicationProcesses,
    ApplicationInstances, ApplicationDocuments, ApplicationStartup
)
from deskagent.platform.base.window import (
    WindowInformation, WindowFocus, WindowPosition, WindowSize, WindowState,
    WindowAppearance, WindowHierarchy, WindowDisplay, WindowArrangement,
    WindowGroups, WindowLifecycle
)
from deskagent.platform.base.input import (
    InputKeyboard, InputMouse, InputShortcuts, InputHotkeys,
    InputClipboard as InputInputClipboard,
    InputSelection, InputState as InputInputState,
    InputGestures, InputAutomation
)
from deskagent.platform.macos.system import (
    MacOSAudio, MacOSClipboard, MacOSDisplay, MacOSInformation,
    MacOSMouse, MacOSNetwork, MacOSNotification, MacOSPower
)
from deskagent.platform.macos.application import (
    MacOSLifecycle,
    MacOSInformation as MacOSAppInformation,
    MacOSFocus as MacOSAppFocus,
    MacOSInstances, MacOSPreferences, MacOSResources,
    MacOSDocuments, MacOSProcesses, MacOSStartup
)
from deskagent.platform.macos.window import (
    MacOSInformation as MacOSWindowInformation,
    MacOSFocus as MacOSWindowFocus,
    MacOSPosition, MacOSSize, MacOSState,
    MacOSAppearance, MacOSHierarchy, MacOSDisplay as MacOSWindowDisplay,
    MacOSArrangement, MacOSGroups, MacOSLifecycle as MacOSWindowLifecycle
)
from deskagent.platform.macos.input import (
    MacOSKeyboard, MacOSMouse, MacOSShortcuts, MacOSHotkeys,
    MacOSClipboard, MacOSSelection, MacOSState,
    MacOSGestures, MacOSAutomation
)


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

@dataclass
class WindowServices:
    information: WindowInformation
    focus: WindowFocus
    position: WindowPosition
    size: WindowSize
    state: WindowState
    appearance: WindowAppearance
    hierarchy: WindowHierarchy
    display: WindowDisplay
    arrangement: WindowArrangement
    groups: WindowGroups
    lifecycle: WindowLifecycle

@dataclass
class InputServices:
    keyboard: InputKeyboard
    mouse: InputMouse
    shortcuts: InputShortcuts
    hotkeys: InputHotkeys
    clipboard: InputInputClipboard
    selection: InputSelection
    state: InputInputState
    gestures: InputGestures
    automation: InputAutomation


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

class MacOSApplicationServices(ApplicationServices):
    def __init__(self):
        super().__init__(
            lifecycle=MacOSLifecycle(),
            information=MacOSAppInformation(),
            focus=MacOSAppFocus(),
            preferences=MacOSPreferences(),
            resources=MacOSResources(),
            processes=MacOSProcesses(),
            instances=MacOSInstances(),
            documents=MacOSDocuments(),
            startup=MacOSStartup(),
        )

class MacOSWindowServices(WindowServices):
    def __init__(self):
        super().__init__(
            information=MacOSWindowInformation(),
            focus=MacOSWindowFocus(),
            position=MacOSPosition(),
            size=MacOSSize(),
            state=MacOSState(),
            appearance=MacOSAppearance(),
            hierarchy=MacOSHierarchy(),
            display=MacOSWindowDisplay(),
            arrangement=MacOSArrangement(),
            groups=MacOSGroups(),
            lifecycle=MacOSWindowLifecycle()
        )

class MacOSInputServices(InputServices):
    def __init__(self):
        super().__init__(
            keyboard=MacOSKeyboard(),
            mouse=MacOSMouse(),
            shortcuts=MacOSShortcuts(),
            hotkeys=MacOSHotkeys(),
            clipboard=MacOSClipboard(),
            selection=MacOSSelection(),
            state=MacOSState(),
            gestures=MacOSGestures(),
            automation=MacOSAutomation()
        )

@dataclass
class Services:
    system: SystemServices
    application: ApplicationServices
    window: WindowServices
    input: InputServices


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
                application=MacOSApplicationServices(),
                window=MacOSWindowServices(),
                input=MacOSInputServices()
            )

        raise RuntimeError(f"Unsupported platform: {platform_name}")
