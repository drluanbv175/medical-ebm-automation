"""Bộ doodle y khoa vẽ tay (line-art) bằng Pillow — KHÔNG cần tải ảnh ngoài.

Mỗi doodle là một hàm vẽ nét mực vào ImageDraw tại tâm (cx, cy) trong khung ~size,
ăn khớp phong cách "bảng trắng viết tay". Có bản đồ chủ đề -> doodle để hệ thống tự
chèn 1–2 hình hợp chủ đề lên slide.
"""
from __future__ import annotations

import math
from typing import Callable, Dict, List


def _poly(d, pts, color, w):
    if len(pts) > 1:
        d.line(list(pts) + [pts[0]], fill=color, width=w, joint="curve")


def _curve(d, pts, color, w):
    if len(pts) > 1:
        d.line(list(pts), fill=color, width=w, joint="curve")


# --- Tim mạch -------------------------------------------------------------
def heart(d, cx, cy, s, color, w=6):
    pts = []
    for i in range(0, 361, 6):
        t = math.radians(i)
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((cx + x * s / 34, cy - y * s / 34))
    _poly(d, pts, color, w)


def ecg(d, cx, cy, s, color, w=6):
    x0, x1 = cx - s / 2, cx + s / 2
    pts = [(x0, cy), (cx - s * 0.22, cy), (cx - s * 0.15, cy + s * 0.08),
           (cx - s * 0.08, cy - s * 0.42), (cx, cy + s * 0.30), (cx + s * 0.06, cy),
           (cx + s * 0.2, cy), (x1, cy)]
    _curve(d, pts, color, w)


# --- Thận / Tiết niệu -----------------------------------------------------
def kidney(d, cx, cy, s, color, w=6):
    pts = []
    for i in range(0, 361, 8):
        t = math.radians(i)
        r = s * 0.34 * (1 - 0.32 * math.cos(t) ** 2)
        x = r * math.sin(t)
        y = r * math.cos(t) * 1.15 + (s * 0.10 if math.sin(t) > 0 else 0) * 0
        # tạo vết lõm bên trong
        if -0.3 < math.sin(t) < 0.3 and math.cos(t) > 0:
            x *= 0.55
        pts.append((cx + x, cy - y))
    _poly(d, pts, color, w)


def droplet(d, cx, cy, s, color, w=6):
    pts = [(cx, cy - s * 0.5)]
    for a in range(-50, 231, 8):
        ang = math.radians(a)
        pts.append((cx + s * 0.32 * math.cos(ang), cy + s * 0.14 + s * 0.32 * math.sin(ang)))
    _poly(d, pts, color, w)


# --- Hô hấp ---------------------------------------------------------------
def lungs(d, cx, cy, s, color, w=6):
    d.line([(cx, cy - s * 0.45), (cx, cy - s * 0.05)], fill=color, width=w)  # khí quản
    d.line([(cx, cy - s * 0.18), (cx - s * 0.12, cy - s * 0.05)], fill=color, width=w)
    d.line([(cx, cy - s * 0.18), (cx + s * 0.12, cy - s * 0.05)], fill=color, width=w)
    for sgn in (-1, 1):
        pts = []
        for a in range(0, 181, 12):
            ang = math.radians(a)
            x = sgn * (s * 0.12 + s * 0.2 * math.sin(ang))
            y = -s * 0.05 + s * 0.4 * (a / 180)
            pts.append((cx + x, cy + y))
        pts.append((cx + sgn * s * 0.12, cy - s * 0.02))
        _curve(d, pts, color, w)


def brain(d, cx, cy, s, color, w=6):
    pts = []
    for i in range(0, 361, 10):
        t = math.radians(i)
        r = s * 0.34 * (1 + 0.14 * math.sin(5 * t))  # gợn nếp nhăn
        pts.append((cx + r * math.cos(t), cy + r * math.sin(t) * 0.92))
    _poly(d, pts, color, w)
    d.line([(cx, cy - s * 0.3), (cx, cy + s * 0.3)], fill=color, width=max(w - 2, 2))


# --- Tiêu hoá / Gan -------------------------------------------------------
def stomach(d, cx, cy, s, color, w=6):
    pts = [(cx - s * 0.18, cy - s * 0.4), (cx + s * 0.16, cy - s * 0.34),
           (cx + s * 0.28, cy), (cx + s * 0.16, cy + s * 0.34),
           (cx - s * 0.14, cy + s * 0.34), (cx - s * 0.26, cy + s * 0.05),
           (cx - s * 0.1, cy - s * 0.05), (cx - s * 0.12, cy - s * 0.2)]
    _curve(d, pts, color, w)
    d.line([(cx - s * 0.18, cy - s * 0.4), (cx - s * 0.34, cy - s * 0.5)],
           fill=color, width=w)


def liver(d, cx, cy, s, color, w=6):
    pts = [(cx - s * 0.4, cy - s * 0.18), (cx + s * 0.4, cy - s * 0.28),
           (cx + s * 0.34, cy + s * 0.22), (cx - s * 0.34, cy + s * 0.2)]
    _poly(d, pts, color, w)
    d.line([(cx + s * 0.05, cy - s * 0.24), (cx + s * 0.05, cy + s * 0.2)],
           fill=color, width=max(w - 2, 2))


def bone(d, cx, cy, s, color, w=6):
    d.line([(cx - s * 0.28, cy - s * 0.18), (cx + s * 0.28, cy + s * 0.18)],
           fill=color, width=w)
    for ex, ey in ((cx - s * 0.28, cy - s * 0.18), (cx + s * 0.28, cy + s * 0.18)):
        dx = s * 0.1 if ex < cx else -s * 0.1
        d.ellipse([ex - s * 0.12, ey - s * 0.12, ex + s * 0.06, ey + s * 0.06],
                  outline=color, width=w)
        d.ellipse([ex - s * 0.06 + dx, ey - s * 0.06 - s * 0.06, ex + s * 0.12 + dx,
                   ey + s * 0.12 - s * 0.06], outline=color, width=w)


# --- Thuốc ----------------------------------------------------------------
def capsule(d, cx, cy, s, color, w=6):
    d.rounded_rectangle([cx - s * 0.4, cy - s * 0.16, cx + s * 0.4, cy + s * 0.16],
                        radius=s * 0.16, outline=color, width=w)
    d.line([(cx, cy - s * 0.16), (cx, cy + s * 0.16)], fill=color, width=w)


def pill(d, cx, cy, s, color, w=6):
    d.ellipse([cx - s * 0.3, cy - s * 0.3, cx + s * 0.3, cy + s * 0.3],
              outline=color, width=w)
    d.line([(cx - s * 0.21, cy - s * 0.21), (cx + s * 0.21, cy + s * 0.21)],
           fill=color, width=max(w - 2, 2))


def syringe(d, cx, cy, s, color, w=6):
    d.line([(cx - s * 0.45, cy), (cx + s * 0.45, cy)], fill=color, width=w)  # trục
    d.rounded_rectangle([cx - s * 0.25, cy - s * 0.12, cx + s * 0.2, cy + s * 0.12],
                        radius=s * 0.04, outline=color, width=w)  # thân
    d.line([(cx - s * 0.25, cy - s * 0.18), (cx - s * 0.25, cy + s * 0.18)],
           fill=color, width=w)  # pít-tông
    for i in range(1, 4):  # vạch
        x = cx - s * 0.25 + i * s * 0.11
        d.line([(x, cy - s * 0.06), (x, cy + s * 0.06)], fill=color, width=max(w - 3, 2))


# --- Nhiễm khuẩn ----------------------------------------------------------
def microbe(d, cx, cy, s, color, w=6):
    r = s * 0.26
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=w)
    for a in range(0, 360, 45):
        ang = math.radians(a)
        x0, y0 = cx + r * math.cos(ang), cy + r * math.sin(ang)
        d.line([(x0, y0), (x0 + s * 0.12 * math.cos(ang), y0 + s * 0.12 * math.sin(ang))],
               fill=color, width=max(w - 2, 2))
    d.ellipse([cx - s * 0.06, cy - s * 0.06, cx, cy], outline=color, width=max(w - 3, 2))
    d.ellipse([cx + s * 0.03, cy + s * 0.02, cx + s * 0.09, cy + s * 0.08],
              outline=color, width=max(w - 3, 2))


# --- Chẩn đoán / thống kê / chung -----------------------------------------
def stethoscope(d, cx, cy, s, color, w=6):
    pts = [(cx - s * 0.32, cy - s * 0.4), (cx - s * 0.34, cy), (cx - s * 0.1, cy + s * 0.2),
           (cx + s * 0.1, cy + s * 0.2), (cx + s * 0.12, cy)]
    _curve(d, pts, color, w)
    d.line([(cx + s * 0.12, cy), (cx + s * 0.12, cy + s * 0.22)], fill=color, width=w)
    d.ellipse([cx + s * 0.02, cy + s * 0.22, cx + s * 0.22, cy + s * 0.42],
              outline=color, width=w)
    d.line([(cx - s * 0.32, cy - s * 0.4), (cx - s * 0.24, cy - s * 0.46)],
           fill=color, width=w)


def bars(d, cx, cy, s, color, w=6):
    d.line([(cx - s * 0.4, cy + s * 0.35), (cx + s * 0.4, cy + s * 0.35)], fill=color, width=w)
    d.line([(cx - s * 0.4, cy + s * 0.35), (cx - s * 0.4, cy - s * 0.4)], fill=color, width=w)
    hs = [0.25, 0.5, 0.38, 0.65]
    for i, h in enumerate(hs):
        x = cx - s * 0.28 + i * s * 0.18
        d.rectangle([x, cy + s * 0.35 - s * h, x + s * 0.1, cy + s * 0.35],
                    outline=color, width=max(w - 2, 2))


def trend_up(d, cx, cy, s, color, w=6):
    d.line([(cx - s * 0.4, cy + s * 0.35), (cx + s * 0.4, cy + s * 0.35)], fill=color, width=w)
    d.line([(cx - s * 0.4, cy + s * 0.35), (cx - s * 0.4, cy - s * 0.4)], fill=color, width=w)
    pts = [(cx - s * 0.32, cy + s * 0.2), (cx - s * 0.1, cy - s * 0.02),
           (cx + s * 0.05, cy + s * 0.08), (cx + s * 0.34, cy - s * 0.32)]
    _curve(d, pts, color, w)
    d.line([(cx + s * 0.34, cy - s * 0.32), (cx + s * 0.18, cy - s * 0.3)], fill=color, width=w)
    d.line([(cx + s * 0.34, cy - s * 0.32), (cx + s * 0.3, cy - s * 0.16)], fill=color, width=w)


def magnifier(d, cx, cy, s, color, w=6):
    r = s * 0.26
    d.ellipse([cx - r - s * 0.08, cy - r - s * 0.08, cx + r - s * 0.08, cy + r - s * 0.08],
              outline=color, width=w)
    d.line([(cx + r * 0.5 - s * 0.08, cy + r * 0.5 - s * 0.08),
            (cx + s * 0.34, cy + s * 0.34)], fill=color, width=w + 1)


def question(d, cx, cy, s, color, w=6):
    pts = []
    for a in range(150, -110, -12):
        ang = math.radians(a)
        pts.append((cx + s * 0.2 * math.cos(ang), cy - s * 0.18 + s * 0.2 * math.sin(ang)))
    pts.append((cx, cy + s * 0.06))
    pts.append((cx, cy + s * 0.16))
    _curve(d, pts, color, w)
    d.ellipse([cx - s * 0.04, cy + s * 0.3, cx + s * 0.04, cy + s * 0.38],
              fill=color)


def warning(d, cx, cy, s, color, w=6):
    pts = [(cx, cy - s * 0.42), (cx + s * 0.42, cy + s * 0.34), (cx - s * 0.42, cy + s * 0.34)]
    _poly(d, pts, color, w)
    d.line([(cx, cy - s * 0.12), (cx, cy + s * 0.12)], fill=color, width=w)
    d.ellipse([cx - s * 0.035, cy + s * 0.2, cx + s * 0.035, cy + s * 0.27], fill=color)


def clipboard(d, cx, cy, s, color, w=6):
    d.rounded_rectangle([cx - s * 0.3, cy - s * 0.38, cx + s * 0.3, cy + s * 0.42],
                        radius=s * 0.05, outline=color, width=w)
    d.rounded_rectangle([cx - s * 0.1, cy - s * 0.46, cx + s * 0.1, cy - s * 0.32],
                        radius=s * 0.03, outline=color, width=w)
    for i, yy in enumerate((-0.12, 0.04, 0.2)):
        d.line([(cx - s * 0.18, cy + s * yy), (cx - s * 0.06, cy + s * yy)],
               fill=color, width=max(w - 2, 2))  # ô tick
        d.line([(cx - s * 0.18, cy + s * yy + s * 0.02), (cx - s * 0.12, cy + s * yy + s * 0.06),
                (cx - s * 0.04, cy + s * yy - s * 0.04)], fill=color, width=max(w - 3, 2),
               joint="curve")
        d.line([(cx + s * 0.0, cy + s * yy), (cx + s * 0.2, cy + s * yy)],
               fill=color, width=max(w - 3, 2))


def clock(d, cx, cy, s, color, w=6):
    r = s * 0.34
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=w)
    d.line([(cx, cy), (cx, cy - r * 0.6)], fill=color, width=w)
    d.line([(cx, cy), (cx + r * 0.5, cy + r * 0.2)], fill=color, width=w)


def shield(d, cx, cy, s, color, w=6):
    pts = [(cx, cy - s * 0.42), (cx + s * 0.3, cy - s * 0.28), (cx + s * 0.3, cy + s * 0.08),
           (cx, cy + s * 0.42), (cx - s * 0.3, cy + s * 0.08), (cx - s * 0.3, cy - s * 0.28)]
    _poly(d, pts, color, w)
    d.line([(cx - s * 0.14, cy + s * 0.02), (cx - s * 0.03, cy + s * 0.16),
            (cx + s * 0.18, cy - s * 0.16)], fill=color, width=w, joint="curve")


def lightbulb(d, cx, cy, s, color, w=6):
    d.ellipse([cx - s * 0.26, cy - s * 0.4, cx + s * 0.26, cy + s * 0.12],
              outline=color, width=w)
    d.line([(cx - s * 0.12, cy + s * 0.14), (cx + s * 0.12, cy + s * 0.14)], fill=color, width=w)
    d.line([(cx - s * 0.1, cy + s * 0.24), (cx + s * 0.1, cy + s * 0.24)], fill=color, width=w)
    for a in (90, 130, 50):  # tia sáng
        ang = math.radians(a)
        d.line([(cx + s * 0.4 * math.cos(ang), cy - s * 0.14 - s * 0.4 * math.sin(ang)),
                (cx + s * 0.5 * math.cos(ang), cy - s * 0.14 - s * 0.5 * math.sin(ang))],
               fill=color, width=max(w - 2, 2))


def calendar(d, cx, cy, s, color, w=6):
    d.rounded_rectangle([cx - s * 0.36, cy - s * 0.3, cx + s * 0.36, cy + s * 0.38],
                        radius=s * 0.05, outline=color, width=w)
    d.line([(cx - s * 0.36, cy - s * 0.12), (cx + s * 0.36, cy - s * 0.12)], fill=color, width=w)
    d.line([(cx - s * 0.2, cy - s * 0.4), (cx - s * 0.2, cy - s * 0.22)], fill=color, width=w)
    d.line([(cx + s * 0.2, cy - s * 0.4), (cx + s * 0.2, cy - s * 0.22)], fill=color, width=w)
    for gx in (-0.12, 0.1):
        for gy in (0.02, 0.18):
            d.ellipse([cx + s * gx, cy + s * gy, cx + s * gx + s * 0.05, cy + s * gy + s * 0.05],
                      fill=color)


# Đăng ký doodle
REGISTRY: Dict[str, Callable] = {
    "heart": heart, "ecg": ecg, "kidney": kidney, "droplet": droplet, "lungs": lungs,
    "brain": brain, "stomach": stomach, "liver": liver, "bone": bone, "capsule": capsule,
    "pill": pill, "syringe": syringe, "microbe": microbe, "stethoscope": stethoscope,
    "bars": bars, "trend_up": trend_up, "magnifier": magnifier, "question": question,
    "warning": warning, "clipboard": clipboard, "clock": clock, "shield": shield,
    "lightbulb": lightbulb, "calendar": calendar,
}

# Bản đồ chuyên khoa -> doodle ưu tiên
_AREA_MAP = {
    "tim mạch": ["heart", "ecg"], "thần kinh": ["brain"], "đột quỵ": ["brain"],
    "nội tiết": ["droplet", "pill"], "chuyển hóa": ["droplet"], "đái tháo đường": ["droplet"],
    "thận": ["kidney"], "hô hấp": ["lungs"], "tiêu hóa": ["stomach"], "gan": ["liver"],
    "cơ xương khớp": ["bone"], "thấp khớp": ["bone"], "nhiễm khuẩn": ["microbe"],
    "kháng sinh": ["microbe", "capsule"], "lão khoa": ["pill", "clock"],
    "cấp cứu": ["warning"], "dự phòng": ["shield"], "vaccine": ["syringe"],
    "tuyến giáp": ["droplet"],
}
# Bản đồ từ khoá tiêu đề -> doodle phụ
_KW_MAP = [
    (("chi phí", "cost", "kinh tế", "giá", "ngân sách"), "bars"),
    (("nguy cơ", "risk", "an toàn", "cảnh báo", "tác dụng phụ", "biến chứng"), "warning"),
    (("tầm soát", "screening", "chẩn đoán", "phát hiện", "sàng lọc"), "magnifier"),
    (("nghịch lý", "tại sao", "vì sao", "?", "câu hỏi", "tranh cãi"), "question"),
    (("tăng", "giảm", "xu hướng", "tỷ lệ", "hiệu quả", "outcome", "tử vong"), "trend_up"),
    (("guideline", "khuyến cáo", "hướng dẫn", "đồng thuận", "tuân thủ"), "clipboard"),
    (("theo dõi", "tái khám", "thời gian", "lịch"), "calendar"),
    (("vaccine", "tiêm", "syringe"), "syringe"),
    (("thuốc", "liều", "kê đơn", "drug"), "capsule"),
    (("dự phòng", "phòng ngừa", "bảo vệ"), "shield"),
    (("mới", "cập nhật", "phát hiện mới", "ý tưởng"), "lightbulb"),
]


def doodles_for(area: str, title: str, n: int = 3) -> List[str]:
    """Chọn tối đa n doodle hợp chủ đề (chuyên khoa + từ khoá tiêu đề), không trùng."""
    text = f"{area or ''} {title or ''}".lower()
    picked: List[str] = []

    def _add(name):
        if name in REGISTRY and name not in picked:
            picked.append(name)

    for key, names in _AREA_MAP.items():
        if key in text:
            for nm in names:
                _add(nm)
    for kws, name in _KW_MAP:
        if any(k in text for k in kws):
            _add(name)
    if not picked:
        _add("clipboard"); _add("lightbulb")
    return picked[:n]


def draw(d, name: str, cx: float, cy: float, size: float, color, w: int = 6) -> bool:
    fn = REGISTRY.get(name)
    if not fn:
        return False
    fn(d, cx, cy, size, color, w)
    return True
