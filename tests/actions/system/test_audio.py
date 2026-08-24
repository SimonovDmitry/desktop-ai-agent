import pytest

from deskagent.actions.system.audio import (
    DecreaseVolume,
    GetVolume,
    IncreaseVolume,
    Mute,
    SetVolume,
    Unmute,
)
from tests.conftest import assert_error, assert_success


def test_set_volume_success(context):
    action = SetVolume()
    result = action.execute(context, {"volume": 55})
    assert_success(result, {"volume": 55})
    context.services.system.audio.set_volume.assert_called_once_with(55)


@pytest.mark.parametrize("volume", [-1, 101])
def test_set_volume_rejects_out_of_range(context, volume):
    result = SetVolume().execute(context, {"volume": volume})
    assert_error(result, "INVALID_RANGE")
    context.services.system.audio.set_volume.assert_not_called()


def test_set_volume_requires_parameter(context):
    result = SetVolume().execute(context, {})
    assert_error(result, "MISSING_PARAM")


def test_set_volume_returns_system_error(context):
    context.services.system.audio.set_volume.side_effect = RuntimeError("audio failed")
    result = SetVolume().execute(context, {"volume": 50})
    assert_error(result, "SYSTEM_ERROR")
    assert result.error == "audio failed"


def test_increase_volume_uses_default_step(context):
    result = IncreaseVolume().execute(context, {})
    assert_success(result, {"increased_by": 10})
    context.services.system.audio.increase_volume.assert_called_once_with(10)


@pytest.mark.parametrize("step", [1, 50])
def test_increase_volume_accepts_boundary_steps(context, step):
    result = IncreaseVolume().execute(context, {"step": step})
    assert_success(result, {"increased_by": step})
    context.services.system.audio.increase_volume.assert_called_once_with(step)


@pytest.mark.parametrize("step", [0, 51])
def test_increase_volume_rejects_invalid_step(context, step):
    result = IncreaseVolume().execute(context, {"step": step})
    assert_error(result, "INVALID_STEP")
    context.services.system.audio.increase_volume.assert_not_called()


def test_increase_volume_returns_system_error(context):
    context.services.system.audio.increase_volume.side_effect = RuntimeError("audio failed")
    result = IncreaseVolume().execute(context, {"step": 5})
    assert_error(result, "SYSTEM_ERROR")


def test_decrease_volume_uses_default_step(context):
    result = DecreaseVolume().execute(context, {})
    assert_success(result, {"decreased_by": 10})
    context.services.system.audio.decrease_volume.assert_called_once_with(10)


@pytest.mark.parametrize("step", [0, 51])
def test_decrease_volume_rejects_invalid_step(context, step):
    result = DecreaseVolume().execute(context, {"step": step})
    assert_error(result, "INVALID_STEP")
    context.services.system.audio.decrease_volume.assert_not_called()


def test_decrease_volume_returns_system_error(context):
    context.services.system.audio.decrease_volume.side_effect = RuntimeError("audio failed")
    result = DecreaseVolume().execute(context, {"step": 5})
    assert_error(result, "SYSTEM_ERROR")


def test_mute_success(context):
    result = Mute().execute(context, {})
    assert_success(result, {"muted": True})
    context.services.system.audio.mute.assert_called_once_with()


def test_mute_returns_system_error(context):
    context.services.system.audio.mute.side_effect = RuntimeError("mute failed")
    result = Mute().execute(context, {})
    assert_error(result, "SYSTEM_ERROR")


def test_unmute_success(context):
    result = Unmute().execute(context, {})
    assert_success(result, {"muted": False})
    context.services.system.audio.unmute.assert_called_once_with()


def test_unmute_returns_system_error(context):
    context.services.system.audio.unmute.side_effect = RuntimeError("unmute failed")
    result = Unmute().execute(context, {})
    assert_error(result, "SYSTEM_ERROR")


def test_get_volume_success(context):
    context.services.system.audio.get_volume.return_value = 42
    result = GetVolume().execute(context, {})
    assert_success(result, {"volume": 42})
    context.services.system.audio.get_volume.assert_called_once_with()


def test_get_volume_returns_system_error(context):
    context.services.system.audio.get_volume.side_effect = RuntimeError("get failed")
    result = GetVolume().execute(context, {})
    assert_error(result, "SYSTEM_ERROR")
