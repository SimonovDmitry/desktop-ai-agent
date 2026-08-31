def target_for(context, path):
    obj = context.services.window
    for part in path.split('.'):
        obj = getattr(obj, part)
    return obj


def run_success_cases(context, cases):
    for action_cls, path, params, expected_data, return_value in cases:
        target = target_for(context, path)
        target.reset_mock()
        target.side_effect = None
        target.return_value = return_value
        result = action_cls().execute(context, params)
        assert result.success is True
        assert result.error is None
        assert result.error_code is None
        assert result.data == expected_data
        assert target.called


def run_exception_cases(context, cases, error_code="SYSTEM_ERROR", message="service failure"):
    for action_cls, path, params, _, _ in cases:
        target = target_for(context, path)
        target.reset_mock()
        target.side_effect = RuntimeError(message)
        result = action_cls().execute(context, params)
        assert result.success is False
        assert result.error == message
        assert result.error_code == error_code
        target.side_effect = None
