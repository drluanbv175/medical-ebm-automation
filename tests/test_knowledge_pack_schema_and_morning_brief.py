import json
from datetime import datetime
from pathlib import Path

from app.services.knowledge_pack_release_gate import (
    assess_all_pack_release_readiness,
    assess_pack_release_readiness,
    release_readiness_payload,
    summarize_release_readiness,
    write_release_readiness_report,
)
from app.services.knowledge_pack_schema import (
    normalize_drug_safety_rules,
    validate_pack_version,
)
from app.services.knowledge_pack_service import KnowledgePackService
from tools import gen_morning_brief

ROOT = Path(__file__).resolve().parents[1]
PACKS_DIR = ROOT / "knowledge-packs"


def test_all_current_knowledge_packs_pass_schema_validator():
    results = [
        validate_pack_version(pack_dir)
        for pack_dir in sorted(PACKS_DIR.iterdir())
        if pack_dir.is_dir()
    ]
    failures = {
        result.pack_id: [f"{issue.file}:{issue.message}" for issue in result.errors]
        for result in results
        if not result.ok
    }

    assert len(results) == 10
    assert failures == {}


def test_knowledge_pack_service_validate_all_and_red_flags_are_loaded():
    service = KnowledgePackService(packs_dir=PACKS_DIR).load()
    results = service.validate_all()

    assert all(result.ok for result in results)
    assert service.status_report()["complete_packs"] == 10
    assert all(len(pack.red_flags) > 0 for pack in service.complete_packs())


def test_current_knowledge_packs_are_review_ready_but_not_clinical_release_ready():
    results = assess_all_pack_release_readiness(PACKS_DIR)
    summary = summarize_release_readiness(results)

    assert summary["total"] == 10
    assert summary["schema_ok"] == 10
    assert summary["review_ready"] == 10
    assert summary["clinical_release_ready"] == 0
    assert summary["patient_facing_ready"] == 0
    assert summary["blocked"] == 10


def test_hypertension_pack_release_gate_requires_real_approval_and_verified_manifest():
    result = assess_pack_release_readiness(PACKS_DIR / "hypertension_adult_outpatient")
    blockers = {f"{issue.file}:{issue.message}" for issue in result.blockers}

    assert result.schema_ok is True
    assert result.review_ready is True
    assert result.clinical_release_ready is False
    assert result.approval_record_present is True
    assert result.evidence_manifest_present is True
    assert "13_approval_record.json:approval_status_not_approved" in blockers
    assert "13_approval_record.json:next_review_due_missing" in blockers
    assert "10_evidence_manifest.json:manifest_release_allowed_false" in blockers


def test_release_readiness_payload_is_machine_readable_and_blocks_release():
    results = assess_all_pack_release_readiness(PACKS_DIR)
    payload = release_readiness_payload(results, generated_at="2026-07-15T00:00:00+00:00")

    assert payload["kind"] == "knowledge_pack_release_readiness_report"
    assert payload["generated_at"] == "2026-07-15T00:00:00+00:00"
    assert payload["summary"]["total"] == 10
    assert payload["summary"]["clinical_release_ready"] == 0
    assert payload["clinical_release_allowed"] is False
    assert len(payload["packs"]) == 10
    assert payload["blocker_counts"]["01_scope.yaml:clinical_release_allowed_false"] == 10


def test_write_release_readiness_report_outputs_json(tmp_path):
    output = tmp_path / "knowledge_pack_release_readiness.json"
    path = write_release_readiness_report(packs_dir=PACKS_DIR, output_path=output)
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert path == output
    assert payload["kind"] == "knowledge_pack_release_readiness_report"
    assert payload["summary"]["review_ready"] == 10
    assert payload["clinical_release_allowed"] is False


def test_drug_safety_normalizer_supports_gate_style_rules():
    normalized = normalize_drug_safety_rules({
        "medication_safety_required": True,
        "rules": [
            {
                "rule_id": "htn_med_current_medications_required",
                "description": "Need current medication list before medication-related recommendation.",
                "gate": "WAITING_FOR_INPUT",
            }
        ],
    })

    assert normalized == [
        {
            "rule_id": "htn_med_current_medications_required",
            "drug": "",
            "condition": "",
            "description": "Need current medication list before medication-related recommendation.",
            "priority": "MEDIUM",
            "source": "",
            "gate": "WAITING_FOR_INPUT",
        }
    ]


def test_morning_brief_preview_handles_all_current_packs():
    brief = gen_morning_brief.generate_brief(preview=True)

    assert "10/10" in brief
    assert "Clinical release ready" in brief
    assert "**0/10**" in brief
    assert "hypertension_adult_outpatient" not in brief
    assert "DRAFT" in brief
    assert "Metformin" in brief


def test_morning_brief_pack_filter_handles_hypertension_gate_schema():
    brief = gen_morning_brief.generate_brief(
        target_pack="hypertension_adult_outpatient",
        preview=True,
    )

    assert "Tăng huyết áp" in brief or "TÄƒng huyáº¿t Ã¡p" in brief
    assert "Cảnh báo thuốc" not in brief
    assert "DỰ THẢO" in brief or "Dá»° THáº¢O" in brief


def test_morning_brief_write_outputs_include_release_manifest(tmp_path, monkeypatch):
    monkeypatch.setattr(gen_morning_brief, "BASE", tmp_path)
    monkeypatch.setattr(gen_morning_brief, "RESULTS_DIR", tmp_path / "results")
    monkeypatch.setattr(gen_morning_brief, "EXPORTS_DIR", tmp_path / "exports" / "morning_brief")

    fixed_output, dated_output = gen_morning_brief.write_brief_outputs(
        "DRAFT test brief",
        now=datetime(2026, 7, 15, 6, 30),
    )
    fixed_manifest = tmp_path / "results" / "daily_ebm_brief_manifest.json"
    dated_manifest = tmp_path / "exports" / "morning_brief" / "EBM_SANG_2026-07-15_manifest.json"
    payload = json.loads(fixed_manifest.read_text(encoding="utf-8"))

    assert fixed_output.exists()
    assert dated_output.exists()
    assert dated_manifest.exists()
    assert payload["kind"] == "morning_brief_run_manifest"
    assert payload["clinical_release_allowed"] is False
    assert payload["release_readiness"]["clinical_release_ready"] == 0
    assert payload["release_readiness"]["total"] == 10
