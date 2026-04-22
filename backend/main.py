from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
import json

from image_processor import process_image, GRID_PRESETS
from step_planner import plan_steps
from pdf_exporter import export_pdf
from palette import get_palette_list

app = FastAPI(title="PinDou API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173",
                   "http://localhost:5174", "http://127.0.0.1:5174"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/palette")
def get_palette():
    return get_palette_list()


@app.get("/grid-presets")
def grid_presets():
    return [{"size": s, "label": f"{s}×{s}"} for s in GRID_PRESETS]


@app.post("/convert")
async def convert(
    file: UploadFile = File(...),
    grid_w: int = Form(29),
    grid_h: int = Form(29),
    crop: str = Form(None),
    max_colors: int = Form(20),
):
    if file.content_type not in ("image/jpeg", "image/png", "image/gif", "image/webp"):
        raise HTTPException(400, "Unsupported image type")

    image_bytes = await file.read()
    crop_dict = json.loads(crop) if crop else None

    result = process_image(image_bytes, grid_w, grid_h, crop=crop_dict, max_colors=max_colors)
    steps = plan_steps(result["grid"])

    return {
        "preview_b64": result["preview_b64"],
        "bead_list": result["bead_list"],
        "grid": result["grid"],
        "steps": steps,
        "width": result["width"],
        "height": result["height"],
    }


@app.post("/export-pdf")
async def export_pdf_endpoint(
    file: UploadFile = File(...),
    grid_w: int = Form(29),
    grid_h: int = Form(29),
    crop: str = Form(None),
    max_colors: int = Form(20),
):
    if file.content_type not in ("image/jpeg", "image/png", "image/gif", "image/webp"):
        raise HTTPException(400, "Unsupported image type")

    image_bytes = await file.read()
    crop_dict = json.loads(crop) if crop else None

    result = process_image(image_bytes, grid_w, grid_h, crop=crop_dict, max_colors=max_colors)
    steps = plan_steps(result["grid"])
    pdf_bytes = export_pdf(
        result["grid"],
        result["bead_list"],
        steps,
        result["width"],
        result["height"],
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=pattern.pdf"},
    )
