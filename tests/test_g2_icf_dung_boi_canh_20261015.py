"""Khuôn ICF G2 không chép câu mẫu sai bối cảnh vào phiếu đồng ý (15/10/2026, đề tài C1a).

Gói G2 của C1a (khảo sát cắt ngang một lần, phiếu không ghi tên) từng mang: «sẽ cố gắng lên lịch hẹn trùng với lần tái
khám», rủi ro «tự điền hoặc qua điện thoại/email», «khuyết danh hoàn toàn nếu không cần theo dõi; mã hóa nếu cần liên
kết», và «quyền xem, sửa hoặc xóa dữ liệu của mình» không kèm điều kiện — câu mẫu ghép mọi kịch bản thành lời hứa
sai với người tham gia. Ngoại tuyến."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
for _p in (REPO_ROOT, REPO_ROOT / "tools"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import run_g2_auto as G2  # noqa: E402


def _goi(thiet_ke: str, ten: str) -> str:
    return G2.generate_g2_full_package(
        topic="Đề tài thử", study_name="TEST-ICF", design_code=thiet_ke, design_primary=ten, reporting_std="STROBE",
        n_sr=0, n_rct=0, evidence_level="", registry=None, risk=G2.get_risk_profile(thiet_ke, ten),
        run_date="2026-10-15T10:00:00", n_adjusted=100)


def _icf(goi: str) -> str:
    return goi[goi.index("TÀI LIỆU 4"):goi.index("TÀI LIỆU 5")]


def test_cat_ngang_khong_mang_cau_mau_sai():
    icf = _icf(_goi("cross_sectional", "Cắt ngang mô tả"))
    for cau in ("lên lịch hẹn trùng", "qua điện thoại/email", "Khuyết danh hoàn toàn nếu không cần theo dõi"):
        assert cau not in icf, cau
    assert "Với dữ liệu còn liên kết được với anh/chị" in icf


@pytest.mark.parametrize("thiet_ke, ten", [("rct", "Thử nghiệm ngẫu nhiên"), ("cohort", "Thuần tập")])
def test_thiet_ke_nhieu_lan_tiep_xuc_van_co_lich_hen(thiet_ke, ten):
    assert "lên lịch hẹn trùng với lần tái khám" in _icf(_goi(thiet_ke, ten))
