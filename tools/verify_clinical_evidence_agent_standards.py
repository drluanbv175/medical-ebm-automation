#!/usr/bin/env python3
"""Kiểm chuẩn agent cho hệ cập nhật chứng cứ y khoa lâm sàng.

Mục tiêu: biến yêu cầu của skill `cap-nhat-chung-cu-y-khoa` thành hợp đồng
máy-kiểm-được cho tầng agent:
- đúng agent phụ trách nguồn/guideline/ứng dụng lâm sàng;
- nguồn chính thống trước, PubMed/Europe PMC là lớp đối chiếu lấy PMID/DOI;
- Evidence Workbench là đầu ra mặc định và có cổng strict source;
- có lớp an toàn thuốc, bản địa hóa Việt Nam, phái sinh và đồng bộ hub;
- không tự áp dụng lâm sàng, không tự ghi Master như đã duyệt, không PII.

Verifier này không xác nhận một khuyến cáo cụ thể là đúng; nó kiểm control-plane
và chuẩn quy trình để mỗi cập nhật chứng cứ thật phải đi qua các cổng trên.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO.parent
AGENTS = REPO / ".claude" / "agents"
ROOT_TOOLS = ROOT / "tools"
SKILL_ROOT = ROOT / "sync" / "skills" / "cap-nhat-chung-cu-y-khoa"
DASH_ROOT = ROOT / "EBM-Dashboards"
MASTER_ROOT = ROOT / "EBM_MASTER"
DEFAULT_JSON = REPO / "reports" / "CLINICAL_EVIDENCE_AGENT_STANDARDS_REPORT.json"
DEFAULT_MD = REPO / "reports" / "CLINICAL_EVIDENCE_AGENT_STANDARDS_REPORT.md"

PASS = "PASS"
FAIL = "FAIL"
HUMAN_GATE = "HUMAN_GATE"
DISCLAIMER = (
    "Cần bác sĩ kiểm chứng. Đây là kiểm chuẩn agent/pipeline kỹ thuật; không thay "
    "xác minh nguồn online, thẩm định chuyên môn, hoặc quyết định áp dụng lâm sàng."
)


@dataclass(frozen=True)
class StandardCheck:
    check_id: str
    title: str
    status: str
    evidence: list[str]
    proves: str
    limitation: str
    missing: list[str]
    human_action: str = ""


@dataclass(frozen=True)
class AgentGateContract:
    gate_id: str
    name: str
    owner_agent: str
    trigger: str
    automated_checks: list[str]
    required_artifacts: list[str]
    fail_closed_when: list[str]
    human_gate: bool
    output_state: str


@dataclass(frozen=True)
class ReleasePacketContract:
    kind: str
    decision: str
    covered_gate_ids: list[str]
    minimum_artifacts: list[str]
    required_commands: list[str]
    hard_stop_reason_codes: list[str]
    doctor_attestations: list[str]
    non_goals: list[str]


def build_agent_contract() -> list[AgentGateContract]:
    """Hợp đồng vận hành tối thiểu cho mỗi lượt cập nhật chứng cứ lâm sàng."""

    return [
        AgentGateContract(
            gate_id="CEG1",
            name="Đóng khung câu hỏi và phạm vi ngoại trú",
            owner_agent="dieu-phoi-lam-sang -> cap-nhat-guideline",
            trigger="Bác sĩ yêu cầu cập nhật chứng cứ/khuyến cáo cho một vấn đề lâm sàng.",
            automated_checks=[
                "Không nhận hoặc xuất PII.",
                "Tự chọn khung PICO/PECO/PIRT/PROGRESS/CoCoPop/SPIDER/ECLIPSE phù hợp.",
                "Gắn bối cảnh ngoại trú Việt Nam và nhóm đặc biệt liên quan.",
            ],
            required_artifacts=["clinical_question_frame", "scope_and_population"],
            fail_closed_when=[
                "Thiếu quần thể/bối cảnh làm thay đổi an toàn xử trí.",
                "Có PII chưa được khử hoặc pseudonymize.",
            ],
            human_gate=False,
            output_state="framed_request",
        ),
        AgentGateContract(
            gate_id="CEG2",
            name="Tìm nguồn chính thống và đối chiếu định danh",
            owner_agent="tra-cuu-chung-cu",
            trigger="Câu hỏi đã được đóng khung.",
            automated_checks=[
                "Ưu tiên guideline/HTA/regulatory source chính thức.",
                "Đối chiếu PubMed/Europe PMC để lấy PMID/DOI khi có.",
                "Gắn PARTIAL hoặc chưa xác minh khi thiếu nguồn truy nguyên.",
                "Không bịa DOI, PMID, ngày phiên bản hoặc phân hạng.",
            ],
            required_artifacts=["source_table", "pmid_doi_url_index", "currency_note"],
            fail_closed_when=[
                "Không có PMID/DOI/URL cho điểm thực hành quan trọng.",
                "Nguồn không khớp tiêu đề/tổ chức/ngày/quần thể.",
                "Nguồn bị rút lại hoặc không truy nguyên được nhưng vẫn được dùng để đổi thực hành.",
            ],
            human_gate=False,
            output_state="verified_sources_or_partial",
        ),
        AgentGateContract(
            gate_id="CEG3",
            name="Thẩm định và chuyển hóa thành quyết định thực hành",
            owner_agent="cap-nhat-guideline -> huong-dan-lam-sang",
            trigger="Nguồn đã đủ để tổng hợp.",
            automated_checks=[
                "Giữ nguyên grading/class/level của nguồn.",
                "Không tự gán GRADE khi nguồn không cấp.",
                "Tách khuyến cáo nguồn, độ chắc chắn chứng cứ và đánh giá vận hành.",
                "Trích hiệu số đúng như nguồn báo cáo.",
                "Nêu cả hai chiều khi chứng cứ xung đột.",
            ],
            required_artifacts=["practice_decision_table", "appraisal_notes", "evidence_to_decision_summary"],
            fail_closed_when=[
                "Không truy được grading provenance.",
                "Hiệu số hoặc kết luận không khớp nguồn.",
                "Có chống chỉ định/cờ đỏ quan trọng chưa được nêu.",
            ],
            human_gate=False,
            output_state="review_ready_recommendations",
        ),
        AgentGateContract(
            gate_id="CEG4",
            name="Dựng Evidence Workbench và chạy cổng nguồn nghiêm ngặt",
            owner_agent="huong-dan-lam-sang",
            trigger="Có bảng quyết định thực hành review-ready.",
            automated_checks=[
                "Dùng template Evidence Workbench mặc định.",
                "Chạy verify_dashboard.py --online --strict-sources với dashboard thật.",
                "Có disclaimer, decision, gradeLevel và export CSV/JSON.",
                "Không sinh ID Master hoặc Cổng A/B trong dashboard vấn đề riêng lẻ.",
            ],
            required_artifacts=["evidence_workbench_html", "dashboard_verify_log"],
            fail_closed_when=[
                "verify_dashboard fail.",
                "Dashboard chứa PII.",
                "Item đổi thực hành thiếu PMID/DOI/URL hoặc strict source mismatch.",
            ],
            human_gate=False,
            output_state="dashboard_passed_or_blocked",
        ),
        AgentGateContract(
            gate_id="CEG5",
            name="An toàn thuốc, cờ đỏ và bản địa hóa Việt Nam",
            owner_agent="huong-dan-lam-sang -> ke-don-an-toan-benh-man",
            trigger="Dashboard có thuốc, nhóm đặc biệt, hoặc khuyến cáo cần triển khai tại Việt Nam.",
            automated_checks=[
                "Chạy drug_safety_scan.py khi có thuốc và người cao tuổi/đa thuốc.",
                "Đối chiếu Beers/STOPP-START như lớp nhắc, không thay bác sĩ.",
                "Đối chiếu BYT/kcb.vn hoặc registry nội bộ khi có tài liệu phù hợp.",
                "Gắn [CẦN XÁC NHẬN TẠI ĐƠN VỊ] cho thuốc/xét nghiệm/luồng phụ thuộc nguồn lực.",
            ],
            required_artifacts=["safety_limits_table", "vn_localization_note", "drug_safety_log_if_applicable"],
            fail_closed_when=[
                "Khuyến cáo thuốc nguy cơ cao thiếu cảnh báo/monitoring.",
                "Cờ đỏ hoặc chỉ định chuyển tuyến bị bỏ sót.",
                "Quyết định phụ thuộc nguồn lực nhưng không gắn nhãn cần xác nhận tại đơn vị.",
            ],
            human_gate=False,
            output_state="localized_safety_checked_package",
        ),
        AgentGateContract(
            gate_id="CEG6",
            name="Tích lũy thư viện, phái sinh và đồng bộ hub",
            owner_agent="cap-nhat-guideline",
            trigger="Dashboard đã qua cổng liêm chính.",
            automated_checks=[
                "Chạy build_library.py add.",
                "Chạy make_derivatives.py để sinh tờ dặn, slide outline, kịch bản TikTok.",
                "Chạy sync_all.py để nạp hub với quarantine cho thẻ không truy nguyên.",
                "Sản phẩm phái sinh không chứa liều trong nội dung cho người bệnh/TikTok.",
            ],
            required_artifacts=["library_entry", "derivatives", "sync_all_log"],
            fail_closed_when=[
                "Thẻ không truy nguyên bị nạp vào evidence_cards.",
                "Sản phẩm phái sinh có PII hoặc thiếu disclaimer.",
                "Hub/WebApp không được đồng bộ sau khi dashboard PASS.",
            ],
            human_gate=False,
            output_state="hub_synced_review_queue",
        ),
        AgentGateContract(
            gate_id="CEG7",
            name="Guardrail cuối và bác sĩ quyết định áp dụng",
            owner_agent="tham-dinh-dau-ra -> bác sĩ",
            trigger="Gói cập nhật đã sẵn sàng giao bác sĩ.",
            automated_checks=[
                "Chạy R1-R7 liêm chính và Q1-Q7 Med-PaLM.",
                "Q2/Q5 đỏ thì chuyển bác sĩ phán định.",
                "Không auto_apply, không real_patient_data_allowed.",
                "Cổng A/B chỉ mở khi bác sĩ duyệt rõ ràng.",
            ],
            required_artifacts=["final_guardrail_result", "doctor_review_packet"],
            fail_closed_when=[
                "Còn lỗi đỏ ở R1-R7 hoặc Q1-Q7.",
                "Tự nhận đã áp dụng cho bệnh nhân hoặc cập nhật Master như đã duyệt.",
                "Thiếu dòng 'Cần bác sĩ kiểm chứng'.",
            ],
            human_gate=True,
            output_state="doctor_gate_required_before_clinical_use",
        ),
    ]


def build_release_packet_contract() -> ReleasePacketContract:
    """Gói tối thiểu phải có trước khi phát hành một cập nhật chứng cứ thật."""

    gates = build_agent_contract()
    artifacts: list[str] = []
    for gate in gates:
        artifacts.extend(gate.required_artifacts)
    return ReleasePacketContract(
        kind="clinical_evidence_update_release_packet_contract",
        decision="BLOCKED_UNTIL_DOCTOR_REVIEW",
        covered_gate_ids=[gate.gate_id for gate in gates],
        minimum_artifacts=sorted(set(artifacts)),
        required_commands=[
            "verify_dashboard.py <dashboard>.html --online --strict-sources",
            "drug_safety_scan.py <dashboard>.html nếu có thuốc + người cao tuổi/đa thuốc",
            "build_library.py add <dashboard>.html",
            "make_derivatives.py <dashboard>.html",
            "EBM_MASTER/tools/sync_all.py",
            "tham-dinh-dau-ra R1-R7 + Q1-Q7 trước khi giao bác sĩ",
        ],
        hard_stop_reason_codes=[
            "PII_DETECTED",
            "SOURCE_UNVERIFIED",
            "STRICT_SOURCE_GATE_FAILED",
            "GRADE_SELF_ASSIGNED",
            "RED_FLAG_OR_CONTRAINDICATION_MISSING",
            "DRUG_SAFETY_SCAN_REQUIRED",
            "HUB_SYNC_OR_QUARANTINE_FAILED",
            "FINAL_GUARDRAIL_RED",
            "DOCTOR_REVIEW_MISSING",
        ],
        doctor_attestations=[
            "Đã mở và kiểm nguồn chính cho các điểm có thể đổi thực hành.",
            "Đã xác nhận tính phù hợp tại đơn vị, thuốc/xét nghiệm/chi phí/BHYT và tuyến chuyển.",
            "Đã rà nhóm nguy cơ cao, tương tác, chống chỉ định, monitoring và cờ đỏ.",
            "Đã quyết định rõ: chỉ lưu hàng chờ, áp dụng chọn lọc, hoặc không đổi thực hành.",
        ],
        non_goals=[
            "Không tự áp dụng cho bệnh nhân thật.",
            "Không thay thế bác sĩ, IRB, hội đồng thuốc, pháp chế hoặc UAT/bảo mật triển khai.",
            "Không biến dashboard vấn đề riêng lẻ thành bản ghi Master đã duyệt khi chưa có lệnh duyệt.",
        ],
    )


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        try:
            return str(path.relative_to(ROOT))
        except ValueError:
            return str(path)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def _missing_files(paths: Iterable[Path]) -> list[str]:
    return [f"missing_file:{_rel(path)}" for path in paths if not path.exists()]


def _missing_tokens(path: Path, tokens: Iterable[str]) -> list[str]:
    if not path.exists():
        return [f"missing_file:{_rel(path)}"]
    text = _read(path)
    return [f"{_rel(path)} missing token: {token}" for token in tokens if token not in text]


def _check_agents() -> StandardCheck:
    files = [
        AGENTS / "cap-nhat-guideline.md",
        AGENTS / "tra-cuu-chung-cu.md",
        AGENTS / "huong-dan-lam-sang.md",
        AGENTS / "tham-dinh-dau-ra.md",
    ]
    missing: list[str] = []
    missing.extend(_missing_files(files))
    missing.extend(_missing_tokens(AGENTS / "cap-nhat-guideline.md", (
        "CỔNG B",
        "PARTIAL",
        "WHO/NICE/ESC/AHA/ADA/KDIGO/GOLD/GINA/Bộ Y tế",
        "PMID/DOI/URL",
        "KHÔNG tự đổi thực hành",
        "tham-dinh-dau-ra",
    )))
    missing.extend(_missing_tokens(AGENTS / "tra-cuu-chung-cu.md", (
        "Cochrane",
        "PubMed/Europe PMC = LỚP ĐỐI CHIẾU",
        "Corrective self-RAG",
        "PARTIAL",
        "PMID/DOI",
        "sang-loc-co-do",
    )))
    missing.extend(_missing_tokens(AGENTS / "huong-dan-lam-sang.md", (
        "CỔNG A",
        "CỔNG B",
        "GRADE Evidence-to-Decision",
        "Evidence Workbench",
        "verify_dashboard.py --online",
        "sync_all.py",
        "gradeLevel:'na'",
    )))
    missing.extend(_missing_tokens(AGENTS / "tham-dinh-dau-ra.md", (
        "R1",
        "R7",
        "Q1",
        "Q7",
        "Q2/Q5",
        "TRẢ-VỀ-SỬA",
    )))
    return StandardCheck(
        check_id="EAS1",
        title="Agent cốt lõi cho cập nhật chứng cứ",
        status=FAIL if missing else PASS,
        evidence=[_rel(path) for path in files],
        proves=(
            "Các agent tìm nguồn, cập nhật guideline, chuyển hóa thành khuyến cáo và kiểm đầu ra "
            "đều có ranh giới/cổng bắt buộc."
        ),
        limitation="Không kiểm nội dung từng câu trả lời LLM; chỉ kiểm hợp đồng nguồn agent.",
        missing=missing,
    )


def _check_skill_mirror() -> StandardCheck:
    skill = SKILL_ROOT / "SKILL.md"
    refs = [SKILL_ROOT / "references" / f"{idx:02d}-{name}.md" for idx, name in (
        (1, "nguon-va-xac-minh"),
        (2, "cong-cu-tham-dinh-va-grade"),
        (3, "thich-ung-viet-nam"),
        (4, "thuoc-khang-sinh-va-cong-cu"),
        (6, "pico-va-trich-dan"),
        (7, "mo-hinh-cau-hoi-va-khung-thay-the"),
        (8, "xuat-san-pham-phai-sinh"),
        (9, "an-toan-thuoc-overlay"),
        (10, "giam-sat-dinh-ky"),
        (11, "guideline-bo-y-te-vn"),
    )]
    quality = [
        SKILL_ROOT / "quality" / "acceptance-checklist.md",
        SKILL_ROOT / "quality" / "web-dashboard-acceptance-checklist.md",
    ]
    missing: list[str] = []
    missing.extend(_missing_files([skill, *refs, *quality]))
    missing.extend(_missing_tokens(skill, (
        "Evidence Workbench",
        "verify_dashboard.py --online",
        "drug_safety_scan.py",
        "build_library.py add",
        "make_derivatives.py",
        "sync_all.py",
        "Không mặc định coi Web Dashboard theo vấn đề cụ thể là bản ghi đã được duyệt vào Master",
        "Chốt kiểm đầu ra 2 LỚP",
    )))
    missing.extend(_missing_tokens(quality[0], (
        "Không tự gán GRADE",
        "PICO đủ 5 dòng",
        "KHÔNG còn thẻ markup trích dẫn thô",
        "CẦN XÁC NHẬN TẠI ĐƠN VỊ",
    )))
    missing.extend(_missing_tokens(quality[1], (
        "verify_dashboard.py <dashboard>.html --online --strict-sources",
        "Chuẩn & chất lượng",
        "CSV",
        "JSON",
        "không phải ID Master",
    )))
    return StandardCheck(
        check_id="EAS2",
        title="Skill mirror và acceptance checklist",
        status=FAIL if missing else PASS,
        evidence=[_rel(path) for path in [skill, *refs, *quality]],
        proves="Skill đã đồng bộ đủ checklist nguồn, PICO, dashboard, phái sinh, drug safety, BYT và kiểm cuối.",
        limitation="Checklist là hợp đồng vận hành; dashboard thật vẫn cần chạy verifier trên file cụ thể.",
        missing=missing,
    )


def _check_source_integrity_contract() -> StandardCheck:
    connector = AGENTS / "_CONNECTOR-CHUNG-CU.md"
    guideline = AGENTS / "_NGUON-GUIDELINE-TU-DONG.md"
    pipeline = ROOT_TOOLS / "verify_clinical_evidence_update_pipeline.py"
    verify_dashboard = DASH_ROOT / "tools" / "verify_dashboard.py"
    missing: list[str] = []
    missing.extend(_missing_files([connector, guideline, pipeline, verify_dashboard]))
    missing.extend(_missing_tokens(connector, (
        "nguồn CHÍNH THỐNG trước",
        "PubMed/Europe PMC — LỚP ĐỐI CHIẾU",
        "PMID/DOI",
        "PARTIAL",
        "KHỬ PII Ở ĐIỂM GỌI",
        "Cochrane",
        "openFDA",
        "DailyMed",
    )))
    missing.extend(_missing_tokens(guideline, (
        "KHÔNG được tự kết luận",
        "URL chính thức + PMID/DOI",
        "verification_status=\"chưa xác minh\"",
        "KHÔNG tự đổi thực hành",
        "Cục KCB — kcb.vn/phac-do",
    )))
    missing.extend(_missing_tokens(pipeline, (
        "--strict-sources",
        "verify_dashboard.py --online --strict-sources",
        "standards",
        "PMID/DOI/URL",
    )))
    missing.extend(_missing_tokens(verify_dashboard, (
        "strict-sources",
        "pii",
        "PMID",
        "DOI",
    )))
    return StandardCheck(
        check_id="EAS3",
        title="Nguồn chính thống, chống citation ảo và PII outbound",
        status=FAIL if missing else PASS,
        evidence=[_rel(path) for path in [connector, guideline, pipeline, verify_dashboard]],
        proves=(
            "Hệ ưu tiên guideline/HTA chính thống, dùng PMID/DOI để đối chiếu, "
            "gắn PARTIAL khi thiếu nguồn và có strict source gate."
        ),
        limitation="Không chạy mạng trong verifier này; dashboard thật vẫn cần `--online --strict-sources`.",
        missing=missing,
    )


def _check_evidence_workbench_contract() -> StandardCheck:
    files = [
        ROOT / "dashboard_mockups" / "templates" / "evidence-workbench-template.html",
        MASTER_ROOT / "skill_assets" / "web-dashboard-evidence-workbench.html",
        SKILL_ROOT / "templates" / "web-dashboard-evidence-workbench.html",
        ROOT / "sync" / "skills" / "dark-analyst" / "templates" / "web-dashboard-evidence-workbench.html",
    ]
    missing: list[str] = []
    missing.extend(_missing_files(files))
    for path in files:
        missing.extend(_missing_tokens(path, (
            "EVIDENCE WORKBENCH",
            "CLINICAL QUICK VIEW",
            "EVIDENCE DETAIL VIEW",
            "GRADE EtD",
            "standards",
            "sourceHierarchy",
            "searchSources",
            "gradeLevel",
            "decision",
            "exportData('csv')",
            "exportData('json')",
            "Cần bác sĩ kiểm chứng",
        )))
    return StandardCheck(
        check_id="EAS4",
        title="Evidence Workbench chuẩn 3 cột",
        status=FAIL if missing else PASS,
        evidence=[_rel(path) for path in files],
        proves="Template nguồn, hub asset và skill mirror cùng giữ schema/UX bắt buộc cho cập nhật chứng cứ.",
        limitation="Không kiểm ảnh chụp giao diện; pipeline riêng kiểm fixture HTML và cổng nguồn.",
        missing=missing,
    )


def _check_safety_localization_and_outputs() -> StandardCheck:
    files = [
        DASH_ROOT / "tools" / "drug_safety_scan.py",
        DASH_ROOT / "tools" / "build_library.py",
        DASH_ROOT / "tools" / "make_derivatives.py",
        DASH_ROOT / "tools" / "surveillance_scan.py",
        DASH_ROOT / "vn-guidelines" / "registry.json",
        MASTER_ROOT / "tools" / "sync_all.py",
        SKILL_ROOT / "data" / "drug_flags.json",
        SKILL_ROOT / "references" / "09-an-toan-thuoc-overlay.md",
        SKILL_ROOT / "references" / "11-guideline-bo-y-te-vn.md",
    ]
    missing: list[str] = []
    missing.extend(_missing_files(files))
    missing.extend(_missing_tokens(DASH_ROOT / "tools" / "drug_safety_scan.py", (
        "Beers",
        "STOPP",
        "drug_flags",
    )))
    missing.extend(_missing_tokens(DASH_ROOT / "tools" / "make_derivatives.py", (
        "to-dan-nguoi-benh",
        "slide-outline",
        "kich-ban-tiktok",
        "Cần bác sĩ kiểm chứng",
    )))
    missing.extend(_missing_tokens(MASTER_ROOT / "tools" / "sync_all.py", (
        "harvest",
        "verify_dashboard.py",
        "quarantine",
        "build_antifacts.py",
    )))
    missing.extend(_missing_tokens(SKILL_ROOT / "references" / "11-guideline-bo-y-te-vn.md", (
        "Bộ Y tế",
        "kcb.vn",
        "QĐ",
        "CẦN XÁC NHẬN TẠI ĐƠN VỊ",
    )))
    return StandardCheck(
        check_id="EAS5",
        title="An toàn thuốc, bản địa hóa Việt Nam, phái sinh và hub",
        status=FAIL if missing else PASS,
        evidence=[_rel(path) for path in files],
        proves="Có lớp Beers/STOPP, BYT/kcb.vn, surveillance, derivatives, library và sync hub có quarantine.",
        limitation="Drug safety flags không đầy đủ; chỉ là lớp nhắc để bác sĩ và agent kê đơn an toàn rà sâu.",
        missing=missing,
    )


def _check_doctor_gate_boundaries() -> StandardCheck:
    files = [
        AGENTS / "_GIAM-SAT-CHUNG-CU-NOI-CHUNG.md",
        AGENTS / "_ROUTINE-AGENT-WIRING.md",
        AGENTS / "dieu-phoi-lam-sang.md",
        ROOT_TOOLS / "upgrade_verify.py",
    ]
    missing: list[str] = []
    missing.extend(_missing_files(files))
    missing.extend(_missing_tokens(AGENTS / "_GIAM-SAT-CHUNG-CU-NOI-CHUNG.md", (
        "Chỉ ĐỀ XUẤT, không tự áp dụng",
        "CỔNG A",
        "CỔNG B",
        "KHÔNG PII",
        "PARTIAL",
    )))
    missing.extend(_missing_tokens(AGENTS / "_ROUTINE-AGENT-WIRING.md", (
        "tham-dinh-dau-ra",
        "CỔNG A",
        "CỔNG B",
        "PMID/DOI",
    )))
    missing.extend(_missing_tokens(AGENTS / "dieu-phoi-lam-sang.md", (
        "Cổng A",
        "Cổng B",
        "C1",
        "C9",
        "tham-dinh-dau-ra",
    )))
    missing.extend(_missing_tokens(ROOT_TOOLS / "upgrade_verify.py", (
        "verify_clinical_evidence_update_pipeline.py",
        "verify_clinical_production_control_plane.py",
        "audit_ebm_system.py",
    )))
    return StandardCheck(
        check_id="EAS6",
        title="Ranh giới bác sĩ duyệt và upgrade_verify",
        status=HUMAN_GATE if not missing else FAIL,
        evidence=[_rel(path) for path in files],
        proves="Hệ có Cổng A/B, guardrail cuối và kiểm toàn hệ cho pipeline chứng cứ + control-plane lâm sàng.",
        limitation="Bác sĩ vẫn phải duyệt nguồn/khuyến cáo trước khi chuyển từ hàng chờ sang áp dụng.",
        missing=missing,
        human_action="Bác sĩ xác minh nguồn gốc, tính áp dụng tại đơn vị và quyết định trước khi áp dụng thực hành.",
    )


def evaluate_all(generated_at: str | None = None) -> dict:
    checks = [
        _check_agents(),
        _check_skill_mirror(),
        _check_source_integrity_contract(),
        _check_evidence_workbench_contract(),
        _check_safety_localization_and_outputs(),
        _check_doctor_gate_boundaries(),
    ]
    agent_contract = build_agent_contract()
    release_packet = build_release_packet_contract()
    fail_count = sum(1 for check in checks if check.status == FAIL)
    human_gate_count = sum(1 for check in checks if check.status == HUMAN_GATE)
    if fail_count:
        overall = "FAIL_CLOSED"
    elif human_gate_count:
        overall = "CLINICAL_EVIDENCE_AGENT_STANDARD_READY_WITH_DOCTOR_GATE"
    else:
        overall = "CLINICAL_EVIDENCE_AGENT_STANDARD_READY"
    return {
        "kind": "clinical_evidence_agent_standards_report",
        "generated_at": generated_at or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "overall_status": overall,
        "fail_count": fail_count,
        "human_gate_count": human_gate_count,
        "standards_ready": fail_count == 0,
        "doctor_review_required_before_apply": True,
        "clinical_production_allowed": False,
        "real_patient_data_allowed": False,
        "auto_apply_allowed": False,
        "agent_contract_gate_count": len(agent_contract),
        "agent_contract_human_gate_ids": [
            gate.gate_id for gate in agent_contract if gate.human_gate
        ],
        "agent_contract": [asdict(gate) for gate in agent_contract],
        "release_packet_contract": asdict(release_packet),
        "checks": [asdict(check) for check in checks],
        "disclaimer": DISCLAIMER,
    }


def markdown_report(report: dict) -> str:
    lines = [
        "# Clinical Evidence Agent Standards",
        "",
        f"- Generated: `{report['generated_at']}`",
        f"- Overall status: `{report['overall_status']}`",
        f"- Fail count: `{report['fail_count']}`",
        f"- Human gates: `{report['human_gate_count']}`",
        f"- Standards ready: `{report['standards_ready']}`",
        f"- Doctor review required before apply: `{report['doctor_review_required_before_apply']}`",
        f"- Clinical production allowed: `{report['clinical_production_allowed']}`",
        f"- Auto-apply allowed: `{report['auto_apply_allowed']}`",
        f"- Agent contract gates: `{report['agent_contract_gate_count']}`",
        f"- Agent contract human gates: `{', '.join(report['agent_contract_human_gate_ids'])}`",
        f"- Release packet decision: `{report['release_packet_contract']['decision']}`",
        "",
        "| Check | Status | Proves | Limitation | Missing |",
        "|---|---|---|---|---|",
    ]
    for row in report["checks"]:
        missing = "<br>".join(row["missing"]) if row["missing"] else "-"
        lines.append(
            "| {check_id} {title} | {status} | {proves} | {limitation} | {missing} |".format(
                check_id=row["check_id"],
                title=row["title"],
                status=row["status"],
                proves=row["proves"],
                limitation=row["limitation"],
                missing=missing,
            )
        )
    packet = report["release_packet_contract"]
    lines.extend([
        "",
        "## Release Packet Contract",
        "",
        f"- Decision: `{packet['decision']}`",
        f"- Covered gates: `{', '.join(packet['covered_gate_ids'])}`",
        f"- Minimum artifacts: `{len(packet['minimum_artifacts'])}`",
        "",
        "| Required Command |",
        "|---|",
    ])
    for command in packet["required_commands"]:
        lines.append(f"| `{command}` |")
    lines.extend([
        "",
        "| Hard Stop Reason |",
        "|---|",
    ])
    for reason in packet["hard_stop_reason_codes"]:
        lines.append(f"| `{reason}` |")
    lines.extend([
        "",
        "## Agent Gate Contract",
        "",
        "| Gate | Owner | Human Gate | Output State | Fail-Closed When |",
        "|---|---|---|---|---|",
    ])
    for gate in report["agent_contract"]:
        fail_closed = "<br>".join(gate["fail_closed_when"])
        lines.append(
            "| {gate_id} {name} | {owner_agent} | {human_gate} | {output_state} | {fail_closed} |".format(
                gate_id=gate["gate_id"],
                name=gate["name"],
                owner_agent=gate["owner_agent"],
                human_gate=gate["human_gate"],
                output_state=gate["output_state"],
                fail_closed=fail_closed,
            )
        )
    lines.extend(["", DISCLAIMER, ""])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify clinical evidence update agent standards.")
    parser.add_argument("--json", action="store_true", help="Print full JSON report")
    parser.add_argument("--write", action="store_true", help="Write JSON/Markdown reports")
    parser.add_argument("--generated-at", help="Fixed ISO timestamp for tests")
    args = parser.parse_args(argv)

    report = evaluate_all(generated_at=args.generated_at)
    if args.write:
        DEFAULT_JSON.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        DEFAULT_MD.write_text(markdown_report(report), encoding="utf-8")
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"overall_status={report['overall_status']}")
        print(f"fail_count={report['fail_count']}")
        print(f"human_gate_count={report['human_gate_count']}")
        print(f"standards_ready={report['standards_ready']}")
        print(f"doctor_review_required_before_apply={report['doctor_review_required_before_apply']}")
        print(f"clinical_production_allowed={report['clinical_production_allowed']}")
        print(f"auto_apply_allowed={report['auto_apply_allowed']}")
        print(f"agent_contract_gate_count={report['agent_contract_gate_count']}")
        print("agent_contract_human_gate_ids=" + ",".join(report["agent_contract_human_gate_ids"]))
        print("release_packet_decision=" + report["release_packet_contract"]["decision"])
        print("Cần bác sĩ kiểm chứng.")
    return 0 if report["fail_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
