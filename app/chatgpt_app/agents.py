"""Cầu nối an toàn từ đội agent EBM sang ChatGPT App.

Tệp Markdown trong ``.claude/agents`` là nguồn biên tập chính. Lớp này chỉ
phục vụ những tệp đã vượt chính sách export, chặn PII và không tự phê duyệt
bất kỳ cổng lâm sàng/nghiên cứu nào.
"""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from app.chatgpt_app.knowledge import _matches_sensitive_id
from app.core.export_policy import classify_export_file
from app.core.policy_engine import contains_pii_text

DISCLAIMER = "Cần bác sĩ kiểm chứng. Không dùng đầu ra này để tự động áp dụng cho người bệnh."
SYNC_CONFIRMATION = "BAC_SI_DONG_Y_DONG_BO"
MAX_AGENT_BYTES = 256_000
AGENT_ID = re.compile(r"[a-z0-9][a-z0-9-]{1,80}")


@dataclass(frozen=True)
class AgentDocument:
    """Một agent đã vượt cổng export và PII."""

    agent_id: str
    title: str
    text: str
    path: Path


class SafeAgentCatalog:
    """Danh mục agent fail-closed dùng cho ChatGPT."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root.resolve()
        self.agent_dir = self.project_root / ".claude/agents"

    def _load(self, path: Path) -> AgentDocument | None:
        try:
            resolved = path.resolve(strict=True)
            resolved.relative_to(self.agent_dir.resolve())
            if resolved.name.startswith("_") or resolved.stat().st_size > MAX_AGENT_BYTES:
                return None
            agent_id = resolved.stem
            if not AGENT_ID.fullmatch(agent_id):
                return None
            decision = classify_export_file(resolved)
            if not decision.allowed:
                return None
            text = resolved.read_text(encoding="utf-8", errors="strict")
            # Agent nguồn thường NÊU TÊN các trường PII (CCCD, họ tên...) để
            # hướng dẫn chặn chúng; đó không phải bản ghi người bệnh. Chỉ chặn
            # khi có một định danh cụ thể đi kèm.
            # QUÉT TOÀN VĂN + NFD-safe (vá audit MCP 2026-07-20): trước đây chỉ
            # dựa vào classify_export_file() (giới hạn 200KB đầu) + regex chưa
            # chuẩn hóa Unicode — agent .md dài 200–256KB hoặc chứa PII dạng NFD
            # lọt cả hai lớp, khác hẳn fetch()/search() (đã quét toàn văn từ
            # 2026-07-18). Đồng bộ 2 đường lại cho cùng một mức bảo vệ.
            if contains_pii_text(text) or _matches_sensitive_id(text):
                return None
        except (OSError, UnicodeError, ValueError):
            return None
        title = agent_id
        for line in text.splitlines()[:50]:
            if line.startswith("# "):
                title = line[2:].strip()[:160]
                break
        return AgentDocument(agent_id=agent_id, title=title, text=text, path=resolved)

    def agents(self) -> list[AgentDocument]:
        """Đọc lại danh mục mỗi lần gọi để nhận thay đổi OneDrive ngay."""
        if not self.agent_dir.is_dir():
            return []
        return [doc for path in sorted(self.agent_dir.glob("*.md")) if (doc := self._load(path))]

    def list_payload(self, domain: str = "all") -> dict[str, object]:
        """Liệt kê agent theo nhóm chính, không trả nội dung dài."""
        clinical_ids = self._clinical_ids()
        rows = []
        for doc in self.agents():
            agent_domain = "clinical" if doc.agent_id in clinical_ids else "research"
            if domain not in {"all", agent_domain}:
                continue
            rows.append({"id": doc.agent_id, "title": doc.title, "domain": agent_domain})
        return {
            "agents": rows,
            "count": len(rows),
            "source_of_truth": ".claude/agents/*.md",
            "live_reload": True,
            "disclaimer": DISCLAIMER,
        }

    def get_payload(self, agent_id: str) -> dict[str, object]:
        """Trả chỉ dẫn của đúng một agent đã allowlist."""
        if not AGENT_ID.fullmatch(agent_id):
            raise KeyError("agent_not_found")
        found = next((doc for doc in self.agents() if doc.agent_id == agent_id), None)
        if found is None:
            raise KeyError("agent_not_found")
        return {
            "agent_id": found.agent_id,
            "title": found.title,
            "instructions": found.text,
            "execution_contract": {
                "mode": "proposal_only",
                "must_call_guardrail_last": True,
                "guardrail_agent": "tham-dinh-dau-ra",
                "pii_allowed": False,
                "automatic_gate_approval": False,
            },
            "disclaimer": DISCLAIMER,
        }

    def workflow_payload(self, kind: str, request: str) -> dict[str, object]:
        """Dựng gói nhạc trưởng; ChatGPT dùng gói này để chạy tuần tự các bước."""
        clean_request = request.strip()
        if not clean_request:
            raise ValueError("request_required")
        if len(clean_request) > 20_000:
            raise ValueError("request_too_large")
        if contains_pii_text(clean_request) or _matches_sensitive_id(clean_request):
            return {
                "status": "blocked",
                "reason": "possible_pii_detected",
                "next_step": (
                    "Khử định danh trước khi gửi lại; không nhập tên, CCCD, BHYT, số điện thoại, email hoặc địa chỉ."
                ),
                "disclaimer": DISCLAIMER,
            }
        if kind == "clinical":
            orchestrator = "dieu-phoi-lam-sang"
            gates = ["GATE_A_PHYSICIAN_APPLICATION", "GATE_B_LEDGER_WRITE"]
            first_agent = "sang-loc-co-do"
        elif kind == "research":
            orchestrator = "dieu-phoi-nghien-cuu"
            gates = ["G2_IRB", "G4_SAP_LOCK", "REAL_DATA", "G8_INDEPENDENT_REVIEW", "G9_PI_INTEGRITY"]
            first_agent = "cau-hoi-nghien-cuu"
        else:
            raise ValueError("unsupported_workflow_kind")
        conductor = self.get_payload(orchestrator)
        guardrail = self.get_payload("tham-dinh-dau-ra")
        return {
            "status": "ready_to_orchestrate",
            "workflow_kind": kind,
            "request": clean_request,
            "entry_agent": orchestrator,
            "first_safety_or_method_agent": first_agent,
            "hard_gates": gates,
            "orchestrator_instructions": conductor["instructions"],
            "final_guardrail_instructions": guardrail["instructions"],
            "agent_loading": (
                "Call get_ebm_agent_instructions for each specialist named by the "
                "orchestrator before performing that step."
            ),
            "release_rule": "Never claim applied/approved/released while any hard gate is pending.",
            "disclaimer": DISCLAIMER,
        }

    def sync_status(self) -> dict[str, object]:
        """Đọc trạng thái mirror Claude↔Codex mà không sửa tệp."""
        source_ids = {doc.agent_id for doc in self.agents()}
        root = self.project_root.parent
        mirrors: dict[str, dict[str, object]] = {}
        for relative in (".Codex/agents", ".codex/agents"):
            folder = root / relative
            ids = {path.stem for path in folder.glob("*.toml")} if folder.is_dir() else set()
            mirrors[relative] = {
                "count": len(ids),
                "missing": sorted(source_ids - ids),
                "extra": sorted(ids - source_ids),
            }
        return {
            "source_count": len(source_ids),
            "mirrors": mirrors,
            "knowledge_live_reload": True,
            "github_auto_push": False,
            "github_note": (
                "Git push remains an explicit operator action to avoid publishing unintended or sensitive changes."
            ),
            "disclaimer": DISCLAIMER,
        }

    def synchronize(self, confirmation: str) -> dict[str, object]:
        """Chạy chuỗi script allowlist; không git pull/push.

        Bước đầu (``enforce_agent_guardrails.py``) có thể GHI TRỰC TIẾP lên
        chính file nguồn biên tập ``.claude/agents/*.md`` (chèn khối guardrail
        nếu thiếu marker), không chỉ tái sinh mirror ``.Codex``/``.codex`` như
        tên hàm/mô tả tool gợi ý — ghi rõ ở đây để không đánh giá thấp phạm vi
        thay đổi khi bác sĩ xác nhận đồng bộ.
        """
        if confirmation != SYNC_CONFIRMATION:
            return {
                "status": "confirmation_required",
                "required_confirmation": SYNC_CONFIRMATION,
                "warning": "Only call after the physician explicitly asks to synchronize agent mirrors.",
            }
        root = self.project_root.parent
        commands = (
            ("enforce", root / "tools/enforce_agent_guardrails.py", ()),
            ("sync", root / "tools/sync_agents_to_codex.py", ()),
            ("check", root / "tools/sync_agents_to_codex.py", ("--check",)),
            ("health", root / "tools/check_claude_codex_sync_health.py", ()),
        )
        results: list[dict[str, object]] = []
        python = Path.home() / ".ebm-venv/bin/python"
        if not python.is_file():
            python = Path("python3")
        for label, script, extra in commands:
            if not script.is_file():
                return {"status": "blocked", "reason": f"missing_sync_script:{script.name}", "results": results}
            completed = subprocess.run(
                [str(python), str(script), *extra],
                cwd=root,
                capture_output=True,
                text=True,
                timeout=180,
                check=False,
                env={"PATH": "/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin"},
            )
            output_tail = (completed.stdout + completed.stderr)[-2_000:]
            # Phòng thủ theo chiều sâu (audit MCP 2026-07-20): đây là nhánh duy nhất
            # trong file trả "nội dung" (log subprocess) mà không qua cùng cổng PII
            # như search/fetch/get_ebm_agent_instructions. 3 script hiện tại chỉ in
            # tên file/số đếm/lỗi TOML, không PII — nhưng nếu một script tương lai
            # vô tình in trích đoạn nội dung, cổng này chặn trước khi rời tiến trình.
            if contains_pii_text(output_tail) or _matches_sensitive_id(output_tail):
                output_tail = "[ẩn: nghi ngờ chứa PII, xem log cục bộ thay vì qua ChatGPT]"
            results.append(
                {
                    "step": label,
                    "returncode": completed.returncode,
                    "output_tail": output_tail,
                }
            )
            if completed.returncode != 0:
                return {"status": "blocked", "reason": f"sync_step_failed:{label}", "results": results}
        return {"status": "synchronized", "results": results, "sync_status": self.sync_status()}

    @staticmethod
    def _clinical_ids() -> set[str]:
        """Danh sách role lâm sàng theo bản đồ đội đã chốt."""
        return {
            "dieu-phoi-lam-sang",
            "sang-loc-co-do",
            "khai-thac-benh-su-kham",
            "pico-lam-sang",
            "tra-cuu-chung-cu",
            "dien-giai-can-lam-sang",
            "chan-doan-xac-suat",
            "thang-diem-nguy-co",
            "tham-dinh-grade-nnt",
            "ket-qua-hoc-tap",
            "ke-don-an-toan",
            "quyet-dinh-chung",
            "loi-dan-tuan-thu",
            "theo-doi-benh-man",
            "du-phong-tam-soat",
            "dau-man-tinh",
            "cham-soc-giam-nhe",
            "tram-cam-lo-au",
            "quan-ly-khang-dong",
            "tham-dinh-do-chinh-xac-chan-doan",
            "cap-nhat-guideline",
        }


def stable_json(payload: dict[str, object]) -> str:
    """JSON ổn định cho log/test."""
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
