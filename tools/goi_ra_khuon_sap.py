#!/usr/bin/env python3
"""goi_ra_khuon_sap.py — GÓI RÀ KHUÔN SAP cho thống kê viên: mỗi thiết kế một trang rà (23/11/2026).

VÌ SAO (bác sĩ duyệt 23/11/2026): khuôn kế hoạch phân tích thống kê (SAP) do `tools/run_g4_auto.py` sinh cho 8 thiết kế
và các biến thể (cụm, không kém hơn, ghép cặp) chưa từng được một thống kê viên rà theo từng thiết kế. Gói này đặt
trước thống kê viên đúng những gì khuôn sẽ viết vào SAP của một đề tài thật, lấy NGUYÊN VĂN từ SAP đã điền của kịch bản
giả lập (chạy công cụ thật của hệ trên đề tài mô phỏng), để thống kê viên đánh dấu «đồng ý / sửa» cho từng hạng mục.

MỖI TRANG (một thiết kế/biến thể):
  • Nguồn ví dụ: kịch bản giả lập, tệp SAP và mã băm SHA-256 (đối chiếu được bản đã rà).
  • Bảng rà 6 hạng mục — nội dung chép nguyên văn từ Phần 3 của SAP ví dụ, không viết câu mới:
      Họ mô hình chính (§4) · Khoảng tin cậy (dòng có «KTC/khoảng tin cậy/95%CI», trừ hàng bảng giả) · Dữ liệu thiếu
      (§6, đúng tiêu đề của thiết kế) · Biến cố hiếm (dòng «biến cố hiếm/Firth/EPV/Clopper…») · Phân tích độ nhạy (§9)
      · Căn cứ PMID (mỗi PMID một dòng kèm câu chứa nó). Hạng mục khuôn không có ⇒ ghi «khuôn SAP của thiết kế này không
      có dòng nào cho hạng mục này» — chính điều đó cũng là nội dung cần rà.
  • Cột thống kê viên: ô «☐ Đồng ý / ☐ Sửa» và dòng chấm để ghi nội dung sửa — để TRỐNG, máy không ghi nhận xét thay.
  • Ví dụ SAP đã điền: toàn văn Phần 3 của SAP ví dụ.
  • Khối ký của thống kê viên (họ tên, chữ ký, ngày — dòng chấm).
Kèm `HUONG_DAN_RA_KHUON_SAP` (.md/.docx) và `MUC_LUC.json` (nguồn, mã băm, tệp ra, hạng mục trống).

NGUỒN: thư mục giả lập trọn vòng dừng ở G4 (`GIA_LAP_TRON_VONG_DIR`), mỗi kịch bản một thư mục
`<mã kịch bản>/repo/exports/<đề tài>/G4_A5_SAP_FINAL_<đề tài>.md`. Lệnh sinh nguồn: `--lenh-sinh-nguon <thư mục>`.

RANH GIỚI: chỉ đọc nguồn; thư mục gói phải NGOÀI repo (gói rà là tài liệu làm việc, không vào git). Không ghi đánh giá,
không đánh dấu ô, không sửa khuôn SAP — nhận xét của thống kê viên được đưa về NGUỒN khuôn (`run_g4_auto.py`,
`g4_quality_gate.py`), giả lập lại, rồi phát hành gói rà mới.

Dùng:
    python3 tools/goi_ra_khuon_sap.py --nguon <thư mục giả lập> --ra <thư mục gói ngoài repo> [--khong-pdf] [--json]
    python3 tools/goi_ra_khuon_sap.py --lenh-sinh-nguon <thư mục giả lập>
Mã thoát: 0 đủ mọi trang · 1 thiếu SAP nguồn của ít nhất một thiết kế (các trang có nguồn vẫn dựng, trang thiếu được
liệt kê) · 3 tham số sai (thư mục gói trong repo, không có nguồn). Cần bác sĩ kiểm chứng.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

for _luong in (sys.stdout, sys.stderr):  # Windows cp1252 làm hỏng print() tiếng Việt — ép UTF-8
    try:
        _luong.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

BASE = Path(__file__).resolve().parents[1]
SCHEMA = "goi_ra_khuon_sap/v1"
CAN_KIEM = "Cần bác sĩ kiểm chứng."

#: (mã trang, mã kịch bản giả lập, mã thiết kế, nhãn) — 8 thiết kế + 3 biến thể, đúng thứ tự trong gói.
DANH_MUC: Tuple[Tuple[str, str, str, str], ...] = (
    ("rct", "rct_nhi_phan", "rct", "Thử nghiệm ngẫu nhiên có đối chứng — kiểm định ưu thế"),
    ("rct_khong_kem", "rct_khong_kem", "rct", "Thử nghiệm ngẫu nhiên có đối chứng — không kém hơn"),
    ("rct_cum", "rct_cum", "rct", "Thử nghiệm ngẫu nhiên theo cụm"),
    ("cohort", "thuan_tap_phoi_nhiem", "cohort", "Nghiên cứu thuần tập"),
    ("case_control", "benh_chung", "case_control", "Nghiên cứu bệnh–chứng (ghép theo tần suất)"),
    ("case_control_ghep_cap", "benh_chung_ghep_cap", "case_control", "Nghiên cứu bệnh–chứng ghép cặp cá thể"),
    ("cross_sectional", "cat_ngang_mo_ta", "cross_sectional", "Nghiên cứu cắt ngang"),
    ("diagnostic", "chan_doan", "diagnostic", "Nghiên cứu độ chính xác chẩn đoán"),
    ("prediction", "mo_hinh_du_bao", "prediction", "Mô hình dự báo lâm sàng"),
    ("sr_ma", "tong_quan_gop", "sr_ma", "Tổng quan hệ thống và phân tích gộp"),
    ("qualitative", "dinh_tinh", "qualitative", "Nghiên cứu định tính"),
)
HANG_MUC: Tuple[Tuple[str, str], ...] = (
    ("mo_hinh", "Họ mô hình chính"),
    ("ktc", "Khoảng tin cậy"),
    ("thieu", "Dữ liệu thiếu"),
    ("hiem", "Biến cố hiếm"),
    ("do_nhay", "Phân tích độ nhạy"),
    ("pmid", "Căn cứ PMID"),
)
KHONG_CO = "Khuôn SAP của thiết kế này không có dòng nào cho hạng mục này."
O_THONG_KE_VIEN = ["☐ Đồng ý", "☐ Sửa — nội dung sửa:", "……………………………………", "……………………………………"]
_KTC = re.compile(r"\bKTC\b|khoảng tin cậy|\d+\s?%\s?CI\b", re.IGNORECASE)
_HIEM = re.compile(r"biến cố hiếm|ít biến cố|\bFirth\b|\bEPV\b|Clopper|sự kiện hiếm", re.IGNORECASE)
_PMID = re.compile(r"PMID[:\s]*(\d{6,9})")
_MUC = re.compile(r"^### §(\d+)\s*(.*)$")


def _sha256(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _gon(dong: str) -> str:
    """Bỏ dấu nhấn mạnh markdown và khoảng trắng thừa — chữ giữ nguyên."""
    return re.sub(r"\s+", " ", dong.replace("**", "").replace("`", "")).strip().strip("-").strip()


def phan_3(sap: str) -> str:
    """Phần 3 (các mục §) của SAP — từ «## PHẦN 3» tới «## PHẦN» kế tiếp."""
    m = re.search(r"^## PHẦN 3\b.*?$(.*?)(?=^## PHẦN \d|\Z)", sap, flags=re.M | re.S)
    return m.group(1).strip("\n") if m else ""


def tach_muc(p3: str) -> Dict[int, Tuple[str, List[str]]]:
    """{số §: (tiêu đề, các dòng thân)}."""
    ra: Dict[int, Tuple[str, List[str]]] = {}
    hien: Optional[int] = None
    for dong in p3.splitlines():
        m = _MUC.match(dong.strip())
        if m:
            hien = int(m.group(1))
            ra[hien] = (m.group(2).strip(), [])
            continue
        if hien is not None and dong.strip():
            ra[hien][1].append(dong.rstrip())
    return ra


def _dong_van(dong_ds: List[str]) -> List[str]:
    """Dòng văn (không phải hàng bảng giả, không phải dòng kẻ) đã làm gọn."""
    return [_gon(d) for d in dong_ds if d.strip() and not d.lstrip().startswith("|") and _gon(d)]


def trich_hang_muc(sap: str) -> Dict[str, List[str]]:
    """Sáu hạng mục rà, mỗi hạng mục là danh sách câu NGUYÊN VĂN của SAP (đã bỏ dấu markdown)."""
    muc = tach_muc(phan_3(sap))

    def than(so: int) -> List[str]:
        if so not in muc:
            return []
        tieu_de, dong = muc[so]
        return [f"§{so} {tieu_de}"] + _dong_van(dong)

    tat_ca: List[str] = []
    for so in sorted(muc):
        if so == 11:  # §11 khung bảng giả — hàng bảng không phải phương pháp
            continue
        tat_ca += _dong_van(muc[so][1])
    pmid: Dict[str, str] = {}
    for so in sorted(muc):
        for d in _dong_van(muc[so][1]):
            for x in _PMID.findall(d):
                pmid.setdefault(x, f"PMID {x} — §{so}: {d}")
    return {
        "mo_hinh": than(4),
        "ktc": list(dict.fromkeys(d for d in tat_ca if _KTC.search(d))),
        "thieu": than(6),
        "hiem": list(dict.fromkeys(d for d in tat_ca if _HIEM.search(d))),
        "do_nhay": than(9),
        "pmid": list(pmid.values()),
    }


def tim_sap(nguon: Path, ma_kich_ban: str) -> Optional[Path]:
    ds = sorted(p for p in (Path(nguon) / ma_kich_ban / "repo" / "exports").glob("*/G4_A5_SAP_FINAL_*.md")
                if p.is_file())
    return ds[0] if len(ds) == 1 else None


# ───────────────────────────────────────────────────────────────────────────── Word / HTML / PDF
def _docx_trang(trang: Dict[str, Any], hang: Dict[str, List[str]], p3: str, ra: Path) -> None:
    import docx  # noqa: PLC0415
    from docx.shared import Pt  # noqa: PLC0415

    tl = docx.Document()
    st = tl.styles["Normal"]
    st.font.name = "Times New Roman"
    st.font.size = Pt(12)
    tl.add_heading(f"Rà khuôn SAP — {trang['nhan']}", level=1)
    tl.add_paragraph(f"Mã thiết kế: {trang['thiet_ke']} · trang {trang['thu_tu']}/{trang['tong']}")
    tl.add_paragraph(f"Ví dụ: SAP đã điền của kịch bản giả lập «{trang['kich_ban']}» (dữ liệu mô phỏng), tệp "
                     f"{trang['tep_nguon']}, SHA-256 {trang['sha256']}. Nội dung khuôn do tools/run_g4_auto.py sinh.")
    bang = tl.add_table(rows=1, cols=3)
    bang.style = "Table Grid"
    for o, t in zip(bang.rows[0].cells, ("Hạng mục", "Khuôn SAP (nguyên văn từ ví dụ)", "Thống kê viên")):
        o.text = t
    for khoa, nhan in HANG_MUC:
        h = bang.add_row().cells
        h[0].text = nhan
        h[1].text = "\n".join(hang.get(khoa) or [KHONG_CO])
        h[2].text = "\n".join(O_THONG_KE_VIEN)
    tl.add_heading("Ví dụ SAP đã điền — Phần 3 nguyên văn", level=2)
    for d in p3.splitlines():
        if d.strip():
            tl.add_paragraph(_gon(d) if not d.lstrip().startswith("|") else d.strip())
    tl.add_heading("Thống kê viên rà", level=2)
    for nhan in ("Họ và tên", "Chữ ký", "Ngày"):
        tl.add_paragraph(f"{nhan}: ……………………………………")
    tl.save(str(ra))


def _html_trang(trang: Dict[str, Any], hang: Dict[str, List[str]], p3: str) -> str:
    e = html.escape
    hang_html = "".join(
        f"<tr><td>{e(nhan)}</td><td>{'<br>'.join(e(x) for x in (hang.get(k) or [KHONG_CO]))}</td>"
        f"<td>{'<br>'.join(e(x) for x in O_THONG_KE_VIEN)}</td></tr>" for k, nhan in HANG_MUC)
    vd = "".join(f"<p>{e(_gon(d))}</p>" for d in p3.splitlines() if d.strip())
    return ("<!doctype html><html lang='vi'><meta charset='utf-8'><style>body{font-family:'Times New Roman',serif;"
            "font-size:12pt;margin:2cm}table{border-collapse:collapse;width:100%}td,th{border:1px solid #000;"
            "padding:4px;vertical-align:top}</style>"
            f"<h1>Rà khuôn SAP — {e(trang['nhan'])}</h1><p>Mã thiết kế: {e(trang['thiet_ke'])} · trang "
            f"{trang['thu_tu']}/{trang['tong']}</p><p>Ví dụ: SAP đã điền của kịch bản giả lập «{e(trang['kich_ban'])}» "
            f"(dữ liệu mô phỏng), tệp {e(trang['tep_nguon'])}, SHA-256 {e(trang['sha256'])}.</p>"
            "<table><tr><th>Hạng mục</th><th>Khuôn SAP (nguyên văn từ ví dụ)</th><th>Thống kê viên</th></tr>"
            f"{hang_html}</table><h2>Ví dụ SAP đã điền — Phần 3 nguyên văn</h2>{vd}<h2>Thống kê viên rà</h2>"
            "<p>Họ và tên: ……………………………………</p><p>Chữ ký: ……………………………………</p><p>Ngày: ……………………………………</p></html>")


_TRINH_DUYET = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
)


def tim_trinh_duyet() -> Optional[str]:
    for p in _TRINH_DUYET:
        if Path(p).is_file():
            return p
    for ten in ("google-chrome", "chromium", "chromium-browser", "microsoft-edge"):
        w = shutil.which(ten)
        if w:
            return w
    return None


def in_pdf(html_van: str, ra: Path) -> bool:
    """HTML → PDF bằng Chrome/Edge headless (máy Mac không có LibreOffice/Word tự động).

    Không có trình duyệt ⇒ False (gói vẫn có Word)."""
    tr = tim_trinh_duyet()
    if not tr:
        return False
    with tempfile.TemporaryDirectory() as td:
        h = Path(td) / "trang.html"
        h.write_text(html_van, encoding="utf-8", newline="\n")
        try:
            subprocess.run([tr, "--headless", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={ra}",
                            h.as_uri()], capture_output=True, timeout=120, check=False)
        except (OSError, subprocess.SubprocessError):
            return False
    return ra.is_file() and ra.stat().st_size > 0


def huong_dan_md(muc_luc: Dict[str, Any]) -> str:
    d = ["# Hướng dẫn rà khuôn kế hoạch phân tích thống kê (SAP) theo thiết kế", "",
         f"Gói dựng lúc {muc_luc['ngay_dung']} bằng `tools/goi_ra_khuon_sap.py`.", "",
         "## Mục đích", "",
         "Mỗi trang đặt trước thống kê viên đúng những gì khuôn SAP của hệ sẽ viết cho một đề tài thật theo thiết kế "
         "đó: họ mô hình chính, khoảng tin cậy, dữ liệu thiếu, biến cố hiếm, phân tích độ nhạy và căn cứ PMID. Nội "
         "dung "
         "chép nguyên văn từ SAP đã điền của kịch bản giả lập (dữ liệu mô phỏng) — mã băm SHA-256 ở đầu trang dùng để "
         "đối chiếu đúng bản đã rà.", "",
         "## Cách rà", "",
         "1. Đọc cột «Khuôn SAP» của từng hạng mục, đối chiếu với phần «Ví dụ SAP đã điền» ở cuối trang.",
         "2. Đánh dấu «Đồng ý» hoặc «Sửa» ở cột «Thống kê viên»; chọn «Sửa» thì ghi nội dung sửa và căn cứ (PMID/DOI, "
         "hướng dẫn chuẩn báo cáo).",
         "3. Hạng mục ghi «Khuôn SAP của thiết kế này không có dòng nào cho hạng mục này»: đánh dấu «Đồng ý» nếu thiết "
         "kế "
         "không cần hạng mục đó, hoặc «Sửa» và ghi nội dung khuôn còn thiếu.",
         "4. Ký khối «Thống kê viên rà» cuối mỗi trang.", "",
         "## Sau khi rà", "",
         "Nhận xét được đưa về NGUỒN khuôn SAP (`tools/run_g4_auto.py`, `tools/g4_quality_gate.py`), sửa tại nguồn, "
         "chạy lại giả lập các kịch bản rồi phát hành gói rà mới. Gói này không ghi đánh giá thay thống kê viên.", "",
         "## Danh sách trang", "", "| # | Thiết kế | Tệp | Nguồn (SHA-256) |", "|---|---|---|---|"]
    for t in muc_luc["trang"]:
        tep = ", ".join(x for x in (t.get("tep_docx"), t.get("tep_pdf")) if x) or "—"
        d.append(f"| {t['thu_tu']} | {t['nhan']} | {tep} | {t.get('sha256') or 'thiếu nguồn'} |")
    if muc_luc["thieu_nguon"]:
        d += ["", "## Trang chưa dựng (thiếu SAP nguồn của kịch bản giả lập)", ""]
        d += [f"- {x['nhan']} — kịch bản `{x['kich_ban']}`" for x in muc_luc["thieu_nguon"]]
        d += ["", f"Sinh nguồn: `{muc_luc['lenh_sinh_nguon']}`"]
    return "\n".join(d + ["", CAN_KIEM]) + "\n"


def lenh_sinh_nguon(nguon: Path) -> str:
    kb = " ".join(f'"tests/test_gia_lap_tron_vong_20261115.py::{x}"' for x in (
        "test_gia_lap_tron_vong", "test_gia_lap_bien_the_kho[rct_ni]", "test_gia_lap_bien_the_kho[rct_cum]",
        "test_gia_lap_bien_the_kho[case_control_ghep_cap]"))
    return (f"GIA_LAP_NEN_G0_DIR=tests/fixtures/gia_lap_nen_g0 GIA_LAP_TRON_VONG=1 GIA_LAP_TRON_VONG_DIR={nguon} "
            f"GIA_LAP_DEN_CONG=G4 python -B -m pytest -q -s -p no:cacheprovider {kb}")


def _trong_repo(p: Path) -> bool:
    try:
        Path(p).resolve().relative_to(BASE.resolve())
        return True
    except ValueError:
        return False


def dung_goi(nguon: Path, ra: Path, pdf: bool = True) -> Dict[str, Any]:
    ra.mkdir(parents=True, exist_ok=True)
    trang_ds: List[Dict[str, Any]] = []
    thieu: List[Dict[str, Any]] = []
    tong = len(DANH_MUC)
    for i, (ma, kich_ban, thiet_ke, nhan) in enumerate(DANH_MUC, 1):
        sap_p = tim_sap(nguon, kich_ban)
        trang: Dict[str, Any] = {"thu_tu": i, "tong": tong, "ma": ma, "kich_ban": kich_ban, "thiet_ke": thiet_ke,
                                 "nhan": nhan}
        if sap_p is None:
            thieu.append(trang)
            trang_ds.append({**trang, "sha256": None})
            continue
        sap = sap_p.read_text(encoding="utf-8")
        p3 = phan_3(sap)
        hang = trich_hang_muc(sap)
        trang.update({"tep_nguon": f"{kich_ban}/repo/exports/{sap_p.parent.name}/{sap_p.name}",
                      "sha256": _sha256(sap_p), "hang_muc_trong": [k for k, _ in HANG_MUC if not hang.get(k)],
                      "so_pmid": len(hang["pmid"])})
        if not p3:
            thieu.append({**trang, "ly_do": "SAP không có Phần 3"})
            trang_ds.append(trang)
            continue
        ten = f"{i:02d}_RA_KHUON_SAP_{ma}"
        _docx_trang(trang, hang, p3, ra / f"{ten}.docx")
        trang["tep_docx"] = f"{ten}.docx"
        if pdf and in_pdf(_html_trang(trang, hang, p3), ra / f"{ten}.pdf"):
            trang["tep_pdf"] = f"{ten}.pdf"
        trang_ds.append(trang)
    muc_luc = {"schema": SCHEMA, "ngay_dung": datetime.now(timezone.utc).isoformat(timespec="seconds"),
               "nguon": str(nguon), "trang": trang_ds,
               "thieu_nguon": [{"kich_ban": x["kich_ban"], "nhan": x["nhan"], "ly_do": x.get("ly_do", "không có SAP")}
                               for x in thieu],
               "lenh_sinh_nguon": lenh_sinh_nguon(nguon), "pdf": pdf and tim_trinh_duyet() is not None}
    hd = huong_dan_md(muc_luc)
    (ra / "HUONG_DAN_RA_KHUON_SAP.md").write_text(hd, encoding="utf-8", newline="\n")
    try:
        import md2docx_vn  # noqa: PLC0415

        md2docx_vn.markdown_to_docx(hd, ra / "HUONG_DAN_RA_KHUON_SAP.docx")
    except Exception:  # noqa: BLE001 — thiếu python-docx ⇒ vẫn có .md
        pass
    (ra / "MUC_LUC.json").write_text(json.dumps(muc_luc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8",
                                     newline="\n")
    return muc_luc


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Gói rà khuôn SAP cho thống kê viên — mỗi thiết kế một trang.")
    ap.add_argument("--nguon", type=Path, help="thư mục giả lập trọn vòng dừng ở G4 (GIA_LAP_TRON_VONG_DIR)")
    ap.add_argument("--ra", type=Path, help="thư mục gói (NGOÀI repo)")
    ap.add_argument("--khong-pdf", action="store_true", help="chỉ xuất Word")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--lenh-sinh-nguon", type=Path, metavar="THU_MUC", help="in lệnh sinh SAP nguồn rồi thoát")
    a = ap.parse_args(argv)
    if a.lenh_sinh_nguon:
        print(lenh_sinh_nguon(a.lenh_sinh_nguon))
        return 0
    if not a.nguon or not a.ra or not Path(a.nguon).is_dir():
        print("Tham số sai: cần --nguon (thư mục giả lập có sẵn) và --ra (thư mục gói).")
        return 3
    if _trong_repo(a.ra):
        print(f"Từ chối: thư mục gói {a.ra} nằm trong repo — gói rà là tài liệu làm việc, đặt ngoài repo.")
        return 3
    ml = dung_goi(Path(a.nguon), Path(a.ra), pdf=not a.khong_pdf)
    if a.json:
        print(json.dumps(ml, ensure_ascii=False, indent=1))
    else:
        print(f"Gói rà khuôn SAP: {sum(1 for t in ml['trang'] if t.get('tep_docx'))}/{len(DANH_MUC)} trang → {a.ra}")
        for t in ml["trang"]:
            dau = "✓" if t.get("tep_docx") else "✗ thiếu nguồn"
            print(f"  {t['thu_tu']:2d}. {t['nhan']}: {dau}" + (f" · hạng mục trống: {', '.join(t['hang_muc_trong'])}"
                                                            if t.get("hang_muc_trong") else ""))
        if ml["thieu_nguon"]:
            print("Sinh nguồn: " + ml["lenh_sinh_nguon"])
        print(CAN_KIEM)
    return 1 if ml["thieu_nguon"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
