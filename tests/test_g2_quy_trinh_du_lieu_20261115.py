"""Khuôn G2 lấy quy trình dữ liệu ĐÃ CHỐT, không khẳng định thay người (15/11/2026, chạy G2 cho BTM).

Khuôn cũ in cứng «Mã hóa: Không cần (không có PII)» và «Kế hoạch hủy: Lưu trữ 5 năm sau công bố theo quy định» cho mọi
đề tài xin miễn ICF; rủi ro cắt ngang luôn nói «bộ câu hỏi» kể cả đề tài chỉ trích hồ sơ. Mỗi test khoá một hành vi.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for _p in (str(ROOT / "tools"), str(ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import run_g2_auto as G2  # noqa: E402

QT = [
    {"muc": "an_danh", "gia_tri": "Phiếu chỉ mang mã nghiên cứu", "nguon": "G1"},
    {"muc": "huy_bang_noi", "gia_tri": "Bảng nối lưu riêng, huỷ sau khi khoá dữ liệu", "nguon": "SOP"},
    {"muc": "luu_tru", "gia_tri": "[CẦN PI QUYẾT — thời hạn lưu trữ]", "nguon": "—"},
]
META_HOI_CUU = {"gate_params": {"G1": {"data_collection_method": "Hồi cứu hồ sơ bệnh án điện tử eHospital"}}}
META_KHAO_SAT = {"gate_params": {"G1": {"data_collection_method": "Phát phiếu khảo sát tự điền cho người bệnh"}}}


def test_mien_icf_lay_quy_trinh_da_chot():
    ma_hoa, huy = G2.dam_bao_bao_mat_mien_icf(QT)
    assert ma_hoa == "Phiếu chỉ mang mã nghiên cứu; Bảng nối lưu riêng, huỷ sau khi khoá dữ liệu"
    assert huy == "[CẦN PI QUYẾT — thời hạn lưu trữ]"


def test_mien_icf_chua_co_quy_trinh_khong_khang_dinh_thay():
    ma_hoa, huy = G2.dam_bao_bao_mat_mien_icf([])
    assert ma_hoa.startswith("[CẦN") and huy.startswith("[CẦN PI QUYẾT")
    assert "Không cần" not in ma_hoa and "5 năm" not in huy


def test_khoi_tl6_in_nguyen_van_quy_trinh():
    khoi = G2.khoi_quy_trinh_g2(QT)
    assert "Phiếu chỉ mang mã nghiên cứu" in khoi and "Bảng nối lưu riêng" in khoi
    assert G2.khoi_quy_trinh_g2([]) == ""


def test_rui_ro_cat_ngang_chi_trich_ho_so():
    goc = G2.get_risk_profile("cross_sectional")
    moi = G2.ap_nguon_du_lieu(goc, "cross_sectional", META_HOI_CUU)
    assert not any("bộ câu hỏi" in r[0].lower() or "bộ câu hỏi" in r[3].lower() for r in moi["risks"])
    assert G2.ap_nguon_du_lieu(goc, "cross_sectional", META_KHAO_SAT) is goc
    assert G2.ap_nguon_du_lieu(goc, "cohort", META_HOI_CUU) is goc


def test_ho_so_g2_tron_goi_khong_con_cau_viet_cung():
    risk = G2.ap_nguon_du_lieu(G2.get_risk_profile("cross_sectional"), "cross_sectional", META_HOI_CUU)
    md = G2.generate_g2_full_package(
        topic="Chủ đề", study_name="ZZTEST-G2-QT", design_code="cross_sectional", design_primary="Cắt ngang",
        reporting_std="STROBE", n_sr=0, n_rct=0, evidence_level="—", registry=None, risk=risk,
        run_date="2026-11-15T10:00:00", meta=META_HOI_CUU, quy_trinh=QT)
    assert "Không cần (không có PII)" not in md and "Lưu trữ 5 năm sau công bố" not in md
    assert "Quy trình dữ liệu đã chốt" in md
    assert "Mã hóa: Phiếu chỉ mang mã nghiên cứu" in md and "Kế hoạch hủy: [CẦN PI QUYẾT" in md
