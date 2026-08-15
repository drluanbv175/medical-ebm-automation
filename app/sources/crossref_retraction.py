# -*- coding: utf-8 -*-
"""Kiểm RÚT BÀI theo DOI qua Crossref — bịt điểm mù chỉ-kiểm-PMID.

VÌ SAO CÓ (14/08/2026, vòng lặp kiểm tra–hoàn thiện vòng 4)
============================================================
Chuỗi 3 tầng dựng ngày 14/08 (`retraction_chain.py`) chỉ nhận **PMID**. Sổ xác minh
vì thế chưa từng kiểm rút bài cho **540 DOI** trong kho — gần một nửa số định danh.

Điểm mù này KHÔNG phải lý thuyết. Nó bị chạm vào ngay trong ngày: một mục trích
PMID 30267080 (đã rút) được sửa thành trích DOI `10.1001/jamaoncol.2018.4070`. Tra
Crossref thì **đó chính là bài đã rút** (`updated-by: retraction →
10.1001/jamaoncol.2019.0576`), nhưng vì cổng chỉ soi PMID nên cảnh báo TẮT trong khi
rủi ro còn nguyên. Một đèn đỏ tắt đi mà nguy cơ không mất là tệ hơn không có đèn.

VÌ SAO CROSSREF ĐỦ THẨM QUYỀN Ở ĐÂY
====================================
Quan hệ `update-to` / `updated-by` là siêu dữ liệu do CHÍNH nhà xuất bản nộp, đúng
kênh mà JAMA/Elsevier/Springer dùng để công bố thông báo rút bài. Không cần khoá,
không hạn mức thực tế. Đây là nguồn SỐNG (lấy được bản ghi thật), khác Retraction
Watch ngoại tuyến vốn không bao giờ được phép nói "ok".

LUẬT GỘP — GIỮ NGUYÊN BẤT ĐỐI XỨNG của retraction_chain.py
===========================================================
  • DƯƠNG TÍNH (`retraction` · `expression_of_concern`) ⇒ nhận ngay.
  • ÂM TÍNH ("ok") chỉ phát khi ĐÃ LẤY ĐƯỢC bản ghi Crossref và bản ghi đó không mang
    quan hệ rút bài nào.
  • Không lấy được bản ghi ⇒ KHÔNG BIẾT (`unknown_fetch_error`), fail-closed. Tuyệt
    đối không đổi im lặng thành lời bảo đảm (BH08/BH27/BH31).

Giữ ĐÚNG bộ khoá trạng thái của `PubMedClient.check_retraction_status()` để mọi nơi
tiêu thụ đọc được mà không phải đổi cách đọc.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Dict, Iterable, List

from app.utils.logging_config import get_logger

logger = get_logger(__name__)

API = "https://api.crossref.org/works/"
# Crossref dùng nhiều nhãn cho cùng một việc; gom về 2 mức nặng của hợp đồng chung.
NHAN_RUT = {"retraction", "retracted", "withdrawal", "withdrawn", "removal"}
NHAN_QUAN_NGAI = {"expression_of_concern", "expression of concern", "concern"}
# `correction`/`corrigendum`/`erratum` CỐ Ý không nằm ở đây: đính chính là chuyện
# bình thường của xuất bản, gộp nó vào "rút bài" sẽ tạo báo động giả hàng loạt và
# làm bác sĩ quen bỏ qua cảnh báo thật.


# Dấu hiệu "RÚT RỒI ĐĂNG LẠI BẢN ĐÃ SỬA" — KHÁC HẲN rút bỏ hẳn, và phải nói khác.
# Ở dạng này bài đã được sửa rồi công bố lại, thường ở CÙNG DOI/PMID; PubMed không
# gắn publication type 'Retracted Publication' và không có dòng 'RIN'. Gọi nó là
# "đã bị rút — không dùng" là NÓI SAI về một trích dẫn hợp lệ, và mỗi lần cảnh báo
# sai như vậy lại dạy người đọc bỏ qua cảnh báo thật.
# Việc cần làm ở dạng này là ĐỐI CHIẾU số liệu với bản đã sửa, không phải bỏ mục.
_RUT_VA_THAY = ("retraction and replacement", "retract and replace",
                "retracted and replaced", "retract-and-replace")


def la_rut_va_thay(*van_ban: str) -> bool:
    """Có phải dạng rút-rồi-đăng-lại không? Đọc tiêu đề thông báo / lý do Retraction Watch."""
    gop = " ".join(v or "" for v in van_ban).lower()
    return any(k in gop for k in _RUT_VA_THAY)


def _chuan_hoa(nhan: str) -> str:
    return (nhan or "").strip().lower().replace("-", "_")


class CrossrefRetraction:
    """Tra trạng thái rút bài cho DOI. Một lời gọi mạng cho mỗi DOI."""

    def __init__(self, mailto: str = "", timeout: int = 25) -> None:
        self.mailto = mailto
        self.timeout = timeout

    # ------------------------------------------------------------------
    def _lay(self, doi: str) -> dict | None:
        url = API + urllib.parse.quote(doi, safe="")
        if self.mailto:
            url += "?mailto=" + urllib.parse.quote(self.mailto)
        req = urllib.request.Request(
            url, headers={"User-Agent": "EBM-Copilot/1.0 (retraction check)"})
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            return json.loads(r.read().decode("utf-8", "replace")).get("message")

    # ------------------------------------------------------------------
    def check(self, dois: Iterable[str]) -> Dict[str, dict]:
        ra: Dict[str, dict] = {}
        for doi in dois:
            d = str(doi).strip()
            if not d:
                continue
            try:
                m = self._lay(d)
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    # Crossref TRẢ LỜI và nói không có bản ghi ⇒ nghi định danh ma,
                    # khác hẳn "không hỏi được". Dùng đúng khoá của hợp đồng chung.
                    ra[d] = {"status": "unresolved",
                             "reason": "Crossref không có bản ghi cho DOI này",
                             "source": "crossref"}
                    continue
                ra[d] = {"status": "unknown_fetch_error",
                         "reason": f"Crossref lỗi HTTP {e.code}", "source": None}
                continue
            except Exception as e:  # noqa: BLE001 — mọi lỗi mạng đều là "chưa biết"
                ra[d] = {"status": "unknown_fetch_error",
                         "reason": f"không hỏi được Crossref: {type(e).__name__}",
                         "source": None}
                continue

            if not m:
                ra[d] = {"status": "unknown_fetch_error",
                         "reason": "Crossref trả rỗng", "source": None}
                continue

            nang: List[tuple[str, str]] = []
            for u in (m.get("updated-by") or []):
                nhan = _chuan_hoa(u.get("type", ""))
                if nhan in NHAN_RUT:
                    nang.append(("retracted", u.get("DOI", "")))
                elif nhan in NHAN_QUAN_NGAI:
                    nang.append(("expression_of_concern", u.get("DOI", "")))

            if any(t == "retracted" for t, _ in nang):
                thong_bao = next(x for t, x in nang if t == "retracted")
                # Đọc TIÊU ĐỀ thông báo để phân biệt "rút bỏ hẳn" với "rút rồi đăng lại
                # bản đã sửa". Chỉ tốn thêm MỘT lời gọi, và chỉ khi đã có tín hiệu rút
                # bài — tức rất hiếm. Không đọc tiêu đề thì hệ nói sai về một trích dẫn
                # hợp lệ, và cảnh báo sai làm hỏng giá trị của cảnh báo đúng.
                tieu_de_tb = ""
                try:
                    tb = self._lay(thong_bao) or {}
                    tieu_de_tb = (tb.get("title") or [""])[0]
                except Exception:  # noqa: BLE001 — không đọc được thì giữ mức chung
                    pass
                ra[d] = {"status": "retracted", "source": "crossref",
                         "reason": "Crossref: updated-by retraction",
                         "notice_doi": thong_bao,
                         "notice_title": tieu_de_tb,
                         "retract_and_replace": la_rut_va_thay(tieu_de_tb),
                         "title": (m.get("title") or [""])[0]}
            elif nang:
                ra[d] = {"status": "expression_of_concern", "source": "crossref",
                         "reason": "Crossref: updated-by expression of concern",
                         "notice_doi": nang[0][1],
                         "title": (m.get("title") or [""])[0]}
            else:
                ra[d] = {"status": "ok", "source": "crossref",
                         "title": (m.get("title") or [""])[0]}
        return ra
