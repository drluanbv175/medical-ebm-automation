"""Hồi quy: `_mask()` trong tools/kiem_newline_vung_ky.py xử lý ký tự '#' một
cách NGÂY THƠ (cắt tại '#' ĐẦU TIÊN trên dòng), không phân biệt được '#' mở
đầu một COMMENT thật với '#' NẰM BÊN TRONG một string literal.

Ca thật đã tái hiện (không phải giả định): `_dung_bo_ba_toi_thieu()` trong
tests/test_g6_quality_gate_workflow_20260904_auto06_real_filenames.py gọi
`.write_text("# Script phân tích\\n(placeholder)\\n", encoding="utf-8",
newline="\\n")` — chuỗi đối số chứa '#'. Bản `_mask()` cũ cắt cụt dòng này
ngay tại '#' trong chuỗi, làm mất luôn dấu ngoặc đóng và mọi ký tự phía sau
TRÊN CÙNG một dòng (kể cả `encoding=`/`newline=` của chính lời gọi đó lẫn
mã nguồn của các lời gọi `write_text()` KẾ TIẾP). Hệ quả xác nhận bằng cách
gọi thẳng `_tim_loi_goi_write_text()` trên văn bản đã qua `_mask()` cũ (bản
lịch sử): 3 lời gọi `write_text()` liên tiếp gộp thành 1 match rác duy nhất,
và một vi phạm THẬT (thiếu `newline=`) nằm ngay lời gọi thứ hai trở nên VÔ
HÌNH với checker.

BẢN VÁ: `_mask()` nay tokenize văn bản bằng module `tokenize` chuẩn của
Python — chính bộ phân tích cú pháp dùng để biên dịch — nên phân biệt ĐÚNG
COMMENT token với STRING token bất kể loại nháy (một/hai/ba nháy, kể cả
f-string): '#' bên trong string literal không bao giờ trở thành COMMENT
token. Chỉ token COMMENT và token STRING dạng BA NHÁY (docstring-style,
giữ nguyên hành vi che-docstring cũ chống bắt lời-kể-về-lỗi) bị che; chuỗi
một/hai nháy — kể cả chuỗi chứa '#' — được giữ NGUYÊN VĂN vì
`_tim_loi_goi_write_text()` so khớp trực tiếp `'encoding="utf-8"' in outer`
trên văn bản gốc.

Nguyên tắc viết test (theo đúng tiền lệ
tests/test_kiem_newline_vung_ky_workflow_20260905_vong24_nested_write_text.py):
gọi THẲNG `_mask()`/`_tim_loi_goi_write_text()`/`main()` thật, không mock —
vì chính cơ chế che ký tự là đối tượng cần kiểm."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import kiem_newline_vung_ky as K  # noqa: E402


def _dem_va_gan_nhan(text: str) -> list[dict]:
    """Tiện ích dùng chung cho các test dưới: chạy `_tim_loi_goi_write_text`
    trên `text` rồi gắn nhãn vi_pham + số dòng cho từng match, đúng logic
    `main()` đang dùng thật (`encoding="utf-8"` có mặt và `newline=` vắng
    mặt ở `outer`)."""
    ra = []
    for start, _end, _full, outer in K._tim_loi_goi_write_text(text):
        ra.append({
            "dong": text[:start].count("\n") + 1,
            "outer": outer,
            "vi_pham": 'encoding="utf-8"' in outer and "newline=" not in outer,
        })
    return ra


class TestMaskKhongCatCutKhiChuoiChuaKyTuHash:
    """★★★ Ca chính, đúng nguyên văn ca thật đã phát hiện: một `write_text()`
    có '#' trong chuỗi đối số, theo sau bởi một `write_text()` KHÁC thiếu
    `newline=` — phải được tìm thấy RIÊNG và bắt được vi phạm thật."""

    DONG_MAU = [
        'def _dung_bo_ba_toi_thieu(thu_muc, study):',
        '    (thu_muc / f"G6_A7_ANALYSIS_SCRIPTS_{study}.md").write_text(',
        '        "# Script phân tích\\n(placeholder)\\n", '
        'encoding="utf-8", newline="\\n")',
        '    (thu_muc / f"G4_A5_SAP_FINAL_{study}.md").write_text(',  # da-nen: bo-qua: chuoi mau tai hien dung ca that, THIEU newline= co chu y
        '        "# SAP\\n(placeholder)\\n", encoding="utf-8")',
        '    (thu_muc / "G6_checkpoint.json").write_text(',
        '        "{}", encoding="utf-8", newline="\\n")',
    ]

    def test_ba_loi_goi_lien_tiep_duoc_tim_thay_rieng_biet(self):
        text = "\n".join(K._mask(self.DONG_MAU))
        found = K._tim_loi_goi_write_text(text)
        assert len(found) == 3, (
            "TRƯỚC bản vá: '#' trong chuỗi của lời gọi thứ nhất bị hiểu nhầm "
            "là mở đầu comment, cắt cụt dòng và làm 3 lời gọi write_text() "
            "liên tiếp gộp thành 1 match rác duy nhất — _mask() mới phải "
            "giữ chúng tách biệt"
        )

    def test_loi_goi_thieu_newline_ngay_sau_chuoi_co_hash_bi_bat_dung(self):
        """★★★ Đúng lỗi thật: lời gọi thứ hai (chuỗi "# SAP...") THIẾU
        newline= — phải bị gắn cờ vi phạm, KHÔNG được vô hình."""
        text = "\n".join(K._mask(self.DONG_MAU))
        ket_qua = _dem_va_gan_nhan(text)
        assert len(ket_qua) == 3
        vi_pham = [k for k in ket_qua if k["vi_pham"]]
        assert len(vi_pham) == 1, (
            f"TRƯỚC bản vá: match duy nhất còn lại không hề chứa "
            f"'encoding=\"utf-8\"' hợp lệ nên KHÔNG BAO GIỜ bị gắn cờ vi "
            f"phạm dù có 1 lời gọi thật thiếu newline= — kết quả hiện tại: "
            f"{ket_qua}"
        )
        assert '"# SAP' in vi_pham[0]["outer"]

    def test_hai_loi_goi_con_lai_da_co_newline_khong_bi_bao_sai(self):
        """Đối chứng bắt buộc — hai lời gọi ĐÃ có `newline="\\n"` đúng chuẩn
        (kể cả lời gọi có '#' trong chuỗi) không được báo vi phạm sai."""
        text = "\n".join(K._mask(self.DONG_MAU))
        ket_qua = _dem_va_gan_nhan(text)
        khong_vi_pham = [k for k in ket_qua if not k["vi_pham"]]
        assert len(khong_vi_pham) == 2


class TestMainBatDungViPhamThatTrenFileThat:
    """Kiểm qua đường đi THẬT: `main()` quét file tạm có đúng cấu trúc lịch
    sử của `_dung_bo_ba_toi_thieu()` (một write_text() chứa '#' trong chuỗi,
    kèm write_text() khác thiếu newline= ngay sau đó)."""

    NOI_DUNG_FILE = (
        'def _dung_bo_ba_toi_thieu(thu_muc, study):\n'
        '    (thu_muc / f"G6_A7_ANALYSIS_SCRIPTS_{study}.md").write_text(\n'
        '        "# Script phân tích\\n(placeholder)\\n", '
        'encoding="utf-8", newline="\\n")\n'
        '    (thu_muc / f"G4_A5_SAP_FINAL_{study}.md").write_text(\n'  # da-nen: bo-qua: chuoi mau tai hien dung ca that, THIEU newline= co chu y
        '        "# SAP\\n(placeholder)\\n", encoding="utf-8")\n'
        '    (thu_muc / "G6_checkpoint.json").write_text(\n'
        '        "{}", encoding="utf-8", newline="\\n")\n'
    )

    def test_main_bat_duoc_vi_pham_thieu_newline_sau_chuoi_co_hash(
        self, tmp_path, monkeypatch,
    ):
        (tmp_path / "tools").mkdir()
        target = tmp_path / "tools" / "gia_lap_g6_workflow.py"
        target.write_text(self.NOI_DUNG_FILE, encoding="utf-8", newline="\n")
        monkeypatch.setattr(K, "REPO", tmp_path)
        rc = K.main()
        assert rc == 2, (
            "TRƯỚC bản vá: '#' trong chuỗi của lời gọi đầu tiên làm gộp cả "
            "3 lời gọi write_text() liên tiếp thành 1 match không mang "
            "encoding=\"utf-8\" hợp lệ, nên vi phạm thiếu newline= của lời "
            "gọi thứ hai lọt qua và main() trả 0 (sạch) dù có vi phạm thật"
        )

    def test_main_khong_bao_dong_gia_khi_da_du_newline_o_ca_ba(
        self, tmp_path, monkeypatch,
    ):
        """Đối chứng bắt buộc — đúng nguyên văn `_dung_bo_ba_toi_thieu()`
        HIỆN TẠI (cả 3 lời gọi đã có newline="\\n") không được báo vi phạm."""
        (tmp_path / "tools").mkdir()
        target = tmp_path / "tools" / "gia_lap_da_sua.py"
        target.write_text(
            'def _dung_bo_ba_toi_thieu(thu_muc, study):\n'
            '    (thu_muc / f"G6_A7_ANALYSIS_SCRIPTS_{study}.md").write_text(\n'
            '        "# Script phân tích\\n(placeholder)\\n", '
            'encoding="utf-8", newline="\\n")\n'
            '    (thu_muc / f"G4_A5_SAP_FINAL_{study}.md").write_text(\n'
            '        "# SAP\\n(placeholder)\\n", '
            'encoding="utf-8", newline="\\n")\n'
            '    (thu_muc / "G6_checkpoint.json").write_text(\n'
            '        "{}", encoding="utf-8", newline="\\n")\n',
            encoding="utf-8", newline="\n",
        )
        monkeypatch.setattr(K, "REPO", tmp_path)
        rc = K.main()
        assert rc == 0


class TestCheDocstringBaNhayVanGiuNguyenHanhViCu:
    """★★ Bảo đảm bản vá KHÔNG làm mất tác dụng che docstring/chú thích cũ
    (mục đích "chống bắt lời-kể-về-lỗi" ghi ngay trong docstring module) —
    một docstring ba nháy KỂ LẠI một lời gọi write_text() thiếu newline=
    (dùng làm ví dụ minh hoạ, như chính module kiem_newline_vung_ky.py đang
    làm ở dòng 46-48) không được bị hiểu nhầm là mã nguồn thật."""

    def test_docstring_ba_nhay_ke_lai_loi_goi_thieu_newline_khong_bi_bao(self):
        dong = [
            'def f():',
            '    """Ví dụ lỗi: `dst.write_text(du_lieu, encoding="utf-8")`',  # da-nen: bo-qua: van xuoi mau trong docstring, khong phai ma that
            '    thiếu newline= — CHỈ LÀ VĂN XUÔI MÔ TẢ, không phải mã thật."""',
            '    pass',
        ]
        text = "\n".join(K._mask(dong))
        found = K._tim_loi_goi_write_text(text)
        assert found == [], (
            f"Docstring ba nháy phải được che TOÀN BỘ nội dung — tìm thấy "
            f"{found} nghĩa là nội dung văn xuôi bị hiểu nhầm thành mã thật"
        )

    def test_comment_that_ke_lai_loi_goi_thieu_newline_khong_bi_bao(self):
        """Comment một dòng (bắt đầu bằng '#' NGOÀI chuỗi) kể lại ví dụ lỗi
        cũng phải được che — đây chính là công dụng CHÍNH của _mask()."""
        dong = [
            'def f():',
            '    # Ví dụ lỗi: dst.write_text(du_lieu, encoding="utf-8") thieu newline=',  # da-nen: bo-qua: van xuoi mau trong comment mau, khong phai ma that
            '    pass',
        ]
        text = "\n".join(K._mask(dong))
        found = K._tim_loi_goi_write_text(text)
        assert found == []


class TestMaskGiuNguyenViTriKhiKhongCoGiDeChe:
    """Đối chứng cấu trúc — số dòng của văn bản đã che phải khớp số dòng gốc
    (bất biến bắt buộc: `main()` tính vị trí bằng `text.count("\\n")` trên
    `goc` gốc, lệch số dòng sẽ làm sai luôn việc tra miễn trừ và số dòng báo
    cáo)."""

    def test_so_dong_khong_doi_sau_khi_che(self):
        dong = [
            'import os',
            '',
            'def f():',
            '    """Docstring',
            '    nhiều dòng',
            '    """',
            '    x = "# khong phai comment"  # day moi la comment that',
            '    return x',
        ]
        masked = K._mask(dong)
        assert len(masked) == len(dong)


class TestMaskCheDuocFStringBaNhay:
    """★★ Phát hiện của phản biện độc lập (Workflow đối kháng, không phải
    giả định): từ Python 3.12 (PEP 701), `tokenize` tách f-string thành
    CHUỖI token FSTRING_START/FSTRING_MIDDLE/FSTRING_END thay vì MỘT token
    STRING duy nhất như <3.12. Nếu `_mask()` chỉ gác cửa docstring-masking
    bằng `tok.type == tokenize.STRING`, một f-string BA NHÁY hoàn toàn
    KHÔNG được che trên Python ≥3.12 — trong khi bản `_mask_ngay_tho()` cũ
    VẪN che được (nó quét ký tự `'''`/`\"\"\"` bất kể tiền tố f/r/b/u).
    Đã xác nhận thực nghiệm CHÉO hai phiên bản Python trên máy này
    (3.9.6 — chưa có PEP 701, f-string vẫn 1 token STRING — và 3.14.6 — đã
    có PEP 701): TRƯỚC khi thêm nhánh FSTRING_START/END, kết quả khác nhau
    giữa hai phiên bản cho CÙNG một đầu vào; SAU khi vá, kết quả khớp nhau."""

    def test_write_text_thieu_newline_voi_doi_so_fstring_ba_nhay_van_bi_bat(self):
        dong = [
            'def f(var):',
            '    p.write_text(',
            '        f"""',
            '        TODO: nho them newline= truoc khi merge {var}',
            '        """,',
            '        encoding="utf-8")',
        ]
        text = "\n".join(K._mask(dong))
        found = K._tim_loi_goi_write_text(text)
        assert len(found) == 1
        _start, _end, _full, outer = found[0]
        assert 'encoding="utf-8"' in outer
        assert "newline=" not in outer, (
            "TRƯỚC bản vá FSTRING_START/END: nội dung f-string ba nháy "
            "KHÔNG được che trên Python ≥3.12 (PEP 701 tách f-string thành "
            "FSTRING_START/MIDDLE/END, không còn là 1 token STRING), nên "
            "chữ 'newline=' xuất hiện trong VĂN XUÔI mẫu của f-string bị "
            "hiểu nhầm là kwarg thật của lời gọi write_text() NGOÀI CÙNG, "
            "khiến vi phạm thiếu newline= thật trở nên vô hình"
        )

    def test_fstring_ba_nhay_ke_lai_vi_du_khong_bi_hieu_nham_la_ma_that(self):
        """Đối chứng — một f-string ba nháy CHỈ dùng làm văn xuôi (không
        phải đối số của write_text()) kể lại ví dụ write_text() thiếu
        newline= cũng phải được che, giữ đúng tinh thần chống-bắt-lời-kể-
        về-lỗi vốn có từ bản docstring ba nháy thường."""
        dong = [
            'def f(x):',
            '    f"""Vi du: dst.write_text(du_lieu, encoding="utf-8") {x}',  # da-nen: bo-qua: van xuoi mau trong f-string, khong phai ma that
            '    thieu newline= chi la van xuoi khong phai ma that."""',
        ]
        text = "\n".join(K._mask(dong))
        found = K._tim_loi_goi_write_text(text)
        assert found == []


class TestMaskDuPhongKhiTokenizeThatBai:
    """Bảo đảm nhánh dự phòng (`_mask_ngay_tho`) khi `tokenize` không đọc
    được văn bản (vd file có chuỗi ba nháy chưa đóng) không làm CHẾT toàn bộ
    checker — chỉ hạ về hành vi cũ (kém chính xác hơn) cho đúng file đó."""

    def test_khong_crash_khi_van_ban_khong_hop_le_cu_phap(self, capsys):
        dong = [
            'def f():',
            '    x = """chuoi ba nhay khong bao gio dong',
        ]
        masked = K._mask(dong)
        assert isinstance(masked, list)
        assert len(masked) == len(dong)
        loi_ra = capsys.readouterr().err
        assert "tokenize" in loi_ra.lower()
