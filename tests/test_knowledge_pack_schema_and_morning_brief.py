from pathlib import Path

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
