"""Hồi quy CRITICAL (vòng lặp kiểm tra-hoàn thiện vòng 2, 2026-07-21):
tools/run_g5_auto.py hoàn toàn thiếu nhánh design_code="qualitative" —
build_redcap_rows() rơi vào nhánh "mặc định" (cohort/case_control/
cross_sectional) sinh CRF lâm sàng định lượng (huyết áp/xét nghiệm/
exposure-outcome nhị phân), và build_strobe_flowchart() rơi vào nhánh
STROBE có khung "CÓ PHƠI NHIỄM/KHÔNG PHƠI NHIỄM" — vô nghĩa với phỏng vấn
sâu/nhóm tiêu điểm lấy mẫu có chủ đích theo bão hòa dữ liệu.
"""
from __future__ import annotations

import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

from run_g5_auto import build_redcap_rows, build_strobe_flowchart  # noqa: E402

_TOPIC = "Trải nghiệm và rào cản tuân thủ điều trị ở bệnh nhân đái tháo đường"

# Trường lâm sàng định lượng KHÔNG được xuất hiện trong CRF định tính.
_QUANT_ONLY_FIELDS = ("bp_sys", "bp_dia", "heart_rate", "egfr", "hba1c")


class TestQualitativeCRFIsNotQuantitativeClinicalForm:
    def test_qualitative_crf_has_no_vitals_or_lab_fields(self):
        rows, _ = build_redcap_rows("qualitative", _TOPIC)
        names = [r[0] for r in rows]
        for f in _QUANT_ONLY_FIELDS:
            assert f not in names, f"CRF định tính vẫn còn trường lâm sàng định lượng '{f}'"

    def test_qualitative_crf_has_sampling_and_saturation_fields(self):
        rows, _ = build_redcap_rows("qualitative", _TOPIC)
        names = [r[0] for r in rows]
        for f in ("participant_id", "sampling_category", "coding_round", "saturation_reached"):
            assert f in names, f"CRF định tính thiếu trường '{f}'"

    def test_qualitative_crf_has_no_duplicate_fields(self):
        rows, _ = build_redcap_rows("qualitative", _TOPIC)
        names = [r[0] for r in rows]
        assert len(names) == len(set(names))


class TestQualitativeFlowchartIsNotStrobeExposureBased:
    def test_qualitative_flowchart_has_no_strobe_exposure_boxes(self):
        chart = build_strobe_flowchart("Demo", "qualitative", 20, 20, 10, "generic")
        assert "CÓ PHƠI" not in chart and "KHÔNG PHƠI" not in chart

    def test_qualitative_flowchart_mentions_saturation_and_coreq(self):
        chart = build_strobe_flowchart("Demo", "qualitative", 20, 20, 10, "generic")
        assert "BÃO HÒA" in chart
        assert "COREQ" in chart or "SRQR" in chart
