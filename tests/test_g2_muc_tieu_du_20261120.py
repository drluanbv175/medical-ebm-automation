"""Hồ sơ đạo đức G2 mang ĐỦ mục tiêu G1 đã chốt — 20/11/2026 (kiểm toàn hệ nghiên cứu, đề tài BTM).

Đo thật: G1 của BTM sửa 20/11 (MT1 thu hẹp «được theo dõi đều», thêm MT3) nhưng hồ sơ G2 trình Hội đồng thiếu MT3 và MT1
còn câu cũ. Hai gốc: (1) khuôn tóm tắt TL2 của `run_g2_auto` chỉ có hai ô {_obj1}/{_obj2} — đề tài 3 mục tiêu mất MT3 kể
cả khi sinh lại; (2) không trục nào so mục tiêu G1 với hồ sơ G2. Ngoại tuyến, đề tài giả, không PII.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
for _p in (REPO_ROOT, REPO_ROOT / "tools"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import nhat_quan_xuyen_cong as NQ  # noqa: E402
import run_g2_auto as G2  # noqa: E402

MT = ["MT1: Mô tả tỷ lệ được xét nghiệm đủ UACR ở người bệnh được theo dõi đều (từ 2 lượt khám trong năm).",
      "MT2: Mô tả thực trạng điều trị bảo vệ thận ở người bệnh đủ chỉ định.",
      "MT3: Phân tích một số yếu tố liên quan với việc không được xét nghiệm đủ (thăm dò)."]


def _goi(objectives: list) -> str:
    meta = {"gate_params": {"G1": {"objectives": objectives}}}
    return G2.generate_g2_full_package(
        topic="Đề tài thử", study_name="TEST-MT", design_code="cross_sectional", design_primary="Cắt ngang",
        reporting_std="STROBE", n_sr=0, n_rct=0, evidence_level="", registry=None,
        risk=G2.get_risk_profile("cross_sectional", "Cắt ngang"), run_date="2026-11-20T10:00:00", n_adjusted=385,
        meta=meta)


def _muc_tieu(goi: str) -> str:
    return goi[goi.index("2. MỤC TIÊU CỤ THỂ:"):goi.index("3. ĐỐI TƯỢNG THAM GIA:")]


def test_tom_tat_liet_ke_du_ba_muc_tieu_nguyen_van():
    khoi = _muc_tieu(_goi(MT))
    for i, o in enumerate(MT, 1):
        assert f"   2.{i} {o}" in khoi, o


def test_chua_co_muc_tieu_thi_giu_hai_o_can():
    khoi = _muc_tieu(_goi([]))
    assert "2.1 [CẦN — Mục tiêu 1, từ PICO G0]" in khoi and "2.2 [CẦN — Mục tiêu 2 nếu có]" in khoi


def _de_tai(tmp_path: Path, g2_text: str):
    out = tmp_path / "S"
    out.mkdir()
    (out / "G2_A3_ETHICS_PACKAGE_S.md").write_text(g2_text, encoding="utf-8", newline="\n")
    return out, {"gate_params": {"G1": {"objectives": MT}}}


def test_truc_khop_khi_du_nguyen_van(tmp_path):
    out, meta = _de_tai(tmp_path, "2. MỤC TIÊU CỤ THỂ:\n" + "\n".join(f"   2.{i} {o}" for i, o in enumerate(MT, 1)))
    k = NQ._truc_muc_tieu_ho_so_g2(out, "S", meta)
    assert k["muc"] == NQ.MUC_KHOP and "3/3" in k["ghi_chu"]


def test_truc_lech_mem_khi_vang_muc_tieu_du_nhan_o_cho_khac(tmp_path):
    """Ca BTM: MT3 vắng khỏi mục tiêu; nhãn «MT3» chỉ nằm giữa câu khác ⇒ vẫn là VẮNG, không phải «khác câu chữ»."""
    g2 = ("2. MỤC TIÊU CỤ THỂ:\n   2.1 MT1: Mô tả tỷ lệ được xét nghiệm đủ UACR (câu cũ, chưa thu hẹp).\n"
          f"   2.2 {MT[1]}\n\nExposure/index test: Biến giải thích cho MT3: tuổi, giới.\n")
    out, meta = _de_tai(tmp_path, g2)
    k = NQ._truc_muc_tieu_ho_so_g2(out, "S", meta)
    assert k["muc"] == NQ.MUC_LECH_MEM
    assert "1/3 mục tiêu G1 không có" in k["ghi_chu"] and "1 mục tiêu khác câu chữ" in k["ghi_chu"]
    assert [n["gia_tri"][:3] for n in k["nguon"]] == ["MT3", "MT1"]


def test_truc_can_xem_khi_chi_khac_cau_chu(tmp_path):
    g2 = "\n".join(f"   2.{i} {o}" for i, o in enumerate(MT, 1)).replace("thăm dò", "khám phá")
    out, meta = _de_tai(tmp_path, g2)
    k = NQ._truc_muc_tieu_ho_so_g2(out, "S", meta)
    assert k["muc"] == NQ.MUC_CAN_XEM and "1/3" in k["ghi_chu"]


def test_truc_bo_qua_dau_cau_va_hoa_thuong(tmp_path):
    g2 = "\n".join(f"   2.{i} {o.upper().replace('.', '').replace('(', '').replace(')', '')}"
                   for i, o in enumerate(MT, 1))
    out, meta = _de_tai(tmp_path, g2)
    assert NQ._truc_muc_tieu_ho_so_g2(out, "S", meta)["muc"] == NQ.MUC_KHOP


@pytest.mark.parametrize("co_g2, co_mt", [(False, True), (True, False)])
def test_truc_none_khi_chua_co_ho_so_hoac_muc_tieu(tmp_path, co_g2, co_mt):
    out = tmp_path / "S"
    out.mkdir()
    if co_g2:
        (out / "G2_A3_ETHICS_PACKAGE_S.md").write_text("x\n", encoding="utf-8", newline="\n")
    meta = {"gate_params": {"G1": {"objectives": MT if co_mt else []}}}
    assert NQ._truc_muc_tieu_ho_so_g2(out, "S", meta) is None


def test_truc_dang_ky_va_chay_trong_chuoi(tmp_path):
    assert "muc_tieu_ho_so_g2" in NQ.TRUC_CHUOI and NQ.TRUC_THEO_CONG["muc_tieu_ho_so_g2"] == ("G1", "G2", "G10")
    out, meta = _de_tai(tmp_path, "2. MỤC TIÊU CỤ THỂ:\n")
    ma = [k["ma"] for k in NQ.truc_chuoi(out, "S", meta, "")]
    assert "muc_tieu_ho_so_g2" in ma
    assert json.dumps(ma)  # mọi trục trả kết quả tuần tự hoá được


def test_truc_chua_du_khi_ho_so_khong_co_muc_muc_tieu(tmp_path):
    out, meta = _de_tai(tmp_path, "Hồ sơ đạo đức bản rút gọn — không có mục mục tiêu.\n")
    k = NQ._truc_muc_tieu_ho_so_g2(out, "S", meta)
    assert k["muc"] == NQ.MUC_CHUA_DU and "không có mục mục tiêu" in k["ghi_chu"]
