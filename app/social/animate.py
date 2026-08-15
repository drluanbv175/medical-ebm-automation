"""Hiệu ứng "vẽ tay" (whiteboard draw-on) cho phong cách bảng trắng.

Ý tưởng (tự chứa, chỉ cần Pillow + numpy + ffmpeg):
- So sánh slide CUỐI với nền bảng trắng (giấy+khung+li) -> ra vùng "mực" (chữ/hình/doodle).
- Gom vùng mực thành các DẢI ngang (mỗi dòng chữ / mỗi hình = 1 dải), lộ dần TRÁI→PHẢI
  theo thứ tự trên→dưới -> giống đang viết/đang vẽ.
- Một CÂY BÚT (vẽ bằng PIL) chạy theo đầu nét. Cuối mỗi slide giữ hình đầy đủ một nhịp.

Khung hình được phát (yield) dạng numpy RGB để video.py bơm thẳng vào ffmpeg.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterator, List, Tuple

W, H = 1080, 1920
_INK_THRESHOLD = 22       # ngưỡng coi là "mực" so với nền
_ROW_GAP_MERGE = 16       # gộp các dòng mực cách nhau < ngưỡng px thành 1 dải


def _bg_array():
    """Nền bảng trắng (giấy + li + khung) trùng khít với _wb_canvas của render."""
    import numpy as np

    from app.social.render import _wb_canvas
    img, _ = _wb_canvas()
    return np.asarray(img.convert("RGB"))


def _marker_rgba(scale: float = 1.0):
    """Cây bút dạ (RGBA) — đầu bút ở GÓC DƯỚI-TRÁI (tip_offset)."""
    from PIL import Image, ImageDraw
    w, h = int(150 * scale), int(190 * scale)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    body = [(int(0.18 * w), int(0.12 * h)), (int(0.62 * w), int(0.0 * h)),
            (int(0.86 * w), int(0.30 * h)), (int(0.42 * w), int(0.42 * h))]
    d.polygon(body, fill=(45, 52, 70, 255))          # thân bút
    d.polygon([(int(0.42 * w), int(0.42 * h)), (int(0.30 * w), int(0.40 * h)),
               (int(0.07 * w), int(0.93 * h)), (int(0.16 * w), int(0.99 * h)),
               (int(0.20 * w), int(0.62 * h))], fill=(231, 168, 60, 255))  # phần gỗ
    d.polygon([(int(0.07 * w), int(0.93 * h)), (int(0.16 * w), int(0.99 * h)),
               (int(0.02 * w), int(1.0 * h))], fill=(40, 42, 54, 255))     # đầu nhọn
    tip = (int(0.02 * w), int(1.0 * h))
    return img, tip


def _content_bands(final_np, bg_np) -> List[Tuple[int, int, int, int]]:
    """Trả về các dải nội dung (y0, y1, x0, x1) theo thứ tự trên→dưới."""
    import numpy as np
    mask = np.abs(final_np.astype(np.int16) - bg_np.astype(np.int16)).max(axis=2) > _INK_THRESHOLD
    row_has = mask.any(axis=1)
    bands = []
    y = 0
    n = len(row_has)
    while y < n:
        if not row_has[y]:
            y += 1
            continue
        y0 = y
        gap = 0
        while y < n and (row_has[y] or gap < _ROW_GAP_MERGE):
            if row_has[y]:
                gap = 0
            else:
                gap += 1
            y += 1
        y1 = y - gap
        cols = mask[y0:y1].any(axis=0)
        xs = np.where(cols)[0]
        if len(xs):
            bands.append((y0, y1, int(xs[0]), int(xs[-1]) + 1))
    return bands


def slide_frames(final_path: Path, dur: float, fps: int = 25,
                 show_pen: bool = True) -> Iterator:
    """Sinh các khung RGB (numpy) cho 1 slide với hiệu ứng vẽ tay.

    dur: tổng thời lượng slide (giây) — khớp lời đọc. Giữ hình đầy đủ ~0.8s cuối.
    """
    import numpy as np
    from PIL import Image

    final_img = Image.open(final_path).convert("RGB").resize((W, H))
    final_np = np.asarray(final_img)
    bg_np = _bg_array()
    bands = _content_bands(final_np, bg_np)

    total = max(int(dur * fps), 1)
    hold = min(int(0.8 * fps), max(total - 1, 1))
    n_draw = max(total - hold, 1)

    if not bands:  # không có nội dung -> tĩnh
        for _ in range(total):
            yield final_np.copy()
        return

    widths = [max(b[3] - b[2], 1) for b in bands]
    cum = np.cumsum(widths)
    tot_w = int(cum[-1])

    pen_img, (tip_x, tip_y) = _marker_rgba()
    pen_np = np.asarray(pen_img)  # RGBA

    def _paste_pen(frame, px, py):
        ph, pw = pen_np.shape[:2]
        x0 = int(px - tip_x)
        y0 = int(py - tip_y)
        sx0, sy0 = max(0, -x0), max(0, -y0)
        dx0, dy0 = max(0, x0), max(0, y0)
        dx1, dy1 = min(W, x0 + pw), min(H, y0 + ph)
        if dx1 <= dx0 or dy1 <= dy0:
            return
        sw, sh = dx1 - dx0, dy1 - dy0
        sub = pen_np[sy0:sy0 + sh, sx0:sx0 + sw]
        alpha = sub[:, :, 3:4].astype(np.float32) / 255.0
        region = frame[dy0:dy1, dx0:dx1].astype(np.float32)
        frame[dy0:dy1, dx0:dx1] = (region * (1 - alpha) + sub[:, :, :3] * alpha).astype(np.uint8)

    for f in range(total):
        canvas = bg_np.copy()
        if f >= n_draw:  # nhịp giữ hình đầy đủ
            yield final_np.copy()
            continue
        pos = (f / n_draw) * tot_w
        # các dải đã xong
        j = int(np.searchsorted(cum, pos, side="right"))
        for k in range(min(j, len(bands))):
            y0, y1, x0, x1 = bands[k]
            canvas[y0:y1, x0:x1] = final_np[y0:y1, x0:x1]
        # dải đang vẽ
        if j < len(bands):
            y0, y1, x0, x1 = bands[j]
            prev = cum[j - 1] if j > 0 else 0
            frac = (pos - prev) / widths[j]
            xr = x0 + int(frac * (x1 - x0))
            if xr > x0:
                canvas[y0:y1, x0:xr] = final_np[y0:y1, x0:xr]
            if show_pen:
                _paste_pen(canvas, xr, (y0 + y1) // 2)
        yield canvas


def available() -> bool:
    try:
        import numpy  # noqa: F401
        import PIL  # noqa: F401
        return True
    except Exception:
        return False
