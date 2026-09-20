"""RxNorm (NLM RxNav REST) — CHUẨN HOÁ TÊN THUỐC cho tầng kê đơn an toàn.

Thêm 20/09/2026 sau khi đánh giá `JamesANZ/medical-mcp` (xem `_CONNECTOR-CHUNG-CU.md` §1ter): đây là MỘT trong hai
khoảng trống thật mà engine chưa phủ (RxNorm và danh mục EMA). Ta gọi THẲNG API công khai của NLM thay vì chạy mã
của bên thứ ba.

ĐÂY KHÔNG PHẢI NGUỒN CHỨNG CỨ. Nó chỉ trả lời «tên này ứng với hoạt chất/mã nào», để agent `ke-don-an-toan` đối
chiếu thuốc (medication reconciliation) theo hoạt chất thay vì theo biệt dược. Nó KHÔNG kiểm tương tác, KHÔNG chỉnh
liều, KHÔNG nêu chống chỉ định: API tương tác thuốc của RxNav đã ngừng (đo 20/09/2026: endpoint `interaction` trả
HTTP 404).

Bốn trạng thái, KHÔNG được gộp:
  * `khop_chinh_xac` — RxNorm có đúng tên này.
  * `gan_dung`       — chỉ khớp theo âm/chữ (approximateTerm). NGUY HIỂM nếu tự nhận: tên gần giống có thể là
                       thuốc KHÁC (look-alike/sound-alike; đo thật: «metfromin» → merbromin, một thuốc sát khuẩn) —
                       bác sĩ phải xác nhận, tuyệt đối không dùng tự động.
  * `khong_thay`     — RxNorm không có. RxNorm là danh mục Hoa Kỳ: biệt dược chỉ bán ở Việt Nam sẽ không có ở
                       đây, nên «không thấy» KHÔNG có nghĩa «thuốc không tồn tại».
  * `loi`            — không hỏi được (mạng/API/đầu vào bị từ chối). Luôn là «KHÔNG BIẾT», không bao giờ được đọc
                       thành «không thấy» (cùng lớp bài học BH27/BH08: không kiểm được phải là một vấn đề, không
                       phải một cái gật đầu).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.core.policy_engine import contains_pii_text
from app.utils.http import HttpClient

BASE = "https://rxnav.nlm.nih.gov/REST"
NGUON = "RxNorm (NLM RxNav REST)"
# IN = hoạt chất đơn · MIN = tổ hợp nhiều hoạt chất · PIN = dạng muối/tinh chất của hoạt chất
TTY_HOAT_CHAT = ("IN", "MIN", "PIN")
TOI_DA_UNG_VIEN = 3
TOI_DA_DO_DAI_TEN = 100
_TTL_CACHE = 7 * 24 * 3600  # danh mục thuốc đổi chậm; 7 ngày
_CANH_BAO_PHAM_VI = ("Chuẩn hoá tên KHÔNG phải kiểm tương tác/liều/chống chỉ định "
                     "(API tương tác của RxNav đã ngừng).")
_CANH_BAO_GAN_DUNG = ("GẦN ĐÚNG theo âm/chữ: tên gần giống có thể là thuốc KHÁC (look-alike/sound-alike) — bác sĩ "
                      "phải xác nhận, KHÔNG dùng tự động cho đối chiếu thuốc.")
_CANH_BAO_KHONG_THAY = ("RxNorm là danh mục Hoa Kỳ: không thấy KHÔNG có nghĩa thuốc không tồn tại (biệt dược chỉ có "
                        "ở Việt Nam sẽ không có ở đây) — tra tên hoạt chất (INN) trên nhãn thuốc.")
_CANH_BAO_MA_NGUNG = ("Mọi mã RxNorm cho tên này đều ĐÃ NGỪNG (Obsolete) — RxNorm không còn hoạt chất để đối chiếu: "
                      "đọc INN trên nhãn thuốc, không dùng kết quả này để đối chiếu.")


class RxNormLoi(RuntimeError):
    """Không hỏi được RxNorm (mạng/JSON hỏng). Người gọi chuyển thành trạng thái `loi`."""


def _lam_sach_ten(ten: Optional[str]) -> str:
    return " ".join((ten or "").split())


def _rxcui_tu_id_group(d: Dict[str, Any]) -> List[str]:
    ids = (d.get("idGroup") or {}).get("rxnormId") or []
    return [str(x) for x in ids if str(x).strip()]


def _khoa_ung_vien(d: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Gộp trùng theo rxcui (RxNav trả cùng một rxcui nhiều lần từ nhiều nguồn), giữ thứ hạng tốt nhất."""
    tot: Dict[str, Dict[str, Any]] = {}
    for c in (d.get("approximateGroup") or {}).get("candidate") or []:
        rxcui = str(c.get("rxcui") or "").strip()
        if not rxcui:
            continue
        try:
            hang = int(c.get("rank") or 999)
        except (TypeError, ValueError):
            hang = 999
        if rxcui not in tot or hang < tot[rxcui]["hang"]:
            tot[rxcui] = {"rxcui": rxcui, "hang": hang, "diem": c.get("score")}
    return sorted(tot.values(), key=lambda x: x["hang"])[:TOI_DA_UNG_VIEN]


def _khung(cp: Dict[str, Any]) -> Dict[str, Any]:
    return {"rxcui": str(cp.get("rxcui") or ""), "ten": cp.get("name") or "", "tty": cp.get("tty") or ""}


class RxNormClient:
    """Chuẩn hoá tên thuốc qua RxNav. `http` tiêm được để kiểm offline (HttpClient thật có retry/backoff/cache)."""

    name = "rxnorm"

    def __init__(self, http: Optional[HttpClient] = None) -> None:
        self.http = http or HttpClient(cache_ttl=_TTL_CACHE)

    # ---- các lời gọi mỏng -------------------------------------------------------------------------------------
    def _get(self, duong_dan: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            d = self.http.get_json(f"{BASE}/{duong_dan}", params=params)
        except Exception as exc:  # noqa: BLE001 — mọi lỗi (mạng/JSON/HTTP) đều = KHÔNG BIẾT
            raise RxNormLoi(f"{type(exc).__name__}: {str(exc)[:160]}") from exc
        if not isinstance(d, dict):
            raise RxNormLoi("phản hồi không phải JSON dạng đối tượng")
        return d

    def _thuoc_tinh(self, rxcui: str) -> Dict[str, Any]:
        p = self._get(f"rxcui/{rxcui}/properties.json").get("properties") or {}
        return {"rxcui": str(rxcui), "ten": p.get("name") or "", "tty": p.get("tty") or ""}

    def _hoat_chat(self, rxcui: str, tty: str) -> List[Dict[str, Any]]:
        if tty in TTY_HOAT_CHAT:  # bản thân đã là hoạt chất
            return []
        # RxNav đòi các tty cách nhau bằng DẤU CÁCH (requests mã hoá thành «+»). Truyền «IN+MIN+PIN» thẳng bị
        # mã hoá thành «%2B» ⇒ HTTP 400 (đo 20/09/2026) — nên đây là dấu cách, không phải chữ «+».
        d = self._get(f"rxcui/{rxcui}/related.json", {"tty": " ".join(TTY_HOAT_CHAT)})
        return [_khung(cp)
                for nhom in (d.get("relatedGroup") or {}).get("conceptGroup") or []
                for cp in nhom.get("conceptProperties") or []]

    def _chi_tiet(self, rxcui: str, diem: Any = None) -> Dict[str, Any]:
        tt = self._thuoc_tinh(rxcui)
        if not tt["ten"]:
            # Thuộc tính RỖNG = mã đã NGỪNG (đo 20/09/2026: «Coversyl» → toàn mã Obsolete). Lấy tên lịch sử để
            # người đọc hiểu đây là mã chết, và KHÔNG có hoạt chất để đối chiếu — không được trình bày như kết
            # quả bình thường.
            ls = self._get(f"rxcui/{rxcui}/historystatus.json").get("rxcuiStatusHistory") or {}
            md, at = ls.get("metaData") or {}, ls.get("attributes") or {}
            tt.update(ten=at.get("name") or "", tty=at.get("tty") or "", hoat_chat=[], hieu_luc=False,
                      trang_thai_rxcui=md.get("status") or "khong_ro")
        else:
            tt["hoat_chat"] = self._hoat_chat(rxcui, tt["tty"])
            tt["hieu_luc"] = True
        if diem is not None:
            tt["diem"] = diem
        return tt

    @staticmethod
    def _canh_bao_ma_ngung(kq: Dict[str, Any]) -> None:
        if kq["ket_qua"] and not any(x.get("hieu_luc") for x in kq["ket_qua"]):
            kq["canh_bao"].append(_CANH_BAO_MA_NGUNG)

    # ---- API chính --------------------------------------------------------------------------------------------
    def chuan_hoa(self, ten: Optional[str]) -> Dict[str, Any]:
        ten = _lam_sach_ten(ten)
        kq: Dict[str, Any] = {"ten_nhap": ten, "trang_thai": "loi", "ket_qua": [], "nguon": NGUON,
                              "canh_bao": [_CANH_BAO_PHAM_VI]}
        if not ten:
            kq["ly_do"] = "tên thuốc rỗng"
            return kq
        if len(ten) > TOI_DA_DO_DAI_TEN or contains_pii_text(ten):
            # Tên gửi ra dịch vụ bên ngoài: chỉ tên thuốc, không câu dài, không dấu hiệu PII/PHI.
            kq["ly_do"] = "đầu vào quá dài hoặc có dấu hiệu định danh — chỉ gửi TÊN thuốc ngắn, không gửi ra ngoài"
            return kq
        try:
            ids = _rxcui_tu_id_group(self._get("rxcui.json", {"name": ten}))
            if ids:
                kq["trang_thai"] = "khop_chinh_xac"
                kq["ket_qua"] = [self._chi_tiet(i) for i in ids[:TOI_DA_UNG_VIEN]]
                self._canh_bao_ma_ngung(kq)
                return kq
            ung_vien = _khoa_ung_vien(self._get("approximateTerm.json", {"term": ten, "maxEntries": 8}))
            if ung_vien:
                kq["trang_thai"] = "gan_dung"
                kq["ket_qua"] = [self._chi_tiet(u["rxcui"], u["diem"]) for u in ung_vien]
                kq["canh_bao"].append(_CANH_BAO_GAN_DUNG)
                self._canh_bao_ma_ngung(kq)
                return kq
            kq["trang_thai"] = "khong_thay"
            kq["canh_bao"].append(_CANH_BAO_KHONG_THAY)
            return kq
        except RxNormLoi as exc:
            kq.update(trang_thai="loi", ket_qua=[], ly_do=str(exc))
            kq["canh_bao"].append("KHÔNG BIẾT (không hỏi được RxNorm) — tuyệt đối không đọc thành «không thấy».")
            return kq
