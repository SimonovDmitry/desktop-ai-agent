from pathlib import Path
from deskagent.actions.file.temporary import CreateTemporaryFile,CreateTemporaryDirectory,GetTemporaryDirectory,CleanupTemporaryFile,CleanupTemporaryDirectory,CleanupTemporaryFiles

def test_create_temp_file():
    r=CreateTemporaryFile().execute(None,{}); assert r.success; p=Path(r.data['path']); assert p.is_file(); p.unlink(missing_ok=True)

def test_create_temp_file_content():
    r=CreateTemporaryFile().execute(None,{'content':'hello'}); assert r.success; p=Path(r.data['path']); assert p.read_text()=='hello'; p.unlink(missing_ok=True)

def test_create_temp_dir():
    r=CreateTemporaryDirectory().execute(None,{}); assert r.success; p=Path(r.data['path']); assert p.is_dir(); p.rmdir()

def test_get_temp_dir():
    r=GetTemporaryDirectory().execute(None,{}); assert r.success and Path(r.data['path']).is_dir()

def test_cleanup_file(tmp_path):
    p=tmp_path/'x.tmp'; p.write_text('x'); r=CleanupTemporaryFile().execute(None,{'path':str(p)}); assert r.success and not p.exists()

def test_cleanup_dir(tmp_path):
    p=tmp_path/'d'; p.mkdir(); (p/'x').write_text('x'); r=CleanupTemporaryDirectory().execute(None,{'path':str(p)}); assert r.success and not p.exists()

def test_cleanup_many(tmp_path):
    r=CleanupTemporaryFiles().execute(None,{'directory':str(tmp_path)}); assert hasattr(r,'success')
