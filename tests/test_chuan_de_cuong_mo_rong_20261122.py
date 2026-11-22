"""Nâng chuẩn đề cương nộp (22/11/2026, bác sĩ: «các chuẩn mực tiêu chuẩn của đề tài nghiên cứu, của đề cương cũng
đã có nền, hãy tiếp tục nâng cấp»).

Trước đó K17 MIỄN CHẶN SPIRIT 2025, PRISMA-P 2015, STARD 2015, TRIPOD+AI 2024 («bộ sinh thiếu N mục») và GRAMMS, SQUIRE,
CHEERS, CARE («chưa có văn bản để đo») qua `CHUAN_CHO_BO_SINH` — tức một sổ nợ: đề cương báo «đạt» khi còn thiếu mục
chuẩn. Đo trên đề cương nộp giả lập 22/11: RCT thiếu 9 mục SPIRIT, tổng quan 8 PRISMA-P, chẩn đoán 7 STARD, dự báo 11
TRIPOD+AI. Các test dưới khoá:
  - bộ sinh viết ĐỦ mục từ quyết định đã chốt (G1/G3/G4/G7/G9 + lời khai trong study_meta); vắng lời khai ⇒ ô «………»
    và K17 vẫn báo thiếu đúng mục (không câu nào dựng thay quyết định của người);
  - K17 không còn tập miễn chặn; chuẩn chưa có văn bản kiểm chứng (SQUIRE, CARE, TREND) ⇒ ⚪ «chưa đo được», chuẩn cơ
    sở chưa đo ⇒ không báo đạt;
  - TREND 2004 đối chiếu Bảng 1 bản gốc; tiêu chí CHEERS 12/13/22 sửa có căn cứ;
  - phần mở rộng CONSORT cho thử nghiệm cụm (Campbell 2012) và không kém hơn (Piaggio 2012) áp theo thiết kế.
"""
from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import kiem_chuan_de_cuong_theo_muc as KCM  # noqa: E402
import run_g4_auto as G4  # noqa: E402
import sinh_de_cuong_nop_hoi_dong as SDC  # noqa: E402
import tieu_chi_chuan_de_cuong as TC  # noqa: E402
from test_sinh_de_cuong_nop_hoi_dong_20261116 import MA, SAP, _de_tai  # noqa: E402

CHAM = SDC.CHAM


def _gop(dich: dict, them: dict) -> None:
    """Ghi đè khoá; giá trị None ⇒ XOÁ khoá (đề tài thử «vắng lời khai» dựng từ fixture đầy đủ)."""
    for k, v in them.items():
        if v is None:
            dich.pop(k, None)
        else:
            dich[k] = v


def _sua(d: Path, g1: dict | None = None, g3: dict | None = None, g3cp: dict | None = None, adm: dict | None = None,
         sap_them: str = "", bien: list | None = None, g7: dict | None = None, g9: dict | None = None,
         sap_goc: bool = False, **meta) -> None:
    p = d / "study_meta.json"
    m = json.loads(p.read_text(encoding="utf-8"))
    _gop(m["gate_params"]["G1"], g1 or {})
    _gop(m["gate_params"]["G3"], g3 or {})
    _gop(m["gate_params"].setdefault("G7", {}), g7 or {})
    _gop(m["administrative"], adm or {})
    _gop(m, meta)
    p.write_text(json.dumps(m, ensure_ascii=False), encoding="utf-8", newline="\n")
    if sap_goc:  # SAP mẫu gốc (không §13–§15 của fixture đầy đủ)
        (d / f"G4_A5_SAP_FINAL_{MA}.md").write_text(SAP, encoding="utf-8", newline="\n")
    if g3cp:
        q = d / "G3_checkpoint.json"
        c = json.loads(q.read_text(encoding="utf-8"))
        c.update(g3cp)
        q.write_text(json.dumps(c), encoding="utf-8", newline="\n")
    if sap_them:
        (d / f"G4_A5_SAP_FINAL_{MA}.md").write_text(SAP.replace("\n---\n", sap_them + "\n---\n"), encoding="utf-8",
                                                     newline="\n")
    if bien:
        q = d / "_bo-bien-rieng.csv"
        with q.open(encoding="utf-8", newline="") as fh:
            hang = list(csv.DictReader(fh))
        mau = dict(hang[0])
        for ten, nhan in bien:
            hang.append({**mau, "Variable / Field Name": ten, "Field Label": nhan})
        with q.open("w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(hang[0]), lineterminator="\n")
            w.writeheader()
            w.writerows(hang)
    if g9:
        q = d / "G9_PUBLICATION_READINESS.json"
        c = json.loads(q.read_text(encoding="utf-8"))
        c.update(g9)
        q.write_text(json.dumps(c, ensure_ascii=False), encoding="utf-8", newline="\n")


def _van(tmp_path: Path, tk: str, **sua) -> str:
    d = _de_tai(tmp_path, tk)
    _sua(d, **sua)
    return SDC.dung_de_cuong(SDC.Nguon(d, MA))


def _ket_qua(van: str, tk: str) -> dict:
    return {(r.chuan, r.ma): r for r in KCM.doi_chieu(van, tk)["ket_qua"]}


def _thieu(van: str, tk: str, chuan: str) -> set:
    return {ma for (c, ma), r in _ket_qua(van, tk).items() if c == chuan and r.trang_thai == "thieu"}


# ═════════════════════════════════════════════ SPIRIT 2025 (RCT)
_SAP_TON_HAI = """
### §15 TỔN HẠI

- **Định nghĩa tổn hại:** biến cố bất lợi liên quan can thiệp (phàn nàn, lo âu, cơn tăng huyết áp)
"""
_KHAI_RCT = dict(
    g1={"benefit_risk_rationale": "Can thiệp nguy cơ tối thiểu, lợi ích tiềm năng tăng tuân thủ",
        "monitoring_plan": "Giám sát việc thực hiện thử nghiệm định kỳ 3 tháng: người không tham gia tuyển đối chiếu "
                           "10% phiếu với hồ sơ gốc"},
    adm={"dia_chi_don_vi_chu_tri": "Phòng Nghiên cứu khoa học, bệnh viện chủ trì, TP. Hồ Chí Minh"},
    sap_them=_SAP_TON_HAI,
    ppi_plan="Hai người bệnh góp ý nội dung tin nhắn trước khi tuyển; kết quả gửi người tham gia bằng tờ tóm tắt",
    protocol_amendment_plan="Mọi sửa đổi quan trọng của đề cương được trình Hội đồng Đạo đức chấp thuận trước khi áp "
                            "dụng và cập nhật trên ClinicalTrials.gov",
    blinding_how="Tách riêng người gửi tin nhắn và người đo huyết áp; phiếu đo không ghi nhánh",
)
_MUC_SPIRIT_MOI = {"3b", "8", "9a", "10", "11", "12", "24b", "29", "31"}


def test_rct_khai_du_thi_chin_muc_spirit_dat(tmp_path):
    van = _van(tmp_path, "rct", **_KHAI_RCT)
    assert not _thieu(van, "rct", "SPIRIT 2025") & _MUC_SPIRIT_MOI
    assert "| Địa chỉ liên hệ của đơn vị chủ trì | Phòng Nghiên cứu khoa học" in van
    assert "- Khung so sánh: thử nghiệm vượt trội (superiority)." in van
    assert "Bên cạnh mục tiêu trên, nghiên cứu mô tả tác hại (biến cố bất lợi)" in van
    assert "- Cách làm mù: Tách riêng người gửi tin nhắn" in van
    assert "- Kế hoạch giám sát: Giám sát việc thực hiện thử nghiệm định kỳ 3 tháng" in van
    # thử nghiệm: kế hoạch giám sát in ở mục quản lý dữ liệu, không lặp ở mục công cụ
    assert "Giám sát chất lượng: Giám sát việc thực hiện" not in van


_VANG_RCT = dict(g1={"benefit_risk_rationale": None, "monitoring_plan": None}, g3={"hypothesis_type": ""},
                 adm={"dia_chi_don_vi_chu_tri": None}, sap_goc=True, ppi_plan=None, protocol_amendment_plan=None,
                 blinding_how=None)


def test_rct_vang_khai_bao_thi_o_trong_va_k17_bao_thieu(tmp_path):
    van = _van(tmp_path, "rct", **_VANG_RCT)
    for nhan in ("| Địa chỉ liên hệ của đơn vị chủ trì |", "Cân nhắc lợi ích – nguy cơ của can thiệp:",
                 "- Khung so sánh:", "- Cách làm mù:", "- Kế hoạch giám sát:",
                 "- Sự tham gia của người bệnh và công chúng:", "- Sửa đổi đề cương:"):
        dong = next(d for d in van.split("\n") if nhan in d)
        assert CHAM in dong, dong
    assert "nghiên cứu mô tả tác hại" not in van  # SAP chưa định nghĩa tổn hại ⇒ không tự nêu mục tiêu tác hại
    assert {"3b", "9a", "10", "11", "12", "24b", "29", "31"} <= _thieu(van, "rct", "SPIRIT 2025")
    assert any(x.startswith("K17 SPIRIT 2025 mục 12") for x in KCM.loi_k17(van, "rct"))  # CHẶN, không còn miễn


# ═════════════════════════════════════════════ PRISMA-P 2015 (tổng quan)
def test_tong_quan_khai_du_thi_muc_prisma_p_dat(tmp_path):
    van = _van(tmp_path, "sr_ma",
               g1={"search_period": "Từ khi thành lập mỗi cơ sở dữ liệu đến 30/06/2027",
                   "records_management": "Nhập EndNote để loại bản trùng; sàng lọc trên Rayyan",
                   "information_sources": ["PubMed/MEDLINE", "Embase", "ClinicalTrials.gov"]},
               g7={"authors": "BS. Nguyễn Văn A (chủ nhiệm) · ThS. Trần Thị B (thống kê viên) — Phòng khám",
                   "author_contributions": "Tác giả 1: ý tưởng, sàng lọc; Tác giả 2: phân tích"},
               g9={"authorship": {"guarantor_author_ref": "AUTHOR-01"}},
               search_strings_full='PubMed: ("Diabetes Mellitus, Type 2"[MeSH]) AND (gliflozin*[tiab])',
               protocol_amendment_plan="Mọi sửa đổi quan trọng của đề cương được cập nhật trên PROSPERO kèm ngày và lý "
                                       "do")
    thieu = _thieu(van, "sr_ma", "PRISMA-P 2015")
    assert not thieu & {"3b", "4", "9", "10", "11a"}, thieu
    assert "- Người bảo đảm của tổng quan (chịu trách nhiệm toàn bộ nội dung): BS. Nguyễn Văn A (chủ nhiệm)" in van
    assert '- Dự thảo câu lệnh tìm: PubMed: ("Diabetes Mellitus, Type 2"[MeSH]) AND (gliflozin*[tiab]).' in van


def test_nguoi_bao_dam_lay_dung_tac_gia_theo_ma_g9(tmp_path):
    d = _de_tai(tmp_path, "sr_ma")
    _sua(d, g7={"authors": "BS. A (chủ nhiệm) · ThS. B (thống kê viên) — Phòng khám"},
         g9={"authorship": {"guarantor_author_ref": "AUTHOR-02"}})
    assert SDC.nguoi_bao_dam_tong_quan(SDC.Nguon(d, MA)) == "ThS. B (thống kê viên)"
    _sua(d, review_guarantor="BS. A")  # lời khai trực tiếp thắng
    assert SDC.nguoi_bao_dam_tong_quan(SDC.Nguon(d, MA)) == "BS. A"


def test_sap_tong_quan_co_o_dieu_kien_gop_va_tong_hop_khi_khong_gop():
    sap = G4.generate("T", "Tổng quan", "sr_ma", "Tổng quan hệ thống", "PRISMA", 0, 0.05, 0.8, None, "RR",
                      "2026-11-22")
    assert "- **Điều kiện gộp định lượng:** [CẦN THỐNG KÊ VIÊN" in sap
    assert "- **Tổng hợp khi không gộp được:** [CẦN THỐNG KÊ VIÊN" in sap


def test_dieu_kien_gop_va_tong_hop_mo_ta_tu_sap_vao_de_cuong(tmp_path):
    them = """
### §5 TỔNG HỢP ĐỊNH LƯỢNG

- **Điều kiện gộp định lượng:** chỉ gộp khi có ít nhất 2 thử nghiệm tương đồng lâm sàng
- **Tổng hợp khi không gộp được:** tổng hợp mô tả theo SWiM
"""
    van = _van(tmp_path, "sr_ma", sap_them=them)
    assert not _thieu(van, "sr_ma", "PRISMA-P 2015") & {"15a", "15d"}


# ═════════════════════════════════════════════ STARD 2015 (chẩn đoán)
def test_chan_doan_khai_du_thi_muc_stard_dat(tmp_path):
    van = _van(tmp_path, "diagnostic",
               g1={"target_condition": "Xơ hoá gan tiến triển", "reference_standard": "Đo độ đàn hồi gan ≥ 10 kPa",
                   "intervention_or_exposure": "Chỉ số FIB-4",
                   "blinding": "Xét nghiệm đánh giá (FIB-4) được tính trước khi có kết quả tiêu chuẩn tham chiếu"},
               bien=[("lsm_kpa", "Độ đàn hồi gan (kPa)"), ("chan_doan_khac", "Chẩn đoán ở người không xơ hoá")],
               reference_standard_rationale="Đo đàn hồi gan được chọn làm chuẩn tham chiếu vì làm được cho mọi người",
               index_threshold_rationale="Ngưỡng 2,67 định trước, dựa trên y văn gốc",
               reference_threshold_rationale="Ngưỡng 10 kPa được dùng vì tương ứng xơ hoá F3–F4",
               disease_severity_variable="lsm_kpa", alternative_diagnosis_variable="chan_doan_khac")
    assert not _thieu(van, "diagnostic", "STARD 2015") & {"11", "12a", "12b", "13a", "21a", "21b"}
    assert "- Ở người có bệnh đích, mô tả phân bố mức độ bệnh theo độ đàn hồi gan." in van


def test_chan_doan_bien_chua_khai_thi_o_trong(tmp_path):
    van = _van(tmp_path, "diagnostic", g1={"blinding": None}, reference_standard_rationale=None,
               index_threshold_rationale=None, reference_threshold_rationale=None, disease_severity_variable=None,
               alternative_diagnosis_variable=None)
    assert f"- Ở người không có bệnh đích, mô tả các chẩn đoán khác theo biến: {CHAM}" in van
    assert {"11", "12a", "13a", "21a", "21b"} <= _thieu(van, "diagnostic", "STARD 2015")


# ═════════════════════════════════════════════ TRIPOD+AI 2024 (dự báo)
_KHAI_DU_BAO = dict(
    g1={"candidate_predictors": ["Tuổi", "NT-proBNP"], "prediction_horizon": "12 tháng",
        "predictor_measurement_timing": "Mọi yếu tố dự báo được đo và ghi nhận tại lần khám tuyển; NT-proBNP từ xét "
                                        "nghiệm máu"},
    model_intended_use="Hỗ trợ bác sĩ phân tầng nguy cơ; người dùng dự kiến là bác sĩ phòng khám",
    health_inequalities="Khác biệt theo giới được đánh giá bằng phân nhóm tiền định",
    model_treatment_handling="Điều trị không đưa vào mô hình làm yếu tố dự báo",
    outcome_assessment_blinding="Người xác định nhập viện không biết giá trị yếu tố dự báo",
    model_output_threshold="Mô hình cho xác suất; không đặt ngưỡng phân loại vì mục đích là phân tầng",
    model_fairness_approach="C-statistic ước lượng riêng theo giới để xem tính công bằng",
    ppi_plan="Không có sự tham gia của người bệnh hoặc công chúng trong thiết kế",
    model_input_handling="Chưa áp dụng mô hình khi thiếu giá trị đầu vào",
    model_user_interaction="Người dùng nhập bốn giá trị có sẵn, không cần kỹ năng thống kê",
    model_next_steps="Kiểm định bên ngoài trên cơ sở khác trước khi dùng cho quyết định cá nhân",
)


def test_du_bao_khai_du_thi_muc_tripod_dat(tmp_path):
    van = _van(tmp_path, "prediction", **_KHAI_DU_BAO)
    assert not _thieu(van, "prediction", "TRIPOD+AI 2024") & {"3b", "3c", "6c", "8c", "9b", "14", "15", "19", "27a",
                                                              "27b", "27c"}


def test_du_bao_vang_khai_thi_o_trong(tmp_path):
    van = _van(tmp_path, "prediction", **{k: None for k in _KHAI_DU_BAO if k != "g1"})
    for nhan in ("- Tính công bằng của mô hình:", "- Bước nghiên cứu tiếp theo:", "- Che giấu khi xác định kết cục:"):
        assert next(d for d in van.split("\n") if nhan in d).endswith(CHAM)
    assert {"14", "27c", "8c"} <= _thieu(van, "prediction", "TRIPOD+AI 2024")


# ═════════════════════════════════════════════ CHEERS 2022 (kinh tế)
_SAP_KINH_TE = """
### §16 ĐÁNH GIÁ KINH TẾ Y TẾ (CHEERS 2022)

- **Loại phân tích:** Phân tích chi phí–hiệu quả (CEA) đi kèm thử nghiệm
- **Góc nhìn (perspective):** Cơ sở y tế
- **Chiết khấu:** Không chiết khấu, khung thời gian ≤ 1 năm
- **Đơn vị tiền tệ và năm giá:** VND, giá năm 2026
- **Hạng mục chi phí và nguồn đơn giá:** Khám, thuốc (biểu giá dịch vụ của bệnh viện)
- **Đơn vị hiệu quả:** Thêm một người đạt kiểm soát huyết áp (đơn vị tự nhiên)
- **Tác động phân bố (công bằng):** Không phân tích theo nhóm thu nhập vì phiếu không ghi thu nhập
- **Bất định:** bootstrap phi tham số phân tầng theo nhánh
"""


def test_kinh_te_thanh_muc_rieng_va_dat_cheers(tmp_path):
    van = _van(tmp_path, "rct", sap_them=_SAP_KINH_TE)
    assert "Đánh giá kinh tế y tế" in [d.split(". ", 1)[-1] for d in van.split("\n") if d.startswith("## 4.")]
    assert "**Đánh giá kinh tế y tế.**" not in van  # không còn đoạn in đậm trong mục phân tích
    assert not _thieu(van, "rct", "CHEERS 2022") & {"8", "10", "13", "14", "15", "19", "22"}


def test_tieu_chi_cheers_12_13_22_sua_co_can_cu():
    tc = {m.ma: m for m in TC.danh_sach_muc_them("CHEERS 2022")}
    import re  # noqa: PLC0415

    def khop(ma: str, chu: str) -> bool:
        return all(re.search(y.mau, chu, re.I) for y in tc[ma].yeu_to)

    assert khop("12", "Kết cục chính: tỷ lệ kiểm soát, xác định bằng huyết áp trung bình 2 lần đo")
    assert khop("13", "Đơn vị hiệu quả: thêm một người đạt kiểm soát (đơn vị tự nhiên)")
    assert not khop("22", "Bất định: bootstrap phi tham số phân tầng theo nhánh")  # siết: không còn khớp nhầm
    assert khop("22", "Báo cáo tham số đầu vào: đơn giá từng hạng mục")


def test_o_kinh_te_g4_co_tac_dong_phan_bo():
    assert "distributional_effects" in [k for k, _n, _g in G4.KINH_TE_O]
    sap = "\n".join(G4.muc_kinh_te({"loai_phan_tich": "CEA"}))
    assert "- **Tác động phân bố (công bằng):** [CẦN BÁC SĨ" in sap


# ═════════════════════════════════════════════ K17: gỡ miễn chặn, chuẩn chưa có văn bản
def test_k17_khong_con_tap_mien_chan_cho_bo_sinh():
    assert not hasattr(KCM, "CHUAN_CHO_BO_SINH")


# SQUIRE 2.0 và CARE 2013 đã kiểm chứng trên văn bản mẫu (cuối tệp) ⇒ chỉ TREND còn «chưa đo được»
@pytest.mark.parametrize("tk,chuan,kich_ban", [("non_randomized", "TREND 2004", "non_randomized")])
def test_chuan_chua_co_van_ban_bao_chua_do_va_khong_bao_dat(tk, chuan, kich_ban):
    md = "# ĐỀ CƯƠNG\n\n## 4.1. Thiết kế nghiên cứu\n\nNội dung.\n"
    assert S_ma(tk) == tk  # mã thiết kế có trong bảng thiết kế của hệ
    kq = KCM.doi_chieu(md, tk)
    muc = [r for r in kq["ket_qua"] if r.chuan == chuan]
    assert muc and all(r.trang_thai in ("chua_do", "bao_cao", "khong_ap_dung") for r in muc)
    assert not any(r.trang_thai == "dat" for r in muc)
    ly_do = dict(kq["chua_do"])[chuan]
    assert kich_ban in ly_do and "không tính là đạt" in ly_do
    assert any(x.startswith(f"K17 {chuan} CHƯA ĐO ĐƯỢC") for x in KCM.loi_k17(md, tk))


def S_ma(tk: str) -> str:
    import skill_standards as S  # noqa: PLC0415

    return S.canonical_design_code(tk) or ""


def test_trend_da_doi_chieu_ban_goc_va_bo_sung_yeu_to():
    assert TC.CHUAN_CHUA_DOI_CHIEU_GOC == {}
    tc = {m.ma: m for m in TC.danh_sach_muc_them("TREND 2004")}
    assert all(m.chan for m in tc.values())
    assert {"cách/đơn vị chuyển tải", "nơi chuyển tải", "hoạt động tăng tuân thủ"} <= {y.ten for y in tc["4"].yeu_to}
    assert "nâng chất lượng đo" in {y.ten for y in tc["6"].yeu_to}
    assert "phân tích bổ sung" in {y.ten for y in tc["11"].yeu_to}
    assert set(TC._TREND_CHU_DE) == {str(i) for i in range(1, 23)}


def test_cli_k17_chay_duoc_de_cuong_chan_doan(tmp_path):
    """Chạy thẳng tệp: hàm điều kiện của mô-đun tiêu chí phải đăng ký vào đúng mô-đun K17 (trước sập «điều kiện hàm
    «§xam_lan_nghien_cuu» chưa đăng ký»)."""
    tep = tmp_path / "dc.md"
    tep.write_text("# ĐỀ CƯƠNG\n\n## 4.1. Thiết kế nghiên cứu\n\nNghiên cứu độ chính xác chẩn đoán.\n",
                   encoding="utf-8", newline="\n")
    r = subprocess.run([sys.executable, "-B", str(ROOT / "tools" / "kiem_chuan_de_cuong_theo_muc.py"), "--study", "X",
                        "--tep", str(tep), "--thiet-ke", "diagnostic"], capture_output=True, text=True, timeout=120)
    assert "Traceback" not in r.stderr, r.stderr[-500:]
    assert r.returncode == 1 and "STARD 2015" in r.stdout


# ═════════════════════════════════════════════ phần mở rộng CONSORT: cụm, không kém hơn
def test_mo_rong_consort_ap_theo_thiet_ke():
    cum = "Thử nghiệm ngẫu nhiên theo cụm, phòng khám là đơn vị phân bổ."
    ni = "Thử nghiệm ngẫu nhiên không kém hơn với biên 10 điểm %."
    assert "CONSORT Cluster 2012" in dict(KCM.chuan_ap_dung("rct", cum))
    assert "CONSORT NI 2012" in dict(KCM.chuan_ap_dung("rct", ni))
    mo_rong = {"CONSORT Cluster 2012", "CONSORT NI 2012"}
    assert not mo_rong & set(dict(KCM.chuan_ap_dung("rct", "Thử nghiệm vượt trội.")))
    assert "CONSORT Cluster 2012" not in dict(KCM.chuan_ap_dung("cohort", cum))  # chỉ áp cho thử nghiệm
    assert "CONSORT NI 2012" not in dict(KCM.chuan_ap_dung("rct", "Không thực hiện thiết kế không kém hơn."))


_KHAI_CUM = dict(
    g1={"cluster_definition": "Cụm là phòng khám; can thiệp triển khai ở mức cụm, mục tiêu và kết cục chính đánh giá "
                              "ở mức cá nhân",
        "cluster_eligibility": ["Phòng khám có ít nhất 8 người đủ tiêu chuẩn mỗi tháng"],
        "cluster_consent": "Lãnh đạo phòng khám đồng ý trước khi ngẫu nhiên hoá; từng người ký phiếu sau khi phòng "
                           "khám được phân bổ",
        "randomisation": "Ngẫu nhiên hoá theo cụm: danh sách phòng khám ngẫu nhiên tỷ lệ 1:1, phân tầng theo quy mô",
        "recruitment_strategy": "Tuyển liên tiếp 8 người đủ tiêu chuẩn mỗi phòng khám"},
    g3={"icc": 0.05, "cluster_size": 8, "equal_cluster_sizes": True,
        "icc_source": "PMID: 11111111 (Adams 2004) — ICC huyết áp tâm thu 0–0,052; chọn 0,05 (cận trên)"},
    g3cp={"design_effect": 1.35, "cluster_size": 8, "icc": 0.05},
)


def test_cum_co_mau_neu_co_cum_deu_va_bat_dinh_icc(tmp_path):
    van = _van(tmp_path, "rct", **_KHAI_CUM)
    dong = next(d for d in van.split("\n") if "hiệu ứng thiết kế DE" in d)
    assert "(ICC huyết áp tâm thu 0–0,052; chọn 0,05 (cận trên))" in dong and "giả định cỡ cụm đều" in dong
    kq = _ket_qua(van, "rct")
    for ma in ("2b", "3a", "4a", "5", "6a", "8b", "10b", "10c", "13a", "13b", "15", "16", "17a"):
        assert kq[("CONSORT Cluster 2012", ma)].trang_thai in ("dat", "khong_ap_dung"), (ma, kq[(
            "CONSORT Cluster 2012", ma)].thieu)
    assert "### 4.3.3. Tiêu chuẩn chọn cụm" in van


def test_cum_vang_khai_thi_o_trong(tmp_path):
    van = _van(tmp_path, "rct", g3=_KHAI_CUM["g3"], g3cp=_KHAI_CUM["g3cp"],
               g1={"randomisation": "Ngẫu nhiên hoá theo cụm, tỷ lệ 1:1"})
    for nhan in ("- Định nghĩa cụm và mức áp dụng:", "- Tiêu chuẩn chọn cụm:",
                 "- Đồng ý tham gia ở mức cụm và mức cá nhân:"):
        assert next(d for d in van.split("\n") if nhan in d).endswith(CHAM), nhan
    assert {"3a", "4a", "10c"} <= _thieu(van, "rct", "CONSORT Cluster 2012")


def test_ni_alpha_mot_phia_va_ly_do_bien(tmp_path):
    van = _van(tmp_path, "rct",
               g1={"ni_rationale": "Chọn thiết kế không kém hơn vì tái khám qua điện thoại giảm đi lại",
                   "ni_constancy": "Quần thể tương tự thử nghiệm xác lập hiệu quả; nhóm chứng khác can thiệp của thử "
                                   "nghiệm đó; kết cục tương tự; giả thuyết không kém hơn chỉ áp cho kết cục chính"},
               g3={"hypothesis_type": "non_inferiority",
                   "margin_justification": "Cách biên cố định M1/M2: giữ ≥ 50% hiệu ứng ⇒ M2 ≤ 11 điểm %"},
               g3cp={"effect_type": "NI_PROPORTION", "alpha": 0.025, "p0": 0.6, "margin": 0.1, "n_per_group": 377,
                     "n_total": 754})
    dong = next(d for d in van.split("\n") if "giả thuyết không kém hơn của hai tỷ lệ" in d)
    assert "α = 0,025 (một phía)" in dong and "α = 0,03" not in dong
    assert "Lý do chọn biên: cách biên cố định M1/M2" in dong
    assert "- Khung so sánh: thử nghiệm không kém hơn (non-inferiority)." in van
    kq = _ket_qua(van, "rct")
    for ma in ("2a", "2b", "4a", "5", "6a", "7a"):
        assert kq[("CONSORT NI 2012", ma)].trang_thai == "dat", (ma, kq[("CONSORT NI 2012", ma)].thieu)
    assert kq[("CONSORT NI 2012", "7b")].trang_thai == "khong_ap_dung"  # không có phân tích giữa kỳ


def test_sap_ni_neu_khoang_tin_cay_hai_phia_tuong_ung_alpha_mot_phia():
    sap = G4.generate("T", "NI", "rct", "RCT", "CONSORT", 888, 0.025, 0.8, 0.6, "NI_PROPORTION", "2026-11-22",
                      hypothesis_type="non_inferiority", margin=0.1)
    dong = next(d for d in sap.split("\n") if "Kết luận không kém hơn" in d)
    assert "khoảng tin cậy hai phía 95% (tương ứng kiểm định một phía α = 0.025)" in dong


def test_tripod_16_chi_ap_khi_muc_tieu_co_kiem_dinh_ngoai():
    """«Bước nghiên cứu tiếp theo: kiểm định bên ngoài…» (TRIPOD+AI 27c) là việc của nghiên cứu sau — không làm mục 16
    (so sánh tập phát triển–đánh giá) áp cho đề tài chỉ kiểm định nội."""
    goc = ("# ĐỀ CƯƠNG\n\n# 2. MỤC TIÊU NGHIÊN CỨU\n\n## 2.1. Mục tiêu\n\n1. Phát triển {x} một mô hình dự báo nhập "
           "viện.\n\n# 4. PHƯƠNG PHÁP\n\n## 4.10. Xử lý và phân tích số liệu\n\n- Kiểm định nội bằng bootstrap.\n\n"
           "## 5.5. Hạn chế\n\n- Bước nghiên cứu tiếp theo: kiểm định bên ngoài trên cơ sở khác.\n")
    noi = _ket_qua(goc.format(x="và kiểm định nội"), "prediction")[("TRIPOD+AI 2024", "16")]
    ngoai = _ket_qua(goc.format(x="và kiểm định ngoại"), "prediction")[("TRIPOD+AI 2024", "16")]
    assert noi.trang_thai == "khong_ap_dung"
    assert ngoai.trang_thai != "khong_ap_dung"


_BT = ("# TIN NHẮN NHẮC UỐNG THUỐC: {tieu}\n\n## TÓM TẮT\n\n{tt}\n\n## I. GIỚI THIỆU\n\nThiếu thử nghiệm không "
       "kém hơn và thử nghiệm theo cụm về can thiệp này [1].\n\n## II. PHƯƠNG PHÁP\n\n{pp}\n\n## III. KẾT QUẢ\n\n{kq}"
       "\n\n## IV. BÀN LUẬN\n\n{bl}\n\n## TÀI LIỆU THAM KHẢO\n\n1. Smith J. A cluster randomised non-inferiority "
       "trial. BMJ. 2020.\n")


def _bt(**k) -> str:
    gia = dict(tieu="THỬ NGHIỆM NGẪU NHIÊN", tt="Thử nghiệm ngẫu nhiên song song.", kq="Kết quả.", bl="Bàn luận.",
               pp="Thử nghiệm ngẫu nhiên song song hai nhánh, phân bổ cá nhân, khung vượt trội.")
    gia.update(k)
    return _BT.format(**gia)


def _k18(md: str) -> dict:
    import tieu_chi_ban_thao as TB  # noqa: PLC0415

    kq = TB.doi_chieu_ban_thao(md, "rct", co_so_lieu=True)
    return {"chuan": {c for c, _ in kq["chuan"]}, "kq": {(r.chuan, r.ma): r for r in kq["ket_qua"]}}


def test_k18_ap_mo_rong_consort_cung_dieu_kien_k17():
    """K18 áp hai phần mở rộng cho bài báo theo thiết kế CỦA ĐỀ TÀI (Phương pháp/Tóm tắt) — không theo Giới thiệu, Bàn
    luận, tài liệu tham khảo hay TÊN chuẩn được dẫn làm nguồn («CONSORT mở rộng không kém hơn, Piaggio 2012»)."""
    mo_rong = {"CONSORT Cluster 2012", "CONSORT NI 2012"}
    vt = _bt(pp="Thử nghiệm ngẫu nhiên song song, phân bổ cá nhân. Phân tích theo đề cương (CONSORT mở rộng không kém "
                "hơn, Piaggio 2012) là phân tích độ nhạy.",
             bl="So với thử nghiệm không kém hơn theo cụm của Smith [1].")
    assert not mo_rong & _k18(vt)["chuan"]
    cum_ni = _bt(pp="Thử nghiệm ngẫu nhiên theo cụm, khung không kém hơn; phòng khám là đơn vị phân bổ.")
    assert mo_rong <= _k18(cum_ni)["chuan"]


def test_k18_muc_ket_qua_mo_rong_cum_va_khong_kem():
    pp = "Thử nghiệm ngẫu nhiên theo cụm, khung không kém hơn; phòng khám là đơn vị phân bổ."
    du = _bt(tieu="THỬ NGHIỆM NGẪU NHIÊN THEO CỤM, KHÔNG KÉM HƠN", pp=pp,
             tt="Thử nghiệm ngẫu nhiên theo cụm không kém hơn, biên Δ = 10 điểm %; 16 phòng khám được phân bổ.",
             kq="16 phòng khám được phân bổ ngẫu nhiên (8 mỗi nhóm), 320 người tham gia. Không có phòng khám nào rút; "
                "12 người mất theo dõi. Đặc điểm nền của người tham gia và của các phòng khám (quy mô) cân bằng. "
                "Cả 16 phòng khám được đưa vào phân tích. ICC ước tính cho kết cục chính = 0,04.",
             bl="Kết quả cho thấy tin nhắn không kém hơn chăm sóc thường quy vì cận dưới KTC 95% nằm trên biên.")
    kq = _k18(du)["kq"]
    for ma in ("1b", "13a", "13b", "15", "16", "17a"):
        assert kq[("CONSORT Cluster 2012", ma)].trang_thai == "dat", (ma, kq[("CONSORT Cluster 2012", ma)].thieu)
    for ma in ("1b", "22"):
        assert kq[("CONSORT NI 2012", ma)].trang_thai == "dat", (ma, kq[("CONSORT NI 2012", ma)].thieu)
    thieu = _k18(_bt(tieu="THỬ NGHIỆM NGẪU NHIÊN THEO CỤM, KHÔNG KÉM HƠN", pp=pp, kq="Hai nhóm tương tự.",
                     bl="Can thiệp có ích."))["kq"]
    for k in (("CONSORT Cluster 2012", "13a"), ("CONSORT Cluster 2012", "17a"), ("CONSORT NI 2012", "22")):
        assert thieu[k].trang_thai == "thieu", k


def test_ni_7b_nhan_co_khong_khong_phai_co_phan_tich_giua_ky():
    pp = "Thử nghiệm ngẫu nhiên song song, khung không kém hơn. *Phân tích giữa kỳ:* có phân tích giữa kỳ: không."
    assert _k18(_bt(pp=pp))["kq"][("CONSORT NI 2012", "7b")].trang_thai == "khong_ap_dung"
    co = _bt(pp="Thử nghiệm ngẫu nhiên song song, khung không kém hơn. Có phân tích giữa kỳ sau 50% người tham gia.")
    assert _k18(co)["kq"][("CONSORT NI 2012", "7b")].trang_thai == "thieu"


# ═════════════════════════════════════════════ biến PI khai phải có trên phiếu của MỌI kịch bản
def test_bien_khai_o_dac_ta_g10_co_tren_phieu_moi_kich_ban():
    """Biến PI khai ở đặc tả G10 (`*_variable`: mức độ bệnh STARD 21a, chẩn đoán khác 21b…) phải là một trường của
    phiếu thu thập của CHÍNH kịch bản — kể cả kịch bản chân thực thay phiếu và biến thể kế thừa. Thiếu ⇒ bộ sinh đề
    cương chỉ in ô trống (không bịa tên biến) và K17 chặn; đo 22/11/2026: kịch bản chẩn đoán chân thực khai
    `chan_doan_khac` nhưng phiếu không có trường đó ⇒ STARD 21b thiếu ở cả đề cương lẫn bản thảo."""
    import gia_lap_bien_the_kho as BTK  # noqa: PLC0415
    import gia_lap_chan_thuc as GCT  # noqa: PLC0415
    import gia_lap_dinh_ky as GL  # noqa: PLC0415

    tat = {**GL.KICH_BAN, **BTK.kich_ban_kho(), **GCT.kich_ban_chan_thuc()}
    lech, dem = [], 0
    for ma, kb in tat.items():
        dt = (kb.get("ho_so_tron_vong") or {}).get("dac_ta_G10") or {}
        ten = {b[0] for b in (kb.get("bien_so") or {}).get("bo_bien") or ()}
        for k, v in dt.items():
            if k.endswith("_variable") and isinstance(v, str) and v.strip():
                dem += 1
                if v not in ten:
                    lech.append((ma, k, v))
    assert dem >= 4 and not lech, lech


def test_phieu_chan_doan_chan_thuc_ghi_chan_doan_khac_dung_nhanh_va_khong_doi_du_lieu_khac():
    """Trường «chẩn đoán khác» của phiếu chẩn đoán chân thực: cùng nhãn và lựa chọn với kịch bản gốc, chỉ hiện khi đo
    đàn hồi hợp lệ VÀ không xơ hoá tiến triển; giá trị tất định theo độ đàn hồi đã mô phỏng (không rút thêm số ngẫu
    nhiên ⇒ mọi trường khác của dữ liệu giữ nguyên)."""
    import gia_lap_chan_thuc as GCT  # noqa: PLC0415
    import gia_lap_dinh_ky as GL  # noqa: PLC0415

    kb = GCT.kich_ban_chan_thuc()["diagnostic_chan_thuc"]
    goc = {b[0]: b for b in GL.KICH_BAN["chan_doan"]["bien_so"]["bo_bien"]}["chan_doan_khac"]
    bo = {b[0]: b for b in kb["bien_so"]["bo_bien"]}
    assert bo["chan_doan_khac"][1:4] == goc[1:4]
    assert kb["bien_so"]["meta_bien"]["chan_doan_khac"]["nhanh"] == "[lsm_hop_le] = '1' and [xo_hoa_tien_trien] = '0'"
    thu_tu = [b[0] for b in kb["bien_so"]["bo_bien"]]
    assert thu_tu.index("chan_doan_khac") == thu_tu.index("xo_hoa_tien_trien") + 1
    meta = kb["bien_so"]["meta_bien"]
    assert meta["chan_doan_khac"]["form"] == meta["xo_hoa_tien_trien"]["form"] == "dan_hoi"  # phần chuẩn tham chiếu

    import copy  # noqa: PLC0415

    import sinh_du_lieu_redcap as SR  # noqa: PLC0415

    hm = kb["du_lieu_redcap"]["hinh_mau"]
    moi = SR.sinh(GCT.tu_dien_cua(kb), 400, hm, seed=7)
    cu_kb = copy.deepcopy(kb)
    cu_kb["bien_so"]["bo_bien"] = [b for b in cu_kb["bien_so"]["bo_bien"] if b[0] != "chan_doan_khac"]
    cu = SR.sinh(GCT.tu_dien_cua(cu_kb), 400, hm, seed=7)
    assert [{k: r[k] for k in c} for r, c in zip(moi, cu)] == cu  # thêm trường không đổi ô nào của dữ liệu cũ
    co_gia_tri = [r for r in moi if r["chan_doan_khac"] is not None]
    assert co_gia_tri and all(r["lsm_hop_le"] == 1 and r["xo_hoa_tien_trien"] == 0 for r in co_gia_tri)
    assert all(r["chan_doan_khac"] == (1 if r["lsm_kpa"] < 8 else 2) for r in co_gia_tri)
    assert all(r["chan_doan_khac"] is None for r in moi if r["lsm_hop_le"] != 1 or r["xo_hoa_tien_trien"] == 1)


def test_mo_rong_rct_chi_doc_phan_thiet_ke_cua_chinh_de_tai():
    """Phần mở rộng cụm/không kém hơn áp theo thiết kế CỦA ĐỀ TÀI (tên, mục tiêu, phương pháp), không theo câu nhắc
    nghiên cứu khác ở Đặt vấn đề/Tổng quan, tên bài trong tài liệu tham khảo hay phần bàn luận."""
    nen = ("# ĐỀ CƯƠNG NGHIÊN CỨU KHOA HỌC\n\n# 1. ĐẶT VẤN ĐỀ\n\nThiếu thử nghiệm không kém hơn về tái khám từ xa.\n\n"
           "# 2. MỤC TIÊU NGHIÊN CỨU\n\n1. So sánh tỷ lệ kiểm soát huyết áp giữa hai nhóm.\n\n"
           "# 3. TỔNG QUAN TÀI LIỆU\n\n## 3.2. Các bằng chứng hiện có\n\nMột thử nghiệm ngẫu nhiên theo cụm ở Anh.\n\n"
           "# 4. ĐỐI TƯỢNG VÀ PHƯƠNG PHÁP NGHIÊN CỨU\n\n## 4.1. Thiết kế nghiên cứu\n\n{tk}\n\n"
           "# 5. DỰ KIẾN KẾT QUẢ\n\n## 5.5. Dự kiến bàn luận\n\nSo với thử nghiệm không kém hơn của Smith.\n\n"
           "# 7. TÀI LIỆU THAM KHẢO\n\n1. Smith J. A cluster randomised non-inferiority trial. BMJ. 2020.\n")
    mo_rong = {"CONSORT Cluster 2012", "CONSORT NI 2012"}
    vuot_troi = nen.format(tk="Thử nghiệm ngẫu nhiên song song hai nhánh, phân bổ cá nhân, khung vượt trội.")
    assert not mo_rong & set(dict(KCM.chuan_ap_dung("rct", vuot_troi)))
    cum_ni = nen.format(tk="Thử nghiệm ngẫu nhiên theo cụm, khung không kém hơn, phòng khám là đơn vị phân bổ.")
    assert mo_rong <= set(dict(KCM.chuan_ap_dung("rct", cum_ni)))


# ═════════════════════════════════════════════ RECORD 2015 mục 13.1 — chọn quần thể từ dữ liệu thường quy
def _nguon_gia(tmp_path: Path, tk: str, loai_tru: list, nguon=("hồ sơ bệnh án", "xét nghiệm máu"), meta=None):
    from types import SimpleNamespace  # noqa: PLC0415

    s = {("data_collection", "source"): list(nguon)}
    return SimpleNamespace(thiet_ke=tk, g1={"exclusion_criteria": loai_tru}, out=tmp_path, study="X",
                           meta=meta or {}, s=lambda *k: s.get(k))


_THUONG_QUY = "Số liệu trích từ hồ sơ bệnh án điện tử."


def test_record_13_1_loc_theo_san_co_chat_luong_tu_quyet_dinh_da_chot(tmp_path):
    n = _nguon_gia(tmp_path, "diagnostic", ["Uống rượu nguy hại", "Không đo được độ đàn hồi gan hợp lệ"])
    ra = SDC.chon_quan_the_thuong_quy(n, _THUONG_QUY)
    loc = ra[0]
    assert loc.startswith("- Chọn quần thể từ dữ liệu thường quy (hồ sơ bệnh án; xét nghiệm máu)")
    # lọc dữ liệu: tiêu chuẩn loại trừ về số đo + lý do loại trên sơ đồ chọn của thiết kế (khuôn G6 vẽ)
    for x in ("không đo được độ đàn hồi gan hợp lệ", "không làm tiêu chuẩn tham chiếu", "kết quả không xác định"):
        assert x in loc, x
    for x in ("uống rượu", "không đủ tiêu chuẩn", "từ chối"):  # tiêu chuẩn lâm sàng/tham gia không phải lọc dữ liệu
        assert x not in loc.lower(), x
    assert ra[1].startswith("- Sơ đồ chọn ghi số người ở từng bước (người bệnh đủ điều kiện → làm xét nghiệm")
    assert SDC.chon_quan_the_thuong_quy(n, "Phỏng vấn người bệnh bằng phiếu.") == []  # không dùng dữ liệu thường quy


def test_record_13_1_doc_so_so_do_luong_cua_de_tai_khong_in_so(tmp_path):
    (tmp_path / "SO_DO_LUONG_X.csv").write_text(
        "buoc,n,loai,nhanh,ly_do\nHồ sơ trong khung chọn mẫu,812,chinh,,\nLoại,40,loai,,"
        "Hồ sơ thiếu dữ liệu HbA1c: 31; Hồ sơ trùng lặp: 9\nĐưa vào phân tích,772,chinh,,\n",
        encoding="utf-8", newline="\n")
    ra = SDC.chon_quan_the_thuong_quy(_nguon_gia(tmp_path, "cross_sectional", []), _THUONG_QUY)
    assert "hồ sơ thiếu dữ liệu HbA1c; hồ sơ trùng lặp" in ra[0]
    assert "hồ sơ trong khung chọn mẫu → đưa vào phân tích" in ra[1]
    assert not any(c.isdigit() for c in "".join(ra).replace("HbA1c", ""))  # kế hoạch, không chép số của sổ


def test_record_13_1_khong_co_loc_du_lieu_thi_o_trong_va_k17_bao_thieu(tmp_path):
    n = _nguon_gia(tmp_path, "case_control", ["Có thai", "Thiếu máu nặng"])  # khuôn bệnh–chứng: lý do lâm sàng
    ra = SDC.chon_quan_the_thuong_quy(n, _THUONG_QUY)
    assert ra == [f"- Lọc theo độ sẵn có và chất lượng dữ liệu khi chọn quần thể: {CHAM}"]
    goc = ("# ĐỀ CƯƠNG\n\n# 1. ĐẶT VẤN ĐỀ\n\nNội dung.\n\n# 4. ĐỐI TƯỢNG VÀ PHƯƠNG PHÁP NGHIÊN CỨU\n\n"
           "## 4.4. Cỡ mẫu và phương pháp chọn mẫu\n\n"
           "### 4.4.2. Phương pháp chọn mẫu\n\nTrích hồ sơ bệnh án điện tử.\n\n{dong}\n")
    trong = _ket_qua(goc.format(dong=ra[0]), "cross_sectional")[("RECORD 2015", "13.1")]
    co = SDC.chon_quan_the_thuong_quy(_nguon_gia(tmp_path, "diagnostic", []), _THUONG_QUY)
    du = _ket_qua(goc.format(dong="\n".join(co)), "cross_sectional")[("RECORD 2015", "13.1")]
    assert trong.trang_thai == "thieu" and du.trang_thai == "dat"


# ═════════════════════════════════════════════ RCT vượt trội: dòng theo đề cương đúng khung, không mã trong văn xuôi
_TT = {"bien": "tuan_thu_de_cuong", "dinh_nghia": "nhận ≥ 80% số lần can thiệp theo nhánh"}
_SAP9 = "### §8 X\n\n### §9 PHÂN TÍCH ĐỘ NHẠY\n\n- Complete case vs MI  \n"


def test_theo_de_cuong_cau_ket_luan_theo_khung_gia_thuyet():
    import dinh_nghia_thay_the as DTT  # noqa: PLC0415

    vt = DTT.chen_theo_de_cuong(_SAP9, _TT, "superiority")
    assert "không kém hơn" not in vt and "phân tích độ nhạy — kết luận chính theo phân tích ITT" in vt
    assert "kết luận không kém hơn phải vững ở cả ITT lẫn theo đề cương" in DTT.chen_theo_de_cuong(
        _SAP9, _TT, "non_inferiority")
    assert "kết luận tương đương phải vững" in DTT.chen_theo_de_cuong(_SAP9, _TT, "equivalence")
    assert "không kém hơn" not in DTT.chen_theo_de_cuong(_SAP9, _TT)  # mặc định: vượt trội
    sap = G4.generate("T", "RCT", "rct", "RCT", "CONSORT", 400, 0.05, 0.8, 0.3, "RR", "2026-11-22",
                      hypothesis_type="superiority")
    sap = G4._dien_khung(sap.replace("### §9", "### §9", 1), {"tuan_thu_de_cuong": _TT}, "rct", "superiority")
    dong = next(d for d in sap.split("\n") if "Phân tích theo đề cương (per-protocol)" in d)
    assert "không kém hơn" not in dong
    # đề cương thử nghiệm vượt trội chép dòng này không còn bị K17 áp nhầm phần mở rộng không kém hơn
    md = ("# ĐỀ CƯƠNG\n\n# 1. ĐẶT VẤN ĐỀ\n\nNội dung.\n\n# 4. ĐỐI TƯỢNG VÀ PHƯƠNG PHÁP NGHIÊN CỨU\n\n"
          "## 4.11. Xử lý và phân tích số liệu\n\n" + dong + "\n")
    assert "CONSORT NI 2012" not in dict(KCM.chuan_ap_dung("rct", md))


def test_dieu_kien_ma_bang_mot_thanh_van_xuoi():
    import kiem_de_cuong_nop_hoi_dong as KD  # noqa: PLC0415

    cu = dict(SDC.NHAN_BIEN)
    try:
        SDC.NHAN_BIEN["tuan_thu_de_cuong"] = "Tuân thủ đề cương"
        s = SDC.lam_sach("Phân tích theo đề cương: chỉ người có `tuan_thu_de_cuong` = 1 — nhận ≥ 80% số lần")
        assert "chỉ người có tuân thủ đề cương — nhận ≥ 80% số lần" in s and "= 1" not in s
        k8 = [bt for bt, ten in KD._DAU_VET_MAY if "mã biến" in ten][0]  # chính luật K8 của bộ kiểm nộp
        assert not k8.search(s)
        assert "= 1" in SDC.lam_sach("chỉ người có `bien_la` = 1")  # biến không có nhãn ⇒ giữ để K8 bắt
    finally:
        SDC.NHAN_BIEN.clear()
        SDC.NHAN_BIEN.update(cu)


def test_g10_cong_cu_do_khong_lay_dinh_nghia_lam_nguon_do(tmp_path, monkeypatch):
    import quyet_dinh_da_chot as QD  # noqa: PLC0415

    mt = [{"vai_tro": "ket_cuc_chinh", "bien": "nhap_vien", "cong_cu": "Hồ sơ + giấy ra viện",
           "khai_niem": "nhập viện"},
          {"vai_tro": "yeu_to", "bien": "ntprobnp", "cong_cu": "Xét nghiệm", "khai_niem": "NT-proBNP"},
          {"vai_tro": "dinh_nghia_thay_the", "bien": "ntprobnp_can2", "khai_niem": "NT-proBNP căn bậc hai",
           "cong_cu": "NT-proBNP biến đổi căn bậc hai, giữ thang liên tục (Royston 2006, PMID 16217841)"},
          {"vai_tro": "tuan_thu_de_cuong", "bien": "tt", "cong_cu": "Tuân thủ: nhận ≥ 80% số lần", "khai_niem": "x"}]
    monkeypatch.setattr(QD, "ma_tran", lambda *_a: mt)
    ra = QD.rut(tmp_path, "X", {"gate_params": {"G1": {"design": "prediction"}}})
    assert ra["instrument"][0]["name"].startswith("Phiếu trích hồ sơ (CRF)")
    assert ra["data_source"][0].startswith("Hồ sơ + giấy ra viện; Xét nghiệm (")
    assert "thang liên tục" not in ra["data_source"][0] and "Tuân thủ" not in ra["data_source"][0]
    mt.append({"vai_tro": "ket_cuc_phu", "bien": "qol", "cong_cu": "Thang đo chất lượng sống KCCQ", "khai_niem": "q"})
    assert "instrument" not in QD.rut(tmp_path, "X", {"gate_params": {"G1": {"design": "prediction"}}})


# ═════════════════════════════════════════════ SQUIRE 2.0 và CARE 2013 — văn bản mẫu kiểm chứng tiêu chí
#: Đề cương cải tiến chất lượng mẫu (văn bản hệ viết để kiểm chứng tiêu chí; số liệu là ví dụ, không phải dữ liệu thật)
DC_CAI_TIEN = """# ĐỀ CƯƠNG DỰ ÁN CẢI TIẾN CHẤT LƯỢNG

## THÔNG TIN CHUNG

| Kinh phí | Nguồn kinh phí của bệnh viện; đơn vị tài trợ không tham gia thiết kế, phân tích hay công bố |

# 1. ĐẶT VẤN ĐỀ

Tỷ lệ người tăng huyết áp được đo lại huyết áp tại lần tái khám tại phòng khám của đơn vị chỉ đạt 54%, là gánh nặng
cho chất lượng chăm sóc [1].

# 2. MỤC TIÊU

1. Đánh giá thay đổi tỷ lệ được đo lại huyết áp trước và sau ba chu trình PDSA tại phòng khám.

# 3. TỔNG QUAN TÀI LIỆU

Dự án dựa trên mô hình cải tiến PDSA [2]; can thiệp được kỳ vọng cải thiện tỷ lệ đo lại nhờ nhắc việc tại bàn khám.

# 4. PHƯƠNG PHÁP

## 4.1. Thiết kế nghiên cứu

Thiết kế trước–sau với chuỗi thời gian gián đoạn theo tuần; xu hướng trước can thiệp được tính để tách tác động.

## 4.2. Địa điểm và thời gian nghiên cứu

Phòng khám nội tổng quát, Bệnh viện chủ trì, năm 2027.

## 4.3. Can thiệp cải tiến

Can thiệp gồm ba chu trình PDSA: phiếu nhắc đo lại tại bàn khám, tập huấn điều dưỡng, phản hồi số liệu
hằng tuần cho nhóm.

## 4.4. Nhân lực và phân công

Nhóm cải tiến gồm 2 bác sĩ, 3 điều dưỡng và 1 cán bộ quản lý chất lượng; thành viên họp mỗi tuần.

## 4.5. Biến số và chỉ số nghiên cứu

- Chỉ số quá trình: tỷ lệ lượt khám có phiếu nhắc; chỉ số kết cục: tỷ lệ được đo lại huyết áp.
- Định nghĩa: đo lại là có ít nhất hai lần đo cách nhau 5 phút; máy đo đã chuẩn hoá, độ tin cậy kiểm định hằng quý.

Yếu tố bối cảnh (thay đổi nhân sự, số lượt khám) được ghi định kỳ mỗi chu kỳ PDSA.

## 4.6. Quy trình nghiên cứu

Mỗi chu kỳ bốn tuần: lập kế hoạch, thực hiện, kiểm tra, điều chỉnh.

## 4.7. Quản lý dữ liệu

Nhập liệu kép và đối chiếu để bảo đảm dữ liệu đầy đủ và chính xác.

## 4.8. Xử lý và phân tích số liệu

Biểu đồ chạy và biểu đồ kiểm soát theo tuần để xem biến thiên theo thời gian; hồi quy phân đoạn so sánh trước–sau.

## 4.9. Sai số và biện pháp khống chế

Nhiễu do xu hướng mùa vụ được kiểm soát bằng chuỗi thời gian; sai lệch đo lường được giảm thiểu bằng tập huấn.

## 4.10. Đạo đức trong nghiên cứu

Hội đồng Đạo đức của bệnh viện xét duyệt; nhóm khai báo không có xung đột lợi ích.

# 5. DỰ KIẾN KẾT QUẢ

- Diễn tiến các chu kỳ can thiệp theo thời gian; chỉ số quá trình và kết cục từng giai đoạn.
- Ghi nhận hệ quả ngoài ý muốn (kéo dài thời gian khám); báo cáo số liệu thiếu theo từng tuần.

## 5.2. Dự kiến bàn luận

So sánh với y văn; bàn chi phí của phiếu nhắc và tính bền vững sau khi kết thúc dự án.

## 5.3. Hạn chế

Một phòng khám nên khó suy rộng; nhiễu chưa đo được khống chế một phần bằng chuỗi thời gian.
"""

#: Đề cương báo cáo ca mẫu (văn bản hệ viết để kiểm chứng tiêu chí; ca hư cấu, không PII)
DC_BAO_CAO_CA = """# ĐỀ CƯƠNG BÁO CÁO CA LÂM SÀNG

# 1. ĐẶT VẤN ĐỀ

Hạ natri máu do thuốc lợi tiểu thiazid ở người cao tuổi hiếm khi biểu hiện co giật [1].

# 2. TRÌNH BÀY CA

- Người bệnh nữ, 78 tuổi, nghề nghiệp trước đây giáo viên (đã khử định danh).
- Triệu chứng chính: lú lẫn và co giật.
- Tiền sử tăng huyết áp; bệnh kèm đái tháo đường; đã điều trị hydrochlorothiazid 25 mg trong 3 tháng.
- Khám: không dấu thần kinh khu trú.
- Dòng thời gian các mốc quan trọng trình bày ở bảng.
- Chẩn đoán: xét nghiệm điện giải đồ, chẩn đoán hình ảnh sọ não; khó khăn do người bệnh lú lẫn không kể được bệnh sử;
  chẩn đoán phân biệt gồm đột quỵ và hạ đường huyết.
- Điều trị: ngừng thiazid, bù natri; liều và thời gian dùng ghi đủ; mọi thay đổi điều trị ghi kèm lý do.
- Theo dõi tái khám sau 1 và 4 tuần; đánh giá tuân thủ và dung nạp; ghi mọi biến cố bất lợi.

# 3. ĐẠO ĐỨC

Người bệnh và người nhà đồng ý bằng văn bản cho công bố.

# 4. DỰ KIẾN BÀN LUẬN

Điểm mạnh và hạn chế của xử trí; đối chiếu y văn [2]; lý do của kết luận về quan hệ nhân quả; bài học chính; quan điểm
của người bệnh được ghi lại.
"""


def _muc_dat(van: str, tk: str, chuan: str) -> dict:
    return {ma: r for (c, ma), r in _ket_qua(van, tk).items() if c == chuan}


def test_squire_kiem_chung_tren_de_cuong_cai_tien_mau():
    kq = _muc_dat(DC_CAI_TIEN, "quality_improvement", "SQUIRE 2.0")
    assert len(kq) == 40
    chua = {ma: r.thieu for ma, r in kq.items() if r.muc_do != "bao_cao" and r.trang_thai not in ("dat",
                                                                                                     "khong_ap_dung")}
    assert not chua, chua
    assert not [x for x in KCM.loi_k17(DC_CAI_TIEN, "quality_improvement") if x.startswith("K17 SQUIRE")]
    # yếu tố bổ sung sau đối chiếu bảng gốc: thiếu ⇒ mục thiếu
    for ma, cu, moi in (("3", "chỉ đạt 54%, là gánh nặng\ncho chất lượng chăm sóc", "còn thấp"),
                        ("5", "can thiệp được kỳ vọng cải thiện tỷ lệ đo lại", "can thiệp gồm nhắc việc"),
                        ("10a", "máy đo đã chuẩn hoá, độ tin cậy kiểm định hằng quý", "máy đo đặt tại bàn khám"),
                        ("10a", "- Định nghĩa: đo lại là có ít nhất hai lần đo cách nhau 5 phút; ", "- "),
                        ("10b", "được ghi định kỳ mỗi chu kỳ PDSA", "được ghi")):
        assert cu in DC_CAI_TIEN
        assert _muc_dat(DC_CAI_TIEN.replace(cu, moi), "quality_improvement", "SQUIRE 2.0")[ma].trang_thai == "thieu", ma


def test_care_kiem_chung_tren_de_cuong_bao_cao_ca_mau():
    kq = _muc_dat(DC_BAO_CAO_CA, "case_report", "CARE 2013")
    assert len(kq) == 23
    chua = {ma: r.thieu for ma, r in kq.items() if r.muc_do != "bao_cao" and r.trang_thai not in ("dat",
                                                                                                     "khong_ap_dung")}
    assert not chua, chua
    assert not [x for x in KCM.loi_k17(DC_BAO_CAO_CA, "case_report") if x.startswith("K17 CARE")]
    for ma, cu, moi in (("5c", "bệnh kèm đái tháo đường; đã điều trị hydrochlorothiazid 25 mg trong 3 tháng",
                         "ổn định"),
                        ("9a", "mọi thay đổi điều trị ghi kèm lý do", "ghi chép đủ"),
                        ("9a", "liều và thời gian dùng ghi đủ; ", ""),
                        ("10a", "đánh giá tuân thủ và dung nạp; ", ""),
                        ("10a", "; ghi mọi biến cố bất lợi", "")):
        assert cu in DC_BAO_CAO_CA
        assert _muc_dat(DC_BAO_CAO_CA.replace(cu, moi), "case_report", "CARE 2013")[ma].trang_thai == "thieu", ma


def test_squire_care_roi_tap_chua_co_van_ban_trend_con_lai():
    assert set(TC.CHUAN_CHUA_CO_VAN_BAN) == {"TREND 2004"}
    for tk, chuan in (("quality_improvement", "SQUIRE 2.0"), ("case_report", "CARE 2013")):
        kq = KCM.doi_chieu("# ĐỀ CƯƠNG\n\n# 1. ĐẶT VẤN ĐỀ\n\nNội dung.\n", tk)
        assert chuan not in dict(kq["chua_do"])
        assert any(x.startswith(f"K17 {chuan} mục") for x in KCM.loi_k17("# ĐỀ CƯƠNG\n\n# 1. ĐẶT VẤN ĐỀ\n\nX.\n", tk))
