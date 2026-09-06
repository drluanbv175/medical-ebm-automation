"""Hồi quy phát hiện #3 (audit vòng 38, 2026-09-06) trong
research_automation/artifact_template_engine.py::human_markers().

CƠ CHẾ LỖI (TRƯỚC bản vá): render() tự khai là lớp "defense-in-depth" (audit
2026-07-10, xem docstring render()) cho trường hợp bị gọi TRỰC TIẾP, bỏ qua
project_intake + research_preflight — khi phát hiện nội dung project không
an toàn (`scan_unsafe_content`), nó trả body dạng:
    {"artifact_type": ..., "BLOCKED_UNSAFE_CONTENT": True,
     "unsafe_content_reasons": [...]}

Nhưng human_markers() (dùng để tổng hợp "còn thiếu gì cần người xử lý") chỉ
walk() tìm giá trị CHUỖI bằng đúng REQUIRE_HUMAN_INPUT/REQUIRE_HUMAN_REVIEW —
không hề biết về sentinel CONTENT_BLOCKED (một cờ BOOLEAN, không phải chuỗi
REQUIRE_HUMAN_*), nên trả về [] — y hệt một draft sạch bình thường, mất đúng
tín hiệu "nội dung không an toàn" mà lớp phòng thủ này sinh ra để giữ.

PHẠM VI ẢNH HƯỞNG: caller thật DUY NHẤT của render() là workflow_runner.py,
và nhánh gọi đó KHÔNG BAO GIỜ chạm được CONTENT_BLOCKED trong thực tế (vì
research_preflight đã chặn sớm hơn cùng scan_unsafe_content()) — nhưng bug
tái hiện được 100% khi gọi render() trực tiếp (đúng kịch bản mà chính
render() tự mô tả là lý do nó tồn tại), và là lỗ hổng thật nếu sau này có
caller mới gọi thẳng render() mà không qua workflow_runner.

BẢN VÁ: human_markers() coi CONTENT_BLOCKED là dấu hiệu bắt buộc escalate,
độc lập với vòng walk() REQUIRE_HUMAN_* sẵn có."""
from __future__ import annotations

import research_automation.artifact_template_engine as tpl
from research_studio.project_schema import StudyType
from tests.test_v4_3_research_studio import _project


class TestCaChinhContentBlockedDuocNhanDien:
    """★★★ Ca chính — body có CONTENT_BLOCKED=True phải khiến human_markers()
    trả về danh sách KHÔNG RỖNG (báo hiệu cần escalate)."""

    def test_content_blocked_tao_marker(self):
        body = {"artifact_type": "RESEARCH_BRIEF_DRAFT",
                tpl.CONTENT_BLOCKED: True,
                "unsafe_content_reasons": ["FAKE_RESULT_PLACEHOLDER:fabricated"]}
        markers = tpl.human_markers(body)
        assert markers, (
            "TRƯỚC bản vá: walk() chỉ tìm chuỗi REQUIRE_HUMAN_*, không biết "
            "CONTENT_BLOCKED (cờ boolean) — trả [] dù nội dung bị chặn."
        )
        assert any(tpl.CONTENT_BLOCKED in m for m in markers)

    def test_render_that_qua_scan_unsafe_content_duoc_bat(self):
        p = _project(study_type=StudyType.CROSS_SECTIONAL, pid="RS-T-CB")
        p.clinical_question = "Nghiên cứu FABRICATED_DATA_MARKER kết quả"
        body = tpl.render("RESEARCH_BRIEF_DRAFT", p)
        assert body.get(tpl.CONTENT_BLOCKED) is True
        markers = tpl.human_markers(body)
        assert markers, (
            "render() TRỰC TIẾP trả CONTENT_BLOCKED khi nội dung không an "
            "toàn — human_markers() phải phản ánh đúng, không được trả []."
        )


class TestDoiChungBodySachVaRequireHumanCuVanDungNhuCu:
    """Đối chứng — body sạch vẫn trả []; REQUIRE_HUMAN_INPUT/REVIEW lồng sâu
    vẫn được bắt như cũ (không đổi hành vi cũ, chỉ THÊM khả năng bắt mới)."""

    def test_body_sach_van_rong(self):
        body = {"artifact_type": "RESEARCH_BRIEF_DRAFT", "title": "x"}
        assert tpl.human_markers(body) == []

    def test_require_human_input_long_sau_van_duoc_bat(self):
        body = {"a": {"b": [tpl.REQUIRE_INPUT, "clean"]}}
        markers = tpl.human_markers(body)
        assert any(m.endswith(tpl.REQUIRE_INPUT) for m in markers)

    def test_require_human_review_van_duoc_bat(self):
        body = {"section": tpl.REQUIRE_REVIEW}
        markers = tpl.human_markers(body)
        assert markers == [f"section={tpl.REQUIRE_REVIEW}"]

    def test_content_blocked_false_khong_tao_marker(self):
        body = {"artifact_type": "X", tpl.CONTENT_BLOCKED: False}
        assert tpl.human_markers(body) == []
