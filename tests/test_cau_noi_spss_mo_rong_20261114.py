"""Kiểm phần MỞ RỘNG của cầu nối SPSS (14/11/2026, bác sĩ chọn mục 1–5).

(1) mô hình hỗn hợp GENLINMIXED ↔ R clmm/glmer · (2) Complex Samples có trọng số hậu phân tầng ↔ R survey (+ bản Python
của thuật toán gộp tầng ↔ hàm R 04a) · (3) RELIABILITY ↔ kiem_tin_cay_thang_do.py · (4) giả định tỷ lệ odds tại từng
ngưỡng ↔ ordinal_model · (5) run_g6_auto sinh .sps cùng script R (test ở tests/test_g6_sps_tu_dong_20261114.py).

Không cần SPSS/R: tệp mẫu ở tests/fixtures/spss_oxml/mo_rong/ là đầu ra THẬT của SPSS 31.0.1 + R 4.6.2 trên đề tài GIẢ
420 ca (đã gỡ bảng «Notes» chứa đường dẫn máy). Ca nào cần R thật thì tự bỏ qua khi máy không có Rscript.
"""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import cau_noi_spss as C  # noqa: E402
import g6_trong_so_survey as TSS  # noqa: E402

FX = Path(__file__).resolve().parent / "fixtures" / "spss_oxml" / "mo_rong"
RSCRIPT = C.tim_rscript()


def _j(ten: str) -> dict:
    return json.loads((FX / ten).read_text(encoding="utf-8"))


def _man() -> dict:
    return _j("man_bien.json") | {"sav": "THU-MR_khoa.sav", "nguon_csv": str(FX / "du_lieu_gia.csv")}


def _kq_mau(tmp: Path) -> Path:
    for f in FX.glob("oms_*.xml"):
        shutil.copy(f, tmp / f.name)
    return tmp


# ───────────── (2) bảng tầng: bản Python ↔ hàm R 04a ─────────────


def test_tang_trong_so_python_trung_ket_qua_r_da_do():
    ts, r = _j("trong_so.json"), _j("r_kq.json")["trong_so"]
    tang = C.tinh_tang_trong_so(FX / "du_lieu_gia.csv", ts, FX / "N_tang_HIS.csv", C._ma_thieu_theo_cot(_man()))
    o_py = {(x["ngay"], x["khung"]): x["nhom"] for x in tang["o"]}
    o_r = {(float(x["ngay"]), float(x["khung"])): x["nhom"] for x in C._hang_r(r["bang"])}
    assert o_py == o_r and tang["so_tang_sau_gop"] == r["so_tang"] == 16
    assert tang["kich_hoat"] is True and tang["lech_max"] == pytest.approx(r["lech_max"], rel=1e-9)
    assert tang["nhat_ky"] == r["nhat_ky"]  # cùng thứ tự gộp, cùng câu nhật ký


def _his(tmp: Path, N: dict) -> Path:
    p = tmp / "N.csv"
    with open(p, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["ngay", "khung", "N_h"])
        for (a, b), n in N.items():
            w.writerow([a, b, n])
    return p


def _du_lieu(tmp: Path, o: dict) -> Path:
    p = tmp / "d.csv"
    with open(p, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["ngay", "khung", "y"])
        for (a, b), n in o.items():
            for _ in range(n):
                w.writerow([a, b, 3])
    return p


TS_NHO = {"bien_ngay": "ngay", "bien_khung": "khung", "ket_cuc": "y", "n_toi_thieu": 10, "nguong_lech": 0.2}


def test_tang_trong_so_gop_dung_luat_va_chan_o_khong_co_luot_kham(tmp_path):
    o = {(1, 1): 30, (1, 2): 4, (1, 3): 25, (2, 1): 3, (2, 2): 28, (2, 3): 22}
    N = {k: 100 for k in o}
    t = C.tinh_tang_trong_so(_du_lieu(tmp_path, o), TS_NHO, _his(tmp_path, N), {})
    nhom = {(int(x["ngay"]), int(x["khung"])): x["nhom"] for x in t["o"]}
    assert nhom[(2, 1)] == "N2_K2"  # nhỏ nhất (3) gộp trước — khung liền kề cùng ngày có nₕ nhỏ nhất: N2_K2 (28)
    assert nhom[(1, 2)] == "N1_K3"  # 4 phiếu: hai ô kề cùng ngày N1_K1 (30) và N1_K3 (25) ⇒ chọn nₕ nhỏ hơn
    assert t["so_tang_sau_gop"] == 4 and len(t["nhat_ky"]) == 2
    with pytest.raises(C.TuChoi, match="không có lượt khám"):
        C.tinh_tang_trong_so(_du_lieu(tmp_path, o), TS_NHO, _his(tmp_path, {**N, (2, 3): 0}), {})
    with pytest.raises(C.KhongDoDuoc, match="HIS"):
        C.tinh_tang_trong_so(_du_lieu(tmp_path, o), TS_NHO, tmp_path / "khong_co.csv", {})


O_LUI = {(1, 1): 20, (1, 2): 20, (2, 1): 3, (3, 1): 15, (3, 2): 25}  # ngày 2 chỉ có MỘT ô ⇒ không có khung kề cùng ngày


def test_tang_trong_so_lui_sang_cung_khung_ngay_lien_ke(tmp_path):
    t = C.tinh_tang_trong_so(_du_lieu(tmp_path, O_LUI), TS_NHO, _his(tmp_path, dict.fromkeys(O_LUI, 100)), {})
    nhom = {(int(x["ngay"]), int(x["khung"])): x["nhom"] for x in t["o"]}
    assert nhom[(2, 1)] == "N3_K1" and "cùng khung giờ, ngày liền kề" in t["nhat_ky"][0]  # N3_K1 (15) < N1_K1 (20)


@pytest.mark.skipif(not RSCRIPT, reason="máy không có Rscript")
@pytest.mark.parametrize("hat", [1, 2, 3, 4, 5, 6])
def test_tang_trong_so_python_trung_ham_r_04a_ngau_nhien(tmp_path, hat):
    import random

    rnd = random.Random(hat)
    o = {(a, b): rnd.choice([0, 1, 3, 6, 9, 12, 25, 40]) for a in range(1, 6) for b in range(1, 5)}
    if hat % 2:  # một ngày chỉ còn MỘT khung giờ trong HIS ⇒ buộc nhánh lùi «cùng khung giờ, ngày liền kề»
        o = {k: v for k, v in o.items() if not (k[0] == 3 and k[1] != 2)} | {(3, 2): rnd.choice([1, 4, 7])}
    N = {k: rnd.randint(20, 400) for k in o}
    d, h = _du_lieu(tmp_path, o), _his(tmp_path, N)
    py = C.tinh_tang_trong_so(d, TS_NHO, h, {})
    (tmp_path / "ham.R").write_text(TSS.R_HAM, encoding="utf-8", newline="\n")
    r_code = (
        'source("ham.R", encoding="UTF-8"); d <- read.csv("d.csv"); N <- read.csv("N.csv");'
        'b <- gop_tang_nho(bang_tang(d, N, "ngay", "khung"), 10); k <- bang_kich_hoat(b$bang, 0.2);'
        'jsonlite::write_json(list(o=b$bang[,c("ngay","khung","nhom")], kich_hoat=k$kich_hoat), "r.json",'
        "auto_unbox=TRUE, digits=NA)"
    )
    subprocess.run([RSCRIPT, "--vanilla", "-e", r_code], cwd=tmp_path, check=True, capture_output=True, timeout=120)
    r = json.loads((tmp_path / "r.json").read_text(encoding="utf-8"))
    assert {(x["ngay"], x["khung"]): x["nhom"] for x in py["o"]} == {
        (float(x["ngay"]), float(x["khung"])): x["nhom"] for x in C._hang_r(r["o"])
    }
    assert py["kich_hoat"] == r["kich_hoat"]


# ───────────── cú pháp bổ sung ─────────────


def _dt(**kw) -> dict:
    d = copy.deepcopy(_j("dac_ta.json"))
    d.update(kw)
    return d


def test_cu_phap_bo_sung_du_bon_khoi_va_khong_trung_ten_bien_tam(tmp_path):
    man = _man()
    vb, cb, phu = C.cu_phap_bo_sung("THU-MR", man, _dt(), tmp_path, sav="x.sav")
    assert vb.startswith("* ") and "SET MDISPLAY=TABLES." in vb  # GENLINMIXED chỉ ra bảng qua OMS khi có lệnh này
    for tag in ("po_nguong_1", "po_nguong_4", "da_bien_hon_hop", "trong_so_ty_le", "trong_so_thu_tu", "tin_cay_1"):
        assert f"/TAG='{tag}'." in vb, tag
    assert [x["k"] for x in phu["po_nguong"]] == [1.0, 2.0, 3.0, 4.0]
    # GENLINMIXED: biến dự báo dạng số phải SCALE (NOMINAL ⇒ thành YẾU TỐ, lệch Python); cụm NOMINAL
    i = vb.index("GENLINMIXED")
    assert "/thoigian_cho_dv tuoi gioitinh (SCALE)" in vb[vb.rindex("VARIABLE LEVEL", 0, i) : i]
    assert "COMPUTE thoigian_cho_dv = thoigian_cho / 15." in vb
    # trọng số: tên biến tạm KHÔNG trùng khi bỏ phân biệt hoa/thường (bản thử đầu: ebm_Nh = ebm_nh ⇒ trọng số = 1)
    import re

    ten = re.findall(r"\b(ebm_\w+)\b", vb)
    assert len({t.upper() for t in ten}) == len(set(ten))
    assert "COMPUTE ebm_w = ebm_n_tong_the / ebm_n_mau." in vb and "ANALYSISWEIGHT=ebm_w" in vb
    assert "RELIABILITY /VARIABLES=a1 a2 a3 a4" in vb and "/ICC=MODEL(MIXED) TYPE(CONSISTENCY)" in vb
    assert any("GENLINMIXED" in c for c in cb) and any("CỐ ĐỊNH" in c for c in cb)


def test_cu_phap_bo_sung_nhi_phan_tham_chieu_ma_thap_va_rong_khi_khong_ap_dung(tmp_path):
    man = copy.deepcopy(_man())
    for b in man["bien"]:
        if b["cot"] == "gioitinh":
            b["muc"] = ["1", "2"]
    dt = _dt(outcome="gioitinh", outcome_type="binary", group="tuoi", covariates=[], thang_do={}, trong_so=None)
    vb, _, phu = C.cu_phap_bo_sung("THU-MR", man, dt, tmp_path, sav="x.sav")
    assert "REFERENCE=1 DISTRIBUTION=BINOMIAL LINK=LOGIT" in vb and "po_nguong" not in phu  # mô hình hoá P(mã cao)
    vb2, _, _ = C.cu_phap_bo_sung(
        "THU-MR", man, dt | {"cot_cum": None, "hon_hop": True}, tmp_path, sav="x.sav"
    )  # không cụm, không thang đo, không trọng số ⇒ không có tệp bổ sung
    assert vb2 == ""


def test_cu_phap_bo_sung_tu_choi_bien_trung_tien_to_va_thang_do_khong_phai_so(tmp_path):
    man = copy.deepcopy(_man())
    man["bien"].append({"cot": "ebm_w", "ten": "EBM_W", "so": True, "muc": None, "muc_do": "SCALE"})
    with pytest.raises(C.TuChoi, match="tiền tố"):
        C.cu_phap_bo_sung("THU-MR", man, _dt(), tmp_path, sav="x.sav")
    with pytest.raises(C.TuChoi, match="không phải biến số"):
        C.cu_phap_bo_sung("THU-MR", _man(), _dt(thang_do={"X": ["a1", "ma_ban_kham"]}), tmp_path, sav="x.sav")


# ───────────── đọc OXML thật ─────────────


def test_doc_ket_qua_bo_sung_tu_oxml_that(tmp_path):
    bs = C.doc_ket_qua_bo_sung(_kq_mau(tmp_path), _dt(), _man())
    assert bs["po_tparallel"]["df"] == 9 and 0 < bs["po_tparallel"]["p"] < 1
    assert set(bs["po_nguong"]) == {"1", "2", "3", "4"} and "thoigian_cho" in bs["po_nguong"]["1"]
    hh = bs["hon_hop"]["he_so"]
    assert set(hh) == {"thoigian_cho", "tuoi", "gioitinh"}  # ngưỡng và hệ số dư bị loại, tên đổi về cột G6
    assert hh["thoigian_cho"]["uoc_luong"] == pytest.approx(0.8616, abs=1e-4) and bs["hon_hop"]["phuong_sai_ngau_nhien"]
    tl = bs["trong_so"]["ty_le"]
    assert tl["p"] == pytest.approx(0.5463, abs=1e-4) and tl["deff"] == pytest.approx(7.378, abs=1e-3)
    assert bs["trong_so"]["thu_tu"]["thoigian_cho"]["uoc_luong"] == pytest.approx(0.8433, abs=1e-4)
    tc = bs["tin_cay"]["Linh vuc A"]
    assert tc["alpha"] == pytest.approx(0.8995, abs=1e-4) and len(tc["muc"]) == 4 and tc["n"] > 300


# ───────────── đối chiếu ─────────────


def _bo() -> tuple[dict, dict, dict, dict]:
    tom = _j("tom_ordinal.json")
    dt = _dt()
    return tom, {"bo_sung": C.doc_ket_qua_bo_sung(_kq_mau_tam(), dt, _man())}, dt, _j("r_kq.json")


def _kq_mau_tam() -> Path:
    import tempfile

    t = Path(tempfile.mkdtemp(prefix="ebm-fx-"))
    return _kq_mau(t)


def test_doi_chieu_bo_sung_so_lieu_that():
    tom, kq, dt, r = _bo()
    tc_py = C.tin_cay_python(_man(), {"Linh vuc A": ["a1", "a2", "a3", "a4"]})
    dong, tt = C.doi_chieu_bo_sung(tom, kq, dt, r=r, tin_cay_py=tc_py)
    tt_ = {}
    for x in dong:
        tt_.setdefault(x["trang_thai"], []).append(x["muc"])
    assert not tt_.get("lech") and not tt_.get("khong_so_duoc"), tt_
    assert len([m for m in tt_["khop"] if m.startswith("Giả định tỷ lệ odds — OR tại")]) == 12
    assert any("R trọng số cố định" in m for m in tt_["khop"]) and any(
        "svyolr trọng số cố định" in m for m in tt_["khop"]
    )
    assert any("postStratify" in m for m in tt_["lech_nho"]) and any("Mô hình hỗn hợp" in m for m in tt_["lech_nho"])
    assert any(m.startswith("Tin cậy — Linh vuc A — Cronbach") for m in tt_["khop"])
    assert any("Phương sai intercept" in x for x in tt) and any("cùng định nghĩa SPSS" in x for x in tt)


def test_doi_chieu_bo_sung_khong_r_va_bang_tang_lech():
    tom, kq, dt, r = _bo()
    dong, _ = C.doi_chieu_bo_sung(tom, kq, dt, r={"loi": "máy không có Rscript"}, tin_cay_py={})
    assert any(x["muc"].startswith("Mô hình hỗn hợp") and x["trang_thai"] == "khong_so_duoc" for x in dong)
    assert any(x["muc"].startswith("Trọng số hậu phân tầng") and x["trang_thai"] == "khong_so_duoc" for x in dong)
    assert any(x["muc"].startswith("Tin cậy") and x["trang_thai"] == "khong_so_duoc" for x in dong)
    r2 = copy.deepcopy(r)
    bang = C._hang_r(r2["trong_so"]["bang"])
    bang[0]["nhom"] = "N9_K9"  # hai bản thuật toán gộp tầng cho kết quả khác ⇒ LỆCH, không lặng lẽ khớp
    r2["trong_so"]["bang"] = bang
    dong, _ = C.doi_chieu_bo_sung(tom, kq, dt, r=r2, tin_cay_py={})
    assert next(x for x in dong if x["muc"].startswith("Trọng số — bảng tầng"))["trang_thai"] == "lech"


def test_doi_chieu_bo_sung_bat_lech_trong_so_va_so_ca_tin_cay():
    tom, kq, dt, r = _bo()
    kq2 = copy.deepcopy(kq)
    kq2["bo_sung"]["trong_so"]["thu_tu"]["thoigian_cho"]["uoc_luong"] = 0.8701  # = OR KHÔNG trọng số (lỗi ebm_Nh)
    kq2["bo_sung"]["trong_so"]["thu_tu"]["thoigian_cho"]["b"] = -0.139
    tc_py = C.tin_cay_python(_man(), {"Linh vuc A": ["a1", "a2", "a3", "a4"]})
    tc_py["Linh vuc A"]["n"] -= 7
    dong, _ = C.doi_chieu_bo_sung(tom, kq2, dt, r=r, tin_cay_py=tc_py)
    assert next(x for x in dong if "thoigian_cho — R svyolr trọng số cố định" in x["muc"])["trang_thai"] == "lech"
    assert next(x for x in dong if "Cronbach" in x["muc"])["trang_thai"] == "lech"


def test_tin_cay_python_doi_ma_thieu_nhu_spss():
    tc = C.tin_cay_python(_man(), {"A": ["a1", "a2", "a3", "a4"]})["A"]
    assert tc["ma_thieu_so"] == [8.0, 9.0] and tc["alpha"] == pytest.approx(0.8995, abs=1e-4)
    sp = C.doc_ket_qua_bo_sung(_kq_mau_tam(), _dt(), _man())["tin_cay"]["Linh vuc A"]
    assert tc["n"] == int(sp["n"])  # cùng số ca dùng: mã 8/9 (glob a?) ⇒ thiếu ở cả hai bên


# ───────────── luồng lệnh (SPSS + R giả lập) ─────────────


def _de_tai(tmp_path: Path, monkeypatch) -> Path:
    monkeypatch.setattr(C, "EXPORTS", tmp_path / "exports")
    d = tmp_path / "exports" / "THU-MR"
    (d / "spss").mkdir(parents=True)
    (d / "his_tong_hop").mkdir()
    shutil.copy(FX / "N_tang_HIS.csv", d / "his_tong_hop" / "N_tang_HIS.csv")
    nguon = d / "khoa.csv"
    shutil.copy(FX / "du_lieu_gia.csv", nguon)
    sav = d / "spss" / "THU-MR_khoa.sav"
    sav.write_bytes(b"$FL2 gia")
    man = _j("man_bien.json") | {
        "sav": str(sav),
        "sav_da_tao": True,
        "sha256_sav": hashlib.sha256(sav.read_bytes()).hexdigest(),
        "sha256_nguon": hashlib.sha256(nguon.read_bytes()).hexdigest(),
        "nguon_csv": str(nguon),
    }
    (d / "spss" / "THU-MR_khoa.sav.manifest.json").write_text(json.dumps(man), encoding="utf-8", newline="\n")
    tom = _j("tom_ordinal.json") | {"data_lock": {"sha256": man["sha256_nguon"]}}
    (d / "G6_analysis_summary.json").write_text(json.dumps(tom), encoding="utf-8", newline="\n")
    ts = _j("trong_so.json") | {"can_trong_so": True, "thieu": []}
    (d / "G6_checkpoint.json").write_text(json.dumps({"trong_so": ts}), encoding="utf-8", newline="\n")
    return d


def test_luong_cu_phap_chay_doi_chieu_gia_lap(tmp_path, monkeypatch):
    d = _de_tai(tmp_path, monkeypatch)
    assert C.main(["cu-phap", "--study", "THU-MR", "--thang-do", "Linh vuc A:a1,a2,a3,a4"]) == C.MA_OK
    assert (d / "spss" / "THU-MR_phan_tich_bo_sung.sps").exists()
    dt = json.loads((d / "spss" / "ket_qua" / "dac_ta.json").read_text(encoding="utf-8"))
    assert dt["hon_hop_da_sinh"] and dt["trong_so_tang"]["so_tang_sau_gop"] == 16 and dt["tin_cay"]
    goi = []

    def spss_gia(py, doi_so, *, thu_muc, thoi_han=0):
        ten = Path(doi_so[1]).name
        goi.append(ten)
        for f in FX.glob("oms_*.xml"):
            if (ten == "phan_tich.sps") == (f.name == "oms_da_bien.xml"):
                shutil.copy(f, thu_muc / "kq" / f.name)
        return 0, "PHIEN_BAN=31.0\nSO_CA=420\n", ""

    monkeypatch.setattr(C, "tim_spss", lambda: Path("python-cua-spss"))
    monkeypatch.setattr(C, "chay_spss", spss_gia)
    monkeypatch.setattr(C, "chay_r_tham_chieu", lambda *a, **k: _j("r_kq.json"))
    assert C.main(["chay", "--study", "THU-MR"]) == C.MA_OK
    assert goi == ["phan_tich.sps", "phan_tich_bo_sung.sps"]  # bổ sung là lượt SPSS RIÊNG, sau phân tích chính
    assert C.main(["doi-chieu", "--study", "THU-MR"]) == C.MA_OK
    md = (d / "G6_spss_doi_chieu.md").read_text(encoding="utf-8")
    assert "Thông tin thêm" in md and "Tham chiếu R" in md and "0 lệch" in md


def test_chay_chan_khi_his_doi_hoac_sps_bo_sung_sua_tay(tmp_path, monkeypatch):
    d = _de_tai(tmp_path, monkeypatch)
    assert C.main(["cu-phap", "--study", "THU-MR"]) == C.MA_OK
    monkeypatch.setattr(C, "tim_spss", lambda: Path("python-cua-spss"))
    monkeypatch.setattr(C, "chay_spss", lambda *a, **k: (0, "", ""))
    his = d / "his_tong_hop" / "N_tang_HIS.csv"
    goc = his.read_bytes()
    his.write_bytes(goc + b"7,1,50\n")
    assert C.main(["chay", "--study", "THU-MR"]) == C.MA_TU_CHOI  # Nₕ đổi sau khi sinh cú pháp
    his.write_bytes(goc)
    monkeypatch.setattr(C, "chay_r_tham_chieu", lambda *a, **k: {})
    assert C.main(["chay", "--study", "THU-MR"]) == C.MA_OK  # khôi phục đúng ⇒ chạy được (chốt không bắt nhầm)
    bs = d / "spss" / "THU-MR_phan_tich_bo_sung.sps"
    bs.write_text(bs.read_text(encoding="utf-8") + "* sửa tay.\n", encoding="utf-8", newline="\n")
    assert C.main(["chay", "--study", "THU-MR"]) == C.MA_TU_CHOI


def test_chay_bo_sung_loi_van_giu_phan_chinh(tmp_path, monkeypatch):
    d = _de_tai(tmp_path, monkeypatch)
    assert C.main(["cu-phap", "--study", "THU-MR"]) == C.MA_OK

    def spss_gia(py, doi_so, *, thu_muc, thoi_han=0):
        if Path(doi_so[1]).name == "phan_tich_bo_sung.sps":
            return 1, "", "LOI_SPSS GENLINMIXED không hội tụ"
        shutil.copy(FX / "oms_da_bien.xml", thu_muc / "kq" / "oms_da_bien.xml")
        return 0, "PHIEN_BAN=31.0\n", ""

    monkeypatch.setattr(C, "tim_spss", lambda: Path("python-cua-spss"))
    monkeypatch.setattr(C, "chay_spss", spss_gia)
    monkeypatch.setattr(C, "chay_r_tham_chieu", lambda *a, **k: {})
    assert C.main(["chay", "--study", "THU-MR"]) == C.MA_OK
    kq = json.loads((d / "G6_spss_ket_qua.json").read_text(encoding="utf-8"))
    assert "GENLINMIXED" in kq["bo_sung_loi"] and kq["ket_qua"].get("da_bien")
    assert C.main(["doi-chieu", "--study", "THU-MR"]) in (C.MA_OK, C.MA_KHONG_DO, C.MA_LECH)
    assert "SPSS lỗi ở tệp bổ sung" in (d / "G6_spss_doi_chieu.md").read_text(encoding="utf-8")


def test_dac_ta_thang_do_va_trong_so_tu_checkpoint(tmp_path, monkeypatch):
    _de_tai(tmp_path, monkeypatch)
    ns = argparse.Namespace(study="THU-MR", gate="G6", covariates=None, thang_do=["A:a1, a2", "B:a3,a4"])
    dt = C.dac_ta(ns)
    assert dt["thang_do"] == {"A": ["a1", "a2"], "B": ["a3", "a4"]} and dt["hon_hop"] is True
    assert dt["trong_so"]["bien_ngay"] == "ngay_trong_tuan" and "thieu" not in dt["trong_so"]
    ns.khong_trong_so, ns.khong_hon_hop = True, True
    dt = C.dac_ta(ns)
    assert dt["trong_so"] is None and dt["hon_hop"] is False
    ns.thang_do = ["khong_co_hai_cham"]
    with pytest.raises(C.TuChoi):
        C.dac_ta(ns)


def test_chay_r_tham_chieu_khong_co_r_bao_ro(tmp_path, monkeypatch):
    monkeypatch.setattr(C, "tim_rscript", lambda: None)
    kq = C.chay_r_tham_chieu(_man(), _dt(), tmp_path / "x.sav", tmp_path, his=FX / "N_tang_HIS.csv")
    assert "Rscript" in kq["loi"]
    assert C.chay_r_tham_chieu(_man(), _dt(hon_hop_da_sinh=False, trong_so=None), tmp_path, tmp_path, his=None) == {}
