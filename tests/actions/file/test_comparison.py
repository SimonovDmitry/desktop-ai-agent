import hashlib
import pytest
from deskagent.actions.file.comparison import CompareFiles,CompareFileContents,GetFileHash,VerifyFileHash,FindDifferences,AreFilesIdentical

def test_hash(text_file):
    expected=hashlib.sha256(text_file.read_bytes()).hexdigest(); r=GetFileHash().execute(None,{'path':str(text_file),'algorithm':'sha256'}); assert r.success and r.data['hash']==expected
@pytest.mark.parametrize('alg',['md5','sha1','sha256','sha512'])
def test_hash_algorithms(text_file,alg):
    r=GetFileHash().execute(None,{'path':str(text_file),'algorithm':alg}); assert r.success and len(r.data['hash'])==hashlib.new(alg).digest_size*2

def test_verify(text_file):
    d=hashlib.sha256(text_file.read_bytes()).hexdigest(); r=VerifyFileHash().execute(None,{'path':str(text_file),'algorithm':'sha256','expected_hash':d}); assert r.success and r.data['valid'] is True; r=VerifyFileHash().execute(None,{'path':str(text_file),'algorithm':'sha256','expected_hash':'0'*64}); assert r.success and r.data['valid'] is False

def test_compare_identical(tmp_path):
    a=tmp_path/'a'; b=tmp_path/'b'; a.write_text('same'); b.write_text('same'); r=CompareFiles().execute(None,{'file1':str(a),'file2':str(b)}); assert r.success and r.data['identical'] is True and r.data['hash_equal'] is True

def test_compare_same_size_different(tmp_path):
    a=tmp_path/'a'; b=tmp_path/'b'; a.write_text('AAAA'); b.write_text('BBBB'); r=CompareFiles().execute(None,{'file1':str(a),'file2':str(b)}); assert r.success and r.data['identical'] is False and r.data['size_equal'] is True

def test_text_difference(tmp_path):
    a=tmp_path/'a'; b=tmp_path/'b'; a.write_text('one\ntwo\n'); b.write_text('one\nTWO\n'); r=CompareFileContents().execute(None,{'file1':str(a),'file2':str(b)}); assert r.success and not r.data['identical'] and r.data['differences']

def test_find_differences(tmp_path):
    a=tmp_path/'a'; b=tmp_path/'b'; a.write_text('a\n'); b.write_text('b\n'); r=FindDifferences().execute(None,{'file1':str(a),'file2':str(b)}); assert r.success and r.data

def test_identical_boolean(tmp_path):
    a=tmp_path/'a'; b=tmp_path/'b'; a.write_text('x'); b.write_text('x'); r=AreFilesIdentical().execute(None,{'file1':str(a),'file2':str(b)}); assert r.success and isinstance(r.data['identical'],bool)
