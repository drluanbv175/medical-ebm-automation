"""Hồi quy phát hiện #4 (audit vòng 36, 2026-09-06) trong
runtime/workflow_state_machine.py — guard "thiếu evidence_reference"
không chuẩn hoá hoa/thường trước khi so, chuỗi literal "None" (từ
str(None)) lọt qua.

CƠ CHẾ LỖI (TRƯỚC bản vá):
    if not evidence_reference or evidence_reference.strip() in ("", "none"):

So sánh chỉ khớp chuỗi rỗng hoặc "none" viết THƯỜNG tuyệt đối — không
`.lower()` trước khi so. Một caller lỡ truyền
`evidence_reference=str(x)` với `x is None` (mẫu lỗi tự nhiên khi
optional field chưa gán) tạo ra chuỗi `"None"` (N hoa) — không khớp
`"none"` — guard KHÔNG chặn, transition được ALLOWED dù "bằng chứng"
thực chất là chuỗi rác từ str(None).

BẢN VÁ: `.strip().lower() in ("", "none")`.

PHẠM VI ẢNH HƯỞNG (xác minh bằng grep toàn repo trước khi sửa, không
suy diễn): caller thật DUY NHẤT của `WorkflowStateMachine.transition()`
ngoài tests/ là `runtime/controlled_orchestrator.py` (nhánh MỒ CÔI theo
CLAUDE.md) — nó luôn truyền
`evidence_reference=f"audit_event:{self._audit_logger.run_id}"`, một
chuỗi f-string có prefix thật, KHÔNG BAO GIỜ rơi vào trường hợp literal
"None". Bug vẫn THẬT (tái hiện được trực tiếp qua API public) nên vẫn
sửa — mức độ latent, chưa bị khai thác bởi bất kỳ caller nào hiện có
trong repo (kể cả caller mồ côi)."""
from __future__ import annotations

from runtime.approval_ledger import ApprovalLedger
from runtime.schemas import WorkflowStateEnum
from runtime.workflow_state_machine import WorkflowStateMachine


class TestCaChinhChuoiNoneHoaBiChan:
    """★★★ Ca chính — evidence_reference=str(None) (chuỗi "None" N hoa)
    phải bị BLOCKED, không được ALLOWED."""

    def test_str_none_bi_chan(self):
        sm = WorkflowStateMachine(workflow_id="wf-test-1")
        t = sm.transition(
            requested_state=WorkflowStateEnum.METHOD_REVIEW,
            authorized_by="someone",
            evidence_reference=str(None),  # → "None" (N hoa)
            approval_ledger=ApprovalLedger(),
        )
        assert t.decision == "BLOCKED", (
            "TRƯỚC bản vá: so sánh 'in (\"\", \"none\")' không .lower() "
            "trước, nên chuỗi 'None' (N hoa, từ str(None)) không khớp "
            f"'none' và lọt qua guard. Kết quả thực tế: {t.decision}, "
            f"{t.reason}"
        )
        assert t.reason == "MISSING_EVIDENCE_REFERENCE"
        assert sm.current_state == WorkflowStateEnum.DRAFT

    def test_chuoi_none_viet_hoa_toan_bo_cung_bi_chan(self):
        sm = WorkflowStateMachine(workflow_id="wf-test-2")
        t = sm.transition(
            requested_state=WorkflowStateEnum.METHOD_REVIEW,
            authorized_by="someone",
            evidence_reference="NONE",
            approval_ledger=ApprovalLedger(),
        )
        assert t.decision == "BLOCKED"


class TestDoiChungEvidenceHopLeVanChoQua:
    """Đối chứng — evidence_reference thật (hoặc chuỗi rỗng, hoặc
    "none" viết thường) vẫn hoạt động đúng như cũ."""

    def test_evidence_hop_le_van_allowed(self):
        sm = WorkflowStateMachine(workflow_id="wf-test-3")
        t = sm.transition(
            requested_state=WorkflowStateEnum.METHOD_REVIEW,
            authorized_by="someone",
            evidence_reference="audit_event:run-123",
            approval_ledger=ApprovalLedger(),
        )
        assert t.decision == "ALLOWED"
        assert sm.current_state == WorkflowStateEnum.METHOD_REVIEW

    def test_chuoi_rong_van_bi_chan_nhu_cu(self):
        sm = WorkflowStateMachine(workflow_id="wf-test-4")
        t = sm.transition(
            requested_state=WorkflowStateEnum.METHOD_REVIEW,
            authorized_by="someone",
            evidence_reference="",
            approval_ledger=ApprovalLedger(),
        )
        assert t.decision == "BLOCKED"
        assert t.reason == "MISSING_EVIDENCE_REFERENCE"

    def test_none_viet_thuong_van_bi_chan_nhu_cu(self):
        sm = WorkflowStateMachine(workflow_id="wf-test-5")
        t = sm.transition(
            requested_state=WorkflowStateEnum.METHOD_REVIEW,
            authorized_by="someone",
            evidence_reference="none",
            approval_ledger=ApprovalLedger(),
        )
        assert t.decision == "BLOCKED"
