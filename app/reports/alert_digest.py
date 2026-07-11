"""Bản tin CẢNH BÁO "Mới tuần này" – chỉ gồm tài liệu LẦN ĐẦU xuất hiện gần đây.

Khác báo cáo EBM tuần (tổng hợp toàn bộ kho), bản tin này tập trung CÁI MỚI:
- Guideline/khuyến cáo mới hoặc cập nhật.
- Cảnh báo an toàn thuốc CHÍNH THỨC mới (cơ quan quản lý) – ưu tiên cao nhất.
- Mục actionable mới (đáng cân nhắc thay đổi thực hành).
- Mục mới cần đọc toàn văn.
Nếu không có gì mới -> nói rõ "Không có cập nhật mới", KHÔNG bịa nội dung.
"""
from __future__ import annotations

import html as html_lib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from app.config import settings
from app.database import session_scope
from app.models import EvidenceItem
from app.services import run_state
from app.utils.logging_config import get_logger

logger = get_logger(__name__)


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d")


def _ref(r: EvidenceItem) -> str:
    parts = []
    if r.doi:
        parts.append(f"DOI:{r.doi}")
    if r.pmid:
        parts.append(f"PMID:{r.pmid}")
    if r.nct_id:
        parts.append(r.nct_id)
    if r.url:
        parts.append(r.url)
    return " ; ".join(parts) or "—"


def _is_regulatory(r: EvidenceItem) -> bool:
    return (r.study_type or "") == "regulatory_alert" or (r.source or "") in (
        "fda", "ema", "mhra", "who", "openfda") and bool(r.safety_signal)


def get_new_items(days: int = 7) -> List[EvidenceItem]:
    """Bản ghi CHÍNH lần đầu xuất hiện trong `days` ngày (theo first_seen_run_id)."""
    run_ids = run_state.recent_run_ids(days=days)
    if not run_ids:
        return []
    with session_scope() as s:
        return (s.query(EvidenceItem)
                .filter(EvidenceItem.is_primary_record.is_(True))
                .filter(EvidenceItem.first_seen_run_id.in_(run_ids))
                .order_by(EvidenceItem.practice_change_score.desc().nullslast())
                .all())


def build_alert_data(days: int = 7) -> Dict:
    items = get_new_items(days=days)
    guidelines, regulatory, actionable, need_ft, drug_signals = [], [], [], [], []
    for r in items:
        if r.source_type == "drug_safety" or r.safety_signal:
            (regulatory if _is_regulatory(r) else drug_signals).append(r)
        elif r.study_type == "guideline":
            guidelines.append(r)
        if r.is_actionable:
            actionable.append(r)
        elif r.classification == "need_full_text":
            need_ft.append(r)

    last = run_state.last_finished_run()
    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "days": days,
        "since_date": last.since_date if last else None,
        "run_mode": last.mode if last else "—",
        "total_new": len(items),
        "guidelines": guidelines, "regulatory": regulatory,
        "actionable": actionable, "need_full_text": need_ft,
        "drug_signals": drug_signals,
    }


def _bullets(rows: List[EvidenceItem]) -> List[str]:
    # 2026-07-11: escape text nguồn NGOÀI (PubMed/RSS/openFDA) trước khi vào Markdown->HTML
    # — chặn XSS nếu title/safety_signal chứa thẻ HTML/script.
    out = []
    for r in rows:
        title = html_lib.escape(r.title or "")
        safety_signal = html_lib.escape(r.safety_signal) if r.safety_signal else ""
        area = f" _({html_lib.escape(r.clinical_area)})_" if r.clinical_area else ""
        out.append(f"- **{title[:110]}**{area}\n"
                   f"  - Mức: {r.operational_evidence_level or '—'} | Tier {r.reliability_tier or '—'}"
                   f"{' | ⚠️ ' + safety_signal[:80] if safety_signal else ''}\n"
                   f"  - Nguồn: {_ref(r)}")
    return out


def render_alert_markdown(data: Dict) -> str:
    L: List[str] = [f"# 🔔 Cảnh báo EBM – Mới trong {data['days']} ngày qua\n",
                    f"*Tạo lúc: {data['generated_at']} | Chế độ: {data['run_mode']}"
                    + (f" | Lấy bài từ: {data['since_date']}" if data['since_date'] else "")
                    + "*\n"]

    if data["total_new"] == 0:
        L.append("> ✅ **Không có cập nhật mới** trong kỳ này. "
                 "Không có nội dung để cảnh báo (hệ thống không bịa tin).\n")
        return "\n".join(L)

    L.append(f"> Tổng **{data['total_new']}** tài liệu mới. Mục dưới đây CHỈ gồm cái mới "
             "lần đầu xuất hiện; không lặp lại kho cũ.\n")

    L.append(f"## ⛑️ Cảnh báo an toàn thuốc CHÍNH THỨC mới ({len(data['regulatory'])})\n")
    L.append("\n".join(_bullets(data["regulatory"])) if data["regulatory"]
             else "*Không có cảnh báo cơ quan quản lý mới.*")
    L.append("")

    L.append(f"## 📌 Guideline mới / cập nhật ({len(data['guidelines'])})\n")
    L.append("\n".join(_bullets(data["guidelines"])) if data["guidelines"]
             else "*Không có guideline mới.*")
    L.append("")

    L.append(f"## ✅ Đáng cân nhắc thay đổi thực hành – MỚI ({len(data['actionable'])})\n")
    L.append("\n".join(_bullets(data["actionable"])) if data["actionable"]
             else "*Chưa có mục actionable mới.*")
    L.append("")

    L.append(f"## 📖 Mới – cần đọc toàn văn trước khi áp dụng ({len(data['need_full_text'])})\n")
    L.append("\n".join(_bullets(data["need_full_text"])) if data["need_full_text"]
             else "*Không có.*")
    L.append("")

    if data["drug_signals"]:
        L.append(f"## 🧪 Tín hiệu an toàn thuốc mới (FAERS – KHÔNG kết luận nhân quả) "
                 f"({len(data['drug_signals'])})\n")
        L.append("\n".join(_bullets(data["drug_signals"])))
        L.append("")
    return "\n".join(L)


def export_alert_digest(days: int = 7) -> Dict[str, Path]:
    data = build_alert_data(days=days)
    md = render_alert_markdown(data)
    md_path = settings.reports_dir / f"Alert_Digest_{_stamp()}.md"
    md_path.write_text(md, encoding="utf-8")
    try:
        import markdown as md_lib
        body = md_lib.markdown(md, extensions=["tables"])
    except Exception:  # pragma: no cover
        body = "<pre>" + md.replace("<", "&lt;") + "</pre>"
    html = (f"<!doctype html><html lang='vi'><head><meta charset='utf-8'>"
            f"<title>Cảnh báo EBM mới</title><style>body{{font-family:system-ui,Arial;"
            f"max-width:1000px;margin:2rem auto;padding:0 1rem;line-height:1.55}}"
            f"blockquote{{background:#eff6ff;border-left:4px solid #3b82f6;padding:.5rem 1rem}}"
            f"h2{{border-bottom:1px solid #e5e7eb;padding-bottom:.2rem}}</style></head>"
            f"<body>{body}</body></html>")
    html_path = settings.reports_dir / f"Alert_Digest_{_stamp()}.html"
    html_path.write_text(html, encoding="utf-8")
    logger.info("Đã xuất bản tin cảnh báo: %s (%d mục mới)", md_path.name, data["total_new"])
    return {"markdown": md_path, "html": html_path, "total_new": data["total_new"]}
