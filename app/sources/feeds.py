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
