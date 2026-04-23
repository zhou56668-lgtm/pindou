# Creative PinDou 🎨

A web application that converts any image into a printable **Perler / Hama bead pattern**.
Upload an image → select a region → choose grid size → get a full color-coded pattern with PDF export.

---

## Features

- **Image Upload** — supports JPG, PNG, GIF
- **Region Selection** — drag to crop the target area on the image
- **Pixel Conversion** — quantizes colors to the official **Hama Midi color library (H01–H45)**
- **Color-coded Preview** — every cell shows its Hama color code (e.g. `H13`)
- **Bead List** — sorted material list with code, swatch, name and count
- **Step-by-Step Guide** — pattern split into 3-row steps with per-step color summary
- **PDF Export** — printable guide with preview, legend, coordinate grid and step pages
- **Max Colors Slider** — control how many bead colors are used (5–40)

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + TypeScript + Vite |
| Backend | Python 3.10 + FastAPI + Uvicorn |
| Image Processing | Pillow + NumPy (LAB color space matching) |
| PDF Generation | ReportLab |
| Color Matching | CIELAB ΔE nearest-neighbor + greedy color reduction |

---

## Project Structure

```
pindou/
├── backend/
│   ├── main.py             # FastAPI entry point
│   ├── palette.py          # Hama color library + LAB quantization
│   ├── image_processor.py  # Image pipeline (blur → resize → quantize → preview)
│   ├── step_planner.py     # Row-by-row step generator
│   ├── pdf_exporter.py     # PDF builder (ReportLab)
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── App.tsx                        # Main app layout & state
    │   ├── api.ts                         # Backend API client
    │   └── components/
    │       ├── ImageUploader.tsx          # Drag-and-drop upload
    │       ├── SelectionCanvas.tsx        # Mouse-drag region selector
    │       ├── GridPreview.tsx            # Preview image + legend + steps
    └── package.json
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+

### 1. Clone the repository

```bash
git clone https://github.com/zhou56668-lgtm/pindou.git
cd pindou
```

### 2. Start the Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

Backend runs at: `http://localhost:8000`

### 3. Start the Frontend

Open a new terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at: `http://localhost:xxxx`

### 4. Open in browser

```
http://localhost:xxxx
```

---

## Usage

| Step | Action |
|------|--------|
| ① | Click or drag an image into the upload area |
| ② | Drag to select a target region (optional — leave empty to use full image) |
| ③ | Choose grid size: **29×29**, **48×48**, or **58×58** |
| ④ | Adjust **Max Colors** slider (fewer = cleaner result) |
| ⑤ | Click **▶ Convert** |
| ⑥ | View the color-coded preview and bead list |
| ⑦ | Click **📄 Export PDF** to download the printable guide |

---

## Hama Color Library

The app uses 45 standard Hama Midi bead colors (H01–H45).
Each pixel is matched to the perceptually closest color using **CIELAB ΔE distance**, which is more accurate than RGB Euclidean distance.

---

## Team

Ji Shuyu · Zhou Hongjie · Yan Boxiang · Xiao Yuchen · Xia Yutong · Zhang Hanxi
