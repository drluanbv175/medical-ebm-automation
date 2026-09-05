"""Hồi quy phát hiện #4 (Medium) của Workflow đối kháng đa-agent 2026-09-05
(vòng 19) trong app/scoring/practice_change.py và app/scoring/reliability.py.

CƠ CHẾ LỖI: app.scoring.evidence_quality.DESIGN_BASE xếp
"expert_opinion"=20 THẤP HƠN "case_series"=25/"narrative_review"=25 (đúng
thứ bậc GRADE — ý kiến chuyên gia yếu hơn case series) — nhưng HAI danh
sách quyết định điểm/tier khác lại KHÔNG khớp thứ bậc đó:
  (a) practice_change.py::weak_design_penalty trừ -25 cho case_series
      nhưng KHÔNG trừ cho expert_opinion -> cùng điều kiện, expert_opinion
      giữ nguyên practice_change_score cao hơn case_series dù DESIGN_BASE
      xếp nó YẾU HƠN.
  (b) reliability.py::EXCLUDED_DESIGNS chặn Tier D cho editorial/
      narrative_review/preprint/animal_invitro nhưng KHÔNG chặn
      expert_opinion -> một bản ghi expert_opinion có thể đạt Tier B/C
      thay vì bị chặn D như các thiết kế yếu cùng nhóm.
Kết quả: expert_opinion — thiết kế được chính DESIGN_BASE của module SÂU
NHẤT xếp là yếu — lại được HAI tầng downstream (điểm + tier) đối xử NHẸ
TAY hơn case_series/narrative_review, đảo ngược đúng thứ bậc mà
DESIGN_BASE đã thiết lập.

BẢN VÁ: thêm "expert_opinion" vào weak_design_penalty (practice_change.py)
và vào EXCLUDED_DESIGNS (reliability.py), khớp đúng DESIGN_BASE.

Nguyên tắc viết test: gọi THẲNG practice_change_score()/reliability_tier()
thật và đối chiếu trực tiếp với EXCLUDED_DESIGNS thật."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.scoring.evidence_quality import DESIGN_BASE  # noqa: E402
from app.scoring.practice_change import practice_change_score  # noqa: E402
from app.scoring.reliability import EXCLUDED_DESIGNS, reliability_tier  # noqa: E402


class TestExpertOpinionBiPhatDungNhuCaseSeries:
    """★★★ Ca chính — expert_opinion (DESIGN_BASE=20, YẾU HƠN case_series=25)
    phải bị phạt weak_design_penalty giống case_series, không được giữ
    nguyên other_base cao hơn."""

    def test_expert_opinion_bi_tru_diem_weak_design_penalty(self):
        _, breakdown = practice_change_score({"study_type": "expert_opinion",
                                                "title": "x", "abstract": "x"})
        assert breakdown.get("weak_design_penalty") == -25, (
            "TRƯỚC bản vá: expert_opinion KHÔNG nằm trong tuple phạt của "
            "practice_change.py, dù DESIGN_BASE xếp nó yếu hơn case_series "
            "(vốn CÓ bị phạt) — đảo ngược thứ bậc"
        )

    def test_expert_opinion_khong_con_diem_cao_hon_case_series(self):
        pc_eo, _ = practice_change_score({"study_type": "expert_opinion",
                                           "title": "x", "abstract": "x"})
        pc_cs, _ = practice_change_score({"study_type": "case_series",
                                           "title": "x", "abstract": "x"})
        # DESIGN_BASE xếp expert_opinion(20) < case_series(25) -> practice_
        # change_score không được để expert_opinion CAO HƠN case_series.
        assert pc_eo <= pc_cs

    def test_expert_opinion_nam_trong_excluded_designs(self):
        assert "expert_opinion" in EXCLUDED_DESIGNS, (
            "TRƯỚC bản vá: expert_opinion thiếu trong EXCLUDED_DESIGNS của "
            "reliability.py dù editorial/narrative_review (cùng nhóm chứng "
            "cứ yếu trong DESIGN_BASE) đều bị chặn Tier D"
        )

    def test_expert_opinion_bi_chan_tier_d(self):
        # Ngay cả khi evidence_q/practice_c cao (giả lập tín hiệu mạnh),
        # EXCLUDED_DESIGNS phải chặn CỨNG về D trước khi xét ngưỡng A/B.
        tier = reliability_tier({"study_type": "expert_opinion"}, 90, 90)
        assert tier == "D"


class TestThuBacDesignBaseKhongDoi:
    """Đối chứng bắt buộc — bản vá không đụng tới DESIGN_BASE (nguồn chân
    lý cho thứ bậc thiết kế); expert_opinion vẫn đúng vị trí 20, thấp hơn
    case_series/narrative_review (25) và cao hơn editorial (15)."""

    def test_design_base_thu_bac_khong_doi(self):
        assert DESIGN_BASE["expert_opinion"] == 20
        assert DESIGN_BASE["case_series"] == 25
        assert DESIGN_BASE["editorial"] == 15
        assert DESIGN_BASE["expert_opinion"] < DESIGN_BASE["case_series"]
        assert DESIGN_BASE["expert_opinion"] > DESIGN_BASE["editorial"]


class TestCacThietKeManhKhongBiDungCham:
    """Đối chứng bắt buộc — bản vá chỉ thêm expert_opinion, không đụng tới
    các thiết kế mạnh (rct/guideline/systematic_review) hay các thiết kế
    yếu ĐÃ bị chặn từ trước (editorial/preprint/animal_invitro/
    narrative_review)."""

    def test_rct_khong_bi_phat(self):
        _, breakdown = practice_change_score({"study_type": "rct",
                                                "title": "x", "abstract": "x"})
        assert "weak_design_penalty" not in breakdown

    def test_guideline_khong_bi_chan_tier_d(self):
        tier = reliability_tier(
            {"study_type": "guideline"}, 90,
            practice_change_score({"study_type": "guideline",
                                    "title": "recommend mortality outcome multicenter",
                                    "abstract": "x"})[0])
        assert tier != "D"

    def test_cac_thiet_ke_yeu_cu_van_bi_chan_d(self):
        for st in ("preprint", "animal_invitro", "editorial", "narrative_review"):
            assert reliability_tier({"study_type": st}, 90, 90) == "D"

    def test_cac_thiet_ke_yeu_cu_van_bi_phat_diem(self):
        for st in ("preprint", "animal_invitro", "case_series",
                   "retrospective_single_center", "narrative_review", "editorial"):
            _, breakdown = practice_change_score(
                {"study_type": st, "title": "x", "abstract": "x"})
            assert breakdown.get("weak_design_penalty") == -25
