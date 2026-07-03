#!/usr/bin/env python3
"""
run_g4_auto.py — Cổng G4: SAP Final + SAP Lock Certificate
Đọc G1+G3 checkpoints → SAP Final đầy đủ + chứng chỉ khóa → A5 .md + .docx + G4_checkpoint.json
G4 là CỔNG CỨNG: bác sĩ phải ký SAP Lock Certificate mới LOCKED được.
"""
import argparse, json, re, sys
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(TOOLS))

import gate_contract as GC  # noqa: E402  (hợp đồng DỪNG dùng chung)

def load_cp(path):
    if Path(path).exists():
        with open(path) as f: return json.load(f)
    return {}

def guardrail(artifact):
    errors, warnings = [], []
    if "APPROVED_EXTERNALLY" in artifact:
        errors.append("R3 🔴 Không ghi APPROVED_EXTERNALLY")
    else:
        warnings.append("R3 ✅ Không tự claim approved")
    draft_n = artifact.count("DRAFT") + artifact.count("CHỜ KÝ")
    if draft_n < 2:
        errors.append("R4 🔴 Thiếu nhãn DRAFT/CHỜ KÝ")
    else:
        warnings.append(f"R4 ✅ Nhãn DRAFT/CHỜ KÝ đủ ({draft_n} lần)")
    can_n = len(re.findall(r'\[CẦN', artifact))
    if can_n < 5:
        errors.append(f"R6 🔴 Quá ít [CẦN...] ({can_n})")
    else:
        warnings.append(f"R6 ✅ {can_n} trường [CẦN...] đã gắn nhãn")
    if "Cần bác sĩ kiểm chứng" not in artifact:
        errors.append("R7 🔴 Thiếu disclaimer")
    else:
        warnings.append("R7 ✅ Có disclaimer")
    # SỬA: check cũ "G4_STATUS: LOCKED" in artifact luôn True (template hướng
    # dẫn LUÔN chứa chuỗi này), nên luôn push vào warnings bất kể artifact có
    # tự ý claim đã khóa/đã duyệt thật hay không — guardrail "chết", chỉ tạo
    # cảm giác an toàn giả (đã verify bằng test: artifact giả claim "đã khóa
    # SAP thành công, đã được duyệt" vẫn lọt qua). Sửa: tìm các cụm CÔNG BỐ
    # HOÀN TẤT cụ thể (không phải câu hướng dẫn quy trình) mà KHÔNG có [CẦN]
    # ngay trong câu đó — đây là tín hiệu artifact tự nhận đã xong thật.
    _FALSE_COMPLETION_PATTERNS = [
        r'đã khóa SAP thành công', r'đã được duyệt', r'đã hoàn tất SAP',
        r'SAP đã (được )?khóa(?! CHỜ)', r'nghiên cứu đã khóa',
    ]
    # SỬA: câu mô tả QUY TRÌNH/ĐIỀU KIỆN ("Nếu SAP đã được duyệt bởi PI, hệ
    # thống sẽ cập nhật trạng thái", "sau khi ký, SAP đã khóa...") bị báo lỗi
    # oan — đây không phải công bố ĐÃ XONG THẬT mà là câu hướng dẫn/điều
    # kiện. Phát hiện bởi vòng kiểm định độc lập sau khi sửa R3 lần đầu.
    # Loại trừ dòng có từ điều kiện/tương lai/hướng dẫn đứng trước cụm khớp.
    _PROCESS_MARKERS = ("nếu ", "sau khi", "khi nào", "khi đã", "sẽ ", "để ")
    # Kiểm theo TỪNG DÒNG (không phải cửa sổ ký tự cố định) — cửa sổ ký tự
    # dễ bị "ăn theo" các [CẦN]/CHỜ KÝ KHÔNG LIÊN QUAN nằm tình cờ gần đó
    # trong văn bản ngắn (đã tự phát hiện lỗi này khi test với artifact giả
    # ngắn — [CẦN] ở dòng trên vẫn lọt vào cửa sổ ±100 ký tự dù không liên
    # quan gì đến câu công bố). Dòng chứa công bố hoàn tất phải TỰ nó có
    # [CẦN]/CHỜ KÝ mới được coi là placeholder, không mượn từ dòng khác.
    found_false_completion = False
    for line in artifact.split("\n"):
        if "[CẦN" in line or "CHỜ KÝ" in line:
            continue
        line_lower = line.lower()
        for pat in _FALSE_COMPLETION_PATTERNS:
            m = re.search(pat, line, re.IGNORECASE)
            if not m:
                continue
            before = line_lower[:m.start()]
            if any(marker in before for marker in _PROCESS_MARKERS):
                continue  # câu điều kiện/quy trình, không phải công bố thật
            found_false_completion = True
            errors.append(f"R3 🔴 Artifact tự công bố đã khóa/duyệt SAP mà không có nhãn "
                           f"[CẦN]/'CHỜ KÝ' ngay trong dòng đó — nghi tự vượt cổng: '{line.strip()}'")
            break
    if not found_false_completion:
        warnings.append("R3 ✅ Không tìm thấy công bố tự vượt cổng khóa SAP")
    return errors, warnings

def generate(study, topic, design_code, design_primary, reporting_std,
             n_adjusted, alpha, power, effect_val, effect_type, run_date):
    sap_sections = {
        "rct": ("Nhóm can thiệp vs nhóm chứng", "Intention-to-treat (ITT), Per-protocol (PP)", "t-test hoặc Mann-Whitney; logistic/log-rank"),
        "cohort": ("Nhóm phơi nhiễm vs không phơi nhiễm", "Phân tích đầy đủ (complete case + MI)", "Cox regression; logistic regression"),
        "cross_sectional": ("Toàn bộ mẫu đủ tiêu chí", "Phân tích đầy đủ", "Hồi quy logistic/tuyến tính"),
        "diagnostic": ("Bệnh nhân có xét nghiệm chỉ số và tiêu chuẩn vàng", "Phân tích đầy đủ", "ROC, AUC, độ nhạy/đặc hiệu"),
        "sr_ma": ("Tất cả nghiên cứu đủ tiêu chí đưa vào", "Phân tích đầy đủ", "Random/Fixed effects meta-analysis"),
        "case_control": ("Ca bệnh vs chứng ghép cặp", "Phân tích đầy đủ", "Conditional logistic regression"),
    }
    pop, analysis_pop, main_method = sap_sections.get(design_code, ("Toàn bộ mẫu", "Phân tích đầy đủ", "[CẦN]"))

    lines = [
        f"# A5 — SAP FINAL + SAP LOCK CERTIFICATE (DRAFT — CHỜ BÁC SĨ KÝ)",
        f"**Đề tài:** {topic}  ",
        f"**Mã:** {study} | **Phiên bản SAP:** 1.0 | **Ngày sinh:** {run_date}",
        f"**Chuẩn báo cáo:** {reporting_std}",
        "",
        "> ⚠️ **CỔNG G4 — SAP LOCK:** SAP này ở trạng thái DRAFT. Bác sĩ phải đọc, điền [CẦN...], KÝ ở Phần 5.",
        "> Sau khi ký: KHÔNG thay đổi kết cục chính / mô hình chính. Phân tích thêm sau khi xem dữ liệu → ghi THĂM DÒ.",
        "",
        "---",
        "",
        "## PHẦN 1 — THÔNG TIN ĐỀ TÀI",
        "",
        f"| Mục | Nội dung |",
        f"|---|---|",
        f"| Tên đề tài | {topic} |",
        f"| Mã nghiên cứu | {study} |",
        f"| Thiết kế | {design_primary} |",
        f"| Chuẩn báo cáo | {reporting_std} |",
        f"| Ngày soạn SAP | {run_date} |",
        f"| Phiên bản | 1.0 |",
        "",
        "---",
        "",
        "## PHẦN 2 — LỊCH SỬ PHIÊN BẢN SAP",
        "",
        f"| Phiên bản | Ngày | Người soạn | Thay đổi chính |",
        f"|---|---|---|---|",
        f"| 1.0 | {run_date} | [CẦN TÊN TÁC GIẢ] | Bản đầu tiên (tự động từ G1) |",
        "",
        "---",
        "",
        "## PHẦN 3 — SAP 12 MỤC CUỐI",
        "",
        "### §1 QUẦN THỂ PHÂN TÍCH",
        "",
        f"- **Quần thể chính:** {pop}  ",
        f"- **Cỡ mẫu cuối:** N = {n_adjusted} (alpha={alpha}, power={int(power*100)}%)  " if n_adjusted else "- **Cỡ mẫu:** [CẦN từ G3]  ",
        "- **Tiêu chí nhận:** [CẦN BÁC SĨ ĐIỀN — từ đề cương]  ",
        "- **Tiêu chí loại:** [CẦN BÁC SĨ ĐIỀN]  ",
        "",
        "### §2 KẾT CỤC",
        "",
        "- **Kết cục chính:** [CẦN BÁC SĨ ĐIỀN — ví dụ: tỷ lệ nhập viện tim mạch trong 12 tháng]  ",
        "- **Đơn vị / ngưỡng:** [CẦN]  ",
        "- **Kết cục phụ 1:** [CẦN]  ",
        "- **Kết cục phụ 2:** [CẦN]  ",
        "- **Kết cục an toàn:** [CẦN — đặc biệt với RCT]  ",
        "",
        "### §3 THỐNG KÊ MÔ TẢ",
        "",
        "- Biến liên tục: trung bình ± SD (phân phối chuẩn) hoặc trung vị [IQR] (lệch)  ",
        "- Biến phân loại: n (%)  ",
        "- So sánh đặc điểm nền: t-test / Mann-Whitney / Chi-square / Fisher  ",
        "",
        f"### §4 PHÂN TÍCH CHÍNH",
        "",
        f"- **Phương pháp:** {main_method}  ",
        f"- **Quần thể:** {analysis_pop}  ",
        "- **Trình bày:** ước lượng + 95%CI; không báo p-value đơn độc  ",
        "",
        "### §5 PHÂN TÍCH ĐA BIẾN",
        "",
        "- **Biến độc lập đưa vào:** [CẦN BÁC SĨ LIỆT KÊ — kèm lý do lâm sàng / DAG]  ",
        "- **Phương pháp chọn biến:** Đưa vào toàn bộ (không stepwise)  ",
        "- **Giả định:** [CẦN kiểm tra PH / normality theo thiết kế]  ",
        "",
        "### §6 DỮ LIỆU THIẾU",
        "",
        "- **Chiến lược:** Multiple Imputation (MI, m=20, method=pmm)  ",
        "- **Giả định:** MAR (missing at random)  ",
        "- **Biến đưa vào mô hình imputation:** [CẦN BÁC SĨ ĐIỀN]  ",
        "- **Phân tích hoàn chỉnh (complete case):** báo cáo song song với MI  ",
        "",
        "### §7 PHÂN TÍCH NHÓM NHỎ (Subgroup Analysis)",
        "",
        "- **Nhóm nhỏ tiền định:** [CẦN BÁC SĨ — phải ghi TRƯỚC khi xem dữ liệu]  ",
        "- **Kiểm định tương tác:** Mô hình với interaction term  ",
        "- **Cảnh báo:** Phân tích nhóm nhỏ chỉ diễn giải thăm dò  ",
        "",
        "### §8 ĐA SO SÁNH",
        "",
        "- **Điều chỉnh:** [CẦN — Bonferroni / FDR nếu >3 kết cục chính]  ",
        "- **Kết cục được coi là kết cục chính:** chỉ 1  ",
        "",
        "### §9 PHÂN TÍCH ĐỘ NHẠY",
        "",
        "- Thay đổi định nghĩa phơi nhiễm/kết cục ±1 SD  ",
        "- Complete case vs MI  ",
        "- [CẦN BÁC SĨ thêm kịch bản cụ thể]  ",
        "",
        "### §10 PHẦN MỀM + SEED",
        "",
        "- **Phần mềm:** [CẦN — R v4.x / Stata v18 / SPSS v29]  ",
        "- **Packages:** [CẦN — survival, lme4, mice, gtsummary...]  ",
        "- **Random seed:** [CẦN BÁC SĨ ẤN ĐỊNH — ví dụ: set.seed(2026)]  ",
        "",
        "### §11 DUMMY TABLES (Khung bảng kết quả)",
        "",
        "**Bảng 1 — Đặc điểm nền:**",
        "| Biến | Nhóm 1 | Nhóm 2 | p |",
        "|---|---|---|---|",
        "| Tuổi (năm) | ___ ± ___ | ___ ± ___ | ___ |",
        "| Giới nữ, n (%) | ___ (_) | ___ (_) | ___ |",
        "| [CẦN thêm biến] | | | |",
        "",
        "**Bảng 2 — Kết cục chính:**",
        "| Kết cục | N (%) / Trung vị | 95%CI | p |",
        "|---|---|---|---|",
        "| [CẦN KẾT QUẢ THẬT] | | | |",
        "",
        f"### §12 ALPHA + POWER",
        "",
        f"- **Alpha (two-sided):** {alpha}  ",
        f"- **Power:** {int(power*100)}%  ",
        f"- **Cỡ mẫu:** N = {n_adjusted}  " if n_adjusted else "- **Cỡ mẫu:** [CẦN từ G3]  ",
        f"- **Effect size dự kiến:** {effect_type} = {effect_val:.2f}  " if effect_val else "- **Effect size:** [CẦN từ G3]  ",
        "",
        "---",
        "",
        "## PHẦN 4 — THAY ĐỔI SAU KHI KHÓA",
        "",
        "| Ngày | Mô tả thay đổi | Loại | Người duyệt |",
        "|---|---|---|---|",
        "| (chưa có) | | | |",
        "",
        "> **Quy tắc:** Mọi thay đổi sau khi ký → phân loại TIỀN ĐỊNH / THĂM DÒ / SAP AMENDMENT.  ",
        "> Không được thay đổi kết cục chính hoặc mô hình chính sau khi xem dữ liệu.",
        "",
        "---",
        "",
        "## PHẦN 5 — SAP LOCK CERTIFICATE (DRAFT — CHỜ KÝ)",
        "",
        "```",
        "╔══════════════════════════════════════════════════════════════╗",
        "║              SAP LOCK CERTIFICATE — PHIÊN BẢN 1.0          ║",
        "╠══════════════════════════════════════════════════════════════╣",
        f"║ Đề tài    : {study:<48} ║",
        f"║ Ngày soạn : {run_date:<48} ║",
        f"║ Cỡ mẫu   : N = {str(n_adjusted):<45} ║" if n_adjusted else "║ Cỡ mẫu   : [CẦN từ G3]                                      ║",
        f"║ Alpha     : {alpha}                                            ║",
        f"║ Power     : {int(power*100)}%                                            ║",
        "║ KQ chính  : [CẦN BÁC SĨ ĐIỀN — từ SAP §2]                 ║",
        "║ Phân tích : [CẦN BÁC SĨ ĐIỀN — quần thể phân tích]        ║",
        "╠══════════════════════════════════════════════════════════════╣",
        "║ TRẠNG THÁI: DRAFT — CHỜ KÝ                                 ║",
        "╠══════════════════════════════════════════════════════════════╣",
        "║ Chủ nhiệm đề tài: _________________________ Ngày: ___/___/ ║",
        "║ Đồng tác giả:     _________________________ Ngày: ___/___/ ║",
        "╚══════════════════════════════════════════════════════════════╝",
        "",
        "  → Sau khi ký: scan + lưu vào exports/<study>/G4_SAP_SIGNED.pdf",
        "  → Cung cấp ngày ký → hệ thống ghi G4_STATUS: LOCKED",
        "  → Chỉ sau khi G4=LOCKED mới được xem dữ liệu (G5→G6)",
        "```",
        "",
        "---",
        "",
        "## PHẦN 6 — TIÊU CHÍ QUA CỔNG G4 + CƠ CHẾ MỞ KHÓA",
        "",
        "**Để G4=LOCKED:**",
        "1. Bác sĩ điền TẤT CẢ [CẦN...] trong SAP §2 (kết cục) và §5 (covariates)",
        "2. Bác sĩ ký SAP Lock Certificate (Phần 5)",
        "3. Cung cấp ngày ký cho hệ thống",
        "4. Hệ thống ghi: `G4_STATUS: LOCKED` vào checkpoint",
        "",
        "**Chỉ sau G4=LOCKED:**",
        "- Mới được mở dữ liệu (G5)",
        "- Mới được chạy phân tích chính (G6)",
        "- Mọi phân tích trước G4=LOCKED bị coi là 'thăm dò'",
        "",
        "---",
        "*Cần bác sĩ kiểm chứng. SAP này chỉ có hiệu lực pháp lý sau khi được ký.*",
    ]
    return "\n".join(lines)

def write_docx(artifact, path):
    try:
        from docx import Document
        from docx.shared import RGBColor
        doc = Document()
        for line in artifact.split("\n"):
            if line.startswith("# "): doc.add_heading(line[2:], 0)
            elif line.startswith("## "): doc.add_heading(line[3:], 1)
            elif line.startswith("### "): doc.add_heading(line[4:], 2)
            elif "[CẦN" in line:
                p = doc.add_paragraph()
                p.add_run(line).font.color.rgb = RGBColor(0xCC, 0x44, 0x00)
            elif line.strip(): doc.add_paragraph(line)
        doc.save(path)
        return True
    except ImportError:
        return False
    except Exception as e:
        # SỬA: chỉ bắt ImportError trước đây — lỗi khác (font/encoding/style
        # thiếu...) làm crash TOÀN BỘ script SAU KHI đã ghi .md nhưng TRƯỚC
        # KHI ghi checkpoint, để lại trạng thái nửa vời khó chẩn đoán.
        print(f"  ⚠️  Lỗi xuất DOCX (bỏ qua, vẫn giữ bản .md): {e}")
        return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--study", required=True)
    args = parser.parse_args()
    study = re.sub(r'[^\w\-]', '_', args.study.strip().replace(" ", "-"))
    out = BASE / "exports" / study
    out.mkdir(parents=True, exist_ok=True)
    run_date = datetime.now().strftime("%Y-%m-%d")

    print(f"📋 G4 — SAP Lock: {study}")
    # SỬA LỖI NGHIÊM TRỌNG: trước đây G4 KHÔNG đọc G0 checkpoint, và đọc SAI
    # đường dẫn key của G1 — G1 lưu topic ở G0 (không có trong G1), còn
    # design_code/design_primary/reporting_standard lưu LỒNG trong G1's
    # "design": {...}, không phải top-level. Mọi lần .get("topic"/"design_code"
    # /"design_primary"/"reporting_standard", default) trước đây LUÔN miss
    # (key không tồn tại ở vị trí được tìm) nên LUÔN âm thầm rơi về default
    # ("cohort", tên mã đề tài thay vì câu hỏi nghiên cứu thật) — bất kể G1
    # thực sự xác định thiết kế gì. Bug này bị che giấu suốt phiên vì mọi ca
    # test đều tình cờ là cohort. Sửa: nạp thêm G0, đọc đúng đường dẫn G1.design.*
    g0 = load_cp(out / "G0_checkpoint.json")
    g1 = load_cp(out / "G1_checkpoint.json")
    g3 = load_cp(out / "G3_checkpoint.json")
    g1_design = g1.get("design") or {}
    topic = (g0.get("topic") or None) or study
    design_code = g1_design.get("internal_code") or "cohort"
    design_primary = g1_design.get("primary") or "Cohort tiến cứu"
    reporting_std = g1_design.get("reporting_standard") or "STROBE 2007"
    # SỬA: n_adjusted có thể là string nếu checkpoint bị ghi/sửa bởi nguồn
    # khác (vd tay sửa JSON) — "n_adjusted <= 0" crash TypeError khi so sánh
    # str với int. Ép kiểu an toàn, giá trị không hợp lệ → coi như 0 (sẽ bị
    # hard-stop chặn ngay dưới, không lan truyền số rác).
    try:
        n_adjusted = int(g3.get("n_adjusted") or 0)
    except (TypeError, ValueError):
        n_adjusted = 0
    alpha = g3.get("alpha") or 0.05
    power = g3.get("power") or 0.80
    effect_val = g3.get("effect_val")
    effect_type = g3.get("effect_type") or "HR"

    # SỬA: trước đây N=0 (G3 chưa chạy/chưa tính được) vẫn cho SAP hoàn tất
    # với guardrail PASS im lặng — một SAP không có cỡ mẫu là vô nghĩa để
    # khóa. Nay hard-stop, không ghi artifact/checkpoint nào khi thiếu N thật.
    if not g3 or n_adjusted <= 0:
        # HỢP ĐỒNG DỪNG: trước đây exit 1 KHÔNG ghi checkpoint → pipeline nhầm là
        # CRASH, báo "❌ failed" trống, không remediation. Nay GHI checkpoint
        # BLOCKED + needs_input trỏ NGƯỢC về G3 (cổng chặn thật là G3 thiếu effect
        # size), rồi exit 2 (blocked, KHÔNG phải lỗi). G4 vẫn TỪ CHỐI sinh SAP
        # Final rỗng — chỉ khác ở chỗ DỪNG có thể hành động ngay.
        print(f"🚧 G4 DỪNG: Chưa có cỡ mẫu hợp lệ từ G3 (n_adjusted={n_adjusted}).")
        need = GC.needs_input(
            GC.REASON_MISSING_SAMPLE_SIZE,
            "G4 (khóa SAP) chưa thể sinh SAP Final vì G3 chưa cho cỡ mẫu hợp lệ "
            f"(N={n_adjusted}). Cổng chặn thật là G3 — cần effect size để tính N.",
            f'python tools/run_g3_auto.py --study {study} --effect-size <giá_trị> '
            '--effect-type <HR|OR|RR|ARR%|AUC>',
            must_not_fabricate=["n_adjusted", "effect_size", "PMID"],
            study_meta_patch={"gate_params": {"G3": {
                "effect_size": "<CẦN BÁC SĨ CẤP — kèm PMID/DOI hoặc MCID>",
                "effect_type": "<HR|OR|RR|ARR%|AUC>"}}},
        )
        cp = {
            "gate": "G4", "study": study, "run_date": run_date,
            "g4_status": "BLOCKED — CHỜ CỠ MẪU TỪ G3",
            "g4_sap_version": None, "g4_lock_date": None,
            "n_from_g3": n_adjusted,
            "guardrail": GC.BLOCKED_GUARDRAIL_STR,
            "core_value": GC.core_value("n_from_g3", n_adjusted, is_empty=True),
            "needs_input": need,
            "pending_doctor_actions": [
                "Cấp effect size cho G3 (PMID/DOI hoặc MCID) rồi chạy lại G3 → G4",
            ],
        }
        (out / "G4_checkpoint.json").write_text(
            json.dumps(cp, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"   → {GC.blocked_detail(cp)}")
        print(f"   💾 Đã ghi G4_checkpoint.json (BLOCKED) để pipeline đọc remediation.")
        raise SystemExit(GC.EXIT_BLOCKED)

    print(f"  → Topic: {topic[:60]}")
    print(f"  → Design: {design_code} | N={n_adjusted}")

    artifact = generate(study, topic, design_code, design_primary, reporting_std,
                        n_adjusted, alpha, power, effect_val, effect_type, run_date)
    md = out / f"G4_A5_SAP_FINAL_{study}.md"
    md.write_text(artifact, encoding="utf-8")
    print(f"  → Lưu: {md} ({len(artifact)//1000}KB)")

    print(f"🛡️  Kiểm guardrail...")
    errors, warnings = guardrail(artifact)
    for w in warnings: print(f"  {w}")
    for e in errors: print(f"  {e}")
    status = "✅ PASS" if not errors else f"⚠ {len(errors)} LỖI"
    print(f"  → Guardrail: {status}")

    docx = out / f"G4_A5_SAP_FINAL_{study}.docx"
    write_docx(artifact, docx)
    print(f"  → DOCX: {docx}")

    cp = {
        "gate": "G4", "study": study, "run_date": run_date,
        "g4_status": "PENDING — CHỜ BÁC SĨ KÝ SAP",
        "g4_sap_version": "1.0", "g4_lock_date": None,
        "n_from_g3": n_adjusted, "alpha": alpha, "power": power,
        "design_code": design_code, "reporting_standard": reporting_std,
        "guardrail": status,
        "pending_doctor_actions": [
            "Điền §2 kết cục chính (tên biến, đơn vị, ngưỡng)",
            "Điền §5 covariates với lý do lâm sàng / DAG",
            "Điền §10 phần mềm + seed",
            "Ký SAP Lock Certificate → cung cấp ngày ký",
        ],
        "lock_instruction": "Để mở G4: ký SAP Lock Certificate → cung cấp ngày ký → ghi G4_STATUS=LOCKED",
    }
    cp_path = out / "G4_checkpoint.json"
    cp_path.write_text(json.dumps(cp, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"💾 Lưu: {cp_path}")
    print(f"\n✅ G4 HOÀN THÀNH — {study}")
    print(f"  SAP version: 1.0, N (từ G3): {n_adjusted}")
    print(f"  G4 Status: PENDING — CHỜ BÁC SĨ KÝ SAP")
    print(f"  → Guardrail: {status}")

if __name__ == "__main__":
    main()
