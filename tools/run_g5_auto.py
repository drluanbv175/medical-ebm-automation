#!/usr/bin/env python3
"""G5 — hạ tầng quản trị dữ liệu và bộ công cụ chuẩn bị khóa dataset.

Lệnh này sinh DMP, data dictionary REDCap và script QC. Dữ liệu thật khử định
danh được xử lý bằng chuỗi intake -> cleaning/query -> data lock riêng; việc sinh
file ở đây không đồng nghĩa cổng G5 đã qua.
"""
import argparse
import csv
import json
import re
import sys
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(BASE / "tools"))
import g5_quality_gate as G5Q  # noqa: E402
import gate_contract as GC  # noqa: E402

# ---------------------------------------------------------------------------
# CRF DEFINITIONS — 55 dòng, cụ thể theo loại thiết kế
# Mỗi tuple: (var_name, form, section, type, label, choices, note,
#              validation_type, val_min, val_max, required, branching)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# NHẬN DIỆN CHUYÊN KHOA THEO CHỦ ĐỀ
# Trước bản sửa này, mọi CRF (bất kể chủ đề) đều dùng cứng field của ca
# SGLT2-HFpEF (NYHA, LVEF, SGLT2i, nhập viện suy tim) — một đề tài về Metformin/
# đái tháo đường vẫn ra field suy tim. Sửa: chọn "bundle" lâm sàng theo từ khóa
# chủ đề; KHÔNG khớp bundle nào → dùng bundle GENERIC với placeholder [CẦN...]
# thay vì bịa nội dung lâm sàng có thể sai hoàn toàn với đề tài thật.
# ---------------------------------------------------------------------------
_SPECIALTY_KEYWORDS = {
    "cardiology_hf": [
        "suy tim", "heart failure", "sglt2", "hfpef", "hfref", "lvef",
        "ef thất trái", "tim mạch", "nhồi máu cơ tim", "nyha",
    ],
    "metabolic_diabetes": [
        "đái tháo đường", "tiền đái tháo đường", "diabetes", "metformin",
        "insulin", "hba1c", "đường huyết", "glucose", "sulfonylurea",
        "gliptin", "glp-1", "chuyển hóa",
    ],
    # THÊM 2026-07-02: 6 chuyên khoa mới để giảm số đề tài rơi về "generic"
    # một cách không cần thiết. Giữ nguyên cơ chế: không khớp từ khóa nào
    # → vẫn "generic" (KHÔNG xóa fallback an toàn).
    "nephrology_ckd": [
        "bệnh thận mạn", "suy thận", "ckd", "chronic kidney disease",
        "lọc máu", "dialysis", "egfr", "chạy thận", "thận nhân tạo",
        "albumin niệu", "protein niệu",
    ],
    "pulmonology_copd_asthma": [
        "copd", "hen phế quản", "hen suyễn", "asthma", "khó thở mạn",
        "fev1", "bptnmt", "đợt cấp copd", "hô hấp mạn",
    ],
    "neurology_stroke": [
        "đột quỵ", "stroke", "nhồi máu não", "xuất huyết não", "nihss",
        "tai biến mạch máu não", "thiếu máu não cục bộ",
    ],
    "musculoskeletal_pain": [
        "đau mạn", "đau lưng", "đau khớp", "viêm khớp", "chronic pain",
        "osteoarthritis", "thoái hóa khớp", "đau cơ xương khớp",
    ],
    "psychiatry_depression_anxiety": [
        "trầm cảm", "lo âu", "depression", "anxiety", "phq-9", "gad-7",
        "rối loạn lo âu", "rối loạn trầm cảm",
    ],
    "gastroenterology": [
        "viêm loét đại tràng", "crohn", "xơ gan", "viêm gan", "gerd",
        "trào ngược dạ dày", "trào ngược", "viêm gan mạn", "bệnh gan mạn",
        "bệnh viêm ruột",
    ],
    # THÊM 2026-07-17: phát hiện thật khi chạy demo đề tài khảo sát hài lòng
    # bệnh nhân C1a, BVQY175 — trước đây rơi về "generic", kéo theo _BASE_VITALS
    # (huyết áp/nhịp tim) và bệnh nền tim mạch/chuyển hóa vào CRF của một khảo
    # sát KHÔNG đo chỉ số lâm sàng, gây bác sĩ đánh giá "đề cương không đảm bảo".
    "patient_satisfaction": [
        "hài lòng", "satisfaction", "chất lượng dịch vụ", "chất lượng khám chữa bệnh",
        "khảo sát bệnh nhân", "khảo sát người bệnh", "trải nghiệm người bệnh",
        "patient experience", "chăm sóc khách hàng y tế",
    ],
}


def detect_specialty(topic: str) -> str:
    """
    Nhận diện chuyên khoa từ chủ đề đề tài để chọn field lâm sàng phù hợp.
    Trả về "generic" nếu không khớp từ khóa nào — KHÔNG đoán liều để tránh
    gán nhầm field của chuyên khoa khác (vd suy tim) cho đề tài không liên quan.
    """
    # SỬA: substring thô "kw in t" khớp nhầm "insulin" bên trong "insulinoma"
    # (u tụy nội tiết, KHÔNG liên quan đái tháo đường) → gán nhầm bundle
    # metabolic_diabetes, sinh CRF hoàn toàn sai chuyên khoa mà không cảnh
    # báo gì (specialty_is_generic_placeholder vẫn False, trông như đã nhận
    # diện đúng). Dùng token-boundary, cùng pattern đã áp dụng ở G1/G6.
    #
    # SỬA 2026-07-02: logic cũ "khớp từ khóa ĐẦU TIÊN thắng" (duyệt dict theo
    # thứ tự khai báo, return ngay khi thấy 1 từ khóa khớp) khiến 1 từ khóa
    # dùng chung nhiều chuyên khoa (vd "sglt2" — thuốc dùng cả tim mạch lẫn
    # thận lẫn ĐTĐ, chỉ khai trong cardiology_hf) LUÔN thắng các từ khóa đặc
    # hiệu hơn của chuyên khoa khác xuất hiện SAU trong dict (vd đề tài về CKD
    # có "bệnh thận mạn"+"ckd" bị gán nhầm cardiology_hf chỉ vì có nhắc
    # "SGLT2" và cardiology_hf được duyệt trước nephrology_ckd). Phát hiện bởi
    # agent kiểm định độc lập khi test tích hợp 6 chuyên khoa mới qua G0-G7.
    # Sửa: tính ĐIỂM cho MỖI chuyên khoa = tổng số TỪ trong mỗi từ khóa khớp
    # (cụm từ dài/đặc hiệu như "bệnh thận mạn" nặng hơn 1 từ khóa ngắn/dùng
    # chung như "sglt2"), chọn chuyên khoa điểm cao nhất. Hòa điểm → giữ thứ
    # tự khai báo trong dict làm tie-break (hành vi cũ, ổn định, không đoán).
    scores = _specialty_scores(topic)
    if not scores:
        return "generic"
    return max(scores.items(), key=lambda kv: kv[1])[0]


def _specialty_scores(topic: str) -> dict:
    """Tính điểm đặc hiệu của mỗi chuyên khoa cho 1 chủ đề — dùng chung bởi
    detect_specialty() và detect_specialty_with_confidence()."""
    t = (topic or "").lower()
    scores: dict[str, int] = {}
    for specialty, keywords in _SPECIALTY_KEYWORDS.items():
        score = 0
        for kw in keywords:
            if re.search(r'(?<![a-zà-ỹ0-9])' + re.escape(kw) + r'(?![a-zà-ỹ0-9])', t):
                score += len(kw.split())
        if score > 0:
            scores[specialty] = score
    return scores


def detect_specialty_with_confidence(topic: str):
    """
    Như detect_specialty() nhưng trả thêm tín hiệu ĐỘ TIN CẬY của lựa chọn —
    dùng để cảnh báo bác sĩ khi 2 chuyên khoa có điểm quá gần nhau (chủ đề
    thật sự mơ hồ, vd vừa nhắc "suy tim" vừa nhắc "bệnh thận mạn" mà không
    rõ trọng tâm), thay vì âm thầm chọn 1 bên theo tie-break.

    THÊM 2026-07-02: guardrail cấu trúc (R1-R7) không kiểm được ĐÚNG-SAI nội
    dung lâm sàng — bug detect_specialty() nghiêm trọng nhất phiên trước đó
    (sglt2 lấn át bệnh thận mạn) đã PASS mọi guardrail vì đây là lỗi nội
    dung, không phải cấu trúc. Cảnh báo này là lớp phòng thủ THỨ HAI: không
    ngăn được lỗi phân loại sai hoàn toàn (đó là việc của thuật toán tính
    điểm), nhưng ít nhất SOI RA những ca ranh giới mờ để bác sĩ tự xác nhận
    thay vì tin tưởng mù quáng vào 1 lựa chọn có thể chỉ hơn đối thủ 1 điểm.

    Trả về (specialty, runner_up, is_ambiguous):
    - specialty: chuyên khoa được chọn (giống hệt detect_specialty())
    - runner_up: chuyên khoa á quân nếu có, None nếu specialty thắng áp đảo/generic
    - is_ambiguous: True khi runner_up đạt ≥75% điểm của specialty thắng (ranh giới mờ)
    """
    scores = _specialty_scores(topic)
    if not scores:
        return "generic", None, False
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    winner, winner_score = ranked[0]
    if len(ranked) < 2:
        return winner, None, False
    runner_up, runner_up_score = ranked[1]
    is_ambiguous = runner_up_score >= winner_score * 0.75
    return winner, (runner_up if is_ambiguous else None), is_ambiguous


# Nhóm biến chung (admin + nhân khẩu) — dùng cho MỌI chuyên khoa VÀ MỌI thiết kế.
_BASE_ADMIN = [
    ("record_id",     "Admin",       "Hành chính",         "text",     "Mã tham gia (duy nhất, không PII)",                    "",                                                                      "",                        "",          "",    "",    "y", ""),
    ("consent_date",  "Admin",       "",                   "text",     "Ngày đồng thuận",                                       "",                                                                      "",                        "date_ymd",  "",    "",    "y", ""),
    ("site_id",       "Admin",       "",                   "text",     "Mã cơ sở / trung tâm",                                  "",                                                                      "",                        "",          "",    "",    "y", ""),
    ("visit_date",    "Admin",       "",                   "text",     "Ngày khám/thu thập dữ liệu",                            "",                                                                      "",                        "date_ymd",  "",    "",    "n", ""),
]

# SỬA 2026-07-17 (bình duyệt đa vai trò phát hiện thật, cùng ngày với đề tài
# hài lòng bệnh nhân C1a): censor_date/censor_reason/protocol_deviation/ltfu
# trước đây nằm CỨNG trong _BASE_ADMIN, nhồi vào MỌI thiết kế kể cả cắt ngang
# MỘT thời điểm (cross_sectional) — "mất theo dõi (LTFU)"/"ngày kiểm duyệt"
# không có Ý NGHĨA gì khi không có trục thời gian theo dõi dọc. Tách riêng,
# CHỈ ghép vào thiết kế thật sự có theo dõi dọc (xem build_redcap_rows()).
_FOLLOWUP_ADMIN = [
    ("censor_date",   "Admin",       "Theo dõi dọc",       "text",     "Ngày kiểm duyệt (kết thúc theo dõi)",                   "",                                                                      "",                        "date_ymd",  "",    "",    "n", ""),
    ("censor_reason", "Admin",       "",                   "dropdown", "Lý do kiểm duyệt",                                      "1, Hoàn thành theo dõi | 2, Rút đồng thuận | 3, Mất liên lạc | 4, Tử vong | 5, Khác", "",          "",          "",    "",    "n", ""),
    ("protocol_deviation","Admin",   "",                   "radio",    "Vi phạm đề cương",                                      "0, Không | 1, Nhỏ | 2, Lớn",                                          "",                        "",          "",    "",    "n", ""),
    ("ltfu",          "Admin",       "",                   "radio",    "Mất theo dõi (LTFU)",                                   "0, Không | 1, Có",                                                     "",                        "",          "",    "",    "n", ""),
]

_BASE_DEMOGRAPHICS = [
    ("age",           "Demographics","Nhân khẩu học",      "text",     "Tuổi (năm)",                                            "",                                                                      "",                        "integer",   "18",  "120", "y", ""),
    ("sex",           "Demographics","",                   "radio",    "Giới tính sinh học",                                    "1, Nam | 2, Nữ | 3, Khác",                                            "",                        "",          "",    "",    "y", ""),
    ("bmi",           "Demographics","",                   "text",     "BMI (kg/m²)",                                           "",                                                                      "",                        "number",    "10",  "60",  "n", ""),
    ("education",     "Demographics","",                   "dropdown", "Trình độ học vấn",                                      "1, Tiểu học | 2, THCS | 3, THPT | 4, CĐ/ĐH | 5, Sau ĐH",             "",                        "",          "",    "",    "n", ""),
    ("ethnicity",     "Demographics","",                   "dropdown", "Dân tộc",                                               "1, Kinh | 2, Hoa | 3, Khmer | 4, Khác",                               "",                        "",          "",    "",    "n", ""),
]

# Sinh hiệu — thật sự tổng quát, dùng cho MỌI chuyên khoa
_BASE_VITALS = [
    ("bp_sys",        "Clinical",    "Sinh hiệu nền",      "text",     "Huyết áp tâm thu (mmHg)",                               "",                                                                      "",                        "number",    "60",  "250", "y", ""),
    ("bp_dia",        "Clinical",    "",                   "text",     "Huyết áp tâm trương (mmHg)",                            "",                                                                      "",                        "number",    "30",  "150", "y", ""),
    ("heart_rate",    "Clinical",    "",                   "text",     "Nhịp tim (lần/phút)",                                   "",                                                                      "",                        "integer",   "30",  "250", "y", ""),
]

# CHUYÊN KHOA: Tim mạch / Suy tim — chỉ dùng khi topic khớp "cardiology_hf"
_CARDIO_HF_CLINICAL = [
    ("nyha",          "Clinical",    "Lâm sàng nền (Tim mạch)", "dropdown", "Phân độ NYHA",                                    "1, I | 2, II | 3, III | 4, IV",                                       "",                        "",          "",    "",    "y", ""),
    ("lvef",          "Clinical",    "",                   "text",     "EF thất trái (%)",                                      "",                                                                      "Siêu âm tim gần nhất ≤3 tháng","number","20",  "85",  "y", ""),
]

# CHUYÊN KHOA: Chuyển hóa / Đái tháo đường — chỉ dùng khi topic khớp "metabolic_diabetes"
_METABOLIC_CLINICAL = [
    ("waist_circumference","Clinical","Lâm sàng nền (Chuyển hóa)","text","Vòng eo (cm)",                                       "",                                                                      "",                        "number",    "40",  "200", "n", ""),
    ("retinopathy_screen","Clinical", "",                   "radio",    "Tầm soát bệnh võng mạc ĐTĐ",                          "0, Không có | 1, Có tổn thương",                                      "",                        "",          "",    "",    "n", ""),
]

# SỬA: trước đây _BASE_COMORBIDITIES/_BASE_LABS được gắn CỨNG vào MỌI bundle
# kể cả "generic" — một đề tài về CBT/trầm cảm vẫn ra field rung nhĩ, COPD,
# CKD, kali huyết thanh (audit follow-up phát hiện, cùng loại bug với CRF
# gốc nhưng ở tầng "base" nằm ngoài dispatch theo specialty). Nay đổi tên
# thành _CARDIOMETABOLIC_* (chỉ dùng cho bundle tim mạch/chuyển hóa — nơi
# các bệnh nền/xét nghiệm này THẬT SỰ liên quan) và thêm _GENERIC_COMORBIDITIES/
# _GENERIC_LABS tối giản, không giả định chuyên khoa, cho bundle generic.
_CARDIOMETABOLIC_COMORBIDITIES = [
    ("dm",            "Comorbidity", "Bệnh kèm",           "radio",    "Đái tháo đường",                                       "0, Không | 1, Có — týp 2 | 2, Có — týp 1",                           "",                        "",          "",    "",    "y", ""),
    ("htn",           "Comorbidity", "",                   "radio",    "Tăng huyết áp",                                        "0, Không | 1, Có",                                                     "",                        "",          "",    "",    "y", ""),
    ("af",            "Comorbidity", "",                   "radio",    "Rung nhĩ",                                              "0, Không | 1, Cơn kịch phát | 2, Dai dẳng | 3, Vĩnh viễn",           "",                        "",          "",    "",    "y", ""),
    ("ckd",           "Comorbidity", "",                   "dropdown", "Bệnh thận mạn (giai đoạn CKD)",                        "0, Không | 1, G1 | 2, G2 | 3, G3a | 4, G3b | 5, G4 | 6, G5",        "",                        "",          "",    "",    "y", ""),
    ("copd",          "Comorbidity", "",                   "radio",    "BPTNMT",                                                "0, Không | 1, Có",                                                     "",                        "",          "",    "",    "y", ""),
    ("stroke",        "Comorbidity", "",                   "radio",    "Đột quỵ / TIA tiền sử",                                "0, Không | 1, Có",                                                     "",                        "",          "",    "",    "n", ""),
]

# Generic — chỉ 2 bệnh nền phổ biến gần như mọi nghiên cứu người lớn đều cần
# hỏi (không giả định chuyên khoa cụ thể); bệnh nền đặc thù khác để bác sĩ
# tự thêm theo PICO/SAP thật của đề tài.
_GENERIC_COMORBIDITIES = [
    ("dm",            "Comorbidity", "Bệnh kèm",           "radio",    "Đái tháo đường",                                       "0, Không | 1, Có — týp 2 | 2, Có — týp 1",                           "",                        "",          "",    "",    "y", ""),
    ("htn",           "Comorbidity", "",                   "radio",    "Tăng huyết áp",                                        "0, Không | 1, Có",                                                     "",                        "",          "",    "",    "y", ""),
    ("comorbid_other","Comorbidity", "",                   "notes",    "Bệnh nền khác liên quan [CẦN BÁC SĨ LIỆT KÊ theo PICO]", "",                                                                    "[CẦN — hệ thống không giả định bệnh nền đặc thù cho chuyên khoa này]", "", "", "", "n", ""),
]

# Xét nghiệm nền tim mạch/chuyển hóa — CHỈ dùng cho bundle cardiology_hf/metabolic_diabetes
_CARDIOMETABOLIC_LABS = [
    ("egfr",          "Labs",        "Xét nghiệm nền",     "text",     "eGFR (mL/min/1.73m²)",                                 "",                                                                      "CKD-EPI",                 "number",    "0",   "200", "y", ""),
    ("hba1c",         "Labs",        "",                   "text",     "HbA1c (%)",                                             "",                                                                      "Chỉ điền nếu có ĐTĐ",     "number",    "4",   "15",  "n", "[dm] <> '0'"),
    ("hgb",           "Labs",        "",                   "text",     "Hemoglobin (g/dL)",                                    "",                                                                      "",                        "number",    "3",   "20",  "n", ""),
    ("creatinine",    "Labs",        "",                   "text",     "Creatinine huyết thanh (µmol/L)",                      "",                                                                      "",                        "number",    "20",  "2000","y", ""),
    ("k_serum",       "Labs",        "",                   "text",     "Kali huyết thanh (mmol/L)",                            "",                                                                      "",                        "number",    "1.5", "8",   "y", ""),
]

# Generic — không giả định panel xét nghiệm cụ thể (eGFR/kali chỉ liên quan
# nếu đề tài thật sự về thận/tim mạch); để bác sĩ tự thêm xét nghiệm liên quan.
_GENERIC_LABS = [
    ("labs_other",    "Labs",        "Xét nghiệm nền",     "notes",    "Xét nghiệm nền liên quan [CẦN BÁC SĨ LIỆT KÊ theo PICO]", "",                                                                  "[CẦN — hệ thống không giả định panel xét nghiệm cho chuyên khoa này]", "", "", "", "n", ""),
]

# CHUYÊN KHOA: Tim mạch / Suy tim
_CARDIO_HF_LABS = [
    ("nt_probnp",     "Labs",        "Xét nghiệm nền (Tim mạch)","text","NT-proBNP (pg/mL)",                                    "",                                                                      "",                        "number",    "0",   "100000","y",""),
]
_CARDIO_HF_MEDS = [
    ("acei_arb",      "Meds",        "Thuốc nền (Tim mạch)", "radio",  "Đang dùng ACEi hoặc ARB",                              "0, Không | 1, ACEi | 2, ARB | 3, ARNI (sacubitril/valsartan)",       "",                        "",          "",    "",    "y", ""),
    ("betablocker",   "Meds",        "",                   "radio",    "Đang dùng Beta-blocker",                               "0, Không | 1, Có",                                                     "",                        "",          "",    "",    "y", ""),
    ("mra",           "Meds",        "",                   "radio",    "Đang dùng MRA (spiro/eplerenone/finerenone)",           "0, Không | 1, Spironolactone | 2, Eplerenone | 3, Finerenone",        "",                        "",          "",    "",    "y", ""),
    ("loop_diuretic", "Meds",        "",                   "radio",    "Đang dùng Lợi tiểu quai",                              "0, Không | 1, Furosemide | 2, Torasemide | 3, Khác",                  "",                        "",          "",    "",    "y", ""),
    ("sglt2i_pre",    "Meds",        "",                   "radio",    "Đã từng dùng SGLT2i trước tuyển",                      "0, Chưa bao giờ | 1, Có — đã ngưng | 2, Có — đang dùng",             "",                        "",          "",    "",    "y", ""),
]
_CARDIO_HF_EXPOSURE = [
    ("sglt2i_type",   "Exposure",    "Phơi nhiễm SGLT2i",  "dropdown", "Loại SGLT2i",                                          "1, Dapagliflozin | 2, Empagliflozin | 3, Canagliflozin | 4, Sotagliflozin | 5, Khác","", "",  "",    "",    "y", ""),
    ("sglt2i_dose",   "Exposure",    "",                   "text",     "Liều SGLT2i (mg/ngày)",                                "",                                                                      "",                        "number",    "1",   "300", "y", "[sglt2i_type] <> ''"),
    ("sglt2i_start_date","Exposure", "",                   "text",     "Ngày bắt đầu SGLT2i",                                  "",                                                                      "",                        "date_ymd",  "",    "",    "y", "[sglt2i_type] <> ''"),
]
_CARDIO_HF_OUTCOMES = [
    ("hf_hosp_first", "Outcomes",    "Kết cục chính",      "radio",    "Nhập viện do suy tim (lần đầu)",                      "0, Không | 1, Có",                                                     "",                        "",          "",    "",    "y", ""),
    ("hf_hosp_date",  "Outcomes",    "",                   "text",     "Ngày nhập viện suy tim lần đầu",                       "",                                                                      "",                        "date_ymd",  "",    "",    "n", "[hf_hosp_first] = '1'"),
    ("cv_death",      "Outcomes",    "",                   "radio",    "Tử vong tim mạch",                                     "0, Không | 1, Có",                                                     "",                        "",          "",    "",    "y", ""),
    ("death_date",    "Outcomes",    "",                   "text",     "Ngày tử vong (mọi nguyên nhân)",                       "",                                                                      "",                        "date_ymd",  "",    "",    "n", "[cv_death] = '1'"),
    ("follow_time_months","Outcomes","",                   "text",     "Thời gian theo dõi (tháng)",                           "",                                                                      "",                        "number",    "0",   "120", "y", ""),
    ("hf_hosp_total", "Outcomes",    "Kết cục phụ",        "text",     "Tổng số lần nhập viện suy tim",                        "",                                                                      "",                        "integer",   "0",   "50",  "n", ""),
    ("qol_score_baseline","Outcomes","",                   "text",     "Điểm chất lượng sống nền (KCCQ hoặc SF-36)",           "",                                                                      "[CẦN CHỈ ĐỊNH THANG ĐO]", "number",    "0",   "100", "n", ""),
    ("qol_score_6m",  "Outcomes",    "",                   "text",     "Điểm chất lượng sống lúc 6 tháng",                    "",                                                                      "",                        "number",    "0",   "100", "n", ""),
    ("ef_change_6m",  "Outcomes",    "",                   "text",     "Thay đổi EF lúc 6 tháng (%)",                         "",                                                                      "Siêu âm tim 6 tháng",     "number",    "-50", "50",  "n", ""),
]

# CHUYÊN KHOA: Chuyển hóa / Đái tháo đường
_METABOLIC_MEDS = [
    ("metformin_dose","Meds",        "Thuốc nền (Chuyển hóa)","text",   "Liều Metformin (mg/ngày)",                            "",                                                                      "",                        "number",    "0",   "3000","n", ""),
    ("insulin_type",  "Meds",        "",                   "dropdown", "Loại Insulin đang dùng",                              "0, Không dùng | 1, Nền | 2, Trộn | 3, Nền-tăng cường",                "",                        "",          "",    "",    "n", ""),
    ("sglt2i_dm_pre", "Meds",        "",                   "radio",    "Đã từng dùng SGLT2i trước tuyển",                     "0, Chưa bao giờ | 1, Có — đã ngưng | 2, Có — đang dùng",             "",                        "",          "",    "",    "n", ""),
]
_METABOLIC_EXPOSURE = [
    ("intervention_type","Exposure","Phơi nhiễm/Can thiệp (Chuyển hóa)","dropdown","Loại can thiệp/thuốc",                      "1, Metformin | 2, SGLT2i | 3, GLP-1 RA | 4, Sulfonylurea | 5, Thay đổi lối sống | 6, Khác","", "", "", "", "y", ""),
    ("intervention_dose","Exposure","",                   "text",     "Liều (mg/ngày, nếu áp dụng)",                          "",                                                                      "",                        "number",    "0",   "3000","n", ""),
    ("intervention_start_date","Exposure","",             "text",     "Ngày bắt đầu can thiệp/phơi nhiễm",                    "",                                                                      "",                        "date_ymd",  "",    "",    "y", ""),
]
_METABOLIC_OUTCOMES = [
    ("incident_t2dm", "Outcomes",    "Kết cục chính",      "radio",    "Tiến triển thành ĐTĐ týp 2 (kết cục chính)",          "0, Không | 1, Có",                                                     "",                        "",          "",    "",    "y", ""),
    ("incident_t2dm_date","Outcomes","",                  "text",     "Ngày chẩn đoán ĐTĐ týp 2",                             "",                                                                      "",                        "date_ymd",  "",    "",    "n", "[incident_t2dm] = '1'"),
    ("hypoglycemia_event","Outcomes","Kết cục phụ",       "radio",    "Có cơn hạ đường huyết",                                "0, Không | 1, Nhẹ | 2, Nặng (cần hỗ trợ)",                            "",                        "",          "",    "",    "n", ""),
    ("microvascular_complication","Outcomes","",          "radio",    "Biến chứng vi mạch mới (võng mạc/thận/thần kinh)",    "0, Không | 1, Có",                                                     "",                        "",          "",    "",    "n", ""),
    ("follow_time_months","Outcomes","",                  "text",     "Thời gian theo dõi (tháng)",                          "",                                                                      "",                        "number",    "0",   "120", "y", ""),
]

# ---------------------------------------------------------------------------
# THÊM 2026-07-02 — 6 CHUYÊN KHOA MỚI (giảm số đề tài rơi về "generic" một
# cách không cần thiết). Mỗi bundle theo ĐÚNG cấu trúc tuple 12 trường của
# cardiology_hf/metabolic_diabetes ở trên. Field nào KHÔNG đủ tự tin về
# thang đo/thuật ngữ chuẩn (vd Mayo score, Child-Pugh chi tiết) dùng "notes"
# tự do kèm "[CẦN xác định — hệ thống không tự tin đủ về thang đo chuẩn]"
# thay vì bịa công thức — cùng tinh thần "KHÔNG bịa" của bundle generic.
# ---------------------------------------------------------------------------

# CHUYÊN KHOA: Thận / Bệnh thận mạn (CKD)
_NEPHRO_CKD_CLINICAL = [
    ("ckd_stage_kdigo","Clinical",   "Lâm sàng nền (Thận)","dropdown", "Giai đoạn CKD (KDIGO)",                                "1, G1 (eGFR≥90) | 2, G2 (60-89) | 3, G3a (45-59) | 4, G3b (30-44) | 5, G4 (15-29) | 6, G5 (<15/lọc máu)","","","","","y", ""),
    ("acr",            "Clinical",    "",                   "text",     "Albumin niệu/Creatinine niệu — ACR (mg/g)",           "",                                                                      "Mẫu nước tiểu bất kỳ (spot urine)","number","0", "20000","y", ""),
    ("dialysis_status","Clinical",    "",                   "radio",    "Đang lọc máu",                                          "0, Không | 1, Chạy thận nhân tạo | 2, Lọc màng bụng",                 "",                        "",          "",    "",    "y", ""),
]
_NEPHRO_CKD_MEDS = [
    ("raas_blocker",  "Meds",        "Thuốc nền (Thận)",   "radio",    "Đang dùng ức chế RAAS (ACEi/ARB)",                     "0, Không | 1, ACEi | 2, ARB",                                          "",                        "",          "",    "",    "y", ""),
    ("sglt2i_ckd_pre","Meds",        "",                   "radio",    "Đã từng dùng SGLT2i trước tuyển",                      "0, Chưa bao giờ | 1, Có — đã ngưng | 2, Có — đang dùng",             "",                        "",          "",    "",    "n", ""),
]
_NEPHRO_CKD_EXPOSURE = [
    ("ckd_intervention_type","Exposure","Phơi nhiễm/Can thiệp (Thận)","dropdown","Loại thuốc/can thiệp",                       "1, Ức chế SGLT2 | 2, ACEi/ARB (RAAS blocker) | 3, Finerenone (MRA không steroid) | 4, Khác","","","","","y",""),
    ("ckd_intervention_dose","Exposure","",                "text",     "Liều (mg/ngày, nếu áp dụng)",                          "",                                                                      "",                        "number",    "0",   "1000","n", ""),
    ("ckd_intervention_start_date","Exposure","",          "text",     "Ngày bắt đầu can thiệp/phơi nhiễm",                    "",                                                                      "",                        "date_ymd",  "",    "",    "y", ""),
]
_NEPHRO_CKD_OUTCOMES = [
    ("egfr_decline_40","Outcomes",   "Kết cục chính",      "radio",    "Tiến triển CKD (giảm eGFR ≥40% so với nền)",          "0, Không | 1, Có",                                                     "",                        "",          "",    "",    "y", ""),
    ("egfr_decline_date","Outcomes","",                    "text",     "Ngày ghi nhận giảm eGFR ≥40%",                         "",                                                                      "",                        "date_ymd",  "",    "",    "n", "[egfr_decline_40] = '1'"),
    ("kidney_replacement","Outcomes","Kết cục phụ",        "radio",    "Khởi đầu điều trị thay thế thận",                      "0, Không | 1, Lọc máu | 2, Ghép thận",                                "",                        "",          "",    "",    "n", ""),
    ("renal_death",   "Outcomes",    "",                   "radio",    "Tử vong do nguyên nhân thận",                          "0, Không | 1, Có",                                                     "",                        "",          "",    "",    "n", ""),
    ("follow_time_months","Outcomes","",                   "text",     "Thời gian theo dõi (tháng)",                          "",                                                                      "",                        "number",    "0",   "120", "y", ""),
]

# CHUYÊN KHOA: Hô hấp / COPD-Hen phế quản
_PULM_COPD_CLINICAL = [
    ("fev1_pct",      "Clinical",    "Lâm sàng nền (Hô hấp)","text",   "FEV1 (% dự đoán)",                                      "",                                                                      "Đo hô hấp ký sau test giãn phế quản","number","10","150","y", ""),
    ("fev1_fvc_ratio","Clinical",    "",                   "text",     "Tỷ số FEV1/FVC (%)",                                    "",                                                                      "",                        "number",    "20",  "100", "y", ""),
    ("mmrc_score",    "Clinical",    "",                   "dropdown", "Điểm khó thở mMRC",                                    "0, Độ 0 | 1, Độ 1 | 2, Độ 2 | 3, Độ 3 | 4, Độ 4",                     "",                        "",          "",    "",    "y", ""),
    ("cat_score",     "Clinical",    "",                   "text",     "Điểm CAT (COPD Assessment Test)",                      "",                                                                      "Thang 0-40, chỉ áp dụng COPD",  "integer","0", "40",  "n", ""),
    ("exacerbation_freq_prior","Clinical","",              "text",     "Số đợt cấp trong 12 tháng trước tuyển",                 "",                                                                      "",                        "integer",   "0",   "50",  "y", ""),
]
_PULM_COPD_MEDS = [
    ("ics_use",       "Meds",        "Thuốc nền (Hô hấp)", "radio",    "Đang dùng ICS (corticosteroid hít)",                   "0, Không | 1, Có",                                                     "",                        "",          "",    "",    "y", ""),
    ("laba_use",      "Meds",        "",                   "radio",    "Đang dùng LABA",                                        "0, Không | 1, Có",                                                     "",                        "",          "",    "",    "y", ""),
    ("lama_use",      "Meds",        "",                   "radio",    "Đang dùng LAMA",                                        "0, Không | 1, Có",                                                     "",                        "",          "",    "",    "y", ""),
]
_PULM_COPD_EXPOSURE = [
    ("pulm_intervention_type","Exposure","Phơi nhiễm/Can thiệp (Hô hấp)","dropdown","Loại thuốc/phác đồ",                     "1, ICS/LABA | 2, LABA/LAMA | 3, ICS/LABA/LAMA (bộ ba) | 4, LAMA đơn | 5, Khác","","","","","y",""),
    ("pulm_intervention_dose","Exposure","",               "text",     "Liều (µg/liều, nếu áp dụng)",                          "",                                                                      "",                        "number",    "0",   "2000","n", ""),
    ("pulm_intervention_start_date","Exposure","",         "text",     "Ngày bắt đầu can thiệp/phơi nhiễm",                    "",                                                                      "",                        "date_ymd",  "",    "",    "y", ""),
]
_PULM_COPD_OUTCOMES = [
    ("exacerbation_hosp","Outcomes","Kết cục chính",       "radio",    "Đợt cấp cần nhập viện",                                "0, Không | 1, Có",                                                     "",                        "",          "",    "",    "y", ""),
    ("exacerbation_hosp_date","Outcomes","",               "text",     "Ngày nhập viện do đợt cấp (lần đầu)",                  "",                                                                      "",                        "date_ymd",  "",    "",    "n", "[exacerbation_hosp] = '1'"),
    ("respiratory_death","Outcomes","",                    "radio",    "Tử vong do nguyên nhân hô hấp",                        "0, Không | 1, Có",                                                     "",                        "",          "",    "",    "n", ""),
    ("fev1_change_followup","Outcomes","Kết cục phụ",      "text",     "Thay đổi FEV1 (%) tại mốc theo dõi",                   "",                                                                      "So với nền",              "number",    "-100","100", "n", ""),
    ("follow_time_months","Outcomes","",                   "text",     "Thời gian theo dõi (tháng)",                          "",                                                                      "",                        "number",    "0",   "120", "y", ""),
]

# CHUYÊN KHOA: Thần kinh / Đột quỵ
_NEURO_STROKE_CLINICAL = [
    ("nihss_baseline","Clinical",    "Lâm sàng nền (Thần kinh)","text","Điểm NIHSS lúc nhập viện",                             "",                                                                      "National Institutes of Health Stroke Scale, 0-42","integer","0","42","y", ""),
    ("stroke_type",   "Clinical",    "",                   "dropdown", "Loại đột quỵ",                                        "1, Nhồi máu não | 2, Xuất huyết não | 3, Xuất huyết dưới nhện | 4, Không xác định","","","","","y", ""),
    ("mrs_baseline",  "Clinical",    "",                   "dropdown", "mRS nền (trước biến cố, nếu có bệnh sử đột quỵ cũ)",  "0, mRS 0 | 1, mRS 1 | 2, mRS 2 | 3, mRS 3 | 4, mRS 4 | 5, mRS 5",     "modified Rankin Scale",   "",          "",    "",    "n", ""),
]
_NEURO_STROKE_MEDS = [
    ("antiplatelet",  "Meds",        "Thuốc nền (Thần kinh)","radio",  "Đang dùng kháng kết tập tiểu cầu",                     "0, Không | 1, Aspirin | 2, Clopidogrel | 3, Phối hợp kép (DAPT)",     "",                        "",          "",    "",    "y", ""),
    ("statin_use",    "Meds",        "",                   "radio",    "Đang dùng statin",                                     "0, Không | 1, Có",                                                     "",                        "",          "",    "",    "y", ""),
    ("thrombolysis",  "Meds",        "",                   "radio",    "Đã dùng tiêu sợi huyết (rtPA)",                        "0, Không | 1, Có",                                                     "Chỉ áp dụng nhồi máu não cấp","",       "",    "",    "n", ""),
]
_NEURO_STROKE_EXPOSURE = [
    ("stroke_intervention_type","Exposure","Phơi nhiễm/Can thiệp (Thần kinh)","dropdown","Loại thuốc/can thiệp",              "1, Kháng kết tập tiểu cầu | 2, Statin | 3, Tiêu sợi huyết | 4, Lấy huyết khối cơ học | 5, Khác","","","","","y",""),
    ("stroke_intervention_dose","Exposure","",             "text",     "Liều (mg/ngày, nếu áp dụng)",                          "",                                                                      "",                        "number",    "0",   "1000","n", ""),
    ("stroke_intervention_start_date","Exposure","",       "text",     "Ngày bắt đầu can thiệp/phơi nhiễm",                    "",                                                                      "",                        "date_ymd",  "",    "",    "y", ""),
]
_NEURO_STROKE_OUTCOMES = [
    ("mrs_followup",  "Outcomes",    "Kết cục chính",      "dropdown", "mRS tại mốc theo dõi (thường 90 ngày)",               "0, mRS 0 | 1, mRS 1 | 2, mRS 2 | 3, mRS 3 | 4, mRS 4 | 5, mRS 5 | 6, mRS 6 (tử vong)","","","","","y",""),
    ("stroke_recurrence","Outcomes","",                    "radio",    "Tái phát đột quỵ",                                     "0, Không | 1, Có",                                                     "",                        "",          "",    "",    "y", ""),
    ("stroke_recurrence_date","Outcomes","",               "text",     "Ngày tái phát đột quỵ",                                "",                                                                      "",                        "date_ymd",  "",    "",    "n", "[stroke_recurrence] = '1'"),
    ("stroke_death",  "Outcomes",    "Kết cục phụ",        "radio",    "Tử vong (mọi nguyên nhân)",                            "0, Không | 1, Có",                                                     "",                        "",          "",    "",    "n", ""),
    ("follow_time_months","Outcomes","",                   "text",     "Thời gian theo dõi (tháng)",                          "",                                                                      "",                        "number",    "0",   "120", "y", ""),
]

# CHUYÊN KHOA: Cơ xương khớp / Đau mạn
_MSK_PAIN_CLINICAL = [
    ("pain_nrs_baseline","Clinical", "Lâm sàng nền (Đau mạn)","text",  "Điểm đau NRS nền (0-10)",                              "",                                                                      "Numeric Rating Scale",   "integer",   "0",   "10",  "y", ""),
    ("pain_location",  "Clinical",   "",                   "dropdown", "Vị trí đau chính",                                     "1, Lưng | 2, Cổ | 3, Khớp gối | 4, Khớp háng | 5, Đa vị trí | 6, Khác","",                       "",          "",    "",    "y", ""),
    ("pain_duration_months","Clinical","",                 "text",     "Thời gian đau (tháng)",                                "",                                                                      "≥3 tháng theo định nghĩa đau mạn","integer","3","600","y", ""),
]
_MSK_PAIN_MEDS = [
    ("analgesic_type","Meds",        "Thuốc nền (Đau mạn)","dropdown", "Loại giảm đau đang dùng",                              "0, Không dùng | 1, Paracetamol | 2, NSAID | 3, Opioid yếu | 4, Opioid mạnh | 5, Phối hợp","","","","","y", ""),
    ("opioid_mme_per_day","Meds",    "",                   "text",     "Liều opioid quy đổi MME/ngày (nếu dùng opioid)",       "",                                                                      "Morphine Milligram Equivalent — chỉ điền nếu analgesic_type gồm opioid","number","0","2000","n","[analgesic_type] = '3' or [analgesic_type] = '4'"),
]
_MSK_PAIN_EXPOSURE = [
    ("msk_intervention_type","Exposure","Phơi nhiễm/Can thiệp (Đau mạn)","dropdown","Loại can thiệp",                          "1, Thuốc giảm đau | 2, Vật lý trị liệu | 3, Can thiệp tâm lý (CBT) | 4, Phối hợp đa mô thức | 5, Khác","","","","","y",""),
    ("msk_intervention_dose","Exposure","",                "text",     "Liều/tần suất (nếu áp dụng)",                          "",                                                                      "[CẦN GHI RÕ ĐƠN VỊ theo loại can thiệp]","text","","", "n", ""),
    ("msk_intervention_start_date","Exposure","",          "text",     "Ngày bắt đầu can thiệp/phơi nhiễm",                    "",                                                                      "",                        "date_ymd",  "",    "",    "y", ""),
]
_MSK_PAIN_OUTCOMES = [
    ("pain_nrs_change","Outcomes",   "Kết cục chính",      "text",     "Thay đổi điểm đau NRS tại mốc theo dõi",               "",                                                                      "So với nền",              "number",    "-10", "10",  "y", ""),
    ("function_score","Outcomes",    "",                   "notes",    "Điểm chức năng (vd Oswestry nếu đau lưng) [CẦN xác định — hệ thống không tự tin đủ về thang đo chuẩn cho mọi vị trí đau]", "", "[CẦN — bác sĩ chọn thang phù hợp vị trí đau: Oswestry/RMDQ cho lưng, WOMAC cho khớp gối/háng]", "", "", "", "n", ""),
    ("opioid_dependence_signal","Outcomes","Kết cục phụ",  "radio",    "Dấu hiệu lệ thuộc/lạm dụng opioid mới xuất hiện",      "0, Không | 1, Có — cần đánh giá thêm",                                "An toàn — theo dõi sát nếu dùng opioid","","","","n", ""),
    ("follow_time_months","Outcomes","",                   "text",     "Thời gian theo dõi (tháng)",                          "",                                                                      "",                        "number",    "0",   "120", "y", ""),
]

# CHUYÊN KHOA: Tâm thần / Trầm cảm-Lo âu
_PSYCH_DEP_ANX_CLINICAL = [
    ("phq9_baseline", "Clinical",    "Lâm sàng nền (Tâm thần)","text",  "Điểm PHQ-9 nền",                                       "",                                                                      "Patient Health Questionnaire-9, thang 0-27","integer","0","27","y", ""),
    ("gad7_baseline", "Clinical",    "",                   "text",     "Điểm GAD-7 nền",                                       "",                                                                      "Generalized Anxiety Disorder-7, thang 0-21","integer","0","21","n", ""),
    ("suicidal_ideation_baseline","Clinical","",           "radio",    "Ý tưởng tự sát tại thời điểm tuyển (PHQ-9 mục 9)",     "0, Không | 1, Có — CẦN ĐÁNH GIÁ AN TOÀN NGAY",                        "An toàn — không chờ hoàn tất CRF nếu dương tính","","","","y", ""),
]
_PSYCH_DEP_ANX_MEDS = [
    ("ssri_snri_use", "Meds",        "Thuốc nền (Tâm thần)","dropdown", "Đang dùng SSRI/SNRI",                                 "0, Không | 1, SSRI | 2, SNRI | 3, Khác",                              "",                        "",          "",    "",    "y", ""),
    ("psychotherapy_use","Meds",     "",                   "radio",    "Đang có liệu pháp tâm lý",                             "0, Không | 1, Có",                                                     "",                        "",          "",    "",    "y", ""),
]
_PSYCH_DEP_ANX_EXPOSURE = [
    ("psych_intervention_type","Exposure","Phơi nhiễm/Can thiệp (Tâm thần)","dropdown","Loại can thiệp",                       "1, SSRI | 2, SNRI | 3, Liệu pháp tâm lý (CBT/IPT) | 4, Phối hợp thuốc+tâm lý | 5, Khác","","","","","y",""),
    ("psych_intervention_dose","Exposure","",              "text",     "Liều (mg/ngày, nếu dùng thuốc)",                       "",                                                                      "",                        "number",    "0",   "600", "n", ""),
    ("psych_intervention_start_date","Exposure","",        "text",     "Ngày bắt đầu can thiệp/phơi nhiễm",                    "",                                                                      "",                        "date_ymd",  "",    "",    "y", ""),
]
_PSYCH_DEP_ANX_OUTCOMES = [
    ("phq9_response","Outcomes",     "Kết cục chính",      "radio",    "Đáp ứng điều trị (giảm ≥50% điểm PHQ-9 so với nền)",  "0, Không | 1, Có",                                                     "",                        "",          "",    "",    "y", ""),
    ("phq9_remission","Outcomes",    "",                   "radio",    "Thuyên giảm (PHQ-9 < 5 tại mốc theo dõi)",             "0, Không | 1, Có",                                                     "",                        "",          "",    "",    "n", ""),
    ("phq9_followup","Outcomes",     "",                   "text",     "Điểm PHQ-9 tại mốc theo dõi",                          "",                                                                      "",                        "integer",   "0",   "27",  "y", ""),
    ("suicidal_ideation_new","Outcomes","Kết cục phụ (an toàn)","radio","Ý tưởng tự sát MỚI xuất hiện trong theo dõi",         "0, Không | 1, Có — CẦN XỬ TRÍ AN TOÀN NGAY",                          "Biến cố an toàn cần theo dõi sát mọi lần tái khám","","","","y", ""),
    ("follow_time_months","Outcomes","",                   "text",     "Thời gian theo dõi (tháng)",                          "",                                                                      "",                        "number",    "0",   "120", "y", ""),
]

# CHUYÊN KHOA: Tiêu hóa
# Điểm hoạt động bệnh: KHÔNG bịa công thức chi tiết (Child-Pugh cần 5 tiêu
# chí bilirubin/albumin/INR/báng/não gan; Mayo score cần 4 tiểu mục nội soi/
# phân/đánh giá bác sĩ) — để field NHẬP ĐIỂM TỔNG đã tính sẵn (bác sĩ/điều
# dưỡng tính theo thang chuẩn ở nơi khác) thay vì hệ thống tự suy ra từng
# tiểu mục, tránh sai lệch nếu ghi nhớ nhầm ngưỡng.
_GASTRO_CLINICAL = [
    ("gastro_diagnosis_group","Clinical","Lâm sàng nền (Tiêu hóa)","dropdown","Nhóm chẩn đoán tiêu hóa mạn",                   "1, Viêm loét đại tràng | 2, Bệnh Crohn | 3, Xơ gan | 4, Viêm gan mạn (B/C) | 5, GERD/trào ngược | 6, Khác","","","","","y",""),
    ("disease_activity_score","Clinical","",               "notes",    "Điểm hoạt động bệnh [CẦN xác định — hệ thống không tự tin đủ về thang đo chuẩn]", "", "[CẦN — bác sĩ chọn & ghi rõ thang: Mayo score cho viêm loét đại tràng, Child-Pugh/MELD cho xơ gan, HBV DNA/HCV RNA cho viêm gan virus]", "", "", "", "n", ""),
    ("child_pugh_class","Clinical","",                     "dropdown", "Phân độ Child-Pugh (chỉ điền nếu xơ gan)",             "0, Không áp dụng | 1, Child A | 2, Child B | 3, Child C",             "Chỉ áp dụng nếu gastro_diagnosis_group = xơ gan","","","","n", "[gastro_diagnosis_group] = '3'"),
]
_GASTRO_MEDS = [
    ("gastro_med_class","Meds",      "Thuốc nền (Tiêu hóa)","dropdown", "Nhóm thuốc điều trị nền đang dùng",                   "0, Không dùng | 1, 5-ASA | 2, Corticosteroid | 3, Ức chế miễn dịch (thiopurine/MTX) | 4, Sinh học (anti-TNF...) | 5, Ức chế bơm proton (PPI) | 6, Kháng virus viêm gan | 7, Khác","","","","","y", ""),
]
_GASTRO_EXPOSURE = [
    ("gastro_intervention_type","Exposure","Phơi nhiễm/Can thiệp (Tiêu hóa)","dropdown","Loại thuốc/can thiệp",                "1, 5-ASA | 2, Corticosteroid | 3, Sinh học (biologic) | 4, PPI | 5, Kháng virus | 6, Khác","","","","","y",""),
    ("gastro_intervention_dose","Exposure","",             "text",     "Liều (mg/ngày hoặc mg/đợt, nếu áp dụng)",              "",                                                                      "",                        "number",    "0",   "5000","n", ""),
    ("gastro_intervention_start_date","Exposure","",       "text",     "Ngày bắt đầu can thiệp/phơi nhiễm",                    "",                                                                      "",                        "date_ymd",  "",    "",    "y", ""),
]
_GASTRO_OUTCOMES = [
    ("hepatic_decompensation","Outcomes","Kết cục chính",  "radio",    "Biến cố gan mất bù mới (báng/xuất huyết TM/não gan)",  "0, Không | 1, Có",                                                     "Chỉ áp dụng nhóm bệnh gan",   "",     "",    "",    "n", ""),
    ("gi_bleeding","Outcomes",       "",                   "radio",    "Xuất huyết tiêu hóa",                                  "0, Không | 1, Có — trên | 2, Có — dưới",                              "",                        "",          "",    "",    "y", ""),
    ("gastro_hospitalization","Outcomes","",               "radio",    "Nhập viện liên quan bệnh tiêu hóa",                    "0, Không | 1, Có",                                                     "",                        "",          "",    "",    "y", ""),
    ("gastro_hospitalization_date","Outcomes","",          "text",     "Ngày nhập viện (lần đầu liên quan)",                   "",                                                                      "",                        "date_ymd",  "",    "",    "n", "[gastro_hospitalization] = '1'"),
    ("follow_time_months","Outcomes","",                   "text",     "Thời gian theo dõi (tháng)",                          "",                                                                      "",                        "number",    "0",   "120", "y", ""),
]

# CHUYÊN KHOA: Khảo sát hài lòng người bệnh (dịch vụ y tế, KHÔNG phải bệnh lý
# lâm sàng cụ thể — không đo sinh hiệu/bệnh nền; xem needs_vitals ở
# _SPECIALTY_BUNDLES). Cấu trúc 5 lĩnh vực + điểm chung tham khảo khung phổ
# biến trong khảo sát hài lòng bệnh viện tại Việt Nam (Bộ Y tế) — CHƯA kiểm
# chứng trực tuyến số quyết định/nội dung chính xác, giữ nguyên nhãn
# [CẦN KIỂM CHỨNG NGUỒN CHÍNH THỨC] cho tới khi bác sĩ đối chiếu bản gốc; nếu
# đơn vị dùng bộ công cụ khác đã kiểm định, thay thế toàn bộ khối này.
_HAI_LONG_CLINICAL = [
    ("visit_type",     "Clinical", "Bối cảnh lượt khám (Khảo sát hài lòng)", "radio", "Loại lượt khám", "1, Khám mới lần đầu tại khoa | 2, Tái khám", "", "", "", "", "y", ""),
    ("payment_type",   "Clinical", "",                   "dropdown", "Hình thức chi trả",                                    "1, Bảo hiểm y tế (BHYT) | 2, Khám theo yêu cầu/dịch vụ | 3, Tự chi trả không BHYT | 4, Khác", "", "", "", "", "y", ""),
    ("wait_time_min",  "Clinical", "",                   "text",     "Thời gian chờ khám (phút, từ đăng ký đến khi được khám)", "",                                                                    "Người bệnh tự ước lượng hoặc ghi nhận thực tế nếu có hệ thống hẹn giờ", "number", "0", "600", "n", ""),
    ("visit_freq_year","Clinical", "",                   "text",     "Số lần đến khám tại khoa trong 12 tháng qua",          "",                                                                      "",                        "integer",   "1",   "365", "n", ""),
]
_HAI_LONG_EXPOSURE = [
    ("occupation",     "Exposure", "Yếu tố liên quan đến hài lòng (mục tiêu phân tích)", "dropdown", "Nghề nghiệp", "1, Cán bộ/công chức/viên chức (kể cả quân nhân) | 2, Lao động tự do/kinh doanh | 3, Hưu trí/nội trợ | 4, Khác", "", "", "", "", "n", ""),
    ("income_self_rated","Exposure","",                  "dropdown", "Mức thu nhập tự đánh giá",                             "1, Thấp | 2, Trung bình | 3, Khá/cao | 9, Không muốn trả lời",       "",                        "",          "",    "",    "n", ""),
]
_HAI_LONG_OUTCOMES = [
    ("domain_access_score",     "Outcomes", "Điểm hài lòng theo lĩnh vực (kết cục chính)", "text", "Điểm hài lòng — Khả năng tiếp cận dịch vụ",              "", "Thang Likert theo bộ công cụ đã chọn [CẦN KIỂM CHỨNG NGUỒN CHÍNH THỨC]", "number", "1", "5", "y", ""),
    ("domain_transparency_score","Outcomes","",          "text",     "Điểm hài lòng — Minh bạch thông tin, thủ tục khám bệnh", "", "",                                                                     "number",    "1",   "5",   "y", ""),
    ("domain_facility_score",   "Outcomes", "",          "text",     "Điểm hài lòng — Cơ sở vật chất, phương tiện phục vụ",    "", "",                                                                     "number",    "1",   "5",   "y", ""),
    ("domain_staff_attitude_score","Outcomes","",        "text",     "Điểm hài lòng — Thái độ ứng xử, năng lực chuyên môn nhân viên y tế", "", "",                                                        "number",    "1",   "5",   "y", ""),
    ("domain_service_result_score","Outcomes","",        "text",     "Điểm hài lòng — Kết quả cung cấp dịch vụ khám chữa bệnh", "", "",                                                                    "number",    "1",   "5",   "y", ""),
    ("overall_satisfaction_score","Outcomes","",         "text",     "Điểm hài lòng chung (kết cục chính tổng hợp)",           "", "Cách tính theo hướng dẫn chấm điểm của bộ công cụ đã chọn",           "number",    "1",   "5",   "y", ""),
    ("overall_satisfaction_binary","Outcomes","Kết cục phụ","radio", "Hài lòng chung (nhị phân, theo ngưỡng cắt bộ công cụ)",  "0, Không hài lòng | 1, Hài lòng", "Ngưỡng cắt theo hướng dẫn chính thức của bộ công cụ [CẦN KIỂM CHỨNG NGUỒN CHÍNH THỨC]", "", "", "", "y", ""),
    ("willing_to_return","Outcomes","",                  "radio",    "Sẵn sàng quay lại khám/giới thiệu người khác",           "0, Không | 1, Có",                                                     "",                        "",          "",    "",    "n", ""),
]

# GENERIC — dùng khi KHÔNG khớp chuyên khoa nào. KHÔNG bịa nội dung lâm sàng
# cụ thể (vì có thể sai hoàn toàn với đề tài thật) — chỉ đặt placeholder rõ
# ràng buộc bác sĩ phải tự định nghĩa theo PICO/SAP của chính đề tài.
_GENERIC_EXPOSURE = [
    ("exposure_var",  "Exposure",    "Phơi nhiễm/Can thiệp [CẦN ĐẶT TÊN THEO PICO]","text","[CẦN] Tên biến phơi nhiễm/can thiệp chính","",                                                     "[CẦN ĐỊNH NGHĨA — hệ thống không tự đoán được cho chuyên khoa này]","","","","y",""),
    ("exposure_start_date","Exposure","",                 "text",     "Ngày bắt đầu phơi nhiễm/can thiệp",                    "",                                                                      "",                        "date_ymd",  "",    "",    "y", ""),
]
_GENERIC_OUTCOMES = [
    ("primary_outcome","Outcomes",   "Kết cục chính [CẦN ĐẶT TÊN THEO SAP §2]","text","[CẦN] Tên + định nghĩa kết cục chính",  "",                                                                      "[CẦN ĐỊNH NGHĨA — hệ thống không tự đoán được cho chuyên khoa này]","","","","y",""),
    ("primary_outcome_date","Outcomes","",                "text",     "Ngày xảy ra kết cục chính",                            "",                                                                      "",                        "date_ymd",  "",    "",    "n", "[primary_outcome] = '1'"),
    ("follow_time_months","Outcomes","",                  "text",     "Thời gian theo dõi (tháng)",                          "",                                                                      "",                        "number",    "0",   "120", "y", ""),
]

_SPECIALTY_BUNDLES = {
    "cardiology_hf": {
        "clinical": _CARDIO_HF_CLINICAL, "labs": _CARDIO_HF_LABS, "meds": _CARDIO_HF_MEDS,
        "exposure": _CARDIO_HF_EXPOSURE, "outcomes": _CARDIO_HF_OUTCOMES,
        "comorbid": _CARDIOMETABOLIC_COMORBIDITIES, "labs_base": _CARDIOMETABOLIC_LABS,
    },
    "metabolic_diabetes": {
        "clinical": _METABOLIC_CLINICAL, "labs": [], "meds": _METABOLIC_MEDS,
        "exposure": _METABOLIC_EXPOSURE, "outcomes": _METABOLIC_OUTCOMES,
        "comorbid": _CARDIOMETABOLIC_COMORBIDITIES, "labs_base": _CARDIOMETABOLIC_LABS,
    },
    # THÊM 2026-07-02 — 6 bundle mới. comorbid/labs_base dùng _GENERIC_* (thay
    # vì _CARDIOMETABOLIC_*) vì bệnh CHÍNH đang nghiên cứu của các bundle này
    # (CKD/COPD/đột quỵ...) đã có field CHI TIẾT riêng ở "clinical" — dùng lại
    # field "bệnh kèm" cùng tên (vd _CARDIOMETABOLIC_COMORBIDITIES có "ckd")
    # sẽ trùng lặp gây nhầm lẫn giữa "bệnh đang nghiên cứu" và "bệnh đi kèm".
    "nephrology_ckd": {
        "clinical": _NEPHRO_CKD_CLINICAL, "labs": [], "meds": _NEPHRO_CKD_MEDS,
        "exposure": _NEPHRO_CKD_EXPOSURE, "outcomes": _NEPHRO_CKD_OUTCOMES,
        "comorbid": _GENERIC_COMORBIDITIES, "labs_base": _CARDIOMETABOLIC_LABS,
    },
    "pulmonology_copd_asthma": {
        "clinical": _PULM_COPD_CLINICAL, "labs": [], "meds": _PULM_COPD_MEDS,
        "exposure": _PULM_COPD_EXPOSURE, "outcomes": _PULM_COPD_OUTCOMES,
        "comorbid": _GENERIC_COMORBIDITIES, "labs_base": _GENERIC_LABS,
    },
    "neurology_stroke": {
        "clinical": _NEURO_STROKE_CLINICAL, "labs": [], "meds": _NEURO_STROKE_MEDS,
        "exposure": _NEURO_STROKE_EXPOSURE, "outcomes": _NEURO_STROKE_OUTCOMES,
        "comorbid": _GENERIC_COMORBIDITIES, "labs_base": _GENERIC_LABS,
    },
    "musculoskeletal_pain": {
        "clinical": _MSK_PAIN_CLINICAL, "labs": [], "meds": _MSK_PAIN_MEDS,
        "exposure": _MSK_PAIN_EXPOSURE, "outcomes": _MSK_PAIN_OUTCOMES,
        "comorbid": _GENERIC_COMORBIDITIES, "labs_base": _GENERIC_LABS,
    },
    "psychiatry_depression_anxiety": {
        "clinical": _PSYCH_DEP_ANX_CLINICAL, "labs": [], "meds": _PSYCH_DEP_ANX_MEDS,
        "exposure": _PSYCH_DEP_ANX_EXPOSURE, "outcomes": _PSYCH_DEP_ANX_OUTCOMES,
        "comorbid": _GENERIC_COMORBIDITIES, "labs_base": _GENERIC_LABS,
    },
    "gastroenterology": {
        "clinical": _GASTRO_CLINICAL, "labs": [], "meds": _GASTRO_MEDS,
        "exposure": _GASTRO_EXPOSURE, "outcomes": _GASTRO_OUTCOMES,
        "comorbid": _GENERIC_COMORBIDITIES, "labs_base": _GENERIC_LABS,
    },
    # THÊM 2026-07-17: needs_vitals=False — khảo sát hài lòng KHÔNG đo sinh
    # hiệu; các bundle khác ở trên giữ nguyên hành vi cũ (mặc định True qua
    # .get(), xem build_redcap_rows) để không đổi CRF của đề tài đang chạy.
    # SỬA 2026-07-17 (bình duyệt agent `dao-duc-dang-ky` phát hiện thật):
    # comorbid/labs_base trước đây dùng _GENERIC_COMORBIDITIES/_GENERIC_LABS
    # (đái tháo đường, tăng huyết áp, xét nghiệm nền...) — nhưng PICO của một
    # khảo sát hài lòng (xem _HAI_LONG_EXPOSURE ở trên) KHÔNG liệt kê bệnh
    # nền là yếu tố liên quan, và ICF không hề công bố sẽ hỏi/thu thập thông
    # tin bệnh nền — thu thêm dữ liệu ngoài mục đích đã công bố vi phạm
    # nguyên tắc tối thiểu hóa dữ liệu (data minimization, Luật 91/2025/QH15)
    # và tạo khoảng cách minh bạch giữa ICF và CRF thật. Để rỗng — nếu bác sĩ
    # thật sự cần khảo sát bệnh nền làm yếu tố liên quan, phải tự thêm CÓ chủ
    # đích và cập nhật ICF tương ứng, không để hệ thống ngầm định.
    "patient_satisfaction": {
        "clinical": _HAI_LONG_CLINICAL, "labs": [], "meds": [],
        "exposure": _HAI_LONG_EXPOSURE, "outcomes": _HAI_LONG_OUTCOMES,
        "comorbid": [], "labs_base": [],
        "needs_vitals": False,
    },
    "generic": {
        "clinical": [], "labs": [], "meds": [],
        "exposure": _GENERIC_EXPOSURE, "outcomes": _GENERIC_OUTCOMES,
        "comorbid": _GENERIC_COMORBIDITIES, "labs_base": _GENERIC_LABS,
    },
}

# SỬA 2026-07-17: ae_any/ae_description/ae_grade/sae_any (phân độ CTCAE, theo
# dõi biến cố bất lợi nghiêm trọng — thuật ngữ ICH-GCP của thử nghiệm CAN
# THIỆP) trước đây nhồi CỨNG vào MỌI thiết kế — một khảo sát hài lòng (không
# can thiệp, không xâm lấn) có CRF ghi "phân độ CTCAE" là dấu hiệu lộ template
# thử nghiệm lâm sàng, gây nhầm lẫn tập huấn và có thể khiến hội đồng nghi
# ngờ phân loại nguy cơ thật. Tách riêng khỏi complete_flag (trạng thái hoàn
# thành phiếu — hoàn toàn tổng quát, không ngụ ý can thiệp) — xem
# build_redcap_rows() để biết thiết kế nào ghép _BASE_SAFETY_AE.
_BASE_SAFETY_AE = [
    ("ae_any",        "Safety",      "An toàn",            "radio",    "Có biến cố bất lợi",                                   "0, Không | 1, Có",                                                     "",                        "",          "",    "",    "y", ""),
    ("ae_description","Safety",      "",                   "notes",    "Mô tả biến cố bất lợi",                                "",                                                                      "",                        "",          "",    "",    "n", "[ae_any] = '1'"),
    ("ae_grade",      "Safety",      "",                   "dropdown", "Phân độ biến cố (CTCAE v5)",                           "1, Độ 1 (nhẹ) | 2, Độ 2 (trung bình) | 3, Độ 3 (nặng) | 4, Độ 4 (đe dọa tính mạng) | 5, Độ 5 (tử vong)", "", "", "", "", "n", "[ae_any] = '1'"),
    ("sae_any",       "Safety",      "",                   "radio",    "Có biến cố bất lợi nghiêm trọng (SAE)",               "0, Không | 1, Có",                                                     "",                        "",          "",    "",    "y", ""),
]
_BASE_ADMIN_COMPLETE = [
    ("complete_flag", "Admin",       "Trạng thái phiếu",   "radio",    "Trạng thái hoàn thành phiếu",                          "0, Chưa hoàn thành | 1, Chưa xác minh | 2, Hoàn thành",              "",                        "",          "",    "",    "n", ""),
]

# RCT thêm: randomization
_RCT_EXTRA = [
    ("randomization_id","Randomization","Ngẫu nhiên hóa", "text",     "Mã ngẫu nhiên hóa",                                    "",                                                                      "",                        "",          "",    "",    "y", ""),
    ("arm",           "Randomization","",                  "radio",    "Nhóm phân công",                                       "0, Đối chứng | 1, Can thiệp",                                         "",                        "",          "",    "",    "y", ""),
    ("allocation_date","Randomization","",                 "text",     "Ngày phân bổ ngẫu nhiên",                              "",                                                                      "",                        "date_ymd",  "",    "",    "y", ""),
    ("blinding_status","Randomization","",                 "dropdown", "Tình trạng mù",                                        "1, Mở | 2, Mù đơn | 3, Mù đôi | 4, Mù ba",                          "",                        "",          "",    "",    "n", ""),
]

# Chẩn đoán thêm
_DIAGNOSTIC_EXTRA = [
    ("index_test_result","Diagnostic","Xét nghiệm chỉ số","text",    "Kết quả xét nghiệm chỉ số (giá trị liên tục)",          "",                                                                      "[CẦN ĐƠN VỊ]",           "number",    "",    "",    "y", ""),
    ("reference_standard","Diagnostic","",                "radio",    "Kết quả tiêu chuẩn vàng",                              "0, Âm tính | 1, Dương tính",                                          "",                        "",          "",    "",    "y", ""),
    ("test_date",     "Diagnostic",  "",                  "text",     "Ngày thực hiện xét nghiệm",                             "",                                                                      "",                        "date_ymd",  "",    "",    "n", ""),
    ("positivity_cutoff","Diagnostic","",                 "text",     "Ngưỡng dương tính áp dụng",                             "",                                                                      "[CẦN XÁC ĐỊNH TRƯỚC - pre-specified]","number","", "", "y", ""),
    ("sensitivity_confirmed","Diagnostic","",             "text",     "Độ nhạy xác nhận tại cơ sở (%)",                       "",                                                                      "",                        "number",    "0",   "100", "n", ""),
    ("specificity_confirmed","Diagnostic","",             "text",     "Độ đặc hiệu xác nhận tại cơ sở (%)",                   "",                                                                      "",                        "number",    "0",   "100", "n", ""),
]

# THÊM 2026-07-22 (vòng lặp kiểm tra-hoàn thiện vòng 7, phát hiện CRITICAL):
# build_redcap_rows() trước đây KHÔNG có nhánh riêng cho design_code=
# "prediction" — rơi vào else (cohort/case_control/cross_sectional), sinh CRF
# dùng bundle["exposure"]/bundle["outcomes"] kiểu cohort, KHÔNG có trường nào
# cho: cờ phân biệt tập PHÁT TRIỂN (development) vs tập ĐÁNH GIÁ (validation)
# — yêu cầu CỐT LÕI của TRIPOD+AI (build_strobe_flowchart() trong CHÍNH file
# này đã vẽ rõ 2 tập D/E cho thiết kế này) — hay điểm nguy cơ mô hình dự đoán.
# Bundle["clinical"]/["comorbid"]/["labs_base"]/["labs"]/["meds"] đã cung cấp
# GIÁ TRỊ ứng viên dự báo hợp lý (tuổi/bệnh nền/xét nghiệm) nên không cần bộ
# trường ứng viên dự báo riêng — phần THẬT sự thiếu là cờ tách tập D/E.
_PREDICTION_EXTRA = [
    ("dataset_split",       "Prediction", "Mô hình tiên lượng (TRIPOD+AI)", "radio",
     "Tập dữ liệu (phát triển hay đánh giá mô hình)",
     "0, Phát triển (development) | 1, Đánh giá/kiểm định (validation)",
     "[CẦN — phân chia TRƯỚC khi xem kết cục, KHÔNG phân chia sau khi biết kết quả — tránh rò rỉ dữ liệu]",
     "", "", "", "y", ""),
    ("predicted_outcome_time","Prediction", "",                             "text",
     "Thời điểm dự báo kết cục (đơn vị thời gian kể từ mốc bắt đầu)",
     "", "[CẦN ĐƠN VỊ — vd tháng/năm]", "number", "0", "", "y", ""),
    ("model_predicted_risk", "Prediction", "",                             "text",
     "Xác suất/điểm nguy cơ do mô hình dự đoán (nếu đã fit mô hình)",
     "", "[Điền SAU khi mô hình đã fit — KHÔNG điền trước khi khóa dữ liệu phát triển, tránh rò rỉ]",
     "number", "0", "1", "n", ""),
]

# SR/MA: biểu mẫu trích xuất
_SRMA_FIELDS = [
    ("study_id",      "Extraction",  "Trích xuất SR/MA",   "text",     "Mã nghiên cứu (Tác giả_Năm)",                         "",                                                                      "",                        "",          "",    "",    "y", ""),
    ("first_author",  "Extraction",  "",                   "text",     "Tác giả đầu tiên",                                    "",                                                                      "",                        "",          "",    "",    "y", ""),
    ("year",          "Extraction",  "",                   "text",     "Năm xuất bản",                                         "",                                                                      "",                        "integer",   "1980","2030","y", ""),
    ("journal",       "Extraction",  "",                   "text",     "Tên tạp chí",                                          "",                                                                      "",                        "",          "",    "",    "y", ""),
    ("design_type",   "Extraction",  "",                   "dropdown", "Loại thiết kế nghiên cứu",                             "1, RCT | 2, Cohort | 3, Case-control | 4, Cắt ngang | 5, Khác",       "",                        "",          "",    "",    "y", ""),
    ("n_intervention","Extraction",  "",                   "text",     "Cỡ mẫu nhóm can thiệp/phơi nhiễm",                   "",                                                                      "",                        "integer",   "0",   "500000","n",""),
    ("n_control",     "Extraction",  "",                   "text",     "Cỡ mẫu nhóm đối chứng",                               "",                                                                      "",                        "integer",   "0",   "500000","n",""),
    ("effect_estimate","Extraction", "",                   "text",     "Ước lượng hiệu quả (HR/OR/RR/MD)",                    "",                                                                      "",                        "number",    "",    "",    "y", ""),
    ("ci_lower",      "Extraction",  "",                   "text",     "Giới hạn dưới 95% CI",                                "",                                                                      "",                        "number",    "",    "",    "y", ""),
    ("ci_upper",      "Extraction",  "",                   "text",     "Giới hạn trên 95% CI",                                "",                                                                      "",                        "number",    "",    "",    "y", ""),
    ("rob_score",     "Extraction",  "",                   "dropdown", "Nguy cơ sai lệch",                                     "1, Thấp | 2, Một số lo ngại | 3, Cao",                                "",                        "",          "",    "",    "y", ""),
    ("inclusion_confirmed","Extraction","",               "radio",    "Đủ tiêu chuẩn đưa vào (xác nhận 2 người)",            "0, Không | 1, Có",                                                     "",                        "",          "",    "",    "y", ""),
]


# THÊM 2026-07-24 (vòng lặp kiểm tra-hoàn thiện vòng 20, phát hiện HIGH): G5
# trước đây KHÔNG có nhánh riêng cho design_code="economic" — rơi vào nhánh
# "mặc định" cohort/case_control/cross_sectional, sinh CRF LÂM SÀNG cho bệnh
# nhân cá thể (sinh hiệu, bệnh nền, exposure/outcome kiểu cohort) HOÀN TOÀN
# KHÔNG có trường nào cho các dữ liệu cốt lõi của CHEERS 2022 (Husereau D et
# al. Value Health. 2022;25(1):3-9, doi:10.1016/j.jval.2021.11.1351 — đã xác
# minh trực tiếp từ PDF gốc ở vòng 11) mà chính run_g7_auto.py đã cam kết báo
# cáo khi design_code/specialist_modules chứa "economic": góc nhìn phân tích,
# khung thời gian/tỷ lệ chiết khấu, danh mục chi phí, đơn giá, công cụ đo độ
# thỏa dụng (QALY), loại mô hình. Cùng lớp bug "rơi fallback sai" đã vá cho
# qualitative (vòng 2) và prediction (vòng 7), nay vá cho economic.
_ECONOMIC_FIELDS = [
    ("record_id",         "Admin",        "Quản lý hồ sơ",                          "text",     "Mã hồ sơ (record_id, ẩn danh, không PII)", "",                                                                       "",                                                                                    "",       "",   "",    "y", ""),
    ("perspective",       "Study Design", "Thiết kế phân tích kinh tế (CHEERS 2022)", "dropdown", "Góc nhìn phân tích",                       "1, Xã hội | 2, Người chi trả (BHYT) | 3, Bệnh viện/cơ sở y tế | 4, Khác", "[CẦN XÁC ĐỊNH TRƯỚC — CHEERS 2022 mục 6]",                                                                                "",       "",   "",    "y", ""),
    ("time_horizon",      "Study Design", "",                                        "text",     "Khung thời gian phân tích (đơn vị năm/tháng)", "",                                                                     "[CẦN — biện minh phù hợp với diễn tiến bệnh, CHEERS 2022 mục 9]",                                                        "number", "0",  "",    "y", ""),
    ("discount_rate",     "Study Design", "",                                        "text",     "Tỷ lệ chiết khấu áp dụng (%/năm)",           "",                                                                     "[CẦN — CHEERS 2022 mục 10 chỉ yêu cầu BÁO CÁO, KHÔNG quy định mức cụ thể]",                                              "number", "0",  "20",  "n", ""),
    ("cost_category",     "Costing",      "Chi phí (CHEERS 2022 mục 15-17)",         "checkbox", "Loại chi phí thu thập",                     "1, Trực tiếp y tế | 2, Trực tiếp ngoài y tế | 3, Gián tiếp (mất năng suất)", "",                                                                                                                     "",       "",   "",    "y", ""),
    ("resource_use_unit", "Costing",      "",                                        "text",     "Đơn vị sử dụng nguồn lực (vd số lần khám/ngày nằm viện)", "",                                                        "[CẦN — theo từng hạng mục chi phí]",                                                                                     "number", "0",  "",    "n", ""),
    ("unit_cost_value",   "Costing",      "",                                        "text",     "Đơn giá áp dụng",                           "",                                                                     "[CẦN NGUỒN — KHÔNG bịa đơn giá, dùng biểu giá BHYT/bệnh viện thật]",                                                     "number", "0",  "",    "y", ""),
    ("unit_cost_source",  "Costing",      "",                                        "text",     "Nguồn đơn giá (PMID/DOI/biểu giá chính thức + năm)", "",                                                             "",                                                                                                                        "",       "",   "",    "y", ""),
    ("utility_instrument","Outcomes",     "Thước đo hiệu quả (CHEERS 2022 mục 18-19)","dropdown", "Công cụ đo độ thỏa dụng (nếu CUA/QALY)",    "0, Không áp dụng (CEA/CBA) | 1, EQ-5D | 2, SF-6D | 3, Khác",              "",                                                                                                                        "",       "",   "",    "n", ""),
    ("utility_score",     "Outcomes",     "",                                        "text",     "Điểm thỏa dụng đo được",                    "",                                                                     "",                                                                                                                        "number", "0",  "1",   "n", ""),
    ("clinical_outcome_unit","Outcomes",  "",                                        "text",     "Đơn vị hiệu quả lâm sàng (nếu CEA — vd số ca tránh được biến cố)", "",                                              "",                                                                                                                        "",       "",   "",    "n", ""),
    ("model_type",        "Modeling",     "Mô hình hóa (nếu có)",                    "dropdown", "Loại mô hình",                              "0, Không dùng mô hình (dữ liệu thử nghiệm trực tiếp) | 1, Cây quyết định (decision tree) | 2, Markov | 3, Khác", "",                                                                                                     "",       "",   "",    "n", ""),
]

# THÊM 2026-07-21 (vòng lặp kiểm tra-hoàn thiện vòng 2, phát hiện CRITICAL: G5
# hoàn toàn thiếu nhánh design_code="qualitative", rơi vào nhánh "mặc định"
# cohort/case_control/cross_sectional và sinh CRF lâm sàng định lượng — huyết
# áp/xét nghiệm/exposure-outcome nhị phân — vô nghĩa với phỏng vấn sâu/nhóm
# tiêu điểm). Bộ trường này theo dõi lấy mẫu có chủ đích, mã hóa và bão hòa dữ
# liệu (COREQ/SRQR) thay vì biến lâm sàng số.
_QUALITATIVE_FIELDS = [
    # SỬA 2026-07-21 (vòng lặp kiểm tra-hoàn thiện vòng 3, phát hiện MEDIUM):
    # tên trường PHẢI là "record_id" (không phải "participant_id") — mọi hàm
    # sinh script dùng chung (gen_data_cleaning_script()::check_duplicates(),
    # báo cáo dữ liệu thiếu, kiểm tra trước phân tích) đều DÒ CỨNG cột tên
    # "record_id" để phát hiện trùng ID; dùng tên khác làm các kiểm tra đó
    # ÂM THẦM không chạy gì (điều kiện `if "record_id" in df.columns` false)
    # thay vì báo lỗi rõ ràng.
    ("record_id",           "Sampling",        "Quản lý người tham gia", "text",     "Mã người tham gia (record_id, ẩn danh, không PII)",         "",                                                              "", "",        "",   "",   "y", ""),
    ("sampling_category",   "Sampling",        "",                       "text",     "Nhóm lấy mẫu có chủ đích (vd theo mức tuân thủ/giới/thời gian mắc bệnh)", "",                                            "", "",        "",   "",   "y", ""),
    ("recruitment_date",    "Sampling",        "",                       "text",     "Ngày mời tham gia",                                          "",                                                              "", "date_ymd","",   "",   "y", ""),
    ("consent_confirmed",   "Sampling",        "",                       "radio",    "Đã ký đồng thuận tham gia",                                  "0, Không | 1, Có",                                             "", "",        "",   "",   "y", ""),
    ("interview_type",      "Data Collection", "Thu thập dữ liệu",       "dropdown", "Loại thu thập",                                              "1, Phỏng vấn sâu | 2, Nhóm tiêu điểm | 3, Quan sát thực địa", "", "",        "",   "",   "y", ""),
    ("interview_date",      "Data Collection", "",                      "text",     "Ngày thu thập",                                              "",                                                              "", "date_ymd","",   "",   "y", ""),
    ("audio_recorded",      "Data Collection", "",                      "radio",    "Có ghi âm (đã đồng thuận)",                                  "0, Không | 1, Có",                                             "", "",        "",   "",   "y", ""),
    ("transcript_id",       "Data Collection", "",                      "text",     "Mã bản gỡ băng (đã khử định danh)",                          "",                                                              "", "",        "",   "",   "y", ""),
    ("coder_assigned",      "Coding",          "Mã hóa chủ đề",          "text",     "Người mã hóa (≥2 người mã độc lập)",                        "",                                                              "", "",        "",   "",   "y", ""),
    ("coding_round",        "Coding",          "",                      "integer",  "Vòng mã hóa (1=mã mở, 2=mã trục...)",                        "",                                                              "", "integer", "1",  "5",  "y", ""),
    ("themes_identified",   "Coding",          "",                      "text",     "Chủ đề/mã xuất hiện (danh sách)",                            "",                                                              "", "",        "",   "",   "y", ""),
    ("saturation_reached",  "Saturation",      "Bão hòa dữ liệu",        "radio",    "Đã đạt bão hòa dữ liệu tại lượt phỏng vấn này",              "0, Chưa | 1, Có",                                              "", "",        "",   "",   "y", ""),
    ("saturation_criterion","Saturation",      "",                      "text",     "Tiêu chí xác định bão hòa (vd 3 lượt liên tiếp không có mã mới)", "",                                                        "", "",        "",   "",   "n", ""),
]


def build_redcap_rows(design_code: str, topic: str = "") -> tuple:
    """
    Xây dựng CRF theo loại thiết kế + chuyên khoa nhận diện từ topic.
    Trả về (rows, specialty) để artifact có thể báo minh bạch bundle nào
    đã được chọn — quan trọng vì bundle "generic" cần bác sĩ tự điền exposure/
    outcome thay vì tin nhầm rằng hệ thống đã tự xác định đúng.
    """
    specialty = detect_specialty(topic)
    bundle = _SPECIALTY_BUNDLES[specialty]
    # SỬA 2026-07-17: _BASE_VITALS (huyết áp/nhịp tim) trước đây bị nhồi CỨNG
    # vào MỌI thiết kế bất kể chuyên khoa — đúng bug làm CRF khảo sát hài lòng
    # có trường sinh hiệu vô nghĩa. Mặc định giữ nguyên True (không đổi hành vi
    # các bundle lâm sàng hiện có); chỉ bundle nào tự khai needs_vitals=False
    # (khảo sát/PROM không đo sinh hiệu) mới bỏ khối này.
    base_vitals = _BASE_VITALS if bundle.get("needs_vitals", True) else []

    # SỬA 2026-07-17 (bình duyệt đa vai trò cho đề tài hài lòng bệnh nhân C1a
    # phát hiện thật): censor/LTFU/protocol_deviation chỉ có ý nghĩa với thiết
    # kế THEO DÕI DỌC (rct — có kỳ theo dõi định trước; cohort — theo dõi
    # phơi nhiễm/kết cục qua thời gian). Biến cố bất lợi/SAE (thuật ngữ
    # ICH-GCP) chỉ có ý nghĩa khi có CAN THIỆP đang thử nghiệm (rct; cohort
    # trong hệ thống này thường là cohort phơi nhiễm thuốc — giữ để an toàn).
    # case_control (hồi cứu, không theo dõi tiến cứu quần thể), cross_sectional
    # (một thời điểm) và diagnostic (so sánh index-test/tiêu chuẩn vàng một
    # lần) KHÔNG có trục thời gian/can thiệp tương ứng — nhồi các trường này
    # vào CRF của chúng là dấu vết SAP/CRF dùng chung mọi thiết kế, dễ bị hội
    # đồng khoa học/đạo đức bắt lỗi ngay khi đọc.
    # SỬA 2026-07-22 (vòng lặp kiểm tra-hoàn thiện vòng 7): "prediction" thêm
    # vào needs_followup — mô hình tiên lượng dự báo kết cục TƯƠNG LAI (vd tử
    # vong 1 năm) luôn cần trục thời gian theo dõi, dù không có can thiệp/AE
    # (needs_ae_safety KHÔNG thêm — không có can thiệp đang thử nghiệm).
    needs_followup = design_code in ("rct", "cohort", "prediction")
    needs_ae_safety = design_code in ("rct", "cohort")
    followup_admin = _FOLLOWUP_ADMIN if needs_followup else []
    safety_ae = _BASE_SAFETY_AE if needs_ae_safety else []

    if design_code == "qualitative":
        return _QUALITATIVE_FIELDS, specialty
    elif design_code == "sr_ma":
        return _SRMA_FIELDS, specialty
    elif design_code == "rct":
        rows = (
            _BASE_ADMIN + followup_admin + _BASE_DEMOGRAPHICS + base_vitals + bundle["clinical"]
            + bundle["comorbid"] + bundle["labs_base"] + bundle["labs"] + bundle["meds"]
            + _RCT_EXTRA
            + bundle["exposure"]   # RCT cũng có exposure (nhóm can thiệp)
            + bundle["outcomes"]
            + safety_ae + _BASE_ADMIN_COMPLETE
        )
    elif design_code == "diagnostic":
        rows = (
            _BASE_ADMIN + followup_admin + _BASE_DEMOGRAPHICS + base_vitals + bundle["clinical"]
            + bundle["comorbid"] + bundle["labs_base"] + bundle["labs"]
            + _DIAGNOSTIC_EXTRA
            + safety_ae + _BASE_ADMIN_COMPLETE
        )
    elif design_code == "prediction":
        # THÊM 2026-07-22 (vòng lặp kiểm tra-hoàn thiện vòng 7, phát hiện
        # CRITICAL): trước đây rơi vào else (cohort/case_control/cross_
        # sectional) — CRF không có cờ tách tập phát triển/đánh giá TRIPOD+AI.
        rows = (
            _BASE_ADMIN + followup_admin + _BASE_DEMOGRAPHICS + base_vitals + bundle["clinical"]
            + bundle["comorbid"] + bundle["labs_base"] + bundle["labs"] + bundle["meds"]
            + bundle["outcomes"]
            + _PREDICTION_EXTRA
            + _BASE_ADMIN_COMPLETE
        )
    elif design_code == "economic":
        # THÊM 2026-07-24 (vòng lặp kiểm tra-hoàn thiện vòng 20): trước đây
        # rơi vào else — CRF không có trường CHEERS 2022 nào (góc nhìn,
        # chi phí, thỏa dụng/QALY, mô hình hóa). Bộ trường ĐỘC LẬP, không
        # nhồi khối lâm sàng cá thể (clinical/comorbid/labs) vì phân tích
        # kinh tế y tế thường tổng hợp ở mức QUẦN THỂ/kịch bản mô hình,
        # không phải hồ sơ từng bệnh nhân.
        # SỬA 2026-07-24 (vòng lặp vòng 21, phát hiện MEDIUM): nhánh này KHÔNG
        # tự chạy tới trong pipeline G0→G10 tự động — grep run_g1_auto.py xác
        # nhận infer_study_design() chỉ gán 1 trong 8 mã canonical (rct/cohort/
        # case_control/cross_sectional/diagnostic/sr_ma/prediction/qualitative);
        # "economic" CHỈ tồn tại như specialist_module CỘNG THÊM (xử lý riêng ở
        # main(), xem "existing_names"/_ECONOMIC_FIELDS phía dưới), không bao
        # giờ trở thành design_code chính qua suy luận tự động. Nhánh dưới đây
        # chỉ chạy nếu design_code="economic" được ép thủ công (vd chỉnh tay
        # study_meta.json — KHÔNG phải đường chính thức doctrine hỗ trợ) — giữ
        # lại để không mất dữ liệu nếu ai đó làm vậy, nhưng KHÔNG coi là một
        # thiết kế "song song, tương đương" sr_ma/qualitative như trước đây.
        return _ECONOMIC_FIELDS, specialty
    else:  # cohort, case_control, cross_sectional, mặc định
        rows = (
            _BASE_ADMIN + followup_admin + _BASE_DEMOGRAPHICS + base_vitals + bundle["clinical"]
            + bundle["comorbid"] + bundle["labs_base"] + bundle["labs"] + bundle["meds"]
            + bundle["exposure"]
            + bundle["outcomes"]
            + safety_ae + _BASE_ADMIN_COMPLETE
        )
    return rows, specialty


# Validation rules tương ứng với CRF 55 dòng
VALIDATION_RULES = [
    ("record_id",       "text",    "Chuỗi",         "Duy nhất trong DB, không PII",              "Báo lỗi trùng ID — hệ thống REDCap tự phát hiện"),
    ("consent_date",    "date",    "2020-01-01→hôm nay","Ngày hợp lệ, không tương lai",         "Báo lỗi ngày"),
    ("age",             "integer", "18–120",         "Người lớn hợp lệ",                          "Báo lỗi tuổi"),
    ("bmi",             "number",  "10–60",          "Phạm vi sinh lý",                           "Cảnh báo ngoài phạm vi"),
    ("lvef",            "number",  "20–85",          "EF sinh lý, THẤP VÀO HFpEF nếu ≥50",       "Gắn cờ nếu <50 (không phải HFpEF)"),
    ("bp_sys",          "number",  "60–250",         "Huyết áp tâm thu",                          "Cảnh báo ngoài phạm vi"),
    ("bp_dia",          "number",  "30–150",         "Huyết áp tâm trương",                       "Cảnh báo ngoài phạm vi"),
    ("heart_rate",      "integer", "30–250",         "Nhịp tim",                                  "Cảnh báo nhịp cực đoan"),
    ("egfr",            "number",  "0–200",          "eGFR sinh lý",                              "Cảnh báo eGFR<20 (CKD nặng, LOẠI TRỪ nếu theo protocol)"),
    ("nt_probnp",       "number",  "0–100000",       "NT-proBNP pg/mL",                           "Cảnh báo >35000 (cần xem lại)"),
    ("hba1c",           "number",  "4–15",           "HbA1c — chỉ khi có ĐTĐ",                   "Phân nhánh: bỏ qua nếu dm=0"),
    ("hgb",             "number",  "3–20",           "Hemoglobin g/dL",                           "Cảnh báo thiếu máu nặng (hgb<7)"),
    ("creatinine",      "number",  "20–2000",        "Creatinine µmol/L",                         "Cảnh báo nếu >884 (eGFR có thể <15)"),
    ("k_serum",         "number",  "1.5–8",          "Kali mmol/L",                               "Cờ ĐỎ nếu <2.5 hoặc >6 (nguy cơ tim mạch)"),
    ("sglt2i_start_date","date",   "≥consent_date",  "Không trước ngày đồng thuận",               "Lỗi logic ngày"),
    ("hf_hosp_date",    "date",    "≥consent_date",  "Ngày nhập viện không trước tuyển",          "Lỗi logic ngày"),
    ("death_date",      "date",    "≥consent_date",  "Ngày tử vong không trước tuyển",            "Lỗi logic ngày; cần ≥hf_hosp_date nếu có"),
    ("follow_time_months","number","0–120",           "Thời gian theo dõi (tháng)",                "Kiểm nhất quán vs censor_date"),
    ("qol_score_baseline","number","0–100",          "Điểm QoL nền [CẦN CHỈ ĐỊNH THANG ĐO]",     "Kiểm phạm vi theo thang cụ thể"),
    ("ef_change_6m",    "number",  "-50–50",         "Thay đổi EF từ nền đến 6 tháng",           "Cảnh báo thay đổi >30 (kiểm lại)"),
    # THÊM 2026-07-02 — range-check cho biến lab/sinh hiệu quan trọng của
    # 6 bundle chuyên khoa mới (nephrology_ckd, pulmonology_copd_asthma,
    # neurology_stroke, musculoskeletal_pain, psychiatry_depression_anxiety).
    ("acr",              "number",  "0–20000",       "Albumin/Creatinine niệu (ACR) mg/g",       "Cảnh báo >300 (albumin niệu nặng, macroalbumin)"),
    ("fev1_pct",         "number",  "10–150",        "FEV1 % dự đoán",                            "Cảnh báo <30 (COPD rất nặng — GOLD 4)"),
    ("fev1_fvc_ratio",   "number",  "20–100",        "Tỷ số FEV1/FVC (%)",                       "Cảnh báo <70 gợi ý tắc nghẽn"),
    ("cat_score",        "integer", "0–40",          "Điểm CAT (COPD Assessment Test)",          "Cảnh báo ≥20 (ảnh hưởng nặng)"),
    ("exacerbation_freq_prior","integer","0–50",     "Số đợt cấp COPD/hen trong 12 tháng trước", "Cảnh báo ≥2 (nguy cơ cao — nhóm E theo GOLD)"),
    ("nihss_baseline",   "integer", "0–42",          "Điểm NIHSS lúc nhập viện",                  "Cảnh báo ≥21 (đột quỵ rất nặng)"),
    ("pain_nrs_baseline","integer", "0–10",          "Điểm đau NRS nền",                          "Cảnh báo =10 (đau tối đa, cần xử trí ngay)"),
    ("pain_duration_months","integer","3–600",       "Thời gian đau mạn (tháng)",                 "Kiểm giá trị <3 (không đạt định nghĩa đau mạn)"),
    ("opioid_mme_per_day","number","0–2000",         "Liều opioid quy đổi MME/ngày",             "Cờ ĐỎ nếu ≥90 MME/ngày (ngưỡng nguy cơ cao CDC)"),
    ("pain_nrs_change",  "number",  "-10–10",        "Thay đổi điểm đau NRS so với nền",         "Kiểm nhất quán chiều thay đổi vs đáp ứng lâm sàng"),
    ("phq9_baseline",    "integer", "0–27",          "Điểm PHQ-9 nền",                            "Cờ ĐỎ nếu mục 9 (ý tưởng tự sát) >0 — xử trí an toàn ngay"),
    ("gad7_baseline",    "integer", "0–21",          "Điểm GAD-7 nền",                            "Cảnh báo ≥15 (lo âu nặng)"),
    ("phq9_followup",    "integer", "0–27",          "Điểm PHQ-9 tại mốc theo dõi",               "So sánh với phq9_baseline để tính đáp ứng/thuyên giảm"),
]


# ---------------------------------------------------------------------------
# AUTO-GENERATED PYTHON SCRIPTS
# ---------------------------------------------------------------------------

def gen_data_cleaning_script(study: str, design_code: str, rows: list) -> str:
    """Sinh data_cleaning.py đọc REDCap export và làm sạch theo CRF dictionary."""
    col_names    = [r[0] for r in rows]
    numeric_cols = [r[0] for r in rows if r[7] in ("number", "integer")]
    date_cols    = [r[0] for r in rows if r[7] == "date_ymd"]
    required_cols = [r[0] for r in rows if r[10] == "y"]

    # Build range checks từ VALIDATION_RULES
    range_lines = []
    for vr in VALIDATION_RULES:
        var, vtype, rng, rule, action = vr
        if "–" in rng and var in col_names:
            parts = rng.split("–")
            try:
                lo = float(parts[0].replace(",", ".").strip())
                hi = float(parts[1].replace(",", ".").strip())
                range_lines.append(f"    ('{var}', {lo}, {hi}),")
            except ValueError:
                pass
    range_checks_str = "\n".join(range_lines) if range_lines else "    # (Thêm range check cho thiết kế này)"

    # SỬA: date_pairs trước đây hardcode cứng 3 cặp riêng của bundle
    # cardiology_hf (sglt2i_start_date/hf_hosp_date/death_date) — với đề tài
    # KHÔNG phải cardiology_hf (metabolic_diabetes, generic), 3 cột này
    # không tồn tại trong CRF thật, mọi cặp âm thầm bị bỏ qua
    # ("if d1 in df.columns" false) → check_logic() thành no-op HOÀN TOÀN dù
    # docstring tự nhận "sinh tự động từ CRF dictionary". Sửa: build cặp
    # ĐỘNG từ chính date_cols thật của CRF — quy tắc chung "consent_date
    # phải ≤ mọi ngày khác" áp dụng được cho MỌI chuyên khoa/thiết kế.
    date_pairs_lines = []
    if "consent_date" in date_cols:
        for dcol in date_cols:
            if dcol != "consent_date":
                date_pairs_lines.append(f'        ("consent_date", "{dcol}"),')
    date_pairs_str = "\n".join(date_pairs_lines) if date_pairs_lines else "        # (Không có cặp ngày nào để kiểm — CRF thiếu consent_date hoặc chỉ có 1 cột ngày)"

    # Dùng plain string + replace thay vì f-string để tránh conflict brace
    template = (
        '#!/usr/bin/env python3\n'
        '# -*- coding: utf-8 -*-\n'
        '"""\n'
        'data_cleaning.py — Lam sach du lieu REDCap cho de tai: __STUDY__\n'
        'NANG CAP G5: sinh tu dong tu CRF dictionary (__NVAR__ bien)\n'
        'Thiet ke: __DESIGN__\n\n'
        'CANH BAO: Script nay chi xu ly file CSV cuc bo. KHONG gui du lieu ra ngoai.\n'
        'Du lieu that chi xu ly tai moi truong bao mat (REDCap co so hoac server noi bo).\n\n'
        'Cach dung:\n'
        '    python data_cleaning.py --input data/raw/redcap_export.csv\n'
        '"""\n'
        'import argparse\n'
        'import pandas as pd\n'
        'from pathlib import Path\n'
        'from datetime import datetime\n\n'
        '# Danh sach bien theo CRF dictionary (sinh tu dong)\n'
        'EXPECTED_COLUMNS = __COLS__\n\n'
        '# Bien so can ep kieu numeric\n'
        'NUMERIC_COLS = __NUMERIC__\n\n'
        '# Bien ngay thang\n'
        'DATE_COLS = __DATES__\n\n'
        '# Bien bat buoc (required)\n'
        'REQUIRED_COLS = __REQUIRED__\n\n'
        '# Kiem tra pham vi (var, min, max) — sinh tu dong tu VALIDATION_RULES\n'
        'RANGE_CHECKS = [\n'
        '__RANGES__\n'
        ']\n\n\n'
        'def load_data(csv_path: str) -> pd.DataFrame:\n'
        '    """Doc REDCap export CSV."""\n'
        '    df = pd.read_csv(csv_path, dtype=str, encoding="utf-8-sig")\n'
        '    print(f"[LOAD] {len(df)} dong, {len(df.columns)} cot")\n'
        '    return df\n\n\n'
        'def check_columns(df: pd.DataFrame) -> None:\n'
        '    """Kiem tra cot thieu / thua so voi CRF dictionary."""\n'
        '    missing = [c for c in EXPECTED_COLUMNS if c not in df.columns]\n'
        '    extra   = [c for c in df.columns if c not in EXPECTED_COLUMNS]\n'
        '    if missing:\n'
        '        print(f"[WARN] Cot THIEU so CRF: {missing}")\n'
        '    if extra:\n'
        '        print(f"[INFO] Cot THEM khong trong CRF: {extra}")\n\n\n'
        'def coerce_types(df: pd.DataFrame) -> pd.DataFrame:\n'
        '    """Ep kieu numeric va date."""\n'
        '    for col in NUMERIC_COLS:\n'
        '        if col in df.columns:\n'
        '            df[col] = pd.to_numeric(df[col], errors="coerce")\n'
        '    for col in DATE_COLS:\n'
        '        if col in df.columns:\n'
        '            df[col] = pd.to_datetime(df[col], errors="coerce", format="%Y-%m-%d")\n'
        '    return df\n\n\n'
        'def check_missing(df: pd.DataFrame) -> pd.Series:\n'
        '    """Tinh % thieu moi bien; in canh bao neu bien bat buoc thieu > 0."""\n'
        '    missing_pct = (df.isnull().sum() / len(df) * 100).round(1)\n'
        '    for varname in REQUIRED_COLS:\n'
        '        if varname in df.columns and missing_pct.get(varname, 0) > 0:\n'
        '            pct_val = missing_pct[varname]\n'
        '            print(f"[WARN] Bien bat buoc \'{varname}\' thieu {pct_val:.1f}%")\n'
        '    return missing_pct\n\n\n'
        'def range_validation(df: pd.DataFrame) -> pd.DataFrame:\n'
        '    """Gan co cac gia tri ngoai pham vi sinh ly."""\n'
        '    for varname, lo, hi in RANGE_CHECKS:\n'
        '        if varname in df.columns:\n'
        '            flag_col = "flag_" + varname\n'
        '            col_num = pd.to_numeric(df[varname], errors="coerce")\n'
        '            df[flag_col] = col_num.notna() & ((col_num < lo) | (col_num > hi))\n'
        '            n_flag = int(df[flag_col].sum())\n'
        '            if n_flag > 0:\n'
        '                print(f"[RANGE] {varname}: {n_flag} gia tri ngoai [{lo}, {hi}]")\n'
        '    return df\n\n\n'
        'def check_logic(df: pd.DataFrame) -> None:\n'
        '    """Kiem tra logic ngay (consent <= event <= censor)."""\n'
        '    date_pairs = [\n'
        '__DATEPAIRS__\n'
        '    ]\n'
        '    for d1, d2 in date_pairs:\n'
        '        if d1 in df.columns and d2 in df.columns:\n'
        '            bad = df[d2].notna() & df[d1].notna() & (df[d2] < df[d1])\n'
        '            if bad.sum() > 0:\n'
        '                print(f"[LOGIC] {d2} truoc {d1}: {bad.sum()} dong")\n\n\n'
        'def check_duplicates(df: pd.DataFrame) -> None:\n'
        '    """Phat hien record_id trung."""\n'
        '    if "record_id" in df.columns:\n'
        '        dups = df["record_id"].duplicated(keep=False)\n'
        '        if dups.sum() > 0:\n'
        '            dup_ids = df.loc[dups, "record_id"].unique()\n'
        '            print(f"[ERROR] record_id TRUNG: {dup_ids}")\n\n\n'
        'def save_clean(df: pd.DataFrame, out_dir: Path) -> None:\n'
        '    """Luu dataset da lam sach."""\n'
        '    out_dir.mkdir(parents=True, exist_ok=True)\n'
        '    out_path = out_dir / "df_clean.csv"\n'
        '    flag_cols = [c for c in df.columns if c.startswith("flag_")]\n'
        '    df_clean = df.drop(columns=flag_cols, errors="ignore")\n'
        '    df_clean.to_csv(out_path, index=False, encoding="utf-8-sig")\n'
        '    print(f"[SAVE] Dataset lam sach -> {out_path} ({len(df_clean)} dong)")\n'
        '    if flag_cols:\n'
        '        flag_path = out_dir / "df_flags.csv"\n'
        '        df[["record_id"] + flag_cols].to_csv(flag_path, index=False, encoding="utf-8-sig")\n'
        '        print(f"[SAVE] Co kiem tra -> {flag_path}")\n\n\n'
        'def main():\n'
        '    parser = argparse.ArgumentParser(description="Lam sach du lieu REDCap — __STUDY__")\n'
        '    parser.add_argument("--input", required=True, help="Duong dan REDCap export CSV")\n'
        '    parser.add_argument("--out-dir", default="data/processed",\n'
        '                        help="Thu muc luu dataset lam sach (mac dinh: data/processed/)")\n'
        '    args = parser.parse_args()\n\n'
        '    print("=== data_cleaning.py — __STUDY__ ===")\n'
        '    print(f"Thiet ke: __DESIGN__ | Thoi gian: {datetime.now().strftime(\'%Y-%m-%d %H:%M\')}")\n'
        '    print("NHAC NHO: Chay tren moi truong bao mat noi bo, KHONG upload du lieu that len cloud.")\n'
        '    print()\n\n'
        '    df = load_data(args.input)\n'
        '    check_columns(df)\n'
        '    df = coerce_types(df)\n'
        '    check_duplicates(df)\n'
        '    check_missing(df)\n'
        '    df = range_validation(df)\n'
        '    check_logic(df)\n'
        '    save_clean(df, Path(args.out_dir))\n\n'
        '    print()\n'
        '    print("=== HOAN TAT lam sach — Kiem tra canh bao tren va xu ly truoc khi phan tich ===")\n'
        '    print("Can bac si kiem chung moi gia tri bat thuong duoc gan co.")\n\n\n'
        'if __name__ == "__main__":\n'
        '    main()\n'
    )

    script = (template
              .replace("__STUDY__", study)
              .replace("__DESIGN__", design_code)
              .replace("__NVAR__", str(len(col_names)))
              .replace("__COLS__", repr(col_names))
              .replace("__NUMERIC__", repr(numeric_cols))
              .replace("__DATES__", repr(date_cols))
              .replace("__REQUIRED__", repr(required_cols))
              .replace("__RANGES__", range_checks_str)
              .replace("__DATEPAIRS__", date_pairs_str))
    return script


def gen_data_quality_report_script(study: str, design_code: str, rows: list) -> str:
    """
    Sinh data_quality_report.py đọc cleaned data và báo cáo chất lượng.
    SỬA: trước đây RANGE_CHECKS hardcode cứng 15 biến của bundle
    cardiology_hf (lvef, nt_probnp, k_serum...) BẤT KỂ chuyên khoa/thiết kế
    thật — đề tài metabolic_diabetes/generic nhận script với range-check
    cho biến KHÔNG tồn tại trong dataset của họ (âm thầm bỏ qua, "if varname
    in df.columns" luôn false), trong khi biến THẬT của đề tài đó lại không
    được kiểm range gì cả. Nay build RANGE_CHECKS động từ CRF thật (rows),
    giống hệt cách gen_data_cleaning_script() đã làm.
    """
    col_names = [r[0] for r in rows]
    range_lines = []
    for vr in VALIDATION_RULES:
        var, vtype, rng, rule, action = vr
        if "–" in rng and var in col_names:
            parts = rng.split("–")
            try:
                lo = float(parts[0].replace(",", ".").strip())
                hi = float(parts[1].replace(",", ".").strip())
                range_lines.append(f'    ("{var}", {lo}, {hi}),')
            except ValueError:
                pass
    range_checks_str = "\n".join(range_lines) if range_lines else "    # (Chưa có range check cho thiết kế/chuyên khoa này)"

    template = (
        '#!/usr/bin/env python3\n'
        '# -*- coding: utf-8 -*-\n'
        '"""\n'
        'data_quality_report.py — Bao cao chat luong du lieu cho de tai: __STUDY__\n'
        'Doc df_clean.csv -> kiem tra N, % complete, vi pham pham vi, trung ID.\n'
        'Sinh: data_quality_report.txt\n\n'
        'CANH BAO: Chi chay tren moi truong bao mat noi bo voi du lieu that.\n\n'
        'Cach dung:\n'
        '    python data_quality_report.py --input data/processed/df_clean.csv\n'
        '"""\n'
        'import argparse\n'
        'import pandas as pd\n'
        'from pathlib import Path\n'
        'from datetime import datetime\n\n\n'
        'RANGE_CHECKS = [\n'
        '__RANGES__\n'
        ']\n\n\n'
        'def generate_report(df: pd.DataFrame, study_name: str, design: str, out_path: Path) -> None:\n'
        '    lines = []\n'
        '    now = datetime.now().strftime("%Y-%m-%d %H:%M")\n'
        '    lines += [\n'
        '        "=" * 60,\n'
        '        f"BAO CAO CHAT LUONG DU LIEU — {study_name}",\n'
        '        f"Ngay sinh bao cao: {now}",\n'
        '        f"Thiet ke: {design}",\n'
        '        "=" * 60,\n'
        '        "",\n'
        '        "TONG QUAN",\n'
        '        f"  N tong (dong): {len(df)}",\n'
        '        f"  So bien      : {len(df.columns)}",\n'
        '        "",\n'
        '    ]\n\n'
        '    if "record_id" in df.columns:\n'
        '        n_dup = int(df["record_id"].duplicated(keep=False).sum())\n'
        '        suffix = "  CANH BAO: CAN XU LY" if n_dup > 0 else "  OK"\n'
        '        lines.append(f"TRUNG record_id: {n_dup} dong{suffix}")\n'
        '    else:\n'
        '        lines.append("TRUNG record_id: khong tim thay cot record_id")\n\n'
        '    lines.append("")\n'
        '    lines.append("% DU LIEU DAY DU (Completeness) theo bien:")\n'
        '    lines.append("  " + "-" * 50)\n'
        '    missing = (df.isnull().sum() / len(df) * 100).round(1)\n'
        '    for varname, pct in missing.sort_values(ascending=True).items():\n'
        '        complete = 100 - pct\n'
        '        if pct > 30:\n'
        '            flag_str = "  THIEU NHIEU"\n'
        '        elif pct > 10:\n'
        '            flag_str = "  CHU Y"\n'
        '        else:\n'
        '            flag_str = ""\n'
        '        lines.append(f"  {varname:<30} {complete:5.1f}% day du{flag_str}")\n\n'
        '    lines.append("")\n'
        '    lines.append("VI PHAM PHAM VI SINH LY:")\n'
        '    n_violations = 0\n'
        '    for varname, lo, hi in RANGE_CHECKS:\n'
        '        if varname in df.columns:\n'
        '            col_num = pd.to_numeric(df[varname], errors="coerce")\n'
        '            n_bad = int(((col_num < lo) | (col_num > hi)).sum())\n'
        '            if n_bad > 0:\n'
        '                lines.append(f"  {varname:<30} {n_bad} gia tri ngoai [{lo}, {hi}]  CANH BAO")\n'
        '                n_violations += n_bad\n'
        '    if n_violations == 0:\n'
        '        lines.append("  Khong phat hien vi pham pham vi trong dataset nay.")\n\n'
        '    lines += ["", "=" * 60, "KET LUAN:"]\n'
        '    issues = []\n'
        '    if "record_id" in df.columns and df["record_id"].duplicated(keep=False).sum() > 0:\n'
        '        issues.append("Co record_id trung — can xu ly truoc khi phan tich")\n'
        '    high_missing = missing[missing > 30]\n'
        '    if not high_missing.empty:\n'
        '        issues.append(f"{len(high_missing)} bien thieu >30%: {list(high_missing.index)}")\n'
        '    if n_violations > 0:\n'
        '        issues.append(f"{n_violations} gia tri vi pham pham vi — can kiem tra lai nguon")\n'
        '    if issues:\n'
        '        for idx, issue in enumerate(issues, 1):\n'
        '            lines.append(f"  {idx}. {issue}")\n'
        '    else:\n'
        '        lines.append("  Khong phat hien van de chat luong nghiem trong.")\n\n'
        '    lines += [\n'
        '        "",\n'
        '        "Can bac si/nha nghien cuu kiem chung bao cao nay.",\n'
        '        "KHONG dung du lieu khi con van de chua giai quyet.",\n'
        '        "=" * 60,\n'
        '    ]\n'
        '    report_text = "\\n".join(lines)\n'
        '    out_path.write_text(report_text, encoding="utf-8")\n'
        '    print(report_text)\n'
        '    print(f"\\n-> Da luu bao cao: {out_path}")\n\n\n'
        'def main():\n'
        '    parser = argparse.ArgumentParser(description="Bao cao chat luong du lieu — __STUDY__")\n'
        '    parser.add_argument("--input", default="data/processed/df_clean.csv",\n'
        '                        help="Duong dan df_clean.csv")\n'
        '    parser.add_argument("--out", default="data/processed/data_quality_report.txt",\n'
        '                        help="Duong dan luu bao cao txt")\n'
        '    args = parser.parse_args()\n\n'
        '    df = pd.read_csv(args.input, encoding="utf-8-sig")\n'
        '    generate_report(df, "__STUDY__", "__DESIGN__", Path(args.out))\n\n\n'
        'if __name__ == "__main__":\n'
        '    main()\n'
    )
    script = (template
              .replace("__STUDY__", study)
              .replace("__DESIGN__", design_code)
              .replace("__RANGES__", range_checks_str))
    return script


# ---------------------------------------------------------------------------
# STROBE PARTICIPANT FLOWCHART (ASCII)
# ---------------------------------------------------------------------------

# 2026-07-07: nhãn phơi nhiễm + tiêu chí loại trừ minh họa cho sơ đồ STROBE —
# CHỈ có nội dung cụ thể cho cardiology_hf (bundle gốc); mọi chuyên khoa khác
# dùng placeholder [CẦN] rõ ràng, KHÔNG bịa nội dung lâm sàng của chuyên khoa
# khác (cùng triết lý với _GENERIC_EXPOSURE/_GENERIC_OUTCOMES ở trên — trước
# đây hàm này hardcode nội dung cardiology_hf cho MỌI chuyên khoa).
_STROBE_EXPOSURE_LABEL = {
    "cardiology_hf": "SGLT2i",
}
_STROBE_EXCLUSION_LINES = {
    "cardiology_hf": [
        "  │  • LVEF < 50% (không HFpEF) │",
        "  │  • eGFR < 20 mL/min/1.73m²  │",
        "  │  • SGLT2i CCĐ               │",
    ],
}
_STROBE_EXPOSURE_LABEL_RCT = {
    "cardiology_hf": "(SGLT2i)",
}


def build_strobe_flowchart(study: str, design_code: str, n_adjusted: int, n_total: int, n_per_group: int, specialty: str = "generic") -> str:
    """Sinh sơ đồ tham gia nghiên cứu dạng ASCII theo STROBE/CONSORT."""
    is_rct = design_code == "rct"
    exposure_label = _STROBE_EXPOSURE_LABEL.get(specialty, "[CẦN — tên biến phơi nhiễm/can thiệp theo PICO]")
    exposure_label_rct = _STROBE_EXPOSURE_LABEL_RCT.get(specialty, "([CẦN — tên can thiệp])")
    exclusion_lines = "\n".join(_STROBE_EXCLUSION_LINES.get(specialty, [
        "  │  • [CẦN — tiêu chí loại trừ theo PICO/SAP thật]  │",
    ]))

    if is_rct:
        group_a = n_per_group
        group_b = n_total - n_per_group
        flowchart = f"""\
┌─────────────────────────────────────────────────────────────────┐
│      BIỂU ĐỒ THAM GIA NGHIÊN CỨU (CONSORT 2025 flow diagram)  │
│                      Đề tài: {study:<30}     │
└─────────────────────────────────────────────────────────────────┘

  ┌──────────────────────────────────────────┐
  │  Đánh giá đủ tiêu chuẩn (Screened):     │
  │  N = [CẦN — BÁC SĨ ĐIỀN]               │
  └────────────────┬─────────────────────────┘
                   │
        ┌──────────▼──────────────────┐
        │  Loại trừ (Excluded):        │
        │  N = [CẦN]                   │
        │  • Không đủ TIÊU CHUẨN VÀO  │
        │    → [CẦN nêu lý do cụ thể] │
        │  • Từ chối tham gia: [CẦN]  │
        │  • Lý do khác: [CẦN]        │
        └─────────────────────────────┘
                   │
  ┌────────────────▼─────────────────────────┐
  │  NGẪU NHIÊN HÓA (Randomised):           │
  │  N = {n_adjusted} (sau điều chỉnh bỏ cuộc)  │
  └────────────────┬─────────────────────────┘
                   │
        ┌──────────┴──────────────────┐
        │                             │
        ▼                             ▼
  ┌───────────────┐           ┌───────────────┐
  │  CAN THIỆP    │           │  ĐỐI CHỨNG    │
  │  N = {group_a:<8}       │           │  N = {group_b:<8}       │
  │  {exposure_label_rct:<11}   │           │  (Placebo/SOC)│
  └───────┬───────┘           └───────┬───────┘
          │                           │
          ▼                           ▼
  ┌───────────────┐           ┌───────────────┐
  │ THEO DÕI      │           │ THEO DÕI      │
  │ Mất/ltfu:     │           │ Mất/ltfu:     │
  │ N = [CẦN]    │           │ N = [CẦN]    │
  └───────┬───────┘           └───────┬───────┘
          │                           │
          ▼                           ▼
  ┌───────────────┐           ┌───────────────┐
  │ PHÂN TÍCH     │           │ PHÂN TÍCH     │
  │ N = [CẦN]    │           │ N = [CẦN]    │
  │ (ITT/PP)      │           │ (ITT/PP)      │
  └───────────────┘           └───────────────┘

  Ghi chú: Điền N=[CẦN] SAU khi thu thập dữ liệu thật.
  Cần bác sĩ kiểm chứng. KHÔNG PII.
"""
    elif design_code == "diagnostic":
        # THÊM 2026-07-17 (đóng việc hoãn từ round 5): sơ đồ STARD flow that —
        # KHÔNG có khung "phơi nhiễm" như STROBE, mà là dòng index test/
        # reference standard theo đúng STARD 2015 mục 19 (participant flow).
        flowchart = f"""\
┌─────────────────────────────────────────────────────────────────┐
│           BIỂU ĐỒ DÒNG NGƯỜI THAM GIA (STARD Flow Diagram)    │
│                      Đề tài: {study:<30}     │
└─────────────────────────────────────────────────────────────────┘

  ┌──────────────────────────────────────────┐
  │  Đánh giá đủ điều kiện (Eligible):      │
  │  N = [CẦN — BÁC SĨ ĐIỀN]               │
  └────────────────┬─────────────────────────┘
                   │
        ┌──────────▼──────────────────┐
        │  Loại trừ (Excluded):        │
        │  N = [CẦN]                   │
{exclusion_lines}
        │  • Không đồng thuận          │
        └─────────────────────────────┘
                   │
  ┌────────────────▼─────────────────────────┐
  │  TUYỂN VÀO (Enrolled):                   │
  │  N = {n_adjusted} (N dự kiến + 20% dự phòng)│
  └────────────────┬─────────────────────────┘
                   │
        ┌──────────▼──────────────────┐
        │  Nhận INDEX TEST:            │
        │  N = [CẦN]                   │
        │  Không nhận: N = [CẦN — lý do]│
        └──────────┬──────────────────┘
                   │
        ┌──────────▼──────────────────┐
        │  Nhận REFERENCE STANDARD:    │
        │  N = [CẦN]                   │
        │  Không nhận: N = [CẦN — lý do]│
        └──────────┬──────────────────┘
                   │
        ┌──────────┴──────────────────┐
        │                             │
        ▼                             ▼
  ┌───────────────┐           ┌───────────────┐
  │  INDEX TEST   │           │  INDEX TEST   │
  │  DƯƠNG TÍNH   │           │  ÂM TÍNH      │
  │  N ≈ {n_per_group:<8}     │           │  N ≈ {n_total - n_per_group:<8}     │
  └───────┬───────┘           └───────┬───────┘
          │                           │
          ▼                           ▼
  ┌──────────────────────────────────────────┐
  │  PHÂN TÍCH (cross-tabulation với          │
  │  reference standard — Se/Sp/PPV/NPV):    │
  │  N = {n_adjusted} → [CẦN điều chỉnh thực tế]│
  └──────────────────────────────────────────┘

  Ghi chú: Điền N=[CẦN] SAU khi thu thập dữ liệu thật.
  Tham chiếu: STARD 2015 mục 19 (PMID: 26511519). Cần bác sĩ kiểm chứng.
"""
    elif design_code == "sr_ma":
        # THÊM 2026-07-17 (đóng việc hoãn từ round 5): sơ đồ PRISMA 2020 flow
        # that (mục 16a) — sàng lọc NGHIÊN CỨU, không phải tuyển BỆNH NHÂN,
        # nên khung hoàn toàn khác STROBE (identification/screening/included).
        flowchart = f"""\
┌─────────────────────────────────────────────────────────────────┐
│              BIỂU ĐỒ SÀNG LỌC (PRISMA 2020 Flow Diagram)       │
│                      Đề tài: {study:<30}     │
└─────────────────────────────────────────────────────────────────┘

  ── IDENTIFICATION ──────────────────────────────────────────────
  ┌──────────────────────────────────────────┐
  │  Bản ghi từ CSDL/registry:               │
  │  N = [CẦN — tổng theo từng CSDL đã tìm] │
  └────────────────┬─────────────────────────┘
                   │
        ┌──────────▼──────────────────┐
        │  Loại trước sàng lọc:        │
        │  • Trùng lặp: N = [CẦN]     │
        │  • Tự động loại: N = [CẦN]  │
        └─────────────────────────────┘
                   │
  ── SCREENING ────────────────────────────────────────────────────
  ┌────────────────▼─────────────────────────┐
  │  Bản ghi được sàng lọc (title/abstract): │
  │  N = {n_adjusted:<8}                        │
  └────────────────┬─────────────────────────┘
                   │
        ┌──────────▼──────────────────┐
        │  Loại (title/abstract):      │
        │  N = [CẦN — lý do]          │
        └─────────────────────────────┘
                   │
  ┌────────────────▼─────────────────────────┐
  │  Toàn văn tìm để đánh giá đủ điều kiện:  │
  │  N = [CẦN] | Không lấy được: N = [CẦN]  │
  └────────────────┬─────────────────────────┘
                   │
        ┌──────────▼──────────────────┐
        │  Loại (toàn văn, kèm lý do): │
        │  N = {n_per_group:<8}            │
{exclusion_lines}
        └─────────────────────────────┘
                   │
  ── INCLUDED ─────────────────────────────────────────────────────
  ┌────────────────▼─────────────────────────┐
  │  Nghiên cứu đưa vào tổng quan:           │
  │  N = {n_total - n_per_group:<8}                        │
  │  → Đưa vào tổng hợp định lượng (MA):     │
  │  N = [CẦN — sau đánh giá đồng nhất]     │
  └──────────────────────────────────────────┘

  Ghi chú: Điền N=[CẦN] SAU khi hoàn tất tìm kiếm/sàng lọc thật.
  Tham chiếu: PRISMA 2020 mục 16a (Page MJ et al., BMJ 2021;372:n71).
  Cần bác sĩ/nhóm sàng lọc kiểm chứng.
"""
    elif design_code == "prediction":
        # THÊM 2026-07-17 (đóng việc hoãn từ round 5): sơ đồ TRIPOD+AI flow
        # that (mục 20a) — tách rõ tập PHÁT TRIỂN (development) và ĐÁNH GIÁ
        # (evaluation), không có khung "phơi nhiễm" như STROBE.
        flowchart = f"""\
┌─────────────────────────────────────────────────────────────────┐
│      BIỂU ĐỒ DÒNG NGƯỜI THAM GIA (TRIPOD+AI Flow Diagram)     │
│                      Đề tài: {study:<30}     │
└─────────────────────────────────────────────────────────────────┘

  ┌──────────────────────────────────────────┐
  │  Đánh giá đủ điều kiện (Eligible):      │
  │  N = [CẦN — BÁC SĨ ĐIỀN]               │
  └────────────────┬─────────────────────────┘
                   │
        ┌──────────▼──────────────────┐
        │  Loại trừ (Excluded):        │
        │  N = [CẦN]                   │
{exclusion_lines}
        │  • Thiếu biến tiên đoán/kết cục N = [CẦN] │
        └─────────────────────────────┘
                   │
  ┌────────────────▼─────────────────────────┐
  │  TUYỂN VÀO (Enrolled):                   │
  │  N = {n_adjusted} (N dự kiến + 20% dự phòng)│
  └────────────────┬─────────────────────────┘
                   │
        ┌──────────┴──────────────────┐
        │                             │
        ▼                             ▼
  ┌───────────────┐           ┌───────────────┐
  │  TẬP PHÁT     │           │  TẬP ĐÁNH GIÁ │
  │  TRIỂN (D)    │           │  (E — nội/    │
  │               │           │  ngoại bộ)    │
  │  N ≈ {n_per_group:<8}     │           │  N ≈ {n_total - n_per_group:<8}     │
  └───────┬───────┘           └───────┬───────┘
          │                           │
          ▼                           ▼
  ┌───────────────┐           ┌───────────────┐
  │ Dữ liệu thiếu │           │ Dữ liệu thiếu │
  │ N = [CẦN]    │           │ N = [CẦN]    │
  └───────┬───────┘           └───────┬───────┘
          │                           │
          ▼                           ▼
  ┌───────────────┐           ┌───────────────┐
  │ MÔ HÌNH CUỐI  │           │ ĐÁNH GIÁ HIỆU │
  │ N = [CẦN]    │           │ NĂNG N=[CẦN] │
  │ (development) │           │ (discrimination/calibration)│
  └───────────────┘           └───────────────┘

  Ghi chú: Điền N=[CẦN] SAU khi thu thập dữ liệu thật.
  Tham chiếu: TRIPOD+AI mục 20a (Collins GS et al., BMJ 2024;385:e078378).
  Cần bác sĩ/thống kê viên kiểm chứng.
"""
    elif design_code == "qualitative":
        # THÊM 2026-07-21 (vòng lặp kiểm tra-hoàn thiện vòng 2, phát hiện CRITICAL:
        # G5 hoàn toàn thiếu nhánh định tính, rơi vào else STROBE có khung "phơi
        # nhiễm" vô nghĩa): sơ đồ LẤY MẪU CÓ CHỦ ĐÍCH + BÃO HÒA DỮ LIỆU theo
        # COREQ/SRQR — không so sánh 2 nhóm phơi nhiễm/không phơi nhiễm.
        flowchart = f"""\
┌─────────────────────────────────────────────────────────────────┐
│   SƠ ĐỒ LẤY MẪU CÓ CHỦ ĐÍCH & BÃO HÒA DỮ LIỆU (COREQ/SRQR)   │
│                      Đề tài: {study:<30}     │
└─────────────────────────────────────────────────────────────────┘

  ┌──────────────────────────────────────────┐
  │  Mời tham gia (Approached):              │
  │  N = [CẦN — BÁC SĨ/NHÓM NGHIÊN CỨU ĐIỀN]│
  └────────────────┬─────────────────────────┘
                   │
        ┌──────────▼──────────────────┐
        │  Từ chối/không đủ điều kiện: │
        │  N = [CẦN]                   │
{exclusion_lines}
        │  • Từ chối tham gia: N=[CẦN]│
        └─────────────────────────────┘
                   │
  ┌────────────────▼─────────────────────────┐
  │  ĐỒNG THUẬN THAM GIA:                    │
  │  N ≈ {n_adjusted} (ước tính ban đầu — cỡ mẫu ĐỊNH TÍNH│
  │  không tính bằng power, xem G3)          │
  └────────────────┬─────────────────────────┘
                   │
        ┌──────────▼──────────────────┐
        │  THU THẬP DỮ LIỆU theo lượt: │
        │  Phỏng vấn sâu/nhóm tiêu điểm│
        │  (mã hóa song song, ≥2 người)│
        └──────────┬──────────────────┘
                   │
        ┌──────────▼──────────────────┐
        │  KIỂM TRA BÃO HÒA sau mỗi   │
        │  lượt: đủ [CẦN — tiêu chí,  │
        │  vd 3 lượt liên tiếp không  │
        │  có mã/chủ đề mới] → DỪNG   │
        └──────────┬──────────────────┘
                   │
  ┌────────────────▼─────────────────────────┐
  │  TỔNG SỐ NGƯỜI THAM GIA (khi bão hòa):  │
  │  N = [CẦN — SAU KHI ĐẠT BÃO HÒA THẬT]  │
  │  → Phân tích chủ đề/khung (thematic/    │
  │    framework analysis)                   │
  └──────────────────────────────────────────┘

  Ghi chú: KHÔNG áp cỡ mẫu định lượng cho thiết kế này — N cuối cùng do
  BÃO HÒA DỮ LIỆU quyết định, không phải công thức power (xem G3).
  Tham chiếu: COREQ (Tong A et al., Int J Qual Health Care 2007;19:349-357)
  hoặc SRQR (O'Brien BC et al., Acad Med 2014;89:1245-1251).
  Cần bác sĩ/nhóm nghiên cứu kiểm chứng. KHÔNG PII.
"""
    else:
        # Khối giữa (sau 2 nhánh phơi nhiễm, trước PHÂN TÍCH) phải khớp trục
        # thời gian THẬT của thiết kế: chỉ cohort mới có giai đoạn theo dõi dọc
        # → mới có "Mất theo dõi/LTFU". case_control tra phơi nhiễm HỒI CỨU;
        # cross_sectional đo đồng thời 1 thời điểm — cả hai KHÔNG có LTFU.
        # (Cùng lớp lỗi "biến/khối mượn từ thiết kế khác" đã vá cho CRF 2026-07-17.)
        # LƯU Ý 2026-07-24 (vòng lặp vòng 21): design_code="economic" cũng rơi
        # vào nhánh else này nếu bị ép thủ công (không xảy ra qua pipeline tự
        # động — xem ghi chú ở build_redcap_rows()) — sơ đồ "CÓ/KHÔNG PHƠI
        # NHIỄM" bên dưới KHÔNG phù hợp CHEERS 2022 (đánh giá kinh tế y tế
        # không có khái niệm dòng người tham gia phơi nhiễm/không phơi nhiễm).
        # Chưa xây nhánh riêng vì đường này chưa có lối vào chính thức.
        if design_code == "cohort":
            followup_block = """\
          │                           │
          ▼                           ▼
  ┌──────────────────────────────────────────┐
  │  THEO DÕI (Follow-up):                  │
  │  Mất theo dõi / LTFU: N = [CẦN]        │
  │  Lý do: [CẦN — rút ĐT/tử vong/ltfu]   │
  └────────────────┬─────────────────────────┘
                   │"""
        elif design_code == "case_control":
            followup_block = """\
          │                           │
          ▼                           ▼
  ┌──────────────────────────────────────────┐
  │  TRA PHƠI NHIỄM HỒI CỨU (case-control): │
  │  Tra được (hồ sơ/phỏng vấn): N = [CẦN] │
  │  Không tra được phơi nhiễm: N = [CẦN]  │
  └────────────────┬─────────────────────────┘
                   │"""
        else:  # cross_sectional (và fallback khác) — 1 thời điểm, không theo dõi
            followup_block = """\
          │                           │
          ▼                           ▼
  ┌──────────────────────────────────────────┐
  │  ĐO ĐỒNG THỜI (cross-sectional):        │
  │  Phơi nhiễm + kết cục đo cùng 1 thời điểm│
  │  Không có giai đoạn theo dõi dọc.       │
  └────────────────┬─────────────────────────┘
                   │"""
        flowchart = f"""\
┌─────────────────────────────────────────────────────────────────┐
│        BIỂU ĐỒ THAM GIA NGHIÊN CỨU (STROBE Flowchart)         │
│                      Đề tài: {study:<30}     │
└─────────────────────────────────────────────────────────────────┘

  ┌──────────────────────────────────────────┐
  │  Đánh giá đủ tiêu chuẩn (Assessed):     │
  │  N = [CẦN — BÁC SĨ ĐIỀN từ sổ bệnh]   │
  └────────────────┬─────────────────────────┘
                   │
        ┌──────────▼──────────────────┐
        │  Loại trừ (Excluded):        │
        │  N = [CẦN]                   │
{exclusion_lines}
        │  • Không đồng thuận          │
        │  • [CẦN thêm lý do cụ thể]  │
        └─────────────────────────────┘
                   │
  ┌────────────────▼─────────────────────────┐
  │  TUYỂN VÀO (Enrolled):                   │
  │  N = {n_adjusted} (N dự kiến + 20% dự phòng)│
  └────────────────┬─────────────────────────┘
                   │
        ┌──────────┴──────────────────┐
        │                             │
        ▼                             ▼
  ┌───────────────┐           ┌───────────────┐
  │  CÓ PHƠI      │           │  KHÔNG PHƠI   │
  │  NHIỄM {exposure_label:<8}│          │  NHIỄM        │
  │  N ≈ {n_per_group:<8}     │           │  N ≈ {n_total - n_per_group:<8}     │
  └───────┬───────┘           └───────┬───────┘
{followup_block}
  ┌────────────────▼─────────────────────────┐
  │  PHÂN TÍCH (Analysed):                   │
  │  N = {n_adjusted} → [CẦN điều chỉnh thực tế]│
  │  Phân tích chính: {n_total} (sau loại trừ)  │
  └──────────────────────────────────────────┘

  Ghi chú: Điền N=[CẦN] SAU khi thu thập dữ liệu thật.
  Tham chiếu: STROBE 2007 (PMID: 18064739). Cần bác sĩ kiểm chứng.
"""
    return flowchart


# ---------------------------------------------------------------------------
# GUARDRAIL R1–R7
# ---------------------------------------------------------------------------

def guardrail(artifact: str) -> tuple[list, list]:
    """Kiểm tra liêm chính R1–R7."""
    errors, warnings = [], []

    # R1 — Nguồn
    if "PMID" in artifact or "DOI" in artifact or "STROBE" in artifact:
        warnings.append("R1 ✅ Có tham chiếu nguồn")
    else:
        errors.append("R1 🔴 Thiếu tham chiếu nguồn")

    # R2 — Không PII
    # SỬA: regex SĐT chỉ bắt đầu số 08/09 — bỏ sót 03 (Viettel), 05
    # (Vietnamobile), 07 (Mobifone) sau đợt chuyển đổi đầu số 2018.
    pii = re.search(r'(?:CMND|CCCD|CMT)\s*\d{9,12}|0[35789]\d{8}\b', artifact, re.I)
    if pii:
        errors.append("R2 🔴 Phát hiện mẫu PII")
    else:
        warnings.append("R2 ✅ KHÔNG PII trong cấu trúc (chỉ template)")

    # R3 — Không vượt cổng A/B/G
    if "Cổng A" in artifact or "Cổng B" in artifact:
        errors.append("R3 🔴 Vượt cổng A/B không đúng chỗ")
    else:
        warnings.append("R3 ✅ Không vượt cổng A/B/G")

    # R4 — Nhãn DRAFT
    n_draft = artifact.count("DRAFT")
    if n_draft >= 1:
        warnings.append(f"R4 ✅ Nhãn DRAFT đủ ({n_draft} lần)")
    else:
        errors.append("R4 🔴 Thiếu nhãn DRAFT")

    # R5 — Nhãn [CẦN...]
    can_n = len(re.findall(r'\[CẦN', artifact))
    if can_n >= 5:
        warnings.append(f"R5 ✅ {can_n} trường [CẦN...] đã gắn nhãn")
    else:
        errors.append(f"R5 🔴 Quá ít [CẦN...] ({can_n}) — cần ≥5")

    # R6 — Không tự gán mức GRADE/khuyến cáo
    # SỬA: regex cũ chỉ bắt cụm tiếng Anh — toàn bộ artifact G5 sinh bằng
    # tiếng Việt nên "Khuyến cáo MẠNH"/"Mức độ khuyến cáo: A" không bị bắt.
    grade_claim = re.search(
        r'\bGRADE [A-D]\b|\b(Strong|Weak|Conditional) recommendation\b|'
        r'(mức độ )?khuyến cáo\s*[:：]?\s*[A-D]\b|khuyến cáo (mạnh|yếu|có điều kiện)',
        artifact, re.I)
    if grade_claim:
        errors.append("R6 🔴 Tự gán mức GRADE/khuyến cáo — không được phép ở G5")
    else:
        warnings.append("R6 ✅ Không tự gán GRADE/khuyến cáo")

    # R7 — Disclaimer
    if "Cần bác sĩ kiểm chứng" in artifact:
        warnings.append("R7 ✅ Có disclaimer")
    else:
        errors.append("R7 🔴 Thiếu disclaimer 'Cần bác sĩ kiểm chứng'")

    return errors, warnings


# ---------------------------------------------------------------------------
# GENERATE CSV
# ---------------------------------------------------------------------------

def generate_csv(study: str, out_dir: Path, rows: list) -> tuple[Path, int]:
    """Sinh CSV data dictionary có thể import vào REDCap.

    Bản cũ chỉ nối trường bằng ``" / "`` nhưng vẫn đặt đuôi ``.csv``; REDCap và
    ``csv.DictReader`` đều đọc toàn bộ dòng thành một cột. Dùng đúng 18 cột data
    dictionary chuẩn, đồng thời giữ mapping tuple nội bộ hiện có.
    """
    headers = [
        "Variable / Field Name",
        "Form Name",
        "Section Header",
        "Field Type",
        "Field Label",
        "Choices, Calculations, OR Slider Labels",
        "Field Note",
        "Text Validation Type OR Show Slider Number",
        "Text Validation Min",
        "Text Validation Max",
        "Identifier?",
        "Branching Logic (Show field only if...)",
        "Required Field?",
        "Custom Alignment",
        "Question Number (surveys only)",
        "Matrix Group Name",
        "Matrix Ranking?",
        "Field Annotation",
    ]
    csv_path = out_dir / f"G5_REDCap_dictionary_{study}.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "Variable / Field Name": row[0],
                    "Form Name": row[1],
                    "Section Header": row[2],
                    "Field Type": row[3],
                    "Field Label": row[4],
                    "Choices, Calculations, OR Slider Labels": row[5],
                    "Field Note": row[6],
                    "Text Validation Type OR Show Slider Number": row[7],
                    "Text Validation Min": row[8],
                    "Text Validation Max": row[9],
                    "Identifier?": "",
                    "Branching Logic (Show field only if...)": row[11],
                    "Required Field?": row[10],
                    "Custom Alignment": "",
                    "Question Number (surveys only)": "",
                    "Matrix Group Name": "",
                    "Matrix Ranking?": "",
                    "Field Annotation": "",
                }
            )
    return csv_path, len(rows)


def write_operational_readiness_template(out_dir: Path) -> Path:
    """Sinh hồ sơ vận hành fail-closed; người có thẩm quyền phải hoàn tất."""
    path = out_dir / G5Q.OPERATIONAL_READINESS_JSON
    if path.exists():
        return path
    payload = {
        "schema_version": "G5-OPS-2026.1",
        "status": "DRAFT_REQUIRES_HUMAN_VERIFICATION",
        "access_control_review": {
            "completed": False,
            "reviewed_at": "[CẦN NGÀY YYYY-MM-DD]",
            "least_privilege_confirmed": False,
            "evidence_ref": "[CẦN MÃ BIÊN BẢN/SOP, KHÔNG PII]",
        },
        "backup_restore_test": {
            "completed": False,
            "tested_at": "[CẦN NGÀY YYYY-MM-DD]",
            "restore_verified": False,
            "checksum_verified": False,
            "evidence_ref": "[CẦN MÃ BIÊN BẢN, KHÔNG PII]",
        },
        "retention_plan": {
            "confirmed": False,
            "retention_rule": "[CẦN QUY TẮC THEO IRB, tài trợ và pháp luật]",
        },
        "protocol_deviations": {
            "reconciled": False,
            "open_count": "[CẦN SỐ NGUYÊN]",
            "log_ref": "[CẦN MÃ DEVIATION LOG, KHÔNG PII]",
        },
        "reviewer_role": "[CẦN DATA_MANAGER hoặc PI]",
        "reviewer_ref": "[CẦN MÃ THAM CHIẾU, KHÔNG GHI HỌ TÊN/PII]",
        "disclaimer": "Cần bác sĩ kiểm chứng.",
    }
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path


# ---------------------------------------------------------------------------
# GENERATE MAIN ARTIFACT (Markdown)
# ---------------------------------------------------------------------------

_SPECIALTY_LABELS = {
    "cardiology_hf":                 "Tim mạch / Suy tim",
    "metabolic_diabetes":            "Chuyển hóa / Đái tháo đường",
    "nephrology_ckd":                "Thận / Bệnh thận mạn (CKD)",
    "pulmonology_copd_asthma":       "Hô hấp / COPD-Hen phế quản",
    "neurology_stroke":              "Thần kinh / Đột quỵ",
    "musculoskeletal_pain":          "Cơ xương khớp / Đau mạn",
    "psychiatry_depression_anxiety": "Tâm thần / Trầm cảm-Lo âu",
    "gastroenterology":              "Tiêu hóa",
    "generic":                       "TỔNG QUÁT (không khớp chuyên khoa cụ thể)",
}


def generate_artifact(
    study: str, topic: str, design_code: str,
    n_adjusted: int, n_total: int, n_per_group: int,
    run_date: str, rows: list, specialty: str = "generic",
    specialty_runner_up=None, hypothesis_type=None, margin=None,
) -> str:
    is_srma = (design_code == "sr_ma")
    n_rows = len(rows)

    flowchart = build_strobe_flowchart(study, design_code, n_adjusted, n_total, n_per_group, specialty)
    specialty_label = _SPECIALTY_LABELS.get(specialty, specialty)

    lines = [
        "# A6 — KẾ HOẠCH QUẢN LÝ DỮ LIỆU (DRAFT)",
        f"**Đề tài:** {topic}  ",
        f"**Mã:** {study} | **Ngày:** {run_date} | **Thiết kế:** {design_code} | **N dự kiến:** {n_adjusted}  ",
        "**Trạng thái:** DRAFT — CHỜ BÁC SĨ ĐIỀN CÁC [CẦN...] VÀ XÁC NHẬN",
        "",
        "> **BẢO MẬT:** KHÔNG đưa PII vào pipeline. Chỉ xử lý bản đã khử định danh trong "
        "môi trường cục bộ được đơn vị cho phép; dữ liệu không được gửi tới mô hình AI.",
        "> Tham chiếu: ICH E6(R3) Data Governance; FDA Electronic Records 2024; "
        "CDISC CDASH; FAIR Principles (PMID: 26978244; DOI: 10.1038/sdata.2016.18).",
        "",
    ]
    if specialty == "generic":
        lines += [
            "> 🔴 **QUAN TRỌNG:** Hệ thống KHÔNG nhận diện được chuyên khoa cụ thể từ chủ đề "
            "đề tài, nên các biến Phơi nhiễm/Can thiệp và Kết cục chính dưới đây CHỈ LÀ "
            "PLACEHOLDER (`exposure_var`, `primary_outcome`) — **bác sĩ PHẢI tự đặt tên và "
            "định nghĩa các biến này theo PICO/SAP của đề tài trước khi dùng CRF.** Các nhóm "
            "biến khác (nhân khẩu, sinh hiệu, bệnh nền, xét nghiệm thường quy) vẫn dùng được.",
            "",
        ]
    else:
        lines += [
            f"> ℹ️ Chuyên khoa nhận diện từ chủ đề: **{specialty_label}** — CRF dưới đây đã chọn "
            "field lâm sàng/thuốc/kết cục phù hợp chuyên khoa này. Vẫn cần bác sĩ xác nhận từng "
            "biến khớp đúng với PICO/SAP thực tế, đặc biệt khi đề tài có yếu tố khác biệt.",
            "",
        ]
        if specialty_runner_up:
            runner_up_label = _SPECIALTY_LABELS.get(specialty_runner_up, specialty_runner_up)
            lines += [
                f"> 🟡 [CẦN XÁC NHẬN CHUYÊN KHOA] Chủ đề có tín hiệu từ khóa GẦN NGANG NHAU giữa "
                f"**{specialty_label}** (đã chọn) và **{runner_up_label}** — hệ thống chỉ chọn "
                f"{specialty_label} vì tính điểm đặc hiệu cao hơn một chút, KHÔNG phải chắc chắn "
                "tuyệt đối. Nếu đề tài thực ra trọng tâm là "
                f"{runner_up_label}, hãy sửa lại chủ đề rõ hơn (thêm từ khóa đặc hiệu) rồi chạy "
                "lại G5 — KHÔNG tự ý dùng CRF này nếu chưa xác nhận đúng chuyên khoa.",
                "",
            ]
    lines += [
        "---",
        "",
        "## PHẦN 1 — CẤU TRÚC CRF (Case Report Form)",
        "",
        f"Thiết kế: **{design_code}** | Chuyên khoa: **{specialty_label}** | "
        f"Tổng biến CRF: **{n_rows} dòng** | N dự kiến: **{n_adjusted}**",
        "",
    ]

    if is_srma:
        lines += [
            "*(SR/MA — Dùng biểu mẫu TRÍCH XUẤT thay vì CRF lâm sàng)*",
            "",
            "| STT | Biến | Nhóm | Loại | Nhãn |",
            "|-----|------|------|------|------|",
        ]
        for i, r in enumerate(rows, 1):
            lines.append(f"| {i} | `{r[0]}` | {r[1]} | {r[3]} | {r[4]} |")
    else:
        # Phân nhóm để hiển thị
        groups_seen = {}
        for r in rows:
            grp = r[1]
            if grp not in groups_seen:
                groups_seen[grp] = []
            groups_seen[grp].append(r)

        for grp, grp_rows in groups_seen.items():
            lines.append(f"### Nhóm: {grp} ({len(grp_rows)} biến)")
            lines.append("")
            lines.append("| Biến | Loại | Nhãn | Bắt buộc | Phạm vi |")
            lines.append("|------|------|------|----------|---------|")
            for r in grp_rows:
                rng = f"{r[8]}–{r[9]}" if r[8] and r[9] else "—"
                lines.append(f"| `{r[0]}` | {r[3]} | {r[4][:50]} | {'✓' if r[10]=='y' else ''} | {rng} |")
            lines.append("")

    lines += [
        "---",
        "",
        "## PHẦN 2 — REDCAP DATA DICTIONARY",
        "",
        f"File CSV: `G5_REDCap_dictionary_{study}.csv` (**{n_rows} dòng**)",
        f"Biến số (numeric): {len([r for r in rows if r[7] in ('number','integer')])}",
        f"Biến ngày: {len([r for r in rows if r[7] == 'date_ymd'])}",
        f"Biến bắt buộc: {len([r for r in rows if r[10] == 'y'])}",
        "",
        "Tóm tắt 10 biến đầu:",
        "| Variable | Form | Type | Label | Bắt buộc |",
        "|----------|------|------|-------|----------|",
    ]
    for r in rows[:10]:
        lines.append(f"| `{r[0]}` | {r[1]} | {r[3]} | {r[4][:45]} | {'✓' if r[10]=='y' else ''} |")
    lines += [
        "| ... | ... | ... | ... | ... |",
        f"| *(+{n_rows - 10} dòng — xem file CSV)* | | | | |",
        "",
        "---",
        "",
        "## PHẦN 3 — LUẬT KIỂM TRA DỮ LIỆU (Validation Rules)",
        "",
        "| Biến | Loại | Phạm vi | Quy tắc | Hành động |",
        "|------|------|---------|---------|-----------|",
    ]
    for r in VALIDATION_RULES:
        lines.append(f"| `{r[0]}` | {r[1]} | {r[2]} | {r[3]} | {r[4]} |")
    lines += [
        "",
        "---",
        "",
        "## PHẦN 4 — SƠ ĐỒ THAM GIA NGHIÊN CỨU (STROBE/CONSORT Flowchart)",
        "",
        "```",
        flowchart,
        "```",
        "",
        "---",
        "",
        "## PHẦN 5 — SCRIPTS TỰ ĐỘNG (Sinh từ CRF Dictionary)",
        "",
        f"**Thư mục:** `exports/{study}/scripts/`",
        "",
        "| Script | Mô tả | Đầu vào | Đầu ra |",
        "|--------|-------|---------|--------|",
        "| `data_cleaning.py` | Làm sạch REDCap export; ép kiểu; kiểm range | `data/raw/redcap_export.csv` | `data/processed/df_clean.csv` |",
        "| `data_quality_report.py` | Báo cáo N, % complete, vi phạm, trùng ID | `data/processed/df_clean.csv` | `data_quality_report.txt` |",
        "",
        "Chạy theo thứ tự:",
        "```bash",
        f"cd exports/{study}/",
        "python scripts/data_cleaning.py --input data/raw/redcap_export.csv",
        "python scripts/data_quality_report.py --input data/processed/df_clean.csv",
        "```",
        "",
        "---",
        "",
        "## PHẦN 6 — QUẢN TRỊ DỮ LIỆU THIẾU VÀ SAI LỆCH",
        "",
        "- G5 chỉ lập hồ sơ mức độ/mẫu hình thiếu và mở query; **không tự nội suy**.",
        "- Phương pháp complete-case, multiple imputation hoặc phân tích nhạy cảm phải "
        "được định trước ở SAP G4 theo cơ chế thiếu và estimand.",
        "- Mọi loại trừ người tham gia/điểm dữ liệu và protocol deviation phải có lý do, "
        "người xác nhận, thời điểm và audit trail.",
        "- [CẦN ĐỐI CHIẾU] Ngưỡng cảnh báo thiếu cho từng biến trọng yếu theo protocol/SAP.",
        "",
        "---",
        "",
        "## PHẦN 7 — CẤU TRÚC GÓI TÁI LẶP",
        "",
        "```",
        f"exports/{study}/",
        "├── data/             # KHÔNG commit — chứa dữ liệu thật",
        "│   ├── raw/          # dữ liệu thô từ REDCap export",
        "│   └── processed/    # df_clean.csv + data_quality_report.txt",
        "├── scripts/          # Python scripts tự động — có thể commit",
        "│   ├── data_cleaning.py        # làm sạch REDCap export",
        "│   └── data_quality_report.py  # báo cáo chất lượng",
        "├── output/           # bảng kết quả, hình (generate — không commit binary)",
        "├── docs/             # SAP, đề cương, các artifact G0-G4",
        f"│   ├── G4_A5_SAP_FINAL_{study}.md",
        f"│   └── G2_A3_ETHICS_PACKAGE_{study}.md",
        "└── README.md         # Hướng dẫn tái lặp đầy đủ",
        "```",
        "",
        "**`.gitignore` bắt buộc:**",
        "```",
        "data/raw/",
        "data/processed/",
        "*.csv",
        "*.xlsx",
        ".env",
        "```",
        "",
        "---",
        "",
        "## PHẦN 7B — VÒNG ĐỜI, BẢO MẬT VÀ AUDIT TRAIL",
        "",
        "- **Provenance:** bản raw đã khử định danh được copy chỉ đọc, gắn SHA-256; mọi "
        "bản clean phải truy ngược được về raw và đúng phiên bản dictionary.",
        "- **Audit trail/correction:** lưu giá trị ban đầu, thay đổi, lý do, thời điểm và "
        "vai trò thực hiện; không sửa/xóa giá trị lâm sàng chỉ vì nằm ngoài khoảng.",
        "- **Khử định danh:** tách bảng ánh xạ khỏi dataset phân tích; không đưa họ tên, "
        "ngày sinh đầy đủ, số hồ sơ, điện thoại, địa chỉ hoặc mã định danh trực tiếp vào G5.",
        "- **Phân quyền:** least privilege theo vai trò; rà quyền định kỳ; người phân tích "
        "chỉ nhận dataset đã khóa và không nhận bảng ánh xạ.",
        "- **Sao lưu:** backup mã hóa theo quy định đơn vị và phải có bằng chứng thử phục hồi.",
        "- **Lưu trữ/hủy:** thời hạn, nơi lưu, quyền truy cập và thủ tục hủy theo IRB, "
        "pháp luật và chính sách tài trợ/đơn vị; không dùng một thời hạn cứng cho mọi đề tài.",
        "- **Sự cố:** ghi nhận vi phạm bảo mật, đánh giá ảnh hưởng và báo bên có thẩm quyền.",
        "",
        "Tham chiếu: ICH E6(R3) §4.2–4.3; FDA Electronic Systems/Records/Signatures 2024.",
        "",
        "---",
        "",
        "## PHẦN 7C — CHIA SẺ DỮ LIỆU VÀ METADATA",
        "",
        "- Xác định dữ liệu/metadata/code được chia sẻ, thời điểm, repository, thời hạn "
        "bảo tồn và người giám sát theo DMP/IRB/consent.",
        "- Dữ liệu người tham gia chỉ chia sẻ khi quyền riêng tư, phạm vi đồng thuận và "
        "kiểm soát truy cập phù hợp; ghi rõ lý do đạo đức/pháp lý/kỹ thuật nếu hạn chế.",
        "- Kèm protocol, data dictionary, README, mã phân tích và điều kiện tái sử dụng "
        "để hỗ trợ FAIR, nhưng FAIR không đồng nghĩa dữ liệu nhạy cảm phải mở công khai.",
        "",
        "---",
        "",
        "## PHẦN 8 — CHECKLIST KHÓA CƠ SỞ DỮ LIỆU",
        "",
        "Thực hiện TRƯỚC khi chạy phân tích chính (G6):",
        "- [ ] Tất cả data queries đã được giải quyết (trả lời đủ)",
        "- [ ] Mức thiếu và protocol deviation đã đối chiếu theo SAP, không dùng ngưỡng chung tùy tiện",
        "- [ ] Audit trail REDCap đầy đủ (không có chỉnh sửa không có lý do)",
        "- [ ] Backup database kiểm tra thành công (restore test OK)",
        "- [ ] Dual-entry hoặc 10% spot-check xác nhận",
        "- [ ] Script `data_quality_report.py` chạy PASS (không có lỗi đỏ)",
        "- [ ] Ngày khóa DB: [CẦN BÁC SĨ ĐIỀN]",
        "- [ ] Người khóa DB (chữ ký): [CẦN]",
        "- [ ] Người chứng kiến (chữ ký): [CẦN]",
    ]
    if hypothesis_type in ("non_inferiority", "equivalence"):
        # THÊM 2026-07-24 (vòng lặp kiểm tra-hoàn thiện vòng 20): cùng khuôn
        # CONSORT-NI/Equivalence (Piaggio et al., JAMA 2012;308(24):2594-2604,
        # doi:10.1001/jama.2012.87802) đã đưa vào run_g7_auto.py/run_g8_auto.py
        # — quần thể ITT/PP và cách phân loại vi phạm đề cương PHẢI chốt TRƯỚC
        # khi khóa DB, vì khác biệt ITT/PP có thể đổi chiều kết luận non-inferior.
        _margin_txt = f"Δ = {margin}" if margin is not None else "[CẦN — chưa ghi ở G3]"
        lines += [
            f"- [ ] **[CẦN THỐNG KÊ VIÊN]** Đề tài giả thuyết **{hypothesis_type}** "
            f"({_margin_txt}) — CHỐT định nghĩa quần thể ITT và Per-Protocol (PP), "
            "cùng quy tắc phân loại vi phạm đề cương, TRƯỚC khi ký khóa DB "
            "(CONSORT-NI/Equivalence, Piaggio 2012, doi:10.1001/jama.2012.87802 — "
            "khác ITT/PP có thể đảo chiều kết luận non-inferior).",
        ]
    lines += [
        "",
        "---",
        "",
        "## PHẦN 9 — TIÊU CHÍ QUA CỔNG G5",
        "",
        "- [ ] **[CẦN BÁC SĨ]** Điền tất cả [CẦN...] trong CRF (biến phơi nhiễm/kết cục cụ thể)",
        "- [ ] **[CẦN BÁC SĨ]** Import REDCap dictionary CSV vào REDCap cơ sở",
        "- [ ] **[CẦN BÁC SĨ + ĐỘI NC]** Thu thập dữ liệu thật (chỉ sau G2 = LOCKED)",
        "- [ ] **[CẦN BÁC SĨ]** Spot-check 10% phiếu CRF",
        "- [ ] **[CẦN BÁC SĨ]** Chạy `data_cleaning.py` + `data_quality_report.py` → PASS",
        "- [ ] **[CẦN BÁC SĨ]** Ký biên bản khóa DB",
        "",
        "---",
        "",
        "*Cần bác sĩ kiểm chứng. KHÔNG đưa PII vào hệ thống.*",
        "*Chỉ chạy pipeline dữ liệu thật khử định danh trong môi trường cục bộ được đơn vị cho phép.*",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# DOCX
# ---------------------------------------------------------------------------

def write_docx(artifact: str, path: Path) -> bool:
    try:
        from docx import Document
        from docx.shared import Pt, RGBColor
        doc = Document()
        for line in artifact.split("\n"):
            stripped = line.strip()
            if not stripped:
                doc.add_paragraph("")
                continue
            if line.startswith("# "):
                doc.add_heading(line[2:], 0)
            elif line.startswith("## "):
                doc.add_heading(line[3:], 1)
            elif line.startswith("### "):
                doc.add_heading(line[4:], 2)
            elif "[CẦN" in line:
                p = doc.add_paragraph()
                run = p.add_run(stripped)
                run.font.color.rgb = RGBColor(0xCC, 0x44, 0x00)
            elif line.startswith("|"):
                p = doc.add_paragraph()
                p.add_run(stripped).font.size = Pt(8)
            elif stripped.startswith("- [ ]") or stripped.startswith("- [x]"):
                doc.add_paragraph(stripped, style="List Bullet")
            else:
                doc.add_paragraph(stripped)
        doc.save(path)
        return True
    except ImportError:
        return False
    except Exception:
        return False


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def load_cp(p) -> dict:
    p = Path(p)
    if p.exists():
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    return {}


def main():
    parser = argparse.ArgumentParser(
        description="G5 NÂNG CẤP — Quản lý dữ liệu với 55-row CRF + Python scripts + STROBE flowchart"
    )
    parser.add_argument("--study", required=True, help="Mã đề tài (vd SGLT2-HFpEF-2026)")
    args = parser.parse_args()

    study = re.sub(r'[^\w\-]', '_', args.study.strip().replace(" ", "-"))
    out = BASE / "exports" / study
    out.mkdir(parents=True, exist_ok=True)
    scripts_dir = out / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)

    run_date = datetime.now().strftime("%Y-%m-%d")

    # ★★ VÁ 2026-07-30 (audit toàn diện G0-G10, G5-F1 — CRITICAL) — CHẶN KHÓA ĐÈ
    # Ở PHÍA G5 CHÍNH NÓ, không chỉ ở lock_analysis_dataset.py.
    # Đo thực tế: dòng "cp = {...}" phía dưới ghi G5_checkpoint.json bằng một
    # dict LITERAL MỚI HOÀN TOÀN (g5_status="PENDING"), không đọc/merge checkpoint
    # cũ — nếu G5 đã được khóa+ký (lock_analysis_dataset.py rồi approve_gate.py
    # --gate G5), chạy lại CHÍNH TOOL NÀY sẽ xóa mất locked_dataset_sha256/
    # reviewer_role/data_lock_date mà lock_analysis_dataset.py đã ghi — làm
    # evidence_hash trong approval_ledger.json KHÔNG còn khớp checkpoint hiện
    # tại, chữ ký duyệt G5 mất hiệu lực NGAY LẬP TỨC, G5 tụt từ PASS_G5_DATA_
    # LOCKED về DRAFT, kéo theo G6/run_stats_analysis.py (đều gọi
    # ledger_approved("G5", ...)) bị chặn theo. Tệ hơn: chạy lại
    # lock_analysis_dataset.py để "sửa" KHÔNG cứu được — vì DATA_LOCK_manifest.json
    # (file RIÊNG, không bị lệnh này đụng tới) vẫn còn nguyên status=LOCKED với
    # đúng sha256 cũ, nên guard idempotent ở đó trả về SỚM (dòng ~526) TRƯỚC KHI
    # chạm tới đoạn ghi lại checkpoint — G5_checkpoint.json vẫn kẹt ở PENDING
    # vĩnh viễn, không có đường tự phục hồi.
    # Vá: kiểm ledger_approved("G5", ...) TRÊN CHÍNH checkpoint hiện tại NGAY TỪ
    # ĐẦU main(), trước khi làm bất kỳ việc gì (kể cả sinh CRF/DMP) — nếu G5 đã
    # có chữ ký hợp lệ khớp đúng bytes hiện tại, TỪ CHỐI chạy tiếp. Cùng tinh
    # thần "chặn khóa đè" đã áp dụng cho lock_analysis_dataset.py (2026-07-27)
    # — muốn soạn lại CRF/DMP cho một G5 đã khóa PHẢI là quyết định CÓ CHỦ Ý,
    # ghi lại được (tự tay lưu/đổi tên G5_checkpoint.json cũ), không diễn ra
    # âm thầm bên trong một lệnh trông vô hại.
    _g5_cp_path = out / "G5_checkpoint.json"
    if GC.ledger_approved("G5", study, _g5_cp_path, repo_root=BASE):
        print("🚫 G5 TỪ CHỐI CHẠY LẠI — checkpoint hiện tại ĐÃ CÓ chữ ký duyệt hợp lệ.")
        print(f"   {_g5_cp_path} đang khớp evidence_hash đã ký trong approval_ledger.json")
        print("   (G5 đã ở trạng thái đã khóa + đã duyệt).")
        print("   Chạy lại công cụ này sẽ GHI ĐÈ TOÀN BỘ checkpoint (dict mới, g5_status=")
        print("   PENDING), XÓA MẤT locked_dataset_sha256/reviewer_role/data_lock_date —")
        print("   làm chữ ký MẤT HIỆU LỰC NGAY LẬP TỨC dù dữ liệu/khoa học không đổi, và")
        print("   chạy lại lock_analysis_dataset.py sau đó KHÔNG tự sửa được (manifest cũ")
        print("   vẫn khớp hash nên trả về sớm, không ghi lại checkpoint).")
        print("   Nếu THẬT SỰ cần soạn lại CRF/DMP cho đề tài này (quyết định có chủ ý):")
        print(f"     1. Tự tay lưu/đổi tên {_g5_cp_path.name} hiện có (để việc đó hiện rõ")
        print("        trong lịch sử thư mục, không diễn ra âm thầm).")
        print("     2. Chạy lại run_g5_auto.py → lock_analysis_dataset.py → approve_gate.py")
        print("        --gate G5 từ đầu cho bộ dữ liệu MỚI.")
        return GC.EXIT_GUARDRAIL_FAIL

    # ★★ VÁ 2026-07-27 — G5 PHẢI ĐÒI G4 ĐÃ KÝ. Kiểm định độc lập đo được: G6 gọi
    # ledger_approved() 20 chỗ, run_stats_analysis.py 8 chỗ, còn G5 = 0 chỗ. Nghĩa là
    # cổng KHÓA DỮ LIỆU chạy được trong khi SAP CHƯA KHÓA.
    # Vì sao đây là lỗ hổng cốt lõi chứ không phải thiếu sót nhỏ: toàn bộ lý do G4 tồn tại
    # là chốt kế hoạch phân tích TRƯỚC khi ai nhìn thấy dữ liệu. Nếu khóa được dữ liệu mà
    # chưa khóa SAP, người nghiên cứu có thể xem dữ liệu rồi mới viết SAP — chính là HARKing
    # (đặt giả thuyết sau khi biết kết quả). Chuỗi chống p-hacking G4→G5→G6 đứt ngay mắt đầu.
    # Fail-closed, có đường đi tiếp tường minh cho đề tài thử nghiệm.
    _g4_artifact = out / f"G4_A5_SAP_FINAL_{study}.md"
    if not GC.ledger_approved("G4", study, _g4_artifact, repo_root=BASE):
        _why = GC.gate_block_reason("G4", study, _g4_artifact, repo_root=BASE)
        print("🚧 G5 DỪNG: chưa có phê duyệt THẬT cho cổng G4 (khóa SAP).")
        if _why:
            print(f"   ⚠️  LÝ DO: {_why}")
        print("   KHÔNG khóa dữ liệu khi kế hoạch phân tích chưa được khóa — nếu không,")
        print("   SAP có thể được viết SAU khi đã nhìn thấy dữ liệu (HARKing/p-hacking).")
        print("   Ghi phê duyệt thật (bác sĩ/thống kê viên TỰ TAY chạy, không nhờ agent):")
        print(f'     python3 tools/approve_gate.py --study "{study}" --gate G4 \\')
        print(f"       --artifact exports/{study}/G4_A5_SAP_FINAL_{study}.md \\")
        print('       --reviewer-role "METHODS_STATISTICS_REVIEWER" --reviewer-ref "<mã người duyệt>"')
        return GC.EXIT_BLOCKED

    # Đọc checkpoints
    g0 = load_cp(out / "G0_checkpoint.json")
    g1 = load_cp(out / "G1_checkpoint.json")
    g2 = load_cp(out / "G2_checkpoint.json")
    g3 = load_cp(out / "G3_checkpoint.json")

    # SỬA: .get(key, default) không dùng default khi key tồn tại với giá trị
    # null — bọc "or" tránh in "None" ra artifact và tránh crash arithmetic.
    topic       = g0.get("topic") or study
    # ★ VÁ 2026-07-28: dòng cũ chỉ đọc G1, cùng lỗi vừa vá ở run_g7_auto.py — G2
    # (nơi bác sĩ truyền --design tường minh) bị bỏ qua. Docstring của
    # resolve_design_code() từng khẳng định SAI "G5 vốn đã đọc cả hai checkpoint";
    # đã đính chính và nối G5 vào đúng hàm dùng chung.
    design_code, _design_drift_g5 = GC.resolve_design_code(out)
    if _design_drift_g5:
        print(f"  {_design_drift_g5}")
    n_adjusted  = g3.get("n_adjusted") or 0
    n_total     = (g3.get("n_total") or n_adjusted) if n_adjusted else 0
    n_per_group = (g3.get("n_per_group") or n_total // 2) if n_total else 0
    g3_effect_type = g3.get("effect_type")  # THÊM 2026-07-06: để đối chiếu loại kết cục vs CRF
    # THÊM 2026-07-24 (vòng lặp kiểm tra-hoàn thiện vòng 20): G5 trước đây
    # KHÔNG đọc specialist_modules (G1) lẫn hypothesis_type/margin (G3) —
    # cùng "khoảng trống truyền field" đã vá cho run_g7_auto.py/run_g8_auto.py/
    # run_g9_auto.py (chỉ riêng "economic", theo đúng phạm vi 2 gate đó đã làm
    # — KHÔNG mở rộng thêm prom_tool/prognostic_model vì G5 chưa có bundle CRF
    # tương ứng cho các mô-đun đó, tránh bịa field không có nguồn).
    specialist_modules = g1.get("specialist_modules") or []
    hypothesis_type = g3.get("hypothesis_type")
    margin = g3.get("margin")

    print(f"📊 G5 NÂNG CẤP — Quản lý dữ liệu: {study}")
    print(f"  → Đề tài: {topic}")
    print(f"  → Thiết kế: {design_code} | N={n_adjusted} (điều chỉnh) / {n_total} (cơ bản) / {n_per_group}/nhóm")

    # THÊM 2026-07-08: G5 chỉ soạn CRF/kế hoạch quản lý dữ liệu (được phép làm
    # song song/trước khi G2 LOCKED — CRF thường phải nộp kèm hồ sơ IRB). KHÔNG
    # chặn cứng bước này, chỉ hiển thị rõ trạng thái G2 để bác sĩ không nhầm là
    # đã được phép THU THẬP dữ liệu thật (việc đó vẫn chờ G2 LOCKED — xem G6).
    g2_status_raw = str(g2.get("g2_status") or "PENDING")
    g2_locked = bool(re.match(r'^LOCKED\b', g2_status_raw.strip().upper())) and \
        not re.search(r'(UN|CH[ƯU]A|KH[ÔO]NG|NOT)\s*LOCKED', g2_status_raw.strip().upper())
    if not g2_locked:
        print(f"  ⚠️  G2 (IRB) chưa LOCKED ({g2_status_raw}) — được phép soạn CRF/kế hoạch dữ liệu "
              "ngay bây giờ, nhưng KHÔNG được thu thập dữ liệu thật cho tới khi G2 LOCKED.")

    # Xây CRF theo thiết kế + chuyên khoa nhận diện từ topic (KHÔNG cứng hóa
    # field của 1 đề tài mẫu cho mọi chủ đề khác — xem detect_specialty())
    rows, specialty = build_redcap_rows(design_code, topic)

    # THÊM 2026-07-24 (vòng lặp kiểm tra-hoàn thiện vòng 20): "nối thêm, không
    # thay thế" — cùng khuôn run_g7_auto.py/run_g8_auto.py/run_g9_auto.py đã
    # áp dụng cho checklist báo cáo CHEERS khi economic là cấu phần CỘNG THÊM
    # (design_code chính không phải "economic" nhưng G1 phát hiện tín hiệu
    # kinh tế y tế trong chủ đề, vd RCT có tiểu mục chi phí-hiệu quả).
    if "economic" in specialist_modules and design_code != "economic":
        # SỬA 2026-07-24 (vòng lặp kiểm tra-hoàn thiện vòng 21, phát hiện HIGH,
        # tự phát hiện lỗi do CHÍNH bản vá vòng 20 gây ra): _ECONOMIC_FIELDS tự
        # khai "record_id" riêng (dùng khi design_code chính LÀ "economic",
        # đứng một mình — không đi qua _BASE_ADMIN). Nhưng khi nối THÊM vào một
        # CRF đã có _BASE_ADMIN (rct/cohort/...), "record_id" bị định nghĩa 2
        # LẦN với Form Name/label khác nhau trong CÙNG data dictionary — REDCap
        # yêu cầu tên biến duy nhất, import sẽ lỗi/không xác định. Loại các
        # trường đã tồn tại theo TÊN trước khi nối, để _BASE_ADMIN thắng.
        existing_names = {r[0] for r in rows}
        add_on_fields = [r for r in _ECONOMIC_FIELDS if r[0] not in existing_names]
        rows = rows + add_on_fields
        print("  → CRF: nối thêm bộ trường KINH TẾ Y TẾ (CHEERS 2022) — "
              "specialist_modules phát hiện 'economic' cộng thêm ở G1")

    print(f"  → Chuyên khoa nhận diện: {_SPECIALTY_LABELS.get(specialty, specialty)}")
    print(f"  → CRF: {len(rows)} dòng (thiết kế: {design_code})")
    if specialty == "generic":
        print("  ⚠️  Không khớp chuyên khoa cụ thể — exposure/outcome là placeholder, "
              "bác sĩ PHẢI tự đặt tên theo PICO/SAP")

    # THÊM 2026-07-06: CRF chọn field kết cục theo TỪ KHÓA CHỦ ĐỀ (bundle chuyên
    # khoa), KHÔNG theo loại biến kết cục thật. Với effect_type=MD (kết cục LIÊN
    # TỤC — đau NRS, HbA1c, chất lượng sống…), phần lớn bundle lại đặt field kết
    # cục chính kiểu nhị phân/biến cố (radio + ngày) → CRF SAI loại biến. Guardrail
    # cấu trúc KHÔNG bắt được (chỉ kiểm placeholder/PII/disclaimer). Cảnh báo để
    # bác sĩ không bị đánh lừa rằng CRF đã đúng — KHÔNG tự đổi field (an toàn:
    # chỉ nhắc, việc đổi thuộc bác sĩ). Kiểm định đối kháng vòng 2.
    if g3_effect_type == "MD" and specialty != "musculoskeletal_pain":
        print("  ⚠️  effect_type=MD (kết cục LIÊN TỤC theo G3) nhưng bundle "
              f"'{_SPECIALTY_LABELS.get(specialty, specialty)}' mặc định field kết cục chính "
              "kiểu NHỊ PHÂN/biến cố — bác sĩ PHẢI thay bằng field số (liên tục) đo lường "
              "trực tiếp kết cục (vd điểm đau, nồng độ, thang chất lượng sống) trước khi dùng CRF.")

    # THÊM 2026-07-02: guardrail cấu trúc không kiểm được đúng-sai nội dung
    # lâm sàng (xem docstring detect_specialty_with_confidence). Tính độ tin
    # cậy phân loại chuyên khoa — cảnh báo khi 2 chuyên khoa điểm quá gần.
    _, specialty_runner_up, specialty_ambiguous = detect_specialty_with_confidence(topic)
    if specialty_ambiguous:
        print(f"  ⚠️  Chủ đề CÓ THỂ thuộc cả '{_SPECIALTY_LABELS.get(specialty, specialty)}' "
              f"lẫn '{_SPECIALTY_LABELS.get(specialty_runner_up, specialty_runner_up)}' "
              "(điểm nhận diện gần nhau) — bác sĩ nên xác nhận đúng trọng tâm chuyên khoa")

    # Sinh artifact Markdown
    artifact = generate_artifact(
        study, topic, design_code,
        n_adjusted, n_total, n_per_group,
        run_date, rows, specialty,
        specialty_runner_up=specialty_runner_up,
        hypothesis_type=hypothesis_type, margin=margin,
    )
    md = out / f"G5_A6_DATA_MGMT_{study}.md"
    md.write_text(artifact, encoding="utf-8")
    print(f"  → Lưu: {md} ({len(artifact)//1000}KB)")

    # Sinh REDCap CSV
    csv_path, n_vars = generate_csv(study, out, rows)
    print(f"  → REDCap CSV: {csv_path} ({n_vars} dòng)")
    operations_path = write_operational_readiness_template(out)
    print(f"  → Hồ sơ vận hành: {operations_path}")

    # Guardrail R1–R7
    errors, warnings = guardrail(artifact)
    for w in warnings:
        print(f"  {w}")
    for e in errors:
        print(f"  {e}")
    status = "✅ PASS" if not errors else f"⚠ {len(errors)} LỖI"
    print(f"  → Guardrail: {status}")

    # Sinh data_cleaning.py
    cleaning_script = gen_data_cleaning_script(study, design_code, rows)
    cleaning_path = scripts_dir / "data_cleaning.py"
    cleaning_path.write_text(cleaning_script, encoding="utf-8")
    print(f"  → Script sinh: {cleaning_path}")

    # Sinh data_quality_report.py
    dqr_script = gen_data_quality_report_script(study, design_code, rows)
    dqr_path = scripts_dir / "data_quality_report.py"
    dqr_path.write_text(dqr_script, encoding="utf-8")
    print(f"  → Script sinh: {dqr_path}")

    # Sinh DOCX
    docx_ok = write_docx(artifact, out / f"G5_A6_DATA_MGMT_{study}.docx")
    print(f"  → DOCX: {'✅ lưu' if docx_ok else '⚠ bỏ qua (python-docx chưa cài)'}")

    # Lưu checkpoint
    cp = {
        "gate":           "G5",
        "study":          study,
        "run_date":       run_date,
        "version":        "3.0-data-governance-contract",
        "quality_contract_version": G5Q.QUALITY_CONTRACT_VERSION,
        "g5_status":      "PENDING",
        "design_code":    design_code,
        "specialty":      specialty,
        "specialty_is_generic_placeholder": specialty == "generic",
        "specialty_ambiguous": specialty_ambiguous,
        "specialty_runner_up": specialty_runner_up,
        "redcap_rows":    n_vars,
        "crf_columns":    [r[0] for r in rows],
        "scripts_generated": [
            str(cleaning_path.relative_to(BASE)),
            str(dqr_path.relative_to(BASE)),
        ],
        "strobe_flowchart": "included_in_artifact",
        "database_lock_status": "PENDING — dữ liệu chưa thu thập (chờ G2 LOCKED)",
        "guardrail": status,
        "automation_level": "DRAFT_AUTOMATED_HUMAN_CONTROLLED",
        "pending_doctor_actions": [
            "Điền tất cả [CẦN...] trong CRF (biến phơi nhiễm/kết cục cụ thể)",
            "Import REDCap dictionary CSV vào REDCap cơ sở",
            f"Hoàn tất {G5Q.OPERATIONAL_READINESS_JSON} bằng bằng chứng tại đơn vị",
            "Thu thập dữ liệu thật (chỉ sau G2 = LOCKED)",
            "Spot-check 10% phiếu CRF",
            "Chạy data_cleaning.py + data_quality_report.py trên dữ liệu thật → PASS",
            "Ký biên bản khóa DB",
        ],
    }
    cp_path = out / "G5_checkpoint.json"
    cp_path.write_text(json.dumps(cp, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"💾 Checkpoint: {cp_path}")

    quality_gate = G5Q.evaluate_study(
        study,
        out,
        repo_root=BASE,
        write=True,
    )
    print(f"  → G5 quality status: {quality_gate['status']}")
    print(f"  → Báo cáo: {out / G5Q.REPORT_JSON}")

    print()
    if quality_gate["status"] == G5Q.STATUS_BLOCKED:
        print("🚧 G5 BỊ CHẶN BỞI LỖI CHẤT LƯỢNG")
    elif quality_gate["status"] == G5Q.STATUS_DRAFT:
        print("🟡 BỘ CÔNG CỤ G5 ĐÃ TẠO — CHƯA QUA CỔNG, CẦN DỮ LIỆU THẬT")
    elif quality_gate["status"] == G5Q.STATUS_READY:
        print("🟠 DATASET ĐÃ KHÓA KỸ THUẬT — CHỜ NGƯỜI CÓ THẨM QUYỀN DUYỆT G5")
    else:
        print("✅ G5 ĐÃ QUA: DATASET KHÓA + PHÊ DUYỆT G5 HỢP LỆ")
    print(f"  CRF: {n_vars} dòng ({design_code}) | Guardrail: {status}")
    print(f"  Scripts: data_cleaning.py + data_quality_report.py → {scripts_dir}")
    print("  STROBE flowchart: nhúng trong artifact")
    print("  Cần bác sĩ kiểm chứng.")
    if errors or quality_gate["status"] == G5Q.STATUS_BLOCKED:
        return GC.EXIT_GUARDRAIL_FAIL
    return GC.EXIT_OK


if __name__ == "__main__":
    # VÁ 2026-07-27: TRƯỚC ĐÂY gọi main() trần nên MỌI mã thoát main() trả về đều bị
    # vứt và tiến trình luôn exit 0 — chốt chặn G4 vừa thêm sẽ in cảnh báo rồi vẫn báo
    # "thành công" với caller/script tự động. Cùng lớp lỗi đã vá ở run_g10_assemble.py.
    sys.exit(main() or 0)
