#!/usr/bin/env python3
"""check_citation_retraction.py — Tra cứu CHỦ ĐỘNG trạng thái rút bài/expression
of concern THẬT từ PubMed cho một danh sách PMID (vá 2026-07-15, Ngày 4 lộ trình
7 ngày — reports/LO_TRINH_7_NGAY_NGHIEN_CUU_Y_KHOA_2026-07-14.md).

Đóng khoảng trống P0-14/P1-19: agent `kiem-chung-trich-dan` (module M5 — "cảnh
báo nếu tài liệu đã bị rút") trước đây hoàn toàn dựa vào PHÁN ĐOÁN của agent khi
đọc metadata/abstract, không có script nào xác minh lại bằng dữ liệu PubMed
sống. Tool này gọi thật `app.sources.pubmed.PubMedClient.check_retraction_status()`
— đọc CẢ `<PublicationType>Retracted Publication</PublicationType>` LẪN
`<CommentsCorrections RefType="RetractionIn">` (xác nhận bằng PMID 9500320,
Wakefield 1998, Lancet — rút 2010, PubMed gắn cả hai cờ).

KHÁC `app/evidence/retraction_monitor.py` (nhánh mồ côi, xem CLAUDE.md mục
"nhánh mồ côi" — chỉ đọc chữ có sẵn, không tự tra cứu, không được tools/ nào
gọi tới). Tool NÀY sống trong tools/ và được doctrine `kiem-chung-trich-dan.md`
(module M5) yêu cầu chạy trước khi ghi artifact A12 "đã xác minh".

Dùng:
    python tools/check_citation_retraction.py --pmids 12345678,23456789
    python tools/check_citation_retraction.py --pmids 12345678 --json
    python tools/check_citation_retraction.py --pmids 12345678,23456789 --study KKB-2026

Exit code: 0 = không phát hiện vấn đề (mọi PMID "ok"); 1 = có PMID retracted/
expression-of-concern/không xác minh được (unresolved/mock/no-email) — KHÔNG
được ghi "ĐÃ XÁC MINH TOÀN BỘ TRÍCH DẪN" vào artifact A12 khi exit code là 1.

LÀM CỨNG CỔNG A12 (vá 2026-07-15, P1.1 lộ trình 7 ngày — sau audit chỉ ra
`run_g10_assemble.py::citation_verification_ok()` trước đây CHỈ đọc một dòng
CHUỖI TEXT do agent tự gõ vào artifact A12 ("KẾT QUẢ CỔNG A12: ĐÃ XÁC MINH
TOÀN BỘ TRÍCH DẪN") — không có gì bảo đảm agent đã thật sự CHẠY tool này trước
khi gõ dòng đó; agent có thể (do lỗi, không phải cố ý) viết dòng xác nhận mà
quên chạy kiểm rút bài thật): khi truyền `--study`, tool ghi THÊM một file
"receipt" máy-kiểm `exports/<study>/A12_RETRACTION_RECEIPT.json` — bằng chứng
tool NÀY đã thật sự chạy, độc lập với chuỗi text agent tự ghi. Ghi cả khi kết
quả KHÔNG sạch (`all_clean: false`) — không được xoá bằng chứng đã chạy dù kết
quả xấu, để `run_g10_assemble.py` có thể đối chiếu.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import gate_contract as GC  # noqa: E402  (ký receipt bằng khóa cục bộ dùng chung với G2/G4/G8/G9)

from app.sources.pubmed import PubMedClient  # noqa: E402

_PROBLEM_STATUSES = {"retracted", "expression_of_concern", "unresolved", "unknown_mock_or_no_email"}

_STATUS_LABEL = {
    "retracted": "🔴 ĐÃ BỊ RÚT",
    "expression_of_concern": "🟡 EXPRESSION OF CONCERN",
    "unresolved": "🔴 KHÔNG XÁC MINH ĐƯỢC (nghi ma/PMID sai)",
    "unknown_mock_or_no_email": "⚠️  KHÔNG TRA CỨU ĐƯỢC (mock/thiếu NCBI_EMAIL/lỗi mạng)",
    "ok": "✅ OK",
}


def configure_utf8_stdio() -> None:
    """Giúp argparse/help và nhãn tiếng Việt không lỗi trên Windows console cp1252."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError, ValueError):
            pass


def pmids_hash(pmids: List[str]) -> str:
    """sha256 của danh sách PMID đã sort, nối bằng dấu phẩy. Dùng để đối chiếu
    receipt máy-kiểm (ghi bởi tool này) với danh sách PMID mà artifact A12 nêu
    (đọc lại bởi `tools/run_g10_assemble.py::citation_verification_ok`) — cả
    hai bên PHẢI dùng đúng công thức này để hash so được với nhau."""
    return hashlib.sha256(",".join(sorted(pmids)).encode("utf-8")).hexdigest()


def _sanitize_study(study_raw: str) -> str:
    """Khớp đúng quy ước sanitize tên đề tài đã dùng ở toàn bộ run_g*_auto.py
    (vd tools/run_g10_assemble.py dòng ~1198) — để tên thư mục exports/<study>
    nhất quán dù bác sĩ/agent gõ khoảng trắng hay ký tự lạ."""
    return re.sub(r"[^\w\-]", "_", study_raw.strip().replace(" ", "-"))


def write_retraction_receipt(study_raw: str, pmids: List[str], results: Dict[str, dict]) -> Path:
    """Ghi receipt máy-kiểm `exports/<study>/A12_RETRACTION_RECEIPT.json` — bằng
    chứng CHẠY THẬT của tool này, độc lập với chuỗi text agent tự gõ vào artifact
    A12. LUÔN ghi (kể cả khi all_clean=false) — không được xoá bằng chứng đã
    chạy dù kết quả xấu (vá 2026-07-15, P1.1 lộ trình 7 ngày)."""
    study = _sanitize_study(study_raw)
    out_dir = REPO_ROOT / "exports" / study
    out_dir.mkdir(parents=True, exist_ok=True)

    sorted_pmids = sorted(pmids)
    per_pmid = {
        pmid: results.get(pmid, {"status": "unresolved", "reason": "không có kết quả"})
        for pmid in pmids
    }
    all_clean = not any(v.get("status") in _PROBLEM_STATUSES for v in per_pmid.values())

    checked_at_utc = datetime.now(timezone.utc).isoformat()
    pmids_hash_value = pmids_hash(sorted_pmids)
    receipt = {
        "study": study,
        "checked_at_utc": checked_at_utc,
        "pmids_checked": sorted_pmids,
        "pmids_hash": pmids_hash_value,
        "all_clean": all_clean,
        "results": per_pmid,
    }
    # Ký receipt bằng khóa cục bộ (cùng cơ chế HMAC dùng cho phê duyệt G2/G4/G8/G9) —
    # vá 2026-07-16 sau khi red-team đối kháng chỉ ra pmids_hash một mình KHÔNG chống
    # giả mạo được: hàm pmids_hash() là CÔNG KHAI (không khóa bí mật), nên ai cũng tự
    # viết tay một receipt "sạch" rồi tự tính đúng pmids_hash cho khớp. None nếu máy
    # này chưa cấu hình khóa (setup_gate_approval_key.py chưa chạy) — run_g10_assemble.py
    # sẽ fail-closed cho đề tài THẬT khi thiếu chữ ký, giữ hành vi cũ cho đề tài khác.
    signature = GC.sign_approval("A12", study, pmids_hash_value, checked_at_utc)
    if signature:
        receipt["receipt_signature"] = signature
    receipt_path = out_dir / "A12_RETRACTION_RECEIPT.json"
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    return receipt_path


def main() -> int:
    configure_utf8_stdio()
    ap = argparse.ArgumentParser(description=__doc__.split("Dùng:")[0])
    ap.add_argument("--pmids", required=True, help="Danh sách PMID, phân cách bằng dấu phẩy")
    ap.add_argument("--json", action="store_true", help="Xuất JSON thay vì bảng văn bản")
    ap.add_argument("--study", default="",
                    help="Mã đề tài (khớp exports/<mã>) — có thì ghi thêm receipt máy-kiểm "
                         "exports/<mã>/A12_RETRACTION_RECEIPT.json, dùng bởi "
                         "run_g10_assemble.py::citation_verification_ok để làm cứng cổng A12")
    args = ap.parse_args()

    pmids = [p.strip() for p in args.pmids.split(",") if p.strip()]
    if not pmids:
        print("✗ --pmids rỗng — không có gì để kiểm.")
        return 1

    client = PubMedClient()
    results = client.check_retraction_status(pmids)

    if args.study.strip():
        receipt_path = write_retraction_receipt(args.study, pmids, results)
        # In ra stderr (không phải stdout) để KHÔNG phá định dạng JSON thuần khi
        # dùng --json (một số script downstream có thể json.loads(toàn bộ stdout)).
        print(f"📝 Đã ghi receipt máy-kiểm: {receipt_path.relative_to(REPO_ROOT)}", file=sys.stderr)

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return 1 if any(v.get("status") in _PROBLEM_STATUSES for v in results.values()) else 0

    print(f"Kiểm rút bài/expression of concern cho {len(pmids)} PMID (nguồn: PubMed E-utilities thật)\n")
    any_problem = False
    for pmid in pmids:
        info = results.get(pmid, {"status": "unresolved", "reason": "không có kết quả"})
        status = info.get("status", "unresolved")
        if status in _PROBLEM_STATUSES:
            any_problem = True
        label = _STATUS_LABEL.get(status, status)
        line = f"  PMID {pmid}: {label}"
        if status == "retracted" and info.get("retraction_notice"):
            n = info["retraction_notice"]
            line += f"\n      → Thông báo rút bài: PMID {n.get('pmid')} — {n.get('citation')}"
        elif status == "expression_of_concern" and info.get("expression_of_concern_notice"):
            n = info["expression_of_concern_notice"]
            line += f"\n      → Thông báo: PMID {n.get('pmid')} — {n.get('citation')}"
        elif status in ("unresolved", "unknown_mock_or_no_email") and info.get("reason"):
            line += f"\n      → {info['reason']}"
        print(line)

    print()
    if any_problem:
        print("🚧 CÓ VẤN ĐỀ — xử lý xong mới được ghi dòng \"KẾT QUẢ CỔNG A12: ĐÃ XÁC MINH "
              "TOÀN BỘ TRÍCH DẪN\" vào artifact A12 (xem kiem-chung-trich-dan.md mục 4b).")
        return 1
    print("✅ Không phát hiện rút bài/expression of concern trong danh sách PMID đã kiểm.")
    print("Cần bác sĩ kiểm chứng.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
