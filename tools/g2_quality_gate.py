#!/usr/bin/env python3
"""Hợp đồng chất lượng G2: đạo đức, đồng thuận và đăng ký nghiên cứu.

Module cố ý tách ba sự kiện khác nhau:

1. Hệ thống đã sinh hồ sơ.
2. Hồ sơ đã đủ để nộp Hội đồng Đạo đức.
3. Hội đồng Đạo đức thật đã phê duyệt đúng phiên bản và đăng ký nghiên cứu
   đã hoàn tất đúng thời điểm khi bắt buộc.

Chỉ sự kiện thứ ba mới nhận ``PASS_G2_APPROVED``. Agent không được tạo chữ ký,
không được tự ghi phê duyệt và không được thay quyết định của IRB/IEC.
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
from typing import Any, Mapping, Optional

import annex2_quality_gate as A2X
import cong_song as CS
import gate_contract as GC
import pii_van_ban as PII
import pipeline_freshness as PF
import placeholder_contract as PC
import skill_standards as S

for _s_r4 in (_sys_r4.stdout, _sys_r4.stderr):
    try:
        _s_r4.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

STATUS_BLOCKED = "BLOCKED"
STATUS_DRAFT = "DRAFT_NEEDS_HUMAN_COMPLETION"
STATUS_READY = "READY_FOR_IRB_SUBMISSION"
STATUS_PENDING = "PENDING_REAL_IRB_OR_REGISTRATION"
STATUS_APPROVED = "PASS_G2_APPROVED"

QUALITY_CONTRACT_VERSION = "G2-2026.1"
ATTESTATION_SCHEMA = "g2-approval-attestation-v1"
ATTESTATION_BEGIN = "<!-- G2_APPROVAL_ATTESTATION_BEGIN -->"
ATTESTATION_END = "<!-- G2_APPROVAL_ATTESTATION_END -->"

WHO_TRDS_VERSION = "1.3.1"
WHO_TRDS_ITEM_COUNT = 24

WHO_TRDS_LABELS = {
    1: "Primary Registry and Trial Identifying Number",
    2: "Date of Registration in Primary Registry",
    3: "Secondary Identifying Numbers",
    4: "Source(s) of Monetary or Material Support",
    5: "Primary Sponsor",
    6: "Secondary Sponsor(s)",
    7: "Contact for Public Queries",
    8: "Contact for Scientific Queries",
    9: "Public Title",
    10: "Scientific Title",
    11: "Countries of Recruitment",
    12: "Health Condition(s) or Problem(s) Studied",
    13: "Intervention(s)",
    14: "Key Inclusion and Exclusion Criteria",
    15: "Study Type",
    16: "Date of First Enrolment",
    17: "Target Sample Size",
    18: "Recruitment Status",
    19: "Primary Outcome(s)",
    20: "Key Secondary Outcomes",
    21: "Ethics Review",
    22: "Completion Date",
    23: "Summary Results",
    24: "IPD Sharing Statement",
}

STANDARDS_BASIS = (
    {
        "standard": "WMA Declaration of Helsinki 2024",
        "scope": "Ethics review, consent, protocol amendments and registration before recruitment",
        "url": "https://www.wma.net/policies-post/wma-declaration-of-helsinki/",
    },
    {
        "standard": "ICH E6(R3)",
        "scope": "IRB/IEC, informed consent, safety and protocol control for clinical trials",
        "url": "https://database.ich.org/sites/default/files/ICH_E6%28R3%29_Step4_FinalGuideline_2025_0106.pdf",
    },
    {
        "standard": A2X.VERSION,
        "scope": "IRB/IEC, consent, privacy và data governance cho decentralised/pragmatic/RWD trials",
        "url": A2X.SOURCE_URL,
    },
    {
        "standard": f"WHO Trial Registration Data Set {WHO_TRDS_VERSION}",
        "scope": f"{WHO_TRDS_ITEM_COUNT} data items for complete trial registration",
        "url": "https://www.who.int/tools/clinical-trials-registry-platform/network/who-data-set",
    },
    {
        "standard": "Thông tư 43/2024/TT-BYT",
        "scope": "Tổ chức và hoạt động Hội đồng Đạo đức trong nghiên cứu y sinh học tại Việt Nam",
        "url": "https://vbpl.vn/TW/Pages/vbpq-van-ban-goc.aspx?ItemID=172919",
    },
    {
        "standard": "Luật 91/2025/QH15 và Nghị định 356/2025/NĐ-CP",
        "scope": "Bảo vệ dữ liệu cá nhân tại Việt Nam",
        "url": "https://vanban.chinhphu.vn/?classid=1&docid=214590&pageid=27160&typegroup=",
    },
)

_PACKAGE_MARKERS = (
    "TÀI LIỆU 1",
    "TÀI LIỆU 2",
    "TÀI LIỆU 3",
    "TÀI LIỆU 4",
    "TÀI LIỆU 5",
    "TÀI LIỆU 6",
    "TÀI LIỆU 7",
    "TÀI LIỆU 8",
    "PHIẾU ĐỒNG Ý THAM GIA NGHIÊN CỨU",
    "KẾ HOẠCH QUẢN LÝ DỮ LIỆU",
    "RỦI RO",
    "BỒI THƯỜNG KHI CÓ TỔN HẠI",
    "NGUỒN TÀI TRỢ VÀ XUNG ĐỘT LỢI ÍCH",
)

_PII_ONLY_HINTS = (
    "HỌ TÊN",
    "TÊN CHỦ NHIỆM",
    "ĐIỆN THOẠI",
    "EMAIL",
    "ĐỊA CHỈ",
    "CHỮ KÝ",
    "NGƯỜI LIÊN HỆ",
)

_RECRUITMENT_MODES = {
    "PROSPECTIVE_NEW_PARTICIPANTS",
    "RETROSPECTIVE_SECONDARY_DATA",
    "NOT_APPLICABLE",
}

# ── WHO TRDS mục 15 — MỘT bảng duy nhất (soát từng cổng G2-07, 04/10/2026) ────────────────────────────────────────
# Trước đây bản đọc trong hồ sơ .md (run_g2_auto) và bản JSON cổng chấm (build_registration_draft) giữ HAI bảng khác
# nhau (cohort «Observational» ở .md nhưng «Epidemiology» ở JSON) và .md in cứng «Blinded» cho mọi RCT. Nay cả hai đọc
# bảng này; các mục khoa học của bản .md dựng từ CHÍNH giá trị của bản JSON (who_trds_values) nên không thể lệch.
WHO_DESIGN_TYPE: dict[str, str] = {
    "rct": "Interventional",
    "cohort": "Observational",
    "case_control": "Observational",
    "cross_sectional": "Observational",
    "diagnostic": "Observational",
    "prediction": "Observational",
    "qualitative": "Observational",
    "sr_ma": "Not applicable - systematic review protocol",
}
WHO_PRIMARY_PURPOSE: dict[str, str] = {
    "rct": "Treatment",
    "diagnostic": "Diagnostic",
    "prediction": "Prognosis",
    "cohort": "Epidemiology",
    "case_control": "Epidemiology",
    "cross_sectional": "Epidemiology",
    "qualitative": "Health services research",
    "sr_ma": "Evidence synthesis",
}
MASKING_CAN_KHAI = "[CẦN — Open label / Single blind / Double blind: khai gate_params.G1.blinding]"
MASKING_KHONG_AP_DUNG = "Not applicable - no assigned intervention"

# ── ICF: nhãn mục bắt buộc theo thiết kế (G2-04, G2-10, G2-11) ──────────────────────────────────────────────────────
# Khớp NHÃN MỤC ở ĐẦU DÒNG («2b. PHÂN NHÓM NGẪU NHIÊN»), không khớp chuỗi trên cả tệp. Chung mọi thiết kế: 7 mục gốc +
# 1b/4b/4c/6c (Helsinki §26). RCT thêm 6b/6d và các yếu tố đồng thuận của thử nghiệm can thiệp theo ICH E6(R3) mục
# 2.8.10: phân nhóm ngẫu nhiên + xác suất (2b), quyền truy cập hồ sơ gốc của giám sát/kiểm tra/Hội đồng/cơ quan quản lý
# (5b), thông tin mới (6f), theo dõi khi ngừng/rút (6g), các trường hợp chấm dứt (6h) — đối chiếu nguyên văn ICH trước
# khi nộp. 6e (mẫu sinh học) là mục «XÓA nếu không áp dụng» nên không bắt buộc; hai bản Việt/Anh phải CÙNG tập mục.
NHAN_ICF_CHUNG = frozenset({"1", "1b", "2", "3", "4", "4b", "4c", "5", "6", "6c", "7"})
NHAN_ICF_RCT = frozenset({"2b", "5b", "6b", "6d", "6f", "6g", "6h"})
_NHAN_MUC_ICF_RE = re.compile(r"^\s*(\d{1,2}[a-h]?)\.\s+\S", re.MULTILINE)
_TIEU_DE_TAI_LIEU_RE = re.compile(r"^##\s+TÀI LIỆU\s+(\d+)\b", re.MULTILINE)
_TIEU_DE_CAP2_RE = re.compile(r"^##\s", re.MULTILINE)


def _thu_tu_nhan(nhan: str) -> tuple[int, str]:
    m = re.match(r"(\d+)([a-h]?)$", nhan)
    return (int(m.group(1)), m.group(2)) if m else (999, nhan)


def khoi_tai_lieu(package_text: str, so: int) -> str:
    """Nội dung của «## TÀI LIỆU <so>» tới tiêu đề «## » kế tiếp; rỗng nếu hồ sơ không có tài liệu đó."""
    for m in _TIEU_DE_TAI_LIEU_RE.finditer(package_text or ""):
        if int(m.group(1)) == so:
            ke = _TIEU_DE_CAP2_RE.search(package_text, m.end())
            return package_text[m.end(): ke.start() if ke else len(package_text)]
    return ""


def nhan_muc_icf(khoi: str) -> set[str]:
    """Tập nhãn mục của một phiếu đồng thuận («1», «1b», «6c»…) — chỉ dòng BẮT ĐẦU bằng nhãn."""
    return {m.group(1).lower() for m in _NHAN_MUC_ICF_RE.finditer(unicodedata.normalize("NFC", khoi or ""))}


def kiem_icf(package_text: str, design_code: str) -> tuple[list[str], list[str]]:
    """(mục bắt buộc thiếu ở ICF tiếng Việt, mục lệch giữa ICF tiếng Việt và tiếng Anh)."""
    vi = nhan_muc_icf(khoi_tai_lieu(package_text, 4))
    en = nhan_muc_icf(khoi_tai_lieu(package_text, 5))
    can = set(NHAN_ICF_CHUNG) | (set(NHAN_ICF_RCT) if design_code == "rct" else set())
    thieu = sorted(can - vi, key=_thu_tu_nhan)
    lech = sorted(vi ^ en, key=_thu_tu_nhan) if vi and en else []
    return thieu, lech


# ── Kế hoạch an toàn cho thử nghiệm can thiệp (G2-03, QĐ-4) ───────────────────────────────────────────────────────
# Trước đây G2-AUTO-07 dò ba cụm «AE/SAE», «DSMB», «quy tắc dừng» trên CẢ hồ sơ — chính khuôn sinh in sẵn ba cụm đó cho
# mọi RCT nên tiêu chí luôn đúng. Nay thử nghiệm can thiệp (RCT, hoặc PI khai safety_plan_required=true) phải có tệp
# kế hoạch an toàn riêng đủ 5 mục có nội dung thật VÀ PI ghi safety_plan_confirmed=true. Nội dung an toàn là quyết định
# của chủ nhiệm/nhà tài trợ/Hội đồng — máy chỉ dựng khung (khung_ke_hoach_an_toan), không điền.
MUC_KE_HOACH_AN_TOAN: tuple[tuple[str, str], ...] = (
    ("1", "1. Định nghĩa biến cố bất lợi (AE/SAE/SUSAR) và cách phân độ"),
    ("2", "2. Mốc và quy trình báo cáo an toàn"),
    ("3", "3. Quy tắc dừng (từng người tham gia và toàn nghiên cứu)"),
    ("4", "4. Hội đồng giám sát dữ liệu và an toàn (DSMB/DMC) hoặc lý do không lập"),
    ("5", "5. Biểu mẫu ghi nhận biến cố bất lợi"),
)


def ten_ke_hoach_an_toan(study: str) -> str:
    return f"G2_SAFETY_PLAN_{study}.md"


def can_ke_hoach_an_toan(design_code: str, meta: Optional[Mapping[str, Any]]) -> bool:
    return design_code == "rct" or _g2_meta(meta or {}).get("safety_plan_required") is True


def khung_ke_hoach_an_toan(study: str) -> str:
    """Khung tệp kế hoạch an toàn (chỉ tiêu đề + ô [CẦN]); run_g2_auto chỉ ghi khi tệp CHƯA có."""
    dong = [
        f"# KẾ HOẠCH AN TOÀN NGƯỜI THAM GIA — {study}",
        "",
        "> Khung do máy dựng (soát từng cổng G2-03). Nội dung an toàn do chủ nhiệm/nhà tài trợ/Hội đồng quyết định —",
        "> máy KHÔNG điền. Điền đủ 5 mục rồi PI ghi study_meta.gate_params.G2.safety_plan_confirmed=true.",
        "",
    ]
    for _so, tieu_de in MUC_KE_HOACH_AN_TOAN:
        dong += [f"## {tieu_de}", "", "[CẦN — chủ nhiệm điền]", ""]
    dong.append("> Cần bác sĩ kiểm chứng.")
    return "\n".join(dong) + "\n"


def kiem_ke_hoach_an_toan(out_dir: Path, study: str, design_code: str,
                          meta: Optional[Mapping[str, Any]]) -> tuple[str, str]:
    """(PASS|REVIEW, bằng chứng) cho G2-AUTO-07."""
    if not can_ke_hoach_an_toan(design_code, meta):
        return "PASS", "không phải RCT và PI không khai safety_plan_required=true — kế hoạch an toàn theo nguy cơ"
    ten = ten_ke_hoach_an_toan(study)
    try:
        text = unicodedata.normalize("NFC", (Path(out_dir) / ten).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError):
        return "REVIEW", f"thiếu {ten} — thử nghiệm can thiệp phải có kế hoạch an toàn riêng (run_g2_auto dựng khung)"
    phan: dict[str, str] = {}
    hien: Optional[str] = None
    for dong in text.splitlines():
        m = re.match(r"^##\s+(\d)\.", dong)
        if m:
            hien = m.group(1)
            phan.setdefault(hien, "")
        elif re.match(r"^#{1,2}\s", dong):
            hien = None
        elif hien is not None:
            phan[hien] += dong + "\n"
    van_de = []
    for so, tieu_de in MUC_KE_HOACH_AN_TOAN:
        if so not in phan:
            van_de.append(f"thiếu mục «{tieu_de}»")
        elif not phan[so].strip() or PC.co_o_trong(phan[so]):
            van_de.append(f"mục {so} còn trống/ô [CẦN]")
    if _g2_meta(meta or {}).get("safety_plan_confirmed") is not True:
        van_de.append("PI chưa ghi gate_params.G2.safety_plan_confirmed=true")
    return ("REVIEW", f"{ten}: " + "; ".join(van_de)) if van_de else ("PASS", f"{ten} đủ 5 mục; PI đã xác nhận")


# ── Liêm chính NỘI DUNG HIỆN HÀNH của hồ sơ (G2-02, CHUNG-G) ────────────────────────────────────────────────────────
# G2-AUTO-01 từng đọc checkpoint['guardrail'] — kết quả tính trên BẢN KHUÔN lúc sinh (C1a: sinh 31/07, biên tập tới
# 03/10). PII hay số IRB tự gán chèn vào SAU đó không bao giờ bị bắt. Nay chạy R1/R2/R3/R7 trên văn bản đang có.
# R4 (đủ ≥5 nhãn DRAFT) và R5 (≥10 ô [CẦN]) bị bỏ khỏi G2-AUTO-01: chúng phạt chính việc hoàn thiện hồ sơ (CHUNG-H).
_R2_SO_TU_GAN_RE = re.compile(r"(?:Mã nghiên cứu|[Ss]ố IRB)[:\s]+(?!.*\[CẦN)([A-Z0-9][A-Z0-9\-/\.]{3,})")
_R3_LOCKED_RE = re.compile(r"Trạng\s*thái\s*hiện\s*tại:\s*LOCKED", re.IGNORECASE)


def kiem_liem_chinh_noi_dung(package_text: str, attestation: Optional[Mapping[str, Any]] = None) -> list[str]:
    """Lỗi liêm chính trên nội dung HIỆN HÀNH (bỏ khối attestation). Số IRB/mã đăng ký trùng attestation được miễn."""
    att = attestation if isinstance(attestation, Mapping) else {}
    dang_ky = att.get("registration") if isinstance(att.get("registration"), Mapping) else {}
    mien = [str(x).strip() for x in (att.get("approval_number"), dang_ky.get("registration_id"))
            if str(x or "").strip()]
    base = unicodedata.normalize("NFC", strip_attestation(package_text or ""))
    loi: list[str] = []
    pii = PII.quet_pii_van_ban(base, che_do=PII.HO_SO, mien=mien)
    if pii:
        loi.append(f"R1 nghi PII trong hồ sơ hiện hành: {PII.tom_tat(pii)}")
    for m in _R2_SO_TU_GAN_RE.finditer(base):
        so = m.group(1)
        if not any(so in x or x in so for x in mien):
            loi.append(f"R2 số phê duyệt/mã nghiên cứu «{so}» không khớp quyết định IRB đã ghi (attestation) — "
                       "nếu là số thật đã cấp, ghi quyết định bằng approve_gate.py; nếu chưa có, để [CẦN]")
            break
    if "APPROVED_EXTERNALLY" in base:
        loi.append("R3 hồ sơ ghi APPROVED_EXTERNALLY — phê duyệt chỉ được ghi qua approve_gate (attestation + sổ cái)")
    elif _R3_LOCKED_RE.search(base):
        loi.append("R3 hồ sơ tự ghi «Trạng thái hiện tại: LOCKED» — khoá G2 chỉ qua approve_gate")
    thuong = base.lower()
    if "cần bác sĩ" not in thuong or "kiểm chứng" not in thuong:
        loi.append("R7 thiếu câu «Cần bác sĩ kiểm chứng»")
    return loi


# ── Dấu đầu vào mà Hội đồng Đạo đức đã duyệt (G2-08) ───────────────────────────────────────────────────────────────
# Sửa đề cương hay cỡ mẫu SAU khi Hội đồng duyệt từng không làm mất hiệu lực G2 (phiên bản «hiện hành» là giá trị
# khuôn «1.0» không ai cập nhật). approve_gate ghi dấu này vào attestation lúc ký; validate_attestation so lại — lệch ⇒
# cần sửa đổi đề cương (amendment) được Hội đồng duyệt rồi ký lại. Chỉ gồm quyết định khoa học/vận hành mà Hội đồng
# duyệt (không gồm risk register/kinh phí vốn cập nhật trong lúc làm).
_KHOA_DAU_VAO_G1 = ("population", "inclusion_criteria", "exclusion_criteria", "intervention_or_exposure", "comparator",
                    "objectives", "primary_outcome", "secondary_outcomes", "follow_up_schedule", "setting",
                    "recruitment_strategy", "estimand", "randomisation", "allocation_concealment", "blinding")


def dau_dau_vao_g2(out_dir: Path, meta: Optional[Mapping[str, Any]] = None) -> tuple[str, dict[str, Any]]:
    """(dấu 16 hex, thành phần) của thiết kế + quyết định G1 + cỡ mẫu G3 mà hồ sơ G2 trình Hội đồng."""
    out_dir = Path(out_dir)
    if not isinstance(meta, Mapping):
        meta = _read_json(out_dir / "study_meta.json")
    g1_cp = _read_json(out_dir / "G1_checkpoint.json")
    g3_cp = _read_json(out_dir / "G3_checkpoint.json")
    thiet_ke = (S.ma_thiet_ke_chuoi(str((g1_cp.get("design") or {}).get("internal_code") or ""))
                or S.ma_thiet_ke_chuoi(str(meta.get("design_code") or "")))
    n = g3_cp.get("confirmed_n") if g3_cp.get("confirmed_n") not in (None, "") else g3_cp.get("n_adjusted")
    g1_meta = _gate_meta(meta, "G1")
    thanh_phan = {"design_code": thiet_ke, "g1": {k: g1_meta.get(k) for k in _KHOA_DAU_VAO_G1}, "g3_n": n}
    return CS.dau_van_tay(thanh_phan), thanh_phan


def _criterion(
    criterion_id: str,
    label: str,
    status: str,
    evidence: str,
    action: str = "",
) -> dict[str, str]:
    return {
        "id": criterion_id,
        "label": label,
        "status": status,
        "evidence": evidence,
        "action": action,
    }


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _parse_iso_date(value: Any) -> Optional[date]:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


def _g2_meta(meta: Mapping[str, Any]) -> Mapping[str, Any]:
    params = meta.get("gate_params")
    if not isinstance(params, Mapping):
        return {}
    value = params.get("G2")
    return value if isinstance(value, Mapping) else {}


def _gate_meta(meta: Optional[Mapping[str, Any]], gate: str) -> Mapping[str, Any]:
    """Đọc dữ kiện đã được pin ở một cổng, không suy diễn từ văn bản tự do."""
    if not isinstance(meta, Mapping):
        return {}
    params = meta.get("gate_params")
    if not isinstance(params, Mapping):
        return {}
    value = params.get(gate)
    return value if isinstance(value, Mapping) else {}


# Vị từ GIÁ TRỊ TRƯỜNG của _real_text (WHO TRDS 13/14/19/20, vá 03/10/2026). Bộ cũ chỉ nhận
# «[CẦN|[CAN|[TBD|[TODO|[PENDING» nên «[TO BE COMPLETED]», «___», «……», «[đơn vị]», «<CẦN…>», «CHƯA XÁC NHẬN»,
# «[XÁC NHẬN THỦ CÔNG NGOÀI HỆ THỐNG]» ghim ở G0/G1 lọt thành «nội dung thật» (đo 03/10/2026) ⇒ nay AND thêm vị từ
# chung placeholder_contract.co_noi_dung_that (mọi họ). Bốn dấu hiệu cũ giữ NGUYÊN ngữ nghĩa (chuỗi con, không phân
# biệt hoa thường, không đòi ranh giới từ) qua them=.
_REAL_TEXT_DAU_HIEU_CU = ("[CẦN", "[TBD", "[TODO", "[PENDING")
# «[CAN» cũ (IGNORECASE, không ranh giới) báo nhầm tiêu chí thật «[Can thiệp giáo dục]», «[cancer cohort]»,
# «[Canxi máu]» (báo nhầm ĐÃ ĐO trong lượt kiểm 03/10/2026) — chỉ bỏ đúng hai dạng đó: «can» nối tiếp chữ cái
# và «can thiệp/thiep».
# Bản CHỮ HOA có ranh giới («[CAN BO SUNG]», «[CAN]») vẫn bị họ NHAN của hợp đồng bắt; bản thường như «[can bo sung]»,
# «[can]» vẫn bị luật này bắt.
_CAN_KHONG_DAU_RE = re.compile(r"\[\s*can(?![^\W\d_])(?!\s+thi[eệ]p)", re.IGNORECASE)


def _real_text(value: Any) -> Optional[str]:
    # Dict/list KHÔNG phải văn bản (vá 27/09/2026): str() của chúng là chuỗi repr Python — từng lọt vào mục #19 WHO TRDS
    # dưới dạng "{'name': ..., 'measure': ...}" mà G2-AUTO-08 vẫn PASS vì chuỗi đó «không trống».
    if isinstance(value, (Mapping, list, tuple, set)):
        return None
    text = str(value or "").strip()
    if (
        not text
        or _CAN_KHONG_DAU_RE.search(text)
        or not PC.co_noi_dung_that(text, them=_REAL_TEXT_DAU_HIEU_CU)
    ):
        return None
    return text


def _real_text_list(value: Any) -> list[str]:
    if isinstance(value, str):
        text = _real_text(value)
        return [text] if text else []
    if not isinstance(value, (list, tuple)):
        return []
    return [text for item in value if (text := _real_text(item))]


def strip_attestation(package_text: str) -> str:
    """Bỏ phụ lục attestation cũ để tính hash và ghi lại idempotent."""
    marker_index = package_text.rfind(ATTESTATION_BEGIN)
    if marker_index < 0:
        return package_text.rstrip() + "\n"
    prefix = package_text[:marker_index]
    heading = "\n---\n\n## PHỤ LỤC KIỂM TOÁN PHÊ DUYỆT G2"
    heading_index = prefix.rfind(heading)
    if heading_index >= 0:
        prefix = prefix[:heading_index]
    return prefix.rstrip() + "\n"


def append_attestation(package_text: str, attestation: Mapping[str, Any]) -> str:
    """Gắn phụ lục JSON có cấu trúc vào bản hồ sơ đã duyệt."""
    base = strip_attestation(package_text)
    payload = json.dumps(attestation, ensure_ascii=False, indent=2, sort_keys=True)
    return (
        f"{base}\n---\n\n## PHỤ LỤC KIỂM TOÁN PHÊ DUYỆT G2\n\n"
        f"{ATTESTATION_BEGIN}\n```json\n{payload}\n```\n{ATTESTATION_END}\n"
        "\n> Phụ lục này chỉ là dấu vết kiểm toán; quyết định thuộc Hội đồng Đạo đức.\n"
        "> Cần bác sĩ kiểm chứng.\n"
    )


def extract_attestation(package_text: str) -> dict[str, Any]:
    """Đọc phụ lục attestation cuối cùng; lỗi định dạng trả dict rỗng."""
    pattern = (
        rf"{re.escape(ATTESTATION_BEGIN)}\s*```json\s*(.*?)\s*```\s*"
        rf"{re.escape(ATTESTATION_END)}"
    )
    matches = re.findall(pattern, package_text, flags=re.DOTALL)
    if not matches:
        return {}
    try:
        value = json.loads(matches[-1])
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def who_trds_values(
    *,
    topic: str,
    design_code: str,
    design_primary: str,
    n_target: Optional[int],
    meta: Optional[Mapping[str, Any]] = None,
) -> dict[int, Any]:
    """Giá trị 24 mục WHO TRDS 1.3.1 từ dữ kiện PI đã pin; thiếu thì để trống/[CẦN] — KHÔNG suy diễn.

    Dùng chung cho bản JSON (build_registration_draft — cổng chấm đọc) và bản đọc trong hồ sơ .md (run_g2_auto,
    render_who_trds_khoa_hoc) để hai bản không bao giờ lệch nhau (G2-07)."""
    design_type = WHO_DESIGN_TYPE.get(design_code, "Other")
    g0 = _gate_meta(meta, "G0")
    g1 = _gate_meta(meta, "G1")
    g2 = _gate_meta(meta, "G2")
    primary_purpose = _real_text(g2.get("primary_purpose")) or WHO_PRIMARY_PURPOSE.get(design_code, "Other")
    intervention = (
        _real_text(g1.get("intervention_or_exposure"))
        or _real_text(g0.get("intervention"))
    )
    comparator = _real_text(g1.get("comparator")) or _real_text(g0.get("comparison"))
    inclusion = _real_text_list(g1.get("inclusion_criteria"))
    exclusion = _real_text_list(g1.get("exclusion_criteria"))
    # G1 có thể ghim kết cục chính dạng CÓ CẤU TRÚC {name, measure, timepoint, type} (C1a từ 02/09/2026) — lấy ĐÚNG từng
    # trường, thiếu trường nào mới lùi về G0 (vá 27/09/2026: trước đây str(dict) bị nhét nguyên vào «name»).
    kc_g1 = g1.get("primary_outcome")
    kc_g1 = kc_g1 if isinstance(kc_g1, Mapping) else {"name": kc_g1}
    primary_outcome = _real_text(kc_g1.get("name")) or _real_text(g0.get("primary_outcome"))
    primary_measure = _real_text(kc_g1.get("measure")) or _real_text(g0.get("primary_outcome_measure"))
    primary_timepoint = _real_text(kc_g1.get("timepoint")) or _real_text(g0.get("primary_outcome_timepoint"))
    secondary_outcomes = _real_text_list(g1.get("secondary_outcomes"))
    if not secondary_outcomes:
        secondary_outcomes = [
            item
            for item in _real_text_list(g0.get("outcomes"))
            if not primary_outcome or item.casefold() != primary_outcome.casefold()
        ]

    if design_code == "rct":
        intervention_value: Any = {
            "intervention": intervention,
            "comparator": comparator,
        }
        # VÁ 04/10/2026 (G2-07): masking lấy từ quyết định G1 (blinding/masking — cùng nguồn với dac_ta_thiet_ke);
        # chưa khai thì để ô [CẦN], KHÔNG in cứng «Blinded».
        masking = _real_text(g1.get("blinding")) or _real_text(g1.get("masking")) or MASKING_CAN_KHAI
        allocation = "Randomized"
    else:
        intervention_value = {
            "assigned_intervention": "Not applicable - no prospectively assigned intervention",
            "exposure_or_index_test": intervention,
        }
        masking = MASKING_KHONG_AP_DUNG
        allocation = "Non-randomized"
    primary_outcome_value = {
        "name": primary_outcome,
        "measure": primary_measure,
        "timepoint": primary_timepoint,
    }

    return {
        1: None,
        2: None,
        3: None,
        4: None,
        5: "[ĐIỀN TRỰC TIẾP TRÊN REGISTRY; KHÔNG LƯU PII TRONG HỆ THỐNG]",
        6: None,
        7: "[ĐIỀN LIÊN HỆ CÔNG KHAI TRỰC TIẾP TRÊN REGISTRY]",
        8: "[ĐIỀN LIÊN HỆ KHOA HỌC TRỰC TIẾP TRÊN REGISTRY]",
        # VÁ 04/10/2026 (G2-07): mục 9 (Public title — ngôn ngữ đại chúng) và 12 (Health condition) từng CHÉP tên đề
        # tài khoa học. Nay ưu tiên gate_params.G2.public_title/health_condition do PI khai; chưa khai thì vẫn dùng tên
        # đề tài làm điểm khởi đầu NHƯNG G2-AUTO-08b giữ REVIEW (registration_pi_confirmation_gaps).
        9: _real_text(g2.get("public_title")) or topic,
        10: topic,
        11: "Vietnam",
        12: _real_text(g2.get("health_condition")) or topic,
        13: intervention_value,
        14: {
            "inclusion": inclusion or None,
            "exclusion": exclusion or None,
        },
        15: {
            "design": design_type,
            "primary_purpose": primary_purpose,
            "allocation": allocation,
            "masking": masking,
            "description": design_primary,
        },
        16: None,
        17: n_target,
        18: "Not yet recruiting",
        19: primary_outcome_value,
        20: secondary_outcomes or None,
        21: {"status": "Not approved", "approval_date": None, "committee_ref": None},
        22: None,
        23: {
            "summary_results_date": None,
            "first_publication_date": None,
            "protocol_url": None,
        },
        24: {
            "plan_to_share_ipd": None,
            "what_when_how_with_whom": None,
        },
    }


def render_who_trds_khoa_hoc(values: Mapping[int, Any]) -> dict[int, str]:
    """Dòng chữ cho các mục 9/12/13/14/15/19/20 của khối WHO TRDS trong hồ sơ .md — dựng từ who_trds_values()."""
    def _o(v: Any, trong: str) -> str:
        t = _real_text(v)
        return t if t else trong

    v13 = values.get(13) if isinstance(values.get(13), Mapping) else {}
    if "intervention" in v13:
        d13 = (f"{_o(v13.get('intervention'), '[CẦN — từ PICO I]')}\n"
               f"            Comparator: {_o(v13.get('comparator'), '[CẦN — từ PICO C]')}")
    else:
        d13 = (f"{v13.get('assigned_intervention') or 'Not applicable'}\n"
               f"            Exposure/index test: {_o(v13.get('exposure_or_index_test'), '[CẦN — từ PICO I/E]')}")
    v14 = values.get(14) if isinstance(values.get(14), Mapping) else {}
    nhan = "; ".join(_real_text_list(v14.get("inclusion"))) or "[CẦN BỔ SUNG — từ protocol/PICO P]"
    loai = "; ".join(_real_text_list(v14.get("exclusion"))) or "[CẦN BỔ SUNG — từ protocol]"
    v15 = values.get(15) if isinstance(values.get(15), Mapping) else {}
    v19 = values.get(19) if isinstance(values.get(19), Mapping) else {}
    d19 = " — ".join(x for x in (_real_text(v19.get("name")), _real_text(v19.get("measure")),
                                 _real_text(v19.get("timepoint"))) if x)
    if not (_real_text(v19.get("name")) and _real_text(v19.get("measure")) and _real_text(v19.get("timepoint"))):
        d19 = (d19 + " " if d19 else "") + "[CẦN — tên kết cục + thước đo + thời điểm từ G0/G1]"
    v10 = _real_text(values.get(10))
    v9, v12 = _real_text(values.get(9)), _real_text(values.get(12))
    return {
        9: (v9 if v9 and v9 != v10 else
            (f"{v9 or ''} [CẦN PI KHAI — tiêu đề công khai bằng ngôn ngữ đại chúng: "
             "gate_params.G2.public_title]").strip()),
        12: (v12 if v12 and v12 != v10 else
             "[CẦN PI KHAI — tình trạng sức khỏe nghiên cứu: gate_params.G2.health_condition]"),
        13: d13,
        14: f"Inclusion: {nhan}\n            Exclusion: {loai}",
        15: (f"{v15.get('design') or 'Other'} · {v15.get('primary_purpose') or 'Other'} · "
             f"{v15.get('allocation') or 'Non-randomized'} · {v15.get('masking') or MASKING_CAN_KHAI}"),
        19: d19,
        20: "; ".join(_real_text_list(values.get(20))) or "[CẦN — tên kết cục + thước đo + thời điểm từ SAP]",
    }


def registration_pi_confirmation_gaps(document: Mapping[str, Any], design_code: str) -> list[str]:
    """Mục WHO TRDS máy TỰ ĐIỀN mà PI chưa khai (G2-07): 9 Public title và 12 Health condition còn chép tên đề tài
    khoa học (mục 10); RCT chưa khai masking ở mục 15."""
    items = document.get("items")
    by_number = {
        item.get("number"): item.get("value")
        for item in (items if isinstance(items, list) else [])
        if isinstance(item, Mapping)
    }
    tieu_de_kh = _real_text(by_number.get(10))
    gaps: list[str] = []
    for so, nhan, khoa in ((9, "Public Title", "public_title"), (12, "Health Condition(s)", "health_condition")):
        gia_tri = _real_text(by_number.get(so))
        if not gia_tri or (tieu_de_kh and gia_tri.casefold() == tieu_de_kh.casefold()):
            gaps.append(f"#{so} {nhan} (đang chép tên đề tài — PI khai gate_params.G2.{khoa})")
    if design_code == "rct":
        v15 = by_number.get(15) if isinstance(by_number.get(15), Mapping) else {}
        if not _real_text(v15.get("masking")):
            gaps.append("#15 Study Type — masking chưa khai (gate_params.G1.blinding)")
    return gaps


def build_registration_draft(
    *,
    study: str,
    topic: str,
    design_code: str,
    design_primary: str,
    risk: Mapping[str, Any],
    n_target: Optional[int],
    out_dir: Path,
    generated_at: str,
    meta: Optional[Mapping[str, Any]] = None,
) -> Path:
    """Sinh WHO TRDS 1.3.1 từ dữ kiện PI đã pin; thiếu thì giữ trống."""
    values = who_trds_values(topic=topic, design_code=design_code, design_primary=design_primary,
                             n_target=n_target, meta=meta)
    document = {
        "schema_version": "who-trds-draft-v1",
        "who_trds_version": WHO_TRDS_VERSION,
        "item_count": WHO_TRDS_ITEM_COUNT,
        "study": study,
        "generated_at": generated_at,
        "status": "DRAFT",
        "registration_requirement": risk.get("registration"),
        "suggested_registry": risk.get("register_where"),
        "items": [
            {
                "number": number,
                "label": WHO_TRDS_LABELS[number],
                "value": values[number],
            }
            for number in range(1, WHO_TRDS_ITEM_COUNT + 1)
        ],
        "scientific_fields_source": {
            "source": "study_meta.gate_params.G0/G1",
            "pi_pinned_only": True,
            "auto_filled_items": [13, 14, 19, 20],
        },
        "no_pii_note": (
            "Thông tin liên hệ cá nhân phải điền trực tiếp trên registry công khai; "
            "không lưu PII trong artifact pipeline."
        ),
        "disclaimer": "Cần bác sĩ kiểm chứng.",
    }
    path = Path(out_dir) / f"G2_REGISTRATION_DRAFT_{study}.json"
    path.write_text(
        json.dumps(document, ensure_ascii=False, indent=2),
        encoding="utf-8", newline="\n"
    )
    return path


def _registration_draft_errors(document: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if document.get("who_trds_version") != WHO_TRDS_VERSION:
        errors.append(f"WHO TRDS phải là phiên bản {WHO_TRDS_VERSION}")
    items = document.get("items")
    if not isinstance(items, list) or len(items) != WHO_TRDS_ITEM_COUNT:
        errors.append(f"WHO TRDS phải có đúng {WHO_TRDS_ITEM_COUNT} mục")
        return errors
    numbers = {item.get("number") for item in items if isinstance(item, Mapping)}
    if numbers != set(range(1, WHO_TRDS_ITEM_COUNT + 1)):
        errors.append("WHO TRDS thiếu hoặc trùng số mục 1-24")
    for item in items:
        if not isinstance(item, Mapping):
            errors.append("WHO TRDS có mục không phải object")
            continue
        number = item.get("number")
        if number in WHO_TRDS_LABELS and item.get("label") != WHO_TRDS_LABELS[number]:
            errors.append(f"Nhãn WHO TRDS mục {number} không đúng")
    # SỬA 2026-07-30 (audit toàn diện G0-G10, G2-F1 — HIGH): trước vá này,
    # hàm này CHỈ kiểm số lượng/nhãn/version — ba trường này do build_
    # registration_draft() sinh ra bằng CHÍNH các hằng số WHO_TRDS_LABELS/
    # WHO_TRDS_ITEM_COUNT/WHO_TRDS_VERSION mà hàm này cũng đọc, nên KHÔNG có
    # đầu vào thật nào (topic/design/dữ liệu bác sĩ) có thể khiến hai bên
    # lệch nhau — tiêu chí G2-AUTO-04 dùng hàm này về mặt toán học không bao
    # giờ có thể fail. Thêm kiểm tra PHỤ THUỘC DỮ LIỆU THẬT: mục 9 (Public
    # Title) và 10 (Scientific Title) phải có nội dung (đều lấy từ `topic`
    # của chính đề tài) — nếu topic rỗng/thiếu (vd G0 chưa từng chạy thật),
    # kiểm tra này MỚI có khả năng thật sự BLOCK.
    by_number = {
        item.get("number"): item
        for item in items
        if isinstance(item, Mapping)
    }
    for number in (9, 10):
        value = by_number.get(number, {}).get("value") if isinstance(by_number.get(number), Mapping) else None
        if not (isinstance(value, str) and value.strip()):
            errors.append(f"WHO TRDS mục {number} ({WHO_TRDS_LABELS[number]}) còn trống")
    # SỬA 2026-07-31 (audit tautology vòng 2, G2-AUTO-04 — reverse-tautology
    # thật): bản vá G2-F1 (trên) chỉ kiểm "không rỗng" — nhưng đường sản
    # xuất thật (tools/run_g2_auto.py::main(), `topic = args.topic or study`)
    # khi thiếu --topic VÀ không có G0 checkpoint sẽ tự fallback về CHÍNH mã
    # đề tài đã làm sạch (vd "NOTOPIC-2026") — một chuỗi máy sinh, không phải
    # tiêu đề khoa học thật — mà vẫn thỏa "không rỗng" nên PASS giả. Xác nhận
    # thực nghiệm: build_registration_draft(study="NOTOPIC-2026",
    # topic="NOTOPIC-2026", ...) (mô phỏng đúng fallback thật) → mục 9/10
    # đều ="NOTOPIC-2026", _registration_draft_errors() trả [] (0 lỗi). Thêm
    # kiểm: mục 9/10 KHÔNG được trùng với document["study"] (mã đề tài). AN
    # TOÀN để BLOCK (khác G2-AUTO-08/09 — không xếp vào _NON_BLOCKING_CRITERIA)
    # vì `topic` LÀ tham số CLI thật (--topic) và/hoặc có đường G0 checkpoint
    # thật trong main() — bác sĩ có cách hợp lệ để giải quyết chỉ bằng chạy
    # lại với --topic hoặc chạy G0 trước, không phải một trường không bao giờ
    # được điền qua pipeline thật.
    study_code = document.get("study")
    if isinstance(study_code, str) and study_code.strip():
        for number in (9, 10):
            value = by_number.get(number, {}).get("value") if isinstance(by_number.get(number), Mapping) else None
            if isinstance(value, str) and value.strip() == study_code.strip():
                errors.append(
                    f"WHO TRDS mục {number} ({WHO_TRDS_LABELS[number]}) trùng với mã đề tài "
                    f"'{study_code}' — có vẻ chỉ là fallback, chưa phải tiêu đề khoa học thật "
                    "(chạy lại với --topic thật hoặc chạy G0 trước)"
                )
    return errors


def _who_trds_value_empty(value: Any) -> bool:
    if isinstance(value, Mapping):
        return all(_who_trds_value_empty(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return all(_who_trds_value_empty(item) for item in value)
    return not bool(_real_text(value))


def scientific_registration_item_gaps(
    document: Mapping[str, Any],
    design_code: str,
) -> list[str]:
    """Liệt kê mục WHO TRDS khoa học chưa đủ, dùng chung cho G2 và verifier."""
    items = document.get("items")
    rows = items if isinstance(items, list) else []
    by_number = {
        item.get("number"): item
        for item in rows
        if isinstance(item, Mapping)
    }

    def _item_empty(number: int, value: Any) -> bool:
        if number == 13 and design_code == "rct":
            return not (
                isinstance(value, Mapping)
                and _real_text(value.get("intervention"))
                and _real_text(value.get("comparator"))
            )
        if number == 14:
            return not (
                isinstance(value, Mapping)
                and not _who_trds_value_empty(value.get("inclusion"))
                and not _who_trds_value_empty(value.get("exclusion"))
            )
        if number == 19:
            return not (
                isinstance(value, Mapping)
                and _real_text(value.get("name"))
                and _real_text(value.get("measure"))
                and _real_text(value.get("timepoint"))
            )
        return _who_trds_value_empty(value)

    return [
        f"#{number} {name}"
        for number, name in (
            (13, "Intervention(s)"),
            (14, "Key Inclusion and Exclusion Criteria"),
            (19, "Primary Outcome(s)"),
            (20, "Key Secondary Outcomes"),
        )
        if _item_empty(number, by_number.get(number, {}).get("value"))
    ]


# Ô MẪU CHUNG sót từ khuôn sinh `run_g2_auto.py` — KHÔNG mang nhãn [CẦN] nên trước 03/10/2026 G2-AUTO-05 không đếm:
# hồ sơ C1a đã điền hết mục đích thật mà ICF tiếng Việt vẫn còn câu ví dụ thử nghiệm thuốc («thuốc/can thiệp X»,
# «[bệnh]») cùng «[đơn vị]», «[tài trợ nếu có]», «[nơi thực hiện]», và ICF tiếng Anh còn 14 ô «[TO BE COMPLETED]».
# Khi mọi [CẦN] được điền, cổng sẽ báo READY_FOR_IRB_SUBMISSION cho một phiếu đồng thuận người bệnh ký còn chữ mẫu.
# «[tài trợ» không đòi dấu đóng: khuôn sinh ngắt dòng giữa ô («[tài trợ\n nếu có]»).
_O_MAU_CHUNG_RE = re.compile(
    r"\[TO BE COMPLETED|\[(?:đơn vị|bệnh|nơi thực hiện)\]|\[tài trợ|thuốc/can thiệp X",
    re.IGNORECASE,
)

# ── Bộ dò ô còn trống của G2 trên hợp đồng chung tools/placeholder_contract.py (03/10/2026) ─────────────────────────
# Lượt kiểm 03/10/2026 (chạy thật trên hồ sơ sinh từ khuôn + hồ sơ C1a) thấy READY_FOR_IRB_SUBMISSION vẫn đạt khi còn:
# «[TÊN ĐƠN VỊ — CẦN BỔ SUNG]» (CẦN không đứng ngay sau «[»), «Thời gian lưu: ___ năm», «trong ___ tháng»,
# «SỐ BẢN NỘP: ___», «[sẽ/sẽ không]», «XÓA mục này», lời dặn soạn thảo ICF 6c, ô PROSPERO «[topic in English]…»,
# thẻ biên tập «[BÁC SĨ ĐIỀN …]»/«[BÁC SĨ RÀ]»; và luật PII bỏ qua NGUYÊN DÒNG che luôn ô không-PII cùng dòng.
# Nguyên tắc: KHÔNG BAO GIỜ yếu hơn bộ dò cũ — «[CẦN» (so trên line.upper()) và _O_MAU_CHUNG_RE vẫn chạy y nguyên trên
# MỌI dòng; các họ mới chỉ CỘNG thêm.
_CAN_CU_RE = re.compile(re.escape("[CẦN"), re.IGNORECASE)
# Họ của hợp đồng chung bật cho tài liệu G2: nhãn + ô mẫu chung (mặc định quét tài liệu), cộng họ TRONG («___», «……»)
# SAU KHI che chỗ ký/ngày điền tay. KHÔNG bật NHAP: «[BẢN NHÁP TỰ ĐỘNG — DRAFT …]» là nhãn BẮT BUỘC của khuôn sinh
# (guardrail R4 đòi ≥ 5 «DRAFT»); KHÔNG bật THU_CONG (nhãn của G10).
_HO_TAI_LIEU_G2 = (PC.NHAN, PC.MAU_CHUNG)
# Chuỗi riêng của khuôn sinh run_g2_auto.py mà hợp đồng chung không có (chuỗi con, không phân biệt hoa thường):
# ô phụ lục PROSPERO (sr_ma) và lời dặn người soạn in thẳng vào mục 6c của ICF mọi thiết kế.
_THEM_G2 = (
    "[topic in English]",
    "[RCT / Observational",
    "[RoB 2 / ROBINS-I",
    "[sẽ bổ sung sau]",
    "mục này có thể rút gọn",
    "không được bỏ hẳn",
)
# Nhãn CẦN KHÔNG đứng ngay sau «[»: «[TÊN ĐƠN VỊ — CẦN BỔ SUNG]» (mặc định khi thiếu irb_name), «[Phiên bản phê duyệt
# sẽ có số IRB, CẦN BỔ SUNG]» (clean_generated_prose đã đổi «—» thành «,»). «CẦN» phải VIẾT HOA cả từ, hoặc «cần» đứng
# ngay sau dấu ngăn — câu chữ thường hợp lệ như «[Mỗi đồng tác giả cần khai báo COI…]» KHÔNG khớp. Bỏ qua ngoặc mở đầu
# bằng «CẦN» (đã có dấu hiệu cũ/họ NHAN) để không đếm hai lần.
_CAN_GIUA_NGOAC_RE = re.compile(
    r"\[(?!\s*(?i:cần))[^\[\]\n]*?(?:\bCẦN\b|(?i:[—–,;:]\s*cần\b))[^\[\]\n]*(?:\]|$)"
)
# Ô trống HỢP LỆ điền tay khi ký/nộp (không phải nội dung khoa học): ngày «___/___/2026», «___/___/____»; chỗ ký/họ
# tên ngay sau nhãn ký; dòng gạch dưới mở đầu bằng «Ký, ghi rõ họ tên». Chúng được CHE trước khi dò họ TRONG.
_NGAY_TRONG_RE = re.compile(r"_{2,}\s*/\s*_{2,}\s*/\s*(?:\d{2,4}|_{2,})")
_NHAN_KY_RE = re.compile(
    r"\b(?:họ(?: và)? tên|ký tên|chữ ký|participant|witness|investigator|signature)\b[^:\n]{0,40}:\s*(_{3,})",
    re.IGNORECASE,
)
_DONG_KY_RE = re.compile(r"^\s*(_{3,})(?=\s*(?:ký|chữ ký|signature)\b)", re.IGNORECASE)
# Khối HƯỚNG DẪN tĩnh cuối hồ sơ (không thuộc tài liệu nộp): «[CHỜ BÁC SĨ]» ở đó là danh sách sự kiện sau khi nộp —
# chỉ dấu hiệu CŨ được dò trong khối này (như trước), họ mới thì không.
_TIEU_DE_RE = re.compile(r"^\s{0,3}#{1,6}\s")
_KHOI_HUONG_DAN_RE = re.compile(
    r"^\s{0,3}#{1,6}\s*(?:CƠ CHẾ MỞ KH(?:ÓA|OÁ) G2|YÊU CẦU ÁP DỤNG KHI QUA CỔNG G2)", re.IGNORECASE
)
# Ô CHỈ ĐIỀN ĐƯỢC SAU khi nộp/phê duyệt/đăng ký: không thể có trước khi nộp IRB ⇒ chỉ là THÔNG TIN ở mốc
# READY_FOR_IRB_SUBMISSION, nhưng vẫn BẮT BUỘC ở mốc PASS_G2_APPROVED (approve_gate từ chối ký khi còn — đường
# attestation). Danh sách hẹp theo đúng câu chữ khuôn sinh (WHO TRDS mục 1/2/3/16/21/22/23, số IRB trên ICF, liên kết
# protocol PROSPERO) — so trên NỘI DUNG Ô, không trên cả dòng, để ô trước-nộp cùng dòng không bị nới nhầm.
_SAU_PHE_DUYET = (
    # (biểu thức trên NHÃN đứng trước ô — None nếu không cần, biểu thức trên chính Ô)
    (re.compile(r"phê duyệt|IRB", re.IGNORECASE), re.compile(r"\bsau khi nhận\b", re.IGNORECASE)),
    (
        None,
        re.compile(
            r"sau quyết định IRB|sẽ có sau khi đăng ký|ngày đăng ký thành công|chỉ tuyển sau phê duyệt"
            r"|ngày hoàn tất dự kiến|sẽ có số IRB|^\[\s*sẽ bổ sung sau\s*\]$",
            re.IGNORECASE,
        ),
    ),
)
# VÁ 04/10/2026 (soát từng cổng, G2-13): ô CHỈ ĐIỀN ĐƯỢC SAU KHI KẾT THÚC NGHIÊN CỨU (WHO TRDS mục 23 — kết quả tóm
# tắt, ngày công bố, URL protocol) từng nằm trong nhóm «sau phê duyệt» ⇒ approve_gate từ chối KÝ G2 cho tới khi có kết
# quả nghiên cứu — dữ kiện không thể có ở G2. Nhóm riêng: không chặn nộp, không chặn ký; chỉ hiện trong báo cáo.
_SAU_NGHIEN_CUU_RE = re.compile(r"cập nhật sau nghiên cứu|chỉ điền sau khi kết thúc nghiên cứu", re.IGNORECASE)
# Dòng chân bản nháp WHO TRDS «DRAFT — Điền trường còn [CẦN] trước khi gửi đăng ký.» là CHỈ DẪN (chuỗi «[CẦN]» theo
# nghĩa đen), xếp cùng nhóm sau phê duyệt: không chặn nộp IRB, vẫn phải sửa trước khi khoá G2.
_CHAN_TRANG_DANG_KY_RE = re.compile(r"Điền trường còn \[CẦN\] trước khi gửi đăng ký", re.IGNORECASE)


def _che_o_ky_hop_le(dong: str) -> str:
    """Thay chỗ ký/ngày điền tay bằng khoảng trắng CÙNG ĐỘ DÀI (giữ nguyên vị trí các khớp khác)."""
    ky_tu = list(dong)

    def _che(dau: int, cuoi: int) -> None:
        for i in range(dau, cuoi):
            ky_tu[i] = " "

    for m in _NGAY_TRONG_RE.finditer(dong):
        _che(m.start(), m.end())
    for m in _NHAN_KY_RE.finditer(dong):
        _che(m.start(1), m.end(1))
    m = _DONG_KY_RE.match(dong)
    if m:
        _che(m.start(1), m.end(1))
    return "".join(ky_tu)


def _khop_tren_dong(tho: str, dong: str, *, quet_ho_moi: bool) -> list[tuple[int, int, bool]]:
    """Mọi khớp ô trống trên MỘT dòng: (đầu, cuối, là_dấu_hiệu_cũ). `tho` = dòng gốc, `dong` = dòng đã NFC."""
    khop: list[tuple[int, int, bool]] = []
    khop.extend((m.start(), m.end(), True) for m in _CAN_CU_RE.finditer(dong))
    khop.extend((m.start(), m.end(), True) for m in _O_MAU_CHUNG_RE.finditer(dong))
    # Lưới an toàn: bộ dò cũ (so trên dòng GỐC) thấy mà vị trí trên dòng NFC không bắt được ⇒ cả dòng là một ô cũ.
    if not khop and ("[CẦN" in tho.upper() or _O_MAU_CHUNG_RE.search(tho)):
        khop.append((0, len(dong), True))
    if not quet_ho_moi:
        return khop
    for ho in _HO_TAI_LIEU_G2:
        for bieu_thuc in PC.mau(ho):
            khop.extend((m.start(), m.end(), False) for m in bieu_thuc.finditer(dong))
    khop.extend((m.start(), m.end(), False) for m in _CAN_GIUA_NGOAC_RE.finditer(dong))
    for chuoi in _THEM_G2:
        khop.extend((m.start(), m.end(), False) for m in re.finditer(re.escape(chuoi), dong, re.IGNORECASE))
    da_che = _che_o_ky_hop_le(dong)
    for bieu_thuc in PC.mau(PC.TRONG):
        khop.extend((m.start(), m.end(), False) for m in bieu_thuc.finditer(da_che))
    return khop


def _o_bao_quanh(dong: str, dau: int, cuoi: int) -> tuple[int, int]:
    """Khoảng của Ô chứa khớp: cả cặp ngoặc vuông bao quanh (tới cuối dòng nếu ngoặc chưa đóng), hoặc chính khớp."""
    mo = dong.rfind("[", 0, dau + 1)
    if mo >= 0 and "]" not in dong[mo:dau]:
        dong_ngoac = dong.find("]", max(dau, mo + 1))
        return mo, (dong_ngoac + 1 if dong_ngoac >= 0 else len(dong))
    return dau, cuoi


def _la_o_pii(nhan: str, o: str) -> bool:
    """Ô dành cho PII (điền ở bản nộp ngoài hệ thống): nhãn ngay trước ô hoặc chính ô mang từ gợi PII, hoặc ô
    ghi «PII»."""
    nhan_hoa, o_hoa = nhan.upper(), o.upper()
    return any(goi_y in nhan_hoa or goi_y in o_hoa for goi_y in _PII_ONLY_HINTS) or bool(
        re.search(r"\bPII\b", o, re.IGNORECASE)
    )


def _la_o_sau_phe_duyet(dong: str, nhan: str, o: str) -> bool:
    if _CHAN_TRANG_DANG_KY_RE.search(dong) and o.strip().upper() == "[CẦN]":
        return True
    return any(
        bt_o.search(o) and (bt_nhan is None or bt_nhan.search(nhan))
        for bt_nhan, bt_o in _SAU_PHE_DUYET
    )


def _o_trong_cua_dong(tho: str, dong: str, *, quet_ho_moi: bool) -> list[tuple[str, str]]:
    """Các Ô CÒN TRỐNG không được miễn trên một dòng: [(nhãn đứng trước, nội dung ô), …].

    Miễn ô PII (thu hẹp 03/10/2026): trước đây một từ gợi PII ở BẤT KỲ đâu trên dòng làm bỏ qua NGUYÊN DÒNG, che luôn
    ô không-PII cùng dòng («Nghiên cứu do [CẦN — họ tên chủ nhiệm], [CẦN — chức danh…]»). Nay chỉ ô có nhãn/nội dung
    PII mới được miễn. Ô mang dấu hiệu CŨ chỉ được miễn khi dòng có từ gợi PII (đúng điều kiện cũ) ⇒ không bao giờ yếu
    hơn bộ dò cũ; ô chỉ có dấu hiệu MỚI được miễn khi là ô PII (vd «[ĐIỀN TRỰC TIẾP TRÊN REGISTRY — không lưu PII…]»).
    """
    khop = _khop_tren_dong(tho, dong, quet_ho_moi=quet_ho_moi)
    if not khop:
        return []
    o_co_cu: dict[tuple[int, int], bool] = {}
    for dau, cuoi, cu in khop:
        khoang = _o_bao_quanh(dong, dau, cuoi)
        o_co_cu[khoang] = o_co_cu.get(khoang, False) or cu
    gop: list[list[Any]] = []
    for dau, cuoi in sorted(o_co_cu):
        if gop and dau < gop[-1][1]:
            gop[-1][1] = max(gop[-1][1], cuoi)
            gop[-1][2] = gop[-1][2] or o_co_cu[(dau, cuoi)]
        else:
            gop.append([dau, cuoi, o_co_cu[(dau, cuoi)]])
    dong_co_goi_y_pii = any(goi_y in tho.upper() for goi_y in _PII_ONLY_HINTS)
    con: list[tuple[str, str]] = []
    truoc = 0
    for dau, cuoi, cu in gop:
        nhan = re.split(r"[|;]", dong[truoc:dau])[-1]
        o = dong[dau:cuoi]
        mien = _la_o_pii(nhan, o) and (dong_co_goi_y_pii or not cu)
        if not mien:
            con.append((nhan, o))
        truoc = cuoi
    return con


def _dong_con_o_trong(package_text: str) -> list[tuple[str, str]]:
    """Mọi DÒNG còn ô trống không được miễn (sau strip_attestation), theo thứ tự, không lặp:
    [(dòng rút gọn ≤ 240 ký tự, mốc), …] — mốc ∈ {"truoc_nop", "sau_phe_duyet", "sau_nghien_cuu"} (mốc của ô
    MUỘN NHẤT còn lại mà mọi ô trên dòng đều thuộc; một ô trước-nộp kéo cả dòng về "truoc_nop")."""
    base = strip_attestation(package_text)
    ra: list[tuple[str, bool]] = []
    da_co: set[str] = set()
    trong_khoi_huong_dan = False
    for tho in base.splitlines():
        dong = unicodedata.normalize("NFC", tho)
        if _TIEU_DE_RE.match(dong):
            trong_khoi_huong_dan = bool(_KHOI_HUONG_DAN_RE.match(dong))
        con = _o_trong_cua_dong(tho, dong, quet_ho_moi=not trong_khoi_huong_dan)
        if not con:
            continue
        compact = re.sub(r"\s+", " ", tho.strip())[:240]
        if not compact or compact in da_co:
            continue
        da_co.add(compact)
        if all(_SAU_NGHIEN_CUU_RE.search(o) for _nhan, o in con):
            moc = "sau_nghien_cuu"
        elif all(_la_o_sau_phe_duyet(dong, nhan, o) or _SAU_NGHIEN_CUU_RE.search(o) for nhan, o in con):
            moc = "sau_phe_duyet"
        else:
            moc = "truoc_nop"
        ra.append((compact, moc))
    return ra


def classify_placeholders(package_text: str) -> dict[str, list[str]]:
    """Phân loại DÒNG còn ô trống của hồ sơ G2 theo mốc:

    - ``pre_submission``: phải điền TRƯỚC khi nộp IRB — lái G2-AUTO-05 ở mốc READY_FOR_IRB_SUBMISSION;
    - ``post_approval``: dòng mà mọi ô còn lại đều chỉ điền được SAU nộp/phê duyệt/đăng ký (số IRB, ngày phê duyệt,
      mã/ngày đăng ký, ngày tuyển đầu tiên, ngày hoàn tất, kết quả tóm tắt, số IRB trên ICF) — thông tin ở mốc READY,
      BẮT BUỘC ở mốc PASS_G2_APPROVED (G2-AUTO-05 khi đã có attestation; approve_gate từ chối ký khi còn);
    - ``post_study``: chỉ điền được sau khi KẾT THÚC nghiên cứu (WHO TRDS mục 23) — không chặn nộp, không chặn ký.
    Bỏ ô chỉ chứa PII và chỗ ký/ngày điền tay."""
    dong = _dong_con_o_trong(package_text)
    return {
        "pre_submission": [noi_dung for noi_dung, moc in dong if moc == "truoc_nop"],
        "post_approval": [noi_dung for noi_dung, moc in dong if moc == "sau_phe_duyet"],
        "post_study": [noi_dung for noi_dung, moc in dong if moc == "sau_nghien_cuu"],
    }


def unresolved_critical_placeholders(package_text: str) -> list[str]:
    """Liệt kê MỌI dòng còn placeholder khoa học/vận hành (nhãn [CẦN…], ô mẫu chung của khuôn sinh, ô trống «___»
    gắn giá trị, thẻ biên tập [BÁC SĨ …]) — gồm cả ô chỉ điền được sau phê duyệt — bỏ qua ô chỉ chứa PII và chỗ ký/ngày.

    approve_gate.py dùng danh sách này để từ chối ghi attestation/ledger ⇒ ô sau phê duyệt vẫn bắt buộc ở
    PASS_G2_APPROVED. Mốc READY_FOR_IRB_SUBMISSION chỉ xét phần ``pre_submission`` của classify_placeholders().
    KHÔNG gồm ô chỉ điền được sau khi kết thúc nghiên cứu (G2-13)."""
    return [noi_dung for noi_dung, moc in _dong_con_o_trong(package_text) if moc != "sau_nghien_cuu"]


def placeholder_total(text: str) -> int:
    """Tổng số khớp ô trống THÔ (không miễn trừ) theo hợp đồng chung NHAN + MAU_CHUNG + TRONG cộng luật riêng G2.

    Dùng cho rào chống đè hồ sơ đã biên tập của run_g2_auto.py: bác sĩ điền «___ năm» hay «[TÊN ĐƠN VỊ — CẦN BỔ SUNG]»
    không đổi số «[CẦN» nhưng làm tổng này giảm."""
    van_ban = unicodedata.normalize("NFC", str(text or ""))
    tong = len(PC.tim(van_ban, (PC.NHAN, PC.MAU_CHUNG, PC.TRONG), them=_THEM_G2))
    return tong + sum(len(_CAN_GIUA_NGOAC_RE.findall(dong)) for dong in van_ban.splitlines())


def validate_attestation(
    *,
    attestation: Mapping[str, Any],
    package_text: str,
    study: str,
    design_code: str,
    meta: Mapping[str, Any],
    today: Optional[date] = None,
    out_dir: Optional[Path] = None,
) -> list[str]:
    """Kiểm metadata phê duyệt; không thay kiểm chữ ký trong approval ledger.

    out_dir (thư mục đề tài) bật phép so DẤU ĐẦU VÀO (G2-08): thiết kế + quyết định G1 + cỡ mẫu G3 lúc ký phải trùng
    hiện tại. Mọi nơi gọi trong chuỗi (G2-HUMAN-01, gate_contract._g2_signed_attestation_state) đều truyền out_dir."""
    errors: list[str] = []
    today = today or date.today()
    if attestation.get("schema_version") != ATTESTATION_SCHEMA:
        errors.append("Sai/thiếu schema attestation G2")
    if attestation.get("study") != study:
        errors.append("Attestation không khớp mã đề tài")
    if attestation.get("ethics_decision") not in {"APPROVED", "EXEMPT", "WAIVER"}:
        errors.append("Thiếu quyết định đạo đức APPROVED/EXEMPT/WAIVER")
    for field, label in (
        ("ethics_committee_ref", "mã Hội đồng Đạo đức"),
        ("approval_number", "số quyết định/phê duyệt"),
        ("approved_protocol_version", "phiên bản protocol được duyệt"),
    ):
        if not str(attestation.get(field) or "").strip():
            errors.append(f"Thiếu {label}")

    approval_date = _parse_iso_date(attestation.get("approval_date"))
    if approval_date is None:
        errors.append("Ngày phê duyệt phải theo YYYY-MM-DD")
    elif approval_date > today:
        errors.append("Ngày phê duyệt không được ở tương lai")

    valid_until = _parse_iso_date(attestation.get("valid_until"))
    no_expiry = attestation.get("no_expiry_confirmed") is True
    if not valid_until and not no_expiry:
        errors.append("Phải có ngày hết hiệu lực/rà tiếp hoặc xác nhận quyết định không ghi hạn")
    if valid_until and valid_until < today:
        errors.append("Phê duyệt G2 đã hết hiệu lực")

    g2 = _g2_meta(meta)
    protocol_version = str(g2.get("protocol_version") or "").strip()
    approved_protocol = str(attestation.get("approved_protocol_version") or "").strip()
    if protocol_version and approved_protocol != protocol_version:
        errors.append("Phiên bản protocol hiện hành không khớp phiên bản IRB đã duyệt")

    waiver = attestation.get("icf_waiver_approved") is True
    approved_icf = str(attestation.get("approved_icf_version") or "").strip()
    if not waiver and not approved_icf:
        errors.append("Thiếu phiên bản ICF được duyệt hoặc quyết định miễn ICF")
    current_icf = str(g2.get("icf_version") or "").strip()
    if current_icf and not waiver and approved_icf != current_icf:
        errors.append("Phiên bản ICF hiện hành không khớp phiên bản IRB đã duyệt")

    mode = str(attestation.get("recruitment_mode") or "").strip()
    if mode not in _RECRUITMENT_MODES:
        errors.append("Thiếu/sai recruitment_mode")
    if design_code == "rct" and mode != "PROSPECTIVE_NEW_PARTICIPANTS":
        errors.append("RCT phải dùng recruitment_mode tiến cứu tuyển người tham gia")

    registration = attestation.get("registration")
    if not isinstance(registration, Mapping):
        errors.append("Thiếu metadata đăng ký nghiên cứu")
    else:
        required = (
            mode == "PROSPECTIVE_NEW_PARTICIPANTS"
            or design_code == "sr_ma"
        )
        if bool(registration.get("required")) != required:
            errors.append("Cờ registration.required không khớp recruitment_mode")
        status = str(registration.get("status") or "").strip()
        if required and status != "REGISTERED":
            errors.append(
                "Thiết kế này chưa có trạng thái REGISTERED ở registry phù hợp"
            )
        if required:
            for field, label in (
                ("registry", "tên registry"),
                ("registration_id", "mã đăng ký"),
                ("registration_date", "ngày đăng ký"),
            ):
                if not str(registration.get(field) or "").strip():
                    errors.append(f"Thiếu {label}")
            registration_date = _parse_iso_date(registration.get("registration_date"))
            enrolment_date = _parse_iso_date(attestation.get("first_enrolment_date"))
            first_search_date = _parse_iso_date(attestation.get("first_search_date"))
            if registration_date is None:
                errors.append("Ngày đăng ký phải theo YYYY-MM-DD")
            elif registration_date > today:
                errors.append("Ngày đăng ký không được ở tương lai")
            if enrolment_date and registration_date and registration_date > enrolment_date:
                errors.append("Đăng ký muộn hơn ngày tuyển người tham gia đầu tiên")
            if design_code == "sr_ma" and first_search_date is None:
                errors.append("SR/MA thiếu ngày bắt đầu tìm kiếm")
            if (
                design_code == "sr_ma"
                and first_search_date
                and registration_date
                and registration_date > first_search_date
            ):
                errors.append("Đăng ký protocol muộn hơn ngày bắt đầu tìm kiếm")
        elif status != "NOT_REQUIRED":
            errors.append("Nghiên cứu không tuyển mới phải ghi registration.status=NOT_REQUIRED")

    base_hash = _sha256_text(strip_attestation(package_text))
    if attestation.get("package_sha256_before_attestation") != base_hash:
        errors.append("Hash hồ sơ nền không khớp attestation")
    if out_dir is not None:
        dau_ky = str(attestation.get("dau_dau_vao") or "").strip().lower()
        dau_nay, _ = dau_dau_vao_g2(out_dir, meta)
        if not dau_ky:
            errors.append("Attestation kiểu cũ chưa gắn dấu đầu vào (thiết kế/đề cương/cỡ mẫu Hội đồng đã duyệt) — "
                          f"ký lại G2 bằng approve_gate.py (dấu hiện tại {dau_nay})")
        elif dau_ky != dau_nay:
            errors.append(f"Đề cương/cỡ mẫu đã đổi SAU khi Hội đồng duyệt (dấu lúc ký {dau_ky} ≠ hiện tại {dau_nay}) — "
                          "cần sửa đổi đề cương (amendment) được Hội đồng duyệt rồi ký lại G2")
    return errors


def evaluate_g2_quality(
    *,
    study: str,
    design_code: str,
    package_path: Path,
    registration_path: Path,
    g1_checkpoint: Mapping[str, Any],
    meta: Mapping[str, Any],
    guardrail_passed: bool,
    ledger_approved: bool,
    design_ambiguous: bool = False,
    today: Optional[date] = None,
    g1_song: Optional[Mapping[str, Any]] = None,
    g1_design_code: Optional[str] = None,
) -> dict[str, Any]:
    """Đánh giá G2 theo lớp tự động và lớp quyết định người thật.

    g1_song: kết quả cong_song.trang_thai_song("G1") — G1 CHẤM SỐNG (evaluate_study truyền vào); vắng thì dùng trạng
    thái G1 lưu trong checkpoint (đường tương thích cho nơi gọi cũ). g1_design_code: thiết kế G1 hiện hành để đối chiếu
    với thiết kế mà hồ sơ G2 được sinh (G2-AUTO-06b)."""
    package_path = Path(package_path)
    registration_path = Path(registration_path)
    package_text = (
        package_path.read_text(encoding="utf-8")
        if package_path.exists()
        else ""
    )
    registration = _read_json(registration_path)
    automatic: list[dict[str, str]] = []
    approval: list[dict[str, str]] = []
    attestation = extract_attestation(package_text)

    # VÁ 04/10/2026 (soát từng cổng, G2-02): chấm liêm chính trên NỘI DUNG HIỆN HÀNH — guardrail lưu trong checkpoint
    # là kết quả của BẢN KHUÔN lúc sinh, có thể cũ hai tháng. guardrail_passed (bản lưu) chỉ còn là thông tin.
    loi_liem_chinh = kiem_liem_chinh_noi_dung(package_text, attestation) if package_text else ["chưa có hồ sơ G2"]
    automatic.append(_criterion(
        "G2-AUTO-01",
        "Liêm chính nội dung hồ sơ HIỆN HÀNH (PII, số phê duyệt tự gán, tự xưng phê duyệt/khoá, disclaimer)",
        "BLOCK" if loi_liem_chinh else "PASS",
        ("; ".join(loi_liem_chinh) if loi_liem_chinh else "R1/R2/R3/R7 sạch trên nội dung hiện hành")
        + f" (guardrail lúc sinh: passed={guardrail_passed})",
        "Sửa PII, số phê duyệt tự gán, tuyên bố vượt cổng hoặc disclaimer trong hồ sơ trước khi nộp.",
    ))

    g1_status = (
        (g1_checkpoint.get("quality_gate") or {}).get("status")
        if isinstance(g1_checkpoint.get("quality_gate"), Mapping)
        else None
    )
    # VÁ 04/10/2026 (soát từng cổng, G1-10 phía tiêu thụ): G1 được CHẤM SỐNG — bản lưu PASS mà chấm lại chưa đạt (sửa
    # đề cương sau khi xác nhận) không còn mở cửa G2; G1 sống BLOCKED ⇒ hồ sơ G2 dựng trên thiết kế đang bị chặn.
    if isinstance(g1_song, Mapping) and g1_song.get("nguon") in (CS.NGUON_SONG, CS.NGUON_LOI):
        muc_g1 = g1_song.get("muc")
        luu_g1 = g1_song.get("trang_thai_luu")
        luu_khac = f"; bản LƯU={luu_g1}" if luu_g1 and luu_g1 != g1_song.get("status") else ""
        if muc_g1 == "PASS":
            g1_trang, g1_bang = "PASS", f"G1 chấm sống={g1_song.get('status')}"
        elif muc_g1 == "BLOCKED":
            g1_trang = "BLOCK"
            g1_bang = f"G1 chấm sống=BLOCKED{luu_khac} — hồ sơ G2 đang dựng trên thiết kế/đề cương bị chặn"
        elif muc_g1 == CS.KHONG_DO_DUOC:
            g1_trang = "REVIEW"
            g1_bang = f"G1 KHÔNG ĐO ĐƯỢC ({g1_song.get('ly_do')}) — không phải «đạt»{luu_khac}"
        else:
            g1_trang, g1_bang = "REVIEW", f"G1 chấm sống={g1_song.get('status')}{luu_khac}"
        g1_da_chot = muc_g1 == "PASS"
    else:
        g1_trang = "PASS" if g1_status == "PASS_G1_CONFIRMED" else "REVIEW"
        g1_bang = f"G1 quality status={g1_status or 'thiếu'} (bản lưu — nơi gọi chưa chấm sống)"
        g1_da_chot = g1_status == "PASS_G1_CONFIRMED"
    automatic.append(_criterion(
        "G2-AUTO-02",
        "G1 đã được PI/methodologist xác nhận (chấm sống)",
        g1_trang,
        g1_bang,
        "Hoàn tất xác nhận phương pháp G1; có thể soạn G2 song song nhưng chưa khóa.",
    ))

    annex2 = A2X.evaluate(meta, design_code, "G2")
    annex2_issues = annex2["errors"] + annex2["missing"]
    automatic.append(_criterion(
        "G2-AUTO-02b",
        f"{A2X.VERSION}: IRB/consent/privacy/data governance đủ cho phương pháp mới",
        # VÁ 04/10/2026 (G1-11 / QĐ-15): RCT chưa khai annex2.applicable ⇒ REVIEW (không suy «không áp dụng»).
        {"BLOCK": "BLOCK", "NEEDS_DECLARATION": "REVIEW"}.get(annex2["status"], "PASS"),
        (
            "; ".join(annex2_issues)
            if annex2_issues
            else ("RCT chưa khai gate_params.G1.annex2.applicable (true/false)"
                  if annex2["status"] == "NEEDS_DECLARATION"
                  else f"status={annex2['status']}; methods={','.join(annex2['methods']) or 'không áp dụng'}")
        ),
        "Hoàn thiện khối annex2 trong study_meta trước khi nộp/khóa G2.",
    ))

    # LƯU Ý PHẠM VI (audit toàn diện G0-G10, 2026-07-30, G2-F1): generate_g2_
    # full_package() in TẤT CẢ marker dưới đây VÔ ĐIỀU KIỆN (không phụ thuộc
    # design_code/dữ liệu bác sĩ), nên tiêu chí này KHÔNG BAO GIỜ tự phát
    # hiện được nội dung THIẾU CHẤT LƯỢNG hay SAI cho đề tài cụ thể — nó chỉ
    # có ý nghĩa THẬT trong một kịch bản: hồ sơ bị XÓA/CẮT một phần sau khi
    # sinh (hand-edit làm mất một mục). PASS ở đây = "cấu trúc còn nguyên",
    # KHÔNG phải "nội dung khoa học đã đủ/đúng cho đề tài này" — xem G2-AUTO-
    # 05 (unresolved_critical_placeholders) và G2-F4 cho khoảng trống nội
    # dung mà tiêu chí NÀY không phủ.
    missing_markers = [
        marker for marker in _PACKAGE_MARKERS
        if marker.casefold() not in package_text.casefold()
    ]
    # VÁ 04/10/2026 (G2-04/G2-10): ICF tiếng Việt phải có đủ nhãn mục bắt buộc THEO THIẾT KẾ, khớp ở đầu dòng.
    icf_thieu, icf_lech = kiem_icf(package_text, design_code)
    automatic.append(_criterion(
        "G2-AUTO-03",
        "Bộ hồ sơ IRB/ICF/DMP có đủ cấu trúc bắt buộc (ICF đủ mục theo thiết kế)",
        "BLOCK" if missing_markers or icf_thieu or not package_text else "PASS",
        "; ".join(
            ([f"thiếu: {', '.join(missing_markers)}"] if missing_markers else [])
            + ([f"ICF tiếng Việt thiếu mục {', '.join(icf_thieu)}"] if icf_thieu else [])
        ) or "đủ marker tài liệu 1-8, ICF, DMP, rủi ro/bồi thường/COI; ICF đủ mục theo thiết kế",
        "Sinh lại hoặc bổ sung phần hồ sơ bị thiếu (RCT: 2b phân nhóm ngẫu nhiên, 5b truy cập hồ sơ gốc, 6b, 6d, "
        "6f thông tin mới, 6g theo dõi khi ngừng/rút, 6h chấm dứt tham gia).",
    ))
    # VÁ 04/10/2026 (G2-11): ICF tiếng Anh từng là khung 7 mục rút gọn — thiếu 1b/4b/4c/6b–6e so với bản tiếng Việt.
    automatic.append(_criterion(
        "G2-AUTO-03b",
        "ICF tiếng Anh tương ứng ICF tiếng Việt (cùng tập mục)",
        "REVIEW" if icf_lech else "PASS",
        (f"lệch mục giữa hai bản: {', '.join(icf_lech)}" if icf_lech
         else "hai bản ICF có cùng tập mục (hoặc chưa có bản tiếng Anh/tiếng Việt để đối chiếu)"),
        "Bổ sung/xoá mục ở ICF tiếng Anh (Tài liệu 5) cho khớp ICF tiếng Việt (Tài liệu 4), hoặc sinh lại G2.",
    ))

    registration_errors = _registration_draft_errors(registration)
    automatic.append(_criterion(
        "G2-AUTO-04",
        f"WHO TRDS {WHO_TRDS_VERSION} đủ {WHO_TRDS_ITEM_COUNT} mục",
        "BLOCK" if registration_errors else "PASS",
        "; ".join(registration_errors) if registration_errors else "24/24 mục đúng số và nhãn",
        "Sinh lại bản đăng ký từ nguồn WHO TRDS hiện hành.",
    ))

    # Mốc của ô trống (03/10/2026): ô chỉ điền được SAU nộp/phê duyệt/đăng ký (số IRB, ngày phê duyệt, mã/ngày đăng ký,
    # ngày tuyển đầu tiên, ngày hoàn tất, kết quả tóm tắt…) KHÔNG THỂ có trước khi nộp — đếm chúng ở mốc READY làm
    # READY_FOR_IRB_SUBMISSION không bao giờ đạt (đo trên C1a). Trước khi có attestation: chỉ ô TRƯỚC NỘP lái
    # G2-AUTO-05,
    # ô sau phê duyệt là danh sách thông tin. Khi đã có attestation (mốc PASS_G2_APPROVED): MỌI ô đều bắt buộc — như cũ.
    phan_loai = classify_placeholders(package_text)
    truoc_nop = phan_loai["pre_submission"]
    sau_phe_duyet = phan_loai["post_approval"]
    sau_nghien_cuu = phan_loai["post_study"]
    unresolved = unresolved_critical_placeholders(package_text)
    lai_trang_thai = unresolved if attestation else truoc_nop
    automatic.append(_criterion(
        "G2-AUTO-05",
        "Không còn placeholder khoa học/vận hành trọng yếu",
        "REVIEW" if lai_trang_thai else "PASS",
        (
            f"còn {len(truoc_nop)} dòng [CẦN]/ô mẫu chung/ô trống phải điền TRƯỚC khi nộp IRB; "
            f"{len(sau_phe_duyet)} dòng chỉ điền được SAU phê duyệt/đăng ký "
            f"({'đã có attestation nên BẮT BUỘC' if attestation else 'thông tin, chưa chặn nộp'}) — "
            "ngoài các ô chỉ chứa PII và chỗ ký/ngày điền tay"
        ),
        "Điền nội dung thật; với PII dùng bản nộp ngoài hệ thống và giữ bản redacted. Ô sau phê duyệt "
        "(số IRB, ngày phê duyệt, mã/ngày đăng ký…) điền khi có quyết định, TRƯỚC khi ký khoá G2.",
    ))

    automatic.append(_criterion(
        "G2-AUTO-06",
        "Thiết kế và lộ trình đạo đức không còn mơ hồ",
        "REVIEW" if design_ambiguous else "PASS",
        f"design_code={design_code or 'không xác định'}; ambiguous={design_ambiguous}",
        "PI/methodologist xác nhận thiết kế rồi tính lại lộ trình IRB.",
    ))

    # VÁ 04/10/2026 (soát từng cổng, G2-05): G1 đổi thiết kế SAU khi sinh hồ sơ G2 từng không bị phát hiện — G2 vẫn chấm
    # (và ký) hồ sơ của thiết kế cũ. Lệch với G1 ĐÃ xác nhận ⇒ BLOCK; G1 chưa xác nhận ⇒ REVIEW.
    ma_g2 = S.ma_thiet_ke_chuoi(design_code) if design_code else None
    ma_g1 = S.ma_thiet_ke_chuoi(g1_design_code) if g1_design_code else None
    if not ma_g2:
        tk_trang, tk_bang = "BLOCK", (f"không xác định được thiết kế của hồ sơ G2 (design_code={design_code!r}) — "
                                       "không mặc định «cohort»")
    elif ma_g1 and ma_g1 != ma_g2:
        tk_trang = "BLOCK" if g1_da_chot else "REVIEW"
        tk_bang = (f"hồ sơ G2 sinh cho «{ma_g2}» nhưng G1 hiện là «{ma_g1}»"
                   + (" (G1 đã xác nhận)" if g1_da_chot else " (G1 chưa xác nhận)"))
    else:
        tk_trang, tk_bang = "PASS", f"hồ sơ G2 và G1 cùng thiết kế «{ma_g2}»" if ma_g1 else f"thiết kế «{ma_g2}»"
    automatic.append(_criterion(
        "G2-AUTO-06b",
        "Hồ sơ G2 sinh đúng thiết kế G1 hiện hành",
        tk_trang,
        tk_bang,
        "Chạy lại run_g2_auto.py với thiết kế G1 đã xác nhận (hồ sơ cũ được sao lưu).",
    ))

    # VÁ 04/10/2026 (soát từng cổng, G2-03 / QĐ-4 — mặc định an toàn chờ bác sĩ duyệt): bản cũ dò ba cụm «AE/SAE»,
    # «DSMB», «quy tắc dừng» trên cả hồ sơ mà khuôn sinh luôn in sẵn cho RCT ⇒ luôn đúng. Nay đòi tệp kế hoạch an toàn
    # riêng đủ 5 mục có nội dung + PI xác nhận (kiem_ke_hoach_an_toan).
    safety_status, safety_evidence = kiem_ke_hoach_an_toan(package_path.parent, study, design_code, meta)
    automatic.append(_criterion(
        "G2-AUTO-07",
        "Kế hoạch an toàn tương xứng thiết kế",
        safety_status,
        safety_evidence,
        f"Điền {ten_ke_hoach_an_toan(study)} (5 mục: định nghĩa AE/SAE/SUSAR, mốc báo cáo, quy tắc dừng, DSMB/DMC hoặc "
        "lý do không lập, biểu mẫu AE) rồi PI ghi gate_params.G2.safety_plan_confirmed=true.",
    ))

    # WHO TRDS 13/14/19/20 chỉ được điền từ StudyMeta do PI xác nhận. Thiếu
    # bất kỳ mục nào vẫn là REVIEW và nay tham gia quyết định trạng thái G2.
    still_empty_scientific = scientific_registration_item_gaps(
        registration,
        design_code,
    )
    automatic.append(_criterion(
        "G2-AUTO-08",
        "Mục khoa học WHO TRDS (can thiệp/tiêu chí/kết cục) đã có nội dung thật",
        "REVIEW" if still_empty_scientific else "PASS",
        (
            f"còn trống: {', '.join(still_empty_scientific)}"
            if still_empty_scientific
            else "mục 13/14/19/20 đã có nội dung"
        ),
        "Điền Intervention(s)/Inclusion-Exclusion/Primary-Secondary Outcome "
        "từ PICO thật của đề tài (checkpoint G1) trước khi đăng ký thật.",
    ))
    # VÁ 04/10/2026 (G2-07): mục máy TỰ ĐIỀN (9 Public title, 12 Health condition chép tên đề tài; masking của RCT).
    chua_khai = registration_pi_confirmation_gaps(registration, design_code)
    automatic.append(_criterion(
        "G2-AUTO-08b",
        "Mục WHO TRDS tự điền đã được PI khai (9 tiêu đề công khai, 12 tình trạng sức khỏe, 15 masking của RCT)",
        "REVIEW" if chua_khai else "PASS",
        ("chưa khai: " + "; ".join(chua_khai)) if chua_khai else "mục 9/12 (và masking RCT) đã do PI khai",
        "Khai gate_params.G2.public_title (ngôn ngữ đại chúng), gate_params.G2.health_condition và — với RCT — "
        "gate_params.G1.blinding, rồi chạy lại run_g2_auto.py để làm mới bản đăng ký.",
    ))
    # VÁ 04/10/2026 (G2-08 / QĐ-6 — mặc định an toàn chờ bác sĩ duyệt): phiên bản đề cương/ICF «hiện hành» là KHAI BÁO
    # của PI (khuôn không còn gieo «1.0»). «1.0» trên đề tài cũ có thể là giá trị khuôn gieo trước 04/10/2026.
    g2m = _g2_meta(meta)
    thieu_pb = [k for k in ("protocol_version", "icf_version")
                if not _real_text(g2m.get(k)) and not (k == "icf_version" and g2m.get("icf_waiver_requested") is True)]
    automatic.append(_criterion(
        "G2-AUTO-10",
        "Phiên bản đề cương/ICF hiện hành do PI khai",
        "REVIEW" if thieu_pb else "PASS",
        (f"chưa khai: {', '.join(thieu_pb)}" if thieu_pb else
         f"protocol_version={g2m.get('protocol_version')}; icf_version={g2m.get('icf_version') or 'miễn ICF'}"
         + ("; «1.0» có thể là giá trị khuôn gieo trước 04/10/2026 — PI xác nhận"
            if "1.0" in (str(g2m.get("protocol_version")), str(g2m.get("icf_version"))) else "")),
        "PI khai gate_params.G2.protocol_version và icf_version (đúng phiên bản trình Hội đồng).",
    ))

    attestation_errors = validate_attestation(
        attestation=attestation,
        package_text=package_text,
        study=study,
        design_code=design_code,
        meta=meta,
        today=today,
        out_dir=package_path.parent,
    ) if attestation else ["Chưa có phụ lục quyết định IRB có cấu trúc"]
    approval.append(_criterion(
        "G2-HUMAN-01",
        "Quyết định IRB/IEC có số, ngày, hiệu lực, phạm vi và phiên bản",
        "PASS" if not attestation_errors else "REVIEW",
        "; ".join(attestation_errors) if attestation_errors else "attestation hợp lệ",
        "Hội đồng/đầu mối được ủy quyền ghi quyết định bằng approve_gate.py.",
    ))
    approval.append(_criterion(
        "G2-HUMAN-02",
        "Approval ledger đúng vai trò IRB và khớp hash artifact",
        "PASS" if ledger_approved else "REVIEW",
        f"ledger_approved={ledger_approved}",
        "Người có thẩm quyền IRB tự ký; agent không được chạy lệnh phê duyệt.",
    ))

    # G2-F5 (30/07/2026): --reviewer-ref dùng CHUNG cho mọi cổng/vai trò, không phải mã Hội đồng Đạo đức — trước đây
    # ethics_committee_ref luôn = reviewer_ref nên validate_attestation (chỉ kiểm «không rỗng») luôn đạt. Cờ
    # --g2-ethics-committee-ref tách ngữ nghĩa; thiếu cờ thì approve_gate ghi nguồn «reviewer_ref_fallback».
    # (Sửa chú thích 04/10/2026, G2-12: tiêu chí này THAM GIA quyết định trạng thái như mọi tiêu chí tự động — chú
    # thích cũ nói «loại khỏi auto_blocked/auto_review» là sai từ khi danh sách loại trừ bị làm rỗng.)
    ethics_ref_source = attestation.get("ethics_committee_ref_source") if attestation else None
    # KHÔNG so == "reviewer_ref_fallback": attestation KÝ TRƯỚC khi cờ
    # --g2-ethics-committee-ref tồn tại không có field này (None), và None
    # cũng phải REVIEW — chỉ "explicit" (đã dùng cờ mới) mới PASS. Chưa có
    # attestation nào (chưa ký) thì chưa có gì để nhắc — PASS vacuously,
    # G2-HUMAN-01 đã tự báo "Chưa có phụ lục quyết định IRB" riêng.
    automatic.append(_criterion(
        "G2-AUTO-09",
        "Mã Hội đồng Đạo đức tách biệt khỏi định danh người duyệt chung",
        "REVIEW" if attestation and ethics_ref_source != "explicit" else "PASS",
        f"ethics_committee_ref_source={ethics_ref_source or 'chưa có attestation'}",
        "Ký lại bằng approve_gate.py --gate G2 kèm --g2-ethics-committee-ref "
        "để tách mã hội đồng khỏi --reviewer-ref dùng chung.",
    ))

    # Mọi tiêu chí tự động đều lái trạng thái (G2-12, 04/10/2026: bỏ danh sách loại trừ rỗng và chú thích cũ nói
    # G2-AUTO-08 «cố ý loại khỏi auto_review» — sai từ khi danh sách đó rỗng; nay mục 13/14/19/20 điền được từ
    # study_meta nên không còn lý do loại).
    _status_driving = list(automatic)
    auto_blocked = any(row["status"] == "BLOCK" for row in _status_driving)
    auto_review = any(row["status"] == "REVIEW" for row in _status_driving)
    approval_complete = all(row["status"] == "PASS" for row in approval)
    if auto_blocked:
        status = STATUS_BLOCKED
    elif auto_review:
        status = STATUS_DRAFT
    elif not attestation:
        status = STATUS_READY
    elif not approval_complete:
        status = STATUS_PENDING
    else:
        status = STATUS_APPROVED

    pending = [
        row["action"] for row in automatic + approval
        if row["status"] != "PASS" and row.get("action")
    ]
    return {
        "contract_version": QUALITY_CONTRACT_VERSION,
        "study": study,
        "gate": "G2",
        "status": status,
        "package_checks_passed": not auto_blocked,
        "package_ready_for_submission": not auto_blocked and not auto_review,
        "human_approval_complete": approval_complete,
        "automatic_criteria": automatic,
        "human_approval_criteria": approval,
        "unresolved_critical_placeholders": unresolved,
        "pre_submission_placeholders": truoc_nop,
        "post_approval_placeholders": sau_phe_duyet,
        "post_study_placeholders": sau_nghien_cuu,
        "pending_actions": list(dict.fromkeys(pending)),
        "attestation": attestation,
        "standards_basis": list(STANDARDS_BASIS),
        "scope_statement": (
            "PASS_G2_APPROVED chỉ xác nhận dấu vết IRB/IEC, phiên bản và đăng ký "
            "đã cung cấp cho hệ thống. HMAC cục bộ không tự chứng minh tính độc lập "
            "của Hội đồng; hồ sơ gốc và quyết định thật vẫn phải được kiểm tra."
        ),
        "disclaimer": "Cần bác sĩ kiểm chứng.",
    }


def write_quality_report(study: str, out_dir: Path, report: Mapping[str, Any]) -> Path:
    """Ghi JSON máy đọc và Markdown để bác sĩ rà."""
    out_dir = Path(out_dir)
    json_path = out_dir / "G2_QUALITY_REPORT.json"
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8", newline="\n"
    )
    lines = [
        f"# G2 QUALITY REPORT — {study}",
        "",
        f"- Trạng thái: **{report.get('status')}**",
        f"- Hồ sơ sẵn sàng nộp: **{report.get('package_ready_for_submission')}**",
        f"- Phê duyệt người thật đủ: **{report.get('human_approval_complete')}**",
        "",
        "## Kiểm tự động",
        "| ID | Tiêu chí | Trạng thái | Bằng chứng |",
        "|---|---|---|---|",
    ]
    for row in report.get("automatic_criteria", []):
        evidence = str(row.get("evidence") or "").replace("|", "/")
        lines.append(f"| {row['id']} | {row['label']} | {row['status']} | {evidence} |")
    lines.extend([
        "",
        "## Phê duyệt người thật",
        "| ID | Tiêu chí | Trạng thái | Bằng chứng |",
        "|---|---|---|---|",
    ])
    for row in report.get("human_approval_criteria", []):
        evidence = str(row.get("evidence") or "").replace("|", "/")
        lines.append(f"| {row['id']} | {row['label']} | {row['status']} | {evidence} |")
    sau_phe_duyet = report.get("post_approval_placeholders") or []
    if sau_phe_duyet:
        lines.extend([
            "",
            "## Ô chỉ điền được SAU phê duyệt/đăng ký",
            "Không chặn nộp IRB; BẮT BUỘC điền trước khi ký khoá G2 (approve_gate từ chối ký khi còn).",
        ])
        lines.extend(f"- {str(item).replace('|', '/')}" for item in sau_phe_duyet)
    lines.extend(["", "## Việc còn lại"])
    pending = report.get("pending_actions") or []
    lines.extend(f"- {item}" for item in pending)
    if not pending:
        lines.append("- Không còn mục chờ trong hợp đồng G2.")
    lines.extend([
        "",
        "## Giới hạn",
        str(report.get("scope_statement") or ""),
        "",
        "> Cần bác sĩ kiểm chứng.",
    ])
    md_path = out_dir / "G2_QUALITY_REPORT.md"
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return md_path


def refresh_checkpoint(
    *,
    study: str,
    out_dir: Path,
    report: Mapping[str, Any],
    quality_report_path: Path,
) -> Path:
    """Cập nhật trạng thái G2 từ báo cáo; không tự tạo phê duyệt."""
    out_dir = Path(out_dir)
    checkpoint_path = out_dir / "G2_checkpoint.json"
    checkpoint = _read_json(checkpoint_path)
    checkpoint.update({
        "study": study,
        "gate": "G2",
        "quality_contract_version": QUALITY_CONTRACT_VERSION,
        "quality_gate": dict(report),
        "pending_doctor_actions": list(report.get("pending_actions") or []),
    })
    artifacts = checkpoint.get("artifacts")
    if not isinstance(artifacts, dict):
        artifacts = {}
        checkpoint["artifacts"] = artifacts
    artifacts["quality_report"] = str(quality_report_path)
    if report.get("status") == STATUS_APPROVED:
        attestation = report.get("attestation") or {}
        registration = attestation.get("registration") or {}
        checkpoint.update({
            "gate_status": "PASS — G2 ĐÃ CÓ PHÊ DUYỆT IRB/IEC THẬT VÀ ĐĂNG KÝ HỢP LỆ",
            "g2_status": "LOCKED",
            "g2_irb_number": attestation.get("approval_number"),
            "g2_approval_date": attestation.get("approval_date"),
            "g2_approval_valid_until": attestation.get("valid_until"),
            "g2_no_expiry_confirmed": attestation.get("no_expiry_confirmed") is True,
            "g2_protocol_version": attestation.get("approved_protocol_version"),
            "g2_icf_version": attestation.get("approved_icf_version"),
            "g2_icf_waiver_approved": attestation.get("icf_waiver_approved") is True,
            "g2_registration": registration.get("registration_id"),
        })
    else:
        checkpoint["gate_status"] = f"{report.get('status')} — G2 CHƯA ĐƯỢC KHÓA"
        checkpoint["g2_status"] = "PENDING"
        # VÁ 04/10/2026 (soát từng cổng, G7-03 phía G2): trạng thái TỤT khỏi PASS_G2_APPROVED (hết hạn, đề cương đổi sau
        # khi duyệt, ledger hỏng…) từng giữ nguyên số IRB/ngày duyệt/phiên bản cũ trong checkpoint — cổng sau (G7 viết
        # Đạo đức, G10) đọc chúng như còn hiệu lực. Xoá các trường khoá khi không còn APPROVED.
        for khoa in ("g2_irb_number", "g2_approval_date", "g2_approval_valid_until", "g2_no_expiry_confirmed",
                     "g2_protocol_version", "g2_icf_version", "g2_icf_waiver_approved", "g2_registration"):
            checkpoint.pop(khoa, None)
    checkpoint["disclaimer"] = "Cần bác sĩ kiểm chứng."
    PF.ghi_checkpoint_giu_moc_sinh(checkpoint_path, json.dumps(checkpoint, ensure_ascii=False, indent=2))
    return checkpoint_path


def evaluate_study(
    study: str,
    out_dir: Path,
    *,
    repo_root: Optional[Path] = None,
    write: bool = True,
    today: Optional[date] = None,
) -> dict[str, Any]:
    """Đọc artifact hiện có và đánh giá lại G2 mà không sinh/ghi phê duyệt."""
    out_dir = Path(out_dir)
    repo_root = Path(repo_root) if repo_root else out_dir.parent.parent
    checkpoint = _read_json(out_dir / "G2_checkpoint.json")
    g1 = _read_json(out_dir / "G1_checkpoint.json")
    meta = _read_json(out_dir / "study_meta.json")
    package_path = out_dir / f"G2_A3_ETHICS_PACKAGE_{study}.md"
    registration_path = out_dir / f"G2_REGISTRATION_DRAFT_{study}.json"
    # VÁ 04/10/2026 (soát từng cổng, G2-05/CHUNG-F): không còn mặc định im lặng «cohort» khi thiếu thiết kế — thiếu thì
    # G2-AUTO-06b CHẶN. Thiết kế của HỒ SƠ (checkpoint G2) được đối chiếu với thiết kế G1 HIỆN HÀNH.
    g1_design_code = str((g1.get("design") or {}).get("internal_code") or "") or None
    design_code = str(checkpoint.get("design_code") or g1_design_code or "")
    guardrail = checkpoint.get("guardrail") or {}
    guardrail_passed = bool(
        isinstance(guardrail, Mapping) and guardrail.get("passed") is True
    )
    ledger_ok = GC.ledger_approved(
        "G2",
        study,
        package_path,
        repo_root=repo_root,
    )
    report = evaluate_g2_quality(
        study=study,
        design_code=design_code,
        package_path=package_path,
        registration_path=registration_path,
        g1_checkpoint=g1,
        meta=meta,
        guardrail_passed=guardrail_passed,
        ledger_approved=ledger_ok,
        design_ambiguous=bool(checkpoint.get("design_ambiguous")),
        today=today,
        g1_song=CS.trang_thai_song("G1", study, out_dir) if g1 else None,
        g1_design_code=g1_design_code,
    )
    if write:
        report_path = write_quality_report(study, out_dir, report)
        # VÁ 26/08/2026: out_dir luôn TUYỆT ĐỐI (repo_root / "exports" / study),
        # nên report_path cũng tuyệt đối — nhưng run_g2_auto.py (tool sinh artifact,
        # dùng Path("exports") / study tương đối theo CWD) ghi field CÙNG TÊN
        # artifacts["quality_report"] dạng tương đối. Chạy công cụ này (đúng thiết
        # kế: chấm lại, không tự phê duyệt) sẽ âm thầm thay đường dẫn tương đối
        # sạch bằng đường dẫn tuyệt đối RIÊNG CỦA MÁY NÀY trong checkpoint dùng
        # chung qua git — đúng họ lỗi BH06 (không đường dẫn cứng của một máy).
        # Chỉ đổi CHUỖI được ghi vào checkpoint; write_quality_report() ở trên vẫn
        # ghi file thật bằng out_dir tuyệt đối, không đổi hành vi I/O.
        try:
            recorded_path = report_path.relative_to(repo_root)
        except ValueError:
            recorded_path = report_path
        refresh_checkpoint(
            study=study,
            out_dir=out_dir,
            report=report,
            quality_report_path=recorded_path,
        )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Đánh giá lại G2; không tự phê duyệt hoặc ký thay IRB."
    )
    parser.add_argument("--study", required=True)
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    out_dir = repo_root / "exports" / args.study
    report = evaluate_study(args.study, out_dir, repo_root=repo_root, write=True)
    print(f"G2 quality status: {report['status']}")
    print(f"Báo cáo: {out_dir / 'G2_QUALITY_REPORT.md'}")
    print("Cần bác sĩ kiểm chứng.")
    return 0 if report["status"] != STATUS_BLOCKED else GC.EXIT_GUARDRAIL_FAIL


if __name__ == "__main__":
    raise SystemExit(main())
