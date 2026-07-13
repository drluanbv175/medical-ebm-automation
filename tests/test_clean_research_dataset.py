from __future__ import annotations

import json
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import clean_research_dataset as CLEAN  # noqa: E402
import lock_analysis_dataset as LAD  # noqa: E402
import run_g10_assemble as G10  # noqa: E402

from tests.test_g10_assemble import _write_cross_sectional_fixture  # noqa: E402


def _csv(path: Path, text: str) -> Path:
    path.write_text(text.strip() + "\n", encoding="utf-8")
    return path


def _dict_json(path: Path) -> Path:
    payload = {
        "id_column": "record_id",
        "missing_tokens": ["999", "không rõ"],
        "variables": [
            {"name": "record_id", "type": "text", "required": True},
            {"name": "age", "type": "integer", "required": True, "min": 18, "max": 100},
            {"name": "sex", "type": "category", "required": True, "allowed": ["F", "M"]},
            {"name": "primary_outcome", "type": "integer", "required": True, "min": 0, "max": 1},
        ],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def _lock_kwargs(query_log: Path) -> dict:
    return {
        "lock_date": "2026-07-13",
        "approved_by": "PI Nguyen",
        "sap_version": "1.0",
        "query_log": query_log,
        "confirm_deidentified": True,
        "confirm_clean_copy": True,
        "confirm_no_open_query": True,
        "confirm_sap_locked": True,
    }


def test_clean_dataset_creates_clean_copy_closed_query_and_can_lock(tmp_path):
    data = _csv(
        tmp_path / "input.csv",
        """
record_id,age,sex,primary_outcome,notes
S001, 45 ,F,0,  stable visit
S002,52,M,1,không rõ
""",
    )
    dictionary = _dict_json(tmp_path / "dictionary.json")

    report = CLEAN.clean_dataset(
        "CLEAN-OK",
        data,
        dictionary_path=dictionary,
        exports_root=tmp_path / "exports",
    )

    assert report["status"] == CLEAN.CLEAN_READY_STATUS
    assert report["ready_for_lock"] is True
    assert report["open_query_count"] == 0
    out_dir = tmp_path / "exports" / "CLEAN-OK"
    clean_path = out_dir / report["clean_dataset_path"]
    query_log = out_dir / report["query_log"]
    assert clean_path.exists()
    assert query_log.exists()
    text = clean_path.read_text(encoding="utf-8")
    assert " 45 " not in text
    assert "stable visit" in text
    assert "không rõ" not in text

    locked = LAD.lock_dataset(
        "CLEAN-OK",
        clean_path,
        exports_root=tmp_path / "exports",
        **_lock_kwargs(query_log),
    )
    assert locked["status"] == LAD.LOCKED_STATUS


def test_clean_dataset_flags_queries_without_fixing_values_and_lock_blocks(tmp_path):
    data = _csv(
        tmp_path / "input.csv",
        """
record_id,age,sex,primary_outcome
S001,45,F,0
S001,145,X,
""",
    )
    dictionary = _dict_json(tmp_path / "dictionary.json")

    report = CLEAN.clean_dataset(
        "CLEAN-QUERY",
        data,
        dictionary_path=dictionary,
        exports_root=tmp_path / "exports",
    )

    assert report["status"] == CLEAN.CLEAN_QUERY_STATUS
    assert report["ready_for_lock"] is False
    assert report["open_query_count"] >= 3
    assert report["query_summary"]["duplicate_id"] == 1
    assert report["query_summary"]["range_high"] == 1
    assert report["query_summary"]["invalid_category"] == 1
    out_dir = tmp_path / "exports" / "CLEAN-QUERY"
    clean_path = out_dir / report["clean_dataset_path"]
    query_log = out_dir / report["query_log"]
    assert "145" in clean_path.read_text(encoding="utf-8")

    locked = LAD.lock_dataset(
        "CLEAN-QUERY",
        clean_path,
        exports_root=tmp_path / "exports",
        **_lock_kwargs(query_log),
    )
    assert locked["status"] == LAD.BLOCKED_STATUS
    assert "open_query_log" in locked["blockers"]


def test_clean_blocks_pii_without_storing_raw_value_or_clean_copy(tmp_path):
    data = _csv(
        tmp_path / "unsafe.csv",
        """
record_id,age,notes
S001,45,call 0912345678 before visit
""",
    )

    report = CLEAN.clean_dataset(
        "CLEAN-PII",
        data,
        exports_root=tmp_path / "exports",
    )

    out_dir = tmp_path / "exports" / "CLEAN-PII"
    report_json = (out_dir / CLEAN.REPORT_NAME).read_text(encoding="utf-8")
    assert report["status"] == CLEAN.BLOCKED_STATUS
    assert report["blocker"] == "pii_detected_before_cleaning"
    assert report["clean_dataset_path"] is None
    assert "0912345678" not in report_json
    assert not (out_dir / "03_clean_working").exists()


def test_g10_mentions_cleaning_report_and_open_query_count(tmp_path):
    study_dir = tmp_path / "STUDY"
    study_dir.mkdir()
    _write_cross_sectional_fixture(study_dir)
    meta = {
        "real_data_cleaning": {
            "status": CLEAN.CLEAN_QUERY_STATUS,
            "report": "DATA_CLEANING_report.json",
            "clean_dataset_path": "03_clean_working/df_clean.abc123.csv",
            "query_log": "04_query_logs/data_cleaning_query_log.csv",
            "open_query_count": 2,
            "ready_for_lock": False,
        }
    }
    (study_dir / "study_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False), encoding="utf-8")

    res = G10.assemble("STUDY", study_dir)
    text = res["md"].read_text(encoding="utf-8")

    assert "Làm sạch dữ liệu trên bản sao" in text
    assert "DATA_CLEANING_report.json" in text
    assert "03_clean_working/df_clean.abc123.csv" in text
    assert "query mở=2" in text
