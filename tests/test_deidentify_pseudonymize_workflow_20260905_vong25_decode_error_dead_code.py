"""Hồi quy phát hiện #3 (Trung bình) của Workflow đối kháng đa-agent 2026-09-05
(vòng 25) trong tools/deidentify_research_dataset.py VÀ tools/pseudonymize_research_dataset.py
— nhánh "decode_error" là CODE CHẾT ở cả hai file, không thể kích hoạt trong
bất kỳ hoàn cảnh nào.

CƠ CHẾ LỖI (giống hệt nhau ở cả 2 file):
    for encoding in ("utf-8-sig", "latin-1"):
        try:
            process = _process_with_encoding(data_path, output_path, encoding)
            ...
            break
        except UnicodeDecodeError as exc:
            last_decode_error = exc
            ...
            continue
    if last_decode_error is not None:
        blocker = "decode_error: hãy xuất lại CSV UTF-8"

"latin-1" (ISO-8859-1) ánh xạ MỌI byte 0x00-0xFF sang một ký tự Unicode hợp
lệ — về mặt kỹ thuật KHÔNG BAO GIỜ ném UnicodeDecodeError. Vì đây luôn là
lượt thử CUỐI trong vòng lặp, nếu chạy tới thì luôn `break` thành công và
gán lại last_decode_error = None. Hệ quả: điều kiện
`if last_decode_error is not None` KHÔNG BAO GIỜ đúng — nhánh
`blocker = "decode_error..."` là code chết.

Hại thật: một CSV lưu bằng Windows-1252 (rất phổ biến với dữ liệu tiếng
Việt xuất từ Excel/REDCap cũ trên Windows — đúng bối cảnh người dùng của hệ
thống này, xem ghi chú "USE_MOCK_SOURCES trên Windows" trong CLAUDE.md) khiến
utf-8-sig decode ném lỗi, nhưng latin-1 decode LUÔN thành công — với văn bản
đã bị mojibake (byte 0x80 của cp1252 là dấu Euro, không tồn tại trong bảng
Latin-1 nên bị hiểu sai) mà KHÔNG có bất kỳ cảnh báo nào. Công cụ vẫn báo
DEIDENTIFIED_READY_FOR_INTAKE / PSEUDONYMIZED_READY_FOR_INTAKE trên dữ liệu
đã hỏng ngầm — người dùng không biết, và cơ chế bảo vệ mà chính code tự hứa
("hãy xuất lại CSV UTF-8") không bao giờ được kích hoạt.

BẢN VÁ: bỏ "latin-1" khỏi vòng thử ở CẢ HAI file — chỉ còn ("utf-8-sig",).
Một CSV không phải UTF-8 hợp lệ giờ bị CHẶN (đúng lời hứa của blocker) thay
vì bị âm thầm đọc sai — khớp triết lý fail-closed của toàn bộ 2 file PII.

Nguyên tắc viết test: gọi THẲNG deidentify_dataset()/pseudonymize_dataset()
thật với một file CSV byte thật (cp1252, byte 0x80) — không mock nội bộ."""
from __future__ import annotations

import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import deidentify_research_dataset as DEID  # noqa: E402
import pseudonymize_research_dataset as PRD  # noqa: E402

# byte 0x80 KHÔNG hợp lệ trong UTF-8 (không phải continuation byte của chuỗi nào)
# nhưng luôn giải mã được bằng latin-1 (thành U+0080, ký tự điều khiển C1) —
# đúng cơ chế khiến vòng thử cũ luôn "thành công" ở lượt latin-1.
_CP1252_BYTES = b"ten,ket_qua\r\nTest\x80case,am tinh\r\n"


class TestDeidentifyKhongConDocNgamSaiFileKhongPhaiUtf8:
    """★★★ Ca chính — tools/deidentify_research_dataset.py phải CHẶN, không
    được âm thầm đọc sai bằng latin-1."""

    def test_csv_cp1252_bi_chan_dung_thong_diep_da_hua(self, tmp_path):
        data = tmp_path / "raw.csv"
        data.write_bytes(_CP1252_BYTES)
        exports_root = tmp_path / "exports"

        report = DEID.deidentify_dataset("STUDY-VONG25-CP1252", data, exports_root=exports_root)

        assert report["status"] == DEID.BLOCKED_STATUS, (
            "TRƯỚC bản vá: 'latin-1' không bao giờ ném UnicodeDecodeError nên "
            "công cụ đọc thành công (sai) rồi báo DEIDENTIFIED_READY_FOR_INTAKE "
            "trên dữ liệu đã mojibake, thay vì chặn"
        )
        assert report.get("blocker") == "decode_error: hãy xuất lại CSV UTF-8"

    def test_csv_utf8_hop_le_van_hoat_dong_dung_nhu_cu(self, tmp_path):
        """Đối chứng bắt buộc — CSV UTF-8 hợp lệ (kể cả có BOM) vẫn xử lý
        thành công như trước bản vá."""
        data = tmp_path / "raw.csv"
        data.write_text("ten,ket_qua\nNguyễn Văn A,âm tính\n", encoding="utf-8-sig", newline="\r\n")
        exports_root = tmp_path / "exports"

        report = DEID.deidentify_dataset("STUDY-VONG25-UTF8", data, exports_root=exports_root)

        assert report["status"] == DEID.DEIDENTIFIED_STATUS
        assert report.get("blocker") is None


class TestPseudonymizeKhongConDocNgamSaiFileKhongPhaiUtf8:
    """★★★ Ca chính, phía pseudonymize — cùng cơ chế lỗi, cùng bản vá."""

    def test_csv_cp1252_bi_chan_dung_thong_diep_da_hua(self, tmp_path):
        data = tmp_path / "raw.csv"
        data.write_bytes(_CP1252_BYTES)
        exports_root = tmp_path / "exports"
        mapping_root = tmp_path / "mapping_safe_dir"

        report = PRD.pseudonymize_dataset(
            "STUDY-VONG25-CP1252", data, exports_root=exports_root,
            mapping_root=mapping_root, retention_months=12, retention_owner="PI-01",
        )

        assert report["status"] == PRD.BLOCKED_STATUS, (
            "TRƯỚC bản vá: 'latin-1' không bao giờ ném UnicodeDecodeError nên "
            "công cụ đọc thành công (sai) rồi báo PSEUDONYMIZED_READY_FOR_INTAKE "
            "trên dữ liệu đã mojibake, thay vì chặn"
        )
        assert report.get("blocker") == "decode_error: hãy xuất lại CSV UTF-8"

    def test_csv_utf8_hop_le_van_hoat_dong_dung_nhu_cu(self, tmp_path):
        """Đối chứng bắt buộc — CSV UTF-8 hợp lệ vẫn xử lý thành công như
        trước bản vá."""
        data = tmp_path / "raw.csv"
        data.write_text("ten,ket_qua\nNguyễn Văn A,âm tính\n", encoding="utf-8-sig", newline="\r\n")
        exports_root = tmp_path / "exports"
        mapping_root = tmp_path / "mapping_safe_dir"

        report = PRD.pseudonymize_dataset(
            "STUDY-VONG25-UTF8", data, exports_root=exports_root,
            mapping_root=mapping_root, retention_months=12, retention_owner="PI-01",
        )

        assert report["status"] == PRD.PSEUDONYMIZED_STATUS
        assert report.get("blocker") is None
