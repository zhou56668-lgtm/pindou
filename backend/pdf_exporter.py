import io
import base64
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from PIL import Image as PILImage
import numpy as np


def _grid_to_pil(grid: list[list[dict]], cell_px: int = 10) -> PILImage.Image:
    h = len(grid)
    w = len(grid[0]) if h > 0 else 0
    arr = np.zeros((h * cell_px, w * cell_px, 3), dtype=np.uint8)
    for ri, row in enumerate(grid):
        for ci, cell in enumerate(row):
            arr[ri*cell_px:(ri+1)*cell_px, ci*cell_px:(ci+1)*cell_px] = [cell["r"], cell["g"], cell["b"]]
    return PILImage.fromarray(arr, "RGB")


def _grid_to_pil_highlighted(grid, steps_data, step_idx, cell_px=10):
    """Render grid with highlighted rows for a specific step."""
    h = len(grid)
    w = len(grid[0]) if h > 0 else 0
    arr = np.zeros((h * cell_px, w * cell_px, 3), dtype=np.uint8)
    step = steps_data[step_idx]
    active_rows = set(range(step["row_start"], step["row_end"] + 1))

    for ri, row in enumerate(grid):
        for ci, cell in enumerate(row):
            r, g, b = cell["r"], cell["g"], cell["b"]
            if ri not in active_rows:
                # Dim inactive rows
                r = int(r * 0.3 + 200 * 0.7)
                g = int(g * 0.3 + 200 * 0.7)
                b = int(b * 0.3 + 200 * 0.7)
            arr[ri*cell_px:(ri+1)*cell_px, ci*cell_px:(ci+1)*cell_px] = [r, g, b]

    return PILImage.fromarray(arr, "RGB")


def _grid_to_pil_coord(grid: list[list[dict]], cell_px: int = 12, label_px: int = 20) -> PILImage.Image:
    """Render grid as PIL image with row/col number labels along the edges."""
    from PIL import ImageDraw, ImageFont
    h = len(grid)
    w = len(grid[0]) if h > 0 else 0

    img_w = label_px + w * cell_px
    img_h = label_px + h * cell_px
    img = PILImage.new("RGB", (img_w, img_h), (240, 240, 240))
    draw = ImageDraw.Draw(img)

    # Try to load a small font; fall back to default
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size=max(8, cell_px - 2))
    except Exception:
        font = ImageFont.load_default()

    # Draw bead cells
    for ri, row in enumerate(grid):
        for ci, cell in enumerate(row):
            x0 = label_px + ci * cell_px
            y0 = label_px + ri * cell_px
            draw.rectangle([x0, y0, x0 + cell_px - 1, y0 + cell_px - 1],
                           fill=(cell["r"], cell["g"], cell["b"]))

    # Column numbers (every 5th column to avoid crowding)
    col_step = max(1, round(5 * 6 / cell_px))  # label every ~5 cells at default size
    for ci in range(w):
        if (ci + 1) % col_step == 0 or ci == 0:
            x = label_px + ci * cell_px + cell_px // 2
            draw.text((x, 2), str(ci + 1), fill=(80, 80, 80), font=font, anchor="mt")

    # Row numbers (every 5th row)
    row_step = max(1, round(5 * 6 / cell_px))
    for ri in range(h):
        if (ri + 1) % row_step == 0 or ri == 0:
            y = label_px + ri * cell_px + cell_px // 2
            draw.text((label_px - 2, y), str(ri + 1), fill=(80, 80, 80), font=font, anchor="rm")

    return img


def export_pdf(
    grid: list[list[dict]],
    bead_list: list[dict],
    steps: list[dict],
    grid_w: int,
    grid_h: int,
) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=15*mm, rightMargin=15*mm,
        topMargin=15*mm, bottomMargin=15*mm,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("title", parent=styles["Title"], fontSize=18, spaceAfter=6)
    h2_style = ParagraphStyle("h2", parent=styles["Heading2"], fontSize=13, spaceBefore=10, spaceAfter=4)
    normal = styles["Normal"]
    center_style = ParagraphStyle("center", parent=normal, alignment=TA_CENTER)

    story = []

    # --- Page 1: Title + Preview ---
    story.append(Paragraph("Creative PinDou — Bead Pattern", title_style))
    story.append(Paragraph(f"Grid size: {grid_w} × {grid_h}  |  Total beads: {grid_w * grid_h}", center_style))
    story.append(Spacer(1, 6*mm))

    preview_pil = _grid_to_pil(grid, cell_px=8)
    img_buf = io.BytesIO()
    preview_pil.save(img_buf, format="PNG")
    img_buf.seek(0)
    max_w = 160*mm
    max_h = 120*mm
    pw, ph = preview_pil.size
    scale = min(max_w / pw, max_h / ph)
    story.append(RLImage(img_buf, width=pw*scale, height=ph*scale))
    story.append(Spacer(1, 6*mm))

    # --- Page 2: Color Legend / Bead List ---
    story.append(Paragraph("Color Legend & Bead Count", h2_style))
    legend_data = [["Color", "Name", "Count"]]
    for item in bead_list:
        color_swatch = f'<font color="#{item["r"]:02x}{item["g"]:02x}{item["b"]:02x}">■■■</font>'
        legend_data.append([
            Paragraph(color_swatch, normal),
            item["name"],
            str(item["count"]),
        ])
    legend_table = Table(legend_data, colWidths=[20*mm, 60*mm, 25*mm])
    legend_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4A90D9")),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F5F5")]),
        ("GRID",       (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN",      (2, 0), (2, -1), "CENTER"),
    ]))
    story.append(legend_table)

    # --- Page 3+: Coordinate Grid ---
    story.append(Paragraph("Coordinate Grid", h2_style))
    story.append(Paragraph(
        "Row numbers on the left, column numbers on the top. Labels shown every 5 cells.",
        normal
    ))
    story.append(Spacer(1, 3*mm))

    # Choose cell_px so the grid fits within 160mm wide
    max_grid_px = int(160 * 3.7795)  # ~604px for 160mm at 96dpi equivalent
    label_px = 20
    cell_px = max(4, min(14, (max_grid_px - label_px) // grid_w))
    coord_pil = _grid_to_pil_coord(grid, cell_px=cell_px, label_px=label_px)
    cbuf = io.BytesIO()
    coord_pil.save(cbuf, format="PNG")
    cbuf.seek(0)
    cw, ch = coord_pil.size
    # Scale to fit page width (160mm)
    coord_scale = min(160*mm / cw, 250*mm / ch)
    story.append(RLImage(cbuf, width=cw * coord_scale, height=ch * coord_scale))

    # --- Step Pages ---
    story.append(Paragraph("Step-by-Step Guide", h2_style))
    story.append(Paragraph(
        "Each step covers 3 rows. Highlighted rows show the current step.",
        normal
    ))

    for i, step in enumerate(steps):
        story.append(Spacer(1, 4*mm))
        story.append(Paragraph(
            f"Step {step['step']}  (Rows {step['row_start']+1}–{step['row_end']+1})",
            h2_style
        ))

        step_pil = _grid_to_pil_highlighted(grid, steps, i, cell_px=8)
        sbuf = io.BytesIO()
        step_pil.save(sbuf, format="PNG")
        sbuf.seek(0)
        sw, sh = step_pil.size
        scale = min(max_w / sw, 80*mm / sh)
        story.append(RLImage(sbuf, width=sw*scale, height=sh*scale))

        # Color summary for this step
        color_counts: dict[str, int] = {}
        for cell in step["cells"]:
            color_counts[cell["name"]] = color_counts.get(cell["name"], 0) + 1
        summary = "  ".join(f'{name}: {cnt}' for name, cnt in sorted(color_counts.items()))
        story.append(Paragraph(f"Colors needed: {summary}", normal))

    doc.build(story)
    return buf.getvalue()
