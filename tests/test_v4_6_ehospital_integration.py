"""
T34–T40 — V4.6 eHospital Mini Integration Tests (V4.2.1 hardened).
Kiểm tra eHospitalConnector: de-identification, read-only, graceful degradation,
và HARDENING V4.2.1 (DISABLED-by-default, no auto-discover, từ chối DB thật).

Tất cả tests đều offline, hermetic — KHÔNG dùng DB thật. Các test có dữ liệu đều
tự tạo SQLite tạm (synthetic) và bật cờ MRAQ_ENABLE_EHOSPITAL_SYNTHETIC_TEST=1
trong setup; KHÔNG có test nào phụ thuộc ~/.ehospital thật (không còn skipif).
"""
import os
import sys
import tempfile
import sqlite3
from pathlib import Path

import pytest

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))

from runtime.ehospital_connector import (
    eHospitalConnector,
    _find_db,
    _PII_FIELDS,
    _EHOSPITAL_DIR,
    _ENABLE_FLAG,
)


# ─── Helper: tạo DB test tạm thời ────────────────────────────────────────────

def _make_test_db(path: Path) -> None:
    """Tạo SQLite DB nhỏ với schema tương tự eHospital Mini."""
    conn = sqlite3.connect(str(path))
    conn.executescript("""
        CREATE TABLE appointments (
            id INTEGER PRIMARY KEY,
            name TEXT,
            ho_ten TEXT,
            cccd TEXT,
            phone TEXT,
            diagnosis_code TEXT,
            complaint TEXT,
            created_at TEXT
        );
        INSERT INTO appointments VALUES
            (1, 'Nguyen Van A', 'Nguyễn Văn A', '012345678901', '0901234567', 'E11', 'Đau đầu', '2026-06-01'),
            (2, 'Tran Thi B', 'Trần Thị B', '098765432109', '0987654321', 'I10', 'Đau ngực', '2026-06-02'),
            (3, NULL, NULL, NULL, NULL, 'E11', 'Mệt mỏi', '2026-06-03');

        CREATE TABLE prescriptions (
            id INTEGER PRIMARY KEY,
            appointment_id INTEGER,
            medication_name TEXT
        );
        INSERT INTO prescriptions VALUES
            (1, 1, 'Metformin 500mg'),
            (2, 1, 'Metformin 500mg'),
            (3, 2, 'Amlodipine 5mg');
    """)
    conn.close()


# ─── T34: Graceful degradation khi DB không có ───────────────────────────────

class TestT34GracefulDegradation:
    def test_is_available_false_when_no_db(self):
        conn = eHospitalConnector(db_path=Path("/nonexistent/path.db"))
        assert conn.is_available is False

    def test_encounter_summary_empty_when_unavailable(self):
        conn = eHospitalConnector(db_path=Path("/nonexistent/path.db"))
        assert conn.get_encounter_summary() == []

    def test_diagnosis_distribution_empty_when_unavailable(self):
        conn = eHospitalConnector(db_path=Path("/nonexistent/path.db"))
        assert conn.get_diagnosis_distribution() == {}

    def test_medication_frequency_empty_when_unavailable(self):
        conn = eHospitalConnector(db_path=Path("/nonexistent/path.db"))
        assert conn.get_medication_frequency() == {}

    def test_db_schema_empty_when_unavailable(self):
        conn = eHospitalConnector(db_path=Path("/nonexistent/path.db"))
        assert conn.get_db_schema() == {}

    def test_default_disabled_no_autodiscover(self, tmp_path):
        """V4.2.1: mặc định (không flag) connector DISABLED, KHÔNG auto-discover."""
        # Bảo đảm flag không bật trong test này
        os.environ.pop(_ENABLE_FLAG, None)
        result = eHospitalConnector(db_path=None)
        assert result.is_available is False
        assert result.db_path is None
        assert result.disabled_reason == "DISABLED_BY_DEFAULT_NO_SYNTHETIC_FLAG"


# ─── T35: De-identification ───────────────────────────────────────────────────

class TestT35Deidentification:
    def setup_method(self):
        # V4.2.1: bật flag synthetic + dùng DB tạm (KHÔNG phải DB thật).
        os.environ[_ENABLE_FLAG] = "1"
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = Path(self.tmp.name)
        _make_test_db(self.db_path)
        self.conn = eHospitalConnector(db_path=self.db_path)

    def teardown_method(self):
        os.environ.pop(_ENABLE_FLAG, None)
        self.tmp.close()
        self.db_path.unlink(missing_ok=True)

    def test_is_available_with_test_db(self):
        assert self.conn.is_available is True

    def test_name_field_is_pseudonym(self):
        rows = self.conn.get_encounter_summary(limit=5)
        for row in rows:
            if row.get("name") is not None:
                assert row["name"].startswith("PT-"), f"name không được pseudonym: {row['name']}"

    def test_ho_ten_field_is_pseudonym(self):
        rows = self.conn.get_encounter_summary(limit=5)
        for row in rows:
            if row.get("ho_ten") is not None:
                assert row["ho_ten"].startswith("PT-")

    def test_cccd_field_is_pseudonym(self):
        rows = self.conn.get_encounter_summary(limit=5)
        for row in rows:
            if row.get("cccd") is not None:
                assert row["cccd"].startswith("PT-")

    def test_phone_field_is_pseudonym(self):
        rows = self.conn.get_encounter_summary(limit=5)
        for row in rows:
            if row.get("phone") is not None:
                assert row["phone"].startswith("PT-")

    def test_non_pii_fields_unchanged(self):
        rows = self.conn.get_encounter_summary(limit=5)
        # diagnosis_code và complaint không phải PII
        real_codes = {"E11", "I10"}
        found_codes = {r.get("diagnosis_code") for r in rows if r.get("diagnosis_code")}
        assert found_codes.issubset(real_codes | {None})

    def test_null_pii_field_remains_none(self):
        rows = self.conn.get_encounter_summary(limit=5)
        # Row 3 có name=NULL → phải trả None, không phải "PT-..."
        null_rows = [r for r in rows if r.get("id") == 3]
        if null_rows:
            assert null_rows[0]["name"] is None

    def test_no_real_pii_in_output(self):
        """Không có giá trị PII thật nào lọt qua de-identification."""
        rows = self.conn.get_encounter_summary(limit=10)
        real_pii_values = {"Nguyen Van A", "Nguyễn Văn A", "012345678901", "0901234567",
                           "Tran Thi B", "Trần Thị B", "098765432109", "0987654321"}
        for row in rows:
            for v in row.values():
                assert v not in real_pii_values, f"PII thật lọt qua: {v!r}"


# ─── T36: Pseudonym consistency ───────────────────────────────────────────────

class TestT36PseudonymConsistency:
    def setup_method(self):
        # V4.2.1: bật flag synthetic + dùng DB tạm (KHÔNG phải DB thật).
        os.environ[_ENABLE_FLAG] = "1"
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = Path(self.tmp.name)
        _make_test_db(self.db_path)
        self.conn = eHospitalConnector(db_path=self.db_path)

    def teardown_method(self):
        os.environ.pop(_ENABLE_FLAG, None)
        self.tmp.close()
        self.db_path.unlink(missing_ok=True)

    def test_pseudonym_is_deterministic(self):
        """Cùng giá trị → cùng pseudonym."""
        p1 = eHospitalConnector._pseudonym("Nguyen Van A")
        p2 = eHospitalConnector._pseudonym("Nguyen Van A")
        assert p1 == p2

    def test_different_values_give_different_pseudonyms(self):
        p1 = eHospitalConnector._pseudonym("Nguyen Van A")
        p2 = eHospitalConnector._pseudonym("Tran Thi B")
        assert p1 != p2

    def test_pseudonym_starts_with_pt(self):
        p = eHospitalConnector._pseudonym("any_value")
        assert p.startswith("PT-")

    def test_pseudonym_does_not_contain_original(self):
        original = "Nguyen Van A"
        p = eHospitalConnector._pseudonym(original)
        assert original not in p


# ─── T37: Diagnosis distribution (no PII) ────────────────────────────────────

class TestT37DiagnosisDistribution:
    def setup_method(self):
        # V4.2.1: bật flag synthetic + dùng DB tạm (KHÔNG phải DB thật).
        os.environ[_ENABLE_FLAG] = "1"
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = Path(self.tmp.name)
        _make_test_db(self.db_path)
        self.conn = eHospitalConnector(db_path=self.db_path)

    def teardown_method(self):
        os.environ.pop(_ENABLE_FLAG, None)
        self.tmp.close()
        self.db_path.unlink(missing_ok=True)

    def test_diagnosis_returns_icd_codes(self):
        dist = self.conn.get_diagnosis_distribution()
        assert "E11" in dist
        assert "I10" in dist

    def test_diagnosis_count_correct(self):
        dist = self.conn.get_diagnosis_distribution()
        assert dist.get("E11") == 2  # 2 lần trong test data

    def test_diagnosis_no_pii(self):
        dist = self.conn.get_diagnosis_distribution()
        for code in dist:
            assert not code.startswith("PT-"), "ICD code không phải PII"


# ─── T38: format_for_agent ────────────────────────────────────────────────────

class TestT38FormatForAgent:
    def setup_method(self):
        # V4.2.1: bật flag synthetic + dùng DB tạm (KHÔNG phải DB thật).
        os.environ[_ENABLE_FLAG] = "1"
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = Path(self.tmp.name)
        _make_test_db(self.db_path)
        self.conn = eHospitalConnector(db_path=self.db_path)

    def teardown_method(self):
        os.environ.pop(_ENABLE_FLAG, None)
        self.tmp.close()
        self.db_path.unlink(missing_ok=True)

    def test_format_has_source_field(self):
        rows = self.conn.get_encounter_summary()
        fmt = self.conn.format_for_agent(rows)
        assert fmt["source"] == "eHospital_Mini"

    def test_format_pii_scrubbed_true(self):
        rows = self.conn.get_encounter_summary()
        fmt = self.conn.format_for_agent(rows)
        assert fmt["pii_scrubbed"] is True

    def test_format_record_count_correct(self):
        rows = self.conn.get_encounter_summary(limit=2)
        fmt = self.conn.format_for_agent(rows)
        assert fmt["record_count"] == len(rows)

    def test_format_empty_list_ok(self):
        fmt = self.conn.format_for_agent([])
        assert fmt["record_count"] == 0
        assert fmt["encounters"] == []


# ─── T39: PII fields registry ─────────────────────────────────────────────────

class TestT39PIIFieldsRegistry:
    def test_pii_fields_include_name(self):
        assert "name" in _PII_FIELDS

    def test_pii_fields_include_cccd(self):
        assert "cccd" in _PII_FIELDS

    def test_pii_fields_include_phone(self):
        assert "phone" in _PII_FIELDS

    def test_pii_fields_is_frozenset(self):
        assert isinstance(_PII_FIELDS, frozenset)

    def test_icd_code_not_in_pii_fields(self):
        assert "diagnosis_code" not in _PII_FIELDS


# ─── T40: V4.2.1 Hardening — DISABLED-by-default, no auto-discover, no real DB ──

class TestT40V421Hardening:
    """eHospitalConnector OUT OF SCOPE cho live workflow; chỉ test synthetic."""

    def teardown_method(self):
        os.environ.pop(_ENABLE_FLAG, None)

    def test_disabled_by_default_even_with_valid_synthetic_path(self):
        """Không flag → DISABLED dù có db_path synthetic hợp lệ; KHÔNG mở DB."""
        os.environ.pop(_ENABLE_FLAG, None)
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        try:
            p = Path(tmp.name)
            _make_test_db(p)
            conn = eHospitalConnector(db_path=p)
            assert conn.is_available is False
            assert conn.db_path is None
            assert conn.disabled_reason == "DISABLED_BY_DEFAULT_NO_SYNTHETIC_FLAG"
            # Không mở DB ⇒ mọi truy vấn trả rỗng.
            assert conn.get_encounter_summary() == []
            assert conn.get_diagnosis_distribution() == {}
        finally:
            tmp.close()
            Path(tmp.name).unlink(missing_ok=True)

    def test_flag_set_but_no_path_does_not_autodiscover(self):
        """Flag bật nhưng không truyền db_path → KHÔNG auto-discover ~/.ehospital."""
        os.environ[_ENABLE_FLAG] = "1"
        conn = eHospitalConnector(db_path=None)
        assert conn.is_available is False
        assert conn.db_path is None
        assert conn.disabled_reason == "NO_EXPLICIT_SYNTHETIC_DB_PATH"

    def test_refuses_real_ehospital_db_path(self):
        """Flag bật + db_path trỏ ~/.ehospital → TỪ CHỐI (không dùng DB thật)."""
        os.environ[_ENABLE_FLAG] = "1"
        real_like = _EHOSPITAL_DIR / "ehospital.db"
        conn = eHospitalConnector(db_path=real_like)
        assert conn.is_available is False
        assert conn.disabled_reason == "REAL_EHOSPITAL_DB_REFUSED"

    def test_enabled_with_synthetic_path_opens(self):
        """Flag bật + db_path synthetic tường minh → khả dụng."""
        os.environ[_ENABLE_FLAG] = "1"
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        try:
            p = Path(tmp.name)
            _make_test_db(p)
            conn = eHospitalConnector(db_path=p)
            assert conn.is_available is True
            assert conn.disabled_reason is None
        finally:
            tmp.close()
            Path(tmp.name).unlink(missing_ok=True)

    def test_offline_default_never_opens_local_db(self, monkeypatch):
        """Chốt offline: ở default mode, connector không bao giờ kết nối sqlite."""
        os.environ.pop(_ENABLE_FLAG, None)
        import runtime.ehospital_connector as ehc

        def _boom(*a, **k):
            raise AssertionError("sqlite3.connect KHÔNG được gọi ở default mode")

        monkeypatch.setattr(ehc.sqlite3, "connect", _boom)
        conn = eHospitalConnector(db_path=None)
        # Mọi API đọc đều phải trả rỗng mà KHÔNG chạm sqlite3.connect.
        assert conn.get_encounter_summary() == []
        assert conn.get_diagnosis_distribution() == {}
        assert conn.get_medication_frequency() == {}
        assert conn.get_db_schema() == {}
