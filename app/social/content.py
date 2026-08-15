"""Sinh KỊCH BẢN bài đăng TikTok từ một bản ghi chứng cứ (EvidenceItem -> row dict).

Đầu ra là một dict `post` có cấu trúc rõ ràng để renderer vẽ slide và packager
xuất caption. KHÔNG sinh nội dung y khoa mới: mọi "điểm chính" đều là câu trích
NGUYÊN VĂN từ abstract (extraction.py), kèm bản dịch máy tham khảo (translate.py).
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional

from app.services.extraction import extract_clinical_points, label_for, ordered_categories
from app.services.translate import translate_vi

# Khuyến cáo cố định gắn mọi bài (tham khảo, không thay khám bệnh).
POST_DISCLAIMER = (
    "Nội dung mang tính tham khảo, cập nhật chứng cứ — KHÔNG thay thế việc khám "
    "và tư vấn trực tiếp của bác sĩ. Hãy đối chiếu từng người bệnh cụ thể."
)

# Loại chứng cứ đủ mạnh để trình bày dưới dạng "cập nhật/khuyến cáo".
_STRONG_STUDY = {
    "guideline", "systematic_review", "meta_analysis", "randomized_controlled_trial",
    "rct", "regulatory_alert", "practice_guideline",
}
# Loại chứng cứ yếu: chỉ được làm "tin nhanh – chưa kết luận", không đăng mặc định.
_WEAK_STUDY = {"preprint", "case_report", "case_series", "in_vitro", "animal"}

# Nhãn hiển thị ngắn cho mức độ chứng cứ trên slide.
_KIND_LABEL = {
    "recommendation": "CẬP NHẬT CHỨNG CỨ",
    "watch": "TIN NHANH · CHƯA KẾT LUẬN",
}


def eligible_for_post(row: Dict) -> Dict:
    """Quyết định bản ghi có nên/đủ điều kiện dựng bài, và ở DẠNG nào.

    Trả về {"ok": bool, "kind": "recommendation|watch", "reason": str}.
    - excluded -> không đăng.
    - tier A/B hoặc study_type mạnh hoặc cảnh báo an toàn chính thức -> recommendation.
    - còn lại (tier C/D, observational, preprint...) -> watch (mặc định KHÔNG đăng).
    """
    if row.get("classification") == "excluded":
        return {"ok": False, "kind": "none", "reason": "Bị loại khỏi báo cáo chính."}

    tier = (row.get("reliability_tier") or "").upper()
    study = (row.get("study_type") or "").lower().replace("-", "_").replace(" ", "_")
    is_safety = bool(row.get("safety_signal")) or row.get("source") == "drug_safety"

    strong = tier in ("A", "B") or any(s in study for s in _STRONG_STUDY) or \
        (is_safety and row.get("source_type") == "drug_safety")
    weak = any(w in study for w in _WEAK_STUDY) or tier == "D"

    if strong and not weak:
        return {"ok": True, "kind": "recommendation",
                "reason": f"Tier {tier or '?'} / {study or 'n/a'} — đủ mạnh để cập nhật."}
    return {"ok": True, "kind": "watch",
            "reason": f"Tier {tier or '?'} / {study or 'n/a'} — chỉ ở mức theo dõi, không khuyến cáo."}


# --------------------------------------------------------------------------
def _clean(text: str) -> str:
    """Bỏ thẻ HTML (abstract cấu trúc EuropePMC hay có <h4>...</h4>) + gọn khoảng trắng."""
    text = re.sub(r"<[^>]+>", " ", text or "")
    return re.sub(r"\s+", " ", text.strip())


def _is_internal_scoring(text: str) -> bool:
    """True nếu chuỗi là lý do chấm điểm nội bộ (không nên hiển thị công khai)."""
    t = (text or "").lower()
    return ("evidence=" in t or "practicechange=" in t
            or bool(re.search(r"\btier [a-d]\b", t)))


def _title_vi(title: str) -> Dict[str, Optional[str]]:
    """Tiêu đề: giữ nguyên văn; thêm bản dịch VI tham khảo nếu tiêu đề là tiếng Anh."""
    title = _clean(title)
    return {"en": title, "vi": translate_vi(title)}


def _bullet(sentence: str) -> Dict[str, Optional[str]]:
    """Một gạch đầu dòng: NGUYÊN VĂN (en) + dịch máy tham khảo (vi)."""
    sentence = _clean(sentence)
    return {"en": sentence, "vi": translate_vi(sentence)}


def _hashtags(row: Dict) -> List[str]:
    base = ["#ykhoa", "#bacsi", "#kienthucykhoa", "#evidencebased", "#suckhoe"]
    area = (row.get("clinical_area") or "").lower()
    area_map = {
        "tim mạch": "#timmach", "thần kinh": "#thankinh", "đột quỵ": "#dotquy",
        "nội tiết": "#noitiet", "chuyển hóa": "#daithaoduong", "thận": "#benhthan",
        "hô hấp": "#hohap", "tiêu hóa": "#tieuhoa", "gan": "#gan",
        "cơ xương khớp": "#coxuongkhop", "nhiễm khuẩn": "#nhiemkhuan",
        "kháng sinh": "#khangsinh", "lão khoa": "#laokhoa", "cấp cứu": "#capcuu",
    }
    for k, tag in area_map.items():
        if k in area and tag not in base:
            base.append(tag)
    return base


def _slides_from_points(row: Dict, max_slides: int = 3, per_slide: int = 3) -> List[Dict]:
    """Dựng các slide 'điểm chính' từ câu trích NGUYÊN VĂN của abstract.

    Ưu tiên nhóm: khuyến cáo > kết quả > an toàn > liều > đối tượng (theo extraction).
    """
    points = extract_clinical_points(_clean(row.get("abstract") or ""), max_per_cat=3)
    slides: List[Dict] = []
    for cat in ordered_categories():
        sents = points.get(cat) or []
        if not sents:
            continue
        bullets = [_bullet(s) for s in sents[:per_slide]]
        slides.append({"heading": label_for(cat), "bullets": bullets})
        if len(slides) >= max_slides:
            break
    return slides


def _fallback_slides(row: Dict) -> List[Dict]:
    """Khi KHÔNG có abstract để trích (guideline/cảnh báo): dựng slide từ các TRƯỜNG
    THẬT đã lưu trong kho (không bịa) — safety_signal, tóm tắt nguồn, ảnh hưởng thực hành.
    """
    syn = row.get("synthesis") or {}
    candidates = [
        ("⚠️ Nội dung cảnh báo", _clean(row.get("safety_signal") or "")),
        ("📋 Tóm tắt cập nhật (từ nguồn)", _clean(syn.get("thong_tin_moi") or "")),
        ("📌 Ảnh hưởng thực hành", _clean(row.get("practice_impact") or "")),
    ]
    slides: List[Dict] = []
    seen = set()
    for heading, text in candidates:
        if not text or text in seen or "Không có abstract" in text:
            continue
        seen.add(text)
        # Tách câu, lấy 1–3 câu đầu làm các gạch đầu dòng (tránh nhồi cả đoạn).
        sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.strip()) > 10]
        chunks = sents[:3] or [text[:280]]
        slides.append({"heading": heading, "bullets": [_bullet(s) for s in chunks]})
        if len(slides) >= 2:
            break
    return slides


def build_post(row: Dict) -> Optional[Dict]:
    """Tạo dict `post` cho một bản ghi chứng cứ. None nếu không đủ điều kiện."""
    elig = eligible_for_post(row)
    if not elig["ok"]:
        return None

    syn = row.get("synthesis") or {}
    # Ưu tiên trích NGUYÊN VĂN từ abstract; nếu không có -> dùng trường thật đã lưu.
    point_slides = _slides_from_points(row) or _fallback_slides(row)

    # Không có nội dung thật nào để đăng -> bỏ qua (không bịa).
    if not point_slides:
        return None

    source_name = row.get("source") or row.get("journal_or_organization") or "Nguồn"
    ids = []
    if row.get("doi"):
        ids.append(f"DOI: {row['doi']}")
    if row.get("pmid"):
        ids.append(f"PMID: {row['pmid']}")
    if row.get("nct_id"):
        ids.append(str(row["nct_id"]))
    url = row.get("url") or ""

    evidence_level = row.get("evidence_level") or row.get("operational_evidence_level") or ""
    tier = row.get("reliability_tier") or ""
    grade = row.get("official_grade") or ""

    # "Áp dụng" lấy từ synthesis. KHÔNG đưa chuỗi chấm điểm nội bộ
    # (Evidence=.., PracticeChange=.., Tier ..) lên slide công khai.
    apply_lines = []
    if syn.get("doi_tuong_ap_dung"):
        apply_lines.append(("Đối tượng", _clean(syn["doi_tuong_ap_dung"])))
    if elig["kind"] == "recommendation":
        action = _clean(syn.get("hanh_dong_de_xuat") or "")
        if _is_internal_scoring(action) or not action:
            action = ("Đối chiếu guideline/nguồn gốc và bối cảnh từng người bệnh "
                      "trước khi áp dụng.")
        apply_lines.append(("Gợi ý áp dụng", action))
    canh_bao = _clean(syn.get("canh_bao_can_trong") or "")
    if canh_bao and "Không có cảnh báo" not in canh_bao and not _is_internal_scoring(canh_bao):
        apply_lines.append(("Thận trọng", canh_bao))

    return {
        "id": row.get("id"),
        "kind": elig["kind"],
        "kind_label": _KIND_LABEL[elig["kind"]],
        "area": row.get("clinical_area") or "Cập nhật y khoa",
        "title": _title_vi(row.get("title") or ""),
        "tier": tier,
        "evidence_level": evidence_level,
        "official_grade": grade,
        "point_slides": point_slides,
        "apply": apply_lines,
        "source_name": source_name,
        "ids": ids,
        "url": url,
        "disclaimer": POST_DISCLAIMER,
        "hashtags": _hashtags(row),
        "eligibility_reason": elig["reason"],
    }


# --------------------------------------------------------------------------
def build_manual_post(title: str, slides: List[Dict], area: str = "Kiến thức y khoa",
                      source: str = "", url: str = "",
                      kind_label: str = "KIẾN THỨC Y KHOA") -> Optional[Dict]:
    """Dựng post từ nội dung TỰ SOẠN của người dùng (không qua pipeline/chứng cứ).

    slides: [{"heading": str, "bullets": [str, ...]}] — văn bản tiếng Việt do bác viết.
    Không dịch, không thêm nội dung; chỉ định dạng để vẽ slide + đọc.
    """
    title = _clean(title)
    if not title and not slides:
        return None
    point_slides = []
    for sl in slides:
        bullets = [{"en": _clean(b), "vi": None} for b in sl.get("bullets", []) if _clean(b)]
        heading = _clean(sl.get("heading", ""))
        if heading or bullets:
            point_slides.append({"heading": heading or "•", "bullets": bullets})
    if not point_slides:
        return None
    return {
        "id": None,
        "kind": "recommendation",
        "kind_label": kind_label,
        "area": area or "Kiến thức y khoa",
        "title": {"en": title, "vi": None},
        "tier": "",
        "evidence_level": "",
        "official_grade": "",
        "point_slides": point_slides,
        "apply": [],
        "source_name": _clean(source) or "Tự soạn",
        "ids": [],
        "url": _clean(url),
        "disclaimer": POST_DISCLAIMER,
        "hashtags": _hashtags({"clinical_area": area}),
        "eligibility_reason": "Nội dung tự soạn (bác sĩ tự chịu trách nhiệm chuyên môn).",
    }


def render_caption(post: Dict) -> str:
    """Caption TikTok (text) từ post — gọn, có nguồn + khuyến cáo + hashtag."""
    title = post["title"]["vi"] or post["title"]["en"]
    lines = [f"🩺 {post['area']} · {post['kind_label']}", "", title, ""]

    # 1–2 điểm chính (bản VI nếu có) để mồi nội dung.
    teaser = []
    for sl in post["point_slides"]:
        for b in sl["bullets"]:
            teaser.append(b["vi"] or b["en"])
            if len(teaser) >= 2:
                break
        if len(teaser) >= 2:
            break
    for t in teaser:
        lines.append(f"• {t}")
    lines.append("")

    src = post["source_name"]
    if post["ids"]:
        src += " — " + " · ".join(post["ids"])
    lines.append(f"📚 Nguồn: {src}")
    if post["url"]:
        lines.append(post["url"])
    badge = []
    if post["tier"]:
        badge.append(f"Độ tin: {post['tier']}")
    if post["evidence_level"]:
        badge.append(f"Mức CC: {post['evidence_level']}")
    if badge:
        lines.append(" · ".join(badge))
    lines.append("")
    lines.append("⚠️ " + post["disclaimer"])
    lines.append("")
    lines.append(" ".join(post["hashtags"]))
    return "\n".join(lines)
