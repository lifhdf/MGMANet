# 合成示例

本目录包含三张 320 × 240 的合成 PNG 图像、一个类别 `target`（ID 为 0）、对应标注及人为构造的预测。

这些文件用于演示 JSON 校验、reference AP 评估和 SVG 可视化。图像不是研究数据集，预测不是模型输出，评估结果不对应论文实验。

从项目根目录运行：

```bash
python -B -m mgmanet check-data --annotations examples/ground_truth.json --predictions examples/predictions.json
python -B -m mgmanet evaluate --annotations examples/ground_truth.json --predictions examples/predictions.json --iou 0.5,0.75 --output outputs/metrics.json
python -B -m mgmanet visualize --annotations examples/ground_truth.json --predictions examples/predictions.json --image-root examples/images --output-dir outputs/visualizations --show-ground-truth
```

输出目录由工具创建。`--show-ground-truth` 可省略，此时只显示预测框。SVG 内嵌示例图像，可在支持 SVG 的浏览器或查看器中打开。

修改数据时，应保持图像和类别引用一致，并使用位于图像范围内的 `[x, y, width, height]` 框。详见 [数据格式](../docs/data_format.md)。

预生成预览见 [preview/index.html](preview/index.html)，预期指标见 [expected_metrics.json](expected_metrics.json)。本合成示例在 IoU 0.5 和 0.75 时的 reference AP 分别为 0.9166666667 和 0.6666666667，均值为 0.7916666667；这些数字仅用于验证工具。
