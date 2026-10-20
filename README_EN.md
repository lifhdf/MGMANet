# MGMANet: preliminary supporting tools

This package provides data validation, detection evaluation, visualization, and synthetic examples. **The research model, training implementation, inference implementation, and weights are not included. This is a preliminary release of supporting tools, cannot reproduce the paper's results, and does not establish that the research model has undergone public verification.**

The tools require Python 3.9 or later and use only the standard library. No PyTorch, GPU, or dataset download is required. All example images, annotations, and predictions are synthetic; the predictions are not model outputs and do not represent paper experiments.

## Run the examples

From this directory:

```bash
python -B -m mgmanet check-data --annotations examples/ground_truth.json --predictions examples/predictions.json
python -B -m mgmanet evaluate --annotations examples/ground_truth.json --predictions examples/predictions.json --iou 0.5,0.75 --output outputs/metrics.json
python -B -m mgmanet visualize --annotations examples/ground_truth.json --predictions examples/predictions.json --image-root examples/images --output-dir outputs/visualizations --show-ground-truth
```

Visualization produces SVG files. PNG/JPEG images are embedded when an image root is supplied; otherwise a blank canvas is used. Predictions are shown by default, with ground truth added by `--show-ground-truth`.

Equivalent scripts are available as `tools/check_data.py`, `tools/evaluate.py`, and `tools/visualize.py`, with the same arguments. Installation is optional: `python -m pip install -e .`. The distribution name is `mgmanet-public`.

## Release scope

Available functionality includes JSON validation, IoU-based reference AP evaluation, SVG rendering, synthetic examples, and tests of these supporting tools.

The following interfaces are intentionally unavailable and exit with status 2:

```bash
python -B -m mgmanet train --config configs/public_example.json
python -B -m mgmanet predict --input examples/images
```

The same applies to `tools/train.py` and `tools/predict.py`. The example configuration demonstrates the public interface only; it cannot start the research model.

## Evaluation contract

Boxes use COCO-style `[x, y, width, height]` coordinates. Predictions are matched one-to-one by category, confidence, and IoU threshold. **Reference AP** uses an all-points precision envelope. Multiple IoU thresholds are supported; their mean is only a reference summary defined by this tool.

Crowd/ignore handling, COCO area ranges, and maxDets rules are not implemented. Results must not be described as official COCO mAP or as a reproduction of the paper. Categories without ground truth have `null` AP and recall and are excluded from the mean; `mean_ap` is `null` when no category can be evaluated.

See [data format](docs/data_format.md) and [evaluation details](docs/evaluation.md).

## Test the supporting tools

```bash
python -B -m unittest discover -s tests -v
```

These tests cover only the released tools, not the unpublished research model.

## Future release and license

The research core is planned for release after paper acceptance and code preparation. Future release contents and version notes will determine what is actually available. See the [release plan](docs/release_plan.md).

The MIT license in [LICENSE](LICENSE) applies only to files included in this package. The unpublished research core is outside this release and is not licensed by it.

## Complete synthetic demo and integrity check

```bash
python -B tools/run_example.py
python -B tools/verify_release.py --strict
```

A pre-generated gallery is in [examples/preview/index.html](examples/preview/index.html). `PUBLIC_MANIFEST.json` records SHA-256 hashes of the public files, excluding the manifest itself. Verification checks file integrity, not research-model correctness or authorship. Strict verification rejects unlisted files except `.git/`, `outputs/`, and Python caches.
