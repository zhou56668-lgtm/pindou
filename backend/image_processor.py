import io
import base64
from PIL import Image, ImageFilter, ImageDraw, ImageFont
import numpy as np
from palette import quantize_to_palette

GRID_PRESETS = [29, 48, 58]


def _text_color(r: int, g: int, b: int) -> tuple[int, int, int]:
    """黑/白文字，保证在格子背景上可读。"""
    luminance = 0.299 * r + 0.587 * g + 0.114 * b
    return (0, 0, 0) if luminance > 140 else (255, 255, 255)


def process_image(
    image_bytes: bytes,
    grid_w: int,
    grid_h: int,
    crop: dict | None = None,
    max_colors: int = 20,
) -> dict:
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    # ── 1. 裁剪 ──────────────────────────────────────────────
    if crop:
        x, y, w, h = int(crop["x"]), int(crop["y"]), int(crop["w"]), int(crop["h"])
        x, y = max(0, x), max(0, y)
        x2, y2 = min(img.width, x + w), min(img.height, y + h)
        img = img.crop((x, y, x2, y2))

    # ── 2. 预处理：模糊去噪 ───────────────────────────────────
    factor = 4
    pre_w  = max(grid_w * factor, img.width)
    pre_h  = max(grid_h * factor, img.height)
    img    = img.resize((pre_w, pre_h), Image.LANCZOS)
    blur_r = max(1.0, pre_w / grid_w * 0.5)
    img    = img.filter(ImageFilter.GaussianBlur(radius=blur_r))
    img_small = img.resize((grid_w, grid_h), Image.LANCZOS)

    # ── 3. 颜色量化 → 含 code 字段的 grid ────────────────────
    grid, color_counts = quantize_to_palette(img_small, max_colors=max_colors)

    # ── 4. 生成带编号的预览图 ─────────────────────────────────
    CELL = 28          # 每格 28px，足够显示编号文字
    img_w = grid_w * CELL
    img_h = grid_h * CELL
    preview_img = Image.new("RGB", (img_w, img_h), (255, 255, 255))
    draw = ImageDraw.Draw(preview_img)

    font_size = max(7, CELL // 3)
    font = None
    for path in [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]:
        try:
            font = ImageFont.truetype(path, font_size)
            break
        except Exception:
            continue
    if font is None:
        font = ImageFont.load_default()

    for ri, row in enumerate(grid):
        for ci, cell_data in enumerate(row):
            x0, y0 = ci * CELL, ri * CELL
            x1, y1 = x0 + CELL - 1, y0 + CELL - 1
            r, g, b = cell_data["r"], cell_data["g"], cell_data["b"]
            code    = cell_data["code"]

            # 格子颜色 + 网格线
            draw.rectangle([x0, y0, x1, y1], fill=(r, g, b))
            draw.rectangle([x0, y0, x1, y1], outline=(150, 150, 150), width=1)

            # 编号文字居中
            tc   = _text_color(r, g, b)
            bbox = font.getbbox(code)
            tw   = bbox[2] - bbox[0]
            th   = bbox[3] - bbox[1]
            tx   = x0 + (CELL - tw) // 2
            ty   = y0 + (CELL - th) // 2
            draw.text((tx, ty), code, fill=tc, font=font)

    buf = io.BytesIO()
    preview_img.save(buf, format="PNG")
    preview_b64 = base64.b64encode(buf.getvalue()).decode()

    bead_list = sorted(color_counts.values(), key=lambda x: -x["count"])

    return {
        "grid": grid,
        "preview_b64": preview_b64,
        "bead_list": bead_list,
        "width": grid_w,
        "height": grid_h,
    }
