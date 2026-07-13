#!/usr/bin/env python3
"""Mã hóa thay thế (pseudonymization) CSV nghiên cứu có bảng ánh xạ bảo vệ riêng.

Công cụ này tạo 2 lớp tách biệt:
- Dataset phân tích: thay định danh bằng `study_subject_id`, loại cột PII,
  redact PII lẫn trong ô tự do, có thể nạp qua intake an toàn.
- Bảng ánh xạ: lưu riêng ngoài repo/OneDrive mặc định, chmod 700/600, không ghi
  đường dẫn hay giá trị PII vào report công khai trong exports.

Pseudonymization KHÔNG phải anonymization tuyệt đối vì còn bảng ánh xạ. Chỉ dùng
khi protocol/IRB/data management plan cho phép tái định danh có kiểm soát.

Ví dụ:
  python3 tools/pseudonymize_research_dataset.py --study KKB-HAI-LONG-2026 \\
    --data raw_export.csv --then-import
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import stat
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

BASE = Path(__file__).resolve().parents[1]
TOOLS = BASE / "tools"
sys.path.insert(0, str(TOOLS))

import gate_contract as GC  # noqa: E402
import import_real_dataset as RDI  # noqa: E402

PSEUDONYMIZED_STATUS = "PSEUDONYMIZED_READY_FOR_INTAKE"
BLOCKED_STATUS = "BLOCKED_PSEUDONYMIZATION"
REDACTION_TOKEN = "[REDACTED_PII]"
REPORT_NAME = "PSEUDONYMIZATION_report.json"
MAPPING_MANIFEST_NAME = "PSEUDONYMIZATION_mapping_manifest.json"
LINKAGE_MAP_NAME = "linkage_map.csv"
REDACTION_MAP_NAME = "redaction_map.csv"


def _default_mapping_root() -> Path:
    return Path.home() / ".ebm-secrets" / "ebm_pseudonymization"


def _default_output_path(study_id: str, data_path: Path, exports_root: Path) -> Path:
    raw_hash = RDI._sha256_file(data_path) if data_path.exists() else "missing"
    return exports_root / study_id / "00_pseudonymized" / f"pseudonymized.{raw_hash[:12]}.csv"


def _safe_rel(path: Optional[Path], base: Path) -> Optional[str]:
    if path is None:
        return None
    try:
        return str(path.relative_to(base))
    except ValueError:
        return str(path.name)


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.resolve().relative_to(base.resolve())
        return True
    except ValueError:
        return False


def _is_onedrive_path(path: Path) -> bool:
    return any("onedrive" in part.lower() for part in path.expanduser().parts)


def _mapping_root_blocker(mapping_root: Path, exports_root: Path) -> Optional[str]:
    if _is_relative_to(mapping_root, BASE):
        return "mapping_root_inside_repo"
    if _is_relative_to(mapping_root, exports_root):
        return "mapping_root_inside_exports"
    if _is_onedrive_path(mapping_root):
        return "mapping_root_inside_onedrive"
    return None


def _secure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    os.chmod(path, stat.S_IRWXU)


def _secure_file(path: Path) -> None:
    os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)


def _redact_value(value: Any) -> Tuple[str, List[Dict[str, str]]]:
    text = "" if value is None else str(value)
    redactions: List[Dict[str, str]] = []
    redacted = text
    for label, pattern in RDI.VALUE_PATTERNS.items():
        matches = list(pattern.finditer(redacted))
        if not matches:
            continue
        for match in matches:
            redactions.append({"pattern_label": label, "value": match.group(0)})
        redacted = pattern.sub(REDACTION_TOKEN, redacted)
    return redacted, redactions


def _readable_blocker(data_path: Path, output_path: Path,
                      mapping_root: Path, exports_root: Path) -> Optional[str]:
    if data_path.suffix.lower() not in RDI.SUPPORTED_SUFFIXES:
        return "unsupported_format: chỉ hỗ trợ CSV"
    if not data_path.exists():
        return "missing_file"
    try:
        if data_path.resolve() == output_path.resolve():
            return "output_path_must_not_overwrite_source"
    except OSError:
        return None
    return _mapping_root_blocker(mapping_root, exports_root)


def _process_with_encoding(data_path: Path, output_path: Path, mapping_dir: Path,
                           encoding: str, id_prefix: str) -> Dict[str, Any]:
    row_count = 0
    redacted_cells_by_column: Dict[str, int] = {}
    redacted_patterns_by_column: Dict[str, Dict[str, int]] = {}
    redaction_rows: List[Dict[str, Any]] = []

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
                "linkage_rows": 0,
                "redaction_rows": 0,
            }

        dropped_columns = [
            {"column": col, "reason": RDI._header_issue(col)}
            for col in columns
            if RDI._header_issue(col)
        ]
        pii_columns = [item["column"] for item in dropped_columns]
        dropped_names = set(pii_columns)
        keep_columns = [
            col for col in columns
            if col not in dropped_names and RDI._normalize_header(col) != "study_subject_id"
        ]
        output_columns = ["study_subject_id"] + keep_columns
        linkage_columns = ["study_subject_id", "source_row_number"] + pii_columns

        output_path.parent.mkdir(parents=True, exist_ok=True)
        linkage_path = mapping_dir / LINKAGE_MAP_NAME
        redaction_path = mapping_dir / REDACTION_MAP_NAME

        with output_path.open("w", encoding="utf-8", newline="") as dst, \
                linkage_path.open("w", encoding="utf-8", newline="") as link:
            out_writer = csv.DictWriter(dst, fieldnames=output_columns)
            link_writer = csv.DictWriter(link, fieldnames=linkage_columns)
            out_writer.writeheader()
            link_writer.writeheader()

            for row_count, row in enumerate(reader, 1):
                subject_id = f"{id_prefix}-{row_count:06d}"
                out_row: Dict[str, str] = {"study_subject_id": subject_id}
                link_row: Dict[str, str] = {
                    "study_subject_id": subject_id,
                    "source_row_number": str(row_count),
                }
                for col in pii_columns:
                    link_row[col] = str((row or {}).get(col) or "")
                for col in keep_columns:
                    redacted, redactions = _redact_value((row or {}).get(col))
                    out_row[col] = redacted
                    if redactions:
                        redacted_cells_by_column[col] = redacted_cells_by_column.get(col, 0) + 1
                        col_counts = redacted_patterns_by_column.setdefault(col, {})
                        for idx, item in enumerate(redactions, 1):
                            label = item["pattern_label"]
                            col_counts[label] = col_counts.get(label, 0) + 1
                            redaction_rows.append({
                                "study_subject_id": subject_id,
                                "source_row_number": row_count,
                                "column": col,
                                "pattern_label": label,
                                "occurrence_index": idx,
                                "value": item["value"],
                            })
                out_writer.writerow(out_row)
                link_writer.writerow(link_row)

        with redaction_path.open("w", encoding="utf-8", newline="") as red:
            fieldnames = [
                "study_subject_id", "source_row_number", "column",
                "pattern_label", "occurrence_index", "value",
            ]
            red_writer = csv.DictWriter(red, fieldnames=fieldnames)
            red_writer.writeheader()
            red_writer.writerows(redaction_rows)

        _secure_file(linkage_path)
        _secure_file(redaction_path)

    return {
        "blocker": None,
        "rows": row_count,
        "input_columns": columns,
        "output_columns": output_columns,
        "dropped_columns": dropped_columns,
        "redacted_cells_by_column": redacted_cells_by_column,
        "redacted_patterns_by_column": redacted_patterns_by_column,
        "linkage_rows": row_count,
        "redaction_rows": len(redaction_rows),
    }


def _write_json(path: Path, payload: Dict[str, Any]) -> Path:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _write_report(out_dir: Path, report: Dict[str, Any]) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    return _write_json(out_dir / REPORT_NAME, report)


def _write_mapping_manifest(mapping_dir: Path, manifest: Dict[str, Any]) -> Path:
    path = _write_json(mapping_dir / MAPPING_MANIFEST_NAME, manifest)
    _secure_file(path)
    return path


def _update_meta(out_dir: Path, report: Dict[str, Any], report_path: Path) -> None:
    meta = GC.ensure_study_meta(out_dir)
    meta["real_data_pseudonymization"] = {
        "status": report["status"],
        "report": str(report_path.relative_to(out_dir)),
        "pseudonymized_path": report.get("pseudonymized_path"),
        "row_count": report.get("row_count"),
        "dropped_column_count": report.get("dropped_column_count"),
        "redacted_cell_count": report.get("redacted_cell_count"),
        "protected_mapping_created": report.get("protected_mapping_created"),
        "mapping_location": "[PROTECTED_EXTERNAL_ROOT]",
        "intake_status": (report.get("then_import") or {}).get("status"),
        "note": (
            "Pseudonymization còn bảng ánh xạ; bảng ánh xạ là PII và không nằm "
            "trong exports/repo/OneDrive."
        ),
    }
    (out_dir / "study_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def pseudonymize_dataset(study: str, data_path: Path, *,
                         output_path: Optional[Path] = None,
                         exports_root: Optional[Path] = None,
                         mapping_root: Optional[Path] = None,
                         then_import: bool = False,
                         max_scan_rows: int = 5000,
                         id_prefix: str = "PSN") -> Dict[str, Any]:
    """Tạo dataset pseudonymized và bảng ánh xạ bảo vệ riêng."""
    study_id = RDI._sanitize_study(study)
    data_path = Path(data_path)
    exports_root = Path(exports_root) if exports_root else BASE / "exports"
    mapping_root = Path(mapping_root).expanduser() if mapping_root else _default_mapping_root()
    out_dir = exports_root / study_id
    output_path = Path(output_path) if output_path else _default_output_path(
        study_id, data_path, exports_root)
    created_at = datetime.now().isoformat(timespec="seconds")
    source_hash = RDI._sha256_file(data_path) if data_path.exists() else "missing"
    mapping_dir = mapping_root / study_id / source_hash[:12]

    blocker = _readable_blocker(data_path, output_path, mapping_root, exports_root)
    process: Dict[str, Any] = {
        "rows": 0,
        "input_columns": [],
        "output_columns": [],
        "dropped_columns": [],
        "redacted_cells_by_column": {},
        "redacted_patterns_by_column": {},
        "linkage_rows": 0,
        "redaction_rows": 0,
    }

    last_decode_error: Optional[UnicodeDecodeError] = None
    if blocker is None:
        _secure_dir(mapping_dir)
        for encoding in ("utf-8-sig", "latin-1"):
            try:
                process = _process_with_encoding(
                    data_path, output_path, mapping_dir, encoding, id_prefix)
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
    pseudonymized_path: Optional[Path] = None
    output_sha256: Optional[str] = None
    if blocker is None and output_path.exists():
        scan = RDI._scan_csv(output_path, max_scan_rows=max_scan_rows)
        issues = list(scan.get("issues") or [])
        output_scan = {
            "passed": not issues,
            "n_blockers": len(issues),
            "issues": issues,
            "note": "Quét lại dataset pseudonymized trước khi cho phép intake.",
        }
        if issues:
            blocker = "pii_remaining_after_pseudonymization"
            output_path.unlink(missing_ok=True)
        else:
            pseudonymized_path = output_path
            output_sha256 = RDI._sha256_file(output_path)

    protected_mapping_created = blocker is None
    mapping_manifest = {
        "kind": "research_dataset_pseudonymization_mapping_manifest",
        "study": study_id,
        "status": "PROTECTED_MAPPING_CREATED" if protected_mapping_created else BLOCKED_STATUS,
        "created_at": created_at,
        "source_filename": RDI._safe_source_filename(data_path),
        "source_sha256": source_hash if source_hash != "missing" else None,
        "linkage_map": LINKAGE_MAP_NAME if protected_mapping_created else None,
        "redaction_map": REDACTION_MAP_NAME if protected_mapping_created else None,
        "row_count": int(process.get("rows") or 0),
        "pii_column_count": len(process.get("dropped_columns") or []),
        "redaction_rows": process.get("redaction_rows") or 0,
        "file_permission_policy": "directory=700; files=600",
        "storage_policy": "Bảng ánh xạ là PII; lưu ngoài repo/OneDrive hoặc vault đã phê duyệt.",
    }
    if blocker is None:
        _write_mapping_manifest(mapping_dir, mapping_manifest)

    redacted_cells_by_column = process.get("redacted_cells_by_column") or {}
    report: Dict[str, Any] = {
        "kind": "research_dataset_pseudonymization_report",
        "study": study_id,
        "status": PSEUDONYMIZED_STATUS if blocker is None else BLOCKED_STATUS,
        "created_at": created_at,
        "source_filename": "[NOT_STORED_TO_AVOID_PII_IN_FILENAMES]",
        "source_file_policy": "Tên file nguồn không được ghi vào report công khai.",
        "pseudonymized_path": _safe_rel(pseudonymized_path, out_dir),
        "output_sha256": output_sha256,
        "row_count": int(process.get("rows") or 0),
        "input_column_count": len(process.get("input_columns") or []),
        "output_column_count": len(process.get("output_columns") or []),
        "dropped_column_count": len(process.get("dropped_columns") or []),
        "dropped_columns": process.get("dropped_columns") or [],
        "redacted_cell_count": sum(int(n) for n in redacted_cells_by_column.values()),
        "redacted_cells_by_column": redacted_cells_by_column,
        "redacted_patterns_by_column": process.get("redacted_patterns_by_column") or {},
        "generated_subject_id": "study_subject_id",
        "protected_mapping_created": protected_mapping_created,
        "mapping_location": "[PROTECTED_EXTERNAL_ROOT]",
        "mapping_storage_policy": (
            "Bảng ánh xạ chứa PII, đặt ngoài exports/repo/OneDrive; chỉ PI/data "
            "manager được phép truy cập."
        ),
        "mapping_manifest": MAPPING_MANIFEST_NAME if protected_mapping_created else None,
        "output_pii_scan": output_scan,
        "blocker": blocker,
        "rules": [
            "Không sửa file nguồn.",
            "Dataset phân tích không chứa PII trực tiếp.",
            "Bảng ánh xạ là PII và không được commit/sync cloud công khai.",
            "Pseudonymization cần được mô tả trong protocol/IRB/DMP.",
            "Dataset pseudonymized vẫn phải qua intake và khóa dữ liệu trước phân tích.",
        ],
    }

    if then_import and blocker is None and pseudonymized_path is not None:
        intake = RDI.import_dataset(
            study_id,
            pseudonymized_path,
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
            "status": "SKIPPED_BECAUSE_PSEUDONYMIZATION_BLOCKED",
            "manifest": None,
            "raw_readonly_path": None,
            "analysis_allowed": False,
        }

    report_path = _write_report(out_dir, report)
    _update_meta(out_dir, report, report_path)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Pseudonymize CSV nghiên cứu và lưu bảng ánh xạ bảo vệ riêng.")
    parser.add_argument("--study", required=True, help="Mã đề tài")
    parser.add_argument("--data", required=True, help="Đường dẫn CSV nguồn có PII")
    parser.add_argument("--output", default=None, help="Đường dẫn CSV pseudonymized tùy chọn")
    parser.add_argument(
        "--mapping-root",
        default=None,
        help="Thư mục gốc bảo vệ bảng ánh xạ; mặc định ~/.ebm-secrets/ebm_pseudonymization",
    )
    parser.add_argument("--id-prefix", default="PSN", help="Tiền tố mã định danh giả")
    parser.add_argument("--then-import", action="store_true",
                        help="Sau khi pseudonymize, nạp ngay dataset sạch qua intake")
    parser.add_argument("--max-scan-rows", type=int, default=5000)
    args = parser.parse_args()

    report = pseudonymize_dataset(
        args.study,
        Path(args.data),
        output_path=Path(args.output) if args.output else None,
        mapping_root=Path(args.mapping_root) if args.mapping_root else None,
        then_import=args.then_import,
        max_scan_rows=args.max_scan_rows,
        id_prefix=args.id_prefix,
    )
    print(f"PSEUDONYMIZATION: {report['status']}")
    print(
        "rows={rows} dropped_columns={dropped} redacted_cells={redacted}".format(
            rows=report["row_count"],
            dropped=report["dropped_column_count"],
            redacted=report["redacted_cell_count"],
        )
    )
    if report["status"] == PSEUDONYMIZED_STATUS:
        print(f"pseudonymized_path={report['pseudonymized_path']}")
        print("protected_mapping=[PROTECTED_EXTERNAL_ROOT]")
        if report.get("then_import"):
            print(f"DATA_INTAKE: {report['then_import']['status']}")
        return 0
    print(f"BLOCKED: {report.get('blocker')}; xem {REPORT_NAME}.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
