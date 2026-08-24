from deskagent.actions.result import ActionResult


def test_action_result_success():
    result = ActionResult(success=True, data={"value": 1})
    assert result.success is True
    assert result.data == {"value": 1}
    assert result.error is None
    assert result.error_code is None


def test_action_result_error():
    result = ActionResult(success=False, error="failed", error_code="SYSTEM_ERROR")
    assert result.success is False
    assert result.error == "failed"
    assert result.error_code == "SYSTEM_ERROR"


def test_action_result_metadata():
    result = ActionResult(success=True, metadata={"request_id": "123"})
    assert result.metadata == {"request_id": "123"}
