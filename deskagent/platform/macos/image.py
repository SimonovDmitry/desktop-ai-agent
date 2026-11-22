"""Native macOS image operations used by vision actions."""
from __future__ import annotations

import hashlib
import os
import platform
import shutil
import subprocess
import tempfile
from pathlib import Path

from deskagent.privacy.guards import FilesystemGuard
from deskagent.platform.base.image import ImageService

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".gif", ".bmp", ".heic"}
OUTPUT_FORMATS = {"png": ".png", "jpeg": ".jpg", "tiff": ".tiff", "gif": ".gif", "bmp": ".bmp", "heic": ".heic"}
MAX_IMAGE_BYTES = 50_000_000
MAX_PIXELS = 100_000_000


def _macos():
    if platform.system() != "Darwin":
        raise RuntimeError("Image actions require macOS sips")


def _guard(context):
    security = context.settings.security
    return FilesystemGuard(security.allowed_paths, security.blocked_paths)


def source_image(context, value):
    _macos()
    path = Path(value).expanduser().resolve()
    if path.suffix.lower() not in IMAGE_EXTENSIONS or not path.is_file():
        raise FileNotFoundError("A supported image file is required")
    decision = _guard(context).check("read_file", {"path": str(path)})
    if not decision.allowed:
        raise PermissionError(decision.reason)
    if path.stat().st_size > MAX_IMAGE_BYTES:
        raise ValueError("Image exceeds 50 MB limit")
    return path


def target_image(context, value, extensions=IMAGE_EXTENSIONS):
    target = Path(value).expanduser().resolve()
    if target.suffix.lower() not in extensions:
        raise ValueError("Unsupported output image extension")
    decision = _guard(context).check("write_file", {"output_path": str(target)})
    if not decision.allowed:
        raise PermissionError(decision.reason)
    if target.exists():
        raise FileExistsError(f"Output already exists: {target}")
    return target


def image_properties(context, value):
    source = source_image(context, value)
    keys = ("pixelWidth", "pixelHeight", "format", "space", "samplesPerPixel",
            "bitsPerSample", "hasAlpha", "dpiWidth", "dpiHeight",
            "creation", "make", "model", "description", "copyright", "artist")
    command = ["/usr/bin/sips"]
    for key in keys:
        command.extend(["-g", key])
    result = subprocess.run([*command, str(source)], capture_output=True, text=True, timeout=20, check=True)
    properties = {}
    for line in result.stdout.splitlines()[1:]:
        if ": " in line:
            key, value = line.strip().split(": ", 1)
            properties[key] = value
    try:
        width, height = int(properties["pixelWidth"]), int(properties["pixelHeight"])
    except (KeyError, ValueError) as exc:
        raise ValueError("Image dimensions are unavailable") from exc
    if width < 1 or height < 1 or width * height > MAX_PIXELS:
        raise ValueError("Image dimensions exceed the processing limit")
    return source, properties


def transform_image(context, source_value, target_value, options, *, extensions=IMAGE_EXTENSIONS):
    source, properties = image_properties(context, source_value)
    target = target_image(context, target_value, extensions)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary_dir = Path(tempfile.mkdtemp(prefix=".deskagent-image-", dir=target.parent))
    try:
        temporary = temporary_dir / ("result" + target.suffix)
        command = ["/usr/bin/sips", *options, str(source), "-o", str(temporary)]
        subprocess.run(command, capture_output=True, text=True, timeout=90, check=True)
        if not temporary.is_file() or not temporary.stat().st_size:
            raise RuntimeError("Image transform produced no output")
        if temporary.stat().st_size > MAX_IMAGE_BYTES:
            raise ValueError("Output image exceeds 50 MB limit")
        temporary.chmod(0o600)
        os.link(temporary, target)
        return {"source": str(source), "path": str(target), "bytes": target.stat().st_size,
                "source_width": int(properties["pixelWidth"]),
                "source_height": int(properties["pixelHeight"])}
    finally:
        shutil.rmtree(temporary_dir)


def image_hash(context, value):
    source = source_image(context, value)
    digest = hashlib.sha256()
    with source.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return {"path": str(source), "sha256": digest.hexdigest(), "bytes": source.stat().st_size}


class MacOSImageService(ImageService):
    def source(self, context, path):
        return source_image(context, path)

    def properties(self, context, path):
        return image_properties(context, path)

    def transform(self, context, source, target, options, *, extensions=None):
        if extensions is None:
            return transform_image(context, source, target, options)
        return transform_image(context, source, target, options, extensions=extensions)

    def hash(self, context, path):
        return image_hash(context, path)
