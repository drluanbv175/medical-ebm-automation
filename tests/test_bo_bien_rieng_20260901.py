"""Hồi quy: BỘ BIẾN RIÊNG của đề tài (G5) + phát hiện biến theo cấu trúc (G6)
+ CLI G1 — kiểm toàn diện 01/09/2026.

Bốn khoảng hở THẬT đo được trong cuộc kiểm toàn diện (đúng lớp bực bội «xử lý
số liệu chưa hoàn thiện» của bác sĩ):
1. run_g5_auto CHỈ sinh dictionary từ bundle đóng hộp — không có đường nạp bộ
   biến mà tầng bien-so đã đặc tả cho đề tài cụ thể; đo trên C1a: bundle đặt
   `wait_time_min` trong khi SAP khoá `thoigian_cho`/`ma_ban_kham`/... — mọi
   script hạ nguồn sinh trên TÊN SAI.
2. Bộ từ khoá covariate của G6 nghiêng tiếng Anh — biến tiếng Việt trượt hết,
   template rơi về "age + sex + bmi" sai tên; cần tín hiệu CẤU TRÚC (Section
   Header khai forced-in / «không hiệu chỉnh»).
3. RANGE_CHECKS tự nhận «dựng động từ CRF» nhưng chỉ lọc bảng VALIDATION_RULES
   tĩnh — min/max khai trong dictionary bị bỏ qua với bộ biến riêng.
4. g1_quality_gate là cổng DUY NHẤT không có CLI — gọi --study thì im lặng
   thoát 0 («yên tâm giả», họ BH32).
"""

import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import run_g5_auto as G5  # noqa: E402
import run_g6_auto as G6  # noqa: E402

_HDR = ('"Variable / Field Name","Form Name","Section Header","Field Type",'
        '"Field Label","Choices, Calculations, OR Slider Labels","Field Note",'
        '"Text Validation Type OR Show Slider Number","Text Validation Min",'
        '"Text Validation Max","Identifier?","Branching Logic (Show field only if...)",'
        '"Required Field?","Custom Alignment","Question Number (surveys only)",'
        '"Matrix Group Name","Matrix Ranking?","Field Annotation"')


def _viet(tmp_path, *dong):
    p = tmp_path / G5.BO_BIEN_RIENG_TEN_FILE
    p.write_text("\n".join([_HDR, *dong]) + "\n", encoding="utf-8", newline="\n")
    return p


class TestNapBoBienRieng:
    def test_vang_mat_tra_none(self, tmp_path):
        assert G5.nap_bo_bien_rieng(tmp_path, "S") is None

    def test_hop_le_tra_tuple_12_truong(self, tmp_path):
        _viet(tmp_path,
              '"record_id","m","","text","Mã phiếu","","","","","","","","y","","","","",""',
              '"tuoi","m","Hiệu chỉnh","text","Tuổi","","","integer","18","120","","","y","","","","",""')
        rows = G5.nap_bo_bien_rieng(tmp_path, "S")
        assert len(rows) == 2 and len(rows[0]) == 12
        assert rows[1][0] == "tuoi" and rows[1][7] == "integer" and rows[1][10] == "y"

    def test_thieu_cot_bat_buoc_dung_ma_2(self, tmp_path):
        p = tmp_path / G5.BO_BIEN_RIENG_TEN_FILE
        p.write_text('"Variable / Field Name","Form Name"\n"x","m"\n',
                     encoding="utf-8", newline="\n")
        with pytest.raises(SystemExit):
            G5.nap_bo_bien_rieng(tmp_path, "S")

    def test_ten_bien_trung_dung_khong_roi_ve_bundle(self, tmp_path):
        """File CÓ MẶT mà hỏng → DỪNG, tuyệt đối không im lặng rơi về bundle."""
        _viet(tmp_path,
              '"record_id","m","","text","Mã","","","","","","","","y","","","","",""',
              '"tuoi","m","","text","Tuổi","","","","","","","","n","","","","",""',
              '"tuoi","m","","text","Tuổi lặp","","","","","","","","n","","","","",""')
        with pytest.raises(SystemExit):
            G5.nap_bo_bien_rieng(tmp_path, "S")

    def test_field_type_la_dung(self, tmp_path):
        _viet(tmp_path,
              '"record_id","m","","text","Mã","","","","","","","","y","","","","",""',
              '"x1","m","","kieu_la","Nhãn","","","","","","","","n","","","","",""')
        with pytest.raises(SystemExit):
            G5.nap_bo_bien_rieng(tmp_path, "S")

    def test_thieu_record_id_tu_chen_dau(self, tmp_path):
        _viet(tmp_path,
              '"tuoi","m","","text","Tuổi","","","integer","18","120","","","n","","","","",""')
        rows = G5.nap_bo_bien_rieng(tmp_path, "S")
        assert rows[0][0] == "record_id", "REDCap đòi record_id đứng đầu"


class TestPhatHienTheoCauTruc:
    def _detect(self, tmp_path, *dong):
        _viet(tmp_path,
              '"record_id","m","","text","Mã","","","","","","","","y","","","","",""',
              '"phoi_nhiem_x","m","Phơi nhiễm X","text","Phơi nhiễm","","","number","0","10","","","y","","","","",""',
              '"ket_cuc_y","m","Kết cục chính","radio","Kết cục",'
              '"1, M1 | 2, M2 | 3, M3 | 4, M4 | 5, M5","","","","","","","y","","","","",""',
              *dong)
        tmp2 = Path(tempfile.mkdtemp())
        rows = G5.nap_bo_bien_rieng(tmp_path, "S")
        csv_path, _ = G5.generate_csv("S", tmp2, rows)
        return G6.detect_variables_from_redcap(csv_path)

    def test_section_forced_in_vao_covariates(self, tmp_path):
        v = self._detect(tmp_path,
            '"bien_viet","m","Biến hiệu chỉnh (forced-in theo DAG)","radio","Biến tiếng Việt",'
            '"1, A | 2, B","","","","","","","n","","","","",""')
        assert "bien_viet" in v["covariates"], (
            "Section khai forced-in phải thắng từ khoá tiếng Anh")

    def test_section_khong_hieu_chinh_bi_loai(self, tmp_path):
        v = self._detect(tmp_path,
            '"age_thamdo","m","Vận hành (mô tả/thăm dò — KHÔNG hiệu chỉnh mô hình chính)",'
            '"text","Age thăm dò","","","number","0","99","","","n","","","","",""')
        assert "age_thamdo" not in v["covariates"], (
            "Section khai KHÔNG hiệu chỉnh phải loại dù từ khoá 'age' khớp")


class TestRangeChecksTuCrf:
    _ROWS = [
        ("record_id", "m", "", "text", "Mã", "", "", "", "", "", "y", ""),
        ("tuoi", "m", "", "text", "Tuổi", "", "", "integer", "18", "120", "y", ""),
        ("diem_tu_do", "m", "", "text", "Điểm", "", "", "number", "0", "5", "n", ""),
        ("khong_range", "m", "", "text", "Không range", "", "", "number", "", "", "n", ""),
    ]

    def test_quality_report_gat_min_max_tu_rows(self):
        q = G5.gen_data_quality_report_script("S", "cross_sectional", list(self._ROWS))
        assert '("tuoi", 18.0, 120.0)' in q
        assert '("diem_tu_do", 0.0, 5.0)' in q
        assert "khong_range" not in q.split("RANGE_CHECKS")[1].split("]")[0]

    def test_cleaning_script_cung_gat(self):
        c = G5.gen_data_cleaning_script("S", "cross_sectional", list(self._ROWS))
        assert "('tuoi', 18.0, 120.0)" in c


class TestG1CoCli:
    def test_thieu_bao_cao_ma_2_khong_im_lang(self, tmp_path):
        """Trước bản vá: gọi --study là im lặng thoát 0 — «yên tâm giả» BH32."""
        r = subprocess.run(
            [sys.executable, str(TOOLS_DIR / "g1_quality_gate.py"),
             "--study", "KHONG-TON-TAI-2026"],
            capture_output=True, text=True, timeout=60)
        assert r.returncode == 2
        assert "chưa từng được chấm" in r.stdout

    def test_c1a_in_trang_thai_da_luu(self):
        out = REPO_ROOT / "exports" / "hai-long-benh-nhan-C1a-BVQY175"
        if not (out / "G1_QUALITY_REPORT.json").exists():
            pytest.skip("không có exports C1a trên máy này")
        r = subprocess.run(
            [sys.executable, str(TOOLS_DIR / "g1_quality_gate.py"),
             "--study", "hai-long-benh-nhan-C1a-BVQY175"],
            capture_output=True, text=True, timeout=60)
        assert "G1 QUALITY" in r.stdout and "ĐÃ LƯU" in r.stdout.upper() or "đã lưu" in r.stdout.lower()
        assert r.returncode in (0, 2, 3)


class TestC1aTronLane:
    """Đề tài thật C1a: bộ biến riêng → dictionary → G6 → script tên thật."""

    def _out(self):
        out = REPO_ROOT / "exports" / "hai-long-benh-nhan-C1a-BVQY175"
        if not (out / G5.BO_BIEN_RIENG_TEN_FILE).exists():
            pytest.skip("không có _bo-bien-rieng.csv của C1a trên máy này")
        return out

    def test_forced_in_khop_sap_5(self):
        out = self._out()
        rows = G5.nap_bo_bien_rieng(out, "hai-long-benh-nhan-C1a-BVQY175")
        tmp = Path(tempfile.mkdtemp())
        csv_path, _ = G5.generate_csv("T", tmp, rows)
        v = G6.detect_variables_from_redcap(csv_path)
        assert v["exposure"] == "thoigian_cho"
        assert v["outcome"] == "g1" and v["outcome_levels"] == [1, 2, 3, 4, 5]
        assert v["cluster_col"] == "ma_ban_kham" and v["mode_var"] == "mode_tra_loi"
        assert sorted(v["covariates"]) == sorted([
            "tuoi", "gioitinh", "noicutru", "cobhyt", "lydokham", "duoc_dung_bacsi",
            "suckhoe_tudanhgia", "khunggio_kham", "ngay_trong_tuan", "chuyenkhoa"]), (
            "covariates phải ĐÚNG 10 biến forced-in SAP §5 — không thừa biến "
            "mô tả/thăm dò, không thiếu biến đã khoá")

    def test_script_thu_bac_mang_ten_that(self):
        out = self._out()
        rows = G5.nap_bo_bien_rieng(out, "hai-long-benh-nhan-C1a-BVQY175")
        tmp = Path(tempfile.mkdtemp())
        csv_path, _ = G5.generate_csv("T", tmp, rows)
        v = G6.detect_variables_from_redcap(csv_path)
        v["outcome_ordinal"] = True
        s = G6.R_ANALYSIS_MAP_FUNC("cross_sectional", v, 1000, 0.05, 0.80, 0.5, "PREVALENCE")
        assert "g1 ~ thoigian_cho" in s and "ma_ban_kham" in s and "mode_tra_loi" in s
