"""Self-contained SVG/HTML overlays for existing prediction files."""
import base64
import html
import struct
from pathlib import Path
from .data import _number, validate_annotations, validate_predictions


def _jpeg_dimensions(content):
    """Read the encoded JPEG size without adding an imaging dependency."""
    position = 2
    frame_markers = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
                     0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}
    while position < len(content):
        if content[position] != 0xFF:
            raise ValueError("invalid JPEG marker")
        while position < len(content) and content[position] == 0xFF:
            position += 1
        if position >= len(content):
            break
        marker = content[position]
        position += 1
        if marker in (0xDA, 0xD9):
            break
        if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
            continue
        if position + 2 > len(content):
            break
        length = int.from_bytes(content[position:position + 2], "big")
        if length < 2 or position + length > len(content):
            raise ValueError("truncated JPEG segment")
        if marker in frame_markers:
            if length < 8:
                raise ValueError("invalid JPEG frame header")
            height, width = struct.unpack(">HH", content[position + 3:position + 7])
            if not width or not height:
                raise ValueError("JPEG dimensions must be positive")
            return width, height
        position += length
    raise ValueError("JPEG frame dimensions were not found")


def _background(image, image_root):
    if image_root is None:
        return None
    root = Path(image_root).resolve()
    filename = (root / image["file_name"]).resolve()
    try:
        filename.relative_to(root)
    except ValueError as error:
        raise ValueError("image path escapes --image-root") from error
    if not filename.is_file():
        raise ValueError(f"image not found: {image['file_name']}")
    if filename.stat().st_size > 32 * 1024 * 1024:
        raise ValueError("background image exceeds the 32 MiB limit")
    content = filename.read_bytes()
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        mime = "image/png"
        if len(content) < 24:
            raise ValueError("truncated PNG image")
        width, height = struct.unpack(">II", content[16:24])
        if (width, height) != (image["width"], image["height"]):
            raise ValueError(f"PNG dimensions disagree with annotations: {image['file_name']}")
    elif content.startswith(b"\xff\xd8\xff"):
        mime = "image/jpeg"
        if _jpeg_dimensions(content) != (image["width"], image["height"]):
            raise ValueError(f"JPEG dimensions disagree with annotations: {image['file_name']}")
    else:
        raise ValueError("background images must be PNG or JPEG; SVG/HTML inputs are not accepted")
    return "data:" + mime + ";base64," + base64.b64encode(content).decode("ascii")


def _box(box, label, color, dashed=False):
    x, y, width, height = box
    dash = ' stroke-dasharray="5 3"' if dashed else ""
    safe_label = html.escape(label, quote=True)
    label_y = max(13.0, y - 4)
    return (f'<rect x="{x:g}" y="{y:g}" width="{width:g}" height="{height:g}" '
            f'fill="none" stroke="{color}" stroke-width="2"{dash}/>'
            f'<text x="{x:g}" y="{label_y:g}" fill="{color}" font-size="12" '
            f'font-family="Arial,sans-serif" paint-order="stroke" stroke="#111827" '
            f'stroke-width="3" stroke-linejoin="round">{safe_label}</text>')


def render_visualizations(ground_truth, predictions, output_dir, image_root=None,
                          score_threshold=0.25, show_ground_truth=False):
    """Draw existing detections, optionally embedding local raster images."""
    dataset = validate_annotations(ground_truth)
    checked = validate_predictions(predictions, dataset)
    cutoff = _number(score_threshold, "score_threshold")
    if not 0 <= cutoff <= 1:
        raise ValueError("score_threshold must be in [0, 1]")
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    gallery = []
    for image_id in sorted(dataset.images):
        image = dataset.images[image_id]
        width, height = image["width"], image["height"]
        safe_name = html.escape(image["file_name"], quote=True)
        layers = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height + 52}" '
                  f'viewBox="0 0 {width} {height + 52}">',
                  '<rect width="100%" height="100%" fill="#111827"/>',
                  f'<text x="10" y="20" fill="#f8fafc" font-size="13" '
                  f'font-family="Arial,sans-serif">{safe_name}</text>',
                  '<text x="10" y="39" fill="#cbd5e1" font-size="10" '
                  'font-family="Arial,sans-serif">Existing predictions | red: prediction | green: GT</text>',
                  '<g transform="translate(0,52)">',
                  f'<rect width="{width}" height="{height}" fill="#202833"/>']
        background = _background(image, image_root)
        if background is not None:
            layers.append(f'<image width="{width}" height="{height}" href="{background}"/>')
        if show_ground_truth:
            for annotation in dataset.annotations:
                if annotation["image_id"] == image_id:
                    name = dataset.categories[annotation["category_id"]]["name"]
                    layers.append(_box(annotation["bbox"], "GT " + name, "#34d399", True))
        for prediction in sorted(checked, key=lambda p: p["score"]):
            if prediction["image_id"] == image_id and prediction["score"] >= cutoff:
                name = dataset.categories[prediction["category_id"]]["name"]
                layers.append(_box(prediction["bbox"], f"{name} {prediction['score']:.2f}", "#fb7185"))
        layers.extend(["</g>", "</svg>"])
        filename = f"image_{image_id:06d}.svg"
        (destination / filename).write_text("\n".join(layers) + "\n", encoding="utf-8")
        gallery.append(f'<figure><a href="{filename}"><img src="{filename}" '
                       f'alt="{safe_name}" loading="lazy"/></a><figcaption>{safe_name}</figcaption></figure>')
    page = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>Prediction overlays</title><style>'
            'body{margin:32px;background:#0b1020;color:#e2e8f0;font:15px Arial,sans-serif}'
            'main{display:flex;flex-wrap:wrap;gap:20px}figure{margin:0}img{max-width:100%;height:auto;'
            'border:1px solid #334155;border-radius:10px}figcaption{margin:10px 0;color:#94a3b8}'
            '</style></head><body><h1>Saved prediction overlays</h1>'
            '<p>This tool renders existing prediction JSON. It does not run a model.</p><main>'
            + "".join(gallery) + '</main></body></html>')
    (destination / "index.html").write_text(page + "\n", encoding="utf-8")
    return {"images": len(gallery), "index": str(destination / "index.html"),
            "note": "No inference was performed."}
