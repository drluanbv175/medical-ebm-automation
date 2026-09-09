"""Đề cương §6.2-§6.5 CÓ ĐIỀU KIỆN, CHỈ RCT (06/09/2026, cùng lệnh "đảm bảo hoàn
thiện... đạt tiêu chuẩn quốc tế/qui định hiện hành" đã thêm SAP §13-15).

Vì sao có: đối chiếu 53 dòng SPIRIT 2025 với khuôn đề cương 18 mục cho thấy 12
mục (9b/11/15a/15d/18/21a/21b/22/23/24a/24b/24c — can thiệp/đối chứng TIDieR,
ngẫu nhiên hoá, làm mù, lịch trình, PPI) đều trỏ vào MỘT MÌNH §6 "Thiết kế và
bối cảnh", trong khi `sec_thietke()` trước đó chỉ có tên thiết kế + bối cảnh —
KHÔNG MỘT DÒNG nào về can thiệp/ngẫu nhiên hoá/làm mù dù đây là nội dung IRB và
tạp chí luôn đòi hỏi ở một RCT.

Phát hiện PHỤ nghiêm trọng hơn khi đo: `exposure_intervention`/`design_specific`
đã tồn tại sẵn trong StudySpec để nuôi "quyết định còn treo" R01-R03
(`_DESIGN_FIELD_REQUIREMENTS["rct"]`), NHƯNG không builder nào render chúng vào
văn bản đề cương — bác sĩ điền dữ liệu xong vẫn không thấy gì thay đổi trong
tài liệu thật (đúng họ lỗi "hai module viết cho nhau mà chưa từng nối" của G3
PREVALENCE 31/07). Và ngay khi vá xong lần đầu, `meta_for_render()`'s luật
"chỉ điền khi khoá vắng mặt" khiến bản ĐÃ LÀM GIÀU của `design_specific` không
bao giờ tới nơi render (khoá đã có sẵn trong meta thô) — bắt được bằng chính
bộ test dưới đây trước khi vá `meta_for_render`.

Bốn việc test khoá: (1) RCT nhận đủ 4 tiểu mục §6.2-§6.5 kèm trích SPIRIT;
(2) dữ liệu THẬT từ exposure_intervention/design_specific thật sự xuất hiện
trong văn bản (không chỉ khung rỗng); (3) thiết kế khác giữ nguyên §6 như cũ,
P24 tự ĐẠT qua not_applicable_rationale suy từ design_code; (4) số tiểu mục
phái sinh đúng từ vị trí hiện tại của §6 (không viết cứng "6.x").
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import run_g10_assemble as G10  # noqa: E402
import skill_standards as S  # noqa: E402

TESTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS_DIR))
from test_g10_assemble import _write_cross_sectional_fixture  # noqa: E402
from test_protocol_checklist_spirit_2025_20260906 import _retarget_design  # noqa: E402


def _block6(text: str) -> str:
    return text.split("# 6. ", 1)[1].split("\n# 7. ", 1)[0]


def _p24_row(text: str) -> str:
    for line in text.split("\n"):
        if line.strip().startswith("| P24 |"):
            return line
    raise AssertionError("không tìm thấy dòng P24 trong ma trận bao phủ")


class TestRctGetsInterventionSubsections:
    def test_rct_with_no_data_gets_headings_and_spirit_citations(self, tmp_path):
        _write_cross_sectional_fixture(tmp_path)
        _retarget_design(tmp_path, "rct")
        res = G10.assemble("FIXT", tmp_path)
        block6 = _block6(res["md"].read_text(encoding="utf-8"))
        assert "## 6.2. Can thiệp và đối chứng (TIDieR)" in block6
        assert "## 6.3. Ngẫu nhiên hoá, phân bổ và làm mù" in block6
        assert "## 6.4. Lịch trình nghiên cứu" in block6
        assert "## 6.5. Sự tham gia của bệnh nhân/cộng đồng (PPI)" in block6
        for spirit_id in ("15a", "9b", "15d", "15b", "15c", "21a", "21b", "22",
                          "23", "24a", "24b", "24c", "18", "11"):
            assert spirit_id in block6, f"thiếu trích SPIRIT {spirit_id}"

    def test_real_data_actually_renders_not_just_placeholder(self, tmp_path):
        _write_cross_sectional_fixture(tmp_path)
        _retarget_design(tmp_path, "rct")
        mp = tmp_path / "study_meta.json"
        meta = json.loads(mp.read_text(encoding="utf-8"))
        meta["intervention"] = {"description": "Statin 20mg/ngày x 12 tuần",
                                "comparator_rationale": "Placebo chuẩn theo RCT tương tự"}
        meta["comparator"] = "Placebo"
        meta["concomitant_care_policy"] = "Cấm dùng statin khác song song"
        meta["design_specific"] = {
            "randomization_sequence_method": "Bảng số ngẫu nhiên máy tính, khối hoán vị 4",
            "randomization_type": "Ngẫu nhiên khối, phân tầng theo trung tâm",
            "allocation_concealment_mechanism": "Phong bì đục, niêm phong, đánh số tuần tự",
            "blinding_who": "Bệnh nhân, người chăm sóc, người đánh giá kết cục",
            "blinding_how": "Viên giả dược giống hệt hình dạng/màu sắc",
            "schedule_description": "Xem Hình 1 — sơ đồ SPIRIT",
            "ppi_plan": "Tham vấn nhóm bệnh nhân khi thiết kế bộ câu hỏi",
        }
        mp.write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8", newline="\n")

        res = G10.assemble("FIXT", tmp_path)
        block6 = _block6(res["md"].read_text(encoding="utf-8"))
        for fragment in ("Statin 20mg/ngày", "Placebo chuẩn theo RCT",
                         "Cấm dùng statin khác", "khối hoán vị 4",
                         "phân tầng theo trung tâm", "Phong bì đục",
                         "người đánh giá kết cục", "giống hệt hình dạng",
                         "sơ đồ SPIRIT", "Tham vấn nhóm bệnh nhân"):
            assert fragment in block6, f"dữ liệu thật không xuất hiện: {fragment!r}"
        # Hai trường CHƯA điền (allocation_access, unblinding_procedure) vẫn
        # phải còn placeholder — không được bịa hoặc để trống im lặng.
        assert block6.count(G10.TAG_BS) >= 2

        text = res["md"].read_text(encoding="utf-8")
        assert "ĐỦ DỮ LIỆU DỰ THẢO" in _p24_row(text)

    def test_sub_heading_numbers_derive_from_current_section_6_position(self, tmp_path):
        _write_cross_sectional_fixture(tmp_path)
        _retarget_design(tmp_path, "rct")
        res = G10.assemble("FIXT", tmp_path)
        text = res["md"].read_text(encoding="utf-8")
        expected = S.de_cuong_dynamic_sub_heading("thietke", "2", "Can thiệp và đối chứng (TIDieR)")
        assert expected in text
        assert expected == "## 6.2. Can thiệp và đối chứng (TIDieR)"


class TestNonRctUnaffectedAndAutoSatisfied:
    def test_cross_sectional_has_no_intervention_subsections(self, tmp_path):
        _write_cross_sectional_fixture(tmp_path)
        res = G10.assemble("FIXT", tmp_path)
        block6 = _block6(res["md"].read_text(encoding="utf-8"))
        assert "6.2." not in block6 and "6.3." not in block6
        assert "6.4." not in block6 and "6.5." not in block6
        assert "TIDieR" not in block6 and "làm mù" not in block6

    def test_p24_auto_satisfied_for_non_rct_via_derived_rationale(self, tmp_path):
        _write_cross_sectional_fixture(tmp_path)
        res = G10.assemble("FIXT", tmp_path)
        text = res["md"].read_text(encoding="utf-8")
        row = _p24_row(text)
        assert "ĐỦ DỮ LIỆU DỰ THẢO" in row

    def test_qualitative_also_unaffected(self, tmp_path):
        _write_cross_sectional_fixture(tmp_path)
        _retarget_design(tmp_path, "qualitative")
        res = G10.assemble("FIXT", tmp_path)
        block6 = _block6(res["md"].read_text(encoding="utf-8"))
        assert "6.2." not in block6
        text = res["md"].read_text(encoding="utf-8")
        assert "ĐỦ DỮ LIỆU DỰ THẢO" in _p24_row(text)


class TestValidatorAndCoverageIntegration:
    def test_check_de_cuong_still_passes_for_rct_with_data(self, tmp_path):
        import check_de_cuong
        _write_cross_sectional_fixture(tmp_path)
        _retarget_design(tmp_path, "rct")
        # R4 sẽ đọc thấy PMID 40294593/40294956 — trích dẫn CỐ ĐỊNH của CHÍNH
        # bảng checklist SPIRIT 2025 (protocol_checklist_items.py), không phải
        # trích dẫn theo-đề-tài — và báo "nghi bịa" vì hai PMID này không nằm
        # trong G0_pubmed_raw.json của đề tài. Đây KHÔNG phải lỗi giả: cả hai
        # ĐÃ được xác minh thật qua PubMed MCP lúc xây protocol_checklist_items.py
        # (06/09/2026) — ghi biên nhận đúng kênh doctrine đã có (BH08, 30/08),
        # không phải lách luật R4.
        (tmp_path / check_de_cuong.BIEN_NHAN_XAC_MINH).write_text(
            json.dumps({"muc": [
                {"pmid": "40294593", "ngay": "2026-09-06",
                 "kenh": "PubMed MCP — SPIRIT 2025 statement (JAMA)"},
                {"pmid": "40294956", "ngay": "2026-09-06",
                 "kenh": "PubMed MCP — SPIRIT 2025 E&E (BMJ, PMC12128891)"},
            ]}, ensure_ascii=False),
            encoding="utf-8")
        mp = tmp_path / "study_meta.json"
        meta = json.loads(mp.read_text(encoding="utf-8"))
        meta["intervention"] = {"description": "Statin 20mg", "comparator_rationale": "Placebo"}
        meta["comparator"] = "Placebo"
        meta["design_specific"] = {
            "randomization_sequence_method": "Bảng số ngẫu nhiên",
            "allocation_concealment_mechanism": "Phong bì đục",
            "allocation_access_control": "Dược sĩ độc lập",
            "blinding_who": "Bệnh nhân, người đánh giá",
            "blinding_how": "Giả dược giống hệt",
            "unblinding_procedure": "Chỉ mở khi có biến cố nghiêm trọng",
            "schedule_description": "Hình 1",
            "ppi_plan": "Tham vấn nhóm bệnh nhân",
        }
        mp.write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8", newline="\n")
        res = G10.assemble("FIXT", tmp_path)
        rep = check_de_cuong.validate(res["md"], tmp_path)
        assert rep["passed"], rep["errors"]
        n = 24
        assert rep["checks"]["R14_protocol_core_coverage"] == f"PASS (đủ P01-P{n})"

    def test_mutation_removing_6_3_is_visible_in_rendered_text(self, tmp_path):
        """Đột biến kiểm nhanh (không phải mutation testing đầy đủ trên mã nguồn):
        đảm bảo thân §6.3 nằm giữa hai tiêu đề, không rò sang §6.4."""
        _write_cross_sectional_fixture(tmp_path)
        _retarget_design(tmp_path, "rct")
        res = G10.assemble("FIXT", tmp_path)
        text = res["md"].read_text(encoding="utf-8")
        seg = text.split("## 6.3. Ngẫu nhiên hoá", 1)[1].split("## 6.4. Lịch trình", 1)[0]
        assert "SPIRIT 21a" in seg and "SPIRIT 24c" in seg
        assert "Lịch tuyển mẫu" not in seg
