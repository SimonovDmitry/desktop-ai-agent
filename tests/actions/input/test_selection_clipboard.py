from unittest.mock import patch
import pytest
from deskagent.actions.input.selection import (
    SelectAllText,SelectText,SelectWord,SelectLine,SelectToStart,
    SelectToEnd,ExtendSelection,ClearSelection)
from deskagent.actions.input.clipboard import (
    CopyText,PasteText,GetSelectedText,ReplaceSelectedText,
    AppendToClipboard,ClearClipboard)

@pytest.mark.parametrize("cls,method,data",[
    (SelectAllText,"select_all",{"selected":True}),
    (SelectWord,"select_word",{"selected":True,"unit":"word"}),
    (SelectLine,"select_line",{"selected":True,"unit":"line"}),
    (ClearSelection,"clear_selection",{"cleared":True})])
def test_selection_simple(ctx,cls,method,data):
    r=cls().execute(ctx,{})
    assert r.success and r.data==data
    getattr(ctx.services.system.keyboard,method).assert_called_once_with()

@pytest.mark.parametrize("start,end",[(0,0),(0,10),(-5,20),(100,25)])
def test_select_range(ctx,start,end):
    r=SelectText().execute(ctx,{"start":start,"end":end})
    assert r.success and r.data=={"start":start,"end":end,"selected":True}
    ctx.services.system.keyboard.select_range.assert_called_once_with(start,end)

@pytest.mark.parametrize("p",[{},{"start":1},{"end":2}])
def test_select_range_missing(ctx,p):
    r=SelectText().execute(ctx,p); assert not r.success and r.error_code=="MISSING_PARAM"

@pytest.mark.parametrize("scope",[None,"line","document"])
def test_select_to_start(ctx,scope):
    p={} if scope is None else {"scope":scope}
    r=SelectToStart().execute(ctx,p)
    assert r.success
    ctx.services.system.keyboard.select_to_start.assert_called_once_with("line" if scope is None else scope)

@pytest.mark.parametrize("scope",[None,"line","document"])
def test_select_to_end(ctx,scope):
    p={} if scope is None else {"scope":scope}
    r=SelectToEnd().execute(ctx,p)
    assert r.success
    ctx.services.system.keyboard.select_to_end.assert_called_once_with("line" if scope is None else scope)

@pytest.mark.parametrize("direction,amount,unit",[("up",1,"character"),("down",3,"word"),("left",5,"line"),("right",2,"character")])
def test_extend_selection(ctx,direction,amount,unit):
    r=ExtendSelection().execute(ctx,{"direction":direction,"amount":amount,"unit":unit})
    assert r.success
    ctx.services.system.keyboard.extend_selection.assert_called_once_with(direction,amount,unit)

def test_extend_selection_missing(ctx):
    r=ExtendSelection().execute(ctx,{"direction":"left","amount":1})
    assert not r.success and r.error_code=="MISSING_PARAM"

def test_copy_text(ctx):
    ctx.services.system.clipboard.get_clipboard.return_value="copied"
    with patch("deskagent.actions.input.clipboard.time.sleep"):
        r=CopyText().execute(ctx,{})
    assert r.success and r.data=={"copied":True,"text":"copied"}
    ctx.services.system.keyboard.copy.assert_called_once_with()

def test_paste_text(ctx):
    r=PasteText().execute(ctx,{"text":"hello"})
    assert r.success and r.data=={"pasted":True,"text_length":5}
    ctx.services.system.clipboard.set_clipboard.assert_called_once_with("hello")
    ctx.services.system.keyboard.paste.assert_called_once_with()

def test_get_selected_text(ctx):
    ctx.services.system.clipboard.get_clipboard.side_effect=["old","selected"]
    with patch("deskagent.actions.input.clipboard.time.sleep"):
        r=GetSelectedText().execute(ctx,{})
    assert r.success and r.data["text"]=="selected"
    assert ctx.services.system.clipboard.get_clipboard.call_count==2

def test_replace_selected_text(ctx):
    r=ReplaceSelectedText().execute(ctx,{"text":"new"})
    assert r.success and r.data=={"replaced":True,"text_length":3}
    ctx.services.system.clipboard.set_clipboard.assert_called_once_with("new")
    ctx.services.system.keyboard.paste.assert_called_once_with()

@pytest.mark.parametrize("current,text,sep,expected",[
    ("a","b","\n","a\nb"),("a","b"," | ","a | b"),
    ("","b","\n","b"),(None,"b","\n","b"),("a","","\n","a\n")])
def test_append_clipboard(ctx,current,text,sep,expected):
    ctx.services.system.clipboard.get_clipboard.return_value=current
    r=AppendToClipboard().execute(ctx,{"text":text,"separator":sep})
    assert r.success and r.data["text_length"]==len(expected)
    ctx.services.system.clipboard.set_clipboard.assert_called_once_with(expected)

def test_clear_clipboard(ctx):
    r=ClearClipboard().execute(ctx,{})
    assert r.success and r.data=={"cleared":True}
    ctx.services.system.clipboard.clean_clipboard.assert_called_once_with()
