# -*- coding: utf-8 -*-
"""Dữ liệu giả lập đóng vai người khai/thu thập cho ba mục chuẩn báo cáo còn thiếu (22/11/2026).

Đo trên gói giả lập trọn vòng: bản thảo chẩn đoán thiếu STARD 2015 mục 21b (chẩn đoán khác ở người không có bệnh đích),
bản thảo tổng quan gộp thiếu PRISMA 2020 mục 16b (trích dẫn báo cáo bị loại), 17 (trích dẫn từng nghiên cứu được đưa
vào) và 22 (mức chắc chắn GRADE) — vì DỮ LIỆU GIẢ LẬP chưa có dữ kiện, không phải vì bộ sinh. Sửa tại nguồn:
- chẩn đoán: phiếu có biến «chẩn đoán khác» (chỉ hỏi khi không có bệnh đích), dữ liệu mô phỏng có giá trị, PI khai biến
  ở đặc tả; G6 mô tả ở Bảng 1 theo chuẩn tham chiếu (biến chỉ ghi nhận ở một nhóm thì KHÔNG kiểm định — trước đây chi
  bình phương trên bảng một cột cho p = 1,0); bộ sinh G7 chép số của nhóm không bệnh từ G6;
- tổng quan: thử nghiệm mô phỏng mang mã đăng ký HƯ CẤU (dải NCT9999xxxx chưa cấp), bảng trích xuất có cột trích dẫn;
  nhóm sàng lọc ghi ba thử nghiệm THẬT bị loại ở bước toàn văn (PMID đã tra, kiểm rút bài); nhóm tác giả xếp GRADE theo
  luật năm lĩnh vực trên kết quả G6 thật của lượt chạy; bộ sinh G7 in đúng các lời khai đó, khai không hợp lệ ⇒ ô [CẦN].
"""
from __future__ import annotations

import csv
import json
import sys
import types
from pathlib import Path

import pandas as pd
import pytest

TOOLS = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import gia_lap_kich_ban_them as KBT  # noqa: E402
import gia_lap_tron_vong as TV  # noqa: E402
import run_g7_auto as G7  # noqa: E402
import run_stats_analysis as RSA  # noqa: E402
import tieu_chi_ban_thao as TB  # noqa: E402

from tests.test_g7_chuan_bao_cao_5_thiet_ke_20261122 import (  # noqa: E402
    _G6_CHAN_DOAN,
    _G6_GOP,
    _PI_CHAN_DOAN,
    _PI_TONG_QUAN,
    TAC_GIA,
    _ban_thao,
    _ghi,
    _meta,
    _nop,
    _tong_quan,
    _tt,
)


# ───────────────────────────── G6 Bảng 1: biến chỉ ghi nhận ở một nhóm ─────────────────────────────
def test_bang1_bien_chi_ghi_nhan_o_mot_nhom_khong_kiem_dinh():
    df = pd.DataFrame({"benh": [0, 0, 0, 0, 1, 1, 1],
                       "chan_doan_khac": ["F0–F1", "F2", "F0–F1", "Khác", None, None, None],
                       "tuoi": [50, 60, 55, 70, 65, 58, 62]})
    t1 = RSA.table1_descriptive(df, "benh", ["chan_doan_khac", "tuoi"])
    r = {x["variable"]: x for x in t1["rows"]}
    assert "p" not in r["chan_doan_khac"] and r["chan_doan_khac"]["test"] == RSA.KHONG_KIEM_DINH_MOT_NHOM
    assert r["chan_doan_khac"]["grp_1"] == "N/A (0 quan sát)"
    assert "F0–F1: 2(50%)" in r["chan_doan_khac"]["grp_0"]
    assert "p" in r["tuoi"]  # biến có ở cả hai nhóm vẫn kiểm định như cũ


# ───────────────────────────── dữ liệu mô phỏng ─────────────────────────────
def test_chan_doan_khac_chi_o_nguoi_khong_benh_va_khong_doi_so_lieu_cu():
    bs = KBT.bien_so_them()["chan_doan"]
    assert bs["meta_bien"]["chan_doan_khac"]["nhanh"] == "[xo_hoa_tien_trien] = '0'"
    g3 = {"prevalence": 0.3, "effect_size": 0.76}
    hang = TV.sinh_du_lieu("diagnostic", bs, g3, 120)
    assert all((r["chan_doan_khac"] is None) == (r["xo_hoa_tien_trien"] == 1) for r in hang)
    assert {r["chan_doan_khac"] for r in hang if r["xo_hoa_tien_trien"] == 0} <= {1, 2, 3}
    assert all(r["chan_doan_khac"] in (1, 3) for r in hang if r["xo_hoa_tien_trien"] == 0 and r["lsm_kpa"] < 8.0)
    khong = {**bs, "bo_bien": [b for b in bs["bo_bien"] if b[0] != "chan_doan_khac"]}
    assert [{k: v for k, v in r.items() if k != "chan_doan_khac"} for r in hang] == \
        TV.sinh_du_lieu("diagnostic", khong, g3, 120)


def test_tong_quan_ma_dang_ky_hu_cau_tat_dinh_va_khong_doi_so_lieu_cu():
    bs = KBT.bien_so_them()["tong_quan_gop"]
    hang = TV.sinh_du_lieu("sr_ma", bs, {}, 15)
    ma = [r["ma_dang_ky"] for r in hang]
    assert ma[0] == "NCT99990001" and len(set(ma)) == len(ma)
    assert all(m.startswith("NCT9999") and len(m) == 11 for m in ma)
    khong = {**bs, "bo_bien": [b for b in bs["bo_bien"] if b[0] != "ma_dang_ky"]}
    assert [{k: v for k, v in r.items() if k != "ma_dang_ky"} for r in hang] == TV.sinh_du_lieu("sr_ma", khong, {}, 15)


def test_ho_so_bao_cao_loai_la_thu_nghiem_that_co_pmid_nhom_ly_do_cua_so():
    ds = KBT.ho_so_tron_vong()["tong_quan_gop"]["sang_loc_toan_van_loai"]
    assert {d["trich_dan"].split("PMID ")[1] for d in ds} == {"31535829", "32865377", "33200892"}
    assert all(d["nhom_ly_do"] == "Sai quần thể" and d["ly_do"] for d in ds)


def _khoa(d: Path, cot: list, dong: list) -> None:
    (d / "05_clean_locked").mkdir(parents=True)
    with (d / "05_clean_locked" / "x.locked.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(cot)
        w.writerows(dong)
    (d / "DATA_LOCK_manifest.json").write_text(json.dumps({"locked_dataset_path": "05_clean_locked/x.locked.csv"}),
                                               encoding="utf-8", newline="\n")


def test_bang_trich_xuat_co_cot_trich_dan_va_ghi_danh_sach_loai(tmp_path):
    _khoa(tmp_path, ["study_id", "ma_dang_ky", "n_can_thiep", "bien_co_can_thiep", "n_chung", "bien_co_chung"],
          [["TN01-2016", "NCT99990001", "3264", "77", "3217", "110"],
           ["TN02-2017", "NCT99990002", "2375", "78", "2419", "120"]])
    kb = {"ho_so_tron_vong": {"sang_loc_toan_van_loai": KBT.ho_so_tron_vong()["tong_quan_gop"][
        "sang_loc_toan_van_loai"]}}
    gia = types.SimpleNamespace(out=tmp_path, buoc=[], kb=kb)
    TV.TronVong._bang_trich_xuat_sr(gia)
    with (tmp_path / TV.TEP_TRICH_XUAT_SR).open(encoding="utf-8", newline="") as fh:
        assert [r["trich_dan"] for r in csv.DictReader(fh)] == ["NCT99990001, 2016", "NCT99990002, 2017"]
    with (tmp_path / G7.TEP_LOAI_TOAN_VAN_TQ).open(encoding="utf-8", newline="") as fh:
        assert [r["bao_cao"] for r in csv.DictReader(fh)] == ["DAPA-HF", "EMPEROR-Reduced", "SOLOIST-WHF"]


def test_bang_trich_xuat_khong_ma_dang_ky_thi_khong_cot_trich_dan_khong_danh_sach(tmp_path):
    _khoa(tmp_path, ["study_id", "n_can_thiep", "bien_co_can_thiep", "n_chung", "bien_co_chung"],
          [["TN01-2016", "3264", "77", "3217", "110"], ["TN02-2017", "2375", "78", "2419", "120"]])
    TV.TronVong._bang_trich_xuat_sr(types.SimpleNamespace(out=tmp_path, buoc=[]))
    with (tmp_path / TV.TEP_TRICH_XUAT_SR).open(encoding="utf-8", newline="") as fh:
        assert "trich_dan" not in (csv.DictReader(fh).fieldnames or [])
    assert not (tmp_path / G7.TEP_LOAI_TOAN_VAN_TQ).exists()


# ───────────────────────────── bộ sinh G7: STARD 21b ─────────────────────────────
_G6_CD_21B = json.loads(json.dumps(_G6_CHAN_DOAN))
_G6_CD_21B["tom_tat"]["table1"]["rows"].append(
    {"variable": "chan_doan_khac", "gia_tri": {"0": "Không có hoặc xơ hoá nhẹ (F0–F1): 25(69%); Xơ hoá đáng kể chưa "
                                                     "tiến triển (F2): 10(28%); Bệnh gan khác kèm theo: 1(3%)",
                                               "1": "N/A (0 quan sát)"}})


def test_stard_21b_dat_khi_pi_khai_bien_va_g6_co_dong(tmp_path, monkeypatch):
    monkeypatch.setattr(G7, "doc_tom_tat_g6_hop_le", lambda out_dir: _G6_CD_21B)
    d = _meta(tmp_path, {"G1": {"reference_standard": "Đo độ đàn hồi gan ≥ 10 kPa"}, "G7": TAC_GIA},
              **_PI_CHAN_DOAN, alternative_diagnosis_variable="chan_doan_khac")
    md = _ban_thao(d, "diagnostic", "Nghiên cứu Độ chính xác Chẩn đoán", "STARD 2015",
                   redcap_vars=[{"variable": "chan_doan_khac",
                                 "label": "Chẩn đoán ở người không có xơ hoá tiến triển"}],
                   khoi_chan_doan_du_bao=G7._khoi_chan_doan_du_bao_g7(d, "diagnostic"))
    assert _tt(md, "diagnostic", "STARD 2015")["21b"] == "dat"
    assert ("*Chẩn đoán khác ở người không có bệnh đích (Chẩn đoán ở người không có xơ hoá tiến triển, "
            "`chan_doan_khac`):* Không có hoặc xơ hoá nhẹ (F0–F1): 25(69%)") in md
    assert "(n = 36)" in md


def test_stard_21b_khong_dung_so_khi_thieu_khai_nhom_khong_quan_sat_hoac_nhom_mo_ho(tmp_path, monkeypatch):
    monkeypatch.setattr(G7, "doc_tom_tat_g6_hop_le", lambda out_dir: _G6_CD_21B)
    d = _meta(tmp_path, {}, **_PI_CHAN_DOAN)
    assert G7._chan_doan_khac_g7(d, G7._doc_meta_g7(d), None).count("[CẦN — ") == 1  # PI chưa khai biến
    d = _meta(tmp_path, {}, **_PI_CHAN_DOAN, alternative_diagnosis_variable="chan_doan_khac")
    sai = json.loads(json.dumps(_G6_CD_21B))
    sai["tom_tat"]["dac_thu"]["auc"]["n_khong_benh"] = 17  # nhóm khớp là nhóm bệnh ⇒ ô «N/A»
    monkeypatch.setattr(G7, "doc_tom_tat_g6_hop_le", lambda out_dir: sai)
    assert G7._chan_doan_khac_g7(d, G7._doc_meta_g7(d), None).count("[CẦN — ") == 1
    mo_ho = json.loads(json.dumps(_G6_CD_21B))
    mo_ho["tom_tat"]["table1"]["n_per_group"] = {"0": 36, "1": 36}
    monkeypatch.setattr(G7, "doc_tom_tat_g6_hop_le", lambda out_dir: mo_ho)
    assert "F0–F1" not in G7._chan_doan_khac_g7(d, G7._doc_meta_g7(d), None)


# ───────────────────────────── bộ sinh G7: PRISMA 16b, 17, 22 ─────────────────────────────
_LUONG = ("buoc,n,loai,nhanh,ly_do\nBản ghi xác định qua cơ sở dữ liệu và nguồn khác,557,chinh,,\n"
          "Báo cáo bị loại,28,loai,,Sai quần thể: 14; Sai can thiệp: 9; Sai kết cục: 2; Sai thiết kế: 3\n"
          "Nghiên cứu đưa vào tổng quan,15,chinh,,\n")
_LOAI = ("bao_cao,trich_dan,nhom_ly_do,ly_do\n"
         "DAPA-HF,\"McMurray và cộng sự 2019, PMID 31535829\",Sai quần thể,chỉ tuyển người suy tim\n"
         "SOLOIST-WHF,\"Bhatt và cộng sự 2021, PMID 33200892\",Sai quần thể,chỉ tuyển người vừa nhập viện vì suy tim\n")
_GRADE = {"grade_certainty": "cao",
          "grade_rationale": "bằng chứng từ thử nghiệm ngẫu nhiên, khởi điểm ở mức cao; nguy cơ sai lệch: không hạ bậc"}


def _du_tong_quan(d: Path) -> None:
    _ghi(d / "SO_DO_LUONG_X.csv", _LUONG)
    _ghi(d / G7.TEP_LOAI_TOAN_VAN_TQ, _LOAI)
    _ghi(d / G7._TEP_TRICH_XUAT_TQ, "study,year,trich_dan\nTN01-2016,2016,\"NCT99990001, 2016\"\n"
                                    "TN02-2017,2017,\"NCT99990002, 2017\"\n")


def test_prisma_16b_17_22_dat_khi_du_lieu_khai_du(tmp_path, monkeypatch):
    monkeypatch.setattr(G7, "doc_tom_tat_g6_hop_le", lambda out_dir: _G6_GOP)
    d = _meta(tmp_path, {"G7": {**TAC_GIA, **_GRADE}, "G1": {"primary_outcome": {"name": "Nhập viện vì suy tim"}}},
              **_PI_TONG_QUAN)
    _du_tong_quan(d)
    md = _tong_quan(d)
    tt = _tt(md, "sr_ma", "PRISMA 2020")
    assert (tt["16b"], tt["22"]) == ("dat", "dat"), tt
    # 17: yếu tố trích dẫn đạt; yếu tố «bảng đặc điểm từng nghiên cứu» do G6 dựng (phép thử không truyền kết quả G6)
    kq = TB.doi_chieu_ban_thao(_nop(md), "sr_ma", co_so_lieu=True)
    r17 = next(r for r in kq["ket_qua"] if r.chuan == "PRISMA 2020" and r.ma == "17")
    assert r17.thieu == ["đặc điểm các nghiên cứu"], r17.thieu
    assert ("DAPA-HF (McMurray và cộng sự 2019, PMID 31535829) bị loại vì sai quần thể: chỉ tuyển người suy tim; "
            "SOLOIST-WHF") in md
    assert "TN01-2016 (NCT99990001, 2016); TN02-2017 (NCT99990002, 2017)." in md
    assert "*Kết cục chính «Nhập viện vì suy tim»:* mức chắc chắn cao — bằng chứng từ thử nghiệm ngẫu nhiên" in md


def test_prisma_16b_khong_in_khi_danh_sach_vuot_so_dem_cua_so(tmp_path):
    _ghi(tmp_path / "SO_DO_LUONG_X.csv", _LUONG.replace("Sai quần thể: 14", "Sai quần thể: 1"))
    _ghi(tmp_path / G7.TEP_LOAI_TOAN_VAN_TQ, _LOAI)
    assert "không khớp số đếm" in G7._bao_cao_loai_tong_quan_g7(tmp_path)
    _ghi(tmp_path / "SO_DO_LUONG_X.csv", _LUONG)
    _ghi(tmp_path / G7.TEP_LOAI_TOAN_VAN_TQ, _LOAI.replace("Sai quần thể,chỉ tuyển người suy tim", "Sai quần thể,"))
    assert G7._bao_cao_loai_tong_quan_g7(tmp_path).count("[CẦN — ") == 1  # dòng thiếu lý do ⇒ không in


@pytest.mark.parametrize("g7", [{}, {"grade_certainty": "vừa phải", "grade_rationale": "x"},
                                {"grade_certainty": "cao", "grade_rationale": ""}])
def test_grade_chua_khai_hoac_khong_hop_le_thi_o_can(g7):
    dong = G7._muc_chac_chan_tong_quan_g7(g7, "Nhập viện vì suy tim")[1]
    assert dong.count("[CẦN — ") == 1 and "mức chắc chắn cao" not in dong
    assert G7._muc_grade_da_khai(g7) == ("", "")


# ───────────────────────────── vai nhóm tác giả: xếp GRADE theo luật trên kết quả G6 ─────────────────────────────
def _tv_tong_quan(tmp_path: Path, i2=0.0, ci=(0.64, 0.75), egger_p=0.68, rob=("1", "1", "2"),
                  nguoi=79845, ris=25462) -> TV.TronVong:
    tv = TV.TronVong("tong_quan_gop", tmp_path, chay=lambda *a, **k: {"ma": 0, "dong": []})
    tv.out.mkdir(parents=True)
    tung = [{"nghien_cuu": f"TN0{i}", "trong_so_ngau_nhien_pct": 100 / len(rob)} for i in range(1, len(rob) + 1)]
    _ghi(tv.out / "G6_analysis_summary.json", json.dumps({"dac_thu": {
        "tung_nghien_cuu": tung, "tong": {"nguoi": nguoi}, "ci_95": list(ci), "i2_pct": i2,
        "egger": {"da_chay": True, "p": egger_p}}}))
    _ghi(tv.out / TV.TEP_TRICH_XUAT_SR, "study,rob2_tong\n" + "".join(f"TN0{i},{r}\n" for i, r in enumerate(rob, 1)))
    _ghi(tv.out / "G3_checkpoint.json", json.dumps({"confirmed_n": ris}))
    return tv


def test_tac_gia_xep_grade_khong_ha_bac_thi_cao(tmp_path):
    muc, ly_do = _tv_tong_quan(tmp_path)._xep_grade_tac_gia()
    assert muc == "cao" and ly_do.count("không hạ bậc") == 5


@pytest.mark.parametrize("tham, muc", [({"i2": 62.0}, "trung bình"),
                                       ({"i2": 62.0, "ci": (0.8, 1.1)}, "thấp"),
                                       ({"rob": ("2", "2", "1")}, "trung bình"),
                                       ({"egger_p": 0.04}, "trung bình"),
                                       ({"nguoi": 20000}, "trung bình"),
                                       ({"i2": 70.0, "ci": (0.8, 1.1), "egger_p": 0.01, "rob": ("3", "3", "1")},
                                        "rất thấp")])
def test_tac_gia_xep_grade_ha_bac_theo_tung_linh_vuc(tmp_path, tham, muc):
    assert _tv_tong_quan(tmp_path, **tham)._xep_grade_tac_gia()[0] == muc


def test_khai_truoc_ban_thao_tong_quan_ghi_grade_va_g7_giu_lai(tmp_path):
    tv = _tv_tong_quan(tmp_path)
    tv._ghi_meta({"gate_params": {"G1": {"design": "sr_ma"}}})
    tv._khai_truoc_ban_thao()
    g7 = tv._meta()["gate_params"]["G7"]
    assert g7["grade_certainty"] == "cao" and "khởi điểm ở mức cao" in g7["grade_rationale"]
    assert tv.du_lieu["khai_truoc_ban_thao"]["gate_params.G7.grade_certainty"] == "nhóm tác giả (GRADE)"
    # lời khai đã có (nhóm tác giả tự xếp) thì không xếp đè
    tv._ghi_meta({"gate_params": {"G7": {"grade_certainty": "trung bình", "grade_rationale": "riêng"}}})
    tv._khai_truoc_ban_thao()
    assert tv._meta()["gate_params"]["G7"]["grade_certainty"] == "trung bình"


def test_g7_ghi_lai_gate_params_giu_loi_khai_grade():
    """Dòng THI HÀNH của `TronVong.g7` ghi lại `gate_params.G7` sau lượt sinh phải giữ hai khoá GRADE (lời khai không có
    trong hồ sơ tĩnh — mất là bản thảo sinh lại ở G10 rơi về ô [CẦN])."""
    import ast  # noqa: PLC0415
    import inspect  # noqa: PLC0415
    import textwrap  # noqa: PLC0415

    cay = ast.parse(textwrap.dedent(inspect.getsource(TV.TronVong.g7)))
    giu = [n for n in ast.walk(cay) if isinstance(n, ast.Tuple)
           and {getattr(e, "value", None) for e in n.elts} == {"grade_certainty", "grade_rationale"}]
    assert giu, "TronVong.g7 không giữ lời khai GRADE khi ghi lại gate_params.G7"


# ───────────────────────────── đề cương nộp: STARD 2015 mục 3 (báo cáo tổng hợp lấy đặt vấn đề từ đây) ─────────────
def _nguon_dvd(thiet_ke: str, vai_tro: str = "Xét nghiệm phân loại ban đầu tại phòng khám ngoại trú"):
    return types.SimpleNamespace(
        td=types.SimpleNamespace(thay=lambda x: x), thiet_ke=thiet_ke,
        g1={"background_problem": "Không phải ai cũng tiếp cận được đo đàn hồi gan", "objectives": ["Xác định X"]},
        s=lambda *a: None, meta={"title": "Đề tài thử", "index_test_role": vai_tro})


def test_dat_van_de_de_cuong_nop_neu_vai_tro_xet_nghiem_chan_doan():
    import sinh_de_cuong_nop_hoi_dong as SDC  # noqa: PLC0415

    dong = SDC.chuong_dat_van_de(_nguon_dvd("diagnostic"))
    assert ("Vai trò dự kiến của xét nghiệm đánh giá trong lộ trình chẩn đoán: xét nghiệm phân loại ban đầu tại phòng "
            "khám ngoại trú.") in dong
    assert not any("Vai trò dự kiến" in d for d in SDC.chuong_dat_van_de(_nguon_dvd("cohort")))
    assert not any("Vai trò dự kiến" in d for d in SDC.chuong_dat_van_de(_nguon_dvd("diagnostic", "")))


# ───────────────────────────── COREQ 2007 / SRQR 2014: đã đối chiếu bản in lại, bật chặn ─────────────────────────
def test_coreq_srqr_da_doi_chieu_ghi_nguon_dung_va_chan():
    import kiem_chuan_de_cuong_theo_muc as K  # noqa: PLC0415
    import tieu_chi_chuan_de_cuong as TC  # noqa: PLC0415

    assert set(TC.CHUAN_CHUA_DOI_CHIEU_GOC) == set() and TC.CHUAN_DA_DOI_CHIEU_CHUA_CHAN == {}
    for chuan, nguon in (("COREQ 2007", ("PMC12567161", "PMC12731783")), ("SRQR 2014", ("PMC12027544",))):
        ghi_chu = TC.NGUON_DOI_CHIEU_BAN_IN_LAI[chuan]
        # nói đúng sự thật: đối chiếu bản in lại toàn văn trong nguồn CC BY, không nói «đã đối chiếu bài gốc»
        assert "bản in lại toàn văn bảng gốc" in ghi_chu and "CC BY" in ghi_chu and "bài gốc" not in ghi_chu
        assert all(p in ghi_chu for p in nguon)
        assert all(m.chan is True for m in TC.danh_sach_muc_them(chuan))
    # 22/11/2026: TREND 2004 đối chiếu Bảng 1 bản gốc ⇒ mục chặn (chưa có văn bản kiểm chứng: «chưa đo được» ở K17)
    assert all(m.chan is True for m in TC.danh_sach_muc_them("TREND 2004"))
    md = "## TÊN\n\n# 4. ĐỐI TƯỢNG VÀ PHƯƠNG PHÁP NGHIÊN CỨU\n\n## 4.1. Thiết kế nghiên cứu\n\nNghiên cứu định tính."
    coreq = [r for r in K.doi_chieu(md, "qualitative")["ket_qua"] if r.chuan == "COREQ 2007"]
    assert any(r.trang_thai == "thieu" for r in coreq) and not any(r.trang_thai == "canh_bao" for r in coreq)


def test_tieu_chi_coreq_sau_doi_chieu_nhan_lien_tiep_va_email():
    import re  # noqa: PLC0415

    import tieu_chi_chuan_de_cuong as TC  # noqa: PLC0415

    muc = {m.ma: m for m in TC.danh_sach_muc_them("COREQ 2007")}
    assert re.search(muc["10"].yeu_to[0].mau, "Chọn mẫu liên tiếp người bệnh đến khám", re.I)
    assert re.search(muc["11"].yeu_to[0].mau, "Mời qua email người bệnh đủ tiêu chuẩn", re.I)
    assert "lý do và mối quan tâm" in muc["8"].tieu_chi and "cách phản tư" not in muc["8"].tieu_chi
