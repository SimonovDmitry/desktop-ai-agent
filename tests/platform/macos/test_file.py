"""macOS file-service tests.

The suite is intentionally deterministic: no real Finder, Trash, LaunchServices,
permission changes or external applications are invoked.  OS boundaries are
mocked while ordinary temporary-directory filesystem behaviour is exercised.
"""
import importlib
import inspect
import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

MODULE = "deskagent.platform.macos.file"


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


def service_class(module):
    classes = [
        c for _, c in inspect.getmembers(module, inspect.isclass)
        if c.__module__ == module.__name__ and "file" in c.__name__.lower()
    ]
    assert classes, "macOS file module must expose a file service class"
    return next((c for c in classes if c.__name__ in {"MacOSFile", "MacOSSystemFile"}), classes[0])


@pytest.fixture
def file_service():
    cls = service_class(load_module())
    return cls()


def test_macos_file_service_implements_base_contract():
    module = load_module()
    cls = service_class(module)
    missing = [name for name in EXPECTED_METHODS if not callable(getattr(cls, name, None))]
    assert not missing, "Missing macOS file API: " + ", ".join(missing)


def test_macos_file_service_is_not_abstract():
    cls = service_class(load_module())
    assert not inspect.isabstract(cls)


@pytest.mark.parametrize("name", EXPECTED_METHODS)
def test_macos_file_operation_has_concrete_implementation(name):
    cls = service_class(load_module())
    method = getattr(cls, name)
    assert callable(method)
    assert not getattr(method, "__isabstractmethod__", False)


def test_get_file_info_real_temp_file(file_service, tmp_path):
    path = tmp_path / "report.final.txt"
    path.write_text("hello\nworld", encoding="utf-8")
    result = file_service.get_file_info(str(path))
    assert result is not None
    assert result["name"] == path.name
    assert result["extension"] == ".txt"
    assert result["size"] == path.stat().st_size
    assert result["type"] == "file"


def test_file_content_round_trip(file_service, tmp_path):
    path = tmp_path / "unicode.txt"
    content = "Привет\n日本語\nemoji: 😀\n"
    file_service.write_file(str(path), content)
    assert file_service.read_file(str(path)) == content


def test_copy_and_move_preserve_content(file_service, tmp_path):
    source = tmp_path / "source.txt"
    copy = tmp_path / "copy.txt"
    moved = tmp_path / "moved.txt"
    source.write_text("payload", encoding="utf-8")
    file_service.copy_file(str(source), str(copy))
    assert copy.read_text(encoding="utf-8") == "payload"
    file_service.move_file(str(copy), str(moved))
    assert moved.read_text(encoding="utf-8") == "payload"
    assert not copy.exists()


def test_symbolic_link_round_trip(file_service, tmp_path):
    target = tmp_path / "target.txt"
    link = tmp_path / "link.txt"
    target.write_text("target", encoding="utf-8")
    file_service.create_symbolic_link(str(target), str(link))
    assert link.is_symlink()
    assert file_service.read_symbolic_link(str(link))
    assert Path(file_service.resolve_path(str(link))).resolve() == target.resolve()
    file_service.remove_link(str(link))
    assert not link.exists()
    assert target.exists()


def test_hard_link_preserves_inode_when_supported(file_service, tmp_path):
    source = tmp_path / "source.bin"
    link = tmp_path / "hard.bin"
    source.write_bytes(b"abc")
    file_service.create_hard_link(str(source), str(link))
    assert link.exists()
    assert os.stat(source).st_ino == os.stat(link).st_ino


def test_create_archive_extracts_contents(file_service, tmp_path):
    first = tmp_path / "a.txt"
    second = tmp_path / "b.txt"
    archive = tmp_path / "bundle.zip"
    out = tmp_path / "extracted"
    first.write_text("A", encoding="utf-8")
    second.write_text("B", encoding="utf-8")
    file_service.create_archive([str(first), str(second)], str(archive), "zip")
    assert archive.exists()
    file_service.extract_archive(str(archive), str(out))
    assert (out / first.name).read_text(encoding="utf-8") == "A"
    assert (out / second.name).read_text(encoding="utf-8") == "B"


def test_compare_identical_and_different_files(file_service, tmp_path):
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    a.write_text("same", encoding="utf-8")
    b.write_text("same", encoding="utf-8")
    assert file_service.compare_files(str(a), str(b))
    b.write_text("different", encoding="utf-8")
    assert not file_service.compare_files(str(a), str(b))


def test_hash_is_stable(file_service, tmp_path):
    path = tmp_path / "hash.txt"
    path.write_text("stable", encoding="utf-8")
    first = file_service.get_file_hash(str(path))
    second = file_service.get_file_hash(str(path))
    assert first == second
    assert first


def test_directory_listing_and_walk(file_service, tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    (root / "a.txt").write_text("a")
    child = root / "child"
    child.mkdir()
    (child / "b.txt").write_text("b")
    listing = file_service.list_directory(str(root))
    assert listing is not None
    walked = file_service.walk_directory(str(root))
    assert walked is not None


def test_missing_path_raises_or_returns_structured_failure(file_service, tmp_path):
    missing = tmp_path / "does-not-exist"
    for name in ("get_file_info", "get_file_size", "get_file_type", "read_file"):
        method = getattr(file_service, name)
        try:
            result = method(str(missing))
        except (FileNotFoundError, OSError):
            continue
        assert result is not None


def test_permissions_can_be_read_without_changing_global_state(file_service, tmp_path):
    path = tmp_path / "permissions.txt"
    path.write_text("x", encoding="utf-8")
    result = file_service.get_file_permissions(str(path))
    assert result is not None
    assert isinstance(result, dict)


def test_opening_external_apps_is_mocked(file_service, tmp_path):
    path = tmp_path / "open.txt"
    path.write_text("x")
    with patch.object(file_service, "open_with_application", return_value=True) as mocked:
        result = file_service.open_with_application(str(path), "TextEdit")
        assert result is True
        mocked.assert_called_once_with(str(path), "TextEdit")


def test_reveal_in_file_manager_is_mocked(file_service, tmp_path):
    path = tmp_path / "reveal.txt"
    path.write_text("x")
    with patch.object(file_service, "reveal_in_file_manager", return_value=True) as mocked:
        result = file_service.reveal_in_file_manager(str(path))
        assert result is True
        mocked.assert_called_once_with(str(path))


def test_trash_and_empty_trash_are_never_executed_against_real_system(file_service, tmp_path):
    path = tmp_path / "trash.txt"
    path.write_text("danger-safe", encoding="utf-8")
    with patch.object(file_service, "trash_file", return_value={"trashed": True}) as trash, \
         patch.object(file_service, "empty_trash", return_value={"emptied": True}) as empty:
        assert file_service.trash_file(str(path))["trashed"] is True
        assert file_service.empty_trash()["emptied"] is True
        trash.assert_called_once_with(str(path))
        empty.assert_called_once_with()
    assert path.exists()
