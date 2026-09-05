# -*- coding: utf-8 -*-
"""Nền NGOẠI TUYẾN kiểm rút bài — cơ sở dữ liệu Retraction Watch (Crossref, CC0).

VÌ SAO CÓ (14/08/2026)
======================
`PubMedClient.check_retraction_status()` là đường DUY NHẤT hệ này kiểm rút bài.
Khi NCBI chặn IP dùng chung, cả kho 1146 định danh đứng ở trạng thái CHƯA kiểm —
fail-closed đúng thiết kế nhưng bế tắc, và máy này chưa lấy được `NCBI_API_KEY`.

Retraction Watch là danh mục rút bài được biên tập thủ công lớn nhất; từ 2023
Crossref mua lại và phát hành CÔNG KHAI giấy phép CC0. Nó có sẵn cột PMID nên
khớp thẳng, KHÔNG cần khoá, và quan trọng nhất: **tải một lần rồi tra hoàn toàn
ngoại tuyến** — không hạn mức, không IP nào chặn được. Đây là thứ giải đúng gốc
vấn đề (đơn nguồn + bị chặn) thay vì đổi một phụ thuộc mạng lấy một phụ thuộc
mạng khác.

RANH GIỚI NGỮ NGHĨA — ĐỌC KỸ TRƯỚC KHI DÙNG
============================================
Module này chỉ trả lời được MỘT NỬA câu hỏi:

    • CÓ trong danh mục  → bằng chứng MẠNH rằng bài đã bị rút.
    • KHÔNG có trong danh mục → **KHÔNG PHẢI** bằng chứng bài còn nguyên vẹn.
      Nó chỉ nghĩa là "danh mục này không nói gì". Có thể bài mới bị rút và
      Retraction Watch chưa cập nhật, hoặc bản CSV trên đĩa đã cũ.

Vì vậy `tra()` trả `None` khi không thấy — cố ý KHÔNG trả "ok". Việc biến im
lặng thành "sạch" đúng là lớp lỗi mà CLAUDE.md ghi ngày 12/08 ("không biết" bị
báo thành một kết luận), chỉ khác chiều và nguy hiểm hơn vì nó bỏ sót thật.
"""
from __future__ import annotations

import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

from app.utils.logging_config import get_logger

logger = get_logger(__name__)

THU_MUC = Path(__file__).resolve().parents[2] / "data" / "retraction_watch"
CSV_MAC_DINH = THU_MUC / "retraction_watch.csv"
META_MAC_DINH = THU_MUC / "retraction_watch.meta.json"

# Endpoint công khai của Crossref. Bắt buộc kèm email theo hợp đồng API của họ
# (cùng lệ "polite pool" mà repo này đã dùng cho OpenAlex/Unpaywall/NCBI).
ENDPOINT = "https://api.labs.crossref.org/data/retractionwatch"

# Cột `RetractionNature` KHÔNG chỉ chứa "Retraction". Đo thật trên dữ liệu sống
# 14/08/2026 thấy cả "Correction". Bảng dưới là chỗ dễ sai nhất của cả module:
#   • Correction/Erratum  → chuyện KHOA HỌC BÌNH THƯỜNG, gắn cờ đỏ là báo động giả.
#   • Reinstatement       → bài đã được PHỤC HỒI, gắn cờ "đã rút" là nói SAI hẳn.
# Nên chỉ hai giá trị đầu mới thành phán quyết; phần còn lại nhường cho nguồn sống.
ANH_XA_NATURE = {
    "retraction": "retracted",
    "expression of concern": "expression_of_concern",
}


class RetractionWatchIndex:
    """Chỉ mục PMID → bản ghi rút bài, dựng từ file CSV đã tải về."""

    def __init__(self, csv_path: Optional[Path] = None,
                 meta_path: Optional[Path] = None) -> None:
        self.csv_path = Path(csv_path) if csv_path else CSV_MAC_DINH
        self.meta_path = Path(meta_path) if meta_path else META_MAC_DINH
        self._chi_muc: Dict[str, dict] = {}
        self._da_nap = False
        self._phuc_hoi: set[str] = set()

    # -- trạng thái ------------------------------------------------------
    def san_sang(self) -> bool:
        """True chỉ khi CSV tồn tại VÀ đã nạp được ÍT NHẤT MỘT bản ghi có
        phán quyết (retracted/expression_of_concern).

        SỬA 2026-09-05 (Workflow đối kháng đa-agent, vòng 20) — trước đây
        chỉ kiểm `csv_path.exists()`, không kiểm chỉ mục có bản ghi nào
        không. Một CSV RỖNG/hỏng/placeholder đồng bộ dở (đúng rủi ro OneDrive
        mà chính docstring module này đã cảnh báo ở đầu file) vẫn báo sẵn
        sàng. Hệ quả kép ở app/sources/retraction_chain.py::check(): (a)
        MỌI PMID nhận "retraction_watch" trong `sources_tried` dù chỉ mục
        trống — thổi phồng bằng chứng máy-kiểm trong receipt A12 đã ký, CÙNG
        LỚP LỖI over-claim đã vá cho europepmc (03/09/2026); (b) điều kiện
        fail-closed `if "retraction_watch" not in da_thu:` hướng dẫn khắc
        phục (chạy `tools/tai_retraction_watch.py`) KHÔNG BAO GIỜ kích hoạt
        vì luôn nghĩ đã tra — người vận hành mất manh mối duy nhất để tự sửa
        khi NCBI chặn IP. Xác nhận sống:
        RetractionWatchIndex(csv_path='/dev/null').san_sang() trả True trước
        khi vá dù so_ban_ghi()==0.
        """
        return self.nap() and len(self._chi_muc) > 0

    def tai_ve_luc(self) -> Optional[datetime]:
        """Mốc TẢI VỀ (không phải mtime — OneDrive đồng bộ làm mtime vô nghĩa)."""
        try:
            meta = json.loads(self.meta_path.read_text(encoding="utf-8"))
            return datetime.fromisoformat(meta["tai_ve_luc"])
        except Exception:
            return None

    def tuoi_ngay(self) -> Optional[float]:
        moc = self.tai_ve_luc()
        if moc is None:
            return None
        return (datetime.now(timezone.utc) - moc).total_seconds() / 86400.0

    # -- nạp -------------------------------------------------------------
    def nap(self) -> bool:
        if self._da_nap:
            return True
        # Kiểm THẲNG file tồn tại (không gọi san_sang()) — san_sang() nay tự
        # gọi nap() để biết chỉ mục có bản ghi hay không (xem docstring
        # san_sang()); gọi ngược lại ở đây sẽ tạo đệ quy vô hạn.
        if not self.csv_path.exists():
            logger.info("[retraction_watch] chưa có CSV tại %s", self.csv_path)
            return False
        # Bản CSV thật có ô Notes rất dài; nới trần để không vỡ giữa chừng.
        try:
            csv.field_size_limit(sys.maxsize)
        except (OverflowError, ValueError):  # pragma: no cover - Windows 32-bit
            csv.field_size_limit(2 ** 31 - 1)

        with self.csv_path.open(encoding="utf-8", errors="replace", newline="") as fh:
            for hang in csv.DictReader(fh):
                pmid = (hang.get("OriginalPaperPubMedID") or "").strip()
                # "0" là giá trị GIỮ CHỖ của Retraction Watch khi không biết PMID —
                # coi nó là PMID thật sẽ gắn cờ rút bài cho một PMID không tồn tại.
                if not pmid or pmid == "0":
                    continue
                nature = (hang.get("RetractionNature") or "").strip().lower()
                if nature == "reinstatement":
                    self._phuc_hoi.add(pmid)
                    continue
                trang_thai = ANH_XA_NATURE.get(nature)
                if not trang_thai:
                    continue
                notice = (hang.get("RetractionPubMedID") or "").strip()
                ban_ghi = {
                    "status": trang_thai,
                    "nature": hang.get("RetractionNature", "").strip(),
                    "retraction_date": (hang.get("RetractionDate") or "").strip(),
                    "reason": (hang.get("Reason") or "").strip(),
                    "journal": (hang.get("Journal") or "").strip(),
                    "notice_pmid": notice if notice and notice != "0" else None,
                    "notice_doi": (hang.get("RetractionDOI") or "").strip() or None,
                }
                # Một bài có thể có NHIỀU dòng (EoC trước, rút bài sau). Rút bài
                # nặng hơn nên được thắng, bất kể thứ tự dòng trong file.
                cu = self._chi_muc.get(pmid)
                if cu is None or (cu["status"] != "retracted" and trang_thai == "retracted"):
                    self._chi_muc[pmid] = ban_ghi
        self._da_nap = True
        logger.info("[retraction_watch] nạp %d PMID có phán quyết, %d PMID được phục hồi",
                    len(self._chi_muc), len(self._phuc_hoi))
        return True

    # -- tra cứu ---------------------------------------------------------
    def tra(self, pmid: str) -> Optional[dict]:
        """Trả bản ghi nếu PMID nằm trong danh mục; `None` nghĩa là KHÔNG BIẾT.

        `None` KHÔNG BAO GIỜ được caller đọc thành "ok" — xem docstring đầu file.
        """
        if not self.nap():
            return None
        pmid = str(pmid).strip()
        if pmid in self._phuc_hoi:
            # SỬA 2026-09-05 (Workflow đối kháng đa-agent, task #89, vòng 6):
            # bản gốc chỉ trả None khi PMID CHỈ có dòng phục hồi, KHÔNG có
            # dòng rút bài/EoC nào khác (`pmid not in self._chi_muc`). Nhưng
            # kịch bản THẬT — và cũng là kịch bản phổ biến nhất của Retraction
            # Watch — là CẢ HAI dòng cùng tồn tại cho một PMID (rút bài trước,
            # phục hồi sau). Khi đó guard cũ KHÔNG fire, hàm rơi xuống trả
            # nguyên `status: "retracted"` (chỉ gắn kèm một khoá `canh_bao`
            # không ai bắt buộc phải đọc) — đúng điều docstring đầu file tự
            # khai là "nói SAI hẳn". Nay hễ có dòng phục hồi cho PMID này —
            # bất kể có dòng rút bài kèm theo hay không — đều KHÔNG kết luận,
            # để nguồn sống (PubMed/Europe PMC) nói tiếp.
            return None
        ban_ghi = self._chi_muc.get(pmid)
        if ban_ghi is None:
            return None
        kq = dict(ban_ghi)
        kq["source"] = "retraction_watch"
        return kq

    def so_ban_ghi(self) -> int:
        self.nap()
        return len(self._chi_muc)
