"""R8 «minh bạch» phải xuất hiện cho MỌI thiết kế, không chỉ 2/8 (06/09/2026).

Phát hiện qua chính bộ test §6.2-6.5 mới (`test_check_de_cuong_still_passes_for_
rct_with_data`): `check_de_cuong` R8 đòi chuỗi TIẾNG VIỆT "minh bạch" xuất hiện
Ở ĐÂU ĐÓ trong tài liệu lắp ráp, nhưng dòng lưu ý UNCONDITIONAL của
`build_international_compliance()` từng viết "transparency" (tiếng Anh).

Đo kỹ hơn khi viết test này cho thấy bức tranh KHÔNG ĐƠN GIẢN như phán đoán ban
đầu ("chỉ 2/8 thiết kế có sẵn"): "minh bạch" thật ra đến từ HAI nguồn độc lập,
không nguồn nào đủ cho mọi thiết kế:
  (a) `reporting_standards_for("cohort"/"cross_sectional")["protocol"]` —
      chỉ 2 thiết kế này có chữ đó trong chuỗi "protocol".
  (b) `build_protocol_checklist()`'s nhánh **fallback** ("thiết kế này không có
      checklist ĐỀ CƯƠNG theo từng mục") — thêm SÁNG NAY cùng tính năng SPIRIT,
      TÌNH CỜ cũng chứa "minh bạch", che cho case_control/diagnostic/prediction/
      qualitative (4 thiết kế KHÔNG rơi vào nhánh SPIRIT của rct hay nhánh
      "PRISMA-P thiếu" của systematic_review).
Hai thiết kế DUY NHẤT không trúng nguồn nào — **rct** (có nhánh SPIRIT riêng,
bỏ qua fallback) và **systematic_review** (có nhánh "PRISMA-P thiếu" riêng,
cũng bỏ qua fallback) — là hai thiết kế THẬT SỰ phụ thuộc vào bản vá này.
Đây đúng kiểu "đo đúng nhưng đo nhầm số" đã lặp nhiều lần trong repo: giả định
ban đầu ("6/8 thiếu") bị chính phép đột biến bên dưới bác bỏ và sửa lại đúng
số ("2/8 thiếu": rct, systematic_review).

Test này khoá: (1) "minh bạch" xuất hiện cho CẢ 8 thiết kế; (2) R8 không FAIL
vì thiếu thuật ngữ, cho cả 8; (3) đột biến bỏ "minh bạch" khỏi dòng lưu ý
unconditional ⇒ ĐÚNG rct và systematic_review (không phải 6 thiết kế khác)
quay lại thiếu — chứng minh test bám đúng vào dòng vừa sửa, không phải trùng
hợp với nguồn (b).
"""
from __future__ import annotations

import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import run_g10_assemble as G10  # noqa: E402

TESTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS_DIR))
from test_g10_assemble import _write_cross_sectional_fixture  # noqa: E402
from test_protocol_checklist_spirit_2025_20260906 import _retarget_design  # noqa: E402

ALL_DESIGNS = ("rct", "cohort", "cross_sectional", "case_control", "diagnostic",
               "prediction", "systematic_review", "qualitative")
# 6 thiết kế mà "minh bạch" có sẵn từ NGUỒN KHÁC (protocol string của cohort/
# cross_sectional, hoặc nhánh fallback của build_protocol_checklist() cho
# case_control/diagnostic/prediction/qualitative) — KHÔNG phụ thuộc dòng lưu ý
# vừa sửa. Chỉ rct và systematic_review thật sự cần bản vá này.
_DEPENDS_ON_THIS_FIX = {"rct", "systematic_review"}


class TestMinhBachAppearsForEveryDesign:
    def test_all_eight_designs_contain_minh_bach(self, tmp_path_factory):
        missing = []
        for design in ALL_DESIGNS:
            tmp = tmp_path_factory.mktemp(design)
            _write_cross_sectional_fixture(tmp)
            _retarget_design(tmp, design)
            res = G10.assemble("FIXT", tmp)
            text = res["md"].read_text(encoding="utf-8")
            if "minh bạch" not in text:
                missing.append(design)
        assert not missing, f"thiếu 'minh bạch': {missing}"

    def test_r8_check_passes_for_every_design(self, tmp_path_factory):
        import check_de_cuong
        for design in ALL_DESIGNS:
            tmp = tmp_path_factory.mktemp(design)
            _write_cross_sectional_fixture(tmp)
            _retarget_design(tmp, design)
            res = G10.assemble("FIXT", tmp)
            rep = check_de_cuong.validate(res["md"], tmp)
            assert rep["checks"]["R8_international_compliance"].startswith("PASS"), (
                f"{design}: {rep['checks']['R8_international_compliance']}"
            )


class TestMutationProvesFixIsReal:
    def test_removing_minh_bach_from_unconditional_note_breaks_rct_and_sr(self, tmp_path_factory, monkeypatch):
        """Đột biến TẠI CHỖ (monkeypatch, không sửa file): mô phỏng bản TRƯỚC khi
        sửa bằng cách gọi lại build_international_compliance với dòng lưu ý cũ
        (transparency, không có minh bạch) — xác nhận CHỈ rct và systematic_review
        (hai thiết kế không trúng nguồn (a)/(b) nào khác) quay lại thiếu 'minh bạch'.

        `assemble()` gọi `build_international_compliance(cps, meta)` bằng TÊN
        module-level (không qua SECTION_BUILDERS — hàm này KHÔNG nằm trong danh
        sách đó, được nối riêng), nên Python tra cứu tên trong globals của module
        MỖI LẦN gọi ⇒ monkeypatch.setattr trên module đủ để đột biến, không cần
        đụng SECTION_BUILDERS."""
        original = G10.build_international_compliance

        def _reverted(cps, meta=None):
            text = original(cps, meta)
            return text.replace(
                "minh bạch (transparency) và khả năng tái lập (reproducibility)",
                "transparency và reproducibility",
            )

        monkeypatch.setattr(G10, "build_international_compliance", _reverted)

        broken = []
        for design in ALL_DESIGNS:
            tmp = tmp_path_factory.mktemp(design)
            _write_cross_sectional_fixture(tmp)
            _retarget_design(tmp, design)
            res = G10.assemble("FIXT", tmp)
            text = res["md"].read_text(encoding="utf-8")
            if "minh bạch" not in text:
                broken.append(design)
        assert set(broken) == _DEPENDS_ON_THIS_FIX, broken
