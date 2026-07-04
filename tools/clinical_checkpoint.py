#!/usr/bin/env python3
"""clinical_checkpoint.py — Máy kiểm THẬT cho sổ trạng thái checkpoint
(`.claude/agents/_SO-TRANG-THAI-CHECKPOINT.md` / `EBM_MASTER/MEMORY.md`).

Vá khoảng trống A2/S2 (audit 2026-07-04): sổ trạng thái tự khai "GIỚI HẠN BẢN CHẤT —
đây là bản ghi VĂN BẢN để mô hình đọc lại, KHÔNG phải checkpoint tiến trình runtime" —
đúng, nhưng trước đây KHÔNG có bất kỳ máy nào kiểm bản ghi có hợp lệ hay không: một
khối checkpoint có thể ghi "cong_vua_qua: A" (đã qua Cổng A — áp dụng cho bệnh nhân)
trong khi "danh_muc_🔴_con_lai" vẫn còn liệt kê mục bắt buộc thiếu — đúng kịch bản
"CẤM kết luận đủ khi còn 🔴" mà completeness-critic (C1–C9) của `dieu-phoi-lam-sang.md`
yêu cầu nhưng chỉ tự chấm bằng lời văn, không ai kiểm lại bằng máy.

Module này KHÔNG thay LLM suy luận lâm sàng (việc đó vẫn là agent con) — chỉ kiểm
TÍNH TOÀN VẸN của BẢN GHI TRẠNG THÁI: đúng schema `_SO-TRANG-THAI-CHECKPOINT.md`,
không vượt cổng khi còn lỗi đỏ, đúng trình tự cổng (A trước B trong cùng 1 ca),
không PII.

Dùng:
    python tools/clinical_checkpoint.py <file_so_trang_thai.md>
    python tools/clinical_checkpoint.py <file>.md --json
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, field


class CheckpointFormatError(ValueError):
    """Khối checkpoint không đúng schema — công cụ TỪ CHỐI đọc thay vì đoán mò."""


DISCLAIMER = "Cần bác sĩ kiểm chứng."

_HEADER_RE = re.compile(
    r"^##\s*CHECKPOINT\s*\[(?P<ngay_header>[^\]]*)\]\s*—\s*"
    r"(?:đề tài/ca:|de tai/ca:)?\s*(?P<case>.*)$",
    re.MULTILINE,
)
# Tên trường CỐ ĐỊNH theo schema (không phải regex mở — tránh đoán bừa field lạ).
# "danh_muc_..._con_lai" chấp nhận emoji 🔴 xen giữa (nguồn .md nhúng emoji trong tên trường).
_FIELD_PATTERNS = {
    "cong_vua_qua": re.compile(r"-\s*cong_vua_qua:\s*(.+)"),
    "ngay": re.compile(r"-\s*ngay:\s*(.+)"),
    "loai_nhiem_vu": re.compile(r"-\s*loai_nhiem_vu:\s*(.+)"),
    "san_pham_vua_xong": re.compile(r"-\s*san_pham_vua_xong:\s*(.+)"),
    "danh_muc_do_con_lai": re.compile(r"-\s*danh_muc_.{0,4}_con_lai:\s*(.+)"),
    "buoc_ke": re.compile(r"-\s*buoc_ke:\s*(.+)"),
    "agent_ghi": re.compile(r"-\s*agent_ghi:\s*(.+)"),
}
REQUIRED_FIELDS = tuple(_FIELD_PATTERNS.keys())

_EMPTY_TOKENS = {"", "(không)", "(khong)", "không", "khong", "none", "n/a", "-"}
_VALID_TASK_TYPES = {"lâm sàng", "lam sang", "nghiên cứu", "nghien cuu"}
_VALID_GATE_RE = re.compile(r"^(?:G\d{1,2}|A|B)$", re.I)
_VALID_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# PII (đồng bộ tinh thần với tools/eval/run_eval.py PII list — sổ trạng thái là văn
# bản tự do do LLM ghi tay nên có nguy cơ lẫn PII y hệt gói đầu ra lâm sàng).
_PII_PATTERNS = [
    ("SĐT_VN", re.compile(r"(?<!\d)(?:\+?84|0)(?:\d[\s.\-]?){8,10}\d(?!\d)")),
    ("CCCD", re.compile(r"(?<!\d)\d{9}(?:\d{3})?(?!\d)")),
    ("EMAIL", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")),
]


@dataclass
class CheckpointEntry:
    index: int
    case_label: str
    cong_vua_qua: str
    ngay: str
    loai_nhiem_vu: str
    san_pham_vua_xong: str
    danh_muc_do_con_lai: str
    buoc_ke: str
    agent_ghi: str
    raw_block: str
    missing_fields: list = field(default_factory=list)

    @property
    def has_outstanding_red_items(self) -> bool:
        return self.danh_muc_do_con_lai.strip().lower() not in _EMPTY_TOKENS

    @property
    def is_gate_entry(self) -> bool:
        return self.cong_vua_qua.strip().upper() in ("A", "B")


@dataclass
class Violation:
    code: str
    entry_index: int
    case_label: str
    message: str


def parse_checkpoint_log(text: str) -> list[CheckpointEntry]:
    """Tách văn bản sổ trạng thái thành các khối CheckpointEntry có cấu trúc.

    KHÔNG raise nếu chưa có checkpoint nào (file mới/trống) — trả về list rỗng;
    CHỈ raise CheckpointFormatError nếu CÓ header "## CHECKPOINT" nhưng nội dung
    sau đó rỗng bất thường (dấu hiệu ghi hỏng, không phải "chưa có checkpoint").
    """
    headers = list(_HEADER_RE.finditer(text))
    entries: list[CheckpointEntry] = []
    for i, h in enumerate(headers):
        start = h.end()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        block = text[start:end]
        if not block.strip():
            raise CheckpointFormatError(
                f"Khối checkpoint #{i + 1} (case: {h.group('case')!r}) có header nhưng "
                "KHÔNG có trường nào theo sau — ghi hỏng, không phải 'chưa có checkpoint'."
            )
        fields_found: dict[str, str] = {}
        missing: list[str] = []
        for name, pat in _FIELD_PATTERNS.items():
            m = pat.search(block)
            if m:
                fields_found[name] = m.group(1).strip()
            else:
                fields_found[name] = ""
                missing.append(name)
        entries.append(CheckpointEntry(
            index=i,
            case_label=h.group("case").strip(),
            raw_block=h.group(0) + "\n" + block,
            missing_fields=missing,
            **fields_found,
        ))
    return entries


def _scan_pii(text: str) -> list[str]:
    hits = []
    for label, pat in _PII_PATTERNS:
        if pat.search(text):
            hits.append(label)
    return hits


def validate_entries(entries: list[CheckpointEntry]) -> list[Violation]:
    """Kiểm TỪNG khối (schema/cổng/PII) rồi kiểm TRÌNH TỰ giữa các khối cùng 1 ca."""
    violations: list[Violation] = []

    for e in entries:
        if e.missing_fields:
            violations.append(Violation(
                "MISSING_FIELD", e.index, e.case_label,
                f"Thiếu trường bắt buộc: {e.missing_fields}"))
            continue  # khối hỏng schema -> không kiểm tiếp các quy tắc phụ thuộc field

        if not _VALID_GATE_RE.match(e.cong_vua_qua.strip()):
            violations.append(Violation(
                "INVALID_GATE_TOKEN", e.index, e.case_label,
                f"cong_vua_qua={e.cong_vua_qua!r} không khớp G0-G99/A/B"))

        if not _VALID_DATE_RE.match(e.ngay.strip()):
            violations.append(Violation(
                "INVALID_DATE", e.index, e.case_label,
                f"ngay={e.ngay!r} không đúng định dạng YYYY-MM-DD"))

        if e.loai_nhiem_vu.strip().lower() not in _VALID_TASK_TYPES:
            violations.append(Violation(
                "INVALID_TASK_TYPE", e.index, e.case_label,
                f"loai_nhiem_vu={e.loai_nhiem_vu!r} phải là 'lâm sàng' hoặc 'nghiên cứu'"))

        # Bất biến CỐT LÕI: không được ghi ĐÃ QUA Cổng A/B khi còn 🔴 bắt buộc —
        # đây là bản dịch MÁY KIỂM của quy tắc "CẤM kết luận đủ khi còn 🔴" trong
        # completeness-critic C1-C9 (dieu-phoi-lam-sang.md), trước đây chỉ LLM tự chấm.
        if e.is_gate_entry and e.has_outstanding_red_items:
            violations.append(Violation(
                "GATE_WITH_OUTSTANDING_RED_ITEMS", e.index, e.case_label,
                f"Cổng {e.cong_vua_qua.strip().upper()} được ghi ĐÃ QUA nhưng "
                f"danh_muc_🔴_con_lai vẫn còn: {e.danh_muc_do_con_lai!r}"))

        pii = _scan_pii(e.raw_block)
        if pii:
            violations.append(Violation(
                "PII_DETECTED", e.index, e.case_label, f"Nghi PII trong khối: {pii}"))

    # Trình tự CỔNG A trước CỔNG B trong CÙNG một ca (không thể ghi sổ cái/Cổng B
    # trước khi bác sĩ đã duyệt áp dụng/Cổng A cho đúng ca đó).
    by_case: dict[str, list[CheckpointEntry]] = {}
    for e in entries:
        if e.missing_fields:
            continue
        by_case.setdefault(e.case_label, []).append(e)
    for case_label, case_entries in by_case.items():
        seen_gate_a = False
        for e in case_entries:
            token = e.cong_vua_qua.strip().upper()
            if token == "A":
                seen_gate_a = True
            elif token == "B" and not seen_gate_a:
                violations.append(Violation(
                    "GATE_B_BEFORE_GATE_A", e.index, case_label,
                    "Cổng B (ghi sổ cái) được ghi TRƯỚC khi có Cổng A (bác sĩ duyệt "
                    "áp dụng) cho cùng ca này — trình tự vô lý, khả năng ghi nhầm."))

    return violations


def format_report(entries: list[CheckpointEntry], violations: list[Violation]) -> dict:
    return {
        "total_entries": len(entries),
        "total_violations": len(violations),
        "violations": [
            {"code": v.code, "entry_index": v.entry_index,
             "case_label": v.case_label, "message": v.message}
            for v in violations
        ],
        "verdict": "TRẢ-VỀ-SỬA" if violations else "ĐẠT",
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Kiểm tính toàn vẹn sổ trạng thái checkpoint (schema/cổng/PII).")
    ap.add_argument("checkpoint_file", help="File .md sổ trạng thái checkpoint")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    text = open(args.checkpoint_file, encoding="utf-8").read()
    try:
        entries = parse_checkpoint_log(text)
    except CheckpointFormatError as e:
        print(f"❌ LỖI ĐỌC: {e}")
        return 1

    violations = validate_entries(entries)
    report = format_report(entries, violations)

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"=== KIỂM SỔ TRẠNG THÁI — {args.checkpoint_file} ===")
        print(f"Tổng {report['total_entries']} khối checkpoint, "
              f"{report['total_violations']} vi phạm.")
        for v in report["violations"]:
            print(f"  🔴 [{v['code']}] khối #{v['entry_index']} "
                  f"(ca: {v['case_label']}) — {v['message']}")
        print(f"\nPHÁN ĐỊNH: {report['verdict']}")
        print(f"\n{DISCLAIMER}")

    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
