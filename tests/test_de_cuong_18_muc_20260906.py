"""Hồi quy cho việc nâng khuôn đề cương 16 → 18 mục và 20 → 23 thành phần (06/09/2026).

Vì sao có: đo trên đề tài thật C1a, khuôn 16 mục không có chương Tổng quan tài liệu,
khung lý thuyết và Dự kiến kết quả/khung bảng trống — ba thứ hội đồng trong nước và
SPIRIT 2025 "Background and rationale" đều đòi. Bản đề cương viết tay của C1a có đủ,
bản G10 lắp ráp thì không ⇒ hai bản "sống" song song. Đợt nâng này đổi MỘT canon
(skill_standards) và buộc mọi nơi tiêu thụ lấy số mục qua helper.

Ba luật khi thêm ca thử (theo chot_hoi_quy_bai_hoc.py):
  (1) kiểm HÀNH VI bằng cách gọi mã đang sống (assemble → validate), không đếm chuỗi;
  (2) mỗi ca gắn với một rủi ro THẬT: số mục viết cứng lệch canon · thiếu mục mới ·
      ma trận thiếu P21–P23 · template 01 lệch canon · R1 không còn răng;
  (3) nhanh và ngoại tuyến (fixture G0–G9 dựng tay, không gọi mạng).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import check_de_cuong  # noqa: E402
import research_study_spec as RS  # noqa: E402
import run_g10_assemble as G10  # noqa: E402
import skill_standards as S  # noqa: E402

TESTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS_DIR))
from test_g10_assemble import _write_cross_sectional_fixture  # noqa: E402

_H1_RE = re.compile(r"^# (\d+)\. (.+?)\s*$", re.MULTILINE)


@pytest.fixture
def study_dir(tmp_path):
    _write_cross_sectional_fixture(tmp_path)
    return tmp_path


def _numbered_h1(text: str) -> list[tuple[str, str]]:
    return [(m.group(1), m.group(2)) for m in _H1_RE.finditer(text)]


class TestAssembledHeadingsFollowCanon:
    def test_h1_sequence_equals_canon_exactly(self, study_dir):
        """Bắt lỗi builder viết cứng số mục: dãy '# N. Tiêu đề' trong đề cương lắp ráp
        phải TRÙNG KHỚP thứ tự + số + tiêu đề của DE_CUONG_SECTIONS (không thừa số nào)."""
        res = G10.assemble("FIXT", study_dir)
        text = res["md"].read_text(encoding="utf-8")
        got = _numbered_h1(text)
        want = [(num, title) for num, title, _ in S.DE_CUONG_SECTIONS]
        assert got == want, f"\nĐƯỢC : {got}\nCẦN  : {want}"

    def test_new_sections_have_content_not_only_heading(self, study_dir):
        res = G10.assemble("FIXT", study_dir)
        text = res["md"].read_text(encoding="utf-8")
        assert "Khung lý thuyết / mô hình khái niệm" in text
        assert "Khung bảng trống theo ma trận" in text
        # Mục 13 phải nhắc luật R6 (không số liệu) — đó là lý do mục này tồn tại.
        assert "R6" in text.split("# 13. ")[1].split("# 14. ")[0]

    def test_sub_headings_follow_parent_numbers(self, study_dir):
        res = G10.assemble("FIXT", study_dir)
        text = res["md"].read_text(encoding="utf-8")
        for _num, _title, subs in S.DE_CUONG_SECTIONS:
            for sub in subs:
                assert f"## {sub}" in text, f"thiếu tiểu mục '## {sub}'"
        # Không còn tiểu mục mang số cũ (4.x / 6.x) sót lại từ khuôn 16 mục.
        assert not re.search(r"^## [46]\.\d\. ", text, re.MULTILINE)


class TestCoverageMatrixAndValidator:
    def test_matrix_lists_every_core_item_including_p21_p23(self, study_dir):
        res = G10.assemble("FIXT", study_dir)
        text = res["md"].read_text(encoding="utf-8")
        n = len(S.PROTOCOL_CORE_ITEMS)
        assert f"# Ma trận bao phủ {n} thành phần protocol lõi" in text
        for item_id, _ in S.PROTOCOL_CORE_ITEMS:
            assert re.search(rf"\|\s*{item_id}\s*\|", text), f"thiếu dòng {item_id}"
        assert {"P21", "P22", "P23"} <= {i for i, _ in S.PROTOCOL_CORE_ITEMS}

    def test_validator_passes_on_fresh_assembly(self, study_dir):
        res = G10.assemble("FIXT", study_dir)
        rep = check_de_cuong.validate(res["md"], study_dir)
        assert rep["passed"], rep["errors"]
        assert rep["checks"]["R1_sections"].startswith("PASS")
        assert rep["checks"]["R14_protocol_core_coverage"] == "PASS (đủ P01-P23)"

    def test_r1_still_bites_when_a_new_section_is_removed(self, study_dir):
        """Đột biến có chủ ý: xoá tiêu đề mục 3 ⇒ R1 phải đỏ và gọi đúng tên mục thiếu."""
        res = G10.assemble("FIXT", study_dir)
        text = res["md"].read_text(encoding="utf-8")
        mutated = text.replace(S.de_cuong_heading("tongquan"), "# 3. Mục bị đổi tên")
        mutated_path = study_dir / "DE_CUONG_THONG_NHAT_FIXT.md"
        mutated_path.write_text(mutated, encoding="utf-8")
        rep = check_de_cuong.validate(mutated_path, study_dir)
        assert not rep["passed"]
        assert any("3. Tổng quan tài liệu và khung lý thuyết" in e for e in rep["errors"])

    def test_r14_accepts_dynamic_count_and_rejects_missing_row(self, study_dir):
        res = G10.assemble("FIXT", study_dir)
        text = res["md"].read_text(encoding="utf-8")
        mutated = re.sub(r"^\|\s*P22\s*\|.*$", "", text, flags=re.MULTILINE)
        mutated_path = study_dir / "DE_CUONG_THONG_NHAT_FIXT.md"
        mutated_path.write_text(mutated, encoding="utf-8")
        rep = check_de_cuong.validate(mutated_path, study_dir)
        assert not rep["passed"]
        assert any("R14" in e and "P22" in e for e in rep["errors"])


class TestStudySpecNewBlocks:
    def test_new_meta_keys_flow_into_spec_and_coverage(self, study_dir):
        cps = {f"G{i}": None for i in range(10)}
        import json
        for i in range(10):
            p = study_dir / f"G{i}_checkpoint.json"
            cps[f"G{i}"] = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
        meta = {
            "literature_review": "Tổng hợp 12 nghiên cứu quan sát.",
            "literature_consensus": "Thời gian chờ liên quan mạnh nhất.",
            "theoretical_framework_not_applicable": "Thiết kế mô tả dịch tễ, không dựa khung hành vi.",
            "table_shells": ["Bảng 1. Đặc điểm nền"],
            "expected_results": "Chỉ khung bảng.",
            "limitations": "Một trung tâm; không suy diễn nhân quả.",
        }
        spec = RS.build_study_spec("FIXT", cps, meta)
        assert spec["literature"]["summary"].startswith("Tổng hợp")
        assert spec["theory"]["framework"] is None
        assert spec["theory"]["not_applicable_rationale"].startswith("Thiết kế")
        assert spec["bias"]["limitations"].startswith("Một trung tâm")
        rows = {r["id"]: r for r in RS.protocol_coverage(spec)}
        assert rows["P21"]["status"] == "ĐỦ DỮ LIỆU DỰ THẢO"
        assert rows["P22"]["status"] == "ĐỦ DỮ LIỆU DỰ THẢO"  # "không áp dụng" có lý do là hợp lệ
        assert rows["P23"]["status"] == "ĐỦ DỮ LIỆU DỰ THẢO"

    def test_missing_theory_and_expected_results_show_up_as_decisions(self, study_dir):
        import json
        cps = {}
        for i in range(10):
            p = study_dir / f"G{i}_checkpoint.json"
            cps[f"G{i}"] = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
        spec = RS.build_study_spec("FIXT", cps, {})
        ids = {row["id"] for row in RS.missing_requirements(spec)}
        assert {"D17", "D18"} <= ids


class TestTemplateMatchesCanon:
    def test_template_01_headings_equal_canon(self):
        """Template của skill (repo gốc) phải khớp canon — không để hai nguồn sự thật.

        Repo gốc có thể là thư mục CHA (bố cục Mac/Windows: `Claude AI/medical-ebm-automation/`)
        hoặc repo ANH EM (bố cục container: `/home/user/EBM-drluanbv175` cạnh
        `/home/user/medical-ebm-automation`), hoặc do biến môi trường EBM_ROOT chỉ.
        Chỉ skip khi KHÔNG tìm thấy ở cả ba nơi — skip là "chưa kiểm được", không phải đạt.
        """
        import os
        rel = Path("sync") / "skills" / "nghien-cuu-y-khoa-chuan-quoc-te" / "templates" / "01_mau_de_cuong_tong_the.md"
        roots = [TOOLS_DIR.parent.parent, TOOLS_DIR.parent.parent / "EBM-drluanbv175"]
        if os.environ.get("EBM_ROOT"):
            roots.insert(0, Path(os.environ["EBM_ROOT"]))
        tpl = next((r / rel for r in roots if (r / rel).exists()), None)
        if tpl is None:
            pytest.skip("template 01 không nằm trong cây làm việc này (đặt EBM_ROOT để kiểm)")
        text = tpl.read_text(encoding="utf-8")
        got = re.findall(r"^## (\d+)\. (.+?)\s*$", text, re.MULTILINE)
        want = [(num, title) for num, title, _ in S.DE_CUONG_SECTIONS]
        assert got == want, f"\nTEMPLATE: {got}\nCANON   : {want}"
        for _num, _title, subs in S.DE_CUONG_SECTIONS:
            for sub in subs:
                assert f"### {sub}" in text, f"template thiếu tiểu mục '### {sub}'"
