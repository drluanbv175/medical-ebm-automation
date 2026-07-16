"""
AC-04 (MRAQ-100 acceptance criteria, gap G-H01) — Golden tests cho G3/G6/G7.

NGUYÊN TẮC BẤT BIẾN của toàn hệ thống (xem
EXECUTION_EVIDENCE_20260704/NO-GO_REMEDIATION_STATUS.md và
tests/test_offline_workflow_integration.py::TestTC12MraqScoreNotRaised):
"AI KHÔNG tự đóng gap, KHÔNG tự ký, KHÔNG tự nâng điểm MRAQ."

Mỗi fixture tests/fixtures/golden/*.json có trường `approved_by_pi`. Bài test
này CHỦ ĐỘNG KHÔNG coi một fixture là "đã qua AC-04" chỉ vì output khớp
expected_output — nó CÒN đòi hỏi approved_by_pi=true (do PI tự ký, AI không
được đặt giá trị này). Nếu chưa duyệt, test SKIP kèm lý do rõ ràng (không
PASS ngầm, không FAIL gây hoang mang) — để không bao giờ tạo cảm giác AC-04
đã đóng khi PI chưa thực sự xem qua.

Test vẫn CHẠY được phần "output có khớp expected_output không" ngay cả khi
chưa duyệt — mục đích: nếu code sau này thay đổi làm hỏng golden case, phát
hiện NGAY (regression), không đợi PI duyệt xong mới biết.
"""
import json
import sys
from pathlib import Path
from typing import Any

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "golden"
TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))


def _load_fixtures():
    if not FIXTURES_DIR.exists():
        return []
    return sorted(FIXTURES_DIR.glob("*.json"))


FIXTURE_FILES = _load_fixtures()


def _fixture_id(path):
    return path.stem


def _dataframe_from_seeded_spec(spec: dict[str, Any]):
    """Tạo dataset synthetic không PII từ đặc tả fixture golden G6.

    Không dùng dữ liệu thật; mục tiêu là regression test kỹ thuật cho engine G6,
    không phải bằng chứng hiệu quả lâm sàng.
    """
    np = pytest.importorskip("numpy")
    pd = pytest.importorskip("pandas")
    rng = np.random.default_rng(spec["seed"])
    kind = spec["kind"]
    n = int(spec["n"])
    if kind == "binary_logistic_seeded":
        exposure = rng.integers(0, 2, n)
        age = rng.normal(55, 9, n).round(1)
        bmi = rng.normal(25, 3, n).round(1)
        sex = rng.integers(0, 2, n)
        coefs = spec["coefficients"]
        lin = (
            float(spec["intercept"])
            + float(coefs["exposure"]) * exposure
            + float(coefs["age_centered"]) * (age - 55)
            + float(coefs["bmi_centered"]) * (bmi - 25)
            + float(coefs["sex"]) * sex
        )
        p = 1 / (1 + np.exp(-lin))
        outcome = rng.binomial(1, p)
        return pd.DataFrame({
            "outcome": outcome,
            "exposure": exposure,
            "age": age,
            "bmi": bmi,
            "sex": sex,
        })
    if kind == "cox_survival_seeded":
        exposure = rng.integers(0, 2, n)
        age = rng.normal(58, 10, n).round(1)
        coefs = spec["coefficients"]
        hazard = (
            float(spec["baseline_hazard"])
            * np.exp(float(coefs["exposure"]) * exposure + float(coefs["age_centered"]) * (age - 58))
        )
        event_time = rng.exponential(1 / hazard)
        censor = rng.uniform(float(spec["censor_uniform_low"]), float(spec["censor_uniform_high"]), n)
        follow = np.minimum(event_time, censor).round(1)
        event = (event_time <= censor).astype(int)
        return pd.DataFrame({
            "age": age,
            "exposure_var": exposure,
            "follow_time": follow,
            "event_flag": event,
        })
    raise ValueError(f"Unsupported golden data kind: {kind}")


@pytest.mark.parametrize("fixture_path", FIXTURE_FILES, ids=_fixture_id)
def test_golden_case_output_matches_expected(fixture_path):
    """Regression: output THẬT của code hôm nay có khớp expected_output đã ghi trong fixture không.

    Chạy độc lập với việc PI đã duyệt hay chưa — mục đích bắt hồi quy sớm.
    Fixture ở trạng thái TODO (chưa có function/expected_output) sẽ SKIP.
    """
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    if fixture.get("status", "").startswith("TODO"):
        pytest.skip(f"{fixture['golden_id']}: {fixture.get('why_not_built_2026-07-06', 'chưa dựng')}")

    gate = fixture["gate"]
    func_name = fixture.get("function")
    expected = fixture["expected_output"]

    if gate == "G3":
        from run_g3_auto import n_continuous_md, n_two_proportion
        fn = {"n_two_proportion": n_two_proportion, "n_continuous_md": n_continuous_md}[func_name]
        actual = fn(**fixture["input"])
        assert actual == expected["n_per_group"], (
            f"{fixture['golden_id']}: {func_name}({fixture['input']}) = {actual}, "
            f"kỳ vọng {expected['n_per_group']} ({fixture['expected_output_source']})"
        )
    elif gate == "G7" and func_name == "guardrail_g7":
        from run_g7_auto import guardrail_g7
        bad_errors, _ = guardrail_g7(fixture["input"]["bad_manuscript"])
        good_errors, _ = guardrail_g7(fixture["input"]["good_manuscript"])
        assert len(bad_errors) == expected["bad_manuscript_error_count"], (
            f"{fixture['golden_id']}: bad manuscript ra {len(bad_errors)} lỗi, "
            f"kỳ vọng {expected['bad_manuscript_error_count']}: {bad_errors}"
        )
        assert len(good_errors) == expected["good_manuscript_error_count"], (
            f"{fixture['golden_id']}: good manuscript ra {len(good_errors)} lỗi (kỳ vọng 0): {good_errors}"
        )
    elif gate == "G6" and func_name == "multivariate_model":
        pytest.importorskip("statsmodels")
        from run_stats_analysis import multivariate_model
        df = _dataframe_from_seeded_spec(fixture["input"]["data"])
        actual = multivariate_model(
            df,
            fixture["input"]["outcome_col"],
            fixture["input"]["group_col"],
            fixture["input"]["covariates"],
            outcome_type=fixture["input"]["outcome_type"],
        )
        assert actual == expected, (
            f"{fixture['golden_id']}: multivariate_model() lệch golden output.\n"
            f"Actual: {actual}\nExpected: {expected}"
        )
    elif gate == "G6" and func_name == "survival_model":
        pytest.importorskip("lifelines")
        from run_stats_analysis import survival_model
        df = _dataframe_from_seeded_spec(fixture["input"]["data"])
        actual = survival_model(
            df,
            fixture["input"]["time_col"],
            fixture["input"]["event_col"],
            fixture["input"]["group_col"],
            fixture["input"]["covariates"],
        )
        assert actual == expected, (
            f"{fixture['golden_id']}: survival_model() lệch golden output.\n"
            f"Actual: {actual}\nExpected: {expected}"
        )
    else:
        pytest.skip(f"{fixture['golden_id']}: gate/function '{gate}/{func_name}' chưa có runner trong test_golden.py")


@pytest.mark.parametrize("fixture_path", FIXTURE_FILES, ids=_fixture_id)
def test_golden_case_pi_approved(fixture_path):
    """AC-04 THẬT SỰ đóng: yêu cầu approved_by_pi=true + approved_by có tên.

    Test này CỐ Ý fail/skip cho tới khi PI thực sự ký — đây là cổng, không phải
    thủ tục hình thức. Không được sửa fixture để tự đặt approved_by_pi=true
    nếu không phải PI làm việc đó.
    """
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    if fixture.get("status", "").startswith("TODO"):
        pytest.skip(f"{fixture['golden_id']}: chưa dựng case, chưa tới bước PI duyệt")
    if not fixture.get("approved_by_pi"):
        pytest.skip(
            f"{fixture['golden_id']}: CHỜ PI DUYỆT (AC-04 chưa đóng) — "
            f"xem notes_for_pi trong {fixture_path.name}"
        )
    assert fixture.get("approved_by"), f"{fixture['golden_id']}: approved_by_pi=true nhưng thiếu tên người duyệt"
    assert fixture.get("approved_date"), f"{fixture['golden_id']}: approved_by_pi=true nhưng thiếu ngày duyệt"
