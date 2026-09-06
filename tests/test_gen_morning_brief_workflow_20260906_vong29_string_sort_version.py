"""Hồi quy phát hiện #4 (MEDIUM) của Workflow đối kháng đa-agent 2026-09-06
(vòng 29) trong tools/gen_morning_brief.py — find_latest_draft() sắp xếp thư
mục phiên bản theo THỨ TỰ CHUỖI thay vì THỨ TỰ SỐ, nên "2026.2-draft" (cũ
hơn) bị chọn thay vì "2026.10-draft" (mới hơn).

CƠ CHẾ LỖI (TRƯỚC bản vá):
    def find_latest_draft(pack_dir):
        versions = sorted([d for d in pack_dir.iterdir() if d.is_dir()], reverse=True)
        return versions[0] if versions else None

`sorted()` không truyền `key` nên so sánh trực tiếp các đối tượng `Path` —
tương đương so sánh CHUỖI tên thư mục theo thứ tự từ điển (lexicographic),
KHÔNG phải so sánh số. Với knowledge pack đã trải qua đủ 10 lần cập nhật
(thư mục "2026.1-draft", "2026.2-draft", ..., "2026.10-draft"), ký tự '2'
(trong "2026.2") LỚN HƠN ký tự '1' (trong "2026.10") ngay ở vị trí sau dấu
chấm — "2026.2-draft" bị xếp "lớn hơn" "2026.10-draft" theo thứ tự chuỗi,
dù về mặt phiên bản 2026.10 MỚI HƠN 2026.2 gấp 5 lần.

Hậu quả: find_latest_draft() — hàm quyết định pack "mới nhất" hiển thị
trong bản tin sáng (bao gồm cả 🚨 Cờ đỏ và ⚠️ Cảnh báo thuốc) — chọn sai
thư mục, khiến bác sĩ nhận bản tin dựa trên nội dung CŨ đã bị thay thế mà
không có cảnh báo gì.

HIỆN TRẠNG DỮ LIỆU THẬT (lý do lỗi chưa từng lộ): tại thời điểm phát hiện,
mọi knowledge pack trong repo chỉ có ĐÚNG MỘT thư mục "2026.1-draft" — cơ
chế sai đã có sẵn, chỉ chờ lần cập nhật pack thứ 10 trở đi.

BẢN VÁ: _version_sort_key(path) tách phần SỐ ở đầu tên thư mục (regex
`^(\\d+)\\.(\\d+)`) thành tuple (năm, số thứ tự) rồi sort theo tuple số đó,
thay vì so sánh chuỗi thô. Tên thư mục KHÔNG khớp mẫu số (vd thư mục phụ
"_archive") bị xếp SAU mọi tên khớp mẫu — không được để một tên lạ vô
tình thắng một phiên bản thật.

Nguyên tắc viết test:
1. Ca chính — 3 thư mục "2026.1-draft"/"2026.2-draft"/"2026.10-draft" phải
   chọn đúng "2026.10-draft" là mới nhất.
2. Đối chứng — chỉ có 1 thư mục (hiện trạng dữ liệu thật hôm nay) vẫn chọn
   đúng thư mục đó, không đổi hành vi.
3. Đối chứng — thư mục KHÔNG khớp mẫu số (tên lạ) không được thắng một
   phiên bản thật đã có.
4. Đối chứng — thư mục pack rỗng (không có version nào) trả None, không
   crash."""
from __future__ import annotations

import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import gen_morning_brief as GMB  # noqa: E402


class TestFindLatestDraftSapXepSoHocKhongPhaiChuoi:
    """★★★ Ca chính — MUTATION-PHÂN-BIỆT ĐƯỢC. Thư mục phiên bản phải được
    chọn theo thứ tự SỐ, không phải thứ tự chuỗi."""

    def test_hai_chu_so_thang_mot_chu_so_theo_dung_thu_tu_so(self, tmp_path):
        for name in ("2026.1-draft", "2026.2-draft", "2026.10-draft"):
            (tmp_path / name).mkdir()

        result = GMB.find_latest_draft(tmp_path)

        assert result is not None
        assert result.name == "2026.10-draft", (
            "TRƯỚC bản vá: sorted() không truyền key nên so sánh CHUỖI tên thư "
            "mục — '2026.2-draft' xếp 'lớn hơn' '2026.10-draft' vì ký tự '2' > "
            "'1' ở vị trí sau dấu chấm, dù 2026.10 là phiên bản MỚI HƠN."
        )

    def test_thu_tu_thu_muc_tren_dia_khong_anh_huong_ket_qua(self, tmp_path):
        """Đối kháng thêm: tạo theo thứ tự CỐ Ý làm lộ lỗi cũ rõ nhất (2 sau
        cùng, 10 ở giữa) — kết quả vẫn phải đúng."""
        for name in ("2026.10-draft", "2026.1-draft", "2026.2-draft"):
            (tmp_path / name).mkdir()

        result = GMB.find_latest_draft(tmp_path)

        assert result.name == "2026.10-draft"


class TestDoiChungHienTrangMotPhienBanDuyNhat:
    """Đối chứng bắt buộc — hiện trạng dữ liệu thật hôm nay (mỗi pack chỉ có
    1 thư mục) không bị ảnh hưởng."""

    def test_mot_thu_muc_duy_nhat_van_duoc_chon(self, tmp_path):
        (tmp_path / "2026.1-draft").mkdir()

        result = GMB.find_latest_draft(tmp_path)

        assert result.name == "2026.1-draft"


class TestDoiChungTenLaKhongThangPhienBanThat:
    """Đối chứng bắt buộc — thư mục có tên KHÔNG khớp mẫu số (vd thư mục phụ
    trợ) không được thắng một phiên bản thật đã có."""

    def test_thu_muc_ten_la_khong_thang_phien_ban_that(self, tmp_path):
        (tmp_path / "2026.1-draft").mkdir()
        (tmp_path / "_archive").mkdir()

        result = GMB.find_latest_draft(tmp_path)

        assert result.name == "2026.1-draft"


class TestDoiChungPackRong:
    """Đối chứng bắt buộc — pack không có version nào trả None, không crash."""

    def test_pack_rong_tra_none(self, tmp_path):
        assert GMB.find_latest_draft(tmp_path) is None
