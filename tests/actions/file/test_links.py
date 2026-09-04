from pathlib import Path
from deskagent.actions.file.links import CreateSymbolicLink,CreateHardLink,ReadSymbolicLink,GetLinkTarget,RemoveLink,ResolvePath

def test_symlink_roundtrip(tmp_path):
    target=tmp_path/'target.txt'; link=tmp_path/'link.txt'; target.write_text('target'); r=CreateSymbolicLink().execute(None,{'target':str(target),'link':str(link)}); assert r.success and link.is_symlink(); q=ReadSymbolicLink().execute(None,{'path':str(link)}); assert q.success and q.data['target']==str(target)

def test_get_link_target(tmp_path):
    target=tmp_path/'real'; target.write_text('x'); link=tmp_path/'link'; link.symlink_to(target); r=GetLinkTarget().execute(None,{'path':str(link)}); assert r.success and Path(r.data['target']).resolve()==target.resolve()

def test_remove_link_preserves_target(tmp_path):
    target=tmp_path/'real'; link=tmp_path/'link'; target.write_text('keep'); link.symlink_to(target); r=RemoveLink().execute(None,{'link':str(link)}); assert r.success and not link.exists() and target.exists()

def test_resolve_path(tmp_path):
    target=tmp_path/'deep'/'real'; target.parent.mkdir(); target.write_text('x'); link=tmp_path/'link'; link.symlink_to(target); r=ResolvePath().execute(None,{'path':str(link)}); assert r.success and Path(r.data['path'])==target.resolve()

def test_hard_link(tmp_path):
    target=tmp_path/'real'; link=tmp_path/'hard'; target.write_bytes(b'123'); r=CreateHardLink().execute(None,{'target':str(target),'link':str(link)}); assert r.success and link.exists() and target.stat().st_ino==link.stat().st_ino
