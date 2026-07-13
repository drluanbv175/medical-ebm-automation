#!/usr/bin/env python3
"""Guardrail: kiểm ĐỀ CƯƠNG THỐNG NHẤT (G10) có tuân thủ chuẩn skill không.

Chạy sau khi run_g10_assemble.py lắp ráp, TRƯỚC khi giao cho bác sĩ. Bắt các
lỗi liêm chính/cấu trúc mà mắt thường dễ bỏ sót:

R1. ĐỦ 16 MỤC của mẫu đề cương skill (templates/01).
R2. Có Bảng trạng thái cổng G0-G9 (đủ 10 cổng skill) + Kết luận sẵn sàng (4 mốc).
R3. Mọi NHÃN dạng '[CẦN.../ĐÃ.../DỰ THẢO...]' phải là nhãn skill HỢP LỆ
    (không có nhãn tự chế sai chuẩn).
R4. KHÔNG trích PMID BỊA: mọi PMID xuất hiện phải truy được về checkpoint pipeline
    (G0 raw / G7 seed). PMID lạ = cờ đỏ citation washing.
R5. Có disclaimer 'Cần bác sĩ kiểm chứng'.
R6. KHÔNG nhồi số liệu KẾT QUẢ vào đề cương (đề cương = trước khi có dữ liệu):
    cảnh báo nếu thấy mẫu 'OR/RR/HR = <số> ... KTC 95%: <số>–<số>' với số cụ thể
    (khác tham số thiết kế α/power/N).
R7. Có danh mục bảng/hình chuẩn xuất bản: tối thiểu Bảng 1, Bảng 2, Hình 1, Hình 2
    và checklist caption/trục/đơn vị/n/95%CI để nối SAP → bản thảo.
R8. Có ma trận tuân thủ tiêu chuẩn quốc tế: reporting checklist đúng thiết kế
    (CONSORT/STROBE/...), ICH-GCP/IRB khi áp dụng, SAP, minh bạch và tái lập.

Trả về report dict{passed, errors[], warnings[], checks{}}. Lỗi R1-R5, R7, R8 = ĐỎ
(passed=False). R6 = cảnh báo (không chặn, vì một số tham số giả định hợp lệ).

Dùng: python3 tools/check_de_cuong.py --study <MÃ>   (hoặc import validate()).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Set

BASE = Path(__file__).resolve().parents[1]
TOOLS = BASE / "tools"
sys.path.insert(0, str(TOOLS))

import skill_standards as S  # noqa: E402

# Nhãn "trông giống marker": mở ngoặc vuông + bắt đầu bằng các từ khoá này.
_MARKER_WORD_RE = re.compile(r"\[\s*(CẦN|ĐÃ|DỰ THẢO|CHƯA)\b[^\]]*\]")
# THÊM 2026-07-06: "[CẦN — giải thích tự do]" (CẦN + em-dash + văn bản) là quy
# ước CHÚ THÍCH TỰ DO đã dùng phổ biến (118+ chỗ) khắp G0-G9 — KHÁC với 6 nhãn
# TRẠNG THÁI cố định của S.VALID_STATUS_TAGS (vd "[CẦN BỔ SUNG]"). R3 trước đây
# coi CẢ HAI loại là "nhãn" và chỉ chấp nhận 6 nhãn cố định, nên MỌI chú thích
# tự do (rất phổ biến, hợp lệ, không phải "nhãn tự chế sai chuẩn" mà R3 muốn
# bắt) đều bị báo lỗi — phát hiện qua chạy thật G0→G10 thiết kế chẩn đoán
# (n_auc's formula_used message) khiến G10 CRASH thật lần đầu tiên đề tài loại
# này chạy hết pipeline. Chỉ "CẦN —" dùng quy ước này (grep xác nhận ĐÃ/DỰ
# THẢO/CHƯA không có biến thể em-dash tự do nào trong codebase).
_FREEFORM_CAN_RE = re.compile(r"^\[CẦN\s+—\s+.+\]$")
# PMID trong văn bản: 'PMID: 12345' hoặc '[PMID:12345]' hoặc 'PMID 12345'.
_PMID_RE = re.compile(r"PMID[:\s]*?(\d{5,9})")
# Mẫu số liệu KẾT QUẢ (chỉ xuất hiện ở phần kết quả, KHÔNG phải tham số thiết kế).
# Sửa #3: mở rộng để bắt nhiều dạng hơn — nhưng CHỈ dạng đặc thù kết quả để
# tránh báo nhầm tham số thiết kế (α=0.05, p=0.50 prevalence, power=0.80).
_RESULT_PATTERNS = [
    # Đo lường hiệu ứng + KTC/CI có số: 'OR = 1.9 (KTC 95%: 1.2-3.1)', 'aOR 2,3 CI'
    re.compile(r"\b(?:OR|RR|HR|aOR|aHR|SMD|MD)\b\s*[=:]?\s*\d+[.,]\d+.{0,40}?(?:KTC|CI|95\s*%)",
               re.IGNORECASE),
    # p-value rất nhỏ (p<0.001, p = 0,0001) — không bao giờ là tham số thiết kế.
    re.compile(r"\bp\s*[<>=]\s*0[.,]0{2,}\d*", re.IGNORECASE),
    # Tỷ lệ % kèm KTC/CI (kết quả tỷ lệ hiện mắc thật): '61,95% (KTC 95%: 53-70)'
    re.compile(r"\d+[.,]\d+\s*%\s*\(?\s*(?:KTC|CI|95\s*%)", re.IGNORECASE),
]
_DISPLAY_REQUIRED_ITEMS = ("Bảng 1", "Bảng 2", "Hình 1", "Hình 2")
_DISPLAY_REQUIRED_TERMS = ("caption", "trục", "đơn vị", "n", "95% CI")
_COMPLIANCE_REQUIRED_TERMS = (
    "CONSORT", "STROBE", "ICH-GCP", "GCP", "IRB", "SAP",
    "data availability", "code availability", "COI", "AI disclosure",
    "minh bạch", "tái lập",
)


def _raw_pmids(out_dir: Path) -> Set[str]:
    """PMID có NGUỒN THẬT = truy hồi từ PubMed (G0_pubmed_raw.json) mà thôi.

    Sửa #1/#2: chỉ những PMID này mới là 'đã đối chiếu nguồn'. KHÔNG gộp seed."""
    raw: Set[str] = set()
    g0raw = out_dir / "G0_pubmed_raw.json"
    if g0raw.exists():
        try:
            raw |= _harvest_pmids_from_obj(json.loads(g0raw.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            pass
    return raw


def _seed_pmids(out_dir: Path) -> Set[str]:
    """PMID 'hạt giống' = có trong checkpoint (G7 seed, v.v.) nhưng CHƯA chắc đối
    chiếu PubMed raw. Tách riêng để không tự chứng nhận là 'đã truy nguồn'."""
    seed: Set[str] = set()
    for g in range(11):
        p = out_dir / f"G{g}_checkpoint.json"
        if p.exists():
            try:
                seed |= _harvest_pmids_from_obj(json.loads(p.read_text(encoding="utf-8")))
            except (json.JSONDecodeError, OSError):
                pass
    return seed


def _harvest_pmids_from_obj(obj) -> Set[str]:
    """Đệ quy gom mọi chuỗi số 5-9 chữ số nằm ở key/giá trị liên quan 'pmid'."""
    out: Set[str] = set()

    def walk(o, key_hint=""):
        if isinstance(o, dict):
            for k, v in o.items():
                walk(v, str(k).lower())
        elif isinstance(o, list):
            for v in o:
                walk(v, key_hint)
        else:
            s = str(o)
            if "pmid" in key_hint and re.fullmatch(r"\d{5,9}", s):
                out.add(s)
            # Chuỗi có 'PMID: 12345'
            for m in _PMID_RE.finditer(s):
                out.add(m.group(1))
    walk(obj)
    return out


def validate(md_path, out_dir) -> Dict:
    """Kiểm 1 file đề cương .md. Trả report dict."""
    md_path = Path(md_path)
    out_dir = Path(out_dir)
    text = md_path.read_text(encoding="utf-8")

    errors: List[str] = []
    warnings: List[str] = []
    checks: Dict[str, str] = {}

    # R1 — đủ 16 mục.
    missing_sections = []
    for num, title, _sub in S.DE_CUONG_SECTIONS:
        # Heading dạng "# {num}. {title}" — khớp linh hoạt dấu cách.
        pat = re.compile(rf"^#\s*{re.escape(num)}\.\s*{re.escape(title)}",
                         re.MULTILINE)
        if not pat.search(text):
            missing_sections.append(f"{num}. {title}")
    if missing_sections:
        errors.append(f"R1 THIẾU MỤC ĐỀ CƯƠNG: {', '.join(missing_sections)}")
        checks["R1_16_sections"] = f"FAIL (thiếu {len(missing_sections)})"
    else:
        checks["R1_16_sections"] = "PASS (đủ 16 mục)"

    # R2 — bảng cổng + kết luận sẵn sàng.
    n_skill_gates_in_table = sum(
        1 for sg in S.SKILL_GATES if re.search(rf"\|\s*{sg}\s*\|", text)
    )
    has_readiness = all(
        milestone[0] in text for milestone in S.READINESS_MILESTONES
    )
    if n_skill_gates_in_table < len(S.SKILL_GATES):
        errors.append(
            f"R2 BẢNG CỔNG thiếu: chỉ thấy {n_skill_gates_in_table}/"
            f"{len(S.SKILL_GATES)} cổng skill.")
        checks["R2_gate_table"] = f"FAIL ({n_skill_gates_in_table}/10 cổng)"
    elif not has_readiness:
        errors.append("R2 THIẾU đủ 4 mốc kết luận sẵn sàng.")
        checks["R2_gate_table"] = "FAIL (thiếu mốc sẵn sàng)"
    else:
        checks["R2_gate_table"] = "PASS (10 cổng + 4 mốc)"

    # R3 — nhãn hợp lệ.
    bad_tags = set()
    for m in _MARKER_WORD_RE.finditer(text):
        tag = m.group(0).strip()
        if S.is_valid_status_tag(tag):
            continue
        if _FREEFORM_CAN_RE.match(tag):
            continue
        bad_tags.add(tag)
    if bad_tags:
        errors.append("R3 NHÃN KHÔNG HỢP LỆ (không thuộc bộ nhãn skill): "
                      + "; ".join(sorted(bad_tags)[:10]))
        checks["R3_valid_tags"] = f"FAIL ({len(bad_tags)} nhãn lạ)"
    else:
        checks["R3_valid_tags"] = "PASS"

    # R4 — PMID truy nguồn (sửa #1/#2: tách raw-PubMed thật vs seed-only).
    raw = _raw_pmids(out_dir)          # nguồn THẬT (đã truy hồi PubMed)
    seed = _seed_pmids(out_dir)        # chỉ có trong checkpoint (chưa chắc đối chiếu raw)
    doc_pmids = {m.group(1) for m in _PMID_RE.finditer(text)}
    fabricated = sorted(doc_pmids - raw - seed)   # không ở đâu cả → bịa
    seed_only = sorted((doc_pmids & seed) - raw)  # ở seed nhưng KHÔNG ở raw
    raw_verified = sorted(doc_pmids & raw)
    if fabricated:
        errors.append(
            f"R4 PMID KHÔNG TRUY ĐƯỢC VỀ BẤT KỲ NGUỒN NÀO (nghi bịa): "
            f"{', '.join(fabricated[:10])}.")
        checks["R4_pmid_traceable"] = f"FAIL ({len(fabricated)} PMID không nguồn)"
    elif seed_only:
        # KHÔNG fail (đề cương đã gắn nhãn [CẦN KIỂM CHỨNG]), nhưng PHẢI cảnh báo
        # rõ — không được báo 'đều truy được' như cũ (bug tự-chứng-nhận).
        warnings.append(
            f"R4 CẢNH BÁO: {len(seed_only)}/{len(doc_pmids)} PMID chỉ có trong "
            f"'seed' checkpoint, CHƯA đối chiếu PubMed raw ({len(raw)} PMID raw "
            f"thật): {', '.join(seed_only[:10])}. Có thể là seed MỒ CÔI từ đề tài "
            "khác — bác sĩ PHẢI kiểm chứng từng PMID (nối `kiem-chung-trich-dan`) "
            "trước khi đưa vào TLTK.")
        checks["R4_pmid_traceable"] = (
            f"WARN ({len(raw_verified)} đối chiếu raw, {len(seed_only)} chỉ-seed cần kiểm)")
    else:
        checks["R4_pmid_traceable"] = (
            f"PASS ({len(raw_verified)}/{len(doc_pmids)} PMID đối chiếu PubMed raw)")

    # R5 — disclaimer.
    if "kiểm chứng" not in text.lower():
        errors.append("R5 THIẾU disclaimer 'Cần bác sĩ kiểm chứng'.")
        checks["R5_disclaimer"] = "FAIL"
    else:
        checks["R5_disclaimer"] = "PASS"

    # R6 — cảnh báo số liệu kết quả (không chặn; mở rộng mẫu — sửa #3).
    result_hits = []
    for pat in _RESULT_PATTERNS:
        result_hits.extend(pat.findall(text))
    if result_hits:
        warnings.append(
            f"R6 CẢNH BÁO: thấy {len(result_hits)} mẫu số liệu KẾT QUẢ (OR/RR/HR+CI, "
            "p<0.00x, hoặc %+KTC) trong ĐỀ CƯƠNG — đề cương là TRƯỚC khi có dữ "
            "liệu, kiểm lại xem có số liệu thật/bịa lọt vào không.")
        checks["R6_no_results"] = f"WARN ({len(result_hits)} mẫu)"
    else:
        checks["R6_no_results"] = "PASS"

    # R7 — danh mục bảng/hình và checklist trình bày đồ thị.
    has_display_section = re.search(
        r"^#\s*Danh mục bảng và hình chuẩn xuất bản\b", text, re.MULTILINE)
    missing_display_items = [
        item for item in _DISPLAY_REQUIRED_ITEMS
        if not re.search(rf"\|\s*{re.escape(item)}\s*\|", text)
    ]
    lowered = text.lower()
    missing_terms = [
        term for term in _DISPLAY_REQUIRED_TERMS
        if term.lower() not in lowered
    ]
    if not has_display_section:
        errors.append("R7 THIẾU mục 'Danh mục bảng và hình chuẩn xuất bản'.")
        checks["R7_display_items"] = "FAIL (thiếu mục bảng/hình)"
    elif missing_display_items:
        errors.append("R7 DANH MỤC BẢNG/HÌNH thiếu: "
                      + ", ".join(missing_display_items))
        checks["R7_display_items"] = (
            f"FAIL (thiếu {len(missing_display_items)} mục bắt buộc)")
    elif missing_terms:
        errors.append("R7 CHECKLIST HÌNH/BẢNG thiếu thuật ngữ bắt buộc: "
                      + ", ".join(missing_terms))
        checks["R7_display_items"] = (
            f"FAIL (thiếu {len(missing_terms)} tiêu chí)")
    else:
        checks["R7_display_items"] = "PASS (Bảng 1/2 + Hình 1/2 + checklist)"

    # R8 — ma trận tuân thủ quốc tế và khả năng tái lập.
    has_compliance_section = re.search(
        r"^#\s*Ma trận tuân thủ tiêu chuẩn quốc tế\b", text, re.MULTILINE)
    missing_compliance_terms = [
        term for term in _COMPLIANCE_REQUIRED_TERMS
        if term.lower() not in lowered
    ]
    if not has_compliance_section:
        errors.append("R8 THIẾU mục 'Ma trận tuân thủ tiêu chuẩn quốc tế'.")
        checks["R8_international_compliance"] = "FAIL (thiếu ma trận)"
    elif missing_compliance_terms:
        errors.append("R8 MA TRẬN TUÂN THỦ thiếu thuật ngữ bắt buộc: "
                      + ", ".join(missing_compliance_terms))
        checks["R8_international_compliance"] = (
            f"FAIL (thiếu {len(missing_compliance_terms)} tiêu chí)")
    else:
        checks["R8_international_compliance"] = (
            "PASS (reporting + ICH-GCP/IRB + SAP + transparency + reproducibility)")

    passed = len(errors) == 0
    return {"passed": passed, "errors": errors, "warnings": warnings,
            "checks": checks, "n_raw_pmids": len(raw), "n_seed_pmids": len(seed),
            "seed_only_pmids": seed_only, "raw_verified_pmids": raw_verified,
            "doc_pmids": sorted(doc_pmids)}


def print_report(report: Dict) -> None:
    status = "✅ PASS" if report["passed"] else "❌ FAIL"
    print(f"  Guardrail đề cương (skill): {status}")
    for name, res in report["checks"].items():
        print(f"    - {name}: {res}")
    for e in report["errors"]:
        print(f"    ❌ {e}")
    for w in report["warnings"]:
        print(f"    ⚠ {w}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Kiểm đề cương thống nhất (G10).")
    ap.add_argument("--study", required=True, help="Mã đề tài")
    ap.add_argument("--file", default=None,
                    help="Đường dẫn .md (mặc định: DE_CUONG_THONG_NHAT_<study>.md)")
    args = ap.parse_args()

    out_dir = BASE / "exports" / args.study
    md_path = Path(args.file) if args.file else out_dir / f"DE_CUONG_THONG_NHAT_{args.study}.md"
    if not md_path.exists():
        print(f"❌ Không thấy file {md_path}")
        return 2

    report = validate(md_path, out_dir)
    print_report(report)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
