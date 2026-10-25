from deskagent.actions.base import ActionRegistry

from deskagent.actions.application.lifecycle import (
    LaunchApplication, LaunchApplicationWithArguments, LaunchApplicationHidden,
    QuitApplication, ForceQuitApplication, RestartApplication,
    WaitForApplication, WaitForApplicationExit, LaunchOrActivateApplication
)
from deskagent.actions.application.information import (
    GetRunningApplications, GetInstalledApplications, FindApplications,
    GetApplicationInfo, GetApplicationStatus, IsApplicationRunning,
    GetActiveApplication, GetApplicationPID, GetApplicationPath,
    GetApplicationExecutablePath, GetApplicationBundleId, GetApplicationVersion,
    GetApplicationArchitecture, GetApplicationName
)
from deskagent.actions.application.focus import (
    ActivateApplication, HideApplication, ShowApplication,
    MinimizeApplication, RestoreApplication, BringApplicationToFront,
    GetApplicationVisibility, GetApplicationFocusState
)
from deskagent.actions.application.preferences import (
    GetApplicationPermissions, GetAccessibilityPermission, GetAutomationPermission,
    GetNotificationPermission, GetDefaultApplication, OpenWithApplication,
    OpenApplicationPreferences, OpenApplicationSystemSettings
)
from deskagent.actions.application.processes import (
    GetApplicationProcesses, GetApplicationProcessTree, GetApplicationMainProcess,
    GetApplicationChildProcesses, SuspendApplication, ResumeApplication
)
from deskagent.actions.application.resources import (
    GetApplicationCPUUsage, GetApplicationMemoryUsage, GetApplicationDiskUsage,
    GetApplicationResourceUsage, GetTopResourceApplications
)
from deskagent.actions.application.instances import (
    GetApplicationInstances, GetApplicationInstanceCount,
    ActivateApplicationInstance, QuitApplicationInstance
)
from deskagent.actions.application.documents import (
    OpenDocument, OpenMultipleDocuments, OpenURLWithApplication,
    RevealApplicationInFileManager, RevealApplicationExecutable
)
from deskagent.actions.application.startup import (
    GetLoginItems, IsApplicationStartupEnabled, AddApplicationToStartup,
    RemoveApplicationFromStartup, EnableApplicationStartup, DisableApplicationStartup
)

from deskagent.actions.file.information import (
    GetFileInfo, GetFileMetadata, GetFileSize, GetFileType,
    GetFileExtension, GetFileMimeType, GetFilePath, GetFileName,
    GetFileDirectory, GetFileCreatedTime, GetFileModifiedTime,
    GetFileAccessedTime, IsFile, IsDirectory, IsSymlink, IsFileAccessible
)
from deskagent.actions.file.lifecycle import (
    CreateFile, DeleteFile, TrashFile, RestoreFile, EmptyTrash,
    RenameFile, CopyFile, MoveFile, DuplicateFile, ReplaceFile
)
from deskagent.actions.file.content import (
    ReadFile, ReadTextFile, ReadBinaryFile, WriteFile, WriteTextFile,
    AppendToFile, PrependToFile, InsertIntoFile, ReplaceInFile,
    ClearFile, GetFileContentPreview
)
from deskagent.actions.file.search import (
    FindFiles, FindFilesByName, FindFilesByExtension, FindFilesByType,
    FindFilesBySize, FindFilesByDate, FindFilesByContent,
    FindRecentFiles, FindLargeFiles, FindDuplicateFiles
)
from deskagent.actions.file.organization import (
    MoveFiles, CopyFiles, RenameFiles, DeleteFiles, OrganizeFiles,
    GroupFilesByType, GroupFilesByDate, SortFiles, FlattenDirectory
)
from deskagent.actions.file.permissions import (
    GetFilePermissions, GetFileOwner, GetFileGroup, SetFilePermissions,
    AddFilePermission, RemoveFilePermission, SetFileOwner, SetFileGroup,
    IsFileReadable, IsFileWritable, IsFileExecutable
)
from deskagent.actions.file.links import (
    CreateSymbolicLink, CreateHardLink, ReadSymbolicLink, GetLinkTarget,
    ResolvePath, RemoveLink
)
from deskagent.actions.file.archive import (
    CreateArchive, ExtractArchive, ListArchiveContents, AddToArchive,
    RemoveFromArchive, TestArchive, GetArchiveInfo
)
from deskagent.actions.file.comparison import (
    CompareFiles, CompareFileContents, GetFileHash, VerifyFileHash,
    FindDifferences, AreFilesIdentical
)
from deskagent.actions.file.disk import (
    GetFileDiskUsage, GetDirectoryDiskUsage, GetDiskUsage,
    FindLargestFiles as FindLargestFilesDisk,
    FindLargestDirectories, GetStorageStatistics
)
from deskagent.actions.file.temporary import (
    CreateTemporaryFile, CreateTemporaryDirectory, GetTemporaryDirectory,
    CleanupTemporaryFile, CleanupTemporaryDirectory, CleanupTemporaryFiles
)
from deskagent.actions.file.system import (
    OpenFile, OpenFileWithApplication, RevealFile,
    GetFileDefaultApplication, SetFileDefaultApplication,
    LockFile, UnlockFile, GetFileLockState
)

from deskagent.actions.system.audio import (
    SetVolume, IncreaseVolume, DecreaseVolume, Mute, Unmute, GetVolume
)
from deskagent.actions.system.clipboard import (
    GetClipboard, SetClipboard, CleanClipboard
)
from deskagent.actions.system.display import (
    SetDisplayBrightness, GetDisplayBrightness, GetDisplays, GetScreenSize
)
from deskagent.actions.system.information import (
    GetCPUProcesses, GetMemoryProcesses, GetDiskProcesses, GetBatteryStatus,
    GetUptime, GetCurrentTime, GetCurrentDate, SystemInfo, GetCPUInfo,
    GetDiskInfo, GetOSInfo, GetUserInfo
)
from deskagent.actions.system.power import (
    LockScreen, SleepComputer, RestartComputer, ShutdownComputer,
    LogoutComputer, CancelShutdownComputer
)
from deskagent.actions.system.notification import (
    SendNotification, ClearAgentNotification
)
from deskagent.actions.input.shortcuts import (
    PressShortcut, ExecuteShortcutSequence, Copy, Paste, Cut,
    Undo, Redo, Save, Find, Close, Quit, SwitchApplication
)
from deskagent.actions.input.keyboard import (
    PressKey, ReleaseKey, TapKey, HoldKey, ReleaseAllKeys, PressKeys,
    TypeText, TypeTextSlowly, PasteText as TypePasteText,
    CopySelection, CutSelection, SelectAll, DeleteSelection,
    GetKeyboardState as GetKBState
)
from deskagent.actions.input.mouse import (
    GetMousePosition, GetMouseButtonState, MoveMouse, MoveMouseRelative,
    MoveMouseSmoothly, ClickMouse, DoubleClickMouse, TripleClickMouse,
    MouseDown, MouseUp, DragMouse, ScrollMouse, HorizontalScrollMouse
)
from deskagent.actions.input.hotkeys import (
    RegisterHotkey, UnregisterHotkey, UnregisterAllHotkeys,
    GetRegisteredHotkeys, IsHotkeyRegistered, TriggerHotkey
)
from deskagent.actions.input.input_state import (
    GetKeyboardState, GetPressedKeys, IsKeyPressed, GetMouseButtonState as GetMBState,
    IsMouseButtonPressed, GetInputState, ReleaseAllInput
)
from deskagent.actions.input.clipboard import (
    CopyText, PasteText, GetSelectedText, ReplaceSelectedText,
    AppendToClipboard, ClearClipboard
)
from deskagent.actions.input.gestures import (
    MoveAndClick, MoveAndDoubleClick, DragGesture, SwipeGesture,
    ClickAndHold, ScrollGesture, MultiClickGesture
)
from deskagent.actions.input.selection import (
    SelectAllText, SelectText, SelectWord, SelectLine,
    SelectToStart, SelectToEnd, ExtendSelection, ClearSelection
)
from deskagent.actions.input.automation import (
    ExecuteInputSequence, ExecuteInputSequenceWithDelay, WaitForInput,
    WaitForKey, WaitForMouseClick, RepeatInputAction, CancelInputAutomation
)

from deskagent.actions.window.information import (
    GetWindows, GetWindow, FindWindows, GetActiveWindow,
    GetWindowBounds, GetWindowState, GetWindowApplication, IsWindowVisible
)
from deskagent.actions.window.focus import (
    ActivateWindow, FocusWindow, BringWindowToFront, SendWindowToBack,
    MinimizeWindow, RestoreWindow, MaximizeWindow, UnmaximizeWindow, ToggleWindowMaximize
)
from deskagent.actions.window.lifecycle import (
    CloseWindow, CloseWindows, CloseApplicationWindows,
    WaitForWindow, WaitForWindowClose, WaitForWindowVisible, WaitForWindowActive
)
from deskagent.actions.window.position import (
    MoveWindow, MoveWindowTo, CenterWindow, CenterWindowOnDisplay,
    MoveWindowToDisplay, SnapWindowLeft, SnapWindowRight, SnapWindowTop,
    SnapWindowBottom, RestoreWindowPosition
)
from deskagent.actions.window.size import (
    ResizeWindow, ResizeWindowTo, SetWindowWidth, SetWindowHeight,
    SetWindowSize, FitWindowToDisplay, MaximizeWindowToDisplay, RestoreWindowSize
)
from deskagent.actions.window.appearance import (
    SetWindowAlwaysOnTop, RemoveWindowAlwaysOnTop, GetWindowAlwaysOnTop,
    SetWindowOpacity, GetWindowOpacity, SetWindowFullscreen,
    ExitWindowFullscreen, ToggleWindowFullscreen
)
from deskagent.actions.window.hierarchy import (
    GetWindowParent, GetWindowChildren, GetWindowOwner,
    GetApplicationWindows, GetWindowHierarchy
)
from deskagent.actions.window.display import (
    GetWindowDisplay, MoveWindowToDisplay as MoveWinToDisplay,
    MoveWindowToNextDisplay, MoveWindowToPreviousDisplay,
    CenterWindowOnDisplay as CenterWinOnDisplay, MaximizeWindowOnDisplay
)
from deskagent.actions.window.arrangement import (
    ArrangeWindows, TileWindows, CascadeWindows, StackWindows,
    ArrangeApplicationWindows, ArrangeWindowsGrid, EqualizeWindowSizes
)
from deskagent.actions.window.groups import (
    GroupWindows, UngroupWindows, GetWindowGroup, GetWindowGroups,
    ActivateWindowGroup, ArrangeWindowGroup
)
from deskagent.actions.window.state import (
    GetWindowState as GetWinState, SetWindowState, MinimizeWindow as MinWin,
    MaximizeWindow as MaxWin, RestoreWindow as ResWin, HideWindow, ShowWindow,
    ToggleWindowVisibility, ToggleWindowState
)

def create_action_registry():
    registry = ActionRegistry(ignore_duplicates=True)

    registry.register(LaunchApplication)
    registry.register(LaunchApplicationWithArguments)
    registry.register(LaunchApplicationHidden)
    registry.register(QuitApplication)
    registry.register(ForceQuitApplication)
    registry.register(RestartApplication)
    registry.register(WaitForApplication)
    registry.register(WaitForApplicationExit)
    registry.register(LaunchOrActivateApplication)
    registry.register(GetRunningApplications)
    registry.register(GetInstalledApplications)
    registry.register(FindApplications)
    registry.register(GetApplicationInfo)
    registry.register(GetApplicationStatus)
    registry.register(IsApplicationRunning)
    registry.register(GetActiveApplication)
    registry.register(GetApplicationPID)
    registry.register(GetApplicationPath)
    registry.register(GetApplicationExecutablePath)
    registry.register(GetApplicationBundleId)
    registry.register(GetApplicationVersion)
    registry.register(GetApplicationArchitecture)
    registry.register(GetApplicationName)
    registry.register(ActivateApplication)
    registry.register(HideApplication)
    registry.register(ShowApplication)
    registry.register(MinimizeApplication)
    registry.register(RestoreApplication)
    registry.register(BringApplicationToFront)
    registry.register(GetApplicationVisibility)
    registry.register(GetApplicationFocusState)
    registry.register(GetApplicationPermissions)
    registry.register(GetAccessibilityPermission)
    registry.register(GetAutomationPermission)
    registry.register(GetNotificationPermission)
    registry.register(GetDefaultApplication)
    registry.register(OpenWithApplication)
    registry.register(OpenApplicationPreferences)
    registry.register(OpenApplicationSystemSettings)
    registry.register(GetApplicationProcesses)
    registry.register(GetApplicationProcessTree)
    registry.register(GetApplicationMainProcess)
    registry.register(GetApplicationChildProcesses)
    registry.register(SuspendApplication)
    registry.register(ResumeApplication)
    registry.register(GetApplicationCPUUsage)
    registry.register(GetApplicationMemoryUsage)
    registry.register(GetApplicationDiskUsage)
    registry.register(GetApplicationResourceUsage)
    registry.register(GetTopResourceApplications)
    registry.register(GetApplicationInstances)
    registry.register(GetApplicationInstanceCount)
    registry.register(ActivateApplicationInstance)
    registry.register(QuitApplicationInstance)
    registry.register(OpenDocument)
    registry.register(OpenMultipleDocuments)
    registry.register(OpenURLWithApplication)
    registry.register(RevealApplicationInFileManager)
    registry.register(RevealApplicationExecutable)
    registry.register(GetLoginItems)
    registry.register(IsApplicationStartupEnabled)
    registry.register(AddApplicationToStartup)
    registry.register(RemoveApplicationFromStartup)
    registry.register(EnableApplicationStartup)
    registry.register(DisableApplicationStartup)

    registry.register(GetFileInfo)
    registry.register(GetFileMetadata)
    registry.register(GetFileSize)
    registry.register(GetFileType)
    registry.register(GetFileExtension)
    registry.register(GetFileMimeType)
    registry.register(GetFilePath)
    registry.register(GetFileName)
    registry.register(GetFileDirectory)
    registry.register(GetFileCreatedTime)
    registry.register(GetFileModifiedTime)
    registry.register(GetFileAccessedTime)
    registry.register(IsFile)
    registry.register(IsDirectory)
    registry.register(IsSymlink)
    registry.register(IsFileAccessible)
    registry.register(CreateFile)
    registry.register(DeleteFile)
    registry.register(TrashFile)
    registry.register(RestoreFile)
    registry.register(EmptyTrash)
    registry.register(RenameFile)
    registry.register(CopyFile)
    registry.register(MoveFile)
    registry.register(DuplicateFile)
    registry.register(ReplaceFile)
    registry.register(ReadFile)
    registry.register(ReadTextFile)
    registry.register(ReadBinaryFile)
    registry.register(WriteFile)
    registry.register(WriteTextFile)
    registry.register(AppendToFile)
    registry.register(PrependToFile)
    registry.register(InsertIntoFile)
    registry.register(ReplaceInFile)
    registry.register(ClearFile)
    registry.register(GetFileContentPreview)
    registry.register(FindFiles)
    registry.register(FindFilesByName)
    registry.register(FindFilesByExtension)
    registry.register(FindFilesByType)
    registry.register(FindFilesBySize)
    registry.register(FindFilesByDate)
    registry.register(FindFilesByContent)
    registry.register(FindRecentFiles)
    registry.register(FindLargeFiles)
    registry.register(FindDuplicateFiles)
    registry.register(MoveFiles)
    registry.register(CopyFiles)
    registry.register(RenameFiles)
    registry.register(DeleteFiles)
    registry.register(OrganizeFiles)
    registry.register(GroupFilesByType)
    registry.register(GroupFilesByDate)
    registry.register(SortFiles)
    registry.register(FlattenDirectory)
    registry.register(GetFilePermissions)
    registry.register(GetFileOwner)
    registry.register(GetFileGroup)
    registry.register(SetFilePermissions)
    registry.register(AddFilePermission)
    registry.register(RemoveFilePermission)
    registry.register(SetFileOwner)
    registry.register(SetFileGroup)
    registry.register(IsFileReadable)
    registry.register(IsFileWritable)
    registry.register(IsFileExecutable)
    registry.register(CreateSymbolicLink)
    registry.register(CreateHardLink)
    registry.register(ReadSymbolicLink)
    registry.register(GetLinkTarget)
    registry.register(ResolvePath)
    registry.register(RemoveLink)
    registry.register(CreateArchive)
    registry.register(ExtractArchive)
    registry.register(ListArchiveContents)
    registry.register(AddToArchive)
    registry.register(RemoveFromArchive)
    registry.register(TestArchive)
    registry.register(GetArchiveInfo)
    registry.register(CompareFiles)
    registry.register(CompareFileContents)
    registry.register(GetFileHash)
    registry.register(VerifyFileHash)
    registry.register(FindDifferences)
    registry.register(AreFilesIdentical)
    registry.register(GetFileDiskUsage)
    registry.register(GetDirectoryDiskUsage)
    registry.register(GetDiskUsage)
    registry.register(FindLargestFilesDisk)
    registry.register(FindLargestDirectories)
    registry.register(GetStorageStatistics)
    registry.register(CreateTemporaryFile)
    registry.register(CreateTemporaryDirectory)
    registry.register(GetTemporaryDirectory)
    registry.register(CleanupTemporaryFile)
    registry.register(CleanupTemporaryDirectory)
    registry.register(CleanupTemporaryFiles)
    registry.register(OpenFile)
    registry.register(OpenFileWithApplication)
    registry.register(RevealFile)
    registry.register(GetFileDefaultApplication)
    registry.register(SetFileDefaultApplication)
    registry.register(LockFile)
    registry.register(UnlockFile)
    registry.register(GetFileLockState)

    registry.register(SetVolume)
    registry.register(IncreaseVolume)
    registry.register(DecreaseVolume)
    registry.register(Mute)
    registry.register(Unmute)
    registry.register(GetVolume)
    registry.register(GetClipboard)
    registry.register(SetClipboard)
    registry.register(CleanClipboard)
    registry.register(SetDisplayBrightness)
    registry.register(GetDisplayBrightness)
    registry.register(GetDisplays)
    registry.register(GetScreenSize)
    registry.register(GetCPUProcesses)
    registry.register(GetMemoryProcesses)
    registry.register(GetDiskProcesses)
    registry.register(GetBatteryStatus)
    registry.register(GetUptime)
    registry.register(GetCurrentTime)
    registry.register(GetCurrentDate)
    registry.register(SystemInfo)
    registry.register(GetCPUInfo)
    registry.register(GetDiskInfo)
    registry.register(GetOSInfo)
    registry.register(GetUserInfo)
    registry.register(LockScreen)
    registry.register(SleepComputer)
    registry.register(RestartComputer)
    registry.register(ShutdownComputer)
    registry.register(LogoutComputer)
    registry.register(CancelShutdownComputer)
    registry.register(SendNotification)
    registry.register(ClearAgentNotification)
    registry.register(PressShortcut)
    registry.register(ExecuteShortcutSequence)
    registry.register(Copy)
    registry.register(Paste)
    registry.register(Cut)
    registry.register(Undo)
    registry.register(Redo)
    registry.register(Save)
    registry.register(Find)
    registry.register(Close)
    registry.register(Quit)
    registry.register(SwitchApplication)
    registry.register(PressKey)
    registry.register(ReleaseKey)
    registry.register(TapKey)
    registry.register(HoldKey)
    registry.register(ReleaseAllKeys)
    registry.register(PressKeys)
    registry.register(TypeText)
    registry.register(TypeTextSlowly)
    registry.register(TypePasteText)
    registry.register(CopySelection)
    registry.register(CutSelection)
    registry.register(SelectAll)
    registry.register(DeleteSelection)
    registry.register(GetKBState)
    registry.register(GetMousePosition)
    registry.register(GetMouseButtonState)
    registry.register(MoveMouse)
    registry.register(DragMouse)
    registry.register(ScrollMouse)
    registry.register(MoveMouseRelative)
    registry.register(MoveMouseSmoothly)
    registry.register(ClickMouse)
    registry.register(DoubleClickMouse)
    registry.register(TripleClickMouse)
    registry.register(MouseDown)
    registry.register(MouseUp)
    registry.register(HorizontalScrollMouse)
    registry.register(RegisterHotkey)
    registry.register(UnregisterHotkey)
    registry.register(UnregisterAllHotkeys)
    registry.register(GetRegisteredHotkeys)
    registry.register(IsHotkeyRegistered)
    registry.register(TriggerHotkey)
    registry.register(GetKeyboardState)
    registry.register(GetPressedKeys)
    registry.register(IsKeyPressed)
    registry.register(GetMBState)
    registry.register(IsMouseButtonPressed)
    registry.register(GetInputState)
    registry.register(ReleaseAllInput)
    registry.register(CopyText)
    registry.register(PasteText)
    registry.register(GetSelectedText)
    registry.register(ReplaceSelectedText)
    registry.register(AppendToClipboard)
    registry.register(ClearClipboard)
    registry.register(MoveAndClick)
    registry.register(MoveAndDoubleClick)
    registry.register(DragGesture)
    registry.register(SwipeGesture)
    registry.register(ClickAndHold)
    registry.register(ScrollGesture)
    registry.register(MultiClickGesture)
    registry.register(SelectAllText)
    registry.register(SelectText)
    registry.register(SelectWord)
    registry.register(SelectLine)
    registry.register(SelectToStart)
    registry.register(SelectToEnd)
    registry.register(ExtendSelection)
    registry.register(ClearSelection)
    registry.register(ExecuteInputSequence)
    registry.register(ExecuteInputSequenceWithDelay)
    registry.register(WaitForInput)
    registry.register(WaitForKey)
    registry.register(WaitForMouseClick)
    registry.register(RepeatInputAction)
    registry.register(CancelInputAutomation)

    registry.register(GetWindows)
    registry.register(GetWindow)
    registry.register(FindWindows)
    registry.register(GetActiveWindow)
    registry.register(GetWindowBounds)
    registry.register(GetWindowState)
    registry.register(GetWinState)
    registry.register(GetWindowApplication)
    registry.register(IsWindowVisible)
    registry.register(ActivateWindow)
    registry.register(FocusWindow)
    registry.register(BringWindowToFront)
    registry.register(SendWindowToBack)
    registry.register(MinimizeWindow)
    registry.register(RestoreWindow)
    registry.register(MaximizeWindow)
    registry.register(UnmaximizeWindow)
    registry.register(ToggleWindowMaximize)
    registry.register(CloseWindow)
    registry.register(CloseWindows)
    registry.register(CloseApplicationWindows)
    registry.register(WaitForWindow)
    registry.register(WaitForWindowClose)
    registry.register(WaitForWindowVisible)
    registry.register(WaitForWindowActive)
    registry.register(MoveWindow)
    registry.register(MoveWindowTo)
    registry.register(CenterWindow)
    registry.register(CenterWindowOnDisplay)
    registry.register(MoveWindowToDisplay)
    registry.register(SnapWindowLeft)
    registry.register(SnapWindowRight)
    registry.register(SnapWindowTop)
    registry.register(SnapWindowBottom)
    registry.register(RestoreWindowPosition)
    registry.register(ResizeWindow)
    registry.register(ResizeWindowTo)
    registry.register(SetWindowWidth)
    registry.register(SetWindowHeight)
    registry.register(SetWindowSize)
    registry.register(FitWindowToDisplay)
    registry.register(MaximizeWindowToDisplay)
    registry.register(RestoreWindowSize)
    registry.register(SetWindowAlwaysOnTop)
    registry.register(RemoveWindowAlwaysOnTop)
    registry.register(GetWindowAlwaysOnTop)
    registry.register(SetWindowOpacity)
    registry.register(GetWindowOpacity)
    registry.register(SetWindowFullscreen)
    registry.register(ExitWindowFullscreen)
    registry.register(ToggleWindowFullscreen)
    registry.register(GetWindowParent)
    registry.register(GetWindowChildren)
    registry.register(GetWindowOwner)
    registry.register(GetApplicationWindows)
    registry.register(GetWindowHierarchy)
    registry.register(GetWindowDisplay)
    registry.register(MoveWinToDisplay)
    registry.register(MoveWindowToNextDisplay)
    registry.register(MoveWindowToPreviousDisplay)
    registry.register(CenterWinOnDisplay)
    registry.register(MaximizeWindowOnDisplay)
    registry.register(ArrangeWindows)
    registry.register(TileWindows)
    registry.register(CascadeWindows)
    registry.register(StackWindows)
    registry.register(ArrangeApplicationWindows)
    registry.register(ArrangeWindowsGrid)
    registry.register(EqualizeWindowSizes)
    registry.register(GroupWindows)
    registry.register(UngroupWindows)
    registry.register(GetWindowGroup)
    registry.register(GetWindowGroups)
    registry.register(ActivateWindowGroup)
    registry.register(ArrangeWindowGroup)
    registry.register(SetWindowState)
    registry.register(MinWin)
    registry.register(MaxWin)
    registry.register(ResWin)
    registry.register(HideWindow)
    registry.register(ShowWindow)
    registry.register(ToggleWindowVisibility)
    registry.register(ToggleWindowState)

    return registry
