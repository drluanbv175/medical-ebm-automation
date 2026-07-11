"""
run_g2_auto.py — TỰ ĐỘNG HÓA CỔNG G2: Đạo đức & Đăng ký nghiên cứu

Đọc G0 + G1 checkpoint → sinh TRỌN BỘ HỒ SƠ G2 (8 tài liệu) sẵn nộp:
  1. Đơn xin phê duyệt IRB
  2. Tóm tắt đề cương cho Hội đồng (lay summary 1 trang)
  3. Bảng rủi ro–lợi ích (phân loại nguy cơ tự động)
  4. Phiếu Đồng thuận Tham gia (ICF tiếng Việt — 7 mục Helsinki đầy đủ)
  5. ICF tiếng Anh (dịch trung thành)
  6. Kế hoạch Quản lý Dữ liệu (DMP — Luật 91/2025/QH15 + NĐ 356/2025)
  7. Checklist nộp Hội đồng Đạo đức (TT43/2024/TT-BYT)
  8. Khai báo COI + Tài trợ + AI (ICMJE form rút gọn)
  + Bản nháp 18 trường WHO Trial Registration (ClinicalTrials.gov)
  + Tìm kiếm thật ClinicalTrials.gov API v2 (prior art + tham khảo NCT)

Bác sĩ chỉ cần: in/ký và nộp Hội đồng → nhận số IRB → cung cấp để mở G2.

Sử dụng:
    python tools/run_g2_auto.py --study "SGLT2-HFpEF-2026"
    python tools/run_g2_auto.py --study "NEW" --topic "..." --design cohort
"""

import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Optional

_REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_REPO_ROOT))

_TODAY = datetime.now().strftime("%d/%m/%Y")
_YEAR  = datetime.now().strftime("%Y")

# ════════════════════════════════════════════════════════════════════════════
# 1. PHÂN LOẠI RỦI RO VÀ LỘ TRÌNH IRB
# ════════════════════════════════════════════════════════════════════════════

RISK_PROFILES = {
    "rct": {
        "risk_level": "LỚN HƠN TỐI THIỂU",
        "irb_route": "FULL BOARD REVIEW (Toàn Hội đồng)",
        "registration": "BẮT BUỘC (trước tuyển NTG đầu tiên)",
        "register_where": "ClinicalTrials.gov hoặc ANZCTR/ISRCTN",
        "icf_required": True,
        "icf_waiver_eligible": False,
        "risks": [
            ("Tác dụng phụ của can thiệp/thuốc thử nghiệm", "Trung bình–Cao", "Nhẹ–Trung bình",
             "Giám sát chặt AE/SAE; dừng nghiên cứu nếu xuất hiện SAE nghiêm trọng; DSMB/DMC giám sát"),
            ("Lấy mẫu máu / thủ thuật bổ sung", "Cao", "Nhẹ",
             "Nhân viên được đào tạo; vô trùng; băng keo sau lấy máu"),
            ("Rò rỉ thông tin cá nhân", "Rất thấp", "Trung bình",
             "Mã hóa AES-256; bảng liên kết ID–tên lưu riêng, khóa mật khẩu mạnh; quy trình vi phạm 72h"),
            ("Gánh nặng thời gian / bất tiện cho NTG", "Cao", "Nhẹ",
             "Tối giản lịch hẹn; bồi thường chi phí đi lại hợp lý; tái khám kết hợp với chăm sóc thường quy"),
            ("Mất theo dõi / dropout ảnh hưởng kết cục", "Trung bình", "Nhẹ",
             "Liên hệ định kỳ; lịch tái khám linh hoạt; ITT analysis trong SAP"),
        ],
        "benefits": "Phát sinh bằng chứng RCT cấp độ cao nhất; cải thiện thực hành điều trị; NTG có thể hưởng lợi trực tiếp từ can thiệp mới",
    },
    "cohort": {
        "risk_level": "TỐI THIỂU",
        "irb_route": "EXPEDITED REVIEW (Rút gọn — nếu chỉ quan sát + lấy mẫu tối thiểu)",
        "registration": "KHUYẾN KHÍCH (trước thu thập, không bắt buộc với quan sát thuần túy)",
        "register_where": "ClinicalTrials.gov (nếu có can thiệp) hoặc không cần",
        "icf_required": True,
        "icf_waiver_eligible": False,
        "risks": [
            ("Lấy mẫu máu / bổ sung ngoài chăm sóc thường quy", "Trung bình", "Nhẹ",
             "Nhân viên được đào tạo; lấy cùng lịch xét nghiệm thường quy nếu có thể"),
            ("Rò rỉ thông tin cá nhân", "Rất thấp", "Trung bình",
             "Mã hóa; khử định danh trước phân tích; bảng liên kết lưu riêng"),
            ("Gánh nặng bộ câu hỏi / phỏng vấn", "Thấp", "Không đáng kể",
             "Bộ câu hỏi ngắn ≤20 phút; trả lời tự nguyện từng mục"),
            ("Phát hiện bệnh không mong đợi trong theo dõi", "Thấp", "Nhẹ–Trung bình",
             "Quy trình thông báo kết quả bất thường và chuyển điều trị phù hợp"),
        ],
        "benefits": "Cung cấp dữ liệu thực hành tại cộng đồng/bệnh viện Việt Nam; không có bằng chứng local → hỗ trợ xây dựng guideline địa phương",
    },
    "case_control": {
        "risk_level": "TỐI THIỂU",
        "irb_route": "EXPEDITED REVIEW",
        "registration": "KHUYẾN KHÍCH",
        "register_where": "Đăng ký trong nước hoặc ClinicalTrials.gov",
        "icf_required": True,
        "icf_waiver_eligible": False,
        "risks": [
            ("Recall bias trong phỏng vấn hồi cứu", "Thấp", "Không đáng kể",
             "Câu hỏi tiền định; phỏng vấn viên mù với tình trạng ca/chứng"),
            ("Rò rỉ thông tin cá nhân", "Rất thấp", "Trung bình",
             "Khử định danh; bảo mật phiếu phỏng vấn"),
            ("Lo lắng tâm lý từ việc hỏi bệnh sử nhạy cảm", "Thấp", "Nhẹ",
             "Nhân viên được đào tạo hỏi nhạy cảm; NTG có thể bỏ qua câu hỏi"),
        ],
        "benefits": "Xác định yếu tố nguy cơ/phơi nhiễm hiệu quả với chi phí thấp; thiết kế phù hợp kết cục hiếm",
    },
    "cross_sectional": {
        "risk_level": "TỐI THIỂU",
        "irb_route": "EXPEDITED REVIEW (hoặc EXEMPT nếu không có PII và rủi ro tối thiểu)",
        "registration": "KHÔNG BẮT BUỘC",
        "register_where": "Không cần (có thể đăng ký tùy chọn)",
        "icf_required": True,
        "icf_waiver_eligible": True,
        "risks": [
            ("Rò rỉ thông tin từ bộ câu hỏi", "Rất thấp", "Nhẹ",
             "Khuyết danh hoàn toàn nếu không cần theo dõi; mã hóa nếu cần liên kết"),
            ("Gánh nặng thời gian", "Thấp", "Không đáng kể",
             "Bộ câu hỏi ngắn; tự điền hoặc qua điện thoại/email"),
        ],
        "benefits": "Cung cấp dữ liệu tỷ lệ hiện mắc/tỷ lệ các yếu tố liên quan tại địa phương; chi phí thấp",
    },
    "diagnostic": {
        "risk_level": "TỐI THIỂU ĐẾN LỚN HƠN TỐI THIỂU (tùy loại xét nghiệm)",
        "irb_route": "EXPEDITED hoặc FULL (tùy xét nghiệm tham chiếu có xâm lấn không)",
        "registration": "KHUYẾN KHÍCH (STARD 2015 yêu cầu tiền đăng ký)",
        "register_where": "ClinicalTrials.gov hoặc PROSPERO (nếu SR chẩn đoán)",
        "icf_required": True,
        "icf_waiver_eligible": False,
        "risks": [
            ("Xét nghiệm tham chiếu (reference standard) có thể xâm lấn", "Trung bình", "Nhẹ–Trung bình",
             "Đánh giá nguy cơ từng xét nghiệm; chỉ làm khi chỉ định lâm sàng độc lập"),
            ("Rò rỉ kết quả xét nghiệm", "Rất thấp", "Trung bình",
             "Kết quả lưu mã hóa; chỉ bác sĩ điều trị biết kết quả thật"),
            ("Trải nghiệm không thoải mái từ index test", "Thấp", "Nhẹ",
             "Mô tả quy trình đầy đủ trong ICF; NTG có thể rút lui"),
        ],
        "benefits": "Cải thiện độ chính xác chẩn đoán; giảm chẩn đoán muộn; cơ sở cho guideline sàng lọc",
    },
    "sr_ma": {
        "risk_level": "TỐI THIỂU (không tiếp xúc người tham gia)",
        "irb_route": "EXEMPT hoặc WAIVER ICF (dữ liệu đã công bố, không có PII)",
        "registration": "BẮT BUỘC đăng ký PROSPERO trước tìm kiếm",
        "register_where": "PROSPERO (https://www.crd.york.ac.uk/prospero/)",
        "icf_required": False,
        "icf_waiver_eligible": True,
        "risks": [
            ("Sai lệch trong tổng hợp bằng chứng → kết luận sai", "Trung bình", "Tiềm tàng cao",
             "Protocol PRISMA 2020 + tiền đăng ký PROSPERO; 2 screener độc lập; RoB tool phù hợp"),
        ],
        "benefits": "Tổng hợp bằng chứng cấp cao nhất; nền tảng cho guideline; tiết kiệm chi phí nghiên cứu mới",
    },
}


# Từ khóa trong TEXT mô tả thiết kế cho thấy có can thiệp/thuốc/ngẫu nhiên hóa
# — dùng để cross-check khi internal_code không đáng tin hoặc không khớp bảng.
_RCT_TEXT_SIGNALS = [
    "rct", "randomiz", "ngẫu nhiên", "thử nghiệm lâm sàng", "can thiệp",
    "clinical trial", "intervention", "thuốc thử nghiệm", "drug trial",
]


def get_risk_profile(internal_code: str, design_primary: str = "") -> dict:
    """
    Trả về hồ sơ nguy cơ theo internal_code.
    SỬA: trước đây fallback về RISK_PROFILES["cohort"] (nguy cơ TỐI THIỂU —
    lộ trình rút gọn) khi internal_code không nhận diện được — sai HƯỚNG AN
    TOÀN, vì một internal_code hỏng/lỗi chính tả có thể đang mô tả một RCT
    thuốc thật (design_primary nói rõ) nhưng vẫn bị định tuyến Expedited thay
    vì Full Board. Nay: fallback về "rct" (mức nguy cơ CAO nhất, Full Board)
    — hướng an toàn hơn khi không chắc chắn. Đồng thời cross-check text mô
    tả thiết kế: nếu có dấu hiệu can thiệp/RCT nhưng code lại trỏ về mức thấp
    hơn, vẫn nâng lên "rct" và cảnh báo rõ trong artifact.
    """
    # Phòng thủ kép: design_primary có thể là None nếu gọi trực tiếp hàm này
    # từ nơi khác không qua main() (nơi đã coerce None → fallback string).
    # SỬA: cụm "can thiệp" khớp cả câu PHỦ ĐỊNH vô hại như "không có can
    # thiệp nào ngoài theo dõi thường quy" — không phải lỗi ranh giới từ (đây
    # vốn đã là cụm nhiều từ có khoảng trắng phân cách tự nhiên) mà là chưa
    # loại trừ ngữ cảnh phủ định. Thêm kiểm tra: bỏ qua khớp nếu ngay trước
    # đó (trong ~20 ký tự) có từ phủ định — vẫn thiên AN TOÀN (chỉ giảm bớt
    # cảnh báo thừa, các khớp không có phủ định đứng trước vẫn nâng Full
    # Board như cũ).
    _dp = str(design_primary or "").lower()
    _NEGATION_WORDS = ("không có", "không phải", "chưa có", "không dùng", "no ")
    text_suggests_rct = False
    for kw in _RCT_TEXT_SIGNALS:
        for m in re.finditer(re.escape(kw), _dp):
            preceding = _dp[max(0, m.start() - 20):m.start()]
            if not any(neg in preceding for neg in _NEGATION_WORDS):
                text_suggests_rct = True
                break
        if text_suggests_rct:
            break

    if internal_code not in RISK_PROFILES:
        # Code không nhận diện được → luôn fallback AN TOÀN NHẤT, không phải
        # "cohort". Đánh dấu để artifact cảnh báo bác sĩ kiểm tra lại.
        profile = dict(RISK_PROFILES["rct"])
        profile["_fallback_warning"] = (
            f"🔴 internal_code='{internal_code}' KHÔNG nhận diện được trong bảng phân loại "
            "nguy cơ — hệ thống mặc định về mức nguy cơ CAO NHẤT (Full Board Review) để an "
            "toàn. BÁC SĨ PHẢI kiểm tra lại design_code từ G1 và xác nhận lộ trình IRB đúng."
        )
        return profile

    profile = RISK_PROFILES[internal_code]
    if text_suggests_rct and internal_code != "rct":
        # Text mô tả thiết kế gợi ý RCT/can thiệp nhưng code lại trỏ về thiết
        # kế nguy cơ thấp hơn (vd cohort) — không tự động tin code, nâng lên
        # rct và cảnh báo rõ thay vì âm thầm dùng Expedited cho một RCT thật.
        profile = dict(RISK_PROFILES["rct"])
        profile["_fallback_warning"] = (
            f"🔴 design_code='{internal_code}' (mức nguy cơ thấp hơn) NHƯNG mô tả thiết kế "
            f"(\"{design_primary[:80]}\") có dấu hiệu RCT/can thiệp/thuốc thử nghiệm — hệ "
            "thống nâng lên mức nguy cơ CAO NHẤT (Full Board) để an toàn. BÁC SĨ PHẢI xác "
            "nhận lại thiết kế thật trước khi nộp Hội đồng Đạo đức."
        )
    return profile


# ════════════════════════════════════════════════════════════════════════════
# 2. TÌM KIẾM CLINICALTRIALS.GOV (API v2 — miễn phí, không cần key)
# ════════════════════════════════════════════════════════════════════════════

_CT_BASE = "https://clinicaltrials.gov/api/v2/studies"

def search_clinicaltrials(topic: str, design_code: str, max_results: int = 8) -> list[dict]:
    """Tìm kiếm ClinicalTrials.gov để tham chiếu prior art."""
    # Tách từ khóa
    words = [w for w in topic.split() if len(w) > 3 and w.lower()
             not in {"effect", "with", "from", "among", "patients", "using",
                     "therapy", "treatment", "nghiên", "hiệu", "quả", "trong", "của"}]
    kw = " ".join(words[:4])  # max 4 từ khóa
    kw_en = re.sub(r'[àáảãạăắằẳẵặâấầẩẫậ]', 'a',
             re.sub(r'[èéẻẽẹêếềểễệ]', 'e',
             re.sub(r'[ìíỉĩị]', 'i',
             re.sub(r'[òóỏõọôốồổỗộơớờởỡợ]', 'o',
             re.sub(r'[ùúủũụưứừửữự]', 'u',
             re.sub(r'[đ]', 'd',
             re.sub(r'[ýỳỷỹỵ]', 'y', kw.lower())))))))

    # Trạng thái tìm phù hợp với thiết kế
    status_filter = ""
    if design_code in ("rct", "cohort"):
        status_filter = "&filter.overallStatus=RECRUITING,ACTIVE_NOT_RECRUITING,COMPLETED,NOT_YET_RECRUITING"

    params = urllib.parse.urlencode({
        "query.term": kw_en,
        "pageSize": max_results,
        "fields": "NCTId,BriefTitle,StudyType,OverallStatus,EnrollmentCount,StartDate,Condition,Intervention,Phase",
    })
    url = f"{_CT_BASE}?{params}{status_filter}"

    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json",
                                                    "User-Agent": "EBM-Copilot/1.0 (bsluanbv175@gmail.com)"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        studies = data.get("studies", [])
        results = []
        for s in studies:
            ps = s.get("protocolSection", {})
            id_mod   = ps.get("identificationModule", {})
            stat_mod = ps.get("statusModule", {})
            design_mod = ps.get("designModule", {})
            cond_mod = ps.get("conditionsModule", {})
            enroll_m = design_mod.get("enrollmentInfo", {})
            results.append({
                "nct_id":    id_mod.get("nctId", ""),
                "title":     id_mod.get("briefTitle", "")[:100],
                "status":    stat_mod.get("overallStatus", ""),
                "study_type": design_mod.get("studyType", ""),
                "phase":     ", ".join(design_mod.get("phases", [])),
                "enrollment": enroll_m.get("count", "?"),
                "start_date": stat_mod.get("startDateStruct", {}).get("date", "?"),
                "conditions": ", ".join(cond_mod.get("conditions", [])[:3]),
                "url": f"https://clinicaltrials.gov/study/{id_mod.get('nctId', '')}",
            })
        time.sleep(0.5)
        return results
    except Exception as e:
        print(f"  ⚠ ClinicalTrials.gov không truy cập được: {e}")
        return []


def _ct_table(trials: list) -> str:
    if not trials:
        return "  → Không tìm thấy thử nghiệm tương tự / ClinicalTrials.gov không truy cập được.\n"
    rows = []
    for t in trials:
        rows.append(f"| {t['nct_id']} | {t['title'][:70]} | {t['status']} | {t['enrollment']} | {t['start_date'][:4] if t['start_date'] != '?' else '?'} | {t['phase']} |")
    header  = "| NCT ID | Tên nghiên cứu | Trạng thái | Cỡ mẫu | Năm | Phase |\n"
    divider = "|--------|---------------|-----------|--------|-----|-------|\n"
    return header + divider + "\n".join(rows)


# ════════════════════════════════════════════════════════════════════════════
# 3. SINH TOÀN BỘ HỒ SƠ G2
# ════════════════════════════════════════════════════════════════════════════

def _risk_table(risks: list) -> str:
    rows = []
    for i, (risk, prob, severity, control) in enumerate(risks, 1):
        rows.append(f"| {i} | {risk} | {prob} | {severity} | {control} |")
    header  = "| # | Rủi ro tiềm tàng | Xác suất | Mức độ | Biện pháp giảm thiểu |\n"
    divider = "|---|-----------------|----------|--------|----------------------|\n"
    return header + divider + "\n".join(rows)


def generate_g2_full_package(
    topic: str, study_name: str, design_code: str, design_primary: str,
    reporting_std: str, n_sr: int, n_rct: int, evidence_level: str,
    ct_trials: list, risk: dict, run_date: str, n_adjusted: int = 0
) -> str:
    """Sinh toàn bộ hồ sơ G2 — 8 tài liệu + 18 WHO fields."""

    risk_table_str = _risk_table(risk["risks"])
    ct_table_str   = _ct_table(ct_trials)
    irb_required   = "BẮT BUỘC" if design_code == "rct" else "KHUYẾN KHÍCH"
    # SỬA (tự động hóa thêm — G2 và G3 chạy song song theo thiết kế, nhưng
    # nếu bác sĩ đã chạy G3 TRƯỚC G2, N thật đã có sẵn — không cần để cứng
    # [CẦN] trong khi dữ liệu đã có trong tay): hiển thị N thật nếu đã có,
    # nếu chưa vẫn giữ nguyên placeholder [CẦN] như cũ.
    n_display = str(n_adjusted) if n_adjusted and n_adjusted > 0 else "[CẦN — chờ kết quả G3]"
    n_display_inline = str(n_adjusted) if n_adjusted and n_adjusted > 0 else "[CẦN — từ G3]"

    # ICF waiver flag
    waiver_section = ""
    if risk["icf_waiver_eligible"] and design_code == "sr_ma":
        waiver_section = """
---

## TÀI LIỆU 9 — ĐỀ NGHỊ MIỄN ICF (ICF Waiver — chỉ cho SR/MA hoặc dữ liệu thứ cấp)

> Kích hoạt vì thiết kế SR/MA không tiếp xúc người tham gia trực tiếp.
> `[CẦN BÁC SĨ XÁC NHẬN: nghiên cứu của tôi đủ điều kiện miễn ICF không?]`

```
YÊU CẦU MIỄN THỦ TỤC ĐỒNG THUẬN (ICF Waiver Request) — DRAFT Phiên bản 1.0
═══════════════════════════════════════════════════════════════
Căn cứ: TT43/2024/TT-BYT Điều 15 · Helsinki WMA 2013 §29
Tên đề tài: {study_name}
Chủ nhiệm: [CẦN BỔ SUNG]
Ngày: {run_date_short}

CƠ SỞ XIN MIỄN (phải thỏa CẢ 4 điều kiện):
☑ SR/MA dùng dữ liệu đã công bố — không truy ngược cá nhân
☑ Không có can thiệp/thủ thuật bổ sung lên người tham gia
☑ Rủi ro không vượt nguy cơ tối thiểu từ dữ liệu đã ẩn danh
☑ Không khả thi yêu cầu ICF từ tác giả gốc (nghiên cứu đã công bố)

ĐẢM BẢO BẢO MẬT:
Loại dữ liệu: Tóm tắt/bảng đã công bố trong y văn — không có PII
Mã hóa: Không cần (không có PII)
Quyền truy cập: Chỉ nhóm nghiên cứu
Kế hoạch hủy: Lưu trữ 5 năm sau công bố theo quy định

CỜ ĐỎ (bất kỳ → PHẢI lấy ICF đầy đủ):
☐ Có dữ liệu cá nhân nhận dạng được → ICF bắt buộc
☐ Có tiếp xúc người tham gia → ICF bắt buộc

Chữ ký chủ nhiệm: [CẦN KÝ]   |   Ngày: ___/___/{year}
"DRAFT — Cần Hội đồng Đạo đức phê duyệt."
═══════════════════════════════════════════════════════════════
```
""".format(study_name=study_name, run_date_short=run_date[:10], year=_YEAR)

    # 18 WHO Registration fields
    who_design_type_map = {
        "rct": "Interventional", "cohort": "Observational", "case_control": "Observational",
        "cross_sectional": "Observational", "diagnostic": "Observational", "sr_ma": "Not Applicable",
    }
    who_primary_purpose_map = {
        "rct": "Treatment", "cohort": "Observational", "case_control": "Epidemiology",
        "cross_sectional": "Epidemiology", "diagnostic": "Diagnostic", "sr_ma": "Health Services Research",
    }

    ncts_for_ref = " · ".join([f"[{t['nct_id']}]({t['url']})" for t in ct_trials[:3]]) if ct_trials else "[Không tìm được thử nghiệm tương tự]"

    # PROSPERO template (chỉ SR/MA)
    prospero_section = ""
    if design_code == "sr_ma":
        prospero_section = """
---

## PHỤ LỤC — BẢN ĐĂNG KÝ PROSPERO (SR/MA — bắt buộc)

> PROSPERO: https://www.crd.york.ac.uk/prospero/ | Điền TRƯỚC khi bắt đầu tìm kiếm.

```
PROSPERO Registration Draft
═══════════════════════════
Tiêu đề: A systematic review and meta-analysis of [topic in English]
Ngôn ngữ cung cấp: English

Review question: [CẦN — từ PICO G0]
Searches: PubMed, Cochrane CENTRAL, Embase, Web of Science, grey literature
Types of study included: [RCT / Observational — tùy câu hỏi]
Population: [CẦN — PICO P]
Intervention/Exposure: [CẦN — PICO I/E]
Comparator: [CẦN — PICO C]
Outcomes: Primary — [CẦN — PICO O] | Secondary — [CẦN]
Risk of bias: [RoB 2 / ROBINS-I / QUADAS-2]
Reporting standard: PRISMA 2020
Start date: [CẦN]
Expected completion: [CẦN]
Co-investigators: [CẦN]
Funding: [CẦN]
Conflicts of interest: [CẦN]
Link to protocol (pre-print): [sẽ bổ sung sau]
```
"""

    doc = f"""# A3 — HỒ SƠ ĐẠO ĐỨC & ĐĂNG KÝ NGHIÊN CỨU | {study_name}
> Tạo tự động: {run_date} | Theo Helsinki 2013 · ICH-GCP E6(R3) · TT43/2024/TT-BYT · Luật 91/2025/QH15
> [BẢN NHÁP TỰ ĐỘNG — DRAFT Phiên bản 1.0 chờ phê duyệt]
> Cần bác sĩ/chủ nhiệm kiểm chứng, chỉnh sửa và ký trước khi nộp Hội đồng đạo đức.

---

## TỔNG QUAN G2

| Mục | Thông tin |
|-----|-----------|
| Thiết kế | {design_primary} |
| Mức nguy cơ | **{risk["risk_level"]}** |
| Lộ trình IRB | **{risk["irb_route"]}** |
| Đăng ký nghiên cứu | {irb_required} — {risk["register_where"]} |
| ICF bắt buộc | {"✅ Có" if risk["icf_required"] else "⚠ Có thể miễn — xem Tài liệu 9"} |
| Chuẩn báo cáo | {reporting_std} |

{f"> {risk['_fallback_warning']}" + chr(10) + chr(10) if risk.get("_fallback_warning") else ""}---

## TÀI LIỆU 1 — ĐƠN XIN PHÊ DUYỆT IRB

```
══════════════════════════════════════════════════════════════
     ĐƠN XIN PHÊ DUYỆT NGHIÊN CỨU Y SINH HỌC
     (DRAFT Phiên bản 1.0 — {run_date[:10]})
══════════════════════════════════════════════════════════════

Kính gửi: Hội đồng Đạo đức Nghiên cứu Y sinh
          [TÊN ĐƠN VỊ — CẦN BỔ SUNG]

Từ:  Chủ nhiệm đề tài: [CẦN BỔ SUNG]
     Chức vụ: [CẦN BỔ SUNG]
     Đơn vị: [CẦN BỔ SUNG]
     Điện thoại: [CẦN BỔ SUNG] | Email: [CẦN BỔ SUNG]

TÊN ĐỀ TÀI: {topic}

THÔNG TIN TỔNG QUAN:
  Loại nghiên cứu: {design_primary}
  Mức nguy cơ (tự đánh giá): {risk["risk_level"]}
  Lộ trình xét duyệt đề nghị: {risk["irb_route"]}
  Dân số tham gia: [CẦN BỔ SUNG — từ PICO P]
  Cỡ mẫu dự kiến: {n_display}
  Thời gian nghiên cứu: [CẦN — từ ___/___/{_YEAR} đến ___/___/____]
  Nguồn tài trợ: [CẦN BỔ SUNG / "Không có tài trợ bên ngoài"]
  Xung đột lợi ích (COI): [CẦN KHAI BÁO — xem Tài liệu 8]
  Đăng ký nghiên cứu: [CẦN — {risk["register_where"]}]

CAM KẾT:
  Chúng tôi cam kết thực hiện nghiên cứu theo Tuyên ngôn Helsinki
  (WMA 2013), ICH-GCP E6(R3), TT43/2024/TT-BYT, Luật BVDLCN
  91/2025/QH15 và NĐ 356/2025/NĐ-CP.

Kèm theo hồ sơ:
  ☐ Tài liệu 1: Đơn xin phê duyệt (file này)
  ☐ Tài liệu 2: Tóm tắt đề cương (lay summary ≤1 trang)
  ☐ Tài liệu 3: Bảng rủi ro–lợi ích
  ☐ Tài liệu 4: ICF tiếng Việt
  ☐ Tài liệu 5: ICF tiếng Anh
  ☐ Tài liệu 6: Kế hoạch Quản lý Dữ liệu (DMP)
  ☐ Tài liệu 7: Checklist nộp Hội đồng
  ☐ Tài liệu 8: Khai báo COI + Tài trợ + AI
  ☐ Đề cương đầy đủ (từ G1)
  ☐ CV chủ nhiệm + nghiên cứu viên chính

Chủ nhiệm đề tài:
___________________________  Ký, ghi rõ họ tên     Ngày: ___/___/{_YEAR}

Xác nhận Trưởng đơn vị:
___________________________  Ký, ghi rõ họ tên     Ngày: ___/___/{_YEAR}

"DRAFT — Chưa nộp — Cần chỉnh sửa và ký trước khi nộp Hội đồng."
══════════════════════════════════════════════════════════════
```

---

## TÀI LIỆU 2 — TÓM TẮT ĐỀ CƯƠNG CHO HỘI ĐỒNG (lay summary ≤1 trang A4)

```
TÓM TẮT ĐỀ CƯƠNG (DRAFT — ngôn ngữ hành chính)
─────────────────────────────────────────────────────────────

1. VẤN ĐỀ NGHIÊN CỨU VÀ LÝ DO CẦN THIẾT:
   {topic}
   Bằng chứng hiện có (từ PubMed): {n_sr} SR/MA · {n_rct} RCT (mức: {evidence_level}).
   [CẦN BỔ SUNG: lý do cần nghiên cứu thêm tại bối cảnh Việt Nam]

2. MỤC TIÊU CỤ THỂ:
   2.1 [CẦN — Mục tiêu 1, từ PICO G0]
   2.2 [CẦN — Mục tiêu 2 nếu có]

3. ĐỐI TƯỢNG THAM GIA:
   Tiêu chí chọn: [CẦN — từ PICO P, G0]
   Tiêu chí loại: [CẦN — từ G1 SAP §1]
   Cỡ mẫu dự kiến: {n_display}

4. PHƯƠNG PHÁP VÀ QUY TRÌNH:
   Thiết kế: {design_primary}
   Chuẩn báo cáo: {reporting_std}
   Nơi thực hiện: [CẦN — Đơn vị/bệnh viện]
   Quy trình: [CẦN MÔ TẢ ngắn gọn theo PICO]

5. RỦI RO TIỀM TÀNG VÀ BIỆN PHÁP BẢO VỆ:
   Mức nguy cơ tổng thể: {risk["risk_level"]}
   [Chi tiết xem Bảng rủi ro–lợi ích — Tài liệu 3]

6. LỢI ÍCH MONG ĐỢI:
   {risk["benefits"]}

7. BẢO MẬT DỮ LIỆU:
   Dữ liệu mã hóa, khử định danh theo Luật 91/2025/QH15.
   Không lưu PII; bảng liên kết lưu riêng có mật khẩu.

8. KẾT QUẢ ĐẦU RA DỰ KIẾN:
   ☐ Bài báo đăng tạp chí quốc tế/trong nước có phản biện
   ☐ Luận văn/báo cáo nghiên cứu
   ☐ Báo cáo khuyến nghị cho đơn vị/chính sách
   [CẦN BỔ SUNG tạp chí/hội nghị mục tiêu]
─────────────────────────────────────────────────────────────
"DRAFT — Cần bác sĩ/chủ nhiệm kiểm chứng trước khi nộp."
```

---

## TÀI LIỆU 3 — BẢNG ĐÁNH GIÁ RỦI RO–LỢI ÍCH

**Phân loại nguy cơ tổng thể: {risk["risk_level"]}**
**Lộ trình xét duyệt đề nghị: {risk["irb_route"]}**

{risk_table_str}

| | **Lợi ích bù đắp** |
|---|---|
| Trực tiếp với NTG | [CẦN BỔ SUNG — xác định xem có lợi ích trực tiếp không] |
| Cộng đồng/y tế | {risk["benefits"]} |

**Kết luận:** Lợi ích dự kiến của nghiên cứu **vượt trội** nguy cơ tiềm tàng.
Mọi rủi ro đều được giảm thiểu bằng biện pháp cụ thể.
`[CẦN BÁC SĨ XÁC NHẬN bảng rủi ro phù hợp với đề tài thật]`

---

## TÀI LIỆU 4 — PHIẾU ĐỒNG Ý THAM GIA NGHIÊN CỨU (ICF — Tiếng Việt)

```
══════════════════════════════════════════════════════════════
   PHIẾU ĐỒNG Ý THAM GIA NGHIÊN CỨU
   DRAFT Phiên bản 1.0 — Ngày soạn: {run_date[:10]}
   [Phiên bản phê duyệt sẽ có số IRB — CẦN BỔ SUNG]
══════════════════════════════════════════════════════════════

TÊN ĐỀ TÀI: {topic}
Đơn vị thực hiện: [CẦN BỔ SUNG]
Chủ nhiệm đề tài: [CẦN BỔ SUNG]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHẦN THÔNG TIN CHO NGƯỜI THAM GIA
(Xin đọc kỹ trước khi quyết định tham gia)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. MỤC ĐÍCH NGHIÊN CỨU
   Chúng tôi kính mời anh/chị tham gia nghiên cứu nhằm:
   [CẦN MÔ TẢ bằng ngôn ngữ đơn giản — không dùng thuật ngữ khó]
   Ví dụ: "Tìm hiểu xem thuốc/can thiệp X có giúp cải thiện tình
   trạng [bệnh] ở người bệnh như anh/chị không."

   Nghiên cứu do [đơn vị] thực hiện với sự hỗ trợ của [tài trợ
   nếu có]. Cỡ mẫu dự kiến: khoảng {n_display_inline} người tham gia
   tại [nơi thực hiện].

   THAM GIA LÀ HOÀN TOÀN TỰ NGUYỆN. Quyết định không tham gia
   KHÔNG ảnh hưởng đến chất lượng chăm sóc y tế của anh/chị.

2. QUY TRÌNH THỰC HIỆN NẾU ĐỒNG Ý THAM GIA
   Nếu anh/chị đồng ý, chúng tôi sẽ yêu cầu:
   ☐ Bước 1: [CẦN MÔ TẢ — ví dụ: ký phiếu đồng thuận này]
   ☐ Bước 2: [CẦN — ví dụ: trả lời bộ câu hỏi ~20 phút]
   ☐ Bước 3: [CẦN — ví dụ: lấy 5 mL máu tĩnh mạch]
   ☐ Bước 4: [CẦN — ví dụ: tái khám sau 3 tháng / 6 tháng]

   Tổng thời gian tham gia ước tính: [CẦN — ví dụ: 12 tháng]
   Số lần đến cơ sở y tế: [CẦN — ví dụ: 3 lần]

   Chúng tôi sẽ cố gắng lên lịch hẹn trùng với lần tái khám
   thường quy để giảm bất tiện cho anh/chị.

3. RỦI RO VÀ BẤT TIỆN CÓ THỂ XẢY RA
   {chr(10).join('   • ' + r[0] + ': ' + r[2] + ' → ' + r[3][:80] for r in risk["risks"])}

   Nếu có bất kỳ vấn đề sức khỏe nào liên quan đến nghiên cứu,
   xin liên hệ ngay chủ nhiệm đề tài (số điện thoại bên dưới).
   Chi phí điều trị biến cố liên quan nghiên cứu: [CẦN XÁC NHẬN].

4. LỢI ÍCH KỲ VỌNG
   Lợi ích trực tiếp: [CẦN — ví dụ: được theo dõi sức khỏe sát
   hơn, được tiếp cận thuốc/can thiệp mới (nếu RCT)]
   Lợi ích cộng đồng: {risk["benefits"]}

   Chúng tôi KHÔNG đảm bảo lợi ích cá nhân từ việc tham gia.
   Anh/chị sẽ nhận được tóm tắt kết quả nghiên cứu khi hoàn tất.

5. BẢO MẬT THÔNG TIN CÁ NHÂN
   Thông tin cá nhân của anh/chị được bảo vệ theo
   Luật BVDLCN 91/2025/QH15:

   ✅ Dữ liệu được mã hóa và lưu tại [CẦN — máy chủ bảo mật/
      ổ cứng mã hóa tại đơn vị]
   ✅ Chỉ nhóm nghiên cứu được phép truy cập dữ liệu danh tính
   ✅ Kết quả công bố dùng dữ liệu TỔNG HỢP — KHÔNG tiết lộ danh tính
   ✅ Dữ liệu nhận dạng được xóa/ẩn danh hóa trong vòng [CẦN] năm
      sau khi kết thúc nghiên cứu theo quy định lưu trữ y tế
   ✅ Trong trường hợp rò rỉ, anh/chị sẽ được thông báo trong 72 giờ

   Anh/chị có quyền yêu cầu xem, sửa hoặc xóa dữ liệu của mình
   (trước khi chúng tôi tiến hành phân tích).

6. QUYỀN TỰ NGUYỆN VÀ RÚT LUI
   ✅ Tham gia là HOÀN TOÀN TỰ NGUYỆN
   ✅ Anh/chị có thể KHÔNG ĐỒNG Ý tham gia mà KHÔNG ảnh hưởng
      đến dịch vụ y tế đang nhận
   ✅ Anh/chị có thể RÚT LUI bất kỳ lúc nào, không cần giải thích
   ✅ Nếu rút lui, dữ liệu đã thu thập: ☐ sẽ bị xóa ☐ vẫn dùng
      (do tính ẩn danh — ghi rõ chính sách) [CẦN XÁC NHẬN]

7. THÔNG TIN LIÊN HỆ
   ┌─────────────────────────────────────────────────────────┐
   │ Thắc mắc về nghiên cứu:                                │
   │   Chủ nhiệm đề tài: [CẦN BỔ SUNG]                     │
   │   Điện thoại: [CẦN BỔ SUNG]  Email: [CẦN BỔ SUNG]     │
   │                                                        │
   │ Thắc mắc về quyền của người tham gia:                  │
   │   Hội đồng Đạo đức: [CẦN — Tên HĐ cơ sở]              │
   │   Điện thoại: [CẦN BỔ SUNG]                           │
   └─────────────────────────────────────────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHẦN KÝ — BẢN NÀY DÀNH CHO NGƯỜI THAM GIA (GIỮ LẠI)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tôi đã đọc / được giải thích thông tin bên trên và có đủ thời
gian để đặt câu hỏi. Tôi ĐỒNG Ý TỰ NGUYỆN tham gia nghiên cứu.

Họ tên người tham gia: _______________
Ký tên: _______________  Ngày: ___/___/{_YEAR}

Họ tên người chứng kiến (nếu cần): _______________
Ký tên: _______________  Ngày: ___/___/{_YEAR}

Họ tên nghiên cứu viên: _______________
Ký tên: _______________  Ngày: ___/___/{_YEAR}

"Tài liệu này do AI hỗ trợ soạn thảo [DRAFT Phiên bản 1.0].
 Cần chủ nhiệm kiểm chứng và HĐ đạo đức phê duyệt trước khi dùng."
══════════════════════════════════════════════════════════════
```

---

## TÀI LIỆU 5 — ICF TIẾNG ANH (English Translation — for journal submission)

```
══════════════════════════════════════════════════════════════
   INFORMED CONSENT FORM (ENGLISH TRANSLATION)
   DRAFT Version 1.0 — Date: {run_date[:10]}
   "English translation of Vietnamese ICF — for journal submission only."
══════════════════════════════════════════════════════════════

STUDY TITLE: {topic}
Institution: [TO BE COMPLETED]
Principal Investigator: [TO BE COMPLETED]

1. PURPOSE
   You are invited to participate in a study that aims to:
   [TO BE COMPLETED — plain language, no jargon]
   Estimated participants: [TO BE COMPLETED — from G3]
   Location: [TO BE COMPLETED]
   PARTICIPATION IS ENTIRELY VOLUNTARY.

2. PROCEDURES
   ☐ Step 1: [TO BE COMPLETED]
   ☐ Step 2: [TO BE COMPLETED]
   Estimated time commitment: [TO BE COMPLETED]

3. RISKS AND DISCOMFORTS
   {chr(10).join('   • ' + r[0] + ' (' + r[1] + ' probability / ' + r[2] + ' severity): ' + r[3][:80] for r in risk["risks"])}

4. POTENTIAL BENEFITS
   [TO BE COMPLETED — include both direct and community benefits]

5. CONFIDENTIALITY
   Data encrypted per Vietnamese Personal Data Protection Law
   No. 91/2025/QH15. Results published in aggregate form only.

6. VOLUNTARY PARTICIPATION AND WITHDRAWAL
   Participation is voluntary. You may withdraw at any time
   without affecting your medical care.

7. CONTACTS
   Investigator: [TO BE COMPLETED] | Email: [TO BE COMPLETED]
   Ethics Committee: [TO BE COMPLETED]

──────────────────────────────────────────────────────────────
CONSENT SIGNATURE (PARTICIPANT'S COPY)
I have read the above and agree to participate voluntarily.

Participant: _______________  Date: ___/___/{_YEAR}
Witness (if applicable): _______________ Date: ___/___/{_YEAR}
Investigator: _______________  Date: ___/___/{_YEAR}
══════════════════════════════════════════════════════════════
```

---

## TÀI LIỆU 6 — KẾ HOẠCH QUẢN LÝ DỮ LIỆU (DMP — Luật 91/2025/QH15)

```
KẾ HOẠCH QUẢN LÝ DỮ LIỆU — Cấp IRB
Đề tài: {study_name} | Phiên bản: 1.0 | Ngày: {run_date[:10]}
─────────────────────────────────────────────────────────────

1. LOẠI DỮ LIỆU THU THẬP:
   ☐ Nhân khẩu học (tuổi, giới, dân tộc) — KHÔNG lưu tên/CMND
   ☐ Lâm sàng (bệnh sử, kết quả khám) — mã hóa theo ID
   ☐ Cận lâm sàng (xét nghiệm, hình ảnh) — mã hóa
   ☐ Kết quả điều tra/khảo sát — ẩn danh hoặc giả danh
   ☐ Dữ liệu thứ cấp (hồ sơ bệnh án) — mã giả danh
   [CẦN BÁC SĨ LIỆT KÊ CỤ THỂ theo đề tài]

2. THU THẬP:
   Công cụ: ☐ REDCap ☐ Google Forms (institutional) ☐ Phiếu giấy
            ☐ [CẦN XÁC NHẬN]
   Phân quyền truy cập: Chỉ nhóm nghiên cứu được cấp phép
   Phê duyệt quyền: Chủ nhiệm đề tài

3. KHỬ ĐỊNH DANH:
   Phương pháp: Thay thế tên/CMND bằng ID nghiên cứu (vd: PT001)
   Bảng liên kết ID–tên: Lưu riêng, mã hóa AES-256, mật khẩu
   mạnh (≥12 ký tự), chỉ chủ nhiệm giữ
   Ngưỡng k-ẩn danh: ≥5 (nhóm nhỏ sẽ nhóm lại trước công bố)

4. LƯU TRỮ:
   Nơi lưu: [CẦN — máy chủ nội bộ / OneDrive institutional
             / ổ cứng mã hóa tại [đơn vị]]
   Bảo mật: AES-256 · mật khẩu cấp người dùng · VPN (nếu từ xa)
   Sao lưu: [CẦN — ví dụ: hàng ngày/tuần, 2 bản độc lập]
   Thời gian lưu: ___ năm sau kết thúc nghiên cứu
                  (theo TT38/2018/TT-BYT về lưu trữ hồ sơ y tế)

5. CHIA SẺ / MỞ DỮ LIỆU:
   ☐ Không chia sẻ (lý do: [CẦN])
   ☐ Chia sẻ theo yêu cầu hợp lý (DTA cần ký trước)
   ☐ Mở hoàn toàn sau ẩn danh hóa (tại: [CẦN — OSF/Zenodo...])
   [CẦN BÁC SĨ CHỌN VÀ BIỆN MINH]

6. XỬ LÝ VI PHẠM DỮ LIỆU:
   Theo NĐ 356/2025/NĐ-CP Điều 23:
   ∎ Phát hiện vi phạm → báo cáo nội bộ trong 24 giờ
   ∎ Thông báo cơ quan bảo vệ dữ liệu trong 72 giờ
   ∎ Thông báo người tham gia bị ảnh hưởng ngay khi xác nhận
   ∎ Khắc phục và điều tra nguyên nhân, lưu hồ sơ xử lý
   Quy trình: [CẦN BỔ SUNG quy trình cụ thể của đơn vị]

7. CUỐI NGHIÊN CỨU:
   ∎ Dữ liệu nhận dạng: xóa/hủy vật lý trong ___ tháng
   ∎ Dữ liệu ẩn danh hóa: lưu theo quy định lưu trữ y tế
   ∎ Backup: xóa an toàn (overwrite 3 lần tiêu chuẩn DoD)
─────────────────────────────────────────────────────────────
"DRAFT — Cần chủ nhiệm kiểm chứng và DMP Luật 91/2025 hoàn chỉnh."
```

---

## TÀI LIỆU 7 — CHECKLIST NỘP HỘI ĐỒNG ĐẠO ĐỨC (theo TT43/2024/TT-BYT)

```
CHECKLIST HỒ SƠ NỘP HỘI ĐỒNG ĐẠO ĐỨC
Đề tài: {study_name} | Ngày chuẩn bị: {run_date[:10]}
─────────────────────────────────────────────────────────────

HỒ SƠ BẮT BUỘC:
☐ Đơn xin phê duyệt (Tài liệu 1) — ký tên chủ nhiệm + trưởng đơn vị
☐ Tóm tắt đề cương ≤1 trang (Tài liệu 2)
☐ Đề cương đầy đủ (từ G1 — A2 Protocol Design)
☐ Bảng rủi ro–lợi ích (Tài liệu 3) — với phân loại mức nguy cơ
☐ ICF tiếng Việt (Tài liệu 4) — 7 mục đủ
☐ CV chủ nhiệm đề tài (cập nhật ≤ 2 năm)
☐ CV nghiên cứu viên chính (nếu có)
☐ Khai báo COI + AI (Tài liệu 8)
☐ Kế hoạch Quản lý Dữ liệu (Tài liệu 6)

HỒ SƠ BỔ SUNG (theo loại NC):
☐ [RCT / can thiệp]: Hồ sơ an toàn DSMB (an-toan-nghien-cuu)
☐ [RCT]: Bằng chứng đã đăng ký / kế hoạch đăng ký trước tuyển
☐ [Can thiệp thuốc]: Thông tin sản phẩm / IB (Investigator Brochure)
☐ [Dữ liệu thứ cấp]: Văn bản chấp thuận cung cấp dữ liệu
☐ [Nhóm dễ tổn thương — trẻ em, thai phụ, người mất NLHV]:
    ICF người giám hộ + biện pháp bảo vệ đặc biệt
☐ [Dùng dữ liệu di truyền/nhạy cảm]: ICF đặc biệt

SỐ BẢN NỘP: ___ [CẦN XÁC NHẬN tại Hội đồng đạo đức cơ sở]
HÌNH THỨC: ☐ Bản cứng ☐ Điện tử ☐ Cả hai

LỘ TRÌNH XÉT DUYỆT DỰ KIẾN: {risk["irb_route"]}
  Full review: thường 4–8 tuần
  Expedited: thường 2–4 tuần
  Exempt: thường 1–2 tuần (xác nhận từ Hội đồng)

SAU KHI NHẬN SỐ PHÊ DUYỆT:
  ∎ Cập nhật số IRB vào ICF (ICF sẽ có phiên bản 1.0 chính thức)
  ∎ Cung cấp số IRB + ngày phê duyệt để hệ thống ghi G2_STATUS: LOCKED
  ∎ Chỉ sau khi G2 LOCKED mới được bắt đầu thu thập dữ liệu thật
─────────────────────────────────────────────────────────────
```

---

## TÀI LIỆU 8 — KHAI BÁO COI + TÀI TRỢ + AI

```
KHAI BÁO XUNG ĐỘT LỢI ÍCH, TÀI TRỢ VÀ SỬ DỤNG AI
(Dựa theo ICMJE Form — phiên bản rút gọn cho IRB)
─────────────────────────────────────────────────────────────
Tên chủ nhiệm: [CẦN BỔ SUNG]
Chức vụ: [CẦN BỔ SUNG] | Đơn vị: [CẦN BỔ SUNG]
Ngày khai báo: {_TODAY}

A. XUNG ĐỘT LỢI ÍCH TÀI CHÍNH (12 tháng gần nhất):
☐ Không có
☐ Có → [Liệt kê: Tên công ty · Loại quan hệ (cổ phần/tư vấn/
         thù lao/tài trợ hội nghị) · Giá trị (nếu phải khai)]

B. XUNG ĐỘT LỢI ÍCH PHI TÀI CHÍNH:
☐ Không có
☐ Có → [Quan hệ cá nhân với người được nghiên cứu / lợi ích
         học thuật (thăng tiến/bằng sáng chế) / quan điểm đối nghịch]

C. NGUỒN TÀI TRỢ:
  Tài trợ chính: [CẦN BỔ SUNG — "Không có tài trợ bên ngoài" nếu đúng]
  Tài trợ bổ sung: [CẦN BỔ SUNG]
  Số hợp đồng (nếu có): [CẦN BỔ SUNG]

D. VAI TRÒ NHÀ TÀI TRỢ:
  Nhà tài trợ có can thiệp vào:
  ☐ Thiết kế nghiên cứu: ☐ Có ☐ Không
  ☐ Thu thập / phân tích dữ liệu: ☐ Có ☐ Không
  ☐ Báo cáo / quyết định công bố: ☐ Có ☐ Không

E. SỬ DỤNG CÔNG CỤ AI TRONG NGHIÊN CỨU:
  ☐ Không sử dụng công cụ AI nào
  ☐ Có sử dụng:
    Tên công cụ: Claude AI (EBM Copilot) · [CẦN BỔ SUNG thêm nếu có]
    Mục đích: Hỗ trợ soạn hồ sơ G2 · tổng quan y văn · thống kê
    Người kiểm tra đầu ra: [CẦN — tên nghiên cứu viên phụ trách]

  XÁC NHẬN (bắt buộc): "Tôi đã kiểm chứng TOÀN BỘ nội dung AI
  hỗ trợ. Mọi số liệu, trích dẫn và kết quả đã được xác minh
  từ nguồn gốc. AI KHÔNG được liệt kê là tác giả." [ICMJE 2023]

Chữ ký chủ nhiệm: _______________  Ngày: ___/___/{_YEAR}
[Mỗi đồng tác giả cần khai báo COI riêng theo mẫu ICMJE]
─────────────────────────────────────────────────────────────
"DRAFT — Cần chủ nhiệm điền và ký trước khi nộp."
```
{waiver_section}
---

## ĐĂNG KÝ NGHIÊN CỨU — 18 TRƯỜNG WHO TRIAL REGISTRATION DATA SET

**Nơi đăng ký đề nghị:** {risk["register_where"]}
**Thời điểm:** {risk["registration"]}

**Nghiên cứu tương tự đã đăng ký (từ ClinicalTrials.gov API):**
{ct_table_str}
*(Tham chiếu NCT: {ncts_for_ref})*

```
WHO Trial Registration Data Set — DRAFT Phiên bản 1.0
═══════════════════════════════════════════════════════════════

Trường 1  — Primary registry & Trial ID:
            [CẦN — sẽ có sau khi đăng ký: NCT_______ / ANZCTR_____]

Trường 2  — Date of registration in primary registry:
            [CẦN — ngày đăng ký thành công]

Trường 3  — Secondary IDs (nếu có):
            Số phê duyệt IRB: [CẦN sau khi nhận]
            PROSPERO (nếu SR): [CẦN]

Trường 4  — Source(s) of monetary or material support:
            [CẦN BỔ SUNG — tên tổ chức tài trợ hoặc "None"]

Trường 5  — Primary sponsor contact:
            [CẦN — Tên chủ nhiệm, Đơn vị, Email, Điện thoại]

Trường 6  — Secondary sponsor / contact (nếu có):
            [CẦN BỔ SUNG]

Trường 7  — Public title (tiêu đề công khai, dễ hiểu):
            [CẦN BỔ SUNG — ngôn ngữ không chuyên]

Trường 8  — Scientific title (tiêu đề khoa học):
            {topic}

Trường 9  — Countries of recruitment:
            Vietnam (VN) [CẦN BỔ SUNG tỉnh/tỉnh thành]

Trường 10 — Health condition(s) studied:
            [CẦN — từ PICO P: ví dụ Heart failure with preserved EF / HFpEF]

Trường 11 — Intervention(s):
            [CẦN — từ PICO I: ví dụ SGLT2 inhibitor (empagliflozin 10mg OD)]
            Comparator: [CẦN — từ PICO C]

Trường 12 — Key inclusion criteria:
            [CẦN BỔ SUNG — từ SAP §1 / PICO P]

Trường 13 — Key exclusion criteria:
            [CẦN BỔ SUNG — từ SAP §1]

Trường 14 — Study type:
            {who_design_type_map.get(design_code, "Observational")} ·
            {who_primary_purpose_map.get(design_code, "Other")} ·
            {"Randomized" if design_code == "rct" else "Non-randomized"} ·
            {"Blinded" if design_code == "rct" else "Open label"}

Trường 15 — Anticipated date of first enrolment:
            [CẦN — sau G2 LOCKED: ___/___/{_YEAR}]

Trường 16 — Target sample size:
            {n_display}

Trường 17 — Recruitment status (tại thời điểm đăng ký):
            Not yet recruiting

Trường 18 — Primary outcome:
            [CẦN — từ PICO O đã ấn định ở G0]

            Key secondary outcomes:
            [CẦN — từ SAP §2]
═══════════════════════════════════════════════════════════════
"DRAFT — Điền trường còn [CẦN] trước khi gửi đăng ký."
```
{prospero_section}
---

## CƠ CHẾ MỞ KHÓA G2

```
╔══════════════════════════════════════════════════════════════╗
║         ĐỂ MỞ CỔNG G2 — bác sĩ cung cấp:                   ║
╠══════════════════════════════════════════════════════════════╣
║  1. Số phê duyệt IRB: ___ (do Hội đồng đạo đức cấp)         ║
║  2. Ngày phê duyệt:   ___/___/20___                         ║
║  3. Phiên bản ICF phê duyệt: 1.0 (hoặc phiên bản đã sửa)   ║
║  4. Nếu RCT: số đăng ký NCT_____ hoặc tương đương           ║
╠══════════════════════════════════════════════════════════════╣
║  → Hệ thống ghi:                                            ║
║    G2_STATUS: LOCKED                                        ║
║    G2_IRB_NUMBER: ___                                       ║
║    G2_APPROVAL_DATE: ___                                    ║
║    G2_ICF_VERSION: ___                                      ║
║    G2_REGISTRATION: ___                                     ║
╠══════════════════════════════════════════════════════════════╣
║  Sau khi LOCKED:                                            ║
║  • G3 (cỡ mẫu), G4 (SAP lock) chạy song song               ║
║  • G5 (thu thập dữ liệu THẬT) CHỈ MỞ khi G2=LOCKED         ║
║  Khi chưa LOCKED: KHÔNG thu thập dữ liệu người tham gia     ║
╚══════════════════════════════════════════════════════════════╝
```

---

## TIÊU CHÍ QUA CỔNG G2 (AI side — tự kiểm)

```
☑ 8 tài liệu IRB đã soạn đầy đủ (Tài liệu 1–8)
☑ ICF tiếng Việt đủ 7 mục Helsinki (MỤC 1–7)
☑ ICF tiếng Anh (dịch trung thành)
☑ Bảng rủi ro–lợi ích có phân loại mức nguy cơ
☑ DMP theo Luật 91/2025/QH15 (7 mục)
☑ Khai báo COI + AI đầy đủ
☑ 18 trường WHO Trial Registration soạn sẵn
☑ ClinicalTrials.gov search: prior art thật
☑ Không PII trong bất kỳ tài liệu nào
☑ Không bịa số phê duyệt/mã đăng ký
☑ Mọi tài liệu đánh dấu "DRAFT — chờ phê duyệt"
☑ Disclaimer cuối mỗi tài liệu
☐ Số IRB thật → bác sĩ nộp + nhận [CHỜ BÁC SĨ]
☐ Số đăng ký NCT/PROSPERO → bác sĩ đăng ký [CHỜ BÁC SĨ]
☐ G2_STATUS: LOCKED → sau khi nhận số IRB thật [CHỜ BÁC SĨ]
```

**Bước tiếp theo:**
1. In hồ sơ, ký → nộp Hội đồng Đạo đức (lộ trình: {risk["irb_route"]})
2. Đăng ký nghiên cứu: {risk["register_where"]}
3. Khi nhận số IRB → cung cấp cho hệ thống → G2 LOCKED
4. Chạy G3 song song: `python tools/run_g3_auto.py --study {study_name}`

---

*[BẢN NHÁP TỰ ĐỘNG — DRAFT Phiên bản 1.0] · Cần bác sĩ kiểm chứng.*
"""
    return doc


# ════════════════════════════════════════════════════════════════════════════
# 4. GUARDRAIL R1-R7 CHO G2
# ════════════════════════════════════════════════════════════════════════════

def guardrail_check_g2(artifact: str) -> dict:
    errors, warnings = [], []

    # R1 — Không PII
    pii_patterns = [r'\b\d{9,12}\b',  # CMND/CCCD
                    r'\b\d{2}/\d{2}/\d{4}\b(?=\s+sinh)',  # ngày sinh rõ
                    r'họ tên:\s+[A-ZÀ-Ỹ][a-zà-ỹ]+']
    pii_found = False
    for pat in pii_patterns:
        if re.search(pat, artifact):
            pii_found = True; break
    if pii_found:
        errors.append("R1 🔴 Phát hiện PII tiềm năng — kiểm tra và xóa")
    else:
        warnings.append("R1 ✅ Không phát hiện PII")

    # R2 — Không bịa số phê duyệt (chỉ flag nếu số xuất hiện dưới dạng "đã được cấp", không phải trong bảng prior art)
    # NCT từ ClinicalTrials.gov search là THẬT → không flag; chỉ flag nếu có vẻ tự gán cho đề tài này
    fake_irb = re.search(r'Mã nghiên cứu:\s+(?!.*\[CẦN)([A-Z]{3,}\d{4,})', artifact)
    if fake_irb:
        errors.append(f"R2 🔴 Số nghiên cứu có vẻ bịa đặt: '{fake_irb.group(1)}' — dùng [CẦN BỔ SUNG]")
    else:
        warnings.append("R2 ✅ Không phát hiện số phê duyệt bịa (NCT trong bảng prior art là THẬT từ API)")

    # R3 — Không ghi APPROVED_EXTERNALLY; không tự claim đã LOCKED thật
    # G2_STATUS: LOCKED trong template hướng dẫn là hợp lệ; chỉ flag nếu claim thật
    if "APPROVED_EXTERNALLY" in artifact:
        errors.append("R3 🔴 Không được ghi APPROVED_EXTERNALLY — cần bằng chứng ngoài hệ thống")
    elif re.search(r'Trạng\s*thái\s*hiện\s*tại:\s*LOCKED', artifact, re.IGNORECASE):
        errors.append("R3 🔴 Không được tự claim G2 đã LOCKED — cần số IRB thật từ bác sĩ")
    else:
        # G2_STATUS: LOCKED trong khối hướng dẫn/template là hợp lệ — không flag
        warnings.append("R3 ✅ Không tự claim APPROVED/LOCKED (LOCKED trong template là hướng dẫn bác sĩ)")

    # R4 — Có nhãn DRAFT trên tài liệu
    draft_count = artifact.count("DRAFT")
    if draft_count >= 5:
        warnings.append(f"R4 ✅ Nhãn DRAFT đủ ({draft_count} lần)")
    else:
        errors.append(f"R4 🔴 Thiếu nhãn DRAFT (chỉ {draft_count} lần — cần ≥5)")

    # R5 — [CẦN BỔ SUNG] đủ cho các trường trống
    can_count = artifact.count("[CẦN")
    if can_count >= 10:
        warnings.append(f"R5 ✅ {can_count} trường [CẦN...] đã gắn nhãn")
    else:
        errors.append(f"R5 🟡 Chỉ {can_count} trường [CẦN...] — kiểm xem còn trường nào trống không")

    # R6 — 7 mục ICF đủ
    icf_sections = ["MỤC ĐÍCH", "QUY TRÌNH", "RỦI RO", "LỢI ÍCH", "BẢO MẬT", "TỰ NGUYỆN", "LIÊN HỆ"]
    missing = [s for s in icf_sections if s not in artifact.upper()]
    if missing:
        errors.append(f"R6 🔴 ICF thiếu mục: {', '.join(missing)}")
    else:
        warnings.append("R6 ✅ ICF đủ 7 mục Helsinki")

    # R7 — Disclaimer
    if "cần bác sĩ" not in artifact.lower() or "kiểm chứng" not in artifact.lower():
        errors.append("R7 🔴 Thiếu disclaimer")
    else:
        warnings.append("R7 ✅ Có disclaimer")

    return {"passed": len(errors) == 0, "errors": errors, "warnings": warnings}


# ════════════════════════════════════════════════════════════════════════════
# 5. XUẤT DOCX
# ════════════════════════════════════════════════════════════════════════════

def export_docx_g2(artifact_md: str, study_name: str, out_dir: Path) -> Optional[Path]:
    try:
        from docx import Document
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.shared import Pt, RGBColor
        doc = Document()
        # Cover page
        title = doc.add_heading("HỒ SƠ ĐẠO ĐỨC & ĐĂNG KÝ NGHIÊN CỨU", 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        doc.add_paragraph(f"Đề tài: {study_name}").alignment = WD_ALIGN_PARAGRAPH.CENTER
        doc.add_paragraph(f"[BẢN NHÁP TỰ ĐỘNG] | {datetime.now().strftime('%Y-%m-%d %H:%M')}").alignment = WD_ALIGN_PARAGRAPH.CENTER
        doc.add_paragraph("Cần bác sĩ/chủ nhiệm kiểm chứng, chỉnh sửa và ký trước khi nộp Hội đồng đạo đức.").alignment = WD_ALIGN_PARAGRAPH.CENTER
        doc.add_page_break()
        for line in artifact_md.split("\n"):
            stripped = line.strip()
            if line.startswith("# "):
                doc.add_heading(line[2:], 1)
            elif line.startswith("## "):
                doc.add_heading(line[3:], 2)
            elif line.startswith("### "):
                doc.add_heading(line[4:], 3)
            elif stripped.startswith("```") or stripped == "---":
                pass
            elif stripped.startswith("|"):
                p = doc.add_paragraph(stripped)
                p.runs[0].font.name = "Courier New"
                p.runs[0].font.size = Pt(8) if len(stripped) > 100 else Pt(9)
            elif stripped:
                p = doc.add_paragraph(line)
                # Highlight [CẦN...] warnings
                for run in p.runs:
                    if "[CẦN" in run.text:
                        run.font.color.rgb = RGBColor(0xCC, 0x44, 0x00)
                    if "DRAFT" in run.text:
                        run.font.bold = True
        docx_path = out_dir / f"G2_A3_ETHICS_PACKAGE_{study_name}.docx"
        doc.save(docx_path)
        return docx_path
    except ImportError:
        print("  ⚠ python-docx không cài — bỏ qua DOCX")
        return None
    except Exception as e:
        print(f"  ⚠ Lỗi DOCX: {e}")
        return None


# ════════════════════════════════════════════════════════════════════════════
# 6. CHECKPOINT G2
# ════════════════════════════════════════════════════════════════════════════

def write_g2_checkpoint(study_name: str, out_dir: Path, design_code: str,
                         risk: dict, ct_trials: list, guardrail: dict,
                         artifact_path: Path, docx_path: Optional[Path]) -> Path:
    cp = {
        "study": study_name, "gate": "G2",
        "gate_status": "DRAFT — CHỜ BÁC SĨ NỘP IRB VÀ NHẬN SỐ PHÊ DUYỆT",
        "generated_at": datetime.now().isoformat(),
        "g2_status": "PENDING",
        "g2_irb_number": None,
        "g2_approval_date": None,
        "g2_icf_version": None,
        "g2_registration": None,
        "design_code": design_code,
        "risk_level": risk["risk_level"],
        "irb_route": risk["irb_route"],
        "registration_required": risk["registration"],
        "register_where": risk["register_where"],
        "icf_required": risk["icf_required"],
        "clinicaltrials_found": len(ct_trials),
        "clinicaltrials_samples": [{"nct_id": t["nct_id"], "title": t["title"][:80], "url": t["url"]}
                                    for t in ct_trials[:5]],
        "guardrail": {"passed": guardrail["passed"], "errors": guardrail["errors"]},
        "artifacts": {
            "A3_markdown": str(artifact_path),
            "A3_docx": str(docx_path) if docx_path else None,
        },
        "documents_generated": [
            "TL1 — Đơn xin phê duyệt IRB",
            "TL2 — Tóm tắt đề cương (lay summary)",
            "TL3 — Bảng rủi ro–lợi ích",
            "TL4 — ICF tiếng Việt (7 mục Helsinki)",
            "TL5 — ICF tiếng Anh",
            "TL6 — DMP (Luật 91/2025/QH15)",
            "TL7 — Checklist nộp Hội đồng",
            "TL8 — Khai báo COI + Tài trợ + AI",
            "WHO 18 fields — bản nháp đăng ký",
        ],
        "pending_doctor_actions": [
            "Điền [CẦN BỔ SUNG] trong tất cả tài liệu (tên, đơn vị, liên lạc, cỡ mẫu...)",
            "Ký Đơn xin phê duyệt (Tài liệu 1) + Trưởng đơn vị xác nhận",
            "Nộp hồ sơ lên Hội đồng Đạo đức (lộ trình: " + risk["irb_route"] + ")",
            "Đăng ký nghiên cứu: " + risk["register_where"],
            "Cung cấp số IRB + ngày phê duyệt để hệ thống ghi G2=LOCKED",
        ],
        "lock_instruction": "Để mở G2: cung cấp số IRB + ngày phê duyệt + phiên bản ICF đã duyệt",
        "next_gate": "G3 (Cỡ mẫu) — chạy SONG SONG với G2 (không cần chờ G2 LOCKED)",
        "note": "G5 (thu thập dữ liệu THẬT) chỉ mở sau khi G2 LOCKED",
        "disclaimer": "Cần bác sĩ kiểm chứng.",
    }
    cp_path = out_dir / "G2_checkpoint.json"
    cp_path.write_text(json.dumps(cp, ensure_ascii=False, indent=2), encoding="utf-8")
    return cp_path


# ════════════════════════════════════════════════════════════════════════════
# 7. MAIN
# ════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="G2 Auto — Tự động hóa cổng G2: Đạo đức & Đăng ký nghiên cứu"
    )
    parser.add_argument("--study",  required=True,
                        help="Mã đề tài (cùng với --study ở G0/G1)")
    parser.add_argument("--topic",  default=None,
                        help="Chủ đề nghiên cứu (nếu không có G0 checkpoint)")
    parser.add_argument("--design", default=None,
                        choices=list(RISK_PROFILES.keys()),
                        help="Loại thiết kế (mặc định: đọc từ G1 checkpoint)")
    args = parser.parse_args()

    run_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    study = re.sub(r'[^\w\-]', '_', args.study.strip().replace(" ", "-"))

    print(f"\n{'='*65}")
    print(f"  G2 AUTO — {study}")
    print(f"  Thời gian: {run_date}")
    print(f"{'='*65}\n")

    out_dir = Path("exports") / study
    out_dir.mkdir(parents=True, exist_ok=True)

    # ── Bước 1: Đọc G0 + G1 checkpoint ──
    topic = args.topic or study
    design_code = args.design or "cohort"
    design_primary = "Cohort tiến cứu"
    reporting_std = "STROBE"
    n_sr, n_rct = 0, 0
    evidence_level = ""

    print("📂 Bước 1/7: Đọc G0 + G1 checkpoints...")
    g0_cp_path = out_dir / "G0_checkpoint.json"
    if g0_cp_path.exists():
        g0 = json.loads(g0_cp_path.read_text(encoding="utf-8"))
        topic = g0.get("topic", topic) or topic
        # SỬA: g0.get("pubmed_results", {}) chỉ dùng default {} khi KHÔNG có
        # key — nếu checkpoint có "pubmed_results": null, .get() vẫn trả
        # None, rồi .get("n_sr") trên None crash AttributeError.
        pub_results = g0.get("pubmed_results") or {}
        n_sr  = pub_results.get("n_sr", 0)
        n_rct = pub_results.get("n_rct", 0)
        evidence_level = g0.get("evidence_level", "")
        print(f"  → G0: topic='{topic[:50]}', {n_sr} SR, {n_rct} RCT")

    g1_cp_path = out_dir / "G1_checkpoint.json"
    if g1_cp_path.exists():
        g1 = json.loads(g1_cp_path.read_text(encoding="utf-8"))
        design_code_raw    = g1.get("design", {}).get("internal_code")
        design_primary_raw = g1.get("design", {}).get("primary")
        reporting_std_raw  = g1.get("design", {}).get("reporting_standard")
        # SỬA: dict.get(key, default) chỉ dùng default khi KHÔNG có key —
        # nếu checkpoint có key nhưng giá trị là null (JSON "null"/Python
        # None — thường gặp khi ghi checkpoint dở dang/lỗi), .get() vẫn trả
        # None chứ không phải default, khiến design_primary.lower()/[:50]
        # crash với TypeError ngay bước đọc checkpoint, chưa kịp tính toán gì.
        # SỬA: --design CLI trước đây luôn thắng design_code_raw (từ G1) mà
        # không cảnh báo gì nếu 2 giá trị khác nhau — nếu bác sĩ gõ nhầm cờ
        # --design, hồ sơ IRB sẽ định tuyến sai lộ trình mà không có tín hiệu
        # nào để phát hiện. Nay cảnh báo rõ khi có chênh lệch.
        if args.design and design_code_raw and args.design != design_code_raw:
            print(f"  ⚠️  --design={args.design} (tham số) KHÁC với thiết kế G1 đã suy luận "
                  f"({design_code_raw}) — đang dùng --design theo yêu cầu. Kiểm tra lại nếu "
                  "đây không phải chủ đích (vd gõ nhầm cờ).")
        design_code    = args.design or design_code_raw or design_code
        design_primary = design_primary_raw or design_primary
        reporting_std  = reporting_std_raw or reporting_std
        print(f"  → G1: design_code={design_code}, design='{design_primary[:50]}'")
    else:
        print(f"  → Không tìm thấy G1 checkpoint; dùng design_code={design_code}")

    # SỬA (tự động hóa thêm): G2 và G3 chạy song song theo thiết kế, nhưng
    # nếu bác sĩ đã chạy G3 TRƯỚC (thứ tự hoàn toàn hợp lệ), N thật đã có
    # sẵn — trước đây G2 chỉ đọc G0+G1, luôn để "[CẦN — chờ G3]" cứng dù dữ
    # liệu đã có trong tay. Nay đọc thêm G3 nếu tồn tại, không bắt buộc.
    n_adjusted = 0
    g3_cp_path = out_dir / "G3_checkpoint.json"
    if g3_cp_path.exists():
        try:
            g3 = json.loads(g3_cp_path.read_text(encoding="utf-8"))
            n_adjusted = int(g3.get("n_adjusted") or 0)
            if n_adjusted > 0:
                print(f"  → G3: đã có cỡ mẫu thật N={n_adjusted} — tự điền vào ICF/đăng ký")
        except (json.JSONDecodeError, OSError, TypeError, ValueError):
            n_adjusted = 0

    # ── Bước 2: Risk profile ──
    print("\n⚖️  Bước 2/7: Xác định mức nguy cơ và lộ trình IRB...")
    risk = get_risk_profile(design_code, design_primary)
    print(f"  → Mức nguy cơ: {risk['risk_level']}")
    print(f"  → Lộ trình IRB: {risk['irb_route']}")
    print(f"  → Đăng ký: {risk['registration']}")
    if risk.get("_fallback_warning"):
        print(f"  {risk['_fallback_warning']}")

    # ── Bước 3: Tìm ClinicalTrials.gov ──
    print("\n🔍 Bước 3/7: Tìm kiếm ClinicalTrials.gov (prior art)...")
    ct_trials = search_clinicaltrials(topic, design_code)
    if ct_trials:
        print(f"  → Tìm được {len(ct_trials)} thử nghiệm tương tự:")
        for t in ct_trials[:3]:
            print(f"     • {t['nct_id']} | {t['title'][:60]} | {t['status']}")
    else:
        print("  → Không tìm được thử nghiệm tương tự")

    # ── Bước 4: Sinh hồ sơ G2 ──
    print("\n✍️  Bước 4/7: Sinh trọn bộ hồ sơ G2 (8 tài liệu)...")
    artifact_md = generate_g2_full_package(
        topic=topic, study_name=study, design_code=design_code,
        design_primary=design_primary, reporting_std=reporting_std,
        n_sr=n_sr, n_rct=n_rct, evidence_level=evidence_level,
        ct_trials=ct_trials, risk=risk, run_date=run_date,
        n_adjusted=n_adjusted
    )
    md_path = out_dir / f"G2_A3_ETHICS_PACKAGE_{study}.md"
    md_path.write_text(artifact_md, encoding="utf-8")
    print(f"  → Lưu: {md_path} ({len(artifact_md)//1000}KB)")

    # ── Bước 5: Guardrail ──
    print("\n🛡️  Bước 5/7: Kiểm guardrail R1-R7...")
    guardrail = guardrail_check_g2(artifact_md)
    for msg in guardrail["warnings"]:
        print(f"  {msg}")
    for err in guardrail["errors"]:
        print(f"  {err}")
    status = "✅ PASS" if guardrail["passed"] else f"⚠ {len(guardrail['errors'])} LỖI"
    print(f"  → Guardrail: {status}")

    # ── Bước 6: DOCX ──
    print(f"\n📄 Bước 6/7: Xuất DOCX ({len(artifact_md.split(chr(10)))} dòng)...")
    docx_path = export_docx_g2(artifact_md, study, out_dir)
    if docx_path:
        print(f"  → Lưu: {docx_path}")

    # ── Bước 7: Checkpoint ──
    print("\n💾 Bước 7/7: Ghi checkpoint G2...")
    cp_path = write_g2_checkpoint(
        study, out_dir, design_code, risk, ct_trials, guardrail, md_path, docx_path
    )
    print(f"  → Lưu: {cp_path}")

    # ── Tóm tắt ──
    print(f"\n{'='*65}")
    print(f"  ✅ G2 HOÀN THÀNH — {study}")
    print(f"{'='*65}")
    print(f"\n  📁 Đầu ra: {out_dir}/")
    print(f"  📝 A3 Markdown: {md_path.name}")
    if docx_path:
        print(f"  📄 A3 DOCX:     {docx_path.name}")
    print("\n  8 TÀI LIỆU ĐÃ SOẠN:")
    print("  TL1 — Đơn xin phê duyệt IRB")
    print("  TL2 — Tóm tắt đề cương (lay summary)")
    print(f"  TL3 — Bảng rủi ro–lợi ích ({risk['risk_level']})")
    print("  TL4 — ICF tiếng Việt (7 mục Helsinki)")
    print("  TL5 — ICF tiếng Anh")
    print("  TL6 — DMP (Luật 91/2025/QH15)")
    print(f"  TL7 — Checklist nộp Hội đồng ({risk['irb_route']})")
    print("  TL8 — Khai báo COI + Tài trợ + AI")
    print("  + WHO 18 fields draft")
    if design_code == "sr_ma":
        print("  + PROSPERO registration draft")
    print(f"  🔍 ClinicalTrials.gov: {len(ct_trials)} thử nghiệm tương tự")
    print(f"  🔴 Guardrail: {status}")
    print("\n  VIỆC CÒN LẠI CỦA BÁC SĨ:")
    print("  1. Mở file DOCX, điền tất cả [CẦN BỔ SUNG]")
    print("  2. Ký + Trưởng đơn vị ký → nộp Hội đồng Đạo đức")
    print(f"  3. Đăng ký: {risk['register_where']}")
    print("  4. Nhận số IRB → cung cấp để G2=LOCKED")
    print(f"  5. Chạy G3 song song: python tools/run_g3_auto.py --study {study}")
    print("\n  Cần bác sĩ kiểm chứng.")
    print(f"{'='*65}\n")


if __name__ == "__main__":
    main()
