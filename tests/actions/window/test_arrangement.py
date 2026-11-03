from deskagent.actions.window import arrangement

from .conftest import assert_success, assert_system_error

CASES = [
    (
        arrangement.ArrangeWindows,
        "arrangement.arrange",
        {"window_ids": [201, 202], "layout": "horizontal"},
        {"arranged": True, "windows": [201, 202]},
        [201, 202],
    ),
    (
        arrangement.TileWindows,
        "arrangement.tile",
        {"window_ids": [201, 202]},
        {"arranged": True},
        None,
    ),
    (
        arrangement.CascadeWindows,
        "arrangement.cascade",
        {"window_ids": [201, 202]},
        {"arranged": True},
        None,
    ),
    (
        arrangement.StackWindows,
        "arrangement.stack",
        {"window_ids": [201, 202]},
        {"arranged": True},
        None,
    ),
    (
        arrangement.ArrangeApplicationWindows,
        "arrangement.arrange_app",
        {"application": "Safari", "layout": "horizontal"},
        {"application": "Safari", "layout": "horizontal"},
        None,
    ),
    (
        arrangement.ArrangeWindowsGrid,
        "arrangement.grid",
        {"window_ids": [201, 202], "rows": 1, "columns": 2},
        {"arranged": True},
        None,
    ),
    (
        arrangement.EqualizeWindowSizes,
        "arrangement.equalize",
        {"window_ids": [201, 202]},
        {"equalized": True},
        None,
    ),
]


def _target(context, path):
    obj = context.services.window
    for part in path.split("."):
        obj = getattr(obj, part)
    return obj


def test_all_actions_success(window_context):
    for action_cls, path, params, expected, return_value in CASES:
        target = _target(window_context, path)
        if return_value is not None:
            target.return_value = return_value
        result = action_cls().execute(window_context, params)
        assert_success(result, expected)
        target.reset_mock()


def test_all_actions_convert_service_exceptions(window_context):
    for action_cls, path, params, _, _ in CASES:
        target = _target(window_context, path)
        target.side_effect = RuntimeError("arrangement failure")
        result = action_cls().execute(window_context, params)
        assert_system_error(result, "arrangement failure")
        target.side_effect = None
        target.reset_mock()
