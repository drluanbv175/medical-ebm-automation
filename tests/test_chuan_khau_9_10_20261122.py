"""Kiểm toàn hệ 11 khâu (bác sĩ 22/11/2026) — hai khoảng hở đo được trên 24 đề tài giả lập:

- KHÂU 9 (phân tích/trình bày): 22/24 kịch bản thiếu HÌNH BẮT BUỘC của chuẩn báo cáo (sơ đồ luồng CONSORT/STROBE/
  STARD/PRISMA/TRIPOD+AI) vì giả lập không điền sổ sàng lọc — cổng phán vẫn xanh. Nay vai nghiên cứu viên giả lập
  điền sổ sàng lọc mô phỏng (`TronVong._dien_so_do_luong`) qua ĐÚNG bộ kiểm số học của hệ, và cổng phán đỏ khi thiếu.
- KHÂU 10 (diễn giải/bàn luận): bản diễn giải G6.5 chỉ bị đòi chữ «hạn chế» — 11/24 không bàn khả năng khái quát,
  11/24 không nêu nguồn sai lệch, gần như không bản quan sát nào nói hướng sai lệch (STROBE 19). Nay
  `dien_giai_ket_qua.kiem_han_che_khai_quat` đối chiếu theo chuẩn của từng thiết kế.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import bieu_do_bao_cao as BB  # noqa: E402
import dien_giai_ket_qua as DG  # noqa: E402
import gia_lap_tron_vong as TV  # noqa: E402
import hinh_g6 as HG6  # noqa: E402
import ve_bieu_do as VB  # noqa: E402

# ── KHÂU 10: hạn chế & khả năng khái quát theo chuẩn của thiết kế ────────────────────────────────────────────────────
DAT = {
    "rct": ("Hạn chế: không làm mù người tham gia nên có thể có sai lệch thực hiện.",
            "Kết quả khái quát cho người bệnh ngoại trú ở cơ sở tương tự."),
    "cohort": ("Hạn chế: nhiễu tồn dư có thể làm ước lượng cao hơn thực.", "Kết quả khái quát cho người từ 60 tuổi."),
    "case_control": ("Hạn chế: sai lệch nhớ lại thường làm ước tính cao mối liên quan.",
                     "Chỉ khái quát cho người cao tuổi."),
    "cross_sectional": ("Hạn chế: sai lệch chọn có thể làm ước tính cao tỷ lệ kiểm soát.",
                        "Khái quát cho cơ sở tương tự."),
    "diagnostic": ("Hạn chế: KTC rộng do ít người có bệnh.", "Khả năng khái quát cho cộng đồng còn hạn chế."),
    "prediction": ("Hạn chế: C-statistic trong mẫu còn lạc quan.", "Chưa kiểm định ngoài."),
    "sr_ma": ("Hạn chế: nguy cơ sai lệch của nghiên cứu được đưa vào; chiến lược tìm giới hạn ngôn ngữ.", ""),
    "qualitative": ("Hạn chế: vai trò của người phỏng vấn có thể ảnh hưởng độ tin cậy.",
                    "Khả năng chuyển giao giới hạn ở bối cảnh tương tự."),
}


@pytest.mark.parametrize("tk", sorted(DAT))
def test_khau10_ban_du_noi_dung_chuan_dat(tk):
    m4, m5 = DAT[tk]
    assert DG.kiem_han_che_khai_quat(m4, m5, tk) == []


@pytest.mark.parametrize("tk, m4, m5, cum", [
    ("rct", "Hạn chế: một cơ sở.", "Kết quả khái quát cho cơ sở tương tự.", "CONSORT 2025 mục 30"),
    ("rct", "Hạn chế: không làm mù.", "Hướng tiếp: thử nghiệm đa trung tâm.", "khả năng khái quát"),
    ("cohort", "Hạn chế: nhiễu tồn dư.", "Khái quát cho người từ 60 tuổi.", "hướng hoặc độ lớn"),
    ("case_control", "Hạn chế: một bệnh viện.", "Khái quát cho người cao tuổi.", "nguồn sai lệch"),
    ("cross_sectional", "Hạn chế: sai lệch chọn có thể làm ước tính cao.", "Hướng tiếp: theo dõi dọc.",
     "STROBE mục 21"),
    ("diagnostic", "Hạn chế: một cơ sở.", "Khả năng khái quát hạn chế.", "STARD 2015 mục 26"),
    ("prediction", "Hạn chế: một cơ sở.", "Chưa kiểm định ngoài.", "TRIPOD+AI mục 26"),
    ("sr_ma", "Hạn chế: chiến lược tìm giới hạn ngôn ngữ.", "", "PRISMA 2020 mục 23b"),
    ("sr_ma", "Hạn chế: nguy cơ sai lệch của nghiên cứu được đưa vào cao.", "", "PRISMA 2020 mục 23c"),
    ("qualitative", "Hạn chế: một cơ sở.", "Khả năng chuyển giao giới hạn.", "SRQR mục 19"),
    ("qualitative", "Hạn chế: vai trò người phỏng vấn ảnh hưởng độ tin cậy.", "Hướng tiếp: can thiệp.", "SRQR mục 18"),
])
def test_khau10_thieu_noi_dung_chuan_bi_bat(tk, m4, m5, cum):
    loi = DG.kiem_han_che_khai_quat(m4, m5, tk)
    assert any(cum in x for x in loi), loi


def test_khau10_khong_suy_duoc_thiet_ke_la_loi_khong_phai_dat():
    """Không đo được ≠ đạt (CLAUDE.md §0.2): thiết kế lạ/vắng ⇒ báo lỗi, không im lặng xanh."""
    for tk in (None, "", "mixed"):
        loi = DG.kiem_han_che_khai_quat("Hạn chế: sai lệch chọn.", "khái quát", tk)
        assert loi and "không xác định được thiết kế" in loi[0], (tk, loi)


def test_khau10_khai_quat_o_muc_5_cung_tinh_nhung_han_che_phai_o_muc_4():
    assert DG.kiem_han_che_khai_quat("Hạn chế: không làm mù.", "Kết quả khái quát cho cơ sở tương tự.", "rct") == []
    loi = DG.kiem_han_che_khai_quat("Hạn chế: một cơ sở.", "Không làm mù nên có sai lệch.", "rct")
    assert any("mục 4 chưa bàn nguồn sai lệch" in x for x in loi), loi


def test_khau10_kiem_day_du_noi_luat_moi(tmp_path):
    """Luật mới chạy TRONG `kiem` (không chỉ là hàm rời): bản diễn giải thiếu hướng sai lệch ⇒ `kiem` báo."""
    out = tmp_path / "ZZ"
    van = DG.sinh_mau("ZZ", out).read_text(encoding="utf-8")
    loi = DG.kiem("ZZ", out, "cohort")
    assert any("[CẦN" in x for x in loi)  # khung chưa điền vẫn bị chặn như cũ
    van = van.replace(van[van.find(DG.MUC[3]):van.find(DG.MUC[4])], f"{DG.MUC[3]}\n\nHạn chế: nhiễu tồn dư.\n\n")
    (out / "G6_DIEN_GIAI_ZZ.md").write_text(van, encoding="utf-8", newline="\n")
    assert any("hướng hoặc độ lớn" in x for x in DG.kiem("ZZ", out, "cohort"))


def test_khau10_moi_kich_ban_gia_lap_dat_chuan_han_che():
    """27 kịch bản giả lập (gốc + khó + chân thực; 23/11/2026 thêm bệnh–chứng ghép cặp cá thể và hai biến thể — giá trị
    thiếu, biến cố hiếm) phải viết mục 4–5 đạt chuẩn của thiết kế — văn bản này chảy vào ô «hạn chế»/«tác động thực
    hành» của bản thảo G7."""
    kb = {**TV.GL.KICH_BAN, **TV._kich_ban_kho()}
    assert len(kb) == 27
    truot = {}
    for ma, v in kb.items():
        dg = (v.get("ho_so_tron_vong") or {}).get("dien_giai") or {}
        loi = DG.kiem_han_che_khai_quat(dg.get("muc_4", ""), dg.get("muc_5", ""), v.get("thiet_ke"))
        if loi:
            truot[ma] = loi
    assert truot == {}


# ── KHÂU 9: sổ sàng lọc mô phỏng ⇒ sơ đồ luồng bắt buộc ───────────────────────────────────────────────────────────────
def _tv(tmp_path, ma, n_ds, n_total, cot=None):
    tv = TV.TronVong(ma, tmp_path / "repo")
    tv.out.mkdir(parents=True)
    tv.du_lieu = {"n": n_ds}
    tk = VB.BI_DANH.get(tv.thiet_ke, tv.thiet_ke)
    VB.ghi_mau_so_do_luong(tk, tv.out / HG6.TEP_LUONG.format(study=tv.study))
    (tv.out / "G6_SAP_ket_qua.json").write_text(json.dumps(
        {"phan_tich": [{"vai": "chinh", "uoc_luong": {"n_total": n_total} if n_total else None}]}),
        encoding="utf-8", newline="\n")
    if cot:
        ten, so1 = cot
        (tv.out / "05_clean_locked").mkdir()
        with (tv.out / "05_clean_locked" / "df_clean.abc.csv").open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["record_id", ten])
            for i in range(n_ds):
                w.writerow([f"R{i}", 1 if i < so1 else 0])
    return tv


def _doc(tv):
    with (tv.out / HG6.TEP_LUONG.format(study=tv.study)).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


DT = {"phan_tich": [{"vai": "chinh", "tham_so": {"group": "nhom", "outcome": "ca_benh"}}]}


@pytest.mark.parametrize("ma, n_ds, n_total, cot", [
    ("rct_nhi_phan", 218, 218, ("nhom", 110)),
    ("benh_chung", 577, 577, ("ca_benh", 190)),
    ("cat_ngang_mo_ta", 400, 391, None),
    ("thuan_tap_phoi_nhiem", 900, 900, None),
    ("chan_doan", 53, None, None),
    ("mo_hinh_du_bao", 600, 600, None),
    ("tong_quan_gop", 15, None, None),
    ("dinh_tinh", 20, None, None),
])
def test_khau9_so_sang_loc_mo_phong_dung_so_hoc_va_n_phan_tich(tmp_path, ma, n_ds, n_total, cot):
    tv = _tv(tmp_path, ma, n_ds, n_total, cot)
    assert tv._dien_so_do_luong(DT) is True
    dong = _doc(tv)
    assert all(str(r["n"]).strip() for r in dong), dong
    k = BB.kiem_so_hoc_luong(dong)
    assert k["loi"] == [], k["loi"]                                     # cùng bộ kiểm số học của G6
    assert HG6._n_cuoi_luong(k["nhanh"]) == (n_total or n_ds)           # hộp cuối = n phân tích chính G6
    for r in dong:                                                      # lý do có số, cộng khớp (đã kiểm ở trên)
        if r["loai"] == "loai" and r["ly_do"]:
            assert all(":" in x and x.split(":")[1].strip().isdigit() for x in r["ly_do"].split(";")), r
    assert tv._dien_so_do_luong(DT) is False                            # không ghi đè sổ đã có số
    assert tv.buoc and "sổ sàng lọc" in tv.buoc[-1]["buoc"]


def test_khau9_nhanh_chia_theo_du_lieu_khoa(tmp_path):
    tv = _tv(tmp_path, "rct_nhi_phan", 218, 218, ("nhom", 110))
    tv._dien_so_do_luong(DT)
    cuoi = {r["nhanh"]: int(r["n"]) for r in _doc(tv) if r["buoc"] == "Đưa vào phân tích"}
    assert cuoi == {"Can thiệp": 110, "Chứng": 108}
    tv = _tv(tmp_path / "b", "benh_chung", 577, 577, ("ca_benh", 190))
    tv._dien_so_do_luong(DT)
    cuoi = {r["nhanh"]: int(r["n"]) for r in _doc(tv) if r["buoc"] == "Đưa vào phân tích"}
    assert cuoi == {"Ca bệnh": 190, "Chứng": 387}


def test_khau9_cat_ngang_loai_khoi_phan_tich_bang_dung_so_thieu_cua_du_lieu(tmp_path):
    tv = _tv(tmp_path, "cat_ngang_mo_ta", 400, 391)
    tv._dien_so_do_luong(DT)
    n = {r["buoc"]: int(r["n"]) for r in _doc(tv)}
    assert n["Tham gia nghiên cứu"] == 400 and n["Loại khỏi phân tích"] == 9 and n["Đưa vào phân tích"] == 391


def test_khau9_khong_co_mau_thi_khong_dien(tmp_path):
    tv = TV.TronVong("rct_nhi_phan", tmp_path / "repo")
    tv.out.mkdir(parents=True)
    tv.du_lieu = {"n": 10}
    assert tv._dien_so_do_luong(DT) is False


def test_khau9_nhan_chuan_so_do_luong_hien_hanh():
    """Nhãn RCT là CONSORT 2025 (không còn CONSORT 2010); STROBE ghi rõ 13a–b bắt buộc, 13c chỉ «cân nhắc»."""
    assert VB.DANH_MUC["rct"]["chuan"].startswith("CONSORT 2025")
    assert "2010" not in VB.DANH_MUC["rct"]["chuan"]
    for tk in ("cohort", "case_control", "cross_sectional"):
        assert "13a–b" in VB.DANH_MUC[tk]["chuan"] and "cân nhắc" in VB.DANH_MUC[tk]["chuan"]
        assert "so_do_luong" in VB.DANH_MUC[tk]["bat_buoc"]


# ── Ô «§5 Hạn chế» của bản thảo G7 (phiên K18 đo 22/11/2026) ─────────────────────────────────────────────────────────
_O_HAN_CHE = ("**§5 Hạn chế (Limitations):**  \n"
              "[CẦN — liệt kê hạn chế cụ thể của thiết kế và thực hiện nghiên cứu này.  \n"
              "Ví dụ với Thuần tập: thiếu ngẫu nhiên hóa có thể có confounding chưa đo được; LTFU có thể không ngẫu "
              "nhiên...]  \n")


@pytest.mark.parametrize("tk", ["cohort", "case_control", "cross_sectional", "rct"])
def test_o_han_che_g7_nhan_cau_tra_loi_tac_gia_khong_bi_vi_du_danh_lua(tk):
    """Chữ «ngẫu nhiên hóa» trong câu VÍ DỤ của khuôn không biến ô hạn chế thành ô «chỉ áp dụng cho RCT»."""
    o = TV.phan_loai_o(_O_HAN_CHE, "G7", "G7.md", {}, {}, tk, [(r"liet ke han che", "HẠN_CHẾ")], {})
    assert [(x["loai"], x["dien"]) for x in o] == [("moi_dung_vai", "HẠN_CHẾ")]


def test_o_that_su_chi_rct_van_khong_ap_dung_cho_quan_sat():
    o = TV.phan_loai_o("Phân tích giữa kỳ: [CẦN — kế hoạch phân tích giữa kỳ và DMC]\n", "G7", "G7.md", {}, {},
                       "cohort", [], {})
    assert o[0]["loai"] == "khong_ap_dung" and "thử nghiệm ngẫu nhiên" in o[0]["dien"]
