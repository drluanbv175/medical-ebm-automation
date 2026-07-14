"""
ApprovalLedger — Append-only ledger cho mọi human approval.
Không cho phép Agent tự tạo approval.
Không lưu PII trong ledger.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .schemas import ApprovalDecisionEnum, ApprovalRecord

STAKEHOLDER_ROLE_ALIASES: dict[str, set[str]] = {
    "PI": {
        "PI",
        "PI_PROJECT_OWNER",
        "PRINCIPAL_INVESTIGATOR",
        "CHU_NHIEM_DE_TAI",
        "CHU_NHIEM_NGHIEN_CUU",
        "NGHIEN_CUU_VIEN_CHINH",
        "CHỦ_NHIỆM_ĐỀ_TÀI",
        "CHỦ_NHIỆM_NGHIÊN_CỨU",
        "NGHIÊN_CỨU_VIÊN_CHÍNH",
    },
    "IRB": {
        "IRB",
        "IRB_CHAIR",
        "IRB_MEMBER",
        "IRB_ETHICS_COMMITTEE",
        "ETHICS_COMMITTEE",
        "HOI_DONG_DAO_DUC",
        "HOI_DONG_Y_DUC",
        "HỘI_ĐỒNG_ĐẠO_ĐỨC",
        "HỘI_ĐỒNG_Y_ĐỨC",
    },
    "STATISTICIAN": {
        "STATISTICIAN",
        "BIOSTATISTICIAN",
        "METHODS_STATISTICS_REVIEWER",
        "THONG_KE_VIEN",
        "CHUYEN_GIA_THONG_KE",
        "PHUONG_PHAP_THONG_KE",
        "THỐNG_KÊ_VIÊN",
        "CHUYÊN_GIA_THỐNG_KÊ",
        "PHƯƠNG_PHÁP_THỐNG_KÊ",
    },
    "INDEPENDENT_PEER_REVIEWER": {
        "INDEPENDENT_PEER_REVIEWER",
        "PEER_REVIEWER",
        "EXTERNAL_REVIEWER",
        "PHAN_BIEN_DOC_LAP",
        "PHAN_BIEN",
        "PHẢN_BIỆN_ĐỘC_LẬP",
        "PHẢN_BIỆN",
    },
}

GATE_REQUIRED_STAKEHOLDERS: dict[str, str] = {
    "G2": "IRB",
    "G4": "STATISTICIAN",
    "G9": "PI",
}


def normalize_reviewer_role(role: str) -> str:
    """Chuẩn hóa role để so khớp alias, không lưu/thao tác PII."""
    return (
        (role or "")
        .strip()
        .upper()
        .replace("-", "_")
        .replace(" ", "_")
        .replace("/", "_")
    )


def reviewer_role_satisfies_stakeholder(role: str, stakeholder: str) -> bool:
    """Role có thuộc nhóm stakeholder bắt buộc không."""
    aliases = STAKEHOLDER_ROLE_ALIASES.get(normalize_reviewer_role(stakeholder), set())
    return normalize_reviewer_role(role) in aliases


def required_stakeholder_for_gate(gate_id: str) -> Optional[str]:
    return GATE_REQUIRED_STAKEHOLDERS.get((gate_id or "").strip().upper())


class ApprovalLedger:
    """
    Append-only ledger lưu ApprovalRecord.
    Mọi approval do Agent tạo sẽ bị block.
    Evidence hash được verify khi check.
    """

    def __init__(self):
        self._records: list[ApprovalRecord] = []

    # ── Write ─────────────────────────────────────────────────────────────────

    def add_approval(
        self,
        record: ApprovalRecord,
        created_by_agent: bool = False,
    ) -> tuple[bool, str]:
        """
        Thêm approval record vào ledger.
        Block nếu created_by_agent=True.
        Trả (success: bool, reason: str).
        """
        if created_by_agent or record._created_by_agent:
            return False, "AGENT_CREATED_APPROVAL_BLOCKED"

        if (
            record.artifact_creator_agent
            and record.reviewer_agent
            and record.artifact_creator_agent == record.reviewer_agent
        ):
            return False, "SELF_REVIEW_BLOCKED"

        # Kiểm tra evidence hash không rỗng
        if not record.evidence_hash or record.evidence_hash in ("", "none", "N/A"):
            return False, "MISSING_EVIDENCE_HASH"

        # Kiểm tra approval_id unique
        existing_ids = {r.approval_id for r in self._records}
        if record.approval_id in existing_ids:
            return False, f"DUPLICATE_APPROVAL_ID:{record.approval_id}"

        self._records.append(record)
        return True, "ADDED"

    # ── Read ──────────────────────────────────────────────────────────────────

    def check_has_approval(
        self,
        gate_id: str,
        decision: ApprovalDecisionEnum = ApprovalDecisionEnum.APPROVED,
    ) -> Optional[ApprovalRecord]:
        """Trả ApprovalRecord mới nhất cho gate_id nếu có, ngược lại None."""
        matching = [
            r for r in self._records
            if r.gate_id == gate_id and r.decision == decision
        ]
        if not matching:
            return None
        # Trả record mới nhất (timestamp_utc sort lexicographic — ISO 8601)
        return sorted(matching, key=lambda r: r.timestamp_utc)[-1]

    def check_required_stakeholder_approval(
        self,
        gate_id: str,
        decision: ApprovalDecisionEnum = ApprovalDecisionEnum.APPROVED,
    ) -> Optional[ApprovalRecord]:
        """
        Trả approval mới nhất cho gate nếu đúng stakeholder bắt buộc.

        G2 cần IRB/ethics committee, G4 cần thống kê/phương pháp, G9 cần PI.
        Approval synthetic, agent-created hoặc self-review không được tính là
        phê duyệt stakeholder thật. Cổng không có cấu hình stakeholder rơi về
        check_has_approval() để giữ tương thích.
        """
        stakeholder = required_stakeholder_for_gate(gate_id)
        if not stakeholder:
            return self.check_has_approval(gate_id, decision=decision)
        matching = [
            r for r in self._records
            if r.gate_id == gate_id
            and r.decision == decision
            and not getattr(r, "is_synthetic", False)
            and not getattr(r, "_created_by_agent", False)
            and not (
                r.artifact_creator_agent
                and r.reviewer_agent
                and r.artifact_creator_agent == r.reviewer_agent
            )
            and reviewer_role_satisfies_stakeholder(r.reviewer_role, stakeholder)
        ]
        if not matching:
            return None
        return sorted(matching, key=lambda r: r.timestamp_utc)[-1]

    def stakeholder_gate_status(self, gate_id: str) -> dict:
        """Tóm tắt trạng thái cổng theo stakeholder thật, dùng cho audit/verifier."""
        stakeholder = required_stakeholder_for_gate(gate_id)
        approval = self.check_required_stakeholder_approval(gate_id)
        if approval is not None:
            return {
                "gate_id": gate_id,
                "required_stakeholder": stakeholder,
                "satisfied": True,
                "reason": "OK",
                "approval_id": approval.approval_id,
                "reviewer_role": approval.reviewer_role,
            }
        if stakeholder:
            return {
                "gate_id": gate_id,
                "required_stakeholder": stakeholder,
                "satisfied": False,
                "reason": f"MISSING_REQUIRED_STAKEHOLDER:{stakeholder}",
                "approval_id": None,
                "reviewer_role": None,
            }
        return {
            "gate_id": gate_id,
            "required_stakeholder": None,
            "satisfied": self.check_has_approval(gate_id) is not None,
            "reason": "NO_STAKEHOLDER_REQUIREMENT",
            "approval_id": None,
            "reviewer_role": None,
        }

    def get_all_approvals(self) -> list[ApprovalRecord]:
        return list(self._records)

    def count(self) -> int:
        return len(self._records)

    def synthetic_approvals(self) -> list[ApprovalRecord]:
        """V4.3: các approval mô phỏng (is_synthetic=True) — KHÔNG phải người."""
        return [r for r in self._records if getattr(r, "is_synthetic", False)]

    def has_synthetic_approvals(self) -> bool:
        return bool(self.synthetic_approvals())

    def has_only_synthetic_for(self, gate_id: str) -> bool:
        """True nếu cổng gate_id chỉ được thỏa bởi approval SYNTHETIC (không có người)."""
        recs = [r for r in self._records if r.gate_id == gate_id]
        return bool(recs) and all(getattr(r, "is_synthetic", False) for r in recs)

    def self_review_violations(self) -> list[ApprovalRecord]:
        """Các record vi phạm độc lập reviewer/creator nếu import từ nguồn cũ."""
        return [
            r for r in self._records
            if r.artifact_creator_agent
            and r.reviewer_agent
            and r.artifact_creator_agent == r.reviewer_agent
        ]

    def has_self_review_violations(self) -> bool:
        return bool(self.self_review_violations())

    def has_ethics_approval(self) -> bool:
        return self.check_required_stakeholder_approval("G2") is not None

    def has_sap_lock(self) -> bool:
        return self.check_required_stakeholder_approval("G4") is not None

    def has_pi_signoff(self) -> bool:
        """G9 = author integrity PI sign-off."""
        return self.check_required_stakeholder_approval("G9") is not None

    def has_gate_a(self) -> bool:
        """GATE_A = cổng áp dụng lâm sàng (dieu-phoi-lam-sang)."""
        return self.check_has_approval("GATE_A") is not None

    def has_gate_b(self) -> bool:
        """GATE_B = cổng ghi sổ cái (so-cai-ghi-nho)."""
        return self.check_has_approval("GATE_B") is not None

    # ── Integrity ─────────────────────────────────────────────────────────────

    def verify_evidence_hash(self, record: ApprovalRecord, content: str) -> bool:
        """
        Kiểm tra evidence_hash khớp SHA256 của content.
        Dùng khi verify một record đã lưu.
        """
        computed = hashlib.sha256(content.encode()).hexdigest()
        return computed == record.evidence_hash

    def export_json(self) -> str:
        """Xuất ledger thành JSON (không có PII)."""
        def record_to_dict(r: ApprovalRecord) -> dict:
            return {
                "approval_id": r.approval_id,
                "gate_id": r.gate_id,
                "reviewer_role": r.reviewer_role,
                "reviewer_identity_reference": r.reviewer_identity_reference,
                "decision": r.decision.value,
                "scope": r.scope,
                "evidence_hash": r.evidence_hash,
                "timestamp_utc": r.timestamp_utc,
                "supersedes": r.supersedes,
                "artifact_creator_agent": r.artifact_creator_agent,
                "reviewer_agent": r.reviewer_agent,
                "is_synthetic": getattr(r, "is_synthetic", False),
                "approver_signature": getattr(r, "approver_signature", None),
            }
        return json.dumps(
            [record_to_dict(r) for r in self._records],
            indent=2,
            ensure_ascii=False,
        )

    # ── Persistence (thêm 2026-07-08, BL-06) ────────────────────────────────────
    # TRƯỚC ĐÂY: ApprovalLedger chỉ sống TRONG BỘ NHỚ (self._records) — mỗi lần
    # research_workflow.py/dashboard.py khởi tạo `ApprovalLedger()` là một sổ RỖNG
    # mới, không có cách nào biết "đã từng có phê duyệt thật ở lần chạy TRƯỚC" khi
    # mỗi lần gọi `python tools/run_g4_auto.py`/`run_g5_auto.py`/`run_g6_auto.py` là
    # MỘT TIẾN TRÌNH MỚI. Đây chính là lý do BL-06 tồn tại: "cryptographic binding"
    # không thể hoạt động qua nhiều lần gọi CLI nếu ledger không ghi ra đĩa. Thêm
    # to_file()/from_file() để ledger SỐNG ĐƯỢC qua nhiều lần chạy — mỗi đề tài có
    # 1 file `exports/<study>/approval_ledger.json`, append-only, PII-free (đúng
    # định dạng export_json() đã có, không tạo định dạng mới).
    def to_file(self, path) -> None:
        """Ghi ledger ra file JSON (ghi đè toàn bộ — gọi SAU khi add_approval() để
        file luôn phản ánh đủ self._records). Không PII (export_json() đã đảm bảo)."""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(p.suffix + ".tmp")
        tmp.write_text(self.export_json(), encoding="utf-8")
        os.replace(tmp, p)  # ghi nguyên tử — tránh file nửa vời nếu crash giữa chừng

    @classmethod
    def from_file(cls, path) -> "ApprovalLedger":
        """Nạp ledger từ file JSON (định dạng export_json()). File không tồn tại/
        rỗng/hỏng → trả ledger RỖNG (KHÔNG raise) — vì phần lớn đề tài CHƯA có file
        này (chưa từng được duyệt qua cơ chế crypto này), đây là trạng thái HỢP LỆ,
        không phải lỗi. Bản ghi nạp lại có _created_by_agent=False (đã ghi ra đĩa
        nghĩa là đã qua add_approval() thành công lúc ghi, không cho phép giả mạo
        lại từ file — file này chỉ được ghi bởi to_file(), không phải input tự do)."""
        ledger = cls()
        p = Path(path)
        if not p.exists():
            return ledger
        try:
            raw = json.loads(p.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            return ledger
        for d in raw:
            try:
                rec = ApprovalRecord(
                    approval_id=d["approval_id"], gate_id=d["gate_id"],
                    reviewer_role=d["reviewer_role"],
                    reviewer_identity_reference=d["reviewer_identity_reference"],
                    decision=ApprovalDecisionEnum(d["decision"]), scope=d["scope"],
                    evidence_hash=d["evidence_hash"], timestamp_utc=d["timestamp_utc"],
                    supersedes=d.get("supersedes"),
                    artifact_creator_agent=d.get("artifact_creator_agent"),
                    reviewer_agent=d.get("reviewer_agent"),
                    _created_by_agent=False,
                    is_synthetic=d.get("is_synthetic", False),
                    approver_signature=d.get("approver_signature"),
                )
            except (KeyError, ValueError):
                continue  # dòng hỏng/thiếu trường bắt buộc — bỏ qua, không crash cả ledger
            ledger._records.append(rec)
        return ledger

    # ── Factory helpers (for tests only) ──────────────────────────────────────

    @staticmethod
    def make_human_approval(
        gate_id: str,
        reviewer_role: str,
        reviewer_ref: str,
        scope: str,
        evidence_content: str,
        decision: ApprovalDecisionEnum = ApprovalDecisionEnum.APPROVED,
        supersedes: Optional[str] = None,
        artifact_creator_agent: Optional[str] = None,
        reviewer_agent: Optional[str] = None,
        approver_signature: Optional[str] = None,
        timestamp_utc: Optional[str] = None,
    ) -> ApprovalRecord:
        """
        Factory dùng trong tests để tạo human approval hợp lệ.
        Tự tính evidence_hash từ evidence_content.

        approver_signature/timestamp_utc (thêm 2026-07-12): chữ ký HMAC cần biết
        evidence_hash+timestamp TRƯỚC khi ký (xem tools/gate_contract.py::
        sign_approval) — caller tự chọn timestamp_utc, ký trước, rồi truyền cả
        hai giá trị vào đây; factory chỉ LƯU, không tự ký (giữ runtime/ độc lập
        tools/, xem tools/approve_gate.py cho quy trình ký thật đầu-cuối).
        timestamp_utc bỏ trống → factory tự sinh như trước (đường test cũ).
        """
        evidence_hash = hashlib.sha256(evidence_content.encode()).hexdigest()
        timestamp = timestamp_utc or datetime.now(timezone.utc).isoformat()
        approval_id = hashlib.sha256(
            f"{gate_id}:{reviewer_ref}:{timestamp}".encode()
        ).hexdigest()[:16]
        return ApprovalRecord(
            approval_id=approval_id,
            gate_id=gate_id,
            reviewer_role=reviewer_role,
            reviewer_identity_reference=reviewer_ref,
            decision=decision,
            scope=scope,
            evidence_hash=evidence_hash,
            timestamp_utc=timestamp,
            supersedes=supersedes,
            artifact_creator_agent=artifact_creator_agent,
            reviewer_agent=reviewer_agent,
            _created_by_agent=False,
            is_synthetic=False,
            approver_signature=approver_signature,
        )

    @staticmethod
    def make_synthetic_approval(
        gate_id: str,
        scope: str,
        evidence_content: str,
        reviewer_role: str = "SYNTHETIC_TECHNICAL_FIXTURE",
        reviewer_ref: str = "MRAQ_HARNESS_NOT_A_PERSON",
        decision: ApprovalDecisionEnum = ApprovalDecisionEnum.APPROVED,
        artifact_creator_agent: Optional[str] = None,
        reviewer_agent: Optional[str] = None,
    ) -> ApprovalRecord:
        """
        V4.3: tạo approval MÔ PHỎNG có marker cấu trúc ``is_synthetic=True``.

        Dùng cho Research Studio để mở cổng trong mô phỏng. KHÁC make_human_approval:
        record này được gắn cờ structural is_synthetic=True (không chỉ free-text),
        truy vấn được qua ledger.synthetic_approvals() và hiện trong export — để
        KHÔNG BAO GIỜ bị nhầm là phê duyệt người.
        """
        rec = ApprovalLedger.make_human_approval(
            gate_id=gate_id, reviewer_role=reviewer_role, reviewer_ref=reviewer_ref,
            scope=scope, evidence_content=evidence_content, decision=decision,
            artifact_creator_agent=artifact_creator_agent,
            reviewer_agent=reviewer_agent,
        )
        rec.is_synthetic = True
        return rec
