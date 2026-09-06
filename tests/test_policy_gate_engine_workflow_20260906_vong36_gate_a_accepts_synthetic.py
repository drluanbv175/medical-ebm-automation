"""Hồi quy phát hiện #3 (audit vòng 36, 2026-09-06) trong
runtime/policy_gate_engine.py — `_check_gate_a_clinical()` chấp nhận
approval SYNTHETIC (is_synthetic=True) làm phê duyệt lâm sàng thật, tái
lặp đúng lỗi đã vá ở file "anh em" runtime/approval_ledger.py (vòng 35,
xem tests/test_approval_ledger_workflow_20260906_vong35_gate_a_b_accepts_synthetic.py).

CƠ CHẾ LỖI (TRƯỚC bản vá):
    def _check_gate_a_clinical(self, context, ledger, fixture, ts):
        approval = ledger.check_has_approval("GATE_A")
        ...

`check_has_approval()` không lọc `is_synthetic`. Vòng 35 đã vá
`ApprovalLedger.has_gate_a()` để dùng `_has_non_synthetic_approval()`
(lọc `is_synthetic`) — nhưng `PolicyGateEngine._check_gate_a_clinical()`
KHÔNG dùng `ledger.has_gate_a()` đã vá đó, mà tự gọi lại
`check_has_approval()` thô. Đúng mẫu "sửa 1 chỗ quên chỗ anh em" mà
chính approval_ledger.py đã tự cảnh báo trong nhiều comment khác.

BẢN VÁ: đổi `_check_gate_a_clinical()` dùng `ledger.has_gate_a()`.

PHẠM VI ẢNH HƯỞNG (xác minh bằng grep toàn repo trước khi sửa, không
suy diễn): `PolicyGateEngine` là code CHẾT HOÀN TOÀN — chỉ
`tests/test_policy_gate_engine.py`, `tests/test_offline_workflow_
integration.py`, `tests/test_reproducibility.py` import và khởi tạo
class này. `research_studio/research_workflow.py` chỉ NHẮC TÊN
"PolicyGateEngine" trong MỘT dòng docstring vẽ sơ đồ kiến trúc, KHÔNG
hề import hay gọi nó — xác nhận bằng grep, không có `from runtime.
policy_gate_engine import` nào ngoài `tests/`. Bug vẫn THẬT (tái hiện
được bằng chạy thật) nên vẫn sửa, nhưng mức độ ảnh hưởng thực tế BẰNG 0
(không có caller sản xuất hay thậm chí caller mồ côi nào khác).

KHÔNG sửa `_check_gate_b_ledger()`: hàm đó kiểm TOÀN VẸN evidence_hash
của TOÀN BỘ ledger (test_gate_b_ledger_clean trong test_policy_gate_
engine.py dùng approval gate "G2" — không phải "GATE_B" — để kiểm
GATE_B) — một Ý NGHĨA "GATE_B" khác hẳn `has_gate_b()` ("đã có phê
duyệt ghi sổ cái GATE_B chưa"). Không rõ ràng đây là bug hay thiết kế cố
ý khác nên không động vào, tránh sửa sai ý đồ của một cổng tổng quát."""
from __future__ import annotations

from runtime.approval_ledger import ApprovalLedger
from runtime.policy_gate_engine import PolicyGateEngine
from runtime.schemas import GateDecisionEnum


def _engine() -> PolicyGateEngine:
    return PolicyGateEngine()


class TestCaChinhGateAKhongDuocDuyetBoiSynthetic:
    """★★★ Ca chính — GATE_A chỉ có approval SYNTHETIC phải bị coi là
    CHƯA duyệt (REQUIRE_HUMAN_APPROVAL), không phải ALLOW."""

    def test_gate_a_chi_co_synthetic_yeu_cau_duyet_nguoi(self):
        engine = _engine()
        ledger = ApprovalLedger()
        rec = ApprovalLedger.make_synthetic_approval(
            gate_id="GATE_A", scope="test", evidence_content="x",
        )
        ledger.add_approval(rec)

        decision = engine.check_gate("GATE_A", {}, ledger)
        assert decision.decision == GateDecisionEnum.REQUIRE_HUMAN_APPROVAL, (
            "TRƯỚC bản vá: _check_gate_a_clinical() gọi thẳng "
            "check_has_approval() không lọc is_synthetic, nên một "
            "approval MÔ PHỎNG (không phải người) khiến GATE_A được ALLOW. "
            f"Kết quả thực tế: {decision.decision}, {decision.reason_code}"
        )
        assert decision.reason_code == "GATE_A_CLINICAL_PENDING"


class TestDoiChungGateAApprovalNguoiThatVaGateBKhongDoi:
    """Đối chứng — approval NGƯỜI THẬT cho GATE_A vẫn được ALLOW như cũ;
    GATE_B (không đụng trong bản vá này) vẫn hoạt động đúng thiết kế
    gốc của nó (kiểm toàn vẹn evidence_hash toàn ledger)."""

    def test_gate_a_voi_approval_nguoi_that_van_allow(self):
        engine = _engine()
        ledger = ApprovalLedger()
        rec = ApprovalLedger.make_human_approval(
            gate_id="GATE_A", reviewer_role="BAC_SI", reviewer_ref="bs001",
            scope="test", evidence_content="y",
        )
        ledger.add_approval(rec)

        decision = engine.check_gate("GATE_A", {}, ledger)
        assert decision.decision == GateDecisionEnum.ALLOW
        assert decision.reason_code == "GATE_A_APPROVED"

    def test_gate_a_rong_yeu_cau_duyet_nguoi(self):
        engine = _engine()
        decision = engine.check_gate("GATE_A", {}, ApprovalLedger())
        assert decision.decision == GateDecisionEnum.REQUIRE_HUMAN_APPROVAL

    def test_gate_b_khong_bi_anh_huong_boi_ban_va(self):
        # GATE_B vẫn ALLOW khi ledger có MỘT approval bất kỳ (kể cả gate
        # khác) có evidence_hash — hành vi gốc, KHÔNG đổi trong bản vá này.
        engine = _engine()
        ledger = ApprovalLedger()
        rec = ApprovalLedger.make_human_approval(
            gate_id="G2", reviewer_role="IRB_ETHICS_COMMITTEE", reviewer_ref="irb1",
            scope="test", evidence_content="z",
        )
        ledger.add_approval(rec)
        decision = engine.check_gate("GATE_B", {}, ledger)
        assert decision.decision == GateDecisionEnum.ALLOW
        assert decision.reason_code == "GATE_B_LEDGER_CLEAN"
