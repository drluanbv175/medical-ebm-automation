#!/usr/bin/env python3
"""Làm sạch dữ liệu nghiên cứu y khoa trên bản sao, có query log kiểm toán.

Công cụ này nằm giữa intake/pseudonymization/de-identification và data lock:
- Không sửa file nguồn.
- Chặn nếu dataset còn PII.
- Tạo bản clean working copy.
- Chỉ tự động hóa các thao tác an toàn: trim whitespace, chuẩn hóa mã missing.
- Không tự sửa giá trị lâm sàng/phương pháp mơ hồ; chỉ tạo query log mở.
- Data lock sẽ tự chặn nếu query log còn open.
- Tôn trọng Branching Logic của từ điển REDCap (15/11/2026, N2) bằng ĐÚNG bộ đánh giá của công cụ nhập Excel
  (`nhap_lieu_excel.danh_gia_logic`): trường bị nhánh ẩn mà trống ⇒ không sinh query thiếu; bị ẩn mà có giá trị ⇒
  query `value_when_branch_hidden`; biểu thức không đánh giá được ⇒ giữ hành vi cũ + cảnh báo trong báo cáo.

Ví dụ:
  python3 tools/clean_research_dataset.py --study KKB-HAI-LONG-2026 \\
    --data exports/KKB-HAI-LONG-2026/02_raw_readonly/data.abc123.csv \\
    --dictionary exports/KKB-HAI-LONG-2026/data_dictionary.json
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys

# Windows: stdout mặc định cp1252 giết print() tiếng Việt — ép UTF-8 (chốt BH55/R4)
import sys as _sys_r4
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

for _s_r4 in (_sys_r4.stdout, _sys_r4.stderr):
    try:
        _s_r4.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

BASE = Path(__file__).resolve().parents[1]
TOOLS = BASE / "tools"
sys.path.insert(0, str(TOOLS))

import cong_song as CS  # noqa: E402
import gate_contract as GC  # noqa: E402
import import_real_dataset as RDI  # noqa: E402
import placeholder_contract as PC  # noqa: E402

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


def _first_declared(*values: Any) -> Any:
    """Trả giá trị ĐẦU TIÊN thực sự được khai báo (khác None và khác chuỗi rỗng),
    None nếu không giá trị nào. KHÔNG dùng `or` ở đây: với `or`, một ngưỡng min/max
    hợp lệ bằng số 0 (JSON int/float, vd biến nhị phân 0/1) là falsy trong Python nên
    bị coi như "chưa khai" và rơi xuống lựa chọn kế tiếp — mất NGƯỠNG THẬT một cách
    im lặng, không phải chỉ mất một giá trị hiển thị."""
    for value in values:
        if value is not None and value != "":
            return value
    return None


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
    for key in (
        "name",
        "variable",
        "variable_name",
        "variable_field_name",
        "field_name",
        "ten_bien",
    ):
        value = raw.get(key)
        if value:
            return str(value).strip()
    return None


def duong_dan_tu_dien_trong_bao_cao(dictionary_path: Optional[Path], out_dir: Path) -> Optional[str]:
    """Đường dẫn dictionary ghi vào báo cáo làm sạch: tương đối theo thư mục đề tài khi nằm trong đó (F7)."""
    if not dictionary_path:
        return None
    return _safe_rel(Path(dictionary_path).resolve(), Path(out_dir).resolve())


def _rules_cua_dong(raw: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Luật của MỘT dòng dictionary REDCap. Trường checkbox ⇒ thêm luật cho từng cột xuất `<biến>___<mã>` (0/1).

    VÁ 16/10/2026 (diễn tập C1a, F6): REDCap xuất trường checkbox thành nhiều cột `<biến>___<mã>`; bản cũ chỉ biết
    tên gốc nên mọi cột xuất bị coi là «undeclared_column» ⇒ query mở, chặn khoá dữ liệu thật có câu chọn nhiều
    đáp án.
    """
    rule = _normalise_rule(raw)
    if not rule:
        return []
    kieu = next((str(v).strip().lower() for k, v in raw.items()
                 if re.sub(r"[^a-z0-9]+", "", str(k).lower()) == "fieldtype"), "")
    if kieu != "checkbox":
        return [rule]
    # Cột con thừa hưởng Branching Logic của trường gốc (REDCap ẩn cả nhóm ô chọn cùng lúc — như nhap_lieu_excel);
    # `checkbox_of` đánh dấu cột con để ô «0» dưới nhánh ẩn KHÔNG bị coi là «có giá trị» (quy ước REDCap).
    con = [dict(rule, name=f"{rule['name']}___{ma}", type="category", allowed=["0", "1"], required=False,
                checkbox_of=rule["name"])
           for ma in rule.get("allowed") or [] if re.fullmatch(r"[A-Za-z0-9_-]+", str(ma))]
    return [rule, *con]


def _normalise_rule(raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    # REDCap dùng tiêu đề có khoảng trắng/dấu "/" (vd "Variable / Field Name").
    # Chuẩn hóa khóa trước khi đọc để data dictionary do G5 sinh ra thực sự dùng
    # được, thay vì bị đọc thành danh sách biến rỗng.
    # F16 (16/10/2026, diễn tập C1a): «Choices, Calculations, OR Slider Labels» chuẩn hoá thành
    # «choices__calculations__or_slider_labels» (hai gạch dưới) ⇒ không khớp khoá đọc bên dưới ⇒ danh sách mã hợp lệ của
    # MỌI câu chọn đáp án REDCap rỗng, không bắt được mã sai. Gộp gạch dưới liên tiếp.
    normalized = {
        re.sub(r"_+", "_", re.sub(
            r"[^a-z0-9_]+",
            "_",
            RDI._normalize_header(str(key)),
        )).strip("_"): value
        for key, value in raw.items()
    }
    name = _variable_name(normalized)
    if not name:
        return None
    allowed = normalized.get("allowed")
    if allowed is None:
        allowed = normalized.get("allowed_values")
    if allowed is None:
        allowed = normalized.get("choices")
    if allowed is None:
        allowed = normalized.get("choices_calculations_or_slider_labels")
    field_type = str(
        normalized.get("type")
        or normalized.get("data_type")
        or normalized.get("field_type")
        or "text"
    ).strip().lower()
    validation_type = str(
        normalized.get("text_validation_type_or_show_slider_number") or ""
    ).strip().lower()
    if field_type in {"radio", "dropdown", "checkbox", "yesno", "truefalse"}:
        data_type = "category"
    elif validation_type in {"number", "number_1dp", "number_2dp", "number_3dp"}:
        data_type = "number"
    elif validation_type == "integer":
        data_type = "integer"
    elif validation_type.startswith("date_"):
        data_type = "date"
    else:
        data_type = field_type
    allowed_values = _split_list(allowed)
    if data_type == "category":
        allowed_values = [
            item.split(",", 1)[0].strip()
            for item in allowed_values
            if item.split(",", 1)[0].strip()
        ]
        if field_type == "yesno" and not allowed_values:
            allowed_values = ["0", "1"]
        elif field_type == "truefalse" and not allowed_values:
            allowed_values = ["0", "1"]
    rule = {
        "name": name,
        "type": data_type,
        "required": _truthy(
            normalized.get("required")
            or normalized.get("required_field")
            or normalized.get("bat_buoc")
        ),
        "min": _first_declared(normalized.get("min"), normalized.get("text_validation_min")),
        "max": _first_declared(normalized.get("max"), normalized.get("text_validation_max")),
        "allowed": allowed_values,
        "is_id": _truthy(
            normalized.get("is_id")
            or normalized.get("identifier")
        ),
        "date_format": str(normalized.get("date_format") or "%Y-%m-%d").strip(),
        # N2 (15/11/2026): «Branching Logic (Show field only if...)» chuẩn hoá thành
        # «branching_logic_show_field_only_if»; tên cột API REDCap là «branching_logic». Bản cũ không đọc khoá này ⇒
        # mọi trường «chỉ hiện khi» bị kiểm «Required Field?» như luôn hiện.
        "branching": str(_first_declared(
            normalized.get("branching_logic_show_field_only_if"),
            normalized.get("branching_logic"),
            normalized.get("branching"),
        ) or "").strip(),
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
                    for rule in _rules_cua_dong(row)
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


MA_THIEU_TEN_FILE = "_ma-thieu-theo-bien.csv"


def _nap_ma_thieu_theo_bien(path: Path) -> Tuple[List[str], Dict[str, List[str]]]:
    """(mã cấp dự án, {cột: [mã]}) từ CSV `bien, ma, nhan` — `bien` = «*» là mã của MỌI cột. Thiếu cột/ô ⇒ ValueError
    (bộ làm sạch chặn, không âm thầm bỏ qua mã đã khai)."""
    path = Path(path)
    if not path.exists():
        raise ValueError(f"không có tệp {path.name}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        thieu = [c for c in ("bien", "ma") if c not in (reader.fieldnames or [])]
        if thieu:
            raise ValueError(f"thiếu cột {', '.join(thieu)}")
        chung: List[str] = []
        theo_cot: Dict[str, List[str]] = {}
        for i, r in enumerate(reader, start=2):
            bien, ma = (r.get("bien") or "").strip(), (r.get("ma") or "").strip()
            if not bien or not ma:
                raise ValueError(f"dòng {i} thiếu «bien» hoặc «ma»")
            (chung if bien == "*" else theo_cot.setdefault(bien, [])).append(ma)
    return chung, theo_cot


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


BO_DANH_GIA_NHANH = "nhap_lieu_excel.danh_gia_logic"


def _bo_danh_gia_nhanh() -> Tuple[Optional[Callable[[str, Dict[str, str]], bool]], Tuple[type, ...], Optional[str]]:
    """(hàm đánh giá, lớp lỗi «không hỗ trợ», lý do không nạp được) của bộ đánh giá Branching Logic DÙNG CHUNG.

    N2 (15/11/2026, giả lập RCT lần 2): bộ làm sạch từng bỏ qua Branching Logic ⇒ 170 query «thiếu bắt buộc» giả
    (34 người mất theo dõi × 5 trường «chỉ hiện khi theo dõi được») trong khi công cụ nhập Excel đọc đúng nhánh ⇒
    hai công cụ cùng dây chuyền mâu thuẫn. Dùng ĐÚNG `nhap_lieu_excel.danh_gia_logic` — KHÔNG viết bộ phân tích
    thứ hai (hai bộ sẽ lệch nhau theo thời gian). Nạp muộn (lazy) để lock/pseudonymize import mô-đun này không trả
    thêm chi phí. Nạp hỏng ⇒ fail-safe: mọi biểu thức coi là «không đánh giá được» (giữ hành vi cũ + cảnh báo),
    tuyệt đối không coi là «ẩn» (ẩn = bớt query)."""
    try:
        import nhap_lieu_excel as NLE  # noqa: PLC0415
    except Exception as exc:  # noqa: BLE001 — mọi lỗi nạp đều phải về hành vi cũ, không làm sập bộ làm sạch
        return None, (), f"không nạp được bộ đánh giá logic dùng chung ({BO_DANH_GIA_NHANH}): {type(exc).__name__}"
    return NLE.danh_gia_logic, (NLE.LogicKhongHo,), None


def _dong_cho_logic(row: Dict[str, Any], columns: List[str]) -> Dict[str, str]:
    """Giá trị một hàng để đánh giá Branching Logic: CHỈ gọt khoảng trắng, GIỮ NGUYÊN mã thiếu (BTR, 998…).

    Cùng góc nhìn với công cụ nhập Excel trên CÙNG tệp CSV (mã thiếu là chuỗi thật) ⇒ hai công cụ ra cùng trạng thái
    nhánh. Chiều an toàn: nếu quy mã thiếu về trống trước khi đánh giá, «[tuoi] >= 65» với tuoi=998 sẽ thành SAI ⇒
    ẩn ⇒ bớt query; giữ nguyên thì không ẩn thêm ngoài phép đánh giá chữ-như-chữ. Kèm bí danh tên cột chuẩn hoá
    (chữ thường, bỏ dấu) để tiêu đề viết hoa vẫn khớp «[ten_bien]»."""
    dong: Dict[str, str] = {}
    for col in columns:
        dong[col] = " ".join(str(row.get(col) or "").strip().split())
    for col in columns:
        dong.setdefault(RDI._normalize_header(col), dong[col])
    return dong


def _validate_rows(columns: List[str], rows: List[Dict[str, str]],
                   rules: Dict[str, Dict[str, Any]],
                   id_column: Optional[str],
                   required_columns: List[str],
                   *,
                   logic_rows: Optional[List[Dict[str, str]]] = None,
                   branching_stats: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Sinh query từ luật dictionary.

    logic_rows (N2, 15/11/2026): hàng dùng đánh giá Branching Logic (xem `_dong_cho_logic`); vắng ⇒ dùng `rows`.
    branching_stats: dict do người gọi truyền vào để nhận thống kê nhánh (trường có logic, số ô bắt buộc trống không
    sinh query vì nhánh ẩn, số query «có giá trị khi nhánh ẩn», trường không đánh giá được + lý do + số hàng)."""
    issues: List[Dict[str, Any]] = []
    normalised_columns = {RDI._normalize_header(col): col for col in columns}
    thong_ke: Dict[str, Any] = branching_stats if branching_stats is not None else {}
    thong_ke.setdefault("fields_with_logic", [])
    thong_ke.setdefault("required_missing_suppressed", 0)
    thong_ke.setdefault("value_when_hidden", 0)
    thong_ke.setdefault("khong_danh_gia_duoc", {})
    co_logic = any(str(r.get("branching") or "").strip() for r in rules.values())
    danh_gia, loi_khong_ho, ly_do_khong_nap = _bo_danh_gia_nhanh() if co_logic else (None, (), None)

    # VÁ 04/10/2026 (soát từng cổng, G5-03): cột KHÔNG có trong dictionary từng bị bỏ qua im lặng («if not rule:
    # continue») ⇒ không luật range/category nào được áp mà bộ dữ liệu vẫn sẵn sàng khoá (tuoi_nam=450 lọt vì
    # dictionary khai «age»). Nay mỗi cột ngoài dictionary (trừ cột ID) là MỘT query «undeclared_column» — chặn
    # ready_for_lock tới khi khai biến vào dictionary (hoặc bỏ cột). Không có dictionary (rules rỗng) thì không phán.
    if rules:
        for col in columns:
            if col == id_column or RDI._normalize_header(col) in rules:
                continue
            issues.append(_issue(
                "undeclared_column",
                col,
                None,
                "Cột không có trong data dictionary — không có luật kiểm; khai biến (loại/phạm vi) hoặc bỏ cột.",
            ))

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

        logic_row = logic_rows[row_idx - 1] if logic_rows is not None else row
        for col in columns:
            value = str(row.get(col) or "")
            rule = rules.get(RDI._normalize_header(col))
            if not rule:
                continue
            # N2: trạng thái nhánh — True (hiện / không có logic), False (ẩn), None (không đánh giá được ⇒ hành vi cũ).
            hien_thi: Optional[bool] = True
            bieu_thuc = str(rule.get("branching") or "").strip()
            if bieu_thuc and col != id_column:  # REDCap: trường mã bản ghi không có nhánh (như nhap_lieu_excel)
                if col not in thong_ke["fields_with_logic"]:
                    thong_ke["fields_with_logic"].append(col)
                ly_do: Optional[str] = ly_do_khong_nap
                if danh_gia is not None:
                    try:
                        hien_thi = bool(danh_gia(bieu_thuc, logic_row))
                    except loi_khong_ho as exc:  # cú pháp ngoài tập con / biến vắng — thông điệp chỉ chứa biểu thức
                        ly_do = str(exc)
                    except Exception as exc:  # noqa: BLE001 — lỗi lạ của bộ đánh giá cũng về hành vi cũ
                        ly_do = f"lỗi bộ đánh giá: {type(exc).__name__}"
                if ly_do is not None:
                    # Fail-safe: không đánh giá được thì KHÔNG coi là ẩn (ẩn = bớt query) — giữ hành vi cũ.
                    hien_thi = None
                    muc = thong_ke["khong_danh_gia_duoc"].setdefault(col, {"ly_do": ly_do, "so_hang": 0})
                    muc["so_hang"] += 1
            if value == "":
                if rule.get("required"):
                    if hien_thi is False:
                        # Trường bị nhánh ẩn: trống là ĐÚNG (REDCap không cho nhập) — không phải dữ liệu thiếu.
                        thong_ke["required_missing_suppressed"] += 1
                        continue
                    issues.append(_issue(
                        "missing_required_value",
                        col,
                        row_idx,
                        "Biến bắt buộc bị thiếu; không tự điền.",
                    ))
                continue
            # Ô chọn nhiều trống được ghi 0 (quy ước REDCap) — «0» dưới nhánh ẩn KHÔNG phải «có giá trị».
            if hien_thi is False and not (rule.get("checkbox_of") and value == "0"):
                thong_ke["value_when_hidden"] += 1
                issues.append(_issue(
                    "value_when_branch_hidden",
                    col,
                    row_idx,
                    f"Có giá trị dù Branching Logic «{bieu_thuc}» đang ẩn trường này; đối chiếu phiếu gốc — "
                    "không tự xoá, không lưu giá trị.",
                ))

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


# VÁ 04/10/2026 (soát từng cổng, G5-04 — QĐ-9): mã đóng query hợp lệ. «da_sua» KHÔNG đóng được một query mà giá trị lỗi
# VẪN CÒN trong dữ liệu (sửa phải diễn ra ở nguồn rồi nạp lại — ALCOA+); nó chỉ ghi nhận query của lần làm sạch trước.
MA_DONG_QUERY = frozenset({"da_sua", "xac_nhan_dung", "khong_ap_dung_co_ly_do"})
TEN_TEP_GIAI_QUYET = "query_resolutions"


def _nap_giai_quyet(path: Optional[Path]) -> Tuple[Dict[Tuple[str, str, str], Dict[str, str]], List[str]]:
    """Đọc tệp giải quyết query (CSV hoặc JSON danh sách): mỗi dòng {issue_type, column, row, resolution, ly_do,
    owner_ref, resolved_at}. Trả ({(issue_type, column, row): dòng hợp lệ}, [lỗi không chứa giá trị dữ liệu])."""
    if path is None:
        return {}, []
    path = Path(path)
    loi: List[str] = []
    try:
        if path.suffix.lower() == ".json":
            raw = json.loads(path.read_text(encoding="utf-8"))
            dong = [r for r in (raw if isinstance(raw, list) else raw.get("resolutions", [])) if isinstance(r, dict)]
        else:
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                dong = list(csv.DictReader(handle))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, csv.Error, AttributeError):
        return {}, [f"khong_doc_duoc_tep_giai_quyet:{path.name}"]
    hop_le: Dict[Tuple[str, str, str], Dict[str, str]] = {}
    for i, r in enumerate(dong, 2):
        khoa = (str(r.get("issue_type") or "").strip(), str(r.get("column") or "").strip(),
                str(r.get("row") or "").strip())
        ma = str(r.get("resolution") or "").strip().lower()
        if ma not in MA_DONG_QUERY:
            loi.append(f"dong_{i}:ma_dong_khong_hop_le")
            continue
        if not PC.co_noi_dung_that(r.get("ly_do")):
            loi.append(f"dong_{i}:thieu_ly_do")
            continue
        if not PC.co_noi_dung_that(r.get("owner_ref")):
            loi.append(f"dong_{i}:thieu_owner_ref")
            continue
        if not CS.iso_khong_tuong_lai(r.get("resolved_at")):
            loi.append(f"dong_{i}:resolved_at_khong_phai_ISO_hoac_o_tuong_lai")
            continue
        hop_le[khoa] = {"resolution": ma, "ly_do": str(r.get("ly_do")).strip(),
                        "owner_ref": str(r.get("owner_ref")).strip(), "resolved_at": str(r.get("resolved_at")).strip()}
    return hop_le, loi


def _tom_tat_nhanh(stats: Dict[str, Any], row_count: int) -> Dict[str, Any]:
    """Khối `branching_logic` của báo cáo làm sạch — không chứa giá trị dữ liệu (lý do chỉ trích biểu thức từ điển)."""
    khong = dict(stats.get("khong_danh_gia_duoc") or {})
    return {
        "evaluator": BO_DANH_GIA_NHANH,
        "fields_with_logic": list(stats.get("fields_with_logic") or []),
        "required_missing_suppressed": int(stats.get("required_missing_suppressed") or 0),
        "value_when_hidden_queries": int(stats.get("value_when_hidden") or 0),
        "khong_danh_gia_duoc": khong,
        "canh_bao": [
            f"{col}: Branching Logic không đánh giá được ở {muc['so_hang']}/{row_count} hàng ({muc['ly_do']}) — giữ "
            "hành vi cũ: trường bắt buộc trống vẫn sinh query, không kiểm «có giá trị khi nhánh ẩn»."
            for col, muc in khong.items()
        ],
    }


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
                "resolution": item.get("resolution") or "verify against source/CRF; do not guess",
            })
    return path


def _write_json(path: Path, payload: Dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
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
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")


def clean_dataset(study: str, data_path: Path, *,
                  dictionary_path: Optional[Path] = None,
                  output_path: Optional[Path] = None,
                  exports_root: Optional[Path] = None,
                  id_column: Optional[str] = None,
                  required_columns: Optional[List[str]] = None,
                  missing_tokens: Optional[List[str]] = None,
                  max_scan_rows: int = 5000,
                  ma_thieu_path: Optional[Path] = None,
                  query_resolutions_path: Optional[Path] = None) -> Dict[str, Any]:
    """Làm sạch an toàn 1 CSV đã khử định danh/pseudonymized.

    query_resolutions_path (VÁ 04/10/2026, G5-04): tệp giải quyết query (xem _nap_giai_quyet). Trước đây KHÔNG có đường
    đóng query hợp lệ: sửa tay query log làm lệch băm (G5-AUTO-07/08 BLOCK), chạy lại thì query mở lại — giá trị cực
    trị đã xác minh với nguồn không bao giờ khoá được, lối thoát duy nhất là sửa dữ liệu hoặc nới dictionary SAU khi đã
    xem dữ liệu. Tệp được sao vào thư mục đề tài và gắn băm (query_resolutions_sha256)."""
    study_id = RDI._sanitize_study(study)
    data_path = Path(data_path)
    exports_root = Path(exports_root) if exports_root else BASE / "exports"
    out_dir = exports_root / study_id
    output_path = Path(output_path) if output_path else _default_output_path(
        study_id, data_path, exports_root)
    cleaned_at = datetime.now().isoformat(timespec="seconds")
    cleaned_at_utc = datetime.now(timezone.utc).isoformat()  # G5-02: so với mốc ký G2/G4 (UTC), đủ micro-giây

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

    # THỨ TỰ ĐẢO 08/09/2026: dictionary được nạp TRƯỚC quét PII (cũ: nạp SAU, khi
    # quét PII đã chặn xong). Lý do: mẫu PII "date" (RDI.VALUE_PATTERNS, thêm
    # 04/09) áp cho MỌI cột không phân biệt — kể cả cột chính dictionary này khai
    # `"type": "date"` (biến ngày lâm sàng NGHIÊN CỨU CẦN GIỮ, vd ngày khám, khác
    # hẳn ngày lẫn trong ghi chú tự do mà mẫu đó sinh ra để bắt). Trước bản vá,
    # dictionary_path TỰ NÓ đã có sẵn trong tham số hàm này — chỉ là bị nạp SAU
    # bước cần nó, nên không bao giờ có cơ hội dùng tới. Không đổi hành vi khi
    # `dictionary_path=None` (mặc định của mọi caller hiện có): dictionary rỗng,
    # date_columns rỗng, quét PII giống hệt trước.
    if blocker is None:
        dictionary = _load_dictionary(Path(dictionary_path) if dictionary_path else None)
        dictionary_blocker = dictionary.get("blocker")
        if dictionary_blocker:
            blocker = str(dictionary_blocker)

    date_columns = frozenset(
        RDI._normalize_header(str(rule["name"]))
        for rule in (dictionary.get("variables") or [])
        if isinstance(rule, dict) and rule.get("type") == "date" and rule.get("name")
    )

    if blocker is None:
        pii_profile = RDI._scan_csv(data_path, max_scan_rows=max_scan_rows,
                                    exempt_date_columns=date_columns)
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
        try:
            columns, rows, _ = _read_csv(data_path)
        except UnicodeDecodeError:
            blocker = "decode_error: hãy xuất lại CSV UTF-8"
        if not columns:
            blocker = blocker or "empty_header"

    action_counts: Dict[str, int] = {}
    validation_issues: List[Dict[str, Any]] = []
    branching_stats: Dict[str, Any] = {}
    loi_giai_quyet: List[str] = []
    clean_dataset_path: Optional[Path] = None
    query_log_path: Optional[Path] = None
    plan_path: Optional[Path] = None
    output_sha256: Optional[str] = None
    query_log_sha256: Optional[str] = None

    # 18/10/2026 (hội đồng G3 C1a): mã thiếu THEO TỪNG BIẾN (`_ma-thieu-theo-bien.csv`; «*» = cấp dự án). Trước đây chỉ
    # có --missing-tokens TOÀN CỤC: khai 998 cho kyvong_thoigiancho thì xoá luôn 998 phút hợp lệ của thoigian_cho.
    ma_thieu_file = Path(ma_thieu_path) if ma_thieu_path else out_dir / MA_THIEU_TEN_FILE
    ma_thieu_cot: Dict[str, List[str]] = {}
    ma_thieu_chung: List[str] = []
    if blocker is None and (ma_thieu_path or ma_thieu_file.exists()):
        try:
            ma_thieu_chung, ma_thieu_cot = _nap_ma_thieu_theo_bien(ma_thieu_file)
        except ValueError as e:
            blocker = f"ma_thieu_theo_bien_invalid: {e}"
    if blocker is None:
        all_missing_tokens = sorted(
            set(DEFAULT_MISSING_TOKENS)
            | {_missing_key(token) for token in (dictionary.get("missing_tokens") or [])}
            | {_missing_key(token) for token in (missing_tokens or [])}
            | {_missing_key(token) for token in ma_thieu_chung}
        )
        clean_rows: List[Dict[str, str]] = []
        for row in rows:
            clean_row: Dict[str, str] = {}
            for col in columns:
                cleaned, actions = _clean_cell(row.get(col), list(all_missing_tokens) + ma_thieu_cot.get(col, []))
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
            columns, clean_rows, rules, detected_id_column, merged_required,
            logic_rows=[_dong_cho_logic(row, columns) for row in rows],
            branching_stats=branching_stats)
        giai_quyet, loi_giai_quyet = _nap_giai_quyet(query_resolutions_path)
        for item in validation_issues:
            r = giai_quyet.get((item["type"], item.get("column") or "", str(item.get("row") or "")))
            if r and r["resolution"] != "da_sua":
                item["status"] = "closed"
                item["resolution"] = f"{r['resolution']}: {r['ly_do']} ({r['owner_ref']}, {r['resolved_at']})"
            elif r:
                loi_giai_quyet.append(f"da_sua_nhung_gia_tri_van_con:{item['type']}:{item.get('column') or ''}")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            writer.writerows(clean_rows)
        clean_dataset_path = output_path
        output_sha256 = RDI._sha256_file(output_path)
        query_log_path = out_dir / "04_query_logs" / QUERY_LOG_NAME
        _write_query_log(query_log_path, validation_issues)
        query_log_sha256 = RDI._sha256_file(query_log_path)
        plan_payload = {
            "kind": "research_dataset_cleaning_plan",
            "study": study_id,
            "created_at": cleaned_at,
            "dictionary": _safe_rel(Path(dictionary_path), out_dir) if dictionary_path else None,
            "dictionary_sha256": (
                RDI._sha256_file(Path(dictionary_path))
                if dictionary_path and Path(dictionary_path).exists()
                else None
            ),
            "id_column": detected_id_column,
            "required_columns": merged_required,
            "missing_tokens": all_missing_tokens,
            "missing_tokens_by_column": ma_thieu_cot,
            "ma_thieu_theo_bien_sha256": (RDI._sha256_file(ma_thieu_file) if ma_thieu_cot or ma_thieu_chung else None),
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

    open_query_count = sum(1 for item in validation_issues if item.get("status") != "closed")
    qr_rel: Optional[str] = None
    qr_sha: Optional[str] = None
    if query_resolutions_path is not None and Path(query_resolutions_path).exists() and blocker is None:
        dich = out_dir / "04_query_logs" / f"{TEN_TEP_GIAI_QUYET}{Path(query_resolutions_path).suffix.lower()}"
        dich.parent.mkdir(parents=True, exist_ok=True)
        if Path(query_resolutions_path).resolve() != dich.resolve():
            dich.write_bytes(Path(query_resolutions_path).read_bytes())
        qr_rel, qr_sha = _safe_rel(dich, out_dir), RDI._sha256_file(dich)
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
        "cleaned_at_utc": cleaned_at_utc,
        "source_filename": RDI._safe_source_filename(data_path),
        "source_sha256": RDI._sha256_file(data_path) if data_path.exists() else None,
        "clean_dataset_path": _safe_rel(clean_dataset_path, out_dir),
        "output_sha256": output_sha256,
        "query_log": _safe_rel(query_log_path, out_dir),
        "query_log_sha256": (
            query_log_sha256 if query_log_path and query_log_path.exists() else None
        ),
        "plan": _safe_rel(plan_path, out_dir),
        "row_count": len(rows),
        "column_count": len(columns),
        "pii_scan": pii_scan,
        "dictionary_loaded": bool(dictionary.get("variables")),
        # F7 (16/10/2026): đường dẫn tương đối theo gốc repo phải quy về tuyệt đối trước khi lấy tương đối theo thư mục
        # đề tài — bản cũ ghi nguyên văn nên lock_analysis_dataset (đọc tương đối theo thư mục đề tài) trượt provenance.
        "dictionary_path": duong_dan_tu_dien_trong_bao_cao(dictionary_path, out_dir),
        "dictionary_sha256": (
            RDI._sha256_file(Path(dictionary_path))
            if dictionary_path and Path(dictionary_path).exists()
            else None
        ),
        "dictionary_blocker": dictionary_blocker,
        # 18/10/2026: mã thiếu theo từng biến đã áp (bằng chứng cho khoá dữ liệu — tệp gắn băm).
        "missing_tokens_by_column": ma_thieu_cot,
        "ma_thieu_theo_bien_sha256": (RDI._sha256_file(ma_thieu_file) if ma_thieu_cot or ma_thieu_chung else None),
        "safe_action_counts": action_counts,
        "open_query_count": open_query_count,
        "query_resolutions": qr_rel,
        "query_resolutions_sha256": qr_sha,
        "query_resolution_errors": loi_giai_quyet,
        "n_query_resolved": sum(1 for item in validation_issues if item.get("status") == "closed"),
        "query_summary": {
            issue_type: sum(1 for item in validation_issues if item["type"] == issue_type)
            for issue_type in sorted({item["type"] for item in validation_issues})
        },
        # N2 (15/11/2026): bằng chứng kiểm toán vì sao số query «thiếu bắt buộc» ít hơn số ô trống.
        "branching_logic": _tom_tat_nhanh(branching_stats, len(rows)),
        "blocker": blocker,
        "ready_for_lock": status == CLEAN_READY_STATUS,
        "rules": [
            "Không sửa file nguồn.",
            "Không tự sửa giá trị lâm sàng/phương pháp mơ hồ.",
            "Không xóa dòng/biến nếu chưa có protocol hoặc query resolution.",
            "Query log phải không còn open trước khi khóa dữ liệu.",
            "Report/query log không lưu giá trị PII hoặc giá trị bất thường thô.",
            "Branching Logic đánh giá bằng bộ dùng chung với công cụ nhập Excel: nhánh ẩn + trống ⇒ không query thiếu; "
            "nhánh ẩn + có giá trị ⇒ query value_when_branch_hidden; không đánh giá được ⇒ giữ hành vi cũ + cảnh báo.",
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
    parser.add_argument("--ma-thieu-theo-bien", default=None,
                        help="CSV mã thiếu theo từng biến (bien, ma, nhan; bien=* là cấp dự án). Vắng ⇒ tự đọc "
                             "exports/<mã>/_ma-thieu-theo-bien.csv nếu có")
    parser.add_argument("--query-resolutions", default=None,
                        help="CSV/JSON giải quyết query: issue_type, column, row, resolution (da_sua/xac_nhan_dung/"
                             "khong_ap_dung_co_ly_do), ly_do, owner_ref (không PII), resolved_at (ISO) — G5-04")
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
        query_resolutions_path=Path(args.query_resolutions) if args.query_resolutions else None,
        ma_thieu_path=Path(args.ma_thieu_theo_bien) if args.ma_thieu_theo_bien else None,
    )
    print(f"DATA_CLEANING: {report['status']}")
    print(
        "rows={rows} columns={cols} open_queries={queries}".format(
            rows=report["row_count"],
            cols=report["column_count"],
            queries=report["open_query_count"],
        )
    )
    nhanh = report.get("branching_logic") or {}
    if nhanh.get("fields_with_logic"):
        print(
            f"Branching Logic: {len(nhanh['fields_with_logic'])} trường có logic; "
            f"{nhanh.get('required_missing_suppressed', 0)} ô bắt buộc trống do nhánh ẩn (không phải thiếu); "
            f"{nhanh.get('value_when_hidden_queries', 0)} query «có giá trị khi nhánh ẩn»."
        )
    for canh_bao in nhanh.get("canh_bao") or []:
        print(f"⚠ {canh_bao}")
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
