from unittest.mock import patch
import pytest
from deskagent.actions.input.input_state import (
    GetKeyboardState,GetPressedKeys,IsKeyPressed,GetMouseButtonState,
    IsMouseButtonPressed,GetInputState,ReleaseAllInput)
from deskagent.actions.input.automation import (
    ExecuteInputSequence,ExecuteInputSequenceWithDelay,WaitForInput,
    WaitForKey,WaitForMouseClick,RepeatInputAction,CancelInputAutomation)

def test_pressed_keys(ctx):
    ctx.services.system.keyboard.get_pressed_keys.return_value=["a","shift"]
    r=GetPressedKeys().execute(ctx,{})
    assert r.success and r.data=={"keys":["a","shift"],"count":2}

def test_key_pressed(ctx):
    ctx.services.system.keyboard.is_pressed.return_value=True
    r=IsKeyPressed().execute(ctx,{"key":"shift"})
    assert r.success and r.data=={"key":"shift","pressed":True}

def test_mouse_button_pressed(ctx):
    ctx.services.system.mouse.is_pressed.return_value=False
    r=IsMouseButtonPressed().execute(ctx,{"button":"right"})
    assert r.success and r.data=={"button":"right","pressed":False}

def test_input_state(ctx):
    ctx.services.system.keyboard.get_state.return_value={"pressed_keys":["cmd"],"extra":1}
    ctx.services.system.mouse.get_cursor_position.return_value=(5,6)
    ctx.services.system.mouse.get_button_state.return_value={"left":True}
    r=GetInputState().execute(ctx,{})
    assert r.success and r.data=={"keyboard":{"pressed_keys":["cmd"]},
                                   "mouse":{"position":(5,6),"buttons":{"left":True}}}

def test_release_all_input(ctx):
    r=ReleaseAllInput().execute(ctx,{})
    assert r.success
    ctx.services.system.keyboard.release_all.assert_called_once_with()
    ctx.services.system.mouse.release_all.assert_called_once_with()

def test_release_all_input_panic_error(ctx):
    ctx.services.system.mouse.release_all.side_effect=RuntimeError("mouse")
    r=ReleaseAllInput().execute(ctx,{})
    assert not r.success and r.error_code=="PANIC_RESET_FAILED"

def test_sequence(ctx):
    actions=[{"type":"move_mouse","x":1,"y":2},{"type":"click","button":"right"},
             {"type":"type_text","text":"hi"},{"type":"press_key","key":"shift"},
             {"type":"tap_key","key":"enter"}]
    r=ExecuteInputSequence().execute(ctx,{"actions":actions})
    assert r.success and r.data=={"completed":True,"executed":5,"failed":0}
    ctx.services.system.mouse.move_mouse.assert_called_once_with(1,2)
    ctx.services.system.mouse.click.assert_called_once_with("right")
    ctx.services.system.keyboard.type.assert_called_once_with("hi")

def test_sequence_failure_reports_completed_before_failure(ctx):
    ctx.services.system.mouse.click.side_effect=RuntimeError("bad click")
    r=ExecuteInputSequence().execute(ctx,{"actions":[
        {"type":"move_mouse","x":1,"y":2},{"type":"click"},{"type":"type_text","text":"no"}]})
    assert not r.success and r.data=={"executed":1}

def test_sequence_delay(ctx):
    with patch("deskagent.actions.input.automation.time.sleep") as sleep:
        r=ExecuteInputSequenceWithDelay().execute(ctx,{"actions":[{},{}],"delay":.2})
    assert r.success and r.data=={"executed":2} and sleep.call_count==2

@pytest.mark.parametrize("input_type",["mouse_click","key_press","any"])
def test_wait_for_input(ctx,input_type):
    ctx.services.system.input_monitor.wait_for_event.return_value=True
    r=WaitForInput().execute(ctx,{"input_type":input_type,"timeout":4})
    assert r.success and r.data=={"triggered":True,"input_type":input_type}

def test_wait_for_key(ctx):
    r=WaitForKey().execute(ctx,{"key":"enter","timeout":3})
    assert r.success and r.data=={"key":"enter","pressed":True}
    ctx.services.system.keyboard.wait_for_key.assert_called_once_with("enter",3)

def test_wait_for_mouse_click(ctx):
    ctx.services.system.mouse.wait_for_click.return_value=(10,20)
    r=WaitForMouseClick().execute(ctx,{"button":"right","timeout":5})
    assert r.success and r.data=={"button":"right","clicked_at":(10,20)}

def test_repeat(ctx):
    with patch("deskagent.actions.input.automation.time.sleep") as sleep:
        r=RepeatInputAction().execute(ctx,{"action":{"type":"click"},"count":3,"interval":.1})
    assert r.success and r.data=={"executed":3,"completed":True}
    assert sleep.call_count==3

def test_cancel(ctx):
    r=CancelInputAutomation().execute(ctx,{"automation_id":"job-7"})
    assert r.success
    ctx.services.system.keyboard.stop_automation.assert_called_once_with("job-7")
    ctx.services.system.mouse.stop_automation.assert_called_once_with("job-7")
