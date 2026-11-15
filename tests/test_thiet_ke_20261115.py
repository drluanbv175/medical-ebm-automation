"""Giai đoạn «Lựa chọn thiết kế nghiên cứu» thành chốt máy (15/11/2026).

Bác sĩ 15/11/2026: «Tiếp tục giai đoạn 4» — «đảm bảo sự đồng bộ xuyên suốt và chính xác nhất». Kiểm tay C1a/BTM:
(1) đề cương nộp C1a ghi «STROBE và CROSS», G1/gói G2/SAP chỉ «STROBE»; SAP BTM «STROBE + RECORD», G1 chỉ «STROBE»;
(2) nhãn «Cắt ngang Mô tả (Prevalence)» ở G1/G2/SAP/đăng ký khi đề tài có mục tiêu phân tích; tiêu đề SAP C1a ghi 1.4
khi bảng lịch sử đã 1.5; (3) bảng kiểm soát sai lệch G1 hứa phân tích mà SAP không có (C1a: đáp ứng/người từ chối, đặc
tính đo lường, thăm dò kỳ vọng; BTM: so sánh nhóm 1 lượt khám). Mỗi test khoá MỘT hành vi.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for _p in (str(ROOT / "tools"), str(ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import doi_chieu_sai_lech_sap as DSL  # noqa: E402
import nhat_quan_xuyen_cong as NQ  # noqa: E402
import run_g1_auto as G1  # noqa: E402
import run_g10_assemble as G10  # noqa: E402
import skill_standards as SK  # noqa: E402

STUDY = "ZZTEST-THIET-KE-20261115"
THU_MOI = "Thu MỚI: phiếu tự điền khuyết danh; khai thác nguồn CÓ SẴN: mốc thời gian chờ từ HIS/eHospital"
CHI_CO_SAN = "Khai thác nguồn CÓ SẴN, không thu mới: mở hồ sơ bệnh án điện tử trên eHospital, ghi vào phiếu thu thập"
MT_PHAN_TICH = ["MT1: Xác định tỷ lệ hài lòng", "MT2 (phân tích): Đánh giá một số yếu tố liên quan đến hài lòng"]
MT_MO_TA = ["MT1: Mô tả tỷ lệ được xét nghiệm", "MT2: Mô tả thực trạng điều trị"]
BIAS = [{"sai_lech": "Sai lệch chọn mẫu", "bien_phap": "Chọn mẫu hệ thống; báo cáo tỷ lệ đáp ứng"},
        {"sai_lech": "Sai lệch nhớ lại", "bien_phap": "Khảo sát ngay sau lượt khám"},
        {"sai_lech": "Gom cụm", "bien_phap": "Sai số chuẩn vững theo cụm; báo cáo ICC"}]
NHAN_PT = "Nghiên cứu Cắt ngang Mô tả có phân tích (Analytical cross-sectional)"
NHAN_CU = "Nghiên cứu Cắt ngang Mô tả (Cross-sectional / Prevalence)"


def _sap(chuan="STROBE + CROSS", nhan=NHAN_PT, phien_ban="1.1", lich_su=("1.0", "1.1"), them="") -> str:
    ls = "\n".join(f"| {v} | 2026-11-0{i + 1} | máy | thay đổi |" for i, v in enumerate(lich_su))
    return (f"# SAP\n**Mã:** {STUDY} | **Phiên bản SAP:** {phien_ban} | **Ngày sinh:** 2026-11-01\n"
            f"**Chuẩn báo cáo:** {chuan}\n\n## PHẦN 1\n| Thiết kế | {nhan} |\n| Chuẩn báo cáo | {chuan} |\n\n"
            f"## PHẦN 2, LỊCH SỬ\n| Phiên bản | Ngày | Người soạn | Thay đổi |\n|---|---|---|---|\n{ls}\n\n"
            "## PHẦN 3\n### §1 QUẦN THỂ\nbáo tỷ lệ đồng ý và người từ chối\n### §4 PHÂN TÍCH CHÍNH\n"
            f"sai số chuẩn robust theo chùm; báo ICC\n### §5 ĐA BIẾN\nDAG\n{them}\n### §9 ĐỘ NHẠY\nĐN1\n## PHẦN 4\n")


def _de_tai(tmp_path: Path, *, thu_thap=THU_MOI, muc_tieu=MT_PHAN_TICH, che_do="PROSPECTIVE_NEW_PARTICIPANTS",
            g1_chuan="STROBE + CROSS", g1_nhan=NHAN_PT, sap=None, bias=BIAS, g1_them=None) -> Path:
    d = tmp_path / "exports" / STUDY
    d.mkdir(parents=True)
    g1 = {"design": "cross_sectional", "objectives": muc_tieu, "data_collection_method": thu_thap,
          "bias_controls": bias}
    g1.update(g1_them or {})
    meta = {"design_code": "cross_sectional", "gate_params": {"G1": g1, "G2": {"recruitment_mode": che_do}}}
    (d / "study_meta.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8", newline="\n")
    (d / "G1_checkpoint.json").write_text(json.dumps(
        {"design": {"internal_code": "cross_sectional", "primary": g1_nhan, "reporting_standard": g1_chuan}},
        ensure_ascii=False), encoding="utf-8", newline="\n")
    (d / f"G1_A2_PROTOCOL_DESIGN_{STUDY}.md").write_text(f"**Chuẩn báo cáo:** {g1_chuan}\n", encoding="utf-8",
                                                       newline="\n")
    (d / f"G4_A5_SAP_FINAL_{STUDY}.md").write_text(sap if sap is not None else _sap(), encoding="utf-8", newline="\n")
    return d


def _meta(d: Path) -> dict:
    return json.loads((d / "study_meta.json").read_text(encoding="utf-8"))


def _truc(d: Path, ten: str) -> dict:
    sap = (d / f"G4_A5_SAP_FINAL_{STUDY}.md").read_text(encoding="utf-8")
    ham = {"chuan_bao_cao": lambda: NQ._truc_chuan_bao_cao(d, STUDY, _meta(d), sap),
           "mo_ta_thiet_ke": lambda: NQ._truc_mo_ta_thiet_ke(d, STUDY, _meta(d), sap),
           "kiem_soat_sai_lech": lambda: NQ._truc_kiem_soat_sai_lech(d, STUDY, _meta(d))}[ten]
    return ham()


def _bang_sai_lech(d: Path, dong) -> None:
    with (d / DSL.TEP).open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(DSL.COT), lineterminator="\n")
        w.writeheader()
        for r in dong:
            w.writerow(dict(zip(DSL.COT, r)))


BANG_DUNG = [("Sai lệch chọn mẫu", "co", "§1", "tỷ lệ đồng ý", "", ""),
             ("Sai lệch nhớ lại", "khong", "", "", "đề cương 4.7", ""),
             ("Gom cụm", "co", "§4", "robust theo chùm | báo ICC", "", "")]


# ── ① chuẩn báo cáo của đề tài (skill_standards) ─────────────────────────────────────────────────────────────────
def test_khao_sat_thu_moi_them_cross_va_record_cho_pi_quyet():
    cb = SK.chuan_bao_cao_de_tai("cross_sectional", {"data_collection_method": THU_MOI})
    assert cb["chuoi"] == "STROBE + CROSS" and [c for c, _ in cb["can_xem"]] == ["RECORD"]


def test_chi_du_lieu_co_san_them_record_va_doc_dung_phu_dinh_khong_thu_moi():
    nd = SK.nguon_du_lieu(CHI_CO_SAN)
    assert nd["thu_moi"] is False and nd["thuong_quy"] is True  # «không thu mới» là phủ định
    cb = SK.chuan_bao_cao_de_tai("cross_sectional", {"data_collection_method": CHI_CO_SAN})
    assert cb["chuoi"] == "STROBE + RECORD" and cb["can_xem"] == []


def test_pi_khai_danh_sach_thi_khong_suy():
    cb = SK.chuan_bao_cao_de_tai("cross_sectional", {"data_collection_method": THU_MOI,
                                                     "reporting_extensions": ["CROSS", "record"]})
    assert cb["pi_khai"] and cb["mo_rong"] == ["CROSS", "RECORD"] and cb["can_xem"] == []
    assert SK.chuan_bao_cao_de_tai("cross_sectional", {"data_collection_method": THU_MOI,
                                                       "reporting_extensions": []})["chuoi"] == "STROBE"


def test_chuan_trong_dong_khong_an_cross_sectional():
    assert SK.chuan_trong_dong(NHAN_CU) == []
    assert SK.chuan_trong_dong("STROBE (cắt ngang) và CROSS (khảo sát)") == ["STROBE", "CROSS"]


# ── ② nhãn thiết kế theo mục tiêu ─────────────────────────────────────────────────────────────────────────────────
def test_nhan_cat_ngang_co_muc_tieu_phan_tich():
    assert SK.nhan_thiet_ke_theo_muc_tieu("cross_sectional", MT_PHAN_TICH, NHAN_CU) == NHAN_PT
    assert SK.nhan_thiet_ke_theo_muc_tieu("cross_sectional", MT_MO_TA, NHAN_CU) == NHAN_CU
    assert SK.nhan_thiet_ke_theo_muc_tieu("cohort", MT_PHAN_TICH, "Đoàn hệ") == "Đoàn hệ"


def test_g1_ghim_thiet_ke_ghi_nhan_va_chuan_bao_cao_de_tai():
    meta = {"gate_params": {"G1": {"objectives": MT_PHAN_TICH, "data_collection_method": CHI_CO_SAN}}}
    d = G1._apply_design_pin({"primary": "x", "internal_code": "cohort"}, "cross_sectional", meta)
    assert d["primary"] == NHAN_PT and d["reporting_standard"] == "STROBE + RECORD"
    assert d["reporting_extensions"] == ["RECORD"] and d["reporting_extensions_can_xem"] == []
    assert "RECORD" in G1._ghi_chu_chuan_bao_cao(d)


def test_g10_in_chuan_bao_cao_cua_de_tai_tu_g1():
    cps = {"G1": {"design": {"reporting_standard": "STROBE + CROSS"}}}
    assert G10._chuan_bao_cao_de_tai(cps, {"primary": "STROBE"}) == "STROBE + CROSS"
    assert G10._chuan_bao_cao_de_tai({"G1": {}}, {"primary": "STROBE"}) == "STROBE"


# ── ③ trục chuan_bao_cao ──────────────────────────────────────────────────────────────────────────────────────────
def test_truc_chuan_bao_cao_khop_khi_moi_noi_cung_khai(tmp_path):
    d = _de_tai(tmp_path)
    (d / f"DE_CUONG_NOP_HOI_DONG_{STUDY}.md").write_text(
        "| Chuẩn báo cáo áp dụng | STROBE và CROSS |\nRECORD không áp dụng vì HIS chỉ dùng mốc giờ\n",
        encoding="utf-8", newline="\n")
    k = _truc(d, "chuan_bao_cao")
    assert k["muc"] == NQ.MUC_KHOP, k["ghi_chu"]


def test_truc_chuan_bao_cao_lech_mem_khi_g1_thieu_mo_rong(tmp_path):
    d = _de_tai(tmp_path, g1_chuan="STROBE")
    k = _truc(d, "chuan_bao_cao")
    assert k["muc"] == NQ.MUC_LECH_MEM and "thiếu CROSS" in k["ghi_chu"]


def test_truc_chuan_bao_cao_lech_cung_khi_sai_chuan_chinh(tmp_path):
    d = _de_tai(tmp_path, sap=_sap(chuan="CONSORT 2025"))
    assert _truc(d, "chuan_bao_cao")["muc"] == NQ.MUC_LECH_CUNG


def test_truc_chuan_bao_cao_can_xem_khi_nguon_du_lieu_doi_ma_chua_ai_ghi(tmp_path):
    d = _de_tai(tmp_path, thu_thap=CHI_CO_SAN, che_do="RETROSPECTIVE_SECONDARY_DATA", g1_chuan="STROBE",
                sap=_sap(chuan="STROBE"))
    k = _truc(d, "chuan_bao_cao")
    assert k["muc"] == NQ.MUC_CAN_XEM and "RECORD" in k["ghi_chu"]


# ── ④ trục mo_ta_thiet_ke ─────────────────────────────────────────────────────────────────────────────────────────
def test_truc_mo_ta_khop(tmp_path):
    d = _de_tai(tmp_path)
    assert _truc(d, "mo_ta_thiet_ke")["muc"] == NQ.MUC_KHOP


def test_truc_mo_ta_can_xem_khi_nhan_chua_ghi_co_phan_tich(tmp_path):
    d = _de_tai(tmp_path, g1_nhan=NHAN_CU)
    k = _truc(d, "mo_ta_thiet_ke")
    assert k["muc"] == NQ.MUC_CAN_XEM and "G1_checkpoint.design.primary" in k["ghi_chu"]


def test_truc_mo_ta_khong_doi_nhan_khi_moi_muc_tieu_mo_ta(tmp_path):
    d = _de_tai(tmp_path, muc_tieu=MT_MO_TA, g1_nhan=NHAN_CU, sap=_sap(nhan=NHAN_CU))
    assert _truc(d, "mo_ta_thiet_ke")["muc"] == NQ.MUC_KHOP


def test_truc_mo_ta_lech_cung_khi_thu_moi_ma_g2_khai_du_lieu_thu_cap(tmp_path):
    d = _de_tai(tmp_path, che_do="RETROSPECTIVE_SECONDARY_DATA")
    assert _truc(d, "mo_ta_thiet_ke")["muc"] == NQ.MUC_LECH_CUNG


def test_truc_mo_ta_lech_cung_khi_chi_du_lieu_co_san_ma_g2_khai_tuyen_moi(tmp_path):
    d = _de_tai(tmp_path, thu_thap=CHI_CO_SAN, g1_chuan="STROBE + RECORD", sap=_sap(chuan="STROBE + RECORD"))
    assert _truc(d, "mo_ta_thiet_ke")["muc"] == NQ.MUC_LECH_CUNG


def test_truc_mo_ta_lech_mem_khi_tieu_de_sap_tut_phien_ban(tmp_path):
    d = _de_tai(tmp_path, sap=_sap(phien_ban="1.0", lich_su=("1.0", "1.1")))
    k = _truc(d, "mo_ta_thiet_ke")
    assert k["muc"] == NQ.MUC_LECH_MEM and "1.0" in k["ghi_chu"] and "1.1" in k["ghi_chu"]


# ── ⑤ bảng đối chiếu sai lệch ↔ SAP ───────────────────────────────────────────────────────────────────────────────
def test_sai_lech_dat(tmp_path):
    d = _de_tai(tmp_path)
    _bang_sai_lech(d, BANG_DUNG)
    kq = DSL.kiem(d, STUDY)
    assert kq["trang_thai"] == DSL.TRANG_THAI_DAT and kq["loi"] == [] and kq["canh_bao"] == []
    assert _truc(d, "kiem_soat_sai_lech")["muc"] == NQ.MUC_KHOP


def test_sai_lech_chua_co_bang_la_chua_du(tmp_path):
    d = _de_tai(tmp_path)
    assert DSL.kiem(d, STUDY)["trang_thai"] == DSL.TRANG_THAI_KHONG_CO
    assert _truc(d, "kiem_soat_sai_lech")["muc"] == NQ.MUC_CHUA_DU


def test_sai_lech_sap_khong_co_phan_tich_da_hua(tmp_path):
    d = _de_tai(tmp_path)
    _bang_sai_lech(d, [BANG_DUNG[0], BANG_DUNG[1],
                       ("Gom cụm", "co", "§4", "robust theo chùm | báo ICC thực tế", "", "")])
    kq = DSL.kiem(d, STUDY)
    assert [x["ma"] for x in kq["loi"]] == ["SL-06"] and "báo ICC thực tế" in kq["loi"][0]["noi_dung"]
    assert _truc(d, "kiem_soat_sai_lech")["muc"] == NQ.MUC_LECH_MEM


def test_sai_lech_thieu_dong_va_dong_la_va_muc_khong_co(tmp_path):
    d = _de_tai(tmp_path)
    _bang_sai_lech(d, [BANG_DUNG[1], ("Gom cụm", "co", "§7", "ICC", "", ""),
                       ("Sai lệch không có", "khong", "", "", "x", "")])
    ma = sorted(x["ma"] for x in DSL.kiem(d, STUDY)["loi"])
    assert ma == ["SL-02", "SL-03", "SL-05"]


def test_sai_lech_ghi_khong_ma_bien_phap_co_phan_tich_thi_canh_bao(tmp_path):
    d = _de_tai(tmp_path)
    _bang_sai_lech(d, [("Sai lệch chọn mẫu", "khong", "", "", "", ""), BANG_DUNG[1], BANG_DUNG[2]])
    kq = DSL.kiem(d, STUDY)
    assert kq["loi"] == [] and sorted(x["ma"] for x in kq["canh_bao"]) == ["SL-07", "SL-08"]
    assert _truc(d, "kiem_soat_sai_lech")["muc"] == NQ.MUC_CAN_XEM


# ── ⑥ giai đoạn 8 «Bàn luận»: hạn chế mở ở G1 phải có trong mục «Hạn chế» của đề cương nộp (SL-09) ───────────────
def _han_che_de_tai(tmp_path: Path, *, neo: str, han_che: str) -> Path:
    bias = [dict(BIAS[0], trang_thai="khống chế"), dict(BIAS[1], trang_thai="khống chế"),
            dict(BIAS[2], trang_thai="khống chế + hạn chế mở")]
    d = _de_tai(tmp_path, bias=bias)
    _bang_sai_lech(d, [r + ("",) for r in BANG_DUNG[:2]] + [BANG_DUNG[2] + (neo,)])
    (d / f"DE_CUONG_NOP_HOI_DONG_{STUDY}.md").write_text(
        "# 4. PHƯƠNG PHÁP\n## 4.12. Hạn chế của nghiên cứu\n" + han_che + "\n## 4.13. Khác\nGom cụm trong mục khác\n",
        encoding="utf-8", newline="\n")
    return d


def test_sl09_han_che_mo_co_trong_muc_han_che(tmp_path):
    d = _han_che_de_tai(tmp_path, neo="Gom cụm theo bàn khám", han_che="| Gom cụm theo bàn khám | KTC hẹp |")
    assert DSL.kiem(d, STUDY)["loi"] == []


def test_sl09_neo_chi_nam_ngoai_muc_han_che_la_loi(tmp_path):
    d = _han_che_de_tai(tmp_path, neo="Gom cụm trong mục khác", han_che="| Thiết kế cắt ngang | … |")
    assert [x["ma"] for x in DSL.kiem(d, STUDY)["loi"]] == ["SL-09"]


def test_sl09_chua_khai_neo_va_chua_co_de_cuong(tmp_path):
    d = _han_che_de_tai(tmp_path, neo="", han_che="| X | Y |")
    assert [x["ma"] for x in DSL.kiem(d, STUDY)["loi"]] == ["SL-09"]
    (d / f"DE_CUONG_NOP_HOI_DONG_{STUDY}.md").unlink()
    assert DSL.kiem(d, STUDY)["loi"] == []  # chưa có đề cương ⇒ không đòi


# ── ⑦ giai đoạn 9 «Báo cáo»: bảng kiểm G7 có bảng kiểm mở rộng của đề tài ─────────────────────────────────────────
def test_g7_bang_kiem_co_khoi_mo_rong_va_nguon_da_kiem():
    import run_g7_auto as G7

    md = G7.generate_checklist("cross_sectional", "STROBE 2007", 22, "—", "—", 1000, 0.05, 0.8,
                               reporting_extensions=["CROSS", "RECORD"])
    assert "Bảng kiểm mở rộng bắt buộc: CROSS" in md and "PMID: 33886027" in md
    assert "Bảng kiểm mở rộng bắt buộc: RECORD" in md and "PMID: 26440803" in md
    assert "Bảng kiểm mở rộng bắt buộc" not in G7.generate_checklist("cross_sectional", "STROBE 2007", 22, "—", "—",
                                                                   1000, 0.05, 0.8)
    assert "CẦN KIỂM CHỨNG NGUỒN" in G7.khoi_bang_kiem_mo_rong(["CHERRIES"])
