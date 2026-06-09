#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_library_catalog.py — Lập DANH MỤC thư viện y văn thật của bác sĩ (đọc-tại-chỗ).

Quét kho tài liệu lâm sàng nằm rải rác ở gốc OneDrive (PDF/Word/PowerPoint), phân loại theo
CHUYÊN KHOA + LOẠI tài liệu bằng heuristic từ khóa, rồi xuất danh mục để skill
`clinical-evidence-rag` tra cứu. KHÔNG copy/di chuyển file gốc (tránh trùng lặp + bản quyền) —
chỉ ghi đường dẫn tương đối. File hành chính (lý lịch/mẫu bìa/danh sách...) bị gắn cờ admin và
tách riêng để không nhiễu kho chứng cứ.

Cách dùng:
    python3 scripts/build_library_catalog.py              # quét mặc định, xuất vào evidence/external-library/
    python3 scripts/build_library_catalog.py --root "<đường dẫn>" --today 2026-06-09

Đầu ra:
    evidence/external-library/catalog.json   — dữ liệu đầy đủ
    evidence/external-library/CATALOG.md     — bảng cho người đọc, nhóm theo chuyên khoa
"""
import os
import re
import sys
import json
import argparse

CLINICAL_EXT = {".pdf", ".docx", ".doc", ".pptx", ".ppt", ".md"}

# Thư mục KHÔNG quét (mã nguồn, đồng bộ, đầu ra routine, kho ứng dụng)
EXCLUDE_DIRS = {
    "Claude AI", "Apps", "node_modules", ".git", "__pycache__", "_archive",
    "EBM cho thực hành lâm sàng hàng tuần",
    "Cập nhật các thông tin quan trọng về thuốc và kháng sinh trong thực hành lâm sàng",
    "Cập nhật cho thực hành lâm sàng",
    "Tổng hợp tất cả cập nhật quan trọng trong tháng",
}

# Chuyên khoa: (nhãn, các từ khóa nhận diện trong tên file, không phân biệt hoa thường)
SPECIALTY = [
    ("Tim mạch", ["tim mach", "cardio", " esc ", "heart", "suy tim", "nhoi mau", "nmct", "tha ", "huyet ap", "rung nhi", "af ", "acs", "lipid", "cholesterol", "statin", "zofenopril", "antiplatelet", "anticoagul"]),
    ("Thần kinh", ["than kinh", "neuro", "dot quy", "stroke", "dong kinh", "parkinson", "chong mat", "sa sut tri tue", "dementia"]),
    ("Nội tiết - ĐTĐ", ["dai thao duong", "diabetes", "dtd", "noi tiet", "tuyen giap", "thyroid", "insulin", "hba1c", "dsf"]),
    ("Thận - Tiết niệu", ["than man", "ckd", "kdigo", "than nhan tao", "loc mau", "than-", "creatinin"]),
    ("Hô hấp", ["ho hap", "copd", "gold", "hen", "asthma", "phoi", "viem phoi", "pneumonia"]),
    ("Tiêu hóa - Gan mật", ["tieu hoa", "gan ", "gan-", "hepat", "aasld", "easl", "xo gan", "cirrho", "viem gan", "masld", "nafld"]),
    ("Cơ xương khớp", ["co xuong", "khop", "rheum", "gout", "loang xuong", "osteoporo", "viem khop"]),
    ("Nhiễm - Kháng sinh", ["nhiem khuan", "khang sinh", "antibiotic", "idsa", "sepsis", "nhiem trung", "vaccine", "aware"]),
    ("Da liễu", ["da lieu", "atopic", "dermatit", "eczema", "chàm", "cham", "phat ban", "vay nen", "psoriasis"]),
    ("Lão khoa - Đa bệnh", ["lao khoa", "nguoi cao tuoi", "geriatr", "beers", "stopp", "da thuoc", "frailty", "polypharmacy"]),
    ("Cấp cứu - HSCC", ["cap cuu", "emergency", "hoi suc", "icu", "cpr"]),
    ("Dinh dưỡng", ["dinh duong", "nutrition", "nutri"]),
    ("Chẩn đoán hình ảnh", ["imaging", "x quang", "x-quang", "ct ", "mri", "sieu am", "anatomy", "radiolog", "/cls/", "cdha"]),
    ("Nội tổng quát / khác", ["bates", "physical examination", "mayo", "harrison", "noi khoa", "kham benh", "noi chung"]),
]

# Loại tài liệu
DOC_TYPE = [
    ("guideline", ["guideline", "khuyen cao", "huong dan", "recommendation", "standard", "consensus", "policy", "kdigo", "gold", " esc ", "aha", "idsa", "aasld", "uspstf", "nice"]),
    ("textbook/sách", ["textbook", "concise", "pocket guide", "handbook", "edition", "atlas", "sach"]),
    ("slide/báo cáo HN", ["bao cao", "hoi nghi", "hoi thao", "hnkh", "seminar", "slide", ".pptx", ".ppt"]),
    ("review/tổng quan", ["review", "tong quan", "meta", "systematic"]),
    ("ca lâm sàng", ["ca lam sang", "case", "tinh huong"]),
    ("nghiên cứu/đề tài", ["nghien cuu", "de tai", "de cuong", "thuyet minh", "nckh", "khao sat"]),
]

# Cờ HÀNH CHÍNH (loại khỏi kho chứng cứ)
ADMIN = ["ly lich", "ly-lich", "mau bia", "mau-bia", "danh sach", "danh-sach", "minh chung",
         "ket qua trong nien han", "ke hoach", "cong van", "bien ban", "du toan", "kinh phi",
         "to trinh", "quyet dinh", "hop dong", "bao cao ket qua", "llkh", "shkh", "de bat quan",
         "nang luong", "bsc.c", "mau dtcs", "dlqn"]


def norm(s):
    """Bỏ dấu tiếng Việt + lower để khớp từ khóa."""
    s = s.lower()
    for a, b in [("áàảãạăắằẳẵặâấầẩẫậ", "a"), ("éèẻẽẹêếềểễệ", "e"), ("íìỉĩị", "i"),
                 ("óòỏõọôốồổỗộơớờởỡợ", "o"), ("úùủũụưứừửữự", "u"), ("ýỳỷỹỵ", "y"), ("đ", "d")]:
        for ch in a:
            s = s.replace(ch, b)
    return s


def classify(name_norm, table, default=None):
    for label, kws in table:
        for kw in kws:
            if kw.strip() and kw in name_norm:
                return label
    return default


def is_admin(name_norm):
    return any(kw in name_norm for kw in ADMIN)


def find_year(name):
    m = re.findall(r"(19|20)\d{2}", name)
    return m and (m[0] + re.search(r"(19|20)(\d{2})", name).group(2)) or ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=None, help="Thư mục gốc để quét (mặc định: gốc OneDrive)")
    ap.add_argument("--out", default=None, help="Thư mục xuất (mặc định: evidence/external-library)")
    ap.add_argument("--today", default="", help="Ngày YYYY-MM-DD để đóng dấu (script không tự lấy giờ)")
    ap.add_argument("--maxdepth", type=int, default=3)
    args = ap.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))               # .../medical-ebm-automation/scripts
    repo = os.path.dirname(here)                                    # .../medical-ebm-automation
    onedrive_root = os.path.dirname(os.path.dirname(repo))          # .../OneDrive-Personal(2)
    root = args.root or onedrive_root
    out = args.out or os.path.join(repo, "evidence", "external-library")
    os.makedirs(out, exist_ok=True)

    root = os.path.abspath(root)
    base_depth = root.rstrip(os.sep).count(os.sep)
    items, admin_items = [], []

    for dirpath, dirnames, filenames in os.walk(root):
        depth = dirpath.count(os.sep) - base_depth
        if depth >= args.maxdepth:
            dirnames[:] = []
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS and not d.startswith(".")]
        for fn in filenames:
            ext = os.path.splitext(fn)[1].lower()
            if ext not in CLINICAL_EXT:
                continue
            rel = os.path.relpath(os.path.join(dirpath, fn), root)
            nn = norm(fn)
            pn = norm(rel)  # gồm cả tên THƯ MỤC (TIM MẠCH/, THẦN KINH/...) → tín hiệu chuyên khoa mạnh
            in_endnote = "endnote" in pn
            rec = {
                "file": fn,
                "path": rel,
                "ext": ext.lstrip("."),
                "year": find_year(fn),
                # Ưu tiên khớp theo đường dẫn (thư mục chuyên khoa), rồi mới tới tên file
                "specialty": classify(pn, SPECIALTY, "Nội tổng quát / khác"),
                "doc_type": "papers/EndNote" if in_endnote else classify(nn, DOC_TYPE, "khác"),
                "source": "EndNote library" if in_endnote else "thư mục lâm sàng",
            }
            (admin_items if is_admin(nn) else items).append(rec)

    items.sort(key=lambda r: (r["specialty"], r["doc_type"], r["file"].lower()))

    catalog = {
        "meta": {
            "generated": args.today or "(chưa đóng dấu ngày)",
            "root": root,
            "clinical_count": len(items),
            "admin_excluded": len(admin_items),
            "note": "Đọc-tại-chỗ; đường dẫn TƯƠNG ĐỐI so với 'root'. Không copy file gốc.",
        },
        "items": items,
        "admin_excluded": admin_items,
    }
    json.dump(catalog, open(os.path.join(out, "catalog.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    # CATALOG.md — nhóm theo chuyên khoa
    by_spec = {}
    for r in items:
        by_spec.setdefault(r["specialty"], []).append(r)
    lines = [
        "# Danh mục thư viện y văn thật (đọc-tại-chỗ) — cho clinical-evidence-rag",
        "",
        f"> Sinh tự động bởi `scripts/build_library_catalog.py` · ngày: {catalog['meta']['generated']}",
        f"> Gốc quét: `{root}`",
        f"> **{len(items)} tài liệu lâm sàng** (đã loại {len(admin_items)} file hành chính).",
        ">",
        "> Đây là danh mục THAM CHIẾU: file gốc nằm nguyên ở OneDrive, không copy vào repo (bản quyền).",
        "> Khi trả lời RAG, ưu tiên: protocol cục bộ > guideline > review > bài báo. Xem `../citation-format.md`.",
        "",
    ]
    for spec in sorted(by_spec):
        rs = by_spec[spec]
        lines.append(f"## {spec} ({len(rs)})")
        lines.append("")
        lines.append("| Tài liệu | Loại | Năm | Đường dẫn |")
        lines.append("|----------|------|-----|-----------|")
        for r in rs:
            safe = r["file"].replace("|", "\\|")
            path = r["path"].replace("|", "\\|")
            lines.append(f"| {safe} | {r['doc_type']} | {r['year'] or '—'} | `{path}` |")
        lines.append("")
    open(os.path.join(out, "CATALOG.md"), "w", encoding="utf-8").write("\n".join(lines))

    print("Danh mục: %d tài liệu lâm sàng, %d file hành chính (loại) → %s" %
          (len(items), len(admin_items), out))
    by = {}
    for r in items:
        by[r["specialty"]] = by.get(r["specialty"], 0) + 1
    for k in sorted(by, key=lambda x: -by[x]):
        print("  %3d  %s" % (by[k], k))
    return 0


if __name__ == "__main__":
    sys.exit(main())
