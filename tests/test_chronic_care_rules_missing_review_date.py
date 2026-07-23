# -*- coding: utf-8 -*-
"""Hồi quy vòng lặp kiểm tra-hoàn thiện vòng 11 (2026-07-23, dimension
third_chronic_care_python_system, phát hiện LOW):
evaluate_chronic_care_rules() trước đây gọi
`datetime.fromisoformat(str(status.get("next_review_due_at")))` không kiểm
tra key tồn tại/định dạng hợp lệ — nếu thiếu trường này, `status.get(...)`
trả None, `str(None)` = "None", và `datetime.fromisoformat("None")` ném
ValueError không được bắt, sập toàn bộ luồng rule-evaluation. Hiện tại được
che chắn vì build_synthetic_case_pack() luôn set trường này, nhưng nếu hàm
này được tái sử dụng với case object thiếu trường (vd nối vào nguồn dữ liệu
thật trong tương lai), một case thiếu trường sẽ làm sập cả pipeline.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.chronic_care.rules import evaluate_chronic_care_rules
from app.chronic_care.synthetic_cases import SyntheticChronicCareCase


def _base_case(**status_overrides) -> SyntheticChronicCareCase:
    return SyntheticChronicCareCase(
        patient_reference_id="SYN-TEST-001",
        age_band="40-49",
        sex="F",
        program_code="HTN",
        synthetic_status_fields=status_overrides,
    )


def test_missing_next_review_due_at_does_not_crash():
    case = _base_case()  # KHÔNG có "next_review_due_at" trong dict
    actions = evaluate_chronic_care_rules(case)
    assert not any(a.rule_id == "CC-001" for a in actions), (
        "Thiếu ngày hẹn thì KHÔNG được coi là quá hạn (fail-closed, không bịa)"
    )


def test_malformed_next_review_due_at_does_not_crash():
    case = _base_case(next_review_due_at="not-a-real-date")
    actions = evaluate_chronic_care_rules(case)
    assert not any(a.rule_id == "CC-001" for a in actions)


def test_valid_overdue_date_still_triggers_cc001():
    past = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
    case = _base_case(next_review_due_at=past)
    actions = evaluate_chronic_care_rules(case)
    assert any(a.rule_id == "CC-001" for a in actions), (
        "Ngày hẹn hợp lệ đã quá hạn vẫn phải kích hoạt CC-001 như trước khi sửa"
    )


def test_valid_future_date_does_not_trigger_cc001():
    future = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
    case = _base_case(next_review_due_at=future)
    actions = evaluate_chronic_care_rules(case)
    assert not any(a.rule_id == "CC-001" for a in actions)
