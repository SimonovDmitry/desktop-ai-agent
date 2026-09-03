import pytest
from deskagent.actions.input.hotkeys import (
    RegisterHotkey,UnregisterHotkey,UnregisterAllHotkeys,
    GetRegisteredHotkeys,IsHotkeyRegistered,TriggerHotkey,
)

def test_register(ctx):
    r=RegisterHotkey().execute(ctx,{"hotkey":"cmd+shift+d","action":"dashboard"})
    assert r.success and r.data=={"hotkey":"cmd+shift+d","registered":True}
    ctx.services.system.keyboard.register_hotkey.assert_called_once_with("cmd+shift+d","dashboard")

@pytest.mark.parametrize("p",[{},{"hotkey":"cmd+c"},{"action":"copy"},{"hotkey":"" ,"action":"copy"}])
def test_register_requires_both(ctx,p):
    r=RegisterHotkey().execute(ctx,p); assert not r.success and r.error_code=="MISSING_PARAM"

def test_unregister(ctx):
    r=UnregisterHotkey().execute(ctx,{"hotkey":"cmd+c"})
    assert r.success and r.data["unregistered"]
    ctx.services.system.keyboard.unregister_hotkey.assert_called_once_with("cmd+c")

def test_unregister_all(ctx):
    ctx.services.system.keyboard.unregister_all_hotkeys.return_value=3
    r=UnregisterAllHotkeys().execute(ctx,{})
    assert r.success and r.data=={"removed":3}

def test_get_registered(ctx):
    value={"cmd+c":"copy"}
    ctx.services.system.keyboard.get_registered_hotkeys.return_value=value
    r=GetRegisteredHotkeys().execute(ctx,{})
    assert r.success and r.data=={"hotkeys":value}

@pytest.mark.parametrize("value",[True,False])
def test_is_registered(ctx,value):
    ctx.services.system.keyboard.is_hotkey_registered.return_value=value
    r=IsHotkeyRegistered().execute(ctx,{"hotkey":"cmd+c"})
    assert r.success and r.data=={"hotkey":"cmd+c","registered":value}

def test_trigger(ctx):
    r=TriggerHotkey().execute(ctx,{"hotkey":"cmd+shift+d"})
    assert r.success and r.data["triggered"]
    ctx.services.system.keyboard.trigger_hotkey.assert_called_once_with("cmd+shift+d")

def test_trigger_error_code(ctx):
    ctx.services.system.keyboard.trigger_hotkey.side_effect=LookupError("missing")
    r=TriggerHotkey().execute(ctx,{"hotkey":"cmd+x"})
    assert not r.success and r.error_code=="NOT_FOUND"
