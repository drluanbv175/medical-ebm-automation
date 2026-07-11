"""Knowledge Pack Service — cầu nối YAML packs ↔ V7 pipeline ↔ Chronic Care OS.

Tải và expose tất cả knowledge packs từ knowledge-packs/ directory.
Enforces safety guardrails: draft_review_only, clinical_release_allowed: false.
KHÔNG bịa dữ liệu. KHÔNG expose pack chưa đủ files cho patient-facing output.

Security constraints:
  R1 — clinical_release_allowed: false  → không dùng cho quyết định kê đơn
  R2 — prescription_generation_allowed: false → không generate đơn thuốc
  R3 — patient_facing_output_allowed: false → không output cho bệnh nhân
  R4 — No PII in pack content
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)

# ── Đường dẫn mặc định ────────────────────────────────────────────────────────
_REPO_ROOT = Path(__file__).resolve().parents[2]
KNOWLEDGE_PACKS_DIR = _REPO_ROOT / "knowledge-packs"

# ── File schemas trong mỗi pack version ───────────────────────────────────────
REQUIRED_FILES = {"01_scope.yaml", "03_red_flags.yaml", "05_recommendations.yaml", "06_drug_safety_rules.yaml"}
OPTIONAL_FILES = {"02_monitoring.yaml", "04_scoring.yaml"}


# ── Dataclasses ───────────────────────────────────────────────────────────────

@dataclass
class PackScope:
    pack_id: str
    version: str
    status: str
    topic: str
    applies_to: List[str] = field(default_factory=list)
    does_not_apply_to: List[str] = field(default_factory=list)
    clinical_release_allowed: bool = False
    patient_facing_output_allowed: bool = False
    emr_write_allowed: bool = False
    prescription_generation_allowed: bool = False
    disclaimer: str = "DRAFT REVIEW-ONLY. Cần bác sĩ kiểm chứng trước khi áp dụng lâm sàng."


@dataclass
class RedFlag:
    red_flag_id: str
    label: str
    gate: str
    referral_level: str


@dataclass
class KnowledgePack:
    """Đại diện đầy đủ của một knowledge pack đã load từ YAML."""
    pack_id: str
    version: str
    pack_dir: Path
    scope: Optional[PackScope] = None
    red_flags: List[RedFlag] = field(default_factory=list)
    recommendations: Dict = field(default_factory=dict)
    drug_safety_rules: Dict = field(default_factory=dict)
    missing_files: List[str] = field(default_factory=list)
    load_errors: List[str] = field(default_factory=list)

    @property
    def is_complete(self) -> bool:
        """True nếu có đủ 4 files bắt buộc và không có load error."""
        return len(self.missing_files) == 0 and len(self.load_errors) == 0

    @property
    def is_safe_for_review(self) -> bool:
        """True nếu scope hợp lệ và status là draft_review_only."""
        return self.scope is not None and self.scope.status == "draft_review_only"


# ── Loader ────────────────────────────────────────────────────────────────────

def _load_yaml_safe(path: Path) -> Dict:
    """Load YAML file, trả dict rỗng nếu lỗi."""
    try:
        with path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data or {}
    except Exception as exc:
        logger.warning("Không load được %s: %s", path, exc)
        return {}


def _load_pack(pack_dir: Path, version_dir: str = "2026.1-draft") -> KnowledgePack:
    """Load một knowledge pack từ thư mục, trả KnowledgePack với trạng thái đầy đủ."""
    pack_id = pack_dir.name
    version_path = pack_dir / version_dir
    pack = KnowledgePack(pack_id=pack_id, version=version_dir, pack_dir=version_path)

    if not version_path.exists():
        pack.missing_files.append(f"{version_dir}/ (directory not found)")
        return pack

    # Kiểm tra files bắt buộc
    for fname in REQUIRED_FILES:
        if not (version_path / fname).exists():
            pack.missing_files.append(fname)

    # 01_scope.yaml
    scope_data = _load_yaml_safe(version_path / "01_scope.yaml")
    if scope_data:
        try:
            pack.scope = PackScope(
                pack_id=scope_data.get("pack_id", pack_id),
                version=scope_data.get("version", version_dir),
                status=scope_data.get("status", "unknown"),
                topic=scope_data.get("topic", ""),
                applies_to=scope_data.get("applies_to", []),
                does_not_apply_to=scope_data.get("does_not_apply_to", []),
                clinical_release_allowed=scope_data.get("clinical_release_allowed", False),
                patient_facing_output_allowed=scope_data.get("patient_facing_output_allowed", False),
                emr_write_allowed=scope_data.get("emr_write_allowed", False),
                prescription_generation_allowed=scope_data.get("prescription_generation_allowed", False),
                disclaimer=scope_data.get("disclaimer", PackScope.__dataclass_fields__["disclaimer"].default),
            )
        except Exception as exc:
            pack.load_errors.append(f"scope: {exc}")
    return pack


def _load_pack_full(pack_dir: Path, version_dir: str = "2026.1-draft") -> KnowledgePack:
    """Load pack đầy đủ bao gồm red_flags, recommendations, drug_safety_rules."""
    pack = _load_pack(pack_dir, version_dir)
    version_path = pack_dir / version_dir

    # 03_red_flags.yaml
    rf_data = _load_yaml_safe(version_path / "03_red_flags.yaml")
    for rf in rf_data.get("red_flags", []):
        try:
            pack.red_flags.append(RedFlag(
                red_flag_id=rf.get("red_flag_id", ""),
                label=rf.get("label", ""),
                gate=rf.get("gate", ""),
                referral_level=rf.get("referral_level", ""),
            ))
        except Exception as exc:
            pack.load_errors.append(f"red_flag: {exc}")

    # 05_recommendations.yaml
    rec_data = _load_yaml_safe(version_path / "05_recommendations.yaml")
    pack.recommendations = rec_data

    # 06_drug_safety_rules.yaml
    drug_data = _load_yaml_safe(version_path / "06_drug_safety_rules.yaml")
    pack.drug_safety_rules = drug_data

    return pack


# ── Service ───────────────────────────────────────────────────────────────────

class KnowledgePackService:
    """Service tập trung để load, query và expose knowledge packs.

    Dùng cho:
      - Morning Brief generation (gen_morning_brief.py)
      - Red flag engine (app/safety/red_flag_engine.py)
      - Medication safety engine (app/safety/medication_safety_engine.py)
      - Chronic Care Clinic OS API layer
      - Dashboard reporting

    An toàn: không expose bất kỳ pack nào vi phạm clinical_release_allowed=True
    khi chế độ draft (status != clinical_release_allowed).
    """

    def __init__(
        self,
        packs_dir: Path = KNOWLEDGE_PACKS_DIR,
        version: str = "2026.1-draft",
        load_full: bool = True,
    ):
        self._packs_dir = packs_dir
        self._version = version
        self._load_full = load_full
        self._packs: Dict[str, KnowledgePack] = {}
        self._loaded = False

    def load(self) -> "KnowledgePackService":
        """Discover và load tất cả packs từ packs_dir. Trả self để chain."""
        if not self._packs_dir.exists():
            logger.error("knowledge-packs directory không tồn tại: %s", self._packs_dir)
            self._loaded = True
            return self

        loader = _load_pack_full if self._load_full else _load_pack
        for pack_dir in sorted(self._packs_dir.iterdir()):
            if not pack_dir.is_dir():
                continue
            pack = loader(pack_dir, self._version)
            self._packs[pack.pack_id] = pack
            if pack.is_complete:
                logger.info("✅ Loaded: %s (%s)", pack.pack_id, self._version)
            else:
                logger.warning(
                    "⚠️  Incomplete: %s — missing: %s, errors: %s",
                    pack.pack_id, pack.missing_files, pack.load_errors,
                )

        self._loaded = True
        logger.info("KnowledgePackService: %d packs loaded", len(self._packs))
        return self

    def _ensure_loaded(self) -> None:
        if not self._loaded:
            self.load()

    # ── Query methods ─────────────────────────────────────────────────────────

    def get(self, pack_id: str) -> Optional[KnowledgePack]:
        """Trả KnowledgePack theo pack_id, hoặc None nếu không tìm thấy."""
        self._ensure_loaded()
        return self._packs.get(pack_id)

    def all_packs(self) -> List[KnowledgePack]:
        """Danh sách tất cả packs đã load."""
        self._ensure_loaded()
        return list(self._packs.values())

    def complete_packs(self) -> List[KnowledgePack]:
        """Chỉ các packs đầy đủ 4 files và không có load error."""
        return [p for p in self.all_packs() if p.is_complete]

    def incomplete_packs(self) -> List[KnowledgePack]:
        """Packs thiếu file hoặc có lỗi load."""
        return [p for p in self.all_packs() if not p.is_complete]

    def red_flags_for(self, pack_id: str) -> List[RedFlag]:
        """Trả danh sách red flags của một pack. Dùng cho red_flag_engine.py."""
        pack = self.get(pack_id)
        return pack.red_flags if pack else []

    def all_red_flags(self) -> Dict[str, List[RedFlag]]:
        """Tất cả red flags theo pack_id — dùng để feed vào RedFlagEngine."""
        return {p.pack_id: p.red_flags for p in self.complete_packs()}

    def drug_safety_rules_for(self, pack_id: str) -> Dict:
        """Drug safety rules cho một pack. Dùng cho medication_safety_engine.py."""
        pack = self.get(pack_id)
        return pack.drug_safety_rules if pack else {}

    # ── Safety enforcement ────────────────────────────────────────────────────

    def assert_draft_only(self, pack_id: str) -> None:
        """Raise nếu cố dùng pack cho mục đích lâm sàng thật.

        Gọi ở mọi điểm có thể dùng pack cho patient-facing output.
        """
        pack = self.get(pack_id)
        if pack is None:
            raise KeyError(f"Pack không tồn tại: {pack_id}")
        scope = pack.scope
        if scope is None:
            raise RuntimeError(f"Pack {pack_id} chưa có scope — không dùng được.")
        if scope.clinical_release_allowed:
            raise RuntimeError(
                f"Pack {pack_id} có clinical_release_allowed=True — "
                "cần review quy trình release trước khi dùng."
            )
        if scope.prescription_generation_allowed:
            raise RuntimeError(
                f"Pack {pack_id} có prescription_generation_allowed=True — "
                "KHÔNG được dùng để generate đơn thuốc."
            )

    # ── Morning Brief adapter ─────────────────────────────────────────────────

    def morning_brief_summary(self) -> List[Dict]:
        """Tóm tắt cho Morning Brief — chỉ complete packs, draft_review_only.

        Trả list dict với: pack_id, topic, version, red_flag_count,
        recommendation_sections, drug_rule_count, status.
        Không include nội dung chi tiết để tránh hallucination risk.
        """
        self._ensure_loaded()
        summaries = []
        for pack in self.complete_packs():
            if not pack.is_safe_for_review:
                continue
            rec_sections = list(pack.recommendations.keys()) if pack.recommendations else []
            drug_groups = list(pack.drug_safety_rules.keys()) if pack.drug_safety_rules else []
            summaries.append({
                "pack_id": pack.pack_id,
                "topic": pack.scope.topic if pack.scope else "",
                "version": pack.version,
                "red_flag_count": len(pack.red_flags),
                "recommendation_sections": rec_sections,
                "drug_rule_groups": drug_groups,
                "status": pack.scope.status if pack.scope else "unknown",
                "disclaimer": pack.scope.disclaimer if pack.scope else "",
            })
        return summaries

    # ── Status report ─────────────────────────────────────────────────────────

    def status_report(self) -> Dict:
        """Trả báo cáo trạng thái đầy đủ — dùng cho Dashboard Master và CI."""
        self._ensure_loaded()
        all_p = self.all_packs()
        complete = self.complete_packs()
        incomplete = self.incomplete_packs()
        return {
            "total_packs": len(all_p),
            "complete_packs": len(complete),
            "incomplete_packs": len(incomplete),
            "version": self._version,
            "packs_dir": str(self._packs_dir),
            "complete": [
                {"pack_id": p.pack_id, "topic": p.scope.topic if p.scope else ""}
                for p in complete
            ],
            "incomplete": [
                {
                    "pack_id": p.pack_id,
                    "missing_files": p.missing_files,
                    "load_errors": p.load_errors,
                }
                for p in incomplete
            ],
        }


# ── Singleton ─────────────────────────────────────────────────────────────────

_service_instance: Optional[KnowledgePackService] = None


def get_knowledge_pack_service(
    packs_dir: Path = KNOWLEDGE_PACKS_DIR,
    version: str = "2026.1-draft",
    reload: bool = False,
) -> KnowledgePackService:
    """Trả singleton KnowledgePackService, lazy-loaded.

    Args:
        packs_dir: Override đường dẫn knowledge-packs (dùng cho test).
        version: Version của pack cần load.
        reload: Force reload từ disk (dùng sau khi thêm pack mới).
    """
    global _service_instance
    if _service_instance is None or reload:
        _service_instance = KnowledgePackService(
            packs_dir=packs_dir, version=version
        ).load()
    return _service_instance


# ── CLI / quick check ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
    svc = KnowledgePackService().load()
    report = svc.status_report()
    print("\n" + "=" * 60)
    print(f"KNOWLEDGE PACK STATUS — version {report['version']}")
    print("=" * 60)
    print(f"Total   : {report['total_packs']}")
    print(f"Complete: {report['complete_packs']} ✅")
    print(f"Missing : {report['incomplete_packs']} ⚠️")
    print("\nComplete packs:")
    for p in report["complete"]:
        print(f"  ✅  {p['pack_id']:<45} {p['topic']}")
    if report["incomplete"]:
        print("\nIncomplete packs:")
        for p in report["incomplete"]:
            print(f"  ⚠️   {p['pack_id']}")
            for f in p["missing_files"]:
                print(f"       missing: {f}")
    print("\nMorning Brief Summary (topic + red_flag_count):")
    for s in svc.morning_brief_summary():
        print(f"  {s['pack_id']:<45} RF={s['red_flag_count']}  {s['topic']}")
    print("=" * 60)
    print("Disclaimer: DRAFT REVIEW-ONLY — không dùng cho quyết định lâm sàng thật.")
