#!/usr/bin/env python3
"""
run_g9_auto.py — TỰ ĐỘNG HÓA CỔNG G9: Liêm chính Tác giả (Author Integrity)

Cổng cứng cuối cùng trước khi nộp bản thảo ra bên ngoài.
Đọc tất cả checkpoints G0-G8 -> sinh GÓI LIÊM CHÍNH TÁC GIẢ (A10) gồm 8 phần:
  Phần 1 — ICMJE Tiêu chuẩn Tác giả (4 tiêu chí, từng tác giả)
  Phần 2 — Khai báo quan hệ/hoạt động và xung đột lợi ích
  Phần 3 — Data Availability Statement
  Phần 4 — AI Use Disclosure theo ICMJE 2026
  Phần 5 — Tuyên bố Liêm chính Nghiên cứu
  Phần 6 — Thư gửi Tạp chí (Cover Letter Shell)
  Phần 7 — Bản mẫu Phản hồi Phản biện (Response-to-Reviewers Template)
  Phần 8 — Tiêu chí qua Cổng G9 (Hard Gate — cần ký)

Bác sĩ / PI phải ký TOÀN BỘ trước khi nộp bài.
KHÔNG CÓ gói này -> KHÔNG nộp bản thảo.

Sử dụng:
    python tools/run_g9_auto.py --study "MA-DE-TAI"
    python tools/run_g9_auto.py --study "SGLT2-HFpEF-2026" --n-authors 3 --target-journal "JACC"
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# ── Cấu hình đường dẫn ──────────────────────────────────────────────────────
_REPO_ROOT = Path(__file__).resolve().parent.parent
_TOOLS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_REPO_ROOT))
sys.path.insert(0, str(_TOOLS_DIR))

import g9_quality_gate as G9Q  # noqa: E402
import gate_contract as GC  # noqa: E402  (hợp đồng DỪNG dùng chung — chỉ dùng load_study_meta)


def _ledger_approved(study: str, gate_id: str, artifact_path: Path) -> bool:
    """Audit 2026-07-11: G9 là cổng cứng CUỐI CÙNG trước nộp bài nhưng trước đây
    KHÔNG có xác minh mật mã ledger nào — ethics_locked/sap_locked chỉ kiểm
    checkpoint text tự do (g2_irb_number/sap_signed_date không placeholder), y hệt
    lỗ hổng đã vá ở run_stats_analysis.py/run_g6_auto.py (BL-06, 2026-07-08/09).

    Vá 2026-07-12 (audit toàn diện cổng G0-G9): trước đây hàm này TỰ CÓ một bản
    sao của cùng logic hash+not-synthetic+not-agent (1 trong 5 bản sao gần-giống-
    nhau rải khắp hệ thống — sửa 1 nơi từng quên 3 nơi khác). Nay ủy quyền cho
    gate_contract.ledger_approved() — nơi DUY NHẤT còn giữ logic này, đồng thời
    có thêm xác minh CHỮ KÝ actor thật (HMAC, xem gate_contract.py) nếu máy đã
    thiết lập khóa ký."""
    return GC.ledger_approved(gate_id, study, artifact_path, repo_root=_REPO_ROOT)

_TODAY = datetime.now().strftime("%d/%m/%Y")
_YEAR  = datetime.now().strftime("%Y")


# ════════════════════════════════════════════════════════════════════════════
# 1. ĐỌC CHECKPOINT (hàm dùng chung)
# ════════════════════════════════════════════════════════════════════════════


def load_cp(path: Path) -> dict:
    """
    Đọc file checkpoint JSON; trả về dict rỗng nếu không tồn tại.
    SỬA: JSON hợp lệ nhưng không phải object (vd literal "null"/mảng) từng
    khiến hàm trả về None/list thay vì dict — các nơi gọi .get() ở downstream
    sẽ crash AttributeError. Đồng bộ với guard đã có ở run_g8_auto.py.
    """
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
        return data if isinstance(data, dict) else {}
    return {}


def collect_all_checkpoints(out_dir: Path) -> dict:
    """Đọc tất cả checkpoints G0-G8 từ thư mục xuất."""
    gate_files = {
        "G0": "G0_checkpoint.json",
        "G1": "G1_checkpoint.json",
        "G2": "G2_checkpoint.json",
        "G3": "G3_checkpoint.json",
        "G4": "G4_checkpoint.json",
        "G5": "G5_checkpoint.json",
        "G6": "G6_checkpoint.json",
        "G7": "G7_checkpoint.json",
        "G8": "G8_checkpoint.json",
    }
    result = {}
    for gate, fname in gate_files.items():
        data = load_cp(out_dir / fname)
        if data:
            result[gate] = data
    return result


# ════════════════════════════════════════════════════════════════════════════
# 2. SINH PHẦN 1 — ICMJE TIÊU CHUẨN TÁC GIẢ
# ════════════════════════════════════════════════════════════════════════════

def build_part1_icmje(n_authors: int, study: str) -> str:
    """
    Sinh bảng ICMJE 4 tiêu chí tác giả cho từng tác giả.
    Cả 4 tiêu chí đều phải được đánh dấu ĐỦ mới đủ tư cách tác giả.
    """
    lines = [
        "## PHẦN 1 — TIÊU CHUẨN TÁC GIẢ ICMJE (CẢ 4 TIÊU CHÍ)",
        "",
        "> **Căn cứ:** ICMJE Recommendations for Conduct, Reporting, Editing, and Publication",
        "> of Scholarly Work in Medical Journals (updated January 2026).",
        "> Tất cả 4 tiêu chí phải đạt ĐỦ mới là Tác giả.",
        "> CRediT mô tả vai trò đóng góp nhưng không thay thế 4 tiêu chí ICMJE.",
        "> Đóng góp chỉ đáp ứng 1-2 tiêu chí -> ghi trong Lời cảm ơn (Acknowledgment).",
        "> ICMJE 01/2026: mọi tác giả phải có khả năng rà dữ liệu hỗ trợ kết quả;",
        "> ít nhất một tác giả phải truy cập dữ liệu gốc và tham gia phân tích.",
        "",
        "### Bảng Tiêu chuẩn Tác giả ICMJE",
        "",
        "| Tiêu chí | Mô tả | " + " | ".join(f"Tác giả {i}" for i in range(1, n_authors + 1)) + " |",
        "|----------|-------|" + "---------|" * n_authors,
    ]

    # 4 tiêu chí ICMJE chuẩn
    tieu_chi = [
        ("TC1",
         "Đóng góp đáng kể vào ÍT NHẤT MỘT trong: Xây dựng ý tưởng/thiết kế "
         "HOẶC Thu thập dữ liệu HOẶC Phân tích/giải thích dữ liệu"),
        ("TC2",
         "Tham gia soạn thảo bản thảo HOẶC sửa chữa nội dung quan trọng về mặt trí tuệ"),
        ("TC3",
         "Phê duyệt phiên bản cuối để nộp xuất bản"),
        ("TC4",
         "Đồng ý chịu trách nhiệm về mọi khía cạnh của bài báo (đảm bảo điều tra "
         "và giải quyết mọi câu hỏi về tính chính xác/trung thực của mọi phần)"),
    ]

    for code, mo_ta in tieu_chi:
        o = " | ".join("☐ Có  ☐ Không" for _ in range(n_authors))
        lines.append(f"| **{code}** | {mo_ta} | {o} |")

    lines += ["", "### Kết luận Tư cách và Chữ ký Từng Tác giả", ""]

    for i in range(1, n_authors + 1):
        lines += [
            f"**Tác giả {i} — [CẦN ĐIỀN HỌ TÊN ĐẦY ĐỦ + ĐƠN VỊ + EMAIL]:**",
            "- Đóng góp cụ thể (CRediT): [CẦN — ví dụ: Conceptualization, "
            "Methodology, Writing – original draft]",
            "- Tư cách tác giả: ☐ ĐỦ CẢ 4 tiêu chí -> LÀ TÁC GIẢ  "
            "☐ Không đủ -> ghi Acknowledgment",
            "- Có khả năng rà dữ liệu hỗ trợ kết quả: ☐ Có  ☐ Không",
            f"- Chữ ký xác nhận: _______________  Ngày: ___/___/{_YEAR}",
            "",
        ]

    # Bảng CRediT taxonomy (14 vai trò)
    lines += [
        "### Bảng Đóng góp CRediT (Contributor Roles Taxonomy — 14 vai trò)",
        "",
        "| Vai trò CRediT | " + " | ".join(f"Tác giả {i}" for i in range(1, n_authors + 1)) + " |",
        "|----------------|" + "---------|" * n_authors,
    ]

    credit_roles = [
        "Conceptualization", "Data curation", "Formal analysis",
        "Funding acquisition", "Investigation", "Methodology",
        "Project administration", "Resources", "Software",
        "Supervision", "Validation", "Visualization",
        "Writing – original draft", "Writing – review & editing",
    ]
    for role in credit_roles:
        row = " | ".join("☐" for _ in range(n_authors))
        lines.append(f"| {role} | {row} |")

    lines += [
        "",
        "### Xác nhận quyền truy cập dữ liệu và độc lập công bố",
        "",
        "- Author ref đã truy cập dữ liệu gốc và tham gia phân tích: [CẦN — AUTHOR-__]",
        "- Nếu hợp tác học thuật/ngoài học thuật: tác giả trên thuộc đơn vị học thuật: ☐ Có ☐ Không áp dụng",
        "- Nghiên cứu có nhà tài trợ: ☐ Có ☐ Không",
        "- Nếu có: hợp đồng bảo toàn quyền truy cập dữ liệu và độc lập công bố: ☐ Có ☐ Không",
        "- Mã tham chiếu hợp đồng/xác nhận (không PII): [CẦN — EVIDENCE-REF]",
        "",
        f"*[DRAFT — Cần tất cả {n_authors} tác giả ký xác nhận trước khi nộp bài.]*",
        "",
        "---",
        "",
    ]
    return "\n".join(lines)


# ════════════════════════════════════════════════════════════════════════════
# 3. SINH PHẦN 2 — KHAI BÁO XUNG ĐỘT LỢI ÍCH CUỐI (FINAL COI)
# ════════════════════════════════════════════════════════════════════════════

def build_part2_coi(n_authors: int, study: str) -> str:
    """
    Sinh checklist chuẩn bị khai báo cho từng tác giả + tuyên bố tập thể.
    Tác giả vẫn phải dùng form ICMJE hiện hành của tạp chí tại ngày nộp.
    """
    lines = [
        "## PHẦN 2 — KHAI BÁO XUNG ĐỘT LỢI ÍCH CUỐI (FINAL COI DECLARATION)",
        "",
        "> **Căn cứ:** ICMJE Disclosure Form hiện hành (kiểm lại tại ngày nộp).",
        "> Hỗ trợ cho chính bản thảo phải khai không giới hạn thời gian; các quan hệ/hoạt động",
        "> khác thường được khai trong 36 tháng trước khi nộp. Mỗi tác giả điền riêng.",
        "> Đây chỉ là checklist chuẩn bị, không thay thế form chính thức của tạp chí.",
        "",
        "### A. MẪU KHAI BÁO TỪNG TÁC GIẢ (điền riêng cho mỗi người)",
        "",
    ]

    for i in range(1, n_authors + 1):
        lines += [
            "```",
            "═══════════════════════════════════════════════════════════════",
            f"ICMJE COI DECLARATION — Tác giả {i}",
            f"Đề tài: {study} | Ngày khai báo: {_TODAY}",
            "═══════════════════════════════════════════════════════════════",
            "",
            "Họ tên tác giả: [CẦN ĐIỀN]",
            "Đơn vị: [CẦN ĐIỀN]",
            "Mã tác giả nội bộ (không PII): [CẦN ĐIỀN]",
            "ORCID/tên/email chỉ điền trong hệ thống nộp bài được kiểm soát, không lưu tại đây.",
            "",
            "I. HỖ TRỢ CHO CHÍNH BẢN THẢO (không giới hạn thời gian)",
            "",
            "1. Tài trợ, vật tư, hỗ trợ viết/phân tích, phí xử lý bài hoặc hỗ trợ khác:",
            "   ☐ Không có",
            "   ☐ Có -> Tổ chức/loại hỗ trợ/đơn vị nhận: ___",
            "",
            "II. QUAN HỆ/HOẠT ĐỘNG TRONG 36 THÁNG QUA",
            "",
            "2. Grants/contracts; 3. Royalties/licenses; 4. Consulting fees;",
            "5. Honoraria; 6. Expert testimony; 7. Travel/meeting support;",
            "8. Patents planned/pending/issued; 9. Data Safety Monitoring Board/advisory board;",
            "10. Leadership/fiduciary role; 11. Stock/stock options;",
            "12. Equipment/materials/drugs/writing/gifts/services; 13. Other interests.",
            "",
            "Khai từng mục trên trong form chính thức:",
            "   ☐ Không có",
            "   ☐ Có -> Mục số: ___ | Tổ chức | Bản chất quan hệ | Đơn vị nhận: ___",
            "   Lưu ý: royalties/licenses có thể gồm bản quyền (copyright) hoặc nội dung",
            "   đã cấp phép (licensed); khai theo câu hỏi thực tế của form hiện hành.",
            "",
            "Tôi tuyên bố các thông tin trên là đầy đủ và chính xác.",
            "",
            "Chữ ký: _______________",
            f"Ngày: ___/___/{_YEAR}",
            "═══════════════════════════════════════════════════════════════",
            "```",
            "",
        ]

    lines += [
        "### B. TUYÊN BỐ TẬP THỂ (COLLECTIVE COI STATEMENT)",
        "",
        "*(Điền vào bản thảo, mục Declarations/Conflicts of Interest)*",
        "",
        "```",
        "CONFLICTS OF INTEREST",
        "─────────────────────────────────────────────────────",
        "[CẦN CHỌN MỘT TRONG HAI]",
        "",
        "Option A (Không có COI):",
        "  'The authors declare that they have no known competing financial",
        "   interests or personal relationships that could have appeared to",
        "   influence the work reported in this paper.'",
        "",
        "Option B (Có COI phải khai báo):",
        "  '[Tên tác giả] reports [loại COI] from [tổ chức], outside the",
        "   submitted work. All other authors declare no conflicts of interest.'",
        "─────────────────────────────────────────────────────",
        "```",
        "",
        f"*[DRAFT — Cần tất cả {n_authors} tác giả ký form ICMJE gốc riêng.]*",
        "",
        "---",
        "",
    ]
    return "\n".join(lines)


# ════════════════════════════════════════════════════════════════════════════
# 4. SINH PHẦN 3 — DATA AVAILABILITY STATEMENT
# ════════════════════════════════════════════════════════════════════════════

def build_part3_data_availability(cps: dict, study: str) -> str:
    """
    Sinh 3 lựa chọn Data Availability theo FAIR, ICMJE và yêu cầu bảo mật áp dụng.
    Bác sĩ chọn một trong ba và điền thông tin còn thiếu.
    """
    # Lấy số IRB từ G2 để điền vào template
    g2 = cps.get("G2", {})
    irb_number = g2.get("g2_irb_number") or "[CẦN SỐ IRB]"

    lines = [
        "## PHẦN 3 — DATA AVAILABILITY STATEMENT",
        "",
        "> **Căn cứ:** FAIR Data Principles; ICMJE Clinical Trials and Data Sharing;",
        "> điều kiện IRB/IEC và pháp luật bảo vệ dữ liệu áp dụng tại thời điểm nộp.",
        "",
        "> **[CẦN BÁC SĨ CHỌN MỘT TRONG BA LỰA CHỌN VÀ XÓA HAI LỰA CHỌN CÒN LẠI]**",
        "",
        "### ☐ Lựa chọn A — Chia sẻ theo yêu cầu (RECOMMENDED khi có dữ liệu cá nhân)",
        "",
        "```",
        "DATA AVAILABILITY STATEMENT — Option A",
        "─────────────────────────────────────────",
        "The data that support the findings of this study are available from",
        "the corresponding author upon reasonable request. Data are not publicly",
        "available due to privacy/ethical restrictions as specified in the ethics",
        f"approval (Approval No. {irb_number}).",
        "Requests for data access: [CẦN — Tên tác giả liên lạc | Email]",
        "─────────────────────────────────────────",
        "```",
        "",
        "### ☐ Lựa chọn B — Dữ liệu đã lưu kho mở (khi dữ liệu ẩn danh hóa được)",
        "",
        "```",
        "DATA AVAILABILITY STATEMENT — Option B",
        "─────────────────────────────────────────",
        "The data that support the findings of this study are openly available in",
        "[CẦN — OSF / Zenodo / Dryad / Figshare] at [CẦN URL]",
        "under DOI [CẦN DOI]. Dataset deposited: [CẦN NGÀY]",
        "─────────────────────────────────────────",
        "```",
        "",
        "### ☐ Lựa chọn C — Không thể chia sẻ (khi pháp luật không cho phép)",
        "",
        "```",
        "DATA AVAILABILITY STATEMENT — Option C",
        "─────────────────────────────────────────",
        "The data that support the findings of this study are not publicly available",
        "due to applicable legal, consent, privacy, and ethics approval restrictions.",
        "Further inquiries can be directed to the corresponding author.",
        "─────────────────────────────────────────",
        "```",
        "",
        "**[CẦN BÁC SĨ XÁC NHẬN lựa chọn trước khi nộp bài]**",
        "",
        "### Phụ lục bắt buộc nếu là thử nghiệm lâm sàng",
        "",
        "Theo yêu cầu ICMJE, tuyên bố phải nêu: có chia sẻ hay không; dữ liệu cá thể nào",
        "được chia sẻ và có khử định danh; tài liệu liên quan (protocol/SAP/code); thời điểm",
        "bắt đầu; thời hạn; tiêu chí và cơ chế truy cập. Nội dung phải nhất quán với đăng ký.",
        "",
        "- Dữ liệu sẽ chia sẻ: [CẦN]",
        "- Tài liệu liên quan: [CẦN]",
        "- Bắt đầu/thời hạn: [CẦN]",
        "- Tiêu chí truy cập/cơ chế xét duyệt/repository: [CẦN]",
        "- Đã đối chiếu registry: ☐ Chưa  ☐ Đã đối chiếu",
        "",
        "---",
        "",
    ]
    return "\n".join(lines)


# ════════════════════════════════════════════════════════════════════════════
# 5. SINH PHẦN 4 — AI USE DISCLOSURE
# ════════════════════════════════════════════════════════════════════════════

def build_part4_ai_disclosure(cps: dict, study: str) -> str:
    """Sinh form khai báo AI fail-closed; không tự suy công cụ hay mục đích."""
    gate_descriptions = {
        "G0": "G0 literature/research-question assistance",
        "G1": "G1 protocol/design assistance",
        "G2": "G2 ethics-document drafting assistance",
        "G3": "G3 sample-size scripting assistance",
        "G4": "G4 SAP drafting assistance",
        "G5": "G5 data-management tooling assistance",
        "G6": "G6 analysis-code assistance",
        "G7": "G7 manuscript-drafting assistance",
        "G8": "G8 presubmission-review assistance",
    }
    possible_uses = [f"  ☐ {desc}" for gate, desc in gate_descriptions.items() if gate in cps]
    if not possible_uses:
        possible_uses = ["  ☐ [CẦN XÁC NHẬN các công việc có AI hỗ trợ]"]

    lines = [
        "## PHẦN 4 — KHAI BÁO SỬ DỤNG AI (ICMJE Mục V, cập nhật 01/2026)",
        "",
        "> ICMJE yêu cầu công khai AI trong cover letter và đúng mục của bản thảo;",
        "> tác giả con người phải kiểm nội dung, chịu trách nhiệm và bảo vệ dữ liệu bí mật.",
        "> Việc có checkpoint chỉ cho biết công cụ đã chạy, không chứng minh AI thực sự",
        "> được dùng cho mục đích nào. Tác giả phải xác nhận từng dòng bên dưới.",
        "",
        "### Hồ sơ xác nhận",
        "",
        "```",
        f"AI USE DISCLOSURE — {study}",
        f"Date: {_TODAY}",
        "─────────────────────────────────────────────────────────────",
        "AI used: ☐ No  ☐ Yes",
        "Tool/provider/model/version/date accessed: [CẦN XÁC NHẬN]",
        "Possible EBM Copilot-assisted stages (tick only after human verification):",
        *possible_uses,
        "Other tools/purposes: [CẦN XÁC NHẬN]",
        "Human reviewer reference (no PII): [CẦN XÁC NHẬN]",
        "☐ Every AI-assisted statement/citation/calculation was independently checked.",
        "☐ No confidential, identifiable participant or unpublished restricted data was uploaded.",
        "☐ AI is not listed as an author; human authors accept full responsibility.",
        "☐ The manuscript statement and cover-letter statement match actual use.",
        "─────────────────────────────────────────────────────────────",
        "```",
        "",
        "### Mẫu soạn sau khi xác nhận thực tế",
        "",
        "```",
        "During preparation of this work, the authors used [TOOL, PROVIDER, VERSION]",
        "for [PURPOSE AND SECTION]. The authors independently reviewed and verified",
        "the output, made all scientific decisions, and accept full responsibility.",
        "```",
        "",
        "---",
        "",
    ]
    return "\n".join(lines)


# ════════════════════════════════════════════════════════════════════════════
# 6. SINH PHẦN 5 — TUYÊN BỐ LIÊM CHÍNH NGHIÊN CỨU
# ════════════════════════════════════════════════════════════════════════════

def build_part5_integrity(cps: dict, study: str) -> str:
    """
    Sinh tuyên bố liêm chính: không đạo văn, không chia nhỏ bài,
    không nộp song song, không fabrication/falsification, không HARKing.
    Tự điền ngày SAP lock từ G4, số IRB từ G2.
    """
    g4 = cps.get("G4", {})
    g2 = cps.get("G2", {})

    sap_lock_date = g4.get("g4_lock_date") or "[CẦN — ngày ký SAP Lock Certificate tại G4]"
    irb_number    = g2.get("g2_irb_number") or "[CẦN SỐ IRB]"
    irb_date      = g2.get("g2_approval_date") or "[CẦN NGÀY PHÊ DUYỆT]"
    registration  = g2.get("g2_registration") or "[CẦN SỐ ĐĂNG KÝ ClinicalTrials.gov/PROSPERO]"

    lines = [
        "## PHẦN 5 — TUYÊN BỐ LIÊM CHÍNH NGHIÊN CỨU",
        "",
        "> **Căn cứ:** Committee on Publication Ethics (COPE); Singapore Statement on",
        "> Research Integrity (2010); Bộ Y tế VN — Quy tắc đạo đức nghiên cứu.",
        "",
        "```",
        "TUYÊN BỐ LIÊM CHÍNH NGHIÊN CỨU",
        f"Đề tài: {study} | Ngày: {_TODAY}",
        "═══════════════════════════════════════════════════════════════",
        "",
        "1. KIỂM TRA ĐẠO VĂN (PLAGIARISM CHECK)",
        "   Tuyên bố: Bài báo này là sáng tạo gốc của nhóm tác giả.",
        "   Không sao chép không trích dẫn từ bất kỳ nguồn nào.",
        "   Công cụ kiểm tra: [CẦN — iThenticate / Turnitin / CrossCheck]",
        "   Tỷ lệ similarity: [CẦN — ghi kết quả, không tự đồng nhất với đạo văn]",
        "   Tiêu chí của tạp chí/cơ sở và kết luận rà soát con người: [CẦN]",
        "   Ngày kiểm tra: [CẦN]",
        "   ☐ Đã kiểm từng đoạn/nguồn và xử lý trùng lặp không phù hợp",
        "",
        "2. KHÔNG CHIA NHỎ BÀI (NO SALAMI SLICING)",
        f"   Tuyên bố: Đây là báo cáo ĐẦY ĐỦ và DUY NHẤT của tập dữ liệu {study}.",
        "   ☐ Không chia tách một nghiên cứu thành nhiều bài báo nhỏ",
        "   [CẦN BÁC SĨ XÁC NHẬN: ☐ Đây là báo cáo duy nhất từ tập dữ liệu này]",
        "   Nếu có ấn phẩm liên quan: [CẦN — Tên | DOI | Mối liên hệ]",
        "",
        "3. KHÔNG NỘP SONG SONG (NO DUPLICATE SUBMISSION)",
        "   Tuyên bố: Bài báo này CHƯA được nộp đồng thời cho tạp chí nào khác.",
        "   ☐ Xác nhận không nộp song song",
        "   Preprint (nếu đã đăng): [CẦN — server/DOI] hoặc ☐ Không có preprint",
        "",
        "4. KHÔNG GIẢ MẠO/BỊA ĐẶT (NO FABRICATION/FALSIFICATION)",
        "   Tuyên bố: Mọi dữ liệu và kết quả từ dữ liệu THẬT đã thu thập.",
        "   ☐ Mọi số liệu từ dữ liệu thật đã khóa DB",
        f"   Dữ liệu gốc: Khóa tại {irb_number} (phê duyệt: {irb_date})",
        "   Lưu trữ: [CẦN — nơi lưu dataset gốc]",
        "",
        "5. KHÔNG HARKING (NO HYPOTHESIZING AFTER RESULTS KNOWN)",
        "   Tuyên bố: Câu hỏi nghiên cứu và giả thuyết đặt ra TRƯỚC khi phân tích dữ liệu.",
        f"   SAP Lock Date: {sap_lock_date}",
        f"   Số đăng ký nghiên cứu: {registration}",
        "   ☐ Giả thuyết tiền nghiệm — SAP khóa trước khi xem dữ liệu",
        "",
        "6. PHÂN TÍCH HẬU KỲ (nếu có)",
        "   ☐ Không có phân tích hậu kỳ (post-hoc) ngoài SAP",
        "   ☐ Có -> [CẦN — tên phân tích | lý do | ghi nhãn post-hoc rõ trong bản thảo]",
        "",
        "CHỮ KÝ XÁC NHẬN LIÊM CHÍNH:",
        f"PI / Chủ nhiệm đề tài: _______________  Ngày: ___/___/{_YEAR}",
        f"Tác giả liên lạc: _______________  Ngày: ___/___/{_YEAR}",
        "",
        "[DRAFT — Tất cả tác giả phải ký xác nhận liêm chính trước khi nộp.]",
        "═══════════════════════════════════════════════════════════════",
        "```",
        "",
        "---",
        "",
    ]
    return "\n".join(lines)


# ════════════════════════════════════════════════════════════════════════════
# 7. SINH PHẦN 6 — THƯ GỬI TẠP CHÍ (COVER LETTER SHELL)
# ════════════════════════════════════════════════════════════════════════════

def build_part6_cover_letter(cps: dict, study: str, target_journal: str) -> str:
    """
    Sinh thư gửi tạp chí chuyên nghiệp.
    Tự điền từ checkpoints: topic, design, reporting_std, registration, IRB, research gaps.
    """
    g0 = cps.get("G0", {})
    g1 = cps.get("G1", {})
    g2 = cps.get("G2", {})
    g3 = cps.get("G3", {})

    # SỬA: (1) topic không None-guard; (2) design_primary/reporting_standard
    # đọc SAI đường dẫn — G1 lưu lồng trong "design": {...}, không phải
    # top-level, nên luôn âm thầm rơi về placeholder "[CẦN...]" ngay cả khi
    # G1 đã xác định rõ thiết kế thật.
    g1_design      = g1.get("design") or {}
    topic          = g0.get("topic") or study
    design_primary = g1_design.get("primary") or "[CẦN THIẾT KẾ NGHIÊN CỨU từ G1]"
    reporting_std  = g1_design.get("reporting_standard") or "[CẦN CHUẨN BÁO CÁO từ G1]"
    registration   = g2.get("g2_registration") or "[CẦN SỐ ĐĂNG KÝ từ G2]"
    irb_number     = g2.get("g2_irb_number") or "[CẦN SỐ IRB từ G2]"
    n_sr  = g0.get("n_sr", 0)
    n_rct = g0.get("n_rct", 0)
    # SỬA: dòng "N = [CẦN — cỡ mẫu thực tế từ kết quả G6]" luôn để trống dù
    # G3 đã tính N KẾ HOẠCH thật bằng công thức thống kê (vd 5755) — vẫn dùng
    # nhất quán ở G4/G6/G7. KHÔNG được ghi thẳng "N=5755" như thể là N đã
    # ENROLL thật (dễ gây hiểu lầm với tạp chí) — chỉ ghi rõ đây là N KẾ HOẠCH,
    # N enroll thật vẫn [CẦN] chờ khóa CSDL (G5) + phân tích (G6).
    n_planned = g3.get("n_adjusted") or g3.get("n_total") or 0

    # Lấy research gaps từ G0 nếu có
    research_gaps = g0.get("research_gaps", "")
    if isinstance(research_gaps, list):
        research_gaps = "; ".join(str(x) for x in research_gaps[:2])
    if not research_gaps:
        research_gaps = "[CẦN — mô tả khoảng trống bằng chứng từ G0]"

    journal_display = target_journal or "[CẦN ĐIỀN TÊN TẠP CHÍ]"

    lines = [
        "## PHẦN 6 — THƯ GỬI TẠP CHÍ (COVER LETTER SHELL)",
        "",
        "> **Hướng dẫn:** Điền đầy đủ [CẦN] trước khi nộp.",
        "> Không vượt quá 1 trang A4. Tông văn: tự tin, súc tích, học thuật.",
        "",
        "```",
        f"[Tên + Địa chỉ đơn vị + Ngày: {_TODAY}]",
        "",
        f"Dear Editor-in-Chief of {journal_display},",
        "",
        "We are pleased to submit our manuscript entitled:",
        "\"[CẦN — TIÊU ĐỀ ĐẦY ĐỦ KHÔNG QUÁ 120 KÝ TỰ]\"",
        f"for consideration for publication in {journal_display}.",
        "",
        "SIGNIFICANCE AND NOVELTY:",
        f"  {topic} represents an important clinical challenge.",
        f"  Current evidence includes {n_sr} systematic review(s) and",
        f"  {n_rct} randomized controlled trial(s), yet:",
        f"  {research_gaps}",
        "  Our study addresses this gap by [CẦN — đóng góp chính của bài].",
        "",
        "STUDY DESIGN:",
        f"  We conducted a {design_primary} following {reporting_std} reporting standards.",
        (
            f"  N (kế hoạch, tính trước theo G3) = {n_planned}. "
            "N thực tế enroll = [CẦN — sau khi khóa CSDL (G5) + phân tích (G6)]."
            if n_planned > 0 else
            "  N = [CẦN — cỡ mẫu thực tế từ kết quả G6]."
        ),
        f"  The study was registered at {registration}",
        f"  and received ethical approval (IRB No. {irb_number}).",
        "",
        "KEY FINDINGS:",
        "  [CẦN — 2-3 câu tóm tắt kết quả chính từ G6/G7]",
        "  [Điền sau khi hoàn tất phân tích và có kết quả thật]",
        "",
        "CONTRIBUTION TO THE FIELD:",
        "  [CẦN — ý nghĩa lâm sàng + chính sách + hướng nghiên cứu tiếp]",
        "",
        "MANUSCRIPT CHECKLIST:",
        f"  ☐ Word count (excluding refs/tables): [CẦN — <= giới hạn {journal_display}]",
        "  ☐ References: [CẦN]   ☐ Tables: [CẦN]   ☐ Figures: [CẦN]",
        f"  ☐ {reporting_std} checklist: Attached",
        "  ☐ Open access option: [CẦN — Yes/No + funding source]",
        "",
        "DECLARATIONS:",
        "  - This manuscript has not been published and is not under consideration elsewhere.",
        "  - All authors have approved the final version for submission.",
        "  - Conflicts of interest: [CẦN — 'None declared' hoặc liệt kê từ Phần 2]",
        "  - Funding: [CẦN]",
        "  - Data availability: [CẦN — lựa chọn từ Phần 3]",
        (
            # ICMJE Recommendations, Section V.A "Use of AI by Authors" (cập nhật 1/2026,
            # icmje.org/recommendations/browse/artificial-intelligence/ai-use-by-authors.html):
            # yêu cầu khai báo việc dùng công nghệ AI (LLM/chatbot/tạo ảnh) trong quá trình
            # tạo ra bản thảo nộp, TẠI HAI NƠI — cover letter VÀ mục phù hợp trong bản thảo.
            # Không khai báo có thể bị coi là hành vi sai trái khoa học (mục III.A/III.B) —
            # thêm dòng này vào cover letter (trước đây chỉ có ở Phần 4 khai báo AI riêng,
            # KHÔNG có trong chính cover letter — vá 2026-07-17, round audit đối kháng 4).
            "  - Use of AI-assisted technologies (LLMs/chatbots/image creators) in producing "
            "this submission: [CẦN XÁC NHẬN Yes/No]. Nếu có dùng EBM Copilot hoặc công cụ "
            "khác, ghi đúng tool/provider/version/purpose và khớp Phần 4."
        ),
        "",
        "SUGGESTED REVIEWERS (khuyến nghị, không bắt buộc):",
        "  1. [CẦN — Tên | Institution | Email | Lý do]",
        "  2. [CẦN — Tên | Institution | Email | Lý do]",
        "  3. [CẦN — Tên | Institution | Email | Lý do]",
        "",
        "EXCLUDED REVIEWERS (nếu cần):",
        "  [CẦN — Tên | Lý do loại trừ]",
        "",
        "Thank you for considering our manuscript.",
        "",
        "Sincerely,",
        "[CẦN — Tên Tác giả Liên lạc]",
        "[CẦN — Chức vụ | Đơn vị | Điện thoại | Email]",
        "[CẦN — ORCID: 0000-0000-0000-0000]",
        "",
        "On behalf of all authors: [CẦN — liệt kê tên tất cả đồng tác giả]",
        "```",
        "",
        "---",
        "",
    ]
    return "\n".join(lines)


# ════════════════════════════════════════════════════════════════════════════
# 8. SINH PHẦN 7 — BẢN MẪU PHẢN HỒI PHẢN BIỆN
# ════════════════════════════════════════════════════════════════════════════

def build_part7_reviewer_response(study: str, target_journal: str) -> str:
    """
    Sinh bản mẫu phản hồi phản biện (Response-to-Reviewers Template).
    Cấu trúc: từng điểm reviewer -> phản hồi -> thay đổi trong bản thảo.
    """
    journal_display = target_journal or "[TÊN TẠP CHÍ]"

    lines = [
        "## PHẦN 7 — BẢN MẪU PHẢN HỒI PHẢN BIỆN (Response-to-Reviewers Template)",
        "",
        "> **Hướng dẫn sử dụng:**",
        "> 1. Điền từng bình luận phản biện vào ô [Bình luận].",
        "> 2. Viết phản hồi học thuật vào [Phản hồi tác giả] — súc tích, tôn trọng.",
        "> 3. Ghi rõ thay đổi cụ thể trong bản thảo: dòng X, trang Y.",
        "> 4. Nếu không đồng ý: lập luận học thuật có căn cứ, không phòng thủ.",
        "",
        "```",
        "RESPONSE TO REVIEWERS",
        "Manuscript: [CẦN — mã bản thảo khi tạp chí cấp]",
        f"Journal: {journal_display}",
        f"Date: {_TODAY}",
        "═══════════════════════════════════════════════════════════════",
        "",
        "Dear Editor and Reviewers,",
        "",
        "We sincerely thank the Editor and Reviewers for their thorough evaluation.",
        "We have carefully addressed all comments. Point-by-point responses below.",
        "Reviewer comments in regular text; responses in [RESPONSE:...];",
        "manuscript changes in [CHANGE:...].",
        "",
        "═══════════════════════════════════════════════════════════════",
        "ASSOCIATE EDITOR'S COMMENTS",
        "═══════════════════════════════════════════════════════════════",
        "",
        "Comment AE-1: [CẦN — bình luận của Associate Editor nếu có]",
        "[RESPONSE: CẦN — phản hồi tác giả]",
        "[CHANGE: CẦN — 'No change required' hoặc 'Line X, page Y: ...']",
        "",
        "───────────────────────────────────────────────────────────────",
        "REVIEWER 1 COMMENTS",
        "───────────────────────────────────────────────────────────────",
        "",
        "Comment R1-1 (Major): [CẦN — bình luận chính 1 của Reviewer 1]",
        "[RESPONSE: CẦN — phản hồi, có tài liệu tham khảo nếu cần]",
        "[CHANGE: CẦN — 'Methods, para 3, page X, line Y: [trích đoạn sửa]']",
        "",
        "Comment R1-2 (Major): [CẦN]",
        "[RESPONSE: CẦN]",
        "[CHANGE: CẦN]",
        "",
        "Comment R1-3 (Minor): [CẦN — typo, phong cách...]",
        "[RESPONSE: Thank you. We have corrected accordingly.]",
        "[CHANGE: CẦN — 'Line X, page Y: corrected from ... to ...']",
        "",
        "───────────────────────────────────────────────────────────────",
        "REVIEWER 2 COMMENTS",
        "───────────────────────────────────────────────────────────────",
        "",
        "Comment R2-1 (Major): [CẦN]",
        "[RESPONSE: CẦN]",
        "[CHANGE: CẦN]",
        "",
        "Comment R2-2 (Minor): [CẦN]",
        "[RESPONSE: CẦN]",
        "[CHANGE: CẦN]",
        "",
        "[THÊM REVIEWER NẾU CÓ — copy block trên]",
        "",
        "═══════════════════════════════════════════════════════════════",
        "SUMMARY OF CHANGES",
        "═══════════════════════════════════════════════════════════════",
        "1. [CẦN — Tóm tắt thay đổi lớn 1]",
        "2. [CẦN — Tóm tắt thay đổi lớn 2]",
        "3. [CẦN — Thay đổi nhỏ về ngôn ngữ/định dạng]",
        "",
        "We remain available to address any further concerns.",
        "Sincerely, [CẦN — Tên Tác giả Liên lạc] | On behalf of all authors",
        "═══════════════════════════════════════════════════════════════",
        "```",
        "",
        "---",
        "",
    ]
    return "\n".join(lines)


# ════════════════════════════════════════════════════════════════════════════
# 9. SINH PHẦN 8 — TIÊU CHÍ QUA CỔNG G9 (HARD GATE)
# ════════════════════════════════════════════════════════════════════════════

def build_part8_gate_criteria(cps: dict, n_authors: int, study: str) -> str:
    """
    Sinh bảng tiêu chí cứng G9.
    Không thể tự động hóa hoàn toàn — cần chữ ký PI và xác nhận thể chế.
    Hiển thị trạng thái cổng trước (G2, G4) từ checkpoint.
    """
    g4 = cps.get("G4", {})
    g2 = cps.get("G2", {})
    g5 = cps.get("G5", {})
    g7 = cps.get("G7", {})
    g1 = cps.get("G1", {})

    g2_status = g2.get("g2_status", "CHƯA RÕ")
    g4_status = g4.get("g4_status", "CHƯA RÕ")
    # SỬA (bug nghiêm trọng nhất tìm thấy ở cặp G8/G9): g2_status/g4_status
    # chỉ có DUY NHẤT MỘT nơi ghi giá trị trong toàn bộ codebase — hardcode
    # cứng "PENDING" (run_g2_auto.py) / "PENDING — CHỜ BÁC SĨ KÝ SAP"
    # (run_g4_auto.py). KHÔNG CÓ script nào từng ghi "LOCKED" vào 2 field
    # này — nghĩa là dù bác sĩ đã điền IRB thật + ký SAP thật (khiến G8 báo
    # "PASS — ĐỦ ĐIỀU KIỆN NỘP"), G9 vẫn mãi mãi hiện "⚠ CHỜ BÁC SĨ" vì đang
    # dựa vào field không bao giờ đổi giá trị — 2 nguồn sự thật mâu thuẫn
    # nhau giữa G8 và G9 cho cùng 1 câu hỏi. Sửa: dùng CÙNG tín hiệu đáng
    # tin mà G8 đã dùng — kiểm nội dung THẬT (số IRB/ngày ký SAP đã điền,
    # không còn placeholder [CẦN]), không dựa vào field trạng thái riêng.
    ethics_locked_text = bool(
        g2.get("g2_irb_number") and "[CẦN" not in str(g2.get("g2_irb_number", ""))
        and "[CAN" not in str(g2.get("g2_irb_number", ""))
    )
    sap_locked_text = bool(
        (g4.get("sap_signed_date") or g4.get("sap_locked"))
        and "[CẦN" not in str(g4.get("sap_signed_date", ""))
    )
    # Audit 2026-07-11: checkpoint text một mình không còn đủ — cần thêm phê duyệt
    # thật khớp hash trong approval_ledger.json (cùng chuẩn run_stats_analysis.py/
    # run_g6_auto.py), vì đây là cổng cứng CUỐI CÙNG trước nộp bài ra ngoài.
    ethics_locked = (
        ethics_locked_text
        and _ledger_approved(
            study, "G2",
            _REPO_ROOT / "exports" / study / f"G2_A3_ETHICS_PACKAGE_{study}.md",
        )
        and GC.g2_quality_contract_satisfied(
            g2,
            GC.load_study_meta(_REPO_ROOT / "exports" / study),
        )
    )
    sap_locked = sap_locked_text and _ledger_approved(
        study, "G4", _REPO_ROOT / "exports" / study / f"G4_A5_SAP_FINAL_{study}.md")

    # THÊM 2026-07-23 (vòng lặp kiểm tra-hoàn thiện vòng 12, phát hiện HIGH):
    # nop-bai-phan-hoi.md BƯỚC 0 điểm 2 yêu cầu xác nhận "G5_STATUS = LOCKED"
    # là tiền đề G9 — nhưng trước đây file này chỉ tính boolean cho G2/G4,
    # KHÔNG có biến nào cho G5 dù đã đọc G5_checkpoint.json vào cps từ trước.
    # Một đề tài có CSDL CHƯA khóa (rủi ro thao túng dữ liệu sau khi đã biết
    # kết quả — đúng loại rủi ro G9 tồn tại để chặn) vẫn nhận gói A10 đầy đủ mà
    # không có cảnh báo tự động, khác hẳn cách G2/G4 được xử lý.
    db_locked_text = bool(
        g5.get("db_lock_date") and "[CẦN" not in str(g5.get("db_lock_date", ""))
        and "[CAN" not in str(g5.get("db_lock_date", ""))
    )
    db_locked = GC.g5_quality_contract_satisfied(
        study,
        repo_root=_REPO_ROOT,
    ) or (
        db_locked_text
        and _ledger_approved(
            study,
            "G5",
            _REPO_ROOT / "exports" / study / f"G5_A6_DATA_MGMT_{study}.md",
        )
    )

    g2_icon = "✅" if ethics_locked else "⚠ CHỜ BÁC SĨ"
    g4_icon = "✅" if sap_locked    else "⚠ CHỜ BÁC SĨ"
    g5_icon = "✅" if db_locked     else "⚠ CHỜ BÁC SĨ"

    # SỬA: g1.get("reporting_standard") đọc sai đường dẫn (lồng trong
    # "design") — nếu G7 chưa chạy, chuỗi fallback nhảy thẳng xuống "[CẦN]"
    # dù G1 đã có chuẩn báo cáo thật.
    reporting_std = (
        g7.get("reporting_standard")
        or (g1.get("design") or {}).get("reporting_standard")
        or "[CẦN]"
    )
    # THÊM 2026-07-23 (vòng lặp kiểm tra-hoàn thiện vòng 12, phát hiện MEDIUM):
    # nếu G1 phát hiện specialist_modules (vd 'economic'), G7 đã tự nối thêm
    # phụ lục CHEERS 2022 riêng vào bản thảo (vòng 11) -- C4 trước đây chỉ nhắc
    # MỘT chuẩn báo cáo chính, khiến bác sĩ có thể tick "Đã điền và đính kèm"
    # mà quên rà phụ lục CHEERS đi kèm.
    specialist_modules = g1.get("specialist_modules") or []
    reporting_std_note = ""
    if "economic" in specialist_modules:
        reporting_std_note = " + CHEERS 2022 (cấu phần kinh tế y tế cộng thêm, xem A8/G7)"

    # THÊM 2026-07-24 (vòng lặp kiểm tra-hoàn thiện vòng 17, phát hiện HIGH):
    # run_g3_auto.py (vòng 15) ghi rõ margin "[CẦN — ...PHẢI có biện minh lâm
    # sàng... và được Hội đồng/thống kê viên xác nhận TRƯỚC khi khóa SAP]",
    # nhưng KHÔNG cổng nào sau G3 (kể cả G9 — cổng liêm chính tác giả CUỐI
    # CÙNG) kiểm tra/bắt xác nhận điều này bằng structured field. Rủi ro: chọn
    # margin lỏng lẻo/thuận tiện SAU khi đã thấy dữ liệu có xu hướng thuận lợi
    # (biến "không đạt superiority" thành "đạt non-inferiority") — cùng loại
    # rủi ro HARKing mà NHÓM A tồn tại để chặn.
    g3 = cps.get("G3", {})
    hypothesis_type = g3.get("hypothesis_type") or "superiority"
    margin = g3.get("margin")
    ni_gate_block = ""
    if hypothesis_type in ("non_inferiority", "equivalence"):
        ni_gate_block = "\n".join([
            "",
            f"A6. [CHỈ {hypothesis_type.upper()}] Margin Δ = {margin if margin is not None else '[CẦN]'} đã "
            "được Hội đồng/thống kê viên xác nhận biện minh lâm sàng TRƯỚC khi khóa SAP (G4)",
            f"    ☐ Chưa xác nhận  ☐ Đã xác nhận, ngày: [CẦN ___/___/{_YEAR}]",
        ])

    lines = [
        "## PHẦN 8 — TIÊU CHÍ QUA CỔNG G9 (HARD GATE — CẦN KÝ)",
        "",
        "> **Cảnh báo:** G9 là Cổng CỨNG cuối cùng. KHÔNG nộp bản thảo ra bên ngoài",
        "> trước khi TẤT CẢ tiêu chí dưới đây được hoàn thành và có chữ ký thật.",
        "> AI KHÔNG THỂ tự động hoàn tất cổng này — cần hành động thực của bác sĩ.",
        "",
        "```",
        "TIÊU CHÍ CỔNG G9 — LIÊM CHÍNH TÁC GIẢ",
        f"Đề tài: {study} | Kiểm tra lúc: {_TODAY}",
        "═══════════════════════════════════════════════════════════════",
        "",
        "NHÓM A — LIÊM CHÍNH TÁC GIẢ (bắt buộc 100%)",
        "─────────────────────────────────────────────",
        f"A1. ICMJE 4 tiêu chí tác giả: Tất cả {n_authors} tác giả đủ tiêu chí",
        f"    ☐ Chưa ký  ☐ Đã ký đầy đủ -> [CẦN ngày ký: ___/___/{_YEAR}]",
        "",
        f"A2. Final COI: Tất cả {n_authors} tác giả khai báo xung đột lợi ích",
        "    ☐ Chưa nộp  ☐ Đã nộp đủ form ICMJE gốc",
        f"    Ngày khai báo cuối: [CẦN ___/___/{_YEAR}]",
        "",
        "A3. Tuyên bố Liêm chính: PI ký xác nhận 5 điểm (Phần 5)",
        f"    ☐ Chưa ký  ☐ PI đã ký  Ngày: [CẦN ___/___/{_YEAR}]",
        "",
        "A4. Khai báo AI đầy đủ (Phần 4) — không thiếu công cụ nào",
        "    ☐ Chưa duyệt  ☐ Đã duyệt và xác nhận",
        "",
        "A5. Data Availability Statement đã chọn (Phần 3)",
        "    ☐ Chưa chọn  ☐ Đã chọn Option [A/B/C]",
        ni_gate_block,
        "",
        "A7. Quyền truy cập dữ liệu theo ICMJE 01/2026 đã xác nhận",
        "    ☐ Mọi tác giả có thể rà dữ liệu hỗ trợ kết quả",
        "    ☐ Ít nhất một tác giả truy cập dữ liệu gốc và tham gia phân tích",
        "    ☐ Hợp đồng tài trợ không hạn chế truy cập dữ liệu/độc lập công bố (nếu áp dụng)",
        "",
        "NHÓM B — TIỀN ĐỀ CỔNG TRƯỚC (phải LOCKED trước G9)",
        "─────────────────────────────────────────────",
        "B1. G2 (Đạo đức) = LOCKED",
        f"    Hiện tại: {'LOCKED (IRB thật đã điền)' if ethics_locked else g2_status}  {g2_icon}",
        f"    Số IRB: {g2.get('g2_irb_number', '[CẦN]')}",
        "",
        "B2. G4 (SAP khóa) = LOCKED",
        f"    Hiện tại: {'LOCKED (SAP đã ký thật)' if sap_locked else g4_status}  {g4_icon}",
        f"    SAP Lock Date: {g4.get('g4_lock_date', '[CẦN]')}",
        "",
        "B3. G5 (Khóa CSDL) = LOCKED",
        f"    Hiện tại: {'LOCKED (CSDL đã khóa thật)' if db_locked else 'CHƯA KHÓA'}  {g5_icon}",
        f"    DB Lock Date: {g5.get('db_lock_date', '[CẦN]')}",
        "",
        "NHÓM C — CHẤT LƯỢNG BẢN THẢO",
        "─────────────────────────────────────────────",
        "C1. Bản thảo IMRAD (G7) đã có kết quả THẬT (không còn [CẦN KẾT QUẢ THẬT])",
        "    ☐ Còn [CẦN]  ☐ Đã hoàn chỉnh",
        "",
        "C2. Tất cả PMID/DOI đã kiểm chứng toàn văn",
        "    ☐ Chưa kiểm  ☐ Đã kiểm chứng đầy đủ",
        "",
        "C3. Similarity/plagiarism đã rà theo chính sách tạp chí/cơ sở",
        "    Tỷ lệ thực tế: [CẦN điền sau khi chạy iThenticate/Turnitin]%",
        "    ☐ Chưa chạy  ☐ Đã rà từng nguồn và có kết luận của người chịu trách nhiệm",
        "",
        f"C4. Checklist báo cáo ({reporting_std}{reporting_std_note}) hoàn chỉnh",
        "    ☐ Chưa điền  ☐ Đã điền và đính kèm",
        "",
        "C5. Thư gửi tạp chí (Phần 6) và mẫu phản biện (Phần 7) hoàn chỉnh",
        "    ☐ Chưa điền  ☐ Đã hoàn chỉnh",
        "",
        "NHÓM D — XÁC NHẬN THỂ CHẾ (nếu bắt buộc)",
        "─────────────────────────────────────────────",
        "D1. Trưởng đơn vị xác nhận cho phép nộp bài",
        f"    ☐ Không cần  ☐ Cần -> ☐ Đã ký  Ngày: [CẦN ___/___/{_YEAR}]",
        "",
        "D2. Hội đồng xét duyệt bài trước khi nộp (nếu đơn vị yêu cầu)",
        "    ☐ Không cần  ☐ Đã qua xét duyệt  Ngày: [CẦN]",
        "",
        "D3. Nhà tài trợ duyệt nội dung (nếu có hợp đồng)",
        "    ☐ Không có tài trợ  ☐ Đã được nhà tài trợ duyệt",
        "",
        "═══════════════════════════════════════════════════════════════",
        "G9 STATUS: DRAFT — CHỜ KÝ TẤT CẢ TÁC GIẢ VÀ PI",
        "",
        "KẾT LUẬN: G9 chỉ PASSED khi TẤT CẢ ô ☐ ở NHÓM A, B, C được tích xong.",
        f"Ngày G9 PASSED dự kiến: [CẦN ___/___/{_YEAR}]",
        "",
        # THÊM 2026-07-30 (audit toàn diện G0-G10, G9-F4 — MEDIUM): checklist
        # trên là văn bản bác sĩ ĐỌC/KÝ trên giấy/Word, nhưng không có mã nào
        # đọc lại trạng thái tick ☐/☑ ở đây — cổng THẬT 100% đến từ
        # G9_PUBLICATION_READINESS.json (chấm bởi g9_quality_gate.py) và chữ
        # ký ledger trên G9_checkpoint.json (qua approve_gate.py --gate G9).
        # Điền/ký đầy đủ bảng trên giấy KHÔNG tự động tiến được bước nào ở
        # cổng thật nếu chưa cập nhật đúng 2 file đó.
        "LƯU Ý: Bảng trên là checklist THAM KHẢO cho bác sĩ tự rà — cổng G9",
        "THẬT (quyết định PASS/BLOCK) đến từ tools/g9_quality_gate.py chấm",
        "G9_PUBLICATION_READINESS.json, và chữ ký PI qua:",
        "  python tools/approve_gate.py --study <mã> --gate G9 ...",
        "Tự tay tick đủ các ô ☐ trên văn bản này KHÔNG thay thế 2 bước đó.",
        "",
        "Chữ ký PI xác nhận G9 PASSED:",
        f"_______________  Ngày: ___/___/{_YEAR}",
        "═══════════════════════════════════════════════════════════════",
        "```",
        "",
        "---",
        "",
    ]
    return "\n".join(lines)


# ════════════════════════════════════════════════════════════════════════════
# 10. GUARDRAIL R1-R7 CHO G9
# ════════════════════════════════════════════════════════════════════════════

def guardrail_check_g9(artifact: str) -> dict:
    """
    Kiểm guardrail 7 quy tắc R1-R7 cho gói G9.
    Trả về dict: passed (bool), errors (list), warnings (list).
    """
    errors, warnings = [], []

    # R1 — Không PII
    pii_patterns = [
        r'\b(CMND|CCCD)\s*[:\-]?\s*\d{9,12}\b',
        r'\bBN\s*\d{5,}\b',
    ]
    if any(re.search(p, artifact, re.IGNORECASE) for p in pii_patterns):
        errors.append("R1 🔴 Phát hiện PII tiềm năng — kiểm tra và xóa")
    else:
        warnings.append("R1 ✅ Không phát hiện PII")

    # R2 — Không bịa DOI/số đăng ký cụ thể ngoài ngữ cảnh [CẦN]
    doi_match = re.search(r'\b10\.\d{4,}/\S{4,}\b', artifact)
    if doi_match:
        start = max(0, doi_match.start() - 50)
        context = artifact[start:doi_match.end() + 50]
        if "[CẦN" not in context:
            errors.append(
                f"R2 🔴 DOI cụ thể '{doi_match.group()}' không có nhãn [CẦN] — kiểm tra không bịa đặt"
            )
        else:
            warnings.append("R2 ✅ DOI có nhãn [CẦN] đi kèm")
    else:
        warnings.append("R2 ✅ Không phát hiện DOI bịa đặt")

    # R3 — Không tự claim G9 đã PASSED
    if re.search(r'G9[_\s]?STATUS\s*[:=]\s*PASSED', artifact, re.IGNORECASE):
        errors.append("R3 🔴 Không được tự claim G9 đã PASSED — cần chữ ký PI thật")
    else:
        warnings.append("R3 ✅ Không tự claim G9 PASSED")

    # R4 — Đủ nhãn DRAFT và CHỜ
    # LƯU Ý PHẠM VI (audit tautology vòng 2, 2026-07-31): main() ghép artifact
    # từ header + 8 phần + footer — cả header ("**Trạng thái:** DRAFT — CHỜ KÝ
    # TẤT CẢ TÁC GIẢ"), footer ("[BẢN NHÁP TỰ ĐỘNG — DRAFT]"), build_part1_
    # icmje/build_part2_coi/build_part5_integrity (mỗi hàm 1 dòng "[DRAFT —
    # ...]" cố định), và build_part8_gate_criteria ("G9 STATUS: DRAFT — CHỜ KÝ
    # TẤT CẢ TÁC GIẢ VÀ PI") đều in các chuỗi này VÔ ĐIỀU KIỆN — không phụ
    # thuộc n_authors/target_journal/checkpoint nào. Ngưỡng draft_count>=3 và
    # cho_count>=2 LUÔN đạt qua pipeline thật (xác nhận: 5 nguồn "DRAFT" + 3
    # nguồn "CHỜ" cố định, chưa kể phần điều kiện). Tiêu chí chỉ bắt được nếu
    # ai đó xóa các dòng này SAU KHI sinh (tampering), không thẩm định gói đã
    # thật sự sẵn sàng ký hay chưa — việc đó thuộc g9_quality_gate.py.
    draft_count = artifact.count("DRAFT")
    cho_count   = artifact.count("CHỜ")
    if draft_count >= 3 and cho_count >= 2:
        warnings.append(f"R4 ✅ Nhãn DRAFT ({draft_count}) và CHỜ ({cho_count}) đủ")
    else:
        errors.append(
            f"R4 🔴 Thiếu nhãn DRAFT/CHỜ (DRAFT={draft_count}, CHỜ={cho_count} — cần >=3/2)"
        )

    # R5 — Đủ trường [CẦN]
    # SỬA 2026-07-30 (audit toàn diện G0-G10, G9-F5 — MEDIUM, phát hiện khi
    # chạy lại guardrail_check_g9() tươi cho G9-AUTO-02): ngưỡng "≥15 [CẦN]"
    # XUNG ĐỘT TRỰC TIẾP với g9_quality_gate.py::_documents_clean() (dùng cho
    # G9-AUTO-05) — hàm đó đòi CHÍNH file A10 này KHÔNG còn "[CẦN..." nào mới
    # được coi "sạch, sẵn sàng nộp". Một gói G9 THỰC SỰ hoàn chỉnh (bác sĩ đã
    # điền hết) sẽ có can_count=0, khiến R5 cũ luôn ERROR đúng lúc gói đã sẵn
    # sàng nhất — cùng lớp "phạt chính việc hoàn thiện" đã sửa ở G8 R6. Hạ
    # xuống cảnh báo thông tin, không còn chặn.
    can_count = len(re.findall(r'\[CẦN', artifact))
    warnings.append(f"R5 ✅ {can_count} trường [CẦN...] còn lại (thông tin, không chặn)")

    # R6 — 8 phần đủ
    # LƯU Ý PHẠM VI (audit tautology vòng 2, 2026-07-31): main() ghép artifact
    # bằng "\n".join([header, part1, ..., part8, footer]) — part1..part8 là
    # kết quả của build_part1_icmje()...build_part8_gate_criteria(), MỖI hàm
    # in tiêu đề "## PHẦN N — ..." VÔ ĐIỀU KIỆN ở đầu, và cả 8 hàm LUÔN được
    # gọi theo đúng thứ tự cố định — không có nhánh nào bỏ qua một phần theo
    # study/n_authors/checkpoint. R6 KHÔNG BAO GIỜ có thể BLOCK qua pipeline
    # thật; giá trị hẹp DUY NHẤT là bắt được nếu ai đó xóa một tiêu đề phần
    # khỏi file .md SAU KHI sinh (tampering/truncation) — không thẩm định nội
    # dung từng phần có đủ/đúng hay chưa (việc đó thuộc g9_quality_gate.py
    # G9-HUMAN-01..10). Cùng dạng lỗi đã đóng ở G7-AUTO-04 (7 mục A8 IMRAD).
    required_sections = [
        "PHẦN 1", "PHẦN 2", "PHẦN 3", "PHẦN 4",
        "PHẦN 5", "PHẦN 6", "PHẦN 7", "PHẦN 8",
    ]
    missing = [s for s in required_sections if s not in artifact]
    if missing:
        errors.append(f"R6 🔴 Thiếu phần: {', '.join(missing)}")
    else:
        warnings.append("R6 ✅ Đủ 8 phần A10")

    # R7 — Disclaimer
    # SỬA 2026-07-31 (audit tautology vòng 2): header ("> Cần bác sĩ kiểm
    # chứng toàn bộ nội dung.") và footer ("Cần bác sĩ kiểm chứng.") của
    # main() đều in dòng này VÔ ĐIỀU KIỆN — R7 chỉ bắt được tampering (xóa
    # dòng sau khi sinh), không thẩm định bác sĩ có thực sự đọc lại nội dung
    # hay chưa. Cùng khuôn R7 đã đóng ở G0/G1/G2/G3/G6/G7/G8 trong đợt audit
    # này.
    if "cần bác sĩ" in artifact.lower() and "kiểm chứng" in artifact.lower():
        warnings.append("R7 ✅ Có disclaimer 'Cần bác sĩ kiểm chứng'")
    else:
        errors.append("R7 🔴 Thiếu disclaimer 'Cần bác sĩ kiểm chứng'")

    return {"passed": len(errors) == 0, "errors": errors, "warnings": warnings}


# ════════════════════════════════════════════════════════════════════════════
# 11. XUẤT DOCX
# ════════════════════════════════════════════════════════════════════════════

def export_docx_g9(artifact_md: str, study: str, out_dir: Path) -> Optional[Path]:
    """
    Xuất gói A10 ra định dạng DOCX.
    Các ô [CẦN] tô màu cam; nhãn DRAFT/CHỜ in đậm để dễ nhận biết.
    """
    try:
        from docx import Document
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.shared import Pt, RGBColor

        doc = Document()

        # Trang bìa
        t = doc.add_heading("GÓI LIÊM CHÍNH TÁC GIẢ — A10", 0)
        t.alignment = WD_ALIGN_PARAGRAPH.CENTER
        s = doc.add_paragraph(f"Đề tài: {study}")
        s.alignment = WD_ALIGN_PARAGRAPH.CENTER
        d = doc.add_paragraph(
            f"[BẢN NHÁP TỰ ĐỘNG] | {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        d.alignment = WD_ALIGN_PARAGRAPH.CENTER
        w = doc.add_paragraph(
            "CẢNH BÁO: Gói này CHỈ có hiệu lực sau khi TẤT CẢ tác giả và PI ký. "
            "Cần bác sĩ kiểm chứng toàn bộ trước khi nộp."
        )
        w.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in w.runs:
            run.bold = True
            run.font.color.rgb = RGBColor(0xCC, 0x00, 0x00)

        doc.add_page_break()

        for line in artifact_md.split("\n"):
            stripped = line.strip()
            if line.startswith("# "):
                doc.add_heading(line[2:], 1)
            elif line.startswith("## "):
                doc.add_heading(line[3:], 2)
            elif line.startswith("### "):
                doc.add_heading(line[4:], 3)
            elif stripped in ("---", "```"):
                pass  # bỏ qua divider và code fence
            elif stripped.startswith("|"):
                p = doc.add_paragraph(stripped)
                if p.runs:
                    p.runs[0].font.name = "Courier New"
                    p.runs[0].font.size = Pt(8)
            elif stripped:
                p = doc.add_paragraph(line)
                for run in p.runs:
                    if "[CẦN" in run.text:
                        run.font.color.rgb = RGBColor(0xCC, 0x44, 0x00)
                    if "DRAFT" in run.text or "CHỜ KÝ" in run.text:
                        run.bold = True

        docx_path = out_dir / f"G9_A10_AUTHOR_INTEGRITY_{study}.docx"
        doc.save(docx_path)
        return docx_path

    except ImportError:
        print("  ⚠ python-docx chưa cài — bỏ qua DOCX (pip install python-docx)")
        return None
    except Exception as exc:
        print(f"  ⚠ Lỗi khi xuất DOCX: {exc}")
        return None


# ════════════════════════════════════════════════════════════════════════════
# 12. GHI CHECKPOINT G9
# ════════════════════════════════════════════════════════════════════════════

def write_g9_checkpoint(
    study: str,
    out_dir: Path,
    n_authors: int,
    target_journal: str,
    guardrail: dict,
    md_path: Path,
    docx_path: Optional[Path],
    cps: dict,
) -> Path:
    """Ghi G9_checkpoint.json với trạng thái DRAFT — CHỜ KÝ TẤT CẢ TÁC GIẢ."""

    g2_cp = cps.get("G2", {}) or {}
    g4_cp = cps.get("G4", {}) or {}
    g5_cp = cps.get("G5", {}) or {}

    # Danh sách việc còn lại của bác sĩ
    pending = [
        f"Tất cả {n_authors} tác giả ký xác nhận ICMJE 4 tiêu chí (Phần 1)",
        f"Tất cả {n_authors} tác giả hoàn tất form disclosure hiện hành và evidence_ref",
        "PI ký Tuyên bố Liêm chính Nghiên cứu 5 điểm (Phần 5)",
        f"Hoàn tất hồ sơ có cấu trúc {G9Q.READINESS_JSON}",
        "Chốt Data Availability và chi tiết ICMJE nếu là thử nghiệm lâm sàng",
        "Điền và ký Thư gửi tạp chí (Phần 6)",
        "Rà similarity theo chính sách tạp chí/cơ sở và phán đoán con người",
        "Xác nhận không nộp song song và không chia nhỏ bài",
        "Duyệt AI Use Disclosure theo công cụ/mục đích thực tế, không tự suy từ checkpoint",
        "G8 phải có phản biện độc lập đã ký và A12 phải còn xác minh hợp lệ",
    ]

    # Ưu tiên thêm blocking actions từ cổng trước nếu chưa locked
    # SỬA (bug nghiêm trọng nhất G8/G9): g2_status/g4_status không bao giờ
    # được bất kỳ script nào ghi thành "LOCKED" (chỉ hardcode "PENDING..."
    # vĩnh viễn ở run_g2_auto.py/run_g4_auto.py) — dựa vào 2 field này khiến
    # phần cảnh báo LUÔN hiện "chưa khóa" dù bác sĩ đã điền IRB/ký SAP thật,
    # mâu thuẫn với G8 (vốn kiểm nội dung thật g2_irb_number/sap_signed_date
    # chứ không dựa field trạng thái). Nay dùng CHUNG tín hiệu đáng tin với
    # G8 để 2 cổng luôn đồng thuận cho cùng 1 câu hỏi.
    ethics_locked_cp_text = bool(
        g2_cp.get("g2_irb_number") and "[CẦN" not in str(g2_cp.get("g2_irb_number", ""))
        and "[CAN" not in str(g2_cp.get("g2_irb_number", ""))
    )
    sap_locked_cp_text = bool(
        (g4_cp.get("sap_signed_date") or g4_cp.get("sap_locked"))
        and "[CẦN" not in str(g4_cp.get("sap_signed_date", ""))
    )
    # Audit 2026-07-11: cùng cổng ledger đã thêm ở build_part8_gate_criteria() —
    # checkpoint viết ra phải phản ánh ĐÚNG trạng thái đã kiểm mật mã, không chỉ text.
    ethics_locked_cp = (
        ethics_locked_cp_text
        and _ledger_approved(
            study, "G2",
            _REPO_ROOT / "exports" / study / f"G2_A3_ETHICS_PACKAGE_{study}.md",
        )
        and GC.g2_quality_contract_satisfied(
            g2_cp,
            GC.load_study_meta(_REPO_ROOT / "exports" / study),
        )
    )
    sap_locked_cp = sap_locked_cp_text and _ledger_approved(
        study, "G4", _REPO_ROOT / "exports" / study / f"G4_A5_SAP_FINAL_{study}.md")
    # THÊM 2026-07-23 (vòng lặp kiểm tra-hoàn thiện vòng 12, phát hiện HIGH):
    # cùng chuỗi lỗi với build_part8_gate_criteria() — G5 (khóa CSDL) chưa bao
    # giờ được đối chiếu ở đây dù nop-bai-phan-hoi.md coi đây là tiền đề G9.
    db_locked_cp_text = bool(
        g5_cp.get("db_lock_date") and "[CẦN" not in str(g5_cp.get("db_lock_date", ""))
        and "[CAN" not in str(g5_cp.get("db_lock_date", ""))
    )
    db_locked_cp = GC.g5_quality_contract_satisfied(
        study,
        repo_root=_REPO_ROOT,
    ) or (
        db_locked_cp_text
        and _ledger_approved(
            study,
            "G5",
            _REPO_ROOT / "exports" / study / f"G5_A6_DATA_MGMT_{study}.md",
        )
    )
    if not ethics_locked_cp:
        pending.insert(
            0, "G2 (Đạo đức) chưa LOCKED — cần số IRB thật từ Hội đồng Đạo đức"
        )
    if not sap_locked_cp:
        pending.insert(
            0, "G4 (SAP) chưa LOCKED — cần ký SAP Lock Certificate"
        )
    if not db_locked_cp:
        pending.insert(
            0, "G5 (Khóa CSDL) chưa LOCKED — cần ký Biên bản khóa dữ liệu (Data Lock Memo)"
        )

    cp = {
        "gate": "G9",
        "study": study,
        "generated_at": datetime.now().isoformat(),
        "quality_contract_version": G9Q.QUALITY_CONTRACT_VERSION,
        "g9_status": "DRAFT — CHỜ KÝ TẤT CẢ TÁC GIẢ",
        "author_integrity_status": "PENDING",
        "ai_disclosure": "GENERATED — needs author review and verification",
        "submission_package_ready": False,
        "n_authors": n_authors,
        "target_journal": target_journal or "",
        "pending": pending,
        "gates_read": sorted(cps.keys()),
        "guardrail": {
            "passed": guardrail["passed"],
            "errors": guardrail["errors"],
            "n_warnings": len(guardrail["warnings"]),
        },
        "artifacts": {
            "A10_markdown": str(md_path),
            "A10_docx": str(docx_path) if docx_path else None,
            "publication_readiness": G9Q.READINESS_JSON,
            "quality_report": G9Q.REPORT_JSON,
        },
        "parts_generated": [
            "Phần 1 — ICMJE Tiêu chuẩn Tác giả (4 tiêu chí)",
            "Phần 2 — Khai báo Xung đột Lợi ích Cuối (Final COI)",
            "Phần 3 — Data Availability Statement (3 lựa chọn)",
            # SỬA 2026-07-30 (audit toàn diện G0-G10, G9-F7 — LOW): nhãn cũ
            # "COPE + Nature Portfolio 2024" là tàn dư từ phiên bản trước khi
            # Phần 4 chuyển sang trích ICMJE Mục V/2026 trực tiếp — header
            # thật của build_part4_ai_disclosure() (dòng ~376) đã ghi đúng
            # "ICMJE Mục V, cập nhật 01/2026", mâu thuẫn nội bộ với nhãn này.
            "Phần 4 — AI Use Disclosure (ICMJE Mục V, cập nhật 01/2026)",
            "Phần 5 — Tuyên bố Liêm chính Nghiên cứu",
            "Phần 6 — Thư gửi Tạp chí (Cover Letter Shell)",
            "Phần 7 — Bản mẫu Phản hồi Phản biện",
            "Phần 8 — Tiêu chí Cổng G9 (Hard Gate)",
        ],
        "lock_instruction": (
            "G9 chỉ khóa khi g9_quality_gate.py chấm READY, tất cả tác giả có "
            "attestation/evidence_ref thật, G2/G4/G5/G8/A12 còn hợp lệ và PI tự "
            "ký đúng G9_checkpoint.json. Không dùng một ngưỡng similarity phổ quát."
        ),
        "next_step": (
            f"Hoàn tất {G9Q.READINESS_JSON}, chạy g9_quality_gate.py, rồi PI tự ký "
            "G9_checkpoint.json nếu trạng thái READY"
        ),
        "disclaimer": "Cần bác sĩ kiểm chứng toàn bộ nội dung trước khi nộp bài.",
    }

    cp_path = out_dir / "G9_checkpoint.json"
    cp_path.write_text(json.dumps(cp, ensure_ascii=False, indent=2), encoding="utf-8")
    return cp_path


# ════════════════════════════════════════════════════════════════════════════
# 13. MAIN
# ════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="G9 Auto — Tự động hóa cổng G9: Liêm chính Tác giả (Author Integrity)"
    )
    parser.add_argument(
        "--study", required=True,
        help="Mã đề tài (cùng với --study ở các cổng G0-G8)",
    )
    parser.add_argument(
        "--n-authors", type=int, default=None,
        help="Số tác giả (mặc định: 1 nếu không truyền/không có pin). Sinh form COI và ICMJE cho từng người.",
    )
    parser.add_argument(
        "--target-journal", default="",
        help="Tên tạp chí mục tiêu (ví dụ: JACC / NEJM / Lancet).",
    )
    args = parser.parse_args()

    run_date       = datetime.now().strftime("%Y-%m-%d %H:%M")
    # 2026-07-11: vá path traversal, khớp chuẩn sanitize đã dùng ở G0-G5.
    study          = re.sub(r'[^\w\-]', '_', args.study.strip().replace(" ", "-"))

    # Thư mục xuất — luôn dùng đường dẫn tuyệt đối từ repo root
    out_dir = _REPO_ROOT / "exports" / study
    out_dir.mkdir(parents=True, exist_ok=True)

    # THÊM 2026-07-08 (CRIT-05): gọi thẳng script (không qua run_pipeline.py)
    # trước đây mất n_authors/target_journal bác sĩ đã pin khi chạy lại.
    # SỬA 2026-07-22 (vòng lặp kiểm tra-hoàn thiện vòng 8, phát hiện MEDIUM): trước đây
    # dùng default=1 làm sentinel cho "bác sĩ không truyền --n-authors" — nhưng 1 cũng là
    # giá trị HỢP LỆ bác sĩ có thể gõ tường minh (vd rút bớt đồng tác giả), nên bị pin cũ
    # đè âm thầm không cảnh báo. Nay default=None phân biệt được "không truyền" (None) với
    # "gõ tường minh 1"; chỉ khôi phục từ pin khi bác sĩ THẬT SỰ không truyền cờ.
    _g9_pinned = (GC.load_study_meta(out_dir).get("gate_params") or {}).get("G9") or {}
    if args.n_authors is None and _g9_pinned.get("n_authors") is not None:
        args.n_authors = _g9_pinned["n_authors"]
        print(f"  → Khôi phục n_authors={args.n_authors} từ study_meta.json (pin trước đó)")
    if args.n_authors is None:
        args.n_authors = 1
    if not args.target_journal and _g9_pinned.get("target_journal"):
        args.target_journal = _g9_pinned["target_journal"]

    # PIN durable (2026-07-09): ĐỐI XỨNG với khối ĐỌC ở trên. Vá 07-08 chỉ thêm khối
    # đọc mà KHÔNG có khối ghi tương ứng → gate_params.G9 không bao giờ được điền,
    # "khôi phục khi chạy lại" là no-op (phát hiện qua kiểm định hậu-kiểm 2026-07-09).
    # Ghi giá trị bác sĩ cấp qua CLI (fill-if-missing). n_authors CHỈ pin khi >1 (1 là
    # mặc định/sàn — pin 1 vô nghĩa và dễ khóa nhầm giá trị mặc định vào sổ).
    _seed_g9 = {}
    if args.n_authors and args.n_authors > 1:
        _seed_g9["n_authors"] = args.n_authors
    if args.target_journal:
        _seed_g9["target_journal"] = args.target_journal
    if _seed_g9:
        GC.ensure_study_meta(out_dir, seed={"gate_params": {"G9": _seed_g9}})

    n_authors      = max(1, args.n_authors)
    target_journal = args.target_journal

    print(f"\n{'='*65}")
    print(f"  G9 AUTO — LIÊM CHÍNH TÁC GIẢ | {study}")
    print(f"  Số tác giả: {n_authors} | Tạp chí: {target_journal or '(chưa xác định)'}")
    print(f"  Thời gian: {run_date}")
    print(f"{'='*65}\n")

    # ── Bước 1: Đọc tất cả checkpoints G0-G8 ──
    print("📂 Bước 1/6: Đọc checkpoints G0-G8...")
    cps = collect_all_checkpoints(out_dir)
    if cps:
        print(f"  -> Tìm thấy checkpoints: {', '.join(sorted(cps.keys()))}")
    else:
        print("  -> Không tìm thấy checkpoint nào (sẽ dùng giá trị mặc định [CẦN])")

    # ── Bước 2: Sinh từng phần ──
    print("\n✍️  Bước 2/6: Sinh 8 phần của gói A10...")

    header = "\n".join([
        "# A10 — GÓI LIÊM CHÍNH TÁC GIẢ (AUTHOR INTEGRITY PACKAGE)",
        f"> Tên file A10 được giữ để tương thích pipeline cũ; hợp đồng {G9Q.QUALITY_CONTRACT_VERSION}",
        "> dùng checkpoint/readiness có cấu trúc làm nguồn quyết định.",
        f"**Mã đề tài:** {study}",
        f"**Số tác giả:** {n_authors}",
        f"**Tạp chí mục tiêu:** {target_journal or '[CẦN XÁC NHẬN]'}",
        f"**Ngày tạo:** {run_date}",
        "**Trạng thái:** DRAFT — CHỜ KÝ TẤT CẢ TÁC GIẢ",
        "",
        "> ⚠️ **CẢNH BÁO:** Gói này CHƯA CÓ HIỆU LỰC cho đến khi TẤT CẢ tác giả ký.",
        "> KHÔNG nộp bản thảo ra bên ngoài trước khi G9 PASSED.",
        "> Mọi ô [CẦN...] phải được điền bởi bác sĩ/tác giả trước khi nộp.",
        "> Cần bác sĩ kiểm chứng toàn bộ nội dung.",
        "",
        "---",
        "",
    ])

    print("  -> Phần 1: ICMJE Tiêu chuẩn Tác giả")
    part1 = build_part1_icmje(n_authors, study)

    print("  -> Phần 2: Khai báo COI Cuối")
    part2 = build_part2_coi(n_authors, study)

    print("  -> Phần 3: Data Availability Statement")
    part3 = build_part3_data_availability(cps, study)

    print("  -> Phần 4: AI Use Disclosure")
    part4 = build_part4_ai_disclosure(cps, study)

    print("  -> Phần 5: Tuyên bố Liêm chính Nghiên cứu")
    part5 = build_part5_integrity(cps, study)

    print("  -> Phần 6: Cover Letter Shell")
    part6 = build_part6_cover_letter(cps, study, target_journal)

    print("  -> Phần 7: Response-to-Reviewers Template")
    part7 = build_part7_reviewer_response(study, target_journal)

    print("  -> Phần 8: Tiêu chí Cổng G9")
    part8 = build_part8_gate_criteria(cps, n_authors, study)

    # Footer tóm tắt việc còn lại
    footer = "\n".join([
        "---",
        "",
        "## TÓM TẮT VIỆC CÒN LẠI CỦA BÁC SĨ/TÁC GIẢ",
        "",
        "| # | Việc cần làm | Phần | Bắt buộc |",
        "|---|-------------|------|---------|",
        f"| 1 | Điền họ tên + CRediT roles cho tất cả {n_authors} tác giả | Phần 1 | ✅ Có |",
        "| 2 | Mỗi tác giả ký xác nhận 4 tiêu chí ICMJE | Phần 1 | ✅ Có |",
        "| 3 | Mỗi tác giả điền và ký form COI ICMJE gốc | Phần 2 | ✅ Có |",
        "| 4 | Chọn Data Availability Option A/B/C | Phần 3 | ✅ Có |",
        "| 5 | Duyệt và bổ sung AI Use Disclosure | Phần 4 | ✅ Có |",
        "| 6 | PI ký Tuyên bố Liêm chính 5 điểm | Phần 5 | ✅ Có |",
        "| 7 | Điền Cover Letter (tiêu đề bài, kết quả chính) | Phần 6 | ✅ Có |",
        "| 8 | Chạy similarity check và rà từng nguồn theo chính sách đích | Phần 5 | ✅ Có |",
        "| 9 | Điền Response-to-Reviewers khi nhận peer review | Phần 7 | Khi cần |",
        "| 10 | Ký checklist G9 (Phần 8) khi tất cả xong | Phần 8 | ✅ Có |",
        "",
        "---",
        "",
        f"*[BẢN NHÁP TỰ ĐỘNG — DRAFT] · Cần bác sĩ kiểm chứng. · {run_date}*",
    ])

    # Ghép toàn bộ artifact
    artifact = "\n".join([
        header, part1, part2, part3, part4,
        part5, part6, part7, part8, footer,
    ])

    # ── Bước 3: Lưu Markdown ──
    print("\n💾 Bước 3/6: Lưu A10 Markdown...")
    md_path = out_dir / f"G9_A10_AUTHOR_INTEGRITY_{study}.md"
    md_path.write_text(artifact, encoding="utf-8")
    cover_letter_path = out_dir / f"G9_COVER_LETTER_{study}.md"
    cover_letter_path.write_text(
        "\n".join(
            [
                f"# COVER LETTER — {study}",
                "",
                "> BẢN NHÁP — phải hoàn tất và đối chiếu với khai báo AI/COI trước khi nộp.",
                "",
                part6,
                "",
                "Cần bác sĩ kiểm chứng.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    readiness_path = G9Q.write_readiness_template(
        out_dir,
        study,
        n_authors,
        target_journal,
    )
    n_lines = artifact.count("\n")
    print(f"  -> Lưu: {md_path} ({len(artifact)//1000} KB, {n_lines} dòng)")

    # ── Bước 4: Guardrail ──
    print("\n🛡️  Bước 4/6: Kiểm guardrail R1-R7...")
    gr = guardrail_check_g9(artifact)
    for msg in gr["warnings"]:
        print(f"  {msg}")
    for err in gr["errors"]:
        print(f"  {err}")
    guardrail_status = "✅ PASS" if gr["passed"] else f"⚠ {len(gr['errors'])} LỖI"
    print(f"  -> Guardrail: {guardrail_status}")

    # ── Bước 5: DOCX ──
    print("\n📄 Bước 5/6: Xuất DOCX...")
    docx_path = export_docx_g9(artifact, study, out_dir)
    if docx_path:
        print(f"  -> Lưu: {docx_path}")
    else:
        print("  -> Bỏ qua DOCX (python-docx chưa cài hoặc lỗi)")

    # ── Bước 6: Checkpoint ──
    print("\n📋 Bước 6/6: Ghi G9_checkpoint.json...")
    cp_path = write_g9_checkpoint(
        study=study,
        out_dir=out_dir,
        n_authors=n_authors,
        target_journal=target_journal,
        guardrail=gr,
        md_path=md_path,
        docx_path=docx_path,
        cps=cps,
    )
    print(f"  -> Lưu: {cp_path}")
    quality_report = G9Q.evaluate_study(
        study,
        out_dir,
        repo_root=_REPO_ROOT,
        write=True,
    )

    # ── Tóm tắt ──
    print(f"\n{'='*65}")
    print(f"  G9 DRAFT ĐÃ SINH — {study}")
    print(f"{'='*65}")
    print(f"\n  📁 Đầu ra: {out_dir}/")
    print(f"  📝 A10 Markdown: {md_path.name}")
    if docx_path:
        print(f"  📄 A10 DOCX:     {docx_path.name}")
    print(f"  📋 Checkpoint:   {cp_path.name}")
    print(f"  🧾 Readiness:    {readiness_path.name}")
    print(f"  ✉️  Cover letter: {cover_letter_path.name}")
    print(f"  🔎 Quality:      {quality_report['status']}")
    print("\n  8 PHẦN ĐÃ SINH:")
    print(f"  Phần 1 — ICMJE Tiêu chuẩn Tác giả ({n_authors} tác giả, 4 tiêu chí + CRediT 14 vai trò)")
    print(f"  Phần 2 — Khai báo COI Cuối ({n_authors} form + tuyên bố tập thể)")
    print("  Phần 3 — Data Availability Statement + chi tiết ICMJE cho clinical trial")
    print("  Phần 4 — AI Use Disclosure (ICMJE 01/2026)")
    print("  Phần 5 — Tuyên bố Liêm chính Nghiên cứu (5 điểm)")
    print(f"  Phần 6 — Cover Letter Shell (tạp chí: {target_journal or '[CẦN]'})")
    print("  Phần 7 — Response-to-Reviewers Template")
    print("  Phần 8 — Tiêu chí Cổng G9 (Hard Gate)")
    print(f"\n  🛡️  Guardrail: {guardrail_status}")
    print(f"  📊 Checkpoints đọc được: {', '.join(sorted(cps.keys())) or '(không có)'}")
    print("\n  ⚠️  G9 STATUS: DRAFT — CHỜ KÝ TẤT CẢ TÁC GIẢ")
    print("  KHÔNG nộp bản thảo cho đến khi G9 PASSED.")
    print("\n  VIỆC CÒN LẠI CỦA BÁC SĨ:")
    print("  1. Mở file DOCX, điền TẤT CẢ [CẦN ...]")
    print(f"  2. Tất cả {n_authors} tác giả ký ICMJE + COI (Phần 1-2)")
    print("  3. PI ký Tuyên bố Liêm chính (Phần 5)")
    print(f"  4. Hoàn tất {G9Q.READINESS_JSON} bằng evidence_ref không PII")
    print("  5. Rà similarity theo chính sách tạp chí/cơ sở và phán đoán con người")
    print(f"  6. Chạy: python tools/g9_quality_gate.py --study {study}")
    print("  7. Chỉ khi trạng thái READY, PI tự ký đúng G9_checkpoint.json")
    print("  8. Chạy lại quality gate; chỉ PASS_G9...LOCKED mới được chuyển G10")
    print("\n  Cần bác sĩ kiểm chứng.")
    print(f"{'='*65}\n")


if __name__ == "__main__":
    main()
