"""Khối câu trả lời biểu mẫu hồ sơ trình đơn vị nằm ở khoá riêng `study_meta.ho_so_don_vi`, ngoài gate_params
(23/11/2026).

Luật được canh:
  * Thêm/sửa khối hồ sơ (HĐĐĐ, đề tài cơ sở) KHÔNG đổi dấu vân tay xác nhận G1, KHÔNG đổi dấu đầu vào G2 mà Hội đồng
    đã duyệt, KHÔNG kích hoạt phép quét chuỗi G1 của hội đồng cổng (ghép hệ thống ngoài).
  * Chốt xác nhận không bị làm yếu: đổi một quyết định G1 thật vẫn đổi dấu; thêm bất kỳ khoá nào vào gate_params.G1
    vẫn đổi dấu (miền băm của G1 là mọi khoá trừ khoá xác nhận).
  * Bộ dựng đọc khoá mới; khối ở vị trí cũ trong gate_params không được đọc ngầm — trích và `kiem` đều báo để dời.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT), str(ROOT / "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

docx = pytest.importorskip("docx")

from tests import test_ho_so_nguon_chung_20261122 as _TNC  # noqa: E402
from tests.test_ho_so_nguon_chung_20261122 import STUDY, _chay_dtcs, _chay_hdd, dat_khoi  # noqa: E402
from tools import g1_quality_gate as G1Q  # noqa: E402
from tools import g2_quality_gate as G2Q  # noqa: E402
from tools import ho_so_dtcs_bvqy175 as DTCS  # noqa: E402
from tools import ho_so_hdd_bvqy175 as HDD  # noqa: E402
from tools import ho_so_nguon_chung as HSC  # noqa: E402
from tools import hoi_dong_cong as HDC  # noqa: E402

de_tai = _TNC.de_tai  # fixture dùng chung: đề tài giả đủ nguồn + bộ mẫu giả + sổ lý lịch giả
THIET_KE = {"internal_code": "cross_sectional"}
#: Khối ĐTCS có dòng tiến độ nhắc eHospital — đúng kiểu nội dung từng làm phép quét G1 «ghép hệ thống ngoài» báo sai.
KHOI_DTCS_HIS = {"thuyet_minh": {"m22_san_pham": "Dạng I: 01 bài báo giả."},
                 "m21_hang": [{"dau": "Thu thập số liệu", "chu_tri": "Chủ nhiệm trích hồ sơ trên eHospital"}]}


def _meta_khong_khoi() -> dict:
    m = _TNC._meta()
    m.pop(HSC.KHOA_HO_SO_DON_VI, None)
    return m


def test_vi_tri_khoi_ngoai_gate_params() -> None:
    assert HDD.KHOI_HDD == HSC.KHOI_HDD and DTCS.KHOI_DTCS == HSC.KHOI_DTCS
    for khoi in (HSC.KHOI_HDD, HSC.KHOI_DTCS):
        assert khoi[0] == HSC.KHOA_HO_SO_DON_VI != "gate_params", khoi


def test_khoi_ho_so_khong_doi_dau_g1_g2(tmp_path: Path) -> None:
    goc = _meta_khong_khoi()
    dau_g1 = G1Q.dau_van_tay_g1(goc, THIET_KE)
    dau_g2, _ = G2Q.dau_dau_vao_g2(tmp_path, goc)
    m = copy.deepcopy(goc)
    dat_khoi(m, DTCS.KHOI_DTCS, KHOI_DTCS_HIS)
    dat_khoi(m, HDD.KHOI_HDD, _TNC.KHOI_HDD)
    assert G1Q.dau_van_tay_g1(m, THIET_KE) == dau_g1, "khối hồ sơ đơn vị không được đổi dấu xác nhận G1"
    assert G2Q.dau_dau_vao_g2(tmp_path, m)[0] == dau_g2, "khối hồ sơ đơn vị không được đổi dấu đầu vào G2"
    m2 = copy.deepcopy(m)
    dat_khoi(m2, DTCS.KHOI_DTCS, {"thuyet_minh": {"m22_san_pham": "Sản phẩm khác."}})
    assert G1Q.dau_van_tay_g1(m2, THIET_KE) == dau_g1, "sửa khối hồ sơ cũng không đổi dấu G1"


def test_doi_quyet_dinh_g1_van_doi_dau() -> None:
    """Chốt xác nhận G1 giữ nguyên độ mạnh: quyết định thật đổi ⇒ dấu đổi; khoá lạ thêm vào G1 ⇒ dấu đổi."""
    goc = _meta_khong_khoi()
    dau = G1Q.dau_van_tay_g1(goc, THIET_KE)
    m = copy.deepcopy(goc)
    m["gate_params"]["G1"]["objectives"] = ["MT1 (mô tả): Mục tiêu khác."]
    assert G1Q.dau_van_tay_g1(m, THIET_KE) != dau
    m = copy.deepcopy(goc)
    m["gate_params"]["G1"]["study_period"] = "Thực hiện dự kiến 01/2027–12/2027."
    assert G1Q.dau_van_tay_g1(m, THIET_KE) != dau
    m = copy.deepcopy(goc)
    m["gate_params"]["G1"]["ho_so_dtcs"] = KHOI_DTCS_HIS  # vị trí cũ: vẫn trong miền băm G1 (không loại trừ ngầm)
    assert G1Q.dau_van_tay_g1(m, THIET_KE) != dau


def test_khoi_ho_so_khong_kich_hoat_quet_g1_ghep_ngoai(tmp_path: Path) -> None:
    """Hội đồng cổng quét chuỗi gate_params.G1 tìm «eHospital/HIS…»: khối hồ sơ ở khoá riêng không lọt vào phép quét."""
    m = _meta_khong_khoi()
    dat_khoi(m, DTCS.KHOI_DTCS, KHOI_DTCS_HIS)
    (tmp_path / "study_meta.json").write_text(json.dumps(m, ensure_ascii=False), encoding="utf-8", newline="\n")
    assert HDC._kiem_g2_ghep_ngoai(tmp_path, STUDY) == []
    m["gate_params"]["G1"]["ho_so_dtcs"] = KHOI_DTCS_HIS
    (tmp_path / "study_meta.json").write_text(json.dumps(m, ensure_ascii=False), encoding="utf-8", newline="\n")
    assert HDC._kiem_g2_ghep_ngoai(tmp_path, STUDY), "đặt trong G1 thì phép quét báo (lý do phải dời khối)"


def _doi_sang_vi_tri_cu(m: dict) -> None:
    khoi = m.pop(HSC.KHOA_HO_SO_DON_VI)
    m["gate_params"]["G2"]["ho_so_hdd"] = khoi["hdd"]
    m["gate_params"]["G1"]["ho_so_dtcs"] = {"thuyet_minh": {"m22_san_pham": "Dạng I: sản phẩm ở vị trí cũ."}}


def test_bo_dung_khong_doc_vi_tri_cu_va_bao(de_tai, capsys) -> None:
    goc = de_tai(meta_sua=_doi_sang_vi_tri_cu)
    d, ghi = HDD.trich_du_kien(goc, STUDY)
    assert d["phu_luc_11"]["muc"]["1a"] != _TNC.KHOI_HDD["phu_luc_11"]["muc"]["1a"], "không đọc khối ở vị trí cũ"
    assert any("gate_params.G2.ho_so_hdd" in g and "vị trí cũ" in g for g in ghi), ghi
    dt, ghi_dt = DTCS.trich_du_kien(goc, STUDY, so_ca_nhan=Path(DTCS.tim_so_ca_nhan()))
    assert dt["thuyet_minh"].get("m22_san_pham") != "Dạng I: sản phẩm ở vị trí cũ."
    assert any("gate_params.G1.ho_so_dtcs" in g and "vị trí cũ" in g for g in ghi_dt), ghi_dt
    assert _chay_hdd(goc, "trich", "--ghi", "--ghi-de") == 0
    assert _chay_dtcs(goc, "trich", "--ghi", "--ghi-de") == 0
    capsys.readouterr()
    _chay_hdd(goc, "kiem")
    assert "gate_params.G2.ho_so_hdd ở vị trí cũ" in capsys.readouterr().out
    _chay_dtcs(goc, "kiem")
    assert "gate_params.G1.ho_so_dtcs ở vị trí cũ" in capsys.readouterr().out


def test_bo_dung_doc_khoa_moi(de_tai) -> None:
    goc = de_tai(meta_sua=lambda m: dat_khoi(m, HSC.KHOI_DTCS, KHOI_DTCS_HIS))
    d, ghi = HDD.trich_du_kien(goc, STUDY)
    assert d["phu_luc_11"]["muc"]["1a"] == _TNC.KHOI_HDD["phu_luc_11"]["muc"]["1a"]
    assert not any("vị trí cũ" in g for g in ghi)
    dt, ghi_dt = DTCS.trich_du_kien(goc, STUDY, so_ca_nhan=Path(DTCS.tim_so_ca_nhan()))
    assert dt["thuyet_minh"]["m22_san_pham"] == "Dạng I: 01 bài báo giả."
    assert dt["_nguon"]["thuyet_minh.m22_san_pham"].endswith("ho_so_don_vi.dtcs.thuyet_minh.m22_san_pham")
    assert not any("vị trí cũ" in g for g in ghi_dt)
