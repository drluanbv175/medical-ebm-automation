"""Connector PubMed / NCBI E-utilities.

Thật: esearch -> efetch (XML). Ở MVP, parse XML tối giản; nếu lỗi/không có email
hoặc USE_MOCK_SOURCES=true thì fallback mock. Lọc ưu tiên SR/MA/RCT/guideline qua
publication type filter trong query.
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional

from defusedxml.ElementTree import fromstring as _safe_fromstring  # chống XXE/billion-laughs

from app.config import settings
from app.sources._fixtures import mock_records_for
from app.sources.base import RawRecord, SourceClient
from app.utils.http import HttpClient
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
EFETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

# Bộ lọc ưu tiên các thiết kế bằng chứng mạnh.
#
# ★ VÁ 2026-07-27 (cổng G0) — TRƯỚC ĐÂY BỘ LỌC NÀY LÀ BẮT BUỘC VỚI MỌI TRUY VẤN, khiến hệ
# MÙ HOÀN TOÀN với nghiên cứu QUAN SÁT. Đo thật trên "outpatient satisfaction hospital":
# 335 hit lọt lưới / 2.916 hit thật — 88% y văn gần đây vô hình. Hệ quả nghiêm trọng cho
# một cổng "phân tích khoảng trống nghiên cứu": một lĩnh vực có 200 cohort và 0 RCT bị báo
# là "THIẾU — chưa có RCT/SR … Khoảng trống lớn — cơ hội nghiên cứu rõ ràng", tức khuyên
# bác sĩ làm một đề tài đã có nhiều người làm. Đề tài hài lòng người bệnh của chính dự án
# này thuộc đúng loại đó. Nay bộ lọc là THAM SỐ: mặc định giữ nguyên (tương thích ngược),
# nhưng caller có thể truyền bộ lọc khác hoặc None để tìm không giới hạn thiết kế.
PUBTYPE_FILTER = (
    '("systematic review"[Publication Type] OR "meta-analysis"[Publication Type] '
    'OR "randomized controlled trial"[Publication Type] OR "guideline"[Publication Type] '
    'OR "practice guideline"[Publication Type])'
)

# ★ LẤY ĐỦ RỒI CHỌN MẠNH NHẤT (vá 25/09/2026, audit/15 §7sexies). Trước đây `_live_search` sắp
# PubMed theo NGÀY rồi cắt `max_results` bài đầu ⇒ trả «10 bài mới nhất», không phải «10 bài mạnh
# nhất». Đo sống 24/09 trên 6 bệnh ngoại trú (THA · suy tim · rung nhĩ · ĐTĐ2 · COPD · CKD): 0/15
# guideline chuẩn 2023–2026 lọt vào kết quả; 4/6 chủ đề có 7–8/10 bài tier C (suy tim khớp 23.502
# bài nên 10 bài mới nhất gần như luôn là tổng quan nhỏ vừa lên mạng). Cùng lỗi đã vá ở
# `surveillance_scan.py` (phương án B, 24/09). Nay khi dùng bộ lọc mặc định: lấy một VÙNG rộng
# (VUNG_MOI_NHAT bài mới nhất + VUNG_GUIDELINE guideline sát chủ đề nhất theo relevance trong
# NAM_GUIDELINE năm, hoặc trong cửa sổ since_date nếu có), xếp theo độ mạnh rồi mới cắt.
# Tắt bằng PUBMED_CHON_MANH_NHAT=false (quay về hành vi cũ).
VUNG_MOI_NHAT = 100
VUNG_GUIDELINE = 20
NAM_GUIDELINE = 5
# «Standards of Care»[ti]: các chương ADA Standards of Care in Diabetes được PubMed gắn nhãn «Review»,
# KHÔNG phải «Guideline» (đo 25/09/2026, PMID 41358900) ⇒ chỉ dựa nhãn loại xuất bản sẽ bỏ sót chúng.
GUIDELINE_FILTER = ('("guideline"[Publication Type] OR "practice guideline"[Publication Type] '
                    'OR "consensus statement"[Publication Type] OR "standards of care"[Title])')


# LÀN GUIDELINE SỐNG theo chuỗi (thêm 25/09/2026). ADA Standards of Care in Diabetes ra MỘT ấn bản mỗi
# năm, chia ~17 chương. Tiêu đề chương không ghi «type 2», nên làn guideline theo relevance bỏ sót cả
# chương 9 «Pharmacologic Approaches to Glycemic Treatment» (đo sống: không lọt 20 bài đầu cho truy vấn
# «type 2 diabetes»; chuẩn vàng trượt nhóm này). Làn này lấy thẳng chuỗi, chỉ giữ ẤN BẢN MỚI NHẤT,
# bỏ đính chính/tóm tắt sửa đổi/lời giới thiệu, lấy SO_CHUONG_CHUOI chương sát nhất theo relevance.
_CHUOI_GUIDELINE_SONG = {
    "diabetes": '"standards of care"[Title] AND diabetes[Title] AND "Diabetes care"[Journal]',
    "diabetic": '"standards of care"[Title] AND diabetes[Title] AND "Diabetes care"[Journal]',
}
SO_CHUONG_CHUOI = 2
_VUNG_CHUOI = 40
_MAU_AN_BAN = re.compile(r"standards of care in diabetes\W*(\d{4})", re.I)
_KHONG_PHAI_CHUONG = re.compile(
    r"^\s*(erratum|correction|summary of revisions|introduction|\d+\.\s*diabetes advocacy)", re.I)


def chon_chuong_moi_nhat(records: List[RawRecord], thu_tu: List[str],
                         so: int = SO_CHUONG_CHUOI) -> List[str]:
    """PMID các chương thuộc ẤN BẢN MỚI NHẤT của chuỗi, theo thứ tự relevance `thu_tu`, tối đa `so`.
    Năm ấn bản đọc từ TIÊU ĐỀ («…Standards of Care in Diabetes—2026»), không đoán theo năm hiện tại."""
    theo_pmid = {r.pmid: r for r in records if r.pmid in set(thu_tu)}
    an_ban: Dict[str, int] = {}
    for pmid, r in theo_pmid.items():
        m = _MAU_AN_BAN.search(r.title or "")
        if m and not _KHONG_PHAI_CHUONG.search(r.title or ""):
            an_ban[pmid] = int(m.group(1))
    if not an_ban:
        return []
    moi_nhat = max(an_ban.values())
    return [p for p in thu_tu if an_ban.get(p) == moi_nhat][:so]


def hang_do_manh(pubtypes: List[str], tieu_de: str = "") -> int:
    """Hạng độ mạnh theo LOẠI XUẤT BẢN THẬT của PubMed (nhỏ = mạnh hơn).

    0 guideline/practice guideline/consensus statement · 1 systematic review/meta-analysis ·
    2 RCT · 3 khác. Bài đã bị rút (Retracted Publication) luôn xếp CUỐI (9) — vẫn trả về để
    tầng kiểm rút bài phía sau gắn cờ, KHÔNG âm thầm vứt đi."""
    j = " | ".join(p.lower() for p in pubtypes)
    if "retracted publication" in j:
        return 9
    if "guideline" in j or "consensus statement" in j:
        return 0
    t = (tieu_de or "").lower()
    if ("standards of care" in t and "published erratum" not in j
            and not t.startswith(("correction", "erratum"))):
        return 0  # ADA Standards of Care: PubMed gắn «Review» nhưng bản chất là guideline
    if "meta-analysis" in j or "systematic review" in j:
        return 1
    if "randomized controlled trial" in j:
        return 2
    return 3


_TU_BO_QUA = {"guideline", "guidelines", "management", "treatment", "therapy", "and", "the",
              "for", "with", "adult", "adults", "patients", "clinical", "practice"}


def _tu_chu_de(query: str) -> List[str]:
    """Từ khoá CHỦ ĐỀ của truy vấn (bỏ thẻ PubMed, toán tử, từ chung chung như «guideline»)."""
    import re
    q = re.sub(r"\[[^\]]*\]", " ", query or "").lower()
    return [t for t in re.findall(r"[a-z0-9]+", q)
            if len(t) >= 3 and t not in _TU_BO_QUA and t not in {"not", "or"}]


# Đồng nghĩa khi so TIÊU ĐỀ (chỉ các cặp phổ biến ở ngoại trú, đã gặp thật): guideline Mỹ 2025 về
# huyết áp ghi «High Blood Pressure», không ghi «hypertension»; GOLD/ERS ghi tên đầy đủ của COPD.
_DONG_NGHIA_TIEU_DE = {
    "hypertension": ("hypertension", "blood pressure"),
    "copd": ("copd", "chronic obstructive"),
    "ckd": ("ckd", "chronic kidney"),
    "afib": ("atrial fibrillation",),
}


def _tieu_de_sat(tieu_de: str, tu: List[str]) -> bool:
    return bool(tu) and all(any(d in tieu_de for d in _DONG_NGHIA_TIEU_DE.get(t, (t,))) for t in tu)


def xep_theo_do_manh(records: List[RawRecord], query: str = "",
                     thu_tu_lien_quan: Optional[Dict[str, int]] = None,
                     sat_chu_de_san: Optional[set] = None) -> List[RawRecord]:
    """Xếp ổn định theo: hạng độ mạnh ↑ → TIÊU ĐỀ chứa đủ từ khoá chủ đề (sát chủ đề trước) →
    thứ tự relevance của PubMed (làn guideline) → NĂM ↓ → thứ tự gốc.

    Vì sao «sát chủ đề» đứng trước «năm» (đo 25/09/2026): xếp năm trước kéo lên các guideline
    2026 LẠC ĐỀ chỉ nhắc từ khoá trong tóm tắt (lọc máu, migraine, CKD ở mèo cho truy vấn tăng
    huyết áp) và đẩy guideline suy tim AHA/ACC/HFSA 2022 xuống cuối.

    `sat_chu_de_san`: PMID đã được chọn VÌ chủ đề (chương chuỗi guideline sống) ⇒ coi là sát chủ đề
    dù tiêu đề không chứa đủ từ khoá (chương ADA không ghi «type 2»)."""
    tu = _tu_chu_de(query)
    lien_quan = thu_tu_lien_quan or {}
    san = sat_chu_de_san or set()

    def khoa(cap):
        i, r = cap
        nam = str(r.publication_date or "")[:4]
        tieu_de = (r.title or "").lower()
        sat = r.pmid in san or _tieu_de_sat(tieu_de, tu)
        return (hang_do_manh((r.raw or {}).get("publication_types") or [], r.title or ""),
                0 if sat else 1,
                lien_quan.get(r.pmid or "", len(lien_quan) + 1),
                -(int(nam) if nam.isdigit() else 0), i)
    return [r for _, r in sorted(enumerate(records), key=khoa)]


# Bộ lọc nghiên cứu QUAN SÁT — dùng MeSH thay vì [Publication Type] vì PubMed KHÔNG có
# publication type cho cohort/case-control/cross-sectional (đó là lý do bộ lọc cũ không
# thể tìm ra chúng dù có muốn).
OBSERVATIONAL_FILTER = (
    '("Cohort Studies"[MeSH] OR "Case-Control Studies"[MeSH] '
    'OR "Cross-Sectional Studies"[MeSH] OR "Observational Study"[Publication Type] '
    'OR "Prospective Studies"[MeSH] OR "Retrospective Studies"[MeSH])'
)


def _own_article_doi(art: ET.Element) -> Optional[str]:
    """Lấy DOI CỦA CHÍNH BÀI trong một phần tử `<PubmedArticle>`.

    ★ VÁ 2026-08-14 — TRẢ VỀ DOI CỦA BÀI KHÁC. Hai chỗ parse (`_parse_efetch`,
    `_parse_metadata_xml`) trước đây dùng `art.findall(".//ArticleId")`: trục
    `.//` quét TOÀN BỘ cây con nên với tới cả
    `PubmedData/ReferenceList/Reference/ArticleIdList/ArticleId` — tức DOI của
    những bài nằm trong DANH MỤC THAM KHẢO. Vòng lặp lại KHÔNG `break`, nên giá
    trị bị GHI ĐÈ tới cuối và bên thắng cuộc là tài liệu tham khảo CUỐI CÙNG
    (không phải cái đầu tiên như thoạt tưởng).

    Đo thật trên PMID 30267080 (Choi và cs., "Risk of Hepatocellular Carcinoma
    in Patients Treated With Entecavir vs Tenofovir…", JAMA Oncology 2019):
    parser cũ trả `10.1159/000096313` — tiền tố 10.1159 là nhà xuất bản Karger,
    thuộc tham khảo thứ 31 (PMID 17164558) — thay vì DOI thật
    `10.1001/jamaoncol.2018.4070`. Quét 10 PMID có thật: 3 bài sai, và đều là
    những bài PubMed có trả kèm `<ReferenceList>` chứa DOI. Đó là lý do lỗi ẩn
    mình lâu: bản ghi không kèm ReferenceList vẫn cho DOI đúng.

    Vì sao đáng sửa: DOI này chảy thẳng vào cổng A12
    (`tools/check_citations.py`, `tools/check_citation_retraction.py`) để đối
    chiếu Crossref. DOI của bài KHÁC làm việc đối chiếu báo "không khớp" trên
    một trích dẫn lành — hoặc tệ hơn, khớp trót lọt với một bài không liên quan.
    Báo động giả nặng hơn không kiểm (xem CLAUDE.md).

    Chỉ đọc hai vị trí của CHÍNH bài, TUYỆT ĐỐI không dùng trục `.//`:
      1) `PubmedData/ArticleIdList` — vị trí chuẩn của bộ định danh chính bài;
      2) `MedlineCitation/Article/ELocationID[@EIdType="doi"]` — dự phòng cho
         bản ghi thiếu (1); bỏ qua mục `ValidYN="N"` vì đó là DOI mà chính
         PubMed đánh dấu SAI.
    Lấy giá trị hợp lệ ĐẦU TIÊN rồi dừng — không để ghi đè như trước.
    """
    for el in art.findall("PubmedData/ArticleIdList/ArticleId"):
        if el.get("IdType") == "doi":
            value = (el.text or "").strip()
            if value:
                return value
    for el in art.findall("MedlineCitation/Article/ELocationID"):
        if el.get("EIdType") == "doi" and (el.get("ValidYN") or "Y").upper() != "N":
            value = (el.text or "").strip()
            if value:
                return value
    return None


def _full_text(elem: Optional[ET.Element]) -> str:
    """Nối TOÀN BỘ văn bản trong một phần tử XML, kể cả bên trong thẻ con.

    SỬA 2026-09-04 (Workflow đối kháng đa-agent vòng 2, phát hiện HIGH) —
    `.text`/`findtext()` chỉ trả phần văn bản đứng TRƯỚC thẻ con ĐẦU TIÊN.
    XML PubMed thường chứa thẻ lồng (`<i>`/`<b>`/`<sub>`/`<sup>`) ngay trong
    ArticleTitle/AbstractText cho tên gen/thuốc/công thức hoá học — xác nhận
    bằng thực nghiệm: tiêu đề "Test article about <i>BRCA1</i> mutation" đọc
    bằng `.text` chỉ ra "Test article about " (mất "BRCA1 mutation"); abstract
    có `<b>significant</b> reduction of 45% (95% CI 30-60%)` chỉ ra "We found
    a " — MẤT TRẮNG toàn bộ số liệu, không có ngoại lệ nào báo. Tiêu đề/abstract
    cụt đi thẳng vào cổng kiểm trích dẫn A12 và bị `kiem_so_lieu.py` đọc nhầm
    thành "⚪ tóm tắt không nêu" (an toàn nhưng sai) thay vì so được số thật.
    `itertext()` duyệt cả thẻ con nên không mất nội dung."""
    if elem is None:
        return ""
    return "".join(elem.itertext())


def _own_article_pmid(art: ET.Element) -> Optional[str]:
    """Lấy PMID CỦA CHÍNH BÀI — cùng họ lỗi với `_own_article_doi()`.

    `.//PMID` cũng chạm được `MedlineCitation/CommentsCorrectionsList/
    CommentsCorrections/PMID` (PMID của thông báo rút bài, bài bình luận…).
    Hiện `findtext` trả bản ghi ĐẦU TIÊN theo thứ tự tài liệu nên vẫn đúng —
    `MedlineCitation/PMID` đứng trước — tức đây là siết phòng xa, KHÔNG phải
    vá một lỗi đang xảy ra. Vẫn giữ `.//PMID` làm đường lui để không thể hồi
    quy nếu gặp bản ghi có cấu trúc lạ.
    """
    return art.findtext("MedlineCitation/PMID") or art.findtext(".//PMID")


# SỬA 2026-09-04 (Workflow đối kháng đa-agent vòng 2): dò trang CHẶN của NCBI dùng
# CHUNG cho mọi hàm parse tiêu thụ phản hồi efetch. Trước bản vá, chỉ
# `_parse_retraction_xml()` có bước dò này (thêm 12/08/2026) — `_parse_metadata_xml()`
# (hàm chị em, cùng tiêu thụ MỘT response trong `check_citations()`) KHÔNG có, nên khi
# NCBI trả trang "WWW Error Blocked Diagnostic" (HTTP 200 hợp lệ, không lỗi parse XML),
# `_parse_metadata_xml()` parse "thành công" ra 0 <PubmedArticle> rồi gán MỌI PMID
# status='unresolved' kèm lý do "PMID có thể sai/không tồn tại" — đúng loại báo động
# giả mà bản vá 12/08 mô tả cho hàm chị em, chỉ là ở một hàm khác chưa được vá theo.
# Trích thành hàm dùng chung để một bản vá tương lai không còn bị bỏ sót kiểu này
# (bài học BH39: thêm luật ở một chỗ phải lan sang mọi nơi tiêu thụ cùng dữ liệu).
def _trang_chan_ncbi(xml_text: str) -> bool:
    """True nếu response là trang HTML chặn của NCBI, không phải XML dữ liệu thật."""
    dau = (xml_text or "").lstrip()[:400].lower()
    return dau.startswith("<!doctype html") or "blocked diagnostic" in dau


_LY_DO_NCBI_CHAN = (
    "NCBI đang CHẶN máy/IP này (WWW Error Blocked Diagnostic). Đăng ký "
    "NCBI_API_KEY miễn phí và đặt vào .env để nâng hạn mức; KHÔNG kết luận gì về PMID."
)


class PubMedClient(SourceClient):
    name = "pubmed"
    endpoint = ESEARCH

    def __init__(self) -> None:
        super().__init__()
        self.http = HttpClient()

    def search(self, query: str, clinical_area: Optional[str] = None,
               max_results: int = 20, since_date: Optional[str] = None,
               pubtype_filter: Optional[str] = PUBTYPE_FILTER) -> List[RawRecord]:
        """pubtype_filter: None = KHÔNG giới hạn thiết kế (xem chú thích PUBTYPE_FILTER)."""
        if self.use_mock or not settings.ncbi_email:
            logger.info("[pubmed] dùng mock (use_mock=%s, có email=%s)",
                        self.use_mock, bool(settings.ncbi_email))
            return mock_records_for(self.name, query, clinical_area, max_results)
        try:
            return self._live_search(query, clinical_area, max_results, since_date,
                                     pubtype_filter)
        except Exception as exc:  # pragma: no cover - lỗi mạng thực tế
            logger.warning("[pubmed] lỗi gọi thật (live) — BỎ QUA nguồn này, KHÔNG bịa mock: %s", exc)
            return []

    def count_hits(self, query: str, since_date: Optional[str] = None,
                   pubtype_filter: Optional[str] = PUBTYPE_FILTER) -> Optional[int]:
        """SỐ BÀI THẬT khớp truy vấn (esearch Count), KHÔNG phải số bài lấy về.

        ★ VÁ 2026-07-27 (cổng G0): analyze_evidence_gaps() trước đây đếm len(danh sách đã
        lấy) — mà danh sách đó bị chặn trần bởi --max-results (mặc định 15). Đo thật: một
        chủ đề có 34 SR/MA và 16 RCT được ghi vào checkpoint là 15/15. Ngưỡng phân loại
        (n_sr>=3 → "MẠNH", n_rct>=2 …) vì thế BÃO HÒA với gần như mọi chủ đề, và hệ không
        thể phân biệt 3 SR với 3.400 SR. Một cổng có nhiệm vụ nói "khoảng trống nghiên cứu
        ở đâu" mà đếm sai bậc độ lớn thì kết luận của nó không dùng được.
        Trả None nếu không tra được (mock/không mạng/không email) — caller PHẢI phân biệt
        "không biết" với "bằng 0", đúng nguyên tắc không bịa của dự án."""
        if self.use_mock or not settings.ncbi_email:
            return None
        term = f"({query}) AND {pubtype_filter}" if pubtype_filter else f"({query})"
        params = {"db": "pubmed", "term": term, "retmax": 0, "retmode": "json",
                  "email": settings.ncbi_email}
        if since_date:
            params.update(datetype="pdat", mindate=since_date.replace("-", "/"),
                          maxdate="3000/01/01")
        if settings.ncbi_api_key:
            params["api_key"] = settings.ncbi_api_key
        try:
            data = self.http.get_json(ESEARCH, params=params)
            # VÁ 2026-07-27 (kiểm định độc lập): mặc định 0 khi THIẾU khóa "count" là
            # fail-OPEN ngay tại hàm mà lý do tồn tại là "phân biệt KHÔNG BIẾT với BẰNG 0".
            # E-utilities trả {"esearchresult": {"ERROR": "..."}} khi truy vấn hỏng — khi đó
            # 0 nghĩa là "không tra được", không phải "không có bài nào".
            _res = data.get("esearchresult")
            if not isinstance(_res, dict) or "count" not in _res:
                logger.warning("[pubmed] esearch không trả 'count' (%s) — trả None, KHÔNG suy ra 0",
                               str(_res)[:120])
                return None
            return int(_res["count"])
        except Exception as exc:  # pragma: no cover - lỗi mạng thực tế
            logger.warning("[pubmed] count_hits lỗi — trả None (KHÔNG suy ra 0): %s", exc)
            return None

    # -- Live ------------------------------------------------------------
    def _live_search(self, query: str, clinical_area: Optional[str],
                     max_results: int, since_date: Optional[str] = None,
                     pubtype_filter: Optional[str] = PUBTYPE_FILTER) -> List[RawRecord]:
        term = f"({query}) AND {pubtype_filter}" if pubtype_filter else f"({query})"
        chon_manh = settings.pubmed_chon_manh_nhat and pubtype_filter == PUBTYPE_FILTER
        params = {
            "db": "pubmed", "term": term,
            "retmax": max(max_results, VUNG_MOI_NHAT) if chon_manh else max_results,
            "retmode": "json", "email": settings.ncbi_email, "sort": "date",
        }
        # Lọc theo ngày xuất bản: chỉ bài MỚI kể từ since_date.
        if since_date:
            params["datetype"] = "pdat"
            params["mindate"] = since_date.replace("-", "/")
            params["maxdate"] = "3000/01/01"
        if settings.ncbi_api_key:
            params["api_key"] = settings.ncbi_api_key
        data = self.http.get_json(ESEARCH, params=params)
        ids = data.get("esearchresult", {}).get("idlist", [])
        lien_quan: Dict[str, int] = {}
        ids_chuoi: List[str] = []
        chi_tu_chuoi: set = set()
        if chon_manh:
            ids_gl = self._ids_guideline(query, since_date)
            lien_quan = {pmid: k for k, pmid in enumerate(ids_gl)}
            ids_chuoi = self._ids_chuoi_song(query, since_date)
            chi_tu_chuoi = set(ids_chuoi) - set(ids_gl) - set(ids)
            ids = list(dict.fromkeys(ids_gl + list(ids) + ids_chuoi))  # bỏ trùng, guideline trước
        if not ids:
            return []
        fetch_params = {
            "db": "pubmed", "id": ",".join(ids), "retmode": "xml",
            "email": settings.ncbi_email,
        }
        if settings.ncbi_api_key:
            fetch_params["api_key"] = settings.ncbi_api_key
        xml_text = self.http.get_text(EFETCH, params=fetch_params)
        self.save_raw(query, xml_text)
        records = self._parse_efetch(xml_text, clinical_area, query)
        if chon_manh:
            chon = set(chon_chuong_moi_nhat(records, ids_chuoi))
            # Chương cũ/không được chọn mà CHỈ đến từ làn chuỗi thì bỏ, để ~40 chương không chiếm top.
            records = [r for r in records if r.pmid not in chi_tu_chuoi or r.pmid in chon]
            records = xep_theo_do_manh(records, query, lien_quan, chon)[:max_results]
        return records

    def _ids_chuoi_song(self, query: str, since_date: Optional[str]) -> List[str]:
        """Làn guideline sống theo chuỗi (hiện có ADA Standards of Care) — chỉ chạy khi truy vấn có từ
        chủ đề khớp khoá trong `_CHUOI_GUIDELINE_SONG`. Lỗi ⇒ [] kèm log (làn phụ)."""
        from datetime import date
        tu = set(_tu_chu_de(query))
        ra: List[str] = []
        for loc in dict.fromkeys(v for k, v in _CHUOI_GUIDELINE_SONG.items() if k in tu):
            params = {"db": "pubmed", "term": loc, "retmax": _VUNG_CHUOI, "retmode": "json",
                      "email": settings.ncbi_email, "sort": "relevance", "datetype": "pdat",
                      "maxdate": "3000/01/01",
                      "mindate": (since_date.replace("-", "/") if since_date
                                  else f"{date.today().year - 1}/01/01")}
            if settings.ncbi_api_key:
                params["api_key"] = settings.ncbi_api_key
            try:
                data = self.http.get_json(ESEARCH, params=params)
                ra += list(data.get("esearchresult", {}).get("idlist", []))
            except Exception as exc:  # pragma: no cover - lỗi mạng thực tế
                logger.warning("[pubmed] làn chuỗi guideline sống lỗi: %s", exc)
        return list(dict.fromkeys(ra))

    def _ids_guideline(self, query: str, since_date: Optional[str]) -> List[str]:
        """Làn guideline: VUNG_GUIDELINE bài guideline/consensus SÁT CHỦ ĐỀ NHẤT (sort=relevance)
        trong cửa sổ since_date, hoặc NAM_GUIDELINE năm gần nhất. Lỗi ⇒ [] (làn phụ, không được
        làm hỏng làn chính) — nhưng GHI LOG, không im lặng."""
        from datetime import date
        params = {"db": "pubmed", "term": f"({query}) AND {GUIDELINE_FILTER}",
                  "retmax": VUNG_GUIDELINE, "retmode": "json", "email": settings.ncbi_email,
                  "sort": "relevance", "datetype": "pdat", "maxdate": "3000/01/01",
                  "mindate": (since_date.replace("-", "/") if since_date
                              else f"{date.today().year - NAM_GUIDELINE}/01/01")}
        if settings.ncbi_api_key:
            params["api_key"] = settings.ncbi_api_key
        try:
            data = self.http.get_json(ESEARCH, params=params)
            return list(data.get("esearchresult", {}).get("idlist", []))
        except Exception as exc:  # pragma: no cover - lỗi mạng thực tế
            logger.warning("[pubmed] làn guideline lỗi — chỉ dùng làn mới nhất: %s", exc)
            return []

    def _parse_efetch(self, xml_text: str, clinical_area: Optional[str],
                      query: str) -> List[RawRecord]:
        records: List[RawRecord] = []
        try:
            root = _safe_fromstring(xml_text)
        except (ET.ParseError, ValueError) as exc:
            logger.warning("[pubmed] parse XML lỗi/không an toàn: %s", exc)
            return records
        for art in root.findall(".//PubmedArticle"):
            pmid = _own_article_pmid(art)
            title = _full_text(art.find(".//ArticleTitle"))
            abstract = " ".join(_full_text(t) for t in art.findall(".//AbstractText"))
            journal = art.findtext(".//Journal/Title")
            year = art.findtext(".//PubDate/Year")
            pubtypes = [pt.text for pt in art.findall(".//PublicationType") if pt.text]
            mesh = [m.text for m in art.findall(".//MeshHeading/DescriptorName") if m.text]
            # DOI của CHÍNH bài — KHÔNG quét `.//` để khỏi nhặt phải DOI trong
            # danh mục tham khảo (xem `_own_article_doi`, vá 2026-08-14).
            doi = _own_article_doi(art)
            authors = ", ".join(
                f"{a.findtext('LastName') or ''} {a.findtext('Initials') or ''}".strip()
                for a in art.findall(".//Author")[:5]
            )
            records.append(RawRecord(
                source=self.name, source_type="article", title=title,
                authors=authors or None, journal_or_organization=journal,
                publication_date=year, doi=doi, pmid=pmid, abstract=abstract or None,
                document_type=pubtypes[0] if pubtypes else None,
                study_type=self._infer_study_type(pubtypes),
                clinical_area=clinical_area, mesh_terms=mesh,
                url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else None,
                ingest_query=query, api_endpoint=EFETCH,
                raw={"publication_types": pubtypes},
            ))
        return records

    # -- Kiểm rút bài CHỦ ĐỘNG (vá 2026-07-15) ---------------------------
    def check_retraction_status(self, pmids: List[str]) -> Dict[str, dict]:
        """Tra cứu CHỦ ĐỘNG trạng thái rút bài/expression-of-concern THẬT từ
        PubMed cho danh sách PMID — khác `app/evidence/retraction_monitor.py`
        (nhánh mồ côi, xem CLAUDE.md) vốn chỉ đọc chữ "retracted"/"withdrawn"
        ĐÃ CÓ SẴN trong metadata truyền vào, không tự tra cứu gì. Xác nhận
        bằng test thật với PMID 9500320 (Wakefield 1998, Lancet — rút 2010):
        PubMed đánh dấu qua CẢ HAI `<PublicationType>Retracted Publication</
        PublicationType>` VÀ `<CommentsCorrections RefType="RetractionIn">`
        (kèm PMID/trích dẫn thông báo rút bài) — hàm này đọc cả hai để không
        bỏ sót trường hợp chỉ có một trong hai (đã gặp khi phiên bản DTD PubMed
        đổi cách gắn cờ theo thời gian).

        Trả {pmid: {"status": ..., ...}}, status một trong:
          "retracted"              — CommentsCorrections RefType="RetractionIn"
                                      hoặc PublicationType="Retracted Publication"
          "expression_of_concern"  — RefType="ExpressionOfConcernIn" (cảnh báo nhẹ hơn)
          "ok"                     — tra được, không có tín hiệu trên
          "unresolved"             — PubMed trả XML hợp lệ nhưng KHÔNG có bản ghi
                                      cho PMID này (nghi trích dẫn ma)
          "unknown_mock_or_no_email" — KHÔNG tra cứu thật được (mock/thiếu NCBI_EMAIL/
                                      lỗi mạng) — PHẢI coi là CHƯA XÁC MINH, không phải "ok".
          "unknown_fetch_error"    — gọi được nhưng KHÔNG đọc được phản hồi (mạng cắt
                                      giữa chừng, NCBI trả trang chặn thay vì XML).
                                      PHẢI coi là CHƯA XÁC MINH — KHÁC "unresolved":
                                      ở đây ta không biết gì cả, không có cơ sở nghi
                                      trích dẫn ma. Tách ra 12/08/2026 sau khi trạng
                                      thái gộp gây báo động giả cho 18 PMID có thật.
        """
        if not pmids:
            return {}
        if self.use_mock or not settings.ncbi_email:
            reason = ("USE_MOCK_SOURCES=true" if self.use_mock else "thiếu NCBI_EMAIL")
            return {
                pmid: {"status": "unknown_mock_or_no_email",
                       "reason": f"{reason} — KHÔNG tra cứu PubMed thật, không được coi là 'ok'"}
                for pmid in pmids
            }
        params = {"db": "pubmed", "id": ",".join(pmids), "retmode": "xml", "email": settings.ncbi_email}
        if settings.ncbi_api_key:
            params["api_key"] = settings.ncbi_api_key
        try:
            # SỬA 2026-07-22 (vòng lặp kiểm tra-hoàn thiện vòng 10, phát hiện HIGH):
            # use_cache=False bắt buộc — self.http mặc định cache 24h (settings.http_cache_ttl),
            # phù hợp cho search() (tra cứu y văn thường) nhưng SAI cho kiểm rút bài: một bài bị
            # rút NGAY SAU lần kiểm trước (trong cửa sổ 24h) sẽ không bị phát hiện cho tới khi
            # cache hết hạn, dù receipt vẫn ghi checked_at_utc MỚI tạo cảm giác đã kiểm tra live.
            xml_text = self.http.get_text(EFETCH, params=params, use_cache=False)
        except Exception as exc:  # pragma: no cover - lỗi mạng thực tế
            logger.warning("[pubmed] check_retraction_status lỗi gọi thật: %s", exc)
            return {
                pmid: {"status": "unknown_mock_or_no_email", "reason": f"lỗi gọi PubMed: {exc}"}
                for pmid in pmids
            }
        return self._parse_retraction_xml(xml_text, pmids)

    @staticmethod
    def _parse_retraction_xml(xml_text: str, requested_pmids: List[str]) -> Dict[str, dict]:
        results: Dict[str, dict] = {}

        # NCBI đôi lúc trả HTTP 200 kèm TRANG HTML "WWW Error Blocked Diagnostic"
        # thay vì XML — hay gặp khi gọi nhiều từ một IP dùng chung (mạng bệnh viện)
        # mà không có NCBI_API_KEY. Nhận ra sớm để nói đúng nguyên nhân và cách sửa,
        # thay vì để nó rơi xuống nhánh "parse XML lỗi" mơ hồ (thêm 12/08/2026; trích
        # thành hàm dùng chung `_trang_chan_ncbi()` 04/09/2026 — xem comment tại đó).
        if _trang_chan_ncbi(xml_text):
            logger.warning("[pubmed] NCBI trả trang CHẶN thay vì XML — cần NCBI_API_KEY")
            return {pmid: {"status": "unknown_fetch_error", "reason": _LY_DO_NCBI_CHAN}
                    for pmid in requested_pmids}

        try:
            root = _safe_fromstring(xml_text)
        except (ET.ParseError, ValueError) as exc:
            # SỬA 12/08/2026: trước đây trả "unresolved" — mà theo docstring của
            # check_retraction_status(), "unresolved" nghĩa là PUBMED KHÔNG CÓ bản
            # ghi cho PMID này, tức NGHI TRÍCH DẪN MA. Lỗi parse XML là chuyện hoàn
            # toàn khác: response bị cắt giữa chừng do mạng chập chờn, hoặc NCBI trả
            # trang chặn thay vì XML. Gộp hai thứ vào một status khiến công cụ gọi
            # nó báo "nghi trích dẫn ma" cho CẢ 18 PMID vốn vừa được chính PubMed
            # xác minh là có thật ở bước trước — báo động giả hàng loạt, và loại báo
            # động này còn tệ hơn không kiểm vì nó làm người ta mất tin vào cảnh báo
            # thật. Nay tách thành status riêng, và caller phải coi là CHƯA KIỂM.
            logger.warning("[pubmed] parse XML (retraction) lỗi/không an toàn: %s", exc)
            return {pmid: {"status": "unknown_fetch_error",
                           "reason": f"không đọc được phản hồi PubMed ({exc}) — "
                                     f"KHÔNG kết luận gì về PMID này"}
                    for pmid in requested_pmids}
        found = set()
        for art in root.findall(".//PubmedArticle"):
            pmid = art.findtext(".//PMID")
            if not pmid:
                continue
            found.add(pmid)
            pubtypes = {pt.text for pt in art.findall(".//PublicationType") if pt.text}
            retraction_notice = None
            retraction_notices = []  # TẤT CẢ thông báo (thêm 20/09/2026: dấu vân tay sổ miễn trừ phải phủ đủ)
            eoc_notice = None
            for cc in art.findall(".//CommentsCorrectionsList/CommentsCorrections"):
                ref_type = cc.get("RefType", "")
                notice = {"pmid": cc.findtext("PMID"), "citation": cc.findtext("RefSource")}
                if ref_type == "RetractionIn":
                    retraction_notice = notice
                    retraction_notices.append(notice)
                elif ref_type == "ExpressionOfConcernIn":
                    eoc_notice = notice
            if "Retracted Publication" in pubtypes or retraction_notice:
                results[pmid] = {"status": "retracted", "retraction_notice": retraction_notice,
                                 "retraction_notices": retraction_notices}
            elif "Expression of Concern" in pubtypes or eoc_notice:
                results[pmid] = {"status": "expression_of_concern",
                                  "expression_of_concern_notice": eoc_notice}
            else:
                results[pmid] = {"status": "ok"}
        for pmid in requested_pmids:
            if pmid not in found:
                results[pmid] = {"status": "unresolved",
                                  # SUA 2026-07-22 (vong lap kiem tra-hoan thien vong 10, phat hien
                                  # LOW): thong diep cu ngu y "PMID sai" - nhung neu PubMed tra HTTP
                                  # 200 hop le ma KHONG chua <PubmedArticle> nao cho CA LO (loi tang
                                  # API/NCBI), MOI pmid deu roi vao day du khong sai. Van chan dung
                                  # (fail-closed), chi lam ro nguyen nhan co the.
                                  "reason": "PubMed không trả về bản ghi cho PMID này trong lô truy vấn "
                                            "(PMID có thể sai/không tồn tại, HOẶC lỗi tầng API khiến "
                                            "cả lô bị bỏ sót — nghi lỗi API nếu NHIỀU PMID cùng lô đều "
                                            "'unresolved')"}
        return results

    # -- GỘP: rút bài + metadata trong MỘT efetch (vá 2026-07-18, giảm token) ---
    def check_citations(self, pmids: List[str]) -> Dict[str, Dict[str, dict]]:
        """Gọi PubMed efetch MỘT LẦN cho danh sách PMID rồi trả CẢ trạng thái rút
        bài LẪN metadata gốc — thay cho việc gọi `check_retraction_status()` và
        `fetch_metadata()` riêng (2 efetch cho cùng danh sách PMID = gấp đôi mạng,
        parse, và token đọc kết quả). Dùng bởi `tools/check_citations.py` để ghi cả
        hai receipt (rút bài + metadata) từ một lệnh duy nhất.

        Trả {"retraction": {pmid: {...}}, "metadata": {pmid: {...}}} — mỗi nhánh
        đúng format của `check_retraction_status()`/`fetch_metadata()` tương ứng, để
        các hàm ghi receipt hiện có tái dùng y nguyên (không phân kỳ logic)."""
        if not pmids:
            return {"retraction": {}, "metadata": {}}
        if self.use_mock or not settings.ncbi_email:
            reason = ("USE_MOCK_SOURCES=true" if self.use_mock else "thiếu NCBI_EMAIL")
            retr = {pmid: {"status": "unknown_mock_or_no_email",
                           "reason": f"{reason} — KHÔNG tra cứu PubMed thật, không được coi là 'ok'"}
                    for pmid in pmids}
            meta = {pmid: {"status": "unknown_mock_or_no_email",
                           "reason": f"{reason} — KHÔNG tra cứu PubMed thật, không được coi là đã phân giải"}
                    for pmid in pmids}
            return {"retraction": retr, "metadata": meta}
        params = {"db": "pubmed", "id": ",".join(pmids), "retmode": "xml", "email": settings.ncbi_email}
        if settings.ncbi_api_key:
            params["api_key"] = settings.ncbi_api_key
        try:
            # SỬA 2026-07-22 (vòng lặp kiểm tra-hoàn thiện vòng 10, phát hiện HIGH) — cùng lý
            # do với check_retraction_status(): tắt cache 24h cho cổng kiểm rút bài/trích dẫn.
            xml_text = self.http.get_text(EFETCH, params=params, use_cache=False)
        except Exception as exc:  # pragma: no cover - lỗi mạng thực tế
            logger.warning("[pubmed] check_citations lỗi gọi thật: %s", exc)
            retr = {pmid: {"status": "unknown_mock_or_no_email", "reason": f"lỗi gọi PubMed: {exc}"}
                    for pmid in pmids}
            meta = {pmid: {"status": "unknown_mock_or_no_email", "reason": f"lỗi gọi PubMed: {exc}"}
                    for pmid in pmids}
            return {"retraction": retr, "metadata": meta}
        # Một XML → hai parser (không gọi mạng lần 2).
        return {
            "retraction": self._parse_retraction_xml(xml_text, pmids),
            "metadata": self._parse_metadata_xml(xml_text, pmids),
        }

    # -- Phân giải METADATA gốc CHỦ ĐỘNG (vá 2026-07-18) ------------------
    def fetch_metadata(self, pmids: List[str]) -> Dict[str, dict]:
        """Phân giải CHỦ ĐỘNG metadata gốc (tác giả·tiêu đề·tạp chí·năm·DOI) THẬT
        từ PubMed cho danh sách PMID — dùng để đối chiếu Bước 1-2 của
        `kiem-chung-trich-dan` (metadata trong bài vs gốc). Khác
        `check_retraction_status()` (chỉ đọc cờ rút bài): hàm này trả metadata
        định danh đầy đủ, làm nền cho `tools/check_citation_metadata.py` ghi
        receipt máy-kiểm A12_METADATA_RECEIPT.json — bằng chứng PMID đã thật sự
        được phân giải, không phải agent tự điền ✅ từ trí nhớ.

        Trả {pmid: {"status": ..., "title", "authors", "journal", "year", "doi"}}:
          "resolved"                 — PubMed trả bản ghi, có metadata gốc
          "unresolved"               — PubMed không trả bản ghi (nghi ma/PMID sai)
          "unknown_mock_or_no_email" — KHÔNG tra cứu thật được (mock/thiếu email/
                                        lỗi mạng) — PHẢI coi là CHƯA phân giải.
        """
        if not pmids:
            return {}
        if self.use_mock or not settings.ncbi_email:
            reason = ("USE_MOCK_SOURCES=true" if self.use_mock else "thiếu NCBI_EMAIL")
            return {
                pmid: {"status": "unknown_mock_or_no_email",
                       "reason": f"{reason} — KHÔNG tra cứu PubMed thật, không được coi là đã phân giải"}
                for pmid in pmids
            }
        params = {"db": "pubmed", "id": ",".join(pmids), "retmode": "xml", "email": settings.ncbi_email}
        if settings.ncbi_api_key:
            params["api_key"] = settings.ncbi_api_key
        try:
            # SỬA 2026-07-22 (vòng lặp kiểm tra-hoàn thiện vòng 10, phát hiện HIGH) — cùng lý
            # do với check_retraction_status()/check_citations(): đây cũng là một phần cơ chế
            # A12 THẬT (kiểm metadata trích dẫn), tắt cache để nhất quán và tránh dữ liệu cũ.
            xml_text = self.http.get_text(EFETCH, params=params, use_cache=False)
        except Exception as exc:  # pragma: no cover - lỗi mạng thực tế
            logger.warning("[pubmed] fetch_metadata lỗi gọi thật: %s", exc)
            return {
                pmid: {"status": "unknown_mock_or_no_email", "reason": f"lỗi gọi PubMed: {exc}"}
                for pmid in pmids
            }
        return self._parse_metadata_xml(xml_text, pmids)

    @staticmethod
    def _parse_metadata_xml(xml_text: str, requested_pmids: List[str]) -> Dict[str, dict]:
        results: Dict[str, dict] = {}

        # SỬA 2026-09-04 (Workflow đối kháng đa-agent vòng 2): hàm chị em
        # `_parse_retraction_xml()` đã dò trang chặn NCBI từ 12/08/2026, hàm này thì
        # chưa — xem comment tại `_trang_chan_ncbi()`.
        if _trang_chan_ncbi(xml_text):
            logger.warning("[pubmed] NCBI trả trang CHẶN thay vì XML — cần NCBI_API_KEY")
            return {pmid: {"status": "unknown_fetch_error", "reason": _LY_DO_NCBI_CHAN}
                    for pmid in requested_pmids}

        try:
            root = _safe_fromstring(xml_text)
        except (ET.ParseError, ValueError) as exc:
            # SỬA 2026-09-04: trước đây trả "unresolved" — cùng loại nhầm lẫn mà hàm
            # chị em _parse_retraction_xml() đã vá 12/08/2026 (xem comment ở đó):
            # "unresolved" nghĩa là PubMed KHÔNG CÓ bản ghi (nghi trích dẫn ma), còn
            # lỗi parse XML (mạng cắt giữa chừng, response hỏng) không kết luận được
            # gì về PMID. Đổi sang "unknown_fetch_error" cho nhất quán.
            logger.warning("[pubmed] parse XML (metadata) lỗi/không an toàn: %s", exc)
            return {pmid: {"status": "unknown_fetch_error",
                           "reason": f"không đọc được phản hồi PubMed ({exc}) — "
                                     f"KHÔNG kết luận gì về PMID này"}
                    for pmid in requested_pmids}
        found = set()
        for art in root.findall(".//PubmedArticle"):
            pmid = _own_article_pmid(art)
            if not pmid:
                continue
            found.add(pmid)
            title = _full_text(art.find(".//ArticleTitle")).strip()
            journal = (art.findtext(".//Journal/Title") or "").strip()
            year = (art.findtext(".//PubDate/Year")
                    or art.findtext(".//PubDate/MedlineDate") or "").strip()
            # DOI của CHÍNH bài — KHÔNG quét `.//` để khỏi nhặt phải DOI trong
            # danh mục tham khảo (xem `_own_article_doi`, vá 2026-08-14).
            doi = _own_article_doi(art)
            authors = ", ".join(
                f"{a.findtext('LastName') or ''} {a.findtext('Initials') or ''}".strip()
                for a in art.findall(".//Author")[:5]
            ).strip()
            results[pmid] = {
                "status": "resolved",
                "title": title,
                "authors": authors or None,
                "journal": journal or None,
                "year": year or None,
                "doi": doi,
            }
        for pmid in requested_pmids:
            if pmid not in found:
                results[pmid] = {"status": "unresolved",
                                  # SUA 2026-07-22 (vong lap kiem tra-hoan thien vong 10, phat hien
                                  # LOW): thong diep cu ngu y "PMID sai" - nhung neu PubMed tra HTTP
                                  # 200 hop le ma KHONG chua <PubmedArticle> nao cho CA LO (loi tang
                                  # API/NCBI), MOI pmid deu roi vao day du khong sai. Van chan dung
                                  # (fail-closed), chi lam ro nguyen nhan co the.
                                  "reason": "PubMed không trả về bản ghi cho PMID này trong lô truy vấn "
                                            "(PMID có thể sai/không tồn tại, HOẶC lỗi tầng API khiến "
                                            "cả lô bị bỏ sót — nghi lỗi API nếu NHIỀU PMID cùng lô đều "
                                            "'unresolved')"}
        return results

    @staticmethod
    def _infer_study_type(pubtypes: List[str]) -> Optional[str]:
        joined = " ".join(pubtypes).lower()
        if "meta-analysis" in joined or "systematic review" in joined:
            return "systematic_review"
        if "guideline" in joined:
            return "guideline"
        if "randomized" in joined:
            return "rct"
        return None
