"""Bộ sinh đề cương nộp dựng TỪNG MỤC chuẩn báo cáo từ quyết định đã chốt — để K17 chặn được cả bản nháp (21/11/2026).

Bác sĩ: «mọi đề tài, mọi thiết kế phải đạt từng mục chuẩn quốc tế và Việt Nam; những gì không đạt chuẩn sẽ phải được
loại bỏ». Đo K17 trên 8 đề cương giả lập: ~50 mục thiếu (STROBE 5/6a/6b/7/8/10/12d/13–16a/18/19/21/22, RECORD
6.1/6.2/7.1/12.2/13.1/19.1/22.1, TT43 Điều 7) dù phần lớn dữ kiện đã có trong G1/G3/G4/G9. Mỗi test khoá một mục:
  - dữ kiện có ⇒ câu dựng từ CHÍNH dữ kiện đó (không câu mẫu chung);
  - dữ kiện vắng ⇒ ô «………» cho chủ nhiệm, và K17 vẫn báo thiếu (ô trống không phải yếu tố).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import can_cu_dao_duc as CCDD  # noqa: E402
import khuon_de_cuong_bvqy175 as KDC  # noqa: E402
import kiem_chuan_de_cuong_theo_muc as KCM  # noqa: E402
import sinh_de_cuong_nop_hoi_dong as SDC  # noqa: E402
from test_sinh_de_cuong_nop_hoi_dong_20261116 import MA, _de_tai  # noqa: E402

CHAM = SDC.CHAM


def _sua_meta(d: Path, g1: dict | None = None, g2: dict | None = None, **meta) -> None:
    p = d / "study_meta.json"
    m = json.loads(p.read_text(encoding="utf-8"))
    m["gate_params"]["G1"].update(g1 or {})
    m["gate_params"]["G2"].update(g2 or {})
    for k, v in meta.items():
        if v is None:
            m.pop(k, None)
        else:
            m[k] = v
    p.write_text(json.dumps(m, ensure_ascii=False), encoding="utf-8", newline="\n")


def _nguon(tmp_path: Path, tk: str = "cohort", g1: dict | None = None, g2: dict | None = None, **meta) -> SDC.Nguon:
    tmp_path.mkdir(parents=True, exist_ok=True)
    d = _de_tai(tmp_path, tk)
    _sua_meta(d, g1, g2, **meta)
    return SDC.Nguon(d, MA)


def _van(tmp_path: Path, tk: str, g1: dict | None = None, g2: dict | None = None, **meta) -> str:
    return SDC.dung_de_cuong(_nguon(tmp_path, tk, g1, g2, **meta))


def _thieu(van: str, tk: str) -> dict:
    return {(r.chuan, r.ma): r.thieu for r in KCM.doi_chieu(van, tk)["ket_qua"] if r.trang_thai == "thieu"}


# ───────────────────────────────────────── đầu–cuối: đề tài đủ quyết định ⇒ K17 sạch ở mọi thiết kế quan sát
@pytest.mark.parametrize("tk", ["cross_sectional", "cohort", "case_control"])
def test_de_tai_du_quyet_dinh_thi_k17_sach(tmp_path, tk):
    assert _thieu(_van(tmp_path, tk), tk) == {}


# ───────────────────────────────────────── STROBE 4–5: hướng thu thập, thời gian, giai đoạn thu thập
def test_thoi_gian_doi_khoang_thang_giua_cau_va_giai_doan_thu_thap_tu_g1(tmp_path):
    assert SDC._thoi_gian("Dữ liệu 2020-01 đến 2025-12; phân tích 2027-03 đến 2027-09") == (
        "Dữ liệu từ tháng 01/2020 đến tháng 12/2025; phân tích từ tháng 03/2027 đến tháng 09/2027")
    assert SDC._thoi_gian("2027-03 đến 2028-03") == "từ tháng 03/2027 đến tháng 03/2028"
    n = _nguon(tmp_path, "cohort", g1={"data_collection_method": "Thu mới: phỏng vấn trực tiếp theo phiếu"})
    dong = SDC.giai_doan_thu_thap(n)
    assert dong == ("- Giai đoạn thu thập số liệu: trong thời gian nghiên cứu, phỏng vấn trực tiếp theo phiếu; "
                    "ban đầu, tháng 3 và tháng 6.")
    van = SDC.dung_de_cuong(n)
    assert "Hướng thu thập số liệu: tiến cứu" in van  # G2 recruitment_mode PROSPECTIVE_NEW_PARTICIPANTS


def test_thieu_che_do_tuyen_thi_strobe_4_thieu_huong_thoi_gian(tmp_path):
    van = _van(tmp_path, "cohort", g2={"recruitment_mode": None})
    assert "Hướng thu thập số liệu" not in van
    assert _thieu(van, "cohort").get(("STROBE 2007", "4")) == ["hướng thời gian"]


# ───────────────────────────────────────── STROBE 6a/6b: bệnh–chứng
def test_benh_chung_ly_do_lay_tu_menh_de_pi_viet_khong_bia(tmp_path):
    n = _nguon(tmp_path, "case_control")
    dong = SDC.nhom_benh_chung(n)
    assert dong[2] == ("- Lý do chọn nhóm bệnh và nhóm chứng: Để nhóm chứng đại diện cho quần thể nguồn sinh ra ca.")
    assert "để nhóm chứng" not in dong[1]  # mệnh đề lý do được tách khỏi dòng nguồn chọn chứng
    # PI chưa viết lý do ⇒ ô trống, và K17 vẫn báo thiếu đúng yếu tố (không nhận nhãn của ô trống)
    van = _van(tmp_path / "b", "case_control", g1={"control_source": "Người khám ngoại trú cùng tuần"})
    assert f"- Lý do chọn nhóm bệnh và nhóm chứng: {CHAM}" in van
    assert _thieu(van, "case_control").get(("STROBE 2007", "6a")) == ["lý do chọn ca và chứng"]


def test_benh_chung_nam_trong_muc_doi_tuong_va_ghep_cap_khong_nhan_tu_nhan(tmp_path):
    van = _van(tmp_path, "case_control")
    assert re.search(r"^### 4\.\d+\.3\. Nhóm bệnh và nhóm chứng$", van, re.M)
    assert "Định nghĩa nhóm bệnh và nhóm chứng" not in van
    # nhãn dòng không chứa «ghép cặp» ⇒ đề tài không ghép thì 6b/12d không bị đòi
    kq = {r.ma: r.trang_thai for r in KCM.doi_chieu(van, "case_control")["ket_qua"] if r.chuan == "STROBE 2007"}
    assert kq["6b"] == "khong_ap_dung" and kq["12d"] == "khong_ap_dung"
    ghep = _van(tmp_path / "g", "case_control", g1={
        "control_source": "Người khám cùng tuần, ghép theo giới, tỷ lệ 2 chứng : 1 ca, để nhóm chứng đại diện cho "
                          "quần thể nguồn"})
    kq = {r.ma: r.trang_thai for r in KCM.doi_chieu(ghep, "case_control")["ket_qua"] if r.chuan == "STROBE 2007"}
    assert kq["6b"] == "dat"  # tiêu chí ghép + số chứng mỗi ca từ CHÍNH dòng nguồn chọn chứng
    assert kq["12d"] == "thieu"  # SAP của fixture không phân tích có điều kiện ⇒ phải báo


# ───────────────────────────────────────── STROBE 7–8: biến điều chỉnh tác động, đo lường như nhau
def test_bien_dieu_chinh_tac_dong_tu_sap_muc_7(tmp_path):
    d = _de_tai(tmp_path, "cohort")
    sap = d / f"G4_A5_SAP_FINAL_{MA}.md"
    sap.write_text(sap.read_text(encoding="utf-8") + "\n### §7 PHÂN TÍCH NHÓM NHỎ (Subgroup Analysis)\n\n"
                   "- **Nhóm nhỏ tiền định:** Giới (nam/nữ) — ghi trước khi xem dữ liệu\n"
                   "- **Kiểm định tương tác:** Mô hình với interaction term\n", encoding="utf-8", newline="\n")
    n = SDC.Nguon(d, MA)
    assert SDC.bien_dieu_chinh_tac_dong(n) == [
        "- Biến điều chỉnh tác động (phân nhóm tiền định, đánh giá bằng số hạng tương tác): Giới (nam/nữ)."]
    assert ("STROBE 2007", "7") not in _thieu(SDC.dung_de_cuong(n), "cohort")
    # SAP khai không phân tích nhóm nhỏ ⇒ không có dòng
    sap.write_text(sap.read_text(encoding="utf-8").replace("Giới (nam/nữ) — ghi trước khi xem dữ liệu",
                                                           "Không có phân tích nhóm nhỏ"), encoding="utf-8",
                   newline="\n")
    assert SDC.bien_dieu_chinh_tac_dong(SDC.Nguon(d, MA)) == []


def test_do_luong_nhu_nhau_va_chat_luong_do_tu_g1(tmp_path):
    dong = SDC.do_luong_nhu_nhau(_nguon(tmp_path, "cohort"))
    assert dong[0] == ("- Bảo đảm chất lượng đo lường: Đo huyết áp chuẩn hoá bằng cùng một quy trình cho mọi người "
                       "tham gia.")
    assert dong[-1].startswith("- Đo lường như nhau giữa các nhóm: nhóm phơi nhiễm và nhóm không phơi nhiễm")
    assert SDC.do_luong_nhu_nhau(_nguon(tmp_path / "c", "cross_sectional", g1={"critical_to_quality": None})) == []


# ───────────────────────────────────────── STROBE 9/19: sai lệch và chiều ảnh hưởng — không đoán thay PI
def test_khong_co_so_sai_lech_thi_chieu_de_trong_va_k17_bao(tmp_path):
    van = _van(tmp_path, "cohort", g1={"bias_controls": []})
    assert f"- Chiều ảnh hưởng dự kiến của từng nguồn sai lệch: {CHAM}" in van
    assert ("STROBE 2007", "19") in _thieu(van, "cohort")
    # sổ có hàng nhưng ô chiều trống ⇒ bảng in ô trống, K17 vẫn báo
    van2 = _van(tmp_path / "b", "cohort",
                g1={"bias_controls": [{"sai_lech": "Sai lệch chọn", "bien_phap": "Tập huấn"}]})
    assert f"| Sai lệch chọn | {CHAM} | Tập huấn. |" in van2
    assert ("STROBE 2007", "19") in _thieu(van2, "cohort")


# ───────────────────────────────────────── STROBE 12d: mất theo dõi
def test_xu_ly_mat_theo_doi_ghep_tu_quyet_dinh_da_chot(tmp_path):
    n = _nguon(tmp_path, "cohort", g1={"exclusion_criteria": [
        "Gãy xương trong 12 tháng trước ngày bắt đầu theo dõi", "Theo dõi <6 tháng"]})
    dong = SDC.xu_ly_mat_theo_doi(n)
    assert dong[0].startswith("- Xử lý mất theo dõi: loại khỏi mẫu: theo dõi <6 tháng")
    assert "gãy xương" not in dong[0]  # tiêu chí bệnh trước đó chỉ tình cờ chứa chữ «theo dõi»
    assert "gán đa trị" in dong[0]  # SAP §6 đưa chính biến kết cục chính vào kế hoạch dữ liệu thiếu
    assert SDC.xu_ly_mat_theo_doi(_nguon(tmp_path / "r", "rct")) == []  # chỉ thuần tập / dự báo
    (tmp_path / "t").mkdir()
    d = _de_tai(tmp_path / "t", "cohort")
    (d / f"G4_A5_SAP_FINAL_{MA}.md").write_text("# SAP\n", encoding="utf-8", newline="\n")
    assert SDC.xu_ly_mat_theo_doi(SDC.Nguon(d, MA)) == [f"- Xử lý mất theo dõi: {CHAM}"]


# ───────────────────────────────────────── STROBE 22 · RECORD 12.2 · RECORD 22.1
def test_kinh_phi_chia_se_tu_khai_bao_g9_vang_thi_o_trong(tmp_path):
    n = _nguon(tmp_path, "cohort")
    assert SDC.kinh_phi_tai_tro(n) == ("- Nguồn kinh phí và vai trò của đơn vị tài trợ: kinh phí đơn vị cấp; đơn vị "
                                       "cấp kinh phí không tham gia thiết kế, phân tích hay quyết định công bố.")
    assert SDC.chia_se_tai_lieu(n).endswith("chia sẻ theo yêu cầu hợp lý gửi chủ nhiệm.")
    (n.out / "G9_PUBLICATION_READINESS.json").unlink()
    assert SDC.kinh_phi_tai_tro(n) == f"- Nguồn kinh phí và vai trò của đơn vị tài trợ: {CHAM}; {CHAM}."
    assert SDC.chia_se_tai_lieu(n) == f"- Khả năng tiếp cận đề cương, dữ liệu và mã phân tích: {CHAM}"
    van = SDC.dung_de_cuong(n)
    assert ("STROBE 2007", "22") in _thieu(van, "cohort")


def test_lam_sach_dem_tu_tu_dien_du_lieu(tmp_path):
    dong = SDC.lam_sach_so_lieu(_nguon(tmp_path, "cohort"))
    assert dong == ("- Làm sạch số liệu: trước khi khoá dữ liệu, kiểm tra miền giá trị hợp lệ của 1 biến theo từ điển "
                    "dữ liệu (Phụ lục D); giá trị ngoài phạm vi hoặc để trống được tạo truy vấn.")


# ───────────────────────────────────────── RECORD 6.1/6.2/19.1 — chỉ khi dữ liệu thường quy
def test_dieu_kien_loc_va_doi_chieu_ma_chi_khi_lay_tu_co_so_du_lieu(tmp_path):
    g1 = {"recruitment_strategy": "Trích toàn bộ hồ sơ đủ tiêu chuẩn từ cơ sở dữ liệu ngoại trú",
          "data_collection_method": "Trích hồ sơ bệnh án điện tử theo phiếu",
          "primary_outcome": {"name": "Gãy xương", "measure": "Mã ICD-10 S72 có phim xác nhận", "timepoint": "3 năm"},
          "critical_to_quality": "Kiểm 10% hồ sơ biến cố bằng phim X-quang"}
    n = _nguon(tmp_path, "cohort", g1=g1)
    assert SDC.dieu_kien_loc(n) == ["- Điều kiện lọc hồ sơ trên cơ sở dữ liệu: tuổi ≥18; đang dùng thuốc hạ áp; loại "
                                    "hồ sơ có: không đọc được tin nhắn."]
    assert SDC.kiem_dinh_ma(n) == ["- Đối chiếu cách xác định bằng mã với hồ sơ gốc: kiểm 10% hồ sơ biến cố bằng phim "
                                   "X-quang."]
    van = SDC.dung_de_cuong(n)
    assert "- Hệ quả của dữ liệu thu thập thường quy: dữ liệu" in van and SDC.DAU_THUONG_QUY not in van
    assert "mã chẩn đoán" in van.split("Hệ quả của dữ liệu thu thập thường quy")[1].split("\n")[0]
    # tuyển mới (fixture gốc) ⇒ không có các dòng RECORD
    goc = _nguon(tmp_path / "goc", "cohort")
    assert SDC.dieu_kien_loc(goc) == [] and SDC.kiem_dinh_ma(goc) == []
    assert "Hệ quả của dữ liệu thu thập thường quy" not in SDC.dung_de_cuong(goc)


# ───────────────────────────────────────── STROBE 18/21: bàn luận theo mục tiêu, phạm vi suy rộng
def test_ban_luan_theo_muc_tieu_va_suy_rong_dung_quyet_dinh(tmp_path):
    van = _van(tmp_path, "cross_sectional")
    assert re.search(r"^## 5\.\d+\. Dự kiến bàn luận$", van, re.M)
    assert re.search(r"^### 5\.\d+\.1\. Bàn luận theo mục tiêu 1$", van, re.M)
    bl = re.search(r"Bàn luận kết quả trả lời mục tiêu 1 .*", van).group(0)
    assert "Bảng 5." in bl  # nêu đúng bảng/biểu đồ gắn «(Mục tiêu 1)»
    assert re.search(r"^## 5\.\d+\. Hạn chế của nghiên cứu và phạm vi suy rộng kết quả$", van, re.M)
    sr = re.search(r"- Phạm vi suy rộng: .*", van).group(0)
    assert "người tăng huyết áp điều trị ngoại trú" in sr and "phòng khám ngoại trú bệnh viện" in sr
    assert "# 4." in van and "Hạn chế của nghiên cứu\n" not in van.split("# 5.")[0]  # không còn ở chương 4


def test_khuon_bvqy175_giu_ban_luan_cua_bo_sinh_khong_nhan_doi(tmp_path):
    van = KDC.chuyen(_van(tmp_path, "cohort")).md
    assert len(re.findall(r"^#+ .*Dự kiến bàn luận$", van, re.M)) == 1  # một mục bàn luận trong thân bài
    assert len(re.findall(r"^#+ .*Bàn luận theo mục tiêu 1$", van, re.M)) == 1
    assert "@@BAN_LUAN" not in van
    assert KCM.loi_k17(van, "cohort") == []


# ───────────────────────────────────────── TT43 Điều 7 khoản 1 điểm b: căn cứ đã đối chiếu, «đoạn» thay «§»
def test_mien_dong_thuan_dan_tt43_dieu_7_va_can_cu_khong_co_ky_hieu_doan(tmp_path):
    assert "§" not in CCDD.CAN_CU_MIEN_DONG_THUAN_VAN_BAN_NOP
    assert "đoạn 32" in CCDD.CAN_CU_MIEN_DONG_THUAN_VAN_BAN_NOP
    assert "Điều 7 khoản 1 điểm b" in CCDD.CAN_CU_MIEN_DONG_THUAN_VAN_BAN_NOP
    van = _van(tmp_path, "cohort",
               g2={"icf_waiver_requested": True, "recruitment_mode": "RETROSPECTIVE_SECONDARY_DATA"})
    assert "theo Thông tư 43/2024/TT-BYT, Điều 7 khoản 1 điểm b" in van
    assert f"Căn cứ đề nghị: {CCDD.CAN_CU_MIEN_DONG_THUAN_VAN_BAN_NOP}" in van
    kq = {r.ma: r.trang_thai for r in KCM.doi_chieu(van, "cohort")["ket_qua"] if r.chuan == "Việt Nam"}
    assert kq["TT43-Đ7.1b"] == "dat" and kq["TT43-ĐỒNG-THUẬN"] == "khong_ap_dung"


# ───────────────────────────────────────── khung biểu bảng: STROBE 13b/14b/14c/15 · RECORD 13.1
import khung_bieu_bang as KBB  # noqa: E402
from test_khung_bieu_bang_20261119 import _ngu_canh  # noqa: E402


def test_khung_thuan_tap_bang_bien_co_thoi_gian_theo_doi_va_cot_so_thieu():
    ctx = _ngu_canh("cohort")
    khong_tg = KBB._bang_bien_co(ctx)
    assert khong_tg is not None and "Tổng thời gian theo dõi (người-năm)" not in khong_tg.cot
    ctx.bien["tg"] = KBB.Bien("tg", "Thời gian theo dõi (tháng)", "lien_tuc", [], "tháng")
    bang = KBB._bang_bien_co(ctx)
    assert bang.ten.startswith("Số biến cố và nguy cơ tích luỹ của kiểm soát huyết áp")
    assert bang.cot[-1] == "Tỷ suất mới mắc /1.000 người-năm (KTC 95%)"
    assert any("KTC: khoảng tin cậy" in g for g in bang.ghi_chu)
    dac = KBB._bang_dac_diem(ctx)
    assert dac.cot[-1] == "Số thiếu, n (%)"
    assert any(d[0].startswith("Thời gian theo dõi (tháng), trung vị [KTPV]") for d in dac.dong)
    assert any("thiếu dữ liệu của từng biến" in g for g in dac.ghi_chu)
    assert KBB._bang_bien_co(_ngu_canh("case_control")) is None  # chỉ thuần tập


def test_khung_so_do_ghi_chu_neu_cac_ly_do_loai_cua_chinh_so_do():
    ctx = _ngu_canh("cohort")
    ctx.hoi_cuu = True
    ghi = " ".join(KBB._so_do(ctx).ghi_chu)
    assert "không đủ tiêu chuẩn chọn hoặc thuộc tiêu chuẩn loại trừ" in ghi
    assert "thiếu dữ liệu kết cục chính" in ghi and "mất theo dõi" in ghi
    assert "(n = …)" not in ghi
