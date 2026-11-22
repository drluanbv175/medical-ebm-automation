"""Giả lập: thống kê viên đối chiếu biện pháp kiểm soát sai lệch G1 ↔ mục SAP (`_doi-chieu-sai-lech-sap.csv`).

22/11/2026 (kiểm 13 khâu): ba kịch bản quan sát khai 2–4 sai lệch ở G1 mà không có bảng đối chiếu ⇒ trục nhất quán
«Kiểm soát sai lệch G1 ↔ SAP» CHƯA ĐỦ ĐỂ SO."""
from __future__ import annotations

import csv
import json
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import doi_chieu_sai_lech_sap as DS  # noqa: E402
import gia_lap_tron_vong as TV  # noqa: E402

S = "ZZTEST-SL"
SAP = """# SAP

## PHẦN 3, SAP 12 MỤC CUỐI

### §5 PHÂN TÍCH ĐA BIẾN

- Hiệu chỉnh theo DAG đã khai.

### §6 DỮ LIỆU THIẾU

- **Chiến lược:** Multiple Imputation (MI, m=20)

### §9 PHÂN TÍCH ĐỘ NHẠY

- Loại người theo dõi dưới 12 tháng

### §10 PHẦN MỀM + SEED

- R 4.4
"""
BIAS = [
    {"sai_lech": "Nhiễu do chỉ định", "bien_phap": "Hiệu chỉnh đa biến theo DAG", "chieu": "…"},
    {"sai_lech": "Mất theo dõi", "bien_phap": "Gán đa trị kết cục thiếu; phân tích độ nhạy loại người theo dõi "
                                           "dưới 12 tháng", "chieu": "…"},
    {"sai_lech": "Đo lường", "bien_phap": "Đo chuẩn hoá bằng máy đã hiệu chuẩn, đo 2 lần", "chieu": "…"},
    {"sai_lech": "Gộp tầng", "bien_phap": "Phân tầng theo cơ sở rồi hồi quy Poisson", "chieu": "…"},
]


def _dung(tmp_path: Path, bias=BIAS) -> types.SimpleNamespace:
    out = tmp_path / S
    out.mkdir()
    (out / f"G4_A5_SAP_FINAL_{S}.md").write_text(SAP, encoding="utf-8", newline="\n")
    (out / "study_meta.json").write_text(json.dumps({"gate_params": {"G1": {"bias_controls": bias}}},
                                                    ensure_ascii=False), encoding="utf-8", newline="\n")
    return types.SimpleNamespace(out=out, study=S, _meta=lambda: json.loads((out / "study_meta.json").read_text(
        encoding="utf-8")), _NEO_PHAN_TICH=TV.TronVong._NEO_PHAN_TICH, _tim_nguyen_van=TV.TronVong._tim_nguyen_van)


def _dong(ns):
    with (ns.out / "_doi-chieu-sai-lech-sap.csv").open(encoding="utf-8") as fh:
        return {r["sai_lech"]: r for r in csv.DictReader(fh)}


def test_neo_nguyen_van_trong_sap_va_kiem_dat_tru_bien_phap_sap_khong_co(tmp_path):
    ns = _dung(tmp_path)
    TV.TronVong._ghi_doi_chieu_sai_lech_sap(ns)
    d = _dong(ns)
    assert d["Nhiễu do chỉ định"]["sap_muc"] == "§5" and "DAG" in d["Nhiễu do chỉ định"]["sap_neo"]
    mt = d["Mất theo dõi"]
    assert mt["sap_muc"] == "§6; §9" and mt["sap_neo"] == "Multiple Imputation | Loại người theo dõi dưới 12 tháng"
    assert d["Đo lường"]["can_phan_tich"] == "khong" and d["Đo lường"]["noi_khac"]
    # SAP không có phân tầng hay Poisson ⇒ KHÔNG đoán mục: để ô [CẦN …] và bộ kiểm phải báo lỗi
    assert d["Gộp tầng"]["sap_muc"] == "[CẦN §]"
    k = DS.kiem(ns.out, S)
    assert k["trang_thai"] != "DAT" and any(x["ma"] == "SL-05" and "Gộp tầng" in x["noi_dung"] for x in k["loi"])


def test_du_neo_thi_bo_kiem_dat(tmp_path):
    ns = _dung(tmp_path, BIAS[:3])
    TV.TronVong._ghi_doi_chieu_sai_lech_sap(ns)
    assert DS.kiem(ns.out, S)["trang_thai"] == "DAT"


def test_khong_ghi_de_bang_da_co(tmp_path):
    ns = _dung(tmp_path)
    (ns.out / "_doi-chieu-sai-lech-sap.csv").write_text("sai_lech\nngười đã chốt\n", encoding="utf-8", newline="\n")
    TV.TronVong._ghi_doi_chieu_sai_lech_sap(ns)
    assert (ns.out / "_doi-chieu-sai-lech-sap.csv").read_text(encoding="utf-8") == "sai_lech\nngười đã chốt\n"
