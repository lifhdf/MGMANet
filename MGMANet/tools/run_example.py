"""Run the complete synthetic example; never loads the research model."""
import argparse
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Run validation, reference evaluation, and synthetic overlays")
    parser.add_argument("--output-dir", default="outputs/example")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    destination = Path(args.output_dir)
    if not destination.is_absolute():
        destination = root / destination
    common = ["--annotations", "examples/ground_truth.json", "--predictions", "examples/predictions.json"]
    commands = [
        ["check-data"] + common,
        ["evaluate"] + common + ["--iou", "0.5,0.75", "--output", str(destination / "metrics.json")],
        ["visualize"] + common + ["--image-root", "examples/images", "--output-dir",
                                  str(destination / "visualizations"), "--show-ground-truth"],
    ]
    for command in commands:
        completed = subprocess.run([sys.executable, "-B", "-m", "mgmanet"] + command, cwd=root)
        if completed.returncode:
            return completed.returncode
    print("Synthetic demonstration complete. No research-model inference was performed.")
    print(destination / "visualizations" / "index.html")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
