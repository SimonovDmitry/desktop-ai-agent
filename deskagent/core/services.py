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
    InputClipboard, InputSelection, InputState,
    InputGestures, InputAutomation
)
from deskagent.platform.base.file import (
    FileInformation, FileLifecycle, FileContent, FileSearch,
    FileOrganization, FilePermissions, FileLinks, FileArchive,
    FileComparison, FileDisk, FileTemporary, FileSystem
)
from deskagent.platform.macos.system import (
    MacOSSystemAudio, MacOSSystemClipboard, MacOSSystemDisplay, MacOSSystemInformation,
    MacOSSystemMouse, MacOSSystemNetwork, MacOSSystemNotification, MacOSSystemPower
)
from deskagent.platform.macos.application import (
    MacOSApplicationLifecycle, MacOSApplicationInformation, MacOSApplicationFocus,
    MacOSApplicationInstances, MacOSApplicationPreferences, MacOSApplicationResources,
    MacOSApplicationDocuments, MacOSApplicationProcesses, MacOSApplicationStartup
)
from deskagent.platform.macos.window import (
    MacOSWindowInformation as MacOSWindowInformation,
    MacOSWindowFocus,
    MacOSWindowPosition, MacOSWindowSize, MacOSWindowState,
    MacOSWindowAppearance, MacOSWindowHierarchy, MacOSWindowDisplay,
    MacOSWindowArrangement, MacOSWindowGroups, MacOSWindowLifecycle
)
from deskagent.platform.macos.input import (
    MacOSInputKeyboard, MacOSInputMouse, MacOSInputShortcuts, MacOSInputHotkeys,
    MacOSInputClipboard, MacOSInputSelection, MacOSInputState,
    MacOSInputGestures, MacOSInputAutomation
)
from deskagent.platform.macos.file import (
    MacOSFileInformation, MacOSFileLifecycle, MacOSFileContent, MacOSFileSearch,
    MacOSFileOrganization, MacOSFilePermissions, MacOSFileLinks, MacOSFileArchive,
    MacOSFileComparison, MacOSFileDisk, MacOSFileTemporary, MacOSFileSystem
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
    clipboard: InputClipboard
    selection: InputSelection
    state: InputState
    gestures: InputGestures
    automation: InputAutomation

@dataclass
class FileServices:
    information: FileInformation
    lifecycle: FileLifecycle
    content: FileContent
    search: FileSearch
    organization: FileOrganization
    permissions: FilePermissions
    links: FileLinks
    archive: FileArchive
    comparison: FileComparison
    disk: FileDisk
    temporary: FileTemporary
    system: FileSystem

class MacOSSystemServices(SystemServices):
    def __init__(self):
        super().__init__(
            audio=MacOSSystemAudio(),
            clipboard=MacOSInputClipboard(),
            display=MacOSSystemDisplay(),
            information=MacOSSystemInformation(),
            mouse=MacOSInputMouse(),
            network=MacOSSystemNetwork(),
            notify=MacOSSystemNotification(),
            power=MacOSSystemPower(),
        )

class MacOSApplicationServices(ApplicationServices):
    def __init__(self):
        super().__init__(
            lifecycle=MacOSApplicationLifecycle(),
            information=MacOSApplicationInformation(),
            focus=MacOSApplicationFocus(),
            preferences=MacOSApplicationPreferences(),
            resources=MacOSApplicationResources(),
            processes=MacOSApplicationProcesses(),
            instances=MacOSApplicationInstances(),
            documents=MacOSApplicationDocuments(),
            startup=MacOSApplicationStartup(),
        )

class MacOSWindowServices(WindowServices):
    def __init__(self):
        super().__init__(
            information=MacOSWindowInformation(),
            focus=MacOSWindowFocus(),
            position=MacOSWindowPosition(),
            size=MacOSWindowSize(),
            state=MacOSWindowState(),
            appearance=MacOSWindowAppearance(),
            hierarchy=MacOSWindowHierarchy(),
            display=MacOSWindowDisplay(),
            arrangement=MacOSWindowArrangement(),
            groups=MacOSWindowGroups(),
            lifecycle=MacOSWindowLifecycle()
        )

class MacOSInputServices(InputServices):
    def __init__(self):
        super().__init__(
            keyboard=MacOSInputKeyboard(),
            mouse=MacOSInputMouse(),
            shortcuts=MacOSInputShortcuts(),
            hotkeys=MacOSInputHotkeys(),
            clipboard=MacOSInputClipboard(),
            selection=MacOSInputSelection(),
            state=MacOSInputState(),
            gestures=MacOSInputGestures(),
            automation=MacOSInputAutomation()
        )

class MacOSFileServices(FileServices):
    def __init__(self):
        super().__init__(
            information=MacOSFileInformation(),
            lifecycle=MacOSFileLifecycle(),
            content=MacOSFileContent(),
            search=MacOSFileSearch(),
            organization=MacOSFileOrganization(),
            permissions=MacOSFilePermissions(),
            links=MacOSFileLinks(),
            archive=MacOSFileArchive(),
            comparison=MacOSFileComparison(),
            disk=MacOSFileDisk(),
            temporary=MacOSFileTemporary(),
            system=MacOSFileSystem()
        )

@dataclass
class Services:
    system: SystemServices
    application: ApplicationServices
    window: WindowServices
    input: InputServices
    file: FileServices


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
                input=MacOSInputServices(),
                file=MacOSFileServices()
            )

        raise RuntimeError(f"Unsupported platform: {platform_name}")