#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""«ĐỌC BÀI HỘ» — gom TOÀN VĂN PMC Open Access cho nền y văn một đề tài (PHA R5).

Vì sao: SciSpace-class tools đọc toàn văn hộ người dùng; hệ này mới thẩm định
trên abstract và gate phần thiếu toàn văn bằng nhãn «thẩm định một phần» (LÔ D
PHA 4). Mảnh còn thiếu là LẤY được toàn văn ở nơi HỢP PHÁP duy nhất máy được
phép: PubMed Central Open Access (P5 — không cào nguồn trả phí, không mirror lậu).

Trung thực độ phủ: OA chỉ là MỘT PHẦN y văn. Bài không có PMC-OA được liệt kê
rõ «cần quyền truy cập của bác sĩ» — không lách, không đoán. Tải về là XML JATS
của PMC (máy đọc tốt cho trích xuất; bác sĩ đọc bản HTML trên PMC qua link in kèm).

Dùng:  python3 tools/gom_toan_van_oa.py --study ZZPHA-R-AUTO-DEMO
       python3 tools/gom_toan_van_oa.py --pmids 12345 67890 --out <thư mục>
Mã thoát: 0 = chạy trọn (kể cả 0%% OA — độ phủ thấp là SỰ THẬT, không phải lỗi)
· 2 = hạ tầng (không đọc được artifact/mạng chết toàn phần).
"""
from __future__ import annotations

import argparse
import http.client
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

HERE = Path(__file__).resolve().parent
EXPORTS = HERE.parent / "exports"
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
MAILTO = "bsluanbv175@gmail.com"


def _goi(url: str, thu: int = 3) -> bytes:
    """GET có RETRY — đo thật 15/08: kho 600 PMID chết giữa chừng ở file thứ 17 vì
    một IncompleteRead đơn lẻ (mạng nháy), mất cả lượt chạy dài. Mạng nháy là
    thường lệ ở lô lớn; lỗi lần cuối mới được ném ra."""
    req = urllib.request.Request(url, headers={"User-Agent": f"EBM-toan-van-oa/1.0 ({MAILTO})"})
    loi: Exception | None = None
    for lan in range(thu):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read()
        except (urllib.error.URLError, OSError, http.client.HTTPException) as e:
            loi = e
            time.sleep(1.5 * (lan + 1))
    raise loi  # type: ignore[misc]


def pmids_tu_g0(study: str) -> list[str]:
    a = EXPORTS / study / f"G0_A1_PICO_FINER_{study}.md"
    if not a.exists():
        return []
    return sorted(set(re.findall(r"PMID[: ]*(\d{7,9})", a.read_text(encoding="utf-8",
                                                                    errors="replace"))))


def _parse_linksets(d: dict) -> dict[str, str]:
    """Bóc PMID→PMCID từ JSON elink. TÁCH RIÊNG để test được không cần mạng.

    🔴 CHỈ nhận linkname == "pubmed_pmc" (CHÍNH bài đó trong PMC). Bẫy đo thật
    15/08 — nguy hiểm nhất từ đầu dự án toàn văn: bài KHÔNG có trong PMC (vd
    Polit & Beck 17654487) vẫn trả linkset `pubmed_pmc_refs` = danh sách các bài
    TRÍCH DẪN nó (1.678 link!); bản đầu của hàm vơ mọi dbto=="pmc" nên đã gắn
    TOÀN VĂN CỦA BÀI KHÁC vào PMID gốc — mọi phép đọc/đối chiếu hạ nguồn chạy
    trên văn bản sai mà không hề báo lỗi. Chính vòng thẩm định toàn văn (⚪ hàng
    loạt ở ngưỡng kinh điển 0,78) mới lộ ra."""
    ra: dict[str, str] = {}
    for ls in d.get("linksets", []):
        pm = (ls.get("ids") or [None])[0]
        for db in ls.get("linksetdbs", []):
            if (db.get("dbto") == "pmc" and db.get("linkname") == "pubmed_pmc"
                    and db.get("links")):
                ra[str(pm)] = str(db["links"][0])
    return ra


def lien_ket_pmc(pmids: list[str], co_lo: int = 50) -> dict[str, str]:
    """PMID → PMCID qua elink, CHIA LÔ. Vắng mặt = KHÔNG có bản PMC.

    Hai bẫy elink đã đo thật, đừng gỡ:
    - 15/08 sáng: gộp ID bằng dấu phẩy làm NCBI TRỘN links vào một linkset —
      mất ánh xạ theo-từng-ID (1/8 thay vì 6/8). Phải lặp `&id=` từng mã.
    - 15/08 chiều: lặp `&id=` cho ~600 mã trong MỘT URL → NCBI trả HTTPError
      (URL quá dài) — cả kho dashboard không gom được bài nào. Chia lô ≤50,
      nghỉ 0.34s giữa lô (đúng nhịp E-utilities không khoá)."""
    ra: dict[str, str] = {}
    for i in range(0, len(pmids), max(1, co_lo)):
        lo = pmids[i:i + co_lo]
        u = (f"{EUTILS}/elink.fcgi?dbfrom=pubmed&db=pmc&retmode=json"
             + "".join(f"&id={p}" for p in lo) + f"&tool=ebm&email={MAILTO}")
        ra.update(_parse_linksets(json.loads(_goi(u).decode("utf-8", "replace"))))
        if i + co_lo < len(pmids):
            time.sleep(0.34)
    return ra


def tai_toan_van(pmcid: str) -> bytes | None:
    """Toàn văn JATS XML từ PMC. PMC chặn/không OA → None (không đoán).

    Bắt CẢ `http.client.HTTPException` (gồm `IncompleteRead`) — `_goi()` có
    thể ném lỗi này sau khi hết 3 lần retry (đúng sự cố 15/08 đã ghi trong
    docstring của `_goi()`), và nó KHÔNG phải lớp con của `OSError`/
    `URLError`. Thiếu nhánh này thì một mạng nháy giữa batch sẽ làm crash cả
    lượt gom thay vì trả `None` đúng hợp đồng của hàm."""
    u = f"{EUTILS}/efetch.fcgi?db=pmc&id={pmcid}&retmode=xml&tool=ebm&email={MAILTO}"
    try:
        xml = _goi(u)
    except (urllib.error.URLError, OSError, http.client.HTTPException):
        return None
    # Bài PMC KHÔNG thuộc tập OA trả về stub không có <body> — đó là «không lấy
    # được hợp pháp», phải phân biệt với bài OA thật (có thân bài).
    return xml if b"<body" in xml else None


def main() -> int:
    ap = argparse.ArgumentParser(description="Gom toàn văn PMC-OA cho nền y văn đề tài")
    ap.add_argument("--study")
    ap.add_argument("--pmids", nargs="*")
    ap.add_argument("--out")
    a = ap.parse_args()
    if a.study:
        pmids = pmids_tu_g0(a.study)
        out = EXPORTS / a.study / "toan_van_oa"
    elif a.pmids:
        pmids = [str(p) for p in a.pmids]
        out = Path(a.out or "toan_van_oa")
    else:
        ap.error("cần --study hoặc --pmids")
    if not pmids:
        print("🔴 Không rút được PMID nào từ G0 artifact — chạy G0 trước.")
        return 2

    print(f"«Đọc bài hộ» — {len(pmids)} PMID nền · nguồn HỢP PHÁP duy nhất: PMC Open Access")
    try:
        anh_xa = lien_ket_pmc(pmids)
    except (urllib.error.URLError, OSError, ValueError, http.client.HTTPException) as exc:
        print(f"🔴 HẠ TẦNG: elink không trả lời ({type(exc).__name__}) — chưa gom được, "
              "KHÔNG kết luận gì về độ phủ OA.")
        return 2
    out.mkdir(parents=True, exist_ok=True)
    co_oa, khong_pmc, khong_oa = [], [], []
    for pm in pmids:
        pmcid = anh_xa.get(pm)
        if not pmcid:
            khong_pmc.append(pm)
            continue
        xml = tai_toan_van(pmcid)
        time.sleep(0.34)
        if xml:
            (out / f"PMID-{pm}_PMC{pmcid}.xml").write_bytes(xml)
            co_oa.append(pm)
        else:
            khong_oa.append((pm, pmcid))

    bc = out / "DO-PHU-OA.md"
    dong = [f"# ĐỘ PHỦ TOÀN VĂN OA — {date.today().isoformat()}", "",
            f"- Tải được toàn văn OA: **{len(co_oa)}/{len(pmids)}** "
            f"({100 * len(co_oa) // max(1, len(pmids))}%) → XML JATS trong thư mục này",
            f"- Có bản PMC nhưng KHÔNG thuộc tập OA (máy không lấy — P5): "
            f"{len(khong_oa)}" + (f" — {[p for p, _ in khong_oa][:6]}" if khong_oa else ""),
            f"- Không có bản PMC: {len(khong_pmc)}"
            + (f" — {khong_pmc[:6]}" if khong_pmc else ""),
            "", "> Phần không-OA cần QUYỀN TRUY CẬP CỦA BÁC SĨ (thư viện/tài khoản) — "
            "[CẦN XÁC NHẬN TẠI ĐƠN VỊ]. Độ phủ thấp là SỰ THẬT về OA, không phải lỗi. "
            "Đọc bản trình bày: https://pmc.ncbi.nlm.nih.gov/articles/PMC<id>/ . "
            "Cần bác sĩ kiểm chứng."]
    bc.write_text("\n".join(dong) + "\n", encoding="utf-8", newline="\n")
    try:
        duong_in = bc.resolve().relative_to(EXPORTS.parent)
    except ValueError:  # --out là đường dẫn tương đối/ngoài repo — in nguyên trạng
        duong_in = bc
    print(f"  OA {len(co_oa)}/{len(pmids)} · không-OA {len(khong_oa)} · "
          f"không-PMC {len(khong_pmc)} → {duong_in}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
