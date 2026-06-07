"""Phân loại metadata dùng chung cho mọi connector ở chế độ API THẬT.

Mục tiêu: từ (title, document_type, journal/source) suy ra `study_type` chuẩn hóa
và nhận diện tổ chức chính thống. Đây là đòn bẩy lớn nhất để chấm điểm chứng cứ
ĐÚNG khi dùng dữ liệu thật — vì nhiều API trả 'journal-article' chung chung.

Nguyên tắc: chỉ phân loại dựa trên TÍN HIỆU CÓ THẬT trong metadata; không suy diễn.
Khi không đủ tín hiệu -> trả None để pipeline xử lý thận trọng (điểm thấp).
"""
from __future__ import annotations

import re
from typing import Optional

# Viết tắt ngắn dễ trùng từ tiếng Anh thông thường (who/Canada/vaccine...). Các tín hiệu này
# CHỈ khớp trong trường journal/organization, không khớp trong tiêu đề/tác giả.
_AMBIGUOUS_ORG_SIGNALS = {"who", "ada", "acc", "esc", "es", "acr", "ema", "easl", "gold", "cdc"}

# Server preprint phổ biến (loại khỏi phần thay đổi thực hành).
_PREPRINT = ("medrxiv", "biorxiv", "ssrn", "preprint", "preprints.org",
             "research square", "rs.3.rs", "arxiv", "/ppr/", "authorea")

# Mẫu tiêu đề chỉ guideline/khuyến cáo chính thức.
_GUIDELINE = ("guideline", "guidance", "recommendation", "consensus statement",
              "consensus document", "scientific statement", "position statement",
              "practice parameter", "standards of care", "standards of medical care",
              "appropriate use criteria", "clinical practice guideline")

_SR = ("systematic review", "meta-analysis", "meta analysis", "network meta-analysis",
       "umbrella review", "cochrane review")

_RCT = ("randomized controlled trial", "randomised controlled trial",
        "randomized clinical trial", "randomized, ", "randomised, ",
        "double-blind", "double blind", "placebo-controlled", "phase 3 trial",
        "phase iii", "phase 3 randomized", "multicenter randomized")

_COHORT = ("prospective cohort", "cohort study", "longitudinal cohort",
           "registry", "population-based cohort")

_CASE = ("case report", "case series", "case-report")
_EDITORIAL = ("editorial", "commentary", "viewpoint", "perspective", "letter to the editor")
_NARRATIVE = ("narrative review", "review of the literature", "scoping review")

# Tổ chức/tạp chí chính thống -> nhận diện theo chuỗi con (lowercase).
OFFICIAL_ORG_SIGNALS = {
    "esc": "ESC", "european heart journal": "ESC", "european society of cardiology": "ESC",
    "aha": "AHA", "circulation": "AHA", "american heart association": "AHA",
    "acc": "ACC", "j am coll cardiol": "ACC", "jacc": "ACC",
    "nice": "NICE", "national institute for health and care excellence": "NICE",
    "who": "WHO", "world health organization": "WHO",
    "cdc": "CDC", "mmwr": "CDC",
    "fda": "FDA", "ema": "EMA", "mhra": "MHRA",
    "ada": "ADA", "diabetes care": "ADA", "american diabetes association": "ADA",
    "kdigo": "KDIGO", "kidney international": "KDIGO",
    "gina": "GINA", "gold": "GOLD",
    "idsa": "IDSA", "clinical infectious diseases": "IDSA",
    "eular": "EULAR", "annals of the rheumatic diseases": "EULAR",
    "american college of rheumatology": "ACR", "arthritis & rheumatology": "ACR",
    "aasld": "AASLD", "hepatology": "AASLD",
    "easl": "EASL", "journal of hepatology": "EASL",
    "uspstf": "USPSTF", "nejm": "NEJM", "new england journal of medicine": "NEJM",
    "lancet": "Lancet", "jama": "JAMA", "bmj": "BMJ",
}


def infer_study_type(title: Optional[str], document_type: Optional[str] = None,
                     journal: Optional[str] = None,
                     source_tag: Optional[str] = None) -> Optional[str]:
    """Suy ra study_type chuẩn hóa từ các tín hiệu metadata thật.

    source_tag: cờ nguồn (vd 'PPR' của Europe PMC -> preprint).
    """
    blob = " ".join(x for x in (title, document_type, journal) if x).lower()
    src = (source_tag or "").lower()

    if src in ("ppr", "preprint") or any(p in blob for p in _PREPRINT):
        return "preprint"
    if any(k in blob for k in _SR):
        return "systematic_review"
    # Guideline: ưu tiên trước RCT vì nhiều guideline có chữ 'trial' trong nền.
    if any(k in blob for k in _GUIDELINE):
        return "guideline"
    if any(k in blob for k in _RCT):
        return "rct"
    if any(k in blob for k in _COHORT):
        return "cohort"
    if any(k in blob for k in _CASE):
        return "case_series"
    if any(k in blob for k in _EDITORIAL):
        return "editorial"
    if any(k in blob for k in _NARRATIVE):
        return "narrative_review"
    # document_type thô từ API (Crossref/OpenAlex)
    dt = (document_type or "").lower()
    if dt in ("journal-article", "article", "proceedings-article", "posted-content"):
        if dt == "posted-content":
            return "preprint"
        return None  # không đủ tín hiệu -> để pipeline chấm thận trọng
    return None


def detect_official_org(title: Optional[str], journal: Optional[str] = None,
                        authors: Optional[str] = None) -> Optional[str]:
    """Nhận diện tổ chức/tạp chí chính thống. Trả tên chuẩn hoặc None.

    Khớp theo RANH GIỚI TỪ để 'who' không trúng 'patients who', 'acc' không trúng
    'vaccine'. Viết tắt dễ nhầm chỉ khớp trong trường journal/organization.
    """
    journal_blob = (journal or "").lower()
    full_blob = " ".join(x for x in (journal, title, authors) if x).lower()
    for signal, name in OFFICIAL_ORG_SIGNALS.items():
        if not isinstance(name, str):
            continue
        blob = journal_blob if signal in _AMBIGUOUS_ORG_SIGNALS else full_blob
        if re.search(rf"(?<![a-z0-9]){re.escape(signal)}(?![a-z0-9])", blob):
            return name
    return None
