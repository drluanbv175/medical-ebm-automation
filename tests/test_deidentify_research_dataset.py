from __future__ import annotations

import json
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import deidentify_research_dataset as DEID  # noqa: E402
import import_real_dataset as RDI  # noqa: E402
import run_g10_assemble as G10  # noqa: E402

from tests.test_g10_assemble import _write_cross_sectional_fixture  # noqa: E402


def _csv(path: Path, text: str) -> Path:
    path.write_text(text.strip() + "\n", encoding="utf-8")
    return path


def test_deidentify_drops_pii_columns_and_redacts_free_text(tmp_path):
    raw = _csv(
        tmp_path / "raw.csv",
        """
record_id,Họ tên,phone,email,age,notes,primary_outcome
001,Nguyen Van A,0912345678,a@example.com,45,call 0912345678 or a@example.com,0
002,Nguyen Van B,0987654321,b@example.com,52,clean note,1
""",
    )

    report = DEID.deidentify_dataset("DEID-OK", raw, exports_root=tmp_path / "exports")

    assert report["status"] == DEID.DEIDENTIFIED_STATUS
    assert report["row_count"] == 2
    assert report["dropped_column_count"] == 3
    assert report["redacted_cell_count"] == 1
    out_dir = tmp_path / "exports" / "DEID-OK"
    deid_path = out_dir / report["deidentified_path"]
    text = deid_path.read_text(encoding="utf-8")
    assert "study_subject_id" in text
    assert "S000001" in text
    assert "Họ tên" not in text
    assert "phone" not in text
    assert "a@example.com" not in text
    assert "0912345678" not in text
    assert "Nguyen Van A" not in text
    assert DEID.REDACTION_TOKEN in text

    intake = RDI.import_dataset("DEID-OK", deid_path, exports_root=tmp_path / "exports")
    assert intake["status"] == RDI.READY_STATUS


def test_redact_value_fully_scrubs_formatted_phone_and_grouped_cccd_in_one_cell():
    """Hồi quy (vòng audit đối kháng 3, 2026-07-16): VALUE_PATTERNS trước đây bỏ sót SĐT có
    ngoặc đơn ("(090) 123 4567") và CCCD viết nhóm 3 số ("012 345 678 901"). Bản vá đầu tiên
    (chỉ nới lỏng phone_vn) lại gây lỗi MỚI: phone_vn (khớp lỏng hơn) chạy trước, ẩn một phần
    số CCCD, làm vỡ cấu trúc 3-3-3(-3) liền mạch mà cccd_cmnd_grouped cần để khớp phần CÒN
    LẠI — hậu quả là đuôi CCCD ("901") vẫn lộ ra trong CSV đã khử định danh. Fix đúng: đặt
    cccd_cmnd_grouped (khớp CHẶT hơn, độ dài cố định) TRƯỚC phone_vn trong VALUE_PATTERNS."""
    text = "Lien he SDT (090) 123 4567, CCCD 012 345 678 901"
    redacted, counts = DEID._redact_value(text)
    assert "090" not in redacted
    assert "4567" not in redacted
    assert "012" not in redacted
    assert "901" not in redacted
    assert counts.get("phone_vn") == 1
    assert counts.get("cccd_cmnd_grouped") == 1

    # Đối chứng: số lâm sàng KHÔNG bị ẩn nhầm.
    clinical = "Huyết áp 140/90, nhịp tim 88, đường huyết 7.2"
    redacted_clinical, counts_clinical = DEID._redact_value(clinical)
    assert redacted_clinical == clinical
    assert counts_clinical == {}


def test_deidentify_report_does_not_store_raw_pii_values(tmp_path):
    raw = _csv(
        tmp_path / "patient_0912345678.csv",
        """
record_id,ho_ten,age,notes
001,Nguyen Van A,45,email a@example.com phone 0912345678
""",
    )

    report = DEID.deidentify_dataset("DEID-NO-LEAK", raw, exports_root=tmp_path / "exports")
    out_dir = tmp_path / "exports" / "DEID-NO-LEAK"
    report_json = (out_dir / DEID.REPORT_NAME).read_text(encoding="utf-8")

    assert report["status"] == DEID.DEIDENTIFIED_STATUS
    assert "Nguyen Van A" not in report_json
    assert "0912345678" not in report_json
    assert "a@example.com" not in report_json
    assert "patient_0912345678.csv" not in report_json
    assert "[NOT_STORED_TO_AVOID_PII_IN_FILENAMES]" in report_json


def test_deidentify_then_import_creates_intake_manifest(tmp_path):
    raw = _csv(
        tmp_path / "raw.csv",
        """
record_id,ten_benh_nhan,cccd,age,notes
001,Nguyen Van A,012345678901,45,phone 0912345678
""",
    )

    report = DEID.deidentify_dataset(
        "DEID-IMPORT",
        raw,
        exports_root=tmp_path / "exports",
        then_import=True,
    )

    out_dir = tmp_path / "exports" / "DEID-IMPORT"
    assert report["status"] == DEID.DEIDENTIFIED_STATUS
    assert report["then_import"]["status"] == RDI.READY_STATUS
    assert (out_dir / "DATA_INTAKE_manifest.json").exists()
    assert (out_dir / report["then_import"]["raw_readonly_path"]).exists()

    meta = json.loads((out_dir / "study_meta.json").read_text(encoding="utf-8"))
    assert meta["real_data_deidentification"]["status"] == DEID.DEIDENTIFIED_STATUS
    assert meta["real_data_intake"]["status"] == RDI.READY_STATUS


def test_deidentify_blocks_overwriting_source(tmp_path):
    raw = _csv(
        tmp_path / "raw.csv",
        """
record_id,age
001,45
""",
    )

    report = DEID.deidentify_dataset(
        "DEID-BLOCK",
        raw,
        output_path=raw,
        exports_root=tmp_path / "exports",
    )

    assert report["status"] == DEID.BLOCKED_STATUS
    assert report["blocker"] == "output_path_must_not_overwrite_source"


def test_g10_mentions_deidentification_report(tmp_path):
    study_dir = tmp_path / "STUDY"
    study_dir.mkdir()
    _write_cross_sectional_fixture(study_dir)
    meta = {
        "real_data_deidentification": {
            "status": DEID.DEIDENTIFIED_STATUS,
            "report": "DEIDENTIFICATION_report.json",
            "deidentified_path": "00_deidentified/deidentified.abc123.csv",
            "dropped_column_count": 3,
            "redacted_cell_count": 2,
        }
    }
    (study_dir / "study_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False), encoding="utf-8")

    res = G10.assemble("STUDY", study_dir)
    text = res["md"].read_text(encoding="utf-8")

    assert "Khử định danh tự động" in text
    assert "DEIDENTIFICATION_report.json" in text
    assert "00_deidentified/deidentified.abc123.csv" in text
    assert "Report không lưu giá trị PII" in text
