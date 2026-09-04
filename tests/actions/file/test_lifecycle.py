from pathlib import Path
from deskagent.actions.file.lifecycle import CreateFile,DeleteFile,RenameFile,CopyFile,MoveFile,DuplicateFile,ReplaceFile,TrashFile,RestoreFile,EmptyTrash

def test_create_file(tmp_path):
    p=tmp_path/'new.txt'; r=CreateFile().execute(None,{'path':str(p),'content':'Hello, 世界'}); assert r.success; assert p.read_text(encoding='utf-8')=='Hello, 世界'; assert r.data['size']==len('Hello, 世界'.encode())

def test_rename_file(tmp_path):
    old=tmp_path/'old.txt'; old.write_text('data'); r=RenameFile().execute(None,{'path':str(old),'new_name':'new.txt'}); assert r.success; assert not old.exists(); assert (tmp_path/'new.txt').read_text()=='data'; assert r.data['old_path']==str(old)

def test_copy_file(tmp_path):
    src=tmp_path/'a.txt'; dst=tmp_path/'b.txt'; src.write_text('copy'); r=CopyFile().execute(None,{'source':str(src),'destination':str(dst)}); assert r.success; assert src.read_text()=='copy'; assert dst.read_text()=='copy'

def test_move_file(tmp_path):
    src=tmp_path/'a.txt'; dst=tmp_path/'sub'/'b.txt'; src.write_text('move'); dst.parent.mkdir(); r=MoveFile().execute(None,{'source':str(src),'destination':str(dst)}); assert r.success; assert not src.exists(); assert dst.read_text()=='move'

def test_duplicate_file(tmp_path):
    src=tmp_path/'report.pdf'; src.write_bytes(b'PDF'); r=DuplicateFile().execute(None,{'path':str(src)}); assert r.success; dst=Path(r.data['destination']); assert dst.exists() and dst!=src and dst.read_bytes()==src.read_bytes()

def test_delete_file(tmp_path):
    p=tmp_path/'x'; p.write_text('x'); r=DeleteFile().execute(None,{'path':str(p)}); assert r.success and not p.exists()

def test_replace_file(tmp_path):
    src=tmp_path/'src'; dst=tmp_path/'dst'; src.write_text('NEW'); dst.write_text('OLD'); r=ReplaceFile().execute(None,{'source':str(src),'destination':str(dst)}); assert r.success; assert dst.read_text()=='NEW'

def test_special_lifecycle_actions_are_structured(tmp_path):
    p=tmp_path/'x'; p.write_text('x')
    for cls in [TrashFile,RestoreFile]:
        r=cls().execute(None,{'path':str(p)}); assert hasattr(r,'success')
    r=EmptyTrash().execute(None,{}); assert hasattr(r,'success')
