"""Ba biểu mẫu pha phát triển bộ câu hỏi mà đề cương C1a mục 4.5.1 cam kết — 17/10/2026 (soát chất lượng G1-T4).

Bộ mẫu cũ chỉ có phiếu CVI + nhật ký phỏng vấn nhận thức theo mục; đề cương còn hứa: hội đồng chuyên gia có thành phần
xác định và HAI câu hỏi mở về nội dung còn thiếu (COSMIN: tính bao phủ — CVI không phát hiện được), thời gian điền
phiếu đo trong phỏng vấn nhận thức (tiêu chí khả thi số 4), bảng truy xuất nguồn gốc câu hỏi. Test chốt: sinh rỗng,
không ghi đè; tính thành phần/thời gian đúng; bảng truy xuất lấy nội dung từ từ điển REDCap, nguồn gốc để chủ nhiệm;
kiểm máy G1-T4 bắt tệp thiếu và mục/chuyên gia không khớp phiếu CVI.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT / "tools"), str(ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import hoi_dong_cong as HD  # noqa: E402
import pha_phat_trien_cong_cu as PCC  # noqa: E402

TU_DIEN = ("Variable / Field Name,Section Header,Field Label,Field Note\n"
           "a1,Phần 2 · A. Tiếp cận,A1. Chờ đăng ký,Likert\na2,,A2. Chờ gặp bác sĩ,\n"
           "g2,Phần 3,G2. Ý định quay lại,\n")


def _hd(dong: list[str]) -> tuple[list[str], list[dict[str, str]]]:
    cot = PCC.COT_HOI_DONG
    return cot, [dict(zip(cot, d.split("|"))) for d in dong]


def test_bo_sung_sinh_rong_va_khong_ghi_de(tmp_path):
    p_hd, p_tn = PCC.sinh_bo_sung(6, tmp_path, so_nguoi=2)
    assert p_hd.read_text(encoding="utf-8").splitlines()[0] == ",".join(PCC.COT_HOI_DONG)
    assert len(p_hd.read_text(encoding="utf-8").splitlines()) == 7 and "NT02" in p_tn.read_text(encoding="utf-8")
    with pytest.raises(PCC.LoiDauVao, match="không ghi đè"):
        PCC.sinh_bo_sung(6, tmp_path)


def test_thanh_phan_hoi_dong_theo_de_cuong():
    du = [f"CG0{i}|lam_sang|khong|||" for i in range(1, 5)] + ["CG05|dai_dien_nguoi_benh|khong|thiếu bãi xe||",
                                                              "CG06|dai_dien_nguoi_benh|co|||"]
    kq = PCC.tinh_hoi_dong(*_hd(du))
    assert kq["vi_pham_thanh_phan"] == [] and kq["so_dai_dien_nguoi_benh"] == 2
    assert kq["so_y_kien_noi_dung_thieu"] == 1 and kq["chua_phan_hoi"] == 1, "ý kiến chưa được chủ nhiệm phản hồi"
    thieu_nb = PCC.tinh_hoi_dong(*_hd(du[:5] + ["CG06|lam_sang|co|||", "CG07|khac|co|||", "CG08|khac|co|||"]))
    assert any("đại diện người bệnh < 2" in v for v in thieu_nb["vi_pham_thanh_phan"])
    assert any("thuộc đơn vị nghiên cứu > 2" in v for v in thieu_nb["vi_pham_thanh_phan"])
    assert any("ngoài khoảng 6–10" in v for v in PCC.tinh_hoi_dong(*_hd(du[:3]))["vi_pham_thanh_phan"])
    with pytest.raises(PCC.LoiDauVao, match="nhóm"):
        PCC.tinh_hoi_dong(*_hd(["CG01|bac_si|khong|||"]))


def test_thoi_gian_dien_phieu_trung_vi_va_nguong():
    cot = PCC.COT_THEO_NGUOI
    dong = [dict(zip(cot, x)) for x in (("NT01", "18", "", ""), ("NT02", "25,5", "giá thuốc", ""),
                                        ("NT03", "22", "", ""), ("NT04", "", "", ""))]
    kq = PCC.tinh_theo_nguoi(cot, dong)
    assert kq["so_nguoi_co_thoi_gian"] == 3 and kq["trung_vi_phut"] == 22 and kq["vuot_nguong_so_bo"] is True
    assert kq["so_nguoi_neu_noi_dung_thieu"] == 1
    assert PCC.tinh_theo_nguoi(cot, dong[:1])["vuot_nguong_so_bo"] is False
    with pytest.raises(PCC.LoiDauVao, match="không phải số"):
        PCC.tinh_theo_nguoi(cot, [dict(zip(cot, ("NT01", "mười", "", "")))])


def test_truy_xuat_lay_noi_dung_tu_tu_dien_nguon_goc_de_chu_nhiem(tmp_path):
    (tmp_path / "td.csv").write_text(TU_DIEN, encoding="utf-8", newline="\n")
    p = PCC.sinh_truy_xuat(["A1", "A2", "G2"], tmp_path / "td.csv", tmp_path / "o")
    _cot, dong = PCC._doc_csv(p)
    a2 = next(d for d in dong if d["muc"] == "A2")
    assert a2["noi_dung"] == "A2. Chờ gặp bác sĩ" and a2["phan_linh_vuc"] == "Phần 2 · A. Tiếp cận", \
        "tiêu đề phần REDCap áp cho trường phía sau"
    assert all(d["nguon_goc"] == PCC.CHO_CHU_NHIEM == d["ly_do_dua_vao"] for d in dong), "công cụ không đoán nguồn"
    with pytest.raises(PCC.LoiDauVao, match="không có trong từ điển"):
        PCC.sinh_truy_xuat(["A1", "ydinh_quaylai"], tmp_path / "td.csv", tmp_path / "khac")


def _du_bo(out: Path, muc: list[str]) -> Path:
    thu = out / "pha_cong_cu"
    PCC.sinh_mau(muc, 6, thu)
    PCC.sinh_bo_sung(6, thu)
    (out / "td.csv").write_text(TU_DIEN, encoding="utf-8", newline="\n")
    PCC.sinh_truy_xuat(muc, out / "td.csv", thu)
    return thu


def test_kiem_may_g1t4_bat_tep_thieu_va_khong_khop(tmp_path):
    out = tmp_path / "S"
    thu = _du_bo(out, ["A1", "A2"])
    assert HD._kiem_pha_cong_cu(out, "S") == []
    (thu / "nhat_ky_phong_van_nhan_thuc_theo_nguoi.csv").unlink()
    assert any("thiếu nhat_ky_phong_van_nhan_thuc_theo_nguoi.csv" in x and "bo-sung" in x
               for x in HD._kiem_pha_cong_cu(out, "S"))
    PCC.sinh_bo_sung(6, tmp_path / "rac")  # tạo lại đúng tệp đã xoá
    (tmp_path / "rac" / "nhat_ky_phong_van_nhan_thuc_theo_nguoi.csv").rename(
        thu / "nhat_ky_phong_van_nhan_thuc_theo_nguoi.csv")
    (thu / "phieu_cvi_hoi_dong.csv").write_text(",".join(PCC.COT_HOI_DONG) + "\nCG01,,,,,\n", encoding="utf-8",
                                                newline="\n")
    assert any("mã chuyên gia không khớp" in x for x in HD._kiem_pha_cong_cu(out, "S"))


def test_bang_truy_xuat_phai_khop_muc_phieu_cvi(tmp_path):
    out = tmp_path / "S"
    thu = _du_bo(out, ["A1", "A2"])
    (thu / "bang_truy_xuat_cau_hoi.csv").write_text(
        ",".join(PCC.COT_TRUY_XUAT) + "\nA1,,x,,,\n", encoding="utf-8", newline="\n")
    loi = HD._kiem_pha_cong_cu(out, "S")
    assert any("mục không khớp phiếu CVI (A2)" in x for x in loi) and any("thiếu nội dung câu" in x for x in loi)


def test_cli_hoi_dong_ma_1_khi_lech_thanh_phan(tmp_path, capsys):
    p = tmp_path / "hd.csv"
    p.write_text(",".join(PCC.COT_HOI_DONG) + "\nCG01,lam_sang,khong,,,\n", encoding="utf-8", newline="\n")
    assert PCC.main(["hoi-dong", str(p)]) == 1 and "Lệch thành phần" in capsys.readouterr().out
