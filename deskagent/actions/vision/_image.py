"""Action result wrappers around macOS image operations."""
from __future__ import annotations

from deskagent.actions.base import Action
from deskagent.actions.types import ActionCategory, ActionResult, RiskLevel
from deskagent.platform.macos import image as native

IMAGE_EXTENSIONS = native.IMAGE_EXTENSIONS
OUTPUT_FORMATS = native.OUTPUT_FORMATS
_guard = native._guard


def _service(context):
    return getattr(getattr(context, "services", None), "image", None)


def source_image(context, value):
    service = _service(context)
    return service.source(context, value) if service else native.source_image(context, value)


def image_properties(context, value):
    service = _service(context)
    return service.properties(context, value) if service else native.image_properties(context, value)


def transform_image(context, source, target, options, *, extensions=None):
    service = _service(context)
    if service:
        return service.transform(context, source, target, options, extensions=extensions)
    if extensions is None:
        return native.transform_image(context, source, target, options)
    return native.transform_image(context, source, target, options, extensions=extensions)


def image_hash(context, value):
    service = _service(context)
    return service.hash(context, value) if service else native.image_hash(context, value)


class ImageAction(Action):
    discoverable = False
    category = ActionCategory.SYSTEM

    @staticmethod
    def run(operation):
        try:
            return ActionResult(True, operation())
        except Exception as exc:
            return ActionResult(False, error=str(exc), error_code="IMAGE_ERROR")


class ImageWriteAction(ImageAction):
    discoverable = False
    risk_level = RiskLevel.MEDIUM
    reversible = True
