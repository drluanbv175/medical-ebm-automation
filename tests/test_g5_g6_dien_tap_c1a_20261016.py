"""Lỗi công cụ lộ ra khi DIỄN TẬP C1a (16/10/2026) — F2, F6, F7, F12; mỗi lỗi một chốt, ngoại tuyến."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import clean_research_dataset as CLEAN  # noqa: E402
import g5_quality_gate as G5Q  # noqa: E402
import g6_quality_gate as G6  # noqa: E402
import kiem_de_cuong_nop_hoi_dong as KDN  # noqa: E402

COT = ["Variable / Field Name", "Form Name", "Section Header", "Field Type", "Field Label",
       "Choices, Calculations, OR Slider Labels", "Field Note", "Text Validation Type OR Show Slider Number",
       "Text Validation Min", "Text Validation Max", "Identifier?", "Branching Logic (Show field only if...)",
       "Required Field?"]


def _tu_dien(tmp_path: Path) -> Path:
    p = tmp_path / "dict.csv"
    with p.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COT)
        w.writeheader()
        w.writerow({"Variable / Field Name": "record_id", "Field Type": "text", "Field Label": "Mã phiếu",
                    "Required Field?": "y"})
        w.writerow({"Variable / Field Name": "lydo_chon", "Field Type": "checkbox", "Field Label": "Lý do (tối đa 2)",
                    "Choices, Calculations, OR Slider Labels": "1, Gần nhà | 2, Bác sĩ giỏi | 3, Khác"})
        w.writerow({"Variable / Field Name": "g1", "Field Type": "radio", "Field Label": "Hài lòng chung",
                    "Choices, Calculations, OR Slider Labels": "1, Rất không hài lòng | 5, Rất hài lòng"})
    return p


# ── F6: cột xuất checkbox REDCap `<biến>___<mã>` ─────────────────────────────────────────────────────────────────────
def test_f6_lam_sach_nhan_cot_xuat_checkbox(tmp_path):
    luat = {r["name"]: r for r in CLEAN._load_dictionary(_tu_dien(tmp_path))["variables"]}
    assert {"lydo_chon___1", "lydo_chon___2", "lydo_chon___3"} <= set(luat)
    assert luat["lydo_chon___2"]["allowed"] == ["0", "1"] and luat["lydo_chon___2"]["required"] is False
    rules = {CLEAN.RDI._normalize_header(k): v for k, v in luat.items()}
    hang = [{"record_id": "R1", "lydo_chon___1": "1", "lydo_chon___2": "0", "lydo_chon___3": "0", "g1": "4"}]
    loi = CLEAN._validate_rows(list(hang[0]), hang, rules, "record_id", [])
    assert not [x for x in loi if x.get("issue_type") == "undeclared_column"], loi


def test_f6_gia_tri_khac_0_1_o_cot_checkbox_van_bi_bat(tmp_path):
    luat = {CLEAN.RDI._normalize_header(r["name"]): r for r in CLEAN._load_dictionary(_tu_dien(tmp_path))["variables"]}
    hang = [{"record_id": "R1", "lydo_chon___1": "7", "lydo_chon___2": "0", "lydo_chon___3": "0", "g1": "4"}]
    assert CLEAN._validate_rows(list(hang[0]), hang, luat, "record_id", []), "giá trị 7 ở cột 0/1 phải ra query"


def test_f6_cong_g5_tinh_cot_xuat_checkbox_la_da_khai(tmp_path):
    d = G5Q._read_redcap_dictionary(_tu_dien(tmp_path))
    assert {"lydo_chon___1", "lydo_chon___3"} <= set(d["export_names"])
    assert "lydo_chon___1" not in d["names"], "tên biến gốc giữ nguyên — chỉ thêm tên cột xuất"


# ── F7: đường dẫn dictionary tương đối theo gốc repo ─────────────────────────────────────────────────────────────────
def test_f7_duong_dan_tuong_doi_quy_ve_thu_muc_de_tai(tmp_path, monkeypatch):
    out_dir = tmp_path / "exports" / "S"
    out_dir.mkdir(parents=True)
    (out_dir / "dict.csv").write_text("x\n", encoding="utf-8", newline="\n")
    monkeypatch.chdir(tmp_path)
    assert CLEAN.duong_dan_tu_dien_trong_bao_cao(Path("exports/S/dict.csv"), out_dir) == "dict.csv"
    assert CLEAN.duong_dan_tu_dien_trong_bao_cao(out_dir / "dict.csv", out_dir) == "dict.csv"
    assert CLEAN.duong_dan_tu_dien_trong_bao_cao(None, out_dir) is None


# ── F12: G6-AUTO-08 không đòi script LÀM SẠCH của G5 gọi chốt «dữ liệu đã khoá» ───────────────────────────────────────
def test_f12_script_lam_sach_g5_that_duoc_mien():
    nd = '"""\ndata_cleaning.py — Lam sach du lieu REDCap cho de tai: S\n"""\nimport pandas as pd\npd.read_csv(x)\n'
    assert G6._la_script_lam_sach_g5("data_cleaning.py", nd)


def test_f12_doi_ten_script_phan_tich_khong_lot():
    nd = '"""Phân tích chính"""\nimport pandas as pd\npd.read_csv(x)\n'
    assert not G6._la_script_lam_sach_g5("data_cleaning.py", nd)
    assert not G6._la_script_lam_sach_g5("phan_tich.py", nd)


# ── F2: đề cương nộp phải mang DE + N tối thiểu của G3 ───────────────────────────────────────────────────────────────
def _de_cuong(tmp_path: Path, than: str, g3: dict) -> Path:
    out = tmp_path / "S"
    out.mkdir()
    (out / "G3_checkpoint.json").write_text(json.dumps(g3), encoding="utf-8", newline="\n")
    (out / "DE_CUONG_NOP_HOI_DONG_S.md").write_text("# ĐẶT VẤN ĐỀ\n" + than + "\n", encoding="utf-8", newline="\n")
    return out


def test_f2_de_cuong_dung_de_khac_g3_bi_bao(tmp_path):
    out = _de_cuong(tmp_path, "DE = 1,78; tối thiểu 808; chốt 1.000 phiếu.",
                    {"confirmed_n": 1000, "n_adjusted": 626, "design_effect": 1.38})
    k5 = [x for x in KDN.kiem(out, "S") if x.startswith("K5")]
    assert any("DE 1.38" in x for x in k5) and any("626" in x for x in k5), k5


def test_f2_de_cuong_khop_g3_khong_bao(tmp_path):
    out = _de_cuong(tmp_path, "DE = 1,38; tối thiểu 626; chốt 1.000 phiếu.",
                    {"confirmed_n": 1000, "n_adjusted": 626, "design_effect": 1.38})
    assert not [x for x in KDN.kiem(out, "S") if x.startswith("K5")]


# ── F16: mã hợp lệ của câu chọn đáp án REDCap phải được đọc (bản cũ rỗng ⇒ không bắt mã sai) ─────────────────────────
def test_f16_ma_hop_le_radio_redcap_duoc_doc_va_ma_sai_bi_bat(tmp_path):
    luat = {CLEAN.RDI._normalize_header(r["name"]): r for r in CLEAN._load_dictionary(_tu_dien(tmp_path))["variables"]}
    assert luat["g1"]["allowed"] == ["1", "5"]
    hang = [{"record_id": "R1", "lydo_chon___1": "0", "lydo_chon___2": "0", "lydo_chon___3": "0", "g1": "7"}]
    assert CLEAN._validate_rows(list(hang[0]), hang, luat, "record_id", []), "g1 = 7 ngoài mã hợp lệ phải ra query"
