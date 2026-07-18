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
