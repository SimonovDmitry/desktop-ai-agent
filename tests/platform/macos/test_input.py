import importlib
import inspect
import platform

import pytest

from deskagent.platform.base.input import (
    InputAutomation,
    InputClipboard,
    InputGestures,
    InputHotkeys,
    InputKeyboard,
    InputMouse,
    InputSelection,
    InputShortcuts,
    InputState,
)


if platform.system() != "Darwin":
    pytest.skip("macOS-only tests", allow_module_level=True)


macos_input = importlib.import_module("deskagent.platform.macos.input")

INTERFACES = (
    InputKeyboard,
    InputMouse,
    InputShortcuts,
    InputHotkeys,
    InputClipboard,
    InputSelection,
    InputState,
    InputGestures,
    InputAutomation,
)


def _implementations_for(interface):
    implementations = []
    for name, obj in vars(macos_input).items():
        if not inspect.isclass(obj):
            continue
        if obj is interface:
            continue
        if issubclass(obj, interface):
            implementations.append(obj)
    return implementations


@pytest.mark.parametrize("interface", INTERFACES)
def test_macos_provides_a_concrete_implementation_for_every_input_interface(interface):
    implementations = _implementations_for(interface)
    assert implementations, f"No macOS implementation found for {interface.__name__}"
    assert all(not inspect.isabstract(cls) for cls in implementations)


@pytest.mark.parametrize("interface", INTERFACES)
def test_macos_implementations_override_every_abstract_method(interface):
    implementations = _implementations_for(interface)
    assert implementations
    for implementation in implementations:
        for method_name in interface.__abstractmethods__:
            member = inspect.getattr_static(implementation, method_name, None)
            assert member is not None, f"{implementation.__name__}.{method_name} is missing"
            assert not getattr(member, "__isabstractmethod__", False), (
                f"{implementation.__name__}.{method_name} remains abstract"
            )


@pytest.mark.parametrize("interface", INTERFACES)
def test_macos_method_signatures_match_the_base_contract(interface):
    implementations = _implementations_for(interface)
    assert implementations
    for implementation in implementations:
        for method_name in interface.__abstractmethods__:
            base_sig = inspect.signature(getattr(interface, method_name))
            impl_sig = inspect.signature(getattr(implementation, method_name))
            assert list(impl_sig.parameters) == list(base_sig.parameters), (
                f"{implementation.__name__}.{method_name} changed parameter names"
            )
            for parameter_name, base_parameter in base_sig.parameters.items():
                impl_parameter = impl_sig.parameters[parameter_name]
                assert impl_parameter.kind is base_parameter.kind, (
                    f"{implementation.__name__}.{method_name}.{parameter_name} changed kind"
                )
                assert impl_parameter.default == base_parameter.default, (
                    f"{implementation.__name__}.{method_name}.{parameter_name} changed default"
                )


def test_macos_input_module_does_not_expose_unrelated_abstract_input_classes():
    concrete_classes = [
        obj for obj in vars(macos_input).values()
        if inspect.isclass(obj)
        and any(issubclass(obj, interface) for interface in INTERFACES)
        and obj not in INTERFACES
    ]
    assert concrete_classes
    assert all(not inspect.isabstract(cls) for cls in concrete_classes)


def test_every_concrete_macos_input_class_has_its_own_implementation():
    for interface in INTERFACES:
        for implementation in _implementations_for(interface):
            for method_name in interface.__abstractmethods__:
                # getattr_static lets us distinguish an actual override from an inherited abstract method.
                member = inspect.getattr_static(implementation, method_name)
                owner = getattr(member, "__qualname__", "")
                assert owner.startswith(implementation.__name__ + "."), (
                    f"{implementation.__name__}.{method_name} is only inherited"
                )


def test_macos_input_module_has_no_duplicate_concrete_class_names():
    names = [
        name for name, obj in vars(macos_input).items()
        if inspect.isclass(obj)
        and any(issubclass(obj, interface) for interface in INTERFACES)
        and obj not in INTERFACES
    ]
    assert len(names) == len(set(names))
