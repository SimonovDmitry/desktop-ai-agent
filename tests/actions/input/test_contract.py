import importlib, inspect, pytest

MODULES={
"keyboard":["PressKey","ReleaseKey","TapKey","HoldKey","ReleaseAllKeys","PressKeys","TypeText","TypeTextSlowly","PasteText","CopySelection","CutSelection","SelectAll","DeleteSelection","GetKeyboardState"],
"mouse":["GetMousePosition","GetMouseButtonState","MoveMouse","MoveMouseRelative","MoveMouseSmoothly","ClickMouse","DoubleClickMouse","TripleClickMouse","MouseDown","MouseUp","DragMouse","DragMouseRelative","ScrollMouse","HorizontalScrollMouse"],
"gestures":["MoveAndClick","MoveAndDoubleClick","DragGesture","SwipeGesture","ClickAndHold","ScrollGesture","MultiClickGesture"],
"hotkeys":["RegisterHotkey","UnregisterHotkey","UnregisterAllHotkeys","GetRegisteredHotkeys","IsHotkeyRegistered","TriggerHotkey"],
"input_state":["GetKeyboardState","GetPressedKeys","IsKeyPressed","GetMouseButtonState","IsMouseButtonPressed","GetInputState","ReleaseAllInput"],
"selection":["SelectAllText","SelectText","SelectWord","SelectLine","SelectToStart","SelectToEnd","ExtendSelection","ClearSelection"],
"clipboard":["CopyText","PasteText","GetSelectedText","ReplaceSelectedText","AppendToClipboard","ClearClipboard"],
"shortcuts":["PressShortcut","ExecuteShortcutSequence","Copy","Paste","Cut","Undo","Redo","Save","SaveAs","Find","Close","Quit","SwitchApplication"],
"automation":["ExecuteInputSequence","ExecuteInputSequenceWithDelay","WaitForInput","WaitForKey","WaitForMouseClick","RepeatInputAction","CancelInputAutomation"]}

@pytest.mark.parametrize("module,classes",MODULES.items())
def test_every_declared_action_imports(module,classes):
    m=importlib.import_module("deskagent.actions.input."+module)
    for name in classes:
        cls=getattr(m,name)
        assert inspect.isclass(cls) and callable(cls.execute)
        assert isinstance(cls.name,str) and cls.name

@pytest.mark.parametrize("module,classes",MODULES.items())
def test_every_action_is_action_subclass(module,classes):
    from deskagent.actions.base import Action
    m=importlib.import_module("deskagent.actions.input."+module)
    for name in classes: assert issubclass(getattr(m,name),Action)

@pytest.mark.parametrize("module,classes",MODULES.items())
def test_schema_contract(module,classes):
    m=importlib.import_module("deskagent.actions.input."+module)
    for name in classes:
        schema=getattr(m,name).parameters_schema
        assert isinstance(schema,dict)
        for key,spec in schema.items():
            assert isinstance(key,str) and isinstance(spec,dict)
            assert "type" in spec and "required" in spec

@pytest.mark.parametrize("module,classes",MODULES.items())
def test_descriptions_present(module,classes):
    m=importlib.import_module("deskagent.actions.input."+module)
    for name in classes:
        assert getattr(m,name).description.strip()
