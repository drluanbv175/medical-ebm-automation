#!/usr/bin/env python3
"""G10 — LẮP RÁP ĐỀ CƯƠNG THỐNG NHẤT từ toàn bộ checkpoint G0-G9.

Đây là cổng CAPSTONE nối chuỗi pipeline (run_g*_auto.py) với chuẩn của skill
`nghien-cuu-y-khoa-chuan-quoc-te`. Thay vì để bác sĩ nhận 10 file cổng rời rạc,
G10 đọc mọi checkpoint và:

1. Xếp DỮ LIỆU THẬT (thiết kế, cỡ mẫu, công thức, PMID, đạo đức, chuẩn báo cáo)
   vào ĐÚNG mẫu ĐỀ CƯƠNG 16 MỤC của skill (templates/01).
2. Đánh dấu mọi chỗ chưa có bằng NHÃN TRẠNG THÁI skill hợp lệ ([CẦN...],
   [DỰ THẢO]...), KHÔNG bịa số liệu/prose.
3. Sinh BẢNG TRẠNG THÁI CỔNG G0-G9 (đánh số theo SKILL, cross-walk từ pipeline).
4. Kết luận 4 mốc "sẵn sàng" trung thực (document vs evidence).
5. Xuất 1 file .md + .docx (chuẩn trình bày luận văn VN) + G10_checkpoint.json.
6. Tự chạy validator check_de_cuong.py để bảo đảm tuân thủ skill trước khi giao.

NGUYÊN TẮC: G10 KHÔNG viết văn xuôi học thuật thay bác sĩ/agent (đó là việc của
viet-ban-thao / tong-quan-y-van). G10 dựng KHUNG chuẩn + nhồi DỮ LIỆU THẬT +
chỉ rõ chỗ cần điền. Mọi output kèm PMID/DOI khi có + disclaimer.

Đầu vào tuỳ chọn: exports/<study>/study_meta.json — nếu có, dùng để điền tên
đề tài đầy đủ, mục tiêu, tác giả, đơn vị (do bác sĩ/agent cung cấp), tránh để
[CẦN...] ở những chỗ đã biết.

Chạy:  python3 tools/run_g10_assemble.py --study KKB-HAI-LONG-2026
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

BASE = Path(__file__).resolve().parents[1]
TOOLS = BASE / "tools"
sys.path.insert(0, str(TOOLS))

import gate_contract as GC  # noqa: E402  (hợp đồng DỪNG dùng chung — 4 mã thoát)
import skill_standards as S  # noqa: E402

TAG_BS = S.STATUS_TAGS["CAN_BO_SUNG"]              # [CẦN BỔ SUNG]
TAG_DV = S.STATUS_TAGS["CAN_XAC_NHAN_DON_VI"]      # [CẦN XÁC NHẬN TẠI ĐƠN VỊ]
TAG_DRAFT = S.STATUS_TAGS["DU_THAO"]               # [DỰ THẢO]
TAG_PROVIDED = S.STATUS_TAGS["DA_CUNG_CAP"]        # [ĐÃ CUNG CẤP]


# ════════════════════════════════════════════════════════════════════════════
# ĐỌC CHECKPOINT
# ════════════════════════════════════════════════════════════════════════════

def load_checkpoints(out_dir: Path) -> Dict[str, dict]:
    """Đọc G0..G9 checkpoint (None nếu thiếu file)."""
    cps: Dict[str, dict] = {}
    for g in range(10):
        p = out_dir / f"G{g}_checkpoint.json"
        if p.exists():
            try:
                cps[f"G{g}"] = json.loads(p.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                cps[f"G{g}"] = None
        else:
            cps[f"G{g}"] = None
    return cps


def load_meta(out_dir: Path) -> dict:
    """Đọc study_meta.json (tuỳ chọn) do bác sĩ/agent cung cấp."""
    p = out_dir / "study_meta.json"
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _rel(path: Optional[Path]) -> Optional[str]:
    """Đường dẫn tương đối với BASE nếu nằm trong repo; ngược lại giữ tuyệt đối.

    out_dir không nhất thiết nằm dưới BASE (vd chạy test ở thư mục tạm, hoặc đề
    tài xuất nơi khác) — không được crash vì relative_to().
    """
    if path is None:
        return None
    try:
        return str(path.relative_to(BASE))
    except ValueError:
        return str(path)


def _g(cp: Optional[dict], *keys, default=None):
    """Đọc lồng an toàn: _g(cp, 'design', 'primary')."""
    cur = cp
    for k in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k)
    return cur if cur is not None else default


def _design_code(cps: Dict[str, dict]) -> Optional[str]:
    """Lấy mã thiết kế THỐNG NHẤT: ưu tiên G1.internal_code, fallback G3/G5.

    Sửa #13: các mục chỉ đọc G3 sẽ in 'None' khi G3 vắng; nay dùng chung 1 nguồn.
    """
    return _g(cps.get("G1"), "design", "internal_code",
              default=_g(cps.get("G3"), "design_code",
                         default=_g(cps.get("G5"), "design_code", default=None)))


# Thiết kế có TỪ 2 NHÓM trở lên (mới nói 'mỗi nhóm' — sửa #14).
_MULTI_ARM_DESIGNS = {"rct", "cohort", "case_control", "non_randomized"}


# ════════════════════════════════════════════════════════════════════════════
# CÁC MỤC ĐỀ CƯƠNG (mỗi hàm trả về markdown 1 mục)
# ════════════════════════════════════════════════════════════════════════════

def sec_tomtat(cps, meta) -> str:
    topic = _g(cps["G0"], "topic", default=meta.get("title", TAG_BS))
    design = _g(cps["G1"], "design", "primary", default=TAG_BS)
    n_adj = _g(cps["G3"], "n_adjusted", default=TAG_BS)
    std = _g(cps["G1"], "design", "reporting_standard",
             default=_g(cps["G4"], "reporting_standard", default=TAG_BS))
    return (
        "# 1. Tóm tắt\n\n"
        f"**Đề tài:** {topic}\n\n"
        f"**Thiết kế:** {design} (chuẩn báo cáo {std}).  \n"
        f"**Cỡ mẫu dự kiến:** {n_adj} đối tượng.  \n"
        f"**Mục tiêu, kết quả và kết luận:** {TAG_BS} — phần tóm tắt có cấu trúc "
        "(Bối cảnh–Mục tiêu–Phương pháp–Kết quả–Kết luận) chỉ hoàn thiện SAU khi "
        "có kết quả thật; hiện để trống phần Kết quả/Kết luận theo nguyên tắc "
        "không bịa số liệu.\n"
    )


def sec_datvande(cps, meta) -> str:
    ev = _g(cps["G0"], "evidence_level", default=TAG_BS)
    n_sr = _g(cps["G0"], "pubmed_results", "n_pmids", default="?")
    gaps = _g(cps["G0"], "research_gaps", default=[]) or []
    gap_txt = "\n".join(f"- {x}" for x in gaps) if gaps else f"- {TAG_BS}"
    return (
        "# 2. Đặt vấn đề\n\n"
        f"Mức độ chứng cứ hiện có (tự động từ G0): **{ev}**, dựa trên "
        f"{n_sr} tài liệu PubMed liên quan đã truy hồi.\n\n"
        "Khoảng trống nghiên cứu (tự động từ G0):\n\n"
        f"{gap_txt}\n\n"
        f"> {TAG_BS}: Phần đặt vấn đề dạng VĂN XUÔI HỌC THUẬT (tầm quan trọng lâm "
        "sàng, bối cảnh Việt Nam/đơn vị, lập luận tính cần thiết) do agent "
        "`viet-ban-thao`/`tong-quan-y-van` hoặc bác sĩ soạn — G10 không tự viết "
        "để tránh bịa bối cảnh. Số liệu Việt Nam/đơn vị phải có nguồn thật.\n"
    )


def sec_cauhoi(cps, meta) -> str:
    qtype = _g(cps["G1"], "question_type", default=TAG_BS)
    return (
        "# 3. Câu hỏi nghiên cứu và giả thuyết\n\n"
        f"**Loại câu hỏi (tự động từ G1):** {qtype}.\n\n"
        f"**Câu hỏi PICO/PECO:** {TAG_BS} — bác sĩ xác nhận 4 thành phần P-I/E-C-O "
        "(đã khởi tạo ở G0, chờ chốt).\n\n"
        f"**Giả thuyết:** {TAG_BS} (với nghiên cứu mô tả có thể không cần giả "
        "thuyết kiểm định; với nghiên cứu phân tích: nêu H0/H1).\n"
    )


def sec_muctieu(cps, meta) -> str:
    objs = meta.get("objectives") or []
    aim = meta.get("aim")
    lines = ["# 4. Mục tiêu\n"]
    lines.append("## 4.1. Mục tiêu chung\n")
    lines.append((aim + "\n") if aim else f"{TAG_BS} — mục tiêu chung của đề tài.\n")
    lines.append("## 4.2. Mục tiêu cụ thể\n")
    if objs:
        for i, o in enumerate(objs, 1):
            lines.append(f"{i}. {o}")
        lines.append("")
    else:
        lines.append(f"{TAG_BS} — liệt kê các mục tiêu cụ thể (đánh số). "
                     "Nếu đã có trong study_meta.json sẽ tự điền.\n")
    return "\n".join(lines)


def sec_thietke(cps, meta) -> str:
    design = _g(cps["G1"], "design", "primary", default=TAG_BS)
    code = _g(cps["G1"], "design", "internal_code",
              default=_g(cps["G3"], "design_code", default=None))
    rs = S.reporting_standards_for(code)
    alt = _g(cps["G1"], "design", "alternative_1", default=None)
    txt = [
        "# 5. Thiết kế và bối cảnh\n",
        f"**Thiết kế (tự động từ G1):** {design}.\n",
        f"**Mã thiết kế nội bộ:** `{code}`.\n",
        f"**Chuẩn báo cáo chính:** {rs['primary']}.  ",
        f"**Protocol/đăng ký:** {rs['protocol']}.  ",
        f"**Công cụ/chuẩn bổ sung cần cân nhắc:** {rs['extra']}.\n",
    ]
    if alt:
        txt.append(f"**Thiết kế thay thế đã cân nhắc:** {alt}.\n")
    txt.append(f"**Bối cảnh (cơ sở, thời gian, địa điểm):** {TAG_DV} — bác sĩ "
               "xác nhận cụ thể tại đơn vị.\n")
    return "\n".join(txt)


def sec_doituong(cps, meta) -> str:
    return (
        "# 6. Đối tượng nghiên cứu\n\n"
        "## 6.1. Tiêu chuẩn chọn\n\n"
        f"{TAG_BS} — bác sĩ xác định tiêu chuẩn nhận (tuổi, tình trạng, đồng thuận...).\n\n"
        "## 6.2. Tiêu chuẩn loại\n\n"
        f"{TAG_BS} — bác sĩ xác định tiêu chuẩn loại trừ.\n\n"
        "## 6.3. Tuyển mẫu\n\n"
        f"{TAG_BS} — phương pháp chọn mẫu (thuận tiện/ngẫu nhiên hệ thống/phân "
        "tầng...) và quy trình tuyển. Cỡ mẫu xem Mục 8.\n"
    )


def sec_bienso(cps, meta) -> str:
    crf = _g(cps["G5"], "crf_columns", default=[]) or []
    n_rows = _g(cps["G5"], "redcap_rows", default=len(crf))
    generic = _g(cps["G5"], "specialty_is_generic_placeholder", default=False)
    specialty = _g(cps["G5"], "specialty", default="generic")
    lines = [
        "# 7. Biến số và kết cục\n",
        f"**Bộ biến số CRF/REDCap (tự động từ G5):** {n_rows} biến, "
        f"chuyên khoa nhận diện = `{specialty}`.\n",
    ]
    if crf:
        lines.append("Danh sách trường CRF hiện có:\n")
        lines.append("| # | Tên trường CRF |")
        lines.append("|---|---|")
        for i, c in enumerate(crf, 1):
            lines.append(f"| {i} | `{c}` |")
        lines.append("")
    # Cảnh báo covariate lâm sàng mặc định khi chuyên khoa 'generic'.
    clinical_default = {"bp_sys", "bp_dia", "heart_rate", "dm", "htn", "bmi"}
    if generic and clinical_default.intersection(set(crf)):
        lines.append(
            f"> {TAG_BS} — CẢNH BÁO LIÊM CHÍNH DỮ LIỆU: bộ biến CRF hiện chứa các "
            "biến sinh hiệu/bệnh nền mặc định (huyết áp, nhịp tim, đái tháo đường, "
            "tăng huyết áp, BMI) do template lâm sàng sinh ra. Nếu đề tài KHÔNG "
            "phải nghiên cứu lâm sàng (vd khảo sát hài lòng/dịch vụ), PHẢI thay "
            "bằng bộ biến đúng chủ đề (thời gian chờ, thái độ nhân viên, cơ sở vật "
            "chất, chi phí...) và một BỘ CÔNG CỤ ĐÃ KIỂM ĐỊNH — không tự chế thang đo.\n"
        )
    lines.append(
        f"**Kết cục chính/phụ + định nghĩa vận hành + thời điểm đo:** {TAG_BS} — "
        "bác sĩ chốt (nối agent `bien-so-nghien-cuu`). Với thang đo/PROM: bổ sung "
        "COSMIN (nối `cong-cu-do-luong`).\n"
    )
    return "\n".join(lines)


def sec_comau(cps, meta) -> str:
    g3 = cps["G3"]
    if not g3:
        return ("# 8. Cỡ mẫu\n\n"
                f"{TAG_BS} — chưa có checkpoint G3 (cỡ mẫu).\n")
    n_per = _g(g3, "n_per_group", default="?")
    n_total = _g(g3, "n_total", default="?")
    n_adj = _g(g3, "n_adjusted", default="?")
    alpha = _g(g3, "alpha", default="?")
    power = _g(g3, "power", default="?")
    dropout = _g(g3, "dropout", default=0)
    formula = _g(g3, "formula_used", default=TAG_BS)
    try:
        dropout_pct = f"{float(dropout) * 100:.0f}%"
    except (TypeError, ValueError):
        dropout_pct = str(dropout)
    # Chỉ nói 'mỗi nhóm' khi thiết kế thực sự có ≥2 nhóm (sửa #14).
    code = S.canonical_design_code(_design_code(cps))
    per_group = ""
    if code in _MULTI_ARM_DESIGNS and n_per not in ("?", n_total):
        per_group = f" (mỗi nhóm: {n_per})"
    return (
        "# 8. Cỡ mẫu\n\n"
        f"**Công thức áp dụng (tự động từ G3):** {formula}.\n\n"
        f"- Mức ý nghĩa α = {alpha}; lực mẫu (power) = {power}.\n"
        f"- Cỡ mẫu tối thiểu tính được: **{n_total}**{per_group}.\n"
        f"- Dự phòng bỏ cuộc {dropout_pct} → cỡ mẫu cần thu: **{n_adj}**.\n\n"
        f"> Lưu ý: nếu effect size/tỷ lệ giả định lấy từ y văn, PHẢI ghi PMID/DOI "
        f"nguồn ({TAG_BS}). G3 dùng quy ước thận trọng khi chưa có ước tính từ "
        "khảo sát tương tự tại cơ sở.\n"
    )


def sec_congcu(cps, meta) -> str:
    scripts = _g(cps["G5"], "scripts_generated", default=[]) or []
    sc_txt = "\n".join(f"- `{Path(s).name}`" for s in scripts) if scripts else f"- {TAG_BS}"
    return (
        "# 9. Công cụ và quy trình thu thập\n\n"
        f"**Công cụ đo lường:** {TAG_BS} — bác sĩ CUNG CẤP bộ công cụ ĐÃ KIỂM ĐỊNH "
        "(không tự chế). Với PROM/thang đo: quy trình dịch–thích nghi văn hoá + "
        "kiểm định COSMIN (nối `cong-cu-do-luong`).\n\n"
        "**Script quản trị dữ liệu đã sinh tự động (G5):**\n\n"
        f"{sc_txt}\n\n"
        f"**Pilot/thử nghiệm công cụ:** {TAG_BS} — nêu cỡ mẫu pilot, tiêu chí "
        "chỉnh sửa.\n"
    )


def sec_quantri_dulieu(cps, meta) -> str:
    lock = _g(cps["G5"], "database_lock_status", default=TAG_BS)
    return (
        "# 10. Quản trị dữ liệu và bảo mật\n\n"
        f"**Trạng thái khoá cơ sở dữ liệu (tự động từ G5):** {lock}.\n\n"
        "**Nguyên tắc:** khử định danh, không lưu PII, tuân thủ Luật Bảo vệ dữ "
        f"liệu cá nhân 91/2025/QH15 {S.TAG_CAN_KIEM_CHUNG_NGUON}; nhật ký truy vấn "
        "dữ liệu; làm sạch trên BẢN SAO, không sửa dữ liệu gốc; kế hoạch dữ liệu "
        "thiếu; quy trình khoá DB trước phân tích chính (ALCOA+).\n\n"
        f"**Kế hoạch quản trị dữ liệu chi tiết (DMP):** {TAG_DV} — đã có bản nháp "
        "ở G2 (TL6). Bác sĩ xác nhận nơi lưu trữ, thời hạn, phân quyền tại đơn vị.\n"
    )


def sec_sap(cps, meta) -> str:
    ver = _g(cps["G4"], "g4_sap_version", default=TAG_BS)
    status = _g(cps["G4"], "g4_status", default=TAG_BS)
    code = _design_code(cps) or TAG_BS
    return (
        "# 11. Kế hoạch phân tích thống kê\n\n"
        f"**Phiên bản SAP (tự động từ G4):** {ver} — trạng thái: {status}.\n\n"
        "**Phân tích dự kiến (định trước):**\n"
        "- Mô tả: tần số/tỷ lệ (biến định tính), TB±ĐLC hoặc trung vị (IQR) tuỳ "
        "phân phối; tỷ lệ kèm KTC 95%.\n"
        "- Phân tích yếu tố liên quan: đơn biến (χ²/Fisher, t-test/Mann-Whitney) → "
        "đa biến (hồi quy logistic/tuyến tính/Cox tuỳ thiết kế), báo cáo ước "
        "lượng + KTC 95% (CẤM p-value đơn độc).\n"
        f"- Phần mềm + seed + ngưỡng ý nghĩa: {TAG_BS}.\n\n"
        f"> Cổng cứng: SAP phải được KÝ KHOÁ (G4 Lock Certificate) TRƯỚC khi xem "
        f"dữ liệu. Mã thiết kế `{code}` quyết định test phù hợp (nối "
        "`thiet-ke-nghien-cuu`/`phan-tich-thong-ke`).\n"
    )


def sec_sailech(cps, meta) -> str:
    code = _design_code(cps)
    rs = S.reporting_standards_for(code)
    return (
        "# 12. Sai lệch và kiểm soát\n\n"
        f"**Công cụ đánh giá nguy cơ sai lệch phù hợp thiết kế:** {rs['extra']}.\n\n"
        "**Các loại sai số cần khống chế:** sai số chọn mẫu, sai số thông tin, "
        "sai số nhớ lại, nhiễu (confounding), và — với nghiên cứu hài lòng/khảo "
        "sát — sai lệch mong muốn xã hội (social desirability).\n\n"
        f"**Biện pháp khống chế cụ thể tại đơn vị:** {TAG_BS} (chuẩn hoá công cụ, "
        "tập huấn điều tra viên, ẩn danh, tự điền phiếu, giám sát chéo...).\n"
    )


def sec_daoduc(cps, meta) -> str:
    g2 = cps["G2"]
    risk = _g(g2, "risk_level", default=TAG_BS)
    route = _g(g2, "irb_route", default=TAG_BS)
    reg = _g(g2, "registration_required", default=TAG_BS)
    reg_where = _g(g2, "register_where", default=TAG_BS)
    irb_num = _g(g2, "g2_irb_number", default=None)
    docs = _g(g2, "documents_generated", default=[]) or []
    doc_txt = "\n".join(f"- {d}" for d in docs) if docs else f"- {TAG_BS}"
    irb_line = (f"Số phê duyệt IRB: **{irb_num}**." if irb_num
                else f"Số phê duyệt IRB: {TAG_DV} — CHƯA có, phải nộp Hội đồng "
                     "Đạo đức và nhận số thật trước khi thu thập dữ liệu.")
    return (
        "# 13. Đạo đức nghiên cứu\n\n"
        f"**Phân loại nguy cơ (tự động từ G2):** {risk}.  \n"
        f"**Lộ trình thẩm định:** {route}.  \n"
        f"**Đăng ký nghiên cứu:** {reg} ({reg_where}).\n\n"
        f"{irb_line}\n\n"
        "**Hồ sơ đạo đức đã sinh tự động (G2):**\n\n"
        f"{doc_txt}\n\n"
        "Tuân thủ Tuyên ngôn Helsinki 2024, ICH-GCP, Thông tư 43/2024/TT-BYT "
        f"{S.TAG_CAN_KIEM_CHUNG_NGUON}. ICF đồng thuận tham gia; tự nguyện; ẩn "
        "danh; bảo mật.\n"
    )


def sec_phobien(cps, meta) -> str:
    js = _g(cps["G8"], "journal_suggestions", default=[]) or []
    js_txt = ""
    if js:
        js_txt = "\n\n**Gợi ý tạp chí đích (tự động từ G8, cần bác sĩ chọn):**\n\n"
        js_txt += "| Tạp chí | IF | Ghi chú |\n|---|---|---|\n"
        for j in js:
            js_txt += f"| {j.get('journal','?')} | {j.get('if','?')} | {j.get('note','')} |\n"
    return (
        "# 14. Kế hoạch phổ biến kết quả/ứng dụng\n\n"
        "Kết quả dùng để cải tiến chất lượng dịch vụ/thực hành tại đơn vị và công "
        f"bố khoa học. Kế hoạch chuyển giao cụ thể: {TAG_BS}."
        f"{js_txt}\n"
    )


def sec_tiendo(cps, meta) -> str:
    return (
        "# 15. Tiến độ và nguồn lực\n\n"
        f"**Nhân lực & phân công:** {TAG_BS} (thu thập/nhập liệu/phân tích/giám sát).\n\n"
        f"**Tiến độ theo mốc cổng G0–G9:** {TAG_BS} (biểu Gantt — nối "
        "`ke-hoach-trien-khai`).\n\n"
        f"**Dự trù kinh phí:** {TAG_BS} — đơn giá/định mức do chủ nhiệm ấn định, "
        "KHÔNG bịa số tiền.\n"
    )


def sec_tltk(cps, meta) -> str:
    # Gộp PMID từ G0 (seed) + G7 (seed dùng trong bản thảo), khử trùng.
    pmids: List[str] = []
    for g in ("G7", "G0"):
        for pid in (_g(cps[g], "pmids_used_as_seed", default=[]) or []):
            if pid not in pmids:
                pmids.append(str(pid))
    # G0 có thể lưu PMID trong pubmed_results — nhưng schema hiện chỉ đếm số.
    lines = ["# 16. Tài liệu tham khảo Vancouver/NLM\n"]
    if pmids:
        lines.append(
            "Danh sách PMID hạt giống (tự động từ G0/G7). Đây là ĐỊNH DANH THẬT "
            "nhưng METADATA đầy đủ (tác giả–năm–tạp chí–trang) phải được KIỂM CHỨNG "
            f"và định dạng Vancouver trước khi nộp ({S.TAG_CAN_KIEM_CHUNG_NGUON}, "
            "nối agent `kiem-chung-trich-dan`):\n")
        for i, pid in enumerate(pmids, 1):
            lines.append(f"{i}. PMID: {pid} — {TAG_BS} (định dạng Vancouver đầy đủ).")
        lines.append("")
    else:
        lines.append(f"{TAG_BS} — chưa có PMID hạt giống trong checkpoint.\n")
    lines.append(
        f"> {TAG_BS}: Tài liệu tham khảo TIẾNG VIỆT (luận văn/tạp chí trong nước) "
        "hệ thống tra cứu tự động (PubMed) không tiếp cận đủ — bác sĩ bổ sung.\n")
    return "\n".join(lines)


SECTION_BUILDERS = [
    sec_tomtat, sec_datvande, sec_cauhoi, sec_muctieu, sec_thietke,
    sec_doituong, sec_bienso, sec_comau, sec_congcu, sec_quantri_dulieu,
    sec_sap, sec_sailech, sec_daoduc, sec_phobien, sec_tiendo, sec_tltk,
]


# ════════════════════════════════════════════════════════════════════════════
# BẢNG TRẠNG THÁI CỔNG + KẾT LUẬN SẴN SÀNG + PHỤ LỤC
# ════════════════════════════════════════════════════════════════════════════

# Cổng skill nào KHÔNG có nguồn pipeline sinh bằng chứng thật (chỉ khoá qua tín
# hiệu bác sĩ xác nhận) — chú thích rõ trong bảng để không đọc nhầm 'đã có' (#15).
_SIGNAL_ONLY_NOTE = {
    "G6": "cần bằng chứng KHOÁ DB thật (bác sĩ xác nhận) — pipeline không tự sinh",
    "G7": "cần KẾT QUẢ phân tích thật (bác sĩ xác nhận) — pipeline chỉ dựng khung",
}


def build_gate_table(cps, meta=None) -> str:
    lines = [
        "# Bảng trạng thái cổng chất lượng G0–G9 (đánh số theo skill)\n",
        "Trạng thái từng cổng SKILL được suy TỰ ĐỘNG từ checkpoint pipeline + tín "
        "hiệu thực-tế (bản đồ chéo — pipeline và skill đánh số G0-G9 KHÁC nhau ở "
        "một số chỉ số). 'KHOÁ' chỉ khi có bằng chứng THẬT, không suy từ artifact.\n",
        "| Cổng (skill) | Tên | Trạng thái | Sản phẩm bắt buộc | Nguồn bằng chứng |",
        "|---|---|---|---|---|",
    ]
    for sg, (name, _cond, product) in S.SKILL_GATES.items():
        state = S.skill_gate_state(sg, cps, meta)
        srcs = ", ".join(f"pipeline {p}" for p in S.SKILL_TO_PIPELINE_GATE.get(sg, []))
        note = _SIGNAL_ONLY_NOTE.get(sg)
        source_cell = srcs if srcs else "—"
        if note:
            source_cell = (srcs + "; " if srcs else "") + note
        lines.append(f"| {sg} | {name} | {state} | {product} | {source_cell} |")
    lines.append("")
    lines.append("**Ba cổng CỨNG của pipeline (không được tự vượt):**\n")
    for pg, why in S.PIPELINE_HARD_GATES.items():
        st = S.normalize_pipeline_gate_state(pg, cps.get(pg), meta)
        lines.append(f"- pipeline {pg}: {st} — {why}")
    lines.append("")
    return "\n".join(lines)


def build_readiness(cps, meta=None, study: str = "<tên>") -> str:
    lines = ["# Kết luận trạng thái sẵn sàng\n",
             "| Mốc | Kết luận | Điều kiện / Chặn bởi |",
             "|---|---|---|"]
    for r in S.readiness_report(cps, meta):
        lines.append(f"| {r['moc']} | {r['dat']} | {r['chi_tiet']} |")
    lines.append("")
    # Audit 2026-07-11: nhãn "ĐẠT (khoá — có bằng chứng thật)" ở trên dựa trên
    # real_world_signals() — nguồn tín hiệu là checkpoint tự khai báo hoặc
    # study_meta.json do bác sĩ tự ghi, KHÔNG phải xác minh mật mã ledger (cơ chế
    # đó — approval_ledger.json + hash artifact — chỉ mới nối vào run_g6/run_g9/
    # run_stats_analysis.py, KHÔNG chạy trong bảng này). "Bằng chứng thật" ở đây
    # nghĩa là "khác artifact rỗng/placeholder", KHÔNG phải "đã qua cổng mật mã".
    lines.append(
        "> ⚠️ **Về độ tin cậy của cột \"Kết luận\":** nhãn \"khoá — có bằng chứng "
        "thật\" dựa trên nội dung checkpoint/`study_meta.json` bác sĩ tự khai, "
        "KHÔNG phải xác minh mật mã ledger (`approval_ledger.json` — cơ chế đó chỉ "
        "chạy khi thật sự phân tích dữ liệu, qua `tools/approve_gate.py`). Trước "
        f"khi nộp bài, xác nhận riêng bằng `python3 tools/run_g9_auto.py --study "
        f"{study}` — cổng G9 có kiểm ledger thật.\n"
    )
    return "\n".join(lines)


def build_phuluc() -> str:
    lines = ["# Phụ lục\n", "Các phụ lục bắt buộc kèm đề cương (chuẩn skill):\n"]
    for i, item in enumerate(S.DE_CUONG_PHU_LUC, 1):
        lines.append(f"- Phụ lục {i}: {item} — {TAG_BS}")
    lines.append("")
    return "\n".join(lines)


def build_legal_refs() -> str:
    lines = ["# Khung pháp lý & tiêu chuẩn tham chiếu\n",
             "| Văn bản/Tiêu chuẩn | Phiên bản | Lĩnh vực | Cờ |",
             "|---|---|---|---|"]
    for r in S.LEGAL_ETHICS_REFS:
        lines.append(f"| {r['ten']} | {r['phien_ban']} | {r['linh_vuc']} | {r['co']} |")
    lines.append(f"\n> Mọi văn bản trên mang cờ {S.TAG_CAN_KIEM_CHUNG_NGUON}: "
                 "phải kiểm nguồn chính thức trước khi trích để kết luận (Quy tắc "
                 "7 của skill).\n")
    return "\n".join(lines)


# ════════════════════════════════════════════════════════════════════════════
# LẮP RÁP TOÀN VĂN
# ════════════════════════════════════════════════════════════════════════════

def build_front_note(study: str, cps, meta) -> str:
    generated = datetime.now().strftime("%Y-%m-%d %H:%M")
    n_pmids = _g(cps["G7"], "n_pmids", default=_g(cps["G0"], "pubmed_results",
                 "n_pmids", default="?"))
    return (
        f"> **Ghi chú tài liệu:** Đề cương THỐNG NHẤT này do cổng G10 (assembler) "
        f"lắp ráp TỰ ĐỘNG lúc {generated} từ checkpoint G0–G9 của đề tài "
        f"`{study}`, theo mẫu 16 mục của skill `nghien-cuu-y-khoa-chuan-quoc-te`. "
        "Dữ liệu cấu trúc (thiết kế, cỡ mẫu, công thức, đạo đức, chuẩn báo cáo, "
        f"{n_pmids} PMID) lấy TỪ pipeline — không bịa. Mọi chỗ mang nhãn "
        f"{TAG_BS}/{TAG_DV}/{TAG_DRAFT}/{S.TAG_CAN_KIEM_CHUNG_NGUON} là chỗ hệ "
        "thống KHÔNG đủ dữ liệu/thẩm quyền để tự quyết. **Văn xuôi học thuật "
        "(Đặt vấn đề, Tổng quan, Bàn luận) do bác sĩ/agent viết riêng — G10 chỉ "
        "dựng khung + nhồi dữ liệu thật + chỉ chỗ cần điền.** Cần bác sĩ kiểm "
        "chứng toàn bộ trước khi trình Hội đồng Đạo đức hoặc sử dụng chính thức.\n"
    )


def title_page_dict(study: str, cps, meta) -> dict:
    org = meta.get("org_lines") or [TAG_DV]
    title = meta.get("title") or _g(cps["G0"], "topic", default=study)
    authors = meta.get("authors")
    place_year = meta.get("place_year") or f"{TAG_BS} (địa điểm – năm)"
    metas = [f"**Mã đề tài:** {study}"]
    if authors:
        metas.append(f"**Nhóm nghiên cứu:** {authors}")
    else:
        metas.append(f"**Chủ nhiệm đề tài:** {TAG_BS}")
    return {
        "org_lines": org,
        "doc_type": "ĐỀ CƯƠNG NGHIÊN CỨU",
        "title": title,
        "meta_lines": metas,
        "place_year": place_year,
    }


def assemble(study: str, out_dir: Path) -> Dict[str, object]:
    cps = load_checkpoints(out_dir)
    meta = load_meta(out_dir)

    present = [g for g in cps if cps[g]]
    if not present:
        raise SystemExit(f"❌ Không tìm thấy checkpoint G0-G9 nào trong {out_dir}. "
                         "Chạy pipeline G0→G9 trước.")

    parts: List[str] = []
    parts.append(build_front_note(study, cps, meta))
    parts.append("")
    # Bảng trạng thái + kết luận sẵn sàng đặt ĐẦU để bác sĩ thấy bức tranh thật.
    parts.append(build_gate_table(cps, meta))
    parts.append(build_readiness(cps, meta, study=study))
    parts.append("---\n")
    # 16 mục đề cương.
    for builder in SECTION_BUILDERS:
        parts.append(builder(cps, meta))
        parts.append("")
    # Phụ lục + pháp lý.
    parts.append(build_phuluc())
    parts.append(build_legal_refs())
    parts.append(
        "\n---\n\n> **Disclaimer:** Tài liệu do hệ thống hỗ trợ lắp ráp; dữ liệu "
        "cấu trúc trích từ checkpoint pipeline, KHÔNG bịa số liệu/PMID. Các mục "
        "gắn nhãn bắt buộc phải được bác sĩ điền/kiểm chứng. **Cần bác sĩ kiểm "
        "chứng toàn bộ nội dung trước khi trình Hội đồng Đạo đức hoặc sử dụng "
        "chính thức.**\n"
    )

    body_md = "\n".join(parts)

    md_path = out_dir / f"DE_CUONG_THONG_NHAT_{study}.md"
    md_path.write_text(body_md, encoding="utf-8")

    docx_path = None
    try:
        import md2docx_vn
        docx_path = out_dir / f"DE_CUONG_THONG_NHAT_{study}.docx"
        md2docx_vn.markdown_to_docx(body_md, docx_path,
                                    title_page=title_page_dict(study, cps, meta))
    except ImportError:
        print("  ⚠ python-docx chưa cài — bỏ qua .docx (vẫn có .md).")
        docx_path = None

    # Chạy guardrail check_de_cuong NGAY để ghi kết quả vào checkpoint (cho
    # orchestrator/đọc máy thấy G10 pass/fail thật, không phải 'no_guardrail').
    guardrail = {"passed": None, "checks": {}, "errors": [], "warnings": []}
    try:
        import check_de_cuong
        rep = check_de_cuong.validate(md_path, out_dir)
        guardrail = {"passed": rep["passed"], "checks": rep["checks"],
                     "errors": rep["errors"], "warnings": rep["warnings"]}
    except ImportError:
        pass

    # Checkpoint G10.
    gate_states = {sg: S.skill_gate_state(sg, cps, meta) for sg in S.SKILL_GATES}
    readiness = S.readiness_report(cps, meta)
    signals = S.real_world_signals(cps, meta)
    checkpoint = {
        "gate": "G10",
        "study": study,
        "generated_at": datetime.now().isoformat(),
        "gate_status": "DỰ THẢO — đề cương thống nhất đã lắp ráp",
        "guardrail": guardrail,
        "checkpoints_present": present,
        "checkpoints_missing": [g for g in cps if not cps[g]],
        "real_world_signals": signals,
        "skill_gate_states": gate_states,
        "readiness": readiness,
        "artifacts": {
            "de_cuong_md": _rel(md_path),
            "de_cuong_docx": _rel(docx_path),
        },
        "n_de_cuong_sections": len(SECTION_BUILDERS),
        "disclaimer": "Cần bác sĩ kiểm chứng.",
    }
    cp_path = out_dir / "G10_checkpoint.json"
    cp_path.write_text(json.dumps(checkpoint, ensure_ascii=False, indent=2),
                       encoding="utf-8")

    return {"md": md_path, "docx": docx_path, "checkpoint": cp_path,
            "body_md": body_md, "cps": cps}


def main() -> int:
    ap = argparse.ArgumentParser(
        description="G10 — Lắp ráp đề cương thống nhất từ checkpoint G0-G9.")
    ap.add_argument("--study", required=True, help="Mã đề tài")
    ap.add_argument("--no-validate", action="store_true",
                    help="Bỏ qua bước tự chạy check_de_cuong.py")
    args = ap.parse_args()

    out_dir = BASE / "exports" / args.study
    if not out_dir.exists():
        print(f"❌ Không thấy thư mục {out_dir}")
        return 2

    print(f"📦 G10 — Lắp ráp đề cương thống nhất cho: {args.study}")
    result = assemble(args.study, out_dir)
    print(f"  ✓ Markdown: {result['md'].relative_to(BASE)}")
    if result["docx"]:
        print(f"  ✓ Word:     {result['docx'].relative_to(BASE)}")
    print(f"  ✓ Checkpoint: {result['checkpoint'].relative_to(BASE)}")

    # Tự chạy validator.
    if not args.no_validate:
        try:
            import check_de_cuong
            print("\n🔍 Tự kiểm tuân thủ skill (check_de_cuong)...")
            report = check_de_cuong.validate(result["md"], out_dir)
            check_de_cuong.print_report(report)
            if not report["passed"]:
                print("  ⚠ Đề cương CHƯA đạt guardrail skill — xem lỗi ở trên.")
                # SỬA 2026-07-06: trước đây return 1 (= GC.EXIT_CRASH) khiến
                # run_pipeline.py coi lỗi nội dung TẤT ĐỊNH (vd nhãn sai chuẩn)
                # là lỗi TẠM THỜI đáng thử lại — retry vô ích (nội dung không
                # đổi giữa các lần chạy), lãng phí 1 lượt thử rồi mới báo failed
                # mơ hồ. Dùng đúng mã GUARDRAIL_FAIL để pipeline DỪNG ngay,
                # không retry, và báo đúng bản chất lỗi (khớp quy ước G0-G9).
                return GC.EXIT_GUARDRAIL_FAIL
        except ImportError:
            print("  ⚠ check_de_cuong.py chưa có — bỏ qua tự kiểm.")

    print("\n✅ Xong. Cần bác sĩ kiểm chứng.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
