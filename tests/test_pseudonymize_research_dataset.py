from __future__ import annotations

import json
import stat
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import import_real_dataset as RDI  # noqa: E402
import pseudonymize_research_dataset as PSN  # noqa: E402
import run_g10_assemble as G10  # noqa: E402

from tests.test_g10_assemble import _write_cross_sectional_fixture  # noqa: E402


def _csv(path: Path, text: str) -> Path:
    path.write_text(text.strip() + "\n", encoding="utf-8")
    return path


def _mode_is_private(path: Path) -> bool:
    return stat.S_IMODE(path.stat().st_mode) & 0o077 == 0


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
