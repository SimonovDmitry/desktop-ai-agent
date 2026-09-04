from pathlib import Path
import pytest
from deskagent.actions.file.organization import MoveFiles,CopyFiles,RenameFiles,DeleteFiles,OrganizeFiles,GroupFilesByType,GroupFilesByDate,SortFiles,FlattenDirectory

def make_files(tmp_path):
    src=tmp_path/'src'; dst=tmp_path/'dst'; src.mkdir(); dst.mkdir()
    ps=[]
    for n,c in [('a.txt','a'),('b.txt','bb'),('c.log','ccc')]: p=src/n; p.write_text(c); ps.append(p)
    return src,dst,ps

def test_move_files(tmp_path):
    src,dst,ps=make_files(tmp_path); r=MoveFiles().execute(None,{'files':[str(p) for p in ps],'destination':str(dst)}); assert r.success; assert all((dst/p.name).exists() for p in ps); assert all(not p.exists() for p in ps)

def test_copy_files(tmp_path):
    src,dst,ps=make_files(tmp_path); r=CopyFiles().execute(None,{'files':[str(p) for p in ps],'destination':str(dst)}); assert r.success; assert all(p.exists() for p in ps); assert all((dst/p.name).exists() for p in ps)

def test_rename_template(tmp_path):
    src,_,_=make_files(tmp_path); r=RenameFiles().execute(None,{'directory':str(src),'pattern':'*.txt','template':'photo_{index}.txt'}); assert r.success; assert any(p.name.startswith('photo_') for p in src.iterdir())

def test_delete_files(tmp_path):
    src,_,ps=make_files(tmp_path); r=DeleteFiles().execute(None,{'files':[str(ps[0]),str(ps[1])]}); assert r.success and not ps[0].exists() and not ps[1].exists() and ps[2].exists()

def test_organize_by_extension(tmp_path):
    src,dst,_=make_files(tmp_path); r=OrganizeFiles().execute(None,{'directory':str(src),'rules':[{'extension':['.txt'],'destination':str(dst)}]}); assert r.success; assert (dst/'a.txt').exists() and (dst/'b.txt').exists()

@pytest.mark.parametrize('cls,args',[ (GroupFilesByType,lambda p:{'directory':str(p)}),(GroupFilesByDate,lambda p:{'directory':str(p)}),(SortFiles,lambda p:{'directory':str(p),'sort_by':'name'}) ])
def test_organization_reports_result(cls,args,tmp_path):
    src,_,_=make_files(tmp_path); r=cls().execute(None,args(src)); assert r.success and r.data is not None

def test_flatten(tmp_path):
    root=tmp_path/'root'; (root/'A').mkdir(parents=True); (root/'B').mkdir(); (root/'A'/'a.txt').write_text('a'); (root/'B'/'b.txt').write_text('b'); r=FlattenDirectory().execute(None,{'directory':str(root)}); assert r.success; assert (root/'a.txt').exists() and (root/'b.txt').exists()
