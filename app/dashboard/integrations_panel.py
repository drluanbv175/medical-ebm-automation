"""Dashboard ĐỘC LẬP cho 5 mảng tích hợp CAFÉ-S — bác sĩ bấm-chạy thay vì gõ CLI.

Tách RIÊNG khỏi `app/dashboard/main.py` (tránh đụng file đang phát triển song song). Mở bằng:

    streamlit run app/dashboard/integrations_panel.py

5 tab: Tương tác thuốc · Ambient SOAP · Đọc ảnh · FHIR R4 · Trích dẫn thang điểm.
Bất biến: KHÔNG lưu PII (xử lý trong bộ nhớ phiên); đầu ra là NHÁP "Cần bác sĩ kiểm chứng";
ambient/đọc ảnh có cổng đồng thuận; chỉ ĐỀ XUẤT.

Lưu ý: phần logic thuần (parse_drug_list, warning_style) tách ra để test offline; phần UI (st.*)
chỉ chạy khi `streamlit run` (guard `__main__`) nên import file này trong pytest KHÔNG kích hoạt UI.
"""
from __future__ import annotations

import html
import os
from typing import List, Tuple


# ---------------------------------------------------------------------------
# Logic thuần (test được, không phụ thuộc Streamlit)
# ---------------------------------------------------------------------------
def parse_drug_list(text: str) -> List[str]:
    """Tách danh sách thuốc từ text (phân cách bởi xuống dòng/dấu phẩy/chấm phẩy), giữ thứ tự, bỏ trùng."""
    import re
    raw = re.split(r"[\n,;]+", text or "")
    out: List[str] = []
    for d in (x.strip() for x in raw):
        if d and d.lower() not in (o.lower() for o in out):
            out.append(d)
    return out


def warning_style(wtype: str) -> Tuple[str, str]:
    """Trả (nhãn hiển thị, biến màu nền) cho một loại cảnh báo thuốc."""
    return {
        "boxed_warning": ("Cảnh báo đóng khung", "#FCEBEB"),
        "contraindication": ("Chống chỉ định", "#FCEBEB"),
        "interaction": ("Tương tác — cần rà", "#FAEEDA"),
        "not_found": ("Không tìm thấy nhãn", "#F1EFE8"),
        "lookup_failed": ("Lỗi tra cứu", "#F1EFE8"),
    }.get(wtype, (wtype, "#F1EFE8"))


def has_anthropic_key() -> bool:
    return bool(os.getenv("ANTHROPIC_API_KEY", "").strip())


# ---------------------------------------------------------------------------
# Giao diện (chỉ chạy khi streamlit run — guard __main__)
# ---------------------------------------------------------------------------
DISCLAIMER = "⚠️ Đầu ra là BẢN NHÁP hỗ trợ — **Cần bác sĩ kiểm chứng**. KHÔNG lưu PII."


def _tab_drug(st) -> None:
    st.subheader("Sàng lọc tương tác / chống chỉ định thuốc")
    st.caption("Nguồn nhãn openFDA (miễn phí). Sàng lọc theo đề-cập — KHÔNG phân hạng nặng; "
               "không-cờ ≠ an toàn. Bổ trợ agent ke-don-an-toan.")
    txt = st.text_area("Danh sách thuốc (mỗi dòng/ngăn bởi dấu phẩy):",
                       placeholder="warfarin\naspirin", height=90)
    if st.button("Sàng lọc", key="drug_run"):
        drugs = parse_drug_list(txt)
        if len(drugs) < 1:
            st.warning("Nhập ít nhất 1 thuốc.")
            return
        from app.integrations.drug_interactions import DrugSafetyChecker
        with st.spinner(f"Tra nhãn openFDA cho {len(drugs)} thuốc…"):
            try:
                warns = DrugSafetyChecker().screen_regimen(drugs)
            except Exception as exc:  # noqa: BLE001
                st.error(f"Lỗi tra cứu: {exc}")
                return
        flags = [w for w in warns if w["type"] in ("interaction", "contraindication", "boxed_warning")]
        if not flags:
            st.success(f"Không có cờ từ nhãn openFDA cho: {', '.join(drugs)} "
                       "(KHÔNG kết luận an toàn — cần bác sĩ kiểm chứng).")
        for w in warns:
            label, color = warning_style(w["type"])
            # 2026-07-11: escape tên thuốc bác sĩ tự gõ + nhãn openFDA trước khi vào
            # unsafe_allow_html — chặn XSS nếu input chứa thẻ HTML/script.
            drugs_safe = html.escape(" + ".join(w["drugs"]))
            detail_safe = html.escape(str(w["detail"]))
            source_safe = html.escape(str(w["source"]))
            st.markdown(
                f"<div style='background:{color};padding:8px 12px;border-radius:8px;margin:4px 0'>"
                f"<b>[{label}]</b> {drugs_safe}<br>{detail_safe}<br>"
                f"<small>nguồn: {source_safe}</small></div>", unsafe_allow_html=True)
        st.caption(DISCLAIMER)


def _tab_soap(st) -> None:
    st.subheader("Ambient → bản nháp SOAP")
    st.caption("Hội thoại buổi khám → khử PII → khung SOAP (skill giao-tiep-quyet-dinh-soap). "
               "KHÔNG lưu transcript.")
    consent = st.checkbox("Đã có đồng thuận ghi âm/ghi chép của bệnh nhân", key="soap_consent")
    transcript = st.text_area("Dán transcript (đã/sẽ được khử định danh):", height=160,
                              key="soap_txt")
    if st.button("Khử PII + dựng SOAP", key="soap_run"):
        if not consent:
            st.error("Cần tích xác nhận đồng thuận trước.")
            return
        if not transcript.strip():
            st.warning("Dán transcript trước.")
            return
        from app.integrations.ambient_scribe import (
            AmbientError,
            blank_soap,
            build_soap_prompt,
            claude_llm,
            scrub_pii,
            transcript_to_soap,
        )
        clean, n = scrub_pii(transcript)
        st.info(f"Đã ẩn {n} mục nghi PII.")
        with st.expander("Transcript đã khử PII (gửi vào LLM)"):
            st.text(clean)
        if has_anthropic_key():
            try:
                note = transcript_to_soap(transcript, llm=claude_llm)
                st.markdown(note.to_markdown())
                return
            except AmbientError as exc:
                st.warning(f"Không gọi được LLM: {exc}")
        st.info("Chưa có ANTHROPIC_API_KEY — dán prompt sau vào skill giao-tiep-quyet-dinh-soap "
                "trong Claude, hoặc dùng khung rỗng bên dưới.")
        with st.expander("Prompt SOAP (sao chép)"):
            st.code(build_soap_prompt(clean))
        st.markdown(blank_soap().to_markdown())


def _tab_image(st) -> None:
    st.subheader("Đọc ảnh y khoa (ECG / CXR / CLS)")
    st.caption("Khử EXIF + đọc có hệ thống. Bác sĩ CHE chữ định danh trên ảnh trước khi tải. "
               "KHÔNG thay đọc chính thức.")
    consent = st.checkbox("Đã có đồng thuận của bệnh nhân", key="img_consent")
    modality = st.selectbox("Loại ảnh", ["ecg", "cxr", "lab", "generic"], key="img_mod")
    up = st.file_uploader("Tải ảnh (jpg/png)", type=["jpg", "jpeg", "png", "webp"], key="img_up")
    ctx = st.text_input("Bối cảnh lâm sàng (tuỳ chọn):", key="img_ctx")
    if st.button("Khử EXIF + đọc", key="img_run"):
        if not consent:
            st.error("Cần tích xác nhận đồng thuận trước.")
            return
        if up is None:
            st.warning("Tải một ảnh trước.")
            return
        from app.integrations.image_reading import (
            ImageReadError,
            build_reading_prompt,
            claude_vision,
            parse_reading,
            strip_exif,
        )
        clean = strip_exif(up.getvalue())
        st.success(f"Đã khử EXIF ({len(clean)} byte). Ảnh không được lưu.")
        prompt = build_reading_prompt(modality, clinical_context=ctx or None)
        if has_anthropic_key():
            try:
                mt = "image/png" if up.name.lower().endswith("png") else "image/jpeg"
                with st.spinner("Vision LLM đang đọc…"):
                    reading = parse_reading(modality, claude_vision(clean, prompt, mt))
                st.markdown(reading.to_markdown())
                return
            except ImageReadError as exc:
                st.warning(f"Không gọi được vision LLM: {exc}")
        st.info("Chưa có ANTHROPIC_API_KEY — dán prompt sau vào agent dien-giai-can-lam-sang "
                "(kèm ảnh) trong Claude.")
        with st.expander("Prompt đọc ảnh (sao chép)"):
            st.code(prompt)


def _tab_fhir(st) -> None:
    st.subheader("Kết nối FHIR R4 (EMR/HIS)")
    st.caption("Đọc — CHẶN ghi mặc định; khử PHI. Mặc định HAPI public sandbox (dữ liệu giả).")
    base = st.text_input("FHIR base URL:",
                         value=os.getenv("FHIR_BASE_URL", "https://hapi.fhir.org/baseR4"), key="fhir_base")
    if st.button("Kết nối + đọc thử", key="fhir_run"):
        from app.integrations.fhir_client import (
            FhirClient,
            FhirError,
            deidentify_patient,
            extract_medication_requests,
        )
        try:
            c = FhirClient(base)
            with st.spinner("Kết nối…"):
                ver = c.assert_r4()
                pts = c.search_resources("Patient", {"_count": "1"})
                meds = extract_medication_requests(c.search_resources("MedicationRequest", {"_count": "5"}))
        except FhirError as exc:
            st.error(f"{exc}")
            return
        st.success(f"FHIR R4 OK (fhirVersion={ver}). Ghi bị chặn (allow_write=False).")
        if pts:
            st.write("Patient (đã khử PHI):", deidentify_patient(pts[0]))
        st.write(f"MedicationRequest (không PII), {len(meds)} bản:", meds)
        st.caption(DISCLAIMER)


def _tab_citations(st) -> None:
    st.subheader("Trích dẫn thang điểm (PMID/DOI tự kiểm chứng)")
    from app.clinical_scores.verified import VERIFIED_SCORES, citation_links, identifier_coverage
    cov = identifier_coverage()
    c1, c2, c3 = st.columns(3)
    c1.metric("Độ phủ định danh", f"{cov['coverage_pct']}%")
    c2.metric("Có PMID/DOI", f"{cov['with_identifier']}/{cov['total']}")
    c3.metric("Có PMID", str(cov["with_pmid"]))
    rows = []
    for s in VERIFIED_SCORES:
        links = citation_links(s)
        rows.append({"Thang điểm": s["score_name"],
                     "PMID": links["pubmed"] or "—", "DOI": links["doi"] or "—"})
    st.dataframe(rows, use_container_width=True, hide_index=True,
                 column_config={"PMID": st.column_config.LinkColumn("PMID"),
                                "DOI": st.column_config.LinkColumn("DOI")})
    st.caption("3 thang không có định danh (NEWS2/NYHA/GOLD) là báo cáo/sách — không tồn tại PMID/DOI.")


def main() -> None:  # pragma: no cover - chỉ chạy khi streamlit run
    import streamlit as st

    st.set_page_config(page_title="Công cụ tích hợp CAFÉ-S", layout="wide")
    st.title("🔌 Công cụ tích hợp CAFÉ-S")
    st.caption("Tương tác thuốc · Ambient SOAP · Đọc ảnh · FHIR R4 · Trích dẫn thang điểm — "
               "KHÔNG lưu PII; chỉ ĐỀ XUẤT, bác sĩ duyệt.")
    t1, t2, t3, t4, t5 = st.tabs([
        "💊 Tương tác thuốc", "🎙️ Ambient SOAP", "🖼️ Đọc ảnh", "🔗 FHIR R4", "📚 Trích dẫn thang điểm"])
    with t1:
        _tab_drug(st)
    with t2:
        _tab_soap(st)
    with t3:
        _tab_image(st)
    with t4:
        _tab_fhir(st)
    with t5:
        _tab_citations(st)


if __name__ == "__main__":  # pragma: no cover
    main()
