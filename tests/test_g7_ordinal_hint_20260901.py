"""Hồi quy: gợi ý phương pháp G7 cho PREVALENCE + kết cục THỨ BẬC — 01/09/2026.

Vì sao có: `_method_hint` của run_g7_auto.py chỉ rẽ theo effect_type
{MD/HR/OR/RR/ARR%/AUC} — đề tài thật đầu tiên đi hết G0-G4 (C1a,
effect_type=PREVALENCE) rơi về câu trung tính "phương pháp thống kê phù hợp
thiết kế", và sau khi G6 có nhánh sinh script proportional odds (01/09) thì
G7 vẫn không biết nói "logistic thứ tự (cOR)" — hai cổng kể hai chuyện khác
nhau về CÙNG một SAP. Cùng lớp lỗi "2 lớp xử lý tách rời nhau".

Ba thứ phải khoá:
1. gate_contract.sap_declares_ordinal là NGUỒN DUY NHẤT (G6 delegate về đây);
   thiếu SAP → False (fail-closed).
2. PREVALENCE có gợi ý riêng (tỷ lệ + Wilson), không rơi về câu trung tính.
3. outcome_ordinal=True → Methods §6 nói proportional odds/cOR/Brant và đổi
   vế dẫn (effect_type là estimand TÍNH CỠ MẪU, không phải mô hình);
   False → hành vi cũ nguyên vẹn, các effect_type khác không đổi.
"""

import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import gate_contract as GC  # noqa: E402
import run_g6_auto as G6  # noqa: E402
import run_g7_auto as G7  # noqa: E402


def _kwargs(**override):
    """Bộ tham số tối thiểu hợp lệ cho generate_manuscript (cắt ngang C1a-style)."""
    kw = dict(
        study="S", topic="T", n_sr=1, n_rct=1, n_guideline=1,
        research_gaps=["khoảng trống"], pmids=["11111111"], pmid_meta={},
        design_code="cross_sectional", design_primary="Cắt ngang",
        reporting_std="STROBE 2007", irb_number="[CẦN]", icf_version="[CẦN]",
        registration="[CẦN]", n_total=850, n_adjusted=1000,
        alpha=0.05, power=0.80, effect_val=0.5, effect_type="PREVALENCE",
        formula_used="Lwanga & Lemeshow", g4_status="PENDING",
        g4_lock_date=None, target_journal="[CẦN]", word_limit=3500,
        run_date="2026-09-01",
    )
    kw.update(override)
    return kw


class TestNguonDuyNhat:
    def test_gc_la_nguon_va_g6_delegate(self, tmp_path):
        (tmp_path / "G4_A5_SAP_FINAL_S.md").write_text(
            "Mô hình chính: hồi quy logistic THỨ TỰ (proportional odds)",
            encoding="utf-8", newline="\n")
        assert GC.sap_declares_ordinal(tmp_path, "S")
        assert G6._sap_declares_ordinal(tmp_path, "S"), "G6 phải delegate về GC"

    def test_thieu_sap_fail_closed(self, tmp_path):
        assert not GC.sap_declares_ordinal(tmp_path, "S")


class TestGoiYPrevalence:
    def test_prevalence_co_goi_y_rieng(self):
        m = G7.generate_manuscript(**_kwargs())
        assert "ước lượng tỷ lệ hiện hành" in m and "Wilson" in m
        assert "phương pháp thống kê phù hợp thiết kế" not in m, (
            "PREVALENCE không được rơi về câu trung tính nữa")

    def test_effect_type_khac_giu_nguyen(self):
        m = G7.generate_manuscript(**_kwargs(
            effect_type="HR", design_code="cohort", design_primary="Cohort"))
        assert "Cox proportional hazards regression" in m
        assert "proportional odds" not in m


class TestGoiYThuBac:
    def test_ordinal_noi_dung_khop_script_g6(self):
        m = G7.generate_manuscript(**_kwargs(), outcome_ordinal=True)
        assert "proportional odds" in m
        assert "cOR" in m
        assert "Brant" in m, "phải nhắc kiểm Brant trước khi diễn giải cOR"
        assert "SAP đã khai mô hình thứ bậc" in m, (
            "vế dẫn phải đổi — effect_type là estimand tính cỡ mẫu, không phải mô hình")

    def test_mac_dinh_khong_thu_bac(self):
        m = G7.generate_manuscript(**_kwargs())
        assert "proportional odds" not in m

    def test_guardrail_sach_tren_ban_thao_thu_bac(self):
        m = G7.generate_manuscript(**_kwargs(), outcome_ordinal=True)
        errors, _ = G7.guardrail_g7(m)
        assert errors == [], f"guardrail G7 phải sạch: {errors}"

    def test_sap_that_c1a_kich_hoat(self):
        out = Path(__file__).resolve().parent.parent / "exports" / "hai-long-benh-nhan-C1a-BVQY175"
        if not (out / "G4_A5_SAP_FINAL_hai-long-benh-nhan-C1a-BVQY175.md").exists():
            import pytest
            pytest.skip("không có exports C1a trên máy này")
        assert GC.sap_declares_ordinal(out, "hai-long-benh-nhan-C1a-BVQY175")
