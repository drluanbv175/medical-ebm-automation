#!/usr/bin/env python3
"""
run_g4_auto.py — Cổng G4: SAP Final + SAP Lock Certificate
Đọc G1+G3 checkpoints → SAP Final đầy đủ + chứng chỉ khóa → A5 .md + .docx + G4_checkpoint.json
G4 là CỔNG CỨNG: bác sĩ phải ký SAP Lock Certificate mới LOCKED được.
"""
import argparse
import json
import re
import sys

# Windows: stdout mặc định cp1252 giết print() tiếng Việt — ép UTF-8 (chốt BH55/R4)
import sys as _sys_r4
from datetime import datetime
from pathlib import Path

for _s_r4 in (_sys_r4.stdout, _sys_r4.stderr):
    try:
        _s_r4.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

BASE = Path(__file__).resolve().parent.parent
TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(TOOLS))

import chuan_trinh_bay as _CTB  # noqa: E402  (chuẩn trình bày tài liệu — font/ký tự, 01/09/2026)
import cong_song as CS  # noqa: E402  (chấm sống G3 trước khi sinh SAP — G4-04)
import g4_quality_gate as G4Q  # noqa: E402  (khung §12 dùng chung với bộ chấm — G4-06)
import gate_contract as GC  # noqa: E402  (hợp đồng DỪNG dùng chung)
import skill_standards as S  # noqa: E402  (đặc tả thiết kế khoá ở G1, chuẩn báo cáo theo thiết kế)
import vn_prose_style as _VNSTYLE  # noqa: E402  (chuẩn hoá văn phong artifact)

# THÊM 2026-07-19 (audit vòng 3, D1 — NGHIÊM TRỌNG, xác nhận bằng thực
# nghiệm chạy thật G3→G4): 3 thiết kế KHÔNG dùng công thức cỡ mẫu power/
# effect size — n_adjusted=0 là CÓ CHỦ ĐÍCH (G3 đã ghi formula_used giải
# thích phương pháp thay thế: RIS/TSA cho sr_ma, pmsampsize cho prediction,
# bão hòa dữ liệu cho qualitative). ĐỒNG BỘ TAY với
# run_g3_auto.py::N_NOT_APPLICABLE_DESIGNS — sửa 1 nơi phải sửa cả 2 (2 file
# độc lập, không cross-import CLI script khác để tránh side-effect).
N_NOT_APPLICABLE_DESIGNS = {"sr_ma", "prediction", "qualitative"}


def load_cp(path):
    if Path(path).exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
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
    # SỬA 2026-07-31 (audit tautology vòng 2 — reverse-tautology CRITICAL):
    # R6 TỪNG BLOCK khi can_n<5 — nhưng một SAP được điền THẬT SỰ đầy đủ (kể
    # cả Lock Certificate: "KQ chính"/"Phân tích") xóa gần hết placeholder,
    # khiến can_n giảm về 0-2, dưới ngưỡng 5 — R6 BLOCK đúng lúc SAP hoàn
    # thiện thật, không phải lúc còn thiếu. g4_quality_gate.py::G4-AUTO-00
    # (thêm 2026-07-30, chạy lại guardrail() trên artifact_text sống) khiến
    # lỗi này lan ra evaluate_g4_quality(): BẤT KỲ BLOCK nào từ guardrail()
    # đều ép report['status']=BLOCKED, đè cả ledger_signed/human_complete.
    # Xác nhận thực nghiệm: SAP điền thật (EPV/VIF đúng, MI đúng biến, subgroup
    # tiền định, R v4.3.1+seed, outcome khớp SAP) + ledger_signed=True +
    # mọi gate_params.G4 human attestations=True → status vẫn BLOCKED chỉ vì
    # G4-AUTO-00 (guardrail_passed=False do R6). Hạ xuống CẢNH BÁO thông tin
    # (không còn chặn) — đúng tiền lệ đã áp cho R6 tương tự của G8. Kiểm
    # placeholder THẬT còn sót ở mục BẮT BUỘC (§1/§2/§4/§5/§9/§10, RCT thêm §13–§15) đã có sẵn ở
    # approve_gate.py::_g4_sections_still_draft() — chốt trước-ký thật sự,
    # không nhân đôi logic sai ở đây.
    can_n = len(re.findall(r'\[CẦN', artifact))
    warnings.append(f"R6 ✅ {can_n} trường [CẦN...] còn lại (thông tin, không chặn)")
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

def _so(gia_tri, mac_dinh="[CẦN từ G3]"):
    """Số tham số in ĐÚNG giá trị G3 (định dạng :g) — None ⇒ nhãn chờ G3.

    VÁ 04/10/2026 (soát từng cổng, G4-06/G4-08): bản cũ in effect size bằng :.2f (0,855 ⇒ «0.85») — văn bản KÝ phải ghi
    đúng tham số đã dùng để tính N; alpha/power vắng từng rơi về 0,05/80% im lặng (CHUNG-F)."""
    if gia_tri is None or gia_tri == "":
        return mac_dinh
    try:
        return f"{float(gia_tri):g}"
    except (TypeError, ValueError):
        return str(gia_tri)


def _phan_tram(ty_le, mac_dinh="[CẦN từ G3]"):
    """0.8 ⇒ «80%» (làm tròn — int(0.29 * 100) của bản cũ ra 28)."""
    try:
        return f"{round(float(ty_le) * 100)}%"
    except (TypeError, ValueError):
        return mac_dinh


# Nhãn hai nhóm của bảng giả cho thiết kế so sánh (§11).
_NHOM_BANG_GIA = {
    "rct": ("Nhóm can thiệp", "Nhóm chứng"),
    "cohort": ("Phơi nhiễm", "Không phơi nhiễm"),
    "case_control": ("Nhóm bệnh (ca)", "Nhóm chứng"),
}


def _bang_gia(design_code, loai12):
    """§11 — khung bảng kết quả THEO THIẾT KẾ.

    VÁ 04/10/2026 (soát từng cổng, G4-06): bản cũ in «Nhóm 1 | Nhóm 2 | p» cho MỌI thiết kế — định tính có cột p mâu
    thuẫn §8, chẩn đoán thiếu bảng 2×2/độ nhạy-độ đặc hiệu, cắt ngang mô tả không có nhóm, và RCT có cột p cho đặc
    điểm nền dù khác biệt nền giữa các nhóm ĐÃ NGẪU NHIÊN HOÁ là do may rủi (CONSORT 2010 E&E, PMID 20332511)."""
    if design_code == "qualitative":
        return [
            "**Bảng 1 — Đặc điểm người tham gia (mô tả, không kiểm định):**",
            "| Đặc điểm | n (%) |",
            "|---|---|",
            "| [CẦN thêm đặc điểm theo tiêu chí đa dạng §7] | |",
            "",
            "**Bảng 2 — Chủ đề và chủ đề con (COREQ/SRQR):**",
            "| Chủ đề | Chủ đề con | Trích dẫn minh hoạ (ẩn danh, mã người tham gia) |",
            "|---|---|---|",
            "| [CẦN KẾT QUẢ THẬT — sau khi mã hoá] | | |",
        ]
    if design_code == "diagnostic":
        return [
            "**Bảng 1 — Đặc điểm người tham gia theo tiêu chuẩn tham chiếu (STARD 2015):**",
            "| Biến | Có bệnh (tham chiếu +) | Không bệnh (tham chiếu −) |",
            "|---|---|---|",
            "| [CẦN thêm biến] | | |",
            "",
            "**Bảng 2 — Xét nghiệm chỉ số × tiêu chuẩn tham chiếu (2×2):**",
            "| Xét nghiệm chỉ số | Tham chiếu + | Tham chiếu − |",
            "|---|---|---|",
            "| Dương tính | a | b |",
            "| Âm tính | c | d |",
            "",
            "**Bảng 3 — Độ chính xác chẩn đoán (ước lượng + 95%CI):**",
            "| Chỉ số | Ước lượng | 95%CI |",
            "|---|---|---|",
            "| Độ nhạy · độ đặc hiệu · LR+ · LR− · AUC | [CẦN KẾT QUẢ THẬT] | |",
        ]
    if design_code == "sr_ma":
        return [
            "**Bảng 1 — Đặc điểm các nghiên cứu được đưa vào (PRISMA 2020):**",
            "| Nghiên cứu | Thiết kế | Cỡ mẫu | Quần thể | Can thiệp/so sánh | Nguy cơ sai lệch |",
            "|---|---|---|---|---|---|",
            "| [CẦN KẾT QUẢ THẬT — sau sàng lọc] | | | | | |",
            "",
            "**Bảng 2 — Ước lượng gộp:**",
            "| Kết cục | Số nghiên cứu (k) | Hiệu ứng gộp (95%CI) | I² | τ² |",
            "|---|---|---|---|---|",
            "| [CẦN KẾT QUẢ THẬT] | | | | |",
        ]
    if design_code == "prediction":
        return [
            "**Bảng 1 — Đặc điểm người tham gia (TRIPOD+AI):**",
            "| Biến | Tập phát triển | Tập kiểm định |",
            "|---|---|---|",
            "| [CẦN thêm biến dự báo] | | |",
            "",
            "**Bảng 2 — Hiệu năng mô hình (ước lượng + 95%CI):**",
            "| Chỉ số | Tập phát triển (đã hiệu chỉnh lạc quan) | Tập kiểm định |",
            "|---|---|---|",
            "| C-statistic · độ dốc/hệ số chặn hiệu chuẩn | [CẦN KẾT QUẢ THẬT] | |",
        ]
    if loai12 == "chinh_xac":
        return [
            "**Bảng 1 — Đặc điểm mẫu nghiên cứu (mô tả toàn mẫu):**",
            "| Biến | Toàn mẫu: n (%) hoặc trung bình ± SD |",
            "|---|---|",
            "| [CẦN thêm biến] | |",
            "",
            "**Bảng 2 — Kết cục chính (ước lượng theo độ chính xác):**",
            "| Kết cục | Tỷ lệ (%) | 95%CI |",
            "|---|---|---|",
            "| [CẦN KẾT QUẢ THẬT] | | |",
        ]
    nhom1, nhom2 = _NHOM_BANG_GIA.get(design_code, ("Nhóm 1", "Nhóm 2"))
    if design_code == "rct":
        return [
            "**Bảng 1 — Đặc điểm nền theo nhóm ngẫu nhiên hoá:**",
            f"| Biến | {nhom1} | {nhom2} | Toàn bộ |",
            "|---|---|---|---|",
            "| Tuổi (năm) | ___ ± ___ | ___ ± ___ | ___ ± ___ |",
            "| Giới nữ, n (%) | ___ (_) | ___ (_) | ___ (_) |",
            "| [CẦN thêm biến] | | | |",
            "",
            "> Không có cột p: không kiểm định ý nghĩa khác biệt nền giữa các nhóm đã ngẫu nhiên hoá "
            "(CONSORT 2010 E&E, PMID 20332511).",
            "",
            "**Bảng 2 — Kết cục chính:**",
            f"| Kết cục | {nhom1} | {nhom2} | Hiệu ứng (95%CI) |",
            "|---|---|---|---|",
            "| [CẦN KẾT QUẢ THẬT] | | | |",
        ]
    return [
        "**Bảng 1 — Đặc điểm nền:**",
        f"| Biến | {nhom1} | {nhom2} | p |",
        "|---|---|---|---|",
        "| Tuổi (năm) | ___ ± ___ | ___ ± ___ | ___ |",
        "| Giới nữ, n (%) | ___ (_) | ___ (_) | ___ |",
        "| [CẦN thêm biến] | | | |",
        "",
        "**Bảng 2 — Kết cục chính:**",
        "| Kết cục | N (%) / Trung vị | 95%CI | p |",
        "|---|---|---|---|",
        "| [CẦN KẾT QUẢ THẬT] | | | |",
    ]


def _thong_ke_mo_ta(design_code, loai12):
    """§3 — mô tả theo thiết kế (VÁ 04/10/2026, G4-06: bản cũ «so sánh đặc điểm nền t-test…» cho MỌI thiết kế)."""
    chung = [
        "- Biến liên tục: trung bình ± SD (phân phối chuẩn) hoặc trung vị [IQR] (lệch)  ",
        "- Biến phân loại: n (%)  ",
    ]
    if design_code == "qualitative":
        return ["- Đặc điểm người tham gia: mô tả tần số, không kiểm định thống kê (COREQ/SRQR)  "]
    if design_code == "rct":
        return chung + [
            "- Đặc điểm nền trình bày theo nhóm ngẫu nhiên hoá; KHÔNG kiểm định ý nghĩa khác biệt nền — khác biệt "
            "giữa các nhóm đã ngẫu nhiên hoá là do may rủi (CONSORT 2010 E&E, PMID 20332511)  ",
        ]
    if design_code in ("cohort", "case_control") or (design_code == "cross_sectional" and loai12 != "chinh_xac"):
        return chung + [
            "- So sánh đặc điểm nền giữa các nhóm: t-test / Mann-Whitney / Chi-square / Fisher (mô tả mất cân bằng; "
            "nhiễu xử lý ở §5)  ",
        ]
    if design_code == "diagnostic":
        return chung + ["- Mô tả người tham gia theo kết quả tiêu chuẩn tham chiếu (có bệnh/không bệnh) — STARD 2015  "]
    if design_code == "sr_ma":
        return ["- Mô tả đặc điểm các nghiên cứu được đưa vào (thiết kế, cỡ mẫu, quần thể, can thiệp) — PRISMA 2020  "]
    if design_code == "prediction":
        return chung + ["- Mô tả người tham gia ở tập phát triển (và tập kiểm định nếu có) — TRIPOD+AI  "]
    return chung + ["- Mô tả toàn mẫu; kết cục chính trình bày tỷ lệ kèm khoảng tin cậy 95%  "]


def _dong_muc_2(design_code, ket_cuc_chinh_da_chot=None):
    """Dòng §2 KẾT CỤC của SAP. Nhãn «Kết cục chính:» GIỮ cho MỌI thiết kế — G4-AUTO-11, G8-AUTO-05 và đối chiếu xuyên
    cổng (G10-AUTO-11) cùng đọc dòng này để truy điều đã định trước.

    ĐỊNH TÍNH (06/10/2026, bác sĩ yêu cầu «giải quyết theo hướng tốt nhất»): bản cũ in khuôn ĐỊNH LƯỢNG («ví dụ: tỷ lệ
    nhập viện…», «Đơn vị / ngưỡng», «Kết cục an toàn») cho cả đề tài định tính. Nay «Kết cục chính» là HIỆN TƯỢNG / CÂU
    HỎI NGHIÊN CỨU TRỌNG TÂM đã chốt ở G1 (điền sẵn — không hỏi lại điều đã chốt), kèm dòng diễn giải (SRQR: mục đích/câu
    hỏi nghiên cứu; không kiểm định giả thuyết); đơn vị/ngưỡng và kết cục an toàn KHÔNG ÁP DỤNG."""
    if design_code == "qualitative":
        chinh = str(ket_cuc_chinh_da_chot or "").strip() or (
            "[CẦN BÁC SĨ ĐIỀN — hiện tượng/câu hỏi nghiên cứu trọng tâm đã chốt ở G1, ví dụ: trải nghiệm của người bệnh "
            "về …]")
        return [
            f"- **Kết cục chính:** {chinh}  ",
            "- **Ý nghĩa với thiết kế định tính:** «kết cục chính» ở đây là HIỆN TƯỢNG / CÂU HỎI NGHIÊN CỨU TRỌNG TÂM đã "
            "định trước (SRQR — mục đích/câu hỏi nghiên cứu), không phải biến kiểm định giả thuyết; không có p-value/"
            "alpha. Phải khớp G1 và đề cương; đổi sau khi đã thu thập dữ liệu là sửa đổi phải giải trình công khai "
            "(gate_params.G10.sua_doi_ket_cuc_chinh).  ",
            "- **Đơn vị / ngưỡng:** KHÔNG ÁP DỤNG (định tính — không đo lường định lượng)  ",
            "- **Kết cục phụ 1:** [CẦN — câu hỏi/chủ đề nghiên cứu phụ, hoặc KHÔNG ÁP DỤNG]  ",
            "- **Kết cục phụ 2:** [CẦN — câu hỏi/chủ đề nghiên cứu phụ, hoặc KHÔNG ÁP DỤNG]  ",
            "- **Kết cục an toàn:** KHÔNG ÁP DỤNG (định tính) — rủi ro tâm lý khi phỏng vấn và cách xử trí nằm ở hồ sơ "
            "đạo đức G2  ",
        ]
    return [
        "- **Kết cục chính:** [CẦN BÁC SĨ ĐIỀN — ví dụ: tỷ lệ nhập viện tim mạch trong 12 tháng]  ",
        "- **Đơn vị / ngưỡng:** [CẦN]  ",
        "- **Kết cục phụ 1:** [CẦN]  ",
        "- **Kết cục phụ 2:** [CẦN]  ",
        "- **Kết cục an toàn:** [CẦN — đặc biệt với RCT]  ",
    ]


def generate(study, topic, design_code, design_primary, reporting_std,
             n_adjusted, alpha, power, effect_val, effect_type, run_date, sd=None,
             hypothesis_type="superiority", margin=None, n_statistical_min=None, *,
             g3=None, estimand=None, giai_trinh_thieu_luc=None, ket_cuc_chinh_da_chot=None):
    """Sinh SAP Final + chứng chỉ khoá (DRAFT — CHỜ KÝ).

    Tham số vị trí giữ nguyên hợp đồng cũ. Từ khoá mới (VÁ 04/10/2026, soát từng cổng):
      g3  — G3_checkpoint đầy đủ: sai số d/p ước lượng (thiết kế theo độ chính xác), p0, p_event, tỷ lệ bỏ cuộc, chiều
            kết cục NI, cụm (ICC/m/DE/số cụm), chẩn đoán (số ca bệnh/không bệnh, tỷ lệ hiện mắc), FPC — G4-06/G4-08.
      estimand — gate_params.G1.estimand (5 thuộc tính ICH E9(R1)) cho §4 của RCT — G4-03; vắng ⇒ ô [CẦN].
      giai_trinh_thieu_luc — gate_params.G3.underpowered_acceptance_justification khi N kế hoạch < N tối thiểu — G4-05.
      ket_cuc_chinh_da_chot — kết cục chính ĐÃ CHỐT ở G1 (rồi G0); thiết kế ĐỊNH TÍNH điền sẵn vào §2 (06/10/2026).
    """
    g3 = dict(g3 or {})
    loai12 = G4Q.loai_muc_12(design_code, {"effect_type": effect_type})
    sap_sections = {
        "rct": ("Nhóm can thiệp vs nhóm chứng", None, "t-test hoặc Mann-Whitney; logistic/log-rank"),
        "cohort": ("Nhóm phơi nhiễm vs không phơi nhiễm", "Phân tích đầy đủ (complete case + MI)", "Cox regression; logistic regression"),
        "cross_sectional": ("Toàn bộ mẫu đủ tiêu chí", "Phân tích đầy đủ", "Hồi quy logistic/tuyến tính"),
        "diagnostic": ("Bệnh nhân có xét nghiệm chỉ số và tiêu chuẩn vàng", "Phân tích đầy đủ", "ROC, AUC, độ nhạy/đặc hiệu"),
        "sr_ma": ("Tất cả nghiên cứu đủ tiêu chí đưa vào", "Phân tích đầy đủ", "Random/Fixed effects meta-analysis"),
        "case_control": ("Ca bệnh vs chứng ghép cặp", "Phân tích đầy đủ", "Conditional logistic regression"),
        # THÊM 2026-07-17 (round audit gate — tiếp nối vòng 5): "prediction"
        # (mô hình tiên lượng/TRIPOD+AI) trước đây rơi vào .get() fallback
        # ("Toàn bộ mẫu", "Phân tích đầy đủ", "[CẦN]") — an toàn (không bịa
        # phương pháp) nhưng mơ hồ. Nêu đúng thuật ngữ TRIPOD+AI thay vì để
        # trống hoàn toàn.
        "prediction": ("Người tham gia đủ tiêu chí phát triển/đánh giá mô hình",
                       "Phân tích đầy đủ (complete case + MI); internal validation qua bootstrap",
                       "Hồi quy logistic/Cox hoặc ML — discrimination (C-statistic) + "
                       "calibration + DCA (TRIPOD+AI)"),
        # THÊM 2026-07-20 (vòng lặp kiểm tra-hoàn thiện): trước rơi vào .get()
        # fallback ("Toàn bộ mẫu", "Phân tích đầy đủ", "[CẦN]") — an toàn
        # nhưng mơ hồ, cùng lớp thiếu sót vừa vá cho §5-§9 bên dưới.
        "qualitative": ("Người tham gia phỏng vấn/nhóm tiêu điểm đủ tiêu chí (chọn mẫu có chủ đích)",
                        "Toàn bộ bản ghi/bản gỡ băng đã mã hóa tới khi bão hòa dữ liệu",
                        "Mã hóa chủ đề (thematic analysis) — mở mã → mã trục → chủ đề "
                        "(COREQ/SRQR, xem A4)"),
    }
    pop, analysis_pop, main_method = sap_sections.get(design_code, ("Toàn bộ mẫu", "Phân tích đầy đủ", "[CẦN]"))
    # VÁ 04/10/2026 (điều phối G4↔G6, lộ khi soát G6-04): RCT/cohort từng in phương pháp CHUNG CHUNG theo thiết kế
    # («t-test hoặc Mann-Whitney; logistic/log-rank» cho mọi RCT) — không nói phân tích chính dùng thước đo nào trong khi
    # G3 đã chốt effect_type, nên G6 không có căn cứ đối chiếu họ mô hình của script với SAP. Nay chọn theo effect_type.
    if design_code in ("rct", "cohort"):
        main_method = {
            "HR": "Cox proportional hazards (HR) + Kaplan–Meier, log-rank cho so sánh thô",
            "RR": "Hồi quy Poisson với sai số chuẩn robust (hoặc log-binomial) → RR",
            "OR": "Hồi quy logistic → OR",
            "ARR%": "Hiệu nguy cơ (risk difference) + 95%CI; hiệu chỉnh: hồi quy nhị thức liên kết đồng nhất",
            "NI_PROPORTION": "Hiệu tỷ lệ (risk difference) + 95%CI (Newcombe) so với biên Δ",
            "MD": "t-test hoặc Mann-Whitney; ANCOVA/hồi quy tuyến tính hiệu chỉnh giá trị nền",
        }.get(str(effect_type or "").upper().replace("ARR", "ARR%").replace("%%", "%"), main_method)

    # THÊM 2026-07-24 (vòng 18): nhãn một/hai phía theo hypothesis_type — non_inferiority dùng z MỘT PHÍA.
    _alpha_sidedness = "one-sided" if hypothesis_type == "non_inferiority" else "two-sided"

    # THÊM 2026-07-19 (audit vòng 3, D1): sr_ma/prediction/qualitative — n_adjusted=0 CÓ CHỦ ĐÍCH (không dùng power);
    # N thật (nếu bác sĩ chốt qua --confirmed-n) đã được main() gán vào n_adjusted trước khi gọi.
    n_not_applicable = design_code in N_NOT_APPLICABLE_DESIGNS and not n_adjusted
    n_na_note = f"N/A — {design_code} không dùng power (xem A4)"
    effect_size_not_applicable = design_code in N_NOT_APPLICABLE_DESIGNS
    precision = g3.get("precision")
    do_tin_cay = _phan_tram(1 - float(alpha)) if alpha is not None else "[CẦN từ G3]"

    # ── §1: dòng cỡ mẫu theo cách N được quyết định ──
    if n_not_applicable:
        dong_co_mau_1 = f"- **Cỡ mẫu:** {n_na_note}  "
    elif not n_adjusted:
        dong_co_mau_1 = "- **Cỡ mẫu:** [CẦN từ G3]  "
    elif loai12 == "power":
        dong_co_mau_1 = f"- **Cỡ mẫu cuối:** N = {n_adjusted} (alpha={_so(alpha)}, power={_phan_tram(power)})  "
    elif loai12 == "chinh_xac":
        dong_co_mau_1 = (f"- **Cỡ mẫu cuối:** N = {n_adjusted} (độ tin cậy {do_tin_cay}, sai số tuyệt đối "
                         f"d = ±{_so(precision)})  ")
    else:
        dong_co_mau_1 = f"- **Cỡ mẫu cuối:** N = {n_adjusted} (phương pháp riêng của thiết kế — xem A4)  "
    # VÁ 04/10/2026 (soát từng cổng, G4-05): câu «N kế hoạch … lớn hơn mức tối thiểu» từng in chỉ với điều kiện hai số
    # KHÁC nhau — không xét CHIỀU — nên SAP ký khẳng định SAI khi chủ nhiệm chốt N THẤP hơn N tối thiểu (đề tài thiếu
    # lực). Nay rẽ nhánh theo chiều; chiều thấp hơn phải có giải trình của người thật (ô [CẦN] nếu chưa khai).
    dong_n_toi_thieu = []
    if n_statistical_min and n_adjusted and n_statistical_min != n_adjusted:
        if n_adjusted > n_statistical_min:
            dong_n_toi_thieu = [f"- **N tối thiểu theo thống kê (từ G3):** {n_statistical_min} — "
                                "N ở trên là cỡ mẫu KẾ HOẠCH do chủ nhiệm/Hội đồng chốt, lớn hơn mức tối thiểu.  "]
        else:
            he_qua = ("đề tài THIẾU LỰC THỐNG KÊ so với giả định ở G3" if loai12 == "power"
                      else "ước lượng KHÔNG đạt độ chính xác đã đặt ở G3")
            giai_trinh = str(giai_trinh_thieu_luc or "").strip()
            if not giai_trinh or "[CẦN" in giai_trinh.upper():
                giai_trinh = ("[CẦN THỐNG KÊ VIÊN/PI GIẢI TRÌNH — vì sao chấp nhận N thấp hơn, hệ quả lên diễn giải; "
                              "ghi gate_params.G3.underpowered_acceptance_justification]")
            dong_n_toi_thieu = [
                f"- **N tối thiểu theo thống kê (từ G3):** {n_statistical_min} — ⚠ N kế hoạch ở trên "
                f"{G4Q.NHAN_LOAI_THIEU_LUC}: {he_qua}.  ",
                f"- **Giải trình chấp nhận:** {giai_trinh}  ",
            ]

    # ── §4: phân tích chính; RCT có estimand + quần thể phân tích CHÍNH ──
    dong_muc4 = [f"- **Phương pháp:** {main_method}  "]
    if design_code == "rct":
        # VÁ 04/10/2026 (soát từng cổng, G4-03 ≡ G1-08): SAP RCT từng in cứng «ITT, PP» mà không nói cái nào CHÍNH và
        # không có estimand dù STANDARDS_BASIS tuyên bố đối chiếu ICH E9(R1). Nay in ĐÚNG estimand PI đã khai ở G1 (đặc
        # tả thiết kế khoá ở G1 — không suy lại); chưa khai ⇒ ô [CẦN]. Quần thể phân tích chính là quyết định người.
        est = estimand if isinstance(estimand, dict) else {}

        def _est(khoa, goi_y):
            gia_tri = str(est.get(khoa) or "").strip()
            return gia_tri if gia_tri else f"[CẦN — {goi_y}; khai ở gate_params.G1.estimand.{khoa}]"

        dong_muc4 += [
            "- **Estimand chính (ICH E9(R1); Kahan BC et al. BMJ 2024, PMID 38262663) — lấy từ G1:**  ",
            f"  - Quần thể (population): {_est('population', 'quần thể đích')}  ",
            f"  - Điều kiện điều trị so sánh: {_est('treatment_condition', 'can thiệp và đối chứng')}  ",
            f"  - Biến kết cục (variable): {_est('variable', 'kết cục chính')}  ",
            f"  - Biến cố xen ngang + chiến lược: {_est('intercurrent_events_strategy', 'biến cố và chiến lược')}  ",
            f"  - Thước đo tổng hợp quần thể: {_est('population_summary_measure', 'RR/OR/RD/HR/MD')}  ",
            "- **Quần thể phân tích CHÍNH:** [CẦN THỐNG KÊ VIÊN/PI CHỐT — phải khớp chiến lược biến cố xen ngang của "
            "estimand (vd treatment-policy ⇒ ITT); quần thể khác (vd per-protocol) chỉ là phân tích độ nhạy ở §9]  ",
        ]
    else:
        dong_muc4.append(f"- **Quần thể:** {analysis_pop}  ")
    icc, cluster_size, design_effect = g3.get("icc"), g3.get("cluster_size"), g3.get("design_effect")
    co_cum = icc is not None and cluster_size is not None
    if co_cum:
        dong_muc4.append(
            f"- **Hiệu chỉnh cụm:** phân tích chính phải tính cấu trúc cụm (DE = {_so(design_effect)}, ICC = {_so(icc)}, "
            f"m = {_so(cluster_size)}) — [CẦN THỐNG KÊ VIÊN chọn phương pháp, vd mô hình hiệu ứng hỗn hợp hoặc GEE]  ")
    if hypothesis_type in ("non_inferiority", "equivalence"):
        dong_muc4.append(
            f"- **Kết luận {'không kém hơn' if hypothesis_type == 'non_inferiority' else 'tương đương'}:** so cận khoảng "
            f"tin cậy với biên Δ = {_so(margin)} theo chiều kết cục {g3.get('outcome_direction') or '[CẦN từ G3]'} "
            "— không dựa vào p-value của kiểm định vượt trội  ")
    if design_code == "qualitative":
        dong_muc4.append("- **Trình bày:** chủ đề, chủ đề con và trích dẫn minh hoạ ẩn danh (COREQ/SRQR)  ")
    else:
        dong_muc4.append("- **Trình bày:** ước lượng + 95%CI; không báo p-value đơn độc  ")

    # THÊM 2026-07-20: §5-§9 cho định tính theo khung COREQ/SRQR (không MI/Bonferroni vô nghĩa).
    if design_code == "qualitative":
        sap_sections_5_to_9 = [
            "### §5 CHIẾN LƯỢC MÃ HÓA (thay Phân tích đa biến — không áp dụng cho định tính)",
            "",
            "- **Tiếp cận:** [CẦN BÁC SĨ — quy nạp (inductive)/diễn dịch (deductive)/hỗn hợp]  ",
            "- **Mã hóa:** [CẦN — số người mã hóa độc lập, phần mềm QDA (NVivo/ATLAS.ti/MAXQDA) hoặc mã tay theo codebook]  ",
            "- **Độ tin cậy liên-người-mã (nếu ≥2 người):** [CẦN — Cohen's kappa hoặc thảo luận đồng thuận]  ",
            "",
            "### §6 BÃO HÒA DỮ LIỆU (thay Dữ liệu thiếu — không áp dụng cho định tính)",
            "",
            "- **Tiêu chí bão hòa:** [CẦN BÁC SĨ — vd không còn mã/chủ đề mới sau N cuộc phỏng vấn liên tiếp]  ",
            "- **Cỡ mẫu dự kiến:** xem A4 (chọn mẫu có chủ đích, không tính power)  ",
            "",
            "### §7 CHỌN MẪU ĐA DẠNG (thay Phân tích nhóm nhỏ — không áp dụng cho định tính)",
            "",
            "- **Chiến lược chọn mẫu:** [CẦN BÁC SĨ — purposive/maximum variation/theoretical sampling]  ",
            "- **Tiêu chí đa dạng:** [CẦN — vd tuổi, giới, mức độ nặng bệnh, thời gian mắc bệnh]  ",
            "",
            "### §8 KHÔNG ÁP DỤNG (Đa so sánh — chỉ dành cho kiểm định giả thuyết thống kê)",
            "",
            "- Nghiên cứu định tính không kiểm định giả thuyết bằng p-value → không có đa so sánh cần hiệu chỉnh.  ",
            "",
            "### §9 TRUSTWORTHINESS (thay Phân tích độ nhạy — khung Lincoln & Guba cho định tính)",
            "",
            "- **Credibility:** [CẦN — member checking / triangulation nguồn dữ liệu]  ",
            "- **Transferability:** [CẦN — mô tả bối cảnh dày (thick description)]  ",
            "- **Dependability:** [CẦN — audit trail quá trình mã hóa]  ",
            "- **Confirmability:** [CẦN — nhật ký phản tư (reflexivity journal)]  ",
            "",
        ]
        muc_10 = [
            "### §10 PHẦN MỀM + SEED",
            "",
            "- **Phần mềm:** [CẦN — phần mềm phân tích định tính và phiên bản (vd NVivo 14 / ATLAS.ti 23 / "
            "MAXQDA 2022) hoặc mã tay theo codebook]  ",
            "- **Packages:** KHÔNG ÁP DỤNG (định tính)  ",
            "- **Random seed:** KHÔNG ÁP DỤNG — định tính không có bước ngẫu nhiên trong phân tích  ",
            "",
        ]
    else:
        sap_sections_5_to_9 = [
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
        ]
        muc_10 = [
            "### §10 PHẦN MỀM + SEED",
            "",
            "- **Phần mềm:** [CẦN — R v4.x / Stata v18 / SPSS v29]  ",
            "- **Packages:** [CẦN — survival, lme4, mice, gtsummary...]  ",
            "- **Random seed:** [CẦN BÁC SĨ ẤN ĐỊNH — ví dụ: set.seed(2026)]  ",
            "",
        ]

    # THÊM 2026-09-06 (bác sĩ duyệt «thêm mục 13–15 có điều kiện»): SPIRIT 2025 28b/28a/17/15b/15c CHỈ cho RCT — nối SAU
    # §12, KHÔNG đánh số lại §1-§12. VÁ 04/10/2026 (soát từng cổng, G4-02 — QĐ-1): §13/§14/§15 nay BẮT BUỘC khi ký SAP
    # RCT (approve_gate._G4_REQUIRED_SECTIONS_RCT) — doctrine thiet-ke-nghien-cuu đã dạy «đạt G4 khi 15 mục nếu RCT».
    sap_sections_13_to_15 = [
        "",
        "### §13 PHÂN TÍCH GIỮA KỲ VÀ QUY TẮC DỪNG (SPIRIT 2025 mục 28b)",
        "",
        "- **Có phân tích giữa kỳ:** [CẦN BÁC SĨ/THỐNG KÊ VIÊN — có/không; nếu có, số lần và mốc "
        "(thời gian hoặc % cỡ mẫu đã thu)]  ",
        "- **Quy tắc dừng (stopping rule):** [CẦN — vd O'Brien-Fleming/Pocock, ngưỡng alpha spending]  ",
        "- **Ai xem kết quả giữa kỳ và ai quyết định dừng:** [CẦN — thường là DMC/DSMB độc lập, "
        "KHÔNG phải nghiên cứu viên chính]  ",
        "- Nếu KHÔNG có phân tích giữa kỳ: [CẦN — nêu lý do, vd thời gian theo dõi ngắn/cỡ mẫu nhỏ/"
        "can thiệp nguy cơ thấp]  ",
        "",
        "### §14 HỘI ĐỒNG THEO DÕI DỮ LIỆU (DMC/DSMB, SPIRIT 2025 mục 28a)",
        "",
        "- **Có DMC/DSMB:** [CẦN — có/không]  ",
        "- **Thành phần và vai trò:** [CẦN — số thành viên, chuyên môn, cơ chế báo cáo]  ",
        "- **Độc lập với nhà tài trợ/nghiên cứu viên:** [CẦN — xác nhận độc lập + khai xung đột "
        "lợi ích]  ",
        "- **Điều lệ (charter):** [CẦN — trích dẫn/đính kèm, hoặc ghi rõ chưa lập và vì sao]  ",
        "- Nếu KHÔNG cần DMC/DSMB: [CẦN — giải thích lý do được chấp nhận theo SPIRIT 2025, vd "
        "can thiệp nguy cơ thấp/thời gian ngắn]  ",
        "",
        "### §15 TỔN HẠI; NGỪNG/ĐỔI CAN THIỆP VÀ TUÂN THỦ (SPIRIT 2025 mục 17, 15b, 15c)",
        "",
        "- **Định nghĩa tổn hại (harms):** [CẦN — thang phân độ biến cố bất lợi dùng, vd CTCAE]  ",
        "- **Cách đánh giá:** [CẦN — hệ thống (hỏi chủ động mỗi lần khám) hay không hệ thống "
        "(người tham gia tự báo cáo)]  ",
        "- **Tiêu chí ngừng/đổi can thiệp cho MỘT người tham gia:** [CẦN — vd đổi liều khi có tác "
        "dụng phụ, tiêu chí rút khỏi nghiên cứu — khác quy tắc dừng CẢ nghiên cứu ở §13]  ",
        "- **Chiến lược cải thiện và theo dõi tuân thủ:** [CẦN — vd đếm viên thuốc hoàn trả, số "
        "buổi tham dự]  ",
        "",
    ]

    # ── §12 + chứng chỉ khoá theo khung (G4-06/G4-08) ──
    dong_n_12 = (f"- **Cỡ mẫu:** {n_na_note}  " if n_not_applicable else
                 (f"- **Cỡ mẫu:** N = {n_adjusted}  " if n_adjusted else "- **Cỡ mẫu:** [CẦN từ G3]  "))
    if loai12 == "dinh_tinh":
        tieu_de_12 = "### §12 KHÔNG KIỂM ĐỊNH GIẢ THUYẾT (định tính)"
        muc_12 = [
            "- **Alpha:** KHÔNG ÁP DỤNG — định tính không kiểm định giả thuyết bằng p-value  ",
            "- **Power:** KHÔNG ÁP DỤNG — cỡ mẫu theo bão hoà dữ liệu (xem §6 và A4)  ",
            dong_n_12,
            f"- **Effect size:** N/A — {design_code} không dùng effect size  ",
        ]
    elif loai12 == "khong_power":
        tieu_de_12 = "### §12 ALPHA + CỠ MẪU (không dùng power của G3)"
        muc_12 = [
            f"- **Alpha ({_alpha_sidedness}):** {_so(alpha)}  ",
            f"- **Power:** KHÔNG ÁP DỤNG cho công thức của G3 — {design_code} dùng phương pháp riêng (xem A4)  ",
            dong_n_12,
            f"- **Effect size:** N/A — {design_code} không dùng effect size  ",
        ]
    elif loai12 == "chinh_xac":
        tieu_de_12 = "### §12 ALPHA + ĐỘ CHÍNH XÁC (cỡ mẫu theo sai số cho phép)"
        muc_12 = [
            f"- **Alpha ({_alpha_sidedness}):** {_so(alpha)} — độ tin cậy {do_tin_cay}  ",
            f"- **Tỷ lệ ước lượng (p):** {_so(effect_val)}  ",
            f"- **Sai số tuyệt đối cho phép (d):** ±{_so(precision)}  ",
            dong_n_12,
            "- **Power:** không dùng — cỡ mẫu theo độ chính xác của ước lượng, không kiểm định giả thuyết  ",
        ]
    else:
        tieu_de_12 = "### §12 ALPHA + POWER"
        muc_12 = [
            f"- **Alpha ({_alpha_sidedness}):** {_so(alpha)}  ",
            f"- **Power:** {_phan_tram(power)}  ",
            dong_n_12,
            (f"- **Effect size:** N/A — {design_code} không dùng effect size  " if effect_size_not_applicable else
             (f"- **Effect size dự kiến:** {effect_type} = {_so(effect_val)}  " if effect_val is not None
              else "- **Effect size:** [CẦN từ G3]  ")),
        ]
        if hypothesis_type in ("non_inferiority", "equivalence"):
            # THÊM 2026-07-24 (vòng 18): margin Δ phải có trong SAP được ký. VÁ 04/10/2026: chỉ NI/tương đương —
            # cắt ngang phân tích có hypothesis_type=descriptive_precision từng bị in khối margin «[CẦN từ G3]».
            muc_12 += [f"- **Loại giả thuyết:** {hypothesis_type}  ",
                       f"- **Biên (margin, Δ):** {_so(margin)} "
                       "— [CẦN Hội đồng/thống kê viên xác nhận biện minh lâm sàng TRƯỚC KHI KÝ]  "]
            if g3.get("outcome_direction"):
                muc_12.append(f"- **Chiều kết cục:** {g3.get('outcome_direction')}  ")
        if effect_type == "MD":
            # THÊM 2026-07-06: SD bắt buộc để tái tạo cỡ mẫu kết cục liên tục.
            muc_12.append(f"- **Độ lệch chuẩn (SD) kết cục:** {_so(sd)}  " if sd is not None
                          else "- **SD kết cục:** [CẦN từ G3 — bắt buộc khi effect_type=MD]  ")
        for khoa, nhan in (("p0", "Tỷ lệ biến cố nhóm chứng (p0)"), ("p_event", "Tỷ lệ biến cố (log-rank, p_event)")):
            if g3.get(khoa) is not None:
                muc_12.append(f"- **{nhan}:** {_so(g3.get(khoa))}  ")
        if design_code == "diagnostic" and g3.get("n_benh") is not None:
            muc_12 += [f"- **Số ca bệnh cần:** {g3.get('n_benh')}  ",
                       f"- **Số ca không bệnh cần:** {g3.get('n_khong_benh')}  ",
                       f"- **Tỷ lệ hiện mắc dự kiến:** {_so(g3.get('prevalence'))}  "]
    if loai12 != "dinh_tinh" and g3.get("dropout") is not None:
        muc_12.append(f"- **Tỷ lệ bỏ cuộc dự kiến:** {_so(g3.get('dropout'))}  ")
    if co_cum:
        muc_12 += [f"- **Hiệu ứng thiết kế (DE):** {_so(design_effect)}  ",
                   f"- **ICC:** {_so(icc)}  ",
                   f"- **Cỡ cụm trung bình (m):** {_so(cluster_size)}  "]
        if g3.get("n_clusters") is not None:
            muc_12.append(f"- **Số cụm:** {g3.get('n_clusters')}  ")
    if g3.get("population_n") is not None:
        muc_12.append(f"- **Quần thể hữu hạn (FPC):** N = {g3.get('population_n')}  ")

    dong_co_mau_cc = (f"║ Cỡ mẫu   : {n_na_note:<49} ║" if n_not_applicable else
                      (f"║ Cỡ mẫu   : N = {str(n_adjusted):<45} ║" if n_adjusted
                       else "║ Cỡ mẫu   : [CẦN từ G3]                                      ║"))
    def _o_khung(nhan, gia_tri):
        return f"║ {nhan:<10}: {gia_tri:<48} ║"

    if loai12 == "dinh_tinh":
        chung_chi_so = [_o_khung("Alpha", "KHÔNG ÁP DỤNG (định tính)"),
                        _o_khung("Power", "KHÔNG ÁP DỤNG (bão hoà dữ liệu)")]
    elif loai12 == "khong_power":
        chung_chi_so = [_o_khung("Alpha", f"{_so(alpha)} ({_alpha_sidedness})"),
                        _o_khung("Power", "KHÔNG ÁP DỤNG (xem A4)")]
    elif loai12 == "chinh_xac":
        chung_chi_so = [_o_khung("Alpha", f"{_so(alpha)} (độ tin cậy {do_tin_cay})"),
                        _o_khung("Sai số d", f"±{_so(precision)} (p = {_so(effect_val)})")]
    else:
        chung_chi_so = [f"║ Alpha     : {_so(alpha)} ({_alpha_sidedness})                                  ║",
                        f"║ Power     : {_phan_tram(power)}                                            ║"]
        if effect_type == "MD":
            chung_chi_so.append(f"║ SD kết cục: {_so(sd):<48} ║" if sd is not None
                                else "║ SD kết cục: [CẦN từ G3 — bắt buộc khi effect_type=MD]       ║")
        if hypothesis_type in ("non_inferiority", "equivalence"):
            chung_chi_so += [f"║ Giả thuyết: {hypothesis_type:<48} ║",
                             f"║ Margin (Δ): {_so(margin):<48} ║"]

    muc_bat_buoc = "§1/§2/§4/§5/§9/§10" + ("/§13/§14/§15" if design_code == "rct" else "")
    vai_tro_ky = GC.required_reviewer_role_hint("G4")
    lines = [
        "# A5 — SAP FINAL + SAP LOCK CERTIFICATE (DRAFT — CHỜ BÁC SĨ KÝ)",
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
        "| Mục | Nội dung |",
        "|---|---|",
        f"| Tên đề tài | {topic} |",
        f"| Mã nghiên cứu | {study} |",
        f"| Thiết kế | {design_primary} |",
        f"| Chuẩn báo cáo | {reporting_std} |",
        f"| Ngày soạn SAP | {run_date} |",
        "| Phiên bản | 1.0 |",
        "",
        "---",
        "",
        "## PHẦN 2 — LỊCH SỬ PHIÊN BẢN SAP",
        "",
        "| Phiên bản | Ngày | Người soạn | Thay đổi chính |",
        "|---|---|---|---|",
        f"| 1.0 | {run_date} | [CẦN TÊN TÁC GIẢ] | Bản đầu tiên (tự động từ G1) |",
        "",
        "---",
        "",
        f"## PHẦN 3 — SAP {'15' if design_code == 'rct' else '12'} MỤC CUỐI",
        "",
        "### §1 QUẦN THỂ PHÂN TÍCH",
        "",
        f"- **Quần thể chính:** {pop}  ",
        # THÊM 06/09/2026: RCT trỏ NGƯỢC sang đề cương §6.2 (TIDieR) thay vì chép lại.
        *(["- **Mô tả can thiệp/đối chứng (TIDieR):** xem đề cương thống nhất "
           "§6.2 Can thiệp và đối chứng — không lặp lại ở đây để tránh hai nơi "
           "cùng một sự thật dễ lệch nhau.  "] if design_code == "rct" else []),
        dong_co_mau_1,
        *dong_n_toi_thieu,
        "- **Tiêu chí nhận:** [CẦN BÁC SĨ ĐIỀN — từ đề cương]  ",
        "- **Tiêu chí loại:** [CẦN BÁC SĨ ĐIỀN]  ",
        "",
        "### §2 KẾT CỤC",
        "",
        *_dong_muc_2(design_code, ket_cuc_chinh_da_chot),
        "",
        "### §3 THỐNG KÊ MÔ TẢ",
        "",
        *_thong_ke_mo_ta(design_code, loai12),
        "",
        "### §4 PHÂN TÍCH CHÍNH",
        "",
        *dong_muc4,
        "",
        *sap_sections_5_to_9,
        *muc_10,
        "### §11 DUMMY TABLES (Khung bảng kết quả)",
        "",
        *_bang_gia(design_code, loai12),
        "",
        tieu_de_12,
        "",
        *muc_12,
        *(sap_sections_13_to_15 if design_code == "rct" else []),
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
        dong_co_mau_cc,
        *chung_chi_so,
        "║ KQ chính  : [CẦN BÁC SĨ ĐIỀN — từ SAP §2]                 ║",
        "║ Phân tích : [CẦN BÁC SĨ ĐIỀN — quần thể phân tích]        ║",
        "╠══════════════════════════════════════════════════════════════╣",
        "║ TRẠNG THÁI: DRAFT — CHỜ KÝ                                 ║",
        "╠══════════════════════════════════════════════════════════════╣",
        "║ Chủ nhiệm đề tài: _________________________ Ngày: ___/___/ ║",
        "║ Đồng tác giả:     _________________________ Ngày: ___/___/ ║",
        "╚══════════════════════════════════════════════════════════════╝",
        "",
        # VÁ 04/10/2026 (soát từng cổng, G4-11): hướng dẫn cũ «Cung cấp ngày ký → hệ thống ghi G4_STATUS: LOCKED» trái
        # cơ chế thật — chốt khoá là bản ghi phê duyệt có niêm phong do thống kê viên/PI TỰ ký bằng approve_gate.py.
        "  → Ký số: thống kê viên/PI TỰ chạy approve_gate.py --gate G4 (sổ cái phê duyệt có niêm phong)",
        "  → Bản giấy có chữ ký (nếu đơn vị yêu cầu): scan lưu exports/<study>/G4_SAP_SIGNED.pdf",
        "  → Chỉ khi sổ cái có phê duyệt G4 hợp lệ mới được xem dữ liệu (G5→G6)",
        "```",
        "",
        "---",
        "",
        "## PHẦN 6 — TIÊU CHÍ QUA CỔNG G4 + CƠ CHẾ MỞ KHÓA",
        "",
        "**Để G4 đạt PASS_G4_SAP_LOCKED:**",
        f"1. Điền TẤT CẢ ô [CẦN...] ở các mục bắt buộc {muc_bat_buoc} và ở chứng chỉ khoá (Phần 5); "
        "không xoá mục bắt buộc nào",
        f"2. Chạy `python3 tools/g4_quality_gate.py --study {study}` — trạng thái phải là READY_FOR_SIGNATURE "
        "(G3 đã chốt PASS_G3_CONFIRMED, số liệu ký khớp G3)",
        "3. Thống kê viên/PI ghi xác nhận vào study_meta.json → gate_params.G4 (epv_vif_reviewed, "
        "missing_data_mechanism_confirmed, subgroup_multiplicity_predefined_confirmed, reviewed_by_role, reviewed_at "
        "ISO-8601, dau_van_tay_chot = dấu nội dung SAP mà bộ chấm in)",
        f"4. Thống kê viên/PI TỰ ký: `python3 tools/approve_gate.py --study {study} --gate G4 --artifact "
        f"exports/{study}/G4_A5_SAP_FINAL_{study}.md --reviewer-role <{vai_tro_ky}> --reviewer-ref <mã người duyệt>` "
        "— hệ thống KHÔNG tự ghi trạng thái khoá",
        "",
        "**Chỉ sau khi G4 được ký trên sổ cái:**",
        "- Mới được mở dữ liệu (G5)",
        "- Mới được chạy phân tích chính (G6)",
        "- Mọi phân tích trước khi ký bị coi là 'thăm dò'",
        "",
        "---",
        "*Cần bác sĩ kiểm chứng. SAP này chỉ có hiệu lực pháp lý sau khi được ký.*",
    ]
    return "\n".join(lines)

def _ket_cuc_chinh_da_chot(meta):
    """Kết cục chính đã chốt — G1 (ghim có cấu trúc {name,…}) rồi G0; CÙNG cách G4-AUTO-11 đọc để đối chiếu §2."""
    gp = (meta.get("gate_params") or {}) if isinstance(meta, dict) else {}
    for cong in ("G1", "G0"):
        v = (gp.get(cong) or {}).get("primary_outcome") if isinstance(gp.get(cong), dict) else None
        if isinstance(v, dict):
            v = v.get("name") or v.get("text")
        if str(v or "").strip():
            return str(v).strip()
    return None


def write_docx(artifact, path):
    try:
        from docx import Document
        from docx.shared import RGBColor
        doc = Document()
        for line in artifact.split("\n"):
            if line.startswith("# "):
                doc.add_heading(line[2:], 0)
            elif line.startswith("## "):
                doc.add_heading(line[3:], 1)
            elif line.startswith("### "):
                doc.add_heading(line[4:], 2)
            elif "[CẦN" in line:
                p = doc.add_paragraph()
                p.add_run(line).font.color.rgb = RGBColor(0xCC, 0x44, 0x00)
            elif line.strip():
                doc.add_paragraph(line)
        _CTB.ap_dinh_dang_tai_lieu(doc)  # chuẩn trình bày: Times New Roman 13pt + sạch ký tự lạ
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
    # THÊM 2026-09-01 (kiểm toàn diện): cờ ghi đè CÓ CHỦ ĐÍCH cho rào chống
    # đè SAP đã biên tập (xem khối rào trước md.write_text bên dưới).
    parser.add_argument("--regenerate-sap", action="store_true",
                        help="Ép sinh lại SAP từ template dù bản đang có đầy đủ hơn "
                             "(bản cũ vẫn được sao lưu .bak-* trước khi đè)")
    args = parser.parse_args()
    GC.ensure_utf8_stdout()
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
    # VÁ 2026-07-27: dùng bộ giải quyết DÙNG CHUNG. Trước đây cổng này chỉ đọc
    # G1_checkpoint rồi mặc định "cohort", nên `--design` bác sĩ truyền TƯỜNG MINH ở
    # G2 bị NUỐT — chuẩn báo cáo/công thức cỡ mẫu chọn sai mà không cảnh báo.
    # Xem gate_contract.resolve_design_code().
    design_code, _design_warn = GC.resolve_design_code(out)
    if _design_warn:
        print(_design_warn)
    # VÁ 04/10/2026 (soát từng cổng, CHUNG-F): mặc định im lặng «Cohort tiến cứu»/«STROBE 2007» từng in vào SAP của MỌI
    # thiết kế khi G1 thiếu khoá — một RCT tự khai là cohort. Nay chuẩn báo cáo lấy theo thiết kế đã giải quyết; mô tả
    # thiết kế vắng ⇒ ô [CẦN].
    design_primary = g1_design.get("primary") or f"{design_code} — [CẦN mô tả thiết kế từ G1]"
    reporting_std = g1_design.get("reporting_standard") or S.reporting_standards_for(design_code).get("primary")
    # SỬA: n_adjusted có thể là string nếu checkpoint bị ghi/sửa bởi nguồn
    # khác (vd tay sửa JSON) — "n_adjusted <= 0" crash TypeError khi so sánh
    # str với int. Ép kiểu an toàn, giá trị không hợp lệ → coi như 0 (sẽ bị
    # hard-stop chặn ngay dưới, không lan truyền số rác).
    try:
        n_adjusted = int(g3.get("n_adjusted") or 0)
    except (TypeError, ValueError):
        n_adjusted = 0
    # THÊM 2026-07-19 (audit vòng 3, D1 — NGHIÊM TRỌNG, xác nhận thực nghiệm
    # G3→G4 thật): với sr_ma/prediction/qualitative, n_adjusted (kết quả
    # công thức power/effect size) LUÔN 0 CÓ CHỦ ĐÍCH — N thật (nếu bác sĩ đã
    # tự tính NGOÀI hệ thống bằng RIS/pmsampsize/bão hòa dữ liệu) nằm ở
    # `confirmed_n` (G3 ghi vào checkpoint khi chạy `--confirmed-n`). Dùng
    # confirmed_n làm N hiệu lực cho 3 thiết kế này — KHÔNG đổi hành vi cho
    # thiết kế khác (rct/cohort/... vẫn chỉ dùng n_adjusted như cũ).
    try:
        confirmed_n = int(g3.get("confirmed_n")) if g3.get("confirmed_n") is not None else None
    except (TypeError, ValueError):
        confirmed_n = None
    # SỬA 2026-07-31 (đề tài THẬT đầu tiên đi qua G4 — hài lòng người bệnh C1a):
    # trước đây confirmed_n CHỈ được dùng cho sr_ma/prediction/qualitative, còn
    # mọi thiết kế khác luôn lấy n_adjusted. Nhưng trường hợp "chủ nhiệm/Hội đồng
    # chốt N LỚN HƠN N tối thiểu" là rất phổ biến (khả năng thu thập, yêu cầu
    # hành chính, biên an toàn cho outcome lệch phân bố). Khi đó SAP — tài liệu
    # ĐƯỢC KÝ VÀ KHÓA — ghi N tối thiểu thay vì N thật sẽ thu, nên phân tích sau
    # này trên N thật sẽ lệch khỏi chính SAP đã khóa. Với C1a: SAP ghi N=453
    # trong khi đề cương và Hội đồng chốt n=1000.
    # N hiệu lực nay là confirmed_n cho MỌI thiết kế; n_adjusted vẫn được in kèm
    # để không mất thông tin "N tối thiểu theo thống kê".
    n_statistical_min = n_adjusted
    if confirmed_n:
        n_adjusted = confirmed_n
    # VÁ 04/10/2026 (soát từng cổng, CHUNG-F/G4-06): «alpha or 0.05», «power or 0.80», «effect_type or "HR"» là giá trị
    # mặc định IM LẶNG trong văn bản sẽ KÝ. G3 (từ 04/10) luôn ghi alpha/power kèm nguồn; vắng ⇒ SAP in [CẦN từ G3].
    alpha = g3.get("alpha")
    power = g3.get("power")
    effect_val = g3.get("effect_val")
    effect_type = g3.get("effect_type")
    sd = g3.get("sd")  # THÊM 2026-07-06: SD kết cục liên tục (effect_type=MD), từng bị rớt khi truyền G3→G4
    # THÊM 2026-07-24 (vòng lặp kiểm tra-hoàn thiện vòng 18, phát hiện HIGH):
    # hypothesis_type/margin bị RỚT khi truyền G3→G4 — cùng lớp lỗi với SD
    # ở trên (2026-07-06), nay áp cùng cách vá.
    hypothesis_type = g3.get("hypothesis_type") or "superiority"
    margin = g3.get("margin")

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
            json.dumps(cp, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
        print(f"   → {GC.blocked_detail(cp)}")
        print("   💾 Đã ghi G4_checkpoint.json (BLOCKED) để pipeline đọc remediation.")
        raise SystemExit(GC.EXIT_BLOCKED)

    # VÁ 04/10/2026 (soát từng cổng, G4-04 ≡ G3-05): run_g3_auto ghi G3_checkpoint (kèm N) TRƯỚC khi chấm rồi mới thoát
    # mã 3 khi BLOCKED ⇒ G4 từng sinh (và cho ký) SAP khoá một N mà chính G3 đánh giá là sai. Nay CHẤM SỐNG G3: bị chặn
    # ⇒ TỪ CHỐI sinh SAP, ghi checkpoint DỪNG trỏ về G3; chưa chốt ⇒ vẫn sinh bản DỰ THẢO để soạn song song nhưng nói rõ
    # G4 không ký được tới khi G3 = PASS_G3_CONFIRMED (g4_quality_gate G4-AUTO-12).
    g3_song = CS.trang_thai_song("G3", study, out, repo_root=BASE)
    if g3_song.get("muc") == "BLOCKED":
        _bc3 = g3_song.get("bao_cao") if isinstance(g3_song.get("bao_cao"), dict) else {}
        _chan3 = [str(r.get("id")) for r in _bc3.get("automatic_criteria") or []
                  if isinstance(r, dict) and r.get("status") == "BLOCK"]
        print(f"🚧 G4 DỪNG: G3 chấm sống = BLOCKED ({', '.join(_chan3) or g3_song.get('ly_do')}) — không khoá SAP "
              "trên cỡ mẫu bị chặn.")
        need = GC.needs_input(
            GC.REASON_MISSING_SAMPLE_SIZE,
            "G4 (khóa SAP) không sinh SAP vì G3 (cỡ mẫu) đang BỊ CHẶN khi chấm sống — N trong G3_checkpoint chưa hợp "
            "lệ. Xử lý các mục BLOCK của G3 trước.",
            f"python3 tools/g3_quality_gate.py --study {study}",
            must_not_fabricate=["n_adjusted", "effect_size", "PMID"],
        )
        cp = {
            "gate": "G4", "study": study, "run_date": run_date,
            "g4_status": "BLOCKED — G3 BỊ CHẶN KHI CHẤM SỐNG",
            "g4_sap_version": None, "g4_lock_date": None,
            "n_from_g3": n_adjusted, "design_code": design_code,
            "g3_trang_thai_luc_sinh": g3_song.get("status"),
            "guardrail": GC.BLOCKED_GUARDRAIL_STR,
            "core_value": GC.core_value("n_from_g3", n_adjusted, is_empty=True),
            "needs_input": need,
            "pending_doctor_actions": ["Xử lý mục BLOCK của G3 (g3_quality_gate.py) rồi chạy lại G3 → G4"],
        }
        (out / "G4_checkpoint.json").write_text(
            json.dumps(cp, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
        print("   💾 Đã ghi G4_checkpoint.json (BLOCKED) — remediation trỏ về G3.")
        raise SystemExit(GC.EXIT_BLOCKED)
    if g3_song.get("muc") != "PASS":
        print(f"  ⚠ G3 chấm sống = {g3_song.get('status')} — SAP sinh ra là DỰ THẢO để soạn song song; G4 KHÔNG ký "
              "được tới khi G3 = PASS_G3_CONFIRMED (thống kê viên/PI xác nhận tham số cỡ mẫu).")

    print(f"  → Topic: {topic[:60]}")
    print(f"  → Design: {design_code} | N={n_adjusted}")

    meta_cp = GC.load_study_meta(out)
    g3_meta = ((meta_cp.get("gate_params") or {}).get("G3") or {}) if isinstance(meta_cp, dict) else {}
    artifact = generate(study, topic, design_code, design_primary, reporting_std,
                        n_adjusted, alpha, power, effect_val, effect_type, run_date, sd,
                        hypothesis_type=hypothesis_type, margin=margin,
                        n_statistical_min=n_statistical_min,
                        g3=g3, estimand=S.dac_ta_thiet_ke(out).get("estimand"),
                        giai_trinh_thieu_luc=g3_meta.get("underpowered_acceptance_justification"),
                        ket_cuc_chinh_da_chot=_ket_cuc_chinh_da_chot(meta_cp))
    md = out / f"G4_A5_SAP_FINAL_{study}.md"
    # SAP là tài liệu bác sĩ/thống kê viên ĐỌC RỒI KÝ, nên chuẩn hoá văn phong
    # trước khi ghi. keep_box=True: khung của SAP LOCK CERTIFICATE đóng vai con
    # dấu, giữ nguyên có chủ đích (tools/vn_prose_style.py).
    artifact = _VNSTYLE.clean_generated_prose(artifact, keep_box=True)
    # ★ RÀO CHỐNG ĐÈ MẤT SAP ĐÃ BIÊN TẬP (kiểm toàn diện 01/09/2026): trước
    # bản vá này md.write_text() đè VÔ ĐIỀU KIỆN — không sao lưu, không rào.
    # Ca thật suýt xảy ra: SAP v1.1 của C1a (12 mục đồng bộ từ đề cương đã
    # duyệt, 12/13 tiêu chí G4 PASS) sẽ bị thay bằng template [CẦN] trống nếu
    # ai chạy lại G4 — kể cả chỉ để xoá cảnh báo freshness của run_pipeline.
    # Luật nội dung 21/08 (họ BH71): bản đích ĐẦY ĐỦ HƠN bản máy sắp sinh
    # (ÍT nhãn [CẦN hơn) → TỪ CHỐI đè; chỉ người thật quyết bằng
    # --regenerate-sap (vẫn sao lưu .bak-* trước). SAP cũ KÉM đầy đủ hơn →
    # đè như cũ nhưng nay LUÔN có .bak-* (cùng khuôn G0 đã làm từ 28/07).
    if md.exists():
        ban_cu = md.read_text(encoding="utf-8")
        bak = md.with_name(md.name + f".bak-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
        bak.write_text(ban_cu, encoding="utf-8", newline="\n")
        print(f"  → Sao lưu SAP hiện có: {bak.name}")
        if (ban_cu.count("[CẦN") < artifact.count("[CẦN")
                and not getattr(args, "regenerate_sap", False)):
            print("⛔ TỪ CHỐI đè SAP: bản đang có ĐẦY ĐỦ HƠN bản máy sắp sinh "
                  f"({ban_cu.count('[CẦN')} vs {artifact.count('[CẦN')} nhãn [CẦN...]) — "
                  "nhiều khả năng đã được bác sĩ/thống kê viên biên tập.")
            print("   Muốn sinh lại từ template CÓ CHỦ ĐÍCH: thêm cờ --regenerate-sap "
                  "(bản cũ vẫn được sao lưu .bak-* ở trên).")
            print("   Chỉ cần bản .docx CHUẨN TRÌNH BÀY từ bản đã biên tập (không sinh lại nội dung):\n"
                  f"     python3 tools/xuat_docx_chuan.py --study {study}")
            raise SystemExit(GC.EXIT_BLOCKED)
    md.write_text(artifact, encoding="utf-8", newline="\n")
    print(f"  → Lưu: {md} ({len(artifact)//1000}KB)")

    print("🛡️  Kiểm guardrail...")
    errors, warnings = guardrail(artifact)
    for w in warnings:
        print(f"  {w}")
    for e in errors:
        print(f"  {e}")
    status = "✅ PASS" if not errors else f"⚠ {len(errors)} LỖI"
    print(f"  → Guardrail: {status}")

    docx = out / f"G4_A5_SAP_FINAL_{study}.docx"
    write_docx(artifact, docx)
    print(f"  → DOCX: {docx}")

    muc_bat_buoc = "§1/§2/§4/§5/§9/§10" + ("/§13/§14/§15" if design_code == "rct" else "")
    cp = {
        "gate": "G4", "study": study, "run_date": run_date,
        "g4_status": "PENDING — CHỜ BÁC SĨ KÝ SAP",
        "g4_sap_version": "1.0", "g4_lock_date": None,
        "n_from_g3": n_adjusted, "alpha": alpha, "power": power,
        "design_code": design_code, "reporting_standard": reporting_std,
        "loai_muc_12": G4Q.loai_muc_12(design_code, g3),
        "g3_trang_thai_luc_sinh": g3_song.get("status"),
        "guardrail": status,
        # VÁ 04/10/2026 (soát từng cổng, G4-11): danh sách cũ bỏ sót §1/§4/§6–§9 và dạy «cung cấp ngày ký → ghi
        # G4_STATUS=LOCKED» — trái cơ chế thật (approve_gate + sổ cái niêm phong + mục bắt buộc + chất lượng READY).
        "pending_doctor_actions": [
            f"Điền mọi ô [CẦN…] ở mục bắt buộc {muc_bat_buoc} và chứng chỉ khoá (Phần 5); không xoá mục bắt buộc",
            "Xử lý các mục REVIEW/BLOCK của python3 tools/g4_quality_gate.py (G3 phải PASS_G3_CONFIRMED)",
            "Thống kê viên/PI ghi gate_params.G4 (EPV/VIF, cơ chế dữ liệu thiếu, nhóm nhỏ tiền định, reviewed_by_role, "
            "reviewed_at ISO, dau_van_tay_chot theo dấu bộ chấm in)",
            "Thống kê viên/PI TỰ ký: python3 tools/approve_gate.py --gate G4 (agent không ký thay)",
        ],
        "lock_instruction": ("G4 chỉ khoá khi thống kê viên/PI TỰ ký bằng approve_gate.py --gate G4 (sổ cái phê duyệt "
                             "có niêm phong) sau khi g4_quality_gate.py báo READY_FOR_SIGNATURE — hệ thống không tự "
                             "ghi trạng thái khoá"),
    }
    cp_path = out / "G4_checkpoint.json"
    cp_path.write_text(json.dumps(cp, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    print(f"💾 Lưu: {cp_path}")
    # Vá 2026-07-11 (vòng 9): trước đây banner "HOÀN THÀNH" in vô điều kiện + exit code luôn
    # 0 dù guardrail có lỗi thật (errors không rỗng) — checkpoint ĐÃ ghi đúng "guardrail":
    # status ở trên, nhưng process exit code không phản ánh, nên chạy trực tiếp (không qua
    # run_pipeline.py) sẽ tưởng nhầm là xong. Đối xứng cách G3/G9 đã làm.
    if errors:
        print(f"\n⚠ G4 CÓ {len(errors)} LỖI GUARDRAIL — CHƯA HOÀN THÀNH — {study}")
        print(f"  → Guardrail: {status}")
        raise SystemExit(GC.EXIT_GUARDRAIL_FAIL)
    # ★ SỬA 2026-07-29: banner cũ in "✅ G4 HOÀN THÀNH" ngay dòng dưới dòng
    # "G4 Status: PENDING — CHỜ BÁC SĨ KÝ SAP" — hai câu liền kề tự mâu thuẫn.
    # G4 là CỔNG CỨNG: chỉ thật sự "hoàn thành" sau khi SAP được KÝ (kiểm bằng
    # GC.ledger_approved("G4", ...), do run_g5_auto.py đòi trước khi mở dữ
    # liệu — chốt fail-closed thật nằm ở đó, không phải ở banner này). Rủi ro
    # bị giới hạn (không hạ tầng nào khác tin banner: run_pipeline.py dùng
    # skill_standards.real_world_signals độc lập), nhưng nói đúng vẫn tốt hơn.
    print(f"\n🟡 G4 ĐÃ SINH SAP DỰ THẢO — CHỜ BÁC SĨ/THỐNG KÊ VIÊN KÝ — {study}")
    print(f"  SAP version: 1.0, N (từ G3): {n_adjusted}")
    print("  G4 Status: PENDING — CHỜ BÁC SĨ KÝ SAP")
    print(f"  → Guardrail: {status}")
    print("\n  Sau khi điền đủ [CẦN...] và bác sĩ/thống kê viên đồng ý, ký thật bằng:")
    print(f'     python3 tools/approve_gate.py --study "{study}" --gate G4 \\')
    print(f"       --artifact exports/{study}/G4_A5_SAP_FINAL_{study}.md \\")
    print('       --reviewer-role "METHODS_STATISTICS_REVIEWER" --reviewer-ref "<mã người duyệt>"')

if __name__ == "__main__":
    main()
