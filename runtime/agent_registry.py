"""
Agent Registry — liên kết agent source với offline runtime.

V4.1: Hai mode tường minh, fail-closed trong FULL_SCOPE_A.

  BUNDLE_RUNTIME_ONLY:
    Registry disabled. Không có agent source, không có hash claim.
    make_trace() bị cấm — không được tuyên bố agent-source hash binding
    khi không có thực thể agent nào được nạp.

  FULL_SCOPE_A:
    Yêu cầu .claude/agents/ và manifest phải tồn tại.
    Fail hard khi bất kỳ điều kiện nào sau đây không đạt:
      - manifest missing
      - agents dir missing
      - count < MINIMUM_AGENT_COUNT
      - required agents missing
      - bất kỳ agent hash None
      - bất kỳ agent hash mismatch với manifest
    make_trace() chỉ hoạt động trong FULL_SCOPE_A với hash thật.

Tuyên bố bắt buộc (chỉ dùng được trong FULL_SCOPE_A):
  Agent source referenced and hash-bound in offline simulation.
  Live Agent execution not verified.
"""

import csv
import dataclasses
import enum
import hashlib
import pathlib
from typing import Dict, List, Optional

BASE_DIR = pathlib.Path(__file__).parent.parent  # medical-ebm-automation/
# V4.3.2.1 (reproducibility): ưu tiên agent source VENDORED trong repo (để
# `git archive` tự-chứa); fallback về cây OneDrive-root khi chạy ngoài archive.
# CHỈ là path resolution — KHÔNG đổi logic nạp/verify (vẫn hash-verify theo manifest).
_IN_REPO_AGENTS_DIR = BASE_DIR / ".claude" / "agents"
_PARENT_AGENTS_DIR = BASE_DIR.parent / ".claude" / "agents"
AGENTS_DIR = _IN_REPO_AGENTS_DIR if _IN_REPO_AGENTS_DIR.exists() else _PARENT_AGENTS_DIR

# V4.2.1 (GAP-009): manifest hiệu lực được đưa VÀO repo/version control.
# Registry KHÔNG còn phụ thuộc manifest ở thư mục OneDrive ngoài repo.
IN_REPO_MANIFEST_PATH = BASE_DIR / "runtime" / "manifests" / "agent_source_manifest.csv"
SCOPE_A_MANIFEST_PATH = IN_REPO_MANIFEST_PATH  # tương thích tên cũ; trỏ manifest in-repo

# Self-check: SHA-256 của CHÍNH file manifest in-repo (chống sửa lén manifest).
# Cập nhật giá trị này khi tái sinh manifest có chủ đích (baseline đã khóa V4.2.1).
# Tái sinh 2026-07-05 (lần 2): nội dung theo-doi-benh-man.md cập nhật guideline
# THA/lipid (2017/2018/2019 → 2025 AHA/ACC + bản hiện hành) → hash trôi lại dù
# số agent (50) không đổi. BÀI HỌC: manifest phải tái sinh sau MỌI lần sửa NỘI
# DUNG agent, không chỉ khi số lượng đổi → chạy
# `scripts/regenerate_agent_manifest.py --write` rồi dán giá trị self-check mới
# vào đây MỖI LẦN sync agent .md đã sửa sang medical-ebm-automation/.claude/agents/.
MANIFEST_SELF_CHECK_SHA256 = (
    "a6c4c7416ed1fb1aa023014babf6d2bcdf18171f0d44bbf15ba1a47c1f9de370"
)

MINIMUM_AGENT_COUNT = 50
# V4.2.1 (GAP-001): hard-enforce đủ 4 agent trọng yếu (2 nhạc trưởng + guardrail
# chốt kiểm cuối + sổ cái). Thiếu bất kỳ agent nào → registry fail-closed.
REQUIRED_AGENTS = frozenset({
    "dieu-phoi-nghien-cuu",
    "dieu-phoi-lam-sang",
    "tham-dinh-dau-ra",
    "so-cai-ghi-nho",
})


class AgentManifestSelfCheckError(AssertionError):
    """Manifest in-repo bị sửa đổi: SHA-256 không khớp giá trị khóa baseline."""

_POLICY_DEPS_MAP: Dict[str, List[str]] = {
    "dieu-phoi-lam-sang":     ["GATE_A", "GATE_B", "PII_EGRESS", "G9"],
    "dieu-phoi-nghien-cuu":   ["G2", "G4", "G9", "GATE_B"],
    "tham-dinh-dau-ra":       ["PII_EGRESS", "AUTO_SUBMIT", "RAW_DATA_WRITE"],
    "dao-duc-dang-ky":        ["G2"],
    "thiet-ke-nghien-cuu":    ["G4"],
    "phan-tich-thong-ke":     ["G4", "G9"],
    "ke-don-an-toan":         ["GATE_A", "PII_EGRESS"],
    "so-cai-ghi-nho":         ["GATE_B"],
    "an-toan-nghien-cuu":     ["G2", "GATE_B"],
    "quan-ly-du-lieu":        ["G4", "G5", "PII_EGRESS", "RAW_DATA_WRITE"],
    "kiem-chung-trich-dan":   ["GATE_B"],
    "viet-ban-thao":          ["G9", "GATE_B"],
    "nop-bai-phan-hoi":       ["G9", "AUTO_SUBMIT"],
}
_DEFAULT_POLICY_DEPS = ["PII_EGRESS"]


class RegistryMode(enum.Enum):
    """Hai mode tường minh của AgentRegistry."""
    BUNDLE_RUNTIME_ONLY = "BUNDLE_RUNTIME_ONLY"
    FULL_SCOPE_A = "FULL_SCOPE_A"


def _compute_sha256(path: pathlib.Path) -> Optional[str]:
    """Tính SHA256 của file. Trả None nếu không tồn tại."""
    if not path.exists():
        return None
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


@dataclasses.dataclass
class AgentRegistryEntry:
    """Thông tin đăng ký của một agent trong phạm vi offline."""
    agent_id: str
    agent_path: str
    agent_source_hash: Optional[str]
    policy_dependencies: List[str]
    allowed_runtime: str
    source_file_exists: bool
    hash_verified: bool


class AgentRegistryDisabledError(RuntimeError):
    """Gọi make_trace() trong BUNDLE_RUNTIME_ONLY mode."""


class AgentRegistryIntegrityError(AssertionError):
    """Lỗi tính toàn vẹn trong FULL_SCOPE_A mode."""


class AgentRegistry:
    """
    Registry liên kết agent source với offline runtime.

    TUYÊN BỐ BẮT BUỘC (chỉ áp dụng khi mode=FULL_SCOPE_A):
      Agent source referenced and hash-bound in offline simulation.
      Live Agent execution not verified.
    """

    EXECUTION_STATEMENT = (
        "Agent source referenced and hash-bound in offline simulation. "
        "Live Agent execution not verified."
    )

    def __init__(self, mode: RegistryMode = RegistryMode.BUNDLE_RUNTIME_ONLY):
        self._mode = mode
        self._entries: Dict[str, AgentRegistryEntry] = {}
        self._manifest_sha256_map: Dict[str, str] = {}

        if mode == RegistryMode.BUNDLE_RUNTIME_ONLY:
            # Registry disabled — không nạp agents, không có hash claim.
            pass
        elif mode == RegistryMode.FULL_SCOPE_A:
            self._load_manifest_hashes_strict()
            self._load_from_agents_dir_strict()
            self._validate_full_scope_a()

    # ── BUNDLE_RUNTIME_ONLY: không làm gì thêm ────────────────────────────────

    # ── FULL_SCOPE_A: load và validate ────────────────────────────────────────

    def _load_manifest_hashes_strict(self) -> None:
        """Nạp SHA256 từ manifest in-repo; fail hard nếu thiếu hoặc self-check sai."""
        if not SCOPE_A_MANIFEST_PATH.exists():
            raise AgentRegistryIntegrityError(
                f"FULL_SCOPE_A mode: in-repo manifest required but missing: "
                f"{SCOPE_A_MANIFEST_PATH}"
            )
        # V4.2.1 (GAP-009): self-check hash của chính file manifest trước khi tin.
        manifest_bytes = SCOPE_A_MANIFEST_PATH.read_bytes()
        actual_self = hashlib.sha256(manifest_bytes).hexdigest()
        if actual_self != MANIFEST_SELF_CHECK_SHA256:
            raise AgentManifestSelfCheckError(
                "FULL_SCOPE_A mode: manifest self-check FAILED. "
                f"Expected {MANIFEST_SELF_CHECK_SHA256[:16]}…, got {actual_self[:16]}…. "
                "Manifest in-repo có thể đã bị sửa đổi — fail-closed."
            )
        with open(SCOPE_A_MANIFEST_PATH, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                path_key = row.get("path", "")
                sha = row.get("sha256", "")
                if path_key and sha and ".claude/agents/" in path_key:
                    agent_id = pathlib.Path(path_key).stem
                    self._manifest_sha256_map[agent_id] = sha

    def _load_from_agents_dir_strict(self) -> None:
        """Nạp registry từ .claude/agents/; fail hard nếu thư mục không tồn tại."""
        if not AGENTS_DIR.exists():
            raise AgentRegistryIntegrityError(
                f"FULL_SCOPE_A mode: agents dir required but missing: {AGENTS_DIR}"
            )
        for md_file in sorted(AGENTS_DIR.glob("*.md")):
            agent_id = md_file.stem
            if agent_id.startswith("_") or agent_id == "README":
                continue
            source_hash = _compute_sha256(md_file)
            manifest_hash = self._manifest_sha256_map.get(agent_id)
            hash_verified = (
                source_hash is not None
                and manifest_hash is not None
                and source_hash == manifest_hash
            )
            entry = AgentRegistryEntry(
                agent_id=agent_id,
                agent_path=str(md_file).replace(str(BASE_DIR.parent) + "/", ""),
                agent_source_hash=source_hash,
                policy_dependencies=_POLICY_DEPS_MAP.get(agent_id, _DEFAULT_POLICY_DEPS),
                allowed_runtime="MOCK_ONLY",
                source_file_exists=True,
                hash_verified=hash_verified,
            )
            self._entries[agent_id] = entry

    def _validate_full_scope_a(self) -> None:
        """Kiểm tra toàn vẹn: fail hard với thông điệp rõ ràng."""
        if self.count() < MINIMUM_AGENT_COUNT:
            raise AgentRegistryIntegrityError(
                f"FULL_SCOPE_A: expected >= {MINIMUM_AGENT_COUNT} agents, "
                f"found {self.count()}. Check .claude/agents/ completeness."
            )
        for required_id in REQUIRED_AGENTS:
            if required_id not in self._entries:
                raise AgentRegistryIntegrityError(
                    f"FULL_SCOPE_A: required agent missing: {required_id}"
                )
        for agent_id, entry in self._entries.items():
            if entry.agent_source_hash is None:
                raise AgentRegistryIntegrityError(
                    f"FULL_SCOPE_A: agent source hash is None: {agent_id}. "
                    "File may be unreadable."
                )
            if not entry.hash_verified:
                raise AgentRegistryIntegrityError(
                    f"FULL_SCOPE_A: agent hash mismatch: {agent_id}. "
                    f"Source hash {entry.agent_source_hash!r} does not match manifest."
                )

    # ── Public API ─────────────────────────────────────────────────────────────

    @property
    def mode(self) -> RegistryMode:
        return self._mode

    def get(self, agent_id: str) -> Optional[AgentRegistryEntry]:
        """Tra cứu entry theo agent_id (None nếu không tìm thấy hoặc BUNDLE mode)."""
        return self._entries.get(agent_id)

    def all_agents(self) -> List[AgentRegistryEntry]:
        return list(self._entries.values())

    def count(self) -> int:
        return len(self._entries)

    def verify_hash(self, agent_id: str) -> bool:
        """Xác minh SHA256 hiện tại của file khớp với lúc nạp (FULL_SCOPE_A only)."""
        if self._mode == RegistryMode.BUNDLE_RUNTIME_ONLY:
            return False
        entry = self.get(agent_id)
        if entry is None or not entry.source_file_exists:
            return False
        current_hash = _compute_sha256(AGENTS_DIR / f"{agent_id}.md")
        return current_hash == entry.agent_source_hash

    def make_trace(
        self,
        *,
        agent_id: str,
        fixture_id: str,
        policy_decision: str,
        state_transition: Optional[str] = None,
        approval_reference: Optional[str] = None,
        audit_event_id: Optional[str] = None,
    ) -> dict:
        """
        Tổng hợp trace đầy đủ cho một lần chạy offline (FULL_SCOPE_A only).

        BUNDLE_RUNTIME_ONLY: raise AgentRegistryDisabledError — không được dùng
        fixture-only trace để tuyên bố agent-source hash binding.

        Trace chứng minh chuỗi:
          agent_id → agent_source_hash → fixture_id → policy_decision
          → state_transition → approval_reference → audit_event_id
        """
        if self._mode == RegistryMode.BUNDLE_RUNTIME_ONLY:
            raise AgentRegistryDisabledError(
                "make_trace() requires FULL_SCOPE_A mode. "
                "BUNDLE_RUNTIME_ONLY does not support agent-source hash binding claims. "
                "To trace with real agent hashes, use AgentRegistry(mode=RegistryMode.FULL_SCOPE_A)."
            )
        entry = self.get(agent_id)
        return {
            "agent_id": agent_id,
            "agent_source_hash": entry.agent_source_hash if entry else None,
            "agent_found_in_registry": entry is not None,
            "agent_hash_verified": entry.hash_verified if entry else False,
            "fixture_id": fixture_id,
            "policy_decision": policy_decision,
            "state_transition": state_transition,
            "approval_reference": approval_reference,
            "audit_event_id": audit_event_id,
            "allowed_runtime": entry.allowed_runtime if entry else None,
            "live_execution_verified": False,
            "execution_statement": self.EXECUTION_STATEMENT,
            "registry_mode": self._mode.value,
        }


# ── Singleton helpers ──────────────────────────────────────────────────────────

_REGISTRY_BUNDLE: Optional[AgentRegistry] = None
_REGISTRY_FULL: Optional[AgentRegistry] = None


def get_registry(mode: RegistryMode = RegistryMode.BUNDLE_RUNTIME_ONLY) -> AgentRegistry:
    """Singleton per mode. BUNDLE_RUNTIME_ONLY mặc định (safe)."""
    global _REGISTRY_BUNDLE, _REGISTRY_FULL
    if mode == RegistryMode.BUNDLE_RUNTIME_ONLY:
        if _REGISTRY_BUNDLE is None:
            _REGISTRY_BUNDLE = AgentRegistry(mode=RegistryMode.BUNDLE_RUNTIME_ONLY)
        return _REGISTRY_BUNDLE
    else:
        if _REGISTRY_FULL is None:
            _REGISTRY_FULL = AgentRegistry(mode=RegistryMode.FULL_SCOPE_A)
        return _REGISTRY_FULL


def reset_registry() -> None:
    """Xóa singleton cache — dùng trong tests."""
    global _REGISTRY_BUNDLE, _REGISTRY_FULL
    _REGISTRY_BUNDLE = None
    _REGISTRY_FULL = None


def from_entries_for_testing(
    entries: list[AgentRegistryEntry],
) -> AgentRegistry:
    """
    Tạo AgentRegistry giả từ danh sách entries — CHỈ DÙNG TRONG TESTS.

    Bypass disk I/O và manifest check để test có thể kiểm soát registry state
    mà không cần .claude/agents/ thật. Mode luôn là BUNDLE_RUNTIME_ONLY
    (fail-closed), không claim FULL_SCOPE_A.
    """
    registry = AgentRegistry.__new__(AgentRegistry)
    registry._mode = RegistryMode.BUNDLE_RUNTIME_ONLY
    registry._entries = {e.agent_id: e for e in entries}
    registry._manifest_sha256_map = {}
    return registry
