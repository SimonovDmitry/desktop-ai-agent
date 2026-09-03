import pytest
from deskagent.actions.input.keyboard import (
    PressKey, ReleaseKey, TapKey, HoldKey, ReleaseAllKeys, PressKeys,
    TypeText, TypeTextSlowly, PasteText, CopySelection, CutSelection,
    SelectAll, DeleteSelection, GetKeyboardState,
)

@pytest.mark.parametrize("cls,method,data,params", [
    (PressKey,"press",{"key":"a","pressed":True},{"key":"a"}),
    (ReleaseKey,"release",{"key":"a","released":True},{"key":"a"}),
    (ReleaseAllKeys,"release_all",{"released":True},{}),
    (CopySelection,"copy",{"copied":True},{}),
    (CutSelection,"cut",{"cut":True},{}),
    (SelectAll,"select_all",{"selected":True},{}),
    (DeleteSelection,"delete",{"deleted":True},{}),
])
def test_basic_keyboard_actions(ctx, cls, method, data, params):
    r=cls().execute(ctx,params)
    assert r.success and r.data==data
    getattr(ctx.services.system.keyboard,method).assert_called_once_with(
        *([params["key"]] if "key" in params else []))

@pytest.mark.parametrize("cls,params,code", [
    (PressKey,{}, "MISSING_PARAM"), (PressKey,{"key":""},"MISSING_PARAM"),
    (ReleaseKey,{}, "MISSING_PARAM"), (TapKey,{}, "MISSING_PARAM"),
    (HoldKey,{"key":"shift"},"MISSING_PARAM"), (HoldKey,{"duration":1},"MISSING_PARAM"),
])
def test_keyboard_required_params(ctx,cls,params,code):
    r=cls().execute(ctx,params); assert not r.success and r.error_code==code

def test_tap_key_default_and_custom_duration(ctx):
    assert TapKey().execute(ctx,{"key":"enter"}).success
    ctx.services.system.keyboard.tap.assert_called_once_with("enter",0.05)
    ctx.services.system.keyboard.reset_mock()
    assert TapKey().execute(ctx,{"key":"enter","duration":0.7}).success
    ctx.services.system.keyboard.tap.assert_called_once_with("enter",0.7)

def test_hold_key(ctx):
    r=HoldKey().execute(ctx,{"key":"shift","duration":1.5})
    assert r.success and r.data=={"key":"shift","duration":1.5,"completed":True}
    ctx.services.system.keyboard.hold.assert_called_once_with("shift",1.5)

@pytest.mark.parametrize("keys", [[],["a"],["cmd","shift","s"],["é","😀"]])
def test_press_keys(ctx,keys):
    r=PressKeys().execute(ctx,{"keys":keys})
    assert r.success and r.data=={"keys":keys,"count":len(keys)}
    ctx.services.system.keyboard.press_sequence.assert_called_once_with(keys)

@pytest.mark.parametrize("bad", [None,"abc",("a","b"),{"a":1},123])
def test_press_keys_rejects_non_list(ctx,bad):
    r=PressKeys().execute(ctx,{"keys":bad})
    assert not r.success and r.error_code=="INVALID_INPUT"
    ctx.services.system.keyboard.press_sequence.assert_not_called()

@pytest.mark.parametrize("text", ["","hello","a\nb\t😀","Привет 世界"])
def test_type_text(ctx,text):
    r=TypeText().execute(ctx,{"text":text})
    assert r.success and r.data=={"text_length":len(text),"typed":True}
    ctx.services.system.keyboard.type.assert_called_once_with(text)

def test_type_text_missing(ctx):
    r=TypeText().execute(ctx,{})
    assert not r.success and r.error_code=="MISSING_PARAM"

@pytest.mark.parametrize("interval",[0,0.01,0.05,1.2])
def test_type_text_slowly(ctx,interval):
    r=TypeTextSlowly().execute(ctx,{"text":"abc","interval":interval})
    assert r.success and r.data["interval"]==interval
    ctx.services.system.keyboard.type.assert_called_once_with("abc",interval=interval)

def test_paste_text(ctx):
    text="long\ntext 😀"
    r=PasteText().execute(ctx,{"text":text})
    assert r.success and r.data=={"text_length":len(text),"pasted":True}
    ctx.services.system.clipboard.set_clipboard.assert_called_once_with(text)
    ctx.services.system.keyboard.paste.assert_called_once_with()

def test_paste_text_missing(ctx):
    r=PasteText().execute(ctx,{})
    assert not r.success
    ctx.services.system.keyboard.paste.assert_not_called()

def test_keyboard_state(ctx):
    state={"pressed_keys":["cmd","shift"]}
    ctx.services.system.keyboard.get_state.return_value=state
    r=GetKeyboardState().execute(ctx,{})
    assert r.success and r.data is state

@pytest.mark.parametrize("cls,method", [
    (PressKey,"press"),(ReleaseKey,"release"),(TapKey,"tap"),(HoldKey,"hold"),
    (ReleaseAllKeys,"release_all"),(PressKeys,"press_sequence"),
    (TypeText,"type"),(TypeTextSlowly,"type"),(PasteText,"paste"),
    (CopySelection,"copy"),(CutSelection,"cut"),(SelectAll,"select_all"),
    (DeleteSelection,"delete"),(GetKeyboardState,"get_state")])
def test_keyboard_exceptions_are_results(ctx,cls,method):
    getattr(ctx.services.system.keyboard,method).side_effect=RuntimeError("boom")
    params={"key":"a"} if cls in (PressKey,ReleaseKey,TapKey) else {}
    if cls is HoldKey: params={"key":"a","duration":1}
    if cls is PressKeys: params={"keys":["a"]}
    if cls in (TypeText,TypeTextSlowly): params={"text":"a"}
    if cls is PasteText: params={"text":"a"}
    r=cls().execute(ctx,params)
    assert not r.success and r.error=="boom"

@pytest.mark.parametrize("cls,name", [
    (PressKey,"press_key"),(ReleaseKey,"release_key"),(TapKey,"tap_key"),
    (HoldKey,"hold_key"),(ReleaseAllKeys,"release_all_keys"),(PressKeys,"press_keys"),
    (TypeText,"type_text"),(TypeTextSlowly,"type_text_slowly"),
    (PasteText,"paste_text"),(CopySelection,"copy_selection"),
    (CutSelection,"cut_selection"),(SelectAll,"select_all"),
    (DeleteSelection,"delete_selection"),(GetKeyboardState,"get_keyboard_state")])
def test_keyboard_names(cls,name): assert cls.name==name
