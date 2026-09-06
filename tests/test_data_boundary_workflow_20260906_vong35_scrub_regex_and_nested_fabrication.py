r"""Hồi quy 2 phát hiện của audit vòng 35 (2026-09-06) trong
runtime/data_boundary.py — cùng một file, cùng vòng audit.

── Phát hiện #1 (CRITICAL) — scrub_pii() double-escape backslash ──────────
CƠ CHẾ LỖI (TRƯỚC bản vá):
    scrubbed = re.sub(
        rf'("{re.escape(sentinel)}"\\s*:\\s*")[^"]*(")',
        ...
    )
Đây là raw f-string (rf'...'). Raw string KHÔNG diễn giải escape, nên HAI
backslash trong SOURCE ("\\s") giữ nguyên HAI backslash lúc runtime — tạo
ra pattern khớp "một ký tự backslash literal, rồi chữ s" thay vì lớp
khoảng trắng \\s (MỘT backslash). Văn bản JSON thật không chứa backslash ở
vị trí đó ⇒ regex KHÔNG BAO GIỜ khớp ⇒ scrub_pii() fail-open câm lặng cho
mọi sentinel key (patient_id, cccd, cmnd, bhyt, ho_ten_benh_nhan...) ngay
trước khi runtime/audit_logger.py ghi vào sổ audit append-only.
Vá: bỏ một lớp backslash (rf'...\\s...' → rf'...\s...').

── Phát hiện #3 (HIGH) — check_fabricated_data/citation chỉ tra cấp 1 ─────
CƠ CHẾ LỖI (TRƯỚC bản vá):
    if "p_value" in output and not output.get("source_pmid"): ...
    if output.get("doi_verified") is False: ...
Tra trực tiếp trên dict gốc — chỉ thấy key CẤP 1. Một output THẬT có cấu
trúc lồng tự nhiên (`{"result": {"p_value": 0.03}}`,
`{"citation": {"doi_verified": False}}`) lọt qua hoàn toàn — cùng họ lỗi
đã vá ở check_pii_in_output() trong CHÍNH file này nhưng chưa áp dụng lại.
Vá: thêm _iter_dicts() duyệt đệ quy mọi dict con, áp cùng điều kiện logic
ở MỌI cấp.

LƯU Ý PHẠM VI (đã xác minh bằng grep, không suy diễn): DataBoundary chỉ
được import bởi research_studio/ và research_automation/ — CLAUDE.md ghi
nhận cụm này là nhánh MỒ CÔI ("NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW
USE"), không phải cổng G0–G10 thật. Cả hai bug vẫn THẬT (tái hiện được
bằng chạy thật, đúng bất biến bị vi phạm) nên vẫn sửa — chỉ không phóng
đại mức ảnh hưởng lên luồng chính."""
from __future__ import annotations

from runtime.data_boundary import DataBoundary


class TestCaChinhScrubPiiRegexDoubleEscape:
    """★★★ Ca chính phát hiện #1 — scrub_pii() phải redact được giá trị
    gắn với sentinel key, không được là no-op câm lặng."""

    def test_patient_id_duoc_redact(self):
        db = DataBoundary()
        out = db.scrub_pii('{"patient_id": "BN0012345", "other": "data"}')
        assert out == '{"patient_id": "[REDACTED]", "other": "data"}', (
            "TRƯỚC bản vá: pattern regex có HAI backslash literal thay vì "
            "lớp khoảng trắng \\s (do raw f-string không diễn giải escape) "
            f"nên không bao giờ khớp — kết quả thực tế: {out!r}"
        )

    def test_cccd_duoc_redact(self):
        # Giá trị "REDACT_ME_PLACEHOLDER" (không phải chuỗi toàn số/khuôn
        # chữ+số của CCCD/BHYT thật) — cô lập ĐÚNG cơ chế sentinel-key
        # regex đang kiểm. Mutation-test phát hiện: một giá trị CCCD 12
        # chữ số thật (vd "012345678901") vô tình khớp SẴN _PII_PATTERNS
        # khác (\b\d{12}\b) và bị pattern đó redact độc lập, khiến test
        # PASS ngay cả khi cơ chế sentinel-key đang kiểm hoàn toàn hỏng.
        db = DataBoundary()
        out = db.scrub_pii('{"cccd": "REDACT_ME_PLACEHOLDER", "note": "test"}')
        assert out == '{"cccd": "[REDACTED]", "note": "test"}'

    def test_ho_ten_benh_nhan_duoc_redact(self):
        db = DataBoundary()
        out = db.scrub_pii('{"ho_ten_benh_nhan": "Nguyen Van A"}')
        assert out == '{"ho_ten_benh_nhan": "[REDACTED]"}'

    def test_bhyt_co_khoang_trang_quanh_dau_hai_cham_duoc_redact(self):
        # Cùng lý do ở trên: tránh giá trị khớp khuôn BHYT thật
        # ([A-Z]{2}\d{10}) — dùng placeholder không phải chữ+số để cô lập
        # đúng cơ chế sentinel-key.
        db = DataBoundary()
        out = db.scrub_pii('{ "bhyt" : "REDACT_ME_PLACEHOLDER" }')
        assert "[REDACTED]" in out
        assert "REDACT_ME_PLACEHOLDER" not in out


class TestCaChinhFabricatedDataCitationLongNested:
    """★★★ Ca chính phát hiện #3 — check_fabricated_data()/
    check_fabricated_citation() phải bắt được p_value/doi_verified LỒNG
    trong dict con, không chỉ ở cấp 1."""

    def test_p_value_long_trong_result_bi_bat(self):
        db = DataBoundary()
        flag, reason = db.check_fabricated_data({"result": {"p_value": 0.03}})
        assert flag is True, (
            "TRƯỚC bản vá: 'p_value' in output chỉ tra cấp 1 của dict, "
            f"bỏ lọt p_value lồng trong 'result'. Kết quả thực tế: "
            f"({flag}, {reason!r})"
        )
        assert reason == "NO_SOURCE_WITH_STATISTICAL_RESULT"

    def test_p_value_long_sau_nhieu_cap_bi_bat(self):
        db = DataBoundary()
        flag, _ = db.check_fabricated_data({"a": {"b": {"p_value": 0.03}}})
        assert flag is True

    def test_p_value_trong_list_bi_bat(self):
        db = DataBoundary()
        flag, _ = db.check_fabricated_data({"items": [{"p_value": 0.03}]})
        assert flag is True

    def test_doi_verified_long_trong_citation_bi_bat(self):
        db = DataBoundary()
        flag, reason = db.check_fabricated_citation(
            {"citation": {"doi_verified": False}},
        )
        assert flag is True, (
            "TRƯỚC bản vá: output.get('doi_verified') chỉ tra cấp 1, bỏ "
            f"lọt doi_verified lồng trong 'citation'. Kết quả thực tế: "
            f"({flag}, {reason!r})"
        )
        assert reason == "CITATION_DOI_NOT_VERIFIED"


class TestDoiChung:
    """Đối chứng — ca cấp 1 (đã đúng từ trước) và ca sạch không bị ảnh
    hưởng bởi cả hai bản vá."""

    def test_p_value_co_source_pmid_van_sach(self):
        db = DataBoundary()
        flag, reason = db.check_fabricated_data(
            {"p_value": 0.03, "source_pmid": "12345678"},
        )
        assert (flag, reason) == (False, "CLEAN")

    def test_p_value_cap_1_van_bi_bat_nhu_cu(self):
        db = DataBoundary()
        flag, _ = db.check_fabricated_data({"p_value": 0.03})
        assert flag is True

    def test_doi_verified_true_van_sach(self):
        db = DataBoundary()
        flag, reason = db.check_fabricated_citation({"doi_verified": True})
        assert (flag, reason) == (False, "CLEAN")

    def test_output_khong_lien_quan_van_sach(self):
        db = DataBoundary()
        assert db.check_fabricated_data({"other": "data"}) == (False, "CLEAN")
        assert db.check_fabricated_citation({"other": "data"}) == (False, "CLEAN")

    def test_sentinel_marker_van_bi_bat_dung_nhu_cu(self):
        db = DataBoundary()
        flag, reason = db.check_fabricated_data(
            {"note": "FABRICATED_DATA_MARKER present"},
        )
        assert flag is True
        assert reason == "FABRICATED_DATA_SENTINEL"

    def test_check_pii_in_output_khong_bi_anh_huong(self):
        # check_pii_in_output() không đụng tới trong cả hai bản vá — xác
        # nhận không hồi quy.
        db = DataBoundary()
        flag, _ = db.check_pii_in_output({"patient_id": "BN00123"})
        assert flag is True
