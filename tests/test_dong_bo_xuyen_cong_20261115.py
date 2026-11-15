"""Đồng bộ xuyên cổng — ma trận mục tiêu → biến → câu hỏi → phân tích (bác sĩ duyệt 15/11/2026).

Tái hiện các lỗi đo được trên giả lập trung thực ZZSIM-DONGBO-TUANTHU-THA-20261115 (đề tài cắt ngang dùng bộ câu hỏi):
bộ biến thiếu yếu tố mục tiêu và kết cục chính nhị phân khai kiểu text vẫn qua mọi cổng; G5 rơi về bộ mẫu chung; SPSS/R
báo «✓ khớp» trên bộ biến sai; G1 bỏ ngưỡng «≥3 tháng» của quần thể G0 vẫn 🟢; biến «có BHYT» bị coi là định danh.
Chỉ dữ liệu tổng hợp, không PII. Cần bác sĩ kiểm chứng.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS))

import g3_quality_gate as G3Q  # noqa: E402
import g5_quality_gate as G5Q  # noqa: E402
import gate_contract as GC  # noqa: E402
import hoi_dong_cong as HD  # noqa: E402
import import_real_dataset as RDI  # noqa: E402
import ma_tran_muc_tieu_bien as MT  # noqa: E402
import nhat_quan_xuyen_cong as NQ  # noqa: E402
import run_g5_auto as RG5  # noqa: E402

STUDY = "ZZTEST-DONG-BO-20261115"
COT_TD = ["Variable / Field Name", "Form Name", "Section Header", "Field Type", "Field Label",
          "Choices, Calculations, OR Slider Labels", "Field Note", "Text Validation Type OR Show Slider Number",
          "Text Validation Min", "Text Validation Max", "Identifier?", "Branching Logic (Show field only if...)",
          "Required Field?", "Custom Alignment", "Question Number (surveys only)", "Matrix Group Name",
          "Matrix Ranking?", "Field Annotation"]
MUC_TIEU = [
    "Mục tiêu 1: Xác định tỷ lệ tuân thủ dùng thuốc hạ áp ở người bệnh tăng huyết áp điều trị ngoại trú",
    "Mục tiêu 2: Phân tích một số yếu tố liên quan đến tuân thủ: tuổi, số thuốc hạ áp, số lần dùng thuốc/ngày, "
    "hỗ trợ của gia đình",
]
BIEN_DUNG = [
    ("record_id", "text", "Mã nghiên cứu", "", "", ""),
    ("tuoi", "text", "Tuổi (năm)", "", "integer", ""),
    ("so_thuoc", "text", "Số thuốc hạ áp", "", "integer", ""),
    ("so_lan_ngay", "text", "Số lần dùng thuốc/ngày", "", "integer", ""),
    ("ho_tro_gd", "radio", "Gia đình hỗ trợ", "0, Không | 1, Có", "", ""),
    ("tuan_thu", "radio", "Tuân thủ (kết cục chính)", "0, Không | 1, Có", "", ""),
    ("tt1", "radio", "Câu TT1", "0, Không | 1, Có", "", ""),
]
MA_TRAN_DUNG = [
    ("1", "Tỷ lệ tuân thủ dùng thuốc hạ áp", "ket_cuc_chinh", "tuan_thu", "nhi_phan", "TT1", "bộ câu hỏi", "§4"),
    ("2", "tuổi", "yeu_to", "tuoi", "lien_tuc", "A1", "phiếu", "§5"),
    ("2", "số thuốc hạ áp", "yeu_to", "so_thuoc", "dem", "B1", "hồ sơ", "§5"),
    ("2", "số lần dùng thuốc/ngày", "yeu_to", "so_lan_ngay", "dem", "B3", "phiếu", "§5"),
    ("2", "hỗ trợ của gia đình", "yeu_to", "ho_tro_gd", "nhi_phan", "C1", "phiếu", "§5"),
]


def _ghi_bo_bien(d: Path, bien=BIEN_DUNG) -> None:
    with (d / MT.TEP_BO_BIEN).open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COT_TD)
        w.writeheader()
        for ten, kieu, nhan, lua, val, ann in bien:
            w.writerow({"Variable / Field Name": ten, "Form Name": "phieu", "Field Type": kieu, "Field Label": nhan,
                        "Choices, Calculations, OR Slider Labels": lua,
                        "Text Validation Type OR Show Slider Number": val, "Required Field?": "y",
                        "Field Annotation": ann})


def _ghi_ma_tran(d: Path, dong=MA_TRAN_DUNG) -> None:
    with (d / MT.TEP_MA_TRAN).open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(list(MT.COT))
        for r in dong:
            w.writerow(list(r) + [""])


def _de_tai(tmp_path: Path, *, kieu_kc: str = "Nhị phân (tuân thủ/không)") -> Path:
    d = tmp_path / "exports" / STUDY
    d.mkdir(parents=True)
    meta = {"topic": "tuân thủ thuốc hạ áp (tổng hợp)", "design_code": "cross_sectional",
            "gate_params": {
                "G0": {"population": "Người bệnh ≥18 tuổi tăng huyết áp điều trị ngoại trú ≥3 tháng tại phòng khám"},
                "G1": {"objectives": MUC_TIEU, "population": "Người bệnh ≥18 tuổi tăng huyết áp điều trị ngoại trú",
                       "primary_outcome": {"name": "Tỷ lệ tuân thủ dùng thuốc hạ áp", "measure": "8 câu",
                                           "timepoint": "khi phỏng vấn", "type": kieu_kc}}}}
    (d / "study_meta.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8", newline="\n")
    return d


# ───────────────────────────── bộ kiểm ma trận ─────────────────────────────
def test_tach_yeu_to_theo_dau_hai_cham_va_lien_tu():
    assert MT.tach_yeu_to(MUC_TIEU[1]) == ["tuổi", "số thuốc hạ áp", "số lần dùng thuốc/ngày", "hỗ trợ của gia đình"]
    assert MT.tach_yeu_to(MUC_TIEU[0]) == []  # mục tiêu không liệt kê ⇒ chỉ đòi ≥ 1 dòng


def test_khong_co_ma_tran_khong_bao_gio_la_dat(tmp_path):
    d = _de_tai(tmp_path)
    _ghi_bo_bien(d)
    kq = MT.kiem(d, STUDY)
    assert kq["trang_thai"] == MT.TRANG_THAI_KHONG_CO and kq["vai_tro"] is None


def test_ma_tran_dung_dat_va_tra_vai_tro(tmp_path):
    d = _de_tai(tmp_path)
    _ghi_bo_bien(d)
    _ghi_ma_tran(d)
    kq = MT.kiem(d, STUDY)
    assert kq["trang_thai"] == MT.TRANG_THAI_DAT, kq["loi"]
    assert kq["vai_tro"]["ket_cuc"] == "tuan_thu"
    assert kq["vai_tro"]["yeu_to"] == ["tuoi", "so_thuoc", "so_lan_ngay", "ho_tro_gd"]


def test_bat_yeu_to_muc_tieu_thieu_bien(tmp_path):
    """Lỗi đo được trên giả lập: thiếu «số lần dùng thuốc/ngày» và «hỗ trợ của gia đình» — không công cụ nào bắt."""
    d = _de_tai(tmp_path)
    _ghi_bo_bien(d)
    _ghi_ma_tran(d, MA_TRAN_DUNG[:3])
    kq = MT.kiem(d, STUDY)
    thieu = [x["noi_dung"] for x in kq["loi"] if x["ma"] == "MT-04"]
    assert kq["trang_thai"] == MT.TRANG_THAI_CHUA_DAT
    assert any("số lần dùng thuốc/ngày" in x for x in thieu) and any("hỗ trợ của gia đình" in x for x in thieu)


def test_bat_ket_cuc_nhi_phan_khai_kieu_text(tmp_path):
    d = _de_tai(tmp_path)
    bien = [b if b[0] != "tuan_thu" else ("tuan_thu", "text", "Tuân thủ", "", "", "") for b in BIEN_DUNG]
    _ghi_bo_bien(d, bien)
    _ghi_ma_tran(d)
    kq = MT.kiem(d, STUDY)
    assert any(x["ma"] == "MT-07" and "tuan_thu" in x["noi_dung"] for x in kq["loi"])


def test_bat_kieu_ket_cuc_lech_g1(tmp_path):
    d = _de_tai(tmp_path, kieu_kc="Liên tục (điểm 0–8)")
    _ghi_bo_bien(d)
    _ghi_ma_tran(d)
    assert any(x["ma"] == "MT-05" for x in MT.kiem(d, STUDY)["loi"])


def test_bat_bien_khong_co_trong_bo_bien(tmp_path):
    d = _de_tai(tmp_path)
    _ghi_bo_bien(d, [b for b in BIEN_DUNG if b[0] != "ho_tro_gd"])
    _ghi_ma_tran(d)
    assert any(x["ma"] == "MT-06" and "ho_tro_gd" in x["noi_dung"] for x in MT.kiem(d, STUDY)["loi"])


def test_bien_phai_sinh_phai_co_nguon_trong_bo_bien(tmp_path):
    d = _de_tai(tmp_path)
    _ghi_bo_bien(d, [b for b in BIEN_DUNG if b[0] != "tuan_thu"])
    (d / MT.TEP_PHAI_SINH).write_text(
        "ten_bien,nhan,kieu,bien_nguon,nhan_gia_tri,nguoi_duyet\n"
        "tuan_thu,Tuân thủ,nhị phân,tt1 tt9,0=Không; 1=Có,STATISTICIAN\n", encoding="utf-8", newline="\n")
    _ghi_ma_tran(d)
    kq = MT.kiem(d, STUDY)
    assert any(x["ma"] == "MT-08" and "tt9" in x["noi_dung"] for x in kq["loi"])


# ───────────────────────────── G3-AUTO-19 ─────────────────────────────
def test_g3_auto_19_review_khi_thieu_ma_tran_pass_khi_dat(tmp_path):
    d = _de_tai(tmp_path)
    _ghi_bo_bien(d)
    meta = MT.doc_meta(d)
    assert G3Q._tieu_chi_ma_tran(STUDY, d, meta)["status"] == "REVIEW"
    _ghi_ma_tran(d)
    assert G3Q._tieu_chi_ma_tran(STUDY, d, meta)["status"] == "PASS"


def test_g3_auto_19_khong_ha_cap_de_tai_da_ky_g4_truoc_moc(tmp_path, monkeypatch):
    """Luật mới không hạ cấp quyết định đã ký: G4 ký trước mốc ⇒ PASS kèm «MIỄN TRỪ … VẪN THIẾU»."""
    d = _de_tai(tmp_path)
    (d / "approval_ledger.json").write_text(json.dumps([{"gate_id": "G4", "decision": "APPROVED",
                                                          "timestamp_utc": "2026-10-17T03:00:00+00:00"}]),
                                            encoding="utf-8", newline="\n")
    monkeypatch.setattr(GC, "ledger_approved", lambda g, *a, **k: g == "G4")
    c = G3Q._tieu_chi_ma_tran(STUDY, d, MT.doc_meta(d))
    assert c["status"] == "PASS" and "MIỄN TRỪ" in c["evidence"] and "VẪN THIẾU" in c["evidence"]
    # chữ ký KHÔNG hợp lệ ⇒ không miễn trừ (fail-closed)
    monkeypatch.setattr(GC, "ledger_approved", lambda g, *a, **k: False)
    assert G3Q._tieu_chi_ma_tran(STUDY, d, MT.doc_meta(d))["status"] == "REVIEW"


def test_g3_auto_19_ky_sau_moc_khong_mien_tru(tmp_path, monkeypatch):
    d = _de_tai(tmp_path)
    (d / "approval_ledger.json").write_text(json.dumps([{"gate_id": "G4", "decision": "APPROVED",
                                                          "timestamp_utc": "2026-11-20T03:00:00+00:00"}]),
                                            encoding="utf-8", newline="\n")
    monkeypatch.setattr(GC, "ledger_approved", lambda g, *a, **k: g == "G4")
    assert G3Q._tieu_chi_ma_tran(STUDY, d, MT.doc_meta(d))["status"] == "REVIEW"


# ───────────────────────────── G5 ─────────────────────────────
def test_g5_dung_han_khi_khong_co_bo_bien_rieng(tmp_path):
    d = _de_tai(tmp_path)
    ma = RG5._dung_thieu_bo_bien(STUDY, d, "cross_sectional", "tuân thủ thuốc hạ áp")
    assert ma == GC.EXIT_BLOCKED
    assert not (d / f"G5_REDCap_dictionary_{STUDY}.csv").exists(), "bộ mẫu chung KHÔNG được thành từ điển G5"
    assert (d / RG5.TEN_TEP_GOI_Y_BO_MAU).exists()
    cp = json.loads((d / "G5_checkpoint.json").read_text(encoding="utf-8"))
    assert cp["needs_input"]["reason_code"] == GC.REASON_MISSING_VARIABLE_SET


def test_g5_main_goi_dung_thieu_bo_bien(tmp_path, monkeypatch):
    """Đường main(): G4 đã ký, chưa có bộ biến ⇒ dừng mã 2, không có từ điển."""
    d = _de_tai(tmp_path)
    (d / "G0_checkpoint.json").write_text(json.dumps({"topic": "tuân thủ thuốc hạ áp"}), encoding="utf-8",
                                          newline="\n")
    monkeypatch.setattr(RG5, "BASE", tmp_path)
    monkeypatch.setattr(RG5.GC, "ledger_approved", lambda g, *a, **k: g == "G4")
    monkeypatch.setattr(RG5.GC, "resolve_design_code", lambda *a, **k: ("cross_sectional", None))
    monkeypatch.setattr(sys, "argv", ["run_g5_auto.py", "--study", STUDY])
    assert RG5.main() == GC.EXIT_BLOCKED
    assert not (d / f"G5_REDCap_dictionary_{STUDY}.csv").exists()


def test_g5_auto_11_bo_mau_chung_va_ma_tran(tmp_path):
    d = _de_tai(tmp_path)
    _ghi_bo_bien(d)
    td = d / f"G5_REDCap_dictionary_{STUDY}.csv"
    td.write_text((d / MT.TEP_BO_BIEN).read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
    meta = MT.doc_meta(d)
    c = G5Q._tieu_chi_tu_dien_ma_tran(STUDY, d, {"specialty": "generic"}, td, meta)
    assert c["status"] == "REVIEW" and "BỘ MẪU CHUNG" in c["evidence"]
    _ghi_ma_tran(d)
    assert G5Q._tieu_chi_tu_dien_ma_tran(STUDY, d, {"specialty": "bo_bien_rieng"}, td, meta)["status"] == "PASS"


def test_g5_auto_12_phieu_hoi_dong(tmp_path):
    d = _de_tai(tmp_path)
    _ghi_bo_bien(d)
    _ghi_ma_tran(d)
    meta = MT.doc_meta(d)
    # «G2_A3_ETHICS» trong tên tệp KHÔNG được tính là câu «A3»
    (d / f"G2_A3_ETHICS_PACKAGE_{STUDY}.md").write_text("Phụ lục phiếu: A1. tuổi; B1) số thuốc; Câu B3: …; "
                                                       "TT1 …\n", encoding="utf-8", newline="\n")
    c = G5Q._tieu_chi_phieu_hoi_dong(STUDY, d, meta)
    assert c["status"] == "REVIEW" and "C1" in c["evidence"]
    (d / "phieu_nop.md").write_text("| C1 | Gia đình có nhắc dùng thuốc không? |\n", encoding="utf-8", newline="\n")
    meta["gate_params"]["G2"] = {"phieu_nop_hoi_dong": ["phieu_nop.md"]}
    assert G5Q._tieu_chi_phieu_hoi_dong(STUDY, d, meta)["status"] == "PASS"


# ───────────────────────────── cầu nối SPSS/R — E4 ─────────────────────────────
def test_e4_chan_tu_dien_giu_cho_va_bo_mau(tmp_path):
    d = _de_tai(tmp_path)
    td = d / f"G5_REDCap_dictionary_{STUDY}.csv"
    rows, _ = RG5.build_redcap_rows("cross_sectional", "tuân thủ thuốc hạ áp")
    RG5.generate_csv(STUDY, d, rows)
    (d / "G5_checkpoint.json").write_text(json.dumps({"specialty": "generic"}), encoding="utf-8", newline="\n")
    loi = MT.kiem_noi_dung_xuat(d, STUDY, td, [r[0] for r in rows])
    toan = " ".join(loi)
    assert "giữ chỗ" in toan and "BỘ MẪU CHUNG" in toan and "chưa có _bo-bien-rieng.csv" in toan


def test_e4_cho_qua_khi_dung_va_chan_khi_thieu_cot(tmp_path):
    d = _de_tai(tmp_path)
    _ghi_bo_bien(d)
    _ghi_ma_tran(d)
    td = d / f"G5_REDCap_dictionary_{STUDY}.csv"
    td.write_text((d / MT.TEP_BO_BIEN).read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
    cot = [b[0] for b in BIEN_DUNG]
    assert MT.kiem_noi_dung_xuat(d, STUDY, td, cot) == []
    loi = MT.kiem_noi_dung_xuat(d, STUDY, td, [c for c in cot if c != "ho_tro_gd"])
    assert any("ho_tro_gd" in x for x in loi)


def test_e4_cau_noi_spss_tu_choi(tmp_path):
    import cau_noi_spss as S  # noqa: PLC0415

    d = _de_tai(tmp_path)
    _ghi_bo_bien(d)  # có bộ biến nhưng CHƯA có ma trận
    td = d / f"G5_REDCap_dictionary_{STUDY}.csv"
    td.write_text((d / MT.TEP_BO_BIEN).read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
    ke = [{"cot": b[0], "bo": False} for b in BIEN_DUNG]
    with pytest.raises(S.TuChoi, match="E4"):
        S.kiem_noi_dung_bien(d, STUDY, td, ke)
    _ghi_ma_tran(d)
    S.kiem_noi_dung_bien(d, STUDY, td, ke)  # không ném


# ───────────────────────────── BHYT ─────────────────────────────
@pytest.mark.parametrize("ten,la_pii", [("bhyt", False), ("co_bhyt", False), ("cobhyt", False), ("loai_bhyt", False),
                                        ("so_the_bhyt", True), ("ma_bhyt", True), ("the_bhyt", True),
                                        ("bhyt_number", True), ("sothebhyt", True), ("ho_ten", True)])
def test_bhyt_tinh_trang_khong_phai_dinh_danh(ten, la_pii):
    assert G5Q._la_ten_bien_dinh_danh(ten) is la_pii
    assert bool(RDI._header_issue(ten)) is la_pii


def test_so_the_bhyt_trong_o_du_lieu_van_bi_bat():
    assert RDI.VALUE_PATTERNS["bhyt_the"].search("thẻ DN4797915123456 còn hạn")
    assert not RDI.VALUE_PATTERNS["bhyt_the"].search("mã ZZSIM-001")


# ───────────────────────────── quần thể hai chiều ─────────────────────────────
def test_quan_the_mat_nguong_la_lech_mem():
    nguon = [{"cong": "G0", "noi": "G0", "gia_tri": "Người bệnh ≥18 tuổi THA điều trị ngoại trú ≥3 tháng"},
             {"cong": "G1", "noi": "G1", "gia_tri": "Người bệnh ≥18 tuổi THA điều trị ngoại trú"}]
    k = NQ._so_quan_the_hai_chieu(nguon)
    assert k["muc"] == NQ.MUC_LECH_MEM and "≥3 tháng" in k["ghi_chu"]


def test_quan_the_con_so_tron_khong_phai_nguong():
    nguon = [{"cong": "G0", "noi": "G0", "gia_tri": "Người bệnh khám tại Bệnh viện 175, khoa C1, theo mục 4.3"},
             {"cong": "G2", "noi": "G2", "gia_tri": "Người bệnh khám tại khoa khám bệnh"}]
    assert NQ._so_quan_the_hai_chieu(nguon)["muc"] != NQ.MUC_LECH_MEM


def test_quan_the_ban_sau_day_du_hon_van_khop():
    nguon = [{"cong": "G0", "noi": "G0", "gia_tri": "Người bệnh ≥18 tuổi THA"},
             {"cong": "G2", "noi": "G2", "gia_tri": "Người bệnh ≥18 tuổi THA đang dùng thuốc, đồng ý tham gia"}]
    assert NQ._so_quan_the_hai_chieu(nguon)["muc"] == NQ.MUC_KHOP


# ───────────────────────────── hội đồng G3-T2 ─────────────────────────────
def test_hoi_dong_g3_t2_bao_loi_ma_tran(tmp_path):
    d = _de_tai(tmp_path)
    _ghi_bo_bien(d)
    assert any("ma trận mục tiêu–biến" in x for x in HD._kiem_bo_bien_so(d, STUDY))
    _ghi_ma_tran(d)
    assert HD._kiem_bo_bien_so(d, STUDY) == []


def test_phieu_hoi_dong_ten_tep_khong_phai_ma_cau(tmp_path):
    """«G2_A3_ETHICS_PACKAGE» (tên tệp/khối) không được tính là câu «A3» của phiếu."""
    d = _de_tai(tmp_path)
    _ghi_bo_bien(d)
    _ghi_ma_tran(d, [*MA_TRAN_DUNG, ("2", "khác", "mo_ta", "tuoi", "lien_tuc", "A3", "phiếu", "§3")])
    (d / f"G2_A3_ETHICS_PACKAGE_{STUDY}.md").write_text(
        "Hồ sơ G2_A3_ETHICS_PACKAGE: A1. … B1) … Câu B3: … TT1 … | C1 |\n", encoding="utf-8", newline="\n")
    kq = MT.kiem_phieu_hoi_dong(d, STUDY)
    assert kq["trang_thai"] == "CHUA_DAT" and "A3" in kq["loi"][0]
