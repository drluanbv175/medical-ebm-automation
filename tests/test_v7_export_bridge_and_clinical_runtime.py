import json

import pytest

from app.clinical_content.clinical_knowledge_pack_standard import ClinicalKnowledgePack
from app.clinical_content.clinical_runtime import build_clinical_draft
from app.clinical_content.vietnam_local_adaptation import needs_local_confirmation
from app.core.export_policy import classify_export_file
from app.dashboard.v7_registry import default_v7_dashboard_sections
from app.export_bridge.chatgpt_project_bridge import prepare_chatgpt_project_export, write_manifest
from app.patient_education.patient_education import create_leaflet


def test_export_policy_blocks_raw_data_and_allows_safe_markdown(tmp_path):
    safe = tmp_path / "safe.md"
    safe.write_text("Tài liệu agent EBM đã khử định danh. PMID 12345678.", encoding="utf-8", newline="\n")
    raw = tmp_path / "dataset.db"
    raw.write_bytes(b"sqlite-like")

    safe_decision = classify_export_file(safe)
    raw_decision = classify_export_file(raw)

    assert safe_decision.allowed
    assert safe_decision.sha256
    assert not raw_decision.allowed
    assert "raw_or_binary_dataset" in raw_decision.reasons


def test_export_policy_blocks_bare_national_id_labels(tmp_path):
    """Hồi quy HIGH (vòng lặp kiểm tra-hoàn thiện vòng 3, 2026-07-21):
    classify_export_file() chỉ gọi contains_pii_text() (không có
    _matches_sensitive_id() như agents.py/knowledge.py) — trước bản vá,
    _MRN trong policy_engine.py không nhận diện nhãn 'cccd'/'cmnd'/'căn cước'/
    'patient id'/'bệnh nhân', khiến manifest export báo safe_to_upload=True
    sai cho file có các nhãn này.

    KHÔNG còn 'số bệnh nhân <số>' trong danh sách (vòng 4, 2026-07-21): đó là
    câu SỐ LƯỢNG bệnh nhân ("Số bệnh nhân: 1000 tham gia nghiên cứu"), không
    phải nhãn mã định danh — _MRN đã thu hẹp có chủ đích để hết false-positive
    này; nhãn mã định danh thật dùng 'mã bệnh nhân'/'mã số bệnh nhân' (vẫn
    được chặn, xem case bên dưới)."""
    for text in (
        "Hồ sơ: CCCD: 012345678901",
        "CMND 123456789",
        "căn cước: 012345678901",
        "Patient ID: AB-123456",
        "mã bệnh nhân: 012345678901",
    ):
        f = tmp_path / "demo.md"
        f.write_text(text, encoding="utf-8", newline="\n")
        decision = classify_export_file(f)
        assert not decision.allowed, f"Không chặn được: {text!r}"
        assert "pii_like_text" in decision.reasons


def test_chatgpt_bridge_requires_feature_flag_and_writes_manifest(tmp_path):
    safe = tmp_path / "agent.md"
    safe.write_text("Agent EBM export. Cần bác sĩ kiểm chứng.", encoding="utf-8", newline="\n")

    with pytest.raises(PermissionError):
        prepare_chatgpt_project_export(tmp_path, [safe], feature_flags={})

    export = prepare_chatgpt_project_export(
        tmp_path,
        [safe],
        feature_flags={"v7_chatgpt_project_export": True},
    )
    manifest_path = write_manifest(export, tmp_path / "manifest.json")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert str(safe) in manifest["files"]
    assert manifest["safe_to_upload"] is True
    assert manifest["system_version"] == "EBM_OS_V7_PHASE_2A"
    assert export.blocked_files == []


def test_clinical_runtime_stops_on_red_flag_before_routine_summary():
    draft = build_clinical_draft(
        "run_1",
        "Ca đã khử định danh có nói khó và méo miệng.",
        claim_ids=["claim_1"],
        context={"evidence_trace_ids": ["pmid:12345678"]},
    )

    assert draft.red_flags
    assert "Dừng workflow" in draft.summary


def test_knowledge_pack_patient_education_and_dashboard_contracts():
    pack = ClinicalKnowledgePack(
        pack_id="ckp_1",
        topic="Bệnh động mạch máu não",
        version="2026.06",
        scope="outpatient_ebm",
        evidence_ids=["ev_1"],
        claim_ids=["claim_1"],
        vietnam_localization=needs_local_confirmation().as_metadata(),
    )
    pack.validate()

    leaflet = create_leaflet("Bệnh động mạch máu não", "Nội dung giáo dục đã được bác sĩ kiểm tra.", True)
    assert leaflet.can_export()

    sections = default_v7_dashboard_sections()
    assert {section.section_id for section in sections} >= {"evidence_delta", "approval_center", "chatgpt_bridge"}
