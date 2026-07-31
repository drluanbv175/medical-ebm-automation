"""Hồi quy audit tautology vòng 2 (2026-07-31): guardrail_check_g0() rule R4
(tự gán GRADE) và R5 (trộn trục khuyến cáo lâm sàng) trước bản vá là
REVERSE-TAUTOLOGY thật — không phải chỉ thiếu honest comment, mà THẬT SỰ
chặn oan các đề tài hợp lệ:

- R4: regex cũ `grade\\s+[a-d]\\b` khớp bất kỳ đâu, kể cả khi cụm đó là một
  phần TOPIC không liên quan gì tới khung GRADE chứng cứ (vd phân độ mô học
  khối u, Los Angeles Classification viêm thực quản trào ngược Grade A-D).
- R5: regex cũ khớp "nên dùng/chỉ định/điều trị" bất kể câu đó là CÂU HỎI
  NGHIÊN CỨU dạng PICO ("có nên...không?") hay CHỈ THỊ LÂM SÀNG khẳng định —
  chặn oan đúng loại câu hỏi mà G0 được thiết kế để phục vụ.

File này kiểm TRỰC TIẾP guardrail_check_g0() thật (không mock), với các case
false-positive (không được chặn) và true-positive (phải chặn) mà bản vá này
phải phân biệt đúng."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import run_g0_auto as G0  # noqa: E402

_RESULTS = {"sr": [], "rct": [], "guideline": [], "observational": []}


def _r_errors(text: str, rule: str) -> list[str]:
    report = G0.guardrail_check_g0(text, _RESULTS)
    return [e for e in report["errors"] if e.startswith(rule)]


class TestR4GradeContextWindow:
    def test_grade_a_in_unrelated_tumor_grading_topic_not_blocked(self):
        text = "Đề tài: Đánh giá Grade A của độ ác tính u gan theo phân loại WHO."
        assert _r_errors(text, "R4") == []

    def test_los_angeles_classification_grade_c_not_blocked(self):
        text = (
            "Chẩn đoán La Grade C viêm thực quản trào ngược theo Los Angeles "
            "Classification."
        )
        assert _r_errors(text, "R4") == []

    def test_real_self_assigned_grade_of_evidence_still_blocked(self):
        text = "Chất lượng chứng cứ của can thiệp X là grade a theo GRADE."
        assert _r_errors(text, "R4") != []

    def test_real_strength_of_recommendation_grade_still_blocked(self):
        text = "Mức khuyến cáo grade b cho điều trị Y."
        assert _r_errors(text, "R4") != []


class TestR5SentenceBoundaryQuestionVsDirective:
    def test_pico_question_ending_khong_not_blocked(self):
        text = "Nên dùng statin cho bệnh nhân đái tháo đường không."
        assert _r_errors(text, "R5") == []

    def test_co_nen_question_form_not_blocked(self):
        text = "Có nên chỉ định thuốc X cho bệnh nhân suy thận không."
        assert _r_errors(text, "R5") == []

    def test_question_mark_form_not_blocked(self):
        text = "Nên điều trị bằng phác đồ X cho bệnh nhân Y trong bao lâu?"
        assert _r_errors(text, "R5") == []

    def test_declarative_clinical_directive_still_blocked(self):
        text = "Bác sĩ nên kê đơn 500mg thuốc X ngay cho bệnh nhân tại phòng khám."
        assert _r_errors(text, "R5") != []

    def test_declarative_recommendation_still_blocked(self):
        text = "Khuyến cáo dùng thuốc X cho mọi bệnh nhân từ hôm nay."
        assert _r_errors(text, "R5") != []
