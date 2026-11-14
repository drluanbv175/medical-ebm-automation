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
    ke, canh_bao = C.ke_hoach_bien(tieu_de, tk, td, [{"bien": "*", "ma": "BTR", "nhan": "Bỏ trống"}])
    b = {x["cot"]: x for x in ke}
    assert n == 3
    assert b["record_id"]["ten"] == "ID" and b["tuoi"]["ten"] == "Tuoi"
    assert b["tuoi"]["muc_do"] == "SCALE" and b["tuoi"]["nhan"] == "Câu 2. Tuổi (năm)"  # bỏ thẻ HTML
    assert b["hai_long"]["muc_do"] == "ORDINAL" and b["gioitinh"]["muc_do"] == "NOMINAL"
    assert b["hut_thuoc"]["so"] and b["hut_thuoc"]["doc_chuoi_roi_doi"] and b["hut_thuoc"]["ma_chu"] == {"BTR": -9991}
    assert ("-9991", "BTR — Bỏ trống") in b["hut_thuoc"]["ma_thieu"]
    assert b["trieu_chung___2"]["nhan"] == "Triệu chứng: Khó thở"
    assert b["trieu_chung___2"]["nhan_gia_tri"] == {"1": "Có", "0": "Không"}
    assert not b["nghe"]["so"] and not canh_bao


def test_cot_dinh_danh_bi_chan(tmp_path):
    p, td = _du_lieu(tmp_path)
    td["record_id"]["dinh_danh"] = "y"
    tieu_de, tk, _ = C.quet_csv(p)
    with pytest.raises(C.TuChoi, match="ĐỊNH DANH"):
        C.ke_hoach_bien(tieu_de, tk, td, [])


def test_cu_phap_nhan_bien(tmp_path):
    p, td = _du_lieu(tmp_path)
    tieu_de, tk, _ = C.quet_csv(p)
    ke, _ = C.ke_hoach_bien(tieu_de, tk, td, [{"bien": "*", "ma": "BTR", "nhan": "Bỏ trống"}])
    s = C.cu_phap_nhan_bien(p, tmp_path / "d.sav", ke, ghi_chu=["thử"])
    assert "ID A2" in s and "Tuoi F8.1" in s and "hut_thuoc A3" in s
    assert "RECODE hut_thuoc ('BTR'='-9991')." in s and "ALTER TYPE hut_thuoc (F8.0)." in s
    assert "MISSING VALUES hut_thuoc (-9991)." in s
    assert "'cong_chuc' 'Công chức'" in s  # mã chữ của biến chuỗi được trích dẫn
    assert "'X'" not in s  # mã chữ «X» không gắn được vào biến số GioiTinh ⇒ bỏ, không làm SPSS lỗi
    assert "VARIABLE LEVEL hai_long (ORDINAL)." in s and s.rstrip().endswith("/COMPRESSED.")


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
    vb, _ = C.cu_phap_phan_tich("THU", _man(), _dt(time="thoi_gian", event="bien_co"), tmp_path)
    i = vb.index("COXREG thoi_gian /STATUS=bien_co(1) /METHOD=ENTER Nhom /PRINT")
    truoc = vb[vb.rindex("OMS ", 0, i) : i]
    assert "TEMPORARY." in truoc and "SELECT IF (NOT MISSING(Tuoi) AND NOT MISSING(GioiTinh))." in truoc


def test_cu_phap_nhi_phan_va_cum(tmp_path):
    vb, cb = C.cu_phap_phan_tich("THU", _man(), _dt(outcome="kq_nhi", cot_cum="ban_kham"), tmp_path)
    assert "SET OLANG=ENGLISH TVARS=NAMES TNUMBERS=VALUES." in vb
    assert "CROSSTABS /TABLES=Nhom BY kq_nhi /STATISTICS=CHISQ RISK" in vb
    assert "LOGISTIC REGRESSION VARIABLES kq_nhi" in vb and "/METHOD=ENTER Nhom Tuoi GioiTinh" in vb
    assert "/REPEATED SUBJECT=ban_kham" in vb and any("GENLIN" in c for c in cb)


def test_cu_phap_khong_co_bien_so_khong_de_with_rong(tmp_path):
    man = _man()
    for b in man["bien"]:
        if b["cot"] in ("tuoi", "gioitinh", "nhom"):
            b["so"] = False
    vb, _ = C.cu_phap_phan_tich("THU", man, _dt(outcome="diem", outcome_type="continuous"), tmp_path)
    assert "UNIANOVA diem BY Nhom Tuoi GioiTinh\n" in vb and "WITH \n" not in vb and " WITH\n" not in vb


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


def test_lenh_chay_va_doi_chieu_gia_lap_spss(tmp_path, monkeypatch):
    monkeypatch.setattr(C, "EXPORTS", tmp_path / "exports")
    d = tmp_path / "exports" / "THU"
    (d / "spss" / "ket_qua").mkdir(parents=True)
    man = _man() | {"sav": str(d / "spss" / "THU_khoa.sav"), "sha256_sav": "x", "sha256_nguon": "abc"}
    (d / "spss" / "THU_khoa.sav.manifest.json").write_text(json.dumps(man), encoding="utf-8", newline="\n")
    (d / "spss" / "THU_phan_tich.sps").write_text("* thử\n", encoding="utf-8", newline="\n")
    (d / "spss" / "ket_qua" / "dac_ta.json").write_text(
        json.dumps(_dt(outcome="kq_nhi", outcome_type="binary")), encoding="utf-8", newline="\n"
    )
    goi = []

    def gia_lap(py, doi_so, *, thu_muc, thoi_han=0):
        goi.append(doi_so)
        _kq_tu_mau(thu_muc.parent, "binary")
        return 0, "PHIEN_BAN=31.0\nSO_CA=240\n", ""

    monkeypatch.setattr(C, "tim_spss", lambda: Path("python-cua-spss"))
    monkeypatch.setattr(C, "chay_spss", gia_lap)
    assert C.main(["chay", "--study", "THU"]) == C.MA_OK
    assert goi and goi[0][0] == "--cu-phap"
    kq = json.loads((d / "G6_spss_ket_qua.json").read_text(encoding="utf-8"))
    assert kq["spss_phien_ban"] == "31.0" and "nhom" in kq["ket_qua"]["da_bien"]["he_so"]
    tom = _tom_nhi_phan() | {"data_lock": {"sha256": "abc"}}
    (d / "G6_analysis_summary.json").write_text(json.dumps(tom), encoding="utf-8", newline="\n")
    assert C.main(["doi-chieu", "--study", "THU"]) == C.MA_OK
    assert "4 khớp" in (d / "G6_spss_doi_chieu.md").read_text(encoding="utf-8")
    tom["data_lock"]["sha256"] = "khac"  # SPSS và Python không cùng bộ dữ liệu khoá ⇒ chặn
    (d / "G6_analysis_summary.json").write_text(json.dumps(tom), encoding="utf-8", newline="\n")
    assert C.main(["doi-chieu", "--study", "THU"]) == C.MA_TU_CHOI


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
