from unittest.mock import patch
import pytest
from deskagent.actions.input.gestures import (
    MoveAndClick, MoveAndDoubleClick, DragGesture, SwipeGesture,
    ClickAndHold, ScrollGesture, MultiClickGesture,
)

def test_move_and_click(ctx):
    with patch("deskagent.actions.input.gestures.time.sleep") as s:
        r=MoveAndClick().execute(ctx,{"x":10,"y":20,"button":"right"})
    assert r.success and r.data["clicked"]
    ctx.services.system.mouse.move_mouse.assert_called_once_with(10,20)
    ctx.services.system.mouse.click.assert_called_once_with("right")
    s.assert_called_once_with(0.05)

def test_move_and_click_missing(ctx):
    r=MoveAndClick().execute(ctx,{"x":1})
    assert not r.success and r.error_code=="MISSING_PARAM"

def test_move_and_double_click(ctx):
    with patch("deskagent.actions.input.gestures.time.sleep"):
        r=MoveAndDoubleClick().execute(ctx,{"x":2,"y":3})
    assert r.success and r.data["click_count"]==2
    ctx.services.system.mouse.double_click.assert_called_once_with("left")

@pytest.mark.parametrize("custom", [False,True])
def test_drag_gesture(ctx,custom):
    p={"start_x":1,"start_y":2,"end_x":3,"end_y":4}
    if custom: p.update(button="right",duration=1.2)
    r=DragGesture().execute(ctx,p)
    assert r.success and r.data=={"gesture":"drag","completed":True}
    expected=(1,2,3,4,"right",1.2) if custom else (1,2,3,4,"left",0.5)
    ctx.services.system.mouse.drag_mouse.assert_called_once_with(*expected)

def test_swipe(ctx):
    r=SwipeGesture().execute(ctx,{"start_x":1,"start_y":2,"end_x":30,"end_y":40,"duration":.8})
    assert r.success
    assert ctx.services.system.mouse.move_smooth.call_args_list==[
        ((1,2,.05),),((30,40,.8),)]

def test_click_and_hold(ctx):
    with patch("deskagent.actions.input.gestures.time.sleep") as s:
        r=ClickAndHold().execute(ctx,{"button":"left","duration":.7})
    assert r.success
    ctx.services.system.mouse.mouse_down.assert_called_once_with("left")
    ctx.services.system.mouse.mouse_up.assert_called_once_with("left")
    s.assert_called_once_with(.7)

@pytest.mark.parametrize("direction,method,value",[
    ("up","scroll_mouse",5),("down","scroll_mouse",-5),
    ("left","scroll_horizontal",-5),("right","scroll_horizontal",5)])
def test_scroll_direction(ctx,direction,method,value):
    r=ScrollGesture().execute(ctx,{"direction":direction,"amount":5})
    assert r.success and r.data["direction"]==direction
    getattr(ctx.services.system.mouse,method).assert_called_once_with(value)

def test_multi_click(ctx):
    with patch("deskagent.actions.input.gestures.time.sleep") as s:
        r=MultiClickGesture().execute(ctx,{"count":4,"button":"middle","interval":.2})
    assert r.success and r.data=={"count":4,"completed":True}
    assert ctx.services.system.mouse.click.call_count==4
    assert s.call_count==4
