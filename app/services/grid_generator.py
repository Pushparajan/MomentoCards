import calendar
import os

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

CANVAS_SIZE = (1024, 1024)
MARGIN = 40
HEADER_HEIGHT = 80
WEEKDAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def _font(size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("DejaVuSans-Bold.ttf", size)
    except OSError:
        return ImageFont.load_default()


def draw_blank_grid(year: int, month: int, out_path: str) -> str:
    """Renders an exact, code-generated calendar grid (no AI) as the structural
    ground-truth that ControlNet will later be conditioned on."""
    img = Image.new("RGB", CANVAS_SIZE, "white")
    draw = ImageDraw.Draw(img)

    grid_top = MARGIN + HEADER_HEIGHT
    grid_bottom = CANVAS_SIZE[1] - MARGIN
    grid_left = MARGIN
    grid_right = CANVAS_SIZE[0] - MARGIN
    cols, rows = 7, 6
    cell_w = (grid_right - grid_left) / cols
    cell_h = (grid_bottom - grid_top) / rows

    header_font = _font(28)
    label_font = _font(18)
    day_font = _font(22)

    draw.text((grid_left, MARGIN), f"{calendar.month_name[month]} {year}", font=header_font, fill="black")

    for col, label in enumerate(WEEKDAY_LABELS):
        x = grid_left + col * cell_w
        draw.text((x + 6, grid_top - 26), label, font=label_font, fill="black")

    for r in range(rows + 1):
        y = grid_top + r * cell_h
        draw.line([(grid_left, y), (grid_right, y)], fill="black", width=3)
    for c in range(cols + 1):
        x = grid_left + c * cell_w
        draw.line([(x, grid_top), (x, grid_bottom)], fill="black", width=3)

    cal = calendar.Calendar(firstweekday=0)
    day_iter = cal.itermonthdays2(year, month)
    cells = list(day_iter)
    for idx, (day, weekday) in enumerate(cells[: cols * rows]):
        if day == 0:
            continue
        r, c = divmod(idx, cols)
        x = grid_left + c * cell_w + 6
        y = grid_top + r * cell_h + 6
        draw.text((x, y), str(day), font=day_font, fill="black")

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.save(out_path)
    return out_path


def to_canny(grid_path: str, out_path: str, low: int = 80, high: int = 160) -> str:
    """Converts the blank grid into a Canny edge map for the ControlNet Canny node."""
    image = cv2.imread(grid_path, cv2.IMREAD_GRAYSCALE)
    edges = cv2.Canny(image, low, high)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    cv2.imwrite(out_path, edges)
    return out_path


def grid_array(grid_path: str) -> np.ndarray:
    return np.array(Image.open(grid_path).convert("RGB"))
