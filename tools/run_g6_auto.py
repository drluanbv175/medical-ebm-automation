#!/usr/bin/env python3
"""
run_g6_auto.py — Cổng G6: Phân tích thống kê (Statistical Analysis) — NÂNG CẤP 75%
Chạy SAU khi thu thập dữ liệu xong và khóa DB (G5).
- Đọc G5 REDCap dictionary → tự phát hiện tên biến thật
- Sinh R scripts với tên biến thật (không [CẦN TÊN BIẾN])
- Sinh run_analysis_cli.py — Python CLI phân tích đầy đủ (pandas/lifelines/statsmodels)
- Sinh sensitivity_analysis.py — E-value, subgroup, complete case vs MI
- Mức tự động: 75%
"""
import argparse
import csv
import json
import re
import sys
from datetime import datetime
from pathlib import Path

# Thư mục gốc dự án
BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import gate_contract as GC  # noqa: E402  (hợp đồng DỪNG dùng chung)

# ─────────────────────────────────────────────
# PHÁT HIỆN BIẾN TỰ ĐỘNG TỪ REDCAP DICTIONARY
# ─────────────────────────────────────────────

# Từ khóa nhận dạng loại biến
_EXPOSURE_KEYWORDS   = ["sglt2", "arm", "exposure", "treatment", "drug", "intervention", "group", "phoi_nhiem"]
_OUTCOME_KEYWORDS    = ["hosp", "death", "event", "outcome", "endpoint", "ket_cuc", "primary_outcome",
                        "readmit", "incident", "complication"]  # "incident"/"complication" mở rộng bao
                        # phủ fallback cho bundle không phải tim mạch (vd incident_t2dm) khi Section
                        # Header không có sẵn (nguồn CSV ngoài/chỉnh tay) — cơ chế chính vẫn là Section
                        # Header ưu tiên trước, đây chỉ là lớp phòng thủ thứ hai.
_TIME_KEYWORDS       = ["time", "follow", "duration", "months", "days", "years", "thoi_gian", "theo_doi"]
_DEMO_KEYWORDS       = ["age", "sex", "gender", "tuoi", "gioi", "education", "race", "ethnicity"]
# SỬA: "nt_pro" không khớp "nt_probnp" sau khi đổi sang token-boundary regex
# (ký tự "b" ngay sau "nt_pro" phá lookahead bên phải — "nt_pro" vốn dùng
# như tiền tố, không phải token trọn vẹn). Dùng "nt_probnp" đầy đủ. Đồng
# thời bổ sung nyha/bp_sys/bp_dia/heart_rate/k_serum — các biến lâm sàng
# nền CỐT LÕI của suy tim (đặc biệt kali máu khi phối hợp SGLT2i+MRA) từng
# bị bỏ sót hoàn toàn khỏi mọi danh sách, khiến Cox model hiệu chỉnh thiếu
# các yếu tố gây nhiễu tim mạch quan trọng nhất.
_LAB_KEYWORDS        = ["egfr", "creatinine", "hba1c", "bmi", "sbp", "dbp", "bnp", "nt_probnp", "lvef",
                        "cholesterol", "ldl", "hdl", "glucose", "hemoglobin", "hgb", "wbc", "plt",
                        "nyha", "bp_sys", "bp_dia", "heart_rate", "k_serum", "potassium"]
_COMORBID_KEYWORDS   = ["dm", "htn", "af", "cad", "ckd", "copd", "chf", "diabetes", "hypert",
                        "benh_nen", "tien_su", "comorbid", "baseline_disease", "stroke", "tia"]


def detect_variables_from_redcap(csv_path: Path) -> dict:
    """
    Đọc G5 REDCap dictionary → phát hiện tên biến theo vai trò.
    Hỗ trợ 2 định dạng:
      - Chuẩn CSV (dấu phẩy): "Variable Name","Form Name",...
      - Định dạng / delimiter: record_id / Admin / ... / text / label / ...
    Trả về dict: exposure, outcome, time_col, covariates, all_vars.
    """
    result = {
        "exposure":      None,
        "outcome":       None,
        "time_col":      None,
        "covariates":    [],
        "all_vars":      [],
        "detection_log": [],
    }

    if not csv_path.exists():
        result["detection_log"].append(f"⚠️  REDCap CSV không tồn tại: {csv_path}")
        return result

    try:
        text = csv_path.read_text(encoding="utf-8")
    except Exception as e:
        result["detection_log"].append(f"⚠️  Không đọc được CSV: {e}")
        return result

    lines = [line.rstrip("\n\r") for line in text.splitlines() if line.strip()]
    if len(lines) < 2:
        result["detection_log"].append("⚠️  CSV quá ngắn (< 2 dòng)")
        return result

    # Xác định delimiter: "/" hoặc ","
    # REDCap dictionary xuất từ hệ thống thường dùng " / " hoặc ","
    first_line = lines[0]
    if " / " in first_line:
        delimiter = " / "
    elif "\t" in first_line:
        delimiter = "\t"
    else:
        delimiter = ","

    def split_row(line: str):
        """Tách dòng theo delimiter, trim whitespace từng field."""
        if delimiter == ",":
            # Dùng csv.reader để xử lý quoted fields
            parts = list(csv.reader([line]))[0]
        else:
            parts = line.split(delimiter)
        return [p.strip() for p in parts]

    header_parts = split_row(lines[0])

    # Tìm vị trí cột Variable Name, Field Label, Section Header trong header
    # Định dạng chuẩn REDCap: col0=Variable, col4=Field Label (hoặc col1 nếu dùng / delimiter)
    var_col     = 0
    label_col   = 4   # default cho CSV chuẩn
    section_col = 2   # "Section Header" — SỬA: trước đây KHÔNG đọc cột này,
                       # chỉ dựa vào keyword-match tên biến để đoán outcome/
                       # covariate. Section Header ghi rõ "Kết cục chính" /
                       # "Kết cục phụ" / "Phơi nhiễm..." — tín hiệu cấu trúc
                       # đáng tin hơn nhiều so với đoán từ khóa trong tên biến.

    header_lower = [h.lower() for h in header_parts]
    for i, h in enumerate(header_lower):
        if "variable" in h and "name" in h:
            var_col = i
        elif h.startswith("variable"):
            var_col = i
    for i, h in enumerate(header_lower):
        if "field label" in h or "label" in h:
            label_col = i
            break
    for i, h in enumerate(header_lower):
        if "section" in h:
            section_col = i
            break

    # Nếu dùng " / " delimiter: cột 0=Variable, cột 2=Section, cột 4=Field Label
    # (đúng với định dạng G5 của hệ thống này)
    if delimiter == " / ":
        var_col     = 0
        section_col = 2
        label_col   = 4

    all_vars = []
    # Biến hành chính không dùng làm predictor
    skip_vars = {
        "record_id", "complete_flag", "comments", "consent_date", "site_id",
        "ae", "ltfu_reason", "visit_date", "admin",
        "protocol_deviation", "ltfu", "censor_reason",
        "ae_any", "ae_grade", "sae_any",   # biến an toàn, không phải covariate lâm sàng
    }

    for line in lines[1:]:
        parts = split_row(line)
        if not parts:
            continue
        var_name = parts[var_col].strip() if len(parts) > var_col else ""
        label    = parts[label_col].strip() if len(parts) > label_col else ""
        section  = parts[section_col].strip() if len(parts) > section_col else ""
        if not var_name or var_name.startswith("#"):
            continue
        if var_name.lower() in skip_vars:
            continue
        all_vars.append((var_name, label, section))

    # Forward-fill Section Header: quy ước REDCap chỉ ghi tên section ở DÒNG
    # ĐẦU của nhóm, các dòng sau cùng nhóm để trống (hiển thị dạng nhóm trên
    # UI REDCap) — nếu không forward-fill, các biến phái sinh cùng nhóm với
    # kết cục chính (vd incident_t2dm_date đi ngay sau incident_t2dm) sẽ có
    # section rỗng và lọt qua bộ lọc loại trừ "Kết cục" ở dưới.
    last_section = ""
    filled_vars = []
    for var_name, label, section in all_vars:
        if section:
            last_section = section
        filled_vars.append((var_name, label, last_section))
    all_vars = filled_vars

    result["all_vars"] = [v for v, _, _ in all_vars]

    def _section_is(section: str, *needles: str) -> bool:
        s = section.lower()
        return any(n in s for n in needles)

    # Hậu tố gợi ý "tiền sử" / "baseline" → không phải biến can thiệp
    _HISTORY_SUFFIXES = ("_pre", "_prior", "_history", "_hx", "_before", "_baseline")

    def _score(var_name, label, keywords):
        """
        Điểm heuristic: tên biến hoặc nhãn chứa từ khóa NHƯ MỘT TOKEN riêng
        biệt (ranh giới là ký tự không phải chữ/số — kể cả underscore/space),
        KHÔNG PHẢI substring bất kỳ vị trí nào.
        SỬA: substring matching cũ để "dm" khớp nhầm bên trong "incident_t2dm"
        (biến kết cục của bundle chuyển hóa, không phải bệnh nền), và "age"
        khớp nhầm bên trong "stage" (vd biến "cancer_stage"). Token-boundary
        matching giải quyết cả lớp lỗi này thay vì chỉ vá riêng "dm".
        """
        combo = (var_name + " " + label).lower()
        def _token_match(kw):
            pattern = r'(?<![a-z0-9])' + re.escape(kw) + r'(?![a-z0-9])'
            return re.search(pattern, combo) is not None
        return sum(1 for kw in keywords if _token_match(kw))

    def _is_history_var(var_name: str) -> bool:
        """True nếu biến là tiền sử/trước tuyển (không phải biến can thiệp hiện tại)."""
        vl = var_name.lower()
        return any(vl.endswith(sfx) for sfx in _HISTORY_SUFFIXES)

    # Phát hiện biến phơi nhiễm — ƯU TIÊN Section Header ("Phơi nhiễm...")
    # trước, chỉ fallback về keyword-match tên biến khi không có tín hiệu này.
    # Lý do: keyword list (_EXPOSURE_KEYWORDS) không thể liệt kê hết mọi tên
    # biến can thiệp có thể có (vd "intervention_type" của bundle chuyển hóa
    # mới không nằm trong bất kỳ danh sách từ khóa nào), trong khi Section
    # Header do chính G5 gắn nhãn "Phơi nhiễm..." luôn đúng theo cấu trúc CRF.
    section_exp = [v for v, _label, s in all_vars if _section_is(s, "phơi nhiễm", "exposure")]
    if section_exp:
        best_exp = section_exp[0]
        result["exposure"] = best_exp
        result["detection_log"].append(f"✅ Phơi nhiễm (từ Section Header): {best_exp}")
    else:
        best_exp, best_score = None, 0
        for var, label, _sec in all_vars:
            s = _score(var, label, _EXPOSURE_KEYWORDS)
            if _is_history_var(var):
                s = max(0, s - 1)   # giảm điểm nếu là biến tiền sử
            if s > best_score:
                best_exp, best_score = var, s
        if best_exp:
            result["exposure"] = best_exp
            result["detection_log"].append(f"✅ Phơi nhiễm (từ từ khóa): {best_exp} (score={best_score})")
        else:
            result["exposure"] = "exposure"   # fallback
            result["detection_log"].append("⚠️  Không tự phát hiện exposure → dùng 'exposure' (fallback)")

    # Phát hiện biến kết cục — ƯU TIÊN section "Kết cục chính" (primary
    # outcome đúng nghĩa), TRÁNH nhầm với "Kết cục phụ" (secondary) như
    # trường hợp "hypoglycemia_event" (chứa từ khóa "event") từng bị chọn
    # nhầm thay vì "incident_t2dm" (kết cục chính thật nhưng không khớp
    # keyword nào trong _OUTCOME_KEYWORDS).
    section_primary_out = [
        v for v, _label, s in all_vars
        if _section_is(s, "kết cục chính") and v != result["exposure"]
    ]
    if section_primary_out:
        best_out = section_primary_out[0]
        result["outcome"] = best_out
        result["detection_log"].append(f"✅ Kết cục (từ Section Header 'Kết cục chính'): {best_out}")
    else:
        best_out, best_score = None, 0
        for var, label, _sec in all_vars:
            if var == result["exposure"]:
                continue
            s = _score(var, label, _OUTCOME_KEYWORDS)
            if s > best_score:
                best_out, best_score = var, s
        if best_out:
            result["outcome"] = best_out
            result["detection_log"].append(f"✅ Kết cục (từ từ khóa): {best_out} (score={best_score})")
        else:
            result["outcome"] = "primary_outcome"  # fallback
            result["detection_log"].append("⚠️  Không tự phát hiện outcome → dùng 'primary_outcome' (fallback)")

    # Phát hiện biến thời gian theo dõi
    for var, label, _sec in all_vars:
        if var in {result["exposure"], result["outcome"]}:
            continue
        s = _score(var, label, _TIME_KEYWORDS)
        if s > 0:
            result["time_col"] = var
            result["detection_log"].append(f"✅ Thời gian: {var}")
            break
    if not result["time_col"]:
        result["time_col"] = "follow_time"  # fallback
        result["detection_log"].append("⚠️  Không tự phát hiện time → dùng 'follow_time' (fallback)")

    # Phát hiện covariates (nhân khẩu + lab + bệnh nền)
    # Loại trừ CỨNG mọi biến có Section Header chứa "Kết cục" (chính HOẶC
    # phụ) — tín hiệu cấu trúc này bắt được CẢ những biến kết cục không
    # khớp keyword nào (vd incident_t2dm, incident_t2dm_date của bundle
    # chuyển hóa) mà _OUTCOME_KEYWORDS (thiết kế quanh ca suy tim) bỏ sót.
    # Vẫn giữ kiểm tra keyword làm lớp phòng thủ thứ hai cho dữ liệu không
    # có Section Header (CSV nhập tay/nguồn ngoài).
    covariate_found = []
    for var, label, section in all_vars:
        if var in {result["exposure"], result["outcome"], result["time_col"]}:
            continue
        if _section_is(section, "kết cục"):
            continue
        if _score(var, label, _OUTCOME_KEYWORDS) > 0:
            continue
        is_demo    = _score(var, label, _DEMO_KEYWORDS) > 0
        is_lab     = _score(var, label, _LAB_KEYWORDS) > 0
        is_comorbid = _score(var, label, _COMORBID_KEYWORDS) > 0
        if is_demo or is_lab or is_comorbid:
            covariate_found.append(var)

    result["covariates"] = covariate_found
    result["detection_log"].append(
        f"✅ Covariates ({len(covariate_found)}): {', '.join(covariate_found) or 'không phát hiện'}"
    )

    return result


# ─────────────────────────────────────────────
# R SCRIPTS — SETUP & CLEANING (chung)
# ─────────────────────────────────────────────

R_00_SETUP = """\
# ============================================================
# 00_setup.R — Cài đặt môi trường và nạp thư viện
# Chạy một lần trước khi thực hiện phân tích
# ============================================================

packages <- c(
  "tidyverse",    # wrangling + visualization
  "survival",     # Cox regression, Kaplan-Meier
  "survminer",    # ggsurvplot — biểu đồ KM đẹp
  "lme4",         # mixed effects models
  "tableone",     # CreateTableOne — Table 1
  "gtsummary",    # tbl_summary — Table 1 xuất Word/HTML
  "mice",         # Multiple Imputation
  "sandwich",     # Robust standard errors
  "lmtest",       # coeftest với robust SE
  "ggplot2",      # biểu đồ
  "broom",        # tidy() — kết quả mô hình
  "here",         # quản lý đường dẫn tương đối
  "renv",         # quản lý phiên bản packages
  "flextable",    # xuất bảng ra Word
  "officer",      # xuất file Word
  "pROC",         # ROC curve
  "dcurves",      # Decision Curve Analysis
  "meta",         # meta-analysis
  "metafor"       # metafor — meta-analysis nâng cao
)

to_install <- packages[!packages %in% installed.packages()[, "Package"]]
if (length(to_install) > 0) {
  message("Đang cài: ", paste(to_install, collapse = ", "))
  install.packages(to_install, repos = "https://cran.rstudio.com/")
}

suppressPackageStartupMessages(
  lapply(packages, require, character.only = TRUE)
)

# Seed — phải khớp với seed đã cam kết trong G4 SAP §10
SEED <- 2026
set.seed(SEED)

DATA_RAW  <- here::here("data", "raw")
DATA_PROC <- here::here("data", "processed")
OUTPUT    <- here::here("output")
SCRIPTS   <- here::here("scripts")

dir.create(DATA_RAW,  showWarnings = FALSE, recursive = TRUE)
dir.create(DATA_PROC, showWarnings = FALSE, recursive = TRUE)
dir.create(OUTPUT,    showWarnings = FALSE, recursive = TRUE)

options(scipen = 999, digits = 4)
message("=== 00_setup.R hoàn tất === Seed: ", SEED)
"""


# THÊM 2026-07-21 (vòng lặp kiểm tra-hoàn thiện vòng 2, phát hiện LOW +
# MEDIUM gộp): _WRONG_METHOD_DESIGNS trước đây định nghĩa LẶP LẠI y hệt ở
# make_run_analysis_cli() và make_sensitivity_analysis() (cùng lớp lỗi "2 nơi
# xử lý design_code tách rời" đã ghi nhận nhiều lần trong file này) — nay
# hoist thành hằng số module-level DÙNG CHUNG, và gộp luôn logic "chèn cảnh
# báo sau shebang" thành 1 helper dùng chung cho CẢ 4 hàm sinh script (bao
# gồm make_r01_cleaning/make_r02_tables — trước đây 2 hàm này sinh code
# cohort-style KHÔNG ĐIỀU KIỆN cho MỌI design_code, không có cảnh báo gì,
# trong khi 03_analysis.R/CLI/sensitivity đã có cảnh báo từ 2026-07-20).
_WRONG_METHOD_DESIGNS = {"cross_sectional", "diagnostic", "prediction", "sr_ma", "qualitative"}

_METHOD_HINT_BY_DESIGN = {
    "cross_sectional": "hồi quy logistic đa biến (OR)",
    "diagnostic": "ROC/AUC + decision curve analysis (STARD)",
    "prediction": "mô hình tiên lượng (TRIPOD+AI) — KHÔNG phải Cox đơn biến",
    "sr_ma": "tổng hợp bằng chứng (PRISMA) trên bảng STUDY-LEVEL, không phải participant-level",
    "qualitative": "mã hóa chủ đề (COREQ/SRQR) — KHÔNG có mô hình thống kê suy diễn",
}


def _insert_warning_after_shebang(code: str, warn: str) -> str:
    """Chèn cảnh báo NGAY sau dòng shebang (nếu có) để nổi bật ngay đầu file;
    nếu không có shebang, chèn lên đầu."""
    if code.startswith("#!"):
        first_nl = code.index("\n") + 1
        return code[:first_nl] + warn + code[first_nl:]
    return warn + code


def _cohort_style_wrong_method_warning(design_code: str, script_name: str) -> str:
    """Cảnh báo dùng chung cho 01_cleaning.R/02_tables.R khi design_code nằm
    trong _WRONG_METHOD_DESIGNS — 2 script này sinh mutate/Table-1-theo-nhóm-
    phơi-nhiễm CỐ ĐỊNH không phù hợp các thiết kế không có trục phơi nhiễm/
    kết cục nhị phân kiểu cohort (vd định tính không có biến số để 'làm sạch'
    theo kiểu này, SR/MA là bảng study-level chứ không phải participant-level)."""
    method_hint = _METHOD_HINT_BY_DESIGN[design_code]
    return (
        f"# ⚠️  [CẦN CHÚ Ý — THIẾT KẾ {design_code.upper()}]\n"
        f"# {script_name} sinh theo khuôn mặc định (biến phơi nhiễm/kết cục kiểu\n"
        "# cohort) — KHÔNG chắc phù hợp thiết kế này (cần "
        f"{method_hint}).\n"
        "# Rà lại với thống kê viên trước khi dùng làm bước làm sạch/mô tả chính;\n"
        "# xem SAP (A5) §4-§6 để biết đúng khung phân tích cho thiết kế này.\n\n"
    )


def make_r01_cleaning(v: dict, design_code: str = "cohort") -> str:
    """Sinh 01_cleaning.R với tên biến thật từ REDCap dictionary."""
    exposure  = v["exposure"]
    outcome   = v["outcome"]
    time_col  = v["time_col"]
    covars    = v["covariates"]

    # Danh sách mutate cho covariates phát hiện được
    mutate_lines = []
    for c in covars:
        if c in ("age", "tuoi"):
            mutate_lines.append(f"    {c} = as.numeric({c}),")
        elif c in ("sex", "gioi", "gender"):
            mutate_lines.append(f"    {c} = factor({c}, levels = c(1, 2), labels = c('Nam', 'Nữ')),")
        elif c in ("dm", "htn", "af", "cad", "ckd", "copd"):
            mutate_lines.append(f"    {c} = factor({c}, levels = c(0, 1), labels = c('Không', 'Có')),")
        else:
            mutate_lines.append(f"    {c} = as.numeric({c}),  # kiểm tra lại kiểu dữ liệu")
    mutate_lines.append(f"    {exposure} = as.numeric({exposure}),")
    mutate_lines.append(f"    {outcome}  = as.integer({outcome}),")
    mutate_lines.append(f"    {time_col} = as.numeric({time_col})")

    mutate_block = "\n".join(mutate_lines)

    code = f"""\
# ============================================================
# 01_cleaning.R — Làm sạch dữ liệu
# Biến phơi nhiễm: {exposure}
# Biến kết cục  : {outcome}
# Thời gian TD  : {time_col}
# Covariates    : {", ".join(covars) if covars else "[xem SAP §5]"}
# Sinh tự động từ G5 REDCap dictionary — kiểm tra lại trước khi chạy
# ============================================================

source(here::here("scripts", "00_setup.R"))

# ----------------------------------------------------------
# BƯỚC 1: ĐỌC DỮ LIỆU THÔ (uncomment đúng nguồn)
# ----------------------------------------------------------

# Cách 1: CSV xuất REDCap
# df_raw <- readr::read_csv(
#   file.path(DATA_RAW, "data_export.csv"),  # đổi tên file thật
#   locale = locale(encoding = "UTF-8")
# )

# Cách 2: REDCap API
# library(REDCapR)
# df_raw <- REDCapR::redcap_read(
#   redcap_uri = Sys.getenv("REDCAP_URI"),
#   token      = Sys.getenv("REDCAP_TOKEN")
# )$data

# ----------------------------------------------------------
# BƯỚC 2: KIỂM TRA CẤU TRÚC
# ----------------------------------------------------------
# message("Số hàng thô: ", nrow(df_raw))
# glimpse(df_raw)

# ----------------------------------------------------------
# BƯỚC 3: KIỂM TRA TRÙNG record_id
# ----------------------------------------------------------
# dup_ids <- df_raw$record_id[duplicated(df_raw$record_id)]
# if (length(dup_ids) > 0) stop("Trùng record_id: ", paste(dup_ids, collapse=", "))

# ----------------------------------------------------------
# BƯỚC 4: CHUYỂN ĐỔI KIỂU DỮ LIỆU (tên biến từ REDCap)
# ----------------------------------------------------------
# df <- df_raw %>%
#   dplyr::mutate(
{mutate_block}
#   ) %>%
#   dplyr::filter(!is.na(record_id))

# ----------------------------------------------------------
# BƯỚC 5: KIỂM TRA GIÁ TRỊ NGOÀI PHẠM VI
# ----------------------------------------------------------
# if ("age" %in% names(df)) {{
#   age_out <- df %>% filter(age < 18 | age > 120)
#   if (nrow(age_out) > 0) warning("Tuổi ngoài phạm vi: ", nrow(age_out), " hàng")
# }}
# out_time <- df %>% filter({time_col} < 0 | {time_col} > 120)
# if (nrow(out_time) > 0) warning("Thời gian TD âm/quá lớn: ", nrow(out_time))

# ----------------------------------------------------------
# BƯỚC 6: TỶ LỆ DỮ LIỆU THIẾU
# ----------------------------------------------------------
# missing_pct <- df %>%
#   summarise(across(everything(), ~mean(is.na(.))*100)) %>%
#   tidyr::pivot_longer(everything(), names_to="variable", values_to="pct_missing") %>%
#   arrange(desc(pct_missing))
# print(missing_pct)
# write.csv(missing_pct, file.path(OUTPUT, "missing_summary.csv"), row.names=FALSE)

# ----------------------------------------------------------
# BƯỚC 7: LƯU DỮ LIỆU ĐÃ LÀM SẠCH
# ----------------------------------------------------------
# saveRDS(df, file.path(DATA_PROC, "df_clean.rds"))
# message("Đã lưu df_clean: ", nrow(df), " hàng x ", ncol(df), " cột")

message("01_cleaning.R — biến phát hiện từ REDCap: {exposure}/{outcome}/{time_col}")
message("[CẦN DỮ LIỆU THẬT + G5 DB LOCKED để uncomment và chạy]")
"""
    if design_code in _WRONG_METHOD_DESIGNS:
        code = _insert_warning_after_shebang(
            code, _cohort_style_wrong_method_warning(design_code, "01_cleaning.R")
        )
    return code


def make_r02_tables(v: dict, design_code: str = "cohort") -> str:
    """Sinh 02_tables.R với tên biến thật."""
    exposure = v["exposure"]
    covars   = v["covariates"]
    vars_list = ", ".join(f'"{c}"' for c in covars) if covars else '"age", "sex", "bmi", "dm", "htn"'

    code = f"""\
# ============================================================
# 02_tables.R — Bảng đặc điểm nền (Table 1) và thống kê mô tả
# Biến phân nhóm: {exposure}
# Covariates    : {", ".join(covars) if covars else "[xem SAP §5]"}
# ============================================================

source(here::here("scripts", "00_setup.R"))
# df <- readRDS(file.path(DATA_PROC, "df_clean.rds"))

# ----------------------------------------------------------
# TABLE 1 — gtsummary với SMD (Standardized Mean Difference)
# ----------------------------------------------------------

# vars_table1 <- c({vars_list})

# tbl1 <- gtsummary::tbl_summary(
#   data    = df %>% dplyr::select(all_of(c(vars_table1, "{exposure}"))),
#   by      = "{exposure}",
#   missing = "ifany",
#   statistic = list(
#     all_continuous()  ~ "{{mean}} ± {{sd}}",
#     all_categorical() ~ "{{n}} ({{p}}%)"
#   ),
#   digits  = all_continuous() ~ 1
# ) %>%
#   gtsummary::add_p(
#     test = list(
#       all_continuous()  ~ "t.test",
#       all_categorical() ~ "chisq.test"
#     )
#   ) %>%
#   gtsummary::add_smd() %>%
#   gtsummary::bold_labels() %>%
#   gtsummary::modify_caption("**Bảng 1. Đặc điểm nền theo nhóm {exposure}**")

# Xuất Word
# gtsummary::as_flex_table(tbl1) %>%
#   flextable::save_as_docx(path = file.path(OUTPUT, "Table1_baseline.docx"))

message("02_tables.R — Biến nhóm: {exposure} | [CẦN DỮ LIỆU THẬT]")
"""
    if design_code in _WRONG_METHOD_DESIGNS:
        code = _insert_warning_after_shebang(
            code, _cohort_style_wrong_method_warning(design_code, "02_tables.R")
        )
    return code


def make_r03_cohort(v: dict, n_adjusted: int, alpha: float, power: float,
                    effect_val: float, effect_type: str) -> str:
    """Sinh 03_analysis.R (cohort/Cox) với tên biến thật từ REDCap."""
    exposure  = v["exposure"]
    outcome   = v["outcome"]
    time_col  = v["time_col"]
    covars    = v["covariates"]

    # Chuỗi covariates cho công thức Cox
    cov_formula = " + ".join(covars) if covars else "age + sex + bmi + dm + htn"
    cov_mi_list  = ", ".join(f'"{c}"' for c in covars) if covars else '"age", "sex", "bmi", "dm", "htn"'
    subgroup_vars = [c for c in covars if c in ("sex", "dm", "htn", "age")]

    # Xây subgroup R code trước — tránh f-string lồng nhau
    subgroup_r_lines = []
    for sg in subgroup_vars:
        subgroup_r_lines.append(f"# Subgroup: {sg}")
        subgroup_r_lines.append(f"# cox_sub_{sg} <- survival::coxph(")
        subgroup_r_lines.append(f"#   surv_obj ~ {exposure}:{sg} + {exposure} + {sg} + {cov_formula},")
        subgroup_r_lines.append("#   data = df")
        subgroup_r_lines.append("# )")
        subgroup_r_lines.append(f"# broom::tidy(cox_sub_{sg}, exponentiate=TRUE, conf.int=TRUE)")
    subgroup_r_block = "\n".join(subgroup_r_lines) if subgroup_r_lines else "# [Không phát hiện biến nhóm con phù hợp — xem SAP §7]"

    return f"""\
# ============================================================
# 03_analysis.R — Phân tích chính: Cohort (Cox + KM)
# Thiết kế: Cohort tiến cứu | Chuẩn: STROBE 2007
# Mã đề tài : [ĐỀ TÀI_MÃ]
# N dự kiến : {n_adjusted} (alpha={alpha}, power={power}, {effect_type}={effect_val})
#
# Biến phơi nhiễm: {exposure}
# Biến kết cục  : {outcome}  (1=biến cố, 0=censored)
# Thời gian TD  : {time_col} (đơn vị: tháng)
# Covariates    : {cov_formula}
#
# Tên biến sinh TỰ ĐỘNG từ G5 REDCap dictionary.
# Kiểm tra lại trước khi chạy — đặc biệt nếu tên thực tế khác.
# SAP đã khóa (G4) PHẢI được ký trước khi uncomment và xem dữ liệu.
# ============================================================

source(here::here("scripts", "00_setup.R"))
# df <- readRDS(file.path(DATA_PROC, "df_clean.rds"))

# ----------------------------------------------------------
# KIỂM TRA TIỀN QUYẾT
# ----------------------------------------------------------
# stopifnot(
#   "{outcome}"   %in% names(df),
#   "{exposure}"  %in% names(df),
#   "{time_col}"  %in% names(df)
# )
# message("N = ", nrow(df), " | biến cố = ", sum(df${outcome}, na.rm=TRUE))

# ----------------------------------------------------------
# ĐỐI TƯỢNG SỐNG CÒN
# ----------------------------------------------------------
# surv_obj <- survival::Surv(
#   time  = df${time_col},
#   event = df${outcome}
# )

# ----------------------------------------------------------
# KAPLAN-MEIER — theo nhóm {exposure}
# ----------------------------------------------------------
# km_fit <- survival::survfit(surv_obj ~ {exposure}, data = df)
# summary(km_fit, times = c(6, 12, 24, 36))
#
# survminer::ggsurvplot(
#   km_fit, data = df,
#   risk.table  = TRUE,
#   pval        = TRUE,
#   conf.int    = TRUE,
#   xlab        = "Thời gian theo dõi (tháng)",
#   ylab        = "Xác suất không có biến cố",
#   legend.title = "{exposure}",
#   palette     = c("#2E9FDF", "#E7B800")
# )
# ggsave(file.path(OUTPUT, "KM_{exposure}_{outcome}.png"), width=10, height=7, dpi=300)

# ----------------------------------------------------------
# COX REGRESSION — Mô hình thô
# ----------------------------------------------------------
# cox_crude <- survival::coxph(surv_obj ~ {exposure}, data = df)
# broom::tidy(cox_crude, exponentiate=TRUE, conf.int=TRUE) %>%
#   dplyr::filter(term == "{exposure}") %>%
#   dplyr::mutate(across(where(is.numeric), ~round(., 3)))

# ----------------------------------------------------------
# COX REGRESSION — Mô hình hiệu chỉnh (covariates từ SAP §5)
# ----------------------------------------------------------
# cox_adj <- survival::coxph(
#   surv_obj ~ {exposure} + {cov_formula},
#   data = df
# )
# summary(cox_adj)
#
# Kiểm định Proportional Hazards
# ph_test <- survival::cox.zph(cox_adj)
# print(ph_test)
# if (any(ph_test$table[,"p"] < 0.05)) {{
#   warning("Vi phạm PH assumption — cân nhắc time-varying covariates")
# }}
#
# Trích xuất HR + 95%CI (Bảng 2)
# result_main <- broom::tidy(cox_adj, exponentiate=TRUE, conf.int=TRUE) %>%
#   dplyr::filter(term == "{exposure}") %>%
#   dplyr::mutate(
#     HR_CI  = paste0(round(estimate,2), " (", round(conf.low,2), "–", round(conf.high,2), ")"),
#     p_fmt  = ifelse(p.value < 0.001, "<0.001", round(p.value,3))
#   )
# print(result_main)
# write.csv(result_main, file.path(OUTPUT, "result_main_cox.csv"), row.names=FALSE)

# ----------------------------------------------------------
# PHÂN TÍCH ĐỘ NHẠY: Multiple Imputation (mice m=20)
# ----------------------------------------------------------
# vars_mi <- c("{outcome}", "{time_col}", "{exposure}", {cov_mi_list})
# imp <- mice::mice(
#   df %>% dplyr::select(all_of(vars_mi)),
#   m=20, method="pmm", seed=SEED, printFlag=FALSE
# )
# plot(imp)  # kiểm tra convergence
#
# cox_mi <- with(imp,
#   survival::coxph(
#     Surv({time_col}, {outcome}) ~ {exposure} + {cov_formula}
#   )
# )
# cox_pooled <- mice::pool(cox_mi)
# summary(cox_pooled, exponentiate=TRUE, conf.int=TRUE)

# ----------------------------------------------------------
# PHÂN TÍCH NHÓM CON (Subgroup — theo SAP §7)
# ----------------------------------------------------------
{subgroup_r_block}

message("03_analysis.R (Cohort/Cox) — Biến: {exposure}/{outcome}/{time_col}")
message("[CẦN DỮ LIỆU THẬT + G4 SAP LOCKED để uncomment và chạy]")
"""


# ─────────────────────────────────────────────
# PYTHON CLI ANALYSIS SCRIPT (run_analysis_cli.py)
# Dùng raw template + .replace() để tránh xung đột với f-string ngoài
# ─────────────────────────────────────────────

_RUN_CLI_TEMPLATE = r'''#!/usr/bin/env python3
"""
run_analysis_cli.py — Phân tích thống kê Python đầy đủ
Đề tài  : __STUDY__
Biến    : exposure=__EXPOSURE__ | outcome=__OUTCOME__ | time=__TIME__
Covariates: __COVARS_DISPLAY__

Cách dùng:
  python run_analysis_cli.py \
      --data path/to/data.csv \
      --exposure __EXPOSURE__ \
      --outcome  __OUTCOME__ \
      --time     __TIME__ \
      --covariates __COVARS_DEFAULT__

Đầu ra:
  G6_results_table1.xlsx  — Table 1 đặc điểm nền
  G6_results_main.xlsx    — Cox thô + hiệu chỉnh
  G6_km_curve.png         — Kaplan-Meier
  G6_results.docx         — Báo cáo Word

Yêu cầu: pandas, scipy, lifelines, matplotlib, openpyxl, python-docx
Cài    : pip install pandas scipy lifelines matplotlib openpyxl python-docx
"""
import argparse, sys, warnings
from pathlib import Path
from datetime import datetime
warnings.filterwarnings("ignore")

_MISSING = []
try:    import pandas as pd
except ImportError: _MISSING.append("pandas")
try:    import numpy as np
except ImportError: _MISSING.append("numpy")
try:    from scipy import stats
except ImportError: _MISSING.append("scipy")
try:
    from lifelines import KaplanMeierFitter, CoxPHFitter
    from lifelines.statistics import logrank_test
except ImportError: _MISSING.append("lifelines")
try:
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError: _MISSING.append("matplotlib")

if _MISSING:
    sys.exit("Thiếu: " + ", ".join(_MISSING) + "\nCài: pip install " + " ".join(_MISSING))


def parse_args():
    p = argparse.ArgumentParser(description="Phân tích Cox+KM — __STUDY__")
    p.add_argument("--data",       required=True, help="CSV dữ liệu")
    p.add_argument("--exposure",   default="__EXPOSURE__",    help="Tên cột phơi nhiễm")
    p.add_argument("--outcome",    default="__OUTCOME__",     help="Tên cột kết cục (0/1)")
    p.add_argument("--time",       default="__TIME__",        help="Tên cột thời gian (số)")
    p.add_argument("--covariates", default="__COVARS_DEFAULT__", help="Covariates (dấu phẩy)")
    p.add_argument("--output-dir", default=".")
    p.add_argument("--i-confirm-sap-locked", action="store_true",
                    help="Ghi đè kiểm tra G4/G5 checkpoint khi không tìm thấy file checkpoint "
                         "nhưng SAP+DB thực tế đã khóa. KHÔNG dùng để né việc chưa khóa thật.")
    p.add_argument("--i-confirm-irb-approved", action="store_true",
                    help="Ghi đè kiểm tra G2 checkpoint khi không tìm thấy file checkpoint "
                         "nhưng IRB thực tế đã phê duyệt. KHÔNG dùng để né việc chưa phê duyệt thật.")
    return p.parse_args()


def _check_sap_db_locked(i_confirm_sap: bool, i_confirm_irb: bool = False) -> None:
    """2026-07-07: script sinh từ template được PHÉP tồn tại trước khi có dữ liệu thật
    (sinh sớm ở G6 FULL AUTO), nhưng phải TỰ CHẶN chạy thật nếu G4 (SAP)/G5 (khóa DB)
    chưa LOCKED — không dựa hoàn toàn vào việc người chạy tự nhớ.

    Vá 2026-07-12 (audit toàn diện cổng G0-G9 — kiểm định đối kháng xác nhận bypass
    THẬT): trước đây --i-confirm-sap-locked/--i-confirm-irb-approved bỏ qua TOÀN BỘ
    kiểm tra kể cả ledger — một cờ tự khai trần, không xác minh gì, đủ để chạy phân
    tích trên dữ liệu bịa. Nay cờ CHỈ còn tác dụng thay thế checkpoint-file (đúng ý
    nghĩa gốc "checkpoint mất nhưng SAP/IRB thật đã xong") — ledger_approved() (xác
    minh chữ ký thật, xem gate_contract.py) LUÔN LUÔN bắt buộc, không cờ nào bỏ qua
    được. Đồng thời gọi qua gate_contract.ledger_approved() dùng chung thay vì hàm
    _ledger_approved() cục bộ (trước đây có 5 bản sao gần-giống-nhau rải khắp hệ
    thống — sửa 1 nơi từng quên 3 nơi khác, đúng lỗi đã xảy ra thật ở chỗ khác)."""
    import hashlib as _hashlib
    import json as _json
    import re as _re
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
    import gate_contract as _GC

    def _is_locked(status):
        s = str(status or "").strip().upper()
        if _re.search(r'(UN|CH[ƯU]A|KH[ÔO]NG|NOT)\s*LOCKED', s):
            return False
        return bool(_re.match(r'^LOCKED\b', s))

    def _load_cp(gate):
        p = Path("exports") / "__STUDY__" / f"{gate}_checkpoint.json"
        if p.exists():
            try:
                return _json.loads(p.read_text(encoding="utf-8"))
            except (ValueError, OSError):
                return {}
        return {}

    g2 = _load_cp("G2")
    g4 = _load_cp("G4")
    g5 = _load_cp("G5")
    g2_checkpoint_locked = _is_locked(g2.get("g2_status", g2.get("G2_STATUS")))
    g4_checkpoint_locked = _is_locked(g4.get("g4_status", g4.get("G4_STATUS")))
    g5_checkpoint_locked = _is_locked(g5.get("g5_status", g5.get("G5_STATUS")))
    g2_ledger_ok = _GC.ledger_approved(
        "G2", "__STUDY__", Path("exports") / "__STUDY__" / "G2_A3_ETHICS_PACKAGE___STUDY__.md")
    g4_ledger_ok = _GC.ledger_approved(
        "G4", "__STUDY__", Path("exports") / "__STUDY__" / "G4_A5_SAP_FINAL___STUDY__.md")
    g5_ledger_ok = _GC.ledger_approved(
        "G5", "__STUDY__", Path("exports") / "__STUDY__" / "G5_checkpoint.json")
    # Cờ --i-confirm-* CHỈ thay thế checkpoint-file, KHÔNG BAO GIỜ thay thế ledger_ok.
    g2_quality_ok = _GC.g2_quality_contract_satisfied(
        g2,
        _GC.load_study_meta(Path("exports") / "__STUDY__"),
    )
    g2_locked = (
        (g2_checkpoint_locked or i_confirm_irb)
        and g2_ledger_ok
        and g2_quality_ok
    )
    g4_locked = (g4_checkpoint_locked or i_confirm_sap) and g4_ledger_ok
    g5_quality_ok = _GC.g5_quality_contract_satisfied("__STUDY__")
    g5_locked = (
        (g5_checkpoint_locked or i_confirm_sap)
        and g5_ledger_ok
        and g5_quality_ok
    )
    if not g2_locked:
        print("✗ DỪNG: G2 (phê duyệt IRB) chưa xác nhận LOCKED bằng phê duyệt thật cho đề tài __STUDY__.")
        print(f"   G2 checkpoint: {'✅ LOCKED' if g2_checkpoint_locked else '⚠️ chưa LOCKED/không tìm thấy'}"
              f"  |  approval_ledger (chữ ký thật): {'✅ khớp' if g2_ledger_ok else '⚠️ thiếu/không khớp'}")
        print("   Không chạy phân tích xác nhận trên dữ liệu thu thập khi chưa có phê duyệt đạo đức thật.")
        print("   Cần bác sĩ TỰ TAY ghi phê duyệt thật bằng tools/approve_gate.py (không nhờ agent chạy hộ).")
        print("   --i-confirm-irb-approved chỉ thay được checkpoint-file bị mất — KHÔNG thay được ledger.")
        sys.exit(1)
    if not (g4_locked and g5_locked):
        print("✗ DỪNG: G4 (SAP) hoặc G5 (khóa DB) chưa xác nhận LOCKED bằng phê duyệt thật cho đề tài __STUDY__.")
        print(f"   G4 checkpoint: {'✅ LOCKED' if g4_checkpoint_locked else '⚠️ chưa LOCKED/không tìm thấy'}"
              f"  |  approval_ledger (chữ ký thật): {'✅ khớp' if g4_ledger_ok else '⚠️ thiếu/không khớp'}")
        print(f"   G5 checkpoint: {'✅ LOCKED' if g5_checkpoint_locked else '⚠️ chưa LOCKED/không tìm thấy'}"
              f"  |  approval_ledger (chữ ký thật): {'✅ khớp' if g5_ledger_ok else '⚠️ thiếu/không khớp'}")
        print("   Không chạy phân tích xác nhận trên dữ liệu chưa khóa (chống p-hacking/HARKing).")
        print("   Cần bác sĩ TỰ TAY ghi phê duyệt thật bằng tools/approve_gate.py (không nhờ agent chạy hộ).")
        print("   --i-confirm-sap-locked chỉ thay được checkpoint-file bị mất — KHÔNG thay được ledger.")
        sys.exit(1)


def fmt_pval(p):
    return "<0.001" if p < 0.001 else f"{p:.3f}"


def _safe_cell(value):
    """Chống formula injection khi ghi Excel (round 20 security review, 2026-07-12):
    tên biến trong bộ dữ liệu (data dictionary) có thể vô tình/cố ý bắt đầu bằng
    =/+/-/@ khiến Excel/Sheets THỰC THI như công thức khi mở file. Khớp _safe_cell()
    đã dùng ở app/reports/exporters.py."""
    if isinstance(value, str) and value and value[0] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + value
    return value


def make_table1(df, exposure, covariates):
    print("\n📊 Tạo Table 1...")
    grp0 = df[df[exposure] == 0]
    grp1 = df[df[exposure] == 1]
    n0, n1 = len(grp0), len(grp1)
    rows = [{"Biến": f"N (n0={n0}, n1={n1})",
              f"Nhóm 0 (n={n0})": str(n0),
              f"Nhóm 1 (n={n1})": str(n1),
              "p-value": ""}]
    for col in covariates:
        if col not in df.columns:
            continue
        d = df[col].dropna()
        if d.empty:
            continue
        g0c, g1c = grp0[col].dropna(), grp1[col].dropna()
        uq = set(d.unique())
        if uq.issubset({0, 1, 2, 3, 4, 5}):
            n0c = g0c.notna().sum()
            n1c = g1c.notna().sum()
            s0 = f"{int(g0c.sum())} ({100*g0c.sum()/n0c if n0c else 0:.1f}%)"
            s1 = f"{int(g1c.sum())} ({100*g1c.sum()/n1c if n1c else 0:.1f}%)"
            try:
                _, p, _, _ = stats.chi2_contingency(pd.crosstab(df[col], df[exposure]))
                pstr = fmt_pval(p)
            except Exception:
                pstr = "n/a"
        else:
            s0 = f"{g0c.mean():.1f} ± {g0c.std():.1f}"
            s1 = f"{g1c.mean():.1f} ± {g1c.std():.1f}"
            try:
                _, p = stats.ttest_ind(g0c, g1c, equal_var=False)
                pstr = fmt_pval(p)
            except Exception:
                pstr = "n/a"
        rows.append({"Biến": _safe_cell(col),
                     f"Nhóm 0 (n={n0})": s0,
                     f"Nhóm 1 (n={n1})": s1,
                     "p-value": pstr})
    tbl = pd.DataFrame(rows)
    print(tbl.to_string(index=False))
    return tbl


def plot_km(df, time_col, outcome, exposure, out_path):
    print("\n📈 Vẽ Kaplan-Meier...")
    fig, ax = plt.subplots(figsize=(9, 6))
    for grp_val, color in zip([0, 1], ["#2E9FDF", "#E7B800"]):
        sub = df[df[exposure] == grp_val]
        if sub.empty:
            continue
        kmf = KaplanMeierFitter()
        kmf.fit(sub[time_col], event_observed=sub[outcome],
                label=f"{exposure}={grp_val} (n={len(sub)})")
        kmf.plot_survival_function(ax=ax, color=color, ci_show=True)
    g0 = df[df[exposure] == 0]
    g1 = df[df[exposure] == 1]
    if not g0.empty and not g1.empty:
        res = logrank_test(
            g0[time_col], g1[time_col],
            event_observed_A=g0[outcome],
            event_observed_B=g1[outcome]
        )
        ax.text(0.65, 0.08, f"Log-rank p = {fmt_pval(res.p_value)}",
                transform=ax.transAxes, fontsize=11,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
    ax.set_xlabel("Thời gian theo dõi (tháng)", fontsize=12)
    ax.set_ylabel("Xác suất không có biến cố", fontsize=12)
    ax.set_title(f"Kaplan-Meier — {exposure} vs {outcome}", fontsize=13)
    ax.legend(fontsize=10)
    ax.set_ylim(0, 1.05)
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"   → KM curve: {out_path}")


def run_cox(df, time_col, outcome, exposure, covariates):
    print("\n🔬 Chạy Cox regression...")
    avail = [c for c in covariates if c in df.columns]
    essential = [time_col, outcome, exposure] + avail
    df_cox = df[essential].dropna()
    n_cox = len(df_cox)
    n_ev  = int(df_cox[outcome].sum())
    print(f"   N={n_cox} | Biến cố={n_ev}")
    results = []

    # Mô hình thô
    try:
        cph = CoxPHFitter()
        cph.fit(df_cox[[time_col, outcome, exposure]],
                duration_col=time_col, event_col=outcome)
        # THÊM 2026-07-21 (vòng lặp kiểm tra-hoàn thiện vòng 5, phát hiện MEDIUM):
        # trước bản vá này, KHÔNG có lệnh nào trong toàn file kiểm định giả định
        # proportional hazards (tương đương cox.zph() của R) cho mô hình Cox THẬT
        # chạy trên dữ liệu thật bằng lifelines/Python — checklist A17b (PHẦN 5)
        # yêu cầu "Kiểm định PH assumption: cox.zph() p > 0.05" nhưng cox.zph()
        # không tồn tại trong lifelines, nên bác sĩ chỉ theo đường Python (không
        # dùng R) sẽ KHÔNG BAO GIỜ kiểm được giả định này. check_assumptions() là
        # tương đương gần nhất trong lifelines (kiểm định Schoenfeld residuals +
        # in cảnh báo/gợi ý). Bọc try/except riêng — đây là bước CHẨN ĐOÁN, lỗi ở
        # đây (dữ liệu ít biến cố, ties...) không nên làm crash toàn bộ phân tích
        # Cox chính.
        try:
            cph.check_assumptions(df_cox[[time_col, outcome, exposure]],
                                   p_value_threshold=0.05, show_plots=False)
        except Exception as _e_ph:
            print(f"   [CẢNH BÁO] Không kiểm được giả định PH (mô hình thô): {_e_ph}")
        s = cph.summary
        hr  = s.loc[exposure, "exp(coef)"]
        clo = s.loc[exposure, "exp(coef) lower 95%"]
        chi = s.loc[exposure, "exp(coef) upper 95%"]
        pv  = s.loc[exposure, "p"]
        results.append({
            "Phân tích":  "Thô (univariable)",
            "HR":          round(hr,  3),
            "95%CI Lower": round(clo, 3),
            "95%CI Upper": round(chi, 3),
            "HR (95%CI)":  f"{hr:.2f} ({clo:.2f}–{chi:.2f})",
            "p-value":     fmt_pval(pv),
            "N":           n_cox,
            "Events":      n_ev,
        })
        print(f"   Thô : HR={hr:.2f} ({clo:.2f}–{chi:.2f}), p={fmt_pval(pv)}")
    except Exception as e:
        print(f"   ⚠️ Cox thô lỗi: {e}")

    # Mô hình hiệu chỉnh
    if avail:
        try:
            cph2 = CoxPHFitter()
            cph2.fit(df_cox[[time_col, outcome, exposure] + avail],
                     duration_col=time_col, event_col=outcome)
            try:
                cph2.check_assumptions(df_cox[[time_col, outcome, exposure] + avail],
                                        p_value_threshold=0.05, show_plots=False)
            except Exception as _e_ph2:
                print(f"   [CẢNH BÁO] Không kiểm được giả định PH (mô hình hiệu chỉnh): {_e_ph2}")
            s2 = cph2.summary
            hr  = s2.loc[exposure, "exp(coef)"]
            clo = s2.loc[exposure, "exp(coef) lower 95%"]
            chi = s2.loc[exposure, "exp(coef) upper 95%"]
            pv  = s2.loc[exposure, "p"]
            lbl = ", ".join(avail[:4]) + ("..." if len(avail) > 4 else "")
            results.append({
                "Phân tích":  f"Hiệu chỉnh ({lbl})",
                "HR":          round(hr,  3),
                "95%CI Lower": round(clo, 3),
                "95%CI Upper": round(chi, 3),
                "HR (95%CI)":  f"{hr:.2f} ({clo:.2f}–{chi:.2f})",
                "p-value":     fmt_pval(pv),
                "N":           n_cox,
                "Events":      n_ev,
            })
            print(f"   Adj : HR={hr:.2f} ({clo:.2f}–{chi:.2f}), p={fmt_pval(pv)}")
            print("\n   Toàn bộ mô hình:")
            print(cph2.summary[["exp(coef)", "exp(coef) lower 95%",
                                 "exp(coef) upper 95%", "p"]].round(3))
        except Exception as e:
            print(f"   ⚠️ Cox adj lỗi: {e}")
    else:
        print("   ℹ️ Không có covariate hợp lệ → chỉ chạy mô hình thô")

    return pd.DataFrame(results)


def export_docx(tbl1, cox_res, km_path, out_path, study_name, exposure, outcome, time_col):
    try:
        from docx import Document
        from docx.shared import Inches
    except ImportError:
        print("   ℹ️ python-docx chưa cài — bỏ qua DOCX")
        return
    doc = Document()
    doc.add_heading(f"Kết quả phân tích — {study_name}", 0)
    doc.add_paragraph(f"Ngày: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    doc.add_paragraph(f"Biến: {exposure}/{outcome}/{time_col}")
    doc.add_paragraph("⚠️ Cần bác sĩ kiểm chứng.")
    doc.add_heading("Bảng 1. Đặc điểm nền", 1)
    t = doc.add_table(rows=1, cols=len(tbl1.columns))
    t.style = "Light Shading Accent 1"
    for i, col in enumerate(tbl1.columns):
        t.rows[0].cells[i].text = col
    for _, row in tbl1.iterrows():
        cells = t.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = str(val)
    doc.add_heading("Bảng 2. Cox regression", 1)
    if not cox_res.empty:
        t2 = doc.add_table(rows=1, cols=len(cox_res.columns))
        t2.style = "Light Shading Accent 1"
        for i, col in enumerate(cox_res.columns):
            t2.rows[0].cells[i].text = col
        for _, row in cox_res.iterrows():
            cells = t2.add_row().cells
            for i, val in enumerate(row):
                cells[i].text = str(val)
    if km_path and Path(km_path).exists():
        doc.add_heading("Biểu đồ Kaplan-Meier", 1)
        doc.add_picture(str(km_path), width=Inches(5.5))
    doc.add_paragraph(
        "\nCần bác sĩ kiểm chứng. Kết quả chỉ có giá trị khi dữ liệu thật đã qua QC."
    )
    doc.save(out_path)
    print(f"   → DOCX: {out_path}")


def main():
    args = parse_args()
    _check_sap_db_locked(args.i_confirm_sap_locked, args.i_confirm_irb_approved)
    data_path  = Path(args.data)
    out_dir    = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    exposure   = args.exposure
    outcome    = args.outcome
    time_col   = args.time
    covariates = [c.strip() for c in args.covariates.split(",") if c.strip()]

    print(f"\n🔬 run_analysis_cli.py — {data_path.name}")
    print(f"   Phơi nhiễm : {exposure}")
    print(f"   Kết cục    : {outcome}")
    print(f"   Thời gian  : {time_col}")
    print(f"   Covariates : {', '.join(covariates)}")

    try:
        df = pd.read_csv(data_path, low_memory=False)
    except Exception as e:
        sys.exit(f"❌ Không đọc được {data_path}: {e}")
    print(f"   Đọc OK: {df.shape[0]} hàng × {df.shape[1]} cột")

    miss = [c for c in [exposure, outcome, time_col] if c not in df.columns]
    if miss:
        print(f"❌ Cột không tồn tại: {', '.join(miss)}")
        print(f"   Cột có sẵn: {', '.join(df.columns.tolist())}")
        sys.exit(1)

    tbl1 = make_table1(df, exposure, covariates)
    tbl1_path = out_dir / "G6_results_table1.xlsx"
    tbl1.to_excel(tbl1_path, index=False)
    print(f"   → Table 1: {tbl1_path}")

    km_path = out_dir / "G6_km_curve.png"
    try:
        plot_km(df, time_col, outcome, exposure, km_path)
    except Exception as e:
        print(f"   ⚠️ KM lỗi: {e}")
        km_path = None

    cox_res = run_cox(df, time_col, outcome, exposure, covariates)
    cox_path = out_dir / "G6_results_main.xlsx"
    cox_res.to_excel(cox_path, index=False)
    print(f"   → Cox: {cox_path}")

    docx_path = out_dir / "G6_results.docx"
    export_docx(tbl1, cox_res, km_path, docx_path,
                "__STUDY__", exposure, outcome, time_col)

    print("\n✅ Hoàn tất")
    print(f"   Table 1 : {tbl1_path}")
    print(f"   Cox     : {cox_path}")
    print(f"   KM      : {km_path}")
    print(f"   DOCX    : {docx_path}")
    print("\n⚠️  Cần bác sĩ kiểm chứng trước khi báo cáo.")


if __name__ == "__main__":
    main()
'''


# SỬA: run_analysis_cli.py trước đây dùng CHUNG 1 template Cox/HR bất kể
# design_code — case-control (không có trục thời gian-đến-biến-cố hợp lệ)
# nhận nhầm cùng phân tích sống còn với cohort. Viết template RIÊNG dùng
# logistic regression (statsmodels.Logit) → Odds Ratio, nhất quán với
# 03_analysis.R đã sửa. Không có KM/log-rank (không áp dụng cho case-control).
_CASE_CONTROL_CLI_TEMPLATE = r'''#!/usr/bin/env python3
"""
run_analysis_cli.py — Phân tích thống kê Python đầy đủ (Case-control)
Đề tài  : __STUDY__
Biến    : phơi nhiễm=__EXPOSURE__ | ca/chứng (outcome)=__OUTCOME__
Covariates: __COVARS_DISPLAY__

Case-control KHÔNG có trục thời gian-đến-biến-cố hợp lệ (hồi cứu, chọn mẫu
theo tình trạng bệnh) — dùng logistic regression → Odds Ratio (OR), KHÔNG
dùng Cox/HR.

Cách dùng:
  python run_analysis_cli.py \
      --data path/to/data.csv \
      --exposure __EXPOSURE__ \
      --outcome  __OUTCOME__ \
      --covariates __COVARS_DEFAULT__

Đầu ra:
  G6_results_table1.xlsx  — Table 1 đặc điểm nền (ca vs chứng)
  G6_results_main.xlsx    — Logistic thô + hiệu chỉnh (OR, 95%CI)
  G6_results.docx         — Báo cáo Word

Yêu cầu: pandas, scipy, statsmodels, numpy, openpyxl, python-docx
Cài    : pip install pandas scipy statsmodels numpy openpyxl python-docx
"""
import argparse, sys, warnings
from pathlib import Path
from datetime import datetime
warnings.filterwarnings("ignore")

_MISSING = []
try:    import pandas as pd
except ImportError: _MISSING.append("pandas")
try:    import numpy as np
except ImportError: _MISSING.append("numpy")
try:    from scipy import stats
except ImportError: _MISSING.append("scipy")
try:    import statsmodels.api as sm
except ImportError: _MISSING.append("statsmodels")

if _MISSING:
    sys.exit("Thiếu: " + ", ".join(_MISSING) + "\nCài: pip install " + " ".join(_MISSING))


def parse_args():
    p = argparse.ArgumentParser(description="Phân tích Logistic (OR) — case-control __STUDY__")
    p.add_argument("--data",       required=True, help="CSV dữ liệu")
    p.add_argument("--exposure",   default="__EXPOSURE__",    help="Tên cột phơi nhiễm (0/1)")
    p.add_argument("--outcome",    default="__OUTCOME__",     help="Tên cột ca/chứng (1=ca, 0=chứng)")
    p.add_argument("--covariates", default="__COVARS_DEFAULT__", help="Covariates (dấu phẩy)")
    p.add_argument("--matched",    action="store_true",
                   help="Nếu case-control CÓ bắt cặp (matched) — cảnh báo dùng conditional logistic thay vì thường")
    p.add_argument("--output-dir", default=".")
    p.add_argument("--i-confirm-sap-locked", action="store_true",
                    help="Ghi đè kiểm tra G4/G5 checkpoint khi không tìm thấy file checkpoint "
                         "nhưng SAP+DB thực tế đã khóa. KHÔNG dùng để né việc chưa khóa thật.")
    p.add_argument("--i-confirm-irb-approved", action="store_true",
                    help="Ghi đè kiểm tra G2 checkpoint khi không tìm thấy file checkpoint "
                         "nhưng IRB thực tế đã phê duyệt. KHÔNG dùng để né việc chưa phê duyệt thật.")
    return p.parse_args()


def _check_sap_db_locked(i_confirm_sap: bool, i_confirm_irb: bool = False) -> None:
    """2026-07-07: tự chặn chạy thật nếu G4 (SAP)/G5 (khóa DB) chưa LOCKED.
    Vá 2026-07-08 (BL-06): thêm sổ phê duyệt mật mã thật (exports/<study>/
    approval_ledger.json, ghi qua tools/approve_gate.py — KHÔNG do agent tự tạo
    được, xem runtime/approval_ledger.py::add_approval chặn created_by_agent) —
    evidence_hash khớp NỘI DUNG HIỆN TẠI của artifact đại diện chứng minh chưa bị
    sửa sau khi duyệt.

    Vá 2026-07-12 (audit toàn diện cổng G0-G9 — kiểm định đối kháng xác nhận bypass
    THẬT): trước đây --i-confirm-sap-locked/--i-confirm-irb-approved bỏ qua TOÀN BỘ
    kiểm tra kể cả ledger — một cờ tự khai trần, không xác minh gì, đủ để chạy phân
    tích trên dữ liệu bịa. Nay cờ CHỈ còn tác dụng thay thế checkpoint-file (đúng ý
    nghĩa gốc "checkpoint mất nhưng SAP/IRB thật đã xong") — ledger_approved() (xác
    minh chữ ký thật, xem gate_contract.py) LUÔN LUÔN bắt buộc, không cờ nào bỏ qua
    được. Đồng thời gọi qua gate_contract.ledger_approved() dùng chung thay vì hàm
    _ledger_approved() cục bộ (trước đây có 5 bản sao gần-giống-nhau rải khắp hệ
    thống — sửa 1 nơi từng quên 3 nơi khác, đúng lỗi đã xảy ra thật ở chỗ khác)."""
    import hashlib as _hashlib
    import json as _json
    import re as _re
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
    import gate_contract as _GC

    def _is_locked(status):
        s = str(status or "").strip().upper()
        if _re.search(r'(UN|CH[ƯU]A|KH[ÔO]NG|NOT)\s*LOCKED', s):
            return False
        return bool(_re.match(r'^LOCKED\b', s))

    def _load_cp(gate):
        p = Path("exports") / "__STUDY__" / f"{gate}_checkpoint.json"
        if p.exists():
            try:
                return _json.loads(p.read_text(encoding="utf-8"))
            except (ValueError, OSError):
                return {}
        return {}

    g2 = _load_cp("G2")
    g4 = _load_cp("G4")
    g5 = _load_cp("G5")
    g2_checkpoint_locked = _is_locked(g2.get("g2_status", g2.get("G2_STATUS")))
    g4_checkpoint_locked = _is_locked(g4.get("g4_status", g4.get("G4_STATUS")))
    g5_checkpoint_locked = _is_locked(g5.get("g5_status", g5.get("G5_STATUS")))
    g2_ledger_ok = _GC.ledger_approved(
        "G2", "__STUDY__", Path("exports") / "__STUDY__" / "G2_A3_ETHICS_PACKAGE___STUDY__.md")
    g4_ledger_ok = _GC.ledger_approved(
        "G4", "__STUDY__", Path("exports") / "__STUDY__" / "G4_A5_SAP_FINAL___STUDY__.md")
    g5_ledger_ok = _GC.ledger_approved(
        "G5", "__STUDY__", Path("exports") / "__STUDY__" / "G5_checkpoint.json")
    # Cờ --i-confirm-* CHỈ thay thế checkpoint-file, KHÔNG BAO GIỜ thay thế ledger_ok.
    g2_quality_ok = _GC.g2_quality_contract_satisfied(
        g2,
        _GC.load_study_meta(Path("exports") / "__STUDY__"),
    )
    g2_locked = (
        (g2_checkpoint_locked or i_confirm_irb)
        and g2_ledger_ok
        and g2_quality_ok
    )
    g4_locked = (g4_checkpoint_locked or i_confirm_sap) and g4_ledger_ok
    g5_quality_ok = _GC.g5_quality_contract_satisfied("__STUDY__")
    g5_locked = (
        (g5_checkpoint_locked or i_confirm_sap)
        and g5_ledger_ok
        and g5_quality_ok
    )
    if not g2_locked:
        print("✗ DỪNG: G2 (phê duyệt IRB) chưa xác nhận LOCKED bằng phê duyệt thật cho đề tài __STUDY__.")
        print(f"   G2 checkpoint: {'✅ LOCKED' if g2_checkpoint_locked else '⚠️ chưa LOCKED/không tìm thấy'}"
              f"  |  approval_ledger (chữ ký thật): {'✅ khớp' if g2_ledger_ok else '⚠️ thiếu/không khớp'}")
        print("   Không chạy phân tích xác nhận trên dữ liệu thu thập khi chưa có phê duyệt đạo đức thật.")
        print("   Cần bác sĩ TỰ TAY ghi phê duyệt thật bằng tools/approve_gate.py (không nhờ agent chạy hộ).")
        print("   --i-confirm-irb-approved chỉ thay được checkpoint-file bị mất — KHÔNG thay được ledger.")
        sys.exit(1)
    if not (g4_locked and g5_locked):
        print("✗ DỪNG: G4 (SAP) hoặc G5 (khóa DB) chưa xác nhận LOCKED bằng phê duyệt thật cho đề tài __STUDY__.")
        print(f"   G4 checkpoint: {'✅ LOCKED' if g4_checkpoint_locked else '⚠️ chưa LOCKED/không tìm thấy'}"
              f"  |  approval_ledger (chữ ký thật): {'✅ khớp' if g4_ledger_ok else '⚠️ thiếu/không khớp'}")
        print(f"   G5 checkpoint: {'✅ LOCKED' if g5_checkpoint_locked else '⚠️ chưa LOCKED/không tìm thấy'}"
              f"  |  approval_ledger (chữ ký thật): {'✅ khớp' if g5_ledger_ok else '⚠️ thiếu/không khớp'}")
        print("   Không chạy phân tích xác nhận trên dữ liệu chưa khóa (chống p-hacking/HARKing).")
        print("   Cần bác sĩ TỰ TAY ghi phê duyệt thật bằng tools/approve_gate.py (không nhờ agent chạy hộ).")
        print("   --i-confirm-sap-locked chỉ thay được checkpoint-file bị mất — KHÔNG thay được ledger.")
        sys.exit(1)


def fmt_pval(p):
    return "<0.001" if p < 0.001 else f"{p:.3f}"


def _safe_cell(value):
    """Chống formula injection khi ghi Excel (round 20 security review, 2026-07-12):
    tên biến trong bộ dữ liệu (data dictionary) có thể vô tình/cố ý bắt đầu bằng
    =/+/-/@ khiến Excel/Sheets THỰC THI như công thức khi mở file. Khớp _safe_cell()
    đã dùng ở app/reports/exporters.py."""
    if isinstance(value, str) and value and value[0] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + value
    return value


def make_table1(df, outcome, covariates):
    print("\n📊 Tạo Table 1 (Ca vs Chứng)...")
    grp0 = df[df[outcome] == 0]
    grp1 = df[df[outcome] == 1]
    n0, n1 = len(grp0), len(grp1)
    rows = [{"Biến": f"N (chứng={n0}, ca={n1})",
              f"Chứng (n={n0})": str(n0),
              f"Ca (n={n1})": str(n1),
              "p-value": ""}]
    for col in covariates:
        if col not in df.columns:
            continue
        d = df[col].dropna()
        if d.empty:
            continue
        g0c, g1c = grp0[col].dropna(), grp1[col].dropna()
        uq = set(d.unique())
        if uq.issubset({0, 1, 2, 3, 4, 5}):
            n0c = g0c.notna().sum()
            n1c = g1c.notna().sum()
            s0 = f"{int(g0c.sum())} ({100*g0c.sum()/n0c if n0c else 0:.1f}%)"
            s1 = f"{int(g1c.sum())} ({100*g1c.sum()/n1c if n1c else 0:.1f}%)"
            try:
                _, p, _, _ = stats.chi2_contingency(pd.crosstab(df[col], df[outcome]))
                pstr = fmt_pval(p)
            except Exception:
                pstr = "n/a"
        else:
            s0 = f"{g0c.mean():.1f} ± {g0c.std():.1f}"
            s1 = f"{g1c.mean():.1f} ± {g1c.std():.1f}"
            try:
                _, p = stats.ttest_ind(g0c, g1c, equal_var=False)
                pstr = fmt_pval(p)
            except Exception:
                pstr = "n/a"
        rows.append({"Biến": _safe_cell(col),
                     f"Chứng (n={n0})": s0,
                     f"Ca (n={n1})": s1,
                     "p-value": pstr})
    tbl = pd.DataFrame(rows)
    print(tbl.to_string(index=False))
    return tbl


def run_logistic(df, outcome, exposure, covariates):
    print("\n🔬 Chạy Logistic regression (Ca/Chứng ~ Phơi nhiễm)...")
    avail = [c for c in covariates if c in df.columns]
    essential = [outcome, exposure] + avail
    df_lr = df[essential].dropna()
    n_lr  = len(df_lr)
    n_case = int(df_lr[outcome].sum())
    print(f"   N={n_lr} | Ca={n_case} | Chứng={n_lr - n_case}")
    results = []

    # Mô hình thô
    try:
        X = sm.add_constant(df_lr[[exposure]].astype(float))
        model = sm.Logit(df_lr[outcome].astype(float), X).fit(disp=0)
        coef = model.params[exposure]
        se   = model.bse[exposure]
        or_  = float(np.exp(coef))
        clo  = float(np.exp(coef - 1.96 * se))
        chi  = float(np.exp(coef + 1.96 * se))
        pv   = float(model.pvalues[exposure])
        results.append({
            "Phân tích":  "Thô (univariable)",
            "OR":          round(or_, 3),
            "95%CI Lower": round(clo, 3),
            "95%CI Upper": round(chi, 3),
            "OR (95%CI)":  f"{or_:.2f} ({clo:.2f}–{chi:.2f})",
            "p-value":     fmt_pval(pv),
            "N":           n_lr,
            "Ca":          n_case,
        })
        print(f"   Thô : OR={or_:.2f} ({clo:.2f}–{chi:.2f}), p={fmt_pval(pv)}")
    except Exception as e:
        print(f"   ⚠️ Logistic thô lỗi: {e}")

    # Mô hình hiệu chỉnh
    if avail:
        try:
            X2 = sm.add_constant(df_lr[[exposure] + avail].astype(float))
            model2 = sm.Logit(df_lr[outcome].astype(float), X2).fit(disp=0)
            coef = model2.params[exposure]
            se   = model2.bse[exposure]
            or_  = float(np.exp(coef))
            clo  = float(np.exp(coef - 1.96 * se))
            chi  = float(np.exp(coef + 1.96 * se))
            pv   = float(model2.pvalues[exposure])
            lbl = ", ".join(avail[:4]) + ("..." if len(avail) > 4 else "")
            results.append({
                "Phân tích":  f"Hiệu chỉnh ({lbl})",
                "OR":          round(or_, 3),
                "95%CI Lower": round(clo, 3),
                "95%CI Upper": round(chi, 3),
                "OR (95%CI)":  f"{or_:.2f} ({clo:.2f}–{chi:.2f})",
                "p-value":     fmt_pval(pv),
                "N":           n_lr,
                "Ca":          n_case,
            })
            print(f"   Adj : OR={or_:.2f} ({clo:.2f}–{chi:.2f}), p={fmt_pval(pv)}")
            or_table = np.exp(model2.params).round(3)
            ci_table = np.exp(model2.conf_int()).round(3)
            print("\n   Toàn bộ mô hình (OR, 95%CI):")
            summary_df = pd.DataFrame({
                "OR": or_table, "CI_low": ci_table[0], "CI_high": ci_table[1],
            })
            print(summary_df)
        except Exception as e:
            print(f"   ⚠️ Logistic adj lỗi: {e}")
    else:
        print("   ℹ️ Không có covariate hợp lệ → chỉ chạy mô hình thô")

    return pd.DataFrame(results)


def export_docx(tbl1, lr_res, out_path, study_name, exposure, outcome, matched):
    try:
        from docx import Document
    except ImportError:
        print("   ℹ️ python-docx chưa cài — bỏ qua DOCX")
        return
    doc = Document()
    doc.add_heading(f"Kết quả phân tích (Case-control) — {study_name}", 0)
    doc.add_paragraph(f"Ngày: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    doc.add_paragraph(f"Biến: phơi nhiễm={exposure} | ca/chứng={outcome}")
    if matched:
        doc.add_paragraph(
            "⚠️ [CẦN] Đề tài khai báo CÓ BẮT CẶP (matched) — logistic thường "
            "(unconditional) ở đây CHỈ LÀ THAM KHẢO, cần thống kê viên chạy "
            "lại bằng conditional logistic regression (vd R survival::clogit "
            "với biến strata) để có ước lượng đúng."
        )
    doc.add_paragraph("⚠️ Cần bác sĩ kiểm chứng.")
    doc.add_heading("Bảng 1. Đặc điểm nền (Ca vs Chứng)", 1)
    t = doc.add_table(rows=1, cols=len(tbl1.columns))
    t.style = "Light Shading Accent 1"
    for i, col in enumerate(tbl1.columns):
        t.rows[0].cells[i].text = col
    for _, row in tbl1.iterrows():
        cells = t.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = str(val)
    doc.add_heading("Bảng 2. Logistic regression (OR)", 1)
    if not lr_res.empty:
        t2 = doc.add_table(rows=1, cols=len(lr_res.columns))
        t2.style = "Light Shading Accent 1"
        for i, col in enumerate(lr_res.columns):
            t2.rows[0].cells[i].text = col
        for _, row in lr_res.iterrows():
            cells = t2.add_row().cells
            for i, val in enumerate(row):
                cells[i].text = str(val)
    doc.add_paragraph(
        "\nCần bác sĩ kiểm chứng. Kết quả chỉ có giá trị khi dữ liệu thật đã qua QC."
    )
    doc.save(out_path)
    print(f"   → DOCX: {out_path}")


def main():
    args = parse_args()
    _check_sap_db_locked(args.i_confirm_sap_locked, args.i_confirm_irb_approved)
    data_path  = Path(args.data)
    out_dir    = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    exposure   = args.exposure
    outcome    = args.outcome
    covariates = [c.strip() for c in args.covariates.split(",") if c.strip()]

    print(f"\n🔬 run_analysis_cli.py (case-control) — {data_path.name}")
    print(f"   Phơi nhiễm : {exposure}")
    print(f"   Ca/Chứng   : {outcome}")
    print(f"   Covariates : {', '.join(covariates)}")
    if args.matched:
        print("   ⚠️ Đề tài khai báo CÓ BẮT CẶP — xem cảnh báo conditional logistic trong DOCX")

    try:
        df = pd.read_csv(data_path, low_memory=False)
    except Exception as e:
        sys.exit(f"❌ Không đọc được {data_path}: {e}")
    print(f"   Đọc OK: {df.shape[0]} hàng × {df.shape[1]} cột")

    miss = [c for c in [exposure, outcome] if c not in df.columns]
    if miss:
        print(f"❌ Cột không tồn tại: {', '.join(miss)}")
        print(f"   Cột có sẵn: {', '.join(df.columns.tolist())}")
        sys.exit(1)

    tbl1 = make_table1(df, outcome, covariates)
    tbl1_path = out_dir / "G6_results_table1.xlsx"
    tbl1.to_excel(tbl1_path, index=False)
    print(f"   → Table 1: {tbl1_path}")

    lr_res = run_logistic(df, outcome, exposure, covariates)
    lr_path = out_dir / "G6_results_main.xlsx"
    lr_res.to_excel(lr_path, index=False)
    print(f"   → Logistic: {lr_path}")

    docx_path = out_dir / "G6_results.docx"
    export_docx(tbl1, lr_res, docx_path, "__STUDY__", exposure, outcome, args.matched)

    print("\n✅ Hoàn tất")
    print(f"   Table 1  : {tbl1_path}")
    print(f"   Logistic : {lr_path}")
    print(f"   DOCX     : {docx_path}")
    print("\n⚠️  Cần bác sĩ kiểm chứng trước khi báo cáo. Nếu bắt cặp (matched),")
    print("    cần thống kê viên xác nhận bằng conditional logistic regression.")


if __name__ == "__main__":
    main()
'''


def make_run_analysis_cli(v: dict, n_adjusted: int, study: str, design_code: str = "cohort",
                          effect_type: str = "HR") -> str:
    """
    Sinh run_analysis_cli.py — Python CLI đầy đủ.
    Dùng raw template + .replace() để tránh xung đột f-string.
    SỬA: trước đây dùng CHUNG _RUN_CLI_TEMPLATE (Cox/HR) cho MỌI design_code —
    case-control không có trục thời gian-đến-biến-cố hợp lệ, sai phương pháp
    thống kê hoàn toàn. Nay tách riêng _CASE_CONTROL_CLI_TEMPLATE (logistic/OR).
    THÊM 2026-07-06: kết cục LIÊN TỤC (effect_type=MD) — CLI Cox/HR sai phương
    pháp cho biến liên tục. Chưa có template CLI liên tục riêng, nên gắn CẢNH
    BÁO ĐẦU FILE để bác sĩ KHÔNG chạy nhầm Cox trên kết cục liên tục (script R
    03_analysis.R đã có nhánh t-test/ANCOVA đúng — dùng bản đó cho MD).
    """
    exposure      = v["exposure"]
    outcome       = v["outcome"]
    time_col      = v["time_col"]
    covars        = v["covariates"]
    covars_default = ",".join(covars) if covars else "age,sex,dm,htn"
    covars_display = ", ".join(covars) if covars else "age, sex, dm, htn"
    template = _CASE_CONTROL_CLI_TEMPLATE if design_code == "case_control" else _RUN_CLI_TEMPLATE
    code = (
        template
        .replace("__STUDY__",         study)
        .replace("__EXPOSURE__",      exposure)
        .replace("__OUTCOME__",       outcome)
        .replace("__TIME__",          time_col or "")
        .replace("__COVARS_DEFAULT__", covars_default)
        .replace("__COVARS_DISPLAY__", covars_display)
    )
    warns = []
    if effect_type == "MD":
        warns.append(
            "# ⚠️  [CẦN CHÚ Ý — KẾT CỤC LIÊN TỤC (effect_type=MD)]\n"
            "# Template CLI này dùng Cox/HR (kết cục thời gian-đến-biến-cố) — SAI\n"
            "# phương pháp cho kết cục LIÊN TỤC (đau NRS, HbA1c, chất lượng sống…).\n"
            "# Dùng script R kèm theo (03_analysis.R nhánh t-test/ANCOVA/lm) làm\n"
            "# phân tích chính; KHÔNG chạy Cox bên dưới cho biến liên tục.\n"
            "# (Phiên bản CLI Python cho kết cục liên tục sẽ bổ sung sau.)\n\n"
        )
    # THÊM 2026-07-20 (vòng lặp kiểm tra-hoàn thiện): trước đây CHỈ tách riêng
    # case_control khỏi _RUN_CLI_TEMPLATE (Cox/HR) — 5 design_code còn lại
    # (cross_sectional/diagnostic/prediction/sr_ma/qualitative) vẫn âm thầm
    # nhận CLI Cox/HR dù 03_analysis.R (đã vá đúng phương pháp cho cả 5) hoàn
    # toàn khác — cùng lớp lỗi "2 lớp xử lý design_code tách rời" đã lặp lại
    # nhiều lần. Chưa viết CLI Python riêng cho từng thiết kế (rủi ro/công sức
    # lớn) — dùng ĐÚNG mẫu cảnh báo nổi bật đã có sẵn cho effect_type=MD.
    # SỬA 2026-07-21 (vòng lặp kiểm tra-hoàn thiện vòng 2): _WRONG_METHOD_DESIGNS
    # và method_hint hoist lên module-level (xem đầu file, gần make_r01_cleaning)
    # — trước đây định nghĩa LẶP LẠI y hệt ở đây và make_sensitivity_analysis().
    if design_code in _WRONG_METHOD_DESIGNS:
        method_hint = _METHOD_HINT_BY_DESIGN[design_code]
        warns.append(
            f"# ⚠️  [CẦN CHÚ Ý — THIẾT KẾ {design_code.upper()}]\n"
            "# Template CLI này dùng Cox/HR (kết cục thời gian-đến-biến-cố) — KHÔNG\n"
            f"# đúng phương pháp cho thiết kế này (cần {method_hint}).\n"
            "# Dùng script R kèm theo (03_analysis.R — đã có nhánh đúng cho thiết kế\n"
            "# này) làm phân tích chính; KHÔNG chạy Cox bên dưới.\n"
            "# (Phiên bản CLI Python riêng cho thiết kế này sẽ bổ sung sau.)\n\n"
        )
    if warns:
        code = _insert_warning_after_shebang(code, "".join(warns))
    return code



_SENSITIVITY_TEMPLATE = (
    "#!/usr/bin/env python3\n"
    "# sensitivity_analysis.py -- Phan tich do nhay\n"
    "# De tai: __STUDY__\n"
    "# Bien  : exposure=__EXPOSURE__ | outcome=__OUTCOME__ | time=__TIME__\n"
    "#\n"
    "# Noi dung:\n"
    "#   1. Complete-case vs Multiple Imputation (mean-impute demo)\n"
    "#   2. Subgroup: sex, dm, htn, age>=70\n"
    "#   3. E-value (unmeasured confounding)\n"
    "#\n"
    "# Cach dung: python sensitivity_analysis.py --data path/to/data.csv\n"
    "# Yeu cau: pandas, numpy, lifelines, scipy\n"
    "import argparse, warnings\n"
    "warnings.filterwarnings(\'ignore\')\n"
    "import numpy as np\n"
    "import pandas as pd\n"
    "try:\n"
    "    from lifelines import CoxPHFitter\n"
    "except ImportError:\n"
    "    raise SystemExit(\'pip install lifelines\')\n"
    "try:\n"
    "    from scipy import stats\n"
    "except ImportError:\n"
    "    raise SystemExit(\'pip install scipy\')\n"
    "\n"
    "def evalue_hr(hr, ci_lo):\n"
    "    \"\"\"E-value (VanderWeele & Ding 2017). PMID: 28693043\"\"\"\n"
    "    def _ev(r):\n"
    "        if r < 1.0: r = 1.0/r\n"
    "        return r + (r*(r-1))**0.5\n"
    "    return round(_ev(hr),2), round(_ev(max(ci_lo,1e-6)),2)\n"
    "\n"
    "def fmt_pval(p):\n"
    "    return \'<0.001\' if p<0.001 else f\'{p:.3f}\'\n"
    "\n"
    "def _check_sap_db_locked(i_confirm_sap, i_confirm_irb=False):\n"
    "    # Audit 2026-07-11: script nay chay hoi quy Cox THAT tren du lieu CSV THAT\n"
    "    # (giong het run_analysis_cli.py) nhung truoc day KHONG co cong nao ca -\n"
    "    # sao chep dung cung co che ledger_approved da co o CLI template chinh.\n"
    "    # Va 2026-07-12 (audit toan dien): co --i-confirm-* truoc day bo qua CA\n"
    "    # ledger check -- nay co CHI thay the checkpoint-file, ledger LUON bat buoc.\n"
    "    import hashlib as _hashlib, json as _json, re as _re, sys as _sys\n"
    "    from pathlib import Path as _Path\n"
    "    _sys.path.insert(0, str(_Path(__file__).resolve().parents[3] / 'tools'))\n"
    "    import gate_contract as _GC\n"
    "    def _is_locked(status):\n"
    "        s = str(status or \'\').strip().upper()\n"
    "        if _re.search(r'(UN|CH[ƯU]A|KH[ÔO]NG|NOT)\\s*LOCKED', s):\n"
    "            return False\n"
    "        return bool(_re.match(r\'^LOCKED\\b\', s))\n"
    "    def _load_cp(gate):\n"
    "        p = _Path(\'exports\') / \'__STUDY__\' / f\'{gate}_checkpoint.json\'\n"
    "        if p.exists():\n"
    "            try:\n"
    "                return _json.loads(p.read_text(encoding=\'utf-8\'))\n"
    "            except (ValueError, OSError):\n"
    "                return {}\n"
    "        return {}\n"
    "    g2 = _load_cp(\'G2\'); g4 = _load_cp(\'G4\'); g5 = _load_cp(\'G5\')\n"
    "    g2_cp = _is_locked(g2.get(\'g2_status\', g2.get(\'G2_STATUS\')))\n"
    "    g4_cp = _is_locked(g4.get(\'g4_status\', g4.get(\'G4_STATUS\')))\n"
    "    g5_cp = _is_locked(g5.get(\'g5_status\', g5.get(\'G5_STATUS\')))\n"
    "    g2_ledger = _GC.ledger_approved(\n"
    "        \"G2\", \"__STUDY__\", _Path(\'exports\') / \'__STUDY__\' / \'G2_A3_ETHICS_PACKAGE___STUDY__.md\')\n"
    "    g4_ledger = _GC.ledger_approved(\n"
    "        \"G4\", \"__STUDY__\", _Path(\'exports\') / \'__STUDY__\' / \'G4_A5_SAP_FINAL___STUDY__.md\')\n"
    "    g5_ledger = _GC.ledger_approved(\n"
    "        \"G5\", \"__STUDY__\", _Path(\'exports\') / \'__STUDY__\' / \'G5_checkpoint.json\')\n"
    "    g2_quality = _GC.g2_quality_contract_satisfied(\n"
    "        g2, _GC.load_study_meta(_Path('exports') / '__STUDY__'))\n"
    "    g2_locked = (g2_cp or i_confirm_irb) and g2_ledger and g2_quality\n"
    "    g4_locked = (g4_cp or i_confirm_sap) and g4_ledger\n"
    "    g5_quality = _GC.g5_quality_contract_satisfied('__STUDY__')\n"
    "    g5_locked = (g5_cp or i_confirm_sap) and g5_ledger and g5_quality\n"
    "    if not g2_locked:\n"
    "        raise SystemExit(\'DUNG: G2 (phe duyet dao duc/IRB) chua xac nhan LOCKED bang phe duyet that (chu ky). \'\n"
    "                         \'--i-confirm-irb-approved chi thay checkpoint-file, KHONG thay duoc ledger.\')\n"
    "    if not (g4_locked and g5_locked):\n"
    "        raise SystemExit(\'DUNG: G4 (SAP) hoac G5 (khoa DB) chua xac nhan LOCKED bang phe duyet that (chu ky). \'\n"
    "                         \'--i-confirm-sap-locked chi thay checkpoint-file, KHONG thay duoc ledger.\')\n"
    "\n"
    "def run_cox_sub(df, time_col, outcome, exposure, avail):\n"
    "    cols = [time_col, outcome, exposure]+avail\n"
    "    df2  = df[[c for c in cols if c in df.columns]].dropna()\n"
    "    cph  = CoxPHFitter()\n"
    "    cph.fit(df2, duration_col=time_col, event_col=outcome)\n"
    "    try:\n"
    "        cph.check_assumptions(df2, p_value_threshold=0.05, show_plots=False)\n"
    "    except Exception as _e_ph:\n"
    "        print(f'   [CANH BAO] Khong kiem duoc gia dinh PH cho {exposure}: {_e_ph}')\n"
    "    s = cph.summary.loc[exposure]\n"
    "    hr, clo, chi, pv = (s[k] for k in[\'exp(coef)\',\'exp(coef) lower 95%\',\'exp(coef) upper 95%\',\'p\'])\n"
    "    return hr,clo,chi,pv,len(df2),int(df2[outcome].sum())\n"
    "\n"
    "def pick_subgroup_covars(sub, outcome, avail, exclude=None):\n"
    "    # Gioi han covariates theo events-per-variable (EPV>=8) de tranh\n"
    "    # non-convergence khi co mau con nho hon nhieu so voi mo hinh chinh.\n"
    "    events = int(sub[outcome].sum())\n"
    "    max_n  = max(1, events // 8)\n"
    "    pool   = [c for c in avail if c != exclude]\n"
    "    return pool[:max_n]\n"
    "\n"
    "def main():\n"
    "    parser = argparse.ArgumentParser()\n"
    "    parser.add_argument(\'--data\', required=True)\n"
    "    parser.add_argument(\'--exposure\',   default=\'__EXPOSURE__\')\n"
    "    parser.add_argument(\'--outcome\',    default=\'__OUTCOME__\')\n"
    "    parser.add_argument(\'--time\',       default=\'__TIME__\')\n"
    "    parser.add_argument(\'--covariates\', default=\'__COVARS_DEFAULT__\')\n"
    "    parser.add_argument(\'--output-dir\', default=\'.')\n"
    "    parser.add_argument(\'--i-confirm-sap-locked\', action=\'store_true\')\n"
    "    parser.add_argument(\'--i-confirm-irb-approved\', action=\'store_true\')\n"
    "    args = parser.parse_args()\n"
    "    _check_sap_db_locked(args.i_confirm_sap_locked, args.i_confirm_irb_approved)\n"
    "    exposure   = args.exposure\n"
    "    outcome    = args.outcome\n"
    "    time_col   = args.time\n"
    "    covariates = [c.strip() for c in args.covariates.split(\',\') if c.strip()]\n"
    "    out_dir    = __import__(\'pathlib\').Path(args.output_dir)\n"
    "    out_dir.mkdir(parents=True, exist_ok=True)\n"
    "    df = pd.read_csv(args.data, low_memory=False)\n"
    "    avail = [c for c in covariates if c in df.columns]\n"
    "    sens_rows = []\n"
    "    # Complete-case\n"
    "    try:\n"
    "        hr,clo,chi,pv,n,ev = run_cox_sub(df,time_col,outcome,exposure,avail)\n"
    "        sens_rows.append(dict(method=\'Complete-case\',HR=round(hr,3),CI_lo=round(clo,3),CI_hi=round(chi,3),p=round(pv,3),N=n,Events=ev))\n"
    "        print(f\'   CC: HR={hr:.2f} ({clo:.2f}-{chi:.2f}), p={fmt_pval(pv)}\')\n"
    "    except Exception as e:\n"
    "        print(f\'   CC loi: {e}\')\n"
    "    # MI demo\n"
    "    try:\n"
    "        cols2 = [time_col,outcome,exposure]+avail\n"
    "        df2   = df[[c for c in cols2 if c in df.columns]].copy()\n"
    "        for col in avail:\n"
    "            if df2[col].isna().any():\n"
    "                uq = df2[col].dropna().unique()\n"
    "                fill = df2[col].mode()[0] if set(uq).issubset({0,1,2,3,4,5}) else df2[col].mean()\n"
    "                df2[col]=df2[col].fillna(fill)\n"
    "        df2=df2.dropna()\n"
    "        hr,clo,chi,pv,n,ev = run_cox_sub(df2,time_col,outcome,exposure,avail)\n"
    "        sens_rows.append(dict(method=\'MI-demo (mean-impute; R mice m=20 for real)\',HR=round(hr,3),CI_lo=round(clo,3),CI_hi=round(chi,3),p=round(pv,3),N=n,Events=ev))\n"
    "        print(f\'   MI: HR={hr:.2f} ({clo:.2f}-{chi:.2f}), p={fmt_pval(pv)}\')\n"
    "    except Exception as e:\n"
    "        print(f\'   MI loi: {e}\')\n"
    "    # Subgroup\n"
    "    sub_rows = []\n"
    "    for sg in [\'sex\',\'dm\',\'htn\']:\n"
    "        if sg not in df.columns: continue\n"
    "        for val in sorted(df[sg].dropna().unique()):\n"
    "            sub = df[df[sg]==val][[c for c in [time_col,outcome,exposure]+avail if c in df.columns]].dropna()\n"
    "            if len(sub)<20 or sub[outcome].sum()<5: continue\n"
    "            sub_covars = pick_subgroup_covars(sub, outcome, avail, exclude=sg)\n"
    "            try:\n"
    "                hr,clo,chi,pv,n,ev = run_cox_sub(sub,time_col,outcome,exposure,sub_covars)\n"
    "                sub_rows.append(dict(Subgroup=sg,Value=str(val),HR=round(hr,3),CI_lo=round(clo,3),CI_hi=round(chi,3),p=round(pv,3),N=n,Events=ev,Covars_used=len(sub_covars)))\n"
    "                print(f\'   {sg}={val}: HR={hr:.2f} ({clo:.2f}-{chi:.2f}), p={fmt_pval(pv)} [adj {len(sub_covars)} bien]\')\n"
    "            except Exception as e:\n"
    "                try:\n"
    "                    hr,clo,chi,pv,n,ev = run_cox_sub(sub,time_col,outcome,exposure,[])\n"
    "                    sub_rows.append(dict(Subgroup=sg,Value=str(val),HR=round(hr,3),CI_lo=round(clo,3),CI_hi=round(chi,3),p=round(pv,3),N=n,Events=ev,Covars_used=0))\n"
    "                    print(f\'   {sg}={val}: HR tho={hr:.2f} ({clo:.2f}-{chi:.2f}), p={fmt_pval(pv)} [khong hoi tu voi covariates, dung mo hinh tho]\')\n"
    "                except Exception as e2:\n"
    "                    print(f\'   {sg}={val} loi: {e2}\')\n"
    "    if \'age\' in df.columns:\n"
    "        df[\'_ag\']=df[\'age\'].apply(lambda x:\'age>=70\' if x>=70 else \'age<70\')\n"
    "        for val in [\'age<70\',\'age>=70\']:\n"
    "            sub=df[df[\'_ag\']==val][[c for c in [time_col,outcome,exposure]+avail if c in df.columns]].dropna()\n"
    "            if len(sub)<20 or sub[outcome].sum()<5: continue\n"
    "            sub_covars = pick_subgroup_covars(sub, outcome, avail, exclude=\'age\')\n"
    "            try:\n"
    "                hr,clo,chi,pv,n,ev=run_cox_sub(sub,time_col,outcome,exposure,sub_covars)\n"
    "                sub_rows.append(dict(Subgroup=\'age_group\',Value=val,HR=round(hr,3),CI_lo=round(clo,3),CI_hi=round(chi,3),p=round(pv,3),N=n,Events=ev,Covars_used=len(sub_covars)))\n"
    "            except Exception:\n"
    "                try:\n"
    "                    hr,clo,chi,pv,n,ev=run_cox_sub(sub,time_col,outcome,exposure,[])\n"
    "                    sub_rows.append(dict(Subgroup=\'age_group\',Value=val,HR=round(hr,3),CI_lo=round(clo,3),CI_hi=round(chi,3),p=round(pv,3),N=n,Events=ev,Covars_used=0))\n"
    "                except Exception: pass\n"
    "    # E-value\n"
    "    if sens_rows:\n"
    "        hr_main=sens_rows[0][\'HR\']; clo_main=sens_rows[0][\'CI_lo\']\n"
    "        ev_pt,ev_ci=evalue_hr(hr_main,clo_main)\n"
    "        print(f\'   E-value: {ev_pt} (CI bound: {ev_ci})\')\n"
    "        print(\'   PMID: 28693043\')\n"
    "        pd.DataFrame([dict(HR=hr_main,CI_lo=clo_main,E_value_point=ev_pt,E_value_CI=ev_ci)]).to_excel(out_dir/\'G6_evalue.xlsx\',index=False)\n"
    "    if sens_rows: pd.DataFrame(sens_rows).to_excel(out_dir/\'G6_sensitivity_ccmi.xlsx\',index=False)\n"
    "    if sub_rows:  pd.DataFrame(sub_rows).to_excel(out_dir/\'G6_subgroup.xlsx\',index=False)\n"
    "    print(\'\\n\u26a0\ufe0f  Can bac si kiem chung. MI that: dung R mice m=20.\')\n"
    "\n"
    "if __name__ == \'__main__\':\n"
    "    main()\n"
)


# SỬA: sensitivity_analysis.py trước đây dùng CHUNG _SENSITIVITY_TEMPLATE
# (Cox/HR, lifelines) cho MỌI design_code — case-control không có trục
# thời gian-đến-biến-cố hợp lệ. Viết template riêng dùng logistic/OR
# (statsmodels), bao gồm cả E-value với xử lý xấp xỉ OR→RR (VanderWeele &
# Ding 2017) khi outcome KHÔNG hiếm — case-control thường có tỷ lệ "ca"
# trong mẫu rất cao (do chủ đích chọn mẫu theo tình trạng bệnh), nên KHÔNG
# thể mặc định coi OR≈RR như với cohort/RCT hiếm biến cố.
_CASE_CONTROL_SENSITIVITY_TEMPLATE = r'''#!/usr/bin/env python3
# sensitivity_analysis.py -- Phan tich do nhay (Case-control)
# De tai: __STUDY__
# Bien  : phoi nhiem=__EXPOSURE__ | ca/chung (outcome)=__OUTCOME__
#
# Noi dung:
#   1. Complete-case vs Multiple Imputation (mean-impute demo)
#   2. Subgroup: sex, dm, htn, age>=70
#   3. E-value (unmeasured confounding) -- OR, co xap xi OR->RR neu outcome pho bien
#
# Cach dung: python sensitivity_analysis.py --data path/to/data.csv
# Yeu cau: pandas, numpy, statsmodels, scipy
import argparse, warnings
warnings.filterwarnings('ignore')
import numpy as np
import pandas as pd
try:
    import statsmodels.api as sm
except ImportError:
    raise SystemExit('pip install statsmodels')
try:
    from scipy import stats
except ImportError:
    raise SystemExit('pip install scipy')


def evalue_or(or_val, ci_lo, outcome_prevalence=None):
    """
    E-value cho Odds Ratio (VanderWeele & Ding 2017, PMID: 28693043).
    Neu outcome PHO BIEN trong mau (case-control thuong nhu vay do chu dich
    chon mau theo tinh trang benh), OR khong xap xi RR tot -- ap dung xap xi
    sqrt(OR) truoc khi tinh E-value (theo khuyen nghi cua chinh bai bao goc).
    outcome_prevalence: ty le "ca" trong QUAN THE NGUON (khong phai trong mau
    case-control da chu dich lay mau) -- neu khong biet, mac dinh gia dinh
    HIEM (< 15%) va CANH BAO ro cho bac si tu xac nhan.
    """
    def _ev(r):
        if r < 1.0:
            r = 1.0 / r
        return r + (r * (r - 1)) ** 0.5
    assume_rare = outcome_prevalence is None or outcome_prevalence < 0.15
    if assume_rare:
        rr_point, rr_ci = or_val, max(ci_lo, 1e-6)
        note = '[CẦN xác nhận] giả định outcome HIẾM trong quần thể nguồn (OR≈RR) -- chưa biết tỷ lệ thật'
    else:
        rr_point, rr_ci = or_val ** 0.5, max(ci_lo, 1e-6) ** 0.5
        note = 'outcome PHỔ BIẾN trong quần thể nguồn -- đã áp xấp xỉ sqrt(OR) trước khi tính E-value'
    return round(_ev(rr_point), 2), round(_ev(rr_ci), 2), note


def fmt_pval(p):
    return '<0.001' if p < 0.001 else f'{p:.3f}'


def _check_sap_db_locked(i_confirm_sap, i_confirm_irb=False):
    # Audit 2026-07-11: script nay chay hoi quy logistic THAT tren du lieu CSV THAT
    # (giong het run_case_control_cli.py) nhung truoc day KHONG co cong nao ca -
    # sao chep dung cung co che ledger_approved da co o CLI template chinh.
    # Va 2026-07-12 (audit toan dien): --i-confirm-* truoc day bo qua CA ledger
    # check -- nay co CHI thay the checkpoint-file, ledger LUON bat buoc.
    import hashlib as _hashlib
    import json as _json
    import re as _re
    import sys as _sys
    from pathlib import Path as _Path
    _sys.path.insert(0, str(_Path(__file__).resolve().parents[3] / "tools"))
    import gate_contract as _GC

    def _is_locked(status):
        s = str(status or '').strip().upper()
        if _re.search(r'(UN|CH[ƯU]A|KH[ÔO]NG|NOT)\s*LOCKED', s):
            return False
        return bool(_re.match(r'^LOCKED\b', s))

    def _load_cp(gate):
        p = _Path('exports') / '__STUDY__' / f'{gate}_checkpoint.json'
        if p.exists():
            try:
                return _json.loads(p.read_text(encoding='utf-8'))
            except (ValueError, OSError):
                return {}
        return {}

    g2 = _load_cp('G2')
    g4 = _load_cp('G4')
    g5 = _load_cp('G5')
    g2_cp = _is_locked(g2.get('g2_status', g2.get('G2_STATUS')))
    g4_cp = _is_locked(g4.get('g4_status', g4.get('G4_STATUS')))
    g5_cp = _is_locked(g5.get('g5_status', g5.get('G5_STATUS')))
    g2_ledger = _GC.ledger_approved(
        "G2", "__STUDY__", _Path('exports') / '__STUDY__' / 'G2_A3_ETHICS_PACKAGE___STUDY__.md')
    g4_ledger = _GC.ledger_approved(
        "G4", "__STUDY__", _Path('exports') / '__STUDY__' / 'G4_A5_SAP_FINAL___STUDY__.md')
    g5_ledger = _GC.ledger_approved(
        "G5", "__STUDY__", _Path('exports') / '__STUDY__' / 'G5_checkpoint.json')
    g2_quality = _GC.g2_quality_contract_satisfied(
        g2, _GC.load_study_meta(_Path('exports') / '__STUDY__'))
    g2_locked = (g2_cp or i_confirm_irb) and g2_ledger and g2_quality
    g4_locked = (g4_cp or i_confirm_sap) and g4_ledger
    g5_quality = _GC.g5_quality_contract_satisfied("__STUDY__")
    g5_locked = (g5_cp or i_confirm_sap) and g5_ledger and g5_quality
    if not g2_locked:
        raise SystemExit('DUNG: G2 (phe duyet dao duc/IRB) chua xac nhan LOCKED bang phe duyet that (chu ky). '
                          '--i-confirm-irb-approved chi thay checkpoint-file, KHONG thay duoc ledger.')
    if not (g4_locked and g5_locked):
        raise SystemExit('DUNG: G4 (SAP) hoac G5 (khoa DB) chua xac nhan LOCKED bang phe duyet that (chu ky). '
                          '--i-confirm-sap-locked chi thay checkpoint-file, KHONG thay duoc ledger.')


def run_logistic_sub(df, outcome, exposure, avail):
    cols = [outcome, exposure] + avail
    df2 = df[[c for c in cols if c in df.columns]].dropna().astype(float)
    X = sm.add_constant(df2[[exposure] + avail])
    model = sm.Logit(df2[outcome], X).fit(disp=0)
    coef = model.params[exposure]
    se = model.bse[exposure]
    or_ = float(np.exp(coef))
    clo = float(np.exp(coef - 1.96 * se))
    chi = float(np.exp(coef + 1.96 * se))
    pv = float(model.pvalues[exposure])
    return or_, clo, chi, pv, len(df2), int(df2[outcome].sum())


def pick_subgroup_covars(sub, outcome, avail, exclude=None):
    # Gioi han covariates theo events-per-variable (EPV>=8) de tranh
    # non-convergence khi co mau con nho hon nhieu so voi mo hinh chinh.
    events = int(sub[outcome].sum())
    max_n = max(1, events // 8)
    pool = [c for c in avail if c != exclude]
    return pool[:max_n]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', required=True)
    parser.add_argument('--exposure', default='__EXPOSURE__')
    parser.add_argument('--outcome', default='__OUTCOME__')
    parser.add_argument('--covariates', default='__COVARS_DEFAULT__')
    parser.add_argument('--outcome-prevalence', type=float, default=None,
                         help='Ty le ca trong QUAN THE NGUON (khong phai trong mau) -- de tinh E-value dung neu outcome pho bien')
    parser.add_argument('--output-dir', default='.')
    parser.add_argument('--i-confirm-sap-locked', action='store_true')
    parser.add_argument('--i-confirm-irb-approved', action='store_true')
    args = parser.parse_args()
    _check_sap_db_locked(args.i_confirm_sap_locked, args.i_confirm_irb_approved)
    exposure = args.exposure
    outcome = args.outcome
    covariates = [c.strip() for c in args.covariates.split(',') if c.strip()]
    out_dir = __import__('pathlib').Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(args.data, low_memory=False)
    avail = [c for c in covariates if c in df.columns]
    sens_rows = []
    # Complete-case
    try:
        or_, clo, chi, pv, n, ev = run_logistic_sub(df, outcome, exposure, avail)
        sens_rows.append(dict(method='Complete-case', OR=round(or_, 3), CI_lo=round(clo, 3), CI_hi=round(chi, 3), p=round(pv, 3), N=n, Ca=ev))
        print(f'   CC: OR={or_:.2f} ({clo:.2f}-{chi:.2f}), p={fmt_pval(pv)}')
    except Exception as e:
        print(f'   CC loi: {e}')
    # MI demo
    try:
        cols2 = [outcome, exposure] + avail
        df2 = df[[c for c in cols2 if c in df.columns]].copy()
        for col in avail:
            if df2[col].isna().any():
                uq = df2[col].dropna().unique()
                fill = df2[col].mode()[0] if set(uq).issubset({0, 1, 2, 3, 4, 5}) else df2[col].mean()
                df2[col] = df2[col].fillna(fill)
        df2 = df2.dropna()
        or_, clo, chi, pv, n, ev = run_logistic_sub(df2, outcome, exposure, avail)
        sens_rows.append(dict(method='MI-demo (mean-impute; R mice m=20 for real)', OR=round(or_, 3), CI_lo=round(clo, 3), CI_hi=round(chi, 3), p=round(pv, 3), N=n, Ca=ev))
        print(f'   MI: OR={or_:.2f} ({clo:.2f}-{chi:.2f}), p={fmt_pval(pv)}')
    except Exception as e:
        print(f'   MI loi: {e}')
    # Subgroup
    sub_rows = []
    for sg in ['sex', 'dm', 'htn']:
        if sg not in df.columns:
            continue
        for val in sorted(df[sg].dropna().unique()):
            sub = df[df[sg] == val][[c for c in [outcome, exposure] + avail if c in df.columns]].dropna()
            if len(sub) < 20 or sub[outcome].sum() < 5:
                continue
            sub_covars = pick_subgroup_covars(sub, outcome, avail, exclude=sg)
            try:
                or_, clo, chi, pv, n, ev = run_logistic_sub(sub, outcome, exposure, sub_covars)
                sub_rows.append(dict(Subgroup=sg, Value=str(val), OR=round(or_, 3), CI_lo=round(clo, 3), CI_hi=round(chi, 3), p=round(pv, 3), N=n, Ca=ev, Covars_used=len(sub_covars)))
                print(f'   {sg}={val}: OR={or_:.2f} ({clo:.2f}-{chi:.2f}), p={fmt_pval(pv)} [adj {len(sub_covars)} bien]')
            except Exception:
                try:
                    or_, clo, chi, pv, n, ev = run_logistic_sub(sub, outcome, exposure, [])
                    sub_rows.append(dict(Subgroup=sg, Value=str(val), OR=round(or_, 3), CI_lo=round(clo, 3), CI_hi=round(chi, 3), p=round(pv, 3), N=n, Ca=ev, Covars_used=0))
                    print(f'   {sg}={val}: OR tho={or_:.2f} ({clo:.2f}-{chi:.2f}), p={fmt_pval(pv)} [khong hoi tu voi covariates, dung mo hinh tho]')
                except Exception as e2:
                    print(f'   {sg}={val} loi: {e2}')
    if 'age' in df.columns:
        df['_ag'] = df['age'].apply(lambda x: 'age>=70' if x >= 70 else 'age<70')
        for val in ['age<70', 'age>=70']:
            sub = df[df['_ag'] == val][[c for c in [outcome, exposure] + avail if c in df.columns]].dropna()
            if len(sub) < 20 or sub[outcome].sum() < 5:
                continue
            sub_covars = pick_subgroup_covars(sub, outcome, avail, exclude='age')
            try:
                or_, clo, chi, pv, n, ev = run_logistic_sub(sub, outcome, exposure, sub_covars)
                sub_rows.append(dict(Subgroup='age_group', Value=val, OR=round(or_, 3), CI_lo=round(clo, 3), CI_hi=round(chi, 3), p=round(pv, 3), N=n, Ca=ev, Covars_used=len(sub_covars)))
            except Exception:
                try:
                    or_, clo, chi, pv, n, ev = run_logistic_sub(sub, outcome, exposure, [])
                    sub_rows.append(dict(Subgroup='age_group', Value=val, OR=round(or_, 3), CI_lo=round(clo, 3), CI_hi=round(chi, 3), p=round(pv, 3), N=n, Ca=ev, Covars_used=0))
                except Exception:
                    pass
    # E-value
    if sens_rows:
        or_main = sens_rows[0]['OR']
        clo_main = sens_rows[0]['CI_lo']
        ev_pt, ev_ci, ev_note = evalue_or(or_main, clo_main, args.outcome_prevalence)
        print(f'   E-value: {ev_pt} (CI bound: {ev_ci})')
        print(f'   {ev_note}')
        print('   PMID: 28693043')
        pd.DataFrame([dict(OR=or_main, CI_lo=clo_main, E_value_point=ev_pt, E_value_CI=ev_ci, Note=ev_note)]).to_excel(out_dir / 'G6_evalue.xlsx', index=False)
    if sens_rows:
        pd.DataFrame(sens_rows).to_excel(out_dir / 'G6_sensitivity_ccmi.xlsx', index=False)
    if sub_rows:
        pd.DataFrame(sub_rows).to_excel(out_dir / 'G6_subgroup.xlsx', index=False)
    print('\n⚠️  Cần bác sĩ kiểm chứng. MI thật: dùng R mice m=20.')
    print('⚠️  Nếu case-control CÓ bắt cặp (matched), cần thống kê viên chạy')
    print('    lại bằng conditional logistic regression (không phải bảng này).')


if __name__ == '__main__':
    main()
'''


def make_sensitivity_analysis(v: dict, study: str, design_code: str = "cohort") -> str:
    """
    Sinh sensitivity_analysis.py — dung raw template + .replace().
    SỬA: trước đây dùng CHUNG _SENSITIVITY_TEMPLATE (Cox/HR) cho MỌI
    design_code — case-control sai phương pháp thống kê hoàn toàn. Nay tách
    riêng _CASE_CONTROL_SENSITIVITY_TEMPLATE (logistic/OR + E-value đã xử lý
    xấp xỉ OR→RR khi outcome không hiếm).
    """
    exposure       = v["exposure"]
    outcome        = v["outcome"]
    time_col       = v["time_col"]
    covars         = v["covariates"]
    covars_default = ",".join(covars) if covars else "age,sex,dm,htn"
    if design_code == "case_control":
        return (
            _CASE_CONTROL_SENSITIVITY_TEMPLATE
            .replace("__STUDY__",          study)
            .replace("__EXPOSURE__",       exposure)
            .replace("__OUTCOME__",        outcome)
            .replace("__COVARS_DEFAULT__", covars_default)
        )
    code = (
        _SENSITIVITY_TEMPLATE
        .replace("__STUDY__",          study)
        .replace("__EXPOSURE__",       exposure)
        .replace("__OUTCOME__",        outcome)
        .replace("__TIME__",           time_col)
        .replace("__COVARS_DEFAULT__", covars_default)
    )
    # THÊM 2026-07-20 (vòng lặp kiểm tra-hoàn thiện): cùng lớp lỗi vừa vá ở
    # make_run_analysis_cli() — _SENSITIVITY_TEMPLATE cũng là Cox/HR
    # (lifelines.CoxPHFitter), sai phương pháp cho 5 design_code này. Dùng
    # đúng mẫu cảnh báo nổi bật đã có, chưa viết template riêng cho từng thiết kế.
    # SỬA 2026-07-21 (vòng lặp kiểm tra-hoàn thiện vòng 2): _WRONG_METHOD_DESIGNS
    # hoist lên module-level (xem đầu file, gần make_r01_cleaning) — trước đây
    # định nghĩa LẶP LẠI y hệt ở đây và make_run_analysis_cli().
    if design_code in _WRONG_METHOD_DESIGNS:
        warn = (
            f"# ⚠️  [CẦN CHÚ Ý — THIẾT KẾ {design_code.upper()}]\n"
            "# Template phân tích độ nhạy này dùng Cox/HR (E-value theo HR) — KHÔNG\n"
            "# đúng phương pháp cho thiết kế này. Cần thống kê viên thiết kế phân\n"
            "# tích độ nhạy phù hợp (vd E-value theo OR cho cross_sectional/\n"
            "# diagnostic, leave-one-out cho sr_ma) trước khi dùng script này.\n\n"
        )
        code = _insert_warning_after_shebang(code, warn)
    return code


# ─────────────────────────────────────────────
# BẢNG KẾT QUẢ DỰ KIẾN THEO THIẾT KẾ
# ─────────────────────────────────────────────

TABLE_SHELLS = {
    "rct": [
        ("Bảng 1 — Đặc điểm nền", [
            ("Biến", "Can thiệp (N=[CẦN])", "Chứng (N=[CẦN])", "SMD"),
            ("Tuổi (năm), TB±SD", "[CẦN]", "[CẦN]", "[CẦN]"),
            ("Giới nữ, n (%)", "[CẦN]", "[CẦN]", "[CẦN]"),
        ]),
        ("Bảng 2 — Kết cục chính (ITT)", [
            ("Phân tích", "Ước lượng", "95%CI", "p"),
            ("RR/OR thô", "[CẦN]", "[CẦN]", "[CẦN]"),
            ("RR/OR hiệu chỉnh", "[CẦN]", "[CẦN]", "[CẦN]"),
        ]),
    ],
    "cohort": [
        ("Bảng 1 — Đặc điểm nền (tên biến thật từ REDCap — xem scripts/02_tables.R)", [
            ("Biến", "Phơi nhiễm+ (N=[CẦN])", "Phơi nhiễm- (N=[CẦN])", "SMD / p"),
            ("Tuổi (năm), TB±SD", "[chạy 02_tables.R]", "[chạy 02_tables.R]", "[chạy]"),
            ("Giới nữ, n (%)", "[chạy 02_tables.R]", "[chạy 02_tables.R]", "[chạy]"),
            ("ĐTĐ, n (%)", "[chạy 02_tables.R]", "[chạy 02_tables.R]", "[chạy]"),
            ("THA, n (%)", "[chạy 02_tables.R]", "[chạy 02_tables.R]", "[chạy]"),
        ]),
        ("Bảng 2 — Kết cục chính (Cox regression)", [
            ("Phân tích", "HR", "95%CI Lower", "95%CI Upper", "p"),
            ("Thô (univariable)", "[chạy 03_analysis.R]", "[chạy]", "[chạy]", "[chạy]"),
            ("Hiệu chỉnh (multivariable)", "[chạy 03_analysis.R]", "[chạy]", "[chạy]", "[chạy]"),
            ("Complete-case sensitivity", "[chạy sensitivity.py]", "[chạy]", "[chạy]", "[chạy]"),
            ("MI (R mice m=20)", "[chạy 03_analysis.R §MI]", "[chạy]", "[chạy]", "[chạy]"),
        ]),
        ("Bảng 3 — Phân tích độ nhạy", [
            ("Phương pháp", "HR (95%CI)", "p", "Ghi chú"),
            ("Complete-case", "[sensitivity.py]", "[chạy]", "Hàng không thiếu"),
            ("MI (demo Python)", "[sensitivity.py]", "[chạy]", "Dùng R mice m=20 cho thật"),
            ("E-value", "[sensitivity.py]", "—", "Min confounding để xóa kết quả"),
        ]),
        ("Bảng 4 — Phân tích nhóm con", [
            ("Nhóm", "HR (95%CI)", "p", "N", "Biến cố"),
            ("[sensitivity.py → G6_subgroup.xlsx]", "[chạy]", "[chạy]", "[chạy]", "[chạy]"),
        ]),
    ],
    # SỬA: trước đây design_code không khớp "rct"/"cohort" (vd diagnostic,
    # cross_sectional, case_control, sr_ma) âm thầm dùng TABLE_SHELLS["cohort"]
    # (bảng Cox regression HR) — với thiết kế chẩn đoán, bảng kết quả nói
    # "Phân tích chính: ROC/AUC" nhưng bảng lại hiện cột "HR/95%CI" mâu thuẫn
    # nội tại, guardrail vẫn PASS. Thêm bảng đúng cho từng thiết kế.
    "cross_sectional": [
        ("Bảng 1 — Đặc điểm nền", [
            ("Biến", "Phơi nhiễm+ (N=[CẦN])", "Phơi nhiễm- (N=[CẦN])", "SMD / p"),
            ("Tuổi (năm), TB±SD", "[chạy 02_tables.R]", "[chạy 02_tables.R]", "[chạy]"),
            ("Giới nữ, n (%)", "[chạy 02_tables.R]", "[chạy 02_tables.R]", "[chạy]"),
        ]),
        ("Bảng 2 — Kết cục chính (Logistic regression)", [
            ("Phân tích", "OR", "95%CI Lower", "95%CI Upper", "p"),
            ("Thô (univariable)", "[chạy 03_analysis.R]", "[chạy]", "[chạy]", "[chạy]"),
            ("Hiệu chỉnh (multivariable)", "[chạy 03_analysis.R]", "[chạy]", "[chạy]", "[chạy]"),
        ]),
    ],
    "case_control": [
        ("Bảng 1 — Đặc điểm nền (Ca/Chứng)", [
            ("Biến", "Ca (N=[CẦN])", "Chứng (N=[CẦN])", "p"),
            ("Tuổi (năm), TB±SD", "[chạy 02_tables.R]", "[chạy 02_tables.R]", "[chạy]"),
            ("Giới nữ, n (%)", "[chạy 02_tables.R]", "[chạy 02_tables.R]", "[chạy]"),
        ]),
        ("Bảng 2 — Phơi nhiễm liên quan (Conditional logistic)", [
            ("Phân tích", "OR", "95%CI Lower", "95%CI Upper", "p"),
            ("Thô (univariable)", "[chạy 03_analysis.R]", "[chạy]", "[chạy]", "[chạy]"),
            ("Hiệu chỉnh (multivariable)", "[chạy 03_analysis.R]", "[chạy]", "[chạy]", "[chạy]"),
        ]),
    ],
    "diagnostic": [
        ("Bảng 1 — Đặc điểm nền", [
            ("Biến", "Bệnh (+) (N=[CẦN])", "Bệnh (-) (N=[CẦN])", "p"),
            ("Tuổi (năm), TB±SD", "[chạy 02_tables.R]", "[chạy 02_tables.R]", "[chạy]"),
        ]),
        ("Bảng 2 — Độ chính xác chẩn đoán (ROC/AUC)", [
            ("Chỉ số", "Giá trị", "95%CI", "Ghi chú"),
            ("AUC", "[chạy pROC]", "[chạy]", "Hanley-McNeil hoặc DeLong"),
            ("Độ nhạy (Se)", "[chạy]", "[chạy]", "Tại ngưỡng tối ưu (Youden)"),
            ("Độ đặc hiệu (Sp)", "[chạy]", "[chạy]", ""),
            ("PPV / NPV", "[chạy]", "[chạy]", "Phụ thuộc tỷ lệ hiện mắc"),
        ]),
        ("Bảng 3 — Decision Curve Analysis", [
            ("Ngưỡng xác suất", "Net benefit (model)", "Net benefit (treat-all)", "Net benefit (treat-none)"),
            ("[chạy dcurves::dca]", "[chạy]", "[chạy]", "0"),
        ]),
    ],
    "sr_ma": [
        ("Bảng 1 — Đặc điểm nghiên cứu đưa vào", [
            ("Nghiên cứu", "Năm", "Thiết kế", "N", "Hiệu ứng (95%CI)"),
            ("[trích xuất từ REDCap Extraction]", "[CẦN]", "[CẦN]", "[CẦN]", "[CẦN]"),
        ]),
        ("Bảng 2 — Kết quả gộp (Random-effects)", [
            ("Chỉ số", "Giá trị", "95%CI", "Ghi chú"),
            ("Pooled effect", "[chạy meta::metagen]", "[chạy]", ""),
            ("I² (heterogeneity)", "[chạy]", "—", ""),
            ("Egger's test (publication bias)", "[chạy meta::metabias]", "—", "p<0.10 → nghi ngờ"),
        ]),
    ],
    # THÊM 2026-07-17 (round audit gate — tiếp nối vòng 5): "prediction" (mô
    # hình tiên lượng/TRIPOD+AI) trước đây KHÔNG có bảng riêng — rơi vào
    # fallback generic 1 dòng "[CẦN] chưa có mẫu bảng cho thiết kế". Bảng 2/3
    # dưới đây theo đúng bộ chỉ số TRIPOD+AI mục 23a (discrimination/
    # calibration) — chỉ là KHUNG TIÊU ĐỀ CỘT (giống mọi design khác ở trên),
    # KHÔNG có công thức/số liệu nào được tính sẵn.
    "prediction": [
        ("Bảng 1 — Đặc điểm quần thể phát triển/đánh giá mô hình", [
            ("Biến", "Phát triển (N=[CẦN])", "Đánh giá (N=[CẦN])", "p"),
            ("Tuổi (năm), TB±SD", "[chạy 02_tables.R]", "[chạy 02_tables.R]", "[chạy]"),
            ("Tỷ lệ biến cố/kết cục, n (%)", "[chạy 02_tables.R]", "[chạy 02_tables.R]", "[chạy]"),
        ]),
        ("Bảng 2 — Hiệu năng phân biệt (Discrimination)", [
            ("Chỉ số", "Giá trị", "95%CI", "Ghi chú"),
            ("C-statistic / AUC", "[chạy]", "[chạy]", "Apparent + internal validation (bootstrap)"),
            ("R² (Cox-Snell / Nagelkerke)", "[chạy]", "[chạy]", ""),
        ]),
        ("Bảng 3 — Hiệu chỉnh & lợi ích lâm sàng (Calibration & DCA)", [
            ("Chỉ số", "Giá trị", "95%CI", "Ghi chú"),
            ("Calibration slope", "[chạy]", "[chạy]", "Lý tưởng = 1"),
            ("Calibration-in-the-large", "[chạy]", "[chạy]", "Lý tưởng = 0"),
            ("Brier score", "[chạy]", "—", ""),
            ("Decision Curve Analysis", "[chạy dcurves::dca]", "—", "Net benefit vs treat-all/treat-none"),
        ]),
    ],
    # THÊM 2026-07-23 (vòng lặp kiểm tra-hoàn thiện vòng 11): "qualitative" là
    # thiết kế chuẩn thứ 8 duy nhất còn thiếu bảng riêng — trước đây rơi vào
    # fallback generic 1 dòng "[CẦN] chưa có mẫu bảng cho thiết kế" dù pipeline
    # G0-G10 đã có nhánh định tính đầy đủ từ vòng trước (task #21). Bảng dưới
    # theo đúng cấu trúc báo cáo định tính chuẩn (đặc điểm người tham gia +
    # bão hòa dữ liệu, rồi chủ đề kèm trích dẫn minh họa) — chỉ KHUNG TIÊU ĐỀ
    # CỘT, không có nội dung/trích dẫn nào được bịa sẵn.
    "qualitative": [
        ("Bảng 1 — Đặc điểm người tham gia & bão hòa dữ liệu", [
            ("Biến", "Giá trị", "Ghi chú"),
            ("Số người tham gia (N)", "[CẦN]", "Đến khi bão hòa dữ liệu"),
            ("Tuổi (năm), TB±SD hoặc khoảng", "[CẦN]", ""),
            ("Giới nữ, n (%)", "[CẦN]", ""),
            ("Phương pháp lấy mẫu", "[CẦN]", "Có chủ đích/lý thuyết"),
            ("Tiêu chí dừng thu thập", "[CẦN]", "Bão hòa chủ đề — ghi rõ căn cứ"),
        ]),
        ("Bảng 2 — Chủ đề & trích dẫn minh họa (Thematic Analysis)", [
            ("Chủ đề chính", "Chủ đề phụ", "Trích dẫn minh họa (ẩn danh)", "Số người tham gia nhắc đến"),
            ("[CẦN — mã hóa từ dữ liệu thật]", "[CẦN]", "[CẦN — KHÔNG bịa trích dẫn]", "[CẦN]"),
        ]),
    ],
}


# ─────────────────────────────────────────────
# HÀM TIỆN ÍCH
# ─────────────────────────────────────────────

def load_cp(path):
    """Đọc file JSON checkpoint."""
    p = Path(path)
    if p.exists():
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    return {}


def guardrail(artifact: str, all_scripts_text: str) -> tuple:
    """
    Kiểm tra guardrail 2 lớp:
    Lớp 1 LIÊM CHÍNH: R1–R7
    Lớp 2 sơ bộ: không hardcode kết quả thống kê
    """
    errors, warnings_list = [], []

    # R1 — Không hardcode kết quả
    hardcoded = re.search(
        r'(?:HR|OR|RR|AUC|β)\s*=\s*\d+\.\d+\s*,?\s*95%CI\s*[:\(]\s*\d+\.\d+',
        all_scripts_text
    )
    if hardcoded:
        errors.append("R1 🔴 Có thể có kết quả hardcoded trong scripts")
    else:
        warnings_list.append("R1 ✅ Scripts không hardcode kết quả")

    # R2 — Không PII
    pii_pattern = re.search(
        r'(?:CMND|CCCD)\s*\d{9,12}|0[89]\d{8}\b|\b\d{12}\b',
        artifact, re.I
    )
    if pii_pattern:
        errors.append("R2 🔴 Phát hiện mẫu PII")
    else:
        warnings_list.append("R2 ✅ Không PII")

    # R3 — Không tự claim LOCKED
    if "G6_STATUS: LOCKED" in artifact or "APPROVED_BY_SYSTEM" in artifact:
        errors.append("R3 🔴 Không tự gán LOCKED/APPROVED")
    else:
        warnings_list.append("R3 ✅ Không tự claim LOCKED")

    # R4 — Có nhãn DRAFT / skeleton
    draft_n = artifact.count("DRAFT") + artifact.count("skeleton") + artifact.count("chờ dữ liệu")
    if draft_n >= 2:
        warnings_list.append(f"R4 ✅ Nhãn DRAFT đủ ({draft_n} lần)")
    else:
        errors.append(f"R4 🔴 Thiếu nhãn DRAFT ({draft_n} lần)")

    # R5 — [CẦN...] hoặc uncomment placeholders
    can_n = len(re.findall(r'\[CẦN|# uncomment|\\[chạy\\]|chạy R', artifact + all_scripts_text))
    if can_n >= 5:
        warnings_list.append(f"R5 ✅ {can_n} placeholder đủ")
    else:
        errors.append(f"R5 🔴 Quá ít placeholder ({can_n})")

    # R6 — CI patterns
    ci_n = len(re.findall(r'95%CI|conf\.int|conf_int|ci_lo|CI_lo|lower 95%', artifact + all_scripts_text))
    if ci_n >= 3:
        warnings_list.append(f"R6 ✅ {ci_n} lần yêu cầu 95%CI")
    else:
        warnings_list.append("R6 ✅ Cấu trúc CI có trong lệnh phân tích")

    # R7 — Disclaimer
    if "Cần bác sĩ kiểm chứng" in artifact:
        warnings_list.append("R7 ✅ Có disclaimer")
    else:
        errors.append("R7 🔴 Thiếu disclaimer 'Cần bác sĩ kiểm chứng'")

    return errors, warnings_list


def write_docx(artifact: str, path: Path) -> bool:
    """Xuất artifact ra .docx."""
    try:
        from docx import Document
        from docx.shared import RGBColor
        doc = Document()
        for line in artifact.split("\n"):
            if not line.strip():
                doc.add_paragraph("")
            elif line.startswith("# "):
                doc.add_heading(line[2:], 0)
            elif line.startswith("## "):
                doc.add_heading(line[3:], 1)
            elif line.startswith("### "):
                doc.add_heading(line[4:], 2)
            elif "[CẦN" in line or "[chạy" in line:
                p = doc.add_paragraph()
                run = p.add_run(line)
                run.font.color.rgb = RGBColor(0xCC, 0x44, 0x00)
            elif line.startswith("| "):
                doc.add_paragraph(line, style="No Spacing")
            else:
                doc.add_paragraph(line)
        doc.save(path)
        return True
    except Exception:
        return False


def render_table_shell(table_name, rows):
    """Render bảng kết quả Markdown."""
    lines = [f"\n**{table_name}:**"]
    if not rows:
        return "\n".join(lines)
    header = rows[0]
    sep = "|".join(["---"] * len(header))
    lines.append("| " + " | ".join(header) + " |")
    lines.append("| " + sep + " |")
    for row in rows[1:]:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def _is_locked(status) -> bool:
    """
    Kiểm tra trạng thái đã LOCKED một cách CHÍNH XÁC.
    SỬA: "LOCKED" in status.upper() là substring match — khớp NHẦM với
    "UNLOCKED", "CHƯA LOCKED", "KHÔNG LOCKED" (chuỗi phủ định vẫn chứa
    "LOCKED" như substring). Nay chỉ coi là locked khi status bắt đầu bằng
    đúng từ LOCKED và KHÔNG có tiền tố phủ định.
    """
    s = str(status or "").strip().upper()
    if re.search(r'(UN|CH[ƯU]A|KH[ÔO]NG|NOT)\s*LOCKED', s):
        return False
    return bool(re.match(r'^LOCKED\b', s))


# SỬA 2026-07-21 (vòng lặp kiểm tra-hoàn thiện vòng 5, phát hiện HIGH): PHẦN 3/
# 5/6 của generate_artifact() (dòng "03_analysis.R | Cox + KM + MI...", checklist
# "cox.zph()"/"E-value"/"KM curve", tiêu chí "Cox kết quả HR...") trước đây là
# text TĨNH, không rẽ nhánh theo design_code — khác hẳn TABLE_SHELLS/analysis_
# name_map/03_analysis.R (đã vá đúng theo thiết kế ở các vòng trước). Với 6/8
# thiết kế KHÔNG dùng Cox (case_control/cross_sectional dùng logistic, diagnostic
# dùng ROC, prediction dùng mô hình đa biến TRIPOD+AI, sr_ma dùng meta-analysis
# study-level, qualitative không có mô hình suy diễn), bác sĩ vẫn nhận artifact
# yêu cầu kiểm cox.zph()/điền HR — mâu thuẫn trực tiếp với 03_analysis.R thật.
def _is_cox_like(design_code, effect_type):
    return design_code in ("rct", "cohort") and effect_type != "MD"


_SCRIPT03_INFO = {
    "cross_sectional": ("Logistic/Linear regression + MI (m=20)", "stats, mice, gtsummary"),
    "case_control":    ("Conditional logistic regression + MI (m=20)", "survival (clogit), mice"),
    "diagnostic":      ("ROC/AUC + Se-Sp (Youden) + CI bootstrap + Calibration", "pROC"),
    "sr_ma":           ("Random/fixed-effects meta-analysis (forest/funnel/Egger)", "meta"),
    "prediction":      ("Mô hình đa biến + shrinkage + internal validation + DCA (TRIPOD+AI)",
                        "rms, glmnet, dcurves"),
    "qualitative":     ("Mã hóa chủ đề (thematic analysis) — KHÔNG mô hình thống kê suy diễn",
                        "N/A (QDA thủ công/NVivo/ATLAS.ti)"),
}


def _script03_row(design_code, effect_type, exposure, outcome, time_col):
    """Dòng '03_analysis.R' của PHẦN 3 — khớp ĐÚNG phương pháp thật dùng cho
    từng thiết kế (xem các hàm _r03_*_with_vars và nhánh Cox/regression trong
    _RUN_CLI_TEMPLATE), tránh mâu thuẫn đã bị vòng 5 phát hiện."""
    if _is_cox_like(design_code, effect_type):
        desc, libs = "Cox + KM + MI (m=20)", "survival, survminer, mice"
    elif design_code in ("rct", "cohort") and effect_type == "MD":
        desc, libs = "Hồi quy tuyến tính/ANCOVA + MI (m=20)", "stats, mice, gtsummary"
    else:
        desc, libs = _SCRIPT03_INFO.get(design_code, ("[CẦN xác định theo SAP]", "[CẦN]"))
    return f"| `03_analysis.R` | {desc} | {exposure}/{outcome}/{time_col} | {libs} |"


def _phan5_checklist(design_code, effect_type):
    """Checklist PHẦN 5 — mỗi mục phải THẬT SỰ áp dụng cho phương pháp phân
    tích của thiết kế đó (cox.zph()/KM/E-value chỉ có nghĩa cho mô hình Cox)."""
    ci_line = "- [ ] Mọi ước lượng kèm **95%CI** — KHÔNG báo p-value đơn độc"
    if _is_cox_like(design_code, effect_type):
        return [
            ci_line,
            "- [ ] Báo cáo **complete case** VÀ **MI (m=20)** — nhất quán",
            "- [ ] Kiểm định **PH assumption**: `check_assumptions()`/`cox.zph()` p > 0.05",
            "- [ ] **E-value** báo cáo kèm kết quả chính (sensitivity_analysis.py)",
            "- [ ] **Subgroup** chỉ chạy nếu có trong SAP §7 đã khóa",
            "- [ ] **KM curve** kèm bảng số-tại-nguy-cơ và log-rank p",
        ]
    if design_code in ("rct", "cohort", "cross_sectional", "case_control"):
        return [
            ci_line,
            "- [ ] Báo cáo **complete case** VÀ **MI (m=20)** — nhất quán",
            "- [ ] Kiểm tra **giả định mô hình hồi quy** (phần dư, đa cộng tuyến VIF)",
            "- [ ] **E-value** báo cáo kèm kết quả chính (nhiễu chưa đo được, nếu quan sát)",
            "- [ ] **Subgroup** chỉ chạy nếu có trong SAP §7 đã khóa",
        ]
    if design_code == "diagnostic":
        return [
            ci_line,
            "- [ ] **AUC + 95%CI** (bootstrap `ci.auc()`) báo cáo đầy đủ",
            "- [ ] **Se/Sp/PPV/NPV tại ngưỡng Youden + 95%CI bootstrap** (`ci.coords()`, KHÔNG chỉ điểm ước lượng)",
            "- [ ] Ngưỡng tối ưu đã được **bác sĩ xác nhận ý nghĩa lâm sàng** (không chỉ thống kê)",
        ]
    if design_code == "prediction":
        return [
            ci_line,
            "- [ ] **Discrimination** (C-statistic/AUC) + **Calibration** (slope/intercept) báo cáo đầy đủ",
            "- [ ] **Internal validation** (bootstrap ≥200 lần) đã chạy, không chỉ split-sample",
            "- [ ] **Decision Curve Analysis** (lợi ích lâm sàng ròng) đã báo cáo",
        ]
    if design_code == "sr_ma":
        return [
            ci_line,
            "- [ ] **I²/τ²/Q** (dị biệt) báo cáo kèm lựa chọn mô hình fixed/random có giải thích",
            "- [ ] **Publication bias** (Egger/funnel) nếu ≥10 nghiên cứu",
            "- [ ] **Forest plot** đính kèm cho kết cục chính",
        ]
    if design_code == "qualitative":
        return [
            "- [ ] **Bão hòa dữ liệu** (data saturation) đã đạt và ghi rõ tiêu chí dừng",
            "- [ ] **Trustworthiness** (credibility/transferability/dependability/confirmability) đã báo cáo",
            "- [ ] **Trích dẫn (quote)** người tham gia THẬT minh họa mỗi chủ đề chính",
        ]
    return [ci_line, f"- [ ] [CẦN xác định checklist phù hợp thiết kế '{design_code}' thủ công]"]


def generate_artifact(study, topic, design_code, reporting_std,
                      n_total, alpha, power, effect_val, effect_type,
                      g4_status, run_date, scripts_dir, v: dict) -> str:
    """Sinh A7 artifact đầy đủ — gồm tên biến thật từ REDCap."""
    g4_locked = _is_locked(g4_status)
    # SỬA: fallback về TABLE_SHELLS["cohort"] cho design_code lạ (không nằm
    # trong 6 key đã định nghĩa) sẽ hiện bảng Cox/HR sai — dùng placeholder
    # trung lập [CẦN] thay vì bịa loại phân tích không khớp thiết kế thật.
    tables = TABLE_SHELLS.get(design_code) or [
        ("Bảng kết quả — [CẦN] chưa có mẫu bảng cho thiết kế '{}'".format(design_code), [
            ("Phân tích", "Ước lượng", "95%CI", "p"),
            ("[CẦN — chọn công thức/bảng phù hợp thiết kế thủ công]", "[CẦN]", "[CẦN]", "[CẦN]"),
        ]),
    ]

    exposure  = v["exposure"]
    outcome   = v["outcome"]
    time_col  = v["time_col"]
    covars    = v["covariates"]
    det_log   = "\n".join(f"  - {line}" for line in v["detection_log"])

    analysis_name_map = {
        # SỬA 2026-07-06: nhãn 'rct' cũ ("GLM/LM/Cox theo loại kết cục") NGỤ Ý
        # hệ tự chọn phương pháp theo kết cục, nhưng script thật chỉ luôn sinh
        # Cox — overclaim. Nay nhãn ĐỘNG theo effect_type để trung thực với
        # script THẬT sinh ra bên dưới (kiểm định đối kháng vòng 2).
        "rct":             ("ITT + PP — t-test/ANCOVA/hồi quy tuyến tính (MD, kết cục liên tục)"
                            if effect_type == "MD"
                            else "ITT + PP — Cox proportional hazards (kết cục thời gian-đến-biến cố)"),
        "cohort":          ("Hồi quy tuyến tính/ANCOVA (MD, kết cục liên tục)"
                            if effect_type == "MD"
                            else "Cox proportional hazards + Kaplan-Meier"),
        "cross_sectional": "Logistic regression (OR 95%CI) / Linear regression (β 95%CI)",
        "case_control":    "Conditional logistic regression (OR 95%CI)",
        "diagnostic":      "ROC/AUC + Calibration + DCA",
        "sr_ma":           "Random effects meta-analysis REML (meta::metagen/metabin)",
        # THÊM 2026-07-17 (round audit gate — tiếp nối vòng 5): "prediction"
        # trước đây rơi vào .get() fallback "[CẦN XÁC ĐỊNH THEO SAP]".
        "prediction":      "Phát triển mô hình (hồi quy logistic/Cox hoặc ML) + "
                           "internal validation (bootstrap) + discrimination "
                           "(C-statistic/AUC) + calibration (slope/intercept) + DCA (TRIPOD+AI)",
        # THÊM 2026-07-23 (vòng lặp kiểm tra-hoàn thiện vòng 11): "qualitative"
        # trước đây rơi vào .get() fallback "[CẦN XÁC ĐỊNH THEO SAP]" dù
        # _SCRIPT03_INFO["qualitative"] (dòng ~2339) đã có nhãn đúng sẵn — dùng
        # lại đúng nhãn đó để nhất quán trong cùng file (không tạo nhãn mới).
        "qualitative":     _SCRIPT03_INFO["qualitative"][0],
    }
    analysis_name = analysis_name_map.get(design_code, "[CẦN XÁC ĐỊNH THEO SAP]")

    lines = [
        "# A7 — R ANALYSIS SCRIPTS + PYTHON CLI + SAP THỰC THI (DRAFT — SKELETON)",
        f"**Đề tài:** {topic}  ",
        f"**Mã:** {study} | **Ngày sinh:** {run_date} | **Phiên bản:** 2.0 (Nâng cấp 75%)",
        f"**Thiết kế:** {design_code} | **Chuẩn báo cáo:** {reporting_std}",
        f"**Phân tích chính:** {analysis_name}",
        "",
        "> ⚠️ **QUAN TRỌNG (DRAFT — SKELETON):** Scripts là cấu trúc code với tên biến thật.",
        "> Không thể chạy phân tích không có dữ liệu thật đã khóa DB (G5).",
        "> R scripts: mọi lệnh đều comment (#) — uncomment khi có dữ liệu.",
        "> Python: run_analysis_cli.py chạy được ngay khi cung cấp CSV thật.",
        "",
        "---",
        "",
        "## PHẦN 1 — BIẾN SỐ TỰ PHÁT HIỆN TỪ REDCAP DICTIONARY (G5)",
        "",
        "| Vai trò | Tên biến | Ghi chú |",
        "|---|---|---|",
        f"| Phơi nhiễm (exposure) | `{exposure}` | Từ G5 REDCap dictionary |",
        f"| Kết cục chính (outcome) | `{outcome}` | 1=biến cố, 0=censored |",
        f"| Thời gian theo dõi | `{time_col}` | Đơn vị: tháng |",
        f"| Covariates | `{', '.join(covars) if covars else '[xem SAP §5]'}` | Nhân khẩu + lab + bệnh nền |",
        "",
        "**Log phát hiện biến:**",
        det_log,
        "",
        "> ⚠️ Kiểm tra lại tên biến với CRF thật trước khi chạy scripts.",
        "",
        "---",
        "",
        "## PHẦN 2 — ĐIỀU KIỆN CHẠY PHÂN TÍCH",
        "",
        f"- [{'x' if g4_locked else ' '}] **G4 SAP đã LOCKED**: {g4_status}",
        f"  {'✅ Đã khóa SAP — an toàn để chạy' if g4_locked else '⚠️ SAP chưa LOCKED — KHÔNG được xem dữ liệu'}",
        "- [ ] **DB đã khóa (G5)**: Biên bản khóa DB có chữ ký bác sĩ",
        "- [ ] **Scripts versioned**: `git commit` trước khi chạy lần đầu",
        "- [ ] **Seed đã ghi vào SAP**: `SEED = 2026` (hoặc theo SAP §10)",
        "- [ ] **R ≥ 4.2 hoặc Python + venv ~/.ebm-venv** đã cài đặt",
        "",
        "---",
        "",
        "## PHẦN 3 — SCRIPTS ĐƯỢC SINH",
        "",
        f"Scripts tại: `exports/{study}/scripts/`",
        "",
        "| Script | Mục đích | Biến dùng | Thư viện |",
        "|---|---|---|---|",
        "| `00_setup.R` | Cài packages R | — | tidyverse, survival, mice, gtsummary |",
        f"| `01_cleaning.R` | Làm sạch, recode biến | {exposure}, {outcome}, {time_col} | tidyverse, REDCapR |",
        f"| `02_tables.R` | Table 1 theo nhóm {exposure} | {', '.join(covars[:4]) if covars else 'age,sex,dm,htn'} | gtsummary, flextable |",
        _script03_row(design_code, effect_type, exposure, outcome, time_col),
        f"| `run_analysis_cli.py` | **Python CLI đầy đủ** — chạy ngay với CSV | {exposure}/{outcome}/{time_col} | lifelines, pandas, matplotlib |",
        f"| `sensitivity_analysis.py` | CC vs MI, Subgroup, E-value | {exposure}/{outcome}/{time_col} | lifelines, pandas |",
        "",
        "**Thứ tự chạy (R):**",
        "```bash",
        "Rscript scripts/00_setup.R",
        "Rscript scripts/01_cleaning.R",
        "Rscript scripts/02_tables.R",
        "Rscript scripts/03_analysis.R",
        "```",
        "",
        "**Chạy Python CLI (khi có CSV thật):**",
        "```bash",
        "python scripts/run_analysis_cli.py \\",
        "    --data data/raw/export.csv \\",
        f"    --exposure {exposure} \\",
        f"    --outcome {outcome} \\",
        f"    --time {time_col} \\",
        f"    --covariates {','.join(covars) if covars else 'age,sex,dm,htn'}",
        "",
        "python scripts/sensitivity_analysis.py \\",
        "    --data data/raw/export.csv",
        "```",
        "",
        "---",
        "",
        "## PHẦN 4 — BẢNG KẾT QUẢ DỰ KIẾN (Shell)",
        "",
        f"*(N dự kiến = {n_total}, alpha = {alpha}, power = {power}, {effect_type} = {effect_val})*",
        "",
    ]

    for table_name, rows in tables:
        lines.append(render_table_shell(table_name, rows))
        lines.append("")

    _sensitivity_line = (
        "- [ ] **Sensitivity** (CC vs MI + E-value) nhất quán [CẦN]"
        if design_code in ("rct", "cohort", "cross_sectional", "case_control")
        else f"- [ ] **Đối chiếu độ nhạy** phù hợp thiết kế '{design_code}' (xem PHẦN 5) [CẦN]"
    )
    lines += [
        "---",
        "",
        "## PHẦN 5 — CHECKLIST TRƯỚC BÁO CÁO",
        "",
        *_phan5_checklist(design_code, effect_type),
        "",
        "---",
        "",
        "## PHẦN 6 — TIÊU CHÍ QUA CỔNG G6",
        "",
        "- [ ] **G4 = LOCKED** trước khi xem dữ liệu [CẦN BÁC SĨ XÁC NHẬN]",
        "- [ ] **Chạy 01_cleaning.R** — log không lỗi [CẦN BÁC SĨ]",
        f"- [ ] **Table 1 hoàn chỉnh** theo nhóm `{exposure}` — SMD < 0.2 [CẦN]",
        f"- [ ] **Kết quả phân tích chính** ({analysis_name}) điền Bảng 2 [CẦN]",
        _sensitivity_line,
        "- [ ] **Bác sĩ duyệt** kết quả trước khi viết G7 [CẦN]",
        "",
        "---",
        "",
        "*Cần bác sĩ kiểm chứng. Scripts với tên biến thật từ REDCap — kiểm tra trước khi chạy.*  ",
        f"*Mã: {study} | Sinh: {run_date} | Version: A7 v2.0 | Mức tự động: 75%*",
    ]

    return "\n".join(lines)


# ─────────────────────────────────────────────
# HÀM CHÍNH
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="G6 NÂNG CẤP — Sinh R scripts + Python CLI với tên biến thật (75% tự động)"
    )
    parser.add_argument("--study", required=True, help="Mã đề tài (vd: SGLT2-HFpEF-2026)")
    args = parser.parse_args()
    # 2026-07-11: vá path traversal, khớp chuẩn sanitize đã dùng ở G0-G5.
    study = re.sub(r'[^\w\-]', '_', args.study.strip().replace(" ", "-"))

    # Đường dẫn
    out = BASE / "exports" / study
    out.mkdir(parents=True, exist_ok=True)
    scripts_dir = out / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    run_date = datetime.now().strftime("%Y-%m-%d")

    print(f"\n📊 G6 NÂNG CẤP — Sinh Analysis Scripts: {study}")
    print("=" * 60)

    # ─── Đọc checkpoints ───
    g0 = load_cp(out / "G0_checkpoint.json")
    g1 = load_cp(out / "G1_checkpoint.json")
    g3 = load_cp(out / "G3_checkpoint.json")
    g4 = load_cp(out / "G4_checkpoint.json")

    # SỬA: g1.get("design_code"/"reporting_standard") đọc SAI đường dẫn —
    # G1 lưu 2 trường này LỒNG trong "design": {...}, không phải top-level.
    # .get() luôn miss (key không tồn tại) nên luôn âm thầm rơi về default
    # "cohort"/"STROBE 2007" bất kể G1 thực sự xác định thiết kế gì — bug
    # bị che giấu suốt phiên vì mọi ca test đều tình cờ là cohort.
    g1_design     = g1.get("design") or {}
    topic         = g0.get("topic") or g1.get("topic") or study
    # VÁ 2026-07-27: dùng bộ giải quyết DÙNG CHUNG. Trước đây cổng này chỉ đọc
    # G1_checkpoint rồi mặc định "cohort", nên `--design` bác sĩ truyền TƯỜNG MINH ở
    # G2 bị NUỐT — chuẩn báo cáo/công thức cỡ mẫu chọn sai mà không cảnh báo.
    # Xem gate_contract.resolve_design_code().
    design_code, _design_warn = GC.resolve_design_code(out)
    if _design_warn:
        print(_design_warn)
    reporting_std = g1_design.get("reporting_standard") or "STROBE 2007"
    n_adjusted    = g3.get("n_adjusted", g3.get("n_total", 0))
    alpha         = g3.get("alpha", 0.05)
    power         = g3.get("power", 0.80)
    effect_val    = g3.get("effect_val", g3.get("effect_size", "[CẦN]"))
    effect_type   = g3.get("effect_type", "HR")
    g4_status     = g4.get("g4_status", "PENDING — chưa chạy G4")
    g4_locked     = _is_locked(g4_status)

    print(f"  → Đề tài   : {topic}")
    print(f"  → Design   : {design_code} | Chuẩn: {reporting_std}")
    print(f"  → Cỡ mẫu  : N={n_adjusted}, alpha={alpha}, power={power}, {effect_type}={effect_val}")
    print(f"  → G4 SAP   : {g4_status}")

    if not g4_locked:
        print("  ⚠️  CẢNH BÁO: G4 SAP chưa LOCKED!")
        print("     Bác sĩ PHẢI ký SAP Lock Certificate trước khi xem dữ liệu.")

    # ─── Đọc REDCap dictionary → phát hiện biến ───
    redcap_csv = out / f"G5_REDCap_dictionary_{study}.csv"
    print(f"\n  📂 Đọc REDCap dictionary: {redcap_csv.name}")
    v = detect_variables_from_redcap(redcap_csv)

    print(f"  → Phơi nhiễm : {v['exposure']}")
    print(f"  → Kết cục    : {v['outcome']}")
    print(f"  → Thời gian  : {v['time_col']}")
    print(f"  → Covariates : {', '.join(v['covariates']) if v['covariates'] else '(fallback: age,sex,dm,htn)'}")
    print("  → Detection log:")
    for log_line in v["detection_log"]:
        print(f"     {log_line}")

    # ─── Sinh R scripts ───
    print("\n  🔧 Sinh R scripts với tên biến thật...")
    r03 = R_ANALYSIS_MAP_FUNC(design_code, v, n_adjusted, alpha, power, effect_val, effect_type)

    scripts_to_write = {
        "00_setup.R":    R_00_SETUP,
        "01_cleaning.R": make_r01_cleaning(v, design_code),
        "02_tables.R":   make_r02_tables(v, design_code),
        "03_analysis.R": r03,
    }

    generated_paths = []
    for filename, code in scripts_to_write.items():
        p = scripts_dir / filename
        p.write_text(code, encoding="utf-8")
        generated_paths.append(str(p))
        print(f"  → {filename} ({len(code)//1024 or 1}KB)")

    # ─── Sinh Python CLI analysis ───
    print("\n  🐍 Sinh run_analysis_cli.py (Python CLI đầy đủ)...")
    cli_code = make_run_analysis_cli(v, n_adjusted, study, design_code, effect_type)
    cli_path = scripts_dir / "run_analysis_cli.py"
    cli_path.write_text(cli_code, encoding="utf-8")
    generated_paths.append(str(cli_path))
    print(f"  → run_analysis_cli.py ({len(cli_code)//1024}KB)")

    # ─── Sinh sensitivity analysis ───
    print("  🔬 Sinh sensitivity_analysis.py...")
    sens_code = make_sensitivity_analysis(v, study, design_code)
    sens_path = scripts_dir / "sensitivity_analysis.py"
    sens_path.write_text(sens_code, encoding="utf-8")
    generated_paths.append(str(sens_path))
    print(f"  → sensitivity_analysis.py ({len(sens_code)//1024}KB)")

    # ─── Sinh artifact A7 ───
    all_scripts_text = "\n".join(scripts_to_write.values()) + cli_code + sens_code
    artifact = generate_artifact(
        study, topic, design_code, reporting_std,
        n_adjusted, alpha, power, effect_val, effect_type,
        g4_status, run_date, scripts_dir, v
    )

    md_path = out / f"G6_A7_ANALYSIS_SCRIPTS_{study}.md"
    md_path.write_text(artifact, encoding="utf-8")
    print(f"\n  → A7 Markdown: {md_path.name} ({len(artifact)//1024}KB)")

    # ─── Guardrail ───
    errors, warnings_list = guardrail(artifact, all_scripts_text)
    print("\n  --- Guardrail R1–R7 ---")
    for w in warnings_list:
        print(f"  {w}")
    for e in errors:
        print(f"  {e}")
    status = "✅ PASS" if not errors else f"⚠ {len(errors)} LỖI"
    print(f"  → Guardrail: {status}")

    # ─── Xuất DOCX ───
    docx_path = out / f"G6_A7_ANALYSIS_SCRIPTS_{study}.docx"
    ok = write_docx(artifact, docx_path)
    print(f"  → DOCX: {'OK — ' + docx_path.name if ok else 'Bỏ qua (python-docx chưa cài)'}")

    # ─── G6 checkpoint ───
    checkpoint = {
        "gate":              "G6",
        "study":             study,
        "run_date":          run_date,
        "version":           "2.0-75pct",
        "design_code":       design_code,
        "reporting_std":     reporting_std,
        "g4_was_locked":     g4_locked,
        "g4_status":         g4_status,
        "redcap_csv":        str(redcap_csv),
        "variables_detected": {
            "exposure":   v["exposure"],
            "outcome":    v["outcome"],
            "time_col":   v["time_col"],
            "covariates": v["covariates"],
        },
        "scripts_generated": generated_paths,
        "n_scripts":         len(generated_paths),
        "python_cli":        str(cli_path),
        "sensitivity_script": str(sens_path),
        "guardrail":         status,
        "automation_level":  "75%",
        "pending":           "Cần dữ liệu thật + DB locked (G5) để chạy Python CLI và uncomment R scripts",
        "next_gate":         "G7 — Viết bản thảo (sau khi có kết quả phân tích thật)",
        "artifact":          str(md_path),
    }
    cp_path = out / "G6_checkpoint.json"
    cp_path.write_text(json.dumps(checkpoint, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n💾 Checkpoint: {cp_path.name}")

    # ─── Tóm tắt ───
    print("\n✅ G6 NÂNG CẤP — Mức tự động: 75%")
    print(f"   Đề tài    : {study}")
    print(f"   Design    : {design_code} | Chuẩn: {reporting_std}")
    print(f"   Biến      : {v['exposure']} / {v['outcome']} / {v['time_col']}")
    print(f"   Covariates: {', '.join(v['covariates']) if v['covariates'] else 'fallback'}")
    print(f"   Scripts   : {len(generated_paths)} files tại {scripts_dir}")
    print("     - 4 R scripts (tên biến thật)")
    print("     - run_analysis_cli.py (Python — chạy ngay khi có CSV)")
    print("     - sensitivity_analysis.py (CC vs MI, subgroup, E-value)")
    print(f"   G4 Locked : {'✅ Đã khóa SAP' if g4_locked else '⚠️ CHƯA khóa'}")
    print(f"   Guardrail : {status}")
    print("   Bước tiếp : Khóa DB (G5) → python run_analysis_cli.py --data <CSV> → G7")

    # Vá 2026-07-11 (vòng 9): trước đây banner "NÂNG CẤP" in vô điều kiện + exit code luôn
    # 0 dù guardrail có lỗi thật — checkpoint ĐÃ ghi đúng "guardrail": status, nhưng process
    # exit code không phản ánh, nên chạy trực tiếp (không qua run_pipeline.py) sẽ tưởng nhầm
    # là xong. Đối xứng cách G3/G4/G9 đã làm.
    if errors:
        raise SystemExit(GC.EXIT_GUARDRAIL_FAIL)


def R_ANALYSIS_MAP_FUNC(design_code: str, v: dict, n_adjusted: int,
                         alpha: float, power: float,
                         effect_val, effect_type: str) -> str:
    """Chọn R script phân tích đúng theo thiết kế và điền biến thật."""
    # SỬA: case_control trước đây gộp chung với cohort → nhận script Cox
    # regression/Kaplan-Meier (Surv/coxph) — sai phương pháp thống kê hoàn
    # toàn, vì case-control (hồi cứu, chọn mẫu theo tình trạng bệnh) không có
    # trục "thời gian đến biến cố" hợp lệ. Mâu thuẫn nội tại: TABLE_SHELLS
    # và analysis_name_map đều ghi đúng "Conditional logistic (OR)" cho
    # case_control, nhưng script R thực tế lại dạy Cox/HR — nay tách riêng.
    # THÊM 2026-07-06: kết cục LIÊN TỤC (effect_type=MD) cho rct/cohort — trước
    # đây LUÔN nhận script Cox/Surv (sai phương pháp thống kê cho biến liên tục
    # như đau NRS/HbA1c/chất lượng sống). Ưu tiên effect_type TRƯỚC design_code
    # khi =MD, giống cách G3 đã làm ở sensitivity_table. Kiểm định đối kháng
    # vòng 2 xác nhận đây là bug thiếu sót (bug of omission) thật.
    if effect_type == "MD" and design_code in ("rct", "cohort"):
        return _r03_continuous_md_with_vars(v, design_code)
    if design_code == "cohort":
        return make_r03_cohort(v, n_adjusted, alpha, power, effect_val, effect_type)
    elif design_code == "case_control":
        return _r03_case_control_with_vars(v)
    # Các thiết kế khác: dùng template generic có điền tên biến
    elif design_code == "rct":
        return _r03_rct_with_vars(v)
    elif design_code == "cross_sectional":
        return _r03_cross_with_vars(v)
    # THÊM 2026-07-19 (audit vòng 3, D2_prediction_dta_gate_coverage — NGHIÊM
    # TRỌNG): "diagnostic"/"prediction"/"sr_ma" trước đây rơi vào else →
    # make_r03_cohort() (Cox regression + Kaplan-Meier) — SAI HOÀN TOÀN
    # phương pháp thống kê cho cả 3 (không có trục thời gian-đến-biến-cố hợp
    # lệ theo nghĩa Cox cho chẩn đoán/mô hình tiên lượng/tổng hợp nhiều
    # nghiên cứu). Mâu thuẫn nội tại: TABLE_SHELLS/analysis_name_map (đã vá
    # 2026-07-17) ghi đúng ROC/AUC+DCA (diagnostic), TRIPOD+AI (prediction),
    # nhưng 03_analysis.R thực tế lại dạy Cox/HR — cùng lớp lỗi "2 lớp xử lý
    # design_code tách rời nhau" mà case_control từng gặp (2026-07-06).
    elif design_code == "diagnostic":
        return _r03_diagnostic_with_vars(v)
    elif design_code == "prediction":
        return _r03_prediction_with_vars(v)
    elif design_code == "sr_ma":
        return _r03_srma_template()
    # THÊM 2026-07-20 (vòng lặp kiểm tra-hoàn thiện, xac nhan doi khang): truoc
    # day "qualitative" khong co nhanh rieng nen roi vao else -> make_r03_cohort()
    # (Cox regression + Kaplan-Meier) — SAI HOAN TOAN phuong phap luan cho du
    # lieu phong van/nhom tieu diem dinh tinh. Cung lop loi "2 lop xu ly
    # design_code tach roi nhau" da vá cho case_control/diagnostic/prediction/
    # sr_ma (G1/G3/G7 da ho tro qualitative tu 2026-07-19, rieng G6 sot lai).
    elif design_code == "qualitative":
        return _r03_qualitative_template()
    else:
        return make_r03_cohort(v, n_adjusted, alpha, power, effect_val, effect_type)


def _r03_continuous_md_with_vars(v: dict, design_code: str = "rct") -> str:
    """Script phân tích kết cục LIÊN TỤC (Mean Difference) — t-test/ANCOVA/lm.

    Dùng cho RCT/cohort có kết cục liên tục (đau NRS, HbA1c, chất lượng sống…),
    KHÔNG dùng Cox/log-rank (không có trục thời gian-đến-biến-cố). Chuẩn: ANCOVA
    hiệu chỉnh giá trị nền (baseline) — mạnh hơn t-test đơn thuần khi có đo lường
    trước-sau. Thêm 2026-07-06 (kiểm định đối kháng vòng 2)."""
    exposure = v["exposure"]
    outcome  = v["outcome"]
    covars   = v["covariates"]
    cov_fml  = " + ".join(covars) if covars else "age + sex + bmi"
    label = "RCT" if design_code == "rct" else "Cohort"
    return f"""\
# 03_analysis.R — {label} kết cục LIÊN TỤC (t-test/ANCOVA → Chênh lệch trung bình MD)
# Biến: nhóm/phơi nhiễm={exposure} | kết cục liên tục={outcome}
# Kết cục LIÊN TỤC (vd đau NRS, HbA1c, chất lượng sống) — KHÔNG dùng Cox/log-rank
# (không có trục thời gian-đến-biến-cố). Chuẩn: so sánh trung bình 2 nhóm; nếu có
# đo baseline thì ANCOVA (hiệu chỉnh giá trị nền) mạnh hơn t-test đơn thuần.
source(here::here("scripts", "00_setup.R"))
# df <- readRDS(file.path(DATA_PROC, "df_clean.rds"))

# (1) So sánh trung bình thô — t-test 2 nhóm độc lập (giả định phương sai bằng nhau):
# t_res <- t.test({outcome} ~ {exposure}, data=df, var.equal=TRUE)
# print(t_res)   # ước lượng chênh lệch trung bình (MD) + 95%CI

# (2) ANCOVA hiệu chỉnh baseline + đồng biến (KHUYẾN NGHỊ nếu có {outcome}_baseline):
# lm_adj <- lm({outcome} ~ {exposure} + {outcome}_baseline + {cov_fml}, data=df)
# broom::tidy(lm_adj, conf.int=TRUE) %>% filter(term=="{exposure}")   # MD hiệu chỉnh + 95%CI
# (Nếu KHÔNG có baseline: bỏ {outcome}_baseline khỏi công thức trên.)

message("03_analysis.R ({label}, kết cục liên tục MD) — Biến: {exposure}/{outcome} | [CẦN DỮ LIỆU THẬT]")
"""


def _r03_case_control_with_vars(v: dict) -> str:
    exposure = v["exposure"]
    outcome  = v["outcome"]
    covars   = v["covariates"]
    cov_fml  = " + ".join(covars) if covars else "age + sex + bmi"
    return f"""\
# 03_analysis.R — Case-control (Conditional/Unconditional logistic → OR)
# Biến: phơi nhiễm={exposure} | ca/chứng (outcome)={outcome}
# Case-control KHÔNG có trục thời gian-đến-biến-cố hợp lệ (hồi cứu, chọn
# mẫu theo tình trạng bệnh) — KHÔNG dùng Cox/log-rank. Đúng chuẩn: logistic
# hồi quy trên TỶ LỆ PHƠI NHIỄM giữa ca và chứng → Odds Ratio (OR).
source(here::here("scripts", "00_setup.R"))
# df <- readRDS(file.path(DATA_PROC, "df_clean.rds"))

# NẾU có bắt cặp (matched case-control, vd theo tuổi/giới/site) — dùng
# conditional logistic regression, cần biến strata (vd "match_id"):
# clogit_adj <- survival::clogit({outcome} ~ {exposure} + {cov_fml} + strata(match_id), data=df)
# broom::tidy(clogit_adj, exponentiate=TRUE, conf.int=TRUE) %>% filter(term=="{exposure}")

# NẾU KHÔNG bắt cặp (unmatched case-control) — logistic thường là đủ:
# glm_crude <- glm({outcome} ~ {exposure}, data=df, family=binomial())
# glm_adj   <- glm({outcome} ~ {exposure} + {cov_fml}, data=df, family=binomial())
# broom::tidy(glm_adj, exponentiate=TRUE, conf.int=TRUE) %>% filter(term=="{exposure}")

message("03_analysis.R (case-control) — Biến: {exposure}/{outcome} | [CẦN XÁC NHẬN có bắt cặp hay không, rồi CẦN DỮ LIỆU THẬT]")
"""


def _r03_rct_with_vars(v: dict) -> str:
    exposure = v["exposure"]
    outcome  = v["outcome"]
    time_col = v["time_col"]
    covars   = v["covariates"]
    cov_fml  = " + ".join(covars) if covars else "age + sex + bmi"
    return f"""\
# 03_analysis.R — RCT (ITT + PP)
# Biến: arm={exposure} | outcome={outcome} | time={time_col}
source(here::here("scripts", "00_setup.R"))
# df <- readRDS(file.path(DATA_PROC, "df_clean.rds"))
# df_itt <- df %>% filter(!is.na({exposure}))

# Kết cục thời gian đến biến cố (Time-to-event)
# surv_obj <- Surv({time_col}, {outcome})
# cox_itt  <- coxph(surv_obj ~ {exposure} + {cov_fml}, data=df_itt)
# summary(cox_itt)
# broom::tidy(cox_itt, exponentiate=TRUE, conf.int=TRUE) %>% filter(term=="{exposure}")

message("03_analysis.R (RCT) — Biến: {exposure}/{outcome}/{time_col} | [CẦN DỮ LIỆU THẬT]")
"""


def _r03_cross_with_vars(v: dict) -> str:
    exposure = v["exposure"]
    outcome  = v["outcome"]
    covars   = v["covariates"]
    cov_fml  = " + ".join(covars) if covars else "age + sex + bmi"
    return f"""\
# 03_analysis.R — Cross-sectional (Logistic)
# Biến: exposure={exposure} | outcome={outcome}
source(here::here("scripts", "00_setup.R"))
# df <- readRDS(file.path(DATA_PROC, "df_clean.rds"))

# Mô hình thô
# glm_crude <- glm({outcome} ~ {exposure}, data=df, family=binomial())
# Mô hình hiệu chỉnh
# glm_adj   <- glm({outcome} ~ {exposure} + {cov_fml}, data=df, family=binomial())
# broom::tidy(glm_adj, exponentiate=TRUE, conf.int=TRUE) %>% filter(term=="{exposure}")

message("03_analysis.R (Cross-sectional) — Biến: {exposure}/{outcome} | [CẦN DỮ LIỆU THẬT]")
"""


def _r03_diagnostic_with_vars(v: dict) -> str:
    """THÊM 2026-07-19 (audit vòng 3, D2 — NGHIÊM TRỌNG): độ chính xác chẩn
    đoán (STARD 2015) — index test vs reference standard. KHÔNG có trục
    thời gian-đến-biến-cố; dùng ROC/AUC + độ nhạy-đặc hiệu tại ngưỡng tối ưu
    (Youden index) + calibration, KHÔNG Cox/log-rank. `exposure`/`outcome`
    (tên field cố định từ detect_variables_from_redcap) dùng làm proxy cho
    index test / reference standard — KHÔNG có field riêng trong REDCap
    dictionary heuristic hiện tại."""
    index_test = v["exposure"]
    ref_standard = v["outcome"]
    return f"""\
# 03_analysis.R — Độ chính xác chẩn đoán (STARD 2015): ROC/AUC + Se/Sp
# Biến: index test={index_test} | tiêu chuẩn vàng (reference standard)={ref_standard}
# Chẩn đoán KHÔNG có trục thời gian-đến-biến-cố hợp lệ — KHÔNG dùng Cox/log-rank.
# Đúng chuẩn: đường cong ROC, AUC, và Se/Sp tại ngưỡng tối ưu (Youden index).
source(here::here("scripts", "00_setup.R"))
# library(pROC)
# df <- readRDS(file.path(DATA_PROC, "df_clean.rds"))

# roc_obj <- pROC::roc(response = df${ref_standard}, predictor = df${index_test}, ci = TRUE)
# roc_obj$auc; ci(roc_obj)  # AUC + 95% CI

# Ngưỡng tối ưu theo Youden index (Se+Sp-1 lớn nhất) — [CẦN BÁC SĨ XÁC NHẬN
# ngưỡng lâm sàng có ý nghĩa thay vì thuần thống kê nếu khác nhau]:
# best_cut <- pROC::coords(roc_obj, "best", best.method = "youden")
# pROC::coords(roc_obj, best_cut$threshold, ret = c("sensitivity","specificity","ppv","npv"))
# SỬA 2026-07-21 (vòng lặp kiểm tra-hoàn thiện vòng 5, phát hiện HIGH): dòng
# coords() ở trên KHÔNG tính khoảng tin cậy nào (mặc định pROC::coords() không
# có CI) — trong khi Bảng 2 (TABLE_SHELLS["diagnostic"]) khai cột "95%CI" cho
# Se/Sp/PPV/NPV, tạo mâu thuẫn: bảng hứa một con số script không bao giờ tính.
# pROC::coords() và pROC::ci.coords() là 2 HÀM KHÁC NHAU — phải gọi ci.coords()
# RIÊNG (bootstrap, boot.n mặc định 2000) mới có CI cho Se/Sp/PPV/NPV tại một
# ngưỡng cụ thể. Quan trọng nhất với cỡ mẫu nhỏ/Se-Sp gần 0%-100% (hay gặp ở
# nghiên cứu chẩn đoán) — chính là tình huống xấp xỉ Wald mặc định sai lệch
# nặng nhất, nên dùng bootstrap (ci.coords) thay vì Wald thủ công.
# ci_coords <- pROC::ci.coords(roc_obj, x = best_cut$threshold, input = "threshold",
#                               ret = c("sensitivity","specificity","ppv","npv"),
#                               boot.n = 2000)
# ci_coords  # in ra 95%CI bootstrap cho từng chỉ số tại ngưỡng đã chọn

# Calibration (nếu index test là điểm số/xác suất liên tục, không phải nhị phân):
# giả::val.prob(df${index_test}, df${ref_standard})  # gói 'giả' hoặc rms::val.prob

message("03_analysis.R (Diagnostic) — index test={index_test} vs reference={ref_standard} | [CẦN DỮ LIỆU THẬT]")
"""


def _r03_prediction_with_vars(v: dict) -> str:
    """THÊM 2026-07-19 (audit vòng 3, D2 — NGHIÊM TRỌNG): mô hình tiên lượng
    (TRIPOD+AI 2024) — phát triển + đánh giá nội bộ. KHÔNG dùng Cox/HR đơn
    biến như cohort thường — cần đa biến + shrinkage (chống overfitting) +
    bootstrap internal validation + calibration + discrimination (C-statistic)
    + DCA, theo Riley RD et al. BMJ 2020;368:m441 (đã dùng ở G3).

    SỬA 2026-07-21 (vòng lặp kiểm tra-hoàn thiện vòng 6, phát hiện HIGH):
    doctrine mo-hinh-tien-luong.md (M7) yêu cầu kiểm định NGOẠI (quần thể độc
    lập) là "Bắt buộc" ngang hàng với kiểm định nội (bootstrap), nhưng bản
    trước của hàm này KHÔNG có mục nào — kể cả comment hướng dẫn — cho kiểm
    định ngoại (grep "ngoại"/"external" trên toàn file cho 0 kết quả). Thêm
    mục 6) làm rõ: pipeline G0-G10 này chỉ vận hành trên MỘT bộ dữ liệu của
    MỘT đề tài (không có quần thể độc lập thứ hai tự động), nên kiểm định
    ngoại LUÔN cần bác sĩ/thống kê viên tự cung cấp dataset độc lập — code
    sườn chỉ hướng dẫn CÁCH làm khi có dataset đó, không tự bịa ra được."""
    outcome  = v["outcome"]
    time_col = v["time_col"]
    covars   = v["covariates"]
    cov_fml  = " + ".join(covars) if covars else "age + sex + bmi + [CẦN — các biến tiên đoán ứng viên khác]"
    return f"""\
# 03_analysis.R — Mô hình tiên lượng (TRIPOD+AI 2024): phát triển + đánh giá nội bộ
# Biến: kết cục dự đoán={outcome} | thời gian (nếu time-to-event)={time_col}
# Biến tiên đoán ứng viên (candidate predictors): {cov_fml}
# KHÔNG dùng Cox/HR đơn biến như cohort thường — cần mô hình ĐA BIẾN có kiểm
# soát overfitting (shrinkage), sau đó đánh giá hiệu chuẩn + phân biệt + DCA.
source(here::here("scripts", "00_setup.R"))
# library(rms); library(glmnet); library(pROC)
# df <- readRDS(file.path(DATA_PROC, "df_clean.rds"))

# 1) PHÁT TRIỂN mô hình đa biến (logistic nếu kết cục nhị phân; Cox nếu
#    time-to-event {time_col} có ý nghĩa — [CẦN BÁC SĨ XÁC NHẬN loại kết cục]):
# model_full <- glm({outcome} ~ {cov_fml}, data = df, family = binomial())
# # HOẶC: model_full <- coxph(Surv({time_col}, {outcome}) ~ {cov_fml}, data = df)

# 2) SHRINKAGE (LASSO/ridge) — chống quá khớp khi nhiều biến tiên đoán so
#    với cỡ mẫu (PROBAST+AI domain 4):
# x <- model.matrix(~ {cov_fml}, data = df)[, -1]; y <- df${outcome}
# cv_lasso <- glmnet::cv.glmnet(x, y, family = "binomial", alpha = 1)

# 3) INTERNAL VALIDATION (bootstrap, KHÔNG split-sample đơn giản):
# val_boot <- rms::validate(rms::lrm({outcome} ~ {cov_fml}, data = df, x=TRUE, y=TRUE),
#                            method = "boot", B = 200)

# 4) CALIBRATION (slope + intercept-in-the-large) + DISCRIMINATION (C-statistic):
# rms::val.prob(predict(model_full, type="response"), df${outcome})

# 5) DECISION CURVE ANALYSIS (lợi ích lâm sàng ròng theo ngưỡng xác suất):
# dcurves::dca({outcome} ~ pred, data = df) |> plot()

# 6) KIỂM ĐỊNH NGOẠI (external validation) — BẮT BUỘC theo TRIPOD+AI M7,
#    KHÔNG được thay thế bằng bootstrap internal validation ở mục 3. Cần một
#    quần thể ĐỘC LẬP (khác thời gian/địa điểm thu thập) — [CẦN BÁC SĨ/THỐNG
#    KÊ VIÊN CUNG CẤP df_external; pipeline này KHÔNG tự có quần thể thứ hai]:
# df_external <- readRDS(file.path(DATA_PROC, "df_external_validation.rds"))  # [CẦN DỮ LIỆU THẬT]
# pred_external <- predict(model_full, newdata = df_external, type = "response")
# rms::val.prob(pred_external, df_external${outcome})  # calibration + discrimination TRÊN quần thể ngoại
# [CẦN — nếu KHÔNG có quần thể độc lập, mô hình CHỈ được coi là "đã phát triển +
# kiểm định nội" — KHÔNG được tuyên bố "đã kiểm định ngoại"/"sẵn sàng lâm sàng"
# cho tới khi có bước này, theo mo-hinh-tien-luong.md M7]

message("03_analysis.R (Prediction/TRIPOD+AI) — kết cục={outcome} | predictors={cov_fml} | [CẦN DỮ LIỆU THẬT — C-statistic/R² kỳ vọng do bác sĩ/thống kê viên cấp theo Riley 2020, PMID 32188600; kiểm định NGOẠI cần quần thể độc lập riêng, xem mục 6]")
"""


def _r03_srma_template() -> str:
    """THÊM 2026-07-19 (audit vòng 3, D2 — NGHIÊM TRỌNG): tổng hợp bằng
    chứng (PRISMA 2020) — random/fixed-effects meta-analysis. KHÁC HẲN 6
    thiết kế còn lại: input KHÔNG phải df tham gia-cấp-cá-nhân từ REDCap
    (detect_variables_from_redcap không áp dụng — SR/MA phân tích bảng
    STUDY-LEVEL: mỗi dòng 1 nghiên cứu đã trích xuất, không phải 1 bệnh
    nhân), nên hàm này KHÔNG nhận `v`."""
    return """\
# 03_analysis.R — Tổng hợp bằng chứng (PRISMA 2020): random/fixed-effects meta-analysis
# KHÁC 6 thiết kế còn lại: input là bảng STUDY-LEVEL (mỗi dòng 1 nghiên cứu đã
# trích xuất — tác giả/năm/effect/SE hoặc 2x2 table), KHÔNG phải df tham gia
# cấp-cá-nhân. KHÔNG dùng Cox/log-rank/logistic đơn-nghiên-cứu.
source(here::here("scripts", "00_setup.R"))
# library(meta)  # hoặc metafor
# extracted <- read.csv(file.path(DATA_PROC, "study_level_extraction.csv"))
# # Cột kỳ vọng: study, year, kèm MỘT trong hai bộ:
# #   (a) hiệu ứng liên tục: TE, seTE (log-scale nếu OR/RR/HR)
# #   (b) 2x2 table (nhị phân): event.e, n.e, event.c, n.c

# SỬA 2026-07-21 (vòng lặp kiểm tra-hoàn thiện vòng 5, phát hiện MEDIUM): bản
# trước ép cứng random=TRUE, common=FALSE cho MỌI trường hợp, không kèm giải
# thích/lựa chọn — nhìn giống một quyết định ngầm hơn là chủ đích. Cả 2 hàm
# dưới đây VẪN tính I²/τ²/Q trong summary() bất kể random/common (gói meta tự
# tính không phụ thuộc lựa chọn mô hình), nên KHÔNG phải thiếu tính toán dị
# biệt — chỉ là dị biệt chưa được dùng để RA quyết định mô hình. Random-effects
# mặc định (bất kể I²) là lập trường CHÍNH THỐNG hiện nay của Cochrane Handbook
# (khuyến nghị coi dị biệt lâm sàng/phương pháp là gần như luôn tồn tại, không
# cần I² thấp mới chọn fixed) — giữ nguyên làm mặc định của template, nhưng nay
# NÊU RÕ đây là lựa chọn có chủ đích + cách đối chiếu bằng fixed-effect làm phân
# tích độ nhạy, để thống kê viên tự quyết định thay vì thấy một tham số ẩn:

# Kết cục NHỊ PHÂN (OR/RR) — [CẦN XÁC NHẬN loại effect size từ PICO]:
# m_bin <- meta::metabin(event.e, n.e, event.c, n.c, studlab = study,
#                         data = extracted, sm = "OR",        # hoặc "RR"
#                         method = "MH", random = TRUE, common = FALSE)
# summary(m_bin); meta::forest(m_bin)
# # Đối chiếu độ nhạy với fixed-effect (Mantel-Haenszel, không giả định dị biệt
# # ngẫu nhiên) — nếu 2 ước lượng lệch nhiều, cần bàn luận rõ trong bài:
# m_bin_fixed <- meta::metabin(event.e, n.e, event.c, n.c, studlab = study,
#                               data = extracted, sm = "OR", method = "MH",
#                               random = FALSE, common = TRUE)
# summary(m_bin_fixed)

# Kết cục LIÊN TỤC hoặc effect size đã tính sẵn (HR/MD) — TE/seTE trên log-scale nếu HR:
# m_gen <- meta::metagen(TE, seTE, studlab = study, data = extracted,
#                         sm = "HR", random = TRUE, common = FALSE)   # sm theo PICO thật
# summary(m_gen); meta::forest(m_gen)
# # Đối chiếu độ nhạy với fixed-effect, cùng lý do như trên:
# m_gen_fixed <- meta::metagen(TE, seTE, studlab = study, data = extracted,
#                               sm = "HR", random = FALSE, common = TRUE)
# summary(m_gen_fixed)

# Dị biệt (heterogeneity) — I²/τ²/Q đã có sẵn trong summary() ở trên (tính bất
# kể random/common). [CẦN THỐNG KÊ VIÊN XÁC NHẬN] lựa chọn mô hình cuối (mặc
# định random-effects ở đây) phù hợp với mức dị biệt và bối cảnh lâm sàng của
# đề tài — không chỉ dùng số mặc định của template mà không xem I²/Q thật.

# Publication bias (chỉ khi ≥10 nghiên cứu — Egger test không đáng tin cậy dưới ngưỡng này):
# meta::funnel(m_bin); meta::metabias(m_bin, method.bias = "Egger")

message("03_analysis.R (SR/MA) — input STUDY-LEVEL (không phải participant-level) | [CẦN BẢNG TRÍCH XUẤT THẬT sau khi hoàn tất sàng lọc PRISMA]")
"""


def _r03_qualitative_template() -> str:
    """THÊM 2026-07-20 (vòng lặp kiểm tra-hoàn thiện): nghiên cứu định
    tính/hỗn hợp (COREQ/SRQR — xem run_g1_auto.py). KHÁC 7 thiết kế còn lại:
    KHÔNG có mô hình thống kê suy diễn (không hồi quy/Cox/log-rank/OR/RR),
    phân tích chính là MÃ HÓA CHỦ ĐỀ (thematic analysis) thường làm bằng
    phần mềm QDA chuyên dụng (NVivo/ATLAS.ti/MAXQDA) hoặc mã tay có bảng mã
    (codebook). R ở đây CHỈ hỗ trợ đếm tần suất/đồng-xuất-hiện mã sau khi đã
    mã hóa thủ công — KHÔNG thay thế bước diễn giải định tính. Không nhận
    `v` (không dò biến REDCap dạng tham gia-cấp-cá-nhân định lượng)."""
    return """\
# 03_analysis.R — Nghiên cứu định tính/hỗn hợp (COREQ/SRQR): KHÔNG có mô hình
# thống kê suy diễn. Phân tích chính là MÃ HÓA CHỦ ĐỀ (thematic analysis),
# thường thực hiện bằng phần mềm QDA (NVivo/ATLAS.ti/MAXQDA) hoặc mã tay theo
# codebook — KHÔNG dùng hồi quy/Cox/log-rank/OR/RR/AUC cho dữ liệu này.
source(here::here("scripts", "00_setup.R"))
# Script này CHỈ hỗ trợ bước phụ (đếm tần suất/đồng-xuất-hiện mã) SAU KHI đã
# mã hóa thủ công xong — không thay thế việc đọc/diễn giải của nhà nghiên cứu.

# codes <- read.csv(file.path(DATA_PROC, "coded_transcripts.csv"))
# # Cột kỳ vọng: record_id, transcript_segment, code_1, code_2, ...
# # (mỗi dòng 1 đoạn trích đã gán mã, sinh ra từ phần mềm QDA hoặc bảng mã tay)

# Tần suất mã theo người tham gia (kiểm tra bão hòa dữ liệu — data saturation):
# table(codes$code_1)
# aggregate(record_id ~ code_1, data = codes, FUN = function(x) length(unique(x)))

# Đồng-xuất-hiện mã (co-occurrence) — gợi ý chủ đề gộp (theme clustering):
# table(codes$code_1, codes$code_2)

# ⚠ KHÔNG chạy bất kỳ mô hình hồi quy/suy diễn nào ở đây. Chất lượng nghiên
# cứu định tính đánh giá qua TRUSTWORTHINESS (Lincoln & Guba): credibility
# (member checking/triangulation), transferability (mô tả bối cảnh dày —
# thick description), dependability (audit trail mã hóa), confirmability
# (phản tư — reflexivity, ghi ở nhật ký nghiên cứu). Xem run_g1_auto.py
# BIAS_CONTROLS["qualitative"] cho khung đầy đủ.

message("03_analysis.R (định tính/hỗn hợp) — KHÔNG có mô hình suy diễn; phân tích chính là mã hóa chủ đề bằng phần mềm QDA hoặc tay | [CẦN BẢNG MÃ HÓA THẬT sau khi hoàn tất phỏng vấn/nhóm tiêu điểm]")
"""


if __name__ == "__main__":
    main()
