"""Kịch bản CHÂN THỰC cho mọi thiết kế (17/11/2026 — bác sĩ: «Giả lập chân thực trên tất cả các đề tài nghiên cứu
để hệ thống hoàn chỉnh có thể thực hiện được tất cả các nghiên cứu y khoa»).

Kiểm (nhanh, ngoại tuyến, không chạy trọn vòng — trọn vòng ở test_gia_lap_tron_vong::test_gia_lap_chan_thuc):
- 8 kịch bản hợp lệ: tên trường duy nhất, siêu dữ liệu đủ, nhánh chỉ tham chiếu trường đứng TRƯỚC, ma trận đúng
  kiểu/vai, hình mẫu chỉ nói về trường có thật, bộ sinh chạy được trên từ điển của chính kịch bản mà KHÔNG vi phạm
  nhánh hay để trống câu bắt buộc đang hiện;
- bộ sinh: mô hình tuyến tính/logistic/công thức/ngày nối tiếp/sống còn/nhị thức/hiệu ứng cụm/ô loại trừ/mã thiếu;
- bộ giả lập: từ điển nhiều biểu mẫu, phiếu chia phần không mang cú pháp REDCap, nền G0 kế thừa, lọc quần thể G6;
- cổng PII: trường PHÂN LOẠI có mã không bị chặn theo tên cột (giá trị ô vẫn quét).
Dữ liệu GIẢ. Cần bác sĩ kiểm chứng.
"""
from __future__ import annotations

import csv
import random
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import gia_lap_chan_thuc as GCT  # noqa: E402
import gia_lap_dinh_ky as GL  # noqa: E402
import import_real_dataset as RDI  # noqa: E402
import ma_tran_muc_tieu_bien as MT  # noqa: E402
import nhap_lieu_excel as N  # noqa: E402
import sinh_du_lieu_redcap as SR  # noqa: E402

KB = GCT.kich_ban_chan_thuc()


def _tu_dien(kb) -> list:
    bs = kb["bien_so"]
    return [{SR.COT_TEN: t, SR.COT_KIEU: loai, SR.COT_LUA: lc, SR.COT_KIEM: kt, SR.COT_MIN: lo, SR.COT_MAX: hi,
             SR.COT_NHANH: bs["meta_bien"][t]["nhanh"]} for t, loai, _nh, lc, kt, lo, hi in bs["bo_bien"]]


def _hinh_mau(kb):
    hm = kb["du_lieu_redcap"]["hinh_mau"]
    return getattr(GCT, hm) if isinstance(hm, str) else hm


# ───────────────────────────── 8 kịch bản hợp lệ ─────────────────────────────


def test_du_tam_thiet_ke_va_ke_thua_dung_goc():
    thiet_ke = {kb["thiet_ke"] for kb in KB.values()}
    assert thiet_ke == {"rct", "cross_sectional", "cohort", "case_control", "diagnostic", "prediction", "sr_ma",
                        "qualitative"}
    for kb in KB.values():
        assert kb["goc"] in GL.KICH_BAN and kb["nen_g0_tu"] == kb["goc"]
        assert kb["study"] == GL.KICH_BAN[kb["goc"]]["study"]


@pytest.mark.parametrize("ma", sorted(KB))
def test_kich_ban_hop_le(ma):
    kb = KB[ma]
    bs = kb["bien_so"]
    ten = [t[0] for t in bs["bo_bien"]]
    assert len(ten) == len(set(ten)) and set(bs["meta_bien"]) == set(ten)
    truoc: set = set()
    for t in ten:
        m = bs["meta_bien"][t]
        for ref in re.findall(r"\[([A-Za-z0-9_]+)", m["nhanh"]):
            assert ref in truoc, f"{ma}.{t}: nhánh tham chiếu «{ref}» chưa đứng trước"
        truoc.add(t)
    ma_cau = [m["ma_cau"] for m in bs["meta_bien"].values()]
    assert len(ma_cau) == len(set(ma_cau)), "mã câu trùng"
    for d in bs["ma_tran"]:
        assert d[3] in ten, f"ma trận nhắc biến vắng: {d[3]}"
        assert d[2] in MT.VAI_TRO and d[4] in MT.KIEU, d
        assert d[5] == bs["meta_bien"][d[3]]["ma_cau"], f"mã câu ma trận lệch phiếu: {d}"
    assert set(_hinh_mau(kb)) - {"_cap_ngay"} <= set(ten), "hình mẫu nói về trường không có"
    assert "du_tieu_chuan" in ten and bs["meta_bien"]["du_tieu_chuan"]["bat_buoc"] is False
    # trường số phải khai đủ khoảng: bộ sinh ép trường không khai vào 0–100 (lặng lẽ làm lệch mô hình)
    for t, _l, _n, _c, kt, lo, hi in bs["bo_bien"]:
        if kt in ("integer", "number") or kt.startswith("date"):
            assert lo != "" and hi != "", f"{ma}.{t}: thiếu min/max"


@pytest.mark.parametrize("ma", sorted(KB))
def test_bo_sinh_tren_tu_dien_chinh_kich_ban_khong_vi_pham_nhanh(ma):
    kb = KB[ma]
    bs = kb["bien_so"]
    can = int(kb["du_lieu_redcap"]["dung_khi"][1]) if kb["du_lieu_redcap"]["dung_khi"][1] != "N_G3" else 60
    hang = SR.sinh(_tu_dien(kb), 20 * can, _hinh_mau(kb), dung_khi=[kb["du_lieu_redcap"]["dung_khi"][0], can])
    ds_calc = [(t, lc) for t, loai, _n, lc, *_ in bs["bo_bien"] if loai == "calc"]
    du = 0
    for r in hang:
        d = {k: SR._chuoi(v) for k, v in r.items()}
        d2, loi = N.dong_kem_calc(d, N.calc_can_cho_logic(ds_calc, [m["nhanh"] for m in bs["meta_bien"].values()]))
        assert not loi
        du += d2["du_tieu_chuan"] == "1"
        for t, loai, *_ in bs["bo_bien"]:
            if loai == "calc":
                assert r[t] is None  # không nhập tay ⇒ không ghi ra
                continue
            m = bs["meta_bien"][t]
            hien = N.danh_gia_logic(m["nhanh"], d2) if m["nhanh"] else True
            if loai == "checkbox":
                con = [v for k, v in r.items() if k.startswith(f"{t}___")]
                assert (any(con) if hien and m["bat_buoc"] else True) and (hien or all(v is None for v in con))
                continue
            assert (d.get(t) not in ("", None)) == bool(hien and (m["bat_buoc"] or d.get(t))), (ma, t, d.get(t))
    assert du == can


# ───────────────────────────── bộ sinh: mô hình ─────────────────────────────

TD = [
    {SR.COT_TEN: "id", SR.COT_KIEU: "text", SR.COT_LUA: "", SR.COT_KIEM: "", SR.COT_MIN: "", SR.COT_MAX: "",
     SR.COT_NHANH: ""},
    {SR.COT_TEN: "nhom", SR.COT_KIEU: "radio", SR.COT_LUA: "1, A | 0, B", SR.COT_KIEM: "", SR.COT_MIN: "",
     SR.COT_MAX: "", SR.COT_NHANH: ""},
    {SR.COT_TEN: "ngay0", SR.COT_KIEU: "text", SR.COT_LUA: "", SR.COT_KIEM: "date_dmy", SR.COT_MIN: "2027-01-01",
     SR.COT_MAX: "2027-01-31", SR.COT_NHANH: ""},
    {SR.COT_TEN: "x", SR.COT_KIEU: "text", SR.COT_LUA: "", SR.COT_KIEM: "integer", SR.COT_MIN: "0", SR.COT_MAX: "300",
     SR.COT_NHANH: ""},
    {SR.COT_TEN: "y", SR.COT_KIEU: "yesno", SR.COT_LUA: "", SR.COT_KIEM: "", SR.COT_MIN: "", SR.COT_MAX: "",
     SR.COT_NHANH: ""},
    {SR.COT_TEN: "tb", SR.COT_KIEU: "text", SR.COT_LUA: "", SR.COT_KIEM: "integer", SR.COT_MIN: "0",
     SR.COT_MAX: "300", SR.COT_NHANH: ""},
    {SR.COT_TEN: "thang", SR.COT_KIEU: "text", SR.COT_LUA: "", SR.COT_KIEM: "integer", SR.COT_MIN: "1",
     SR.COT_MAX: "36", SR.COT_NHANH: ""},
    {SR.COT_TEN: "tt", SR.COT_KIEU: "radio", SR.COT_LUA: "1, SK | 2, TV | 3, MD | 4, Het", SR.COT_KIEM: "",
     SR.COT_MIN: "", SR.COT_MAX: "", SR.COT_NHANH: ""},
    {SR.COT_TEN: "ngay1", SR.COT_KIEU: "text", SR.COT_LUA: "", SR.COT_KIEM: "date_dmy", SR.COT_MIN: "",
     SR.COT_MAX: "", SR.COT_NHANH: ""},
    {SR.COT_TEN: "thuoc", SR.COT_KIEU: "checkbox", SR.COT_LUA: "1, A | 2, B | 0, Không dùng", SR.COT_KIEM: "",
     SR.COT_MIN: "", SR.COT_MAX: "", SR.COT_NHANH: ""},
]
HM = {
    "id": {"co_dinh": "R{i:04d}"}, "nhom": {"phan_bo": {"1": 0.5, "0": 0.5}}, "ngay0": {"tu": "2027-01-01",
                                                                                      "den": "2027-01-31"},
    "x": {"tuyen_tinh": {"chan": 100, "he_so": [["[nhom] = '1'", -20]], "sd": 0.001}},
    "y": {"logit": {"chan": -20, "he_so": [["[nhom] = '1'", 40]]}},
    "tb": {"cong_thuc": "([x] + 1) / 2", "lam_tron": 0},
    "thang": {"song_con": {"chan": -2.0, "he_so": [["[nhom] = '1'", 1.0]], "toi_da": 36, "tu_vong_moi_thang": 0.0,
                           "mat_dau_moi_thang": 0.0, "bien_trang_thai": "tt",
                           "ma": {"su_kien": 1, "tu_vong": 2, "mat_dau": 3, "het": 4}}},
    "ngay1": {"ngay_cong_thang": ["ngay0", "thang"]},
    "thuoc": {"p": {"1": 0.5, "2": 0.5}, "doc_quyen": "0"},
}  # fmt: skip


def test_bo_sinh_mo_hinh_tuyen_tinh_logistic_cong_thuc_ngay_song_con_doc_quyen():
    hang = SR.sinh(TD, 400, HM, seed=3)
    for r in hang:
        assert r["x"] == (80 if r["nhom"] == 1 else 100)  # tuyến tính, sai số ~0
        assert r["y"] == (1 if r["nhom"] == 1 else 0)  # logit ±20 ⇒ tất định
        assert r["tb"] == round((r["x"] + 1) / 2)  # công thức + làm tròn
        assert r["tt"] in (1, 4) and (r["tt"] == 4) == (r["thang"] == 36)  # sống còn ghi trạng thái
        assert r["ngay1"] > r["ngay0"]
        assert (r["thuoc___0"] == 1) == (r["thuoc___1"] == 0 and r["thuoc___2"] == 0)  # ô loại trừ
    sk = {g: [r["thang"] for r in hang if r["nhom"] == g and r["tt"] == 1] for g in (0, 1)}
    assert sum(sk[1]) / len(sk[1]) < sum(sk[0]) / len(sk[0])  # nguy cơ cao hơn ⇒ biến cố sớm hơn


def test_bo_sinh_nhi_thuc_va_hieu_ung_cum_cung_ten_dung_chung():
    # khoảng phải khai: trường số không khai min/max bị bộ sinh ép vào 0–100
    td = [TD[0], *({SR.COT_TEN: t, SR.COT_KIEU: "text", SR.COT_LUA: "", SR.COT_KIEM: "integer", SR.COT_MIN: "0",
                    SR.COT_MAX: "100000", SR.COT_NHANH: ""} for t in ("n", "a", "b"))]
    nen = {"ten": "nen", "bien": "id", "sd": 3.0}
    hm = {"id": {"co_dinh": "S{i}"}, "n": {"deu": (1000, 1000)},
          "a": {"nhi_thuc": {"n": "n", "log_p": {"chan": -3.0, "hieu_ung_cum": [nen]}}},
          "b": {"nhi_thuc": {"n": "n", "log_p": {"chan": -3.0, "hieu_ung_cum": [nen]}}}}  # fmt: skip
    hang = SR.sinh(td, 30, hm, seed=5)
    assert all(0 <= r["a"] <= 1000 for r in hang)
    # SD 3 trên thang log ⇒ số biến cố dao động RẤT rộng giữa các nghiên cứu (không hiệu ứng: ~50 ± 7)
    assert max(r["a"] for r in hang) - min(r["a"] for r in hang) > 200
    # cùng hiệu ứng «nen» theo từng nghiên cứu ⇒ a và b tương quan mạnh giữa các nghiên cứu (SD 3 trên thang log)
    xa, xb = [r["a"] for r in hang], [r["b"] for r in hang]
    ma, mb = sum(xa) / 30, sum(xb) / 30
    cov = sum((p - ma) * (q - mb) for p, q in zip(xa, xb))
    assert cov > 0


def test_bo_sinh_ma_thieu_co_ghi_nhan():
    hm = dict(HM, x={"chuan": (100, 5), "ma_thieu": {"p": 1.0, "ma": "KDD", "khi": "[nhom] = '1'"}})
    hm = {k: v for k, v in hm.items() if k not in ("tb",)}
    td = [r for r in TD if r[SR.COT_TEN] != "tb"]
    for r in SR.sinh(td, 50, hm, seed=9):
        assert (r["x"] == "KDD") == (r["nhom"] == 1)


def test_bo_sinh_ngay_sau_thieu_goc_thi_dung_ro():
    hm = dict(HM, ngay0={"ngay_sau": ["vang", 0, 3]})
    with pytest.raises(SR.KhongSinhDuoc, match="vang"):
        SR.sinh(TD, 3, hm)


# ───────────────────────────── bộ giả lập ─────────────────────────────


def test_tu_dien_nhieu_bieu_mau_co_nhanh_bat_buoc_va_tieu_de_phan(tmp_path):
    gl = object.__new__(GL.GiaLap)
    gl.kb, gl.out = KB["rct_chan_thuc"], tmp_path
    gl._dung_bo_bien_ma_tran()
    with (tmp_path / "_bo-bien-rieng.csv").open(encoding="utf-8") as fh:
        r = {d["Variable / Field Name"]: d for d in csv.DictReader(fh)}
    assert r["record_id"]["Form Name"] == "sang_loc" and r["record_id"]["Section Header"].startswith("A.")
    assert r["ha_tt_t6"]["Branching Logic (Show field only if...)"] == "[theo_doi_t6] = '1'"
    assert r["du_tieu_chuan"]["Field Type"] == "calc" and r["du_tieu_chuan"]["Required Field?"] == "n"
    assert r["tuoi"]["Required Field?"] == "y" and r["tuoi"]["Form Name"] == "nen"
    assert len({d["Form Name"] for d in r.values()}) == 5


def test_nen_g0_ke_thua_kich_ban_goc(tmp_path):
    gl = object.__new__(GL.GiaLap)
    gl.kb, gl.ma, gl.nen_g0_dir = KB["rct_chan_thuc"], "rct_chan_thuc", tmp_path
    assert gl._nen_g0() == tmp_path / "rct_nhi_phan"
    (tmp_path / "rct_chan_thuc").mkdir()
    assert gl._nen_g0() == tmp_path / "rct_chan_thuc"  # có nền riêng ⇒ dùng nền riêng


def test_kich_ban_ke_thua_khong_ghi_nen_g0_rieng(tmp_path):
    """Kịch bản kế thừa không được ghi nền G0 (ghi vào nền gốc sẽ xoá nền của kịch bản gốc; ghi riêng thì trùng lặp)."""
    gl = object.__new__(GL.GiaLap)
    gl.kb, gl.ma, gl.nen_g0_dir = KB["rct_chan_thuc"], "rct_chan_thuc", tmp_path
    goc = tmp_path / "rct_nhi_phan"
    goc.mkdir()
    (goc / "_nen.json").write_text("{}", encoding="utf-8", newline="\n")
    gl._cp = lambda _g: {"n_pmids": 5}
    gl._g0_bi_chan_vi_nguon = lambda: False
    gl.luu_nen_g0()
    assert (goc / "_nen.json").read_text(encoding="utf-8") == "{}"
    assert not (tmp_path / "rct_chan_thuc").exists()


def test_bo_chay_tron_vong_khong_chep_nen_g0_cho_kich_ban_ke_thua(tmp_path):
    """`_nen_g0_tu_goc` chép nền gốc sang thư mục riêng cho biến thể cùng đề tài — kịch bản kế thừa thì không."""
    import gia_lap_tron_vong as TV  # noqa: PLC0415

    goc = tmp_path / "rct_nhi_phan"
    goc.mkdir()
    (goc / "_nen.json").write_text("{}", encoding="utf-8", newline="\n")
    tv = object.__new__(TV.TronVong)
    tv.kb, tv.ma, tv.nen_g0_dir = KB["rct_chan_thuc"], "rct_chan_thuc", tmp_path
    tv._nen_g0_tu_goc()
    assert not (tmp_path / "rct_chan_thuc").exists()


def test_moi_phan_tich_g6_loc_quan_the():
    for ma, kb in KB.items():
        for pt in kb["ho_so_tron_vong"]["g6"]:
            ts = pt.get("tham_so")
            if isinstance(ts, dict) and (pt.get("vai") == "chinh" or not pt.get("ke_thua") or "loc" in ts):
                assert "du_tieu_chuan == 1" in ts["loc"], (ma, pt["id"], ts.get("loc"))
    nam = next(p for p in KB["rct_chan_thuc"]["ho_so_tron_vong"]["g6"] if p["id"] == "NC_nam")
    assert nam["tham_so"]["loc"] == "du_tieu_chuan == 1 and gioi == 1"  # nhóm nhỏ không ghi đè quần thể


def test_phieu_thu_thap_chia_phan_khong_mang_cu_phap_redcap(tmp_path):
    import gia_lap_tron_vong as TV

    tv = object.__new__(TV.TronVong)
    tv.out, tv.study, tv.o, tv.kb = tmp_path, "X", [], KB["cohort_chan_thuc"]
    (tmp_path / "study_meta.json").write_text("{}", encoding="utf-8", newline="\n")
    tv._soan_phieu_thu_thap()
    van = (tmp_path / "PHIEU_THU_THAP_SO_LIEU_X.md").read_text(encoding="utf-8")
    assert "## PHẦN A. Sàng lọc hồ sơ" in van and "## PHẦN D. Theo dõi" in van
    assert "[" not in re.sub(r"\(`[^`]*`\)", "", van.split("\n", 3)[3]), "cú pháp REDCap lọt vào phiếu"
    assert "chỉ hỏi khi câu A2 = 1" in van and "máy tự tính" in van


# ───────────────────────────── cổng PII: tên cột của trường phân loại ─────────────────────────────


def test_cot_phan_loai_khong_bi_chan_theo_ten_nhung_gia_tri_van_quet(tmp_path):
    du_lieu = tmp_path / "dl.csv"
    du_lieu.write_text("record_id,tc_dien_thoai\nR1,1\nR2,0\n", encoding="utf-8", newline="\n")
    loi = RDI._scan_csv(du_lieu)["issues"]
    assert [x["type"] for x in loi] == ["header_pii:tc_dien_thoai"]  # không khai từ điển ⇒ chặn như cũ
    assert RDI._scan_csv(du_lieu, exempt_header_columns=frozenset({"tc_dien_thoai"}))["issues"] == []
    du_lieu.write_text("record_id,tc_dien_thoai\nR1,0903123456\n", encoding="utf-8", newline="\n")
    loi = RDI._scan_csv(du_lieu, exempt_header_columns=frozenset({"tc_dien_thoai"}))["issues"]
    assert any("phone" in x["type"] for x in loi), loi  # số điện thoại thật trong ô vẫn bị chặn


def test_cot_phan_loai_tu_dien_va_cong_g5(tmp_path):
    import g5_quality_gate as G5Q

    td = tmp_path / "td.csv"
    with td.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["Variable / Field Name", "Form Name", "Field Type", "Field Label",
                    "Choices, Calculations, OR Slider Labels", "Required Field?", "Identifier?"])
        w.writerow(["record_id", "a", "text", "Mã", "", "y", ""])
        w.writerow(["tc_dien_thoai", "a", "yesno", "Có điện thoại nhận tin nhắn", "", "y", ""])
        w.writerow(["so_dien_thoai", "a", "text", "Số điện thoại", "", "n", ""])
    assert "tc_dien_thoai" in RDI.cot_phan_loai_tu_dien(td) and "so_dien_thoai" not in RDI.cot_phan_loai_tu_dien(td)
    loi = G5Q._read_redcap_dictionary(td)["issues"]
    assert any("so_dien_thoai" in x and "tc_dien_thoai" not in x for x in loi if x.startswith("direct_identifier")), loi


def test_hat_giong_tat_dinh():
    kb = KB["prediction_chan_thuc"]
    a = SR.sinh(_tu_dien(kb), 200, _hinh_mau(kb), seed=11, dung_khi=["[du_tieu_chuan] = '1'", 50])
    b = SR.sinh(_tu_dien(kb), 200, _hinh_mau(kb), seed=11, dung_khi=["[du_tieu_chuan] = '1'", 50])
    assert a == b and random.Random(1).random() == random.Random(1).random()


# ───────────────────────────── kiểm độ chính xác (khôi phục tham số) ─────────────────────────────


def test_phan_xet_chinh_xac_ba_muc_va_thang_log():
    assert GCT.phan_xet_chinh_xac(0.26, 0.18, (0.04, 0.32), False)["ket"] == "DAT"
    assert GCT.phan_xet_chinh_xac(0.36, 0.18, (0.04, 0.32), False)["ket"] == "CANH_BAO"  # z ≈ 2,5
    assert GCT.phan_xet_chinh_xac(0.60, 0.18, (0.04, 0.32), False)["ket"] == "SAI"  # z ≈ 5,9
    # thang log: OR thật 1,84, KTC 1,2–2,8 ⇒ đạt; thật 6,0 ⇒ sai
    assert GCT.phan_xet_chinh_xac(1.84, 1.83, (1.2, 2.8), True)["ket"] == "DAT"
    assert GCT.phan_xet_chinh_xac(6.0, 1.83, (1.2, 2.8), True)["ket"] == "SAI"


def test_auc_mann_whitney():
    assert GCT._auc([1, 2, 3, 4], [0, 0, 1, 1]) == 1.0
    assert GCT._auc([1, 2, 3, 4], [1, 1, 0, 0]) == 0.0
    assert GCT._auc([1, 1, 1, 1], [0, 1, 0, 1]) == 0.5  # hoà tính ½


def test_tham_so_that_khop_mo_hinh_sinh():
    assert GCT.tham_so_that("sr_ma_chan_thuc") == 0.70
    # bệnh–chứng: OR thô = e^0,61 ≈ 1,84 vì NSAID độc lập với hiệp biến khi biết nhóm (quần thể lớn ⇒ sai số nhỏ)
    assert abs(GCT.tham_so_that("case_control_chan_thuc", n=20000) - 1.84) < 0.2


def test_cong_phan_ci_bat_sai_va_chua_do(tmp_path):
    import json

    import kiem_gia_lap_16 as KG

    tot = {"cong": {"G10": {"trang_thai": "PASS_G10_RELEASE_PACKAGE_LOCKED"}}, "so_o_loi_may": 0,
           "du_lieu": {"de_cuong_nop": {"ma": 0}}}  # fmt: skip
    for cx, mong in (({"ket": "DAT"}, []), ({"ket": "KHONG_AP_DUNG"}, []), ({"ket": "CANH_BAO"}, []),
                     ({"ket": "SAI", "lay": "or_tho", "that": 1.84, "uoc": 6.0, "ci_95": [4, 9]}, ["SAI"]),
                     ({"ket": "CHUA_DO", "lay": "auc"}, ["CHUA_DO"])):
        p = tmp_path / "bc.json"
        p.write_text(json.dumps({**tot, "chinh_xac": cx}), encoding="utf-8", newline="\n")
        loi = KG.kiem_mot(p)
        assert [m for m in mong if any(m in x for x in loi)] == mong and (bool(loi) == bool(mong)), (cx, loi)
    assert set(KG.CHAN_THUC) == {f"{t}_chan_thuc" for t in ("rct", "cross_sectional", "cohort", "case_control",
                                                            "diagnostic", "prediction", "sr_ma", "qualitative")}
    assert set(GCT.KIEM_CHINH_XAC) == set(KG.CHAN_THUC) - {"qualitative_chan_thuc"}


def test_workflow_ci_chay_du_8_kich_ban_chan_thuc():
    yaml = pytest.importorskip("yaml")
    import kiem_gia_lap_16 as KG

    wf = yaml.safe_load((ROOT / ".github" / "workflows" / "gia-lap-16.yml").read_text(encoding="utf-8"))
    ma_tran = {m["kb"]: m["node"] for m in wf["jobs"]["kich-ban"]["strategy"]["matrix"]["include"]}
    for kb in KG.CHAN_THUC:
        assert ma_tran.get(kb) == f"test_gia_lap_chan_thuc[{kb}]", kb
    assert set(KG.KICH_BAN) | set(KG.CHAN_THUC) == set(ma_tran)


def test_bo_gia_lap_so_tham_so_that_quy_doi_ty_le_phan_tram(monkeypatch):
    import gia_lap_tron_vong as TV

    tv = object.__new__(TV.TronVong)
    monkeypatch.setattr(GCT, "tham_so_that", lambda ma, **_kw: {"cross_sectional_chan_thuc": 0.41,
                                                                "case_control_chan_thuc": 1.84}[ma])
    tv.ma = "cross_sectional_chan_thuc"
    tv._uoc_luong = lambda lay, gate: {"uoc": 40.0, "ci": [35.2, 44.9], "p": None, "nguon": "x", "so_le": 1}
    kq = tv.kiem_chinh_xac()
    assert kq["ket"] == "DAT" and kq["lay"] == "ty_le" and kq["that"] == 41.0  # tỷ lệ báo theo %
    tv.ma = "case_control_chan_thuc"
    tv._uoc_luong = lambda lay, gate: {"uoc": 6.0, "ci": [4.5, 8.0], "p": None, "nguon": "x", "so_le": 2}
    assert tv.kiem_chinh_xac()["ket"] == "SAI"
    tv._uoc_luong = lambda lay, gate: None
    assert tv.kiem_chinh_xac()["ket"] == "CHUA_DO"
    tv.ma = "rct_nhi_phan"
    assert tv.kiem_chinh_xac()["ket"] == "KHONG_AP_DUNG"
