import base64
import pytest
from deskagent.actions.file.content import ReadFile,ReadTextFile,ReadBinaryFile,WriteFile,WriteTextFile,AppendToFile,PrependToFile,InsertIntoFile,ReplaceInFile,ClearFile,GetFileContentPreview

def test_read_file(text_file):
    r=ReadFile().execute(None,{'path':str(text_file)}); assert r.success; assert r.data['content']=='alpha\nbeta\ngamma\n'; assert r.data['size']==len(text_file.read_bytes()); assert r.data['encoding']

def test_read_text_unicode(tmp_path):
    p=tmp_path/'u.txt'; p.write_text('Привет\nこんにちは\n🙂',encoding='utf-8'); r=ReadTextFile().execute(None,{'path':str(p)}); assert r.success and r.data['content']==p.read_text(encoding='utf-8')

def test_read_binary(binary_file):
    r=ReadBinaryFile().execute(None,{'path':str(binary_file)}); assert r.success; data=r.data['content']; assert (base64.b64decode(data,validate=True) if isinstance(data,str) else bytes(data))==binary_file.read_bytes()

def test_write_file(tmp_path):
    p=tmp_path/'w'; r=WriteFile().execute(None,{'path':str(p),'content':'Hello'}); assert r.success and p.read_text()=='Hello' and r.data['bytes_written']==5

def test_write_text_encoding(tmp_path):
    p=tmp_path/'w'; r=WriteTextFile().execute(None,{'path':str(p),'content':'café','encoding':'utf-8'}); assert r.success and p.read_text(encoding='utf-8')=='café'

def test_append_and_prepend(text_file):
    before=text_file.read_text(); assert AppendToFile().execute(None,{'path':str(text_file),'content':'TAIL'}).success; assert text_file.read_text()==before+'TAIL'; assert PrependToFile().execute(None,{'path':str(text_file),'content':'HEAD'}).success; assert text_file.read_text().startswith('HEAD')

def test_insert(tmp_path):
    p=tmp_path/'x'; p.write_text('abcdef'); r=InsertIntoFile().execute(None,{'path':str(p),'content':'X','position':3}); assert r.success and p.read_text()=='abcXdef'

def test_replace_all(tmp_path):
    p=tmp_path/'x'; p.write_text('localhost localhost localhost'); r=ReplaceInFile().execute(None,{'path':str(p),'old':'localhost','new':'127.0.0.1'}); assert r.success and p.read_text().count('127.0.0.1')==3 and r.data['replacements']==3

def test_clear_keeps_file(text_file):
    r=ClearFile().execute(None,{'path':str(text_file)}); assert r.success and text_file.exists() and text_file.read_bytes()==b''

@pytest.mark.parametrize('limit',[0,1,5,10,100])
def test_preview_limit(text_file,limit):
    r=GetFileContentPreview().execute(None,{'path':str(text_file),'max_length':limit}); assert r.success; preview=r.data.get('content',r.data.get('preview')); assert preview is not None and len(preview)<=limit
