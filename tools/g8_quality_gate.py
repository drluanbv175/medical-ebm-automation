#!/usr/bin/env python3
"""Hợp đồng chất lượng G8: bình duyệt độc lập trước khi nộp bài.

Vì sao module này tồn tại
─────────────────────────
G8 đã là một cổng KÝ thật (``_GATE_REQUIRED_STAKEHOLDERS["G8"] =
("INDEPENDENT_PEER_REVIEWER",)``) và lớp mật mã quanh nó khá dày: chữ ký
HMAC-SHA256 payload v4 có buộc NHÓM VAI TRÒ, chuỗi băm ``prev_hash`` chống
xóa/đảo/chèn, con dấu ``approval_ledger.seal.json`` chống cắt đuôi, và
``run_g10_assemble.py`` fail-closed khi thiếu chữ ký.

Nhưng có một khoảng trống NỘI DUNG mà lớp mật mã không thể lấp được:

**Artifact mà chữ ký G8 ràng buộc vào — ``G8_A9_PRESUBMISSION_<study>.md`` — là
bản TỰ KIỂM do chính ``run_g8_auto.py`` sinh ra từ checkpoint G0–G7, KHÔNG phải
bản nhận xét của người bình duyệt.** Nó có 7 phần (kiểm toán pipeline, checklist
chuẩn báo cáo, toàn vẹn thống kê, gợi ý tạp chí, gói khai báo tác giả, tự chấm
30 điểm, tiêu chí qua cổng) và không phần nào chứa phát hiện/khuyến nghị của một
người phản biện. Vì vậy một chữ ký G8 hợp lệ chỉ chứng minh:

    "một người truy cập được khóa ký đã xác nhận bản TỰ KIỂM này, với nội dung
     đúng bằng hash tại thời điểm ký, và tự khai vai trò là phản biện độc lập"

Nó KHÔNG chứng minh rằng một cuộc bình duyệt độc lập đã thực sự diễn ra, và cũng
không chứng minh người ký khác chủ nhiệm đề tài — vì HMAC là mật mã ĐỐI XỨNG nên
máy xác minh buộc phải giữ đúng khóa đã ký; trên một máy đơn, cấu hình khả thi
duy nhất lại chính là cấu hình mà một người giữ đủ mọi khóa.

Module này KHÔNG cố sửa giới hạn mật mã đó (việc đó cần chuyển sang chữ ký bất
đối xứng — thuộc thẩm quyền bác sĩ). Nó làm ba việc trong tầm với:

1. **Nói đúng mức bảo đảm.** Không bao giờ phát ngôn "đã có bình duyệt độc lập"
   vô điều kiện; luôn kèm phạm vi khóa (``role`` / ``shared`` / không xác định).
2. **Đòi bằng chứng NỘI DUNG của việc bình duyệt** — một bản nhận xét riêng có
   khuyến nghị, lỗi nghiêm trọng kèm vị trí, và khai báo độc lập/COI của người
   phản biện (doctrine ``binh-duyet.md`` đã quy định mẫu này; code chưa làm).
3. **Kiểm những thứ máy kiểm được mà hiện không ai kiểm**: đổi kết cục chính so
   với SAP (selective outcome reporting), vệt công cụ nội bộ còn sót trong bản
   thảo, và các nghĩa vụ ICMJE bản 1/2026 ở thời điểm tiền nộp bài.

Giới hạn đã biết (ghi rõ để không ai đọc nhầm)
─────────────────────────────────────────────
- ``PASS_G8_REVIEW_RECORDED`` CỐ Ý không mang chữ "ĐỘC LẬP": hệ không biết điều
  đó có thật hay không.
- Từ 24/08/2026 ``approve_gate.py --gate G8`` dùng CHÍNH module này để TỪ CHỐI ký: trạng thái phải là PENDING/
  REVIEWED và các tiêu chí người kiểm được trước khi ký (G8-HUMAN-01/05/06) phải PASS. Cổng sau (G9, G10) hỏi sổ cái
  G8 và đối chiếu băm bản thảo + bản nhận xét nhúng trong A9 (hợp đồng CHUNG-E, cong_song.trich_bam_a9). SỬA
  05/10/2026 (soát từng cổng G8-15): câu cũ «module này KHÔNG phải cổng chặn, chốt duy nhất là run_g10_assemble.py»
  không còn đúng.
- KHÔNG được đổi tên ``G8_A9_PRESUBMISSION_<study>.md``: tên này là hợp đồng ba
  bên (run_g8_auto ghi · run_g10_assemble tra ledger · doctrine dạy bác sĩ gõ
  tay vào approve_gate --artifact) và nội dung nó bị băm trong chữ ký. Tên "A9"
  lệch crosswalk (A9 thật = DMP ở G5, bình duyệt = A15) nhưng đó là lệch ĐÃ BIẾT
  và sửa tên sẽ phá cổng G10 lẫn mọi chữ ký cũ.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re

# Windows: stdout mặc định cp1252 giết print() tiếng Việt — ép UTF-8 (chốt BH55/R4)
import sys as _sys_r4
import unicodedata
from datetime import date
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

import cong_song as CS
import gate_contract as GC
import pipeline_freshness as PF
import placeholder_contract as PC

for _s_r4 in (_sys_r4.stdout, _sys_r4.stderr):
    try:
        _s_r4.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

STATUS_BLOCKED = "BLOCKED"
STATUS_DRAFT = "DRAFT_NEEDS_HUMAN_COMPLETION"
STATUS_READY = "READY_FOR_INDEPENDENT_REVIEW"
STATUS_PENDING = "PENDING_REAL_REVIEW_SIGNATURE"
STATUS_REVIEWED = "PASS_G8_REVIEW_RECORDED"

QUALITY_CONTRACT_VERSION = "G8-2026.2"  # 05/10/2026: soát từng cổng G8

REVIEWER_ROLE_GROUP = "INDEPENDENT_PEER_REVIEWER"

# Tên artifact — HỢP ĐỒNG downstream, không được đổi (xem docstring module).
def presubmission_artifact_name(study: str) -> str:
    return f"G8_A9_PRESUBMISSION_{study}.md"


def manuscript_artifact_name(study: str) -> str:
    return f"G7_A8_MANUSCRIPT_{study}.md"


# Artifact MỚI mà hợp đồng này đòi: bản nhận xét THẬT của người bình duyệt.
# run_g8_auto.py không sinh file này (và không nên sinh — máy không được tự viết
# nhận xét phản biện rồi tự ký). Thiếu nó là REVIEW, không phải BLOCK.
def peer_review_report_name(study: str) -> str:
    return f"G8_PEER_REVIEW_REPORT_{study}.md"


# Mục bắt buộc của bản nhận xét phản biện, theo mẫu TỔNG HỢP của
# .claude/agents/binh-duyet.md (khuyến nghị 4 mức · lỗi nghiêm trọng kèm vị trí ·
# góp ý nhỏ · câu hỏi cho tác giả · kết luận tổng thể).
_REVIEW_REPORT_SECTIONS: Sequence[tuple[str, Sequence[str]]] = (
    ("KHUYẾN NGHỊ", ("KHUYẾN NGHỊ", "RECOMMENDATION")),
    ("LỖI NGHIÊM TRỌNG", ("LỖI NGHIÊM TRỌNG", "MAJOR")),
    ("GÓP Ý NHỎ", ("GÓP Ý NHỎ", "MINOR")),
    ("CÂU HỎI CHO TÁC GIẢ", ("CÂU HỎI CHO TÁC GIẢ", "QUESTIONS FOR THE AUTHORS")),
    ("KẾT LUẬN TỔNG THỂ", ("KẾT LUẬN TỔNG THỂ", "OVERALL")),
)

_REVIEW_RECOMMENDATIONS = (
    "CHẤP NHẬN",
    "SỬA NHỎ",
    "SỬA LỚN",
    "TỪ CHỐI",
    "ACCEPT",
    "MINOR REVISION",
    "MAJOR REVISION",
    "REJECT",
)

# ── Bản nhận xét chép nguyên MẪU (thêm 03/10/2026) ─────────────────────────────────────────────────────────
# Lượt đo: khối «TỔNG HỢP — NHẬN XÉT PHẢN BIỆN CUỐI» chép nguyên từ binh-duyet.md (chưa điền gì) qua G8-HUMAN-01
# ⇒ PASS_G8_REVIEW_RECORDED, vì dòng mẫu «KHUYẾN NGHỊ: ☐ Chấp nhận ☐ Sửa nhỏ ☐ Sửa lớn ☐ Từ chối» liệt kê ĐỦ 4 mức
# nên tự thoả «có khuyến nghị rõ mức». Ba chốt tối thiểu: khuyến nghị phải được CHỌN (tích ☑/☒/[x] đúng MỘT mức,
# hoặc chỉ còn một mức); kết luận không còn để cả hai lựa chọn; không còn ô mẫu của khuôn (ngoặc mẫu, «___» ngoài
# dòng tích chọn, bảng chỉ có số thứ tự).
_REVIEW_LEVEL_ALTS: Mapping[str, str] = {
    "chấp nhận": r"(?:CHẤP NHẬN|ACCEPT(?:ED)?)",
    "sửa nhỏ": r"(?:SỬA NHỎ|MINOR REVISIONS?)",
    "sửa lớn": r"(?:SỬA LỚN|MAJOR REVISIONS?)",
    "từ chối": r"(?:TỪ CHỐI|REJECT(?:ED|ION)?)",
}
_TICK_MARK = r"(?:☑|☒|✓|✔|■|\[X\])"
_OPEN_BOX = r"(?:☐|\[ \])"
_LEVEL_TICKED_RE = {k: re.compile(_TICK_MARK + r"\s*\**\s*" + v + r"(?!\w)") for k, v in _REVIEW_LEVEL_ALTS.items()}
_LEVEL_BOXED_RE = {k: re.compile(_OPEN_BOX + r"\s*\**\s*" + v + r"(?!\w)") for k, v in _REVIEW_LEVEL_ALTS.items()}
# «Accept with minor revisions» / «chấp nhận sau khi sửa nhỏ» là MỘT mức (sửa nhỏ), không phải hai.
_ACCEPT_WITH_RE = re.compile(
    r"(?:ACCEPT(?:ED)?\s+(?:WITH|AFTER)|CHẤP NHẬN\s+(?:VỚI|SAU KHI|KÈM))\s+"
    r"(?=(?:MINOR|MAJOR)\s+REVISION|SỬA (?:NHỎ|LỚN))"
)
_RECOMMENDATION_KEY_RE = re.compile(r"KHUYẾN NGHỊ|RECOMMENDATION", re.IGNORECASE)
# Dòng kết luận của mẫu còn để nguyên cả hai lựa chọn.
_UNCHOSEN_CONCLUSION_RE = re.compile(r"sẵn sàng nộp\s*/\s*cần sửa thêm", re.IGNORECASE)
# Ngoặc mẫu của khuôn binh-duyet.md (so không phân biệt hoa/thường; MAU_CHUNG chỉ nhận «[tên…]» chữ thường).
_REVIEW_TEMPLATE_LITERALS = (
    "[Tên bài]",
    "[Tên thiết kế]",
    "[Ngày]",
    "[CONSORT/STROBE/...]",
    "[Người phản biện tự điền",
)
# Trích dẫn nguyên văn từ bản thảo (người phản biện chỉ ra «N = ___» còn sót) KHÔNG phải ô trống của bản nhận xét.
_QUOTED_SPAN_RE = re.compile(r"`[^`\n]*`|«[^»\n]*»|“[^”\n]*”|\"[^\"\n]*\"")
_CHECKBOX_CHAR_RE = re.compile(r"[☐☑☒]|\[[ xX]\]")
_TABLE_SEPARATOR_RE = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(?:\|\s*:?-{2,}:?\s*)*\|?\s*$")

# "Vệt công cụ nội bộ" — doctrine binh-duyet.md §Lăng kính 3 mục 8 xếp mức CHẶN:
# còn sót bất kỳ mục nào = KHÔNG sẵn sàng nộp, không phải góp ý nhỏ.
_INTERNAL_TRACE_PATTERNS: Sequence[tuple[str, Any]] = (
    ("nhãn [CẦN…] còn trong thân bài", re.compile(r"\[CẦN[^\]]{0,80}\]")),
    # SỬA 05/10/2026 (soát từng cổng G8-11): «\bagent\b» trần CHẶN oan thuật ngữ dược lý tiếng Anh («contrast agent»,
    # «single agent», «alkylating agent») trong bản thảo nộp quốc tế — cùng họ lỗi «Todorov/TODO» đã sửa 03/10. Nay chỉ
    # bắt «agent» trong NGỮ CẢNH của hệ: kèm tên trong backtick hoặc tên kebab-case viết thường của agent nội bộ
    # (kiem-chung-trich-dan), «sub-agent», «.claude/agents», hoặc đứng trong câu tiếng Việt («dùng agent», «agent tự…»).
    (
        "nhắc tới 'agent' của hệ nội bộ",
        re.compile(
            r"(?i:\bsub-?agents?\b|\.claude/agents|\bagents?\s+`[^`\n]+`"
            r"|\b(?:các|một|nhờ|dùng|gọi|chạy|bởi|giao)\s+agents?\b"
            r"|\bagents?\s+(?:của|tự|đã|sẽ|này|khác|phụ|con|kiểm|rà)\b)"
            r"|(?i:\bagents?)\s+[a-z]+(?:-[a-z]+)+\b"
        ),
    ),
    ("nhắc 'checklist nội bộ'", re.compile(r"checklist\s+nội\s+bộ", re.IGNORECASE)),
    (
        "hướng dẫn biên tập còn sót",
        # SỬA 03/10/2026 (báo nhầm ĐÃ CHỨNG MINH ở lượt đo cùng ngày): TODO/FIXME/XXX trước đây khớp như chuỗi
        # con không ranh giới ⇒ tên tác giả «Todorov» trong TLTK, chữ «Todos», mặt nạ «0xxx-xxx» CHẶN oan và
        # không sửa được. Nay chỉ khớp khi đứng thành TOKEN (không dính chữ/số/gạch nối hai bên) — «TODO»,
        # «TODO:», «[TODO]», «XXX», «FIXME» vẫn bắt như cũ.
        re.compile(
            r"(cần chủ nhiệm bổ sung|điền vào đây|(?<![A-Za-z0-9-])(?:TODO|FIXME|XXX)(?![A-Za-z0-9-]))",
            re.IGNORECASE,
        ),
    ),
    (
        "lựa chọn (A) hay (B) còn bỏ ngỏ",
        re.compile(r"\(A\)\s*(hay|hoặc|or)\s*\(B\)", re.IGNORECASE),
    ),
    (
        "tên file/công cụ nội bộ của pipeline",
        re.compile(r"(run_g\d+_auto\.py|G\d_checkpoint\.json|study_meta\.json|approval_ledger)", re.IGNORECASE),
    ),
)

# ── Ô CÒN TRỐNG / Ô MẪU trong phần bản thảo GỬI tạp chí (thêm 03/10/2026, bộ dò chung placeholder_contract) ──
# Lượt đo thật cùng ngày: bản thảo do run_g7_auto.generate_manuscript sinh, điền hết nhãn [CẦN…] bằng chữ rồi bỏ
# dòng «agent» ⇒ G8-AUTO-04 PASS dù còn «N = ___», «[Ước lượng hiệu quả]», «CẦN KẾT QUẢ THẬT» trong tiêu đề mục,
# banner nháp; mẫu nhãn cũ «\[CẦN[^\]]{0,80}\]» còn bỏ sót 10 nhãn dài >80 ký tự, «[CAN]», «[Cần …]». Lớp này
# BỔ SUNG cho _INTERNAL_TRACE_PATTERNS (không thay):
#   • họ NHAN (mọi [CẦN…] mọi hoa/thường, không giới hạn độ dài; [CAN …] chữ hoa; [TODO]/[TBD]/[TO BE COMPLETED];
#     <…điền…>…) + MAU_CHUNG («[đơn vị]», «thuốc/can thiệp X», «[… — điền]»…);
#   • họ TRONG («___», «……») chỉ trên dòng NGOÀI bảng và không tính dòng chỉ toàn gạch dưới (đường kẻ Markdown);
#   • ô mẫu RIÊNG của khuôn G7 không mang nhãn (danh sách dưới, đo trên bản thảo sinh thật).
# KHÔNG dùng «ngoặc vuông chung» trần: bản thảo thật có trích dẫn số «[1]», «[10]», nhãn «[V1]» (bài giao thức C1a).
# KHÔNG kế thừa \bagent\b hay TODO/XXX vào bộ dò chung — hai mẫu đó là luật RIÊNG của G8 ở trên.
_MANUSCRIPT_FAMILIES = (PC.NHAN, PC.MAU_CHUNG)
# Chuỗi con nguyên văn (so không phân biệt hoa/thường) của khuôn run_g7_auto.py — chỉ xuất hiện khi CHƯA soạn xong.
_G7_TEMPLATE_LITERALS = (
    "[Ước lượng hiệu quả]",
    "[kết cục chính]",
    "[cơ sở/quần thể]",
    "[thời gian]",
    "[loại thiết kế]",
    "[kết quả thật]",
    "[Năm]",
    "Gợi ý cấu trúc:",
    "BẢN NHÁP TỰ ĐỘNG",
    "IMRAD SKELETON",
    "(Bắt đầu bằng:",
    "chỉ điền sau khi có kết quả thật",
    "sinh từ kết quả thật",
    "BẢNG ƯỚC TÍNH SỐ TỪ",
    "Kiểm chứng bắt buộc trước khi nộp",
    "(Không liệt kê AI là tác giả",
    "PMID seed",
    # 04/10/2026 (soát từng cổng G7-06, bộ quét DÙNG CHUNG G7-AUTO-05/G8-AUTO-04): cờ mà doctrine viet-ban-thao.md bắt
    # gắn cho trích dẫn không xác minh được — «KHÔNG để lọt vào bản nộp» — trước ngày này không họ nhãn nào bắt.
    "[TRÍCH DẪN CHƯA XÁC MINH",
    # 05/10/2026 (điều phối G7↔G8): dòng chỉ dẫn «> • …» của khuôn G7 không mang nhãn — trước đây chỉ dòng ĐẦU mỗi khối
    # bị bắt, các gạch đầu dòng sau (kể cả «Dùng agent `kiem-chung-trich-dan`») lọt vào bản thảo «đã soạn xong».
    "chứa TOÀN BỘ placeholder",
    "KHÔNG điền số liệu giả",
    "cần bác sĩ điền thông tin thực",
    "dùng làm seed TLTK",
    "phải chứa: thiết kế + quần thể + kết cục",
    "Điền sau khi: G5",
    "Không được điền số liệu ước tính/giả định",
    "Xác minh tác giả/volume/số/trang toàn văn",
    "kiem-chung-trich-dan` hoặc PubMed trực tiếp",
    "Định dạng Vancouver đầy đủ (theo hướng dẫn tác giả tạp chí)",
)
# Mẫu riêng của khuôn G7 cần biểu thức. «KẾT QUẢ THẬT» CỐ Ý phân biệt hoa/thường: khuôn luôn in CHỮ HOA («CẦN/CHỜ/
# yêu cầu KẾT QUẢ THẬT»), còn văn xuôi «kết quả thật sự…» là hợp lệ.
_G7_TEMPLATE_PATTERNS: Sequence[tuple[str, Any]] = (
    ("cụm «KẾT QUẢ THẬT» của khuôn G7", re.compile(r"KẾT QUẢ THẬT")),
    ("chú thích khuôn trong tiêu đề mục", re.compile(r"\*\((?:ước tính:[^)\n]*|điền thủ công)\)\*", re.IGNORECASE)),
    ("trỏ tệp bảng nội bộ của G6", re.compile(r"\(Xem file Table\d*\.docx", re.IGNORECASE)),
)
# Đường kẻ ngang Markdown («---», «***», «___» đứng riêng một dòng) — không phải ô trống.
_HR_LINE_RE = re.compile(r"^\s{0,3}(?:-{3,}|\*{3,}|_{3,})\s*$")
# Mốc phụ lục kiểm tra NỘI BỘ ở cuối bản thảo (không gửi tạp chí) — dùng chung cho _body_without_labels_section.
_INTERNAL_APPENDIX_MARKERS = ("## PHỤ LỤC", "## APPENDIX", "<!-- INTERNAL", "## CHECKLIST NỘI BỘ")

# ICMJE bản Updated January 2026 — Mục V (AI) là phần cấp 1 quan trọng cho khai báo AI.
# SỬA 2026-07-31 (audit tích hợp plugin, phát hiện qua rà lại các "chưa sửa" cũ trong CLAUDE.md):
# comment này TỪNG nói nhãn "ICMJE 2023" "hiện còn" trong run_g8_auto.py là STALE — đã lỗi thời,
# nhãn đó đã được sửa xong ở run_g8_auto.py từ trước (đọc đúng "ICMJE Mục V, bản cập nhật 1/2026");
# comment cũ mô tả một trạng thái không còn đúng. Giữ lại như ghi chú LỊCH SỬ về lý do có bộ token
# dưới đây (bắt câu khai báo AI thật, không phải kiểm tra nhãn chuẩn).
_AI_DISCLOSURE_TOKENS = ("trí tuệ nhân tạo", "artificial intelligence", "AI-assisted", "LLM")
_AI_TOOL_NAME_RE = re.compile(
    r"(chatgpt|gpt-?[0-9]|claude|gemini|copilot|bard|llama|mistral)", re.IGNORECASE
)

_REGISTRY_ID_RE = re.compile(
    r"(NCT\d{8}|ISRCTN\d{8}|ChiCTR[-A-Za-z0-9]+|CTRI/\d{4}/\d{2}/\d+|"
    r"IRCT\d+[A-Za-z0-9]*|jRCT\d+|ACTRN\d{14}|EUCTR[\d-]+)"
)

# Thiết kế thỏa ĐỊNH NGHĨA THỬ NGHIỆM của ICMJE ("prospectively assigns people to
# an intervention"). CỐ Ý rộng hơn design_code=="rct": ICMJE liệt kê đích danh cả
# can thiệp cải tiến chất lượng, giáo dục, hành vi. Với thiết kế quan sát, ICMJE
# KHUYẾN KHÍCH chứ không bắt buộc đăng ký ⇒ chỉ nhắc, không tính là lỗi.
_TRIAL_LIKE_DESIGNS = frozenset({"rct"})
_REGISTRATION_ENCOURAGED_DESIGNS = frozenset({"cohort", "cross_sectional", "case_control"})

# 5 trường bắt buộc của data sharing statement (ICMJE §III.L.3).
_DATA_SHARING_FIELDS: Sequence[tuple[str, Sequence[str]]] = (
    ("có chia sẻ IPD hay không", ("chia sẻ", "share")),
    ("dữ liệu nào được chia sẻ", ("dữ liệu nào", "what data")),
    ("tài liệu kèm theo", ("protocol", "đề cương", "SAP")),
    ("mốc thời gian", ("thời gian", "when", "bắt đầu")),
    ("tiêu chí truy cập", ("tiêu chí", "access", "cơ chế")),
)

STANDARDS_BASIS: Sequence[Mapping[str, str]] = (
    {
        "standard": "ICMJE Recommendations (Updated January 2026) — Mục V: Use of AI in Publishing",
        "scope": (
            "V.A: khai báo AI ở CẢ cover letter lẫn bản thảo, nêu công cụ/mục đích, "
            "cấm liệt kê AI là tác giả, cấm trích dẫn nội dung AI làm nguồn gốc; "
            "V.B: người PHẢN BIỆN phải khai dùng AI và không tải bản thảo lên công "
            "cụ không bảo đảm bảo mật"
        ),
        "url": "https://www.icmje.org/icmje-recommendations.pdf",
    },
    {
        "standard": "ICMJE §II.B.1.b — nghĩa vụ của người bình duyệt",
        "scope": (
            "Người phản biện phải khai mọi quan hệ/hoạt động có thể làm thiên lệch "
            "ý kiến và phải TỪ CHỐI khi có xung đột"
        ),
        "url": "https://www.icmje.org/icmje-recommendations.pdf",
    },
    {
        "standard": "ICMJE §III.L.1 — đăng ký nghiên cứu trước tuyển ca đầu tiên",
        "scope": (
            "Điều kiện để được xem xét đăng; phê duyệt của Hội đồng Đạo đức KHÔNG "
            "thay thế được đăng ký; đăng ký hồi cứu không đạt mục đích nào"
        ),
        "url": "https://www.icmje.org/icmje-recommendations.pdf",
    },
    {
        "standard": "ICMJE §III.L.3 — tuyên bố chia sẻ dữ liệu",
        "scope": (
            "Báo cáo kết quả thử nghiệm lâm sàng phải có đủ 5 trường; "
            "'undecided' KHÔNG phải câu trả lời chấp nhận được"
        ),
        "url": "https://www.icmje.org/icmje-recommendations.pdf",
    },
    {
        "standard": "ICMJE §IV.B — nội dung bắt buộc của cover letter",
        "scope": (
            "Khai mọi bản nộp/báo cáo trước có thể bị coi là trùng lặp; COI; xác nhận "
            "mọi tác giả đã đọc và duyệt; thông tin liên hệ; trạng thái preprint"
        ),
        "url": "https://www.icmje.org/icmje-recommendations.pdf",
    },
    {
        "standard": "Cochrane RoB — miền báo cáo kết quả chọn lọc (selective reporting)",
        "scope": (
            "Kết cục chính trong bản thảo phải khớp kết cục chính đã định trước ở "
            "SAP/đăng ký; lệch mà không giải trình là sai lệch báo cáo"
        ),
        "url": "https://methods.cochrane.org/risk-bias-2",
    },
)


# ════════════════════════════════════════════════════════════════════════════
# Tiện ích
# ════════════════════════════════════════════════════════════════════════════


def _criterion(criterion_id: str, label: str, status: str, evidence: str,
               action: str = "") -> dict[str, str]:
    return {
        "id": criterion_id,
        "label": label,
        "status": status,
        "evidence": evidence,
        "action": action,
    }


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _read_text(path: Path) -> str:
    try:
        return Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


# Khớp đúng nhãn máy-đọc-được mà run_g8_auto.py::generate_a9_artifact() nhúng
# vào A9 -- xem comment tại chỗ ở đó. Đổi định dạng dòng đó bắt buộc phải sửa
# regex này theo, nếu không G8-AUTO-12 sẽ luôn REVIEW ("chưa nhúng hash") dù
# nhãn có mặt.
_MANUSCRIPT_HASH_RE = re.compile(
    r"Hash SHA-256 bản thảo đã ràng buộc[^:]*:\*\*\s*`([0-9a-f]{64})`", re.IGNORECASE
)


def _trich_hash_ban_thao_da_ky(presubmission_text: str) -> Optional[str]:
    """Trích hash SHA-256 bản thảo đã nhúng trong A9 -- None nếu không thấy
    (artifact định dạng cũ trước bản vá này, hoặc chưa có bản thảo lúc sinh)."""
    m = _MANUSCRIPT_HASH_RE.search(presubmission_text or "")
    return m.group(1) if m else None


def _g8_meta(meta: Mapping[str, Any]) -> Mapping[str, Any]:
    params = meta.get("gate_params")
    if not isinstance(params, Mapping):
        return {}
    value = params.get("G8")
    return value if isinstance(value, Mapping) else {}


def _present(value: Any) -> bool:
    """Giá trị gate_params.G8 có nội dung thật không.

    Giữ NGUYÊN chốt cũ (rỗng/None; «[CẦN»/«[CAN» so trên chữ HOA — tức không phân biệt hoa/thường) rồi AND thêm
    vị từ chung ``placeholder_contract.co_noi_dung_that`` (03/10/2026): «___», «TBD» trong ngoặc, «[đơn vị]», ký hiệu
    đứng một mình «?»/«-»/«xxx»… trước đây được coi là đã điền (lượt đo: _present('___') == True)."""
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return False
        if "[CẦN" in text.upper() or "[CAN" in text.upper():
            return False
        return PC.co_noi_dung_that(text)
    return bool(value) and PC.co_noi_dung_that(value)


def _body_without_labels_section(manuscript: str) -> str:
    """Thân bài, bỏ phần phụ lục/checklist ở cuối nếu có.

    Quét vệt công cụ nội bộ chỉ có nghĩa trên phần sẽ gửi tạp chí; nếu bản thảo có
    mục phụ lục kiểm tra nội bộ thì phần đó không phải "sót".
    """
    for marker in _INTERNAL_APPENDIX_MARKERS:
        idx = manuscript.find(marker)
        if idx > 0:
            return manuscript[:idx]
    return manuscript


def _cut_at_internal_appendix(text: str) -> str:
    """Cắt tại mốc phụ lục nội bộ SỚM NHẤT (kể cả ở vị trí 0) — dùng cho phần đuôi sau phụ lục."""
    hits = [i for i in (text.find(m) for m in _INTERNAL_APPENDIX_MARKERS) if i >= 0]
    return text[:min(hits)] if hits else text


def _manuscript_scan_regions(manuscript: str) -> list[str]:
    """Các đoạn bản thảo SẼ GỬI tạp chí cần quét.

    (1) Thân bài như quy ước cũ (bỏ phụ lục kiểm tra nội bộ — test khoá). (2) THÊM 03/10/2026 (khoảng hở thấp của
    lượt đo): phần ĐUÔI sau đường kẻ ngang cuối cùng nằm SAU phụ lục — khuôn G7 luôn nối «---» rồi banner
    «[BẢN NHÁP TỰ ĐỘNG — DRAFT G7] …» ở đó, trước đây bị cắt bỏ cùng phụ lục. Đuôi lại bắt đầu bằng phụ lục khác thì
    vẫn bỏ phần phụ lục đó."""
    body = _body_without_labels_section(manuscript)
    regions = [body]
    rest = manuscript[len(body):]
    if rest:
        offset, last_hr_end = 0, None
        for line in rest.splitlines(keepends=True):
            offset += len(line)
            if _HR_LINE_RE.match(line.rstrip("\r\n")):
                last_hr_end = offset
        if last_hr_end is not None:
            regions.append(_cut_at_internal_appendix(rest[last_hr_end:]))
    return regions


def _nfc(text: Any) -> str:
    return unicodedata.normalize("NFC", str(text or ""))


def _excerpt(line: str, needle: str, width: int = 32) -> str:
    """Trích ngắn quanh chỗ khớp để làm bằng chứng (không in cả dòng dài)."""
    idx = line.find(needle) if needle else -1
    if idx < 0:
        return line[: 2 * width]
    start, end = max(0, idx - width), min(len(line), idx + len(needle) + width)
    return ("…" if start else "") + line[start:end] + ("…" if end < len(line) else "")


def manuscript_residues(manuscript: str) -> list[str]:
    """Ô còn trống / ô mẫu chưa điền trong phần bản thảo gửi tạp chí — mỗi DÒNG một bằng chứng «…trích…».

    Dùng cho G8-AUTO-04 (CHẶN). G9-AUTO-05 CHƯA nối (04/10/2026 — phần G9 của lượt tích hợp chưa làm); khi nối, gọi
    chính hàm này để hai cổng nói MỘT chuyện."""
    found: list[str] = []
    seen: set[str] = set()

    def _add(line: str, needle: str) -> None:
        compact = re.sub(r"\s+", " ", line.strip())
        if compact in seen:
            return
        seen.add(compact)
        compact_needle = re.sub(r"\s+", " ", needle.strip())
        found.append("«" + _excerpt(compact, compact_needle) + "»")

    for region in _manuscript_scan_regions(_nfc(manuscript)):
        for hit in PC.tim(region, _MANUSCRIPT_FAMILIES, them=_G7_TEMPLATE_LITERALS):
            _add(hit.dong, hit.khop)
        for line in region.splitlines():
            if not line.strip():
                continue
            for _label, pattern in _G7_TEMPLATE_PATTERNS:
                match = pattern.search(line)
                if match:
                    _add(line, match.group(0))
            if line.lstrip().startswith("|") or _HR_LINE_RE.match(line):
                continue
            for hit in PC.tim(line, (PC.TRONG,)):
                _add(line, hit.khop)
    return found


def ledger_records(study: str, repo_root: Path) -> list[dict[str, Any]]:
    """Đọc sổ cái phê duyệt dạng thô (chỉ để ĐỐI CHIẾU, không để phán cổng)."""
    path = Path(repo_root) / "exports" / str(study) / "approval_ledger.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return []
    return [r for r in value if isinstance(r, dict)] if isinstance(value, list) else []


def _latest_approved(records: Sequence[Mapping[str, Any]], gate_id: str) -> Optional[Mapping[str, Any]]:
    """Bản ghi APPROVED mới nhất của một cổng, theo timestamp ISO.

    CỐ Ý chỉ dùng cho việc ĐỐI CHIẾU reviewer_ref giữa các cổng (một báo cáo, không
    phải một phán quyết). Mọi kết luận "cổng đã duyệt hay chưa" phải hỏi
    ``GC.ledger_approved`` để hai nơi không đọc cùng một sổ mà nói hai chuyện.
    """
    candidates = [
        r for r in records
        if str(r.get("gate_id", "")).strip().upper() == gate_id.upper()
        and str(r.get("decision", "")).strip().upper() == "APPROVED"
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda r: str(r.get("timestamp_utc", "")))


def _reviewer_ref(record: Optional[Mapping[str, Any]]) -> str:
    if not record:
        return ""
    for key in ("reviewer_identity_reference", "reviewer_ref"):
        value = str(record.get(key) or "").strip()
        if value:
            return value
    return ""


def norm_ref(ref: Any) -> str:
    """Chuẩn hoá reviewer_ref để SO người ký giữa các cổng: NFC, không phân biệt hoa/thường, bỏ khoảng trắng/./_/-.

    SỬA 05/10/2026 (soát từng cổng G8-14): «pi-01» ở G8 và «PI-01» ở G2/G4/G9 từng bị coi là hai người khác nhau ⇒
    G8-HUMAN-04 («người ký G8 khác người ký các cổng khác») PASS sai. G9 dùng lại hàm này."""
    return re.sub(r"[\s._\-]+", "", unicodedata.normalize("NFC", str(ref or "")).casefold())


# ════════════════════════════════════════════════════════════════════════════
# Các phép kiểm nội dung
# ════════════════════════════════════════════════════════════════════════════


def scan_internal_traces(manuscript: str) -> list[str]:
    """Tìm vệt công cụ nội bộ còn sót trong bản thảo (doctrine xếp mức CHẶN).

    Ô trống/ô mẫu chưa điền do ``manuscript_residues`` đảm nhận (bộ dò chung); hàm này giữ đúng các luật riêng
    của doctrine binh-duyet.md (Lăng kính 3, mục 8). Từ 03/10/2026 quét cả phần đuôi sau phụ lục (xem
    ``_manuscript_scan_regions``)."""
    body = "\n".join(_manuscript_scan_regions(manuscript))
    found: list[str] = []
    for label, pattern in _INTERNAL_TRACE_PATTERNS:
        match = pattern.search(body)
        if match:
            snippet = re.sub(r"\s+", " ", match.group(0))[:60]
            found.append(f"{label} ({snippet!r})")
    return found


def _chuan_kc(text: Any) -> str:
    """Chuẩn hoá để so một KẾT CỤC: NFC, chữ thường, bỏ đánh dấu Markdown/backtick, dấu thanh kiểu cũ/mới về một kiểu
    (khoá → khóa), gọn khoảng trắng và dấu câu hai đầu."""
    t = _nfc(text).casefold()
    t = re.sub(r"[*_`>#|]", " ", t)
    for cu, moi in (("oá", "óa"), ("oà", "òa"), ("oả", "ỏa"), ("oã", "õa"), ("oạ", "ọa"),
                    ("uý", "úy"), ("uỳ", "ùy"), ("uỷ", "ủy"), ("uỹ", "ũy"), ("uỵ", "ụy")):
        t = t.replace(cu, moi)
    return re.sub(r"\s+", " ", t).strip(" .;,:")


# Dòng KHAI kết cục trong SAP: nhãn đứng ĐẦU dòng (sau gạch đầu dòng/chữ đậm) — «- **Kết cục chính:** …», «Kết cục
# phụ 2: …», «Primary outcome: …». «Kết cục được coi là kết cục chính: chỉ 1», «Bảng 2, Kết cục chính:» KHÔNG phải dòng
# khai.
_DONG_KHAI_KET_CUC_RE = re.compile(
    r"^\s*(?:[-*•]\s*)?(?:\*\*)?\s*(kết\s*cục\s*(chính|phụ)(?:\s*\d+)?|primary\s+outcome|secondary\s+outcomes?(?:\s*\d+)?)"
    r"\s*(?:\*\*)?\s*[:：]\s*(?:\*\*)?\s*(.+)$",
    re.IGNORECASE,
)
_CAU_KET_CUC_CHINH_RE = re.compile(r"kết\s*cục\s*chính|primary\s+outcome", re.IGNORECASE)
# ĐỊNH TÍNH (06/10/2026): bài theo COREQ/SRQR nêu điều đã định trước bằng «câu hỏi/hiện tượng/mục tiêu nghiên cứu», hiếm
# khi viết «kết cục chính» ⇒ chỉ nhận cụm định lượng thì bản thảo định tính đúng chuẩn vẫn rơi REVIEW giả.
_CAU_KET_CUC_CHINH_DINH_TINH_RE = re.compile(
    r"kết\s*cục\s*chính|primary\s+outcome|hiện\s*tượng\s*nghiên\s*cứu|câu\s*hỏi\s*nghiên\s*cứu|research\s+question|"
    r"phenomenon\s+of\s+interest|mục\s*(?:tiêu|đích)\s*nghiên\s*cứu|aims?\s+of\s+(?:the|this)\s+study",
    re.IGNORECASE,
)


def _la_dinh_tinh(design_code: Optional[str]) -> bool:
    return str(design_code or "").strip().lower().replace("-", "_") in {"qualitative", "dinh_tinh", "định tính"}


def ket_cuc_sap(sap_text: str) -> tuple[list[str], list[str]]:
    """(các kết cục CHÍNH, các kết cục PHỤ) mà SAP khai — phần sau nhãn, bỏ đuôi «— biến `x`», đã chuẩn hoá."""
    chinh: list[str] = []
    phu: list[str] = []
    for line in _nfc(sap_text).splitlines():
        m = _DONG_KHAI_KET_CUC_RE.match(line)
        if not m:
            continue
        gia_tri = re.split(r"\s+[—–-]\s+(?:biến|variable)\b", m.group(3), flags=re.IGNORECASE)[0]
        gia_tri = _chuan_kc(gia_tri)
        if len(gia_tri) < 4:
            continue
        la_chinh = (m.group(2) or "").casefold() == "chính" or "primary" in m.group(1).casefold()
        (chinh if la_chinh else phu).append(gia_tri)
    return chinh, phu


def primary_outcome_consistency(
    sap_text: str, manuscript: str, declared_outcome: str, design_code: Optional[str] = None
) -> tuple[str, str]:
    """So kết cục chính đã định trước với kết cục chính mà bản thảo BÁO.

    Trả (status, evidence). Đây là miền "báo cáo kết quả chọn lọc" của Cochrane RoB — lệch mà không giải trình là một
    trong những sai lệch nặng nhất. SỬA 05/10/2026 (soát từng cổng G8-09): bản cũ chỉ hỏi «chuỗi khai có mặt ở ĐÂU ĐÓ
    trong SAP và trong bản thảo» ⇒ khai một kết cục PHỤ của SAP (có trong SAP, có trong bản thảo) vẫn PASS dù bản thảo
    đã đổi kết cục chính. Nay: (1) kết cục khai ở G8 phải là kết cục CHÍNH của SAP (dòng «Kết cục chính:»), (2) câu nêu
    «kết cục chính» của bản thảo phải chứa nó; câu đó lại nêu một kết cục PHỤ của SAP ⇒ CHẶN (đổi kết cục chính);
    không xác nhận được ⇒ REVIEW, kèm yêu cầu giải trình."""
    if not _present(declared_outcome):
        return "REVIEW", "chưa khai kết cục chính định trước (gate_params.G8.primary_outcome)"
    if not sap_text:
        return "REVIEW", "không đọc được SAP (G4) để đối chiếu kết cục chính"
    if not manuscript:
        return "REVIEW", "không đọc được bản thảo (G7) để đối chiếu kết cục chính"
    khai = _chuan_kc(declared_outcome)
    chinh_sap, phu_sap = ket_cuc_sap(sap_text)
    if not chinh_sap:
        return "REVIEW", "không rút được dòng «Kết cục chính:» của SAP để đối chiếu — kiểm tay SAP §2"
    if not any(khai in c or c in khai for c in chinh_sap):
        return "BLOCK", (
            f"kết cục khai ở G8 {declared_outcome[:60]!r} KHÔNG phải kết cục CHÍNH của SAP "
            f"({chinh_sap[0][:60]!r}) — nghi báo cáo kết quả chọn lọc"
        )
    vung_gui = _manuscript_scan_regions(_nfc(manuscript))
    if khai not in _chuan_kc("\n".join(vung_gui)):
        return "BLOCK", (
            f"kết cục chính {declared_outcome[:60]!r} KHÔNG có mặt trong bản thảo (G7) — nghi báo cáo kết quả chọn lọc"
        )
    neo = _CAU_KET_CUC_CHINH_DINH_TINH_RE if _la_dinh_tinh(design_code) else _CAU_KET_CUC_CHINH_RE
    cau_ban_thao = [_chuan_kc(d) for vung in vung_gui for d in vung.splitlines() if neo.search(d)]
    if not cau_ban_thao:
        return "REVIEW", ("bản thảo không có câu nào nêu «kết cục chính»" + (
            " / câu hỏi–hiện tượng nghiên cứu" if _la_dinh_tinh(design_code) else "") + " để đối chiếu với SAP")
    if any(khai in c for c in cau_ban_thao):
        return "PASS", f"kết cục chính {declared_outcome[:60]!r} = SAP §2 và được bản thảo nêu đúng là kết cục chính"
    doi = [p for p in phu_sap if len(p) >= 8 and any(p in c for c in cau_ban_thao)]
    if doi:
        return "BLOCK", (
            f"bản thảo nêu kết cục PHỤ của SAP ({doi[0][:60]!r}) làm kết cục chính — đổi kết cục chính so với SAP "
            "(báo cáo kết quả chọn lọc)"
        )
    return "REVIEW", (
        f"câu «kết cục chính» trong bản thảo không chứa kết cục đã định trước {declared_outcome[:60]!r} — đối chiếu "
        "lại hoặc giải trình công khai việc đổi"
    )


def _manuscript_signals_ai_use(manuscript: str) -> bool:
    """Bản thảo có tự nhắc tới việc dùng AI hay không.

    Dùng để đối chiếu NGƯỢC với khai báo ``ai_use_declared`` (G8-F3) — tái dùng
    ``_AI_DISCLOSURE_TOKENS``/``_AI_TOOL_NAME_RE`` đã có, không viết lại regex.
    """
    if not manuscript:
        return False
    if any(token.casefold() in manuscript.casefold() for token in _AI_DISCLOSURE_TOKENS):
        return True
    return bool(_AI_TOOL_NAME_RE.search(manuscript))


def ai_disclosure_issues(manuscript: str, g8: Mapping[str, Any]) -> list[str]:
    """Kiểm khai báo AI theo ICMJE Mục V.A (bản 1/2026)."""
    issues: list[str] = []
    declared = g8.get("ai_use_declared")
    # SỬA 05/10/2026 (soát từng cổng G8-08): giá trị KHÁC kiểu bool («có», «true», «false», «không» gõ tay vào
    # study_meta.json) từng rơi qua cả ba nhánh None/True/False ⇒ issues rỗng ⇒ PASS «khai báo AI đầy đủ» — nặng nhất là
    # chuỗi «false» bỏ qua luôn phép đối chiếu ngược với bản thảo. Fail-closed như các cờ cover_letter_* (`is True`).
    if declared is not None and not isinstance(declared, bool):
        issues.append(f"ai_use_declared phải là true/false (JSON), nhận {declared!r} — chưa khai dứt khoát "
                      "có/không dùng AI")
        if _manuscript_signals_ai_use(manuscript):
            issues.append("bản thảo có nhắc tới việc dùng AI — chốt gate_params.G8.ai_use_declared bằng true/false")
        return issues
    if declared is None:
        issues.append("chưa khai dứt khoát có/không dùng AI (ICMJE: không khai có thể bị coi là misconduct)")
        # SỬA 2026-07-30 (G8-F3): trước đây return NGAY tại đây nên không bao
        # giờ đối chiếu với bản thảo thật — một bản thảo đã thừa nhận dùng AI
        # (vd CLEAN_MANUSCRIPT trong test: "công cụ trí tuệ nhân tạo để hiệu
        # đính ngôn ngữ") mà gate_params chưa chốt có/không vẫn chỉ bị coi là
        # thiếu sót hành chính chung chung. Thêm cảnh báo CỤ THỂ khi bản thảo
        # đã tự lộ việc dùng AI để bác sĩ biết cần chốt field này ngay.
        if _manuscript_signals_ai_use(manuscript):
            issues.append(
                "bản thảo có nhắc tới việc dùng AI dù CHƯA khai dứt khoát — cần chốt "
                "có/không trong gate_params.G8.ai_use_declared trước khi nộp"
            )
        return issues
    if declared is True:
        if not _present(g8.get("ai_tools")):
            issues.append("khai có dùng AI nhưng thiếu TÊN CÔNG CỤ + phiên bản")
        if not _present(g8.get("ai_purpose")):
            issues.append("khai có dùng AI nhưng thiếu MỤC ĐÍCH sử dụng")
        if g8.get("ai_declared_in_cover_letter") is not True:
            issues.append("thiếu khai AI trong COVER LETTER (ICMJE đòi khai ở CẢ hai nơi)")
        if manuscript and not any(
            token.casefold() in manuscript.casefold() for token in _AI_DISCLOSURE_TOKENS
        ):
            issues.append("thiếu khai AI trong chính BẢN THẢO")
    elif declared is False:
        # SỬA 2026-07-30 (G8-F3, MEDIUM FABRICATION_RISK): trước đây nhánh
        # declared=False KHÔNG kiểm gì cả — khai "KHÔNG dùng AI" trong khi bản
        # thảo THẬT SỰ nhắc tới AI (vd "công cụ trí tuệ nhân tạo để hiệu đính
        # ngôn ngữ") lọt qua hoàn toàn, dù đó là khai báo SAI SỰ THẬT theo
        # ICMJE Mục V.A (Updated January 2026). primary_outcome_consistency()
        # trong cùng file là mẫu thiết kế cho việc đối chiếu hai chiều này.
        if _manuscript_signals_ai_use(manuscript):
            issues.append(
                "khai KHÔNG dùng AI (ai_use_declared=False) NHƯNG bản thảo THẬT SỰ nhắc "
                "tới việc dùng AI — nghi khai báo SAI SỰ THẬT, vi phạm ICMJE Mục V.A"
            )
    # Cấm tuyệt đối: AI ở vị trí tác giả, hoặc AI bị trích dẫn làm nguồn gốc.
    if manuscript:
        author_block = manuscript[:3000]
        if _AI_TOOL_NAME_RE.search(author_block) and re.search(
            r"(tác giả|author)", author_block, re.IGNORECASE
        ):
            issues.append("nghi có tên công cụ AI trong khối TÁC GIẢ — ICMJE cấm liệt kê AI là tác giả")
        ref_idx = max(
            manuscript.rfind("TÀI LIỆU THAM KHẢO"),
            manuscript.rfind("REFERENCES"),
        )
        if ref_idx > 0 and _AI_TOOL_NAME_RE.search(manuscript[ref_idx:]):
            issues.append("nghi TRÍCH DẪN nội dung AI trong danh mục tài liệu tham khảo — ICMJE không chấp nhận")
    return issues


_KHONG_XAC_DINH_THIET_KE = (
    "không xác định được thiết kế nghiên cứu (G1/G2) — không kết luận được nghĩa vụ đăng ký/chia sẻ dữ liệu của ICMJE"
)


def _ngay_iso(value: Any) -> Optional[date]:
    """Ngày YYYY-MM-DD hợp lệ ⇒ date; còn lại (rỗng, «2026-3-1», «15/03/2026») ⇒ None. So chuỗi ngày thô từng cho
    «2026-03-15» < «2026-3-1» (G8-07)."""
    text = str(value or "").strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def registration_issues(design_code: str, g8: Mapping[str, Any], g2: Mapping[str, Any],
                        attestation: Optional[Mapping[str, Any]] = None) -> tuple[str, list[str]]:
    """Kiểm đăng ký nghiên cứu theo ICMJE §III.L.1.

    Trả (mức, danh sách vấn đề). CỐ Ý không gắn vào ``design_code == "rct"``: định
    nghĩa thử nghiệm của ICMJE rộng hơn (mọi phân bổ TIẾN CỨU vào một can thiệp,
    kể cả can thiệp giáo dục/cải tiến chất lượng). Ngược lại với thiết kế quan sát
    ICMJE nói rõ chỉ KHUYẾN KHÍCH — báo lỗi ở đó là báo sai chuẩn.

    SỬA 05/10/2026 (soát từng cổng G8-07/G8-10): (1) nguồn THẨM QUYỀN là attestation đã ký trong gói G2
    (registration.registration_id/registration_date, first_enrolment_date) — gate_params.G8 khai khác ⇒ REVIEW; (2) ngày
    phải ISO YYYY-MM-DD và so bằng date (so chuỗi thô từng cho đăng ký hồi cứu qua); (3) mã đăng ký phải KHỚP TRỌN
    mẫu registry («xem NCT0123456789» từng đạt); (4) thiết kế không xác định ⇒ REVIEW, không mặc định im lặng là quan
    sát."""
    interventional = design_code in _TRIAL_LIKE_DESIGNS or g8.get("interventional") is True
    if not design_code and not interventional:
        return "REVIEW", [_KHONG_XAC_DINH_THIET_KE]
    att = attestation if isinstance(attestation, Mapping) else {}
    att_reg = att.get("registration") if isinstance(att.get("registration"), Mapping) else {}
    registration_id = str(
        att_reg.get("registration_id") or g8.get("registration_id") or g2.get("g2_registration") or ""
    ).strip()
    problems: list[str] = []
    if not interventional:
        if design_code in _REGISTRATION_ENCOURAGED_DESIGNS and not registration_id:
            return "PASS", ["thiết kế quan sát — ICMJE KHUYẾN KHÍCH đăng ký, không bắt buộc"]
        return "PASS", []
    if not registration_id or not _REGISTRY_ID_RE.fullmatch(registration_id):
        problems.append(f"thiếu mã đăng ký hợp lệ (nhận được {registration_id or 'rỗng'!r})")
    for khoa_g8, gia_tri_att in (("registration_id", att_reg.get("registration_id")),
                                 ("registration_date", att_reg.get("registration_date")),
                                 ("first_enrolment_date", att.get("first_enrolment_date"))):
        khai = str(g8.get(khoa_g8) or "").strip()
        if gia_tri_att and khai and khai != str(gia_tri_att).strip():
            problems.append(f"gate_params.G8.{khoa_g8}={khai!r} LỆCH attestation G2 đã ký ({gia_tri_att!r})")
    reg_raw = att_reg.get("registration_date") or g8.get("registration_date")
    enrol_raw = att.get("first_enrolment_date") or g8.get("first_enrolment_date")
    reg_date, enrol_date = _ngay_iso(reg_raw), _ngay_iso(enrol_raw)
    if reg_date and enrol_date:
        if reg_date > enrol_date:
            problems.append(
                f"ĐĂNG KÝ HỒI CỨU: ngày đăng ký {reg_date.isoformat()} SAU ngày tuyển ca đầu {enrol_date.isoformat()}"
            )
    elif reg_raw or enrol_raw:
        problems.append(
            f"ngày đăng ký/tuyển ca đầu phải đúng ISO YYYY-MM-DD (nhận {reg_raw!r} / {enrol_raw!r})"
        )
    else:
        problems.append("thiếu ngày đăng ký và/hoặc ngày tuyển ca đầu tiên để đối chiếu")
    if g8.get("registration_date_is_irb_date") is True:
        problems.append(
            "dùng ngày phê duyệt Hội đồng Đạo đức thay cho ngày đăng ký — ICMJE nói rõ không thay thế được"
        )
    return ("REVIEW" if problems else "PASS"), problems


_PHU_DINH_RE = re.compile(r"(?<!\w)(?:không|not|no|none)(?!\w)", re.IGNORECASE)


def data_sharing_issues(design_code: str, g8: Mapping[str, Any]) -> tuple[str, list[str]]:
    """ICMJE §III.L.3 — chỉ BẮT BUỘC với báo cáo kết quả thử nghiệm lâm sàng.

    Thiết kế không xác định ⇒ REVIEW (G8-10). SỬA 05/10/2026 (soát từng cổng G8-13): tuyên bố KHÔNG chia sẻ dữ liệu cá
    nhân là câu trả lời HỢP LỆ — bài ICMJE 2017 (PLoS Med, PMID 28582414, doi:10.1371/journal.pmed.1002315) Bảng 1 Ví
    dụ 4: «No» và các mục còn lại «Not available/Not applicable». Bản cũ đòi từ khoá của đủ 5 trường cả khi câu trả lời
    là KHÔNG ⇒ giữ REVIEW vĩnh viễn (muốn gỡ chỉ có cách nhồi từ khoá). PI khai TƯỜNG MINH gate_params.G8.ipd_sharing
    =false (bool) — tránh suy từ văn bản («không chia sẻ dữ liệu ĐỊNH DANH» vẫn có thể là tuyên bố CÓ chia sẻ); văn
    bản phải có ý phủ định cho khớp; «undecided» vẫn bị từ chối."""
    interventional = design_code in _TRIAL_LIKE_DESIGNS or g8.get("interventional") is True
    if not design_code and not interventional:
        return "REVIEW", [_KHONG_XAC_DINH_THIET_KE]
    statement = str(g8.get("data_sharing_statement") or "")
    if not interventional:
        return "PASS", ["không phải báo cáo kết quả thử nghiệm — ICMJE không bắt buộc"]
    if not _present(statement):
        return "REVIEW", ["thiếu tuyên bố chia sẻ dữ liệu (bắt buộc cho thử nghiệm lâm sàng)"]
    problems: list[str] = []
    if re.search(r"(undecided|chưa quyết định|sẽ xem xét sau)", statement, re.IGNORECASE):
        problems.append("chứa 'undecided' — ICMJE nói rõ đây KHÔNG phải câu trả lời chấp nhận được")
    ipd = g8.get("ipd_sharing")
    if ipd is False and not problems:
        if not _PHU_DINH_RE.search(statement):
            return "REVIEW", [
                "gate_params.G8.ipd_sharing=false nhưng tuyên bố không nói KHÔNG chia sẻ — hai nơi phải khớp"]
        return "PASS", [
            "tuyên bố KHÔNG chia sẻ dữ liệu cá nhân — các mục còn lại «không áp dụng» (ICMJE 2017, Ví dụ 4)"]
    lowered = statement.casefold()
    for label, tokens in _DATA_SHARING_FIELDS:
        if not any(token.casefold() in lowered for token in tokens):
            problems.append(f"thiếu trường: {label}")
    return ("REVIEW" if problems else "PASS"), problems


def _recommendation_segments(report_text: str) -> list[str]:
    """Các đoạn thuộc mục KHUYẾN NGHỊ: phần sau từ khoá trên chính dòng đó + các dòng kế tiếp tới tiêu đề/đường
    kẻ/khung «═══» kế tiếp (tối đa 15 dòng)."""
    lines = _nfc(report_text).splitlines()
    segments: list[str] = []
    for idx, line in enumerate(lines):
        match = _RECOMMENDATION_KEY_RE.search(line)
        if not match:
            continue
        segments.append(line[match.end():])
        for nxt in lines[idx + 1: idx + 16]:
            if (nxt.lstrip().startswith("#") or "═══" in nxt or _HR_LINE_RE.match(nxt)
                    or _RECOMMENDATION_KEY_RE.search(nxt)):
                break
            segments.append(nxt)
    return segments


def _recommendation_choice_problem(report_text: str) -> Optional[str]:
    """Khuyến nghị đã được CHỌN chưa — None nếu đã chọn hoặc không phán được (để chốt cấu trúc cũ lo).

    Chỉ báo khi THẤY bằng chứng chưa chọn: dòng còn liệt kê ≥2 mức với ô ☐ mà không tích mức nào, hoặc tích
    nhiều hơn một mức. Một mức đứng riêng («SỬA NHỎ», «Khuyến nghị: Major revision (sửa lớn)») là đã chọn."""
    ticked: set[str] = set()
    option_list = False
    for segment in _recommendation_segments(report_text):
        upper = _ACCEPT_WITH_RE.sub("", segment.upper())
        seg_ticked = {k for k, r in _LEVEL_TICKED_RE.items() if r.search(upper)}
        seg_boxed = {k for k, r in _LEVEL_BOXED_RE.items() if r.search(upper)}
        ticked |= seg_ticked
        if len(seg_boxed) >= 2 and not seg_ticked:
            option_list = True
    if len(ticked) == 1:
        return None
    if len(ticked) > 1:
        return f"KHUYẾN NGHỊ tích nhiều hơn một mức ({', '.join(sorted(ticked))}) — chỉ được chọn MỘT"
    if option_list:
        return (
            "KHUYẾN NGHỊ chưa được CHỌN — dòng mẫu còn liệt kê các mức ☐ chưa tích (tích ☑ đúng một mức hoặc "
            "xoá các mức không chọn)"
        )
    return None


def _empty_template_tables(text: str) -> list[str]:
    """Bảng mà MỌI hàng dữ liệu chỉ còn số thứ tự (vd «| 1 | | | | |» của mẫu binh-duyet.md)."""
    found: list[str] = []
    block: list[str] = []
    for line in text.splitlines() + [""]:
        if line.lstrip().startswith("|"):
            block.append(line)
            continue
        if block:
            rows = [r for r in block[1:] if not _TABLE_SEPARATOR_RE.match(r)]
            if rows and all(_table_row_is_empty(r) for r in rows):
                found.append(f"bảng chỉ có hàng trống: «{block[0].strip()[:80]}»")
            block = []
    return found


def _table_row_is_empty(row: str) -> bool:
    cells = [c.strip() for c in row.strip().strip("|").split("|")]
    if cells and re.fullmatch(r"#?\d*\.?", cells[0]):
        cells = cells[1:]
    return all(not c for c in cells)


def review_template_residues(report_text: str) -> list[str]:
    """Ô mẫu còn sót trong bản nhận xét phản biện (khuôn binh-duyet.md) — bằng chứng «…trích…».

    Bỏ qua phần TRÍCH NGUYÊN VĂN (`…`, «…», “…”, "…") vì người phản biện có thể dẫn đúng ô trống của bản thảo.
    «___» trên dòng có ô tích (☐/☑) là ô điều kiện hợp lệ («☐ Có (ghi rõ): ___» khi chọn «Không có»)."""
    clean = _QUOTED_SPAN_RE.sub("", _nfc(report_text))
    found: list[str] = []
    seen: set[str] = set()

    def _add(line: str, needle: str) -> None:
        compact = re.sub(r"\s+", " ", line.strip())
        if compact not in seen:
            seen.add(compact)
            found.append("«" + _excerpt(compact, needle) + "»")

    for hit in PC.tim(clean, _MANUSCRIPT_FAMILIES, them=_REVIEW_TEMPLATE_LITERALS):
        _add(hit.dong, hit.khop)
    for line in clean.splitlines():
        if (not line.strip() or _CHECKBOX_CHAR_RE.search(line) or _HR_LINE_RE.match(line)
                or line.lstrip().startswith("|")):
            continue
        for hit in PC.tim(line, (PC.TRONG,)):
            _add(line, hit.khop)
    found.extend(_empty_template_tables(clean))
    return found


# ── Đọc NỘI DUNG bản nhận xét phản biện (VÁ 05/10/2026, soát từng cổng G8-01/G8-02/G8-12) ─────────────────────────
# Bản cũ chỉ hỏi «có đủ mục (chuỗi con ở BẤT KỲ đâu) / đã chọn một mức / còn ô mẫu không» — không đọc mức ĐÃ CHỌN, kết
# luận, bảng lỗi nghiêm trọng hay khối khai báo của người phản biện ⇒ «☑ Từ chối» + «Cần sửa thêm» + «☑ Có xung đột lợi
# ích» vẫn ký được G8; «MAJOR … OVERALL ACCEPT» một dòng cũng qua (G8-12; «majority», «overall survival» khớp nhầm).

# Nhãn mọi mục của khuôn binh-duyet.md (dùng để biết một mục KẾT THÚC ở đâu).
_NHAN_MUC_BAO_CAO = tuple(alt for _l, alts in _REVIEW_REPORT_SECTIONS for alt in alts) + (
    "KHAI BÁO CỦA NGƯỜI PHẢN BIỆN", "REVIEWER DECLARATION", "ĐỐI CHIẾU CHECKLIST", "CỔNG TRÍCH DẪN",
    "ĐA LĂNG KÍNH", "TÓM TẮT NHẬN XÉT")


def _la_tieu_de(line: str, nhan: str) -> bool:
    """Dòng là TIÊU ĐỀ của mục `nhan` (không phân biệt hoa/thường): tiêu đề Markdown «#…»/khung «═══» chứa nhãn, hoặc
    dòng MỞ ĐẦU bằng nhãn rồi tới «:»/«(»/gạch/hết dòng. Văn xuôi «overall survival», «Major revisions are…» không
    khớp."""
    text = _nfc(line).strip()
    if not text:
        return False
    upper, n = text.upper(), nhan.upper()
    if (text.startswith("#") or "═══" in text) and n in upper:
        return True
    bo = re.sub(r"^[\s*_>#\-•]+", "", upper)
    return bool(re.match(re.escape(n) + r"\s*(?:[:：(—–\-]|\*\*|$)", bo))


def _doan_muc(report_text: str, nhan_cac: Sequence[str]) -> Optional[str]:
    """Nội dung mục có tiêu đề là một trong `nhan_cac`: phần sau nhãn trên chính dòng tiêu đề + các dòng tới tiêu đề kế
    tiếp (Markdown «#», khung ═══, hoặc nhãn mục khác của khuôn đứng đầu dòng). None nếu không có tiêu đề nào."""
    lines = _nfc(report_text).splitlines()
    rieng = {n.upper() for n in nhan_cac}
    for i, line in enumerate(lines):
        nhan = next((n for n in nhan_cac if _la_tieu_de(line, n)), None)
        if nhan is None:
            continue
        idx = line.upper().find(nhan.upper())
        phan = [line[idx + len(nhan):] if idx >= 0 else ""]
        for nxt in lines[i + 1:]:
            if ("═══" in nxt or nxt.lstrip().startswith("#")
                    or any(_la_tieu_de(nxt, n) for n in _NHAN_MUC_BAO_CAO if n.upper() not in rieng)):
                break
            phan.append(nxt)
        return "\n".join(phan)
    return None


_MUC_CHO_PHEP_NOP = ("chấp nhận", "sửa nhỏ")
_LEVEL_ANY_RE = {k: re.compile(r"(?<!\w)" + v + r"(?!\w)") for k, v in _REVIEW_LEVEL_ALTS.items()}


def muc_khuyen_nghi(report_text: str) -> Optional[str]:
    """Mức khuyến nghị ĐÃ CHỌN («chấp nhận» · «sửa nhỏ» · «sửa lớn» · «từ chối»); None nếu chưa chọn/mơ hồ.

    Ưu tiên ô đã tích (☑/☒/✓/[X]); không có ô tích thì nhận mức DUY NHẤT được nêu trong mục khuyến nghị («SỬA NHỎ»,
    «Khuyến nghị: Major revision»). «Accept with minor revisions» là MỘT mức (sửa nhỏ)."""
    ticked: set[str] = set()
    neu: set[str] = set()
    for segment in _recommendation_segments(report_text):
        upper = _ACCEPT_WITH_RE.sub("", segment.upper())
        ticked |= {k for k, r in _LEVEL_TICKED_RE.items() if r.search(upper)}
        boxed = {k for k, r in _LEVEL_BOXED_RE.items() if r.search(upper)}
        neu |= {k for k, r in _LEVEL_ANY_RE.items() if r.search(upper)} - boxed
    if ticked:
        return next(iter(ticked)) if len(ticked) == 1 else None
    return next(iter(neu)) if len(neu) == 1 else None


_KET_LUAN_CAN_SUA_RE = re.compile(
    r"cần sửa thêm|chưa sẵn sàng|không đủ điều kiện nộp|chưa đủ điều kiện|not ready|requires? (?:major |minor )?"
    r"revisions?|needs? (?:further |major |minor )?revisions?", re.IGNORECASE)
_KET_LUAN_SAN_SANG_RE = re.compile(r"sẵn sàng nộp|đủ điều kiện nộp|ready for submission|ready to submit", re.IGNORECASE)


def ket_luan_tong_the(report_text: str) -> Optional[str]:
    """«san_sang» · «can_sua» · None (chưa chọn / không có mục kết luận). Còn nguyên hai lựa chọn của mẫu ⇒ None; «cần
    sửa thêm» thắng khi cả hai cùng xuất hiện (nguyên tắc mặc định nghi ngờ của binh-duyet.md)."""
    doan = _doan_muc(report_text, ("KẾT LUẬN TỔNG THỂ", "OVERALL"))
    if doan is None or _UNCHOSEN_CONCLUSION_RE.search(doan):
        return None
    if _KET_LUAN_CAN_SUA_RE.search(doan):
        return "can_sua"
    if _KET_LUAN_SAN_SANG_RE.search(doan):
        return "san_sang"
    return None


_KHONG_CO_RE = re.compile(r"(?<!\w)(?:không có|không phát hiện|none|nil|n/a)(?!\w)", re.IGNORECASE)


def loi_nghiem_trong(report_text: str) -> tuple[Optional[int], list[str]]:
    """(số lỗi nghiêm trọng còn ghi, các lỗi THIẾU vị trí) trong mục LỖI NGHIÊM TRỌNG — (None, []) khi không có mục.

    Bảng: mỗi hàng có nội dung (ngoài số thứ tự) là một lỗi, và cột «Vị trí/Location» của hàng đó phải có nội dung.
    Gạch đầu dòng/đánh số có chữ (không phải «không có») cũng là một lỗi. Mục chỉ ghi «không có»/«none» ⇒ 0."""
    doan = _doan_muc(report_text, ("LỖI NGHIÊM TRỌNG", "MAJOR ISSUES", "MAJOR COMMENTS", "MAJOR"))
    if doan is None:
        return None, []
    so, thieu_vi_tri = 0, []
    tieu_de_bang: Optional[list[str]] = None
    for line in doan.splitlines():
        s = line.strip()
        if s.startswith("|"):
            if _TABLE_SEPARATOR_RE.match(s):
                continue
            cells = [c.strip() for c in s.strip("|").split("|")]
            if tieu_de_bang is None:
                tieu_de_bang = [c.casefold() for c in cells]
                continue
            if all(not c or re.fullmatch(r"#?\d*\.?", c) or _KHONG_CO_RE.fullmatch(c) for c in cells):
                continue
            so += 1
            vi_tri = next((i for i, h in enumerate(tieu_de_bang) if "vị trí" in h or "location" in h), None)
            if vi_tri is not None and (vi_tri >= len(cells) or not cells[vi_tri]):
                thieu_vi_tri.append(" | ".join(c for c in cells if c)[:80])
            continue
        if not s:
            tieu_de_bang = None
            continue
        m = re.match(r"^(?:[-*•]|\d+[.)])\s+(.+)$", s)
        if m and not _KHONG_CO_RE.search(m.group(1)) and PC.co_noi_dung_that(m.group(1)):
            so += 1
    return so, thieu_vi_tri


# Khối KHAI BÁO CỦA NGƯỜI PHẢN BIỆN (binh-duyet.md — «người phản biện tự điền»): (khoá, mẫu dòng câu hỏi, đáp án
# «không», đáp án «có»).
_CAU_KHAI_BAO: Sequence[tuple[str, Any, tuple[str, ...], tuple[str, ...]]] = (
    ("xung đột lợi ích", re.compile(r"xung đột lợi ích|conflict of interest", re.IGNORECASE),
     ("không có", "none", "no"), ("có", "yes")),
    ("đồng tác giả/cấp trên/cấp dưới", re.compile(r"đồng tác giả|co-?author", re.IGNORECASE),
     ("không", "no"), ("có", "yes")),
    ("dùng AI khi phản biện",
     re.compile(r"dùng AI|AI khi phản biện|use[ds]? (?:any )?(?:generative )?AI", re.IGNORECASE),
     ("không", "no"), ("có", "yes")),
)
_O_TICH_RE = re.compile(r"(?:☑|☒|✓|✔|■|\[[xX]\])\s*\**\s*([^☐☑☒✓✔■\[\]:]+)")
_BO_O_TICH_RE = re.compile(r"[☐☑☒✓✔■]|\[[ xX]\]")


def _cau_hoi(dong: str) -> str:
    """Phần CÂU HỎI của một dòng khai báo — trước ô tích đầu tiên. Chi tiết tự do sau ô «Có» (vd «là đồng tác giả bài
    trước» ghi ở dòng XUNG ĐỘT LỢI ÍCH) từng làm câu khai đồng tác giả đọc nhầm dòng đó (đột biến 05/10/2026)."""
    m = _CHECKBOX_CHAR_RE.search(dong)
    return dong[: m.start()] if m else dong


def _dap_an(line: str, nhan_khong: Sequence[str], nhan_co: Sequence[str]) -> Optional[str]:
    """«khong» · «co» · None (chưa tích / tích cả hai) cho MỘT dòng câu hỏi có ô tích."""
    da_tich: set[str] = set()
    for m in _O_TICH_RE.finditer(_nfc(line)):
        nhan = m.group(1).strip().casefold()
        if any(nhan.startswith(k) for k in nhan_khong):
            da_tich.add("khong")
        elif any(nhan.startswith(k) for k in nhan_co):
            da_tich.add("co")
    return next(iter(da_tich)) if len(da_tich) == 1 else None


def khai_bao_nguoi_phan_bien(report_text: str) -> tuple[list[str], list[str]]:
    """(lý do CHẶN, lý do REVIEW) từ khối KHAI BÁO CỦA NGƯỜI PHẢN BIỆN trong bản nhận xét (G8-02).

    CHẶN: tự khai CÓ xung đột lợi ích hoặc LÀ đồng tác giả/cấp trên/cấp dưới trực tiếp — ICMJE §II.B.1.b: người phản
    biện có xung đột phải TỪ CHỐI phản biện. REVIEW: thiếu khối; câu chưa tích đúng một ô; khai CÓ dùng AI mà không nêu
    công cụ + mục đích; chưa tích «Xác nhận» cam kết bảo mật (ICMJE §V.B). Bản cũ chỉ đọc 4 cờ boolean trong
    study_meta (ai sửa study_meta cũng đặt được, không nằm trong phạm vi ký)."""
    doan = _doan_muc(report_text, ("KHAI BÁO CỦA NGƯỜI PHẢN BIỆN", "REVIEWER DECLARATION"))
    if doan is None:
        return [], ["thiếu khối «KHAI BÁO CỦA NGƯỜI PHẢN BIỆN» trong bản nhận xét (mẫu binh-duyet.md)"]
    chan: list[str] = []
    xem: list[str] = []
    lines = doan.splitlines()
    for ten, mau, khong, co in _CAU_KHAI_BAO:
        dong = next((d for d in lines if _CHECKBOX_CHAR_RE.search(d) and mau.search(_cau_hoi(d))), None)
        if dong is None:
            xem.append(f"không thấy câu khai «{ten}» (kèm ô tích) trong khối khai báo")
            continue
        dap = _dap_an(dong, khong, co)
        if dap is None:
            xem.append(f"câu khai «{ten}» chưa tích đúng MỘT ô")
        elif dap == "co" and ten == "xung đột lợi ích":
            chan.append("người phản biện tự khai CÓ xung đột lợi ích — ICMJE §II.B.1.b: phải TỪ CHỐI phản biện")
        elif dap == "co" and ten.startswith("đồng tác giả"):
            chan.append("người phản biện tự khai LÀ đồng tác giả/cấp trên/cấp dưới trực tiếp — không độc lập")
        elif dap == "co":
            chi_tiet = _BO_O_TICH_RE.sub("", dong.rsplit(":", 1)[-1] if ":" in dong else "").strip()
            if not PC.co_noi_dung_that(chi_tiet):
                xem.append("khai CÓ dùng AI khi phản biện nhưng thiếu tên công cụ + mục đích (ICMJE §V.B)")
    xac_nhan = [d for d in lines if re.search(r"xác nhận|i confirm", d, re.IGNORECASE) and _CHECKBOX_CHAR_RE.search(d)]
    if not any(_O_TICH_RE.search(_nfc(d)) for d in xac_nhan):
        xem.append("chưa tích «Xác nhận» cam kết không tải bản thảo lên công cụ AI thiếu bảo mật (ICMJE §V.B)")
    return chan, xem


def _ly_do_khuyen_nghi(report_text: str) -> str:
    """Phần LÝ DO trong mục khuyến nghị — đã bỏ ô tích, tên các mức và nhãn «Lý do:»."""
    doan = _doan_muc(report_text, ("KHUYẾN NGHỊ", "RECOMMENDATION")) or ""
    doan = _BO_O_TICH_RE.sub(" ", _ACCEPT_WITH_RE.sub(" ", doan.upper()))
    for r in _LEVEL_ANY_RE.values():
        doan = r.sub(" ", doan)
    doan = re.sub(r"(?<!\w)(?:LÝ DO|REASON|RATIONALE)\s*[:：]", " ", doan)
    return re.sub(r"[\s*_:;,.\-—–]+", " ", doan).strip()


def review_report_issues(report_text: str) -> list[str]:
    """Bản nhận xét phản biện có đủ cấu trúc mẫu của doctrine binh-duyet.md không.

    Từ 03/10/2026: khuyến nghị phải được CHỌN, kết luận không còn hai lựa chọn, không còn ô mẫu (xem
    ``review_template_residues``). SỬA 05/10/2026 (soát từng cổng G8-12): mục nhận theo DÒNG TIÊU ĐỀ (không còn chuỗi
    con ở bất kỳ đâu); khuyến nghị phải có LÝ DO; kết luận phải được CHỌN; mỗi lỗi nghiêm trọng trong bảng phải kèm vị
    trí. Kết luận CHO PHÉP NỘP hay không là việc của G8-HUMAN-06, khai báo người phản biện là việc của G8-HUMAN-05."""
    if not report_text.strip():
        return ["chưa có bản nhận xét phản biện"]
    problems: list[str] = []
    for label, alternatives in _REVIEW_REPORT_SECTIONS:
        if _doan_muc(report_text, alternatives) is None:
            problems.append(f"thiếu mục '{label}' (tiêu đề mục)")
    choice_problem = _recommendation_choice_problem(report_text)
    if choice_problem:
        problems.append(choice_problem)
    elif muc_khuyen_nghi(report_text) is None:
        problems.append("thiếu KHUYẾN NGHỊ rõ mức (chấp nhận / sửa nhỏ / sửa lớn / từ chối)")
    if len(re.findall(r"\w", _ly_do_khuyen_nghi(report_text))) < 15:
        problems.append("KHUYẾN NGHỊ thiếu LÝ DO (dòng «Lý do: …» có nội dung)")
    if _UNCHOSEN_CONCLUSION_RE.search(_nfc(report_text)):
        problems.append("KẾT LUẬN TỔNG THỂ còn để cả hai lựa chọn «sẵn sàng nộp / cần sửa thêm» — chọn một")
    elif ket_luan_tong_the(report_text) is None:
        problems.append("KẾT LUẬN TỔNG THỂ chưa chọn «sẵn sàng nộp» hay «cần sửa thêm»")
    _so_loi, thieu_vi_tri = loi_nghiem_trong(report_text)
    if thieu_vi_tri:
        problems.append(f"lỗi nghiêm trọng thiếu VỊ TRÍ (trang/mục/dòng): {'; '.join(thieu_vi_tri[:3])}")
    residues = review_template_residues(report_text)
    if residues:
        problems.append(
            f"bản nhận xét còn ô mẫu chưa điền ({len(residues)} chỗ): " + "; ".join(residues[:4])
        )
    return problems


# ════════════════════════════════════════════════════════════════════════════
# Lõi đánh giá
# ════════════════════════════════════════════════════════════════════════════


def evaluate_g8_quality(
    *,
    study: str,
    checkpoint: Mapping[str, Any],
    presubmission_text: str,
    manuscript_text: str,
    sap_text: str,
    review_report_text: str,
    g2_checkpoint: Mapping[str, Any],
    meta: Mapping[str, Any],
    citation_ok: bool,
    citation_detail: str,
    ledger_signed: bool,
    ledger_reason: str,
    signature_scope: Optional[str],
    role_key_available: bool,
    cross_gate_refs: Mapping[str, str],
    design_drift_warning: Optional[str] = None,
    design_code: Optional[str] = None,
    tien_de_g7: Optional[Mapping[str, str]] = None,
    attestation_g2: Optional[Mapping[str, Any]] = None,
) -> dict[str, Any]:
    """Chấm G8 hai tầng: máy kiểm NỘI DUNG, rồi bằng chứng bình duyệt người thật.

    05/10/2026 (soát từng cổng G8): `design_code` — thiết kế SỐNG do evaluate_study tính qua resolve_design_code (G2 >
    G1), vắng thì rơi về checkpoint/G2 như cũ, rỗng ⇒ G8-AUTO-07/08 REVIEW (G8-10); `tien_de_g7` — G7 chấm sống
    ({status, evidence}), vắng ⇒ «không đo được», không bao giờ đạt (G8-06); `attestation_g2` — attestation đã ký trong
    gói G2 khi G2 đã duyệt, nguồn THẨM QUYỀN cho mã/ngày đăng ký (G8-07)."""
    g8 = _g8_meta(meta)
    # LƯU Ý (G8-F5, MEDIUM DOWNSTREAM_CONTRACT_RISK): design_code ở đây KHÔNG
    # đến từ G8_checkpoint.json (write_g8_checkpoint() trong run_g8_auto.py
    # không bao giờ ghi khóa "design_code") — luôn rơi về g2_checkpoint, khác
    # với cách run_g8_auto.py::main() tự lấy design_code (đọc thẳng
    # gates['G1']['design']['internal_code']), và cũng khác
    # gate_contract.resolve_design_code() (ưu tiên G2 > G1, đã nối vào G5/G7).
    # Đổi nguồn chính ở đây rủi ro lan sang mọi call site (evaluate_study(),
    # approve_gate.py, test) nên KHÔNG đổi biến này — thay vào đó
    # ``design_drift_warning`` (tham số mới, do evaluate_study() tính qua
    # resolve_design_code()) nuôi một tiêu chí CẢNH BÁO riêng (G8-AUTO-11)
    # bên dưới khi G1/G2 lệch nhau, để bác sĩ biết registration_issues()/
    # data_sharing_issues() có thể đang dùng design_code sai.
    if design_code is None:
        design_code = str(checkpoint.get("design_code") or g2_checkpoint.get("design_code") or "")
    design_code = str(design_code or "")
    automatic: list[dict[str, str]] = []
    approval: list[dict[str, str]] = []

    # ── G8-AUTO-00 — guardrail nền ─────────────────────────────────────────
    # SỬA 2026-07-30 (audit toàn diện G0-G10, phát hiện khi vá G8-F1 — cùng
    # lớp "tin cache cũ" đã đóng ở G7-F1): trước đây đọc thẳng
    # checkpoint["guardrail"]["passed"] — giá trị ĐÓNG BĂNG tại thời điểm
    # run_g8_auto.py sinh artifact lần đầu — dù presubmission_text ở trên đã
    # đọc FRESH từ đĩa. Một bác sĩ sửa file .md sau đó (chèn PII, xóa
    # disclaimer, hoặc NGƯỢC LẠI đã sửa xong lỗi cũ) sẽ KHÔNG bao giờ được
    # phản ánh vào G8-AUTO-00 vì nó chưa từng đọc lại. Chạy lại guardrail_g8()
    # TRÊN presubmission_text THẬT; dựng "pipeline" tối thiểu mà guardrail_g8()
    # cần (R1: có checkpoint cổng trước hay không) từ chính
    # checkpoint["pipeline_completeness"]/["pipeline_pass_count"] đã ghi.
    try:
        import run_g8_auto as G8run  # noqa: PLC0415
        _pipeline_rows = [
            {"checkpoint_exists": bool(v.get("checkpoint_exists"))}
            for v in (checkpoint.get("pipeline_completeness") or {}).values()
            if isinstance(v, Mapping)
        ]
        _pipeline_for_guardrail = {
            "rows": _pipeline_rows,
            "n_pass": checkpoint.get("pipeline_pass_count", 0),
        }
        fresh_guardrail = G8run.guardrail_g8(presubmission_text, _pipeline_for_guardrail)
        guardrail_passed = bool(fresh_guardrail.get("passed"))
    except ImportError:  # pragma: no cover - lưới an toàn nếu import thất bại
        guardrail = checkpoint.get("guardrail")
        guardrail_passed = (
            guardrail.get("passed") is True if isinstance(guardrail, Mapping) else False
        )
    automatic.append(_criterion(
        "G8-AUTO-00",
        "Guardrail liêm chính G8 sạch",
        "PASS" if guardrail_passed else "BLOCK",
        f"guardrail.passed={guardrail_passed}",
        "Sửa lỗi guardrail của run_g8_auto.py trước khi chấm chất lượng.",
    ))

    # ── G8-AUTO-01 — có gói tiền nộp bài ───────────────────────────────────
    automatic.append(_criterion(
        "G8-AUTO-01",
        "Có gói tiền nộp bài A9 để bình duyệt",
        "PASS" if presubmission_text.strip() else "BLOCK",
        f"{len(presubmission_text)} ký tự",
        "Chạy run_g8_auto.py để sinh gói A9 trước.",
    ))

    # ── G8-AUTO-02 — có bản thảo thật ──────────────────────────────────────
    automatic.append(_criterion(
        "G8-AUTO-02",
        "Có bản thảo G7 để đối chiếu nội dung",
        "PASS" if manuscript_text.strip() else "REVIEW",
        f"{len(manuscript_text)} ký tự",
        "Chạy G7 sinh bản thảo; không có bản thảo thì mọi kiểm nội dung đều rỗng.",
    ))

    # ── G8-AUTO-03 — A12 kiểm chứng trích dẫn PHẢI đạt ─────────────────────
    # Hiện A12 chỉ nuôi 2/30 điểm tự chấm và KHÔNG nằm trong 5 điều kiện quyết
    # định g8_status, nên G8 có thể in "PASS — ĐỦ ĐIỀU KIỆN NỘP BÀI" khi A12 chưa
    # từng chạy. Ở hợp đồng này, trích dẫn chưa xác minh là lỗi CHẶN.
    automatic.append(_criterion(
        "G8-AUTO-03",
        "Cổng A12 (kiểm chứng trích dẫn) đã đạt thật",
        "PASS" if citation_ok else "BLOCK",
        citation_detail or f"citation_ok={citation_ok}",
        "Chạy agent kiem-chung-trich-dan và tools/check_citation_retraction.py cho tới khi sạch.",
    ))

    # ── G8-AUTO-04 — vệt công cụ nội bộ + ô còn trống trong bản thảo ───────
    # THÊM 03/10/2026: ô trống/ô mẫu chưa điền (bộ dò chung placeholder_contract + ô mẫu riêng khuôn G7) cũng
    # CHẶN — trước đó bản thảo thật đã điền hết nhãn [CẦN…] nhưng còn «N = ___», «[Ước lượng hiệu quả]» vẫn PASS.
    traces = scan_internal_traces(manuscript_text) if manuscript_text else []
    residues = manuscript_residues(manuscript_text) if manuscript_text else []
    trace_evidence = list(traces)
    if residues:
        more = f" (+{len(residues) - 6} dòng khác)" if len(residues) > 6 else ""
        trace_evidence.append(
            f"ô trống/ô mẫu chưa điền ({len(residues)} dòng): " + "; ".join(residues[:6]) + more
        )
    # 05/10/2026 (lộ khi đo C1a trên bản sao): chưa có bản thảo thì KHÔNG ĐO ĐƯỢC — bản cũ in PASS «không thấy nhãn
    # [CẦN]…» trên văn bản rỗng (xanh giả ở cấp tiêu chí; trạng thái chung vẫn nhờ G8-AUTO-02 REVIEW).
    automatic.append(_criterion(
        "G8-AUTO-04",
        "Bản thảo không còn vệt công cụ nội bộ hay ô mẫu chưa điền",
        "BLOCK" if trace_evidence else "PASS" if manuscript_text.strip() else "REVIEW",
        "; ".join(trace_evidence) if trace_evidence else (
            "không thấy nhãn [CẦN], ô trống/ô mẫu khuôn G7, tên file pipeline hay hướng dẫn biên tập sót lại"
            if manuscript_text.strip() else "chưa có bản thảo để quét (không đo được ≠ sạch — xem G8-AUTO-02)"
        ),
        "Xóa mọi vệt nội bộ và điền mọi ô mẫu trong thân bài — doctrine xếp đây là lỗi CHẶN, không phải góp ý nhỏ.",
    ))

    # ── G8-AUTO-05 — báo cáo kết quả chọn lọc ──────────────────────────────
    outcome_status, outcome_evidence = primary_outcome_consistency(
        sap_text, manuscript_text, str(g8.get("primary_outcome") or ""), design_code
    )
    automatic.append(_criterion(
        "G8-AUTO-05",
        "Kết cục chính trong bản thảo khớp kết cục đã định trước ở SAP",
        outcome_status,
        outcome_evidence,
        "Ghi gate_params.G8.primary_outcome; nếu đổi kết cục chính thì phải giải trình công khai trong bài.",
    ))

    # ── G8-AUTO-06 — khai báo AI theo ICMJE 1/2026 ─────────────────────────
    ai_issues = ai_disclosure_issues(manuscript_text, g8)
    automatic.append(_criterion(
        "G8-AUTO-06",
        "Khai báo dùng AI đủ theo ICMJE Mục V (bản 1/2026)",
        "REVIEW" if ai_issues else "PASS",
        "; ".join(ai_issues) if ai_issues else "khai báo AI đầy đủ ở cover letter và bản thảo",
        "Khai gate_params.G8: ai_use_declared, ai_tools, ai_purpose, ai_declared_in_cover_letter.",
    ))

    # ── G8-AUTO-07 — đăng ký nghiên cứu ────────────────────────────────────
    reg_status, reg_problems = registration_issues(design_code, g8, g2_checkpoint, attestation_g2)
    automatic.append(_criterion(
        "G8-AUTO-07",
        "Đăng ký nghiên cứu đúng ICMJE (tiền cứu, không dùng ngày IRB thay thế)",
        reg_status,
        "; ".join(reg_problems) if reg_problems else "đăng ký hợp lệ hoặc không thuộc diện bắt buộc",
        "Khai registration_id/registration_date/first_enrolment_date trong gate_params.G8.",
    ))

    # ── G8-AUTO-08 — chia sẻ dữ liệu ───────────────────────────────────────
    ds_status, ds_problems = data_sharing_issues(design_code, g8)
    automatic.append(_criterion(
        "G8-AUTO-08",
        "Tuyên bố chia sẻ dữ liệu đủ 5 trường (thử nghiệm lâm sàng)",
        ds_status,
        "; ".join(ds_problems) if ds_problems else "đủ 5 trường theo ICMJE §III.L.3",
        "Viết data_sharing_statement đủ 5 trường; 'undecided' không được chấp nhận. KHÔNG chia sẻ dữ liệu cá nhân là "
        "câu trả lời hợp lệ: khai gate_params.G8.ipd_sharing=false (bool) và nói rõ trong tuyên bố.",
    ))

    # ── G8-AUTO-09 — cover letter ──────────────────────────────────────────
    cover_missing = [
        label for label, key in (
            ("khai nộp trùng lặp", "cover_letter_no_duplicate_submission"),
            ("khai xung đột lợi ích", "cover_letter_coi_declared"),
            ("xác nhận mọi tác giả đã duyệt", "cover_letter_all_authors_approved"),
            ("thông tin liên hệ tác giả", "cover_letter_corresponding_contact"),
            ("trạng thái preprint", "cover_letter_preprint_status"),
        )
        if g8.get(key) is not True
    ]
    automatic.append(_criterion(
        "G8-AUTO-09",
        "Cover letter có đủ nội dung bắt buộc (ICMJE §IV.B)",
        "REVIEW" if cover_missing else "PASS",
        "thiếu: " + "; ".join(cover_missing) if cover_missing else "đủ 5 nhóm nội dung",
        "Soạn cover letter theo ICMJE §IV.B rồi đánh dấu từng mục trong gate_params.G8.",
    ))

    # ── G8-AUTO-10 — checklist chuẩn báo cáo có tham gia quyết định không ──
    # LỊCH SỬ (đã lỗi thời, giữ để hiểu bối cảnh): comment ở đây từng nói
    # g8_status của run_g8_auto.py "chỉ tính 5 điều kiện — reporting_ok bị bỏ
    # ngoài" (một đề tài checklist 30% vẫn PASS). SỬA 2026-07-31 (rà lại các
    # mục "chưa sửa" cũ trong CLAUDE.md): bug đó đã được vá TRƯỚC ĐÓ, ngày
    # 2026-07-29 (commit bc2890a, `decide_g8_status()` nay nhận đủ 6 biến gồm
    # `reporting_ok` — xác nhận qua đọc code + `git log -S"reporting_ok"` +
    # `tests/test_g8_quality_gate.py` 5 test khóa đúng hành vi mới). Comment
    # SỬA 2026-07-31 CRITICAL KEY_MISMATCH bên dưới được viết SAU bug 5-vs-6
    # nhưng TRƯỚC khi phát hiện nó đã được vá — nên vẫn đúng về key-mismatch,
    # chỉ riêng câu mở đầu "chỉ tính 5 điều kiện" ở trên là không còn đúng.
    # G8-AUTO-10 do đó KHÔNG còn là "cửa duy nhất" — nó là lớp kiểm ĐỘC LẬP
    # THỨ HAI đọc lại checkpoint, hữu ích nếu checkpoint bị sửa tay/ghi sai
    # key sau khi run_g8_auto.py đã quyết định g8_status (đúng như key-mismatch
    # bên dưới minh hoạ) — không phải vì run_g8_auto.py không tự kiểm.
    # SỬA 2026-07-31 (audit tautology vòng 2 — CRITICAL KEY_MISMATCH): trước
    # đây đọc "reporting_completeness_pct"/"reporting_pct" — nhưng
    # run_g8_auto.py::write_g8_checkpoint() (dòng ~1919) chỉ TỪNG ghi khóa
    # "reporting_score_pct". Hai khóa cũ KHÔNG BAO GIỜ được ghi bởi đường sản
    # xuất thật ⇒ pct luôn None ⇒ G8-AUTO-10 luôn REVIEW ⇒ MỌI đề tài thật
    # kẹt vĩnh viễn, không bao giờ đạt PASS_G8_REVIEW_RECORDED — xác nhận
    # bằng grep: run_g8_auto.py không có dòng nào ghi 2 khóa cũ. Đọc đúng khóa
    # thật trước; giữ 2 khóa cũ làm fallback vô hại (đề phòng checkpoint từ
    # writer khác/tương lai).
    reporting_pct = checkpoint.get("reporting_score_pct")
    if reporting_pct is None:
        reporting_pct = checkpoint.get("reporting_completeness_pct")
    if reporting_pct is None:
        reporting_pct = checkpoint.get("reporting_pct")
    try:
        pct = float(reporting_pct)
    except (TypeError, ValueError):
        pct = None
    if pct is None:
        rep_status, rep_evidence = "REVIEW", "không đọc được % hoàn thành checklist chuẩn báo cáo"
    elif pct < 60:
        rep_status = "REVIEW"
        rep_evidence = (
            f"checklist chuẩn báo cáo {pct:.0f}% < 60% — run_g8_auto.py cũng dùng "
            "đúng ngưỡng này khi tính g8_status (từ 2026-07-29); đây là lớp kiểm "
            "độc lập thứ hai đọc lại checkpoint, phòng khi checkpoint bị sửa tay/ghi sai key"
        )
    else:
        rep_status, rep_evidence = "PASS", f"checklist chuẩn báo cáo {pct:.0f}%"
    automatic.append(_criterion(
        "G8-AUTO-10",
        "Checklist chuẩn báo cáo đạt ngưỡng đã tuyên bố là bắt buộc",
        rep_status,
        rep_evidence,
        "Bổ sung các mục checklist còn thiếu trong bản thảo trước khi mời phản biện.",
    ))

    # ── G8-AUTO-11 — thiết kế KHÔNG lệch giữa G1 và G2 ─────────────────────
    # THÊM 2026-07-30 (G8-F5, MEDIUM DOWNSTREAM_CONTRACT_RISK): design_code ở
    # trên (đầu hàm) đọc checkpoint/g2_checkpoint bằng logic RIÊNG của module
    # này, KHÁC gate_contract.resolve_design_code() mà G5/G7 đã nối vào. Nếu
    # G1 và G2 từng chạy với --design khác nhau (run_g2_auto.py chỉ CẢNH BÁO
    # console, không chặn), G8-AUTO-07/08 (đăng ký/chia sẻ dữ liệu) có thể
    # âm thầm dùng design_code SAI mà không ai biết. Giải pháp AN TOÀN: KHÔNG
    # đổi design_code chính (rủi ro lan sang mọi call site) — chỉ thêm tiêu
    # chí CẢNH BÁO (REVIEW, không BLOCK) tái dùng resolve_design_code() làm
    # trọng tài, giống cách G7-AUTO-01b đã làm cho G7.
    automatic.append(_criterion(
        "G8-AUTO-11",
        "Mã thiết kế KHÔNG lệch giữa G1 và G2 (ảnh hưởng đăng ký/chia sẻ dữ liệu)",
        "REVIEW" if design_drift_warning else "PASS",
        design_drift_warning or "G1/G2 khớp thiết kế (hoặc chỉ một nơi có giá trị)",
        "G1 suy luận và G2 (nơi bác sĩ có thể truyền --design tường minh) lệch nhau — "
        "chạy lại G1/G2 cho khớp trước khi tin design_code dùng ở G8-AUTO-07/08. Xem "
        "gate_contract.py::resolve_design_code().",
    ))

    # ── G8-AUTO-12 — chữ ký G8 phải ràng buộc ĐÚNG bản thảo hiện tại ────────
    # THÊM 2026-09-04 (vá lỗ hổng: chữ ký G8 chỉ băm A9 -- bản TỰ KIỂM do máy
    # sinh -- KHÔNG BAO GIỜ băm G7_A8_MANUSCRIPT_<study>.md; bản thảo có thể bị
    # sửa SAU KHI ký (đổi hiệu số, thêm trích dẫn đã rút, xóa cảnh báo an toàn)
    # mà chữ ký vẫn báo "hợp lệ", và không có kiểm tra nào ở downstream (kể cả
    # run_g10_assemble.py) từng phát hiện việc này). run_g8_auto.py nay nhúng
    # SHA-256 của bản thảo NGAY LÚC sinh A9 -- kiểm ở đây là đối chiếu hash đã
    # nhúng (tại thời điểm A9 được ký) với hash SỐNG của manuscript_text hiện
    # tại (đọc tươi từ đĩa ở evaluate_study()).
    #
    # Mức nghiêm trọng CÓ CHỦ Ý phân theo ledger_signed: sửa bản thảo TRƯỚC KHI
    # ký là hoạt động soạn thảo bình thường (REVIEW, không chặn) -- nguy hiểm
    # thật chỉ xảy ra SAU khi đã ký (BLOCK), đúng kịch bản mà module này sinh
    # ra để bắt.
    #
    # SỬA (cùng ngày, phát hiện qua chạy bộ test hồi quy đầy đủ): nhánh
    # "không tìm thấy hash nhúng" BAN ĐẦU trả REVIEW -- nhưng auto_review =
    # any(status=="REVIEW") kéo TOÀN BỘ report["status"] về STATUS_DRAFT vô
    # điều kiện (dòng ~921), nên MỌI đề tài đã ký G8 THẬT TRƯỚC bản vá này
    # (100% số đề tài đang có, vì khả năng nhúng hash chỉ vừa ra đời) sẽ đồng
    # loạt tụt từ PASS_G8_REVIEW_RECORDED xuống DRAFT_NEEDS_HUMAN_COMPLETION
    # dù nội dung không đổi gì -- đúng lớp lỗi BH08 mà chính comment cũ ở đây
    # định tránh (biến "chưa biết" thành "có vấn đề"), chỉ là áp nhầm hướng.
    # 6 test hồi quy cũ (test_g8_quality_gate.py) bắt được ngay. G8-AUTO-02 đã
    # sẵn REVIEW khi thiếu bản thảo -- không cần G8-AUTO-12 lặp lại tín hiệu
    # đó.
    # SỬA 05/10/2026 (soát từng cổng G8-03): nhánh «A9 không nhúng hash» trả PASS kể cả khi ĐANG CÓ bản thảo ⇒ ký được
    # một A9 (sinh lúc chưa có bản thảo) không ràng buộc bản thảo nào, và run_g10_assemble cũng bỏ qua vì hash nhúng
    # None — câu «bảo vệ THẬT nằm ở run_g10_assemble» SAI đúng cho trường hợp này. Nay: có bản thảo mà A9 không nhúng
    # hash ⇒ CHẶN (sinh lại A9 — rẻ); không có bản thảo thì G8-AUTO-02 đã REVIEW. Mối lo BH08 (đề tài ký trước 04/09
    # tụt hạng) không còn áp dụng: đề tài thật duy nhất chưa tới G8.
    _embedded_hash = _trich_hash_ban_thao_da_ky(presubmission_text)
    _live_hash = (
        hashlib.sha256(manuscript_text.encode("utf-8")).hexdigest()
        if manuscript_text.strip() else None
    )
    if _embedded_hash is None and _live_hash is not None:
        hash_status = "BLOCK"
        hash_evidence = (
            "A9 KHÔNG ràng buộc bản thảo đang có (A9 sinh khi chưa có bản thảo hoặc định dạng cũ) — chữ ký trên A9 này "
            "không chứng cho bản thảo nào; chạy lại run_g8_auto.py để nhúng hash rồi mới ký"
        )
    elif _embedded_hash is None:
        hash_status = "PASS"
        hash_evidence = "chưa có bản thảo để đối chiếu (G8-AUTO-02 đã REVIEW)"
    elif _live_hash is None:
        hash_status = "REVIEW"
        hash_evidence = f"bản thảo không còn tồn tại/rỗng trên đĩa, A9 đã nhúng hash {_embedded_hash[:12]}…"
    elif _embedded_hash == _live_hash:
        hash_status = "PASS"
        hash_evidence = f"hash khớp ({_live_hash[:12]}…) — bản thảo không đổi kể từ lúc A9 được sinh"
    else:
        hash_status = "BLOCK" if ledger_signed else "REVIEW"
        hash_evidence = (
            f"bản thảo đã bị sửa SAU KHI A9 được sinh: hash nhúng {_embedded_hash[:12]}… "
            f"≠ hash hiện tại {_live_hash[:12]}…"
            + (" — VÀ G8 ĐÃ ĐƯỢC KÝ trên bản A9 cũ: chữ ký không còn ràng buộc bản thảo đang có"
               if ledger_signed else " (chưa ký — sửa bản thảo trước khi ký là bình thường)")
        )
    automatic.append(_criterion(
        "G8-AUTO-12",
        "Chữ ký G8 ràng buộc ĐÚNG nội dung bản thảo hiện tại (không chỉ bản tự kiểm A9)",
        hash_status,
        hash_evidence,
        "Sinh lại A9 (run_g8_auto.py) rồi ký lại G8 sau bất kỳ thay đổi nào vào bản thảo.",
    ))

    # ── G8-AUTO-12b — chữ ký G8 ràng buộc ĐÚNG bản NHẬN XÉT phản biện (G8-04, hợp đồng CHUNG-E) ──────────────────────
    # Chữ ký G8 chỉ băm A9; A9 sinh TRƯỚC bản nhận xét nên sau khi ký có thể xoá/đổi/tráo bản nhận xét (đổi «Từ chối»
    # thành «Chấp nhận») mà G9/G10 chỉ hỏi sổ cái. Nay run_g8_auto nhúng băm bản nhận xét vào A9 (sinh lại A9 SAU khi có
    # bản nhận xét) — chữ ký A9 vì thế ràng buộc cả bản nhận xét; cổng sau so lại bằng cong_song.trich_bam_a9.
    _bam_bc = CS.trich_bam_a9(presubmission_text).get("bao_cao_phan_bien")
    _live_bc = (hashlib.sha256(review_report_text.encode("utf-8")).hexdigest()
                if review_report_text.strip() else None)
    if _live_bc is None and _bam_bc is None:
        bc_status, bc_evidence = "PASS", "chưa có bản nhận xét phản biện (G8-HUMAN-01 đòi)"
    elif _live_bc is None:
        bc_status = "BLOCK" if ledger_signed else "REVIEW"
        bc_evidence = f"A9 đã ràng buộc bản nhận xét {_bam_bc[:12]}… nhưng bản nhận xét KHÔNG còn trên đĩa"
    elif _bam_bc is None:
        bc_status = "BLOCK" if ledger_signed else "REVIEW"
        bc_evidence = (
            "A9 chưa nhúng băm bản nhận xét phản biện — sinh lại A9 (run_g8_auto.py) SAU khi có bản nhận xét để chữ "
            "ký G8 ràng buộc nó" + (" — G8 ĐÃ ký trên A9 không ràng buộc bản nhận xét" if ledger_signed else "")
        )
    elif _bam_bc == _live_bc:
        bc_status, bc_evidence = "PASS", f"băm bản nhận xét khớp ({_live_bc[:12]}…)"
    else:
        bc_status = "BLOCK" if ledger_signed else "REVIEW"
        bc_evidence = (
            f"bản nhận xét đã SỬA sau khi A9 được sinh: băm nhúng {_bam_bc[:12]}… ≠ hiện tại {_live_bc[:12]}…"
            + (" — VÀ G8 ĐÃ ký trên bản cũ" if ledger_signed else " (chưa ký — sinh lại A9 rồi mới ký)")
        )
    automatic.append(_criterion(
        "G8-AUTO-12b",
        "Chữ ký G8 ràng buộc ĐÚNG bản nhận xét phản biện hiện tại",
        bc_status,
        bc_evidence,
        "Sinh lại A9 (run_g8_auto.py) SAU khi có/sửa bản nhận xét phản biện, rồi mới ký G8.",
    ))

    # ── G8-AUTO-13 — tiền đề: bản thảo G7 đã PASS_G7_CONFIRMED (chấm sống) (G8-06) ─────────────────────────────────
    # Bản cũ không đọc kết luận của chính run_g8_auto («PENDING — cần IRB thật, SAP ký, kết quả thật») hay trạng thái
    # G7: ký được «bình duyệt trước nộp» cho bản thảo chưa có kết quả thật («Kết quả sẽ được điền sau khi khoá dữ
    # liệu»).
    # G7 PASS đã bao hàm G0–G6 PASS thật + kết quả G6 khớp + bản thảo sạch + tác giả đọc lại đúng bản này.
    g7_song = dict(tien_de_g7 or {"status": "REVIEW", "evidence": "không đo được G7 sống (chấm qua evaluate_study)"})
    automatic.append(_criterion(
        "G8-AUTO-13",
        "Bản thảo G7 đã PASS_G7_CONFIRMED (chấm sống) — tiền đề bình duyệt trước nộp",
        g7_song.get("status") if g7_song.get("status") in ("PASS", "REVIEW", "BLOCK") else "REVIEW",
        str(g7_song.get("evidence") or ""),
        "Hoàn tất G7 (kết quả thật từ G6, khai báo ICMJE, A12, đọc lại toàn văn gắn dấu) rồi mới bình duyệt G8.",
    ))

    # ── Tầng BẰNG CHỨNG BÌNH DUYỆT NGƯỜI THẬT ──────────────────────────────
    report_problems = review_report_issues(review_report_text)
    approval.append(_criterion(
        "G8-HUMAN-01",
        "Có bản NHẬN XÉT phản biện thật (không phải bản tự kiểm do máy sinh)",
        "PASS" if not report_problems else "REVIEW",
        "; ".join(report_problems) if report_problems else "đủ khuyến nghị, lỗi nghiêm trọng, góp ý, câu hỏi, kết luận",
        f"Người phản biện viết {peer_review_report_name(study)} theo mẫu binh-duyet.md.",
    ))

    approval.append(_criterion(
        "G8-HUMAN-02",
        "Sổ cái có phê duyệt G8 hợp lệ đúng vai trò phản biện",
        "PASS" if ledger_signed else "REVIEW",
        ledger_reason or f"ledger_approved={ledger_signed}",
        f"Người phản biện tự ký: approve_gate.py --gate G8 --reviewer-role {GC.required_reviewer_role_hint('G8')}",
    ))

    # Mức bảo đảm của khóa — KHÔNG được diễn giải scope='role' thành "đã độc lập".
    if signature_scope == "role":
        scope_status = "PASS"
        scope_evidence = (
            "ký bằng khóa RIÊNG của nhóm phản biện (scope=role) — có dấu vết tách bạch "
            "vận hành, NHƯNG vẫn không chứng minh được người ký khác chủ nhiệm"
        )
    elif signature_scope == "shared":
        scope_status = "REVIEW"
        scope_evidence = (
            "ký bằng khóa CHUNG (scope=shared) — khóa này ký được MỌI vai trò, nên chữ "
            "ký không phân biệt được phản biện độc lập với chủ nhiệm tự ký"
        )
    else:
        scope_status = "REVIEW"
        scope_evidence = (
            f"chưa xác định phạm vi khóa; khóa riêng nhóm phản biện có sẵn={role_key_available}"
        )
    approval.append(_criterion(
        "G8-HUMAN-03",
        "Mức bảo đảm của khóa ký được nêu đúng (không nói quá)",
        scope_status,
        scope_evidence,
        "Tạo khóa riêng: setup_gate_approval_key.py --role INDEPENDENT_PEER_REVIEWER, và để người phản biện giữ.",
    ))

    # Đối chiếu reviewer_ref giữa các cổng — chỉ số ĐỘC LẬP rẻ nhất hiện có.
    g8_ref = cross_gate_refs.get("G8", "")
    # G8-14 (05/10/2026): so sau chuẩn hoá — «pi-01» và «PI-01» là CÙNG một người.
    clashes = [
        gate for gate, ref in cross_gate_refs.items()
        if gate != "G8" and ref and g8_ref and norm_ref(ref) == norm_ref(g8_ref)
    ]
    if not g8_ref:
        ref_status, ref_evidence = "REVIEW", "chưa có bản ghi phê duyệt G8 để đối chiếu"
    elif clashes:
        ref_status = "REVIEW"
        ref_evidence = (
            f"reviewer_ref của G8 ({g8_ref!r}) TRÙNG với cổng {', '.join(sorted(clashes))} "
            "— cùng một người đang ký nhiều vai trò"
        )
    else:
        ref_status = "PASS"
        ref_evidence = f"reviewer_ref của G8 ({g8_ref!r}) khác mọi cổng còn lại"
    approval.append(_criterion(
        "G8-HUMAN-04",
        "Người ký G8 khác người ký các cổng khác (chỉ dấu độc lập)",
        ref_status,
        ref_evidence,
        "Mời người phản biện KHÔNG phải tác giả/chủ nhiệm, và dùng reviewer_ref riêng.",
    ))

    reviewer_declarations = [
        label for label, key in (
            ("khai xung đột lợi ích của người phản biện", "reviewer_coi_declared"),
            ("cam kết không phải tác giả/đồng nghiệp trực tiếp", "reviewer_independence_declared"),
            ("khai có/không dùng AI khi phản biện (ICMJE V.B)", "reviewer_ai_use_declared"),
            ("cam kết không tải bản thảo lên công cụ AI không bảo mật", "reviewer_confidentiality_declared"),
        )
        if g8.get(key) is not True
    ]
    # G8-02 (05/10/2026): đọc CHÍNH khối «KHAI BÁO CỦA NGƯỜI PHẢN BIỆN» trong bản nhận xét (tệp được băm vào A9 —
    # G8-AUTO-12b), không chỉ 4 cờ boolean trong study_meta (ai sửa cũng đặt được, «declared=True» không phân biệt khai
    # KHÔNG hay CÓ xung đột). Tự khai CÓ xung đột/LÀ đồng tác giả ⇒ CHẶN.
    kb_chan, kb_xem = (khai_bao_nguoi_phan_bien(review_report_text) if review_report_text.strip()
                       else ([], ["chưa có bản nhận xét phản biện để đọc khối khai báo"]))
    van_de_05 = kb_chan + kb_xem + (["cờ gate_params.G8 chưa đủ: " + "; ".join(reviewer_declarations)]
                                    if reviewer_declarations else [])
    approval.append(_criterion(
        "G8-HUMAN-05",
        "Người phản biện đã khai COI, tính độc lập và việc dùng AI (khối khai báo trong bản nhận xét)",
        "BLOCK" if kb_chan else "REVIEW" if van_de_05 else "PASS",
        "; ".join(van_de_05) if van_de_05 else "khối khai báo: không xung đột, không đồng tác giả, AI đã khai, đã cam "
                                               "kết bảo mật; đủ 4 cờ gate_params.G8",
        "ICMJE §II.B.1.b và §V.B: người phản biện tự điền khối KHAI BÁO trong bản nhận xét; có xung đột thì phải TỪ "
        "CHỐI phản biện — mời người khác.",
    ))

    # G8-HUMAN-06 (G8-01, 05/10/2026): kết luận của phản biện phải CHO PHÉP nộp — bản cũ không đọc mức đã chọn hay kết
    # luận ⇒ «☑ Từ chối» / «Sửa lớn» / «Cần sửa thêm» / bảng lỗi nghiêm trọng còn dòng vẫn ký được và G10 in «Đã qua
    # G8».
    van_de_06: list[str] = []
    if not review_report_text.strip():
        van_de_06.append("chưa có bản nhận xét phản biện")
    else:
        muc = muc_khuyen_nghi(review_report_text)
        if muc not in _MUC_CHO_PHEP_NOP:
            van_de_06.append(f"khuyến nghị {('«' + muc.upper() + '»') if muc else 'chưa chọn'} — chỉ CHẤP NHẬN/SỬA "
                             "NHỎ mới cho phép nộp")
        ket_luan = ket_luan_tong_the(review_report_text)
        if ket_luan != "san_sang":
            van_de_06.append("kết luận tổng thể " + ("«cần sửa thêm»" if ket_luan == "can_sua" else "chưa chọn"))
        so_loi, _thieu = loi_nghiem_trong(review_report_text)
        if so_loi:
            van_de_06.append(f"còn {so_loi} lỗi nghiêm trọng trong bản nhận xét")
    approval.append(_criterion(
        "G8-HUMAN-06",
        "Kết luận phản biện CHO PHÉP nộp (chấp nhận/sửa nhỏ, «sẵn sàng nộp», không còn lỗi nghiêm trọng)",
        "REVIEW" if van_de_06 else "PASS",
        "; ".join(van_de_06) if van_de_06 else "khuyến nghị cho phép nộp, kết luận «sẵn sàng nộp», 0 lỗi nghiêm trọng",
        "Sửa bản thảo theo nhận xét → sinh lại A9 → người phản biện viết VÒNG SAU xác nhận đã xử lý (khuyến nghị "
        "chấp nhận/sửa nhỏ, «sẵn sàng nộp», bảng lỗi nghiêm trọng «không có») rồi mới ký G8.",
    ))

    # ── Tổng hợp ───────────────────────────────────────────────────────────
    # 05/10/2026 (G8-02): tiêu chí người cũng có thể CHẶN (phản biện tự khai có xung đột) ⇒ BLOCKED, không «chờ ký».
    auto_blocked = any(row["status"] == "BLOCK" for row in automatic + approval)
    auto_review = any(row["status"] == "REVIEW" for row in automatic)
    approval_complete = all(row["status"] == "PASS" for row in approval)
    has_review_evidence = not report_problems

    if auto_blocked:
        status = STATUS_BLOCKED
    elif auto_review:
        status = STATUS_DRAFT
    elif not has_review_evidence and not ledger_signed:
        status = STATUS_READY
    elif not approval_complete:
        status = STATUS_PENDING
    else:
        status = STATUS_REVIEWED

    # SỬA 2026-07-30 (G8-F4, LOW INTERNAL_INCONSISTENCY): tên
    # STATUS_PENDING="PENDING_REAL_REVIEW_SIGNATURE" khiến bác sĩ đọc nhầm là
    # "còn thiếu CHỮ KÝ" ngay cả khi ledger_signed=True thật (chữ ký G8 đã tồn
    # tại, chỉ thiếu bằng chứng NỘI DUNG/ĐỘC LẬP khác — bản nhận xét, khóa
    # CHUNG, hoặc reviewer_ref trùng cổng khác). KHÔNG đổi tên hằng số/giá trị
    # chuỗi (hợp đồng downstream: test + mọi nơi đọc report["status"]) — chỉ
    # làm rõ NGỮ CẢNH trong một trường evidence riêng.
    status_detail = ""
    if status == STATUS_PENDING:
        missing_labels = [row["label"] for row in approval if row["status"] != "PASS"]
        if ledger_signed:
            status_detail = (
                "Đã có chữ ký G8 hợp lệ trên sổ cái (ledger_signed=True) — còn thiếu: "
                + "; ".join(missing_labels)
            )
        else:
            status_detail = (
                "Chưa có chữ ký G8 hợp lệ trên sổ cái — "
                + (ledger_reason or "chưa ai duyệt")
            )

    pending = [
        row["action"] for row in automatic + approval
        if row["status"] != "PASS" and row.get("action")
    ]
    return {
        "schema_version": "1.0",
        "contract_version": QUALITY_CONTRACT_VERSION,
        "study": study,
        "gate": "G8",
        "status": status,
        "status_detail": status_detail,
        "automated_checks_passed": not auto_blocked,
        "package_ready_for_review": not auto_blocked and not auto_review,
        "review_evidence_complete": approval_complete,
        "signature_scope": signature_scope,
        "automatic_criteria": automatic,
        "approval_criteria": approval,
        "pending_actions": list(dict.fromkeys(pending)),
        "standards_basis": [dict(item) for item in STANDARDS_BASIS],
        "scope_statement": (
            "PASS_G8_REVIEW_RECORDED CỐ Ý không mang chữ 'ĐỘC LẬP'. Chữ ký G8 chứng "
            "minh rằng một người truy cập được khóa ký đã xác nhận artifact với nội "
            "dung đúng bằng hash lúc ký, và tự khai vai trò phản biện độc lập. Vì "
            "HMAC là mật mã ĐỐI XỨNG (máy xác minh buộc phải giữ khóa đã ký), hệ "
            "KHÔNG chứng minh được người ký khác chủ nhiệm đề tài; khóa riêng theo "
            "vai trò chỉ chứng minh một FILE tồn tại trên cùng máy. Bằng chứng độc "
            "lập THẬT phải đến từ ngoài hệ (thư phản biện có danh tính, biên bản hội "
            "đồng). approve_gate.py dùng chính báo cáo này để từ chối ký khi chưa đạt; cổng sau đối chiếu băm bản "
            "thảo và bản nhận xét nhúng trong A9."
        ),
        "disclaimer": "Cần bác sĩ kiểm chứng.",
    }


# ════════════════════════════════════════════════════════════════════════════
# Xuất báo cáo, cập nhật checkpoint, CLI
# ════════════════════════════════════════════════════════════════════════════


def write_quality_report(study: str, out_dir: Path, report: Mapping[str, Any]) -> Path:
    out_dir = Path(out_dir)
    (out_dir / "G8_QUALITY_REPORT.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n"
    )
    lines = [
        f"# BÁO CÁO CHẤT LƯỢNG G8 (BÌNH DUYỆT) — {study}",
        "",
        f"**Trạng thái:** `{report.get('status')}`",
    ]
    # G8-F4: làm rõ NGỮ CẢNH của trạng thái (vd STATUS_PENDING có thể là "đã
    # ký, còn thiếu bằng chứng khác" chứ không phải "chưa ký").
    if report.get("status_detail"):
        lines.append(f"**Chi tiết trạng thái:** {report['status_detail']}")
    lines += [
        f"**Phiên bản hợp đồng:** {report.get('contract_version')}",
        f"**Phạm vi khóa ký:** {report.get('signature_scope') or 'không xác định'}",
        "",
        "## Kiểm tự động (máy kiểm NỘI DUNG gói tiền nộp bài)",
        "| Mã | Tiêu chí | Trạng thái | Bằng chứng |",
        "|---|---|---|---|",
    ]
    for row in report.get("automatic_criteria", []):
        lines.append(
            f"| {row['id']} | {row['label']} | {row['status']} | "
            f"{str(row.get('evidence') or '').replace('|', '/')} |"
        )
    lines.extend([
        "",
        "## Bằng chứng bình duyệt người thật",
        "| Mã | Tiêu chí | Trạng thái | Bằng chứng |",
        "|---|---|---|---|",
    ])
    for row in report.get("approval_criteria", []):
        lines.append(
            f"| {row['id']} | {row['label']} | {row['status']} | "
            f"{str(row.get('evidence') or '').replace('|', '/')} |"
        )
    lines.extend(["", "## Việc còn lại"])
    pending = report.get("pending_actions") or []
    lines.extend(f"- {item}" for item in pending)
    if not pending:
        lines.append("- Không còn mục chờ trong hợp đồng G8.")
    lines.extend([
        "",
        "## Nền chuẩn",
        "| Chuẩn | Phạm vi | Nguồn |",
        "|---|---|---|",
    ])
    for item in report.get("standards_basis", []):
        source = str(item.get("url") or item.get("doi") or item.get("pmid") or "")
        lines.append(
            f"| {item.get('standard')} | {item.get('scope')} | {source.replace('|', '/')} |"
        )
    lines.extend([
        "",
        "## Giới hạn phán định",
        str(report.get("scope_statement") or ""),
        "",
        "> Cần bác sĩ kiểm chứng.",
    ])
    md_path = out_dir / "G8_QUALITY_REPORT.md"
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return md_path


def refresh_checkpoint(*, study: str, out_dir: Path, report: Mapping[str, Any],
                       quality_report_path: Path) -> Path:
    """Gắn kết quả chất lượng vào G8_checkpoint, giữ nguyên khóa downstream."""
    out_dir = Path(out_dir)
    checkpoint_path = out_dir / "G8_checkpoint.json"
    checkpoint = _read_json(checkpoint_path)
    checkpoint.update({
        "study": study,
        "gate": "G8",
        "quality_contract_version": QUALITY_CONTRACT_VERSION,
        "quality_gate": dict(report),
    })
    artifacts = checkpoint.get("artifacts")
    if not isinstance(artifacts, dict):
        artifacts = {}
        checkpoint["artifacts"] = artifacts
    artifacts["quality_report"] = str(quality_report_path)
    checkpoint["disclaimer"] = "Cần bác sĩ kiểm chứng."
    PF.ghi_checkpoint_giu_moc_sinh(checkpoint_path, json.dumps(checkpoint, ensure_ascii=False, indent=2))
    return checkpoint_path


def evaluate_study(study: str, out_dir: Path, *, repo_root: Optional[Path] = None,
                   write: bool = True) -> dict[str, Any]:
    """Chấm lại G8 từ artifact đã có; KHÔNG ký, KHÔNG tự tạo nhận xét phản biện."""
    out_dir = Path(out_dir)
    repo_root = Path(repo_root) if repo_root else out_dir.parent.parent
    checkpoint = _read_json(out_dir / "G8_checkpoint.json")
    presubmission = out_dir / presubmission_artifact_name(study)

    try:
        import run_g10_assemble as G10
        citation_ok, citation_detail = G10.citation_verification_ok(study, out_dir, kiem_ban_g10=False)
    except Exception as exc:  # pragma: no cover - lưới an toàn
        citation_ok, citation_detail = False, f"không kiểm được A12: {exc}"

    ledger_signed = GC.ledger_approved("G8", study, presubmission, repo_root=repo_root)
    try:
        ledger_reason = "" if ledger_signed else GC.gate_block_reason(
            "G8", study, presubmission, repo_root=repo_root
        )
    except Exception:  # pragma: no cover
        ledger_reason = ""
    try:
        scope = GC.approving_signature_scope("G8", study, repo_root=repo_root)
    except Exception:  # pragma: no cover
        scope = None
    try:
        role_key = GC.per_role_key_available(REVIEWER_ROLE_GROUP)
    except Exception:  # pragma: no cover
        role_key = False

    records = ledger_records(study, repo_root)
    cross_refs = {
        gate: _reviewer_ref(_latest_approved(records, gate))
        for gate in ("G2", "G4", "G5", "G8", "G9")
    }

    # G8-F5 + G8-10 (05/10/2026): resolve_design_code() (G2 > G1, đã nối vào G5/G7) là nguồn thiết kế DÙNG CHUNG — nay
    # cũng là design_code chính của G8 (bản cũ đọc G8/G2_checkpoint, rỗng ⇒ im lặng coi như quan sát: RCT không bị đòi
    # đăng ký/chia sẻ dữ liệu). Không xác định được ⇒ "" ⇒ G8-AUTO-07/08 REVIEW.
    try:
        design_code_song, design_drift_warning = GC.resolve_design_code(out_dir, default="")
    except Exception:  # pragma: no cover - lưới an toàn
        design_code_song, design_drift_warning = "", None

    # G8-06: tiền đề G7 chấm SỐNG (PASS_G7_CONFIRMED bao hàm G0–G6 thật + kết quả G6 khớp + bản thảo sạch + đọc lại).
    try:
        g7s = CS.trang_thai_song("G7", study, out_dir, repo_root=repo_root)
        muc = g7s.get("muc")
        tien_de_g7 = {"status": "PASS" if muc == "PASS" else "BLOCK" if muc == "BLOCKED" else "REVIEW",
                      "evidence": f"G7={g7s.get('status')}"}
    except Exception as exc:  # noqa: BLE001 — không đo được ≠ đạt
        tien_de_g7 = {"status": "REVIEW", "evidence": f"không chấm được G7 sống: {type(exc).__name__}"}

    # G8-07: attestation đã ký trong gói G2 (khi G2 đã duyệt theo hợp đồng dùng chung) là nguồn thẩm quyền cho đăng ký.
    attestation_g2: dict[str, Any] = {}
    try:
        import g2_quality_gate as G2Q  # noqa: PLC0415 — import lười
        import g7_quality_gate as G7Q  # noqa: PLC0415
        if G7Q.g2_da_duyet(study, out_dir, repo_root)[0]:
            attestation_g2 = G2Q.extract_attestation(_read_text(out_dir / f"G2_A3_ETHICS_PACKAGE_{study}.md")) or {}
    except Exception:  # noqa: BLE001 — không đọc được thì rơi về gate_params.G8 (vẫn kiểm ISO/fullmatch)
        attestation_g2 = {}

    report = evaluate_g8_quality(
        study=study,
        checkpoint=checkpoint,
        presubmission_text=_read_text(presubmission),
        manuscript_text=_read_text(out_dir / manuscript_artifact_name(study)),
        sap_text=_read_text(out_dir / f"G4_A5_SAP_FINAL_{study}.md"),
        review_report_text=_read_text(out_dir / peer_review_report_name(study)),
        g2_checkpoint=_read_json(out_dir / "G2_checkpoint.json"),
        meta=GC.load_study_meta(out_dir),
        citation_ok=bool(citation_ok),
        citation_detail=str(citation_detail),
        ledger_signed=bool(ledger_signed),
        ledger_reason=str(ledger_reason),
        signature_scope=scope,
        role_key_available=bool(role_key),
        cross_gate_refs=cross_refs,
        design_drift_warning=design_drift_warning,
        design_code=design_code_song,
        tien_de_g7=tien_de_g7,
        attestation_g2=attestation_g2,
    )
    if write:
        report_path = write_quality_report(study, out_dir, report)
        # VÁ 26/08/2026 (cùng họ lỗi BH06 với g2/g4_quality_gate.py): out_dir luôn
        # tuyệt đối nên report_path cũng tuyệt đối — chỉ đổi CHUỖI ghi vào
        # checkpoint sang tương đối với repo_root, không đổi hành vi ghi file thật.
        try:
            recorded_path = report_path.relative_to(repo_root)
        except ValueError:
            recorded_path = report_path
        refresh_checkpoint(
            study=study, out_dir=out_dir, report=report,
            quality_report_path=recorded_path,
        )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Chấm lại hợp đồng chất lượng G8; không ký thay người phản biện."
    )
    parser.add_argument("--study", required=True)
    args = parser.parse_args()
    GC.ensure_utf8_stdout()
    repo_root = Path(__file__).resolve().parents[1]
    study = re.sub(r"[^\w\-]", "_", args.study.strip().replace(" ", "-"))
    out_dir = repo_root / "exports" / study
    report = evaluate_study(study, out_dir, repo_root=repo_root, write=True)
    print(f"G8 quality status: {report['status']}")
    print(f"Phạm vi khóa ký: {report.get('signature_scope') or 'không xác định'}")
    for row in report["automatic_criteria"] + report["approval_criteria"]:
        if row["status"] != "PASS":
            print(f"  {row['status']:6} {row['id']} — {row['label']}")
            print(f"         ↳ {row['evidence']}")
    print(f"Báo cáo: {out_dir / 'G8_QUALITY_REPORT.md'}")
    print("Cần bác sĩ kiểm chứng.")
    return 0 if report["status"] != STATUS_BLOCKED else GC.EXIT_GUARDRAIL_FAIL


if __name__ == "__main__":
    raise SystemExit(main())
