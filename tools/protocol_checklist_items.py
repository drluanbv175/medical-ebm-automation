#!/usr/bin/env python3
"""Danh mục item của chuẩn ĐỀ CƯƠNG theo thiết kế — nguồn chính thức, sinh tự động.

SPIRIT 2025 (34 mục / 53 dòng kể cả mục con): nguyên văn tiếng Anh lấy từ TIÊU ĐỀ MỤC
của bài Explanation & Elaboration chính thức (các tiêu đề này lặp lại đúng nội dung
checklist), trích bằng script từ toàn văn PMC — KHÔNG gõ tay, không dịch để tránh lệch
nghĩa. Cột "vị trí gợi ý" ánh xạ sang khuôn đề cương 18 mục là DIỄN GIẢI của hệ thống,
bác sĩ/methodologist xác nhận khi điền checklist.

PRISMA-P 2015 (17 mục / 26 dòng): CHƯA có trong module — toàn văn PMC của bài statement
(PMC4320440) rụng bảng checklist, bài E&E (PMID 25555855) không có bản PMC, các trang
prisma-statement.org / equator-network.org bị chặn ở phiên cloud 06/09/2026. Không bịa
danh mục từ trí nhớ; items_for_design("sr_ma") trả None, missing_item_list_reason("sr_ma")
trả lý do.

MÃ THIẾT KẾ: mọi tra cứu đi qua skill_standards.canonical_design_code() — pipeline phát
bí danh ('sr_ma', 'rct_parallel'…) còn khoá ở đây là key CANON ('systematic_review', 'rct').
Bản đầu 06/09/2026 khoá theo bí danh 'sr_ma' nên nhánh PRISMA-P không bao giờ chạy tới
(G10 đã chuẩn hoá mã trước khi gọi) — đúng họ lỗi «hai module viết cho nhau mà chưa từng
nối» của G3 PREVALENCE 31/07; test hồi quy khoá cả hai dạng mã.
"""
from __future__ import annotations

from typing import Optional, Tuple

import skill_standards as S

SPIRIT_2025_PROVENANCE = {
    "standard": "SPIRIT 2025",
    "statement": "Chan AW et al. SPIRIT 2025 statement: updated guideline for protocols of "
                 "randomized trials. JAMA 2025;334(5):435-443. doi:10.1001/jama.2025.4486 "
                 "(PMID 40294593); đồng công bố BMJ/Lancet/Nat Med/PLOS Med.",
    "items_source": "SPIRIT 2025 explanation and elaboration. BMJ 2025. "
                    "doi:10.1136/bmj-2024-081660 (PMID 40294956; PMC12128891)",
    "retrieved": "2026-09-06 qua PubMed/PMC E-utilities",
    "n_items": 34,
    "n_rows": 53,
    "wording": "nguyên văn tiếng Anh từ tiêu đề mục của bài E&E; không dịch",
}

# (mã mục, nguyên văn tiếng Anh, vị trí gợi ý trong khuôn đề cương 18 mục)
SPIRIT_2025_ITEMS: Tuple[Tuple[str, str, str], ...] = (
    ("1a", "Title stating the trial design, population, and interventions, with identification as a protocol", "Thông tin kiểm soát · §1"),
    ("1b", "Structured summary of trial design and methods, including items from the World Health Organization Trial Registration Data Set", "§1 Tóm tắt (kèm WHO TRDS)"),
    ("2", "Version date and identifier", "Thông tin kiểm soát"),
    ("3a", "Names, affiliations, and roles of protocol contributors", "Thông tin kiểm soát · §17"),
    ("3b", "Name and contact information for the trial sponsor", "§17"),
    ("3c", "Role of trial sponsor and funders in design, conduct, analysis, and reporting of trial; including any authority over these activities", "§17 · §16 (COI)"),
    ("3d", "Composition, roles, and responsibilities of the coordinating site, steering committee, endpoint adjudication committee, data management team, and other individuals or groups overseeing the trial, if applicable", "§17"),
    ("4", "Name of trial registry, identifying number (with URL), and date of registration. If not yet registered, name of intended registry", "§16 (đăng ký) · §15"),
    ("5", "Where the trial protocol and statistical analysis plan can be accessed", "§12 · §16"),
    ("6", "Where and how the individual deidentified participant data (including data dictionary), statistical code, and any other materials will be accessible", "§11 · §16"),
    ("7a", "Sources of funding and other support (eg, supply of drugs)", "§17"),
    ("7b", "Financial and other conflicts of interest for principal investigators and steering committee members", "§15 · §16"),
    ("8", "Plans to communicate trial results to participants, healthcare professionals, the public, and other relevant groups (eg, reporting in trial registry, plain language summary, publication)", "§16"),
    ("9a", "Scientific background and rationale, including summary of relevant studies (published and unpublished) examining benefits and harms for each intervention", "§2 · §3"),
    ("9b", "Explanation for choice of comparator", "§3 · §6.2"),
    ("10", "Specific objectives related to benefits and harms", "§5"),
    ("11", "Details of, or plans for, patient or public involvement in the design, conduct, and reporting of the trial", "§6.5 (PPI)"),
    ("12", "Description of trial design including type of trial (eg, parallel group, crossover), allocation ratio, and framework (eg, superiority, equivalence, non-inferiority, exploratory)", "§6.1"),
    ("13", "Settings (eg, community, hospital) and locations (eg, countries, sites) where the trial will be conducted", "§6.1"),
    ("14a", "Eligibility criteria for participants", "§7.1 · §7.2"),
    ("14b", "If applicable, eligibility criteria for sites and for individuals who will deliver the interventions (eg, surgeons, physiotherapists)", "§7"),
    ("15a", "Intervention and comparator with sufficient details to allow replication including how, when, and by whom they will be administered. If relevant, where additional materials describing the intervention and comparator (eg, intervention manual) can be accessed", "§6.2 (mô tả theo TIDieR)"),
    ("15b", "Criteria for discontinuing or modifying allocated intervention/comparator for a trial participant (eg, drug dose change in response to harms, participant request, or improving/worsening disease)", "§6.2 (tham chiếu) · SAP §15"),
    ("15c", "Strategies to improve adherence to intervention/comparator protocols, if applicable, and any procedures for monitoring adherence (eg, drug tablet return, sessions attended)", "§6.2 (tham chiếu) · SAP §15"),
    ("15d", "Concomitant care that is permitted or prohibited during the trial", "§6.2"),
    ("16", "Primary and secondary outcomes, including the specific measurement variable (eg, systolic blood pressure), analysis metric (eg, change from baseline, final value, time to event), method of aggregation (eg, median, proportion), and time point for each outcome", "§8"),
    ("17", "How harms are defined and will be assessed (eg, systematically, non-systematically)", "§8 · §15"),
    ("18", "Time schedule of enrolment, interventions (including any run-ins and washouts), assessments, and visits for participants. A schematic diagram is highly recommended (see)", "§6.4 · §10 (sơ đồ lịch SPIRIT)"),
    ("19", "How sample size was determined, including all assumptions supporting the sample size calculation", "§9"),
    ("20", "Strategies for achieving adequate participant enrolment to reach target sample size", "§7.3"),
    ("21a", "Who will generate the random allocation sequence and the method used", "§6.3"),
    ("21b", "Type of randomisation (simple or restricted) and details of any factors for stratification. To reduce predictability of a random sequence, other details of any planned restriction (eg, blocking) should be provided in a separate document that is unavailable to those who enrol participants or assign interventions", "§6.3"),
    ("22", "Mechanism used to implement the random allocation sequence (eg, central computer/telephone; sequentially numbered, opaque, sealed containers), describing any steps to conceal the sequence until interventions are assigned", "§6.3"),
    ("23", "Whether the personnel who will enrol and those who will assign participants to the interventions will have access to the random allocation sequence", "§6.3"),
    ("24a", "Who will be blinded after assignment to interventions (eg, participants, care providers, outcome assessors, data analysts)", "§6.3 · §14"),
    ("24b", "If blinded, how blinding will be achieved and description of the similarity of interventions", "§6.3 · §14"),
    ("24c", "If blinded, circumstances under which unblinding is permissible, and procedure for revealing a participant’s allocated intervention during the trial", "§6.3 · §15"),
    ("25a", "Plans for assessment and collection of trial data, including any related processes to promote data quality (eg, duplicate measurements, training of assessors) and a description of trial instruments (eg, questionnaires, laboratory tests) along with their reliability and validity, if known. Reference to where data collection forms can be accessed, if not in the protocol", "§10"),
    ("25b", "Plans to promote participant retention and complete follow-up, including list of any outcome data to be collected for participants who discontinue or deviate from intervention protocols", "§7.3 · §10"),
    ("26", "Plans for data entry, coding, security, and storage, including any related processes to promote data quality (eg, double data entry; range checks for data values). Reference to where details of data management procedures can be accessed, if not in the protocol", "§11"),
    ("27a", "Statistical methods used to compare groups for primary and secondary outcomes, including harms", "§12"),
    ("27b", "Definition of who will be included in each analysis (eg, all randomised participants), and in which group", "§12"),
    ("27c", "How missing data will be handled in the analysis", "§12"),
    ("27d", "Methods for any additional analyses (eg, subgroup and sensitivity analyses)", "§12"),
    ("28a", "Composition of data monitoring committee (DMC); summary of its role and reporting structure; statement of whether it is independent from the sponsor and funder; conflicts of interest and reference to where further details about its charter can be found, if not in the protocol. Alternatively, an explanation of why a DMC is not needed", "§15 · §17"),
    ("28b", "Explanation of any interim analyses and stopping guidelines, including who will have access to these interim results and make the final decision to terminate the trial", "§12"),
    ("29", "Frequency and procedures for monitoring trial conduct. If there is no monitoring, give explanation", "§11 · §15"),
    ("30", "Plans for seeking research ethics committee/institutional review board approval", "§15"),
    ("31", "Plans for communicating important protocol modifications to relevant parties", "Thông tin kiểm soát · §15"),
    ("32a", "Who will obtain informed consent or assent from potential trial participants or authorised proxies, and how", "§15"),
    ("32b", "Additional consent provisions for collection and use of participant data and biological specimens in ancillary studies, if applicable", "§15"),
    ("33", "How personal information about potential and enrolled participants will be collected, shared, and maintained in order to protect confidentiality before, during, and after the trial", "§11 · §15"),
    ("34", "Provisions, if any, for ancillary and post-trial care, and for compensation to those who suffer harm from trial participation", "§15"),
)

assert len(SPIRIT_2025_ITEMS) == 53 and len({i for i, _, _ in SPIRIT_2025_ITEMS}) == 53

_PROTOCOL_CHECKLIST_BY_DESIGN = {
    "rct": ("SPIRIT 2025", SPIRIT_2025_ITEMS, SPIRIT_2025_PROVENANCE),
}

_NO_ITEM_LIST_REASON = {
    # key CANON của skill_standards (bí danh 'sr_ma'/'sr'/'meta_analysis' đều về đây)
    "systematic_review": (
        "PRISMA-P 2015",
        "Chưa có danh mục item trong kho: nguồn chính thức chưa lấy được "
        "ở phiên 06/09/2026 (bảng checklist rụng khi tải PMC; E&E không có PMC; website bị chặn). "
        "Điền checklist PRISMA-P từ bản gốc prisma-statement.org — KHÔNG dùng danh mục tự nhớ.",
    ),
}

# Mọi key phải là mã CANON — khoá theo bí danh là lỗi đã mắc (xem docstring module)
assert all(S.canonical_design_code(k) == k for k in _PROTOCOL_CHECKLIST_BY_DESIGN)
assert all(S.canonical_design_code(k) == k for k in _NO_ITEM_LIST_REASON)


def items_for_design(design_code: Optional[str]):
    """(tên chuẩn, tuple item, provenance) cho thiết kế có checklist protocol theo mục; None nếu không.

    Nhận cả mã canon lẫn bí danh pipeline ('rct_parallel', 'RCT'…). Thiết kế quan sát
    (cohort/case-control/cross-sectional) KHÔNG có checklist protocol theo mục được chấp nhận
    rộng rãi (STROBE là chuẩn BÁO CÁO) — trả None là sự thật, không phải thiếu sót."""
    return _PROTOCOL_CHECKLIST_BY_DESIGN.get(S.canonical_design_code(design_code) or "")


def missing_item_list_reason(design_code: Optional[str]):
    """(tên chuẩn, lý do) khi thiết kế CÓ chuẩn protocol nhưng kho CHƯA có danh mục item.

    Nhận cả mã canon ('systematic_review') lẫn bí danh ('sr_ma', 'meta_analysis')."""
    return _NO_ITEM_LIST_REASON.get(S.canonical_design_code(design_code) or "")
