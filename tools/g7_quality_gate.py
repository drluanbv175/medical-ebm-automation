#!/usr/bin/env python3
"""Hợp đồng chất lượng cho cổng G7: BẢN THẢO IMRAD.

LÝ DO MODULE NÀY TỒN TẠI
------------------------
G7 sinh artifact A8 — **bản thảo sẽ gửi tạp chí**. Đây là cổng có đầu ra đi ra
ngoài xa nhất, nên sai ở đây là sai công khai.

Trước 2026-07-28, G7 không có hợp đồng chất lượng riêng (G0/G1/G2/G3 đều đã có).
Hệ quả TÁI HIỆN ĐƯỢC, không phải suy đoán — chạy thử trên một đề tài chỉ có G0
(và G0 còn đang BLOCKED, thoát mã 2), không hề có G1–G6:

    python tools/run_g7_auto.py --study ZZ-G7-PROBE
    → "✅ G7 HOÀN THÀNH", guardrail "✅ PASS", thoát mã 0
    → sinh trọn bản thảo IMRAD 3.547 từ, có Methods, có cỡ mẫu, có mục đạo đức,
      có tài liệu tham khảo

Tức G7 viết một bản thảo hoàn chỉnh cho đề tài **chưa có câu hỏi nghiên cứu, chưa
có thiết kế, chưa qua Hội đồng Đạo đức, chưa tính cỡ mẫu, chưa có dữ liệu, chưa
phân tích** — rồi tuyên bố hoàn thành.

ĐIỂM KHÁC CỐT LÕI so với g0/g1/g2/g3_quality_gate
-------------------------------------------------
Module này **đọc lại artifact A8 TỪ ĐĨA**, không chấm bản vừa sinh trong bộ nhớ.
Lý do: G7 là cổng mà bản thảo phải chuyển từ SKELETON sang BẢN THẢO THẬT bằng tay
bác sĩ. Chấm bản do chính công cụ vừa sinh ra thì mãi mãi chỉ đo được công cụ, và
không bao giờ biết bác sĩ đã điền tới đâu.

BA TRẠNG THÁI
-------------
- ``BLOCKED``: thiếu tiền đề bắt buộc (không có G1 → chuẩn báo cáo chọn sai), lỗi
  liêm chính, hoặc artifact khuyết.
- ``DRAFT_READY_NEEDS_HUMAN_REVIEW``: khung bản thảo đã dựng đúng; còn chờ kết quả
  thật và phần viết của bác sĩ. **Đây là trạng thái ĐÚNG của một lần chạy G7 sớm.**
- ``PASS_G7_CONFIRMED``: hết ô [CẦN KẾT QUẢ THẬT], có kết quả phân tích thật, trích
  dẫn đã kiểm chứng (A12), và tác giả đã chốt khai báo ICMJE. Chỉ khi đó mới được
  nói bản thảo sẵn sàng cho G8 (bình duyệt).

GIỚI HẠN PHÁN ĐỊNH: ``PASS_G7_CONFIRMED`` KHÔNG có nghĩa bản thảo tốt, đúng khoa
học, hay đáng đăng. Nó chỉ nói: không còn chỗ trống, không còn khẳng định về việc
chưa làm, và người thật đã xác nhận (SỬA 2026-07-30, audit toàn diện G0-G10,
G7-F4: G7 KHÔNG có trong ``_GATE_REQUIRED_STAKEHOLDERS`` của gate_contract.py —
đây là xác nhận nội dung, không phải chữ ký mật mã như G2/G4/G5/G8/G9/G10).
Thẩm định khoa học là việc của G8.

Chạy lại độc lập (không sinh lại bản thảo, không ghi đè bản bác sĩ đã sửa):
    python tools/g7_quality_gate.py --study <MÃ-ĐỀ-TÀI>
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys

# Windows: stdout mặc định cp1252 giết print() tiếng Việt — ép UTF-8 (chốt BH55/R4)
import sys as _sys_r4
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

for _s_r4 in (_sys_r4.stdout, _sys_r4.stderr):
    try:
        _s_r4.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gate_contract as GC  # noqa: E402
import placeholder_contract as PC  # noqa: E402

# Sentinel "chưa truyền" cho design_drift_warning — phân biệt với None HỢP LỆ
# (nghĩa là "đã tính SỐNG qua resolve_design_code() và không có lệch", SỬA
# 2026-07-31, G7-AUTO-01b). Dùng None làm mặc định sẽ không phân biệt được
# "caller không truyền gì" (nên fallback checkpoint cũ) với "caller đã tính
# sống và kết quả là không lệch" (PHẢI tin giá trị sống, không fallback).
_UNSET = object()

STATUS_BLOCKED = "BLOCKED"
STATUS_DRAFT_READY = "DRAFT_READY_NEEDS_HUMAN_REVIEW"
STATUS_CONFIRMED = "PASS_G7_CONFIRMED"

QUALITY_CONTRACT_VERSION = "G7-2026.2"  # 04/10/2026: soát từng cổng G7

# Mục IMRAD bắt buộc phải có trong A8.
REQUIRED_A8_SECTIONS: Sequence[str] = (
    "TÓM TẮT",
    "I. GIỚI THIỆU",
    "II. PHƯƠNG PHÁP",
    "III. KẾT QUẢ",
    "IV. BÀN LUẬN",
    "V. KẾT LUẬN",
    "TÀI LIỆU THAM KHẢO",
)

# Khai báo bắt buộc theo ICMJE — thiếu là tạp chí trả lại.
ICMJE_DECLARATIONS: Sequence[tuple[str, str]] = (
    ("author_contributions", "Đóng góp tác giả (CRediT/ICMJE 4 tiêu chí)"),
    ("coi_declared", "Xung đột lợi ích"),
    ("funding_declared", "Nguồn tài trợ"),
    ("data_sharing_statement", "Tuyên bố chia sẻ dữ liệu"),
    ("ai_use_declared", "Khai báo sử dụng công cụ AI"),
)

_REVIEW_ROLES = {
    "pi", "principal investigator", "corresponding author", "tác giả liên lạc",
    "chủ nhiệm", "chủ nhiệm đề tài", "tác giả chính", "first author",
}

_PLACEHOLDER_MARKERS = ("[CẦN", "[REQUIRE_HUMAN", "CHƯA XÁC NHẬN", "[TODO", "___")

# Câu KHẲNG ĐỊNH TRẦN về việc có thể chưa xảy ra. Đây là lớp phòng thủ cuối: kể cả
# khi bác sĩ tự viết tay vào bản thảo, những câu này không được đứng một mình mà
# thiếu bằng chứng tương ứng ở cổng trước.
_UNSUPPORTED_CLAIM_PATTERNS: Sequence[tuple[str, str, str]] = (
    # SỬA 2026-07-31 (audit tautology vòng 2, G7-AUTO-06 — phòng thủ lớp 2):
    # thêm biến thể viết tắt "IRB" — trước đây chỉ khớp "Hội đồng Đạo đức",
    # bỏ lọt 2 câu khẳng định thật ở run_g7_auto.py (dòng ~1398, ~1333 trước
    # khi vá) dùng chữ "IRB" thay vì "Hội đồng Đạo đức".
    #
    # SỬA 2026-09-04 (Workflow đối kháng đa-agent vòng 2 — G7-AUTO-06 bị vượt
    # qua bằng cách diễn đạt tự nhiên): 4 regex trước đây đòi cụm từ LIỀN KỀ
    # cứng nhắc — không cho chèn thêm chữ (tên bệnh viện, số quyết định…) và
    # không có từ đồng nghĩa. Câu thật "Đề tài đã được Hội đồng Đạo đức Bệnh
    # viện Quân y 175 phê duyệt." (chèn tên tổ chức, đúng cách viết tự nhiên
    # nhất cho tổ chức của repo này) trước đây LỌT hoàn toàn qua regex #1.
    # Nay dùng cửa sổ ký tự giới hạn `[^.\n]{0,N}?` (cùng khuôn với R4/R5 của
    # guardrail_check_g1 trong run_g1_auto.py) để cho phép chèn văn bản mô tả
    # giữa thực thể và động từ, và thêm từ đồng nghĩa (chấp thuận/thông qua/
    # đồng ý) cho khẳng định IRB. Đây là lớp phòng thủ CUỐI nên thiên về
    # recall cao — chấp nhận vài false positive REVIEW còn hơn để lọt một
    # khẳng định bịa đặt thật.
    (r"được\s+(?:Hội\s*đồng\s*Đạo\s*đức|IRB|Ethics\s*Committee)[^.\n]{0,60}?"
     r"(?:phê\s*duyệt|chấp\s*thuận|thông\s*qua|đồng\s*ý)", "irb_approved",
     "khẳng định đã được Hội đồng Đạo đức/IRB phê duyệt"),
    (r"đã\s+(?:được\s+)?đăng\s*ký[^.\n]{0,20}?ClinicalTrials", "registered",
     "khẳng định đã đăng ký ClinicalTrials.gov"),
    (r"SAP[^.\n]{0,30}?đã\s+(?:được\s+)?khóa|"
     r"kế\s*hoạch\s*phân\s*tích[^.\n]{0,30}?đã\s+khóa|"
     r"SAP\s+khóa\s+trước\s+khi\s+xem\s+dữ\s+liệu", "sap_locked",
     "khẳng định đã khóa SAP"),
    (r"(?:cơ\s*sở\s*dữ\s*liệu|dữ\s*liệu)[^.\n]{0,30}?đã\s+(?:được\s+)?khóa", "db_locked",
     "khẳng định đã khóa cơ sở dữ liệu"),
    # VÁ 04/10/2026 (soát từng cổng, G7-02): lớp DUY NHẤT soi khẳng định trần từng bỏ lọt câu bị động «được phê duyệt
    # bởi …», câu chủ động «Hội đồng Đạo đức … đã phê duyệt», chính tả «khoá», khoá không có chữ «đã», khẳng định
    # ĐỒNG THUẬN, câu do CHÍNH bộ sinh in («SAP … ký ngày … (G4=LOCKED)») và mọi câu tiếng Anh. Văn bản và mẫu cùng
    # được chuẩn hoá dấu thanh (khoá → khóa) trước khi so.
    (r"được\s+(?:phê\s*duyệt|chấp\s*thuận|thông\s*qua)[^.\n]{0,40}?bởi[^.\n]{0,10}?"
     r"(?:Hội\s*đồng\s*Đạo\s*đức|IRB|Ethics\s*Committee)", "irb_approved",
     "khẳng định đã được Hội đồng Đạo đức/IRB phê duyệt"),
    (r"(?:Hội\s*đồng\s*Đạo\s*đức|IRB)[^.\n]{0,60}?(?:đã\s+)?(?:phê\s*duyệt|chấp\s*thuận|thông\s*qua)",
     "irb_approved", "khẳng định đã được Hội đồng Đạo đức/IRB phê duyệt"),
    (r"approved\s+by[^.\n]{0,60}?(?:ethics|review\s+board|IRB)|"
     r"(?:ethics\s+committee|institutional\s+review\s+board|IRB)[^.\n]{0,40}?approv", "irb_approved",
     "khẳng định đã được Hội đồng Đạo đức/IRB phê duyệt"),
    (r"registered\s+(?:at|with|in|on)[^.\n]{0,20}?(?:ClinicalTrials|ICTRP|registry)", "registered",
     "khẳng định đã đăng ký ClinicalTrials.gov"),
    (r"SAP[^.\n]{0,40}?ký\s+ngày|G4\s*=\s*LOCKED|"
     r"(?:SAP|kế\s*hoạch\s*phân\s*tích)[^.\n]{0,30}?(?:được\s+)?khóa\s+(?:ngày|trước)|"
     r"(?:SAP|statistical\s+analysis\s+plan)[^.\n]{0,30}?(?:was|were|had\s+been)\s+(?:locked|finali[sz]ed|signed)",
     "sap_locked", "khẳng định đã khóa SAP"),
    (r"(?:cơ\s*sở\s*dữ\s*liệu|dữ\s*liệu)[^.\n]{0,30}?(?:được\s+)?khóa\s+(?:ngày|trước)|"
     r"(?:database|data)[^.\n]{0,30}?(?:was|were)\s+locked", "db_locked",
     "khẳng định đã khóa cơ sở dữ liệu"),
    (r"(?:đã\s+)?ký\s+(?:vào\s+)?(?:phiếu|bản|giấy)\s+(?:chấp\s*thuận|đồng\s*thuận)|"
     r"informed\s+consent\s+was\s+obtained|participants?\s+(?:provided|gave|signed)\s+(?:written\s+)?informed"
     r"\s+consent", "consent",
     "khẳng định người tham gia đã ký đồng thuận (không có G2 thật hoặc IRB miễn đồng thuận)"),
)


_STANDARDS_BASIS = (
    {
        "standard": "ICMJE Recommendations",
        "scope": "Tiêu chí tác giả, khai báo COI/tài trợ/chia sẻ dữ liệu/AI",
        "url": "https://www.icmje.org/recommendations/",
    },
    {
        "standard": "EQUATOR Network",
        "scope": "Chuẩn báo cáo theo thiết kế (CONSORT/STROBE/PRISMA/STARD/TRIPOD+AI)",
        "url": "https://www.equator-network.org/library/",
    },
    {
        "standard": "COPE",
        "scope": "Đạo đức xuất bản — không khẳng định điều chưa xảy ra",
        "url": "https://publicationethics.org/guidance",
    },
)


# ════════════════════════════════════════════════════════════════════════════
# Tiện ích
# ════════════════════════════════════════════════════════════════════════════

def _present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return True
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return False
        return not any(m in text.upper() for m in _PLACEHOLDER_MARKERS)
    if isinstance(value, Mapping):
        return any(_present(v) for v in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_present(v) for v in value)
    return True


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _g7_meta(meta: Mapping[str, Any]) -> Mapping[str, Any]:
    gp = meta.get("gate_params")
    if not isinstance(gp, Mapping):
        return {}
    g7 = gp.get("G7")
    return g7 if isinstance(g7, Mapping) else {}


def _valid_iso_time(value: Any) -> bool:
    if not _present(value):
        return False
    try:
        datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def _criterion(criterion_id: str, label: str, status: str,
               evidence: str, action: str = "") -> Dict[str, str]:
    return {"id": criterion_id, "label": label, "status": status,
            "evidence": evidence, "action": action}


def count_placeholders(text: str) -> Dict[str, int]:
    """Đếm ô còn trống trong bản thảo HIỆN TẠI (bản trên đĩa, không phải bản mẫu)."""
    return {
        "total": len(re.findall(r"\[CẦN", text)),
        "results": len(re.findall(r"\[CẦN KẾT QUẢ THẬT", text)),
        "methods": len(re.findall(r"\[CẦN", _section(text, "II. PHƯƠNG PHÁP", "III. KẾT QUẢ"))),
        "results_section": len(re.findall(r"\[CẦN", _section(text, "III. KẾT QUẢ", "IV. BÀN LUẬN"))),
    }


def _section(text: str, start_marker: str, end_marker: str) -> str:
    """Cắt một mục của bản thảo (rỗng nếu không tìm thấy)."""
    i = text.find(start_marker)
    if i < 0:
        return ""
    j = text.find(end_marker, i)
    return text[i:j] if j > i else text[i:]


_DONG_TRONG = re.compile(r"\n[ \t]*\n")


def _khoi_can(text: str) -> tuple[list[tuple[int, int]], list[int]]:
    """(khoảng các ô [CẦN …] ĐÃ ĐÓNG, vị trí các «[CẦN» KHÔNG đóng trong cùng đoạn).

    Đếm độ lồng ngoặc vuông («[CẦN — tài trợ …; IRB: [CẦN SỐ IRB THẬT]; …]» là MỘT ô) và KHÔNG vượt dòng trống: ô chưa
    đóng trong đoạn của nó là lỗi cấu trúc, không phải ô kéo dài tới «]» gần nhất ở nhiều đoạn sau."""
    text = text or ""
    dong_khoang: list[tuple[int, int]] = []
    ho: list[int] = []
    i = 0
    while True:
        k = text.find("[CẦN", i)
        if k < 0:
            return dong_khoang, ho
        m = _DONG_TRONG.search(text, k)
        het_doan = m.start() if m else len(text)
        do_long, dong = 0, None
        for j in range(k, het_doan):
            if text[j] == "[":
                do_long += 1
            elif text[j] == "]":
                do_long -= 1
                if do_long == 0:
                    dong = j
                    break
        if dong is None:
            ho.append(k)
            i = k + 4
        else:
            dong_khoang.append((k, dong + 1))
            i = dong + 1


def strip_placeholder_blocks(text: str) -> str:
    """Bỏ nội dung nằm TRONG nhãn [CẦN …] trước khi soi khẳng định.

    Nội dung trong nhãn là CHỈ DẪN cho bác sĩ ("KHÔNG được viết 'nghiên cứu được
    Hội đồng Đạo đức phê duyệt' trước khi việc đó xảy ra"), không phải khẳng định
    của bản thảo. Không bóc ra thì chính lời cảnh báo lại bị bắt là vi phạm — đã
    xảy ra thật khi chạy thử bản vá đầu tiên.

    VÁ 04/10/2026 (soát từng cổng, G7 — phát hiện bổ sung của phản biện): bản cũ `\\[CẦN.*?\\]` + DOTALL — một ô
    «[CẦN …» quên đóng ngoặc kéo phần bị bóc tới «]» gần nhất (thường là trích dẫn «[1]» nhiều đoạn sau) ⇒ mọi khẳng
    định nằm giữa («Đề tài đã được Hội đồng Đạo đức phê duyệt. SAP đã được khóa…») bị che khỏi G7-AUTO-06. Nay chỉ bóc
    ô ĐÃ ĐÓNG trong cùng đoạn (đếm ngoặc lồng); ô không đóng GIỮ NGUYÊN để khẳng định phía sau vẫn bị soi và
    `o_can_chua_dong` báo lỗi cấu trúc.
    """
    text = text or ""
    khoang, _ho = _khoi_can(text)
    phan, truoc = [], 0
    for a, b in khoang:
        phan.append(text[truoc:a])
        phan.append(" ")
        truoc = b
    phan.append(text[truoc:])
    return "".join(phan)


def o_can_chua_dong(text: str) -> List[str]:
    """Các ô «[CẦN …» không đóng ngoặc trong đoạn của nó (trích ≤ 60 ký tự) — lỗi cấu trúc bản thảo."""
    text = text or ""
    return [text[k:k + 60].replace("\n", " ") for k in _khoi_can(text)[1]]


def _chuan_hoa_chinh_ta(text: str) -> str:
    """NFC + đưa dấu thanh kiểu cũ/mới về MỘT kiểu (khoá → khóa, hoà → hòa, thuý → thúy) trước khi so mẫu.

    VÁ 04/10/2026 (soát từng cổng, G7-02): mẫu «khóa» không khớp «khoá» (cả repo dùng lẫn hai cách gõ) nên câu
    «SAP đã được khoá trước khi xem dữ liệu» lọt qua lớp phòng thủ cuối."""
    text = unicodedata.normalize("NFC", str(text or ""))
    for cu, moi in (("oá", "óa"), ("oà", "òa"), ("oả", "ỏa"), ("oã", "õa"), ("oạ", "ọa"),
                    ("oé", "óe"), ("oè", "òe"), ("oẻ", "ỏe"), ("oẽ", "õe"), ("oẹ", "ọe"),
                    ("uý", "úy"), ("uỳ", "ùy"), ("uỷ", "ủy"), ("uỹ", "ũy"), ("uỵ", "ụy")):
        text = text.replace(cu, moi).replace(cu.upper(), moi.upper()).replace(cu.capitalize(), moi.capitalize())
    return text


def find_unsupported_claims(text: str, signals: Mapping[str, bool]) -> List[str]:
    """Câu khẳng định điều CHƯA có bằng chứng ở cổng trước.

    Đây là lớp phòng thủ cuối cùng trước khi bản thảo rời hệ thống: kể cả khi bác
    sĩ tự gõ vào, "nghiên cứu được Hội đồng Đạo đức phê duyệt" mà không có G2 thật
    vẫn phải bị chặn.
    """
    body = strip_placeholder_blocks(_chuan_hoa_chinh_ta(text or ""))
    found: List[str] = []
    for pattern, signal, human in _UNSUPPORTED_CLAIM_PATTERNS:
        if re.search(_chuan_hoa_chinh_ta(pattern), body, re.IGNORECASE) and not signals.get(signal) \
                and human not in found:
            found.append(human)
    return found


def _gate_present(cp: Mapping[str, Any]) -> bool:
    """Checkpoint có tồn tại và KHÔNG ở trạng thái chặn (chỉ còn để tương thích; bộ chấm KHÔNG dùng — G7-01)."""
    return bool(cp) and not GC.is_blocked(dict(cp))


def _goc_repo(out_dir: Path, repo_root: Optional[Path]) -> Path:
    """Gốc repo chứa exports/<mã>: tham số tường minh > suy từ out_dir (…/exports/<mã>) > repo của công cụ."""
    if repo_root is not None:
        return Path(repo_root)
    out_dir = Path(out_dir)
    return out_dir.parent.parent if out_dir.parent.name == "exports" else Path(__file__).resolve().parents[1]


def g2_da_duyet(study: str, out_dir: Path, repo_root: Optional[Path] = None) -> tuple[bool, str]:
    """(G2 đã được IRB duyệt?, bằng chứng) — chữ ký sổ cái G2 khớp gói đạo đức HIỆN TẠI và
    gate_contract.g2_quality_contract_satisfied (hạn hiệu lực, phiên bản protocol/ICF, attestation đã ký).

    ĐÚNG phép kiểm mà G5, chốt khoá phân tích (kiem_khoa_phan_tich, G6), run_g7_auto và G10 dùng — điều phối thống nhất
    (04/10/2026): «G2 đã duyệt» phải mang MỘT nghĩa ở mọi cổng sau. Bộ chấm G2 sống (cong_song) đánh giá cả CHẤT LƯỢNG
    HỒ SƠ theo luật HIỆN HÀNH — phê duyệt IRB thật, chữ ký còn khớp, không vì luật hồ sơ mới mà thành «chưa duyệt»."""
    out_dir = Path(out_dir)
    root = _goc_repo(out_dir, repo_root)
    if not GC.ledger_approved("G2", study, out_dir / f"G2_A3_ETHICS_PACKAGE_{study}.md", repo_root=root):
        return False, "chưa có chữ ký sổ cái G2 (IRB) khớp gói đạo đức hiện tại"
    if not GC.g2_quality_contract_satisfied(_read_json(out_dir / "G2_checkpoint.json"), GC.load_study_meta(out_dir),
                                            study=study, out_dir=out_dir):
        return False, "hợp đồng chất lượng G2 chưa đạt (hết hạn / lệch phiên bản protocol-ICF / attestation)"
    return True, "chữ ký sổ cái + hợp đồng chất lượng G2 (cùng phép kiểm G5/G6/G10)"


def tien_de_song(study: str, out_dir: Path, repo_root: Optional[Path] = None) -> Dict[str, Dict[str, str]]:
    """{cổng: {status: PASS|REVIEW|BLOCK, evidence}} — chấm SỐNG G0–G6 bằng bộ chấm của chính cổng đó (cong_song).

    VÁ 04/10/2026 (soát từng cổng, G7-01): bản cũ coi «checkpoint tồn tại và không có needs_input.blocked» là đạt — mà
    run_g1/run_g2/run_g4/run_g6 KHÔNG ghi needs_input ⇒ G7 PASS khi G1 bị chặn, G2 chưa phê duyệt, G4 chưa ký SAP, không
    có G5, G6 quality BLOCKED. Nay mỗi cổng phải PASS_* thật (chữ ký + chất lượng do bộ chấm của cổng đó phán). Riêng G2
    (cổng cứng có sổ cái): đạt khi `g2_da_duyet` — cùng hợp đồng mà G5/G6/G10 dùng; không đạt thì mức chặn lấy theo
    bộ chấm G2 sống. G4/G5: hợp đồng của gate_contract VỐN LÀ chấm sống nên trùng nghĩa."""
    import cong_song as CS  # noqa: PLC0415 — import lười
    out_dir = Path(out_dir)
    ket: Dict[str, Dict[str, str]] = {}
    for g in ("G0", "G1", "G2", "G3", "G4", "G5", "G6"):
        s = CS.trang_thai_song(g, study, out_dir, repo_root=repo_root)
        muc = s.get("muc")
        if g == "G2":
            ok, ly_do = g2_da_duyet(study, out_dir, repo_root)
            ket[g] = {"status": "PASS" if ok else "BLOCK" if muc == "BLOCKED" else "REVIEW",
                      "evidence": f"G2: {ly_do} (bộ chấm G2 sống: {s.get('status')})"}
            continue
        ket[g] = {"status": "PASS" if muc == "PASS" else "BLOCK" if muc == "BLOCKED" else "REVIEW",
                  "evidence": f"{g}={s.get('status')}"}
    return ket


# Nơi G6 ghi tóm tắt phân tích: Python CLI (run_stats_analysis.py → exports/<mã>/) và đường R (khối cuối 03_analysis.R
# → 06_phan_tich_R/output/). VÁ 04/10/2026 (điều phối G6↔G7): bản đầu chỉ tìm ở gốc đề tài ⇒ đề tài phân tích bằng R
# (cắt ngang/thứ bậc như C1a) không bao giờ có «kết quả thật».
TOM_TAT_G6 = ("G6_analysis_summary.json", "06_ket_qua/G6_analysis_summary.json",
              "06_phan_tich_R/output/G6_analysis_summary.json")


def _thoi_diem(v: Any) -> Optional[datetime]:
    """ISO-8601 → datetime GIỜ ĐỊA PHƯƠNG không múi (để so được bản có/không múi giờ); hỏng ⇒ None."""
    try:
        d = datetime.fromisoformat(str(v or "").strip())
    except ValueError:
        return None
    return d.astimezone().replace(tzinfo=None) if d.tzinfo else d


def _cham_mot_tom_tat(p: Path, manifest: Mapping[str, Any], moc_khoa: datetime, so_ban_thao: set,
                      out_dir: Path) -> Dict[str, str]:
    ten = p.relative_to(out_dir).as_posix()
    tt = _read_json(p)
    if not tt:
        return {"status": "REVIEW", "evidence": f"{ten} không đọc được"}
    sha_tt = (tt.get("data_lock") or {}).get("sha256") if isinstance(tt.get("data_lock"), dict) else None
    sha_tt = sha_tt or tt.get("locked_data_sha256")
    sha_khoa = manifest.get("sha256")
    if sha_tt and sha_khoa and str(sha_tt).lower() != str(sha_khoa).lower():
        return {"status": "BLOCK", "evidence": f"{ten} phân tích trên dataset KHÁC bản khoá hiện hành (sha256 lệch) — "
                                               "chạy lại phân tích trên dữ liệu đã khoá, xoá tệp cũ"}
    if not sha_tt:
        # Không có dấu dữ liệu ⇒ dựa vào thời điểm sinh (ghi TRONG tệp; mtime chỉ là dự phòng, có thể bị dàn phẳng).
        sinh = _thoi_diem(tt.get("generated"))
        if sinh is None:
            try:
                import pipeline_freshness as PF  # noqa: PLC0415
                mtime_ngo = PF.mtime_khong_tin_duoc(out_dir)
            except Exception:  # noqa: BLE001
                mtime_ngo = "không kiểm được độ tin của mtime"
            if mtime_ngo:
                return {"status": "REVIEW", "evidence": f"{ten} không ghi sha256/thời điểm sinh và mtime không tin "
                                                        f"được ({mtime_ngo})"}
            sinh = datetime.fromtimestamp(p.stat().st_mtime)
        if sinh < moc_khoa:
            return {"status": "BLOCK", "evidence": f"{ten} sinh TRƯỚC thời điểm khoá dữ liệu"}
    try:
        n = int(tt.get("n_total"))
    except (TypeError, ValueError):
        return {"status": "REVIEW", "evidence": f"{ten} không có n_total đọc được"}
    if n not in so_ban_thao:
        return {"status": "REVIEW", "evidence": f"N phân tích = {n} ({ten}) KHÔNG thấy trong Tóm tắt/Kết quả — đối "
                                                "chiếu số liệu bản thảo với đầu ra G6"}
    return {"status": "PASS", "evidence": f"{ten} từ dataset khoá hiện hành; N = {n} khớp bản thảo"}


def doi_chieu_ket_qua_g6(study: str, out_dir: Path, manuscript_text: str,
                         repo_root: Optional[Path] = None) -> Dict[str, str]:
    """{status, evidence} — kết quả phân tích THẬT của G6 có mặt, từ ĐÚNG dataset đã khoá, và N khớp bản thảo (G7-05).

    Bản cũ chỉ hỏi «có G6_checkpoint» + cờ results_final — script G6 sinh ra là có checkpoint, chưa chạy phân tích nào
    vẫn đạt; số liệu trong bản thảo không được đối chiếu với đầu ra phân tích. Nay: (1) có tóm tắt G6 ở một trong
    TOM_TAT_G6; (2) dữ liệu đã khoá (DATA_LOCK_manifest LOCKED_FOR_ANALYSIS + locked_at); (3) mỗi tóm tắt mang sha256
    TRÙNG bản khoá hiện hành — vắng dấu thì thời điểm sinh phải SAU khoá (khoá lại cùng dữ liệu không làm mất hiệu lực
    kết quả cũ vì dấu nội dung trùng); (4) N phân tích có mặt trong Tóm tắt/Kết quả. Một tóm tắt cũ từ dataset khác còn
    nằm đó ⇒ CHẶN (nguy cơ chép số cũ vào bản thảo)."""
    out_dir = Path(out_dir)
    ung_vien = [out_dir / rel for rel in TOM_TAT_G6 if (out_dir / rel).is_file()]
    if not ung_vien:
        return {"status": "REVIEW",
                "evidence": "thiếu G6_analysis_summary.json — Python CLI (run_stats_analysis.py) ghi ở exports/<mã>/, "
                            "đường R ghi ở 06_phan_tich_R/output/ (khối cuối 03_analysis.R) — chưa có kết quả phân "
                            "tích thật để đối chiếu"}
    manifest = _read_json(out_dir / "DATA_LOCK_manifest.json")
    moc_khoa = _thoi_diem(manifest.get("locked_at"))
    if manifest.get("status") != "LOCKED_FOR_ANALYSIS" or moc_khoa is None:
        return {"status": "BLOCK", "evidence": "có kết quả phân tích mà dữ liệu chưa khoá (DATA_LOCK_manifest)"}
    noi = "\n".join(_section(manuscript_text or "", s, e) for s, e in (("TÓM TẮT", "I. GIỚI THIỆU"),
                                                                         ("III. KẾT QUẢ", "IV. BÀN LUẬN")))
    so_ban_thao = {int(x.replace(".", "").replace(",", ""))
                   for x in re.findall(r"\b\d{1,3}(?:[.,]\d{3})+\b|\b\d+\b", noi)}
    ket = [_cham_mot_tom_tat(p, manifest, moc_khoa, so_ban_thao, out_dir) for p in ung_vien]
    for muc in ("BLOCK", "REVIEW"):
        xau = [k["evidence"] for k in ket if k["status"] == muc]
        if xau:
            return {"status": muc, "evidence": "; ".join(xau)}
    return {"status": "PASS", "evidence": "; ".join(k["evidence"] for k in ket)}


def evaluate_g7_quality(
    *,
    manuscript_text: str,
    checkpoints: Mapping[str, Mapping[str, Any]],
    meta: Mapping[str, Any],
    artifact_paths: Optional[Mapping[str, Path]] = None,
    citation_verification_ok: Optional[bool] = None,
    guardrail_passed: Optional[bool] = None,
    design_drift_warning: Any = _UNSET,
    tien_de: Optional[Mapping[str, Mapping[str, str]]] = None,
    ket_qua_g6: Optional[Mapping[str, str]] = None,
    citation_detail: str = "",
) -> Dict[str, Any]:
    """Chấm G7 theo hai tầng: máy kiểm được vs người thật phải chốt.

    `checkpoints` là dict {"G0": {...}, "G1": {...}, …, "G7": {...}}.
    `tien_de` (04/10/2026, G7-01): trạng thái SỐNG G0–G6 do evaluate_study tính (tien_de_song); vắng ⇒ «không đo được»
    — KHÔNG BAO GIỜ đạt. `ket_qua_g6` (G7-05): kết quả doi_chieu_ket_qua_g6; vắng ⇒ không đạt.
    """
    artifact_paths = artifact_paths or {}
    automatic: List[Dict[str, str]] = []
    human: List[Dict[str, str]] = []
    khong_do = {"status": "REVIEW", "evidence": "không đo được tiền đề (chấm qua evaluate_study)"}
    td = {g: dict((tien_de or {}).get(g) or khong_do) for g in ("G0", "G1", "G2", "G3", "G4", "G5", "G6")}

    g7cp = checkpoints.get("G7") or {}
    if guardrail_passed is None:
        guard = g7cp.get("guardrail")
        status_str = str((guard or {}).get("status", "")) if isinstance(guard, Mapping) else ""
        errs = (guard or {}).get("errors") if isinstance(guard, Mapping) else None
        guardrail_passed = bool(status_str) and not errs

    automatic.append(_criterion(
        "G7-AUTO-00", "Guardrail liêm chính G7 sạch",
        "PASS" if guardrail_passed else "BLOCK",
        f"guardrail_passed={guardrail_passed}",
        "Sửa lỗi guardrail rồi sinh lại bản thảo.",
    ))

    # ── Tiền đề cổng trước — CHẤM SỐNG (G7-01) ───────────────────────────────
    # G1 là tiền đề CỨNG: không có thiết kế thì chuẩn báo cáo bị chọn sai (run_g7_auto.py rơi về "cohort"/STROBE cho
    # mọi đề tài), kéo theo cả checklist phụ lục sai.
    automatic.append(_criterion(
        "G7-AUTO-01", "Thiết kế nghiên cứu G1 đã chốt (quyết định chuẩn báo cáo) — chấm sống",
        "BLOCK" if td["G1"]["status"] == "BLOCK" else td["G1"]["status"],
        td["G1"]["evidence"],
        "Chạy `python tools/run_g1_auto.py --study <mã>` và chốt G1; không có thiết kế đã chốt thì chuẩn báo cáo "
        "(CONSORT/STROBE/PRISMA…) sẽ bị chọn sai cho cả bản thảo.",
    ))

    # SỬA 2026-07-31 (audit tautology vòng 2, G7-AUTO-01b — reverse-tautology do stale cache): khi caller đã tính SỐNG
    # (evaluate_study() gọi GC.resolve_design_code() ngay lúc chấm), dùng giá trị đó thay vì tin cache.
    design_drift = (
        design_drift_warning if design_drift_warning is not _UNSET
        else g7cp.get("design_drift_warning")
    )
    automatic.append(_criterion(
        "G7-AUTO-01b", "Mã thiết kế KHÔNG lệch giữa G1 và G2",
        "BLOCK" if design_drift else "PASS",
        design_drift or "G1/G2 khớp thiết kế (hoặc chỉ một nơi có giá trị)",
        "G1 suy luận và G2 (nơi bác sĩ có thể truyền --design tường minh) lệch nhau — "
        "chạy lại G1/G2 cho khớp trước khi tin chuẩn báo cáo của bản thảo này. Xem "
        "gate_contract.py::resolve_design_code().",
    ))

    tien_de_0234 = {g: td[g] for g in ("G0", "G2", "G3", "G4")}
    chan = [g for g, v in tien_de_0234.items() if v["status"] == "BLOCK"]
    chua = [g for g, v in tien_de_0234.items() if v["status"] != "PASS"]
    automatic.append(_criterion(
        "G7-AUTO-02", "Đủ tiền đề G0/G2/G3/G4 (câu hỏi · đạo đức · cỡ mẫu · SAP) — chấm sống",
        "BLOCK" if chan else "REVIEW" if chua else "PASS",
        "; ".join(v["evidence"] for v in tien_de_0234.values()),
        "Bản thảo chỉ là KHUNG cho tới khi các cổng này PASS thật (G2 ký IRB, G4 ký SAP); đừng gửi đi.",
    ))

    # ── Kết quả thật (G7-05) ─────────────────────────────────────────────────
    results_final = meta.get("results_final") is True
    kq = dict(ket_qua_g6 or {"status": "REVIEW", "evidence": "chưa đối chiếu đầu ra G6 (chấm qua evaluate_study)"})
    g56_chan = [g for g in ("G5", "G6") if td[g]["status"] == "BLOCK"]
    g56_ok = all(td[g]["status"] == "PASS" for g in ("G5", "G6"))
    automatic.append(_criterion(
        "G7-AUTO-03", "Kết quả phân tích THẬT: G5 khoá + G6 xác nhận + đầu ra G6 sau khoá, N khớp bản thảo",
        "BLOCK" if (g56_chan or kq["status"] == "BLOCK") else
        "PASS" if (results_final and g56_ok and kq["status"] == "PASS") else "REVIEW",
        f"{td['G5']['evidence']}; {td['G6']['evidence']}; {kq['evidence']}; study_meta.results_final={results_final}",
        "Khóa dữ liệu (G5) → chạy phân tích (G6/run_stats_analysis.py) → điền số THẬT từ G6_analysis_summary.json → "
        "bác sĩ đặt results_final=true trong study_meta.json. Hệ KHÔNG tự bật cờ này.",
    ))

    # ── Artifact ─────────────────────────────────────────────────────────────
    # LƯU Ý PHẠM VI (audit tautology vòng 2, 2026-07-31): tiêu chí này CHỈ bắt xóa/cắt SAU KHI SINH, KHÔNG thẩm định
    # nội dung khoa học — việc đó thuộc G7-HUMAN-04 (đọc lại toàn văn) và G8 (bình duyệt độc lập).
    text = manuscript_text or ""
    missing_sections = [s for s in REQUIRED_A8_SECTIONS
                        if s.casefold() not in text.casefold()]
    if not text.strip():
        art_status, art_evidence = "BLOCK", "Không đọc được artifact A8"
    elif missing_sections:
        art_status = "BLOCK"
        art_evidence = f"A8 thiếu mục: {', '.join(missing_sections)}"
    else:
        art_status = "PASS"
        art_evidence = f"A8 đủ {len(REQUIRED_A8_SECTIONS)} mục IMRAD"
    automatic.append(_criterion(
        "G7-AUTO-04", "Artifact A8 có đủ cấu trúc IMRAD", art_status, art_evidence,
        "Sinh lại bản thảo bằng run_g7_auto.py.",
    ))

    # ── Ô còn trống — DÙNG CHUNG bộ quét của G8 (G7-06) ─────────────────────
    # Bản cũ chỉ đếm «[CẦN KẾT QUẢ THẬT]» ⇒ PASS khi còn [CẦN…] ngoài kết quả, «___», «[Tác giả] et al.», «[Năm]»,
    # «[TRÍCH DẪN CHƯA XÁC MINH]». Nay gọi CHÍNH g8_quality_gate.manuscript_residues (G8-AUTO-04) để hai cổng nói MỘT
    # chuyện về «bản thảo còn ô chưa soạn» — G7 REVIEW, G8 CHẶN.
    ph = count_placeholders(text)
    try:
        import g8_quality_gate as G8Q  # noqa: PLC0415 — import lười, tránh vòng import
        con_trong = G8Q.manuscript_residues(text)
        # Điều phối G7↔G8 (05/10/2026, lộ khi chạy chuỗi thật G7 PASS → G8): bản thảo G7 đã PASS vẫn bị G8-AUTO-04
        # CHẶN vì dòng chỉ dẫn «> • Dùng agent `kiem-chung-trich-dan`…» của khuôn — G7 chỉ quét ô trống, G8 quét cả
        # vệt công cụ nội bộ. Nay G7 dùng ĐỦ hai bộ quét của G8: G7 PASS ⇒ G8-AUTO-04 không còn gì để chặn.
        con_trong = con_trong + [f"vệt công cụ nội bộ: {v}" for v in G8Q.scan_internal_traces(text)]
    except ImportError:  # pragma: no cover - lưới an toàn
        con_trong = [f"{ph['total']} ô [CẦN…]"] if ph["total"] else []
    # Lỗi CẤU TRÚC đứng trước (bằng chứng chỉ hiện 3 dòng đầu).
    con_trong = [f"ô «[CẦN» KHÔNG đóng ngoặc: «{x}…»" for x in o_can_chua_dong(_chuan_hoa_chinh_ta(text))] + con_trong
    automatic.append(_criterion(
        "G7-AUTO-05", "Không còn ô trống / ô mẫu chưa soạn trong phần bản thảo gửi tạp chí",
        "PASS" if not con_trong and ph["results"] == 0 else "REVIEW",
        (f"còn {len(con_trong)} dòng chưa soạn: {' · '.join(con_trong[:3])}" if con_trong
         else "không còn ô trống/ô mẫu") + f"; [CẦN KẾT QUẢ THẬT]={ph['results']}",
        "Điền nội dung thật (kết quả, trích dẫn, tác giả/tạp chí/năm) — KHÔNG nộp khi còn ô này.",
    ))

    # ── Khẳng định trần về việc chưa làm (G7-02) ─────────────────────────────
    # Tín hiệu lấy từ NGUỒN THẨM QUYỀN (chấm sống G2/G4/G5) — bản cũ tin cờ meta trần (chuỗi «[CẦN NGÀY]» cũng bật).
    g2cp = checkpoints.get("G2") or {}
    g2_ok = td["G2"]["status"] == "PASS"
    mien_dong_thuan = g2cp.get("g2_icf_waiver_approved") is True
    signals = {
        "irb_approved": g2_ok,
        "registered": g2_ok and PC.co_noi_dung_that(g2cp.get("g2_registration")),
        "sap_locked": td["G4"]["status"] == "PASS",
        "db_locked": td["G5"]["status"] == "PASS",
        "consent": g2_ok and not mien_dong_thuan,
    }
    claims = find_unsupported_claims(text, signals)
    automatic.append(_criterion(
        "G7-AUTO-06", "Không khẳng định việc chưa có bằng chứng ở cổng trước",
        "BLOCK" if claims else "PASS",
        "; ".join(claims) if claims else "không thấy khẳng định trần",
        "Xoá hoặc đổi thành [CẦN…] cho tới khi việc đó xảy ra thật. Đây là loại sai "
        "phạm liêm chính bị tạp chí rút bài.",
    ))

    # ── Trích dẫn đã kiểm chứng (A12) — hàm CHUẨN của G10 (G7-07) ───────────
    if citation_verification_ok is None:
        cit_status, cit_evidence = "REVIEW", citation_detail or "chưa có artifact A12"
    elif citation_verification_ok:
        cit_status, cit_evidence = "PASS", citation_detail or "A12 đạt"
    else:
        cit_status, cit_evidence = "REVIEW", citation_detail or "A12 có nhưng chưa sạch"
    automatic.append(_criterion(
        "G7-AUTO-07", "Trích dẫn đã được kiểm chứng (A12)", cit_status, cit_evidence,
        "Chạy agent `kiem-chung-trich-dan` + tools/check_citation_retraction.py --study <mã>, ghi kết quả vào "
        "A12_CITATION_VERIFICATION_<study>.md — run_g10_assemble.py sẽ CHẶN nếu thiếu.",
    ))

    # ── Tầng HUMAN — giá trị phải là NỘI DUNG THẬT (G7-06) ──────────────────
    g7 = _g7_meta(meta)

    def _that(v: Any) -> bool:
        return isinstance(v, str) and PC.co_noi_dung_that(v)

    title_ok = _that(g7.get("title"))
    authors_ok = _that(g7.get("authors"))
    human.append(_criterion(
        "G7-HUMAN-01", "Tiêu đề và danh sách tác giả đã chốt",
        "PASS" if (title_ok and authors_ok) else "REVIEW",
        f"title={'có' if title_ok else 'thiếu/ô trống'}; authors={'có' if authors_ok else 'thiếu/ô trống'}",
        "Điền gate_params.G7.title và .authors (tên/đơn vị/ORCID) — chuỗi nội dung thật, không phải true/[TBD].",
    ))

    missing_decl = [label for key, label in ICMJE_DECLARATIONS if not _that(g7.get(key))]
    human.append(_criterion(
        "G7-HUMAN-02", "Đủ khai báo bắt buộc theo ICMJE",
        "PASS" if not missing_decl else "REVIEW",
        f"thiếu/ô trống: {', '.join(missing_decl)}" if missing_decl else "5/5 khai báo có nội dung",
        "Điền author_contributions · coi_declared · funding_declared · data_sharing_statement · ai_use_declared "
        "trong gate_params.G7 bằng câu khai báo thật (không phải true, «TBD», «[TÁC GIẢ ĐIỀN…]»).",
    ))

    journal_ok = _that(g7.get("target_journal"))
    human.append(_criterion(
        "G7-HUMAN-03", "Đã chọn tạp chí đích",
        "PASS" if journal_ok else "REVIEW",
        f"target_journal={g7.get('target_journal') or 'thiếu'}",
        "Điền target_journal; định dạng và giới hạn từ phụ thuộc tạp chí.",
    ))

    # G7-09: xác nhận «đã đọc lại toàn văn» gắn DẤU nội dung bản thảo — sửa bản thảo sau khi xác nhận ⇒ hết hiệu lực.
    import cong_song as CS  # noqa: PLC0415
    dau_ban_thao = CS.dau_van_tay(text.replace("\r\n", "\n"))
    read_ok = g7.get("manuscript_reviewed_confirmed") is True
    dau_khop = g7.get("dau_van_tay_chot") == dau_ban_thao
    human.append(_criterion(
        "G7-HUMAN-04", "Tác giả đã đọc lại TOÀN VĂN đúng bản thảo hiện tại",
        "PASS" if (read_ok and dau_khop) else "REVIEW",
        f"manuscript_reviewed_confirmed={read_ok}; dấu bản thảo hiện tại {dau_ban_thao}"
        + ("" if dau_khop else " — dau_van_tay_chot vắng hoặc KHÁC (bản thảo đã sửa sau khi xác nhận?)"),
        "Đọc lại toàn văn (đặc biệt Methods §7 đạo đức và Section III kết quả) rồi đặt "
        f"manuscript_reviewed_confirmed=true và dau_van_tay_chot=\"{dau_ban_thao}\". Bản nháp do công cụ sinh KHÔNG "
        "được gửi đi khi chưa có người đọc lại.",
    ))

    role = str(g7.get("reviewed_by_role") or "").strip().casefold()
    sign_ok = role in _REVIEW_ROLES and _valid_iso_time(g7.get("reviewed_at"))
    human.append(_criterion(
        "G7-HUMAN-05", "Có vai trò và thời điểm chốt bản thảo",
        "PASS" if sign_ok else "REVIEW",
        f"vai trò={role or 'thiếu'}; reviewed_at={g7.get('reviewed_at') or 'thiếu'}",
        "Ghi reviewed_by_role (PI/tác giả liên lạc) và reviewed_at dạng ISO-8601.",
    ))

    # ── Kết luận ─────────────────────────────────────────────────────────────
    auto_blocked = any(r["status"] == "BLOCK" for r in automatic)
    auto_review = any(r["status"] == "REVIEW" for r in automatic)
    human_complete = all(r["status"] == "PASS" for r in human)

    if auto_blocked:
        status = STATUS_BLOCKED
    elif auto_review or not human_complete:
        status = STATUS_DRAFT_READY
    else:
        status = STATUS_CONFIRMED

    pending = [r["action"] for r in automatic + human
               if r["status"] != "PASS" and r.get("action")]

    manifest: Dict[str, Dict[str, str]] = {}
    for key, path in artifact_paths.items():
        p = Path(path)
        if p.exists():
            manifest[key] = {"path": str(p),
                             "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}

    report: Dict[str, Any] = {
        "schema_version": "1.0",
        "contract_version": QUALITY_CONTRACT_VERSION,
        "status": status,
        "automated_checks_passed": not auto_blocked,
        "human_confirmation_complete": human_complete,
        "automatic_criteria": automatic,
        "human_criteria": human,
        "pending_actions": pending,
        "placeholder_counts": ph,
        "manuscript_residues": con_trong,
        "unsupported_claims": claims,
        "dau_ban_thao": dau_ban_thao,
        "artifact_manifest": manifest,
        "standards_basis": list(_STANDARDS_BASIS),
        "scope_statement": (
            "PASS_G7_CONFIRMED KHÔNG có nghĩa bản thảo tốt, đúng khoa học hay đáng "
            "đăng. Nó chỉ xác nhận: tiền đề G0–G6 PASS thật, kết quả G6 có thật và khớp N, không còn ô trống bắt "
            "buộc, không còn khẳng định về việc chưa làm, trích dẫn đã qua A12, và tác giả thật đã đọc lại ĐÚNG bản "
            "này và chốt khai báo ICMJE. Thẩm định khoa học là việc của G8 (bình duyệt độc lập) và của người bình "
            "duyệt tạp chí."
        ),
    }

    if status == STATUS_DRAFT_READY:
        report["needs_input"] = GC.needs_input(
            GC.REASON_MISSING_DATA if ph["results"] else GC.REASON_MISSING_INTEGRITY,
            (f"Bản thảo còn {ph['results']} ô [CẦN KẾT QUẢ THẬT]"
             if ph["results"] else
             "Bản thảo chưa đủ điều kiện (tiền đề/kết quả G6/ô trống/khai báo/đọc lại toàn văn)")
            + " — chưa được coi là sẵn sàng cho G8.",
            "sửa exports/<study>/study_meta.json → gate_params.G7 rồi chạy: "
            "python tools/g7_quality_gate.py --study <study>",
            must_not_fabricate=["kết quả thống kê", "số IRB", "số đăng ký",
                                "danh sách tác giả"],
            study_meta_patch={"gate_params": {"G7": {"manuscript_reviewed_confirmed": True,
                                                     "dau_van_tay_chot": dau_ban_thao}}},
        )
    return report


# ════════════════════════════════════════════════════════════════════════════
# Báo cáo
# ════════════════════════════════════════════════════════════════════════════

def write_quality_report(study: str, out_dir: Path,
                         report: Mapping[str, Any]) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "G7_QUALITY_REPORT.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    def _rows(key: str) -> List[str]:
        return [
            f"| {r['id']} | {r['label']} | {r['status']} | "
            f"{str(r['evidence']).replace('|', '/')} |"
            for r in report.get(key, [])
        ]

    ph = report.get("placeholder_counts") or {}
    lines = [
        f"# BÁO CÁO CHẤT LƯỢNG G7 (BẢN THẢO) — {study}",
        "",
        f"**Trạng thái:** `{report['status']}`  ·  "
        f"**Hợp đồng:** `{report.get('contract_version', '')}`",
        "",
        "> Báo cáo này chấm BẢN THẢO ĐANG CÓ TRÊN ĐĨA (kể cả phần bác sĩ đã viết tay),",
        "> không chấm bản do công cụ vừa sinh. `DRAFT_READY_NEEDS_HUMAN_REVIEW` là kết",
        "> quả ĐÚNG khi chưa có kết quả phân tích thật.",
        "",
        f"**Ô còn trống:** {ph.get('total', '?')} ô `[CẦN…]` — trong đó "
        f"{ph.get('results', '?')} ô `[CẦN KẾT QUẢ THẬT]` "
        f"(Methods {ph.get('methods', '?')} · Results {ph.get('results_section', '?')})",
        "",
        "## Kiểm tra tự động",
        "| Mã | Tiêu chí | Trạng thái | Bằng chứng |",
        "|---|---|---|---|",
        *_rows("automatic_criteria"),
        "",
        "## Xác nhận người thật",
        "| Mã | Tiêu chí | Trạng thái | Bằng chứng |",
        "|---|---|---|---|",
        *_rows("human_criteria"),
    ]

    claims = report.get("unsupported_claims") or []
    if claims:
        lines.extend(["", "## ⚠️ KHẲNG ĐỊNH CHƯA CÓ BẰNG CHỨNG (phải sửa trước khi nộp)"])
        lines.extend(f"- {c}" for c in claims)

    pending = report.get("pending_actions") or []
    if pending:
        lines.extend(["", "## Việc còn lại trước khi được ghi PASS_G7_CONFIRMED"])
        lines.extend(f"{i}. {a}" for i, a in enumerate(pending, 1))

    manifest = report.get("artifact_manifest") or {}
    if manifest:
        lines.extend(["", "## Manifest artifact",
                      "| Artifact | Đường dẫn | SHA-256 |", "|---|---|---|"])
        for key, item in manifest.items():
            lines.append(f"| {key} | {str(item['path']).replace('|', '/')} | "
                         f"`{item['sha256']}` |")

    lines.extend(["", "## Nền chuẩn", "| Chuẩn | Phạm vi | Nguồn |", "|---|---|---|"])
    for item in report.get("standards_basis", []):
        lines.append(f"| {item['standard']} | {item['scope']} | {item.get('url', '')} |")

    lines.extend(["", "## Giới hạn phán định",
                  str(report.get("scope_statement") or ""),
                  "", "> Cần bác sĩ kiểm chứng."])

    md_path = out_dir / "G7_QUALITY_REPORT.md"
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return md_path


def evaluate_study(study: str, out_dir: Path, *, write: bool = True,
                   repo_root: Optional[Path] = None) -> Dict[str, Any]:
    """Chấm lại G7 từ các file đã có — KHÔNG sinh lại bản thảo.

    Quan trọng: đọc artifact A8 TỪ ĐĨA, nên nếu bác sĩ đã viết tay vào đó, báo cáo
    này phản ánh đúng bản hiện tại chứ không phải bản khung ban đầu.
    `repo_root` (04/10/2026): gốc chứa exports/ để chấm sống tiền đề/tra sổ cái — mặc định suy từ out_dir.
    """
    out_dir = Path(out_dir)
    root = _goc_repo(out_dir, repo_root)
    checkpoints = {g: _read_json(out_dir / f"{g}_checkpoint.json")
                   for g in ("G0", "G1", "G2", "G3", "G4", "G5", "G6", "G7")}
    meta = _read_json(out_dir / "study_meta.json")

    # VÁ 04/10/2026 (soát từng cổng, G7-13): chỉ ĐÚNG tệp của đề tài — bản cũ dò glob «G7_A8_MANUSCRIPT_*.md» khi vắng
    # và có thể chấm nhầm bản sao lưu .bak cũ. Vắng ⇒ text rỗng ⇒ G7-AUTO-04 CHẶN.
    md_path = out_dir / f"G7_A8_MANUSCRIPT_{study}.md"
    try:
        text = md_path.read_text(encoding="utf-8")
    except OSError:
        text = ""

    # G7-07: kiểm A12 bằng hàm CHUẨN của G10 (receipt rút bài máy-ghi, không chỉ dòng chữ agent tự gõ) — bản cũ nhận
    # cả A12 mang dòng kết luận THẤT BẠI chính thức.
    citation_ok: Optional[bool]
    if (out_dir / f"A12_CITATION_VERIFICATION_{study}.md").exists():
        try:
            import run_g10_assemble as G10  # noqa: PLC0415 — import lười
            citation_ok, citation_detail = G10.citation_verification_ok(study, out_dir, kiem_ban_g10=False)
        except Exception as exc:  # noqa: BLE001 — không đo được ≠ sạch
            citation_ok, citation_detail = False, f"không chấm được A12: {type(exc).__name__}"
    else:
        citation_ok, citation_detail = None, "chưa có artifact A12"

    # G7-01/G7-05: tiền đề và kết quả G6 tính SỐNG.
    tien_de = tien_de_song(study, out_dir, repo_root=root)
    ket_qua_g6 = doi_chieu_ket_qua_g6(study, out_dir, text, repo_root=root)

    # SỬA 2026-07-30 (audit toàn diện G0-G10, G7-F1 — HIGH, FABRICATION_RISK): chạy lại guardrail_g7() TRÊN CHÍNH `text`
    # vừa đọc, không tin cache. VÁ 04/10/2026 (G7-08): guardrail biết số đăng ký THẬT của G2 đã duyệt (R2 không còn coi
    # mọi NCT là bịa) và khi nào kết quả đã THẬT (R5 hạ xuống cảnh báo).
    g2cp = checkpoints.get("G2") or {}
    dang_ky_g2 = g2cp.get("g2_registration") if tien_de["G2"]["status"] == "PASS" else None
    ket_qua_that = (meta.get("results_final") is True and ket_qua_g6.get("status") == "PASS"
                    and all(tien_de[g]["status"] == "PASS" for g in ("G5", "G6")))
    try:
        import run_g7_auto as G7  # noqa: PLC0415
        fresh_errors, _fresh_warnings = G7.guardrail_g7(text, dang_ky_g2=dang_ky_g2, ket_qua_that=ket_qua_that)
        guardrail_passed = not fresh_errors
    except ImportError:  # pragma: no cover - lưới an toàn
        guardrail_passed = None

    # SỬA 2026-07-31 (G7-AUTO-01b): tính SỐNG thay vì tin g7cp["design_drift_warning"] đóng băng.
    try:
        _dc_live, design_drift_warning = GC.resolve_design_code(out_dir)
    except Exception:  # pragma: no cover - lưới an toàn
        design_drift_warning = None

    report = evaluate_g7_quality(
        manuscript_text=text,
        checkpoints=checkpoints,
        meta=meta,
        artifact_paths={"A8": md_path} if md_path.exists() else {},
        citation_verification_ok=citation_ok,
        guardrail_passed=guardrail_passed,
        design_drift_warning=design_drift_warning,
        tien_de=tien_de,
        ket_qua_g6=ket_qua_g6,
        citation_detail=citation_detail,
    )
    if write:
        write_quality_report(study, out_dir, report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Chấm lại cổng G7 từ bản thảo + checkpoint đã có (không sinh lại bản thảo)."
    )
    parser.add_argument("--study", required=True, help="Mã đề tài")
    parser.add_argument("--exports-dir", default=None,
                        help="Thư mục gốc exports (mặc định: <repo>/exports)")
    parser.add_argument("--no-write", action="store_true", help="Chỉ in, không ghi báo cáo")
    args = parser.parse_args()
    GC.ensure_utf8_stdout()

    base = Path(args.exports_dir) if args.exports_dir else (
        Path(__file__).resolve().parent.parent / "exports")
    out_dir = base / args.study
    if not out_dir.exists():
        print(f"🚧 Không thấy thư mục đề tài: {out_dir}")
        return GC.EXIT_BLOCKED

    report = evaluate_study(args.study, out_dir, write=not args.no_write)

    print(f"\n{'='*68}")
    print(f"  CHẤT LƯỢNG G7 (BẢN THẢO) — {args.study}")
    print(f"{'='*68}")
    for row in report["automatic_criteria"] + report["human_criteria"]:
        icon = {"PASS": "✅", "REVIEW": "🟡", "BLOCK": "🔴"}.get(row["status"], "•")
        print(f"  {icon} {row['id']}  {row['label']}")
        print(f"       {row['evidence']}")
    ph = report["placeholder_counts"]
    print(f"\n  📝 Ô còn trống: {ph['total']} tổng · {ph['results']} [CẦN KẾT QUẢ THẬT]")
    if report["unsupported_claims"]:
        print("\n  ⚠️  KHẲNG ĐỊNH CHƯA CÓ BẰNG CHỨNG:")
        for c in report["unsupported_claims"]:
            print(f"     • {c}")
    print(f"\n  → Trạng thái: {report['status']}")
    if report["pending_actions"]:
        print("\n  VIỆC CÒN LẠI TRƯỚC KHI ĐƯỢC GHI PASS_G7_CONFIRMED:")
        for i, action in enumerate(report["pending_actions"], 1):
            print(f"  {i}. {action}")
    print("\n  Cần bác sĩ kiểm chứng.")
    print(f"{'='*68}\n")

    if report["status"] == STATUS_BLOCKED:
        return GC.EXIT_GUARDRAIL_FAIL
    if report["status"] == STATUS_DRAFT_READY:
        return GC.EXIT_BLOCKED
    return GC.EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
