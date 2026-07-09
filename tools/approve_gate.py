#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
approve_gate.py — Ghi PHÊ DUYỆT THẬT (ràng buộc mật mã) cho một cổng G, vá 2026-07-08 (BL-06).

Bối cảnh: "runtime/approval_ledger.py::ApprovalLedger" đã có cơ chế chống Agent tự phê duyệt
(add_approval() chặn created_by_agent=True) + evidence_hash (SHA256 nội dung artifact tại thời
điểm duyệt) — nhưng CHƯA từng được nối vào các cổng CLI (run_g4_auto.py/run_g5_auto.py) vì lớp
đó chỉ sống TRONG BỘ NHỚ một tiến trình. Script này là điểm NHẬP DUY NHẤT để bác sĩ tự tay ghi
một phê duyệt THẬT — không phải agent tự động gọi trong pipeline (nếu agent gọi script này thay
bác sĩ, đó là VI PHẠM nguyên tắc — script chỉ kiểm tra kỹ thuật, không kiểm tra "ai đang gõ lệnh"
được, nên kỷ luật vận hành nằm ở việc CHỈ bác sĩ chạy lệnh này khi đã thật sự duyệt xong).

Dùng:
    python3 tools/approve_gate.py --study <tên> --gate G4 \\
        --artifact exports/<tên>/G4_A5_SAP_FINAL_<tên>.md \\
        --reviewer-role "Chủ nhiệm đề tài" --reviewer-ref "<mã/tên viết tắt, KHÔNG PII đầy đủ>"

Sau khi chạy: exports/<tên>/approval_ledger.json có thêm 1 dòng phê duyệt, evidence_hash =
SHA256 của ĐÚNG nội dung file --artifact TẠI THỜI ĐIỂM CHẠY LỆNH NÀY. Nếu artifact bị sửa SAU
khi duyệt, lần kiểm tiếp theo (run_g6_auto.py/run_g9_auto.py) sẽ thấy hash KHÔNG khớp → không
còn được coi là "đã khóa" nữa — đây chính là ý nghĩa "ràng buộc mật mã" (khác hoàn toàn so với
gõ tay "LOCKED" vào checkpoint, vốn không biết nội dung có bị đổi sau đó hay không).

KHÔNG dùng để tự động hóa duyệt hàng loạt — mỗi lần gọi là một hành động có chủ ý của một người.
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from runtime.approval_ledger import ApprovalLedger
from runtime.schemas import ApprovalDecisionEnum


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("Dùng:")[0])
    ap.add_argument("--study", required=True, help="Tên đề tài (khớp thư mục exports/<tên>)")
    ap.add_argument("--gate", required=True, choices=["G2", "G4", "G5", "G9", "GATE_A", "GATE_B"])
    ap.add_argument("--artifact", required=True, help="File đại diện cho nội dung được duyệt (SAP/checkpoint/...)")
    ap.add_argument("--reviewer-role", required=True, help='vd "Chủ nhiệm đề tài", "Nghiên cứu viên chính"')
    ap.add_argument("--reviewer-ref", required=True,
                    help="Mã/tên viết tắt định danh người duyệt — KHÔNG ghi tên đầy đủ/CCCD/số điện thoại")
    ap.add_argument("--scope", default="", help="Mô tả ngắn phạm vi duyệt (tùy chọn)")
    ap.add_argument("--decision", default="APPROVED", choices=["APPROVED", "REJECTED", "CONDITIONAL"])
    args = ap.parse_args()

    artifact_path = Path(args.artifact)
    if not artifact_path.exists():
        print(f"✗ Không thấy file artifact: {artifact_path}")
        return 1
    evidence_content = artifact_path.read_text(encoding="utf-8", errors="replace")

    study_dir = Path(__file__).resolve().parents[1] / "exports" / args.study
    if not study_dir.exists():
        print(f"✗ Không thấy thư mục đề tài: {study_dir}")
        return 1
    ledger_path = study_dir / "approval_ledger.json"

    ledger = ApprovalLedger.from_file(ledger_path)
    record = ApprovalLedger.make_human_approval(
        gate_id=args.gate,
        reviewer_role=args.reviewer_role,
        reviewer_ref=args.reviewer_ref,
        scope=args.scope or f"Duyệt {args.gate} cho đề tài {args.study}",
        evidence_content=evidence_content,
        decision=ApprovalDecisionEnum(args.decision),
    )
    ok, reason = ledger.add_approval(record, created_by_agent=False)
    if not ok:
        print(f"✗ TỪ CHỐI ghi phê duyệt: {reason}")
        return 1

    ledger.to_file(ledger_path)
    print(f"✅ Đã ghi phê duyệt THẬT cho {args.gate} — đề tài {args.study}")
    print(f"   approval_id : {record.approval_id}")
    print(f"   evidence_hash (SHA256 của {artifact_path.name}): {record.evidence_hash[:16]}…")
    print(f"   Ghi vào     : {ledger_path}")
    print("   ⚠️  Nếu file artifact bị sửa SAU thời điểm này, phê duyệt sẽ KHÔNG còn khớp hash")
    print("      (lần kiểm tiếp theo sẽ coi như chưa duyệt) — đúng ý nghĩa ràng buộc mật mã.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
