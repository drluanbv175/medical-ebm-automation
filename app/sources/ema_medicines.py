"""EMA — danh mục thuốc cấp phép TẬP TRUNG tại Liên minh châu Âu (báo cáo JSON công khai của EMA).

Thêm 20/09/2026 sau khi đánh giá `JamesANZ/medical-mcp` (xem `_CONNECTOR-CHUNG-CU.md` §1ter): cùng RxNorm, đây là
khoảng trống thật của engine. Ta tải THẲNG bộ dữ liệu công khai của EMA thay vì chạy mã của bên thứ ba.

Đo 20/09/2026: ~0,7 MB nén / 6,8 MB giải nén, 2.746 bản ghi (2.351 thuốc người + 395 thú y), cập nhật hằng ngày.
Trạng thái: Authorised 1.876 · Withdrawn 419 · Application withdrawn 286 · Refused 67 · Opinion 35 · Lapsed 29 ·
Expired 19 · Revoked 9.

GIÁ TRỊ: trả lời nhanh «thuốc này đang được EU cấp phép, đã bị thu hồi/rút khỏi thị trường, hay đang giám sát bổ
sung?» cho `ke-don-an-toan` và tầng cập nhật chứng cứ (ví dụ rosiglitazone: Avandia `Expired`, Avaglim `Withdrawn`).

BA ĐIỀU KHÔNG ĐƯỢC ĐỌC SAI (mỗi điều có cảnh báo đi kèm trong kết quả):
  1. Chỉ có thuốc cấp phép TẬP TRUNG. Thuốc cấp phép quốc gia không có trong danh sách ⇒ «không thấy» KHÔNG có
     nghĩa «chưa được cấp phép ở EU».
  2. Trạng thái KHÔNG kèm LÝ DO. `Withdrawn`/`Expired`/`Lapsed` thường là quyết định thương mại; không tự suy ra
     vấn đề an toàn — phải đọc EPAR qua `medicine_url`.
  3. Đây là quản lý của châu Âu, không phải khuyến cáo và không thay Cục Quản lý Dược Việt Nam.
Lỗi mạng/dữ liệu hỏng ⇒ trạng thái `loi` («KHÔNG BIẾT»), không bao giờ được thành «không thấy».
"""
from __future__ import annotations

import re
from collections import Counter
from typing import Any, Dict, List, Optional

from app.core.policy_engine import contains_pii_text
from app.sources.ec_union_register import (
    CANH_BAO_EC,
    NGUON_EC,
    TRANG_THAI_EC_KHONG_CON,
    EcLoi,
    EcUnionRegisterClient,
    url_trang_thuoc,
)
from app.utils.http import HttpClient

EMA_URL = "https://www.ema.europa.eu/en/documents/report/medicines-output-medicines_json-report_en.json"
NGUON = "EMA — danh mục thuốc cấp phép tập trung (medicines JSON report)"
_TTL_CACHE = 7 * 24 * 3600
TOI_DA_DO_DAI_TU_KHOA = 100
_NGAY_KET_THUC = "withdrawal_expiry_revocation_lapse_of_marketing_authorisation_date"
# Trường giữ lại (bỏ văn bản dài như therapeutic_indication cho gọn; có `medicine_url` để đọc EPAR).
TRUONG_GIU = (
    "name_of_medicine", "active_substance", "international_non_proprietary_name_common_name", "category",
    "medicine_status", "additional_monitoring", "conditional_approval", "patient_safety", "generic", "biosimilar",
    "orphan_medicine", "atc_code_human", "therapeutic_area_mesh", "marketing_authorisation_date", _NGAY_KET_THUC,
    "withdrawal_of_application_date", "refusal_of_marketing_authorisation_date",
    "suspension_of_marketing_authorisation_date", "last_updated_date", "ema_product_number", "medicine_url",
)
_UU_TIEN_TRANG_THAI = {"Authorised": 0, "Opinion": 1}
_CANH_BAO = (
    "EMA chỉ liệt kê thuốc cấp phép TẬP TRUNG: thuốc cấp phép quốc gia không có ở đây — «không thấy» KHÔNG có "
    "nghĩa «chưa được cấp phép ở EU».",
    "Trạng thái KHÔNG kèm lý do: Withdrawn/Expired/Lapsed thường là quyết định thương mại — không tự suy ra vấn "
    "đề an toàn, đọc EPAR qua medicine_url.",
    "Thông tin quản lý của châu Âu, KHÔNG phải khuyến cáo và không thay Cục Quản lý Dược Việt Nam.",
)


class EmaLoi(RuntimeError):
    """Không lấy được hoặc không đọc được danh mục EMA."""


def _ngay_sap_xep(s: str) -> str:
    """dd/mm/yyyy → yyyy-mm-dd để sắp giảm dần; ngày rỗng/lạ xếp cuối."""
    m = re.fullmatch(r"(\d{2})/(\d{2})/(\d{4})", (s or "").strip())
    return f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else ""


def _hoat_chat_cua(x: Dict[str, Any]) -> str:
    return (f"{x.get('active_substance') or ''} | "
            f"{x.get('international_non_proprietary_name_common_name') or ''}").casefold()


class EmaMedicinesClient:
    """Tra danh mục EMA. `http` tiêm được để kiểm offline; HttpClient thật có retry/backoff và cache 7 ngày."""

    name = "ema_medicines"

    def __init__(self, http: Optional[HttpClient] = None, ec: Optional[EcUnionRegisterClient] = None) -> None:
        self.http = http or HttpClient(cache_ttl=_TTL_CACHE)
        # Đường DỰ PHÒNG khi danh mục EMA không tới được (01/10/2026, bác sĩ: «VPN luôn bật» — www.ema.europa.eu bị
        # CloudFront chặn qua VPN): Sổ đăng ký Liên minh của Uỷ ban châu Âu, dùng chung HttpClient (cache 7 ngày).
        self._ec = ec

    def _nap(self) -> Dict[str, Any]:
        try:
            d = self.http.get_json(EMA_URL)
        except Exception as exc:  # noqa: BLE001 — mọi lỗi = KHÔNG BIẾT
            raise EmaLoi(f"{type(exc).__name__}: {str(exc)[:160]}") from exc
        du_lieu = d.get("data") if isinstance(d, dict) else None
        if not isinstance(du_lieu, list) or not du_lieu:
            # Bố cục đổi/tệp rỗng: danh sách rỗng KHÔNG được đọc thành «không có thuốc nào khớp».
            raise EmaLoi("bố cục dữ liệu EMA không như dự kiến (thiếu danh sách `data` hoặc rỗng)")
        return d

    def tra(self, tu_khoa: Optional[str], *, ca_thu_y: bool = False, toi_da: int = 25) -> Dict[str, Any]:
        tu_khoa = " ".join((tu_khoa or "").split())
        kq: Dict[str, Any] = {"tu_khoa": tu_khoa, "trang_thai": "loi", "ket_qua": [], "nguon": NGUON,
                              "canh_bao": list(_CANH_BAO)}
        if len(tu_khoa) < 3:
            kq["ly_do"] = "từ khoá quá ngắn (cần ≥ 3 ký tự để không khớp tràn lan)"
            return kq
        if len(tu_khoa) > TOI_DA_DO_DAI_TU_KHOA or contains_pii_text(tu_khoa):
            kq["ly_do"] = "đầu vào quá dài hoặc có dấu hiệu định danh — chỉ tra TÊN hoạt chất/biệt dược ngắn"
            return kq
        try:
            d = self._nap()
        except EmaLoi as exc:
            return self._tra_du_phong_ec(kq, tu_khoa, exc, ca_thu_y=ca_thu_y, toi_da=toi_da)

        mau = re.compile(r"(?<!\w)" + re.escape(tu_khoa.casefold()) + r"(?!\w)")
        khop: List[Dict[str, Any]] = []
        for x in d["data"]:
            if not ca_thu_y and (x.get("category") or "").casefold() != "human":
                continue
            if mau.search(_hoat_chat_cua(x)):
                loai = "hoat_chat"
            elif mau.search((x.get("name_of_medicine") or "").casefold()):
                loai = "ten_thuoc"
            else:
                continue
            ban = {k: x.get(k, "") for k in TRUONG_GIU}
            ban["khop_theo"] = loai
            khop.append(ban)
        # Hai lượt sắp ỔN ĐỊNH: mới cập nhật lên trước, rồi Authorised/Opinion lên trước các trạng thái đã kết thúc.
        khop.sort(key=lambda b: _ngay_sap_xep(b["last_updated_date"]), reverse=True)
        khop.sort(key=lambda b: _UU_TIEN_TRANG_THAI.get(b["medicine_status"], 2))
        kq["du_lieu_luc"] = (d.get("meta") or {}).get("timestamp", "")
        kq["tong_bai_ghi_ema"] = len(d["data"])
        kq["so_khop"] = len(khop)
        kq["theo_trang_thai"] = dict(Counter(b["medicine_status"] for b in khop))
        kq["ket_qua"] = khop[:max(1, toi_da)]
        kq["bi_cat_bot"] = max(0, len(khop) - len(kq["ket_qua"]))
        kq["trang_thai"] = "co_ket_qua" if khop else "khong_thay"
        return kq

    def _tra_du_phong_ec(self, kq: Dict[str, Any], tu_khoa: str, loi_ema: EmaLoi, *, ca_thu_y: bool,
                         toi_da: int) -> Dict[str, Any]:
        """EMA không lấy được ⇒ tra Sổ đăng ký Liên minh (EC). Sổ EC cũng hỏng ⇒ «loi» (KHÔNG BIẾT) như trước.

        Bản ghi giữ đúng các khoá `TRUONG_GIU` (khoá sổ EC không có thì để rỗng) để công cụ đọc kết quả không phải đổi;
        thuốc đang lưu hành mang trạng thái «Authorised» (cùng ưu tiên sắp xếp như EMA), thuốc không còn lưu hành mang
        `TRANG_THAI_EC_KHONG_CON` — sổ EC không cho biết là rút, hết hạn hay đình chỉ."""
        ec = self._ec or EcUnionRegisterClient(http=self.http)
        try:
            so = ec.nap()
        except EcLoi as loi_ec:
            kq.update(trang_thai="loi", ly_do=f"{loi_ema}; dự phòng EC Union Register cũng lỗi: {loi_ec}")
            kq["canh_bao"].append("KHÔNG BIẾT (không lấy được danh mục EMA lẫn sổ EC) — tuyệt đối không đọc thành "
                                  "«không thấy».")
            return kq
        mau = re.compile(r"(?<!\w)" + re.escape(tu_khoa.casefold()) + r"(?!\w)")
        khop: List[Dict[str, Any]] = []
        for nhom, trang_thai in (("dang_luu_hanh", "Authorised"), ("khong_con", TRANG_THAI_EC_KHONG_CON)):
            for x in so.get(nhom) or []:
                hoat_chat, ten = str(x.get("inn") or ""), str(x.get("name") or "")
                if mau.search(hoat_chat.casefold()):
                    loai = "hoat_chat"
                elif mau.search(ten.casefold()):
                    loai = "ten_thuoc"
                else:
                    continue
                eu = x.get("eu_num") if isinstance(x.get("eu_num"), dict) else {}
                ban = {k: "" for k in TRUONG_GIU}
                ban.update(name_of_medicine=ten, active_substance=hoat_chat,
                           international_non_proprietary_name_common_name=hoat_chat, category="Human",
                           medicine_status=trang_thai, ema_product_number=str(eu.get("display") or ""),
                           medicine_url=url_trang_thuoc(eu))
                ban["khop_theo"] = loai
                ban["nguon_ban_ghi"] = "EC Union Register"
                khop.append(ban)
        khop.sort(key=lambda b: _UU_TIEN_TRANG_THAI.get(b["medicine_status"], 2))
        kq["nguon"] = f"{NGUON} — DỰ PHÒNG: {NGUON_EC}"
        kq["du_phong"] = {"nguon": NGUON_EC, "ly_do_ema": str(loi_ema)}
        kq["canh_bao"].extend(CANH_BAO_EC)
        if ca_thu_y:
            kq["canh_bao"].append("Dự phòng sổ EC chỉ có thuốc NGƯỜI — phần thú y KHÔNG được tra (không đọc thành "
                                  "«không thấy»).")
        kq["tong_bai_ghi_du_phong"] = sum(len(so.get(n) or []) for n in ("dang_luu_hanh", "khong_con"))
        kq["so_khop"] = len(khop)
        kq["theo_trang_thai"] = dict(Counter(b["medicine_status"] for b in khop))
        kq["ket_qua"] = khop[:max(1, toi_da)]
        kq["bi_cat_bot"] = max(0, len(khop) - len(kq["ket_qua"]))
        kq["trang_thai"] = "co_ket_qua" if khop else "khong_thay"
        return kq
