# -*- coding: utf-8 -*-
"""G7 dựng Bảng 1 và kết cục PHỤ từ đầu ra G6 (giả lập lần 3, 15/11/2026).

Giả lập lần 3 đo được trên đề tài RCT tổng hợp: G7 đã chép số chính của G6 (N16, #261) nhưng
  • Bảng 1 luôn là ô trống: tóm tắt G6 chỉ mang n_per_group, giá trị từng biến nằm ở `G6_table1_descriptive.txt`; khung
    dựng từ từ điển còn kéo cả biến KẾT CỤC (huyết áp tháng 6, kiểm soát HA…) vào «đặc điểm nền»;
  • bảng .txt của G6 in «n=-» (khoá nhóm số ≠ chuỗi) và ô phân loại dài dính sang cột nhóm kế tiếp;
  • §4 kết cục phụ luôn trống dù chay_sap_g6 đã chạy từng kết cục phụ của SAP (mỗi cái một tóm tắt riêng).
Nay G6 ghi Bảng 1 có cấu trúc (`bang1_cho_tom_tat`), G7 chép NGUYÊN VĂN (có tự kiểm số) kèm nhãn đối chiếu; §4 chép từ
chỉ mục SAP với CÙNG luật hợp lệ + tự kiểm như tóm tắt chính. Thư mục tạm, dữ liệu tổng hợp, không PII, không mạng.
Cần bác sĩ kiểm chứng.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT / "tools", ROOT / "tests"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import run_g7_auto as G7A  # noqa: E402
import run_stats_analysis as RS  # noqa: E402
from test_g7_tu_dien_ket_qua_g6_20261115 import SHA, _ghi_tom_tat, _manifest, _sinh, _tom_tat_nhi_phan  # noqa: E402

DF = pd.DataFrame({
    "nhom": [0] * 6 + [1] * 6,
    "tuoi": [50.0, 52.5, 61.0, 58.0, 49.0, 63.0, 55.0, 57.5, 60.0, 47.0, 66.0, 59.0],
    "gioi": [1, 0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 0],
    "so_thuoc": [1, 2, 3, 1, 2, 4, 1, 1, 2, 3, 3, 4],
})
BANG1_G6 = {"n_per_group": {"0": 109, "1": 109}, "groups": ["0", "1"], "rows": [
    {"variable": "tuoi", "type": "continuous", "gia_tri": {"0": "59.56 ± 10.84", "1": "59.60 ± 9.66"}, "p": None,
     "test": "không kiểm định (RCT — CONSORT 2010)"},
    {"variable": "so_thuoc_nen", "type": "categorical",
     "gia_tri": {"0": "1: 47(43%); 2: 35(32%); 3: 22(20%); 4: 5(5%)",
                 "1": "1: 51(47%); 2: 31(28%); 3: 24(22%); 4: 3(3%)"},
     "p": None, "test": "không kiểm định (RCT — CONSORT 2010)"}]}


# ───────────────────────────────────────────────────────────────────────────────────────────── G6
def test_g6_bang1_cho_tom_tat_khoa_chuoi_va_gia_tri_nguyen_van():
    t1 = RS.table1_descriptive(DF, "nhom", ["tuoi", "gioi", "so_thuoc"], kiem_dinh_nen=False)
    b = RS.bang1_cho_tom_tat(t1)
    assert b["groups"] == ["0", "1"] and b["n_per_group"] == {"0": 6, "1": 6}
    theo = {r["variable"]: r for r in b["rows"]}
    assert set(theo) == {"tuoi", "gioi", "so_thuoc"}
    assert theo["tuoi"]["gia_tri"] == {"0": t1["rows"][0]["grp_0"], "1": t1["rows"][0]["grp_1"]}
    assert theo["tuoi"]["p"] is None and "CONSORT" in theo["tuoi"]["test"]
    json.dumps(b)  # ghi được JSON (khoá numpy từng làm hỏng)


def test_g6_bang1_co_kiem_dinh_thi_p_la_so_thuc():
    t1 = RS.table1_descriptive(DF, "nhom", ["tuoi", "gioi"], kiem_dinh_nen=True)
    b = RS.bang1_cho_tom_tat(t1)
    ps = [r["p"] for r in b["rows"]]
    assert all(p is None or isinstance(p, float) for p in ps) and any(isinstance(p, float) for p in ps)


def test_g6_bang1_txt_dung_n_moi_nhom_va_cot_khong_dinh():
    t1 = RS.table1_descriptive(DF, "nhom", ["tuoi", "so_thuoc"], kiem_dinh_nen=False)
    txt = RS.format_table1_text(t1)
    assert "Nhóm 0 (n=6)" in txt and "Nhóm 1 (n=6)" in txt and "(n=-)" not in txt
    dong = next(d for d in txt.splitlines() if d.startswith("so_thuoc"))
    o0 = next(r for r in t1["rows"] if r["variable"] == "so_thuoc")["grp_0"]
    assert f"{o0}  " in dong, "ô nhóm 0 phải tách khỏi ô nhóm 1 ít nhất hai khoảng trắng"


# ───────────────────────────────────────────────────────────────────────────────────────────── G7 Bảng 1
def _de_tai(tmp_path: Path, **de) -> Path:
    out = tmp_path / "exports" / "THU"
    _manifest(out)
    _ghi_tom_tat(out, _tom_tat_nhi_phan(**de))
    return out


def test_g7_bang1_chep_nguyen_van_tu_g6_va_tu_kiem_sach(tmp_path):
    out = _de_tai(tmp_path, table1=BANG1_G6)
    g6 = G7A.doc_tom_tat_g6_hop_le(out)
    kq = G7A.dung_ket_qua_tu_g6(g6)
    assert kq["da_dung"], kq.get("ly_do")
    assert kq["bien_bang1"] == ["tuoi", "so_thuoc_nen"]
    s2 = "\n".join(kq["s2"])
    assert "| `tuoi` | 59,56 ± 10,84 | 59,60 ± 9,66 | không kiểm định (RCT — CONSORT 2010) |" in s2
    assert "| `so_thuoc_nen` | 1: 47(43%); 2: 35(32%); 3: 22(20%); 4: 5(5%) |" in s2
    assert "Nhóm `0` (N=109)" in s2 and G7A.NHAN_DOI_CHIEU_G6 in s2
    assert "chưa mang giá trị từng biến" not in s2
    assert G7A.kiem_so_trich_g6(s2, g6["van_ban"]) == []


def test_g7_bang1_tom_tat_cu_chi_co_n_thi_giu_o_trong(tmp_path):
    out = _de_tai(tmp_path)  # table1 = {"n_per_group": …} như tóm tắt trước bản vá
    kq = G7A.dung_ket_qua_tu_g6(G7A.doc_tom_tat_g6_hop_le(out))
    assert kq["da_dung"] and kq["bien_bang1"] == []
    assert any("chưa mang giá trị từng biến" in d for d in kq["s2"])


def test_g7_bang1_nhom_lech_n_per_group_thi_khong_chep(tmp_path):
    lech = json.loads(json.dumps(BANG1_G6))
    lech["rows"][0]["gia_tri"] = {"0": "1", "2": "2"}
    out = _de_tai(tmp_path, table1=lech)
    kq = G7A.dung_ket_qua_tu_g6(G7A.doc_tom_tat_g6_hop_le(out))
    assert kq["da_dung"] and kq["bien_bang1"] == []


def test_g7_bang1_so_bia_trong_o_thi_bo_ca_ban_nhap(tmp_path, monkeypatch):
    """Tự kiểm vẫn canh: bộ dựng bảng mà chép sai một số ⇒ bỏ cả bản nháp (fail-closed)."""
    out = _de_tai(tmp_path, table1=BANG1_G6)
    goc = G7A._o_bang1
    monkeypatch.setattr(G7A, "_o_bang1", lambda v: goc(v).replace("59.56", "59.6"))
    kq = G7A.dung_ket_qua_tu_g6(G7A.doc_tom_tat_g6_hop_le(out))
    assert kq["da_dung"] is False and "tự kiểm" in kq["ly_do"]


def test_g7_chu_giai_bang1_thay_khung_tu_dien_va_vao_ban_thao(tmp_path):
    out = _de_tai(tmp_path, table1=BANG1_G6)
    kq = G7A.dung_ket_qua_tu_g6(G7A.doc_tom_tat_g6_hop_le(out))
    tu_dien = [{"variable": "tuoi", "label": "Tuổi (năm)", "form": "demo"},
               {"variable": "so_thuoc_nen", "label": "Số thuốc hạ áp lúc nền (≥ 2 thuốc)", "form": "demo"},
               {"variable": "kiem_soat_t6", "label": "Kiểm soát HA tháng 6 (<140/90)", "form": "demo"}]
    cg = G7A.chu_giai_bang1_g6(tu_dien, kq["bien_bang1"])
    assert "`tuoi` = Tuổi (năm)" in cg and "kiem_soat_t6" not in cg, "chỉ chú giải biến của Bảng 1 G6"
    text = _sinh(ket_qua_g6=kq, table1_shell=cg)
    assert "| `tuoi` | 59,56 ± 10,84 |" in text and "`so_thuoc_nen` = Số thuốc hạ áp lúc nền (≥ 2 thuốc)" in text
    assert G7A.guardrail_g7(text)[0] == []


# ───────────────────────────────────────────────────────────────────────────────────────────── G7 §4 kết cục phụ
def _chi_muc(out: Path, phan_tich: list, sha: str = SHA) -> None:
    (out / G7A.TEP_SAP_KET_QUA_G6).write_text(json.dumps(
        {"study": "THU", "du_lieu_khoa": {"tep": "x.csv", "sha256": sha}, "phan_tich": phan_tich},
        ensure_ascii=False), encoding="utf-8", newline="\n")


# Đúng khoá compare_primary_outcome ghi cho kết cục liên tục (md_crude; nhóm có n/mean/sd).
KCP = {"outcome_type": "continuous", "groups": ["0", "1"], "group_0": {"n": 96, "mean": 6.1234, "sd": 1.9876},
       "group_1": {"n": 88, "mean": 7.0412, "sd": 1.7654}, "md_crude": 0.9178, "p_value": 0.0011,
       "test": "Welch t-test"}


def test_g7_ket_cuc_phu_tu_chi_muc_sap_g6(tmp_path):
    out = _de_tai(tmp_path)
    _ghi_tom_tat(out, _tom_tat_nhi_phan(primary_outcome=KCP, multivariate=None, multiple_imputation=None,
                                        table1=None, n_total=184), "G6_KCP1_analysis_summary.json")
    _chi_muc(out, [
        {"id": "chinh", "vai": "chinh", "trang_thai": "DA_CHAY", "gate": "G6"},
        {"id": "KCP1", "vai": "phu", "sap_muc": "§8", "mo_ta": "điểm tuân thủ 0–10", "trang_thai": "DA_CHAY",
         "gate": "G6_KCP1"},
        {"id": "KCP2", "vai": "phu", "sap_muc": "§8", "trang_thai": "CHUA_TU_DONG", "ly_do": "spline RCS"},
        {"id": "KCP3", "vai": "phu", "sap_muc": "§8", "trang_thai": "LOI", "ly_do": "thiếu biến x"},
        {"id": "DN1", "vai": "do_nhay", "trang_thai": "DA_CHAY", "gate": "G6_DN1"}])
    dong = G7A.dung_ket_cuc_phu_g6(out)
    text = "\n".join(dong)
    assert "**`KCP1`** (SAP §8)" in text and "n = 184" in text and "MD = 0,9178" in text and "7,0412" in text
    assert "`KCP2`** (SAP §8): [CẦN THỐNG KÊ VIÊN — SAP cam kết nhưng hệ chưa có công cụ" in text
    assert "`KCP3`** (SAP §8): [CẦN THỐNG KÊ VIÊN — G6 chạy phân tích này LỖI: thiếu biến x]" in text
    assert "DN1" not in text and "`chinh`" not in text, "chỉ vai «phu» vào §4"
    vb = (out / "G6_KCP1_analysis_summary.json").read_text(encoding="utf-8")
    khoi_kcp1 = text.split("**`KCP2`**")[0]
    assert G7A.kiem_so_trich_g6("\n".join(x for x in khoi_kcp1.splitlines() if "SAP §8" not in x), vb) == []


def test_g7_ket_cuc_phu_tom_tat_khac_ban_khoa_thi_o_can_thong_ke_vien(tmp_path):
    out = _de_tai(tmp_path)
    tt = _tom_tat_nhi_phan(primary_outcome=KCP, n_total=184)
    tt["data_lock"] = {"sha256": "cd" * 32}
    _ghi_tom_tat(out, tt, "G6_KCP1_analysis_summary.json")
    _chi_muc(out, [{"id": "KCP1", "vai": "phu", "trang_thai": "DA_CHAY", "gate": "G6_KCP1"}])
    text = "\n".join(G7A.dung_ket_cuc_phu_g6(out))
    assert "dataset KHÁC bản khoá" in text and "0.9178" not in text


def test_g7_ket_cuc_phu_chi_muc_khac_ban_khoa_thi_khong_chep(tmp_path):
    out = _de_tai(tmp_path)
    _chi_muc(out, [{"id": "KCP1", "vai": "phu", "trang_thai": "DA_CHAY", "gate": "G6_KCP1"}], sha="ef" * 32)
    dong = G7A.dung_ket_cuc_phu_g6(out)
    assert len(dong) == 1 and "KHÁC bản khoá" in dong[0]


def test_g7_ket_cuc_phu_khong_co_chi_muc_hoac_khong_co_phu_thi_none(tmp_path):
    out = _de_tai(tmp_path)
    assert G7A.dung_ket_cuc_phu_g6(out) is None
    _chi_muc(out, [{"id": "chinh", "vai": "chinh", "trang_thai": "DA_CHAY", "gate": "G6"}])
    assert G7A.dung_ket_cuc_phu_g6(out) is None


def test_g7_ket_cuc_phu_gate_la_khong_doc_tep_ngoai(tmp_path):
    out = _de_tai(tmp_path)
    _chi_muc(out, [{"id": "KCP1", "vai": "phu", "trang_thai": "DA_CHAY", "gate": "../../ngoai"}])
    assert "gate lạ" in "\n".join(G7A.dung_ket_cuc_phu_g6(out))


def test_g7_ket_cuc_phu_vao_ban_thao_va_qua_guardrail(tmp_path):
    out = _de_tai(tmp_path)
    _ghi_tom_tat(out, _tom_tat_nhi_phan(primary_outcome=KCP, n_total=184), "G6_KCP1_analysis_summary.json")
    _chi_muc(out, [{"id": "KCP1", "vai": "phu", "sap_muc": "§8", "trang_thai": "DA_CHAY", "gate": "G6_KCP1"}])
    kq = G7A.dung_ket_qua_tu_g6(G7A.doc_tom_tat_g6_hop_le(out))
    kq["s4"] = G7A.dung_ket_cuc_phu_g6(out)
    text = _sinh(ket_qua_g6=kq)
    muc4 = text.split("**§4 Kết cục phụ")[1].split("**§5")[0]
    assert "0,9178" in muc4 and "tóm tắt G6 không chứa kết cục phụ" not in muc4
    assert G7A.guardrail_g7(text)[0] == []


# ── sửa sau thẩm định đối kháng #277 ─────────────────────────────────────────────────────────────────────────────────
import hashlib  # noqa: E402


def _bang1(nhom: dict, rows: list) -> dict:
    return {"n_per_group": nhom, "groups": list(nhom), "rows": rows}


def test_g7_bang1_o_dai_khong_cat_va_giu_ngoac_vuong(tmp_path):
    """Đ3: ô bị cắt ở 120 ký tự từng cắt GIỮA số («Khh: 1…») mà tự kiểm vẫn sạch. X2: «[q1–q3]» giữ nguyên."""
    dai = "; ".join(f"Nghề {i}: {i * 3}({i}%)" for i in range(1, 15))
    t1 = _bang1({"0": 109, "1": 109}, [
        {"variable": "nghe", "type": "categorical", "gia_tri": {"0": dai, "1": "Nghề 1: 5(5%)"}, "p": None,
         "test": "—"},
        {"variable": "so_con", "type": "continuous", "gia_tri": {"0": "2.00 [1.00–9.75]", "1": "2.00 [1.00–3.00]"},
         "p": None, "test": "—"}])
    out = _de_tai(tmp_path, table1=t1)
    g6 = G7A.doc_tom_tat_g6_hop_le(out)
    kq = G7A.dung_ket_qua_tu_g6(g6)
    s2 = "\n".join(kq["s2"])
    assert dai in s2 and "…" not in s2 and "2,00 [1,00–9,75]" in s2  # 23/11/2026: số theo quy ước tiếng Việt
    assert G7A.kiem_so_trich_g6(s2, g6["van_ban"]) == []


def test_g7_bang1_tra_theo_khoa_nhom_goc_va_o_rong_la_o_cho(tmp_path):
    """V1: nhãn nhóm có khoảng trắng cuối/«|» từng làm ô thành «N/A». V2: ô rỗng thành ô chờ, không im lặng."""
    t1 = _bang1({"Chứng ": 3, "Can|thiệp": 3}, [
        {"variable": "tuoi", "type": "continuous", "gia_tri": {"Chứng ": "57.42 ± 6.28", "Can|thiệp": "58.10 ± 5.01"},
         "p": None, "test": "—"},
        {"variable": "hoc_van", "type": "categorical", "gia_tri": {"Chứng ": "Cấp 1: 2(67%)", "Can|thiệp": ""},
         "p": None, "test": "—"}])
    out = _de_tai(tmp_path, table1=t1)
    kq = G7A.dung_ket_qua_tu_g6(G7A.doc_tom_tat_g6_hop_le(out))
    s2 = "\n".join(kq["s2"])
    assert "| `tuoi` | 57,42 ± 6,28 | 58,10 ± 5,01 |" in s2 and "N/A" not in s2
    assert "| `hoc_van` | Cấp 1: 2(67%) | [CẦN THỐNG KÊ VIÊN — G6 không ghi giá trị ô này] |" in s2


def test_g6_bang1_nhom_thieu_toan_bo_bien_phan_loai_ghi_n_a():
    """V2 (phía G6): nhóm thiếu toàn bộ biến phân loại kiểu chữ từng cho chuỗi rỗng."""
    df = pd.DataFrame({"nhom": [0, 0, 0, 1, 1, 1], "hoc_van": ["Cấp 1", "Cấp 2", "Cấp 3", None, None, None]})
    t1 = RS.table1_descriptive(df, "nhom", ["hoc_van"], kiem_dinh_nen=False)
    assert t1["rows"][0]["type"] == "categorical", "tiền đề: nhánh PHÂN LOẠI (3 mức), không phải nhị phân"
    assert RS.bang1_cho_tom_tat(t1)["rows"][0]["gia_tri"]["1"] == "N/A (0 quan sát)"


def _sap_va_dac_ta(out: Path, phan_tich: list) -> dict:
    sap = out / "G4_A5_SAP_FINAL_THU.md"
    sap.write_text("# SAP\n## §8 Kết cục phụ\n", encoding="utf-8", newline="\n")
    dt = {"nguon_sap": sap.name, "sha256_sap": hashlib.sha256(sap.read_bytes()).hexdigest(), "phan_tich": phan_tich}
    (out / "G6_DAC_TA_SAP.json").write_text(json.dumps(dt, ensure_ascii=False), encoding="utf-8", newline="\n")
    return dt


def _chi_muc_co_dau(out: Path, phan_tich: list) -> None:
    import chay_sap_g6 as CSG  # noqa: PLC0415

    dt = CSG.doc_dac_ta(out)
    (out / G7A.TEP_SAP_KET_QUA_G6).write_text(json.dumps(
        {"study": "THU", "dac_ta": {"dau": CSG.kiem_dac_ta(out, dt)["dau"]},
         "du_lieu_khoa": {"tep": "x.csv", "sha256": SHA}, "phan_tich": phan_tich}, ensure_ascii=False),
        encoding="utf-8", newline="\n")


DT_PHU = [{"id": "KCP1", "vai": "phu", "sap_muc": "§8", "tham_so": {"outcome": "diem_tuan_thu"}},
          {"id": "KCP2", "vai": "phu", "sap_muc": "§8", "tham_so": {"outcome": "ha_tt"}}]


def _kcp1(out: Path, outcome: str = "diem_tuan_thu") -> dict:
    tt = _tom_tat_nhi_phan(primary_outcome=KCP, n_total=184, multivariate={
        "model": "logistic", "n": 184,
        "results": [{"variable": "nhom", "OR_adj": 2.1, "CI_95": [1.2, 3.4], "p": 0.01}]},
        dac_ta_phan_tich={"outcome": outcome})
    _ghi_tom_tat(out, tt, "G6_KCP1_analysis_summary.json")
    return tt


def test_g7_ket_cuc_phu_doi_chieu_dac_ta_sap(tmp_path):
    """V4: kết cục phụ của đặc tả vắng trong chỉ mục ⇒ ô chờ (không biến mất im lặng); V3: nhãn bảng theo gate."""
    import chay_sap_g6 as CSG  # noqa: PLC0415

    out = _de_tai(tmp_path)
    _sap_va_dac_ta(out, DT_PHU)
    tt = _kcp1(out)
    _chi_muc_co_dau(out, [{"id": "KCP1", "vai": "phu", "sap_muc": "§8", "trang_thai": "DA_CHAY", "gate": "G6_KCP1",
                           "uoc_luong": CSG._tom_tat_uoc_luong(tt)}])
    text = "\n".join(G7A.dung_ket_cuc_phu_g6(out))
    assert "MD = 0,9178" in text and "`G6_KCP1_table4_multivariate.txt`" in text
    assert "`G6_table4_multivariate.txt`" not in text
    assert "**`KCP2`** (SAP §8): [CẦN THỐNG KÊ VIÊN — SAP cam kết kết cục phụ này" in text


def test_g7_ket_cuc_phu_sai_ket_cuc_hoac_chi_muc_cu_thi_o_cho(tmp_path):
    import chay_sap_g6 as CSG  # noqa: PLC0415

    out = _de_tai(tmp_path)
    _sap_va_dac_ta(out, DT_PHU[:1])
    tt = _kcp1(out, outcome="can_nang_t6")   # chạy lại tay với kết cục khác đặc tả
    _chi_muc_co_dau(out, [{"id": "KCP1", "vai": "phu", "trang_thai": "DA_CHAY", "gate": "G6_KCP1",
                           "uoc_luong": CSG._tom_tat_uoc_luong(tt)}])
    text = "\n".join(G7A.dung_ket_cuc_phu_g6(out))
    assert "kết cục «can_nang_t6» nhưng đặc tả SAP là «diem_tuan_thu»" in text and "0.9178" not in text
    _kcp1(out)
    _chi_muc_co_dau(out, [{"id": "KCP1", "vai": "phu", "trang_thai": "DA_CHAY", "gate": "G6_KCP1",
                           "uoc_luong": {"n_total": 184, "md_tho": {"uoc_luong": 0.5}}}])
    text = "\n".join(G7A.dung_ket_cuc_phu_g6(out))
    assert "đã đổi sau khi lập chỉ mục" in text and "0.9178" not in text


def test_g7_ket_cuc_phu_dac_ta_hoac_sap_doi_thi_khong_chep(tmp_path):
    import chay_sap_g6 as CSG  # noqa: PLC0415

    out = _de_tai(tmp_path)
    _sap_va_dac_ta(out, DT_PHU[:1])
    tt = _kcp1(out)
    _chi_muc_co_dau(out, [{"id": "KCP1", "vai": "phu", "trang_thai": "DA_CHAY", "gate": "G6_KCP1",
                           "uoc_luong": CSG._tom_tat_uoc_luong(tt)}])
    _sap_va_dac_ta(out, DT_PHU)   # đặc tả đổi sau lượt chạy
    dong = G7A.dung_ket_cuc_phu_g6(out)
    assert len(dong) == 1 and "đặc tả CŨ" in dong[0]
    (out / "G4_A5_SAP_FINAL_THU.md").write_text("# SAP đã sửa\n", encoding="utf-8", newline="\n")
    dong = G7A.dung_ket_cuc_phu_g6(out)
    assert len(dong) == 1 and "SAP đã ĐỔI" in dong[0]


def test_g7_ket_cuc_phu_tu_kiem_so_bia_thi_o_cho(tmp_path, monkeypatch):
    """X1: nhánh tự kiểm của §4 chưa có test — bộ dựng chép sai một số ⇒ ô [CẦN THỐNG KÊ VIÊN], không in số đó."""
    out = _de_tai(tmp_path)
    _kcp1(out)
    _chi_muc(out, [{"id": "KCP1", "vai": "phu", "trang_thai": "DA_CHAY", "gate": "G6_KCP1"}])
    monkeypatch.setattr(G7A, "_khoi_uoc_luong_g6", lambda tt, nguon, tien_to="G6": ["MD = 9.9999 (bịa)  "])
    text = "\n".join(G7A.dung_ket_cuc_phu_g6(out))
    assert "tự kiểm" in text and "MD = 9.9999" not in text
