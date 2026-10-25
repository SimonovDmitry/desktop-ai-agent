import logging
from typing import Any, Callable
from deskagent.actions.base import ActionRegistry
from deskagent.actions.types import ActionResult


class ActionExecutor:
    def __init__(self, registry: ActionRegistry, permission_checker: Callable = None,
                 confirmation_handler: Callable = None):
        self.registry = registry
        self.permission_checker = permission_checker
        self.confirmation_handler = confirmation_handler

    def execute(self, action_name: str, context, parameters: dict[str, Any] = None) -> ActionResult:
        params = parameters or {}
        try:
            action = self.registry.create(action_name)
            self._log(context, logging.INFO, "Action started: %s", action.name)

            result = self._validate_parameters(action, params)
            if not result: result = self._check_permissions(context, action)
            if not result: result = self._check_confirmation(context, action, params)

            if result:
                self._log_result(context, action, result)
                return result

            result = action.execute(context, params)
            if not isinstance(result, ActionResult):
                result = ActionResult(success=True, data=result)

            self._log_result(context, action, result)
            return result

        except Exception as exc:
            self._get_logger(context).exception("Action execution exception: %s", action_name)
            return ActionResult(success=False, error=str(exc), error_code="EXECUTION_ERROR")

    def _validate_parameters(self, action, params: dict[str, Any]) -> ActionResult | None:
        schema = getattr(action, "parameters_schema", {})
        types = {
            "string": (str,), "integer": (int,), "float": (int, float), "boolean": (bool,),
            "list": (list,), "dict": (dict,), "string_or_int": (str, int),
        }

        for name, cfg in schema.items():
            if cfg.get("required") and name not in params:
                return ActionResult(success=False, error=f"'{name}' required", error_code="MISSING_PARAM")

            if name not in params: continue

            val, t_name = params[name], cfg.get("type")
            if t_name in types and (isinstance(val, bool) != (t_name == "boolean")
                                    or not isinstance(val, types[t_name])):
                return ActionResult(success=False, error=f"'{name}' must be {t_name}", error_code="INVALID_PARAM")

            if (enum := cfg.get("enum")) and val not in enum:
                return ActionResult(success=False, error=f"'{name}' not in {enum}", error_code="INVALID_PARAM")
            if "minimum" in cfg and val < cfg["minimum"]:
                return ActionResult(success=False, error=f"'{name}' is below minimum", error_code="INVALID_PARAM")
            if "maximum" in cfg and val > cfg["maximum"]:
                return ActionResult(success=False, error=f"'{name}' is above maximum", error_code="INVALID_PARAM")
        return None

    def _check_permissions(self, context, action) -> ActionResult | None:
        perms = getattr(action, "required_permissions", ())
        if hasattr(self.permission_checker, "check_action"):
            report = self.permission_checker.check_action(action)
            if report.granted:
                return None
            return ActionResult(success=False, error=report.error, error_code="PERMISSION_DENIED",
                                metadata=report.to_dict())
        if not perms:
            return None
        if not self.permission_checker:
            return ActionResult(success=False, error="Permission checker is not configured",
                                error_code="PERMISSION_CHECK_ERROR")
        if not self.permission_checker(context, action, perms):
            return ActionResult(success=False, error=f"Required permissions denied: {', '.join(perms)}",
                                error_code="PERMISSION_DENIED")
        return None

    def _check_confirmation(self, context, action, params) -> ActionResult | None:
        if not getattr(action, "requires_confirmation", False): return None
        if not self.confirmation_handler:
            return ActionResult(success=False, error="Confirm required", error_code="CONFIRMATION_REQUIRED")
        if not self.confirmation_handler(context, action, params):
            return ActionResult(success=False, error="Cancelled", error_code="ACTION_CANCELLED")
        return None

    def _get_logger(self, context):
        return getattr(context, "logger", logging.getLogger(__name__))

    def _log(self, context, level, msg, *args):
        logger = self._get_logger(context)
        if level == logging.INFO:
            logger.info(msg, *args)
        elif level == logging.WARNING:
            logger.warning(msg, *args)
        elif level == logging.ERROR:
            logger.error(msg, *args)
        else:
            logger.log(level, msg, *args)

    def _log_result(self, context, action, result):
        if result.success:
            self._log(context, logging.INFO, "Action completed: %s", action.name)
        else:
            self._log(context, logging.WARNING, "Action failed: %s [%s]", action.name, result.error_code)
