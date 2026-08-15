"""
R2.0 Synthetic EDC Core Tests — CRF registry, data dictionary, edit checks.

MRAQ_OFFLINE_CI=1 pytest tests/test_r2_0_synthetic_edc_core.py -v
"""

import pytest

from research_project.synthetic_edc_core import (
    PROD_EDC_DEPENDENCY,
    SYNTHETIC_EDC_CLASSIFICATION,
    CRFVersion,
    CRFVersionRegistry,
    DataDictionary,
    EditCheck,
    EditCheckEngine,
    EditCheckSeverity,
    FieldDefinition,
    FieldType,
)

# ── Fixtures ───────────────────────────────────────────────────────────────

def _make_crf_v1(is_current: bool = True) -> CRFVersion:
    return CRFVersion(
        version_id="v1.0",
        version_label="Version 1.0",
        effective_date="2026-01-01",
        is_current=is_current,
        change_reason="Initial version",
        approved_by="PI_synthetic",
        fields=["age", "sex", "sbp"],
    )

def _make_crf_v2() -> CRFVersion:
    return CRFVersion(
        version_id="v2.0",
        version_label="Version 2.0",
        effective_date="2026-06-01",
        is_current=True,
        change_reason="Added blood glucose",
        approved_by="PI_synthetic",
        fields=["age", "sex", "sbp", "glucose"],
    )

def _make_dict_with_fields() -> DataDictionary:
    dd = DataDictionary(study_id="STUDY-001")
    dd.add_field(FieldDefinition("age", FieldType.INTEGER, required=True,
                                  label="Age (years)", min_value=0, max_value=120))
    dd.add_field(FieldDefinition("sex", FieldType.CATEGORICAL, required=True,
                                  label="Sex", allowed_values=["M", "F", "OTHER"]))
    dd.add_field(FieldDefinition("sbp", FieldType.FLOAT, required=False,
                                  label="Systolic BP (mmHg)", min_value=50, max_value=300,
                                  unit="mmHg"))
    dd.add_field(FieldDefinition("glucose", FieldType.FLOAT, required=False,
                                  label="Fasting glucose (mmol/L)", min_value=0, max_value=50))
    return dd


# ── CRFVersionRegistry ─────────────────────────────────────────────────────

class TestCRFVersionRegistry:
    def test_add_and_get_current(self):
        reg = CRFVersionRegistry()
        reg.add_version(_make_crf_v1())
        current = reg.get_current()
        assert current.version_id == "v1.0"

    def test_adding_new_current_demotes_previous(self):
        reg = CRFVersionRegistry()
        reg.add_version(_make_crf_v1())
        reg.add_version(_make_crf_v2())
        assert reg.get_current().version_id == "v2.0"
        assert reg.get_version("v1.0").is_current is False

    def test_get_version_by_id(self):
        reg = CRFVersionRegistry()
        reg.add_version(_make_crf_v1())
        v = reg.get_version("v1.0")
        assert v.version_label == "Version 1.0"

    def test_duplicate_version_id_raises(self):
        reg = CRFVersionRegistry()
        reg.add_version(_make_crf_v1())
        with pytest.raises(KeyError):
            reg.add_version(_make_crf_v1())

    def test_get_current_without_any_version_raises(self):
        reg = CRFVersionRegistry()
        with pytest.raises(LookupError):
            reg.get_current()

    def test_list_versions(self):
        reg = CRFVersionRegistry()
        reg.add_version(_make_crf_v1())
        reg.add_version(_make_crf_v2())
        assert set(reg.list_versions()) == {"v1.0", "v2.0"}

    def test_lock_prevents_new_version(self):
        reg = CRFVersionRegistry()
        reg.add_version(_make_crf_v1())
        reg.lock()
        assert reg.is_locked is True
        with pytest.raises(PermissionError):
            reg.add_version(_make_crf_v2())

    def test_version_count(self):
        reg = CRFVersionRegistry()
        assert reg.version_count == 0
        reg.add_version(_make_crf_v1())
        assert reg.version_count == 1


# ── CRFVersion validation ──────────────────────────────────────────────────

class TestCRFVersion:
    def test_valid_version_is_created(self):
        v = _make_crf_v1()
        assert v.version_id == "v1.0"

    def test_empty_version_id_raises(self):
        with pytest.raises(ValueError, match="version_id"):
            CRFVersion("", "v1", "2026-01-01", True, "reason", "PI")

    def test_empty_label_raises(self):
        with pytest.raises(ValueError, match="version_label"):
            CRFVersion("v1", "", "2026-01-01", True, "reason", "PI")

    def test_empty_date_raises(self):
        with pytest.raises(ValueError, match="effective_date"):
            CRFVersion("v1", "Version 1", "", True, "reason", "PI")


# ── DataDictionary ─────────────────────────────────────────────────────────

class TestDataDictionary:
    def test_add_and_retrieve_field(self):
        dd = _make_dict_with_fields()
        fd = dd.get_field("age")
        assert fd.field_type == FieldType.INTEGER

    def test_duplicate_field_raises(self):
        dd = DataDictionary("S1")
        dd.add_field(FieldDefinition("age", FieldType.INTEGER, True, "Age"))
        with pytest.raises(KeyError):
            dd.add_field(FieldDefinition("age", FieldType.INTEGER, True, "Age dup"))

    def test_unknown_field_raises(self):
        dd = DataDictionary("S1")
        with pytest.raises(KeyError):
            dd.get_field("nonexistent")

    def test_required_fields_list(self):
        dd = _make_dict_with_fields()
        req = dd.required_fields
        assert "age" in req
        assert "sex" in req
        assert "sbp" not in req

    def test_validate_valid_record(self):
        dd = _make_dict_with_fields()
        results = dd.validate_record({"age": 45, "sex": "M", "sbp": 120.0})
        errors = [r for r in results if not r.is_valid]
        assert errors == []

    def test_validate_missing_required_field(self):
        dd = _make_dict_with_fields()
        results = dd.validate_record({"sex": "F"})
        age_result = next(r for r in results if r.field_name == "age")
        assert not age_result.is_valid
        assert "required" in age_result.error_message

    def test_validate_integer_out_of_range(self):
        dd = _make_dict_with_fields()
        results = dd.validate_record({"age": 200, "sex": "M"})
        age_result = next(r for r in results if r.field_name == "age")
        assert not age_result.is_valid
        assert "max" in age_result.error_message

    def test_validate_invalid_categorical(self):
        dd = _make_dict_with_fields()
        results = dd.validate_record({"age": 40, "sex": "UNKNOWN"})
        sex_result = next(r for r in results if r.field_name == "sex")
        assert not sex_result.is_valid

    def test_validate_unknown_field_in_record(self):
        dd = _make_dict_with_fields()
        results = dd.validate_record({"age": 30, "sex": "F", "UNKNOWN_FIELD": "x"})
        unknown = next(r for r in results if r.field_name == "UNKNOWN_FIELD")
        assert not unknown.is_valid


# ── EditCheckEngine ────────────────────────────────────────────────────────

class TestEditCheckEngine:
    def test_no_checks_returns_empty(self):
        engine = EditCheckEngine()
        assert engine.run_checks("rec-001", {"age": 30}) == []

    def test_passing_check_returns_no_violation(self):
        engine = EditCheckEngine()
        engine.add_check(EditCheck(
            "EC-001", "age",
            lambda d: d.get("age", 0) < 0,
            "Age cannot be negative",
        ))
        violations = engine.run_checks("rec-001", {"age": 30})
        assert violations == []

    def test_failing_check_returns_violation(self):
        engine = EditCheckEngine()
        engine.add_check(EditCheck(
            "EC-002", "sbp",
            lambda d: d.get("sbp", 0) > 300,
            "SBP > 300 is implausible",
            EditCheckSeverity.ERROR,
        ))
        violations = engine.run_checks("rec-001", {"sbp": 350})
        assert len(violations) == 1
        assert violations[0].check_id == "EC-002"
        assert violations[0].severity == EditCheckSeverity.ERROR

    def test_duplicate_check_id_raises(self):
        engine = EditCheckEngine()
        engine.add_check(EditCheck("EC-001", "age", lambda d: False, "msg"))
        with pytest.raises(KeyError):
            engine.add_check(EditCheck("EC-001", "sbp", lambda d: False, "msg2"))

    def test_check_count(self):
        engine = EditCheckEngine()
        engine.add_check(EditCheck("EC-A", "age", lambda d: False, "a"))
        engine.add_check(EditCheck("EC-B", "sbp", lambda d: False, "b"))
        assert engine.check_count == 2

    def test_run_checks_for_specific_field(self):
        engine = EditCheckEngine()
        engine.add_check(EditCheck("EC-AGE", "age", lambda d: d.get("age", 0) < 0, "neg age"))
        engine.add_check(EditCheck("EC-SBP", "sbp", lambda d: d.get("sbp", 0) > 300, "high sbp"))
        violations = engine.run_checks_for_field("age", "rec-001", {"age": -1, "sbp": 350})
        assert all(v.field == "age" for v in violations)
        assert len(violations) == 1

    def test_multiple_violations_returned(self):
        engine = EditCheckEngine()
        engine.add_check(EditCheck("EC-1", "age", lambda d: d.get("age", 0) < 0, "neg age"))
        engine.add_check(EditCheck("EC-2", "sbp", lambda d: d.get("sbp", 0) > 300, "high sbp"))
        violations = engine.run_checks("rec-001", {"age": -5, "sbp": 400})
        assert len(violations) == 2

    def test_warning_severity_check(self):
        engine = EditCheckEngine()
        engine.add_check(EditCheck(
            "EC-WARN", "glucose",
            lambda d: d.get("glucose", 5) > 10,
            "High glucose — verify",
            EditCheckSeverity.WARNING,
        ))
        violations = engine.run_checks("rec-001", {"glucose": 15})
        assert violations[0].severity == EditCheckSeverity.WARNING

    def test_constants_present(self):
        assert PROD_EDC_DEPENDENCY
        assert "NOT_IMPLEMENTED" in PROD_EDC_DEPENDENCY
        assert SYNTHETIC_EDC_CLASSIFICATION
        assert "SYNTHETIC" in SYNTHETIC_EDC_CLASSIFICATION
