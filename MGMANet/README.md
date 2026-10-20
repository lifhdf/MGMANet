# MGMANet：预发布外围工具

本包公开数据校验、检测结果评估和可视化等外围实现，并提供合成示例。**研究核心模型、训练流程、推理流程和权重尚未公开；这不是完整模型开源版本，不能用于复现论文结果，也不代表核心模型已通过公开复核。**

当前代码仅使用 Python 标准库，要求 Python 3.9 或更高版本。运行本包无需安装 PyTorch，无需 GPU，也无需下载数据。示例图像、标注和预测均为合成数据，不是模型输出，不对应论文实验。

## 快速开始

可以先打开 [预生成的合成示例](examples/preview/index.html)，或一条命令运行整个示例：

```bash
python -B tools/run_example.py
```


在本目录运行：

```bash
python -B -m mgmanet check-data --annotations examples/ground_truth.json --predictions examples/predictions.json
python -B -m mgmanet evaluate --annotations examples/ground_truth.json --predictions examples/predictions.json --iou 0.5,0.75 --output outputs/metrics.json
python -B -m mgmanet visualize --annotations examples/ground_truth.json --predictions examples/predictions.json --image-root examples/images --output-dir outputs/visualizations --show-ground-truth
```

可视化生成 SVG 文件；提供图像目录时，PNG/JPEG 图像会内嵌到 SVG 中。不提供 `--image-root` 时使用空白画布。默认只绘制预测框，加入 `--show-ground-truth` 后同时显示真值框。

也可使用 `tools/check_data.py`、`tools/evaluate.py`、`tools/visualize.py`，参数与相应子命令一致。无需安装即可从本目录运行；如需安装，可选用 `python -m pip install -e .`，发行包名为 `mgmanet-public`。

## 当前可用与待发布内容

| 内容 | 当前状态 |
|---|---|
| JSON 数据校验 | 可用 |
| 基于 IoU 的 reference AP 评估 | 可用 |
| 检测框 SVG 可视化 | 可用 |
| 合成示例与外围工具测试 | 可用 |
| 研究核心模型、训练、推理、权重 | 未包含，待后续发布 |

以下命令保留接口，但当前会明确提示未实现并以状态码 2 退出：

```bash
python -B -m mgmanet train --config configs/public_example.json
python -B -m mgmanet predict --input examples/images
```

`tools/train.py` 和 `tools/predict.py` 具有相同边界。示例配置只用于展示公开接口，无法启动研究模型。

## 评估范围

所有检测框采用 COCO 风格的 `[x, y, width, height]`。评估按类别、置信度和 IoU 阈值进行一对一匹配，以 all-points precision envelope 计算 **reference AP**。支持单个或多个 IoU 阈值；多阈值均值仅是本工具定义的参考汇总值。

该评估不处理 crowd/ignore，不实现 COCO 的面积分组和 maxDets 规则，不能称为 COCO 官方 mAP，也不能代替论文评测流程。无真值的类别的 AP/recall 为 `null`，不参与均值；没有可评估类别时，`mean_ap` 为 `null`。

数据格式与评估细节见 [数据格式](docs/data_format.md) 和 [评估约定](docs/evaluation.md)。

## 验证外围工具

```bash
python -B -m unittest discover -s tests -v
```

测试仅覆盖本包的公开外围工具，不构成对未公开研究核心的验证。

## 后续发布与许可

计划在论文录用并完成整理后公开研究核心；以本仓库后续实际发布的文件和版本说明为准。阶段安排见 [发布计划](docs/release_plan.md)。

本包文件使用 MIT 许可，详见 [LICENSE](LICENSE)。该许可仅适用于当前包内实际提供的文件，未包含的研究核心不在此次发布与许可范围内。

English version: [README_EN.md](README_EN.md)

## 文件布局与完整性核对

```text
mgmanet/        数据校验、参考评估、可视化与未公开功能占位
tools/          命令行快捷入口、一键示例和文件校验
configs/        仅用于外围工具的公开示例配置
examples/       合成图像、JSON、预期指标与预生成预览
tests/          外围评估的独立测试
docs/           数据格式、评估约定和后续发布计划
PUBLIC_MANIFEST.json  本公开包文件的 SHA-256 清单
```

```bash
python -B tools/verify_release.py --strict
```

清单不包含它自身；校验仅检查本包文件完整性，不能证明未公开模型的效果或作者身份。`--strict` 额外检查未列入清单的文件（忽略 `.git/`、`outputs/` 和 Python 缓存）。
