"""Báo cáo tuần riêng: An toàn thuốc (Drug Safety) và Kháng sinh (Antibiotic Stewardship).

Nguyên tắc:
- Cảnh báo cơ quan quản lý (FDA/EMA/MHRA/WHO) có trọng số cao hơn tín hiệu FAERS.
- FAERS chỉ mô tả tín hiệu báo cáo tự phát, KHÔNG kết luận nhân quả.
- Báo cáo kháng sinh không cổ vũ lạm dụng; gắn phân loại WHO AWaRe khi áp dụng.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from app.config import settings
from app.database import session_scope
from app.models import EvidenceItem
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

_ANTIBIOTIC_KW = ("antibiotic", "antimicrobial", "stewardship", "kháng sinh",
                  "aware", "pneumonia", "uti", "urinary tract", "sepsis", "resistance")


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d")


def _ref(r: EvidenceItem) -> str:
    parts = []
    if r.doi:
        parts.append(f"DOI:{r.doi}")
    if r.pmid:
        parts.append(f"PMID:{r.pmid}")
    if r.url:
        parts.append(r.url)
    return " ; ".join(parts) or "Không có định danh"


def _is_regulatory(r: EvidenceItem) -> bool:
    return (r.study_type or "") == "regulatory_alert" or (r.source or "") in (
        "fda", "ema", "mhra", "who")


def _md_table(headers: List[str], rows: List[List[str]]) -> str:
    out = ["| " + " | ".join(headers) + " |",
           "| " + " | ".join("---" for _ in headers) + " |"]
    for r in rows:
        out.append("| " + " | ".join((c or "").replace("|", "/") for c in r) + " |")
    return "\n".join(out)


# --------------------------------------------------------------------------
# Drug Safety
# --------------------------------------------------------------------------
def build_drug_safety_data() -> Dict:
    with session_scope() as s:
        rows = (s.query(EvidenceItem)
                .filter(EvidenceItem.is_primary_record.is_(True))
                .filter((EvidenceItem.source_type == "drug_safety")
                        | (EvidenceItem.safety_signal.isnot(None)))
                .all())
        regulatory = [_row(r) for r in rows if _is_regulatory(r)]
        signals = [_row(r) for r in rows if not _is_regulatory(r)]
    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "regulatory": regulatory, "signals": signals,
        "counts": {"regulatory": len(regulatory), "signals": len(signals)},
    }


def _row(r: EvidenceItem) -> Dict:
    return {"title": r.title, "source": r.journal_or_organization or r.source,
            "safety_signal": r.safety_signal, "clinical_area": r.clinical_area,
            "tier": r.reliability_tier, "ref": _ref(r),
            "study_type": r.study_type}


def render_drug_safety_md(data: Dict) -> str:
    L: List[str] = ["# Báo cáo An toàn thuốc – Tuần\n",
                    f"*Tạo lúc: {data['generated_at']}*\n",
                    "> Cảnh báo cơ quan quản lý có trọng số cao hơn tín hiệu FAERS. "
                    "FAERS KHÔNG dùng để kết luận nhân quả.\n"]
    c = data["counts"]
    L.append(f"- Cảnh báo cơ quan quản lý: **{c['regulatory']}** | "
             f"Tín hiệu báo cáo tự phát (FAERS…): **{c['signals']}**\n")

    L.append("## 1. Cảnh báo chính thức (cơ quan quản lý) – ưu tiên cao\n")
    if data["regulatory"]:
        L.append(_md_table(
            ["Thuốc/Cảnh báo", "Nguồn", "Đối tượng nguy cơ / Nội dung", "Hành động", "Truy vết"],
            [[r["title"][:60], r["source"] or "", (r["safety_signal"] or "")[:90],
              "Áp dụng cảnh báo; rà soát chỉ định/liều/chống chỉ định", r["ref"]]
             for r in data["regulatory"]]))
    else:
        L.append("*Không có cảnh báo cơ quan quản lý mới tuần này.*")
    L.append("")

    L.append("## 2. Tín hiệu báo cáo tự phát (chỉ theo dõi, KHÔNG nhân quả)\n")
    if data["signals"]:
        L.append(_md_table(
            ["Tín hiệu", "Nguồn", "Mô tả", "Truy vết"],
            [[r["title"][:60], r["source"] or "", (r["safety_signal"] or "")[:90], r["ref"]]
             for r in data["signals"]]))
        L.append("\n*Lưu ý: tín hiệu FAERS cần diễn giải thận trọng, không suy luận nhân quả.*")
    else:
        L.append("*Không có tín hiệu mới.*")
    L.append("")
    L.append("## 3. Nhắc kê đơn an toàn\n"
             "- Rà soát hiệu chỉnh liều ở CKD/bệnh gan/người cao tuổi.\n"
             "- Kiểm tra tương tác thuốc–thuốc và chống chỉ định mới.\n")
    return "\n".join(L)


# --------------------------------------------------------------------------
# Antibiotic Stewardship
# --------------------------------------------------------------------------
def build_antibiotic_data() -> Dict:
    with session_scope() as s:
        rows = s.query(EvidenceItem).filter(
            EvidenceItem.is_primary_record.is_(True)).all()
        ab = [_row(r) for r in rows if _matches_antibiotic(r)]
    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "items": ab, "counts": {"items": len(ab)},
    }


def _matches_antibiotic(r: EvidenceItem) -> bool:
    text = " ".join(str(x or "") for x in (
        r.title, r.abstract, " ".join(r.keywords or []),
        r.journal_or_organization)).lower()
    return any(k in text for k in _ANTIBIOTIC_KW)


def render_antibiotic_md(data: Dict) -> str:
    L: List[str] = ["# Báo cáo Kháng sinh / Antibiotic Stewardship – Tuần\n",
                    f"*Tạo lúc: {data['generated_at']}*\n",
                    "> Không cổ vũ lạm dụng kháng sinh. Ưu tiên phân loại WHO AWaRe "
                    "(Access/Watch/Reserve) và thời gian điều trị ngắn nhất có hiệu quả.\n"]
    L.append(f"- Số mục liên quan kháng sinh/đề kháng: **{data['counts']['items']}**\n")
    L.append("## Cập nhật & cảnh báo kháng sinh\n")
    if data["items"]:
        L.append(_md_table(
            ["Nội dung", "Nguồn", "Mức tin cậy", "Áp dụng ngoại trú", "Truy vết"],
            [[r["title"][:60], r["source"] or "", r["tier"] or "",
              "Có" if (r["clinical_area"] in ("Nhiễm khuẩn", "Hô hấp")) else "Cân nhắc",
              r["ref"]] for r in data["items"]]))
    else:
        L.append("*Không có cập nhật kháng sinh đáng kể tuần này.*")
    L.append("\n## Nguyên tắc stewardship ngoại trú\n"
             "- Phân biệt nhiễm virus vs vi khuẩn trước khi kê.\n"
             "- Chọn nhóm Access khi phù hợp; hạn chế Watch/Reserve.\n"
             "- Đúng liều – đúng thời gian – đánh giá lại sau 48–72h.\n")
    return "\n".join(L)


# --------------------------------------------------------------------------
# Export
# --------------------------------------------------------------------------
def _export(md: str, html_title: str, basename: str) -> Dict[str, Path]:
    md_path = settings.reports_dir / f"{basename}_{_stamp()}.md"
    md_path.write_text(md, encoding="utf-8")
    try:
        import markdown as md_lib
        body = md_lib.markdown(md, extensions=["tables"])
    except Exception:  # pragma: no cover
        body = "<pre>" + md.replace("<", "&lt;") + "</pre>"
    html = (f"<!doctype html><html lang='vi'><head><meta charset='utf-8'>"
            f"<title>{html_title}</title><style>body{{font-family:system-ui,Arial;"
            f"max-width:1000px;margin:2rem auto;padding:0 1rem;line-height:1.5}}"
            f"table{{border-collapse:collapse;width:100%;font-size:.9rem}}"
            f"th,td{{border:1px solid #ccc;padding:4px 8px;text-align:left}}"
            f"th{{background:#f3f4f6}}blockquote{{background:#fff7ed;"
            f"border-left:4px solid #fb923c;padding:.5rem 1rem}}</style></head>"
            f"<body>{body}</body></html>")
    html_path = settings.reports_dir / f"{basename}_{_stamp()}.html"
    html_path.write_text(html, encoding="utf-8")
    return {"markdown": md_path, "html": html_path}


def export_drug_safety_report() -> Dict[str, Path]:
    data = build_drug_safety_data()
    paths = _export(render_drug_safety_md(data), "Drug Safety Weekly", "Drug_Safety_Weekly")
    logger.info("Đã xuất báo cáo an toàn thuốc: %s", paths["markdown"].name)
    return paths


def export_antibiotic_report() -> Dict[str, Path]:
    data = build_antibiotic_data()
    paths = _export(render_antibiotic_md(data), "Antibiotic Stewardship Weekly",
                    "Antibiotic_Stewardship_Weekly")
    logger.info("Đã xuất báo cáo kháng sinh: %s", paths["markdown"].name)
    return paths
