"""Hồi quy phát hiện #1 (miền quality-gates-g1-g6-g7-g10) của Workflow đối kháng
đa-agent vòng 2 (2026-09-03/04) trong tools/g7_quality_gate.py.

`_UNSUPPORTED_CLAIM_PATTERNS` là "lớp phòng thủ cuối cùng" (docstring của chính
module) chặn bác sĩ tự gõ tay vào bản thảo một câu khẳng định TRẦN (đã được Hội
đồng Đạo đức phê duyệt / đã đăng ký ClinicalTrials / SAP đã khóa / dữ liệu đã
khóa) khi cổng trước (G2/G4/G5) CHƯA thật sự đạt. Trước bản vá, 4 regex đòi cụm
từ LIỀN KỀ cứng nhắc — không cho chèn thêm chữ (tên tổ chức, số quyết định…) và
không có từ đồng nghĩa — nên một cách diễn đạt tự nhiên khác đi một chút (ví dụ
chèn đúng tên cơ sở của repo này, "Bệnh viện Quân y 175", vào giữa "Hội đồng Đạo
đức" và "phê duyệt") lọt hoàn toàn qua cổng, kể cả khi chạy TRỌN
`evaluate_g7_quality()`.

Nguyên tắc viết test: KIỂM HÀNH VI bằng cách gọi hàm thật, không grep chuỗi
trong mã nguồn. Không gọi mạng.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
for _p in (str(REPO_ROOT), str(TOOLS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import g7_quality_gate as G7Q  # noqa: E402


def _manuscript(section7: str) -> str:
    """Bản thảo A8 tối thiểu — đủ mục IMRAD, thay §7 bằng câu cần thử."""
    return (
        "# BẢN THẢO DRAFT\n\n"
        "**Trạng thái:** DRAFT — chưa nộp tạp chí.\n\n"
        "## TÓM TẮT\nNền tảng, mục tiêu, thiết kế.\n\n"
        "## I. GIỚI THIỆU\nBối cảnh nghiên cứu.\n\n"
        "## II. PHƯƠNG PHÁP\n"
        "**§5 Cỡ mẫu:** Cỡ mẫu được tính theo công thức log-rank, N = 320.\n"
        f"**§7 Đạo đức và đăng ký:** {section7}\n\n"
        "## III. KẾT QUẢ\n"
        "[CẦN KẾT QUẢ THẬT — Bảng 2 kết cục chính]\n"
        "[CẦN KẾT QUẢ THẬT — Bảng 1 đặc điểm nền]\n\n"
        "## IV. BÀN LUẬN\nBàn luận.\n\n"
        "## V. KẾT LUẬN\nKết luận.\n\n"
        "## TÀI LIỆU THAM KHẢO\n1. Nguyen A. PMID: 30000001\n"
        "\nCần bác sĩ kiểm chứng.\n"
    )


def _cps(**over) -> dict:
    base = {
        "G0": {"gate": "G0", "topic": "x"},
        "G1": {"gate": "G1", "design": {"internal_code": "cohort"}},
        "G2": {"gate": "G2"},  # KHÔNG có IRB thật — đúng kịch bản bypass
        "G3": {"gate": "G3", "n_adjusted": 320},
        "G4": {"gate": "G4"},
        "G5": {"gate": "G5"},
        "G6": {"gate": "G6"},
        "G7": {"gate": "G7", "guardrail": {"status": "✅ PASS", "errors": []}},
    }
    base.update(over)
    return base


# ════════════════════════════════════════════════════════════════════════════
# 1. find_unsupported_claims() — biến thể diễn đạt tự nhiên phải bị bắt
# ════════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("cau,tin_hieu", [
    # #1 — đồng nghĩa "chấp thuận" thay "phê duyệt"
    ("Nghiên cứu đã được Hội đồng Đạo đức chấp thuận trước khi triển khai.",
     "irb_approved"),
    # #2 — chèn tên tổ chức thật giữa thực thể và động từ (kịch bản thực tế
    # nhất: bác sĩ ghi đúng tên cơ sở của mình)
    ("Đề tài đã được Hội đồng Đạo đức Bệnh viện Quân y 175 phê duyệt.",
     "irb_approved"),
    # #3 — đồng nghĩa "thông qua"
    ("Đề cương đã được IRB Bệnh viện Quân y 175 thông qua ngày 01/06/2026.",
     "irb_approved"),
    # #4 — thiếu "tại/trên" trước ClinicalTrials
    ("Nghiên cứu đã đăng ký ClinicalTrials.gov mã NCT01234567.", "registered"),
    # #5 — chèn "nghiên cứu" giữa "dữ liệu" và "đã khóa"
    ("Dữ liệu nghiên cứu đã được khóa hoàn toàn trước khi phân tích.",
     "db_locked"),
    # #6 — chèn mô tả giữa SAP và "đã khóa"
    ("SAP phiên bản cuối cùng đã được khóa ngày 01/05/2026.", "sap_locked"),
])
def test_bat_duoc_bien_the_dien_dat_tu_nhien(cau, tin_hieu):
    claims = G7Q.find_unsupported_claims(cau, {tin_hieu: False})
    assert claims, f"KHÔNG bắt được khẳng định bịa đặt (bypass): {cau!r}"
    # Có bằng chứng thật thì cùng câu đó phải hợp lệ trở lại
    assert G7Q.find_unsupported_claims(cau, {tin_hieu: True}) == []


def test_khong_bat_nham_cau_khong_lien_quan():
    """Đối chứng âm: câu hoàn toàn không nhắc IRB/đăng ký/khóa không bị bắt."""
    text = "Nghiên cứu thu tuyển 320 người tham gia tại 3 trung tâm."
    assert G7Q.find_unsupported_claims(
        text, {"irb_approved": False, "registered": False,
               "sap_locked": False, "db_locked": False},
    ) == []


def test_khong_bat_nham_nhan_CAN_dien_giai_rong_hon():
    """Cửa sổ ký tự rộng hơn không được làm hỏng rào đã có: nội dung trong nhãn
    [CẦN…] vẫn phải bị bóc trước khi soi, kể cả khi nhãn đó dài và mô tả chi tiết
    tên tổ chức (đúng kịch bản chèn-tên vừa được nới cho phép bắt)."""
    text = _manuscript(
        "[CẦN — KHÔNG được viết 'đã được Hội đồng Đạo đức Bệnh viện Quân y 175 "
        "phê duyệt' trước khi việc đó xảy ra thật]"
    )
    claims = G7Q.find_unsupported_claims(text, {"irb_approved": False})
    assert claims == [], f"bắt nhầm chỉ dẫn trong nhãn [CẦN…]: {claims}"


# ════════════════════════════════════════════════════════════════════════════
# 2. evaluate_g7_quality() TRỌN — đúng kịch bản evidence #5 của phát hiện
# ════════════════════════════════════════════════════════════════════════════

def test_evaluate_g7_quality_chan_khang_dinh_chen_ten_to_chuc():
    """Bản thảo giả có §7 chứa nguyên văn 'Đề tài đã được Hội đồng Đạo đức Bệnh
    viện Quân y 175 phê duyệt.' trong khi G2 KHÔNG có IRB thật (irb_approved=False
    qua checkpoints/meta rỗng, đúng kịch bản không có G2 thật). G7-AUTO-06 phải
    BLOCK, không được PASS."""
    text = _manuscript(
        "Đề tài đã được Hội đồng Đạo đức Bệnh viện Quân y 175 phê duyệt. "
        "Nghiên cứu đã đăng ký ClinicalTrials.gov mã NCT01234567."
    )
    report = G7Q.evaluate_g7_quality(
        manuscript_text=text, checkpoints=_cps(G2={}), meta={},
    )
    row = next(r for r in report["automatic_criteria"] if r["id"] == "G7-AUTO-06")
    assert row["status"] == "BLOCK", row
    assert any("Hội đồng Đạo đức" in c for c in report["unsupported_claims"])
    assert any("ClinicalTrials" in c for c in report["unsupported_claims"])
    assert report["status"] == G7Q.STATUS_BLOCKED


def test_evaluate_g7_quality_hop_le_khi_chen_ten_to_chuc_nhung_co_bang_chung_that():
    """Cùng cách diễn đạt (chèn tên tổ chức) nhưng G2 có IRB thật — không được
    cảnh báo oan chỉ vì cách viết khác cụm mẫu gốc."""
    text = _manuscript(
        "Đề tài đã được Hội đồng Đạo đức Bệnh viện Quân y 175 phê duyệt "
        "(IRB-2026-001)."
    )
    report = G7Q.evaluate_g7_quality(
        manuscript_text=text,
        checkpoints=_cps(G2={"gate": "G2", "g2_irb_number": "IRB-2026-001"}),
        meta={"irb_approved": True},
    )
    row = next(r for r in report["automatic_criteria"] if r["id"] == "G7-AUTO-06")
    assert row["status"] == "PASS", row
    assert not any("Hội đồng Đạo đức" in c for c in report["unsupported_claims"])
