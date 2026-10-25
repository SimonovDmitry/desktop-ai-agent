import logging
from unittest.mock import Mock

import pytest

from deskagent.actions.base import Action
from deskagent.actions.executor import ActionExecutor
from deskagent.actions.registry import ActionRegistry
from deskagent.actions.result import ActionResult


class FakeContext:
    def __init__(self):
        self.logger = Mock()


class SuccessfulAction(Action):
    name = "successful_action"

    parameters_schema = {
        "value": {
            "type": "string",
            "required": True,
        }
    }

    def execute(self, context, parameters):
        return ActionResult(
            success=True,
            data={
                "value": parameters["value"]
            }
        )


class DictAction(Action):
    name = "dict_action"

    parameters_schema = {}

    def execute(self, context, parameters):
        return {
            "hello": "world"
        }


class FailingAction(Action):
    name = "failing_action"

    parameters_schema = {}

    def execute(self, context, parameters):
        return ActionResult(
            success=False,
            error="Action failed",
            error_code="ACTION_FAILED"
        )


class ExceptionAction(Action):
    name = "exception_action"

    parameters_schema = {}

    def execute(self, context, parameters):
        raise RuntimeError("Something went wrong")


class PermissionAction(Action):
    name = "permission_action"

    required_permissions = (
        "accessibility",
    )

    parameters_schema = {}

    def execute(self, context, parameters):
        return ActionResult(
            success=True,
            data={"executed": True}
        )


class ConfirmationAction(Action):
    name = "confirmation_action"

    requires_confirmation = True

    parameters_schema = {}

    def execute(self, context, parameters):
        return ActionResult(
            success=True,
            data={"executed": True}
        )


class StringAction(Action):
    name = "string_action"

    parameters_schema = {
        "value": {
            "type": "string",
            "required": True,
        }
    }

    def execute(self, context, parameters):
        return ActionResult(
            success=True,
            data=parameters
        )


class IntegerAction(Action):
    name = "integer_action"

    parameters_schema = {
        "value": {
            "type": "integer",
            "required": True,
        }
    }

    def execute(self, context, parameters):
        return ActionResult(
            success=True,
            data=parameters
        )


class BooleanAction(Action):
    name = "boolean_action"

    parameters_schema = {
        "value": {
            "type": "boolean",
            "required": True,
        }
    }

    def execute(self, context, parameters):
        return ActionResult(
            success=True,
            data=parameters
        )


class ListAction(Action):
    name = "list_action"

    parameters_schema = {
        "value": {
            "type": "list",
            "required": True,
        }
    }

    def execute(self, context, parameters):
        return ActionResult(
            success=True,
            data=parameters
        )


class EnumAction(Action):
    name = "enum_action"

    parameters_schema = {
        "value": {
            "type": "string",
            "required": True,
            "enum": [
                "one",
                "two",
                "three",
            ],
        }
    }

    def execute(self, context, parameters):
        return ActionResult(
            success=True,
            data=parameters
        )


@pytest.fixture
def context():
    return FakeContext()


@pytest.fixture
def registry():
    registry = ActionRegistry()

    registry.register(SuccessfulAction)
    registry.register(DictAction)
    registry.register(FailingAction)
    registry.register(ExceptionAction)
    registry.register(PermissionAction)
    registry.register(ConfirmationAction)
    registry.register(StringAction)
    registry.register(IntegerAction)
    registry.register(BooleanAction)
    registry.register(ListAction)
    registry.register(EnumAction)

    return registry


@pytest.fixture
def executor(registry):
    return ActionExecutor(
        registry=registry
    )


def test_execute_successful_action(
    executor,
    context,
):
    result = executor.execute(
        "successful_action",
        context,
        {"value": "hello"}
    )

    assert result.success is True
    assert result.data == {
        "value": "hello"
    }


def test_parameters_are_passed_to_action(
    executor,
    context,
):
    result = executor.execute(
        "successful_action",
        context,
        {"value": "Safari"}
    )

    assert result.success is True
    assert result.data["value"] == "Safari"


def test_dict_result_is_converted_to_action_result(
    executor,
    context,
):
    result = executor.execute(
        "dict_action",
        context
    )

    assert isinstance(
        result,
        ActionResult
    )

    assert result.success is True
    assert result.data == {
        "hello": "world"
    }


def test_action_failure_is_returned(
    executor,
    context,
):
    result = executor.execute(
        "failing_action",
        context
    )

    assert result.success is False
    assert result.error == "Action failed"
    assert result.error_code == "ACTION_FAILED"


def test_missing_required_parameter(
    executor,
    context,
):
    result = executor.execute(
        "successful_action",
        context,
        {}
    )

    assert result.success is False
    assert result.error_code == "MISSING_PARAM"


def test_invalid_string_parameter(
    executor,
    context,
):
    result = executor.execute(
        "string_action",
        context,
        {"value": 123}
    )

    assert result.success is False
    assert result.error_code == "INVALID_PARAM"


def test_invalid_integer_parameter(
    executor,
    context,
):
    result = executor.execute(
        "integer_action",
        context,
        {"value": "123"}
    )

    assert result.success is False
    assert result.error_code == "INVALID_PARAM"


def test_invalid_boolean_parameter(
    executor,
    context,
):
    result = executor.execute(
        "boolean_action",
        context,
        {"value": "true"}
    )

    assert result.success is False
    assert result.error_code == "INVALID_PARAM"


def test_invalid_list_parameter(
    executor,
    context,
):
    result = executor.execute(
        "list_action",
        context,
        {"value": "not-a-list"}
    )

    assert result.success is False
    assert result.error_code == "INVALID_PARAM"


def test_invalid_enum_parameter(
    executor,
    context,
):
    result = executor.execute(
        "enum_action",
        context,
        {"value": "invalid"}
    )

    assert result.success is False
    assert result.error_code == "INVALID_PARAM"


def test_valid_enum_parameter(
    executor,
    context,
):
    result = executor.execute(
        "enum_action",
        context,
        {"value": "two"}
    )

    assert result.success is True


def test_permission_checker_is_called(
    registry,
    context,
):
    permission_checker = Mock(
        return_value=True
    )

    executor = ActionExecutor(
        registry=registry,
        permission_checker=permission_checker,
    )

    result = executor.execute(
        "permission_action",
        context
    )

    assert result.success is True

    permission_checker.assert_called_once()


def test_permission_denied_prevents_execution(
    registry,
    context,
):
    permission_checker = Mock(
        return_value=False
    )

    executor = ActionExecutor(
        registry=registry,
        permission_checker=permission_checker,
    )

    result = executor.execute(
        "permission_action",
        context
    )

    assert result.success is False
    assert result.error_code == "PERMISSION_DENIED"


def test_permission_checker_missing(
    registry,
    context,
):
    executor = ActionExecutor(
        registry=registry
    )

    result = executor.execute(
        "permission_action",
        context
    )

    assert result.success is False
    assert result.error_code == "PERMISSION_CHECK_ERROR"


def test_confirmation_handler_is_called(
    registry,
    context,
):
    confirmation_handler = Mock(
        return_value=True
    )

    executor = ActionExecutor(
        registry=registry,
        confirmation_handler=confirmation_handler,
    )

    result = executor.execute(
        "confirmation_action",
        context
    )

    assert result.success is True

    confirmation_handler.assert_called_once()


def test_confirmation_rejected_prevents_execution(
    registry,
    context,
):
    confirmation_handler = Mock(
        return_value=False
    )

    executor = ActionExecutor(
        registry=registry,
        confirmation_handler=confirmation_handler,
    )

    result = executor.execute(
        "confirmation_action",
        context
    )

    assert result.success is False
    assert result.error_code == "ACTION_CANCELLED"


def test_confirmation_handler_missing(
    registry,
    context,
):
    executor = ActionExecutor(
        registry=registry
    )

    result = executor.execute(
        "confirmation_action",
        context
    )

    assert result.success is False
    assert result.error_code == "CONFIRMATION_REQUIRED"


def test_action_exception_is_caught(
    executor,
    context,
):
    result = executor.execute(
        "exception_action",
        context
    )

    assert result.success is False
    assert result.error == "Something went wrong"
    assert result.error_code == "EXECUTION_ERROR"


def test_action_start_is_logged(
    executor,
    context,
):
    executor.execute(
        "successful_action",
        context,
        {"value": "hello"}
    )

    context.logger.info.assert_any_call(
        "Action started: %s",
        "successful_action"
    )


def test_success_is_logged(
    executor,
    context,
):
    executor.execute(
        "successful_action",
        context,
        {"value": "hello"}
    )

    context.logger.info.assert_any_call(
        "Action completed: %s",
        "successful_action"
    )


def test_failure_is_logged(
    executor,
    context,
):
    executor.execute(
        "failing_action",
        context
    )

    context.logger.warning.assert_called_once_with(
        "Action failed: %s [%s]",
        "failing_action",
        "ACTION_FAILED"
    )


def test_exception_is_logged(
    executor,
    context,
):
    executor.execute(
        "exception_action",
        context
    )

    context.logger.exception.assert_called_once_with(
        "Action execution exception: %s",
        "exception_action"
    )