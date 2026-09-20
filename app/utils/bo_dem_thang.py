"""Bộ đếm lượt gọi THEO THÁNG, bền qua các tiến trình (ghi tệp JSON), FAIL-CLOSED.

Vì sao cần: ngân sách "mỗi lượt chạy" của SerpApi chỉ sống trong MỘT tiến trình và tự về 0 mỗi ngày, trong khi
ingest, dossier và manager là các tiến trình riêng — N tiến trình = N lần ngân sách, và gói Free của SerpApi chỉ có
250 search/THÁNG. Bộ đếm này giữ số đã dùng trong tháng dương lịch (UTC) trong một tệp dưới `data/raw/_state/`.

Luật (cùng khuôn bộ đếm tháng của Consensus, `app/sources/consensus_api.py`):
  * tệp VẮNG = cài mới = 0; tháng trong tệp CŨ hơn tháng hiện tại = sang tháng mới = 0;
  * tệp HỎNG/không đọc được/không ghi được = coi như ĐÃ CHẠM TRẦN (không bao giờ hiểu là 0);
  * ghi NGUYÊN TỬ (tệp tạm -> fsync -> os.replace) và luôn đọc lại tệp trước khi sửa;
  * hoàn 1 lượt được (trúng cache cục bộ) nhưng bộ đếm hỏng thì giữ nguyên (thận trọng);
  * nhà cung cấp báo HẾT quota thì đánh dấu hết cả tháng.
"""
from __future__ import annotations

import json
import os
import re
import tempfile
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from app.utils.logging_config import get_logger

logger = get_logger(__name__)

PHIEN_BAN = 1
_THANG_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


class TrangThaiHong(Exception):
    """Tệp bộ đếm hỏng/không đọc được (KHÔNG bao giờ được hiểu là 0)."""


class HetTran(Exception):
    """Không giữ chỗ được một lượt gọi. `pham_vi`: thang | het_quota | trang_thai_hong | khong_ghi_duoc."""

    def __init__(self, thong_bao: str, pham_vi: str) -> None:
        super().__init__(thong_bao)
        self.pham_vi = pham_vi


def _bay_gio() -> datetime:
    return datetime.now(timezone.utc)


class BoDemThang:
    """Một bộ đếm tháng gắn với MỘT tệp. `duong_dan_fn` được gọi mỗi lần (test đổi được thư mục dữ liệu)."""

    def __init__(self, ten: str, duong_dan_fn: Callable[[], Path],
                 bay_gio_fn: Optional[Callable[[], datetime]] = None) -> None:
        self.ten = ten
        self._duong_dan_fn = duong_dan_fn
        self._bay_gio = bay_gio_fn or _bay_gio
        self._khoa = threading.Lock()

    # ------------------------------------------------------------------ đọc/ghi
    def _thang(self) -> str:
        return self._bay_gio().strftime("%Y-%m")

    def _doc(self) -> Dict[str, Any]:
        """{thang, da_goi, het_quota}. NÉM TrangThaiHong với mọi thứ bất thường (JSON hỏng, sai kiểu, số âm, lạ)."""
        duong_dan = self._duong_dan_fn()
        hien_tai = self._thang()
        try:
            van_ban = duong_dan.read_text(encoding="utf-8")
        except FileNotFoundError:
            return {"thang": hien_tai, "da_goi": 0, "het_quota": False}
        except OSError as exc:
            raise TrangThaiHong(f"không đọc được tệp ({type(exc).__name__})") from None
        try:
            du_lieu = json.loads(van_ban)
        except ValueError:
            raise TrangThaiHong("nội dung không phải JSON hợp lệ") from None
        if not isinstance(du_lieu, dict):
            raise TrangThaiHong("nội dung không phải JSON object")
        pb = du_lieu.get("phien_ban", PHIEN_BAN)
        if isinstance(pb, bool) or pb != PHIEN_BAN:
            raise TrangThaiHong(f"phiên bản định dạng lạ ({pb!r})")
        thang, da_goi, het = du_lieu.get("thang"), du_lieu.get("da_goi"), du_lieu.get("het_quota", False)
        if not isinstance(thang, str) or not _THANG_RE.match(thang):
            raise TrangThaiHong("trường 'thang' thiếu hoặc sai định dạng YYYY-MM")
        if isinstance(da_goi, bool) or not isinstance(da_goi, int) or da_goi < 0:
            raise TrangThaiHong("trường 'da_goi' thiếu hoặc không phải số nguyên >= 0")
        if not isinstance(het, bool):
            raise TrangThaiHong("trường 'het_quota' không phải bool")
        if thang < hien_tai:
            return {"thang": hien_tai, "da_goi": 0, "het_quota": False}
        # thang > hien_tai (đồng hồ lùi/tệp từ máy lệch giờ): GIỮ số đếm, không đặt lại.
        return {"thang": thang, "da_goi": da_goi, "het_quota": het}

    def _ghi(self, trang_thai: Dict[str, Any]) -> None:
        """Ghi NGUYÊN TỬ; lỗi thì dọn tệp tạm rồi NÉM OSError."""
        duong_dan = self._duong_dan_fn()
        duong_dan.parent.mkdir(parents=True, exist_ok=True)
        noi_dung = dict(trang_thai)
        noi_dung["phien_ban"] = PHIEN_BAN
        noi_dung["cap_nhat_luc"] = self._bay_gio().isoformat()
        fd, ten_tam = tempfile.mkstemp(prefix=f".{self.ten}_usage.", suffix=".tmp", dir=str(duong_dan.parent))
        da_thay = False
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(noi_dung, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())
            for lan in range(4):
                try:
                    os.replace(ten_tam, duong_dan)
                    da_thay = True
                    return
                except PermissionError:
                    if lan == 3:
                        raise
                    time.sleep(0.05 * (lan + 1))
        finally:
            if not da_thay:
                try:
                    os.unlink(ten_tam)
                except OSError:
                    pass

    # ------------------------------------------------------------------ giao diện
    def giu_cho(self, tran: int) -> None:
        """Giữ chỗ 1 lượt trong trần tháng `tran`; NÉM HetTran nếu không được. Chỉ đếm khi đã ghi được tệp."""
        with self._khoa:
            try:
                tt = self._doc()
            except TrangThaiHong as exc:
                raise HetTran(
                    f"bộ đếm lượt gọi THÁNG của {self.ten} bị hỏng/không đọc được ({exc}) — coi như ĐÃ CHẠM TRẦN "
                    f"(fail-closed), KHÔNG tự đặt lại về 0. Đối chiếu số lượt thật rồi sửa hoặc xoá tay tệp "
                    f"{self._duong_dan_fn()}.", "trang_thai_hong") from None
            if tt["het_quota"]:
                raise HetTran(f"{self.ten} đã báo HẾT quota của tháng {tt['thang']} — không gọi thêm đến hết "
                              "tháng dương lịch (UTC).", "het_quota")
            if tt["da_goi"] >= tran:
                raise HetTran(f"đã dùng {tt['da_goi']}/{tran} lượt của THÁNG {tt['thang']} — các truy vấn còn "
                              "lại BỊ BỎ QUA có chủ đích.", "thang")
            tt["da_goi"] += 1
            try:
                self._ghi(tt)
            except OSError as exc:
                raise HetTran(f"không ghi được bộ đếm lượt gọi tháng ({type(exc).__name__}) — không thể bảo đảm "
                              "trần tháng nên KHÔNG gọi (fail-closed).", "khong_ghi_duoc") from None

    def hoan(self) -> None:
        """Hoàn 1 lượt (trúng cache cục bộ). Bộ đếm hỏng/lỗi ghi thì giữ nguyên số đếm (hướng thận trọng)."""
        with self._khoa:
            try:
                tt = self._doc()
                if tt["da_goi"] > 0:
                    tt["da_goi"] -= 1
                    self._ghi(tt)
            except (TrangThaiHong, OSError) as exc:
                logger.warning("[%s] không hoàn được 1 lượt trong bộ đếm tháng (giữ nguyên): %s",
                               self.ten, type(exc).__name__)

    def danh_dau_het(self, tran: int) -> None:
        """Nhà cung cấp báo hết quota: đặt bộ đếm >= trần và đánh dấu hết cả tháng."""
        with self._khoa:
            try:
                tt = self._doc()
            except TrangThaiHong:
                return  # tệp hỏng vốn đã chặn (fail-closed); không ghi đè bằng suy đoán
            tt["da_goi"] = max(tt["da_goi"], tran)
            tt["het_quota"] = True
            try:
                self._ghi(tt)
            except OSError as exc:
                logger.warning("[%s] không ghi được dấu hết quota tháng: %s", self.ten, type(exc).__name__)

    def anh_chup(self, tran: int) -> Dict[str, Any]:
        """Ảnh chụp cho diagnostics. KHÔNG NÉM, KHÔNG sửa gì; tệp hỏng thì `con_lai` = 0 (fail-closed)."""
        with self._khoa:
            info: Dict[str, Any] = {"thang": self._thang(), "tran_thang": tran,
                                    "duong_dan": str(self._duong_dan_fn())}
            try:
                tt = self._doc()
            except TrangThaiHong:
                info.update(da_goi_thang=None, het_quota=False, trang_thai_hong=True, con_lai_thang=0)
                return info
            info.update(da_goi_thang=tt["da_goi"], het_quota=tt["het_quota"], trang_thai_hong=False,
                        con_lai_thang=0 if tt["het_quota"] else max(tran - tt["da_goi"], 0))
            return info
