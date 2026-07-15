#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
stakeholder_review_audit.py — CLI CHỈ ĐỂ XEM trạng thái stakeholder approval
(G2/G4/G8/G9) của một đề tài, đối chiếu (nếu có thể) với lớp audit "mirror"
research_project/.

★ ĐÂY KHÔNG PHẢI CỔNG CHẶN. Không có script run_g*_auto.py nào gọi tới file
này — nó chỉ đọc lại và in ra trạng thái đã có, phục vụ bác sĩ/PI xem nhanh.
Nguồn sự thật duy nhất cho cổng THẬT vẫn là tools/gate_contract.py +
tools/approve_gate.py + tools/run_g*_auto.py (xem CLAUDE.md mục "5 nhánh mồ côi").

Vì sao có script này (bối cảnh 2026-07-15): "runtime/approval_ledger.py::ApprovalLedger"
là ledger THẬT (ghi bởi tools/approve_gate.py vào exports/<study>/approval_ledger.json).
research_project/ là một hệ "mirror" HOÀN TOÀN TÁCH RỜI (project_id riêng, thư mục
projects/<project_id>/ riêng, tự khai "NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE")
— nó có hàm get_controlled_review_readiness() đọc CÙNG MỘT approval_ledger (duck-typing
qua stakeholder_gate_status()) để tổng hợp thêm layer "review theo artifact/role", nhưng
milestone của nó chỉ biết G2/G4/G9 (chưa có G8 — một khoảng trống KHÁC, không thuộc phạm
vi vá lần này). Script này cho phép xem CẢ HAI lớp cùng lúc mà KHÔNG làm research_project/
trở thành một cổng thật thứ hai: mọi lỗi từ research_project/ (import hỏng, API đổi, thư
mục hỏng...) chỉ in cảnh báo rồi bỏ qua — nguồn sự thật để QUYẾT ĐỊNH (exit code) luôn là
ApprovalLedger thật, KHÔNG BAO GIỜ bị ảnh hưởng bởi kết quả research_project/.

Dùng:
    python3 tools/stakeholder_review_audit.py --study <tên đề tài>
    python3 tools/stakeholder_review_audit.py --study <tên đề tài> --gate G8

Exit code:
    0  Ledger chưa tồn tại (đề tài chưa có approval nào — KHÔNG phải lỗi), HOẶC
       mọi gate được hỏi đều satisfied=True theo ApprovalLedger thật.
    2  Ledger tồn tại nhưng có ÍT NHẤT 1 gate được hỏi chưa satisfied.
    (Không có exit 1 "lỗi" ở đây — script chỉ đọc, không có gì để "crash" theo
    nghĩa thao tác ghi; lỗi research_project/ được nuốt có chủ ý, xem trên.)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.utils.console import configure_unicode_console  # noqa: E402
from runtime.approval_ledger import (  # noqa: E402
    GATE_REQUIRED_STAKEHOLDERS,
    ApprovalLedger,
)

_ALL_GATES = tuple(sorted(GATE_REQUIRED_STAKEHOLDERS.keys()))
# Hôm nay = ("G2", "G4", "G8", "G9") — lấy ĐỘNG từ runtime/approval_ledger.py thay vì
# hard-code, để nếu sau này thêm gate mới vào bảng đó (và test parity ở
# tests/test_gate_contract_approval_ledger_stakeholder_parity.py vẫn xanh), script này
# tự động hỏi thêm gate mới mà không cần sửa tay.

_REPO_ROOT = Path(__file__).resolve().parents[1]


def _try_research_project_cross_check(study: str, approval_ledger: ApprovalLedger) -> dict:
    """Cố gắng đối chiếu với lớp mirror research_project/ — TOÀN BỘ thao tác (import +
    tìm project mirror qua ProjectRegistry + gọi get_controlled_review_readiness) nằm
    trong MỘT try/except bắt MỌI Exception. Không bao giờ raise ra ngoài; trả dict mô tả
    kết quả (never None) để caller in ra một cách nhất quán.

    KHÔNG import research_project Ở BẤT KỲ NƠI NÀO KHÁC ngoài hàm này trong cả repo —
    xem tests/test_stakeholder_review_audit.py::TestNoResearchProjectImportInRealGates.
    """
    try:
        from research_project.project_registry import ProjectRegistry

        projects_root = _REPO_ROOT / "projects"
        registry = ProjectRegistry(projects_root)
        if not registry.exists(study):
            return {
                "status": "SKIPPED_NO_MIRROR",
                "message": (
                    f"Không thấy project mirror 'projects/{study}/' — bỏ qua đối chiếu "
                    "research_project/ (đây là lớp PHỤ, không bắt buộc phải có)."
                ),
            }

        # Import muộn (chỉ khi chắc chắn có mirror để tránh phụ thuộc không cần thiết) —
        # vẫn nằm trong cùng try/except với phần còn lại.
        from research_project.project_review_operations import (
            get_controlled_review_readiness,
        )

        project_dir = projects_root / study
        readiness = get_controlled_review_readiness(project_dir, approval_ledger=approval_ledger)
        return {"status": "OK", "readiness": readiness}
    except Exception as exc:  # noqa: BLE001 — cố ý bắt MỌI lỗi, đây là lớp PHỤ không phải cổng thật
        return {
            "status": "ERROR",
            "message": (
                f"[CẢNH BÁO] Đối chiếu research_project/ thất bại ({type(exc).__name__}: {exc}) "
                "— bỏ qua, KHÔNG ảnh hưởng kết quả ApprovalLedger thật bên dưới."
            ),
        }


def _print_research_project_result(result: dict) -> None:
    status = result.get("status")
    if status == "SKIPPED_NO_MIRROR":
        print(f"[research_project/] {result['message']}")
    elif status == "ERROR":
        print(result["message"])
    elif status == "OK":
        readiness = result["readiness"]
        print("[research_project/] Đối chiếu lớp mirror THÀNH CÔNG (chỉ tham khảo, không phải cổng thật):")
        print(f"    overall_status: {readiness.get('overall_status')}")
        print(
            f"    milestones sẵn sàng: {readiness.get('milestone_ready_count')}/"
            f"{readiness.get('milestone_total')}"
        )
        for milestone in readiness.get("milestones", []):
            tag = "PASS" if milestone.get("ready") else "BLOCKED"
            print(f"    [{tag}] {milestone.get('milestone_id')} (gate {milestone.get('approval_gate_id')})")
    else:  # pragma: no cover — phòng thủ, không nên xảy ra
        print(f"[research_project/] Kết quả không xác định: {result}")


def _print_real_ledger_status(approval_ledger: ApprovalLedger, gates: tuple[str, ...]) -> bool:
    """In trạng thái THẬT (nguồn sự thật chính) cho từng gate. Trả True nếu TẤT CẢ
    gate được hỏi đều satisfied."""
    print("\n[ApprovalLedger — nguồn sự thật thật] Trạng thái stakeholder theo gate:")
    all_satisfied = True
    for gate_id in gates:
        status = approval_ledger.stakeholder_gate_status(gate_id)
        satisfied = bool(status.get("satisfied"))
        all_satisfied = all_satisfied and satisfied
        tag = "PASS" if satisfied else "BLOCKED"
        print(f"    [{tag}] {gate_id} — cần: {status.get('required_stakeholder')} — lý do: {status.get('reason')}")
        if satisfied:
            print(f"          approval_id={status.get('approval_id')} reviewer_role={status.get('reviewer_role')}")
    return all_satisfied


def main(argv: list[str] | None = None) -> int:
    configure_unicode_console()
    ap = argparse.ArgumentParser(
        description=(
            "Xem (KHÔNG chặn) trạng thái stakeholder approval G2/G4/G8/G9 của một đề tài. "
            "Không phải cổng — chỉ đọc lại ApprovalLedger thật."
        )
    )
    ap.add_argument("--study", required=True, help="Tên đề tài (khớp thư mục exports/<tên>)")
    ap.add_argument(
        "--gate",
        choices=list(_ALL_GATES),
        default=None,
        help="Chỉ xem một gate cụ thể; bỏ trống để xem cả " + "/".join(_ALL_GATES),
    )
    args = ap.parse_args(argv)

    gates = (args.gate,) if args.gate else _ALL_GATES

    ledger_path = _REPO_ROOT / "exports" / args.study / "approval_ledger.json"
    print(f"=== STAKEHOLDER REVIEW AUDIT — {args.study} ===")
    print(f"Ledger: {ledger_path}")

    if not ledger_path.exists():
        print(f"\nChưa có approval nào cho đề tài này ('{args.study}') — file ledger chưa tồn tại.")
        print("Đây KHÔNG phải lỗi, chỉ là đề tài chưa từng qua tools/approve_gate.py.")
        return 0

    approval_ledger = ApprovalLedger.from_file(ledger_path)

    # Bước 2 — lớp PHỤ research_project/ (fail-open, không ảnh hưởng exit code).
    rp_result = _try_research_project_cross_check(args.study, approval_ledger)
    _print_research_project_result(rp_result)

    # Bước 3 — nguồn sự thật CHÍNH, luôn chạy dù bước 2 thành công hay thất bại.
    all_satisfied = _print_real_ledger_status(approval_ledger, gates)

    print(
        "\nCần bác sĩ kiểm chứng. Script này CHỈ ĐỂ XEM — không có run_g*_auto.py nào "
        "gọi tới; không thay thế tools/approve_gate.py / tools/gate_contract.py."
    )
    return 0 if all_satisfied else 2


if __name__ == "__main__":
    sys.exit(main())
