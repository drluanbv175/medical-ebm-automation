"""Hồi quy phát hiện #3 (Medium-High) của Workflow đối kháng đa-agent
2026-09-05 (vòng 20) trong app/sources/rss_feed.py::phan_loai_canh_bao().

CƠ CHẾ LỖI: bộ lọc thực phẩm _TP chứa 4 từ khóa mơ hồ không phải "dấu hiệu
RÕ RÀNG là thực phẩm" như đúng nguyên tắc bộ lọc này tự đặt ra:
  - "produce" — ĐỘNG TỪ tiếng Anh phổ biến ("can produce severe
    hypoglycaemia"), không chỉ danh từ "nông sản".
  - "juice" — trùng cảnh báo tương tác thuốc KINH ĐIỂN "grapefruit juice"
    (ức chế CYP3A4, ảnh hưởng statin/thuốc chẹn kênh canxi).
  - "beverage" — từ chung "tránh đồ uống có cồn/caffein khi dùng thuốc X".
  - "frozen" — trùng thuật ngữ lâm sàng "frozen shoulder" (đông cứng khớp
    vai/viêm dính bao khớp — tác dụng phụ đã ghi nhận của một số thuốc).
Hệ quả: cảnh báo AN TOÀN THUỐC THẬT (hạ đường huyết do insulin, tương tác
statin-nước bưởi, đông cứng khớp vai do thuốc) bị dán nhãn "Thu hồi thực
phẩm" (NHAN_CANH_BAO["thuc_pham"]) và biến mất khỏi mục an toàn thuốc của
báo cáo tuần (app/reports/weekly_ebm.py gom theo clinical_area).

BẢN VÁ: bỏ 4 từ khóa mơ hồ khỏi regex _TP. Các tín hiệu thực phẩm CÒN LẠI
(listeria, salmonella, undeclared milk/egg..., salsa, cheese, jalapeno, ice
cream...) vẫn đủ đặc hiệu để bắt các cảnh báo thu hồi thực phẩm thật.

Nguyên tắc viết test: gọi THẲNG phan_loai_canh_bao() thật."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.sources.rss_feed import phan_loai_canh_bao  # noqa: E402

_URL_THUOC = "https://www.fda.gov/safety/medwatch-safety-alerts-human-medical-products/x"


class TestTuKhoaMoHoKhongConDanNhamThucPham:
    """★★★ Ca chính — 4 từ khóa mơ hồ không được dán nhãn cảnh báo an toàn
    thuốc thật thành "Thu hồi thực phẩm"."""

    def test_produce_dong_tu_khong_bi_gan_nham_thuc_pham(self):
        loai = phan_loai_canh_bao(
            "FDA MedWatch: Insulin glargine dosing errors", _URL_THUOC,
            "Errors in dose selection can produce severe hypoglycaemia in older patients.")
        assert loai == "thuoc", (
            "TRƯỚC bản vá: 'produce' (động từ) trong _TP khớp bừa, gán nhầm "
            "cảnh báo hạ đường huyết do insulin thành 'Thu hồi thực phẩm'"
        )

    def test_grapefruit_juice_khong_bi_gan_nham_thuc_pham(self):
        loai = phan_loai_canh_bao(
            "Statin interaction warning", _URL_THUOC,
            "Concomitant grapefruit juice increases plasma simvastatin and "
            "rhabdomyolysis risk.")
        assert loai == "thuoc"

    def test_avoid_beverage_khong_bi_gan_nham_thuc_pham(self):
        loai = phan_loai_canh_bao(
            "Drug X patient counseling", _URL_THUOC,
            "Avoid alcoholic beverage while taking this medication.")
        assert loai == "thuoc"

    def test_frozen_shoulder_khong_bi_gan_nham_thuc_pham(self):
        loai = phan_loai_canh_bao(
            "Aromatase inhibitor safety update", _URL_THUOC,
            "Increased risk of frozen shoulder (adhesive capsulitis) reported "
            "with prolonged use.")
        assert loai == "thuoc"


class TestCanhBaoThucPhamThatVanDuocNhanDienDung:
    """Đối chứng bắt buộc — cảnh báo thu hồi thực phẩm THẬT (mang tín hiệu
    đặc hiệu khác) vẫn được nhận diện đúng như trước bản vá."""

    def test_listeria_produce_that_van_nhan_dien_dung(self):
        loai = phan_loai_canh_bao(
            "Recall of fresh produce due to Listeria contamination", "",
            "Listeria monocytogenes detected in cantaloupe.")
        assert loai == "thuc_pham"

    def test_undeclared_milk_beverage_that_van_nhan_dien_dung(self):
        loai = phan_loai_canh_bao(
            "Company recalls beverage due to undeclared milk", "",
            "undeclared milk allergen")
        assert loai == "thuc_pham"

    def test_salmonella_van_hoat_dong(self):
        loai = phan_loai_canh_bao(
            "Recall due to Salmonella risk", "", "Salmonella contamination found")
        assert loai == "thuc_pham"

    def test_ice_cream_van_hoat_dong(self):
        loai = phan_loai_canh_bao(
            "Ice cream recalled nationwide", "", "possible Listeria contamination")
        assert loai == "thuc_pham"


class TestUuTienDuongDanKhongDoi:
    """Đối chứng bắt buộc — đường dẫn FDA (tín hiệu đáng tin nhất, kiểm
    TRƯỚC từ khóa) vẫn ưu tiên đúng như hành vi gốc, không bị ảnh hưởng."""

    def test_url_drug_safety_update_luon_thang_du_tieu_de_co_tu_mo_ho(self):
        loai = phan_loai_canh_bao(
            "Some warning mentioning juice and produce",
            "https://www.mhra.gov.uk/drug-safety-update/something", "")
        assert loai == "thuoc"

    def test_url_medical_devices_van_hoat_dong(self):
        loai = phan_loai_canh_bao(
            "Device recall", "https://www.fda.gov/medical-devices/recall-x", "")
        assert loai == "thiet_bi"
