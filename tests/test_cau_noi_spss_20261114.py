"""Kiểm cầu nối IBM SPSS Statistics (tools/cau_noi_spss.py) — 14/11/2026.

Không cần SPSS: tệp mẫu trong tests/fixtures/spss_oxml/ là đầu ra OXML THẬT của SPSS 31.0.1 (chạy trên dữ liệu giả 240
ca, đã gỡ bảng «Notes» chứa đường dẫn máy); lượt chạy SPSS được giả lập. Số kỳ vọng phía Python là kết quả của chính
run_stats_analysis.py trên cùng dữ liệu giả (đo 14/11/2026).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import cau_noi_spss as C  # noqa: E402

FX = Path(__file__).resolve().parent / "fixtures" / "spss_oxml"
ANH_XA = {
    "record_id": "ID",
    "nhom": "Nhom",
    "tuoi": "Tuoi",
    "gioitinh": "GioiTinh",
    "ban_kham": "ban_kham",
    "kq_nhi": "kq_nhi",
    "diem": "diem",
    "hai_long": "hai_long",
    "thoi_gian": "thoi_gian",
    "bien_co": "bien_co",
}


def _man() -> dict:
    muc = {
        "nhom": ["0", "1"],
        "kq_nhi": ["0", "1"],
        "gioitinh": ["1", "2"],
        "bien_co": ["0", "1"],
        "hai_long": ["1", "2", "3", "4", "5"],
    }
    return {
        "bien": [
            {"cot": c, "ten": t, "so": c != "record_id", "muc_do": "SCALE", "nhan": c, "muc": muc.get(c), "ma_chu": {}}
            for c, t in ANH_XA.items()
        ]
    }


def _kq_tu_mau(tmp: Path, kich_ban: str) -> Path:
    kq = tmp / "ket_qua"
    kq.mkdir(parents=True, exist_ok=True)
    for f in (FX / kich_ban).glob("oms_*.xml"):
        shutil.copy(f, kq / f.name)
    return kq


def _dt(**kw) -> dict:
    d = {
        "outcome": None,
        "group": "nhom",
        "covariates": ["tuoi", "gioitinh"],
        "outcome_type": "auto",
        "time": None,
        "event": None,
        "cot_cum": None,
    }
    d.update(kw)
    return d


# ───────────── tiện ích tên / chuỗi ─────────────


def test_ten_va_chuoi_spss():
    assert C.ten_hop_le("Tuoi") and C.ten_hop_le("GioiTinh")
    assert not C.ten_hop_le("BY") and not C.ten_hop_le("9a") and not C.ten_hop_le("tuoi.")
    assert C.chuan_ten("9x") == "v_9x" and C.chuan_ten("with") == "with_"
    assert C.chuoi_spss("O'Neil") == "'O''Neil'"
    dai = "Câu hỏi rất dài về mức độ hài lòng với thời gian chờ khám tại phòng khám ngoại trú " * 4
    s = C.chuoi_spss(dai)
    doan = [x.strip().strip("+").strip() for x in s.split("\n")]
    assert all(len(x.encode("utf-8")) <= 104 for x in doan)
    assert "".join(x[1:-1] for x in doan) == " ".join(dai.split())


def test_ten_spss_tu_chu_thich_bo_dau_cham_cuoi():
    assert C.ten_spss_tu_chu_thich({"chu_thich": "Tên SPSS: Tuoi. GIỮ LIÊN TỤC trong mô hình"}) == "Tuoi"
    assert C.ten_spss_tu_chu_thich({"chu_thich": "không có"}) is None


# ───────────── kế hoạch biến + cú pháp nhãn ─────────────


def _du_lieu(tmp: Path) -> tuple[Path, dict]:
    p = tmp / "d.csv"
    p.write_text(
        "record_id,tuoi,gioitinh,hai_long,nghe,hut_thuoc,trieu_chung___2\n"
        "A1,50.5,1,3,cong_chuc,0,1\nA2,61,2,5,khac,BTR,0\nA3,,1,1,nong_dan,1,0\n",
        encoding="utf-8",
        newline="\n",
    )
    td = {
        "record_id": {"loai": "text", "nhan": "Mã phiếu", "chu_thich": "Tên SPSS: ID."},
        "tuoi": {
            "loai": "text",
            "nhan": "Câu 2. <b>Tuổi</b> (năm)",
            "kiem_tra": "number",
            "chu_thich": "Tên SPSS: Tuoi.",
        },
        "gioitinh": {"loai": "radio", "nhan": "Giới tính", "lua_chon": "1, Nam | 2, Nữ | X, Khác"},
        "hai_long": {
            "loai": "radio",
            "nhan": "Hài lòng",
            "lua_chon": "1, Rất không | 2, Không | 3, Bình thường | 4, Có | 5, Rất",
        },
        "nghe": {
            "loai": "dropdown",
            "nhan": "Nghề",
            "lua_chon": "cong_chuc, Công chức | khac, Khác | nong_dan, Nông dân",
        },
        "hut_thuoc": {"loai": "yesno", "nhan": "Hút thuốc"},
        "trieu_chung": {"loai": "checkbox", "nhan": "Triệu chứng", "lua_chon": "1, Đau | 2, Khó thở"},
    }
    return p, td


def test_ke_hoach_bien_ten_muc_do_ma_thieu_checkbox(tmp_path):
    p, td = _du_lieu(tmp_path)
    tieu_de, tk, n = C.quet_csv(p)
    ke, canh_bao, de_xuat = C.ke_hoach_bien(tieu_de, tk, td, [{"bien": "*", "ma": "BTR", "nhan": "Bỏ trống"}])
    b = {x["cot"]: x for x in ke}
    assert n == 3
    assert b["record_id"]["ten"] == "ID" and b["tuoi"]["ten"] == "Tuoi"
    assert b["tuoi"]["muc_do"] == "SCALE" and b["tuoi"]["nhan"] == "Câu 2. Tuổi (năm)"  # bỏ thẻ HTML
    assert b["hai_long"]["muc_do"] == "ORDINAL" and b["gioitinh"]["muc_do"] == "NOMINAL"
    assert b["hut_thuoc"]["so"] and b["hut_thuoc"]["doc_chuoi_roi_doi"] and b["hut_thuoc"]["ma_chu"] == {"BTR": -9991}
    assert ("-9991", "BTR — Bỏ trống") in b["hut_thuoc"]["ma_thieu"]
    assert b["trieu_chung___2"]["nhan"] == "Triệu chứng: Khó thở"
    assert b["trieu_chung___2"]["nhan_gia_tri"] == {"1": "Có", "0": "Không"}
    assert not b["nghe"]["so"] and not canh_bao and not de_xuat
    assert b["nghe"]["thieu_chuoi"] == [""]  # biến chuỗi: ô rỗng khai là thiếu (pandas đọc là NaN)


def test_cot_dinh_danh_bi_chan(tmp_path):
    p, td = _du_lieu(tmp_path)
    td["record_id"]["dinh_danh"] = "y"
    tieu_de, tk, _ = C.quet_csv(p)
    with pytest.raises(C.TuChoi, match="ĐỊNH DANH"):
        C.ke_hoach_bien(tieu_de, tk, td, [])


def test_cu_phap_nhan_bien(tmp_path):
    p, td = _du_lieu(tmp_path)
    tieu_de, tk, _ = C.quet_csv(p)
    ke, _, _ = C.ke_hoach_bien(tieu_de, tk, td, [{"bien": "*", "ma": "BTR", "nhan": "Bỏ trống"}])
    s = C.cu_phap_nhan_bien(p, tmp_path / "d.sav", ke, ghi_chu=["thử"])
    # hut_thuoc (0/1/BTR) đọc dạng chuỗi rồi RECODE — độ rộng phải chứa «-9991» (bản cũ A3 cắt thành «-99» hợp lệ)
    assert "ID A2" in s and "Tuoi F8.1" in s and "hut_thuoc A5" in s and "hut_thuoc A3" not in s
    assert "RECODE hut_thuoc ('BTR'='-9991')." in s and "ALTER TYPE hut_thuoc (F8.0)." in s
    assert "MISSING VALUES hut_thuoc (-9991)." in s
    assert "'cong_chuc' 'Công chức'" in s  # mã chữ của biến chuỗi được trích dẫn
    assert "'X'" not in s  # mã chữ «X» không gắn được vào biến số GioiTinh ⇒ bỏ, không làm SPSS lỗi
    assert "VARIABLE LEVEL hai_long (ORDINAL)." in s and s.rstrip().endswith("/COMPRESSED.")
    assert "MISSING VALUES nghe ('')." in s
    assert "* thử." in s  # chú thích kết thúc bằng dấu chấm — không nuốt lệnh kế tiếp


# ───────────── xuat-sav (không SPSS) ─────────────


def _de_tai(tmp_path: Path, monkeypatch) -> Path:
    monkeypatch.setattr(C, "EXPORTS", tmp_path / "exports")
    d = tmp_path / "exports" / "THU"
    (d / "05_clean_locked").mkdir(parents=True)
    p, td = _du_lieu(tmp_path)
    khoa = d / "05_clean_locked" / "k.csv"
    shutil.copy(p, khoa)
    (d / "DATA_LOCK_manifest.json").write_text(
        json.dumps(
            {
                "locked_dataset_path": "05_clean_locked/k.csv",
                "sha256": hashlib.sha256(khoa.read_bytes()).hexdigest(),
                "lock_date": "2026-11-14",
                "status": "LOCKED_FOR_ANALYSIS",
                "analysis_allowed": True,
            }
        ),
        encoding="utf-8",
        newline="\n",
    )
    cot = {
        "ten": "Variable / Field Name",
        "loai": "Field Type",
        "nhan": "Field Label",
        "lua_chon": "Choices, Calculations, OR Slider Labels",
        "kiem_tra": "Text Validation Type OR Show Slider Number",
        "dinh_danh": "Identifier?",
        "chu_thich": "Field Annotation",
    }
    with open(d / "G5_REDCap_dictionary_THU.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, list(cot.values()))
        w.writeheader()
        for ten, x in td.items():
            w.writerow({cot["ten"]: ten, **{cot[k]: v for k, v in x.items()}})
    return d


def _ns(**kw) -> argparse.Namespace:
    d = {"study": "THU", "data": None, "ban_nhap": False, "dictionary": None, "ma_thieu": None, "gate": "G6"}
    d.update(kw)
    return argparse.Namespace(**d)


def test_xuat_sav_khong_co_spss_van_sinh_cu_phap(tmp_path, monkeypatch):
    d = _de_tai(tmp_path, monkeypatch)
    monkeypatch.setattr(C, "tim_spss", lambda: (_ for _ in ()).throw(C.KhongDoDuoc("không có SPSS")))
    assert C.lenh_xuat_sav(_ns()) == C.MA_KHONG_DO
    assert (d / "spss" / "THU_nhan_bien.sps").exists()
    man = json.loads((d / "spss" / "THU_khoa.sav.manifest.json").read_text(encoding="utf-8"))
    assert {b["cot"]: b["ten"] for b in man["bien"]}["tuoi"] == "Tuoi" and man["so_ca_csv"] == 3


def test_xuat_sav_du_lieu_doi_sau_khoa_bi_chan(tmp_path, monkeypatch):
    d = _de_tai(tmp_path, monkeypatch)
    with open(d / "05_clean_locked" / "k.csv", "a", encoding="utf-8") as f:
        f.write("A4,40,1,2,khac,0,0\n")
    assert C.main(["xuat-sav", "--study", "THU"]) == C.MA_TU_CHOI


def test_xuat_sav_data_ngoai_khoa_phai_kem_ban_nhap(tmp_path, monkeypatch):
    _de_tai(tmp_path, monkeypatch)
    assert C.main(["xuat-sav", "--study", "THU", "--data", str(tmp_path / "d.csv")]) == C.MA_TU_CHOI


# ───────────── cú pháp phân tích ─────────────


def test_cu_phap_cox_tho_loc_cung_tap_ca_voi_python(tmp_path):
    vb, _, _ = C.cu_phap_phan_tich("THU", _man(), _dt(time="thoi_gian", event="bien_co"), tmp_path, sav="x.sav")
    i = vb.index("COXREG thoi_gian /STATUS=bien_co(1) /METHOD=ENTER Nhom /PRINT")
    truoc = vb[vb.rindex("OMS ", 0, i) : i]
    assert "TEMPORARY." in truoc and "SELECT IF (NOT MISSING(Tuoi) AND NOT MISSING(GioiTinh))." in truoc


def test_cu_phap_nhi_phan_va_cum(tmp_path):
    vb, cb, _ = C.cu_phap_phan_tich("THU", _man(), _dt(outcome="kq_nhi", cot_cum="ban_kham"), tmp_path, sav="x.sav")
    assert "SET OLANG=ENGLISH TVARS=NAMES TNUMBERS=VALUES." in vb
    assert "CROSSTABS /TABLES=Nhom BY kq_nhi /STATISTICS=CHISQ RISK" in vb
    assert "LOGISTIC REGRESSION VARIABLES kq_nhi" in vb and "/METHOD=ENTER Nhom Tuoi GioiTinh" in vb
    assert "/REPEATED SUBJECT=ban_kham" in vb and any("GENLIN" in c for c in cb)


def test_cu_phap_khong_co_bien_so_khong_de_with_rong(tmp_path):
    man = _man()
    for b in man["bien"]:
        if b["cot"] in ("tuoi", "gioitinh", "nhom"):
            b["so"] = False
    vb, _, _ = C.cu_phap_phan_tich("THU", man, _dt(outcome="diem", outcome_type="continuous"), tmp_path, sav="x.sav")
    assert "UNIANOVA diem\n    BY Nhom Tuoi GioiTinh\n" in vb and "WITH \n" not in vb and "WITH\n" not in vb


# ───────────── đọc OXML thật ─────────────


def test_doc_ket_qua_nhi_phan(tmp_path):
    kq = C.doc_ket_qua(_kq_tu_mau(tmp_path, "binary"), _dt(outcome="kq_nhi", outcome_type="binary"), _man())
    kc = kq["ket_cuc_chinh"]
    assert kc["or"] == pytest.approx(3.0776914539, rel=1e-6) and kc["ci"][0] == pytest.approx(1.79378426, rel=1e-6)
    assert kc["p_yates"] == pytest.approx(6.0635e-05, rel=1e-3)
    hs = kq["da_bien"]["he_so"]
    assert set(hs) == {"nhom", "tuoi", "gioitinh"}  # tên SPSS đã đổi ngược về tên cột G6
    assert hs["nhom"]["uoc_luong"] == pytest.approx(3.27287066, rel=1e-6)
    assert hs["nhom"]["ci"] == pytest.approx([1.84246642, 5.81377344], rel=1e-6)


def test_doc_ket_qua_lien_tuc_doi_dau_hieu_trung_binh(tmp_path):
    kq = C.doc_ket_qua(_kq_tu_mau(tmp_path, "continuous"), _dt(outcome="diem", outcome_type="continuous"), _man())
    w = kq["ket_cuc_chinh"]["welch"]
    assert w["md_g1_tru_g0"] == pytest.approx(4.8032477678, rel=1e-6)  # SPSS in nhóm 0 − nhóm 1 = −4,803
    assert w["ci"][0] < w["ci"][1] and w["ci"][0] > 0
    assert kq["da_bien"]["thang"] == "B" and kq["da_bien"]["he_so"]["nhom"]["uoc_luong"] == pytest.approx(
        4.7033407, rel=1e-6
    )


def test_doc_ket_qua_thu_tu_lay_mu_cua_b(tmp_path):
    kq = C.doc_ket_qua(_kq_tu_mau(tmp_path, "ordinal"), _dt(outcome="hai_long", outcome_type="ordinal"), _man())
    hs = kq["da_bien"]["he_so"]
    assert "hai_long" not in hs and set(hs) == {"nhom", "tuoi", "gioitinh"}  # ngưỡng (Threshold) bị loại
    assert hs["nhom"]["uoc_luong"] == pytest.approx(2.37319, rel=1e-4) and hs["nhom"]["b"] == pytest.approx(
        0.86427, rel=1e-4
    )


def test_doc_ket_qua_cum_va_song_con(tmp_path):
    kq = C.doc_ket_qua(
        _kq_tu_mau(tmp_path, "cum"), _dt(outcome="kq_nhi", outcome_type="binary", cot_cum="ban_kham"), _man()
    )
    g = kq["da_bien_cum"]["he_so"]["nhom"]
    assert g["uoc_luong"] == pytest.approx(3.2728, rel=1e-3) and g["p"] is not None and g["ci"][0] > 1.4
    kq = C.doc_ket_qua(_kq_tu_mau(tmp_path / "s", "song_con"), _dt(time="thoi_gian", event="bien_co"), _man())
    assert kq["song_con_tho"]["he_so"]["nhom"]["uoc_luong"] == pytest.approx(2.2379, rel=1e-3)
    assert kq["song_con_hieu_chinh"]["he_so"]["nhom"]["uoc_luong"] == pytest.approx(2.2591265, rel=1e-6)


# ───────────── đối chiếu với kết quả Python ─────────────


def _tom_nhi_phan(or_nhom: float = 3.273) -> dict:
    return {
        "dac_ta_phan_tich": _dt(outcome="kq_nhi", outcome_type="binary"),
        "primary_outcome": {"outcome_type": "binary", "or_crude": 3.078, "ci_95": [1.794, 5.281], "p_value": 0.0001},
        "multivariate": {
            "model": "logistic",
            "results": [
                {"variable": "nhom", "OR_adj": or_nhom, "CI_95": [1.842, 5.814], "p": 0.0001},
                {"variable": "tuoi", "OR_adj": 1.04, "CI_95": [1.014, 1.067], "p": 0.0024},
                {"variable": "gioitinh", "OR_adj": 1.803, "CI_95": [1.021, 3.184], "p": 0.0422},
            ],
        },
    }


def test_doi_chieu_khop_roi_lech(tmp_path):
    kq = C.doc_ket_qua(_kq_tu_mau(tmp_path, "binary"), _dt(outcome="kq_nhi", outcome_type="binary"), _man())
    dong = C.doi_chieu(_tom_nhi_phan(), kq)
    assert len(dong) == 4 and all(x["trang_thai"] == "khop" for x in dong)
    dong = C.doi_chieu(_tom_nhi_phan(or_nhom=3.45), kq)  # Python lệch 5 % ⇒ phải bắt
    assert {x["muc"].split("— ")[-1]: x["trang_thai"] for x in dong}["nhom"] == "lech"


def test_doi_chieu_cum_la_lech_nho_khong_phai_lech(tmp_path):
    kq = C.doc_ket_qua(
        _kq_tu_mau(tmp_path, "cum"), _dt(outcome="kq_nhi", outcome_type="binary", cot_cum="ban_kham"), _man()
    )
    tom = _tom_nhi_phan()
    tom["dac_ta_phan_tich"]["cot_cum"] = "ban_kham"
    tom["multivariate"]["results"][0].update({"CI_95": [1.091, 9.817], "p": 0.0392})
    nhom = next(x for x in C.doi_chieu(tom, kq) if x["muc"].endswith("nhom"))
    assert nhom["trang_thai"] == "lech_nho" and "GEE" in nhom["ghi_chu"]


def _de_tai_co_sav(tmp_path: Path, monkeypatch, *, dt: dict | None = None) -> Path:
    """Đề tài giả có .sav (tệp byte giả, SHA-256 khớp manifest) + cú pháp sinh bằng cu-phap."""
    monkeypatch.setattr(C, "EXPORTS", tmp_path / "exports")
    d = tmp_path / "exports" / "THU"
    (d / "spss").mkdir(parents=True)
    sav = d / "spss" / "THU_khoa.sav"
    sav.write_bytes(b"$FL2 gia lap")
    man = _man() | {
        "sav": str(sav),
        "sav_da_tao": True,
        "sha256_sav": hashlib.sha256(sav.read_bytes()).hexdigest(),
        "sha256_nguon": "abc",
    }
    (d / "spss" / "THU_khoa.sav.manifest.json").write_text(json.dumps(man), encoding="utf-8", newline="\n")
    dt = dt or _dt(outcome="kq_nhi", outcome_type="binary")
    (d / "G6_analysis_summary.json").write_text(json.dumps({"dac_ta_phan_tich": dt}), encoding="utf-8", newline="\n")
    assert C.main(["cu-phap", "--study", "THU"]) == C.MA_OK
    return d


def _gia_lap_spss(monkeypatch, kich_ban: str, *, ma: int = 0):
    goi = []

    def gia_lap(py, doi_so, *, thu_muc, thoi_han=0):
        goi.append((doi_so, (thu_muc / "phan_tich.sps").read_text(encoding="utf-8")))
        if ma == 0:
            for f in (FX / kich_ban).glob("oms_*.xml"):
                shutil.copy(f, thu_muc / "kq" / f.name)
        return ma, "PHIEN_BAN=31.0\nSO_CA=240\n", "" if ma == 0 else "LOI_SPSS hỏng"

    monkeypatch.setattr(C, "tim_spss", lambda: Path("python-cua-spss"))
    monkeypatch.setattr(C, "chay_spss", gia_lap)
    return goi


def test_lenh_chay_va_doi_chieu_gia_lap_spss(tmp_path, monkeypatch):
    d = _de_tai_co_sav(tmp_path, monkeypatch)
    goi = _gia_lap_spss(monkeypatch, "binary")
    assert C.main(["chay", "--study", "THU"]) == C.MA_OK
    doi_so, vb = goi[0]
    assert doi_so[0] == "--cu-phap"
    # chạy trong VÙNG TẠM đường dẫn ngắn (SPSS hỏng khi đường dẫn > ~255 byte), không phải đường OneDrive
    assert "vao.sav" in vb and str(d) not in vb
    kq = json.loads((d / "G6_spss_ket_qua.json").read_text(encoding="utf-8"))
    assert kq["spss_phien_ban"] == "31.0" and "nhom" in kq["ket_qua"]["da_bien"]["he_so"]
    assert (d / "spss" / "ket_qua" / "oms_da_bien.xml").exists()  # kết quả đã chép về
    tom = _tom_nhi_phan() | {"data_lock": {"sha256": "abc"}}
    (d / "G6_analysis_summary.json").write_text(json.dumps(tom), encoding="utf-8", newline="\n")
    assert C.main(["doi-chieu", "--study", "THU"]) == C.MA_OK
    assert "4 khớp" in (d / "G6_spss_doi_chieu.md").read_text(encoding="utf-8")
    tom["data_lock"]["sha256"] = "khac"  # SPSS và Python không cùng bộ dữ liệu khoá ⇒ chặn
    (d / "G6_analysis_summary.json").write_text(json.dumps(tom), encoding="utf-8", newline="\n")
    assert C.main(["doi-chieu", "--study", "THU"]) == C.MA_TU_CHOI
    del tom["data_lock"]  # thiếu SHA-256 phía Python ⇒ KHÔNG đo được (bản cũ bỏ qua chốt, vẫn «khớp»)
    (d / "G6_analysis_summary.json").write_text(json.dumps(tom), encoding="utf-8", newline="\n")
    assert C.main(["doi-chieu", "--study", "THU"]) == C.MA_KHONG_DO


def test_doi_chieu_chan_ket_qua_spss_cu_va_dac_ta_lech(tmp_path, monkeypatch):
    d = _de_tai_co_sav(tmp_path, monkeypatch)
    _gia_lap_spss(monkeypatch, "binary")
    assert C.main(["chay", "--study", "THU"]) == C.MA_OK
    tom = _tom_nhi_phan() | {"data_lock": {"sha256": "abc"}}
    tom["dac_ta_phan_tich"]["covariates"] = ["tuoi"]  # Python chạy với bộ hiệp biến khác ⇒ chặn
    (d / "G6_analysis_summary.json").write_text(json.dumps(tom), encoding="utf-8", newline="\n")
    assert C.main(["doi-chieu", "--study", "THU"]) == C.MA_TU_CHOI
    tom["dac_ta_phan_tich"]["covariates"] = ["tuoi", "gioitinh"]
    (d / "G6_analysis_summary.json").write_text(json.dumps(tom), encoding="utf-8", newline="\n")
    kq_p = d / "G6_spss_ket_qua.json"
    kq = json.loads(kq_p.read_text(encoding="utf-8"))
    kq["sha256_sav"] = "cua-sav-truoc"  # kết quả SPSS của .sav CŨ ⇒ chặn
    kq_p.write_text(json.dumps(kq), encoding="utf-8", newline="\n")
    assert C.main(["doi-chieu", "--study", "THU"]) == C.MA_TU_CHOI


def test_chay_hong_xoa_ket_qua_cu_va_chan_sps_sua_tay(tmp_path, monkeypatch):
    d = _de_tai_co_sav(tmp_path, monkeypatch)
    _gia_lap_spss(monkeypatch, "binary")
    assert C.main(["chay", "--study", "THU"]) == C.MA_OK and (d / "G6_spss_ket_qua.json").exists()
    _gia_lap_spss(monkeypatch, "binary", ma=1)
    assert C.main(["chay", "--study", "THU"]) == C.MA_LECH
    assert not (d / "G6_spss_ket_qua.json").exists()  # lượt hỏng không để lại kết quả lượt trước
    sps = d / "spss" / "THU_phan_tich.sps"
    sps.write_text(sps.read_text(encoding="utf-8") + "* sửa tay.\n", encoding="utf-8", newline="\n")
    assert C.main(["chay", "--study", "THU"]) == C.MA_TU_CHOI


def test_dac_ta_lay_tu_tom_tat_g6(tmp_path, monkeypatch):
    monkeypatch.setattr(C, "EXPORTS", tmp_path / "exports")
    d = tmp_path / "exports" / "THU"
    d.mkdir(parents=True)
    (d / "G6_analysis_summary.json").write_text(
        json.dumps({"dac_ta_phan_tich": _dt(outcome="kq_nhi")}), encoding="utf-8", newline="\n"
    )
    ns = argparse.Namespace(
        study="THU",
        gate="G6",
        outcome=None,
        group=None,
        covariates=None,
        outcome_type=None,
        time=None,
        event=None,
        cot_cum=None,
    )
    assert C.dac_ta(ns)["outcome"] == "kq_nhi" and C.dac_ta(ns)["covariates"] == ["tuoi", "gioitinh"]
    ns.covariates = "tuoi"
    assert C.dac_ta(ns)["covariates"] == ["tuoi"]


# ───────────── tìm SPSS, nhập .sav, từ điển REDCap ─────────────


def test_tim_python_spss_bo_qua_python3_hong(tmp_path, monkeypatch):
    b = tmp_path / "IBM SPSS Statistics" / "Resources" / "Python3" / "bin"
    b.mkdir(parents=True)
    for ten in ("python3", "python3.13", "python3.13-config", "python3.9"):
        (b / ten).write_text("", encoding="utf-8", newline="\n")
    monkeypatch.delenv("EBM_SPSS_PYTHON", raising=False)
    monkeypatch.setattr(C.sys, "platform", "darwin")
    assert [p.name for p in C.ung_vien_python_spss(tmp_path)] == ["python3.13", "python3.9"]
    monkeypatch.setenv("EBM_SPSS_PYTHON", "/khac/python")
    assert C.ung_vien_python_spss(tmp_path) == [Path("/khac/python")]


def test_nhap_sav_tu_choi_thu_muc_ra_trong_repo(tmp_path):
    sav = tmp_path / "a.sav"
    sav.write_bytes(b"$FL2")
    assert C.main(["nhap-sav", "--sav", str(sav), "--ra", str(C.BASE / "exports" / "_khong_duoc")]) == C.MA_TU_CHOI


def test_ghi_tu_dien_redcap(tmp_path):
    p = tmp_path / "td.csv"
    C.ghi_tu_dien_redcap(
        [
            {
                "ten": "GioiTinh",
                "nhan": "Giới tính",
                "kieu": 0,
                "dinh_dang": "F1",
                "muc_do": "NOMINAL",
                "nhan_gia_tri": {"1.0": "Nam", "2.0": "Nữ"},
                "thieu": [1, 9.0, None, None],
            },
            {
                "ten": "Tuoi",
                "nhan": "Tuổi",
                "kieu": 0,
                "dinh_dang": "F5.1",
                "muc_do": "SCALE",
                "nhan_gia_tri": {},
                "thieu": [0],
            },
            {
                "ten": "SoCon",
                "nhan": "",
                "kieu": 0,
                "dinh_dang": "F2",
                "muc_do": "SCALE",
                "nhan_gia_tri": {},
                "thieu": [0],
            },
        ],
        p,
    )
    r = {x["Variable / Field Name"]: x for x in csv.DictReader(open(p, encoding="utf-8"))}
    assert (
        r["gioitinh"]["Field Type"] == "radio"
        and r["gioitinh"]["Choices, Calculations, OR Slider Labels"] == "1, Nam | 2, Nữ"
    )
    assert (
        "Tên SPSS: GioiTinh" in r["gioitinh"]["Field Annotation"]
        and "Mã thiếu SPSS: 9" in r["gioitinh"]["Field Annotation"]
    )
    assert r["tuoi"]["Text Validation Type OR Show Slider Number"] == "number"
    assert (
        r["socon"]["Text Validation Type OR Show Slider Number"] == "integer" and r["socon"]["Field Label"] == "SoCon"
    )
    assert r["gioitinh"]["Identifier?"] == ""


# ───────────── vá sau rà độc lập 14/11/2026 ─────────────


def test_goi_ds_va_duong_dan_khong_gop_khoang_trang():
    ten = [f"bien_ten_rat_dai_so_{i:02d}_cho_thong_ke_vien" for i in range(70)]
    s = C.goi_ds(ten)
    assert all(len(x.encode("utf-8")) <= 204 for x in s.split("\n")) and s.split() == ten
    assert C.dd_spss("/a/OneDrive  hai cach/t.csv") == "'/a/OneDrive  hai cach/t.csv'"  # bản cũ gộp thành một dấu cách
    assert C.chuoi_spss("a  b") == "'a b'"  # nhãn vẫn gộp khoảng trắng


def test_chuan_ten_khong_sinh_ten_hong():
    for x in ("#nhap", "$sys", "9x", "a" * 63 + ".b", "_x"):
        assert C.ten_hop_le(C.chuan_ten(x)), (x, C.chuan_ten(x))
    assert not C.ten_hop_le("#nhap") and not C.ten_hop_le("$sys")  # biến nháp/biến hệ thống không lưu được


def test_cu_phap_nhan_bien_goi_dong_dai_va_chu_thich_co_dau_cham(tmp_path):
    ten = [f"cau_hoi_hai_long_linh_vuc_{i:02d}_chi_tiet" for i in range(70)]
    p = tmp_path / "d.csv"
    p.write_text(",".join(ten) + "\n" + ",".join("1" for _ in ten) + "\n", encoding="utf-8", newline="\n")
    tieu_de, tk, _ = C.quet_csv(p)
    td = {t: {"loai": "radio", "nhan": t, "lua_chon": "1, Có | 0, Không"} for t in ten}
    ke, _, _ = C.ke_hoach_bien(tieu_de, tk, td, [])
    s = C.cu_phap_nhan_bien(p, tmp_path / "d.sav", ke, ghi_chu=["Nguồn: d.csv · 1 ca", "câu không có dấu chấm"])
    assert max(len(x.encode("utf-8")) for x in s.split("\n")) <= 260  # đo 14/11: > ~1024 byte ⇒ SPSS lỗi cú pháp
    assert all(x.endswith(".") for x in s.split("\n") if x.startswith("*"))


def test_ma_thieu_qua_3_gom_khoang_va_tu_choi_khi_khong_khai_duoc():
    assert C.menh_de_thieu_so("x", ["998"], [-9991, -9992, -9993]) == "LO THRU -9991, 998"
    assert C.menh_de_thieu_so("x", ["7", "8", "9", "10"], []) == "7 THRU 10"
    assert C.menh_de_thieu_so("x", ["8", "9"], [-9991]) == "8, 9, -9991"
    with pytest.raises(C.TuChoi, match="3 giá trị rời"):
        C.menh_de_thieu_so("x", ["8", "9"], [-9991, -9992])


def _td_c1a() -> dict:
    likert = (
        "1, Rất không hài lòng | 2, Không hài lòng | 3, Bình thường/Không ý kiến | 4, Hài lòng | 5, Rất hài lòng"
        " | 8, Không biết/không nhớ | 9, Không trả lời/từ chối"
    )
    return {
        "a1": {"loai": "radio", "nhan": "A1", "lua_chon": likert},
        "nghenghiep": {
            "loai": "radio",
            "nhan": "Nghề",
            "lua_chon": "1, CBCC/viên chức | 2, Nông/Lâm/Ngư | 3, Công nhân | 4, LĐ tự do | 5, Hưu trí | 6, Nội trợ",
        },
        "khoangcach": {"loai": "radio", "nhan": "KC", "lua_chon": "1, Dưới 5 km | 2, 5–10 km | 3, Trên 10 km"},
        "ykien": {"loai": "notes", "nhan": "Ý kiến đóng góp"},
    }


def test_muc_do_thu_tu_va_de_xuat_ma_thieu_theo_nhan(tmp_path):
    p = tmp_path / "d.csv"
    p.write_text("a1,nghenghiep,khoangcach,ykien\n4,2,1,tot\n9,5,3,\n", encoding="utf-8", newline="\n")
    tieu_de, tk, _ = C.quet_csv(p)
    ke, cb, de_xuat = C.ke_hoach_bien(tieu_de, tk, _td_c1a(), [])
    b = {x["cot"]: x for x in ke}
    # Likert có mã 8/9 vẫn là ORDINAL; nghề nghiệp mã 1..6 liên tiếp KHÔNG phải thứ tự;
    # khoảng cách «dưới/trên» là thứ tự
    assert b["a1"]["muc_do"] == "ORDINAL" and b["nghenghiep"]["muc_do"] == "NOMINAL"
    assert b["khoangcach"]["muc_do"] == "ORDINAL"
    assert {(x["bien"], x["ma"]) for x in de_xuat} == {("a1", "8"), ("a1", "9")}  # chỉ đề xuất, không tự khai
    assert b["a1"]["menh_de_thieu"] is None and any("de-xuat-ma-thieu" in c for c in cb)
    assert b["ykien"]["bo"] and not b["a1"]["bo"]  # văn bản tự do bị bỏ khỏi .sav
    s = C.cu_phap_nhan_bien(p, tmp_path / "d.sav", ke, ghi_chu=[])
    assert "/DROP=ykien." in s and "ykien '" not in s.split("VARIABLE LABELS")[1]
    ke2, _, _ = C.ke_hoach_bien(tieu_de, tk, _td_c1a(), [], giu_ghi_chu=True)
    assert not {x["cot"]: x for x in ke2}["ykien"]["bo"]


def test_ma_thieu_mau_glob_ap_ma_so_con_sao_tran_khong(tmp_path):
    p = tmp_path / "d.csv"
    p.write_text("a1,a2,nghenghiep\n4,8,2\n9,5,9\n", encoding="utf-8", newline="\n")
    tieu_de, tk, _ = C.quet_csv(p)
    td = _td_c1a() | {"a2": _td_c1a()["a1"]}
    mt = [
        {"bien": "a?", "ma": "8", "nhan": "Không biết"},
        {"bien": "a?", "ma": "9", "nhan": "Từ chối"},
        {"bien": "*", "ma": "9", "nhan": "mã số với «*» KHÔNG áp mọi trường"},
    ]
    ke, _, de_xuat = C.ke_hoach_bien(tieu_de, tk, td, mt)
    b = {x["cot"]: x for x in ke}
    assert b["a1"]["menh_de_thieu"] == "8, 9" and b["a2"]["menh_de_thieu"] == "8, 9"
    assert b["nghenghiep"]["menh_de_thieu"] is None and not de_xuat


def test_bien_chuoi_ma_chu_giu_nguyen_va_nhan_vua_do_rong(tmp_path):
    p = tmp_path / "d.csv"
    p.write_text("ban_kham,nghe\nP1,A\n,BTR\nP2,B\n", encoding="utf-8", newline="\n")
    tieu_de, tk, _ = C.quet_csv(p)
    td = {"nghe": {"loai": "dropdown", "nhan": "Nghề", "lua_chon": "A, Công chức | B, Nông dân | XYZW, Khác"}}
    ke, _, _ = C.ke_hoach_bien(tieu_de, tk, td, [{"bien": "*", "ma": "BTR", "nhan": "Bỏ trống"}])
    b = {x["cot"]: x for x in ke}
    assert b["ban_kham"]["thieu_chuoi"] == [""] and b["nghe"]["thieu_chuoi"] == ["", "BTR"]
    assert b["nghe"]["ma_chu"] == {} and b["nghe"]["rong"] >= 4  # nhãn «XYZW» vừa độ rộng (Warning #4487)
    s = C.cu_phap_nhan_bien(p, tmp_path / "d.sav", ke, ghi_chu=[])
    assert "MISSING VALUES nghe ('', 'BTR')." in s and "'-9991'" not in s and "RECODE nghe" not in s


def test_cot_ten_nghi_pii_bi_chan_ca_khi_khong_co_trong_tu_dien(tmp_path):
    p = tmp_path / "d.csv"
    p.write_text("cobhyt,so_dien_thoai\n1,0901\n", encoding="utf-8", newline="\n")
    tieu_de, tk, _ = C.quet_csv(p)
    with pytest.raises(C.TuChoi, match="so_dien_thoai"):
        C.ke_hoach_bien(tieu_de, tk, {"cobhyt": {"loai": "yesno", "nhan": "Có BHYT"}}, [])
    assert C._quet_pii_ten(["cobhyt"]) == []  # C1a: «có BHYT» (có/không) — luật bổ sung không bắt nhầm số thẻ


def test_xuat_sav_chan_manifest_chua_khoa(tmp_path, monkeypatch):
    d = _de_tai(tmp_path, monkeypatch)
    man_p = d / "DATA_LOCK_manifest.json"
    man = json.loads(man_p.read_text(encoding="utf-8"))
    man["status"] = "DRAFT"
    man_p.write_text(json.dumps(man), encoding="utf-8", newline="\n")
    assert C.main(["xuat-sav", "--study", "THU"]) == C.MA_TU_CHOI
    man["status"], man["sha256"] = "LOCKED_FOR_ANALYSIS", None  # thiếu SHA-256 ⇒ chặn (bản cũ bỏ qua kiểm)
    man_p.write_text(json.dumps(man), encoding="utf-8", newline="\n")
    assert C.main(["xuat-sav", "--study", "THU"]) == C.MA_TU_CHOI


def test_cu_phap_phoi_nhiem_lien_tuc_thu_tu_c1a(tmp_path):
    man = _man()
    for b in man["bien"]:
        if b["cot"] == "tuoi":
            b["muc"] = None  # > 20 giá trị — vai «thời gian chờ»
    dt = _dt(outcome="hai_long", group="tuoi", covariates=["gioitinh"], outcome_type="ordinal")
    vb, cb, phu = C.cu_phap_phan_tich("THU", man, dt | {"don_vi_phoi_nhiem": 15}, tmp_path, sav="x.sav")
    assert "oms_bang1" not in vb and any("phơi nhiễm liên tục" in c for c in cb)  # như Python: không Bảng 1
    assert "COMPUTE Tuoi_dv = Tuoi / 15." in vb and phu == {"ten_phoi_nhiem_mo_hinh": "Tuoi_dv"}
    assert "PLUM hai_long" in vb and "WITH Tuoi_dv GioiTinh" in vb
    vb2, _, phu2 = C.cu_phap_phan_tich("THU", man, dt, tmp_path, sav="x.sav")  # không đơn vị ⇒ mỗi 1 đơn vị
    assert "COMPUTE" not in vb2 and "WITH Tuoi GioiTinh" in vb2 and phu2 == {}
    with pytest.raises(C.TuChoi, match="2 mức"):  # kết cục nhị phân vẫn đòi nhóm 2 mức
        C.cu_phap_phan_tich("THU", man, _dt(outcome="kq_nhi", group="tuoi"), tmp_path, sav="x.sav")


def test_doc_ket_qua_doi_ten_phoi_nhiem_chia_don_vi(tmp_path):
    kq = C.doc_ket_qua(
        _kq_tu_mau(tmp_path, "ordinal"),
        _dt(outcome="hai_long", outcome_type="ordinal", ten_phoi_nhiem_mo_hinh="Nhom"),
        {"bien": [b for b in _man()["bien"] if b["cot"] != "nhom"]},
    )
    assert "nhom" in kq["da_bien"]["he_so"]


def test_dac_ta_doc_don_vi_phoi_nhiem(tmp_path, monkeypatch):
    monkeypatch.setattr(C, "EXPORTS", tmp_path / "exports")
    d = tmp_path / "exports" / "THU"
    d.mkdir(parents=True)
    ns = argparse.Namespace(study="THU", gate="G6", covariates=None)
    (d / "G6_analysis_summary.json").write_text(
        json.dumps({"dac_ta_phan_tich": _dt(outcome="g1"), "ordinal": {"don_vi_phoi_nhiem": {"don_vi": 15.0}}}),
        encoding="utf-8",
        newline="\n",
    )
    assert C.dac_ta(ns)["don_vi_phoi_nhiem"] == 15.0  # tóm tắt cũ: lấy từ khối ordinal
    ns.don_vi_phoi_nhiem = 0
    with pytest.raises(C.TuChoi):
        C.dac_ta(ns)


def test_so_mot_thang_log_va_nguong_p():
    py = {"uoc_luong": 1.035, "ci": [0.80, 1.34], "p": 0.30}
    assert C.so_mot("x", py, {"uoc_luong": 1.030, "ci": [0.80, 1.34], "p": 0.30}, ty_so=True)["trang_thai"] == "lech"
    # bản cũ (±0,5 % trên thang OR) gọi cặp này là «khớp» dù β lệch 16 %
    khop = C.so_mot("x", py, {"uoc_luong": 1.0352, "ci": [0.8001, 1.3402], "p": 0.3001}, ty_so=True, lam_tron=0.0005)
    assert khop["trang_thai"] == "khop"  # lệch trong nửa đơn vị làm tròn của Python ⇒ khớp
    # không có KTC: thang OR (±0,5 % của 1,035) gọi cặp này «khớp»; thang log (±0,5 % của β = 0,034) thì không
    khong_ci = C.so_mot("x", {"uoc_luong": 1.035, "ci": None}, {"uoc_luong": 1.030, "ci": None}, ty_so=True)
    assert khong_ci["trang_thai"] == "lech"
    # KTC rất hẹp: SPSS 3,0776914 so Python 3,078 (đã làm tròn 3 chữ số) chỉ khớp nhờ nửa đơn vị làm tròn
    hep_py = {"uoc_luong": 3.078, "ci": [3.070, 3.086], "p": 0.0001}
    hep_sp = {"uoc_luong": 3.0776914, "ci": [3.0702, 3.0858], "p": 0.0001}
    assert C.so_mot("x", hep_py, hep_sp, ty_so=True, lam_tron=0.0005)["trang_thai"] == "khop"
    assert C.so_mot("x", hep_py, hep_sp, ty_so=True)["trang_thai"] == "lech"
    p_doi = C.so_mot(
        "x", {"uoc_luong": 2.0, "ci": [1.0, 4.0], "p": 0.048}, {"uoc_luong": 2.0, "ci": [1.0, 4.0], "p": 0.052}
    )
    assert p_doi["trang_thai"] == "lech" and "0,05" in p_doi["ghi_chu"]
    cox = C.so_mot(
        "x",
        {"uoc_luong": 2.0, "ci": [1.0, 4.0], "p": 0.04},
        {"uoc_luong": 2.02, "ci": [1.0, 4.1], "p": 0.04},
        ty_so=True,
        phuong_phap_khac="Breslow ≠ Efron",
    )
    assert cox["trang_thai"] == "lech_nho"
    xa = C.so_mot(
        "x",
        {"uoc_luong": 2.0, "ci": [1.0, 4.0], "p": 0.04},
        {"uoc_luong": 3.0, "ci": [1.5, 6.0], "p": 0.01},
        ty_so=True,
        phuong_phap_khac="Breslow ≠ Efron",
    )
    assert xa["trang_thai"] == "lech"  # khác phương pháp KHÔNG che lệch lớn


def test_doi_chieu_khong_bo_dong_im_lang():
    tom = _tom_nhi_phan()
    tom["multivariate"] = {"error": "Pandas data cast to numpy dtype of object"}
    tom["survival"] = {"crude": {"HR": 2.1, "CI_95": [1.2, 3.6], "p": 0.01}}
    tom["dac_ta_phan_tich"]["cot_cum"] = None
    dong = C.doi_chieu(tom, {})
    tt = {x["muc"]: x for x in dong}
    assert tt["Đa biến"]["trang_thai"] == "khong_so_duoc" and "Python" in tt["Đa biến"]["ghi_chu"]
    assert tt["Kết cục chính"]["trang_thai"] == "khong_so_duoc"
    assert any(x["muc"].startswith("Cox") and x["trang_thai"] == "khong_so_duoc" for x in dong)
    tom = _tom_nhi_phan()
    tom["dac_ta_phan_tich"]["cot_cum"] = "ban_kham"
    kq = {"da_bien": {"thang": "OR", "he_so": {"nhom": {"uoc_luong": 3.273, "ci": [1.84, 5.81], "p": 0.0001}}}}
    dong = C.doi_chieu(tom, kq)  # có cụm mà SPSS thiếu GENLIN ⇒ KHÔNG so với mô hình không hiệu chỉnh cụm
    assert any("GENLIN" in x["ghi_chu"] and x["trang_thai"] == "khong_so_duoc" for x in dong)
    assert not any(x["trang_thai"] == "khop" and "nhom" in x["muc"] and "Đa biến" in x["muc"] for x in dong)


def test_he_so_khong_bo_bien_ten_bat_dau_bang_step():
    bang = {
        "o": [
            {"hang": ["steps"], "cot": ["B"], "so": 0.5},
            {"hang": ["steps"], "cot": ["Sig."], "so": 0.01},
            {"hang": ["Step 0", "nhom"], "cot": ["B"], "so": 9.0},
            {"hang": ["Step 1a", "nhom"], "cot": ["B"], "so": 1.2},
        ]
    }
    hs = C.he_so(bang, mu=False)
    assert hs["steps"]["uoc_luong"] == 0.5 and hs["nhom"]["uoc_luong"] == 1.2


def test_mo_ta_thieu_khoang_lo_hi():
    assert C.mo_ta_thieu([-2, "LO", -1.0, None]) == "LO THRU -1"
    assert C.mo_ta_thieu([-3, -1.7976931348623157e308, -1.0, 99.0]) == "LO THRU -1, 99"
    assert C.mo_ta_thieu([2, 8.0, 9.0, None]) == "8, 9"


def test_nhap_sav_chan_moi_repo_git_khong_phan_biet_hoa_thuong(tmp_path):
    repo = tmp_path / "RepoKhac"
    (repo / ".git").mkdir(parents=True)
    sav = tmp_path / "a.sav"
    sav.write_bytes(b"$FL2")
    assert C.main(["nhap-sav", "--sav", str(sav), "--ra", str(repo / "ra")]) == C.MA_TU_CHOI
    assert C._trong_repo_git(Path(str(C.BASE).swapcase()) / "x") is not None or sys.platform not in ("darwin", "win32")


@pytest.mark.skipif(sys.platform == "win32", reason="nhóm tiến trình POSIX")
def test_chay_spss_het_han_dung_ca_tien_trinh_con(tmp_path, monkeypatch):
    pid_p = tmp_path / "con.pid"
    trinh = tmp_path / "gia_spss.py"
    trinh.write_text(
        "import subprocess, sys, time\n"
        "c = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])\n"
        f"open({str(pid_p)!r}, 'w').write(str(c.pid))\n"
        "print('PHIEN_BAN=gia', flush=True)\n"
        "time.sleep(60)\n",
        encoding="utf-8",
        newline="\n",
    )
    monkeypatch.setattr(C, "TRINH_CHAY", trinh)
    import os
    import time

    t0 = time.monotonic()
    ma, out, err = C.chay_spss(Path(sys.executable), [], thu_muc=tmp_path, thoi_han=3)
    assert ma == 1 and "quá thời hạn" in err and "PHIEN_BAN=gia" in out and time.monotonic() - t0 < 20
    time.sleep(0.5)
    pid = int(pid_p.read_text())
    with pytest.raises(ProcessLookupError):  # tiến trình con (vai lõi SPSS) KHÔNG mồ côi
        os.kill(pid, 0)


@pytest.mark.skipif(sys.platform == "win32", reason="nhóm tiến trình POSIX")
def test_chay_spss_khong_treo_khi_con_giu_ong_ra(tmp_path, monkeypatch):
    trinh = tmp_path / "gia_spss_loi.py"
    trinh.write_text(
        "import subprocess, sys\n"
        "subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])\n"
        "print('LOI_SPSS gia', file=sys.stderr)\n"
        "sys.exit(1)\n",
        encoding="utf-8",
        newline="\n",
    )
    monkeypatch.setattr(C, "TRINH_CHAY", trinh)
    import time

    t0 = time.monotonic()
    ma, _, err = C.chay_spss(Path(sys.executable), [], thu_muc=tmp_path, thoi_han=30)
    assert ma == 1 and "LOI_SPSS gia" in err and time.monotonic() - t0 < 15  # bản cũ (ống dẫn) chờ hết 30 giây


def test_trinh_chay_nen_tham_so_va_ma_thieu_khoang(capsys):
    import spss_chay_nen as N  # chỉ import `spss` SAU khi kiểm tham số ⇒ chạy được không cần SPSS

    assert N.main([]) == 2 and N.main(["--sai", "x"]) == 2 and "dùng:" in capsys.readouterr().err
    assert N._thieu([-2, -1.7976931348623157e308, -1.0, None]) == [-2, "LO", -1.0, None]
    assert N._thieu([-3, 5.0, 1.7976931348623157e308, 9.0]) == [-3, 5.0, "HI", 9.0]
    assert C.mo_ta_thieu(N._thieu([-2, -1.7976931348623157e308, -1.0, None])) == "LO THRU -1"


def test_gan_giu_chu_ky_cu_cho_cau_noi_r():
    # tools/cau_noi_r.py gọi S._gan(a, b, S.TOL_UOC) — chữ ký cũ phải còn chạy, kết quả như bản đầu
    assert C._gan(1.003, 1.0, C.TOL_UOC) is True and C._gan(1.01, 1.0, C.TOL_UOC) is False
    assert C._gan(0.0005, 0.0, C.TOL_UOC) is True  # sàn tuyệt đối 0,0006 như bản đầu
    assert C._gan(None, 1.0, C.TOL_UOC) is None and C._gan(1.0, 1.0, tran=0.0) is True
