"""Test cầu nối agent EBM cho ChatGPT App."""

from __future__ import annotations

import unicodedata
from pathlib import Path

import pytest

from app.chatgpt_app.agents import SYNC_CONFIRMATION, SafeAgentCatalog

ROOT = Path(__file__).resolve().parents[1]


def test_catalog_exposes_orchestrators_and_guardrail() -> None:
    catalog = SafeAgentCatalog(ROOT)
    ids = {row["id"] for row in catalog.list_payload()["agents"]}
    assert "dieu-phoi-lam-sang" in ids
    assert "dieu-phoi-nghien-cuu" in ids
    assert "tham-dinh-dau-ra" in ids
    assert len(ids) >= 50


def test_agent_payload_is_proposal_only() -> None:
    payload = SafeAgentCatalog(ROOT).get_payload("ke-don-an-toan")
    contract = payload["execution_contract"]
    assert contract["mode"] == "proposal_only"
    assert contract["must_call_guardrail_last"] is True
    assert contract["automatic_gate_approval"] is False


def test_clinical_workflow_blocks_pii() -> None:
    payload = SafeAgentCatalog(ROOT).workflow_payload(
        "clinical", "Bệnh nhân Nguyễn Văn An, CCCD 012345678901, đau ngực"
    )
    assert payload["status"] == "blocked"
    assert payload["reason"] == "possible_pii_detected"


def test_clinical_workflow_includes_gate_a_b_and_guardrail() -> None:
    payload = SafeAgentCatalog(ROOT).workflow_payload(
        "clinical", "Nam 68 tuổi, đau ngực khi gắng sức, không có thông tin định danh"
    )
    assert payload["status"] == "ready_to_orchestrate"
    assert payload["entry_agent"] == "dieu-phoi-lam-sang"
    assert "GATE_A_PHYSICIAN_APPLICATION" in payload["hard_gates"]
    assert "tham-dinh-dau-ra" in payload["final_guardrail_instructions"]


def test_research_workflow_includes_hard_gates() -> None:
    payload = SafeAgentCatalog(ROOT).workflow_payload(
        "research", "Đề tài hiệu quả can thiệp tuân thủ ở người bệnh tăng huyết áp"
    )
    assert payload["status"] == "ready_to_orchestrate"
    assert payload["entry_agent"] == "dieu-phoi-nghien-cuu"
    assert {"G2_IRB", "G4_SAP_LOCK", "G8_INDEPENDENT_REVIEW", "G9_PI_INTEGRITY"} <= set(payload["hard_gates"])


def test_agent_path_traversal_is_blocked() -> None:
    with pytest.raises(KeyError):
        SafeAgentCatalog(ROOT).get_payload("../secrets")


def test_sync_requires_exact_confirmation() -> None:
    payload = SafeAgentCatalog(ROOT).synchronize("yes")
    assert payload["status"] == "confirmation_required"
    assert payload["required_confirmation"] == SYNC_CONFIRMATION


# ── Hồi quy audit MCP ChatGPT 2026-07-20 ──────────────────────────────────────


def test_clinical_ids_match_readme_cum_lam_sang() -> None:
    """Danh sách domain='clinical' phải khớp ĐÚNG bảng "Cụm Lâm sàng (21 agent)"
    trong .claude/agents/README.md — trước đây có 'huong-dan-lam-sang' (thực ra
    thuộc Cụm Nghiên cứu, cầu nối NC↔Thực hành) mà THIẾU 'cap-nhat-guideline'."""
    ids = {row["id"] for row in SafeAgentCatalog(ROOT).list_payload("clinical")["agents"]}
    assert "cap-nhat-guideline" in ids
    assert "huong-dan-lam-sang" not in ids
    assert len(ids) == 21


def test_agent_source_with_nfd_pii_is_blocked(tmp_path: Path) -> None:
    """SENSITIVE_ID_PATTERN literal ở dạng NFC — trước bản vá, agent .md chứa PII
    dạng NFD (chữ nền + dấu rời, phổ biến khi dán từ macOS/nguồn khác) lọt cổng
    hoàn toàn dù cùng nội dung ở dạng NFC bị chặn đúng thiết kế."""
    agent_dir = tmp_path / ".claude/agents"
    agent_dir.mkdir(parents=True)
    body_nfc = "# Demo\n\ncăn cước: ABC123456\n"
    (agent_dir / "demo-nfd.md").write_text(unicodedata.normalize("NFD", body_nfc), encoding="utf-8")
    (agent_dir / "demo-nfc.md").write_text(body_nfc, encoding="utf-8")

    catalog = SafeAgentCatalog(tmp_path)
    with pytest.raises(KeyError):
        catalog.get_payload("demo-nfd")
    with pytest.raises(KeyError):
        catalog.get_payload("demo-nfc")


def test_agent_source_with_phone_beyond_classify_sample_is_blocked(tmp_path: Path) -> None:
    """classify_export_file() lấy mẫu — agents.py phải TỰ quét toàn văn thêm bằng
    contains_pii_text() (trước đây chỉ dựa SENSITIVE_ID_PATTERN, bỏ sót SĐT/email)."""
    agent_dir = tmp_path / ".claude/agents"
    agent_dir.mkdir(parents=True)
    (agent_dir / "demo-phone.md").write_text(
        "# Demo\n\nLiên hệ hỗ trợ: 090 123 4567\n", encoding="utf-8"
    )
    with pytest.raises(KeyError):
        SafeAgentCatalog(tmp_path).get_payload("demo-phone")


def test_clinical_workflow_blocks_realistic_free_text_pii() -> None:
    """Tái hiện đúng kịch bản audit: câu văn tự do có họ tên + địa chỉ + SĐT có dấu
    cách + 'số bệnh án' — trước bản vá contains_pii_text/SENSITIVE_ID_PATTERN đều
    bỏ sót, khiến toàn bộ PII bị echo nguyên văn vào response gửi ChatGPT."""
    text = (
        "Bệnh nhân Nguyễn Văn A, 45 tuổi, ngụ 12 Nguyễn Trãi Q1 TPHCM, "
        "SĐT 090 123 4567, số bệnh án 123456, đang dùng metformin"
    )
    payload = SafeAgentCatalog(ROOT).workflow_payload("clinical", text)
    assert payload["status"] == "blocked"
    assert payload["reason"] == "possible_pii_detected"


def test_synchronize_redacts_pii_like_subprocess_output(monkeypatch, tmp_path: Path) -> None:
    """output_tail của synchronize() phải qua cùng cổng PII như mọi nhánh khác —
    trước đây log subprocess được trả nguyên văn không qua contains_pii_text/
    SENSITIVE_ID_PATTERN (phòng thủ theo chiều sâu cho thay đổi script tương lai)."""
    import subprocess as subprocess_module

    project_root = tmp_path / "medical-ebm-automation"
    project_root.mkdir()
    catalog = SafeAgentCatalog(project_root)
    root = tmp_path  # synchronize() dùng root = project_root.parent
    for name in (
        "tools/enforce_agent_guardrails.py",
        "tools/sync_agents_to_codex.py",
        "tools/check_claude_codex_sync_health.py",
    ):
        script = root / name
        script.parent.mkdir(parents=True, exist_ok=True)
        script.write_text("print('ok')\n", encoding="utf-8")

    class _FakeCompleted:
        returncode = 0
        stdout = "leak: CCCD 012345678901\n"
        stderr = ""

    monkeypatch.setattr(subprocess_module, "run", lambda *a, **k: _FakeCompleted())
    payload = catalog.synchronize(SYNC_CONFIRMATION)
    assert payload["status"] == "synchronized"
    for step in payload["results"]:
        assert "012345678901" not in step["output_tail"]
