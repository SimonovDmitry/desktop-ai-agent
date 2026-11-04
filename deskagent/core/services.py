import platform
from dataclasses import dataclass

from deskagent.perception.accessibility import AccessibilityClient
from deskagent.platform.base.application import (
    ApplicationDocuments,
    ApplicationFocus,
    ApplicationInformation,
    ApplicationInstances,
    ApplicationLifecycle,
    ApplicationPreferences,
    ApplicationProcesses,
    ApplicationResources,
    ApplicationStartup,
)
from deskagent.platform.base.file import (
    FileArchive,
    FileComparison,
    FileContent,
    FileDisk,
    FileInformation,
    FileLifecycle,
    FileLinks,
    FileOrganization,
    FilePermissions,
    FileSearch,
    FileSystem,
    FileTemporary,
)
from deskagent.platform.base.input import (
    InputAutomation,
    InputClipboard,
    InputGestures,
    InputHotkeys,
    InputKeyboard,
    InputMouse,
    InputSelection,
    InputShortcuts,
    InputState,
)
from deskagent.platform.base.system import (
    SystemAudio,
    SystemClipboard,
    SystemDisplay,
    SystemInformation,
    SystemMouse,
    SystemNetwork,
    SystemNotification,
    SystemPower,
)
from deskagent.platform.base.window import (
    WindowAppearance,
    WindowArrangement,
    WindowDisplay,
    WindowFocus,
    WindowGroups,
    WindowHierarchy,
    WindowInformation,
    WindowLifecycle,
    WindowPosition,
    WindowSize,
    WindowState,
)
from deskagent.platform.macos.application import (
    MacOSApplicationDocuments,
    MacOSApplicationFocus,
    MacOSApplicationInformation,
    MacOSApplicationInstances,
    MacOSApplicationLifecycle,
    MacOSApplicationPreferences,
    MacOSApplicationProcesses,
    MacOSApplicationResources,
    MacOSApplicationStartup,
)
from deskagent.platform.macos.file import (
    MacOSFileArchive,
    MacOSFileComparison,
    MacOSFileContent,
    MacOSFileDisk,
    MacOSFileInformation,
    MacOSFileLifecycle,
    MacOSFileLinks,
    MacOSFileOrganization,
    MacOSFilePermissions,
    MacOSFileSearch,
    MacOSFileSystem,
    MacOSFileTemporary,
)
from deskagent.platform.macos.input import (
    MacOSInputAutomation,
    MacOSInputClipboard,
    MacOSInputGestures,
    MacOSInputHotkeys,
    MacOSInputKeyboard,
    MacOSInputMouse,
    MacOSInputSelection,
    MacOSInputShortcuts,
    MacOSInputState,
)
from deskagent.platform.macos.system import (
    MacOSSystemAudio,
    MacOSSystemClipboard,
    MacOSSystemDisplay,
    MacOSSystemInformation,
    MacOSSystemMouse,
    MacOSSystemNetwork,
    MacOSSystemNotification,
    MacOSSystemPower,
)
from deskagent.platform.macos.window import (
    MacOSWindowAppearance,
    MacOSWindowArrangement,
    MacOSWindowDisplay,
    MacOSWindowFocus,
    MacOSWindowGroups,
    MacOSWindowHierarchy,
    MacOSWindowLifecycle,
    MacOSWindowPosition,
    MacOSWindowSize,
    MacOSWindowState,
)
from deskagent.platform.macos.window import (
    MacOSWindowInformation as MacOSWindowInformation,
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
            clipboard=MacOSSystemClipboard(),
            display=MacOSSystemDisplay(),
            information=MacOSSystemInformation(),
            mouse=MacOSSystemMouse(),
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
            lifecycle=MacOSWindowLifecycle(),
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
            automation=MacOSInputAutomation(),
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
            system=MacOSFileSystem(),
        )


@dataclass
class Services:
    accessibility: AccessibilityClient | None = None
    system: SystemServices | None = None
    application: ApplicationServices | None = None
    window: WindowServices | None = None
    input: InputServices | None = None
    file: FileServices | None = None


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
                accessibility=AccessibilityClient(),
                system=MacOSSystemServices(),
                application=MacOSApplicationServices(),
                window=MacOSWindowServices(),
                input=MacOSInputServices(),
                file=MacOSFileServices(),
            )

        raise RuntimeError(f"Unsupported platform: {platform_name}")
