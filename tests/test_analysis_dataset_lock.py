from __future__ import annotations

import json
import stat
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import lock_analysis_dataset as LAD  # noqa: E402
import run_g10_assemble as G10  # noqa: E402
import skill_standards as S  # noqa: E402

from tests.g5_test_helpers import (  # noqa: E402
    configure_test_signing_key,
    prepare_locked_g5_study,
)
from tests.test_g10_assemble import _write_cross_sectional_fixture  # noqa: E402


def _csv(path: Path, text: str) -> Path:
    path.write_text(text.strip() + "\n", encoding="utf-8")
    return path


def _closed_query_log(path: Path) -> Path:
    return _csv(
        path,
        """
timestamp,issue_type,column,row,detail,status,owner,resolution
2026-07-13,INTAKE_CHECK,,,ok,closed,data manager,closed
""",
    )


def _open_query_log(path: Path) -> Path:
    return _csv(
        path,
        """
timestamp,issue_type,column,row,detail,status,owner,resolution
2026-07-13,RANGE_CHECK,age,2,out of range,open,data manager,
""",
    )


def _clean_dataset(path: Path) -> Path:
    return _csv(
        path,
        """
record_id,age,sex,exposure_var,primary_outcome
S001,45,F,1,0
S002,52,M,0,1
""",
    )


def _lock_kwargs(query_log: Path) -> dict:
    return {
        "lock_date": "2026-07-13",
        "reviewer_role": "DATA_GOVERNANCE_QA_REVIEWER",
        "reviewer_ref": "PYTEST-G5-REVIEWER",
        "sap_version": "1.0",
        "query_log": query_log,
        "confirm_deidentified": True,
        "confirm_clean_copy": True,
        "confirm_no_open_query": True,
        "confirm_sap_locked": True,
        "confirm_dictionary_crf_aligned": True,
        "confirm_access_control_reviewed": True,
        "confirm_backup_restore_tested": True,
        "confirm_retention_plan": True,
        "confirm_protocol_deviations_reconciled": True,
    }


def test_lock_clean_dataset_copies_readonly_and_updates_meta(tmp_path, monkeypatch):
    clean = _clean_dataset(tmp_path / "df_clean.csv")
    configure_test_signing_key(tmp_path, monkeypatch)
    locked_path, _ = prepare_locked_g5_study(
        "LOCK-OK",
        clean,
        exports_root=tmp_path / "exports",
        repo_root=tmp_path,
    )

    out_dir = tmp_path / "exports" / "LOCK-OK"
    manifest = json.loads(
        (out_dir / "DATA_LOCK_manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["status"] == LAD.LOCKED_STATUS
    assert manifest["analysis_allowed"] is True
    assert locked_path.exists()
    assert locked_path.stat().st_mode & stat.S_IWUSR == 0
    assert (out_dir / "DATA_LOCK_manifest.json").exists()
    assert (out_dir / "DATA_LOCK_memo.md").exists()

    meta = json.loads((out_dir / "study_meta.json").read_text(encoding="utf-8"))
    assert meta["data_lock_date"] == manifest["lock_date"]
    assert meta["real_data_lock"]["status"] == LAD.LOCKED_STATUS
    assert S.real_world_signals({"G5": {}}, meta)["db_locked"] is True


def test_lock_blocks_without_required_confirmations(tmp_path):
    clean = _clean_dataset(tmp_path / "df_clean.csv")
    qlog = _closed_query_log(tmp_path / "query_log.csv")

    manifest = LAD.lock_dataset(
        "LOCK-MISSING",
        clean,
        exports_root=tmp_path / "exports",
        lock_date="2026-07-13",
        reviewer_role="DATA_GOVERNANCE_QA_REVIEWER",
        reviewer_ref="PYTEST-G5-REVIEWER",
        sap_version="1.0",
        query_log=qlog,
        confirm_deidentified=True,
        confirm_clean_copy=False,
        confirm_no_open_query=True,
        confirm_sap_locked=True,
        confirm_dictionary_crf_aligned=True,
        confirm_access_control_reviewed=True,
        confirm_backup_restore_tested=True,
        confirm_retention_plan=True,
        confirm_protocol_deviations_reconciled=True,
    )

    assert manifest["status"] == LAD.BLOCKED_STATUS
    assert "missing_confirmation:clean_copy_not_raw" in manifest["blockers"]
    assert manifest["locked_dataset_path"] is None
    assert not (tmp_path / "exports" / "LOCK-MISSING" / "05_clean_locked").exists()


def test_lock_blocks_open_query_log(tmp_path):
    clean = _clean_dataset(tmp_path / "df_clean.csv")
    qlog = _open_query_log(tmp_path / "query_log.csv")

    manifest = LAD.lock_dataset(
        "LOCK-OPENQ",
        clean,
        exports_root=tmp_path / "exports",
        **_lock_kwargs(qlog),
    )

    assert manifest["status"] == LAD.BLOCKED_STATUS
    assert "open_query_log" in manifest["blockers"]
    assert manifest["query_log"]["open_queries"]


def test_lock_blocks_pii_value_without_storing_value(tmp_path):
    clean = _csv(
        tmp_path / "df_clean.csv",
        """
record_id,age,notes
S001,45,phone 0912345678
""",
    )
    qlog = _closed_query_log(tmp_path / "query_log.csv")

    manifest = LAD.lock_dataset(
        "LOCK-PII",
        clean,
        exports_root=tmp_path / "exports",
        **_lock_kwargs(qlog),
    )

    assert manifest["status"] == LAD.BLOCKED_STATUS
    assert "pii_detected_in_clean_data" in manifest["blockers"]
    dumped = json.dumps(manifest, ensure_ascii=False)
    assert "0912345678" not in dumped


def test_g10_mentions_locked_analysis_dataset(tmp_path):
    study_dir = tmp_path / "STUDY"
    study_dir.mkdir()
    _write_cross_sectional_fixture(study_dir)
    meta = {
        "data_lock_date": "2026-07-13",
        "real_data_lock": {
            "status": LAD.LOCKED_STATUS,
            "locked_dataset_path": "05_clean_locked/df_clean.abc123.locked.csv",
            "lock_date": "2026-07-13",
            "approved_by": "PI Nguyen",
            "sap_version": "1.0",
            "sha256": "abc123",
            "memo": "DATA_LOCK_memo.md",
        },
    }
    (study_dir / "study_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False), encoding="utf-8")

    res = G10.assemble("STUDY", study_dir)
    text = res["md"].read_text(encoding="utf-8")

    assert "Dữ liệu phân tích đã khóa" in text
    assert "05_clean_locked/df_clean.abc123.locked.csv" in text
    assert "DATA_LOCK_memo.md" in text


def test_sap_version_mismatch_no_longer_blocks_truthful_amendment(tmp_path):
    """Hồi quy audit tautology vòng 2 (2026-07-31): tools/run_g4_auto.py chỉ
    từng ghi g4_sap_version=None hoặc hardcode "1.0" — không CLI flag nào
    từng gán giá trị khác. Trước bản vá, bác sĩ khai TRUNG THỰC một SAP đã
    tu chỉnh (vd "2.0", đúng thực tế) bị chặn vì g4_sap_version trong
    checkpoint vẫn là "1.0" (giá trị duy nhất run_g4_auto.py có thể ghi) —
    reverse-tautology: phạt khai đúng, thưởng khai khớp hằng số vô nghĩa."""
    clean = _clean_dataset(tmp_path / "df_clean.csv")
    qlog = _closed_query_log(tmp_path / "query_log.csv")
    study = "LOCK-SAP-AMEND"
    out_dir = tmp_path / "exports" / study
    out_dir.mkdir(parents=True)
    (out_dir / "G4_checkpoint.json").write_text(
        json.dumps({"g4_sap_version": "1.0"}, ensure_ascii=False), encoding="utf-8"
    )

    kwargs = _lock_kwargs(qlog)
    kwargs["sap_version"] = "2.0"  # khai TRUNG THỰC một SAP đã tu chỉnh
    manifest = LAD.lock_dataset(
        study,
        clean,
        exports_root=tmp_path / "exports",
        **kwargs,
    )

    assert "sap_version_mismatch_with_G4" not in manifest["blockers"], manifest["blockers"]
    assert manifest["g4_sap_version_at_signing"] == "1.0"
    assert manifest["sap_version"] == "2.0"


def test_sap_version_dishonest_match_recorded_but_not_specially_flagged(tmp_path):
    """Đối chứng: khai "1.0" trùng hằng số (dù SAP thật có thể đã khác) cũng
    KHÔNG bị chặn — xác nhận field này chỉ còn tính ghi-nhận-audit, không
    còn là một lớp bảo vệ (bảo vệ thật nằm ở chữ ký mật mã upstream["G4"])."""
    clean = _clean_dataset(tmp_path / "df_clean.csv")
    qlog = _closed_query_log(tmp_path / "query_log.csv")
    study = "LOCK-SAP-MATCH"
    out_dir = tmp_path / "exports" / study
    out_dir.mkdir(parents=True)
    (out_dir / "G4_checkpoint.json").write_text(
        json.dumps({"g4_sap_version": "1.0"}, ensure_ascii=False), encoding="utf-8"
    )

    manifest = LAD.lock_dataset(
        study,
        clean,
        exports_root=tmp_path / "exports",
        **_lock_kwargs(qlog),  # sap_version="1.0" mặc định
    )

    assert "sap_version_mismatch_with_G4" not in manifest["blockers"]
    assert manifest["g4_sap_version_at_signing"] == "1.0"
