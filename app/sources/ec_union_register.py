"""Sổ đăng ký Liên minh (Union Register) của Uỷ ban châu Âu — đường DỰ PHÒNG cho danh mục EMA khi VPN bật (01/10/2026).

Vì sao: bác sĩ chốt «VPN luôn bật». Đo thật 01/10/2026 qua Kaspersky VPN: www.ema.europa.eu trả trang chặn CloudFront
403 cho tệp JSON danh mục thuốc (`EmaMedicinesClient` ⇒ «KHÔNG BIẾT» ở mọi lần tra), còn ec.europa.eu — Uỷ ban châu
Âu, cơ quan RA QUYẾT ĐỊNH cấp phép tập trung (EMA là cơ quan thẩm định) — trả đủ hai trang sổ: 1.554 thuốc người ĐANG
lưu hành (`reg_hum_act.htm`) và 447 thuốc KHÔNG CÒN lưu hành (`reg_hum_nact.htm`; vd Avandia/Avaglim — khớp trạng thái
Expired/Withdrawn bên EMA). Dữ liệu nằm sẵn trong trang dạng `var dataSet = [...]` (JSON; chuỗi có ký tự điều khiển
nên đọc `strict=False`, và đọc ĐÚNG MỘT giá trị JSON bằng `raw_decode` — không cắt bằng regex).

GIỚI HẠN (đi kèm mọi kết quả, xem `CANH_BAO_EC`): chỉ biết ĐANG / KHÔNG CÒN lưu hành — không lý do (rút/hết hạn/đình
chỉ), không ngày, không cờ giám sát bổ sung hay cấp phép có điều kiện; hồ sơ bị TỪ CHỐI hoặc rút đơn trước cấp phép
không có trong sổ; chỉ thuốc NGƯỜI. Lỗi mạng/bố cục ⇒ `EcLoi` — không bao giờ được đọc thành «không thấy».
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from app.utils.http import HttpClient

EC_SO_DANG_KY = "https://ec.europa.eu/health/documents/community-register/html/"
EC_DANG_LUU_HANH = EC_SO_DANG_KY + "reg_hum_act.htm"
EC_KHONG_CON = EC_SO_DANG_KY + "reg_hum_nact.htm"
NGUON_EC = ("EC Union Register — sổ thuốc cấp phép tập trung của Uỷ ban châu Âu "
            "(ec.europa.eu, reg_hum_act + reg_hum_nact)")
TRANG_THAI_EC_KHONG_CON = "Không còn lưu hành (sổ EC: rút/hết hạn/đình chỉ — không rõ loại)"
CANH_BAO_EC = (
    "DỰ PHÒNG: danh mục EMA không tới được trên đường mạng hiện tại — dữ liệu lấy từ Sổ đăng ký Liên minh của Uỷ ban "
    "châu Âu (cơ quan ra quyết định cấp phép tập trung).",
    "Sổ EC chỉ cho biết ĐANG / KHÔNG CÒN lưu hành: KHÔNG có lý do, ngày, cờ giám sát bổ sung hay cấp phép có điều kiện "
    "— cần các thông tin đó thì đọc trang thuốc (medicine_url) hoặc tra lại EMA khi đường mạng cho phép.",
    "Hồ sơ bị TỪ CHỐI hoặc rút đơn trước khi cấp phép KHÔNG có trong sổ EC.",
)
_TTL_CACHE = 7 * 24 * 3600
_DAU_DU_LIEU = "var dataSet ="
_RE_MA_TRANG = re.compile(r"[a-z]{1,3}\d{1,5}")


class EcLoi(RuntimeError):
    """Không lấy được hoặc không đọc được Sổ đăng ký Liên minh."""


def doc_bo_du_lieu(html_text: str) -> List[Dict[str, Any]]:
    """Đọc khối `var dataSet = [...]` của một trang sổ EC → danh sách bản ghi thuốc. Bố cục lạ/rỗng ⇒ `EcLoi`."""
    i = html_text.find(_DAU_DU_LIEU)
    j = html_text.find("[", i) if i >= 0 else -1
    if j < 0:
        raise EcLoi("không thấy khối `var dataSet` trong trang sổ EC (bố cục đổi?)")
    try:
        du_lieu, _ = json.JSONDecoder(strict=False).raw_decode(html_text, j)
    except ValueError as exc:
        raise EcLoi(f"không đọc được khối dữ liệu sổ EC: {exc}") from exc
    if not isinstance(du_lieu, list):
        raise EcLoi("khối dữ liệu sổ EC không phải danh sách")
    ban_ghi = [x for x in du_lieu if isinstance(x, dict) and (x.get("name") or x.get("inn"))]
    if not ban_ghi:
        # Danh sách rỗng KHÔNG được đọc thành «không có thuốc nào khớp».
        raise EcLoi("khối dữ liệu sổ EC rỗng")
    return ban_ghi


def url_trang_thuoc(eu_num: Any) -> str:
    """Trang của một thuốc trong sổ EC (vd EU/1/00/137 ⇒ …/html/h137.htm); thiếu mã ⇒ chuỗi rỗng."""
    if not isinstance(eu_num, dict):
        return ""
    ma = f"{eu_num.get('pre') or ''}{eu_num.get('id') or ''}"
    return EC_SO_DANG_KY + ma + ".htm" if _RE_MA_TRANG.fullmatch(ma) else ""


class EcUnionRegisterClient:
    """Nạp hai trang sổ (thuốc người). `http` tiêm được để kiểm offline; HttpClient thật có retry và cache 7 ngày."""

    name = "ec_union_register"

    def __init__(self, http: Optional[Any] = None) -> None:
        self.http = http or HttpClient(cache_ttl=_TTL_CACHE)

    def nap(self) -> Dict[str, List[Dict[str, Any]]]:
        """{"dang_luu_hanh": [...], "khong_con": [...]}; một trang hỏng là cả lần nạp hỏng (`EcLoi`)."""
        ra: Dict[str, List[Dict[str, Any]]] = {}
        for nhom, url in (("dang_luu_hanh", EC_DANG_LUU_HANH), ("khong_con", EC_KHONG_CON)):
            try:
                van_ban = self.http.get_text(url)
            except Exception as exc:  # noqa: BLE001 — mọi lỗi = KHÔNG BIẾT
                raise EcLoi(f"{type(exc).__name__}: {str(exc)[:160]}") from exc
            ra[nhom] = doc_bo_du_lieu(str(van_ban or ""))
        return ra
