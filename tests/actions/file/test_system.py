import pytest
from deskagent.actions.file.system import OpenFile,OpenFileWithApplication,RevealFile,RevealFileInFileManager,GetFileDefaultApplication,SetFileDefaultApplication,LockFile,UnlockFile,GetFileLockState

def test_open(service_context,text_file):
    s=service_context.services.system.file; s.open_file.return_value=True; r=OpenFile().execute(service_context,{'path':str(text_file)}); assert r.success; s.open_file.assert_called_once_with(str(text_file))

def test_open_with_app(service_context,text_file):
    s=service_context.services.system.file; s.open_file_with_application.return_value=True; r=OpenFileWithApplication().execute(service_context,{'path':str(text_file),'application':'Preview'}); assert r.success; s.open_file_with_application.assert_called_once_with(str(text_file),'Preview')

def test_reveal(service_context,text_file):
    s=service_context.services.system.file; s.reveal_file.return_value=True; r=RevealFile().execute(service_context,{'path':str(text_file)}); assert r.success; s.reveal_file.assert_called_once_with(str(text_file))

def test_reveal_file_manager(service_context,text_file):
    s=service_context.services.system.file; s.reveal_file_in_file_manager.return_value=True; r=RevealFileInFileManager().execute(service_context,{'path':str(text_file)}); assert r.success; s.reveal_file_in_file_manager.assert_called_once_with(str(text_file))

def test_default_application(service_context,text_file):
    s=service_context.services.system.file; s.get_default_application.return_value='Preview'; r=GetFileDefaultApplication().execute(service_context,{'path':str(text_file)}); assert r.success and r.data['application']=='Preview'

def test_set_default_application(service_context,text_file):
    s=service_context.services.system.file; s.set_default_application.return_value=True; r=SetFileDefaultApplication().execute(service_context,{'path':str(text_file),'application':'TextEdit'}); assert r.success; s.set_default_application.assert_called_once_with(str(text_file),'TextEdit')

def test_lock_unlock(service_context,text_file):
    s=service_context.services.system.file; s.lock_file.return_value=True; s.unlock_file.return_value=True; assert LockFile().execute(service_context,{'path':str(text_file)}).success; assert UnlockFile().execute(service_context,{'path':str(text_file)}).success

def test_lock_state(service_context,text_file):
    s=service_context.services.system.file; s.get_file_lock_state.return_value=True; r=GetFileLockState().execute(service_context,{'path':str(text_file)}); assert r.success and r.data['locked'] is True
