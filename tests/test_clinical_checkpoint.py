# -*- coding: utf-8 -*-
"""Test tools/clinical_checkpoint.py — máy kiểm sổ trạng thái checkpoint lâm sàng/NC."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import clinical_checkpoint as CC  # noqa: E402


def _block(case="CA-001", cong="A", ngay="2026-07-04", loai="lâm sàng",
           san_pham="Khuyến nghị điều trị THA", con_lai="(không)",
           buoc_ke="Chờ bác sĩ áp dụng", agent="so-cai-ghi-nho",
           guardrail="ĐẠT"):
    return (
        f"## CHECKPOINT [{ngay}] — đề tài/ca: {case}\n"
        f"- cong_vua_qua:   {cong}\n"
        f"- ngay:           {ngay}\n"
        f"- loai_nhiem_vu:  {loai}\n"
        f"- san_pham_vua_xong: {san_pham}\n"
        f"- danh_muc_🔴_con_lai: {con_lai}\n"
        f"- buoc_ke:        {buoc_ke}\n"
        f"- agent_ghi:      {agent}\n"
        f"- guardrail_dau_ra: {guardrail}\n"
    )


def test_parse_empty_log_returns_empty_list():
    text = "# SỔ TRẠNG THÁI\n\n_(Chưa có checkpoint nào.)_\n"
    assert CC.parse_checkpoint_log(text) == []


def test_parse_single_valid_block():
    text = _block()
    entries = CC.parse_checkpoint_log(text)
    assert len(entries) == 1
    e = entries[0]
    assert e.case_label == "CA-001"
    assert e.cong_vua_qua == "A"
    assert e.missing_fields == []


def test_parse_two_blocks_in_sequence():
    text = _block(case="CA-002", cong="A") + "\n" + _block(case="CA-002", cong="B")
    entries = CC.parse_checkpoint_log(text)
    assert len(entries) == 2
    assert entries[0].cong_vua_qua == "A"
    assert entries[1].cong_vua_qua == "B"


def test_parse_raises_on_header_with_no_fields():
    text = (
        "## CHECKPOINT [2026-07-04] — đề tài/ca: CA-BAD\n\n"
        "## CHECKPOINT [2026-07-05] — đề tài/ca: CA-002\n- cong_vua_qua: A\n"
    )
    import pytest
    with pytest.raises(CC.CheckpointFormatError):
        CC.parse_checkpoint_log(text)


def test_validate_clean_entry_passes():
    entries = CC.parse_checkpoint_log(_block())
    violations = CC.validate_entries(entries)
    assert violations == []


def test_validate_missing_field_flagged():
    text = (
        "## CHECKPOINT [2026-07-04] — đề tài/ca: CA-003\n"
        "- cong_vua_qua:   A\n"
        "- ngay:           2026-07-04\n"
    )
    entries = CC.parse_checkpoint_log(text)
    violations = CC.validate_entries(entries)
    codes = {v.code for v in violations}
    assert "MISSING_FIELD" in codes


def test_validate_invalid_gate_token_flagged():
    entries = CC.parse_checkpoint_log(_block(cong="XYZ"))
    violations = CC.validate_entries(entries)
    assert any(v.code == "INVALID_GATE_TOKEN" for v in violations)


def test_validate_research_gate_tokens_accepted():
    entries = CC.parse_checkpoint_log(_block(loai="nghiên cứu", cong="G3"))
    violations = CC.validate_entries(entries)
    assert violations == []


def test_validate_invalid_date_flagged():
    entries = CC.parse_checkpoint_log(_block(ngay="04/07/2026"))
    violations = CC.validate_entries(entries)
    assert any(v.code == "INVALID_DATE" for v in violations)


def test_validate_invalid_task_type_flagged():
    entries = CC.parse_checkpoint_log(_block(loai="hành chính"))
    violations = CC.validate_entries(entries)
    assert any(v.code == "INVALID_TASK_TYPE" for v in violations)


def test_validate_gate_a_with_outstanding_red_items_is_violation():
    # Bất biến CỐT LÕI: không được ghi ĐÃ QUA Cổng A khi còn 🔴 bắt buộc.
    entries = CC.parse_checkpoint_log(_block(cong="A", con_lai="C6 chưa rà đơn"))
    violations = CC.validate_entries(entries)
    assert any(v.code == "GATE_WITH_OUTSTANDING_RED_ITEMS" for v in violations)


def test_validate_non_gate_entry_with_red_items_is_not_violation():
    # Bước trung gian (không phải cổng A/B) vẫn có thể còn 🔴 -> không phải lỗi.
    entries = CC.parse_checkpoint_log(_block(cong="G3", loai="nghiên cứu",
                                             con_lai="chờ dữ liệu thô"))
    violations = CC.validate_entries(entries)
    assert not any(v.code == "GATE_WITH_OUTSTANDING_RED_ITEMS" for v in violations)


def test_validate_gate_a_without_guardrail_verdict_is_violation():
    # 2026-07-12: guardrail phải THẬT SỰ chạy và ĐẠT trước khi coi Cổng A/B là xong —
    # trường rỗng/thiếu bị chặn, không còn chỉ là quy ước cấp prompt.
    entries = CC.parse_checkpoint_log(_block(cong="A", guardrail=""))
    violations = CC.validate_entries(entries)
    assert any(v.code == "GATE_WITHOUT_GUARDRAIL_VERDICT" for v in violations)


def test_validate_gate_a_with_guardrail_not_dat_is_violation():
    entries = CC.parse_checkpoint_log(_block(cong="A", guardrail="TRẢ-VỀ-SỬA"))
    violations = CC.validate_entries(entries)
    assert any(v.code == "GATE_WITHOUT_GUARDRAIL_VERDICT" for v in violations)


def test_validate_gate_a_with_guardrail_dat_is_clean():
    entries = CC.parse_checkpoint_log(_block(cong="A", guardrail="ĐẠT"))
    violations = CC.validate_entries(entries)
    assert not any(v.code == "GATE_WITHOUT_GUARDRAIL_VERDICT" for v in violations)


def test_validate_non_gate_entry_without_guardrail_is_not_violation():
    # G-cổng nghiên cứu trung gian (không phải A/B) không bắt buộc guardrail_dau_ra.
    entries = CC.parse_checkpoint_log(_block(cong="G3", loai="nghiên cứu", guardrail=""))
    violations = CC.validate_entries(entries)
    assert not any(v.code == "GATE_WITHOUT_GUARDRAIL_VERDICT" for v in violations)


def test_validate_gate_b_before_gate_a_same_case_is_violation():
    text = _block(case="CA-004", cong="B") + "\n" + _block(case="CA-004", cong="A")
    entries = CC.parse_checkpoint_log(text)
    violations = CC.validate_entries(entries)
    assert any(v.code == "GATE_B_BEFORE_GATE_A" for v in violations)


def test_validate_gate_a_then_b_same_case_is_clean():
    text = _block(case="CA-005", cong="A") + "\n" + _block(case="CA-005", cong="B")
    entries = CC.parse_checkpoint_log(text)
    violations = CC.validate_entries(entries)
    assert not any(v.code == "GATE_B_BEFORE_GATE_A" for v in violations)


def test_validate_gate_b_before_a_different_cases_not_flagged():
    # Cổng B của CA-006 không liên quan tới CA-007 (chưa có Cổng A) -> không nhầm.
    text = _block(case="CA-006", cong="A") + "\n" + _block(case="CA-006", cong="B") + \
        "\n" + _block(case="CA-007", cong="A")
    entries = CC.parse_checkpoint_log(text)
    violations = CC.validate_entries(entries)
    assert not any(v.code == "GATE_B_BEFORE_GATE_A" for v in violations)


def test_validate_pii_phone_number_detected():
    entries = CC.parse_checkpoint_log(_block(san_pham="Liên hệ 0912345678 xác nhận"))
    violations = CC.validate_entries(entries)
    assert any(v.code == "PII_DETECTED" for v in violations)


def test_validate_pii_absent_in_clean_entry():
    entries = CC.parse_checkpoint_log(_block())
    violations = CC.validate_entries(entries)
    assert not any(v.code == "PII_DETECTED" for v in violations)


def test_format_report_verdict_dat_when_no_violations():
    entries = CC.parse_checkpoint_log(_block())
    violations = CC.validate_entries(entries)
    report = CC.format_report(entries, violations)
    assert report["verdict"] == "ĐẠT"


def test_format_report_verdict_tra_ve_sua_when_violations():
    entries = CC.parse_checkpoint_log(_block(cong="A", con_lai="còn thiếu"))
    violations = CC.validate_entries(entries)
    report = CC.format_report(entries, violations)
    assert report["verdict"] == "TRẢ-VỀ-SỬA"
