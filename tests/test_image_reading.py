"""Test đọc ảnh y khoa đa phương thức (CAFÉ-S 2.3) — offline, vision LLM stub.

Phủ: khử EXIF THẬT (Pillow) · cổng đồng thuận · prompt an toàn · parse mô tả/gợi ý/cờ đỏ ·
pipeline với stub · disclaimer · không-key.
"""
from __future__ import annotations

import io

import pytest

from app.integrations.image_reading import (
    DISCLAIMER,
    ImageReadError,
    build_reading_prompt,
    claude_vision,
    parse_reading,
    read_image,
    strip_exif,
)

PIL = pytest.importorskip("PIL")
from PIL import Image  # noqa: E402


def _make_image_with_exif(path):
    img = Image.new("RGB", (12, 12), "white")
    exif = img.getexif()
    exif[270] = "PATIENT: Nguyen Van A"   # 270 = ImageDescription (định danh nhồi vào)
    exif[305] = "ECG-Machine-X"           # 305 = Software
    img.save(path, format="JPEG", exif=exif)


# -- Khử EXIF ---------------------------------------------------------------
def test_strip_exif_removes_metadata(tmp_path):
    p = tmp_path / "ecg.jpg"
    _make_image_with_exif(str(p))
    # Trước khi khử: EXIF có chứa định danh.
    assert "Nguyen Van A" in str(dict(Image.open(str(p)).getexif()))
    clean_bytes = strip_exif(str(p))
    reopened = Image.open(io.BytesIO(clean_bytes))
    assert dict(reopened.getexif()) == {}, "EXIF phải bị xóa sạch"
    assert reopened.size == (12, 12)  # pixel vẫn còn


def test_strip_exif_accepts_bytes(tmp_path):
    p = tmp_path / "x.png"
    Image.new("RGB", (8, 8), "black").save(str(p), format="PNG")
    raw = p.read_bytes()
    out = strip_exif(raw)
    assert isinstance(out, bytes) and len(out) > 0


# -- Cổng đồng thuận + thiếu vision ----------------------------------------
def test_read_image_requires_consent(tmp_path):
    p = tmp_path / "x.png"
    Image.new("RGB", (8, 8), "white").save(str(p))
    with pytest.raises(ImageReadError):
        read_image(str(p), consent=False, vision_llm=lambda b, pr, mt: "x")


def test_read_image_requires_vision_llm(tmp_path):
    p = tmp_path / "x.png"
    Image.new("RGB", (8, 8), "white").save(str(p))
    with pytest.raises(ImageReadError):
        read_image(str(p), consent=True, vision_llm=None)


# -- Prompt an toàn ---------------------------------------------------------
def test_build_prompt_ecg_has_safety_rules():
    p = build_reading_prompt("ecg")
    assert "ST" in p  # khung ECG
    assert "định danh" in p and "KHÔNG bịa" in p
    assert "CỜ ĐỎ" in p


def test_build_prompt_unknown_modality_falls_back_generic():
    p = build_reading_prompt("khong_biet")
    assert "có hệ thống" in p


# -- Parse + pipeline -------------------------------------------------------
def test_parse_reading_sections():
    text = ("MÔ TẢ: nhịp xoang, tần số 78, không ST chênh.\n"
            "GỢI Ý: ECG trong giới hạn bình thường [cần đối chiếu lâm sàng].\n"
            "CỜ ĐỎ: không thấy trên ảnh")
    r = parse_reading("ecg", text)
    assert "nhịp xoang" in r.description
    assert "giới hạn bình thường" in r.impression
    assert "không thấy" in r.red_flags


def test_read_image_end_to_end_with_stub(tmp_path):
    p = tmp_path / "ecg.jpg"
    _make_image_with_exif(str(p))
    captured = {}

    def stub_vision(image_bytes, prompt, media_type):
        captured["mt"] = media_type
        captured["bytes"] = image_bytes
        return ("MÔ TẢ: nhịp xoang 80, trục bình thường.\n"
                "GỢI Ý: không bất thường cấp [cần đối chiếu lâm sàng].\n"
                "CỜ ĐỎ: ST chênh lên V1-V3 — cần đọc khẩn.")

    reading = read_image(str(p), consent=True, vision_llm=stub_vision, modality="ecg")
    assert captured["mt"] == "image/jpeg"
    # Ảnh truyền vào vision đã khử EXIF (không còn định danh trong metadata).
    assert b"Nguyen Van A" not in captured["bytes"]
    assert "ST chênh" in reading.red_flags
    assert DISCLAIMER in reading.to_markdown()


def test_claude_vision_requires_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(ImageReadError):
        claude_vision(b"x", "prompt")
