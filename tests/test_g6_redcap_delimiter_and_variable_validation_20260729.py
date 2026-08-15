"""Hồi quy CRITICAL cho cổng G6 (2026-07-29) — tích hợp G5→G6 thật đã vỡ.

BỐI CẢNH: khi soi cổng G6, agent audit báo "G6 đọc SAI data dictionary do chính
G5 sinh ra — tên biến tiền định trở thành CẢ DÒNG CSV, cổng vẫn báo ✅ PASS".
Ban đầu bị nghi ngờ vì đây là lời của một agent chưa qua phản biện (workflow
chết vì giới hạn phiên trước khi phản biện kịp chạy). Tự tay tái hiện bằng
đúng cặp hàm thật của pipeline — `run_g5_auto.generate_csv()` sinh, rồi
`run_g6_auto.detect_variables_from_redcap()` đọc lại — và XÁC NHẬN 100%:

  Nguyên nhân: `detect_variables_from_redcap()` đoán delimiter bằng quy tắc
  "có ' / ' trong dòng đầu thì dùng ' / ' làm delimiter". Nhưng CSV chuẩn REDCap
  18 cột (đúng định dạng `run_g5_auto.py::generate_csv()` sinh ra) có TÊN CỘT
  ĐẦU TIÊN literally là "Variable / Field Name" — dòng đầu LUÔN chứa " / " dù
  toàn file phân tách bằng dấu phẩy. Hậu quả: `exposure`/`outcome` trở thành
  NGUYÊN CẢ DÒNG CSV, và mọi script R/CLI sinh ra nhúng chuỗi đó làm tên cột
  → vỡ cú pháp hoàn toàn. `guardrail()` (chỉ kiểm PII/hardcode/claim-LOCKED/
  disclaimer) không có cơ chế nào bắt được — cổng báo "✅ PASS" trên một
  pipeline đã tê liệt.

HAI LỚP VÁ ĐỘC LẬP (kiểm cả hai — một lớp hỏng không được để lộ ra người dùng):
  1. Sửa THUẬT TOÁN đoán delimiter: đếm số cột thực tế mỗi delimiter ứng viên
     tách được, chọn delimiter cho ra NHIỀU CỘT NHẤT.
  2. `_reject_if_variable_names_invalid()`: lớp phòng thủ ĐỘC LẬP — nếu vì lý
     do nào khác mà tên biến vẫn không phải định danh hợp lệ, DỪNG CỨNG
     (exit code GC.EXIT_GUARDRAIL_FAIL) thay vì âm thầm sinh script vỡ.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parent.parent
for _p in (str(_REPO), str(_REPO / "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import gate_contract as GC  # noqa: E402
import run_g5_auto as G5  # noqa: E402
import run_g6_auto as G6  # noqa: E402


def _real_g5_dictionary(tmp_path: Path, study: str, rows) -> Path:
    """Sinh dictionary CSV bằng ĐÚNG hàm thật của G5 — không tự viết CSV tay,
    để test này thất bại ngay nếu run_g5_auto.py đổi định dạng mà không đồng bộ."""
    csv_path, _n = G5.generate_csv(study, tmp_path, rows)
    return csv_path


class TestTichHopThatG5SinhG6DocLai:
    """Tái hiện đúng CHUỖI THẬT của pipeline: G5 sinh dictionary → G6 đọc lại."""

    def test_csv_chuan_18_cot_g6_doc_dung_ten_bien(self, tmp_path):
        rows = [
            ("exposure_group", "demographics", "", "radio", "Nhóm phơi nhiễm",
             "1, Có | 0, Không", "", "", "", "", "", ""),
            ("outcome_event", "outcomes", "Kết cục chính", "yesno",
             "Biến cố kết cục", "", "", "", "", "", "", ""),
            ("age", "demographics", "", "text", "Tuổi", "", "", "integer",
             "0", "120", "", ""),
        ]
        csv_path = _real_g5_dictionary(tmp_path, "S1", rows)

        # Chốt tiền đề: dòng đầu CSV thật do G5 sinh PHẢI chứa " / " (đây chính
        # là cái bẫy) — nếu run_g5_auto.py đổi header, test này báo ngay.
        first_line = csv_path.read_text(encoding="utf-8").splitlines()[0]
        assert " / " in first_line, (
            "tiền đề của test không còn đúng — header CSV G5 không còn chứa ' / ', "
            "kiểm lại run_g5_auto.py::generate_csv()"
        )

        v = G6.detect_variables_from_redcap(csv_path)
        assert v["exposure"] == "exposure_group", (
            f"exposure bị đọc sai: {v['exposure']!r} — nghi lại lỗi delimiter cũ"
        )
        assert v["outcome"] == "outcome_event"
        assert "," not in v["exposure"]
        assert "," not in v["outcome"]

    def test_ten_bien_dung_de_nhung_vao_r_khong_vo_cu_phap(self, tmp_path):
        rows = [
            ("exposure_group", "demographics", "", "radio", "Nhóm phơi nhiễm",
             "1, Có | 0, Không", "", "", "", "", "", ""),
            ("outcome_event", "outcomes", "Kết cục chính", "yesno",
             "Biến cố kết cục", "", "", "", "", "", "", ""),
        ]
        csv_path = _real_g5_dictionary(tmp_path, "S2", rows)
        v = G6.detect_variables_from_redcap(csv_path)
        r_code = G6.make_r02_tables(v, "cohort")
        by_line = next(line for line in r_code.splitlines() if 'by      = "' in line)
        assert by_line.count('"') == 2, (
            f"dòng 'by =' có dấu ngoặc kép thừa — cú pháp R sẽ vỡ: {by_line!r}"
        )

    def test_dinh_dang_cu_slash_van_hoat_dong_khong_hoi_quy(self, tmp_path):
        """Không được sửa quá tay: định dạng cũ nối bằng ' / ' (không dấu phẩy)
        vẫn phải nhận diện đúng exposure/outcome như trước khi vá."""
        old_text = (
            "record_id / Admin / age / text / Tuổi / / / integer / 0 / 120 / /\n"
            "exposure_group / Demo / exposure_group / radio / Nhóm phơi nhiễm / "
            "1,Có|0,Không / / / / / /\n"
            "outcome_event / Outcomes / outcome_event / yesno / Biến cố kết cục "
            "/ / / / / / /\n"
        )
        p = tmp_path / "legacy.csv"
        p.write_text(old_text, encoding="utf-8")
        v = G6.detect_variables_from_redcap(p)
        assert v["exposure"] == "exposure_group"
        assert v["outcome"] == "outcome_event"


class TestDoanDelimiterBangSoCot:
    """Kiểm trực tiếp thuật toán mới: chọn delimiter cho ra nhiều cột nhất."""

    def test_header_csv_that_chua_slash_trong_ten_cot(self, tmp_path):
        """Trường hợp lỗi gốc: dòng đầu CSV chuẩn (dấu phẩy) có MỘT tên cột
        chứa ' / ' — không được để việc đó đánh lừa thuật toán."""
        text = (
            '"Variable / Field Name","Form Name","Section Header",'
            '"Field Type","Field Label"\n'
            '"a","f1","","radio","nhan a"\n'
        )
        p = tmp_path / "x.csv"
        p.write_text(text, encoding="utf-8")
        v = G6.detect_variables_from_redcap(p)
        assert v["all_vars"] == ["a"], v

    def test_dong_dau_khong_tach_duoc_gi_roi_ve_dau_phay(self, tmp_path):
        p = tmp_path / "single.csv"
        p.write_text("onlyonecolumn\nrow1value\n", encoding="utf-8")
        v = G6.detect_variables_from_redcap(p)
        assert v["all_vars"] == ["row1value"]


class TestLopPhongThuThuHaiValidateTenBien:
    """`_reject_if_variable_names_invalid` — độc lập với việc sửa delimiter ở trên."""

    def test_ten_bien_hop_le_khong_bi_chan(self):
        G6._reject_if_variable_names_invalid(
            {"exposure": "exposure_group", "outcome": "outcome_event",
             "time_col": "follow_time", "covariates": ["age", "sex"]}
        )  # không raise

    def test_ten_bien_chua_dau_phay_bi_chan_cung(self):
        with pytest.raises(SystemExit) as exc:
            G6._reject_if_variable_names_invalid(
                {"exposure": "a,b,c,d", "outcome": "outcome_event",
                 "time_col": None, "covariates": []}
            )
        assert exc.value.code == GC.EXIT_GUARDRAIL_FAIL

    def test_ten_bien_chua_dau_ngoac_kep_bi_chan(self):
        with pytest.raises(SystemExit):
            G6._reject_if_variable_names_invalid(
                {"exposure": 'x","y', "outcome": "ok", "time_col": None,
                 "covariates": []}
            )

    def test_covariate_hong_cung_bi_bat(self):
        with pytest.raises(SystemExit):
            G6._reject_if_variable_names_invalid(
                {"exposure": "ok_exp", "outcome": "ok_out", "time_col": None,
                 "covariates": ["age", "bad,name"]}
            )

    def test_time_col_rong_khong_bi_chan_oan(self):
        """time_col thường là None/rỗng cho thiết kế không sống còn — không
        được coi giá trị rỗng là 'tên biến hỏng'."""
        G6._reject_if_variable_names_invalid(
            {"exposure": "ok_exp", "outcome": "ok_out", "time_col": None,
             "covariates": []}
        )  # không raise
