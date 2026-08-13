"""Connector Europe PMC REST API – bổ sung metadata, full text/open access.

Từ 14/08/2026 connector này còn giữ vai trò NGUỒN KIỂM RÚT BÀI DỰ PHÒNG cho
`app.sources.retraction_chain` — xem `check_retraction_status()` ở cuối file.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from app.sources._fixtures import mock_records_for
from app.sources.base import RawRecord, SourceClient
from app.sources.classify_meta import infer_study_type
from app.utils.http import HttpClient
from app.utils.logging_config import get_logger

logger = get_logger(__name__)
SEARCH = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"


def _infer_study_type(pubtype: str, journal: str, raw: dict) -> "str | None":
    """Suy study_type từ pubType + tạp chí + cờ nguồn (PPR=preprint) của Europe PMC."""
    title = raw.get("title") or ""
    return infer_study_type(f"{title} {pubtype}", pubtype, journal,
                            source_tag=raw.get("source"))


class EuropePMCClient(SourceClient):
    name = "europepmc"
    endpoint = SEARCH

    def __init__(self) -> None:
        super().__init__()
        self.http = HttpClient()

    def search(self, query: str, clinical_area: Optional[str] = None,
               max_results: int = 20, since_date: Optional[str] = None) -> List[RawRecord]:
        if self.use_mock:
            return mock_records_for(self.name, query, clinical_area, max_results)
        try:
            q = query
            if since_date:
                # Lọc bài có ngày xuất bản đầu tiên >= since_date.
                q = f"({query}) AND (FIRST_PDATE:[{since_date} TO 3000-01-01])"
            params = {"query": q, "format": "json", "pageSize": max_results,
                      "resultType": "core"}
            data = self.http.get_json(SEARCH, params=params)
            self.save_raw(query, data)
            out: List[RawRecord] = []
            for r in data.get("resultList", {}).get("result", []):
                pubtype = r.get("pubType") or ""
                journal = r.get("journalTitle") or ""
                out.append(RawRecord(
                    source=self.name, title=r.get("title", ""),
                    authors=r.get("authorString"),
                    journal_or_organization=journal,
                    publication_date=r.get("firstPublicationDate"),
                    doi=r.get("doi"), pmid=r.get("pmid"), pmcid=r.get("pmcid"),
                    abstract=r.get("abstractText"),
                    document_type=pubtype,
                    study_type=_infer_study_type(pubtype, journal, r),
                    clinical_area=clinical_area,
                    url=f"https://europepmc.org/article/{r.get('source')}/{r.get('id')}",
                    ingest_query=query, api_endpoint=SEARCH,
                ))
            return out
        except Exception as exc:  # pragma: no cover
            logger.warning("[europepmc] lỗi gọi thật (live) — BỎ QUA, KHÔNG bịa mock: %s", exc)
            return []

    # -- Kiểm rút bài DỰ PHÒNG khi NCBI chặn (thêm 2026-08-14) ---------------
    def check_retraction_status(self, pmids: List[str]) -> Dict[str, dict]:
        """Cùng hợp đồng trả về với `PubMedClient.check_retraction_status()`.

        VÌ SAO CÓ: NCBI chặn IP dùng chung (trang "WWW Error Blocked Diagnostic")
        làm CẢ kho đứng ở trạng thái CHƯA kiểm rút bài, và máy này chưa lấy được
        `NCBI_API_KEY`. Europe PMC soi lại chính chỉ mục MEDLINE (`SRC:MED`) và
        KHÔNG đòi khoá — nên đây là nguồn gần nghĩa nhất, cách diễn giải không đổi.
        Đo thật 14/08/2026: PMID 9500320 → "retracted publication" + "retraction in";
        PMID 26760044 → sạch.

        Giữ NGUYÊN 6 trạng thái của hợp đồng gốc. Đặc biệt KHÔNG được để
        "không tìm thấy" thành "ok" — vắng mặt không bao giờ là bằng chứng sạch.
        """
        if not pmids:
            return {}
        if self.use_mock:
            return {p: {"status": "unknown_mock_or_no_email",
                        "reason": "USE_MOCK_SOURCES=true — KHÔNG tra cứu Europe PMC thật, "
                                  "không được coi là 'ok'"} for p in pmids}

        ket_qua: Dict[str, dict] = {}
        for lo in [pmids[i:i + 50] for i in range(0, len(pmids), 50)]:
            truy_van = "(" + " OR ".join(f"EXT_ID:{p}" for p in lo) + ") AND SRC:MED"
            try:
                data = self.http.get_json(
                    SEARCH,
                    params={"query": truy_van, "format": "json",
                            "resultType": "core", "pageSize": len(lo)},
                    # use_cache=False bắt buộc: cache 24h là ĐÚNG cho search() nhưng SAI
                    # cho kiểm rút bài — một bài bị rút trong cửa sổ cache sẽ không bị
                    # phát hiện dù receipt vẫn ghi mốc kiểm MỚI. Cùng lý do đã vá cho
                    # PubMedClient 22/07/2026.
                    use_cache=False,
                )
            except Exception as exc:
                logger.warning("[europepmc] kiểm rút bài lỗi gọi thật: %s", exc)
                for p in lo:
                    ket_qua[p] = {"status": "unknown_fetch_error",
                                  "reason": f"không gọi được Europe PMC ({exc}) — "
                                            f"KHÔNG kết luận gì về PMID này"}
                continue

            thay = {}
            for r in (data.get("resultList", {}) or {}).get("result", []) or []:
                if r.get("pmid"):
                    thay[str(r["pmid"])] = r
            for p in lo:
                ket_qua[p] = self._doc_rut_bai(thay[p]) if p in thay else {
                    "status": "unresolved",
                    "reason": "Europe PMC (chỉ mục MEDLINE) không có bản ghi cho PMID này "
                              "(PMID có thể sai/không tồn tại, HOẶC lỗi tầng API khiến cả "
                              "lô bị bỏ sót — nghi lỗi API nếu NHIỀU PMID cùng lô đều vậy)",
                }
        return ket_qua

    @staticmethod
    def _doc_rut_bai(r: dict) -> dict:
        """Đọc cờ rút bài trên MỘT bản ghi Europe PMC.

        BẪY PHẢI TRÁNH — khớp lỏng chuỗi "retract" là SAI. MEDLINE dùng hai nhãn
        gần giống nhau cho hai thứ NGƯỢC NHAU:
            • "Retracted Publication"    → bài BỊ rút          ⇒ có vấn đề
            • "Retraction of Publication"→ chính THÔNG BÁO rút → KHÔNG bị rút
        Khớp lỏng sẽ gắn cờ đỏ cho một thông báo rút bài hoàn toàn lành, đúng lớp
        "báo động giả còn tệ hơn không kiểm" đã ghi trong CLAUDE.md ngày 12/08.
        """
        pubtypes = {str(t).strip().lower()
                    for t in (r.get("pubTypeList") or {}).get("pubType", []) or []}
        lien_ket = [
            {"type": str(c.get("type", "")).strip().lower(),
             "pmid": c.get("id"), "citation": c.get("note") or c.get("source")}
            for c in (r.get("commentCorrectionList") or {}).get("commentCorrection", []) or []
        ]

        thong_bao_rut = next((c for c in lien_ket if c["type"].startswith("retraction in")), None)
        thong_bao_eoc = next((c for c in lien_ket if c["type"].startswith("expression of concern in")), None)

        if "retracted publication" in pubtypes or thong_bao_rut:
            return {"status": "retracted",
                    "retraction_notice": ({"pmid": thong_bao_rut["pmid"],
                                           "citation": thong_bao_rut["citation"]}
                                          if thong_bao_rut else None)}
        if "expression of concern" in pubtypes or thong_bao_eoc:
            return {"status": "expression_of_concern",
                    "expression_of_concern_notice": ({"pmid": thong_bao_eoc["pmid"],
                                                      "citation": thong_bao_eoc["citation"]}
                                                     if thong_bao_eoc else None)}
        return {"status": "ok"}
