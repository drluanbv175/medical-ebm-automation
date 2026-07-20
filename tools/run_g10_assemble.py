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
import hmac
import json
import re
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

# THÊM 2026-07-17: dùng MỘT LẦN ở đầu khối nội dung lấy từ study_meta.json khi
# nội dung đó là phán đoán/soạn thảo (PICO, giả thuyết, tiêu chuẩn chọn/loại,
# công cụ đo lường...) thay vì gắn TAG_PROVIDED cho TỪNG dòng — assembler
# không biết nội dung trong study_meta.json do bác sĩ tự gõ hay do agent soạn
# hộ, nên KHÔNG được khẳng định "đã cung cấp" (quy sai nguồn gốc, vi phạm
# đúng bảng "Phân biệt nguồn thông tin" của chính tài liệu).
_META_DRAFT_NOTE = (
    f"{TAG_DRAFT} — nội dung dưới đây do hệ thống/agent soạn dựa trên thông tin "
    "đã có, bác sĩ/chủ nhiệm PHẢI xác nhận hoặc chỉnh sửa trước khi dùng chính thức."
)


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
    # THÊM 2026-07-17: nếu bác sĩ/chủ nhiệm đã CHỐT N thực tế (--confirmed-n ở
    # G3), tóm tắt phải nêu con số THẬT SẼ THU THẬP, không chỉ N tối thiểu lý
    # thuyết — tránh đề cương nói "428" trong khi bác sĩ đã quyết định 1000.
    confirmed_n = _g(cps["G3"], "confirmed_n", default=None)
    if confirmed_n is not None:
        n_txt = f"{confirmed_n} đối tượng (đã bác sĩ/chủ nhiệm chốt; N tối thiểu tính toán: {n_adj})"
    else:
        n_txt = f"{n_adj} đối tượng"
    std = _g(cps["G1"], "design", "reporting_standard",
             default=_g(cps["G4"], "reporting_standard", default=TAG_BS))
    return (
        "# 1. Tóm tắt\n\n"
        f"**Đề tài:** {topic}\n\n"
        f"**Thiết kế:** {design} (chuẩn báo cáo {std}).  \n"
        f"**Cỡ mẫu dự kiến:** {n_txt}.  \n"
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
    # SỬA 2026-07-17: trước đây hàm này BỎ QUA meta hoàn toàn (luôn TAG_BS) dù
    # meta.get("research_question") đã được ĐỌC và dùng ở nơi khác trong cùng
    # file (ma trận truy xuất, bảng kiểm) — tài liệu lắp ráp tự mâu thuẫn nội
    # bộ khi bác sĩ đã cung cấp research_question/pico/hypothesis. Mở rộng
    # theo ĐÚNG pattern meta-driven đã có ở sec_muctieu (aim/objectives).
    qtype = _g(cps["G1"], "question_type", default=TAG_BS)
    lines = [
        "# 3. Câu hỏi nghiên cứu và giả thuyết\n",
        f"**Loại câu hỏi (tự động từ G1):** {qtype}.\n",
    ]
    if meta.get("research_question") or meta.get("pico") or meta.get("hypothesis"):
        lines.append(f"> {_META_DRAFT_NOTE}\n")
    research_question = meta.get("research_question")
    if research_question:
        lines.append(f"**Câu hỏi nghiên cứu:** {research_question}\n")
    pico = meta.get("pico") or {}
    if pico:
        lines.append("**Câu hỏi PICO/PECO:**\n")
        for key, label in (
            ("p", "P — Đối tượng (Population)"),
            ("i_e", "I/E — Can thiệp/Yếu tố phơi nhiễm (Intervention/Exposure)"),
            ("c", "C — So sánh (Comparison)"),
            ("o", "O — Kết cục (Outcome)"),
        ):
            val = pico.get(key)
            lines.append(f"- **{label}:** {val if val else TAG_BS}")
        lines.append("")
    else:
        lines.append(f"**Câu hỏi PICO/PECO:** {TAG_BS} — bác sĩ xác nhận 4 thành phần "
                     "P-I/E-C-O (đã khởi tạo ở G0, chờ chốt).\n")
    hypothesis = meta.get("hypothesis")
    if hypothesis:
        lines.append(f"**Giả thuyết:** {hypothesis}\n")
    else:
        lines.append(f"**Giả thuyết:** {TAG_BS} (với nghiên cứu mô tả có thể không cần "
                     "giả thuyết kiểm định; với nghiên cứu phân tích: nêu H0/H1).\n")
    return "\n".join(lines)


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
    # SỬA 2026-07-17: mở rộng theo pattern meta-driven — inclusion_criteria/
    # exclusion_criteria (list[str]) nếu bác sĩ đã cung cấp trong study_meta.json.
    inclusion = meta.get("inclusion_criteria") or []
    exclusion = meta.get("exclusion_criteria") or []
    sampling = meta.get("sampling_method")
    inclusion_txt = (
        "\n".join(f"- {c}" for c in inclusion)
        if inclusion else
        f"{TAG_BS} — bác sĩ xác định tiêu chuẩn nhận (tuổi, tình trạng, đồng thuận...)."
    )
    exclusion_txt = (
        "\n".join(f"- {c}" for c in exclusion)
        if exclusion else
        f"{TAG_BS} — bác sĩ xác định tiêu chuẩn loại trừ."
    )
    sampling_txt = (
        sampling
        if sampling else
        f"{TAG_BS} — phương pháp chọn mẫu (thuận tiện/ngẫu nhiên hệ thống/phân "
        "tầng...) và quy trình tuyển. Cỡ mẫu xem Mục 8."
    )
    draft_note = f"> {_META_DRAFT_NOTE}\n\n" if (inclusion or exclusion or sampling) else ""
    return (
        "# 6. Đối tượng nghiên cứu\n\n"
        f"{draft_note}"
        "## 6.1. Tiêu chuẩn chọn\n\n"
        f"{inclusion_txt}\n\n"
        "## 6.2. Tiêu chuẩn loại\n\n"
        f"{exclusion_txt}\n\n"
        "## 6.3. Tuyển mẫu\n\n"
        f"{sampling_txt}\n"
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
    confirmed_n = _g(g3, "confirmed_n", default=None)
    confirmed_block = ""
    if confirmed_n is not None:
        adequate = _g(g3, "confirmed_n_adequate", default=None)
        if adequate is True:
            confirmed_block = (
                f"\n**N thực tế đã chốt (bác sĩ/chủ nhiệm quyết định):** **{confirmed_n}** — "
                f"✅ ĐẠT, ≥ N tối thiểu tính theo thống kê ({n_adj}).\n"
            )
        elif adequate is False:
            confirmed_block = (
                f"\n**N thực tế đã chốt (bác sĩ/chủ nhiệm quyết định):** **{confirmed_n}** — "
                f"🔴 CẢNH BÁO, THẤP HƠN N tối thiểu tính theo thống kê ({n_adj}); nguy cơ "
                "thiếu lực thống kê (underpowered) — cần xác nhận có chủ đích hoặc điều chỉnh.\n"
            )
        else:
            confirmed_block = f"\n**N thực tế đã chốt (bác sĩ/chủ nhiệm quyết định):** **{confirmed_n}**.\n"
    return (
        "# 8. Cỡ mẫu\n\n"
        f"**Công thức áp dụng (tự động từ G3):** {formula}.\n\n"
        f"- Mức ý nghĩa α = {alpha}; lực mẫu (power) = {power}.\n"
        f"- Cỡ mẫu tối thiểu tính được: **{n_total}**{per_group}.\n"
        f"- Dự phòng bỏ cuộc {dropout_pct} → cỡ mẫu cần thu: **{n_adj}**.\n"
        f"{confirmed_block}\n"
        f"> Lưu ý: nếu effect size/tỷ lệ giả định lấy từ y văn, PHẢI ghi PMID/DOI "
        f"nguồn ({TAG_BS}). G3 dùng quy ước thận trọng khi chưa có ước tính từ "
        "khảo sát tương tự tại cơ sở.\n"
    )


def sec_congcu(cps, meta) -> str:
    scripts = _g(cps["G5"], "scripts_generated", default=[]) or []
    sc_txt = "\n".join(f"- `{Path(s).name}`" for s in scripts) if scripts else f"- {TAG_BS}"
    instrument = meta.get("instrument") or {}
    if instrument.get("name"):
        note = instrument.get("note")
        instrument_txt = (
            f"> {_META_DRAFT_NOTE}\n\n"
            f"**Công cụ đo lường:** {instrument['name']}"
            + (f" — {instrument.get('source')}" if instrument.get("source") else "")
            + ". " + (note if note else S.TAG_CAN_KIEM_CHUNG_NGUON) + " Với PROM/thang đo: "
            "quy trình dịch–thích nghi văn hoá + kiểm định COSMIN (nối `cong-cu-do-luong`).\n"
        )
    else:
        instrument_txt = (
            f"**Công cụ đo lường:** {TAG_BS} — bác sĩ CUNG CẤP bộ công cụ ĐÃ KIỂM ĐỊNH "
            "(không tự chế). Với PROM/thang đo: quy trình dịch–thích nghi văn hoá + "
            "kiểm định COSMIN (nối `cong-cu-do-luong`).\n"
        )
    return (
        "# 9. Công cụ và quy trình thu thập\n\n"
        f"{instrument_txt}\n"
        "**Script quản trị dữ liệu đã sinh tự động (G5):**\n\n"
        f"{sc_txt}\n\n"
        f"**Pilot/thử nghiệm công cụ:** {TAG_BS} — nêu cỡ mẫu pilot, tiêu chí "
        "chỉnh sửa.\n"
    )


def sec_quantri_dulieu(cps, meta) -> str:
    lock = _g(cps["G5"], "database_lock_status", default=TAG_BS)
    pseudo = (meta or {}).get("real_data_pseudonymization") or {}
    deid = (meta or {}).get("real_data_deidentification") or {}
    intake = (meta or {}).get("real_data_intake") or {}
    cleaning = (meta or {}).get("real_data_cleaning") or {}
    data_lock = (meta or {}).get("real_data_lock") or {}
    if pseudo:
        pseudo_txt = (
            f"**Mã hóa thay thế / pseudonymization:** trạng thái "
            f"`{pseudo.get('status', TAG_BS)}`; dataset pseudonymized "
            f"`{pseudo.get('pseudonymized_path') or TAG_BS}`; report "
            f"`{pseudo.get('report', 'PSEUDONYMIZATION_report.json')}`; "
            f"bảng ánh xạ bảo vệ riêng: {pseudo.get('mapping_location', TAG_BS)}. "
            "Lưu ý: bảng ánh xạ vẫn là PII, không đưa vào exports/repo/OneDrive.\n\n"
        )
    else:
        pseudo_txt = (
            "**Mã hóa thay thế / pseudonymization:** nếu nghiên cứu cần tái định "
            "danh có kiểm soát, chạy `python3 tools/pseudonymize_research_dataset.py "
            "--study <MÃ> --data <file.csv> --then-import`. Bảng ánh xạ sẽ lưu ở "
            "`~/.ebm-secrets/ebm_pseudonymization` hoặc vault được đơn vị phê duyệt, "
            "không nằm trong dataset phân tích.\n\n"
        )
    if deid:
        deid_txt = (
            f"**Khử định danh tự động:** trạng thái `{deid.get('status', TAG_BS)}`; "
            f"file khử định danh `{deid.get('deidentified_path') or TAG_BS}`; "
            f"report `{deid.get('report', 'DEIDENTIFICATION_report.json')}`; "
            f"đã loại {deid.get('dropped_column_count', TAG_BS)} cột định danh và "
            f"redact {deid.get('redacted_cell_count', TAG_BS)} ô có mẫu PII. "
            "Report không lưu giá trị PII/bảng ánh xạ.\n\n"
        )
    else:
        deid_txt = (
            "**Khử định danh tự động:** nếu file thật còn PII hoặc intake bị chặn, "
            "chạy `python3 tools/deidentify_research_dataset.py --study <MÃ> "
            "--data <file.csv> --then-import` để tạo bản khử định danh, quét lại "
            "PII và nạp vào intake an toàn.\n\n"
        )
    if intake:
        intake_txt = (
            f"**Dữ liệu thật đã nhập:** trạng thái `{intake.get('status', TAG_BS)}`; "
            f"file raw read-only `{intake.get('raw_readonly_path') or TAG_BS}`; "
            f"N={intake.get('rows', TAG_BS)}, số biến={intake.get('columns', TAG_BS)}; "
            f"SHA-256 `{intake.get('sha256') or TAG_BS}`; manifest "
            f"`{intake.get('manifest', 'DATA_INTAKE_manifest.json')}`. "
            "Đây mới là bước intake, chưa đồng nghĩa khóa DB.\n\n"
        )
    else:
        intake_txt = (
            f"**Dữ liệu thật đã nhập:** {TAG_BS} — dùng "
            "`python3 tools/import_real_dataset.py --study <MÃ> --data <file.csv>` "
            "để quét PII, copy raw read-only và tạo manifest trước G6.\n\n"
        )
    if cleaning:
        cleaning_txt = (
            f"**Làm sạch dữ liệu trên bản sao:** trạng thái "
            f"`{cleaning.get('status', TAG_BS)}`; clean dataset "
            f"`{cleaning.get('clean_dataset_path') or TAG_BS}`; query log "
            f"`{cleaning.get('query_log') or TAG_BS}`; report "
            f"`{cleaning.get('report', 'DATA_CLEANING_report.json')}`; "
            f"query mở={cleaning.get('open_query_count', TAG_BS)}. "
            "Chỉ được khóa dữ liệu khi query mở = 0.\n\n"
        )
    else:
        cleaning_txt = (
            "**Làm sạch dữ liệu trên bản sao:** sau intake, chạy "
            "`python3 tools/clean_research_dataset.py --study <MÃ> --data "
            "<raw_readonly.csv> --dictionary <data_dictionary.json>` để tạo "
            "`df_clean`, `DATA_CLEANING_report.json` và query log trước khi khóa.\n\n"
        )
    if data_lock and data_lock.get("status") == "LOCKED_FOR_ANALYSIS":
        data_lock_txt = (
            f"**Dữ liệu phân tích đã khóa:** file "
            f"`{data_lock.get('locked_dataset_path') or TAG_BS}`; ngày khóa "
            f"{data_lock.get('lock_date') or TAG_BS}; người xác nhận "
            f"{data_lock.get('approved_by') or TAG_BS}; SAP version "
            f"{data_lock.get('sap_version') or TAG_BS}; SHA-256 "
            f"`{data_lock.get('sha256') or TAG_BS}`; memo "
            f"`{data_lock.get('memo', 'DATA_LOCK_memo.md')}`.\n\n"
        )
    elif data_lock:
        data_lock_txt = (
            f"**Dữ liệu phân tích đã khóa:** CHƯA ĐẠT — trạng thái "
            f"`{data_lock.get('status', TAG_BS)}`; blockers: "
            f"{', '.join(data_lock.get('blockers') or [TAG_BS])}; xem "
            f"`{data_lock.get('memo', 'DATA_LOCK_memo.md')}`.\n\n"
        )
    else:
        data_lock_txt = (
            f"**Dữ liệu phân tích đã khóa:** {TAG_BS} — sau khi làm sạch trên bản "
            "sao, dùng `python3 tools/lock_analysis_dataset.py --study <MÃ> "
            "--clean-data <df_clean.csv> --query-log <query_log.csv> --lock-date "
            "<YYYY-MM-DD> --approved-by <PI> --sap-version <x.y> "
            "--confirm-deidentified --confirm-clean-copy --confirm-no-open-query "
            "--confirm-sap-locked`.\n\n"
        )
    return (
        "# 10. Quản trị dữ liệu và bảo mật\n\n"
        f"**Trạng thái khoá cơ sở dữ liệu (tự động từ G5):** {lock}.\n\n"
        f"{pseudo_txt}"
        f"{deid_txt}"
        f"{intake_txt}"
        f"{cleaning_txt}"
        f"{data_lock_txt}"
        "**Nguyên tắc:** khử định danh, không lưu PII, tuân thủ Luật Bảo vệ dữ "
        f"liệu cá nhân 91/2025/QH15 {S.TAG_CAN_KIEM_CHUNG_NGUON}; nhật ký truy vấn "
        "dữ liệu; làm sạch trên BẢN SAO, không sửa dữ liệu gốc; kế hoạch dữ liệu "
        "thiếu; quy trình khoá DB trước phân tích chính (ALCOA+).\n\n"
        f"**Kế hoạch quản trị dữ liệu chi tiết (DMP):** {TAG_DV} — đã có bản nháp "
        "ở G2 (TL6). Bác sĩ xác nhận nơi lưu trữ, thời hạn, phân quyền tại đơn vị.\n"
    )


_SURVIVAL_CAPABLE_DESIGNS = {"cohort", "rct", "prediction"}
# SỬA 2026-07-21 (vòng lặp kiểm tra-hoàn thiện vòng 2, phát hiện HIGH): thiếu
# "prediction" ở đây làm G10 khẳng định CỨNG "không áp dụng Cox" cho MỌI mô
# hình tiên lượng — mâu thuẫn trực tiếp với chính run_g6_auto.py (biến
# analysis_name_map["prediction"]) vốn đã ghi rõ "hồi quy logistic/Cox hoặc
# ML tuỳ SAP" cho thiết kế này (mô hình tiên lượng thời gian-đến-biến cố,
# vd Cox tiên lượng tử vong 5 năm, là một dạng TRIPOD+AI hợp lệ).


def sec_sap(cps, meta) -> str:
    ver = _g(cps["G4"], "g4_sap_version", default=TAG_BS)
    status = _g(cps["G4"], "g4_status", default=TAG_BS)
    code = _design_code(cps) or TAG_BS
    # THÊM 2026-07-21 (vòng lặp kiểm tra-hoàn thiện vòng 3, phát hiện CRITICAL):
    # bản vá vòng 2 chỉ thêm "prediction" vào _SURVIVAL_CAPABLE_DESIGNS —
    # "qualitative" hoàn toàn không xuất hiện ở đâu trong file này (xác nhận
    # bằng grep), nên vẫn rơi vào nhánh dưới và sinh một Mục 11 THUẦN ĐỊNH
    # LƯỢNG (χ²/Fisher/t-test/hồi quy) cho nghiên cứu định tính — mâu thuẫn
    # trực tiếp với G2/G5/G6/G7/G8 (đã đúng COREQ/SRQR cho "qualitative" từ
    # 2026-07-19/21). Đây là văn bản đề cương/protocol CUỐI CÙNG bác sĩ có
    # thể nộp hội đồng đạo đức/tạp chí — SAI ở đây dễ bị bắt lỗi ngay hoặc
    # tệ hơn là không ai nhận ra.
    if code == "qualitative":
        return (
            "# 11. Kế hoạch phân tích thống kê\n\n"
            f"**Phiên bản SAP (tự động từ G4):** {ver} — trạng thái: {status}.\n\n"
            "**Không áp dụng phân tích thống kê suy diễn (nghiên cứu ĐỊNH TÍNH):**\n"
            "- Phân tích chính: mã hóa chủ đề (thematic/framework analysis) — mã "
            "mở → mã trục → chủ đề, ≥2 người mã hóa độc lập (COREQ/SRQR).\n"
            "- Cỡ mẫu: xác định bằng BÃO HÒA DỮ LIỆU (data saturation), không "
            "tính bằng power/alpha (xem A4).\n"
            "- Độ tin cậy (thay ước lượng + KTC 95%): trustworthiness theo Lincoln "
            "& Guba — credibility (member checking/triangulation), transferability "
            "(mô tả bối cảnh dày), dependability (audit trail), confirmability "
            "(nhật ký phản tư).\n"
            "- KHÔNG dùng p-value/χ²/t-test/hồi quy — không kiểm định giả thuyết "
            "thống kê cho thiết kế này.\n"
            f"- Phần mềm mã hóa (QDA): {TAG_BS} (vd NVivo/ATLAS.ti/MAXQDA hoặc mã tay theo codebook).\n\n"
            f"> Cổng cứng: SAP phải được KÝ KHOÁ (G4 Lock Certificate) TRƯỚC khi xem "
            f"dữ liệu. Mã thiết kế `{code}` (COREQ/SRQR, nối `nghien-cuu-dinh-tinh`/`phan-tich-thong-ke`).\n"
        )
    # SỬA 2026-07-17 (bình duyệt binh-duyet phát hiện thật): câu SAP từng nhắc
    # "Cox" KHÔNG điều kiện cho MỌI thiết kế — hồi quy Cox chỉ có ý nghĩa với
    # dữ liệu sống còn/thời gian-đến-biến cố (cohort/rct theo dõi dọc); một
    # nghiên cứu cắt ngang MỘT thời điểm (cross_sectional/case_control/
    # diagnostic) không có trục thời gian để tính Cox — nhắc "Cox" ở đó là
    # dấu vết SAP dùng chung mọi thiết kế chưa rà lại, phản biện thật sẽ bắt
    # ngay. Chỉ nhắc Cox khi thiết kế THỰC SỰ có thể có kết cục sống còn.
    multivar = (
        "đa biến (hồi quy logistic/tuyến tính/Cox tuỳ thiết kế)"
        if code in _SURVIVAL_CAPABLE_DESIGNS else
        "đa biến (hồi quy logistic/tuyến tính tuỳ kết cục — không áp dụng Cox vì "
        "thiết kế không có trục thời gian-đến-biến cố)"
    )
    return (
        "# 11. Kế hoạch phân tích thống kê\n\n"
        f"**Phiên bản SAP (tự động từ G4):** {ver} — trạng thái: {status}.\n\n"
        "**Phân tích dự kiến (định trước):**\n"
        "- Mô tả: tần số/tỷ lệ (biến định tính), TB±ĐLC hoặc trung vị (IQR) tuỳ "
        "phân phối; tỷ lệ kèm KTC 95%.\n"
        f"- Phân tích yếu tố liên quan: đơn biến (χ²/Fisher, t-test/Mann-Whitney) → "
        f"{multivar}, báo cáo ước lượng + KTC 95% (CẤM p-value đơn độc).\n"
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
        "sai số nhớ lại, nhiễu (confounding); và — với nghiên cứu hài lòng/khảo "
        "sát — sai lệch mong muốn xã hội (social desirability) và **sai lệch "
        "không trả lời (non-response bias)** (người không hài lòng có xu hướng "
        "từ chối/bỏ dở phiếu cao hơn, có thể làm ước lượng mức hài lòng bị "
        "thổi phồng — cần ghi nhận tỷ lệ từ chối + lý do, đối chiếu đặc điểm "
        "cơ bản giữa người từ chối và người tham gia nếu khả thi).\n\n"
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


def build_traceability_matrix(cps, meta=None) -> str:
    """Ma trận mục tiêu-biến-công cụ-phân tích-bảng để kiểm đồng bộ hồ sơ."""
    meta = meta or {}
    design = _g(cps.get("G1"), "design", "primary", default=TAG_BS)
    question_type = _g(cps.get("G1"), "question_type", default=TAG_BS)
    sap_version = _g(cps.get("G4"), "g4_sap_version", default=TAG_BS)
    sap_status = _g(cps.get("G4"), "g4_status", default=TAG_BS)
    crf = _g(cps.get("G5"), "crf_columns", default=[]) or []
    specialty = _g(cps.get("G5"), "specialty", default=TAG_BS)
    crf_source = (
        f"CRF/REDCap G5 ({len(crf)} biến; chuyên khoa `{specialty}`)"
        if crf else TAG_BS
    )
    primary_outcome = meta.get("primary_outcome")
    if not primary_outcome and "primary_outcome" in crf:
        primary_outcome = "`primary_outcome`"
    primary_outcome = primary_outcome or TAG_BS
    exposure = meta.get("exposure") or meta.get("main_predictor")
    if not exposure and "exposure_var" in crf:
        exposure = "`exposure_var`"
    exposure = exposure or TAG_BS
    aim = meta.get("aim") or TAG_BS
    research_question = meta.get("research_question") or f"Loại câu hỏi: {question_type}"
    objectives = meta.get("objectives") or []

    lines = [
        "# Ma trận truy xuất mục tiêu-biến-công cụ-phân tích-bảng\n",
        "Ma trận này là cầu nối bắt buộc giữa đề cương, CRF/codebook, SAP, bảng/hình "
        "và bản thảo. Nếu một mục tiêu không có biến, công cụ, phân tích định trước "
        "hoặc bảng/hình tương ứng thì chưa được kết luận ở báo cáo cuối.\n",
        "| Mục tiêu/câu hỏi | Biến/kết cục | Công cụ/nguồn dữ liệu | "
        "Phân tích định trước | Bảng/hình đầu ra | Cổng nguồn |",
        "|---|---|---|---|---|---|",
        f"| Mục tiêu chung: {aim}; câu hỏi: {research_question} | Kết cục chính: "
        f"{primary_outcome}; phơi nhiễm/yếu tố chính: {exposure} | {crf_source} | "
        f"Thiết kế {design}; SAP version {sap_version} ({sap_status}); mô tả + "
        "ước lượng chính kèm 95% CI/KTC 95%, không p-value đơn độc | Bảng 1, "
        "Bảng 2, Hình 1, Hình 2 | G0/G1/G4/G5 |",
    ]

    if objectives:
        for idx, objective in enumerate(objectives, 1):
            lines.append(
                f"| Mục tiêu cụ thể {idx}: {objective} | {TAG_BS} — biến/kết cục "
                "tương ứng cần map trong codebook | CRF/codebook + nguồn đo tương ứng | "
                "Phân tích định trước trong SAP; nếu thăm dò phải ghi rõ exploratory | "
                f"Bảng/Hình tương ứng mục tiêu {idx} | G4/G5/G7 |"
            )
    else:
        lines.append(
            f"| Mục tiêu cụ thể | {TAG_BS} — chưa có danh sách mục tiêu cụ thể đã khóa | "
            f"{TAG_BS} | {TAG_BS} — chưa thể chốt phân tích theo từng mục tiêu | "
            f"{TAG_BS} | G0/G4/G5 |"
        )

    lines.extend([
        "",
        "## Quy tắc truy xuất khi viết báo cáo/bài báo",
        "- Mỗi câu kết luận trong Results/Discussion phải truy ngược được tới một hàng của ma trận này.",
        "- Không thêm phân tích/bảng/hình ngoài SAP mà không ghi deviation hoặc exploratory.",
        "- Nếu đổi mục tiêu, biến chính, công cụ hoặc phân tích: cập nhật protocol/SAP, "
        "nhật ký thay đổi và xin xác nhận chủ nhiệm/IRB khi cần.",
        f"- {TAG_BS}: Bác sĩ/chủ nhiệm cần hoàn thiện mapping chi tiết cho từng biến "
        "sau khi codebook và SAP được khóa.\n",
    ])
    return "\n".join(lines)


def build_display_items(cps, meta=None) -> str:
    """Danh mục bảng/hình tối thiểu, nối SAP -> manuscript -> submission."""
    code = S.canonical_design_code(_design_code(cps))
    std = S.reporting_standards_for(code)
    fig2_title, fig2_requirements = S.DISPLAY_ITEM_BY_DESIGN.get(
        code or "",
        ("Biểu đồ/đồ thị phân tích chính theo thiết kế thật",
         "Chọn loại hình theo SAP; trục/đơn vị/n/95% CI phải đầy đủ."),
    )
    rows = list(S.DISPLAY_ITEM_CORE) + [
        ("Hình 2", fig2_title, fig2_requirements),
    ]
    lines = [
        "# Danh mục bảng và hình chuẩn xuất bản\n",
        f"**Thiết kế chuẩn hoá:** `{code or TAG_BS}`.  ",
        f"**Chuẩn báo cáo áp dụng:** {std['primary']}.\n",
        "| Mã | Tên bảng/hình bắt buộc | Yêu cầu tối thiểu trước khi nộp |",
        "|---|---|---|",
    ]
    for item_id, title, requirement in rows:
        lines.append(f"| {item_id} | {title} | {requirement} |")
    lines.append("")
    lines.append("**Checklist chất lượng caption/bảng/đồ thị:**")
    for item in S.DISPLAY_ITEM_CHECKLIST:
        lines.append(f"- {item}")
    lines.append(
        f"\n> {TAG_BS}: Khi có dữ liệu thật, agent phân tích phải xuất file nguồn "
        "cho từng bảng/hình (CSV/XLSX/PNG/SVG hoặc script) để truy vết; không dán "
        "ảnh/bảng không có nguồn sinh.\n"
    )
    return "\n".join(lines)


def build_international_compliance(cps, meta=None) -> str:
    """Ma trận tuân thủ quốc tế cho bản báo cáo/bài báo cuối cùng."""
    code = S.canonical_design_code(_design_code(cps))
    std = S.reporting_standards_for(code)
    primary = std["primary"]
    all_guidelines = ", ".join(S.INTERNATIONAL_REPORTING_GUIDELINES)
    lines = [
        "# Ma trận tuân thủ tiêu chuẩn quốc tế\n",
        f"**Thiết kế chuẩn hoá:** `{code or TAG_BS}`.  ",
        f"**Checklist chính phải điền:** {primary}.  ",
        f"**Bộ chuẩn tham chiếu:** {all_guidelines}.\n",
        "| Lớp chuẩn | Chuẩn/khung áp dụng | Bằng chứng đầu ra tối thiểu |",
        "|---|---|---|",
    ]
    for layer, standard, evidence in S.INTERNATIONAL_COMPLIANCE_CORE:
        lines.append(f"| {layer} | {standard} | {evidence} |")
    lines.append(
        "\n**Điều kiện xuất bản tối thiểu:** bản thảo chỉ được xem là sẵn sàng khi "
        "reporting checklist đúng thiết kế đã điền, IRB/EC và consent/waiver có "
        "bằng chứng thật, SAP đã khóa trước phân tích, dataset phân tích đã khóa, "
        "data availability + code availability rõ ràng, COI/funding/AI disclosure "
        "đầy đủ, và toàn bộ bảng/hình có nguồn sinh tái lập.\n"
    )
    lines.append(
        f"> {TAG_DV}: GCP/ICH-GCP chỉ là điều kiện bắt buộc khi đề tài là thử nghiệm "
        "can thiệp/clinical trial hoặc đơn vị/IRB yêu cầu; với nghiên cứu quan sát "
        "vẫn giữ Helsinki, bảo mật dữ liệu, protocol/SAP, transparency và "
        "reproducibility như điều kiện tối thiểu.\n"
    )
    return "\n".join(lines)


def build_final_technical_completion(cps, meta=None) -> str:
    """Bảng kiểm cuối trước khi tuyên bố hoàn thành kỹ thuật."""
    lines = [
        "# Bảng kiểm hoàn thành kỹ thuật\n",
        "Bảng này triển khai quy trình 10 bước để bộ hồ sơ nghiên cứu có thể được "
        "trình hội đồng khoa học/đạo đức, triển khai, phân tích, báo cáo, viết "
        "bài và tái lập bởi nhóm khác. Mọi mục chưa có bằng chứng thật giữ nhãn "
        f"{TAG_BS}/{TAG_DV}/{TAG_DRAFT}; hệ thống KHÔNG tự tuyên bố hoàn tất.\n",
        "## Nội dung đã được khóa\n",
        "| Nội dung | Trạng thái | Ghi chú chống tự ý thay đổi |",
        "|---|---|---|",
    ]
    locked_items = [
        ("Tên đề tài", _g(cps.get("G0"), "topic", default=meta.get("title", TAG_BS))),
        ("Mục tiêu", meta.get("aim", TAG_BS)),
        ("Câu hỏi nghiên cứu/giả thuyết", meta.get("research_question", TAG_BS)),
        ("Thiết kế nghiên cứu", _g(cps.get("G1"), "design", "primary", default=TAG_BS)),
        ("Kết cục chính", meta.get("primary_outcome", TAG_BS)),
    ]
    for item, value in locked_items:
        lines.append(
            f"| {item} | {value} | Không tự ý thay đổi; nếu lỗi nghiêm trọng thì "
            "phải xin chủ nhiệm xác nhận trước. |")

    lines.extend([
        "",
        "## Phân biệt nguồn thông tin",
        "| Loại thông tin | Quy ước trong đầu ra |",
        "|---|---|",
        "| Người dùng cung cấp | Ghi là [ĐÃ CUNG CẤP] hoặc trích nguyên văn có bối cảnh |",
        "| Tài liệu/y văn | Gắn PMID/DOI/URL hoặc cờ cần kiểm chứng nguồn |",
        "| Suy luận chuyên môn | Nêu rõ là suy luận, không thay thế quyết định của chủ nhiệm |",
        "| AI đề xuất | Gắn nhãn dự thảo/cần xác nhận, không ghi như sự thật đã duyệt |",
        "",
        "## Quy trình 10 bước",
        "| Bước | Nội dung kiểm | Điều kiện đạt tối thiểu |",
        "|---|---|---|",
    ])
    for step_id, name, criterion in S.RESEARCH_COMPLETION_STEPS:
        lines.append(f"| {step_id} | {name} | {criterion} |")

    lines.extend([
        "",
        "## Bộ đầu ra bắt buộc",
        "| # | Tài liệu đầu ra | Trạng thái mặc định |",
        "|---|---|---|",
    ])
    for i, item in enumerate(S.RESEARCH_OUTPUT_PACKAGE_ITEMS, 1):
        lines.append(f"| {i} | {item} | {TAG_BS} hoặc đường dẫn artifact thật |")

    lines.extend([
        "",
        "## Kiểm định cuối trước khi ký",
        "| # | Câu hỏi kiểm định | Trạng thái |",
        "|---|---|---|",
    ])
    for i, item in enumerate(S.FINAL_TECHNICAL_CHECKS, 1):
        lines.append(f"| {i} | {item}? | {TAG_BS} |")

    lines.extend([
        "",
        "## Cấu trúc báo cáo cuối",
        "| # | Mục báo cáo cuối |",
        "|---|---|",
    ])
    for i, item in enumerate(S.FINAL_REPORT_SECTIONS, 1):
        lines.append(f"| {i} | {item} |")

    lines.append(
        "\n**Quy tắc kết luận:** chỉ ghi **HOÀN THÀNH KỸ THUẬT** khi tất cả vấn "
        "đề nghiêm trọng đã được xử lý, mọi cổng cứng có bằng chứng thật, và chủ "
        "nhiệm nghiên cứu đã thẩm định. Nếu chưa đạt, phải ghi rõ chưa đạt ở đâu, "
        "nguyên nhân, cần sửa gì, ai quyết định và điều kiện chuyển trạng thái.\n"
    )
    return "\n".join(lines)


def build_missing_information(cps, meta=None) -> str:
    """Danh sách thiếu sót còn lại để bác sĩ/chủ nhiệm ra quyết định."""
    signals = S.real_world_signals(cps, meta)
    signal_rows = {
        "irb_approved": (
            "Phê duyệt Hội đồng đạo đức thật (số + ngày)",
            "Không được triển khai thu thập dữ liệu người tham gia.",
            "Dừng ở bản dự thảo; nộp IRB/EC và chờ phê duyệt thật.",
            "Chủ nhiệm đề tài + Hội đồng đạo đức",
        ),
        "sap_locked": (
            "SAP đã ký khóa trước khi xem dữ liệu",
            "Nguy cơ p-hacking/chọn phân tích theo kết quả.",
            "Chỉ soạn SAP; không mở dữ liệu/phân tích chính cho tới khi khóa.",
            "Chủ nhiệm đề tài + thống kê viên",
        ),
        "db_locked": (
            "Dữ liệu phân tích đã làm sạch và khóa",
            "Không thể phân tích chính hoặc tái lập kết quả.",
            "Hoàn tất query log, data dictionary, lock memo; làm sạch trên bản sao.",
            "Data manager + chủ nhiệm đề tài",
        ),
        "results_final": (
            "Kết quả phân tích thật đã được bác sĩ xác nhận",
            "Không được viết kết quả/kết luận cuối hoặc bài báo hoàn chỉnh.",
            "Giữ phần Results/Discussion ở nhãn [CẦN BỔ SUNG]; chỉ dùng dummy tables.",
            "Chủ nhiệm đề tài + nhóm phân tích",
        ),
        "integrity_signed": (
            "Gói liêm chính tác giả đã ký (ICMJE/COI/tài trợ/AI/CRediT)",
            "Không đủ điều kiện nộp công bố/nghiệm thu.",
            "Chạy G9, thu chữ ký và khai báo đầy đủ trước khi nộp.",
            "Tất cả tác giả + chủ nhiệm đề tài",
        ),
    }
    lines = [
        "# Danh sách thông tin còn thiếu và quyết định cần xác nhận\n",
        "Mục này gom các thiếu sót còn lại thành hành động an toàn. Nếu một thông "
        "tin chưa có bằng chứng thật, hệ thống chỉ được giữ ở trạng thái dự thảo "
        "hoặc chờ xác nhận; không tự điền thay chủ nhiệm/IRB/thống kê viên.\n",
        "| Nhóm | Thông tin còn thiếu | Ảnh hưởng | Phương án an toàn | Người quyết định |",
        "|---|---|---|---|---|",
    ]

    added = False
    for key, (missing, impact, safe_action, owner) in signal_rows.items():
        if not signals.get(key):
            added = True
            lines.append(
                f"| Tín hiệu đời thực `{key}` | {missing} | {impact} | "
                f"{safe_action} | {owner} |")

    missing_checkpoints = [g for g in [f"G{i}" for i in range(10)] if not cps.get(g)]
    if missing_checkpoints:
        added = True
        lines.append(
            f"| Checkpoint pipeline | Thiếu {', '.join(missing_checkpoints)} | "
            "Không đủ truy xuất G0-G9; G10 chỉ là bản lắp ráp không đầy đủ. | "
            "Chạy lại các cổng còn thiếu hoặc ghi rõ lý do không áp dụng. | "
            "Điều phối nghiên cứu + chủ nhiệm đề tài |")

    topic = _g(cps.get("G0"), "topic", default=meta.get("title") if meta else None)
    design = _g(cps.get("G1"), "design", "primary", default=None)
    locked_fields = [
        ("Tên đề tài", topic),
        ("Mục tiêu chung", (meta or {}).get("aim")),
        ("Câu hỏi nghiên cứu/giả thuyết", (meta or {}).get("research_question")),
        ("Thiết kế nghiên cứu", design),
        ("Kết cục chính", (meta or {}).get("primary_outcome")),
    ]
    for field, value in locked_fields:
        if not value or str(value).startswith("[CẦN"):
            added = True
            lines.append(
                f"| Khóa phạm vi | {field} chưa được cung cấp/xác nhận | "
                "Không thể coi protocol là bản cuối; nguy cơ tài liệu mâu thuẫn. | "
                "Bác sĩ/chủ nhiệm xác nhận bằng study_meta.json hoặc artifact đã duyệt. | "
                "Chủ nhiệm đề tài |")

    if not added:
        lines.append(
            "| Không còn thiếu sót cứng | Các tín hiệu bắt buộc đã có theo checkpoint/meta | "
            "Có thể chuyển sang bước thẩm định cuối. | Vẫn cần bác sĩ kiểm chứng và ký. | "
            "Chủ nhiệm đề tài |")

    lines.append(
        "\n> Nếu tiếp tục khi còn thiếu thông tin trong bảng này, đầu ra phải ghi "
        "**CHƯA HOÀN THÀNH KỸ THUẬT** và không được dùng như bản nộp chính thức.\n"
    )
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

def build_front_note(study: str, cps, meta, generated: str | None = None) -> str:
    generated = generated or datetime.now().strftime("%Y-%m-%d %H:%M")
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


def build_document_control(study: str, cps, meta, generated: str | None = None) -> str:
    """Kiểm soát phiên bản/ngày/lịch sử thay đổi cho hồ sơ chính."""
    generated = generated or datetime.now().strftime("%Y-%m-%d %H:%M")
    present = [g for g in [f"G{i}" for i in range(10)] if cps.get(g)]
    version = (
        meta.get("document_version")
        or meta.get("protocol_version")
        or meta.get("version")
        or TAG_DRAFT
    )
    document_date = (
        meta.get("document_date")
        or meta.get("version_date")
        or meta.get("updated_at")
        or generated
    )
    prepared_by = meta.get("prepared_by") or meta.get("authors") or TAG_BS
    approved_by = meta.get("approved_by") or meta.get("pi") or meta.get("principal_investigator")
    approved_by = approved_by or TAG_BS
    sap_version = _g(cps.get("G4"), "g4_sap_version", default=TAG_BS)
    source = ", ".join(present) if present else TAG_BS

    lines = [
        "# Kiểm soát phiên bản và lịch sử thay đổi\n",
        "Mục này bắt buộc cho tài liệu chính của nghiên cứu. Mọi chỉnh sửa sau khi "
        "đã nộp Hội đồng đạo đức, khóa SAP hoặc khóa dữ liệu phải có lý do, "
        "người phê duyệt và dấu vết phiên bản; hệ thống không tự ghi đè quyết "
        "định đã được phê duyệt.\n",
        "| Trường kiểm soát | Giá trị | Quy tắc an toàn |",
        "|---|---|---|",
        f"| Phiên bản tài liệu | {version} | Nếu thay đổi mục tiêu, thiết kế, kết cục, "
        "SAP hoặc consent sau khi đã duyệt thì phải lập amendment. |",
        f"| Ngày tạo/cập nhật | {document_date} | Ngày do hệ thống ghi hoặc chủ nhiệm "
        "cung cấp; kiểm lại trước khi nộp. |",
        f"| Nguồn thay đổi | Checkpoint {source}; SAP version {sap_version} | Chỉ dùng "
        "nguồn có trace; không sửa tay ngoài pipeline mà không ghi nhật ký. |",
        f"| Người soạn/cập nhật | {prepared_by} | Người thật chịu trách nhiệm rà soát. |",
        f"| Người phê duyệt/chủ nhiệm | {approved_by} | {TAG_BS} nếu chưa có chữ ký/xác nhận. |",
        f"| Trạng thái khóa tài liệu | {TAG_DRAFT} | Chỉ khóa khi G2/G4/G6/G9 có bằng chứng thật. |",
        "",
        "## Nhật ký thay đổi",
        "| Phiên bản | Ngày | Nguồn thay đổi | Nội dung thay đổi | Người phê duyệt/chủ nhiệm |",
        "|---|---|---|---|---|",
        f"| {version} | {generated} | G10 assembler từ {source} | Lắp ráp đề cương thống "
        f"nhất, bảng cổng, bảng/hình, compliance, kiểm hoàn thành và thiếu sót còn lại. | "
        f"{approved_by} |",
    ]

    history = meta.get("change_history") or meta.get("version_history") or []
    if isinstance(history, list):
        for row in history:
            if not isinstance(row, dict):
                continue
            row_version = row.get("version") or row.get("phien_ban") or TAG_BS
            row_date = row.get("date") or row.get("ngay") or TAG_BS
            row_source = row.get("source") or row.get("nguon") or "study_meta.json"
            row_change = row.get("change") or row.get("noi_dung") or TAG_BS
            row_approver = row.get("approver") or row.get("nguoi_duyet") or approved_by
            lines.append(
                f"| {row_version} | {row_date} | {row_source} | {row_change} | {row_approver} |"
            )

    lines.append(
        "\n> Nếu không có nhật ký thay đổi, mọi đầu ra chỉ là bản nháp có kiểm soát; "
        "không được coi là bản đã phê duyệt hoặc đã khóa.\n"
    )
    return "\n".join(lines)


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
    now = datetime.now()
    generated_display = now.strftime("%Y-%m-%d %H:%M")
    generated_iso = now.isoformat()

    present = [g for g in cps if cps[g]]
    if not present:
        raise SystemExit(f"❌ Không tìm thấy checkpoint G0-G9 nào trong {out_dir}. "
                         "Chạy pipeline G0→G9 trước.")

    parts: List[str] = []
    parts.append(build_front_note(study, cps, meta, generated=generated_display))
    parts.append("")
    parts.append(build_document_control(study, cps, meta, generated=generated_display))
    parts.append("")
    # Bảng trạng thái + kết luận sẵn sàng đặt ĐẦU để bác sĩ thấy bức tranh thật.
    parts.append(build_gate_table(cps, meta))
    parts.append(build_readiness(cps, meta, study=study))
    parts.append("---\n")
    # 16 mục đề cương.
    for builder in SECTION_BUILDERS:
        parts.append(builder(cps, meta))
        parts.append("")
    # Phụ lục + danh mục hình/bảng + tuân thủ quốc tế + kiểm hoàn thành + pháp lý.
    parts.append(build_phuluc())
    parts.append(build_traceability_matrix(cps, meta))
    parts.append(build_display_items(cps, meta))
    parts.append(build_international_compliance(cps, meta))
    parts.append(build_final_technical_completion(cps, meta))
    parts.append(build_missing_information(cps, meta))
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
        "generated_at": generated_iso,
        "gate_status": "DỰ THẢO — đề cương thống nhất đã lắp ráp",
        "guardrail": guardrail,
        "checkpoints_present": present,
        "checkpoints_missing": [g for g in cps if not cps[g]],
        "document_control": {
            "document_version": (
                meta.get("document_version")
                or meta.get("protocol_version")
                or meta.get("version")
                or TAG_DRAFT
            ),
            "document_date": (
                meta.get("document_date")
                or meta.get("version_date")
                or meta.get("updated_at")
                or generated_display
            ),
            "requires_change_history": True,
            "status": TAG_DRAFT,
        },
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


# Vá 2026-07-18 (audit vòng 2): tiền tố "PMID" đã khử nhập nhằng → dùng \d+ (không
# giới hạn 7-8 chữ số) để KHÔNG bỏ sót PMID <7 chữ số (bài MEDLINE thập niên 1950-60
# đã bị rút) hay >8 chữ số. AN TOÀN vì phải có chữ "PMID" ngay trước — không dính năm/
# cỡ mẫu. (Ô-bảng thuần KHÔNG có tiền tố nên VẪN giữ \d{7,8}, tránh bắt nhầm "2020"/"150".)
_ARTIFACT_PMID_INLINE_RE = re.compile(r'PMID\s*:?\s*(\d+)', re.IGNORECASE)
_TABLE_CELL_PMID_RE = re.compile(r"\d{7,8}")


def _pmids_from_text(text: str) -> set:
    """Trích PMID từ một khối văn bản: (a) số ngay sau chữ "PMID" (mọi độ dài — tiền
    tố đã khử nhập nhằng) và (b) ô CUỐI của mỗi dòng bảng markdown khi ô đó thuần 7-8
    chữ số (cột "PMID/DOI đã xác minh"). KHÔNG quét bừa mọi dãy số trong toàn văn,
    tránh dính DOI (.../S0140-6736(10)60175-4) hay cỡ mẫu/năm tháng."""
    found = set(_ARTIFACT_PMID_INLINE_RE.findall(text))
    for line in text.splitlines():
        line = line.strip()
        if not (line.startswith("|") and line.endswith("|")):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if cells and _TABLE_CELL_PMID_RE.fullmatch(cells[-1]):
            found.add(cells[-1])
    return found


def _extract_pmids_from_artifact(text: str) -> set:
    """Trích PMID mà artifact A12 nhắc tới, để đối chiếu receipt máy-kiểm."""
    return _pmids_from_text(text)


def _extract_pmids_from_final_document(study: str, out_dir: Path) -> set:
    """Trích PMID xuất hiện trong bản G10 cuối nếu file đã được assemble().

    G10 gọi citation_verification_ok() SAU khi ghi DE_CUONG_THONG_NHAT_<study>.md,
    nên đây là lớp đối chiếu phát hành cuối: PMID có mặt trong tài liệu chuẩn bị
    nộp/nghiệm thu cũng phải có trong receipt máy-kiểm A12. Vá 2026-07-18: dùng CHUNG
    `_pmids_from_text` với artifact → cũng bắt PMID trong ô-bảng (trước chỉ bắt inline,
    bất đối xứng — PMID chỉ nằm ở ô-bảng bản cuối từng thoát coverage)."""
    final_doc = out_dir / f"DE_CUONG_THONG_NHAT_{study}.md"
    if not final_doc.exists():
        return set()
    try:
        return _pmids_from_text(final_doc.read_text(encoding="utf-8"))
    except OSError:
        return set()


def citation_verification_ok(study: str, out_dir: Path) -> tuple[bool, str]:
    """Cổng A12 (kiem-chung-trich-dan) — trước 2026-07-15, run_g7_auto.py chỉ IN
    RA một dòng nhắc bác sĩ tự chạy agent kiểm trích dẫn (không gì ép buộc); đề
    tài có thể march thẳng G7→G8→G9→G10 mà chưa ai xác minh PMID/DOI có thật/
    đúng nội dung — đúng lỗ hổng "citation ma" mà A12 được thiết kế để chặn
    (doctrine đã gọi A12 là artifact "dễ sót", xem dieu-phoi-nghien-cuu.md).

    Đây KHÔNG dùng cơ chế approval_ledger/chữ ký như G2/G4/G8/G9 (những cổng đó
    cần MỘT NGƯỜI CÓ VAI TRÒ THẬT ký) — kiểm chứng trích dẫn là việc của AGENT
    (phán đoán LLM đọc abstract/toàn văn, xem module M3 trong kiem-chung-trich-dan.md),
    không phải chữ ký con người, nên chỉ cần xác minh ARTIFACT tồn tại + "sạch"
    (không PARTIAL, không còn 🔴 chưa xử lý) — khớp đúng bản chất của bước này.

    LÀM CỨNG (vá 2026-07-15, P1.1 lộ trình 7 ngày): trước bản vá này, kiểm tra
    ở trên CHỈ tin vào một CHUỖI TEXT do agent tự gõ vào artifact ("KẾT QUẢ CỔNG
    A12: ĐÃ XÁC MINH TOÀN BỘ TRÍCH DẪN") — không có gì bảo đảm agent thật sự đã
    CHẠY `tools/check_citation_retraction.py` trước khi gõ dòng đó (agent có thể,
    do lỗi chứ không cần cố ý, viết dòng xác nhận rồi quên/bỏ qua bước kiểm rút
    bài thật). Nay đọc THÊM `exports/<study>/A12_RETRACTION_RECEIPT.json` — bằng
    chứng máy-kiểm do CHÍNH `check_citation_retraction.py --study <study>` ghi ra
    (không phải do agent gõ tay) — và đối chiếu với danh sách PMID artifact nêu:
    thiếu receipt, receipt hỏng, `all_clean` != true, receipt bị sửa tay (hash
    không khớp `pmids_checked`), hoặc artifact nhắc PMID chưa từng được kiểm
    (không có trong receipt) đều bị CHẶN — dòng text "ĐÃ XÁC MINH" một mình
    không còn đủ để qua cổng.

    Trả (ok, lý_do_chặn) — lý_do_chặn rỗng khi ok=True.
    """
    p = out_dir / f"A12_CITATION_VERIFICATION_{study}.md"
    if not p.exists():
        return False, "chưa chạy agent `kiem-chung-trich-dan` (thiếu artifact A12)"
    try:
        text = p.read_text(encoding="utf-8")
    except OSError:
        return False, "không đọc được artifact A12"
    # SỬA 2026-07-17 (phát hiện qua chạy demo thật cho đề tài hài lòng bệnh
    # nhân C1a BVQY175): "PARTIAL" in text là substring-match thô — khớp nhầm
    # cả khi agent viết PHỦ ĐỊNH tường minh "KHÔNG PARTIAL" (đúng ý "connector
    # HOẠT ĐỘNG, không phải PARTIAL") để xác nhận rõ ràng connector đã sẵn sàng.
    # Cùng lớp bug substring-không-nhận-phủ-định đã gặp ở run_g8_auto.py
    # (_is_locked_or_pass — "UNLOCKED" chứa "LOCKED"). Doctrine kiem-chung-
    # trich-dan.md định nghĩa nhãn PARTIAL chính thức là "⚠ PARTIAL" — ưu tiên
    # khớp nhãn đó; nếu không có, chỉ coi là PARTIAL khi "PARTIAL" xuất hiện
    # KHÔNG bị phủ định ngay trước (KHÔNG/không/NOT/not).
    if re.search(r"⚠\s*PARTIAL", text) or re.search(
        r"(?<!KHÔNG )(?<!không )(?<!NOT )(?<!not )\bPARTIAL\b", text
    ):
        return False, "artifact A12 ở trạng thái PARTIAL (connector PubMed/Crossref không sẵn lúc kiểm)"
    if "KẾT QUẢ CỔNG A12: ĐÃ XÁC MINH TOÀN BỘ TRÍCH DẪN" not in text:
        return False, "artifact A12 chưa có dòng xác nhận sạch (còn 🔴 chưa xử lý hoặc chưa hoàn tất)"

    # Từ đây trở xuống: artifact TỰ KHAI đã sạch — bắt buộc có bằng chứng máy-kiểm
    # thật đứng sau lời khai đó (không chỉ tin chuỗi text agent tự ghi).
    receipt_path = out_dir / "A12_RETRACTION_RECEIPT.json"
    if not receipt_path.exists():
        return False, (
            "artifact A12 tự khai \"ĐÃ XÁC MINH\" nhưng THIẾU receipt máy-kiểm "
            "A12_RETRACTION_RECEIPT.json — chưa thấy bằng chứng đã chạy thật "
            "`python tools/check_citation_retraction.py --pmids <...> --study "
            f"{study}` (dòng text agent tự gõ không đủ, xem kiem-chung-trich-dan.md mục 4b)"
        )
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False, "receipt A12_RETRACTION_RECEIPT.json hỏng/không phải JSON hợp lệ"
    if not isinstance(receipt, dict):
        return False, "receipt A12_RETRACTION_RECEIPT.json không đúng cấu trúc (không phải object)"
    if receipt.get("all_clean") is not True:
        return False, (
            "receipt máy-kiểm A12_RETRACTION_RECEIPT.json ghi all_clean=false (còn PMID "
            "retracted/expression-of-concern/không xác minh được) — không khớp với dòng "
            "\"ĐÃ XÁC MINH\" mà artifact A12 tự khai"
        )
    checked_pmids = receipt.get("pmids_checked")
    if not isinstance(checked_pmids, list):
        return False, "receipt A12_RETRACTION_RECEIPT.json thiếu/sai kiểu trường pmids_checked"
    # Đối chiếu hash — chống receipt bị sửa tay (vd thêm PMID vào pmids_checked
    # mà không thật sự kiểm) sau khi tool đã ghi.
    import check_citation_retraction as CCR  # noqa: E402 (nạp trễ, tránh phụ thuộc vòng lúc import module)
    expected_hash = CCR.pmids_hash([str(x) for x in checked_pmids])
    if receipt.get("pmids_hash") != expected_hash:
        return False, (
            "receipt A12_RETRACTION_RECEIPT.json có pmids_hash không khớp với "
            "pmids_checked (nghi bị sửa tay sau khi ghi) — không đủ tin cậy để qua cổng"
        )
    # Vá 2026-07-16 (round audit đối kháng 3): pmids_hash MỘT MÌNH không chống giả mạo
    # được — công thức pmids_hash() công khai (không khóa bí mật), nên ai/agent nào
    # cũng tự viết tay một receipt "sạch" (all_clean=true) rồi tự tính đúng hash cho
    # khớp pmids_checked, KHÔNG cần thật sự gọi PubMed — tái hiện được bằng script độc
    # lập. Xác minh THÊM chữ ký HMAC (cùng khóa cục bộ dùng cho phê duyệt G2/G4/G8/G9):
    # đề tài THẬT mà máy đang chạy chưa cấu hình khóa ký, hoặc receipt thiếu/sai chữ ký
    # → fail-closed (coi như CHƯA xác minh). Đề tài khác giữ hành vi cũ (không bắt buộc
    # chữ ký) để không phá luồng/test synthetic có từ trước khi receipt có chữ ký.
    receipt_signature = receipt.get("receipt_signature")
    if GC.signing_key_configured():
        expected_signature = GC.sign_approval(
            "A12", study, receipt.get("pmids_hash", ""), receipt.get("checked_at_utc", "")
        )
        if not receipt_signature or not expected_signature or not hmac.compare_digest(
            str(receipt_signature), str(expected_signature)
        ):
            return False, (
                "receipt A12_RETRACTION_RECEIPT.json thiếu chữ ký hợp lệ hoặc chữ ký "
                "không khớp (nghi bị giả mạo/sửa tay) — không đủ tin cậy để qua cổng"
            )
    elif GC.is_real_study_denylisted(study):
        return False, (
            "đề tài THẬT nhưng máy đang chạy CHƯA cấu hình khóa ký "
            "(setup_gate_approval_key.py) — không thể xác minh chữ ký receipt A12, "
            "coi như CHƯA xác minh (fail-closed), không hạ chuẩn cho đề tài thật"
        )
    artifact_pmids = _extract_pmids_from_artifact(text)
    checked_set = {str(x) for x in checked_pmids}
    missing = sorted(artifact_pmids - checked_set)
    if missing:
        return False, (
            "artifact A12 nhắc tới PMID chưa có trong receipt máy-kiểm (chưa được "
            "`check_citation_retraction.py` kiểm rút bài thật): " + ", ".join(missing)
        )
    final_doc_pmids = _extract_pmids_from_final_document(study, out_dir)
    missing_final = sorted(final_doc_pmids - checked_set)
    if missing_final:
        return False, (
            "bản G10 cuối nhắc tới PMID chưa có trong receipt máy-kiểm A12 "
            "(chưa được `check_citation_retraction.py` kiểm rút bài trước khi phát hành): "
            + ", ".join(missing_final)
        )
    # (e) Điều kiện metadata (vá 2026-07-18): khâu ĐỐI CHIẾU tác giả/tiêu đề/tạp chí
    # (Bước 1-2 kiem-chung-trich-dan) trước đây KHÔNG có bằng chứng máy-kiểm — chỉ
    # bảng agent tự gõ. Nay đòi THÊM receipt A12_METADATA_RECEIPT.json (do
    # check_citation_metadata.py ghi) chứng minh mỗi PMID đã thật sự được PHÂN GIẢI
    # metadata gốc. Bắt buộc (fail-closed) cho đề tài THẬT (denylist); validate khi
    # có mặt cho mọi đề tài; bỏ qua khi vắng cho đề tài synthetic (không phá test).
    meta_ok, meta_reason = metadata_verification_ok(
        study, out_dir, artifact_pmids | final_doc_pmids
    )
    if not meta_ok:
        return False, meta_reason
    return True, ""


def metadata_verification_ok(study: str, out_dir: Path, required_pmids: set) -> tuple[bool, str]:
    """Điều kiện (e) của cổng A12 — đối chiếu receipt máy-kiểm METADATA
    (`A12_METADATA_RECEIPT.json`, ghi bởi `tools/check_citation_metadata.py`).

    Song song với phần rút bài trong `citation_verification_ok`: chứng minh mỗi PMID
    đã thật sự được PHÂN GIẢI metadata gốc từ PubMed (không phải agent tự điền ✅ từ
    trí nhớ). KHÔNG tự chứng minh "trích dẫn trong bài khớp metadata gốc" (so khớp
    ngữ nghĩa vẫn là phán đoán agent+bác sĩ) — nhưng buộc metadata gốc phải được lấy
    về THẬT làm mốc đối chiếu.

    Gating (khớp cách phần rút bài xử lý synthetic vs thật):
      - Thiếu receipt + đề tài THẬT (denylist) → CHẶN (fail-closed).
      - Thiếu receipt + đề tài synthetic → cho qua (không phá test/luồng cũ).
      - Có receipt → LUÔN validate (all_resolved, hash, chữ ký khi có khóa, coverage).
    """
    receipt_path = out_dir / "A12_METADATA_RECEIPT.json"
    if not receipt_path.exists():
        if GC.is_real_study_denylisted(study):
            return False, (
                "đề tài THẬT thiếu receipt máy-kiểm A12_METADATA_RECEIPT.json — chưa "
                "thấy bằng chứng đã phân giải metadata gốc thật "
                "(`python tools/check_citation_metadata.py --pmids <...> --study "
                f"{study}`); bảng metadata agent tự gõ không đủ để qua cổng A12"
            )
        return True, ""
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False, "receipt A12_METADATA_RECEIPT.json hỏng/không phải JSON hợp lệ"
    if not isinstance(receipt, dict):
        return False, "receipt A12_METADATA_RECEIPT.json không đúng cấu trúc (không phải object)"
    if receipt.get("all_resolved") is not True:
        return False, (
            "receipt máy-kiểm A12_METADATA_RECEIPT.json ghi all_resolved=false (còn PMID "
            "chưa phân giải được metadata gốc) — không khớp dòng \"ĐÃ XÁC MINH\" artifact A12 tự khai"
        )
    checked_pmids = receipt.get("pmids_checked")
    if not isinstance(checked_pmids, list):
        return False, "receipt A12_METADATA_RECEIPT.json thiếu/sai kiểu trường pmids_checked"
    import check_citation_metadata as CCM  # noqa: E402 (nạp trễ, tránh phụ thuộc vòng)
    expected_hash = CCM.pmids_hash([str(x) for x in checked_pmids])
    if receipt.get("pmids_hash") != expected_hash:
        return False, (
            "receipt A12_METADATA_RECEIPT.json có pmids_hash không khớp pmids_checked "
            "(nghi bị sửa tay sau khi ghi) — không đủ tin cậy để qua cổng"
        )
    # Chữ ký HMAC (gate_id A12META riêng, không trùng chữ ký receipt rút bài).
    if GC.signing_key_configured():
        expected_signature = GC.sign_approval(
            CCM.METADATA_GATE_ID, study, receipt.get("pmids_hash", ""),
            receipt.get("checked_at_utc", "")
        )
        receipt_signature = receipt.get("receipt_signature")
        if not receipt_signature or not expected_signature or not hmac.compare_digest(
            str(receipt_signature), str(expected_signature)
        ):
            return False, (
                "receipt A12_METADATA_RECEIPT.json thiếu chữ ký hợp lệ hoặc chữ ký không "
                "khớp (nghi bị giả mạo/sửa tay) — không đủ tin cậy để qua cổng"
            )
    elif GC.is_real_study_denylisted(study):
        return False, (
            "đề tài THẬT nhưng máy đang chạy CHƯA cấu hình khóa ký "
            "(setup_gate_approval_key.py) — không thể xác minh chữ ký receipt "
            "A12_METADATA_RECEIPT.json, coi như CHƯA xác minh (fail-closed)"
        )
    checked_set = {str(x) for x in checked_pmids}
    missing = sorted({str(x) for x in required_pmids} - checked_set)
    if missing:
        return False, (
            "PMID trong artifact/bản G10 cuối chưa được phân giải metadata gốc thật "
            "(`check_citation_metadata.py`): " + ", ".join(missing)
        )
    return True, ""


def main() -> int:
    ap = argparse.ArgumentParser(
        description="G10 — Lắp ráp đề cương thống nhất từ checkpoint G0-G9.")
    ap.add_argument("--study", required=True, help="Mã đề tài")
    ap.add_argument("--no-validate", action="store_true",
                    help="Bỏ qua bước tự chạy check_de_cuong.py")
    ap.add_argument("--i-know-g9-not-signed", action="store_true",
                    help="Vẫn lắp ráp dù G9 (liêm chính tác giả) chưa có phê duyệt "
                         "thật — CHỈ dùng để xem trước bản NHÁP, KHÔNG dùng bản xuất "
                         "ra khi cờ này bật để nộp bài.")
    ap.add_argument("--i-know-g8-not-signed", action="store_true",
                    help="Vẫn lắp ráp dù G8 (bình duyệt độc lập) chưa có phê duyệt "
                         "thật — CHỈ dùng để xem trước bản NHÁP, KHÔNG dùng bản xuất "
                         "ra khi cờ này bật để nộp bài.")
    ap.add_argument("--i-know-citations-not-verified", action="store_true",
                    help="Vẫn lắp ráp dù trích dẫn (cổng A12, agent "
                         "`kiem-chung-trich-dan`) chưa được xác minh sạch — CHỈ dùng "
                         "để xem trước bản NHÁP, KHÔNG dùng bản xuất ra khi cờ này "
                         "bật để nộp bài.")
    args = ap.parse_args()
    # 2026-07-11: vá path traversal, khớp chuẩn sanitize đã dùng ở G0-G5.
    study = re.sub(r'[^\w\-]', '_', args.study.strip().replace(" ", "-"))

    out_dir = BASE / "exports" / study
    if not out_dir.exists():
        print(f"❌ Không thấy thư mục {out_dir}")
        return 2

    print(f"📦 G10 — Lắp ráp đề cương thống nhất cho: {study}")
    result = assemble(study, out_dir)
    print(f"  ✓ Markdown: {result['md'].relative_to(BASE)}")
    if result["docx"]:
        print(f"  ✓ Word:     {result['docx'].relative_to(BASE)}")
    print(f"  ✓ Checkpoint: {result['checkpoint'].relative_to(BASE)}")

    # Làm mới STUDY_INDEX.md theo checkpoint THẬT — trước đây chỉ sinh 1 lần lúc
    # scaffold (mọi hàng cố định 🔴 Mới mãi mãi, kể cả sau khi march xong G10).
    # G10 là bước capstone bắt buộc sau mỗi lần march (xem doctrine
    # dieu-phoi-nghien-cuu.md) nên đây là chỗ tự nhiên nhất để giữ chỉ mục sống.
    try:
        sys.path.insert(0, str(TOOLS))
        from scaffold_research_project import regenerate_study_index
        idx_path = regenerate_study_index(study, out_dir)
        print(f"  ✓ STUDY_INDEX làm mới: {idx_path.relative_to(BASE)}")
    except Exception as exc:  # noqa: BLE001
        print(f"  [WARN] Không làm mới được STUDY_INDEX.md: {exc}")

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

    # Vá 2026-07-15 (vòng 2): 3 chốt DỪNG dưới đây (citation/G8/G9) chỉ IN RA màn
    # hình rồi return EXIT_BLOCKED — KHÔNG ghi khối needs_input vào G10_checkpoint.json
    # (checkpoint đã ghi cố định ở assemble(), phía trên). Hậu quả: gate_contract.
    # is_blocked()/blocked_detail() luôn trả None/False cho G10 — mọi công cụ đọc
    # checkpoint để biết cổng có đang CHẶN không (vd tools/research_studies_overview.py)
    # sẽ báo SAI một đề tài đang chặn thật ở G10 là "✅ xong". run_pipeline.py khi đó
    # phải dò lý do qua 6 dòng cuối stdout — bản dự phòng, không phải tín hiệu có cấu
    # trúc như mọi cổng khác. Vá bằng cách ghi needs_input đúng chuẩn TRƯỚC khi return.
    def _mark_g10_blocked(reason_code: str, human_message: str, command: str) -> None:
        cp = json.loads(result["checkpoint"].read_text(encoding="utf-8"))
        cp["gate_status"] = "BLOCKED — chờ input đời-thực"
        cp["needs_input"] = GC.needs_input(
            reason_code, human_message, command,
            must_not_fabricate=["approval_ledger.json", "A12_RETRACTION_RECEIPT.json",
                                "A12_METADATA_RECEIPT.json"],
        )
        result["checkpoint"].write_text(
            json.dumps(cp, ensure_ascii=False, indent=2), encoding="utf-8")

    # Vá 2026-07-15 (Ngày 1 lộ trình 7 ngày — reports/LO_TRINH_7_NGAY_NGHIEN_CUU_Y_KHOA
    # _2026-07-14.md): trích dẫn (cổng A12, agent `kiem-chung-trich-dan`) trước đây
    # CHỈ được in ra như một dòng nhắc ở cuối run_g7_auto.py — không gì ép buộc bác sĩ
    # thực sự chạy trước khi march tiếp G8→G9→G10. Nay xác minh THẬT artifact A12 tồn
    # tại + sạch trước khi cho lắp ráp gói sẵn sàng nộp — kiểm TRƯỚC G8 vì phản biện
    # độc lập không nên đọc một bản thảo còn trích dẫn chưa xác minh.
    citation_ok, citation_reason = citation_verification_ok(study, out_dir)
    if not citation_ok and not args.i_know_citations_not_verified:
        print(f"\n🚧 CHƯA SẴN SÀNG NỘP BÀI: Trích dẫn (cổng A12) {citation_reason}.")
        print("   Chạy agent `kiem-chung-trich-dan` TRƯỚC (xác minh PMID/DOI thật +")
        print("   đúng nội dung) — agent tự ghi kết quả vào file A12 nêu trên. Tài")
        print("   liệu đã xuất Ở TRÊN chỉ là BẢN NHÁP — KHÔNG dùng để nộp khi ở trạng")
        print("   thái này. Nếu chỉ muốn xem trước, thêm --i-know-citations-not-verified.")
        _mark_g10_blocked(
            GC.REASON_MISSING_CITATION_VERIFICATION,
            f"Trích dẫn (cổng A12) {citation_reason}.",
            # Tool GỘP: 1 efetch, ghi cả 2 receipt (rút bài + metadata) — ít token/mạng.
            f"python tools/check_citations.py --study {study} --pmids <...>",
        )
        return GC.EXIT_BLOCKED

    # Advisory KHÔNG chặn (vá 2026-07-18, audit vòng 2 D5): cổng metadata (điều kiện e)
    # chỉ BẮT BUỘC receipt cho đề tài THẬT trong denylist. Một đề tài thật MỚI quên thêm
    # vào REAL_STUDY_DENYLIST sẽ bỏ qua metadata IM LẶNG. Làm cho nó KHÔNG im lặng: nếu
    # thiếu A12_METADATA_RECEIPT.json mà không nằm denylist → nhắc (không đổi kết quả cổng).
    if citation_ok and not (out_dir / "A12_METADATA_RECEIPT.json").exists() \
            and not GC.is_real_study_denylisted(study):
        print("\nℹ️  Lưu ý (không chặn): chưa thấy A12_METADATA_RECEIPT.json. Nếu đây là "
              "đề tài THẬT sắp nộp hội đồng, chạy `python tools/check_citations.py --study "
              f"{study} --pmids <...>` để có bằng chứng phân giải metadata gốc, và cân nhắc "
              "thêm mã đề tài vào gate_contract.REAL_STUDY_DENYLIST.")

    # Vá 2026-07-14 (nâng cấp kiểm soát PI/IRB/thống kê viên/phản biện): G8 (bình
    # duyệt độc lập) trước đây KHÔNG có cổng cứng nào — không nằm trong --gate choices
    # của approve_gate.py, không yêu cầu role, không gì chặn nếu bác sĩ bỏ qua bình
    # duyệt mà march thẳng tới G9. Theo doctrine (dieu-phoi-nghien-cuu.md), G8 diễn ra
    # TRƯỚC G9 — nay xác minh THẬT qua ledger tại đây, cùng chỗ với chốt G9 bên dưới.
    g8_artifact = out_dir / f"G8_A9_PRESUBMISSION_{study}.md"
    g8_signed = GC.ledger_approved("G8", study, g8_artifact, repo_root=BASE)
    if not g8_signed and not args.i_know_g8_not_signed:
        print("\n🚧 CHƯA SẴN SÀNG NỘP BÀI: G8 (bình duyệt độc lập) chưa có phê duyệt")
        print("   THẬT trong approval_ledger.json (chạy tools/approve_gate.py --gate G8,")
        print("   TỰ TAY bởi người phản biện, không nhờ agent). Tài liệu đã xuất Ở TRÊN")
        print("   chỉ là BẢN NHÁP để rà soát — KHÔNG dùng để nộp khi ở trạng thái này.")
        print("   Nếu chỉ muốn xem trước, thêm --i-know-g8-not-signed.")
        _mark_g10_blocked(
            GC.REASON_MISSING_PEER_REVIEW,
            "G8 (bình duyệt độc lập) chưa có phê duyệt thật trong approval_ledger.json.",
            f"python tools/approve_gate.py --study {study} --gate G8 "
            f"--artifact {g8_artifact.name} --reviewer-role PHAN_BIEN_DOC_LAP",
        )
        return GC.EXIT_BLOCKED

    # Vá 2026-07-12 (audit toàn diện cổng G0-G9): G10 là bước lắp ráp CUỐI trước khi
    # tài liệu này có thể bị hiểu nhầm là "sẵn sàng nộp" — nhưng G9 (liêm chính tác
    # giả, cổng cứng cuối cùng) trước đây KHÔNG có chốt chặn nào ở đây, chỉ tự in
    # trạng thái "DRAFT" trong văn bản (dễ bị bỏ qua). Nay xác minh THẬT qua ledger
    # (chữ ký, xem gate_contract.py) — vẫn XUẤT file (bác sĩ có thể cần xem nháp),
    # nhưng KHÔNG báo "sẵn sàng"/exit 0 nếu G9 chưa thật sự có phê duyệt.
    #
    # GIỚI HẠN THẬT ĐÃ BIẾT (ghi nhận 2026-07-18, audit đối kháng 7 trục — KHÔNG phải
    # drift mới, là đặc điểm kiến trúc từ đầu): cổng cứng mã hóa G9 chỉ đòi MỘT chữ ký
    # ledger role=PI, KHÔNG đối chiếu số bản ghi với n_authors. Hệ thống chưa có hạ
    # tầng định danh riêng cho từng đồng tác giả nên KHÔNG thể xác minh bằng mã việc
    # "đủ N chữ ký tay của tất cả tác giả" mà tài liệu A10 (ICMJE) yêu cầu trên giấy.
    # Kỷ luật vận hành — PI chỉ ký cổng G9 SAU khi đã thật sự thu đủ chữ ký giấy của
    # TẤT CẢ đồng tác giả — là lớp bảo vệ DUY NHẤT cho phần này. Không nới lỏng cổng;
    # chỉ nêu rõ ranh giới máy-kiểm để bác sĩ không hiểu nhầm "G9 xanh = đủ mọi chữ ký".
    g9_artifact = out_dir / f"G9_A10_AUTHOR_INTEGRITY_{study}.md"
    g9_signed = GC.ledger_approved("G9", study, g9_artifact, repo_root=BASE)
    if not g9_signed and not args.i_know_g9_not_signed:
        print("\n🚧 CHƯA SẴN SÀNG NỘP BÀI: G9 (liêm chính tác giả) chưa có phê duyệt")
        print("   THẬT trong approval_ledger.json (chạy tools/approve_gate.py --gate G9,")
        print("   TỰ TAY bởi bác sĩ/PI, không nhờ agent). Tài liệu đã xuất Ở TRÊN chỉ là")
        print("   BẢN NHÁP để rà soát — KHÔNG dùng để nộp tạp chí/hội đồng khi ở trạng")
        print("   thái này. Nếu chỉ muốn xem trước, thêm --i-know-g9-not-signed.")
        _mark_g10_blocked(
            GC.REASON_MISSING_INTEGRITY,
            "G9 (liêm chính tác giả) chưa có phê duyệt thật trong approval_ledger.json.",
            f"python tools/approve_gate.py --study {study} --gate G9 "
            f"--artifact {g9_artifact.name} --reviewer-role PI",
        )
        return GC.EXIT_BLOCKED

    print("\n✅ Xong. Cần bác sĩ kiểm chứng.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
