"""Native macOS image inspection and transformations."""
from __future__ import annotations

from pathlib import Path

from deskagent.actions.vision._image import (
    IMAGE_EXTENSIONS, OUTPUT_FORMATS, ImageAction, ImageWriteAction,
    image_hash, image_properties, source_image, transform_image,
)

PATH = {"path": {"type": "string", "required": True}}
PATH_OUTPUT = {**PATH, "output_path": {"type": "string", "required": True}}


def _info(context, path):
    source, values = image_properties(context, path)
    return {"path": str(source), "bytes": source.stat().st_size, "properties": values}


class InspectImageFile(ImageAction):
    name = "inspect_image_file"
    description = "Inspect image dimensions, format, color properties and file size"
    parameters_schema = PATH
    discoverable = True

    def execute(self, context, parameters):
        return self.run(lambda: _info(context, parameters["path"]))


class GetImageDimensions(ImageAction):
    name = "get_image_dimensions"
    description = "Read width, height, aspect ratio and orientation of an image"
    parameters_schema = PATH
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            source, props = image_properties(context, parameters["path"])
            width, height = int(props["pixelWidth"]), int(props["pixelHeight"])
            return {"path": str(source), "width": width, "height": height,
                    "aspect_ratio": round(width / height, 6),
                    "orientation": "landscape" if width > height else
                    "portrait" if height > width else "square"}
        return self.run(operation)


class GetImageColorInfo(ImageAction):
    name = "get_image_color_info"
    description = "Read image color space, depth, alpha presence and sample count"
    parameters_schema = PATH
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            source, props = image_properties(context, parameters["path"])
            return {"path": str(source), "color_space": props.get("space"),
                    "samples_per_pixel": props.get("samplesPerPixel"),
                    "bits_per_sample": props.get("bitsPerSample"),
                    "has_alpha": props.get("hasAlpha") == "yes", "format": props.get("format")}
        return self.run(operation)


class GetImageMetadataSummary(ImageAction):
    name = "get_image_metadata_summary"
    description = "Read non-pixel image metadata including DPI and attribution fields"
    parameters_schema = PATH
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            source, props = image_properties(context, parameters["path"])
            keys = ("dpiWidth", "dpiHeight", "creation", "make", "model",
                    "description", "copyright", "artist")
            return {"path": str(source), "metadata": {
                key: props[key] for key in keys if key in props and props[key] != "<nil>"
            }}
        return self.run(operation)


class HashImageFile(ImageAction):
    name = "hash_image_file"
    description = "Compute SHA-256 of an image file without returning image bytes"
    parameters_schema = PATH
    discoverable = True

    def execute(self, context, parameters):
        return self.run(lambda: image_hash(context, parameters["path"]))


class CompareImageFiles(ImageAction):
    name = "compare_image_files"
    description = "Compare image file hashes and dimensions"
    parameters_schema = {"first_path": {"type": "string", "required": True},
                         "second_path": {"type": "string", "required": True}}
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            first = image_hash(context, parameters["first_path"])
            second = image_hash(context, parameters["second_path"])
            _, left = image_properties(context, parameters["first_path"])
            _, right = image_properties(context, parameters["second_path"])

            def dimensions(props):
                return [int(props["pixelWidth"]), int(props["pixelHeight"])]
            return {"first": first, "second": second,
                    "identical_bytes": first["sha256"] == second["sha256"],
                    "same_dimensions": dimensions(left) == dimensions(right),
                    "first_dimensions": dimensions(left), "second_dimensions": dimensions(right)}
        return self.run(operation)


class ImageTransformAction(ImageWriteAction):
    discoverable = False
    output_extensions = IMAGE_EXTENSIONS

    def options(self, context, parameters):
        raise NotImplementedError

    def execute(self, context, parameters):
        def operation():
            source = source_image(context, parameters["path"])
            target = Path(parameters["output_path"]).expanduser().resolve()
            if self.output_extensions == IMAGE_EXTENSIONS and target.suffix.lower() != source.suffix.lower():
                raise ValueError("Transform output extension must match source extension")
            return transform_image(context, source, target, self.options(context, parameters),
                                   extensions=self.output_extensions)
        return self.run(operation)


class ResizeImage(ImageTransformAction):
    name = "resize_image"
    description = "Resize an image to exact width and height in a new file"
    parameters_schema = {**PATH_OUTPUT,
                         "width": {"type": "integer", "required": True, "minimum": 1, "maximum": 20000},
                         "height": {"type": "integer", "required": True, "minimum": 1, "maximum": 20000}}
    discoverable = True

    def options(self, context, parameters):
        width, height = parameters["width"], parameters["height"]
        if width < 1 or height < 1 or width * height > 100_000_000:
            raise ValueError("Target dimensions exceed the processing limit")
        return ["-z", str(height), str(width)]


class FitImageWithin(ImageTransformAction):
    name = "fit_image_within"
    description = "Scale an image to fit a square bound while preserving aspect ratio"
    parameters_schema = {**PATH_OUTPUT,
                         "max_dimension": {"type": "integer", "required": True,
                                           "minimum": 1, "maximum": 20000}}
    discoverable = True

    def options(self, context, parameters):
        dimension = parameters["max_dimension"]
        if not 1 <= dimension <= 20000:
            raise ValueError("Invalid maximum dimension")
        return ["-Z", str(dimension)]


class RotateImage(ImageTransformAction):
    name = "rotate_image"
    description = "Rotate an image clockwise by a right angle"
    parameters_schema = {**PATH_OUTPUT, "degrees": {"type": "integer", "required": True, "enum": [90, 180, 270]}}
    discoverable = True

    def options(self, context, parameters):
        degrees = parameters["degrees"]
        if degrees not in {90, 180, 270}:
            raise ValueError("Rotation must be 90, 180 or 270 degrees")
        return ["-r", str(degrees)]


class FlipImage(ImageTransformAction):
    name = "flip_image"
    description = "Flip an image horizontally or vertically"
    parameters_schema = {**PATH_OUTPUT, "direction": {"type": "string", "required": True, "enum": ["horizontal", "vertical"]}}
    discoverable = True

    def options(self, context, parameters):
        direction = parameters["direction"]
        if direction not in {"horizontal", "vertical"}:
            raise ValueError("Invalid flip direction")
        return ["-f", direction]


class CropImageCenter(ImageTransformAction):
    name = "crop_image_center"
    description = "Center-crop an image to a specified width and height"
    parameters_schema = {**PATH_OUTPUT,
                         "width": {"type": "integer", "required": True, "minimum": 1},
                         "height": {"type": "integer", "required": True, "minimum": 1}}
    discoverable = True

    def options(self, context, parameters):
        _, props = image_properties(context, parameters["path"])
        width, height = parameters["width"], parameters["height"]
        if width < 1 or height < 1 or width > int(props["pixelWidth"]) or height > int(props["pixelHeight"]):
            raise ValueError("Crop must fit inside the source image")
        return ["-c", str(height), str(width)]


class PadImage(ImageTransformAction):
    name = "pad_image"
    description = "Pad an image to a larger width and height with a chosen color"
    parameters_schema = {**PATH_OUTPUT,
                         "width": {"type": "integer", "required": True, "minimum": 1},
                         "height": {"type": "integer", "required": True, "minimum": 1},
                         "color": {"type": "string", "required": False, "default": "FFFFFF"}}
    discoverable = True

    def options(self, context, parameters):
        _, props = image_properties(context, parameters["path"])
        width, height = parameters["width"], parameters["height"]
        color = parameters.get("color", "FFFFFF")
        if width < int(props["pixelWidth"]) or height < int(props["pixelHeight"]) or width * height > 100_000_000:
            raise ValueError("Padding dimensions must contain the source and stay within limits")
        if len(color) != 6 or any(char not in "0123456789ABCDEFabcdef" for char in color):
            raise ValueError("Color must be six hexadecimal digits")
        return ["-p", str(height), str(width), "--padColor", color]


class ConvertImageFormat(ImageTransformAction):
    name = "convert_image_format"
    description = "Convert an image to a supported output format"
    parameters_schema = {**PATH_OUTPUT,
                         "format": {"type": "string", "required": True, "enum": list(OUTPUT_FORMATS)}}
    output_extensions = frozenset(OUTPUT_FORMATS.values())
    discoverable = True

    def options(self, context, parameters):
        format_name = parameters["format"]
        if format_name not in OUTPUT_FORMATS:
            raise ValueError("Unsupported output format")
        target_suffix = Path(parameters["output_path"]).suffix.lower()
        if target_suffix != OUTPUT_FORMATS[format_name]:
            raise ValueError("Output extension does not match requested format")
        return ["-s", "format", format_name]


class SetImageDpi(ImageTransformAction):
    name = "set_image_dpi"
    description = "Set horizontal and vertical print resolution in a new image"
    parameters_schema = {**PATH_OUTPUT,
                         "dpi": {"type": "integer", "required": True, "minimum": 36, "maximum": 1200}}
    discoverable = True

    def options(self, context, parameters):
        dpi = parameters["dpi"]
        if not 36 <= dpi <= 1200:
            raise ValueError("DPI must be between 36 and 1200")
        return ["-s", "dpiWidth", str(dpi), "-s", "dpiHeight", str(dpi)]


class OptimizeImageForSharing(ImageTransformAction):
    name = "optimize_image_for_sharing"
    description = "Apply macOS color optimization to a new image"
    parameters_schema = PATH_OUTPUT
    discoverable = True

    def options(self, context, parameters):
        return ["--optimizeColorForSharing"]


class SetJpegQuality(ImageTransformAction):
    name = "set_jpeg_quality"
    description = "Re-encode a JPEG copy at a selected quality level"
    parameters_schema = {**PATH_OUTPUT,
                         "quality": {"type": "integer", "required": True,
                                     "minimum": 1, "maximum": 100}}
    output_extensions = frozenset({".jpg", ".jpeg"})
    discoverable = True

    def options(self, context, parameters):
        source = source_image(context, parameters["path"])
        if source.suffix.lower() not in {".jpg", ".jpeg"}:
            raise ValueError("JPEG input is required")
        quality = parameters["quality"]
        if not 1 <= quality <= 100:
            raise ValueError("Quality must be 1-100")
        return ["-s", "format", "jpeg", "-s", "formatOptions", str(quality)]
