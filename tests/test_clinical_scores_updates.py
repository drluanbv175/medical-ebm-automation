"""Test KHÓA (pinning) các cập nhật guideline 2024–2026 cho 6 thang điểm.

Mục đích: chống TRÔI nội dung. Nếu một cụm từ/ngưỡng đã được kiểm chứng bị xóa
khỏi `verified.py`, test tương ứng phải FAIL ngay (regression guard).

Nguồn của các pin: docs/RA_SOAT_THANG_DIEM_2026-06.md (đã đối chiếu web 2024–2026).
Mỗi pin gắn với một thay đổi guideline cụ thể, không phải kiểm tra văn phong.
"""
from __future__ import annotations

import pytest

from app.clinical_scores.verified import VERIFIED_SCORES


def _entry(score_id: str) -> dict:
    for e in VERIFIED_SCORES:
        if e.get("score_id") == score_id:
            return e
    raise AssertionError(f"score_id '{score_id}' không có trong VERIFIED_SCORES")


def _blob(score_id: str) -> str:
    """Ghép mọi giá trị chuỗi của 1 entry để pin không phụ thuộc field cụ thể."""
    e = _entry(score_id)
    parts: list[str] = []
    for v in e.values():
        if isinstance(v, str):
            parts.append(v)
        elif isinstance(v, list):
            parts.extend(str(x) for x in v)
    return "\n".join(parts)


def _assert_pins(score_id: str, pins: list[str]) -> None:
    blob = _blob(score_id)
    missing = [p for p in pins if p not in blob]
    assert not missing, f"[{score_id}] thiếu cập nhật guideline: {missing}"


def test_cha2ds2_va_esc_2024():
    # ESC 2024: CHA2DS2-VASc → CHA2DS2-VA, bỏ giới, tối đa 8, ngưỡng ≥2 không phân biệt giới
    _assert_pins("cha2ds2_vasc", ["CHA2DS2-VA", "ESC 2024", "tối đa 8", "0–8",
                                  "≥2", "không phân biệt giới"])


def test_fib4_masld_aasld_2023():
    # AASLD 2023: ngưỡng nguy cơ thấp ở MASLD là <1.3 (không phải 1.45)
    _assert_pins("fib4", ["1.3", "AASLD 2023", "MASLD"])


def test_qsofa_ssc_2021_strong_against():
    # Surviving Sepsis 2021: khuyến cáo MẠNH CHỐNG dùng qSOFA làm sàng lọc đơn lẻ
    _assert_pins("qsofa", ["Surviving Sepsis", "2021", "MẠNH CHỐNG"])


def test_meld_3_0_since_2023():
    # UNOS/OPTN 2023: MELD 3.0 (thêm albumin & giới) thay MELD-Na
    _assert_pins("meld_na", ["MELD 3.0", "2023"])


def test_gold_abe_2025():
    # GOLD 2025: nhóm A/B/E; eosinophil ≥300 để cân nhắc ICS
    _assert_pins("gold_abe", ["ABE", "300", "2025"])


def test_ascvd_prevent_caveat_2023():
    # AHA PREVENT 2023: cảnh báo PCE có thể ước tính cao; PREVENT bỏ chủng tộc
    _assert_pins("ascvd_pce", ["PREVENT", "2023"])


def test_gad7_uspstf_2023_grade_b():
    # USPSTF 2023: khuyến cáo MỚI mức B sàng lọc rối loạn lo âu ở người lớn ≤64
    _assert_pins("gad7", ["USPSTF 2023", "mức B", "lo âu"])


@pytest.mark.parametrize("score_id", ["cha2ds2_vasc", "fib4", "qsofa",
                                      "meld_na", "gold_abe", "ascvd_pce", "gad7"])
def test_updated_scores_have_source_and_guideline(score_id):
    # Liêm chính: mỗi thang đã cập nhật phải còn nguồn + guideline_reference
    e = _entry(score_id)
    assert e.get("source"), f"[{score_id}] thiếu source"
    assert e.get("guideline_reference"), f"[{score_id}] thiếu guideline_reference"
