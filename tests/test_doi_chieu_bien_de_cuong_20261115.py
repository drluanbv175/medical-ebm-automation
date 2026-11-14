"""Đối chiếu biến ↔ đề cương/bộ biến đã duyệt (tools/doi_chieu_bien_de_cuong.py) + chốt ở nhập liệu — 15/11/2026.

Bác sĩ: «Biến xác định không đúng, nhập liệu không đúng thì không thể phân tích được nên phải đảm bảo xác định biến đúng
đồng bộ với đề cương». Mỗi luật V1–V8 một ca có lệch thật; dữ liệu giả, không PII.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import bien_phai_sinh as BPS  # noqa: E402
import doi_chieu_bien_de_cuong as D  # noqa: E402
import nhap_lieu_excel as NL  # noqa: E402

S = "DE-TAI-THU"
COT = [
    "Variable / Field Name",
    "Form Name",
    "Section Header",
    "Field Type",
    "Field Label",
    "Choices, Calculations, OR Slider Labels",
    "Field Note",
    "Text Validation Type OR Show Slider Number",
    "Text Validation Min",
    "Text Validation Max",
    "Identifier?",
    "Branching Logic (Show field only if...)",
]
DE_CUONG = """# PHỤ LỤC E. BẢNG BIẾN SỐ VÀ MÃ HÓA

| Mã biến | Nội dung | Loại biến | Mã hóa / đơn vị | Nguồn |
|---|---|---|---|---|
| ID | Mã nghiên cứu | Danh định | Mã ngẫu nhiên | Phiếu |
| Tuoi | Tuổi | Định lượng | Năm | Phiếu – câu 1 |
| GioiTinh | Giới | Nhị phân | 1 = nam; 2 = nữ | Phiếu – câu 2 |
| HocVan | Học vấn | Thứ bậc | 1 = chưa đi học … 4 = đại học | Phiếu – câu 3 |
| A1–A3 | Hài lòng từng câu | Thứ bậc | 1–5; 7 = không sử dụng – ô KSD (chỉ A3); 9 = bỏ trống | Phiếu – Phần 2 |
| kyvong | Thời gian chờ dự kiến | Định lượng | Phút; 998 = không ước lượng được | Phiếu – câu 4 |
| G1 | Hài lòng chung | Thứ bậc | 1–5 | Phiếu – Phần 3 |
| SHL_NhiPhan | Hài lòng nhị phân | Nhị phân (tính toán) | 1 = hài lòng (G1 ≥ 4); 0 = chưa hài lòng | Tính toán |
| A_Mean | Điểm lĩnh vực A | Định lượng (tính toán) | Trung bình; chỉ tính khi ≥ 80% số câu có điểm | Tính toán |
"""
LIK = "1, Rất kém | 2, Kém | 3, TB | 4, Tốt | 5, Rất tốt | 9, Bỏ trống"
TRUONG = [
    ("record_id", "text", "", "", "", ""),
    ("tuoi", "text", "", "integer", "", ""),
    ("gioitinh", "radio", "1, Nam | 2, Nữ", "", "", ""),
    ("hocvan", "radio", "1, a | 2, b | 3, c | 4, d", "", "", ""),
    ("a1", "radio", LIK, "", "", ""),
    ("a2", "radio", LIK, "", "", ""),
    ("a3", "radio", LIK + " | 7, KSD", "", "", ""),
    ("kyvong", "text", "", "number", "", ""),
    ("g1", "radio", "1, a | 2, b | 3, c | 4, d | 5, e", "", "", ""),
]
PS = [
    ("SHL_NhiPhan", "neu(trong(g1, [1, 2, 3, 4, 5]), g1 >= 4, thieu())"),
    ("A_Mean", "tb_hop_le([a1, a2, a3], hop_le=[1, 5], khong_ap_dung=[7], ty_le_toi_thieu=0.8)"),
]


def ghi_tu_dien(p: Path, truong) -> None:
    with open(p, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(COT)
        for t, ft, lc, kt, lo, hi in truong:
            w.writerow([t, "f", "", ft, t, lc, "", kt, lo, hi, "", ""])


def ghi_ps(d: Path, ps) -> None:
    with open(d / "_bien-phai-sinh.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "ten_bien",
                "nhan",
                "kieu",
                "dinh_nghia",
                "bien_nguon",
                "quy_tac_ma_thieu",
                "dung_o",
                "nguon",
                "cong_thuc",
                "lap_k",
                "nhan_gia_tri",
                "nguoi_duyet",
            ]
        )
        for t, ct in ps:
            w.writerow([t, t, "", "", "", "", "", "", ct, "", "", ""])


@pytest.fixture()
def de_tai(tmp_path) -> Path:
    d = tmp_path / S
    d.mkdir()
    (d / f"DE_CUONG_NOP_HOI_DONG_{S}.md").write_text(DE_CUONG, encoding="utf-8", newline="\n")
    ghi_tu_dien(d / "_bo-bien-rieng.csv", TRUONG)
    ghi_tu_dien(d / f"G5_REDCap_dictionary_{S}.csv", TRUONG)
    ghi_ps(d, PS)
    (d / "_ma-thieu-theo-bien.csv").write_text(
        "bien,ma,nhan,pham_vi,nguon\nkyvong,998,Không ước lượng,,đề cương\n", encoding="utf-8", newline="\n"
    )
    return d


def _lech(kq, luat=None):
    return {(p.luat, p.bien) for p in kq.phat_hien if p.muc == D.LECH and (luat is None or p.luat == luat)}


def test_dong_bo_khi_ban_may_khop_de_cuong(de_tai):
    kq = D.doi_chieu(de_tai, S)
    assert kq.trang_thai == "DONG_BO" and kq.ma_thoat() == 0, [(p.luat, p.bien, p.chi_tiet) for p in kq.phat_hien]
    assert kq.so_bien_nguon == 11 and {x["bien"] for x in kq.dat_canh} == {"SHL_NhiPhan", "A_Mean"}


def test_v1_bien_de_cuong_thieu_trong_tu_dien_va_bien_tinh_toan_thieu_cong_thuc(de_tai):
    ghi_tu_dien(de_tai / f"G5_REDCap_dictionary_{S}.csv", [t for t in TRUONG if t[0] != "hocvan"])
    ghi_tu_dien(de_tai / "_bo-bien-rieng.csv", [t for t in TRUONG if t[0] != "hocvan"])
    ghi_ps(de_tai, PS[:1])
    kq = D.doi_chieu(de_tai, S)
    assert _lech(kq, "V1") == {("V1", "HocVan"), ("V1", "A_Mean")} and kq.ma_thoat() == 1


def test_v2_ma_khac_menh_de_chi_va_ma_thieu_duoc_mien(de_tai):
    t = [
        x
        if x[0] not in ("gioitinh", "a1", "a3")
        else {
            "gioitinh": ("gioitinh", "radio", "1, Nam | 2, Nữ | 3, Khác", "", "", ""),
            "a1": ("a1", "radio", LIK + " | 7, KSD", "", "", ""),  # 7 chỉ dành cho A3
            "a3": ("a3", "radio", LIK, "", "", ""),
        }[x[0]]
        for x in TRUONG
    ]
    ghi_tu_dien(de_tai / "_bo-bien-rieng.csv", t)
    ghi_tu_dien(de_tai / f"G5_REDCap_dictionary_{S}.csv", t)
    kq = D.doi_chieu(de_tai, S)
    assert _lech(kq, "V2") == {("V2", "GioiTinh"), ("V2", "A1"), ("V2", "A3")}
    chi = {p.bien: p.chi_tiet for p in kq.phat_hien if p.luat == "V2"}
    assert "thừa [3]" in chi["GioiTinh"] and "thừa [7]" in chi["A1"] and "thiếu [7]" in chi["A3"]
    # mã 8 có trong từ điển nhưng khai là mã thiếu cấp dự án ⇒ miễn
    t2 = [
        x if x[0] != "g1" else ("g1", "radio", "1, a | 2, b | 3, c | 4, d | 5, e | 8, Không biết", "", "", "")
        for x in TRUONG
    ]
    ghi_tu_dien(de_tai / "_bo-bien-rieng.csv", t2)
    ghi_tu_dien(de_tai / f"G5_REDCap_dictionary_{S}.csv", t2)
    assert ("V2", "G1") in _lech(D.doi_chieu(de_tai, S))
    (de_tai / "_ma-thieu-theo-bien.csv").write_text(
        "bien,ma,nhan,pham_vi,nguon\nkyvong,998,x,,y\n*,8,Không biết,,y\n", encoding="utf-8", newline="\n"
    )
    assert ("V2", "G1") not in _lech(D.doi_chieu(de_tai, S))


def test_v2_ma_dac_biet_bien_dinh_luong_phai_khai_ma_thieu(de_tai):
    (de_tai / "_ma-thieu-theo-bien.csv").write_text("bien,ma,nhan,pham_vi,nguon\n", encoding="utf-8", newline="\n")
    kq = D.doi_chieu(de_tai, S)
    assert _lech(kq) == {("V2", "kyvong")} and "998" in next(p.chi_tiet for p in kq.phat_hien if p.bien == "kyvong")


def test_v5_bien_phai_sinh_ngoai_de_cuong_va_nguong_khong_khop(de_tai):
    ghi_ps(
        de_tai,
        [
            ("SHL_NhiPhan", "neu(trong(g1, [1, 2, 3, 4, 5]), g1 >= 3, thieu())"),
            PS[1],
            ("NhomTuoi", "nhom(tuoi, [40, 60], [1, 2, 3])"),
            ("tang", "@g6_trong_so_survey"),
        ],
    )
    kq = D.doi_chieu(de_tai, S)
    assert _lech(kq) == {("V5", "NhomTuoi")}
    xem = {p.bien: p.chi_tiet for p in kq.phat_hien if p.muc == D.XEM}
    assert "4" in xem["SHL_NhiPhan"] and "tang" in xem


def test_v6_truong_calc_phai_co_bien_phai_sinh_cung_ten(de_tai):
    t = TRUONG + [("bmi", "calc", "round([can] / ([cao] / 100) ^ 2, 1)", "", "", "")]
    ghi_tu_dien(de_tai / "_bo-bien-rieng.csv", t)
    ghi_tu_dien(de_tai / f"G5_REDCap_dictionary_{S}.csv", t)
    kq = D.doi_chieu(de_tai, S)
    assert ("V6", "bmi") in _lech(kq)
    ghi_ps(de_tai, PS + [("bmi", "tuoi / 2")])
    assert ("V6", "bmi") not in _lech(D.doi_chieu(de_tai, S))


def test_v7_bo_bien_rieng_phai_trung_tu_dien_g5(de_tai):
    ghi_tu_dien(
        de_tai / f"G5_REDCap_dictionary_{S}.csv",
        [x if x[0] != "tuoi" else ("tuoi", "text", "", "number", "", "") for x in TRUONG]
        + [("them", "text", "", "", "", "")],
    )
    kq = D.doi_chieu(de_tai, S)
    assert {("V7", "tuoi"), ("V7", "them")} <= _lech(kq)


def test_v8_dac_ta_phan_tich_chi_dung_bien_doc_duoc(de_tai):
    t = TRUONG + [("bmi", "calc", "x", "", "", "")]
    ghi_tu_dien(de_tai / "_bo-bien-rieng.csv", t)
    ghi_tu_dien(de_tai / f"G5_REDCap_dictionary_{S}.csv", t)
    (de_tai / "G6_DAC_TA_SAP.json").write_text(
        json.dumps(
            {
                "phan_tich": [
                    {
                        "id": "C",
                        "tham_so": {
                            "outcome": "g1",
                            "group": "tuoi",
                            "covariates": ["gioitinh", "bmi"],
                            "ty_le": ["SHL_NhiPhan"],
                            "loc": "khong_co == 1",
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
        newline="\n",
    )
    kq = D.doi_chieu(de_tai, S)
    v8 = {p.bien: p.chi_tiet for p in kq.phat_hien if p.luat == "V8"}
    assert set(v8) == {"bmi", "khong_co"} and "calc" in v8["bmi"]


def test_khong_co_nguon_nguoi_duyet_la_khong_do_duoc(de_tai):
    (de_tai / f"DE_CUONG_NOP_HOI_DONG_{S}.md").unlink()
    kq = D.doi_chieu(de_tai, S)
    assert kq.trang_thai == "KHONG_DO_DUOC" and kq.ma_thoat() == 2 and not kq.phat_hien


def test_nguon_bo_bien_g3_dang_bang_ten_bien_va_bien_phai_sinh(tmp_path):
    d = tmp_path / S
    d.mkdir()
    (d / f"G3_BO_BIEN_SO_{S}.md").write_text(
        "## 3. Bảng bộ biến\n\n| Tên biến | Nhãn | Loại | Giá trị hợp lệ | Nhóm |\n|---|---|---|---|---|\n"
        "| `tha` | Tăng huyết áp | chọn một | 1, Có; 0, Không | 3 |\n| `hba1c` | HbA1c | số | 3 – 20 | 4 |\n\n"
        "## 4. Biến phái sinh\n\n| Tên | Nhãn | Kiểu | Định nghĩa / công thức | Biến nguồn |\n|---|---|---|---|---|\n"
        "| `tha_x2` | Hai lần | Nhị phân | 1 nếu tha = 1 | tha |\n",
        encoding="utf-8",
        newline="\n",
    )
    ghi_tu_dien(
        d / "_bo-bien-rieng.csv",
        [
            ("record_id", "text", "", "", "", ""),
            ("tha", "radio", "1, Có | 0, Không | 9, ?", "", "", ""),
            ("hba1c", "text", "", "number", "3", "15"),
        ],
    )
    ghi_ps(d, [("tha_x2", "tha == 1"), ("ngoai", "tha == 0")])
    kq = D.doi_chieu(d, S)
    assert kq.nguon_nguoi_duyet == [f"G3_BO_BIEN_SO_{S}.md"]
    assert _lech(kq) == {("V2", "tha"), ("V2", "hba1c"), ("V5", "ngoai")}


def test_doc_ma_va_mo_rong_ten():
    assert D.mo_rong_ten("A1–A3, B1–B2") == ["A1", "A2", "A3", "B1", "B2"]
    assert D.mo_rong_ten("A_Mean … C_Mean") == ["A_Mean", "B_Mean", "C_Mean"]
    assert D.doc_ma("1 = chưa đi học … 7 = sau đại học")[0] == set(range(1, 8))
    assert D.doc_ma("1 = < 5 triệu; 2 = 5 – < 10 triệu; 3 = ≥ 10 triệu")[0] == {1, 2, 3}
    assert D.doc_ma("1 = < 5 km; 2 = 5–10 km; 3 = > 10 km")[0] == {1, 2, 3}
    assert D.doc_ma("1–9 (9 = khác, ghi rõ)")[0] == set(range(1, 10))
    ma, gh = D.doc_ma("1–5; 7 = KSD (chỉ A3, A4); 9 = bỏ trống")
    assert ma == {1, 2, 3, 4, 5, 7, 9} and gh == {7: {"a3", "a4"}}
    assert D.doc_ma("1, Có; 0, Không")[0] == {0, 1} and D.doc_ma("Mã ngẫu nhiên")[0] is None


def test_nhap_lieu_chan_mau_va_tiep_nhan_khi_lech(de_tai, monkeypatch, capsys):
    monkeypatch.setattr(NL.SP, "thu_muc_de_tai", lambda s: de_tai)
    NL.kiem_dong_bo_de_cuong(S, chan=True)  # đồng bộ ⇒ không chặn
    assert "✓ Biến đồng bộ" in capsys.readouterr().out
    ghi_ps(de_tai, PS + [("NhomTuoi", "nhom(tuoi, [40, 60], [1, 2, 3])")])
    NL.kiem_dong_bo_de_cuong(S, chan=True)  # lệch PHÂN TÍCH (biến phái sinh ngoài đề cương) ⇒ chỉ cảnh báo ở nhập liệu
    ra = capsys.readouterr().out
    assert "⚠ [V5] NhomTuoi" in ra and "chặn ở bước phân tích" in ra
    ghi_tu_dien(de_tai / "_bo-bien-rieng.csv", [x for x in TRUONG if x[0] != "hocvan"])
    ghi_tu_dien(de_tai / f"G5_REDCap_dictionary_{S}.csv", [x for x in TRUONG if x[0] != "hocvan"])
    with pytest.raises(NL.TuChoi, match="(?s)CHƯA đồng bộ.*HocVan"):  # lệch NHẬP LIỆU ⇒ chặn
        NL.kiem_dong_bo_de_cuong(S, chan=True)
    NL.kiem_dong_bo_de_cuong(S, chan=False)  # chỉ kiểm (không tiếp nhận) ⇒ cảnh báo, không chặn
    assert "⚠ bộ biến máy CHƯA đồng bộ" in capsys.readouterr().out
    (de_tai / f"DE_CUONG_NOP_HOI_DONG_{S}.md").unlink()
    NL.kiem_dong_bo_de_cuong(S, chan=True)  # không có nguồn ⇒ cảnh báo, không coi là đồng bộ
    assert "Chưa đối chiếu được" in capsys.readouterr().out
    monkeypatch.setattr(BPS, "doc_dac_ta", lambda d: (_ for _ in ()).throw(RuntimeError("hong")))
    (de_tai / f"DE_CUONG_NOP_HOI_DONG_{S}.md").write_text(DE_CUONG, encoding="utf-8", newline="\n")
    with pytest.raises(NL.TuChoi, match="không đối chiếu được"):
        NL.kiem_dong_bo_de_cuong(S, chan=True)


def test_lenh_mau_va_nhap_tiep_nhan_that_su_goi_chot(de_tai, monkeypatch, capsys, tmp_path):
    """Nối dây: `mau` và `nhap --tiep-nhan` gọi chốt TRƯỚC mọi việc khác; `nhap` không tiếp nhận chỉ cảnh báo."""
    monkeypatch.setattr(NL.SP, "EXPORTS", de_tai.parent)
    ghi_tu_dien(de_tai / "_bo-bien-rieng.csv", [x for x in TRUONG if x[0] != "hocvan"])
    ghi_tu_dien(de_tai / f"G5_REDCap_dictionary_{S}.csv", [x for x in TRUONG if x[0] != "hocvan"])
    assert NL.main(["mau", "--study", S, "--ra", str(tmp_path / "m.xlsx")]) == NL.MA_TU_CHOI
    assert "⛔ bộ biến máy CHƯA đồng bộ" in capsys.readouterr().out and not (tmp_path / "m.xlsx").exists()
    vang = str(tmp_path / "ngoai" / "khong_co.xlsx")
    assert NL.main(["nhap", "--study", S, "--excel", vang, "--tiep-nhan"]) == NL.MA_TU_CHOI
    assert "⛔ bộ biến máy CHƯA đồng bộ" in capsys.readouterr().out
    NL.main(["nhap", "--study", S, "--excel", vang])
    ra = capsys.readouterr().out
    assert "⚠ bộ biến máy CHƯA đồng bộ" in ra and "⛔ bộ biến máy" not in ra


def test_phan_tich_chan_bien_phai_sinh_ngoai_de_cuong(de_tai):
    """Cổng PHÂN TÍCH: bien_phai_sinh.ap_dung_cho_phan_tich từ chối tính biến phái sinh ngoài đề cương (đề tài thật);
    giả lập chỉ cảnh báo; biến trong đề cương vẫn tính được."""
    import pandas as pd

    ghi_ps(de_tai, [(t, ct) for t, ct in PS] + [("NhomTuoi", "nhom(tuoi, [40, 60], [1, 2, 3])")])
    duyet = []
    for b in BPS.doc_dac_ta(de_tai):  # duyệt mọi công thức để chỉ còn lý do «ngoài đề cương»
        duyet.append((b.goc, b.cong_thuc_goc, f"TKV:THU:2026-11-15:{b.dau}"))
    with open(de_tai / "_bien-phai-sinh.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "ten_bien",
                "nhan",
                "kieu",
                "dinh_nghia",
                "bien_nguon",
                "quy_tac_ma_thieu",
                "dung_o",
                "nguon",
                "cong_thuc",
                "lap_k",
                "nhan_gia_tri",
                "nguoi_duyet",
            ]
        )
        for t, ct, nd in duyet:
            w.writerow([t, t, "", "", "", "", "", "", ct, "", "", nd])
    df = pd.DataFrame({"tuoi": [30, 50, 70], "g1": [5, 2, 4], "a1": [4, 4, 4], "a2": [5, 5, 5], "a3": [3, 3, 3]})
    df2, info = BPS.ap_dung_cho_phan_tich(df, de_tai, S, ["SHL_NhiPhan"])  # trong đề cương ⇒ tính
    assert list(df2["SHL_NhiPhan"].astype(float)) == [1.0, 0.0, 1.0]
    with pytest.raises(BPS.TuChoi, match="NGOÀI đề cương.*NhomTuoi"):
        BPS.ap_dung_cho_phan_tich(df, de_tai, S, ["NhomTuoi"])
    (de_tai / "study_meta.json").write_text('{"study_kind": "synthetic_test"}', encoding="utf-8", newline="\n")
    _df3, info3 = BPS.ap_dung_cho_phan_tich(df, de_tai, S, ["NhomTuoi"])
    assert any("ngoài đề cương" in c for c in info3["canh_bao"])
