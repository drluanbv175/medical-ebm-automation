"""Giai đoạn «Xác định vấn đề & hình thành câu hỏi nghiên cứu» thành chốt máy (15/11/2026).

Bác sĩ 15/11/2026: «… hãy tiếp tục đối với Xác Định Vấn Đề & Hình Thành Câu Hỏi Nghiên Cứu; … Hãy đảm bảo sự đồng bộ
xuyên suốt và chính xác nhất» + «mỗi vấn đề xây dựng và hoàn thiện phải được cập nhật vào hệ thống». Đo trên C1a:
`study_meta.topic` (chuỗi chủ đề tìm y văn G0) bị các bộ sinh in làm TÊN ĐỀ TÀI — kể cả mục 10 «Scientific Title» của
bản đăng ký WHO TRDS — khác tên chính thức của đề cương nộp. Mỗi test khoá MỘT hành vi.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

import g2_quality_gate as G2Q  # noqa: E402
import nhat_quan_xuyen_cong as NQ  # noqa: E402
import ten_de_tai as TDT  # noqa: E402

STUDY = "VDCH-THU"
TEN = "Đánh giá sự hài lòng của người bệnh tại Khoa Khám bệnh C1a, Bệnh viện Quân y 175"
CHU_DE = "Sự hài lòng người bệnh tại khoa khám theo yêu cầu, bệnh viện quân y tuyến cuối"


def _ghi(d: Path, ten: str, noi_dung: str) -> None:
    (d / ten).write_text(noi_dung, encoding="utf-8", newline="\n")


# ── ① tên chính thức trong bộ sinh ──────────────────────────────────────────────────────────────────────────────────
def test_ten_chinh_thuc_va_lui_ve_chu_de(tmp_path):
    assert TDT.ten_chinh_thuc({"title": TEN, "topic": CHU_DE}, CHU_DE) == TEN
    assert TDT.ten_chinh_thuc({"topic": CHU_DE}, CHU_DE) == CHU_DE  # chưa khai tên ⇒ hành vi cũ
    assert TDT.ten_chinh_thuc({"title": "[CẦN PI KHAI]"}, CHU_DE) == CHU_DE
    _ghi(tmp_path, "study_meta.json", json.dumps({"title": TEN}))
    assert TDT.ten_chinh_thuc(tmp_path, CHU_DE) == TEN  # đọc từ thư mục đề tài
    assert TDT.ten_chinh_thuc(tmp_path / "khong-co", CHU_DE) == CHU_DE


def test_ten_khoa_hoc_dang_ky_uu_tien_khai_rieng_cua_g2():
    meta = {"title": TEN, "gate_params": {"G2": {"scientific_title": "Patient satisfaction … (scientific)"}}}
    assert TDT.ten_khoa_hoc_dang_ky(meta, CHU_DE).startswith("Patient satisfaction")
    assert TDT.ten_khoa_hoc_dang_ky({"title": TEN}, CHU_DE) == TEN


def test_who_trds_muc_10_la_ten_chinh_thuc_khong_phai_chu_de():
    v = G2Q.who_trds_values(topic=CHU_DE, design_code="cross_sectional", design_primary="Cắt ngang",
                            n_target=1000, meta={"title": TEN, "gate_params": {}})
    assert v[10] == TEN
    v = G2Q.who_trds_values(topic=CHU_DE, design_code="cross_sectional", design_primary="Cắt ngang",
                            n_target=1000, meta={"gate_params": {}})
    assert v[10] == CHU_DE


def test_bo_sinh_in_ten_chinh_thuc_tren_dong_thi_hanh():
    # khớp DÒNG THI HÀNH (không khớp cả tệp — chú thích cùng chuỗi làm xanh giả, CLAUDE.md §0.8)
    for f in ("run_g3_auto.py", "run_g4_auto.py", "run_g5_auto.py", "run_g6_auto.py"):
        dong = [x for x in (REPO_ROOT / "tools" / f).read_text(encoding="utf-8").splitlines()
                if x.strip().startswith('f"**Đề tài:** ')]
        assert dong and all("TDT.ten_chinh_thuc(" in x for x in dong), f
    g2 = (REPO_ROOT / "tools" / "run_g2_auto.py").read_text(encoding="utf-8")
    assert "TÊN ĐỀ TÀI: {topic}" not in g2 and g2.count("TÊN ĐỀ TÀI: {ten_dt}") == 2
    # ô tên không được in MÃ đề tài (study_name) — bộ sinh cũ in «Đề tài: <mã> | Phiên bản …»
    assert "Đề tài: {study_name}" not in g2 and "Tên đề tài: {study_name}" not in g2


# ── ② trục tên đề tài ────────────────────────────────────────────────────────────────────────────────────────────────
def _reg(d: Path, ten10: str) -> None:
    _ghi(d, f"G2_REGISTRATION_DRAFT_{STUDY}.json", json.dumps({"items": [{"number": 10, "value": ten10}]}))


def test_ten_de_tai_khop(tmp_path):
    _ghi(tmp_path, f"DE_CUONG_NOP_HOI_DONG_{STUDY}.md", f"# ĐỀ CƯƠNG\n\n## {TEN.upper()}\n")
    _ghi(tmp_path, f"G2_A3_ETHICS_PACKAGE_{STUDY}.md", f"TÊN ĐỀ TÀI: {TEN} | Phiên bản: 1.0 | Ngày: 2026-07-31\n")
    _reg(tmp_path, TEN)
    k = NQ._truc_ten_de_tai(tmp_path, STUDY, {"title": TEN})
    assert k["muc"] == NQ.MUC_KHOP and "3 nơi" in k["ghi_chu"]  # đuôi «| Phiên bản …» được cắt; HOA/thường như nhau


def test_ten_de_tai_bo_qua_dau_cau(tmp_path):
    # bộ chuẩn trình bày của G2 đổi «—» thành «,» — vẫn là cùng một tên
    ten = "Suy tim ngoại trú — đề tài thử"
    _ghi(tmp_path, f"G2_A3_ETHICS_PACKAGE_{STUDY}.md", "TÊN ĐỀ TÀI: Suy tim ngoại trú, đề tài thử\n")
    assert NQ._truc_ten_de_tai(tmp_path, STUDY, {"title": ten})["muc"] == NQ.MUC_KHOP
    _ghi(tmp_path, f"G2_A3_ETHICS_PACKAGE_{STUDY}.md", "TÊN ĐỀ TÀI: Suy tim nội trú, đề tài thử\n")
    assert NQ._truc_ten_de_tai(tmp_path, STUDY, {"title": ten})["muc"] == NQ.MUC_LECH_MEM  # khác chữ ⇒ vẫn lệch


def test_ten_de_tai_dang_ky_mang_chu_de_la_lech_mem(tmp_path):
    _ghi(tmp_path, f"DE_CUONG_NOP_HOI_DONG_{STUDY}.md", f"## {TEN}\n")
    _reg(tmp_path, CHU_DE)
    k = NQ._truc_ten_de_tai(tmp_path, STUDY, {"title": TEN})
    assert k["muc"] == NQ.MUC_LECH_MEM and "Scientific Title" in k["ghi_chu"]


def test_ten_de_tai_chi_van_ban_may_sinh_lech_la_can_xem(tmp_path):
    _ghi(tmp_path, f"DE_CUONG_NOP_HOI_DONG_{STUDY}.md", f"## {TEN}\n")
    _ghi(tmp_path, f"G4_A5_SAP_FINAL_{STUDY}.md", f"# SAP\n**Đề tài:** {CHU_DE}  \n")
    k = NQ._truc_ten_de_tai(tmp_path, STUDY, {"title": TEN})
    assert k["muc"] == NQ.MUC_CAN_XEM and "SAP" in k["ghi_chu"]


def test_ten_de_tai_chua_khai_ten_la_chua_du(tmp_path):
    _ghi(tmp_path, f"DE_CUONG_NOP_HOI_DONG_{STUDY}.md", f"## {TEN}\n")
    assert NQ._truc_ten_de_tai(tmp_path, STUDY, {})["muc"] == NQ.MUC_CHUA_DU
    rong = tmp_path / "rong"
    rong.mkdir()
    assert NQ._truc_ten_de_tai(rong, STUDY, {"title": TEN}) is None  # không văn bản nào ⇒ không áp dụng


# ── ③ trục câu hỏi ↔ mục tiêu ↔ giả thuyết ─────────────────────────────────────────────────────────────────────────
def _m(g0: dict, g1: dict) -> dict:
    return {"gate_params": {"G0": g0, "G1": g1}}


MT = ["MT1 (mô tả): Xác định mức độ hài lòng", "MT2 (phân tích): Đánh giá một số yếu tố liên quan đến mức độ hài lòng"]
RQ = "Mức độ hài lòng là bao nhiêu, và những yếu tố nào liên quan?"


def test_cau_hoi_mo_ta_co_muc_tieu_phan_tich_can_gia_thuyet_hoac_tham_do():
    g0 = {"question_type": "descriptive", "test_type": "descriptive"}
    k = NQ._truc_cau_hoi_gia_thuyet(_m(g0, {"objectives": MT, "research_question": RQ}))
    assert k["muc"] == NQ.MUC_CAN_XEM and "giả thuyết" in k["ghi_chu"]
    k = NQ._truc_cau_hoi_gia_thuyet(_m({**g0, "hypothesis_secondary": "MT2: H0: OR = 1"},
                                       {"objectives": MT, "research_question": RQ}))
    assert k["muc"] == NQ.MUC_KHOP
    mt_tham_do = [MT[0], MT[1] + " (phân tích thăm dò, không kiểm định giả thuyết định trước)"]
    assert NQ._truc_cau_hoi_gia_thuyet(_m(g0, {"objectives": mt_tham_do, "research_question": RQ}))["muc"] \
        == NQ.MUC_KHOP


def test_cau_hoi_dieu_tri_thieu_h0_h1_la_lech_mem():
    g1 = {"objectives": ["MT1: So sánh hiệu quả A với B"], "research_question": "A có hiệu quả hơn B?"}
    assert NQ._truc_cau_hoi_gia_thuyet(_m({"question_type": "treatment", "test_type": "superiority"}, g1))["muc"] \
        == NQ.MUC_LECH_MEM
    g0 = {"question_type": "treatment", "test_type": "superiority", "hypothesis_h0": "A = B", "hypothesis_h1": "A ≠ B"}
    assert NQ._truc_cau_hoi_gia_thuyet(_m(g0, g1))["muc"] == NQ.MUC_KHOP


def test_cau_hoi_khong_phu_muc_tieu_yeu_to():
    g0 = {"question_type": "descriptive", "hypothesis_secondary": "MT2: H0 …"}
    k = NQ._truc_cau_hoi_gia_thuyet(_m(g0, {"objectives": MT, "research_question": "Mức độ hài lòng là bao nhiêu?"}))
    assert k["muc"] == NQ.MUC_CAN_XEM and "không hỏi về yếu tố" in k["ghi_chu"]


def test_truc_moi_nam_trong_chuoi_va_co_cong_chu(tmp_path):
    for ma in ("ten_de_tai", "cau_hoi_gia_thuyet"):
        assert ma in NQ.TRUC_CHUOI and NQ.TRUC_THEO_CONG.get(ma), ma
    _ghi(tmp_path, "study_meta.json", json.dumps({"title": TEN, **_m({"question_type": "descriptive"},
                                                                       {"objectives": MT, "research_question": RQ})}))
    _reg(tmp_path, CHU_DE)
    ma = {t["ma"]: t["muc"] for t in NQ.doi_chieu(tmp_path, STUDY)["thong_so"]}
    assert ma["ten_de_tai"] == NQ.MUC_LECH_MEM and ma["cau_hoi_gia_thuyet"] == NQ.MUC_CAN_XEM
