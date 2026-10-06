#!/usr/bin/env python3
"""Hợp đồng chất lượng cho cổng G0: CÂU HỎI NGHIÊN CỨU.

LÝ DO MODULE NÀY TỒN TẠI
------------------------
Trước 2026-07-28, G0 là cổng DUY NHẤT trong chuỗi G0–G10 không có hợp đồng chất
lượng riêng (G1 có ``g1_quality_gate.py``, G2 có ``g2_quality_gate.py``). Hệ quả
đo được, không phải suy đoán: chạy ``run_g0_auto.py`` trên một đề tài bất kỳ,
màn hình in **"✅ G0 HOÀN THÀNH"** và tiến trình thoát mã 0 — trong khi mọi ô
P/I/C/O của artifact A1 vẫn nguyên placeholder ``[CẦN BÁC SĨ XÁC NHẬN]``, chưa
có kết cục chính, chưa có giả thuyết, chưa ai đánh giá FINER. Nói cách khác: cổng
KHỞI ĐẦU của một nghiên cứu tuyên bố hoàn thành khi **câu hỏi nghiên cứu chưa
tồn tại**. Đây đúng là kiểu "thành công giả" mà chính docstring của run_g0_auto.py
đã cảnh báo ở một chỗ khác.

Hằng số ``GC.REASON_MISSING_PICO`` ("G0: PICO chưa được xác nhận") đã nằm sẵn
trong ``gate_contract.py`` từ đầu nhưng chưa từng có dòng code nào dùng — bằng
chứng cho thấy tình huống này đã được dự trù mà chưa bao giờ được thực thi.

BA TRẠNG THÁI (cùng ngữ nghĩa với G1/G2 để cả chuỗi đọc nhất quán)
-----------------------------------------------------------------
- ``BLOCKED``: lỗi kỹ thuật/liêm chính — không có bằng chứng thật, guardrail bẩn,
  artifact khuyết, hoặc checkpoint thiếu trường mà cổng sau phụ thuộc.
- ``DRAFT_READY_NEEDS_HUMAN_REVIEW``: phần máy làm được đã đạt; còn chờ bác sĩ
  chốt PICO, kết cục chính, giả thuyết, FINER. **Đây là trạng thái ĐÚNG của một
  lần chạy G0 tự động bình thường** — không phải lỗi.
- ``PASS_G0_CONFIRMED``: bác sĩ đã pin đủ quyết định vào
  ``study_meta.json → gate_params.G0``. Chỉ khi đó mới được nói G0 đã qua.

Nền doctrine: ``.claude/agents/cau-hoi-nghien-cuu.md`` — "Đạt G0 khi: 6 thành
phần hoàn chỉnh · kết cục chính DUY NHẤT đã định nghĩa đo được · FINER đánh giá
từng tiêu chí · thiết kế gợi ý có lý do · bác sĩ xác nhận PICO + kết cục".

GIỚI HẠN PHÁN ĐỊNH: module này KHÔNG thẩm định chất lượng khoa học của câu hỏi.
Nó chỉ kiểm rằng câu hỏi ĐÃ ĐƯỢC MỘT NGƯỜI THẬT VIẾT RA VÀ CHỐT, và rằng nền
bằng chứng máy dựng là thật. Một PICO đầy đủ vẫn có thể là một PICO tồi.

Chạy lại độc lập (sau khi bác sĩ điền study_meta.json, KHÔNG cần gọi lại PubMed):
    python tools/g0_quality_gate.py --study <MÃ-ĐỀ-TÀI>
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

import cong_song as CS  # noqa: E402
import gate_contract as GC  # noqa: E402
import pii_van_ban as PII  # noqa: E402
import pipeline_freshness as PF  # noqa: E402
import placeholder_contract as PC  # noqa: E402
import skill_standards as S  # noqa: E402

STATUS_BLOCKED = "BLOCKED"
STATUS_DRAFT_READY = "DRAFT_READY_NEEDS_HUMAN_REVIEW"
STATUS_CONFIRMED = "PASS_G0_CONFIRMED"

QUALITY_CONTRACT_VERSION = "G0-2026.1"

# Các mục BẮT BUỘC phải hiện diện trong artifact A1 — ánh xạ 1-1 với 6 THÀNH PHẦN
# của doctrine cau-hoi-nghien-cuu.md. Thiếu mục nào = artifact chưa đủ khung để
# bác sĩ điền, nên chặn ở tầng AUTO (lỗi của hệ, không phải của bác sĩ).
REQUIRED_A1_SECTIONS: Sequence[str] = (
    "PICO / PECO",
    "KIỂM FINER",
    "GIẢ THUYẾT",
    "BẰNG CHỨNG HIỆN CÓ",
    "PHÂN TÍCH KHOẢNG TRỐNG",
    "THIẾT KẾ GỢI Ý",
    "TIÊU CHÍ QUA CỔNG G0",
)

# Trường checkpoint mà các cổng sau ĐỌC THẬT (đã grep run_g1..g10, list_studies,
# study_readiness, g1_quality_gate.collect_evidence_identifiers). Thiếu = lệch
# hợp đồng im lặng: cổng sau lùi về mặc định mà không báo gì.
REQUIRED_CHECKPOINT_KEYS: Sequence[str] = (
    "study", "gate", "topic", "base_query",
    "evidence_level", "research_gaps", "design_suggestion",
    "pubmed_results", "guardrail", "artifacts",
)
REQUIRED_PUBMED_KEYS: Sequence[str] = (
    "total_found", "n_pmids", "all_pmids", "n_sr", "n_rct",
    "n_guideline", "n_observational", "n_recent", "counts_are_real",
)

# VÁ 04/10/2026 (soát từng cổng, G0-05): bảng loại câu hỏi RIÊNG của G0 («therapy») lệch bảng của G1 («treatment»)
# và thiếu «qualitative»/«prediction» ⇒ đề tài định tính/dự báo kẹt REVIEW mãi. Nay chuẩn hoá qua bảng DÙNG CHUNG
# skill_standards.chuan_hoa_question_type (therapy ≡ treatment…). «sr» là THIẾT KẾ, không phải loại câu hỏi.
_QUESTION_TYPES_CHAP_NHAN = frozenset({"treatment", "diagnosis", "prognosis", "harm", "descriptive", "qualitative",
                                       "prediction_model"})
# Loại câu hỏi có so sánh/hiệu ứng: test_type «descriptive» với các loại này phải có lý do (G0-06).
_QUESTION_TYPES_CO_GIA_THUYET = frozenset({"treatment", "diagnosis", "prognosis", "harm"})
_TEST_TYPES = {
    "superiority", "non_inferiority", "non-inferiority", "equivalence",
    "descriptive", "mô tả",
}
# Kết luận FINER PHỦ ĐỊNH (G0-03): chỉ cụm phủ định MẠNH, nói thẳng tiêu chí không đạt. KHÔNG bắt «chưa/không» đứng đầu
# câu nói chung — «Chưa có dữ liệu Việt Nam» chính là lý do tính MỚI (đã thử: bắt nhầm). Chiều mơ hồ để bác sĩ đọc.
_FINER_AM = re.compile(
    r"\bkhông\s+(?:khả\s+thi|đạt|phù\s+hợp|đảm\s+bảo\s+đạo\s+đức)\b|\bvi\s+phạm\s+đạo\s+đức\b"
    r"|\bnot\s+(?:feasible|ethical|novel|relevant|interesting)\b|\binfeasible\b|\bunethical\b",
    re.IGNORECASE,
)
# Khoá của gate_params.G0 KHÔNG đưa vào dấu vân tay chốt (là chính phần xác nhận, không phải nội dung được xác nhận).
_KHOA_XAC_NHAN_G0 = frozenset({"pico_confirmed", "evidence_reviewed_confirmed", "reviewed_by_role", "reviewed_at",
                               "dau_van_tay_chot"})
# Vai trò được phép chốt câu hỏi nghiên cứu ở G0. Cố ý KHÁC danh sách của G2
# (IRB) — G0 là quyết định khoa học của chủ nhiệm/nhà phương pháp, không phải
# quyết định đạo đức.
_REVIEW_ROLES = {
    "pi", "principal investigator", "research lead", "methodologist",
    "nhà phương pháp", "chủ nhiệm", "chủ nhiệm đề tài",
}

# Dấu hiệu «chưa điền» RIÊNG của G0 (có từ 2026-07-28) — so CHUỖI CON trên value.upper(), không phân biệt
# hoa/thường. GIỮ NGUYÊN ngữ nghĩa này (03/10/2026): hợp đồng chung `placeholder_contract` hẹp hơn ở vài chỗ
# («CHƯA XÁC NHẬN» chỉ khớp CHỮ HOA; không có «SUY RA TỪ TOPIC» — ô P/I/E của khuôn A1 — hay «XXX»), nên
# vị từ trường của G0 = marker cũ HOẶC hợp đồng chung, không bao giờ thay marker cũ bằng hợp đồng.
# Biết trước (kiểm toán 03/10, mức thấp): «CHƯA XÁC NHẬN»/«XXX» không neo ngoặc nên văn xuôi hợp lệ
# («… chưa xác nhận ở người Việt», «karyotype 47,XXX») bị REVIEW oan — chiều an toàn, chưa nới (cần bác sĩ quyết).
_PLACEHOLDER_MARKERS = (
    "[CẦN", "[REQUIRE_HUMAN", "CHƯA XÁC NHẬN", "[TODO", "___",
    "SUY RA TỪ TOPIC", "XXX",
)

_STANDARDS_BASIS = (
    {
        "standard": "PICO framework",
        "scope": "Khung câu hỏi lâm sàng/nghiên cứu 4 thành phần",
        "pmid": "7582737",
    },
    {
        "standard": "FINER criteria (Hulley, Designing Clinical Research)",
        "scope": "Sàng lọc câu hỏi nghiên cứu: Feasible/Interesting/Novel/Ethical/Relevant",
        "url": "https://www.equator-network.org/library/",
    },
    {
        "standard": "EQUATOR Network",
        "scope": "Bản đồ chuẩn báo cáo theo loại thiết kế (dùng cho chuẩn dự kiến ở G0)",
        "url": "https://www.equator-network.org/library/",
    },
    {
        "standard": "ICMJE Recommendations",
        "scope": "Đăng ký nghiên cứu trước khi tuyển người tham gia đầu tiên",
        "url": "https://www.icmje.org/recommendations/",
    },
)


# ════════════════════════════════════════════════════════════════════════════
# Tiện ích
# ════════════════════════════════════════════════════════════════════════════

def _chuoi_that(value: str) -> bool:
    """Một CHUỖI có nội dung thật không: marker cũ của G0 (nguyên văn) VÀ hợp đồng chung (mọi họ).

    Hợp đồng chung (`PC.co_noi_dung_that`, mặc định MỌI họ vì đây là GIÁ TRỊ TRƯỜNG) bắt thêm những gì đo được
    là lọt G0 tới PASS_G0_CONFIRMED (kiểm toán 03/10/2026, đã chạy): nhãn nháp «[DỰ THẢO — CHỜ BÁC SĨ …]» (có
    thật ở novelty_justification của C1a), ô khung của CHÍNH khuôn A1 «[P — điền]»/«[xem §3 bên dưới]», ô mẫu
    chung «[nơi thực hiện]», «[TO BE COMPLETED]»/«[TBD]»/«[PENDING]»/«<CẦN …>», «[XÁC NHẬN THỦ CÔNG…]»,
    «……», ký hiệu đứng một mình («?», «…», «-») và chuỗi chỉ toàn ô tick «☐ tăng ☐ giảm». Ba chấm ASCII «...»
    trong văn xuôi vẫn hợp lệ (C1a primary_outcome_measure).
    """
    text = value.strip()
    if not text:
        return False
    upper = text.upper()
    if any(marker in upper for marker in _PLACEHOLDER_MARKERS):
        return False
    return PC.co_noi_dung_that(text)


def _present(value: Any) -> bool:
    """Giá trị có NỘI DUNG THẬT không (placeholder không tính là có).

    Danh sách: phải KHÔNG rỗng và MỌI phần tử thật (vá 03/10/2026 — trước đó any(): outcomes
    ["Tử vong tim mạch", "[CẦN BÁC SĨ ẤN ĐỊNH]"] tính là ĐÃ ĐIỀN, G1 thì vốn dùng all()).
    Dict: có ít nhất một giá trị thật VÀ không giá trị nào còn ô trống (khoá để None vẫn được chấp nhận,
    chỉ siết đúng phần dư của khuôn).
    """
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return True
    if isinstance(value, str):
        return _chuoi_that(value)
    if isinstance(value, Mapping):
        return any(_present(v) for v in value.values()) and not _con_o_trong(value)
    if isinstance(value, (list, tuple, set)):
        return bool(value) and all(_present(v) for v in value)
    return True


def _con_o_trong(value: Any) -> bool:
    """True khi giá trị (hoặc một phần tử con) là chuỗi CÓ CHỮ nhưng còn dấu hiệu chưa điền.

    Phân biệt «còn ô trống/nhãn nháp» với «thiếu» (rỗng/None) để bằng chứng báo cáo nói đúng việc bác sĩ phải
    làm: gỡ nhãn/ô mẫu chứ không phải viết từ đầu.
    """
    if isinstance(value, str):
        return bool(value.strip()) and not _chuoi_that(value)
    if isinstance(value, Mapping):
        return any(_con_o_trong(v) for v in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_con_o_trong(v) for v in value)
    return False


def _mo_ta(value: Any) -> str:
    """Nhãn bằng chứng cho một trường: 'có' / 'còn ô trống/nhãn nháp' / 'thiếu'."""
    if _present(value):
        return "có"
    return "còn ô trống/nhãn nháp" if _con_o_trong(value) else "thiếu"


_HANH_DONG_GO_O_TRONG = (
    " Gỡ hết nhãn nháp/ô mẫu còn sót trong trường (vd «[DỰ THẢO…]», «[… — điền]», «___», «☐ … ☐ …») — "
    "hệ KHÔNG tự viết thay."
)


def _g0_meta(meta: Mapping[str, Any]) -> Mapping[str, Any]:
    gp = meta.get("gate_params")
    if not isinstance(gp, Mapping):
        return {}
    g0 = gp.get("G0")
    return g0 if isinstance(g0, Mapping) else {}


def _valid_iso_time(value: Any) -> bool:
    """ISO-8601 thật và KHÔNG ở tương lai (VÁ 04/10/2026, G0-07 + bỏ sót: bản cũ nhận cả «2099-12-31»)."""
    if not _present(value):
        return False
    return CS.iso_khong_tuong_lai(value)


def _finer_ket_luan(value: Any) -> str:
    """Kết luận của MỘT tiêu chí FINER: «dat» · «khong_dat» · «can_ly_do» · «thieu» (VÁ 04/10/2026, G0-03).

    Bản cũ chỉ hỏi «có chữ không»: «KHÔNG KHẢ THI», số 0 hay False đều được tính là «có kết luận» ⇒ PASS. Bool True
    / số trơn không kèm lý do cũng PASS — trong khi F và E là hai tiêu chí máy KHÔNG thể tự đánh giá."""
    if isinstance(value, bool):
        return "can_ly_do" if value else "khong_dat"
    if isinstance(value, (int, float)):
        return "khong_dat" if value == 0 else "can_ly_do"
    if not _present(value):
        return "thieu"
    if _FINER_AM.search(unicodedata.normalize("NFC", str(value))):
        return "khong_dat"
    return "dat"


def dau_van_tay_g0(checkpoint: Mapping[str, Any], meta: Mapping[str, Any]) -> str:
    """Dấu vân tay của NỘI DUNG mà bác sĩ chốt ở G0: chủ đề + tập PMID đã đọc + mọi quyết định trong gate_params.G0
    (trừ chính các khoá xác nhận). Đổi chủ đề, chạy lại PubMed ra PMID khác, hay sửa PICO sau khi chốt ⇒ dấu đổi ⇒
    xác nhận cũ hết hiệu lực (VÁ 04/10/2026, G0-07)."""
    pubmed = checkpoint.get("pubmed_results") if isinstance(checkpoint.get("pubmed_results"), Mapping) else {}
    pmids = sorted(str(x) for x in (pubmed.get("all_pmids") or []))
    g0 = {k: v for k, v in _g0_meta(meta).items() if k not in _KHOA_XAC_NHAN_G0}
    return CS.dau_van_tay(str(checkpoint.get("topic") or ""), pmids, g0)


def _thiet_ke_ghim(meta: Mapping[str, Any]) -> Optional[str]:
    """Mã thiết kế chuỗi bác sĩ ghim (study_meta.design_code hoặc gate_params.G1.design).

    None nếu chưa ghim hoặc ngoài 8 mã chuỗi hỗ trợ."""
    gp = meta.get("gate_params") if isinstance(meta.get("gate_params"), Mapping) else {}
    g1 = gp.get("G1") if isinstance(gp.get("G1"), Mapping) else {}
    raw = meta.get("design_code") or g1.get("design")
    return S.ma_thiet_ke_chuoi(raw) if isinstance(raw, str) else None


def _criterion(criterion_id: str, label: str, status: str,
               evidence: str, action: str = "") -> Dict[str, str]:
    return {
        "id": criterion_id, "label": label, "status": status,
        "evidence": evidence, "action": action,
    }


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _count_unique_primary_outcomes(value: Any) -> int:
    """Đếm số kết cục CHÍNH được khai — doctrine bắt buộc DUY NHẤT 1.

    Chấp nhận chuỗi (1 kết cục) hoặc list. Chuỗi có dấu phân tách kiểu liệt kê
    (";" hoặc " và " hoặc ",") KHÔNG bị coi là nhiều kết cục: nhiều kết cục hợp
    lệ được viết dưới dạng "tỷ lệ tử vong do mọi nguyên nhân, đo tại 30 ngày".
    Chỉ list mới coi là nhiều — nếu bác sĩ thật sự muốn khai 2 kết cục chính thì
    họ sẽ viết list, và đó chính là điều cần chặn.
    """
    if isinstance(value, (list, tuple, set)):
        return len([v for v in value if _present(v)])
    return 1 if _present(value) else 0


# ════════════════════════════════════════════════════════════════════════════
# Chuẩn báo cáo dự kiến từ gợi ý thiết kế của G0
# ════════════════════════════════════════════════════════════════════════════

# G0 chỉ GỢI Ý thiết kế (G1 mới quyết định). Bản đồ này chuyển gợi ý văn xuôi
# tiếng Việt của analyze_evidence_gaps() thành mã canonical để tra chuẩn báo cáo
# dự kiến — doctrine THÀNH PHẦN 5 yêu cầu nêu "Chuẩn báo cáo dự kiến", mà artifact
# A1 trước đây không có dòng nào.
_DESIGN_HINT_PATTERNS: Sequence[tuple[str, str]] = (
    (r"sr\s*/\s*meta|meta-?analysis|tổng quan hệ thống", "sr_ma"),
    (r"\brct\b|ngẫu nhiên có đối chứng|pragmatic trial", "rct"),
    (r"cohort|thuần tập", "cohort"),
    (r"bệnh[- ]chứng|case[- ]control", "case_control"),
    (r"cắt ngang|cross[- ]sectional", "cross_sectional"),
    (r"chẩn đoán|diagnostic|độ chính xác", "diagnostic"),
    (r"tiên lượng|prediction|mô hình dự báo", "prediction"),
    (r"định tính|qualitative", "qualitative"),
)


def infer_design_code_from_hint(design_hint: Optional[str]) -> Optional[str]:
    """Suy mã thiết kế canonical từ câu gợi ý của G0 (None nếu không chắc).

    Cố ý trả None thay vì đoán bừa: chọn sai mã thiết kế kéo theo chọn sai chuẩn
    báo cáo — đúng lỗi đã xảy ra thật ở G2→G3/G4/G6 (xem resolve_design_code).
    """
    text = str(design_hint or "").strip().lower()
    if not text:
        return None
    # RCT xuất hiện cùng "SR/Meta-analysis (tổng hợp RCT hiện có)" → SR thắng vì
    # mẫu SR được duyệt trước; thứ tự trong _DESIGN_HINT_PATTERNS là có chủ ý.
    for pattern, code in _DESIGN_HINT_PATTERNS:
        if re.search(pattern, text):
            return code
    return None


# Loại câu hỏi ⇒ thiết kế CHẮC CHẮN (chỉ những cặp không mơ hồ; «treatment» có thể là RCT hoặc thuần tập ⇒ không suy).
_THIET_KE_THEO_LOAI_CAU_HOI = {
    "descriptive": "cross_sectional", "diagnosis": "diagnostic", "qualitative": "qualitative",
    "prediction_model": "prediction",
}


def expected_reporting_standard(design_hint: Optional[str], meta: Optional[Mapping[str, Any]] = None) -> Dict[str, str]:
    """Gói chuẩn báo cáo DỰ KIẾN cho G0.

    VÁ 04/10/2026 (soát từng cổng, G0-08): bản cũ chỉ suy từ CÂU GỢI Ý của G0 — câu đó gần như luôn là «RCT … HOẶC
    Cohort …», nên đề tài cắt ngang C1a bị ghi chuẩn dự kiến CONSORT 2025/SPIRIT 2025. Thứ tự ưu tiên nay: thiết kế
    bác sĩ ĐÃ GHIM → loại câu hỏi bác sĩ đã khai (chỉ cặp chắc chắn) → câu gợi ý; gợi ý mơ hồ («HOẶC», khớp nhiều
    mã) ⇒ «[CẦN XÁC ĐỊNH Ở G1]», không đoán."""
    meta = meta if isinstance(meta, Mapping) else {}
    code = _thiet_ke_ghim(meta)
    if not code:
        qt = S.chuan_hoa_question_type(_g0_meta(meta).get("question_type"))
        code = _THIET_KE_THEO_LOAI_CAU_HOI.get(qt or "")
    if not code:
        hint = str(design_hint or "")
        so_ma = {c for pattern, c in _DESIGN_HINT_PATTERNS if re.search(pattern, hint.lower())}
        mo_ho = bool(re.search(r"\bHOẶC\b|\bhoặc\b|\bOR\b", hint)) and len(so_ma) > 1
        code = None if mo_ho else infer_design_code_from_hint(design_hint)
    if not code:
        return {
            "design_code": "",
            "primary": "[CẦN XÁC ĐỊNH Ở G1] — tra EQUATOR Network theo thiết kế thật",
            "protocol": "[CẦN XÁC ĐỊNH Ở G1]",
        }
    pack = S.reporting_standards_for(code)
    return {
        "design_code": code,
        "primary": pack.get("primary", ""),
        "protocol": pack.get("protocol", ""),
    }


# ════════════════════════════════════════════════════════════════════════════
# Đánh giá
# ════════════════════════════════════════════════════════════════════════════

def evaluate_g0_quality(
    *,
    checkpoint: Mapping[str, Any],
    meta: Mapping[str, Any],
    artifact_text: str = "",
    artifact_paths: Optional[Mapping[str, Path]] = None,
    guardrail_passed: Optional[bool] = None,
    registry_check: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Chấm G0 theo hai tầng: máy kiểm được vs người thật phải chốt."""
    artifact_paths = artifact_paths or {}
    automatic: List[Dict[str, str]] = []
    human: List[Dict[str, str]] = []

    # ── Tầng AUTO ────────────────────────────────────────────────────────────
    guard = checkpoint.get("guardrail")
    if guardrail_passed is None:
        guardrail_passed = bool(
            isinstance(guard, Mapping) and guard.get("passed") is True
        )
    automatic.append(_criterion(
        "G0-AUTO-00", "Guardrail liêm chính G0 sạch",
        "PASS" if guardrail_passed else "BLOCK",
        f"guardrail_passed={guardrail_passed}",
        "Sửa mọi lỗi R1–R7 (nguồn, PII, vượt cổng, disclaimer) rồi chạy lại G0.",
    ))

    topic = checkpoint.get("topic")
    automatic.append(_criterion(
        "G0-AUTO-01", "Đề tài có chủ đề thật (không rỗng/placeholder)",
        "PASS" if _present(topic) else "BLOCK",
        f"topic={str(topic or '')[:80]!r}",
        "Chạy lại với --topic mô tả đúng vấn đề nghiên cứu.",
    ))

    pubmed = checkpoint.get("pubmed_results")
    pubmed = pubmed if isinstance(pubmed, Mapping) else {}
    n_pmids = pubmed.get("n_pmids")
    n_pmids = int(n_pmids) if isinstance(n_pmids, int) else 0
    automatic.append(_criterion(
        "G0-AUTO-02", "Có bằng chứng THẬT làm nền (≥1 PMID từ PubMed)",
        "PASS" if n_pmids > 0 else "BLOCK",
        f"n_pmids={n_pmids}",
        'Chạy lại với --query-en "<từ khóa tiếng Anh>"; hệ KHÔNG bịa PMID.',
    ))

    # Số hit THẬT (esearch Count) vs số bài lấy về: nếu không phải số thật thì mọi
    # kết luận "khoảng trống" chỉ là ước lượng dưới — không được để nó lặng lẽ đi
    # tiếp dưới nhãn PASS.
    counts_are_real = pubmed.get("counts_are_real")
    unavailable = pubmed.get("counts_unavailable") or []
    automatic.append(_criterion(
        "G0-AUTO-03", "Số hit dùng để kết luận khoảng trống là SỐ THẬT",
        "PASS" if counts_are_real is True else "REVIEW",
        f"counts_are_real={counts_are_real}; nhánh không tra được={list(unavailable)}",
        "Chạy lại G0 khi mạng ổn định; đừng kết luận 'khoảng trống' trên số ước lượng dưới.",
    ))

    # LƯU Ý PHẠM VI (audit tautology vòng 2, 2026-07-31): write_checkpoint()
    # trong run_g0_auto.py in CỨNG đủ 19 khóa này (10 REQUIRED_CHECKPOINT_KEYS
    # + 9 REQUIRED_PUBMED_KEYS) VÔ ĐIỀU KIỆN cho MỌI checkpoint mới do pipeline
    # thật sinh (đã xác nhận thực nghiệm với 4 tổ hợp topic/results khác
    # nhau) — tiêu chí này KHÔNG BAO GIỜ tự phát hiện được nội dung THIẾU CHẤT
    # LƯỢNG cho một checkpoint MỚI. Nó vẫn có giá trị THẬT: bắt checkpoint CŨ/
    # hỏng/sửa tay/ghi bởi writer khác (đã xác nhận: checkpoint bị xoá tay 1
    # khóa → BLOCK đúng) — đây là kiểm SCHEMA/toàn vẹn, không phải thước đo
    # chất lượng câu hỏi nghiên cứu cho đề tài cụ thể (việc đó thuộc
    # G0-HUMAN-01..07, đọc study_meta.json).
    missing_cp = [k for k in REQUIRED_CHECKPOINT_KEYS if k not in checkpoint]
    missing_pm = [k for k in REQUIRED_PUBMED_KEYS if k not in pubmed]
    cp_problems = (
        [f"checkpoint thiếu: {', '.join(missing_cp)}"] if missing_cp else []
    ) + (
        [f"pubmed_results thiếu: {', '.join(missing_pm)}"] if missing_pm else []
    )
    automatic.append(_criterion(
        "G0-AUTO-04", "Checkpoint đủ trường hợp đồng cho cổng sau đọc",
        "BLOCK" if cp_problems else "PASS",
        "; ".join(cp_problems) if cp_problems else
        f"{len(REQUIRED_CHECKPOINT_KEYS)} khóa gốc + "
        f"{len(REQUIRED_PUBMED_KEYS)} khóa pubmed_results đầy đủ",
        "Chạy lại G0 bản hiện hành để ghi checkpoint đúng schema.",
    ))

    # LƯU Ý PHẠM VI (audit tautology vòng 2, 2026-07-31): 7 tiêu đề mục trong
    # REQUIRED_A1_SECTIONS là header markdown TĨNH được generate_a1_artifact()
    # in CỨNG VÔ ĐIỀU KIỆN — không phụ thuộc topic/gaps/results (đã xác nhận
    # thực nghiệm nhiều tổ hợp topic×results, không case nào thiếu mục). Tiêu
    # chí này chỉ có khả năng BLOCK thật khi artifact bị TRUNCATE/tampering
    # SAU khi file .md đã ghi ra đĩa (đã xác nhận: cắt tay 1 header → BLOCK
    # đúng) — không phải thước đo bác sĩ đã điền PICO/FINER/giả thuyết đủ nội
    # dung hay chưa (việc đó thuộc G0-HUMAN-01..07).
    missing_sections = [
        s for s in REQUIRED_A1_SECTIONS
        if s.casefold() not in (artifact_text or "").casefold()
    ]
    if not (artifact_text or "").strip():
        art_status, art_evidence = "BLOCK", "Không đọc được artifact A1"
    elif missing_sections:
        art_status = "BLOCK"
        art_evidence = f"A1 thiếu mục: {', '.join(missing_sections)}"
    else:
        art_status = "PASS"
        art_evidence = f"A1 có đủ {len(REQUIRED_A1_SECTIONS)} mục bắt buộc"
    automatic.append(_criterion(
        "G0-AUTO-05", "Artifact A1 có đủ 6 thành phần theo doctrine",
        art_status, art_evidence,
        "Sinh lại A1 bằng run_g0_auto.py bản hiện hành.",
    ))

    # Trùng lặp nghiên cứu: PubMed trả lời "đã CÔNG BỐ gì", không trả lời "đang có
    # ai LÀM chưa". Thiếu vế sau, bác sĩ có thể khởi động một đề tài trùng hoàn
    # toàn với thử nghiệm đang tuyển bệnh.
    # VÁ 04/10/2026 (soát từng cổng, G0-02): bộ sinh (trial_registry) ghi `n_active`, bộ chấm từng đọc `n_recruiting`
    # ⇒ báo cáo luôn nói «0 đang tuyển» — một số 0 BỊA. Đọc n_active (n_recruiting là bí danh cũ); không phải số
    # nguyên ⇒ «không rõ», KHÔNG ép thành 0.
    n_active: Optional[int] = None
    if isinstance(registry_check, Mapping) and registry_check:
        checked = registry_check.get("checked") is True
        n_trials = registry_check.get("n_trials")
        n_trials_txt = str(n_trials) if isinstance(n_trials, int) and not isinstance(n_trials, bool) else "không rõ số"
        raw_active = registry_check.get("n_active", registry_check.get("n_recruiting"))
        if isinstance(raw_active, int) and not isinstance(raw_active, bool):
            n_active = raw_active
        reg_status = "PASS" if checked else "REVIEW"
        reg_evidence = (
            f"ClinicalTrials.gov: {n_trials_txt} hồ sơ khớp, "
            + (f"{n_active} đang tuyển" if n_active is not None else "không rõ số đang tuyển")
            if checked else
            f"chưa tra được ({registry_check.get('error') or 'không rõ lý do'})"
        )
    else:
        reg_status = "REVIEW"
        reg_evidence = "chưa tra đăng ký nghiên cứu"
    automatic.append(_criterion(
        "G0-AUTO-06", "Đã tra ClinicalTrials.gov (chủ yếu phủ thử nghiệm can thiệp; ICTRP/PROSPERO ở G0-HUMAN-08)",
        reg_status, reg_evidence,
        "Chạy lại G0 khi có mạng, hoặc tự tra ClinicalTrials.gov/WHO ICTRP "
        "trước khi khẳng định đề tài là mới.",
    ))

    # VÁ 04/10/2026 (soát từng cổng, G0-09 / CHUNG-G): không cổng nào quét PII trên chính các trường bác sĩ GÕ TAY ở
    # gate_params.G0 — số điện thoại hay CCCD dán vào population vẫn PASS. Quét bằng bộ dò dùng chung (chế độ «chat»),
    # bỏ mẫu «ngày tháng cụ thể» (thời gian nghiên cứu là hợp lệ ở đây) nhưng giữ «ngày sinh» + một ngày (chế độ
    # «ho_so»). Bằng chứng chỉ nêu TÊN KHOÁ, không in giá trị.
    khoa_pii: List[str] = []
    g0_quet = {k: v for k, v in _g0_meta(meta).items() if k not in _KHOA_XAC_NHAN_G0}
    g0_quet["topic (checkpoint)"] = checkpoint.get("topic")
    for khoa, gia_tri in g0_quet.items():
        if isinstance(gia_tri, bool) or gia_tri is None:
            continue
        thay = [x for x in PII.quet_pii_van_ban(gia_tri, che_do=PII.CHAT) if x.loai != "ngày tháng cụ thể"]
        thay += [x for x in PII.quet_pii_van_ban(gia_tri, che_do=PII.HO_SO) if x.loai == "ngày sinh cụ thể"]
        if thay:
            khoa_pii.append(f"{khoa} ({', '.join(sorted({x.loai for x in thay}))})")
    automatic.append(_criterion(
        "G0-AUTO-07", "Trường bác sĩ điền ở gate_params.G0 không chứa thông tin định danh",
        "BLOCK" if khoa_pii else "PASS",
        ("nghi PII ở: " + "; ".join(khoa_pii)) if khoa_pii else "không thấy mẫu PII trong gate_params.G0 + chủ đề",
        "Xoá thông tin định danh khỏi các khoá đã nêu (tên, SĐT, CCCD, BHYT, ngày sinh, email) — chỉ mô tả quần thể ở "
        "mức nhóm.",
    ))

    # ── Tầng HUMAN — đọc study_meta.json → gate_params.G0 ─────────────────────
    g0 = _g0_meta(meta)
    dau_hien_tai = dau_van_tay_g0(checkpoint, meta)

    pico_fields = {
        "population": g0.get("population"),
        "intervention": g0.get("intervention"),
        "comparison": g0.get("comparison"),
        "outcomes": g0.get("outcomes"),
    }
    pico_missing = [k for k, v in pico_fields.items() if not _present(v)]
    pico_residue = [k for k in pico_missing if _con_o_trong(pico_fields[k])]
    human.append(_criterion(
        "G0-HUMAN-01", "PICO/PECO đủ 4 thành phần do bác sĩ viết",
        "PASS" if not pico_missing else "REVIEW",
        (
            f"thiếu: {', '.join(pico_missing)}"
            + (f" (còn ô trống/nhãn nháp: {', '.join(pico_residue)})" if pico_residue else "")
        ) if pico_missing else "P/I/C/O đều có nội dung",
        "Điền gate_params.G0.population/intervention/comparison/outcomes "
        "trong study_meta.json (ghi 'không có nhóm so sánh — mô tả' nếu đúng vậy)."
        + (_HANH_DONG_GO_O_TRONG if pico_residue else ""),
    ))

    primary_raw = g0.get("primary_outcome")
    n_primary = _count_unique_primary_outcomes(primary_raw)
    # Vá 03/10/2026: list ["Kết cục thật", "[CẦN …]"] từng đếm = 1 kết cục ⇒ PASS dù còn ô trống.
    primary_residue = _con_o_trong(primary_raw)
    measure_ok = _present(g0.get("primary_outcome_measure"))
    timepoint_ok = _present(g0.get("primary_outcome_timepoint"))
    po_residue = primary_residue or any(
        _con_o_trong(g0.get(k)) for k in ("primary_outcome_measure", "primary_outcome_timepoint")
    )
    if n_primary == 1 and measure_ok and timepoint_ok and not primary_residue:
        po_status = "PASS"
        po_evidence = "1 kết cục chính, có thang đo và thời điểm đo"
    elif n_primary > 1:
        po_status = "REVIEW"
        po_evidence = (
            f"khai {n_primary} kết cục CHÍNH — doctrine yêu cầu DUY NHẤT 1 "
            "(các kết cục còn lại chuyển sang outcomes phụ)"
        )
    else:
        po_status = "REVIEW"
        po_evidence = (
            f"primary_outcome={'còn ô trống/nhãn nháp' if primary_residue else ('có' if n_primary else 'thiếu')}; "
            f"thang đo={_mo_ta(g0.get('primary_outcome_measure'))}; "
            f"thời điểm đo={_mo_ta(g0.get('primary_outcome_timepoint'))}"
        )
    human.append(_criterion(
        "G0-HUMAN-02", "Kết cục CHÍNH duy nhất, đo được, có thời điểm",
        po_status, po_evidence,
        "Điền primary_outcome (1 kết cục) + primary_outcome_measure + "
        "primary_outcome_timepoint." + (_HANH_DONG_GO_O_TRONG if po_residue else ""),
    ))

    h0_ok = _present(g0.get("hypothesis_h0"))
    h1_ok = _present(g0.get("hypothesis_h1"))
    dir_ok = _present(g0.get("expected_direction"))
    test_type = str(g0.get("test_type") or "").strip().lower()
    test_ok = test_type in _TEST_TYPES
    # Nghiên cứu mô tả không cần H0/H1 — ép có giả thuyết ở đây sẽ đẩy bác sĩ
    # đến chỗ bịa một giả thuyết cho một đề tài mô tả thuần.
    descriptive = test_type in {"descriptive", "mô tả"}
    # VÁ 04/10/2026 (soát từng cổng, G0-06): loại câu hỏi có so sánh/hiệu ứng (điều trị, chẩn đoán, tiên lượng, tác
    # hại) mà khai test_type «descriptive» thì bỏ qua được giả thuyết mà vẫn PASS — nay phải có lý do bằng chữ.
    qtype_canon = S.chuan_hoa_question_type(g0.get("question_type"))
    can_ly_do_mo_ta = descriptive and qtype_canon in _QUESTION_TYPES_CO_GIA_THUYET
    ly_do_mo_ta_ok = _present(g0.get("descriptive_justification"))
    hypo_ok = test_ok and (descriptive or (h0_ok and h1_ok and dir_ok)) and (not can_ly_do_mo_ta or ly_do_mo_ta_ok)
    hypo_residue = not descriptive and any(
        _con_o_trong(g0.get(k)) for k in ("hypothesis_h0", "hypothesis_h1", "expected_direction")
    )
    human.append(_criterion(
        "G0-HUMAN-03", "Giả thuyết H0/H1 + chiều kỳ vọng + loại kiểm định",
        "PASS" if hypo_ok else "REVIEW",
        f"test_type={test_type or 'thiếu'}; H0={_mo_ta(g0.get('hypothesis_h0'))}; "
        f"H1={_mo_ta(g0.get('hypothesis_h1'))}; chiều={_mo_ta(g0.get('expected_direction'))}"
        + (f"; loại câu hỏi «{qtype_canon}» + kiểm định mô tả ⇒ lý do={_mo_ta(g0.get('descriptive_justification'))}"
           if can_ly_do_mo_ta else ""),
        "Điền test_type (superiority/non_inferiority/equivalence/descriptive); "
        "nếu không phải nghiên cứu mô tả thì điền cả hypothesis_h0/h1 và "
        "expected_direction." + (_HANH_DONG_GO_O_TRONG if hypo_residue and not hypo_ok else "")
        + (" Câu hỏi điều trị/chẩn đoán/tiên lượng/tác hại mà chỉ mô tả: viết descriptive_justification."
           if can_ly_do_mo_ta and not ly_do_mo_ta_ok else ""),
    ))

    qtype = str(g0.get("question_type") or "").strip()
    qtype_ok = qtype_canon in _QUESTION_TYPES_CHAP_NHAN
    human.append(_criterion(
        "G0-HUMAN-04", "Loại câu hỏi đã xác định",
        "PASS" if qtype_ok else "REVIEW",
        f"question_type={qtype or 'thiếu'}" + (f" (chuẩn hoá: {qtype_canon})" if qtype_canon else "")
        + (" — «sr» là THIẾT KẾ, không phải loại câu hỏi" if qtype_canon == "sr" else ""),
        "Điền question_type: treatment (≡ therapy)/diagnosis/prognosis/harm/descriptive/qualitative/prediction_model.",
    ))

    finer_keys = ("finer_feasible", "finer_interesting", "finer_novel",
                  "finer_ethical", "finer_relevant")
    finer_kl = {k: _finer_ket_luan(g0.get(k)) for k in finer_keys}
    finer_missing = [k for k, kl in finer_kl.items() if kl == "thieu"]
    finer_residue = [k for k in finer_missing if _con_o_trong(g0.get(k))]
    finer_am = [k for k, kl in finer_kl.items() if kl == "khong_dat"]
    finer_tron = [k for k, kl in finer_kl.items() if kl == "can_ly_do"]

    def _ten(ds: List[str]) -> str:
        return ", ".join(k.replace("finer_", "") for k in ds)

    phan_finer = []
    if finer_am:
        phan_finer.append(f"kết luận KHÔNG ĐẠT/phủ định ở: {_ten(finer_am)}")
    if finer_missing:
        phan_finer.append(f"thiếu: {_ten(finer_missing)}"
                          + (f" (còn ô trống/nhãn nháp: {_ten(finer_residue)})" if finer_residue else ""))
    if finer_tron:
        phan_finer.append(f"chỉ có cờ đúng/số, chưa có lý do: {_ten(finer_tron)}")
    human.append(_criterion(
        "G0-HUMAN-05", "FINER đánh giá đủ từng tiêu chí (5/5), kết luận ĐẠT và có lý do",
        "PASS" if not phan_finer else "REVIEW",
        "; ".join(phan_finer) if phan_finer else "5/5 tiêu chí có kết luận đạt kèm lý do",
        "Viết cho mỗi khoá finer_* một câu kết luận + lý do (F và E máy KHÔNG thể tự đánh giá). Tiêu chí KHÔNG ĐẠT ⇒ "
        "đổi câu hỏi nghiên cứu, hoặc ghi rõ vì sao vẫn chấp nhận." + (_HANH_DONG_GO_O_TRONG if finer_residue else ""),
    ))

    evidence_reviewed = g0.get("evidence_reviewed_confirmed") is True
    novelty = g0.get("novelty_justification")
    novelty_ok = _present(novelty)
    human.append(_criterion(
        "G0-HUMAN-06", "Đã đọc lại bằng chứng G0 và biện minh tính mới",
        "PASS" if (evidence_reviewed and novelty_ok) else "REVIEW",
        f"evidence_reviewed_confirmed={evidence_reviewed}; "
        f"novelty_justification={_mo_ta(novelty)}",
        "Đọc danh sách PMID ở §3 của A1, rồi đặt evidence_reviewed_confirmed=true "
        "và viết novelty_justification." + (_HANH_DONG_GO_O_TRONG if _con_o_trong(novelty) else ""),
    ))

    role = str(g0.get("reviewed_by_role") or "").strip().casefold()
    pico_confirmed = g0.get("pico_confirmed") is True
    # VÁ 04/10/2026 (soát từng cổng, G0-07 / CHUNG-C): xác nhận phải GẮN với nội dung được xác nhận — đổi chủ đề,
    # chạy lại PubMed hay sửa PICO sau khi chốt mà vẫn PASS là lỗi; reviewed_at ở tương lai cũng không nhận.
    xn_ok, xn_ly_do = CS.xac_nhan_gan_noi_dung(
        {"reviewed_at": g0.get("reviewed_at"), "dau_van_tay": g0.get("dau_van_tay_chot")}, dau_hien_tai)
    sign_ok = pico_confirmed and role in _REVIEW_ROLES and _valid_iso_time(g0.get("reviewed_at")) and xn_ok
    human.append(_criterion(
        "G0-HUMAN-07", "Chủ nhiệm/nhà phương pháp chốt PICO (vai trò + thời điểm + gắn đúng nội dung)",
        "PASS" if sign_ok else "REVIEW",
        f"pico_confirmed={pico_confirmed}; vai trò={role or 'thiếu'}; "
        f"reviewed_at={g0.get('reviewed_at') or 'thiếu'}; {xn_ly_do}",
        "Đặt pico_confirmed=true, reviewed_by_role (PI/chủ nhiệm/methodologist), reviewed_at dạng ISO-8601 (không ở "
        f"tương lai) và dau_van_tay_chot=\"{dau_hien_tai}\" (dấu của nội dung đang chốt). Không cần lưu danh tính.",
    ))

    # VÁ 04/10/2026 (soát từng cổng, G0-04 / QĐ-17 — mặc định an toàn chờ bác sĩ duyệt qua PR): G0 chỉ tự tra
    # ClinicalTrials.gov (chủ yếu thử nghiệm can thiệp). WHO ICTRP (gồm đăng ký quan sát, các registry quốc gia) và
    # PROSPERO (tổng quan hệ thống) phải do PI tự tra rồi ghi ngày; có thử nghiệm ĐANG TUYỂN khớp ⇒ PI viết đánh giá
    # chồng lấn. Máy KHÔNG gọi thêm mạng ở đây.
    tra_tay = g0.get("registry_manual_checked") if isinstance(g0.get("registry_manual_checked"), Mapping) else {}
    can_prospero = _thiet_ke_ghim(meta) == "sr_ma"
    thieu_tra = []
    if not _valid_iso_time(tra_tay.get("ictrp")):
        thieu_tra.append("ictrp")
    if can_prospero and not _valid_iso_time(tra_tay.get("prospero")):
        thieu_tra.append("prospero")
    can_chong_lan = isinstance(n_active, int) and n_active > 0
    chong_lan_ok = (not can_chong_lan) or _present(g0.get("registry_overlap_assessment"))
    human.append(_criterion(
        "G0-HUMAN-08", "PI đã tự tra WHO ICTRP (và PROSPERO cho tổng quan) + đánh giá chồng lấn khi có thử nghiệm "
        "đang tuyển",
        "PASS" if not thieu_tra and chong_lan_ok else "REVIEW",
        ("thiếu ngày tra (ISO, không ở tương lai): " + ", ".join(thieu_tra) if thieu_tra else "đã ghi ngày tra")
        + ("" if chong_lan_ok else f"; ClinicalTrials.gov có {n_active} thử nghiệm đang tuyển khớp — thiếu "
           "registry_overlap_assessment"),
        "Tự tra WHO ICTRP (trialsearch.who.int) — và PROSPERO nếu là tổng quan hệ thống — rồi ghi "
        "gate_params.G0.registry_manual_checked = {\"ictrp\": \"YYYY-MM-DD\", \"prospero\": \"YYYY-MM-DD\"}; có thử "
        "nghiệm đang tuyển khớp ⇒ viết registry_overlap_assessment (khác biệt/chồng lấn).",
    ))

    # ── Kết luận ─────────────────────────────────────────────────────────────
    auto_blocked = any(row["status"] == "BLOCK" for row in automatic)
    auto_review = any(row["status"] == "REVIEW" for row in automatic)
    human_complete = all(row["status"] == "PASS" for row in human)

    if auto_blocked:
        status = STATUS_BLOCKED
    elif auto_review or not human_complete:
        status = STATUS_DRAFT_READY
    else:
        status = STATUS_CONFIRMED

    pending = [
        row["action"] for row in automatic + human
        if row["status"] != "PASS" and row.get("action")
    ]

    manifest: Dict[str, Dict[str, str]] = {}
    for key, path in artifact_paths.items():
        p = Path(path)
        if p.exists():
            manifest[key] = {
                "path": str(p),
                "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
            }

    report: Dict[str, Any] = {
        "schema_version": "1.0",
        "contract_version": QUALITY_CONTRACT_VERSION,
        "status": status,
        "automated_checks_passed": not auto_blocked,
        "human_confirmation_complete": human_complete,
        "automatic_criteria": automatic,
        "human_criteria": human,
        "pending_actions": pending,
        "artifact_manifest": manifest,
        "standards_basis": list(_STANDARDS_BASIS),
        "expected_reporting_standard": expected_reporting_standard(
            checkpoint.get("design_suggestion"), meta
        ),
        "dau_van_tay_hien_tai": dau_hien_tai,
        "scope_statement": (
            "PASS_G0_CONFIRMED chỉ xác nhận rằng câu hỏi nghiên cứu ĐÃ ĐƯỢC MỘT "
            "NGƯỜI THẬT VIẾT RA VÀ CHỐT, và nền bằng chứng máy dựng là thật. "
            "KHÔNG thẩm định chất lượng khoa học của câu hỏi, không thay tổng quan "
            "y văn có hệ thống, không thay Hội đồng Đạo đức. Một PICO đầy đủ vẫn "
            "có thể là một PICO tồi."
        ),
    }

    # needs_input máy-đọc-được cho pipeline: chỉ khi phần máy đã sạch mà người
    # thật chưa chốt — đây là lần đầu REASON_MISSING_PICO được dùng thật.
    if status == STATUS_DRAFT_READY and not human_complete:
        report["needs_input"] = GC.needs_input(
            GC.REASON_MISSING_PICO,
            "G0 đã dựng xong NỀN BẰNG CHỨNG nhưng CÂU HỎI NGHIÊN CỨU chưa được "
            "bác sĩ chốt (PICO/kết cục chính/FINER còn trống). Hệ KHÔNG tự viết "
            "PICO thay bác sĩ.",
            "sửa exports/<study>/study_meta.json → gate_params.G0 rồi chạy: "
            "python tools/g0_quality_gate.py --study <study>",
            must_not_fabricate=["PICO", "primary_outcome", "FINER", "hypothesis"],
            study_meta_patch={"gate_params": {"G0": {"pico_confirmed": True}}},
        )
    return report


# ════════════════════════════════════════════════════════════════════════════
# Báo cáo
# ════════════════════════════════════════════════════════════════════════════

def write_quality_report(study: str, out_dir: Path,
                         report: Mapping[str, Any]) -> Path:
    """Ghi báo cáo G0 (JSON máy đọc + Markdown bác sĩ đọc)."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "G0_QUALITY_REPORT.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    def _rows(key: str) -> List[str]:
        out = []
        for row in report.get(key, []):
            out.append(
                f"| {row['id']} | {row['label']} | {row['status']} | "
                f"{str(row['evidence']).replace('|', '/')} |"
            )
        return out

    lines = [
        f"# BÁO CÁO CHẤT LƯỢNG G0 — {study}",
        "",
        f"**Trạng thái:** `{report['status']}`  ·  "
        f"**Hợp đồng:** `{report.get('contract_version', '')}`",
        "",
        "> G0 = cổng CÂU HỎI NGHIÊN CỨU. `DRAFT_READY_NEEDS_HUMAN_REVIEW` là kết quả",
        "> ĐÚNG của một lần chạy tự động — không phải lỗi. Chỉ `PASS_G0_CONFIRMED`",
        "> mới có nghĩa câu hỏi đã được người thật chốt.",
        "",
        "## Kiểm tra tự động (máy làm được)",
        "| Mã | Tiêu chí | Trạng thái | Bằng chứng |",
        "|---|---|---|---|",
        *_rows("automatic_criteria"),
        "",
        "## Xác nhận người thật (bác sĩ phải chốt)",
        "| Mã | Tiêu chí | Trạng thái | Bằng chứng |",
        "|---|---|---|---|",
        *_rows("human_criteria"),
    ]

    pending = report.get("pending_actions") or []
    if pending:
        lines.extend(["", "## Việc còn lại trước khi được ghi PASS_G0_CONFIRMED"])
        lines.extend(f"{i}. {a}" for i, a in enumerate(pending, 1))

    std = report.get("expected_reporting_standard") or {}
    if std:
        lines.extend([
            "",
            "## Chuẩn báo cáo DỰ KIẾN (G1 quyết định chính thức)",
            f"- Mã thiết kế suy từ gợi ý G0: `{std.get('design_code') or '[chưa suy được]'}`",
            f"- Chuẩn báo cáo: {std.get('primary', '')}",
            f"- Chuẩn đề cương: {std.get('protocol', '')}",
        ])

    manifest = report.get("artifact_manifest") or {}
    if manifest:
        lines.extend([
            "",
            "## Manifest artifact",
            "| Artifact | Đường dẫn | SHA-256 |",
            "|---|---|---|",
        ])
        for key, item in manifest.items():
            lines.append(
                f"| {key} | {str(item['path']).replace('|', '/')} | `{item['sha256']}` |"
            )

    lines.extend([
        "",
        "## Nền chuẩn",
        "| Chuẩn | Phạm vi | PMID/DOI/URL |",
        "|---|---|---|",
    ])
    for item in report.get("standards_basis", []):
        source = f"PMID:{item['pmid']}" if item.get("pmid") else ""
        if item.get("doi"):
            source = f"{source}; DOI:{item['doi']}".strip("; ")
        if item.get("url"):
            source = f"{source}; {item['url']}".strip("; ")
        lines.append(
            f"| {item['standard']} | {item['scope']} | {source.replace('|', '/')} |"
        )

    lines.extend([
        "",
        "## Giới hạn phán định",
        str(report.get("scope_statement") or ""),
        "",
        "> Cần bác sĩ kiểm chứng.",
    ])

    md_path = out_dir / "G0_QUALITY_REPORT.md"
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return md_path


def refresh_checkpoint(*, study: str, out_dir: Path,
                       report: Mapping[str, Any]) -> Path:
    """Đồng bộ G0_checkpoint.json['quality_gate'] khi chấm ĐỘC LẬP.

    SỬA 2026-07-30 (audit toàn diện G0-G10, G0-04 — MEDIUM): trước đây CHỈ
    run_g0_auto.py (một lượt CHẠY LẠI TOÀN BỘ, kể cả gọi lại PubMed tốn thời
    gian) mới ghi ``cp["quality_gate"]``. Doctrine + docstring module này đều
    hướng dẫn bác sĩ, sau khi điền study_meta.json, chạy ĐỘC LẬP
    ``python tools/g0_quality_gate.py --study <MÃ>`` để chấm lại "không cần
    gọi lại PubMed" — nhưng đường đó chỉ ghi G0_QUALITY_REPORT.json/.md, để
    checkpoint đứng yên ở giá trị CŨ. Bất kỳ công cụ nào đọc trực tiếp
    checkpoint (đài kiểm soát, study_readiness.py) sẽ thấy dữ liệu lỗi thời.
    """
    out_dir = Path(out_dir)
    checkpoint_path = out_dir / "G0_checkpoint.json"
    checkpoint = _read_json(checkpoint_path)
    # Vá 2026-09-06 (audit vòng 33, phát hiện #1 — CRITICAL): mọi cổng chị em
    # (G1/G2/G3/G4/G5/G8/G9) ghi "quality_contract_version" Ở CẤP CAO NHẤT của
    # checkpoint (sibling của "quality_gate"), và tools/g10_quality_gate.py
    # (G10-AUTO-02B) đọc ĐÚNG khóa cấp cao đó để quyết định checkpoint có
    # "hiện hành" hay "lịch sử" (legacy). Trước bản vá, G0 CHỈ ghi
    # "contract_version" LỒNG bên trong "quality_gate" — không bao giờ có khóa
    # cấp cao — nên G10 luôn xếp G0 vào legacy_quality dù đề tài đã
    # PASS_G0_CONFIRMED thật, khiến modern_quality_ok/non_pi_pending không bao
    # giờ đạt và G10 KHÔNG BAO GIỜ đạt READY_FOR_G10_PI_RELEASE_APPROVAL cho
    # bất kỳ đề tài nào — cổng phát hành cuối cùng bị chặn oan vĩnh viễn.
    checkpoint["quality_contract_version"] = QUALITY_CONTRACT_VERSION
    checkpoint["quality_gate"] = {
        "status": report["status"],
        "contract_version": report.get("contract_version"),
        "automated_checks_passed": report.get("automated_checks_passed"),
        "human_confirmation_complete": report.get("human_confirmation_complete"),
        "pending_actions": report.get("pending_actions", []),
        # VÁ 04/10/2026 (G0-01): dấu nội dung lúc chấm — cổng sau so với dấu hiện tại để biết bản lưu đã cũ.
        "dau_van_tay_luc_cham": report.get("dau_van_tay_hien_tai"),
    }
    # Không để needs_input (PICO chưa chốt) ghi đè needs_input NẶNG HƠN đã có
    # (0 PMID) — mirror đúng guard `if not blocked and ...` của run_g0_auto.py.
    existing = checkpoint.get("needs_input")
    existing = existing if isinstance(existing, dict) else {}
    existing_reason = existing.get("reason_code")
    already_blocked_on_pubmed = existing_reason == GC.REASON_MISSING_PUBMED
    if report.get("needs_input") and not already_blocked_on_pubmed:
        checkpoint["needs_input"] = report["needs_input"]
    elif (report.get("status") == STATUS_CONFIRMED and existing.get("blocked")
          and existing_reason == GC.REASON_MISSING_PICO):
        # SỬA 02/09/2026 (kiểm chi tiết 5 trục, lần chạy đầu trên C1a): bác sĩ đã chốt
        # PICO — hợp đồng trả PASS_G0_CONFIRMED — nhưng cờ chặn MISSING_PICO từ lượt chạy
        # đầu vẫn nằm lại trong checkpoint ⇒ GC.is_blocked() vẫn True, đài kiểm soát
        # (audit_research_gates) vẫn đòi "chốt PICO" và study_readiness/kiểm chi tiết nói
        # ngược nhau về CÙNG một cổng. Hai lớp kể hai chuyện. Giữ bản ghi để truy vết,
        # chỉ gỡ cờ chặn và ghi rõ ai/khi nào gỡ. Cờ MISSING_PUBMED KHÔNG gỡ ở đây —
        # 0 PMID không thể được "xác nhận" qua.
        checkpoint["needs_input"] = {
            **existing, "blocked": False,
            "resolved_by": "g0_quality_gate.refresh_checkpoint",
            "resolved_at": datetime.now().isoformat(timespec="seconds"),
        }
    PF.ghi_checkpoint_giu_moc_sinh(checkpoint_path, json.dumps(checkpoint, ensure_ascii=False, indent=2))
    return checkpoint_path


def evaluate_study(study: str, out_dir: Path, *, write: bool = True) -> Dict[str, Any]:
    """Chấm lại G0 từ các file đã có — KHÔNG gọi lại PubMed.

    Đây là đường bác sĩ dùng sau khi điền study_meta.json: không phải chờ 30 giây
    tìm kiếm lại chỉ để biết mình đã điền đủ chưa.
    """
    out_dir = Path(out_dir)
    checkpoint = _read_json(out_dir / "G0_checkpoint.json")
    meta = _read_json(out_dir / "study_meta.json")

    artifact_path = out_dir / f"G0_A1_PICO_FINER_{study}.md"
    if not artifact_path.exists():
        found = sorted(out_dir.glob("G0_A1_PICO_FINER_*.md"))
        artifact_path = found[0] if found else artifact_path
    try:
        artifact_text = artifact_path.read_text(encoding="utf-8")
    except OSError:
        artifact_text = ""

    report = evaluate_g0_quality(
        checkpoint=checkpoint,
        meta=meta,
        artifact_text=artifact_text,
        artifact_paths={"A1": artifact_path} if artifact_path.exists() else {},
        registry_check=checkpoint.get("registry_check"),
    )
    if write:
        write_quality_report(study, out_dir, report)
        refresh_checkpoint(study=study, out_dir=out_dir, report=report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Chấm lại cổng G0 từ artifact + study_meta đã có (không gọi PubMed)."
    )
    parser.add_argument("--study", required=True, help="Mã đề tài (tên thư mục exports/<study>)")
    parser.add_argument("--exports-dir", default="exports", help="Thư mục gốc exports")
    parser.add_argument("--no-write", action="store_true", help="Chỉ in, không ghi báo cáo")
    args = parser.parse_args()
    GC.ensure_utf8_stdout()

    out_dir = Path(args.exports_dir) / args.study
    if not out_dir.exists():
        print(f"🚧 Không thấy thư mục đề tài: {out_dir}")
        return GC.EXIT_BLOCKED

    report = evaluate_study(args.study, out_dir, write=not args.no_write)

    print(f"\n{'='*65}")
    print(f"  CHẤT LƯỢNG G0 — {args.study}")
    print(f"{'='*65}")
    for row in report["automatic_criteria"] + report["human_criteria"]:
        icon = {"PASS": "✅", "REVIEW": "🟡", "BLOCK": "🔴"}.get(row["status"], "•")
        print(f"  {icon} {row['id']}  {row['label']}")
        print(f"       {row['evidence']}")
    print(f"\n  → Trạng thái: {report['status']}")
    if report["pending_actions"]:
        print("\n  VIỆC CÒN LẠI TRƯỚC KHI ĐƯỢC GHI PASS_G0_CONFIRMED:")
        for i, action in enumerate(report["pending_actions"], 1):
            print(f"  {i}. {action}")
    print("\n  Cần bác sĩ kiểm chứng.")
    print(f"{'='*65}\n")

    if report["status"] == STATUS_BLOCKED:
        return GC.EXIT_GUARDRAIL_FAIL
    if report["status"] == STATUS_DRAFT_READY:
        return GC.EXIT_BLOCKED
    return GC.EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
