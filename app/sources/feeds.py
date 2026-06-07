"""Danh mục RSS/Atom feed CHÍNH THỐNG (an toàn thuốc + guideline) – TỰ ĐỘNG hoá.

Các URL dưới đây ĐÃ được kiểm tra hoạt động (HTTP 200, trả XML) tại thời điểm tích hợp.
Tuy nhiên feed của cơ quan/nhà xuất bản CÓ THỂ ĐỔI: nếu một feed lỗi, hệ thống ghi
Source Log và bỏ qua (không bịa dữ liệu). Bạn có thể sửa/bổ sung URL tại đây.

Tôn trọng điều khoản sử dụng: chỉ đọc RSS/Atom công khai do tổ chức phát hành.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class FeedConfig:
    id: str
    name: str
    url: str
    org: str
    kind: str               # "drug_safety" | "guideline"
    clinical_area: str | None = None


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
