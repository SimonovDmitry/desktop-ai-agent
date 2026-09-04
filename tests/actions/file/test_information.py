from pathlib import Path
import pytest
from deskagent.actions.file.information import GetFileInfo,GetFileMetadata,GetFileSize,GetFileType,GetFileExtension,GetFileMimeType,GetFilePath,GetFileName,GetFileDirectory,GetFileCreatedTime,GetFileModifiedTime,GetFileAccessedTime,IsFile,IsDirectory,IsSymlink,IsFileAccessible

def test_get_file_info(text_file):
    r=GetFileInfo().execute(None,{'path':str(text_file)}); assert r.success
    assert r.data['name']=='document.txt'; assert r.data['extension']=='.txt'; assert r.data['size']==len(text_file.read_bytes()); assert r.data['type']=='file'

def test_get_metadata(text_file):
    r=GetFileMetadata().execute(None,{'path':str(text_file)}); assert r.success
    assert {'size','created_at','modified_at','permissions','owner','group'} <= set(r.data)

def test_size(text_file):
    r=GetFileSize().execute(None,{'path':str(text_file)}); assert r.success; assert r.data['size']==len(text_file.read_bytes())

@pytest.mark.parametrize('name,expected',[('README',''),('archive.tar.gz','.gz'),('.env',''),('photo.JPG','.JPG'),('report.final.pdf','.pdf')])
def test_extension_edges(tmp_path,name,expected):
    p=tmp_path/name; p.write_text('x'); r=GetFileExtension().execute(None,{'path':str(p)}); assert r.success; assert r.data['extension']==expected

def test_path_normalized(tmp_path):
    p=tmp_path/'a'/'b.txt'; p.parent.mkdir(); p.write_text('x'); r=GetFilePath().execute(None,{'path':str(tmp_path/'a'/'..'/'a'/'b.txt')}); assert r.success; assert Path(r.data['path'])==p.resolve()

def test_name_and_directory(text_file):
    n=GetFileName().execute(None,{'path':str(text_file)}); d=GetFileDirectory().execute(None,{'path':str(text_file)}); assert n.success and n.data['name']=='document.txt'; assert d.success and Path(d.data['directory'])==text_file.parent

def test_file_and_directory_predicates(tmp_path,text_file):
    directory=tmp_path/'dir'; directory.mkdir()
    assert IsFile().execute(None,{'path':str(text_file)}).data['is_file'] is True
    assert IsFile().execute(None,{'path':str(directory)}).data['is_file'] is False
    assert IsDirectory().execute(None,{'path':str(directory)}).data['is_directory'] is True
    assert IsDirectory().execute(None,{'path':str(text_file)}).data['is_directory'] is False

def test_symlink(tmp_path,text_file):
    link=tmp_path/'link.txt'; link.symlink_to(text_file); r=IsSymlink().execute(None,{'path':str(link)}); assert r.success and r.data['is_symlink'] is True

def test_times_are_present(text_file):
    for cls,key in [(GetFileCreatedTime,'created_at'),(GetFileModifiedTime,'modified_at'),(GetFileAccessedTime,'accessed_at')]:
        r=cls().execute(None,{'path':str(text_file)}); assert r.success and r.data[key]

def test_mime_type(text_file):
    r=GetFileMimeType().execute(None,{'path':str(text_file)}); assert r.success; assert r.data['mime_type'].startswith('text/')

def test_accessibility_fields(text_file):
    r=IsFileAccessible().execute(None,{'path':str(text_file)}); assert r.success; assert {'readable','writable','executable'} <= set(r.data)

@pytest.mark.parametrize('cls',[GetFileInfo,GetFileMetadata,GetFileSize,GetFileType,GetFileExtension,GetFileMimeType,GetFilePath,GetFileName,GetFileDirectory,GetFileCreatedTime,GetFileModifiedTime,GetFileAccessedTime,IsFile,IsDirectory,IsSymlink,IsFileAccessible])
def test_missing_path_is_structured_failure(cls,tmp_path):
    r=cls().execute(None,{'path':str(tmp_path/'missing')}); assert r.success is False; assert r.error
