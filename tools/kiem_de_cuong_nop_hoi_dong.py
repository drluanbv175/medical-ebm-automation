#!/usr/bin/env python3
"""Kiểm bản ĐỀ CƯƠNG NỘP HỘI ĐỒNG `exports/<mã>/DE_CUONG_NOP_HOI_DONG_<mã>.md` + `.docx` (nhiệm vụ G10-T4, 15/10/2026).

Vì sao có: bác sĩ chê bản lắp máy `DE_CUONG_THONG_NHAT_<mã>` (ký hiệu hệ thống, tên biến, bảng cổng) «khó mà chấp
nhận được» để nộp Hội đồng; đề cương nộp được viết lại bằng văn phong khoa học. Viết tay thì dễ trôi khỏi quyết định đã
chốt hoặc sót ký hiệu nội bộ — công cụ này là lớp kiểm MÁY cho đầu ra đó (chất lượng văn phong, độ đúng nguồn vẫn do
`tham-dinh-dau-ra` + `kiem-chung-trich-dan` chấm chéo).

Luật (mỗi lỗi một dòng; rỗng = đạt):
  K1  có đủ cặp `.md` + `.docx`;
  K2  bản Word sinh từ CHÍNH bản `.md`: mọi đề mục cấp 1 của `.md` có trong chữ hiển thị của `.docx`, cùng tập PMID;
  K3  đủ chương mục của đề cương (đặt vấn đề · mục tiêu · tổng quan · đối tượng và phương pháp · đạo đức · dự kiến kết
      quả · kế hoạch · tài liệu tham khảo · phụ lục bản thông tin/phiếu đồng ý · phụ lục công cụ thu thập);
  K4  không ký hiệu nội bộ của hệ thống (cổng G0/G4–G10, «SAP §», «§», nhãn [CẦN…], checkpoint, study_meta, pipeline,
      agent, dry-run, forced-in…); tên biến dạng `ten_bien` chỉ được ở bảng hoặc ở phụ lục;
  K5  cỡ mẫu khớp G3 (`confirmed_n` của G3_checkpoint.json có mặt trong văn bản);
  K6  mọi PMID nằm trong biên nhận rút bài A12 (`A12_RETRACTION_RECEIPT.json`) đã kiểm và sạch;
  K7  không email/số điện thoại (bỏ DOI/URL trước khi dò), không nhãn ô trống [CẦN…] (dòng chấm «………» để PI điền tay
      là hợp lệ).

Lệnh:  python3 tools/kiem_de_cuong_nop_hoi_dong.py --study <mã> [--json]
Mã thoát: 0 đạt · 1 có lỗi · 2 thiếu tệp đề cương nộp.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional

for _luong in (sys.stdout, sys.stderr):
    try:
        _luong.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

BASE = Path(__file__).resolve().parents[1]
if str(BASE / "tools") not in sys.path:
    sys.path.insert(0, str(BASE / "tools"))

import g10_quality_gate as G10  # noqa: E402

TEN = "DE_CUONG_NOP_HOI_DONG_{study}"
# (nhãn hiển thị, các từ khoá — một đề mục bất kỳ chứa MỘT từ khoá là đạt; so không phân biệt hoa thường)
CHUONG_BAT_BUOC = (
    ("đặt vấn đề", ("ĐẶT VẤN ĐỀ",)),
    ("mục tiêu nghiên cứu", ("MỤC TIÊU",)),
    ("tổng quan tài liệu", ("TỔNG QUAN",)),
    ("đối tượng và phương pháp", ("ĐỐI TƯỢNG VÀ PHƯƠNG PHÁP",)),
    ("đạo đức nghiên cứu", ("ĐẠO ĐỨC",)),
    ("dự kiến kết quả", ("DỰ KIẾN KẾT QUẢ",)),
    ("kế hoạch thực hiện", ("KẾ HOẠCH THỰC HIỆN", "TIẾN ĐỘ")),
    ("tài liệu tham khảo", ("TÀI LIỆU THAM KHẢO",)),
    ("phụ lục bản thông tin/phiếu đồng ý", ("ĐỒNG Ý THAM GIA", "ĐỒNG THUẬN")),
    ("phụ lục công cụ thu thập", ("PHIẾU KHẢO SÁT", "PHIẾU THU THẬP", "BỘ CÂU HỎI", "BỆNH ÁN NGHIÊN CỨU")),
)
# Ký hiệu nội bộ của hệ thống không được lọt vào văn bản nộp. Không bắt «G1–G3» vì có thể là mã câu hỏi của phiếu.
_KY_HIEU_NOI_BO = (
    (re.compile(r"\bcổng\s+G\d", re.IGNORECASE), "«cổng G…»"),
    (re.compile(r"\bG(?:0|[4-9]|10)\b"), "mã cổng G0/G4–G10"),
    (re.compile(r"\bSAP\b"), "«SAP»"),
    (re.compile(r"§"), "ký hiệu «§»"),
    (re.compile(r"\[CẦN", re.IGNORECASE), "nhãn [CẦN…]"),
    (re.compile(r"\b(?:checkpoint|study_meta|pipeline|StudySpec|dry-run|forced-in|complete-case)\b",
                re.IGNORECASE), "thuật ngữ nội bộ hệ thống"),
    (re.compile(r"\bagent\b", re.IGNORECASE), "«agent»"),
)
_TEN_BIEN_RE = re.compile(r"(?<![\w./-])[a-z][a-z0-9]*_[a-z0-9_]+\b")
_DE_MUC_RE = re.compile(r"^(#{1,4})\s+(.*\S)\s*$", re.MULTILINE)


def _doc(p: Path) -> Optional[str]:
    try:
        return p.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _chu_docx(p: Path) -> Optional[str]:
    try:
        with zipfile.ZipFile(p) as archive:
            xml = archive.read("word/document.xml").decode("utf-8", errors="strict")
            return G10._docx_visible_text(archive, xml)
    except (OSError, KeyError, UnicodeDecodeError, zipfile.BadZipFile):
        return None


def _chuan(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[*_`]", "", s)).strip().upper()


def _pmid(text: str) -> set:
    return set(re.findall(r"PMID:?\s*(\d{5,9})", text))


def _dinh_dang_n(n: int) -> tuple:
    return (str(n), f"{n:,}".replace(",", "."), f"{n:,}")


def kiem(out_dir: Path, study: str) -> List[str]:
    """Danh sách lỗi của bản đề cương nộp Hội đồng (rỗng = đạt). Thiếu tệp `.md` ⇒ một lỗi K1."""
    out_dir = Path(out_dir)
    md_p = out_dir / (TEN.format(study=study) + ".md")
    docx_p = out_dir / (TEN.format(study=study) + ".docx")
    loi: List[str] = []
    if not md_p.is_file():
        return [f"K1 chưa có {md_p.name}"]
    md = _doc(md_p)
    if md is None:
        return [f"K1 không đọc được {md_p.name}"]
    docx_chu = _chu_docx(docx_p) if docx_p.is_file() else None
    if docx_chu is None:
        loi.append(f"K1 thiếu hoặc hỏng {docx_p.name} (xuất bằng tools/md_sang_docx_times.py --trang-de-cuong)")

    de_muc = [(len(m.group(1)), m.group(2)) for m in _DE_MUC_RE.finditer(md)]
    if docx_chu is not None:
        chu = _chuan(docx_chu)
        thieu = [dm for cap, dm in de_muc if cap == 1 and _chuan(dm) not in chu]
        if thieu:
            loi.append(f"K2 bản Word không khớp bản .md — thiếu đề mục: {'; '.join(thieu[:3])} (xuất lại Word)")
        if _pmid(md) != _pmid(docx_chu):
            loi.append("K2 bản Word không khớp bản .md — tập PMID khác nhau (xuất lại Word)")

    tat_ca_de_muc = " | ".join(_chuan(dm) for _, dm in de_muc)
    for nhan, tu in CHUONG_BAT_BUOC:
        if not any(t in tat_ca_de_muc for t in tu):
            loi.append(f"K3 thiếu chương/mục «{nhan}»")

    chuong = ""
    for so, dong in enumerate(md.splitlines(), 1):
        m = _DE_MUC_RE.match(dong)
        if m and len(m.group(1)) == 1:
            chuong = _chuan(m.group(2))
        sach = G10._DOI_URL_RE.sub(" ", dong)
        for bt, nhan in _KY_HIEU_NOI_BO:
            if bt.search(sach):
                loi.append(f"K4 dòng {so}: {nhan}")
                break
        if not chuong.startswith("PHỤ LỤC") and not dong.lstrip().startswith("|"):
            ten = _TEN_BIEN_RE.findall(sach)
            if ten:
                loi.append(f"K4 dòng {so}: tên biến trong văn xuôi ({', '.join(ten[:2])}) — dồn về bảng/phụ lục")

    try:
        g3 = json.loads((out_dir / "G3_checkpoint.json").read_text(encoding="utf-8"))
        n = g3.get("confirmed_n") if g3.get("confirmed_n") not in (None, "") else g3.get("n_adjusted")
        n = int(n)
    except (OSError, ValueError, TypeError, AttributeError):
        n = None
    if n is None:
        loi.append("K5 không đọc được cỡ mẫu đã chốt từ G3_checkpoint.json — không đối chiếu được")
    elif not any(re.search(rf"(?<![\d.,]){re.escape(s)}(?![\d])", md) for s in _dinh_dang_n(n)):
        loi.append(f"K5 cỡ mẫu đã chốt ở G3 ({n}) không xuất hiện trong đề cương nộp")
    # F2 (16/10/2026, diễn tập C1a): đề cương nộp dùng DE 1,78 / N tối thiểu 808 (có hệ số biến thiên cỡ cụm) trong khi
    # G3 ghi DE 1,38 / 626 — K5 cũ chỉ so N chốt nên không thấy. Nay DE và N tối thiểu của G3 cũng phải có mặt.
    if n is not None:
        de = g3.get("design_effect") if isinstance(g3, dict) else None
        n_min = g3.get("n_adjusted") if isinstance(g3, dict) else None
        if isinstance(de, (int, float)) and float(de) > 1:
            dang = {f"{float(de):.2f}", f"{float(de):.2f}".replace(".", ",")}
            if not any(re.search(rf"(?<![\d.,]){re.escape(x)}(?![\d])", md) for x in dang):
                loi.append(f"K5 hiệu ứng thiết kế G3 (DE {float(de):.2f}) không xuất hiện trong đề cương nộp — "
                           "đề cương dùng con số khác G3? Đồng bộ hai bên (chạy lại G3 hoặc sửa đề cương)")
        if isinstance(n_min, (int, float)) and int(n_min) != n:
            if not any(re.search(rf"(?<![\d.,]){re.escape(x)}(?![\d])", md) for x in _dinh_dang_n(int(n_min))):
                loi.append(f"K5 cỡ mẫu tối thiểu G3 ({int(n_min)}) không xuất hiện trong đề cương nộp")

    pm = _pmid(md)
    if pm:
        try:
            rc = json.loads((out_dir / "A12_RETRACTION_RECEIPT.json").read_text(encoding="utf-8"))
            da_kiem = {str(x) for x in rc.get("pmids_checked") or []}
            sach_rc = rc.get("all_clean") is True
        except (OSError, ValueError, AttributeError):
            da_kiem, sach_rc = set(), False
        chua = sorted(pm - da_kiem)
        if chua:
            loi.append(f"K6 {len(chua)} PMID chưa có trong biên nhận A12: {', '.join(chua[:6])} — chạy "
                       "check_citations.py --study với hợp PMID của bản lắp và bản nộp")
        elif not sach_rc:
            loi.append("K6 biên nhận A12 chưa ghi all_clean=true")

    for so, dong in enumerate(md.splitlines(), 1):
        if G10._PLACEHOLDER_RE.search(dong):
            loi.append(f"K7 dòng {so}: nhãn ô trống [CẦN…]/<…>")
    if G10._co_lien_lac_ca_nhan(md) or (docx_chu is not None and G10._co_lien_lac_ca_nhan(docx_chu)):
        loi.append("K7 có email/số điện thoại — PII liên lạc để dòng chấm cho PI điền tay ngoài hệ thống")
    return loi


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Kiểm bản đề cương nộp Hội đồng (G10-T4).")
    ap.add_argument("--study", required=True)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    out_dir = BASE / "exports" / a.study
    loi = kiem(out_dir, a.study)
    ket: Dict[str, Any] = {"study": a.study, "dat": not loi, "loi": loi}
    if a.json:
        print(json.dumps(ket, ensure_ascii=False, indent=2))
    else:
        print(f"Đề cương nộp Hội đồng — {a.study}: {'ĐẠT' if not loi else f'{len(loi)} lỗi'}")
        for d in loi:
            print(f"  ✗ {d}")
        print("Cần bác sĩ kiểm chứng.")
    if loi and loi[0].startswith("K1 chưa có"):
        return 2
    return 0 if not loi else 1


if __name__ == "__main__":
    raise SystemExit(main())
