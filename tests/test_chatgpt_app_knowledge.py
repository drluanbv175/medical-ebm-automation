"""Kiểm tra corpus ChatGPT App luôn fail-closed và đúng schema MCP."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from app.chatgpt_app.knowledge import SafeKnowledgeIndex, json_text
from app.chatgpt_app.server import _local_git_ref, mcp


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

    assert set(tools) == {"search", "fetch", "get_system_status"}
    assert set(tools["search"].inputSchema["properties"]) == {"query"}
    assert tools["search"].inputSchema["required"] == ["query"]
    assert set(tools["fetch"].inputSchema["properties"]) == {"id"}
    assert tools["fetch"].inputSchema["required"] == ["id"]
    for tool in tools.values():
        assert tool.annotations is not None
        assert tool.annotations.readOnlyHint is True
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
    assert s["mode"] == "read_only_review"
    assert s["writes_enabled"] is False
    assert s["pii_allowed"] is False
    assert s["clinical_release"] == "blocked"
    assert set(s["mcp_tools"]) == {"search", "fetch", "get_system_status"}


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
