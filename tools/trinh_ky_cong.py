#!/usr/bin/env python3
"""Trợ lý TRÌNH-KÝ cổng G2 (IRB) và G8 (phản biện độc lập) — người thật xác nhận.

Vì sao tồn tại (yêu cầu bác sĩ 01/09/2026): lệnh ký thật `approve_gate.py` đúng
nhưng khó dùng — riêng G2 có hơn 15 cờ, người duyệt không thể nhớ. Công cụ này
làm đúng ba việc: (1) THẨM TRA cổng đã tới lúc ký chưa và TRÌNH nội dung sắp ký
(đường dẫn + SHA256 artifact, phán quyết lớp chất lượng, danh sách còn thiếu);
(2) PHỎNG VẤN từng trường bằng tiếng Việt, không bịa mặc định cho bất kỳ dữ
kiện thật nào (số quyết định, ngày...) — bỏ trống trường bắt buộc là DỪNG;
(3) SOẠN trọn lệnh `approve_gate.py` rồi chỉ chạy sau khi người duyệt gõ đúng
câu xác nhận.

RANH GIỚI CỨNG — đọc trước khi sửa:
- Đây KHÔNG phải đường ký mới. Điểm nhập ghi sổ cái duy nhất vẫn là
  `approve_gate.py` (nó tự kiểm lại toàn bộ: quality gate, khoá, ledger).
  Công cụ này chỉ là người điền form; mọi từ chối của approve_gate giữ nguyên.
- CHỈ NGƯỜI DUYỆT TỰ CHẠY. Không nhờ agent (Claude Code/Codex) chạy hộ —
  cùng lý do với approve_gate. Rào máy: stdin không phải terminal (bị pipe/
  agent điều khiển) ⇒ từ chối chạy (mã 2), vì phỏng vấn mất nghĩa khi không
  có người thật trả lời.
- KHÔNG ký trước sự kiện thật: cổng chưa ở trạng thái ký được ⇒ in danh sách
  còn thiếu rồi DỪNG — đó chính là "đưa nội dung để bác sĩ xác nhận" ở pha
  chuẩn bị.

Cần bác sĩ kiểm chứng.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

BASE = Path(__file__).resolve().parents[1]
TOOLS = BASE / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

# Trạng thái quality-gate mà approve_gate chấp nhận cho từng cổng (chép đúng
# dây nối 24/08 trong approve_gate.py — đổi ở đó thì đổi ở đây theo).
KY_DUOC = {
    "G2": lambda st: not (st.startswith("BLOCKED") or st.startswith("DRAFT")),
    "G8": lambda st: st in {"PENDING_REAL_REVIEW_SIGNATURE", "PASS_G8_REVIEW_RECORDED"},
}
ROLE_THEO_GATE = {"G2": "IRB", "G8": "INDEPENDENT_PEER_REVIEWER"}


def hop_le_ngay(s: str) -> bool:
    """YYYY-MM-DD thật (không nhận 2026-13-40)."""
    try:
        date.fromisoformat(s)
        return True
    except ValueError:
        return False


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def doc_design_code(study_dir: Path) -> str:
    """Đọc design_code từ G2_checkpoint.json — logic khớp NGUYÊN VĂN
    approve_gate.py (đổi ở đó thì đổi ở đây theo).

    SỬA vòng 25 (2026-09-05, phát hiện #2): trước bản vá, phong_van_g2()
    không hề biết design_code nên không bao giờ hỏi --g2-first-search-date —
    trường mà approve_gate.py BẮT BUỘC khi design_code == "sr_ma". Hậu quả:
    người ký một đề tài SR/MA trả lời hết toàn bộ phỏng vấn (10+ câu), gõ
    đúng "KY THAT", rồi mới bị approve_gate từ chối ở PHÚT CHÓT vì thiếu
    đúng cờ mà trợ lý trình-ký lẽ ra phải hỏi từ đầu.
    """
    try:
        checkpoint = json.loads((study_dir / "G2_checkpoint.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        checkpoint = {}
    return str(checkpoint.get("design_code") if isinstance(checkpoint, dict) else "").strip()


def soan_lenh(gate: str, study: str, artifact: Path, tra_loi: dict) -> list:
    """Soạn vector đối số approve_gate từ câu trả lời phỏng vấn (thuần, test được).

    Chỉ truyền cờ có giá trị — cặp loại trừ nhau (valid-until/no-expiry,
    icf-version/waiver) do NGƯỜI chọn một trong hai ở khâu phỏng vấn;
    approve_gate vẫn là trọng tài cuối.
    """
    lenh = [
        sys.executable, str(TOOLS / "approve_gate.py"),
        "--study", study, "--gate", gate,
        "--artifact", str(artifact),
        "--reviewer-role", ROLE_THEO_GATE[gate],
        "--reviewer-ref", tra_loi["reviewer_ref"],
        "--decision", tra_loi.get("decision", "APPROVED"),
    ]
    if gate == "G2":
        don_gian = [
            ("g2_ethics_committee_ref", "--g2-ethics-committee-ref"),
            ("g2_approval_number", "--g2-approval-number"),
            ("g2_approval_date", "--g2-approval-date"),
            ("g2_protocol_version", "--g2-protocol-version"),
            ("g2_ethics_decision", "--g2-ethics-decision"),
            ("g2_recruitment_mode", "--g2-recruitment-mode"),
            ("g2_registration_status", "--g2-registration-status"),
            ("g2_registry", "--g2-registry"),
            ("g2_registration_id", "--g2-registration-id"),
            ("g2_registration_date", "--g2-registration-date"),
            ("g2_valid_until", "--g2-valid-until"),
            ("g2_icf_version", "--g2-icf-version"),
            ("g2_approval_scope", "--g2-approval-scope"),
            ("g2_first_search_date", "--g2-first-search-date"),
        ]
        for khoa, co in don_gian:
            gia_tri = str(tra_loi.get(khoa, "") or "").strip()
            if gia_tri:
                lenh += [co, gia_tri]
        if tra_loi.get("g2_no_expiry_confirmed"):
            lenh.append("--g2-no-expiry-confirmed")
        if tra_loi.get("g2_icf_waiver_approved"):
            lenh.append("--g2-icf-waiver-approved")
    return lenh


def _hoi(cau: str, bat_buoc: bool = True, kiem=None) -> str:
    while True:
        try:
            gia_tri = input(f"  {cau}: ").strip()
        except EOFError:
            print("\n  ⛔ Mất kênh nhập (EOF) — không có người thật trả lời. Dừng, không ký.")
            raise SystemExit(2) from None
        if not gia_tri:
            if not bat_buoc:
                return ""
            print("  ⛔ Trường bắt buộc — không được bỏ trống (không bịa hộ).")
            print("     Chưa có dữ kiện thật thì DỪNG ở đây, quay lại khi có.")
            raise SystemExit(2)
        if kiem and not kiem(gia_tri):
            print("  ✗ Không hợp lệ, nhập lại (ngày theo YYYY-MM-DD).")
            continue
        return gia_tri


def _hoi_chon(cau: str, lua_chon: list) -> str:
    print(f"  {cau}:")
    for i, lc in enumerate(lua_chon, 1):
        print(f"    {i}) {lc}")
    while True:
        try:
            so = input("  Chọn số: ").strip()
        except EOFError:
            print("\n  ⛔ Mất kênh nhập (EOF) — không có người thật trả lời. Dừng, không ký.")
            raise SystemExit(2) from None
        if so.isdigit() and 1 <= int(so) <= len(lua_chon):
            return lua_chon[int(so) - 1]
        print("  ✗ Gõ đúng một số trong danh sách.")


def phong_van_g2(study_dir: Path) -> dict:
    print("\n── PHỎNG VẤN G2 — chép ĐÚNG từ quyết định của Hội đồng, không suy đoán ──")
    tl: dict = {}
    tl["reviewer_ref"] = _hoi("Người ký (tên/mã định danh, vd HĐĐĐ-BVQY175/Nguyễn Văn A)")
    tl["g2_ethics_committee_ref"] = _hoi("Tên/mã Hội đồng đạo đức")
    tl["g2_approval_number"] = _hoi("SỐ quyết định phê duyệt")
    tl["g2_approval_date"] = _hoi("NGÀY phê duyệt (YYYY-MM-DD)", kiem=hop_le_ngay)
    tl["g2_ethics_decision"] = _hoi_chon("Loại quyết định", ["APPROVED", "EXEMPT", "WAIVER"])
    tl["g2_protocol_version"] = _hoi("Phiên bản đề cương được duyệt (vd v1.1)")
    if _hoi_chon("Hiệu lực quyết định", ["Có ngày hết hiệu lực", "Không ghi hạn (xác nhận)"]) \
            == "Có ngày hết hiệu lực":
        tl["g2_valid_until"] = _hoi("Hiệu lực đến (YYYY-MM-DD)", kiem=hop_le_ngay)
    else:
        tl["g2_no_expiry_confirmed"] = True
    if _hoi_chon("Phiếu đồng thuận (ICF)", ["Có phiên bản ICF được duyệt", "Được MIỄN ICF"]) \
            == "Có phiên bản ICF được duyệt":
        tl["g2_icf_version"] = _hoi("Phiên bản ICF (vd v1.0)")
    else:
        tl["g2_icf_waiver_approved"] = True
    tl["g2_recruitment_mode"] = _hoi_chon(
        "Kiểu tuyển mẫu",
        ["PROSPECTIVE_NEW_PARTICIPANTS", "RETROSPECTIVE_SECONDARY_DATA", "NOT_APPLICABLE"],
    )
    if tl["g2_recruitment_mode"] == "PROSPECTIVE_NEW_PARTICIPANTS":
        tl["g2_registration_status"] = "REGISTERED"
        tl["g2_registry"] = _hoi("Registry đã đăng ký (vd OSF Registries)")
        tl["g2_registration_id"] = _hoi("Mã đăng ký")
        tl["g2_registration_date"] = _hoi("Ngày đăng ký (YYYY-MM-DD)", kiem=hop_le_ngay)
    else:
        tl["g2_registration_status"] = "NOT_REQUIRED"
    if doc_design_code(study_dir) == "sr_ma":
        tl["g2_first_search_date"] = _hoi(
            "SR/MA — ngày BẮT ĐẦU tìm kiếm y văn hệ thống (YYYY-MM-DD, mốc PROSPERO/protocol)",
            kiem=hop_le_ngay,
        )
    tl["g2_approval_scope"] = _hoi("Phạm vi phê duyệt (Enter để bỏ qua)", bat_buoc=False)
    return tl


def phong_van_g8() -> dict:
    print("\n── PHỎNG VẤN G8 — chỉ ký khi bản nhận xét phản biện THẬT đã tồn tại ──")
    tl: dict = {}
    tl["reviewer_ref"] = _hoi("Người phản biện (tên/mã định danh)")
    tl["decision"] = _hoi_chon("Kết luận bình duyệt", ["APPROVED", "CONDITIONAL", "REJECTED"])
    return tl


def main() -> int:
    ap = argparse.ArgumentParser(description="Trợ lý trình-ký G2 (IRB) / G8 (phản biện)")
    ap.add_argument("--study", required=True, help="Mã đề tài (thư mục trong exports/)")
    ap.add_argument("--gate", required=True, choices=["G2", "G8"])
    args = ap.parse_args()

    # Rào người-thật: đòi CẢ stdin LẪN stdout là terminal. Chỉ kiểm stdin là
    # FAIL-OPEN trên Windows — đo thật trên CI 01/09/2026: thiết bị NUL là
    # character device nên isatty(stdin=DEVNULL) trả True và tool chạy tiếp
    # (đúng họ BH05 "chạy được ở đây ≠ chạy được ở kia"). Agent/pipe luôn bắt
    # output nên stdout-không-phải-tty chặn được nhánh đó trên mọi nền; nhánh
    # NUL-cả-hai-đầu còn lại chết ở EOF của input() (đã fail-closed trong _hoi).
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        print("⛔ Phiên không tương tác (stdin/stdout bị pipe hoặc agent điều khiển).")
        print("   Trợ lý trình-ký chỉ chạy khi NGƯỜI DUYỆT ngồi tại bàn phím —")
        print("   đó là toàn bộ giá trị của chữ ký. Mở Terminal và tự chạy.")
        return 2

    study_dir = BASE / "exports" / args.study
    ten_artifact = {
        "G2": f"G2_A3_ETHICS_PACKAGE_{args.study}.md",
        "G8": f"G8_A9_PRESUBMISSION_{args.study}.md",
    }[args.gate]
    artifact = study_dir / ten_artifact
    if not artifact.exists():
        print(f"⛔ Chưa có artifact {ten_artifact} — chạy run_{args.gate.lower()}_auto.py trước.")
        return 2

    # ── Bước 1: THẨM TRA — cổng đã tới lúc ký chưa ──────────────────────────
    if args.gate == "G2":
        import g2_quality_gate as GQ
    else:
        import g8_quality_gate as GQ
    bao_cao = GQ.evaluate_study(args.study, study_dir, write=False)
    trang_thai = str(bao_cao.get("status", ""))
    print(f"\n📋 Lớp chất lượng {args.gate}: {trang_thai}")
    if not KY_DUOC[args.gate](trang_thai):
        print("⛔ CHƯA TỚI LÚC KÝ. Các mục còn thiếu (đây là nội dung cần hoàn tất trước):")
        for muc in bao_cao.get("automatic_criteria", []) + bao_cao.get("human_criteria", []):
            if muc.get("status") in {"BLOCK", "REVIEW", "FAIL"}:
                print(f"   • [{muc.get('id')}] {muc.get('label')} — {muc.get('evidence', '')[:120]}")
        return 2

    # ── Bước 2: TRÌNH NỘI DUNG sắp ký ──────────────────────────────────────
    print("\n── NỘI DUNG SẮP KÝ — đọc file thật trước khi trả lời phỏng vấn ──")
    print(f"  Hồ sơ : {artifact}")
    print(f"  SHA256: {sha256_file(artifact)} (băm này bị khoá trong chữ ký)")
    if args.gate == "G8":
        bb = study_dir / f"G8_PEER_REVIEW_REPORT_{args.study}.md"
        if not bb.exists():
            print(f"⛔ Thiếu bản nhận xét phản biện THẬT: {bb.name} — máy không sinh hộ file này.")
            return 2
        print(f"  Nhận xét phản biện: {bb} (SHA256 {sha256_file(bb)[:16]}…)")

    tra_loi = phong_van_g2(study_dir) if args.gate == "G2" else phong_van_g8()
    lenh = soan_lenh(args.gate, args.study, artifact, tra_loi)

    # ── Bước 3: XÁC NHẬN của người thật rồi mới ký ──────────────────────────
    print("\n── LỆNH SẼ CHẠY (kiểm mắt lần cuối) ──")
    print("  " + " ".join(lenh[2:]))
    khoa_rieng = Path.home() / ".ebm-secrets" / f"gate_ed25519_{ROLE_THEO_GATE[args.gate]}.key"
    if khoa_rieng.exists():
        print(f"  🔑 Thấy khoá riêng {khoa_rieng.name} → chữ ký sẽ là ed1 (bằng chứng độc lập).")
    else:
        print(f"  ⚠️ KHÔNG thấy {khoa_rieng.name} — cắm USB của người giữ vai và chép về"
              " ~/.ebm-secrets/ để ký ed1; thiếu thì approve_gate dùng mức bảo đảm thấp hơn"
              " và sẽ nói rõ.")
    if input("\n  Gõ đúng chữ  KY THAT  để ký (mọi thứ khác = huỷ): ").strip() != "KY THAT":
        print("Đã huỷ — không ghi gì vào sổ cái.")
        return 1

    rc = subprocess.run(lenh).returncode
    if rc == 0:
        print("\n✅ Đã ký. Việc ngay sau đó:")
        print("   1) Rút USB / xoá khoá riêng khỏi máy (nếu là khoá trao tay).")
        print(f"   2) Commit sổ cái: git add exports/{args.study}/approval_ledger*.json && git commit && git push")
        buoc_sau = {
            "G2": "   3) Bước kế tiếp của đề tài: pha phát triển công cụ (I-CVI, pilot) → ký G4 (SAP) → run_g5_auto.py",
            "G8": "   3) Bước kế tiếp của đề tài: run_g9_auto.py (liêm chính tác giả) → G10 lắp gói nộp",
        }[args.gate]
        print(buoc_sau)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
