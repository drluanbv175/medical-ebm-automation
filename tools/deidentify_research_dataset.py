#!/usr/bin/env python3
"""Khử định danh CSV nghiên cứu trước khi nạp dữ liệu thật.

Công cụ này xử lý tình huống intake bị chặn vì PII:
- Không sửa file nguồn.
- Không copy file nguồn còn PII vào exports/raw.
- Loại cột định danh trực tiếp theo header.
- Thay thế email/số điện thoại/CMND-CCCD còn lẫn trong ô tự do bằng token.
- Tạo `study_subject_id` mới và báo cáo không lưu giá trị PII.
- Tùy chọn `--then-import` để nạp ngay bản đã khử định danh qua intake an toàn.

Ví dụ:
  python3 tools/deidentify_research_dataset.py --study KKB-HAI-LONG-2026 \\
    --data raw_export.csv --then-import
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

BASE = Path(__file__).resolve().parents[1]
TOOLS = BASE / "tools"
sys.path.insert(0, str(TOOLS))

import gate_contract as GC  # noqa: E402
import import_real_dataset as RDI  # noqa: E402

DEIDENTIFIED_STATUS = "DEIDENTIFIED_READY_FOR_INTAKE"
BLOCKED_STATUS = "BLOCKED_DEIDENTIFICATION"
REDACTION_TOKEN = "[REDACTED_PII]"
REPORT_NAME = "DEIDENTIFICATION_report.json"


def _safe_rel(path: Optional[Path], base: Path) -> Optional[str]:
    if path is None:
        return None
    try:
        return str(path.relative_to(base))
    except ValueError:
        return str(path.name)


def _default_output_path(study_id: str, data_path: Path, exports_root: Path) -> Path:
    """Tạo tên output không dùng stem file nguồn, tránh rò PII qua filename."""
    raw_hash = RDI._sha256_file(data_path) if data_path.exists() else "missing"
    return exports_root / study_id / "00_deidentified" / f"deidentified.{raw_hash[:12]}.csv"


def _redact_value(value: Any) -> Tuple[str, Dict[str, int]]:
    text = "" if value is None else str(value)
    counts: Dict[str, int] = {}
    redacted = text
    for label, pattern in RDI.VALUE_PATTERNS.items():
        matches = pattern.findall(redacted)
        if not matches:
            continue
        counts[label] = len(matches)
        redacted = pattern.sub(REDACTION_TOKEN, redacted)
    return redacted, counts


def _drop_reason(column: str) -> Optional[str]:
    reason = RDI._header_issue(column)
    if reason:
        return reason
    return None


def _readable_blocker(data_path: Path, output_path: Path) -> Optional[str]:
    if data_path.suffix.lower() not in RDI.SUPPORTED_SUFFIXES:
        return "unsupported_format: chỉ hỗ trợ CSV"
    if not data_path.exists():
        return "missing_file"
    try:
        if data_path.resolve() == output_path.resolve():
            return "output_path_must_not_overwrite_source"
    except OSError:
        return None
    return None


def _process_with_encoding(data_path: Path, output_path: Path,
                           encoding: str) -> Dict[str, Any]:
    row_count = 0
    redacted_cells_by_column: Dict[str, int] = {}
    redacted_patterns_by_column: Dict[str, Dict[str, int]] = {}

    with data_path.open("r", encoding=encoding, newline="") as src:
        sample = src.read(4096)
        src.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample)
        except csv.Error:
            dialect = csv.excel

        reader = csv.DictReader(src, dialect=dialect)
        columns = list(reader.fieldnames or [])
        if not columns:
            return {
                "blocker": "empty_header",
                "rows": 0,
                "input_columns": [],
                "output_columns": [],
                "dropped_columns": [],
                "redacted_cells_by_column": {},
                "redacted_patterns_by_column": {},
            }

        dropped_columns = [
            {"column": col, "reason": _drop_reason(col)}
            for col in columns
            if _drop_reason(col)
        ]
        dropped_names = {item["column"] for item in dropped_columns}
        keep_columns = [
            col for col in columns
            if col not in dropped_names and RDI._normalize_header(col) != "study_subject_id"
        ]
        output_columns = ["study_subject_id"] + keep_columns

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8", newline="") as dst:
            writer = csv.DictWriter(dst, fieldnames=output_columns)
            writer.writeheader()
            for row_count, row in enumerate(reader, 1):
                out_row: Dict[str, str] = {"study_subject_id": f"S{row_count:06d}"}
                for col in keep_columns:
                    redacted, counts = _redact_value((row or {}).get(col))
                    out_row[col] = redacted
                    if counts:
                        redacted_cells_by_column[col] = redacted_cells_by_column.get(col, 0) + 1
                        col_counts = redacted_patterns_by_column.setdefault(col, {})
                        for label, n in counts.items():
                            col_counts[label] = col_counts.get(label, 0) + n
                writer.writerow(out_row)

    return {
        "blocker": None,
        "rows": row_count,
        "input_columns": columns,
        "output_columns": output_columns,
        "dropped_columns": dropped_columns,
        "redacted_cells_by_column": redacted_cells_by_column,
        "redacted_patterns_by_column": redacted_patterns_by_column,
    }


def _write_report(out_dir: Path, report: Dict[str, Any]) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / REPORT_NAME
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    return path


def _update_meta(out_dir: Path, report: Dict[str, Any], report_path: Path) -> None:
    meta = GC.ensure_study_meta(out_dir)
    meta["real_data_deidentification"] = {
        "status": report["status"],
        "report": str(report_path.relative_to(out_dir)),
        "deidentified_path": report.get("deidentified_path"),
        "row_count": report.get("row_count"),
        "input_column_count": report.get("input_column_count"),
        "output_column_count": report.get("output_column_count"),
        "dropped_column_count": report.get("dropped_column_count"),
        "redacted_cell_count": report.get("redacted_cell_count"),
        "intake_status": (report.get("then_import") or {}).get("status"),
        "note": "Báo cáo không lưu giá trị PII; chỉ lưu số lượng/cột/mẫu xử lý.",
    }
    (out_dir / "study_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")


def deidentify_dataset(study: str, data_path: Path, *,
                       output_path: Optional[Path] = None,
                       exports_root: Optional[Path] = None,
                       then_import: bool = False,
                       max_scan_rows: int = 5000) -> Dict[str, Any]:
    """Tạo bản CSV đã khử định danh và tùy chọn nạp qua intake."""
    study_id = RDI._sanitize_study(study)
    data_path = Path(data_path)
    exports_root = Path(exports_root) if exports_root else BASE / "exports"
    out_dir = exports_root / study_id
    output_path = Path(output_path) if output_path else _default_output_path(
        study_id, data_path, exports_root)
    created_at = datetime.now().isoformat(timespec="seconds")

    blocker = _readable_blocker(data_path, output_path)
    process: Dict[str, Any] = {
        "rows": 0,
        "input_columns": [],
        "output_columns": [],
        "dropped_columns": [],
        "redacted_cells_by_column": {},
        "redacted_patterns_by_column": {},
    }

    last_decode_error: Optional[UnicodeDecodeError] = None
    if blocker is None:
        for encoding in ("utf-8-sig", "latin-1"):
            try:
                process = _process_with_encoding(data_path, output_path, encoding)
                blocker = process.get("blocker")
                last_decode_error = None
                break
            except UnicodeDecodeError as exc:
                last_decode_error = exc
                if output_path.exists():
                    output_path.unlink()
                continue
    if last_decode_error is not None:
        blocker = "decode_error: hãy xuất lại CSV UTF-8"

    output_scan: Dict[str, Any] = {"passed": False, "n_blockers": 0, "issues": []}
    deidentified_path: Optional[Path] = None
    output_sha256: Optional[str] = None
    if blocker is None and output_path.exists():
        scan = RDI._scan_csv(output_path, max_scan_rows=max_scan_rows)
        issues = list(scan.get("issues") or [])
        output_scan = {
            "passed": not issues,
            "n_blockers": len(issues),
            "issues": issues,
            "note": "Quét lại bản đã khử định danh trước khi cho phép intake.",
        }
        if issues:
            blocker = "pii_remaining_after_deidentification"
            output_path.unlink(missing_ok=True)
        else:
            deidentified_path = output_path
            output_sha256 = RDI._sha256_file(output_path)

    redacted_cells_by_column = process.get("redacted_cells_by_column") or {}
    redacted_patterns_by_column = process.get("redacted_patterns_by_column") or {}
    report: Dict[str, Any] = {
        "kind": "research_dataset_deidentification_report",
        "study": study_id,
        "status": DEIDENTIFIED_STATUS if blocker is None else BLOCKED_STATUS,
        "created_at": created_at,
        "source_filename": "[NOT_STORED_TO_AVOID_PII_IN_FILENAMES]",
        "source_file_policy": (
            "Tên file nguồn không được ghi vào report vì có thể chứa định danh."
        ),
        "deidentified_path": _safe_rel(deidentified_path, out_dir),
        "output_sha256": output_sha256,
        "row_count": int(process.get("rows") or 0),
        "input_column_count": len(process.get("input_columns") or []),
        "output_column_count": len(process.get("output_columns") or []),
        "dropped_column_count": len(process.get("dropped_columns") or []),
        "dropped_columns": process.get("dropped_columns") or [],
        "redacted_cell_count": sum(int(n) for n in redacted_cells_by_column.values()),
        "redacted_cells_by_column": redacted_cells_by_column,
        "redacted_patterns_by_column": redacted_patterns_by_column,
        "generated_subject_id": "study_subject_id",
        "linkage_mapping_saved": False,
        "output_pii_scan": output_scan,
        "blocker": blocker,
        "rules": [
            "Không sửa file nguồn.",
            "Không lưu giá trị PII trong report.",
            "Không lưu bảng ánh xạ định danh.",
            "Bản khử định danh phải qua intake và khóa dữ liệu trước phân tích.",
        ],
    }

    if then_import and blocker is None and deidentified_path is not None:
        intake = RDI.import_dataset(
            study_id,
            deidentified_path,
            exports_root=exports_root,
            max_scan_rows=max_scan_rows,
        )
        report["then_import"] = {
            "status": intake["status"],
            "manifest": "DATA_INTAKE_manifest.json",
            "raw_readonly_path": intake.get("raw_readonly_path"),
            "analysis_allowed": intake.get("analysis_allowed"),
        }
    elif then_import:
        report["then_import"] = {
            "status": "SKIPPED_BECAUSE_DEIDENTIFICATION_BLOCKED",
            "manifest": None,
            "raw_readonly_path": None,
            "analysis_allowed": False,
        }

    report_path = _write_report(out_dir, report)
    _update_meta(out_dir, report, report_path)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Khử định danh CSV nghiên cứu trước khi import dữ liệu thật.")
    parser.add_argument("--study", required=True, help="Mã đề tài")
    parser.add_argument("--data", required=True, help="Đường dẫn CSV nguồn")
    parser.add_argument("--output", default=None, help="Đường dẫn CSV khử định danh tùy chọn")
    parser.add_argument("--then-import", action="store_true",
                        help="Sau khi khử định danh, nạp ngay qua import_real_dataset")
    parser.add_argument("--max-scan-rows", type=int, default=5000)
    args = parser.parse_args()

    report = deidentify_dataset(
        args.study,
        Path(args.data),
        output_path=Path(args.output) if args.output else None,
        then_import=args.then_import,
        max_scan_rows=args.max_scan_rows,
    )
    print(f"DEIDENTIFICATION: {report['status']}")
    print(
        "rows={rows} dropped_columns={dropped} redacted_cells={redacted}".format(
            rows=report["row_count"],
            dropped=report["dropped_column_count"],
            redacted=report["redacted_cell_count"],
        )
    )
    if report["status"] == DEIDENTIFIED_STATUS:
        print(f"deidentified_path={report['deidentified_path']}")
        if report.get("then_import"):
            print(f"DATA_INTAKE: {report['then_import']['status']}")
        return 0
    print(f"BLOCKED: {report.get('blocker')}; xem {REPORT_NAME}.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
