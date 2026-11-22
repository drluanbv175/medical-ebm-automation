"""`khung_bieu_bang.py --nang-cap` tái lập được và vẽ lại hình đã có khi nguồn đổi (bác sĩ 22/11/2026: «Đảm bảo đề
cương hoàn thiện từng chữ, câu, bảng, đồ thị… đúng chuẩn đề cương nghiên cứu y khoa»).

Đo trước khi vá trên đề cương C1a thật:
  1. Chạy lần hai trên chương đã nâng cấp ⇒ ghi chú chép trùng «*Ghi chú:* Chữ viết tắt — KTC: khoảng tin cậy.
     * Chữ viết tắt — KTC: khoảng tin cậy; BHYT: …» và thêm một dòng trống sau mỗi bảng (`cu.strip("*")` còn sót
     «Ghi chú:*»).
  2. Biểu đồ đã có không bao giờ được vẽ lại: Biểu đồ 3.2 C1a vẫn là forest các biến hiệu chỉnh của SAP cũ dù
     tên/ghi chú đã là «mô hình chính và các kịch bản độ nhạy»; Hình 3.1 vẫn là quy trình chọn mẫu trước quyết định
     hội đồng.
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import khung_bieu_bang as KBB  # noqa: E402


def _ngu_canh(luong=None) -> KBB.NguCanh:
    bien = {
        "kq": KBB.Bien("kq", "Hài lòng chung", "thu_tu", [("1", "Rất không hài lòng"), ("5", "Rất hài lòng")]),
        "cho": KBB.Bien("cho", "Thời gian chờ", "lien_tuc", [], "phút"),
        "gioi": KBB.Bien("gioi", "Giới", "nhi_phan", [("1", "Nam"), ("2", "Nữ")]),
        "a": KBB.Bien("a", "Điểm lĩnh vực A", "lien_tuc", [], "", (1.0, 5.0)),
        "b": KBB.Bien("b", "Điểm lĩnh vực B", "lien_tuc", [], "", (1.0, 5.0)),
    }
    ma_tran = [
        {"muc_tieu": "1", "khai_niem": "điểm lĩnh vực A", "vai_tro": "mo_ta", "bien": "a", "kieu": "lien_tuc"},
        {"muc_tieu": "1", "khai_niem": "điểm lĩnh vực B", "vai_tro": "mo_ta", "bien": "b", "kieu": "lien_tuc"},
        {"muc_tieu": "2", "khai_niem": "hài lòng chung", "vai_tro": "ket_cuc_chinh", "bien": "kq", "kieu": "thu_tu"},
        {"muc_tieu": "2", "khai_niem": "thời gian chờ", "vai_tro": "phoi_nhiem", "bien": "cho", "kieu": "lien_tuc"},
        {"muc_tieu": "2", "khai_niem": "giới", "vai_tro": "hiep_bien", "bien": "gioi", "kieu": "nhi_phan"},
    ]
    pt = [{"id": "MT2_chinh", "vai": "chinh", "mo_ta": "Chính",
           "tham_so": {"outcome": "kq", "group": "cho", "covariates": ["gioi"], "outcome_type": "ordinal"}}]
    return KBB.NguCanh("cross_sectional", ["Mô tả mức hài lòng", "Phân tích yếu tố liên quan đến hài lòng"], bien,
                       ma_tran, pt, 1000, False, list(luong or []))


BANG_DN = ("**Bảng 5.4. Kết quả phân tích độ nhạy**\n\n"
           "| Phân tích | n | Ước lượng (KTC 95%) | So với phân tích chính |\n"
           "|---|---|---|---|\n"
           "| Điền khuyết đa lần (20 bộ dữ liệu) cho biến nền | … | … (… – …) | cùng chiều / khác chiều |\n"
           "| Hồi quy tuyến tính trên G1 coi là biến liên tục, sai số chuẩn vững HC3 | … | … (… – …) | cùng chiều |\n"
           "| Ước lượng theo thiết kế: cụm là bàn khám | … | … (… – …) | cùng chiều / khác chiều |\n"
           "| Phân tích giới hạn cho người bỏ về trước khi khám | … | … (… – …) | — |\n\n"
           "*Ghi chú:* Chữ viết tắt — KTC: khoảng tin cậy; HC3: sai số chuẩn vững loại 3. Các phân tích đã định "
           "trước.\n")
BANG_A = ("**Bảng 5.3. Mối liên quan giữa thời gian chờ và hài lòng (Mục tiêu 2)**\n\n"
          "| Yếu tố | Đơn vị | Ước lượng (KTC 95%) | p |\n|---|---|---|---|\n"
          "| Thời gian chờ khám, mô hình thô | Mỗi 15 phút | … (… – …) | … |\n"
          "| **Thời gian chờ khám, mô hình chính (kết quả chính)** | **Mỗi 15 phút** | **… (… – …)** | **…** |\n\n"
          "*Ghi chú:* Chữ viết tắt — KTC: khoảng tin cậy; BHYT: bảo hiểm y tế. Mô hình logistic thứ tự.\n")
GHI_BD = ("*Ghi chú:* Mỗi dòng là một mô hình: mô hình thô, mô hình chính và các kịch bản độ nhạy (không gồm hồi quy "
          "tuyến tính và phân tích giới hạn cho người bỏ về). Chữ viết tắt — OR: tỷ số chênh.")


def _chuong(anh_bd: str = "bieu-bang/bieu-do-5-2.png", ten_bd: str = "Tỷ số chênh chung của thời gian chờ và KTC 95% "
            "trong mô hình chính và các kịch bản độ nhạy (Mục tiêu 2)") -> str:
    return ("# 5. DỰ KIẾN KẾT QUẢ\n\nKết quả trình bày theo mục tiêu.\n\n"
            "Quy ước trình bày: như mục 2.6.\n\n"
            "## 5.1. Kết quả theo mục tiêu 1\n\n"
            "**Bảng 5.1. Đặc điểm chung (n = 1.000)**\n\n| Đặc điểm | TB ± ĐLC | KTC 95% |\n|---|---|---|\n"
            "| Tuổi (năm) | … ± … | … – … |\n\n"
            "*Ghi chú:* Chữ viết tắt — TB: trung bình; ĐLC: độ lệch chuẩn; BHYT: bảo hiểm y tế; HIS: hệ thống thông "
            "tin bệnh viện. Biến định lượng trình bày TB ± ĐLC.\n\n"
            "**Bảng 5.2. Mức hài lòng theo lĩnh vực (Mục tiêu 1)**\n\n| Lĩnh vực | TB ± ĐLC | Tỷ lệ, % (KTC 95%) |\n"
            "|---|---|---|\n| A | … ± … | … (… – …) |\n\n"
            "*Điểm theo thang 1–5.*\n\n"
            "![Biểu đồ 5.1](bieu-bang/bieu-do-5-1.png)\n\n"
            "**Biểu đồ 5.1. Giá trị trung bình các chỉ số chính kèm khoảng tin cậy 95% (Mục tiêu 1)**\n\n"
            "*Ghi chú:* Cột là ước lượng điểm; thanh sai số là KTC 95%.\n\n"
            "## 5.2. Kết quả theo mục tiêu 2\n\n" + BANG_A + "\n"
            f"![Biểu đồ 5.2]({anh_bd})\n\n**Biểu đồ 5.2. {ten_bd}**\n\n" + GHI_BD + "\n\n"
            "## 5.3. Phân tích độ nhạy\n\n" + BANG_DN + "\n# 6. KẾ HOẠCH\n")


def _anh_cu(goc: Path, ten: str) -> Path:
    """Ảnh «cũ» (khung khác nguồn hiện hành) đặt sẵn ở đúng tệp chương tham chiếu."""
    p = goc / KBB.THU_MUC_HINH / ten
    KBB.ve_hinh(KBB.Khung("bieu_do", "", dac_ta={"kieu": "forest", "nhan": ["Tuổi", "Giới: nữ"], "ref": 1.0,
                                                  "log": True, "truc_x": "OR"}), p)
    return p


# ── 1. Tái lập: chạy hai, ba lần giống hệt; chữ viết tắt gộp, không chép trùng ─────────────────────────────────────
def test_nang_cap_tai_lap_va_gop_chu_viet_tat(tmp_path):
    nc = _ngu_canh()
    md = _chuong()
    m1, _ = KBB.nang_cap_chuong(md, nc, tmp_path, True)
    m2, _ = KBB.nang_cap_chuong(m1, nc, tmp_path, True)
    m3, _ = KBB.nang_cap_chuong(m2, nc, tmp_path, True)
    assert m1 == m2 == m3
    ghi = next(x for x in m1.splitlines() if x.startswith("*Ghi chú:* Chữ viết tắt — TB"))
    # thứ tự và định nghĩa sẵn có giữ nguyên (BHYT, HIS riêng của đề tài), KTC tính từ bảng được thêm đúng một lần
    assert ghi == ("*Ghi chú:* Chữ viết tắt — TB: trung bình; ĐLC: độ lệch chuẩn; BHYT: bảo hiểm y tế; HIS: hệ thống "
                   "thông tin bệnh viện; KTC: khoảng tin cậy. Biến định lượng trình bày TB ± ĐLC.")
    assert m1.count("Chữ viết tắt —") == m1.count("*Ghi chú:* Chữ viết tắt —") + GHI_BD.count("Chữ viết tắt —")
    assert ". * Chữ viết tắt" not in m1 and "\n\n\n" not in m1
    # ghi chú nghiêng soạn tay dưới bảng được ghép sau câu chữ viết tắt
    assert "*Ghi chú:* Chữ viết tắt — TB: trung bình; ĐLC: độ lệch chuẩn; KTC: khoảng tin cậy. Điểm theo thang 1–5." \
        in m1


def test_bo_nhan_ghi_chu():
    assert KBB._bo_nhan_ghi_chu("*Ghi chú:* Chữ viết tắt — KTC: khoảng tin cậy.") == \
        "Chữ viết tắt — KTC: khoảng tin cậy."
    assert KBB._bo_nhan_ghi_chu("*Tỷ lệ tính trên người đến khám.*") == "Tỷ lệ tính trên người đến khám."


def test_ghep_ghi_chu_giu_giai_thich_va_khong_trung_khoa():
    cu = "Chữ viết tắt — KTC: khoảng tin cậy; NVYT: nhân viên y tế. Điểm theo thang 1–5."
    ra = KBB._ghep_ghi_chu(["Chỉ số", "TB ± ĐLC", "KTC 95%"], [["A", "…", "…"]], cu)
    assert ra == ["Chữ viết tắt — KTC: khoảng tin cậy; NVYT: nhân viên y tế; TB: trung bình; ĐLC: độ lệch chuẩn.",
                  "Điểm theo thang 1–5."]
    assert KBB._ghep_ghi_chu(["Chỉ số", "TB ± ĐLC", "KTC 95%"], [["A", "…", "…"]], " ".join(ra)) == ra


# ── 2. Vẽ lại hình đã có khi nguồn đổi; không ghi lại khi nguồn không đổi ─────────────────────────────────────────
def test_ve_lai_khi_nguon_doi_va_giu_tep_khi_khong_doi(tmp_path):
    nc = _ngu_canh()
    p2 = _anh_cu(tmp_path, "bieu-do-5-2.png")
    p1 = _anh_cu(tmp_path, "bieu-do-5-1.png")
    cu2, cu1 = p2.read_bytes(), p1.read_bytes()
    bc: list = []
    m1, loi = KBB.nang_cap_chuong(_chuong(), nc, tmp_path, True, bc)
    assert not loi
    assert p2.read_bytes() != cu2 and p1.read_bytes() != cu1, bc
    assert any(x.startswith("vẽ lại Biểu đồ 5.2") and "bảng «Kết quả phân tích độ nhạy»" in x for x in bc)
    assert any(x.startswith("vẽ lại Biểu đồ 5.1") and "khung chuẩn" in x for x in bc)
    # ảnh vẽ lại TRÙNG ảnh dựng trực tiếp từ nguồn hiện hành
    kh, _ = KBB._forest_do_nhay_tu_chuong(KBB._chuong_du_kien(m1, True)[0], GHI_BD, nc)
    KBB.ve_hinh(kh, tmp_path / "doi_chieu.png")
    assert (tmp_path / "doi_chieu.png").read_bytes() == p2.read_bytes()
    # lượt sau: nguồn không đổi ⇒ không ghi lại tệp
    t2 = p2.stat().st_mtime_ns
    bc2: list = []
    KBB.nang_cap_chuong(m1, nc, tmp_path, True, bc2)
    assert p2.stat().st_mtime_ns == t2
    assert any(x.startswith("không đổi Biểu đồ 5.2") for x in bc2)
    assert not list((tmp_path / KBB.THU_MUC_HINH).glob("*.tam-ve-lai.png"))


def test_khong_xac_dinh_nguon_thi_giu_anh_va_bao(tmp_path):
    p = _anh_cu(tmp_path, "bieu-do-5-2.png")
    cu = p.read_bytes()
    bc: list = []
    KBB.nang_cap_chuong(_chuong(ten_bd="Phân bố thời gian chờ theo khung giờ (Mục tiêu 2)"), _ngu_canh(), tmp_path,
                        True, bc)
    assert p.read_bytes() == cu
    assert any(x.startswith("giữ nguyên Biểu đồ 5.2") and "không xác định được nguồn" in x for x in bc)


def test_khong_ghi_de_ngoai_thu_muc_hinh(tmp_path):
    ngoai = tmp_path / "anh.png"
    KBB.ve_hinh(KBB.Khung("bieu_do", "", dac_ta={"kieu": "roc"}), ngoai)
    cu = ngoai.read_bytes()
    bc: list = []
    KBB.nang_cap_chuong(_chuong(anh_bd="anh.png"), _ngu_canh(), tmp_path, True, bc)
    assert ngoai.read_bytes() == cu and any("ngoài thư mục" in x for x in bc)


def test_forest_do_nhay_lay_dung_dong_cua_chuong():
    dong = (BANG_A + "\n" + BANG_DN).splitlines()
    kh, nguon = KBB._forest_do_nhay_tu_chuong(dong, GHI_BD, _ngu_canh())
    assert kh.dac_ta["nhan"] == ["Mô hình thô", "Mô hình chính (kết quả chính)", "Điền khuyết đa lần",
                                 "Ước lượng theo thiết kế"]
    assert kh.dac_ta["ref"] == 1.0 and kh.dac_ta["log"] is True
    assert kh.dac_ta["truc_x"] == "Tỷ số chênh chung (KTC 95%)"
    # ghi chú loại một phân tích không có trong bảng ⇒ không vẽ bừa
    kh2, ly_do = KBB._forest_do_nhay_tu_chuong(dong, GHI_BD.replace("hồi quy tuyến tính", "mô hình Bayes"),
                                               _ngu_canh())
    assert kh2 is None and "mô hình bayes" in ly_do


def test_nhan_ngan():
    assert KBB._nhan_ngan("**Điền khuyết đa lần (20 bộ dữ liệu) cho biến nền**") == "Điền khuyết đa lần"
    assert KBB._nhan_ngan("Có và không có trọng số hậu phân tầng") == "Có và không có trọng số hậu phân tầng"
    assert KBB._nhan_ngan("Tập phân tích mở rộng: mọi phiếu có G1") == "Tập phân tích mở rộng"


# ── 3. Sơ đồ chọn từ sổ sơ đồ luồng của đề tài (khuôn ve_bieu_do.py mau-so-do-luong) ─────────────────────────────
LUONG = [
    {"buoc": "Số thứ tự được chọn", "n": "", "loai": "chinh", "nhanh": "", "ly_do": ""},
    {"buoc": "Không vào buồng khám", "n": "", "loai": "loai", "nhanh": "", "ly_do": "Bỏ về trước khi khám: "},
    {"buoc": "Hoàn thành lượt khám", "n": "", "loai": "chinh", "nhanh": "", "ly_do": ""},
    {"buoc": "Không được mời", "n": "12", "loai": "loai", "nhanh": "",
     "ly_do": "Không đủ tiêu chuẩn: 7; Không gặp được để mời: 5"},
    {"buoc": "Phiếu hợp lệ đưa vào phân tích", "n": "", "loai": "chinh", "nhanh": "", "ly_do": ""},
]


def test_so_do_tu_so_luong_rieng():
    kh = KBB._so_do(_ngu_canh(LUONG))
    assert [b[0].split(" (n =")[0] for b in kh.dac_ta["buoc"]] == ["Số thứ tự được chọn", "Hoàn thành lượt khám",
                                                                     "Phiếu hợp lệ đưa vào phân tích"]
    assert kh.dac_ta["buoc"][1][1] == ("Không được mời (n = …)\n– Không đủ tiêu chuẩn (n = …)\n"
                                       "– Không gặp được để mời (n = …)")  # khung không in số thật
    assert "(n = 12)" not in json.dumps(kh.dac_ta, ensure_ascii=False)
    assert kh.ghi_chu[1] == ("Các lý do loại và ra khỏi nghiên cứu được ghi nhận: bỏ về trước khi khám; không đủ tiêu "
                             "chuẩn; không gặp được để mời.")
    assert kh.ghi_chu[2] == KBB.GHI_MOT_LAN


def test_nap_so_luong_bo_qua_mau_chung(tmp_path):
    import ve_bieu_do as VB  # noqa: PLC0415

    (tmp_path / "study_meta.json").write_text(json.dumps({"gate_params": {"G1": {"design": "cross_sectional"}}}),
                                              encoding="utf-8", newline="\n")
    p = tmp_path / "SO_DO_LUONG_S.csv"
    VB.ghi_mau_so_do_luong("cross_sectional", p)
    assert KBB.nap_ngu_canh(tmp_path, "S").luong == []  # mẫu chung G6 tự tạo — không mang thông tin riêng
    with p.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["buoc", "n", "loai", "nhanh", "ly_do"], lineterminator="\n")
        w.writeheader()
        w.writerows(LUONG)
    assert len(KBB.nap_ngu_canh(tmp_path, "S").luong) == len(LUONG)


def test_ve_lai_so_do_cap_nhat_cau_may_cua_ghi_chu(tmp_path):
    nc = _ngu_canh(LUONG)
    p = tmp_path / KBB.THU_MUC_HINH / "hinh-5-1.png"
    KBB.ve_hinh(KBB.Khung("hinh", "", dac_ta={"kieu": "so_do", "buoc": [("A (n = …)", None), ("B (n = …)", None)],
                                              "tach": []}), p)
    md = _chuong().replace("## 5.1. Kết quả theo mục tiêu 1\n\n", "## 5.1. Kết quả theo mục tiêu 1\n\n"
                           "![Hình 5.1](bieu-bang/hinh-5-1.png)\n\n**Hình 5.1. Sơ đồ tuyển chọn đối tượng (theo "
                           "STROBE)**\n\n*Ghi chú:* Số lượng ở từng bước ghi khi kết thúc thu thập.\n\n")
    bc: list = []
    m1, _ = KBB.nang_cap_chuong(md, nc, tmp_path, True, bc)
    ghi = next(x for x in m1.splitlines() if x.startswith("*Ghi chú:* Số lượng ở từng bước"))
    assert ghi == ("*Ghi chú:* Số lượng ở từng bước ghi khi kết thúc thu thập. Các lý do loại và ra khỏi nghiên cứu "
                   "được ghi nhận: bỏ về trước khi khám; không đủ tiêu chuẩn; không gặp được để mời. "
                   + KBB.GHI_MOT_LAN)
    assert any(x.startswith("vẽ lại Hình 5.1") and "SO_DO_LUONG" in x for x in bc)
    m2, _ = KBB.nang_cap_chuong(m1, nc, tmp_path, True)
    assert m2 == m1
    # không có sổ riêng và tên khác khung chuẩn ⇒ không thay sơ đồ soạn tay bằng khung chung
    bc3: list = []
    KBB.nang_cap_chuong(md, _ngu_canh(), tmp_path, True, bc3)
    assert any(x.startswith("giữ nguyên Hình 5.1") for x in bc3)


# ── 4. Nguồn đúng cho nội dung ảnh ────────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("mien, cach, ky_vong", [
    (False, "thu MỚI bằng phiếu; khai thác nguồn CÓ SẴN trên HIS", False),
    (True, "phiếu tự điền", True),
    (None, "trích hồ sơ có sẵn", True),
    (None, "phiếu tự điền", False)])
def test_hoi_cuu_theo_mien_dong_thuan(tmp_path, mien, cach, ky_vong):
    meta = {"gate_params": {"G1": {"design": "cross_sectional", "data_collection_method": cach},
                            "G2": ({} if mien is None else {"icf_waiver_requested": mien})}}
    (tmp_path / "study_meta.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8", newline="\n")
    assert KBB.nap_ngu_canh(tmp_path, "S").hoi_cuu is ky_vong


def test_thang_diem_tu_bien_phai_sinh():
    assert KBB._thang_hop_le("Loại mã 7, 8 và 9 theo SAP §6; mức hợp lệ 1–5") == (1.0, 5.0)
    assert KBB._thang_hop_le("không khai") is None
    bd = next(k for k in KBB._khung_muc_tieu(_ngu_canh(), 1, "Mô tả mức hài lòng") if k.loai == "bieu_do")
    assert bd.dac_ta["truc_y"] == "Giá trị trung bình (thang 1–5)" and bd.dac_ta["y_max"] == 5.0
    ngu = _ngu_canh()
    ngu.bien["b"].thang = (0.0, 10.0)  # hai biến khác thang ⇒ không ghi thang chung
    bd2 = next(k for k in KBB._khung_muc_tieu(ngu, 1, "Mô tả mức hài lòng") if k.loai == "bieu_do")
    assert bd2.dac_ta["truc_y"] == "Giá trị trung bình" and "y_max" not in bd2.dac_ta


def test_truc_dau_phay_thap_phan():
    plt = KBB._plt()
    fig, ax = plt.subplots()
    ax.set_ylim(0, 1)
    KBB._truc_so_viet(ax, "y")
    assert ax.yaxis.get_major_formatter()(0.2, 0) == "0,2"
    plt.close(fig)


def test_nhom_nho_dua_hau_to_chung_len_ghi_chu():
    nc = _ngu_canh()
    nc.phan_tich = nc.phan_tich + [
        {"id": "N1", "vai": "nhom_con", "mo_ta": "Tỷ lệ hài lòng — giới: nam; nhóm dưới 30 người chỉ báo số đếm"},
        {"id": "N2", "vai": "nhom_con", "mo_ta": "Tỷ lệ hài lòng — giới: nữ; nhóm dưới 30 người chỉ báo số đếm"},
        {"id": "N3", "vai": "nhom_con",
         "mo_ta": "Tỷ lệ hài lòng — người bệnh có thẻ bảo hiểm y tế còn hiệu lực; nhóm dưới 30 người chỉ báo số đếm"}]
    bang, bd = KBB._khung_nhom_nho_do_nhay(nc)
    dai = "Người bệnh có thẻ bảo hiểm y tế còn hiệu lực"
    assert len(dai) > 40
    assert [d[0] for d in bang.dong] == ["Giới: nam", "Giới: nữ", dai]
    assert any("nhóm dưới 30 người chỉ báo số đếm." in g for g in bang.ghi_chu)
    assert bd.dac_ta["nhan"] == ["Giới: nam", "Giới: nữ", dai, "Chung"]  # không cắt giữa chữ ở 40 ký tự
    assert KBB._tach_hau_to_chung(["a; x y", "b"]) == ("", ["a; x y", "b"])


def test_hang_forest_nhan_dai_khong_chong():
    y1, t1 = KBB._vi_tri_hang_forest(["A", "B\nC", "D"])
    assert (y1, t1) == ([2.0, 1.0, 0.0], 3)  # một–hai dòng: đúng bước cũ ⇒ ảnh cũ vẽ lại không đổi
    y2, t2 = KBB._vi_tri_hang_forest(["A", "B\nC\nD\nE", "F"])
    assert t2 > 3 and y2[0] - y2[1] > 1 and y2[1] - y2[2] > 1
    assert re.match(r"^\d", str(t2))


def test_ve_hinh_cot_trung_binh_dung_thang_va_dau_phay(tmp_path, monkeypatch):
    import matplotlib.axes as MA  # noqa: PLC0415

    goi: list = []
    goc_ylim = MA.Axes.set_ylim
    def _ylim(self, *a, **k):
        goi.append(("ylim", a))
        return goc_ylim(self, *a, **k)

    monkeypatch.setattr(MA.Axes, "set_ylim", _ylim)
    monkeypatch.setattr(KBB, "_truc_so_viet", lambda ax, truc: goi.append(("truc", truc)))
    bd = next(k for k in KBB._khung_muc_tieu(_ngu_canh(), 1, "Mô tả mức hài lòng") if k.loai == "bieu_do")
    KBB.ve_hinh(bd, tmp_path / "x.png")
    assert ("ylim", (0, 5.0)) in goi and ("truc", "y") in goi


def test_so_do_nhan_qua_khong_bi_coi_la_so_do_chon(tmp_path):
    """«Sơ đồ nhân quả (DAG) lựa chọn biến» chứa chữ «chọn» nhưng không phải sơ đồ chọn đối tượng — không được vẽ đè
    bằng sơ đồ luồng."""
    assert KBB._SO_DO_TEN_RE.search("Sơ đồ tuyển chọn đối tượng nghiên cứu (theo STROBE)")
    assert not KBB._SO_DO_TEN_RE.search("Sơ đồ nhân quả (DAG) lựa chọn biến hiệu chỉnh")
    kh, ly_do = KBB._nguon_hinh("Hình", "Sơ đồ nhân quả (DAG) lựa chọn biến hiệu chỉnh", "", _ngu_canh(LUONG), [], [])
    assert kh is None and "không khớp khung chuẩn" in ly_do
