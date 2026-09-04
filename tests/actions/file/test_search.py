from pathlib import Path
import pytest
from deskagent.actions.file.search import FindFiles,FindFilesByName,FindFilesByExtension,FindFilesByType,FindFilesBySize,FindFilesByDate,FindFilesByContent,FindRecentFiles,FindLargeFiles,FindDuplicateFiles

def items(r): return r.data.get('files',r.data.get('results',[]))
def paths(r): return [str(x.get('path',x)) if isinstance(x,dict) else str(x) for x in items(r)]

def test_find_recursive(sample_tree):
    r=FindFiles().execute(None,{'directory':str(sample_tree),'recursive':True,'pattern':'*.txt'}); assert r.success; assert any(x.endswith('a.txt') for x in paths(r)); assert any(x.endswith('deep.txt') for x in paths(r))

def test_find_nonrecursive(sample_tree):
    r=FindFiles().execute(None,{'directory':str(sample_tree),'recursive':False,'pattern':'*.txt'}); assert r.success; assert not any(x.endswith('deep.txt') for x in paths(r))

@pytest.mark.parametrize('name',['a.txt','b.txt','deep.txt'])
def test_by_name(sample_tree,name):
    r=FindFilesByName().execute(None,{'directory':str(sample_tree),'name':name}); assert r.success and any(x.endswith(name) for x in paths(r))

def test_by_extension(sample_tree):
    r=FindFilesByExtension().execute(None,{'directory':str(sample_tree),'extension':'.txt'}); assert r.success; assert all(Path(x).suffix=='.txt' for x in paths(r))

def test_by_type(sample_tree):
    r=FindFilesByType().execute(None,{'directory':str(sample_tree),'type':'image'}); assert r.success and any(x.endswith('photo.jpg') for x in paths(r))

def test_by_size(sample_tree):
    r=FindFilesBySize().execute(None,{'directory':str(sample_tree),'min_size':4}); assert r.success; assert all(Path(x['path'] if isinstance(x,dict) else x).stat().st_size>=4 for x in items(r))

def test_by_content(sample_tree):
    r=FindFilesByContent().execute(None,{'directory':str(sample_tree),'query':'database_url','extensions':['.txt','.log']}); assert r.success and any(x.endswith('c.log') for x in paths(r))

def test_recent(sample_tree):
    r=FindRecentFiles().execute(None,{'directory':str(sample_tree),'days':7}); assert r.success and any(x.endswith('a.txt') for x in paths(r))

def test_large_limit(sample_tree):
    r=FindLargeFiles().execute(None,{'directory':str(sample_tree),'limit':2}); assert r.success and len(items(r))<=2

def test_duplicates(sample_tree):
    r=FindDuplicateFiles().execute(None,{'directory':str(sample_tree)}); assert r.success; groups=r.data.get('duplicates',[]); assert any(len(g.get('files',[]))>=2 and any(str(f).endswith('a.txt') for f in g['files']) and any(str(f).endswith('b.txt') for f in g['files']) for g in groups)

def test_empty_search_is_list(sample_tree):
    r=FindFilesByName().execute(None,{'directory':str(sample_tree),'name':'nothing.xyz'}); assert r.success and isinstance(items(r),list)
