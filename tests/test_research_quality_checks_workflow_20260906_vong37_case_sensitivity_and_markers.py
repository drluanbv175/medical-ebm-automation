"""Hồi quy 3 phát hiện (audit vòng 37, 2026-09-06) trong
research_studio/research_quality_checks.py.

BỐI CẢNH: research_studio/ là nhánh MỒ CÔI theo CLAUDE.md — không được
tools/approve_gate.py/tools/gate_contract.py (cổng G0-G10 THẬT) gọi tới. Cả
gr7_citation_retraction/gr8_no_fabrication/gr9_no_pii_no_real_data chỉ được
gọi ở 2 nơi, cả hai đều nội bộ nhánh mồ côi: research_workflow.run_work_package()
(qua safety_gates_on_output) và research_automation/quality_gate_runner.py.
0 caller sản xuất thật ở app/ hay tools/. Cả 3 bug đều LATENT (mức ảnh hưởng
thực tế = 0 caller sản xuất) nhưng THẬT và tái hiện được — sửa vì bug thật vẫn
là bug thật, bất kể caller ở đâu.

PHÁT HIỆN #1 — gr7_citation_retraction case-sensitivity:
    if RETRACTION_MARKER in text or "retracted" in text.lower():
So sánh vế đầu KHÔNG .lower() — "retraction_marker"/"Retraction_Marker" lọt
qua thành PASS dù cùng nội dung với "RETRACTION_MARKER". Vế "retracted" không
cứu được vì đó là chuỗi tiếng Anh khác, không phải biến thể case của sentinel.

PHÁT HIỆN #2 — REAL_DATA_MARKERS (gr9) + _ACTION_MARKERS[REAL_DATA_OPERATION]
(capability_profile.py) là 2 danh sách tay lệch với nguồn canonical
DataBoundary._PRODUCTION_CONNECTOR_MARKERS/_RAW_DATA_WRITE_MARKERS mà
research_preflight.py trong CÙNG thư mục đã dùng đúng — xem
tests/test_capability_profile_workflow_20260906_vong37_real_data_markers.py
cho phần capability_profile.py.

PHÁT HIỆN #3 — gr8_no_fabrication bỏ sót nhánh CITATION_DOI_NOT_VERIFIED:
    found_c, reason_c = _boundary.check_fabricated_citation(output)
    if found_c and "FABRICATED" in reason_c:
check_fabricated_citation() trả found_c=True với 2 loại reason:
"FABRICATED_CITATION_SENTINEL" (chứa "FABRICATED") hoặc
"CITATION_DOI_NOT_VERIFIED" (KHÔNG chứa "FABRICATED"). Điều kiện lọc thêm
khiến case thứ hai không bao giờ BLOCK dù found_c đã True. Bug bị
gr7_citation_retraction (chạy CÙNG output, BLOCK vô điều kiện với found_c bất
kỳ reason nào) che khuất hoàn toàn trong 2 caller thật hiện có."""
from __future__ import annotations

from research_studio.research_quality_checks import (
    ResearchGateDecision,
    gr7_citation_retraction,
    gr8_no_fabrication,
    gr9_no_pii_no_real_data,
)


class TestCaChinhGR7KhongPhanBietHoaThuong:
    """★★★ Ca chính phát hiện #1 — RETRACTION_MARKER viết thường/hoa lẫn phải
    cùng bị REQUIRE_HUMAN_REVIEW như viết hoa toàn bộ."""

    def test_sentinel_viet_hoa_bi_bat(self):
        r = gr7_citation_retraction({"evidence_plan": "includes RETRACTION_MARKER source"})
        assert r.decision == ResearchGateDecision.REQUIRE_HUMAN_REVIEW
        assert r.reason_code == "RETRACTION_DETECTED"

    def test_sentinel_viet_thuong_van_phai_bi_bat(self):
        r = gr7_citation_retraction({"evidence_plan": "includes retraction_marker source"})
        assert r.decision == ResearchGateDecision.REQUIRE_HUMAN_REVIEW, (
            "TRƯỚC bản vá: 'RETRACTION_MARKER in text' so sánh phân biệt "
            "hoa/thường tuyệt đối, không .lower() — sentinel viết thường lọt "
            f"qua thành PASS. Kết quả thực tế: {r.decision}, {r.reason_code}"
        )
        assert r.reason_code == "RETRACTION_DETECTED"

    def test_sentinel_hoa_thuong_lan_lon_van_phai_bi_bat(self):
        r = gr7_citation_retraction({"evidence_plan": "Includes Retraction_Marker source"})
        assert r.decision == ResearchGateDecision.REQUIRE_HUMAN_REVIEW


class TestDoiChungGR7VanChayDungKhiSach:
    """Đối chứng — output sạch (không sentinel, không fabricated citation)
    vẫn PASS như cũ."""

    def test_output_sach_pass(self):
        r = gr7_citation_retraction({"evidence_plan": "clean synthetic plan, no markers"})
        assert r.decision == ResearchGateDecision.PASS


class TestCaChinhGR8BoSotCitationDoiNotVerified:
    """★★★ Ca chính phát hiện #3 — check_fabricated_citation() trả found=True
    với reason KHÔNG chứa "FABRICATED" (CITATION_DOI_NOT_VERIFIED) vẫn phải
    khiến gr8 BLOCK, không được PASS."""

    def test_doi_chua_xac_minh_bi_block(self):
        r = gr8_no_fabrication({"citation": {"doi_verified": False}})
        assert r.decision == ResearchGateDecision.BLOCK, (
            "TRƯỚC bản vá: điều kiện lọc thêm 'FABRICATED' in reason_c bỏ sót "
            "nhánh CITATION_DOI_NOT_VERIFIED (found_c=True nhưng reason không "
            f"chứa chữ FABRICATED). Kết quả thực tế: {r.decision}, {r.reason_code}"
        )
        assert "CITATION_DOI_NOT_VERIFIED" in r.reason_code

    def test_fabricated_citation_sentinel_van_block_nhu_cu(self):
        r = gr8_no_fabrication({"citation": "FABRICATED_CITATION_MARKER present"})
        assert r.decision == ResearchGateDecision.BLOCK


class TestDoiChungGR8VanChayDungKhiSach:
    def test_output_sach_pass(self):
        r = gr8_no_fabrication({"result": "clean synthetic result, no markers"})
        assert r.decision == ResearchGateDecision.PASS

    def test_fabricated_data_sentinel_van_block_nhu_cu(self):
        r = gr8_no_fabrication({"result": "FABRICATED_DATA_MARKER present"})
        assert r.decision == ResearchGateDecision.BLOCK


class TestCaChinhGR9DungNguonCanonicalDataBoundary:
    """★★★ Ca chính phát hiện #2 (phần gr9) — marker canonical của
    DataBoundary._PRODUCTION_CONNECTOR_MARKERS/_RAW_DATA_WRITE_MARKERS mà
    REAL_DATA_MARKERS (danh sách tay 4 phần tử) trước đây bỏ sót hoàn toàn
    phải khiến gr9 BLOCK."""

    def test_his_connect_bi_block(self):
        r = gr9_no_pii_no_real_data({"x": "output nối HIS_CONNECT trực tiếp"})
        assert r.decision == ResearchGateDecision.BLOCK, (
            "TRƯỚC bản vá: REAL_DATA_MARKERS = (REAL_PATIENT_DATA, "
            "REAL_DATA_MARKER, LIVE_DATABASE, EHOSPITAL_CONNECT) không có "
            f"HIS_CONNECT. Kết quả thực tế: {r.decision}, {r.reason_code}"
        )

    def test_emr_connect_bi_block(self):
        r = gr9_no_pii_no_real_data({"x": "EMR_CONNECT đang bật"})
        assert r.decision == ResearchGateDecision.BLOCK

    def test_lis_connect_bi_block(self):
        r = gr9_no_pii_no_real_data({"x": "LIS_CONNECT đang bật"})
        assert r.decision == ResearchGateDecision.BLOCK

    def test_pacs_connect_bi_block(self):
        r = gr9_no_pii_no_real_data({"x": "PACS_CONNECT đang bật"})
        assert r.decision == ResearchGateDecision.BLOCK

    def test_production_mode_bi_block(self):
        r = gr9_no_pii_no_real_data({"x": "PRODUCTION_MODE=true"})
        assert r.decision == ResearchGateDecision.BLOCK

    def test_raw_write_bi_block(self):
        r = gr9_no_pii_no_real_data({"x": "cố raw_write vào bảng"})
        assert r.decision == ResearchGateDecision.BLOCK

    def test_write_raw_patient_data_bi_block(self):
        r = gr9_no_pii_no_real_data({"x": "gọi write_raw_patient_data()"})
        assert r.decision == ResearchGateDecision.BLOCK


class TestDoiChungGR9MarkerCuVaPIIVanHoatDongDungNhuCu:
    """Đối chứng — 4 marker cũ (REAL_PATIENT_DATA/LIVE_DATABASE/
    EHOSPITAL_CONNECT) vẫn BLOCK vì đều nằm trong danh sách canonical; PII
    vẫn BLOCK; output sạch vẫn PASS."""

    def test_real_patient_data_van_block(self):
        r = gr9_no_pii_no_real_data({"x": "REAL_PATIENT_DATA"})
        assert r.decision == ResearchGateDecision.BLOCK

    def test_live_database_van_block(self):
        r = gr9_no_pii_no_real_data({"x": "LIVE_DATABASE connect"})
        assert r.decision == ResearchGateDecision.BLOCK

    def test_ehospital_connect_van_block(self):
        r = gr9_no_pii_no_real_data({"x": "EHOSPITAL_CONNECT"})
        assert r.decision == ResearchGateDecision.BLOCK

    def test_pii_van_block(self):
        r = gr9_no_pii_no_real_data({"x": "cccd 012345678901"})
        assert r.decision == ResearchGateDecision.BLOCK

    def test_output_sach_van_pass(self):
        r = gr9_no_pii_no_real_data({"x": "clean synthetic draft, no markers"})
        assert r.decision == ResearchGateDecision.PASS
