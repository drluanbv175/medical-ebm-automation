# -*- coding: utf-8 -*-
"""Bộ sinh G7 — mục chuẩn báo cáo K18 còn thiếu ở các kịch bản giả lập BIẾN THỂ (22/11/2026, tối).

Chốt CI giả lập không còn sổ nợ: mọi kịch bản phải đạt đủ mục chuẩn báo cáo ở bản thảo G7 và báo cáo tổng hợp. Đo trên
giả lập trọn vòng: thử nghiệm không kém hơn thiếu CONSORT 2025 mục 7 ở báo cáo tổng hợp; thử nghiệm cụm thiếu mục 19;
thuần tập sống còn thiếu RECORD 13.1, 19.1 và STROBE 16a; thuần tập thiếu dữ liệu thiếu RECORD 13.1, 19.1 và STROBE 19;
thử nghiệm kèm đánh giá kinh tế thiếu CHEERS 2022 mục 4, 8, 10, 13, 18, 19, 22 và CONSORT 24a. Mỗi phép dưới đây kiểm
một đoạn bộ sinh: dòng chép dữ kiện CÓ THẬT (sổ sàng lọc, tóm tắt G6, SAP §16) ⇒ K18 đạt; vắng dữ kiện ⇒ K18 vẫn thiếu
(không câu mẫu làm bằng chứng giả).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

import bao_cao_tong_hop as B  # noqa: E402
import run_g4_auto as G4A  # noqa: E402
import run_g7_auto as G7  # noqa: E402
import tieu_chi_ban_thao as TB  # noqa: E402

STUDY = "X"


def _ghi(p: Path, s: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding="utf-8", newline="\n")


def _meta(d: Path, gp: dict, **pi) -> Path:
    _ghi(d / "study_meta.json", json.dumps({"gate_params": gp, **pi}, ensure_ascii=False))
    return d


def _ban_thao(d: Path, tk: str, design_primary: str, std: str, ext: tuple = (), **them) -> str:
    """Bản thảo do CHÍNH bộ sinh dựng (generate_manuscript + lap_o_da_chot) từ hồ sơ trong `d`."""
    kw = dict(study=STUDY, topic="Chủ đề thử", n_sr=1, n_rct=1, n_guideline=0, research_gaps=["còn thiếu dữ liệu"],
              pmids=["11111111", "22222222", "33333333"], pmid_meta={}, design_code=tk,
              design_primary=design_primary, reporting_std=std, irb_number="GL-1/2026", icf_version="1.0",
              registration="Không đăng ký — không bắt buộc", n_total=100, n_adjusted=110, alpha=0.05, power=0.8,
              effect_val=None, effect_type="OR", formula_used="", g4_status="LOCKED", g4_lock_date="2026-11-01",
              target_journal="Tạp chí Y học Việt Nam", word_limit=3500, run_date="2026-11-22",
              khoi_consort=G7.khoi_consort_bo_sung_g7(d, STUDY, tk),
              khoi_chuan=G7.khoi_chuan_bao_cao_g7(d, STUDY, tk, None, list(ext)), **them)
    van, _da = G7.lap_o_da_chot_g7(G7.generate_manuscript(**kw), d, STUDY)
    return van


def _tt(md: str, tk: str, chuan: str) -> dict:
    """{mã: trạng thái} — chế độ NỘP, sau khi tác giả đối chiếu số G6 và gỡ nhãn đối chiếu."""
    kq = TB.doi_chieu_ban_thao(md.replace(G7.NHAN_DOI_CHIEU_G6, ""), tk, co_so_lieu=True)
    return {r.ma: r.trang_thai for r in kq["ket_qua"] if r.chuan == chuan}


RCT = ("rct", "Thử nghiệm lâm sàng ngẫu nhiên có đối chứng (RCT)", "CONSORT 2025")


# ───────────────────── CONSORT 2025 mục 7 — mục tiêu tác hại phải tới được báo cáo tổng hợp ─────────────────────
DE_CUONG = """# ĐỀ CƯƠNG NGHIÊN CỨU KHOA HỌC

## SO SÁNH TÁI KHÁM QUA ĐIỆN THOẠI VÀ TÁI KHÁM TRỰC TIẾP

# 1. ĐẶT VẤN ĐỀ

Tăng huyết áp phổ biến [1].

# 2. MỤC TIÊU NGHIÊN CỨU

## 2.1. Mục tiêu

1. Đánh giá tái khám qua điện thoại có không kém hơn tái khám trực tiếp về kiểm soát huyết áp.

# 3. TỔNG QUAN TÀI LIỆU

Các nghiên cứu trước [1] ở nước thu nhập cao.

# 7. TÀI LIỆU THAM KHẢO

1. Alpha A. Hypertension burden worldwide in adults. Lancet. 2020. PMID: 11111111.
"""


def _gioi_thieu(md: str) -> str:
    return md[md.index("## I. GIỚI THIỆU"):md.index("## II. PHƯƠNG PHÁP")]


def test_muc_tieu_tac_hai_cua_ban_thao_toi_duoc_bao_cao_tong_hop(tmp_path):
    """Bộ dựng báo cáo bỏ thân khối «§n» không nhãn (đề cương đã phủ); mục tiêu tác hại là câu bộ sinh G7 THÊM theo
    CONSORT 7 nên phải mang nhãn để sang được đặt vấn đề của báo cáo ⇒ K18 báo cáo đạt mục 7."""
    d = _meta(tmp_path / "exports" / STUDY, {})
    sap = {"ton_hai": "Biến cố bất lợi liên quan can thiệp: lo âu, phàn nàn"}
    md = _ban_thao(d, *RCT, sap_tom_tat=sap)
    _ghi(d / f"DE_CUONG_NOP_HOI_DONG_{STUDY}.md", DE_CUONG)
    _ghi(d / f"G7_A8_MANUSCRIPT_{STUDY}.md", "# Bài\n\n" + _gioi_thieu(md) + "## II. PHƯƠNG PHÁP\n\nThử nghiệm.\n\n"
                                              "## III. KẾT QUẢ\n\nKết quả.\n")
    van = B.sinh(STUDY, d)["van"]
    dvd = van[van.index("# ĐẶT VẤN ĐỀ"):van.index("# CHƯƠNG 1.")]
    assert "Mục tiêu về tác hại: nghiên cứu đồng thời mô tả tác hại (biến cố bất lợi) ở từng nhóm" in dvd
    assert _tt(van, "rct", "CONSORT 2025")["7"] == "dat"
    # đối chứng: SAP chưa định nghĩa tổn hại ⇒ bản thảo không nêu ⇒ báo cáo thiếu mục 7 (không câu mẫu)
    _ghi(d / f"G7_A8_MANUSCRIPT_{STUDY}.md", "# Bài\n\n" + _gioi_thieu(_ban_thao(d, *RCT)) + "## II. PHƯƠNG PHÁP\n\n"
                                              "Thử nghiệm.\n\n## III. KẾT QUẢ\n\nKết quả.\n")
    assert _tt(B.sinh(STUDY, d)["van"], "rct", "CONSORT 2025")["7"] == "thieu"


# ───────────────────── STROBE 2007 16a — Cox hiệu chỉnh nêu rõ biến hiệu chỉnh ─────────────────────
SONG_CON = {"survival": {"crude": {"HR": 1.423, "CI_95": [1.132, 1.789], "p": 0.0025},
                         "adjusted": {"HR": 1.419, "CI_95": [1.128, 1.784], "p": 0.0028},
                         "adjusted_covariates": ["tuoi", "corticoid", "loang_xuong"]}}


def test_cox_hieu_chinh_neu_bien_hieu_chinh_dat_yeu_to_16a():
    dong = "\n".join(G7._khoi_uoc_luong_g6(SONG_CON, "G6_analysis_summary.json"))
    assert "Cox hiệu chỉnh theo các hiệp biến tuoi, corticoid, loang_xuong: HR = 1.419" in dong
    yt = next(y for y in TB._GHI_DE[("STROBE 2007", "16a")]["yeu_to"] if y.ten == "biến được hiệu chỉnh")
    cau = next(x for x in dong.splitlines() if x.startswith("Cox hiệu chỉnh"))
    assert re.search(yt.mau, cau, re.IGNORECASE)
    # G6 không ghi danh sách hiệp biến ⇒ không nói «theo …» (không bịa biến)
    khong = dict(SONG_CON["survival"], adjusted_covariates=[])
    assert "Cox hiệu chỉnh: HR = 1.419" in "\n".join(G7._khoi_uoc_luong_g6({"survival": khong}, "x.json"))


# ───────────────────── RECORD 2015 mục 13.1 — lọc theo chất lượng/sẵn có của dữ liệu ─────────────────────
LUONG_THUAN_TAP = ("buoc,n,loai,nhanh,ly_do\nĐối tượng tiềm năng được tiếp cận,120,chinh,,\n"
                   "Không tham gia,10,loai,,Không đủ tiêu chuẩn: 10\nTham gia nghiên cứu,110,chinh,,\n"
                   "Loại khỏi phân tích,4,loai,,Thiếu dữ liệu kết cục chính: 4; Lý do khác: 0\n"
                   "Đưa vào phân tích,106,chinh,,\n")
G6_THIEU = {"hop_le": True, "nguon": "G6_analysis_summary.json", "tom_tat": {
    "missing_data": {"n_total": 106, "n_complete_cases": 90, "variables_with_missing": {
        "corticoid": {"n_missing": 10, "pct": 9.4}, "loang_xuong": {"n_missing": 8, "pct": 7.5}}},
    "multiple_imputation": {"n_imputations": 20, "n_missing_rows": 16}}}
_G1_TQ = {"data_collection_method": "Trích hồ sơ bệnh án điện tử theo phiếu trích",
          "intervention_or_exposure": "Dùng thuốc A liên tục ≥ 12 tháng theo đơn cấp phát",
          "primary_outcome": {"name": "Gãy xương", "measure": "Mã ICD-10 S72 có phim X-quang xác nhận"}}


def _thuan_tap(d: Path) -> str:
    return _ban_thao(d, "cohort", "Nghiên cứu Đoàn hệ (Cohort)", "STROBE + RECORD", ("RECORD",))


def test_record_13_1_chep_so_sang_loc_va_du_lieu_thieu_g6(tmp_path, monkeypatch):
    monkeypatch.setattr(G7, "doc_tom_tat_g6_hop_le", lambda out_dir: G6_THIEU)
    d = _meta(tmp_path, {"G1": _G1_TQ, "G2": {"recruitment_mode": "RETROSPECTIVE_SECONDARY_DATA"}})
    _ghi(d / f"SO_DO_LUONG_{STUDY}.csv", LUONG_THUAN_TAP)
    kq = "\n".join(G7.khoi_chuan_bao_cao_g7(d, STUDY, "cohort", None, ["RECORD"])["ket_qua"])
    assert ("4 hồ sơ bị loại vì thiếu dữ liệu kết cục chính (sổ sàng lọc, hộp «Loại khỏi phân tích»); 90/106 hồ sơ "
            "đưa vào phân tích đủ dữ liệu mọi biến phân tích; hồ sơ thiếu dữ liệu ở `corticoid` (10) và `loang_xuong` "
            "(8) được giữ lại và gán đa trị (m = 20, G6).") in kq
    assert "Lý do khác" not in kq and "Không đủ tiêu chuẩn" not in kq       # chỉ lý do thuộc nhóm dữ liệu
    assert _tt(_thuan_tap(d), "cohort", "RECORD 2015")["13.1"] == "dat"
    # không gán đa trị ⇒ nói đúng: hồ sơ thiếu không vào mô hình chính
    monkeypatch.setattr(G7, "doc_tom_tat_g6_hop_le", lambda out_dir: {**G6_THIEU, "tom_tat": {
        "missing_data": G6_THIEU["tom_tat"]["missing_data"]}})
    assert "không vào mô hình chính (phân tích ca đầy đủ, G6)" in "\n".join(G7._loc_du_lieu_record_g7(d, STUDY))


def test_record_13_1_vang_so_va_g6_thi_o_can_va_thieu(tmp_path, monkeypatch):
    monkeypatch.setattr(G7, "doc_tom_tat_g6_hop_le", lambda out_dir: {"hop_le": False})
    d = _meta(tmp_path, {"G1": _G1_TQ, "G2": {"recruitment_mode": "RETROSPECTIVE_SECONDARY_DATA"}})
    dong = G7._loc_du_lieu_record_g7(d, STUDY)
    assert any("[CẦN — số hồ sơ bị loại vì thiếu dữ liệu" in x for x in dong)
    assert _tt(_thuan_tap(d), "cohort", "RECORD 2015")["13.1"] == "thieu"
    # tiêu đề khối không làm bằng chứng giả
    yt = TB.danh_sach_muc_ban_thao("RECORD 2015", "cohort")
    mau = next(m for m in yt if m.ma == "13.1").yeu_to[0].mau
    assert not re.search(mau, dong[1], re.IGNORECASE)


# ───────────────────── CONSORT 2025 mục 24a — can thiệp như thực tế đã nhận ─────────────────────
def _luong_rct(nhan: bool = True) -> str:
    ra = ["buoc,n,loai,nhanh,ly_do", "Đánh giá đủ tiêu chuẩn,130,chinh,,",
          "Loại trừ,10,loai,,Không đủ tiêu chuẩn: 10; Từ chối tham gia: 0; Lý do khác: 0",
          "Phân bổ ngẫu nhiên,120,chinh,,"]
    for nh, khong, mat in (("Can thiệp", 2, 3), ("Chứng", 1, 2)):
        ra.append(f"Được phân bổ nhóm {nh.lower()},60,chinh,{nh},")
        if nhan:
            ra += [f"Không nhận can thiệp theo phân bổ,{khong},loai,{nh},Từ chối can thiệp: {khong}; Lý do khác: 0",
                   f"Nhận can thiệp theo phân bổ,{60 - khong},chinh,{nh},"]
            ra += [f"Mất theo dõi / ngừng can thiệp,{mat},loai,{nh},Mất liên lạc: {mat}; Rút đồng ý: 0; Lý do khác: 0",
                   f"Đưa vào phân tích,{60 - khong - mat},chinh,{nh},"]
        else:
            ra += [f"Mất theo dõi / ngừng can thiệp,{mat},loai,{nh},Mất liên lạc: {mat}",
                   f"Đưa vào phân tích,{60 - mat},chinh,{nh},"]
    return "\n".join(ra) + "\n"


def test_consort_24a_chep_so_thuc_te_nhan_can_thiep_tu_so_sang_loc(tmp_path):
    d = _meta(tmp_path, {})
    _ghi(d / f"SO_DO_LUONG_{STUDY}.csv", _luong_rct())
    kq = G7.khoi_consort_bo_sung_g7(d, STUDY, "rct")["ket_qua"]
    assert ("*Can thiệp và nhóm chứng như đã triển khai:* 58/60 người ở nhóm can thiệp và 59/60 người ở nhóm chứng "
            "thực tế nhận đúng can thiệp theo phân bổ (sổ sàng lọc).  ") in kq
    assert _tt(_ban_thao(d, *RCT), "rct", "CONSORT 2025")["24a"] == "dat"
    mau = TB._CONSORT["24a"][2][0].mau
    assert not re.search(mau, "**Can thiệp như đã thực hiện:**", re.IGNORECASE)   # tiêu đề không làm bằng chứng


def test_consort_24a_so_thieu_hop_nhan_can_thiep_thi_khong_in_va_thieu(tmp_path):
    d = _meta(tmp_path, {})
    _ghi(d / f"SO_DO_LUONG_{STUDY}.csv", _luong_rct(nhan=False))
    assert G7._can_thiep_thuc_te_g7(d, STUDY) == []
    assert G7.khoi_consort_bo_sung_g7(d, STUDY, "rct")["ket_qua"] == []
    assert _tt(_ban_thao(d, *RCT), "rct", "CONSORT 2025")["24a"] == "thieu"
    assert G7.khoi_consort_bo_sung_g7(d, STUDY, "cohort")["ket_qua"] == []          # không phải thử nghiệm


# ───────────────────── CHEERS 2022 mục 22–24 — kết quả kinh tế từ G6 ─────────────────────
KINH_TE = {"n": {"can_thiep": 110, "so_sanh": 108}, "chi_phi_tb": {"can_thiep": 2382054.5454545454,
                                                                  "so_sanh": 1732101.851851852},
           "hieu_qua_tb": {"can_thiep": 0.7, "so_sanh": 0.5}, "delta_c": 649952.6936026935,
           "delta_e": 0.19999999999999996, "icer": 3249763.468013468,
           "goc_phan_tu": "Đông Bắc (tốn hơn, hiệu quả hơn) — tính ICER, so ngưỡng WTP", "nguong_wtp": 5000000.0,
           "nmb_tai_wtp": 350047.30639730627, "ci_95_delta_c": [542091.5951178452, 760654.2718855216],
           "ci_95_delta_e": [0.07949494949494948, 0.32929292929292925],
           "ci_95_nmb": [-293298.5101010101, 1056091.1026936024],
           "mat_phang_bootstrap_pct": {"dong_bac": 99.8, "dong_nam": 0.0, "tay_bac": 0.2, "tay_nam": 0.0},
           "ceac": [{"boi_so": 1.0, "wtp": 5000000.0, "ty_le_chi_phi_hieu_qua": 0.8525}],
           "bootstrap": {"so_lap": 2000, "hat_giong": 20261115, "kieu": "phi tham số, phân tầng theo nhánh"},
           "chuan_bao_cao": "CHEERS 2022 (PMID 35017145)",
           "ghi_chu": "CEAC là tần suất trong mẫu bootstrap — không phải xác suất Bayes."}


def test_kinh_te_g6_chep_bang_tham_so_theo_cach_trinh_bay_cua_g6():
    """Số chép theo đúng cách G6 trình bày ở `<gate>_ket_qua.md` (tiền làm tròn tới đồng, tỷ lệ 3 chữ số) — mọi số
    của khối có trong tóm tắt hoặc tệp kết quả G6; không còn chuỗi thập phân dài (guardrail R1 nhận là dãy định
    danh)."""
    import phan_tich_thiet_ke_dac_thu as PT

    tt = {"n_total": 218, "loai_dac_thu": "kinh_te", "dac_thu": KINH_TE}
    van = "\n".join(G7._khoi_uoc_luong_g6(tt, "G6_KT_analysis_summary.json"))
    assert "| Chi phí gia tăng ΔC | 649.953 | 542.092 đến 760.654 |" in van
    assert "| Chi phí trung bình mỗi người — nhánh can thiệp | 2.382.055 |" in van
    assert "| Hiệu quả gia tăng ΔE | 0,200 | 0,079 đến 0,329 |" in van
    assert "| ICER = ΔC/ΔE | 3.249.763 | — |" in van and "| 350.047 | -293.299 đến 1.056.091 |" in van
    assert "WTP 5.000.000 → 0,853" in van and "Đông Bắc 99,8%" in van
    md_g6 = PT.md_ket_qua("THU", "G6_KT", "kinh_te", KINH_TE, None)
    assert G7.kiem_so_trich_g6(van, json.dumps(tt, ensure_ascii=False) + "\n" + md_g6) == []
    assert not re.search(r"\b\d{9,12}\b", van)                                  # không dãy số dài
    for ma in ("22", "23", "24"):
        mau = next(m for m in TB.danh_sach_muc_ban_thao("CHEERS 2022", "rct") if m.ma == ma).yeu_to[0].mau
        assert re.search(mau, van, re.IGNORECASE), ma
    khong = G7._khoi_dac_thu_g6("kinh_te", {**KINH_TE, "icer": None}, "x.json")
    assert "| ICER = ΔC/ΔE | không tính được — đọc theo góc phần tư | — |" in "\n".join(khong)


def test_kinh_te_qua_chi_muc_sap_g6_vao_ban_thao_va_qua_guardrail(tmp_path):
    """Đường thật: chỉ mục SAP G6 → `dung_ket_cuc_phu_g6` (tự kiểm với tóm tắt + `<gate>_ket_qua.md`) → bản thảo →
    guardrail. Trên giả lập trước bản vá, bảng chép số chưa làm tròn làm guardrail R1 chặn G7 (PII giả)."""
    import phan_tich_thiet_ke_dac_thu as PT

    sys.path.insert(0, str(ROOT / "tests"))
    from test_g7_tu_dien_ket_qua_g6_20261115 import SHA, _ghi_tom_tat, _manifest, _sinh, _tom_tat_nhi_phan

    out = tmp_path / "exports" / "THU"
    _manifest(out)
    _ghi_tom_tat(out, _tom_tat_nhi_phan())
    tt = {**_tom_tat_nhi_phan(), "gate": "G6_KT", "loai_dac_thu": "kinh_te", "dac_thu": KINH_TE}
    for k in ("primary_outcome", "multivariate", "multiple_imputation", "table1", "poisson_pr"):
        tt.pop(k, None)
    _ghi_tom_tat(out, tt, "G6_KT_analysis_summary.json")
    _ghi(out / "G6_KT_ket_qua.md", PT.md_ket_qua("THU", "G6_KT", "kinh_te", KINH_TE, None))
    _ghi(out / G7.TEP_SAP_KET_QUA_G6, json.dumps(
        {"study": "THU", "du_lieu_khoa": {"tep": "x.csv", "sha256": SHA}, "phan_tich": [
            {"id": "KT", "vai": "phu", "sap_muc": "§16", "trang_thai": "DA_CHAY", "gate": "G6_KT"}]}))
    dong = G7.dung_ket_cuc_phu_g6(out)
    text = "\n".join(dong)
    assert "| Chi phí gia tăng ΔC | 649.953 | 542.092 đến 760.654 |" in text and "[CẦN THỐNG KÊ VIÊN" not in text
    kq = G7.dung_ket_qua_tu_g6(G7.doc_tom_tat_g6_hop_le(out))
    kq["s4"] = dong
    errors = G7.guardrail_g7(_sinh(ket_qua_g6=kq))[0]
    assert not any(e.startswith("R1") for e in errors), errors
    # thiếu tệp kết quả G6 ⇒ số trình bày không đối chiếu được ⇒ ô thống kê viên (fail-closed)
    (out / "G6_KT_ket_qua.md").unlink()
    assert "tự kiểm: số không có nguyên văn" in "\n".join(G7.dung_ket_cuc_phu_g6(out))


# ───────────────────── CHEERS 2022 mục 4, 8, 10, 13, 18, 19 — phương pháp kinh tế từ SAP §16 ─────────────────────
KT_DU = {"loai_phan_tich": "Phân tích chi phí–hiệu quả (CEA) đi kèm thử nghiệm, trên dữ liệu cá thể",
         "perspective": "Cơ sở y tế (chi phí trực tiếp y tế do phòng khám chi trả)",
         "comparator": "Chăm sóc thường quy — nhánh chứng của thử nghiệm",
         "time_horizon": "6 tháng, bằng thời gian theo dõi (không ngoại suy)",
         "discounting": "Không chiết khấu — khung thời gian ≤ 1 năm", "currency_year": "VND, giá năm 2026",
         "cost_items": "Khám, thuốc hạ áp, xét nghiệm theo dõi (biểu giá dịch vụ của bệnh viện)",
         "effect_measure": "Thêm một người đạt kiểm soát huyết áp tại tháng 6 (đơn vị tự nhiên)",
         "outcome_valuation": "Không định giá theo thoả dụng: hiệu quả tính bằng đơn vị tự nhiên",
         "wtp": "5.000.000 VND cho thêm một người đạt kiểm soát huyết áp",
         "wtp_source": "Chủ nhiệm ấn định cho đơn vị tự nhiên",
         "heterogeneity": "Không ước lượng chi phí–hiệu quả theo phân nhóm: cỡ mẫu không đủ lực",
         "distributional_effects": "Không phân tích phân bố tác động theo nhóm thu nhập hay vùng",
         "patient_involvement": "Không có người bệnh tham gia thiết kế phân tích kinh tế",
         "bien_nhom": "nhom", "bien_chi_phi": "chi_phi_6t", "bien_hieu_qua": "kiem_soat_t6"}
MUC_CHEERS = ("4", "8", "10", "13", "18", "19")


def _sap_kinh_te(d: Path, kt: dict) -> None:
    _ghi(d / f"G4_A5_SAP_FINAL_{STUDY}.md", "## PHẦN 3, SAP\n\n### §15 TỔN HẠI\n\n- **Cách đánh giá:** Hỏi chủ động\n"
         + "\n".join(G4A.muc_kinh_te(kt)) + "\n## PHẦN 4, THAY ĐỔI SAU KHI KHÓA\n")


def test_kinh_te_phuong_phap_chep_sap_16_dat_cheers(tmp_path):
    d = _meta(tmp_path, {})
    _sap_kinh_te(d, KT_DU)
    pp = "\n".join(G7.khoi_chuan_bao_cao_g7(d, STUDY, "rct", None, [])["phuong_phap"])
    assert "*Quan điểm phân tích (perspective):* Cơ sở y tế (chi phí trực tiếp y tế do phòng khám chi trả).  " in pp
    assert "*Chiết khấu:* Không chiết khấu — khung thời gian ≤ 1 năm.  " in pp
    assert "*Cách quy đổi kết cục hiệu quả:* Không định giá theo thoả dụng" in pp
    assert "*Phân tích chính:* ICER = ΔC/ΔE" in pp and "[CẦN" not in pp
    tt = _tt(_ban_thao(d, *RCT), "rct", "CHEERS 2022")
    assert {m: tt[m] for m in MUC_CHEERS} == {m: "dat" for m in MUC_CHEERS}, tt


def test_kinh_te_sap_thieu_ba_muc_moi_thi_o_can_va_thieu(tmp_path):
    """SAP cũ (chưa có chỗ khai CHEERS 13, 18, 19) hoặc chủ nhiệm chưa khai ⇒ ô [CẦN] cùng dòng nhãn; nhãn bản thảo
    không mang từ khoá của mục nên K18 vẫn báo thiếu đúng ba mục."""
    d = _meta(tmp_path, {})
    # đơn vị hiệu quả QALY (cần định giá theo thoả dụng) — đơn vị tự nhiên tự nó đã trả lời CHEERS 13 (tiêu chí K18)
    _sap_kinh_te(d, {**{k: v for k, v in KT_DU.items()
                        if k not in ("outcome_valuation", "heterogeneity", "distributional_effects")},
                     "effect_measure": "Số QALY tránh được trong 6 tháng", "wtp_source": "Chủ nhiệm ấn định"})
    pp = "\n".join(G7._khoi_kinh_te_g7(d, STUDY))
    assert pp.count("[CẦN — ") == 3 and "khai ở SAP §16" in pp
    tt = _tt(_ban_thao(d, *RCT), "rct", "CHEERS 2022")
    assert {m: tt[m] for m in MUC_CHEERS} == {"4": "dat", "8": "dat", "10": "dat", "13": "thieu", "18": "thieu",
                                               "19": "thieu"}, tt


def test_khong_co_sap_16_thi_khong_in_khoi_kinh_te(tmp_path):
    d = _meta(tmp_path, {})
    _ghi(d / f"G4_A5_SAP_FINAL_{STUDY}.md", "### §15 TỔN HẠI\n\n- **Cách đánh giá:** Hỏi chủ động\n")
    assert G7._khoi_kinh_te_g7(d, STUDY) == [] and G7._khoi_kinh_te_g7(tmp_path / "khong", STUDY) == []


def test_sap_16_co_cho_khai_ba_muc_cheers_moi():
    khoa = [k for k, _n, _g in G4A.KINH_TE_O]
    assert {"outcome_valuation", "heterogeneity", "distributional_effects"} <= set(khoa)
    sap = "\n".join(G4A.muc_kinh_te({"perspective": "x"}))
    assert "Định giá kết cục hiệu quả (CHEERS 2022 mục 13):** [CẦN BÁC SĨ" in sap


# ───────────────────── dữ kiện giả lập (vai người khai) ─────────────────────
def test_gia_lap_bien_the_khai_du_cho_cac_muc_chuan():
    import gia_lap_bien_the_kho as BTK

    kb = BTK.kich_ban_kho()
    mau19 = TB._CONSORT["19"][2][0].mau
    assert re.search(mau19, kb["rct_cum"]["pi"]["G1"]["allocation_concealment"], re.IGNORECASE)
    kt = kb["rct_kinh_te"]["pi"]["G1"]["economic_evaluation"]
    assert all(kt.get(k) for k, _n, _g in G4A.KINH_TE_O)


# ───────────────────── RECORD 2015 mục 19.1 — sai lệch đã chốt ở G1 kèm chiều tác động ─────────────────────
SAI_LECH_G1 = [
    {"sai_lech": "Nhiễu do chỉ định: người dùng thuốc A có nhiều bệnh kèm hơn", "bien_phap": "Hiệu chỉnh theo DAG",
     "chieu": "Nhiễu còn sót có thể làm nguy cơ tương đối được ước lượng cao hơn thực tế"},
    {"sai_lech": "Sai lệch phân loại phơi nhiễm từ đơn cấp phát (thuốc mua ngoài không được ghi nhận)",
     "bien_phap": "Định nghĩa phơi nhiễm ≥ 80% số ngày có thuốc",
     "chieu": "Phân loại sai không phân biệt theo kết cục kéo ước lượng về giá trị 1 (thấp hơn thực tế)"},
    {"sai_lech": "Sai lệch chọn do chuyển nơi khám", "bien_phap": "Phân tích độ nhạy"}]   # không khai chiều ⇒ bỏ


def _mau(chuan: str, ma: str, tk: str = "cohort"):
    return next(m for m in TB.danh_sach_muc_ban_thao(chuan, tk) if m.ma == ma).yeu_to


def test_record_19_1_chep_sai_lech_va_chieu_da_chot_o_g1(tmp_path, monkeypatch):
    monkeypatch.setattr(G7, "doc_tom_tat_g6_hop_le", lambda out_dir: {"hop_le": False})
    d = _meta(tmp_path, {"G1": {**_G1_TQ, "bias_controls": SAI_LECH_G1},
                         "G2": {"recruitment_mode": "RETROSPECTIVE_SECONDARY_DATA"}})
    bl = G7.khoi_chuan_bao_cao_g7(d, STUDY, "cohort", None, ["RECORD"])["ban_luan_han_che"]
    assert bl[0].startswith("*Dữ liệu thường quy:* dữ liệu trích từ nguồn có sẵn (trích hồ sơ bệnh án điện tử theo "
                            "phiếu trích), vốn được ghi nhận cho mục đích chăm sóc người bệnh")
    assert bl[1] == ("*Sai lệch tiềm ẩn đã xác định ở thiết kế và chiều tác động có thể có:* Nhiễu do chỉ định: "
                     "người dùng thuốc A có nhiều bệnh kèm hơn — nhiễu còn sót có thể làm nguy cơ tương đối được ước "
                     "lượng cao hơn thực tế; Sai lệch phân loại phơi nhiễm từ đơn cấp phát (thuốc mua ngoài không được "
                     "ghi nhận) — phân loại sai không phân biệt theo kết cục kéo ước lượng về giá trị 1 (thấp hơn thực "
                     "tế).  ")
    assert "chuyển nơi khám" not in "\n".join(bl)                         # mục không khai chiều không in
    md = _thuan_tap(d)
    assert _tt(md, "cohort", "RECORD 2015")["19.1"] == "dat"
    assert _tt(md, "cohort", "STROBE 2007")["19"] == "dat"
    # nhãn dòng không mang từ khoá của RECORD 19.1 (bằng chứng phải nằm ở lời khai đã chốt)
    assert not re.search(_mau("RECORD 2015", "19.1")[1].mau, bl[1].split(":*")[0], re.IGNORECASE)


def test_record_19_1_khong_khai_sai_lech_thi_khong_cau_mau_va_thieu(tmp_path, monkeypatch):
    monkeypatch.setattr(G7, "doc_tom_tat_g6_hop_le", lambda out_dir: {"hop_le": False})
    khong_chieu = [{k: v for k, v in x.items() if k != "chieu"} for x in SAI_LECH_G1]
    d = _meta(tmp_path, {"G1": {**_G1_TQ, "bias_controls": khong_chieu},
                         "G2": {"recruitment_mode": "RETROSPECTIVE_SECONDARY_DATA"}})
    bl = G7.khoi_chuan_bao_cao_g7(d, STUDY, "cohort", None, ["RECORD"])["ban_luan_han_che"]
    assert len(bl) == 1 and "chiều tác động" not in bl[0]
    assert _tt(_thuan_tap(d), "cohort", "RECORD 2015")["19.1"] == "thieu"
    # không phải hồi cứu trên dữ liệu thứ cấp ⇒ giữ ô [CẦN] như trước, không in sai lệch
    d2 = _meta(tmp_path / "tien_cuu", {"G1": {**_G1_TQ, "bias_controls": SAI_LECH_G1}, "G2": {}})
    bl2 = G7.khoi_chuan_bao_cao_g7(d2, STUDY, "cohort", None, ["RECORD"])["ban_luan_han_che"]
    assert len(bl2) == 1 and "[CẦN — hệ quả của việc dùng dữ liệu" in bl2[0]


def test_gia_lap_thuan_tap_hoi_cuu_da_chot_sai_lech_kem_chieu():
    """Hai biến thể thuần tập hồi cứu kế thừa sai lệch đã chốt ở G1 của kịch bản gốc — mỗi mục có chiều tác động, có
    mục phân loại sai từ dữ liệu thường quy (nguồn dữ kiện của dòng RECORD 19.1 trong bản thảo)."""
    import gia_lap_bien_the_kho as BTK

    kb = BTK.kich_ban_kho()
    for ma in ("thuan_tap_song_con", "thuan_tap_mi"):
        sl = G7._sai_lech_chot_g7({}, kb[ma]["pi"]["G1"])
        assert re.search(_mau("RECORD 2015", "19.1")[1].mau, sl, re.IGNORECASE), ma


# ───────────────────── Phần mở rộng CONSORT 2010 — không kém hơn (Piaggio 2012) và theo cụm (Campbell 2012) ─────────
NI_G1 = {"ni_rationale": ("Chọn thiết kế không kém hơn vì tái khám qua điện thoại giảm đi lại và thời gian chờ cho "
                          "người bệnh"),
         "ni_constancy": ("Quần thể tương tự thử nghiệm đã xác lập hiệu quả (người tăng huyết áp ngoại trú); nhóm "
                          "chứng ở đề tài này khác can thiệp của thử nghiệm đó; kết cục tương tự (đạt đích huyết áp); "
                          "giả thuyết không kém hơn chỉ áp cho kết cục chính")}
NI_G3 = {"hypothesis_type": "non_inferiority", "margin": 0.10,
         "margin_justification": "Biên cố định M1/M2: M1 ≈ 22 điểm %, giữ ≥ 50% hiệu ứng ⇒ M2 ≤ 11 điểm %"}


def test_mo_rong_khong_kem_hon_chep_loi_khai_g1_g3(tmp_path):
    d = _meta(tmp_path, {"G1": NI_G1, "G3": NI_G3})
    k = G7.khoi_chuan_bao_cao_g7(d, STUDY, "rct", None, [])
    pp3 = "\n".join(k["phuong_phap_3"])
    assert f"*Lý do chọn thiết kế không kém hơn:* {NI_G1['ni_rationale']}.  " in pp3
    assert "*Lý do chọn biên không kém hơn:* Biên cố định M1/M2" in "\n".join(k["phuong_phap"])
    kq18 = TB.doi_chieu_ban_thao(_ban_thao(d, *RCT), "rct", co_so_lieu=True)
    tt = {r.ma: r for r in kq18["ket_qua"] if r.chuan == "CONSORT NI 2012"}
    assert {m: tt[m].trang_thai for m in ("2a", "4a", "5", "6a")} == {m: "dat" for m in ("2a", "4a", "5", "6a")}
    # 2b: vế giả thuyết kèm biên do câu giả thuyết G0 (ô ở bộ dựng thử này); vế lý do chọn biên do dòng G3 trên
    assert "lý do chọn biên" not in tt["2b"].thieu, tt["2b"].thieu
    # chưa khai ⇒ ô [CẦN] cùng dòng nhãn, K18 vẫn thiếu (không câu mẫu)
    d2 = _meta(tmp_path / "rong", {"G3": {"hypothesis_type": "non_inferiority", "margin": 0.10}})
    tt2 = _tt(_ban_thao(d2, *RCT), "rct", "CONSORT NI 2012")
    assert {m: tt2[m] for m in ("2a", "4a", "5", "6a")} == {m: "thieu" for m in ("2a", "4a", "5", "6a")}, tt2
    assert G7.khoi_chuan_bao_cao_g7(_meta(tmp_path / "vt", {"G1": NI_G1}), STUDY, "rct", None, [])["phuong_phap_3"] \
        == []                                                                       # thử nghiệm vượt trội: không in


CUM_G1 = {"cluster_definition": ("Cụm là phòng khám ngoại trú; can thiệp triển khai ở mức cụm, còn mục tiêu và kết cục "
                                 "chính đánh giá ở mức cá nhân người bệnh"),
          "cluster_eligibility": ["Phòng khám thuộc chương trình", "Mỗi tháng có ít nhất 8 người đủ tiêu chuẩn"],
          "cluster_consent": ("Lãnh đạo phòng khám ký đồng ý trước khi ngẫu nhiên hoá cụm; người bệnh ký phiếu đồng ý "
                              "sau khi phòng khám đã được phân bổ")}
CUM_G3 = {"icc": 0.05, "cluster_size": 4, "n_clusters": 4, "equal_cluster_sizes": True,
          "icc_source": "PMID: 15485730 — ICC huyết áp tâm thu 0–0,052; chọn 0,05 (cận trên)"}
SAP_CUM = ("### §4 PHÂN TÍCH CHÍNH\n\n- **Hiệu chỉnh cụm:** phân tích chính phải tính cấu trúc cụm — Hồi quy Poisson "
           "với sai số chuẩn theo cụm, phòng khám là cụm\n\n### §5 PHÂN TÍCH ĐA BIẾN\n")
LUONG_CUM = ("buoc,n,loai,nhanh,ly_do\nĐánh giá đủ tiêu chuẩn,18,chinh,,\nLoại trừ,2,loai,,Không đủ tiêu chuẩn: 2\n"
             "Phân bổ ngẫu nhiên,16,chinh,,\nĐược phân bổ nhóm can thiệp,8,chinh,Can thiệp,\n"
             "Nhận can thiệp theo phân bổ,8,chinh,Can thiệp,\nMất theo dõi / ngừng can thiệp,0,loai,Can thiệp,\n"
             "Đưa vào phân tích,8,chinh,Can thiệp,\nĐược phân bổ nhóm chứng,8,chinh,Chứng,\n"
             "Nhận can thiệp theo phân bổ,8,chinh,Chứng,\nMất theo dõi / ngừng can thiệp,1,loai,Chứng,Mất liên lạc: 1\n"
             "Đưa vào phân tích,7,chinh,Chứng,\n")
G6_CUM = {"hop_le": True, "nguon": "G6_analysis_summary.json", "tom_tat": {
    "dac_ta_phan_tich": {"group": "nhom"}, "table1": {"n_per_group": {"0": 7, "1": 8}},
    "icc_cluster": {"cot_cum": "ma_pk", "so_cum": 4, "n": 15, "co_cum_trung_binh": 3.75, "co_cum_min": 3,
                    "co_cum_max": 4, "icc": 0.0467, "hieu_ung_thiet_ke": 1.14}}}
MUC_CUM = ("1b", "2b", "3a", "4a", "5", "6a", "7a", "10c", "12a", "13a", "13b", "17a")


def _de_tai_cum(d: Path, g1: dict = CUM_G1, sha_lech: bool = False) -> Path:
    import hashlib

    _meta(d, {"G1": g1, "G3": CUM_G3})
    _ghi(d / f"G4_A5_SAP_FINAL_{STUDY}.md", SAP_CUM)
    _ghi(d / f"SO_DO_LUONG_{STUDY}.csv", LUONG_CUM)
    du_lieu = "nhom,ma_pk,y\n" + "".join(f"{g},{pk},1\n" for g, pk, n in (("1", "A", 4), ("1", "B", 4),
                                                                         ("0", "C", 4), ("0", "D", 3))
                                       for _ in range(n))
    _ghi(d / "05_clean_locked/df.locked.csv", du_lieu)
    sha = hashlib.sha256((d / "05_clean_locked/df.locked.csv").read_bytes()).hexdigest()
    _ghi(d / "DATA_LOCK_manifest.json", json.dumps({"locked_dataset_path": "05_clean_locked/df.locked.csv",
                                                    "sha256": "0" * 64 if sha_lech else sha}))
    return d


def test_mo_rong_cum_chep_g1_g3_sap_g6_du_lieu_khoa_va_so_sang_loc(tmp_path, monkeypatch):
    monkeypatch.setattr(G7, "doc_tom_tat_g6_hop_le", lambda out_dir: G6_CUM)
    d = _de_tai_cum(tmp_path)
    rv = [{"variable": "nhom", "choices": "1, Tin nhắn | 0, Chăm sóc thường quy"}]
    k = G7.khoi_chuan_bao_cao_g7(d, STUDY, "rct", rv, [])
    kq = "\n".join(k["ket_qua"])
    assert ("*Số cụm theo nhóm:* 2 cụm vào nhóm chăm sóc thường quy (7 người) và 2 cụm vào nhóm tin nhắn (8 người) "
            "được phân bổ và đưa vào phân tích kết cục chính; tổng 4 cụm, n = 15") in kq
    assert "không cụm nào rút khỏi nghiên cứu (số cụm phân tích/theo kế hoạch đã chốt ở G3: 4/4)" in kq
    assert "0 người ở nhóm can thiệp và 1 người ở nhóm chứng mất theo dõi" in kq
    assert "ICC = 0,0467; hiệu ứng thiết kế 1,14" in kq  # 23/11/2026: số G6 kiểu Việt (hien_so_g6)
    assert ("*Cách tính cấu trúc cụm trong phân tích (SAP §4):* phân tích chính phải tính cấu trúc cụm — Hồi quy "
            "Poisson với sai số chuẩn theo cụm") in "\n".join(k["phuong_phap"])
    assert k["tom_tat"][0].startswith("**Clusters:** 4 cụm được phân bổ ngẫu nhiên theo cụm")
    kq18 = TB.doi_chieu_ban_thao(_ban_thao_cum(d, rv).replace(G7.NHAN_DOI_CHIEU_G6, ""), "rct", co_so_lieu=True)
    tt = {r.ma: r for r in kq18["ket_qua"] if r.chuan == "CONSORT Cluster 2012"}
    assert {m: tt[m].trang_thai for m in MUC_CUM} == {m: "dat" for m in MUC_CUM}, \
        {m: (tt[m].trang_thai, tt[m].thieu) for m in MUC_CUM}
    assert "đặc điểm nền mức cụm" not in tt["15"].thieu                           # mức cá nhân do Bảng 1 G6 (giả lập)


def _ban_thao_cum(d: Path, rv: list) -> str:
    kw = dict(study=STUDY, topic="Chương trình tin nhắn theo phòng khám: thử nghiệm ngẫu nhiên theo cụm", n_sr=1,
              n_rct=1, n_guideline=0, research_gaps=["còn thiếu dữ liệu"], pmids=["11111111"], pmid_meta={},
              design_code="rct", design_primary=RCT[1], reporting_std=RCT[2], irb_number="GL-1/2026",
              icf_version="1.0", registration="Không đăng ký — không bắt buộc", n_total=16, n_adjusted=16, alpha=0.05,
              power=0.8, effect_val=None, effect_type="RR", formula_used="", g4_status="LOCKED",
              g4_lock_date="2026-11-01", target_journal="Tạp chí Y học Việt Nam", word_limit=3500,
              run_date="2026-11-22",
              khoi_consort=G7.khoi_consort_bo_sung_g7(d, STUDY, "rct"),
              khoi_chuan=G7.khoi_chuan_bao_cao_g7(d, STUDY, "rct", rv, []))
    van, _da = G7.lap_o_da_chot_g7(G7.generate_manuscript(**kw), d, STUDY)
    return van


def test_mo_rong_cum_thieu_du_kien_thi_o_can_khong_so(tmp_path, monkeypatch):
    """G1 chưa khai cụm ⇒ ô [CẦN]; dữ liệu khoá sai sha256 ⇒ không đếm cụm theo nhóm (không in số cụm/nhóm)."""
    monkeypatch.setattr(G7, "doc_tom_tat_g6_hop_le", lambda out_dir: G6_CUM)
    d = _de_tai_cum(tmp_path, g1={}, sha_lech=True)
    k = G7.khoi_chuan_bao_cao_g7(d, STUDY, "rct", None, [])
    pp3 = "\n".join(k["phuong_phap_3"])
    assert pp3.count("[CẦN — ") == 3 and "Cụm là" not in pp3
    assert "Số cụm theo nhóm" not in "\n".join(k["ket_qua"]) and k["tom_tat"] == []
    assert G7._cum_theo_nhom_g7(d, "ma_pk", "nhom") == {}
    tt = _tt(_ban_thao_cum(d, None), "rct", "CONSORT Cluster 2012")
    assert {m: tt[m] for m in ("3a", "4a", "10c", "13a")} == {m: "thieu" for m in ("3a", "4a", "10c", "13a")}, tt
