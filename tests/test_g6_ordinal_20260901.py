"""Hồi quy cho nhánh kết cục THỨ BẬC (proportional odds) của G6 — 01/09/2026.

Vì sao có: trước ngày này `run_g6_auto.py` KHÔNG có nhánh thứ bậc nào
(grep polr|ordinal|clm = 0 hit), trong khi SAP đã khoá của đề tài thật đầu
tiên đi hết G0-G4 (C1a) khai mô hình CHÍNH là hồi quy logistic thứ tự trên
kết cục 5 mức — cổng G6 sẽ sinh script logistic NHỊ PHÂN mâu thuẫn trực tiếp
với SAP §4. Cùng lớp lỗi "2 lớp xử lý design_code tách rời nhau" đã vá cho
case_control/diagnostic/prediction/sr_ma/qualitative.

Bốn thứ phải khoá:
1. Thẩm quyền kích hoạt là SAP ĐÃ KHOÁ (_sap_declares_ordinal), KHÔNG suy từ
   mã số mức trong dictionary (điều kiện cần chứ không đủ — biến danh định
   nhiều mức cũng mã số nguyên). Thiếu SAP → fail-closed về logistic nhị phân.
2. Dispatch: cờ bật + cross_sectional → template proportional odds phủ đủ cam
   kết SAP (polr · vcovCL cụm · <15 cụm → clmm thành CHÍNH · Brant → partial
   PO · RCS 3 nút · HC3 · loại phiếu hỗ trợ ghi · gộp nhị phân EPV-gated);
   cờ tắt → template nhị phân CŨ nguyên vẹn; cờ bật nhưng design khác → không
   ảnh hưởng.
3. Detect: outcome_levels/cluster_col/mode_var đọc từ REDCap dictionary; các
   khoá mới có mặt ở MỌI đường thoát (kể cả CSV thiếu).
4. Artifact 2 lớp: nhãn phân tích + bảng shell + checklist PHẦN 5 rẽ nhánh
   CÙNG cờ với script — không được nói "logistic OR" khi script dạy polr.
"""

import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import run_g6_auto as G6  # noqa: E402

_HEADER = ('"Variable / Field Name","Form Name","Section Header","Field Type",'
           '"Field Label","Choices, Calculations, OR Slider Labels","Field Note"')

_CSV_ORDINAL = "\n".join([
    _HEADER,
    '"record_id","Admin","","text","Mã bản ghi","",""',
    '"thoigian_cho","Exposure","Phơi nhiễm thời gian chờ","text","Thời gian chờ (phút)","",""',
    '"shlnb_g1","Outcomes","Kết cục chính","radio","Mức hài lòng chung G1",'
    '"1, Rất không hài lòng | 2, Không hài lòng | 3, Bình thường | 4, Hài lòng | 5, Rất hài lòng",""',
    '"ma_ban_kham","Admin","","dropdown","Mã bàn khám","1, Bàn 1 | 2, Bàn 2 | 3, Bàn 3",""',
    '"mode_tra_loi","Admin","","radio","Phương thức trả lời",'
    '"1, Tự điền | 2, Hỗ trợ đọc | 3, Hỗ trợ ghi",""',
    '"age","Demographics","","text","Tuổi","",""',
    '"sex","Demographics","","radio","Giới tính sinh học","1, Nam | 2, Nữ",""',
]) + "\n"

_CSV_BINARY = "\n".join([
    _HEADER,
    '"exposure_x","Exposure","Phơi nhiễm","radio","Phơi nhiễm X","0, Không | 1, Có",""',
    '"outcome_y","Outcomes","Kết cục chính","radio","Kết cục Y","0, Không | 1, Có",""',
    '"age","Demographics","","text","Tuổi","",""',
]) + "\n"


def _v_ordinal():
    """Bộ biến chuẩn cho các test dispatch/artifact — khớp khuôn C1a."""
    return {
        "exposure": "thoigian_cho", "outcome": "shlnb_g1", "time_col": "follow_time",
        "covariates": ["age", "sex"], "detection_log": ["test"],
        "outcome_ordinal": True, "outcome_levels": [1, 2, 3, 4, 5],
        "cluster_col": "ma_ban_kham", "mode_var": "mode_tra_loi",
    }


class TestPhatHienTuDictionary:
    def test_ordinal_levels_cluster_mode(self, tmp_path):
        csv = tmp_path / "dict.csv"
        csv.write_text(_CSV_ORDINAL, encoding="utf-8", newline="\n")
        v = G6.detect_variables_from_redcap(csv)
        assert v["outcome"] == "shlnb_g1"
        assert v["outcome_levels"] == [1, 2, 3, 4, 5]
        assert v["cluster_col"] == "ma_ban_kham"
        assert v["mode_var"] == "mode_tra_loi"
        assert v["cluster_col"] not in v["covariates"], (
            "biến cụm không được đồng thời là covariate cố định")

    def test_binary_khong_bi_coi_la_thu_bac(self, tmp_path):
        csv = tmp_path / "dict.csv"
        csv.write_text(_CSV_BINARY, encoding="utf-8", newline="\n")
        v = G6.detect_variables_from_redcap(csv)
        assert v["outcome_levels"] == [], "2 mức không phải tín hiệu thứ bậc"

    def test_csv_thieu_van_co_du_khoa_moi(self, tmp_path):
        """Khoá mới phải có ở MỌI đường thoát — kể cả early-return CSV thiếu."""
        v = G6.detect_variables_from_redcap(tmp_path / "khong_ton_tai.csv")
        assert v["outcome_levels"] == []
        assert v["cluster_col"] is None
        assert v["mode_var"] is None


class TestSapLaThamQuyen:
    def test_sap_khai_proportional_odds(self, tmp_path):
        (tmp_path / "G4_A5_SAP_FINAL_S.md").write_text(
            "Phương pháp: hồi quy logistic THỨ TỰ (ordinal/proportional odds)",
            encoding="utf-8", newline="\n")
        assert G6._sap_declares_ordinal(tmp_path, "S")

    def test_sap_tieng_viet_khong_kem_tieng_anh(self, tmp_path):
        (tmp_path / "G4_A5_SAP_FINAL_S.md").write_text(
            "Mô hình chính: hồi quy logistic thứ tự trên G1 giữ 5 mức",
            encoding="utf-8", newline="\n")
        assert G6._sap_declares_ordinal(tmp_path, "S")

    def test_sap_logistic_thuong_khong_kich_hoat(self, tmp_path):
        (tmp_path / "G4_A5_SAP_FINAL_S.md").write_text(
            "Mô hình chính: hồi quy logistic đa biến (OR)",
            encoding="utf-8", newline="\n")
        assert not G6._sap_declares_ordinal(tmp_path, "S")

    def test_thieu_sap_fail_closed(self, tmp_path):
        assert not G6._sap_declares_ordinal(tmp_path, "S"), (
            "thiếu SAP phải rơi về hành vi cũ, không đoán")


class TestDispatchThuBac:
    def test_co_bat_sinh_proportional_odds_du_cam_ket_sap(self):
        s = G6.R_ANALYSIS_MAP_FUNC("cross_sectional", _v_ordinal(),
                                   1000, 0.05, 0.80, 0.5, "PREVALENCE")
        # Mô hình chính + từng cam kết SAP §4/§5/§9:
        assert "MASS::polr" in s
        assert "vcovCL" in s and "ma_ban_kham" in s          # SE robust theo cụm
        assert "clmm" in s and "< 15" in s                     # <15 cụm → chặn ngẫu nhiên CHÍNH
        assert "brant::brant" in s                             # kiểm proportional odds
        assert "nominal = ~" in s                              # partial PO khi vi phạm
        assert "rcs(" in s                                     # phi tuyến RCS 3 nút
        assert 'type = "HC3"' in s                             # độ nhạy tuyến tính robust
        assert "mode_tra_loi" in s                             # loại phiếu hỗ trợ ghi
        assert "10 biến cố/tham số" in s                       # gộp nhị phân EPV-gated
        assert "ordered = TRUE" in s                           # kết cục GIỮ thang thứ bậc

    def test_phan_chinh_khong_phai_logistic_nhi_phan(self):
        s = G6.R_ANALYSIS_MAP_FUNC("cross_sectional", _v_ordinal(),
                                   1000, 0.05, 0.80, 0.5, "PREVALENCE")
        phan_chinh = s.split("(6c)")[0]  # trước nhánh độ nhạy gộp nhị phân
        assert "family = binomial" not in phan_chinh and "family=binomial" not in phan_chinh

    def test_co_tat_giu_nguyen_template_nhi_phan_cu(self):
        v = _v_ordinal()
        v["outcome_ordinal"] = False
        s = G6.R_ANALYSIS_MAP_FUNC("cross_sectional", v, 1000, 0.05, 0.80, 0.5, "PREVALENCE")
        assert "polr" not in s
        assert "glm_adj" in s, "hành vi cũ (logistic nhị phân) phải nguyên vẹn"

    def test_co_bat_nhung_design_khac_khong_anh_huong(self):
        v = _v_ordinal()
        v["time_col"] = "follow_time"
        s = G6.R_ANALYSIS_MAP_FUNC("cohort", v, 1000, 0.05, 0.80, 1.5, "HR")
        assert "polr" not in s, "cờ thứ bậc chỉ áp cho cross_sectional"

    def test_thieu_cum_va_mode_in_placeholder_khong_bia(self):
        v = _v_ordinal()
        v["cluster_col"] = None
        v["mode_var"] = None
        v["outcome_levels"] = []
        s = G6.R_ANALYSIS_MAP_FUNC("cross_sectional", v, 1000, 0.05, 0.80, 0.5, "PREVALENCE")
        assert "[CẦN TÊN BIẾN CỤM" in s
        assert "[CẦN TÊN BIẾN PHƯƠNG THỨC TRẢ LỜI" in s
        assert "[CẦN NGƯỠNG THEO SAP" in s


class TestArtifactHaiLopKhop:
    def test_artifact_thu_bac_khop_script(self, tmp_path):
        v = _v_ordinal()
        art = G6.generate_artifact("S", "T", "cross_sectional", "STROBE 2007",
                                   1000, 0.05, 0.80, 0.5, "PREVALENCE",
                                   "PENDING", "2026-09-01", tmp_path, v)
        assert "proportional odds" in art.lower() or "THỨ TỰ" in art
        assert "Brant" in art, "checklist PHẦN 5 phải có mục kiểm proportional odds"
        assert "Logistic regression (OR 95%CI)" not in art
        # Ghim RIÊNG lớp bảng shell (đột biến 01/09 lộ ra: 2 assert trên đạt
        # nhờ nhãn phân tích + checklist trong khi bảng vẫn là bản nhị phân —
        # phải ghim đúng TIÊU ĐỀ bảng, không chỉ sự có mặt của chuỗi "cOR"):
        assert "Kết cục chính (Proportional odds — cOR)" in art
        assert "Kết cục chính (Logistic regression)" not in art
        assert "Giả định & độ nhạy (SAP §5/§9)" in art, "bảng 3 giả định/độ nhạy phải có"

    def test_artifact_nhi_phan_giu_nhan_cu(self, tmp_path):
        v = _v_ordinal()
        v["outcome_ordinal"] = False
        art = G6.generate_artifact("S", "T", "cross_sectional", "STROBE 2007",
                                   1000, 0.05, 0.80, 0.5, "PREVALENCE",
                                   "PENDING", "2026-09-01", tmp_path, v)
        assert "Logistic regression (OR 95%CI)" in art
        assert "Brant" not in art

    def test_guardrail_khong_loi_tren_goi_thu_bac(self, tmp_path):
        v = _v_ordinal()
        s = G6.R_ANALYSIS_MAP_FUNC("cross_sectional", v, 1000, 0.05, 0.80, 0.5, "PREVALENCE")
        art = G6.generate_artifact("S", "T", "cross_sectional", "STROBE 2007",
                                   1000, 0.05, 0.80, 0.5, "PREVALENCE",
                                   "PENDING", "2026-09-01", tmp_path, v)
        errors, _ = G6.guardrail(art, s)
        assert errors == [], f"guardrail phải sạch trên gói thứ bậc: {errors}"

    def test_sap_that_c1a_kich_hoat_co(self):
        """Đề tài thật C1a (SAP v1.1 đã đồng bộ 30/08) phải kích hoạt nhánh này."""
        out = Path(__file__).resolve().parent.parent / "exports" / "hai-long-benh-nhan-C1a-BVQY175"
        sap = out / "G4_A5_SAP_FINAL_hai-long-benh-nhan-C1a-BVQY175.md"
        if not sap.exists():
            import pytest
            pytest.skip("không có exports C1a trên máy này")
        assert G6._sap_declares_ordinal(out, "hai-long-benh-nhan-C1a-BVQY175")
