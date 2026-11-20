"""Kiểm rút bài cho TỪNG trích dẫn của đề tài và ghi theo từng mã (15/11/2026).

Bác sĩ 15/11/2026 giao đồng bộ giai đoạn «Tổng quan tài liệu» + «mỗi vấn đề … phải được cập nhật vào hệ thống». Đo
thật: bản ghi rút bài của G0 BTM chỉ ghi TỔNG SỐ («56 PMID đã kiểm … 14 nguồn trong nước chỉ có DOI: CHƯA kiểm rút
bài») — không ai đối chiếu được mã nào đã kiểm; biên nhận A12 của C1a đã quá hạn 30 ngày nhưng nằm trong gói G10 đã
băm nên không được ghi đè. Công cụ này kiểm MỌI định danh của TLTK đề cương nộp + danh mục trích dẫn:
- PMID: chuỗi 3 tầng `app.sources.retraction_chain.RetractionChain` (Retraction Watch ngoại tuyến → NCBI → Europe PMC);
- DOI không có PMID: Crossref `updated-by` (`CrossrefRetraction`) + Retraction Watch theo DOI;
- từ 20/11/2026 thêm DOI CHỈ có trong văn bản gói phát hành mà G10 quét (tài liệu phương pháp SAP dẫn…);
và ghi `exports/<mã>/KIEM_RUT_BAI_TRICH_DAN_<mã>.json` (tệp RIÊNG, không đụng biên nhận A12 đã băm). Luật gộp bất đối
xứng giữ nguyên: tín hiệu DƯƠNG từ bất kỳ nguồn nào là nhận; không kết luận được ⇒ KHÔNG BIẾT, không bao giờ «ok».

Dùng:
    python tools/kiem_rut_bai_trich_dan.py --study <mã>          # chạy khô: in kết quả, không ghi
    python tools/kiem_rut_bai_trich_dan.py --study <mã> --ghi    # ghi tệp kết quả theo từng mã
Mã thoát: 0 mọi mã «ok» · 1 có bài đã rút/expression of concern · 2 có mã không kết luận được · 3 không có trích dẫn.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

import danh_muc_trich_dan as DMT  # noqa: E402

TEP = "KIEM_RUT_BAI_TRICH_DAN_{study}.json"
SCHEMA = "de_tai/kiem_rut_bai_trich_dan/v1"
DUONG_TINH = ("retracted", "expression_of_concern")
# Trạng thái mang phán quyết của một nguồn đã lấy được bản ghi — còn lại là «không biết».
CO_PHAN_QUYET = ("ok", "correction", "retracted", "expression_of_concern")


def thu_thap(out_dir: Path, study: str) -> List[Dict[str, Any]]:
    """[{nguon, pmid, doi}] — TLTK đề cương nộp (nếu có) + mục `trich_dan` của danh mục + DOI chỉ có trong văn bản gói
    phát hành mà G10 quét (A12_CITATION_VERIFICATION, đề cương thống nhất, bản nộp); bỏ trùng theo định danh."""
    ra: List[Dict[str, Any]] = []
    da: set = set()

    def _them(nguon: str, khoa: set) -> None:
        if not khoa or khoa & da:
            return
        da.update(khoa)
        pmid = next((k.split(":", 1)[1] for k in khoa if k.startswith("pmid:")), None)
        doi = next((k.split(":", 1)[1] for k in sorted(khoa) if k.startswith("doi:")), None)
        ra.append({"nguon": nguon, "pmid": pmid, "doi": doi})

    p = Path(out_dir) / f"DE_CUONG_NOP_HOI_DONG_{study}.md"
    tach = DMT.tach_tltk(p.read_text(encoding="utf-8")) if p.is_file() else None
    if tach is not None:
        for n, dong in sorted(tach[0].items()):
            _them(f"TLTK số {n}", DMT.dinh_danh(dong))
    for x in DMT.doc(out_dir, study).get("trich_dan") or []:
        if isinstance(x, dict):
            _them(f"danh mục {x.get('id') or '?'}", DMT.khoa_cua(x))
    # 20/11/2026 (kiểm toàn hệ nghiên cứu): DOI CHỈ có trong văn bản gói phát hành mà G10 quét cho cảnh báo A12 —
    # A12_CITATION_VERIFICATION (bảng tài liệu phương pháp mà SAP dẫn), đề cương thống nhất, bản nộp Hội đồng. Trước
    # đây chỉ đọc TLTK + danh mục ⇒ DOI mà SAP dẫn (C1a: Dean & Pagano 2015, Solon và cộng sự 2015) không bao giờ được
    # kiểm — trái doctrine kiem-chung-trich-dan 19/11 — và G10 vẫn bảo tra tay. Dùng CHUNG bộ tách/chuẩn hoá DOI của
    # G10 để hai bên cùng một tập.
    import run_g10_assemble as G10A  # noqa: PLC0415 — nạp trễ, chỉ cần hai hàm tách DOI
    van_ban = [G10A._van_ban_ban_cuoi(study, Path(out_dir))]
    tep_a12 = Path(out_dir) / f"A12_CITATION_VERIFICATION_{study}.md"
    if tep_a12.is_file():
        van_ban.append(tep_a12.read_text(encoding="utf-8"))
    for d in sorted(G10A._dois_from_text("\n".join(van_ban)), key=str.lower):
        _them("văn bản gói phát hành", {f"doi:{G10A._chuan_doi(d)}"})
    return ra


def kiem(muc: List[Dict[str, Any]], chain: Any = None, crossref: Any = None,
         rw: Any = None) -> Dict[str, Dict[str, Any]]:
    """{khoá «pmid:/doi:» → {status, source, reason, nguon}}. Không gọi mạng khi các đối tượng được tiêm (test)."""
    pmids = sorted({m["pmid"] for m in muc if m["pmid"]})
    dois = sorted({m["doi"] for m in muc if m["doi"] and not m["pmid"]})
    if chain is None and pmids:
        from app.sources.retraction_chain import RetractionChain  # noqa: PLC0415
        chain = RetractionChain()
    if crossref is None and dois:
        from app.sources.crossref_retraction import CrossrefRetraction  # noqa: PLC0415
        crossref = CrossrefRetraction()
    if rw is None and dois:
        from app.sources.retraction_watch import RetractionWatchIndex  # noqa: PLC0415
        rw = RetractionWatchIndex()
    kq_p = chain.check(pmids) if pmids else {}
    kq_d = crossref.check(dois) if dois else {}
    ra: Dict[str, Dict[str, Any]] = {}
    for m in muc:
        if m["pmid"]:
            k, r = f"pmid:{m['pmid']}", kq_p.get(m["pmid"]) or {}
        elif m["doi"]:
            k, r = f"doi:{m['doi']}", dict(kq_d.get(m["doi"]) or {})
            duong = rw.tra_doi(m["doi"]) if rw is not None else None
            if duong and duong.get("status") in DUONG_TINH and r.get("status") not in DUONG_TINH:
                r = {**duong, "ghi_chu": f"Crossref: {r.get('status') or 'không có kết quả'}"}
        else:
            continue
        st = str(r.get("status") or "unknown_fetch_error")
        if st not in CO_PHAN_QUYET and st not in DUONG_TINH:
            st = st if st.startswith("unknown") or st == "unresolved" else "unknown_fetch_error"
        ra[k] = {"status": st, "source": r.get("source"), "reason": str(r.get("reason") or "")[:200],
                 "nguon": m["nguon"]}
    return ra


def ghi(out_dir: Path, study: str, ket_qua: Dict[str, Dict[str, Any]], luc: Optional[str] = None) -> Path:
    tong: Dict[str, int] = {}
    for v in ket_qua.values():
        tong[v["status"]] = tong.get(v["status"], 0) + 1
    p = Path(out_dir) / TEP.format(study=study)
    p.write_text(json.dumps({
        "schema": SCHEMA, "study": study,
        "checked_at": luc or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "cong_cu": "tools/kiem_rut_bai_trich_dan.py — PMID: RetractionChain (Retraction Watch → NCBI → Europe PMC); "
                   "DOI không PMID: Crossref updated-by + Retraction Watch theo DOI",
        "tong": tong, "ket_qua": ket_qua,
        "disclaimer": "Cần bác sĩ kiểm chứng. «ok» chỉ khi một nguồn ĐÃ lấy được bản ghi; mã không kết luận được giữ "
                      "trạng thái không biết — KHÔNG phải «chưa bị rút».",
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return p


def doc_ket_qua(out_dir: Path, study: str) -> Dict[str, Any]:
    try:
        j = json.loads((Path(out_dir) / TEP.format(study=study)).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return j if isinstance(j, dict) and j.get("schema") == SCHEMA else {}


def main(argv: Optional[List[str]] = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Kiểm rút bài cho từng trích dẫn của đề tài (TLTK + danh mục)")
    ap.add_argument("--study", required=True)
    ap.add_argument("--repo-root", default=str(ROOT))
    ap.add_argument("--ghi", action="store_true", help="Ghi exports/<mã>/KIEM_RUT_BAI_TRICH_DAN_<mã>.json")
    a = ap.parse_args(argv)
    out_dir = Path(a.repo_root) / "exports" / a.study
    muc = thu_thap(out_dir, a.study)
    if not muc:
        print("Không có trích dẫn nào có PMID/DOI (chưa có TLTK đề cương nộp lẫn danh mục trích dẫn).")
        return 3
    kq = kiem(muc)
    duong = {k: v for k, v in kq.items() if v["status"] in DUONG_TINH}
    khong_biet = {k: v for k, v in kq.items() if v["status"] not in CO_PHAN_QUYET}
    print(f"Kiểm rút bài {len(kq)} trích dẫn — {a.study}")
    for k, v in sorted(kq.items(), key=lambda x: x[1]["nguon"]):
        dau = "🔴" if k in duong else ("⚪" if k in khong_biet else "🟢")
        print(f"  {dau} {v['nguon']:<16} {k:<40} {v['status']} ({v['source'] or '—'})")
    if a.ghi:
        print(f"Đã ghi {ghi(out_dir, a.study, kq).name}")
    else:
        print("Chạy khô — thêm --ghi để ghi kết quả theo từng mã.")
    print("Cần bác sĩ kiểm chứng.")
    return 1 if duong else (2 if khong_biet else 0)


if __name__ == "__main__":
    sys.exit(main())
