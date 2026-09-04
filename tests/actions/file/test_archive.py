import zipfile
from deskagent.actions.file.archive import CreateArchive,ExtractArchive,ListArchiveContents,AddToArchive,RemoveFromArchive,TestArchive,GetArchiveInfo

def setup(tmp_path):
    src=tmp_path/'src'; src.mkdir(); (src/'a.txt').write_text('A'); (src/'b.txt').write_text('B'); return src,tmp_path/'bundle.zip'

def create(src,archive): return CreateArchive().execute(None,{'files':[str(src/'a.txt'),str(src/'b.txt')],'destination':str(archive),'format':'zip'})

def test_create_and_list(tmp_path):
    src,a=setup(tmp_path); r=create(src,a); assert r.success and a.exists(); q=ListArchiveContents().execute(None,{'archive':str(a)}); assert q.success and q.data is not None; 
    with zipfile.ZipFile(a) as z: assert any(n.endswith('a.txt') for n in z.namelist())

def test_extract(tmp_path):
    src,a=setup(tmp_path); assert create(src,a).success; out=tmp_path/'out'; r=ExtractArchive().execute(None,{'archive':str(a),'destination':str(out)}); assert r.success; assert any(p.name=='a.txt' for p in out.rglob('*')); assert any(p.name=='b.txt' for p in out.rglob('*'))

def test_test_and_info(tmp_path):
    src,a=setup(tmp_path); assert create(src,a).success; r=TestArchive().execute(None,{'archive':str(a)}); assert r.success and r.data['valid'] is True; q=GetArchiveInfo().execute(None,{'archive':str(a)}); assert q.success and {'format','size','entries'}<=set(q.data)

def test_add_remove(tmp_path):
    src,a=setup(tmp_path); CreateArchive().execute(None,{'files':[str(src/'a.txt')],'destination':str(a),'format':'zip'}); r=AddToArchive().execute(None,{'archive':str(a),'files':[str(src/'b.txt')]}); assert r.success; q=RemoveFromArchive().execute(None,{'archive':str(a),'file':'a.txt'}); assert q.success
    with zipfile.ZipFile(a) as z: names=z.namelist(); assert not any(n.endswith('a.txt') for n in names); assert any(n.endswith('b.txt') for n in names)

def test_corrupt_archive(tmp_path):
    a=tmp_path/'broken.zip'; a.write_bytes(b'not zip'); r=TestArchive().execute(None,{'archive':str(a)}); assert r.success is False or r.data.get('valid') is False
