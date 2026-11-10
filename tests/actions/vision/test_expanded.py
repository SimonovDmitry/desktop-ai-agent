import struct
import zlib
from types import SimpleNamespace

from deskagent.actions.registry import create_action_registry
from deskagent.actions.vision import ocr_inspection
from deskagent.actions.vision.image_files import (
    CompareImageFiles, ConvertImageFormat, CropImageCenter, FitImageWithin,
    FlipImage, GetImageColorInfo, GetImageDimensions, GetImageMetadataSummary,
    HashImageFile, InspectImageFile, OptimizeImageForSharing, PadImage,
    ResizeImage, RotateImage, SetImageDpi, SetJpegQuality,
)
from deskagent.actions.vision.ocr_inspection import (
    CompareImageText, CountTextInImage, FindTextInImage, FindTextNearText,
    GetImageTextReadingOrder, GetImageTextSummary, GetOcrConfidenceReport,
    GetTextInImageRegion,
)
from deskagent.core.config import SecuritySettings, Settings


def context(tmp_path):
    return SimpleNamespace(settings=Settings(
        security=SecuritySettings(allowed_paths=[str(tmp_path)], blocked_paths=[])
    ))


def png(path, width=4, height=3):
    def chunk(kind, data):
        return b"".join((struct.pack(">I", len(data)), kind, data,
                         struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)))
    row = b"\x00" + b"\xff\x00\x00" * width
    path.write_bytes(b"".join((
        b"\x89PNG\r\n\x1a\n",
        chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)),
        chunk(b"IDAT", zlib.compress(row * height)),
        chunk(b"IEND", b""),
    )))
    return path


def test_native_image_inspection_and_transforms(tmp_path):
    source = png(tmp_path / "source.png")
    ctx = context(tmp_path)
    path = str(source)
    assert InspectImageFile().execute(ctx, {"path": path}).data["properties"]["pixelWidth"] == "4"
    assert GetImageDimensions().execute(ctx, {"path": path}).data["orientation"] == "landscape"
    assert GetImageColorInfo().execute(ctx, {"path": path}).data["color_space"] == "RGB"
    assert "dpiWidth" in GetImageMetadataSummary().execute(ctx, {"path": path}).data["metadata"]
    assert len(HashImageFile().execute(ctx, {"path": path}).data["sha256"]) == 64
    assert CompareImageFiles().execute(ctx, {"first_path": path, "second_path": path}).data["identical_bytes"]
    operations = [
        (ResizeImage(), {"width": 8, "height": 6}, "resize.png", (8, 6)),
        (FitImageWithin(), {"max_dimension": 2}, "fit.png", (2, 1)),
        (RotateImage(), {"degrees": 90}, "rotate.png", (3, 4)),
        (FlipImage(), {"direction": "horizontal"}, "flip.png", (4, 3)),
        (CropImageCenter(), {"width": 2, "height": 2}, "crop.png", (2, 2)),
        (PadImage(), {"width": 6, "height": 5, "color": "FFFFFF"}, "pad.png", (6, 5)),
        (SetImageDpi(), {"dpi": 144}, "dpi.png", (4, 3)),
        (OptimizeImageForSharing(), {}, "optimized.png", (4, 3)),
    ]
    for action, extra, filename, dimensions in operations:
        result = action.execute(ctx, {"path": path, "output_path": str(tmp_path / filename), **extra})
        assert result.success, (action.name, result.error)
        output = GetImageDimensions().execute(ctx, {"path": result.data["path"]})
        assert output.success
        assert (output.data["width"], output.data["height"]) == dimensions
    converted = ConvertImageFormat().execute(ctx, {
        "path": path, "output_path": str(tmp_path / "converted.jpg"), "format": "jpeg",
    })
    assert converted.success, converted.error
    quality = SetJpegQuality().execute(ctx, {
        "path": converted.data["path"], "output_path": str(tmp_path / "quality.jpg"), "quality": 70,
    })
    assert quality.success, quality.error


def test_image_output_collision_and_allowed_path(tmp_path):
    source = png(tmp_path / "source.png")
    ctx = context(tmp_path)
    collision = ResizeImage().execute(ctx, {
        "path": str(source), "output_path": str(source), "width": 2, "height": 2,
    })
    outside = ResizeImage().execute(ctx, {
        "path": str(source), "output_path": str(tmp_path.parent / "outside.png"),
        "width": 2, "height": 2,
    })
    assert not collision.success and not outside.success
    assert GetImageDimensions().execute(ctx, {"path": str(source)}).data["width"] == 4


def test_ocr_inspection_actions(tmp_path, monkeypatch):
    source = png(tmp_path / "source.png", 100, 100)
    second = png(tmp_path / "second.png", 100, 100)
    lines = [
        {"text": "Save", "confidence": 0.95,
         "bounds": {"x": 10, "y": 10, "width": 20, "height": 10}},
        {"text": "Cancel", "confidence": 0.4,
         "bounds": {"x": 60, "y": 60, "width": 20, "height": 10}},
    ]
    monkeypatch.setattr(ocr_inspection, "_ocr", lambda path: lines if path == str(source) else lines[:1])
    ctx = context(tmp_path)
    path = str(source)
    assert FindTextInImage().execute(ctx, {"path": path, "query": "save"}).data["total"] == 1
    assert GetTextInImageRegion().execute(ctx, {
        "path": path, "x": 0, "y": 0, "width": 50, "height": 50,
    }).data["total"] == 1
    assert GetImageTextSummary().execute(ctx, {"path": path}).data["line_count"] == 2
    assert GetOcrConfidenceReport().execute(ctx, {"path": path, "threshold": 0.5}).data["total"] == 1
    assert GetImageTextReadingOrder().execute(ctx, {"path": path}).data["lines"][0]["text"] == "Save"
    assert FindTextNearText().execute(ctx, {"path": path, "anchor": "Save"}).data["nearby"][0]["text"] == "Cancel"
    assert CountTextInImage().execute(ctx, {"path": path, "query": "Cancel"}).data["matching_lines"] == 1
    comparison = CompareImageText().execute(ctx, {"first_path": path, "second_path": str(second)})
    assert comparison.data["removed_lines"] == ["Cancel"]


def test_vision_actions_are_registered():
    names = create_action_registry(include_plugins=False).names()
    for name in ("resize_image", "convert_image_format", "find_text_in_image",
                 "get_image_text_summary", "inspect_image_file"):
        assert name in names
