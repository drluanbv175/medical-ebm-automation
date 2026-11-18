"""K8 bổ sung (18/11/2026): dấu vết máy mà K1–K8 bỏ sót, lộ khi phản biện máy lượt 2 đọc đề cương BTM thật và bác sĩ
xác nhận «máy đúng». Bộ sinh đề cương gỡ đúng các ghi chú nguồn gốc mà K8 nay bắt (cặp sinh–kiểm khớp nhau).

Đo trước khi chốt mẫu: đề cương BTM cũ 11 lỗi K8 thật · BTM đã sửa 0 · C1a 0 · 24 đề cương giả lập 0 (sau khi
bộ sinh gỡ).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))

import kiem_de_cuong_nop_hoi_dong as K  # noqa: E402
import sinh_de_cuong_nop_hoi_dong as G  # noqa: E402


@pytest.mark.parametrize(
    "dong, nhan",
    [
        # Nguyên văn đề cương BTM trước khi sửa
        ("… đái tháo đường típ 1 hoặc thể khác (PICO đã chốt).", "(… đã chốt)"),
        ("… huỷ sau khi khoá dữ liệu (quy trình dữ liệu đã chốt).", "(… đã chốt)"),
        ("… khung mẫu eHospital (theo quy trình chuẩn SOP-TR-01 của đề tài).", "SOP-…"),
        ("Thời gian mắc ĐTĐ (năm chẩn đoán không ghi — mã KGHS), BMI …", "mã KGHS"),
        ("  - Phụ 1: người có phân loại bệnh thận mạn theo xét nghiệm khác 9 (đủ xét nghiệm).", "khác 9"),
        ("  - Phụ 2: người có phân loại bệnh thận mạn theo xét nghiệm = 2.", "= 1"),
        ("  - Phụ 3a: người có đủ chỉ định ACEi/ARB theo KDIGO 2022, trừ … ACEi/ARB = 1 (báo cáo riêng).", "= 1"),
        ("… mới trong nước. Mức tính mới: mở rộng bối cảnh — không mới trên thế giới.", "Mức tính mới"),
        ("… hoặc mô tả kê đơn. Phạm vi tra: PubMed và Crossref; chưa tra Google Scholar.", "Mức tính mới"),
        ("HbA1c 3 mức (< 7% / ≥ 7% / không làm HbA1c năm 2026; biến hbA1c 3 mức), đang dùng insulin", "biến hbA1c"),
    ],
)
def test_k8_bat_dau_vet_moi(dong, nhan):
    loi = K.loi_k8(dong)
    assert len(loi) == 1 and nhan in loi[0], loi


@pytest.mark.parametrize(
    "dong",
    [
        "Người từ 18 tuổi, chẩn đoán đái tháo đường típ 2 (mã ICD-10 E11), quản lý ngoại trú.",
        "Cỡ mẫu tối thiểu N = 385; gán đa trị m = 20 bộ, quy tắc Rubin.",
        "| don_ha_glucose_nam | Có đơn thuốc hạ glucose | Nhị phân | 1 = Có; 0 = Không | Phiếu thu thập số liệu |",
        "Biến kết cục: gãy xương mới (chỉ báo biến cố (có/không)) trong 12 tháng.",
        "Phân tích đơn biến; biến số định lượng mô tả bằng trung vị.",
        "Đề tài mở rộng bối cảnh: chủ đề không mới trên thế giới, nhưng chưa được đo trọn tại bệnh viện quân đội.",
        "mã ATC A10 cho thuốc hạ glucose; mã ICD-10 N18 cho bệnh thận mạn.",
        "| `egfr_k` | eGFR tại kết quả creatinin thứ k (k = 1…6) | Định lượng |",
    ],
)
def test_k8_khong_bao_nham(dong):
    assert K.loi_k8(dong) == []


def test_k8_thoi_diem_huy_bang_noi_ma_lech_nhau():
    """BTM 17/11: mục đạo đức và quản lý dữ liệu «huỷ sau khi khoá dữ liệu», cam kết bảo mật «sau khi kết thúc»."""
    lech = "- Bảo mật: … huỷ sau khi khoá dữ liệu.\n\n## Phụ lục\nCam kết: … huỷ sau khi kết thúc nghiên cứu;\n"
    loi = K.loi_k8(lech)
    assert any("thời điểm huỷ bảng nối mã khác nhau" in x for x in loi)
    assert K.loi_k8("… huỷ sau khi khoá dữ liệu.\n… huỷ sau khi khoá dữ liệu (DMP).\n") == []


@pytest.mark.parametrize(
    "vao, ra",
    [
        ("huỷ sau khi khoá dữ liệu (quy trình dữ liệu đã chốt)", "huỷ sau khi khoá dữ liệu"),
        ("thể khác (PICO đã chốt).", "thể khác."),
        ("Không bắt buộc đăng ký (PI chốt ở G2)", "Không bắt buộc đăng ký"),  # luật cũ của bộ sinh đã gỡ dạng này
    ],
)
def test_bo_sinh_go_ghi_chu_nguon_goc(vao, ra):
    assert G.lam_sach(vao) == ra


def test_bo_sinh_giu_ngoac_noi_dung():
    assert G.lam_sach("Chi tiết ở mục 4.9 (xem Phụ lục D).") == "Chi tiết ở mục 4.9 (xem Phụ lục D)."


def test_van_ban_sau_khi_bo_sinh_go_thi_k8_sach():
    """Cặp sinh–kiểm khớp: mọi ghi chú bộ sinh gỡ thì K8 không còn gì để bắt."""
    vao = ("Thu thập: trích hồ sơ eHospital; nhập kép (quy trình dữ liệu đã chốt). "
           "Đăng ký: không bắt buộc (PI chốt ở G2). Tiêu chuẩn: E11 (PICO đã chốt).")
    assert K.loi_k8(vao) and K.loi_k8(G.lam_sach(vao)) == []


# ── 18/11/2026 (chiều): mã phân tích độ nhạy bị hạ chữ — đề cương BTM «Đn1…Đn9», kế hoạch phân tích «ĐN1…ĐN9» ──────
@pytest.mark.parametrize("dong", ["Đn2 — xét nghiệm ngoài viện: kết cục chính tính cả kết quả ngoài BVQY175.",
                                  "… (Đn6 ở mục 4.9 chỉ cần một lần) …"])
def test_k8_bat_ma_do_nhay_bi_ha_chu(dong):
    loi = K.loi_k8(dong)
    assert len(loi) == 1 and "Đn2" in loi[0], loi


@pytest.mark.parametrize("dong", ["ĐN2 — xét nghiệm ngoài viện.", "Đơn thuốc 2 lần", "Đnh2", "điểm Đ12"])
def test_k8_ma_do_nhay_dung_chu_khong_bao(dong):
    assert K.loi_k8(dong) == []


def test_bo_sinh_giu_ma_in_hoa_co_chu_so():
    """Cụm IN HOA có chữ số là mã (ĐN2, MT1) — không hạ chữ; chữ nhấn mạnh không số vẫn hạ như cũ."""
    assert G._cau("ĐN2 — xét nghiệm ngoài viện") == "ĐN2 — xét nghiệm ngoài viện."
    assert G._cau("MT1 và ĐN4") == "MT1 và ĐN4."
    assert G._cau("Quần thể CHÍNH") == "Quần thể chính."
    assert G._cau("KHÔNG kiểm định") == "Không kiểm định."
