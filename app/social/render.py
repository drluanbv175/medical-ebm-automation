"""Vẽ slideshow ảnh dọc 1080×1920 cho TikTok (photo mode) bằng Pillow.

Thiết kế tối giản, chữ là chính (hợp nội dung EBM): nền màu y khoa, badge chuyên
khoa, tiêu đề, các điểm chính (nguyên văn + dịch tham khảo), slide nguồn + khuyến cáo.

An toàn: nếu thiếu Pillow hoặc font, hàm trả [] và packager vẫn xuất gói TEXT
(caption + kịch bản) — không làm vỡ pipeline.
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Dict, List, Optional

# Loại emoji/ký hiệu ngoài BMP khi VẼ ảnh (font Arial không có glyph -> ô vuông).
# Vẫn giữ emoji trong caption/markdown (TikTok/markdown hiển thị tốt).
_EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF←-⇿⬀-⯿️]")


def _strip(text: str) -> str:
    return re.sub(r"\s{2,}", " ", _EMOJI_RE.sub("", text or "")).strip()

W, H = 1080, 1920
MARGIN = 90

# Bảng màu theo dạng nội dung.
THEME = {
    "recommendation": {"bg": (12, 74, 110), "accent": (56, 189, 248), "card": (8, 47, 73)},
    "watch": {"bg": (67, 56, 30), "accent": (251, 191, 36), "card": (52, 44, 24)},
}
FG = (241, 245, 249)
MUTED = (148, 163, 184)

_FONT_CANDIDATES = [
    os.getenv("TIKTOK_FONT", ""),
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/Library/Fonts/Arial Unicode.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
]
_FONT_BOLD_CANDIDATES = [
    os.getenv("TIKTOK_FONT_BOLD", ""),
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/Library/Fonts/Arial Unicode.ttf",
]


def _font_path(candidates: List[str]) -> Optional[str]:
    for c in candidates:
        if c and Path(c).exists():
            return c
    return None


def available() -> bool:
    """True nếu có thể vẽ ảnh (Pillow + font tiếng Việt)."""
    try:
        import PIL  # noqa: F401
    except Exception:
        return False
    return _font_path(_FONT_CANDIDATES) is not None


def _load_fonts():
    from PIL import ImageFont
    reg = _font_path(_FONT_CANDIDATES)
    bold = _font_path(_FONT_BOLD_CANDIDATES) or reg
    return {
        "badge": ImageFont.truetype(bold, 38),
        "h1": ImageFont.truetype(bold, 70),
        "h2": ImageFont.truetype(bold, 52),
        "body": ImageFont.truetype(reg, 46),
        "small": ImageFont.truetype(reg, 36),
        "tiny": ImageFont.truetype(reg, 30),
    }


def _wrap(draw, text: str, font, max_w: int) -> List[str]:
    """Ngắt dòng theo chiều rộng pixel (giữ nguyên từ). Bỏ emoji trước khi vẽ."""
    words = _strip(text).split()
    if not words:
        return [""]
    lines, cur = [], words[0]
    for w in words[1:]:
        trial = cur + " " + w
        if draw.textlength(trial, font=font) <= max_w:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


def _draw_footer(draw, fonts, page: int, total: int, accent):
    draw.text((MARGIN, H - 70), "Tham khảo · không thay khám bệnh",
              font=fonts["tiny"], fill=MUTED)
    label = f"{page}/{total}"
    tw = draw.textlength(label, font=fonts["tiny"])
    draw.text((W - MARGIN - tw, H - 70), label, font=fonts["tiny"], fill=accent)


def _new_canvas(bg):
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (W, H), bg)
    return img, ImageDraw.Draw(img)


def _draw_badge(draw, fonts, text: str, accent, y: int = 110) -> int:
    text = _strip(text)
    pad_x, pad_y = 34, 18
    tw = draw.textlength(text, font=fonts["badge"])
    draw.rounded_rectangle([MARGIN, y, MARGIN + tw + pad_x * 2, y + 38 + pad_y * 2],
                           radius=18, fill=accent)
    draw.text((MARGIN + pad_x, y + pad_y), text, font=fonts["badge"], fill=(7, 26, 43))
    return y + 38 + pad_y * 2


def _render_cover(post: Dict, fonts, theme, total: int):
    img, draw = _new_canvas(theme["bg"])
    y = _draw_badge(draw, fonts, f"  {post['kind_label']}  ", theme["accent"])
    y += 40
    draw.text((MARGIN, y), _strip(post["area"]), font=fonts["h2"], fill=theme["accent"])
    y += 90
    title = post["title"]["vi"] or post["title"]["en"]
    for line in _wrap(draw, title, fonts["h1"], W - 2 * MARGIN):
        draw.text((MARGIN, y), line, font=fonts["h1"], fill=FG)
        y += 84
    # Nguyên văn tiếng Anh (nếu có dịch) — nhỏ, để truy vết.
    if post["title"]["vi"] and post["title"]["en"]:
        y += 20
        for line in _wrap(draw, post["title"]["en"], fonts["small"], W - 2 * MARGIN)[:3]:
            draw.text((MARGIN, y), line, font=fonts["small"], fill=MUTED)
            y += 46
    # Dải tin cậy ở dưới.
    badge = []
    if post["tier"]:
        badge.append(f"Độ tin: {post['tier']}")
    if post["evidence_level"]:
        badge.append(f"Mức CC: {post['evidence_level']}")
    if badge:
        draw.text((MARGIN, H - 200), " · ".join(badge), font=fonts["small"], fill=theme["accent"])
    _draw_footer(draw, fonts, 1, total, theme["accent"])
    return img


def _render_points(slide: Dict, post: Dict, fonts, theme, page: int, total: int):
    img, draw = _new_canvas(theme["bg"])
    y = _draw_badge(draw, fonts, f"  {post['area']}  ", theme["accent"])
    y += 36
    for line in _wrap(draw, slide["heading"], fonts["h2"], W - 2 * MARGIN):
        draw.text((MARGIN, y), line, font=fonts["h2"], fill=theme["accent"])
        y += 64
    y += 16
    for b in slide["bullets"]:
        text = b["vi"] or b["en"]
        draw.ellipse([MARGIN, y + 18, MARGIN + 16, y + 34], fill=theme["accent"])
        for i, line in enumerate(_wrap(draw, text, fonts["body"], W - 2 * MARGIN - 50)):
            draw.text((MARGIN + 50, y), line, font=fonts["body"], fill=FG)
            y += 58
        # nguyên văn tiếng Anh nhỏ (truy vết, chống bịa) nếu có bản dịch.
        if b["vi"] and b["en"]:
            for line in _wrap(draw, b["en"], fonts["tiny"], W - 2 * MARGIN - 50)[:3]:
                draw.text((MARGIN + 50, y), line, font=fonts["tiny"], fill=MUTED)
                y += 36
        y += 26
        if y > H - 260:
            break
    _draw_footer(draw, fonts, page, total, theme["accent"])
    return img


def _render_source(post: Dict, fonts, theme, page: int, total: int):
    img, draw = _new_canvas(theme["card"])
    y = _draw_badge(draw, fonts, "  NGUỒN & LƯU Ý  ", theme["accent"])
    y += 50
    # Áp dụng (nếu có).
    for label, val in post.get("apply", []):
        draw.text((MARGIN, y), f"{label}:", font=fonts["h2"], fill=theme["accent"])
        y += 62
        for line in _wrap(draw, val, fonts["small"], W - 2 * MARGIN)[:3]:
            draw.text((MARGIN, y), line, font=fonts["small"], fill=FG)
            y += 46
        y += 24
    # Nguồn.
    draw.text((MARGIN, y), "Nguồn:", font=fonts["h2"], fill=theme["accent"])
    y += 62
    for line in _wrap(draw, post["source_name"], fonts["small"], W - 2 * MARGIN):
        draw.text((MARGIN, y), line, font=fonts["small"], fill=FG)
        y += 46
    for idline in post["ids"]:
        draw.text((MARGIN, y), idline, font=fonts["small"], fill=MUTED)
        y += 46
    if post["url"]:
        for line in _wrap(draw, post["url"], fonts["tiny"], W - 2 * MARGIN)[:2]:
            draw.text((MARGIN, y), line, font=fonts["tiny"], fill=MUTED)
            y += 36
    # Khuyến cáo.
    y = max(y + 30, H - 520)
    draw.rounded_rectangle([MARGIN, y, W - MARGIN, y + 360], radius=24,
                           outline=theme["accent"], width=3)
    yy = y + 36
    draw.text((MARGIN + 30, yy), "Lưu ý", font=fonts["h2"], fill=theme["accent"])
    yy += 70
    for line in _wrap(draw, post["disclaimer"], fonts["small"], W - 2 * MARGIN - 60):
        draw.text((MARGIN + 30, yy), line, font=fonts["small"], fill=FG)
        yy += 46
    _draw_footer(draw, fonts, page, total, theme["accent"])
    return img


def render_slides(post: Dict, out_dir: Path, style: str = "clinical") -> List[Path]:
    """Vẽ toàn bộ slide -> PNG, trả danh sách path. [] nếu không vẽ được.

    style: "clinical" (nền y khoa tối, mặc định) hoặc "whiteboard" (bảng trắng
    viết tay — nền giấy, font Brush Script/Chalkboard, nét vẽ tay).
    """
    if not available():
        return []
    if style == "whiteboard":
        return _render_whiteboard_all(post, out_dir)

    fonts = _load_fonts()
    theme = THEME.get(post["kind"], THEME["recommendation"])
    total = 2 + len(post["point_slides"])  # cover + points + source

    out_dir.mkdir(parents=True, exist_ok=True)
    paths: List[Path] = []

    def _save(img, idx: int) -> Path:
        p = out_dir / f"slide_{idx:02d}.png"
        img.save(p, "PNG")
        paths.append(p)
        return p

    _save(_render_cover(post, fonts, theme, total), 1)
    page = 2
    for slide in post["point_slides"]:
        _save(_render_points(slide, post, fonts, theme, page, total), page)
        page += 1
    _save(_render_source(post, fonts, theme, page, total), page)
    return paths


# ==========================================================================
# PHONG CÁCH "BẢNG TRẮNG VIẾT TAY" (whiteboard / doodle)
# Nền giấy trắng, chữ viết tay có dấu (Brush Script + Chalkboard SE),
# khung & gạch chân nét tay, bút dạ quang. Hợp giọng đọc mềm.
# ==========================================================================
WB_PAPER = (252, 250, 244)
WB_INK = (40, 42, 54)
WB_ACCENT = (13, 148, 136)     # marker xanh ngọc
WB_ACCENT2 = (217, 70, 80)     # marker đỏ cam (điểm nhấn)
WB_HILITE = (254, 240, 138)    # bút dạ quang vàng
WB_MUTED = (120, 120, 130)

_WB_TITLE = "/System/Library/Fonts/Supplemental/Brush Script.ttf"
_WB_BODY = "/System/Library/Fonts/Supplemental/ChalkboardSE.ttc"


def whiteboard_available() -> bool:
    try:
        import PIL  # noqa: F401
    except Exception:
        return False
    return Path(_WB_TITLE).exists() and Path(_WB_BODY).exists()


def _wb_fonts():
    from PIL import ImageFont

    def _ttc(size, idx):
        try:
            return ImageFont.truetype(_WB_BODY, size, index=idx)
        except Exception:
            return ImageFont.truetype(_WB_BODY, size)
    title_path = _WB_TITLE if Path(_WB_TITLE).exists() else _WB_BODY
    return {
        "title": ImageFont.truetype(title_path, 118),
        "h1": _ttc(74, 1),
        "h2": _ttc(56, 1),
        "body": _ttc(46, 0),
        "small": _ttc(36, 0),
        "tiny": _ttc(30, 0),
    }


def _wb_wrap(draw, text, font, max_w):
    words = _strip(text).split()
    if not words:
        return [""]
    lines, cur = [], words[0]
    for w in words[1:]:
        if draw.textlength(cur + " " + w, font=font) <= max_w:
            cur += " " + w
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


def _wb_squiggle(draw, x0, x1, y, color, amp=7, wl=46, width=5):
    """Gạch chân lượn sóng kiểu vẽ tay."""
    import math
    pts = []
    x = x0
    while x <= x1:
        pts.append((x, y + amp * math.sin((x - x0) / wl * math.pi)))
        x += 6
    if len(pts) > 1:
        draw.line(pts, fill=color, width=width, joint="curve")


def _wb_frame(draw):
    """Khung nét tay (hai đường lệch nhẹ cho cảm giác vẽ tay)."""
    draw.rounded_rectangle([46, 46, W - 46, H - 46], radius=34, outline=WB_INK, width=5)
    draw.rounded_rectangle([54, 54, W - 56, H - 58], radius=30, outline=WB_ACCENT, width=2)


def _wb_footer(draw, fonts, page, total):
    draw.text((MARGIN, H - 96), "Tham khảo · không thay khám bệnh",
              font=fonts["tiny"], fill=WB_MUTED)
    lbl = f"{page}/{total}"
    tw = draw.textlength(lbl, font=fonts["tiny"])
    draw.text((W - MARGIN - tw, H - 96), lbl, font=fonts["tiny"], fill=WB_ACCENT)


def _wb_highlight(draw, x, y, w, h, color=WB_HILITE):
    """Vệt bút dạ quang (vẽ TRƯỚC chữ)."""
    draw.rounded_rectangle([x - 8, y, x + w + 8, y + h], radius=10, fill=color)


def _wb_canvas():
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (W, H), WB_PAPER)
    d = ImageDraw.Draw(img)
    # vài chấm/li nhạt cho giống giấy
    for gy in range(150, H - 120, 140):
        d.line([(70, gy), (W - 70, gy)], fill=(238, 235, 228), width=1)
    _wb_frame(d)
    return img, d


def _wb_arrow(draw, x, y, color=WB_ACCENT2):
    """Mũi tên nguệch ngoạc nhỏ (doodle)."""
    draw.line([(x, y), (x + 70, y + 40)], fill=color, width=5, joint="curve")
    draw.line([(x + 70, y + 40), (x + 50, y + 16)], fill=color, width=5)
    draw.line([(x + 70, y + 40), (x + 44, y + 44)], fill=color, width=5)


def _wb_cover(post, fonts, total, dnames=None):
    from app.social import doodles as _dd
    img, d = _wb_canvas()
    y = 230
    d.text((MARGIN, y), _strip(post["area"]), font=fonts["h2"], fill=WB_ACCENT)
    _wb_squiggle(d, MARGIN, MARGIN + d.textlength(_strip(post["area"]), font=fonts["h2"]),
                 y + 78, WB_ACCENT)
    y += 150
    title = post["title"]["vi"] or post["title"]["en"]
    for line in _wb_wrap(d, title, fonts["title"], W - 2 * MARGIN):
        d.text((MARGIN, y), line, font=fonts["title"], fill=WB_INK)
        y += 116
    if post["title"]["vi"] and post["title"]["en"]:
        y += 16
        for line in _wb_wrap(d, post["title"]["en"], fonts["small"], W - 2 * MARGIN)[:3]:
            d.text((MARGIN, y), line, font=fonts["small"], fill=WB_MUTED)
            y += 46
    # Doodle minh hoạ trong khoảng trống giữa tiêu đề và badge (1–2 hình hợp chủ đề).
    dnames = dnames or []
    gap_y = max(y + 180, int(H * 0.62))
    if len(dnames) >= 1:
        _dd.draw(d, dnames[0], W * 0.30, gap_y, 210, WB_ACCENT, w=6)
    if len(dnames) >= 2:
        _dd.draw(d, dnames[1], W * 0.70, gap_y + 70, 175, WB_ACCENT2, w=6)
    _wb_arrow(d, W - 230, H - 360)
    badge = []
    if post["tier"]:
        badge.append(f"Độ tin: {post['tier']}")
    if post["evidence_level"]:
        badge.append(f"Mức CC: {post['evidence_level']}")
    if badge:
        d.text((MARGIN, H - 200), " · ".join(badge), font=fonts["small"], fill=WB_ACCENT)
    _wb_footer(d, fonts, 1, total)
    return img


def _wb_points(slide, post, fonts, page, total, corner=None):
    from app.social import doodles as _dd
    img, d = _wb_canvas()
    # doodle nhỏ, nhạt ở góc trên-phải (không chạm chữ ở lề trái)
    if corner:
        _dd.draw(d, corner, W - 150, 156, 120, (214, 222, 214), w=5)
    y = 150
    head = _strip(slide["heading"])
    # dạ quang sau tiêu đề
    hw = d.textlength(head, font=fonts["h2"])
    _wb_highlight(d, MARGIN, y + 6, hw, 64)
    d.text((MARGIN, y), head, font=fonts["h2"], fill=WB_INK)
    y += 110
    for b in slide["bullets"]:
        text = b["vi"] or b["en"]
        d.text((MARGIN, y - 2), "–", font=fonts["h2"], fill=WB_ACCENT)
        for line in _wb_wrap(d, text, fonts["body"], W - 2 * MARGIN - 56):
            d.text((MARGIN + 56, y), line, font=fonts["body"], fill=WB_INK)
            y += 58
        if b["vi"] and b["en"]:
            for line in _wb_wrap(d, b["en"], fonts["tiny"], W - 2 * MARGIN - 56)[:3]:
                d.text((MARGIN + 56, y), line, font=fonts["tiny"], fill=WB_MUTED)
                y += 36
        y += 28
        if y > H - 240:
            break
    _wb_footer(d, fonts, page, total)
    return img


def _wb_source(post, fonts, page, total, corner=None):
    from app.social import doodles as _dd
    img, d = _wb_canvas()
    if corner:
        _dd.draw(d, corner, W - 150, 156, 120, (214, 222, 214), w=5)
    y = 150
    d.text((MARGIN, y), "Nguồn & lưu ý", font=fonts["h1"], fill=WB_INK)
    _wb_squiggle(d, MARGIN, MARGIN + d.textlength("Nguồn & lưu ý", font=fonts["h1"]),
                 y + 86, WB_ACCENT)
    y += 150
    for label, val in post.get("apply", []):
        d.text((MARGIN, y), f"{label}:", font=fonts["h2"], fill=WB_ACCENT)
        y += 60
        for line in _wb_wrap(d, val, fonts["small"], W - 2 * MARGIN)[:3]:
            d.text((MARGIN, y), line, font=fonts["small"], fill=WB_INK)
            y += 44
        y += 18
    d.text((MARGIN, y), f"Nguồn: {post['source_name']}", font=fonts["small"], fill=WB_INK)
    y += 50
    for idline in post["ids"]:
        d.text((MARGIN, y), idline, font=fonts["small"], fill=WB_MUTED)
        y += 44
    y = max(y + 24, H - 520)
    d.rounded_rectangle([MARGIN, y, W - MARGIN, y + 360], radius=22,
                        outline=WB_ACCENT2, width=4)
    yy = y + 30
    d.text((MARGIN + 28, yy), "Lưu ý", font=fonts["h2"], fill=WB_ACCENT2)
    yy += 74
    for line in _wb_wrap(d, post["disclaimer"], fonts["small"], W - 2 * MARGIN - 56):
        d.text((MARGIN + 28, yy), line, font=fonts["small"], fill=WB_INK)
        yy += 44
    _wb_footer(d, fonts, page, total)
    return img


def _render_whiteboard_all(post: Dict, out_dir: Path) -> List[Path]:
    from app.social import doodles as _dd
    fonts = _wb_fonts()
    total = 2 + len(post["point_slides"])
    title = post["title"]["vi"] or post["title"]["en"]
    dnames = _dd.doodles_for(post.get("area", ""), title, n=4)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: List[Path] = []

    def _save(img, idx):
        p = out_dir / f"slide_{idx:02d}.png"
        img.save(p, "PNG")
        paths.append(p)

    _save(_wb_cover(post, fonts, total, dnames), 1)
    page = 2
    for k, slide in enumerate(post["point_slides"]):
        # mỗi slide điểm 1 doodle nhỏ góc trên-phải, xoay vòng theo danh sách
        corner = dnames[(k + 1) % len(dnames)] if dnames else None
        _save(_wb_points(slide, post, fonts, page, total, corner), page)
        page += 1
    _save(_wb_source(post, fonts, page, total, dnames[0] if dnames else None), page)
    return paths


def _wb_doodle(img, name, cx, cy, size, color):
    """Vẽ doodle (nếu có) lên ảnh."""
    if not name:
        return
    from PIL import ImageDraw

    from app.social import doodles as _dd
    _dd.draw(ImageDraw.Draw(img), name, cx, cy, size, color, w=6)
