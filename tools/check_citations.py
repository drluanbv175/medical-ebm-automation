#!/usr/bin/env python3
"""check_citations.py — Kiểm TRỌN GÓI một danh sách PMID trong MỘT lệnh (vá
2026-07-18, giảm token/mạng mỗi lần chạy).

GỘP hai bước xác minh trích dẫn vốn phải chạy riêng — rút bài
(`check_citation_retraction.py`) và metadata gốc (`check_citation_metadata.py`) —
thành MỘT lời gọi PubMed efetch duy nhất (`PubMedClient.check_citations()`), rồi
ghi CẢ HAI receipt máy-kiểm (`A12_RETRACTION_RECEIPT.json` + `A12_METADATA_RECEIPT.
json`) mà cổng A12 (`run_g10_assemble.py`) đòi. Lợi ích:

- 1 efetch thay vì 2 (cùng danh sách PMID) → nửa số lời gọi mạng + nửa parse XML.
- Agent/bác sĩ chạy 1 lệnh, đọc 1 bảng kết quả gộp thay vì 2 → ÍT TOKEN hơn mỗi lần.
- Tái dùng NGUYÊN VẸN hai hàm ghi receipt đã có (`write_retraction_receipt`,
  `write_metadata_receipt`) — không phân kỳ logic/định dạng/chữ ký, nên hai tool lẻ
  vẫn tương thích (dùng khi chỉ cần một trong hai).

SỬA 29/10/2026 (đánh giá chéo hội đồng G10 C1a, G10-DG-20261028T211140-262b8de6, RQ2 — cả hai người chấm): nhánh
rút bài từng lấy THẲNG kết quả PubMed — receipt A12 thành bằng chứng MỘT nguồn, trái chuỗi 3 tầng bắt buộc
(CLAUDE.md §6.4): mỗi mục chỉ có {"status": "ok"}, không có `source`/`sources_tried`, và tầng Retraction Watch
ngoại tuyến (tầng duy nhất từng bắt ca rút-và-thay mà cả PubMed lẫn Europe PMC báo «ok») không được hỏi. Nay
rút bài đi `RetractionChain` (Retraction Watch → NCBI → Europe PMC khi NCBI không kết luận được), tầng NCBI
DÙNG LẠI kết quả của lời efetch gộp (`_TangNcbiDungLai`) ⇒ PubMed vẫn chỉ bị gọi MỘT lần cho cả hai nhánh.

Dùng:
    python tools/check_citations.py --pmids 12345678,23456789
    python tools/check_citations.py --pmids 12345678 --study KKB-2026 --json

Exit code: 0 = mọi PMID sạch rút bài ("ok") VÀ phân giải được metadata ("resolved");
1 = còn ít nhất một vấn đề ở bất kỳ nhánh nào, kể cả trạng thái lạ (danh sách trắng,
26/09/2026) — KHÔNG được ghi "ĐÃ XÁC MINH TOÀN BỘ TRÍCH DẪN" vào artifact A12 khi
exit code là 1.
"""
from __future__ import annotations

import argparse
import json
import sys

# Windows: stdout mặc định cp1252 giết print() tiếng Việt — ép UTF-8 (chốt BH55/R4)
import sys as _sys_r4
from pathlib import Path

for _s_r4 in (_sys_r4.stdout, _sys_r4.stderr):
    try:
        _s_r4.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_citation_metadata as CCM  # noqa: E402
import check_citation_retraction as CCR  # noqa: E402

from app.sources.pubmed import PubMedClient  # noqa: E402
from app.sources.retraction_chain import RetractionChain  # noqa: E402


class _TangNcbiDungLai:
    """Tầng NCBI của `RetractionChain` dùng lại kết quả rút bài của lời efetch gộp — không gọi PubMed lần hai.
    `fetch_metadata` (tiêu đề thông báo rút bài — chuỗi chỉ gọi khi đã có tín hiệu rút) chuyển cho client thật."""

    def __init__(self, client: PubMedClient, ket_qua: dict) -> None:
        self._client, self._kq = client, ket_qua if isinstance(ket_qua, dict) else {}

    def check_retraction_status(self, pmids: list) -> dict:
        return {p: self._kq[p] for p in pmids if p in self._kq}

    def fetch_metadata(self, pmids: list) -> dict:
        return self._client.fetch_metadata(pmids)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("Dùng:")[0])
    ap.add_argument("--pmids", required=True, help="Danh sách PMID, phân cách bằng dấu phẩy")
    ap.add_argument("--json", action="store_true", help="Xuất JSON gộp thay vì bảng văn bản")
    ap.add_argument("--study", default="",
                    help="Mã đề tài (khớp exports/<mã>) — có thì ghi CẢ HAI receipt "
                         "A12_RETRACTION_RECEIPT.json + A12_METADATA_RECEIPT.json")
    args = ap.parse_args()

    pmids = [p.strip() for p in args.pmids.split(",") if p.strip()]
    if not pmids:
        print("✗ --pmids rỗng — không có gì để kiểm.")
        return 1

    # MỘT efetch → cả hai kết quả.
    client = PubMedClient()
    both = client.check_citations(pmids)
    # Rút bài qua chuỗi 3 tầng — luật gộp bất đối xứng ở app/sources/retraction_chain.py, hợp đồng 6 trạng thái
    # giữ nguyên nên receipt A12 và mọi nơi đọc không đổi cách đọc (chỉ THÊM `source`/`sources_tried`).
    retraction = RetractionChain(pubmed=_TangNcbiDungLai(client, both["retraction"])).check(pmids)
    metadata = both["metadata"]

    if args.study.strip():
        # Tái dùng đúng hàm ghi receipt của từng tool lẻ (cùng chữ ký/định dạng).
        rp = CCR.write_retraction_receipt(args.study, pmids, retraction)
        mp = CCM.write_metadata_receipt(args.study, pmids, metadata)
        print(f"📝 Đã ghi 2 receipt máy-kiểm: {rp.relative_to(REPO_ROOT)} + "
              f"{mp.relative_to(REPO_ROOT)}", file=sys.stderr)

    # DANH SÁCH TRẮNG (vá 26/09/2026, #34): rút bài chỉ "ok" là sạch (`CCR.la_van_de`), metadata chỉ
    # "resolved" là phân giải được. Xét theo DANH SÁCH PMID đã hỏi — PMID vắng mặt, trạng thái lạ,
    # None hay bản ghi không phải dict đều là vấn đề. Danh sách đen cũ coi mọi trạng thái lạ là sạch.
    retr_problem = any(CCR.la_van_de(retraction.get(p)) for p in pmids)
    meta_problem = any(not isinstance(metadata.get(p), dict) or metadata[p].get("status") != "resolved"
                       for p in pmids)

    if args.json:
        print(json.dumps({"retraction": retraction, "metadata": metadata},
                         ensure_ascii=False, indent=2))
        return 1 if (retr_problem or meta_problem) else 0

    print(f"Kiểm TRỌN GÓI {len(pmids)} PMID — 1 lời gọi PubMed (metadata + tầng NCBI), rút bài qua chuỗi 3 tầng "
          "(Retraction Watch → NCBI → Europe PMC khi NCBI không kết luận được)\n")
    for pmid in pmids:
        r = retraction.get(pmid, {"status": "unresolved"})
        m = metadata.get(pmid, {"status": "unresolved"})
        r = r if isinstance(r, dict) else {"status": None}
        m = m if isinstance(m, dict) else {"status": None}
        r_label = CCR.nhan_trang_thai(r.get("status"))
        m_label = CCM._STATUS_LABEL.get(m.get("status")) or (
            f"⚠️  TRẠNG THÁI LẠ {m.get('status')!r} — CHƯA phân giải (không được coi là sạch)")
        print(f"  PMID {pmid}:")
        nguon = r.get("source") or "—"
        print(f"      Rút bài:  {r_label} (nguồn kết luận: {nguon}; đã hỏi: "
              f"{', '.join(r.get('sources_tried') or []) or '—'})")
        print(f"      Metadata: {m_label}")
        if m.get("status") == "resolved":
            print(f"          → {m.get('authors') or '[?]'} — {m.get('title') or '[?]'} — "
                  f"{m.get('journal') or '[?]'} ({m.get('year') or '?'})")

    print()
    if retr_problem or meta_problem:
        print("🚧 CÓ VẤN ĐỀ (rút bài hoặc metadata) — xử lý xong mới được ghi "
              "\"KẾT QUẢ CỔNG A12: ĐÃ XÁC MINH TOÀN BỘ TRÍCH DẪN\".")
        return 1
    print("✅ Mọi PMID sạch rút bài VÀ phân giải được metadata gốc. "
          "So khớp NỘI DUNG với bài vẫn cần agent/bác sĩ đọc. Cần bác sĩ kiểm chứng.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
