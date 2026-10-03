"""G2-AUTO-05 phải đếm cả Ô MẪU CHUNG sót từ khuôn sinh, không chỉ nhãn [CẦN] (03/10/2026).

Sự cố: bộ hồ sơ C1a đã điền hết mục đích thật, nhưng ICF tiếng Việt vẫn còn câu ví dụ thử nghiệm thuốc
(«thuốc/can thiệp X», «[bệnh]») cùng «[đơn vị]», «[tài trợ nếu có]», «[nơi thực hiện]»; ICF tiếng Anh còn 14 ô
«[TO BE COMPLETED]». Cổng chỉ đếm «[CẦN» ⇒ khi mọi [CẦN] được điền sẽ báo READY_FOR_IRB_SUBMISSION cho một phiếu
đồng thuận người bệnh ký còn chữ mẫu.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import g2_quality_gate as G2Q  # noqa: E402
import run_g2_auto as G2  # noqa: E402
from test_g2_quality_gate import _evaluate, _package  # noqa: E402


@pytest.mark.parametrize("dong", [
    "Institution: [TO BE COMPLETED]",
    "   [TO BE COMPLETED — plain language, no jargon]",
    'Ví dụ: "Tìm hiểu xem thuốc/can thiệp X có giúp cải thiện tình',
    "trạng [bệnh] ở người bệnh như anh/chị không.\"",
    "Nghiên cứu do [đơn vị] thực hiện với sự hỗ trợ của [tài trợ",
    "   Cỡ mẫu dự kiến 1000, với sự hỗ trợ của [tài trợ",  # riêng ô ngắt dòng chưa đóng ngoặc
    "khoảng 1000 người tham gia tại [nơi thực hiện].",
])
def test_o_mau_chung_bi_dem(dong: str) -> None:
    assert G2Q.unresolved_critical_placeholders(_package() + dong + "\n"), dong


@pytest.mark.parametrize("dong", [
    "Can thiệp X theo protocol",                       # tên can thiệp thật trong fixture, không phải câu mẫu
    "[Chi tiết xem Bảng rủi ro–lợi ích, Tài liệu 3]",  # tham chiếu chéo hợp lệ
    "Đơn vị thực hiện: Khoa Khám bệnh C1a",
    "Thang đo [đơn vị đo: điểm]",
])
def test_khong_bao_dong_gia(dong: str) -> None:
    assert G2Q.unresolved_critical_placeholders(_package() + dong + "\n") == []


def test_goi_con_o_mau_chung_khong_bao_gio_ready(tmp_path) -> None:
    report = _evaluate(tmp_path, _package() + "\nInstitution: [TO BE COMPLETED]\n", ledger=False)
    assert report["status"] == G2Q.STATUS_DRAFT
    assert report["package_ready_for_submission"] is False


def test_khuon_sinh_dien_het_can_van_con_o_mau_bi_bat() -> None:
    """Mô phỏng đúng sự cố: sinh hồ sơ thật bằng khuôn, điền HẾT mọi ô [CẦN…] ⇒ cổng vẫn phải thấy ô mẫu chung."""
    goi = G2.generate_g2_full_package(
        topic="Sự hài lòng của người bệnh ngoại trú", study_name="TEST-O-MAU", design_code="cross_sectional",
        design_primary="Cắt ngang mô tả", reporting_std="STROBE", n_sr=0, n_rct=0, evidence_level="",
        registry=None, risk=G2.get_risk_profile("cross_sectional", "Cắt ngang mô tả"), run_date="2026-10-03T10:00:00",
        n_adjusted=1000,
    )
    da_dien = re.sub(r"\[CẦN[^\]]*\]", "nội dung thật", goi)
    assert "[CẦN" not in da_dien.upper()
    con = G2Q.unresolved_critical_placeholders(da_dien)
    assert any("thuốc/can thiệp X" in x for x in con), "câu ví dụ thử nghiệm thuốc trong ICF lọt cổng"
    assert any("TO BE COMPLETED" in x for x in con), "ICF tiếng Anh còn [TO BE COMPLETED] lọt cổng"


def test_khuon_sinh_dan_xoa_dong_vi_du() -> None:
    goi = G2.generate_g2_full_package(
        topic="Sự hài lòng của người bệnh ngoại trú", study_name="TEST-O-MAU", design_code="cross_sectional",
        design_primary="Cắt ngang mô tả", reporting_std="STROBE", n_sr=0, n_rct=0, evidence_level="",
        registry=None, risk=G2.get_risk_profile("cross_sectional", "Cắt ngang mô tả"), run_date="2026-10-03T10:00:00",
    )
    assert "XOÁ dòng ví dụ" in goi

