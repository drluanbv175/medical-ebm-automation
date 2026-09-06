"""Hồi quy phát hiện #2 (audit vòng 35, 2026-09-06) trong
runtime/approval_ledger.py — has_gate_a()/has_gate_b() công nhận approval
SYNTHETIC (is_synthetic=True), khác 3 hàm has_* chị em.

CƠ CHẾ LỖI (TRƯỚC bản vá):
    def has_gate_a(self) -> bool:
        return self.check_has_approval("GATE_A") is not None

``check_has_approval()`` chỉ lọc theo `gate_id` + `decision` (mới nhất, chưa
bị thu hồi) — KHÔNG loại `is_synthetic`. Trong khi ``has_ethics_approval()``
(G2), ``has_sap_lock()`` (G4), ``has_pi_signoff()`` (G9) đều gọi
``check_required_stakeholder_approval()``, hàm này lọc rõ
``not getattr(r, "is_synthetic", False)`` trước khi công nhận một approval.
``make_synthetic_approval()`` tự khai trong docstring: "record này được
gắn cờ structural is_synthetic=True... để KHÔNG BAO GIỜ bị nhầm là phê
duyệt người" — nhưng has_gate_a()/has_gate_b() vẫn nhầm.

LƯU Ý PHẠM VI ẢNH HƯỞNG (đã xác minh bằng grep toàn repo trước khi sửa,
không suy diễn): "GATE_A"/"GATE_B" là cổng LÂM SÀNG (Cổng A = áp dụng cho
bệnh nhân, Cổng B = ghi sổ cái — dieu-phoi-lam-sang/so-cai-ghi-nho), KHÁC
6 cổng G0–G10 nghiên cứu. Hai caller DUY NHẤT của has_gate_a()/has_gate_b()
là ``runtime/controlled_orchestrator.py`` và
``runtime/check_has_approval("GATE_A")`` trong ``runtime/policy_gate_engine.py``
— cả hai file này CLAUDE.md đã ghi nhận là nhánh MỒ CÔI ("NO-GO — NOT
QUALIFIED FOR RESEARCH WORKFLOW USE"), không phải cổng G0–G10 thật mà
``tools/approve_gate.py`` dùng. Bug vẫn THẬT (tái hiện được, đúng bất biến
bị vi phạm) nên vẫn sửa — chỉ không phóng đại mức ảnh hưởng.

BẢN VÁ: thêm ``_has_non_synthetic_approval()`` (lọc ``is_synthetic``, dùng
riêng cho has_gate_a/has_gate_b) — KHÔNG đổi sang gọi
``check_required_stakeholder_approval()`` vì "GATE_A"/"GATE_B" không có
trong ``tools/gate_contract.py::_GATE_REQUIRED_STAKEHOLDERS`` nên hàm đó
sẽ fallback nguyên xi về ``check_has_approval()`` — không lọc gì thêm
(đã xác minh bằng grep + đọc mã nguồn, không phải suy đoán)."""
from __future__ import annotations

from runtime.approval_ledger import ApprovalLedger


class TestCaChinhGateAKhongDuocDuyetBoiSynthetic:
    """★★★ Ca chính — GATE_A/GATE_B chỉ có approval SYNTHETIC không được
    coi là đã duyệt."""

    def test_gate_a_chi_co_synthetic_tra_ve_false(self):
        ledger = ApprovalLedger()
        rec = ApprovalLedger.make_synthetic_approval(
            gate_id="GATE_A", scope="test", evidence_content="x",
        )
        ok, reason = ledger.add_approval(rec)
        assert ok is True, reason

        assert ledger.has_gate_a() is False, (
            "TRƯỚC bản vá: has_gate_a() gọi thẳng check_has_approval() "
            "không lọc is_synthetic, nên một approval MÔ PHỎNG (không phải "
            "người) khiến has_gate_a() trả True."
        )

    def test_gate_b_chi_co_synthetic_tra_ve_false(self):
        ledger = ApprovalLedger()
        rec = ApprovalLedger.make_synthetic_approval(
            gate_id="GATE_B", scope="test", evidence_content="x",
        )
        ledger.add_approval(rec)
        assert ledger.has_gate_b() is False


class TestDoiChungApprovalNguoiThatVanDuocCongNhan:
    """Đối chứng — approval NGƯỜI THẬT (không synthetic) vẫn phải được
    has_gate_a()/has_gate_b() công nhận đúng như trước."""

    def test_gate_a_voi_approval_nguoi_that_tra_ve_true(self):
        ledger = ApprovalLedger()
        rec = ApprovalLedger.make_human_approval(
            gate_id="GATE_A", reviewer_role="BAC_SI", reviewer_ref="bs001",
            scope="test", evidence_content="y",
        )
        ledger.add_approval(rec)
        assert ledger.has_gate_a() is True

    def test_gate_b_voi_approval_nguoi_that_tra_ve_true(self):
        ledger = ApprovalLedger()
        rec = ApprovalLedger.make_human_approval(
            gate_id="GATE_B", reviewer_role="BAC_SI", reviewer_ref="bs002",
            scope="test", evidence_content="y",
        )
        ledger.add_approval(rec)
        assert ledger.has_gate_b() is True

    def test_gate_a_nguoi_that_cong_them_synthetic_van_true(self):
        # Có CẢ synthetic lẫn người thật cho cùng gate — vẫn phải nhận diện
        # đúng nhờ bản ghi người thật, không bị synthetic che khuất.
        ledger = ApprovalLedger()
        ledger.add_approval(ApprovalLedger.make_synthetic_approval(
            gate_id="GATE_A", scope="test", evidence_content="x"))
        ledger.add_approval(ApprovalLedger.make_human_approval(
            gate_id="GATE_A", reviewer_role="BAC_SI", reviewer_ref="bs003",
            scope="test", evidence_content="y"))
        assert ledger.has_gate_a() is True

    def test_has_ethics_approval_g2_khong_doi_hanh_vi(self):
        # has_ethics_approval() (G2) vốn đã lọc synthetic đúng từ trước qua
        # check_required_stakeholder_approval() — bản vá này KHÔNG ĐỘNG vào
        # đường đó, xác nhận không hồi quy.
        ledger = ApprovalLedger()
        ledger.add_approval(ApprovalLedger.make_synthetic_approval(
            gate_id="G2", scope="test", evidence_content="w"))
        assert ledger.has_ethics_approval() is False

    def test_gate_khac_khong_lien_quan_khong_bi_anh_huong(self):
        ledger = ApprovalLedger()
        ledger.add_approval(ApprovalLedger.make_synthetic_approval(
            gate_id="GATE_A", scope="test", evidence_content="x"))
        assert ledger.has_gate_b() is False
        assert ledger.count() == 1
