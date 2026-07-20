"""Chỉ mục tài liệu an toàn dùng bởi ChatGPT App.

Lớp này cố ý chỉ đọc các loại tài liệu đã cho phép và chạy lại bộ phân loại
export trước mỗi lần phục vụ. Không đọc database, dataset thô, `.env` hay hồ
sơ bệnh nhân.
"""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import quote

from app.core.export_policy import classify_export_file, validate_project_manifest
from app.core.policy_engine import _collapse_digit_separators, contains_bare_id_number, contains_pii_text

DISCLAIMER = "Cần bác sĩ kiểm chứng. Không dùng đầu ra này để tự động áp dụng cho người bệnh."
DEFAULT_PATTERNS = (
    "README.md",
    "ROADMAP_EBM_CLINICAL.md",
    "docs/**/*.md",
    "knowledge-packs/**/*.yaml",
    "exports/chatgpt_project/README.md",
    ".claude/agents/*.md",
)
MAX_DOCUMENT_BYTES = 512_000
SENSITIVE_ID_PATTERN = re.compile(
    r"(?i)\b(?:cccd|cmnd|căn\s*cước|mã\s*(?:người\s*)?bệnh|patient\s*id)\s*[:#-]?\s*[A-Z0-9-]{6,}\b"
)


def _matches_sensitive_id(text: str) -> bool:
    """Chuẩn hóa NFC + gộp dấu cách/chấm/gạch giữa số trước khi so khớp
    SENSITIVE_ID_PATTERN — literal trong pattern là NFC-precomposed nên văn bản
    NFD (chữ nền + dấu rời) khớp trượt hoàn toàn nếu so trực tiếp trên text thô;
    CCCD viết tách nhóm ('012 345 678 901') cũng lọt nếu không gộp số trước."""
    normalized = unicodedata.normalize("NFC", text or "")
    return bool(SENSITIVE_ID_PATTERN.search(_collapse_digit_separators(normalized)))


@dataclass(frozen=True)
class KnowledgeDocument:
    """Một tài liệu đã vượt cổng export an toàn."""

    id: str
    title: str
    url: str
    text: str
    sha256: str


def _title_for(path: Path, text: str) -> str:
    """Lấy tiêu đề Markdown đầu tiên, nếu không có thì dùng tên tệp."""
    for line in text.splitlines()[:40]:
        candidate = line.strip().lstrip("#").strip()
        if line.lstrip().startswith("#") and candidate:
            return candidate[:200]
    return path.stem.replace("_", " ").replace("-", " ").strip()[:200]


def _tokens(value: str) -> set[str]:
    """Tách token Unicode đơn giản, đủ cho tìm kiếm Việt/Anh cục bộ."""
    return set(re.findall(r"[^\W_]{2,}", value.casefold(), flags=re.UNICODE))


class SafeKnowledgeIndex:
    """Chỉ mục read-only fail-closed trên tập tài liệu được allowlist."""

    def __init__(
        self,
        root: Path,
        *,
        repository: str = "drluanbv175/medical-ebm-automation",
        git_ref: str = "master",
        patterns: Iterable[str] = DEFAULT_PATTERNS,
    ) -> None:
        self.root = root.resolve()
        self.repository = repository
        self.git_ref = git_ref
        self.patterns = tuple(patterns)

    def _candidate_paths(self) -> list[Path]:
        """Liệt kê ứng viên duy nhất, không đi theo đường dẫn ngoài repository."""
        candidates: set[Path] = set()
        for pattern in self.patterns:
            candidates.update(path for path in self.root.glob(pattern) if path.is_file())
        return sorted(candidates)

    def _load(self, path: Path) -> KnowledgeDocument | None:
        """Đọc một tài liệu sau khi kiểm policy; lỗi nào cũng đóng cổng."""
        try:
            resolved = path.resolve(strict=True)
            resolved.relative_to(self.root)
            if resolved.stat().st_size > MAX_DOCUMENT_BYTES:
                return None
            decision = classify_export_file(resolved)
            if not decision.allowed or not decision.sha256:
                return None
            text = resolved.read_text(encoding="utf-8", errors="strict")
            # Lớp bảo vệ bổ sung cho định danh y tế/CCCD mà policy chung có thể
            # chưa nhận ra; connector y khoa cần đóng cổng chặt hơn export docs.
            # QUÉT TOÀN VĂN (vá 2026-07-18, audit vòng 2): trước đây chỉ quét
            # text[:200_000] nhưng fetch() phục vụ TOÀN BỘ tới MAX_DOCUMENT_BYTES
            # (512KB) → PII ở phần đuôi (200k–512k) lọt qua cổng mà vẫn bị trả về.
            if contains_pii_text(text) or _matches_sensitive_id(text):
                return None
        except (OSError, UnicodeError, ValueError):
            return None
        relative = resolved.relative_to(self.root).as_posix()
        url_path = quote(relative, safe="/")
        return KnowledgeDocument(
            id=relative,
            title=_title_for(resolved, text),
            url=f"https://github.com/{self.repository}/blob/{self.git_ref}/{url_path}",
            text=text,
            sha256=decision.sha256,
        )

    def documents(self) -> list[KnowledgeDocument]:
        """Trả danh sách tài liệu an toàn hiện có."""
        return [doc for path in self._candidate_paths() if (doc := self._load(path))]

    def search(self, query: str, *, limit: int = 10) -> dict[str, object]:
        """Tìm tài liệu, trả đúng payload chuẩn `search` của MCP."""
        # THÊM 2026-07-21 (vòng lặp kiểm tra-hoàn thiện vòng 3, phát hiện HIGH):
        # search(query) trước đây là đường THỨ HAI bỏ sót hoàn toàn cổng PII —
        # workflow_payload() (agents.py) là nơi DUY NHẤT gọi contains_bare_id_
        # number(), nhưng mô tả tool `search` không cấm PII và có thể được gọi
        # trực tiếp với câu tự do của bác sĩ thay vì qua prepare_*_workflow.
        if (
            contains_pii_text(query)
            or _matches_sensitive_id(query)
            or contains_bare_id_number(query)
        ):
            return {
                "status": "blocked",
                "reason": "possible_pii_detected",
                "next_step": (
                    "Khử định danh trước khi gửi lại; không nhập tên, CCCD, BHYT, số điện thoại, email hoặc địa chỉ."
                ),
                "disclaimer": DISCLAIMER,
            }
        query_tokens = _tokens(query)
        ranked: list[tuple[int, KnowledgeDocument]] = []
        for doc in self.documents():
            title_hits = len(query_tokens & _tokens(doc.title))
            body_hits = len(query_tokens & _tokens(doc.text[:100_000]))
            score = title_hits * 5 + body_hits
            if not query_tokens or score:
                ranked.append((score, doc))
        ranked.sort(key=lambda pair: (-pair[0], pair[1].title.casefold(), pair[1].id))
        return {
            "results": [
                {"id": doc.id, "title": doc.title, "url": doc.url}
                for _, doc in ranked[: max(1, min(limit, 20))]
            ]
        }

    def fetch(self, document_id: str) -> dict[str, object]:
        """Lấy một tài liệu theo ID tương đối; chặn path traversal và tệp ngoài allowlist."""
        requested = (self.root / document_id).resolve()
        try:
            requested.relative_to(self.root)
        except ValueError as exc:
            raise KeyError("document_not_found") from exc
        allowed = {path.resolve() for path in self._candidate_paths()}
        if requested not in allowed:
            raise KeyError("document_not_found")
        doc = self._load(requested)
        if doc is None:
            raise PermissionError("document_blocked_by_export_policy")
        # Chèn disclaimer NGAY TRONG thân `text` (vá 2026-07-18, audit vòng 2):
        # trước đây disclaimer chỉ ở `metadata` — ChatGPT thường render field `text`
        # làm nội dung nên có thể trình bày nội dung y khoa mà KHÔNG hiển thị
        # disclaimer, vi phạm bất biến CLAUDE.md #5. Nay disclaimer luôn ở đầu nội dung.
        return {
            "id": doc.id,
            "title": doc.title,
            "text": f"⚠️ {DISCLAIMER}\n\n{doc.text}",
            "url": doc.url,
            "metadata": {
                "sha256": doc.sha256,
                "safety": "review_only_no_pii",
                "disclaimer": DISCLAIMER,
            },
        }

    def system_status(self) -> dict[str, object]:
        """Đọc trạng thái export hiện có mà không khởi tạo hay sửa database."""
        manifest_path = self.root / "exports/chatgpt_project/v7_manifest.json"
        manifest: dict[str, object] = {}
        manifest_valid = False
        blockers: list[str] = []
        warnings: list[str] = []
        if manifest_path.is_file():
            try:
                loaded = json.loads(manifest_path.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    manifest = loaded
                    validation = validate_project_manifest(manifest)
                    manifest_valid = validation.valid
                    blockers = list(validation.blockers)
                    warnings = list(validation.warnings)
            except (OSError, json.JSONDecodeError):
                blockers = ["manifest_unreadable"]
        docs = self.documents()
        return {
            "mode": "governed_orchestration_review",
            "mcp_tools": [
                "search", "fetch", "get_system_status", "list_ebm_agents",
                "get_ebm_agent_instructions", "prepare_clinical_workflow",
                "prepare_research_workflow", "get_sync_status", "synchronize_ebm_system",
            ],
            "safe_document_count": len(docs),
            "corpus_sha256": hashlib.sha256(
                "".join(sorted(doc.sha256 for doc in docs)).encode("utf-8")
            ).hexdigest(),
            "manifest_valid": manifest_valid,
            "manifest_blockers": blockers,
            "manifest_warnings": warnings,
            "clinical_release": "blocked",
            "writes_enabled": "agent_mirror_sync_only_with_explicit_confirmation",
            "pii_allowed": False,
            "disclaimer": DISCLAIMER,
        }


def json_text(payload: dict[str, object]) -> str:
    """Mã hóa ổn định cho MCP content text."""
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
