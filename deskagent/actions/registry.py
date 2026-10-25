import importlib
import inspect
import pkgutil
from importlib import metadata
from types import ModuleType

from deskagent.actions.base import Action, ActionRegistry
from deskagent.actions.contracts import ActionContractValidator

DEFAULT_PACKAGES = ("deskagent.actions",)
PLUGIN_GROUP = "deskagent.actions"
SKIP_MODULES = {"base", "contracts", "executor", "registry", "result", "types"}


def discover_actions(packages=DEFAULT_PACKAGES, include_plugins=True):
    actions = []
    for package_name in packages:
        package = importlib.import_module(package_name)
        actions.extend(_module_actions(package))
        if hasattr(package, "__path__"):
            for info in pkgutil.walk_packages(package.__path__, f"{package.__name__}."):
                if not info.ispkg and info.name.rsplit(".", 1)[-1] not in SKIP_MODULES:
                    actions.extend(_module_actions(importlib.import_module(info.name)))
    if include_plugins:
        for entry_point in metadata.entry_points().select(group=PLUGIN_GROUP):
            actions.extend(_plugin_actions(entry_point.load()))
    return actions


def create_action_registry(packages=DEFAULT_PACKAGES, include_plugins=True, context=None):
    registry = ActionRegistry()
    for action in discover_actions(packages, include_plugins):
        registry.register(action)
    ActionContractValidator(context).validate_registry(registry)
    return registry


def _module_actions(module: ModuleType):
    return [value for _, value in inspect.getmembers(module, inspect.isclass)
            if value is not Action and issubclass(value, Action) and value.__module__ == module.__name__
            and not inspect.isabstract(value) and value.discoverable]


def _plugin_actions(value):
    if inspect.isclass(value) and issubclass(value, Action):
        return [value]
    if isinstance(value, ModuleType):
        return _module_actions(value)
    if callable(value):
        return _plugin_actions(value())
    if isinstance(value, (list, tuple, set)):
        return [action for item in value for action in _plugin_actions(item)]
    raise TypeError(f"Unsupported {PLUGIN_GROUP} plugin: {value!r}")
