"""Hồi quy phát hiện #2 (Cao) của Workflow đối kháng đa-agent 2026-09-05
(vòng 24) trong tools/kiem_newline_vung_ky.py — chốt CI (chạy thật trong
`.github/workflows/offline-ci.yml`, cả 2 lane) canh "bất biến newline vùng
ký" (`write_text(..., encoding="utf-8")` THIẾU `newline="\n"` sinh CRLF trên
Windows, phá hash chữ ký của cổng G-gate) có HAI lỗi độc lập cùng làm lọt vi
phạm THẬT ra khỏi CI mà không báo:

BUG A — regex cũ `MAU = re.compile(r'\\.write_text\\((?:[^()]|\\([^()]*\\))*?\\)')`
chỉ hỗ trợ ĐÚNG 1 CẤP ngoặc lồng bên trong `.write_text(...)`. Một lời gọi có
≥2 cấp lồng (vd `write_text(f(g(x)), encoding="utf-8")`) hoàn toàn KHÔNG được
`finditer()` tìm thấy — không phải khớp sai vị trí, mà chính occurrence đó
biến mất khỏi kết quả quét. Bằng chứng THẬT (không phải giả định): dòng
`tools/vn_prose_style.py:218` (trước bản vá)
`dst.write_text(clean_generated_prose(src.read_text(encoding="utf-8",
newline="\\n")), encoding="utf-8")` — outer write_text KHÔNG có newline=,
chỉ inner read_text mới có — chưa từng xuất hiện trong danh sách vi phạm dù
đúng loại lỗi checker sinh ra để bắt.

BUG B (độc lập, phát hiện khi verify Bug A) — SAU KHI vá Bug A để tìm được
occurrence có ≥2 cấp lồng, luật kiểm `"newline=" in s` (soi trên TOÀN BỘ
chuỗi khớp, kể cả nội dung của lời gọi LỒNG BÊN TRONG) vẫn sai: ca thật ở
trên có `newline="\\n"` nằm trong `read_text()` LỒNG BÊN TRONG — chuỗi con
"newline=" vẫn có mặt trong toàn bộ span dù outer write_text hoàn toàn
KHÔNG có kwarg này — khiến vi phạm bị bỏ qua LẦN THỨ HAI dù đã được tìm
thấy. Phải tách riêng `outer` (chỉ nội dung ở CẤP NGOÀI CÙNG của
write_text(), nội dung lồng bên trong bị lược còn dấu ngoặc rỗng "()") và
soi luật trên `outer`, không soi trên chuỗi khớp đầy đủ.

BẢN VÁ: `_tim_loi_goi_write_text()` — quét bằng ĐẾM NGOẶC THẬT (khớp mọi cấp
lồng, không giới hạn), trả về CẢ chuỗi khớp đầy đủ LẪN `outer` (chỉ cấp
ngoài cùng); `main()` kiểm `'encoding="utf-8"' not in outer or "newline=" in
outer` — thay `s` (chuỗi khớp đầy đủ) bằng `outer`.

Nguyên tắc viết test: gọi THẲNG `_tim_loi_goi_write_text()` thật (import từ
module), không mock — vì chính cơ chế quét ký tự là đối tượng cần kiểm."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import kiem_newline_vung_ky as K  # noqa: E402


class TestNgoacLongDaCapDuocTimThay:
    """★★★ Bug A — lời gọi write_text có ≥2 cấp ngoặc lồng bên trong phải
    được finditer/scanner tìm thấy, không bị bỏ sót hoàn toàn."""

    def test_hai_cap_long_van_tim_thay(self):
        text = 'dst.write_text(f(g(x)), encoding="utf-8")'  # da-nen: bo-qua: chuoi mau cho scanner
        found = K._tim_loi_goi_write_text(text)
        assert len(found) == 1, (
            "TRƯỚC bản vá: regex chỉ hỗ trợ 1 cấp ngoặc lồng nên lời gọi có "
            "2 cấp lồng (f(g(x))) hoàn toàn không được tìm thấy — finditer() "
            "trả về rỗng cho occurrence này"
        )

    def test_mot_cap_long_van_tim_thay_dung_hanh_vi_cu(self):
        """Đối chứng — 1 cấp lồng (hành vi regex cũ VẪN xử lý đúng) không
        được hồi quy sau khi đổi sang scanner mới."""
        text = 'dst.write_text(f(x), encoding="utf-8")'  # da-nen: bo-qua: chuoi mau cho scanner
        found = K._tim_loi_goi_write_text(text)
        assert len(found) == 1

    def test_khong_long_van_tim_thay(self):
        text = 'p.write_text(text, encoding="utf-8")'  # da-nen: bo-qua: chuoi mau cho scanner
        found = K._tim_loi_goi_write_text(text)
        assert len(found) == 1


class TestNewlineTrongLoiGoiLongKhongDuocTinhChoOuterCall:
    """★★★ Bug B — ca thật của tools/vn_prose_style.py:218: newline="\\n"
    nằm trong lời gọi LỒNG BÊN TRONG (read_text) không được phép làm outer
    write_text() bị coi là 'đã có newline='."""

    def test_ca_that_vn_prose_style_van_bi_bat_la_vi_pham(self):
        text = (
            'dst.write_text(clean_generated_prose(src.read_text('  # da-nen: bo-qua: chuoi mau cho scanner
            'encoding="utf-8", newline="\\n")), encoding="utf-8")'
        )
        found = K._tim_loi_goi_write_text(text)
        assert len(found) == 1
        _start, _end, _full, outer = found[0]
        assert 'encoding="utf-8"' in outer
        assert "newline=" not in outer, (
            "TRƯỚC bản vá: kiểm tra 'newline=' in <toàn bộ chuỗi khớp> sẽ "
            "tìm thấy newline=\"\\n\" từ read_text() LỒNG BÊN TRONG rồi kết "
            "luận SAI rằng outer write_text() đã có newline=, dù outer "
            "hoàn toàn không có kwarg này"
        )

    def test_newline_o_dung_outer_thi_khong_bi_bao_vi_pham(self):
        """Đối chứng — khi newline= nằm ĐÚNG ở outer write_text(), outer
        text phải chứa nó (không bị lọc mất theo hướng ngược lại)."""
        text = 'p.write_text(f(x), encoding="utf-8", newline="\\n")'
        found = K._tim_loi_goi_write_text(text)
        _start, _end, _full, outer = found[0]
        assert "newline=" in outer


class TestMainPhatHienDungViPhamThatTrenFileThat:
    """Kiểm qua đường đi THẬT: main() quét file thật, đúng ca lịch sử của
    tools/vn_prose_style.py (mô phỏng bằng file tạm cùng nội dung)."""

    def test_main_bat_duoc_vi_pham_hai_cap_long_tren_file_that(self, tmp_path, monkeypatch):
        (tmp_path / "tools").mkdir()
        target = tmp_path / "tools" / "gia_lap_vn_prose_style.py"
        target.write_text(
            'def f(src, dst):\n'
            '    dst.write_text(g(src.read_text(encoding="utf-8", newline="\\n")), '
            'encoding="utf-8")\n',
            encoding="utf-8", newline="\n",
        )
        monkeypatch.setattr(K, "REPO", tmp_path)
        rc = K.main()
        assert rc == 2, (
            "TRƯỚC bản vá: cả Bug A (không tìm thấy occurrence) và Bug B "
            "(newline= của lời gọi lồng bị tính nhầm cho outer) đều khiến "
            "vi phạm này lọt qua, main() trả 0 (sạch) dù có vi phạm thật"
        )

    def test_main_khong_bao_dong_gia_khi_that_su_khong_vi_pham(self, tmp_path, monkeypatch):
        """Đối chứng bắt buộc — file có write_text ĐÃ đúng chuẩn (newline=
        ở đúng outer) không được báo vi phạm."""
        (tmp_path / "tools").mkdir()
        target = tmp_path / "tools" / "gia_lap_dung_chuan.py"
        target.write_text(
            'def f(src, dst):\n'
            '    dst.write_text(g(src.read_text(encoding="utf-8")), '  # da-nen: bo-qua: vi du minh hoa
            'encoding="utf-8", newline="\\n")\n',
            encoding="utf-8", newline="\n",
        )
        monkeypatch.setattr(K, "REPO", tmp_path)
        rc = K.main()
        assert rc == 0
