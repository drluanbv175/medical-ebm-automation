#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Hồi quy 25/10/2026 — bộ sinh tài liệu G1 dùng dữ kiện ĐÃ CHỐT của đề tài thay vì khuôn chung.

Bối cảnh: hội đồng G1 của C1a (khảo sát hài lòng cắt ngang, một khoa) trả G1-T3 về sửa và ghi lưu ý ở G1-T1/G1-T2:
A13 in RACI/GANTT/QTL/giám sát cứng dù PI đã chốt team_roles, study_schema_timeline, critical_to_quality,
monitoring_plan; kinh phí có «xét nghiệm»; A13b viết cho thử nghiệm nhiều điểm («estimand», «nhiều điểm tuyển»), không
có rủi ro dữ liệu cá nhân; A2b gắn một nhãn RoB chung cho mọi thiết kế, để «cần đối chiếu tránh trùng lặp» như việc treo
dù PI đã đánh giá ở G0, không ghi kiểm rút bài; A2 PHẦN 2 chỉ có khuôn sai lệch chung. Ngoại tuyến, dữ liệu tổng hợp.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
for _p in (str(REPO_ROOT / "tools"), str(REPO_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import g1_quality_gate as G1Q  # noqa: E402
import run_g1_auto as G1  # noqa: E402

STUDY = "G1-THU"


def _sinh(tmp_path: Path, g1: dict, ma_tk: str = "cross_sectional", g0: dict | None = None) -> dict:
    meta = {"gate_params": {"G1": g1, "G0": g0 or {}}}
    G1Q.build_supporting_artifacts(study=STUDY, topic="T", out_dir=tmp_path,
                                   design={"primary": "Cắt ngang", "internal_code": ma_tk},
                                   g0_checkpoint={"research_gaps": ["Có 3 thử nghiệm đang tuyển — cần đối chiếu để "
                                                                     "tránh trùng lặp (xem §3.6)"]},
                                   effects=[], meta=meta, generated_at="2026-10-25 10:00")
    return {k: (tmp_path / f"G1_{k}_{ten}_{STUDY}.md").read_text(encoding="utf-8") for k, ten in (
        ("A13", "IMPLEMENTATION_PLAN"), ("A13b", "RISK_REGISTER"), ("A2b", "EVIDENCE_LEDGER"))}


DA_CHOT = {"team_roles": "Chủ nhiệm A; thống kê viên độc lập B", "study_schema_timeline": "12/2026 → 12/2028",
           "critical_to_quality": "F1 ≥ 80%; F2 ≥ 60%", "monitoring_plan": "QC độc lập kiểm 10% phiếu"}


def test_a13_dung_du_kien_da_chot(tmp_path):
    a13 = _sinh(tmp_path, dict(DA_CHOT))["A13"]
    for gia_tri in DA_CHOT.values():
        assert gia_tri in a13, gia_tri
    assert "Methodologist | Biostatistician" not in a13 and "[CẦN PI/methodologist ấn định" not in a13
    assert "theo lịch đã khai" in a13
    for muc in G1Q._REQUIRED_SECTIONS["A13"]:
        assert muc in a13, f"bộ chấm G1 đòi mục «{muc}» trong A13"


def test_a13_chua_khai_thi_khuon_kem_cho_dien_va_khong_xet_nghiem_mac_dinh(tmp_path):
    a13 = _sinh(tmp_path, {})["A13"]
    assert "gate_params.G1.team_roles" in a13 and "gate_params.G1.critical_to_quality" in a13
    assert "gate_params.G1.budget" in a13 and "gate_params.G1.study_schema_timeline" in a13
    assert "Thu thập/xét nghiệm" not in a13 and "Xét nghiệm/cận lâm sàng (chỉ khi đề cương có)" in a13


def test_a13b_khuon_theo_thiet_ke_co_rui_ro_du_lieu_ca_nhan(tmp_path):
    a13b = _sinh(tmp_path, {})["A13b"]
    assert "estimand" not in a13b and "nhiều điểm tuyển" not in a13b and "G1-R07" in a13b
    assert "KHUÔN MẶC ĐỊNH" in a13b and "| Cao |" not in a13b
    assert "estimand" in _sinh(tmp_path, {}, ma_tk="rct")["A13b"]


def test_a13b_co_so_rui_ro_that_thi_khong_con_nhan_khuon(tmp_path):
    rr = [{"id": "R1", "loai": "Tuyển mẫu", "rui_ro": "Tỷ lệ đồng ý thấp", "xac_suat": "Vừa", "tac_dong": "Cao",
           "giam_thieu": "Giải thích kỹ", "capa": "Kéo dài thu thập", "chu_nhan": "Điều phối", "trang_thai": "Mở"}]
    a13b = _sinh(tmp_path, {"risk_register": rr})["A13b"]
    assert "KHUÔN MẶC ĐỊNH" not in a13b and "Tỷ lệ đồng ý thấp" in a13b and "G1-R07" not in a13b


def test_a2b_khoang_trong_noi_ket_luan_chong_lan_g0(tmp_path):
    a2b = _sinh(tmp_path, {}, g0={"registry_overlap_assessment": "Không chồng lấn: NCT0 là thử nghiệm khác"})["A2b"]
    assert "PI ĐÃ ĐÁNH GIÁ ở G0" in a2b and "Không chồng lấn: NCT0" in a2b
    assert "PI ĐÃ ĐÁNH GIÁ" not in _sinh(tmp_path, {})["A2b"]


def test_a2b_chua_kiem_rut_bai_thi_noi_ro(tmp_path):
    assert "CHƯA KIỂM RÚT BÀI" in _sinh(tmp_path, {})["A2b"]


def test_goi_y_cong_cu_rob_theo_thiet_ke():
    goi_y = {
        "Cắt ngang, 3 bệnh viện (n=108)": "JBI cắt ngang",
        "Tổng quan hệ thống Cochrane (2012)": "AMSTAR 2",
        "Thử nghiệm ngẫu nhiên thí điểm, mù người đánh giá": "RoB 2",
        "Nghiên cứu triển khai CÓ CAN THIỆP, tiến cứu": "ROBINS-I",
        "Phương pháp hỗn hợp, định tính + khảo sát": "MMAT",
        "Theo dõi tiến cứu một nhóm phẫu thuật": "ROBINS-E",
    }
    for thiet_ke, cong_cu in goi_y.items():
        assert cong_cu in G1Q._o_rob(thiet_ke), (thiet_ke, G1Q._o_rob(thiet_ke))
    assert G1Q._o_rob("Xã luận").startswith("Không áp dụng")
    assert "chọn công cụ theo thiết kế" in G1Q._o_rob("")


def test_a2_sai_lech_rieng_cua_de_tai():
    meta = {"gate_params": {"G1": {"bias_controls": [
        {"sai_lech": "Người bỏ về trước khi khám", "bien_phap": "Đếm từ HIS, phân tích giới hạn", "chieu": "ước cao"},
        {"sai_lech": "", "bien_phap": "dòng thiếu tên bị bỏ"}]}}}
    assert G1._bias_rieng_de_tai(meta) == [("Người bỏ về trước khi khám",
                                           "Đếm từ HIS, phân tích giới hạn (chiều lệch: ước cao)")]
    design = G1.infer_study_design("descriptive", {}, "hài lòng người bệnh ngoại trú")
    a2 = G1.generate_g1_artifact("t", "S", "descriptive", design, [], {}, "2026-10-25 10:00", meta=meta)
    assert "Người bỏ về trước khi khám" in a2 and "Sai lệch RIÊNG của đề tài" in a2
    assert "[từ §2 Bias Control]" not in a2
    a2_khuon = G1.generate_g1_artifact("t", "S", "descriptive", design, [], {}, "2026-10-25 10:00",
                                       meta={"gate_params": {"G1": {}}})
    assert "KHUÔN CHUNG theo thiết kế" in a2_khuon and "[từ §2 Bias Control]" in a2_khuon
    assert json.dumps(design["bias_controls"]) == json.dumps(
        G1.infer_study_design("descriptive", {}, "hài lòng người bệnh ngoại trú")["bias_controls"]), \
        "design.bias_controls (bộ chấm G1 đếm) không đổi theo khai riêng"
