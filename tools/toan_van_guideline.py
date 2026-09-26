#!/usr/bin/env python3
"""toan_van_guideline.py — Đọc TOÀN VĂN guideline cho agent (tra-cuu-chung-cu, huong-dan-lam-sang) — thêm 24/09/2026.

Nối bốn connector toàn văn vốn «mồ côi» (chỉ export, không ai gọi): GOLD · GINA · PMC (S3 công khai) · BTS.
Cùng khuôn `tools/tra_thuoc_quoc_te.py`. Chỉ tải từ nguồn đã khảo sát robots.txt/điều khoản; KHÔNG vượt
Cloudflare/đăng nhập; KHÔNG tải nội dung NICE (điều khoản đòi giấy phép AI trả phí).

Dùng:
    python3 medical-ebm-automation/tools/toan_van_guideline.py gold [--url <PDF goldcopd.org>] [--tim "<cụm từ>"]
    python3 medical-ebm-automation/tools/toan_van_guideline.py gina [--url <PDF ginasthma.org>] [--tim "<cụm từ>"]
    python3 medical-ebm-automation/tools/toan_van_guideline.py pmc <PMCID> [--tim "<cụm từ>"]
    python3 medical-ebm-automation/tools/toan_van_guideline.py bts <URL PDF brit-thoracic.org.uk> [--tim "<cụm từ>"]
    python3 medical-ebm-automation/tools/toan_van_guideline.py trich-dan --doi <DOI> | --pmid <PMID>   (đường lùi)
Tuỳ chọn chung: --tim (lặp được) · --ngu-canh 300 · --toi-da-khop 10 · --toan-bo · --gioi-han N ·
                --luu <tệp NGOÀI repo> · --doi/--pmid (để gợi ý đường lùi khi tải thất bại) · --json

In ra: metadata (tổ chức, URL nguồn, năm/phiên bản suy từ URL, số ký tự, số trang, SHA-256 tệp nguồn, ngày tải)
+ ghi chú bản quyền. Có --tim: đoạn quanh từ khoá kèm vị trí ký tự và số trang. KHÔNG bao giờ in toàn văn.
Mặc định không --tim: trích tới 200.000 ký tự (như connector); có --tim: tìm trong TOÀN BỘ tài liệu.

Mã thoát: 0 = tải được (và mọi --tim đều khớp) · 1 = tải được nhưng có --tim KHÔNG khớp ·
          2 = LỖI/KHÔNG BIẾT (mạng, bị chặn, nguồn đổi cấu trúc, không có trong PMC OA) ·
          3 = connector CHƯA BẬT (cờ ENABLE_* tắt) · 4 = đầu vào bị từ chối (URL ngoài nguồn đã khảo sát,
          NICE, PMCID sai, --luu trong repo).
Chỉ là nguồn tham chiếu nội bộ để trích câu chữ kèm nguồn; cần bác sĩ kiểm chứng.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from app.sources.guideline_fulltext_common import (  # noqa: E402
    GHI_CHU_BAN_QUYEN_CHUAN,
    GIOI_HAN_KY_TU_MAC_DINH,
    ConnectorChuaBat,
    KetQuaToanVanGuideline,
    trang_cua_vi_tri,
)

DISCLAIMER = "Cần bác sĩ kiểm chứng."
MA_OK, MA_KHONG_KHOP, MA_LOI, MA_CHUA_BAT, MA_TU_CHOI = 0, 1, 2, 3, 4

# Domain được phép theo từng nguồn — đúng các domain đã khảo sát robots.txt/điều khoản (xem CLAUDE.md).
DOMAIN_CHO_PHEP = {"gold": ("goldcopd.org",), "gina": ("ginasthma.org",), "bts": ("brit-thoracic.org.uk",)}
DOMAIN_CAM = ("nice.org.uk",)  # giấy phép AI trả phí — không tải, bất kể nguồn nào


def _thuoc_domain(url: str, cac_domain: tuple) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return any(host == d or host.endswith("." + d) for d in cac_domain)


def kiem_url(nguon: str, url: Optional[str]) -> Optional[str]:
    """Lý do TỪ CHỐI url (None = chấp nhận). Kiểm TRƯỚC khi dựng connector ⇒ không gọi mạng."""
    if url is None:
        return None
    if urlparse(url).scheme != "https":
        return f"URL phải là https: {url}"
    if _thuoc_domain(url, DOMAIN_CAM):
        return ("URL thuộc nice.org.uk — điều khoản NICE đòi giấy phép + phí cho mọi truy cập phục vụ AI; "
                "KHÔNG tải. Chỉ bác sĩ tự xin cấp phép mới gỡ được.")
    if not _thuoc_domain(url, DOMAIN_CHO_PHEP[nguon]):
        return (f"URL không thuộc {DOMAIN_CHO_PHEP[nguon]} (nguồn đã khảo sát cho «{nguon}») — từ chối để không "
                "tải từ domain chưa kiểm robots.txt/điều khoản.")
    return None


def kiem_duong_luu(duong: str) -> Optional[str]:
    """Không cho lưu toàn văn vào cây repo (tránh commit/phân phối lại nội dung có bản quyền)."""
    p = Path(duong).expanduser().resolve()
    try:
        p.relative_to(REPO)
    except ValueError:
        return None
    return (f"Không lưu toàn văn vào trong repo ({REPO.name}/) — dễ bị commit/phân phối lại. "
            "Chọn đường dẫn NGOÀI repo (vd thư mục tạm).")


def nam_phien_ban(url: str) -> Dict[str, Optional[str]]:
    """Năm/phiên bản SUY TỪ URL/tên tệp (không bịa): không thấy thì None."""
    ten = urlparse(url).path.rsplit("/", 1)[-1]
    nam = re.findall(r"(?<!\d)(20\d\d)(?!\d)", ten) or re.findall(r"(?<!\d)(20\d\d)(?!\d)", url)
    pb = re.search(r"(?i)(?<![a-z])v(\d+(?:[._]\d+)*)", ten)
    pmc = re.search(r"(PMC\d+)\.(\d+)\.txt$", ten)
    return {
        "nam_suy_tu_url": max(nam) if nam else None,
        "phien_ban_suy_tu_url": (pb.group(1).replace("_", ".") if pb else (pmc.group(2) if pmc else None)),
    }


def _mau_tim(cum: str) -> "re.Pattern[str]":
    """Khớp không phân biệt hoa/thường, chấp nhận xuống dòng/nhiều dấu cách giữa các từ (PDF hay ngắt dòng)."""
    tu = [re.escape(t) for t in cum.split()]
    return re.compile(r"\s+".join(tu), re.IGNORECASE)


def tim_trong_van_ban(van_ban: str, cum: str, moc_trang: list, ngu_canh: int, toi_da: int) -> Dict[str, Any]:
    khop = list(_mau_tim(cum).finditer(van_ban)) if cum.split() else []
    doan = []
    for m in khop[:toi_da]:
        a, b = max(0, m.start() - ngu_canh), min(len(van_ban), m.end() + ngu_canh)
        doan.append({
            "vi_tri_ky_tu": m.start(),
            "trang": trang_cua_vi_tri(moc_trang, m.start()),
            "doan": ("…" if a > 0 else "") + " ".join(van_ban[a:b].split()) + ("…" if b < len(van_ban) else ""),
        })
    return {"cum_tu": cum, "so_khop": len(khop), "hien_thi": len(doan), "doan": doan}


def _dung_client(nguon: str):
    if nguon == "gold":
        from app.sources.gold_copd import GoldCopdFullTextClient
        return GoldCopdFullTextClient()
    if nguon == "gina":
        from app.sources.gina_asthma import GinaAsthmaFullTextClient
        return GinaAsthmaFullTextClient()
    if nguon == "bts":
        from app.sources.bts_guidelines import BtsGuidelineFullTextClient
        return BtsGuidelineFullTextClient()
    from app.sources.pmc_guideline_fulltext import PmcGuidelineFullTextClient
    return PmcGuidelineFullTextClient()


def tai(nguon: str, dinh_danh: Optional[str], gioi_han: Optional[int]) -> KetQuaToanVanGuideline:
    client = _dung_client(nguon)  # ConnectorChuaBat nếu cờ tắt
    if nguon in ("gold", "gina"):
        return client.tai_toan_van_pdf(dinh_danh, gioi_han_ky_tu=gioi_han)
    return client.tai_toan_van(dinh_danh, gioi_han_ky_tu=gioi_han)


def goi_y_duong_lui(doi: Optional[str], pmid: Optional[str]) -> str:
    if doi or pmid:
        tham_so = " ".join(x for x in (f'--doi "{doi}"' if doi else "", f"--pmid {pmid}" if pmid else "") if x)
        return ("Đường lùi (trích dẫn + TÓM TẮT của tác giả, KHÔNG phải toàn văn): "
                f"python3 medical-ebm-automation/tools/toan_van_guideline.py trich-dan {tham_so}")
    return ("Có DOI/PMID của guideline thì thêm --doi/--pmid để được gợi ý đường lùi trích dẫn + tóm tắt "
            "(app/sources/guideline_citation_summary.py).")


def xu_ly_tai(args) -> Dict[str, Any]:
    nguon = args.nguon
    dinh_danh = getattr(args, "dinh_danh", None) or getattr(args, "url", None)
    out: Dict[str, Any] = {"nguon": nguon, "dinh_danh": dinh_danh, "ghi_chu_ban_quyen": GHI_CHU_BAN_QUYEN_CHUAN}
    if nguon in DOMAIN_CHO_PHEP:
        ly_do = kiem_url(nguon, dinh_danh)
        if ly_do:
            return {**out, "trang_thai": "tu_choi", "ly_do": ly_do, "ma_thoat": MA_TU_CHOI}
    if args.luu:
        ly_do = kiem_duong_luu(args.luu)
        if ly_do:
            return {**out, "trang_thai": "tu_choi", "ly_do": ly_do, "ma_thoat": MA_TU_CHOI}
    gioi_han: Optional[int]
    if args.gioi_han is not None:
        gioi_han = args.gioi_han
    elif args.toan_bo or args.tim:
        gioi_han = None  # tìm từ khoá phải tìm TOÀN BỘ tài liệu, không chỉ 200.000 ký tự đầu
    else:
        gioi_han = GIOI_HAN_KY_TU_MAC_DINH
    try:
        kq = tai(nguon, dinh_danh, gioi_han)
    except ConnectorChuaBat as exc:
        return {**out, "trang_thai": "chua_bat", "ly_do": str(exc), "ma_thoat": MA_CHUA_BAT}
    except Exception as exc:  # noqa: BLE001 — lỗi ngoài dự kiến: nói rõ, không traceback
        return {**out, "trang_thai": "loi", "ly_do": f"{exc.__class__.__name__}: {exc}"[:500],
                "goi_y": goi_y_duong_lui(args.doi, args.pmid), "ma_thoat": MA_LOI}
    ngay_tai = datetime.now(timezone.utc).isoformat(timespec="seconds")
    if not kq.thanh_cong:
        ly_do = kq.ghi_chu or "không rõ"
        tu_choi = nguon == "pmc" and "không đúng định dạng PMCID" in ly_do
        return {**out, "to_chuc": kq.to_chuc, "url_nguon": kq.url_nguon, "ngay_thu": ngay_tai,
                "trang_thai": "tu_choi" if tu_choi else "loi", "ly_do": ly_do,
                "goi_y": None if tu_choi else goi_y_duong_lui(args.doi, args.pmid),
                "ma_thoat": MA_TU_CHOI if tu_choi else MA_LOI}
    van_ban = kq.van_ban_trich or ""
    out.update({
        "trang_thai": "tai_duoc", "to_chuc": kq.to_chuc, "url_nguon": kq.url_nguon, "ngay_tai": ngay_tai,
        **nam_phien_ban(kq.url_nguon),
        "so_ky_tu": len(van_ban), "so_trang_pdf": kq.so_trang_pdf, "bi_cat": kq.bi_cat,
        "gioi_han_ky_tu": gioi_han, "sha256_nguon": kq.sha256_nguon,
        "ghi_chu": kq.ghi_chu, "ghi_chu_ban_quyen": kq.ghi_chu_ban_quyen,
    })
    ma = MA_OK
    if args.tim:
        out["tim"] = [tim_trong_van_ban(van_ban, c, kq.moc_trang, args.ngu_canh, args.toi_da_khop)
                      for c in args.tim]
        if kq.bi_cat:
            out["canh_bao_tim"] = "Văn bản bị cắt — chỉ tìm trong phần đã trích; bỏ --gioi-han để tìm toàn bộ."
        if any(t["so_khop"] == 0 for t in out["tim"]):
            ma = MA_KHONG_KHOP
    if args.luu:
        dich = Path(args.luu).expanduser()
        dich.parent.mkdir(parents=True, exist_ok=True)
        dich.write_text(van_ban, encoding="utf-8", newline="\n")
        out["da_luu_noi_bo"] = str(dich)
    out["ma_thoat"] = ma
    return out


def xu_ly_trich_dan(args) -> Dict[str, Any]:
    from app.sources.guideline_citation_summary import lay_trich_dan_tom_tat
    try:
        kq = lay_trich_dan_tom_tat(doi=args.doi, pmid=args.pmid)
    except Exception as exc:  # noqa: BLE001
        return {"nguon": "trich-dan", "trang_thai": "loi", "ly_do": f"{exc.__class__.__name__}: {exc}"[:500],
                "ma_thoat": MA_LOI}
    from dataclasses import asdict
    d = asdict(kq)
    if not (args.doi or args.pmid):
        ma = MA_TU_CHOI  # thiếu định danh — module không tự tìm/đoán DOI/PMID
    else:
        ma = MA_OK if kq.thanh_cong else MA_LOI
    d.update(nguon="trich-dan", trang_thai="co_ket_qua" if kq.thanh_cong else "loi", ma_thoat=ma)
    return d


def _in(out: Dict[str, Any]) -> None:
    tt = out.get("trang_thai")
    if out.get("nguon") == "trich-dan":
        print(f"Trích dẫn dự phòng → {tt}")
        for k in ("trich_dan", "doi", "pmid", "nguon_tom_tat"):
            if out.get(k):
                print(f"  {k}: {out[k]}")
        if out.get("tom_tat"):
            print("  TÓM TẮT (của tác giả, không phải toàn văn):", out["tom_tat"])
        print("  Ghi chú:", out.get("ghi_chu") or out.get("ly_do"))
        print(f"  {DISCLAIMER}")
        return
    print(f"Toàn văn guideline [{out['nguon']}] → {tt}")
    if tt == "chua_bat":
        print("  CONNECTOR CHƯA BẬT:", out["ly_do"])
    elif tt in ("tu_choi", "loi"):
        nhan = "TỪ CHỐI: " if tt == "tu_choi" else "KHÔNG TẢI ĐƯỢC (mạng lỗi/bị chặn/nguồn đổi): "
        print("  " + nhan + out["ly_do"])
        if out.get("url_nguon"):
            print("  URL:", out["url_nguon"])
        if out.get("goi_y"):
            print("  ➜", out["goi_y"])
    else:
        print(f"  Tổ chức: {out['to_chuc']} · URL nguồn: {out['url_nguon']}")
        print(f"  Năm/phiên bản (suy từ URL): {out.get('nam_suy_tu_url') or 'không rõ'} / "
              f"{out.get('phien_ban_suy_tu_url') or 'không rõ'}")
        dong = f"  Số ký tự: {out['so_ky_tu']:,}"
        if out.get("so_trang_pdf"):
            dong += f" · số trang PDF: {out['so_trang_pdf']}"
        print(dong + (" · ⚠ ĐÃ BỊ CẮT" if out.get("bi_cat") else " · đầy đủ"))
        print(f"  SHA-256 tệp nguồn: {out.get('sha256_nguon')} · ngày tải (UTC): {out['ngay_tai']}")
        if out.get("ghi_chu"):
            print("  Ghi chú:", out["ghi_chu"])
        for t in out.get("tim", []):
            them = f" (hiện {t['hien_thi']})" if t["so_khop"] > t["hien_thi"] else ""
            print(f"  --tim «{t['cum_tu']}»: {t['so_khop']} lần khớp{them}")
            for d in t["doan"]:
                trang = f" · trang {d['trang']}" if d.get("trang") else ""
                print(f"    · ký tự {d['vi_tri_ky_tu']:,}{trang}: {d['doan']}")
        if out.get("canh_bao_tim"):
            print("  ⚠", out["canh_bao_tim"])
        if out.get("da_luu_noi_bo"):
            print("  Đã lưu văn bản (CHỈ dùng nội bộ):", out["da_luu_noi_bo"])
    print("  Bản quyền:", out.get("ghi_chu_ban_quyen", GHI_CHU_BAN_QUYEN_CHUAN))


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    sub = ap.add_subparsers(dest="nguon", required=True)
    chung = argparse.ArgumentParser(add_help=False)
    chung.add_argument("--tim", action="append", default=[], help="cụm từ cần tìm (lặp được)")
    chung.add_argument("--ngu-canh", type=int, default=300, help="số ký tự ngữ cảnh mỗi bên")
    chung.add_argument("--toi-da-khop", type=int, default=10)
    chung.add_argument("--toan-bo", action="store_true", help="trích toàn bộ tài liệu (không cắt 200.000 ký tự)")
    chung.add_argument("--gioi-han", type=int, default=None, help="cắt ở N ký tự (ghi đè --toan-bo)")
    chung.add_argument("--luu", help="lưu văn bản trích ra tệp NGOÀI repo (chỉ dùng nội bộ)")
    chung.add_argument("--doi", help="DOI của guideline — để gợi ý đường lùi khi tải thất bại")
    chung.add_argument("--pmid", help="PMID của guideline — để gợi ý đường lùi khi tải thất bại")
    chung.add_argument("--json", action="store_true", help="in JSON máy đọc (không kèm toàn văn)")
    for ten, tro_giup in (("gold", "báo cáo GOLD (COPD) mới nhất"), ("gina", "báo cáo GINA (hen) mới nhất")):
        p = sub.add_parser(ten, parents=[chung], help=tro_giup)
        p.add_argument("--url", help=f"URL PDF đã biết trên {DOMAIN_CHO_PHEP[ten][0]} (bỏ trống = tự dò bản mới nhất)")
    p = sub.add_parser("pmc", parents=[chung], help="bài/chương guideline trong PMC Open Access theo PMCID")
    p.add_argument("dinh_danh", metavar="PMCID")
    p = sub.add_parser("bts", parents=[chung], help="hướng dẫn BTS theo URL PDF đã biết")
    p.add_argument("dinh_danh", metavar="URL")
    t = sub.add_parser("trich-dan", help="đường lùi: trích dẫn + tóm tắt theo DOI/PMID (không phải toàn văn)")
    t.add_argument("--doi")
    t.add_argument("--pmid")
    t.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    out = xu_ly_trich_dan(args) if args.nguon == "trich-dan" else xu_ly_tai(args)
    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        _in(out)
    return int(out["ma_thoat"])


if __name__ == "__main__":
    sys.exit(main())
