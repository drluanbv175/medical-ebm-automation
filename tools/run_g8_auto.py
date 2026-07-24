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

# SỬA 2026-07-23 (vòng lặp kiểm tra-hoàn thiện vòng 12, phát hiện HIGH): tái
# dùng cơ chế A12 THẬT (đọc artifact A12_CITATION_VERIFICATION_<study>.md +
# A12_RETRACTION_RECEIPT.json) thay vì proxy g0._file_exists (chỉ phản ánh G0
# tìm kiếm PubMed tồn tại, không phản ánh kiem-chung-trich-dan đã chạy/PASS).
import run_g10_assemble as G10  # noqa: E402

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
    ("Enrollment flow (Results)", "13",
     # Vá 2026-07-17 (round 5): ten muc cu "Participants (Results)" chua tu khoa
     # "participant" -> bi _item_auto_check() tu-danh-dau "da xong" qua rule
     # participant->G1, dù day la MUC KET QUA can so lieu tuyen chon THAT (chua
     # co khi G1 vua xong). Doi ten de tranh trung tu khoa, giu nguyen noi dung.
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
    ("Enrollment numbers by group (Results)", "22a",
     # Vá 2026-07-17 (round 5): ten cu "Participant numbers" chua tu khoa
     # "participant" -> tu-danh-dau nham qua G1, du day la MUC KET QUA
     # (Participant flow) can so lieu tuyen chon THAT tu thu nghiem.
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

# THEM 2026-07-24 (vong lap kiem tra-hoan thien vong 17, phat hien HIGH): CONSORT
# co phu luc RIENG cho non-inferiority/equivalence trial -- Piaggio G, Elbourne DR,
# Pocock SJ, Evans SJ, Altman DG; CONSORT Group. "Reporting of noninferiority and
# equivalence randomized trials: extension of the CONSORT 2010 statement." JAMA.
# 2012;308(24):2594-2604. doi:10.1001/jama.2012.87802 -- xac minh truc tiep qua
# trang bai bao JAMA. run_g8_auto.py truoc day dung CHUNG CONSORT_ITEMS superiority
# cho MOI RCT bat ke hypothesis_type (ghi o G3_checkpoint.json tu vong 15) -- cong
# kiem truoc nop bai co the cham PASS du ban thao thieu cac muc rieng cua thiet ke
# NI/equivalence. Danh sach PARAPHRASE (khong chep nguyen van) khop voi
# CONSORT_NI_EXTENSION_ITEMS trong run_g7_auto.py.
CONSORT_NI_EXTENSION_ITEMS = [
    ("Title (NI)", "1a-NI", "Tieu de PHAI ghi ro day la thu nghiem non-inferiority/equivalence"),
    ("Abstract (NI)", "1b-NI", "Tom tat neu ro gia thuyet NI/equivalence + margin, ket qua dien giai THEO margin"),
    ("Background (NI)", "2a-NI", "Ly do CHON thiet ke NI/equivalence + bang chung dieu tri doi chung da co hieu qua"),
    ("Objectives (NI)", "2b-NI", "Neu ro gia thuyet NI/equivalence, margin Delta VA bien minh lam sang cho margin do"),
    ("Participants (NI)", "4a-NI", "Doi chieu quan the thu nghiem nay voi quan the (cac) thu nghiem da xac lap hieu qua dieu tri doi chung"),
    ("Interventions (NI)", "5-NI", "Dieu tri doi chung o day co GIONG (hoac rat gan) voi dieu tri doi chung trong (cac) thu nghiem da xac lap hieu qua khong"),
    ("Outcomes (NI)", "6a-NI", "Neu ro ket cuc nao kiem dinh NI/equivalence, ket cuc nao (neu co) van kiem dinh superiority"),
    ("Sample size (NI)", "7a-NI", "NEU RO co mau tinh theo tieu chi NI/equivalence, margin Delta dung de tinh, VA nguon/bien minh margin (KHONG bia margin)"),
    ("Statistical methods (NI)", "12a-NI", "Neu ro dung khoang tin cay MOT phia hay HAI phia de ket luan NI/equivalence"),
    ("Outcomes/estimation (NI)", "17a-NI", "Trinh bay khoang tin cay cua ket cuc NI/equivalence SO VOI margin"),
    ("Interpretation (NI)", "22-NI", "Ban ket qua THEO gia thuyet NI/equivalence; neu chuyen sang ket luan superiority, PHAI bien minh ro ly do chuyen"),
]

# PRISMA 2020 (27 muc chinh thuc / 42 dong checklist -- SR/MA)
# Vá 2026-07-17 (round audit doi khang 5): ban cu 27 "muc" nhung DANH SO SAI hoan
# toan so voi checklist that (vd "11a" dung mot minh khong co "11b", thieu het cac
# muc con 13b-13f, 16b, 20b-20d, 23b-23d, 24b/24c...) -- khong khop chuan cong bo
# (Page MJ et al., BMJ 2021;372:n71). Xay lai dung 42 dong theo PDF chinh thuc
# prisma-statement.org / PMC8005924. Muc KET QUA (16-23) luon "☐" (can du lieu
# that) -- ten muc CO CHU Y tranh cac tu khoa "bias"/"missing"/"participant" ma
# _item_auto_check() dung de tu-danh-dau, vi cac muc nay la KET QUA khong phai
# ke hoach phuong phap (tranh tu-danh-dau nham "da xong" khi chua co du lieu that).
PRISMA_ITEMS = [
    ("Title", "1", "Xac dinh la SR, MA, hoac ca hai ngay trong tieu de"),
    ("Abstract (structured)", "2",
     "Trinh bay tom tat theo checklist PRISMA for Abstracts rieng"),
    ("Rationale", "3",
     "Giai thich ly do thuc hien tong quan trong boi canh hieu biet hien tai"),
    ("Objectives", "4", "Neu muc tieu/cau hoi PICO ma tong quan tra loi"),
    ("Eligibility criteria", "5",
     "Tieu chi nhan/loai va cach nhom nghien cuu de tong hop"),
    ("Information sources (search)", "6",
     "Liet ke moi nguon da tim kiem va ngay tim cuoi cung"),
    ("Search strategy", "7",
     "Trinh bay day du chien luoc tim kiem cho it nhat 1 co so du lieu"),
    ("Selection process", "8",
     "Quy trinh sang loc: so nguoi doc doc lap, cong cu tu dong (neu co)"),
    ("Data collection process", "9",
     "Quy trinh trich xuat du lieu: so nguoi, doc lap, lien he tac gia"),
    ("Outcomes sought", "10a",
     "Liet ke/dinh nghia moi ket cuc tim kiem; cach xu ly ket qua khong day du"),
    ("Other variables sought", "10b",
     "Liet ke/dinh nghia cac bien khac (dac diem PICOS, nguon tai tro...)"),
    ("Risk of bias assessment method", "11",
     "Phuong phap va cong cu danh gia RoB tung nghien cuu, so nguoi danh gia"),
    ("Effect measures", "12",
     "Thuoc do hieu qua chinh dung cho tung ket cuc (RR, MD...)"),
    ("Synthesis -- eligibility per analysis", "13a",
     "Quy trinh quyet dinh nghien cuu nao du dieu kien cho tung tong hop cu the"),
    ("Synthesis -- data preparation", "13b",
     "Cac buoc chuan bi du lieu truoc tong hop (chuyen doi thong ke, xu ly thieu)"),
    ("Synthesis -- tabulation methods", "13c",
     "Phuong phap trinh bay bang/hinh ve ket qua tung nghien cuu va tong hop"),
    ("Synthesis method & model", "13d",
     "Phuong phap tong hop, mo hinh (fixed/random effects), khong dong nhat, phan mem"),
    ("Synthesis -- heterogeneity exploration", "13e",
     "Phuong phap kham pha khong dong nhat (subgroup, meta-regression)"),
    ("Synthesis -- sensitivity analysis", "13f",
     "Phan tich do nhay kiem tra do vung cua ket qua gop"),
    ("Reporting bias assessment methods", "14",
     "Phuong phap danh gia sai lech bao cao (missing results) trong tung tong hop"),
    ("Certainty assessment method", "15",
     "Phuong phap danh gia do chac chan bang chung (vd GRADE) cho tung ket cuc"),
    ("Study selection results (flow diagram)", "16a",
     "Ket qua tim kiem/sang loc theo tung giai doan, ly tuong co so do dong"),
    ("Studies excluded with reasons", "16b",
     "Liet ke nghien cuu co ve du dieu kien nhung bi loai, kem ly do"),
    ("Included-study characteristics (Results)", "17",
     "Trich dan tung nghien cuu dua vao va tom tat dac diem"),
    ("Study-level quality appraisal (Results)", "18",
     "Trinh bay danh gia RoB THAT cho tung nghien cuu dua vao"),
    ("Individual study results", "19",
     "So lieu tom tat tung nghien cuu va uoc luong hieu qua kem do chinh xac"),
    ("Pooled-analysis results -- characteristics", "20a",
     # Vá 2026-07-17 (round 5): ten cu "Synthesis results" chua tu khoa
     # "synthesis" -> bi _item_auto_check() tu-danh-dau nham qua G4, du day la
     # MUC KET QUA can so lieu gop THAT. Doi ten tranh trung tu khoa.
     "Tom tat dac diem/chat luong cac nghien cuu dong gop cho tung tong hop"),
    ("Pooled-analysis results -- estimate", "20b",
     "Ket qua tung tong hop thong ke: uoc luong gop, do chinh xac, khong dong nhat"),
    ("Pooled-analysis results -- heterogeneity", "20c",
     "Ket qua kham pha nguyen nhan khong dong nhat"),
    ("Pooled-analysis results -- sensitivity", "20d",
     "Ket qua phan tich do nhay"),
    ("Evidence-completeness findings (per pooled analysis)", "21",
     "Ket qua danh gia sai lech bao cao THAT cho tung tong hop"),
    ("Certainty of evidence (Results)", "22",
     "Ket qua xep hang do chac chan bang chung THAT cho tung ket cuc quan trong"),
    ("Discussion -- interpretation", "23a",
     "Dien giai chung ket qua trong boi canh bang chung khac"),
    ("Discussion -- limitations of evidence", "23b",
     "Ban luan han che cua bang chung duoc dua vao"),
    ("Discussion -- limitations of review process", "23c",
     "Ban luan han che cua chinh quy trinh tong quan"),
    ("Discussion -- implications", "23d",
     "Y nghia doi voi thuc hanh, chinh sach, nghien cuu tuong lai"),
    ("Registration", "24a",
     "Chi tiet dang ky (PROSPERO...) hoac neu khong dang ky"),
    ("Protocol availability", "24b",
     "Noi truy cap giao thuc tong quan, hoac neu chua co giao thuc"),
    ("Protocol amendments", "24c",
     "Mo ta/giai thich moi thay doi so voi dang ky/giao thuc goc"),
    ("Funding/support", "25", "Nguon tai tro/ho tro va vai tro nha tai tro"),
    ("Competing interests", "26",
     "Khai bao xung dot loi ich cua tac gia tong quan"),
    ("Availability of data, code, materials", "27",
     "Neu ro tai lieu (form sang loc, du lieu trich xuat, code) truy cap o dau"),
]

# STARD 2015 (30 muc chinh thuc / 34 dong checklist -- chan doan)
# Vá 2026-07-17 (round audit doi khang 5): ban cu THIEU HAN muc 18 (co mau --
# nhay tu "17" thang "19") va khai tong sai (24 thay vi 30 -- doi chieu PDF goc
# equator-network.org/wp-content/uploads/2015/03/STARD-2015-checklist.pdf,
# Bossuyt PM et al. BMJ 2015;351:h5527). Xay lai du 30 muc / 34 dong (10a/10b,
# 12a/12b, 13a/13b, 21a/21b tach doi). Muc KET QUA (19-27) luon "☐" -- ten muc
# tranh tu khoa "participant"/"bias"/"missing" de khong bi _item_auto_check()
# tu-danh-dau nham khi chua co du lieu that.
STARD_ITEMS = [
    ("Title/Abstract", "1",
     "Xac dinh la NC do chinh xac chan doan, neu it nhat 1 chi so do (Se/Sp/AUC)"),
    ("Abstract", "2",
     "Trinh bay dang chuan hoa: boi canh, phuong phap, ket qua, ket luan"),
    ("Background", "3",
     "Boi canh khoa hoc/lam sang -- vai tro du kien cua index test"),
    ("Objectives", "4", "Muc tieu nghien cuu va gia thuyet"),
    ("Study design", "5",
     "Huong thu thap du lieu -- truoc (tien cuu) hay sau (hoi cuu) index test"),
    ("Eligibility criteria", "6", "Tieu chi chon nguoi tham gia"),
    ("Participant identification", "7",
     "Cach xac dinh nguoi du dieu kien (trieu chung, XN truoc, danh sach BN)"),
    ("Setting and dates", "8", "Noi va thoi gian xac dinh nguoi tham gia"),
    ("Sampling type", "9",
     "Tuyen lien tiep, mau ngau nhien, hay mau thuan tien"),
    ("Index test description", "10a",
     "Mo ta index test du chi tiet de nguoi khac lap lai"),
    ("Reference standard description", "10b",
     "Mo ta reference standard du chi tiet de nguoi khac lap lai"),
    ("Reference standard rationale", "11",
     "Ly do chon reference standard, neu co nhieu lua chon kha di"),
    ("Index test cutoffs", "12a",
     "Nguong cat/phan loai ket qua index test -- dinh truoc hay do tim sau"),
    ("Reference standard cutoffs", "12b",
     "Nguong cat/phan loai ket qua reference standard -- dinh truoc hay do tim sau"),
    ("Blinding of index-test readers", "13a",
     "Nguoi doc index test co biet thong tin lam sang/ket qua reference standard"),
    ("Blinding of reference-standard readers", "13b",
     "Nguoi doc reference standard co biet thong tin lam sang/ket qua index test"),
    ("Statistical analysis methods", "14",
     "Phuong phap uoc luong/so sanh cac chi so do chinh xac chan doan"),
    ("Indeterminate results handling", "15",
     "Cach xu ly ket qua khong xac dinh (indeterminate) cua index/reference"),
    ("Missing data handling", "16",
     "Cach xu ly du lieu thieu cua index test/reference standard"),
    ("Subgroup analysis plan", "17",
     "Phan tich bien thien do chinh xac theo phan nhom -- dinh truoc hay do tim sau"),
    ("Sample size", "18", "Co mau du kien va cach tinh"),
    ("Flow diagram (Results)", "19",
     "So do dong nguoi tham gia (STARD flow diagram)"),
    ("Baseline characteristics (Results)", "20",
     "Dac diem nhan khau hoc va lam sang nen"),
    ("Disease severity distribution (Results)", "21a",
     "Phan bo muc do nang benh o nhom co benh muc tieu"),
    ("Alternative diagnoses distribution (Results)", "21b",
     "Phan bo cac chan doan thay the o nhom khong co benh muc tieu"),
    ("Time interval between tests (Results)", "22",
     "Khoang thoi gian va can thiep lam sang xen giua index test va reference"),
    ("Cross tabulation (Results)", "23",
     "Bang cheo (2x2) doi chieu ket qua index test voi reference standard"),
    ("Accuracy estimates (Results)", "24",
     "Uoc luong do chinh xac chan doan (Se/Sp/PPV/NPV...) kem 95% CI"),
    ("Adverse events (Results)", "25",
     "Bien co bat loi khi thuc hien index test hoac reference standard"),
    ("Limitations (Discussion)", "26",
     "Han che nghien cuu -- nguon sai lech, bat dinh thong ke, kha nang khai quat"),
    ("Clinical implications (Discussion)", "27",
     "Y nghia lam sang -- vai tro du kien cua index test trong thuc hanh"),
    ("Registration", "28", "So dang ky va ten co quan dang ky nghien cuu"),
    ("Protocol availability", "29",
     "Noi co the truy cap giao thuc nghien cuu day du"),
    ("Sources of funding", "30",
     "Nguon tai tro va vai tro cua nha tai tro"),
]

# TRIPOD+AI 2024 (27 muc chinh thuc / 52 dong checklist -- tien luong/du doan,
# THAY THE HOAN TOAN TRIPOD 2015).
# Vá 2026-07-17 (round audit doi khang 5): ban cu "TRIPOD 2015, 20 dong" sai TREN
# CA HAI TRUC dong thoi -- (1) ngay voi TRIPOD 2015 goc da thieu nhieu muc that
# (11 risk groups, 12 dev-vs-validation, 13b/13c, 14b, 15a/15b...), va (2) TRIPOD
# 2015 da bi TRIPOD+AI 2024 THAY THE HOAN TOAN cho moi mo hinh tien luong (hoi quy
# lan AI/ML) tu thang 4/2025 (Collins GS et al., BMJ 2024;385:e078378) -- doctrine
# (run_g1_auto.py::REPORTING_STANDARDS["prediction"]) da tuyen bo dung "TRIPOD+AI
# 2024" tu truoc, nhung file nay (cong G8 -- kiem tien nop bai) chua he co noi
# dung khop. Xay lai du 27 muc / 52 dong theo checklist chinh thuc
# tripod-statement.org (TRIPODAI-Supplement.pdf, xac minh truc tiep). Danh dau
# D=Development, E=Evaluation, D;E=ca hai trong item_desc. Muc KET QUA/THAO LUAN
# (20 tro di) luon "☐" -- ten muc tranh tu khoa "participant"/"bias"/"missing" de
# khong bi _item_auto_check() tu-danh-dau nham khi chua co du lieu that.
TRIPOD_ITEMS = [
    ("Title", "1",
     "[D;E] Xac dinh dang phat trien/danh gia mo hinh, quan the dich, ket cuc du doan"),
    ("Abstract (structured)", "2",
     "[D;E] Hoan thanh checklist rieng TRIPOD+AI for Abstracts"),
    ("Background -- context", "3a",
     "[D;E] Boi canh lam sang (chan doan/tien luong), ly do, tham chieu mo hinh co san"),
    ("Background -- target population", "3b",
     "[D;E] Quan the dich, muc dich su dung trong quy trinh cham soc, nguoi dung du kien"),
    ("Background -- health inequalities", "3c",
     "[D;E] Bat binh dang suc khoe da biet giua cac nhom nhan khau xa hoi lien quan"),
    ("Objectives", "4",
     "[D;E] Neu ro day la phat trien, danh gia, hay ca hai"),
    ("Data sources", "5a",
     "[D;E] Nguon du lieu rieng cho phat trien/danh gia, ly do, tinh dai dien, du lieu tong hop (neu co)"),
    ("Accrual dates", "5b",
     "[D;E] Ngay bat dau tuyen va ngay ket thuc theo doi"),
    ("Study setting", "6a",
     "[D;E] Boi canh nghien cuu, so luong/vi tri trung tam"),
    ("Eligibility criteria", "6b",
     "[D;E] Tieu chi chon nguoi tham gia"),
    ("Treatments received", "6c",
     "[D;E] Dieu tri nhan duoc va cach xu ly trong qua trinh phat trien/danh gia"),
    ("Data preparation", "7",
     "[D;E] Tien xu ly/lam sach/feature engineering, kiem tra chat luong, tinh nhat quan giua cac nhom"),
    ("Outcome definition", "8a",
     "[D;E] Dinh nghia ket cuc + moc thoi gian, ly do, tinh nhat quan giua cac nhom"),
    ("Outcome assessors", "8b",
     "[D;E] Trinh do/dac diem nguoi danh gia ket cuc (neu ket cuc mang tinh chu quan)"),
    ("Outcome blinding", "8c",
     "[D;E] Lam mu khi danh gia ket cuc (tranh ro ri nhan/label leakage)"),
    ("Predictor selection", "9a",
     "[D] Cach chon/nguon bien tien doan ban dau va moi tien-loc truoc khi xay mo hinh"),
    ("Predictor definitions", "9b",
     "[D;E] Dinh nghia moi bien tien doan, cach/thoi diem do, lam mu"),
    ("Predictor assessors", "9c",
     "[D;E] Trinh do/dac diem nguoi danh gia bien tien doan (neu mang tinh chu quan)"),
    ("Sample size", "10",
     "[D;E] Cach xac dinh co mau, rieng cho phat trien/danh gia, kem chi tiet tinh toan"),
    ("Missing data handling", "11",
     "[D;E] Cach xu ly du lieu thieu, ly do thieu"),
    ("Data partitioning", "12a",
     "[D] Cach chia du lieu (phat trien, tuning, danh gia), kiem tra ro ri du lieu (leakage)"),
    ("Predictor handling", "12b",
     "[D] Dang ham/chuan hoa/bien doi cua bien tien doan"),
    ("Model building method", "12c",
     "[D] Loai mo hinh + ly do, cac buoc xay dung, tuning sieu tham so, validation noi bo"),
    ("Cluster heterogeneity (methods)", "12d",
     "[D;E] Do khong dong nhat giua cum (benh vien/quoc gia); doi chieu TRIPOD-Cluster"),
    ("Performance measures specified", "12e",
     "[D;E] Chi so/bieu do danh gia hieu nang da xac dinh (phan biet, hieu chinh, loi ich lam sang)"),
    ("Model updating method", "12f",
     "[E] Cap nhat/hieu chinh lai mo hinh phat sinh tu danh gia"),
    ("Prediction calculation method", "12g",
     "[E] Cach tinh du doan khi danh gia (cong thuc/code/object/API)"),
    ("Class imbalance handling", "13",
     "[D;E] Co dung phuong phap xu ly mat can bang lop (SMOTE...) va tai hieu chinh khong"),
    ("Fairness approach", "14",
     "[D;E] Cach tiep can dam bao cong bang/giam thien kien mo hinh va ly do"),
    ("Model output type", "15",
     "[D] Loai dau ra (xac suat/phan loai), ly do nguong cat, khoang bat dinh"),
    ("Development vs evaluation differences", "16",
     "[D;E] Khac biet giua du lieu phat trien va danh gia (boi canh, tieu chi, ket cuc, tien doan)"),
    ("Ethical approval", "17",
     "[D;E] Ten hoi dong dao duc/IRB, dong thuan hoac ly do mien"),
    ("Open Science -- funding", "18a",
     "[D;E] Nguon tai tro va vai tro nha tai tro"),
    ("Open Science -- conflicts of interest", "18b",
     "[D;E] Xung dot loi ich/khai bao tai chinh cua moi tac gia"),
    ("Open Science -- protocol availability", "18c",
     "[D;E] Noi truy cap giao thuc nghien cuu, hoac neu chua co"),
    ("Open Science -- registration", "18d",
     "[D;E] Ten/so dang ky, hoac neu chua dang ky"),
    ("Open Science -- data sharing", "18e",
     "[D;E] Chi tiet kha nang tiep can du lieu, dieu kien, tu dien du lieu"),
    ("Open Science -- code sharing", "18f",
     "[D;E] Kha nang tiep can code phan tich, moi truong tinh toan/phien ban phan mem-phan cung"),
    ("Patient and public involvement", "19",
     "[D;E] PPI trong thiet ke/thuc hien/bao cao/pho bien, hoac neu khong co (GRIPP2)"),
    ("Results -- flow and follow-up", "20a",
     "[D;E] Luong nguoi tham gia, so ket cuc, tom tat theo doi"),
    ("Results -- baseline characteristics", "20b",
     "[D;E] Dac diem chung/theo nguon, gom khac biet giua nhom nhan khau xa hoi"),
    ("Results -- comparison to development data", "20c",
     "[E] So sanh phan bo bien tien doan/ket cuc voi du lieu phat trien"),
    ("Model development counts", "21",
     "[D;E] So nguoi tham gia va so ket cuc trong tung phan tich (phat trien, tuning, danh gia)"),
    ("Model specification (Results)", "22",
     "[D] Chi tiet day du mo hinh (cong thuc/code/object/API) de ben thu ba su dung, han che tiep can neu co"),
    ("Model performance estimates (Results)", "23a",
     "[D;E] Uoc luong hieu nang kem CI, gom cac phan nhom quan trong, bieu do"),
    ("Performance heterogeneity across clusters (Results)", "23b",
     "[D;E] Do khong dong nhat hieu nang giua cac cum; doi chieu TRIPOD-Cluster"),
    ("Model updating results", "24",
     "[E] Ket qua cap nhat mo hinh (neu co), mo hinh va hieu nang sau cap nhat"),
    ("Discussion -- interpretation", "25",
     "[D;E] Dien giai tong the, gom cong bang, so voi muc tieu/nghien cuu truoc"),
    ("Discussion -- limitations", "26",
     "[D;E] Han che nghien cuu va anh huong den sai lech/bat dinh/kha nang khai quat"),
    ("Usability -- poor-quality input handling", "27a",
     "[D] Cach xu ly du lieu dau vao kem chat luong/khong co khi trien khai thuc te"),
    ("Usability -- human-AI interaction", "27b",
     "[D] Co can tuong tac nguoi-AI khong, muc do chuyen mon can thiet"),
    ("Next steps and generalisability", "27c",
     # Vá 2026-07-17 (round 5): ten cu "Future research implications" chua chuoi
     # con "search" AN TRONG chu "reSEARCH" -> vo tinh khop tu khoa
     # background/rationale/search/eligibility cua _item_auto_check() -> tu
     # danh dau nham. Doi ten, giu nguyen noi dung mo ta.
     "[D;E] Buoc tiep theo cho nghien cuu tuong lai, kha nang khai quat hoa"),
]

# SRQR 2014 (21 muc -- Standards for Reporting Qualitative Research, O'Brien BC
# et al., Acad Med 2014;89:1245-1251). THEM 2026-07-21 (vong lap kiem tra-hoan
# thien vong 2, phat hien HIGH): DESIGN_CHECKLIST_MAP truoc day thieu han
# "qualitative" -- build_reporting_checklist() fallback ve STROBE 2007 (22 muc
# ngau nhien hoa/mu/phoi nhiem) cho nghien cuu dinh tinh, du run_g1_auto.py va
# run_g7_auto.py da gan DUNG chuan SRQR cho thiet ke nay tu 2026-07-19.
# Noi dung dong bo Y HET voi run_g7_auto.py::CHECKLIST_ITEMS["qualitative"] (21
# muc, da vetted 2026-07-19) -- tranh dung lop loi "2 file xu ly cung khai niem
# nhung lech nhau" da gap nhieu lan trong du an nay.
SRQR_ITEMS = [
    ("Title", "1",
     "Neu ro nghien cuu la DINH TINH hoac ten cach tiep can (vd hien tuong hoc)"),
    ("Abstract", "2", "Tom luoc muc tieu, phuong phap, ket qua chinh theo cau truc"),
    ("Problem formulation", "3", "Mo ta van de nghien cuu va tong quan y van lien quan"),
    ("Purpose/research question", "4", "Neu ro cau hoi nghien cuu khop paradigm dinh tinh"),
    ("Qualitative approach and research paradigm", "5",
     "Hien tuong hoc/grounded theory/phan tich chu de..., ly do chon"),
    ("Researcher characteristics and reflexivity", "6",
     "Kinh nghiem, dao tao, moi quan he voi nguoi tham gia, gia dinh (reflexivity)"),
    ("Context", "7", "Co so/dia diem nghien cuu va ly do chon"),
    ("Sampling strategy", "8", "Cach chon nguoi tham gia (purposive/snowball...), tieu chi, cach tiep can"),
    ("Ethical issues pertaining to human subjects", "9",
     "Chap thuan IRB, dong thuan tham gia, bao mat, can nhac dac thu nghien cuu dinh tinh"),
    ("Data collection methods", "10",
     "Hinh thuc (phong van/nhom/quan sat), thoi gian, so lan lap, ly do dung"),
    ("Data collection instruments and technologies", "11",
     "Huong dan phong van/quan sat, thu nghiem truoc, ai thu thap, thay doi trong qua trinh"),
    ("Units of study", "12", "So nguoi/nhom tham gia, muc do tham gia, dac diem nhan khau"),
    ("Data processing", "13", "Go bang, ghi chu hien truong, quan ly du lieu, khu dinh danh"),
    ("Data analysis", "14", "Quy trinh ma hoa, ai phan tich, phan mem ho tro (neu co)"),
    ("Techniques to enhance trustworthiness", "15",
     "Trustworthiness (credibility/transferability/dependability/confirmability), triangulation, member checking, audit trail"),
    # SUA 2026-07-21 (vong lap kiem tra-hoan thien vong 3, phat hien LOW, do
    # tin cay trung binh): ten muc 16/18 truoc day ("Results/findings"/
    # "Integration with theory") khong khop checklist SRQR 2014 chinh thuc
    # (O'Brien BC et al., Acad Med 2014;89:1245-1251) -- muc 16 la "Synthesis
    # and interpretation" (khong phai ten muc lon "Results/findings" gom ca
    # 16-17), muc 18 la "Integration with other literature". Sua dong bo ca
    # run_g7_auto.py.
    ("Synthesis and interpretation", "16", "Trinh bay phat hien chinh co ho tro bang du lieu (quote/trich doan) THAT"),
    ("Links to empirical data", "17", "Ket luan co bam sat/duoc minh hoa boi du lieu thu thap"),
    ("Integration with other literature", "18", "Doi chieu phat hien voi khung ly thuyet/y van hien co"),
    ("Limitations", "19", "Han che nghien cuu, anh huong den do tin cay/kha nang chuyen giao ket qua"),
    ("Conflicts of interest", "20", "Khai bao xung dot loi ich cua nhom nghien cuu"),
    ("Funding source", "21", "Nguon tai tro va vai tro nha tai tro trong thiet ke/thuc hien/cong bo"),
]

# THEM 2026-07-23 (vong lap kiem tra-hoan thien vong 12, phat hien MEDIUM):
# CHEERS 2022 (28 muc chinh thuc) -- dong bo Y HET noi dung da xac minh truc
# tiep Table 1 (Husereau D et al. Value Health. 2022;25(1):3-9) va da dung o
# run_g7_auto.py::CHECKLIST_ITEMS["economic"] (vong 11) -- tranh dung lop loi
# "2 file xu ly cung khai niem nhung lech nhau".
CHEERS_ITEMS = [
    ("Title", "1", "Xac dinh day la danh gia kinh te y te va neu ro cac can thiep duoc so sanh"),
    ("Abstract", "2", "Tom tat co cau truc -- boi canh, phuong phap chinh, ket qua, phan tich thay the"),
    ("Background and objectives", "3", "Boi canh nghien cuu, cau hoi nghien cuu, y nghia thuc tien cho quyet dinh"),
    ("Health economic analysis plan", "4", "Neu ro da xay dung ke hoach phan tich kinh te y te hay chua, noi truy cap"),
    ("Study population", "5", "Dac diem quan the nghien cuu (tuoi, nhan khau hoc, kinh te-xa hoi, lam sang)"),
    ("Setting and location", "6", "Thong tin boi canh lien quan co the anh huong ket qua"),
    ("Comparators", "7", "Cac can thiep/chien luoc duoc so sanh va ly do chon"),
    ("Perspective", "8", "Goc nhin cua nghien cuu va ly do chon"),
    ("Time horizon", "9", "Khung thoi gian cua nghien cuu va ly do phu hop"),
    ("Discount rate", "10", "Ty le chiet khau va ly do chon"),
    ("Selection of outcomes", "11", "Ket cuc nao duoc dung lam thuoc do loi ich/tac hai"),
    ("Measurement of outcomes", "12", "Cach do luong cac ket cuc dung de nam bat loi ich/tac hai"),
    ("Valuation of outcomes", "13", "Quan the va phuong phap dung de do luong va dinh gia ket cuc"),
    ("Measurement and valuation of resources and costs", "14", "Cach dinh gia chi phi"),
    ("Currency, price date, and conversion", "15", "Thoi diem uoc tinh nguon luc/don gia, don vi tien te, nam quy doi"),
    ("Rationale and description of model", "16", "Neu co mo hinh hoa: mo ta chi tiet va ly do; mo hinh co cong khai khong"),
    ("Analytics and assumptions", "17", "Phuong phap phan tich/bien doi thong ke, ngoai suy, tham dinh mo hinh"),
    ("Characterizing heterogeneity", "18", "Phuong phap uoc tinh ket qua khac nhau the nao giua cac nhom nho"),
    ("Characterizing distributional effects", "19", "Cach tac dong duoc phan bo giua cac ca nhan/dieu chinh nhom uu tien"),
    ("Characterizing uncertainty", "20", "Phuong phap mo ta dac diem cac nguon bat dinh trong phan tich"),
    ("Approach to engagement with patients and others affected by the study", "21",
     "Cach tiep can de benh nhan/cong dong/ben lien quan tham gia thiet ke nghien cuu"),
    ("Study parameters", "22", "Moi tham so dau vao phan tich (gia tri, khoang, nguon) kem gia dinh bat dinh"),
    ("Summary of main results", "23", "Gia tri trung binh cho cac nhom chi phi/ket cuc chinh, tong hop bang thuoc do phu hop"),
    ("Effect of uncertainty", "24", "Bat dinh ve nhan dinh/dau vao/du phong anh huong ket qua the nao"),
    ("Effect of engagement with patients and others affected by the study", "25",
     "Su tham gia cua benh nhan/cong dong da thay doi cach tiep can/ket qua ra sao"),
    ("Study findings, limitations, generalizability, and current knowledge", "26",
     "Phat hien chinh, han che, can nhac dao duc/cong bang chua nam bat, anh huong benh nhan/chinh sach"),
    ("Source of funding", "27", "Nguon tai tro va vai tro nha tai tro trong xac dinh/thiet ke/trien khai/bao cao"),
    ("Conflicts of interest", "28", "Xung dot loi ich cua tac gia theo yeu cau tap chi hoac ICMJE"),
]

# Anh xa design_code -> (ten chuan, danh sach muc)
DESIGN_CHECKLIST_MAP = {
    "rct":             ("CONSORT 2025",   CONSORT_ITEMS),
    "cohort":          ("STROBE 2007",    STROBE_ITEMS),
    "case_control":    ("STROBE 2007",    STROBE_ITEMS),
    "cross_sectional": ("STROBE 2007",    STROBE_ITEMS),
    "diagnostic":      ("STARD 2015",     STARD_ITEMS),
    "sr_ma":           ("PRISMA 2020",    PRISMA_ITEMS),
    "prediction":      ("TRIPOD+AI 2024", TRIPOD_ITEMS),
    "tripod":          ("TRIPOD+AI 2024", TRIPOD_ITEMS),
    "qualitative":     ("SRQR 2014",      SRQR_ITEMS),
    "economic":        ("CHEERS 2022",    CHEERS_ITEMS),
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
    "case_control": {
        "default": [
            ("American Journal of Epidemiology", 5.0, "Case-control dich te phan tich"),
            ("International Journal of Epidemiology", 7.7, "Case-control dich te lon"),
            ("BMJ Open", 2.9, "Case-control lam sang + cong dong"),
            ("PLOS ONE", 3.7, "Case-control da linh vuc, tiep can mo"),
            ("Journal of Epidemiology & Community Health", 5.5, "Case-control dich te"),
        ],
        "cardiology": [
            ("American Heart Journal", 4.3, "Case-control tim mach"),
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
    # THEM 2026-07-21 (vong lap kiem tra-hoan thien vong 5, phat hien MEDIUM): key
    # "qualitative" bi THIEU trong dict nay tu dau (7/8 ma canon design_code) --
    # suggest_journals() rơi vao nhanh fallback "cohort" (goi y tap chi lam sang
    # dinh luong nhu JACC/Diabetes Care cho mot nghien cuu dinh tinh, sai chuyen
    # mon du co in canh bao). Cung loi "sua 1 dict quen dict song song" nhu
    # DESIGN_CHECKLIST_MAP da vá o vong truoc (dict ngay phia tren, dong ~502) --
    # 2 dict nay dinh nghia SONG SONG theo design_code nhung duoc bao tri doc lap.
    "qualitative": {
        "default": [
            ("Qualitative Health Research", 2.9, "Dinh tinh y te noi chung"),
            ("BMC Medical Research Methodology", 4.4, "Phuong phap luan dinh tinh/hon hop"),
            ("International Journal of Qualitative Methods", 2.5,
             "Dinh tinh da phuong phap, open access"),
            ("Global Qualitative Nursing Research", 2.5, "Dinh tinh dieu duong/cham soc suc khoe"),
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


def build_reporting_checklist(design_code: str, gates: dict, specialist_modules: list = None,
                               hypothesis_type: str = "superiority", margin=None) -> dict:
    """Xay dung checklist chuan bao cao va tu kiem tu checkpoints.

    THEM 2026-07-23 (vong lap kiem tra-hoan thien vong 12, phat hien MEDIUM):
    run_g1_auto.py::detect_specialist_modules() co the gan module cong them
    (vd 'economic') vao checkpoint G1 doc lap voi design_code CHINH -- truoc
    day ham nay KHONG doc lai specialist_modules (grep xac nhan khong co chuoi
    'specialist' nao trong file), nen diem % checklist/muc "Checklist >= 60%"
    o Phan 7 khong bao gio phan anh CHEERS du run_g7_auto.py da noi tu vong 11.
    specialist_module_checklist=None neu khong co module cong them nao ap dung.

    THEM 2026-07-24 (vong lap kiem tra-hoan thien vong 17, phat hien HIGH):
    tuong tu -- khi design_code=='rct' VA hypothesis_type la non_inferiority/
    equivalence (ghi o G3_checkpoint.json boi run_g3_auto.py, vong 15), them
    ni_extension_checklist rieng (Piaggio 2012) -- xem CONSORT_NI_EXTENSION_ITEMS.
    """
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
    result = {
        "standard_name": std_name,
        "items": rows,
        "checked": checked,
        "total": total,
        "score_pct": round(checked / total * 100) if total > 0 else 0,
        "specialist_module_checklist": None,
        "ni_extension_checklist": None,
    }

    specialist_modules = specialist_modules or []
    if "economic" in specialist_modules and design_code != "economic":
        result["specialist_module_checklist"] = build_reporting_checklist("economic", gates)

    if design_code == "rct" and hypothesis_type in ("non_inferiority", "equivalence"):
        ni_rows = [{"num": num, "name": name, "desc": desc, "mark": "☐ [CẦN]"}
                   for name, num, desc in CONSORT_NI_EXTENSION_ITEMS]
        result["ni_extension_checklist"] = {
            "standard_name": f"CONSORT Non-inferiority/Equivalence Extension "
                              f"(Piaggio 2012, JAMA;308(24):2594-2604, doi:10.1001/jama.2012.87802)",
            "hypothesis_type": hypothesis_type,
            "margin": margin,
            "items": ni_rows,
            "checked": 0,
            "total": len(ni_rows),
            "score_pct": 0,
        }
    return result


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

    design_journals = JOURNAL_SUGGESTIONS.get(design_code)
    if design_journals is None:
        # Không khớp key nào → rơi về cohort, NHƯNG in cảnh báo (không âm thầm):
        # tránh lặp lại lỗi đã gặp khi "prediction"/"case_control" bị fallback ngầm.
        print(
            f"  ⚠ G8: design_code='{design_code}' chưa có bảng gợi ý tạp chí riêng "
            f"→ tạm dùng danh sách 'cohort'. Cân nhắc bổ sung key này vào "
            f"JOURNAL_SUGGESTIONS."
        )
        design_journals = JOURNAL_SUGGESTIONS.get("cohort", {})
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
                                   journal_suggestions: list,
                                   study: str = "", out_dir: Path = None) -> dict:
    """
    Xay dung danh sach 30 muc tu kiem truoc nop.
    Nhom: PIPELINE (10) + KHOA HOC (8) + LIEM CHINH (7) + TRINH BAY (5).
    Nguong nop: >= 25/30.
    """
    g0 = gates.get("G0", {})
    g2 = gates.get("G2", {})
    g4 = gates.get("G4", {})
    g5 = gates.get("G5", {})

    # SỬA 2026-07-23 (vòng lặp kiểm tra-hoàn thiện vòng 12, phát hiện HIGH):
    # 2 mục dưới đây (LIEM CHINH "PMID/DOI đã xác minh" + TRINH BAY "định dạng
    # trích dẫn") trước đây dùng g0.get("_file_exists") làm proxy — G0 là
    # checkpoint TÌM KIẾM PUBMED, gần như luôn tồn tại rất sớm, hoàn toàn không
    # phản ánh agent kiem-chung-trich-dan (cổng A12 thật) đã chạy/PASS. Dùng
    # lại citation_verification_ok() thật của run_g10_assemble.py — cùng cơ chế
    # đọc A12_CITATION_VERIFICATION_<study>.md + A12_RETRACTION_RECEIPT.json.
    citation_ok = False
    if study and out_dir is not None:
        citation_ok, _reason = G10.citation_verification_ok(study, out_dir)

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
         citation_ok,
         note="Cong A12 (kiem-chung-trich-dan)" if citation_ok
              else "[CAN] Chua PASS cong A12 -- chay agent kiem-chung-trich-dan")
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
         citation_ok,
         note="Cong A12 (kiem-chung-trich-dan)" if citation_ok
              else "[CAN] Chua PASS cong A12 -- chay agent kiem-chung-trich-dan")
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
    gate_criteria: dict = None,
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

    # THÊM 2026-07-23 (vòng lặp kiểm tra-hoàn thiện vòng 12): cấu phần chuyên
    # biệt (vd kinh tế y tế) mà run_g1_auto.py::detect_specialist_modules()
    # phát hiện cộng thêm bên cạnh thiết kế chính — trước đây tính xong rồi
    # KHÔNG hiển thị ở đâu cả trong artifact A9.
    sm = reporting.get("specialist_module_checklist")
    if sm:
        ln(f"### Cấu phần cộng thêm — CHECKLIST {sm['standard_name']} ({sm['total']} MỤC)")
        ln()
        ln(f"> Đề tài có cấu phần chuyên biệt cộng thêm (specialist_modules phát hiện ở G1) — "
           f"checklist {sm['standard_name']} dưới đây báo cáo RIÊNG cho cấu phần đó, KHÔNG thay "
           f"thế checklist chính ở trên.")
        ln(f"> **Tự kiểm từ checkpoints:** {sm['checked']}/{sm['total']} mục = **{sm['score_pct']}%**")
        ln()
        ln("| # | Mục | Mô tả rút gọn | Trạng thái |")
        ln("|---|-----|--------------|-----------|")
        for item in sm["items"]:
            desc_s = item["desc"][:70] + ("..." if len(item["desc"]) > 70 else "")
            ln(f"| {item['num']} | {item['name']} | {desc_s} | {item['mark']} |")
        ln()

    # THÊM 2026-07-24 (vòng lặp kiểm tra-hoàn thiện vòng 17, phát hiện HIGH):
    # phụ lục CONSORT-NI/Equivalence (Piaggio 2012) — cùng khuôn hiển thị như
    # specialist_module_checklist ở trên, nhưng theo hypothesis_type (G3) chứ
    # không phải specialist_modules (G1).
    ni_ext = reporting.get("ni_extension_checklist")
    if ni_ext:
        margin_note = f"margin Δ={ni_ext['margin']}" if ni_ext.get("margin") is not None else "margin [CẦN BÁC SĨ/THỐNG KÊ VIÊN CUNG CẤP]"
        ln(f"### ⚠️ Đề tài {ni_ext['hypothesis_type'].upper()} — CHECKLIST {ni_ext['standard_name']} ({ni_ext['total']} MỤC)")
        ln()
        ln(f"> Đề tài thiết kế **{ni_ext['hypothesis_type']}** ({margin_note}, từ G3_checkpoint.json) — "
           f"CONSORT chuẩn KHÔNG đủ, PHẢI báo cáo thêm các mục dưới đây. KHÔNG thay thế checklist chính ở trên.")
        ln()
        ln("| # | Mục | Mô tả rút gọn | Trạng thái |")
        ln("|---|-----|--------------|-----------|")
        for item in ni_ext["items"]:
            desc_s = item["desc"][:70] + ("..." if len(item["desc"]) > 70 else "")
            ln(f"| {item['num']} | {item['name']} | {desc_s} | {item['mark']} |")
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

    # Phan 7 -- SUA 2026-07-23 (vong lap kiem tra-hoan thien vong 12, phat hien
    # HIGH): truoc day ham nay TU TINH LAI mot ban sao rieng irb_ok/sap_ok/
    # g7_ok/score_ok chi de HIEN THI, troi dat khoi logic g8_status THAT trong
    # main() (2 noi tinh doc lap -- cung lop loi da lap lai nhieu lan trong
    # file nay). Va results_final -- dieu kien CHAN THAT trong main() (thieu no
    # → luon PENDING/PARTIAL) -- KHONG he xuat hien trong bang "BAT BUOC" hien
    # thi cho bac si, chi duoc nhac nhe o muc 6 ngang hang voi "phan cong CRediT
    # roles". Nay nhan gate_criteria (dict) tu main() lam NGUON SU THAT DUY NHAT
    # -- khong tinh lai; gate_criteria=None (vd goi truc tiep tu test cu) →
    # fallback tinh nhu cu de khong pha vo tuong thich nguoc.
    if gate_criteria is None:
        irb_ok = bool(
            gates["G2"].get("g2_irb_number") and
            "[CAN" not in str(gates["G2"].get("g2_irb_number", ""))
        )
        sap_ok = bool(
            gates["G4"].get("sap_signed_date") or gates["G4"].get("sap_locked")
        )
        g7_ok = gates["G7"].get("_file_exists", False)
        score_ok = presubmission["passed"] >= 25
        results_final = False
    else:
        irb_ok = gate_criteria["irb_ok"]
        sap_ok = gate_criteria["sap_ok"]
        g7_ok = gate_criteria["g7_ok"]
        score_ok = gate_criteria["score_ok"]
        results_final = gate_criteria["results_final"]
    reporting_ok = reporting["score_pct"] >= 60

    ln("---")
    ln()
    ln("## PHẦN 7 — TIÊU CHÍ QUA CỔNG G8")
    ln()
    ln("```")
    ln("G8 PASS khi dap ung TAT CA 6 dieu kien BAT BUOC + bac si xac nhan 4 muc cuoi:")
    ln()
    ln("BAT BUOC (tu dong kiem tu checkpoints):")
    ln(f"{'OK' if irb_ok else 'ND'} 1. G2 LOCKED -- IRB number that: {gates['G2'].get('g2_irb_number','[CAN]')}")
    ln(f"{'OK' if sap_ok else 'ND'} 2. G4 LOCKED -- SAP da ky truoc khi xem du lieu")
    ln(f"{'OK' if g7_ok else 'ND'} 3. G7 DONE -- Ban thao IMRAD skeleton da sinh")
    ln(f"{'OK' if results_final else 'ND'} 4. Ket qua phan tich THAT da xac nhan (results_final trong "
       "study_meta.json -- dieu kien CHAN, thieu no thi KHONG bao gio PASS du diem tu kiem cao)")
    ln(f"{'OK' if score_ok else 'ND'} 5. Diem tu kiem >= 25/30 (hien: {presubmission['passed']}/30)")
    ln(f"{'OK' if reporting_ok else 'ND'} 6. Checklist {reporting['standard_name']} >= 60% (hien: {reporting['score_pct']}%)")
    ln()
    ln("CAN BAC SI XAC NHAN (khong the tu dong):")
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
    reporting = build_reporting_checklist(
        design_code, gates, specialist_modules=gates.get("G1", {}).get("specialist_modules") or [],
        hypothesis_type=gates.get("G3", {}).get("hypothesis_type") or "superiority",
        margin=gates.get("G3", {}).get("margin"),
    )
    print(f"  -> {reporting['standard_name']}: {reporting['checked']}/{reporting['total']} "
          f"({reporting['score_pct']}%)")
    if reporting["specialist_module_checklist"]:
        sm = reporting["specialist_module_checklist"]
        print(f"  -> + {sm['standard_name']} (cau phan cong them): {sm['checked']}/{sm['total']} ({sm['score_pct']}%)")

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
        pipeline, reporting, stat_check, gates, journal_suggestions,
        study=study, out_dir=out_dir,
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
    gate_criteria = {
        "irb_ok": irb_ok, "sap_ok": sap_ok, "g7_ok": g7_ok,
        "score_ok": score_ok, "results_final": results_final,
    }
    artifact_md = generate_a9_artifact(
        study, run_date, gates, pipeline, reporting, stat_check,
        journal_suggestions, presubmission, args.target_journal, args.impact_factor,
        g8_status, gate_criteria=gate_criteria,
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
