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
R9. Có bảng kiểm hoàn thành kỹ thuật: khóa phạm vi, phân biệt nguồn thông tin,
    đủ 10 bước, đủ bộ 16 đầu ra, kiểm định cuối và quy tắc chỉ ghi HOÀN THÀNH
    KỸ THUẬT khi mọi lỗi nghiêm trọng đã xử lý.
R10. Không tự tuyên bố “HOÀN THÀNH KỸ THUẬT” nếu chưa có đủ tín hiệu đời thực:
     IRB thật, SAP khóa, dữ liệu khóa, kết quả thật, gói liêm chính ký.
R11. Có danh sách thông tin còn thiếu và quyết định cần xác nhận: mỗi tín hiệu
     đời thực còn thiếu phải có ảnh hưởng, phương án an toàn và người quyết định.
R12. Có kiểm soát phiên bản và lịch sử thay đổi: phiên bản, ngày cập nhật, nguồn
     thay đổi và người phê duyệt/chủ nhiệm phải hiện rõ trong đầu ra chính.
R13. Có ma trận truy xuất mục tiêu-biến-công cụ-phân tích-bảng để đồng bộ
     protocol, CRF/codebook, SAP, bảng/hình và kết luận.

Trả về report dict{passed, errors[], warnings[], checks{}}. Lỗi R1-R5, R7-R13 = ĐỎ
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
_TECHNICAL_COMPLETION_TERMS = (
    "Nội dung đã được khóa",
    "Phân biệt nguồn thông tin",
    "Quy trình 10 bước",
    "Bộ đầu ra bắt buộc",
    "Kiểm định cuối trước khi ký",
    "Cấu trúc báo cáo cuối",
    "HOÀN THÀNH KỸ THUẬT",
)
_COMPLETION_CLAIM_RE = re.compile(
    r"(?im)^\s*(?:[-*]\s*)?"
    r"(?:kết luận[^:\n]{0,80}|trạng thái[^:\n]{0,80}|verdict|final status|decision)"
    r"\s*[:：-]\s*(?!CHƯA\b)(?:ĐÃ\s*)?HOÀN THÀNH KỸ THUẬT\b"
)
_COMPLETION_REQUIRED_SIGNALS = (
    "irb_approved", "sap_locked", "db_locked", "results_final", "integrity_signed",
)
_MISSING_INFO_REQUIRED_TERMS = (
    "Thông tin còn thiếu", "Ảnh hưởng", "Phương án an toàn", "Người quyết định",
)
_DOCUMENT_CONTROL_REQUIRED_TERMS = (
    "Phiên bản tài liệu",
    "Ngày tạo/cập nhật",
    "Nguồn thay đổi",
    "Người phê duyệt/chủ nhiệm",
    "Nhật ký thay đổi",
)
_TRACEABILITY_REQUIRED_TERMS = (
    "Mục tiêu/câu hỏi",
    "Biến/kết cục",
    "Công cụ/nguồn dữ liệu",
    "Phân tích định trước",
    "Bảng/hình đầu ra",
    "Cổng nguồn",
)


def _load_json(path: Path) -> Dict:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return {}


def _load_checkpoints(out_dir: Path) -> Dict[str, Dict]:
    cps: Dict[str, Dict] = {}
    for g in range(11):
        p = out_dir / f"G{g}_checkpoint.json"
        if p.exists():
            cps[f"G{g}"] = _load_json(p)
    return cps


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

    # R9 — bảng kiểm hoàn thành kỹ thuật theo đặc tả vận hành.
    has_completion_section = re.search(
        r"^#\s*Bảng kiểm hoàn thành kỹ thuật\b", text, re.MULTILINE)
    missing_completion_terms = [
        term for term in _TECHNICAL_COMPLETION_TERMS
        if term.lower() not in lowered
    ]
    missing_steps = [
        step_id for step_id, _name, _criterion in S.RESEARCH_COMPLETION_STEPS
        if not re.search(rf"\|\s*{re.escape(step_id)}\s*\|", text)
    ]
    missing_outputs = [
        item for item in S.RESEARCH_OUTPUT_PACKAGE_ITEMS
        if item.lower() not in lowered
    ]
    missing_final_checks = [
        item for item in S.FINAL_TECHNICAL_CHECKS
        if item.lower() not in lowered
    ]
    if not has_completion_section:
        errors.append("R9 THIẾU mục 'Bảng kiểm hoàn thành kỹ thuật'.")
        checks["R9_technical_completion"] = "FAIL (thiếu bảng kiểm)"
    elif missing_completion_terms:
        errors.append("R9 BẢNG KIỂM HOÀN THÀNH thiếu mục bắt buộc: "
                      + ", ".join(missing_completion_terms))
        checks["R9_technical_completion"] = (
            f"FAIL (thiếu {len(missing_completion_terms)} mục lõi)")
    elif missing_steps:
        errors.append("R9 THIẾU bước quy trình: " + ", ".join(missing_steps))
        checks["R9_technical_completion"] = (
            f"FAIL (thiếu {len(missing_steps)} bước)")
    elif missing_outputs:
        errors.append("R9 THIẾU tài liệu đầu ra bắt buộc: "
                      + "; ".join(missing_outputs[:5]))
        checks["R9_technical_completion"] = (
            f"FAIL (thiếu {len(missing_outputs)} đầu ra)")
    elif missing_final_checks:
        errors.append("R9 THIẾU câu hỏi kiểm định cuối: "
                      + "; ".join(missing_final_checks[:5]))
        checks["R9_technical_completion"] = (
            f"FAIL (thiếu {len(missing_final_checks)} kiểm định)")
    else:
        checks["R9_technical_completion"] = (
            "PASS (10 bước + 16 đầu ra + kiểm định cuối + quy tắc hoàn thành)")

    # R10 — chống tự tuyên bố hoàn thành kỹ thuật khi cổng đời thực chưa đủ.
    completion_claims = [m.group(0).strip() for m in _COMPLETION_CLAIM_RE.finditer(text)]
    cps = _load_checkpoints(out_dir)
    meta = _load_json(out_dir / "study_meta.json")
    signals = S.real_world_signals(cps, meta)
    missing_signals = [s for s in _COMPLETION_REQUIRED_SIGNALS if not signals.get(s)]
    if completion_claims and missing_signals:
        errors.append(
            "R10 TỰ TUYÊN BỐ HOÀN THÀNH KỸ THUẬT khi thiếu tín hiệu đời thực: "
            + ", ".join(missing_signals)
            + ". Chỉ được ghi 'CHƯA HOÀN THÀNH KỸ THUẬT' hoặc mô tả điều kiện còn thiếu.")
        checks["R10_no_false_completion"] = (
            f"FAIL ({len(completion_claims)} tuyên bố, thiếu {len(missing_signals)} tín hiệu)")
    elif completion_claims:
        checks["R10_no_false_completion"] = (
            "PASS (có tuyên bố hoàn thành và đủ tín hiệu đời thực)")
    else:
        checks["R10_no_false_completion"] = (
            "PASS (không tự tuyên bố hoàn thành kỹ thuật)")

    # R11 — bảng thông tin còn thiếu/cần xác nhận để bác sĩ biết điểm chặn.
    has_missing_info_section = re.search(
        r"^#\s*Danh sách thông tin còn thiếu và quyết định cần xác nhận\b",
        text, re.MULTILINE)
    missing_info_terms = [
        term for term in _MISSING_INFO_REQUIRED_TERMS if term.lower() not in lowered
    ]
    missing_signal_rows = [
        s for s in missing_signals if f"`{s}`".lower() not in lowered
    ]
    if not has_missing_info_section:
        errors.append(
            "R11 THIẾU mục 'Danh sách thông tin còn thiếu và quyết định cần xác nhận'.")
        checks["R11_missing_information"] = "FAIL (thiếu bảng thiếu sót)"
    elif missing_info_terms:
        errors.append("R11 BẢNG THIẾU SÓT thiếu cột/thuật ngữ bắt buộc: "
                      + ", ".join(missing_info_terms))
        checks["R11_missing_information"] = (
            f"FAIL (thiếu {len(missing_info_terms)} thuật ngữ)")
    elif missing_signal_rows:
        errors.append(
            "R11 BẢNG THIẾU SÓT chưa liệt kê tín hiệu đời thực còn thiếu: "
            + ", ".join(missing_signal_rows))
        checks["R11_missing_information"] = (
            f"FAIL (thiếu {len(missing_signal_rows)} tín hiệu)")
    else:
        checks["R11_missing_information"] = (
            "PASS (thiếu sót/cổng chờ được liệt kê với ảnh hưởng và phương án an toàn)")

    # R12 — tài liệu chính phải có audit trail phiên bản/ngày/thay đổi.
    has_document_control_section = re.search(
        r"^#\s*Kiểm soát phiên bản và lịch sử thay đổi\b",
        text, re.MULTILINE)
    missing_document_terms = [
        term for term in _DOCUMENT_CONTROL_REQUIRED_TERMS if term.lower() not in lowered
    ]
    if not has_document_control_section:
        errors.append(
            "R12 THIẾU mục 'Kiểm soát phiên bản và lịch sử thay đổi'.")
        checks["R12_document_control"] = "FAIL (thiếu audit trail phiên bản)"
    elif missing_document_terms:
        errors.append("R12 KIỂM SOÁT PHIÊN BẢN thiếu thuật ngữ bắt buộc: "
                      + ", ".join(missing_document_terms))
        checks["R12_document_control"] = (
            f"FAIL (thiếu {len(missing_document_terms)} thuật ngữ)")
    else:
        checks["R12_document_control"] = (
            "PASS (phiên bản/ngày/nguồn thay đổi/người duyệt/nhật ký hiện rõ)")

    # R13 — đồng bộ mục tiêu -> biến/công cụ -> phân tích -> bảng/hình -> kết luận.
    has_traceability_section = re.search(
        r"^#\s*Ma trận truy xuất mục tiêu-biến-công cụ-phân tích-bảng\b",
        text, re.MULTILINE)
    traceability_text = ""
    if has_traceability_section:
        after_heading = text[has_traceability_section.end():]
        next_section = re.search(r"^#\s+", after_heading, re.MULTILINE)
        traceability_text = (
            after_heading[:next_section.start()] if next_section else after_heading
        )
    traceability_header = ""
    if traceability_text:
        header_match = re.search(
            r"^\|\s*Mục tiêu/câu hỏi\s*\|.*$",
            traceability_text,
            re.MULTILINE,
        )
        traceability_header = header_match.group(0) if header_match else ""
    traceability_header_lowered = traceability_header.lower()
    missing_traceability_terms = [
        term for term in _TRACEABILITY_REQUIRED_TERMS
        if term.lower() not in traceability_header_lowered
    ]
    if not has_traceability_section:
        errors.append(
            "R13 THIẾU mục 'Ma trận truy xuất mục tiêu-biến-công cụ-phân tích-bảng'.")
        checks["R13_traceability_matrix"] = "FAIL (thiếu ma trận truy xuất)"
    elif missing_traceability_terms:
        errors.append("R13 MA TRẬN TRUY XUẤT thiếu thuật ngữ bắt buộc: "
                      + ", ".join(missing_traceability_terms))
        checks["R13_traceability_matrix"] = (
            f"FAIL (thiếu {len(missing_traceability_terms)} thuật ngữ)")
    else:
        checks["R13_traceability_matrix"] = (
            "PASS (mục tiêu-biến-công cụ-phân tích-bảng được nối trong một ma trận)")

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
