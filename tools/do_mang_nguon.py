#!/usr/bin/env python3
"""Đo đường mạng tới TỪNG nguồn chứng cứ và phân loại kiểu bị chặn — để so hai đường mạng (vd VPN BẬT với VPN TẮT).

Vì sao (01/10/2026, bác sĩ yêu cầu «giải quyết vấn đề VPN triệt để»): nguồn nào bị chặn phụ thuộc IP thoát ra Internet
LÚC ĐO, không cố định theo «VPN bật/tắt» (ECDC chạy qua VPN ngày 21/09, bị CloudFront chặn qua VPN ngày 29/09; NCBI chặn
IP trực tiếp 01→16/09). Quyết định bật/tắt VPN — hoặc tách tuyến cho ứng dụng nào — là của BÁC SĨ; công cụ này chỉ
cho số đo để quyết: chạy một lần ở mỗi đường, ghi JSON, rồi `--so-sanh`.

Chỉ ĐỌC: mỗi nguồn MỘT yêu cầu nhỏ, không thử lại, hết giờ 12 giây; không gọi nguồn tính phí (Consensus, SerpApi).
Scopus tốn hạn mức của tổ chức nên chỉ đo khi thêm `--co-scopus` (1 yêu cầu). Phân loại dùng CHUNG bộ nhận diện với
engine (`app.utils.http.nhan_trang_chan`/`nhan_loi_ket_noi`) — nhãn ở đây khớp nhãn trong Source Log. Dấu vân đường
mạng lấy tại máy (`app.utils.mang`), không tra IP ở dịch vụ ngoài. Khoá API đọc từ cấu hình engine, KHÔNG in ra.

Dùng (từ thư mục repo y khoa, venv ~/.ebm-venv):
    python tools/do_mang_nguon.py [--co-scopus] [--ghi <tệp.json>] [--json]
    python tools/do_mang_nguon.py --so-sanh <đường-A.json> <đường-B.json>
Mã thoát: 0 = đo xong (kể cả có nguồn bị chặn) · 2 = tham số/tệp sai.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple
from urllib.parse import urlparse

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import requests  # noqa: E402

from app.utils.http import nhan_loi_ket_noi, nhan_trang_chan  # noqa: E402
from app.utils.mang import dau_van_mang, mo_ta_ngan  # noqa: E402

UA_ENGINE = "Mozilla/5.0 (compatible; medical-ebm-automation/0.1; RSS reader; +https://example.org/bot)"
HET_GIO = 12
DOC_TOI_DA = 20000
NHOM_LOI = "lõi khám phá"
NHOM_AN_TOAN = "an toàn thuốc"
NHOM_GUIDELINE = "guideline/feed"
NHOM_PHU = "phụ trợ"

# (tên, nhóm, url, params, headers, mã HTTP coi là «tới được»)
Diem = Tuple[str, str, str, Dict[str, str], Dict[str, str], Tuple[int, ...]]


def danh_sach_diem(cfg: Any, co_scopus: bool = False) -> List[Diem]:
    """Một yêu cầu nhỏ mỗi nguồn, đúng máy chủ engine dùng."""
    email = getattr(cfg, "ncbi_email", "") or getattr(cfg, "openalex_email", "") or ""
    ncbi = {"db": "pubmed", "term": "heart failure", "retmax": "1", "retmode": "json", "tool": "medical-ebm-automation",
            "email": email}
    if getattr(cfg, "ncbi_api_key", ""):
        ncbi["api_key"] = cfg.ncbi_api_key
    rss = {"User-Agent": UA_ENGINE}
    ds: List[Diem] = [
        ("NCBI E-utilities (PubMed)", NHOM_LOI, "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi", ncbi, {},
         (200,)),
        ("Europe PMC", NHOM_LOI, "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
         {"query": "heart failure", "pageSize": "1", "format": "json"}, {}, (200,)),
        ("Crossref", NHOM_LOI, "https://api.crossref.org/works", {"rows": "1", "mailto": email}, {}, (200,)),
        ("OpenAlex", NHOM_PHU, "https://api.openalex.org/works", {"per-page": "1", "mailto": email}, {}, (200,)),
        ("ClinicalTrials.gov", NHOM_PHU, "https://clinicaltrials.gov/api/v2/studies", {"pageSize": "1"}, {}, (200,)),
        ("openFDA", NHOM_AN_TOAN, "https://api.fda.gov/drug/label.json", {"limit": "1"}, {}, (200,)),
        ("FDA MedWatch — RSS", NHOM_AN_TOAN,
         "https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/medwatch/rss.xml", {}, rss, (200,)),
        ("MHRA Drug Safety Update", NHOM_AN_TOAN, "https://www.gov.uk/drug-safety-update.atom", {}, rss, (200,)),
        ("EMA — tệp thuốc JSON", NHOM_AN_TOAN,
         "https://www.ema.europa.eu/en/documents/report/medicines-output-medicines_json-report_en.json", {},
         {"Range": "bytes=0-2047"}, (200, 206)),
        ("DailyMed", NHOM_AN_TOAN, "https://dailymed.nlm.nih.gov/dailymed/services/v2/spls.json", {"pagesize": "1"},
         {}, (200,)),
        ("RxNorm (RxNav)", NHOM_AN_TOAN, "https://rxnav.nlm.nih.gov/REST/rxcui.json", {"name": "metformin"}, {},
         (200,)),
        ("ECDC — feed mối đe doạ", NHOM_GUIDELINE, "https://www.ecdc.europa.eu/en/taxonomy/term/2942/feed", {}, rss,
         (200,)),
        ("WHO IRIS — OAI-PMH", NHOM_GUIDELINE, "https://iris.who.int/oai/request", {"verb": "Identify"}, {}, (200,)),
        ("NEJM — RSS (nay engine đọc qua Crossref)", NHOM_GUIDELINE, "https://www.nejm.org/action/showFeed",
         {"type": "etoc", "feed": "rss", "jc": "nejm"}, rss, (200,)),
        ("CDC MMWR — RSS", NHOM_GUIDELINE, "https://tools.cdc.gov/api/v2/resources/media/132036.rss", {}, rss, (200,)),
        ("Bộ Y tế VN — kcb.vn", NHOM_GUIDELINE, "https://kcb.vn/phac-do", {}, {}, (200,)),
        ("GOLD — feed", NHOM_GUIDELINE, "https://goldcopd.org/feed/", {}, rss, (200,)),
        ("GINA — feed", NHOM_GUIDELINE, "https://ginasthma.org/feed/", {}, rss, (200,)),
        ("BJGP — RSS", NHOM_GUIDELINE, "https://bjgp.org/rss/current.xml", {}, rss, (200,)),
        ("Unpaywall", NHOM_PHU, "https://api.unpaywall.org/v2/10.1056/nejmoa2204233", {"email": email}, {}, (200,)),
        ("Semantic Scholar (không khoá)", NHOM_PHU, "https://api.semanticscholar.org/graph/v1/paper/search",
         {"query": "heart failure", "limit": "1"}, {}, (200,)),
        ("scite (công khai)", NHOM_PHU, "https://api.scite.ai/tallies/10.1056/nejmoa2204233", {}, {}, (200,)),
        # Không có token TDM thì máy chủ Wiley trả 400 — vẫn là «tới được», đúng thứ cần đo.
        ("Wiley TDM API (chỉ chạm máy chủ)", NHOM_PHU,
         "https://api.wiley.com/onlinelibrary/tdm/v1/articles/10.1002%2Fjcsm.70385", {}, {}, (200, 400)),
        ("GitHub API (cảm biến CI)", NHOM_PHU, "https://api.github.com/zen", {}, {}, (200,)),
    ]
    if getattr(cfg, "core_api_key", ""):
        ds.append(("CORE", NHOM_PHU, "https://api.core.ac.uk/v3/search/works", {"q": "heart failure", "limit": "1"},
                   {"Authorization": f"Bearer {cfg.core_api_key}"}, (200,)))
    if co_scopus and getattr(cfg, "scopus_api_key", ""):
        ds.append(("Scopus (1 yêu cầu hạn mức)", NHOM_PHU, "https://api.elsevier.com/content/search/scopus",
                   {"query": "TITLE(heart failure)", "count": "1"},
                   {"X-ELS-APIKey": cfg.scopus_api_key, "Accept": "application/json"}, (200,)))
    return ds


def phan_loai(resp: Any, loi: Optional[BaseException], ma_toi_duoc: Sequence[int] = (200,)) -> str:
    """Nhãn kết quả một lần đo — CÙNG tên nhãn với Source Log của engine (không ngoặc)."""
    if loi is not None:
        nhan = nhan_loi_ket_noi(loi)
        if nhan:
            return nhan[1:-1]
        if isinstance(loi, requests.exceptions.ReadTimeout):
            return "doc-het-gio"
        return f"LOI_{type(loi).__name__}"
    url_cuoi = str(getattr(resp, "url", "") or "")
    than = str(getattr(resp, "text", "") or "")[:400].lower()
    if (urlparse(url_cuoi).netloc.endswith("misuse.ncbi.nlm.nih.gov")
            or "blocked diagnostic" in than or "blocked for possible abuse" in than):
        return "ncbi-chan"
    ma = getattr(resp, "status_code", None)
    if ma in tuple(ma_toi_duoc):
        return "OK"
    nhan = nhan_trang_chan(resp)
    if nhan:
        return nhan[1:-1]
    return f"HTTP_{ma}"


def _goi(url: str, params: Dict[str, str], headers: Dict[str, str]) -> Tuple[Any, Optional[BaseException]]:
    tieu_de = {"User-Agent": headers.get("User-Agent", "medical-ebm-automation/0.1 (+https://example.org)")}
    tieu_de.update({k: v for k, v in headers.items() if k != "User-Agent"})
    try:
        r = requests.get(url, params=params, headers=tieu_de, timeout=HET_GIO, allow_redirects=True, stream=True)
    except Exception as exc:  # noqa: BLE001 — mọi lỗi vận chuyển đều là một kết quả đo
        return None, exc
    try:
        r._content = r.raw.read(DOC_TOI_DA, decode_content=True)  # chỉ đọc phần đầu phản hồi
    except Exception as exc:  # noqa: BLE001
        r.close()
        return None, exc
    r.close()
    return r, None


def do(cfg: Any, co_scopus: bool = False, goi=_goi) -> Dict[str, Any]:
    kq: Dict[str, Any] = {"mang": dau_van_mang(), "nguon": {}}
    for ten, nhom, url, params, headers, ma_ok in danh_sach_diem(cfg, co_scopus):
        t = time.monotonic()
        r, loi = goi(url, params, headers)
        kq["nguon"][ten] = {"nhom": nhom, "ket_qua": phan_loai(r, loi, ma_ok), "giay": round(time.monotonic() - t, 1),
                            "http": getattr(r, "status_code", None)}
    return kq


def in_bang(kq: Dict[str, Any]) -> None:
    print(f"Đường mạng lúc đo: {mo_ta_ngan(kq.get('mang'))}")
    for nhom in (NHOM_LOI, NHOM_AN_TOAN, NHOM_GUIDELINE, NHOM_PHU):
        dong = [(t, v) for t, v in kq["nguon"].items() if v.get("nhom") == nhom]
        if not dong:
            continue
        print(f"\n[{nhom}] {sum(1 for _, v in dong if v['ket_qua'] == 'OK')}/{len(dong)} tới được")
        for ten, v in dong:
            print(f"  {'✓' if v['ket_qua'] == 'OK' else '✗'} {ten:42} {v['ket_qua']:18} {v['giay']:5.1f}s")


def so_sanh(a: Dict[str, Any], b: Dict[str, Any]) -> List[str]:
    """Bảng so hai lần đo + bốn nhóm sự thật. KHÔNG khuyến nghị bật/tắt VPN — đó là quyết định của bác sĩ."""
    ra = [f"A: {mo_ta_ngan(a.get('mang'))} — đo lúc {(a.get('mang') or {}).get('luc')}",
          f"B: {mo_ta_ngan(b.get('mang'))} — đo lúc {(b.get('mang') or {}).get('luc')}", ""]
    chi_a, chi_b, ca_hai_hong, ca_hai_ok = [], [], [], []
    for ten in sorted(set(a.get("nguon", {})) | set(b.get("nguon", {}))):
        ka = (a.get("nguon", {}).get(ten) or {}).get("ket_qua", "—")
        kb = (b.get("nguon", {}).get(ten) or {}).get("ket_qua", "—")
        ra.append(f"{'  ' if ka == kb else '≠ '}{ten:42} A={ka:18} B={kb}")
        if "—" in (ka, kb):
            continue
        if ka == "OK" and kb == "OK":
            ca_hai_ok.append(ten)
        elif ka == "OK":
            chi_a.append(f"{ten} (B: {kb})")
        elif kb == "OK":
            chi_b.append(f"{ten} (A: {ka})")
        else:
            ca_hai_hong.append(f"{ten} (A: {ka}, B: {kb})")
    ra += ["", f"Chạy được trên CẢ HAI đường: {len(ca_hai_ok)} nguồn",
           f"CHỈ chạy được trên đường A: {'; '.join(chi_a) or 'không có'}",
           f"CHỈ chạy được trên đường B: {'; '.join(chi_b) or 'không có'}",
           f"Hỏng trên cả hai: {'; '.join(ca_hai_hong) or 'không có'}",
           "Một lần đo là ảnh chụp: IP thoát của VPN đổi theo máy chủ, IP trực tiếp cũng có lúc bị gắn cờ — "
           "đo lại khi đổi mạng/máy chủ VPN."]
    return ra


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--ghi", help="ghi kết quả JSON vào tệp này")
    ap.add_argument("--json", action="store_true", help="in JSON thay cho bảng")
    ap.add_argument("--co-scopus", action="store_true", help="đo cả Scopus (tốn 1 yêu cầu hạn mức của tổ chức)")
    ap.add_argument("--so-sanh", nargs=2, metavar=("A.json", "B.json"), help="so hai lần đo đã ghi")
    a = ap.parse_args(argv)
    if a.so_sanh:
        try:
            hai = [json.loads(Path(p).read_text(encoding="utf-8")) for p in a.so_sanh]
        except (OSError, ValueError) as exc:
            print(f"Không đọc được tệp đo: {exc}", file=sys.stderr)
            return 2
        print("\n".join(so_sanh(*hai)))
        return 0
    from app.config import settings
    kq = do(settings, co_scopus=a.co_scopus)
    if a.json:
        print(json.dumps(kq, ensure_ascii=False, indent=2))
    else:
        in_bang(kq)
    if a.ghi:
        Path(a.ghi).write_text(json.dumps(kq, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
        print(f"\nđã ghi {a.ghi}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
