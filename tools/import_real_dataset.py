#!/usr/bin/env python3
"""Nhập dữ liệu thật đã khử định danh vào hồ sơ nghiên cứu một cách an toàn.

Công cụ này là cổng tiếp nhận TRƯỚC G6:
- Không sửa file nguồn.
- Quét PII theo header và giá trị phổ biến trước khi copy.
- Chỉ copy khi không phát hiện PII rõ ràng.
- Lưu bản raw read-only theo checksum.
- Tạo manifest + query log + cập nhật study_meta.json để G10/G6 truy vết.

Ví dụ:
  python3 tools/import_real_dataset.py --study KKB-HAI-LONG-2026 --data data.csv
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import stat
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

BASE = Path(__file__).resolve().parents[1]
TOOLS = BASE / "tools"
sys.path.insert(0, str(TOOLS))

import gate_contract as GC  # noqa: E402

SUPPORTED_SUFFIXES = {".csv"}
BLOCKED_STATUS = "BLOCKED_PII_OR_UNSAFE"
READY_STATUS = "READY_FOR_CLEANING_NOT_LOCKED"

PII_HEADER_EXACT = {
    "name", "full_name", "patient_name", "ho_ten", "ten_benh_nhan",
    "phone", "mobile", "telephone", "email", "address", "dia_chi",
    "dob", "date_of_birth", "birth_date", "ngay_sinh",
    "cccd", "cmnd", "citizen_id", "national_id", "passport",
    "mrn", "medical_record_number", "hospital_number", "patient_id",
    "bhyt", "insurance_number", "health_insurance_number",
}
PII_HEADER_CONTAINS = (
    "so_dien_thoai", "dien_thoai", "phone_number", "email_address",
    "home_address", "diachi", "ma_benh_an", "so_benh_an", "ma_y_te",
)
VALUE_PATTERNS = {
    "email": re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I),
    "phone_vn": re.compile(r"(?<!\d)0(?:3|5|7|8|9)\d{8}(?!\d)"),
    "cccd_cmnd": re.compile(r"(?<!\d)(?:\d{9}|\d{12})(?!\d)"),
}


def _sanitize_study(study: str) -> str:
    return re.sub(r"[^\w\-]", "_", study.strip().replace(" ", "-"))


def _normalize_header(name: str) -> str:
    s = name.strip().lower()
    s = re.sub(r"[\s\-./]+", "_", s)
    s = re.sub(r"_+", "_", s)
    return s.strip("_")


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _safe_stem(path: Path) -> str:
    stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", path.stem).strip("._")
    return stem or "dataset"


def _header_issue(column: str) -> Optional[str]:
    norm = _normalize_header(column)
    if norm in PII_HEADER_EXACT:
        return f"header_pii:{norm}"
    if any(token in norm for token in PII_HEADER_CONTAINS):
        return f"header_pii:{norm}"
    return None


def _scan_csv(path: Path, *, max_scan_rows: int = 5000) -> Dict[str, Any]:
    issues: List[Dict[str, Any]] = []
    row_count = 0
    columns: List[str] = []

    last_decode_error: Optional[UnicodeDecodeError] = None
    for encoding in ("utf-8-sig", "latin-1"):
        try:
            with path.open("r", encoding=encoding, newline="") as f:
                sample = f.read(4096)
                f.seek(0)
                try:
                    dialect = csv.Sniffer().sniff(sample)
                except csv.Error:
                    dialect = csv.excel
                reader = csv.DictReader(f, dialect=dialect)
                columns = list(reader.fieldnames or [])
                if not columns:
                    issues.append({
                        "severity": "blocker",
                        "type": "empty_header",
                        "column": None,
                        "detail": "CSV không có header.",
                    })
                    return {"rows": 0, "columns": [], "issues": issues}

                for col in columns:
                    reason = _header_issue(col)
                    if reason:
                        issues.append({
                            "severity": "blocker",
                            "type": reason,
                            "column": col,
                            "detail": "Tên cột gợi ý định danh trực tiếp/nhạy cảm.",
                        })

                for row in reader:
                    row_count += 1
                    if row_count > max_scan_rows:
                        continue
                    for col, value in (row or {}).items():
                        text = str(value or "").strip()
                        if not text:
                            continue
                        for label, pattern in VALUE_PATTERNS.items():
                            if pattern.search(text):
                                issues.append({
                                    "severity": "blocker",
                                    "type": f"value_pii:{label}",
                                    "column": col,
                                    "row": row_count,
                                    "detail": (
                                        "Giá trị khớp mẫu PII; không lưu giá trị trong manifest."
                                    ),
                                })
                return {"rows": row_count, "columns": columns, "issues": issues}
        except UnicodeDecodeError as exc:
            last_decode_error = exc
            row_count = 0
            columns = []
            issues = []
            continue
        except OSError as exc:
            issues.append({
                "severity": "blocker",
                "type": "read_error",
                "column": None,
                "detail": f"Không đọc được file: {exc}",
            })
            return {"rows": row_count, "columns": columns, "issues": issues}

    if last_decode_error:
        issues.append({
            "severity": "blocker",
            "type": "decode_error",
            "column": None,
            "detail": "Không đọc được CSV bằng UTF-8/Latin-1; hãy xuất lại CSV UTF-8.",
        })
    return {"rows": row_count, "columns": columns, "issues": issues}


def _write_query_log(path: Path, issues: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "timestamp", "issue_type", "column", "row",
                "detail", "status", "owner", "resolution",
            ],
        )
        writer.writeheader()
        now = datetime.now().isoformat(timespec="seconds")
        if not issues:
            writer.writerow({
                "timestamp": now,
                "issue_type": "INTAKE_CHECK",
                "column": "",
                "row": "",
                "detail": "Không phát hiện PII rõ ràng trong bước intake.",
                "status": "closed",
                "owner": "data manager + PI",
                "resolution": "raw copied read-only; cleaning chưa chạy",
            })
            return
        for issue in issues:
            writer.writerow({
                "timestamp": now,
                "issue_type": issue.get("type", "unknown"),
                "column": issue.get("column") or "",
                "row": issue.get("row") or "",
                "detail": issue.get("detail") or "",
                "status": "open",
                "owner": "data manager + PI",
                "resolution": "remove/deidentify at source, then re-import",
            })


def _write_manifest(out_dir: Path, manifest: Dict[str, Any]) -> Path:
    path = out_dir / "DATA_INTAKE_manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _update_study_meta(out_dir: Path, manifest: Dict[str, Any], manifest_path: Path) -> None:
    meta = GC.ensure_study_meta(out_dir)
    meta["real_data_intake"] = {
        "status": manifest["status"],
        "manifest": str(manifest_path.relative_to(out_dir)),
        "source_filename": manifest["source_filename"],
        "rows": manifest["row_count"],
        "columns": manifest["column_count"],
        "sha256": manifest.get("sha256"),
        "raw_readonly_path": manifest.get("raw_readonly_path"),
        "imported_at": manifest["imported_at"],
        "db_locked": False,
        "note": "Dữ liệu thật đã nhập nhưng CHƯA khóa DB; không phân tích chính cho tới khi có lock memo.",
    }
    (out_dir / "study_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def import_dataset(study: str, data_path: Path, *,
                   exports_root: Optional[Path] = None,
                   max_scan_rows: int = 5000) -> Dict[str, Any]:
    """Nhập 1 CSV đã khử định danh. Trả manifest máy-đọc-được."""
    study_id = _sanitize_study(study)
    data_path = Path(data_path)
    exports_root = Path(exports_root) if exports_root else BASE / "exports"
    out_dir = exports_root / study_id
    out_dir.mkdir(parents=True, exist_ok=True)

    imported_at = datetime.now().isoformat(timespec="seconds")
    suffix = data_path.suffix.lower()
    issues: List[Dict[str, Any]] = []
    if suffix not in SUPPORTED_SUFFIXES:
        issues.append({
            "severity": "blocker",
            "type": "unsupported_format",
            "column": None,
            "detail": "Hiện chỉ nhận CSV đã khử định danh; hãy xuất CSV từ REDCap/EDC.",
        })
        profile = {"rows": 0, "columns": [], "issues": issues}
    elif not data_path.exists():
        issues.append({
            "severity": "blocker",
            "type": "missing_file",
            "column": None,
            "detail": "Không thấy file dữ liệu.",
        })
        profile = {"rows": 0, "columns": [], "issues": issues}
    else:
        profile = _scan_csv(data_path, max_scan_rows=max_scan_rows)
        issues = list(profile["issues"])

    query_log = out_dir / "04_query_logs" / "data_intake_query_log.csv"
    _write_query_log(query_log, issues)

    manifest: Dict[str, Any] = {
        "kind": "real_data_intake_manifest",
        "study": study_id,
        "status": BLOCKED_STATUS if issues else READY_STATUS,
        "imported_at": imported_at,
        "source_filename": data_path.name,
        "supported_format": suffix in SUPPORTED_SUFFIXES,
        "row_count": int(profile["rows"]),
        "column_count": len(profile["columns"]),
        "columns": profile["columns"],
        "max_scan_rows": max_scan_rows,
        "pii_scan": {
            "passed": not issues,
            "n_blockers": len(issues),
            "issues": issues,
            "note": "Manifest không lưu giá trị PII; chỉ lưu vị trí/mẫu phát hiện.",
        },
        "raw_readonly_path": None,
        "sha256": None,
        "query_log": str(query_log.relative_to(out_dir)),
        "db_locked": False,
        "analysis_allowed": False,
        "rules": [
            "Không sửa file nguồn.",
            "Không copy dữ liệu nếu phát hiện PII.",
            "Bản raw trong 02_raw_readonly là chỉ đọc.",
            "Chỉ làm sạch trên bản sao bằng script/query log.",
            "Không phân tích chính cho tới khi có lock memo và data_lock_date thật.",
        ],
    }

    if not issues and data_path.exists():
        sha = _sha256_file(data_path)
        raw_dir = out_dir / "02_raw_readonly"
        raw_dir.mkdir(parents=True, exist_ok=True)
        dest = raw_dir / f"{_safe_stem(data_path)}.{sha[:12]}{suffix}"
        if not dest.exists():
            shutil.copy2(data_path, dest)
        os.chmod(dest, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
        manifest["raw_readonly_path"] = str(dest.relative_to(out_dir))
        manifest["sha256"] = sha

    manifest_path = _write_manifest(out_dir, manifest)
    _update_study_meta(out_dir, manifest, manifest_path)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Nhập CSV dữ liệu thật đã khử định danh vào hồ sơ nghiên cứu.")
    parser.add_argument("--study", required=True, help="Mã đề tài")
    parser.add_argument("--data", required=True, help="Đường dẫn CSV đã khử định danh")
    parser.add_argument("--max-scan-rows", type=int, default=5000,
                        help="Số dòng tối đa quét PII giá trị (mặc định 5000)")
    args = parser.parse_args()

    manifest = import_dataset(
        args.study,
        Path(args.data),
        max_scan_rows=args.max_scan_rows,
    )
    print(f"DATA_INTAKE: {manifest['status']}")
    print(f"rows={manifest['row_count']} columns={manifest['column_count']}")
    if manifest["pii_scan"]["passed"]:
        print(f"raw_readonly={manifest['raw_readonly_path']}")
        print("Tiếp theo: chạy script làm sạch trên bản sao; chưa phân tích chính khi chưa khóa DB.")
        return 0
    print("BLOCKED: phát hiện nguy cơ PII/định dạng không an toàn; xem DATA_INTAKE_manifest.json.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
