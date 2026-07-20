"""Kiểm tra corpus ChatGPT App luôn fail-closed và đúng schema MCP."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from app.chatgpt_app.knowledge import SafeKnowledgeIndex, json_text
from app.chatgpt_app.server import _local_git_ref, mcp

ROOT = Path(__file__).resolve().parents[1]


def _index(tmp_path: Path) -> SafeKnowledgeIndex:
    return SafeKnowledgeIndex(tmp_path, repository="owner/repo", git_ref="main")


def test_search_and_fetch_use_standard_shapes(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "guide.md").write_text("# Hướng dẫn EBM\n\nCổng duyệt bác sĩ.", encoding="utf-8")

    index = _index(tmp_path)
    result = index.search("EBM bác sĩ")

    assert list(result) == ["results"]
    assert result["results"][0]["id"] == "docs/guide.md"
    fetched = index.fetch("docs/guide.md")
    assert fetched["title"] == "Hướng dẫn EBM"
    assert fetched["url"] == "https://github.com/owner/repo/blob/main/docs/guide.md"
    assert fetched["metadata"]["safety"] == "review_only_no_pii"
    assert "Cần bác sĩ kiểm chứng" in fetched["metadata"]["disclaimer"]


def test_secret_and_raw_dataset_are_never_indexed(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "safe.md").write_text("# Safe\nNo identifiers.", encoding="utf-8")
    (tmp_path / ".env").write_text("OPENAI_API_KEY=secret", encoding="utf-8")
    (docs / "patients.sqlite").write_bytes(b"not a real database")

    ids = {item["id"] for item in _index(tmp_path).search("")["results"]}

    assert ids == {"docs/safe.md"}


def test_fetch_blocks_path_traversal_and_non_allowlisted_file(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Public", encoding="utf-8")
    (tmp_path / "private.txt").write_text("not allowlisted", encoding="utf-8")
    index = _index(tmp_path)

    with pytest.raises(KeyError):
        index.fetch("../outside.md")
    with pytest.raises(KeyError):
        index.fetch("private.txt")


def test_pii_like_document_is_blocked(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "unsafe.md").write_text(
        "# Ca bệnh\nCCCD: 012345678901",
        encoding="utf-8",
    )

    assert _index(tmp_path).search("")["results"] == []


def test_json_text_is_valid_unicode_json() -> None:
    payload = {"results": [{"id": "a", "title": "Bằng chứng", "url": "https://example.com"}]}
    assert json.loads(json_text(payload)) == payload


def test_mcp_tool_contract_is_read_only_and_company_knowledge_compatible() -> None:
    tools = {tool.name: tool for tool in asyncio.run(mcp.list_tools())}

    assert set(tools) == {
        "search",
        "fetch",
        "get_system_status",
        "list_ebm_agents",
        "get_ebm_agent_instructions",
        "prepare_clinical_workflow",
        "prepare_research_workflow",
        "get_sync_status",
        "synchronize_ebm_system",
    }
    assert set(tools["search"].inputSchema["properties"]) == {"query"}
    assert tools["search"].inputSchema["required"] == ["query"]
    assert set(tools["fetch"].inputSchema["properties"]) == {"id"}
    assert tools["fetch"].inputSchema["required"] == ["id"]
    for name, tool in tools.items():
        assert tool.annotations is not None
        assert tool.annotations.readOnlyHint is (name != "synchronize_ebm_system")
        assert tool.annotations.destructiveHint is False


def test_local_git_ref_is_detected_without_subprocess(tmp_path: Path) -> None:
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "HEAD").write_text("ref: refs/heads/feat/chatgpt-app\n", encoding="utf-8")

    assert _local_git_ref(tmp_path) == "feat/chatgpt-app"


# ── Audit vòng 2 (2026-07-18): gia cố disclaimer inline, PII đuôi, auth, invariants ──


def test_fetch_text_includes_inline_disclaimer(tmp_path: Path) -> None:
    """Disclaimer PHẢI nằm trong thân `text` (không chỉ metadata) — ChatGPT
    thường render `text` làm nội dung; đầu ra y khoa luôn kèm disclaimer."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "g.md").write_text("# Hướng dẫn\nNội dung y khoa.", encoding="utf-8")
    fetched = _index(tmp_path).fetch("docs/g.md")
    assert "Cần bác sĩ kiểm chứng" in fetched["text"]
    assert fetched["text"].index("Cần bác sĩ") < fetched["text"].index("Nội dung y khoa")


def test_pii_in_document_tail_beyond_scan_window_is_blocked(tmp_path: Path) -> None:
    """PII ở phần đuôi (sau 200k ký tự cũ) phải bị chặn — vì fetch() phục vụ toàn
    văn tới 512KB. Trước vá 2026-07-18 chỉ quét text[:200_000] nên PII đuôi lọt."""
    docs = tmp_path / "docs"
    docs.mkdir()
    body = "# An toàn\n" + ("nội dung sạch. " * 15000) + "\nCCCD: 012345678901\n"
    assert len(body) > 200_000  # PII nằm SAU cửa sổ quét cũ
    (docs / "big.md").write_text(body, encoding="utf-8")
    assert _index(tmp_path).search("")["results"] == []


def test_system_status_invariants_are_locked(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# X", encoding="utf-8")
    s = _index(tmp_path).system_status()
    assert s["mode"] == "governed_orchestration_review"
    assert s["writes_enabled"] == "agent_mirror_sync_only_with_explicit_confirmation"
    assert s["pii_allowed"] is False
    assert s["clinical_release"] == "blocked"
    assert "prepare_clinical_workflow" in s["mcp_tools"]
    assert "prepare_research_workflow" in s["mcp_tools"]
    assert "synchronize_ebm_system" in s["mcp_tools"]


def test_agent_sources_are_live_searchable_documents() -> None:
    index = SafeKnowledgeIndex(ROOT, repository="owner/repo", git_ref="main")
    fetched = index.fetch(".claude/agents/dieu-phoi-lam-sang.md")
    assert fetched["id"] == ".claude/agents/dieu-phoi-lam-sang.md"
    assert "Cần bác sĩ kiểm chứng" in fetched["text"]


def test_yaml_knowledge_pack_with_pii_is_blocked(tmp_path: Path) -> None:
    """Lớp PII thứ cấp phải áp cho cả .yaml (knowledge-packs), không chỉ .md."""
    kp = tmp_path / "knowledge-packs" / "sub"
    kp.mkdir(parents=True)
    (kp / "pack.yaml").write_text("title: x\nnote: 'CCCD 012345678901'\n", encoding="utf-8")
    assert _index(tmp_path).search("")["results"] == []


def test_main_refuses_non_localhost_bind_without_token(monkeypatch) -> None:
    """Fail-closed: bind ra ngoài localhost mà không có EBM_MCP_TOKEN → từ chối."""
    import app.chatgpt_app.server as srv

    calls = {"run": 0}
    monkeypatch.setattr(srv.mcp, "run", lambda *a, **k: calls.__setitem__("run", calls["run"] + 1))
    monkeypatch.setenv("EBM_MCP_HOST", "0.0.0.0")
    monkeypatch.delenv("EBM_MCP_TOKEN", raising=False)
    with pytest.raises(SystemExit):
        srv.main()
    assert calls["run"] == 0
    monkeypatch.setenv("EBM_MCP_TOKEN", "secret")
    srv.main()
    assert calls["run"] == 1
    monkeypatch.setenv("EBM_MCP_HOST", "127.0.0.1")
    monkeypatch.delenv("EBM_MCP_TOKEN", raising=False)
    srv.main()
    assert calls["run"] == 2


def test_tool_lookup_errors_stay_inside_disclaimer_envelope() -> None:
    """Hồi quy audit MCP 2026-07-20: trước đây fetch/get_ebm_agent_instructions/
    prepare_*_workflow ném KeyError/ValueError THẲNG ra ngoài _result(), đi vòng
    qua lớp gắn disclaimer/PII của app (dispatcher chung của thư viện mcp bắt
    exception ở tầng khác). Nay mọi lỗi tra cứu phải đi qua CÙNG _result() có
    disclaimer, phòng khi một raise tương lai vô tình chèn nội dung động."""
    import app.chatgpt_app.server as srv

    result = srv.fetch(id="does/not/exist.md")
    assert result.structuredContent["status"] == "error"
    assert "Cần bác sĩ kiểm chứng" in result.structuredContent["disclaimer"]

    result = srv.get_ebm_agent_instructions(agent_id="khong-ton-tai")
    assert result.structuredContent["status"] == "error"
    assert "Cần bác sĩ kiểm chứng" in result.structuredContent["disclaimer"]


def test_main_supports_stdio_for_tunnel_supervision(monkeypatch) -> None:
    """Tunnel-client sở hữu cả vòng đời MCP, không cần server HTTP rời."""
    import app.chatgpt_app.server as srv

    calls: list[str] = []
    monkeypatch.setattr(srv.mcp, "run", lambda *a, **k: calls.append(k["transport"]))
    monkeypatch.setenv("EBM_MCP_TRANSPORT", "stdio")
    monkeypatch.setenv("EBM_MCP_HOST", "0.0.0.0")
    monkeypatch.delenv("EBM_MCP_TOKEN", raising=False)
    srv.main()
    assert calls == ["stdio"]
