#!/usr/bin/env python3
"""
run_g3_auto.py — Cổng G3: Tính cỡ mẫu tự động
Đọc G0+G1 checkpoints → tính cỡ mẫu với công thức thật → A4 .md + .docx + G3_checkpoint.json
"""
import argparse
import json
import math
import re
import sys
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(TOOLS))

import gate_contract as GC  # noqa: E402  (hợp đồng DỪNG dùng chung)

# Hệ số z phổ biến
Z_TABLE = {0.20: 0.842, 0.15: 1.036, 0.10: 1.282, 0.05: 1.645, 0.025: 1.960, 0.01: 2.326, 0.005: 2.576}

def z(p):
    """Tính z-score từ xác suất một phía."""
    try:
        from scipy.stats import norm
        return norm.ppf(1 - p)
    except ImportError:
        return Z_TABLE.get(p, 1.960)

def n_two_proportion(p1, p2, alpha=0.05, power=0.80):
    """Cỡ mẫu so sánh hai tỷ lệ (two-sided)."""
    if not (0 < p1 < 1) or not (0 < p2 < 1):
        raise InvalidEffectSizeError(f"p1, p2 phải trong (0,1), nhận được p1={p1}, p2={p2}")
    if abs(p1 - p2) < 0.001:
        raise InvalidEffectSizeError(
            f"p1={p1} và p2={p2} gần như bằng nhau (không có hiệu quả để phát hiện) — "
            "cần chênh lệch tỷ lệ thực tế khác 0."
        )
    za = z(alpha / 2)
    zb = z(1 - power)
    pooled = (p1 + p2) / 2
    num = (za * math.sqrt(2 * pooled * (1 - pooled)) + zb * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2
    denom = (p1 - p2) ** 2
    return math.ceil(num / denom)

class InvalidEffectSizeError(ValueError):
    """Effect size/tham số nằm ngoài miền công thức có thể tính hợp lệ."""


def n_log_rank(hr, alpha=0.05, power=0.80, p_event=0.30):
    """
    Số biến cố (Schoenfeld) + cỡ mẫu từ tỷ lệ biến cố.
    SỬA: hr=1.0 → log(1)=0 → chia cho 0 → OverflowError khi ép sang int;
    hr âm → log(số âm) → ValueError. Cả hai trước đây làm crash toàn bộ G3
    không ghi lại artifact/checkpoint nào. Nay validate trước, báo lỗi rõ
    ràng thay vì traceback khó hiểu.
    """
    if hr is None or hr <= 0:
        raise InvalidEffectSizeError(f"HR phải dương, nhận được HR={hr}")
    if 0.98 <= hr <= 1.02:
        raise InvalidEffectSizeError(
            f"HR={hr} quá gần 1.0 (không có hiệu quả để phát hiện) — "
            "công thức Schoenfeld cho ra cỡ mẫu vô hạn. Cần effect size thực tế khác 1.0."
        )
    za = z(alpha / 2)
    zb = z(1 - power)
    # SỬA: công thức Schoenfeld (1983) cho phân bổ 1:1 cần hệ số 4
    # (= 1/[ψ(1-ψ)] với ψ=0.5) ở tử số — thiếu hệ số này làm số biến cố
    # (và do đó N) bị đánh giá thấp đúng 4 lần. Kiểm chứng: HR=0.5,
    # alpha=0.05, power=80% → thiếu hệ số 4 cho d≈16 (sai); có hệ số 4
    # cho d≈65 (khớp textbook Machin/Campbell).
    n_events = math.ceil(4 * (za + zb) ** 2 / (math.log(hr)) ** 2)
    if p_event is None or p_event <= 0:
        raise InvalidEffectSizeError(f"Tỷ lệ biến cố (p_event) phải dương, nhận được p_event={p_event}")
    n_total = math.ceil(n_events / p_event)
    return n_total, n_events

def n_prevalence(p, e=0.05, alpha=0.05):
    """Cỡ mẫu ước lượng tỷ lệ (Wilson)."""
    if not (0 < p < 1):
        raise InvalidEffectSizeError(f"Tỷ lệ p phải trong (0,1), nhận được p={p}")
    if not (0 < e < 1):
        raise InvalidEffectSizeError(f"Sai số biên e phải trong (0,1), nhận được e={e}")
    za = z(alpha / 2)
    return math.ceil(za ** 2 * p * (1 - p) / e ** 2)

def n_auc(auc, alpha=0.05, power=0.80):
    """
    Cỡ mẫu kiểm định MỘT AUC so với hằng số null 0.5 (một mẫu, không phải
    so sánh hai AUC độc lập).
    SỬA: công thức cũ nhân thêm hệ số 2 ở tử số — hệ số 2 chỉ đúng khi so
    sánh HAI AUC ước lượng từ hai mẫu độc lập riêng biệt (mỗi mẫu có
    phương sai σ² riêng, Var(AUC1-AUC2)=2σ²/n). Ở đây chỉ có MỘT mẫu/MỘT
    AUC kiểm định so với hằng số 0.5 (không phải biến ngẫu nhiên có
    phương sai riêng), nên không có phép trừ hai đại lượng ngẫu nhiên độc
    lập — hệ số 2 không áp dụng. Suy ra từ power của kiểm định 1 mẫu:
    n = σ²(zα/2+zβ)²/(AUC-0.5)² (không hệ số 2).
    """
    if not (0 < auc < 1):
        raise InvalidEffectSizeError(f"AUC phải trong (0,1), nhận được AUC={auc}")
    if 0.49 <= auc <= 0.51:
        raise InvalidEffectSizeError(
            f"AUC={auc} quá gần 0.5 (test không phân biệt được bệnh/không bệnh) — "
            "cần AUC thực tế khác 0.5."
        )
    za = z(alpha / 2)
    zb = z(1 - power)
    sigma2 = auc * (1 - auc) + (auc - 0.5) ** 2 / 3  # xấp xỉ Hanley-McNeil
    if sigma2 <= 0:
        sigma2 = 0.05
    return math.ceil((za + zb) ** 2 * sigma2 / (auc - 0.5) ** 2)

def extract_best_effect(effect_samples):
    """
    Trích xuất ước lượng hiệu quả tốt nhất từ danh sách G1.
    Trả về (value, type, quality) — quality "labeled" (có 95%CI đi kèm, đáng
    tin) hoặc "crude" (chỉ số % thô không CI, có thể lẫn ARR/RR).
    SỬA: trước đây bỏ qua hoàn toàn trường "quality" mà G1 đã gắn nhãn —
    chọn effect đầu tiên khớp type bất kể lấy từ pattern có nhãn hay thô,
    khiến việc phân biệt labeled/crude ở G1 vô nghĩa với phép tính cỡ mẫu
    thật (G3 mới là nơi con số này được DÙNG, không phải chỉ hiển thị).
    """
    if not effect_samples:
        return None, None, None
    # Ưu tiên: HR/OR/RR loại "labeled" > HR/OR/RR loại "crude" > ARR% "labeled"
    # > ARR% "crude" — luôn ưu tiên quality trước, bất kể thứ tự trong list.
    for want_quality in ("labeled", "crude"):
        for ef in effect_samples:
            if ef.get("type") in ("HR", "OR", "RR") and ef.get("quality", "crude") == want_quality:
                val = ef.get("value")
                if val and 0.3 < float(val) < 3.0:
                    return float(val), ef.get("type"), want_quality
    for want_quality in ("labeled", "crude"):
        for ef in effect_samples:
            if ef.get("type") == "ARR%" and ef.get("quality", "crude") == want_quality:
                # SỬA: .get("value", 0.10) không dùng default khi key tồn
                # tại với giá trị null — bọc "or 0.10" tránh float(None) crash
                # (nhánh HR/OR/RR phía trên đã có "if val" guard, nhánh này
                # thiếu, cùng loại lỗi None-unsafe đã sửa ở nhiều nơi khác).
                val = ef.get("value")
                if val is not None:
                    return float(val), "ARR%", want_quality
    return None, None, None

def sensitivity_table(design_code, base_n, effect_val, effect_type, alpha, p_event=0.30, p0=0.30):
    """Bảng phân tích độ nhạy: power × effect_size → N."""
    powers = [0.70, 0.80, 0.90]
    mults = [0.80, 1.00, 1.20]  # -20%, cơ sở, +20%
    rows = []
    for pwr in powers:
        row = []
        for m in mults:
            ev = effect_val * m
            try:
                # SỬA: nhánh cũ "elif design_code in ('cohort',):" không kiểm
                # effect_type nên bắt luôn cả ARR% của cohort, đẩy giá trị %
                # (vd 11.2) vào n_log_rank() như thể là HR — ra N vô nghĩa
                # (N=4) mà không có cờ [CẦN] hay lỗi nào. Sửa: kiểm effect_type
                # TRƯỚC design_code, đồng bộ với logic thật trong main().
                if effect_type == "ARR%" and design_code in ("rct", "cohort", "case_control"):
                    p1, p2 = p0, p0 - ev / 100
                    if p2 <= 0: p2 = 0.05
                    n = n_two_proportion(p1, p2, alpha, pwr) * 2
                elif design_code == "case_control" and effect_type in ("OR", "RR", "HR"):
                    # SỬA: đồng bộ với main() — case-control dùng two-proportion
                    # trên tỷ lệ phơi nhiễm suy từ OR, KHÔNG dùng log-rank
                    # (không có trục thời gian-đến-biến cố hợp lệ).
                    odds0 = p0 / (1 - p0)
                    odds1 = ev * odds0
                    p1_exposed = odds1 / (1 + odds1)
                    n = n_two_proportion(p1_exposed, p0, alpha, pwr) * 2
                elif effect_type in ("HR",) and design_code in ("cohort", "rct"):
                    ev_hr = ev if ev < 1.0 else 1 / ev
                    n, _ = n_log_rank(ev_hr, alpha, pwr, p_event)
                elif effect_type in ("OR", "RR") and design_code == "cohort":
                    ev_hr = ev if ev < 1.0 else 1 / ev
                    n, _ = n_log_rank(ev_hr, alpha, pwr, p_event)
                else:
                    row.append("N/A")
                    continue
            except Exception:
                row.append("N/A")
                continue
            row.append(n)
        rows.append((pwr, row))
    return rows, mults

def load_checkpoint(path):
    """Đọc checkpoint JSON nếu tồn tại."""
    if Path(path).exists():
        with open(path) as f:
            return json.load(f)
    return {}

def guardrail_check(artifact, n_adjusted, effect_val):
    """Kiểm guardrail R1-R7 cho G3."""
    errors, warnings = [], []
    # R1 — Không bịa PMID
    if re.search(r'PMID:\d{8}(?!\d)', artifact):
        pmids = re.findall(r'PMID:(\d+)', artifact)
        if any(int(p) > 40000000 for p in pmids):
            errors.append("R1 🔴 Có thể có PMID không thật")
        else:
            warnings.append("R1 ✅ PMID nằm trong khoảng hợp lý")
    else:
        warnings.append("R1 ✅ Không có PMID bịa")
    # R2 — Không PII
    if re.search(r'\b(CMND|CCCD|CMT)\s*\d{9,12}', artifact, re.IGNORECASE):
        errors.append("R2 🔴 Phát hiện mẫu PII (CMND/CCCD)")
    else:
        warnings.append("R2 ✅ Không PII")
    # R3 — Không claim approved
    if "APPROVED_EXTERNALLY" in artifact or "G3_STATUS: LOCKED" in artifact:
        errors.append("R3 🔴 Không được tự claim APPROVED/LOCKED")
    else:
        warnings.append("R3 ✅ Không tự claim approved")
    # R4 — Có DRAFT
    draft_count = artifact.count("DRAFT")
    if draft_count < 1:
        errors.append("R4 🔴 Thiếu nhãn DRAFT")
    else:
        warnings.append(f"R4 ✅ Nhãn DRAFT đủ ({draft_count} lần)")
    # R5 — Sensitivity analysis
    if "sensitivity" in artifact.lower() or "độ nhạy" in artifact.lower():
        warnings.append("R5 ✅ Sensitivity analysis gồm nhiều kịch bản")
    else:
        errors.append("R5 🔴 Thiếu sensitivity analysis")
    # R6 — Có [CẦN]
    can_count = len(re.findall(r'\[CẦN', artifact))
    if can_count < 3:
        errors.append(f"R6 🔴 Quá ít trường [CẦN...] ({can_count})")
    else:
        warnings.append(f"R6 ✅ {can_count}+ trường [CẦN...] đã gắn nhãn")
    # R7 — Disclaimer
    if "Cần bác sĩ kiểm chứng" not in artifact:
        errors.append("R7 🔴 Thiếu disclaimer")
    else:
        warnings.append("R7 ✅ Có disclaimer")
    # R8 — Không âm thầm báo N=0 như thể đã tính xong (SỬA: trước đây tổ hợp
    # design/effect chưa có công thức bị fabricate N=100/200 và vẫn PASS lặng
    # lẽ; nay N=0 hợp lệ nhưng PHẢI hiện rõ để bác sĩ biết cần tính thủ công)
    if effect_val and n_adjusted == 0:
        warnings.append("R8 ⚠️ N=0 — công thức tự động chưa hỗ trợ tổ hợp design/effect này, "
                         "cần bác sĩ/thống kê viên tính thủ công (xem formula_used)")
    return errors, warnings

def generate_artifact(study, topic, design_code, design_primary, alpha, power, effect_val, effect_type,
                      n_per_group, n_total, n_adjusted, dropout, formula_used, sens_rows, sens_mults,
                      p_event, run_date):
    """Sinh A4 — Kế hoạch cỡ mẫu."""
    study_safe = study.replace(" ", "-")
    lines = [
        f"# A4 — KẾ HOẠCH CỠ MẪU (DRAFT)",
        f"**Đề tài:** {topic}  ",
        f"**Mã:** {study_safe} | **Ngày sinh:** {run_date} | **Trạng thái:** DRAFT — CHỜ BÁC SĨ XÁC NHẬN",
        "",
        "---",
        "",
        "## PHẦN 1 — THÔNG SỐ ĐẦU VÀO",
        "",
        f"| Thông số | Giá trị | Nguồn |",
        f"|---|---|---|",
        f"| Mức ý nghĩa (α) | {alpha} (two-sided) | Quy ước |",
        f"| Lực thống kê (1−β) | {int(power*100)}% | Quy ước |",
        f"| Tỷ lệ bỏ cuộc dự kiến | {int(dropout*100)}% | [CẦN BÁC SĨ XÁC NHẬN] |",
    ]
    if effect_val:
        lines += [
            f"| Effect size ước lượng | {effect_type} = {effect_val:.2f} | Trích từ y văn G0 |",
            f"| Loại hiệu quả | {effect_type} | G1 checkpoint |",
        ]
        if design_code in ("cohort", "rct") and effect_type == "HR":
            lines.append(f"| Tỷ lệ biến cố nền | {p_event*100:.0f}% | [CẦN XÁC NHẬN — từ y văn/pilot] |")
    else:
        lines += [
            "| Effect size | **[CẦN BÁC SĨ ẤN ĐỊNH]** | Không tìm được từ G0 |",
            "| Gợi ý: dùng MCID của kết cục chính | — | [CẦN PMID/DOI hỗ trợ] |",
        ]
    lines += [
        "",
        f"> **Thiết kế:** {design_primary}  ",
        f"> **Công thức:** {formula_used}",
        "",
        "---",
        "",
        "## PHẦN 2 — KẾT QUẢ TÍNH TOÁN",
        "",
    ]
    if effect_val:
        lines += [
            f"| Chỉ số | Kết quả |",
            f"|---|---|",
            f"| N mỗi nhóm | **{n_per_group}** |",
            f"| N tổng (không dropout) | **{n_total}** |",
            f"| N điều chỉnh (dropout {int(dropout*100)}%) | **{n_adjusted}** |",
            "",
            f"**KẾT LUẬN:** Nghiên cứu cần tuyển **{n_adjusted} người tham gia** (chia đều {n_per_group} mỗi nhóm).",
        ]
    else:
        lines += [
            "**⚠ Chưa tính được** — bác sĩ cần cung cấp effect size.",
            "",
            "| Chỉ số | Kết quả |",
            "|---|---|",
            "| N mỗi nhóm | **[CẦN EFFECT SIZE]** |",
            "| N tổng | **[CẦN EFFECT SIZE]** |",
            "| N điều chỉnh | **[CẦN EFFECT SIZE]** |",
        ]
    lines += [
        "",
        "---",
        "",
        "## PHẦN 3 — PHÂN TÍCH ĐỘ NHẠY (Sensitivity Analysis)",
        "",
        f"Bảng: Power × Effect size → N tổng (điều chỉnh {int(dropout*100)}% dropout)",
        "",
        f"| Power | ES × {sens_mults[0]} ({int(sens_mults[0]*100)}%) | ES × {sens_mults[1]} (cơ sở) | ES × {sens_mults[2]} ({int(sens_mults[2]*100)}%) |",
        "|---|---|---|---|",
    ]
    for pwr, row in sens_rows:
        r = [str(v) if v != "N/A" else "N/A" for v in row]
        lines.append(f"| {int(pwr*100)}% | {r[0]} | {r[1]} | {r[2]} |")
    lines += [
        "",
        "> *Lưu ý: Nếu bác sĩ điều chỉnh effect size, cỡ mẫu thay đổi theo bảng trên.*",
        "",
        "---",
        "",
        "## PHẦN 4 — KHỐI CỠ MẪU (dán vào đề cương)",
        "",
        "```",
        f"Cỡ mẫu được tính theo {formula_used}.",
        f"Với mức ý nghĩa hai phía α = {alpha}, lực thống kê 1−β = {int(power*100)}%,",
    ]
    if effect_val:
        # SỬA: dòng "{effect_type} = {effect_val} (lấy từ y văn [CẦN PMID/DOI])"
        # đúng cho cohort/case_control/RCT (effect_val THẬT LÀ effect size
        # trích từ 1 bài báo cụ thể) nhưng SAI ngữ cảnh cho cross_sectional
        # (effect_val ở đó là TỶ LỆ HIỆN MẮC GIẢ ĐỊNH p cho công thức Wilson,
        # không phải effect size từ 1 bài báo — ghi "lấy từ y văn [CẦN PMID]"
        # khiến bác sĩ tưởng cần trích dẫn nguồn cho con số quy ước thống kê).
        if design_code == "cross_sectional":
            p_used = effect_val if effect_val < 1.0 else 0.30
            lines.append(
                f"với tỷ lệ hiện mắc giả định p = {p_used:.2f} "
                "([CẦN bác sĩ xác nhận — dùng p=0.50 theo quy ước thận trọng nếu "
                "chưa có ước tính từ khảo sát tương tự tại cơ sở/khu vực; nếu có "
                "số liệu sơ bộ/y văn gần đây, thay p bằng ước tính đó để cỡ mẫu "
                "sát thực tế hơn]),"
            )
        elif design_code == "diagnostic":
            lines.append(f"với AUC giả định = {effect_val:.2f} ([CẦN — lấy từ nghiên cứu "
                          "chẩn đoán tương tự, ghi PMID/DOI]),")
        else:
            lines.append(f"và {effect_type} = {effect_val:.2f} (lấy từ y văn [CẦN PMID/DOI]),")
        lines.append(f"cần {n_per_group} người mỗi nhóm (N tổng = {n_total}).")
        lines.append(f"Tính thêm {int(dropout*100)}% bỏ cuộc dự kiến, cỡ mẫu cuối = {n_adjusted} người.")
    else:
        lines.append("cỡ mẫu = [CẦN EFFECT SIZE từ bác sĩ].")
    lines += [
        "```",
        "",
        "---",
        "",
        "## PHẦN 5 — TIÊU CHÍ QUA CỔNG G3",
        "",
        "- [ ] Bác sĩ xác nhận effect size (nguồn: PMID/DOI) [CẦN BÁC SĨ]",
        "- [ ] Bác sĩ xác nhận tỷ lệ dropout [CẦN BÁC SĨ]",
        "- [ ] Bác sĩ xác nhận tỷ lệ biến cố nền (với thiết kế sống còn) [CẦN BÁC SĨ]",
        "- [ ] Cập nhật G3_checkpoint.json với N đã duyệt",
        "- [ ] Copy khối cỡ mẫu vào đề cương (PHẦN 4)",
        "",
        "---",
        "*Cần bác sĩ kiểm chứng. Mọi số liệu cỡ mẫu phải được bác sĩ duyệt trước khi đưa vào đề cương chính thức.*",
    ]
    return "\n".join(lines)

def write_docx(artifact, out_path):
    """Xuất DOCX."""
    try:
        from docx import Document
        from docx.shared import Pt, RGBColor
        doc = Document()
        doc.add_heading("A4 — KẾ HOẠCH CỠ MẪU", 0)
        for line in artifact.split("\n"):
            if line.startswith("# "):
                doc.add_heading(line[2:], 1)
            elif line.startswith("## "):
                doc.add_heading(line[3:], 2)
            elif line.startswith("### "):
                doc.add_heading(line[4:], 3)
            elif "[CẦN" in line:
                p = doc.add_paragraph()
                run = p.add_run(line)
                run.font.color.rgb = RGBColor(0xCC, 0x44, 0x00)
            elif line.strip():
                doc.add_paragraph(line)
        doc.save(out_path)
        return True
    except ImportError:
        return False

def main():
    parser = argparse.ArgumentParser(description="G3 — Tính cỡ mẫu tự động")
    parser.add_argument("--study", required=True, help="Mã đề tài")
    parser.add_argument("--alpha", type=float, default=0.05)
    parser.add_argument("--power", type=float, default=0.80)
    parser.add_argument("--effect-size", type=float, default=None)
    parser.add_argument("--effect-type", default=None, choices=["HR", "OR", "RR", "ARR%", "AUC", "MD"])
    parser.add_argument("--p0", type=float, default=0.30, help="Tỷ lệ biến cố nhóm chứng")
    parser.add_argument("--dropout", type=float, default=0.20)
    parser.add_argument("--p-event", type=float, default=0.30, help="Tỷ lệ biến cố tổng thể (log-rank)")
    args = parser.parse_args()
    GC.ensure_utf8_stdout()

    study = args.study
    out_dir = BASE / "exports" / study
    out_dir.mkdir(parents=True, exist_ok=True)
    run_date = datetime.now().strftime("%Y-%m-%d")

    print(f"🔢 G3 — Tính cỡ mẫu: {study}")
    print(f"📂 Bước 1/6: Đọc checkpoints...")
    g0_cp = load_checkpoint(out_dir / "G0_checkpoint.json")
    g1_cp = load_checkpoint(out_dir / "G1_checkpoint.json")
    # SỬA (2 lỗi cùng lúc):
    # 1) topic đọc bằng .get("topic", study) không có "or" bọc ngoài — nếu
    #    checkpoint có key "topic" nhưng giá trị null, .get() trả về None
    #    (KHÔNG dùng default), làm crash topic[:60] ngay sau. Bọc "or study".
    # 2) design_code/design_primary đọc SAI đường dẫn key — G1 lưu lồng
    #    trong "design": {"internal_code":..., "primary":...}, KHÔNG PHẢI
    #    top-level "design_code"/"design_primary". Trước đây .get() luôn
    #    miss (key không tồn tại) nên luôn rơi về default "cohort" — MỌI
    #    đề tài RCT/chẩn đoán/sr_ma đều bị tính cỡ mẫu như thể là cohort mà
    #    không cảnh báo gì (bug bị che giấu vì mọi ca test trong phiên này
    #    tình cờ đều là cohort). Sửa: đọc đúng "design"."internal_code".
    topic = (g0_cp.get("topic") or study)
    design_code = g1_cp.get("design", {}).get("internal_code") or "cohort"
    design_primary = g1_cp.get("design", {}).get("primary") or "Cohort tiến cứu"
    effect_samples = g1_cp.get("effect_size_samples", [])
    print(f"  → Topic: {topic[:60]}")
    print(f"  → Design: {design_code} | {design_primary}")

    print(f"⚙️  Bước 2/6: Xác định tham số...")
    effect_quality = None
    # SỬA: "if args.effect_size and ..." coi 0.0 là falsy (Python) — nếu bác
    # sĩ cố tình/nhầm truyền --effect-size 0.0, điều kiện này bị bỏ qua âm
    # thầm, hệ thống tự chuyển sang dùng effect size khác từ G1 mà KHÔNG báo
    # cho bác sĩ biết giá trị họ nhập đã bị bỏ qua. Dùng "is not None" để chỉ
    # phân biệt "không truyền" (None) với "có truyền" (kể cả 0.0).
    if args.effect_size is not None and args.effect_type:
        effect_val, effect_type = args.effect_size, args.effect_type
        print(f"  → Effect size (từ tham số): {effect_type} = {effect_val}")
    else:
        effect_val, effect_type, effect_quality = extract_best_effect(effect_samples)
        if effect_val:
            print(f"  → Effect size (từ G1/G0): {effect_type} = {effect_val:.3f} (quality={effect_quality})")
            if effect_quality == "crude":
                print(f"  ⚠️  Effect size này là loại THÔ (không có 95%CI đi kèm khi trích "
                      f"từ abstract) — có thể lẫn ARR%/RR%, ĐỘ TIN CẬY THẤP HƠN. "
                      f"Khuyến nghị bác sĩ đọc toàn văn PMID xác nhận trước khi dùng "
                      f"để khóa cỡ mẫu, hoặc cung cấp --effect-size/--effect-type thủ công.")
        else:
            print(f"  ⚠ Không tìm được effect size — bác sĩ cần ấn định")

    alpha = args.alpha
    power = args.power
    dropout = args.dropout
    p_event = args.p_event

    # Validate tham số đầu vào — SỬA: dropout=1.0 gây ZeroDivisionError,
    # dropout gần 1.0 (vd 0.99) không crash nhưng âm thầm nhân N lên gấp
    # hàng chục/trăm lần vô lý mà không cảnh báo.
    if not (0 <= dropout < 0.5):
        print(f"❌ LỖI: --dropout={dropout} không hợp lệ. Phải trong [0, 0.5) — "
              "dropout ≥50% cho thấy thiết kế nghiên cứu có vấn đề nghiêm trọng "
              "hơn là vấn đề cỡ mẫu, cần bác sĩ xem lại trước khi tính.")
        sys.exit(1)
    if not (0 < alpha < 1) or not (0 < power < 1):
        print(f"❌ LỖI: alpha={alpha} và power={power} phải trong khoảng (0,1).")
        sys.exit(1)

    print(f"🧮 Bước 3/6: Tính cỡ mẫu...")
    n_per_group, n_total, n_adjusted = 0, 0, 0
    formula_used = ""
    sens_rows, sens_mults = [], [0.80, 1.00, 1.20]

    if effect_val:
        try:
            if design_code == "cohort" and effect_type in ("HR", "OR", "RR"):
                ev = effect_val if effect_val < 1.0 else 1 / effect_val
                n_total_raw, n_events = n_log_rank(ev, alpha, power, p_event)
                n_per_group = math.ceil(n_total_raw / 2)
                n_total = n_per_group * 2
                n_adjusted = math.ceil(n_total / (1 - dropout))
                formula_used = f"Schoenfeld log-rank: d = (zα/2+zβ)²/ln(HR)² = {n_events} biến cố → N={n_total}"
            elif design_code == "case_control" and effect_type in ("OR", "RR", "HR"):
                # SỬA: case-control (hồi cứu, chọn mẫu theo tình trạng bệnh)
                # không có trục "thời gian đến biến cố" hợp lệ để dùng
                # log-rank/Schoenfeld (vốn cho cohort/RCT có theo dõi dọc).
                # Đúng chuẩn: two-proportion trên TỶ LỆ PHƠI NHIỄM giữa ca và
                # chứng, suy ra từ OR (xấp xỉ Cornfield nếu effect size là
                # HR/RR thay vì OR thật).
                p0_exposed = args.p0  # tái dùng --p0 làm tỷ lệ phơi nhiễm NỀN ở nhóm chứng
                OR = effect_val
                odds0 = p0_exposed / (1 - p0_exposed)
                odds1 = OR * odds0
                p1_exposed = odds1 / (1 + odds1)
                n_per_group = n_two_proportion(p1_exposed, p0_exposed, alpha, power)
                n_total = n_per_group * 2
                n_adjusted = math.ceil(n_total / (1 - dropout))
                formula_used = (f"Two-proportion (case-control, {effect_type}={effect_val:.2f} → "
                                 f"tỷ lệ phơi nhiễm ca≈{p1_exposed:.2f} vs chứng={p0_exposed:.2f}). "
                                 f"[CẦN — --p0 ở đây được diễn giải là TỶ LỆ PHƠI NHIỄM NỀN của "
                                 "nhóm chứng (không phải tỷ lệ biến cố như ở cohort/RCT); bác sĩ "
                                 "xác nhận con số này đúng với đề tài, mặc định 0.30 chỉ là khởi tạo.]")
            elif design_code == "rct" and effect_type in ("HR",):
                ev = effect_val if effect_val < 1.0 else 1 / effect_val
                n_total_raw, n_events = n_log_rank(ev, alpha, power, p_event)
                n_per_group = math.ceil(n_total_raw / 2)
                n_total = n_per_group * 2
                n_adjusted = math.ceil(n_total / (1 - dropout))
                formula_used = f"Schoenfeld log-rank: d={n_events} biến cố"
            elif design_code in ("rct", "cohort", "case_control") and effect_type == "ARR%":
                # SỬA: trước đây "cohort + ARR%" (tổ hợp THỰC TẾ THƯỜNG GẶP —
                # đã xảy ra đúng với ca SGLT2-HFpEF trong phiên này) rơi vào
                # nhánh else fabricate N=100/200 không qua công thức nào.
                p1 = args.p0
                p2 = p1 - effect_val / 100
                clamp_note = ""
                if p2 <= 0:
                    p2 = 0.05
                    clamp_note = (f" [CẦN LƯU Ý — ARR%={effect_val} với p0={p1:.2f} cho p2≤0 → "
                                   f"đã kẹp p2=0.05 (ARR hiệu dụng = {(p1-0.05)*100:.1f}%, "
                                   f"KHÔNG phải {effect_val}% như yêu cầu ban đầu)]")
                    print(f"  ⚠️  ARR%={effect_val} với p0={p1:.2f} cho p2≤0 → đã kẹp p2=0.05 "
                          f"(ARR hiệu dụng = {(p1-0.05)*100:.1f}%, KHÔNG phải {effect_val}% như yêu cầu)")
                n_per_group = n_two_proportion(p1, p2, alpha, power)
                n_total = n_per_group * 2
                n_adjusted = math.ceil(n_total / (1 - dropout))
                formula_used = f"Two-proportion z-test: p1={p1:.2f}, p2={p2:.2f}{clamp_note}"
            elif design_code == "cross_sectional":
                p = effect_val if effect_val < 1.0 else 0.30
                n_total = n_prevalence(p, 0.05, alpha)
                n_per_group = n_total
                n_adjusted = math.ceil(n_total / (1 - dropout))
                formula_used = f"Wilson prevalence: p={p:.2f}, e=0.05"
            elif design_code == "diagnostic":
                auc = effect_val if effect_type == "AUC" else 0.75
                n_total = n_auc(auc, alpha, power)
                n_per_group = math.ceil(n_total / 2)
                n_adjusted = math.ceil(n_total / (1 - dropout))
                formula_used = (f"Hanley-McNeil AUC (một mẫu so với 0.5): AUC={auc:.2f}. "
                                 "[CẦN — các phần mềm khác nhau (PASS/MedCalc/nQuery) có thể "
                                 "cho N hơi khác do giả định phương sai khác nhau; nếu cỡ mẫu "
                                 "của nghiên cứu phụ thuộc chủ yếu vào con số này, nên nhờ "
                                 "thống kê viên đối chiếu lại bằng phần mềm chuyên dụng.]")
            else:
                # SỬA: KHÔNG còn fabricate N=100/200 giả khi không khớp công
                # thức nào — để trống + gắn nhãn [CẦN] thay vì số bịa mà
                # guardrail vẫn báo PASS như trước.
                n_per_group = n_total = n_adjusted = 0
                formula_used = (f"[CẦN CÔNG THỨC CỤ THỂ — tổ hợp design_code={design_code} + "
                                f"effect_type={effect_type} chưa có công thức tự động. "
                                "Bác sĩ/thống kê viên cần chọn công thức phù hợp thủ công.]")
                print(f"  ⚠️  Không có công thức tự động cho design={design_code} + "
                      f"effect_type={effect_type} — KHÔNG bịa số, cần bác sĩ tính thủ công")
            if n_total:
                sens_rows, sens_mults = sensitivity_table(design_code, n_total, effect_val, effect_type, alpha, p_event, args.p0)
                print(f"  → N mỗi nhóm: {n_per_group}, N tổng: {n_total}, N điều chỉnh: {n_adjusted}")
        except InvalidEffectSizeError as e:
            print(f"❌ LỖI EFFECT SIZE: {e}")
            print("   → KHÔNG tính được cỡ mẫu với effect size này. Kiểm tra lại "
                  "--effect-size/--effect-type hoặc effect size trích từ G1.")
            n_per_group = n_total = n_adjusted = 0
            formula_used = f"[LỖI — {e}]"
    else:
        formula_used = "[CẦN EFFECT SIZE từ bác sĩ để tính]"
        print(f"  → N: [CẦN BÁC SĨ ẤN ĐỊNH EFFECT SIZE]")

    print(f"📝 Bước 4/6: Sinh artifact A4...")
    artifact = generate_artifact(
        study, topic, design_code, design_primary, alpha, power,
        effect_val, effect_type, n_per_group, n_total, n_adjusted,
        dropout, formula_used, sens_rows, sens_mults, p_event, run_date
    )
    md_path = out_dir / f"G3_A4_SAMPLE_SIZE_{study}.md"
    md_path.write_text(artifact, encoding="utf-8")
    print(f"  → Lưu: {md_path} ({len(artifact)//1000}KB)")

    print(f"🛡️  Bước 5/6: Kiểm guardrail R1-R7...")
    errors, warnings = guardrail_check(artifact, n_adjusted, effect_val)
    for w in warnings:
        print(f"  {w}")
    for e in errors:
        print(f"  {e}")

    # ── HỢP ĐỒNG DỪNG (blocked contract) ──────────────────────────────────────
    # Ba trạng thái RỜI NGHĨA thay cho "✅ PASS im lặng trên artifact rỗng":
    #   1) errors R1–R7 (liêm chính) → GUARDRAIL FAIL (exit 3).
    #   2) n_adjusted <= 0 (GIÁ TRỊ LÕI RỖNG — chưa tính được cỡ mẫu) → BLOCKED
    #      (exit 2) + khối needs_input máy-đọc-được; KHÔNG bao giờ báo PASS.
    #   3) n_adjusted > 0 + không lỗi R → PASS (exit 0) — đường thành công cũ.
    # SỬA lỗi false-PASS đã xác nhận: trước đây n=0 (thiếu effect size) vẫn ghi
    # guardrail "✅ PASS", làm cả chuỗi tưởng G3 xong rồi kẹt ở G4.
    core = GC.core_value("n_adjusted", n_adjusted, is_empty=(n_adjusted <= 0))
    need = None
    if errors:
        status = f"⚠ {len(errors)} LỖI (R1–R7)"
        exit_code = GC.EXIT_GUARDRAIL_FAIL
    elif core["is_empty"]:
        status = GC.BLOCKED_GUARDRAIL_STR
        exit_code = GC.EXIT_BLOCKED
        cmd = (f'python tools/run_g3_auto.py --study {study} '
               '--effect-size <giá_trị> --effect-type <HR|OR|RR|ARR%|AUC>')
        if effect_val is None:
            need = GC.needs_input(
                GC.REASON_MISSING_EFFECT_SIZE,
                "G3 chưa tính được cỡ mẫu vì THIẾU effect size. Không tìm được "
                "ước lượng hiệu quả từ y văn G0/G1 và bác sĩ chưa cấp. Hệ KHÔNG "
                "bịa effect size để 'đi cho hết' (liêm chính > tiến độ).",
                cmd,
                must_not_fabricate=["effect_size", "PMID"],
                study_meta_patch={"gate_params": {"G3": {
                    "effect_size": "<CẦN BÁC SĨ CẤP — kèm PMID/DOI nguồn hoặc MCID>",
                    "effect_type": "<HR|OR|RR|ARR%|AUC>"}}},
            )
        else:
            need = GC.needs_input(
                GC.REASON_MISSING_SAMPLE_SIZE,
                f"G3 có effect size ({effect_type}={effect_val}) nhưng tổ hợp "
                f"thiết kế={design_code} + loại hiệu quả={effect_type} chưa có "
                "công thức tự động (hoặc effect size ngoài miền tính hợp lệ). "
                "Cần thống kê viên chọn công thức/tính thủ công — hệ KHÔNG bịa N.",
                cmd,
                must_not_fabricate=["n_adjusted"],
            )
    else:
        status = "✅ PASS"
        exit_code = GC.EXIT_OK
    print(f"  → Guardrail: {status}")

    print(f"📄 Bước 6/6: Xuất DOCX...")
    docx_path = out_dir / f"G3_A4_SAMPLE_SIZE_{study}.docx"
    ok = write_docx(artifact, docx_path)
    if ok:
        print(f"  → Lưu: {docx_path}")
    else:
        print(f"  ⚠ python-docx không có — bỏ qua DOCX")

    # PIN durable: nếu bác sĩ cấp effect size qua CLI → ghi vào study_meta.json để
    # CHẠY LẠI (chỉ với --study) KHÔNG mất input (đóng vòng param-loss ở re-run).
    if args.effect_size is not None and args.effect_type:
        GC.ensure_study_meta(out_dir, seed={"gate_params": {"G3": {
            "effect_size": args.effect_size, "effect_type": args.effect_type,
            "dropout": dropout, "p_event": p_event}}})

    cp = {
        "gate": "G3", "study": study, "run_date": run_date,
        "gate_status": ("BLOCKED — CHỜ EFFECT SIZE/CÔNG THỨC"
                        if exit_code == GC.EXIT_BLOCKED else "DRAFT — CHỜ BÁC SĨ XÁC NHẬN"),
        "design_code": design_code, "alpha": alpha, "power": power,
        "effect_val": effect_val, "effect_type": effect_type,
        "effect_quality": effect_quality,  # "labeled" (có 95%CI) / "crude" (thô) / None (do bác sĩ cung cấp tay)
        "n_per_group": n_per_group, "n_total": n_total, "n_adjusted": n_adjusted,
        "dropout": dropout, "formula_used": formula_used, "p_event": p_event,
        "p0": args.p0,  # lưu tỷ lệ biến cố nhóm chứng → chạy lại KHÔNG mất (fix param recovery)
        "guardrail": status,
        "core_value": core,
        "pending_doctor_actions": [
            "Xác nhận effect size (PMID/DOI từ y văn/pilot study)",
            "Xác nhận tỷ lệ bỏ cuộc dự kiến",
            "Xác nhận tỷ lệ biến cố nền (với log-rank)",
            "Copy khối cỡ mẫu vào đề cương",
        ] + (
            ["🔴 Effect size dùng để tính N là loại THÔ (không có 95%CI từ abstract) — "
             "PHẢI đọc toàn văn PMID xác nhận trước khi khóa cỡ mẫu (G4)"]
            if effect_quality == "crude" else []
        ),
    }
    if need is not None:
        cp["needs_input"] = need
    cp_path = out_dir / "G3_checkpoint.json"
    cp_path.write_text(json.dumps(cp, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"💾 Ghi checkpoint G3...")
    print(f"  → Lưu: {cp_path}")
    if exit_code == GC.EXIT_BLOCKED:
        print(f"\n🚧 G3 DỪNG — {study} (cần input đời thực, hệ KHÔNG tự vượt)")
        print(f"  → {GC.blocked_detail(cp)}")
    else:
        print(f"\n✅ G3 HOÀN THÀNH — {study}")
        print(f"  N mỗi nhóm: {n_per_group}, N tổng: {n_total}, N điều chỉnh (dropout {int(dropout*100)}%): {n_adjusted}")
        print(f"  Alpha: {alpha}, Power: {int(power*100)}%, {effect_type}: {effect_val}")
    print(f"  → Guardrail: {status}")
    return exit_code

if __name__ == "__main__":
    raise SystemExit(main() or 0)
