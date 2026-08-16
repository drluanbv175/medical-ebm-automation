"""Test G10 assembler + validator check_de_cuong trên bộ checkpoint FIXTURE.

Không phụ thuộc mạng: dựng tay checkpoint G0-G9 tối thiểu trong thư mục tạm,
chạy assemble(), rồi kiểm đề cương sinh ra đạt chuẩn skill. Có test đối kháng:
- CRF caveat PHẢI nổ với đề tài generic + biến lâm sàng mặc định.
- CRF caveat KHÔNG nổ với đề tài lâm sàng thật (chuyên khoa cụ thể).
- Validator PHẢI bắt: PMID bịa, nhãn tự chế, thiếu mục.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import check_de_cuong  # noqa: E402
import run_g10_assemble as G10  # noqa: E402
import skill_standards as S  # noqa: E402


def _write_cross_sectional_fixture(d: Path, specialty="generic",
                                   crf=None, pmids=None):
    """Ghi bộ checkpoint G0-G9 tối thiểu cho đề tài cắt ngան."""
    if crf is None:
        crf = ["record_id", "age", "sex", "bmi", "bp_sys", "heart_rate",
               "dm", "htn", "exposure_var", "primary_outcome"]
    if pmids is None:
        pmids = ["40995744", "24700992", "16003661"]
    cps = {
        "G0": {"study": "FIXT", "gate": "G0", "guardrail": {"passed": True},
               "topic": "Đề tài fixture cắt ngang",
               "pubmed_results": {"n_pmids": len(pmids)},
               "evidence_level": "TRUNG BÌNH",
               "research_gaps": ["Chưa có guideline"]},
        "G1": {"study": "FIXT", "gate": "G1", "guardrail": {"passed": True},
               "question_type": "descriptive",
               "design": {"primary": "Nghiên cứu Cắt ngang Mô tả",
                          "internal_code": "cross_sectional",
                          "reporting_standard": "STROBE"}},
        "G2": {"study": "FIXT", "gate": "G2", "guardrail": {"passed": True},
               "g2_status": "PENDING", "risk_level": "TỐI THIỂU",
               "irb_route": "EXPEDITED", "registration_required": "KHÔNG BẮT BUỘC",
               "register_where": "Không cần",
               "documents_generated": ["TL1 — Đơn IRB", "TL4 — ICF"]},
        "G3": {"study": "FIXT", "gate": "G3", "guardrail": "✅ PASS",
               "design_code": "cross_sectional", "alpha": 0.05, "power": 0.8,
               "n_per_group": 385, "n_total": 385, "n_adjusted": 428,
               "dropout": 0.1, "formula_used": "Cỡ mẫu ước lượng tỷ lệ (xấp xỉ chuẩn/Cochran): p=0.50, e=0.05"},
        "G4": {"study": "FIXT", "gate": "G4", "guardrail": "✅ PASS",
               "g4_sap_version": "1.0", "g4_status": "PENDING",
               "reporting_standard": "STROBE"},
        "G5": {"study": "FIXT", "gate": "G5", "guardrail": "✅ PASS",
               "specialty": specialty,
               "specialty_is_generic_placeholder": (specialty == "generic"),
               "redcap_rows": len(crf), "crf_columns": crf,
               "scripts_generated": ["scripts/data_cleaning.py"],
               "database_lock_status": "PENDING — chưa thu thập"},
        "G6": {"study": "FIXT", "gate": "G6", "guardrail": "✅ PASS",
               "reporting_std": "STROBE"},
        "G7": {"study": "FIXT", "gate": "G7",
               "guardrail": {"status": "✅ PASS", "errors": []},
               "pmids_used_as_seed": pmids, "n_pmids": len(pmids),
               "reporting_standard": "STROBE 2007"},
        "G8": {"study": "FIXT", "gate": "G8", "guardrail": {"passed": True},
               "journal_suggestions": [{"journal": "PLOS ONE", "if": 3.7,
                                        "note": "Đa lĩnh vực"}]},
        "G9": {"study": "FIXT", "gate": "G9", "guardrail": {"passed": True},
               "submission_package_ready": False, "n_authors": 3},
    }
    for g, cp in cps.items():
        (d / f"{g}_checkpoint.json").write_text(
            json.dumps(cp, ensure_ascii=False), encoding="utf-8", newline="\n")
    # G0_pubmed_raw.json: nguồn PubMed THẬT — để R4 đối chiếu (raw-verified).
    raw = {"pmids": pmids, "results": [{"pmid": p} for p in pmids]}
    (d / "G0_pubmed_raw.json").write_text(
        json.dumps(raw, ensure_ascii=False), encoding="utf-8", newline="\n")
    (d / "study_meta.json").write_text(
        json.dumps(
            {
                "study_kind": "synthetic_test",
                "disclaimer": "SYNTHETIC TEST ONLY — không phải phê duyệt người thật.",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


@pytest.fixture
def cross_sectional_study(tmp_path):
    _write_cross_sectional_fixture(tmp_path)
    return tmp_path


class TestAssemble:
    def test_produces_md_and_checkpoint(self, cross_sectional_study):
        res = G10.assemble("FIXT", cross_sectional_study)
        assert res["md"].exists()
        assert res["checkpoint"].exists()
        cp = json.loads(res["checkpoint"].read_text(encoding="utf-8", newline="\n"))
        assert cp["gate"] == "G10"
        assert cp["n_de_cuong_sections"] == 16

    def test_all_16_sections_present(self, cross_sectional_study):
        res = G10.assemble("FIXT", cross_sectional_study)
        text = res["md"].read_text(encoding="utf-8")
        for num, title, _ in S.DE_CUONG_SECTIONS:
            assert f"# {num}. {title}" in text, f"thiếu mục {num}. {title}"

    def test_real_sample_size_pulled(self, cross_sectional_study):
        res = G10.assemble("FIXT", cross_sectional_study)
        text = res["md"].read_text(encoding="utf-8")
        assert "428" in text            # N điều chỉnh
        assert "Cỡ mẫu ước lượng tỷ lệ" in text

    def test_gate_table_has_all_10_skill_gates(self, cross_sectional_study):
        res = G10.assemble("FIXT", cross_sectional_study)
        text = res["md"].read_text(encoding="utf-8")
        for sg in S.SKILL_GATES:
            assert f"| {sg} |" in text

    def test_display_item_inventory_has_required_tables_and_figures(self, cross_sectional_study):
        res = G10.assemble("FIXT", cross_sectional_study)
        text = res["md"].read_text(encoding="utf-8")
        assert "# Danh mục bảng và hình chuẩn xuất bản" in text
        for item in ("Bảng 1", "Bảng 2", "Hình 1", "Hình 2"):
            assert f"| {item} |" in text
        for term in ("caption", "trục", "đơn vị", "N", "95% CI"):
            assert term in text

    def test_international_compliance_matrix_has_transparency_reproducibility(self, cross_sectional_study):
        res = G10.assemble("FIXT", cross_sectional_study)
        text = res["md"].read_text(encoding="utf-8")
        assert "# Ma trận tuân thủ tiêu chuẩn quốc tế" in text
        for term in (
            "CONSORT", "STROBE", "ICH-GCP", "GCP", "IRB", "SAP",
            "data availability", "code availability", "COI", "AI disclosure",
            "minh bạch", "tái lập",
        ):
            assert term in text

    def test_final_technical_completion_checklist_has_10_steps_and_outputs(self, cross_sectional_study):
        res = G10.assemble("FIXT", cross_sectional_study)
        text = res["md"].read_text(encoding="utf-8")
        assert "# Bảng kiểm hoàn thành kỹ thuật" in text
        for step_id, _name, _criterion in S.RESEARCH_COMPLETION_STEPS:
            assert f"| {step_id} |" in text
        for item in S.RESEARCH_OUTPUT_PACKAGE_ITEMS:
            assert item in text
        for term in (
            "Nội dung đã được khóa",
            "Phân biệt nguồn thông tin",
            "Kiểm định cuối trước khi ký",
            "HOÀN THÀNH KỸ THUẬT",
        ):
            assert term in text

    def test_missing_information_register_lists_open_real_world_signals(self, cross_sectional_study):
        res = G10.assemble("FIXT", cross_sectional_study)
        text = res["md"].read_text(encoding="utf-8")
        assert "# Danh sách thông tin còn thiếu và quyết định cần xác nhận" in text
        for term in ("Thông tin còn thiếu", "Ảnh hưởng", "Phương án an toàn",
                     "Người quyết định"):
            assert term in text
        for signal in ("irb_approved", "sap_locked", "db_locked",
                       "results_final", "integrity_signed"):
            assert f"`{signal}`" in text

    def test_document_control_has_version_date_and_change_history(self, cross_sectional_study):
        res = G10.assemble("FIXT", cross_sectional_study)
        text = res["md"].read_text(encoding="utf-8")
        assert "# Kiểm soát phiên bản và lịch sử thay đổi" in text
        for term in (
            "Phiên bản tài liệu",
            "Ngày tạo/cập nhật",
            "Nguồn thay đổi",
            "Người phê duyệt/chủ nhiệm",
            "Nhật ký thay đổi",
        ):
            assert term in text
        cp = json.loads(res["checkpoint"].read_text(encoding="utf-8"))
        assert cp["document_control"]["requires_change_history"] is True

    def test_traceability_matrix_links_objectives_variables_analysis_and_outputs(
            self, cross_sectional_study):
        res = G10.assemble("FIXT", cross_sectional_study)
        text = res["md"].read_text(encoding="utf-8")
        assert "# Ma trận truy xuất mục tiêu-biến-công cụ-phân tích-bảng" in text
        for term in (
            "Mục tiêu/câu hỏi",
            "Biến/kết cục",
            "Công cụ/nguồn dữ liệu",
            "Phân tích định trước",
            "Bảng/hình đầu ra",
            "Cổng nguồn",
            "Bảng 1",
            "Bảng 2",
            "Hình 1",
            "Hình 2",
        ):
            assert term in text

    def test_passes_own_validator(self, cross_sectional_study):
        res = G10.assemble("FIXT", cross_sectional_study)
        report = check_de_cuong.validate(res["md"], cross_sectional_study)
        assert report["passed"], report["errors"]


class TestCrfIntegrityCaveat:
    def test_caveat_fires_for_generic_with_clinical_covariates(self, tmp_path):
        _write_cross_sectional_fixture(tmp_path, specialty="generic")
        res = G10.assemble("FIXT", tmp_path)
        text = res["md"].read_text(encoding="utf-8")
        assert "CẢNH BÁO LIÊM CHÍNH DỮ LIỆU" in text

    def test_caveat_suppressed_for_real_specialty(self, tmp_path):
        _write_cross_sectional_fixture(tmp_path, specialty="cardiology_hf")
        res = G10.assemble("FIXT", tmp_path)
        text = res["md"].read_text(encoding="utf-8")
        assert "CẢNH BÁO LIÊM CHÍNH DỮ LIỆU" not in text

    def test_caveat_suppressed_when_no_clinical_covariates(self, tmp_path):
        # generic nhưng CRF KHÔNG chứa biến sinh hiệu -> không nổ cảnh báo.
        _write_cross_sectional_fixture(
            tmp_path, specialty="generic",
            crf=["record_id", "wait_time", "staff_attitude", "facility_score"])
        res = G10.assemble("FIXT", tmp_path)
        text = res["md"].read_text(encoding="utf-8")
        assert "CẢNH BÁO LIÊM CHÍNH DỮ LIỆU" not in text


class TestValidatorCatchesFabrication:
    def test_catches_fabricated_pmid(self, cross_sectional_study):
        res = G10.assemble("FIXT", cross_sectional_study)
        # Chèn 1 PMID KHÔNG có trong checkpoint -> phải bị bắt.
        text = res["md"].read_text(encoding="utf-8")
        text += "\n\nTham khảo giả: PMID: 99999999 (bịa).\n"
        res["md"].write_text(text, encoding="utf-8", newline="\n")
        report = check_de_cuong.validate(res["md"], cross_sectional_study)
        assert not report["passed"]
        assert any("99999999" in e for e in report["errors"])

    def test_catches_invalid_status_tag(self, cross_sectional_study):
        res = G10.assemble("FIXT", cross_sectional_study)
        text = res["md"].read_text(encoding="utf-8")
        text += "\n\nGhi chú: [CẦN LÀM NGAY LẬP TỨC] nhãn tự chế.\n"
        res["md"].write_text(text, encoding="utf-8", newline="\n")
        report = check_de_cuong.validate(res["md"], cross_sectional_study)
        assert not report["passed"]
        assert any("R3" in e for e in report["errors"])

    def test_freeform_can_caveat_not_flagged_as_invalid_tag(self, cross_sectional_study):
        """Bug thật (2026-07-06, phát hiện qua chạy G0→G10 thiết kế chẩn đoán
        lần đầu): mẫu "[CẦN — giải thích tự do]" (có em-dash) là quy ước chú
        thích ĐÃ DÙNG PHỔ BIẾN khắp G0-G9 (vd n_auc() trong G3), KHÔNG phải
        nhãn trạng thái tự chế sai chuẩn — R3 trước đây coi cả hai là một,
        khiến G10 CRASH thật (exit=1) lần đầu tiên một đề tài chẩn đoán chạy
        hết pipeline. Câu chữ THẬT lấy nguyên văn từ tools/run_g3_auto.py."""
        res = G10.assemble("FIXT", cross_sectional_study)
        text = res["md"].read_text(encoding="utf-8")
        text += (
            "\n\n[CẦN — các phần mềm khác nhau (PASS/MedCalc/nQuery) có thể "
            "cho N hơi khác do giả định phương sai khác nhau; nếu cỡ mẫu "
            "của nghiên cứu phụ thuộc chủ yếu vào con số này, nên nhờ "
            "thống kê viên đối chiếu lại bằng phần mềm chuyên dụng.]\n"
        )
        res["md"].write_text(text, encoding="utf-8", newline="\n")
        report = check_de_cuong.validate(res["md"], cross_sectional_study)
        assert report["checks"]["R3_valid_tags"] == "PASS"

    def test_still_catches_short_invented_tag_without_em_dash(self, cross_sectional_study):
        """Đối chứng: nhãn tự chế NGẮN không có em-dash (không phải chú thích
        tự do) vẫn phải bị bắt — tránh sửa quá tay làm R3 mất tác dụng."""
        res = G10.assemble("FIXT", cross_sectional_study)
        text = res["md"].read_text(encoding="utf-8")
        text += "\n\n[CẦN GẤP RÚT XỬ LÝ]\n"
        res["md"].write_text(text, encoding="utf-8", newline="\n")
        report = check_de_cuong.validate(res["md"], cross_sectional_study)
        assert not report["passed"]
        assert any("R3" in e for e in report["errors"])

    def test_catches_missing_section(self, cross_sectional_study):
        res = G10.assemble("FIXT", cross_sectional_study)
        text = res["md"].read_text(encoding="utf-8")
        # Xoá heading mục 8 (Cỡ mẫu) -> validator phải báo thiếu.
        text = text.replace("# 8. Cỡ mẫu", "# 8888. Cỡ mẫu XXX")
        res["md"].write_text(text, encoding="utf-8", newline="\n")
        report = check_de_cuong.validate(res["md"], cross_sectional_study)
        assert not report["passed"]
        assert any("R1" in e for e in report["errors"])

    def test_catches_missing_display_item_inventory(self, cross_sectional_study):
        res = G10.assemble("FIXT", cross_sectional_study)
        text = res["md"].read_text(encoding="utf-8")
        text = text.replace("# Danh mục bảng và hình chuẩn xuất bản",
                            "# Danh mục bị đổi tên")
        res["md"].write_text(text, encoding="utf-8", newline="\n")
        report = check_de_cuong.validate(res["md"], cross_sectional_study)
        assert not report["passed"]
        assert any("R7" in e for e in report["errors"])

    def test_catches_missing_required_figure(self, cross_sectional_study):
        res = G10.assemble("FIXT", cross_sectional_study)
        text = res["md"].read_text(encoding="utf-8")
        text = text.replace("| Hình 2 |", "| Hình X |")
        res["md"].write_text(text, encoding="utf-8", newline="\n")
        report = check_de_cuong.validate(res["md"], cross_sectional_study)
        assert not report["passed"]
        assert any("Hình 2" in e for e in report["errors"])

    def test_catches_missing_international_compliance_matrix(self, cross_sectional_study):
        res = G10.assemble("FIXT", cross_sectional_study)
        text = res["md"].read_text(encoding="utf-8")
        text = text.replace("# Ma trận tuân thủ tiêu chuẩn quốc tế",
                            "# Ma trận bị đổi tên")
        res["md"].write_text(text, encoding="utf-8", newline="\n")
        report = check_de_cuong.validate(res["md"], cross_sectional_study)
        assert not report["passed"]
        assert any("R8" in e for e in report["errors"])

    def test_catches_missing_ich_gcp_in_compliance_matrix(self, cross_sectional_study):
        res = G10.assemble("FIXT", cross_sectional_study)
        text = res["md"].read_text(encoding="utf-8")
        text = text.replace("ICH-GCP", "ICH G_C_P")
        res["md"].write_text(text, encoding="utf-8", newline="\n")
        report = check_de_cuong.validate(res["md"], cross_sectional_study)
        assert not report["passed"]
        assert any("ICH-GCP" in e for e in report["errors"])

    def test_catches_missing_final_technical_completion_checklist(self, cross_sectional_study):
        res = G10.assemble("FIXT", cross_sectional_study)
        text = res["md"].read_text(encoding="utf-8")
        text = text.replace("# Bảng kiểm hoàn thành kỹ thuật",
                            "# Bảng kiểm bị đổi tên")
        res["md"].write_text(text, encoding="utf-8", newline="\n")
        report = check_de_cuong.validate(res["md"], cross_sectional_study)
        assert not report["passed"]
        assert any("R9" in e for e in report["errors"])

    def test_catches_missing_required_output_document(self, cross_sectional_study):
        res = G10.assemble("FIXT", cross_sectional_study)
        text = res["md"].read_text(encoding="utf-8")
        text = text.replace("Báo cáo phản biện ba vai trò", "Báo cáo phản biện")
        res["md"].write_text(text, encoding="utf-8", newline="\n")
        report = check_de_cuong.validate(res["md"], cross_sectional_study)
        assert not report["passed"]
        assert any("Báo cáo phản biện ba vai trò" in e for e in report["errors"])

    def test_catches_false_technical_completion_claim(self, cross_sectional_study):
        res = G10.assemble("FIXT", cross_sectional_study)
        text = res["md"].read_text(encoding="utf-8")
        text += "\n\nKết luận điều hành: HOÀN THÀNH KỸ THUẬT.\n"
        res["md"].write_text(text, encoding="utf-8", newline="\n")
        report = check_de_cuong.validate(res["md"], cross_sectional_study)
        assert not report["passed"]
        assert any("R10" in e for e in report["errors"])
        assert any("irb_approved" in e for e in report["errors"])

    def test_allows_explicit_not_completed_status(self, cross_sectional_study):
        res = G10.assemble("FIXT", cross_sectional_study)
        text = res["md"].read_text(encoding="utf-8")
        text += "\n\nKết luận điều hành: CHƯA HOÀN THÀNH KỸ THUẬT.\n"
        res["md"].write_text(text, encoding="utf-8", newline="\n")
        report = check_de_cuong.validate(res["md"], cross_sectional_study)
        assert report["passed"], report["errors"]

    def test_allows_completion_claim_when_all_real_world_signals_exist(self, cross_sectional_study):
        meta = {
            "irb_approved": True,
            "sap_lock_date": "2026-07-13",
            "data_lock_date": "2026-07-14",
            "results_final": True,
            "peer_review_approved": True,
            "integrity_signed": True,
        }
        (cross_sectional_study / "study_meta.json").write_text(
            json.dumps(meta, ensure_ascii=False), encoding="utf-8", newline="\n")
        res = G10.assemble("FIXT", cross_sectional_study)
        text = res["md"].read_text(encoding="utf-8")
        text += "\n\nKết luận điều hành: HOÀN THÀNH KỸ THUẬT.\n"
        res["md"].write_text(text, encoding="utf-8", newline="\n")
        report = check_de_cuong.validate(res["md"], cross_sectional_study)
        assert report["passed"], report["errors"]
        assert report["checks"]["R10_no_false_completion"].startswith("PASS")

    def test_catches_missing_information_register(self, cross_sectional_study):
        res = G10.assemble("FIXT", cross_sectional_study)
        text = res["md"].read_text(encoding="utf-8")
        text = text.replace("# Danh sách thông tin còn thiếu và quyết định cần xác nhận",
                            "# Danh sách bị đổi tên")
        res["md"].write_text(text, encoding="utf-8", newline="\n")
        report = check_de_cuong.validate(res["md"], cross_sectional_study)
        assert not report["passed"]
        assert any("R11" in e for e in report["errors"])

    def test_catches_missing_open_signal_in_missing_information_register(self, cross_sectional_study):
        res = G10.assemble("FIXT", cross_sectional_study)
        text = res["md"].read_text(encoding="utf-8")
        text = text.replace("`results_final`", "`ket_qua_that`")
        res["md"].write_text(text, encoding="utf-8", newline="\n")
        report = check_de_cuong.validate(res["md"], cross_sectional_study)
        assert not report["passed"]
        assert any("results_final" in e for e in report["errors"])

    def test_catches_missing_document_control(self, cross_sectional_study):
        res = G10.assemble("FIXT", cross_sectional_study)
        text = res["md"].read_text(encoding="utf-8")
        text = text.replace("# Kiểm soát phiên bản và lịch sử thay đổi",
                            "# Kiểm soát bị đổi tên")
        res["md"].write_text(text, encoding="utf-8", newline="\n")
        report = check_de_cuong.validate(res["md"], cross_sectional_study)
        assert not report["passed"]
        assert any("R12" in e for e in report["errors"])

    def test_catches_missing_document_control_term(self, cross_sectional_study):
        res = G10.assemble("FIXT", cross_sectional_study)
        text = res["md"].read_text(encoding="utf-8")
        text = text.replace("Người phê duyệt/chủ nhiệm", "Người ký")
        res["md"].write_text(text, encoding="utf-8", newline="\n")
        report = check_de_cuong.validate(res["md"], cross_sectional_study)
        assert not report["passed"]
        assert any("Người phê duyệt/chủ nhiệm" in e for e in report["errors"])

    def test_catches_missing_traceability_matrix(self, cross_sectional_study):
        res = G10.assemble("FIXT", cross_sectional_study)
        text = res["md"].read_text(encoding="utf-8")
        text = text.replace("# Ma trận truy xuất mục tiêu-biến-công cụ-phân tích-bảng",
                            "# Ma trận truy xuất bị đổi tên")
        res["md"].write_text(text, encoding="utf-8", newline="\n")
        report = check_de_cuong.validate(res["md"], cross_sectional_study)
        assert not report["passed"]
        assert any("R13" in e for e in report["errors"])

    def test_catches_missing_traceability_required_term(self, cross_sectional_study):
        res = G10.assemble("FIXT", cross_sectional_study)
        text = res["md"].read_text(encoding="utf-8")
        text = text.replace("Phân tích định trước", "Phân tích dự kiến")
        res["md"].write_text(text, encoding="utf-8", newline="\n")
        report = check_de_cuong.validate(res["md"], cross_sectional_study)
        assert not report["passed"]
        assert any("Phân tích định trước" in e for e in report["errors"])

    def test_clean_de_cuong_passes(self, cross_sectional_study):
        res = G10.assemble("FIXT", cross_sectional_study)
        report = check_de_cuong.validate(res["md"], cross_sectional_study)
        assert report["passed"]
        # PMID trong fixture đều có trong G0_pubmed_raw.json -> đối chiếu raw.
        assert report["checks"]["R4_pmid_traceable"].startswith("PASS")

    def test_seed_only_pmid_warns_not_silent_pass(self, tmp_path):
        # Regression #1/#2: PMID chỉ ở seed (KHÔNG ở raw) phải WARN, không im lặng PASS.
        _write_cross_sectional_fixture(tmp_path, pmids=["40995744", "24700992"])
        # Ghi đè raw để CHỈ chứa 1/2 PMID -> PMID kia thành seed-only.
        (tmp_path / "G0_pubmed_raw.json").write_text(
            json.dumps({"pmids": ["40995744"], "results": [{"pmid": "40995744"}]}),
            encoding="utf-8", newline="\n")
        res = G10.assemble("FIXT", tmp_path)
        report = check_de_cuong.validate(res["md"], tmp_path)
        assert report["passed"]  # không fail (đề cương đã gắn nhãn cần kiểm chứng)
        assert report["checks"]["R4_pmid_traceable"].startswith("WARN")
        assert "24700992" in report["seed_only_pmids"]
        assert any("seed" in w.lower() for w in report["warnings"])


class TestNoCheckpointsRaises:
    def test_empty_dir_raises(self, tmp_path):
        with pytest.raises(SystemExit):
            G10.assemble("EMPTY", tmp_path)
