"""Hồi quy: `_tim_loi_goi_write_text()` trong tools/kiem_newline_vung_ky.py ĐẾM
NGOẶC bằng cách quét TỪNG KÝ TỰ `(`/`)` trên văn bản đã che (`_mask()`), nên
một dấu `(` KHÔNG CÂN nằm bên trong một string literal của một lời gọi LỒNG
BÊN TRONG sẽ đánh lừa bộ đếm `depth`.

Ca cụ thể (phát hiện qua ba lượt rà độc lập trong một Workflow đối kháng khi
kiểm một thay đổi khác — không phải giả định):

    dst.write_text(clean(src.read_text(x, "see foo(bar")), encoding="utf-8",
    newline="\\n")

Dấu `(` trong chuỗi `"see foo(bar"` khiến bộ đếm ký tự thô nghĩ nó VỪA MỞ
THÊM một cấp ngoặc lồng, nên `depth` bị đẩy lố một cấp cho toàn bộ phần còn
lại của lời gọi: `encoding="utf-8"` và `newline="\\n"` — vốn nằm ĐÚNG ở cấp
NGOÀI CÙNG của `write_text()` — bị bộ đếm coi là nằm trong lời gọi lồng bên
trong nên hoàn toàn biến mất khỏi `outer`. Hệ quả: luật kiểm ở `main()`
(`if 'encoding="utf-8"' not in outer or "newline=" in outer: continue`) đọc
`outer` là KHÔNG hề mang `encoding="utf-8"`, nên bỏ qua occurrence này hoàn
toàn — kể cả khi lời gọi thật sự THIẾU `newline=`, vi phạm trở nên vô hình
(false negative), đúng chiều nguy hiểm nhất cho một checker sinh ra để canh
CRLF phá hash ký (`ledger_approved`) trên Windows.

Repro này CHƯA từng có trong repo tại thời điểm phát hiện (grep `tools`,
`runtime`, `tests`, `scripts` không ra file thật nào khớp mẫu), nên lỗi ở
trạng thái tiềm ẩn — không phải một vi phạm đang bị che giấu trong lượt quét
hiện tại. Bản vá: `_tim_loi_goi_write_text()` nay định vị `.write_text(...)`
và khớp ngoặc bằng `tokenize` (cùng module `_mask()` đã dùng để phân biệt
'#' trong comment thật với '#' trong string literal) — một dấu '(' bên
trong một STRING token KHÔNG BAO GIỜ là một OP token riêng, nên không thể
đánh lừa bộ đếm `depth` theo cách ký tự thô mắc phải. Bản đếm ký tự thô cũ
được giữ lại làm `_tim_loi_goi_write_text_ngay_tho()` — CHỈ dùng khi `text`
không tokenize được.

Nguyên tắc viết test (theo đúng tiền lệ
tests/test_kiem_newline_vung_ky_workflow_20260905_vong24_nested_write_text.py
và tests/test_kiem_newline_vung_ky_mask_comment_vs_string_20260912.py): gọi
THẲNG `_tim_loi_goi_write_text()`/`_tim_loi_goi_write_text_ngay_tho()`/
`main()` thật, không mock — vì chính cơ chế đếm ngoặc là đối tượng cần kiểm."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import kiem_newline_vung_ky as K  # noqa: E402

# Đúng nguyên văn ca thật đã phát hiện — dấu '(' không cân trong chuỗi đối
# số của read_text() (lồng 2 cấp bên trong write_text()), lời gọi write_text
# NGOÀI CÙNG thiếu newline="\n".
# da-nen: bo-qua: chuoi mau tai hien dung ca that, THIEU newline= co chu y
DONG_THIEU_NEWLINE = (
    'dst.write_text(clean(src.read_text(x, "see foo(bar")), '
    'encoding="utf-8")'
)
# Đối chứng — cùng cấu trúc nhưng write_text() NGOÀI CÙNG ĐÃ có newline="\n".
DONG_DA_CO_NEWLINE = (
    'dst.write_text(clean(src.read_text(x, "see foo(bar")), '
    'encoding="utf-8", newline="\\n")'
)


class TestParenKhongCanTrongChuoiLongKhongLamLechDoSau:
    """★★★ Ca chính — dấu '(' không cân trong chuỗi của lời gọi LỒNG BÊN
    TRONG (read_text) không được làm `depth` bị đẩy lố, khiến `encoding=`/
    `newline=` của write_text() NGOÀI CÙNG biến mất khỏi `outer`."""

    def test_van_tim_thay_dung_1_match(self):
        found = K._tim_loi_goi_write_text(DONG_THIEU_NEWLINE)
        assert len(found) == 1, (
            f"TRƯỚC bản vá: dấu '(' không cân trong \"see foo(bar\" có thể "
            f"làm bộ đếm ký tự thô chạy lố qua toàn bộ phần còn lại của "
            f"văn bản (depth không bao giờ về 0) — tìm thấy {found}"
        )

    def test_outer_van_thay_encoding_utf8_du_co_paren_khong_can_trong_chuoi_long(self):
        """★★★ Đúng lỗi thật: TRƯỚC bản vá, `outer` chỉ còn 'clean()' — mất
        hẳn `encoding="utf-8"` — nên occurrence này bị `main()` bỏ qua HOÀN
        TOÀN (không được coi là một lời gọi write_text(..., encoding="utf-8")
        nào cả), dù nó thật sự thiếu newline=."""
        _start, _end, _full, outer = K._tim_loi_goi_write_text(DONG_THIEU_NEWLINE)[0]
        assert 'encoding="utf-8"' in outer, (
            f"TRƯỚC bản vá: dấu '(' trong \"see foo(bar\" (bên trong "
            f"read_text(), lồng 2 cấp) làm depth bị đẩy lố 1, nên "
            f"encoding=\"utf-8\" — vốn ở ĐÚNG cấp ngoài cùng của "
            f"write_text() — bị coi là nằm trong lời gọi lồng và biến mất "
            f"khỏi outer. outer hiện tại: {outer!r}"
        )

    def test_vi_pham_thieu_newline_duoc_bat_dung_khong_con_vo_hinh(self):
        """★★★ Khẳng định trực tiếp luật vi phạm của `main()` — occurrence
        THIẾU newline= này PHẢI bị gắn cờ, đúng lý do checker tồn tại."""
        _start, _end, _full, outer = K._tim_loi_goi_write_text(DONG_THIEU_NEWLINE)[0]
        vi_pham = 'encoding="utf-8"' in outer and "newline=" not in outer
        assert vi_pham, (
            f"TRƯỚC bản vá: vi phạm thật (thiếu newline=) trở nên VÔ HÌNH "
            f"vì luật `'encoding=\"utf-8\"' not in outer` đã đúng (bỏ qua "
            f"occurrence) trước khi luật `newline= in outer` kịp chạy — "
            f"outer hiện tại: {outer!r}"
        )

    def test_doi_chung_da_co_newline_o_dung_cap_ngoai_cung_khong_bi_bao_sai(self):
        """Đối chứng bắt buộc — cùng cấu trúc nhưng write_text() NGOÀI CÙNG
        ĐÃ có newline="\\n": không được báo vi phạm (outer phải thấy CẢ hai
        kwarg, không chỉ encoding=)."""
        found = K._tim_loi_goi_write_text(DONG_DA_CO_NEWLINE)
        assert len(found) == 1
        _start, _end, _full, outer = found[0]
        assert 'encoding="utf-8"' in outer
        assert "newline=" in outer, (
            f"TRƯỚC bản vá: newline=\"\\n\" cũng bị đẩy lố depth y hệt "
            f"encoding=\"utf-8\", nên dù đã viết đúng chuẩn vẫn không thấy "
            f"được trong outer — outer hiện tại: {outer!r}"
        )


class TestBanDemKyTuThoVanMangDungHanhViCuLamDuPhong:
    """Bảo đảm `_tim_loi_goi_write_text_ngay_tho()` (dự phòng khi `text`
    không tokenize được) vẫn mang ĐÚNG hành vi lịch sử — kể cả phần bị lỗi —
    để không ai vô tình "sửa luôn" bản dự phòng và làm mất tính năng dự
    phòng thật (dự phòng chỉ cần "còn hơn không quét được gì", không cần
    đúng bằng bản tokenize-hoá)."""

    def test_ban_dem_ky_tu_tho_van_bi_danh_lua_boi_paren_trong_chuoi(self):
        _start, _end, _full, outer = K._tim_loi_goi_write_text_ngay_tho(
            DONG_THIEU_NEWLINE
        )[0]
        assert outer == "clean()", (
            f"Bản đếm ký tự thô PHẢI còn giữ đúng hành vi lịch sử (kể cả "
            f"phần lỗi) để tài liệu hoá rõ vì sao cần chuyển sang tokenize "
            f"— outer hiện tại: {outer!r}"
        )


class TestMainBatDungViPhamTrenFileThatCoParenKhongCanTrongChuoiLong:
    """Kiểm qua đường đi THẬT: `main()` quét file tạm chứa đúng cấu trúc ca
    thật (lời gọi write_text() lồng 2 cấp, đối số chuỗi mang dấu '(' không
    cân, thiếu newline= ở cấp ngoài cùng)."""

    def test_main_bat_duoc_vi_pham_thieu_newline_dang_sau_paren_khong_can(
        self, tmp_path, monkeypatch,
    ):
        (tmp_path / "tools").mkdir()
        target = tmp_path / "tools" / "gia_lap_paren_khong_can_trong_chuoi.py"
        target.write_text(
            "def f(dst, src, clean, x):\n"
            f"    {DONG_THIEU_NEWLINE}\n",
            encoding="utf-8", newline="\n",
        )
        monkeypatch.setattr(K, "REPO", tmp_path)
        rc = K.main()
        assert rc == 2, (
            "TRƯỚC bản vá: dấu '(' không cân trong chuỗi đối số của "
            "read_text() (lồng bên trong) làm occurrence bị coi là không "
            "mang encoding=\"utf-8\" hợp lệ, nên vi phạm thiếu newline= "
            "thật lọt qua và main() trả 0 (sạch) dù có vi phạm thật"
        )

    def test_main_khong_bao_sai_khi_da_co_newline_du_van_co_paren_khong_can_trong_chuoi(
        self, tmp_path, monkeypatch,
    ):
        """Đối chứng bắt buộc — cùng cấu trúc paren-không-cân-trong-chuỗi
        nhưng write_text() ngoài cùng ĐÃ đúng chuẩn không được báo vi phạm
        sai."""
        (tmp_path / "tools").mkdir()
        target = tmp_path / "tools" / "gia_lap_paren_khong_can_da_dung.py"
        target.write_text(
            "def f(dst, src, clean, x):\n"
            f"    {DONG_DA_CO_NEWLINE}\n",
            encoding="utf-8", newline="\n",
        )
        monkeypatch.setattr(K, "REPO", tmp_path)
        rc = K.main()
        assert rc == 0
