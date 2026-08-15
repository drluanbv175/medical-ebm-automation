#!/usr/bin/env python3
"""check_citation_metadata.py — Phân giải CHỦ ĐỘNG metadata gốc (tác giả·tiêu
đề·tạp chí·năm·DOI) THẬT từ PubMed cho một danh sách PMID, và ghi receipt máy-kiểm
`exports/<study>/A12_METADATA_RECEIPT.json` (vá 2026-07-18, audit đối kháng 7 trục).

BỐI CẢNH — LỖ HỔNG ĐƯỢC ĐÓNG: trước bản vá này, cổng A12 (`run_g10_assemble.py::
citation_verification_ok`) CHỈ có bằng chứng máy-kiểm cho khâu RÚT BÀI
(`A12_RETRACTION_RECEIPT.json` do `check_citation_retraction.py` ghi). Khâu ĐỐI
CHIẾU METADATA (Bước 1-2 của `kiem-chung-trich-dan`: phân giải PMID/DOI → metadata
gốc, so tác giả·năm·tạp chí·tiêu đề) hoàn toàn dựa vào lời TỰ KHAI của agent (agent
gõ ✅/🟡/🔴 vào bảng artifact A12) — KHÔNG có receipt/chữ ký nào để cổng đối chiếu
độc lập. Nếu agent (do lỗi, không cố ý) quên gọi MCP tool phân giải và tự điền ✅ từ
trí nhớ cho tác giả/tiêu đề/tạp chí, không cơ chế nào bắt được — đúng lỗ hổng mà bản
vá 2026-07-15/07-16 đã đóng cho khâu rút bài nhưng CHƯA áp cho khâu metadata.

Tool này đóng lỗ hổng đó bằng cách nhân bản đúng khuôn receipt rút bài: gọi THẬT
`app.sources.pubmed.PubMedClient.fetch_metadata()` (PubMed E-utilities), ghi metadata
gốc đã phân giải vào receipt có hash + chữ ký HMAC (cùng cơ chế `gate_contract.py`
dùng cho G2/G4/G8/G9). Receipt là BẰNG CHỨNG mỗi PMID đã thật sự được phân giải —
agent không thể "qua cổng" chỉ bằng dòng text tự gõ.

LƯU Ý — receipt này chứng minh ĐÃ PHÂN GIẢI metadata gốc, KHÔNG tự động chứng minh
"trích dẫn trong bài KHỚP metadata gốc" (so khớp ngữ nghĩa/ngữ cảnh vẫn là phán đoán
của agent + bác sĩ — vd 'tiêu đề dịch sai bối cảnh'). Nhưng nó buộc metadata gốc phải
được LẤY VỀ THẬT làm mốc đối chiếu, thay vì agent tự điền từ trí nhớ.

Dùng:
    python tools/check_citation_metadata.py --pmids 12345678,23456789
    python tools/check_citation_metadata.py --pmids 12345678 --json
    python tools/check_citation_metadata.py --pmids 12345678,23456789 --study KKB-2026

Exit code: 0 = mọi PMID phân giải được (status "resolved"); 1 = có PMID
unresolved/mock/không email — KHÔNG được ghi "ĐÃ XÁC MINH TOÀN BỘ TRÍCH DẪN" vào
artifact A12 khi exit code là 1.
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
from typing import Dict, List

for _s_r4 in (_sys_r4.stdout, _sys_r4.stderr):
    try:
        _s_r4.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import gate_contract as GC  # noqa: E402  (ký receipt bằng khóa cục bộ dùng chung với G2/G4/G8/G9)

from app.sources.pubmed import PubMedClient  # noqa: E402

# Gate id RIÊNG cho receipt metadata — KHÔNG dùng "A12" để chữ ký metadata không
# trùng/không thay thế được chữ ký receipt rút bài (payload ký gồm gate_id).
METADATA_GATE_ID = "A12META"

_PROBLEM_STATUSES = {"unresolved", "unknown_mock_or_no_email"}

_STATUS_LABEL = {
    "resolved": "✅ PHÂN GIẢI ĐƯỢC",
    "unresolved": "🔴 KHÔNG PHÂN GIẢI ĐƯỢC (nghi ma/PMID sai)",
    "unknown_mock_or_no_email": "⚠️  KHÔNG TRA CỨU ĐƯỢC (mock/thiếu NCBI_EMAIL/lỗi mạng)",
}


def pmids_hash(pmids: List[str]) -> str:
    """sha256 của danh sách PMID đã sort — cùng công thức với
    check_citation_retraction.pmids_hash để cổng đối chiếu nhất quán."""
    return hashlib.sha256(",".join(sorted(pmids)).encode("utf-8")).hexdigest()


def _sanitize_study(study_raw: str) -> str:
    """Khớp đúng quy ước sanitize tên đề tài của run_g*_auto.py."""
    return re.sub(r"[^\w\-]", "_", study_raw.strip().replace(" ", "-"))


def write_metadata_receipt(study_raw: str, pmids: List[str], results: Dict[str, dict]) -> Path:
    """Ghi receipt máy-kiểm `exports/<study>/A12_METADATA_RECEIPT.json` — bằng chứng
    ĐÃ PHÂN GIẢI metadata gốc THẬT, độc lập với bảng agent tự gõ. LUÔN ghi (kể cả khi
    all_resolved=false) — không xoá bằng chứng đã chạy dù kết quả xấu."""
    study = _sanitize_study(study_raw)
    out_dir = REPO_ROOT / "exports" / study
    out_dir.mkdir(parents=True, exist_ok=True)

    sorted_pmids = sorted(pmids)
    per_pmid = {
        pmid: results.get(pmid, {"status": "unresolved", "reason": "không có kết quả"})
        for pmid in pmids
    }
    all_resolved = all(v.get("status") == "resolved" for v in per_pmid.values())

    checked_at_utc = datetime.now(timezone.utc).isoformat()
    pmids_hash_value = pmids_hash(sorted_pmids)
    receipt = {
        "study": study,
        "checked_at_utc": checked_at_utc,
        "pmids_checked": sorted_pmids,
        "pmids_hash": pmids_hash_value,
        "all_resolved": all_resolved,
        "metadata": per_pmid,
    }
    # Ký receipt bằng khóa cục bộ (cùng HMAC dùng cho G2/G4/G8/G9). None nếu máy chưa
    # cấu hình khóa — run_g10_assemble.py fail-closed cho đề tài THẬT khi thiếu chữ ký.
    signature = GC.sign_approval(METADATA_GATE_ID, study, pmids_hash_value, checked_at_utc)
    if signature:
        receipt["receipt_signature"] = signature
    receipt_path = out_dir / "A12_METADATA_RECEIPT.json"
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    return receipt_path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("Dùng:")[0])
    ap.add_argument("--pmids", required=True, help="Danh sách PMID, phân cách bằng dấu phẩy")
    ap.add_argument("--json", action="store_true", help="Xuất JSON thay vì bảng văn bản")
    ap.add_argument("--study", default="",
                    help="Mã đề tài (khớp exports/<mã>) — có thì ghi thêm receipt máy-kiểm "
                         "exports/<mã>/A12_METADATA_RECEIPT.json, dùng bởi "
                         "run_g10_assemble.py::citation_verification_ok để làm cứng cổng A12")
    args = ap.parse_args()

    pmids = [p.strip() for p in args.pmids.split(",") if p.strip()]
    if not pmids:
        print("✗ --pmids rỗng — không có gì để phân giải.")
        return 1

    client = PubMedClient()
    results = client.fetch_metadata(pmids)

    if args.study.strip():
        receipt_path = write_metadata_receipt(args.study, pmids, results)
        print(f"📝 Đã ghi receipt máy-kiểm: {receipt_path.relative_to(REPO_ROOT)}", file=sys.stderr)

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return 1 if any(v.get("status") in _PROBLEM_STATUSES for v in results.values()) else 0

    print(f"Phân giải metadata gốc cho {len(pmids)} PMID (nguồn: PubMed E-utilities thật)\n")
    any_problem = False
    for pmid in pmids:
        info = results.get(pmid, {"status": "unresolved", "reason": "không có kết quả"})
        status = info.get("status", "unresolved")
        if status in _PROBLEM_STATUSES:
            any_problem = True
        label = _STATUS_LABEL.get(status, status)
        line = f"  PMID {pmid}: {label}"
        if status == "resolved":
            line += (f"\n      → {info.get('authors') or '[không có tác giả]'} — "
                     f"{info.get('title') or '[không có tiêu đề]'} — "
                     f"{info.get('journal') or '[không có tạp chí]'} ({info.get('year') or '?'})"
                     f"{'  doi:' + info['doi'] if info.get('doi') else ''}")
        elif info.get("reason"):
            line += f"\n      → {info['reason']}"
        print(line)

    print()
    if any_problem:
        print("🚧 CÓ PMID CHƯA PHÂN GIẢI — đối chiếu/sửa xong mới được ghi dòng \"KẾT QUẢ "
              "CỔNG A12: ĐÃ XÁC MINH TOÀN BỘ TRÍCH DẪN\" (xem kiem-chung-trich-dan.md).")
        return 1
    print("✅ Mọi PMID đã phân giải được metadata gốc. So khớp NỘI DUNG với bài vẫn cần agent/bác sĩ đọc.")
    print("Cần bác sĩ kiểm chứng.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
