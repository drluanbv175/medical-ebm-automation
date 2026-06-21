"""Panel ResearchOS cho Tab 6 của Streamlit dashboard.

Gọi bằng: render_research_os_panel(st)
Không có dependency SQLAlchemy — hoàn toàn in-memory.
"""
from __future__ import annotations

import streamlit as st


def render_research_os_panel() -> None:  # noqa: PLR0912, PLR0915
    """Render ResearchOS tools section (design router, guideline mapper, SAP, traceability)."""
    st.divider()
    st.subheader("🔬 ResearchOS — Công cụ thiết kế nghiên cứu (G0–G9)")
    st.caption(
        "Công cụ HỖ TRỢ ra quyết định: định tuyến thiết kế từ câu hỏi PICO, "
        "ánh xạ chuẩn báo cáo EQUATOR, kiểm tra SAP, xây ma trận truy nguyên. "
        "Không lưu dữ liệu bệnh nhân (PII). Không thay thế phán đoán chuyên môn."
    )

    try:
        from app.research_os.design_router import route_design_with_confidence
        from app.research_os.reporting_guideline_mapper import (
            reporting_guideline_for_design as reporting_guideline,
            reporting_guidelines_all,
        )
        from app.research_os.causal_inference import (
            design_allows_causal,
            causal_design_warning,
        )
        from app.research_os.sap_engine import create_sap, lock_sap
        from app.research_os.study_traceability_matrix import (
            TraceabilityRow,
            validate_traceability,
        )
    except ImportError as exc:
        st.error(f"Không load được research_os: {exc}")
        return

    ros_tab1, ros_tab2, ros_tab3, ros_tab4 = st.tabs([
        "🗺️ Design Router",
        "📋 Reporting Guideline",
        "📊 SAP Validator",
        "🔗 Traceability Matrix",
    ])

    # ── Tab R1: Design Router ────────────────────────────────────────────────
    with ros_tab1:
        st.markdown("#### Định tuyến thiết kế nghiên cứu từ câu hỏi")
        st.caption(
            "Nhập câu hỏi nghiên cứu (bằng tiếng Việt hoặc tiếng Anh) → hệ thống "
            "gợi ý thiết kế phù hợp nhất và mức tin cậy."
        )
        pico_q = st.text_area(
            "Câu hỏi nghiên cứu / PICO",
            key="ros_pico_q",
            height=100,
            placeholder=(
                "VD: Ở bệnh nhân THA, liệu phác đồ 2 thuốc có giảm biến cố tim mạch "
                "hơn đơn trị liệu không?\n"
                "VD: Xây dựng mô hình dự báo nguy cơ đái tháo đường type 2 tại cộng đồng."
            ),
        )
        if st.button("🔍 Định tuyến thiết kế", key="ros_route_btn", disabled=not pico_q.strip()):
            design, conf = route_design_with_confidence(pico_q)
            allows_causal = design_allows_causal(design)
            causal_warn = causal_design_warning(design)

            col_a, col_b = st.columns(2)
            col_a.metric("Thiết kế đề xuất", design.replace("_", " ").title())
            col_b.metric("Độ tin cậy phân loại", f"{int(conf * 100)}%")

            if allows_causal:
                st.success("✅ Thiết kế này **cho phép** kết luận quan hệ nhân quả.")
            elif causal_warn:
                st.warning(f"⚠️ **Cảnh báo nhân quả:** {causal_warn}")

    # ── Tab R2: Reporting Guideline ──────────────────────────────────────────
    with ros_tab2:
        st.markdown("#### Ánh xạ chuẩn báo cáo EQUATOR")
        DESIGN_OPTIONS = {
            "RCT": "randomized_controlled_trial",
            "Cohort": "cohort",
            "Case-Control": "case_control",
            "Cross-sectional": "cross_sectional",
            "Systematic Review / Meta-analysis": "systematic_review",
            "Scoping Review": "evidence_mapping_or_scoping_review",
            "Diagnostic Accuracy": "diagnostic_accuracy",
            "Prediction Model / AI": "prediction_model",
            "Qualitative": "qualitative",
            "Case Report": "case_report",
            "Economic Evaluation": "economic_evaluation",
            "Quality Improvement": "quality_improvement",
        }
        selected_label = st.selectbox(
            "Thiết kế nghiên cứu", list(DESIGN_OPTIONS.keys()), key="ros_design_sel"
        )
        selected_design = DESIGN_OPTIONS[selected_label]
        gl_info = reporting_guidelines_all(selected_design)
        primary_gl = reporting_guideline(selected_design)

        st.markdown(f"**Chuẩn báo cáo chính:** `{primary_gl}`")
        supps = gl_info.get("supplementary", [])
        if supps:
            st.markdown("**Chuẩn bổ sung:** " + ", ".join(f"`{s}`" for s in supps))
        url = gl_info.get("equator_url", "")
        if url:
            st.markdown(f"**EQUATOR Network:** [{url}]({url})")

    # ── Tab R3: SAP Validator ────────────────────────────────────────────────
    with ros_tab3:
        st.markdown("#### Tạo và kiểm tra SAP (Statistical Analysis Plan)")
        st.caption(
            "Điền thông tin → hệ thống kiểm tra tính hợp lệ theo cổng G7. "
            "SAP phải được khóa TRƯỚC khi phân tích. Không lưu vào database."
        )
        sap_primary = st.text_input(
            "Phân tích chính (primary analysis)",
            key="ros_sap_primary",
            placeholder="VD: Hồi quy logistic đa biến, kết cục: THA kiểm soát ở tháng 6",
        )
        sap_secondary = st.text_area(
            "Phân tích phụ (secondary analyses, mỗi dòng 1 phân tích)",
            key="ros_sap_secondary",
            height=80,
            placeholder="VD: Phân tích theo nhóm tuổi\nPhân tích per-protocol",
        )
        sap_sensitivity = st.text_area(
            "Phân tích độ nhạy (sensitivity analyses)",
            key="ros_sap_sensitivity",
            height=60,
            placeholder="VD: Loại bệnh nhân mất theo dõi > 20%",
        )
        sap_missing = st.selectbox(
            "Chiến lược dữ liệu thiếu",
            ["complete_case", "multiple_imputation", "last_observation_carried_forward", "other"],
            key="ros_sap_missing",
        )
        sap_alpha = st.number_input(
            "Mức ý nghĩa thống kê (α)", min_value=0.001, max_value=0.1,
            value=0.05, step=0.005, key="ros_sap_alpha"
        )

        if st.button("✅ Kiểm tra SAP", key="ros_sap_check", disabled=not sap_primary.strip()):
            secondary_list = [x.strip() for x in sap_secondary.splitlines() if x.strip()]
            sensitivity_list = [x.strip() for x in sap_sensitivity.splitlines() if x.strip()]
            try:
                sap = create_sap(
                    primary_analysis=sap_primary,
                    secondary_analyses=secondary_list or None,
                    sensitivity_analyses=sensitivity_list or None,
                    missing_data_strategy=sap_missing,
                    significance_level=sap_alpha,
                )
                st.success(f"✅ SAP hợp lệ (ID: `{sap.sap_id}`). Có thể khóa để chạy phân tích.")
                if st.button("🔒 Khóa SAP (mô phỏng)", key="ros_sap_lock"):
                    locked = lock_sap(sap)
                    st.success(f"🔒 SAP đã khóa — trạng thái: {locked.status.value}")
            except ValueError as e:
                st.error(f"❌ SAP không hợp lệ: {e}")

    # ── Tab R4: Traceability Matrix ──────────────────────────────────────────
    with ros_tab4:
        st.markdown("#### Ma trận truy nguyên (Objective → Variable → Instrument → Analysis → Output)")
        st.caption(
            "Thêm hàng vào ma trận đồng bộ — đảm bảo mọi mục tiêu đều có biến số, "
            "công cụ thu thập, bước phân tích và bảng kết quả tương ứng."
        )

        if "ros_matrix_rows" not in st.session_state:
            st.session_state["ros_matrix_rows"] = []

        with st.form("ros_matrix_form"):
            fc1, fc2 = st.columns(2)
            f_rq = fc1.text_input("Câu hỏi NC / Mục tiêu", key="ros_f_rq",
                                  placeholder="RQ1: Tỉ lệ THA kiểm soát đạt")
            f_obj = fc2.text_input("Objective (ngắn gọn)", key="ros_f_obj",
                                   placeholder="Xác định tỉ lệ đạt mục tiêu HA")
            fc3, fc4 = st.columns(2)
            f_var = fc3.text_input("Tên biến số", key="ros_f_var",
                                   placeholder="bp_controlled_6m")
            f_inst = fc4.text_input("Công cụ thu thập", key="ros_f_inst",
                                    placeholder="Bảng thu thập hồ sơ bệnh án")
            fc5, fc6 = st.columns(2)
            f_ana = fc5.text_input("Bước phân tích", key="ros_f_ana",
                                   placeholder="Tần số, tỉ lệ % + 95% CI")
            f_out = fc6.text_input("Bảng kết quả", key="ros_f_out",
                                   placeholder="Table 2 — Tỉ lệ đạt mục tiêu")
            if st.form_submit_button("➕ Thêm hàng"):
                if f_rq.strip() and f_var.strip() and f_ana.strip() and f_out.strip():
                    st.session_state["ros_matrix_rows"].append(
                        TraceabilityRow(
                            research_question=f_rq.strip(),
                            variable_name=f_var.strip(),
                            analysis_step=f_ana.strip(),
                            output_table=f_out.strip(),
                            objective=f_obj.strip(),
                            instrument_name=f_inst.strip(),
                        )
                    )
                    st.success("Đã thêm hàng.")
                else:
                    st.warning("Điền ít nhất: câu hỏi NC, tên biến, bước phân tích, bảng kết quả.")

        rows = st.session_state.get("ros_matrix_rows", [])
        if rows:
            import pandas as pd
            df = pd.DataFrame([{
                "Câu hỏi NC": r.research_question,
                "Mục tiêu": r.objective,
                "Biến số": r.variable_name,
                "Công cụ": r.instrument_name,
                "Phân tích": r.analysis_step,
                "Bảng KQ": r.output_table,
            } for r in rows])
            st.dataframe(df, use_container_width=True, hide_index=True)

            issues = validate_traceability(rows)
            if issues:
                for iss in issues:
                    st.warning(f"⚠️ {iss}")
            else:
                st.success(f"✅ Ma trận hợp lệ — {len(rows)} hàng, không phát hiện lỗ hổng.")

            if st.button("🗑️ Xóa toàn bộ ma trận", key="ros_matrix_clear"):
                st.session_state["ros_matrix_rows"] = []
                st.rerun()
        else:
            st.info("Chưa có hàng nào. Điền form trên và bấm '➕ Thêm hàng'.")
