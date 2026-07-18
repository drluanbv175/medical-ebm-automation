"""MCP server chỉ đọc để kết nối EBM Copilot với ứng dụng ChatGPT."""
from __future__ import annotations

import os
import re
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from mcp.types import CallToolResult, TextContent, ToolAnnotations

from app.chatgpt_app.knowledge import SafeKnowledgeIndex, json_text

ROOT = Path(__file__).resolve().parents[2]


def _local_git_ref(root: Path) -> str:
    """Phát hiện nhánh local để URL GitHub không trỏ nhầm nhánh.

    Hosting production nên đặt `EBM_GITHUB_REF` tường minh; fallback này chỉ
    phục vụ chạy local và không gọi subprocess.
    """
    try:
        head = (root / ".git/HEAD").read_text(encoding="utf-8").strip()
    except OSError:
        return "main"
    prefix = "ref: refs/heads/"
    candidate = head[len(prefix):] if head.startswith(prefix) else ""
    return candidate if re.fullmatch(r"[A-Za-z0-9._/-]+", candidate) else "main"


INDEX = SafeKnowledgeIndex(
    ROOT,
    repository=os.getenv("EBM_GITHUB_REPOSITORY", "drluanbv175/medical-ebm-automation"),
    git_ref=os.getenv("EBM_GITHUB_REF") or _local_git_ref(ROOT),
)

mcp = FastMCP(
    "EBM Copilot",
    instructions=(
        "Read-only EBM review source. Search before fetch. Never request or store PII. "
        "Never present content as an automatically approved clinical recommendation. "
        "Always retain the disclaimer: Cần bác sĩ kiểm chứng."
    ),
    host=os.getenv("EBM_MCP_HOST", "127.0.0.1"),
    port=int(os.getenv("EBM_MCP_PORT", "2091")),
    streamable_http_path="/mcp",
)

READ_ONLY = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False,
)


def _result(payload: dict[str, object]) -> CallToolResult:
    """Tạo response vừa có structuredContent vừa tương thích connector cũ."""
    return CallToolResult(
        structuredContent=payload,
        content=[TextContent(type="text", text=json_text(payload))],
    )


@mcp.tool(
    name="search",
    title="Tìm tri thức EBM",
    description="Use this when you need to find safe, review-only EBM system documents by a text query.",
    annotations=READ_ONLY,
)
def search(query: str) -> CallToolResult:
    """Tìm trong corpus đã vượt chính sách export an toàn."""
    return _result(INDEX.search(query))


@mcp.tool(
    name="fetch",
    title="Đọc tài liệu EBM",
    description="Use this when you need the full text of one document ID returned by search.",
    annotations=READ_ONLY,
)
def fetch(id: str) -> CallToolResult:
    """Đọc toàn văn một tài liệu an toàn theo ID từ search."""
    return _result(INDEX.fetch(id))


@mcp.tool(
    name="get_system_status",
    title="Trạng thái EBM Copilot",
    description="Use this when you need the read-only safety, export, and corpus status of EBM Copilot.",
    annotations=READ_ONLY,
)
def get_system_status() -> CallToolResult:
    """Trả snapshot trạng thái, không tạo bảng hay thay đổi feature flag."""
    return _result(INDEX.system_status())


def main() -> None:
    """Chạy transport Streamable HTTP tại `/mcp`."""
    # Fail-closed (vá 2026-07-18, audit vòng 2): connector đọc kho tri thức y khoa.
    # Nếu bind RA NGOÀI localhost mà KHÔNG đặt token bí mật `EBM_MCP_TOKEN` → TỪ CHỐI
    # khởi động, buộc người vận hành chủ ý cấu hình xác thực trước khi phơi ra mạng
    # (tránh phơi công khai không xác thực; docs gợi ý ngrok nên rủi ro là thật).
    host = os.getenv("EBM_MCP_HOST", "127.0.0.1")
    if host not in {"127.0.0.1", "localhost", "::1"} and not os.getenv("EBM_MCP_TOKEN"):
        raise SystemExit(
            f"[chatgpt_app] TỪ CHỐI bind host={host!r} khi chưa đặt EBM_MCP_TOKEN. "
            "Đặt một token bí mật (và đặt sau proxy/xác thực) trước khi phơi MCP ra "
            "ngoài localhost — fail-closed để không phơi kho tri thức công khai."
        )
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
