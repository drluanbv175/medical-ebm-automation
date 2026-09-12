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

# Windows: stdout mặc định cp1252 giết print() tiếng Việt — ép UTF-8 (chốt BH55/R4)
import sys as _sys_r4
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

for _s_r4 in (_sys_r4.stdout, _sys_r4.stderr):
    try:
        _s_r4.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

BASE = Path(__file__).resolve().parents[1]
TOOLS = BASE / "tools"
sys.path.insert(0, str(TOOLS))

import gate_contract as GC  # noqa: E402

SUPPORTED_SUFFIXES = {".csv"}
BLOCKED_STATUS = "BLOCKED_PII_OR_UNSAFE"
READY_STATUS = "READY_FOR_CLEANING_NOT_LOCKED"

PII_HEADER_EXACT = {
    "name", "full_name", "patient_name", "ho_ten", "ten_benh_nhan",
    "initials", "patient_initials", "ten_viet_tat",
    "phone", "mobile", "telephone", "email", "address", "dia_chi",
    "dob", "date_of_birth", "dateofbirth", "birth_date", "birthdate", "ngay_sinh",
    "cccd", "cmnd", "citizen_id", "national_id", "passport",
    "mrn", "medical_record_number", "hospital_number", "patient_id",
    "bhyt", "insurance_number", "health_insurance_number", "ssn",
}
PII_HEADER_CONTAINS = (
    "so_dien_thoai", "dien_thoai", "phone_number", "email_address",
    "home_address", "diachi", "ma_benh_an", "so_benh_an", "ma_y_te",
    "ngaysinh", "so_cmnd", "so_cccd", "ho_va_ten", "hoten", "ten_bn",
    "ma_benh_nhan", "ma_bn", "ma_hsba", "sdt",
)
# Vá 2026-07-16 (round audit đối kháng 3): PII_HEADER_EXACT/CONTAINS ở trên là danh sách
# CỐ ĐỊNH, bỏ sót các biến thể tên cột thực tế phổ biến (vd "phone_formatted", "cccd_so",
# "patient_phone"). Kiểm thêm theo TỪNG TOKEN (tách bởi "_") khớp CHÍNH XÁC — an toàn hơn
# substring vì không khớp nhầm từ tiếng Việt chứa chuỗi con trùng (vd "tuyen_giap" không có
# token nào == "ten").
PII_HEADER_TOKENS = {
    "phone", "cccd", "cmnd", "ten", "email", "dob", "mrn", "bhyt", "ssn",
    "address", "name", "sdt",
}
VALUE_PATTERNS = {
    "email": re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I),
    # THÊM 2026-09-04 (Workflow đối kháng đa-agent vòng 3, CRITICAL): NGÀY THÁNG.
    # HIPAA Safe Harbor liệt "mọi thành phần ngày tháng gắn với một cá nhân — trừ
    # năm — gồm ngày sinh, ngày nhập viện, ngày xuất viện" là ĐỊNH DANH TRỰC TIẾP,
    # nhưng VALUE_PATTERNS trước đây KHÔNG có mục nào cho ngày tháng. Hậu quả đo
    # được: một ô ghi chú tự do (header không gợi ý PII, vd cột "notes"/"ghi_chu")
    # chứa "BN sinh ngày 15/07/1980, nhập viện 03/03/2024" lọt qua CẢ _scan_csv()
    # (cổng tiếp nhận, BLOCKED_PII_OR_UNSAFE lẽ ra phải bật) LẪN _redact_value() —
    # deidentify_research_dataset.py VÀ pseudonymize_research_dataset.py CÙNG dùng
    # chung dict này (RDI.VALUE_PATTERNS) — khiến báo cáo khử định danh khẳng định
    # SAI `output_pii_scan.passed: true` trong khi ngày sinh vẫn còn nguyên trong
    # file xuất ra. CỐ Ý RỘNG hơn `_DOB` của app/core/policy_engine.py (đòi nhãn
    # "dob"/"ngày sinh" đứng trước ngày): ở ĐÂY hậu quả một trận dương tính giả chỉ
    # là "ô bị chặn/redact để người xem lại tay" (không xoá âm thầm một phần văn
    # bản như policy_engine), nên bắt LUÔN mọi ngày dd/mm/yyyy (mọi dấu / - .) và
    # yyyy-mm-dd (ISO) có năm 19xx/20xx, không đòi nhãn đứng trước.
    "date": re.compile(
        r"(?<!\d)(?:\d{1,2}[/\-.]\d{1,2}[/\-.](?:19|20)\d{2}"
        r"|(?:19|20)\d{2}[/\-]\d{1,2}[/\-]\d{1,2})(?!\d)"
    ),
    # CCCD/CMND viết theo NHÓM 3 chữ số cách nhau bởi khoảng trắng/chấm/gạch (cách viết
    # phổ biến trên giấy tờ thật, vd "012 345 678 901") — trước đây chỉ bắt chuỗi LIỀN.
    # ĐẶT TRƯỚC phone_vn có chủ đích: một CCCD 12 số bắt đầu bằng "0" cũng "trông giống"
    # số điện thoại ở vài chữ số đầu — nếu phone_vn (khớp lỏng hơn, độ dài biến thiên) chạy
    # trước và redact một phần, phần CÒN LẠI của CCCD sẽ vỡ cấu trúc 3-3-3(-3) liền mạch mà
    # cccd_cmnd_grouped cần, để lọt phần đuôi PII chưa bị ẩn (đã tái hiện bằng test).
    "cccd_cmnd_grouped": re.compile(
        r"(?<!\d)\d{3}[\s.\-]\d{3}[\s.\-]\d{3}(?:[\s.\-]\d{3})?(?!\d)"
    ),
    "cccd_cmnd": re.compile(r"(?<!\d)(?:\d{9}|\d{12})(?!\d)"),
    # SĐT VN: cho phép khoảng trắng/chấm/gạch/NGOẶC ĐƠN xen giữa các chữ số (vd
    # "(090) 123 4567") — {0,3} vì có thể có NHIỀU ký tự phân cách liền nhau (")" + " ").
    "phone_vn": re.compile(r"(?<!\d)\(?(?:\+?84|0)\)?(?:[\s.\-()]{0,3}\d){8,10}(?!\d)"),
}


def _sanitize_study(study: str) -> str:
    return re.sub(r"[^\w\-]", "_", study.strip().replace(" ", "-"))


def _normalize_header(name: str) -> str:
    s = name.strip().lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.replace("đ", "d").replace("Đ", "D")
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


def _filename_has_pii_signal(name: str) -> bool:
    norm = _normalize_header(Path(name).stem)
    if _header_issue(norm):
        return True
    return any(pattern.search(name) for pattern in VALUE_PATTERNS.values())


def _safe_source_filename(path: Path) -> str:
    suffix = path.suffix.lower()
    if _filename_has_pii_signal(path.name):
        return f"[REDACTED_SOURCE_FILENAME]{suffix}"
    return path.name


def _header_issue(column: str) -> Optional[str]:
    norm = _normalize_header(column)
    if norm in PII_HEADER_EXACT:
        return f"header_pii:{norm}"
    if any(token in norm for token in PII_HEADER_CONTAINS):
        return f"header_pii:{norm}"
    if set(norm.split("_")) & PII_HEADER_TOKENS:
        return f"header_pii:{norm}"
    return None


def _scan_csv(path: Path, *, max_scan_rows: int = 5000,
              exempt_date_columns: frozenset = frozenset()) -> Dict[str, Any]:
    """Quét CSV tìm PII. `exempt_date_columns` (tên cột đã CHUẨN HOÁ qua
    `_normalize_header`) là NGOẠI LỆ CÓ CHỦ Ý, TẮT theo mặc định: chỉ bỏ qua mẫu
    "date" — vẫn quét đủ mọi mẫu khác (email/SĐT/CCCD) — cho đúng những cột mà một
    NGƯỜI GỌI đã tường minh khai là biến ngày lâm sàng cần giữ (vd `visit_date` đã
    khai `"type": "date"` trong data dictionary). Không truyền gì = hành vi CŨ,
    không đổi cho bất kỳ lời gọi nào chưa cập nhật.

    VÌ SAO CẦN (08/09/2026): mẫu "date" trong VALUE_PATTERNS (thêm 04/09, chặn
    ngày ẩn trong ô ghi chú tự do — đúng, phải giữ) áp dụng cho MỌI cột không phân
    biệt, nên một cột ngày khám đã khai kiểu "date" trong dictionary — dữ liệu
    NGHIÊN CỨU cần giữ, không phải PII rò rỉ — vẫn bị chặn y hệt PII thật. Tham số
    này KHÔNG áp cho `import_dataset()` khi gọi trực tiếp trên file THÔ (mặc định
    rỗng ở đó) — chỉ có tác dụng khi CALLER tường minh biết cột nào là ngày đã khai."""
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
                        col_is_exempt_date = _normalize_header(col) in exempt_date_columns
                        for label, pattern in VALUE_PATTERNS.items():
                            if label == "date" and col_is_exempt_date:
                                continue
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
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
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
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")


def import_dataset(study: str, data_path: Path, *,
                   exports_root: Optional[Path] = None,
                   max_scan_rows: int = 5000,
                   exempt_date_columns: frozenset = frozenset()) -> Dict[str, Any]:
    """Nhập 1 CSV đã khử định danh. Trả manifest máy-đọc-được.

    `exempt_date_columns`: xem docstring `_scan_csv`. RỖNG theo mặc định — file
    THÔ đi thẳng vào cổng này (không qua pseudonymize trước) vẫn bị quét NGHIÊM
    NGẶT như cũ; chỉ `pseudonymize_dataset(..., then_import=True)` mới truyền vào,
    vì CHỈ nơi đó mới biết cột nào đã được khai là biến ngày lâm sàng hợp lệ."""
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
        profile = _scan_csv(data_path, max_scan_rows=max_scan_rows,
                            exempt_date_columns=exempt_date_columns)
        issues = list(profile["issues"])

    query_log = out_dir / "04_query_logs" / "data_intake_query_log.csv"
    _write_query_log(query_log, issues)

    manifest: Dict[str, Any] = {
        "kind": "real_data_intake_manifest",
        "study": study_id,
        "status": BLOCKED_STATUS if issues else READY_STATUS,
        "imported_at": imported_at,
        "source_filename": _safe_source_filename(data_path),
        "source_filename_redacted": _safe_source_filename(data_path) != data_path.name,
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
            "Nếu bị chặn PII, chạy tools/deidentify_research_dataset.py để tạo bản khử định danh rồi nạp lại.",
            "Nếu cần tái định danh có kiểm soát, chạy "
            "tools/pseudonymize_research_dataset.py để tạo mã giả và bảng ánh xạ bảo vệ riêng.",
            "Bản raw trong 02_raw_readonly là chỉ đọc.",
            "Chỉ làm sạch trên bản sao bằng tools/clean_research_dataset.py hoặc script có query log.",
            "Không phân tích chính cho tới khi có lock memo và data_lock_date thật.",
        ],
        "remediation": {
            "deidentify_command": (
                f"python3 tools/deidentify_research_dataset.py --study {study_id} "
                "--data <file.csv> --then-import"
            ),
            "pseudonymize_command": (
                f"python3 tools/pseudonymize_research_dataset.py --study {study_id} "
                "--data <file.csv> --then-import"
            ),
            "cleaning_command_after_ready_intake": (
                f"python3 tools/clean_research_dataset.py --study {study_id} "
                "--data <raw_readonly.csv> --dictionary <data_dictionary.json>"
            ),
            "note": "Không đưa file còn PII vào exports/raw; chỉ nhập bản đã khử định danh.",
        },
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
        print("Tiếp theo: chạy tools/clean_research_dataset.py trên bản sao; chưa phân tích chính khi chưa khóa DB.")
        return 0
    print("BLOCKED: phát hiện nguy cơ PII/định dạng không an toàn; xem DATA_INTAKE_manifest.json.")
    print(
        "Gợi ý: chạy `python3 tools/deidentify_research_dataset.py --study "
        f"{args.study} --data {args.data} --then-import` để tạo bản khử định danh."
    )
    print(
        "Hoặc nếu protocol cần tái định danh có kiểm soát: `python3 "
        "tools/pseudonymize_research_dataset.py --study "
        f"{args.study} --data {args.data} --then-import`."
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
