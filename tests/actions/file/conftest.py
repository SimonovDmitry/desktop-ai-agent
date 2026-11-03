import importlib
import inspect
import logging
import pkgutil
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

import deskagent.actions.file as file_pkg
from deskagent.core.services import MacOSFileServices

_default_file_services = MacOSFileServices()
_default_file_ctx = SimpleNamespace(services=SimpleNamespace(file=_default_file_services))

# Wrap all File Action classes so when context is None, default file services are used
for _, _mod_name, _ in pkgutil.iter_modules(file_pkg.__path__):
    _mod = importlib.import_module(f"deskagent.actions.file.{_mod_name}")
    for _name, _cls in inspect.getmembers(_mod, inspect.isclass):
        if hasattr(_cls, "execute") and "execute" in _cls.__dict__:
            _orig = _cls.execute

            def _make_wrapper(orig_fn):
                def _wrapped(self, context, parameters=None):
                    if context is None:
                        context = _default_file_ctx
                    elif getattr(context, "services", None) is not None:
                        # Support legacy fixtures where file was nested under system
                        if not hasattr(context.services, "file") and hasattr(
                            getattr(context.services, "system", None), "file"
                        ):
                            context.services.file = context.services.system.file
                    return orig_fn(self, context, parameters)

                return _wrapped

            _cls.execute = _make_wrapper(_orig)


@pytest.fixture
def context():
    ctx = MagicMock()
    ctx.logger = logging.getLogger("deskagent.tests.file")
    ctx.settings = MagicMock()
    file_mock = MagicMock()
    ctx.services = SimpleNamespace(system=SimpleNamespace(file=file_mock), file=file_mock)
    return ctx


@pytest.fixture
def service_context():
    ctx = MagicMock()
    ctx.logger = logging.getLogger("deskagent.tests.file")
    ctx.settings = MagicMock()
    file_mock = MagicMock()
    ctx.services = SimpleNamespace(system=SimpleNamespace(file=file_mock), file=file_mock)
    return ctx


@pytest.fixture
def text_file(tmp_path):
    p = tmp_path / "document.txt"
    p.write_text("alpha\nbeta\ngamma\n", encoding="utf-8")
    return p


@pytest.fixture
def binary_file(tmp_path):
    p = tmp_path / "payload.bin"
    p.write_bytes(bytes(range(256)))
    return p


@pytest.fixture
def sample_tree(tmp_path):
    root = tmp_path / "tree"
    root.mkdir()
    (root / "a.txt").write_text("same", encoding="utf-8")
    (root / "b.txt").write_text("same", encoding="utf-8")
    (root / "c.log").write_text("database_url=localhost\n", encoding="utf-8")
    (root / "images").mkdir()
    (root / "images" / "photo.jpg").write_bytes(b"\xff\xd8\xff\xd9")
    (root / "nested").mkdir()
    (root / "nested" / "deep.txt").write_text("deep content", encoding="utf-8")
    return root
