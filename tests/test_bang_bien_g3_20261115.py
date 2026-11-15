# -*- coding: utf-8 -*-
"""Bảng bộ biến G3 cho PI duyệt — `tools/bang_bien_g3.py` (G3-T2, bác sĩ chọn 15/11/2026, sau giả lập trọn lần 3).

Bác sĩ chọn: «Agent bien-so-nghien-cuu soạn thêm G3_BO_BIEN_SO_<mã>.md cho PI đọc và duyệt; thêm vào danh mục hội đồng
G3 và dạy agent. Giữ nguyên ý của #266: dữ liệu máy phải khớp một nguồn do người duyệt.»

Test chốt: ① bảng máy soạn đọc được bằng CHÍNH bộ đọc của G5-AUTO-11, và sau khi PI duyệt thì đối chiếu với bộ máy ra 0
phát hiện; ② bản nháp CHƯA duyệt KHÔNG phải nguồn người duyệt (lỗi vòng tròn: máy so với chính nó vẫn ra «đồng bộ»);
③ sửa bảng sau khi duyệt ⇒ xác nhận mất hiệu lực, còn sửa khung trạng thái thì không; ④ bộ máy đổi sau khi PI duyệt ⇒
đối chiếu báo LỆCH theo bảng đã duyệt; ⑤ không bao giờ ghi đè bảng người soạn / đã duyệt / đã bị sửa tay; ⑥ bảng người
soạn (#266) vẫn là nguồn; ⑦ MT-11 cảnh báo sớm ở G3, không đổi trạng thái ma trận. Ngoại tuyến, đề tài giả, không PII.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
for _p in (str(REPO_ROOT / "tools"), str(REPO_ROOT / "tests"), str(REPO_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import bang_bien_g3 as BB  # noqa: E402
import bien_phai_sinh as BPS  # noqa: E402
import doi_chieu_bien_de_cuong as DC  # noqa: E402
import hoi_dong_cong as HD  # noqa: E402
import ma_tran_muc_tieu_bien as MT  # noqa: E402
from test_dong_bo_xuyen_cong_20261115 import BIEN_E5, COT_TD, STUDY, _de_tai_e5  # noqa: E402

DE_CUONG_CO_BANG_BIEN = ("| Mã biến | Tên biến | Loại | Mã hoá | Nguồn |\n|---|---|---|---|---|\n"
                         "| tuoi | Tuổi | định lượng | 18 – 100 | x |\n")
PS_COT = ["ten_bien", "nhan", "kieu", "dinh_nghia", "bien_nguon", "cong_thuc", "lap_k", "nhan_gia_tri", "nguoi_duyet"]


def _duyet(d: Path, dau: str | None = None, luc: str = "2026-11-15T10:00:00") -> None:
    """PI GIẢ LẬP ghi xác nhận (đề tài giả trong tmp) — agent thật KHÔNG ghi khoá này."""
    m = json.loads((d / "study_meta.json").read_text(encoding="utf-8"))
    dau = dau or BB.trang_thai(d, STUDY)["dau_hien_tai"]
    m.setdefault("gate_params", {}).setdefault("G3", {})[BB.KHOA_DUYET] = {"reviewed_at": luc, "dau_van_tay": dau}
    (d / "study_meta.json").write_text(json.dumps(m, ensure_ascii=False), encoding="utf-8", newline="\n")


def _phai_sinh(d: Path) -> None:
    ct = "neu(tuoi >= 60, 1, 0)"
    with (d / MT.TEP_PHAI_SINH).open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=PS_COT, lineterminator="\n")
        w.writeheader()
        w.writerow({"ten_bien": "nhom_tuoi", "nhan": "Nhóm tuổi", "kieu": "nhị phân",
                    "dinh_nghia": "1 nếu tuổi ≥ 60, 0 nếu dưới 60", "bien_nguon": "tuoi", "cong_thuc": ct,
                    "nhan_gia_tri": "0, <60 | 1, ≥60",
                    "nguoi_duyet": f"THONG_KE_VIEN:TEST:2026-11-15:{BPS.dau_cong_thuc('nhom_tuoi', ct, '')}"})


def _ghi_bo_bien(d: Path, bien) -> None:
    """Ghi lại bộ biến + từ điển G5 (cùng nội dung) với danh sách biến mới (đổi bộ máy sau khi soạn bảng)."""
    for ten_tep in (MT.TEP_BO_BIEN, f"G5_REDCap_dictionary_{STUDY}.csv"):
        with (d / ten_tep).open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=COT_TD)
            w.writeheader()
            for ten, kieu, nhan, lua, val, ann, lo, hi in bien:
                w.writerow({"Variable / Field Name": ten, "Form Name": "phieu", "Field Type": kieu, "Field Label": nhan,
                            "Choices, Calculations, OR Slider Labels": lua,
                            "Text Validation Type OR Show Slider Number": val, "Required Field?": "y",
                            "Text Validation Min": lo, "Text Validation Max": hi, "Field Annotation": ann})


def _bien_e5(**sua):
    ra = []
    for ten, kieu, nhan, lua, val, ann in BIEN_E5:
        lo, hi = ("18", "100") if ten == "tuoi" else ("", "")
        ra.append(sua.get(ten, (ten, kieu, nhan, lua, val, ann, lo, hi)))
    return ra


# ── ① bảng đọc được bằng bộ đọc của G5-AUTO-11 + vòng khứ hồi ─────────────────────────────────────────────────────────
def test_bang_may_soan_doc_duoc_bang_bo_doc_g5_auto_11(tmp_path):
    d, _, _ = _de_tai_e5(tmp_path)
    _phai_sinh(d)
    chu, _ = BB.soan(d, STUDY, ngay="2026-11-15")
    assert BB.NHAN_CHO_DUYET in chu and BB.DAU_MAY in chu and BB.MOC_TT_BD in chu and BB.MOC_TT_KT in chu
    p = d / BB.ten_tep(STUDY)
    p.write_text(chu, encoding="utf-8", newline="\n")
    nguon, ten = DC.doc_bo_bien_g3(d, STUDY)
    assert ten == p.name
    theo_ten = {b.ten: b for b in nguon}
    assert set(theo_ten) == {b[0] for b in BIEN_E5} | {"nhom_tuoi"}, "đủ mọi trường + biến phái sinh, không thừa"
    assert theo_ten["trinh_do"].ma_hoa == "1, Tiểu học; 2, THCS; 3, THPT; 4, Đại học"
    assert DC.doc_ma(theo_ten["trinh_do"].ma_hoa)[0] == {1, 2, 3, 4}
    assert theo_ten["tuoi"].ma_hoa == "18 – 100" and theo_ten["tuoi"].loai == "số nguyên"
    assert theo_ten["nhom_tuoi"].tinh_toan and "≥ 60" in theo_ten["nhom_tuoi"].dinh_nghia
    assert ("| `tuan_thu` | Tuân thủ (kết cục chính) | chọn một | 0, Không; 1, Có | phieu | ket_cuc_chinh | 1 | TT1 |"
            in chu)


def test_pi_duyet_thi_bang_la_nguon_va_doi_chieu_dong_bo_khong_phat_hien(tmp_path):
    d, _, _ = _de_tai_e5(tmp_path)
    _phai_sinh(d)
    # thêm một ô có/không (yesno) và một ô ngày — mỗi loại trường phải khứ hồi được qua bộ đọc G5-AUTO-11
    _ghi_bo_bien(d, _bien_e5() + [("hut_thuoc", "yesno", "Hút thuốc lá", "", "", "", "", ""),
                                  ("ngay_pv", "text", "Ngày phỏng vấn", "", "date_ymd", "", "2026-01-01",
                                   "2026-12-31")])
    p, _, ma = BB.ghi(d, STUDY)
    assert p is not None and ma == 0
    _duyet(d)
    st = BB.trang_thai(d, STUDY)
    assert st["trang_thai"] == BB.DA_DUYET and st["la_nguon_nguoi_duyet"] and st["nguon_doi"] is False
    kq = DC.doi_chieu(d, STUDY)
    assert kq.nguon_nguoi_duyet == [p.name] and kq.nguon_bi_loai == []
    assert kq.trang_thai == "DONG_BO", [(x.luat, x.bien, x.chi_tiet) for x in kq.phat_hien]


# ── ② bản nháp chưa duyệt KHÔNG phải nguồn ────────────────────────────────────────────────────────────────────────────
def test_ban_nhap_chua_duyet_khong_duoc_tinh_la_nguon_nguoi_duyet(tmp_path):
    d, _, _ = _de_tai_e5(tmp_path)
    BB.ghi(d, STUDY)
    st = BB.trang_thai(d, STUDY)
    assert st["trang_thai"] == BB.CHUA_DUYET and not st["la_nguon_nguoi_duyet"]
    assert st["dau_hien_tai"] in st["ly_do"], "lý do phải in dấu nội dung để PI ghi"
    kq = DC.doi_chieu(d, STUDY)
    assert kq.trang_thai == "KHONG_DO_DUOC", "máy so với bảng do chính nó soạn ⇒ «đồng bộ» giả"
    assert "chưa có nguồn người duyệt" in kq.khong_do_duoc and kq.nguon_bi_loai
    assert kq.nguon_nguoi_duyet == []
    assert "Không tính là nguồn người duyệt" in DC.markdown(kq)


def test_xac_nhan_ngay_tuong_lai_hoac_thieu_dau_khong_hop_le(tmp_path):
    d, _, _ = _de_tai_e5(tmp_path)
    BB.ghi(d, STUDY)
    _duyet(d, luc="2999-01-01T00:00:00")
    assert BB.trang_thai(d, STUDY)["trang_thai"] == BB.XAC_NHAN_LECH
    _duyet(d, dau="0123456789abcdef")
    st = BB.trang_thai(d, STUDY)
    assert st["trang_thai"] == BB.XAC_NHAN_LECH and "đã đổi" in st["ly_do"]
    assert DC.doi_chieu(d, STUDY).trang_thai == "KHONG_DO_DUOC"


# ── ③ sửa sau khi duyệt ───────────────────────────────────────────────────────────────────────────────────────────────
def test_sua_bang_sau_khi_duyet_mat_hieu_luc_sua_khung_trang_thai_thi_khong(tmp_path):
    d, _, _ = _de_tai_e5(tmp_path)
    p, _, _ = BB.ghi(d, STUDY)
    _duyet(d)
    chu = p.read_text(encoding="utf-8")
    p.write_text(chu.replace(f"**{BB.NHAN_CHO_DUYET}**", "**ĐÃ DUYỆT 15/11/2026**"), encoding="utf-8", newline="\n")
    assert BB.trang_thai(d, STUDY)["trang_thai"] == BB.DA_DUYET, "khung trạng thái không tính vào dấu"
    p.write_text(p.read_text(encoding="utf-8").replace("| 18 – 100 |", "| 18 – 90 |"), encoding="utf-8",
                 newline="\n")
    st = BB.trang_thai(d, STUDY)
    assert st["trang_thai"] == BB.XAC_NHAN_LECH and st["sua_sau_khi_soan"] is True
    assert DC.doi_chieu(d, STUDY).trang_thai == "KHONG_DO_DUOC"


# ── ④ bộ máy đổi sau khi duyệt ────────────────────────────────────────────────────────────────────────────────────────
def test_bo_may_doi_sau_khi_pi_duyet_thi_doi_chieu_bao_lech_theo_bang_da_duyet(tmp_path):
    d, _, _ = _de_tai_e5(tmp_path)
    BB.ghi(d, STUDY)
    _duyet(d)
    _ghi_bo_bien(d, _bien_e5(tuoi=("tuoi", "text", "Tuổi (năm)", "", "integer", "", "18", "90")))
    st = BB.trang_thai(d, STUDY)
    assert st["trang_thai"] == BB.DA_DUYET and st["nguon_doi"] is True
    kq = DC.doi_chieu(d, STUDY)
    assert any(x.luat == "V2" and x.bien == "tuoi" and x.muc == DC.LECH for x in kq.lech()), kq.to_dict()
    canh = [x["noi_dung"] for x in MT.kiem(d, STUDY)["canh_bao"] if x["ma"] == "MT-11"]
    assert canh and "đã đổi sau khi soạn" in canh[0]


# ── ⑤ không ghi đè ────────────────────────────────────────────────────────────────────────────────────────────────────
def test_khong_ghi_de_bang_nguoi_soan_da_duyet_hay_da_sua_tay(tmp_path):
    d, _, _ = _de_tai_e5(tmp_path)
    p = d / BB.ten_tep(STUDY)
    p.write_text("# bảng người soạn\n\n| Tên biến | Nhãn | Loại | Giá trị hợp lệ |\n|---|---|---|---|\n"
                 "| `tuoi` | Tuổi | số nguyên | 18 – 100 |\n", encoding="utf-8", newline="\n")
    assert BB.ghi(d, STUDY, ghi_de=True)[0] is None, "bảng người soạn: KHÔNG BAO GIỜ ghi đè"
    p.unlink()
    assert BB.ghi(d, STUDY)[0] == p
    assert BB.ghi(d, STUDY) == (None, f"{p.name} đã đúng bản máy soạn hiện tại — không đổi", 0)
    # bộ máy đổi, bản nháp CHƯA sửa tay ⇒ soạn lại được (không cần --ghi-de)
    _ghi_bo_bien(d, _bien_e5(tuoi=("tuoi", "text", "Tuổi (năm)", "", "integer", "", "18", "95")))
    assert BB.ghi(d, STUDY)[0] == p and "18 – 95" in p.read_text(encoding="utf-8")
    # người sửa tay bản nháp ⇒ từ chối, --ghi-de mới cho
    p.write_text(p.read_text(encoding="utf-8").replace("Tuổi (năm)", "Tuổi tròn năm"), encoding="utf-8", newline="\n")
    _ghi_bo_bien(d, _bien_e5())
    tep, tb, ma = BB.ghi(d, STUDY)
    assert tep is None and ma == 1 and "sửa sau khi máy soạn" in tb
    assert BB.ghi(d, STUDY, ghi_de=True)[0] == p and "Tuổi tròn năm" not in p.read_text(encoding="utf-8")
    # đã duyệt ⇒ từ chối cả khi --ghi-de
    _duyet(d)
    _ghi_bo_bien(d, _bien_e5(tuoi=("tuoi", "text", "Tuổi (năm)", "", "integer", "", "18", "80")))
    tep, tb, ma = BB.ghi(d, STUDY, ghi_de=True)
    assert tep is None and ma == 1 and "xác nhận PI hợp lệ" in tb
    assert BB.trang_thai(d, STUDY)["trang_thai"] == BB.DA_DUYET


def test_thieu_bo_bien_thi_khong_soan(tmp_path):
    d = tmp_path / "exports" / STUDY
    d.mkdir(parents=True)
    assert BB.ghi(d, STUDY)[2] == 2 and not (d / BB.ten_tep(STUDY)).exists()


# ── ⑥ bảng người soạn (#266) ──────────────────────────────────────────────────────────────────────────────────────────
def test_bang_nguoi_soan_khong_dau_may_van_la_nguon_nhu_266(tmp_path):
    """Người soạn lại bảng (bỏ HẾT cấu trúc của máy: dòng dấu, khung trạng thái) ⇒ bảng người soạn như #266."""
    d, _, _ = _de_tai_e5(tmp_path)
    chu, _ = BB.soan(d, STUDY)
    tay = "# Bộ biến số (người soạn lại)\n\n" + "\n".join(
        x for x in BB.than_bang(chu).split("\n") if not x.startswith(BB.DAU_MAY))
    (d / BB.ten_tep(STUDY)).write_text(tay, encoding="utf-8", newline="\n")
    assert BB.trang_thai(d, STUDY)["trang_thai"] == BB.NGUOI_SOAN
    kq = DC.doi_chieu(d, STUDY)
    assert kq.trang_thai == "DONG_BO" and kq.nguon_nguoi_duyet == [BB.ten_tep(STUDY)]


def test_go_rieng_dong_dau_may_van_la_ban_nhap_chua_duyet(tmp_path):
    """Thẩm định #274, VÀNG 3: xoá MỘT dòng chú thích (hoặc chép qua bản xem trước Markdown làm rơi chú thích HTML) mà
    khung trạng thái «[CẦN PI DUYỆT]» còn nguyên ⇒ vẫn là bản nháp máy chưa duyệt, không thành «người soạn»."""
    d, _, _ = _de_tai_e5(tmp_path)
    p, _, _ = BB.ghi(d, STUDY)
    p.write_text("\n".join(x for x in p.read_text(encoding="utf-8").split("\n") if not x.startswith(BB.DAU_MAY)),
                 encoding="utf-8", newline="\n")
    st = BB.trang_thai(d, STUDY)
    assert st["trang_thai"] == BB.CHUA_DUYET and "dấu máy đã bị gỡ" in st["ly_do"]
    assert DC.doi_chieu(d, STUDY).trang_thai == "KHONG_DO_DUOC"
    assert BB.ghi(d, STUDY)[0] is None, "bản đã bị sửa ⇒ không tự ghi đè"


# ── ⑦ MT-11 ───────────────────────────────────────────────────────────────────────────────────────────────────────────
def _mt11(d: Path) -> list[str]:
    kq = MT.kiem(d, STUDY)
    assert kq["trang_thai"] == MT.TRANG_THAI_DAT, "MT-11 chỉ cảnh báo — không đổi trạng thái ma trận"
    return [x["noi_dung"] for x in kq["canh_bao"] if x["ma"] == "MT-11"]


def test_mt11_canh_bao_khi_chua_co_hoac_chua_duyet_im_khi_da_duyet(tmp_path):
    d, _, _ = _de_tai_e5(tmp_path)
    assert any("bang_bien_g3.py soan" in x for x in _mt11(d)), "chưa có bảng + đề cương chưa có bảng biến ⇒ cảnh báo"
    BB.ghi(d, STUDY)
    assert any("CHƯA được PI duyệt" in x for x in _mt11(d))
    _duyet(d)
    assert _mt11(d) == []


def test_mt11_im_khi_de_cuong_nop_da_co_bang_bien_so(tmp_path):
    d, _, _ = _de_tai_e5(tmp_path)
    (d / f"DE_CUONG_NOP_HOI_DONG_{STUDY}.md").write_text(
        "## Bảng E.1\n\n| Mã biến | Tên biến | Loại | Mã hoá | Nguồn |\n|---|---|---|---|---|\n"
        "| tuoi | Tuổi | định lượng | 18 – 100 | phỏng vấn |\n", encoding="utf-8", newline="\n")
    assert _mt11(d) == []


# ── tự kiểm mã + định danh ────────────────────────────────────────────────────────────────────────────────────────────
def test_nhan_lua_chon_lam_bo_doc_hieu_sai_thi_dua_vao_muc_pi_xem_tay(tmp_path):
    d, _, _ = _de_tai_e5(tmp_path)
    _ghi_bo_bien(d, _bien_e5(trinh_do=("trinh_do", "radio", "Trình độ", "1, BMI = 18 | 2, Khác", "", "", "", "")))
    _, xem = BB.soan(d, STUDY)
    assert any("`trinh_do`" in x and "đối chiếu tay" in x for x in xem)


def test_truong_dinh_danh_duoc_neu_trong_bang_va_muc_xem_tay(tmp_path):
    d, _, _ = _de_tai_e5(tmp_path)
    rows = list(csv.DictReader((d / MT.TEP_BO_BIEN).open(encoding="utf-8")))
    rows[0]["Identifier?"] = "y"
    with (d / MT.TEP_BO_BIEN).open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COT_TD)
        w.writeheader()
        w.writerows(rows)
    chu, xem = BB.soan(d, STUDY)
    assert "ĐỊNH DANH" in chu and any("định danh" in x for x in xem) and "**SAI" in chu


# ── hội đồng + CLI ────────────────────────────────────────────────────────────────────────────────────────────────────
def test_hoi_dong_g3_t2_doi_bang_bo_bien_cho_pi_hoac_de_cuong_nop(tmp_path):
    dau_ra = HD._nhiem_vu("G3", "G3-T2")["dau_ra"]
    muc = next(d for d in dau_ra if "G3_BO_BIEN_SO_<mã>.md" in d)
    assert HD.phuong_an_dau_ra(muc) == ["G3_BO_BIEN_SO_<mã>.md", "DE_CUONG_NOP_HOI_DONG_<mã>.md"]
    d, _, _ = _de_tai_e5(tmp_path)
    assert not HD.co_dau_ra(d, STUDY, muc)
    (d / f"DE_CUONG_NOP_HOI_DONG_{STUDY}.md").write_text("# đề cương\n", encoding="utf-8", newline="\n")
    assert HD.co_dau_ra(d, STUDY, muc), "có một trong hai tệp là đủ đầu ra"
    loi = HD._kiem_bo_bien_so(d, STUDY)
    assert any("chưa có nguồn người duyệt" in x for x in loi), "đề cương KHÔNG có bảng biến số ⇒ kiểm máy G3-T2 báo"
    (d / f"DE_CUONG_NOP_HOI_DONG_{STUDY}.md").write_text(
        DE_CUONG_CO_BANG_BIEN,
        encoding="utf-8", newline="\n")
    assert not any("nguồn người duyệt" in x for x in HD._kiem_bo_bien_so(d, STUDY))


@pytest.mark.parametrize("buoc, ma", [("chua_co", 2), ("chua_duyet", 1), ("da_duyet", 0)])
def test_cli_trang_thai_ma_thoat(tmp_path, monkeypatch, capsys, buoc, ma):
    d, _, _ = _de_tai_e5(tmp_path)
    monkeypatch.setattr(BB, "BASE", tmp_path)
    if buoc != "chua_co":
        assert BB.main(["soan", "--study", STUDY, "--ghi"]) == 0
    if buoc == "da_duyet":
        _duyet(d)
    capsys.readouterr()
    assert BB.main(["trang-thai", "--study", STUDY]) == ma
    assert "Agent không ghi xác nhận PI" in capsys.readouterr().out


# ── canary giả lập định kỳ: bước G3-T2 có bảng + PI giả lập duyệt (đúng thiết kế, không phải máy hỏng) ─────────────
def test_canary_pi_gia_lap_duyet_bang_g3_la_can_thiep_dung_thiet_ke(tmp_path):
    import gia_lap_dinh_ky as GL  # noqa: PLC0415
    from test_gia_lap_dinh_ky_20261115 import KB_THU  # noqa: PLC0415

    d, _, _ = _de_tai_e5(tmp_path)
    gl = GL.GiaLap("thu", {**KB_THU, "study": STUDY}, tmp_path, False, chay=lambda *a, **k: {"ma": 0, "ra": ""},
                   cham=lambda *a, **k: {"status": "KHONG_DO_DUOC"}, nen_g0_dir=tmp_path / "nen")
    assert gl._duyet_bang_bien_g3() is False, "chưa có bảng ⇒ không có gì để duyệt"
    BB.ghi(d, STUDY)
    assert gl._duyet_bang_bien_g3() is True
    assert BB.trang_thai(d, STUDY)["trang_thai"] == BB.DA_DUYET
    assert gl.can_thiep[-1]["loai"] == "duyet_bang_bien_g3" and gl.can_thiep[-1]["do_may"] is False
    assert {"soan_bang_bien_g3", "duyet_bang_bien_g3"} <= set(GL.CAN_THIEP_DUNG_THIET_KE)
    assert gl._duyet_bang_bien_g3() is False, "đã duyệt ⇒ không ghi lại"


# ── sửa sau thẩm định đối kháng #274 ─────────────────────────────────────────────────────────────────────────────────
def _duyet_roi_bo_may_them_ma(tmp_path):
    """PI duyệt bảng; sau đó bộ máy thêm mã 5 cho trinh_do ⇒ đối chiếu phải LỆCH V2 theo bảng đã duyệt."""
    d, _, _ = _de_tai_e5(tmp_path)
    p, _, _ = BB.ghi(d, STUDY)
    _duyet(d)
    _ghi_bo_bien(d, _bien_e5(trinh_do=("trinh_do", "radio", "Trình độ học vấn",
                                       "1, Tiểu học | 2, THCS | 3, THPT | 4, Đại học | 5, Sau đại học", "", "", "",
                                       "")))
    kq = DC.doi_chieu(d, STUDY)
    assert any(x.luat == "V2" and x.bien == "trinh_do" for x in kq.lech()), "tiền đề: lệch thật bị bắt"
    return d, p


def test_chen_dong_trong_hoac_noi_hang_sau_khi_duyet_lam_mat_hieu_luc(tmp_path):
    """Thẩm định #274, ĐỎ 1: dấu cũ gộp mọi khoảng trắng kể cả xuống dòng ⇒ chèn một dòng trống trước hàng trinh_do
    (bộ đọc bảng tách bảng ⇒ hàng đó rơi khỏi bảng) giữ DA_DUYET và CHE lệch thật (G5-AUTO-11 BLOCK → PASS)."""
    d, p = _duyet_roi_bo_may_them_ma(tmp_path)
    goc = p.read_text(encoding="utf-8")
    hang = next(x for x in goc.split("\n") if x.startswith("| `trinh_do`"))
    for sua in (goc.replace(hang, "\n" + hang), goc.replace("\n" + hang, " " + hang)):
        p.write_text(sua, encoding="utf-8", newline="\n")
        st = BB.trang_thai(d, STUDY)
        assert st["trang_thai"] == BB.XAC_NHAN_LECH, "đổi ranh giới dòng phải làm xác nhận mất hiệu lực"
        assert DC.doi_chieu(d, STUDY).trang_thai == "KHONG_DO_DUOC"
    p.write_text(goc, encoding="utf-8", newline="\n")
    assert BB.trang_thai(d, STUDY)["trang_thai"] == BB.DA_DUYET


def test_bang_chen_vao_khung_trang_thai_khong_duoc_doc_va_lam_mat_hieu_luc(tmp_path):
    """Thẩm định #274, ĐỎ 2: vùng không tính dấu (tiêu đề, khung trạng thái) từng được bộ đọc G5-AUTO-11 đọc ⇒ chèn bảng
    biến phái sinh vào đó che LỆCH V5 mà xác nhận vẫn còn."""
    d, p = _duyet_roi_bo_may_them_ma(tmp_path)
    goc = p.read_text(encoding="utf-8")
    chen = "| Tên | Định nghĩa / công thức |\n|---|---|\n| `gia_70` | 1 nếu tuổi ≥ 70 |\n"
    for sua in (goc.replace(BB.MOC_TT_KT, chen + BB.MOC_TT_KT), goc.replace(BB.MOC_TT_BD, chen + BB.MOC_TT_BD)):
        p.write_text(sua, encoding="utf-8", newline="\n")
        assert BB.trang_thai(d, STUDY)["trang_thai"] == BB.XAC_NHAN_LECH
        assert "gia_70" not in {b.ten for b in DC.doc_bo_bien_g3(d, STUDY)[0]}, "bộ đọc chỉ đọc thân bảng"


def test_slider_khu_hoi_khong_sinh_lech_gia_sau_khi_duyet(tmp_path):
    """Thẩm định #274, VÀNG 5: nhãn thanh trượt «0 = … | 100 = …» trong ô Giá trị hợp lệ ⇒ LỆCH V2 «mã đặc biệt 100»."""
    d, _, _ = _de_tai_e5(tmp_path)
    _ghi_bo_bien(d, _bien_e5() + [("dau", "slider", "Mức đau", "0 = Không đau | 50 = Vừa | 100 = Đau nhất", "", "",
                                   "", "")])
    p, _, _ = BB.ghi(d, STUDY)
    chu = p.read_text(encoding="utf-8")
    hang = next(x for x in chu.split("\n") if x.startswith("| `dau`"))
    assert "| 0 – 100 |" in hang and "nhãn thanh trượt: 0 = Không đau" in hang
    _duyet(d)
    kq = DC.doi_chieu(d, STUDY)
    assert not [x for x in kq.lech() if x.bien == "dau"], [(x.luat, x.chi_tiet) for x in kq.lech()]


def test_ghi_khong_xoa_ghi_chu_pi_trong_khung_trang_thai(tmp_path):
    """Thẩm định #274, VÀNG 6: PI ghi chú vào khung của bản nháp, bộ máy đổi ⇒ `ghi` không được lặng lẽ xoá ghi chú."""
    d, _, _ = _de_tai_e5(tmp_path)
    p, _, _ = BB.ghi(d, STUDY)
    p.write_text(p.read_text(encoding="utf-8").replace(BB.MOC_TT_KT, "> PI: KHÔNG duyệt bản này — chờ sửa nhãn.\n"
                                                                        + BB.MOC_TT_KT), encoding="utf-8", newline="\n")
    _ghi_bo_bien(d, _bien_e5(tuoi=("tuoi", "text", "Tuổi (năm)", "", "integer", "", "18", "95")))
    tep, tb, ma = BB.ghi(d, STUDY)
    assert tep is None and ma == 1 and "khung trạng thái" in tb
    assert "KHÔNG duyệt bản này" in p.read_text(encoding="utf-8")
    assert BB.ghi(d, STUDY, ghi_de=True)[0] == p, "--ghi-de vẫn mở được khi PI bảo soạn lại"


def test_de_cuong_co_bang_bien_va_ban_nhap_chua_duyet_thi_chi_dung_de_cuong(tmp_path):
    """Thẩm định #274, XÁM 7 (đột biến M-q lọt): có đề cương nộp + bảng G3 máy soạn chưa duyệt ⇒ bảng G3 bị loại, đề
    cương vẫn là nguồn."""
    d, _, _ = _de_tai_e5(tmp_path)
    (d / f"DE_CUONG_NOP_HOI_DONG_{STUDY}.md").write_text(
        DE_CUONG_CO_BANG_BIEN,
        encoding="utf-8", newline="\n")
    BB.ghi(d, STUDY)
    kq = DC.doi_chieu(d, STUDY)
    assert kq.nguon_nguoi_duyet == [f"DE_CUONG_NOP_HOI_DONG_{STUDY}.md"]
    assert kq.nguon_bi_loai and BB.ten_tep(STUDY) in kq.nguon_bi_loai[0]


def test_tep_bang_khong_phai_utf8_khong_bi_ghi_de_va_khong_vang_loi(tmp_path):
    """Thẩm định #274, XÁM 8: bảng lưu UTF-16 (Notepad «Unicode») ⇒ từ chối rõ ràng, không traceback, không ghi đè."""
    d, _, _ = _de_tai_e5(tmp_path)
    p = d / BB.ten_tep(STUDY)
    p.write_bytes("| Tên biến | Nhãn | Loại | Giá trị hợp lệ |\n".encode("utf-16"))
    st = BB.trang_thai(d, STUDY)
    assert st["doc_duoc"] is False and not st["la_nguon_nguoi_duyet"]
    tep, tb, ma = BB.ghi(d, STUDY, ghi_de=True)
    assert tep is None and ma == 1 and "UTF-8" in tb
    assert p.read_bytes().startswith(b"\xff\xfe") or p.read_bytes().startswith(b"\xfe\xff")


def test_canary_mot_buoc_pi_soan_roi_duyet_bang_qua_duong_noi_that(tmp_path):
    """Thẩm định #274, XÁM 7 (đột biến M-w lọt): đi qua ĐÚNG GiaLap.mot_buoc_pi — bước 1 gọi bang_bien_g3.py soan, bước
    2 PI giả lập duyệt; cả hai là can thiệp đúng thiết kế."""
    import gia_lap_dinh_ky as GL  # noqa: PLC0415
    from test_gia_lap_dinh_ky_20261115 import KB_THU  # noqa: PLC0415

    d, _, _ = _de_tai_e5(tmp_path)
    (d / "G3_checkpoint.json").write_text(json.dumps({"gate": "G3", "n_adjusted": 120}), encoding="utf-8",
                                         newline="\n")
    lenh = []

    def chay(cmd, *a, **k):
        lenh.append([Path(x).name for x in cmd])
        if any(str(x).endswith("bang_bien_g3.py") for x in cmd):
            BB.ghi(d, STUDY)
        return {"ma": 0, "ra": ""}

    kb = {**KB_THU, "study": STUDY, "query_en": None, "pi": {"G3": {}},
          "bien_so": {"bo_bien": [], "ma_tran": []}}
    gl = GL.GiaLap("thu", kb, tmp_path, False, chay=chay, cham=lambda *a, **k: {"status": "PASS_G3_CONFIRMED"},
                   nen_g0_dir=tmp_path / "nen")
    assert gl.mot_buoc_pi() == "G3" and any("bang_bien_g3.py" in x for x in lenh[-1])
    assert gl.can_thiep[-1]["loai"] == "soan_bang_bien_g3" and gl.can_thiep[-1]["do_may"] is False
    assert gl.mot_buoc_pi() == "G3"
    assert gl.can_thiep[-1]["loai"] == "duyet_bang_bien_g3"
    assert BB.trang_thai(d, STUDY)["trang_thai"] == BB.DA_DUYET
