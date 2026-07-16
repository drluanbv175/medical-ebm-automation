from __future__ import annotations

import json
import stat
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import import_real_dataset as RDI  # noqa: E402
import run_g10_assemble as G10  # noqa: E402

from tests.test_g10_assemble import _write_cross_sectional_fixture  # noqa: E402


def _csv(path: Path, text: str) -> Path:
    path.write_text(text.strip() + "\n", encoding="utf-8")
    return path


def test_import_deidentified_csv_copies_raw_readonly_and_updates_meta(tmp_path):
    data = _csv(
        tmp_path / "clean.csv",
        """
record_id,age,sex,exposure_var,primary_outcome
S001,45,F,1,0
S002,52,M,0,1
""",
    )
    manifest = RDI.import_dataset("REAL-DATA", data, exports_root=tmp_path / "exports")

    assert manifest["status"] == RDI.READY_STATUS
    assert manifest["pii_scan"]["passed"] is True
    assert manifest["row_count"] == 2
    assert manifest["column_count"] == 5
    out_dir = tmp_path / "exports" / "REAL-DATA"
    raw_path = out_dir / manifest["raw_readonly_path"]
    assert raw_path.exists()
    assert raw_path.stat().st_mode & stat.S_IWUSR == 0
    assert manifest["sha256"] == RDI._sha256_file(data)
    assert (out_dir / "04_query_logs" / "data_intake_query_log.csv").exists()

    meta = json.loads((out_dir / "study_meta.json").read_text(encoding="utf-8"))
    assert meta["real_data_intake"]["status"] == RDI.READY_STATUS
    assert meta["real_data_intake"]["db_locked"] is False
    assert meta["data_lock_date"] is None


def test_import_blocks_direct_pii_header_without_copying_raw(tmp_path):
    data = _csv(
        tmp_path / "unsafe.csv",
        """
record_id,ho_ten,age,primary_outcome
S001,Nguyen Van A,45,0
""",
    )
    manifest = RDI.import_dataset("PII-HDR", data, exports_root=tmp_path / "exports")

    assert manifest["status"] == RDI.BLOCKED_STATUS
    assert manifest["pii_scan"]["passed"] is False
    assert any(issue["type"].startswith("header_pii") for issue in manifest["pii_scan"]["issues"])
    out_dir = tmp_path / "exports" / "PII-HDR"
    assert manifest["raw_readonly_path"] is None
    assert not (out_dir / "02_raw_readonly").exists()
    assert (out_dir / "DATA_INTAKE_manifest.json").exists()


def test_import_blocks_accented_vietnamese_pii_header(tmp_path):
    data = _csv(
        tmp_path / "unsafe_accented.csv",
        """
record_id,Họ tên,Số điện thoại,age,primary_outcome
S001,Nguyen Van A,0912345678,45,0
""",
    )
    manifest = RDI.import_dataset("PII-ACCENT", data, exports_root=tmp_path / "exports")

    assert manifest["status"] == RDI.BLOCKED_STATUS
    issue_types = {issue["type"] for issue in manifest["pii_scan"]["issues"]}
    assert "header_pii:ho_ten" in issue_types
    assert "header_pii:so_dien_thoai" in issue_types
    assert manifest["raw_readonly_path"] is None


def test_import_blocks_tokenized_pii_headers_without_overblocking(tmp_path):
    data = _csv(
        tmp_path / "unsafe_tokenized_headers.csv",
        """
record_id,patient_phone,cccd_so,tuyen_giap,primary_outcome
S001,redacted,redacted,0,1
""",
    )
    manifest = RDI.import_dataset("PII-TOKEN-HDR", data, exports_root=tmp_path / "exports")

    assert manifest["status"] == RDI.BLOCKED_STATUS
    issue_types = {issue["type"] for issue in manifest["pii_scan"]["issues"]}
    assert "header_pii:patient_phone" in issue_types
    assert "header_pii:cccd_so" in issue_types
    assert "header_pii:tuyen_giap" not in issue_types
    assert manifest["raw_readonly_path"] is None


def test_import_blocks_direct_pii_value_without_storing_value(tmp_path):
    data = _csv(
        tmp_path / "unsafe_value.csv",
        """
record_id,age,notes
S001,45,call 0912345678 before visit
""",
    )
    manifest = RDI.import_dataset("PII-VAL", data, exports_root=tmp_path / "exports")

    assert manifest["status"] == RDI.BLOCKED_STATUS
    issues = manifest["pii_scan"]["issues"]
    assert any(issue["type"] == "value_pii:phone_vn" for issue in issues)
    assert "pseudonymize_research_dataset.py" in manifest["remediation"]["pseudonymize_command"]
    dumped = json.dumps(manifest, ensure_ascii=False)
    assert "0912345678" not in dumped


def test_import_blocks_formatted_phone_and_grouped_citizen_id_values(tmp_path):
    data = _csv(
        tmp_path / "unsafe_formatted_values.csv",
        """
record_id,age,notes
S001,45,"call (090) 123 4567; CCCD 012 345 678 901"
""",
    )
    manifest = RDI.import_dataset("PII-FMT-VAL", data, exports_root=tmp_path / "exports")

    issues = manifest["pii_scan"]["issues"]
    assert manifest["status"] == RDI.BLOCKED_STATUS
    assert any(issue["type"] == "value_pii:phone_vn" for issue in issues)
    assert any(issue["type"] == "value_pii:cccd_cmnd_grouped" for issue in issues)
    dumped = json.dumps(manifest, ensure_ascii=False)
    assert "(090) 123 4567" not in dumped
    assert "012 345 678 901" not in dumped


def test_blocked_intake_redacts_source_filename_with_pii_signal(tmp_path):
    data = _csv(
        tmp_path / "patient_0912345678.csv",
        """
record_id,age,notes
S001,45,call 0912345678 before visit
""",
    )
    manifest = RDI.import_dataset("PII-FILENAME", data, exports_root=tmp_path / "exports")

    dumped = json.dumps(manifest, ensure_ascii=False)
    assert manifest["status"] == RDI.BLOCKED_STATUS
    assert manifest["source_filename"] == "[REDACTED_SOURCE_FILENAME].csv"
    assert manifest["source_filename_redacted"] is True
    assert "patient_0912345678.csv" not in dumped
    assert "0912345678" not in dumped


def test_g10_mentions_real_data_intake_manifest(tmp_path):
    study_dir = tmp_path / "STUDY"
    study_dir.mkdir()
    _write_cross_sectional_fixture(study_dir)
    meta = {
        "real_data_intake": {
            "status": RDI.READY_STATUS,
            "manifest": "DATA_INTAKE_manifest.json",
            "raw_readonly_path": "02_raw_readonly/clean.abc123.csv",
            "rows": 2,
            "columns": 5,
            "sha256": "abc123",
            "db_locked": False,
        }
    }
    (study_dir / "study_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False), encoding="utf-8")

    res = G10.assemble("STUDY", study_dir)
    text = res["md"].read_text(encoding="utf-8")

    assert "Dữ liệu thật đã nhập" in text
    assert "DATA_INTAKE_manifest.json" in text
    assert "02_raw_readonly/clean.abc123.csv" in text
    assert "chưa đồng nghĩa khóa DB" in text
