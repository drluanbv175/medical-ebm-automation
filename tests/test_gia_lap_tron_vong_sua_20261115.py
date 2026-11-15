"""Lỗi hệ thống lộ ra khi giả lập TRỌN VÒNG như một đề tài thật (bác sĩ 15/11/2026).

1. Trục kết cục chính so NGUYÊN dòng §2 mà CHÍNH máy điền sẵn từ G1 («tên; đo bằng …; thời điểm: … — biến `x`
   *(điền sẵn …)*») với tên kết cục G0 ⇒ lệch mềm ⇒ PI phải xác nhận «cùng một kết cục» cho một đề tài nhất quán từ đầu
   (đề tài thuần tập tổng hợp; BTM phải làm đúng bước này — mục B1 phiếu quyết định 15/11).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import nhat_quan_xuyen_cong as NQ  # noqa: E402
import run_g4_auto as G4A  # noqa: E402

TEN = "Gãy xương mọi vị trí trong thời gian theo dõi"
DO = "Chẩn đoán gãy xương mới có phim X-quang xác nhận trong hồ sơ"
TD = "Trong 3 năm kể từ ngày bắt đầu theo dõi"


def _dong_khuon() -> str:
    """Dòng §2 do CHÍNH bộ sinh SAP điền (đi qua `_dien_khung` thật — đổi khuôn thì test này theo)."""
    sap = "- **Kết cục chính:** [CẦN BÁC SĨ ĐIỀN — ví dụ: tỷ lệ nhập viện tim mạch trong 12 tháng]  "
    khung = {"ket_cuc": {"name": TEN, "measure": DO, "timepoint": TD, "type": "nhị phân"},
             "ket_cuc_bien": "gay_xuong_3nam"}
    return G4A._dien_khung(sap, khung, "cohort")


def _sap(dong: str) -> str:
    return f"# SAP\n\n### §2 KẾT CỤC\n\n{dong}\n\n### §3 CỠ MẪU\n\nN\n"


@pytest.mark.parametrize("dong", [
    _dong_khuon(),
    # cùng khuôn sau khi bộ chuẩn trình bày đổi « — » thành dấu câu (đo được trên SAP thật của giả lập)
    f"- **Kết cục chính:** {TEN}; đo bằng {DO}; thời điểm: {TD}. Biến `gay_xuong_3nam` "
    "*(điền sẵn từ quyết định đã chốt, thống kê viên/PI sửa nếu cần)*  ",
])
def test_ten_ket_cuc_sap_bo_duoi_may_dien(dong):
    assert NQ._ten_ket_cuc_sap(_sap(dong)) == TEN


def test_sap_nguoi_viet_khong_theo_khuon_giu_nguyen():
    dong = "- **Kết cục chính (MT1):** Tỷ lệ gãy xương sau 3 năm theo hồ sơ"
    assert NQ._ten_ket_cuc_sap(_sap(dong)) == "Tỷ lệ gãy xương sau 3 năm theo hồ sơ"


def _de_tai(tmp_path: Path, dong_sap: str) -> Path:
    out = tmp_path / "exports" / "ZZT-KC"
    out.mkdir(parents=True)
    po = {"name": TEN, "measure": DO, "timepoint": TD, "type": "nhị phân"}
    meta = {"gate_params": {"G0": {"primary_outcome": TEN, "primary_outcome_measure": DO,
                                   "primary_outcome_timepoint": TD},
                            "G1": {"primary_outcome": po}}}
    (out / "study_meta.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8", newline="\n")
    (out / "G4_A5_SAP_FINAL_ZZT-KC.md").write_text(_sap(dong_sap), encoding="utf-8", newline="\n")
    return out


def _truc(out: Path) -> dict:
    return next(t for t in NQ.doi_chieu(out, "ZZT-KC")["thong_so"] if t["ma"] == "ket_cuc_chinh")


def test_truc_ket_cuc_chinh_khop_khi_sap_do_may_dien_tu_g1(tmp_path):
    t = _truc(_de_tai(tmp_path, _dong_khuon()))
    assert t["muc"] == NQ.MUC_KHOP, t


def test_truc_ket_cuc_chinh_van_bat_doi_ket_cuc_that(tmp_path):
    t = _truc(_de_tai(tmp_path, "- **Kết cục chính:** Tử vong mọi nguyên nhân trong 3 năm; đo bằng hồ sơ"))
    assert t["muc"] == NQ.MUC_LECH_MEM, t


def _dong_khuon_chi_ten() -> str:
    sap = "- **Kết cục chính:** [CẦN BÁC SĨ ĐIỀN — ví dụ: tỷ lệ nhập viện tim mạch trong 12 tháng]  "
    return G4A._dien_khung(sap, {"ket_cuc": {"name": TEN}, "ket_cuc_bien": "gay_xuong_3nam"}, "cohort")


@pytest.mark.parametrize("dong", [
    _dong_khuon_chi_ten(),
    f"- **Kết cục chính:** {TEN}. Biến `gay_xuong_3nam` *(điền sẵn từ quyết định đã chốt, thống kê viên/PI sửa)*  ",
])
def test_khuon_chi_co_ten_bien_va_ghi_chu(dong):
    assert NQ._ten_ket_cuc_sap(_sap(dong)) == TEN, dong


# ─────────────────────── 2. G3: thiết kế không dùng công thức lực mẫu mà khai «descriptive_precision» (đề tài định
# tính)
import g3_quality_gate as G3Q  # noqa: E402

from tests._chuoi_da_chot import chay_g3_that, dung_g0_g1_da_chot  # noqa: E402


@pytest.mark.parametrize("thiet_ke, them", [
    ("qualitative", {"saturation_stopping_rule": "Dừng khi 3 phỏng vấn liên tiếp không có mã mới (tối thiểu 12)",
                     "confirmed_n_method": "Bão hoà dữ liệu"}),
    ("prediction", {"confirmed_n_method": "pmsampsize Riley 2020: 10 tham số, tỷ lệ biến cố 20% ⇒ 898"}),
])
def test_a4_khong_in_khung_do_chinh_xac_cho_thiet_ke_khong_dung_power(tmp_path, thiet_ke, them):
    """Giả lập trọn vòng: run_g3_auto in «Với độ tin cậy 95% (α = 0.05) và sai số d = ±5%» vào khối dán đề cương của đề
    tài ĐỊNH TÍNH khi PI khai hypothesis_type «descriptive_precision» ⇒ chính G3-AUTO-17 của hệ chặn đề tài."""
    study = f"ZZT-G3-{thiet_ke}"
    out = tmp_path / "exports" / study
    dung_g0_g1_da_chot(out, study, thiet_ke=thiet_ke)
    meta = json.loads((out / "study_meta.json").read_text(encoding="utf-8"))
    meta["gate_params"].setdefault("G3", {}).update(them)
    (out / "study_meta.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8", newline="\n")
    chay_g3_that(out, study, ["--confirmed-n", "20" if thiet_ke == "qualitative" else "900",
                              "--hypothesis-type", "descriptive_precision"])
    a4 = next(out.glob("G3_A4_SAMPLE_SIZE_*.md")).read_text(encoding="utf-8")
    assert not G3Q._POWER_LANGUAGE.search(G3Q._protocol_block(a4)), G3Q._protocol_block(a4)
    assert "sai số tuyệt đối cho phép" not in G3Q._protocol_block(a4)
    assert "Power ×" not in a4 and "Khung cỡ mẫu" in a4
    if thiet_ke == "qualitative":
        bao = G3Q.evaluate_study(study, out, write=False)
        tc = next(c for c in bao["automatic_criteria"] if c["id"] == "G3-AUTO-17")
        assert tc["status"] == "PASS", tc


# ─────────────────────── 3. Ma trận mục tiêu → biến: kết cục chính của phân tích gộp trích ở cấp nghiên cứu, từng nhánh
import csv as _csv  # noqa: E402

import ma_tran_muc_tieu_bien as MT  # noqa: E402


def _de_tai_ma_tran(tmp_path: Path, thiet_ke: str, dong_kc: list) -> Path:
    out = tmp_path / "exports" / "ZZT-MT"
    out.mkdir(parents=True)
    meta = {"gate_params": {"G1": {"design": thiet_ke, "objectives": ["Ước lượng hiệu quả của thuốc X lên biến cố Y"],
                                   "primary_outcome": {"name": "Biến cố Y", "type": "nhị phân"}}}}
    (out / "study_meta.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8", newline="\n")
    cot = ["Variable / Field Name", "Form Name", "Section Header", "Field Type", "Field Label",
           "Choices, Calculations, OR Slider Labels", "Field Note", "Text Validation Type OR Show Slider Number"]
    with (out / MT.TEP_BO_BIEN).open("w", encoding="utf-8", newline="") as fh:
        w = _csv.DictWriter(fh, fieldnames=cot)
        w.writeheader()
        for ten in ("study_id", "bien_co_can_thiep", "bien_co_chung", "thuoc"):
            w.writerow({"Variable / Field Name": ten, "Form Name": "trich_xuat", "Field Type": "text",
                        "Field Label": ten, "Text Validation Type OR Show Slider Number":
                            "" if ten in ("study_id", "thuoc") else "integer"})
    with (out / MT.TEP_MA_TRAN).open("w", encoding="utf-8", newline="") as fh:
        w = _csv.writer(fh)
        w.writerow(MT.COT)
        for bien, kieu in dong_kc:
            w.writerow(["1", "Biến cố Y", "ket_cuc_chinh", bien, kieu, "KC", "Bảng trích xuất", "§4", ""])
    return out


def _loi_mt05(out: Path) -> list:
    return [x["noi_dung"] for x in MT.kiem(out, "ZZT-MT")["loi"] if x["ma"] == "MT-05"]


def test_tong_quan_nhieu_dong_ket_cuc_chinh_cap_nghien_cuu_hop_le(tmp_path):
    out = _de_tai_ma_tran(tmp_path, "sr_ma", [("bien_co_can_thiep", "dem"), ("bien_co_chung", "dem")])
    assert _loi_mt05(out) == []


def test_thiet_ke_khac_van_dung_mot_ket_cuc_chinh(tmp_path):
    out = _de_tai_ma_tran(tmp_path, "cohort", [("bien_co_can_thiep", "dem"), ("bien_co_chung", "dem")])
    assert any("ĐÚNG một dòng" in x for x in _loi_mt05(out))


def test_tong_quan_nhieu_dong_nhi_phan_khong_phai_cap_nghien_cuu_van_bao(tmp_path):
    out = _de_tai_ma_tran(tmp_path, "sr_ma", [("bien_co_can_thiep", "nhi_phan"), ("bien_co_chung", "dem")])
    assert any("ĐÚNG một dòng" in x for x in _loi_mt05(out))
