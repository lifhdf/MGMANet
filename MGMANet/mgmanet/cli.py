"""Command-line interface for public pre-release utilities."""
import argparse
import json
import sys
from . import __version__
from .data import check_data, load_json, write_json
from .engine import predict, train
from .evaluation import evaluate
from .models import CoreNotReleasedError
from .visualization import render_visualizations


def _input_arguments(parser):
    parser.add_argument("--annotations", required=True, help="Ground-truth COCO-subset JSON")
    parser.add_argument("--predictions", required=True, help="Prediction list JSON (xywh boxes)")


def make_parser():
    parser = argparse.ArgumentParser(description="MGMANet public pre-release utilities; core model withheld")
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)
    validator = commands.add_parser("check-data", help="Validate annotations and prediction JSON")
    _input_arguments(validator)
    evaluator = commands.add_parser("evaluate", help="Evaluate existing predictions with reference AP")
    _input_arguments(evaluator)
    evaluator.add_argument("--iou", default="0.5", help="Comma-separated IoU thresholds, e.g. 0.5,0.75")
    evaluator.add_argument("--score-threshold", type=float, default=0.0)
    evaluator.add_argument("--output", help="Optional metrics JSON destination")
    visualizer = commands.add_parser("visualize", help="Render existing predictions to local SVG/HTML")
    _input_arguments(visualizer)
    visualizer.add_argument("--image-root", help="Optional directory containing PNG/JPEG backgrounds")
    visualizer.add_argument("--output-dir", default="outputs/visualizations")
    visualizer.add_argument("--score-threshold", type=float, default=0.25)
    visualizer.add_argument("--show-ground-truth", action="store_true")
    trainer = commands.add_parser("train", help="Reserved; training is not included")
    trainer.add_argument("--config", help="Reserved future configuration argument")
    predictor = commands.add_parser("predict", help="Reserved; model inference is not included")
    predictor.add_argument("--input", help="Reserved future image/video argument")
    return parser


def main(argv=None):
    parser = make_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "train":
            train(args.config)
            return 0
        if args.command == "predict":
            predict(args.input)
            return 0
        ground_truth, predictions = load_json(args.annotations), load_json(args.predictions)
        if args.command == "check-data":
            result = check_data(ground_truth, predictions)
        elif args.command == "evaluate":
            try:
                thresholds = [float(item.strip()) for item in args.iou.split(",")]
            except ValueError as error:
                raise ValueError("--iou must contain comma-separated numbers") from error
            result = evaluate(ground_truth, predictions, thresholds, args.score_threshold)
            if args.output:
                write_json(args.output, result)
        else:
            result = render_visualizations(ground_truth, predictions, args.output_dir,
                                           args.image_root, args.score_threshold, args.show_ground_truth)
        print(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False))
        return 0
    except CoreNotReleasedError as error:
        print(f"Not released: {error}", file=sys.stderr)
        return 2
    except (ValueError, OSError, OverflowError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
