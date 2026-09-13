#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""kiem_do_tuoi_thang_diem.py — Kiểm RÚT BÀI + ĐỘ TƯƠI cho 32 thang điểm/công cụ
lâm sàng "verified" (app/clinical_scores/verified.py::VERIFIED_SCORES).

VÌ SAO CÓ (13/09/2026, bác sĩ chốt "xây ngay" sau audit toàn diện hệ nghiên cứu
và cập nhật chứng cứ):
====================================================================
`_VERIFIED_IDS` trong verified.py ghi PMID/DOI nguồn gốc cho 32 thang điểm,
xác minh MỘT LẦN vào 2026-06-14 (đối chiếu tác giả·năm·tạp chí·volume·trang).
`tests/test_verified_identifiers_online.py` kiểm các PMID đó còn PHÂN GIẢI
được trên PubMed — nhưng đó là test opt-in (EBM_RUN_ONLINE_PMID_TEST=1), KHÔNG
có lịch chạy nào, và nó KHÔNG kiểm RÚT BÀI (chỉ kiểm tồn tại/tiêu đề). Đo
13/09/2026: 0 cơ chế tự động tái-kiểm định kỳ cho kho 32 thang điểm — một PMID
nền tảng của công thức/ngưỡng lâm sàng (CURB-65, CHA2DS2-VASc, qSOFA, MELD-Na…)
có thể bị rút SAU 2026-06-14 mà không ai biết, và hệ vẫn tính điểm/áp ngưỡng
dựa trên nó.

Công cụ này CHỈ ĐO VÀ BÁO (BH10 — không đổi VERIFIED_SCORES/decision/cut-off
nào, kể cả khi phát hiện rút bài thật):
  ① Với mỗi PMID: chạy CHUỖI 3 TẦNG rút bài (Retraction Watch ngoại tuyến →
     NCBI → Europe PMC) — cùng `app/sources/retraction_chain.py` mà
     `tools/check_citation_retraction.py` dùng cho cổng A12.
  ② Với thang chỉ có DOI (không có PMID): tra Crossref `updated-by`
     (`app/sources/crossref_retraction.py`, cùng cơ chế BH33 đã bắt được ca
     PMID 30267080 ⇄ DOI 10.1001/jamaoncol.2018.4070).
  ③ Thang không có cả PMID lẫn DOI (báo cáo hội đồng/sách — 4 mục đã tự khai
     trong `_VERIFIED_IDS`) → ghi rõ "KHÔNG CÓ ĐỊNH DANH ĐỂ TỰ KIỂM", KHÔNG
     phải lỗi (BH08: thiếu nguyên liệu không phải bằng chứng nguy hiểm).
  ④ Độ tươi của CHÍNH LẦN KIỂM: ghi mốc lần chạy đầy đủ gần nhất vào
     `state/kiem-thang-diem-quy.json`; `--nhanh` chỉ đọc lại mốc đó (không gọi
     mạng) và báo quá hạn khi vượt ngưỡng (mặc định 120 ngày — cùng ngưỡng
     BH32 dùng cho độ tươi dashboard, tránh đỏ giả mỗi quý vì nhịp thật là 92
     ngày).

Dùng:
    python tools/kiem_do_tuoi_thang_diem.py            # kiểm đầy đủ (gọi mạng)
    python tools/kiem_do_tuoi_thang_diem.py --nhanh    # chỉ đọc sổ, không gọi mạng
    python tools/kiem_do_tuoi_thang_diem.py --json

Exit code: 0 = sạch (không rút bài/EoC/không xác minh được, chưa quá hạn tươi);
1 = có phát hiện cần bác sĩ đọc (rút bài/EoC/không xác minh được/quá hạn tươi);
2 = lỗi công cụ (crash, không phải phát hiện).
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from app.clinical_scores.verified import VERIFIED_SCORES  # noqa: E402
from app.sources.crossref_retraction import CrossrefRetraction  # noqa: E402
from app.sources.retraction_chain import DUONG_TINH, KHONG_BIET, RetractionChain  # noqa: E402

STATE_PATH = REPO_ROOT / "state" / "kiem-thang-diem-quy.json"
NGUONG_QUA_HAN_NGAY = 120

# Trạng thái được coi là "vấn đề cần đọc" — hợp nhất DUONG_TINH (retracted/EoC),
# "unresolved" (nghi định danh sai/ma) và KHONG_BIET (chưa kiểm được do mạng/
# thiếu cấu hình). Giữ đúng bài học BH27: "không kiểm được PHẢI là một vấn đề",
# không được để fail-open thành "sạch".
_VAN_DE = set(DUONG_TINH) | {"unresolved"} | set(KHONG_BIET)

_NHAN = {
    "retracted": "🔴 ĐÃ BỊ RÚT",
    "expression_of_concern": "🟡 EXPRESSION OF CONCERN",
    "unresolved": "🔴 KHÔNG XÁC MINH ĐƯỢC (nghi định danh sai/ma)",
    "unknown_mock_or_no_email": "⚠️  CHƯA KIỂM ĐƯỢC (mock/thiếu NCBI_EMAIL/lỗi mạng)",
    "unknown_fetch_error": "⚠️  CHƯA KIỂM ĐƯỢC (nguồn không trả lời được)",
    "khong_co_dinh_danh": "⚪ KHÔNG CÓ ĐỊNH DANH — cần bác sĩ đối chiếu bằng tay",
    "ok": "✅ OK",
}


def _nhan_cho(status: str) -> str:
    return _NHAN.get(status, status)


def _doc_so_cu() -> dict:
    if STATE_PATH.exists():
        try:
            return json.loads(STATE_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _ghi_so(du_lieu: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(du_lieu, ensure_ascii=False, indent=2),
                           encoding="utf-8", newline="\n")


def thu_thap_dinh_danh() -> List[Dict[str, Optional[str]]]:
    """[{score_id, score_name, pmid, doi}] cho toàn bộ 32 thang điểm verified."""
    ra = []
    for s in VERIFIED_SCORES:
        ra.append({
            "score_id": s["score_id"],
            "score_name": s.get("score_name", s["score_id"]),
            "pmid": s.get("pmid"),
            "doi": s.get("doi"),
        })
    return ra


def kiem_day_du(chain: Optional[RetractionChain] = None,
                crossref: Optional[CrossrefRetraction] = None) -> dict:
    """Chạy chuỗi rút bài cho mọi PMID + Crossref cho DOI-only. KHÔNG gọi mạng
    nếu `chain`/`crossref` được tiêm sẵn (dùng cho test ngoại tuyến)."""
    items = thu_thap_dinh_danh()
    pmids = sorted({it["pmid"] for it in items if it["pmid"]})
    dois_only = sorted({it["doi"] for it in items if it["doi"] and not it["pmid"]})

    chain = chain if chain is not None else RetractionChain()
    ket_qua_pmid = chain.check(pmids) if pmids else {}

    crossref = crossref if crossref is not None else CrossrefRetraction()
    ket_qua_doi = crossref.check(dois_only) if dois_only else {}

    hang_muc = []
    for it in items:
        if it["pmid"]:
            r = ket_qua_pmid.get(it["pmid"]) or {
                "status": "unknown_fetch_error", "reason": "không có kết quả từ chuỗi rút bài"}
            nguon_kiem = "pmid"
        elif it["doi"]:
            r = ket_qua_doi.get(it["doi"]) or {
                "status": "unknown_fetch_error", "reason": "không có kết quả từ Crossref"}
            nguon_kiem = "doi"
        else:
            r = {"status": "khong_co_dinh_danh",
                 "reason": "nguồn là báo cáo thể chế/sách, không đăng ký PMID/DOI (đã tự khai trong verified.py)"}
            nguon_kiem = None
        hang_muc.append({**it, "nguon_kiem": nguon_kiem, "ket_qua": r})

    return {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "n_scores": len(items),
        "n_pmid": len(pmids),
        "n_doi_only": len(dois_only),
        "n_no_identifier": sum(1 for it in items if not it["pmid"] and not it["doi"]),
        "hang_muc": hang_muc,
    }


def _in_bao_cao(ket_qua: dict) -> None:
    print(f"Kiểm rút bài + độ tươi cho {ket_qua['n_scores']} thang điểm verified "
          f"({ket_qua['n_pmid']} có PMID, {ket_qua['n_doi_only']} chỉ có DOI, "
          f"{ket_qua['n_no_identifier']} không có định danh).\n")
    for h in ket_qua["hang_muc"]:
        status = h["ket_qua"].get("status", "")
        dinh_danh = (f"PMID {h['pmid']}" if h["pmid"]
                     else (f"DOI {h['doi']}" if h["doi"] else "—"))
        print(f"  [{h['score_id']:16s}] {h['score_name']:42s} {dinh_danh:26s} {_nhan_cho(status)}")
        ly_do = h["ket_qua"].get("reason")
        if ly_do:
            print(f"      → {ly_do}")
        if status in DUONG_TINH:
            n = h["ket_qua"].get("retraction_notice") or h["ket_qua"].get("expression_of_concern_notice")
            if n:
                print(f"      → Thông báo: PMID {n.get('pmid')} — {n.get('citation')}")
            if h["ket_qua"].get("nature"):
                print(f"      → {h['ket_qua']['nature']} ngày {h['ket_qua'].get('retraction_date', '?')}")
    print()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("Dùng:")[0])
    ap.add_argument("--nhanh", action="store_true",
                     help="Chỉ đọc sổ lần kiểm đầy đủ trước — KHÔNG gọi mạng.")
    ap.add_argument("--json", action="store_true", help="Xuất JSON thay vì bảng văn bản.")
    args = ap.parse_args()

    if args.nhanh:
        so_cu = _doc_so_cu()
        last = so_cu.get("checked_at")
        if not last:
            if args.json:
                print(json.dumps({"error": "chua_tung_chay"}, ensure_ascii=False))
            else:
                print("⚪ CHƯA TỪNG CHẠY kiểm đầy đủ — chạy không có --nhanh ít nhất một lần trước.")
            return 1
        try:
            ngay_qua = (datetime.now(timezone.utc) - datetime.fromisoformat(last)).days
        except ValueError:
            if args.json:
                print(json.dumps({"error": "so_hong", "checked_at": last}, ensure_ascii=False))
            else:
                print(f"✗ Sổ hỏng — trường checked_at không đọc được: {last!r}")
            return 2
        qua_han = ngay_qua > NGUONG_QUA_HAN_NGAY
        if args.json:
            print(json.dumps({"last_checked_at": last, "days_since": ngay_qua,
                               "qua_han": qua_han}, ensure_ascii=False))
        else:
            print(f"Lần kiểm rút bài đầy đủ gần nhất: {last} ({ngay_qua} ngày trước).")
            if qua_han:
                print(f"🟡 QUÁ HẠN {ngay_qua - NGUONG_QUA_HAN_NGAY} ngày so với ngưỡng "
                      f"{NGUONG_QUA_HAN_NGAY} — nên chạy lại đầy đủ (bỏ --nhanh).")
            else:
                print("🟢 Còn trong hạn.")
        return 1 if qua_han else 0

    try:
        ket_qua = kiem_day_du()
    except Exception as e:  # noqa: BLE001 — lỗi công cụ, KHÔNG phải một phát hiện
        print(f"✗ Lỗi công cụ khi kiểm rút bài 32 thang điểm: {type(e).__name__}: {e}",
              file=sys.stderr)
        return 2

    van_de = [h for h in ket_qua["hang_muc"] if h["ket_qua"].get("status") in _VAN_DE]

    if args.json:
        print(json.dumps(ket_qua, ensure_ascii=False, indent=2))
    else:
        _in_bao_cao(ket_qua)

    _ghi_so({**ket_qua, "n_van_de": len(van_de)})

    # Từ đây chỉ IN THÊM văn bản khi KHÔNG ở chế độ --json — payload JSON ở trên
    # đã đủ để caller đọc n_van_de/hang_muc; in thêm dòng văn xuôi sẽ phá định
    # dạng JSON thuần (đúng bài học "In ra stderr" của check_citation_retraction.py,
    # ở đây đơn giản hơn: chỉ cần không in gì thêm vào stdout).
    if van_de:
        if not args.json:
            n_rut = sum(1 for h in van_de if h["ket_qua"].get("status") in DUONG_TINH)
            if n_rut:
                print(f"🔴 {n_rut} thang điểm có nguồn ĐÃ BỊ RÚT/expression of concern — "
                      "ĐỌC NGAY, cần bác sĩ đối chiếu và quyết định có đổi công thức/nguồn không.")
            con_lai = len(van_de) - n_rut
            if con_lai:
                print(f"⚠️  {con_lai} mục còn lại chưa xác minh được (mạng/định danh nghi sai) — "
                      "không kết luận, thử chạy lại sau.")
            print("Công cụ CHỈ ĐO VÀ BÁO — không tự đổi thang điểm/quyết định lâm sàng nào.")
        return 1

    if not args.json:
        print("✅ Không phát hiện rút bài/expression of concern trong 32 thang điểm verified.")
        print("Cần bác sĩ kiểm chứng.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
