"""Contract tests for the platform-independent file service.

These tests intentionally avoid touching the real platform.  They verify that
`deskagent.platform.base.file` exposes a complete file-service contract and
that the contract is actually abstract rather than silently providing an
OS-specific implementation in the base layer.
"""
from abc import ABC
import inspect
import importlib
import os

import pytest


MODULE = "deskagent.platform.base.file"

# Public service operations implied by the file action layer.
EXPECTED_METHODS = [
    "get_file_info", "get_file_metadata", "get_file_size", "get_file_type",
    "get_file_extension", "get_file_mime_type", "get_file_path", "get_file_name",
    "get_file_directory", "get_file_created_time", "get_file_modified_time",
    "get_file_accessed_time", "is_file", "is_directory", "is_symlink",
    "is_file_accessible", "create_file", "delete_file", "restore_file", "trash_file",
    "empty_trash", "rename_file", "copy_file", "move_file", "duplicate_file",
    "replace_file", "read_file", "write_file", "append_file", "prepend_file",
    "read_lines", "write_lines", "insert_lines", "delete_lines", "replace_text",
    "find_in_file", "create_directory", "delete_directory", "list_directory",
    "walk_directory", "find_files", "find_directories", "find_by_pattern",
    "find_by_extension", "find_by_size", "find_by_date", "create_symbolic_link",
    "create_hard_link", "read_symbolic_link", "get_link_target", "remove_link",
    "resolve_path", "create_archive", "extract_archive", "list_archive_contents",
    "add_to_archive", "remove_from_archive", "test_archive", "get_archive_info",
    "get_file_permissions", "set_file_permissions", "add_file_permission",
    "remove_file_permission", "get_file_owner", "set_file_owner", "get_file_group",
    "set_file_group", "is_file_readable", "is_file_writable", "is_file_executable",
    "compare_files", "compare_directories", "get_file_hash", "get_disk_usage",
    "get_free_space", "get_directory_size", "create_temp_file", "create_temp_directory",
    "get_temp_directory", "cleanup_temp_file", "cleanup_temp_directory",
    "open_file", "reveal_in_file_manager", "open_with_application", "set_file_hidden",
    "is_file_hidden", "watch_file", "stop_watching",
]


def load_module():
    return importlib.import_module(MODULE)


def public_classes(module):
    return [
        cls for _, cls in inspect.getmembers(module, inspect.isclass)
        if cls.__module__ == module.__name__ and not cls.__name__.startswith("_")
    ]


def service_class(module):
    classes = public_classes(module)
    candidates = [c for c in classes if "file" in c.__name__.lower()]
    assert candidates, "base file module must expose a file service class"
    # Prefer the canonical SystemFile name when present.
    return next((c for c in candidates if c.__name__ == "SystemFile"), candidates[0])


def test_base_file_module_imports():
    module = load_module()
    assert module.__name__ == MODULE


def test_base_file_service_is_abstract():
    cls = service_class(load_module())
    assert issubclass(cls, ABC)
    assert inspect.isabstract(cls)
    assert getattr(cls, "__abstractmethods__", set())


def test_base_file_service_declares_public_file_operations():
    cls = service_class(load_module())
    missing = [name for name in EXPECTED_METHODS if not callable(getattr(cls, name, None))]
    assert not missing, "Missing base file API: " + ", ".join(missing)


def test_base_file_operations_are_abstract():
    cls = service_class(load_module())
    abstract = getattr(cls, "__abstractmethods__", set())
    missing_abstract = [name for name in EXPECTED_METHODS if name not in abstract]
    assert not missing_abstract, (
        "Base file operations must be abstract: " + ", ".join(missing_abstract)
    )


@pytest.mark.parametrize("method_name", EXPECTED_METHODS)
def test_file_operation_is_callable_on_the_class(method_name):
    cls = service_class(load_module())
    method = getattr(cls, method_name)
    assert callable(method)
    assert not method_name.startswith("_")


def test_base_file_service_does_not_perform_real_io(tmp_path):
    cls = service_class(load_module())
    with pytest.raises(TypeError):
        cls()
    # A base contract test must not create or mutate files merely by importing it.
    assert list(tmp_path.iterdir()) == []


def test_base_contract_has_no_platform_specific_commands():
    module = load_module()
    source = inspect.getsource(module)
    forbidden = ("osascript", "AppKit", "Foundation", "NSWorkspace", "subprocess.run")
    assert not any(token in source for token in forbidden)
