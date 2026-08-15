"""Hồi quy (vòng audit đối kháng 4, 2026-07-17 — chuẩn quốc tế): ICMJE Recommendations
cập nhật 1/2026 thêm Mục V "Use of Artificial Intelligence in Publishing" (xác minh trực
tiếp qua icmje.org/recommendations/browse/artificial-intelligence/ai-use-by-authors.html)
— Mục V.A bắt buộc khai báo dùng công nghệ AI TẠI HAI NƠI: cover letter VÀ mục phù hợp
trong bản thảo; không khai báo có thể bị coi là hành vi sai trái khoa học (Mục III.A/III.B).

Trước bản vá: build_part6_cover_letter() (Phần 6 — thư gửi tạp chí) không có dòng khai báo
AI nào — chỉ Phần 4 (khai báo AI riêng) có, và Phần 4 tự trích dẫn "ICMJE Recommendations
(2023): AI tools cannot be authors" — vị trí ĐÃ BỊ THAY bởi Mục V (1/2026).
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import run_g9_auto as G9  # noqa: E402


def _fake_cps() -> dict:
    return {
        "G0": {"topic": "Test topic", "n_sr": 2, "n_rct": 1, "research_gaps": []},
        "G1": {"design": {"primary": "Cross-sectional", "reporting_standard": "STROBE 2007"}},
        "G2": {"g2_registration": "Không đăng ký (quan sát)", "g2_irb_number": "IRB-001"},
        "G3": {"n_adjusted": 100},
    }


def test_cover_letter_declares_ai_use_per_icmje_section_v():
    out = G9.build_part6_cover_letter(_fake_cps(), "PYTEST-G9-AI-DISCLOSURE", "Tạp chí Y học TP.HCM")
    assert "Use of AI-assisted technologies" in out
    assert "EBM Copilot" in out


def test_part4_ai_disclosure_cites_current_icmje_section_v_not_superseded_2023_position():
    out = G9.build_part4_ai_disclosure({}, "PYTEST-G9-AI-DISCLOSURE")
    assert "Mục V" in out or "Section V" in out
    assert "AI cannot be authors" not in out
    assert "ICMJE Recommendations (2023): AI tools cannot be authors" not in out


def test_coi_intellectual_property_covers_copyright_and_licensing_not_just_patent():
    """Hồi quy: mục 'Intellectual Property' của ICMJE Uniform Disclosure Form (xác minh
    qua icmje.org + đối chiếu mẫu form thật) bao gồm CẢ patent VÀ copyright, bất kể đang
    chờ cấp/đã cấp/đã cấp phép/đang nhận tiền bản quyền — trước bản vá chỉ hỏi 'Bằng sáng
    chế' (patent), bỏ sót toàn bộ phần copyright/licensing/royalty."""
    out = G9.build_part2_coi(1, "PYTEST-G9-COI-IP")
    assert "copyright" in out.lower() or "bản quyền" in out.lower()
    assert "cấp phép" in out.lower() or "licensed" in out.lower()
