"""Behavioral tests for the public, dependency-free detection evaluator."""

import copy
import unittest

from mgmanet.evaluation import bbox_iou, evaluate


def ground_truth(*, annotations=None, categories=None, images=None):
    """A small COCO-style fixture; bboxes are [x, y, width, height]."""
    return {
        "images": images if images is not None else [
            {"id": 1, "file_name": "frame.png", "width": 100, "height": 100}
        ],
        "categories": categories if categories is not None else [
            {"id": 0, "name": "target"}
        ],
        "annotations": annotations if annotations is not None else [
            {"id": 1, "image_id": 1, "category_id": 0, "bbox": [0, 0, 10, 10]}
        ],
    }


def prediction(bbox=None, score=0.9, category_id=0, image_id=1):
    return {
        "image_id": image_id,
        "category_id": category_id,
        "bbox": [0, 0, 10, 10] if bbox is None else bbox,
        "score": score,
    }


def class_result(result, category_id=0, threshold_index=0):
    return next(
        item for item in result["thresholds"][threshold_index]["per_class"]
        if item["category_id"] == category_id
    )


class EvaluationTests(unittest.TestCase):
    def test_iou_uses_continuous_xywh_coordinates(self):
        self.assertAlmostEqual(bbox_iou([0, 0, 10, 10], [0, 0, 5, 10]), 0.5)
        self.assertAlmostEqual(bbox_iou([0, 0, 10, 10], [5, 0, 10, 10]), 1 / 3)
        self.assertEqual(bbox_iou([0, 0, 10, 10], [10, 0, 10, 10]), 0.0)

    def test_perfect_prediction(self):
        result = evaluate(ground_truth(), [prediction()])
        item = class_result(result)
        self.assertEqual((item["tp"], item["fp"], item["fn"]), (1, 0, 0))
        self.assertEqual((item["num_gt"], item["num_predictions"]), (1, 1))
        self.assertEqual((item["precision"], item["recall"], item["ap"]), (1, 1, 1))
        self.assertEqual(result["mean_ap"], 1)

    def test_duplicate_detection_cannot_match_same_gt_twice(self):
        result = evaluate(ground_truth(), [prediction(score=0.9), prediction(score=0.8)])
        item = class_result(result)
        self.assertEqual((item["tp"], item["fp"], item["fn"]), (1, 1, 0))
        self.assertEqual((item["precision"], item["recall"]), (0.5, 1))
        self.assertEqual(item["ap"], 1)

    def test_ap_sorts_by_confidence_not_input_order(self):
        target = ground_truth()
        predictions = [prediction(score=0.5), prediction([30, 30, 10, 10], score=0.9)]
        before = copy.deepcopy(predictions)
        result = evaluate(target, predictions)
        self.assertEqual(class_result(result)["ap"], 0.5)
        self.assertEqual(predictions, before)
        predictions[0]["score"] = 0.95
        self.assertEqual(class_result(evaluate(target, predictions))["ap"], 1)

    def test_gt_without_predictions(self):
        result = evaluate(ground_truth(), [])
        item = class_result(result)
        self.assertEqual((item["tp"], item["fp"], item["fn"]), (0, 0, 1))
        self.assertEqual((item["precision"], item["recall"], item["ap"]), (0, 0, 0))
        self.assertEqual(result["mean_ap"], 0)

    def test_multiple_iou_thresholds_have_independent_matches(self):
        result = evaluate(
            ground_truth(), [prediction([0, 0, 6, 10])], iou_thresholds=(0.5, 0.75)
        )
        self.assertEqual([item["iou"] for item in result["thresholds"]], [0.5, 0.75])
        self.assertEqual([item["map"] for item in result["thresholds"]], [1, 0])
        self.assertEqual(class_result(result, threshold_index=0)["tp"], 1)
        self.assertEqual(class_result(result, threshold_index=1)["fn"], 1)
        self.assertEqual(result["mean_ap"], 0.5)

    def test_prediction_with_wrong_category_is_not_a_match(self):
        target = ground_truth(categories=[{"id": 0, "name": "target"}, {"id": 1, "name": "other"}])
        result = evaluate(target, [prediction(category_id=1)])
        self.assertEqual(class_result(result, 0)["fn"], 1)
        self.assertEqual(class_result(result, 0)["ap"], 0)
        self.assertEqual(class_result(result, 1)["fp"], 1)
        self.assertIsNone(class_result(result, 1)["ap"])
        self.assertIsNone(class_result(result, 1)["recall"])
        self.assertEqual(result["mean_ap"], 0)

    def test_category_without_gt_is_excluded_from_map(self):
        target = ground_truth(categories=[{"id": 0, "name": "target"}, {"id": 1, "name": "other"}])
        result = evaluate(target, [prediction(), prediction(category_id=1)])
        self.assertEqual(class_result(result, 1)["fp"], 1)
        self.assertIsNone(class_result(result, 1)["ap"])
        self.assertEqual(result["mean_ap"], 1)

    def test_predictions_never_match_gt_from_another_image(self):
        target = ground_truth(images=[
            {"id": 1, "file_name": "a.png", "width": 100, "height": 100},
            {"id": 2, "file_name": "b.png", "width": 100, "height": 100},
        ])
        item = class_result(evaluate(target, [prediction(image_id=2)]))
        self.assertEqual((item["tp"], item["fp"], item["fn"]), (0, 1, 1))
        self.assertEqual(item["ap"], 0)

    def test_one_prediction_can_match_only_one_of_two_gt(self):
        target = ground_truth(annotations=[
            {"id": 1, "image_id": 1, "category_id": 0, "bbox": [0, 0, 10, 10]},
            {"id": 2, "image_id": 1, "category_id": 0, "bbox": [0, 0, 10, 10]},
        ])
        item = class_result(evaluate(target, [prediction()]))
        self.assertEqual((item["tp"], item["fp"], item["fn"]), (1, 0, 1))
        self.assertEqual(item["recall"], 0.5)
        self.assertEqual(item["ap"], 0.5)  # All-point precision-envelope integral.

    def test_dataset_without_gt_has_undefined_map(self):
        target = ground_truth(annotations=[])
        for predictions in ([], [prediction()]):
            with self.subTest(predictions=predictions):
                result = evaluate(target, predictions)
                item = class_result(result)
                self.assertIsNone(item["ap"])
                self.assertIsNone(item["recall"])
                self.assertIsNone(result["thresholds"][0]["map"])
                self.assertIsNone(result["mean_ap"])
                self.assertEqual(item["fp"], len(predictions))

    def test_iou_and_score_threshold_boundaries_are_inclusive(self):
        target = ground_truth()
        preds = [prediction([0, 0, 5, 10], score=0.7)]
        result = evaluate(target, preds, iou_thresholds=(0.5, 0.500001), score_threshold=0.7)
        self.assertEqual(class_result(result, threshold_index=0)["tp"], 1)
        self.assertEqual(class_result(result, threshold_index=1)["fp"], 1)
        filtered = evaluate(target, preds, score_threshold=0.700001)
        self.assertEqual(class_result(filtered)["num_predictions"], 0)

    def test_score_filter_applies_before_metric_counts(self):
        preds = [prediction([30, 30, 10, 10], score=0.2), prediction(score=0.8)]
        item = class_result(evaluate(ground_truth(), preds, score_threshold=0.5))
        self.assertEqual((item["num_predictions"], item["tp"], item["fp"]), (1, 1, 0))
        self.assertEqual(item["ap"], 1)

    def test_nonfinite_values_and_out_of_range_scores_are_rejected(self):
        for score in (float("nan"), float("inf"), float("-inf"), -0.01, 1.01):
            with self.subTest(score=score):
                with self.assertRaises(ValueError):
                    evaluate(ground_truth(), [prediction(score=score)])
        for value in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(coordinate=value):
                with self.assertRaises(ValueError):
                    evaluate(ground_truth(), [prediction([value, 0, 10, 10])])
                target = ground_truth()
                target["annotations"][0]["bbox"] = [0, 0, value, 10]
                with self.assertRaises(ValueError):
                    evaluate(target, [])

    def test_malformed_or_out_of_image_boxes_are_rejected(self):
        boxes = ([0, 0, 10], [0, 0, 10, 10, 0], [0, 0, 0, 10],
                 [0, 0, 10, -1], [-1, 0, 10, 10], [95, 0, 10, 10])
        for box in boxes:
            with self.subTest(box=box):
                with self.assertRaises(ValueError):
                    evaluate(ground_truth(), [prediction(list(box))])
                target = ground_truth()
                target["annotations"][0]["bbox"] = list(box)
                with self.assertRaises(ValueError):
                    evaluate(target, [])

    def test_unsupported_crowd_or_ignore_annotations_are_rejected(self):
        for field in ("iscrowd", "ignore"):
            with self.subTest(field=field):
                target = ground_truth()
                target["annotations"][0][field] = 1
                with self.assertRaises(ValueError):
                    evaluate(target, [])


if __name__ == "__main__":
    unittest.main()
