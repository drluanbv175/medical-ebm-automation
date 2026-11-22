# -*- coding: utf-8 -*-
"""Định nghĩa thay thế của phơi nhiễm/kết cục — khai ở G3, chép vào SAP §9 (G4), chạy ở G6 (22/11/2026).

VÌ SAO: khuôn SAP §9 cũ in «Định nghĩa thay thế của phơi nhiễm/kết cục, khai trước khi xem dữ liệu» rồi không nói định
nghĩa nào — 19/20 đề tài giả lập để phân tích độ nhạy này «chưa tự động». Một phân tích độ nhạy chỉ có nghĩa khi định
nghĩa thay thế được chốt TRƯỚC khi xem dữ liệu và có căn cứ (ngưỡng thay thế của hướng dẫn/chuẩn, thang đo gốc của biến
nhị phân suy từ phép đo — Altman & Royston 2006, BMJ, PMID 16675816 —, dạng hàm của yếu tố dự báo liên tục — Royston,
Altman & Sauerbrei 2006, Stat Med, PMID 16217841).

NGUỒN SỰ THẬT: ma trận mục tiêu–biến của G3 (`_ma-tran-muc-tieu-bien.csv`). Mỗi định nghĩa thay thế là MỘT dòng:
  vai_tro = `dinh_nghia_thay_the` · bien = biến mang định nghĩa thay thế (trường nhập hoặc trường tính calc của bộ
  biến) · khai_niem = TRÙNG khái niệm của dòng biến được thay (kết cục chính / phơi nhiễm / yếu tố dự báo) · kieu = kiểu
  của biến thay thế · cong_cu = định nghĩa + căn cứ (PMID/hướng dẫn) · phan_tich_sap = «SAP §9 …».
Khái niệm không khớp dòng nào ⇒ thay cho kết cục chính (mặc định an toàn: không lẳng lặng bỏ).

- G4 (`run_g4_auto`): `dong_sap(ds)` thay dòng chung của §9 bằng từng định nghĩa CỤ THỂ (biến, định nghĩa, căn cứ).
- G6: `phan_tich_g6(ds, ts_chinh, loai)` dựng mục đặc tả: cùng mô hình phân tích chính, chỉ thay biến — kết cục nhị
  phân thay thế giữ họ mô hình chính; thay bằng biến liên tục ⇒ hồi quy tuyến tính; phơi nhiễm liên tục ⇒ hiệu ứng trên
  mỗi 1 độ lệch chuẩn (`don_vi_phoi_nhiem` = "1SD", tính trên quần thể phân tích lúc chạy); chỉ số xét nghiệm thay thế
  nhị phân ⇒ độ nhạy/độ đặc hiệu tại giá trị 1; yếu tố dự báo thay thế ⇒ thay trong danh sách biến dự báo.
Không bịa ngưỡng: ngưỡng và căn cứ do người soạn bộ biến G3 khai; mô-đun chỉ chép và ánh xạ. Cần bác sĩ kiểm chứng.
"""
from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Mapping, Optional

VAI_TRO = "dinh_nghia_thay_the"
#: vai trò của dòng được thay, theo thứ tự ưu tiên khi khái niệm trùng nhiều dòng
_VAI_DICH = ("ket_cuc_chinh", "phoi_nhiem", "yeu_to", "hiep_bien")
_NHAN_VAI = {"ket_cuc_chinh": "kết cục chính", "phoi_nhiem": "phơi nhiễm", "yeu_to": "yếu tố dự báo",
             "hiep_bien": "hiệp biến"}
#: chữ neo chung của mọi dòng §9 mô-đun sinh — đặc tả G6 neo vào đoạn có tên biến (duy nhất trong SAP)
NEO = "Định nghĩa thay thế của"
DONG_CHUNG = "- Định nghĩa thay thế của phơi nhiễm/kết cục, khai trước khi xem dữ liệu  "
LIEN_TUC = ("lien_tuc", "dem")


def _chuan(s: Any) -> str:
    import ma_tran_muc_tieu_bien as MT  # noqa: PLC0415 — một hàm bỏ dấu cho mọi so khớp khái niệm

    return MT.bo_dau(s)


def tu_dong_ma_tran(dong: Optional[Iterable[Mapping[str, Any]]]) -> List[Dict[str, Any]]:
    """Danh sách định nghĩa thay thế từ các dòng ma trận: {bien, kieu, dinh_nghia, khai_niem, thay, vai_thay}."""
    dong = [dict(r) for r in (dong or [])]
    chinh = [r for r in dong if r.get("vai_tro") in _VAI_DICH and str(r.get("bien") or "").strip()]
    ra: List[Dict[str, Any]] = []
    for r in dong:
        if r.get("vai_tro") != VAI_TRO or not str(r.get("bien") or "").strip():
            continue
        kn = _chuan(r.get("khai_niem"))
        dich = None
        for vai in _VAI_DICH:
            dich = next((x for x in chinh if x.get("vai_tro") == vai and _chuan(x.get("khai_niem")) == kn), None)
            if dich:
                break
        dich = dich or next((x for x in chinh if x.get("vai_tro") == "ket_cuc_chinh"), None)
        if not dich:
            continue
        ra.append({"bien": str(r["bien"]).strip(), "kieu": str(r.get("kieu") or "").strip(),
                   "dinh_nghia": str(r.get("cong_cu") or "").strip(), "khai_niem": str(r.get("khai_niem") or ""),
                   "thay": str(dich["bien"]).strip(), "vai_thay": dich["vai_tro"]})
    return ra


def doc(out_dir) -> List[Dict[str, Any]]:
    """Định nghĩa thay thế của đề tài (ma trận G3); ma trận vắng/lỗi ⇒ []."""
    from pathlib import Path  # noqa: PLC0415

    import ma_tran_muc_tieu_bien as MT  # noqa: PLC0415

    dong, loi = MT.doc_ma_tran(Path(out_dir))
    return [] if loi else tu_dong_ma_tran(dong)


def dong_sap(ds: List[Dict[str, Any]]) -> List[str]:
    """Các dòng §9 thay dòng chung — mỗi định nghĩa một dòng, nêu biến thay, biến được thay, định nghĩa và căn cứ."""
    ra = []
    for d in ds:
        nhan = _NHAN_VAI.get(d["vai_thay"], d["vai_thay"])
        ra.append(f"- {NEO} {nhan} `{d['thay']}`: `{d['bien']}` — {d['dinh_nghia'] or d['khai_niem']}; cùng mô hình "
                  "phân tích chính, chỉ thay biến (khai ở bộ biến G3, trước khi xem dữ liệu)  ")
    return ra


def thay_dong_chung(sap: str, ds: List[Dict[str, Any]]) -> str:
    """Thay dòng chung của §9 bằng các định nghĩa cụ thể; không có định nghĩa nào ⇒ giữ nguyên SAP."""
    if not ds or DONG_CHUNG.strip() not in sap:
        return sap
    return re.sub(r"^" + re.escape(DONG_CHUNG.strip()) + r"[ \t]*$", lambda _m: "\n".join(dong_sap(ds)), sap,
                  count=1, flags=re.M)


def neo_cua(d: Mapping[str, Any]) -> str:
    """Neo đặc tả của một định nghĩa — đoạn chứa tên hai biến (duy nhất trong SAP)."""
    return f"`{d['thay']}`: `{d['bien']}`"


def phan_tich_g6(ds: List[Dict[str, Any]], ts_chinh: Mapping[str, Any]) -> List[Dict[str, Any]]:
    """Mục đặc tả G6 (vai do_nhay, sap_muc §9) của từng định nghĩa thay thế: tham số = tham số phân tích chính, thay
    đúng một biến. Trả [] khi không ánh xạ được (vai được thay không có trong phân tích chính)."""
    ra = []
    for d in ds:
        ts = {k: (list(v) if isinstance(v, list) else v) for k, v in ts_chinh.items()}
        lt = d["kieu"] in LIEN_TUC
        dac_thu = ts.get("loai_dac_thu")
        if dac_thu == "chan_doan" and ts.get("chi_so") == d["thay"]:
            ts["chi_so"] = d["bien"]
            if not lt:
                ts["nguong"] = 1  # chỉ số thay thế nhị phân: dương tính = 1
        elif dac_thu == "du_bao" and d["thay"] in (ts.get("covariates") or []):
            ts["covariates"] = [d["bien"] if c == d["thay"] else c for c in ts["covariates"]]
        elif d["vai_thay"] == "ket_cuc_chinh" and ts.get("outcome") == d["thay"]:
            ts["outcome"] = d["bien"]
            if lt:
                ts["outcome_type"] = "continuous"
        elif d["vai_thay"] == "ket_cuc_chinh" and d["thay"] in (ts.get("ty_le") or []):
            ts["ty_le"] = [d["bien"] if c == d["thay"] else c for c in ts["ty_le"]]
        elif d["vai_thay"] == "phoi_nhiem" and ts.get("group") == d["thay"]:
            ts["group"] = d["bien"]
            if lt:
                ts["don_vi_phoi_nhiem"] = "1SD"
        else:
            continue
        ra.append({"id": f"DN_dinh_nghia_{d['bien']}"[:60], "vai": "do_nhay", "sap_muc": "§9", "sap_neo": neo_cua(d),
                   "mo_ta": f"Định nghĩa thay thế: {d['bien']} thay {d['thay']} — {d['dinh_nghia'] or d['khai_niem']}",
                   "tham_so": ts})
    return ra


# ─────────────────────────── phân tích theo đề cương (per-protocol) của RCT ───────────────────────────
#: Neo của dòng §9 — trùng cụm chữ thống kê viên quen ghi, nên mục đặc tả cũ «Phân tích theo đề cương (per-protocol)»
#: vẫn neo được.
NEO_THEO_DE_CUONG = "Phân tích theo đề cương (per-protocol)"


def tuan_thu_tu_dong_ma_tran(dong: Optional[Iterable[Mapping[str, Any]]]) -> Optional[Dict[str, str]]:
    """Biến tuân thủ đề cương (vai_tro `tuan_thu_de_cuong`, mã 1 = tuân thủ) + định nghĩa ở cột cong_cu; vắng ⇒ None."""
    for r in dong or []:
        if r.get("vai_tro") == "tuan_thu_de_cuong" and str(r.get("bien") or "").strip():
            return {"bien": str(r["bien"]).strip(), "dinh_nghia": str(r.get("cong_cu") or "").strip()}
    return None


def chen_theo_de_cuong(sap: str, tt: Optional[Mapping[str, str]]) -> str:
    """Chèn dòng phân tích theo đề cương vào ĐẦU §9 (RCT có biến tuân thủ). Đã có neo ⇒ giữ nguyên."""
    if not tt or NEO_THEO_DE_CUONG.casefold() in sap.casefold():
        return sap
    m = re.search(r"^### §9[^\n]*\n\n?", sap, flags=re.M)
    if not m:
        return sap
    dong = (f"- {NEO_THEO_DE_CUONG}: chỉ người có `{tt['bien']}` = 1 — {tt['dinh_nghia']}; cùng mô hình phân tích "
            "chính; kết luận của thử nghiệm không kém hơn phải vững ở cả ITT lẫn theo đề cương  \n")
    return sap[:m.end()] + dong + sap[m.end():]


def phan_tich_theo_de_cuong(tt: Mapping[str, str], ts_chinh: Mapping[str, Any]) -> Dict[str, Any]:
    """Mục đặc tả G6: tham số phân tích chính, quần thể thêm điều kiện `<biến tuân thủ> == 1`."""
    ts = {k: (list(v) if isinstance(v, list) else v) for k, v in ts_chinh.items()}
    dk = f"{tt['bien']} == 1"
    ts["loc"] = f"{ts['loc']} and {dk}" if ts.get("loc") else dk
    return {"id": "DN_theo_de_cuong", "vai": "do_nhay", "sap_muc": "§9", "sap_neo": NEO_THEO_DE_CUONG,
            "mo_ta": f"Phân tích theo đề cương: chỉ người có {tt['bien']} = 1", "tham_so": ts}
