"""Hồi quy và đối kháng cho hợp đồng chất lượng G5."""

from __future__ import annotations

import csv
import json
import os
import stat
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOLS_DIR))
sys.path.insert(0, str(REPO_ROOT))

import clean_research_dataset as CLEAN  # noqa: E402
import g5_quality_gate as G5Q  # noqa: E402
import gate_contract as GC  # noqa: E402
import run_g5_auto as G5  # noqa: E402

from tests.g5_test_helpers import (  # noqa: E402
    append_signed_approval,
    configure_test_signing_key,
    prepare_locked_g5_study,
    write_g5_toolkit,
)


def _csv(path: Path, text: str) -> Path:
    path.write_text(text.strip() + "\n", encoding="utf-8", newline="\n")
    return path


def _source(path: Path) -> Path:
    return _csv(
        path,
        """
record_id,age,sex,exposure_var,primary_outcome
S001,45,F,0,0
S002,52,M,1,1
""",
    )


def test_generated_redcap_dictionary_is_real_18_column_csv(tmp_path):
    rows, _ = G5.build_redcap_rows("cohort", "Tăng huyết áp")
    path, count = G5.generate_csv("CSV-VALID", tmp_path, rows)

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        parsed = list(reader)

    assert len(reader.fieldnames or []) == 18
    assert len(parsed) == count == len(rows)
    assert parsed[0]["Variable / Field Name"] == rows[0][0]
    dictionary = CLEAN._load_dictionary(path)
    assert len(dictionary["variables"]) == count


def test_dictionary_blocks_direct_identifiers_without_false_positive_on_drug_name(
    tmp_path,
):
    path = tmp_path / "dictionary.csv"
    path.write_text(
        (
            "Variable / Field Name,Form Name,Field Type,Field Label,Identifier?\n"
            "drug_name,meds,text,Tên thuốc,\n"
            "patient_name,admin,text,Họ tên,y\n"
        ),
        encoding="utf-8",
    )
    result = G5Q._read_redcap_dictionary(path)
    issues = " ".join(result["issues"])
    assert "patient_name" in issues
    assert "redcap_identifier_rows" in issues
    assert "drug_name" not in issues


def test_draft_toolkit_cannot_claim_g5_pass(tmp_path):
    study = "G5-DRAFT"
    out_dir = tmp_path / "exports" / study
    write_g5_toolkit(study, out_dir)

    report = G5Q.evaluate_study(
        study,
        out_dir,
        repo_root=tmp_path,
        write=True,
    )

    assert report["status"] == G5Q.STATUS_DRAFT
    assert report["real_data_present"] is False
    assert report["technical_lock_valid"] is False
    assert report["human_approval_valid"] is False


def test_full_chain_is_ready_then_human_signature_makes_pass(
    tmp_path,
    monkeypatch,
):
    configure_test_signing_key(tmp_path, monkeypatch)
    study = "G5-E2E"
    exports_root = tmp_path / "exports"
    _, report = prepare_locked_g5_study(
        study,
        _source(tmp_path / "source.csv"),
        exports_root=exports_root,
        repo_root=tmp_path,
        approve_g5=False,
    )
    assert report["status"] == G5Q.STATUS_READY

    out_dir = exports_root / study
    append_signed_approval(
        study,
        out_dir / "G5_checkpoint.json",
        "G5",
        "DATA_GOVERNANCE_QA_REVIEWER",
        repo_root=tmp_path,
    )
    report = G5Q.evaluate_study(
        study,
        out_dir,
        repo_root=tmp_path,
        write=True,
    )

    assert report["status"] == G5Q.STATUS_LOCKED
    assert report["technical_lock_valid"] is True
    assert report["human_approval_valid"] is True
    assert GC.g5_quality_contract_satisfied(study, repo_root=tmp_path) is True


def test_unknown_query_status_invalidates_existing_lock(tmp_path, monkeypatch):
    configure_test_signing_key(tmp_path, monkeypatch)
    study = "G5-QUERY-TAMPER"
    exports_root = tmp_path / "exports"
    _, _ = prepare_locked_g5_study(
        study,
        _source(tmp_path / "source.csv"),
        exports_root=exports_root,
        repo_root=tmp_path,
    )
    out_dir = exports_root / study
    cleaning = json.loads(
        (out_dir / CLEAN.REPORT_NAME).read_text(encoding="utf-8")
    )
    query_path = out_dir / cleaning["query_log"]
    query_path.write_text(
        query_path.read_text(encoding="utf-8").replace("closed", "mystery"),
        encoding="utf-8",
    )

    report = G5Q.evaluate_study(
        study,
        out_dir,
        repo_root=tmp_path,
        write=False,
    )

    assert report["status"] == G5Q.STATUS_BLOCKED
    query_criterion = next(
        row for row in report["automatic_criteria"] if row["id"] == "G5-AUTO-08"
    )
    assert query_criterion["status"] == "BLOCK"


def test_locked_dataset_tamper_invalidates_g5(tmp_path, monkeypatch):
    configure_test_signing_key(tmp_path, monkeypatch)
    study = "G5-DATA-TAMPER"
    exports_root = tmp_path / "exports"
    locked_path, _ = prepare_locked_g5_study(
        study,
        _source(tmp_path / "source.csv"),
        exports_root=exports_root,
        repo_root=tmp_path,
    )
    os.chmod(locked_path, stat.S_IRUSR | stat.S_IWUSR)
    with locked_path.open("a", encoding="utf-8") as handle:
        handle.write("S999,99,F,1,1\n")

    report = G5Q.evaluate_study(
        study,
        exports_root / study,
        repo_root=tmp_path,
        write=False,
    )

    assert report["status"] == G5Q.STATUS_BLOCKED
    lock_criterion = next(
        row for row in report["automatic_criteria"] if row["id"] == "G5-AUTO-09"
    )
    assert lock_criterion["status"] == "BLOCK"


def test_operational_evidence_tamper_invalidates_g5(tmp_path, monkeypatch):
    configure_test_signing_key(tmp_path, monkeypatch)
    study = "G5-OPS-TAMPER"
    exports_root = tmp_path / "exports"
    _, _ = prepare_locked_g5_study(
        study,
        _source(tmp_path / "source.csv"),
        exports_root=exports_root,
        repo_root=tmp_path,
    )
    out_dir = exports_root / study
    operations_path = out_dir / G5Q.OPERATIONAL_READINESS_JSON
    operations = json.loads(operations_path.read_text(encoding="utf-8"))
    operations["backup_restore_test"]["evidence_ref"] = "PYTEST-BACKUP-TAMPERED"
    operations_path.write_text(
        json.dumps(operations, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    # Kẻ sửa đồng thời cả file vận hành và manifest vẫn không được qua, vì
    # checkpoint đã ký giữ hash gốc của toàn bộ chuỗi provenance.
    manifest_path = out_dir / "DATA_LOCK_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["operational_readiness_sha256"] = G5Q._sha256(operations_path)
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    report = G5Q.evaluate_study(
        study,
        out_dir,
        repo_root=tmp_path,
        write=False,
    )

    assert report["status"] == G5Q.STATUS_BLOCKED
    operations_criterion = next(
        row for row in report["automatic_criteria"] if row["id"] == "G5-AUTO-04"
    )
    lock_criterion = next(
        row for row in report["automatic_criteria"] if row["id"] == "G5-AUTO-09"
    )
    assert operations_criterion["status"] == "PASS"
    assert lock_criterion["status"] == "BLOCK"
