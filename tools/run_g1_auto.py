"""
run_g1_auto.py — TỰ ĐỘNG HÓA CỔNG G1: Thiết kế nghiên cứu + SAP skeleton

Đọc G0_checkpoint.json (từ run_g0_auto.py) → sinh tự động:
  1. Suy loại thiết kế (rule-based từ PICO type + evidence landscape)
  2. Bảng 2-3 ứng viên thiết kế có so sánh
  3. Kiểm soát 7 sai lệch (bias control table)
  4. Estimand ICH E9(R1) nếu can thiệp
  5. Trích xuất effect size ƯỚC LƯỢNG từ abstracts PubMed thật (để tính cỡ mẫu)
  6. KHỐI THIẾT KẾ hoàn chỉnh (dán vào Protocol)
  7. SAP skeleton 12 mục (bác sĩ điền [CẦN...])
  8. Dummy tables 4 bảng (shell sẵn sàng)
  9. SAP Lock Certificate (chờ bác sĩ ký → mở G4)
  10. Guardrail R1-R7 + xuất A2 .md + .docx + G1_checkpoint.json

Bác sĩ chỉ cần: xác nhận thiết kế chọn + điền effect size thật từ pilot/y văn.

Sử dụng:
    python tools/run_g1_auto.py --study "SGLT2-HFpEF-2026"         # đọc G0 checkpoint
    python tools/run_g1_auto.py --study "NEW" --topic "..." --question-type treatment
"""

import argparse
import json
import os
import re
import sys
import time
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Optional

_REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_REPO_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import gate_contract as GC  # noqa: E402  (hợp đồng DỪNG dùng chung)

_DEFAULT_EMAIL = "bsluanbv175@gmail.com"
if not os.environ.get("NCBI_EMAIL"):
    os.environ["NCBI_EMAIL"] = _DEFAULT_EMAIL
if not os.environ.get("USE_MOCK_SOURCES"):
    os.environ["USE_MOCK_SOURCES"] = "false"


# ════════════════════════════════════════════════════════════════════════════
# 1. THIẾT KẾ NGHIÊN CỨU — CÁC LOẠI VÀ TIÊU CHÍ CHỌN
# ════════════════════════════════════════════════════════════════════════════

QUESTION_TYPES = {
    "treatment":    "Can thiệp / Điều trị (RCT preferred)",
    "diagnosis":    "Chẩn đoán (cross-sectional diagnostic accuracy)",
    "prognosis":    "Tiên lượng (cohort)",
    "harm":         "Tác hại / An toàn (cohort hoặc case-control)",
    "descriptive":  "Mô tả (cross-sectional)",
    "sr":           "Tổng hợp bằng chứng (SR/meta-analysis)",
    # THÊM 2026-07-19 (audit vòng 3, D1_qual_mixed_gate_coverage — NGHIÊM TRỌNG):
    # trước bản vá này, infer_study_design() KHÔNG có nhánh nào cho định tính/
    # hỗn hợp — mọi đề tài định tính bị âm thầm gán internal_code="rct" (khi
    # question_type mặc định "treatment") hoặc "cross_sectional" (nhánh else
    # "descriptive"), kéo theo G3 tính cỡ mẫu bằng công thức SAI (power thay vì
    # bão hòa dữ liệu), G4 hard-block khi N=0, G7 gán sai checklist STROBE thay
    # COREQ/SRQR. Cùng lớp lỗi & cùng khuôn vá đã làm cho "prediction" 2026-07-17.
    "qualitative":  "Định tính/hỗn hợp (COREQ/SRQR — bão hòa dữ liệu thay power)",
}

REPORTING_STANDARDS = {
    "rct":              "CONSORT 2025 (+Extension phù hợp)",
    "cohort":           "STROBE",
    "case_control":     "STROBE",
    "cross_sectional":  "STROBE",
    "sr_ma":            "PRISMA 2020",
    "diagnostic":       "STARD 2015",
    "prediction":       "TRIPOD+AI 2024",
    "qualitative":      "COREQ (phỏng vấn/nhóm tiêu điểm) / SRQR (định tính nói chung)",
}

BIAS_CONTROLS = {
    "rct": [
        ("Selection bias",  "Ngẫu nhiên hóa (phân tầng theo trung tâm/yếu tố tiên lượng)"),
        ("Performance bias", "Làm mù người tham gia + can thiệp viên (nếu khả thi)"),
        ("Detection bias",  "Làm mù người đánh giá kết cục (outcome assessor blinding)"),
        ("Attrition bias",  "ITT analysis + tipping-point sensitivity cho mất theo dõi"),
        ("Reporting bias",  "Đăng ký ClinicalTrials/DRKS trước + SAP lock (G4)"),
        ("Confounding",     "Ngẫu nhiên hóa (triệt tiêu confounders đã biết + chưa biết)"),
        ("Information bias","Định nghĩa vận hành rõ ràng + calibrate công cụ đo"),
    ],
    "cohort": [
        ("Selection bias",  "Chọn mẫu đại diện; tiêu chí chọn/loại rõ ràng; matching nếu cần"),
        ("Information bias","Định nghĩa phơi nhiễm/kết cục tiền định; blinded outcome assessment"),
        ("Confounding",     "Đa biến + DAG; propensity score matching/weighting nếu cần"),
        ("Attrition bias",  "Theo dõi tích cực; phân tích nhạy cảm cho mất theo dõi"),
        ("Lead-time bias",  "Thời điểm bắt đầu theo dõi nhất quán cho mọi người tham gia"),
        ("Reporting bias",  "Đăng ký nghiên cứu trước (quan sát) + SAP lock"),
        ("Detection bias",  "Blinded adjudication cho endpoint có chủ quan"),
    ],
    "case_control": [
        ("Selection bias",  "Chọn chứng từ dân số nguồn sinh ra ca; tỷ lệ 1:2–4"),
        ("Information bias","Recall bias: tiền định câu hỏi; blinded interviewer; data từ hồ sơ"),
        ("Confounding",     "Matching theo age/sex + đa biến đa chiều"),
        ("Berkson bias",    "Tránh chọn ca+chứng từ cùng một cơ sở y tế nếu phơi nhiễm liên quan nhập viện"),
        ("Reporting bias",  "Pre-registration nếu có + SAP lock"),
        ("Neyman bias",     "Ca là ca mới/incident (không phải prevalent) để tránh bỏ ca tử vong sớm"),
        ("Detection bias",  "Tiêu chí chẩn đoán rõ ràng, không phụ thuộc phơi nhiễm"),
    ],
    "cross_sectional": [
        ("Selection bias",  "Sampling ngẫu nhiên hoặc liên tiếp; tránh tự chọn"),
        ("Information bias","Đo phơi nhiễm + kết cục cùng thời điểm → không suy nhân quả"),
        ("Confounding",     "Đa biến; hạn chế: cùng thời điểm → không loại trừ causal confounders"),
        ("Prevalence-incidence bias", "Thiết kế chỉ ước lượng hiện mắc; bàn luận giới hạn này"),
        ("Non-response bias", "So sánh người trả lời vs không trả lời (nếu có thể)"),
        ("Social desirability", "Tự báo cáo → có thể underreport hành vi tiêu cực"),
        ("Reporting bias",  "Đăng ký nghiên cứu + tiền định phân tích"),
    ],
    "diagnostic": [
        ("Spectrum bias",   "Bao gồm đa dạng mức độ bệnh (nhẹ-nặng) + giống bệnh tương tự"),
        ("Verification bias","Mọi người tham gia nhận CÙNG reference standard"),
        ("Incorporation bias","Reference standard KHÔNG chứa thành phần của index test"),
        ("Observer bias",   "Đọc index test mù với reference standard"),
        ("Partial verification", "Tránh chỉ gửi dương tính để xác nhận → overestimate Se"),
        ("Disease progression", "Index test và reference standard đo ĐỒNG THỜI"),
        ("Reporting bias",  "STARD checklist + report tất cả ngưỡng đã thử"),
    ],
    "sr_ma": [
        ("Publication bias", "Funnel plot + Egger test; search unpublished (clinicaltrials.gov)"),
        ("Search bias",      "≥2 cơ sở dữ liệu; không giới hạn ngôn ngữ; kiểm thư xám"),
        ("Selection bias",   "2 screener độc lập + consensus/third screener khi bất đồng"),
        ("Extraction bias",  "2 người trích xuất độc lập; kappa inter-rater"),
        ("Assessment bias",  "RoB 2 cho RCT; ROBINS-I cho quan sát; QUADAS-2 cho chẩn đoán"),
        ("Heterogeneity",    "Định lượng I²/τ²; không gộp khi I² > 75% không có lý do lâm sàng"),
        ("Reporting bias",   "PRISMA 2020 + registrátion (PROSPERO)"),
    ],
    # THÊM 2026-07-17 (round audit gate — tiếp nối hoàn thiện gate cho
    # "prediction"): trước đây "prediction" KHÔNG có trong dict này -> .get()
    # fallback im lặng về bias_controls của "cohort" (không sai hoàn toàn —
    # selection/confounding vẫn liên quan — nhưng thiếu các mối lo ĐẶC THÙ mô
    # hình tiên lượng như overfitting/optimism, data leakage, class imbalance).
    # 4 domain dưới đây theo ĐÚNG cấu trúc PROBAST+AI đã xác minh trực tiếp:
    # Moons KGM, Damen JAA, Kaul T, et al. "PROBAST+AI: an updated quality,
    # risk of bias, and applicability assessment tool for prediction models
    # using regression or artificial intelligence methods." BMJ 2025;388:
    # e082505 (PMID 40127903) — GIỮ NGUYÊN 4 domain của PROBAST 2019 gốc
    # (Participants and data sources / Predictors / Outcome / Analysis),
    # KHÔNG thêm domain mới — mối lo AI/ML (overfitting, data leakage, class
    # imbalance) được gộp vào domain Analysis, không phải domain riêng.
    "prediction": [
        ("Selection bias (Participants/data sources)",
         "Chọn mẫu đại diện quần thể đích; tiêu chí chọn/loại rõ ràng — PROBAST+AI domain 1"),
        ("Predictor bias",
         "Định nghĩa/thời điểm đo biến tiên đoán nhất quán phát triển-đánh giá; "
         "KHÔNG dùng biến chỉ có SAU thời điểm dự đoán (data leakage) — PROBAST+AI domain 2"),
        ("Outcome bias",
         "Định nghĩa/thời điểm đo kết cục tiền định, nhất quán, đánh giá không "
         "biết trước biến tiên đoán (blinded) — PROBAST+AI domain 3"),
        ("Overfitting/optimism",
         "Internal validation bằng bootstrap/cross-validation; shrinkage/penalization "
         "(LASSO/ridge) nếu số biến tiên đoán lớn so với cỡ mẫu — PROBAST+AI domain 4 (Analysis)"),
        ("Missing data",
         "Multiple imputation (không complete-case đơn thuần trừ khi MCAR) — PROBAST+AI domain 4"),
        ("Class imbalance/fairness",
         "Đánh giá hiệu năng/công bằng theo phân nhóm nhân khẩu-xã hội, không chỉ tổng thể "
         "(TRIPOD+AI mục 14/23a) — PROBAST+AI domain 4"),
        ("Reporting bias",
         "Đăng ký/giao thức trước nếu có + checklist TRIPOD+AI đầy đủ (không chỉ báo cáo mô hình cuối)"),
    ],
    # THÊM 2026-07-19 (audit vòng 3, D1 — NGHIÊM TRỌNG): định tính KHÔNG dùng
    # khung "bias" định lượng (selection/confounding/detection...) — nếu thiếu
    # entry này, .get(internal, BIAS_CONTROLS["cohort"]) sẽ fallback SAI sang
    # bias cohort. Dùng khung TRUSTWORTHINESS chuẩn (Lincoln & Guba) mà chính
    # nghien-cuu-dinh-tinh.md đòi ("bảng trustworthiness 4 tiêu chí").
    "qualitative": [
        ("Credibility (độ tin cậy nội tại)",
         "Tam giác đạc nguồn/phương pháp (triangulation); member checking; thời gian tương tác đủ dài"),
        ("Transferability (khả năng chuyển giao)",
         "Mô tả dày (thick description) bối cảnh + đặc điểm mẫu để người đọc tự đánh giá áp dụng"),
        ("Dependability (độ tin cậy quy trình)",
         "Audit trail rõ ràng (nhật ký quyết định phân tích); quy trình mã hóa nhất quán"),
        ("Confirmability (tính khách quan)",
         "Phản tư của nhà nghiên cứu (reflexivity); đối chiếu độc lập giữa 2 người mã hóa"),
        ("Reporting bias",
         "Chuẩn báo cáo COREQ (phỏng vấn/nhóm)/SRQR đầy đủ — không chọn lọc quote hợp ý"),
    ],
}

# ════════════════════════════════════════════════════════════════════════════
# 2. SUY LOẠI THIẾT KẾ (Tree-of-Thoughts)
# ════════════════════════════════════════════════════════════════════════════

def _kw_in(keywords, text):
    """
    Khớp từ khóa theo ranh giới token (không phải substring thô) — tránh
    false-positive kiểu "auc" khớp nhầm bên trong 1 từ dài hơn, cùng loại
    bug substring-match đã sửa ở G6/G7 (_score()/_TABLE1_OUTCOME_KW).
    """
    for kw in keywords:
        if re.search(r'(?<![a-z0-9])' + re.escape(kw) + r'(?![a-z0-9])', text):
            return True
    return False


_DESIGN_LABEL = {
    "cross_sectional": "Nghiên cứu Cắt ngang Mô tả (Cross-sectional / Prevalence)",
    "cohort": "Nghiên cứu Đoàn hệ (Cohort)",
    "case_control": "Nghiên cứu Bệnh-Chứng (Case-control)",
    "rct": "Thử nghiệm Ngẫu nhiên Đối chứng (RCT)",
    "diagnostic": "Nghiên cứu Độ chính xác Chẩn đoán",
    "sr_ma": "Tổng quan Hệ thống / Phân tích gộp",
}


# ════════════════════════════════════════════════════════════════════════════
# 1bis. MÔ-ĐUN CHUYÊN BIỆT (điều kiện, cộng thêm — KHÔNG thay đổi thiết kế chính)
# ════════════════════════════════════════════════════════════════════════════
# Bổ sung 2026-07-05: 4 agent chuyên biệt (cong-cu-do-luong, mo-hinh-tien-luong,
# kinh-te-y-te, nghien-cuu-dinh-tinh) đã có trong bản đồ đội (README.md,
# dieu-phoi-nghien-cuu.md) và trong control-plane dry-run tools/orchestrator/
# nhưng CHƯA từng nối vào automation THẬT của G1 — đề tài cần 1 trong 4 năng
# lực này trước đây không được nhắc gì trong A2. Từ khóa CỐ Ý cụ thể/nhiều-từ
# (không dùng từ đơn chung chung như "tiên lượng"/"auc" đã dùng cho
# infer_study_design ở trên) để tránh bắt nhầm đề tài tiên lượng/chẩn đoán
# thông thường thành "đang xây mô hình/công cụ mới".
SPECIALIST_MODULE_KEYWORDS: dict[str, list[str]] = {
    "prom_tool": [
        "xây dựng thang đo", "phát triển thang đo", "phát triển bộ câu hỏi",
        "phát triển bộ công cụ", "kiểm định thang đo", "kiểm định bộ câu hỏi",
        "dịch thuật thích nghi văn hóa", "thích nghi văn hóa", "cronbach",
        "phân tích nhân tố khám phá", "phân tích nhân tố khẳng định",
        "cosmin", "prom", "patient-reported outcome",
    ],
    "prognostic_model": [
        "mô hình tiên lượng", "mô hình dự báo", "mô hình dự đoán", "nomogram",
        "prediction model", "predictive model", "xây dựng thang điểm nguy cơ",
        "phát triển thang điểm nguy cơ", "tripod",
    ],
    "economic": [
        "chi phí hiệu quả", "chi phí-hiệu quả", "cost-effectiveness",
        "cost effectiveness", "kinh tế y tế", "chi phí thỏa dụng",
        "cost-utility", "icer", "qaly", "tác động ngân sách", "budget impact",
        "phân tích chi phí", "cheers",
    ],
    "qualitative": [
        "nghiên cứu định tính", "phỏng vấn sâu", "nhóm tập trung",
        "focus group", "in-depth interview", "grounded theory",
        "phenomenology", "hiện tượng học", "phân tích chủ đề",
        "thematic analysis", "coreq", "srqr",
        # THÊM 2026-07-19 (audit vòng 3, D1 — khớp ĐÚNG 3 cụm doctrine
        # nghien-cuu-dinh-tinh.md dòng 35 tự công bố: "Phương pháp khớp câu
        # hỏi: 'trải nghiệm/ý nghĩa/rào cản' → định tính" — trước bản vá này,
        # danh sách keyword ở đây KHÔNG chứa 3 cụm mà chính doctrine dùng làm
        # ví dụ chuẩn, nên ví dụ mẫu của agent tự nó cũng không kích hoạt được
        # qua đường tự động).
        "trải nghiệm", "ý nghĩa", "rào cản",
    ],
}

_SPECIALIST_MODULE_LABEL = {
    "prom_tool": "Kiểm định công cụ đo lường (COSMIN)",
    "prognostic_model": "Mô hình tiên lượng/dự báo (TRIPOD+AI)",
    "economic": "Phân tích kinh tế y tế (CHEERS 2022)",
    "qualitative": "Nghiên cứu định tính/hỗn hợp (COREQ/SRQR)",
}


def detect_specialist_modules(topic: str) -> list[str]:
    """Phát hiện tín hiệu ĐỘC LẬP (không loại trừ lẫn nhau — 1 đề tài có thể
    cần nhiều mô-đun cùng lúc, khác với infer_study_design vốn chọn 1 thiết
    kế chính). Trả về list rỗng nếu không phát hiện tín hiệu nào."""
    topic_lower = topic.lower()
    return [
        module for module, keywords in SPECIALIST_MODULE_KEYWORDS.items()
        if _kw_in(keywords, topic_lower)
    ]


def _specialist_module_section(module: str) -> str:
    if module == "prom_tool":
        return f"""### MÔ-ĐUN — {_SPECIALIST_MODULE_LABEL[module]}
> Phát hiện tín hiệu: đề tài có cấu phần xây dựng/kiểm định thang đo/bộ câu hỏi (PROM).

- Thiết kế item + miền nội dung: [CẦN nhóm nghiên cứu xác định + item pool]
- Độ giá trị nội dung (content validity): [CẦN hội đồng chuyên gia + hệ số CVI]
- Độ giá trị cấu trúc: ☐ EFA  ☐ CFA — [CẦN cỡ mẫu đủ, thường ≥5–10 người/item]
- Dịch thuật & thích nghi văn hóa (nếu công cụ gốc nước ngoài): forward–back translation + hội đồng chuyên gia [CẦN]
- Độ tin cậy: Cronbach's α (nội tại, ngưỡng thường ≥0.70) [CẦN] · Test–retest ICC [CẦN khoảng thời gian lặp lại]
- Độ giá trị hội tụ/phân biệt: [CẦN công cụ tham chiếu đã kiểm định]
- Độ đáp ứng & MCID (nếu đo thay đổi theo thời gian): [CẦN]
- Sai số đo (SEM/SDC), floor/ceiling effect: [CẦN]
- Chuẩn báo cáo: COSMIN Reporting Guideline.
- → Cân nhắc mời agent `cong-cu-do-luong` hỗ trợ chi tiết từng bước.
"""
    if module == "prognostic_model":
        return f"""### MÔ-ĐUN — {_SPECIALIST_MODULE_LABEL[module]}
> Phát hiện tín hiệu: đề tài xây dựng/kiểm định mô hình tiên lượng-dự báo mới.

- Ứng viên dự báo (candidate predictors): [CẦN lý luận lâm sàng/y văn — KHÔNG data-dredging]
- EPV/EPP đủ: [CẦN tính theo số biến dự kiến — quy tắc thường dùng ≥10 sự kiện/biến]
- Xử lý dữ liệu thiếu: ☐ Multiple imputation [CẦN phương pháp cụ thể]
- Hiệu chuẩn (calibration): calibration plot + calibration-in-the-large/slope [CẦN]
- Phân biệt (discrimination): C-statistic/AUC (95%CI) [CẦN]
- Kiểm định: ☐ Nội (bootstrap/cross-validation)  ☐ Ngoại (quần thể độc lập) [CẦN]
- Decision Curve Analysis (DCA): [CẦN nếu mục tiêu hỗ trợ quyết định lâm sàng]
- Trình bày mô hình: điểm số/nomogram [CẦN]
- Nếu THẨM ĐỊNH mô hình có sẵn (không xây mới): dùng PROBAST thay vì mục trên.
- Chuẩn báo cáo: TRIPOD+AI 2024.
- → Cân nhắc mời agent `mo-hinh-tien-luong` hỗ trợ chi tiết từng bước.
"""
    if module == "economic":
        return f"""### MÔ-ĐUN — {_SPECIALIST_MODULE_LABEL[module]}
> Phát hiện tín hiệu: đề tài có cấu phần chi phí–hiệu quả/kinh tế y tế.

- Góc nhìn phân tích: ☐ Xã hội  ☐ Người chi trả (BHYT)  ☐ Bệnh viện [CẦN XÁC NHẬN]
- Khung thời gian + tỷ lệ chiết khấu: [CẦN]
- Nhận diện–đo lường–định giá chi phí: [CẦN nguồn đơn giá thật — KHÔNG bịa]
- Thước đo hiệu quả: ☐ QALY (CUA)  ☐ Đơn vị lâm sàng (CEA)  ☐ Tiền tệ (CBA) [CẦN]
- ICER + ngưỡng sẵn lòng chi trả: [CẦN ngưỡng theo bối cảnh VN — có nguồn]
- Phân tích độ nhạy: ☐ Một chiều  ☐ Xác suất (PSA) + đường cong CEAC [CẦN]
- Nếu là **Phân tích tác động ngân sách (BIA)**: dùng ISPOR BIA GPP II 2014 RIÊNG — CHEERS 2022 KHÔNG bao BIA.
- Chuẩn báo cáo: CHEERS 2022 (CEA/CUA/CBA).
- → Cân nhắc mời agent `kinh-te-y-te` hỗ trợ chi tiết từng bước.
"""
    # qualitative
    return f"""### MÔ-ĐUN — {_SPECIALIST_MODULE_LABEL[module]}
> Phát hiện tín hiệu: đề tài có cấu phần định tính hoặc hỗn hợp (mixed-methods).

- Cách tiếp cận: ☐ Hiện tượng học  ☐ Lý thuyết nền (grounded theory)
  ☐ Phân tích nội dung/chủ đề  ☐ Nghiên cứu trường hợp [CẦN]
- Lấy mẫu có chủ đích + tiêu chí bão hòa dữ liệu: [CẦN]
- Bộ câu hỏi phỏng vấn/nhóm tiêu điểm: [CẦN soạn + thử nghiệm trước]
- Phương pháp mã hóa/phân tích: ☐ Thematic  ☐ Framework analysis [CẦN]
- Độ tin cậy (trustworthiness): credibility/transferability/dependability/
  confirmability [CẦN biện pháp cụ thể cho từng tiêu chí]
- Nếu HỖN HỢP (mixed-methods): thiết kế tích hợp ☐ Hội tụ
  ☐ Giải thích tuần tự  ☐ Khám phá tuần tự + điểm tích hợp [CẦN]
- Chuẩn báo cáo: COREQ (phỏng vấn/nhóm tiêu điểm) hoặc SRQR (tổng quát).
- → Cân nhắc mời agent `nghien-cuu-dinh-tinh` hỗ trợ chi tiết từng bước.
"""


def specialist_modules_block(modules: list[str]) -> str:
    """Ghép các mô-đun chuyên biệt được phát hiện thành 1 khối markdown.
    Trả về chuỗi RỖNG nếu không phát hiện tín hiệu nào (không thêm mục thừa)."""
    if not modules:
        return ""
    sections = "\n".join(_specialist_module_section(m) for m in modules)
    return f"""
---

## PHẦN 8 — MÔ-ĐUN CHUYÊN BIỆT (phát hiện tín hiệu — cộng thêm, KHÔNG thay đổi thiết kế chính ở §1)

> Đề tài có tín hiệu cần {len(modules)} năng lực chuyên biệt ngoài khung thiết kế/SAP chuẩn ở trên.
> Đây là bổ sung PHƯƠNG PHÁP LUẬN — không thay cho §1–§7, chạy song song.

{sections}"""


# THÊM 2026-07-21 (vòng lặp kiểm tra-hoàn thiện vòng 4, phát hiện CRITICAL):
# bác sĩ pin design_code qua study_meta.json bằng bí danh tự nhiên (vd "qual"
# thay vì "qualitative") — trước bản vá, giá trị THÔ này được ghi thẳng vào
# internal_code, khiến MỌI so khớp chuỗi chính xác rải khắp run_g2/g4/g5/g6/
# g7/g8/g10_auto.py (RISK_PROFILES, DESIGN_CHECKLIST_MAP, N_NOT_APPLICABLE_
# DESIGNS, _WRONG_METHOD_DESIGNS, _SURVIVAL_CAPABLE_DESIGNS...) đều KHÔNG
# khớp, rơi vào nhánh mặc định sai thiết kế — đúng lớp bug CRITICAL vừa vá
# cho design_code="qualitative" ở G10, chỉ khác input trigger.
#
# CỐ Ý KHÔNG dùng skill_standards.canonical_design_code()/DESIGN_CODE_ALIASES:
# bảng đó phục vụ vocabulary RIÊNG của reporting_standards_for()/
# DISPLAY_ITEM_BY_DESIGN (vd "sr_ma" -> "systematic_review") — áp trực tiếp
# ở đây sẽ làm HỎNG mọi so khớp `internal_code == "sr_ma"` rải khắp các file
# run_g*_auto.py (vốn dùng "sr_ma" LÀM canon, không phải "systematic_review").
# Bảng dưới đây ánh xạ RIÊNG về đúng 8 mã canon mà pipeline G2-G10 dùng làm
# internal_code: rct, cohort, case_control, cross_sectional, diagnostic,
# sr_ma, prediction, qualitative.
_PIN_DESIGN_ALIASES = {
    "qual": "qualitative",
    "rct_parallel": "rct",
    "rct_crossover": "rct",
    "randomized": "rct",
    "sr": "sr_ma",
    "systematic_review": "sr_ma",
    "meta_analysis": "sr_ma",
    "metaanalysis": "sr_ma",
    "case_control_study": "case_control",
    "cross_sectional_descriptive": "cross_sectional",
    "prevalence": "cross_sectional",
    "prognostic": "prediction",
    "prediction_model": "prediction",
    "diagnostic_accuracy": "diagnostic",
}


def _canonicalize_pinned_design_code(raw: str) -> str:
    """Chuẩn hoá bí danh design_code do bác sĩ pin về đúng 8 mã canon dùng
    làm internal_code xuyên suốt G2-G10 (xem chú thích _PIN_DESIGN_ALIASES)."""
    key = raw.strip().lower()
    return _PIN_DESIGN_ALIASES.get(key, key)


def _read_pinned_design(out_dir) -> str:
    """Đọc study_meta.json['design_code'] (hoặc gate_params.G1.design). '' nếu không có."""
    import json as _json
    from pathlib import Path as _Path
    p = _Path(out_dir) / "study_meta.json"
    if not p.exists():
        return ""
    try:
        meta = _json.loads(p.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return ""
    pin = meta.get("design_code") or (meta.get("gate_params", {}).get("G1", {}) or {}).get("design")
    return _canonicalize_pinned_design_code(str(pin)) if pin else ""


def _apply_design_pin(design: dict, pinned: str) -> dict:
    """Ghi đè thiết kế bằng giá trị bác sĩ pin; giữ nguyên các trường khác."""
    d = dict(design)
    d["internal_code"] = pinned
    d["primary"] = _DESIGN_LABEL.get(pinned, f"Thiết kế: {pinned}")
    try:
        import sys as _sys
        from pathlib import Path as _Path
        _sys.path.insert(0, str(_Path(__file__).resolve().parent))
        import skill_standards as _S
        d["reporting_standard"] = _S.reporting_standards_for(pinned)["primary"]
    except Exception:  # noqa: BLE001
        pass
    d["rationale"] = ("Thiết kế do BÁC SĨ pin trong study_meta.json (quyết định "
                      "thật, ưu tiên hơn suy luận tự động). " + str(design.get("rationale", "")))
    return d


# Bộ từ khóa khai báo thiết kế TƯỜNG MINH trong topic — DÙNG CHUNG giữa suy
# luận thiết kế (infer_study_design) và guardrail đối chiếu ngược
# (check_topic_design_consistency ở guardrail_check_g1), để 1 chỗ sửa không
# lệch pha với chỗ kia (đúng lớp bug case-control/harm đã xảy ra thật, sửa
# 2026-07-06 — 4/5 nhánh có keyword-detect, riêng "harm" ban đầu bị bỏ sót).
DESIGN_KEYWORD_HINTS = {
    "sr": ["tổng quan", "systematic review", "meta-analysis", "tong quan"],
    "diagnosis": ["chẩn đoán", "chan doan", "độ nhạy", "do nhay", "auc", "sensitivity"],
    # THÊM 2026-07-17 (round audit gate — tiếp nối hoàn thiện gate cho
    # "prediction"): TRƯỚC ĐÂY "prediction" (TRIPOD+AI) đã được nối xuyên suốt
    # G2-G9 (round trước) nhưng KHÔNG BAO GIỜ CHẠM TỚI ĐƯỢC từ phân loại tự
    # động — mọi đề tài "xây dựng mô hình tiên lượng" đều khớp từ khóa
    # "tiên lượng"/"prognosis" phía dưới và bị gán internal_code="cohort" (STROBE),
    # KHÔNG BAO GIỜ "prediction" (TRIPOD+AI). Cụm từ ở đây phải TƯỜNG MINH hơn
    # "tiên lượng" đơn lẻ (vốn cũng đúng cho câu hỏi tiên lượng 1 yếu tố nguy cơ
    # kiểu cohort/STROBE bình thường) — chỉ khớp khi đề tài NÊU RÕ Ý ĐỊNH XÂY
    # DỰNG/PHÁT TRIỂN MỘT MÔ HÌNH ĐA BIẾN, không phải mọi câu hỏi có chữ "tiên
    # lượng". Đặt TRƯỚC "prognosis" trong thứ tự kiểm tra bên dưới để thắng ưu
    # tiên khi cả 2 đều khớp (vd "mô hình tiên lượng" chứa cả "mô hình tiên
    # lượng" LẪN "tiên lượng").
    "prediction_model": [
        "mô hình tiên lượng", "mo hinh tien luong", "mô hình dự đoán", "mo hinh du doan",
        "mô hình dự báo", "mo hinh du bao", "xây dựng thang điểm", "xay dung thang diem",
        "phát triển thang điểm", "phat trien thang diem", "prediction model",
        "predictive model", "risk prediction model", "clinical prediction rule",
        "clinical prediction model", "nomogram", "risk calculator", "tripod",
    ],
    "prognosis": ["tiên lượng", "tien luong", "prognosis", "sống còn", "song con",
                  "tử vong", "tu vong"],
    # Chỉ khớp cụm từ TƯỜNG MINH khai báo thiết kế (không dùng "yếu tố nguy cơ"
    # đơn lẻ — cụm này quá chung, cũng xuất hiện ở nhiều đề tài cohort).
    "harm": ["bệnh-chứng", "bệnh chứng", "benh-chung", "benh chung",
             "case-control", "case control", "ca-chứng", "ca chứng",
             "nested case-control", "nested case control"],
    "descriptive": ["tỷ lệ", "ty le", "prevalence", "mô tả", "mo ta", "tần suất",
                    # Nghiên cứu dịch vụ y tế/khảo sát: hài lòng, khảo sát, thực
                    # trạng → cắt ngang mô tả (trước rơi vào nhánh evidence->cohort sai).
                    "hài lòng", "hai long", "satisfaction", "khảo sát", "khao sat",
                    "survey", "thực trạng", "thuc trang", "kiến thức thái độ",
                    "kap", "chất lượng dịch vụ", "chat luong dich vu"],
    # THÊM 2026-07-19 (audit vòng 3, D1 — NGHIÊM TRỌNG, cùng khuôn vá
    # "prediction_model" 2026-07-17): tái dùng ĐÚNG danh sách keyword định
    # tính ở SPECIALIST_MODULE_KEYWORDS["qualitative"] để 2 lớp phát hiện
    # (design chính + specialist module cộng thêm) nhất quán, một nguồn duy
    # nhất — sửa ở 1 nơi tự lan sang cả 2. Đặt TRƯỚC "descriptive" trong thứ
    # tự elif của infer_study_design() vì không đụng độ (không cụm nào ở đây
    # trùng "hài lòng/khảo sát/thực trạng/tỷ lệ" của descriptive).
    "qualitative": SPECIALIST_MODULE_KEYWORDS["qualitative"],
}

# question_type (từ khóa phát hiện) → internal_code KỲ VỌNG tương ứng, dùng
# cho guardrail đối chiếu ngược (không dùng để suy luận — suy luận vẫn qua
# infer_study_design, có logic chọn giữa case_control/cohort tùy ngữ cảnh).
_KEYWORD_TO_EXPECTED_INTERNAL = {
    "sr": "sr_ma",
    "diagnosis": "diagnostic",
    "prediction_model": "prediction",
    "prognosis": "cohort",
    "harm": "case_control",
    "descriptive": "cross_sectional",
    "qualitative": "qualitative",
}


def check_topic_design_consistency(topic: str, chosen_internal_code: str) -> list:
    """
    Đối chiếu từ khóa thiết kế TƯỜNG MINH trong tên đề tài với design_code đã
    chọn CUỐI CÙNG (sau mọi override/pin) — bắt các ca thiết kế bị suy nhầm dù
    topic đã khai rõ, ngay cả khi nguyên nhân không phải thiếu keyword-detect
    (vd bác sĩ pin sai tay, hoặc future bug tương tự). Trả về list cảnh báo
    (KHÔNG phải lỗi cứng — bác sĩ có thể có lý do chính đáng chọn khác, guardrail
    chỉ nhắc xác nhận, không tự chặn). Thêm 2026-07-06 sau kiểm định đối kháng
    vòng 2 (khuyến nghị độc lập từ 2 cụm kiểm toán khác nhau).
    """
    topic_lower = topic.lower()
    warns = []
    # SỬA 2026-07-17: "prediction_model" (mô hình tiên lượng đa biến) LUÔN chứa
    # cả từ khóa "prognosis" đơn lẻ (vd "mô hình tiên lượng" khớp cả "tiên
    # lượng") — nếu không loại trừ, mọi đề tài "prediction" hợp lệ vẫn bị cảnh
    # báo giả "topic gợi ý cohort" (từ nhánh prognosis) dù đã chọn ĐÚNG. Khi
    # prediction_model khớp, bỏ qua kiểm tra prognosis (bị bao hàm/thay thế).
    _skip_qtypes = {"prognosis"} if _kw_in(DESIGN_KEYWORD_HINTS["prediction_model"], topic_lower) else set()
    for qtype, kws in DESIGN_KEYWORD_HINTS.items():
        if qtype in _skip_qtypes:
            continue
        if _kw_in(kws, topic_lower):
            expected = _KEYWORD_TO_EXPECTED_INTERNAL[qtype]
            if chosen_internal_code != expected:
                warns.append(
                    f"R6 ⚠️ Tên đề tài có từ khóa gợi ý thiết kế '{expected}' nhưng "
                    f"design_code đã chọn là '{chosen_internal_code}' — bác sĩ xác nhận "
                    "đây đúng ý định, hay cần pin lại qua study_meta.json['design_code']."
                )
    return warns


def infer_study_design(question_type: str, gaps: dict, topic: str) -> dict:
    """
    Suy luận loại thiết kế từ câu hỏi + bức tranh evidence từ G0.
    Trả về: dict với primary, alternatives, rationale, internal_code, reporting
    """
    n_sr  = gaps.get("n_sr", 0)
    n_rct = gaps.get("n_rct", 0)
    topic_lower = topic.lower()
    # THÊM 2026-07-08: nhánh bão hòa RCT+SR dưới đây gán internal_code="cohort"
    # làm PLACEHOLDER TẠM (bác sĩ CHƯA xác nhận khoảng trống thật) — nhưng
    # run_g3_auto.py vẫn đọc thẳng "cohort" này và tính N THẬT, không có cờ
    # nào phân biệt với "cohort" đã bác sĩ xác nhận thật. Cờ `ambiguous` lan
    # xuống G3/G10 để buộc cảnh báo NGAY cạnh giá trị N (khoảng trống liêm
    # chính phát hiện qua kiểm định đối kháng, 2026-07-08).
    ambiguous = False

    # ── Phát hiện từ khóa thiết kế tường minh trong topic ──
    # SỬA 2026-07-17: kiểm "prediction_model" TRƯỚC "prognosis" — cụm như "mô
    # hình tiên lượng" khớp CẢ HAI, nhưng đây là đề tài xây mô hình đa biến
    # (TRIPOD+AI), không phải câu hỏi tiên lượng 1 yếu tố nguy cơ (cohort/STROBE
    # thường). Nếu để "prognosis" thắng trước (thứ tự cũ), mọi đề tài prediction
    # model đều bị phân loại nhầm thành "cohort" — không bao giờ chạm được vào
    # nhánh TRIPOD+AI đã nối xuyên G2-G9 (xem infer_study_design elif dưới).
    if _kw_in(DESIGN_KEYWORD_HINTS["sr"], topic_lower):
        question_type = "sr"
    # THÊM 2026-07-19 (audit vòng 3, D1 — NGHIÊM TRỌNG): kiểm "qualitative"
    # NGAY SAU "sr" — trước bản vá này, đề tài định tính rơi thẳng vào nhánh
    # else "descriptive" hoặc mặc định "treatment"→"rct", SAI phương pháp
    # luận (không power/effect size). Đặt SỚM (trước diagnosis/prognosis) vì
    # marker "trải nghiệm/ý nghĩa/rào cản" là dấu hiệu PARADIGM/PHƯƠNG PHÁP
    # LUẬN — đặc hiệu hơn và phải THẮNG marker DOMAIN/TOPIC như "chẩn đoán"/
    # "tiên lượng" (vd "Ý nghĩa của chẩn đoán ung thư..." là câu hỏi định
    # tính dù chứa chữ "chẩn đoán" — đã xác nhận qua ca thật khi kiểm chứng
    # bản vá, "diagnosis" từng nuốt mất câu này khi đặt "qualitative" sau).
    elif _kw_in(DESIGN_KEYWORD_HINTS["qualitative"], topic_lower):
        question_type = "qualitative"
    elif _kw_in(DESIGN_KEYWORD_HINTS["diagnosis"], topic_lower):
        question_type = "diagnosis"
    elif _kw_in(DESIGN_KEYWORD_HINTS["prediction_model"], topic_lower):
        question_type = "prediction_model"
    elif _kw_in(DESIGN_KEYWORD_HINTS["prognosis"], topic_lower):
        question_type = "prognosis"
    elif _kw_in(DESIGN_KEYWORD_HINTS["harm"], topic_lower):
        question_type = "harm"
    elif _kw_in(DESIGN_KEYWORD_HINTS["descriptive"], topic_lower):
        question_type = "descriptive"

    if question_type == "treatment":
        if n_rct == 0 and n_sr == 0:
            primary = "RCT Song song (Randomized Controlled Trial)"
            internal = "rct"
            alt1 = "Cohort tiến cứu (nếu RCT không khả thi về đạo đức/nguồn lực)"
            alt2 = "Pilot study / Feasibility trial (nếu chưa có dữ liệu nền)"
            rationale = ("Không có RCT nào trên topic này → khoảng trống lớn. "
                         "RCT song song cung cấp bằng chứng nhân quả mạnh nhất "
                         "(Level I evidence). Ngẫu nhiên hóa kiểm soát confounders đã biết và chưa biết.")
        elif n_rct >= 2 and n_sr == 0:
            primary = "Systematic Review / Meta-analysis (tổng hợp các RCT hiện có)"
            internal = "sr_ma"
            alt1 = "RCT mới với quần thể đặc thù (Việt Nam/châu Á/nhóm chưa được nghiên cứu)"
            alt2 = "Individual Patient Data (IPD) meta-analysis"
            rationale = (f"Có {n_rct} RCT nhưng chưa có SR/MA → cơ hội tổng hợp định lượng. "
                         "SR/MA cung cấp ước lượng pooled effect chính xác hơn mỗi RCT đơn lẻ.")
        elif n_sr >= 1 and n_rct >= 3:
            # SỬA: trước đây bất kỳ n_sr>=1 đều bị ép ra "Cohort" làm primary,
            # kể cả khi chủ đề đã bão hòa RCT (vd statin dự phòng tim mạch có
            # 15 RCT + 15 SR) — một quyết định sai vì lĩnh vực đã có bằng chứng
            # nhân quả mạnh, không cần thêm cohort quan sát. Khi CẢ n_sr>=1 VÀ
            # n_rct>=3 (lĩnh vực bão hòa cả RCT lẫn tổng hợp), không tự chọn
            # 1 thiết kế duy nhất — liệt kê 3 khả năng theo loại khoảng trống
            # và buộc bác sĩ xác nhận khoảng trống thật trước khi khóa thiết kế.
            gaps_text = " ".join(str(g) for g in gaps.get("research_gaps", [])).lower()
            population_specific = any(
                k in gaps_text for k in
                ["việt nam", "viet nam", "châu á", "chau a", "asian", "vietnamese",
                 "quần thể đặc thù", "dân tộc", "khu vực"]
            )
            primary = ("⚠️ CẦN BÁC SĨ XÁC NHẬN KHOẢNG TRỐNG TRƯỚC KHI CHỌN THIẾT KẾ "
                       "(lĩnh vực đã bão hòa cả RCT lẫn SR/MA)")
            internal = "cohort"  # placeholder tạm, KHÔNG dùng để tính cỡ mẫu/CRF trước khi bác sĩ xác nhận
            ambiguous = True
            alt1 = ("Nếu khoảng trống là QUẦN THỂ ĐẶC THÙ (VN/châu Á/dân tộc — "
                    f"{'phát hiện dấu hiệu này trong ghi chú G0' if population_specific else 'CHƯA thấy dấu hiệu này trong ghi chú G0, cần bác sĩ xác nhận'}"
                    "): Cohort tiến cứu quần thể đặc thù (pragmatic)")
            alt2 = ("Nếu khoảng trống là SR/MA CŨ hoặc CHƯA cập nhật RCT mới nhất: "
                    "Systematic Review/Meta-analysis cập nhật (updated SR/MA)")
            rationale = (
                f"Chủ đề có {n_sr} SR/MA VÀ {n_rct} RCT — bằng chứng nhân quả (Level I) đã "
                "khá đầy đủ. KHÔNG tự động chọn Cohort chỉ vì có SR/MA, vì lĩnh vực bão hòa "
                "RCT thường không cần thêm quan sát mà cần: (1) SR/MA cập nhật nếu bằng chứng "
                "cũ, (2) RCT nhắm đúng phân nhóm/khoảng trống cụ thể chưa được nghiên cứu, "
                "hoặc (3) Cohort/pragmatic CHỈ khi khoảng trống thật sự là external validity "
                "ở quần thể đặc thù (không phải hiệu quả điều trị nói chung). "
                f"{'G0 gợi ý khoảng trống quần thể đặc thù — cohort có thể phù hợp.' if population_specific else 'G0 KHÔNG nêu rõ khoảng trống quần thể đặc thù — bác sĩ cần xác nhận trước khi chọn.'} "
                "[CẦN BÁC SĨ ĐỌC LẠI research_gaps G0 VÀ CHỌN 1 TRONG 3 HƯỚNG TRÊN]"
            )
        elif n_sr >= 1:
            primary = "Cohort tiến cứu (quần thể đặc thù / pragmatic)"
            internal = "cohort"
            alt1 = "Nghiên cứu phân tích dưới nhóm (subgroup) từ RCT/cohort đã có"
            alt2 = "Nested case-control (nếu kết cục hiếm)"
            rationale = (f"Chủ đề đã có {n_sr} SR/MA nhưng ít RCT gốc ({n_rct}) → bằng chứng "
                         "nhân quả còn mỏng, cần biện minh rõ tính mới. Cohort tiến cứu tại "
                         "Việt Nam/quần thể đặc thù có thể lấp khoảng trống về tính ngoại suy "
                         "(external validity) của evidence hiện có.")
        else:
            primary = "RCT Song song hoặc Cohort tiến cứu"
            internal = "rct"
            alt1 = "Pilot/Feasibility study"
            alt2 = "Registry study"
            rationale = "Cần xem xét khả thi (F trong FINER) trước khi chọn thiết kế cuối."

    elif question_type == "sr":
        primary = "Systematic Review / Meta-analysis"
        internal = "sr_ma"
        alt1 = "Scoping Review (nếu câu hỏi rộng, exploratory)"
        alt2 = "Rapid Review (nếu deadline cấp thiết)"
        rationale = "Câu hỏi yêu cầu tổng hợp toàn bộ bằng chứng hiện có theo chuẩn PRISMA."

    elif question_type == "diagnosis":
        primary = "Nghiên cứu Cắt ngang (Độ chính xác chẩn đoán)"
        internal = "diagnostic"
        alt1 = "Cohort tiến cứu (nếu cần theo dõi tiến triển bệnh)"
        alt2 = "RCT chẩn đoán (nếu so sánh chiến lược kiểm tra)"
        rationale = ("Câu hỏi chẩn đoán: cần so index test với reference standard. "
                     "Cắt ngang với blinded verification là thiết kế chuẩn. Báo cáo: STARD 2015.")

    elif question_type == "prediction_model":
        # THÊM 2026-07-17 (round audit gate — tiếp nối hoàn thiện gate cho
        # "prediction"): tách khỏi nhánh "prognosis" phía dưới — câu hỏi XÂY
        # DỰNG/PHÁT TRIỂN một mô hình tiên lượng ĐA BIẾN (dùng để dự đoán nguy
        # cơ/kết cục cho từng cá nhân) khác về bản chất với câu hỏi tiên lượng
        # ĐƠN YẾU TỐ (vd "hút thuốc có tiên lượng tử vong không" — vẫn là
        # cohort/STROBE bình thường, ở nhánh "prognosis"). Trước khi có nhánh
        # này, MỌI đề tài prediction model đều rơi vào "prognosis" → internal=
        # "cohort" → không bao giờ chạm được nhánh TRIPOD+AI đã nối xuyên G2-G9.
        primary = "Nghiên cứu Phát triển/Đánh giá Mô hình Tiên lượng (Prediction Model)"
        internal = "prediction"
        alt1 = "Cohort tiến cứu đơn thuần (nếu chỉ khảo sát 1-2 yếu tố nguy cơ, không xây mô hình đa biến)"
        alt2 = "External validation study (nếu mô hình đã có sẵn, chỉ kiểm định lại ở quần thể mới)"
        rationale = ("Câu hỏi xây dựng/đánh giá mô hình dự đoán đa biến: cần phân biệt rõ "
                     "giai đoạn PHÁT TRIỂN (development) và ĐÁNH GIÁ (validation nội bộ/ngoại "
                     "bộ). Chuẩn báo cáo: TRIPOD+AI 2024 (Collins GS et al., BMJ "
                     "2024;385:e078378) — thay thế hoàn toàn TRIPOD 2015, áp dụng cho cả mô "
                     "hình hồi quy lẫn AI/ML.")

    elif question_type == "prognosis":
        primary = "Cohort Tiến cứu (Prospective Cohort)"
        internal = "cohort"
        alt1 = "Cohort Hồi cứu (nếu có dữ liệu hồ sơ bệnh án đủ chất lượng)"
        alt2 = "Registry / Database study"
        rationale = ("Câu hỏi tiên lượng: cần theo dõi kết cục theo thời gian. "
                     "Cohort tiến cứu hạn chế recall bias; hồi cứu nhanh hơn nhưng "
                     "phụ thuộc chất lượng hồ sơ.")

    elif question_type == "harm":
        primary = "Case-Control Study"
        internal = "case_control"
        alt1 = "Cohort hồi cứu (nếu phơi nhiễm phổ biến và hồ sơ đầy đủ)"
        alt2 = "Self-controlled case series (SCCS) (nếu phơi nhiễm nhất thời)"
        rationale = ("Câu hỏi tác hại: kết cục thường hiếm → case-control hiệu quả. "
                     "Nếu phơi nhiễm phổ biến và có hồ sơ tốt → cohort hồi cứu.")

    elif question_type == "qualitative":
        # THÊM 2026-07-19 (audit vòng 3, D1 — NGHIÊM TRỌNG, cùng khuôn vá
        # "prediction_model" 2026-07-17): trước bản vá này, KHÔNG nhánh nào ở
        # đây từng gán internal="qualitative" — infer_study_design() luôn trả
        # về rct/cohort/cross_sectional cho MỌI đề tài, kể cả định tính thuần
        # túy. Hệ quả downstream: G3 tính cỡ mẫu bằng công thức power/effect
        # size (SAI phương pháp luận — định tính dùng bão hòa dữ liệu, không
        # phải power); G4 hard-block SAP khi N=0; G7 gán checklist STROBE/
        # CONSORT thay vì COREQ/SRQR.
        primary = "Nghiên cứu Định tính (Qualitative Research)"
        internal = "qualitative"
        alt1 = "Mixed-methods (nếu cần bổ sung cấu phần định lượng — thiết kế tích hợp hội tụ/giải thích tuần tự/khám phá tuần tự)"
        alt2 = "Nghiên cứu trường hợp (case study) nếu câu hỏi tập trung MỘT đơn vị/bối cảnh cụ thể"
        rationale = ("Câu hỏi khai thác TRẢI NGHIỆM/Ý NGHĨA/RÀO CẢN (paradigm định tính, không "
                     "phải 'bao nhiêu/liên quan' của định lượng): cần cách tiếp cận (hiện tượng "
                     "học/grounded theory/phân tích chủ đề) + lấy mẫu có chủ đích + quy tắc BÃO "
                     "HÒA DỮ LIỆU (không ấn định cỡ mẫu cứng như power/effect size). Chuyển "
                     "`nghien-cuu-dinh-tinh` để thiết kế chi tiết. Chuẩn báo cáo: COREQ (phỏng "
                     "vấn/nhóm tiêu điểm) / SRQR (định tính nói chung).")

    else:  # descriptive
        primary = "Nghiên cứu Cắt ngang Mô tả (Cross-sectional / Prevalence)"
        internal = "cross_sectional"
        alt1 = "Khảo sát dựa cộng đồng (nếu muốn ngoại suy toàn dân số)"
        alt2 = "Registry / Audit lâm sàng (nếu muốn dữ liệu thực hành)"
        rationale = ("Câu hỏi mô tả (tỷ lệ/đặc điểm) → cắt ngang là tiêu chuẩn. "
                     "Không suy nhân quả từ thiết kế này.")

    reporting = REPORTING_STANDARDS.get(
        internal,
        REPORTING_STANDARDS.get(
            "cohort" if "cohort" in internal else "cross_sectional", "STROBE"
        )
    )

    return {
        "primary": primary,
        "internal_code": internal,
        "alternative_1": alt1,
        "alternative_2": alt2,
        "rationale": rationale,
        "reporting_standard": reporting,
        "bias_controls": BIAS_CONTROLS.get(internal, BIAS_CONTROLS["cohort"]),
        "ambiguous": ambiguous,
    }


# ════════════════════════════════════════════════════════════════════════════
# 3. TRÍCH XUẤT EFFECT SIZE ƯỚC LƯỢNG TỪ ABSTRACTS PUBMED THẬT
# ════════════════════════════════════════════════════════════════════════════

# SỬA: pattern cũ bắt buộc dấu ( hoặc [ ngay sau điểm ước lượng trước khi
# "95% CI" xuất hiện — nhưng abstract thật thường viết dạng chấm phẩy/phẩy
# ("HR = 0.77; 95% CI: 0.61–0.98") không có ngoặc mở ngay sau, nên regex cũ
# KHÔNG BAO GIỜ khớp và luôn rơi vào fallback thô "NN% reduction" (không phân
# biệt được ARR tuyệt đối hay RR tương đối, và khớp bừa trên bất kỳ số nào).
# Regex mới chấp nhận mọi dấu phân cách thường gặp: ( [ ; , : hoặc khoảng trắng.
_ES_PATTERNS_LABELED = [
    (r'OR[=\s]+(\d+\.?\d*)\s*[\(\[;,:]*\s*95%\s*CI[:\s]*(\d+\.?\d*)\s*(?:[\-–]|to)\s*(\d+\.?\d*)', "OR"),
    (r'HR[=\s]+(\d+\.?\d*)\s*[\(\[;,:]*\s*95%\s*CI[:\s]*(\d+\.?\d*)\s*(?:[\-–]|to)\s*(\d+\.?\d*)', "HR"),
    (r'RR[=\s]+(\d+\.?\d*)\s*[\(\[;,:]*\s*95%\s*CI[:\s]*(\d+\.?\d*)\s*(?:[\-–]|to)\s*(\d+\.?\d*)', "RR"),
    (r'hazard ratio[=\s]+(\d+\.?\d*)\s*[\(\[;,:]*\s*95%\s*CI[:\s]*(\d+\.?\d*)\s*(?:[\-–]|to)\s*(\d+\.?\d*)', "HR"),
    (r'odds ratio[=\s]+(\d+\.?\d*)\s*[\(\[;,:]*\s*95%\s*CI[:\s]*(\d+\.?\d*)\s*(?:[\-–]|to)\s*(\d+\.?\d*)', "OR"),
    (r'mean difference[=\s]+([\-]?\d+\.?\d*)\s*[\(\[;,:]*\s*95%\s*CI[:\s]*([\-]?\d+\.?\d*)\s*(?:[\-–]|to)\s*([\-]?\d+\.?\d*)', "MD"),
]
# Fallback THÔ — không có CI đi kèm, không phân biệt được ARR/RR% → luôn gắn
# nhãn "crude" để downstream (G3) biết cần cảnh báo, KHÔNG ưu tiên bằng loại
# đã gắn nhãn HR/OR/RR/MD ở trên.
_ES_PATTERNS_CRUDE = [
    (r'reduction of (\d+\.?\d*)%', "ARR%"),
    (r'(\d+\.?\d*)% reduction', "ARR%"),
    (r'mean difference[=\s]+([\-]?\d+\.?\d*)', "MD"),
    (r'MD[=\s]+([\-]?\d+\.?\d*)', "MD"),
]
# Biên hợp lý theo loại — HR/OR/RR ngoài khoảng này gần như chắc chắn là
# regex bắt nhầm số khác trong câu (vd cỡ mẫu, p-value), không phải effect size
_SANITY_BOUNDS = {"HR": (0.05, 20), "OR": (0.02, 50), "RR": (0.05, 20),
                  "MD": (-1000, 1000), "ARR%": (0.1, 100)}


def extract_effect_sizes(articles: list) -> list[dict]:
    """
    Trích xuất effect size ước lượng từ abstracts PubMed thật.
    Ưu tiên pattern CÓ NHÃN + CÓ 95%CI (đáng tin hơn) trước pattern thô;
    mỗi kết quả gắn "quality": "labeled" hoặc "crude" để downstream
    (hiển thị G1, tính cỡ mẫu G3) biết mà cảnh báo bác sĩ kiểm tra kỹ hơn
    với loại "crude".
    """
    found = []
    for r in articles:
        if not r.abstract:
            continue
        per_article = []
        for pattern, es_type in _ES_PATTERNS_LABELED:
            matches = re.findall(pattern, r.abstract, re.IGNORECASE)
            for m in matches[:2]:
                if not (isinstance(m, tuple) and len(m) >= 3):
                    continue
                try:
                    val = float(m[0])
                    lo, hi = _SANITY_BOUNDS.get(es_type, (0.01, 100))
                    if lo <= val <= hi:
                        per_article.append({
                            "type": es_type, "value": val,
                            "ci": f"95%CI: {m[1]}–{m[2]}",
                            "pmid": r.pmid, "title": (r.title or "")[:80],
                            "year": r.publication_date or "?",
                            "quality": "labeled",
                        })
                except (ValueError, TypeError):
                    pass
        # Chỉ dùng fallback thô nếu abstract này KHÔNG có pattern có nhãn nào khớp
        if not per_article:
            for pattern, es_type in _ES_PATTERNS_CRUDE:
                matches = re.findall(pattern, r.abstract, re.IGNORECASE)
                for m in matches[:1]:
                    es_val = m if isinstance(m, str) else (m[0] if m else None)
                    if es_val is None:
                        continue
                    try:
                        val = float(es_val)
                        lo, hi = _SANITY_BOUNDS.get(es_type, (0.01, 100))
                        if lo <= val <= hi:
                            per_article.append({
                                "type": es_type, "value": val, "ci": "",
                                "pmid": r.pmid, "title": (r.title or "")[:80],
                                "year": r.publication_date or "?",
                                "quality": "crude",
                            })
                    except (ValueError, TypeError):
                        pass
        found.extend(per_article)
        # SỬA: break sớm theo len(found)>=10 xảy ra TRƯỚC sort bên dưới — nếu
        # 10 kết quả đầu tiên đều "crude" (vd 5 bài × 2 match/bài), các bài
        # sau đó (có thể chứa effect "labeled" đáng tin hơn) KHÔNG BAO GIỜ
        # được trích xuất, vì vòng lặp đã break trước khi kịp đọc chúng.
        # `articles` vốn đã giới hạn ~10 bài (search_for_effect_sizes
        # max_results=10) nên xử lý hết toàn bộ rồi mới cắt bớt không tốn
        # kém — bỏ break sớm, sort trước, cắt sau.
    found.sort(key=lambda x: 0 if x["quality"] == "labeled" else 1)
    return found[:10]


def search_for_effect_sizes(topic: str, study_name: str, max_results: int = 10) -> list[dict]:
    """Tìm kiếm PubMed để lấy ước lượng effect size từ SR/RCT abstracts."""
    from app.sources.pubmed import PubMedClient
    client = PubMedClient()
    q = f"{topic} AND (systematic review[pt] OR meta-analysis[pt] OR randomized controlled trial[pt])"
    print(f"  🔍 Tìm effect size từ abstracts ({q[:70]}...)...")
    try:
        records = client.search(q, max_results=max_results)
        effects = extract_effect_sizes(records)
        time.sleep(0.4)
        return effects
    except Exception as e:
        print(f"     ⚠ Lỗi tìm effect size: {e}")
        return []


# ════════════════════════════════════════════════════════════════════════════
# 4. SINH ARTIFACT G1 — THIẾT KẾ VÀ SAP SKELETON
# ════════════════════════════════════════════════════════════════════════════

def _bias_table(bias_list: list) -> str:
    rows = []
    for bias, control in bias_list:
        rows.append(f"| {bias} | {control} |")
    return "\n".join(rows)


def _effect_size_section(effects: list) -> str:
    if not effects:
        return "  → Không trích xuất được effect size từ abstracts. [CẦN TỰ ĐỌC Y VĂN]\n"
    lines = ["  (Tự động trích từ abstracts PubMed — cần bác sĩ kiểm chứng toàn văn)\n"]
    for e in effects[:8]:
        ci = f" ({e['ci']})" if e.get("ci") else ""
        if e.get("quality") == "crude":
            flag = "  ⚠️ [THÔ — không có 95%CI đi kèm, có thể lẫn ARR/RR, PHẢI đọc toàn văn xác nhận]"
        else:
            flag = ""
        lines.append(f"  • {e['type']} = {e['value']}{ci} — PMID:{e['pmid']} ({e['year']}) {e['title'][:60]}{flag}")
    return "\n".join(lines) + "\n"


def generate_g1_artifact(topic: str, study_name: str, question_type: str,
                          design: dict, effects: list, g0_gaps: dict,
                          run_date: str) -> str:
    bias_table = _bias_table(design["bias_controls"])
    es_section = _effect_size_section(effects)
    internal = design["internal_code"]
    specialist_modules = detect_specialist_modules(topic)
    specialist_block = specialist_modules_block(specialist_modules)

    # Chọn SAP template theo thiết kế
    if internal == "rct":
        sap_analysis_note = ("Phân tích chính: ITT (treatment-policy estimand)\n"
                             "Kết cục liên tục: ANCOVA (post - baseline; covariates: baseline + stratification)\n"
                             "Kết cục nhị phân: logistic / Poisson + robust SE → RR (95%CI)\n"
                             "Thời gian đến sự kiện: log-rank + Cox → HR (95%CI)")
        quanso_note = "ITT / Per-Protocol / Completers (ITT là chính)"
        epv_note = "N/A (RCT — cỡ mẫu từ power calculation)"
    elif internal in ("cohort", "case_control"):
        sap_analysis_note = ("Phân tích chính: Cox regression → HR (95%CI) + Kaplan-Meier\n"
                             "Hoặc: Logistic regression → OR (95%CI) nếu kết cục nhị phân\n"
                             "Kiểm giả định PH: Schoenfeld residuals")
        quanso_note = "Toàn bộ người đủ tiêu chí (Complete case) / Sensitivity: MI"
        epv_note = "EPV ≥ 10: cần N_events ≥ 10 × số biến đa biến"
    elif internal == "cross_sectional":
        sap_analysis_note = ("Phân tích chính: Logistic regression → OR (95%CI)\n"
                             "Hoặc: Linear regression → β (95%CI) nếu kết cục liên tục\n"
                             "VIF < 5 (kiểm đa cộng tuyến); Hosmer-Lemeshow (logistic)")
        quanso_note = "Toàn bộ người đủ tiêu chí (Complete case)"
        epv_note = "EPV ≥ 10 cho mô hình đa biến"
    elif internal == "diagnostic":
        sap_analysis_note = ("Phân tích chính: 2×2 table → Se, Sp, PPV, NPV, LR+, LR−\n"
                             "ROC curve → AUC (95%CI bootstrap)\n"
                             "Calibration: Hosmer-Lemeshow; DCA (decision curve analysis)")
        quanso_note = "Toàn bộ người tham gia (không có nhóm so sánh can thiệp)"
        epv_note = "EPP ≥ 10: cần N_events ≥ 10 × số predictor"
    else:  # sr_ma
        sap_analysis_note = ("Phân tích gộp: random-effects (DerSimonian-Laird) nếu I² > 25%\n"
                             "Fixed-effects nếu I² < 25% và đồng nhất lâm sàng\n"
                             "Publication bias: funnel plot + Egger test (nếu N ≥ 10 nghiên cứu)")
        quanso_note = "Tất cả nghiên cứu đủ tiêu chí nhận vào"
        epv_note = "N/A (SR/MA)"

    # Gợi ý R packages theo thiết kế + seed tự sinh từ ngày chạy — dữ liệu
    # (internal_code, run_date) đã có sẵn trong tay nhưng trước đây để
    # trắng hoàn toàn thành [CẦN ẤN ĐỊNH]/[CẦN]. Đây là gợi ý kỹ thuật
    # thuần túy (không phải quyết định lâm sàng) nên tự động hóa được —
    # bác sĩ vẫn cần XÁC NHẬN, không phải tự nghĩ từ đầu.
    _PACKAGE_SUGGESTIONS = {
        "rct":            "survival, geepack, tableone",
        "cohort":         "survival, tableone, mice",
        "case_control":   "survival, tableone, mice",
        "cross_sectional": "tableone, car",
        "diagnostic":     "pROC, tableone, rmda",
        "sr_ma":          "meta, metafor",
    }
    suggested_packages = _PACKAGE_SUGGESTIONS.get(internal, "tableone")
    suggested_seed = run_date[:10].replace("-", "")

    # Estimand block (chỉ cho RCT/can thiệp)
    estimand_block = ""
    if internal == "rct":
        estimand_block = """
### ESTIMAND ICH E9(R1) — Bắt buộc cho RCT

```
Dân số: [CẦN BÁC SĨ XÁC NHẬN — từ PICO P]
Biến kết cục: [CẦN — từ PICO O, kết cục chính]
Biến cố xen ngang: ☐ Dừng điều trị ☐ Điều trị thêm ☐ Tử vong cạnh tranh
  Chiến lược: ☐ Treatment-policy  ☐ Composite  ☐ While-on-treatment
              ☐ Hypothetical  ☐ Principal-stratum
Thước đo tổng hợp: ☐ RR  ☐ OR  ☐ RD  ☐ HR  ☐ MD
Quần thể phân tích chính: ☐ ITT (treatment-policy)  ☐ Per-protocol
```
"""

    artifact = f"""# A2 — THIẾT KẾ NGHIÊN CỨU & SAP SKELETON | {study_name}
> Tạo tự động: {run_date} | Rule-based + PubMed effect size thật
> [BẢN NHÁP TỰ ĐỘNG] — Bác sĩ xác nhận thiết kế chọn + điền [CẦN...] trước khi tiến G2/G4
> Cần bác sĩ kiểm chứng.

---

## PHẦN 1 — BẢNG THIẾT KẾ ỨNG VIÊN

| Thiết kế | Phù hợp câu hỏi | Kiểm soát sai lệch | Khả thi | Lực | Chọn/Loại |
|---|---|---|---|---|---|
| **{design["primary"]}** | ✅ Phù hợp nhất ({QUESTION_TYPES.get(question_type, question_type)}) | Cao (xem §2) | [CẦN BÁC SĨ] | [CẦN cỡ mẫu] | **→ ƯU TIÊN** |
| {design["alternative_1"]} | Phù hợp thay thế | Trung bình | [CẦN] | [CẦN] | Phương án 2 |
| {design["alternative_2"]} | Phù hợp trong điều kiện đặc biệt | Thấp hơn | [CẦN] | [CẦN] | Phương án 3 |

**Lý do chọn ưu tiên `{design["primary"]}`:**
{design["rationale"]}

**Chuẩn báo cáo:** {design["reporting_standard"]}

---

## PHẦN 2 — KIỂM SOÁT 7 SAI LỆCH CHÍNH

| Sai lệch | Biện pháp kiểm soát cho `{design["primary"]}` |
|---|---|
{bias_table}

---
{estimand_block}
## PHẦN 3 — EFFECT SIZE ƯỚC LƯỢNG (từ PubMed thật — dùng tính cỡ mẫu G3)

> **Quan trọng:** Đây là ước lượng TỰ ĐỘNG từ abstracts.
> Bác sĩ PHẢI đọc toàn văn để xác minh trước khi dùng tính cỡ mẫu.
> Nếu không có nghiên cứu phù hợp → dùng pilot data hoặc MCID lâm sàng.

{es_section}
**Evidence landscape từ G0:**
- SR/MA hiện có: {g0_gaps.get("n_sr", "N/A")}
- RCT hiện có: {g0_gaps.get("n_rct", "N/A")}
- Năm gần nhất: {g0_gaps.get("most_recent_year", "?")}
- Mức độ evidence: {g0_gaps.get("evidence_level", "?")}

---

## PHẦN 4 — KHỐI THIẾT KẾ (dán vào §Phương pháp của Đề cương)

```
═══════════════════════════════════════════════════════════════
KHỐI THIẾT KẾ — {study_name}
Loại thiết kế: {design["primary"]}
Bố trí: ☐ Song song  ☐ Bắt chéo  ☐ Factorial  ☐ Thích nghi
Ngẫu nhiên hóa: ☐ Không  ☐ Đơn giản  ☐ Phân tầng: [theo ___]  ☐ Cụm
Làm mù: ☐ Mở  ☐ Đơn mù  ☐ Đôi mù  ☐ Tam mù
Estimand chính (can thiệp): [CẦN XÁC NHẬN — xem §Estimand bên trên]
Kiểm soát biến nhiễu chính: [từ §2 Bias Control]
Thời gian theo dõi: [CẦN BÁC SĨ XÁC NHẬN]
Cỡ mẫu dự kiến: [CẦN → chạy run_g3_auto.py sau khi xác nhận effect size]
Giả định effect size (nguồn): [CẦN — xem §3 hoặc pilot data]
Chuẩn báo cáo: {design["reporting_standard"]}
═══════════════════════════════════════════════════════════════
```

---

## PHẦN 5 — SAP SKELETON (12 MỤC — bác sĩ điền [CẦN...])

> SAP phải hoàn chỉnh và KHÓA TRƯỚC KHI XEM DỮ LIỆU THẬT (Cổng G4).
> [CẦN...] = cần bác sĩ điền; mọi mục này KHÔNG thay đổi sau khi khóa.

### SAP §1 — Quần thể phân tích
```
{quanso_note}
Tiêu chí chọn vào: [CẦN — từ PICO P]
Tiêu chí loại trừ: [CẦN BÁC SĨ ẤN ĐỊNH]
Quần thể CHÍNH dùng báo cáo: [CẦN XÁC NHẬN]
```

### SAP §2 — Biến kết cục (định nghĩa vận hành)
```
KẾT CỤC CHÍNH (chỉ 1):
  Tên: [CẦN — từ PICO O, kết cục chính BÁC SĨ ĐÃ ẤN ĐỊNH ở G0]
  Định nghĩa vận hành: [CẦN — rõ ràng, đo được, cụ thể]
  Đơn vị đo: [CẦN]
  Thời điểm đo: [CẦN]
  Thước đo: ☐ Liên tục  ☐ Nhị phân  ☐ Thứ tự  ☐ Thời gian đến sự kiện

KẾT CỤC PHỤ (tối đa 3–5):
  1. ___ | thời điểm: ___
  2. ___ | thời điểm: ___
  3. ___ | thời điểm: ___
```

### SAP §3 — Thống kê mô tả (Table 1)
```
Biến liên tục: kiểm phân phối → Shapiro-Wilk (n<50) hoặc histogram (n≥50)
  Chuẩn: TB ± ĐLC  |  Lệch: Trung vị [IQR Q1–Q3]
Biến phân loại: n (%)
So sánh nền (Table 1): t-test/Mann-Whitney + chi²/Fisher (CHỈ MÔ TẢ, không p-value chính)
```

### SAP §4 — Phân tích chính (Mục tiêu 1)
```
{sap_analysis_note}
α (hai đuôi): 0.05
Hiệu ứng trình bày: [OR/HR/RR/MD + 95%CI] — KHÔNG chỉ p-value
Phần mềm: ☐ R  ☐ Stata  ☐ SPSS  | Seed ngẫu nhiên: {suggested_seed} [CẦN BÁC SĨ XÁC NHẬN — gợi ý tự sinh từ ngày chạy]
```

### SAP §5 — Phân tích đa biến (Mục tiêu 2 — nếu có)
```
Mô hình: ☐ Logistic  ☐ Linear  ☐ Cox  ☐ Mixed-effects  ☐ GEE
Covariates (định trước — KHÔNG thêm sau khi xem dữ liệu):
  - [CẦN BÁC SĨ LIỆT KÊ với lý do cho từng biến + DAG nếu có]
{epv_note}
Kiểm đa cộng tuyến: VIF < 5 cho mọi biến
Kiểm mức phù hợp: ☐ Hosmer-Lemeshow  ☐ Calibration plot
```

### SAP §6 — Dữ liệu thiếu
```
Giả định: ☐ MCAR  ☐ MAR  ☐ MNAR (phân tích pattern thiếu trước khi chọn)
  MCAR → Complete-case (báo cáo tỷ lệ thiếu)
  MAR  → Multiple Imputation: m=20, phương pháp PMM/logistic
  MNAR → Sensitivity (tilt parameter / pattern mixture)
Ngưỡng chấp nhận: < [CẦN ẤN ĐỊNH]% (ví dụ: <20%)
```

### SAP §7 — Phân tích nhóm nhỏ (định trước — KHÔNG thêm sau)
```
Nhóm nhỏ 1: [CẦN — tiêu chí: ___] | Giả thuyết tương tác: ___
Nhóm nhỏ 2: [CẦN]
Kiểm định tương tác: interaction test (p < 0.05 = subgroup effect có ý nghĩa)
Kết quả nhóm nhỏ là THĂM DÒ nếu không có giả thuyết định trước
```

### SAP §8 — Kiểm soát đa so sánh
```
Số kết cục phụ / nhóm / thời điểm: [CẦN ẤN ĐỊNH]
Chiến lược:
  ☐ Không điều chỉnh (1 kết cục chính rõ, phụ là thăm dò)
  ☐ Bonferroni: α = 0.05 / n_so_sánh
  ☐ Holm-Bonferroni
  ☐ FDR Benjamini-Hochberg
Khớp với α dùng khi tính cỡ mẫu (G3): ✓
```

### SAP §9 — Phân tích nhạy cảm
```
1. [CẦN — lý do: ___] → kỳ vọng: kết quả ổn định
2. [CẦN — lý do: ___] → kỳ vọng: ___
3. Per-protocol sensitivity (nếu ITT là chính) → kiểm tính vững chắc
```

### SAP §10 — Phần mềm và seed
```
Phần mềm chính: ☐ R v___  ☐ Stata v___  ☐ SPSS v___
R packages dự kiến: {suggested_packages} [CẦN BÁC SĨ XÁC NHẬN — gợi ý theo thiết kế {internal}]
Random seed: {suggested_seed} [CẦN BÁC SĨ XÁC NHẬN — gợi ý tự sinh từ ngày chạy, có thể đổi]
Script phân tích: lưu tại exports/{study_name}/scripts/ — versioned cùng protocol
```

### SAP §11 — Dummy Tables (Shells — điền sau khi có kết quả thật)

```
BẢNG 1 — ĐẶC ĐIỂM NỀN
| Biến | Nhóm A (n=___) | Nhóm B (n=___) | p |
|------|----------------|----------------|---|
| Tuổi, TB±ĐLC (năm) | | | |
| Giới nữ, n (%) | | | |
| [Bệnh kèm], n (%) | | | |
| [Biến nền theo PICO P] | | | |
| [Biến lâm sàng chính] | | | |

BẢNG 2 — KẾT CỤC CHÍNH
| Kết cục | Nhóm A (n=___) | Nhóm B (n=___) | Hiệu ứng (95%CI) | p |
|---------|----------------|----------------|-------------------|---|
| [Tên kết cục chính] | | | [OR/HR/MD]=___ | |

BẢNG 3 — KẾT CỤC PHỤ
| Kết cục phụ | Nhóm A | Nhóm B | Hiệu ứng (95%CI) | p |
|-------------|--------|--------|-------------------|---|
| [Kết cục phụ 1] | | | | |
| [Kết cục phụ 2] | | | | |
| [Kết cục phụ 3] | | | | |

BẢNG 4 — PHÂN TÍCH ĐA BIẾN
| Biến | OR/HR (thô) | 95%CI | OR/HR (hiệu chỉnh) | 95%CI | p |
|------|-------------|-------|---------------------|-------|---|
| [Can thiệp/Phơi nhiễm chính] | | | | | |
| [Covariate 1] | | | | | |
| [Covariate 2] | | | | | |
```

### SAP §12 — Ngưỡng ý nghĩa và power
```
α (hai đuôi): 0.05
Power mục tiêu: ___% (thường 80% hoặc 90%)
→ Khớp với tính cỡ mẫu (G3) — KHÔNG đổi sau khi chốt.
```

---

## PHẦN 6 — SAP LOCK CERTIFICATE (CHỜ BÁC SĨ KÝ → MỞ G4)

```
╔══════════════════════════════════════════════════════════════╗
║    BIÊN BẢN KHÓA KẾ HOẠCH PHÂN TÍCH THỐNG KÊ (SAP)        ║
╠══════════════════════════════════════════════════════════════╣
║  Đề tài: {study_name:<54}║
║  Phiên bản SAP: 1.0                                         ║
║  Ngày soạn SAP: {run_date[:10]:<46}║
║  Trạng thái dữ liệu lúc khóa: CHƯA CÓ / CHƯA XEM          ║
║                                                              ║
║  Kết cục chính (KHÔNG đổi sau khóa):                        ║
║    [CẦN BÁC SĨ ĐIỀN — từ PICO O đã xác nhận ở G0]          ║
║  Quần thể phân tích chính:                                  ║
║    [CẦN BÁC SĨ ĐIỀN — từ SAP §1]                           ║
║  Phương pháp phân tích chính:                               ║
║    [CẦN BÁC SĨ ĐIỀN — từ SAP §4]                           ║
║  α: 0.05 (hai đuôi)  |  Power: [CẦN]%                      ║
╠══════════════════════════════════════════════════════════════╣
║  Người xác nhận: ___ (Chủ nhiệm đề tài)                     ║
║  Ngày khóa chính thức: [CẦN ĐIỀN + KÝ TÊN]                 ║
║                                                              ║
║  Chữ ký: _______________  Ngày: ___/___/20__                ║
╠══════════════════════════════════════════════════════════════╣
║  SAU KHI KÝ: KHÔNG đổi kết cục chính / mô hình chính.      ║
║  Phân tích bổ sung sau khi xem dữ liệu → ghi THĂM DÒ.     ║
╚══════════════════════════════════════════════════════════════╝
```

**→ Để mở G4:** Bác sĩ xác nhận "SAP đã khóa ngày [DD/MM/YYYY]"
  Agent ghi: G4_STATUS=LOCKED | G4_SAP_VERSION=1.0 | G4_LOCK_DATE=[date]

---

## PHẦN 7 — TIÊU CHÍ QUA CỔNG G1

```
☑ Loại thiết kế đã suy luận từ PICO + evidence landscape
☑ 2-3 thiết kế ứng viên đã so sánh
☑ 7 sai lệch đã phân tích với biện pháp kiểm soát
☑ SAP skeleton 12 mục đã sinh
☑ Dummy tables 4 bảng đã tạo shell
☑ Effect size ước lượng từ PubMed thật (xem §3)
☐ Bác sĩ xác nhận thiết kế chọn [CHỜ BÁC SĨ]
☐ PICO O (kết cục) điền vào SAP §2 [CHỜ BÁC SĨ]
☐ Covariates SAP §5 liệt kê với lý do [CHỜ BÁC SĨ]
☐ Effect size thật + cỡ mẫu → G3 (co-mau-nghien-cuu) [BƯỚC TIẾP]
☐ SAP Lock Certificate ký → G4 [CHỜ SAU G3]
```

**Bước tiếp theo:**
1. Bác sĩ xem §3 (effect size) → chọn ước lượng phù hợp
2. Chạy G3: `python tools/run_g3_auto.py --study {study_name}`
3. Sau khi có cỡ mẫu, ký SAP → mở G4
{specialist_block}
---

*[BẢN NHÁP TỰ ĐỘNG] — Cần bác sĩ kiểm chứng. PMID/DOI trong §3 là THẬT từ PubMed.*
"""
    return artifact


# ════════════════════════════════════════════════════════════════════════════
# 5. GUARDRAIL R1-R7 CHO G1
# ════════════════════════════════════════════════════════════════════════════

def guardrail_check_g1(artifact: str, effects: list, topic: str = "", internal_code: str = "") -> dict:
    errors, warnings = [], []

    # R1 — Effect sizes có nguồn thật (nếu có)
    if effects:
        warnings.append(f"R1 ✅ {len(effects)} effect size ước lượng từ PubMed thật")
    else:
        warnings.append("R1 ⚠ Không tìm được effect size từ abstracts — bác sĩ cần tự tìm")

    # R2 — PII
    # Chuẩn hóa NFC trước khi so khớp: pii_keywords liệt kê ở dạng tổ hợp sẵn (NFC); artifact
    # ở dạng NFD (chữ nền + dấu rời) khớp trượt hoàn toàn, để lọt PII qua guardrail G1 mà
    # không báo lỗi.
    artifact_normalized = unicodedata.normalize("NFC", artifact).lower()
    pii_keywords = ["tên bệnh nhân", "họ tên", "ngày sinh", "cccd"]
    for p in pii_keywords:
        if p in artifact_normalized:
            errors.append(f"R2 🔴 PII phát hiện: '{p}'")
            break
    else:
        warnings.append("R2 ✅ Không có PII")

    # R3 — Không tự vượt cổng G4
    if "G4_STATUS = LOCKED" in artifact or "G4=LOCKED" in artifact:
        errors.append("R3 🔴 Không được tự ghi G4=LOCKED — cần bác sĩ ký")
    else:
        warnings.append("R3 ✅ Không tự vượt cổng G4")

    # R4 — Không bịa effect size
    if "[CẦN" in artifact:
        warnings.append("R4 ✅ Các giá trị cần bác sĩ điền đã gắn nhãn [CẦN...]")
    else:
        errors.append("R4 🔴 Thiếu nhãn [CẦN...] cho các mục cần bác sĩ")

    # R5 — Không bịa cỡ mẫu
    # SỬA: kiểm tra "[CẦN" trên TOÀN VĂN BẢN vô nghĩa vì template có ≥40 chỗ
    # "[CẦN" ở khắp SAP §1-§12 không liên quan gì tới câu "cỡ mẫu" — điều
    # kiện "not in artifact" gần như KHÔNG BAO GIỜ đúng, nên nếu một dòng
    # "cỡ mẫu = 200" bịa xuất hiện ở BẤT KỲ ĐÂU khác trong văn bản 700+ dòng,
    # guardrail vẫn PASS oan (vì "[CẦN" luôn tồn tại ở chỗ khác). Sửa: kiểm
    # CỤC BỘ trong cửa sổ ±80 ký tự quanh MỖI vị trí khớp "cỡ mẫu...=...\d+".
    import re as _re
    artifact_lower = artifact.lower()
    unlabeled_matches = []
    for m in _re.finditer(r'cỡ mẫu.*?=\s*\d+', artifact_lower):
        window = artifact_lower[max(0, m.start() - 80): m.end() + 80]
        if "[cần" not in window:
            unlabeled_matches.append(artifact[m.start():m.end()])
    if unlabeled_matches:
        errors.append(
            f"R5 🔴 Tìm thấy cỡ mẫu cụ thể KHÔNG kèm nhãn [CẦN...] gần đó "
            f"(nghi bịa số, không phải placeholder): {unlabeled_matches[:3]}"
        )
    else:
        warnings.append("R5 ✅ Mọi chỗ 'cỡ mẫu = N' đều gắn nhãn [CẦN...] cục bộ hoặc chưa điền")

    # R7 — Disclaimer
    if "cần bác sĩ kiểm chứng" not in artifact.lower():
        errors.append("R7 🔴 Thiếu disclaimer")
    else:
        warnings.append("R7 ✅ Có disclaimer")

    # R6 — Đối chiếu từ khóa thiết kế tường minh trong topic vs design_code đã
    # chọn CUỐI CÙNG. Cảnh báo (KHÔNG chặn cứng — không dùng errors) vì có thể
    # bác sĩ có lý do chính đáng khác thiết kế "hiển nhiên" theo từ khóa. Thêm
    # 2026-07-06 (khuyến nghị độc lập từ 2 cụm kiểm định đối kháng vòng 2).
    if topic and internal_code:
        consistency_warns = check_topic_design_consistency(topic, internal_code)
        if consistency_warns:
            warnings.extend(consistency_warns)
        else:
            warnings.append("R6 ✅ design_code khớp từ khóa thiết kế trong tên đề tài (nếu có)")

    return {"passed": len(errors) == 0, "errors": errors, "warnings": warnings}


# ════════════════════════════════════════════════════════════════════════════
# 6. XUẤT DOCX
# ════════════════════════════════════════════════════════════════════════════

def export_docx_g1(artifact_md: str, study_name: str, out_dir: Path) -> Optional[Path]:
    try:
        from docx import Document
        from docx.shared import Pt, RGBColor
        doc = Document()
        doc.add_heading(f"A2 — THIẾT KẾ NGHIÊN CỨU & SAP | {study_name}", 0)
        doc.add_paragraph(f"[BẢN NHÁP TỰ ĐỘNG] | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        doc.add_paragraph("Cần bác sĩ kiểm chứng.")
        doc.add_page_break()
        for line in artifact_md.split("\n"):
            if line.startswith("# "):
                doc.add_heading(line[2:], 1)
            elif line.startswith("## "):
                doc.add_heading(line[3:], 2)
            elif line.startswith("### "):
                doc.add_heading(line[4:], 3)
            elif line.strip().startswith("|"):
                p = doc.add_paragraph(line)
                p.style.font.name = "Courier New"
                p.style.font.size = Pt(9)
            elif line.strip().startswith("```") or line.strip() == "---":
                pass
            elif line.strip():
                p = doc.add_paragraph(line)
                if "[CẦN" in line:
                    for run in p.runs:
                        if "[CẦN" in run.text:
                            run.font.color.rgb = RGBColor(0xCC, 0x44, 0x00)
        docx_path = out_dir / f"G1_A2_PROTOCOL_DESIGN_{study_name}.docx"
        doc.save(docx_path)
        return docx_path
    except ImportError:
        print("  ⚠ python-docx không cài — bỏ qua DOCX")
        return None
    except Exception as e:
        print(f"  ⚠ Lỗi DOCX: {e}")
        return None


# ════════════════════════════════════════════════════════════════════════════
# 7. GHI CHECKPOINT G1
# ════════════════════════════════════════════════════════════════════════════

def write_g1_checkpoint(study_name: str, out_dir: Path, question_type: str,
                         design: dict, effects: list, guardrail: dict,
                         artifact_path: Path, docx_path: Optional[Path],
                         specialist_modules: Optional[list[str]] = None) -> Path:
    cp = {
        "study": study_name, "gate": "G1",
        "gate_status": "DRAFT — CHỜ BÁC SĨ XÁC NHẬN THIẾT KẾ + ĐIỀN PICO O VÀO SAP",
        "generated_at": datetime.now().isoformat(),
        "question_type": question_type,
        "design": {
            "primary": design["primary"],
            "internal_code": design["internal_code"],
            "reporting_standard": design["reporting_standard"],
            "alternative_1": design["alternative_1"],
            "ambiguous": design.get("ambiguous", False),
            # Vá 2026-07-17 (round audit đối kháng 4, chuẩn STROBE mục 9 — Bias): bảng
            # kiểm soát sai lệch ĐÃ tính ở đây (BIAS_CONTROLS, dùng để render bảng trong
            # artifact A2 markdown) nhưng trước đây KHÔNG được ghi vào checkpoint — G7
            # (đọc G1_checkpoint.json để dựng bản thảo) không có đường nào lấy lại dữ
            # liệu này, nên mục 9 STROBE ("mô tả nỗ lực xử lý nguồn sai lệch") luôn để
            # trống [CẦN] trong Methods dù G1 đã tính sẵn.
            "bias_controls": design.get("bias_controls", []),
        },
        "specialist_modules": specialist_modules or [],
        "effect_sizes_found": len(effects),
        "effect_size_samples": effects[:3] if effects else [],
        "guardrail": {
            "passed": guardrail["passed"],
            "errors": guardrail["errors"],
        },
        "artifacts": {
            "A2_markdown": str(artifact_path),
            "A2_docx": str(docx_path) if docx_path else None,
        },
        "pending_doctor_actions": [
            "Xác nhận thiết kế chọn (§1)",
            "Điền kết cục chính (SAP §2) — từ PICO O ở G0",
            "Điền covariates (SAP §5) với lý do",
            "Chọn effect size ước lượng từ §3 (hoặc pilot data)",
        ],
        "next_gate": "G2 (Đạo đức IRB) song song với G3 (Cỡ mẫu + SAP hoàn thiện)",
        "g4_status": "PENDING — SAP chưa khóa (khóa sau G3 sau khi bác sĩ ký)",
        "disclaimer": "Cần bác sĩ kiểm chứng.",
    }
    cp_path = out_dir / "G1_checkpoint.json"
    cp_path.write_text(json.dumps(cp, ensure_ascii=False, indent=2), encoding="utf-8")
    return cp_path


# ════════════════════════════════════════════════════════════════════════════
# 8. MAIN
# ════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="G1 Auto — Tự động hóa cổng G1: Thiết kế nghiên cứu + SAP skeleton"
    )
    parser.add_argument("--study", required=True,
                        help="Mã/tên đề tài (cùng với --study đã dùng ở G0)")
    parser.add_argument("--topic", default=None,
                        help="Chủ đề nghiên cứu (tuỳ chọn — nếu không có G0_checkpoint.json)")
    parser.add_argument("--question-type", default="treatment",
                        choices=list(QUESTION_TYPES.keys()),
                        help="Loại câu hỏi (mặc định: treatment)")
    parser.add_argument("--email", default=None)
    args = parser.parse_args()

    if args.email:
        os.environ["NCBI_EMAIL"] = args.email

    run_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    study = re.sub(r'[^\w\-]', '_', args.study.strip().replace(" ", "-"))

    print(f"\n{'='*65}")
    print(f"  G1 AUTO — {study}")
    print(f"  Thời gian: {run_date}")
    print(f"{'='*65}\n")

    # Đọc G0 checkpoint nếu có
    out_dir = Path("exports") / study
    out_dir.mkdir(parents=True, exist_ok=True)
    g0_cp_path = out_dir / "G0_checkpoint.json"

    g0_gaps = {}
    topic = args.topic or study
    question_type = args.question_type

    if g0_cp_path.exists():
        print("📂 Bước 1/7: Đọc G0 checkpoint...")
        g0_cp = json.loads(g0_cp_path.read_text(encoding="utf-8"))
        pm = g0_cp.get("pubmed_results", {})
        g0_gaps["n_sr"]             = pm.get("n_sr", 0)
        g0_gaps["n_rct"]            = pm.get("n_rct", 0)
        g0_gaps["n_guide"]          = pm.get("n_guideline", 0)
        g0_gaps["n_recent"]         = pm.get("n_recent", 0)
        g0_gaps["most_recent_year"] = pm.get("most_recent_year")
        g0_gaps["evidence_level"]   = g0_cp.get("evidence_level", "")
        g0_gaps["research_gaps"]    = g0_cp.get("research_gaps", [])
        g0_gaps["design_hint"]      = g0_cp.get("design_suggestion", "")
        # Đọc topic + base_query từ G0 checkpoint (có từ run_g0_auto v2)
        # SỬA: .get("topic", study) không có "or" bọc ngoài — nếu checkpoint
        # có key "topic" nhưng giá trị null, .get() trả None (không dùng
        # default), crash topic[:60] ngay dưới. Bọc "or study" như G2 đã sửa.
        topic = args.topic or (g0_cp.get("topic") or study)
        g0_gaps["base_query"]       = g0_cp.get("base_query", topic)
        print(f"  → G0: {g0_gaps['n_sr']} SR | {g0_gaps['n_rct']} RCT | {g0_gaps['evidence_level']}")
        print(f"  → Topic: {topic[:60]}")
    else:
        print(f"📂 Bước 1/7: Không tìm thấy G0 checkpoint tại {g0_cp_path}")
        print(f"   Tiếp tục với --question-type={question_type}")

    # Suy loại thiết kế
    print(f"\n🔬 Bước 2/7: Suy loại thiết kế ({QUESTION_TYPES.get(question_type, question_type)})...")
    design = infer_study_design(question_type, g0_gaps, topic)

    # PIN THIẾT KẾ (bác sĩ xác nhận, durable) — study_meta.json['design_code']
    # ghi đè suy luận tự động để CHẠY LẠI KHÔNG DRIFT (vd đề tài hài lòng phải là
    # cross_sectional, không để rơi về placeholder 'cohort'). Đây là quyết định
    # THẬT của bác sĩ, hệ tôn trọng — không tự đổi.
    pinned = _read_pinned_design(out_dir)
    if pinned:
        design = _apply_design_pin(design, pinned)
        print(f"  → 📌 Dùng THIẾT KẾ PIN từ study_meta.json: {pinned}")

    print(f"  → Thiết kế ưu tiên: {design['primary']}")
    print(f"  → Chuẩn báo cáo: {design['reporting_standard']}")

    # Tìm effect size từ PubMed thật
    print("\n📊 Bước 3/7: Trích xuất effect size từ abstracts PubMed...")
    search_query = g0_gaps.get("base_query") or topic
    effects = search_for_effect_sizes(search_query, study)
    print(f"  → Tìm được {len(effects)} ước lượng effect size từ abstracts thật")
    if effects:
        for e in effects[:3]:
            print(f"     • {e['type']}={e['value']} — PMID:{e['pmid']} ({e['year']})")

    # Sinh artifact G1
    print("\n✍️  Bước 4/7: Sinh artifact G1 (Design + SAP skeleton)...")
    artifact_md = generate_g1_artifact(
        topic, study, question_type, design, effects, g0_gaps, run_date
    )
    md_path = out_dir / f"G1_A2_PROTOCOL_DESIGN_{study}.md"
    md_path.write_text(artifact_md, encoding="utf-8")
    print(f"  → Lưu: {md_path}")
    detected_modules = detect_specialist_modules(topic)
    if detected_modules:
        labels = ", ".join(_SPECIALIST_MODULE_LABEL[m] for m in detected_modules)
        print(f"  → 🧩 Mô-đun chuyên biệt phát hiện: {labels}")

    # Guardrail
    print("\n🛡️  Bước 5/7: Kiểm guardrail R1-R7...")
    guardrail = guardrail_check_g1(artifact_md, effects, topic, design.get("internal_code", ""))
    for msg in guardrail["warnings"]:
        print(f"  {msg}")
    for err in guardrail["errors"]:
        print(f"  {err}")
    status = "✅ PASS" if guardrail["passed"] else f"⚠ {len(guardrail['errors'])} LỖI"
    print(f"  → Guardrail: {status}")

    # Xuất DOCX
    print("\n📄 Bước 6/7: Xuất DOCX...")
    docx_path = export_docx_g1(artifact_md, study, out_dir)
    if docx_path:
        print(f"  → Lưu: {docx_path}")

    # Checkpoint
    print("\n💾 Bước 7/7: Ghi checkpoint G1...")
    specialist_modules = detect_specialist_modules(topic)
    cp_path = write_g1_checkpoint(
        study, out_dir, question_type, design, effects, guardrail, md_path, docx_path,
        specialist_modules=specialist_modules,
    )
    print(f"  → Lưu: {cp_path}")

    # Tóm tắt
    print(f"\n{'='*65}")
    print(f"  ✅ G1 HOÀN THÀNH — {study}")
    print(f"{'='*65}")
    print(f"\n  📁 Đầu ra: {out_dir}/")
    print(f"  📝 A2 Markdown: {md_path.name}")
    if docx_path:
        print(f"  📄 A2 DOCX:     {docx_path.name}")
    print(f"  🔬 Thiết kế:   {design['primary']}")
    print(f"  📊 Effect sizes: {len(effects)} từ PubMed thật")
    print(f"  🔴 Guardrail:  {status}")
    print("\n  VIỆC CÒN LẠI CỦA BÁC SĨ:")
    print("  1. Xem §1 — xác nhận thiết kế chọn")
    print("  2. Xem §3 — effect size ước lượng → chọn cho G3")
    print("  3. Điền §5 SAP §2 (kết cục chính) + §5 (covariates)")
    print(f"  4. Chạy G3 (cỡ mẫu): python tools/run_g3_auto.py --study {study}")
    print("  5. Sau G3: ký SAP Lock Certificate → mở G4")
    print("\n  Cần bác sĩ kiểm chứng.")
    print(f"{'='*65}\n")

    # Vá 2026-07-11 (vòng 9): trước đây banner "HOÀN THÀNH" in vô điều kiện + exit code
    # luôn 0 dù guardrail có lỗi thật — checkpoint ĐÃ ghi đúng, nhưng process exit code
    # không phản ánh, nên chạy trực tiếp (không qua run_pipeline.py) sẽ tưởng nhầm là
    # xong. Đối xứng cách G3/G4/G9 đã làm.
    if not guardrail["passed"]:
        raise SystemExit(GC.EXIT_GUARDRAIL_FAIL)

    return {
        "gate": "G1", "status": status,
        "design": design["primary"],
        "n_effects": len(effects),
    }


if __name__ == "__main__":
    main()
