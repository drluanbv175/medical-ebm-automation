"""Vá sau lượt rà phản biện độc lập 14/11/2026 cho phép khứ hồi .sav/.rds (cau_noi_spss.so_sanh_gia_tri) và xuat-sav.

1. Số > 15 chữ số có nghĩa: double không lưu đúng ⇒ float(nguồn) và giá trị đọc lại CÙNG bị làm tròn, ngưỡng ulp che
   lệch ⇒ trước đây báo «khớp từng ô». Nay báo LỆCH riêng («vượt độ chính xác»).
2. Số nguyên ≤ 15 chữ số phải trùng TUYỆT ĐỐI (ở 1e15, 8 ulp = 1 đơn vị: 999999999999999 từng «khớp» 1e15).
3. Ô có xuống dòng: SPSS GET DATA tách thành hai ca ⇒ xuat-sav chặn TRƯỚC khi chạy SPSS, chỉ rõ dòng · cột.
Không cần SPSS/R, dữ liệu GIẢ.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import cau_noi_spss as C  # noqa: E402

FX = Path(__file__).resolve().parent / "fixtures" / "spss_khu_hoi"


def _ke() -> list[dict]:
    return [{"bo": False, "ten": t, "cot": t, "so": True, "ma_chu": {}} for t in ("ma", "x")]


def _csv(tmp_path: Path, dong: list[str]) -> Path:
    p = tmp_path / "nguon.csv"
    p.write_text("ma,x\n" + "\n".join(dong) + "\n", encoding="utf-8", newline="\n")
    return p


def test_so_qua_15_chu_so_khong_bao_gio_khop(tmp_path):
    p = _csv(tmp_path, ["12345678901234567,0.1", "9007199254740993,2.5"])
    ca = [[float("12345678901234567"), 0.1], [float("9007199254740993"), 2.5]]  # đúng như SPSS/R đọc (đã làm tròn)
    kq = C.so_sanh_gia_tri(p, _ke(), ["ma", "x"], ca)
    assert kq["trang_thai"] == "LECH" and kq["so_lech"] == 2
    assert all("vượt độ chính xác" in m["loai"] for m in kq["mau_lech"])
    assert C.vuot_do_chinh_xac("12345678901234567") and not C.vuot_do_chinh_xac("0.1")
    assert not C.vuot_do_chinh_xac("0.41817215137075947") and not C.vuot_do_chinh_xac("007")


def test_so_nguyen_15_chu_so_phai_trung_tuyet_doi(tmp_path):
    p = _csv(tmp_path, ["999999999999999,1.5", "123456789012345,2.5"])
    lech = C.so_sanh_gia_tri(p, _ke(), ["ma", "x"], [[1e15, 1.5], [123456789012345.0, 2.5]])
    assert lech["so_lech"] == 1 and lech["mau_lech"][0]["ca"] == 1  # 999999999999999 ≠ 1e15 dù chỉ trong 8 ulp
    khop = C.so_sanh_gia_tri(p, _ke(), ["ma", "x"], [[999999999999999.0, 1.5], [123456789012345.0, 2.5]])
    assert khop["trang_thai"] == "KHOP"
    p2 = _csv(tmp_path, ["1,0.41817215137075947"])  # số THỰC dài: bộ đọc của SPSS lệch 1 ulp ⇒ vẫn khớp (đo thật)
    assert C.so_sanh_gia_tri(p2, _ke(), ["ma", "x"], [[1.0, 0.4181721513707594]])["trang_thai"] == "KHOP"


def test_xuat_sav_chan_o_xuong_dong_truoc_khi_chay_spss(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(C, "EXPORTS", tmp_path / "exports")
    d = tmp_path / "exports" / "THU"
    d.mkdir(parents=True)
    shutil.copy(FX / "tu_dien.csv", d / "G5_REDCap_dictionary_THU.csv")
    shutil.copy(FX / "ma_thieu.csv", d / "_ma-thieu-theo-bien.csv")
    nguon = (FX / "du_lieu.csv").read_text(encoding="utf-8").replace('"Nói ""không"" rõ"', '"Nói\nkhông rõ"', 1)
    assert "\nkhông rõ" in nguon
    p = tmp_path / "nhieu_dong.csv"
    p.write_text(nguon, encoding="utf-8", newline="\n")
    monkeypatch.setattr(C, "tim_spss", lambda: (_ for _ in ()).throw(AssertionError("không được chạy SPSS")))
    assert C.main(["xuat-sav", "--study", "THU", "--data", str(p), "--ban-nhap"]) == C.MA_TU_CHOI
    ra = capsys.readouterr().out
    assert "XUỐNG DÒNG" in ra and "dòng 2 · ghi" in ra and "không rõ" not in ra  # chỉ vị trí, không in giá trị
    assert not (d / "spss" / "THU_BAN-NHAP.sav").exists()
