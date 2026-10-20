# 评估约定

本工具计算检测任务的 **reference AP**，用于检查数据与外围评估流程。它不包含研究模型，也不复现论文评测。

## 匹配规则

每个 IoU 阈值独立评估，每个类别独立处理：

1. 按预测置信度从高到低处理预测。
2. 只在同一图像、同一类别内寻找尚未匹配的真值框。
3. 选择符合阈值的最佳 IoU 真值框；IoU 大于或等于阈值时可匹配。每个真值最多匹配一次。
4. 匹配成功记为真阳性，其余预测记为假阳性。对同一目标重复预测不会获得多次正确匹配。

边框采用连续坐标的 `[x, y, width, height]`。IoU 是交集面积除以并集面积，不使用像素索引的 `+1` 修正。

## AP 计算

对排序后的预测累计真阳性和假阳性，得到 precision 与 recall。AP 使用 all-points precision envelope：将 precision 包络调整为随 recall 增加而不升高，在 recall 改变的位置对包络面积求和。

该实现不是 11 点插值，也不是 COCO 官方评估流程。置信度相同时应保持输入顺序稳定；如需比较两次结果，应保持输入顺序一致。

## 多类别与多阈值

- 有真值、无正确预测的类别：AP 和 recall 为零。
- 无真值的类别：AP 和 recall 为 `null`，不参与类别均值。
- 没有任何可评估类别：`mean_ap` 为 `null`。
- 每个阈值分别计算类别均值；多个阈值的汇总仅称为 reference mean AP。

例如：

```bash
python -B -m mgmanet evaluate --annotations examples/ground_truth.json --predictions examples/predictions.json --iou 0.5,0.75 --output outputs/metrics.json
```

指定两个阈值不等同于运行 COCO 的完整阈值和评估约定。

## 范围限制

本工具不实现 crowd/ignore、COCO 面积分组或 maxDets 限制。输出不能标为 COCO 官方 mAP，不能直接与使用不同匹配、数据划分或评估约定的结果比较。示例数据与预测是人为构造的，输出只验证工具行为，不作为研究模型性能证据。

运行测试：

```bash
python -B -m unittest discover -s tests -v
```
