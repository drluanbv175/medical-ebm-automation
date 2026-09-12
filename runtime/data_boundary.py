"""
DataBoundary — Kiểm tra PII, raw data write, auto-submit, production connector.
Không có API call, không lưu PII.
"""

from __future__ import annotations

import re
import unicodedata

# ─── PII patterns (Vietnamese context) ────────────────────────────────────────

_PII_PATTERNS = [
    # CCCD 12 số, CMND 9 số
    re.compile(r'\b\d{12}\b'),
    re.compile(r'\b\d{9}\b'),
    # Số điện thoại VN: 09x, 08x, 07x, 03x, 05x, 06x
    re.compile(r'\b(0[3-9]\d{8})\b'),
    # BHYT: 10 ký tự bắt đầu bằng chữ + số
    re.compile(r'\b[A-Z]{2}\d{13}\b'),
    re.compile(r'\b[A-Z]{2}\d{10}\b'),
    # Họ tên VN (heuristic: 2-4 từ, từ đầu viết hoa)
    re.compile(r'\b(Nguyễn|Trần|Lê|Phạm|Hoàng|Huỳnh|Phan|Vũ|Võ|Đặng|Bùi|Đỗ|Hồ|Ngô|Dương|Lý)\s+[A-ZĐÀÁẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬ][a-zđàáảãạăắằẳẵặâấầẩẫậ]+(\s+[A-ZĐÀÁẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬ][a-zđàáảãạăắằẳẵặâấầẩẫậ]+)?'),
    # Email
    re.compile(r'\b[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}\b'),
    # Ngày sinh format dd/mm/yyyy
    re.compile(r'\b(0[1-9]|[12]\d|3[01])/(0[1-9]|1[0-2])/\d{4}\b'),
]

# Sentinels rõ ràng trong fixture. "patient id"/"mã bệnh nhân"/"ma benh nhan" thêm
# 2026-07-11: research_preflight.py's defense-in-depth scan (dùng check_pii_in_output
# này) từng hẹp hơn project_intake.py's _PATIENT_ID_MARKERS — giờ hợp nhất về đây
# (nguồn PII scan DUY NHẤT) để mọi caller cùng bắt được, không chỉ project_intake.
_PII_SENTINELS = ["cccd", "cmnd", "bhyt", "patient_id", "patient id", "BN00", "PII_MARKER",
                   "ho_ten_benh_nhan", "pii_leak_marker", "mã bệnh nhân", "ma benh nhan"]

# Sentinels trong output dict keys/values
_PRODUCTION_CONNECTOR_MARKERS = [
    "HIS_CONNECT", "EMR_CONNECT", "LIS_CONNECT", "PACS_CONNECT",
    "EHOSPITAL_CONNECT", "PRODUCTION_MODE", "REAL_PATIENT_DATA",
    "LIVE_DATABASE",
]

_AUTO_SUBMIT_MARKERS = [
    "AUTO_SUBMIT_ATTEMPT", "auto_submit_to_journal", "JOURNAL_SUBMISSION",
    "auto_release", "auto_approve", "auto_submit",
]

_RAW_DATA_WRITE_MARKERS = [
    "RAW_DATA_WRITE_ATTEMPT", "write_raw_patient_data",
    "RAW_DATA_WRITE", "raw_write", "database/patients",
]


class DataBoundary:
    """
    Kiểm tra đầu ra agent trước khi cho phép egress.
    Không log PII, không lưu dữ liệu thật.
    """

    def check_pii_in_output(self, output: dict | str) -> tuple[bool, str]:
        """
        Trả (found: bool, reason: str).
        Chuyển dict → str để scan pattern.
        """
        # Chuẩn hóa NFC: _PII_PATTERNS "Họ tên VN" liệt kê chữ cái có dấu ở dạng tổ hợp sẵn
        # (NFC) — văn bản NFD (chữ nền + dấu rời) khớp trượt hoàn toàn nếu không chuẩn hóa.
        text = unicodedata.normalize("NFC", self._to_scannable(output))

        # Kiểm tra sentinel markers trước (fixtures)
        for sentinel in _PII_SENTINELS:
            if sentinel.lower() in text.lower():
                return True, f"PII_SENTINEL_DETECTED:{sentinel}"

        # Kiểm tra regex patterns
        for pattern in _PII_PATTERNS:
            if pattern.search(text):
                return True, f"PII_PATTERN_MATCH:{pattern.pattern[:40]}"

        return False, "CLEAN"

    def scrub_pii(self, text: str) -> str:
        """Thay thế PII bằng [REDACTED] trước khi log."""
        scrubbed = unicodedata.normalize("NFC", text)
        for pattern in _PII_PATTERNS:
            scrubbed = pattern.sub("[REDACTED]", scrubbed)
        for sentinel in _PII_SENTINELS:
            # Thay value sau sentinel key trong JSON-like text.
            # Vá 2026-09-06 (audit vòng 35, phát hiện #1 — CRITICAL, fail-open):
            # bản cũ viết "\\s" (HAI backslash) bên trong raw f-string
            # (rf'...') — raw string KHÔNG diễn giải escape nên hai backslash
            # trong SOURCE giữ nguyên hai backslash lúc runtime, tạo ra pattern
            # regex khớp "một ký tự backslash literal, rồi chữ s" (\\s theo
            # nghĩa \-literal + s) thay vì lớp khoảng trắng \s (một backslash).
            # Vì văn bản JSON thật không chứa backslash ở vị trí ":", regex
            # KHÔNG BAO GIỜ khớp — toàn bộ vòng lặp thay giá trị theo sentinel
            # key (patient_id, cccd, cmnd, bhyt, ho_ten_benh_nhan...) là no-op
            # câm lặng, khiến scrub_pii() fail-open đúng loại dữ liệu nó được
            # thiết kế riêng để chặn, ngay trước khi audit_logger.py ghi vào
            # sổ audit append-only. Chỉ cần MỘT backslash "\s" trong raw
            # string (rf'...\s...') để có đúng lớp khoảng trắng.
            scrubbed = re.sub(
                rf'("{re.escape(sentinel)}"\s*:\s*")[^"]*(")',
                r'\1[REDACTED]\2',
                scrubbed,
                flags=re.IGNORECASE,
            )
        return scrubbed

    def check_auto_submit(self, output: dict) -> tuple[bool, str]:
        """Block nếu output chứa auto-submit marker."""
        text = self._to_scannable(output)
        for marker in _AUTO_SUBMIT_MARKERS:
            if marker.lower() in text.lower():
                return True, f"AUTO_SUBMIT_MARKER:{marker}"
        return False, "CLEAN"

    def check_raw_data_write(self, output: dict) -> tuple[bool, str]:
        """Block nếu output cố write raw data."""
        text = self._to_scannable(output)
        for marker in _RAW_DATA_WRITE_MARKERS:
            if marker.lower() in text.lower():
                return True, f"RAW_DATA_WRITE_MARKER:{marker}"
        return False, "CLEAN"

    def check_production_connector(self, output: dict) -> tuple[bool, str]:
        """Block nếu output chứa production connector marker."""
        text = self._to_scannable(output)
        for marker in _PRODUCTION_CONNECTOR_MARKERS:
            if marker.lower() in text.lower():
                return True, f"PRODUCTION_CONNECTOR_MARKER:{marker}"
        return False, "CLEAN"

    def check_fabricated_data(self, output: dict) -> tuple[bool, str]:
        """Block nếu output có FABRICATED_DATA_MARKER hoặc thiếu nguồn."""
        text = self._to_scannable(output)
        if "FABRICATED_DATA_MARKER" in text:
            return True, "FABRICATED_DATA_SENTINEL"
        # Thiếu source khi có p_value/result — quét MỌI dict con (đệ quy),
        # không chỉ cấp 1. Xem chú thích ở _iter_dicts().
        for d in self._iter_dicts(output):
            if "p_value" in d and not d.get("source_pmid"):
                return True, "NO_SOURCE_WITH_STATISTICAL_RESULT"
        return False, "CLEAN"

    def check_fabricated_citation(self, output: dict) -> tuple[bool, str]:
        """Review-required nếu citation chưa verified."""
        if "FABRICATED_CITATION_MARKER" in self._to_scannable(output):
            return True, "FABRICATED_CITATION_SENTINEL"
        # Quét MỌI dict con (đệ quy) — xem chú thích ở _iter_dicts().
        for d in self._iter_dicts(output):
            if d.get("doi_verified") is False:
                return True, "CITATION_DOI_NOT_VERIFIED"
        return False, "CLEAN"

    # ── helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _iter_dicts(obj):
        """Duyệt ĐỆ QUY mọi dict con (kể cả `obj` chính nó nếu là dict) bên
        trong một cấu trúc dict/list lồng nhau tuỳ ý.

        Vá 2026-09-06 (audit vòng 35, phát hiện #3 — HIGH): check_fabricated_
        data()/check_fabricated_citation() trước đây tra trực tiếp
        `"p_value" in output`/`output.get("doi_verified")` — chỉ thấy key ở
        CẤP 1 của dict. Một output THẬT có cấu trúc lồng tự nhiên (vd
        `{"result": {"p_value": 0.03}}`, `{"citation": {"doi_verified":
        False}}`) sẽ lọt qua hoàn toàn — cùng họ lỗi đã vá ở
        check_pii_in_output() trong CHÍNH file này (bản cũ "chỉ soát string
        CẤP CAO NHẤT... bỏ lọt PII thật lồng trong dict/list", xem
        runtime/controlled_orchestrator.py) nhưng chưa được áp dụng lại cho
        hai hàm chống dữ liệu/trích dẫn giả này."""
        if isinstance(obj, dict):
            yield obj
            for value in obj.values():
                yield from DataBoundary._iter_dicts(value)
        elif isinstance(obj, list):
            for item in obj:
                yield from DataBoundary._iter_dicts(item)

    @staticmethod
    def _to_scannable(output: dict | str) -> str:
        if isinstance(output, str):
            return output
        import json
        try:
            return json.dumps(output, ensure_ascii=False)
        except Exception:
            return str(output)
