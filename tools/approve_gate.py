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

Role bắt buộc theo cổng (vá 2026-07-14 — nâng cấp kiểm soát PI/IRB/thống kê viên/
phản biện; G4 nới thêm PI vì doctrine hướng dẫn "Chủ nhiệm đề tài" tự ký khóa SAP
khi không có thống kê viên riêng; G8 mới thêm — trước đây bình duyệt không có cổng
cứng nào):
    G2  → IRB / IRB_ETHICS_COMMITTEE / ETHICS_COMMITTEE
    G4  → METHODS_STATISTICS_REVIEWER / BIOSTATISTICIAN / STATISTICIAN
          HOẶC PI / PI_PROJECT_OWNER / PRINCIPAL_INVESTIGATOR
    G8  → PHAN_BIEN / PEER_REVIEWER / EXTERNAL_REVIEWER (bình duyệt độc lập)
    G9  → PI / PI_PROJECT_OWNER / PRINCIPAL_INVESTIGATOR

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
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import gate_contract as GC

from app.utils.console import configure_unicode_console
from runtime.approval_ledger import ApprovalLedger, LedgerLockInvalidated
from runtime.schemas import ApprovalDecisionEnum

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


def main() -> int:
    configure_unicode_console()
    ap = argparse.ArgumentParser(description=__doc__.split("Dùng:")[0])
    ap.add_argument("--study", required=True, help="Tên đề tài (khớp thư mục exports/<tên>)")
    ap.add_argument("--gate", required=True, choices=["G2", "G4", "G5", "G8", "G9", "GATE_A", "GATE_B"])
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
    if not GC.reviewer_role_satisfies_gate(args.gate, args.reviewer_role):
        print(f"✗ Role người duyệt không đúng stakeholder bắt buộc cho {args.gate}.")
        print(f"   {args.gate} cần: {GC.required_reviewer_role_hint(args.gate)}")
        print("   Không ghi ledger để tránh cổng có approval nhưng sai thẩm quyền.")
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

    study_dir = Path(__file__).resolve().parents[1] / "exports" / args.study
    if not study_dir.exists():
        print(f"✗ Không thấy thư mục đề tài: {study_dir}")
        return 1
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
    # decision NẰM TRONG payload từ v3 (2026-07-27): trước đây ký mà không gồm quyết định,
    # nên một bản ghi REJECTED đã ký hợp lệ chỉ cần sửa chuỗi thành APPROVED là qua cổng.
    signature = GC.sign_approval(args.gate, args.study, evidence_hash, timestamp_utc,
                                 reviewer_role=args.reviewer_role, reviewer_ref=args.reviewer_ref,
                                 decision=args.decision, is_synthetic=False)
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
            )
            ok, reason = ledger.add_approval(record, created_by_agent=False)
    except (TimeoutError, LedgerLockInvalidated) as exc:
        print(f"✗ TỪ CHỐI ghi phê duyệt (khóa ledger): {exc}")
        print("   Đây là lỗi tạm thời — chạy lại chính xác lệnh này.")
        return 1
    if not ok:
        print(f"✗ TỪ CHỐI ghi phê duyệt: {reason}")
        return 1

    print(f"✅ Đã ghi phê duyệt THẬT cho {args.gate} — đề tài {args.study}")
    print(f"   approval_id : {record.approval_id}")
    print(f"   evidence_hash (SHA256 của {artifact_path.name}): {record.evidence_hash[:16]}…")
    print(f"   Ghi vào     : {ledger_path}")
    print("   ⚠️  Nếu file artifact bị sửa SAU thời điểm này, phê duyệt sẽ KHÔNG còn khớp hash")
    print("      (lần kiểm tiếp theo sẽ coi như chưa duyệt) — đúng ý nghĩa ràng buộc mật mã.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
