"""MCP server điều phối có quản trị để kết nối EBM Copilot với ChatGPT."""

from __future__ import annotations

import functools
import os
import re
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from mcp.types import CallToolResult, TextContent, ToolAnnotations

from app.chatgpt_app.agents import SafeAgentCatalog
from app.chatgpt_app.knowledge import DISCLAIMER, SafeKnowledgeIndex, json_text

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
    candidate = head[len(prefix) :] if head.startswith(prefix) else ""
    return candidate if re.fullmatch(r"[A-Za-z0-9._/-]+", candidate) else "main"


INDEX = SafeKnowledgeIndex(
    ROOT,
    repository=os.getenv("EBM_GITHUB_REPOSITORY", "drluanbv175/medical-ebm-automation"),
    git_ref=os.getenv("EBM_GITHUB_REF") or _local_git_ref(ROOT),
)
AGENTS = SafeAgentCatalog(ROOT)

mcp = FastMCP(
    "EBM Copilot",
    instructions=(
        "Governed EBM orchestration source. Use prepare_clinical_workflow for clinical cases "
        "and prepare_research_workflow for research topics, then load every named specialist "
        "with get_ebm_agent_instructions. Never request or store PII. Never auto-approve Gate A/B "
        "or G2/G4/G8/G9. Always run tham-dinh-dau-ra last and retain: Cần bác sĩ kiểm chứng."
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

CONTROLLED_WRITE = ToolAnnotations(
    readOnlyHint=False,
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


def _safe(fn):
    """Bọc lỗi tra cứu (không tìm thấy/không cho phép/tham số sai) qua _result()
    thay vì để lộ ra ngoài như exception thô.

    Phòng thủ theo chiều sâu (audit MCP 2026-07-20): dispatcher chung của thư
    viện mcp bắt mọi exception KHÔNG qua _result()/DISCLAIMER — hiện tại mọi
    raise trong app đều dùng chuỗi hằng cố định nên chưa rò nội dung động, nhưng
    một thay đổi tương lai (vd. except re-raise lỗi filesystem gốc) sẽ tự động
    thoát khỏi lớp gắn disclaimer nếu không đi qua điểm bọc chung này.
    """

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except (KeyError, PermissionError, ValueError) as exc:
            return _result({"status": "error", "reason": str(exc), "disclaimer": DISCLAIMER})

    return wrapper


@mcp.tool(
    name="search",
    title="Tìm tri thức EBM",
    description=(
        "Use this when you need to find safe, review-only EBM system documents by a text query. "
        "Note: agent doctrine files are also indexed here AND served by get_ebm_agent_instructions/"
        "prepare_*_workflow — check already_included_agent_ids in a prior workflow response before "
        "fetching an agent .md you may already have."
    ),
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
@_safe
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


@mcp.tool(
    name="list_ebm_agents",
    title="Danh mục agent EBM",
    description="Use this when you need to discover all governed clinical or research agents available in EBM Copilot.",
    annotations=READ_ONLY,
)
def list_ebm_agents(domain: str = "all") -> CallToolResult:
    """Liệt kê agent; domain nhận all/clinical/research."""
    return _result(AGENTS.list_payload(domain))


@mcp.tool(
    name="get_ebm_agent_instructions",
    title="Nạp agent EBM chuyên trách",
    description=(
        "Use this before performing a workflow step named by an EBM orchestrator; "
        "load the exact governed instructions for one agent ID."
    ),
    annotations=READ_ONLY,
)
@_safe
def get_ebm_agent_instructions(agent_id: str) -> CallToolResult:
    """Nạp role chuyên trách từ nguồn Claude chính."""
    return _result(AGENTS.get_payload(agent_id))


@mcp.tool(
    name="prepare_clinical_workflow",
    title="Điều phối ca lâm sàng EBM",
    description=(
        "Use this first for any patient case, diagnosis, treatment, medication, test "
        "interpretation, prevention, or follow-up request. It blocks PII and enforces "
        "red-flag screening plus Gate A/B."
    ),
    annotations=READ_ONLY,
)
@_safe
def prepare_clinical_workflow(case_summary: str) -> CallToolResult:
    """Dựng gói nhạc trưởng lâm sàng, không áp dụng điều trị."""
    return _result(AGENTS.workflow_payload("clinical", case_summary))


@mcp.tool(
    name="prepare_research_workflow",
    title="Điều phối nghiên cứu y khoa",
    description=(
        "Use this first for any medical research topic, protocol, sample size, analysis, "
        "manuscript, or evidence-synthesis request. It enforces G2/G4/data/G8/G9 gates."
    ),
    annotations=READ_ONLY,
)
@_safe
def prepare_research_workflow(research_topic: str) -> CallToolResult:
    """Dựng gói nhạc trưởng nghiên cứu G0–G9, không tự duyệt cổng."""
    return _result(AGENTS.workflow_payload("research", research_topic))


@mcp.tool(
    name="get_sync_status",
    title="Kiểm tra đồng bộ EBM",
    description=(
        "Use this when you need the live Claude-to-Codex agent mirror and knowledge "
        "reload status without changing files."
    ),
    annotations=READ_ONLY,
)
def get_sync_status() -> CallToolResult:
    """Đọc trạng thái đồng bộ agent và corpus."""
    return _result(AGENTS.sync_status())


@mcp.tool(
    name="synchronize_ebm_system",
    title="Đồng bộ hệ thống agent EBM",
    description=(
        "Use this only after the physician explicitly asks to synchronize. Pass the exact "
        "confirmation returned by the tool; it regenerates Claude-to-Codex mirrors AND may "
        "write directly to the source .claude/agents/*.md files (guardrail block insertion, "
        "additive only), but never pulls or pushes GitHub."
    ),
    annotations=CONTROLLED_WRITE,
)
@_safe
def synchronize_ebm_system(confirmation: str = "") -> CallToolResult:
    """Chạy chuỗi đồng bộ allowlist, cần xác nhận tường minh."""
    return _result(AGENTS.synchronize(confirmation))


def main() -> None:
    """Chạy Streamable HTTP hoặc stdio do tunnel-client quản lý."""
    transport = os.getenv("EBM_MCP_TRANSPORT", "streamable-http")
    if transport == "stdio":
        mcp.run(transport="stdio")
        return
    if transport != "streamable-http":
        raise SystemExit(f"[chatgpt_app] Transport không hỗ trợ: {transport!r}")
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
