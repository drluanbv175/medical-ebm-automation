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

from sqlalchemy import or_

from app.config import settings
from app.database import session_scope
from app.models import EvidenceItem
from app.services import run_state
from app.services.filtering import la_ly_do_eoc, la_ly_do_rut_bai
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
    """True nếu đây là cảnh báo CHÍNH THỨC của cơ quan quản lý (FDA/EMA/MHRA/WHO) — KHÁC tín
    hiệu FAERS chưa xác minh (source="openfda", spontaneous report, xem app/sources/openfda.py).

    SỬA 2026-09-05 (Workflow đối kháng đa-agent, task #80, HIGH) — bản gốc:
        (A == B) or (C in D and E)   # ưu tiên toán tử `and` trước `or` trong Python
    với D = ("fda", "ema", "mhra", "who", "openfda") và E = bool(r.safety_signal). Mọi bản ghi
    nguồn openFDA (app/sources/openfda.py::search()) LUÔN có source="openfda" VÀ LUÔN có
    safety_signal được điền (`f"{count} báo cáo phản ứng..."`) — nên `C in D and E` luôn ĐÚNG
    cho MỌI bản ghi openFDA, bất kể đó chỉ là một tín hiệu FAERS tự phát CHƯA xác minh. Hậu quả:
    mọi tín hiệu FAERS bị thăng cấp thành "cảnh báo cơ quan quản lý CHÍNH THỨC – ưu tiên cao
    nhất" trong bản tin — ngược hẳn nguyên tắc chính module tự khai ở dòng 5 và ở
    `app/integrations/drug_interactions.py`: "FAERS là báo cáo tự phát... KHÔNG suy luận quan hệ
    nhân quả".

    Đã đối chiếu với hàm sinh đôi cùng chức năng `app/reports/safety_reports.py::_is_regulatory()`
    (cùng nguyên tắc phân biệt FAERS/regulatory ở docstring đầu file đó) — hàm đó KHÔNG có
    "openfda" trong tuple và KHÔNG có mệnh đề `and bool(r.safety_signal)`. Sửa theo đúng hàm đó:
    bỏ "openfda" khỏi tuple nguồn quy phạm, bỏ mệnh đề an toàn_signal thừa gây sai độ ưu tiên.
    """
    return (r.study_type or "") == "regulatory_alert" or (r.source or "") in (
        "fda", "ema", "mhra", "who")


def get_new_items(days: int = 7, chi_live: bool = False) -> List[EvidenceItem]:
    """Bản ghi CHÍNH lần đầu xuất hiện trong `days` ngày (theo first_seen_run_id).

    chi_live=True (đường GỬI cảnh báo — vá 26/09/2026, synthesis #6): chỉ mục do lượt
    mode=="live" đưa vào kho, VÀ cờ is_mock khác True (phòng thủ nhiều lớp). Lọc is_mock
    MỘT MÌNH không đủ: mục mock của RSS cũ trong DB mang is_mock=0. chi_live=False (hiển
    thị): giữ mọi mục, `build_alert_data` gắn nhãn DEMO cho mục của lượt mock."""
    run_ids = run_state.recent_run_ids(days=days, mode="live" if chi_live else None)
    if not run_ids:
        return []
    with session_scope() as s:
        q = (s.query(EvidenceItem)
             .filter(EvidenceItem.is_primary_record.is_(True))
             .filter(EvidenceItem.first_seen_run_id.in_(run_ids)))
        if chi_live:
            q = q.filter(or_(EvidenceItem.is_mock.is_(None), EvidenceItem.is_mock.is_(False)))
        return q.order_by(EvidenceItem.practice_change_score.desc().nullslast()).all()


def _mo_ta_che_do(modes: List[str], mac_dinh: str) -> str:
    """Dòng «Chế độ» theo các lượt ĐÃ GÓP mục (không theo lượt 'ok' mới nhất)."""
    tap = {m or "?" for m in modes}
    if not tap:
        return mac_dinh
    if tap == {"live"}:
        return "live"
    if "live" in tap:
        return "live + mock (DEMO)"
    return "mock (DEMO)"


def build_alert_data(days: int = 7, chi_live: bool = False) -> Dict:
    items = get_new_items(days=days, chi_live=chi_live)
    mode_theo_luot = run_state.run_modes({r.first_seen_run_id for r in items})
    # Mục DEMO = lượt đưa vào không phải live (kể cả không rõ lượt) HOẶC cờ is_mock.
    demo_ids = {r.id for r in items
                if r.is_mock or mode_theo_luot.get(r.first_seen_run_id) != "live"}
    guidelines, regulatory, actionable, need_ft, drug_signals = [], [], [], [], []
    retracted: List[EvidenceItem] = []
    for r in items:
        # Vá 26/09/2026 (synthesis #4): bài ĐÃ BỊ RÚT không bao giờ vào danh sách guideline/
        # actionable/cảnh báo — liệt kê ở mục đỏ riêng, không xoá im lặng.
        if r.classification == "excluded" and la_ly_do_rut_bai(r.reason_for_exclusion):
            retracted.append(r)
            continue
        if r.source_type == "drug_safety" or r.safety_signal:
            (regulatory if _is_regulatory(r) else drug_signals).append(r)
        elif r.study_type == "guideline" and r.classification != "excluded":
            guidelines.append(r)
        if r.is_actionable:
            actionable.append(r)
        elif r.classification == "need_full_text":
            need_ft.append(r)

    last = run_state.last_live_ok_run() if chi_live else run_state.last_finished_run()
    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "days": days,
        "since_date": last.since_date if last else None,
        "run_mode": _mo_ta_che_do([mode_theo_luot.get(r.first_seen_run_id, "") for r in items],
                                  last.mode if last else "—"),
        "total_new": len(items),
        "guidelines": guidelines, "regulatory": regulatory,
        "actionable": actionable, "need_full_text": need_ft,
        "drug_signals": drug_signals,
        "retracted": retracted,
        "chi_live": chi_live,
        "demo_ids": demo_ids, "n_demo": len(demo_ids),
    }


_NHAN_DEMO = "🧪 [DEMO — dữ liệu mẫu, KHÔNG phải tin thật] "


def _bullets(rows: List[EvidenceItem], demo_ids=frozenset()) -> List[str]:
    # 2026-07-11: escape text nguồn NGOÀI (PubMed/RSS/openFDA) trước khi vào Markdown->HTML
    # — chặn XSS nếu title/safety_signal chứa thẻ HTML/script.
    out = []
    for r in rows:
        title = html_lib.escape(r.title or "")
        safety_signal = html_lib.escape(r.safety_signal) if r.safety_signal else ""
        area = f" _({html_lib.escape(r.clinical_area)})_" if r.clinical_area else ""
        nhan = _NHAN_DEMO if r.id in demo_ids else ""
        if la_ly_do_eoc(r.reason_for_exclusion):
            nhan += "🟠 [Có Expression of Concern] "
        out.append(f"- {nhan}**{title[:110]}**{area}\n"
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
    demo_ids = data.get("demo_ids") or frozenset()
    if demo_ids:
        L.append(f"> 🧪 **{len(demo_ids)} mục là DỮ LIỆU MẪU (DEMO — do lượt chạy mock đưa vào)**: "
                 "chỉ để xem thử giao diện, KHÔNG phải tin thật, KHÔNG bao giờ được gửi "
                 "email/webhook. Các mục này mang nhãn 🧪 [DEMO] bên dưới.\n")

    retracted = data.get("retracted") or []
    if retracted:
        L.append(f"## ⛔ Bài đã bị rút — KHÔNG dùng ({len(retracted)})\n")
        L.append("> Nguồn (PubMed/Europe PMC) gắn nhãn rút bài cho các mục dưới đây: đã LOẠI khỏi "
                 "guideline/actionable/cảnh báo và không đưa sang EBM_MASTER. Liệt kê để bác sĩ "
                 "biết, KHÔNG dùng lâm sàng.\n")
        out_rut = []
        for dong, r in zip(_bullets(retracted, demo_ids), retracted):
            ly_do = html_lib.escape(r.reason_for_exclusion or "")
            out_rut.append(f"{dong}\n  - Lý do: {ly_do[:220]}")
        L.append("\n".join(out_rut))
        L.append("")

    L.append(f"## ⛑️ Cảnh báo an toàn thuốc CHÍNH THỨC mới ({len(data['regulatory'])})\n")
    L.append("\n".join(_bullets(data["regulatory"], demo_ids)) if data["regulatory"]
             else "*Không có cảnh báo cơ quan quản lý mới.*")
    L.append("")

    L.append(f"## 📌 Guideline mới / cập nhật ({len(data['guidelines'])})\n")
    L.append("\n".join(_bullets(data["guidelines"], demo_ids)) if data["guidelines"]
             else "*Không có guideline mới.*")
    L.append("")

    L.append(f"## ✅ Đáng cân nhắc thay đổi thực hành – MỚI ({len(data['actionable'])})\n")
    L.append("\n".join(_bullets(data["actionable"], demo_ids)) if data["actionable"]
             else "*Chưa có mục actionable mới.*")
    L.append("")

    L.append(f"## 📖 Mới – cần đọc toàn văn trước khi áp dụng ({len(data['need_full_text'])})\n")
    L.append("\n".join(_bullets(data["need_full_text"], demo_ids)) if data["need_full_text"]
             else "*Không có.*")
    L.append("")

    if data["drug_signals"]:
        L.append(f"## 🧪 Tín hiệu an toàn thuốc mới (FAERS – KHÔNG kết luận nhân quả) "
                 f"({len(data['drug_signals'])})\n")
        L.append("\n".join(_bullets(data["drug_signals"], demo_ids)))
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
