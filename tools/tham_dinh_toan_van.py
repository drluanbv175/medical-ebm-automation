#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""THẨM ĐỊNH TOÀN VĂN — đối chiếu SỐ LIỆU tường thuật của đề tài với TOÀN VĂN OA (PHA R5-D2).

Vì sao: hệ đã xác minh «PMID có thật + không bị rút» và (tầng dashboard) «hiệu số khớp
TÓM TẮT». Mảnh cuối của chữ "tin cậy" là TOÀN VĂN — nhiều con số chỉ nằm ở thân bài/bảng.

Đơn vị đối chiếu là CÂU TƯỜNG THUẬT có dẫn nguồn kiểu [n] (Vancouver), ánh xạ n→PMID
qua danh mục TLTK của chính tài liệu. Câu dẫn nhiều nguồn: mỗi con số chỉ cần tìm thấy
trong ≥1 bài được dẫn (văn phong tổng hợp gán số cho một trong các nguồn của câu).

⚠️ BẪY ĐÃ GẶP THẬT khi viết bản đầu của công cụ này (15/08/2026, cùng họ BH32
«con số không đo thứ nó tự nhận»): quét theo DÒNG chứa "PMID" thì 19/23 mục "khớp"
hoá ra là dòng DANH MỤC TLTK, và "con số tìm thấy" chính là `10.xxxx` của DOI bài đó —
toàn văn nào chẳng chứa DOI của chính nó. Vì vậy bản này: (a) bóc [n]/DOI/PMID TRƯỚC
khi tách số; (b) bỏ hẳn dòng TLTK khỏi phép đo (metadata TLTK thuộc kiem-chung-trich-dan);
(c) tìm số với BIÊN (không khớp chuỗi con kiểu 85 trong 1985).

Các mức — trung thực theo BH08 (không biết ≠ có vấn đề):
  ✓ KHỚP      — mọi con số của câu tìm thấy trong toàn văn (các) bài được dẫn
  🟠 MỘT PHẦN  — tìm thấy một phần
  ⚪ KHÔNG NÊU — không tìm thấy trong các toàn văn ĐANG CÓ (KHÔNG kết luận «trích sai»)
  🔒 THIẾU OA  — câu có số chưa khớp VÀ ≥1 nguồn của câu không có toàn văn OA → chưa kiểm đủ
So khớp chịu khác biệt dấu thập phân Việt/Anh/Lancet: 78,5 ⇄ 78.5 ⇄ 78·5.

Dùng:  python3 tools/tham_dinh_toan_van.py --study <mã> [--tai-lieu <file.md>]
Mã thoát: 0 = chạy trọn · 1 = thiếu kho toàn văn/tài liệu/danh mục · 2 = tham số sai.
Máy chỉ ĐO và BÁO — không sửa đề cương, không đổi decision. Cần bác sĩ kiểm chứng.
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

HERE = Path(__file__).resolve().parent
EXPORTS = HERE.parent / "exports"
sys.path.insert(0, str(HERE))
from doc_toan_van import _van_ban  # noqa: E402  (tái dùng, không chép đôi)

RE_TLTK = re.compile(r"^\s*(\d{1,3})\.\s+\S")          # «12. Tác giả…»
RE_PMID_TRONG_DONG = re.compile(r"PMID[: ]*(\d{7,9})")
RE_MARKER = re.compile(r"\[(\d{1,3}(?:\s*,\s*\d{1,3})*)\]")   # [2] · [9,10]
# Số đáng đối chiếu — SAU khi đã bóc marker/DOI/PMID: thập phân · phần trăm · n=
RE_SO = re.compile(r"\d+[.,·]\d+\s*%?|\d+\s*%|[nN]\s*=\s*\d[\d.,]*")


def _lam_sach_cau(cau: str) -> str:
    """Bỏ những chuỗi mang chữ số nhưng KHÔNG phải số liệu: marker [n], DOI, PMID,
    và THAM CHIẾU CHÉO NỘI BỘ («mục 4.10», «Bảng 4.5») — bẫy đo thật 15/08: các
    tham chiếu này bị bắt như số thập phân rồi báo ⚪ oan cho bài được dẫn."""
    cau = RE_MARKER.sub(" ", cau)
    cau = re.sub(r"doi:\s*\S+|\b10\.\d{4,9}/\S+", " ", cau, flags=re.I)
    cau = re.sub(r"PMID[: ]*\d+", " ", cau)
    cau = re.sub(r"\b(?:mục|bảng|hình|phần|chương|section|table|figure|fig\.?)\s*\d+(?:\.\d+)*",
                 " ", cau, flags=re.I)
    return cau


def _chuan_so(s: str) -> str:
    s = s.replace(" ", "").replace(" ", "").replace("·", ".").replace(",", ".")
    return s.lstrip("nN=")


def _tim_co_bien(so_chuan: str, ft: str) -> bool:
    """Tìm con số với BIÊN số hai phía — «85%» không được khớp «1985», «0.78»
    không được khớp chuỗi con của «0.786».

    Hai co giãn CÓ CHỦ ĐÍCH (đo thật 15/08 trên chính bài Polit & Beck 17654487):
    (a) văn phong APA bỏ số 0 dẫn đầu — bài viết «.78» trong khi đề cương viết
        «0,78»; (b) số 0 đuôi — «0,90» của đề cương ⇄ «0.9» trong bài."""
    la_phan_tram = so_chuan.endswith("%")
    goc = so_chuan.rstrip("%")
    dang = {goc}
    if "." in goc:
        rut = goc.rstrip("0").rstrip(".")
        if rut and rut != ".":
            dang.add(rut)
    for d in dang:
        if la_phan_tram:
            mau = rf"(?<![\d.]){re.escape(d)}(?:\.0+)?\s*%"
        elif d.startswith("0."):
            # 0 dẫn đầu TUỲ CHỌN: khớp cả «0.78» lẫn «.78» (APA)
            mau = rf"(?<![\d.])0?{re.escape(d[1:])}(?![\d.])"
        else:
            mau = rf"(?<![\d.]){re.escape(d)}(?![\d.])"
        if re.search(mau, ft):
            return True
    return False


def _tach_cau(doan: str) -> list[str]:
    """Tách đoạn thành câu, giữ marker [n] đi liền câu của nó."""
    return [c.strip() for c in re.split(r"(?<=[.!?])\s+(?=[A-ZĐÀ-Ỹ*\-•(])", doan) if c.strip()]


def main() -> int:
    ap = argparse.ArgumentParser(description="Đối chiếu số liệu tường thuật với toàn văn OA")
    ap.add_argument("--study", required=True)
    ap.add_argument("--tai-lieu", help="file .md cần thẩm định (mặc định: De-cuong_*.md)")
    a = ap.parse_args()
    sdir = EXPORTS / a.study
    kho = sdir / "toan_van_oa"
    if a.tai_lieu:
        doc = Path(a.tai_lieu)
    else:
        cands = sorted(sdir.glob("De-cuong_*.md")) or sorted(sdir.glob("G1_A2_PROTOCOL_*.md"))
        if not cands:
            print("🔴 Không thấy đề cương (De-cuong_*.md) — chỉ định bằng --tai-lieu.")
            return 1
        doc = cands[0]
    if not doc.exists():
        print(f"🔴 Không đọc được {doc}")
        return 1
    xmls = {re.search(r"PMID-(\d+)_", f.name).group(1): f
            for f in kho.glob("PMID-*.xml")} if kho.exists() else {}
    if not xmls:
        print(f"🔴 Chưa có kho toàn văn cho {a.study} — chạy gom_toan_van_oa trước.")
        return 1

    text = doc.read_text(encoding="utf-8", errors="replace")

    # 1) Danh mục TLTK: n → PMID (chỉ dòng dạng «n. …» có PMID)
    ref_map: dict[str, str] = {}
    for line in text.splitlines():
        m = RE_TLTK.match(line)
        pm = RE_PMID_TRONG_DONG.search(line)
        if m and pm:
            ref_map.setdefault(m.group(1), pm.group(1))
    if not ref_map:
        print("🔴 Không dựng được ánh xạ [n]→PMID từ danh mục TLTK — kiểm định dạng tài liệu.")
        return 1

    cache: dict[str, str] = {}

    def _ft(pm: str) -> str | None:
        if pm not in xmls:
            return None
        if pm not in cache:
            vb = _van_ban(xmls[pm])
            cache[pm] = re.sub(r"(\d)[·,](\d)", r"\1.\2", vb)
        # XML hỏng → _van_ban trả "" — phải coi là KHÔNG CÓ toàn văn (🔒 chưa kiểm),
        # tuyệt đối không để rơi vào «có toàn văn nhưng không nêu» (⚪ oan, cùng họ
        # lỗi return-sớm 12/08: luật sau chạy trên dữ liệu rỗng mà vẫn ra kết luận).
        return cache[pm] or None

    # 2) Câu tường thuật có [n] (bỏ dòng TLTK)
    ket = {"khop": 0, "motphan": 0, "khongneu": 0, "thieuoa": 0, "dinhtinh": 0}
    dong_bc: list[str] = []
    for line in text.splitlines():
        if RE_TLTK.match(line) and RE_PMID_TRONG_DONG.search(line):
            continue
        for cau in _tach_cau(line):
            markers = RE_MARKER.findall(cau)
            if not markers:
                continue
            ns = sorted({n.strip() for grp in markers for n in grp.split(",")})
            pmids = [(n, ref_map.get(n)) for n in ns]
            so = [m.group(0).strip() for m in RE_SO.finditer(_lam_sach_cau(cau))]
            trich = (cau[:130] + "…") if len(cau) > 130 else cau
            nguon = ", ".join(f"[{n}]→{p or '?'}" for n, p in pmids)
            if not so:
                ket["dinhtinh"] += 1
                continue  # câu định tính không vào bảng — giữ báo cáo gọn, đếm ở tổng
            fts = {p: _ft(p) for _, p in pmids if p}
            thieu_oa = [n for n, p in pmids if not p or fts.get(p) is None]
            thay, chua = [], []
            for s in so:
                sc = _chuan_so(s)
                if any(ft and _tim_co_bien(sc, ft) for ft in fts.values()):
                    thay.append(s)
                else:
                    chua.append(s)
            if not chua:
                ket["khop"] += 1
                dong_bc.append(f"| ✓ | {nguon} | {trich} | {len(so)}/{len(so)} số có trong toàn văn |")
            elif thieu_oa:
                ket["thieuoa"] += 1
                dong_bc.append(f"| 🔒 | {nguon} | {trich} | chưa thấy {', '.join(chua[:4])} nhưng "
                               f"nguồn [{']['.join(thieu_oa)}] không có toàn văn OA → chưa kiểm đủ |")
            elif thay:
                ket["motphan"] += 1
                dong_bc.append(f"| 🟠 | {nguon} | {trich} | thấy {len(thay)}/{len(so)}; "
                               f"chưa thấy: {', '.join(chua[:4])} |")
            else:
                ket["khongneu"] += 1
                dong_bc.append(f"| ⚪ | {nguon} | {trich} | toàn văn không nêu: {', '.join(chua[:4])} "
                               "— KHÔNG kết luận trích sai |")

    out = sdir / f"THAM-DINH-TOAN-VAN_{date.today().isoformat()}.md"
    n_so = ket["khop"] + ket["motphan"] + ket["khongneu"] + ket["thieuoa"]
    header = [
        f"# THẨM ĐỊNH TOÀN VĂN — {a.study} — {date.today().isoformat()}",
        "",
        f"Tài liệu: `{doc.name}` · Kho toàn văn OA: {len(xmls)} bài · "
        f"Ánh xạ TLTK: {len(ref_map)} mục [n]→PMID",
        "",
        f"Câu tường thuật có dẫn nguồn: **{n_so + ket['dinhtinh']}** — trong đó "
        f"**{n_so} câu mang con số** được đối chiếu · {ket['dinhtinh']} câu định tính (không có số, không liệt kê)",
        "",
        f"- ✓ khớp đủ: **{ket['khop']}** · 🟠 một phần: **{ket['motphan']}** · "
        f"⚪ không nêu: **{ket['khongneu']}** · 🔒 chưa kiểm đủ (thiếu OA): **{ket['thieuoa']}**",
        "",
        "> ⚪ nghĩa là *chưa xác minh được qua toàn văn đang có*, KHÔNG phải *trích sai* —",
        "> số có thể do đề cương tự tính/làm tròn/gộp, hoặc nằm trong bảng/hình mà XML không mang.",
        "> Phân xử từng mục ⚪/🟠 là việc của bác sĩ (mở link PMC đọc bản trình bày).",
        "> Dòng danh mục TLTK KHÔNG nằm trong phép đo này — metadata TLTK do kiem-chung-trich-dan lo.",
        "",
        "| Mức | Nguồn của câu | Câu trích | Ghi chú |",
        "|---|---|---|---|",
    ]
    out.write_text("\n".join(header + dong_bc +
                             ["", "> Máy chỉ ĐO và BÁO. Cần bác sĩ kiểm chứng."]) + "\n",
                   encoding="utf-8")
    print(f"THẨM ĐỊNH TOÀN VĂN: {n_so} câu mang số — ✓ {ket['khop']} · 🟠 {ket['motphan']} · "
          f"⚪ {ket['khongneu']} · 🔒 {ket['thieuoa']} (+{ket['dinhtinh']} câu định tính)")
    print(f"  → {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
