"""Hồi quy 2 phát hiện của Workflow đối kháng đa-agent 2026-09-05 (vòng 10,
task #95) trong `app/scoring/evidence_quality.py`/`operational_level.py`.

═══ Phát hiện #2 (HIGH) — study_type không xác định điểm CAO HƠN thiết kế
đã biết là YẾU ═══
`DESIGN_BASE.get(study_type, 40)` — mặc định 40 CAO HƠN 6 thiết kế đã đặt
tên và tự khai YẾU (case_series/narrative_review=25, expert_opinion=20,
editorial=15, preprint=10, animal_invitro=5). `app/sources/classify_meta.py`
tự khai ý định: "Khi không đủ tín hiệu -> trả None để pipeline xử lý THẬN
TRỌNG (điểm THẤP)" — mặc định 40 làm NGƯỢC LẠI, thưởng việc không xác định
được thiết kế hơn là phạt việc thành thật khai yếu.
BẢN VÁ: mặc định đưa về 0 — thấp hơn MỌI thiết kế đã đặt tên.

═══ Phát hiện #3 (HIGH) — thứ tự kiểm chuỗi con đảo ngược mức GRADE ═══
`operational_evidence_level()` kiểm "high" TRƯỚC "moderate"/"low" trên văn
bản tự do (`official_grade`). Một câu như "Downgraded from high to low"
hay "High risk of bias, low certainty" đều CHỨA chữ "high" nên bị báo
"High" dù kết luận thật của câu là "low" — đảo ngược mức tin cậy hiển thị
cho bác sĩ NHƯ THỂ đó là phân hạng CHÍNH THỨC (is_official=True).
BẢN VÁ: đảo thứ tự kiểm THẤP -> TRUNG BÌNH -> CAO (thận trọng nhất trước).

Nguyên tắc viết test: gọi THẲNG `evidence_quality_score()`/`reliability_
tier()`/`operational_evidence_level()` thật.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.scoring import evidence_quality_score  # noqa: E402
from app.scoring.operational_level import operational_evidence_level  # noqa: E402

_BASE_TEXT = {"title": "A study on cardiovascular outcomes",
              "abstract": "mortality reduction observed"}


class TestStudyTypeKhongXacDinhKhongDuocDiemCaoHonThietKeYeu:
    """★★★ Ca chính — study_type=None phải điểm THẤP HƠN mọi thiết kế đã
    đặt tên là yếu (case_series/editorial/preprint/animal_invitro)."""

    def test_none_thap_hon_case_series(self):
        eq_none, _ = evidence_quality_score(dict(_BASE_TEXT, study_type=None))
        eq_case, _ = evidence_quality_score(dict(_BASE_TEXT, study_type="case_series"))
        assert eq_none < eq_case

    def test_none_thap_hon_ca_animal_invitro(self):
        """animal_invitro=5 là thiết kế điểm THẤP NHẤT đã đặt tên — study_type
        không xác định phải <= mức này, không được vượt qua."""
        eq_none, _ = evidence_quality_score(dict(_BASE_TEXT, study_type=None))
        eq_animal, _ = evidence_quality_score(dict(_BASE_TEXT, study_type="animal_invitro"))
        assert eq_none <= eq_animal

    def test_chuoi_rong_cung_khong_duoc_diem_cao(self):
        eq_empty, _ = evidence_quality_score(dict(_BASE_TEXT, study_type=""))
        eq_case, _ = evidence_quality_score(dict(_BASE_TEXT, study_type="case_series"))
        assert eq_empty < eq_case


class TestThietKeDaBietVanGiuThuBacDungNhuCu:
    """Đối chứng bắt buộc — thứ bậc điểm giữa các thiết kế ĐÃ ĐẶT TÊN không
    đổi (guideline > rct > cohort > case_series > preprint), bản vá chỉ
    đụng tới NHÁNH MẶC ĐỊNH, không đụng bảng DESIGN_BASE."""

    def test_guideline_van_cao_nhat(self):
        eq_guideline, _ = evidence_quality_score(dict(_BASE_TEXT, study_type="guideline"))
        eq_rct, _ = evidence_quality_score(dict(_BASE_TEXT, study_type="rct"))
        assert eq_guideline > eq_rct

    def test_editorial_van_thap_hon_case_series(self):
        eq_editorial, _ = evidence_quality_score(dict(_BASE_TEXT, study_type="editorial"))
        eq_case, _ = evidence_quality_score(dict(_BASE_TEXT, study_type="case_series"))
        assert eq_editorial < eq_case


class TestKhongXacDinhThietKeVanCoTheDatTierCaoHonNeuCoTinHieuThatManh:
    """Đối chứng bắt buộc — bản vá KHÔNG cấm tuyệt đối; nếu văn bản có tín
    hiệu thật mạnh (đa trung tâm, outcome cứng, nguồn uy tín), study_type
    không xác định vẫn cộng điểm bình thường từ các tín hiệu đó, không bị
    khoá cứng ở 0."""

    def test_tin_hieu_manh_van_cong_diem_du_khong_xac_dinh_thiet_ke(self):
        item = {"title": "Multicenter international trial",
                "abstract": "clinical outcome mortality reduction, n=2000 patients",
                "study_type": None}
        eq, breakdown = evidence_quality_score(item)
        assert breakdown["base_design"] == 0.0
        assert eq > 0  # vẫn cộng được multicenter/hard_outcome/large_sample


class TestGradeVanBiChanNguocKhiVanBanTuDoNhacCaHaiMuc:
    """★★★ Ca chính — official_grade là chuỗi tự do nhắc CẢ "high" LẪN
    "low"/"moderate" phải báo đúng mức THẤP HƠN (kết luận thật), không phải
    mức "high" xuất hiện tình cờ trước đó trong câu."""

    def test_downgraded_tu_high_xuong_low_bao_dung_low(self):
        level, is_official = operational_evidence_level(
            {"official_grade": "Downgraded from high to low"}, 50)
        assert level == "Low"
        assert is_official is True

    def test_high_risk_of_bias_low_certainty_bao_dung_low(self):
        level, is_official = operational_evidence_level(
            {"official_grade": "High risk of bias, low certainty"}, 50)
        assert level == "Low"
        assert is_official is True

    def test_moderate_to_high_bao_muc_than_trong_hon_la_moderate(self):
        level, is_official = operational_evidence_level(
            {"official_grade": "Moderate to high certainty"}, 50)
        assert level == "Moderate"


class TestGradeDonGianVanHoatDongNhuCu:
    """Đối chứng bắt buộc — official_grade chỉ nhắc ĐÚNG MỘT mức (không mơ
    hồ) vẫn báo đúng mức đó như hành vi gốc."""

    def test_high_don_gian_van_bao_high(self):
        level, is_official = operational_evidence_level({"official_grade": "High"}, 50)
        assert level == "High"
        assert is_official is True

    def test_moderate_don_gian_van_bao_moderate(self):
        level, is_official = operational_evidence_level({"official_grade": "Moderate"}, 50)
        assert level == "Moderate"

    def test_very_low_van_bao_low(self):
        level, is_official = operational_evidence_level({"official_grade": "Very low"}, 50)
        assert level == "Low"

    def test_khong_co_official_grade_van_dung_uoc_luong_van_hanh(self):
        level, is_official = operational_evidence_level({}, 80)
        assert is_official is False
        assert "High" in level
