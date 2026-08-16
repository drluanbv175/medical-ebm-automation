#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
approve_gate.py — Ghi PHÊ DUYỆT THẬT (ràng buộc mật mã) cho một cổng G, vá 2026-07-08 (BL-06);
nâng cấp CHỮ KÝ ACTOR THẬT 2026-07-12 (audit toàn diện cổng G0-G9).

Bối cảnh: "runtime/approval_ledger.py::ApprovalLedger" đã có cơ chế chống Agent tự phê duyệt
(add_approval() chặn created_by_agent=True) + evidence_hash (SHA256 nội dung artifact tại thời
điểm duyệt) — nhưng CHƯA từng được nối vào các cổng CLI (run_g4_auto.py/run_g5_auto.py) vì lớp
đó chỉ sống TRONG BỘ NHỚ một tiến trình. Script này là điểm NHẬP DUY NHẤT để bác sĩ tự tay ghi
một phê duyệt THẬT.

★ QUAN TRỌNG — KHÔNG BAO GIỜ để agent (Claude Code/Codex) tự chạy lệnh này thay bác sĩ. Trước
2026-07-12, script CHỈ kiểm tra kỹ thuật (artifact tồn tại, hash khớp), không có cách nào biết
"ai đang gõ lệnh" — một agent tự gọi script này tạo ra bản ghi KHÔNG THỂ PHÂN BIỆT với phê duyệt
bác sĩ thật (đã kiểm định đối kháng xác nhận: agent tự phê duyệt rồi chạy trót lọt phân tích
thống kê, không có bác sĩ nào tham gia). Nay có CHỮ KÝ HMAC-SHA256 bằng khóa cục bộ
~/.ebm-secrets/gate_approval_key (đặt ngoài OneDrive, đúng quy ước secrets sẵn có của dự án) —
BÁC SĨ tự thiết lập MỘT LẦN bằng `python3 tools/setup_gate_approval_key.py` (script đó PHẢI do
bác sĩ tự chạy, KHÔNG nhờ agent — nếu agent chạy hộ, agent sẽ biết khóa và tính năng vô nghĩa).
Sau khi có khóa, mọi phê duyệt được ký; downstream (gate_contract.py::ledger_approved(), dùng ở
run_g6_auto.py/run_g9_auto.py) xác minh LẠI chữ ký bằng ĐÚNG khóa đó trước khi coi một cổng là
khóa thật — không còn chỉ dựa vào "reviewer_ref tự khai". GIỚI HẠN THẬT (không giấu): nếu bác sĩ
TỰ NHỜ agent chạy script duyệt này (thay vì tự tay), chữ ký vẫn được tạo nhưng không còn ý nghĩa
độc lập — kỷ luật vận hành ("chỉ bác sĩ tự tay chạy") vẫn là lớp bảo vệ cuối cùng, không thể thay
hoàn toàn bằng kỹ thuật trong một hệ mà agent có quyền đọc toàn bộ filesystem.

Dùng:
    python3 tools/approve_gate.py --study <tên> --gate G4 \\
        --artifact exports/<tên>/G4_A5_SAP_FINAL_<tên>.md \\
        --reviewer-role "METHODS_STATISTICS_REVIEWER" --reviewer-ref "<mã/tên viết tắt, KHÔNG PII đầy đủ>"

G2 cần thêm metadata quyết định thật (số/ngày/hiệu lực, phiên bản protocol/ICF,
loại tuyển mẫu và đăng ký). Xem ``python3 tools/approve_gate.py --help``.

Role bắt buộc theo cổng (vá 2026-07-14 — nâng cấp kiểm soát PI/IRB/thống kê viên/
phản biện; G4 nới thêm PI vì doctrine hướng dẫn "Chủ nhiệm đề tài" tự ký khóa SAP
khi không có thống kê viên riêng; G8 mới thêm — trước đây bình duyệt không có cổng
cứng nào):
    G2  → IRB / IRB_ETHICS_COMMITTEE / ETHICS_COMMITTEE
    G4  → METHODS_STATISTICS_REVIEWER / BIOSTATISTICIAN / STATISTICIAN
          HOẶC PI / PI_PROJECT_OWNER / PRINCIPAL_INVESTIGATOR
    G5  → DATA_MANAGER / DATA_STEWARD / DATA_GOVERNANCE_QA_REVIEWER
          HOẶC PI / PI_PROJECT_OWNER / PRINCIPAL_INVESTIGATOR
    G8  → PHAN_BIEN / PEER_REVIEWER / EXTERNAL_REVIEWER (bình duyệt độc lập)
    G9  → PI / PI_PROJECT_OWNER / PRINCIPAL_INVESTIGATOR
    G10 → PI / PI_PROJECT_OWNER / PRINCIPAL_INVESTIGATOR

Sau khi chạy: exports/<tên>/approval_ledger.json có thêm 1 dòng phê duyệt, evidence_hash =
SHA256 của ĐÚNG nội dung file --artifact TẠI THỜI ĐIỂM CHẠY LỆNH NÀY. Nếu artifact bị sửa SAU
khi duyệt, lần kiểm tiếp theo (run_g6_auto.py/run_g9_auto.py/run_stats_analysis.py — các script
THỰC SỰ nối gate_contract.ledger_approved()) sẽ thấy hash KHÔNG khớp → không còn được coi là "đã
khóa" nữa — đây chính là ý nghĩa "ràng buộc mật mã" (khác hoàn toàn so với gõ tay "LOCKED" vào
checkpoint, vốn không biết nội dung có bị đổi sau đó hay không).

KHÔNG dùng để tự động hóa duyệt hàng loạt — mỗi lần gọi là một hành động có chủ ý của một người.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys

# Windows: stdout mặc định cp1252 giết print() tiếng Việt — ép UTF-8 (chốt BH55/R4)
import sys as _sys_r4
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import g2_quality_gate as G2Q  # noqa: E402 — cần sys.path.insert trước
import g4_quality_gate as G4Q  # noqa: E402 — cần sys.path.insert trước
import g5_quality_gate as G5Q  # noqa: E402 — cần sys.path.insert trước
import g9_quality_gate as G9Q  # noqa: E402 — cần sys.path.insert trước
import g10_quality_gate as G10Q  # noqa: E402 — cần sys.path.insert trước
import gate_contract as GC  # noqa: E402 — cần sys.path.insert trước

from app.utils.console import configure_unicode_console  # noqa: E402 — cần sys.path.insert trước
from runtime.approval_ledger import ApprovalLedger, LedgerLockInvalidated  # noqa: E402 — cần sys.path.insert trước
from runtime.schemas import ApprovalDecisionEnum  # noqa: E402 — cần sys.path.insert trước

for _s_r4 in (_sys_r4.stdout, _sys_r4.stderr):
    try:
        _s_r4.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass


# SỬA 2026-07-24 (vòng lặp kiểm tra-hoàn thiện vòng 15, phát hiện HIGH): trước
# đây KHÔNG có chỗ nào trong chuỗi khóa G4 thật (approve_gate.py →
# ApprovalLedger.add_approval() → gate_contract.ledger_approved()) kiểm nội
# dung artifact còn placeholder "[CẦN" hay chưa trước khi cho ký/coi LOCKED —
# khóa mật mã (evidence_hash + chữ ký) chỉ bảo vệ TÍNH TOÀN VẸN của một nội
# dung, không đảm bảo nội dung đó có Ý NGHĨA (không rỗng). Một SAP vừa sinh ra
# (nguyên placeholder "[CẦN BÁC SĨ ĐIỀN]" ở §2 kết cục chính/§5 covariates/
# §10 phần mềm+seed) vẫn ký được — phá vỡ mục đích chống HARKing/p-hacking mà
# G4 hướng tới. Tái dùng khái niệm đếm "[CẦN" đã có ở run_g4_auto.py::
# guardrail() R6, nhưng áp NGAY TRƯỚC lúc ký thay vì chỉ trên bản DRAFT gốc.
_G4_REQUIRED_SECTIONS = {
    "§1": "Tiêu chí nhận/loại (Quần thể phân tích)",
    "§2": "Kết cục chính",
    "§5": "Covariates/Phân tích đa biến",
    "§10": "Phần mềm + seed",
}


def _g4_sections_still_draft(content: str) -> list[str]:
    """Trả về danh sách mục §N BẮT BUỘC của SAP còn placeholder '[CẦN' chưa
    điền. Thiết kế không có một mục nào đó (vd định tính dùng §5 CHIẾN LƯỢC
    MÃ HÓA thay vì PHÂN TÍCH ĐA BIẾN — vẫn đánh số §5) không bị coi là lỗi
    riêng biệt; chỉ mục THẬT SỰ tồn tại mà còn placeholder mới bị chặn."""
    lines = content.splitlines()
    still_draft = []
    for section_num, label in _G4_REQUIRED_SECTIONS.items():
        start = None
        for i, line in enumerate(lines):
            if re.match(rf'^#{{2,3}}\s+{re.escape(section_num)}\b', line):
                start = i
                break
        if start is None:
            continue
        end = len(lines)
        for j in range(start + 1, len(lines)):
            if re.match(r'^#{2,3}\s+§\d', lines[j]):
                end = j
                break
        body = "\n".join(lines[start:end])
        if "[CẦN" in body:
            still_draft.append(f"{section_num} ({label})")
    return still_draft


def _valid_iso_date(value: str | None) -> bool:
    """Ngày G2 phải là ISO YYYY-MM-DD để so sánh không mơ hồ."""
    if not value:
        return False
    try:
        datetime.fromisoformat(value)
    except ValueError:
        return False
    return bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", value))


def _prepare_g2_attestation(
    args: argparse.Namespace,
    artifact_path: Path,
    evidence_content: str,
    study_dir: Path,
) -> tuple[str | None, list[str]]:
    """Kiểm semantic G2 và gắn attestation có cấu trúc vào đúng A3.

    Trả ``(nội_dung_mới, lỗi)``. Hàm không ký và không ghi ledger.
    """
    errors: list[str] = []
    try:
        artifact_path.resolve().relative_to(study_dir.resolve())
    except ValueError:
        errors.append("Artifact G2 phải nằm trong đúng thư mục exports/<study>")

    expected_name = f"G2_A3_ETHICS_PACKAGE_{args.study}.md"
    if artifact_path.name != expected_name:
        errors.append(f"Artifact G2 phải là {expected_name}")

    required = (
        ("g2_approval_number", "số quyết định/phê duyệt IRB"),
        ("g2_approval_date", "ngày phê duyệt"),
        ("g2_protocol_version", "phiên bản protocol được duyệt"),
        ("g2_ethics_decision", "loại quyết định đạo đức"),
        ("g2_recruitment_mode", "loại tuyển mẫu"),
        ("g2_registration_status", "trạng thái đăng ký"),
    )
    for field, label in required:
        if not str(getattr(args, field, "") or "").strip():
            errors.append(f"Thiếu {label}")

    if args.g2_approval_date and not _valid_iso_date(args.g2_approval_date):
        errors.append("--g2-approval-date phải theo YYYY-MM-DD")
    elif (
        args.g2_approval_date
        and args.g2_approval_date > datetime.now(timezone.utc).date().isoformat()
    ):
        errors.append("--g2-approval-date không được ở tương lai")
    if args.g2_valid_until and not _valid_iso_date(args.g2_valid_until):
        errors.append("--g2-valid-until phải theo YYYY-MM-DD")
    elif (
        args.g2_valid_until
        and args.g2_valid_until < datetime.now(timezone.utc).date().isoformat()
    ):
        errors.append("Quyết định G2 đã hết hiệu lực")
    if not args.g2_valid_until and not args.g2_no_expiry_confirmed:
        errors.append(
            "Phải có --g2-valid-until hoặc --g2-no-expiry-confirmed"
        )
    if args.g2_valid_until and args.g2_no_expiry_confirmed:
        errors.append(
            "Không dùng đồng thời --g2-valid-until và --g2-no-expiry-confirmed"
        )
    if (
        args.g2_approval_date
        and args.g2_valid_until
        and _valid_iso_date(args.g2_approval_date)
        and _valid_iso_date(args.g2_valid_until)
        and args.g2_valid_until < args.g2_approval_date
    ):
        errors.append("Ngày hết hiệu lực không được trước ngày phê duyệt")
    if not args.g2_icf_version and not args.g2_icf_waiver_approved:
        errors.append(
            "Phải có --g2-icf-version hoặc --g2-icf-waiver-approved"
        )
    if args.g2_icf_version and args.g2_icf_waiver_approved:
        errors.append(
            "Không dùng đồng thời phiên bản ICF và xác nhận miễn ICF"
        )

    checkpoint_path = study_dir / "G2_checkpoint.json"
    try:
        checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        checkpoint = {}
    design_code = str(
        checkpoint.get("design_code") if isinstance(checkpoint, dict) else ""
    ).strip()
    registration_required = (
        args.g2_recruitment_mode == "PROSPECTIVE_NEW_PARTICIPANTS"
        or design_code == "sr_ma"
    )
    if registration_required:
        if args.g2_registration_status != "REGISTERED":
            errors.append(
                "Thiết kế này phải có trạng thái REGISTERED "
                "(registry người tham gia hoặc registry protocol phù hợp)"
            )
        for field, label in (
            ("g2_registry", "tên registry"),
            ("g2_registration_id", "mã đăng ký"),
            ("g2_registration_date", "ngày đăng ký"),
        ):
            if not str(getattr(args, field, "") or "").strip():
                errors.append(f"Thiếu {label}")
        if args.g2_registration_date and not _valid_iso_date(args.g2_registration_date):
            errors.append("--g2-registration-date phải theo YYYY-MM-DD")
        elif (
            args.g2_registration_date
            and args.g2_registration_date
            > datetime.now(timezone.utc).date().isoformat()
        ):
            errors.append("--g2-registration-date không được ở tương lai")
    elif args.g2_registration_status != "NOT_REQUIRED":
        errors.append(
            "Không tuyển mới phải ghi --g2-registration-status NOT_REQUIRED"
        )

    if args.g2_first_enrolment_date:
        if not _valid_iso_date(args.g2_first_enrolment_date):
            errors.append("--g2-first-enrolment-date phải theo YYYY-MM-DD")
        elif (
            args.g2_registration_date
            and _valid_iso_date(args.g2_registration_date)
            and args.g2_registration_date > args.g2_first_enrolment_date
        ):
            errors.append("Ngày đăng ký không được muộn hơn ngày tuyển đầu tiên")
    if design_code == "sr_ma":
        if not args.g2_first_search_date:
            errors.append("SR/MA phải có --g2-first-search-date")
        elif not _valid_iso_date(args.g2_first_search_date):
            errors.append("--g2-first-search-date phải theo YYYY-MM-DD")
        elif (
            args.g2_registration_date
            and _valid_iso_date(args.g2_registration_date)
            and args.g2_registration_date > args.g2_first_search_date
        ):
            errors.append("Đăng ký protocol muộn hơn ngày bắt đầu tìm kiếm")

    unresolved = G2Q.unresolved_critical_placeholders(evidence_content)
    if unresolved:
        errors.append(
            f"Hồ sơ còn {len(unresolved)} placeholder khoa học/vận hành '[CẦN]'"
        )

    if errors:
        return None, errors

    base = G2Q.strip_attestation(evidence_content)
    attestation = {
        "schema_version": G2Q.ATTESTATION_SCHEMA,
        "study": args.study,
        "ethics_decision": args.g2_ethics_decision,
        "ethics_committee_ref": args.g2_ethics_committee_ref or args.reviewer_ref,
        "ethics_committee_ref_source": (
            "explicit" if args.g2_ethics_committee_ref else "reviewer_ref_fallback"
        ),
        "approval_number": args.g2_approval_number,
        "approval_date": args.g2_approval_date,
        "valid_until": args.g2_valid_until,
        "no_expiry_confirmed": bool(args.g2_no_expiry_confirmed),
        "approval_scope": args.g2_approval_scope or args.scope,
        "approved_protocol_version": args.g2_protocol_version,
        "approved_icf_version": args.g2_icf_version,
        "icf_waiver_approved": bool(args.g2_icf_waiver_approved),
        "recruitment_mode": args.g2_recruitment_mode,
        "first_enrolment_date": args.g2_first_enrolment_date,
        "first_search_date": args.g2_first_search_date,
        "registration": {
            "required": registration_required,
            "status": args.g2_registration_status,
            "registry": args.g2_registry,
            "registration_id": args.g2_registration_id,
            "registration_date": args.g2_registration_date,
        },
        "package_sha256_before_attestation": hashlib.sha256(
            base.encode("utf-8")
        ).hexdigest(),
        "attested_at": datetime.now(timezone.utc).isoformat(),
        "pii_policy": "Reviewer reference only; no full name/contact/identity document.",
        "disclaimer": "Cần bác sĩ kiểm chứng.",
    }
    return G2Q.append_attestation(base, attestation), []


def main() -> int:
    configure_unicode_console()
    ap = argparse.ArgumentParser(description=__doc__.split("Dùng:")[0])
    ap.add_argument("--study", required=True, help="Tên đề tài (khớp thư mục exports/<tên>)")
    ap.add_argument(
        "--gate",
        required=True,
        choices=["G2", "G4", "G5", "G8", "G9", "G10", "GATE_A", "GATE_B"],
    )
    ap.add_argument("--artifact", required=True, help="File đại diện cho nội dung được duyệt (SAP/checkpoint/...)")
    ap.add_argument("--reviewer-role", required=True, help='vd "Chủ nhiệm đề tài", "Nghiên cứu viên chính"')
    ap.add_argument("--reviewer-ref", required=True,
                    help="Mã/tên viết tắt định danh người duyệt — KHÔNG ghi tên đầy đủ/CCCD/số điện thoại")
    ap.add_argument("--scope", default="", help="Mô tả ngắn phạm vi duyệt (tùy chọn)")
    ap.add_argument("--decision", default="APPROVED", choices=["APPROVED", "REJECTED", "CONDITIONAL"])
    # G2 hard gate: metadata chỉ bắt buộc khi ghi quyết định APPROVED. Agent
    # không được chạy lệnh này; người có thẩm quyền IRB tự nhập dữ kiện thật.
    # SỬA 2026-07-30 (audit toàn diện G0-G10, G2-F5): --reviewer-ref là định
    # danh NGƯỜI DUYỆT dùng CHUNG cho MỌI gate/vai trò (help text: "định danh
    # người duyệt"), không phải mã Hội đồng Đạo đức — trước đây ethics_
    # committee_ref luôn = reviewer_ref nên validate_attestation() kiểm
    # "không rỗng" vacuously PASS với bất kỳ giá trị reviewer_ref nào, kể cả
    # khi đó KHÔNG phải mã hội đồng thật. Cờ này TÙY CHỌN để tách biệt ngữ
    # nghĩa; thiếu thì fallback về reviewer_ref (giữ nguyên hành vi CLI cũ,
    # không phá vỡ test/luồng ký hiện có) và G2-AUTO-09 chỉ REVIEW nhắc bác
    # sĩ, không BLOCK cổng.
    ap.add_argument(
        "--g2-ethics-committee-ref",
        help="Mã/tên viết tắt Hội đồng Đạo đức đã duyệt (khác --reviewer-ref "
        "là định danh người duyệt chung); thiếu thì fallback về --reviewer-ref",
    )
    ap.add_argument("--g2-approval-number")
    ap.add_argument("--g2-approval-date")
    ap.add_argument("--g2-valid-until")
    ap.add_argument("--g2-no-expiry-confirmed", action="store_true")
    ap.add_argument("--g2-protocol-version")
    ap.add_argument("--g2-icf-version")
    ap.add_argument("--g2-icf-waiver-approved", action="store_true")
    ap.add_argument(
        "--g2-ethics-decision",
        choices=["APPROVED", "EXEMPT", "WAIVER"],
    )
    ap.add_argument(
        "--g2-recruitment-mode",
        choices=[
            "PROSPECTIVE_NEW_PARTICIPANTS",
            "RETROSPECTIVE_SECONDARY_DATA",
            "NOT_APPLICABLE",
        ],
    )
    ap.add_argument(
        "--g2-registration-status",
        choices=["REGISTERED", "NOT_REQUIRED"],
    )
    ap.add_argument("--g2-registry")
    ap.add_argument("--g2-registration-id")
    ap.add_argument("--g2-registration-date")
    ap.add_argument("--g2-first-enrolment-date")
    ap.add_argument("--g2-first-search-date")
    ap.add_argument("--g2-approval-scope")
    args = ap.parse_args()

    artifact_path = Path(args.artifact)
    if not artifact_path.exists():
        print(f"✗ Không thấy file artifact: {artifact_path}")
        return 1
    if not GC.reviewer_role_satisfies_gate(args.gate, args.reviewer_role):
        print(f"✗ Role người duyệt không đúng stakeholder bắt buộc cho {args.gate}.")
        print(f"   {args.gate} cần: {GC.required_reviewer_role_hint(args.gate)}")
        print("   Không ghi ledger để tránh cổng có approval nhưng sai thẩm quyền.")
        return 1
    study_dir = Path(__file__).resolve().parents[1] / "exports" / args.study
    if not study_dir.exists():
        print(f"✗ Không thấy thư mục đề tài: {study_dir}")
        return 1
    # RÀNG BUỘC HASH VÀO ĐÚNG BYTES TRÊN ĐĨA (vá 2026-07-09): make_human_approval tính
    # evidence_hash = sha256(evidence_content.encode("utf-8")), CÒN _ledger_approved ở
    # run_g6/run_g9/run_stats_analysis kiểm sha256(artifact_path.read_bytes()). Hai bên
    # CHỈ khớp khi content.encode("utf-8") == bytes gốc. read_text(errors="replace") cũ
    # có thể thay byte hỏng bằng U+FFFD → hash lệch ÂM THẦM (bác sĩ duyệt thật mà cổng
    # vẫn báo "chưa duyệt" — fail-closed nhưng khó hiểu, nhất là repo đồng bộ Mac↔Windows
    # dễ dính BOM). Nay decode STRICT: file UTF-8 hợp lệ (kể cả có BOM) round-trip đúng
    # byte; file KHÔNG phải UTF-8 → báo lỗi RÕ thay vì tạo hash lệch (fail loud > fail silent).
    try:
        evidence_content = artifact_path.read_bytes().decode("utf-8")
    except UnicodeDecodeError:
        print(f"✗ Artifact không phải UTF-8 hợp lệ, không thể ràng buộc hash an toàn: {artifact_path}")
        print("   (Kiểm tra lại encoding file — mọi artifact pipeline phải là UTF-8 không BOM.)")
        return 1

    if args.gate == "G2" and args.decision == "APPROVED":
        prepared, g2_errors = _prepare_g2_attestation(
            args,
            artifact_path,
            evidence_content,
            study_dir,
        )
        if g2_errors:
            print("✗ TỪ CHỐI ký G2 — hồ sơ/metadata phê duyệt chưa đủ:")
            for item in g2_errors:
                print(f"   - {item}")
            print("   Không ghi ledger và không tự suy diễn quyết định IRB.")
            return 1
        evidence_content = prepared or evidence_content
        artifact_path.write_text(evidence_content, encoding="utf-8", newline="\n")

    if args.gate == "G4":
        still_draft = _g4_sections_still_draft(evidence_content)
        if still_draft:
            print("✗ TỪ CHỐI ký G4 — SAP còn placeholder '[CẦN' chưa điền ở mục bắt buộc:")
            for item in still_draft:
                print(f"   - {item}")
            print("   Bác sĩ/thống kê viên PHẢI điền đầy đủ các mục này TRƯỚC khi ký khóa G4")
            print("   (khóa mật mã bảo vệ TÍNH TOÀN VẸN nội dung, không tự đảm bảo nội dung có ý nghĩa).")
            print("   Không ghi ledger để tránh SAP rỗng bị coi là đã khóa.")
            return 1

    if args.gate == "G5" and args.decision == "APPROVED":
        expected_artifact = study_dir / "G5_checkpoint.json"
        try:
            artifact_matches = (
                artifact_path.resolve() == expected_artifact.resolve()
            )
        except OSError:
            artifact_matches = False
        if not artifact_matches:
            print(
                "✗ TỪ CHỐI ký G5 — artifact phải là "
                f"{expected_artifact.name} trong đúng thư mục đề tài."
            )
            print("   Không cho dùng file tự chọn để thay thế hồ sơ khóa dữ liệu.")
            return 1
        try:
            g5_report = G5Q.evaluate_study(
                args.study,
                study_dir,
                repo_root=Path(__file__).resolve().parents[1],
                write=False,
            )
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print(f"✗ TỪ CHỐI ký G5 — không thẩm định được hồ sơ: {exc}")
            return 1
        if g5_report.get("status") != G5Q.STATUS_READY:
            print(
                "✗ TỪ CHỐI ký G5 — hồ sơ chưa ở trạng thái "
                f"{G5Q.STATUS_READY}."
            )
            print(f"   Trạng thái hiện tại: {g5_report.get('status', 'UNKNOWN')}")
            blocked = [
                item
                for item in g5_report.get("automatic_criteria", [])
                if item.get("status") == "BLOCK"
            ]
            for item in blocked[:10]:
                print(
                    f"   - {item.get('id')}: {item.get('label')} "
                    f"({item.get('evidence')})"
                )
            print("   Không ghi ledger; phải xử lý hết lỗi dữ liệu trước.")
            return 1

    if args.gate == "G9" and args.decision == "APPROVED":
        expected_artifact = study_dir / G9Q.CHECKPOINT_JSON
        try:
            artifact_matches = artifact_path.resolve() == expected_artifact.resolve()
        except OSError:
            artifact_matches = False
        if not artifact_matches:
            print(
                "✗ TỪ CHỐI ký G9 — artifact phải là "
                f"{expected_artifact.name} trong đúng thư mục đề tài."
            )
            print("   Gói A10 riêng lẻ không ràng buộc manuscript/readiness/G8/A12.")
            return 1
        try:
            g9_report = G9Q.evaluate_study(
                args.study,
                study_dir,
                repo_root=Path(__file__).resolve().parents[1],
                write=False,
            )
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print(f"✗ TỪ CHỐI ký G9 — không thẩm định được hồ sơ: {exc}")
            return 1
        if g9_report.get("status") != G9Q.STATUS_READY:
            print(
                "✗ TỪ CHỐI ký G9 — hồ sơ chưa ở trạng thái "
                f"{G9Q.STATUS_READY}."
            )
            print(f"   Trạng thái hiện tại: {g9_report.get('status', 'UNKNOWN')}")
            for item in g9_report.get("automatic_criteria", []):
                if item.get("status") != "PASS":
                    print(
                        f"   - {item.get('id')}: {item.get('label')} "
                        f"({item.get('evidence')})"
                    )
            print("   Không ghi ledger; PI phải kiểm đủ form thật của từng tác giả.")
            return 1

    if args.gate == "G10" and args.decision == "APPROVED":
        expected_artifact = study_dir / G10Q.CHECKPOINT_JSON
        try:
            artifact_matches = artifact_path.resolve() == expected_artifact.resolve()
        except OSError:
            artifact_matches = False
        if not artifact_matches:
            print(
                "✗ TỪ CHỐI ký G10 — artifact phải là "
                f"{expected_artifact.name} trong đúng thư mục đề tài."
            )
            print("   Chỉ checkpoint này ràng buộc manifest của toàn bộ gói phát hành.")
            return 1
        try:
            g10_report = G10Q.evaluate_study(
                args.study,
                study_dir,
                repo_root=Path(__file__).resolve().parents[1],
                write=False,
            )
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print(f"✗ TỪ CHỐI ký G10 — không thẩm định được gói cuối: {exc}")
            return 1
        if g10_report.get("status") != G10Q.STATUS_READY:
            print(
                "✗ TỪ CHỐI ký G10 — gói chưa ở trạng thái "
                f"{G10Q.STATUS_READY}."
            )
            print(f"   Trạng thái hiện tại: {g10_report.get('status', 'UNKNOWN')}")
            for item in g10_report.get("automatic_criteria", []):
                if item.get("status") != "PASS":
                    print(
                        f"   - {item.get('id')}: {item.get('label')} "
                        f"({item.get('evidence')})"
                    )
            print("   Không ghi ledger; PI phải rà đúng gói cuối và xử lý hết mục còn lại.")
            return 1
        # Dọn tín hiệu BLOCKED trước khi ký. Đây vẫn là thay đổi TRƯỚC chữ ký;
        # manifest G10 không chứa chính checkpoint nên không tạo vòng hash.
        # Sau bước này, hash ledger ràng buộc đúng bytes không còn needs_input cũ.
        try:
            g10_checkpoint = json.loads(artifact_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            print("✗ TỪ CHỐI ký G10 — không đọc được checkpoint để dọn trạng thái chờ.")
            return 1
        if not isinstance(g10_checkpoint, dict):
            print("✗ TỪ CHỐI ký G10 — checkpoint không phải JSON object.")
            return 1
        g10_checkpoint.pop("needs_input", None)
        g10_checkpoint["gate_status"] = G10Q.STATUS_READY
        artifact_path.write_text(
            json.dumps(g10_checkpoint, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        evidence_content = artifact_path.read_text(encoding="utf-8")

    ledger_path = study_dir / "approval_ledger.json"

    # Chữ ký (2026-07-12): cần evidence_hash + timestamp TRƯỚC khi ký (payload chữ ký
    # gồm cả hai) — tính thủ công ở đây thay vì để make_human_approval() tự sinh, để
    # ký ĐÚNG giá trị sẽ được ghi vào bản ghi (không lệch múi giờ/độ chính xác giây).
    import hashlib as _hashlib
    evidence_hash = _hashlib.sha256(evidence_content.encode("utf-8")).hexdigest()
    timestamp_utc = datetime.now(timezone.utc).isoformat()
    # VÁ 2026-07-26: truyền reviewer_role + reviewer_ref vào chữ ký. Trước đây payload
    # chỉ gồm gate/study/hash/timestamp, nên MỘT chữ ký hợp lệ dùng lại được cho BẤT KỲ
    # vai trò nào (đổi nhãn reviewer_role trong JSON là xong) — tách vai trò IRB/thống
    # kê/phản biện/PI chỉ tồn tại trên giấy. Nay role nằm trong nội dung được ký.
    role_group = GC.role_group_for(args.reviewer_role)
    # SỔ CÁI CHUỖI BĂM (v4, 2026-07-27): mắt xích = vân tay bản ghi ĐANG ĐỨNG CUỐI sổ cái.
    # Nhờ vậy, xóa/đảo/chèn bản ghi về sau sẽ làm đứt xích và bị phát hiện — điều mà chữ
    # ký một mình KHÔNG làm được (sổ cái bị cắt bớt trông y hệt sổ cái ngắn). Đọc ở đây
    # thay vì trong locked_update để ký ĐÚNG giá trị sẽ ghi; nếu có tiến trình khác chen
    # vào giữa, khóa file sẽ xếp hàng và lần chạy này ghi tiếp vào đuôi mới.
    try:
        _existing = json.loads(ledger_path.read_text(encoding="utf-8")) if ledger_path.exists() else []
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        _existing = []
    _prev = _existing[-1] if isinstance(_existing, list) and _existing else None
    prev_hash = GC.chain_prev_hash(_prev if isinstance(_prev, dict) else None)
    # decision NẰM TRONG payload từ v3 (2026-07-27): trước đây ký mà không gồm quyết định,
    # nên một bản ghi REJECTED đã ký hợp lệ chỉ cần sửa chuỗi thành APPROVED là qua cổng.
    signature = GC.sign_approval(args.gate, args.study, evidence_hash, timestamp_utc,
                                 reviewer_role=args.reviewer_role, reviewer_ref=args.reviewer_ref,
                                 decision=args.decision, is_synthetic=False,
                                 prev_hash=prev_hash)
    if signature:
        if GC.per_role_key_available(role_group or ""):
            print(f"🔑 Đã ký bằng KHÓA RIÊNG của nhóm {role_group} "
                  f"(~/.ebm-secrets/gate_approval_key_{role_group}).")
            # SỬA 2026-07-26 vòng 2: dòng này TỪNG ghi "bằng chứng TÁCH VAI TRÒ thật" —
            # red-team độc lập chỉ ra là NÓI QUÁ. HMAC đối xứng: máy này xác minh được
            # nghĩa là chính nó đang giữ khóa đó, nên không thể loại trừ khả năng chủ
            # nhiệm đề tài tự ký. Nói đúng mức bảo đảm thay vì trấn an.
            print("   → Tách bạch VẬN HÀNH: khóa riêng cho vai trò này, không dùng chung với vai trò khác.")
            print("   ⚠️  KHÔNG phải bằng chứng mật mã về tính độc lập: máy này xác minh được")
            print("      nghĩa là chính nó đang giữ khóa đó. Bảo đảm độc lập thật cần chữ ký")
            print("      bất đối xứng (người duyệt giữ khóa riêng, máy chỉ giữ khóa công).")
        else:
            print("🔑 Đã ký bằng khóa CHUNG của máy (~/.ebm-secrets/gate_approval_key).")
            print("   ⚠️  GIỚI HẠN THẬT — nói rõ để không hiểu nhầm mức bảo đảm: khóa chung ký được")
            print("      MỌI vai trò, nên chữ ký này CHỨNG MINH 'có người truy cập được máy đã ký',")
            print("      KHÔNG chứng minh người ký độc lập với chủ nhiệm đề tài.")
            if role_group in ("IRB", "INDEPENDENT_PEER_REVIEWER"):
                print(f"      Với {args.gate} ({role_group}) — vai trò BẮT BUỘC phải độc lập — muốn có")
                print("      bằng chứng tách vai trò thật, tạo khóa riêng cho người duyệt đó:")
                print(f"      python3 tools/setup_gate_approval_key.py --role {role_group}")
    else:
        print("⚠️  CHƯA THIẾT LẬP KHÓA KÝ — phê duyệt này KHÔNG có chữ ký mật mã.")
        print("   Chạy MỘT LẦN (TỰ TAY, không nhờ agent): python3 tools/setup_gate_approval_key.py")
        print("   ⚠️  SỬA 2026-07-26: phê duyệt KHÔNG chữ ký nay KHÔNG còn được các cổng downstream")
        print("      coi là 'đã duyệt' (fail-closed), trừ đề tài đã đánh dấu synthetic_test.")

    # locked_update() khóa file độc quyền quanh load→mutate→save (thêm 2026-07-15
    # sau red-team đối kháng — vá lost-update race khi 2 tiến trình duyệt gần như
    # đồng thời trên cùng ledger; xem docstring ApprovalLedger.locked_update).
    # Bắt TimeoutError/LedgerLockInvalidated (thêm 2026-07-16, red-team vòng 2) —
    # đây là lỗi TẠM THỜI/hiếm (tiến trình khác đang giữ khóa, hoặc file .lock bị
    # xóa/thay giữa chừng), KHÔNG để traceback thô lộ ra — báo rõ để bác sĩ chạy lại.
    try:
        with ApprovalLedger.locked_update(ledger_path) as ledger:
            record = ApprovalLedger.make_human_approval(
                gate_id=args.gate,
                reviewer_role=args.reviewer_role,
                reviewer_ref=args.reviewer_ref,
                scope=args.scope or f"Duyệt {args.gate} cho đề tài {args.study}",
                evidence_content=evidence_content,
                decision=ApprovalDecisionEnum(args.decision),
                approver_signature=signature,
                timestamp_utc=timestamp_utc,
                # VÁ 2026-07-27: prev_hash PHẢI vào cả BẢN GHI, không chỉ vào chữ ký.
                # Trước đó nó được tính và đưa vào sign_approval() nhưng KHÔNG truyền
                # xuống make_human_approval(), nên bản ghi ghi ra đĩa có prev_hash=None
                # trong khi chữ ký lại tính theo prev_hash THẬT ⇒ từ bản ghi THỨ HAI trở
                # đi chữ ký KHÔNG XÁC MINH ĐƯỢC. Hệ quả: đường ký hợp lệ bị đóng hoàn
                # toàn — bác sĩ ký đúng quy trình mà cổng vẫn báo "chưa duyệt". Lỗi do
                # chính đợt thêm chuỗi băm hôm nay gây ra; phát hiện qua đánh giá độc lập.
                prev_hash=prev_hash,
            )
            ok, reason = ledger.add_approval(record, created_by_agent=False)
    except (TimeoutError, LedgerLockInvalidated) as exc:
        print(f"✗ TỪ CHỐI ghi phê duyệt (khóa ledger): {exc}")
        print("   Đây là lỗi tạm thời — chạy lại chính xác lệnh này.")
        return 1
    if not ok:
        print(f"✗ TỪ CHỐI ghi phê duyệt: {reason}")
        return 1

    # Niêm phong lại sổ cái NGAY SAU khi ghi — con dấu (số bản ghi + vân tay đuôi, đã ký)
    # là mốc neo NGOÀI file, thứ duy nhất phát hiện được việc CẮT ĐUÔI sổ cái. Xem
    # gate_contract.write_ledger_seal().
    try:
        _sealed = GC.write_ledger_seal(
            args.study, json.loads(ledger_path.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        _sealed = False
    if _sealed:
        print("🔏 Đã niêm phong lại sổ cái (approval_ledger.seal.json) — chống cắt đuôi.")

    print(f"✅ Đã ghi phê duyệt THẬT cho {args.gate} — đề tài {args.study}")
    print(f"   approval_id : {record.approval_id}")
    print(f"   evidence_hash (SHA256 của {artifact_path.name}): {record.evidence_hash[:16]}…")
    print(f"   Ghi vào     : {ledger_path}")
    print("   ⚠️  Nếu file artifact bị sửa SAU thời điểm này, phê duyệt sẽ KHÔNG còn khớp hash")
    print("      (lần kiểm tiếp theo sẽ coi như chưa duyệt) — đúng ý nghĩa ràng buộc mật mã.")
    if args.gate == "G2":
        try:
            report = G2Q.evaluate_study(
                args.study,
                study_dir,
                repo_root=Path(__file__).resolve().parents[1],
                write=True,
            )
            print(f"   G2 quality status: {report['status']}")
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print(f"⚠️  Đã ghi ledger nhưng chưa cập nhật được G2 quality report: {exc}")
    elif args.gate == "G4":
        try:
            report = G4Q.evaluate_study(
                args.study,
                study_dir,
                repo_root=Path(__file__).resolve().parents[1],
                write=True,
            )
            print(f"   G4 quality status: {report['status']}")
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print(f"⚠️  Đã ghi ledger nhưng chưa cập nhật được G4 quality report: {exc}")
    elif args.gate == "G5":
        try:
            report = G5Q.evaluate_study(
                args.study,
                study_dir,
                repo_root=Path(__file__).resolve().parents[1],
                write=True,
            )
            print(f"   G5 quality status: {report['status']}")
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print(f"⚠️  Đã ghi ledger nhưng chưa cập nhật được G5 quality report: {exc}")
    elif args.gate == "G9":
        try:
            report = G9Q.evaluate_study(
                args.study,
                study_dir,
                repo_root=Path(__file__).resolve().parents[1],
                write=True,
            )
            print(f"   G9 quality status: {report['status']}")
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print(f"⚠️  Đã ghi ledger nhưng chưa cập nhật được G9 quality report: {exc}")
    elif args.gate == "G10":
        try:
            report = G10Q.evaluate_study(
                args.study,
                study_dir,
                repo_root=Path(__file__).resolve().parents[1],
                write=True,
            )
            print(f"   G10 quality status: {report['status']}")
            print("   Việc nộp bên ngoài: CHƯA được G10 thực hiện hoặc chứng minh.")
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print(f"⚠️  Đã ghi ledger nhưng chưa cập nhật được G10 quality report: {exc}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
