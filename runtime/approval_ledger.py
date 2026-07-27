"""
ApprovalLedger — Append-only ledger cho mọi human approval.
Không cho phép Agent tự tạo approval.
Không lưu PII trong ledger.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Optional

from .schemas import ApprovalDecisionEnum, ApprovalRecord

if sys.platform == "win32":
    import msvcrt
else:
    import fcntl


class LedgerLockInvalidated(RuntimeError):
    """Raise khi khóa liên-tiến-trình của ApprovalLedger.locked_update() bị vô
    hiệu hóa giữa chừng (file .lock bị xóa/thay trong lúc đang giữ khóa — xem
    ApprovalLedger._exclusive_file_lock/_lock_identity_matches). Caller PHẢI
    bắt exception này (không để traceback thô lộ ra CLI) và báo bác sĩ chạy
    lại lệnh — đây là lỗi TẠM THỜI/hiếm, không phải lỗi cấu hình."""

# Vá 2026-07-15 (hợp nhất bảng stakeholder — trước đây file này giữ 3 bản sao RIÊNG
# của tools/gate_contract.py (STAKEHOLDER_ROLE_ALIASES, GATE_REQUIRED_STAKEHOLDERS,
# GATE_ADDITIONAL_STAKEHOLDERS), và đã LỆCH THẬT 2 lần trong 24 giờ — G4 nới nhận PI
# (2026-07-14, vá 2026-07-15) rồi G8 bị bỏ sót hoàn toàn (vá 2026-07-15, xem
# test_gate_contract_approval_ledger_stakeholder_parity.py) — mỗi lần do 1 phiên
# khác nhau sửa gate_contract.py mà quên bản sao ở đây. Từ nay KHÔNG còn dict tay
# nào cả — mọi giá trị suy ra TRỰC TIẾP từ gate_contract.py (nguồn THẬT, được
# tools/approve_gate.py + run_g*_auto.py dùng), nên không thể lệch nữa "by
# construction" thay vì chỉ dựa vào test dò lệch. gate_contract.py cố tình chỉ dùng
# thư viện chuẩn để 5 tool tính toán (clinical_calc.py...) bare-import được không cần
# sys.path — chiều import ở đây (runtime/ -> tools/) không phá ràng buộc đó vì
# approval_ledger.py luôn được import qua package đầy đủ (runtime.approval_ledger),
# không bao giờ bare-import, nên tự thêm sys.path là an toàn. Không có nguy cơ vòng
# lặp import: gate_contract.py không import bất kỳ thứ gì từ runtime/ (xác nhận qua
# grep trước khi đổi).
_TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))
import gate_contract as _GC  # noqa: E402

STAKEHOLDER_ROLE_ALIASES: dict[str, set[str]] = _GC._STAKEHOLDER_ROLE_ALIASES

# dict[str, str] — CHỈ nhóm CHÍNH (nhãn hiển thị), giữ nguyên kiểu trả về cũ vì
# research_project/ và test_v4_3_4_... nối chuỗi/so sánh == trên field
# "required_stakeholder"; đổi sang tuple sẽ vỡ các chỗ đó.
GATE_REQUIRED_STAKEHOLDERS: dict[str, str] = {
    gate: groups[0] for gate, groups in _GC._GATE_REQUIRED_STAKEHOLDERS.items()
}

# Nhóm PHỤ (ngoài nhóm chính) được chấp nhận cho gate đó, vd G4 nhận thêm PI.
GATE_ADDITIONAL_STAKEHOLDERS: dict[str, tuple[str, ...]] = {
    gate: tuple(groups[1:])
    for gate, groups in _GC._GATE_REQUIRED_STAKEHOLDERS.items()
    if len(groups) > 1
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


def _allowed_stakeholders_for_gate(gate_id: str) -> tuple[str, ...]:
    """Mọi nhóm stakeholder được CHẤP NHẬN cho gate_id — nhóm chính (nhãn hiển thị,
    xem required_stakeholder_for_gate) CỘNG nhóm phụ (GATE_ADDITIONAL_STAKEHOLDERS,
    vd G4 nhận thêm PI)."""
    primary = required_stakeholder_for_gate(gate_id)
    extra = GATE_ADDITIONAL_STAKEHOLDERS.get((gate_id or "").strip().upper(), ())
    return ((primary,) if primary else ()) + extra


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
        """Trả ApprovalRecord mới nhất cho gate_id nếu có, ngược lại None.

        ★ VÁ 2026-07-27 (vòng kiểm định độc lập thứ 3 → sửa vòng 4): TÔN TRỌNG THU HỒI.
        Bản trước lọc `r.decision == decision` RỒI mới lấy bản mới nhất, nên một quyết
        định TỪ CHỐI ghi SAU đó không bao giờ che được phê duyệt trước — hội đồng rút phê
        duyệt mà hàm này vẫn trả về approval cũ. Đây là bản sao CÙNG LỖI với
        tools/gate_contract.py::ledger_approved(); lỗi ở đó đã vá trước, còn ở đây thì
        chưa — đúng mẫu "sửa 1 chỗ quên chỗ anh em" đã lặp lại nhiều vòng trong dự án.
        Hệ quả THẬT: tools/stakeholder_review_audit.py (công cụ BÁC SĨ dùng kiểm tay) gọi
        xuống đây nên vẫn in [PASS] cho một cổng đã bị thu hồi — người kiểm tra thủ công
        được xác nhận một câu trả lời SAI."""
        return self._latest_if_not_superseded(
            [r for r in self._records if r.gate_id == gate_id], decision
        )

    @staticmethod
    def _latest_if_not_superseded(
        candidates: list[ApprovalRecord],
        decision: ApprovalDecisionEnum,
    ) -> Optional[ApprovalRecord]:
        """Bản ghi MỚI NHẤT trong `candidates` — chỉ trả về nếu quyết định của nó ĐÚNG
        bằng `decision`. Nếu bản mới nhất mang quyết định khác (vd REJECTED thu hồi một
        APPROVED trước đó) thì trả None.

        Tách riêng việc CHỌN bản mới nhất khỏi việc XÉT quyết định — đúng cách
        gate_contract._latest_authoritative_record() làm, để hai nơi không lệch nhau."""
        if not candidates:
            return None
        # timestamp_utc sort lexicographic — ISO 8601; str() phòng giá trị phi-chuỗi.
        latest = sorted(candidates, key=lambda r: str(getattr(r, "timestamp_utc", "") or ""))[-1]
        return latest if latest.decision == decision else None

    def check_required_stakeholder_approval(
        self,
        gate_id: str,
        decision: ApprovalDecisionEnum = ApprovalDecisionEnum.APPROVED,
    ) -> Optional[ApprovalRecord]:
        """
        Trả approval mới nhất cho gate nếu đúng stakeholder bắt buộc.

        G2 cần IRB/ethics committee, G4 cần thống kê/phương pháp HOẶC PI tự ký
        (GATE_ADDITIONAL_STAKEHOLDERS, vá 2026-07-15), G9 cần PI. Approval synthetic,
        agent-created hoặc self-review không được tính là phê duyệt stakeholder thật.
        Cổng không có cấu hình stakeholder rơi về check_has_approval() để giữ tương
        thích.
        """
        allowed_stakeholders = _allowed_stakeholders_for_gate(gate_id)
        if not allowed_stakeholders:
            return self.check_has_approval(gate_id, decision=decision)
        # VÁ 2026-07-27: KHÔNG lọc theo decision ở đây — chọn bản mới nhất trong số các
        # bản ghi ĐỦ THẨM QUYỀN (đúng stakeholder, không synthetic, không agent tự duyệt)
        # rồi mới xét quyết định của nó, để một REJECTED muộn hơn THU HỒI được approval.
        matching = [
            r for r in self._records
            if r.gate_id == gate_id
            and not getattr(r, "is_synthetic", False)
            and not getattr(r, "_created_by_agent", False)
            and not (
                r.artifact_creator_agent
                and r.reviewer_agent
                and r.artifact_creator_agent == r.reviewer_agent
            )
            and any(
                reviewer_role_satisfies_stakeholder(r.reviewer_role, s)
                for s in allowed_stakeholders
            )
        ]
        return self._latest_if_not_superseded(matching, decision)

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

    # ── Khóa liên-tiến-trình (thêm 2026-07-15, sau red-team đối kháng) ──────────
    # Lỗ hổng THẬT đã tái hiện được: from_file() → mutate → to_file() là read-
    # modify-write KHÔNG khóa — 2 tiến trình gọi tools/approve_gate.py (hoặc
    # approve_gate_synthetic_admin.py) gần như đồng thời trên CÙNG 1
    # approval_ledger.json, tiến trình ghi SAU đè mất bản ghi tiến trình ghi
    # TRƯỚC dù cả hai đều báo "✅ đã ghi phê duyệt" thành công — mất một phê
    # duyệt THẬT trong im lặng. locked_update() khóa file độc quyền quanh TRỌN
    # chu trình load→mutate→save để 2 tiến trình tự xếp hàng thay vì chồng nhau.
    @staticmethod
    def _lock_identity_matches(fd, lock_path: Path) -> bool:
        """True nếu file descriptor đang giữ VẪN CHÍNH LÀ file tại lock_path lúc
        này (so (st_dev, st_ino) — mẫu chuẩn chống flock+unlink race). False nếu
        file đã bị xóa/thay từ dưới chân ta (unlink rồi tạo lại, hoặc xóa hẳn)."""
        try:
            on_disk = os.stat(lock_path)
        except OSError:
            return False
        held = os.fstat(fd.fileno())
        return (on_disk.st_dev, on_disk.st_ino) == (held.st_dev, held.st_ino)

    @staticmethod
    @contextlib.contextmanager
    def _exclusive_file_lock(lock_path: Path, timeout_s: float = 30.0):
        """Khóa advisory liên-tiến-trình cross-platform (fcntl trên POSIX,
        msvcrt trên Windows — dự án chạy cả Mac lẫn Windows, xem CLAUDE.md).
        Yield chính file descriptor đang giữ khóa (KHÔNG phải None) — caller
        (locked_update) cần fd này để tự xác minh LẠI khóa còn hợp lệ NGAY
        TRƯỚC lúc ghi (xem lý do dưới).

        VÁ 2026-07-16 (red-team vòng 2, CONFIRMED bằng script thật): bản vá đầu
        tiên chỉ xác nhận identity NGAY SAU khi acquire — KHÔNG đủ, vì tấn công
        thật là xóa file `.lock` TRONG LÚC tiến trình đang ở "giữa" khối with
        (đang làm việc), không phải lúc acquire. Ở thời điểm acquire, mọi thứ
        VẪN nhất quán; vài trăm ms sau đó file mới bị xóa+tạo lại bởi tiến trình
        khác (inode mới) — tiến trình khác lấy khóa NGAY trên inode mới đó
        (hợp lệ theo góc nhìn của chính nó), trong khi tiến trình đầu vẫn tưởng
        mình đang giữ khóa "cho path đó". Kiểm 1 lần lúc acquire không bắt được
        trường hợp này. Đây LÀ lý do `_lock_identity_matches` phải được gọi LẠI
        bởi `locked_update` ngay trước `to_file()` — xem ở đó.

        GIỚI HẠN THẬT: chỉ có hiệu lực GIỮA CÁC TIẾN TRÌNH TRÊN CÙNG MỘT MÁY —
        KHÔNG bảo vệ được khi Mac và Windows cùng ghi gần như đồng thời qua
        OneDrive (OneDrive không có khóa file phân tán thật, chỉ đồng bộ
        "last-write-wins" giữa 2 máy) — xem lưu ý concurrent-editing đã biết
        của dự án."""
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        deadline = time.monotonic() + timeout_s
        fd = open(lock_path, "a+b")
        acquired = False
        try:
            while True:
                try:
                    if sys.platform == "win32":
                        msvcrt.locking(fd.fileno(), msvcrt.LK_NBLCK, 1)
                    else:
                        fcntl.flock(fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    acquired = True
                    break
                except OSError:
                    if time.monotonic() >= deadline:
                        raise TimeoutError(
                            f"Không lấy được khóa ledger trong {timeout_s}s: {lock_path} "
                            "— có tiến trình khác đang ghi cùng đề tài, thử lại sau."
                        )
                    time.sleep(0.05)
            yield fd
        finally:
            if acquired:
                try:
                    if sys.platform == "win32":
                        fd.seek(0)
                        msvcrt.locking(fd.fileno(), msvcrt.LK_UNLCK, 1)
                    else:
                        fcntl.flock(fd.fileno(), fcntl.LOCK_UN)
                except OSError:
                    pass
            fd.close()

    @classmethod
    @contextlib.contextmanager
    def locked_update(cls, path) -> Iterator["ApprovalLedger"]:
        """Chu trình load→mutate→save AN TOÀN LIÊN-TIẾN-TRÌNH — dùng thay cho
        gọi rời from_file()/to_file(). Ví dụ:
            with ApprovalLedger.locked_update(ledger_path) as ledger:
                ok, reason = ledger.add_approval(record, created_by_agent=False)
            # to_file() tự động chạy khi thoát khối with — kể cả khi add_approval
            # thất bại (ok=False), ghi lại ĐÚNG trạng thái hiện tại, không mất gì.

        VÁ 2026-07-16: xác minh LẠI khóa còn hợp lệ (file .lock chưa bị ai
        xóa/thay từ dưới chân) NGAY TRƯỚC to_file() — không chỉ lúc acquire.
        Nếu bị vô hiệu hóa giữa chừng (tấn công/nhầm lẫn xóa file .lock trong
        lúc khối with đang chạy), TỪ CHỐI ghi và raise LedgerLockInvalidated
        thay vì ghi đè âm thầm lên bản đã bị tiến trình khác cập nhật — biến
        "mất dữ liệu trong im lặng" thành "thất bại rõ ràng, gọi lại được".
        Caller (tools/approve_gate.py, tools/approve_gate_synthetic_admin.py)
        PHẢI bắt exception này (xem ở đó) — không được để traceback thô lộ ra."""
        path = Path(path)
        lock_path = path.with_suffix(path.suffix + ".lock")
        with cls._exclusive_file_lock(lock_path) as fd:
            ledger = cls.from_file(path)
            yield ledger
            if not cls._lock_identity_matches(fd, lock_path):
                raise LedgerLockInvalidated(
                    f"Khóa ledger đã bị VÔ HIỆU HÓA giữa chừng (file .lock bị xóa/thay khi "
                    f"tool đang chạy) — TỪ CHỐI ghi để tránh lost-update: {path}. "
                    "KHÔNG được xóa file .lock trong khi một lệnh duyệt đang chạy — flock tự "
                    "nhả khi tiến trình kết thúc, không cần xóa tay. Chạy lại lệnh."
                )
            ledger.to_file(path)

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
