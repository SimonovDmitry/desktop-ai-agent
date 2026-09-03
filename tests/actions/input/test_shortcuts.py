from unittest.mock import patch
import pytest
from deskagent.actions.input.shortcuts import (
    PressShortcut,ExecuteShortcutSequence,Copy,Paste,Cut,Undo,Redo,
    Save,SaveAs,Find,Close,Quit,SwitchApplication)

def test_press_shortcut(ctx):
    r=PressShortcut().execute(ctx,{"shortcut":"cmd+shift+s"})
    assert r.success and r.data=={"shortcut":"cmd+shift+s","executed":True}
    ctx.services.system.keyboard.press_shortcut.assert_called_once_with("cmd+shift+s")

@pytest.mark.parametrize("p",[{},{"shortcut":""},{"shortcut":None}])
def test_press_shortcut_missing(ctx,p):
    r=PressShortcut().execute(ctx,p); assert not r.success and r.error_code=="MISSING_PARAM"

def test_sequence(ctx):
    with patch("deskagent.actions.input.shortcuts.time.sleep") as sleep:
        r=ExecuteShortcutSequence().execute(ctx,{"shortcuts":["cmd+a","cmd+c"],"delay":.25})
    assert r.success and r.data=={"executed":2,"completed":True}
    assert sleep.call_count==2
    assert [c.args for c in ctx.services.system.keyboard.press_shortcut.call_args_list]==[("cmd+a",),("cmd+c",)]

@pytest.mark.parametrize("bad",[None,"cmd+c",("cmd+c",),{"x":1}])
def test_sequence_requires_list(ctx,bad):
    r=ExecuteShortcutSequence().execute(ctx,{"shortcuts":bad})
    assert not r.success and r.error_code=="INVALID_INPUT"

@pytest.mark.parametrize("cls,method,key",[
    (Copy,"copy","copied"),(Paste,"paste","pasted"),(Cut,"cut","cut"),
    (Undo,"undo","undone"),(Redo,"redo","redone"),(Save,"save","saved"),
    (Close,"close","closed"),(Quit,"quit","quit")])
def test_simple_shortcuts(ctx,cls,method,key):
    r=cls().execute(ctx,{})
    assert r.success and r.data=={key:True}
    getattr(ctx.services.system.keyboard,method).assert_called_once_with()

def test_save_as(ctx):
    r=SaveAs().execute(ctx,{"path":"/tmp/x.txt"})
    assert r.success
    ctx.services.system.keyboard.save_as.assert_called_once_with("/tmp/x.txt")

def test_save_as_default(ctx):
    r=SaveAs().execute(ctx,{})
    assert r.success
    ctx.services.system.keyboard.save_as.assert_called_once_with(None)

def test_find(ctx):
    with patch("deskagent.actions.input.shortcuts.time.sleep") as sleep:
        r=Find().execute(ctx,{"text":"needle"})
    assert r.success and r.data=={"search":"needle","executed":True}
    ctx.services.system.keyboard.press_shortcut.assert_called_once_with("cmd+f")
    ctx.services.system.keyboard.type.assert_called_once_with("needle")
    sleep.assert_called_once_with(.2)

def test_switch_application(ctx):
    r=SwitchApplication().execute(ctx,{"application":"Safari"})
    assert r.success
    ctx.services.application.focus.activate.assert_called_once_with("Safari")
