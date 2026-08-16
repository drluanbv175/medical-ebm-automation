#!/usr/bin/env python3
"""Hợp đồng chất lượng cho pipeline G1: Thiết kế và nền đề cương.

G1 có hai tầng khác nhau:

1. Tầng tự động: sinh đủ artifact, kiểm thiết kế, chuẩn báo cáo, truy nguyên
   bằng chứng và tính nhất quán kỹ thuật.
2. Tầng xác nhận phương pháp: PI/methodologist chốt thiết kế, mục tiêu, kết cục,
   quần thể, tính khả thi và đã đọc lại bằng chứng.

Không được dùng việc "đã sinh file" thay cho kết luận G1 đã qua. Module trả một
trong ba trạng thái:

- BLOCKED: lỗi kỹ thuật/liêm chính hoặc thiếu tiền đề G0.
- DRAFT_READY_NEEDS_HUMAN_REVIEW: phần tự động đạt, còn quyết định người thật.
- PASS_G1_CONFIRMED: cả phần tự động và xác nhận người thật đều đủ.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence

import skill_standards as S

STATUS_BLOCKED = "BLOCKED"
STATUS_DRAFT_READY = "DRAFT_READY_NEEDS_HUMAN_REVIEW"
STATUS_CONFIRMED = "PASS_G1_CONFIRMED"
QUALITY_CONTRACT_VERSION = "G1-2026.1"

REQUIRED_ARTIFACT_KEYS = ("A1b", "A2", "A2b", "A13", "A13b")

_REQUIRED_SECTIONS: Dict[str, Sequence[str]] = {
    "A1b": (
        "PROJECT CHARTER",
        "Mục tiêu SMART",
        "Phạm vi",
        "Governance",
        "Milestone",
    ),
    "A2": (
        "ĐỀ CƯƠNG LÕI",
        "Quản trị tài liệu",
        "Cơ sở khoa học và khoảng trống",
        "Mục tiêu, câu hỏi và giả thuyết",
        "Thiết kế, địa điểm và thời gian",
        "Quần thể, tiêu chí chọn và tuyển mẫu",
        "Can thiệp/phơi nhiễm và đối chứng",
        "Kết cục và lịch đánh giá",
        "Cỡ mẫu",
        "Quản lý dữ liệu, bảo mật và chất lượng",
        "Đạo đức, an toàn và đăng ký",
        "Giám sát, sửa đổi và phổ biến",
        "Tài liệu tham khảo và phụ lục",
        "BẢNG THIẾT KẾ ỨNG VIÊN",
        "KIỂM SOÁT",
        "Chuẩn báo cáo",
        "Chuẩn đề cương/protocol",
        "SAP SKELETON",
    ),
    "A2b": (
        "EVIDENCE LEDGER",
        "Chiến lược tìm kiếm",
        "PMID/DOI",
        "Khoảng trống",
    ),
    "A13": (
        "RACI",
        "GANTT",
        "KINH PHÍ",
        "QUALITY-BY-DESIGN",
    ),
    "A13b": (
        "RISK REGISTER",
        "CAPA",
        "Chủ nhân",
        "Ngày rà",
    ),
}

_REPORTING_TOKENS: Dict[str, Sequence[str]] = {
    "rct": ("CONSORT 2025",),
    "cohort": ("STROBE",),
    "case_control": ("STROBE",),
    "cross_sectional": ("STROBE",),
    "diagnostic": ("STARD",),
    "sr_ma": ("PRISMA 2020",),
    "prediction": ("TRIPOD+AI",),
    "qualitative": ("COREQ", "SRQR"),
}

_PROTOCOL_TOKENS: Dict[str, Sequence[str]] = {
    "rct": ("SPIRIT 2025",),
    "sr_ma": ("PRISMA-P",),
}

_STANDARDS_BASIS = (
    {
        "standard": "EQUATOR Network",
        "scope": "Bản đồ guideline theo loại nghiên cứu",
        "url": "https://www.equator-network.org/library/",
    },
    {
        "standard": "SPIRIT 2025",
        "scope": "Protocol thử nghiệm ngẫu nhiên",
        "pmid": "40294593",
        "doi": "10.1001/jama.2025.4486",
    },
    {
        "standard": "CONSORT 2025",
        "scope": "Báo cáo kết quả thử nghiệm ngẫu nhiên",
        "doi": "10.1136/bmj-2024-081123",
    },
    {
        "standard": "PRISMA-P 2015",
        "scope": "Protocol tổng quan hệ thống",
        "doi": "10.1186/2046-4053-4-1",
    },
    {
        "standard": "ICH E6(R3)",
        "scope": "Quality-by-design và GCP cho thử nghiệm lâm sàng",
        "url": "https://www.ema.europa.eu/en/ich-e6-good-clinical-practice-scientific-guideline",
    },
)

_REVIEW_ROLES = {
    "pi",
    "principal investigator",
    "research lead",
    "methodologist",
    "nhà phương pháp",
    "chủ nhiệm",
}


def _present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return False
        return not any(
            marker in text.upper()
            for marker in ("[CẦN", "[REQUIRE_HUMAN", "CHƯA XÁC NHẬN")
        )
    if isinstance(value, Mapping):
        return any(_present(v) for v in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_present(v) for v in value)
    return True


def _text(value: Any, fallback: str = "[CẦN BỔ SUNG]") -> str:
    if not _present(value):
        return fallback
    if isinstance(value, Mapping):
        for key in ("name", "text", "description", "general"):
            if _present(value.get(key)):
                return str(value[key]).strip()
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, (list, tuple, set)):
        return "; ".join(str(v).strip() for v in value if _present(v))
    return str(value).strip()


def _g1_meta(meta: Mapping[str, Any]) -> Mapping[str, Any]:
    gp = meta.get("gate_params")
    if not isinstance(gp, Mapping):
        return {}
    g1 = gp.get("G1")
    return g1 if isinstance(g1, Mapping) else {}


def _first_present(*values: Any) -> Any:
    for value in values:
        if _present(value):
            return value
    return None


def _normalise_role(value: Any) -> str:
    return str(value or "").strip().casefold()


def _valid_review_time(value: Any) -> bool:
    if not _present(value):
        return False
    try:
        datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def _list_complete(value: Any) -> bool:
    """True khi danh sách có ít nhất một mục nội dung thật."""
    return isinstance(value, (list, tuple)) and bool(value) and all(
        _present(item) for item in value
    )


def _outcome_components(meta: Mapping[str, Any]) -> Dict[str, Any]:
    """Chuẩn hóa kết cục chính thành bốn thành phần vận hành tối thiểu."""
    outcome = _primary_outcome(meta)
    g1 = _g1_meta(meta)
    if isinstance(outcome, Mapping):
        return {
            "name": _first_present(
                outcome.get("name"),
                outcome.get("text"),
                outcome.get("description"),
            ),
            "measure": _first_present(
                outcome.get("measure"),
                outcome.get("measurement"),
                outcome.get("definition"),
                outcome.get("unit"),
            ),
            "timepoint": _first_present(
                outcome.get("timepoint"),
                outcome.get("time_point"),
                outcome.get("assessment_time"),
            ),
            "type": _first_present(
                outcome.get("type"),
                outcome.get("scale_type"),
                outcome.get("data_type"),
            ),
        }
    return {
        "name": outcome,
        "measure": _first_present(
            meta.get("primary_outcome_measure"),
            g1.get("primary_outcome_measure"),
        ),
        "timepoint": _first_present(
            meta.get("primary_outcome_timepoint"),
            g1.get("primary_outcome_timepoint"),
        ),
        "type": _first_present(
            meta.get("primary_outcome_type"),
            g1.get("primary_outcome_type"),
        ),
    }


def _estimand_complete(g1: Mapping[str, Any]) -> bool:
    estimand = g1.get("estimand")
    if not isinstance(estimand, Mapping):
        return False
    required = (
        "population",
        "treatment_condition",
        "variable",
        "intercurrent_events_strategy",
        "population_summary_measure",
    )
    return all(_present(estimand.get(key)) for key in required)


def build_protocol_core(
    *,
    study: str,
    topic: str,
    design: Mapping[str, Any],
    meta: Mapping[str, Any],
    generated_at: str,
) -> str:
    """Sinh khung đề cương lõi chung; chỗ thiếu luôn mang nhãn, không suy diễn."""
    g1 = _g1_meta(meta)
    outcome = _outcome_components(meta)
    reporting = str(design.get("reporting_standard") or "[CẦN BỔ SUNG]")
    protocol = str(design.get("protocol_standard") or "[CẦN BỔ SUNG]")
    estimand = g1.get("estimand")
    estimand = estimand if isinstance(estimand, Mapping) else {}
    internal = str(design.get("internal_code") or "")
    design_specific_core = ""
    if internal == "qualitative":
        design_specific_core = f"""
- Hiện tượng trung tâm: {_text(g1.get("central_phenomenon"))}
- Cách tiếp cận định tính: {_text(g1.get("qualitative_approach"))}
- Phương pháp thu thập dữ liệu: {_text(g1.get("data_collection_method"))}
- Tiêu chí bão hòa/dừng thu thập: {_text(g1.get("saturation_criterion"))}
"""
    elif internal == "sr_ma":
        design_specific_core = f"""
- Nguồn thông tin: {_text(g1.get("information_sources"))}
- Chiến lược tìm kiếm: {_text(g1.get("search_strategy"))}
- Ngày tìm cuối cùng dự kiến: {_text(g1.get("search_last_date"))}
- Quy trình chọn nghiên cứu: {_text(g1.get("study_selection_process"))}
"""

    def joined(value: Any) -> str:
        return _text(value)

    return f"""
## PHẦN 0 — ĐỀ CƯƠNG LÕI

> [DỰ THẢO] Đây là cấu trúc đề cương để nhóm nghiên cứu hoàn thiện và xác nhận.
> Sự có mặt của một mục không chứng minh nội dung khoa học của mục đó đã đúng.

### 0.1 Quản trị tài liệu
- Mã đề tài: `{study}`
- Tên đề tài: {_text(topic)}
- Phiên bản protocol: {_text(g1.get("protocol_version"))}
- Ngày tạo/cập nhật: {generated_at}
- Chủ nhiệm, nhà phương pháp, thống kê viên, quản lý dữ liệu: [CẦN BỔ SUNG]
- Tài trợ, bảo hiểm, xung đột lợi ích và vai trò nhà tài trợ: [CẦN BỔ SUNG]
- Chuẩn đề cương: {protocol}
- Chuẩn báo cáo kết quả dự kiến: {reporting}

### 0.2 Cơ sở khoa học và khoảng trống
- Vấn đề nghiên cứu và gánh nặng liên quan: [CẦN TỔNG HỢP TỪ A2b]
- Bằng chứng hiện có và giới hạn: [CẦN TỔNG HỢP TỪ A2b]
- Khoảng trống, tính mới và lý do cần nghiên cứu: [CẦN PI/NGƯỜI RÀ BẰNG CHỨNG XÁC NHẬN]
- Cân bằng lợi ích, nguy cơ và tính hợp lý khoa học: [CẦN BỔ SUNG]

### 0.3 Mục tiêu, câu hỏi và giả thuyết
- Mục tiêu: {joined(_objectives(meta))}
- Câu hỏi nghiên cứu/PICO-PECO-PIRD: {_text(g1.get("research_question"))}
- Giả thuyết chính và hướng hiệu ứng: [CẦN BỔ SUNG]
- Kết cục chính neo mục tiêu: {_text(outcome["name"])}

### 0.4 Thiết kế, địa điểm và thời gian
- Thiết kế đã chọn: {_text(design.get("primary"))}
- Lý do chọn so với phương án thay thế: {_text(design.get("rationale"))}
- Địa điểm/bối cảnh: {_text(_first_present(meta.get("setting"), g1.get("setting")))}
- Thời gian nghiên cứu: {_text(_first_present(meta.get("study_period"), g1.get("study_period")))}
- Sơ đồ nghiên cứu và lịch tuyển-can thiệp-đánh giá: [CẦN BỔ SUNG]

### 0.5 Quần thể, tiêu chí chọn và tuyển mẫu
- Quần thể đích/nguồn: {_text(_first_present(meta.get("population"), g1.get("population")))}
- Tiêu chí chọn vào: {joined(g1.get("inclusion_criteria"))}
- Tiêu chí loại trừ: {joined(g1.get("exclusion_criteria"))}
- Chiến lược tuyển/chọn mẫu và tránh thiên lệch chọn mẫu: {_text(g1.get("recruitment_strategy"))}
- Đồng thuận tham gia và xử lý rút lui: [CẦN HOÀN THIỆN Ở G2]

### 0.6 Can thiệp/phơi nhiễm và đối chứng
- Can thiệp, phơi nhiễm hoặc index test: {_text(g1.get("intervention_or_exposure"))}
- Đối chứng/comparator hoặc lý do không áp dụng: {_text(g1.get("comparator"))}
- Liều/cường độ, thời lượng, đồng can thiệp, tuân thủ hoặc cách đo phơi nhiễm: [CẦN BỔ SUNG]
- Tiêu chí dừng/chuyển/điều trị cứu hộ nếu áp dụng: [CẦN BỔ SUNG]
{design_specific_core}

### 0.7 Kết cục và lịch đánh giá
- Kết cục chính: {_text(outcome["name"])}
- Định nghĩa/công cụ/đơn vị đo: {_text(outcome["measure"])}
- Thời điểm đánh giá chính: {_text(outcome["timepoint"])}
- Loại dữ liệu/thước đo: {_text(outcome["type"])}
- Kết cục phụ: {joined(g1.get("secondary_outcomes"))}
- Lịch theo dõi/đánh giá: {_text(g1.get("follow_up_schedule"))}

### 0.8 Cỡ mẫu
- Cỡ mẫu và power chính thức: [CẦN TÍNH Ở G3]
- Effect size/MCID, alpha, power, tỷ lệ biến cố, mất theo dõi và design effect:
  [CẦN NGUỒN PMID/DOI HOẶC PILOT]
- Phân bổ theo nhóm/tầng/trung tâm nếu có: [CẦN BỔ SUNG]

### 0.9 Quản lý dữ liệu, bảo mật và chất lượng
- CRF/data dictionary, nguồn dữ liệu và quy tắc kiểm tra: [CẦN HOÀN THIỆN G3/G5]
- Mã giả danh, phân quyền, audit trail, lưu trữ và hủy dữ liệu: [CẦN HOÀN THIỆN G2/G5]
- Critical-to-quality factors và quality tolerance limits: [CẦN PI ẤN ĐỊNH]
- Kế hoạch dữ liệu thiếu, sai lệch protocol và CAPA: [CẦN HOÀN THIỆN G4/G5]

### 0.10 Đạo đức, an toàn và đăng ký
- Phê duyệt IRB/IEC, ICF/waiver, bảo mật và bồi thường: [CẦN HỒ SƠ THẬT Ở G2]
- Đăng ký nghiên cứu/protocol trước mốc bắt buộc: [CẦN HỒ SƠ THẬT Ở G2]
- AE/SAE, giám sát an toàn, DMC/DSMB và quy tắc dừng nếu áp dụng: [CẦN BỔ SUNG]
- Nhóm dễ tổn thương và biện pháp bảo vệ: [CẦN ĐÁNH GIÁ]

### 0.11 Giám sát, sửa đổi và phổ biến
- Monitoring/audit và phân công trách nhiệm: [CẦN BỔ SUNG]
- Quy trình protocol amendment, cập nhật registry/IRB và thông báo bên liên quan: [CẦN BỔ SUNG]
- Kế hoạch công bố kể cả kết quả âm, chia sẻ dữ liệu/mã và truyền đạt cho người tham gia:
  [CẦN BỔ SUNG]
- Tác giả, contributorship, COI, tài trợ và khai báo AI: [CẦN XÁC NHẬN Ở G9]

### 0.12 Tài liệu tham khảo và phụ lục
- Evidence Ledger: `G1_A2b_EVIDENCE_LEDGER_{study}.md`
- Project Charter: `G1_A1b_PROJECT_CHARTER_{study}.md`
- Kế hoạch triển khai/RACI/kinh phí: `G1_A13_IMPLEMENTATION_PLAN_{study}.md`
- Risk Register/CAPA: `G1_A13b_RISK_REGISTER_{study}.md`
- Estimand RCT hiện hành: dân số={_text(estimand.get("population"))};
  điều kiện điều trị={_text(estimand.get("treatment_condition"))};
  biến kết cục={_text(estimand.get("variable"))};
  biến cố xen ngang/chiến lược={_text(estimand.get("intercurrent_events_strategy"))};
  thước đo tổng hợp quần thể={_text(estimand.get("population_summary_measure"))}.

> Cần bác sĩ kiểm chứng.

---
"""


def collect_evidence_identifiers(
    out_dir: Path,
    g0_checkpoint: Mapping[str, Any],
    effects: Iterable[Mapping[str, Any]],
) -> Dict[str, List[str]]:
    """Thu PMID/DOI đã xuất hiện thật; không tự tạo định danh mới."""
    pmids: List[str] = []
    dois: List[str] = []

    def add_unique(bucket: List[str], value: Any) -> None:
        text = str(value or "").strip()
        if text and text not in bucket:
            bucket.append(text)

    for effect in effects:
        add_unique(pmids, effect.get("pmid"))
        add_unique(dois, effect.get("doi"))

    pubmed = g0_checkpoint.get("pubmed_results")
    if isinstance(pubmed, Mapping):
        for key in ("pmids", "all_pmids", "pmids_used_as_seed"):
            values = pubmed.get(key)
            if isinstance(values, list):
                for value in values:
                    add_unique(pmids, value)

    candidates: List[Path] = []
    artifacts = g0_checkpoint.get("artifacts")
    if isinstance(artifacts, Mapping):
        raw = artifacts.get("A1_markdown")
        if raw:
            p = Path(str(raw))
            candidates.append(p if p.is_absolute() else Path.cwd() / p)
    candidates.extend(sorted(Path(out_dir).glob("G0_A1_PICO_FINER_*.md")))

    for path in candidates:
        if not path.exists():
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            continue
        for value in re.findall(r"(?i)\bPMID\s*:?\s*(\d{5,9})\b", content):
            add_unique(pmids, value)
        for value in re.findall(r"(?i)\b10\.\d{4,9}/[-._;()/:A-Z0-9]+", content):
            add_unique(dois, value.rstrip(".,;)"))

    return {"pmids": pmids, "dois": dois}


def _objectives(meta: Mapping[str, Any]) -> Any:
    g1 = _g1_meta(meta)
    return _first_present(meta.get("objectives"), g1.get("objectives"))


def _primary_outcome(meta: Mapping[str, Any]) -> Any:
    g1 = _g1_meta(meta)
    return _first_present(meta.get("primary_outcome"), g1.get("primary_outcome"))


def build_supporting_artifacts(
    *,
    study: str,
    topic: str,
    out_dir: Path,
    design: Mapping[str, Any],
    g0_checkpoint: Mapping[str, Any],
    effects: Sequence[Mapping[str, Any]],
    meta: Mapping[str, Any],
    generated_at: str,
) -> Dict[str, Path]:
    """Sinh bốn artifact G1 còn thiếu ngoài A2; mọi giả định đều mang nhãn."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    g1 = _g1_meta(meta)
    objectives = _text(_objectives(meta))
    primary_outcome = _text(_primary_outcome(meta))
    population = _text(_first_present(meta.get("population"), g1.get("population")))
    setting = _text(_first_present(meta.get("setting"), g1.get("setting")))
    study_period = _text(_first_present(meta.get("study_period"), g1.get("study_period")))
    identifiers = collect_evidence_identifiers(out_dir, g0_checkpoint, effects)
    query = _text(
        _first_present(
            g0_checkpoint.get("base_query"),
            meta.get("query_en"),
            topic,
        )
    )

    charter = f"""# PROJECT CHARTER (A1b) — {study}
> [DỰ THẢO] Sinh tự động {generated_at}; không thay xác nhận của PI/methodologist.

## Phạm vi
- Tên/chủ đề: {_text(topic)}
- Thiết kế dự kiến: {_text(design.get("primary"))}
- Quần thể: {population}
- Bối cảnh: {setting}
- Thời gian nghiên cứu: {study_period}
- Ngoài phạm vi: {_text(_first_present(meta.get("out_of_scope"), g1.get("out_of_scope")))}

## Mục tiêu SMART
- Mục tiêu: {objectives}
- Kết cục chính neo mục tiêu: {primary_outcome}

## Governance
| Quyết định | Vai trò chịu trách nhiệm | Bằng chứng |
|---|---|---|
| Chốt thiết kế G1 | PI/Methodologist | `study_meta.json: gate_params.G1` |
| Phê duyệt đạo đức G2 | IRB/IEC | Approval ledger có chữ ký |
| Khóa SAP G4 | Biostatistician/PI | SAP lock có chữ ký |
| Khóa dữ liệu | Data Manager/PI | Data Lock Memo |
| Bình duyệt G8 | Independent reviewer | Approval ledger đúng vai trò |

## Milestone
| Mốc | Sản phẩm | Điều kiện đóng |
|---|---|---|
| G0 | PICO/FINER + evidence seed | Câu hỏi và khoảng trống được xác nhận |
| G1 | A1b/A2/A2b/A13/A13b | Thiết kế + reporting map được PI/methodologist xác nhận |
| G2 | Ethics/registration package | IRB/IEC thật |
| G3–G4 | Cỡ mẫu + SAP | Tham số có nguồn + SAP lock |
| G5–G6 | Dữ liệu + phân tích | Data lock + phân tích theo SAP |
| G7–G10 | Báo cáo + kiểm duyệt + lắp ráp | A12/G8/G9 sạch và đúng vai trò |

> Cần bác sĩ kiểm chứng.
"""

    evidence_rows: List[str] = []
    for effect in effects:
        pmid = str(effect.get("pmid") or "").strip()
        if not pmid:
            continue
        evidence_rows.append(
            "| PMID:{pmid} | {title} | [CẦN TRÍCH XUẤT] | {effect} | "
            "[CẦN THẨM ĐỊNH RoB] | [CẦN XÁC NHẬN NỘI DUNG] |".format(
                pmid=pmid,
                title=_text(effect.get("title")),
                effect=f"{effect.get('type', '?')}={effect.get('value', '?')}",
            )
        )
    effect_pmids = {str(effect.get("pmid") or "").strip() for effect in effects}
    for pmid in identifiers["pmids"]:
        if pmid in effect_pmids:
            continue
        evidence_rows.append(
            f"| PMID:{pmid} | [CẦN TRÍCH XUẤT METADATA] | "
            "[CẦN TRÍCH XUẤT] | [CẦN TRÍCH XUẤT] | "
            "[CẦN THẨM ĐỊNH RoB] | [CẦN XÁC NHẬN NỘI DUNG] |"
        )
    for doi in identifiers["dois"]:
        evidence_rows.append(
            f"| DOI:{doi} | [CẦN TRÍCH XUẤT METADATA] | "
            "[CẦN TRÍCH XUẤT] | [CẦN TRÍCH XUẤT] | "
            "[CẦN THẨM ĐỊNH RoB] | [CẦN XÁC NHẬN NỘI DUNG] |"
        )
    if not evidence_rows:
        evidence_rows.append(
            "| [CẦN PMID/DOI] | [CẦN TRÍCH XUẤT] | [CẦN] | [CẦN] | "
            "[CẦN] | CHƯA ĐỦ BẰNG CHỨNG TRUY NGUYÊN |"
        )

    gap_lines = g0_checkpoint.get("research_gaps")
    if isinstance(gap_lines, list) and gap_lines:
        gap_text = "\n".join(f"- {item}" for item in gap_lines)
    else:
        gap_text = "- [CẦN BỔ SUNG sau tổng quan có hệ thống]"
    evidence = f"""# EVIDENCE LEDGER (A2b) — {study}
> [DỰ THẢO] Không tự gán GRADE; chưa đọc toàn văn phải giữ nhãn [CẦN].

## Chiến lược tìm kiếm
- Nguồn tối thiểu: PubMed + ít nhất một nguồn phù hợp khác.
- Truy vấn G0: `{query}`
- Ngày rà: {generated_at[:10]}
- Giới hạn truy xuất/recall: [CẦN XÁC NHẬN]

## Bảng Evidence Ledger
| PMID/DOI | Tiêu đề | Thiết kế/N | Hiệu ứng chính | RoB | Trạng thái nội dung |
|---|---|---|---|---|---|
{chr(10).join(evidence_rows)}

## Khoảng trống nghiên cứu
{gap_text}

> Mỗi luận điểm trong protocol phải truy ngược được về dòng PMID/DOI phù hợp.
> Cần bác sĩ kiểm chứng.
"""

    plan = f"""# KẾ HOẠCH TRIỂN KHAI (A13) — {study}
> [DỰ THẢO] Đơn giá, nhân sự và thời lượng thật do chủ nhiệm/đơn vị xác nhận.

## RACI
| Công việc | PI | Methodologist | Biostatistician | Data Manager | Site team |
|---|---|---|---|---|---|
| Chốt thiết kế/protocol | A | R | C | I | C |
| Cỡ mẫu/SAP | A | C | R | C | I |
| IRB/consent | A | C | I | C | R |
| Thu thập/QC dữ liệu | A | I | C | R | R |
| Phân tích/báo cáo | A | C | R | C | I |

## GANTT theo cổng
| Chặng | Phụ thuộc | Thời lượng | Mốc nghiệm thu |
|---|---|---|---|
| G0–G1 | Không | [CẦN] | Thiết kế + protocol map |
| G2 | G1 | [CẦN] | IRB/registration |
| G3–G4 | G1 | [CẦN] | Cỡ mẫu + SAP lock |
| G5 | G2/G4 | [CẦN] | Pilot/SOP/data tools |
| G6–G10 | Data lock | [CẦN] | Analysis/report/review/closeout |

## KINH PHÍ
| Nhóm chi phí | Số lượng | Đơn giá có nguồn | Thành tiền | Trạng thái |
|---|---:|---:|---:|---|
| Nhân công | [CẦN] | [CẦN CHỦ NHIỆM ẤN ĐỊNH] | [CẦN] | Dự thảo |
| Thu thập/xét nghiệm | [CẦN] | [CẦN] | [CẦN] | Dự thảo |
| Dữ liệu/phần mềm | [CẦN] | [CẦN] | [CẦN] | Dự thảo |
| Công bố/lưu trữ | [CẦN] | [CẦN] | [CẦN] | Dự thảo |

## QUALITY-BY-DESIGN
- Critical-to-quality factors: quyền/an toàn người tham gia; tính tin cậy kết cục chính;
  tuyển mẫu; missing data; tuân thủ protocol; truy nguyên dữ liệu.
- Quality tolerance limits: [CẦN PI/methodologist ấn định trước triển khai].
- Monitoring và escalation: [CẦN xác nhận tại đơn vị].

> Cần bác sĩ kiểm chứng.
"""

    review_date = generated_at[:10]
    risk_rows = (
        "| G1-R01 | Thiết kế | Thiết kế không khớp câu hỏi/estimand | [CẦN] | Cao | "
        "Methodologist rà trước G2 | Sửa protocol có version; vô hiệu downstream cũ | "
        f"PI/Methodologist | Mở | {review_date} |",
        "| G1-R02 | Đạo đức | Hồ sơ không khớp phiên bản protocol | [CẦN] | Cao | "
        f"Hash/version mọi artifact | Dừng tuyển; amendment IRB | PI | Mở | {review_date} |",
        "| G1-R03 | Tuyển mẫu | Không đạt tốc độ tuyển dự kiến | [CẦN] | Cao | "
        "Feasibility log + nhiều điểm tuyển | CAPA tuyển mẫu; điều chỉnh timeline đã duyệt | "
        f"Site lead | Mở | {review_date} |",
        "| G1-R04 | Dữ liệu | Thiếu/sai dữ liệu kết cục chính | [CẦN] | Cao | "
        f"CRF validation + pilot | Query/CAPA; không tự điền dữ liệu | Data Manager | Mở | {review_date} |",
        "| G1-R05 | Thống kê | Outcome/SAP thay đổi sau xem dữ liệu | [CẦN] | Cao | "
        "Khóa SAP G4 | Ghi deviation; phân tích gắn nhãn thăm dò | "
        f"Biostatistician | Mở | {review_date} |",
        "| G1-R06 | Liêm chính | Trích dẫn ma/sai nội dung | [CẦN] | Cao | "
        f"Evidence Ledger + A12 | Loại/sửa nguồn; chạy lại A12 | Evidence reviewer | Mở | {review_date} |",
    )
    risks = f"""# RISK REGISTER SỐNG (A13b) — {study}
> [DỰ THẢO] Mức xác suất/tác động phải được nhóm nghiên cứu hiệu chỉnh.

| ID | Loại | Rủi ro | Xác suất | Tác động | Giảm thiểu trước | CAPA nếu xảy ra | Chủ nhân | Trạng thái | Ngày rà |
|---|---|---|---|---|---|---|---|---|---|
{chr(10).join(risk_rows)}

## Quy tắc cập nhật
- Rà sau mỗi cổng và khi có protocol amendment.
- Không xóa dòng cũ; cập nhật trạng thái, ngày, nguyên nhân và CAPA.

> Cần bác sĩ kiểm chứng.
"""

    contents = {
        "A1b": charter,
        "A2b": evidence,
        "A13": plan,
        "A13b": risks,
    }
    paths = {
        "A1b": out_dir / f"G1_A1b_PROJECT_CHARTER_{study}.md",
        "A2b": out_dir / f"G1_A2b_EVIDENCE_LEDGER_{study}.md",
        "A13": out_dir / f"G1_A13_IMPLEMENTATION_PLAN_{study}.md",
        "A13b": out_dir / f"G1_A13b_RISK_REGISTER_{study}.md",
    }
    for key, path in paths.items():
        path.write_text(contents[key], encoding="utf-8", newline="\n")
    return paths


def _criterion(
    criterion_id: str,
    label: str,
    status: str,
    evidence: str,
    action: str = "",
) -> Dict[str, str]:
    return {
        "id": criterion_id,
        "label": label,
        "status": status,
        "evidence": evidence,
        "action": action,
    }


def evaluate_g1_quality(
    *,
    design: Mapping[str, Any],
    artifact_texts: Mapping[str, str],
    artifact_paths: Mapping[str, Path],
    g0_checkpoint: Mapping[str, Any],
    meta: Mapping[str, Any],
    evidence_identifiers: Mapping[str, Sequence[str]],
    guardrail_passed: bool = True,
) -> Dict[str, Any]:
    """Đánh giá G1 theo tiêu chí máy và xác nhận người thật."""
    automatic: List[Dict[str, str]] = []
    human: List[Dict[str, str]] = []

    automatic.append(_criterion(
        "G1-AUTO-00",
        "Guardrail liêm chính G1 sạch",
        "PASS" if guardrail_passed else "BLOCK",
        f"guardrail_passed={guardrail_passed}",
        "Sửa mọi lỗi PII, vượt cổng, nguồn hoặc disclaimer trước khi tiếp tục.",
    ))

    g0_guard = g0_checkpoint.get("guardrail")
    g0_present = bool(g0_checkpoint)
    g0_contract = bool(g0_checkpoint.get("quality_contract_version"))
    g0_quality = g0_checkpoint.get("quality_gate")
    g0_quality_status = (
        str(g0_quality.get("status") or "")
        if isinstance(g0_quality, Mapping)
        else ""
    )
    legacy_g0_ok = bool(
        isinstance(g0_guard, Mapping) and g0_guard.get("passed") is True
    )
    if not g0_present:
        g0_status = "REVIEW"
        g0_evidence = "Chưa có G0; chỉ được tạo dự thảo G1 độc lập"
    elif g0_contract and g0_quality_status == "PASS_G0_CONFIRMED":
        g0_status = "PASS"
        g0_evidence = "G0 quality_gate=PASS_G0_CONFIRMED"
    elif g0_contract and g0_quality_status == "BLOCKED":
        g0_status = "BLOCK"
        g0_evidence = "G0 quality contract đang BLOCKED"
    elif g0_contract:
        g0_status = "REVIEW"
        g0_evidence = (
            f"G0 quality_gate={g0_quality_status or 'thiếu'}; "
            "chưa có xác nhận câu hỏi nghiên cứu"
        )
    elif legacy_g0_ok:
        g0_status = "PASS"
        g0_evidence = "G0 legacy guardrail passed=True"
    else:
        g0_status = "BLOCK"
        g0_evidence = "Có checkpoint G0 nhưng guardrail chưa đạt"
    automatic.append(_criterion(
        "G1-AUTO-01",
        "Tiền đề G0 có checkpoint và guardrail sạch",
        g0_status,
        g0_evidence,
        "Hoàn thiện G0 trước khi xác nhận G1.",
    ))

    internal = str(design.get("internal_code") or "")
    canonical_ok = internal in _REPORTING_TOKENS
    automatic.append(_criterion(
        "G1-AUTO-02",
        "Mã thiết kế thuộc vocabulary canonical",
        "PASS" if canonical_ok else "BLOCK",
        f"internal_code={internal!r}",
        "Chọn một mã thiết kế canonical được hệ hỗ trợ.",
    ))

    reporting = str(design.get("reporting_standard") or "")
    expected_tokens = _REPORTING_TOKENS.get(internal, ())
    reporting_ok = bool(expected_tokens) and all(
        token.casefold() in reporting.casefold() for token in expected_tokens
    )
    official = S.reporting_standards_for(internal).get("primary", "")
    automatic.append(_criterion(
        "G1-AUTO-03",
        "Chuẩn báo cáo khớp thiết kế",
        "PASS" if reporting_ok else "BLOCK",
        f"đã chọn={reporting!r}; canon={official!r}",
        "Sửa reporting map theo skill_standards.py.",
    ))

    protocol = str(design.get("protocol_standard") or "")
    protocol_tokens = _PROTOCOL_TOKENS.get(internal, ())
    official_protocol = S.reporting_standards_for(internal).get("protocol", "")
    if protocol_tokens:
        protocol_ok = all(
            token.casefold() in protocol.casefold()
            for token in protocol_tokens
        )
    else:
        protocol_ok = bool(protocol) and protocol.casefold() == official_protocol.casefold()
    automatic.append(_criterion(
        "G1-AUTO-03b",
        "Chuẩn đề cương/protocol khớp thiết kế",
        "PASS" if protocol_ok else "BLOCK",
        f"đã chọn={protocol!r}; canon={official_protocol!r}",
        "Gắn chuẩn protocol riêng; không dùng checklist báo cáo kết quả thay thế.",
    ))

    ambiguous = bool(design.get("ambiguous"))
    automatic.append(_criterion(
        "G1-AUTO-04",
        "Thiết kế không còn suy luận mơ hồ",
        "REVIEW" if ambiguous else "PASS",
        "ambiguous=true" if ambiguous else "ambiguous=false",
        "PI/methodologist phải pin thiết kế sau khi đọc lại khoảng trống.",
    ))

    primary_present = _present(design.get("primary"))
    alternatives_complete = all(
        _present(design.get(key))
        for key in ("alternative_1", "alternative_2")
    )
    rationale_present = _present(design.get("rationale"))
    draft_rationale_present = bool(str(design.get("rationale") or "").strip())
    # SỬA 2026-07-31 (audit tautology vòng 2 — reverse-tautology CRITICAL):
    # ngưỡng >=7 hardcode cho MỌI thiết kế, nhưng run_g1_auto.py::
    # BIAS_CONTROLS["qualitative"] CHỦ Ý chỉ có 5 mục (4 miền trustworthiness
    # Lincoln & Guba — Credibility/Transferability/Dependability/
    # Confirmability — cộng Reporting bias; định tính KHÔNG dùng khung bias
    # định lượng, đã ghi chú tại nơi định nghĩa 2026-07-19) — khiến MỌI đề
    # tài định tính hợp lệ bị BLOCK cứng (main() coi BLOCKED là SystemExit
    # thật, không chỉ REVIEW). Xác nhận thực nghiệm: cả infer_study_design()
    # và _apply_design_pin() (2 đường sản xuất thật gán internal_code=
    # "qualitative") đều trả bias_controls dài 5 — một đề tài định tính ĐÃ
    # ĐIỀN ĐẦY ĐỦ mọi trường G1-HUMAN-01..08 vẫn BLOCK chỉ vì mục này.
    _MIN_BIAS_CONTROLS_BY_DESIGN = {"qualitative": 5}
    _DEFAULT_MIN_BIAS_CONTROLS = 7
    bias_controls = design.get("bias_controls")
    _min_bias = _MIN_BIAS_CONTROLS_BY_DESIGN.get(internal, _DEFAULT_MIN_BIAS_CONTROLS)
    bias_ok = isinstance(bias_controls, (list, tuple)) and len(bias_controls) >= _min_bias
    if (
        not alternatives_complete
        or not bias_ok
        or (ambiguous and not draft_rationale_present)
    ):
        design_comparison_status = "BLOCK"
    elif ambiguous:
        design_comparison_status = "REVIEW"
    elif not primary_present or not rationale_present:
        design_comparison_status = "BLOCK"
    else:
        design_comparison_status = "PASS"
    automatic.append(_criterion(
        "G1-AUTO-04b",
        "So sánh ít nhất ba phương án và kiểm soát đủ nhóm sai lệch/"
        "trustworthiness theo thiết kế",
        design_comparison_status,
        f"primary_present={primary_present}; "
        f"alternatives_complete={alternatives_complete}; "
        f"rationale_present={rationale_present}; "
        f"bias_controls={len(bias_controls) if isinstance(bias_controls, (list, tuple)) else 0}",
        (
            "PI/methodologist chọn một phương án chính từ bảng so sánh."
            if design_comparison_status == "REVIEW"
            else "Bổ sung 3 phương án, lý do chọn/loại và đủ 7 nhóm sai lệch."
        ),
    ))

    a2_text = artifact_texts.get("A2", "")
    method_conflicts: List[str] = []
    conflict_patterns = {
        "case_control": (
            "Phân tích chính: Cox regression",
            "Kaplan-Meier + Cox",
        ),
        "diagnostic": (
            "Calibration: Hosmer-Lemeshow; DCA",
            "EPP ≥ 10",
        ),
        "sr_ma": (
            "DerSimonian-Laird) nếu I²",
            "Fixed-effects nếu I² <",
        ),
        # THÊM 2026-07-30 (audit toàn diện G0-G10, G1-F3 — HIGH): dict này
        # trước đây chỉ có 4/8 mã thiết kế — HOÀN TOÀN THIẾU 'prediction',
        # đúng thiết kế mà chính g1_design_blocks.py (docstring) ghi nhận có
        # lịch sử rơi vào khuôn sr_ma nhiều lần (2026-07-17, 2026-07-21,
        # xem nhánh `elif internal == "prediction"` ở run_g1_auto.py — thêm
        # RIÊNG đúng vì trước đó rơi vào else viết cho sr_ma). Hai cụm dưới
        # xác nhận CHỈ xuất hiện trong nhánh sap_analysis_note của sr_ma
        # (run_g1_auto.py, không xuất hiện ở bất kỳ nhánh thiết kế nào khác) —
        # nếu SAP §4 của một đề tài 'prediction' chứa các cụm này, đó là dấu
        # hiệu khuôn sr_ma đã rò vào thay vì khuôn tiên lượng riêng.
        "prediction": (
            "Hartung-Knapp",
            "funnel plot/Egger",
        ),
        "qualitative": (
            "α: 0.05 (hai đuôi)",
            "Power: [CẦN]%",
            "Mô hình: ☐ Logistic",
        ),
    }
    for pattern in conflict_patterns.get(internal, ()):
        if pattern.casefold() in a2_text.casefold():
            method_conflicts.append(pattern)
    automatic.append(_criterion(
        "G1-AUTO-04c",
        "SAP không chứa khuôn phân tích mâu thuẫn với thiết kế",
        "BLOCK" if method_conflicts else "PASS",
        (
            f"mâu thuẫn={', '.join(method_conflicts)}"
            if method_conflicts
            else f"không phát hiện khuôn sai cho {internal}"
        ),
        "Sinh lại A2 bằng template theo đúng thiết kế; không vá một khuôn RCT cho mọi loại.",
    ))

    # LƯU Ý PHẠM VI (audit tautology vòng 2, 2026-07-31): mọi tiêu đề mục
    # trong _REQUIRED_SECTIONS và dòng disclaimer đều được các hàm sinh
    # artifact (build_protocol_core()/build_supporting_artifacts()) in CỨNG
    # VÔ ĐIỀU KIỆN — đã xác nhận thực nghiệm với meta RỖNG HOÀN TOÀN (mọi
    # trường bác sĩ điền tự do rơi về placeholder "[CẦN...]") vẫn PASS 5/5.
    # Tiêu chí này kiểm CẤU TRÚC (đủ mục/đủ disclaimer), không thẩm định nội
    # dung khoa học có đúng/đủ cho đề tài cụ thể hay không — module tự khai
    # đúng phạm vi này trong scope_statement; việc thẩm định nội dung thuộc
    # G1-HUMAN-01..08 (đọc gate_params.G1 thật). Không có ground truth máy
    # đọc được khác để thẩm định câu trả lời tự do dưới mỗi tiêu đề.
    artifact_failures: List[str] = []
    for key in REQUIRED_ARTIFACT_KEYS:
        path = artifact_paths.get(key)
        text = artifact_texts.get(key, "")
        if not path or not Path(path).exists() or not text.strip():
            artifact_failures.append(f"{key}: thiếu file/nội dung")
            continue
        missing_sections = [
            section for section in _REQUIRED_SECTIONS[key]
            if section.casefold() not in text.casefold()
        ]
        if missing_sections:
            artifact_failures.append(f"{key}: thiếu {', '.join(missing_sections)}")
        if "cần bác sĩ kiểm chứng" not in text.casefold():
            artifact_failures.append(f"{key}: thiếu disclaimer")
    automatic.append(_criterion(
        "G1-AUTO-05",
        "Đủ bộ A1b/A2/A2b/A13/A13b và các phần bắt buộc",
        "BLOCK" if artifact_failures else "PASS",
        "; ".join(artifact_failures) if artifact_failures else "5/5 artifact có mặt và qua kiểm cấu trúc",
        "Sinh lại hoặc sửa artifact G1 bị thiếu.",
    ))

    identifiers = list(evidence_identifiers.get("pmids") or []) + list(
        evidence_identifiers.get("dois") or []
    )
    ledger_text = artifact_texts.get("A2b", "")
    ledger_traceable = any(
        str(identifier).casefold() in ledger_text.casefold()
        for identifier in identifiers
    )
    automatic.append(_criterion(
        "G1-AUTO-06",
        # SỬA 2026-07-30 (audit toàn diện G0-G10, G1-F6): nhãn CŨ "có ít nhất
        # một định danh truy nguyên" dễ đọc nhầm là định danh đã được XÁC
        # MINH tồn tại thật — hàm này chỉ so khớp CHUỖI PMID/DOI xuất hiện
        # case-insensitive trong text Evidence Ledger, KHÔNG gọi PubMed/
        # Crossref. Xác minh tồn tại thật thuộc cổng A12 (kiem-chung-trich-dan),
        # không phải G1 (G1 chạy thường xuyên, không có rate-limit/cache
        # mạng như A12 — quyết định phạm vi, không thêm gọi mạng ở đây).
        "Có định danh PMID/DOI khớp chuỗi trong Evidence Ledger (CHƯA xác "
        "minh qua PubMed/Crossref — việc đó thuộc cổng A12 kiem-chung-trich-dan)",
        "PASS" if identifiers and ledger_traceable else "REVIEW",
        (
            f"{len(identifiers)} PMID/DOI được thu, ledger_traceable={ledger_traceable} "
            "(khớp CHUỖI, KHÔNG gọi PubMed để xác minh tồn tại)"
        ),
        "Bổ sung Evidence Ledger có PMID/DOI thật; không bịa nguồn.",
    ))

    g1 = _g1_meta(meta)
    pinned_design = _first_present(meta.get("design_code"), g1.get("design"))
    pin_matches = _present(pinned_design) and str(pinned_design).strip() == internal
    design_confirmed = bool(g1.get("design_confirmed")) and pin_matches
    human.append(_criterion(
        "G1-HUMAN-01",
        "PI/methodologist xác nhận thiết kế",
        "PASS" if design_confirmed else "REVIEW",
        f"pin={pinned_design!r}; design_confirmed={bool(g1.get('design_confirmed'))}",
        "Điền design_code/gate_params.G1.design và design_confirmed=true.",
    ))

    objectives = _objectives(meta)
    outcome = _outcome_components(meta)
    outcome_complete = all(_present(value) for value in outcome.values())
    research_question = g1.get("research_question")
    if internal == "qualitative":
        objective_ok = (
            _list_complete(objectives)
            and _present(research_question)
            and _present(g1.get("central_phenomenon"))
            and _present(g1.get("qualitative_approach"))
        )
        objective_evidence = (
            f"objectives={'đủ' if _list_complete(objectives) else 'thiếu'}; "
            f"research_question={'có' if _present(research_question) else 'thiếu'}; "
            f"central_phenomenon={'có' if _present(g1.get('central_phenomenon')) else 'thiếu'}; "
            f"qualitative_approach={'có' if _present(g1.get('qualitative_approach')) else 'thiếu'}"
        )
        objective_action = (
            "Điền objectives, research_question, central_phenomenon và "
            "qualitative_approach; không ép kết cục định lượng."
        )
    else:
        objective_ok = (
            _list_complete(objectives)
            and outcome_complete
            and (internal != "sr_ma" or _present(research_question))
        )
        objective_evidence = (
            f"objectives={'đủ' if _list_complete(objectives) else 'thiếu'}; "
            f"outcome_name={'có' if _present(outcome['name']) else 'thiếu'}; "
            f"measure={'có' if _present(outcome['measure']) else 'thiếu'}; "
            f"timepoint={'có' if _present(outcome['timepoint']) else 'thiếu'}; "
            f"type={'có' if _present(outcome['type']) else 'thiếu'}"
        )
        if internal == "sr_ma":
            objective_evidence += (
                f"; research_question={'có' if _present(research_question) else 'thiếu'}"
            )
        objective_action = (
            "Điền objectives và primary_outcome gồm tên, định nghĩa/công cụ đo, "
            "thời điểm và loại dữ liệu."
        )
    human.append(_criterion(
        "G1-HUMAN-02",
        (
            "Mục tiêu, câu hỏi và hiện tượng trung tâm đã chốt"
            if internal == "qualitative"
            else "Mục tiêu và kết cục chính vận hành đã chốt"
        ),
        "PASS" if objective_ok else "REVIEW",
        objective_evidence,
        objective_action,
    ))

    population = _first_present(meta.get("population"), g1.get("population"))
    setting = _first_present(meta.get("setting"), g1.get("setting"))
    period = _first_present(meta.get("study_period"), g1.get("study_period"))
    inclusion = g1.get("inclusion_criteria")
    exclusion = g1.get("exclusion_criteria")
    recruitment = g1.get("recruitment_strategy")
    if internal == "sr_ma":
        sources = g1.get("information_sources")
        frame_ok = (
            _list_complete(inclusion)
            and _list_complete(exclusion)
            and _list_complete(sources)
            and all(
                _present(value)
                for value in (
                    g1.get("search_strategy"),
                    g1.get("search_last_date"),
                    g1.get("study_selection_process"),
                )
            )
        )
        frame_evidence = (
            f"eligibility={'đủ' if _list_complete(inclusion) and _list_complete(exclusion) else 'thiếu'}; "
            f"information_sources={'có' if _list_complete(sources) else 'thiếu'}; "
            f"search_strategy={'có' if _present(g1.get('search_strategy')) else 'thiếu'}; "
            f"search_last_date={'có' if _present(g1.get('search_last_date')) else 'thiếu'}; "
            f"selection_process={'có' if _present(g1.get('study_selection_process')) else 'thiếu'}"
        )
        frame_action = (
            "Điền eligibility, information_sources, search_strategy, "
            "search_last_date và study_selection_process theo PRISMA-P."
        )
    else:
        frame_ok = (
            all(_present(v) for v in (population, setting, period, recruitment))
            and _list_complete(inclusion)
            and _list_complete(exclusion)
        )
        frame_evidence = (
            f"population={'có' if _present(population) else 'thiếu'}; "
            f"inclusion={'có' if _list_complete(inclusion) else 'thiếu'}; "
            f"exclusion={'có' if _list_complete(exclusion) else 'thiếu'}; "
            f"recruitment={'có' if _present(recruitment) else 'thiếu'}; "
            f"setting={'có' if _present(setting) else 'thiếu'}; "
            f"study_period={'có' if _present(period) else 'thiếu'}"
        )
        frame_action = (
            "Điền population, inclusion/exclusion criteria, recruitment_strategy, "
            "setting và study_period."
        )
    human.append(_criterion(
        "G1-HUMAN-03",
        (
            "Tiêu chí chọn, nguồn tìm và quy trình chọn nghiên cứu đã xác định"
            if internal == "sr_ma"
            else "Quần thể, tiêu chí chọn, tuyển mẫu, bối cảnh và thời gian đã xác định"
        ),
        "PASS" if frame_ok else "REVIEW",
        frame_evidence,
        frame_action,
    ))

    intervention = g1.get("intervention_or_exposure")
    comparator = g1.get("comparator")
    follow_up = g1.get("follow_up_schedule")
    if internal == "qualitative":
        treatment_frame_ok = all(
            _present(value)
            for value in (
                g1.get("qualitative_approach"),
                g1.get("data_collection_method"),
                g1.get("saturation_criterion"),
            )
        )
        treatment_evidence = (
            f"qualitative_approach={'có' if _present(g1.get('qualitative_approach')) else 'thiếu'}; "
            f"data_collection_method={'có' if _present(g1.get('data_collection_method')) else 'thiếu'}; "
            f"saturation_criterion={'có' if _present(g1.get('saturation_criterion')) else 'thiếu'}"
        )
        treatment_action = (
            "Điền qualitative_approach, data_collection_method và saturation_criterion."
        )
    elif internal == "sr_ma":
        treatment_frame_ok = all(
            _present(value) for value in (intervention, comparator)
        )
        treatment_evidence = (
            f"intervention_or_exposure={'có' if _present(intervention) else 'thiếu'}; "
            f"comparator={'có' if _present(comparator) else 'thiếu'}"
        )
        treatment_action = (
            "Điền intervention_or_exposure và comparator hoặc lý do N/A trong PICO."
        )
    else:
        treatment_frame_ok = all(
            _present(value) for value in (intervention, comparator, follow_up)
        )
        treatment_evidence = (
            f"intervention_or_exposure={'có' if _present(intervention) else 'thiếu'}; "
            f"comparator={'có' if _present(comparator) else 'thiếu'}; "
            f"follow_up_schedule={'có' if _present(follow_up) else 'thiếu'}"
        )
        treatment_action = (
            "Điền intervention_or_exposure, comparator (hoặc lý do N/A) "
            "và follow_up_schedule."
        )
    human.append(_criterion(
        "G1-HUMAN-04",
        (
            "Phương pháp thu thập và quy tắc bão hòa đã xác định"
            if internal == "qualitative"
            else "Can thiệp/phơi nhiễm, đối chứng và lịch theo dõi đã xác định"
        ),
        "PASS" if treatment_frame_ok else "REVIEW",
        treatment_evidence,
        treatment_action,
    ))

    estimand_ok = internal != "rct" or _estimand_complete(g1)
    human.append(_criterion(
        "G1-HUMAN-05",
        "Estimand đủ 5 thuộc tính khi là RCT",
        "PASS" if estimand_ok else "REVIEW",
        (
            "N/A cho thiết kế không phải RCT"
            if internal != "rct"
            else f"estimand_complete={estimand_ok}"
        ),
        "Điền population, treatment condition, variable, intercurrent-event strategy và population summary measure.",
    ))

    feasibility_ok = g1.get("feasibility_confirmed") is True
    protocol_ok = g1.get("protocol_core_confirmed") is True
    bias_review_ok = g1.get("bias_controls_confirmed") is True
    human.append(_criterion(
        "G1-HUMAN-06",
        "Đề cương lõi, kiểm soát sai lệch và tính khả thi được xác nhận",
        "PASS" if feasibility_ok and protocol_ok and bias_review_ok else "REVIEW",
        f"protocol_core_confirmed={protocol_ok}; "
        f"bias_controls_confirmed={bias_review_ok}; "
        f"feasibility_confirmed={feasibility_ok}",
        "PI/methodologist rà toàn bộ protocol core, bảng bias và tính khả thi rồi bật ba cờ xác nhận.",
    ))

    evidence_review_ok = g1.get("evidence_review_confirmed") is True and bool(identifiers)
    human.append(_criterion(
        "G1-HUMAN-07",
        "Khoảng trống và nội dung trích dẫn đã được người thật đọc lại",
        "PASS" if evidence_review_ok else "REVIEW",
        f"evidence_review_confirmed={g1.get('evidence_review_confirmed') is True}; "
        f"identifiers={len(identifiers)}",
        "Evidence reviewer/PI xác nhận nội dung nguồn và khoảng trống.",
    ))

    role = _normalise_role(g1.get("reviewed_by_role"))
    review_ok = role in _REVIEW_ROLES and _valid_review_time(g1.get("reviewed_at"))
    human.append(_criterion(
        "G1-HUMAN-08",
        "Có vai trò và thời điểm rà phương pháp",
        "PASS" if review_ok else "REVIEW",
        f"reviewed_by_role={role or 'thiếu'}; reviewed_at={g1.get('reviewed_at') or 'thiếu'}",
        "Ghi reviewed_by_role và reviewed_at dạng ISO-8601; không cần lưu danh tính.",
    ))

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
    artifact_manifest: Dict[str, Dict[str, str]] = {}
    for key, path in artifact_paths.items():
        artifact_path = Path(path)
        if not artifact_path.exists():
            continue
        artifact_manifest[key] = {
            "path": str(artifact_path),
            "sha256": hashlib.sha256(artifact_path.read_bytes()).hexdigest(),
        }
    return {
        "schema_version": "1.1",
        "contract_version": QUALITY_CONTRACT_VERSION,
        "status": status,
        "automated_checks_passed": not auto_blocked,
        "human_confirmation_complete": human_complete,
        "automatic_criteria": automatic,
        "human_criteria": human,
        "pending_actions": pending,
        "artifact_manifest": artifact_manifest,
        "standards_basis": list(_STANDARDS_BASIS),
        "scope_statement": (
            "PASS_G1_CONFIRMED chỉ xác nhận thiết kế/reporting map và bộ artifact "
            "G1 theo bằng chứng đã ghi; không thay IRB, khóa SAP, dữ liệu thật hoặc "
            "thẩm định khoa học độc lập. Checklist báo cáo đánh giá tính đầy đủ "
            "của mô tả, không tự chứng minh chất lượng thiết kế hay thực hiện."
        ),
    }


def write_quality_report(study: str, out_dir: Path, report: Mapping[str, Any]) -> Path:
    """Ghi báo cáo G1 máy-đọc được đồng thời với bản Markdown dễ kiểm toán."""
    out_dir = Path(out_dir)
    json_path = out_dir / "G1_QUALITY_REPORT.json"
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    lines = [
        f"# BÁO CÁO CHẤT LƯỢNG G1 — {study}",
        "",
        f"**Trạng thái:** `{report['status']}`",
        "",
        "## Kiểm tra tự động",
        "| Mã | Tiêu chí | Trạng thái | Bằng chứng |",
        "|---|---|---|---|",
    ]
    for row in report.get("automatic_criteria", []):
        lines.append(
            f"| {row['id']} | {row['label']} | {row['status']} | "
            f"{row['evidence'].replace('|', '/')} |"
        )
    lines.extend([
        "",
        "## Xác nhận người thật",
        "| Mã | Tiêu chí | Trạng thái | Bằng chứng |",
        "|---|---|---|---|",
    ])
    for row in report.get("human_criteria", []):
        lines.append(
            f"| {row['id']} | {row['label']} | {row['status']} | "
            f"{row['evidence'].replace('|', '/')} |"
        )
    lines.extend([
        "",
        "## Manifest artifact",
        "| Artifact | Đường dẫn | SHA-256 |",
        "|---|---|---|",
    ])
    for key, item in report.get("artifact_manifest", {}).items():
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
        source = (
            f"PMID:{item['pmid']}" if item.get("pmid") else ""
        )
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
    md_path = out_dir / "G1_QUALITY_REPORT.md"
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return md_path
