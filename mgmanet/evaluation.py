"""Reference object-detection AP; not the official COCO evaluator."""
import math
from .data import _number, validate_annotations, validate_predictions


def bbox_iou(first, second):
    """IoU for continuous [x, y, width, height] rectangles (no pixel +1)."""
    values = []
    for box in (first, second):
        if not isinstance(box, (list, tuple)) or len(box) != 4:
            raise ValueError("IoU boxes must each contain four xywh values")
        checked = [_number(v, "IoU box") for v in box]
        if checked[2] <= 0 or checked[3] <= 0:
            raise ValueError("IoU box dimensions must be positive")
        values.append(checked)
    a, b = values
    width = max(0.0, min(a[0] + a[2], b[0] + b[2]) - max(a[0], b[0]))
    height = max(0.0, min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1]))
    intersection = width * height
    union = a[2] * a[3] + b[2] * b[3] - intersection
    return intersection / union if union > 0 else 0.0


def _average_precision(recalls, precisions):
    """Integrate the monotonic precision envelope over recall changes."""
    extended_recall = [0.0] + recalls + [1.0]
    extended_precision = [0.0] + precisions + [0.0]
    for index in range(len(extended_precision) - 2, -1, -1):
        extended_precision[index] = max(extended_precision[index], extended_precision[index + 1])
    return sum((extended_recall[i] - extended_recall[i - 1]) * extended_precision[i]
               for i in range(1, len(extended_recall))
               if extended_recall[i] != extended_recall[i - 1])


def _class_result(dataset, predictions, category_id, threshold):
    ground_truth = [a for a in dataset.annotations if a["category_id"] == category_id]
    by_image = {}
    for index, annotation in enumerate(ground_truth):
        by_image.setdefault(annotation["image_id"], []).append((index, annotation["bbox"]))
    ranked = sorted((p for p in predictions if p["category_id"] == category_id),
                    key=lambda p: -p["score"])
    matched, recalls, precisions = set(), [], []
    tp = fp = 0
    for prediction in ranked:
        best_index, best_iou = None, -1.0
        for index, box in by_image.get(prediction["image_id"], []):
            if index in matched:
                continue
            overlap = bbox_iou(prediction["bbox"], box)
            if overlap > best_iou:
                best_index, best_iou = index, overlap
        if best_index is not None and best_iou >= threshold:
            matched.add(best_index)
            tp += 1
        else:
            fp += 1
        recalls.append(tp / len(ground_truth) if ground_truth else 0.0)
        precisions.append(tp / (tp + fp))
    num_gt, num_predictions = len(ground_truth), len(ranked)
    return {"category_id": category_id, "name": dataset.categories[category_id]["name"],
            "num_gt": num_gt, "num_predictions": num_predictions,
            "tp": tp, "fp": fp, "fn": num_gt - tp,
            "precision": tp / num_predictions if num_predictions else 0.0,
            "recall": tp / num_gt if num_gt else None,
            "ap": _average_precision(recalls, precisions) if num_gt else None}


def evaluate(ground_truth, predictions, iou_thresholds=(0.5,), score_threshold=0.0):
    """Evaluate existing prediction JSON. No model is loaded or executed.

    Mean AP excludes categories with zero GT. Tied confidence scores preserve
    JSON input order. A detection matches at most one GT of its own image/class.
    """
    dataset = validate_annotations(ground_truth)
    checked = validate_predictions(predictions, dataset)
    cutoff = _number(score_threshold, "score_threshold")
    if not 0 <= cutoff <= 1:
        raise ValueError("score_threshold must be in [0, 1]")
    if not isinstance(iou_thresholds, (tuple, list)) or not iou_thresholds:
        raise ValueError("iou_thresholds must be a non-empty list or tuple")
    thresholds = []
    for value in iou_thresholds:
        threshold = _number(value, "IoU threshold")
        if not 0 < threshold <= 1:
            raise ValueError("IoU thresholds must be in (0, 1]")
        if threshold in thresholds:
            raise ValueError("IoU thresholds must be unique")
        thresholds.append(threshold)
    selected = [p for p in checked if p["score"] >= cutoff]
    results = []
    for threshold in thresholds:
        classes = [_class_result(dataset, selected, category_id, threshold)
                   for category_id in sorted(dataset.categories)]
        aps = [result["ap"] for result in classes if result["ap"] is not None]
        results.append({"iou": threshold, "map": math.fsum(aps) / len(aps) if aps else None,
                        "per_class": classes})
    means = [result["map"] for result in results if result["map"] is not None]
    return {"schema_version": "1.0", "evaluation_type": "reference_all_points_ap",
            "bbox_format": "xywh", "score_threshold": cutoff,
            "num_images": len(dataset.images), "num_ground_truth": len(dataset.annotations),
            "num_predictions_input": len(checked), "num_predictions_evaluated": len(selected),
            "mean_ap": math.fsum(means) / len(means) if means else None,
            "thresholds": results,
            "note": "Reference utility only; not official COCO mAP or a reproduction of paper results."}
