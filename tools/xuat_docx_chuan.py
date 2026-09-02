#!/usr/bin/env python3
"""Xuất .docx CHUẨN TRÌNH BÀY từ artifact .md HIỆN CÓ — không sinh lại nội dung.

★ VÌ SAO TỒN TẠI (02/09/2026): sau khi có rào chống đè (G2/G4 từ chối tái
sinh khi hồ sơ đã biên tập đầy đủ hơn template) thì đường DUY NHẤT tới bản
.docx là chạy lại cổng — mà chạy lại thì bị rào chặn (đúng), nên .docx của
hồ sơ đạo đức và SAP đã biên tập KẸT ở bản cũ (đo trên C1a: G2 còn 130, G4
còn 342 ký tự trang trí, 12pt). G0 cũng kẹt vì tái sinh cần mạng PubMed.

Công cụ này tách hai việc vốn bị dính vào nhau: NỘI DUNG (.md — do cổng/bác
sĩ biên tập, có rào) và TRÌNH BÀY (.docx — luôn render lại được). Nó chỉ
đọc .md và render qua md2docx_vn (Times New Roman 13pt, bảng Word thật,
chuẩn luận văn VN) + làm sạch ký tự trang trí (chuan_trinh_bay). KHÔNG chạm
.md, KHÔNG chạm checkpoint/ledger, KHÔNG qua mạng.

Cách dùng:
    python3 tools/xuat_docx_chuan.py --study <mã>          # mọi G*_A*_<mã>.md
    python3 tools/xuat_docx_chuan.py --file <đường/dẫn.md>  # một file
Mã thoát: 0 = xong · 1 = không có file nào để render · 2 = lỗi render.
Cần bác sĩ kiểm chứng.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

BASE = Path(__file__).resolve().parents[1]
TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))

import chuan_trinh_bay as _CTB  # noqa: E402
import md2docx_vn as M2D  # noqa: E402

# Artifact của cổng: G<n>_A<m>_<mã>.md — KHÔNG lấy checkpoint/quality report
# (json/md máy đọc) và không lấy tài liệu do agent viết tay (De-cuong_*).
MAU_ARTIFACT = re.compile(r"^G\d{1,2}_A\d{1,2}[a-z]?_.+\.md$")


def render_mot_file(md_path: Path) -> Path:
    """Render một .md → .docx cùng tên. Trả đường dẫn .docx."""
    md_text = md_path.read_text(encoding="utf-8")
    # Dòng đầu là tiêu đề cấp 1 → dùng làm tiêu đề; phần còn lại là thân bài
    docx_path = md_path.with_suffix(".docx")
    M2D.markdown_to_docx(md_text, docx_path)
    return docx_path


def do_ky_tu_la(docx_path: Path) -> int:
    """Đếm ký tự trang trí còn lại trong .docx (để in kết quả đo, không quyết định)."""
    from docx import Document
    doc = Document(docx_path)
    n = 0
    for p in doc.paragraphs:
        n += sum(1 for ch in p.text if _CTB._la_ky_tu_ve(ch) or ch in _CTB._THAY_KY_HIEU
                 or ch in _CTB._BO_HAN)
    return n


def main() -> int:
    ap = argparse.ArgumentParser(description="Xuất .docx chuẩn trình bày từ artifact .md hiện có")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--study", help="Mã đề tài — render mọi G*_A*_<mã>.md trong exports/<mã>/")
    g.add_argument("--file", help="Một file .md cụ thể")
    a = ap.parse_args()

    if a.file:
        files = [Path(a.file)]
    else:
        study = re.sub(r"[^\w\-]", "_", a.study.strip().replace(" ", "-"))
        out_dir = BASE / "exports" / study
        files = sorted(p for p in out_dir.glob("*.md") if MAU_ARTIFACT.match(p.name))
    files = [f for f in files if f.exists()]
    if not files:
        print("⚠️  Không có artifact .md nào để render.")
        return 1

    loi = 0
    for f in files:
        try:
            out = render_mot_file(f)
            print(f"  ✓ {out.name}  (ký tự trang trí còn lại: {do_ky_tu_la(out)})")
        except Exception as e:  # noqa: BLE001 — báo từng file, không giết cả lượt
            loi += 1
            print(f"  ✗ {f.name}: {e}")
    print("Cần bác sĩ kiểm chứng.")
    return 2 if loi else 0


if __name__ == "__main__":
    raise SystemExit(main())
