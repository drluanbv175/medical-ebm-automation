from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import pytest

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import import_real_dataset as RDI  # noqa: E402
import pseudonymize_research_dataset as PSN  # noqa: E402
import run_g10_assemble as G10  # noqa: E402
from secure_permissions import is_owner_exclusive  # noqa: E402

from tests.test_g10_assemble import _write_cross_sectional_fixture  # noqa: E402


def _csv(path: Path, text: str) -> Path:
    path.write_text(text.strip() + "\n", encoding="utf-8")
    return path


def _mode_is_private(path: Path) -> bool:
    """Alias mỏng cho is_owner_exclusive — POSIX+Windows đều dùng chung 1 hàm thật."""
    return is_owner_exclusive(path)


def test_pseudonymize_creates_clean_dataset_and_protected_mapping(tmp_path):
    raw = _csv(
        tmp_path / "raw.csv",
        """
record_id,Họ tên,phone,email,age,notes,primary_outcome
001,Nguyen Van A,0912345678,a@example.com,45,call 0987654321 before visit,0
002,Nguyen Van B,0987654321,b@example.com,52,clean note,1
""",
    )
    mapping_root = tmp_path / "protected_mapping"

    report = PSN.pseudonymize_dataset(
        "PSN-OK",
        raw,
        exports_root=tmp_path / "exports",
        mapping_root=mapping_root,
        then_import=True,
    )

    assert report["status"] == PSN.PSEUDONYMIZED_STATUS
    assert report["then_import"]["status"] == RDI.READY_STATUS

    out_dir = tmp_path / "exports" / "PSN-OK"
    pseudonymized = out_dir / report["pseudonymized_path"]
    output_text = pseudonymized.read_text(encoding="utf-8")
    assert "study_subject_id" in output_text
    assert "PSN-000001" in output_text
    assert "Nguyen Van A" not in output_text
    assert "0912345678" not in output_text
    assert "a@example.com" not in output_text
    assert PSN.REDACTION_TOKEN in output_text

    mapping_dir = mapping_root / "PSN-OK" / RDI._sha256_file(raw)[:12]
    linkage_map = mapping_dir / PSN.LINKAGE_MAP_NAME
    redaction_map = mapping_dir / PSN.REDACTION_MAP_NAME
    manifest = mapping_dir / PSN.MAPPING_MANIFEST_NAME
    assert _mode_is_private(mapping_dir)
    assert _mode_is_private(linkage_map)
    assert _mode_is_private(redaction_map)
    assert _mode_is_private(manifest)
    linkage_text = linkage_map.read_text(encoding="utf-8")
    redaction_text = redaction_map.read_text(encoding="utf-8")
    assert "Nguyen Van A" in linkage_text
    assert "0912345678" in linkage_text
    assert "a@example.com" in linkage_text
    assert "0987654321" in redaction_text


def test_pseudonymization_public_report_does_not_leak_pii_or_mapping_path(tmp_path):
    raw = _csv(
        tmp_path / "patient_0912345678.csv",
        """
record_id,ho_ten,cccd,age,notes
001,Nguyen Van A,012345678901,45,email a@example.com phone 0912345678
""",
    )
    mapping_root = tmp_path / "protected_mapping"

    report = PSN.pseudonymize_dataset(
        "PSN-NO-LEAK",
        raw,
        exports_root=tmp_path / "exports",
        mapping_root=mapping_root,
    )

    out_dir = tmp_path / "exports" / "PSN-NO-LEAK"
    report_json = (out_dir / PSN.REPORT_NAME).read_text(encoding="utf-8")
    assert report["status"] == PSN.PSEUDONYMIZED_STATUS
    assert "Nguyen Van A" not in report_json
    assert "0912345678" not in report_json
    assert "012345678901" not in report_json
    assert "a@example.com" not in report_json
    assert "patient_0912345678.csv" not in report_json
    assert str(mapping_root) not in report_json
    assert "[PROTECTED_EXTERNAL_ROOT]" in report_json


def test_pseudonymization_blocks_mapping_root_inside_exports(tmp_path):
    raw = _csv(
        tmp_path / "raw.csv",
        """
record_id,ho_ten,age
001,Nguyen Van A,45
""",
    )
    exports_root = tmp_path / "exports"

    report = PSN.pseudonymize_dataset(
        "PSN-BLOCK",
        raw,
        exports_root=exports_root,
        mapping_root=exports_root / "PSN-BLOCK" / "mapping",
    )

    assert report["status"] == PSN.BLOCKED_STATUS
    assert report["blocker"] == "mapping_root_inside_exports"
    assert not (exports_root / "PSN-BLOCK" / "mapping").exists()


def test_retention_set_when_months_and_owner_both_given(tmp_path):
    raw = _csv(tmp_path / "raw.csv", "record_id,ho_ten,age\n001,Nguyen Van A,45\n")
    mapping_root = tmp_path / "protected_mapping"

    report = PSN.pseudonymize_dataset(
        "PSN-RETENTION-SET",
        raw,
        exports_root=tmp_path / "exports",
        mapping_root=mapping_root,
        retention_months=24,
        retention_owner="PI - BS. Nguyen Van Test",
    )

    assert report["status"] == PSN.PSEUDONYMIZED_STATUS
    assert report["retention_status"] == PSN.RETENTION_STATUS_SET
    assert report["retention_months"] == 24
    assert report["retention_until"] is not None

    created_dt = datetime.fromisoformat(report["created_at"])
    expected_until = PSN._add_months(created_dt, 24).isoformat(timespec="seconds")
    assert report["retention_until"] == expected_until

    mapping_dir = mapping_root / "PSN-RETENTION-SET" / RDI._sha256_file(raw)[:12]
    manifest = json.loads((mapping_dir / PSN.MAPPING_MANIFEST_NAME).read_text(encoding="utf-8"))
    policy = manifest["retention_policy"]
    assert policy["retention_status"] == PSN.RETENTION_STATUS_SET
    assert policy["retention_months"] == 24
    assert policy["retention_owner"] == "PI - BS. Nguyen Van Test"
    assert policy["retention_until"] == expected_until


def test_retention_unset_flagged_when_not_provided(tmp_path):
    raw = _csv(tmp_path / "raw.csv", "record_id,ho_ten,age\n001,Nguyen Van A,45\n")
    mapping_root = tmp_path / "protected_mapping"

    report = PSN.pseudonymize_dataset(
        "PSN-RETENTION-UNSET",
        raw,
        exports_root=tmp_path / "exports",
        mapping_root=mapping_root,
    )

    assert report["status"] == PSN.PSEUDONYMIZED_STATUS
    assert report["retention_status"] == PSN.RETENTION_UNSET_MARKER
    assert report["retention_months"] is None
    assert report["retention_until"] is None

    mapping_dir = mapping_root / "PSN-RETENTION-UNSET" / RDI._sha256_file(raw)[:12]
    manifest = json.loads((mapping_dir / PSN.MAPPING_MANIFEST_NAME).read_text(encoding="utf-8"))
    assert manifest["retention_policy"]["retention_status"] == PSN.RETENTION_UNSET_MARKER
    assert manifest["retention_policy"]["retention_owner"] is None


def test_retention_partial_input_treated_as_unset_with_issue_note(tmp_path):
    raw = _csv(tmp_path / "raw.csv", "record_id,ho_ten,age\n001,Nguyen Van A,45\n")
    mapping_root = tmp_path / "protected_mapping"

    report = PSN.pseudonymize_dataset(
        "PSN-RETENTION-PARTIAL",
        raw,
        exports_root=tmp_path / "exports",
        mapping_root=mapping_root,
        retention_months=12,
        retention_owner=None,
    )

    assert report["retention_status"] == PSN.RETENTION_UNSET_MARKER
    mapping_dir = mapping_root / "PSN-RETENTION-PARTIAL" / RDI._sha256_file(raw)[:12]
    manifest = json.loads((mapping_dir / PSN.MAPPING_MANIFEST_NAME).read_text(encoding="utf-8"))
    assert manifest["retention_policy"]["input_issue"] is not None


def test_retention_owner_never_leaks_into_public_report_or_meta(tmp_path):
    raw = _csv(tmp_path / "raw.csv", "record_id,ho_ten,age\n001,Nguyen Van A,45\n")
    mapping_root = tmp_path / "protected_mapping"
    secret_owner = "PI - BS. Tran Thi Vi Du Bi Mat"

    report = PSN.pseudonymize_dataset(
        "PSN-RETENTION-NOLEAK",
        raw,
        exports_root=tmp_path / "exports",
        mapping_root=mapping_root,
        retention_months=6,
        retention_owner=secret_owner,
    )

    out_dir = tmp_path / "exports" / "PSN-RETENTION-NOLEAK"
    report_json = (out_dir / PSN.REPORT_NAME).read_text(encoding="utf-8")
    meta_json = (out_dir / "study_meta.json").read_text(encoding="utf-8")
    assert secret_owner not in report_json
    assert secret_owner not in meta_json
    assert report["retention_status"] == PSN.RETENTION_STATUS_SET

    mapping_dir = mapping_root / "PSN-RETENTION-NOLEAK" / RDI._sha256_file(raw)[:12]
    manifest_json = (mapping_dir / PSN.MAPPING_MANIFEST_NAME).read_text(encoding="utf-8")
    assert secret_owner in manifest_json


def test_add_months_handles_year_rollover_and_day_clamping():
    assert PSN._add_months(datetime(2026, 1, 31), 1) == datetime(2026, 2, 28)
    assert PSN._add_months(datetime(2026, 12, 15), 2) == datetime(2027, 2, 15)
    assert PSN._add_months(datetime(2026, 5, 10), 0) == datetime(2026, 5, 10)


def test_cli_rejects_non_positive_retention_months(tmp_path, capsys):
    raw = _csv(tmp_path / "raw.csv", "record_id,ho_ten,age\n001,Nguyen Van A,45\n")
    argv = [
        "pseudonymize_research_dataset.py",
        "--study", "PSN-CLI-BADMONTHS",
        "--data", str(raw),
        "--retention-months", "0",
        "--retention-owner", "PI",
    ]
    old_argv = sys.argv
    sys.argv = argv
    try:
        with pytest.raises(SystemExit) as exc:
            PSN.main()
        assert exc.value.code == 2
    finally:
        sys.argv = old_argv
    assert "--retention-months" in capsys.readouterr().err


def test_g10_mentions_pseudonymization_mapping_policy(tmp_path):
    study_dir = tmp_path / "STUDY"
    study_dir.mkdir()
    _write_cross_sectional_fixture(study_dir)
    meta = {
        "real_data_pseudonymization": {
            "status": PSN.PSEUDONYMIZED_STATUS,
            "report": "PSEUDONYMIZATION_report.json",
            "pseudonymized_path": "00_pseudonymized/pseudonymized.abc123.csv",
            "mapping_location": "[PROTECTED_EXTERNAL_ROOT]",
        }
    }
    (study_dir / "study_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False), encoding="utf-8")

    res = G10.assemble("STUDY", study_dir)
    text = res["md"].read_text(encoding="utf-8")

    assert "Mã hóa thay thế / pseudonymization" in text
    assert "PSEUDONYMIZATION_report.json" in text
    assert "00_pseudonymized/pseudonymized.abc123.csv" in text
    assert "không đưa vào exports/repo/OneDrive" in text
