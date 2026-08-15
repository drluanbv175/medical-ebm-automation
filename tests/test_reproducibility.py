"""
AC-05 (MRAQ-100 acceptance criteria) — Reproduction test: cùng input phải cho
cùng output (hash khớp), chạy nhiều lần liên tiếp trên MockAgentRuntime
(offline, deterministic, không gọi API, không PII).

Đây là kiểm tra TÍNH TẤT ĐỊNH CỦA PHẦN MỀM (cùng input → cùng output) — không
phải đánh giá ĐÚNG-SAI Y KHOA của nội dung (việc đó thuộc golden test AC-04,
cần PI duyệt expected output). Do đó bài test này KHÔNG cần phán đoán lâm sàng
và có thể tự động hóa/chạy lặp lại hợp lệ.
"""
import dataclasses
import hashlib
import json

import pytest

from runtime.approval_ledger import ApprovalLedger
from runtime.mock_agent_runtime import FIXTURE_CATALOG, MockAgentRuntime
from runtime.policy_gate_engine import PolicyGateEngine


def _hash_output(result) -> str:
    """Băm output của AgentRunResult (bỏ trường không tất định: run_id, timestamp_utc)."""
    d = dataclasses.asdict(result)
    d.pop("run_id", None)
    d.pop("timestamp_utc", None)
    payload = json.dumps(d, sort_keys=True, default=str, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


REPRO_FIXTURE_IDS = [fid for fid in FIXTURE_CATALOG if fid.startswith("FX-0")][:8]


@pytest.mark.parametrize("fixture_id", REPRO_FIXTURE_IDS)
def test_same_input_same_output_hash(fixture_id):
    """Chạy cùng 1 fixture 3 lần liên tiếp qua MockAgentRuntime — hash output phải khớp cả 3 lần."""
    runtime = MockAgentRuntime()
    hashes = []
    for _ in range(3):
        result = runtime.run(agent_id="repro-test", fixture_id=fixture_id, input_data={})
        hashes.append(_hash_output(result))
    assert len(set(hashes)) == 1, (
        f"{fixture_id}: hash KHÔNG khớp giữa các lần chạy — vi phạm tính tất định "
        f"({hashes})"
    )


@pytest.mark.parametrize("fixture_id", REPRO_FIXTURE_IDS)
def test_same_input_same_policy_decision(fixture_id):
    """PolicyGateEngine phải ra cùng quyết định cho cùng fixture, lặp lại 3 lần, ledger trống mỗi lần."""
    runtime = MockAgentRuntime()
    engine = PolicyGateEngine()
    decisions = []
    for _ in range(3):
        runtime.run(agent_id="repro-test", fixture_id=fixture_id, input_data={})
        ledger = ApprovalLedger()
        decision = engine.evaluate_fixture(FIXTURE_CATALOG[fixture_id], ledger)
        decisions.append(decision)
    assert len(set(decisions)) == 1, (
        f"{fixture_id}: PolicyGateEngine quyết định KHÔNG khớp giữa các lần chạy ({decisions})"
    )


def test_two_independent_runtime_instances_agree():
    """Hai instance MockAgentRuntime độc lập (không chia sẻ state) phải cho cùng hash cho cùng fixture."""
    fixture_id = REPRO_FIXTURE_IDS[0]
    r1 = MockAgentRuntime().run(agent_id="repro-test", fixture_id=fixture_id, input_data={})
    r2 = MockAgentRuntime().run(agent_id="repro-test", fixture_id=fixture_id, input_data={})
    assert _hash_output(r1) == _hash_output(r2)
