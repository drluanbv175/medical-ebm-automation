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


def _so_cai_gia(d, monkeypatch, ban_ghi):
    """Sổ cái tổng hợp + bản ghi «có thẩm quyền» giả (thay xác minh chữ ký) — ban_ghi=None ⇒ bất thường/không có."""
    (d / "approval_ledger.json").write_text(json.dumps([{"gate_id": "G4"}]), encoding="utf-8", newline="\n")
    monkeypatch.setattr(GC, "_latest_authoritative_record",
                        lambda so, g, study, root: (ban_ghi if g == "G4" else None))


def test_g3_auto_19_khong_ha_cap_de_tai_da_ky_g4_truoc_moc(tmp_path, monkeypatch):
    """Luật mới không hạ cấp quyết định đã ký: G4 ký (bản ghi đang hiệu lực) trước mốc ⇒ PASS kèm «MIỄN TRỪ … VẪN
    THIẾU»."""
    d = _de_tai(tmp_path)
    _so_cai_gia(d, monkeypatch, {"decision": "APPROVED", "timestamp_utc": "2026-10-17T03:00:00+00:00"})
    c = G3Q._tieu_chi_ma_tran(STUDY, d, MT.doc_meta(d))
    assert c["status"] == "PASS" and "MIỄN TRỪ" in c["evidence"] and "VẪN THIẾU" in c["evidence"]
    # bản ghi không xác minh được (bất thường) ⇒ không miễn trừ (fail-closed)
    _so_cai_gia(d, monkeypatch, None)
    assert G3Q._tieu_chi_ma_tran(STUDY, d, MT.doc_meta(d))["status"] == "REVIEW"


@pytest.mark.parametrize("ban_ghi", [
    {"decision": "APPROVED", "timestamp_utc": "2026-11-20T03:00:00+00:00"},  # ký sau mốc
    {"decision": "REJECTED", "timestamp_utc": "2026-10-17T03:00:00+00:00"},  # đã thu hồi
    {"decision": "APPROVED", "timestamp_utc": ""},                            # không có thời điểm
    {"decision": "APPROVED", "timestamp_utc": "2026-10-17"},                  # không có múi giờ
    {"decision": "APPROVED", "timestamp_utc": "2026-10-17T03:00:00+00:00", "is_synthetic": True},
])
def test_mien_tru_fail_closed(tmp_path, monkeypatch, ban_ghi):
    """Thẩm định #268: miễn trừ chỉ khi bản ghi ĐANG HIỆU LỰC là APPROVED, không synthetic, thời điểm hợp lệ trước
    mốc."""
    d = _de_tai(tmp_path)
    _so_cai_gia(d, monkeypatch, ban_ghi)
    assert MT.da_ky_truoc_moc(d, STUDY)[0] is False


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


# ───────────────────────────── khung đề tài: G0 đã chốt → G1 · SAP · G10 ─────────────────────────────
import g0_quality_gate as G0Q  # noqa: E402
import g1_quality_gate as G1Q  # noqa: E402
import khung_de_tai as KD  # noqa: E402
import run_g4_auto as RG4  # noqa: E402
import run_g10_assemble as RG10  # noqa: E402

G0_CHOT = {"pico_confirmed": True, "population": "Người bệnh ≥18 tuổi THA điều trị ngoại trú ≥3 tháng",
           "intervention": "Không can thiệp — phơi nhiễm là các yếu tố liên quan",
           "comparison": "Không có nhóm so sánh — mô tả", "outcomes": ["Tỷ lệ tuân thủ", "Yếu tố liên quan"],
           "primary_outcome": "Tỷ lệ tuân thủ", "primary_outcome_measure": "Bộ câu hỏi 8 mục",
           "primary_outcome_timepoint": "Khi phỏng vấn"}


def test_khung_ke_thua_g0_chi_khi_da_chot_va_g1_thang():
    meta = {"gate_params": {"G0": dict(G0_CHOT), "G1": {}}}
    assert KD.gia_tri(meta, "population") == (G0_CHOT["population"], "G0")
    kc = KD.ket_cuc_chinh(meta)
    assert (kc["name"], kc["measure"], kc["timepoint"], kc["type"]) == ("Tỷ lệ tuân thủ", "Bộ câu hỏi 8 mục",
                                                                        "Khi phỏng vấn", None)
    assert KD.gia_tri(meta, "secondary_outcomes")[0] == ["Yếu tố liên quan"]
    meta["gate_params"]["G1"]["population"] = "Bản G1"
    assert KD.gia_tri(meta, "population") == ("Bản G1", "G1")
    meta["gate_params"]["G0"]["pico_confirmed"] = False
    assert KD.gia_tri(meta, "comparator") == (None, None), "G0 chưa chốt ⇒ không đem nháp đi xa hơn cổng"


def test_a2_g1_dien_san_tu_g0_co_nhan_nguon():
    meta = {"gate_params": {"G0": dict(G0_CHOT), "G1": {}}}
    a2 = G1Q.build_protocol_core(study=STUDY, topic="t", design={"primary": "Cắt ngang", "internal_code":
                                 "cross_sectional"}, meta=meta, generated_at="2026-11-15T07:00:00+07:00")
    dong = next(x for x in a2.splitlines() if x.startswith("- Quần thể đích/nguồn:"))
    assert G0_CHOT["population"] in dong and "kế thừa G0 đã chốt" in dong
    assert "- Định nghĩa/công cụ/đơn vị đo: Bộ câu hỏi 8 mục" in a2


def test_dau_van_tay_g1_khong_doi_khi_g1_tu_ghi_du():
    """Đề tài đã tự ghi đủ ở G1 (C1a, btm) ⇒ dấu vân tay G1 giữ nguyên — không hạ cấp xác nhận cũ."""
    import cong_song as CS  # noqa: PLC0415

    g1 = {"population": "P", "intervention_or_exposure": "I", "comparator": "C", "secondary_outcomes": ["S"],
          "research_question": "RQ", "primary_outcome": {"name": "O", "measure": "M", "timepoint": "T", "type": "x"}}
    meta = {"design_code": "cross_sectional", "gate_params": {"G0": dict(G0_CHOT), "G1": g1}}
    design = {"internal_code": "cross_sectional"}
    assert KD.ke_thua_dang_dung(meta) == {}
    assert G1Q.dau_van_tay_g1(meta, design) == CS.dau_van_tay(g1, "cross_sectional", "cross_sectional")
    del meta["gate_params"]["G1"]["population"]
    assert G1Q.dau_van_tay_g1(meta, design) != CS.dau_van_tay(meta["gate_params"]["G1"], "cross_sectional",
                                                             "cross_sectional"), "kế thừa ⇒ vào dấu vân tay"


def test_sap_dien_san_tu_khung_va_ma_tran(tmp_path):
    d = _de_tai(tmp_path)
    _ghi_bo_bien(d)
    _ghi_ma_tran(d)
    meta = MT.doc_meta(d)
    meta["gate_params"]["G1"].update({"inclusion_criteria": ["≥18 tuổi", "Đồng ý"], "exclusion_criteria": ["Có thai"]})
    khung = RG4._khung_sap(d, meta)
    sap = RG4._dien_khung("\n".join([
        "- **Tiêu chí nhận:** [CẦN BÁC SĨ ĐIỀN — từ đề cương]  ",
        "- **Kết cục chính:** [CẦN BÁC SĨ ĐIỀN — ví dụ: tỷ lệ nhập viện tim mạch trong 12 tháng]  ",
        "- **Biến độc lập đưa vào:** [CẦN BÁC SĨ LIỆT KÊ — kèm lý do lâm sàng / DAG]  "]), khung, "cross_sectional")
    assert "≥18 tuổi; Đồng ý" in sap
    assert "Tỷ lệ tuân thủ dùng thuốc hạ áp" in sap and "biến `tuan_thu`" in sap
    assert "`so_lan_ngay` (số lần dùng thuốc/ngày)" in sap and "[CẦN THỐNG KÊ VIÊN/PI]" in sap, \
        "biến lấy từ ma trận; lý do lâm sàng/DAG vẫn là việc của người"


def test_g10_ma_tran_truy_xuat_dung_ma_tran_khi_dat(tmp_path):
    d = _de_tai(tmp_path)
    _ghi_bo_bien(d)
    _ghi_ma_tran(d)
    meta = {**MT.doc_meta(d), "objectives": MUC_TIEU, "_g10": {"out_dir": str(d)}}
    txt = RG10.build_traceability_matrix({}, meta)
    dong2 = next(x for x in txt.splitlines() if x.startswith("| Mục tiêu cụ thể 2"))
    assert "`ho_tro_gd` (nhi_phan, yeu_to)" in dong2 and RG10.TAG_MANUAL not in dong2


# ───────────────────────────── G0-AUTO-08 ─────────────────────────────
def _g0(population, outcome, base_query, *, query_en=None, intervention="Không can thiệp — mô tả"):
    meta = {"gate_params": {"G0": {"pico_confirmed": True, "population": population, "intervention": intervention,
                                   "primary_outcome": outcome}}}
    if query_en:
        meta["query_en"] = query_en
    return G0Q._tieu_chi_phu_pico({"base_query": base_query}, meta, {"query": base_query}, {})


def test_g0_auto_08_bat_truy_van_mat_khai_niem_ket_cuc():
    """Lỗi đo được: «tuân thủ dùng thuốc hạ áp…» ⇒ `hypertension treatment` mà G0 vẫn PASS."""
    c = _g0("Người bệnh tăng huyết áp", "Tỷ lệ tuân thủ dùng thuốc hạ áp", "hypertension treatment")
    assert c["status"] == "REVIEW" and "PubMed" in c["evidence"] and "ClinicalTrials.gov" in c["evidence"]


def test_g0_auto_08_nhan_cum_cat_cut_va_bo_thuat_ngu_chung():
    c = _g0("Người bệnh tăng huyết áp đang điều trị", "Tỷ lệ tuân thủ dùng thuốc",
            '"Hypertension"[Mesh] AND adheren*[tiab]', query_en='"Hypertension"[Mesh] AND adheren*[tiab]')
    assert c["status"] == "PASS", c["evidence"]
    # Quần thể CHỈ có thuật ngữ chung («điều trị» → treatment) ⇒ không đòi truy vấn chứa «treatment» (báo nhầm C1a).
    c2 = _g0("Người bệnh đang điều trị ngoại trú", "Tỷ lệ tuân thủ dùng thuốc", "adherence[tiab]",
             query_en="adherence[tiab]")
    assert c2["status"] == "PASS" and "vắng" not in c2["evidence"], c2["evidence"]


def test_g0_auto_08_khai_niem_ngoai_tu_dien():
    may = _g0("Người bệnh khoa khám bệnh", "Mức hài lòng", "satisfaction")
    assert may["status"] == "REVIEW" and "MÁY tự dịch" in may["evidence"]
    pi = _g0("Người bệnh khoa khám bệnh", "Mức hài lòng", "satisf*", query_en="satisf*")
    assert pi["status"] == "PASS" and "PI tự viết" in pi["evidence"]


# ───────────────────────────── G6 lấy vai trò biến từ ma trận/SAP ─────────────────────────────
import run_g6_auto as RG6  # noqa: E402


def _ten_goc(bien):
    return {b[0].lower(): b[0] for b in bien}


def test_g6_vai_tro_theo_ma_tran_thay_bien_do(tmp_path):
    """Đo được: dò từ khoá chọn `primary_outcome`/`exposure` (không tồn tại), hiệp biến chỉ tuổi/giới."""
    d = _de_tai(tmp_path)
    _ghi_bo_bien(d)
    _ghi_ma_tran(d)
    v = {"outcome": "primary_outcome", "exposure": "exposure", "covariates": ["tuoi"], "detection_log": []}
    assert RG6.ap_vai_tro_ma_tran(v, d, STUDY, _ten_goc(BIEN_DUNG)) is None
    assert v["outcome"] == "tuan_thu"
    assert v["exposure"] == "tuoi" and "so_lan_ngay" in v["covariates"] and "ho_tro_gd" in v["covariates"]


def test_g6_khong_ma_tran_khong_doan_thi_dung(tmp_path):
    d = _de_tai(tmp_path)
    _ghi_bo_bien(d)
    v = {"outcome": "primary_outcome", "exposure": "exposure", "covariates": [], "detection_log": []}
    ly_do = RG6.ap_vai_tro_ma_tran(v, d, STUDY, _ten_goc(BIEN_DUNG))
    assert ly_do and "không đoán" in ly_do and "primary_outcome" in ly_do


def test_g6_sap_da_khoa_thang_ma_tran_khi_lech(tmp_path):
    d = _de_tai(tmp_path)
    _ghi_bo_bien(d)
    _ghi_ma_tran(d)
    v = {"outcome": "tt1", "exposure": "tuoi", "covariates": [], "detection_log": ["✅ Kết cục chính THEO SAP §2: tt1"]}
    assert RG6.ap_vai_tro_ma_tran(v, d, STUDY, _ten_goc(BIEN_DUNG)) is None
    assert v["outcome"] == "tt1" and any("LỆCH ma trận" in x for x in v["detection_log"])


# ───────────────────────────── sửa theo thẩm định #268 ─────────────────────────────
@pytest.mark.parametrize("loai,ma", [
    ("Thứ hạng (ordinal) 5 mức Likert — GIỮ nguyên thứ hạng trong mô hình chính; ngưỡng nhị phân thứ cấp", "thu_tu"),
    ("Liên tục (điểm 0–100); phân tích phụ nhị phân", "lien_tuc"),
    ("Nhị phân (tuân thủ/không)", "nhi_phan"),
    ("nhị phân hoặc liên tục", None),
])
def test_kieu_ket_cuc_doc_menh_de_chinh(loai, ma):
    meta = {"gate_params": {"G1": {"primary_outcome": {"name": "x", "type": loai}}}}
    assert MT.kieu_ket_cuc_g1(meta) == ma


def test_tach_yeu_to_khong_lay_ten_co_so_va_tien_to_mt():
    assert MT.tach_yeu_to("MT1 (mô tả): Xác định mức hài lòng tại Trung tâm Khám bệnh, Điều trị theo yêu cầu C1, "
                          "Bệnh viện Quân y 175") == []
    assert MT.tach_yeu_to("MT2 (phân tích): Đánh giá một số yếu tố liên quan đến hài lòng: tuổi, giới tại khoa A") \
        == ["tuổi", "giới"]


def test_khop_khai_niem_hai_chieu_khong_xanh_gia():
    assert not MT.khop_khai_niem("số loại thuốc", "thuốc")
    assert not MT.khop_khai_niem("tuổi", MUC_TIEU[1]), "khái niệm là nguyên câu mục tiêu không được phủ mọi yếu tố"
    assert MT.khop_khai_niem("số lần dùng thuốc/ngày", "Số lần dùng thuốc mỗi ngày")


def test_ma_tran_dinh_tinh_khong_doi_ket_cuc_chinh(tmp_path):
    d = _de_tai(tmp_path)
    m = MT.doc_meta(d)
    m["design_code"] = "qualitative"
    m["gate_params"]["G1"]["objectives"] = ["Khám phá trải nghiệm chờ khám của người bệnh"]
    (d / "study_meta.json").write_text(json.dumps(m, ensure_ascii=False), encoding="utf-8", newline="\n")
    _ghi_bo_bien(d, [("record_id", "text", "Mã", "", "", ""), ("ban_go_bang", "notes", "Bản gỡ băng", "", "", "")])
    _ghi_ma_tran(d, [("1", "trải nghiệm chờ khám", "mo_ta", "ban_go_bang", "van_ban", "", "phỏng vấn sâu", "§4")])
    assert MT.kiem(d, STUDY)["trang_thai"] == MT.TRANG_THAI_DAT


def _xuat_dung(tmp_path):
    d = _de_tai(tmp_path)
    _ghi_bo_bien(d)
    _ghi_ma_tran(d)
    td = d / f"G5_REDCap_dictionary_{STUDY}.csv"
    td.write_text((d / MT.TEP_BO_BIEN).read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
    return d, td, [b[0] for b in BIEN_DUNG]


def test_e4_tu_dien_lech_bo_bien_bi_chan(tmp_path):
    """Đột biến M1 của người duyệt sống sót — ghim: từ điển G5 ≠ bộ biến riêng ⇒ E4 từ chối."""
    d, td, cot = _xuat_dung(tmp_path)
    td.write_text(td.read_text(encoding="utf-8") + "bien_la,phieu,,text,Biến lạ\n", encoding="utf-8", newline="\n")
    assert any("lệch bộ biến" in x for x in MT.kiem_noi_dung_xuat(d, STUDY, td, [*cot, "bien_la"]))


def test_e4_bien_van_ban_va_checkbox_khong_bi_chan_oan(tmp_path):
    """M6 (biến `van_ban` không vào .sav) + checkbox REDCap xuất thành `<bien>___<mã>`."""
    d = _de_tai(tmp_path)
    bien = [*BIEN_DUNG, ("y_kien", "notes", "Ý kiến đóng góp (văn bản tự do)", "", "", "")]
    _ghi_bo_bien(d, bien)
    _ghi_ma_tran(d, [*MA_TRAN_DUNG, ("2", "ý kiến đóng góp", "mo_ta", "y_kien", "van_ban", "", "phiếu", "")])
    td = d / f"G5_REDCap_dictionary_{STUDY}.csv"
    td.write_text((d / MT.TEP_BO_BIEN).read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
    # .sav bỏ biến notes (`y_kien`) và tách checkbox thành `ho_tro_gd___1` — không phải «thiếu biến».
    cot = [b[0] for b in BIEN_DUNG if b[0] != "ho_tro_gd"] + ["ho_tro_gd___1"]
    assert MT.kiem_noi_dung_xuat(d, STUDY, td, cot) == []


def test_quan_the_bo_tu_khong_nguong_la_can_xem():
    """Đột biến M5 (quay về phủ đối xứng) sống sót — ghim chiều cổng khi mất từ mà không mất ngưỡng số."""
    nguon = [{"cong": "G0", "noi": "G0",
              "gia_tri": "Người bệnh THA điều trị tại phòng khám nội tim mạch bệnh viện tỉnh"},
             {"cong": "G1", "noi": "G1", "gia_tri": "Người bệnh THA"}]
    assert NQ._so_quan_the_hai_chieu(nguon)["muc"] == NQ.MUC_CAN_XEM


def test_quan_the_ngay_thang_khong_phai_nguong():
    nguon = [{"cong": "G0", "noi": "G0", "gia_tri": "Người bệnh khám từ 01/2026 đến 06/2026"},
             {"cong": "G1", "noi": "G1", "gia_tri": "Người bệnh khám từ tháng 1/2026 đến tháng 6/2026"}]
    assert NQ._so_quan_the_hai_chieu(nguon)["muc"] != NQ.MUC_LECH_MEM


def test_phieu_ma_c1_khong_khop_c1a(tmp_path):
    d = _de_tai(tmp_path)
    _ghi_bo_bien(d)
    _ghi_ma_tran(d, [("1", "Tỷ lệ tuân thủ dùng thuốc hạ áp", "ket_cuc_chinh", "tuan_thu", "nhi_phan", "C1", "x",
                      "§4")])
    (d / f"G2_A3_ETHICS_PACKAGE_{STUDY}.md").write_text("Khoa C1a — câu hỏi khác\n", encoding="utf-8", newline="\n")
    assert MT.kiem_phieu_hoi_dong(d, STUDY)["trang_thai"] == "CHUA_DAT"


def test_g6_dinh_tinh_va_mo_ta_thuan_khong_doi_phoi_nhiem(tmp_path):
    d = _de_tai(tmp_path)
    v = {"outcome": "tuan_thu", "exposure": "exposure", "covariates": [], "detection_log": []}
    assert RG6.ap_vai_tro_ma_tran(dict(v), d, STUDY, _ten_goc(BIEN_DUNG), "qualitative") is None
    _ghi_bo_bien(d)
    _ghi_ma_tran(d, [MA_TRAN_DUNG[0]])  # chỉ kết cục chính — mô tả thuần
    m = MT.doc_meta(d)
    m["gate_params"]["G1"]["objectives"] = ["Xác định tỷ lệ tuân thủ dùng thuốc hạ áp"]
    (d / "study_meta.json").write_text(json.dumps(m, ensure_ascii=False), encoding="utf-8", newline="\n")
    assert RG6.ap_vai_tro_ma_tran(dict(v), d, STUDY, _ten_goc(BIEN_DUNG), "cross_sectional") is None


def test_g6_ma_tran_dat_khong_giu_phoi_nhiem_do_tu_khoa(tmp_path):
    """Đo của người duyệt: `job_group` (dò từ khoá, có trong từ điển, KHÔNG có trong ma trận) lọt vào mô hình."""
    d = _de_tai(tmp_path)
    _ghi_bo_bien(d, [*BIEN_DUNG, ("job_group", "radio", "Nhóm nghề", "1, A | 2, B", "", "")])
    _ghi_ma_tran(d)
    v = {"outcome": "tuan_thu", "exposure": "job_group", "covariates": [], "detection_log": []}
    tg = _ten_goc([*BIEN_DUNG, ("job_group",)])
    assert RG6.ap_vai_tro_ma_tran(v, d, STUDY, tg, "cross_sectional") is None
    assert v["exposure"] != "job_group" and v["exposure"] == "tuoi"


def test_dau_van_tay_g1_xac_nhan_truoc_moc_giu_cach_tinh_cu():
    import cong_song as CS  # noqa: PLC0415

    g1 = {"population": "P", "primary_outcome": {"name": "O", "measure": "M", "timepoint": "T", "type": "x"},
          "reviewed_at": "2026-10-20T09:00:00+07:00"}   # thiếu intervention/comparator ⇒ sẽ kế thừa G0
    meta = {"design_code": "cross_sectional", "gate_params": {"G0": dict(G0_CHOT), "G1": g1}}
    cu = CS.dau_van_tay({k: v for k, v in g1.items() if k not in G1Q._KHOA_XAC_NHAN_G1}, "cross_sectional",
                        "cross_sectional")
    assert G1Q.dau_van_tay_g1(meta, {"internal_code": "cross_sectional"}) == cu
    g1["reviewed_at"] = "2026-11-20T09:00:00+07:00"
    assert G1Q.dau_van_tay_g1(meta, {"internal_code": "cross_sectional"}) != cu


def test_cot_bhyt_chua_ma_so_van_bi_chan(tmp_path):
    p = tmp_path / "d.csv"
    p.write_text("record_id,bhyt\nZ1,1234567890\nZ2,1\n", encoding="utf-8", newline="\n")
    loai = {(i["type"], i["row"]) for i in RDI._scan_csv(p)["issues"]}
    assert ("value_pii:ma_bhyt_bhxh", 1) in loai and not any(r == 2 for t, r in loai if t.startswith("value_pii"))
