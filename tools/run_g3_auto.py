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

# THÊM 2026-07-19 (audit vòng 3, D1 — NGHIÊM TRỌNG): 3 thiết kế KHÔNG dùng
# công thức cỡ mẫu power/effect size truyền thống — n_adjusted=0 là CÓ CHỦ
# ĐÍCH (kèm formula_used giải thích phương pháp thay thế: RIS/TSA cho sr_ma,
# pmsampsize cho prediction, bão hòa dữ liệu cho qualitative), KHÔNG phải
# "thiếu effect size" (lỗi thật). Hằng số DÙNG CHUNG giữa guardrail (không
# hard-block) và generate_artifact (không hiện nhầm thông báo "chưa tính
# được — cần effect size").
N_NOT_APPLICABLE_DESIGNS = {"sr_ma", "prediction", "qualitative"}

# Hệ số z phổ biến (6 chữ số thập phân — khớp scipy.stats.norm.ppf để tránh
# lệch 1 đơn vị ở biên math.ceil() khi phải dùng bảng dự phòng không scipy)
Z_TABLE = {
    0.20: 0.841621,
    0.15: 1.036433,
    0.10: 1.281552,
    0.05: 1.644854,
    0.025: 1.959964,
    0.01: 2.326348,
    0.005: 2.575829,
}

def z(p):
    """
    Tính z-score từ xác suất một phía.
    SỬA 2026-07-06: khi không có scipy, tra Z_TABLE bằng key float thô
    (vd `1 - power`) sai lệch do sai số dấu phẩy động — `1 - 0.80` cho
    ra 0.19999999999999996, không khớp khóa 0.20 → âm thầm rơi về mặc
    định 1.960 (sai gần gấp đôi cho power=80%), làm MỌI cỡ mẫu tính ra
    lớn gấp ~2 lần giá trị đúng. Nay làm tròn khóa trước khi tra, và
    báo lỗi rõ ràng thay vì âm thầm dùng giá trị mặc định sai khi thiếu
    scipy lẫn giá trị trong bảng.
    """
    try:
        from scipy.stats import norm
        return norm.ppf(1 - p)
    except ImportError:
        key = round(p, 4)
        if key not in Z_TABLE:
            raise InvalidEffectSizeError(
                f"Không có scipy và p={p} (làm tròn {key}) không có trong Z_TABLE dự phòng "
                "— cài `pip install scipy` hoặc bổ sung giá trị vào Z_TABLE; "
                "không tự ý dùng z mặc định vì sẽ làm sai cỡ mẫu."
            )
        return Z_TABLE[key]

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

def n_continuous_md(md, sd, alpha=0.05, power=0.80):
    """
    Cỡ mẫu so sánh HAI TRUNG BÌNH độc lập (kết cục LIÊN TỤC — vd thang đau
    NRS/VAS, WOMAC, chất lượng sống), 2 nhóm cỡ bằng nhau, giả định phương
    sai bằng nhau (Machin/Campbell/Fayers — công thức chuẩn dùng trong PASS/
    G*Power cho superiority trial kết cục liên tục):
        n mỗi nhóm = 2 × (SD/MD)² × (zα/2 + zβ)²
    THÊM 2026-07-06: trước đây design RCT/cohort + effect_type=MD (kết cục
    liên tục) KHÔNG có công thức tự động nào — rơi vào nhánh "chưa có công
    thức", dù đây là loại kết cục PHỔ BIẾN NHẤT cho thử nghiệm về triệu chứng
    (đau, chức năng, chất lượng sống). Phát hiện qua chạy thật G0→G10 trên
    một đề tài RCT mới (đau khớp gối, kết cục NRS liên tục).
    """
    if sd is None or sd <= 0:
        raise InvalidEffectSizeError(f"SD phải dương, nhận được SD={sd}")
    if md is None or abs(md) < 1e-9:
        raise InvalidEffectSizeError(
            f"MD={md} bằng 0 (không có hiệu quả để phát hiện) — cần chênh lệch "
            "trung bình thực tế khác 0."
        )
    za = z(alpha / 2)
    zb = z(1 - power)
    return math.ceil(2 * (sd / abs(md)) ** 2 * (za + zb) ** 2)

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

def sensitivity_table(design_code, base_n, effect_val, effect_type, alpha, p_event=0.30, p0=0.30, sd=None):
    """Bảng phân tích độ nhạy: power × effect_size → N."""
    powers = [0.70, 0.80, 0.90]
    mults = [0.80, 1.00, 1.20]  # -20%, cơ sở, +20%
    rows = []
    for pwr in powers:
        row = []
        for m in mults:
            ev = effect_val * m
            try:
                if effect_type == "MD" and design_code in ("rct", "cohort") and sd:
                    n = n_continuous_md(ev, sd, alpha, pwr) * 2
                # SỬA: nhánh cũ "elif design_code in ('cohort',):" không kiểm
                # effect_type nên bắt luôn cả ARR% của cohort, đẩy giá trị %
                # (vd 11.2) vào n_log_rank() như thể là HR — ra N vô nghĩa
                # (N=4) mà không có cờ [CẦN] hay lỗi nào. Sửa: kiểm effect_type
                # TRƯỚC design_code, đồng bộ với logic thật trong main().
                elif effect_type == "ARR%" and design_code in ("rct", "cohort", "case_control"):
                    p1, p2 = p0, p0 - ev / 100
                    if p2 <= 0:
                        p2 = 0.05
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
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}

def guardrail_check(artifact, n_adjusted, effect_val, missing_sd=False):
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
        if missing_sd:
            warnings.append("R8 ⚠️ N=0 — có MD nhưng THIẾU SD (độ lệch chuẩn), "
                             "cần bác sĩ/thống kê viên cấp SD từ pilot/y văn (xem formula_used)")
        else:
            warnings.append("R8 ⚠️ N=0 — công thức tự động chưa hỗ trợ tổ hợp design/effect này, "
                             "cần bác sĩ/thống kê viên tính thủ công (xem formula_used)")
    return errors, warnings

def generate_artifact(study, topic, design_code, design_primary, alpha, power, effect_val, effect_type,
                      n_per_group, n_total, n_adjusted, dropout, formula_used, sens_rows, sens_mults,
                      p_event, run_date, sd=None, design_ambiguous=False, confirmed_n=None):
    """Sinh A4 — Kế hoạch cỡ mẫu."""
    study_safe = study.replace(" ", "-")
    lines = [
        "# A4 — KẾ HOẠCH CỠ MẪU (DRAFT)",
        f"**Đề tài:** {topic}  ",
        f"**Mã:** {study_safe} | **Ngày sinh:** {run_date} | **Trạng thái:** DRAFT — CHỜ BÁC SĨ XÁC NHẬN",
        "",
        "---",
        "",
        "## PHẦN 1 — THÔNG SỐ ĐẦU VÀO",
        "",
        "| Thông số | Giá trị | Nguồn |",
        "|---|---|---|",
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
        if design_code in ("cohort", "rct") and effect_type == "MD":
            if sd is not None and sd > 0:
                lines.append(f"| Độ lệch chuẩn (SD) kết cục | {sd:.2f} | [CẦN XÁC NHẬN — từ y văn/pilot] |")
            else:
                lines.append("| Độ lệch chuẩn (SD) kết cục | **[CẦN BÁC SĨ ẤN ĐỊNH]** | Không thể tự trích từ abstract |")
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
            "| Chỉ số | Kết quả |",
            "|---|---|",
            f"| N mỗi nhóm | **{n_per_group}** |",
            f"| N tổng (không dropout) | **{n_total}** |",
            f"| N điều chỉnh (dropout {int(dropout*100)}%) | **{n_adjusted}** |",
            "",
            f"**KẾT LUẬN:** Nghiên cứu cần tuyển **{n_adjusted} người tham gia** (chia đều {n_per_group} mỗi nhóm).",
        ]
        if design_ambiguous:
            lines += [
                "",
                f"> ⚠️ **[CẦN BÁC SĨ XÁC NHẬN THIẾT KẾ TRƯỚC KHI DÙNG N NÀY]** — G1 gán thiết kế "
                f"`{design_code}` làm PLACEHOLDER TẠM (lĩnh vực đã bão hòa cả RCT lẫn SR/MA, bác sĩ "
                "CHƯA xác nhận khoảng trống thật — xem G1 A2 §khoảng trống). N ở trên tính đúng công "
                f"thức cho thiết kế `{design_code}` NHƯNG có thể phải tính LẠI nếu bác sĩ chọn thiết kế "
                "khác (SR/MA cập nhật không cần cỡ mẫu kiểu này, hoặc RCT nhắm phân nhóm cụ thể).",
            ]
    elif design_code in N_NOT_APPLICABLE_DESIGNS:
        # SỬA 2026-07-19 (audit vòng 3, D1 — NGHIÊM TRỌNG): trước bản vá này,
        # nhánh `else` phía dưới ("⚠ Chưa tính được — cần effect size") hiện
        # SAI cho sr_ma/prediction/qualitative — 3 thiết kế này effect_val
        # LUÔN None (không áp dụng), N=0 là CÓ CHỦ ĐÍCH với phương pháp thay
        # thế đã giải thích ở PHẦN 1 (formula_used), không phải "thiếu".
        lines += [
            f"**ℹ️ N=0 CÓ CHỦ ĐÍCH** — thiết kế `{design_code}` không dùng công thức "
            "cỡ mẫu power/effect size truyền thống. Xem PHẦN 1 (mục Công thức) để "
            "biết phương pháp đúng cho thiết kế này.",
            "",
            "| Chỉ số | Kết quả |",
            "|---|---|",
            "| N mỗi nhóm | **[N/A — xem Công thức]** |",
            "| N tổng | **[N/A — xem Công thức]** |",
            "| N điều chỉnh | **[N/A — xem Công thức]** |",
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
    if confirmed_n is not None:
        lines += [
            "",
            "## PHẦN 2b — CỠ MẪU THỰC TẾ ĐÃ CHỐT (bác sĩ/chủ nhiệm quyết định)",
            "",
            f"**N thực tế đã chốt:** **{confirmed_n}** người tham gia — quyết định của "
            "bác sĩ/chủ nhiệm đề tài (vd theo khả năng thu thập/thời gian/hành chính), "
            "KHÔNG thay thế công thức tính N tối thiểu ở PHẦN 2, chỉ ghi SONG SONG để "
            "đối chiếu.",
            "",
        ]
        if n_adjusted > 0:
            if confirmed_n >= n_adjusted:
                margin = ""
                if design_code == "cross_sectional":
                    moe = 1.96 * math.sqrt(0.5 * 0.5 / confirmed_n) * 100
                    margin = (
                        f" Với N={confirmed_n} (giả định p=0.50, xấu nhất), sai số biên "
                        f"(margin of error) 95% CI ước lượng tỷ lệ ≈ ±{moe:.1f} điểm phần "
                        "trăm — chặt hơn mức tối thiểu PHẦN 2 (N tối thiểu cho ±5%)."
                    )
                lines.append(
                    f"✅ **ĐẠT** — N chốt ({confirmed_n}) ≥ N tối thiểu tính theo thống kê "
                    f"({n_adjusted}), đủ hoặc dư lực thống kê/độ chính xác so với yêu cầu tối "
                    f"thiểu.{margin}"
                )
            else:
                lines.append(
                    f"🔴 **CẢNH BÁO** — N chốt ({confirmed_n}) THẤP HƠN N tối thiểu tính theo "
                    f"thống kê ({n_adjusted}) — nguy cơ THIẾU LỰC THỐNG KÊ (underpowered). Bác "
                    "sĩ/thống kê viên cần xác nhận đây là quyết định có chủ đích (vd nghiên cứu "
                    "thăm dò/pilot) và ghi rõ giới hạn này trong đề cương, hoặc tăng N/điều "
                    "chỉnh effect size kỳ vọng."
                )
        else:
            lines.append(
                "[CẦN BỔ SUNG] — chưa có N tối thiểu tính theo thống kê để đối chiếu (thiếu "
                "effect size ở PHẦN 1); N chốt ở trên vẫn được ghi nhận nhưng KHÔNG có cơ sở "
                "so sánh."
            )
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
    if confirmed_n is not None:
        lines.append(
            f"N THỰC TẾ đã được bác sĩ/chủ nhiệm CHỐT = {confirmed_n} người "
            f"({'≥' if (n_adjusted > 0 and confirmed_n >= n_adjusted) else '—'} N tối thiểu tính toán)."
        )
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
        from docx.shared import RGBColor
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
    parser.add_argument("--sd", type=float, default=None,
                         help="Độ lệch chuẩn kết cục liên tục (bắt buộc khi --effect-type MD)")
    # THÊM 2026-07-17: trước đây G3 CHỈ tính N từ effect size — không có chỗ
    # ghi nhận khi bác sĩ/chủ nhiệm CHỐT một N thực tế khác (vd theo khả năng
    # thu thập/hành chính, thường ≥ N tối thiểu để dư an toàn) như phát hiện
    # thật khi bác sĩ báo "Mẫu được chốt là 1000 mẫu". KHÔNG thay thế N tính
    # theo thống kê — chỉ ghi SONG SONG cả hai, so sánh và cảnh báo nếu N chốt
    # < N tối thiểu (thiếu lực thống kê).
    parser.add_argument("--confirmed-n", type=int, default=None,
                         help="N thực tế bác sĩ/chủ nhiệm đã CHỐT (vd theo khả năng thu thập/hành "
                              "chính) — ghi kèm N tối thiểu tính theo thống kê, KHÔNG thay thế công thức")
    args = parser.parse_args()
    GC.ensure_utf8_stdout()

    # Audit 2026-07-11: G0/G1/G2 đều làm sạch --study (chặn '/', '..' ghi ra ngoài
    # exports/) — G3 trước đây dùng thẳng args.study, lệch chuẩn với 3 cổng anh em.
    study = re.sub(r'[^\w\-]', '_', args.study.strip().replace(" ", "-"))
    out_dir = BASE / "exports" / study
    out_dir.mkdir(parents=True, exist_ok=True)
    run_date = datetime.now().strftime("%Y-%m-%d")

    # THÊM 2026-07-08 (CRIT-05): trước đây chỉ run_pipeline.py (_recover_params)
    # mới đọc lại study_meta.json['gate_params']['G3'] khi CHẠY LẠI — gọi
    # THẲNG run_g3_auto.py --study X (không qua orchestrator) vẫn MẤT effect
    # size/type/SD bác sĩ đã pin, rơi về extract_best_effect() từ G1 (nguồn
    # khác hẳn). Nay G3 tự đọc study_meta trực tiếp làm fallback — chỉ điền
    # khi CLI không truyền (None), KHÔNG bao giờ ghi đè giá trị CLI đã cho.
    _study_meta = GC.load_study_meta(out_dir)
    _g3_pinned = (_study_meta.get("gate_params") or {}).get("G3") or {}
    if args.effect_size is None and _g3_pinned.get("effect_size") is not None:
        args.effect_size = _g3_pinned["effect_size"]
        print(f"  → Khôi phục effect_size={args.effect_size} từ study_meta.json (chạy lại không mất)")
    if args.effect_type is None and _g3_pinned.get("effect_type"):
        args.effect_type = _g3_pinned["effect_type"]
        print(f"  → Khôi phục effect_type={args.effect_type} từ study_meta.json")
    if args.sd is None and _g3_pinned.get("sd") is not None:
        args.sd = _g3_pinned["sd"]
        print(f"  → Khôi phục sd={args.sd} từ study_meta.json")
    if args.confirmed_n is None and _g3_pinned.get("confirmed_n") is not None:
        args.confirmed_n = _g3_pinned["confirmed_n"]
        print(f"  → Khôi phục confirmed_n={args.confirmed_n} từ study_meta.json (chạy lại không mất)")

    print(f"🔢 G3 — Tính cỡ mẫu: {study}")
    print("📂 Bước 1/6: Đọc checkpoints...")
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
    # THÊM 2026-07-08: G1 gắn cờ ambiguous=True khi "cohort" chỉ là placeholder
    # tạm (lĩnh vực bão hòa RCT+SR, bác sĩ CHƯA xác nhận khoảng trống thật) —
    # N tính ra dưới đây vẫn là số thật theo công thức, nhưng PHẢI cảnh báo
    # NGAY cạnh giá trị N rằng thiết kế nền chưa được xác nhận (CRIT-06).
    design_ambiguous = bool(g1_cp.get("design", {}).get("ambiguous", False))
    effect_samples = g1_cp.get("effect_size_samples", [])
    print(f"  → Topic: {topic[:60]}")
    print(f"  → Design: {design_code} | {design_primary}")

    print("⚙️  Bước 2/6: Xác định tham số...")
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
                print("  ⚠️  Effect size này là loại THÔ (không có 95%CI đi kèm khi trích "
                      "từ abstract) — có thể lẫn ARR%/RR%, ĐỘ TIN CẬY THẤP HƠN. "
                      "Khuyến nghị bác sĩ đọc toàn văn PMID xác nhận trước khi dùng "
                      "để khóa cỡ mẫu, hoặc cung cấp --effect-size/--effect-type thủ công.")
        else:
            print("  ⚠ Không tìm được effect size — bác sĩ cần ấn định")

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

    print("🧮 Bước 3/6: Tính cỡ mẫu...")
    n_per_group, n_total, n_adjusted = 0, 0, 0
    formula_used = ""
    sens_rows, sens_mults = [], [0.80, 1.00, 1.20]
    missing_sd = False  # THÊM: cờ riêng cho ca "có MD nhưng thiếu SD" — khác "chưa có công thức"

    # SỬA 2026-07-17 (round audit gate): "sr_ma"/"prediction" KHÔNG dùng cỡ mẫu
    # kiểu so-sánh-2-nhóm (HR/OR/RR/MD/AUC) nên KHÔNG được đặt trong nhánh
    # "elif design_code == ..." lồng bên trong "if effect_val:" như trước —
    # nếu G1 không trích được effect_val nào cho đề tài (rất có thể xảy ra với
    # sr_ma/prediction, vì effect_val ở 2 thiết kế này vốn KHÔNG có ý nghĩa
    # thống kê tương ứng), code rơi thẳng xuống else "[CẦN EFFECT SIZE từ bác
    # sĩ]" chung chung — bỏ lỡ hoàn toàn lời giải thích RIS/TSA hoặc pmsampsize
    # đã viết riêng cho 2 thiết kế này. Kiểm design_code == sr_ma/prediction
    # TRƯỚC, không phụ thuộc effect_val còn hay không.
    if design_code == "sr_ma":
        # THÊM 2026-07-06: sr_ma là nhánh G1 gán THƯỜNG GẶP (topic có ≥2
        # RCT chưa có SR/MA, hoặc câu hỏi tường minh yêu cầu tổng quan)
        # nhưng G3 trước đây rơi vào else chung chung. SR/MA KHÔNG dùng
        # công thức cỡ mẫu 1 nghiên cứu đơn lẻ — "cỡ mẫu" của SR/MA là
        # SỐ NGHIÊN CỨU/số bệnh nhân cộng dồn cần để đạt power cho pooled
        # estimate, tính bằng required information size (RIS) / Trial
        # Sequential Analysis (TSA). Đây phụ thuộc dị biệt (I²), phương
        # sai giữa nghiên cứu (τ²) — cần dữ liệu chỉ có SAU khi trích
        # xuất, nên KHÔNG tự động hóa hoàn toàn được ở G3; ta chỉ chỉ rõ
        # phương pháp đúng thay vì thông báo generic vô hướng.
        n_per_group = n_total = n_adjusted = 0
        formula_used = (
            "[CẦN — SR/MA KHÔNG dùng công thức cỡ mẫu 1 nghiên cứu đơn lẻ. "
            "Cỡ mẫu SR/MA = Required Information Size (RIS) / Trial Sequential "
            "Analysis (TSA): số bệnh nhân cộng dồn cần để pooled estimate đạt "
            "power, phụ thuộc dị biệt I²/τ² (chỉ biết SAU khi trích xuất dữ liệu). "
            "Dùng phần mềm TSA (Copenhagen Trial Unit) hoặc metafor::power. "
            "Bác sĩ/thống kê viên tính RIS sau bước trích xuất, KHÔNG bịa N ở đây.]"
        )
        print("  ⚠️  design=sr_ma → cần RIS/TSA (không phải công thức 1 nghiên cứu) "
              "— KHÔNG bịa số, xem hướng dẫn trong artifact A4")
    elif design_code == "prediction":
        # THÊM 2026-07-17 (round audit gate — tiếp nối vòng 5): "prediction"
        # (mô hình tiên lượng/TRIPOD+AI) trước đây rơi vào else chung chung.
        # Cỡ mẫu mô hình tiên lượng KHÔNG dùng công thức so sánh 2 nhóm (HR/
        # OR/RR/MD) — cần phương pháp riêng theo Riley RD, Ensor J, Snell KIE,
        # et al. "Calculating the sample size required for developing a
        # clinical prediction model." BMJ 2020;368:m441 (PMID 32188600) —
        # đòi hỏi ước lượng trước C-statistic/R² kỳ vọng, số tham số tiên
        # đoán ứng viên, và tỷ lệ hiện mắc/biến cố — những con số CHỈ bác
        # sĩ/thống kê viên mới có thể ấn định cho đề tài cụ thể (không thể
        # suy ra từ effect_val/effect_type như các thiết kế so sánh 2 nhóm).
        # KHÔNG bịa công thức từ trí nhớ — chỉ dẫn đúng phương pháp + gói
        # phần mềm (pmsampsize, R/Stata) thay vì thông báo generic vô hướng.
        n_per_group = n_total = n_adjusted = 0
        formula_used = (
            "[CẦN — Mô hình tiên lượng (TRIPOD+AI) KHÔNG dùng công thức so "
            "sánh 2 nhóm (HR/OR/RR/MD). Cỡ mẫu tính theo Riley RD et al. "
            "'Calculating the sample size required for developing a clinical "
            "prediction model.' BMJ 2020;368:m441 (PMID 32188600) — cần bác "
            "sĩ/thống kê viên cung cấp: C-statistic hoặc R² kỳ vọng, số tham "
            "số tiên đoán ứng viên, tỷ lệ hiện mắc/biến cố trong quần thể "
            "đích. Dùng gói phần mềm pmsampsize (R hoặc Stata) để tính. "
            "KHÔNG bịa N ở đây.]"
        )
        print("  ⚠️  design=prediction → cần pmsampsize (Riley 2020, PMID "
              "32188600), không phải công thức so sánh 2 nhóm — KHÔNG bịa "
              "số, xem hướng dẫn trong artifact A4")
    elif design_code == "qualitative":
        # THÊM 2026-07-19 (audit vòng 3, D1 — NGHIÊM TRỌNG, cùng khuôn vá
        # sr_ma/prediction 2026-07-06/07-17): trước bản vá này, "qualitative"
        # rơi thẳng vào nhánh else "[CẦN EFFECT SIZE từ bác sĩ]" chung chung —
        # SAI phương pháp luận hoàn toàn. Định tính KHÔNG dùng power/effect
        # size — cỡ mẫu xác định bằng BÃO HÒA DỮ LIỆU (data saturation, không
        # ấn định cứng trước khi thu thập). n_adjusted=0 CÓ CHỦ Ý (không phải
        # thiếu dữ liệu) — G4 phải nhận diện design_code="qualitative" để
        # KHÔNG hard-block như với N=0 của thiết kế định lượng thật.
        n_per_group = n_total = n_adjusted = 0
        formula_used = (
            "[Nghiên cứu định tính KHÔNG dùng công thức cỡ mẫu power/effect size. "
            "Cỡ mẫu xác định bằng QUY TẮC BÃO HÒA DỮ LIỆU (data saturation) — dừng "
            "phỏng vấn/nhóm tiêu điểm khi không còn chủ đề mới xuất hiện (thường "
            "12-20 người tham gia cho phỏng vấn sâu, 4-6 nhóm cho focus group — "
            "kinh nghiệm chung, KHÔNG phải ngưỡng cứng). Xem `nghien-cuu-dinh-tinh` "
            "để lập kế hoạch lấy mẫu có chủ đích + tiêu chí dừng bão hòa cụ thể. "
            "KHÔNG áp công thức power cho thiết kế này.]"
        )
        print("  ℹ️  design=qualitative → cỡ mẫu theo BÃO HÒA DỮ LIỆU (không phải "
              "power/effect size) — N=0 có chủ đích, xem artifact A4/nghien-cuu-dinh-tinh")
    elif effect_val:
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
            elif design_code in ("rct", "cohort") and effect_type == "MD":
                # THÊM 2026-07-06: kết cục LIÊN TỤC (đau/chức năng/chất lượng
                # sống) — loại kết cục PHỔ BIẾN NHẤT cho RCT triệu chứng,
                # trước đây KHÔNG có công thức nào (rơi vào nhánh else, N=0
                # với thông báo chung chung "chưa có công thức"). MD cần thêm
                # SD (độ lệch chuẩn) mà HR/OR/RR/ARR% không cần — SD KHÔNG có
                # sẵn trong G0/G1 (không trích được từ abstract một cách đáng
                # tin), nên PHẢI do bác sĩ/thống kê viên cấp qua --sd, hệ
                # KHÔNG bịa SD để "cho ra số".
                if args.sd is None or args.sd <= 0:
                    missing_sd = True
                    n_per_group = n_total = n_adjusted = 0
                    formula_used = (f"[CẦN — có MD={effect_val:.2f} (kết cục liên tục) nhưng THIẾU SD "
                                     "(độ lệch chuẩn) để tính cỡ mẫu. Bác sĩ/thống kê viên cấp qua "
                                     "--sd <giá_trị> (lấy từ pilot/y văn cùng kết cục, ghi rõ nguồn "
                                     "PMID/DOI) — hệ KHÔNG bịa SD.]")
                    print(f"  ⚠️  Có MD={effect_val} nhưng THIẾU --sd — KHÔNG bịa SD, cần bác sĩ cấp")
                else:
                    n_per_group = n_continuous_md(effect_val, args.sd, alpha, power)
                    n_total = n_per_group * 2
                    n_adjusted = math.ceil(n_total / (1 - dropout))
                    formula_used = (f"Two-sample continuous (Machin/Campbell/Fayers): "
                                     f"n=2×(SD/MD)²×(zα/2+zβ)² với MD={effect_val:.2f}, SD={args.sd:.2f}")
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
                sens_rows, sens_mults = sensitivity_table(design_code, n_total, effect_val, effect_type, alpha, p_event, args.p0, args.sd)
                print(f"  → N mỗi nhóm: {n_per_group}, N tổng: {n_total}, N điều chỉnh: {n_adjusted}")
        except InvalidEffectSizeError as e:
            print(f"❌ LỖI EFFECT SIZE: {e}")
            print("   → KHÔNG tính được cỡ mẫu với effect size này. Kiểm tra lại "
                  "--effect-size/--effect-type hoặc effect size trích từ G1.")
            n_per_group = n_total = n_adjusted = 0
            formula_used = f"[LỖI — {e}]"
    else:
        formula_used = "[CẦN EFFECT SIZE từ bác sĩ để tính]"
        print("  → N: [CẦN BÁC SĨ ẤN ĐỊNH EFFECT SIZE]")

    print("📝 Bước 4/6: Sinh artifact A4...")
    artifact = generate_artifact(
        study, topic, design_code, design_primary, alpha, power,
        effect_val, effect_type, n_per_group, n_total, n_adjusted,
        dropout, formula_used, sens_rows, sens_mults, p_event, run_date, args.sd,
        design_ambiguous=design_ambiguous, confirmed_n=args.confirmed_n,
    )
    md_path = out_dir / f"G3_A4_SAMPLE_SIZE_{study}.md"
    md_path.write_text(artifact, encoding="utf-8")
    print(f"  → Lưu: {md_path} ({len(artifact)//1000}KB)")

    print("🛡️  Bước 5/6: Kiểm guardrail R1-R7...")
    errors, warnings = guardrail_check(artifact, n_adjusted, effect_val, missing_sd)
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
    #
    # SỬA 2026-07-19 (audit vòng 3, D1 — NGHIÊM TRỌNG, xác nhận bằng thực
    # nghiệm chạy thật G3→G4 cho sr_ma/prediction): với sr_ma/prediction/
    # qualitative, effect_size KHÔNG áp dụng (n_adjusted=0 CÓ CHỦ ĐÍCH, kèm
    # formula_used hướng dẫn phương pháp riêng: RIS/TSA, pmsampsize, bão hòa
    # dữ liệu). Test cũ (2026-07-17, test_gate_prediction_design_coverage.py)
    # CÓ CHỦ Ý giữ BLOCKED cho tới khi bác sĩ tự tính N (ngoài hệ thống, theo
    # phương pháp đã hướng dẫn) rồi CHỐT qua `--confirmed-n` — không bỏ hẳn
    # yêu cầu hành động của bác sĩ trước khi khóa SAP (đúng triết lý "liêm
    # chính > tiến độ" của toàn hệ). Vấn đề THẬT không phải "có nên chặn" mà
    # là (a) thông báo SAI ("thiếu effect size" — effect size không hề áp
    # dụng) và (b) `--confirmed-n` TRƯỚC ĐÂY KHÔNG có tác dụng cho 3 thiết kế
    # này (is_empty chỉ nhìn n_adjusted, bỏ qua confirmed_n hoàn toàn — bug
    # thật, khác bản chất so với D1 nhưng phát hiện được khi vá D1). Nay: đã
    # CHỐT --confirmed-n → PASS (dùng N đã chốt); CHƯA chốt → vẫn BLOCKED,
    # nhưng thông báo đúng (xem nhánh needs_input bên dưới).
    core_is_empty = (n_adjusted <= 0) and not (
        design_code in N_NOT_APPLICABLE_DESIGNS and args.confirmed_n is not None
    )
    core = GC.core_value("n_adjusted", n_adjusted, is_empty=core_is_empty)
    need = None
    if errors:
        status = f"⚠ {len(errors)} LỖI (R1–R7)"
        exit_code = GC.EXIT_GUARDRAIL_FAIL
    elif core["is_empty"]:
        status = GC.BLOCKED_GUARDRAIL_STR
        exit_code = GC.EXIT_BLOCKED
        cmd = (f'python tools/run_g3_auto.py --study {study} '
               '--effect-size <giá_trị> --effect-type <HR|OR|RR|ARR%|AUC>')
        if design_code in N_NOT_APPLICABLE_DESIGNS:
            # THÊM 2026-07-19 (audit vòng 3, D1 — NGHIÊM TRỌNG): sr_ma/
            # prediction/qualitative KHÔNG dùng effect_size — thông báo
            # "thiếu effect size" ở nhánh dưới SAI hoàn toàn cho 3 thiết kế
            # này. Đúng quy trình: bác sĩ/thống kê viên tự tính N NGOÀI hệ
            # thống theo phương pháp đã hướng dẫn trong artifact (RIS/TSA,
            # pmsampsize, hoặc quy tắc bão hòa dữ liệu), rồi CHỐT qua
            # `--confirmed-n` (cờ có sẵn, trước bản vá này KHÔNG có tác dụng
            # cho 3 thiết kế này — is_empty chỉ nhìn n_adjusted).
            _method_hint = {
                "sr_ma": "Required Information Size (RIS)/TSA — dùng metafor::power hoặc phần mềm TSA (Copenhagen Trial Unit)",
                "prediction": "pmsampsize theo Riley RD et al. BMJ 2020;368:m441 (PMID 32188600)",
                "qualitative": "quy tắc bão hòa dữ liệu (data saturation) — xem nghien-cuu-dinh-tinh",
            }[design_code]
            need = GC.needs_input(
                GC.REASON_MISSING_SAMPLE_SIZE,
                f"G3 (thiết kế `{design_code}`) KHÔNG dùng effect_size/power truyền thống "
                f"— cần bác sĩ/thống kê viên tự tính N theo {_method_hint} (NGOÀI hệ "
                "thống, xem hướng dẫn chi tiết trong artifact A4), rồi chốt qua --confirmed-n. "
                "Hệ KHÔNG tự tính/bịa N cho thiết kế này.",
                f'python tools/run_g3_auto.py --study {study} --confirmed-n <N_đã_tự_tính>',
                must_not_fabricate=["n_adjusted", "confirmed_n"],
                study_meta_patch={"gate_params": {"G3": {
                    "confirmed_n": f"<CẦN BÁC SĨ/THỐNG KÊ VIÊN CẤP — tự tính bằng {_method_hint}>"}}},
            )
        elif effect_val is None:
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
        elif missing_sd:
            # THÊM 2026-07-06: phân biệt "có MD nhưng thiếu SD" (CÓ công thức,
            # chỉ thiếu 1 tham số) với "tổ hợp chưa có công thức tự động" —
            # thông báo chung chung ở nhánh else phía dưới sẽ SAI (nói "chưa
            # có công thức" trong khi thật ra có, chỉ thiếu SD).
            need = GC.needs_input(
                GC.REASON_MISSING_EFFECT_SIZE,
                f"G3 có MD={effect_val:.2f} (kết cục liên tục) nhưng THIẾU SD "
                "(độ lệch chuẩn) để tính cỡ mẫu. Hệ KHÔNG bịa SD — bác sĩ/thống "
                "kê viên cần cấp SD từ pilot/y văn cùng kết cục (ghi nguồn "
                "PMID/DOI hoặc MCID).",
                f'python tools/run_g3_auto.py --study {study} --effect-size {effect_val} '
                '--effect-type MD --sd <giá_trị>',
                must_not_fabricate=["sd"],
                study_meta_patch={"gate_params": {"G3": {
                    "sd": "<CẦN BÁC SĨ CẤP — kèm PMID/DOI nguồn hoặc MCID>"}}},
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

    print("📄 Bước 6/6: Xuất DOCX...")
    docx_path = out_dir / f"G3_A4_SAMPLE_SIZE_{study}.docx"
    ok = write_docx(artifact, docx_path)
    if ok:
        print(f"  → Lưu: {docx_path}")
    else:
        print("  ⚠ python-docx không có — bỏ qua DOCX")

    # PIN durable: nếu bác sĩ cấp effect size qua CLI → ghi vào study_meta.json để
    # CHẠY LẠI (chỉ với --study) KHÔNG mất input (đóng vòng param-loss ở re-run).
    if args.effect_size is not None and args.effect_type:
        seed_g3 = {"effect_size": args.effect_size, "effect_type": args.effect_type,
                   "dropout": dropout, "p_event": p_event}
        if args.sd is not None:
            seed_g3["sd"] = args.sd
        if args.confirmed_n is not None:
            seed_g3["confirmed_n"] = args.confirmed_n
        GC.ensure_study_meta(out_dir, seed={"gate_params": {"G3": seed_g3}})
    elif args.confirmed_n is not None:
        # Bác sĩ có thể chốt N thực tế TRƯỚC khi effect size sẵn sàng — vẫn ghim
        # riêng để không mất khi chạy lại.
        GC.ensure_study_meta(out_dir, seed={"gate_params": {"G3": {"confirmed_n": args.confirmed_n}}})

    cp = {
        "gate": "G3", "study": study, "run_date": run_date,
        "gate_status": ("BLOCKED — CHỜ EFFECT SIZE/CÔNG THỨC"
                        if exit_code == GC.EXIT_BLOCKED else "DRAFT — CHỜ BÁC SĨ XÁC NHẬN"),
        "design_code": design_code, "design_ambiguous": design_ambiguous, "alpha": alpha, "power": power,
        "effect_val": effect_val, "effect_type": effect_type,
        "effect_quality": effect_quality,  # "labeled" (có 95%CI) / "crude" (thô) / None (do bác sĩ cung cấp tay)
        "n_per_group": n_per_group, "n_total": n_total, "n_adjusted": n_adjusted,
        "confirmed_n": args.confirmed_n,
        "confirmed_n_adequate": (
            (args.confirmed_n >= n_adjusted) if (args.confirmed_n is not None and n_adjusted > 0) else None
        ),
        "dropout": dropout, "formula_used": formula_used, "p_event": p_event,
        "p0": args.p0,  # lưu tỷ lệ biến cố nhóm chứng → chạy lại KHÔNG mất (fix param recovery)
        "sd": args.sd,  # lưu SD kết cục liên tục (effect_type=MD) → chạy lại KHÔNG mất
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
    print("💾 Ghi checkpoint G3...")
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
