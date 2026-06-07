"""Trích NGUYÊN VĂN các câu mang tín hiệu lâm sàng từ abstract.

NGUYÊN TẮC CHỐNG BỊA ĐẶT (quan trọng):
- CHỈ tách câu và gắn nhãn theo từ khóa, rồi TRẢ LẠI CÂU NGUỒN NGUYÊN VĂN.
- KHÔNG tóm tắt lại, KHÔNG diễn giải, KHÔNG sinh nội dung mới.
- Mọi câu hiển thị đều truy vết được nguyên văn về abstract gốc.

Phần lớn abstract bằng tiếng Anh (PubMed/EuropePMC/Crossref) -> câu trích là tiếng Anh
(nguyên văn nguồn). Hỗ trợ thêm vài từ khóa tiếng Việt.
"""
from __future__ import annotations

import re
from typing import Dict, List

# (mã nhóm, từ khóa nhận diện – so khớp lowercase). Chọn từ khóa ĐẶC HIỆU để giảm dương tính giả.
_CATEGORIES = [
    ("doi_tuong", ["patients with", "patients who", "in adults", "participants",
                   "were enrolled", "aged ", "women with", "men with", "people with",
                   "individuals with", "cohort of", "n =", "n=", "sample of",
                   "inclusion criteria", "eligible patients",
                   "bệnh nhân", "người bệnh", "đối tượng"]),
    ("ket_qua", ["reduced", "reduction", "increased", "decreased", "improved",
                 "associated with", "hazard ratio", "odds ratio", "risk ratio",
                 "relative risk", "95% ci", "95%ci", "confidence interval",
                 "p <", "p<", "p =", "p=", "no significant", "no difference",
                 "noninferior", "non-inferior", "superior to", "primary outcome",
                 "primary endpoint", "mortality", "incidence of", "efficacy",
                 "giảm", "tăng nguy cơ", "cải thiện", "tử vong", "kết cục"]),
    ("khuyen_cao", ["recommend", "should be", "should receive", "first-line",
                    "first line", "we suggest", "is advised", "no longer recommended",
                    "guideline recommends", "preferred", "is indicated",
                    "khuyến cáo", "nên dùng", "ưu tiên", "không nên", "chỉ định"]),
    ("an_toan", ["risk of", "adverse event", "adverse effect", "warning", "caution",
                 "safety", "bleeding", "hypoglyc", "toxicity", "side effect",
                 "contraindicat", "should be monitored", "avoid", "serious adverse",
                 "nguy cơ", "tác dụng phụ", "chống chỉ định", "cảnh báo", "thận trọng"]),
    ("lieu", ["dose", "dosing", " mg ", "mg/", "mg daily", "dose adjustment",
              "renal impairment", "hepatic impairment", "creatinine clearance",
              "egfr", "titration", "discontinuation", "liều", "chỉnh liều",
              "suy thận", "suy gan"]),
]

_LABELS = {
    "doi_tuong": "👤 Đối tượng",
    "ket_qua": "📊 Kết quả / Hiệu quả",
    "khuyen_cao": "✅ Khuyến cáo / Đề xuất (từ nguồn)",
    "an_toan": "⚠️ An toàn / Thận trọng",
    "lieu": "💊 Liều / Hiệu chỉnh",
}

_ORDER = ["khuyen_cao", "ket_qua", "an_toan", "lieu", "doi_tuong"]


def _split_sentences(text: str) -> List[str]:
    text = re.sub(r"\s+", " ", text or "").strip()
    if not text:
        return []
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9(])", text)
    return [p.strip() for p in parts if len(p.strip()) > 20]


_KW = {cat: kws for cat, kws in _CATEGORIES}


def extract_clinical_points(abstract: str, max_per_cat: int = 3) -> Dict[str, List[str]]:
    """Trả về {nhóm: [câu nguyên văn,...]} trích từ abstract.

    Mỗi câu chỉ được gán vào MỘT nhóm (theo thứ tự ưu tiên _ORDER) để tránh lặp.
    Rỗng nếu không có abstract.
    """
    sentences = _split_sentences(abstract)
    out: Dict[str, List[str]] = {}
    for s in sentences:
        low = s.lower()
        for cat in _ORDER:  # gán theo ưu tiên: khuyến cáo > kết quả > an toàn > liều > đối tượng
            if any(k in low for k in _KW[cat]):
                bucket = out.setdefault(cat, [])
                if s.rstrip() not in bucket and len(bucket) < max_per_cat:
                    bucket.append(s.rstrip())
                break  # mỗi câu chỉ vào 1 nhóm
    return {cat: out[cat] for cat in _ORDER if cat in out}


def label_for(category: str) -> str:
    return _LABELS.get(category, category)


def ordered_categories() -> List[str]:
    return _ORDER


# ===========================================================================
# TRÍCH KẾT LUẬN (điểm mấu chốt áp dụng lâm sàng) — NGUYÊN VĂN từ abstract.
# Kết luận của tác giả là phần trả lời rõ nhất "nghiên cứu này dùng được gì".
# ===========================================================================
_CONCL_LABELS = ("conclusion", "conclusions", "interpretation", "kết luận",
                 "implication", "implications", "summary")
_CONCL_CUES = ["in conclusion", "we conclude", "in summary", "taken together",
               "these findings suggest", "these results suggest", "our findings suggest",
               "our findings indicate", "this study suggests", "this suggests that",
               "we recommend", "should be considered", "may be considered",
               "supports the use", "do not support", "is recommended",
               "kết luận", "tóm lại", "cho thấy rằng"]


def _sections(text: str):
    """Tách abstract đã làm sạch thành [(nhãn, nội_dung)] dựa trên dòng 'Nhãn:'."""
    secs = []
    label, buf = None, []
    for raw in (text or "").split("\n"):
        line = raw.strip()
        if not line:
            continue
        if len(line) <= 40 and line.endswith(":"):  # dòng nhãn mục (vd 'Conclusion:')
            if label is not None or buf:
                secs.append((label, " ".join(buf).strip()))
            label, buf = line[:-1].strip(), []
        else:
            buf.append(line)
    if label is not None or buf:
        secs.append((label, " ".join(buf).strip()))
    return secs


def extract_conclusion(abstract: str, max_sentences: int = 2) -> List[str]:
    """Trả về câu KẾT LUẬN (nguyên văn) từ abstract — phần áp dụng lâm sàng rõ nhất.

    Ưu tiên: (1) mục có nhãn Conclusion/Interpretation; (2) câu chứa cụm kết luận;
    (3) câu cuối abstract. Mọi câu là chuỗi con (chuẩn hóa khoảng trắng) của nguồn.
    """
    text = (abstract or "").strip()
    if not text:
        return []
    # (1) Mục có nhãn kết luận (abstract có cấu trúc)
    for label, content in _sections(text):
        if label and any(k in label.lower() for k in _CONCL_LABELS) and content:
            sents = _split_sentences(content)
            return (sents or [content.strip()])[:max_sentences]
    # (2) Câu chứa cụm tín hiệu kết luận
    sentences = _split_sentences(text)
    hits = [s for s in sentences if any(c in s.lower() for c in _CONCL_CUES)]
    if hits:
        return hits[:max_sentences]
    # (3) Câu cuối (abstract không cấu trúc thường kết bằng hàm ý lâm sàng)
    return sentences[-1:] if sentences else []


# ===========================================================================
# TÓM TẮT THEO PICO (Population – Intervention – Comparison – Outcome)
# Cũng CHỈ trích nguyên văn theo từ khóa; không bịa, không diễn giải.
# ===========================================================================
_PICO_KW = {
    "P": ["patients with", "patients who", "in patients with", "adults with", "participants",
          "people with", "individuals with", "subjects with", "n =", "n=", "were enrolled",
          "enrolled", " aged ", "men with", "women with", "children with", "cohort of",
          "inclusion criteria", "eligible patients", "were recruited", "were included"],
    "I": ["randomized to", "randomised to", "assigned to", "treated with", "received",
          "treatment with", "therapy with", "administration of", "were given", "use of",
          "underwent", "intervention group"],
    "C": ["compared with", "compared to", "versus", " vs ", " vs.", "placebo", "control group",
          "usual care", "standard care", "control arm", "than those receiving"],
    "O": ["primary outcome", "primary endpoint", "secondary outcome", "co-primary", "the primary",
          "we found", "results showed", "hazard ratio", "odds ratio", "risk ratio", "95% ci",
          "95%ci", "confidence interval", "p <", "p<", "p =", "p=", "mortality", "incidence of",
          "reduced the", "increased the", "no significant difference", "no difference",
          "efficacy", "associated with", "was higher", "was lower"],
}
# Ưu tiên GÁN câu: O (kết quả) > P (đối tượng) > I (can thiệp) > C (so sánh).
_PICO_ASSIGN = ["O", "P", "I", "C"]
_PICO_DISPLAY = ["P", "I", "C", "O"]
_PICO_LABEL = {
    "P": "P — Đối tượng / Bệnh nhân",
    "I": "I — Can thiệp",
    "C": "C — So sánh / Đối chứng",
    "O": "O — Kết cục / Kết quả",
}


def extract_pico(abstract: str, max_per: int = 2) -> Dict[str, List[str]]:
    """Trả về {P|I|C|O: [câu nguyên văn,...]} từ abstract. Mỗi câu chỉ 1 nhóm."""
    sentences = _split_sentences(abstract)
    out: Dict[str, List[str]] = {}
    for s in sentences:
        low = s.lower()
        for cat in _PICO_ASSIGN:
            if any(k in low for k in _PICO_KW[cat]):
                bucket = out.setdefault(cat, [])
                if s.rstrip() not in bucket and len(bucket) < max_per:
                    bucket.append(s.rstrip())
                break
    return out


def pico_label(cat: str) -> str:
    return _PICO_LABEL.get(cat, cat)


def pico_display_order() -> List[str]:
    return _PICO_DISPLAY
