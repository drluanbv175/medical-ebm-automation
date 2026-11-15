"""Hoàn thiện HỆ THỐNG (mọi đề tài) cho chuỗi biến → nhập liệu → SPSS/R, trước khi có dữ liệu (15/11/2026).

Bác sĩ: «Hãy hoàn thiện vấn đề hệ thống nghiên cứu chứ không phải chỉ riêng cho 2 đề tài trên». Hai lỗ hệ thống đo được
trên C1a/BTM:
  A. Trường calc của REDCap: V6 chỉ PHÁT HIỆN thiếu công thức (nhập Excel/SPSS không tính calc ⇒ cột trống) — đề tài
     nào cũng phải viết tay. ⇒ `bien_phai_sinh.py soan-tu-calc` dịch biểu thức REDCap thành công thức NHÁP (không ghi
     người duyệt; không dịch được ⇒ không ghi dòng nào, để V6 không xanh giả).
  B. Khai báo biến ở SPSS/R chỉ kiểm được SAU khi có dữ liệu. ⇒ `dien_tap_spss_r.py` sinh dữ liệu GIẢ từ từ điển G5,
     chạy đúng cầu nối thật (xuat-sav, xuat-rds) trên bản sao tạm ngoài repo.
Soi HÀNH VI; không gọi mạng; SPSS/R thật chỉ chạy khi máy có (skipif).
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
import types
from datetime import date
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))
sys.path.insert(0, str(_REPO_ROOT / "tools"))
sys.path.insert(0, str(_REPO_ROOT / "tests"))

import bien_phai_sinh as B  # noqa: E402
import cau_noi_spss as SP  # noqa: E402
import dien_tap_spss_r as DT  # noqa: E402
import doi_chieu_bien_de_cuong as DC  # noqa: E402
import nhap_lieu_excel as NL  # noqa: E402
from test_dong_bo_xuyen_cong_20261115 import COT_TD, STUDY, _co_rscript, _co_spss, _de_tai_e5  # noqa: E402


# ── A. Bộ dịch calc REDCap ─────────────────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("bt, ky_vong", [
    ("round([can_nang] / (([chieu_cao] / 100) ^ 2), 1)", "can_nang / (chieu_cao / 100) ** 2"),
    ("[a] + [b]", "a + b"),
    ("if([x] = '1', 1, 0)", "neu(neu(la_thieu(x), 0, x == 1), 1, 0)"),
    ("[a] <> 2", "neu(la_thieu(a), 1, a != 2)"),
    ("if([q(3)] = '1' AND [t] = 0, 1, 0)",
     "neu(neu(la_thieu(q___3), 0, q___3 == 1) and neu(la_thieu(t), 0, t == 0), 1, 0)"),
    ("if([a] >= 18, 1, 0)", "neu(a >= 18, 1, 0)"),
])
def test_dich_calc_redcap_dung(bt, ky_vong):
    ct, _ = B.dich_calc_redcap(bt)
    assert ct == ky_vong
    B.phan_tich(ct)  # hợp lệ với chính bộ phân tích của hệ


@pytest.mark.parametrize("bt, ly_do", [
    ("datediff([d1], [d2], 'y')", "datediff"),
    ("sum([a], [b])", "sum"),
    ("[ev_1][a] + 1", "sự kiện"),
    ("if([gioi] = 'M', 1, 0)", "chuỗi"),
    ("", "trống"),
    ("[a] + ", "cú pháp"),
])
def test_dich_calc_redcap_tu_choi_khi_khong_dich_duoc(bt, ly_do):
    ct, ghi = B.dich_calc_redcap(bt)
    assert ct is None and any(ly_do in g for g in ghi), ghi


def test_ngu_nghia_o_trong_giong_redcap():
    """REDCap so `[x] = '1'` với ô trống ⇒ khác (0), KHÔNG phải thiếu — công thức dịch phải cho đúng như vậy."""
    import pandas as pd

    ct, _ = B.dich_calc_redcap("if([x] = '1' and [y] = '0', 1, 0)")
    dm = B.DanhMuc(cot={"x", "y"}, ngay=set())
    bien = [B.BienPS(ten="z", cong_thuc=ct, nhan="", kieu="", goc="z", cong_thuc_goc=ct, lap_k="", dau="",
                     nguoi_duyet="", nhan_gia_tri={}, dong=2, ngoai_tang=False)]
    kq = B.kiem_dac_ta(bien, dm)
    df = pd.DataFrame({"x": ["1", "", "1"], "y": ["0", "0", ""]})
    z = list(B.tinh_df(df, kq, dm, ["z"])["z"])
    assert z == [1.0, 0.0, 0.0], z


def _de_tai_calc(tmp_path: Path, bt_bmi: str = "round([can_nang] / (([chieu_cao] / 100) ^ 2), 1)") -> Path:
    d = tmp_path / "exports" / "ZZ-CALC"
    d.mkdir(parents=True)
    with (d / "G5_REDCap_dictionary_ZZ-CALC.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COT_TD)
        w.writeheader()
        for ten, kieu, nhan, lua in (("record_id", "text", "Mã", ""), ("can_nang", "text", "Cân nặng", ""),
                                     ("chieu_cao", "text", "Chiều cao", ""), ("bmi", "calc", "BMI", bt_bmi),
                                     ("tuoi_nam", "calc", "Tuổi", "datediff([ngay_sinh], 'today', 'y')")):
            w.writerow({"Variable / Field Name": ten, "Form Name": "phieu", "Field Type": kieu, "Field Label": nhan,
                        "Choices, Calculations, OR Slider Labels": lua})
    # Nguồn NGƯỜI soạn (không dấu máy) cho đối chiếu biến ↔ đề cương (V6 cần một chuẩn để đối chiếu)
    (d / "G3_BO_BIEN_SO_ZZ-CALC.md").write_text(
        "# Bộ biến\n\n| Tên biến | Nhãn | Loại | Giá trị hợp lệ |\n|---|---|---|---|\n"
        "| record_id | Mã | Định danh | — |\n| can_nang | Cân nặng | Định lượng | 30–200 |\n"
        "| chieu_cao | Chiều cao | Định lượng | 120–220 |\n| bmi | BMI | Định lượng | — |\n"
        "| tuoi_nam | Tuổi | Định lượng | — |\n", encoding="utf-8", newline="\n")
    (d / "_bien-phai-sinh.csv").write_text(
        "ten_bien,nhan,kieu,dinh_nghia,bien_nguon,quy_tac_ma_thieu,dung_o,nguon,cong_thuc,lap_k,nhan_gia_tri,"
        "nguoi_duyet\ncu,Biến cũ,,,,,,,can_nang * 2,,,PI:X:2026-11-01:abc\n", encoding="utf-8", newline="\n")
    return d


def test_soan_tu_calc_ghi_nhap_khong_ghi_nguoi_duyet_va_khong_ghi_dong_khong_dich(tmp_path, monkeypatch, capsys):
    d = _de_tai_calc(tmp_path)
    monkeypatch.setattr(B, "_study_dir", lambda s: d)
    truoc = (d / "_bien-phai-sinh.csv").read_text(encoding="utf-8").splitlines()[1]
    assert B.lenh_soan_tu_calc(types.SimpleNamespace(study="ZZ-CALC", ghi=False)) == 1  # tuoi_nam không dịch được
    assert "bmi" not in (d / "_bien-phai-sinh.csv").read_text(encoding="utf-8"), "chạy khô không được ghi"
    assert B.lenh_soan_tu_calc(types.SimpleNamespace(study="ZZ-CALC", ghi=True)) == 1
    rows = list(csv.DictReader((d / "_bien-phai-sinh.csv").open(encoding="utf-8")))
    ten = [r["ten_bien"] for r in rows]
    assert ten == ["cu", "bmi"], ten                       # tuoi_nam KHÔNG có dòng (V6 không xanh giả)
    bmi = rows[1]
    assert bmi["cong_thuc"] == "can_nang / (chieu_cao / 100) ** 2" and bmi["nguoi_duyet"] == ""
    assert "round" in bmi["dinh_nghia"] and "CHỜ" in bmi["nguon"] and bmi["bien_nguon"] == "can_nang chieu_cao"
    assert (d / "_bien-phai-sinh.csv").read_text(encoding="utf-8").splitlines()[1] == truoc  # dòng cũ nguyên văn
    assert list(d.glob("_bien-phai-sinh.csv.bak-*")), "phải sao lưu trước khi ghi"
    kq = B.kiem_dac_ta(B.doc_dac_ta(d), B.doc_danh_muc_tu_dien(d, "ZZ-CALC"))
    assert kq.trang_thai["bmi"] == "CHUA_DUYET", kq.trang_thai   # phân tích vẫn dừng tới khi người duyệt
    # chạy lại: đã có ⇒ không thêm trùng
    B.lenh_soan_tu_calc(types.SimpleNamespace(study="ZZ-CALC", ghi=True))
    assert [r["ten_bien"] for r in csv.DictReader((d / "_bien-phai-sinh.csv").open(encoding="utf-8"))] == ["cu", "bmi"]
    out = capsys.readouterr().out
    assert "tuoi_nam" in out and "viết công thức tay" in out


def test_v6_het_lech_sau_khi_soan_va_thong_diep_tro_lenh(tmp_path, monkeypatch):
    d = _de_tai_calc(tmp_path, bt_bmi="[can_nang] / (([chieu_cao] / 100) ^ 2)")
    md = DC.markdown(DC.doi_chieu(d, "ZZ-CALC"))
    dong_v6 = [x for x in md.splitlines() if "| V6 |" in x]
    assert any("bmi" in x for x in dong_v6) and all("soan-tu-calc --study ZZ-CALC --ghi" in x for x in dong_v6)
    monkeypatch.setattr(B, "_study_dir", lambda s: d)
    B.lenh_soan_tu_calc(types.SimpleNamespace(study="ZZ-CALC", ghi=True))
    md = DC.markdown(DC.doi_chieu(d, "ZZ-CALC"))
    dong_v6 = [x for x in md.splitlines() if "| V6 |" in x]
    assert not any("`bmi`" in x for x in dong_v6) and any("tuoi_nam" in x for x in dong_v6), dong_v6


# ── B. Diễn tập SPSS/R trước thu thập ─────────────────────────────────────────────────────────────────────────────
def test_du_lieu_gia_hop_le_theo_tu_dien(tmp_path):
    d, td_p, _ = _de_tai_e5(tmp_path)
    ra = tmp_path / "gia.csv"
    gen = DT.sinh_du_lieu_gia(td_p, d / "_ma-thieu-theo-bien.csv", ra, 12)
    rows = list(csv.DictReader(ra.open(encoding="utf-8")))
    assert len(rows) == 12 and gen["so_ca"] == 12
    cot = {c.ten: c for c in NL.ke_hoach_cot(NL.doc_tu_dien_day_du(td_p),
                                            SP.doc_ma_thieu(d / "_ma-thieu-theo-bien.csv"))[0]}
    for c in cot.values():
        gt = [r[c.ten] for r in rows]
        assert all("\n" not in g for g in gt)
        if c.kieu == "ma":
            hop_le = set(c.lua_chon) | set(map(str, c.ma_thieu))
            assert set(gt) <= hop_le and set(c.lua_chon) <= set(gt), (c.ten, gt)  # mỗi mã đều xuất hiện
        if c.kieu == "so_nguyen" and c.min:
            so = [float(g) for g in gt[:-1]]
            assert min(so) >= float(c.min) and max(so) <= float(c.max), (c.ten, so)
    assert rows[-1]["tuoi"] == "-99", "ca cuối phải mang mã thiếu để diễn tập khai báo mã thiếu"


def test_dien_tap_khong_co_tu_dien_la_khong_do_duoc(tmp_path):
    (tmp_path / "exports" / "ZZ-KHONG-TD").mkdir(parents=True)
    bc = DT.dien_tap("ZZ-KHONG-TD", goc_exports=tmp_path / "exports")
    assert bc["trang_thai"] == DT.KHONG_DO and "run_g5_auto" in bc["chang"][0]["ghi"]


def _bam_thu_muc(d: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(d.rglob("*")):
        if p.is_file():
            h.update(p.relative_to(d).as_posix().encode() + p.read_bytes())
    return h.hexdigest()


def test_dien_tap_khong_ghi_vao_de_tai_va_tra_lai_cau_noi(tmp_path):
    d, _, _ = _de_tai_e5(tmp_path)
    (d / "du_lieu.csv").unlink()
    truoc = _bam_thu_muc(d)
    exports_cu, study_dir_cu = SP.EXPORTS, B._study_dir
    bc = DT.dien_tap(STUDY, so_ca=6, spss=False, r=False, goc_exports=d.parent)
    assert _bam_thu_muc(d) == truoc, "diễn tập không được ghi/sửa gì trong thư mục đề tài"
    assert SP.EXPORTS is exports_cu and B._study_dir is study_dir_cu, "phải trả lại cầu nối như cũ"
    assert bc["trang_thai"] == DT.DAT and bc["chang"][0]["trang_thai"] == DT.DAT


def test_dien_tap_bao_chan_khi_thieu_ma_tran(tmp_path):
    """Đề tài chưa có ma trận mục tiêu–biến ⇒ cầu nối SPSS CHẶN (E4) ⇒ diễn tập báo LỆCH có lý do (không xanh giả).
    Không cần SPSS: E4 chặn TRƯỚC khi gọi SPSS."""
    d, _, _ = _de_tai_e5(tmp_path)
    (d / "_ma-tran-muc-tieu-bien.csv").unlink()
    bc = DT.dien_tap(STUDY, so_ca=6, r=False, goc_exports=d.parent)
    sp = next(c for c in bc["chang"] if c["ten"].startswith("SPSS"))
    assert sp["trang_thai"] == DT.LECH and "ma trận" in sp["nhat_ky"], sp
    assert bc["trang_thai"] == DT.LECH


@pytest.mark.skipif(not (_co_spss() and _co_rscript()), reason="cần cả SPSS lẫn Rscript")
def test_dien_tap_spss_r_that_dat_tren_de_tai_du_dieu_kien(tmp_path):
    d, _, _ = _de_tai_e5(tmp_path)
    (d / "du_lieu.csv").unlink()
    bc = DT.dien_tap(STUDY, so_ca=8, goc_exports=d.parent)
    tt = {c["ten"].split(" ")[0]: c["trang_thai"] for c in bc["chang"]}
    assert tt.get("SPSS") == DT.DAT and tt.get("R") == DT.DAT, json.dumps(bc, ensure_ascii=False)[:3000]
    assert bc["trang_thai"] == DT.DAT
    assert not (d / "spss").exists() and not (d / "r").exists(), ".sav/.rds diễn tập không được rơi vào đề tài"


def test_cli_ghi_bao_cao_rieng(tmp_path, monkeypatch, capsys):
    d, _, _ = _de_tai_e5(tmp_path)
    monkeypatch.setattr(DT, "BASE", tmp_path)
    assert d.parent == tmp_path / "exports"
    ma = DT.main(["--study", STUDY, "--so-ca", "5", "--khong-spss", "--khong-r", "--ghi"])
    assert ma == 0
    bc = (d / f"DIEN_TAP_SPSS_R_{STUDY}.md").read_text(encoding="utf-8")
    assert "ĐẠT" in bc and "dữ liệu GIẢ" in bc and date.today().isoformat() in bc
