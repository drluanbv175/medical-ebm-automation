#!/usr/bin/env python3
"""Làm sạch dữ liệu nghiên cứu y khoa trên bản sao, có query log kiểm toán.

Công cụ này nằm giữa intake/pseudonymization/de-identification và data lock:
- Không sửa file nguồn.
- Chặn nếu dataset còn PII.
- Tạo bản clean working copy.
- Chỉ tự động hóa các thao tác an toàn: trim whitespace, chuẩn hóa mã missing.
- Không tự sửa giá trị lâm sàng/phương pháp mơ hồ; chỉ tạo query log mở.
- Data lock sẽ tự chặn nếu query log còn open.

Ví dụ:
  python3 tools/clean_research_dataset.py --study KKB-HAI-LONG-2026 \\
    --data exports/KKB-HAI-LONG-2026/02_raw_readonly/data.abc123.csv \\
    --dictionary exports/KKB-HAI-LONG-2026/data_dictionary.json
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

BASE = Path(__file__).resolve().parents[1]
TOOLS = BASE / "tools"
sys.path.insert(0, str(TOOLS))

import gate_contract as GC  # noqa: E402
import import_real_dataset as RDI  # noqa: E402

CLEAN_READY_STATUS = "CLEAN_READY_FOR_LOCK"
CLEAN_QUERY_STATUS = "CLEAN_REQUIRES_QUERY_RESOLUTION"
BLOCKED_STATUS = "BLOCKED_CLEANING_REQUIREMENTS"
REPORT_NAME = "DATA_CLEANING_report.json"
PLAN_NAME = "DATA_CLEANING_plan.json"
QUERY_LOG_NAME = "data_cleaning_query_log.csv"

DEFAULT_MISSING_TOKENS = {
    "",
    ".",
    "-",
    "na",
    "n_a",
    "n/a",
    "null",
    "none",
    "missing",
    "unknown",
    "khong_ro",
    "khong_ap_dung",
    "khong_co",
}
DEFAULT_ID_CANDIDATES = (
    "study_subject_id",
    "record_id",
    "participant_id",
    "subject_id",
    "id",
)


def _safe_rel(path: Optional[Path], base: Path) -> Optional[str]:
    if path is None:
        return None
    try:
        return str(path.relative_to(base))
    except ValueError:
        return str(path)


def _default_output_path(study_id: str, data_path: Path, exports_root: Path) -> Path:
    source_hash = RDI._sha256_file(data_path) if data_path.exists() else "missing"
    return exports_root / study_id / "03_clean_working" / f"df_clean.{source_hash[:12]}.csv"


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "x", "required", "bat_buoc"}


def _split_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    text = str(value).strip()
    if not text:
        return []
    for sep in ("|", ";"):
        if sep in text:
            return [item.strip() for item in text.split(sep) if item.strip()]
    return [item.strip() for item in text.split(",") if item.strip()]


def _variable_name(raw: Dict[str, Any]) -> Optional[str]:
    for key in ("name", "variable", "variable_name", "field_name", "ten_bien"):
        value = raw.get(key)
        if value:
            return str(value).strip()
    return None


def _normalise_rule(raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    name = _variable_name(raw)
    if not name:
        return None
    allowed = raw.get("allowed")
    if allowed is None:
        allowed = raw.get("allowed_values")
    if allowed is None:
        allowed = raw.get("choices")
    rule = {
        "name": name,
        "type": str(raw.get("type") or raw.get("data_type") or "text").strip().lower(),
        "required": _truthy(raw.get("required") or raw.get("bat_buoc")),
        "min": raw.get("min"),
        "max": raw.get("max"),
        "allowed": _split_list(allowed),
        "date_format": str(raw.get("date_format") or "%Y-%m-%d").strip(),
    }
    return rule


def _load_dictionary(path: Optional[Path]) -> Dict[str, Any]:
    if path is None:
        return {"variables": [], "id_column": None, "missing_tokens": []}
    path = Path(path)
    if not path.exists():
        return {
            "variables": [],
            "id_column": None,
            "missing_tokens": [],
            "blocker": "missing_dictionary_file",
        }
    if path.suffix.lower() == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            raw_vars = payload.get("variables") or payload.get("fields") or []
            if isinstance(raw_vars, dict):
                raw_vars = list(raw_vars.values())
            return {
                "variables": [
                    rule for item in raw_vars
                    if isinstance(item, dict)
                    for rule in [_normalise_rule(item)]
                    if rule
                ],
                "id_column": payload.get("id_column") or payload.get("record_id_column"),
                "missing_tokens": _split_list(payload.get("missing_tokens")),
            }
    if path.suffix.lower() == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            return {
                "variables": [
                    rule for row in reader
                    for rule in [_normalise_rule(row)]
                    if rule
                ],
                "id_column": None,
                "missing_tokens": [],
            }
    return {
        "variables": [],
        "id_column": None,
        "missing_tokens": [],
        "blocker": "unsupported_dictionary_format",
    }


def _read_csv(path: Path) -> Tuple[List[str], List[Dict[str, str]], csv.Dialect]:
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
                rows = [dict(row) for row in reader]
                return columns, rows, dialect
        except UnicodeDecodeError as exc:
            last_decode_error = exc
            continue
    if last_decode_error:
        raise UnicodeDecodeError("utf-8", b"", 0, 1, "decode_error")
    return [], [], csv.excel


def _missing_key(value: str) -> str:
    return RDI._normalize_header(value)


def _clean_cell(value: Any, missing_tokens: Iterable[str]) -> Tuple[str, Dict[str, int]]:
    original = "" if value is None else str(value)
    collapsed = " ".join(original.strip().split())
    actions: Dict[str, int] = {}
    if collapsed != original:
        actions["trim_or_collapse_whitespace"] = 1
    missing_keys = {_missing_key(token) for token in missing_tokens}
    if _missing_key(collapsed) in missing_keys:
        if collapsed != "":
            actions["standardize_missing_token"] = 1
        return "", actions
    return collapsed, actions


def _parse_float(value: str) -> Optional[float]:
    if value == "":
        return None
    try:
        return float(value)
    except ValueError:
        if "," in value and "." not in value:
            try:
                return float(value.replace(",", "."))
            except ValueError:
                return None
    return None


def _issue(issue_type: str, column: Optional[str], row: Optional[int],
           detail: str) -> Dict[str, Any]:
    return {
        "severity": "query",
        "type": issue_type,
        "column": column,
        "row": row,
        "detail": detail,
        "status": "open",
    }


def _detect_id_column(columns: List[str], rules: Dict[str, Dict[str, Any]],
                      id_column: Optional[str]) -> Optional[str]:
    if id_column and id_column in columns:
        return id_column
    for rule in rules.values():
        if rule["name"] in columns and _truthy(rule.get("is_id")):
            return rule["name"]
    normalised = {RDI._normalize_header(col): col for col in columns}
    for candidate in DEFAULT_ID_CANDIDATES:
        if candidate in normalised:
            return normalised[candidate]
    return None


def _validate_rows(columns: List[str], rows: List[Dict[str, str]],
                   rules: Dict[str, Dict[str, Any]],
                   id_column: Optional[str],
                   required_columns: List[str]) -> List[Dict[str, Any]]:
    issues: List[Dict[str, Any]] = []
    normalised_columns = {RDI._normalize_header(col): col for col in columns}

    for required in required_columns:
        if required not in columns and RDI._normalize_header(required) not in normalised_columns:
            issues.append(_issue(
                "missing_required_column",
                required,
                None,
                "Thiếu biến bắt buộc theo data dictionary/SAP.",
            ))

    seen_ids: Dict[str, int] = {}
    for row_idx, row in enumerate(rows, 1):
        if id_column:
            value = str(row.get(id_column) or "").strip()
            if value:
                if value in seen_ids:
                    issues.append(_issue(
                        "duplicate_id",
                        id_column,
                        row_idx,
                        "ID nghiên cứu bị trùng; không lưu giá trị ID trong query log.",
                    ))
                else:
                    seen_ids[value] = row_idx

        for col in columns:
            value = str(row.get(col) or "")
            rule = rules.get(RDI._normalize_header(col))
            if not rule:
                continue
            if rule.get("required") and value == "":
                issues.append(_issue(
                    "missing_required_value",
                    col,
                    row_idx,
                    "Biến bắt buộc bị thiếu; không tự điền.",
                ))
                continue
            if value == "":
                continue

            dtype = str(rule.get("type") or "text").lower()
            if dtype in {"number", "numeric", "float", "int", "integer"}:
                number = _parse_float(value)
                if number is None:
                    issues.append(_issue(
                        "invalid_numeric",
                        col,
                        row_idx,
                        "Không parse được số; không lưu giá trị trong query log.",
                    ))
                    continue
                if dtype in {"int", "integer"} and not number.is_integer():
                    issues.append(_issue(
                        "invalid_integer",
                        col,
                        row_idx,
                        "Giá trị không phải số nguyên; không tự làm tròn.",
                    ))
                min_v = rule.get("min")
                max_v = rule.get("max")
                if min_v not in (None, "") and number < float(min_v):
                    issues.append(_issue(
                        "range_low",
                        col,
                        row_idx,
                        f"Giá trị thấp hơn min={min_v}; không lưu giá trị.",
                    ))
                if max_v not in (None, "") and number > float(max_v):
                    issues.append(_issue(
                        "range_high",
                        col,
                        row_idx,
                        f"Giá trị cao hơn max={max_v}; không lưu giá trị.",
                    ))
            elif dtype in {"category", "categorical", "cat", "choice"}:
                allowed = [str(item) for item in (rule.get("allowed") or [])]
                if allowed and value not in allowed:
                    issues.append(_issue(
                        "invalid_category",
                        col,
                        row_idx,
                        "Giá trị ngoài danh mục hợp lệ; không lưu giá trị.",
                    ))
            elif dtype == "date":
                from datetime import datetime as _dt

                fmt = str(rule.get("date_format") or "%Y-%m-%d")
                try:
                    _dt.strptime(value, fmt)
                except ValueError:
                    issues.append(_issue(
                        "invalid_date",
                        col,
                        row_idx,
                        f"Ngày không khớp định dạng {fmt}; không lưu giá trị.",
                    ))
    return issues


def _write_query_log(path: Path, issues: List[Dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now().isoformat(timespec="seconds")
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "timestamp", "issue_type", "column", "row",
                "detail", "status", "owner", "resolution",
            ],
        )
        writer.writeheader()
        if not issues:
            writer.writerow({
                "timestamp": now,
                "issue_type": "CLEANING_CHECK",
                "column": "",
                "row": "",
                "detail": "Không còn query mở sau làm sạch an toàn.",
                "status": "closed",
                "owner": "data manager + PI",
                "resolution": "ready for data lock review",
            })
            return path
        for item in issues:
            writer.writerow({
                "timestamp": now,
                "issue_type": item["type"],
                "column": item.get("column") or "",
                "row": item.get("row") or "",
                "detail": item.get("detail") or "",
                "status": item.get("status") or "open",
                "owner": "data manager + PI",
                "resolution": "verify against source/CRF; do not guess",
            })
    return path


def _write_json(path: Path, payload: Dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _update_meta(out_dir: Path, report: Dict[str, Any], report_path: Path) -> None:
    meta = GC.ensure_study_meta(out_dir)
    meta["real_data_cleaning"] = {
        "status": report["status"],
        "report": str(report_path.relative_to(out_dir)),
        "clean_dataset_path": report.get("clean_dataset_path"),
        "query_log": report.get("query_log"),
        "plan": report.get("plan"),
        "row_count": report.get("row_count"),
        "column_count": report.get("column_count"),
        "open_query_count": report.get("open_query_count"),
        "ready_for_lock": report.get("ready_for_lock"),
        "note": "Làm sạch trên bản sao; query mở phải được đóng trước data lock.",
    }
    (out_dir / "study_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def clean_dataset(study: str, data_path: Path, *,
                  dictionary_path: Optional[Path] = None,
                  output_path: Optional[Path] = None,
                  exports_root: Optional[Path] = None,
                  id_column: Optional[str] = None,
                  required_columns: Optional[List[str]] = None,
                  missing_tokens: Optional[List[str]] = None,
                  max_scan_rows: int = 5000) -> Dict[str, Any]:
    """Làm sạch an toàn 1 CSV đã khử định danh/pseudonymized."""
    study_id = RDI._sanitize_study(study)
    data_path = Path(data_path)
    exports_root = Path(exports_root) if exports_root else BASE / "exports"
    out_dir = exports_root / study_id
    output_path = Path(output_path) if output_path else _default_output_path(
        study_id, data_path, exports_root)
    cleaned_at = datetime.now().isoformat(timespec="seconds")

    blocker: Optional[str] = None
    if data_path.suffix.lower() not in RDI.SUPPORTED_SUFFIXES:
        blocker = "unsupported_format: chỉ hỗ trợ CSV"
    elif not data_path.exists():
        blocker = "missing_file"
    else:
        try:
            if data_path.resolve() == output_path.resolve():
                blocker = "output_path_must_not_overwrite_source"
        except OSError:
            blocker = None

    pii_scan = {"passed": False, "n_blockers": 0, "issues": []}
    columns: List[str] = []
    rows: List[Dict[str, str]] = []
    dictionary = {"variables": [], "id_column": None, "missing_tokens": []}
    dictionary_blocker = None

    if blocker is None:
        pii_profile = RDI._scan_csv(data_path, max_scan_rows=max_scan_rows)
        pii_issues = list(pii_profile.get("issues") or [])
        pii_scan = {
            "passed": not pii_issues,
            "n_blockers": len(pii_issues),
            "issues": pii_issues,
            "note": "Cleaning không chạy nếu còn PII.",
        }
        if pii_issues:
            blocker = "pii_detected_before_cleaning"

    if blocker is None:
        dictionary = _load_dictionary(Path(dictionary_path) if dictionary_path else None)
        dictionary_blocker = dictionary.get("blocker")
        if dictionary_blocker:
            blocker = str(dictionary_blocker)

    if blocker is None:
        try:
            columns, rows, _ = _read_csv(data_path)
        except UnicodeDecodeError:
            blocker = "decode_error: hãy xuất lại CSV UTF-8"
        if not columns:
            blocker = blocker or "empty_header"

    action_counts: Dict[str, int] = {}
    validation_issues: List[Dict[str, Any]] = []
    clean_dataset_path: Optional[Path] = None
    query_log_path: Optional[Path] = None
    plan_path: Optional[Path] = None
    output_sha256: Optional[str] = None

    if blocker is None:
        all_missing_tokens = sorted(
            set(DEFAULT_MISSING_TOKENS)
            | {_missing_key(token) for token in (dictionary.get("missing_tokens") or [])}
            | {_missing_key(token) for token in (missing_tokens or [])}
        )
        clean_rows: List[Dict[str, str]] = []
        for row in rows:
            clean_row: Dict[str, str] = {}
            for col in columns:
                cleaned, actions = _clean_cell(row.get(col), all_missing_tokens)
                clean_row[col] = cleaned
                for key, value in actions.items():
                    action_counts[key] = action_counts.get(key, 0) + value
            clean_rows.append(clean_row)

        rules = {
            RDI._normalize_header(rule["name"]): rule
            for rule in (dictionary.get("variables") or [])
            if isinstance(rule, dict) and rule.get("name")
        }
        cli_required = required_columns or []
        dict_required = [
            rule["name"] for rule in rules.values()
            if rule.get("required")
        ]
        merged_required = sorted(set(cli_required + dict_required))
        detected_id_column = _detect_id_column(
            columns, rules, id_column or dictionary.get("id_column"))
        validation_issues = _validate_rows(
            columns, clean_rows, rules, detected_id_column, merged_required)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            writer.writerows(clean_rows)
        clean_dataset_path = output_path
        output_sha256 = RDI._sha256_file(output_path)
        query_log_path = out_dir / "04_query_logs" / QUERY_LOG_NAME
        _write_query_log(query_log_path, validation_issues)
        plan_payload = {
            "kind": "research_dataset_cleaning_plan",
            "study": study_id,
            "created_at": cleaned_at,
            "dictionary": _safe_rel(Path(dictionary_path), out_dir) if dictionary_path else None,
            "id_column": detected_id_column,
            "required_columns": merged_required,
            "missing_tokens": all_missing_tokens,
            "safe_actions": [
                "trim_or_collapse_whitespace",
                "standardize_missing_token",
            ],
            "forbidden_actions": [
                "no_row_drop_without_protocol",
                "no_imputation",
                "no_range_fix_without_source_verification",
                "no_category_recode_without_query_resolution",
            ],
        }
        plan_path = _write_json(out_dir / "03_cleaning_scripts" / PLAN_NAME, plan_payload)

    open_query_count = len(validation_issues)
    status = (
        BLOCKED_STATUS if blocker
        else CLEAN_QUERY_STATUS if open_query_count
        else CLEAN_READY_STATUS
    )
    report: Dict[str, Any] = {
        "kind": "research_dataset_cleaning_report",
        "study": study_id,
        "status": status,
        "cleaned_at": cleaned_at,
        "source_filename": RDI._safe_source_filename(data_path),
        "source_sha256": RDI._sha256_file(data_path) if data_path.exists() else None,
        "clean_dataset_path": _safe_rel(clean_dataset_path, out_dir),
        "output_sha256": output_sha256,
        "query_log": _safe_rel(query_log_path, out_dir),
        "plan": _safe_rel(plan_path, out_dir),
        "row_count": len(rows),
        "column_count": len(columns),
        "pii_scan": pii_scan,
        "dictionary_loaded": bool(dictionary.get("variables")),
        "dictionary_blocker": dictionary_blocker,
        "safe_action_counts": action_counts,
        "open_query_count": open_query_count,
        "query_summary": {
            issue_type: sum(1 for item in validation_issues if item["type"] == issue_type)
            for issue_type in sorted({item["type"] for item in validation_issues})
        },
        "blocker": blocker,
        "ready_for_lock": status == CLEAN_READY_STATUS,
        "rules": [
            "Không sửa file nguồn.",
            "Không tự sửa giá trị lâm sàng/phương pháp mơ hồ.",
            "Không xóa dòng/biến nếu chưa có protocol hoặc query resolution.",
            "Query log phải không còn open trước khi khóa dữ liệu.",
            "Report/query log không lưu giá trị PII hoặc giá trị bất thường thô.",
        ],
    }
    report_path = _write_json(out_dir / REPORT_NAME, report)
    _update_meta(out_dir, report, report_path)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Làm sạch CSV nghiên cứu y khoa trên bản sao, có query log.")
    parser.add_argument("--study", required=True, help="Mã đề tài")
    parser.add_argument("--data", required=True, help="CSV đã khử định danh/pseudonymized")
    parser.add_argument("--dictionary", default=None, help="Data dictionary JSON/CSV tùy chọn")
    parser.add_argument("--output", default=None, help="Đường dẫn df_clean.csv tùy chọn")
    parser.add_argument("--id-column", default=None, help="Cột ID nghiên cứu để kiểm trùng")
    parser.add_argument("--required-cols", default="", help="Danh sách cột bắt buộc, ngăn cách dấu phẩy")
    parser.add_argument("--missing-tokens", default="", help="Mã missing bổ sung, ngăn cách dấu phẩy")
    parser.add_argument("--max-scan-rows", type=int, default=5000)
    args = parser.parse_args()

    report = clean_dataset(
        args.study,
        Path(args.data),
        dictionary_path=Path(args.dictionary) if args.dictionary else None,
        output_path=Path(args.output) if args.output else None,
        id_column=args.id_column,
        required_columns=_split_list(args.required_cols),
        missing_tokens=_split_list(args.missing_tokens),
        max_scan_rows=args.max_scan_rows,
    )
    print(f"DATA_CLEANING: {report['status']}")
    print(
        "rows={rows} columns={cols} open_queries={queries}".format(
            rows=report["row_count"],
            cols=report["column_count"],
            queries=report["open_query_count"],
        )
    )
    if report["status"] == CLEAN_READY_STATUS:
        print(f"clean_dataset={report['clean_dataset_path']}")
        print(f"query_log={report['query_log']}")
        print("Tiếp theo: chạy lock_analysis_dataset.py với clean_dataset + query_log.")
        return 0
    if report["status"] == CLEAN_QUERY_STATUS:
        print(f"clean_dataset={report['clean_dataset_path']}")
        print(f"query_log={report['query_log']}")
        print("BLOCKED FOR LOCK: còn query mở; cần PI/data manager đối chiếu nguồn và đóng query.")
        return 2
    print(f"BLOCKED: {report.get('blocker')}; xem {REPORT_NAME}.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
