"""Strict, dependency-free readers for the public reference data format."""
import json
import math
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath


@dataclass
class DetectionData:
    images: dict
    categories: dict
    annotations: list


def _integer(value, context, minimum=0):
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{context} must be an integer >= {minimum}")
    return value


def _number(value, context):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{context} must be a finite number")
    try:
        valid = math.isfinite(value)
    except (OverflowError, TypeError):
        valid = False
    if not valid:
        raise ValueError(f"{context} must be a finite number")
    return float(value)


def _object(value, context):
    if not isinstance(value, dict):
        raise ValueError(f"{context} must be an object")
    return value


def _list_field(value, key):
    result = value.get(key)
    if not isinstance(result, list):
        raise ValueError(f"{key} must be a list")
    return result


def _relative_filename(value, context):
    if not isinstance(value, str) or not value.strip() or "\\" in value:
        raise ValueError(f"{context} must be a non-empty relative path using '/' separators")
    posix, windows = PurePosixPath(value), PureWindowsPath(value)
    if posix.is_absolute() or windows.is_absolute() or windows.drive:
        raise ValueError(f"{context} must be relative")
    if any(part in ("", ".", "..") for part in value.split("/")):
        raise ValueError(f"{context} contains an unsafe path component")
    if any(ord(char) < 32 for char in value) or ":" in value:
        raise ValueError(f"{context} contains an unsafe character")
    return value


def _bbox(value, image, context):
    if not isinstance(value, list) or len(value) != 4:
        raise ValueError(f"{context} must be [x, y, width, height]")
    x, y, width, height = [_number(v, context) for v in value]
    if x < 0 or y < 0 or width <= 0 or height <= 0:
        raise ValueError(f"{context} requires x,y >= 0 and width,height > 0")
    if x + width > image["width"] + 1e-6 or y + height > image["height"] + 1e-6:
        raise ValueError(f"{context} extends beyond the image dimensions")
    return [x, y, width, height]


def validate_annotations(raw):
    """Validate a COCO-style subset; crowd/ignore semantics are unsupported."""
    _object(raw, "annotations document")
    images, categories, annotations = {}, {}, []
    filenames = set()
    for index, item in enumerate(_list_field(raw, "images")):
        context = f"images[{index}]"
        _object(item, context)
        image_id = _integer(item.get("id"), f"{context}.id")
        if image_id in images:
            raise ValueError(f"duplicate image id: {image_id}")
        filename = _relative_filename(item.get("file_name"), f"{context}.file_name")
        if filename in filenames:
            raise ValueError(f"duplicate image filename: {filename}")
        filenames.add(filename)
        images[image_id] = {
            "id": image_id, "file_name": filename,
            "width": _integer(item.get("width"), f"{context}.width", 1),
            "height": _integer(item.get("height"), f"{context}.height", 1),
        }
    for index, item in enumerate(_list_field(raw, "categories")):
        context = f"categories[{index}]"
        _object(item, context)
        category_id = _integer(item.get("id"), f"{context}.id")
        name = item.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"{context}.name must be a non-empty string")
        if category_id in categories:
            raise ValueError(f"duplicate category id: {category_id}")
        categories[category_id] = {"id": category_id, "name": name}
    annotation_ids = set()
    for index, item in enumerate(_list_field(raw, "annotations")):
        context = f"annotations[{index}]"
        _object(item, context)
        annotation_id = _integer(item.get("id"), f"{context}.id")
        if annotation_id in annotation_ids:
            raise ValueError(f"duplicate annotation id: {annotation_id}")
        annotation_ids.add(annotation_id)
        for flag in ("iscrowd", "ignore", "difficult"):
            if item.get(flag, 0) not in (0, False, None):
                raise ValueError(f"{context}.{flag}: crowd/ignore/difficult annotations are unsupported")
        image_id = _integer(item.get("image_id"), f"{context}.image_id")
        category_id = _integer(item.get("category_id"), f"{context}.category_id")
        if image_id not in images or category_id not in categories:
            raise ValueError(f"{context} references an unknown image or category")
        annotations.append({"id": annotation_id, "image_id": image_id,
                            "category_id": category_id,
                            "bbox": _bbox(item.get("bbox"), images[image_id], f"{context}.bbox")})
    return DetectionData(images, categories, annotations)


def validate_predictions(raw, dataset):
    if not isinstance(raw, list):
        raise ValueError("predictions must be a JSON list")
    predictions = []
    for index, item in enumerate(raw):
        context = f"predictions[{index}]"
        _object(item, context)
        image_id = _integer(item.get("image_id"), f"{context}.image_id")
        category_id = _integer(item.get("category_id"), f"{context}.category_id")
        if image_id not in dataset.images or category_id not in dataset.categories:
            raise ValueError(f"{context} references an unknown image or category")
        score = _number(item.get("score"), f"{context}.score")
        if not 0 <= score <= 1:
            raise ValueError(f"{context}.score must be in [0, 1]")
        predictions.append({"image_id": image_id, "category_id": category_id,
                            "bbox": _bbox(item.get("bbox"), dataset.images[image_id], f"{context}.bbox"),
                            "score": score})
    return predictions


def _reject_constant(value):
    raise ValueError(f"non-finite JSON constant is not permitted: {value}")


def load_json(filename):
    with Path(filename).open("r", encoding="utf-8-sig") as handle:
        return json.load(handle, parse_constant=_reject_constant)


def write_json(filename, value):
    destination = Path(filename)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")


def check_data(ground_truth, predictions):
    dataset = validate_annotations(ground_truth)
    checked = validate_predictions(predictions, dataset)
    return {"valid": True, "images": len(dataset.images),
            "categories": len(dataset.categories), "annotations": len(dataset.annotations),
            "predictions": len(checked), "bbox_format": "xywh"}
