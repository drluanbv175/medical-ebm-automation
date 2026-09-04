"""Hồi quy phát hiện #3 của Workflow đối kháng đa-agent vòng 3 (2026-09-04, CRITICAL) trong
tools/import_real_dataset.py::VALUE_PATTERNS — dùng chung bởi deidentify_research_dataset.py
VÀ pseudonymize_research_dataset.py.

HIPAA Safe Harbor liệt "mọi thành phần ngày tháng gắn với một cá nhân — trừ năm — gồm ngày
sinh, ngày nhập viện, ngày xuất viện" là ĐỊNH DANH TRỰC TIẾP, nhưng VALUE_PATTERNS trước đây
KHÔNG có mục nào cho ngày tháng. Một ô ghi chú tự do (header không gợi ý PII, vd cột "notes")
chứa "BN sinh ngày 15/07/1980, nhập viện 03/03/2024" lọt qua CẢ _scan_csv() (cổng tiếp nhận)
LẪN _redact_value() (công cụ khử định danh), khiến báo cáo khử định danh khẳng định SAI
`output_pii_scan.passed: true` trong khi ngày sinh vẫn còn nguyên trong file xuất ra.

Nguyên tắc viết test: gọi THẲNG _scan_csv()/deidentify_dataset()/_redact_value() với dữ liệu
dựng tay đúng kịch bản trong finding — không grep chuỗi trong mã nguồn.
"""
from __future__ import annotations

import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import deidentify_research_dataset as DEID  # noqa: E402
import import_real_dataset as RDI  # noqa: E402
import pseudonymize_research_dataset as PSN  # noqa: E402


def _csv(path: Path, text: str) -> Path:
    path.write_text(text.strip() + "\n", encoding="utf-8", newline="\n")
    return path


class TestValuePatternsCoDauDate:
    def test_gia_tri_pattern_co_khoa_date(self):
        assert "date" in RDI.VALUE_PATTERNS


class TestScanCsvBatDuocNgayTrongOTuDo:
    """★★ Ca chính, đúng nguyên văn kịch bản trong finding: cột 'notes' (header
    KHÔNG gợi ý PII) chứa ngày sinh/ngày nhập viện dạng dd/mm/yyyy."""

    def test_ngay_trong_cot_notes_bi_chan(self, tmp_path):
        raw = _csv(
            tmp_path / "raw.csv",
            """
record_id,age,notes,primary_outcome
001,45,BN sinh ngay 15/07/1980 nhap vien 03/03/2024 tai xa Binh An,0
002,52,ghi chu binh thuong khong co gi dac biet,1
""",
        )
        result = RDI._scan_csv(raw)
        loai = {i["type"] for i in result["issues"]}
        assert "value_pii:date" in loai
        # Đúng CỘT/DÒNG bị gắn cờ, không phải toàn file.
        date_issues = [i for i in result["issues"] if i["type"] == "value_pii:date"]
        assert all(i["column"] == "notes" for i in date_issues)
        assert any(i["row"] == 1 for i in date_issues)

    def test_ngay_dinh_dang_iso_cung_bi_bat(self, tmp_path):
        raw = _csv(
            tmp_path / "raw_iso.csv",
            """
record_id,age,notes
001,45,admission date 2024-03-03 discharge later
""",
        )
        result = RDI._scan_csv(raw)
        loai = {i["type"] for i in result["issues"]}
        assert "value_pii:date" in loai

    def test_so_lam_sang_khong_bi_bao_nham_la_ngay(self, tmp_path):
        """Đối chứng: huyết áp/liều lượng dạng phân số KHÔNG có nhóm năm 19xx/20xx
        không được gắn cờ là ngày tháng."""
        raw = _csv(
            tmp_path / "raw_clinical.csv",
            """
record_id,age,notes
001,45,huyet ap 140/90 nhip tim 88 lieu 5/10 mg
""",
        )
        result = RDI._scan_csv(raw)
        loai = {i["type"] for i in result["issues"]}
        assert "value_pii:date" not in loai


class TestRedactValueXoaSachNgay:
    """_redact_value() của deidentify_research_dataset.py VÀ pseudonymize_research_dataset.py
    CÙNG dùng RDI.VALUE_PATTERNS — kiểm cả hai để không lệch nhau (BH20: nhiều nơi tiêu
    thụ cùng một nguồn phải đồng bộ)."""

    def test_deidentify_redact_value_xoa_ngay(self):
        text = "BN sinh ngay 15/07/1980, nhap vien 03/03/2024 tai xa Binh An"
        redacted, counts = DEID._redact_value(text)
        assert "1980" not in redacted
        assert "2024" not in redacted
        assert "15/07" not in redacted
        assert counts.get("date") == 2

    def test_pseudonymize_redact_value_xoa_ngay(self):
        text = "BN sinh ngay 15/07/1980, nhap vien 03/03/2024 tai xa Binh An"
        redacted, redactions = PSN._redact_value(text)
        assert "1980" not in redacted
        assert "2024" not in redacted
        labels = {r["pattern_label"] for r in redactions}
        assert "date" in labels

    def test_khong_dong_chuoi_lam_sang_khong_co_nam(self):
        """Đối chứng: câu văn lâm sàng có phân số nhưng KHÔNG có nhóm năm không bị đụng tới."""
        clinical = "Huyết áp 140/90, nhịp tim 88, đường huyết 7.2"
        redacted, counts = DEID._redact_value(clinical)
        assert redacted == clinical
        assert counts == {}


class TestDeidentifyDatasetEndToEnd:
    """★★ Tái hiện ĐÚNG kịch bản đầu-cuối trong finding: chạy deidentify_dataset() thật,
    xác nhận file đầu ra KHÔNG còn ngày sinh và output_pii_scan.passed phản ánh đúng —
    quét lại sau khi redact phải sạch (vì ngày đã bị thay bằng REDACTION_TOKEN)."""

    def test_ngay_sinh_bi_xoa_khoi_file_dau_ra(self, tmp_path):
        raw = _csv(
            tmp_path / "raw.csv",
            """
record_id,age,notes,primary_outcome
001,45,BN sinh ngay 15/07/1980 nhap vien 03/03/2024 tai xa Binh An,0
002,52,ghi chu binh thuong,1
""",
        )
        report = DEID.deidentify_dataset("DEID-DATE-PII", raw, exports_root=tmp_path / "exports")
        assert report["status"] == DEID.DEIDENTIFIED_STATUS
        out_dir = tmp_path / "exports" / "DEID-DATE-PII"
        deid_path = out_dir / report["deidentified_path"]
        text = deid_path.read_text(encoding="utf-8")
        assert "15/07/1980" not in text
        assert "03/03/2024" not in text
        assert "1980" not in text
        assert "2024" not in text
        assert DEID.REDACTION_TOKEN in text
        # Cổng tiếp nhận chạy lại trên bản ĐÃ khử định danh: phải sạch thật, không
        # phải "sạch" do chưa từng quét ngày tháng.
        rescan = RDI._scan_csv(deid_path)
        assert not any(i["type"] == "value_pii:date" for i in rescan["issues"])


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
