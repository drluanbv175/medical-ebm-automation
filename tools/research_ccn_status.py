#!/usr/bin/env python3
"""research_ccn_status.py — Báo cáo tổng hợp CCN (mục "Cần Chờ Người/hạ tầng
Ngoài") của nhánh NGHIÊN CỨU, đọc TRỰC TIẾP 4 sổ nguồn đã có sẵn trong repo —
KHÔNG hard-code lại danh sách mục, KHÔNG tự đóng/sửa trạng thái bất kỳ mục nào.

CHỈ ĐỌC (read-only). Công cụ này không ghi đè, không đánh dấu CLOSED, không sửa
4 sổ nguồn dưới đây dưới bất kỳ hình thức nào.

4 sổ nguồn (đường dẫn mặc định, có thể override bằng cờ CLI để test/di chuyển):
  1. release_evidence/PROGRAM/RESEARCH_OS_PRODUCTION_READINESS_GAP_REGISTER.csv
     (GAP-REG, cột owner tường minh)
  2. release_evidence/PROGRAM/RESEARCH_OS_OPEN_DEPENDENCIES_REGISTER.csv
     (OPEN-DEP, cột owner tường minh nhưng thường chỉ ghi "Dr Luân [/ X]" —
     Dr Luân là người theo dõi, KHÔNG phải bên thật sự đang chặn; bên chặn thật
     nằm ở phần sau dấu "/" hoặc trong resolution_path khi owner chỉ ghi trơn
     "Dr Luân")
  3. release_evidence/PROGRAM/RESEARCH_OS_EXTERNAL_DEPENDENCY_REGISTER.md
     (EXT-DEP, không có cột owner — suy từ tên nhóm Category A-F + nội dung mục)
  4. ../reports/AUTOMATION_GAP_REGISTER_RESEARCH_CLINICAL_EBM_2026-07-14.md
     (AUTO-GAP, ở NGOÀI medical-ebm-automation/, tại gốc OneDrive "Claude AI").
     Chỉ lấy 2 phần liên quan tới NGHIÊN CỨU trong sổ này:
       - Bảng "P1 - Bắt buộc trước pilot nghiên cứu thật và tự động G0-G9 với dữ
         liệu thật" (P1-01..P1-12) — LOẠI những ID đã xuất hiện trong bảng
         "Phụ lục — cập nhật sau lộ trình 7 ngày" (mục 10), vì các ID đó đã có
         ghi chú tiến độ/còn-mở RIÊNG (không còn là một dòng "một-chủ-đang-chờ"
         đơn giản nữa — xem cột "Còn mở" của chính bảng phụ lục đó).
       - Bảng "P2" (P2-01..P2-10): CHỈ lấy dòng liên quan đánh giá-người/human
         evaluation (từ khoá: scorecard, human evaluation, kappa/κ, Likert,
         chấm mù, đánh giá mù) — vì đây là phần P2 duy nhất gắn với CCN nghiên
         cứu (đánh giá độc lập/κ của agent NC), các dòng P2 khác (orchestrator,
         NLU, monitoring, Docker, training...) không phải CCN nghiên cứu.
     Bảng P0 và bảng P1 "...dùng lâm sàng EBM thường quy" (P1-13..P1-22) KHÔNG
     được lấy — đó là CCN của nhánh lâm sàng/bảo mật hệ thống, không phải
     nghiên cứu.

Phân loại "ai đang chờ": suy từ NỘI DUNG cột owner/tên nhóm/resolution_path
bằng một bộ từ khoá minh bạch (xem GROUP_* bên dưới) — KHÔNG suy diễn ngoài
những gì đọc được từ file. Một mục có thể khớp NHIỀU nhóm cùng lúc (ví dụ owner
"PI + IRB") — khi đó mục được đếm vào TẤT CẢ các nhóm khớp (giống cách một
người tự tổng hợp trước đó đã làm), nên tổng theo nhóm có thể LỚN HƠN tổng số
mục. Mục nào không khớp từ khoá nào được xếp "KHONG_RO" và in rõ ra, KHÔNG bịa.

Dùng:
    python tools/research_ccn_status.py
    python tools/research_ccn_status.py --out-md path/to/report.md
    python tools/research_ccn_status.py --gap-register <path> --open-deps <path> \
        --ext-deps <path> --auto-gap <path>   (override đường dẫn, dùng cho test)

Cần bác sĩ kiểm chứng — đây là script đọc dữ liệu thô, không phải nhận định
lâm sàng hay quyết định đóng/mở gap.
"""
from __future__ import annotations

import argparse
import csv
import re
import sys

# Windows: stdout mặc định cp1252 giết print() tiếng Việt — ép UTF-8 (chốt BH55/R4)
import sys as _sys_r4
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set

for _s_r4 in (_sys_r4.stdout, _sys_r4.stderr):
    try:
        _s_r4.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

BASE = Path(__file__).resolve().parents[1]          # medical-ebm-automation/
WORKSPACE_ROOT = BASE.parent                          # .../OneDrive/Claude AI/

sys.path.insert(0, str(BASE / "tools"))
from gate_contract import ensure_utf8_stdout  # noqa: E402

DEFAULT_GAP_REGISTER = BASE / "release_evidence" / "PROGRAM" / "RESEARCH_OS_PRODUCTION_READINESS_GAP_REGISTER.csv"
DEFAULT_OPEN_DEPS = BASE / "release_evidence" / "PROGRAM" / "RESEARCH_OS_OPEN_DEPENDENCIES_REGISTER.csv"
DEFAULT_EXT_DEPS = BASE / "release_evidence" / "PROGRAM" / "RESEARCH_OS_EXTERNAL_DEPENDENCY_REGISTER.md"
DEFAULT_AUTO_GAP = WORKSPACE_ROOT / "reports" / "AUTOMATION_GAP_REGISTER_RESEARCH_CLINICAL_EBM_2026-07-14.md"

# ----------------------------------------------------------------------------
# Nhóm canonical "ai đang chờ" + nhãn hiển thị
# ----------------------------------------------------------------------------
PI, IRB, THONG_KE_VIEN, REVIEWER, HA_TANG_NGOAI, TO_CHUC, KHONG_RO = (
    "PI", "IRB", "THONG_KE_VIEN", "REVIEWER", "HA_TANG_NGOAI", "TO_CHUC", "KHONG_RO",
)

GROUP_ORDER = [PI, IRB, THONG_KE_VIEN, REVIEWER, HA_TANG_NGOAI, TO_CHUC, KHONG_RO]

GROUP_LABELS = {
    PI: "PI (nghiên cứu viên chính)",
    IRB: "IRB / Hội đồng đạo đức",
    THONG_KE_VIEN: "Thống kê viên",
    REVIEWER: "Phản biện / chuyên gia thẩm định độc lập",
    HA_TANG_NGOAI: "Hạ tầng ngoài (IT / vendor / hệ thống cơ sở)",
    TO_CHUC: "Tổ chức / cơ sở (quy trình, pháp lý, quản trị)",
    KHONG_RO: "Chưa phân loại được (cần bác sĩ xem lại)",
}

# Cụm từ đặc trưng cho từng nhóm — so khớp DẠNG CHUỖI CON trên văn bản đã hạ
# chữ thường. Chọn cụm càng đặc trưng càng tốt để tránh khớp nhầm nhóm khác
# (vd "governance policy/committee" thay vì "governance" trơn — tránh khớp
# nhầm cụm "IT + Data governance" sang nhóm TO_CHUC trong khi bản chất là hạ
# tầng ngoài).
_PI_PHRASES = ["dr luân", "dr luan", "written pilot activation", "bác sĩ", "bac si"]
_IRB_PHRASES = ["ethics committee", "ethics approval", "ethics/irb"]
_STATS_PHRASES = ["biostatistician", "date-shifting", "thống kê viên", "thong ke vien"]
_REVIEWER_PHRASES = [
    "review", "security team", "security assessment", "assessment firm",
    "penetration test", "pentest", "qualification report", "validation master plan",
    "chuyên gia", "chuyen gia", "phản biện", "phan bien",
]
_HA_TANG_PHRASES = [
    "institutional it", "it + security", "it + data governance", "institutional network",
    "session store", "worm", "backup", "rbac", "ehospital", "his/lis/pacs", "vpn",
    "key vault", "hsm", "pseudonymization", "edc", "vendor selection",
    "infrastructure decision", "server infrastructure", "account registry",
    "role-to-user mapping", "service account",
]
# "sso"/"mfa"/"idp" quá ngắn để so khớp dạng chuỗi con an toàn — vd "sso" khớp
# nhầm bên trong "asSSOr/assessor" nếu dùng substring. Bắt buộc nguyên từ.
_HA_TANG_WORDS = ["sso", "mfa", "idp"]
_TO_CHUC_PHRASES = [
    "research team", "research office", "legal hold", "governance policy",
    "governance committee", "trial registration", "regulatory authority",
    "institutional author", "future phase", "nlp engineer",
    "data access agreement", "data transfer agreement", "data manager",
    "tổ chức", "to chuc",
]
# Token ngắn/dễ trùng chữ khác — bắt buộc so khớp NGUYÊN TỪ (word boundary).
_PI_WORDS = ["pi"]
_IRB_WORDS = ["irb"]
_STATS_WORDS = ["statistician"]
_REVIEWER_WORDS = ["assessor"]
_TO_CHUC_WORDS = ["legal"]


def _phrase_hit(phrases: Sequence[str], text: str) -> bool:
    return any(p in text for p in phrases)


def _word_hit(words: Sequence[str], text: str) -> bool:
    return any(re.search(r"\b" + re.escape(w) + r"\b", text) for w in words)


def classify_text(raw_text: str) -> Set[str]:
    """Suy ra tập nhóm "ai đang chờ" khớp với 1 đoạn văn bản (owner/tên nhóm/
    resolution_path...). Trả về set RỖNG nếu không có gợi ý gì trong đoạn văn
    bản này (người gọi tự quyết định fallback KHONG_RO khi hợp toàn bộ các
    nguồn cho 1 mục vẫn rỗng)."""
    if not raw_text:
        return set()
    t = raw_text.strip().lower()
    if not t:
        return set()
    # Đặc cách 2 nhãn owner bị cắt cộc lốc hay gặp ở sổ OPEN-DEP khi owner ghi
    # "Dr Luân / IT" hoặc "Dr Luân / Institution" — phần sau dấu "/" chỉ còn
    # đúng 1 từ, không đủ để khớp cụm dài hơn ở trên.
    if t == "it":
        return {HA_TANG_NGOAI}
    if t == "institution":
        return {TO_CHUC}

    groups: Set[str] = set()
    if _phrase_hit(_PI_PHRASES, t) or _word_hit(_PI_WORDS, t):
        groups.add(PI)
    if _phrase_hit(_IRB_PHRASES, t) or _word_hit(_IRB_WORDS, t):
        groups.add(IRB)
    if _phrase_hit(_STATS_PHRASES, t) or _word_hit(_STATS_WORDS, t):
        groups.add(THONG_KE_VIEN)
    if _phrase_hit(_REVIEWER_PHRASES, t) or _word_hit(_REVIEWER_WORDS, t):
        groups.add(REVIEWER)
    if _phrase_hit(_HA_TANG_PHRASES, t) or _word_hit(_HA_TANG_WORDS, t):
        groups.add(HA_TANG_NGOAI)
    if _phrase_hit(_TO_CHUC_PHRASES, t) or _word_hit(_TO_CHUC_WORDS, t):
        groups.add(TO_CHUC)
    return groups


def classify_fields(*texts: str) -> List[str]:
    """Gộp classify_text() trên NHIỀU trường độc lập (vd owner-suffix +
    resolution_path) rồi hợp nhất tập nhóm khớp được; nếu không trường nào
    khớp gì → trả về [KHONG_RO] (không bịa nhóm)."""
    groups: Set[str] = set()
    for t in texts:
        groups |= classify_text(t or "")
    if not groups:
        return [KHONG_RO]
    return [g for g in GROUP_ORDER if g in groups]


# ----------------------------------------------------------------------------
# Trạng thái đóng/mở — chỉ đếm CLOSED nếu văn bản trạng thái THẬT SỰ nói vậy,
# không suy diễn. Mọi trạng thái có dấu phủ định ("NOT ...", "chưa ...",
# "OPEN", "MỞ", "EXTERNAL", "PENDING", "DEFERRED") luôn là MỞ.
# ----------------------------------------------------------------------------
_NEGATIVE_STATUS_MARKERS = ["not ", "chưa ", "khong ", "không ", "open", "mở", "mo ",
                            "external", "pending", "deferred"]
_POSITIVE_STATUS_MARKERS = ["closed", "đã đóng", "da dong", "resolved", "hoàn thành",
                             "hoan thanh", "done", "issued", "signed", "engaged",
                             "written", "obtained", "provided"]


def is_closed_status(status_text: str) -> bool:
    s = (status_text or "").strip().lower()
    if not s:
        return False
    if any(m in s for m in _NEGATIVE_STATUS_MARKERS):
        return False
    return any(m in s for m in _POSITIVE_STATUS_MARKERS)


# ----------------------------------------------------------------------------
# Cấu trúc 1 mục CCN
# ----------------------------------------------------------------------------
@dataclass
class CCNItem:
    source: str            # tên sổ nguồn (vd "GAP-REG")
    item_id: str
    description: str
    owner_raw: str          # đúng nguyên văn cột/đoạn dùng để phân loại — để bác sĩ tự đối chiếu
    status_raw: str
    groups: List[str] = field(default_factory=list)
    closed: bool = False


# ----------------------------------------------------------------------------
# Parser markdown table generic — dùng cho cả 2 sổ .md
# ----------------------------------------------------------------------------
_SEP_RE = re.compile(r"^\s*\|?\s*:?-{2,}.*\|")


def iter_markdown_tables(text: str):
    """Yield (heading_gần_nhất, headers, rows) cho mỗi bảng pipe-table trong
    văn bản markdown. heading = dòng '#...' gần nhất phía trên bảng."""
    lines = text.splitlines()
    current_heading = ""
    i, n = 0, len(lines)
    while i < n:
        line = lines[i]
        stripped = line.strip()
        if stripped.startswith("#"):
            current_heading = stripped.lstrip("#").strip()
            i += 1
            continue
        if stripped.startswith("|") and i + 1 < n and _SEP_RE.match(lines[i + 1]):
            headers = [c.strip() for c in stripped.strip("|").split("|")]
            j = i + 2
            rows: List[List[str]] = []
            while j < n and lines[j].strip().startswith("|"):
                cells = [c.strip() for c in lines[j].strip().strip("|").split("|")]
                rows.append(cells)
                j += 1
            yield current_heading, headers, rows
            i = j
            continue
        i += 1


def _rows_as_dicts(headers: List[str], rows: List[List[str]]) -> List[Dict[str, str]]:
    out = []
    for r in rows:
        d = dict(zip(headers, r))
        out.append(d)
    return out


def normalize_cell_id(raw: str) -> str:
    """Chuẩn hoá 1 giá trị ô mã ID đọc từ bảng markdown: bỏ khoảng trắng thừa
    VÀ ký tự nhấn markdown (**đậm**/_nghiêng_) — sổ AUTO-GAP viết ID trong bảng
    Phụ lục §10 dạng đậm ("**P1-01**") trong khi bảng gốc viết trơn ("P1-01");
    không chuẩn hoá thì so khớp chuỗi sẽ luôn trật, làm bộ lọc loại-trừ-phụ-lục
    im lặng không loại được gì."""
    return (raw or "").strip().strip("*_").strip()


# ----------------------------------------------------------------------------
# Parser sổ 1: GAP-REG (csv, cột owner tường minh)
# ----------------------------------------------------------------------------
def parse_gap_register(path: Path) -> List[CCNItem]:
    items: List[CCNItem] = []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            gap_id = (row.get("gap_id") or "").strip()
            if not gap_id:
                continue
            owner = (row.get("owner") or "").strip()
            status = (row.get("status") or "").strip()
            desc = (row.get("description") or "").strip()
            items.append(CCNItem(
                source="GAP-REG",
                item_id=gap_id,
                description=desc,
                owner_raw=owner,
                status_raw=status,
                groups=classify_fields(owner),
                closed=is_closed_status(status),
            ))
    return items


# ----------------------------------------------------------------------------
# Parser sổ 2: OPEN-DEP (csv). Owner thường chỉ ghi "Dr Luân [/ X]" — Dr Luân
# là người theo dõi sổ, KHÔNG phải bên chặn thật; bên chặn thật nằm ở phần sau
# dấu "/" (nếu có) hoặc phải suy từ resolution_path (khi owner ghi trơn "Dr
# Luân" không có "/").
# ----------------------------------------------------------------------------
def parse_open_dependencies(path: Path) -> List[CCNItem]:
    items: List[CCNItem] = []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            dep_id = (row.get("dependency_id") or "").strip()
            if not dep_id:
                continue
            owner = (row.get("owner") or "").strip()
            status = (row.get("status") or "").strip()
            desc = (row.get("dependency_name") or "").strip()
            resolution = (row.get("resolution_path") or "").strip()
            suffix = ""
            if "/" in owner:
                suffix = owner.split("/", 1)[1].strip()
            items.append(CCNItem(
                source="OPEN-DEP",
                item_id=dep_id,
                description=desc,
                owner_raw=f"{owner} | resolution_path: {resolution}",
                status_raw=status,
                groups=classify_fields(suffix, resolution),
                closed=is_closed_status(status),
            ))
    return items


# ----------------------------------------------------------------------------
# Parser sổ 3: EXT-DEP (.md, KHÔNG có cột owner) — suy từ heading nhóm
# (Category A-F) + tên dependency. Bỏ qua bảng "Summary" (không phải danh sách
# mục, chỉ là bảng đếm tổng).
# ----------------------------------------------------------------------------
def parse_external_dependency_md(path: Path) -> List[CCNItem]:
    text = path.read_text(encoding="utf-8")
    items: List[CCNItem] = []
    for heading, headers, rows in iter_markdown_tables(text):
        h_low = heading.lower()
        if "summary" in h_low or "tổng" in h_low:
            continue
        if not headers or headers[0].upper() != "ID":
            continue
        for rd in _rows_as_dicts(headers, rows):
            dep_id = normalize_cell_id(rd.get("ID") or "")
            if not dep_id or not dep_id.upper().startswith("DEP"):
                continue
            desc = (rd.get("Dependency") or "").strip()
            status = (rd.get("Status") or "").strip()
            classify_input = f"{heading} {desc}"
            items.append(CCNItem(
                source="EXT-DEP",
                item_id=dep_id,
                description=desc,
                owner_raw=f"(suy từ nhóm) {heading}",
                status_raw=status,
                groups=classify_fields(classify_input),
                closed=is_closed_status(status),
            ))
    return items


# ----------------------------------------------------------------------------
# Parser sổ 4: AUTO-GAP (.md, ở NGOÀI medical-ebm-automation/) — chỉ lấy 2
# phần liên quan nghiên cứu, xem docstring đầu file.
# ----------------------------------------------------------------------------
_HUMAN_EVAL_KEYWORDS = [
    "scorecard", "human evaluation", "κ", "kappa", "likert", "chấm mù", "cham mu",
    "đánh giá mù", "danh gia mu",
]


def parse_automation_gap_register(path: Path) -> List[CCNItem]:
    text = path.read_text(encoding="utf-8")

    appendix_ids: Set[str] = set()
    research_p1_rows: List[Dict[str, str]] = []
    p2_rows: List[Dict[str, str]] = []

    for heading, headers, rows in iter_markdown_tables(text):
        h_low = heading.lower()
        row_dicts = _rows_as_dicts(headers, rows)
        if "phụ lục" in h_low or "phu luc" in h_low:
            for rd in row_dicts:
                rid = normalize_cell_id(rd.get("ID") or "")
                if rid:
                    appendix_ids.add(rid)
        elif h_low.startswith("p1") and ("nghiên cứu" in h_low or "nghien cuu" in h_low):
            research_p1_rows.extend(row_dicts)
        elif h_low.startswith("p2"):
            p2_rows.extend(row_dicts)

    items: List[CCNItem] = []

    for rd in research_p1_rows:
        rid = normalize_cell_id(rd.get("ID") or "")
        if not rid:
            continue
        if rid in appendix_ids:
            # Đã có dòng riêng trong Phụ lục §10 với tiến độ/còn-mở chi tiết
            # hơn (không còn là 1 dòng "một-chủ-đang-chờ" đơn giản) → không
            # gộp lại đây tránh đếm trùng/đánh giá sai lệch.
            continue
        desc = (rd.get("Vấn đề cần hoàn thiện") or "").strip()
        owner = (rd.get("Chủ sở hữu") or "").strip()
        items.append(CCNItem(
            source="AUTO-GAP(P1-nghiên cứu)",
            item_id=rid,
            description=desc,
            owner_raw=owner,
            status_raw="MỞ (P1 gốc 2026-07-14, không có trong phụ lục cập nhật)",
            groups=classify_fields(owner),
            closed=False,
        ))

    for rd in p2_rows:
        rid = normalize_cell_id(rd.get("ID") or "")
        if not rid:
            continue
        desc = (rd.get("Vấn đề cần hoàn thiện") or "").strip()
        action = (rd.get("Hành động đề xuất") or "").strip()
        blob = f"{desc} {action}".lower()
        if not any(k in blob for k in _HUMAN_EVAL_KEYWORDS):
            continue
        items.append(CCNItem(
            source="AUTO-GAP(P2)",
            item_id=rid,
            description=desc,
            owner_raw=f"(suy từ hành động đề xuất) {action}",
            status_raw="MỞ (P2 nâng cao — không có cột trạng thái ở sổ gốc)",
            groups=classify_fields(action),
            closed=False,
        ))

    return items


# ----------------------------------------------------------------------------
# Tổng hợp + in báo cáo
# ----------------------------------------------------------------------------
def collect_all_items(
    gap_register: Path = DEFAULT_GAP_REGISTER,
    open_deps: Path = DEFAULT_OPEN_DEPS,
    ext_deps: Path = DEFAULT_EXT_DEPS,
    auto_gap: Path = DEFAULT_AUTO_GAP,
) -> List[CCNItem]:
    items: List[CCNItem] = []
    items.extend(parse_gap_register(gap_register))
    items.extend(parse_open_dependencies(open_deps))
    items.extend(parse_external_dependency_md(ext_deps))
    items.extend(parse_automation_gap_register(auto_gap))
    return items


def build_report(items: List[CCNItem]) -> str:
    total = len(items)
    closed = sum(1 for it in items if it.closed)
    pct_closed = (closed / total * 100) if total else 0.0

    group_counts: Dict[str, int] = {g: 0 for g in GROUP_ORDER}
    for it in items:
        for g in it.groups:
            group_counts[g] += 1

    lines: List[str] = []
    lines.append("# Báo cáo trạng thái CCN (Cần Chờ Người/hạ tầng Ngoài) — nhánh nghiên cứu")
    lines.append("")
    lines.append("Nguồn: đọc trực tiếp 4 sổ (chỉ đọc, không sửa):")
    lines.append("- GAP-REG: release_evidence/PROGRAM/RESEARCH_OS_PRODUCTION_READINESS_GAP_REGISTER.csv")
    lines.append("- OPEN-DEP: release_evidence/PROGRAM/RESEARCH_OS_OPEN_DEPENDENCIES_REGISTER.csv")
    lines.append("- EXT-DEP: release_evidence/PROGRAM/RESEARCH_OS_EXTERNAL_DEPENDENCY_REGISTER.md")
    lines.append(
        "- AUTO-GAP: reports/AUTOMATION_GAP_REGISTER_RESEARCH_CLINICAL_EBM_2026-07-14.md "
        "(chỉ phần P1-nghiên cứu + P2 liên quan đánh giá-người)"
    )
    lines.append("")
    lines.append(f"## Tổng số mục còn mở: {total}")
    lines.append("")
    lines.append(f"## Đã đóng: {closed}/{total} ({pct_closed:.1f}%)")
    if closed == 0:
        lines.append(
            "(0 mục có trạng thái CLOSED trong 4 sổ nguồn tại thời điểm chạy — "
            "ghi đúng 0%, không suy diễn thêm.)"
        )
    lines.append("")
    lines.append(
        "## Theo \"ai đang chờ\" (1 mục có thể khớp nhiều nhóm nếu owner ghi kiểu \"A + B\" "
        "→ tổng dưới đây có thể > tổng số mục)"
    )
    lines.append("")
    lines.append("| Nhóm | Số mục |")
    lines.append("|---|---|")
    for g in GROUP_ORDER:
        if group_counts[g] == 0 and g == KHONG_RO:
            continue
        lines.append(f"| {GROUP_LABELS[g]} | {group_counts[g]} |")
    lines.append("")
    lines.append("## Bảng chi tiết")
    lines.append("")
    lines.append("| STT | Nguồn | Mã ID | Mô tả | Ai đang chờ | Trạng thái gốc |")
    lines.append("|---|---|---|---|---|---|")
    for i, it in enumerate(items, start=1):
        groups_label = ", ".join(GROUP_LABELS[g] for g in it.groups)
        desc = it.description.replace("|", "\\|")
        status = it.status_raw.replace("|", "\\|")
        lines.append(f"| {i} | {it.source} | {it.item_id} | {desc} | {groups_label} | {status} |")
    lines.append("")
    lines.append("Cần bác sĩ kiểm chứng — công cụ này CHỈ ĐỌC dữ liệu thô từ 4 sổ, không tự")
    lines.append("đóng/mở gap và không đưa ra nhận định lâm sàng hay quyết định quản trị nào.")
    lines.append("Phân loại \"ai đang chờ\" dựa trên từ khoá — vài mục biên (owner ghi kiểu tổ")
    lines.append("hợp \"A + B\") có thể được xếp vào nhiều/ít nhóm hơn một người đọc kỹ sẽ chọn;")
    lines.append("xem cột \"Ai đang chờ\" cùng \"Mô tả\" để tự đối chiếu lại nếu cần.")
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    ensure_utf8_stdout()
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else "")
    parser.add_argument("--gap-register", type=Path, default=DEFAULT_GAP_REGISTER)
    parser.add_argument("--open-deps", type=Path, default=DEFAULT_OPEN_DEPS)
    parser.add_argument("--ext-deps", type=Path, default=DEFAULT_EXT_DEPS)
    parser.add_argument("--auto-gap", type=Path, default=DEFAULT_AUTO_GAP)
    parser.add_argument("--out-md", type=Path, default=None, help="Ghi báo cáo ra file markdown (ngoài in console)")
    args = parser.parse_args(argv)

    missing = [p for p in (args.gap_register, args.open_deps, args.ext_deps, args.auto_gap) if not p.exists()]
    if missing:
        for p in missing:
            print(f"LỖI: không tìm thấy sổ nguồn: {p}", file=sys.stderr)
        return 2

    items = collect_all_items(args.gap_register, args.open_deps, args.ext_deps, args.auto_gap)
    report = build_report(items)
    print(report)

    if args.out_md:
        args.out_md.parent.mkdir(parents=True, exist_ok=True)
        args.out_md.write_text(report + "\n", encoding="utf-8", newline="\n")
        print(f"\n(Đã ghi báo cáo ra: {args.out_md})", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
