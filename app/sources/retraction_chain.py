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

# Hai tầng TRỰC TUYẾN cần requests/defusedxml (chỉ venv có). Hook SessionStart và
# chốt kiểm chạy python3 HỆ THỐNG ⇒ tầng nào thiếu thư viện thì VẮNG MẶT CÓ KHAI
# BÁO — chuỗi vẫn sống bằng tầng nền ngoại tuyến (thuần stdlib), đúng lý do tồn
# tại của thiết kế đa tầng. Vắng mặt ≠ "ok": PMID không kết luận được vẫn giữ
# KHÔNG BIẾT (fail-closed), xem nhánh 3 của `_gop`.
try:
    from app.sources.europepmc import EuropePMCClient
except ModuleNotFoundError:
    EuropePMCClient = None  # type: ignore[assignment, misc]
try:
    from app.sources.pubmed import PubMedClient
except ModuleNotFoundError:
    PubMedClient = None  # type: ignore[assignment, misc]
from app.sources.retraction_watch import RetractionWatchIndex
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

# Trạng thái KHÔNG mang phán quyết — chỉ nghĩa là "chưa biết".
KHONG_BIET = {"unknown_mock_or_no_email", "unknown_fetch_error"}
# Trạng thái DƯƠNG — có vấn đề thật, ưu tiên cao nhất khi gộp.
DUONG_TINH = ("retracted", "expression_of_concern")
# Trạng thái mang PHÁN QUYẾT của một nguồn sống (vá 26/09/2026, phát hiện #34 — phòng thủ
# nhiều lớp). Nguồn trả trạng thái NGOÀI tập này và ngoài KHONG_BIET (vd 'rate_limited',
# 'timeout', None, '') bị coi là «không biết»: được hỏi Europe PMC như KHONG_BIET, và nếu
# không nguồn nào kết luận được thì CHUẨN HOÁ thành 'unknown_fetch_error' (giữ trạng thái
# gốc trong `reason`) — receipt A12 không bao giờ mang một trạng thái mà nơi tiêu thụ không biết.
CO_PHAN_QUYET = frozenset({"ok", "unresolved", *DUONG_TINH})


def _chi_dict(kq: object) -> Dict[str, dict]:
    """Kết quả của một client: chỉ giữ mục là dict (mục hỏng ⇒ coi như nguồn không trả lời PMID đó)."""
    if not isinstance(kq, dict):
        return {}
    return {str(k): v for k, v in kq.items() if isinstance(v, dict)}



def _cac_thong_bao(kq: dict) -> list:
    """Mọi thông báo rút bài mà MỘT nguồn báo (ưu tiên danh sách đầy đủ; lùi về thông báo đơn)."""
    ds = [n for n in (kq.get("retraction_notices") or []) if isinstance(n, dict)]
    if not ds and isinstance(kq.get("retraction_notice"), dict):
        ds = [kq["retraction_notice"]]
    return ds


class RetractionChain:
    """Hỏi lần lượt 3 nguồn rồi gộp theo luật bất đối xứng ở docstring đầu file."""

    def __init__(self, rw: Optional[RetractionWatchIndex] = None,
                 pubmed=None, europepmc=None) -> None:
        self.rw = rw if rw is not None else RetractionWatchIndex()
        # Tầng trực tuyến chỉ dựng được khi thư viện có mặt; thiếu → None và
        # `check()` coi tầng đó là "chưa hỏi được" (không bao giờ là "ok").
        self.pubmed = pubmed if pubmed is not None else (
            PubMedClient() if PubMedClient is not None else None)
        self.europepmc = europepmc if europepmc is not None else (
            EuropePMCClient() if EuropePMCClient is not None else None)

    # ------------------------------------------------------------------
    def check(self, pmids: List[str]) -> Dict[str, dict]:
        if not pmids:
            return {}
        pmids = [str(p).strip() for p in pmids if str(p).strip()]

        # Tầng 0 — ngoại tuyến. Chạy TRƯỚC vì không tốn mạng và không thể hỏng.
        rw_co = self.rw.san_sang()
        rw_verdict: Dict[str, dict] = {}
        if rw_co:
            for p in pmids:
                bg = self.rw.tra(p)
                if bg:
                    rw_verdict[p] = bg
        else:
            logger.info("[retraction_chain] chưa tải Retraction Watch — bỏ qua tầng nền. "
                        "Chạy: python tools/tai_retraction_watch.py")

        # Tầng 1 — NCBI. Vẫn hỏi trước: khi chạy được thì nó là nguồn đầy đủ nhất
        # (có CommentsCorrections gốc kèm PMID thông báo rút bài). Tầng không dựng
        # được (thiếu thư viện — chạy python3 hệ thống) thì KHÔNG ghi vào
        # `sources_tried`: chưa hỏi thì không được kể là đã thử.
        pm: Dict[str, dict] = {}
        if self.pubmed is not None:
            pm = _chi_dict(self.pubmed.check_retraction_status(pmids))
        else:
            logger.info("[retraction_chain] tầng NCBI vắng mặt (thiếu thư viện — "
                        "python3 hệ thống?) — chỉ còn nền ngoại tuyến + Europe PMC")

        # THÊM 2026-09-03 (Workflow đối kháng đa-agent, phát hiện #3): 'unresolved'
        # bị loại khỏi KHONG_BIET nên trước đây KHÔNG BAO GIỜ kích hoạt Europe PMC
        # — kể cả khi 'unresolved' là do LỖI TẦNG API của NCBI (HTTP 200 hợp lệ
        # nhưng KHÔNG chứa PubmedArticle nào cho CẢ LÔ — xem docstring
        # PubMedClient._parse_retraction_xml) chứ không phải PMID thật sự không
        # tồn tại. Nhánh xử lý bất đồng "một nguồn lấy được bản ghi, nguồn kia bảo
        # không có" trong _gop() (nhánh co_ma bên dưới) vì thế là DEAD CODE — ep
        # không bao giờ được truyền dữ liệu cho một PMID có pm.status='unresolved'.
        # Chỉ kích hoạt khi TOÀN BỘ lô cùng 'unresolved' — đúng dấu hiệu lỗi tầng
        # API mà chính pubmed.py mô tả ("nghi lỗi API nếu NHIỀU PMID cùng lô đều
        # 'unresolved'") — để không gọi Europe PMC tràn lan cho từng trích dẫn ma
        # lẻ tẻ thật sự không tồn tại trong một lô phần lớn vẫn giải quyết được.
        toan_bo_unresolved = bool(pmids) and all(
            pm.get(p, {}).get("status") == "unresolved" for p in pmids
        )
        trang_thai_can_kiem_cheo = set(KHONG_BIET)
        if toan_bo_unresolved:
            trang_thai_can_kiem_cheo.add("unresolved")

        # Tầng 2 — Europe PMC, CHỈ hỏi cho PMID mà tầng 1 không kết luận được.
        # Hỏi thừa vừa tốn mạng vừa dễ tạo bất đồng giả giữa hai nguồn.
        # Vá 26/09/2026 (#34): trạng thái LẠ của PubMed (ngoài CO_PHAN_QUYET) cũng là «không biết»
        # ⇒ hỏi Europe PMC, thay vì để nó trôi thẳng vào receipt.
        def _can_hoi_ep(p: str) -> bool:
            tt = pm.get(p, {}).get("status", "unknown_fetch_error")
            return tt in trang_thai_can_kiem_cheo or tt not in CO_PHAN_QUYET

        con_thieu = [p for p in pmids if _can_hoi_ep(p)]
        con_thieu_tap = set(con_thieu)
        ep: Dict[str, dict] = {}
        if con_thieu and self.europepmc is not None:
            logger.info("[retraction_chain] tầng 1 câm cho %d/%d PMID → hỏi Europe PMC",
                        len(con_thieu), len(pmids))
            ep = _chi_dict(self.europepmc.check_retraction_status(con_thieu))

        # SỬA 2026-09-03 (Workflow đối kháng đa-agent, phát hiện #4): `sources_tried`
        # trước đây là MỘT list dùng CHUNG cho cả lô — một PMID được pubmed trả lời
        # dứt khoát (vd 'ok') và KHÔNG hề được hỏi Europe PMC vẫn bị ghi
        # 'sources_tried': [...,'europepmc'], làm sai lệch bằng chứng máy-kiểm
        # trong receipt A12 đã ký (receipt tuyên bố một nguồn đã được tra trong khi
        # thực tế chưa từng gọi). Nay tính ĐÚNG theo từng PMID: retraction_watch/
        # pubmed đã hỏi ĐỒNG LOẠT cho cả lô (an toàn để dùng chung), europepmc chỉ
        # ghi cho đúng PMID nằm trong con_thieu — nơi nó THẬT SỰ được gọi.
        def _nguon_da_thu(p: str) -> List[str]:
            ds: List[str] = []
            if rw_co:
                ds.append("retraction_watch")
            if self.pubmed is not None:
                ds.append("pubmed")
            if self.europepmc is not None and p in con_thieu_tap:
                ds.append("europepmc")
            return ds

        # THÊM 2026-09-04 (vá cờ retract_and_replace không hoạt động): pm/ep chỉ
        # từng trả `retraction_notice.citation` — một chuỗi trích dẫn THÔ (tạp
        # chí/năm/số trang), KHÔNG BAO GIỜ mang tiêu đề — nên la_rut_va_thay()
        # trong _gop() trước đây CHỈ có thể bắt cụm "retract and replace" qua
        # rw.reason (Retraction Watch ngoại tuyến, làm mới 30 ngày/lần). Một PMID
        # vừa bị rút mà RW CHƯA kịp crawl, hoặc RW dùng cụm từ khác, khiến cờ IM
        # LẶNG không bao giờ bật dù status vẫn đúng "retracted" (fail-closed vẫn
        # giữ, chỉ mất phần CÂU CHỮ phân biệt "rút bỏ hẳn" với "rút rồi đăng lại
        # bản đã sửa"). Tra thêm TIÊU ĐỀ của chính thông báo rút bài — đúng cách
        # crossref_retraction.py đã làm cho DOI — CHỈ khi đã có tín hiệu rút bài
        # thật (rất hiếm trong một lô), một lệnh CHUNG cho cả lô thay vì từng PMID.
        notice_pmids: set[str] = set()
        for nguon in (pm, ep):
            for kq in nguon.values():
                if kq.get("status") == "retracted":
                    for n in _cac_thong_bao(kq):
                        if n.get("pmid"):
                            notice_pmids.add(str(n["pmid"]))
        notice_titles: Dict[str, str] = {}
        if notice_pmids:
            ds_notice = sorted(notice_pmids)
            if self.pubmed is not None:
                for npid, m in self.pubmed.fetch_metadata(ds_notice).items():
                    if m.get("status") == "resolved" and m.get("title"):
                        notice_titles[npid] = m["title"]
            con_thieu_tieu_de = [p for p in ds_notice if p not in notice_titles]
            if con_thieu_tieu_de and self.europepmc is not None:
                notice_titles.update(self.europepmc.fetch_notice_titles(con_thieu_tieu_de))

        return {p: self._gop(p, rw_verdict.get(p), pm.get(p), ep.get(p), _nguon_da_thu(p),
                             notice_titles)
                for p in pmids}

    # ------------------------------------------------------------------
    @staticmethod
    def _gop(pmid: str, rw: Optional[dict], pm: Optional[dict],
             ep: Optional[dict], da_thu: List[str],
             notice_titles: Optional[Dict[str, str]] = None) -> dict:
        """Gộp phán quyết của 3 nguồn cho MỘT PMID.

        `notice_titles` (thêm 2026-09-04): {pmid_thông_báo: tiêu_đề}, tra SỐNG
        qua PubMed.fetch_metadata()/EuropePMCClient.fetch_notice_titles() cho
        PMID của CHÍNH thông báo rút bài — xem check() ở trên. Trước bản vá này
        la_rut_va_thay() chỉ đọc được rw.reason (Retraction Watch ngoại tuyến);
        pm/ep không bao giờ mang tiêu đề thông báo nên hai đối số kia luôn rỗng."""
        notice_titles = notice_titles or {}
        nen = {"sources_tried": list(da_thu)}
        # Mục không phải dict (client hỏng) ⇒ coi như nguồn đó không trả lời (fail-closed ở nhánh 3).
        rw = rw if isinstance(rw, dict) else None
        pm = pm if isinstance(pm, dict) else None
        ep = ep if isinstance(ep, dict) else None

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
                    from app.sources.crossref_retraction import (  # noqa: PLC0415
                        la_rut_va_thay,
                        la_thong_bao_sua_loi_bi_rut,
                    )
                    notice_pmid = str((kq.get("retraction_notice") or {}).get("pmid") or "")
                    if la_rut_va_thay((rw or {}).get("reason", ""),
                                      kq.get("notice_title", ""),
                                      kq.get("reason", ""),
                                      notice_titles.get(notice_pmid, "")):
                        ra["retract_and_replace"] = True
                    if muc == "retracted":
                        # «BẢN ĐÍNH CHÍNH BỊ RÚT» (20/09/2026) — chỉ NHẬN DIỆN CÂU CHỮ, trạng thái
                        # vẫn `retracted`. Đánh cờ CHỈ khi hội đủ: (1) biết MỌI thông báo rút và
                        # đã đọc được tiêu đề của TỪNG cái, (2) tất cả đều là đính chính bị rút,
                        # (3) Retraction Watch không có phán quyết dương tính riêng (RW ghi một
                        # vụ rút THẬT thì không được gọi nó là «đính chính»). Thiếu một điều kiện
                        # ⇒ không cờ ⇒ giữ thông điệp «đã bị rút» như cũ (đường an toàn).
                        ds_tb = _cac_thong_bao(kq)
                        ra["notice_ids"] = sorted({str(n["pmid"]) for n in ds_tb if n.get("pmid")})
                        rw_duong = bool(rw and rw.get("status") in DUONG_TINH)
                        ra["withdrawn_correction_notice"] = bool(
                            ds_tb and len(ra["notice_ids"]) == len(ds_tb) and not rw_duong
                            and all(la_thong_bao_sua_loi_bi_rut(notice_titles.get(str(n["pmid"]), ""))
                                    for n in ds_tb))
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
        trang_thai = goc.get("status", "unknown_fetch_error")
        ly_do = str(goc.get("reason") or "không nguồn nào kiểm được")
        if trang_thai not in KHONG_BIET:
            # Trạng thái LẠ (vá 26/09/2026, #34): chuẩn hoá về 'unknown_fetch_error' để receipt không
            # mang một trạng thái mà nơi tiêu thụ (danh sách trắng/đen) không biết; giữ nguyên gốc trong lý do.
            ly_do = (f"nguồn trả trạng thái lạ {trang_thai!r} — chuẩn hoá thành "
                     f"'unknown_fetch_error' (CHƯA xác minh) | {ly_do}")
            trang_thai = "unknown_fetch_error"
        ra = {
            "status": trang_thai,
            "reason": ly_do,
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
