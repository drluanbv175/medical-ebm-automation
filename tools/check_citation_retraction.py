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

Exit code: 0 = không phát hiện vấn đề (mọi PMID "ok"); 1 = có PMID retracted/
expression-of-concern/không xác minh được (unresolved/mock/no-email) — KHÔNG
được ghi "ĐÃ XÁC MINH TOÀN BỘ TRÍCH DẪN" vào artifact A12 khi exit code là 1.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from app.sources.pubmed import PubMedClient  # noqa: E402

_PROBLEM_STATUSES = {"retracted", "expression_of_concern", "unresolved", "unknown_mock_or_no_email"}

_STATUS_LABEL = {
    "retracted": "🔴 ĐÃ BỊ RÚT",
    "expression_of_concern": "🟡 EXPRESSION OF CONCERN",
    "unresolved": "🔴 KHÔNG XÁC MINH ĐƯỢC (nghi ma/PMID sai)",
    "unknown_mock_or_no_email": "⚠️  KHÔNG TRA CỨU ĐƯỢC (mock/thiếu NCBI_EMAIL/lỗi mạng)",
    "ok": "✅ OK",
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("Dùng:")[0])
    ap.add_argument("--pmids", required=True, help="Danh sách PMID, phân cách bằng dấu phẩy")
    ap.add_argument("--json", action="store_true", help="Xuất JSON thay vì bảng văn bản")
    args = ap.parse_args()

    pmids = [p.strip() for p in args.pmids.split(",") if p.strip()]
    if not pmids:
        print("✗ --pmids rỗng — không có gì để kiểm.")
        return 1

    client = PubMedClient()
    results = client.check_retraction_status(pmids)

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
