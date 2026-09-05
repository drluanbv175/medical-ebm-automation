"""Hồi quy phát hiện MEDIUM của Workflow đối kháng đa-agent 2026-09-05 (vòng 5,
task #87) trong
`app/clinical_content/clinical_runtime.py::build_clinical_draft()` — một block
của `PolicyEngine` vì lý do KHÁC cờ đỏ (PII trong case_text, thiếu
evidence_trace_ids) bị BỎ QUA HOÀN TOÀN khi không kèm cờ đỏ nào.

CƠ CHẾ LỖI: bản gốc chỉ chặn khi `not decision.allowed and red_flags` — hai
điều kiện AND. `PolicyEngine().evaluate()` được gọi với
`{"lane": "clinical", "text": case_text, "claim_text": "clinical draft",
"evidence_trace_ids": ..., "red_flag_unresolved": bool(red_flags)}`, và có
ÍT NHẤT hai cách khiến `decision.allowed == False` mà KHÔNG liên quan cờ đỏ:
(1) `case_text` chứa PII-like text → violation EBM-V7-P001 (severity "block");
(2) `evidence_trace_ids` rỗng/thiếu trong khi `claim_text` truthy (luôn truthy
— hardcode "clinical draft") → violation EBM-V7-P002. Khi `red_flags == []`
(rỗng, falsy), điều kiện `not decision.allowed and red_flags` là `True and
False = False` — hàm rơi thẳng xuống nhánh cuối, trả về một ClinicalDraft với
summary "Bản nháp hỗ trợ quyết định lâm sàng, cần review trước khi áp dụng."
— y hệt như thể PolicyEngine CHƯA TỪNG chặn gì, dù nó vừa phát hiện PII hoặc
thiếu truy nguyên chứng cứ.

BẢN VÁ: tách điều kiện `not decision.allowed` ra khỏi `red_flags` — MỌI quyết
định bị PolicyEngine chặn đều dừng workflow thường quy; nhánh cờ đỏ giữ
nguyên thông điệp riêng (test cũ `test_clinical_runtime_stops_on_red_flag_
before_routine_summary` phụ thuộc câu chữ "Dừng workflow"), các lý do khác
được liệt kê nguyên văn từ `PolicyViolation.message`.

Nguyên tắc viết test: gọi THẲNG `build_clinical_draft()` thật, không mock
`PolicyEngine`, dựng input để PolicyEngine chặn qua ĐÚNG nhánh cần kiểm
(PII trong case_text hoặc evidence_trace_ids rỗng) mà KHÔNG có cờ đỏ.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.clinical_content.clinical_runtime import build_clinical_draft  # noqa: E402


class TestPolicyBlockKhongKemCoDoVanPhaiChanWorkflow:
    """★★★ Ca chính — PolicyEngine chặn vì lý do KHÁC cờ đỏ (không có triệu
    chứng cờ đỏ nào trong case_text) phải dừng workflow, KHÔNG được lọt qua
    thành "Bản nháp hỗ trợ quyết định lâm sàng"."""

    def test_thieu_evidence_trace_ids_khong_co_co_do_van_bi_chan(self):
        """Không truyền evidence_trace_ids (context rỗng) → EBM-V7-P002 chặn,
        case_text không chứa từ khoá cờ đỏ nào → red_flags rỗng."""
        draft = build_clinical_draft(
            "run_test_1",
            "Bệnh nhân tái khám định kỳ tăng huyết áp, huyết áp ổn định.",
            claim_ids=["claim_1"],
            context={},
        )
        assert not draft.red_flags, "test này đòi hỏi KHÔNG có cờ đỏ để cô lập nhánh lỗi"
        assert "Dừng workflow" in draft.summary, (
            f"PolicyEngine chặn (thiếu evidence_trace_ids) nhưng summary không "
            f"phản ánh — thực tế: {draft.summary!r}"
        )
        assert "Bản nháp hỗ trợ quyết định lâm sàng" not in draft.summary

    def test_pii_trong_case_text_khong_co_co_do_van_bi_chan(self):
        """case_text chứa PII-like text (số điện thoại) nhưng không có từ
        khoá cờ đỏ nào → EBM-V7-P001 chặn, red_flags vẫn rỗng."""
        draft = build_clinical_draft(
            "run_test_2",
            "Bệnh nhân tái khám định kỳ, liên hệ theo số 0912345678.",
            claim_ids=["claim_1"],
            context={"evidence_trace_ids": ["pmid:12345678"]},
        )
        assert not draft.red_flags, "test này đòi hỏi KHÔNG có cờ đỏ để cô lập nhánh lỗi"
        assert "Dừng workflow" in draft.summary
        assert "Bản nháp hỗ trợ quyết định lâm sàng" not in draft.summary


class TestKhongBlockVanDungNhuCu:
    """Đối chứng bắt buộc — dữ liệu SẠCH (đủ evidence_trace_ids, không PII,
    không cờ đỏ) vẫn phải ra đúng draft hỗ trợ quyết định như hành vi gốc,
    không bị bản vá làm chặn oan."""

    def test_du_dieu_kien_khong_bi_chan_ra_draft_ho_tro_quyet_dinh(self):
        draft = build_clinical_draft(
            "run_test_3",
            "Bệnh nhân tái khám định kỳ tăng huyết áp, huyết áp ổn định.",
            claim_ids=["claim_1"],
            context={"evidence_trace_ids": ["pmid:12345678"]},
        )
        assert not draft.red_flags
        assert "Bản nháp hỗ trợ quyết định lâm sàng" in draft.summary

    def test_thieu_claim_ids_van_bao_chua_du_claim_nhu_cu(self):
        draft = build_clinical_draft(
            "run_test_4",
            "Bệnh nhân tái khám định kỳ tăng huyết áp, huyết áp ổn định.",
            claim_ids=[],
            context={"evidence_trace_ids": ["pmid:12345678"]},
        )
        assert not draft.red_flags
        assert "Chưa đủ claim" in draft.summary


class TestCoDoVanGiuThongDiepRieng:
    """Đối chứng bắt buộc — hành vi cờ đỏ (đã có test cũ ở
    test_v7_export_bridge_and_clinical_runtime.py) không bị thay đổi bởi bản
    vá: vẫn đúng câu thông điệp cờ đỏ riêng, không lẫn với thông điệp chung."""

    def test_co_do_van_ra_dung_thong_diep_rieng(self):
        draft = build_clinical_draft(
            "run_test_5",
            "Ca đã khử định danh có nói khó và méo miệng.",
            claim_ids=["claim_1"],
            context={"evidence_trace_ids": ["pmid:12345678"]},
        )
        assert draft.red_flags
        assert draft.summary == "Dừng workflow thường quy vì có cờ đỏ; cần bác sĩ đánh giá ngay."
