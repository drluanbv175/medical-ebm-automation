"""Guardrail G2: R4 (nhãn DRAFT) và R5 (ô [CẦN]) chỉ là THÔNG TIN — không phạt hồ sơ đã hoàn thiện (17/10/2026).

C1a còn 8 ô chờ dữ kiện sau phê duyệt ⇒ R5 cũ báo lỗi ⇒ checkpoint guardrail FAIL ⇒ kiem_chi_tiet trục ① 🔴, trong khi
g2_quality_gate đã bỏ R4/R5 khỏi G2-AUTO-01 từ 04/10/2026."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import run_g2_auto as G2  # noqa: E402

_ICF = "MỤC ĐÍCH QUY TRÌNH RỦI RO LỢI ÍCH BẢO MẬT TỰ NGUYỆN LIÊN HỆ"


def test_ho_so_it_nhan_khong_bi_loi_r4_r5():
    kq = G2.guardrail_check_g2("Hồ sơ đã điền gần đủ. [CẦN SỐ PHÊ DUYỆT] " + _ICF)
    assert not [e for e in kq["errors"] if e.startswith(("R4", "R5"))]
    assert any(w.startswith("R5 ℹ️ còn 1 ô") for w in kq["warnings"])


def test_luat_khac_van_chan():
    kq = G2.guardrail_check_g2("APPROVED_EXTERNALLY " + _ICF)
    assert any(e.startswith("R3") for e in kq["errors"]) and kq["passed"] is False
