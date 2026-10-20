# 数据格式

本包接收 JSON 标注文件和 JSON 预测文件。示例使用合成数据，仅用于验证外围工具的输入输出。

## 标注文件

顶层对象包含 `images`、`categories` 和 `annotations` 数组：

```json
{
  "images": [
    {"id": 1, "file_name": "sample.png", "width": 320, "height": 240}
  ],
  "categories": [
    {"id": 0, "name": "target"}
  ],
  "annotations": [
    {"id": 1, "image_id": 1, "category_id": 0, "bbox": [40, 50, 30, 20]}
  ]
}
```

- 图像、类别和标注的 ID 应为合法整数，各自不能重复。标注引用的图像和类别必须存在。
- 图像的 `width`、`height` 应为正整数；类别提供名称。
- `file_name` 使用相对路径和 POSIX 风格的 `/` 分隔符，例如 `sequence/frame.png`。不得使用绝对路径、反斜杠或越过图像根目录的路径。
- `bbox` 为四个有限数值，格式是 `[x, y, width, height]`，不是两个角点；宽高必须大于零，框必须位于对应图像范围内。
- 当前格式不支持 crowd/ignore 评估语义。

## 预测文件

顶层是数组，每项包含图像 ID、类别 ID、边框和置信度：

```json
[
  {"image_id": 1, "category_id": 0, "bbox": [42, 50, 30, 20], "score": 0.9}
]
```

图像和类别 ID 必须引用标注文件中的条目。框使用相同的 `xywh` 格式与范围约束。`score` 必须是 `[0, 1]` 内的有限数值。没有预测时使用空数组 `[]`。

## 校验

```bash
python -B -m mgmanet check-data --annotations examples/ground_truth.json --predictions examples/predictions.json
```

先通过校验，再进行评估或可视化。格式校验通过仅表示输入符合本工具约定，不说明预测来自某个模型，也不说明检测质量。

## 可视化的图像目录

`--image-root` 指定图像目录，程序根据每个图像条目的 `file_name` 查找 PNG/JPEG 并内嵌到输出 SVG。无图像目录时，使用标注中的宽高创建空白画布；框的坐标约定不变。

PNG/JPEG 的实际编码宽高必须与 JSON 一致，否则可视化会报错。带 EXIF 旋转信息的 JPEG 请先统一为正确朝向的像素图，再生成与之对应的标注；本工具不执行旋转或坐标转换。
