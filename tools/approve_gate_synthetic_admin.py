#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
approve_gate_synthetic_admin.py — BƯỚC 2/2 của cơ chế "admin phê duyệt toàn
quyền CHỈ cho dữ liệu tổng hợp/thử nghiệm" (2026-07-15, theo yêu cầu bác sĩ).

★ KHÁC tools/approve_gate.py (CLI thật, dành cho đề tài người thật, MỖI LẦN
gọi là MỘT quyết định có chủ ý của MỘT stakeholder cụ thể — IRB ký G2, thống
kê viên/PI ký G4, phản biện độc lập ký G8, PI ký G9): script NÀY cho một
danh tính DUY NHẤT (ADMIN_SYNTHETIC_BYPASS_TOOL — không phải người, không PII)
tự ký MỌI vai trò cho MỌI cổng — kể cả G2 (IRB) và G8 (phản biện độc lập), thứ
mà approve_gate.py cố tình không cho phép PI tự làm. Đây CHÍNH LÀ "quyền phê
duyệt tất cả" bác sĩ yêu cầu, nhưng bị khóa cứng CHỈ hoạt động trên đề tài đã
được tools/mark_study_synthetic.py đánh dấu tường minh study_kind=synthetic_test.

An toàn — 3 lớp kiểm tra, TẤT CẢ phải qua (không lớp nào một mình là đủ):
  1. exports/<study>/ tồn tại.
  2. gate_contract.is_real_study_denylisted(study) == False — KHÔNG cờ nào
     bỏ qua được (kể cả --i-confirm-... dưới đây).
  3. study_meta.json["study_kind"] == "synthetic_test" CHÍNH XÁC (đặt bởi
     tools/mark_study_synthetic.py, KHÔNG phải script này tự đặt).
  + Cờ --i-confirm-synthetic-admin-bypass bắt buộc (không có giá trị an toàn
    kỹ thuật thêm — mục đích là buộc người/agent gọi phải ĐỌC docstring này
    trước khi tự động hóa lệnh, giống quy ước --i-confirm-* đã có trong dự án).

Mỗi bản ghi ghi vào approval_ledger.json mang is_synthetic=False (để
gate_contract.ledger_approved() coi là ĐÃ DUYỆT — pipeline thực sự đi tiếp,
khác hẳn ledger.make_synthetic_approval() dùng cho mô phỏng RBAC, thứ CỐ TÌNH
is_synthetic=True để KHÔNG BAO GIỜ mở được cổng thật) nhưng field `scope` LUÔN
mang tiền tố [ADMIN-SYNTHETIC-BYPASS] để không thể nhầm là phê duyệt người
thật khi đọc lại ledger sau này.

Dùng:
    python3 tools/approve_gate_synthetic_admin.py --study TEST-ADMIN-BYPASS-DEMO \\
        --i-confirm-synthetic-admin-bypass
    # mặc định duyệt cả 4 cổng G2,G4,G8,G9. Giới hạn phạm vi:
    python3 tools/approve_gate_synthetic_admin.py --study TEST-ADMIN-BYPASS-DEMO \\
        --gates G2,G8 --i-confirm-synthetic-admin-bypass
    # cung cấp artifact có sẵn thay vì tự sinh evidence giả lập:
    python3 tools/approve_gate_synthetic_admin.py --study TEST-ADMIN-BYPASS-DEMO \\
        --artifacts artifact_map.json --i-confirm-synthetic-admin-bypass
    # artifact_map.json: {"G2": "exports/.../G2_A3_ETHICS_PACKAGE_....md", ...}
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import gate_contract as GC  # noqa: E402

from app.utils.console import configure_unicode_console  # noqa: E402
from runtime.approval_ledger import ApprovalLedger, LedgerLockInvalidated  # noqa: E402
from runtime.schemas import ApprovalDecisionEnum  # noqa: E402

ALL_GATES = ("G2", "G4", "G8", "G9")

# Role tự-ký cho mỗi cổng — chọn nhóm ĐẦU TIÊN được _GATE_REQUIRED_STAKEHOLDERS
# chấp nhận (khớp gate_contract.py, không hardcode song song bảng riêng).
_ROLE_FOR_GATE = {
    "G2": "IRB",
    "G4": "PI",
    "G8": "INDEPENDENT_PEER_REVIEWER",
    "G9": "PI",
}

_REVIEWER_REF = "ADMIN_SYNTHETIC_BYPASS_TOOL"  # không phải người — không PII


def _placeholder_evidence(study: str, gate_id: str) -> str:
    return (
        f"# [ADMIN-SYNTHETIC-BYPASS] Bằng chứng giả lập cho cổng {gate_id}\n\n"
        f"Đề tài: {study}\n"
        f"Sinh tự động bởi tools/approve_gate_synthetic_admin.py.\n\n"
        "File này KHÔNG phải hồ sơ đạo đức/SAP/phản biện/liêm chính THẬT — chỉ tồn tại để "
        "ràng buộc hash cho một phê duyệt admin-bypass trên đề tài tổng hợp/thử nghiệm "
        f"(study_meta.json[\"study_kind\"] == \"synthetic_test\"). Cổng {gate_id} của đề tài "
        "này KHÔNG được một " + GC.required_reviewer_role_hint(gate_id) + " THẬT xem xét.\n"
    )


def main() -> int:
    configure_unicode_console()
    ap = argparse.ArgumentParser(description=__doc__.split("Dùng:")[0])
    ap.add_argument("--study", required=True, help="Tên đề tài (khớp thư mục exports/<tên>)")
    ap.add_argument("--gates", default=",".join(ALL_GATES),
                    help=f"Danh sách cổng phân cách dấu phẩy, mặc định {','.join(ALL_GATES)}")
    ap.add_argument("--artifacts", default=None,
                    help="File JSON map gate_id -> đường dẫn artifact có sẵn (tùy chọn; "
                         "thiếu gate nào thì tự sinh evidence giả lập cho gate đó)")
    ap.add_argument("--i-confirm-synthetic-admin-bypass", dest="confirm", action="store_true",
                    help="Bắt buộc — xác nhận đã đọc docstring, hiểu đây là admin-bypass "
                         "CHỈ hợp lệ cho dữ liệu tổng hợp/thử nghiệm")
    args = ap.parse_args()

    gates = [g.strip().upper() for g in args.gates.split(",") if g.strip()]
    unknown = [g for g in gates if g not in ALL_GATES]
    if unknown:
        print(f"✗ Cổng không hợp lệ: {unknown} — chỉ chấp nhận {ALL_GATES}")
        return 1

    if not args.confirm:
        print("✗ Thiếu cờ xác nhận bắt buộc: --i-confirm-synthetic-admin-bypass")
        return 1

    repo_root = Path(__file__).resolve().parents[1]

    # Lớp phòng thủ 1 (CONTAINMENT + DENYLIST + TOCTOU): chốt an toàn dùng chung
    # gate_contract.resolve_synthetic_study_dir — trả về đường dẫn CANONICAL đã
    # resolve toàn bộ symlink, đồng thời từ chối denylist / path thoát exports/ /
    # chuỗi rỗng. MỌI I/O bên dưới dùng study_dir = real_dir này (KHÔNG dùng lại
    # Path chưa resolve — đóng TOCTOU symlink race red-team tái hiện được 2026-07-15).
    real_dir, err = GC.resolve_synthetic_study_dir(args.study, repo_root)
    if err:
        print(f"✗ TỪ CHỐI: {err}")
        if "REAL_STUDY_DENYLIST" in err:
            print("   Admin-bypass KHÔNG BAO GIỜ chạm tới đề tài người thật, bất kể study_meta ghi gì.")
        return 1
    study_dir = real_dir

    # Lớp phòng thủ 2: phải đã được đánh dấu TƯỜNG MINH bởi mark_study_synthetic.py.
    meta = GC.load_study_meta(study_dir)
    if meta.get("study_kind") != "synthetic_test":
        print(f"✗ TỪ CHỐI: '{args.study}' chưa được đánh dấu study_kind=synthetic_test.")
        print("   Chạy trước: python3 tools/mark_study_synthetic.py --study "
              f"{args.study} --i-confirm-this-is-synthetic-test-data-not-a-real-study")
        return 1

    artifact_map = {}
    if args.artifacts:
        try:
            artifact_map = json.loads(Path(args.artifacts).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"✗ Không đọc được --artifacts {args.artifacts}: {exc}")
            return 1
        # Giới hạn CONTAINMENT cho artifact do người dùng chỉ định: phải nằm TRONG
        # thư mục đề tài synthetic này (defense-in-depth — red-team xác nhận việc
        # hash file ngoài là vô hại với bất biến, nhưng chặn để không vô tình hash
        # một tài liệu đề tài THẬT vào ledger synthetic, gây khó phân biệt khi audit).
        for gid, apath in list(artifact_map.items()):
            try:
                ar = Path(apath).resolve(strict=True)
            except (OSError, RuntimeError, ValueError):
                print(f"✗ [{gid}] --artifacts trỏ tới file không tồn tại/không giải được: {apath}")
                return 1
            if study_dir not in ar.parents and ar.parent != study_dir:
                print(f"✗ [{gid}] --artifacts phải nằm TRONG thư mục đề tài {study_dir} — "
                      f"'{apath}' (→ {ar}) nằm ngoài. Từ chối để không hash tài liệu đề tài khác.")
                return 1

    print(f"⚠️  ADMIN-SYNTHETIC-BYPASS — đề tài '{args.study}' (xác nhận study_kind=synthetic_test)")
    print(f"   Sẽ tự duyệt {len(gates)} cổng: {gates} — KHÔNG PHẢI phê duyệt đạo đức/phản biện/")
    print("   thống kê THẬT. KHÔNG áp dụng ngoài dữ liệu tổng hợp/thử nghiệm.\n")

    ledger_path = study_dir / "approval_ledger.json"
    # QUAN TRỌNG: dùng TÊN CANONICAL (study_dir.name = real_dir.name) cho chữ ký +
    # thông điệp, KHÔNG dùng args.study thô — vì chữ ký HMAC bind theo tên đề tài
    # (gate_contract._signature_payload) và downstream ledger_approved()/run_g9_auto.py
    # dựng đường dẫn từ TÊN THƯ MỤC. Nếu người dùng nhập biến thể path ("TÊN/" hay
    # "./TÊN"), args.study khác tên thư mục → chữ ký sẽ lệch khi verify lại. Tên
    # canonical khớp cả 2 phía.
    study_name = study_dir.name
    # locked_update() khóa file độc quyền quanh TRỌN chu trình load→mutate→save
    # (thêm 2026-07-15 sau red-team đối kháng — đóng lost-update race khi 2 tiến
    # trình duyệt gần như đồng thời trên cùng ledger, kể cả khi tiến trình kia là
    # tools/approve_gate.py thật). Vẫn nạp 1 lần/ghi 1 lần cho MỌI cổng trong 1
    # lệnh gọi (giảm số lần lấy/nhả khóa), nhưng nay TRỌN khối nằm trong khóa.
    ok_count = 0
    try:
        with ApprovalLedger.locked_update(ledger_path) as ledger:
            ok_count = _approve_all_gates(ledger, gates, artifact_map, study_dir, study_name)
    except (TimeoutError, LedgerLockInvalidated) as exc:
        print(f"✗ TỪ CHỐI (khóa ledger): {exc}")
        print("   Đây là lỗi tạm thời — chạy lại chính xác lệnh này.")
        return 1

    print(f"\nHoàn tất: {ok_count}/{len(gates)} cổng đã ghi phê duyệt admin-bypass cho '{study_name}'.")
    print(f"Ledger: {ledger_path}")
    return 0 if ok_count == len(gates) else 1


def _approve_all_gates(ledger, gates, artifact_map, study_dir, study_name) -> int:
    ok_count = 0
    for gate_id in gates:
        artifact_str = artifact_map.get(gate_id)
        if artifact_str:
            artifact_path = Path(artifact_str)
            if not artifact_path.exists():
                print(f"✗ [{gate_id}] Không thấy artifact chỉ định: {artifact_path} — bỏ qua cổng này.")
                continue
            try:
                evidence_content = artifact_path.read_bytes().decode("utf-8")
            except UnicodeDecodeError:
                print(f"✗ [{gate_id}] Artifact không phải UTF-8 hợp lệ: {artifact_path} — bỏ qua.")
                continue
        else:
            bypass_dir = study_dir / "_admin_synthetic_bypass"
            bypass_dir.mkdir(parents=True, exist_ok=True)
            artifact_path = bypass_dir / f"{gate_id}_ADMIN_BYPASS_EVIDENCE.md"
            evidence_content = _placeholder_evidence(study_name, gate_id)
            # Preserve the exact bytes bound into the ledger hash. On Windows,
            # write_text() may translate "\n" to "\r\n", which makes the
            # on-disk hash differ from the signed evidence_content.
            artifact_path.write_bytes(evidence_content.encode("utf-8"))

        evidence_hash = hashlib.sha256(evidence_content.encode("utf-8")).hexdigest()
        timestamp_utc = datetime.now(timezone.utc).isoformat()
        signature = GC.sign_approval(gate_id, study_name, evidence_hash, timestamp_utc)

        role = _ROLE_FOR_GATE[gate_id]
        scope = (
            f"[ADMIN-SYNTHETIC-BYPASS] Tự động duyệt {gate_id} qua "
            "tools/approve_gate_synthetic_admin.py — CHỈ hợp lệ vì đề tài "
            f"'{study_name}' đã đánh dấu study_kind=synthetic_test (KHÔNG áp dụng cho đề tài "
            f"thật). KHÔNG PHẢI phê duyệt {GC.required_reviewer_role_hint(gate_id)} THẬT."
        )

        record = ApprovalLedger.make_human_approval(
            gate_id=gate_id,
            reviewer_role=role,
            reviewer_ref=_REVIEWER_REF,
            scope=scope,
            evidence_content=evidence_content,
            decision=ApprovalDecisionEnum.APPROVED,
            approver_signature=signature,
            timestamp_utc=timestamp_utc,
        )
        added, reason = ledger.add_approval(record, created_by_agent=False)
        if not added:
            print(f"✗ [{gate_id}] TỪ CHỐI ghi ledger: {reason}")
            continue
        sig_note = "có chữ ký HMAC" if signature else "CHƯA có chữ ký (chưa thiết lập khóa cục bộ)"
        print(f"✅ [{gate_id}] Ghi phê duyệt admin-bypass ({role}, {sig_note}) — "
              f"evidence_hash={record.evidence_hash[:16]}…")
        ok_count += 1
    return ok_count


if __name__ == "__main__":
    sys.exit(main())
