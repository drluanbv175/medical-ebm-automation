# -*- coding: utf-8 -*-
"""Bộ sinh G7 — các mục chuẩn báo cáo K18 còn báo thiếu trên 5 thiết kế (22/11/2026, chiều).

Đo trên gói giả lập trọn vòng 8 kịch bản (mã trước bản vá): RCT thiếu CONSORT 2025 mục 3, 4, 10, 20b; thuần tập dữ liệu
thường quy thiếu RECORD 1.1, 6.2, 7.1, 12.1, 12.2, 19.1; chẩn đoán thiếu STARD 3, 11, 12a, 12b, 21a, 21b, 29; dự báo
thiếu TRIPOD+AI 3b, 3c, 6c, 7, 8c, 15, 18c, 18e, 18f, 19, 22, 27a, 27b; tổng quan thiếu PRISMA 2 (A5, A7, A9), 7, 11,
16a, 16b, 17, 22, 24b, 24c. Luật liêm chính: mọi dòng chép dữ kiện CÓ THẬT của hồ sơ (G1, G2, đặc tả PI ở study_meta,
khai báo tác giả G7, báo cáo làm sạch G5, quy trình dữ liệu đã chốt, tóm tắt G6 hợp lệ, bảng trích xuất); vắng ⇒ ô
«[CẦN — …]» nói rõ thiếu gì (K18 vẫn báo thiếu — trung thực). Kèm hai việc điều phối giao cùng đợt: (1) bảng kiểm cuối
bản thảo chỉ đánh ☑ khi K18 chấm «dat» (trước đây giả lập điền «☑ đã báo cáo trong bản thảo» vào mọi ô ☐ [CẦN]); (2)
kịch bản cắt ngang mô tả hết tự mâu thuẫn tên đề tài ↔ mục tiêu.
"""
from __future__ import annotations

import ast
import inspect
import json
import re
import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import go_khung_ban_thao_g7 as GK  # noqa: E402
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
              khoi_chuan=G7.khoi_chuan_bao_cao_g7(d, STUDY, tk, them.pop("redcap_vars", None), list(ext)), **them)
    van, _da = G7.lap_o_da_chot_g7(G7.generate_manuscript(**kw), d, STUDY)
    return van


def _nop(md: str) -> str:
    """Như tác giả ở giả lập: đối chiếu xong số G6 thì gỡ nhãn «[CẦN KẾT QUẢ THẬT — đối chiếu G6]»."""
    return md.replace(G7.NHAN_DOI_CHIEU_G6, "")


def _tt(md: str, tk: str, chuan: str) -> dict:
    """{mã: trạng thái} của một chuẩn — chế độ NỘP (ô [CẦN] thành ô trống, như bản thảo đã gỡ khung)."""
    kq = TB.doi_chieu_ban_thao(_nop(md), tk, co_so_lieu=True)
    return {r.ma: r.trang_thai for r in kq["ket_qua"] if r.chuan == chuan}


TAC_GIA = {"data_sharing_statement": ("Dữ liệu cá thể không chia sẻ công khai; mã phân tích (kịch bản R) và từ điển dữ "
                                      "liệu được cung cấp theo yêu cầu gửi tác giả liên lạc"),
           "protocol_access_statement": ("Đề cương nghiên cứu và kế hoạch phân tích thống kê đã khoá được cung cấp "
                                         "theo yêu cầu gửi tác giả liên lạc"),
           "protocol_changes_statement": "Không có thay đổi nào so với đề cương và kế hoạch phân tích đã khoá"}


def _lam_sach(d: Path) -> None:
    _ghi(d / "03_cleaning_scripts/DATA_CLEANING_plan.json", json.dumps(
        {"required_columns": ["a", "b", "c"], "safe_actions": ["standardize_missing_token"],
         "forbidden_actions": ["no_row_drop_without_protocol"]}))
    _ghi(d / "DATA_CLEANING_report.json", json.dumps(
        {"ready_for_lock": True, "row_count": 120, "column_count": 3, "dictionary_loaded": True,
         "plan": "03_cleaning_scripts/DATA_CLEANING_plan.json", "open_query_count": 0, "pii_scan": {"passed": True}}))
    _ghi(d / "_quy-trinh-du-lieu.csv", "muc,gia_tri,nguon\nkiem_chung,Đối chiếu hai lượt nhập,G1\n")


# ───────────────────────────── CONSORT 2025: 3, 4, 10 (lời khai tác giả) ─────────────────────────────
def test_rct_khai_bao_tac_gia_dat_3_4_10_vang_thi_thieu(tmp_path):
    d = _meta(tmp_path / "co", {"G7": TAC_GIA})
    tt = _tt(_ban_thao(d, "rct", "Thử nghiệm lâm sàng ngẫu nhiên có đối chứng (RCT)", "CONSORT 2025"), "rct",
             "CONSORT 2025")
    assert (tt["3"], tt["4"], tt["10"]) == ("dat", "dat", "dat"), tt
    rong = _meta(tmp_path / "rong", {})
    md = _ban_thao(rong, "rct", "Thử nghiệm lâm sàng ngẫu nhiên có đối chứng (RCT)", "CONSORT 2025")
    tt = _tt(md, "rct", "CONSORT 2025")
    assert (tt["3"], tt["4"], tt["10"]) == ("thieu", "thieu", "thieu"), tt
    # vắng lời khai ⇒ ô nói rõ thiếu gì, KHÔNG còn câu khuôn «có thể cung cấp theo yêu cầu hợp lý…»
    assert "có thể cung cấp theo yêu cầu" not in md
    assert G7._o_can("tuyên bố chia sẻ dữ liệu: dữ liệu cá nhân đã khử định danh, mã phân tích, nơi và cách truy cập, "
                     "hoặc lý do không chia sẻ") in md


def test_loi_khai_khong_thay_doi_mau_thuan_bang_thay_doi_sap_thi_khong_in(tmp_path):
    d = _meta(tmp_path, {"G7": TAC_GIA})
    _ghi(d / f"G4_A5_SAP_FINAL_{STUDY}.md", "## PHẦN 4, THAY ĐỔI SAU KHI KHÓA\n\n| Ngày | Mô tả thay đổi | Loại |\n"
                                            "|---|---|---|\n| 02/05/2027 | Thêm phân tích độ nhạy | THĂM DÒ |\n")
    pp = "\n".join(G7.khoi_consort_bo_sung_g7(d, STUDY, "rct")["phuong_phap"])
    assert "02/05/2027: Thêm phân tích độ nhạy" in pp
    assert "Không có thay đổi nào" not in pp and "mâu thuẫn với bảng thay đổi" in pp


# ───────────────────────────── RECORD 2015 ─────────────────────────────
_G1_THUONG_QUY = {"data_collection_method": "Trích hồ sơ bệnh án điện tử theo phiếu trích",
                  "intervention_or_exposure": "Dùng thuốc A liên tục ≥ 12 tháng theo đơn cấp phát",
                  "primary_outcome": {"name": "Gãy xương", "measure": "Mã ICD-10 S72 có phim X-quang xác nhận"}}
_PI_THUONG_QUY = {"routine_code_validation": "Đối chiếu mã ICD-10 với phim X-quang cho mọi ca",
                  "routine_database_access": "Nhóm nghiên cứu được đơn vị cấp quyền truy xuất hồ sơ bệnh án điện tử"}
MUC_RECORD = ("1.1", "6.2", "7.1", "12.1", "12.2", "19.1")


def _thuan_tap(d: Path, **kw) -> str:
    return _ban_thao(d, "cohort", "Nghiên cứu Đoàn hệ (Cohort)", "STROBE + RECORD", ("RECORD",), **kw)


def test_record_du_6_muc_tu_ho_so(tmp_path):
    d = _meta(tmp_path, {"G1": _G1_THUONG_QUY, "G2": {"recruitment_mode": "RETROSPECTIVE_SECONDARY_DATA"}},
              **_PI_THUONG_QUY)
    _lam_sach(d)
    md = _thuan_tap(d)
    # 19.1 có hai vế: «dữ liệu không thu thập cho câu hỏi này» (bộ sinh suy từ thiết kế hồi cứu dữ liệu thứ cấp) và hệ
    # quả phân loại sai/nhiễu/thiếu (tác giả bàn ở Hạn chế) — chưa có lời tác giả ⇒ chỉ thiếu vế sau
    kq = TB.doi_chieu_ban_thao(md, "cohort", co_so_lieu=True)
    r191 = next(r for r in kq["ket_qua"] if r.chuan == "RECORD 2015" and r.ma == "19.1")
    assert r191.thieu == ["phân loại sai/nhiễu không đo/thiếu"], r191.thieu
    md = md.replace("*Dữ liệu thường quy:*", "Phân loại sai phơi nhiễm từ đơn cấp phát có thể xảy ra.\n\n"
                                             "*Dữ liệu thường quy:*")
    tt = _tt(md, "cohort", "RECORD 2015")
    assert {m: tt[m] for m in MUC_RECORD} == {m: "dat" for m in MUC_RECORD}, tt
    assert "**Data source:** Trích hồ sơ bệnh án điện tử theo phiếu trích." in md
    assert ("*Làm sạch dữ liệu:* Bộ dữ liệu 120 dòng × 3 biến được làm sạch theo kế hoạch làm sạch đã lưu, đối chiếu "
            "từ điển dữ liệu; kiểm tra đủ 3 biến bắt buộc; chuẩn hoá mã giá trị thiếu; không xoá dòng khi đề cương "
            "chưa quy định; truy vấn dữ liệu còn mở khi khoá: 0; quét thông tin định danh đạt; kiểm chứng chất lượng "
            "thu thập: đối chiếu hai lượt nhập.") in md


def test_record_vang_dac_ta_thi_o_can_va_thieu(tmp_path):
    """PI chưa khai kiểm định mã / quyền truy cập, chưa có báo cáo làm sạch, không phải hồi cứu ⇒ ô [CẦN], K18 thiếu."""
    d = _meta(tmp_path, {"G1": _G1_THUONG_QUY, "G2": {}})
    md = _thuan_tap(d)
    tt = _tt(md, "cohort", "RECORD 2015")
    assert {m: tt[m] for m in ("6.2", "12.1", "12.2", "19.1")} == {m: "thieu" for m in ("6.2", "12.1", "12.2",
                                                                                         "19.1")}, tt
    assert md.count("[CẦN — ") >= 4 and "cấp quyền truy xuất" not in md


def test_khong_record_thi_khong_in_khoi_du_lieu_thuong_quy(tmp_path):
    d = _meta(tmp_path, {"G1": _G1_THUONG_QUY}, **_PI_THUONG_QUY)
    k = G7.khoi_chuan_bao_cao_g7(d, STUDY, "cohort", None, [])
    assert all(v == [] for v in k.values()), k


# ───────────────────────────── STARD 2015 ─────────────────────────────
_PI_CHAN_DOAN = {"index_test_role": "Xét nghiệm phân loại ban đầu trước khi chỉ định đo đàn hồi gan",
                 "reference_standard_rationale": "Đo đàn hồi gan được chọn vì làm được cho mọi người tham gia",
                 "index_threshold_rationale": "Ngưỡng 2,67 định trước trong SAP, dựa trên y văn gốc (PMID 19523535)",
                 "reference_threshold_rationale": "Ngưỡng 10 kPa được dùng vì tương ứng xơ hoá F3–F4",
                 "disease_severity_variable": "lsm_kpa"}
_G6_CHAN_DOAN = {"hop_le": True, "nguon": "G6_analysis_summary.json", "tom_tat": {
    "table1": {"n_per_group": {"0": 36, "1": 17}, "rows": [
        {"variable": "lsm_kpa", "gia_tri": {"0": "6.50 [4.92–7.78]", "1": "16.06 ± 2.87"}}]},
    "dac_thu": {"auc": {"auc": 0.6, "n_co_benh": 17, "n_khong_benh": 36}}}}


def test_stard_muc_3_11_12a_12b_21a_dat_21b_trung_thuc_thieu(tmp_path, monkeypatch):
    monkeypatch.setattr(G7, "doc_tom_tat_g6_hop_le", lambda out_dir: _G6_CHAN_DOAN)
    d = _meta(tmp_path, {"G1": {"reference_standard": "Đo độ đàn hồi gan ≥ 10 kPa"}, "G7": TAC_GIA}, **_PI_CHAN_DOAN)
    md = _ban_thao(d, "diagnostic", "Nghiên cứu Độ chính xác Chẩn đoán", "STARD 2015",
                   redcap_vars=[{"variable": "lsm_kpa", "label": "Độ đàn hồi gan (kPa)"}],
                   khoi_chan_doan_du_bao=G7._khoi_chan_doan_du_bao_g7(d, "diagnostic"))
    tt = _tt(md, "diagnostic", "STARD 2015")
    assert {m: tt[m] for m in ("3", "11", "12a", "12b", "21a", "29")} == {m: "dat" for m in
                                                                          ("3", "11", "12a", "12b", "21a", "29")}, tt
    # 21b: chưa có phân tích chẩn đoán khác trên dữ liệu đã khoá ⇒ ô [CẦN], K18 báo thiếu (không dựng số)
    assert tt["21b"] == "thieu"
    assert ("*Phân bố mức độ bệnh ở người có bệnh đích (Độ đàn hồi gan (kPa), `lsm_kpa`):* 16,06 ± 2,87 (n = 17) "
            + G7.NHAN_DOI_CHIEU_G6) in md


def test_stard_21a_khong_dung_so_khi_g6_chua_hop_le_hoac_nhom_mo_ho(tmp_path, monkeypatch):
    d = _meta(tmp_path, {}, **_PI_CHAN_DOAN)
    monkeypatch.setattr(G7, "doc_tom_tat_g6_hop_le", lambda out_dir: {"hop_le": False, "ly_do": "chưa khoá"})
    assert G7._phan_bo_muc_do_benh_g7(d, G7._doc_meta_g7(d), None).count("[CẦN — ") == 1
    hai_nhom_bang = json.loads(json.dumps(_G6_CHAN_DOAN))
    hai_nhom_bang["tom_tat"]["table1"]["n_per_group"] = {"0": 17, "1": 17}
    monkeypatch.setattr(G7, "doc_tom_tat_g6_hop_le", lambda out_dir: hai_nhom_bang)
    assert "16.06" not in G7._phan_bo_muc_do_benh_g7(d, G7._doc_meta_g7(d), None)


# ───────────────────────────── TRIPOD+AI 2024 ─────────────────────────────
_PI_DU_BAO = {"model_intended_use": "Hỗ trợ bác sĩ phòng khám phân tầng nguy cơ; người dùng dự kiến là bác sĩ",
              "health_inequalities": "Chưa có dữ liệu trong nước về khác biệt giữa các nhóm dân số",
              "model_treatment_handling": "Điều trị không đưa vào mô hình làm yếu tố dự báo",
              "outcome_assessment_blinding": "Người xác định nhập viện không biết giá trị yếu tố dự báo",
              "model_output_threshold": "Mô hình cho xác suất nhập viện; không đặt ngưỡng phân loại",
              "model_input_handling": "Chưa áp dụng mô hình khi thiếu giá trị đầu vào",
              "model_user_interaction": "Người dùng nhập bốn giá trị có sẵn, không cần kỹ năng thống kê",
              "ppi_plan": "Không có sự tham gia của người bệnh hoặc công chúng trong thiết kế nghiên cứu"}
MUC_TRIPOD = ("3b", "3c", "6c", "7", "8c", "15", "18c", "18e", "18f", "19", "22", "27a", "27b")
_G6_DU_BAO = {"hop_le": True, "nguon": "G6_analysis_summary.json", "tom_tat": {"dac_thu": {"he_so": [
    {"bien": "(hằng số)", "beta": -4.28, "or": 0.01}, {"bien": "tuoi", "beta": 0.0384, "or": 1.04}]}}}


def test_tripod_13_muc_dat_khi_co_ho_so(tmp_path, monkeypatch):
    monkeypatch.setattr(G7, "doc_tom_tat_g6_hop_le", lambda out_dir: _G6_DU_BAO)
    d = _meta(tmp_path, {"G7": TAC_GIA}, **_PI_DU_BAO)
    _lam_sach(d)
    md = _ban_thao(d, "prediction", "Nghiên cứu phát triển mô hình dự báo", "TRIPOD+AI")
    tt = _tt(md, "prediction", "TRIPOD+AI 2024")
    assert {m: tt[m] for m in MUC_TRIPOD} == {m: "dat" for m in MUC_TRIPOD}, tt
    assert f"*Hệ số hồi quy đầy đủ của mô hình (β):* hằng số = -4,28; `tuoi` = 0,0384 {G7.NHAN_DOI_CHIEU_G6}" in md


def test_tripod_vang_ho_so_thi_o_can_va_thieu(tmp_path, monkeypatch):
    monkeypatch.setattr(G7, "doc_tom_tat_g6_hop_le", lambda out_dir: {"hop_le": False})
    d = _meta(tmp_path, {})
    md = _ban_thao(d, "prediction", "Nghiên cứu phát triển mô hình dự báo", "TRIPOD+AI")
    tt = _tt(md, "prediction", "TRIPOD+AI 2024")
    assert {m: tt[m] for m in MUC_TRIPOD} == {m: "thieu" for m in MUC_TRIPOD}, tt


# ───────────────────────────── PRISMA 2020 ─────────────────────────────
_PI_TONG_QUAN = {"search_strings_full": ('PubMed: ("Sodium-Glucose Transporter 2 Inhibitors"[MeSH] OR '
                                         'gliflozin*[tiab]) AND randomi*[tiab]; bộ lọc RCT, không giới hạn ngôn ngữ'),
                 "rob_assessment_process": "RoB 2 cho từng thử nghiệm; hai người đánh giá độc lập"}
_G6_GOP = {"hop_le": True, "nguon": "G6_analysis_summary.json", "tom_tat": {"dac_thu": {"k": 15,
                                                                                       "tong": {"nguoi": 79845}}}}
_SO_TQ = {"nhanh": {"": [{"buoc": "Bản ghi xác định qua cơ sở dữ liệu", "n": 557, "loai": "chinh"},
                         {"buoc": "Báo cáo bị loại", "n": 28, "loai": "loai",
                          "ly_do": [{"ly_do": "Sai quần thể", "n": 28}]},
                         {"buoc": "Nghiên cứu đưa vào tổng quan", "n": 15, "loai": "chinh"}]}}


def _tong_quan(d: Path) -> str:
    return _ban_thao(d, "sr_ma", "Tổng quan Hệ thống / Phân tích gộp", "PRISMA 2020",
                     khoi_tuyen_chon=G7.khoi_tuyen_chon_g7(_SO_TQ, "sr_ma"))


def test_prisma_a5_a7_7_11_16a_24b_24c_dat_16b_17_trung_thuc_thieu(tmp_path, monkeypatch):
    monkeypatch.setattr(G7, "doc_tom_tat_g6_hop_le", lambda out_dir: _G6_GOP)
    d = _meta(tmp_path, {"G7": TAC_GIA, "G2": {"registration_required": True}}, **_PI_TONG_QUAN)
    _ghi(d / "G2_checkpoint.json", json.dumps({"g2_registration": "CRD42099999999"}))
    _ghi(d / G7._TEP_TRICH_XUAT_TQ, "study,year,n.e\nTN01-2016,2016,10\n")
    md = _tong_quan(d)
    tt = _tt(md, "sr_ma", "PRISMA 2020")
    assert {m: tt[m] for m in ("7", "11", "16a", "24b", "24c")} == {m: "dat" for m in ("7", "11", "16a", "24b",
                                                                                         "24c")}, tt
    assert "**Included studies:** 15 nghiên cứu, 79845 người tham gia" in md
    assert "Xác định được 557 bản ghi qua tìm kiếm; 15 nghiên cứu được đưa vào tổng quan." in md
    assert "Đề cương tổng quan đã đăng ký tại CRD42099999999" in md
    # bảng trích xuất không có cột định danh bài báo, sổ sàng lọc chỉ có số đếm ⇒ ô [CẦN], K18 thiếu 16b, 17
    assert (tt["16b"], tt["17"]) == ("thieu", "thieu"), tt
    # A9 «Limitations» là ô tác giả viết ⇒ mục 2 còn thiếu A9 cho tới khi tác giả điền
    kq = TB.doi_chieu_ban_thao(_nop(md), "sr_ma", co_so_lieu=True)
    muc2 = next(r for r in kq["ket_qua"] if r.chuan == "PRISMA 2020" and r.ma == "2")
    assert not any("A5" in t or "A7" in t for t in muc2.thieu) and any("A9" in t for t in muc2.thieu), muc2.thieu
    dien = md.replace(G7._o_can("hạn chế chính của bằng chứng được đưa vào"), "Ít thử nghiệm lớn chi phối kết quả")
    kq = TB.doi_chieu_ban_thao(_nop(dien), "sr_ma", co_so_lieu=True)
    muc2 = next(r for r in kq["ket_qua"] if r.chuan == "PRISMA 2020" and r.ma == "2")
    assert not any(t.endswith(("(A5)", "(A7)", "(A9)")) for t in muc2.thieu), muc2.thieu


def test_prisma_17_dat_khi_bang_trich_xuat_co_cot_dinh_danh(tmp_path, monkeypatch):
    monkeypatch.setattr(G7, "doc_tom_tat_g6_hop_le", lambda out_dir: _G6_GOP)
    d = _meta(tmp_path, {}, **_PI_TONG_QUAN)
    _ghi(d / G7._TEP_TRICH_XUAT_TQ, "study,pmid\nTN01-2016,PMID 11111111\nTN02-2017,PMID 22222222\n")
    assert G7._trich_dan_nc_tong_quan_g7(d) == ("*Trích dẫn từng nghiên cứu được đưa vào:* TN01-2016 (PMID "
                                                "11111111); TN02-2017 (PMID 22222222).  ")
    _ghi(d / G7._TEP_TRICH_XUAT_TQ, "study,pmid\nTN01-2016,PMID 11111111\nTN02-2017,\n")  # thiếu một dòng ⇒ không in
    assert G7._trich_dan_nc_tong_quan_g7(d).count("[CẦN — ") == 1


# ───────────────────────────── bảng kiểm: ☑ chỉ khi K18 chấm đạt ─────────────────────────────
_CAT_NGANG = ("# Tỷ lệ X: nghiên cứu cắt ngang mô tả\n\n## TÓM TẮT\n\n**Phương pháp:** cắt ngang.\n\n"
              "**Kết quả:** 48,6% (KTC 95% 43,9–53,3).\n\n**Kết luận:** x.\n\n## I. GIỚI THIỆU\n\nx [1]. Nghiên cứu "
              "nhằm xác định tỷ lệ X.\n\n## II. PHƯƠNG PHÁP\n\nThiết kế cắt ngang mô tả.\n\n## III. KẾT QUẢ\n\n"
              "428 người. Phân tích yếu tố liên quan chưa phân tích ở đợt này.\n\n## IV. BÀN LUẬN\n\nx [2].\n\n"
              "## V. KẾT LUẬN\n\nx.\n")


def test_bang_kiem_khong_danh_dau_dat_muc_k18_bao_thieu(tmp_path):
    """Ví dụ điều phối: STROBE 16a (ước lượng thô + hiệu chỉnh) của cắt ngang mô tả — bản thảo ghi «chưa phân tích ở
    đợt này» ⇒ bảng kiểm KHÔNG được ☑; mục K18 chấm đạt mới ☑."""
    std, tong = G7.REPORTING_CHECKLISTS["cross_sectional"]
    k18 = G7.ket_qua_k18_g7(_CAT_NGANG, "cross_sectional")["STROBE 2007"]
    bk = G7.generate_checklist("cross_sectional", std, tong, "GL-1", "—", 428, 0.05, 0.8, md=_CAT_NGANG)
    dong = {ln.split("|")[1].strip(): ln for ln in bk.splitlines() if ln.startswith("| ")}
    assert k18["16a"].trang_thai != "dat" and G7.DAU_DAT_K18 not in dong["16a"], dong["16a"]
    assert "[CẦN" not in bk.split("## PHỤ LỤC", 1)[1].split("**Tổng kết", 1)[0]  # bảng không còn ô để «tick hộ»
    for ma, ln in dong.items():
        if ma in k18:
            assert (G7.DAU_DAT_K18 in ln) == (k18[ma].trang_thai == "dat"), (ma, ln)


def test_cham_lai_bang_kiem_sua_dau_tick_ho_cua_ban_cu(tmp_path):
    """Bản thảo cũ: giả lập đã điền «☑ đã báo cáo trong bản thảo» vào mọi dòng ⇒ chấm lại theo K18 trên bản nộp."""
    std, tong = G7.REPORTING_CHECKLISTS["cross_sectional"]
    bk = G7.generate_checklist("cross_sectional", std, tong, "GL-1", "—", 428, 0.05, 0.8, md=_CAT_NGANG)
    cu = re.sub(r"\| (☑ đã báo cáo|☐ chưa báo cáo|☐ chưa đo được|— không áp dụng) \| [^|\n]* \|$",
                "| ☑ đã báo cáo trong bản thảo | Bác sĩ điền khi có kết quả thật |", bk, flags=re.MULTILINE)
    assert cu.count("☑ đã báo cáo trong bản thảo") > 20
    moi, doi = G7.cap_nhat_bang_kiem_k18(_CAT_NGANG + cu, "cross_sectional")
    assert doi > 0 and "☑ đã báo cáo trong bản thảo" not in moi
    dong16a = next(ln for ln in moi.splitlines() if ln.startswith("| 16a |"))
    # cắt ngang mô tả không có mục tiêu phân tích liên quan ⇒ K18: «không áp dụng» — tuyệt đối không ☑
    assert "☑" not in dong16a and ("— không áp dụng" in dong16a or "☐ chưa báo cáo" in dong16a), dong16a
    assert G7.cap_nhat_bang_kiem_k18(moi, "cross_sectional") == (moi, 0)  # chấm lại lần hai không đổi gì


def test_go_khung_cham_lai_bang_kiem_theo_thiet_ke(tmp_path, monkeypatch):
    import gate_contract as GC

    monkeypatch.setattr(GC, "resolve_design_code", lambda out_dir, default="cohort": ("cross_sectional", None))
    std, tong = G7.REPORTING_CHECKLISTS["cross_sectional"]
    bk = G7.generate_checklist("cross_sectional", std, tong, "GL-1", "—", 428, 0.05, 0.8, md=_CAT_NGANG)
    cu = bk.replace("| 16a | ", "| 16a | ").replace("☐ chưa báo cáo", "☑ đã báo cáo trong bản thảo")
    moi, doi = GK.cham_lai_bang_kiem(_CAT_NGANG + cu, tmp_path)
    assert doi > 0 and "☑ đã báo cáo trong bản thảo" not in moi


def test_bang_kiem_mo_rong_record_theo_k18(tmp_path):
    d = _meta(tmp_path, {"G1": _G1_THUONG_QUY, "G2": {"recruitment_mode": "RETROSPECTIVE_SECONDARY_DATA"}},
              **_PI_THUONG_QUY)
    _lam_sach(d)
    md = _thuan_tap(d)
    k18 = G7.ket_qua_k18_g7(md, "cohort")
    khoi = G7.khoi_bang_kiem_mo_rong(["RECORD"], k18)
    assert "[CẦN điền theo bảng kiểm gốc]" not in khoi
    for ma, r in k18["RECORD 2015"].items():
        dong = next(ln for ln in khoi.splitlines() if ln.startswith(f"| {ma} — "))
        assert dong.endswith(f"| {G7.o_trang_thai_k18([r])[0]} |"), dong


def test_main_noi_khoi_chuan_va_cham_bang_kiem_tren_ban_thao():
    """Nối dây: main() truyền `khoi_chuan=khoi_chuan_bao_cao_g7(...)` cho bộ sinh và `md=manuscript` cho bảng kiểm."""
    cay = ast.parse(inspect.getsource(G7.main))
    goi = {getattr(n.func, "id", ""): n for n in ast.walk(cay) if isinstance(n, ast.Call)}
    kw_sinh = {k.arg: k.value for k in goi["generate_manuscript"].keywords}
    assert getattr(kw_sinh["khoi_chuan"].func, "id", "") == "khoi_chuan_bao_cao_g7"
    kw_bk = {k.arg: k.value for k in goi["generate_checklist"].keywords}
    assert getattr(kw_bk.get("md"), "id", "") == "manuscript"


# ───────────────────────────── kịch bản giả lập: tên đề tài ↔ mục tiêu ─────────────────────────────
_HUA_LIEN_QUAN = re.compile(r"yếu tố liên quan|mối liên quan|các yếu tố (nguy cơ|ảnh hưởng)", re.IGNORECASE)


def test_ten_de_tai_gia_lap_khong_hua_noi_dung_ma_muc_tieu_khong_co():
    """Chốt tất định cho bộ giả lập (22/11/2026, điều phối): tên đề tài nêu «yếu tố liên quan» thì phải có mục tiêu
    G1 phân tích liên quan. Lỗi cũ: «Tỷ lệ kiểm soát huyết áp và các yếu tố liên quan…» với một mục tiêu mô tả."""
    import gia_lap_dinh_ky as GL

    sai = []
    for ma, kb in GL.KICH_BAN.items():
        ten = str(kb.get("topic") or "")
        muc_tieu = " ".join(map(str, ((kb.get("pi") or {}).get("G1") or {}).get("objectives") or []))
        if _HUA_LIEN_QUAN.search(ten) and not re.search(r"liên quan|yếu tố", muc_tieu, re.IGNORECASE):
            sai.append((ma, ten))
    assert not sai, sai


def test_nen_g0_cat_ngang_cung_ten_voi_kich_ban():
    """Nền G0 lưu (ngoại tuyến) đặt tên đề tài cho study_meta — phải trùng tên kịch bản, không mang tên cũ."""
    import gia_lap_dinh_ky as GL

    nen = json.loads((Path(__file__).parent / "fixtures/gia_lap_nen_g0/cat_ngang_mo_ta/_nen.json").read_text(
        encoding="utf-8"))
    assert nen["topic"] == GL.KICH_BAN["cat_ngang_mo_ta"]["topic"]
    assert not _HUA_LIEN_QUAN.search(nen["topic"])


@pytest.mark.parametrize("ma", ["rct_nhi_phan", "thuan_tap_phoi_nhiem", "chan_doan", "mo_hinh_du_bao",
                                "tong_quan_gop"])
def test_ho_so_gia_lap_khai_du_khoa_bo_sinh_doc_cho_thiet_ke(ma):
    """Mỗi kịch bản khai TRƯỚC G7 các đặc tả mà bộ sinh đọc cho thiết kế của nó (đúng vai PI/tác giả)."""
    import gia_lap_dinh_ky as GL

    hs = GL.KICH_BAN[ma]["ho_so_tron_vong"]
    can = {"rct_nhi_phan": ("blinding_how", "ppi_plan"),
           "thuan_tap_phoi_nhiem": ("routine_code_validation", "routine_database_access"),
           "chan_doan": ("index_test_role", "reference_standard_rationale", "index_threshold_rationale",
                         "reference_threshold_rationale", "disease_severity_variable"),
           "mo_hinh_du_bao": ("model_intended_use", "health_inequalities", "model_treatment_handling",
                              "outcome_assessment_blinding", "model_output_threshold", "model_input_handling",
                              "model_user_interaction", "ppi_plan"),
           "tong_quan_gop": ("search_strings_full", "rob_assessment_process")}[ma]
    assert all(hs["dac_ta_G10"].get(k) for k in can), [k for k in can if not hs["dac_ta_G10"].get(k)]
    assert set(can) <= set(G7.KHOA_DAC_TA_BAN_THAO)
    assert all(hs["tac_gia_G7"].get(k) for k in ("protocol_access_statement", "protocol_changes_statement"))


def test_go_khung_main_goi_cham_lai_bang_kiem_va_ghi_khi_doi():
    """Nối dây: công cụ gỡ khung (tác giả/giả lập chạy trước khi nộp) phải chấm lại bảng kiểm và GHI khi chỉ bảng kiểm
    đổi (bản thảo không còn dòng khung nào vẫn phải được chấm lại)."""
    nguon = inspect.getsource(GK.main)
    assert "cham_lai_bang_kiem(moi, out_dir)" in nguon
    assert "if a.ap_dung and (bo or doi_bk):" in nguon


def test_ghi_chu_bang_kiem_ban_nhap_khong_mang_o_can():
    """Bản nháp (còn ô [CẦN…]) ⇒ ghi chú K18 «bản thảo chưa có số liệu (còn ô [CẦN…]…)» — chép nguyên vào bảng kiểm thì
    chính phụ lục thành «ô chờ điền» (bộ quét ô của giả lập điền vào đó; chế độ nộp của K18 coi cả bản là nháp)."""
    nhap = _CAT_NGANG.replace("428 người.", "[CẦN KẾT QUẢ THẬT — số người] người.")
    std, tong = G7.REPORTING_CHECKLISTS["cross_sectional"]
    bk = G7.generate_checklist("cross_sectional", std, tong, "GL-1", "—", 428, 0.05, 0.8, md=nhap)
    assert "chưa có số liệu" in bk and "[CẦN" not in bk.split("**Tổng kết", 1)[0]


def test_cham_lai_chi_cham_than_bai_khong_doc_o_can_cua_phu_luc_cu():
    """Bản nộp (thân bài hết ô [CẦN]) nhưng phụ lục khuôn cũ còn «☐ [CẦN]», «[CẦN điền theo bảng kiểm gốc]» ⇒ K18 vẫn
    chấm ở chế độ NỘP (chỉ thân bài) — không được ghi «bản thảo chưa có số liệu» cho mục Kết quả."""
    std, tong = G7.REPORTING_CHECKLISTS["cross_sectional"]
    cu = G7.generate_checklist("cross_sectional", std, tong, "GL-1", "—", 428, 0.05, 0.8)
    cu = cu.replace("| ☐ chưa đo được |", "| ☐ [CẦN] |") + (
        "\n### 📋 Bảng kiểm mở rộng bắt buộc: CROSS\n\n| Mục | Vị trí | Trạng thái |\n|---|---|---|\n"
        "| [CẦN điền theo bảng kiểm gốc] | [CẦN] | ☐ |\n")
    moi, _doi = G7.cap_nhat_bang_kiem_k18(_CAT_NGANG + cu, "cross_sectional")
    assert "chưa có số liệu" not in moi and "| ☐ [CẦN] |" not in moi
