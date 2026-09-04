import inspect
import pytest
from deskagent.actions.file.information import *
from deskagent.actions.file.lifecycle import *
from deskagent.actions.file.content import *
from deskagent.actions.file.search import *
from deskagent.actions.file.organization import *
from deskagent.actions.file.permissions import *
from deskagent.actions.file.links import *
from deskagent.actions.file.archive import *
from deskagent.actions.file.comparison import *
from deskagent.actions.file.disk import *
from deskagent.actions.file.temporary import *
from deskagent.actions.file.system import *

ALL_ACTIONS = [
GetFileInfo,GetFileMetadata,GetFileSize,GetFileType,GetFileExtension,GetFileMimeType,GetFilePath,GetFileName,GetFileDirectory,GetFileCreatedTime,GetFileModifiedTime,GetFileAccessedTime,IsFile,IsDirectory,IsSymlink,IsFileAccessible,
CreateFile,DeleteFile,RestoreFile,TrashFile,EmptyTrash,RenameFile,CopyFile,MoveFile,DuplicateFile,ReplaceFile,
ReadFile,ReadTextFile,ReadBinaryFile,WriteFile,WriteTextFile,AppendToFile,PrependToFile,InsertIntoFile,ReplaceInFile,ClearFile,GetFileContentPreview,
FindFiles,FindFilesByName,FindFilesByExtension,FindFilesByType,FindFilesBySize,FindFilesByDate,FindFilesByContent,FindRecentFiles,FindLargeFiles,FindDuplicateFiles,
MoveFiles,CopyFiles,RenameFiles,DeleteFiles,OrganizeFiles,GroupFilesByType,GroupFilesByDate,SortFiles,FlattenDirectory,
GetFilePermissions,SetFilePermissions,AddFilePermission,RemoveFilePermission,GetFileOwner,SetFileOwner,GetFileGroup,SetFileGroup,IsFileReadable,IsFileWritable,IsFileExecutable,
CreateSymbolicLink,CreateHardLink,ReadSymbolicLink,GetLinkTarget,RemoveLink,ResolvePath,
CreateArchive,ExtractArchive,ListArchiveContents,AddToArchive,RemoveFromArchive,TestArchive,GetArchiveInfo,
CompareFiles,CompareFileContents,GetFileHash,VerifyFileHash,FindDifferences,AreFilesIdentical,
GetFileDiskUsage,GetDirectoryDiskUsage,GetDiskUsage,FindLargestFiles,FindLargestDirectories,GetStorageStatistics,
CreateTemporaryFile,CreateTemporaryDirectory,GetTemporaryDirectory,CleanupTemporaryFile,CleanupTemporaryDirectory,CleanupTemporaryFiles,
OpenFile,OpenFileWithApplication,RevealFile,RevealFileInFileManager,GetFileDefaultApplication,SetFileDefaultApplication,LockFile,UnlockFile,GetFileLockState]

@pytest.mark.parametrize('cls', ALL_ACTIONS)
def test_action_metadata_contract(cls):
    assert inspect.isclass(cls)
    assert isinstance(cls.name,str) and cls.name
    assert isinstance(cls.description,str) and cls.description
    assert isinstance(cls.parameters_schema,dict)
    assert hasattr(cls,'category') and hasattr(cls,'risk_level')
    assert isinstance(cls.requires_confirmation,bool)
    assert isinstance(cls.reversible,bool)
    assert callable(getattr(cls,'execute',None))

def test_names_unique():
    names=[c.name for c in ALL_ACTIONS]
    assert len(names)==len(set(names))

@pytest.mark.parametrize('cls',[DeleteFile,DeleteFiles,EmptyTrash,ReplaceFile,SetFileOwner,SetFileGroup])
def test_destructive_actions_require_confirmation(cls):
    assert cls.requires_confirmation is True
