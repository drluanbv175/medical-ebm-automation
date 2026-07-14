#!/usr/bin/env python3
"""
run_pipeline_integrated.py — INTEGRATION LAYER
Nối hệ thống Pipeline G0-G9 với Template 16-Mục (skill nghien-cuu-y-khoa-chuan-quoc-te)

MỤC ĐÍCH:
  Đọc tất cả artifacts G0-G9 của một nghiên cứu đã chạy pipeline,
  trích xuất nội dung từng cổng và tổng hợp thành đề cương chuẩn 16-mục
  theo mẫu templates/01_mau_de_cuong_tong_the.md của skill.

ÁNH XẠ G0-G9 → 16 MỤC:
  G0 (A1: PICO+FINER+Evidence) → Mục 1 (Tóm tắt), 2 (Đặt vấn đề), 3 (Câu hỏi), 4 (Mục tiêu), 16 (TLTK)
  G1 (A2: Protocol Design)     → Mục 5 (Thiết kế), 7 (Biến số và kết cục)
  G2 (A3: Ethics Package)      → Mục 13 (Đạo đức)
  G3 (A4: Sample Size+CRF)     → Mục 6 (Đối tượng), 8 (Cỡ mẫu)
  G4 (A5: SAP Final)           → Mục 11 (Kế hoạch phân tích)
  G5 (A6: Data Management)     → Mục 9 (Công cụ thu thập), 10 (Quản trị dữ liệu), 12 (Sai lệch)
  G6 (A7: Analysis Scripts)    → Mục 11 (bổ sung SAP)
  G7 (A8: Manuscript)          → Mục 1 (Tóm tắt - trích abstract)
  G8 (A9: Pre-submission)      → Mục 14 (Kế hoạch phổ biến)
  G9 (A10: Author Integrity)   → Mục 14 (phần khai báo tác giả + AI)

GUARDRAILS (R1-R7 từ pipeline gốc):
  R1 — KHÔNG bịa PMID/DOI; chỉ dùng PMIDs đã xác minh từ G0
  R2 — KHÔNG bịa số liệu kết quả
  R3 — KHÔNG lưu PII bệnh nhân
  R4 — [CẦN BÁC SĨ XÁC NHẬN] đánh dấu nội dung cần bác sĩ kiểm tra
  R5 — Luôn ghi nguồn checkpoint (G0-G9)
  R6 — Không tự gán mức GRADE; chỉ dùng mức từ nguồn
  R7 — Cần bác sĩ ký trước khi dùng chính thức

SỬ DỤNG:
    python tools/run_pipeline_integrated.py --study "KKB-HAI-LONG-2026"
    python tools/run_pipeline_integrated.py --study "SGLT2-HFpEF-2026" --output-dir custom/path

YÊU CẦU: Đã chạy ít nhất G0 (G0_checkpoint.json phải tồn tại)
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

# Thư mục gốc
BASE = Path(__file__).resolve().parent.parent
EXPORTS_DIR = BASE / "exports"
SKILL_TEMPLATES_DIR = Path("/var/folders/t_/nspjmxbs4gdb3yw_gwqk533h0000gn/T/claude-hostloop-plugins/1289901ffda7d3a9/skills/nghien-cuu-y-khoa-chuan-quoc-te/templates")


# ════════════════════════════════════════════════════════════════════════════
# 1. ĐỌC CHECKPOINTS VÀ ARTIFACTS
# ════════════════════════════════════════════════════════════════════════════

def load_checkpoint(study_dir: Path, gate: str) -> dict:
    """Đọc G{n}_checkpoint.json. Trả về {} nếu không có."""
    cp_file = study_dir / f"{gate}_checkpoint.json"
    if cp_file.exists():
        try:
            return json.loads(cp_file.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def load_artifact_md(study_dir: Path, gate: str, artifact_code: str) -> str:
    """Đọc artifact .md chính của mỗi gate (ví dụ G0_A1_*.md)."""
    pattern = f"{gate}_{artifact_code}_*.md"
    matches = sorted(study_dir.glob(pattern))
    if matches:
        return matches[0].read_text(encoding="utf-8")
    # Fallback: đọc file md đầu tiên của gate này
    fallback = sorted(study_dir.glob(f"{gate}_*.md"))
    if fallback:
        return fallback[0].read_text(encoding="utf-8")
    return ""


def extract_section(text: str, section_header: str, next_headers: list[str] = None) -> str:
    """Trích xuất một đoạn từ text dựa trên header section."""
    if not text or section_header not in text:
        return ""
    start = text.find(section_header)
    if start == -1:
        return ""
    start += len(section_header)
    end = len(text)
    if next_headers:
        for h in next_headers:
            idx = text.find(h, start)
            if idx != -1 and idx < end:
                end = idx
    return text[start:end].strip()


# ════════════════════════════════════════════════════════════════════════════
# 2. TRÍCH XUẤT TỪNG MỤC TỪ G-GATES
# ════════════════════════════════════════════════════════════════════════════

def extract_g0_content(study_dir: Path) -> dict:
    """G0: PICO + Evidence → Mục 1 (Tóm tắt), 2 (Đặt vấn đề), 3, 4, 16."""
    cp = load_checkpoint(study_dir, "G0")
    md = load_artifact_md(study_dir, "G0", "A1")

    study_name = cp.get("study", "")
    topic = cp.get("topic", "")
    pico = cp.get("pico", {})
    evidence = cp.get("evidence_summary", {})
    pmids = cp.get("pmids_verified", [])
    design_code = cp.get("design_code", "")
    question_type = cp.get("question_type", "")

    # Xây dựng nội dung Mục 3 (Câu hỏi nghiên cứu)
    population = pico.get("P", "[CẦN BÁC SĨ BỔ SUNG: Quần thể nghiên cứu]")
    intervention = pico.get("I", "[CẦN BÁC SĨ BỔ SUNG: Can thiệp/phơi nhiễm]")
    comparator = pico.get("C", "[CẦN BÁC SĨ BỔ SUNG: So sánh]")
    outcome = pico.get("O", "[CẦN BÁC SĨ BỔ SUNG: Kết cục]")

    n_pmids = len(pmids)
    evidence_note = (
        f"Hệ thống tự động tìm được {n_pmids} bài báo PubMed có PMID thật "
        f"liên quan đến chủ đề (đã xác minh, không bịa)."
        if n_pmids > 0 else
        "[CẦN tra cứu y văn — G0 chưa chạy hoặc không tìm được bài báo]"
    )

    return {
        "study_name": study_name,
        "topic": topic,
        "pico": {"P": population, "I": intervention, "C": comparator, "O": outcome},
        "design_code": design_code,
        "question_type": question_type,
        "evidence_summary": evidence,
        "evidence_note": evidence_note,
        "pmids_verified": pmids,
        "n_pmids": n_pmids,
        "raw_md": md,
        "gate_present": bool(cp),
    }


def extract_g1_content(study_dir: Path) -> dict:
    """G1: Thiết kế + SAP skeleton → Mục 5 (Thiết kế), 7 (Biến số)."""
    cp = load_checkpoint(study_dir, "G1")
    md = load_artifact_md(study_dir, "G1", "A2")
    design_selected = cp.get("design_selected", "")
    reporting_standard = cp.get("reporting_standard", "")
    bias_table = cp.get("bias_control", [])
    return {
        "design_selected": design_selected or "[CẦN BÁC SĨ XÁC NHẬN thiết kế nghiên cứu]",
        "reporting_standard": reporting_standard or "[CẦN xác định chuẩn báo cáo]",
        "bias_table": bias_table,
        "raw_md": md,
        "gate_present": bool(cp),
    }


def extract_g2_content(study_dir: Path) -> dict:
    """G2: Ethics Package → Mục 13 (Đạo đức)."""
    cp = load_checkpoint(study_dir, "G2")
    md = load_artifact_md(study_dir, "G2", "A3")
    ethics_board = cp.get("ethics_board", "[CẦN ẤN ĐỊNH: Hội đồng Đạo đức]")
    approval_number = cp.get("approval_number", "[CẦN BỔ SUNG khi được cấp]")
    risk_level = cp.get("risk_level", "nguy cơ tối thiểu")
    return {
        "ethics_board": ethics_board,
        "approval_number": approval_number,
        "risk_level": risk_level,
        "raw_md": md,
        "gate_present": bool(cp),
    }


def extract_g3_content(study_dir: Path) -> dict:
    """G3: Sample Size + CRF → Mục 6 (Đối tượng), 8 (Cỡ mẫu)."""
    cp = load_checkpoint(study_dir, "G3")
    md = load_artifact_md(study_dir, "G3", "A4")
    n_calculated = cp.get("n_calculated", 0)
    n_adjusted = cp.get("n_adjusted", 0)
    formula = cp.get("formula", "Wilson / công thức ước lượng tỷ lệ")
    alpha = cp.get("alpha", 0.05)
    power = cp.get("power", 0.80)
    p_estimate = cp.get("p_estimate", 0.50)
    margin = cp.get("margin_of_error", 0.05)
    dropout_rate = cp.get("dropout_rate", 0.10)
    inclusion_criteria = cp.get("inclusion_criteria", [])
    exclusion_criteria = cp.get("exclusion_criteria", [])
    return {
        "n_calculated": n_calculated or "[CẦN tính lại từ G3]",
        "n_adjusted": n_adjusted or "[CẦN tính lại từ G3]",
        "formula": formula,
        "alpha": alpha,
        "power": power,
        "p_estimate": p_estimate,
        "margin": margin,
        "dropout_rate": dropout_rate,
        "inclusion_criteria": inclusion_criteria,
        "exclusion_criteria": exclusion_criteria,
        "raw_md": md,
        "gate_present": bool(cp),
    }


def extract_g4_content(study_dir: Path) -> dict:
    """G4: SAP Final → Mục 11 (Kế hoạch phân tích)."""
    cp = load_checkpoint(study_dir, "G4")
    md = load_artifact_md(study_dir, "G4", "A5")
    sap_locked = cp.get("sap_locked", False)
    primary_analysis = cp.get("primary_analysis", "")
    secondary_analysis = cp.get("secondary_analysis", "")
    software = cp.get("statistical_software", "[CẦN BÁC SĨ CHỈ ĐỊNH phần mềm thống kê]")
    return {
        "sap_locked": sap_locked,
        "primary_analysis": primary_analysis or "[CẦN điền từ SAP G4]",
        "secondary_analysis": secondary_analysis or "[CẦN điền từ SAP G4]",
        "software": software,
        "raw_md": md,
        "gate_present": bool(cp),
    }


def extract_g5_content(study_dir: Path) -> dict:
    """G5: Data Management → Mục 9, 10, 12."""
    cp = load_checkpoint(study_dir, "G5")
    md = load_artifact_md(study_dir, "G5", "A6")
    redcap_dict_exists = (study_dir / f"G5_REDCap_dictionary_{cp.get('study', '')}.csv").exists()
    data_platform = cp.get("data_platform", "REDCap hoặc Excel được bảo mật")
    return {
        "data_platform": data_platform,
        "redcap_dict_exists": redcap_dict_exists,
        "raw_md": md,
        "gate_present": bool(cp),
    }


def extract_g7_content(study_dir: Path) -> dict:
    """G7: Manuscript → Trích abstract cho Mục 1 (Tóm tắt)."""
    cp = load_checkpoint(study_dir, "G7")
    md = load_artifact_md(study_dir, "G7", "A8")
    # Thử trích phần abstract từ bản thảo
    abstract = extract_section(md, "## Abstract", ["## Introduction", "# Introduction", "# CHƯƠNG"])
    if not abstract:
        abstract = extract_section(md, "## Tóm tắt", ["## Đặt vấn đề", "# CHƯƠNG"])
    return {
        "abstract": abstract or "",
        "gate_present": bool(cp),
    }


def extract_g8_content(study_dir: Path) -> dict:
    """G8: Pre-submission → Mục 14 (Kế hoạch phổ biến)."""
    cp = load_checkpoint(study_dir, "G8")
    md = load_artifact_md(study_dir, "G8", "A9")
    target_journal = cp.get("target_journal", "[CẦN BÁC SĨ ẤN ĐỊNH tạp chí mục tiêu]")
    reporting_checklist = cp.get("reporting_checklist", "")
    return {
        "target_journal": target_journal,
        "reporting_checklist": reporting_checklist,
        "raw_md": md,
        "gate_present": bool(cp),
    }


def extract_g9_content(study_dir: Path) -> dict:
    """G9: Author Integrity → Mục 14 (khai báo tác giả + AI)."""
    cp = load_checkpoint(study_dir, "G9")
    md = load_artifact_md(study_dir, "G9", "A10")
    authors = cp.get("authors", [])
    ai_disclosure = cp.get("ai_disclosure", "")
    coi = cp.get("conflict_of_interest", "Không có xung đột lợi ích [CẦN XÁC NHẬN]")
    return {
        "authors": authors,
        "ai_disclosure": ai_disclosure or "Đề cương và bản thảo có sử dụng hỗ trợ AI (EBM Copilot). "
                                          "Khai báo theo quy định ICMJE và tạp chí tiếp nhận khi nộp bài.",
        "conflict_of_interest": coi,
        "gate_present": bool(cp),
    }


# ════════════════════════════════════════════════════════════════════════════
# 3. TỔ HỢP 16 MỤC
# ════════════════════════════════════════════════════════════════════════════

def assemble_16_section_proposal(study_id: str, study_dir: Path) -> str:
    """Tổng hợp nội dung G0-G9 thành đề cương 16-mục chuẩn."""

    # Đọc tất cả gates
    g0 = extract_g0_content(study_dir)
    g1 = extract_g1_content(study_dir)
    g2 = extract_g2_content(study_dir)
    g3 = extract_g3_content(study_dir)
    g4 = extract_g4_content(study_dir)
    g5 = extract_g5_content(study_dir)
    g7 = extract_g7_content(study_dir)
    g8 = extract_g8_content(study_dir)
    g9 = extract_g9_content(study_dir)

    # Xác định gates đã chạy
    gates_done = []
    for gn, gdata in [("G0", g0), ("G1", g1), ("G2", g2), ("G3", g3),
                       ("G4", g4), ("G5", g5), ("G7", g7), ("G8", g8), ("G9", g9)]:
        if gdata.get("gate_present"):
            gates_done.append(gn)

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    completeness = f"{len(gates_done)}/10 gates ({', '.join(gates_done) if gates_done else 'chưa có'})"

    # PMIDs cho phần tài liệu tham khảo
    pmids = g0.get("pmids_verified", [])
    tltk_section = ""
    if pmids:
        tltk_section = "\n".join(
            f"{i+1}. PMID:{pid} — [CẦN BÁC SĨ điền đầy đủ thông tin Vancouver từ PubMed]"
            for i, pid in enumerate(pmids[:20])
        )
    else:
        tltk_section = "[CẦN BÁC SĨ BỔ SUNG tài liệu tham khảo — G0 chưa có PMID xác minh]"

    # Tóm tắt: ưu tiên abstract từ G7, fallback từ G0
    abstract_text = g7.get("abstract", "")
    if not abstract_text:
        abstract_text = (
            f"**[DỰ THẢO — cần cập nhật sau khi có kết quả]**\n\n"
            f"Chủ đề: {g0.get('topic', '[CẦN ẤN ĐỊNH]')}\n"
            f"Thiết kế: {g1.get('design_selected', '[CẦN ẤN ĐỊNH]')}\n"
            f"Cỡ mẫu: N = {g3.get('n_adjusted', '[CẦN tính]')}\n"
            f"Chuẩn báo cáo: {g1.get('reporting_standard', '[CẦN ẤN ĐỊNH]')}"
        )

    # SAP note
    sap_note = ""
    if g4.get("sap_locked"):
        sap_note = "*(SAP đã được khóa tại G4 trước khi thu thập số liệu — đảm bảo liêm chính phân tích)*"
    else:
        sap_note = "*[CẦN: SAP phải được khóa (G4) TRƯỚC khi thu thập dữ liệu — R5 guardrail]*"

    # Biên soạn toàn bộ đề cương
    doc = f"""# ĐỀ CƯƠNG NGHIÊN CỨU — 16 MỤC CHUẨN
## {study_id}

> **Tài liệu này được tạo tự động bởi run_pipeline_integrated.py**
> Ngày tạo: {now} | Gates đã hoàn thành: {completeness}
> **Nguồn:** Artifacts G0-G9 từ pipeline nghiên cứu EBM Copilot
> **QUAN TRỌNG:** Tất cả mục đánh dấu [CẦN...] phải được bác sĩ xác nhận/bổ sung.
> Không sử dụng chính thức khi chưa có chữ ký xác nhận của Chủ nhiệm đề tài.

---

## Thông tin kiểm soát
- **Tên đề tài:** {g0.get("topic", "[CẦN ẤN ĐỊNH]")}
- **Mã đề tài:** {study_id}
- **Chủ nhiệm:** [CẦN ẤN ĐỊNH]
- **Đơn vị:** [CẦN ẤN ĐỊNH]
- **Phiên bản/ngày:** {now} (tự động tổng hợp từ pipeline)
- **Trạng thái:** [DỰ THẢO] — Cần bác sĩ xét duyệt

---

## 1. Tóm tắt
*(Nguồn: G7 manuscript abstract + G0 PICO)*

{abstract_text}

---

## 2. Đặt vấn đề
*(Nguồn: G0 — evidence landscape từ {g0.get("n_pmids", 0)} PMIDs đã xác minh)*

{g0.get("evidence_note", "[CẦN BÁC SĨ BỔ SUNG]")}

[CẦN BÁC SĨ BỔ SUNG: Bối cảnh địa phương, khoảng trống nghiên cứu, lý do triển khai tại đơn vị]

---

## 3. Câu hỏi nghiên cứu và giả thuyết
*(Nguồn: G0 PICO)*

**Khung PICO:**
- **P (Population):** {g0["pico"]["P"]}
- **I (Intervention/Exposure):** {g0["pico"]["I"]}
- **C (Comparator):** {g0["pico"]["C"]}
- **O (Outcome):** {g0["pico"]["O"]}

**Câu hỏi nghiên cứu:** [CẦN BÁC SĨ DIỄN ĐẠT lại thành câu hỏi hoàn chỉnh từ PICO trên]

**Giả thuyết nghiên cứu:** [CẦN BÁC SĨ ẤN ĐỊNH — H0 và H1]

---

## 4. Mục tiêu
*(Nguồn: G0)*

### 4.1. Mục tiêu chung
[CẦN BÁC SĨ DIỄN ĐẠT — thường là 1 câu bao quát toàn bộ nghiên cứu]

### 4.2. Mục tiêu cụ thể
[CẦN BÁC SĨ ẤN ĐỊNH — thường 2-3 mục tiêu cụ thể, có thể đo lường được, tương ứng với từng câu hỏi nghiên cứu]

---

## 5. Thiết kế và bối cảnh
*(Nguồn: G1 Protocol Design)*

**Thiết kế nghiên cứu:** {g1.get("design_selected", "[CẦN BÁC SĨ XÁC NHẬN]")}

**Chuẩn báo cáo:** {g1.get("reporting_standard", "[CẦN xác định]")}

**Địa điểm nghiên cứu:** [CẦN BÁC SĨ BỔ SUNG — mô tả địa bàn]

**Thời gian nghiên cứu:** [CẦN BÁC SĨ ẤN ĐỊNH — bao gồm thời gian thu thập số liệu]

---

## 6. Đối tượng nghiên cứu
*(Nguồn: G3 Sample Size + CRF)*

### 6.1. Tiêu chuẩn chọn
"""

    # Tiêu chuẩn chọn từ G3
    if g3.get("inclusion_criteria"):
        for c in g3["inclusion_criteria"]:
            doc += f"- {c}\n"
    else:
        doc += "- [CẦN BÁC SĨ ẤN ĐỊNH tiêu chuẩn lựa chọn]\n"

    doc += "\n### 6.2. Tiêu chuẩn loại\n"
    if g3.get("exclusion_criteria"):
        for c in g3["exclusion_criteria"]:
            doc += f"- {c}\n"
    else:
        doc += "- [CẦN BÁC SĨ ẤN ĐỊNH tiêu chuẩn loại trừ]\n"

    doc += f"""
### 6.3. Tuyển mẫu
[CẦN BÁC SĨ ẤN ĐỊNH phương pháp chọn mẫu — xem gợi ý tại mục 8 bên dưới]

---

## 7. Biến số và kết cục
*(Nguồn: G1 — design + variables; G3 — CRF)*

**Biến kết cục chính (primary outcome):** [CẦN BÁC SĨ XÁC NHẬN từ kết cục O trong PICO]

**Biến kết cục phụ (secondary outcomes):** [CẦN BÁC SĨ ẤN ĐỊNH]

**Biến độc lập / biến nền:** [CẦN BÁC SĨ liệt kê — tham chiếu G3 CRF]

> *REDCap dictionary: {"Có (G5_REDCap_dictionary.csv)" if g5.get("redcap_dict_exists") else "Chưa có hoặc G5 chưa chạy"}*

---

## 8. Cỡ mẫu
*(Nguồn: G3 — tính toán trực tiếp bằng script, không suy diễn)*

**Công thức:** {g3.get("formula", "Wilson / ước lượng tỷ lệ")}
- α = {g3.get("alpha", "0.05")} (độ tin cậy 95%)
- Power = {g3.get("power", "0.80")} [{g3.get("power", "0.80") if g4.get("gate_present") else "xem lại G1/G4"}]
- p ước tính = {g3.get("p_estimate", "[CẦN ẤN ĐỊNH]")}
- Sai số biên e = {g3.get("margin", "[CẦN ẤN ĐỊNH]")}
- Tỷ lệ bỏ cuộc = {int(g3.get("dropout_rate", 0.10) * 100)}%

**Cỡ mẫu tối thiểu (n):** {g3.get("n_calculated", "[CẦN tính lại từ G3]")}
**Cỡ mẫu có điều chỉnh (N):** {g3.get("n_adjusted", "[CẦN tính lại từ G3]")}

**Phương pháp chọn mẫu:** [CẦN BÁC SĨ ẤN ĐỊNH]

---

## 9. Công cụ và quy trình thu thập
*(Nguồn: G5 Data Management)*

**Nền tảng thu thập dữ liệu:** {g5.get("data_platform", "REDCap hoặc Excel bảo mật [CẦN xác nhận]")}

**Công cụ đo lường chính:** [CẦN BÁC SĨ CHỈ ĐỊNH — bộ câu hỏi/thang đo đã kiểm định]

**Quy trình thu thập:** [CẦN BÁC SĨ mô tả — tham chiếu SOP tại G5a]

**Tập huấn điều tra viên:** [CẦN BÁC SĨ ẤN ĐỊNH — thời gian, nội dung]

---

## 10. Quản trị dữ liệu và bảo mật
*(Nguồn: G5 Data Management Plan)*

- Dữ liệu được lưu trữ tại: {g5.get("data_platform", "[CẦN ẤN ĐỊNH]")}
- Quyền truy cập hạn chế theo phân quyền [CẦN ẤN ĐỊNH]
- Dữ liệu định danh (PII) tách biệt khỏi dữ liệu nghiên cứu
- Thời gian lưu trữ: tối thiểu 5 năm sau khi công bố [theo quy định BV 175]
- Không sử dụng AI xử lý dữ liệu có PII (R3 guardrail)

> *Kế hoạch quản lý dữ liệu chi tiết: xem G5b_DMP và G5c_DATALOCK*

---

## 11. Kế hoạch phân tích thống kê
*(Nguồn: G4 SAP Final + G6 Analysis Scripts)*
{sap_note}

**Phần mềm thống kê:** {g4.get("software", "[CẦN BÁC SĨ CHỈ ĐỊNH — SPSS/Stata/R + phiên bản]")}

**Phân tích mô tả:**
- Biến định lượng: TB ± ĐLC hoặc Median [IQR] tùy phân phối (kiểm định Kolmogorov-Smirnov)
- Biến định tính: tần số, tỷ lệ %, KTC 95%

**Phân tích chính (Primary analysis):**
{g4.get("primary_analysis", "[CẦN BÁC SĨ xác nhận từ SAP G4]")}

**Phân tích phụ (Secondary analysis):**
{g4.get("secondary_analysis", "[CẦN BÁC SĨ xác nhận từ SAP G4]")}

**Ngưỡng ý nghĩa thống kê:** p < 0,05 (hai phía)

> *Script phân tích: xem G6_A7 và scripts/ trong thư mục nghiên cứu*

---

## 12. Sai lệch và kiểm soát
*(Nguồn: G1 bias table + G5 SOP)*

[CẦN BÁC SĨ XÁC NHẬN — tham chiếu bảng bias control từ G1 và SOP từ G5]

Các loại sai lệch cần lưu ý (theo loại thiết kế {g1.get("design_selected", "")}):
- Sai lệch lựa chọn (selection bias)
- Sai lệch thông tin (information bias)
- Sai lệch nhớ lại (recall bias) nếu có
- Yếu tố gây nhiễu (confounding) — kiểm soát bằng phân tích đa biến

---

## 13. Đạo đức nghiên cứu
*(Nguồn: G2 Ethics Package)*

**Hội đồng Đạo đức:** {g2.get("ethics_board", "[CẦN ẤN ĐỊNH]")}
**Số phê duyệt:** {g2.get("approval_number", "[CẦN BỔ SUNG khi được cấp — KHÔNG ĐƯỢC bịa số]")}
**Phân loại nguy cơ:** Nghiên cứu {g2.get("risk_level", "nguy cơ tối thiểu")}

- Tham gia hoàn toàn tự nguyện; có quyền rút lui không cần giải thích
- Thu thập phiếu đồng thuận (informed consent) trước khi tham gia
- Dữ liệu ẩn danh, bảo mật, lưu trữ theo quy định
- Không sử dụng PII trong hệ thống AI (R3 guardrail)

> *Hồ sơ đạo đức chi tiết: xem G2_A3 và G2_ETHICS*

---

## 14. Kế hoạch phổ biến kết quả và ứng dụng
*(Nguồn: G8 Pre-submission + G9 Author Integrity)*

**Tạp chí mục tiêu:** {g8.get("target_journal", "[CẦN BÁC SĨ ẤN ĐỊNH]")}

**Khai báo AI:** {g9.get("ai_disclosure", "[CẦN khai báo khi nộp bài]")}

**Xung đột lợi ích:** {g9.get("conflict_of_interest", "[CẦN XÁC NHẬN]")}

**Kế hoạch ứng dụng:**
- Báo cáo kết quả trước ban lãnh đạo đơn vị sau khi có kết quả
- Đề xuất can thiệp cải tiến chất lượng dựa trên kết quả nghiên cứu
- Theo dõi hiệu quả can thiệp sau 12–18 tháng (nếu phù hợp)

---

## 15. Tiến độ và nguồn lực

**Tổng thời gian ước tính:** 10–12 tháng kể từ khi được phê duyệt đạo đức

| Giai đoạn | Nội dung | Thời gian | Phụ trách |
|---|---|---|---|
| 1. Chuẩn bị | Hoàn thiện đề cương, bộ công cụ, phiếu ICF | [CẦN ẤN ĐỊNH] | Chủ nhiệm |
| 2. Đạo đức | Nộp hồ sơ, xin phê duyệt | [CẦN ẤN ĐỊNH] | Chủ nhiệm |
| 3. Pilot test | Thử nghiệm bộ công cụ ~20 đối tượng | [CẦN ẤN ĐỊNH] | Nhóm NC |
| 4. Thu thập | Thu thập N = {g3.get("n_adjusted", "?")} đối tượng | [CẦN ẤN ĐỊNH] | Điều tra viên |
| 5. Làm sạch & phân tích | Nhập liệu, làm sạch, phân tích | [CẦN ẤN ĐỊNH] | Nhóm NC |
| 6. Viết báo cáo | Soạn bản thảo toàn văn | [CẦN ẤN ĐỊNH] | Chủ nhiệm |
| 7. Nghiệm thu | Báo cáo Hội đồng, nộp bài | [CẦN ẤN ĐỊNH] | Chủ nhiệm |

**Nhân lực:** [CẦN ẤN ĐỊNH — danh sách nghiên cứu viên, điều tra viên, cố vấn thống kê]

**Kinh phí:** [CẦN ẤN ĐỊNH — nguồn và khái toán theo quy định đơn vị]

---

## 16. Tài liệu tham khảo Vancouver/NLM
*(Nguồn: G0 — {g0.get("n_pmids", 0)} PMIDs đã xác minh thật)*

{tltk_section}

[CẦN BÁC SĨ bổ sung tài liệu tham khảo tiếng Việt — hệ thống chỉ tra được PubMed quốc tế]

---

## Phụ lục
- **PLuc A — Ma trận mục tiêu – biến – phân tích – bảng:** [xem chi tiết bên dưới]
- **PLuc B — CRF / Phiếu khảo sát:** xem G3c_CRF và G5_REDCap_dictionary
- **PLuc C — Phiếu đồng thuận (ICF):** xem G2_A3 Ethics Package
- **PLuc D — Data dictionary:** xem G5b_DMP
- **PLuc E — SAP (Statistical Analysis Plan):** xem G4_A5_SAP_FINAL
- **PLuc F — Checklist chuẩn báo cáo {g1.get("reporting_standard", "")}:** xem G8_A9

### Ma trận mục tiêu – biến – phân tích – bảng

| Mục tiêu | Biến số chính | Loại biến | Phân tích | Bảng kết quả | Nguồn Gate |
|---|---|---|---|---|---|
| Mô tả mẫu | Đặc điểm nền | Định tính/lượng | Tần số, TB ± ĐLC | Bảng 3.1 | G3 |
| MT1: Kết cục chính | {g0["pico"]["O"][:50] if len(g0["pico"]["O"]) > 0 else "[O từ PICO]"}... | [CẦN ẤN ĐỊNH] | Tần số, KTC 95% | Bảng 3.2 | G0+G4 |
| MT2: Yếu tố liên quan — đơn biến | Biến độc lập (≥ 5) | Định tính/lượng | χ², t-test, Fisher | Bảng 3.3 | G1+G4 |
| MT2: Đa biến | Biến p<0,2 từ đơn biến | Hỗn hợp | Hồi quy logistic/tuyến tính; OR/β hiệu chỉnh | Bảng 3.4 | G4+G6 |

---

## Xác nhận và chữ ký

| Vai trò | Họ tên | Chữ ký | Ngày |
|---|---|---|---|
| Chủ nhiệm đề tài | [CẦN ẤN ĐỊNH] | _________________ | |
| Người hướng dẫn (nếu có) | [CẦN ẤN ĐỊNH] | _________________ | |
| Trưởng khoa/đơn vị | [CẦN ẤN ĐỊNH] | _________________ | |

---

> **DISCLAIMER (R7 guardrail):**
> Tài liệu này được tổng hợp tự động từ pipeline G0-G9 bởi run_pipeline_integrated.py.
> - Các mục đánh dấu [CẦN...] BẮT BUỘC phải được Chủ nhiệm đề tài xác nhận.
> - Số phê duyệt đạo đức KHÔNG ĐƯỢC bịa — chỉ điền khi có quyết định thật.
> - Tài liệu tham khảo: chỉ liệt kê PMIDs đã xác minh từ G0 (không bịa thêm).
> - Không sử dụng làm đề cương chính thức trước khi có chữ ký Chủ nhiệm đề tài.
> Tổng hợp lúc: {now} | Pipeline version: G0-G9 integrated v1.0
"""

    return doc


# ════════════════════════════════════════════════════════════════════════════
# 4. KIỂM TRA TRẠNG THÁI PIPELINE
# ════════════════════════════════════════════════════════════════════════════

def check_pipeline_status(study_dir: Path) -> dict:
    """Kiểm tra xem gate nào đã chạy, gate nào còn thiếu."""
    gates = ["G0", "G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8", "G9"]
    status = {}
    for gate in gates:
        cp_file = study_dir / f"{gate}_checkpoint.json"
        artifacts = list(study_dir.glob(f"{gate}_*.md")) + list(study_dir.glob(f"{gate}_*.docx"))
        status[gate] = {
            "checkpoint": cp_file.exists(),
            "artifact_count": len(artifacts),
            "complete": cp_file.exists() and len(artifacts) > 0,
        }
    done = [g for g, s in status.items() if s["complete"]]
    missing = [g for g, s in status.items() if not s["complete"]]
    return {
        "gates_done": done,
        "gates_missing": missing,
        "completeness_pct": len(done) * 10,
        "detail": status,
    }


# ════════════════════════════════════════════════════════════════════════════
# 5. MAIN
# ════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Nối pipeline G0-G9 với template 16-mục (skill nghien-cuu-y-khoa-chuan-quoc-te)"
    )
    parser.add_argument("--study", required=True, help="Mã đề tài (ví dụ: KKB-HAI-LONG-2026)")
    parser.add_argument("--output-dir", default=None, help="Thư mục xuất (mặc định: exports/<study>/)")
    parser.add_argument("--status-only", action="store_true", help="Chỉ kiểm tra trạng thái pipeline, không tạo file")
    args = parser.parse_args()

    study_id = re.sub(r'[^\w\-]', '_', args.study.strip().replace(" ", "-"))  # 2026-07-11: vá path traversal
    study_dir = EXPORTS_DIR / study_id

    if not study_dir.exists():
        print(f"[LỖI] Không tìm thấy thư mục nghiên cứu: {study_dir}")
        print(f"  Gợi ý: Chạy G0 trước: python tools/run_g0_auto.py --study \"{study_id}\" --topic \"...\"")
        sys.exit(1)

    # Kiểm tra trạng thái
    status = check_pipeline_status(study_dir)
    print(f"\n{'='*60}")
    print(f"PIPELINE STATUS: {study_id}")
    print(f"{'='*60}")
    print(f"Gates hoàn thành: {', '.join(status['gates_done']) or 'Chưa có'}")
    print(f"Gates còn thiếu: {', '.join(status['gates_missing']) or 'Không'}")
    print(f"Mức hoàn thiện:  {status['completeness_pct']}%")

    if args.status_only:
        return

    # G0 là bắt buộc
    if "G0" not in status["gates_done"]:
        print("\n[DỪNG] G0 chưa chạy — G0_checkpoint.json không tồn tại.")
        print(f"  Chạy: python tools/run_g0_auto.py --study \"{study_id}\" --topic \"...\"")
        sys.exit(1)

    # Tổng hợp đề cương 16-mục
    print("\n[Đang tổng hợp đề cương 16-mục từ pipeline G0-G9...]")
    proposal_text = assemble_16_section_proposal(study_id, study_dir)

    # Xác định thư mục xuất
    output_dir = Path(args.output_dir) if args.output_dir else study_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    output_file = output_dir / f"DE_CUONG_16_MUC_TICH_HOP_{study_id}_{timestamp}.md"
    output_file.write_text(proposal_text, encoding="utf-8")

    print("\n[XONG] Đề cương 16-mục đã được tổng hợp:")
    print(f"  → {output_file}")
    print("\nBước tiếp theo:")
    print("  1. Mở file và điền tất cả mục đánh dấu [CẦN...]")
    print("  2. Ký xác nhận trước khi trình Hội đồng Đạo đức")
    print("  3. Sau khi có số phê duyệt đạo đức, điền vào Mục 13")
    print("\n[GUARDRAIL R7] Tài liệu này là DỰ THẢO — cần bác sĩ xét duyệt trước khi dùng chính thức.")


if __name__ == "__main__":
    main()
