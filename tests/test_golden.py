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
        from run_g3_auto import n_two_proportion, n_continuous_md
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
