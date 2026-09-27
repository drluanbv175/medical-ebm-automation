"""Bước 4: Evidence filtering – áp bộ lọc chứng cứ bắt buộc.

Phân loại thành: actionable | need_full_text | watch_only | excluded.
Mỗi bản ghi PHẢI có lý do (actionable_reason hoặc reason_for_exclusion).
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from app.config import settings

# Thiết kế bị loại khỏi phần "thay đổi thực hành" (mục 4.4).
EXCLUDED_STUDY_TYPES = {
    "preprint", "animal_invitro", "editorial", "narrative_review",
}
EXCLUDE_KEYWORDS = ("advertisement", "press release", "quảng cáo", "company pr")

# Từ khóa nhận diện chủ đề kháng sinh (dùng CHUNG cho báo cáo + dashboard, tránh trùng lặp).
# SỬA 2026-09-05 (Workflow đối kháng đa-agent, vòng 14) — từ khóa đơn "aware"
# nhằm bắt phân loại WHO AWaRe (Access/Watch/Reserve) nhưng sau khi lowercase
# trở thành substring khớp bất kỳ văn bản nào chứa từ tiếng Anh phổ biến
# "aware"/"awareness" (vd "Clinicians should be aware of the risk of falls
# in elderly patients on benzodiazepines" — hoàn toàn không liên quan kháng
# sinh) — dương tính giả gây nhiễu mục kháng sinh của báo cáo tuần/dashboard.
# Thay bằng cụm đặc hiệu cho đúng cách các bài kháng sinh thật nhắc tới
# khung phân loại này.
ANTIBIOTIC_KEYWORDS = ("antibiotic", "antimicrobial", "stewardship",
                       "kháng sinh", "aware classification", "access, watch, reserve",
                       "pneumonia")


def is_antibiotic_text(*parts) -> bool:
    """True nếu bất kỳ phần văn bản nào (title/abstract/keywords/source) chứa từ khóa kháng sinh."""
    text = " ".join(str(p or "") for p in parts).lower()
    return any(k in text for k in ANTIBIOTIC_KEYWORDS)


# --- Tín hiệu rút bài / Expression of Concern (vá 26/09/2026, synthesis #4) -----------------
# Nguồn (PubMed `_parse_efetch`, Europe PMC `search`) gắn raw["rut_bai"] ∈ {"retracted","eoc"}
# khi KHỚP ĐÚNG TOKEN («Retracted Publication» / RefType RetractionIn / ExpressionOfConcernIn —
# KHÔNG BAO GIỜ «Retraction of Publication», tức chính thông báo rút). `normalize()` chép sang
# khoá tạm `_rut_bai` (tiền tố _ ⇒ không ghi DB) + `reason_for_exclusion` (⇒ tier D). Tiền tố
# lý do là HỢP ĐỒNG: bản tin cảnh báo nhận diện hàng «đã bị rút» trong DB qua tiền tố này.
TIEN_TO_LY_DO_RUT_BAI = "⛔ Bài đã bị rút"
TIEN_TO_LY_DO_EOC = "🟠 Có Expression of Concern"


def ly_do_rut_bai(nguon: str = "", thong_bao: Optional[List[dict]] = None) -> str:
    """Lý do loại cụ thể cho bài đã bị rút (kèm PMID thông báo rút nếu nguồn có)."""
    pmids = [str(t.get("pmid")) for t in (thong_bao or []) if t and t.get("pmid")]
    kem = f"; thông báo rút: PMID {', '.join(pmids)}" if pmids else ""
    goc = f" ({nguon}{kem})" if nguon or kem else ""
    return (f"{TIEN_TO_LY_DO_RUT_BAI}{goc} — KHÔNG dùng lâm sàng, không đưa vào báo cáo "
            "chính/cảnh báo/EBM_MASTER. Cần bác sĩ kiểm chứng.")


def la_ly_do_rut_bai(reason: Optional[str]) -> bool:
    return bool(reason) and str(reason).startswith(TIEN_TO_LY_DO_RUT_BAI)


def la_ly_do_eoc(reason: Optional[str]) -> bool:
    return bool(reason) and str(reason).startswith(TIEN_TO_LY_DO_EOC)


def classify(item: Dict) -> Tuple[str, bool, str, str]:
    """Trả về (classification, is_actionable, actionable_reason, reason_for_exclusion).

    Nhánh ĐẦU TIÊN (vá 26/09/2026, synthesis #4): bài đã bị rút ⇒ 'excluded' kèm lý do rút bài
    cụ thể (không để bị ghi đè thành «Tier D» chung chung). Bài có Expression of Concern ⇒ tối
    đa 'need_full_text' (không bao giờ actionable), lý do ghi rõ. Không vứt bản ghi nào."""
    rut_bai = item.get("_rut_bai")
    if rut_bai == "retracted":
        return ("excluded", False, "", item.get("_ly_do_rut_bai") or ly_do_rut_bai())
    phan_loai, actionable, a_reason, x_reason = _classify_co_ban(item)
    if rut_bai == "eoc" and phan_loai != "excluded":
        ghi_chu = (f"{TIEN_TO_LY_DO_EOC} (thông báo quan ngại của tạp chí) — đọc toàn văn và thông "
                   "báo trước khi dùng; không actionable.")
        cu = x_reason or a_reason
        ly_do = f"{ghi_chu} {cu}".strip()
        if phan_loai in ("actionable", "need_full_text"):
            return ("need_full_text", False, "", ly_do)
        return (phan_loai, False, "", ly_do)
    return (phan_loai, actionable, a_reason, x_reason)


def _classify_co_ban(item: Dict) -> Tuple[str, bool, str, str]:
    """Phân loại gốc (không xét tín hiệu rút bài/EoC — `classify()` xét trước/sau)."""
    study_type = (item.get("study_type") or "").lower()
    eq = float(item.get("evidence_quality_score") or 0)
    pc = float(item.get("practice_change_score") or 0)
    tier = item.get("reliability_tier") or "C"
    text = " ".join(str(item.get(k, "") or "") for k in ("title", "abstract")).lower()

    # 1) Loại trừ tuyệt đối
    if study_type in EXCLUDED_STUDY_TYPES:
        return ("excluded", False, "",
                f"Loại thiết kế '{study_type}' không dùng để thay đổi thực hành (mục 4.4).")
    if any(k in text for k in EXCLUDE_KEYWORDS):
        return ("excluded", False, "", "Phát hiện dấu hiệu quảng cáo/PR, loại khỏi báo cáo chính.")
    if not item.get("title"):
        return ("excluded", False, "", "Tài liệu không có tiêu đề/không truy xuất được nguồn gốc.")
    if tier == "D":
        return ("excluded", False, "", "Reliability Tier D – loại khỏi báo cáo chính.")

    # 2) Actionable: đạt ngưỡng cấu hình + tier A
    if (eq >= settings.min_evidence_score and pc >= settings.min_practice_change_score
            and tier == "A"):
        reason = (f"Tier A, Evidence={eq:.0f}≥{settings.min_evidence_score}, "
                  f"PracticeChange={pc:.0f}≥{settings.min_practice_change_score}. "
                  "Nguồn mạnh, có hành động cụ thể, áp dụng được.")
        return ("actionable", True, reason, "")

    # 3) Cần đọc toàn văn / guideline gốc
    if tier == "B" or (eq >= 60 and pc >= 45):
        reason_x = ("Bằng chứng/khả năng đổi thực hành ở mức trung bình; "
                    "cần đọc toàn văn hoặc guideline gốc trước khi triển khai.")
        return ("need_full_text", False, "", reason_x)

    # 4) Chỉ theo dõi
    return ("watch_only", False, "",
            "Chứng cứ chưa đủ mạnh hoặc tác động thực hành thấp; chỉ theo dõi (watch).")
