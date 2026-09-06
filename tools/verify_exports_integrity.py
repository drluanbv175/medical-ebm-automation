#!/usr/bin/env python3
"""Kiểm liêm chính NỘI DUNG tài liệu nghiên cứu trong `exports/`.

VÌ SAO CÓ FILE NÀY (2026-07-31)
--------------------------------
Hook pre-commit của hai repo chỉ kiểm ĐỒNG BỘ agent/doctrine, không kiểm nội dung
tài liệu nghiên cứu. Ngày 31/07/2026 một commit (a21a01f) đi qua hook sạch hoàn
toàn trong khi file đề cương đang hỏng 26 chỗ: các placeholder giá trị của bảng
dự kiến kết quả ("n = —", "cOR = —", ô "— (—; —) [ref]") bị một bước xử lý văn
bản đổi nhầm thành dấu phẩy ("n =,", ", (, ;, ) [ref]"). Lỗi chỉ lộ ra khi có
người đối chiếu tay với bản gốc. Nếu không đối chiếu, bản hỏng đã có thể đi
thẳng vào tài liệu trình Hội đồng Đạo đức.

Công cụ này chặn đúng LỚP LỖI đó, không chỉ một trường hợp: nó soi các dấu hiệu
hỏng đọc được bằng máy trong tài liệu nghiên cứu, cộng thêm vài luật liêm chính
nền mà mọi tài liệu y khoa của dự án phải giữ.

PHẠM VI CỐ Ý HẸP
----------------
Chỉ kiểm file `.md` dưới `exports/`. Không chấm chất lượng khoa học, không thay
quality gate G0-G10, không thay thẩm định của bác sĩ. Mỗi luật ở đây phải là thứ
máy khẳng định được chắc chắn; nghi ngờ thì cảnh báo, không chặn.

Thuần thư viện chuẩn Python, không cần mạng.

Dùng:
    python3 tools/verify_exports_integrity.py            # kiểm toàn bộ exports/
    python3 tools/verify_exports_integrity.py --staged   # chỉ file đang stage (hook)
    python3 tools/verify_exports_integrity.py --path F   # kiểm một file

Mã thoát: 0 = đạt (có thể kèm cảnh báo) · 1 = có lỗi CHẶN.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys

# Windows: stdout mặc định cp1252 giết print() tiếng Việt — ép UTF-8 (chốt BH55/R4)
import sys as _sys_r4
from dataclasses import dataclass, field
from pathlib import Path

for _s_r4 in (_sys_r4.stdout, _sys_r4.stderr):
    try:
        _s_r4.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

REPO = Path(__file__).resolve().parent.parent
EXPORTS = REPO / "exports"

# Tài liệu nội bộ (checklist, sổ tay làm việc) không phải sản phẩm nộp ra ngoài,
# nên miễn luật disclaimer. Nhận diện bằng tiền tố "_" theo quy ước sẵn có.
INTERNAL_PREFIX = "_"


@dataclass
class Finding:
    file: str
    line: int
    code: str
    message: str
    blocking: bool = True
    evidence: str = ""


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)
    files_checked: int = 0

    @property
    def blocking(self) -> list[Finding]:
        return [f for f in self.findings if f.blocking]

    @property
    def warnings(self) -> list[Finding]:
        return [f for f in self.findings if not f.blocking]


# ── Luật 1: placeholder giá trị bị phá ────────────────────────────────────────
# Bảng dự kiến kết quả dùng "—" làm chỗ trống chờ điền. Một bước xử lý văn bản
# đổi nhầm thành dấu phẩy sẽ để lại "= ," / "=," — không có nghĩa trong tài liệu
# khoa học và là dấu vết chắc chắn của hỏng máy móc, không phải văn người viết.
_BROKEN_PLACEHOLDER = re.compile(r"[=≈]\s*,(?=\s*[|)\s;]|$)")
# Chuỗi dấu phẩy liên tiếp kiểu ", (, ;, )" — hệ quả của cùng lỗi đó trên ô bảng.
_COMMA_SOUP = re.compile(r",\s*[(\[]\s*,|,\s*;\s*,")


def _check_placeholder_integrity(path: Path, lines: list[str], rep: Report) -> None:
    for i, line in enumerate(lines, 1):
        for m in _BROKEN_PLACEHOLDER.finditer(line):
            rep.findings.append(Finding(
                file=str(path), line=i, code="EXP-PLACEHOLDER-BROKEN",
                message="Placeholder giá trị của bảng kết quả bị phá "
                        "(dạng '= ,' thay vì '= —'). Đây là lỗi xử lý văn bản, không phải văn người viết.",
                evidence=line[max(0, m.start() - 45):m.end() + 25].strip(),
            ))
        for m in _COMMA_SOUP.finditer(line):
            rep.findings.append(Finding(
                file=str(path), line=i, code="EXP-PLACEHOLDER-SOUP",
                message="Ô bảng còn chuỗi dấu phẩy vô nghĩa — dấu hiệu placeholder '—' bị thay hàng loạt.",
                evidence=line[max(0, m.start() - 45):m.end() + 25].strip(),
            ))


# ── Luật 2: định dạng nguồn ───────────────────────────────────────────────────
# Không kiểm PMID có THẬT hay không (việc đó của kiem-chung-trich-dan / A12, cần
# mạng). Chỉ bắt PMID sai định dạng — thứ chắc chắn là lỗi dù chưa tra cứu.
# Bắt buộc có dấu hai chấm: đó là dạng TRÍCH DẪN thật ("PMID: 33886027"). Nếu
# nhận cả "PMID " thì mọi câu văn xuôi nhắc tới chữ PMID ("có PMID (kèm DOI...)",
# tiêu đề cột "Nguồn (PMID · DOI)") đều bị báo oan.
_PMID_BAD = re.compile(r"PMID:\s*(?!\d{1,9}\b)([^\s|.,;)\]]+)")
_DOI_BAD = re.compile(r"doi:\s*(?!10\.\d{4,9}/)([^\s|,;)\]]+)", re.IGNORECASE)


def _check_source_format(path: Path, lines: list[str], rep: Report) -> None:
    for i, line in enumerate(lines, 1):
        for m in _PMID_BAD.finditer(line):
            bad = m.group(1)
            if bad.strip("*_`[]") in {"", "—", "..."}:
                continue  # ô chờ điền, không phải sai định dạng
            rep.findings.append(Finding(
                file=str(path), line=i, code="EXP-PMID-FORMAT",
                message=f"PMID sai định dạng (phải là số): {bad!r}",
                evidence=line.strip()[:120],
            ))
        for m in _DOI_BAD.finditer(line):
            bad = m.group(1)
            if bad.strip("*_`[]") in {"", "—", "..."}:
                continue
            rep.findings.append(Finding(
                file=str(path), line=i, code="EXP-DOI-FORMAT",
                message=f"DOI sai định dạng (phải bắt đầu '10.'): {bad!r}",
                evidence=line.strip()[:120],
            ))


# ── Luật 3: disclaimer bắt buộc ───────────────────────────────────────────────
_DISCLAIMER = re.compile(
    r"cần bác sĩ kiểm chứng|bác sĩ kiểm chứng|chờ hội đồng|dự thảo|draft"
    r"|cần chủ nhiệm|chưa được phê duyệt",
    re.IGNORECASE,
)


# Thư mục fixture của bộ test (mã bắt đầu bằng PYTEST-/ZZ/REFUTE-/TEST-/T-G) là
# dữ liệu thử, không phải tài liệu nộp ra ngoài, nên miễn luật disclaimer. Các
# luật còn lại (placeholder, định dạng nguồn, markdown) vẫn áp dụng: lỗi hỏng
# vẫn là lỗi dù ở fixture.
_FIXTURE = re.compile(r"^(PYTEST-|ZZ|REFUTE-|TEST-|T-G|test-|phase_)")


def _is_fixture(path: Path) -> bool:
    return any(_FIXTURE.match(part) for part in path.parts)


def _check_disclaimer(path: Path, text: str, rep: Report) -> None:
    if path.name.startswith(INTERNAL_PREFIX) or _is_fixture(path):
        return
    if _DISCLAIMER.search(text):
        return
    rep.findings.append(Finding(
        file=str(path), line=1, code="EXP-NO-DISCLAIMER",
        message="Tài liệu nghiên cứu thiếu nhãn trạng thái/disclaimer "
                "('Cần bác sĩ kiểm chứng', '[DỰ THẢO]', 'chờ Hội đồng'...).",
        blocking=False,  # cảnh báo: một số artifact máy sinh có nhãn ở dạng khác
    ))


# ── Luật 4: dấu vết định danh người bệnh ──────────────────────────────────────
# Bắt PII dạng chắc chắn. Cố ý KHÔNG đoán tên người (dễ dương tính giả trong văn
# bản tiếng Việt); các mẫu dưới đây đều là định dạng máy nhận ra không nhầm.
# Cố ý KHÔNG bắt "dãy 10 chữ số": PMID, mã DOI và số tiền đều rơi vào mẫu đó,
# nhiễu nhiều hơn tín hiệu. Ba mẫu dưới đây máy nhận ra không nhầm.
_PII = [
    # SỬA vòng 26 (2026-09-05): \b không khớp được ngay trước "+" (dấu "+"
    # không phải \w, và ký tự đứng trước nó trong văn bản thật — khoảng
    # trắng, dấu ":", đầu dòng — cũng không phải \w, nên KHÔNG có ranh giới
    # từ ở đó) ⇒ nhánh "+84..." của regex cũ KHÔNG BAO GIỜ khớp trong bất kỳ
    # cách viết số điện thoại quốc tế thông thường nào (đã kiểm chứng bằng
    # thực nghiệm: "+84912345678" không khớp, "0912345678" vẫn khớp bình
    # thường). Dùng lookaround dựa trên chữ số thay vì \b — cùng cách
    # clinical_checkpoint.py đã làm cho SĐT_VN.
    (re.compile(r"(?<!\d)(?:0|\+84)\d{9,10}(?!\d)"), "số điện thoại"),
    (re.compile(r"\b\d{12}\b"), "số căn cước công dân 12 chữ số"),
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"), "địa chỉ email"),
]
# Ô mẫu để trống trên biểu mẫu (ICF) không phải PII thật.
_FORM_BLANK = re.compile(r"[…\.]{3,}|_{3,}|x{6,}", re.IGNORECASE)


def _check_pii(path: Path, lines: list[str], rep: Report) -> None:
    for i, line in enumerate(lines, 1):
        if _FORM_BLANK.search(line):
            continue
        for pat, name in _PII:
            m = pat.search(line)
            if not m:
                continue
            rep.findings.append(Finding(
                file=str(path), line=i, code="EXP-PII",
                message=f"Nghi có thông tin định danh ({name}) trong tài liệu nghiên cứu.",
                evidence=line.strip()[:110],
                blocking=False,  # cảnh báo để người đọc quyết: email liên hệ IRB là hợp lệ
            ))
            break


# ── Luật 5: cấu trúc markdown cân bằng ────────────────────────────────────────
def _check_markdown_balance(path: Path, text: str, rep: Report) -> None:
    if text.count("**") % 2 != 0:
        rep.findings.append(Finding(
            file=str(path), line=1, code="EXP-MD-BOLD-UNBALANCED",
            message=f"Số dấu '**' lẻ ({text.count('**')}) — có cụm in đậm bị cắt đôi, "
                    "bản Word sẽ hỏng định dạng từ chỗ đó trở đi.",
        ))
    # Đã thử một luật "ngoặc lệch theo từng dòng" và bỏ đi: markdown xuống dòng
    # giữa câu khiến nó báo oan hàng loạt (26 cảnh báo trên exports/ hiện tại,
    # gần như toàn dương tính giả). Cảnh báo bị nhiễu thì sẽ bị bỏ qua, nên ở đây
    # chỉ giữ luật '**' lẻ vốn chắc chắn và có hậu quả thấy được trên bản Word.


def check_file(path: Path, rep: Report) -> None:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        rep.findings.append(Finding(
            file=str(path), line=1, code="EXP-UNREADABLE",
            message=f"Không đọc được file: {exc}",
        ))
        return
    lines = text.split("\n")
    rep.files_checked += 1
    _check_placeholder_integrity(path, lines, rep)
    _check_source_format(path, lines, rep)
    _check_disclaimer(path, text, rep)
    _check_pii(path, lines, rep)
    _check_markdown_balance(path, text, rep)


def _staged_md_files() -> list[Path]:
    try:
        out = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            cwd=REPO, capture_output=True, text=True, check=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
    files = []
    for name in out.splitlines():
        if name.startswith("exports/") and name.endswith(".md"):
            p = REPO / name
            if p.exists():
                files.append(p)
    return files


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Kiểm liêm chính nội dung tài liệu nghiên cứu trong exports/."
    )
    ap.add_argument("--staged", action="store_true",
                    help="Chỉ kiểm file .md dưới exports/ đang được stage (dùng cho pre-commit).")
    ap.add_argument("--path", type=Path, help="Kiểm một file/thư mục cụ thể.")
    args = ap.parse_args()

    if args.path:
        targets = sorted(args.path.rglob("*.md")) if args.path.is_dir() else [args.path]
    elif args.staged:
        targets = _staged_md_files()
    else:
        targets = sorted(EXPORTS.rglob("*.md")) if EXPORTS.exists() else []

    if not targets:
        print("Không có tài liệu nào cần kiểm.")
        return 0

    rep = Report()
    for path in targets:
        check_file(path, rep)

    print("=" * 78)
    print(" KIỂM LIÊM CHÍNH NỘI DUNG — exports/")
    print("=" * 78)
    print(f"  Đã kiểm: {rep.files_checked} tài liệu")

    if rep.blocking:
        print(f"\n  🔴 LỖI CHẶN ({len(rep.blocking)}):")
        for f in rep.blocking:
            rel = Path(f.file).relative_to(REPO) if str(f.file).startswith(str(REPO)) else f.file
            print(f"    [{f.code}] {rel}:{f.line}")
            print(f"      {f.message}")
            if f.evidence:
                print(f"      → {f.evidence}")

    if rep.warnings:
        print(f"\n  🟡 CẢNH BÁO ({len(rep.warnings)}) — không chặn commit:")
        for f in rep.warnings[:12]:
            rel = Path(f.file).relative_to(REPO) if str(f.file).startswith(str(REPO)) else f.file
            print(f"    [{f.code}] {rel}:{f.line} — {f.message}")
        if len(rep.warnings) > 12:
            print(f"    ... và {len(rep.warnings) - 12} cảnh báo nữa")

    if not rep.findings:
        print("\n  ✅ Không phát hiện lỗi liêm chính nội dung.")

    print("\n  Phạm vi: kiểm dấu hiệu hỏng đọc được bằng máy. KHÔNG thay thẩm định")
    print("  khoa học của bác sĩ, không thay quality gate G0-G10.")
    print("  Cần bác sĩ kiểm chứng.")
    print("=" * 78)
    return 1 if rep.blocking else 0


if __name__ == "__main__":
    sys.exit(main())
