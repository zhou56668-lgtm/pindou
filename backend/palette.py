# Hama Midi Bead Color Library
# Official Hama color codes with RGB values
# Format: (code, name, R, G, B)
# Source: Hama official color chart (Midi bead series)

PALETTE = [
    # code   name                    R    G    B
    ("H01",  "White",              255, 255, 255),
    ("H02",  "Cream",              255, 246, 200),
    ("H03",  "Yellow",             255, 221,   0),
    ("H04",  "Orange",             255, 138,   0),
    ("H05",  "Red",                220,  20,  40),
    ("H06",  "Dark Red",           160,   0,  30),
    ("H07",  "Pink",               255, 176, 196),
    ("H08",  "Light Pink",         255, 210, 220),
    ("H09",  "Purple",             130,  50, 150),
    ("H10",  "Lavender",           190, 160, 210),
    ("H11",  "Light Blue",         160, 210, 235),
    ("H12",  "Sky Blue",           100, 185, 230),
    ("H13",  "Blue",                30, 100, 200),
    ("H14",  "Dark Blue",           10,  40, 130),
    ("H15",  "Navy",                10,  20,  80),
    ("H16",  "Light Green",        180, 225, 140),
    ("H17",  "Green",               60, 170,  70),
    ("H18",  "Dark Green",          10, 100,  40),
    ("H19",  "Olive",              120, 130,  60),
    ("H20",  "Brown",              140,  80,  30),
    ("H21",  "Light Brown",        200, 155, 100),
    ("H22",  "Beige",              240, 220, 180),
    ("H23",  "Peach",              255, 200, 160),
    ("H24",  "Salmon",             240, 130, 110),
    ("H25",  "Coral",              255, 110,  80),
    ("H26",  "Gold",               230, 185,  30),
    ("H27",  "Light Gray",         210, 210, 210),
    ("H28",  "Gray",               140, 140, 140),
    ("H29",  "Dark Gray",           70,  70,  70),
    ("H30",  "Black",                0,   0,   0),
    ("H31",  "Silver",             195, 195, 200),
    ("H32",  "Turquoise",           50, 200, 190),
    ("H33",  "Teal",                 0, 130, 130),
    ("H34",  "Cyan",                 0, 210, 230),
    ("H35",  "Mint",               180, 240, 200),
    ("H36",  "Lime",               180, 220,  50),
    ("H37",  "Yellow Green",       160, 200,  60),
    ("H38",  "Magenta",            220,  40, 160),
    ("H39",  "Hot Pink",           255,  60, 150),
    ("H40",  "Violet",              90,  30, 130),
    ("H41",  "Indigo",              60,  40, 140),
    ("H42",  "Maroon",             120,  20,  40),
    ("H43",  "Tan",                210, 175, 125),
    ("H44",  "Khaki",              195, 180, 120),
    ("H45",  "Sand",               230, 210, 165),
]

import numpy as np
from PIL import Image

# ── LAB 色彩空间转换 ─────────────────────────────────────────
def _rgb_to_lab(rgb_array: np.ndarray) -> np.ndarray:
    """Convert Nx3 float32 array (0-255) to CIELAB."""
    rgb = rgb_array.astype(np.float32) / 255.0
    # sRGB → linear
    mask = rgb > 0.04045
    rgb[mask] = ((rgb[mask] + 0.055) / 1.055) ** 2.4
    rgb[~mask] = rgb[~mask] / 12.92
    # linear RGB → XYZ D65
    M = np.array([
        [0.4124564, 0.3575761, 0.1804375],
        [0.2126729, 0.7151522, 0.0721750],
        [0.0193339, 0.1191920, 0.9503041],
    ], dtype=np.float32)
    xyz = rgb @ M.T
    xyz[:, 0] /= 0.95047
    xyz[:, 2] /= 1.08883
    # XYZ → LAB
    eps, kappa = 0.008856, 903.3
    f = np.where(xyz > eps, np.cbrt(xyz), (kappa * xyz + 16.0) / 116.0)
    L = 116.0 * f[:, 1] - 16.0
    a = 500.0 * (f[:, 0] - f[:, 1])
    b = 200.0 * (f[:, 1] - f[:, 2])
    return np.stack([L, a, b], axis=1)


# 预计算调色板数据
_palette_codes = [code for code, *_ in PALETTE]
_palette_names = [name for _, name, *_ in PALETTE]
_palette_rgb   = np.array([[r, g, b] for _, _, r, g, b in PALETTE], dtype=np.float32)
_palette_lab   = _rgb_to_lab(_palette_rgb.copy())


def _batch_nearest_lab(pixels_lab: np.ndarray, allowed_indices: np.ndarray) -> np.ndarray:
    """Vectorised nearest-palette-color in LAB space."""
    palette_sub = _palette_lab[allowed_indices]
    diff = pixels_lab[:, np.newaxis, :] - palette_sub[np.newaxis, :, :]
    dists = np.sum(diff ** 2, axis=2)
    local_idx = np.argmin(dists, axis=1)
    return allowed_indices[local_idx]


def quantize_to_palette(
    img_small: Image.Image,
    max_colors: int = 20,
) -> tuple[list[list[dict]], dict]:
    """
    Map every pixel → nearest Hama palette color (in LAB space),
    then greedily merge until ≤ max_colors colors are used.
    Returns (grid, color_counts).
    Each cell: {code, name, r, g, b}
    """
    pixels_rgb = np.array(img_small, dtype=np.float32).reshape(-1, 3)
    pixels_lab = _rgb_to_lab(pixels_rgb.copy())

    # Step 1: full palette match
    all_indices = np.arange(len(PALETTE))
    global_idx  = _batch_nearest_lab(pixels_lab, all_indices)

    # Step 2: greedy color reduction
    used = np.unique(global_idx)
    while len(used) > max_colors:
        counts    = {u: int(np.sum(global_idx == u)) for u in used}
        rarest    = min(counts, key=lambda u: counts[u])
        remaining = used[used != rarest]
        mask      = global_idx == rarest
        if mask.any():
            global_idx[mask] = _batch_nearest_lab(pixels_lab[mask], remaining)
        used = remaining

    # Step 3: build grid + counts
    H, W = img_small.height, img_small.width
    grid_flat   = global_idx.reshape(H, W)
    grid        = []
    color_counts: dict[str, dict] = {}

    for ri in range(H):
        row = []
        for ci in range(W):
            idx  = int(grid_flat[ri, ci])
            code = _palette_codes[idx]
            name = _palette_names[idx]
            r    = int(_palette_rgb[idx][0])
            g    = int(_palette_rgb[idx][1])
            b    = int(_palette_rgb[idx][2])
            row.append({"code": code, "name": name, "r": r, "g": g, "b": b})
            if code not in color_counts:
                color_counts[code] = {"code": code, "name": name, "r": r, "g": g, "b": b, "count": 0}
            color_counts[code]["count"] += 1
        grid.append(row)

    return grid, color_counts


def get_palette_list() -> list[dict]:
    return [
        {"code": code, "name": name, "r": r, "g": g, "b": b}
        for code, name, r, g, b in PALETTE
    ]
