# -*- coding: utf-8 -*-
"""CHUỖI 3 TẦNG kiểm rút bài — bỏ thế đơn nguồn vào NCBI.

VÌ SAO CÓ (14/08/2026, bác sĩ chốt phương án)
==============================================
Trước đây `tools/check_citation_retraction.py` chỉ có MỘT đường: NCBI E-utilities.
NCBI chặn IP dùng chung (trang "WWW Error Blocked Diagnostic") ⇒ mất hẳn năng lực
kiểm rút bài, và máy này chưa lấy được `NCBI_API_KEY`. Ba nguồn dưới đây đã ĐO
THẬT ngày 14/08 bằng 2 PMID biết trước đáp án (9500320 đã rút / 26760044 chưa):

  Tầng 0 — Retraction Watch (ngoại tuyến, CC0):  nền, không mạng, không hạn mức
  Tầng 1 — NCBI E-utilities:                     giữ nguyên, dùng khi có khoá/không bị chặn
  Tầng 2 — Europe PMC (không cần khoá):          dự phòng sống khi tầng 1 câm

LUẬT GỘP — CHỖ DỄ SAI NHẤT CỦA CẢ TÍNH NĂNG
============================================
Bất đối xứng có chủ ý giữa tín hiệu DƯƠNG và tín hiệu ÂM:

  • DƯƠNG (đã rút / EoC) từ BẤT KỲ nguồn nào ⇒ nhận. Rút bài tìm thấy ở một nguồn
    là rút bài thật; không nguồn nào có quyền phủ nhận nguồn khác.
  • ÂM ("ok") CHỈ được phát ra bởi nguồn đã THỰC SỰ LẤY ĐƯỢC bản ghi. Retraction
    Watch VĨNH VIỄN không được nói "ok": vắng mặt trong danh mục nghĩa là danh mục
    im lặng, KHÔNG phải bài còn nguyên vẹn.
  • Không nguồn nào kết luận được ⇒ giữ trạng thái KHÔNG BIẾT (fail-closed).

Giữ NGUYÊN 6 trạng thái của hợp đồng gốc `PubMedClient.check_retraction_status()`
để mọi nơi tiêu thụ (`so_xac_minh_nguon.py`, receipt A12, `run_g10_assemble.py`)
không phải đổi cách đọc. Chỉ THÊM khoá mô tả xuất xứ (`source`, `sources_tried`),
là bổ sung thuần nên không phá ai.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from app.sources.europepmc import EuropePMCClient
from app.sources.pubmed import PubMedClient
from app.sources.retraction_watch import RetractionWatchIndex
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

# Trạng thái KHÔNG mang phán quyết — chỉ nghĩa là "chưa biết".
KHONG_BIET = {"unknown_mock_or_no_email", "unknown_fetch_error"}
# Trạng thái DƯƠNG — có vấn đề thật, ưu tiên cao nhất khi gộp.
DUONG_TINH = ("retracted", "expression_of_concern")


class RetractionChain:
    """Hỏi lần lượt 3 nguồn rồi gộp theo luật bất đối xứng ở docstring đầu file."""

    def __init__(self, rw: Optional[RetractionWatchIndex] = None,
                 pubmed: Optional[PubMedClient] = None,
                 europepmc: Optional[EuropePMCClient] = None) -> None:
        self.rw = rw if rw is not None else RetractionWatchIndex()
        self.pubmed = pubmed if pubmed is not None else PubMedClient()
        self.europepmc = europepmc if europepmc is not None else EuropePMCClient()

    # ------------------------------------------------------------------
    def check(self, pmids: List[str]) -> Dict[str, dict]:
        if not pmids:
            return {}
        pmids = [str(p).strip() for p in pmids if str(p).strip()]

        da_thu: List[str] = []

        # Tầng 0 — ngoại tuyến. Chạy TRƯỚC vì không tốn mạng và không thể hỏng.
        rw_co = self.rw.san_sang()
        rw_verdict: Dict[str, dict] = {}
        if rw_co:
            da_thu.append("retraction_watch")
            for p in pmids:
                bg = self.rw.tra(p)
                if bg:
                    rw_verdict[p] = bg
        else:
            logger.info("[retraction_chain] chưa tải Retraction Watch — bỏ qua tầng nền. "
                        "Chạy: python tools/tai_retraction_watch.py")

        # Tầng 1 — NCBI. Vẫn hỏi trước: khi chạy được thì nó là nguồn đầy đủ nhất
        # (có CommentsCorrections gốc kèm PMID thông báo rút bài).
        da_thu.append("pubmed")
        pm = self.pubmed.check_retraction_status(pmids)

        # Tầng 2 — Europe PMC, CHỈ hỏi cho PMID mà tầng 1 không kết luận được.
        # Hỏi thừa vừa tốn mạng vừa dễ tạo bất đồng giả giữa hai nguồn.
        con_thieu = [p for p in pmids
                     if pm.get(p, {}).get("status", "unknown_fetch_error") in KHONG_BIET]
        ep: Dict[str, dict] = {}
        if con_thieu:
            da_thu.append("europepmc")
            logger.info("[retraction_chain] tầng 1 câm cho %d/%d PMID → hỏi Europe PMC",
                        len(con_thieu), len(pmids))
            ep = self.europepmc.check_retraction_status(con_thieu)

        return {p: self._gop(p, rw_verdict.get(p), pm.get(p), ep.get(p), da_thu)
                for p in pmids}

    # ------------------------------------------------------------------
    @staticmethod
    def _gop(pmid: str, rw: Optional[dict], pm: Optional[dict],
             ep: Optional[dict], da_thu: List[str]) -> dict:
        """Gộp phán quyết của 3 nguồn cho MỘT PMID."""
        nen = {"sources_tried": list(da_thu)}

        # 1. DƯƠNG TÍNH thắng tất cả, theo mức nặng: rút bài > expression of concern.
        #    Duyệt theo thứ tự nguồn giàu thông tin nhất để giữ được notice gốc.
        for muc in DUONG_TINH:
            for ten, kq in (("pubmed", pm), ("europepmc", ep), ("retraction_watch", rw)):
                if kq and kq.get("status") == muc:
                    ra = {k: v for k, v in kq.items() if k != "source"}
                    ra.update(nen)
                    ra["source"] = ten
                    # Ghi cả bằng chứng ngoại tuyến khi nó đồng thuận — receipt A12
                    # nhờ đó truy được vì sao kết luận, không chỉ kết luận là gì.
                    if ten != "retraction_watch" and rw:
                        ra["retraction_watch"] = {
                            "nature": rw.get("nature"),
                            "retraction_date": rw.get("retraction_date"),
                            "reason": rw.get("reason"),
                        }
                    # PHÂN BIỆT "rút bỏ hẳn" với "RÚT RỒI ĐĂNG LẠI BẢN ĐÃ SỬA".
                    # Retraction Watch ghi dạng này trong `reason` (vd "Error in Data;
                    # Retract and Replace;"). Ở dạng đó bài đã được sửa rồi công bố lại,
                    # thường CÙNG DOI/PMID — PubMed không gắn 'Retracted Publication'
                    # và không có dòng 'RIN'. Gọi chung là "đã bị rút, không dùng" là
                    # nói sai về một trích dẫn hợp lệ; việc cần làm là ĐỐI CHIẾU số liệu
                    # với bản đã sửa, không phải bỏ mục. Vẫn giữ status 'retracted' để
                    # cổng còn chặn (fail-closed) — chỉ CÂU CHỮ đổi.
                    from app.sources.crossref_retraction import la_rut_va_thay  # noqa: PLC0415
                    if la_rut_va_thay((rw or {}).get("reason", ""),
                                      kq.get("notice_title", ""),
                                      kq.get("reason", "")):
                        ra["retract_and_replace"] = True
                    return ra

        # 2. ÂM TÍNH hoặc "nghi ma" — chỉ nguồn SỐNG mới được nói, theo thứ tự ưu tiên.
        #    Retraction Watch cố ý KHÔNG có mặt ở nhánh này (xem docstring đầu file).
        song = [("pubmed", pm), ("europepmc", ep)]
        co_ok = next(((t, k) for t, k in song if k and k.get("status") == "ok"), None)
        co_ma = next(((t, k) for t, k in song if k and k.get("status") == "unresolved"), None)

        if co_ok:
            ten, kq = co_ok
            ra = dict(kq)
            ra.update(nen)
            ra["source"] = ten
            if co_ma:
                # Một nguồn lấy được bản ghi, nguồn kia bảo không có. Lấy được bản ghi
                # là bằng chứng DƯƠNG rằng trích dẫn không phải ma, nên "ok" thắng —
                # nhưng bất đồng phải hiện ra trong receipt, không được nuốt im.
                ra["ghi_chu"] = (f"nguồn {co_ma[0]} KHÔNG tìm thấy bản ghi trong khi {ten} "
                                 f"tìm thấy — nghi lỗi tầng API, không phải trích dẫn ma")
            return ra

        if co_ma:
            ten, kq = co_ma
            ra = dict(kq)
            ra.update(nen)
            ra["source"] = ten
            return ra

        # 3. Không nguồn nào kết luận được → FAIL-CLOSED, giữ nguyên lý do của tầng 1
        #    (nó nói rõ NCBI đang chặn) và nói thêm rằng dự phòng cũng đã thử.
        goc = pm or ep or {}
        ra = {
            "status": goc.get("status", "unknown_fetch_error"),
            "reason": goc.get("reason", "không nguồn nào kiểm được"),
        }
        ra.update(nen)
        ra["source"] = None
        if ep and ep.get("status") in KHONG_BIET:
            ra["reason"] += " | dự phòng Europe PMC cũng KHÔNG kết luận được: " + \
                            str(ep.get("reason", ""))[:160]
        if "retraction_watch" not in da_thu:
            ra["reason"] += (" | CHƯA tải nền ngoại tuyến — chạy "
                             "`python tools/tai_retraction_watch.py` để kiểm được "
                             "mà không cần mạng/khoá")
        return ra
