"""Hồi quy (vòng lặp kiểm tra-hoàn thiện vòng 2, 2026-07-21):

1. [HIGH] RISK_PROFILES trong tools/run_g2_auto.py trước đây thiếu 2 khóa
   "prediction" và "qualitative" — get_risk_profile() coi 2 mã thiết kế hợp
   lệ này là "không nhận diện được" và fallback về hồ sơ rủi ro "rct" (AE/
   SAE, DSMB/DMC giám sát, lấy mẫu máu bổ sung — nội dung sai bản chất cho
   2 thiết kế không có can thiệp thuốc thử nghiệm nào).

2. [MEDIUM] TÀI LIỆU 9 (Đề nghị miễn ICF) chỉ kích hoạt khi
   `risk["icf_waiver_eligible"] and design_code == "sr_ma"` — vế thiết kế
   khóa cứng khiến cờ icf_waiver_eligible=True của cross_sectional (đã có
   từ trước) và nay cả prediction trở thành dead value, không bao giờ sinh
   artifact dù hệ thống tự đánh giá đủ điều kiện.
"""
from __future__ import annotations

import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

from run_g2_auto import RISK_PROFILES, generate_g2_full_package, get_risk_profile  # noqa: E402


def _gen(design_code, design_primary="Thiết kế test"):
    risk = RISK_PROFILES[design_code]
    return generate_g2_full_package(
        topic="Đề tài test", study_name="TEST-STUDY", design_code=design_code,
        design_primary=design_primary, reporting_std="STROBE", n_sr=5, n_rct=0,
        evidence_level="TRUNG BÌNH", registry=None, risk=risk,
        run_date="2026-07-21", n_adjusted=1000,
    )


class TestPredictionAndQualitativeHaveOwnRiskProfile:
    def test_prediction_is_a_recognized_design_code(self):
        assert get_risk_profile("prediction", "Mô hình tiên lượng tử vong").get("_fallback_warning") is None

    def test_qualitative_is_a_recognized_design_code(self):
        assert get_risk_profile("qualitative", "Phỏng vấn sâu rào cản tuân thủ").get("_fallback_warning") is None

    def test_prediction_risk_profile_does_not_mention_rct_adverse_events(self):
        """Không hồi quy về hồ sơ 'rct' (AE/SAE/DSMB) — sai bản chất cho mô
        hình tiên lượng không có can thiệp thuốc thử nghiệm."""
        risk = RISK_PROFILES["prediction"]
        risk_names = " ".join(r[0] for r in risk["risks"])
        assert "thuốc thử nghiệm" not in risk_names
        assert "DSMB" not in risk_names

    def test_qualitative_risk_profile_does_not_mention_rct_adverse_events(self):
        risk = RISK_PROFILES["qualitative"]
        risk_names = " ".join(r[0] for r in risk["risks"])
        assert "thuốc thử nghiệm" not in risk_names
        assert "DSMB" not in risk_names

    def test_prediction_full_package_generates_without_crash(self):
        doc = _gen("prediction")
        assert "TÀI LIỆU 4" in doc
        assert "PHIẾU ĐỒNG Ý THAM GIA NGHIÊN CỨU" in doc

    def test_qualitative_full_package_generates_without_crash(self):
        doc = _gen("qualitative")
        assert "TÀI LIỆU 4" in doc
        assert "PHIẾU ĐỒNG Ý THAM GIA NGHIÊN CỨU" in doc


class TestIcfWaiverActivatesForAnyEligibleDesignNotJustSrMa:
    def test_cross_sectional_now_gets_icf_waiver_document(self):
        """Trước bản vá: cross_sectional có icf_waiver_eligible=True nhưng
        KHÔNG BAO GIỜ nhận TÀI LIỆU 9 vì điều kiện khóa cứng 'sr_ma'."""
        assert RISK_PROFILES["cross_sectional"]["icf_waiver_eligible"] is True
        doc = _gen("cross_sectional")
        assert "TÀI LIỆU 9" in doc
        assert "ĐỀ NGHỊ MIỄN ICF" in doc

    def test_prediction_gets_icf_waiver_document(self):
        assert RISK_PROFILES["prediction"]["icf_waiver_eligible"] is True
        doc = _gen("prediction")
        assert "TÀI LIỆU 9" in doc

    def test_sr_ma_still_gets_icf_waiver_document_with_srma_specific_wording(self):
        doc = _gen("sr_ma")
        assert "TÀI LIỆU 9" in doc
        assert "SR/MA dùng dữ liệu đã công bố" in doc

    def test_cross_sectional_waiver_does_not_falsely_claim_srma_published_data(self):
        """Nội dung mẫu đơn phải khớp bản chất thiết kế — không giả định sai
        rằng cross_sectional dùng 'dữ liệu đã công bố trong y văn' như SR/MA."""
        doc = _gen("cross_sectional")
        waiver_block = doc.split("TÀI LIỆU 9")[1]
        assert "SR/MA dùng dữ liệu đã công bố" not in waiver_block

    def test_qualitative_has_no_icf_waiver_document(self):
        """Không hồi quy ngược: qualitative vẫn KHÔNG đủ điều kiện miễn ICF
        (icf_waiver_eligible=False) — phỏng vấn luôn cần đồng thuận đầy đủ."""
        assert RISK_PROFILES["qualitative"]["icf_waiver_eligible"] is False
        doc = _gen("qualitative")
        assert "TÀI LIỆU 9" not in doc

    def test_rct_and_cohort_still_have_no_icf_waiver_document(self):
        for code in ("rct", "cohort", "case_control", "diagnostic"):
            assert RISK_PROFILES[code]["icf_waiver_eligible"] is False
            assert "TÀI LIỆU 9" not in _gen(code)
