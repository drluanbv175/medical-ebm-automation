"""Danh mục RSS/Atom feed CHÍNH THỐNG (an toàn thuốc + guideline) – TỰ ĐỘNG hoá.

Các URL dưới đây ĐÃ được kiểm tra hoạt động (HTTP 200, trả XML) tại thời điểm tích hợp.
Tuy nhiên feed của cơ quan/nhà xuất bản CÓ THỂ ĐỔI: nếu một feed lỗi, hệ thống ghi
Source Log và bỏ qua (không bịa dữ liệu). Bạn có thể sửa/bổ sung URL tại đây.

Tôn trọng điều khoản sử dụng: chỉ đọc RSS/Atom công khai do tổ chức phát hành.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import List


@dataclass(frozen=True)
class FeedConfig:
    id: str
    name: str
    url: str
    org: str
    kind: str               # "drug_safety" | "guideline"
    clinical_area: str | None = None
    # mode "rss" (mặc định) đọc RSS/Atom ở `url`; mode "crossref" lấy bài MỚI NHẤT của tạp chí theo `issn` qua Crossref
    # (api.crossref.org, không khoá) — dùng khi RSS của nhà xuất bản không đọc được từ máy chủ/mạng của bác sĩ.
    issn: str | None = None
    mode: str = "rss"
    # ── LANE guideline (20/09/2026, xem app/sources/guideline_lanes.py) ──
    # mode: "rss" | "crossref" (bài mới nhất theo ISSN) | "crossref_title" (khuyến cáo của hiệp hội trên tạp chí của
    # họ; `issn` có thể là NHIỀU ISSN ngăn bằng "|", kèm `title_query` + `title_regex`) | "europepmc" (`epmc_query`) |
    # "who_iris" (OAI-PMH) | "kcb_vn".
    title_query: str | None = None
    title_regex: str | None = None       # regex TỔ CHỨC phải khớp trong tiêu đề (vd "KDIGO", "\\bESC\\b")
    window_days: int | None = None       # cửa sổ khi ingestion không truyền since_date
    epmc_query: str | None = None
    oai_set: str | None = None
    is_guideline: bool = False           # nguồn xác nhận loại «guideline» (vd pubtype MEDLINE): study_type=guideline
    cap_results: int | None = None       # lane khối lượng lớn: lấy tối thiểu từng này bản ghi mỗi lượt


# An toàn thuốc CHÍNH THỨC (cơ quan quản lý) – trọng số cao.
DRUG_SAFETY_FEEDS: List[FeedConfig] = [
    FeedConfig(
        id="fda_medwatch", name="FDA MedWatch Safety Alerts",
        url="https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/medwatch/rss.xml",
        org="FDA", kind="drug_safety", clinical_area="An toàn thuốc"),
    FeedConfig(
        id="fda_recalls", name="FDA Recalls, Market Withdrawals & Safety Alerts",
        url="https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/recalls/rss.xml",
        org="FDA", kind="drug_safety", clinical_area="An toàn thuốc"),
    FeedConfig(
        id="mhra_dsu", name="MHRA Drug Safety Update",
        url="https://www.gov.uk/drug-safety-update.atom",
        org="MHRA", kind="drug_safety", clinical_area="An toàn thuốc"),
]

# Guideline / nguồn chất lượng cao (phát hiện guideline qua tiêu đề khi quét).
# Các feed hiệp hội/tạp chí chuyên khoa dưới đây ĐÃ kiểm chứng chạy thật (HTTP 200 + XML
# có mục) ngày 2026-06-06. Nhiều khuyến cáo hiệp hội được ĐĂNG trong các tạp chí này
# (vd khuyến cáo EULAR trong Ann Rheum Dis, tuyên bố BTS trong Thorax) -> guideline được
# nhận diện qua tiêu đề (infer_study_type). Feed nào lỗi sẽ ghi Source Log & bỏ qua.
GUIDELINE_FEEDS: List[FeedConfig] = [
    # --- Đa nguồn / cơ quan chính thống ---
    FeedConfig(
        id="cdc_mmwr", name="CDC MMWR (Recommendations & Reports)",
        url="https://tools.cdc.gov/api/v2/resources/media/132036.rss",
        org="CDC", kind="guideline", clinical_area=None),
    FeedConfig(
        id="nejm_current", name="NEJM Current Issue",
        url="https://www.nejm.org/action/showFeed?type=etoc&feed=rss&jc=nejm",
        org="NEJM", kind="guideline", clinical_area=None),
    FeedConfig(
        id="bmj_ebm", name="BMJ Evidence-Based Medicine",
        url="https://ebm.bmj.com/rss/current.xml",
        org="BMJ EBM", kind="guideline", clinical_area=None),
    FeedConfig(
        id="bjgp", name="British Journal of General Practice (ngoại trú/đa khoa)",
        url="https://bjgp.org/rss/current.xml",
        org="BJGP", kind="guideline", clinical_area=None),
    # --- Tim mạch ---
    FeedConfig(
        id="heart_bmj", name="Heart (BMJ/BCS)",
        url="https://heart.bmj.com/rss/current.xml",
        org="Heart (BMJ)", kind="guideline", clinical_area="Tim mạch"),
    FeedConfig(
        id="jacc", name="Journal of the American College of Cardiology (ACC)",
        url="https://www.jacc.org/action/showFeed?type=etoc&feed=rss&jc=jac",
        org="JACC/ACC", kind="guideline", clinical_area="Tim mạch"),
    # --- Tiêu hoá – gan mật ---
    FeedConfig(
        id="gut_bmj", name="Gut (BMJ/BSG)",
        url="https://gut.bmj.com/rss/current.xml",
        org="Gut (BMJ)", kind="guideline", clinical_area="Tiêu hóa - Gan mật"),
    FeedConfig(
        id="fg_bmj", name="Frontline Gastroenterology (BMJ/BSG)",
        url="https://fg.bmj.com/rss/current.xml",
        org="Frontline Gastro (BMJ)", kind="guideline", clinical_area="Tiêu hóa - Gan mật"),
    # --- Hô hấp ---
    FeedConfig(
        id="thorax_bmj", name="Thorax (BMJ/BTS)",
        url="https://thorax.bmj.com/rss/current.xml",
        org="Thorax (BMJ)", kind="guideline", clinical_area="Hô hấp"),
    # --- Cơ xương khớp – thấp khớp ---
    FeedConfig(
        id="ard_bmj", name="Annals of the Rheumatic Diseases (EULAR/BMJ)",
        url="https://ard.bmj.com/rss/current.xml",
        org="Ann Rheum Dis (EULAR)", kind="guideline", clinical_area="Cơ xương khớp"),
    FeedConfig(
        id="rmdopen_bmj", name="RMD Open (EULAR/BMJ)",
        url="https://rmdopen.bmj.com/rss/current.xml",
        org="RMD Open (EULAR)", kind="guideline", clinical_area="Cơ xương khớp"),
    # --- Nội tiết – chuyển hoá ---
    FeedConfig(
        id="bmj_drc", name="BMJ Open Diabetes Research & Care",
        url="https://drc.bmj.com/rss/current.xml",
        org="BMJ Diab Res Care", kind="guideline", clinical_area="Nội tiết - Chuyển hóa"),
    FeedConfig(
        id="diabetologia", name="Diabetologia (EASD)",
        url="https://link.springer.com/search.rss?query=&facet-journal-id=125",
        org="Diabetologia (EASD)", kind="guideline", clinical_area="Nội tiết - Chuyển hóa"),
    # --- Truyền nhiễm ---
    FeedConfig(
        id="sti_bmj", name="Sexually Transmitted Infections (BMJ)",
        url="https://sti.bmj.com/rss/current.xml",
        org="STI (BMJ)", kind="guideline", clinical_area="Nhiễm khuẩn"),
    FeedConfig(
        id="bmj_gh", name="BMJ Global Health",
        url="https://gh.bmj.com/rss/current.xml",
        org="BMJ Global Health", kind="guideline", clinical_area="Nhiễm khuẩn"),
    FeedConfig(
        id="ecdc_threats", name="ECDC Communicable Disease Threats",
        url="https://www.ecdc.europa.eu/en/taxonomy/term/2942/feed",
        org="ECDC", kind="guideline", clinical_area="Nhiễm khuẩn"),
    # --- Cấp cứu ---
    FeedConfig(
        id="emj_bmj", name="Emergency Medicine Journal (BMJ)",
        url="https://emj.bmj.com/rss/current.xml",
        org="EMJ (BMJ)", kind="guideline", clinical_area="Cấp cứu ban đầu"),
    # --- Thần kinh / Đột quỵ ---
    FeedConfig(
        id="jnnp_bmj", name="J Neurology Neurosurgery & Psychiatry (BMJ)",
        url="https://jnnp.bmj.com/rss/current.xml",
        org="JNNP (BMJ)", kind="guideline", clinical_area="Thần kinh/Đột quỵ"),
    FeedConfig(
        id="practneurol_bmj", name="Practical Neurology (BMJ/ABN)",
        url="https://pn.bmj.com/rss/current.xml",
        org="Practical Neurology (BMJ)", kind="guideline", clinical_area="Thần kinh/Đột quỵ"),
    FeedConfig(
        id="svn_bmj", name="Stroke & Vascular Neurology (BMJ/CSA)",
        url="https://svn.bmj.com/rss/current.xml",
        org="Stroke & Vasc Neurology (BMJ)", kind="guideline",
        clinical_area="Thần kinh/Đột quỵ"),
    # --- Thận ---
    FeedConfig(
        id="bmc_nephrol", name="BMC Nephrology",
        url="https://link.springer.com/search.rss?query=&facet-journal-id=12882",
        org="BMC Nephrology", kind="guideline", clinical_area="Thận"),
    FeedConfig(
        id="j_nephrol", name="Journal of Nephrology (Springer/SIN)",
        url="https://link.springer.com/search.rss?query=&facet-journal-id=40620",
        org="J Nephrology", kind="guideline", clinical_area="Thận"),
    # --- Tâm thần ---
    FeedConfig(
        id="bmj_mentalhealth", name="BMJ Mental Health",
        url="https://mentalhealth.bmj.com/rss/current.xml",
        org="BMJ Mental Health", kind="guideline", clinical_area="Tâm thần"),
    # --- Tạp chí tổng quát lớn (đa khoa) ---
    FeedConfig(
        id="jama", name="JAMA (current)",
        url="https://jamanetwork.com/rss/site_3/67.xml",
        org="JAMA", kind="guideline", clinical_area=None),
    FeedConfig(
        id="plos_med", name="PLOS Medicine",
        url="https://journals.plos.org/plosmedicine/feed/atom",
        org="PLOS Medicine", kind="guideline", clinical_area=None),
    FeedConfig(
        id="bmj_recent", name="The BMJ (recent)",
        url="https://www.bmj.com/rss/recent.xml",
        org="The BMJ", kind="guideline", clinical_area=None),
]


# ── FEED RSS KHÔNG ĐỌC ĐƯỢC → LẤY QUA CROSSREF THEO ISSN (đo thật 20/09/2026) ─────────────────────────────────────────
# Đo 29 feed: 14 feed trả 0 mục bằng CHÍNH client của hệ (UA/Accept chuẩn, giãn 4 giây): họ BMJ HTTP 429 hoặc timeout
# ~30 giây (chống bot của HighWire), 3 feed Springer HTTP 406, `bmj_recent` HTTP 403; nhật ký 14 ngày cũng lỗi/ok chập
# chờn. Đổi UA/giãn nhịp không cứu được, và mỗi lần lỗi tốn tới 30 giây. Crossref cho đúng thứ cần (bài MỚI NHẤT của tạp
# chí: DOI + tiêu đề + ngày) ổn định từ mọi mạng. ISSN đã đối chiếu từng cái bằng
# `api.crossref.org/journals/{issn}` (khớp
# tên tạp chí, có bài 60 ngày gần nhất). BMJ dùng ISSN ĐIỆN TỬ 1756-1833 vì bài mới không gắn ISSN in 0959-8138 trong
# Crossref (đo: 0 bài so với 473). Cochrane dùng ISSN điện tử 1465-1858 (ISSN in 1469-493X: 0 bài so với 70).
_CROSSREF_THAY_RSS = {
    "bmj_ebm": "2515-446X", "ard_bmj": "0003-4967", "bmj_drc": "2052-4897", "diabetologia": "0012-186X",
    "sti_bmj": "1368-4973", "bmj_gh": "2059-7908", "emj_bmj": "1472-0205", "jnnp_bmj": "0022-3050",
    "practneurol_bmj": "1474-7758", "svn_bmj": "2059-8688", "bmc_nephrol": "1471-2369", "j_nephrol": "1121-8428",
    "bmj_mentalhealth": "2755-9734", "bmj_recent": "1756-1833",
}
GUIDELINE_FEEDS = [replace(f, issn=_CROSSREF_THAY_RSS[f.id], mode="crossref") if f.id in _CROSSREF_THAY_RSS else f
                   for f in GUIDELINE_FEEDS]

# Tạp chí nơi các HIỆP HỘI ĐĂNG guideline/đồng thuận (ACC/AHA, ESC, ADA, IDSA, AASLD, KDIGO, ATS/ERS, AGS, ACP,
# ASCO/ESMO,
# ASH, AGA/ACG) + Cochrane: hệ không có connector trực tiếp tới trang của các hiệp hội này nên phủ qua nơi họ công bố.
# Guideline được nhận diện qua TIÊU ĐỀ (infer_study_type) và vẫn phải qua cổng xác minh/duyệt như mọi ứng viên — đây
# KHÔNG phải nguồn "đã duyệt".
_JOURNAL_GUIDELINE_SPECS = [
    # (id, tên, tổ chức, lĩnh vực, ISSN)
    ("circulation", "Circulation (AHA)", "Circulation (AHA)", "Tim mạch", "0009-7322"),
    ("eur_heart_j", "European Heart Journal (ESC)", "Eur Heart J (ESC)", "Tim mạch", "0195-668X"),
    ("diabetes_care", "Diabetes Care (ADA)", "Diabetes Care (ADA)", "Nội tiết - Chuyển hóa", "0149-5992"),
    ("cid", "Clinical Infectious Diseases (IDSA)", "Clin Infect Dis (IDSA)", "Nhiễm khuẩn", "1058-4838"),
    ("hepatology", "Hepatology (AASLD)", "Hepatology (AASLD)", "Tiêu hóa - Gan mật", "0270-9139"),
    ("gastroenterology", "Gastroenterology (AGA)", "Gastroenterology (AGA)", "Tiêu hóa - Gan mật", "0016-5085"),
    ("am_j_gastroenterol", "American Journal of Gastroenterology (ACG)", "Am J Gastroenterol (ACG)",
     "Tiêu hóa - Gan mật", "0002-9270"),
    ("kidney_int", "Kidney International (KDIGO)", "Kidney Int (KDIGO)", "Thận", "0085-2538"),
    ("ajrccm", "Am J Respir Crit Care Med (ATS)", "AJRCCM (ATS)", "Hô hấp", "1073-449X"),
    ("eur_respir_j", "European Respiratory Journal (ERS)", "Eur Respir J (ERS)", "Hô hấp", "0903-1936"),
    ("jags", "Journal of the American Geriatrics Society (AGS)", "JAGS (AGS)", "Lão khoa - Đa bệnh lý", "0002-8614"),
    ("ann_intern_med", "Annals of Internal Medicine (ACP)", "Ann Intern Med (ACP)", None, "0003-4819"),
    ("lancet", "The Lancet", "The Lancet", None, "0140-6736"),
    ("cochrane_cdsr", "Cochrane Database of Systematic Reviews", "Cochrane", None, "1465-1858"),
    ("jco", "Journal of Clinical Oncology (ASCO)", "JCO (ASCO)", None, "0732-183X"),
    ("ann_oncol", "Annals of Oncology (ESMO)", "Ann Oncol (ESMO)", None, "0923-7534"),
    ("blood_adv", "Blood Advances (ASH)", "Blood Adv (ASH)", None, "2473-9529"),
]
GUIDELINE_FEEDS = GUIDELINE_FEEDS + [
    FeedConfig(id=i, name=n, url=f"https://api.crossref.org/journals/{issn}", org=o, kind="guideline",
               clinical_area=a, issn=issn, mode="crossref")
    for (i, n, o, a, issn) in _JOURNAL_GUIDELINE_SPECS
]


# ══ LANE GUIDELINE NỐI TRỰC TIẾP, MIỄN PHÍ, KHÔNG KHOÁ (thêm 20/09/2026, theo yêu cầu «kết nối các nguồn guideline»)
# ═══════
# Đo 20/09/2026: RSS chính thức chỉ có ở GOLD · GINA · KDIGO · EASL · AASLD · CDC MMWR (đã nối dưới đây).
# IDSA/ESC/EULAR/ADA/ACC/
# SIGN/BTS/ASH/AAN đều 404, WHO 403, NICE 403, USPSTF không có RSS — nên các nơi đó được phủ qua đường công khai khác
# (Europe PMC,
# WHO IRIS OAI-PMH, kcb.vn, Crossref theo tiêu đề trên tạp chí của hiệp hội). Chi tiết + giới hạn:
# app/sources/guideline_lanes.py.
_UA_EPMC = "https://europepmc.org/search"
GUIDELINE_LANES: list[FeedConfig] = [
    FeedConfig(id="epmc_practice_guideline", name="Europe PMC — loại xuất bản Practice Guideline (MEDLINE, có PMID)",
               url=_UA_EPMC, org="MEDLINE Practice Guideline", kind="guideline", mode="europepmc",
               epmc_query='PUB_TYPE:"Practice Guideline"', is_guideline=True, window_days=45, cap_results=50),
    FeedConfig(id="epmc_uspstf", name="USPSTF — Recommendation Statement (qua Europe PMC)", url=_UA_EPMC,
               org="USPSTF", kind="guideline", mode="europepmc", clinical_area="Dự phòng - Tầm soát",
               epmc_query=('"Preventive Services Task Force" AND "Recommendation Statement" '
                           'AND PUB_TYPE:"Practice Guideline"'),
               is_guideline=True, window_days=730),   # USPSTF ra rất ít: 0 bài trong 365 ngày, 2 bài trong 15 tháng
    FeedConfig(id="epmc_who", name="WHO — guideline trong MEDLINE (qua Europe PMC)", url=_UA_EPMC, org="WHO (MEDLINE)",
               kind="guideline", mode="europepmc",
               epmc_query='AFF:"World Health Organization" AND PUB_TYPE:"Practice Guideline"', is_guideline=True,
               window_days=365),
    FeedConfig(id="epmc_cdc_mmwr_rr", name="CDC MMWR Recommendations & Reports (qua Europe PMC)", url=_UA_EPMC,
               org="CDC MMWR R&R", kind="guideline", mode="europepmc", clinical_area="Nhiễm khuẩn",
               epmc_query='JOURNAL:"MMWR Recomm Rep"', is_guideline=True, window_days=365),
    FeedConfig(id="who_iris", name="WHO IRIS — ấn phẩm guideline mới (OAI-PMH chính thức)",
               url="https://iris.who.int/oai/request", org="WHO IRIS", kind="guideline", mode="who_iris",
               window_days=60),
    FeedConfig(id="kcb_vn", name="Bộ Y tế VN — Hướng dẫn chẩn đoán, điều trị (kcb.vn)", url="https://kcb.vn/phac-do",
               org="Bộ Y tế VN", kind="guideline", mode="kcb_vn"),
    # RSS trực tiếp của hiệp hội/tổ chức (đo 20/09/2026: HTTP 200, có mục thật)
    FeedConfig(id="gold_copd", name="GOLD — Global Initiative for COPD", url="https://goldcopd.org/feed/", org="GOLD",
               kind="guideline", clinical_area="Hô hấp"),
    FeedConfig(id="gina", name="GINA — Global Initiative for Asthma", url="https://ginasthma.org/feed/", org="GINA",
               kind="guideline", clinical_area="Hô hấp"),
    FeedConfig(id="kdigo_news", name="KDIGO — tin/khuyến cáo", url="https://kdigo.org/feed/", org="KDIGO",
               kind="guideline", clinical_area="Thận"),
    FeedConfig(id="easl", name="EASL — European Association for the Study of the Liver", url="https://easl.eu/feed/",
               org="EASL", kind="guideline", clinical_area="Tiêu hóa - Gan mật"),
    FeedConfig(id="aasld_rss", name="AASLD — tin/khuyến cáo", url="https://www.aasld.org/rss.xml", org="AASLD",
               kind="guideline", clinical_area="Tiêu hóa - Gan mật"),
    FeedConfig(id="cdc_mmwr_weekly", name="CDC MMWR Weekly", url="https://tools.cdc.gov/api/v2/resources/media/342778.rss",
               org="CDC MMWR", kind="guideline", clinical_area="Nhiễm khuẩn"),
]

# Khuyến cáo của hiệp hội đăng trên TẠP CHÍ của họ: (id, tên, tổ chức, lĩnh vực, ISSN in|ISSN điện tử, cụm tìm tiêu
# đề, regex tổ chức)
_HIEP_HOI_TREN_TAP_CHI = [
    ("acc_aha_circ", "ACC/AHA — khuyến cáo trên Circulation", "ACC/AHA", "Tim mạch", "0009-7322|1524-4539",
     "ACC AHA guideline", r"\b(?:ACC|AHA|American Heart Association|American College of Cardiology)\b"),
    ("acc_aha_jacc", "ACC/AHA — khuyến cáo trên JACC", "ACC/AHA", "Tim mạch", "0735-1097|1558-3597",
     "ACC AHA guideline", r"\b(?:ACC|AHA|American Heart Association|American College of Cardiology)\b"),
    ("esc_ehj", "ESC — Guidelines trên European Heart Journal", "ESC", "Tim mạch", "0195-668X|1522-9645",
     "ESC Guidelines", r"\bESC\b|European Society of Cardiology"),
    ("ada_standards", "ADA — Standards of Care trên Diabetes Care", "ADA", "Nội tiết - Chuyển hóa",
     "0149-5992|1935-5548",
     "Standards of Care in Diabetes", r"Standards of Care|Consensus Report|\bADA\b|American Diabetes Association"),
    ("idsa_cid", "IDSA — guideline trên Clinical Infectious Diseases", "IDSA", "Nhiễm khuẩn", "1058-4838|1537-6591",
     "IDSA guideline", r"\bIDSA\b|Infectious Diseases Society"),
    ("eular_ard", "EULAR — recommendations trên Ann Rheum Dis", "EULAR", "Cơ xương khớp", "0003-4967|1468-2060",
     "EULAR recommendations", r"\bEULAR\b"),
    ("aasld_hep", "AASLD — practice guidance trên Hepatology", "AASLD", "Tiêu hóa - Gan mật", "0270-9139|1527-3350",
     "AASLD practice guidance", r"\bAASLD\b|American Association for the Study of Liver"),
    ("kdigo_ki", "KDIGO — guideline trên Kidney International", "KDIGO", "Thận", "0085-2538|1523-1755",
     "KDIGO clinical practice guideline", r"\bKDIGO\b|Kidney Disease: Improving Global Outcomes"),
    ("ats_ajrccm", "ATS — guideline trên AJRCCM", "ATS", "Hô hấp", "1073-449X|1535-4970",
     "ATS clinical practice guideline", r"\bATS\b|American Thoracic Society"),
    ("ers_erj", "ERS — guideline trên European Respiratory Journal", "ERS", "Hô hấp", "0903-1936|1399-3003",
     "ERS guidelines", r"\bERS\b|European Respiratory Society"),
    ("bts_thorax", "BTS — guideline trên Thorax", "BTS", "Hô hấp", "0040-6376|1468-3296",
     "BTS guideline", r"\bBTS\b|British Thoracic Society"),
    ("ags_jags", "AGS — Beers/khuyến cáo trên JAGS", "AGS", "Lão khoa - Đa bệnh lý", "0002-8614|1532-5415",
     "American Geriatrics Society Beers Criteria guideline", r"\bAGS\b|American Geriatrics Society"),
    ("acp_annals", "ACP — clinical guideline trên Annals of Internal Medicine", "ACP", None, "0003-4819|1539-3704",
     "American College of Physicians guideline", r"American College of Physicians|\bACP\b"),
    ("asco_jco", "ASCO — guideline trên JCO", "ASCO", None, "0732-183X|1527-7755",
     "ASCO guideline", r"\bASCO\b|American Society of Clinical Oncology"),
    ("esmo_annonc", "ESMO — Clinical Practice Guideline trên Annals of Oncology", "ESMO", None, "0923-7534|1569-8041",
     "ESMO Clinical Practice Guideline", r"\bESMO\b|European Society for Medical Oncology"),
    ("ash_bloodadv", "ASH — guideline trên Blood Advances", "ASH", None, "2473-9529",
     "ASH guidelines", r"\bASH\b|American Society of Hematology"),
    ("aga_gastro", "AGA — guideline trên Gastroenterology", "AGA", "Tiêu hóa - Gan mật", "0016-5085|1528-0012",
     "AGA clinical practice guideline", r"\bAGA\b|American Gastroenterological Association"),
    ("acg_ajg", "ACG — guideline trên Am J Gastroenterol", "ACG", "Tiêu hóa - Gan mật", "0002-9270|1572-0241",
     "ACG clinical guideline", r"\bACG\b|American College of Gastroenterology"),
    ("aan_neurology", "AAN — guideline trên Neurology", "AAN", "Thần kinh/Đột quỵ", "0028-3878|1526-632X",
     "AAN practice guideline", r"\bAAN\b|American Academy of Neurology|Practice (?:Guideline|Advisory|Parameter)"),
    ("aha_stroke", "AHA/ASA — guideline trên Stroke", "AHA/ASA", "Thần kinh/Đột quỵ", "0039-2499|1524-4628",
     "AHA ASA guideline", r"\b(?:AHA|ASA)\b|American Stroke Association|American Heart Association"),
    ("acr_rheum", "ACR — guideline trên Arthritis Rheumatol / Arthritis Care Res", "ACR", "Cơ xương khớp",
     "2326-5191|2326-5205|2151-464X|2151-4658", "ACR guideline", r"\bACR\b|American College of Rheumatology"),
]
GUIDELINE_LANES += [
    FeedConfig(id=i, name=n, url=f"https://api.crossref.org/journals/{issn.split('|')[0]}", org=o, kind="guideline",
               clinical_area=a, mode="crossref_title", issn=issn, title_query=q, title_regex=rg, window_days=365)
    for (i, n, o, a, issn, q, rg) in _HIEP_HOI_TREN_TAP_CHI
]
GUIDELINE_FEEDS = GUIDELINE_FEEDS + GUIDELINE_LANES
