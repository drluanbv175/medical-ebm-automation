"""Test cho phần mở rộng meta-driven của G10 assembler — thêm 2026-07-17.

Trước đây `sec_muctieu` (Mục 4 — Mục tiêu) ĐÃ đọc meta.get("aim")/"objectives"
khi bác sĩ cung cấp, nhưng `sec_cauhoi` (Mục 3), `sec_doituong` (Mục 6),
`sec_congcu` (Mục 9) và phần "Cỡ mẫu thực tế" ở `sec_comau`/`sec_tomtat`
LUÔN hard-code [CẦN BỔ SUNG] bất kể meta — tài liệu lắp ráp tự mâu thuẫn nội
bộ (vd ma trận truy xuất đã dùng meta["research_question"] nhưng Mục 3 vẫn
trống). Phát hiện khi bác sĩ phàn nàn đề cương thật (hài lòng bệnh nhân C1a,
BVQY175) "không đảm bảo của một đề cương nghiên cứu" — quá nhiều placeholder
dù thông tin đã có sẵn. Test này khóa: có meta → hiển thị thật; KHÔNG có meta
→ giữ nguyên placeholder cũ (không hồi quy các đề tài chưa cung cấp meta).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import run_g10_assemble as G10  # noqa: E402

TESTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS_DIR))
from test_g10_assemble import _write_cross_sectional_fixture  # noqa: E402


def _write_meta(d: Path, meta: dict) -> None:
    (d / "study_meta.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8", newline="\n")


@pytest.fixture
def cross_sectional_study(tmp_path):
    _write_cross_sectional_fixture(tmp_path)
    return tmp_path


class TestCauHoiMetaDriven:
    def test_placeholder_when_meta_absent(self, cross_sectional_study):
        res = G10.assemble("FIXT", cross_sectional_study)
        text = res["md"].read_text(encoding="utf-8")
        assert "**Câu hỏi PICO/PECO:** [CẦN BỔ SUNG]" in text
        assert "**Giả thuyết:** [CẦN BỔ SUNG]" in text

    def test_research_question_and_pico_rendered_when_provided(self, cross_sectional_study):
        _write_meta(cross_sectional_study, {
            "research_question": "Mức độ hài lòng của người bệnh tại Khoa C1a là bao nhiêu?",
            "pico": {"p": "Người bệnh ngoại trú tại C1a", "i_e": "Trải nghiệm khám chữa bệnh",
                     "c": "Không có nhóm so sánh (mô tả)", "o": "Điểm hài lòng theo thang đã chọn"},
            "hypothesis": "Nghiên cứu mô tả — không kiểm định giả thuyết chính thức.",
        })
        res = G10.assemble("FIXT", cross_sectional_study)
        text = res["md"].read_text(encoding="utf-8")
        assert "Mức độ hài lòng của người bệnh tại Khoa C1a là bao nhiêu?" in text
        assert "Người bệnh ngoại trú tại C1a" in text
        assert "Điểm hài lòng theo thang đã chọn" in text
        # SỬA 2026-07-17: KHÔNG gắn cứng [ĐÃ CUNG CẤP] cho nội dung trong
        # study_meta.json — assembler không thể biết nội dung đó do bác sĩ tự
        # gõ hay do agent soạn hộ; gắn nhãn "đã cung cấp" cho nội dung AI soạn
        # là quy sai nguồn gốc (vi phạm bảng "Phân biệt nguồn thông tin" của
        # chính tài liệu). Thay vào đó: MỘT dòng cảnh báo [DỰ THẢO] chung cho
        # cả khối, đúng thực chất.
        assert "nội dung dưới đây do hệ thống/agent soạn" in text
        assert "bác sĩ/chủ nhiệm PHẢI xác nhận" in text

    def test_pico_missing_key_falls_back_to_placeholder_per_field(self, cross_sectional_study):
        _write_meta(cross_sectional_study, {"pico": {"p": "Người bệnh ngoại trú"}})
        res = G10.assemble("FIXT", cross_sectional_study)
        text = res["md"].read_text(encoding="utf-8")
        assert "Người bệnh ngoại trú" in text
        assert "[CẦN BỔ SUNG]" in text  # các trường I/E, C, O còn thiếu


class TestDoiTuongMetaDriven:
    def test_placeholder_when_meta_absent(self, cross_sectional_study):
        res = G10.assemble("FIXT", cross_sectional_study)
        text = res["md"].read_text(encoding="utf-8")
        # Tiểu mục lấy qua canon (06/09/2026: "6.1." → "7.1." khi khuôn lên 18 mục).
        sub = G10.S.de_cuong_sub_heading("doituong", 0)
        assert sub.endswith("Tiêu chuẩn chọn")
        assert f"{sub}\n\n[CẦN BỔ SUNG]" in text

    def test_inclusion_exclusion_rendered_when_provided(self, cross_sectional_study):
        _write_meta(cross_sectional_study, {
            "inclusion_criteria": ["Người bệnh ≥18 tuổi đến khám tại C1a", "Đồng ý tham gia"],
            "exclusion_criteria": ["Không đủ khả năng trả lời phiếu (rối loạn nhận thức nặng)"],
            "sampling_method": "Chọn mẫu thuận tiện liên tiếp trong thời gian nghiên cứu.",
        })
        res = G10.assemble("FIXT", cross_sectional_study)
        text = res["md"].read_text(encoding="utf-8")
        assert "Người bệnh ≥18 tuổi đến khám tại C1a" in text
        assert "Không đủ khả năng trả lời phiếu" in text
        assert "Chọn mẫu thuận tiện liên tiếp" in text
        assert "nội dung dưới đây do hệ thống/agent soạn" in text


class TestCongCuMetaDriven:
    def test_placeholder_when_meta_absent(self, cross_sectional_study):
        res = G10.assemble("FIXT", cross_sectional_study)
        text = res["md"].read_text(encoding="utf-8")
        assert "**Công cụ đo lường:** [CẦN BỔ SUNG]" in text

    def test_instrument_rendered_when_provided(self, cross_sectional_study):
        _write_meta(cross_sectional_study, {
            "instrument": {
                "name": "Bộ phiếu khảo sát hài lòng người bệnh ngoại trú",
                "source": "Bộ Y tế (QĐ 3869/QĐ-BYT 2019)",
                "note": "[CẦN KIỂM CHỨNG NGUỒN CHÍNH THỨC] — bác sĩ đối chiếu bản gốc trước khi dùng.",
            }
        })
        res = G10.assemble("FIXT", cross_sectional_study)
        text = res["md"].read_text(encoding="utf-8")
        assert "Bộ phiếu khảo sát hài lòng người bệnh ngoại trú" in text
        assert "QĐ 3869/QĐ-BYT 2019" in text
        assert "[CẦN KIỂM CHỨNG NGUỒN CHÍNH THỨC]" in text
        assert "nội dung dưới đây do hệ thống/agent soạn" in text


class TestConfirmedNSurfacedInAssembledDoc:
    """G3 --confirmed-n phải hiện trong tài liệu lắp ráp cuối, không chỉ artifact G3 riêng lẻ."""

    def test_no_confirmed_n_unchanged_output(self, cross_sectional_study):
        res = G10.assemble("FIXT", cross_sectional_study)
        text = res["md"].read_text(encoding="utf-8")
        assert "N thực tế đã chốt" not in text
        assert "**Cỡ mẫu dự kiến:** 428 đối tượng." in text

    def test_confirmed_n_adequate_surfaced(self, cross_sectional_study):
        cp_path = cross_sectional_study / "G3_checkpoint.json"
        cp = json.loads(cp_path.read_text(encoding="utf-8"))
        cp["confirmed_n"] = 1000
        cp["confirmed_n_adequate"] = True
        cp_path.write_text(json.dumps(cp, ensure_ascii=False), encoding="utf-8", newline="\n")

        res = G10.assemble("FIXT", cross_sectional_study)
        text = res["md"].read_text(encoding="utf-8")
        assert "N thực tế đã chốt" in text
        assert "1000" in text
        assert "ĐẠT" in text
        assert "**Cỡ mẫu dự kiến:** 1000 đối tượng" in text

    def test_confirmed_n_inadequate_surfaces_warning(self, cross_sectional_study):
        cp_path = cross_sectional_study / "G3_checkpoint.json"
        cp = json.loads(cp_path.read_text(encoding="utf-8"))
        cp["confirmed_n"] = 50
        cp["confirmed_n_adequate"] = False
        cp_path.write_text(json.dumps(cp, ensure_ascii=False), encoding="utf-8", newline="\n")

        res = G10.assemble("FIXT", cross_sectional_study)
        text = res["md"].read_text(encoding="utf-8")
        assert "CẢNH BÁO" in text
        assert "underpowered" in text.lower()
