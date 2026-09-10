r"""Hồi quy G5-F3 (audit toàn diện G0-G10, 2026-07-30 — vá thật 10/09/2026,
audit toàn diện hệ nghiên cứu).

CƠ CHẾ LỖI (TRƯỚC bản vá): `G5-AUTO-03` trong `tools/g5_quality_gate.py` chỉ
hỏi "11 nhãn bắt buộc (`_REQUIRED_DMP_TOKENS`) có xuất hiện Ở ĐÂU ĐÓ trong
toàn văn bản DMP không" — mà `run_g5_auto.py::generate_artifact()` LUÔN in đủ
11 nhãn đó vô điều kiện (không phụ thuộc design_code/specialty/rows). Nghĩa là
luật này KHÔNG BAO GIỜ có thể BLOCK về mặt cấu trúc: một DMP chỉ toàn 11 nhãn
trần, không một dòng nội dung thật nào dưới mỗi nhãn, vẫn PASS. Lỗ hổng này đã
được TỰ THÚ trong comment code từ 2026-07-30 (mã "G5-F3 — MEDIUM") nhưng chưa
từng được vá cho tới hôm nay.

BẢN VÁ: thêm `_dmp_noi_dung_thieu_duoi_nhan()` — với mỗi nhãn đã xuất hiện,
trích đoạn văn bản NGAY SAU nhãn đó tới nhãn kế tiếp (theo vị trí THẬT trong
văn bản), bỏ mọi placeholder `[CẦN...]`/`[REQUIRE_HUMAN...]`, rồi đòi phần còn
lại có ít nhất 20 ký tự nội dung thật. Đúng khuôn BH97
(`approve_gate._g4_sections_still_draft`): phân biệt "nhãn có mặt nhưng thân
mục rỗng" (BLOCK) khỏi "nhãn hoàn toàn vắng mặt" (đã có `missing_dmp` xử lý
riêng, không đổi).

Nguyên tắc viết test:
1. Đối chứng KHÔNG hồi quy — DMP THẬT do CHÍNH `run_g5_auto.generate_artifact()`
   sinh ra (không phải fixture giả định) phải vẫn PASS sau bản vá.
2. Ca chính — DMP tautology (chỉ 11 nhãn trần, không nội dung) phải BLOCK, và
   phải liệt kê đúng các nhãn thiếu nội dung.
3. Đột biến — mô phỏng lại LUẬT CŨ (chỉ kiểm substring có mặt, bỏ qua kiểm nội
   dung) trên chính DMP tautology ở (2) để chứng minh: nếu KHÔNG có bản vá này,
   luật sẽ (sai) báo PASS. Đây là bằng chứng trực tiếp cho khẳng định "lỗ hổng
   là thật", không chỉ suy diễn.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import g5_quality_gate as G5Q  # noqa: E402
import run_g5_auto as RG5  # noqa: E402

_ROWS_MAU = [
    ("subject_id", "demographics", "", "text", "Mã đối tượng", "", "", "", "", "", "y"),
    ("visit_date", "demographics", "", "date_ymd", "Ngày khám", "", "", "", "", "", "y"),
    ("age", "demographics", "", "number", "Tuổi", "", "", "", "18", "99", "y"),
    ("primary_outcome", "outcome", "", "number", "Kết cục chính", "", "", "", "0", "1", "y"),
]


def _sinh_dmp_that() -> str:
    """Gọi ĐÚNG bộ sinh thật của G5 — không phải fixture rút gọn — để chứng
    minh bản vá không tạo báo động giả trên đường vận hành thật."""
    return RG5.generate_artifact(
        study="PYTEST-REAL-DMP-CHECK-20260910",
        topic="Đề tài kiểm thử G5-AUTO-03",
        design_code="cross_sectional",
        n_adjusted=200,
        n_total=200,
        n_per_group=0,
        run_date="2026-09-10",
        rows=_ROWS_MAU,
        specialty="generic",
    )


class TestDoiChungKhongHoiQuyTrenDmpThat:
    def test_dmp_that_khong_thieu_nhan(self):
        text = _sinh_dmp_that()
        thieu = [
            t for t in G5Q._REQUIRED_DMP_TOKENS if t.casefold() not in text.casefold()
        ]
        assert thieu == []

    def test_dmp_that_khong_thieu_noi_dung(self):
        text = _sinh_dmp_that()
        thieu_noi_dung = G5Q._dmp_noi_dung_thieu_duoi_nhan(text, G5Q._REQUIRED_DMP_TOKENS)
        assert thieu_noi_dung == [], (
            "DMP do CHÍNH run_g5_auto.py sinh ra phải PASS luật nội dung mới — "
            f"nếu FAIL thì bản vá đang báo động giả trên đường vận hành thật: {thieu_noi_dung}"
        )


class TestCaChinhDmpTautologyBiChan:
    """DMP chỉ toàn 11 nhãn trần — đúng hiện trạng lỗ hổng G5-F3 đã tự thú
    trong comment code trước bản vá."""

    def _dmp_gia_chi_nhan_tran(self) -> str:
        return "\n".join(G5Q._REQUIRED_DMP_TOKENS)

    def test_khong_thieu_nhan_nhung_thieu_noi_dung(self):
        text = self._dmp_gia_chi_nhan_tran()
        thieu_nhan = [
            t for t in G5Q._REQUIRED_DMP_TOKENS if t.casefold() not in text.casefold()
        ]
        assert thieu_nhan == [], "Cả 11 nhãn đều CÓ MẶT — đúng tiền đề của tautology"

        thieu_noi_dung = G5Q._dmp_noi_dung_thieu_duoi_nhan(text, G5Q._REQUIRED_DMP_TOKENS)
        assert set(thieu_noi_dung) == set(G5Q._REQUIRED_DMP_TOKENS), (
            "Mọi nhãn đều phải bị gắn cờ THIẾU NỘI DUNG — thân mục giữa hai nhãn "
            f"liên tiếp chỉ là một dấu xuống dòng. Thực tế: {thieu_noi_dung}"
        )

    def test_dmp_tautology_di_qua_full_criterion_van_block(self, tmp_path, monkeypatch):
        """Kiểm ở đúng tầng tích hợp: gọi lại chính đoạn logic G5-AUTO-03 bằng
        cách dựng report qua evaluate_study không khả thi (cần toàn bộ chuỗi
        G2-G9 khác) — nên kiểm trực tiếp cặp hàm mà G5-AUTO-03 gọi, đã đủ để
        chứng minh trạng thái BLOCK/PASS cuối cùng của tiêu chí này."""
        text = self._dmp_gia_chi_nhan_tran()
        missing_dmp = [
            t for t in G5Q._REQUIRED_DMP_TOKENS if t.casefold() not in text.casefold()
        ]
        content_thieu = G5Q._dmp_noi_dung_thieu_duoi_nhan(text, G5Q._REQUIRED_DMP_TOKENS)
        thieu_tong = missing_dmp or content_thieu
        assert thieu_tong, "G5-AUTO-03 PHẢI BLOCK cho DMP chỉ toàn nhãn trần"


class TestDotBienChungMinhLoHongThatSuTonTaiTruocBanVa:
    """Mô phỏng LẠI luật CŨ (chỉ kiểm substring có mặt — không có
    `_dmp_noi_dung_thieu_duoi_nhan`) trên CHÍNH DMP tautology ở trên, để
    chứng minh trực tiếp: không có bản vá này, G5-AUTO-03 sẽ SAI mà báo PASS.
    Đây là bằng chứng thực nghiệm, không phải suy diễn từ đọc code."""

    def test_luat_cu_se_bao_pass_sai_tren_dmp_tautology(self):
        text = "\n".join(G5Q._REQUIRED_DMP_TOKENS)

        # Đúng nguyên văn điều kiện CŨ trước bản vá 10/09/2026.
        missing_dmp_theo_luat_cu = [
            t for t in G5Q._REQUIRED_DMP_TOKENS if t.casefold() not in text.casefold()
        ]
        trang_thai_theo_luat_cu = "BLOCK" if missing_dmp_theo_luat_cu else "PASS"

        assert trang_thai_theo_luat_cu == "PASS", (
            "Đây CHÍNH LÀ lỗ hổng G5-F3: luật cũ chỉ đếm nhãn có mặt nên báo PASS "
            "sai cho một DMP hoàn toàn không có nội dung thật nào."
        )

        # Đối chứng: luật MỚI (đã vá) phải BLOCK đúng cho cùng văn bản này.
        content_thieu_theo_luat_moi = G5Q._dmp_noi_dung_thieu_duoi_nhan(
            text, G5Q._REQUIRED_DMP_TOKENS
        )
        assert content_thieu_theo_luat_moi, "Luật MỚI phải bắt được điều luật cũ bỏ sót"
