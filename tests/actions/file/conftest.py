import logging
from types import SimpleNamespace
from unittest.mock import MagicMock
import pytest

@pytest.fixture
def context():
    ctx = MagicMock()
    ctx.logger = logging.getLogger('deskagent.tests.file')
    ctx.settings = MagicMock()
    ctx.services = SimpleNamespace(system=MagicMock())
    return ctx

@pytest.fixture
def service_context():
    ctx = MagicMock()
    ctx.logger = logging.getLogger('deskagent.tests.file')
    ctx.settings = MagicMock()
    ctx.services = SimpleNamespace(system=SimpleNamespace(file=MagicMock()))
    return ctx

@pytest.fixture
def text_file(tmp_path):
    p = tmp_path / 'document.txt'
    p.write_text('alpha\nbeta\ngamma\n', encoding='utf-8')
    return p

@pytest.fixture
def binary_file(tmp_path):
    p = tmp_path / 'payload.bin'
    p.write_bytes(bytes(range(256)))
    return p

@pytest.fixture
def sample_tree(tmp_path):
    root = tmp_path / 'tree'; root.mkdir()
    (root / 'a.txt').write_text('same', encoding='utf-8')
    (root / 'b.txt').write_text('same', encoding='utf-8')
    (root / 'c.log').write_text('database_url=localhost\n', encoding='utf-8')
    (root / 'images').mkdir(); (root / 'images' / 'photo.jpg').write_bytes(b'\xff\xd8\xff\xd9')
    (root / 'nested').mkdir(); (root / 'nested' / 'deep.txt').write_text('deep content', encoding='utf-8')
    return root
