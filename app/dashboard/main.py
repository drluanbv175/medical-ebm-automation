"""Streamlit dashboard điều hành – 12 tab theo đề bài.

Chạy: python run.py dashboard  (hoặc: python -m streamlit run app/dashboard/main.py)
"""
from __future__ import annotations

import html as _html  # noqa: E402
import re as _re  # noqa: E402
import sys
from pathlib import Path

# Cho phép chạy trực tiếp bằng `streamlit run app/dashboard/main.py`
ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from app.config import settings  # noqa: E402
from app.database import init_db, session_scope  # noqa: E402
from app.models import (  # noqa: E402
    ChangeLogEntry,
    ClinicalScore,
    EvidenceItem,
    ResearchProject,
    SourceLog,
)
from app.reports import (  # noqa: E402
    build_alert_data,
    export_alert_digest,
    export_antibiotic_report,
    export_dashboard_excel,
    export_drug_safety_report,
    export_research_tracker_excel,
    export_source_log_csv,
    export_weekly_ebm_html,
    export_weekly_ebm_markdown,
    export_zotero_bibtex,
    render_alert_markdown,
)
from app.services.pipeline import run_pipeline  # noqa: E402
from app.utils.seed import seed_all  # noqa: E402
from app.utils.text import clean_text  # noqa: E402

st.set_page_config(page_title="Medical EBM Automation", layout="wide")

# --- HỆ THỐNG THIẾT KẾ "Evidence Workbench" (nền sáng, nhấn teal/blue) ----------
st.markdown("""
<style>
  /* DÙNG FONT MẶC ĐỊNH của Streamlit (hiển thị tiếng Việt chuẩn) — KHÔNG nạp font ngoài. */
  :root{
    --ink:#0f172a; --ink2:#334155; --muted:#64748b; --line:#e2e8f0; --line2:#cbd5e1;
    --bg:#f4f7fb; --surface:#ffffff; --surface2:#f8fafc;
    --primary:#0e7490; --primary2:#0891b2; --accent:#2563eb;
    --apply:#16a34a; --consider:#ca8a04; --notyet:#ea580c; --danger:#dc2626;
    --shadow:0 1px 2px rgba(15,23,42,.04),0 2px 8px rgba(15,23,42,.06);
  }
  .stApp { background:var(--bg); }
  .block-container { padding-top: 3.2rem; padding-bottom: 1.2rem;
                     padding-left: 2rem; padding-right: 2rem; max-width: 1520px; }

  /* ---------- TABS (kiểu pill, nhấn teal) ---------- */
  div[data-testid="stTabs"] { position: relative; z-index: 1; }
  div[data-testid="stTabs"] [data-baseweb="tab-list"]{
    gap:2px; background:var(--surface); padding:5px; border-radius:12px;
    border:1px solid var(--line); box-shadow:var(--shadow); flex-wrap:wrap; }
  button[data-baseweb="tab"]{ font-size:.86rem; font-weight:600; color:var(--muted);
    border-radius:8px; padding:6px 12px; }
  button[data-baseweb="tab"]:hover{ background:var(--surface2); color:var(--ink2); }
  button[data-baseweb="tab"][aria-selected="true"]{
    background:linear-gradient(135deg,var(--primary),var(--primary2)); color:#fff; }
  div[data-testid="stTabs"] [data-baseweb="tab-highlight"],
  div[data-testid="stTabs"] [data-baseweb="tab-border"]{ display:none; }

  /* ---------- METRIC -> THẺ KPI ---------- */
  div[data-testid="stMetric"]{ background:var(--surface); padding:12px 14px 11px;
    border:1px solid var(--line); border-radius:12px; box-shadow:var(--shadow);
    position:relative; overflow:hidden; transition:transform .12s,box-shadow .12s; }
  div[data-testid="stMetric"]:hover{ transform:translateY(-2px);
    box-shadow:0 4px 14px rgba(15,23,42,.10); }
  div[data-testid="stMetric"]::before{ content:""; position:absolute; left:0; top:0;
    bottom:0; width:4px; background:linear-gradient(180deg,var(--primary),var(--accent)); }
  div[data-testid="stMetricValue"]{ font-size:1.7rem; font-weight:800; color:var(--ink);
    font-variant-numeric:tabular-nums; letter-spacing:-.5px; }
  div[data-testid="stMetricLabel"] p{ font-size:.7rem; font-weight:700; color:var(--muted);
    text-transform:uppercase; letter-spacing:.4px; }

  /* ---------- TIÊU ĐỀ ---------- */
  h1{ font-size:1.55rem !important; font-weight:800; letter-spacing:-.4px; }
  h2{ font-size:1.2rem !important; font-weight:700; color:var(--ink);
      padding-left:11px; border-left:4px solid var(--primary); margin:.3rem 0 .6rem; }
  h3{ font-size:1.02rem !important; font-weight:700; color:var(--ink2); }
  h4{ font-size:1rem !important; margin:.5rem 0 .15rem !important;
      color:var(--primary); font-weight:700; }

  /* ---------- NÚT ---------- */
  div[data-testid="stButton"] button{ border-radius:9px; font-weight:600;
    border:1px solid var(--line); transition:.12s; }
  div[data-testid="stButton"] button:hover{ border-color:var(--primary2);
    box-shadow:var(--shadow); }
  div[data-testid="stButton"] button[kind="primary"]{
    background:linear-gradient(135deg,var(--primary),var(--primary2));
    border:0; box-shadow:0 2px 8px rgba(14,116,144,.30); }

  /* ---------- SIDEBAR ---------- */
  section[data-testid="stSidebar"]{ background:var(--surface);
    border-right:1px solid var(--line); }
  section[data-testid="stSidebar"] .block-container{ padding-top:1.2rem; }

  /* ---------- ALERT / EXPANDER / DATAFRAME mềm mại ---------- */
  div[data-testid="stAlert"]{ border-radius:10px; border:1px solid var(--line);
    box-shadow:var(--shadow); }
  details[data-testid="stExpander"], div[data-testid="stExpander"]{
    border:1px solid var(--line) !important; border-radius:11px !important;
    box-shadow:var(--shadow); background:var(--surface); }
  div[data-testid="stDataFrame"]{ border:1px solid var(--line); border-radius:11px;
    overflow:hidden; box-shadow:var(--shadow); }

  /* ---------- KPI STRIP (thẻ chỉ số có màu ngữ nghĩa) ---------- */
  .kpi-strip{ display:grid; grid-template-columns:repeat(4,1fr); gap:11px; margin:.2rem 0 .4rem; }
  @media(min-width:1200px){ .kpi-strip{ grid-template-columns:repeat(8,1fr); } }
  .kpi{ background:var(--surface); border:1px solid var(--line); border-radius:12px;
    padding:11px 13px; box-shadow:var(--shadow); position:relative; overflow:hidden;
    transition:transform .12s,box-shadow .12s; }
  .kpi:hover{ transform:translateY(-2px); box-shadow:0 4px 14px rgba(15,23,42,.10); }
  .kpi::before{ content:""; position:absolute; left:0; top:0; bottom:0; width:4px;
    background:var(--c,#0e7490); }
  .kpi .kl{ font-size:.66rem; font-weight:700; color:var(--muted); text-transform:uppercase;
    letter-spacing:.4px; display:flex; align-items:center; gap:5px; }
  .kpi .kv{ font-size:1.7rem; font-weight:800; color:var(--ink); letter-spacing:-.5px;
    font-variant-numeric:tabular-nums; line-height:1.15; margin-top:2px; }
  .kpi .kv.c{ color:var(--c,#0f172a); }

  /* Giảm khoảng cách dọc giữa các khối */
  div[data-testid="stVerticalBlock"] { gap: .45rem; }
  /* Blockquote (câu trích) gọn, ít khoảng trắng */
  blockquote { margin: .1rem 0 !important; padding: .05rem .7rem !important;
               border-left: 3px solid #cfd8e3 !important; }
  blockquote p { margin-bottom: .1rem !important; }
  /* Đoạn văn markdown sát nhau hơn */
  div[data-testid="stMarkdownContainer"] p { margin-bottom: .25rem; }
  div[data-testid="stCaptionContainer"] { margin-top: -.15rem; }
  /* Bảng PICO chuẩn mực: kẻ đều, căn lề trên, chữ cân đối */
  table.pico { border-collapse: collapse; width: 100%; margin: .2rem 0 .5rem;
               font-size: .92rem; line-height: 1.5; table-layout: fixed; }
  table.pico th, table.pico td { border: 1px solid #e1e7ef; padding: 8px 12px;
                                  vertical-align: top; text-align: left;
                                  word-break: break-word; }
  table.pico th.lbl { width: 175px; background: #eef3fa; font-weight: 700;
                      color: #1f3a5f; }
  /* Mỗi câu trích = 1 gạch đầu dòng, cách đều nhau */
  table.pico .qrow { position: relative; padding-left: 16px; margin-bottom: 9px; }
  table.pico .qrow:last-child { margin-bottom: 0; }
  table.pico .qrow::before { content: "•"; position: absolute; left: 2px; top: 0;
                             color: #3b7dd8; font-weight: 700; }
  table.pico .vi { color: #1a1f29; margin: 0 0 2px; }
  table.pico .en { color: #6b7686; font-style: italic; font-size: .84rem;
                   margin: 0; padding-left: 2px; }
  table.pico .na { color: #9aa3af; font-style: italic; }
</style>
""", unsafe_allow_html=True)

init_db()


def _df(query_fn):
    with session_scope() as s:
        return pd.DataFrame(query_fn(s))


def _clean(text):
    """Bỏ thẻ HTML + giải mã ký tự để hiển thị tiêu đề sạch."""
    if not text:
        return text
    text = _re.sub(r"<[^>]+>", "", str(text))
    text = _html.unescape(text)
    return _re.sub(r"\s+", " ", text).strip()


@st.cache_data(show_spinner=False)
def _tr_vi(text: str):
    """Dịch máy EN->VI (cache theo phiên + file). None nếu tiếng Việt sẵn/lỗi/offline."""
    from app.services.translate import translate_vi
    return translate_vi(text)


def _evidence_rows(s, **filters):
    from app.services import run_state
    new_run_ids = run_state.recent_run_ids(days=7)
    q = s.query(EvidenceItem).filter(EvidenceItem.is_primary_record.is_(True))
    for k, v in filters.items():
        q = q.filter(getattr(EvidenceItem, k) == v)
    return [{
        "is_new": r.first_seen_run_id in new_run_ids if new_run_ids else False,
        "id": r.id, "clinical_area": r.clinical_area, "title": _clean(r.title),
        "source": r.journal_or_organization or r.source, "study_type": r.study_type,
        "evidence_quality": r.evidence_quality_score,
        "practice_change": r.practice_change_score, "tier": r.reliability_tier,
        "evidence_level": r.operational_evidence_level,
        "classification": r.classification, "actionable": r.is_actionable,
        "safety_signal": r.safety_signal, "doi": r.doi, "pmid": r.pmid,
        "nct_id": r.nct_id, "url": r.url,
    } for r in q.order_by(EvidenceItem.practice_change_score.desc().nullslast()).all()]


def _evidence_detail(item_id: int):
    """Lấy đầy đủ một bản ghi chứng cứ (kèm synthesis) theo id."""
    with session_scope() as s:
        r = s.get(EvidenceItem, item_id)
        if not r:
            return None
        return {
            "id": r.id, "title": _clean(r.title), "clinical_area": r.clinical_area,
            "source_type": r.source_type,
            "authors": r.authors, "source": r.journal_or_organization or r.source,
            "publication_date": r.publication_date, "study_type": r.study_type,
            "document_type": r.document_type, "guideline_version": r.guideline_version,
            "evidence_quality": r.evidence_quality_score,
            "practice_change": r.practice_change_score, "tier": r.reliability_tier,
            "evidence_level": r.operational_evidence_level, "official_grade": r.official_grade,
            "classification": r.classification, "actionable": r.is_actionable,
            "actionable_reason": r.actionable_reason,
            "reason_for_exclusion": r.reason_for_exclusion,
            "safety_signal": r.safety_signal, "abstract": r.abstract,
            "doi": r.doi, "pmid": r.pmid, "nct_id": r.nct_id, "url": r.url,
            "synthesis": r.synthesis or {},
        }


def _ref_line(d: dict) -> str:
    parts = []
    if d.get("doi"):
        parts.append(f"DOI: {d['doi']}")
    if d.get("pmid"):
        parts.append(f"PMID: {d['pmid']}")
    if d.get("nct_id"):
        parts.append(d["nct_id"])
    if d.get("url"):
        parts.append(d["url"])
    return " · ".join(parts) or "—"


_TIER_NOTE = {
    "A": "🟢 Tier A — có thể cân nhắc áp dụng ngay nếu phù hợp bối cảnh (vẫn nên đọc nguồn gốc).",
    "B": "🟡 Tier B — cần đọc toàn văn / guideline gốc trước khi triển khai.",
    "C": "🟠 Tier C — chỉ theo dõi, chứng cứ chưa đủ để thay đổi thực hành.",
    "D": "🔴 Tier D — loại khỏi áp dụng thực hành (preprint/nghiên cứu yếu...).",
}


def _application_hint(d: dict) -> str:
    """Gợi ý CÁCH TIẾP CẬN áp dụng theo LOẠI chứng cứ (định hướng, KHÔNG bịa chỉ định cụ thể)."""
    st_ = (d.get("study_type") or "").lower()
    if st_ == "regulatory_alert" or d.get("source_type") == "drug_safety" or d.get("safety_signal"):
        return ("Cảnh báo/khuyến cáo chính thức từ cơ quan quản lý → **rà soát bệnh nhân đang dùng "
                "nhóm thuốc liên quan**; áp dụng nội dung cảnh báo (theo dõi dấu hiệu, điều chỉnh/ngưng "
                "thuốc như mô tả); cập nhật quy trình kê đơn. Đọc nguyên văn cảnh báo ở nguồn gốc.")
    if st_ == "guideline":
        return ("Đây là khuyến cáo/guideline → **đọc khuyến cáo gốc và áp dụng theo phác đồ cơ sở của bạn**; "
                "đối chiếu các điểm trích (khuyến cáo, đối tượng, liều, ngưỡng) với từng bệnh nhân cụ thể.")
    if st_ == "systematic_review":
        return ("Tổng quan hệ thống/phân tích gộp (mức chứng cứ cao) → cân nhắc **cập nhật thực hành nếu "
                "phù hợp guideline nền và bối cảnh bệnh nhân**; xem phần Kết quả & An toàn trích bên dưới.")
    if st_ == "rct":
        return ("Một thử nghiệm lâm sàng đơn lẻ → **KHÔNG đổi thực hành chỉ dựa vào 1 nghiên cứu**. "
                "Đối chiếu guideline nền, cỡ mẫu, đối tượng và khả năng lặp lại trước khi áp dụng.")
    return ("Đọc toàn văn nguồn gốc và **đối chiếu guideline nền + bối cảnh bệnh nhân** trước khi áp dụng. "
            "Chứng cứ hiện chưa đủ mạnh để tự thay đổi thực hành.")


def render_clinical_application(d: dict) -> None:
    """Hiển thị tóm tắt giúp HIỂU nghiên cứu + ĐỊNH HƯỚNG áp dụng (không bịa)."""
    syn = d.get("synthesis") or {}
    st.markdown(f"### 📋 {d['title']}")
    meta = " · ".join(filter(None, [
        d.get("clinical_area"), d.get("source"),
        (d.get("publication_date") or "")[:10], d.get("study_type")]))
    st.caption(meta)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Chất lượng CC", f"{d.get('evidence_quality') or '—'}")
    c2.metric("Đổi thực hành", f"{d.get('practice_change') or '—'}")
    c3.metric("Độ tin cậy", d.get("tier") or "—")
    c4.metric("Mức CC", str(d.get("evidence_level") or "—")[:14])
    if d.get("tier") in _TIER_NOTE:
        (st.success if d["tier"] == "A" else st.warning if d["tier"] in ("B",)
         else st.info)(_TIER_NOTE[d["tier"]])

    # Làm sạch abstract (gỡ thẻ XML, giải mã &ge;->≥) + TRÍCH nguyên văn (không bịa)
    abstract = clean_text(d.get("abstract")) or ""
    from app.services.extraction import (
        extract_clinical_points,
        extract_conclusion,
        extract_pico,
        label_for,
        ordered_categories,
        pico_display_order,
        pico_label,
    )
    pico = extract_pico(abstract)
    clin = extract_clinical_points(abstract)
    concl = extract_conclusion(abstract)

    def _vi(s):
        return (_tr_vi(s) or s) if s else None

    def _first(*lists):
        for lst in lists:
            if lst:
                return lst[0]
        return None

    def _is_aimish(s):
        low = (s or "").lower()
        return any(c in low for c in ("we aim", "aimed to", "to evaluate", "to assess",
                                      "to determine", "objective", "the purpose of",
                                      "we sought", "we investigated", "mục đích", "nhằm"))

    _STAT = _re.compile(r"\d|hazard ratio|odds ratio|risk ratio|95% ?ci|p\s*[<=]|"
                        r"no significant|no difference|reduced|increased|mortality",
                        _re.IGNORECASE)

    def _best_result(*lists):
        """Chọn câu KẾT QUẢ thực (có số/thống kê, KHÔNG phải câu mục tiêu)."""
        cands = []
        for lst in lists:
            if lst:
                cands.extend(lst)
        ranked = [s for s in cands if _STAT.search(s) and not _is_aimish(s)]
        if ranked:
            return ranked[0]
        non_aim = [s for s in cands if not _is_aimish(s)]
        return (non_aim or cands or [None])[0]

    # ===== 1) 🎯 ĐIỂM MẤU CHỐT — ÁP DỤNG LÂM SÀNG (đặt ĐẦU: trả lời "dùng được gì") =====
    st.markdown("#### 🎯 Điểm mấu chốt — Áp dụng lâm sàng")
    if concl:
        with st.spinner("Đang dịch kết luận..."):
            for s in concl:
                vi = _tr_vi(s)
                st.markdown(f"> 🎯 **Kết luận của tác giả:** {vi or s}")
                if vi:
                    st.caption(f"📄 {s}")
    # Bảng áp dụng: Ai → Khuyến cáo/Kết quả → Có nên đổi → (lý do) — đều từ nguồn
    pop = _first(pico.get("P"), clin.get("doi_tuong"))
    rec = _first(clin.get("khuyen_cao"))
    res = _best_result(clin.get("ket_qua"), pico.get("O"))
    if d.get("actionable"):
        verdict = "✅ Có thể cân nhắc áp dụng (nếu hợp bối cảnh & từng bệnh nhân)."
    elif d.get("classification") == "need_full_text":
        verdict = "🟡 Chưa chắc — cần đọc toàn văn / guideline gốc trước."
    else:
        verdict = "⏸️ Chưa — theo dõi thêm, chưa đủ để đổi thực hành."
    apply_rows = [("Áp dụng cho ai", _vi(pop) or d.get("clinical_area") or "—")]
    if rec:
        apply_rows.append(("Khuyến cáo nêu trong nguồn", _vi(rec)))
    if res:
        apply_rows.append(("Hiệu quả / kết quả chính", _vi(res)))
    apply_rows.append(("Có nên đổi thực hành?", verdict))
    if d.get("reason_for_exclusion"):
        apply_rows.append(("Vì sao chưa nên áp dụng", d["reason_for_exclusion"]))
    st.markdown('<table class="pico">'
                + "".join(f'<tr><th class="lbl">{_html.escape(k)}</th>'
                          f'<td>{_html.escape(str(v))}</td></tr>' for k, v in apply_rows)
                + '</table>', unsafe_allow_html=True)
    st.success(f"**👉 Việc cần làm:** {_application_hint(d)}")
    safety = clean_text(d.get("safety_signal")) or syn.get("canh_bao_can_trong")
    if safety and safety != "Không có cảnh báo an toàn đặc biệt.":
        st.warning(f"**⚠️ Cảnh báo / thận trọng:** {safety}")
    st.caption("Mọi câu là **trích nguyên văn** từ nguồn; tiếng Việt là **dịch máy (tham khảo)**. "
               "Luôn đối chiếu nguồn gốc & dùng phán đoán lâm sàng.")

    # ===== 2) 🧬 CHI TIẾT THEO PICO / NỘI DUNG CHÍNH (trích nguyên văn) =====
    def _cell(items):
        """Mỗi câu = 1 gạch đầu dòng: tiếng Việt (thường) + nguyên văn EN (nghiêng) dưới."""
        from app.services.translate import translate_vi_batch
        vis = translate_vi_batch(list(items))  # dịch cả cụm trong 1 lượt gọi mạng (nhanh hơn)
        blocks = []
        for s, vi in zip(items, vis):
            en = _html.escape(s)
            if vi and _html.escape(vi) != en:
                blocks.append(f'<div class="qrow"><div class="vi">{_html.escape(vi)}</div>'
                              f'<div class="en">{en}</div></div>')
            else:
                blocks.append(f'<div class="qrow"><div class="vi">{en}</div></div>')
        return "".join(blocks)

    has_pico = any(pico.get(c) for c in pico_display_order())
    rows_html = []
    if has_pico:
        title2 = "🧬 Chi tiết theo PICO (trích nguyên văn)"
        shown = set()
        for cat in pico_display_order():
            items = pico.get(cat) or []
            for s in items:
                shown.add(s)
            content = _cell(items) if items else \
                '<div class="na">— Không nêu rõ trong abstract (xem nguồn gốc) —</div>'
            rows_html.append(f'<tr><th class="lbl">{_html.escape(pico_label(cat))}</th>'
                             f'<td>{content}</td></tr>')
        for ecat, lbl in (("an_toan", "⚠️ An toàn / Thận trọng"),
                          ("lieu", "💊 Liều / Hiệu chỉnh")):
            extra = [s for s in clin.get(ecat, []) if s not in shown]
            if extra:
                rows_html.append(f'<tr><th class="lbl">{lbl}</th><td>{_cell(extra)}</td></tr>')
    elif clin:
        title2 = "🧬 Chi tiết nội dung chính (trích nguyên văn)"
        for cat in ordered_categories():
            items = clin.get(cat) or []
            if items:
                rows_html.append(f'<tr><th class="lbl">{_html.escape(label_for(cat))}</th>'
                                 f'<td>{_cell(items)}</td></tr>')
    else:
        title2 = None

    if rows_html:
        if d.get("study_type"):
            rows_html.append(f'<tr><th class="lbl">Thiết kế / Loại</th>'
                             f'<td><b>{_html.escape(d["study_type"])}</b></td></tr>')
        with st.expander(f"{title2} — bấm để xem", expanded=False):
            st.markdown('<table class="pico">' + "".join(rows_html) + '</table>',
                        unsafe_allow_html=True)

    # ===== 3) 📖 TÓM TẮT TOÀN VĂN (thu gọn — mở khi cần đọc sâu) =====
    if abstract:
        with st.expander("📖 Tóm tắt toàn văn (dịch + nguyên văn) — bấm để mở", expanded=False):
            vi_abs = _tr_vi(abstract)
            if vi_abs:
                st.markdown(f"🇻🇳 {vi_abs}")
                st.caption("📄 Nguyên văn (tiếng Anh):")
                st.write(abstract)
            else:
                st.markdown(abstract)
    else:
        st.caption("(Nguồn này không kèm abstract — bấm 🔗 mở nguồn gốc để đọc đầy đủ.)")

    # 4) NGUỒN ----------------------------------------------------------------
    st.markdown(f"**🔎 Nguồn truy vết:** {_ref_line(d)}")
    if d.get("url"):
        st.markdown(f"[🔗 Mở nguồn gốc để đọc đầy đủ]({d['url']})")
    extra = []
    if d.get("evidence_quality") is not None:
        extra.append(f"Chất lượng CC {d['evidence_quality']}")
    if d.get("practice_change") is not None:
        extra.append(f"Đổi thực hành {d['practice_change']}")
    st.caption(f"({' · '.join(extra)} — điểm số là đánh giá VẬN HÀNH của hệ thống, không thay thẩm định "
               "GRADE chính thức.) ⚠️ Luôn đọc nguồn gốc & dùng phán đoán lâm sàng của bạn.")


def _open_path_in_browser(path) -> bool:
    """Mở file HTML bằng trình duyệt mặc định trên máy (server = máy bác sĩ)."""
    try:
        import subprocess as _sp
        import sys as _sys
        if _sys.platform == "darwin":
            _sp.Popen(["open", str(path)])
        elif _sys.platform.startswith("win"):
            import os as _os
            _os.startfile(str(path))  # type: ignore[attr-defined]
        else:
            _sp.Popen(["xdg-open", str(path)])
        return True
    except Exception:
        return False


def render_item_dark(item_id: int, key_prefix: str, detail=None, height=780) -> None:
    """Hiển thị item đã chọn theo mẫu DARK ANALYST (nền tối, 3 cột) — theo skill /dark-analyst.

    Có nút mở toàn màn hình + tải; kèm lựa chọn xem 'Thẻ chi tiết (sáng)' khi cần đọc text.
    """
    import streamlit.components.v1 as _comp

    from app.reports.evidence_workbench import OUT_DIR as _OUT
    from app.reports.evidence_workbench import render_item_dashboard
    view = st.radio("Kiểu hiển thị", ["🌑 Dark Analyst", "📄 Thẻ chi tiết (sáng)"],
                    horizontal=True, key=f"{key_prefix}_view", label_visibility="collapsed")
    if view.startswith("🌑"):
        with st.spinner("Đang dựng Dark Analyst (việt hoá + thẩm định)…"):
            html = render_item_dashboard(item_id, dark=True, vi=True)
        if not html:
            st.warning("Không dựng được Dark Analyst cho item này — xem thẻ chi tiết.")
            d = detail or _evidence_detail(item_id)
            if d:
                render_clinical_application(d)
            return
        b1, b2 = st.columns(2)
        if b1.button("🌐 Mở toàn màn hình (trình duyệt)", key=f"{key_prefix}_open"):
            _OUT.mkdir(parents=True, exist_ok=True)
            fp = _OUT / f"_view_DarkAnalyst_item_{item_id}.html"
            fp.write_text(html, encoding="utf-8")
            st.success("Đã mở trong trình duyệt." if _open_path_in_browser(fp)
                       else f"Mở thủ công: {fp}")
        b2.download_button("⬇️ Tải .html", html, key=f"{key_prefix}_dl",
                           file_name=f"DarkAnalyst_item_{item_id}.html", mime="text/html")
        _comp.html(html, height=height, scrolling=True)
    else:
        d = detail or _evidence_detail(item_id)
        if d:
            with st.container(border=True):
                render_clinical_application(d)


@st.cache_data(show_spinner=False)
def _dark_dashboard_html(ids_tuple, topic, vi=True):
    """Dựng (cache) HTML Dark Analyst nhiều item. vi=True: dịch ĐẦY ĐỦ (gộp 1 lượt, nhanh,
    rồi cache). vi=False: giữ nguyên văn tiếng Anh (xem nhanh). Cache theo (ids, topic, vi)."""
    from app.reports.evidence_workbench import render_dashboard_for_ids
    return render_dashboard_for_ids(list(ids_tuple), question=topic, dark=True, vi=vi,
                                    verify_pmids=False, cache_only=False)


def _dark_view(html, key, n_shown, n_total, height=880):
    """Khối hiển thị chung: nút mở toàn màn hình + tải + nhúng iframe."""
    import streamlit.components.v1 as _comp
    if not html:
        st.warning("Không dựng được dashboard cho nhóm này.")
        return
    bo, bd = st.columns(2)
    if bo.button("🌐 Mở toàn màn hình", key=f"{key}_open"):
        from app.reports.evidence_workbench import OUT_DIR as _O
        _O.mkdir(parents=True, exist_ok=True)
        fp = _O / f"_view_DarkAnalyst_{key}.html"
        fp.write_text(html, encoding="utf-8")
        st.success("Đã mở trong trình duyệt." if _open_path_in_browser(fp)
                   else f"Mở thủ công: {fp}")
    bd.download_button("⬇️ Tải .html", html, key=f"{key}_dl",
                       file_name=f"DarkAnalyst_{key}.html", mime="text/html")
    st.caption(f"Hiển thị {n_shown}/{n_total} · **bấm item trong bảng tối** để mở panel "
               "thẩm định bên phải. **Mở toàn màn hình** để xem trọn 3 cột.")
    _comp.html(html, height=height, scrolling=True)


def render_dark_tab(rows, topic, key, default_n=10, height=880):
    """TỰ HIỆN nhóm chứng cứ dưới dạng Dark Analyst 3 cột, ĐÃ VIỆT HOÁ ĐẦY ĐỦ (mặc định).

    Lần đầu dịch (gộp 1 lượt, nhanh) rồi cache → các lần sau tức thì. Tick 'Xem tiếng Anh'
    để bỏ dịch (xem ngay).
    """
    if not rows:
        st.info("Không có item cho mục này.")
        return
    c1, c2 = st.columns([1.2, 2.6])
    min_n, max_n = (1 if len(rows) < 5 else 5), min(40, len(rows))
    n = c1.slider("Số item", min_n, max_n, min(default_n, max_n), key=f"{key}_n")
    en = c2.checkbox("Xem nhanh tiếng Anh (không dịch)", value=False, key=f"{key}_en")
    use = rows[:n]
    ids = tuple(r["id"] for r in use)
    with st.spinner("Đang việt hoá & dựng Dark Analyst (lần đầu vài giây, sau tức thì)…"
                    if not en else "Đang dựng…"):
        html = _dark_dashboard_html(ids, topic, vi=not en)
    _dark_view(html, key, len(use), len(rows), height)


@st.cache_data(show_spinner=False)
def _scores_dark_html(names_tuple, topic, vi=True):
    """Dựng (cache) Dark Analyst cho các thang điểm theo tên (việt hoá đầy đủ mặc định)."""
    from app.reports.evidence_workbench import render_scores_for_names
    return render_scores_for_names(list(names_tuple), topic=topic, dark=True, vi=vi,
                                   cache_only=False)


def render_scores_dark(names, topic, key, default_n=15, height=880):
    """TỰ HIỆN các thang điểm dưới dạng Dark Analyst (khung 'Thang điểm'), đã việt hoá."""
    if not names:
        st.info("Chưa có công cụ.")
        return
    c1, c2 = st.columns([1.2, 2.6])
    min_n, max_n = (1 if len(names) < 5 else 5), min(40, len(names))
    n = c1.slider("Số công cụ", min_n, max_n, min(default_n, max_n), key=f"{key}_n")
    en = c2.checkbox("Xem nhanh tiếng Anh (không dịch)", value=False, key=f"{key}_en")
    use = tuple(names[:n])
    with st.spinner("Đang việt hoá & dựng…" if not en else "Đang dựng…"):
        html = _scores_dark_html(use, topic, vi=not en)
    _dark_view(html, key, len(use), len(names), height)


def render_clickable_evidence(rows, disp, key, column_config=None, height=360,
                              hint="⬆️ **Bấm vào một hàng** ở bảng trên để xem chi tiết "
                                   "theo mẫu Dark Analyst (nền tối, 3 cột)."):
    """Bảng chứng cứ bấm-được: click 1 hàng → hiện DARK ANALYST của item đó bên dưới.

    `rows`: list dict có khóa 'id' (theo _evidence_rows); `disp`: DataFrame hiển thị
    (cùng thứ tự với rows). Dùng chung cho các tab Drug Safety / Antibiotics / Guidelines.
    """
    st.caption("👉 **Bấm vào một hàng** → xem chi tiết theo mẫu **Dark Analyst** bên dưới.")
    event = st.dataframe(
        disp, hide_index=True, width="stretch", height=height,
        on_select="rerun", selection_mode="single-row", key=key,
        column_config=column_config or {})
    sel = event.selection.rows if (event and getattr(event, "selection", None)) else []
    st.divider()
    if sel:
        render_item_dark(rows[sel[0]]["id"], key_prefix=key)
    else:
        st.info(hint)


# --- Sidebar --------------------------------------------------------------
st.sidebar.title("🩺 Medical EBM Automation")
st.sidebar.caption("Hệ thống tự động hoá cập nhật chứng cứ y khoa & quản lý nghiên cứu")

with session_scope() as s:
    has_data = s.query(EvidenceItem).count() > 0

def _latest_report(pattern: str):
    files = sorted(Path(settings.reports_dir).glob(pattern),
                   key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


# ===== HÀNH ĐỘNG CHÍNH: Cập nhật ngay (nguồn thật + gửi email) =====
st.sidebar.markdown("### ▶️ Hành động")
if st.sidebar.button("🔄 Cập nhật ngay (nguồn THẬT + email)",
                     type="primary", use_container_width=True):
    from app.main import cmd_live_update
    _ok = False
    try:
        with st.spinner("Đang quét nguồn thật (PubMed/FDA/MHRA…) – có thể vài phút. "
                        "Sẽ tự gửi email nếu có mục mới…"):
            res = cmd_live_update()
        p = res.get("pipeline", {})
        notify = res.get("notify", {}) or {}
        st.sidebar.success(
            f"✅ Xong: {p.get('new_items', 0)} mục MỚI / {p.get('total', 0)} bản ghi. "
            f"Email: {notify.get('email', {}).get('status', '—')}")
        _ok = True
    except Exception as exc:  # noqa: BLE001 - hiển thị lỗi thân thiện thay vì traceback
        from app.utils.logging_config import get_logger
        get_logger(__name__).exception("Lỗi cập nhật trực tiếp từ dashboard")
        st.sidebar.error(
            f"❌ Cập nhật thất bại: {exc}\n\n"
            "Kiểm tra kết nối mạng và cấu hình email (.env) rồi thử lại.")
    if _ok:
        st.rerun()

c_a, c_b = st.sidebar.columns(2)
if c_a.button("🌱 Dữ liệu mẫu", use_container_width=True,
              help="Nạp dữ liệu minh hoạ (offline) để xem thử giao diện"):
    with st.spinner("Đang nạp dữ liệu mẫu..."):
        seed_all(run_pipeline_mock=True)
    st.rerun()
if c_b.button("🔁 Quét lại", use_container_width=True,
              help="Chạy lại pipeline với dữ liệu/nguồn hiện có"):
    with st.spinner("Đang chạy..."):
        run_pipeline()
    st.rerun()

# ===== BÁO CÁO: xem / tải ngay trong dashboard =====
st.sidebar.divider()
st.sidebar.subheader("📄 Báo cáo")
if st.sidebar.button("🔃 Tạo lại tất cả báo cáo", use_container_width=True):
    with st.spinner("Đang tạo báo cáo..."):
        export_weekly_ebm_markdown()
        export_weekly_ebm_html()
        export_alert_digest()
        export_drug_safety_report()
        export_antibiotic_report()
    st.sidebar.success("Đã tạo báo cáo mới.")

for _label, _pat in [("🔔 Bản tin cảnh báo (Mới)", "Alert_Digest_*.html"),
                     ("📅 EBM tuần", "EBM_Weekly_Update_*.html"),
                     ("💊 An toàn thuốc", "Drug_Safety_Weekly_*.html"),
                     ("🦠 Kháng sinh", "Antibiotic_Stewardship_Weekly_*.html")]:
    _f = _latest_report(_pat)
    if _f:
        st.sidebar.download_button(f"⬇️ {_label}", _f.read_bytes(), file_name=_f.name,
                                   mime="text/html", use_container_width=True,
                                   key=f"dl_{_pat}")

with st.sidebar.expander("📊 Xuất Excel / CSV / BibTeX"):
    if st.button("Xuất tất cả bảng dữ liệu", use_container_width=True):
        export_dashboard_excel()
        export_research_tracker_excel()
        export_source_log_csv()
        export_zotero_bibtex()
        st.success("Đã xuất vào data/exports")

if not has_data:
    st.warning("Chưa có dữ liệu. Bấm **Nạp dữ liệu mẫu (seed)** ở thanh bên trái để bắt đầu.")

# Banner LIÊM CHÍNH: cảnh báo chế độ DEMO hoặc dữ liệu mock lẫn vào dữ liệu thật.
with session_scope() as _s_mock:
    _mock_n = _s_mock.query(EvidenceItem).filter(EvidenceItem.is_mock.is_(True)).count()
if settings.use_mock_sources:
    st.warning("⚠️ **CHẾ ĐỘ DEMO (USE_MOCK_SOURCES=true)** — dữ liệu hiển thị là MINH HỌA, "
               "KHÔNG dùng cho quyết định lâm sàng. Đặt `USE_MOCK_SOURCES=false` trong `.env` "
               "để quét nguồn thật.")
elif _mock_n:
    st.warning(f"⚠️ DB có **{_mock_n} bản ghi DEMO** lẫn dữ liệu thật — đã LOẠI khỏi danh sách "
               "khuyến cáo (actionable) trong báo cáo tuần. Cân nhắc làm sạch nếu cần.")

tabs = st.tabs([
    "1. Executive", "2. Weekly EBM", "3. Drug Safety", "4. Antibiotics",
    "5. Guidelines", "6. Research", "7. Clinical Scores", "8. Source Log", "9. Change Log",
    "📱 10. TikTok", "📚 11. Tổng hợp RAG", "🧭 12. Evidence Workbench",
    "🛡️ 13. V7 Shadow Read-only", "🫀 14. Chronic Care Shadow Pilot",
])

# --- Tab 1: Executive -----------------------------------------------------
with tabs[0]:
    st.header("Tổng quan điều hành")

    # --- Bản tin "Mới tuần này" (cảnh báo) ---
    alert = build_alert_data(days=7)
    if alert["total_new"] > 0:
        st.success(f"🔔 **{alert['total_new']} tài liệu MỚI** trong 7 ngày qua "
                   f"({len(alert['regulatory'])} cảnh báo an toàn thuốc chính thức, "
                   f"{len(alert['guidelines'])} guideline, {len(alert['actionable'])} actionable).")
    else:
        st.info("🔕 Không có tài liệu mới trong 7 ngày qua (hệ thống không bịa tin).")
    cN = st.columns(2)
    if cN[0].button("📰 Xem bản tin cảnh báo (Mới)"):
        st.markdown(render_alert_markdown(alert))
    if cN[1].button("💾 Xuất bản tin cảnh báo"):
        res = export_alert_digest(days=7)
        st.success(f"Đã xuất: {res['markdown'].name}")
    st.divider()

    with session_scope() as s:
        rows = _evidence_rows(s)
        n_sources = s.query(SourceLog).count()
        n_scanned = s.query(SourceLog).with_entities(SourceLog.record_count).all()
        total_scanned = sum(x[0] or 0 for x in n_scanned)
        n_guideline = s.query(EvidenceItem).filter(
            EvidenceItem.study_type == "guideline").count()
    excluded = [r for r in rows if r["classification"] == "excluded"]
    need_ft = [r for r in rows if r["classification"] == "need_full_text"]
    actionable = [r for r in rows if r["actionable"]]
    drug = [r for r in rows if r["safety_signal"]]
    # 8 thẻ KPI có MÀU NGỮ NGHĨA (đồng bộ palette Evidence Workbench)
    _kpis = [
        ("🔎 Lượt quét", n_sources, "#0e7490"), ("🗂️ Bản ghi", total_scanned, "#2563eb"),
        ("📄 Record chính", len(rows), "#0891b2"), ("🚫 Bị loại", len(excluded), "#94a3b8"),
        ("📖 Cần toàn văn", len(need_ft), "#ca8a04"), ("✅ Actionable", len(actionable), "#16a34a"),
        ("⚠️ Cảnh báo thuốc", len(drug), "#dc2626"), ("📋 Guideline", n_guideline, "#059669"),
    ]
    st.markdown(
        '<div class="kpi-strip">'
        + "".join(f'<div class="kpi" style="--c:{c}">'
                  f'<div class="kl">{lbl}</div>'
                  f'<div class="kv c">{val:,}</div></div>' for lbl, val, c in _kpis)
        + '</div>', unsafe_allow_html=True)

    if rows:
        df = pd.DataFrame(rows)
        st.subheader("Phân bố theo chuyên khoa")
        # Biểu đồ ngang có nhãn số, màu thương hiệu (Altair) — đẹp & dễ đọc.
        import altair as alt
        by_area = (df.groupby("clinical_area").size().reset_index(name="n")
                   .rename(columns={"clinical_area": "area"}))
        by_area = by_area[by_area["area"].notna() & (by_area["area"] != "")]
        base = alt.Chart(by_area).encode(
            y=alt.Y("area:N", sort="-x", title=None,
                    axis=alt.Axis(labelFontSize=12, labelColor="#334155", labelLimit=180)),
            x=alt.X("n:Q", title=None, axis=alt.Axis(grid=True, gridColor="#eef2f7")))
        bars = base.mark_bar(height=16, cornerRadiusEnd=5,
                             color=alt.Gradient(
                                 gradient="linear",
                                 stops=[alt.GradientStop(color="#0e7490", offset=0),
                                        alt.GradientStop(color="#2563eb", offset=1)],
                                 x1=0, x2=1, y1=0, y2=0))
        labels = base.mark_text(align="left", dx=4, fontSize=11, fontWeight="bold",
                                color="#0f172a").encode(text="n:Q")
        chart = (bars + labels).properties(
            height=max(200, 30 * len(by_area)),
            padding={"left": 4, "right": 24, "top": 2, "bottom": 2}
        ).configure_view(strokeWidth=0)
        st.altair_chart(chart, use_container_width=True)

# --- Tab 2: Weekly EBM ----------------------------------------------------
with tabs[1]:
    st.header("Cập nhật EBM tuần")
    with session_scope() as s:
        rows = _evidence_rows(s)
    if rows:
        col1, col2, col3 = st.columns([2, 2, 1])
        areas = ["(Tất cả)"] + sorted({r["clinical_area"] for r in rows if r["clinical_area"]})
        pick = col1.selectbox("Lọc theo chuyên khoa", areas)
        kw = col2.text_input("🔎 Tìm trong tiêu đề/nguồn",
                             placeholder="vd: atrial fibrillation, statin…")
        only_new = col3.checkbox("🆕 Mới (7 ngày)", value=False)
        kw_l = kw.strip().lower()
        filtered = [r for r in rows
                    if (pick == "(Tất cả)" or r["clinical_area"] == pick)
                    and (not only_new or r["is_new"])
                    and (not kw_l
                         or kw_l in (str(r["title"]) + " " + str(r["source"] or "")).lower())]
        st.caption(f"📊 {len(filtered)} tài liệu khớp lọc → hiển thị dạng **Dark Analyst** "
                   "(bấm item trong bảng tối để mở panel thẩm định). Lọc/tìm ở trên để thu hẹp.")
        _topic = "EBM tuần" if pick == "(Tất cả)" else f"EBM tuần — {pick}"
        render_dark_tab(filtered, topic=_topic, key="dark_weekly", default_n=15)
    else:
        st.info("Chưa có dữ liệu EBM.")

# --- Tab 3: Drug Safety ---------------------------------------------------
with tabs[2]:
    st.header("Cảnh báo an toàn thuốc")
    st.caption("⚠️ FAERS chỉ là tín hiệu báo cáo tự phát — KHÔNG kết luận nhân quả.")
    with session_scope() as s:
        rows = [r for r in _evidence_rows(s) if r["safety_signal"]]
    render_dark_tab(rows, topic="An toàn thuốc", key="dark_drug")

# --- Tab 4: Antibiotics ---------------------------------------------------
with tabs[3]:
    st.header("Kháng sinh / Antibiotic Stewardship")
    with session_scope() as s:
        rows = _evidence_rows(s)
    from app.services.filtering import is_antibiotic_text
    ab = [r for r in rows if r["title"] and is_antibiotic_text(r["title"], r.get("source", ""))]
    st.caption("Không cổ vũ lạm dụng kháng sinh; cân nhắc phân loại WHO AWaRe.")
    render_dark_tab(ab, topic="Kháng sinh / Antibiotic Stewardship", key="dark_ab")

# --- Tab 5: Guidelines ----------------------------------------------------
with tabs[4]:
    st.header("Guideline mới / cập nhật")
    with session_scope() as s:
        rows = [r for r in _evidence_rows(s, study_type="guideline")]
    render_dark_tab(rows, topic="Guideline mới / cập nhật", key="dark_guide")

# --- Tab 6: Research ------------------------------------------------------
with tabs[5]:
    st.header("Dự án nghiên cứu y khoa")
    with session_scope() as s:
        projs = [{
            "project_id": p.project_id, "title": p.project_title,
            "department": p.department, "PI": p.principal_investigator,
            "design": p.study_design, "ethics": p.ethics_status,
            "protocol": p.protocol_status, "data": p.data_collection_status,
            "analysis": p.analysis_status, "manuscript": p.manuscript_status,
            "next_actions": p.next_actions, "risks": p.risks,
            "deadline": p.deadline,
            "missing": ", ".join(p.missing_documents or []),
        } for p in s.query(ResearchProject).all()]
    if projs:
        st.dataframe(pd.DataFrame(projs), use_container_width=True, hide_index=True)
        st.subheader("Hồ sơ nghiên cứu (đề cương + tài liệu nền + checklist)")
        ids = [p["project_id"] for p in projs]
        pick = st.selectbox("Chọn đề tài", ids, key="dossier_pick")
        if st.button("📑 Tạo hồ sơ nghiên cứu"):
            from app.research import export_research_dossier
            with st.spinner("Đang tìm tài liệu nền & dựng hồ sơ..."):
                path = export_research_dossier(pick)
            if path:
                st.success(f"Đã xuất: {path.name}")
                st.markdown(path.read_text(encoding="utf-8"))
            else:
                st.error("Không tạo được hồ sơ.")
    else:
        st.info("Chưa có đề tài. Seed dữ liệu mẫu để xem ví dụ.")

# --- Tab 7: Clinical Scores -----------------------------------------------
with tabs[6]:
    st.header("Thang điểm / công cụ lâm sàng")
    with session_scope() as s:
        all_scores = s.query(ClinicalScore).order_by(ClinicalScore.clinical_area).all()
        scores = [{
            "score_name": c.score_name, "clinical_area": c.clinical_area,
            "situation": c.clinical_situation,
            "thresholds": c.action_thresholds or "(chưa nhập)",
            "source": c.source or "—", "status": c.update_status,
        } for c in all_scores]
        verified = [c for c in all_scores if c.update_status == "verified"]
    cA, cB = st.columns(2)
    cA.metric("Tổng công cụ", len(scores))
    cB.metric("Đã xác minh công thức + nguồn", len(verified))
    st.caption("Công cụ `needs_verification` CHƯA có công thức xác minh — không dùng làm khuyến cáo.")
    if scores:
        # --- TỰ HIỆN Dark Analyst cho thang điểm (khung Thang điểm: tình huống/cách tính/ngưỡng/diễn giải) ---
        st.markdown("#### 🌑 Dark Analyst — thang điểm lâm sàng")
        _sc_all = st.checkbox("Gồm cả công cụ chưa xác minh", value=False, key="sc_dark_all")
        _names = [s["score_name"] for s in scores
                  if _sc_all or s["status"] == "verified"]
        render_scores_dark(_names, topic="Thang điểm / công cụ lâm sàng", key="dark_scores")
        st.divider()
        st.markdown("#### 📑 Danh mục dạng bảng")
        only_verified = st.checkbox("Chỉ hiện công cụ đã xác minh", value=False)
        df = pd.DataFrame(scores)
        if only_verified:
            df = df[df["status"] == "verified"]
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.subheader("Chi tiết công cụ đã xác minh")
        names = [c.score_name for c in verified]
        if names:
            pick = st.selectbox("Chọn công cụ", names)
            c = next(x for x in verified if x.score_name == pick)
            st.markdown(f"**{c.score_name}** — *{c.clinical_area}*")
            st.markdown(f"- **Mục đích:** {c.purpose}")
            st.markdown(f"- **Thành phần:** {', '.join(c.components or [])}")
            st.markdown(f"- **Cách tính:** {c.calculation_method}")
            st.markdown(f"- **Diễn giải:** {c.interpretation}")
            st.markdown(f"- **Ngưỡng & hành động:** {c.action_thresholds}")
            st.markdown(f"- **Hạn chế:** {c.limitations}")
            st.markdown(f"- **Nguồn:** {c.source}")
            st.markdown(f"- **Guideline tham chiếu:** {c.guideline_reference or '—'}")
    else:
        st.info("Chưa nạp danh mục thang điểm.")

    # ===== 45 THANG ĐIỂM LÂM SÀNG (tài liệu HTML đầy đủ, trích nguyên văn) =====
    st.divider()
    st.subheader("📚 45 thang điểm lâm sàng thiết yếu 2026 (tài liệu đầy đủ)")
    import streamlit.components.v1 as _components

    from app.clinical_scores import reference_import as _refimp

    ref = _refimp.load_reference()

    # --- Mục CẬP NHẬT: nhập/nhập lại từ file HTML ---
    with st.expander("🔄 Cập nhật / nhập danh mục thang điểm (từ file HTML)",
                     expanded=(ref is None)):
        st.caption("Khi guideline thay đổi: chỉnh file HTML thang điểm rồi nhập lại tại đây. "
                   "Hệ thống chỉ **trích nguyên văn** từ file của bạn (không bịa).")
        default_path = (ref or {}).get("meta", {}).get("source_path") \
            or str(Path.home() / "Downloads" / "Thang_diem_45_tich_hop_123.html")
        ref_path = st.text_input("Đường dẫn file HTML", value=default_path, key="ref45_path")
        if st.button("📥 Nhập / cập nhật ngay", key="ref45_import"):
            try:
                with st.spinner("Đang tách thang điểm từ file HTML..."):
                    meta = _refimp.import_from_html(ref_path)
                st.success(f"✅ Đã nhập {meta['count']} thang điểm "
                           f"(lúc {meta['imported_at']}).")
                st.rerun()
            except Exception as e:  # noqa: BLE001
                st.error(f"Không nhập được: {e}")

    if not ref:
        st.info("Chưa nhập tài liệu 45 thang điểm. Mở mục **🔄 Cập nhật** ở trên để nhập từ file HTML.")
    else:
        meta = ref["meta"]
        items = ref["items"]
        m1, m2, m3 = st.columns(3)
        m1.metric("Số thang điểm", meta["count"])
        m2.metric("Số nhóm chuyên khoa", len({i["group"] for i in items}))
        m3.metric("Cập nhật lần cuối", meta["imported_at"])
        st.caption(f"Nguồn: **{meta['source']}** — trích nguyên văn, hiển thị kèm định dạng gốc.")

        groups = ["(Tất cả)"] + sorted({i["group"] for i in items if i["group"]})
        gsel = st.selectbox("Lọc theo nhóm chuyên khoa", groups, key="ref45_group")
        q = st.text_input("🔎 Tìm theo tên thang điểm", key="ref45_q").strip().lower()
        visible = [i for i in items
                   if (gsel == "(Tất cả)" or i["group"] == gsel)
                   and (not q or q in (i["name"] or "").lower())]

        st.caption(f"👉 **Bấm vào một hàng** để xem chi tiết đầy đủ (bảng chấm điểm, diễn giải, "
                   f"hành động, cảnh báo, nguồn). ({len(visible)} thang điểm)")
        disp = pd.DataFrame([{
            "STT": i["stt"], "Nhóm": i["group"], "Thang điểm": i["name"],
            "Mức CC": i["evidence"], "Tình huống dùng": i["situation"],
        } for i in visible])
        ev = st.dataframe(
            disp, hide_index=True, width="stretch", height=380,
            on_select="rerun", selection_mode="single-row", key="tbl_ref45",
            column_config={
                "STT": st.column_config.NumberColumn("STT", width="small"),
                "Thang điểm": st.column_config.TextColumn("Thang điểm", width="medium"),
                "Tình huống dùng": st.column_config.TextColumn("Tình huống dùng", width="large"),
            })
        rsel = ev.selection.rows if (ev and getattr(ev, "selection", None)) else []
        if rsel:
            it = visible[rsel[0]]
            st.markdown(f"#### 📋 {it['stt']}. {it['name']} — *{it['group']}* · "
                        f"Mức chứng cứ: **{it['evidence']}**")
            doc = (f"<style>{ref['css']}</style>"
                   f"<div class='wrap' style='padding:6px 10px'>"
                   f"<article class='card'>{it['html']}</article></div>")
            _components.html(doc, height=720, scrolling=True)
        else:
            st.info("⬆️ Bấm một hàng để xem chi tiết thang điểm (giữ nguyên định dạng tài liệu gốc).")

# --- Tab 8: Source Log ----------------------------------------------------
with tabs[7]:
    st.header("Nhật ký nguồn (Source Log)")
    with session_scope() as s:
        logs = [{
            "run_at": str(sl.run_at), "source": sl.source, "query": sl.query,
            "records": sl.record_count, "status": sl.status, "mode": sl.mode,
            "error": sl.error_message,
        } for sl in s.query(SourceLog).order_by(SourceLog.run_at.desc()).limit(300).all()]
    if logs:
        st.dataframe(pd.DataFrame(logs), use_container_width=True, hide_index=True)
    else:
        st.info("Chưa có log nguồn.")

# --- Tab 9: Change Log ----------------------------------------------------
with tabs[8]:
    st.header("Change Log")
    with session_scope() as s:
        changes = [{
            "date": str(c.change_date), "summary": c.change_summary,
            "source": c.source, "module": c.module, "by": c.created_by,
            "review": c.review_status,
        } for c in s.query(ChangeLogEntry).order_by(
            ChangeLogEntry.change_date.desc()).limit(300).all()]
    if changes:
        st.dataframe(pd.DataFrame(changes), use_container_width=True, hide_index=True)
    else:
        st.info("Chưa có thay đổi nào được ghi nhận.")

# --- Tab 10: TikTok -------------------------------------------------------
with tabs[9]:
    import json as _json

    from app.social import package as _tt

    st.header("📱 Nội dung TikTok (cập nhật chứng cứ)")
    st.caption("Biến chứng cứ trong kho thành gói slideshow + caption để **bác sĩ DUYỆT "
               "rồi tự đăng**. Không bịa số liệu; mọi điểm chính trích nguyên văn + nguồn.")

    from app.social import video as _ttv
    _vid_ok = _ttv.available()
    _style_label = st.radio(
        "Phong cách", ["Lâm sàng (nền tối)", "Bảng trắng viết tay (giọng mềm)"],
        horizontal=True,
        help="Bảng trắng: nền giấy, chữ viết tay (Brush Script/Chalkboard), nét vẽ tay, "
             "chuyển động mềm + giọng nữ HoaiMy (cần mạng cho giọng neural).")
    _style = "whiteboard" if _style_label.startswith("Bảng") else "clinical"
    col1, col2, col3, col4 = st.columns([2, 2, 2, 3])
    n_posts = col1.slider("Số bài mỗi lô", 1, 10, 3)
    inc_watch = col2.checkbox("Gồm 'tin nhanh' (chứng cứ yếu)", value=False,
                              help="Mặc định chỉ lấy guideline/SR/RCT/cảnh báo (đủ mạnh). "
                                   "Bật ô này để thêm tài liệu mức theo dõi — KHÔNG khuyến cáo.")
    mk_video = col3.checkbox("🎬 Tạo cả video (giọng đọc)",
                             value=(_style == "whiteboard"), disabled=not _vid_ok,
                             help=("Dựng video dọc + giọng đọc tiếng Việt. Chậm hơn ảnh."
                                   if _vid_ok else
                                   "Cần giọng đọc (edge-tts hoặc macOS 'say') + ffmpeg."))
    draw_on = st.checkbox("✍️ Hiệu ứng vẽ tay (draw-on) — chữ hiện dần + cây bút (chậm hơn)",
                          value=False,
                          disabled=not (_vid_ok and mk_video and _style == "whiteboard"),
                          help="Kiểu whiteboard thật. Chỉ áp dụng cho phong cách Bảng trắng + có video.")
    if col4.button("✨ Tạo gói nội dung TikTok", type="primary", use_container_width=True):
        _msg = "Đang dựng slideshow + caption" + (
            " + video vẽ tay…" if (mk_video and draw_on) else
            (" + video (giọng đọc)…" if mk_video else "…"))
        with st.spinner(_msg):
            res = _tt.generate_tiktok_batch(limit=n_posts, include_watch=inc_watch,
                                            make_video=mk_video, style=_style,
                                            draw_on=draw_on)
        if res["count"]:
            st.success(f"✅ Đã tạo {res['count']} bài (bỏ qua {res['skipped']} mục chưa đủ điều kiện).")
        else:
            st.warning(f"Chưa tạo được bài nào (bỏ qua {res['skipped']}). "
                       "Thử bật 'tin nhanh' hoặc cập nhật dữ liệu trước.")
        if not res["render_available"]:
            st.info("⚠️ Chưa vẽ được ảnh (thiếu Pillow). Cài: ~/.ebm-venv/bin/pip install Pillow")
        st.rerun()

    # ===== TỰ SOẠN NỘI DUNG -> TẠO VIDEO =====
    with st.expander("✍️ Tự soạn nội dung → XEM TRƯỚC rồi tạo video", expanded=False):
        st.caption("Bước 1: nhập nội dung → **Xem trước** (ảnh + lời đọc). "
                   "Bước 2: **sửa lời đọc** cho suôn/ngắt nghỉ đúng ý → **Tạo video**. "
                   "Quy ước: một dòng trống = sang slide mới; dòng đầu mỗi đoạn là tiêu đề "
                   "slide, các dòng sau là ý.")
        from app.config import CLINICAL_AREAS as _AREAS
        _area_opts = ["Kiến thức y khoa"] + list(_AREAS.keys())
        mc1, mc2 = st.columns([3, 2])
        m_title = mc1.text_input("Tiêu đề bài", key="m_title",
                                 placeholder="VD: 3 điều cần biết về huyết áp tại nhà")
        m_area = mc2.selectbox("Chuyên khoa (chọn doodle)", _area_opts, key="m_area")
        m_content = st.text_area("Nội dung", key="m_content", height=220,
                                 placeholder="Vì sao đo huyết áp tại nhà?\n"
                                 "Phản ánh đúng huyết áp thường ngày\n"
                                 "Tránh tăng huyết áp áo choàng trắng\n\n"
                                 "Đo thế nào cho đúng?\n"
                                 "Ngồi nghỉ 5 phút trước khi đo\n"
                                 "Đo 2 lần, cách nhau 1-2 phút")
        mcc1, mcc2 = st.columns([3, 2])
        m_source = mcc1.text_input("Nguồn (tuỳ chọn)", key="m_source",
                                   placeholder="VD: Khuyến cáo ESC 2024")
        m_stylelabel = mcc2.selectbox("Phong cách", ["Bảng trắng viết tay", "Lâm sàng (nền tối)"],
                                      key="m_style")
        m_style = "whiteboard" if m_stylelabel.startswith("Bảng") else "clinical"

        if st.button("👁️ Xem trước (ảnh + lời đọc)", key="m_prev_btn",
                     disabled=not (m_title.strip() and m_content.strip())):
            with st.spinner("Đang dựng slide xem trước…"):
                pv = _tt.preview_manual(m_title, m_content, area=m_area,
                                        source=m_source, style=m_style)
            if not pv.get("ok"):
                st.warning(pv.get("error", "Lỗi xem trước."))
            else:
                st.session_state["m_prev"] = pv
                for _i, _n in enumerate(pv["narrations"]):
                    st.session_state[f"m_narr_{_i}"] = _n
            st.rerun()

        pv = st.session_state.get("m_prev")
        if pv and pv.get("ok"):
            st.divider()
            st.markdown("**👀 Xem trước slide** — muốn đổi slide thì sửa nội dung trên rồi "
                        "bấm *Xem trước* lại.")
            if pv["slides"]:
                st.image(list(pv["slides"]), width=150)
            st.markdown("**🗣️ Lời đọc từng slide** — sửa cho suôn/ngắt nghỉ đúng ý bác "
                        "(mỗi dấu chấm = một nhịp nghỉ):")
            _n = len(pv["narrations"])
            _labels = ["Slide 1 (bìa)"] + [f"Slide {k+1}" for k in range(1, _n - 1)] + \
                      (["Slide cuối (nguồn & lưu ý)"] if _n > 1 else [])
            for _i in range(_n):
                _lab = _labels[_i] if _i < len(_labels) else f"Slide {_i+1}"
                st.text_area(_lab, key=f"m_narr_{_i}", height=80)
            if not _vid_ok:
                st.info("⚠️ Chưa có giọng đọc/ffmpeg để dựng video.")
            cpv1, cpv2, cpv3 = st.columns([2, 2, 2])
            m_draw = cpv1.checkbox("✍️ Hiệu ứng vẽ tay", value=False, key="m_draw",
                                   disabled=not (_vid_ok and pv["style"] == "whiteboard"))
            if cpv2.button("🎥 Tạo video", type="primary", key="m_create", disabled=not _vid_ok):
                _narr = [st.session_state.get(f"m_narr_{_i}", "") for _i in range(_n)]
                with st.spinner("Đang dựng video theo lời đọc đã sửa…"):
                    cr = _tt.create_manual_video(pv["folder"], pv["post"], pv["slides"],
                                                 _narr, style=pv["style"], draw_on=m_draw)
                if cr.get("ok"):
                    st.success("✅ Đã tạo video.")
                    _vf = Path(cr["folder"]) / cr["video"]
                    if _vf.exists():
                        st.video(str(_vf))
                        st.download_button("⬇️ Tải video.mp4", _vf.read_bytes(),
                                           file_name=f"{pv['slug']}.mp4", mime="video/mp4",
                                           key="m_dlv2")
                    st.caption(f"📂 {cr['folder']}")
                else:
                    st.warning(cr.get("error", "Không tạo được video."))
            if cpv3.button("🗑️ Xoá xem trước", key="m_clearprev"):
                st.session_state.pop("m_prev", None)
                st.rerun()

    # Hàng đợi chủ đề tự nhập.
    with st.expander("✍️ Hàng đợi chủ đề tự chọn (mỗi dòng: id bản ghi hoặc từ khoá tiêu đề)"):
        _q = _tt.QUEUE_PATH.read_text(encoding="utf-8") if _tt.QUEUE_PATH.exists() else \
            "# Ví dụ: gõ id (49) hoặc một phần tiêu đề (atrial fibrillation)\n"
        _newq = st.text_area("queue.txt", value=_q, height=120, label_visibility="collapsed")
        if st.button("💾 Lưu hàng đợi"):
            _tt.TIKTOK_DIR.mkdir(parents=True, exist_ok=True)
            _tt.QUEUE_PATH.write_text(_newq, encoding="utf-8")
            st.success("Đã lưu. Lần tạo lô sau sẽ ưu tiên các chủ đề này.")

    st.divider()

    # Xem trước các lô đã tạo (mới nhất trước).
    batches = sorted([d for d in _tt.TIKTOK_DIR.glob("20*") if d.is_dir()], reverse=True) \
        if _tt.TIKTOK_DIR.exists() else []
    if not batches:
        st.info("Chưa có lô nào. Bấm **Tạo gói nội dung TikTok** ở trên để bắt đầu.")
    else:
        names = [b.name for b in batches]
        sel = st.selectbox("Chọn lô để xem", names, index=0)
        bdir = _tt.TIKTOK_DIR / sel
        mf_path = bdir / "manifest.json"
        manifest = _json.loads(mf_path.read_text(encoding="utf-8")) if mf_path.exists() else {}
        items = manifest.get("items", [])
        st.caption(f"{len(items)} bài · {bdir}")
        for it in items:
            kind_icon = "✅" if it["kind"] == "recommendation" else "🟡"
            with st.expander(f"{kind_icon} {it['title_vi'] or it['title_en']}  "
                             f"· {it['area']} · Tier {it.get('tier') or '?'}", expanded=False):
                folder = bdir / it["slug"]
                cc1, cc2 = st.columns([1, 2])
                slide_files = sorted(folder.glob("slide_*.png"))
                if slide_files:
                    cc1.image(str(slide_files[0]), use_container_width=True)
                with cc2:
                    cap_f = folder / "caption.txt"
                    if cap_f.exists():
                        st.text_area("Caption (bấm góc phải để sao chép)",
                                     cap_f.read_text(encoding="utf-8"), height=220,
                                     key=f"cap_{it['slug']}")
                if slide_files:
                    st.write("**Tải ảnh slideshow** (đăng theo thứ tự):")
                    dl_cols = st.columns(min(len(slide_files), 5))
                    for i, sf in enumerate(slide_files):
                        dl_cols[i % len(dl_cols)].download_button(
                            f"⬇️ {sf.name}", sf.read_bytes(), file_name=sf.name,
                            mime="image/png", key=f"dl_{it['slug']}_{i}")
                vf = folder / (it.get("video") or "")
                if it.get("video") and vf.exists():
                    st.write("**🎬 Video (giọng đọc tiếng Việt):**")
                    st.video(str(vf))
                    st.download_button("⬇️ Tải video.mp4", vf.read_bytes(),
                                       file_name=f"{it['slug']}.mp4", mime="video/mp4",
                                       key=f"dlv_{it['slug']}")
                st.caption(f"📂 Thư mục: {folder}")


# --- Tab 11: Tổng hợp chứng cứ (RAG, có trích dẫn) ------------------------
with tabs[10]:
    st.header("📚 Tổng hợp chứng cứ (RAG — có trích dẫn)")
    st.caption("Mỗi thang điểm neo vào nguồn gốc + guideline (không bịa). 🆕 = cập nhật 2024–2026. "
               "Công cụ HỖ TRỢ, không thay phán đoán lâm sàng.")
    _brief = ROOT / "evidence" / "reviews" / "tong-hop-chung-cu-thang-diem-2026.md"
    if not _brief.exists():
        st.info("Chưa có bản tổng hợp. Chạy: `python scripts/gen_evidence_brief.py`")
    else:
        from scripts.gen_evidence_brief import freshness_label as _rag_freshness
        st.caption(f"🕒 Cập nhật lần cuối: {_rag_freshness(_brief)} "
                   "(tự sinh lại hằng tuần bằng scheduler, hoặc chạy tay "
                   "`python scripts/gen_evidence_brief.py`).")
        _md = _brief.read_text(encoding="utf-8")
        _q = st.text_input("🔎 Tìm thang điểm / chuyên khoa / từ khóa",
                           placeholder="vd: CHA2DS2, FIB-4, kháng đông, sepsis…", key="rag_q")
        _parts = _md.split("\n### ")
        if _q.strip():
            _ql = _q.strip().lower()
            _blocks = ["### " + b for b in _parts[1:] if _ql in b.lower()]
            st.caption(f"{len(_blocks)} thang điểm khớp “{_q}”.")
            st.markdown(_parts[0] + "\n" + "\n".join(_blocks) if _blocks
                        else "Không có thang điểm nào khớp.")
        else:
            st.markdown(_md)
        st.download_button("⬇️ Tải bản .md", _md, file_name=_brief.name,
                           mime="text/markdown", key="dl_rag_md")

# --- Tab 12: Evidence Workbench (theo skill cap-nhat-chung-cu-y-khoa) -------
with tabs[11]:
    st.header("🧭 Evidence Workbench — Dashboard cập nhật theo vấn đề")
    st.caption("Tạo **Web Dashboard độc lập** theo mẫu MẶC ĐỊNH *Evidence Workbench* "
               "(3 cột: bộ lọc · Clinical Quick View + bảng item · panel thẩm định) cho MỘT "
               "chuyên khoa/vấn đề — đúng cấu trúc skill `cap-nhat-chung-cu-y-khoa`. "
               "Chỉ gồm chứng cứ ĐÃ XÁC MINH (PMID/DOI), trích nguyên văn, kèm disclaimer.")
    from app.reports.evidence_workbench import OUT_DIR as _EW_OUT
    with session_scope() as s:
        _areas = sorted({a[0] for a in s.query(EvidenceItem.clinical_area)
                         .filter(EvidenceItem.is_primary_record.is_(True))
                         .filter((EvidenceItem.pmid.isnot(None)) | (EvidenceItem.doi.isnot(None)))
                         .distinct().all() if a[0]})
    import streamlit.components.v1 as _ew_components

    def _open_in_browser(path):
        """Mở file HTML bằng trình duyệt mặc định trên máy (server = máy bác sĩ)."""
        try:
            import subprocess as _sp
            import sys as _sys
            if _sys.platform == "darwin":
                _sp.Popen(["open", str(path)])
            elif _sys.platform.startswith("win"):
                import os as _os
                _os.startfile(str(path))  # type: ignore[attr-defined]
            else:
                _sp.Popen(["xdg-open", str(path)])
            return True
        except Exception:
            return False

    def _embed(path, height=820):
        """Nhúng dashboard NGAY trong app + nút mở trình duyệt + tải."""
        html_txt = Path(path).read_text(encoding="utf-8")
        b1, b2 = st.columns(2)
        if b1.button("🌐 Mở trong trình duyệt (toàn màn hình)", key=f"openb_{path.name}"):
            st.success("Đã mở trong trình duyệt." if _open_in_browser(path)
                       else "Không mở được — dùng đường dẫn bên dưới.")
        b2.download_button("⬇️ Tải .html", html_txt, file_name=path.name,
                           mime="text/html", key=f"dl_{path.name}")
        _ew_components.html(html_txt, height=height, scrolling=True)

    if not _areas:
        st.info("Chưa có chứng cứ truy nguyên (PMID/DOI). Bấm **Cập nhật ngay** để quét nguồn thật.")
    else:
        cc1, cc2, cc3 = st.columns([2, 1, 1])
        _area = cc1.selectbox("Chuyên khoa / vấn đề", _areas, key="ew_area")
        _limit = cc2.slider("Số item tối đa", 5, 30, 15, key="ew_limit")
        _online = cc3.checkbox("Xác minh PMID online", value=True, key="ew_online",
                               help="Kiểm tra mỗi PMID phân giải đúng trên PubMed (chống trích dẫn ảo)")
        st.caption("ℹ️ Nội dung được **dịch máy sang tiếng Việt (tham khảo)**; references giữ nguyên văn + "
                   "PMID/DOI để truy nguyên. Luôn đối chiếu nguồn gốc.")
        if st.button("🛠️ Tạo Word + Dashboard + việt hoá + cổng liêm chính", type="primary", key="ew_go"):
            from app.reports.evidence_workbench import export_and_publish
            with st.spinner("Đang xuất, dịch tiếng Việt, xác minh PMID & chạy cổng liêm chính…"):
                res = export_and_publish(area=_area, limit=_limit, online=_online)
            if not res.get("path"):
                st.error(res.get("gate_log") or "Không tạo được dashboard.")
            else:
                p = res["path"]
                st.session_state["ew_last"] = str(p)
                if res.get("docx"):
                    st.session_state["ew_last_docx"] = str(res["docx"])
                (st.success if res["gate_pass"] else st.warning)(
                    f"{'✅ Cổng liêm chính PASS' if res['gate_pass'] else '⚠️ Cổng FAIL — xem log'} · "
                    f"{p.name}")
                with st.expander("📋 Nhật ký cổng liêm chính"):
                    st.code(res.get("gate_log") or "", language="text")
        # Hiển thị (nhúng) dashboard vừa/đang chọn NGAY trong app
        _last = st.session_state.get("ew_last")
        if _last and Path(_last).exists():
            st.markdown(f"#### 👁️ Xem trực tiếp: `{Path(_last).name}`")
            _docx = st.session_state.get("ew_last_docx")
            if _docx and Path(_docx).exists():
                _dp = Path(_docx)
                st.download_button("⬇️ Tải file Word (.docx)", _dp.read_bytes(),
                                   file_name=_dp.name,
                                   mime=("application/vnd.openxmlformats-officedocument."
                                         "wordprocessingml.document"),
                                   key=f"dl_docx_{_dp.name}")
            _embed(Path(_last))

        # Danh sách dashboard EW đã tạo — chọn để mở ngay
        st.divider()
        st.subheader("📂 Các Evidence Workbench đã tạo")
        _files = sorted(_EW_OUT.glob("WebDashboard_EBM_*.html"),
                        key=lambda x: x.stat().st_mtime, reverse=True)[:30]
        if _files:
            _pick = st.selectbox("Chọn dashboard để mở ngay tại app", [f.name for f in _files],
                                 key="ew_pick")
            if st.button("👁️ Mở dashboard đã chọn", key="ew_open_existing"):
                st.session_state["ew_last"] = str(_EW_OUT / _pick)
                st.rerun()
            st.caption(f"Thư mục: {_EW_OUT} (đồng bộ OneDrive Mac↔Windows).")
        else:
            st.caption("Chưa có dashboard nào.")

with tabs[12]:
    from app.dashboard.v7_readonly import render_v7_readonly_dashboard

    render_v7_readonly_dashboard(st)

with tabs[13]:
    from app.chronic_care.dashboard import render_chronic_care_shadow_dashboard

    render_chronic_care_shadow_dashboard(st)
