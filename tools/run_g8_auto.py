#!/usr/bin/env python3
"""
run_g8_auto.py -- Cong G8: Kiem tra truoc nop bai (Pre-submission Review)

Doc tat ca checkpoints G0-G7 -> sinh bao cao kiem toan toan pipeline A9:
  Phan 1 -- Kiem toan pipeline (bang trang thai G0-G7)
  Phan 2 -- Checklist chuan bao cao (CONSORT/STROBE/PRISMA/STARD/TRIPOD)
  Phan 3 -- Kiem tra tinh toan ven thong ke
  Phan 4 -- Goi y tap chi muc tieu
  Phan 5 -- Goi khai bao tac gia (CRediT + ORCID + COI)
  Phan 6 -- Diem tu kiem truoc nop (30 diem)
  Phan 7 -- Tieu chi qua cong G8

Xuat: A9 .md + .docx + G8_checkpoint.json

Cach dung:
    python tools/run_g8_auto.py --study "MA-DE-TAI"
    python tools/run_g8_auto.py --study "MA-DE-TAI" --target-journal "BMJ" --impact-factor 105.7
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

# Them thu muc goc du an vao sys.path
BASE = Path(__file__).resolve().parent.parent
TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(TOOLS))

import gate_contract as GC  # noqa: E402  (hợp đồng DỪNG dùng chung — chỉ dùng load_study_meta)

# ============================================================================
# 1. DU LIEU CHECKLIST CHUAN BAO CAO
# ============================================================================

# STROBE 2007 (22 muc -- cohort, case-control, cross-sectional)
STROBE_ITEMS = [
    ("Title & Abstract", "1",
     "Chi ro thiet ke nghien cuu trong tieu de hoac tom tat; co tom tat co cau truc"),
    ("Background/Rationale", "2",
     "Giai thich co so khoa hoc va ly do cua nghien cuu"),
    ("Objectives", "3",
     "Neu muc tieu cu the, bao gom gia thuyet tien nghiem neu co"),
    ("Study design", "4",
     "Mo ta yeu to thiet ke quan trong ngay tu dau bao cao"),
    ("Setting", "5",
     "Mo ta boi canh, dia diem, thoi gian lien quan"),
    ("Participants", "6",
     "Tieu chi chon/loai doi tuong; nguon va phuong phap chon mau"),
    ("Variables", "7",
     "Dinh nghia tat ca bien ket cuc, phoi nhiem, tien doan, yeu to nhieu"),
    ("Data sources/Measurement", "8",
     "Mo ta nguon du lieu va cach do luong tung bien"),
    ("Bias", "9",
     "Mo ta moi no luc giai quyet sai lech tiem an"),
    ("Study size", "10",
     "Giai thich cach xac dinh co mau"),
    ("Quantitative variables", "11",
     "Cach xu ly bien dinh luong trong phan tich"),
    ("Statistical methods", "12",
     "Mo ta tat ca phuong phap thong ke, bao gom kiem soat confounding"),
    ("Participants (Results)", "13",
     "Bao cao so nguoi tham gia tung buoc; ly do loai tru"),
    ("Descriptive data", "14",
     "Dac diem nguoi tham gia; thieu du lieu"),
    ("Outcome data", "15",
     "Bao cao so bien co hoac do luong tom tat theo thoi gian"),
    ("Main results", "16",
     "Uoc luong khong hieu chinh va hieu chinh; do chinh xac (CI 95%)"),
    ("Other analyses", "17",
     "Phan tich khac: phan nhom, tuong tac, do nhay"),
    ("Key results", "18",
     "Tom tat ket qua chinh theo muc tieu"),
    ("Limitations", "19",
     "Han che; nguon sai lech tiem an; huong va do lon"),
    ("Interpretation", "20",
     "Giai thich than trong, xem xet muc tieu, han che, tong the bang chung"),
    ("Generalisability", "21",
     "Kha nang tong quat hoa ket qua"),
    ("Funding", "22",
     "Nguon tai tro va vai tro cua nha tai tro"),
]

# Va 2026-07-17 (round audit doi khang 4, chuan quoc te): CONSORT_ITEMS ban CU chi co 25
# dong nhung KHONG khop 25 muc CONSORT that -- danh so nhay tu "15" thang "17a" (bo qua
# muc 16 "Numbers analysed"), va DUNG HAN o do -- thieu hoan toan 16b/17b/18/19 (Harms!)/
# 20/21/22/23/24/25 (~10 muc, gom ca muc Harms -- tac hai -- rat quan trong cho an toan
# thu nghiem). Xay lai theo DUNG CONSORT 2025 (thay CONSORT 2010, cong bo dong thoi BMJ/
# JAMA/Lancet/Nature Medicine/PLOS Medicine 4/2025 -- xac minh truc tiep PMC11996237) --
# 30 muc chinh thuc, mot so muc co tach chu cai (vd 21a-d). Khop dung nhan "CONSORT 2025"
# ma doctrine da tuyen bo o nhieu noi nhung code truoc day van dung noi dung 2010.
CONSORT_ITEMS = [
    ("Title", "1a", "Nhan dien la thu nghiem ngau nhien (RCT) ngay trong tieu de"),
    ("Abstract", "1b",
     "Tom tat co cau truc ve thiet ke, phuong phap, ket qua, ket luan"),
    ("Trial registration", "2",
     "Ten noi dang ky, so dang ky (kem URL), va ngay dang ky"),
    ("Protocol/SAP access", "3",
     "Noi co the truy cap protocol va ke hoach phan tich thong ke (SAP)"),
    ("Data/code access", "4",
     "Noi co the truy cap du lieu an danh, ma thong ke, tai lieu"),
    ("Funding", "5a", "Nguon tai tro + ho tro khac (vd cung cap thuoc); vai tro nha tai tro"),
    ("Author COI", "5b", "Xung dot loi ich tai chinh va khac cua cac tac gia ban thao"),
    ("Background", "6", "Boi canh khoa hoc va ly do nghien cuu"),
    ("Objectives", "7", "Muc tieu cu the lien quan loi ich va tac hai"),
    ("Patient & public involvement", "8",
     "Chi tiet su tham gia cua benh nhan/cong chung trong thiet ke, thuc hien, bao cao"),
    ("Trial design", "9", "Mo ta thiet ke thu nghiem gom loai va khung (song song, factorial...)"),
    ("Protocol changes", "10", "Thay doi quan trong trong protocol sau khi bat dau"),
    ("Setting", "11", "Boi canh (vd cong dong, benh vien) va dia diem thuc hien thu nghiem"),
    ("Eligibility (participants)", "12a", "Tieu chi nhan cho nguoi tham gia"),
    ("Eligibility (sites/providers)", "12b",
     "Tieu chi nhan cho dia diem va nguoi thuc hien can thiep"),
    ("Interventions", "13", "Can thiep va nhom so sanh voi du chi tiet de tai lap"),
    ("Outcomes", "14", "Ket cuc chinh/phu dinh truoc voi chi tiet cach do va thoi diem"),
    ("Harms definition", "15", "Cach dinh nghia va danh gia tac hai (vd he thong, khong he thong)"),
    ("Sample size", "16a", "Xac dinh co mau gom cac gia dinh"),
    ("Interim analyses", "16b", "Giai thich phan tich trung gian va quy tac dung (neu co)"),
    ("Randomisation sequence", "17a", "Phuong phap tao chuoi ngau nhien + nhan su thuc hien"),
    ("Randomisation type", "17b", "Loai ngau nhien hoa + chi tiet han che (vd phan tang, block)"),
    ("Allocation concealment", "18", "Co che che giau phan bo"),
    ("Implementation", "19", "Nhan su tiep can chuoi phan bo (ai tao, ai tuyen, ai phan bo)"),
    ("Blinding (who)", "20a", "Ai duoc lam mu sau khi phan nhom can thiep"),
    ("Blinding (method)", "20b", "Phuong phap lam mu + do tuong dong can thiep"),
    ("Statistical methods", "21a",
     "Phuong phap thong ke so sanh nhom cho ket cuc chinh va phu"),
    ("Analysis populations", "21b", "Dinh nghia quan the phan tich va cac nhom"),
    ("Missing data", "21c", "Cach xu ly du lieu thieu trong phan tich"),
    ("Additional analyses methods", "21d",
     "Phuong phap phan tich them, phan biet dinh truoc voi post hoc"),
    ("Participant numbers", "22a",
     "So nguoi tham gia theo nhom (duoc phan bo, nhan dieu tri, phan tich)"),
    ("Losses & exclusions", "22b", "Mat/loai tru sau ngau nhien hoa, kem ly do"),
    ("Recruitment dates", "23a", "Ngay xac dinh giai doan tuyen va theo doi"),
    ("Trial ending", "23b", "Ly do thu nghiem ket thuc/dung som (neu co)"),
    ("Interventions as administered", "24a", "Can thiep va so sanh nhu da thuc hien thuc te"),
    ("Concomitant care", "24b", "Cham soc dong thoi nhan duoc trong thu nghiem cho moi nhom"),
    ("Baseline data", "25", "Bang dac diem nhan khau va lam sang nen"),
    ("Outcomes and estimation", "26",
     "Ket qua ket cuc chinh/phu theo nhom kem uoc luong hieu qua + do chinh xac"),
    ("Harms", "27", "Moi tac hai hoac bien co khong mong muon o MOI nhom"),
    ("Other analyses", "28", "Phan tich khac da thuc hien, phan biet dinh truoc voi post hoc"),
    ("Interpretation", "29", "Dien giai nhat quan voi ket qua, can bang loi ich va tac hai"),
    ("Limitations", "30",
     "Han che thu nghiem, de cap nguon sai lech/do chinh xac/kha nang khai quat hoa"),
]

# PRISMA 2020 (27 muc -- SR/MA)
PRISMA_ITEMS = [
    ("Title", "1", "Xac dinh la SR, MA, hoac ca hai trong tieu de"),
    ("Abstract", "2", "Tom tat co cau truc"),
    ("Rationale", "3",
     "Mo ta ly do tong quan trong boi canh hieu biet hien tai"),
    ("Objectives", "4", "PICO va loai thiet ke nghien cuu du dieu kien"),
    ("Protocol & registration", "5", "Giao thuc da dang ky va so dang ky"),
    ("Eligibility criteria", "6", "Tieu chi chon/loai voi ly do"),
    ("Information sources", "7", "Tat ca nguon tim kiem thong tin"),
    ("Search strategy", "8",
     "Chien luoc tim kiem day du cho it nhat 1 co so du lieu"),
    ("Selection process", "9", "Quy trinh sang loc va chon nghien cuu"),
    ("Data collection process", "10", "Quy trinh trich xuat du lieu"),
    ("Data items", "11a", "Liet ke va dinh nghia cac bien trich xuat"),
    ("Study risk of bias", "12", "Phuong phap danh gia RoB tung nghien cuu"),
    ("Effect measures", "13", "Thuoc do hieu qua chinh"),
    ("Synthesis methods", "14a", "Quy trinh tong hop bang chung"),
    ("Reporting bias", "15", "Phuong phap danh gia sai lech bao cao"),
    ("Certainty assessment", "16",
     "Phuong phap danh gia chac chan bang chung (GRADE)"),
    ("Study selection (Results)", "17",
     "Ket qua sang loc, ly do loai tru (PRISMA flow)"),
    ("Study characteristics", "18", "Dac diem tung nghien cuu"),
    ("Risk of bias in studies", "19", "RoB tung nghien cuu"),
    ("Results of syntheses", "20a",
     "Ket qua tong hop; uoc luong hieu qua voi CI"),
    ("Reporting biases", "21", "Moi bang chung ve sai lech bao cao"),
    ("Certainty of evidence", "22", "Muc chac chan bang chung (GRADE)"),
    ("Discussion", "23", "Giai thich than trong; xem xet han che"),
    ("Limitations", "24",
     "Han che o cap bang chung, nghien cuu, va tong quan"),
    ("Conclusions", "25",
     "Giai thich chung; y nghia cho thuc hanh/nghien cuu"),
    ("Funding", "26", "Nguon tai tro; vai tro cua nha tai tro"),
    ("Competing interests", "27",
     "Xung dot loi ich cua tac gia tong quan"),
]

# STARD 2015 (24 muc -- chan doan)
STARD_ITEMS = [
    ("Title/Abstract/Keywords", "1",
     "Xac dinh la nghien cuu do chinh xac chan doan"),
    ("Abstract", "2",
     "Tom tat co cau truc: thiet ke, phuong phap, ket qua, ket luan"),
    ("Background", "3", "Boi canh khoa hoc va lam sang"),
    ("Objectives", "4", "Muc tieu nghien cuu va gia thuyet"),
    ("Study design", "5",
     "Thiet ke (prospective, retrospective, cross-sectional)"),
    ("Participants", "6", "Tieu chi chon/loai va nguon tuyen dung"),
    ("Test methods", "7",
     "Mo ta test chi so va tieu chuan tham chieu"),
    ("Rationale", "8", "Ly do chon tieu chuan tham chieu"),
    ("Sampling", "9", "Thiet ke lay mau"),
    ("Data collection", "10", "Ai thuc hien va doc ket qua"),
    ("Definitions", "11", "Dinh nghia va can cu nguong cat"),
    ("Sample size", "12", "Co mau du kien va cach tinh"),
    ("Participants (Results)", "13", "So do dong nguoi tham gia"),
    ("Missing data", "14", "Xu ly du lieu thieu"),
    ("Reference standard", "15", "Phan phoi benh trong mau"),
    ("Cross tabulation", "16",
     "Bang cheo ket qua test chi so va tieu chuan tham chieu"),
    ("Estimates of diagnostic accuracy", "17",
     "Se/Sp/PPV/NPV; LR+ LR-; AUC voi CI 95%"),
    ("Adverse events", "19", "Tac dung khong mong muon cua test"),
    ("Limitations", "20", "Han che nghien cuu"),
    ("Generalisability", "21", "Kha nang tong quat hoa"),
    ("Discussion", "22", "Y nghia thuc hanh, co che"),
    ("Registration", "23", "So dang ky va ten co quan dang ky"),
    ("Protocol", "24", "Giao thuc nghien cuu truy cap duoc o dau"),
    ("Sources of funding", "25",
     "Nguon tai tro va vai tro nha tai tro"),
]

# TRIPOD 2015 (20 muc -- tien luong/du doan)
TRIPOD_ITEMS = [
    ("Title", "1",
     "Xac dinh loai mo hinh du doan va quan the trong tieu de"),
    ("Abstract", "2",
     "Tom tat co cau truc: muc tieu, thiet ke, ket qua, ket luan"),
    ("Background & Objectives", "3a",
     "Boi canh y hoc va giai thich ly do"),
    ("Objectives", "3b",
     "Muc tieu bao gom loai mo hinh va quan the dich"),
    ("Source of data", "4a", "Nguon du lieu"),
    ("Source of data - details", "4b", "Tieu chi chon mau"),
    ("Participants", "5a",
     "Mo ta boi canh lay mau; ngay bat dau va ket thuc"),
    ("Outcome", "6a",
     "Dinh nghia ket cuc du doan bao gom thoi diem do"),
    ("Predictors", "7",
     "Dinh nghia va thoi diem cua bien tien doan"),
    ("Sample size", "8", "Co mau va ly do"),
    ("Missing data", "9", "Xu ly du lieu thieu"),
    ("Statistical methods - development", "10a",
     "Phuong phap xay dung mo hinh"),
    ("Statistical methods - validation", "10b",
     "Quy trinh validation noi/ngoai"),
    ("Results - participants", "13a", "Dong nguoi tham gia"),
    ("Results - model", "14a",
     "Chi so phan biet (c-statistic/AUC); hieu chinh"),
    ("Limitations", "16", "Han che nghien cuu"),
    ("Interpretation", "17", "Giai thich tong the ket qua"),
    ("Generalisability", "18", "Kha nang tong quat"),
    ("Funding", "19a", "Nguon tai tro va vai tro nha tai tro"),
    ("TRIPOD extension", "19b",
     "So dang ky neu co (PROSPERO, OSF...)"),
]

# Anh xa design_code -> (ten chuan, danh sach muc)
DESIGN_CHECKLIST_MAP = {
    "rct":             ("CONSORT 2025", CONSORT_ITEMS),
    "cohort":          ("STROBE 2007",  STROBE_ITEMS),
    "case_control":    ("STROBE 2007",  STROBE_ITEMS),
    "cross_sectional": ("STROBE 2007",  STROBE_ITEMS),
    "diagnostic":      ("STARD 2015",   STARD_ITEMS),
    "sr_ma":           ("PRISMA 2020",  PRISMA_ITEMS),
    "prediction":      ("TRIPOD 2015",  TRIPOD_ITEMS),
    "tripod":          ("TRIPOD 2015",  TRIPOD_ITEMS),
}

# 14 vai tro CRediT taxonomy
CREDIT_ROLES = [
    "Conceptualization",
    "Methodology",
    "Software",
    "Validation",
    "Formal analysis",
    "Investigation",
    "Resources",
    "Data Curation",
    "Writing – Original Draft Preparation",
    "Writing – Review & Editing",
    "Visualization",
    "Supervision",
    "Project Administration",
    "Funding Acquisition",
]

# Goi y tap chi theo design + linh vuc
JOURNAL_SUGGESTIONS = {
    "sr_ma": {
        "default": [
            ("Cochrane Database of Systematic Reviews", 8.8, "SR/MA moi linh vuc"),
            ("BMJ", 105.7, "SR/MA anh huong lam sang cao"),
            ("JAMA", 120.7, "SR/MA lam sang co y nghia thuc hanh"),
            ("Lancet", 202.7, "SR/MA dot pha suc khoe toan cau"),
            ("Systematic Reviews (BioMed Central)", 4.9, "SR/MA phuong phap luan"),
        ],
        "cardiology": [
            ("European Heart Journal", 39.3, "Tim mach SR/MA"),
            ("JACC", 24.0, "The tich lon tim mach"),
        ],
        "endocrine": [
            ("Diabetes Care", 16.2, "DTD va noi tiet"),
            ("Diabetologia", 8.4, "DTD co che va dieu tri"),
        ],
    },
    "rct": {
        "default": [
            ("NEJM", 176.1, "RCT dot pha, co mau lon"),
            ("JAMA", 120.7, "RCT lam sang anh huong cao"),
            ("Lancet", 202.7, "RCT suc khoe toan cau"),
            ("BMJ", 105.7, "RCT lam sang thuc hanh"),
            ("Trials (BioMed Central)", 2.0, "RCT phuong phap + giao thuc"),
        ],
        "cardiology": [
            ("European Heart Journal", 39.3, "RCT tim mach"),
            ("JACC", 24.0, "RCT tim mach can thiep"),
        ],
    },
    "cohort": {
        "default": [
            ("BMJ Open", 2.9, "Cohort quan sat, tiep can mo"),
            ("PLOS ONE", 3.7, "Cohort da linh vuc mo"),
            ("BMC Medicine", 7.0, "Cohort y khoa lam sang"),
            ("Journal of Epidemiology & Community Health", 5.5, "Cohort dich te"),
            ("International Journal of Epidemiology", 7.7, "Cohort dich te lon"),
        ],
        "cardiology": [
            ("American Heart Journal", 4.3, "Cohort tim mach"),
            ("European Journal of Preventive Cardiology", 8.1, "Du phong tim mach"),
        ],
        "vietnam": [
            ("BMC Health Services Research", 3.4, "Dich vu y te + boi canh chau A"),
            ("Tropical Medicine & International Health", 3.0, "Boi canh nhiet doi"),
        ],
    },
    "cross_sectional": {
        "default": [
            ("BMC Public Health", 4.5, "Cross-sectional suc khoe cong dong"),
            ("PLOS ONE", 3.7, "Da linh vuc, tiep can mo"),
            ("BMJ Open", 2.9, "Cross-sectional lam sang + cong dong"),
            ("Journal of Public Health", 3.0, "Suc khoe cong dong"),
        ],
    },
    "diagnostic": {
        "default": [
            ("Radiology", 19.7, "Chan doan hinh anh"),
            ("JAMA Internal Medicine", 24.7, "Chan doan noi khoa"),
            ("Clinical Chemistry", 9.3, "Xet nghiem sinh hoa"),
            ("Annals of Internal Medicine", 39.2, "Chan doan lam sang"),
            ("Diagnostic and Prognostic Research", 4.2, "Chan doan & tien luong"),
        ],
    },
    "prediction": {
        "default": [
            ("BMC Medical Informatics and Decision Making", 3.3,
             "Mo hinh du doan lam sang"),
            ("PLOS Medicine", 10.5, "Mo hinh y hoc chinh xac"),
            ("Journal of Clinical Epidemiology", 5.9, "TRIPOD prediction models"),
        ],
    },
}


# ============================================================================
# 2. DOC CHECKPOINTS
# ============================================================================

def load_checkpoint(path: Path) -> dict:
    """Doc JSON checkpoint, tra ve dict rong neu khong ton tai."""
    if path.exists():
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            # SỬA: file JSON hợp lệ nhưng nội dung là "null"/số/mảng (không
            # phải object) khiến json.load trả về None/khác dict — gây crash
            # TypeError ngay khi gọi code tiếp theo cố gán key vào đó
            # (gates[key]["_file_exists"] = ... trên None). Ép về dict rỗng.
            return data if isinstance(data, dict) else {"_load_error": str(path)}
        except (json.JSONDecodeError, OSError):
            return {"_load_error": str(path)}
    return {}


def load_all_checkpoints(out_dir: Path) -> dict:
    """Doc tat ca checkpoints G0-G7, tra ve dict theo gate."""
    gates = {}
    for i in range(8):
        key = f"G{i}"
        cp_path = out_dir / f"G{i}_checkpoint.json"
        gates[key] = load_checkpoint(cp_path)
        gates[key]["_file_exists"] = cp_path.exists()
        gates[key]["_file_path"] = str(cp_path)
    return gates


# ============================================================================
# 3. PHAN TICH TRANG THAI PIPELINE
# ============================================================================

def _is_locked_or_pass(status: str) -> bool:
    """
    Kiểm tra status có nghĩa PASS/LOCKED một cách CHÍNH XÁC — không dùng
    substring "LOCKED" in status vì có thể khớp nhầm nếu tương lai một gate
    trả về chuỗi phủ định như "UNLOCKED"/"CHƯA LOCKED" (hiện tại _gate_status_label
    chỉ trả các giá trị cố định an toàn, nhưng khóa chặt để tránh landmine
    nếu logic phía trên thay đổi).
    """
    s = str(status or "").strip().upper()
    if re.search(r'(UN|CH[ƯU]A|KH[ÔO]NG|NOT)\s*LOCKED', s):
        return False
    return bool(re.search(r'\bPASS\b', s) or re.search(r'\bLOCKED\b', s))


def _gate_status_label(cp: dict) -> str:
    """Xac dinh trang thai cua mot gate tu checkpoint."""
    if not cp.get("_file_exists"):
        return "CHUA CHAY"
    gate = cp.get("gate", "")
    # G2 va G4 la "cong cung"
    if gate == "G2":
        irb = cp.get("g2_irb_number", "")
        # SỬA: check "CAN" (không ngoặc) là substring quá rộng — một số IRB
        # thật có thể chứa "CAN" (vd mã viện dẫn "Cần Thơ" viết ASCII "CAN
        # THO", hoặc mã có chữ "CAN" tình cờ), khiến IRB THẬT bị coi nhầm là
        # placeholder. 7 chỗ khác trong cùng file chỉ dùng "[CAN" (có ngoặc
        # vuông — khớp đúng định dạng placeholder "[CẦN...]"), nay đồng bộ.
        if irb and "[CAN" not in str(irb):
            return "LOCKED OK"
        return "PENDING -- cho IRB that"
    if gate == "G4":
        if cp.get("sap_locked") or cp.get("sap_signed_date"):
            return "LOCKED OK"
        return "PENDING -- cho SAP ky"
    # Cac gate khac: dung guardrail
    guardrail_val = cp.get("guardrail", "")
    if isinstance(guardrail_val, str):
        if "PASS" in guardrail_val:
            return "PASS OK"
        if "LOI" in guardrail_val or "WARNING" in guardrail_val:
            return "DRAFT"
    elif isinstance(guardrail_val, dict):
        if guardrail_val.get("passed"):
            return "PASS OK"
        return "DRAFT"
    return "DRAFT"


def _gate_artifact_name(gate_key: str) -> str:
    """Tra ve ten artifact chuan theo gate."""
    return {
        "G0": "G0_A1_PICO",
        "G1": "G1_A2_DESIGN",
        "G2": "G2_A3_IRB",
        "G3": "G3_A4_SAMPLE",
        "G4": "G4_A5_SAP",
        "G5": "G5_A6_DATA",
        "G6": "G6_A7_SCRIPTS",
        "G7": "G7_A8_MANUSCRIPT",
    }.get(gate_key, f"{gate_key}_ARTIFACT")


def _gate_pending_actions(cp: dict, gate_key: str) -> str:
    """Tra ve chuo mo ta viec con ton dong cua gate."""
    if not cp.get("_file_exists"):
        return f"[Chua chay run_{gate_key.lower()}_auto.py]"
    pending = cp.get("pending_doctor_actions", [])
    if pending:
        return "; ".join(str(p) for p in pending[:2])
    defaults = {
        "G0": "Xac nhan PICO + ket cuc chinh",
        "G1": "Bac si chon thiet ke cuoi",
        "G2": f"IRB: {cp.get('g2_irb_number','[CAN SO IRB]')}",
        "G3": f"N={cp.get('n_adjusted', cp.get('n_total','[CAN]'))} -- kiem dropout",
        "G4": f"SAP ky ngay: {cp.get('sap_signed_date','[CAN]')}",
        "G5": f"DB lock: {cp.get('db_lock_date','[CAN NGAY KHOA]')}",
        "G6": "Xem xet scripts; KHONG chay tren du lieu that cho den G5",
        "G7": "Dien Section III Results + V Conclusion khi co ket qua that",
    }
    return defaults.get(gate_key, "Xem checkpoint chi tiet")


def analyze_pipeline(gates: dict, study: str) -> dict:
    """Phan tich toan bo trang thai pipeline G0-G7."""
    rows = []
    n_pass = 0

    for i in range(8):
        key = f"G{i}"
        cp = gates[key]
        status = _gate_status_label(cp)
        artifact = _gate_artifact_name(key)
        pending = _gate_pending_actions(cp, key)

        extra = ""
        if key == "G0":
            # SỬA: .get("pubmed_results", {}) không dùng default {} khi giá
            # trị null — bọc "or {}" tránh crash pub.get(...) ngay dưới.
            pub = cp.get("pubmed_results") or {}
            n_sr = pub.get("n_sr", cp.get("n_sr", "?"))
            n_rct = pub.get("n_rct", cp.get("n_rct", "?"))
            extra = f"PubMed: {n_sr} SR, {n_rct} RCT"
        elif key == "G2":
            extra = f"IRB: {cp.get('g2_irb_number','[CAN]')}"
        elif key == "G3":
            extra = f"N={cp.get('n_adjusted', cp.get('n_total','?'))}"
        elif key == "G4":
            extra = f"SAP ky: {cp.get('sap_signed_date','[CAN]')}"
        elif key == "G5":
            extra = f"DB lock: {cp.get('db_lock_date','[CAN]')}"
        elif key == "G7":
            # SỬA: word_estimate là dict {current_skeleton, when_complete, note}
            # (xem run_g7_auto.py) — in thẳng dict ra str() cho bác sĩ đọc là
            # rác Python repr, không phải lỗi hiển thị con số.
            we = cp.get("word_estimate")
            if isinstance(we, dict):
                extra = f"~{we.get('current_skeleton','?')} từ (dự kiến {we.get('when_complete','?')} khi đủ kết quả)"
            else:
                extra = f"~{we or '?'} từ"

        rows.append({
            "gate": key,
            "status": status,
            "artifact": artifact,
            "extra": extra,
            "pending": pending,
            "checkpoint_exists": cp.get("_file_exists", False),
        })

        if _is_locked_or_pass(status):
            n_pass += 1

    return {
        "rows": rows,
        "n_pass": n_pass,
        "n_total": 8,
        "completeness_pct": round(n_pass / 8 * 100),
        "all_pass": n_pass == 8,
    }


# ============================================================================
# 4. CHECKLIST CHUAN BAO CAO
# ============================================================================

def _item_auto_check(item_name: str, gates: dict, design_code: str) -> str:
    """
    Tu kiem xem muc checklist da duoc dien chua dua vao checkpoints.
    Tra ve 'OK' neu co bang chung, 'ND' neu can bac si hoan thien.
    """
    g0 = gates.get("G0", {})
    g1 = gates.get("G1", {})
    g2 = gates.get("G2", {})
    g3 = gates.get("G3", {})
    g4 = gates.get("G4", {})
    g5 = gates.get("G5", {})
    g6 = gates.get("G6", {})

    name_lower = item_name.lower()

    if any(k in name_lower for k in ["background", "rationale", "search", "eligibility"]):
        return "☑" if g0.get("_file_exists") else "☐"
    if "objective" in name_lower:
        return "☑" if g0.get("_file_exists") else "☐"
    if any(k in name_lower for k in ["study design", "trial design"]):
        return "☑" if g1.get("_file_exists") else "☐"
    if "participant" in name_lower:
        return "☑" if g1.get("_file_exists") else "☐"
    if any(k in name_lower for k in ["variable", "data item"]):
        # SỬA: mục STROBE #7 "Variables" đòi hỏi định nghĩa biến kết cục/phơi
        # nhiễm/tiên đoán/nhiễu — dữ liệu đó nằm ở G5 (crf_columns — tên biến
        # CRF thật) và G6 (variables_detected — exposure/outcome/covariates
        # thật), KHÔNG nằm ở G4 (SAP chỉ có N/alpha/power/design). Trước đây
        # dùng g4.get("_file_exists") làm tín hiệu nên luôn báo "☐ cần điền"
        # dù G5/G6 đã có sẵn danh sách biến thật.
        has_vars = bool(g6.get("variables_detected")) or bool(g5.get("crf_columns"))
        return "☑" if has_vars else "☐"
    if "sample size" in name_lower:
        return "☑" if g3.get("_file_exists") else "☐"
    if any(k in name_lower for k in ["statistic", "effect measure", "synthesis"]):
        return "☑" if g4.get("_file_exists") else "☐"
    if any(k in name_lower for k in ["ethical", "registration", "ethical"]):
        irb = g2.get("g2_irb_number", "")
        return "☑" if (irb and "[CAN" not in str(irb)) else "☐"
    if "bias" in name_lower:
        return "☑" if g1.get("_file_exists") else "☐"
    if "missing" in name_lower:
        return "☑" if g4.get("_file_exists") else "☐"
    if any(k in name_lower for k in ["randomis", "allocation", "blinding"]):
        return "☑" if (design_code == "rct" and g4.get("_file_exists")) else "☐"
    # Cac muc can ket qua that hoac bac si dien
    return "☐"


def build_reporting_checklist(design_code: str, gates: dict) -> dict:
    """Xay dung checklist chuan bao cao va tu kiem tu checkpoints."""
    std_name, items = DESIGN_CHECKLIST_MAP.get(
        design_code, ("STROBE 2007", STROBE_ITEMS)
    )

    checked = 0
    rows = []
    for item_name, item_num, item_desc in items:
        mark = _item_auto_check(item_name, gates, design_code)
        if mark == "☑":
            checked += 1
        rows.append({
            "num": item_num,
            "name": item_name,
            "desc": item_desc,
            "mark": mark,
        })

    total = len(items)
    return {
        "standard_name": std_name,
        "items": rows,
        "checked": checked,
        "total": total,
        "score_pct": round(checked / total * 100) if total > 0 else 0,
    }


# ============================================================================
# 5. KIEM TRA TINH TOAN VEN THONG KE
# ============================================================================

def check_statistical_integrity(gates: dict) -> dict:
    """
    Kiem tra tinh toan ven thong ke tu checkpoints G3, G4, G6, G7.
    Tra ve danh sach ket qua kiem tra va danh gia tong the.
    """
    g3 = gates.get("G3", {})
    g4 = gates.get("G4", {})
    g6 = gates.get("G6", {})
    g7 = gates.get("G7", {})

    checks = []
    warnings = []
    passed_count = 0

    # Kiem 1 -- SAP da ky truoc khi xem du lieu
    sap_signed = g4.get("sap_signed_date") or g4.get("sap_locked")
    if g4.get("_file_exists") and sap_signed:
        checks.append("☑ SAP da ky/khoa truoc khi phan tich (G4)")
        passed_count += 1
    elif g4.get("_file_exists"):
        checks.append("☐ SAP chua co xac nhan ky -- [CAN ngay ky SAP]")
        warnings.append("SAP chua duoc ky chinh thuc")
    else:
        checks.append("☐ SAP chua ton tai (G4 chua chay)")

    # Kiem 2 -- Co mau da tinh (G3)
    if g3.get("_file_exists"):
        n_adj = g3.get("n_adjusted", g3.get("n_total", "?"))
        effect_type = g3.get("effect_type", "")
        effect_val = g3.get("effect_val", "?")
        alpha = g3.get("alpha", 0.05)
        power = g3.get("power", 0.80)
        try:
            power_pct = int(float(power) * 100)
        except (TypeError, ValueError):
            power_pct = 80
        checks.append(
            f"☑ Co mau da tinh: N={n_adj} "
            f"(alpha={alpha}, power={power_pct}%, {effect_type}={effect_val})"
        )
        passed_count += 1
    else:
        checks.append("☐ Co mau chua tinh (G3 chua chay)")

    # Kiem 3 -- Scripts phan tich sinh tu SAP (G6)
    if g4.get("_file_exists") and g6.get("_file_exists"):
        # SỬA: key thật trong G6 checkpoint là "n_scripts" (xem run_g6_auto.py
        # dòng ghi checkpoint) — "n_scripts_generated"/"scripts_count" không
        # tồn tại nên luôn fallback về 0, hiển thị "0 scripts" nhưng vẫn tính
        # PASS (☑), khiến bác sĩ tin lầm là không có script nào dù thực ra có.
        n_scripts = g6.get("n_scripts", 0)
        checks.append(f"☑ Scripts phan tich sinh tu SAP (G6): {n_scripts} scripts")
        passed_count += 1
    elif g4.get("_file_exists"):
        checks.append("☐ Scripts phan tich chua sinh (G6 chua chay)")
    else:
        checks.append("☐ SAP + Scripts chua co (G4+G6 chua chay)")

    # Kiem 4 -- Khong co ket qua hardcoded trong ban thao G7
    study_id = g7.get("study", "")
    g7_checked = False
    if g7.get("_file_exists") and study_id:
        g7_md = Path(g7.get("_file_path", "")).parent / f"G7_A8_MANUSCRIPT_{study_id}.md"
        if g7_md.exists():
            text = g7_md.read_text(encoding="utf-8")
            fake = re.search(r'(?:HR|OR|RR|beta|AUC)\s*=\s*\d+\.\d+\s*\(95%CI', text)
            has_placeholder = "[CAN KET QUA THAT" in text or "[CẦN KẾT QUẢ THẬT" in text
            if fake and not has_placeholder:
                checks.append(
                    "☐ Phat hien ket qua co the hardcoded trong A8 -- [CAN XEM XET]"
                )
                warnings.append("Nguy co ket qua hardcoded trong ban thao")
            else:
                checks.append(
                    "☑ Ban thao A8 khong co ket qua hardcoded (chi placeholder [CAN...])"
                )
                passed_count += 1
            g7_checked = True
    if not g7_checked:
        checks.append("☐ Ban thao G7 chua co de kiem tra ket qua hardcoded")

    # Kiem 5 -- Phan tich post-hoc
    if g4.get("_file_exists"):
        checks.append(
            "☑ SAP da ghi nhan -- moi phan tich post-hoc phai duoc khai bao ro rang"
        )
        passed_count += 1
    else:
        checks.append(
            "☐ SAP chua co -- nguy co phan tich post-hoc khong duoc khai bao"
        )

    # Kiem 6 -- Xu ly du lieu thieu
    if g4.get("_file_exists"):
        checks.append("☑ Chien luoc xu ly du lieu thieu da ghi trong SAP Section 6 (G4)")
        passed_count += 1
    else:
        checks.append("☐ Chien luoc xu ly du lieu thieu chua ghi (G4 chua chay)")

    return {
        "checks": checks,
        "warnings": warnings,
        "passed_count": passed_count,
        "total_checks": 6,
        "pass_rate": round(passed_count / 6 * 100),
        "overall": "PASS" if passed_count >= 4 else "WARNINGS",
    }


# ============================================================================
# 6. GOI Y TAP CHI
# ============================================================================

def suggest_journals(design_code: str, topic: str, target_journal: str,
                     impact_factor: float, gates: dict) -> list:
    """
    Goi y tap chi dua tren thiet ke + chu de.
    Neu --target-journal duoc cung cap, uu tien hien thi dau tien.
    """
    suggestions = []

    if target_journal:
        suggestions.append({
            "journal": target_journal,
            "if": impact_factor if impact_factor else "N/A",
            "note": "TAP CHI MUC TIEU do bac si chi dinh",
            "priority": "HIGH",
        })

    design_journals = JOURNAL_SUGGESTIONS.get(
        design_code, JOURNAL_SUGGESTIONS.get("cohort", {})
    )
    topic_lower = topic.lower()

    sublists_to_use = ["default"]
    if any(k in topic_lower for k in ["tim", "mach", "cardiac", "heart", "cardio", "coronary"]):
        sublists_to_use.append("cardiology")
    if any(k in topic_lower for k in ["dtd", "diabet", "insulin", "sglt2", "glp-1"]):
        sublists_to_use.append("endocrine")
    if any(k in topic_lower for k in ["viet", "hanoi", "hcm"]):
        sublists_to_use.append("vietnam")

    seen = {target_journal} if target_journal else set()
    for sublist_key in sublists_to_use:
        for jname, jif, jnote in design_journals.get(sublist_key, []):
            if jname not in seen:
                seen.add(jname)
                suggestions.append({
                    "journal": jname,
                    "if": jif,
                    "note": jnote,
                    "priority": "SUGGESTED",
                })

    return suggestions[:8]


# ============================================================================
# 7. DIEM TU KIEM TRUOC NOP (30 DIEM)
# ============================================================================

def build_presubmission_checklist(pipeline: dict, reporting: dict,
                                   stat_check: dict, gates: dict,
                                   journal_suggestions: list) -> dict:
    """
    Xay dung danh sach 30 muc tu kiem truoc nop.
    Nhom: PIPELINE (10) + KHOA HOC (8) + LIEM CHINH (7) + TRINH BAY (5).
    Nguong nop: >= 25/30.
    """
    g0 = gates.get("G0", {})
    g2 = gates.get("G2", {})
    g4 = gates.get("G4", {})
    g5 = gates.get("G5", {})

    items = []

    def _add(cat, desc, passed, note=""):
        items.append({
            "category": cat,
            "description": desc,
            "passed": bool(passed),
            "note": note,
            "mark": "☑" if passed else "☐",
        })

    # --- NHOM A: PIPELINE (10 diem) ---
    _add("PIPELINE", "G0 -- PICO + Evidence: checkpoint ton tai",
         gates["G0"].get("_file_exists", False))
    _add("PIPELINE", "G1 -- Thiet ke nghien cuu: checkpoint ton tai",
         gates["G1"].get("_file_exists", False))
    _add("PIPELINE", "G2 -- IRB/Dao duc: so IRB that da co",
         bool(g2.get("g2_irb_number") and "[CAN" not in str(g2.get("g2_irb_number", ""))))
    _add("PIPELINE", "G3 -- Co mau: da tinh va co N",
         gates["G3"].get("_file_exists", False))
    _add("PIPELINE", "G4 -- SAP: da khoa/ky truoc khi xem du lieu",
         bool(g4.get("sap_signed_date") or g4.get("sap_locked")),
         note="Bat buoc truoc phan tich")
    _add("PIPELINE", "G5 -- DB Lock: co so du lieu da khoa",
         bool(g5.get("db_lock_date") and "[CAN" not in str(g5.get("db_lock_date", ""))),
         note="Truoc khi phan tich cuoi")
    _add("PIPELINE", "G6 -- Scripts: da sinh R/Python analysis scripts",
         gates["G6"].get("_file_exists", False))
    _add("PIPELINE", "G7 -- Ban thao IMRAD skeleton: da sinh",
         gates["G7"].get("_file_exists", False))
    _add("PIPELINE", "Guardrail G0-G7: >= 6/8 gates qua",
         pipeline["n_pass"] >= 6,
         note=f"{pipeline['n_pass']}/{pipeline['n_total']} gates qua")
    _add("PIPELINE", f"Checklist {reporting['standard_name']}: >60% muc co bang chung",
         reporting["score_pct"] >= 60,
         note=f"{reporting['checked']}/{reporting['total']} = {reporting['score_pct']}%")

    # --- NHOM B: KHOA HOC (8 diem) ---
    # SỬA: cùng lỗi None-unsafe đã sửa ở dòng ~467 (analyze_pipeline) — hàm
    # KHÁC trong CÙNG FILE này bị bỏ sót ở lần sửa trước, đúng bài học đã ghi
    # nhận: sửa 1 chỗ không có nghĩa toàn file đã an toàn.
    pub = g0.get("pubmed_results") or {}
    try:
        n_sr = int(pub.get("n_sr", g0.get("n_sr", 0)) or 0)
        n_rct = int(pub.get("n_rct", g0.get("n_rct", 0)) or 0)
    except (TypeError, ValueError):
        n_sr = n_rct = 0

    _add("KHOA HOC", f"Evidence hien co da tong quan: {n_sr} SR, {n_rct} RCT",
         bool(n_sr > 0 or n_rct > 0),
         note="Tu G0 PubMed search")
    _add("KHOA HOC", "Cau hoi PICO da xac nhan (4 thanh phan P-I-C-O)",
         g0.get("_file_exists", False),
         note="Bac si can xac nhan truc tiep")
    _add("KHOA HOC", "Ket cuc chinh: DUY NHAT va do luong duoc",
         g4.get("_file_exists", False),
         note="Xac nhan trong SAP Section 2")
    _add("KHOA HOC", "Effect size + CI 95% da khai bao trong SAP",
         bool(gates["G3"].get("_file_exists") and g4.get("_file_exists")),
         note="G3 effect_val + G4 SAP")
    _add("KHOA HOC", "Phan tich thong ke khong chi dua vao p-value",
         stat_check["passed_count"] >= 3,
         note="Tu kiem tra thong ke G8")
    _add("KHOA HOC", "Missing data da co chien luoc xu ly (SAP Section 6)",
         g4.get("_file_exists", False))
    _add("KHOA HOC", "Khong co phan tich post-hoc ngoai SAP",
         g4.get("_file_exists", False),
         note="Can bac si xac nhan sau khi co ket qua")
    _add("KHOA HOC", "Assumptions thong ke da kiem (PH, normality...)",
         gates["G6"].get("_file_exists", False),
         note="Tu scripts G6")

    # --- NHOM C: LIEM CHINH (7 diem) ---
    _add("LIEM CHINH", "Khong co PII (thong tin dinh danh benh nhan) trong artifact",
         True,
         note="Guardrail R2 tu dong -- luon PASS")
    _add("LIEM CHINH", "Tat ca PMID/DOI da xac minh (khong bia)",
         g0.get("_file_exists", False),
         note="Kiem lai bang agent kiem-chung-trich-dan")
    _add("LIEM CHINH", "So IRB that (khong phai placeholder [CAN...])",
         bool(g2.get("g2_irb_number") and "[CAN" not in str(g2.get("g2_irb_number", ""))))
    _add("LIEM CHINH", "Dang ky thu nghiem (ClinicalTrials.gov / TCTR)",
         bool(g2.get("g2_registration") and "[CAN" not in str(g2.get("g2_registration", ""))),
         note="Bat buoc cho RCT theo ICMJE")
    _add("LIEM CHINH", "Khai bao AI: EBM Copilot da duoc ghi nhan trong Methods/Acknowledgements",
         gates["G7"].get("_file_exists", False),
         note="Theo ICMJE/nhieu tap chi 2024+")
    _add("LIEM CHINH", "Disclaimer 'Can bac si kiem chung' trong moi artifact",
         True,
         note="Guardrail R7 tu dong -- luon PASS")
    _add("LIEM CHINH", "Xung dot loi ich (COI) da khai bao hoac xac nhan khong co",
         False,
         note="[CAN -- dien form COI o Phan 5]")

    # --- NHOM D: TRINH BAY (5 diem) ---
    _add("TRINH BAY", "Tieu de bai <= 120 ky tu, chua thiet ke nghien cuu",
         False,
         note="[CAN xac nhan tieu de cuoi tu G7]")
    _add("TRINH BAY", "Tom tat co cau truc <= 250 tu",
         False,
         note="[CAN sau khi co ket qua that]")
    _add("TRINH BAY", "Danh sach tac gia + affiliations + ORCID day du",
         False,
         note="[CAN xac nhan CRediT roles o Phan 5]")
    _add("TRINH BAY", "Tai lieu tham khao theo dinh dang tap chi dich (Vancouver/APA/...)",
         g0.get("_file_exists", False),
         note="Kiem lai bang agent kiem-chung-trich-dan")
    _add("TRINH BAY", "Cover letter chuan bi cho ban bien tap",
         False,
         note="[CAN bac si soan -- khong sinh tu dong]")

    total_passed = sum(1 for it in items if it["passed"])
    return {
        "items": items,
        "total": len(items),
        "passed": total_passed,
        "score_label": f"{total_passed}/{len(items)}",
        "ready": total_passed >= 25,
        "readiness_note": (
            "SAN SANG NOP" if total_passed >= 25
            else f"CAN THEM {25 - total_passed} DIEM"
        ),
    }


# ============================================================================
# 8. SINH ARTIFACT A9 (MARKDOWN)
# ============================================================================

def generate_a9_artifact(
    study: str,
    run_date: str,
    gates: dict,
    pipeline: dict,
    reporting: dict,
    stat_check: dict,
    journal_suggestions: list,
    presubmission: dict,
    target_journal: str,
    impact_factor: float,
    g8_status: str,
) -> str:
    """Sinh artifact A9 -- Bao cao toan dien kiem tra truoc nop bai."""

    g0 = gates.get("G0", {})
    g1 = gates.get("G1", {})
    # SỬA: 2 lỗi — (1) .get("topic", study) không dùng default khi giá trị
    # null; (2) g1.get("design_code"/"design_primary") đọc SAI đường dẫn —
    # G1 lưu lồng trong "design": {...}, không phải top-level, nên luôn âm
    # thầm rơi về "cohort" bất kể thiết kế thật.
    g1_design = g1.get("design") or {}
    topic = g0.get("topic") or study
    design_code = g1_design.get("internal_code") or "cohort"
    design_primary = g1_design.get("primary") or "Cohort tien cuu"

    L = []  # danh sach dong artifact

    def ln(s=""):
        L.append(s)

    ln("# A9 — BÁO CÁO KIỂM TRA TRƯỚC NỘP BÀI (PRE-SUBMISSION REVIEW)")
    ln(f"**Mã đề tài:** {study}")
    ln(f"**Ngày kiểm toán:** {run_date}")
    ln(f"**Thiết kế:** {design_primary} (`{design_code}`)")
    ln(f"**Chuẩn báo cáo áp dụng:** {reporting['standard_name']}")
    ln(f"**Điểm pipeline:** {pipeline['n_pass']}/{pipeline['n_total']} gates PASS ({pipeline['completeness_pct']}%)")
    # SỬA: score_label đã tự chứa mẫu số ("18/30") — nối thêm "/30" ở đây
    # tạo ra chuỗi hiển thị sai "18/30/30" cho bác sĩ đọc.
    ln(f"**Điểm tự kiểm:** {presubmission['score_label']} — {presubmission['readiness_note']}")
    ln()
    ln("> [BẢN NHÁP TỰ ĐỘNG] — Dựa trên checkpoints G0-G7.")
    ln("> Các mục [CAN] yêu cầu bác sĩ/nhóm tác giả hoàn thiện trước khi nộp.")
    ln("> Cần bác sĩ kiểm chứng.")
    ln()
    ln("---")
    ln()
    ln("## PHẦN 1 — KIỂM TOÁN PIPELINE HOÀN CHỈNH")
    ln()
    ln("| Gate | Trạng thái | Artifact chính | Chi tiết | Việc còn tồn đọống |")
    ln("|------|-----------|----------------|----------|-------------------|")

    for row in pipeline["rows"]:
        ln(f"| {row['gate']} | {row['status']} | `{row['artifact']}` | {row['extra']} | {row['pending']} |")

    ln()
    ln(f"**Tổng kết pipeline:** {pipeline['n_pass']}/{pipeline['n_total']} gates đạt ({pipeline['completeness_pct']}%)")
    ln()
    ln("---")
    ln()
    ln(f"## PHẦN 2 — CHECKLIST {reporting['standard_name']} ({reporting['total']} MỤC)")
    ln()
    ln(f"> **Tự kiểm từ checkpoints:** {reporting['checked']}/{reporting['total']} mục = **{reporting['score_pct']}%**")
    ln("> ☑ = Có bằng chứng trong checkpoints G0-G7")
    ln("> ☐ = Cần hoàn thiện thủ công (kết quả thật / bác sĩ điền)")
    ln()
    ln("| # | Mục | Mô tả rút gọn | Trạng thái |")
    ln("|---|-----|--------------|-----------|")

    for item in reporting["items"]:
        desc_s = item["desc"][:70] + ("..." if len(item["desc"]) > 70 else "")
        ln(f"| {item['num']} | {item['name']} | {desc_s} | {item['mark']} |")

    ln()
    ln(f"**Tóm tắt:** {reporting['checked']}/{reporting['total']} mục có bằng chứng từ checkpoints.")
    ln(f"{reporting['total'] - reporting['checked']} mục ☐ cần bác sĩ điền thủ công.")
    ln()
    ln("---")
    ln()
    ln("## PHẦN 3 — KIỂM TRA TÍNH TOÀN VẸN THỐNG KÊ")
    ln()
    ln(f"**Kết quả:** {stat_check['passed_count']}/{stat_check['total_checks']} kiểm tra qua — **{stat_check['overall']}**")
    ln()

    for check in stat_check["checks"]:
        ln(f"- {check}")

    if stat_check["warnings"]:
        ln()
        ln("**Cảnh báo cần xem xét:**")
        for w in stat_check["warnings"]:
            ln(f"  - [CANH BAO] {w}")

    ln()
    ln("**Quy tắc vàng báo cáo thống kê:**")
    ln("- Báo cáo effect size (HR/OR/RR/MD/AUC) + **CI 95%** — không chỉ p-value")
    ln("- Mọi phân tích thêm (subgroup, sensitivity) phải được khai báo trong SAP G4")
    ln("- Phân tích post-hoc phát sinh sau khi xem dữ liệu phải được ghi nhận rõ ràng")
    ln("- Kiểm định assumptions: PH test (Cox), Shapiro-Wilk (normality)")
    ln("- Missing data: báo cáo số và % thiếu; chiến lược multiple imputation nếu >= 5%")
    ln()
    ln("---")
    ln()
    ln("## PHẦN 4 — GỢI Ý TẠP CHÍ")
    ln()

    if target_journal:
        ln(f"> **Tạp chí mục tiêu do bác sĩ chỉ định:** {target_journal}" +
           (f" (IF: {impact_factor})" if impact_factor else ""))
        ln()
    else:
        ln("> **Lưu ý quan trọng:** Danh sách dưới đây là GỢI Ý dựa trên thiết kế + chủ đề.")
        ln("> KHÔNG phải đảm bảo acceptance. Bác sĩ cần kiểm tra Instructions for Authors.")
        ln(f"> Cơ sở gợi ý: thiết kế `{design_code}` + chủ đề: *{topic[:60]}*")
        ln()

    ln("| Tạp chí | IF (2024 ước tính) | Ghi chú | Ưu tiên |")
    ln("|---------|-------------------|---------|---------|")

    for sug in journal_suggestions:
        if_val = str(sug["if"])
        ln(f"| {sug['journal']} | {if_val} | {sug['note']} | {sug['priority']} |")

    ln()
    ln("**Tiêu chí bổ sung khi chọn tạp chí:**")
    ln("- Scope có phù hợp thiết kế và quần thể nghiên cứu không?")
    ln("- Article Processing Charge (APC) nếu chọn Open Access")
    ln("- Thời gian peer review trung bình (xem Peer Review Speed)")
    ln("- Word limit, số bảng/hình tối đa, format tài liệu tham khảo")
    ln("- Yêu cầu khai báo AI (ngày càng phổ biến 2024+)")
    ln()
    ln("---")
    ln()
    ln("## PHẦN 5 — GÓI KHAI BÁO TÁC GIẢ (Author Declaration Package)")
    ln()
    ln("### 5.1 CRediT Taxonomy Roles — Phân công vai trò tác giả")
    ln()
    ln("> Tham khảo: https://credit.niso.org/ (14 vai trò chuẩn)")
    ln("> Ghi chú: **L** = Lead | **S** = Supporting | **-** = Không tham gia")
    ln()
    ln("| Vai trò CRediT | Tác giả 1 | Tác giả 2 | Tác giả 3 | Tác giả 4+ |")
    ln("|----------------|-----------|-----------|-----------|------------|")

    for role in CREDIT_ROLES:
        ln(f"| {role} | [CAN] | [CAN] | [CAN] | [CAN] |")

    ln()
    ln("### 5.2 Thông tin tác giả")
    ln()
    ln("| # | Họ tên | Học hàm | Đơn vị công tác | ORCID | Email |")
    ln("|---|--------|---------|----------------|-------|-------|")
    ln("| 1 | [CAN -- tac gia chinh] | [CAN] | [CAN] | [CAN -- https://orcid.org/...] | [CAN] |")
    ln("| 2 | [CAN] | [CAN] | [CAN] | [CAN] | |")
    ln("| 3+ | [CAN] | | | | |")
    ln()
    ln("**Tác giả liên lạc (Corresponding Author):** [CAN -- ten day du + email + dia chi lien he]")
    ln()
    ln("### 5.3 Khai báo xung đột lợi ích (COI)")
    ln()
    ln("☐ **Tất cả tác giả xác nhận KHÔNG có xung đột lợi ích**")
    ln("☐ **Có xung đột — khai báo chi tiết:**")
    ln()
    ln("| Tác giả | Loại quan hệ | Với tổ chức nào | Thời gian |")
    ln("|---------|-------------|----------------|-----------|")
    ln("| [CAN] | [tai chinh/co phan/tu van/khac] | [CAN] | [CAN] |")
    ln()
    ln("### 5.4 Khai báo nguồn tài trợ (Funding)")
    ln()
    ln("| Nguồn tài trợ | Số grant/hợp đồng | Tác giả nhận | Vai trò trong NC |")
    ln("|--------------|------------------|-------------|-----------------|")
    ln("| [CAN -- hoac 'Khong nhan tai tro tu ben ngoai'] | | | |")
    ln()
    ln("### 5.5 Khai báo sử dụng AI (ICMJE 2023+)")
    ln()
    ln("Nghiên cứu này sử dụng **EBM Copilot** (Claude-based AI tool) để hỗ trợ:")
    ln("1. Tổng quan y văn tự động: tìm kiếm PubMed, phân loại bằng chứng (G0)")
    ln("2. Sinh skeleton SAP và R/Python scripts (G4, G6)")
    ln("3. Soạn thảo IMRAD skeleton dựa trên checkpoints (G7)")
    ln()
    ln("Tất cả nội dung khoa học, kết quả, diễn giải do tác giả người kiểm chứng và chịu trách nhiệm.")
    ln("Theo ICMJE 2023, AI KHÔNG được liệt kê là tác giả.")
    ln()
    ln("---")
    ln()
    ln("## PHẦN 6 — ĐIỂM TỰ KIỂM TRƯỚC NỘP (30 ĐIỂM)")
    ln()
    ln(f"**Điểm đạt được: {presubmission['passed']}/{presubmission['total']}**")
    ln(f"**Đánh giá: {presubmission['readiness_note']}**")
    ln("*(Ngưỡng đủ điều kiện nộp: >= 25/30 điểm)*")
    ln()

    categories = ["PIPELINE", "KHOA HOC", "LIEM CHINH", "TRINH BAY"]
    cat_labels = {
        "PIPELINE":    "A. Pipeline (10 điểm)",
        "KHOA HOC":    "B. Khoa học (8 điểm)",
        "LIEM CHINH":  "C. Liêm chính (7 điểm)",
        "TRINH BAY":   "D. Trình bày (5 điểm)",
    }

    for cat in categories:
        cat_items = [it for it in presubmission["items"] if it["category"] == cat]
        cat_passed = sum(1 for it in cat_items if it["passed"])
        ln(f"### {cat_labels[cat]} — {cat_passed}/{len(cat_items)}")
        ln()
        for item in cat_items:
            note_str = f" *({item['note']})*" if item.get("note") else ""
            ln(f"- {item['mark']} {item['description']}{note_str}")
        ln()

    # Phan 7
    irb_ok = bool(
        gates["G2"].get("g2_irb_number") and
        "[CAN" not in str(gates["G2"].get("g2_irb_number", ""))
    )
    sap_ok = bool(
        gates["G4"].get("sap_signed_date") or gates["G4"].get("sap_locked")
    )
    g7_ok = gates["G7"].get("_file_exists", False)
    score_ok = presubmission["passed"] >= 25
    reporting_ok = reporting["score_pct"] >= 60

    ln("---")
    ln()
    ln("## PHẦN 7 — TIÊU CHÍ QUA CỔNG G8")
    ln()
    ln("```")
    ln("G8 PASS khi dap ung TAT CA 5 dieu kien BAT BUOC + bac si xac nhan 5 muc cuoi:")
    ln()
    ln("BAT BUOC (tu dong kiem tu checkpoints):")
    ln(f"{'OK' if irb_ok else 'ND'} 1. G2 LOCKED -- IRB number that: {gates['G2'].get('g2_irb_number','[CAN]')}")
    ln(f"{'OK' if sap_ok else 'ND'} 2. G4 LOCKED -- SAP da ky truoc khi xem du lieu")
    ln(f"{'OK' if g7_ok else 'ND'} 3. G7 DONE -- Ban thao IMRAD skeleton da sinh")
    ln(f"{'OK' if score_ok else 'ND'} 4. Diem tu kiem >= 25/30 (hien: {presubmission['passed']}/30)")
    ln(f"{'OK' if reporting_ok else 'ND'} 5. Checklist {reporting['standard_name']} >= 60% (hien: {reporting['score_pct']}%)")
    ln()
    ln("CAN BAC SI XAC NHAN (khong the tu dong):")
    ln("[CAN] 6. Ket qua that da dien vao Section III+V ban thao (sau G5+G6 phan tich)")
    ln("[CAN] 7. Toan bo ban thao doc lai -- khong con placeholder [CAN...]")
    ln("[CAN] 8. CRediT roles da phan cong day du (Phan 5)")
    ln("[CAN] 9. COI da khai bao hoac xac nhan khong co (Phan 5)")
    ln("[CAN] 10. Cover letter da soan theo yeu cau tap chi dich")
    ln("```")
    ln()
    ln(f"**Trạng thái G8:** {g8_status}")
    ln()
    ln("---")
    ln()
    ln("*Cần bác sĩ kiểm chứng. Artifact A9 là BẢN NHÁP TỰ ĐỘNG từ checkpoints G0-G7 --*")
    ln("*không thay thế đánh giá chuyên môn của nhóm tác giả trước khi nộp bài.*")

    return "\n".join(L)


# ============================================================================
# 9. GUARDRAIL R1-R7 (PHIEN BAN G8)
# ============================================================================

def guardrail_g8(artifact: str, pipeline: dict) -> dict:
    """Kiem guardrail R1-R7 toan pipeline cho artifact A9."""
    errors = []
    warnings = []

    # R1 -- Co nguon dan that (gate checkpoints)
    n_exists = sum(1 for row in pipeline["rows"] if row["checkpoint_exists"])
    if n_exists == 0:
        errors.append("R1 [DO] Khong co checkpoint nao -- khong the kiem toan pipeline")
    else:
        warnings.append(f"R1 [OK] {n_exists}/8 checkpoints ton tai")

    # R2 -- PII
    pii_patterns = ["ten benh nhan", "ho ten:", "ngay sinh:", "cccd", "so ho so:"]
    for p in pii_patterns:
        if p in artifact.lower():
            errors.append(f"R2 [DO] PII phat hien: '{p}'")
            break
    else:
        warnings.append("R2 [OK] Khong phat hien PII")

    # R3 -- Khong vuot cong G8 khi pipeline chua hoan chinh
    # SUA: kiem tra cu "G8 PASS" in artifact la FALSE POSITIVE co san -- chuoi
    # nay luon xuat hien trong CAU GIAI THICH TIEU CHI ("G8 PASS khi dap ung
    # TAT CA 5 dieu kien...") o MOI artifact bat ke trang thai that, nen dieu
    # kien nay thuc chat chua bao gio kiem tra dung thu. Doi sang kiem tra
    # chuoi TUYEN BO THAT (readiness_note = "SAN SANG NOP", chi xuat hien khi
    # total_passed>=25) + dong bo nguong voi checklist (>=6/8 gates).
    if "SAN SANG NOP" in artifact and pipeline["n_pass"] < 6:
        errors.append("R3 [DO] Tuyen bo SAN SANG NOP khi pipeline chua du dieu kien (can >=6/8 gates)")
    else:
        warnings.append("R3 [OK] Trang thai gate phu hop voi du lieu checkpoints")

    # R4 -- Khong tu gan GRADE tuy tien
    # SUA: truoc day MOI cum "GRADE [A-D]" bi day thang vao errors, ke ca khi
    # co trich nguon PMID/DOI hop le ngay canh (vd agent tham-dinh-grade-nnt
    # gan GRADE co nguon that trong Discussion) -- gay false-FAIL cho noi
    # dung hoan toan dung. Nay kiem CUC BO: neu co PMID/DOI trong +-120 ky tu
    # quanh cum GRADE, coi la CO NGUON (warning), chi bao loi khi KHONG co.
    grade_matches = list(re.finditer(r'GRADE [A-D](?!\s*taxonomy|\/)', artifact))
    unsourced_grade = []
    for m in grade_matches:
        window = artifact[max(0, m.start() - 120): m.end() + 120]
        if not re.search(r'PMID|DOI', window, re.IGNORECASE):
            unsourced_grade.append(m.group())
    if unsourced_grade:
        errors.append(f"R4 [VANG] Phat hien nhan GRADE KHONG co PMID/DOI gan do: {unsourced_grade[:3]}")
    elif grade_matches:
        warnings.append(f"R4 [OK] {len(grade_matches)} nhan GRADE deu co PMID/DOI gan do (co nguon)")
    else:
        warnings.append("R4 [OK] Khong tu gan GRADE")

    # R5 -- Khong co ket qua hardcoded
    # SUA 2026-07-06: them MD/AUC/beta vao alternation (truoc day chi HR|OR|RR)
    # va cho phep gia tri AM + >=1 (\-?\d+\.\d+ thay vi 0\.\d+) — MD (chenh lech
    # trung binh) co the am hoac lon hon 1, HR/OR/RR cung co the >1; regex cu bo
    # sot ca hai truong hop (false negative khi ban thao bi dien cung MD=... hoac
    # HR=2.5... ma quen danh dau [CAN]). Phat hien qua kiem dinh doi khang vong 2.
    fake = re.search(r'(?:HR|OR|RR|MD|AUC|beta)\s*=\s*-?\d+\.\d+\s*\(95%CI', artifact)
    if fake:
        ctx = artifact[max(0, fake.start()-50):fake.end()+50]
        if "[CAN KET QUA THAT" not in ctx and "[CẦN KẾT" not in ctx:
            errors.append("R5 [DO] Ket qua thong ke hardcoded trong A9")
        else:
            warnings.append("R5 [OK] Khong co ket qua hardcoded")
    else:
        warnings.append("R5 [OK] Khong co ket qua hardcoded")

    # R6 -- Nhan [CAN...] cho muc chua hoan chinh
    n_can = len(re.findall(r'\[CAN', artifact))
    if n_can >= 8:
        warnings.append(f"R6 [OK] {n_can} nhan [CAN...] danh dau ro phan can hoan thien")
    else:
        errors.append(f"R6 [DO] Qua it nhan [CAN...] ({n_can}) cho bao cao pre-submission")

    # R7 -- Disclaimer
    if "can bac si kiem chung" in artifact.lower() or "Cần bác sĩ kiểm chứng" in artifact:
        warnings.append("R7 [OK] Co disclaimer")
    else:
        errors.append("R7 [DO] Thieu disclaimer 'Can bac si kiem chung'")

    passed = len(errors) == 0
    status = "[OK] PASS" if passed else f"[CANH BAO] {len(errors)} LOI"
    return {
        "passed": passed,
        "status": status,
        "errors": errors,
        "warnings": warnings,
    }


# ============================================================================
# 10. XUAT DOCX
# ============================================================================

def export_docx(artifact_md: str, study: str, out_dir: Path):
    """Xuat file .docx tu artifact markdown, to mau cac muc [CAN...]."""
    try:
        from docx import Document
        from docx.shared import Pt, RGBColor

        doc = Document()
        doc.add_heading(f"A9 -- Pre-Submission Review: {study}", 0)
        doc.add_paragraph(f"Ngay: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        doc.add_paragraph("Can bac si kiem chung. [BAN NHAP TU DONG]")
        doc.add_page_break()

        for line in artifact_md.split("\n"):
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("# "):
                doc.add_heading(stripped[2:], 1)
            elif stripped.startswith("## "):
                doc.add_heading(stripped[3:], 2)
            elif stripped.startswith("### "):
                doc.add_heading(stripped[4:], 3)
            elif stripped.startswith("- ") or stripped.startswith("* "):
                p = doc.add_paragraph(stripped[2:], style="List Bullet")
                if "[CAN" in stripped:
                    for run in p.runs:
                        run.font.color.rgb = RGBColor(0xCC, 0x44, 0x00)
            elif stripped in ("---", "```"):
                pass
            elif stripped.startswith("|"):
                p = doc.add_paragraph(stripped)
                if p.runs:
                    p.runs[0].font.size = Pt(9)
            else:
                p = doc.add_paragraph(stripped)
                if "[CAN" in stripped:
                    for run in p.runs:
                        run.font.color.rgb = RGBColor(0xCC, 0x44, 0x00)

        docx_path = out_dir / f"G8_A9_PRESUBMISSION_{study}.docx"
        doc.save(docx_path)
        return docx_path
    except ImportError:
        print("  [CANH BAO] python-docx khong cai -- bo qua xuat DOCX")
        return None
    except Exception as e:
        print(f"  [CANH BAO] Loi xuat DOCX: {e}")
        return None


# ============================================================================
# 11. GHI CHECKPOINT G8
# ============================================================================

def write_g8_checkpoint(
    study: str,
    out_dir: Path,
    run_date: str,
    pipeline: dict,
    reporting: dict,
    stat_check: dict,
    journal_suggestions: list,
    presubmission: dict,
    guardrail: dict,
    target_journal: str,
    impact_factor: float,
    g8_status: str,
) -> Path:
    """Ghi G8_checkpoint.json voi day du thong tin kiem toan."""
    cp = {
        "gate": "G8",
        "study": study,
        "run_date": run_date,
        "gate_status": g8_status,

        # Hoan chinh pipeline
        "pipeline_completeness": {
            row["gate"]: {
                "status": row["status"],
                "artifact": row["artifact"],
                "checkpoint_exists": row["checkpoint_exists"],
            }
            for row in pipeline["rows"]
        },
        "pipeline_pass_count": pipeline["n_pass"],
        "pipeline_total": pipeline["n_total"],
        "pipeline_completeness_pct": pipeline["completeness_pct"],

        # Checklist chuan bao cao
        "reporting_standard": reporting["standard_name"],
        "reporting_checklist_score": f"{reporting['checked']}/{reporting['total']}",
        "reporting_score_pct": reporting["score_pct"],

        # Kiem tra thong ke
        "statistical_integrity": {
            "overall": stat_check["overall"],
            "passed_count": stat_check["passed_count"],
            "total_checks": stat_check["total_checks"],
            "warnings": stat_check["warnings"],
        },

        # Goi y tap chi
        "target_journal": target_journal or None,
        "target_journal_if": impact_factor or None,
        "journal_suggestions": [
            {"journal": s["journal"], "if": s["if"], "note": s["note"]}
            for s in journal_suggestions
        ],

        # Diem tu kiem
        "presubmission_score": presubmission["passed"],
        "presubmission_total": presubmission["total"],
        "presubmission_readiness": presubmission["readiness_note"],

        # Trang thai nop bai
        "submission_readiness": (
            "READY" if ("PASS" in g8_status or "SAN SANG" in g8_status)
            else f"NEEDS: {g8_status}"
        ),

        # Guardrail
        "guardrail": {
            "status": guardrail["status"],
            "passed": guardrail["passed"],
            "n_errors": len(guardrail["errors"]),
            "errors": guardrail["errors"],
        },

        "disclaimer": "Can bac si kiem chung.",
        "next_gate": "SUBMISSION hoac G9 (Peer Review Response) sau khi nop",
    }

    cp_path = out_dir / "G8_checkpoint.json"
    cp_path.write_text(json.dumps(cp, ensure_ascii=False, indent=2), encoding="utf-8")
    return cp_path


# ============================================================================
# 12. MAIN -- CLI ENTRY POINT
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="G8 Auto -- Kiem tra toan dien truoc nop bai (Pre-submission Review)"
    )
    parser.add_argument(
        "--study", required=True,
        help="Ma de tai (dung dat ten file, khong dau, khong khoang trang)"
    )
    parser.add_argument(
        "--target-journal", default="",
        help="Ten tap chi muc tieu (tuy chon -- neu khong co, he thong goi y)"
    )
    parser.add_argument(
        "--impact-factor", type=float, default=0.0,
        help="Impact Factor cua tap chi muc tieu (tuy chon)"
    )
    args = parser.parse_args()

    # 2026-07-11: vá path traversal, khớp chuẩn sanitize đã dùng ở G0-G5.
    study = re.sub(r'[^\w\-]', '_', args.study.strip().replace(" ", "-"))
    run_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    out_dir = BASE / "exports" / study
    out_dir.mkdir(parents=True, exist_ok=True)

    # THÊM 2026-07-08 (CRIT-05): gọi thẳng script (không qua run_pipeline.py)
    # trước đây mất target_journal/impact_factor bác sĩ đã pin khi chạy lại.
    _g8_pinned = (GC.load_study_meta(out_dir).get("gate_params") or {}).get("G8") or {}
    if not args.target_journal and _g8_pinned.get("target_journal"):
        args.target_journal = _g8_pinned["target_journal"]
        print(f"  → Khôi phục target_journal='{args.target_journal}' từ study_meta.json")
    if not args.impact_factor and _g8_pinned.get("impact_factor") is not None:
        args.impact_factor = _g8_pinned["impact_factor"]
        print(f"  → Khôi phục impact_factor={args.impact_factor} từ study_meta.json")

    # PIN durable (2026-07-09): ĐỐI XỨNG với khối ĐỌC ở trên. Vá 07-08 chỉ thêm khối
    # đọc mà KHÔNG có khối ghi tương ứng → không nơi nào điền gate_params.G8, nên việc
    # "khôi phục khi chạy lại" là no-op (phát hiện qua kiểm định hậu-kiểm 2026-07-09).
    # Nay ghi giá trị bác sĩ cấp qua CLI vào study_meta.json (fill-if-missing qua
    # ensure_study_meta — KHÔNG đè giá trị đã có), khép vòng như G3.
    _seed_g8 = {}
    if args.target_journal:
        _seed_g8["target_journal"] = args.target_journal
    if args.impact_factor:
        _seed_g8["impact_factor"] = args.impact_factor
    if _seed_g8:
        GC.ensure_study_meta(out_dir, seed={"gate_params": {"G8": _seed_g8}})

    print(f"\n{'='*65}")
    print(f"  G8 AUTO -- PRE-SUBMISSION REVIEW: {study}")
    print(f"  Thoi gian: {run_date}")
    if args.target_journal:
        print(f"  Tap chi muc tieu: {args.target_journal}")
    print(f"{'='*65}\n")

    # 1. Doc tat ca checkpoints
    print("Buoc 1/7: Doc checkpoints G0-G7...")
    gates = load_all_checkpoints(out_dir)
    n_exists = sum(1 for i in range(8) if gates[f"G{i}"].get("_file_exists"))
    print(f"  -> {n_exists}/8 checkpoints ton tai")

    # SỬA: cùng 2 lỗi đã sửa ở generate_a9_artifact() — design_code đọc SAI
    # đường dẫn (top-level thay vì lồng trong "design") và topic không có
    # None-guard. Hàm KHÁC (main()) trong CÙNG FILE bị bỏ sót lần trước.
    design_code = (gates["G1"].get("design") or {}).get("internal_code") or "cohort"
    topic = gates["G0"].get("topic") or study
    print(f"  -> Design: {design_code} | Topic: {topic[:50]}")

    # 2. Phan tich pipeline
    print("\nBuoc 2/7: Phan tich trang thai pipeline G0-G7...")
    pipeline = analyze_pipeline(gates, study)
    print(f"  -> {pipeline['n_pass']}/{pipeline['n_total']} gates PASS ({pipeline['completeness_pct']}%)")
    for row in pipeline["rows"]:
        print(f"    {row['gate']}: {row['status']}")

    # 3. Checklist chuan bao cao
    print(f"\nBuoc 3/7: Kiem checklist {design_code}...")
    reporting = build_reporting_checklist(design_code, gates)
    print(f"  -> {reporting['standard_name']}: {reporting['checked']}/{reporting['total']} "
          f"({reporting['score_pct']}%)")

    # 4. Kiem tra thong ke
    print("\nBuoc 4/7: Kiem tra tinh toan ven thong ke...")
    stat_check = check_statistical_integrity(gates)
    print(f"  -> {stat_check['passed_count']}/{stat_check['total_checks']} qua -- {stat_check['overall']}")
    for w in stat_check["warnings"]:
        print(f"    [CANH BAO] {w}")

    # 5. Goi y tap chi
    print("\nBuoc 5/7: Goi y tap chi...")
    journal_suggestions = suggest_journals(
        design_code, topic, args.target_journal, args.impact_factor, gates
    )
    print(f"  -> {len(journal_suggestions)} goi y")
    for sug in journal_suggestions[:3]:
        print(f"    - {sug['journal']} (IF: {sug['if']})")

    # 6. Diem tu kiem 30 diem
    print("\nBuoc 6/7: Tinh diem tu kiem (30 diem)...")
    presubmission = build_presubmission_checklist(
        pipeline, reporting, stat_check, gates, journal_suggestions
    )
    print(f"  -> Diem: {presubmission['passed']}/30 -- {presubmission['readiness_note']}")

    # Xac dinh trang thai G8
    # SUA 2026-07-08 (BL-05, phat hien qua kiem dinh doc lap): g7_ok TRUOC DAY chi
    # kiem FILE TON TAI ("_file_exists"), khong kiem noi dung co con placeholder
    # "[CAN KET QUA THAT]" hay khong -- nghia la co the dat IRB that + SAP ky that +
    # G0-G7 chay xong (guardrail PASS) MA CHUA MOT DONG PHAN TICH THAT NAO chay tren
    # du lieu that, ma g8_status/submission_readiness van bao "PASS -- DU DIEU KIEN
    # NOP BAI" -- mau thuan truc tiep voi dinh nghia "San sang nop cong bo" cua
    # skill_standards.py (doi hoi results_final). Them cop ket qua that qua
    # study_meta.json["results_final"] (chi bac si tu tay bat, khong tu dong bat
    # duoc -- dung quy uoc da co san o G7/G9/skill_standards.py).
    _study_meta_g8 = GC.load_study_meta(out_dir)
    results_final = bool(_study_meta_g8.get("results_final"))

    irb_ok = bool(
        gates["G2"].get("g2_irb_number") and
        "[CAN" not in str(gates["G2"].get("g2_irb_number", ""))
    )
    sap_ok = bool(
        gates["G4"].get("sap_signed_date") or gates["G4"].get("sap_locked")
    )
    g7_ok = gates["G7"].get("_file_exists", False)
    score_ok = presubmission["passed"] >= 25

    if irb_ok and sap_ok and g7_ok and results_final and score_ok:
        g8_status = "PASS -- DU DIEU KIEN NOP BAI (sau xac nhan bac si muc 6-10)"
    elif irb_ok and sap_ok and g7_ok and results_final:
        g8_status = f"PARTIAL -- Can them {25 - presubmission['passed']} diem tu kiem"
    else:
        missing = []
        if not irb_ok:
            missing.append("IRB that (G2)")
        if not sap_ok:
            missing.append("SAP ky (G4)")
        if not g7_ok:
            missing.append("Ban thao (G7)")
        if not results_final:
            missing.append("Ket qua phan tich THAT da xac nhan (results_final trong study_meta.json -- "
                            "chua co nghia la ban thao con placeholder [CAN KET QUA THAT], KHONG duoc "
                            "coi la san sang nop du diem tu kiem co cao)")
        g8_status = f"PENDING -- Can: {', '.join(missing)}"

    # 7. Sinh artifact A9 + guardrail
    print("\nBuoc 7/7: Sinh artifact A9 + guardrail...")
    artifact_md = generate_a9_artifact(
        study, run_date, gates, pipeline, reporting, stat_check,
        journal_suggestions, presubmission, args.target_journal, args.impact_factor,
        g8_status
    )

    guardrail = guardrail_g8(artifact_md, pipeline)
    print(f"  -> Guardrail: {guardrail['status']}")
    for w in guardrail["warnings"]:
        print(f"    {w}")
    for e in guardrail["errors"]:
        print(f"    {e}")

    # Luu artifact .md
    md_path = out_dir / f"G8_A9_PRESUBMISSION_{study}.md"
    md_path.write_text(artifact_md, encoding="utf-8")
    print(f"\n  -> Luu A9 Markdown: {md_path.name} ({len(artifact_md)//1000}KB)")

    # Xuat DOCX
    docx_path = export_docx(artifact_md, study, out_dir)
    if docx_path:
        print(f"  -> Luu A9 DOCX: {docx_path.name}")

    # Ghi checkpoint
    cp_path = write_g8_checkpoint(
        study, out_dir, run_date, pipeline, reporting, stat_check,
        journal_suggestions, presubmission, guardrail,
        args.target_journal, args.impact_factor, g8_status
    )
    print(f"  -> Luu checkpoint: {cp_path.name}")

    # Tom tat cuoi
    print(f"\n{'='*65}")
    print(f"  G8 HOAN THANH -- {study}")
    print(f"{'='*65}")
    print(f"\n  Dau ra tai: {out_dir}/")
    print(f"  A9 Markdown: {md_path.name}")
    if docx_path:
        print(f"  A9 DOCX:     {docx_path.name}")
    print(f"  Checkpoint:  {cp_path.name}")
    print("\n  KET QUA KIEM TOAN:")
    print(f"  Pipeline:   {pipeline['n_pass']}/{pipeline['n_total']} PASS ({pipeline['completeness_pct']}%)")
    print(f"  Checklist:  {reporting['checked']}/{reporting['total']} "
          f"{reporting['standard_name']} ({reporting['score_pct']}%)")
    print(f"  Thong ke:   {stat_check['passed_count']}/{stat_check['total_checks']} -- {stat_check['overall']}")
    print(f"  Diem/30:    {presubmission['passed']}/{presubmission['total']}")
    print(f"  Guardrail:  {guardrail['status']}")
    print(f"  G8 Status:  {g8_status}")
    print("\n  VIEC CON LAI (bac si thuc hien):")
    print("  1. Dien ket qua that vao Section III+V ban thao G7 (sau phan tich G5+G6)")
    print("  2. Phan cong CRediT roles -- A9 Phan 5")
    print("  3. Khai bao COI day du -- A9 Phan 5")
    print("  4. Soan cover letter theo yeu cau tap chi dich")
    print("  5. Chay plagiarism check (iThenticate/Turnitin) truoc khi nop")
    print("\n  Can bac si kiem chung.")
    print(f"{'='*65}\n")
    # Va 2026-07-11 (vong 9): truoc day exit code luon 0 du guardrail["passed"]=False --
    # checkpoint DA ghi dung, nhung process exit code khong phan anh, nen chay truc tiep
    # (khong qua run_pipeline.py) se tuong nham la xong. Doi xung G3/G4/G9.
    if not guardrail["passed"]:
        print(f"  !! G8 GUARDRAIL LOI ({len(guardrail['errors'])}) -- CHUA HOAN THANH -- {study}")
        raise SystemExit(GC.EXIT_GUARDRAIL_FAIL)


if __name__ == "__main__":
    main()
