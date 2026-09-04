import stat
import pytest
from deskagent.actions.file.permissions import GetFilePermissions,SetFilePermissions,AddFilePermission,RemoveFilePermission,GetFileOwner,GetFileGroup,IsFileReadable,IsFileWritable,IsFileExecutable

def test_get_permissions(text_file):
    r=GetFilePermissions().execute(None,{'path':str(text_file)}); assert r.success; assert len(r.data['mode'])==4 and r.data['mode'].isdigit()

def test_set_permissions(tmp_path):
    p=tmp_path/'x'; p.write_text('x'); r=SetFilePermissions().execute(None,{'path':str(p),'mode':'0755'}); assert r.success; assert stat.S_IMODE(p.stat().st_mode)==0o755

def test_add_remove_owner_execute(tmp_path):
    p=tmp_path/'x'; p.write_text('x'); p.chmod(0o600); r=AddFilePermission().execute(None,{'path':str(p),'permission':'owner_execute'}); assert r.success and p.stat().st_mode&stat.S_IXUSR; r=RemoveFilePermission().execute(None,{'path':str(p),'permission':'owner_execute'}); assert r.success and not p.stat().st_mode&stat.S_IXUSR

def test_owner_group(text_file):
    o=GetFileOwner().execute(None,{'path':str(text_file)}); g=GetFileGroup().execute(None,{'path':str(text_file)}); assert o.success and o.data['owner']; assert g.success and g.data['group']

@pytest.mark.parametrize('cls,key',[ (IsFileReadable,'readable'),(IsFileWritable,'writable'),(IsFileExecutable,'executable') ])
def test_permission_predicates(cls,key,text_file):
    r=cls().execute(None,{'path':str(text_file)}); assert r.success and isinstance(r.data[key],bool)
