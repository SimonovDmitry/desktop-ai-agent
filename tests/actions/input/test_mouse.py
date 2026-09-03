import pytest
from deskagent.actions.input.mouse import (
    GetMousePosition, GetMouseButtonState, MoveMouse, MoveMouseRelative,
    MoveMouseSmoothly, ClickMouse, DoubleClickMouse, TripleClickMouse,
    MouseDown, MouseUp, DragMouse, DragMouseRelative, ScrollMouse,
    HorizontalScrollMouse,
)

def test_mouse_state(ctx):
    ctx.services.system.mouse.get_cursor_position.return_value=(10,20)
    assert GetMousePosition().execute(ctx,{}).data==(10,20)
    state={"left":True,"right":False,"middle":False}
    ctx.services.system.mouse.get_button_state.return_value=state
    assert GetMouseButtonState().execute(ctx,{}).data is state

@pytest.mark.parametrize("x,y",[(0,0),(-10,5),(1920,1080)])
def test_move_mouse(ctx,x,y):
    r=MoveMouse().execute(ctx,{"x":x,"y":y})
    assert r.success and r.data=={"x":x,"y":y,"moved":True}
    ctx.services.system.mouse.move_mouse.assert_called_once_with(x,y)

@pytest.mark.parametrize("p",[{},{"x":1},{"y":2}])
def test_move_mouse_requires_xy(ctx,p):
    r=MoveMouse().execute(ctx,p); assert not r.success and r.error_code=="MISSING_PARAM"

def test_relative_move(ctx):
    ctx.services.system.mouse.move_relative.return_value=(30,40)
    r=MoveMouseRelative().execute(ctx,{"dx":10,"dy":-5})
    assert r.success and r.data["new_pos"]==(30,40)
    ctx.services.system.mouse.move_relative.assert_called_once_with(10,-5)

def test_smooth_move_default_and_custom(ctx):
    assert MoveMouseSmoothly().execute(ctx,{"x":5,"y":6}).success
    ctx.services.system.mouse.move_smooth.assert_called_once_with(5,6,0.5)
    ctx.services.system.mouse.reset_mock()
    assert MoveMouseSmoothly().execute(ctx,{"x":5,"y":6,"duration":1.1}).success
    ctx.services.system.mouse.move_smooth.assert_called_once_with(5,6,1.1)

@pytest.mark.parametrize("cls,method,button",[
    (ClickMouse,"click","left"),(DoubleClickMouse,"double_click","right"),
    (TripleClickMouse,"triple_click","middle"),(MouseDown,"mouse_down","left"),
    (MouseUp,"mouse_up","right")])
def test_button_actions(ctx,cls,method,button):
    r=cls().execute(ctx,{"button":button})
    assert r.success
    getattr(ctx.services.system.mouse,method).assert_called_once_with(button)

@pytest.mark.parametrize("cls,method",[(ClickMouse,"click"),(DoubleClickMouse,"double_click"),(TripleClickMouse,"triple_click")])
def test_click_defaults(ctx,cls,method):
    r=cls().execute(ctx,{})
    assert r.success
    getattr(ctx.services.system.mouse,method).assert_called_once_with("left")

def test_drag_mouse(ctx):
    r=DragMouse().execute(ctx,{"x1":1,"y1":2,"x2":30,"y2":40,"button":"right"})
    assert r.success
    ctx.services.system.mouse.drag_mouse.assert_called_once_with(1,2,30,40,"right")

def test_drag_mouse_default(ctx):
    r=DragMouse().execute(ctx,{"x1":1,"y1":2,"x2":3,"y2":4})
    assert r.success
    ctx.services.system.mouse.drag_mouse.assert_called_once_with(1,2,3,4)

def test_drag_mouse_missing(ctx):
    r=DragMouse().execute(ctx,{"x1":1,"y1":2,"x2":3})
    assert not r.success and r.error_code=="MISSING_PARAM"

def test_drag_relative(ctx):
    r=DragMouseRelative().execute(ctx,{"dx":-2,"dy":5,"button":"middle","duration":0.8})
    assert r.success
    ctx.services.system.mouse.drag_mouse_relative.assert_called_once_with(-2,5,"middle",0.8)

@pytest.mark.parametrize("cls,method,value",[
    (ScrollMouse,"scroll_mouse",-5),(ScrollMouse,"scroll_mouse",0),
    (HorizontalScrollMouse,"scroll_horizontal",7)])
def test_scroll_actions(ctx,cls,method,value):
    r=cls().execute(ctx,{"clicks":value})
    assert r.success
    getattr(ctx.services.system.mouse,method).assert_called_once_with(value)

def test_scroll_missing(ctx):
    r=ScrollMouse().execute(ctx,{})
    assert not r.success and r.error_code=="MISSING_PARAM"

def test_mouse_error_is_result(ctx):
    ctx.services.system.mouse.click.side_effect=OSError("unavailable")
    r=ClickMouse().execute(ctx,{"button":"left"})
    assert not r.success and r.error=="unavailable"
