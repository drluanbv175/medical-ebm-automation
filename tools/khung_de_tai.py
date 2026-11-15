#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Khung đề tài — MỘT nguồn sự thật cho PICO đã chốt, để G1 · SAP (G4) · đề cương (G10) điền sẵn.

Bác sĩ duyệt 15/11/2026. Vì sao: giả lập trung thực ZZSIM-DONGBO-TUANTHU-THA-20261115 cho thấy PI phải gõ lại quần
thể, kết cục chính, công cụ đo, thời điểm tới BA lần (G0 → A2 của G1 «[CẦN BỔ SUNG]» → SAP «[CẦN BÁC SĨ ĐIỀN — ví dụ:
tỷ lệ nhập viện tim mạch…]»). Gõ lại là nguồn lệch: lần gõ thứ hai đã đổi «tuân thủ DÙNG THUỐC» thành «tuân thủ ĐIỀU
TRỊ» và bỏ «≥3 tháng».

Luật kế thừa (đơn giản, có thể kiểm):
  • Giá trị G1 (gate_params.G1 / khoá cấp cao study_meta) THẮNG — PI sửa ở G1 thì dùng bản G1.
  • G1 vắng ⇒ kế thừa G0 CHỈ KHI G0 ĐÃ CHỐT (gate_params.G0.pico_confirmed = true). G0 chưa chốt thì không kế thừa
    (không đem nháp đi xa hơn cổng của nó).
  • Mỗi giá trị trả kèm NGUỒN («G1» / «G0») để nơi hiển thị ghi «(kế thừa G0 đã chốt)».
Không ghi tệp nào. Cần bác sĩ kiểm chứng.
"""
from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Tuple

_KHONG_CO = ("", None)


def _gp(meta: Mapping[str, Any], cong: str) -> Mapping[str, Any]:
    g = (meta.get("gate_params") or {}).get(cong) if isinstance(meta, Mapping) else None
    return g if isinstance(g, Mapping) else {}


def _co(v: Any) -> bool:
    """Có nội dung thật (không rỗng, không chỉ nhãn [CẦN…])."""
    if v is None:
        return False
    if isinstance(v, str):
        s = v.strip()
        return bool(s) and not s.upper().startswith(("[CẦN", "[CAN ", "TBD", "TODO"))
    if isinstance(v, (list, tuple)):
        return any(_co(x) for x in v)
    if isinstance(v, Mapping):
        return any(_co(x) for x in v.values())
    return True


def g0_da_chot(meta: Mapping[str, Any]) -> bool:
    return _gp(meta, "G0").get("pico_confirmed") is True


def _g0(meta: Mapping[str, Any], khoa: str) -> Any:
    return _gp(meta, "G0").get(khoa) if g0_da_chot(meta) else None


def gia_tri(meta: Mapping[str, Any], khoa: str) -> Tuple[Any, Optional[str]]:
    """(giá trị, nguồn) cho một trường của khung: population · intervention_or_exposure · comparator ·
    secondary_outcomes · research_question. Nguồn None = chưa có ở đâu."""
    g1 = _gp(meta, "G1")
    v = meta.get(khoa) if khoa in ("population",) else None
    if _co(v):
        return v, "G1"
    if _co(g1.get(khoa)):
        return g1.get(khoa), "G1"
    if not g0_da_chot(meta):
        return None, None
    if khoa == "population":
        v = _g0(meta, "population")
    elif khoa == "intervention_or_exposure":
        v = _g0(meta, "intervention")
    elif khoa == "comparator":
        v = _g0(meta, "comparison")
    elif khoa == "secondary_outcomes":
        chinh = str(_g0(meta, "primary_outcome") or "").strip().casefold()
        v = [x for x in (_g0(meta, "outcomes") or []) if str(x).strip().casefold() != chinh] or None
    elif khoa == "research_question":
        p, i, c = _g0(meta, "population"), _g0(meta, "intervention"), _g0(meta, "comparison")
        o = _g0(meta, "primary_outcome")
        v = (f"P: {p}; I/E: {i}; C: {c}; O: {o}" if all(_co(x) for x in (p, o)) else None)
    return (v, "G0") if _co(v) else (None, None)


def ket_cuc_chinh(meta: Mapping[str, Any]) -> Dict[str, Any]:
    """Kết cục chính 4 thành phần {name, measure, timepoint, type} + {nguon: {thành phần: G1|G0}}.

    Từng thành phần lấy G1 trước, G0 đã chốt sau (G0 không có «type» — loại dữ liệu chốt ở G1)."""
    g1 = _gp(meta, "G1")
    po = meta.get("primary_outcome") if _co(meta.get("primary_outcome")) else g1.get("primary_outcome")
    if isinstance(po, Mapping):
        g1_vals = {"name": po.get("name") or po.get("text") or po.get("description"),
                   "measure": po.get("measure") or po.get("measurement") or po.get("definition") or po.get("unit"),
                   "timepoint": po.get("timepoint") or po.get("time_point") or po.get("assessment_time"),
                   "type": po.get("type") or po.get("scale_type") or po.get("data_type")}
    else:
        g1_vals = {"name": po,
                   "measure": meta.get("primary_outcome_measure") or g1.get("primary_outcome_measure"),
                   "timepoint": meta.get("primary_outcome_timepoint") or g1.get("primary_outcome_timepoint"),
                   "type": meta.get("primary_outcome_type") or g1.get("primary_outcome_type")}
    g0_vals = {"name": _g0(meta, "primary_outcome"), "measure": _g0(meta, "primary_outcome_measure"),
               "timepoint": _g0(meta, "primary_outcome_timepoint"), "type": None}
    ra: Dict[str, Any] = {"nguon": {}}
    for k in ("name", "measure", "timepoint", "type"):
        if _co(g1_vals[k]):
            ra[k], ra["nguon"][k] = g1_vals[k], "G1"
        elif _co(g0_vals[k]):
            ra[k], ra["nguon"][k] = g0_vals[k], "G0"
        else:
            ra[k] = None
    return ra


def ke_thua_dang_dung(meta: Mapping[str, Any]) -> Dict[str, Any]:
    """Các giá trị G1 đang KẾ THỪA từ G0 (G1 vắng) — đưa vào dấu vân tay G1 để G0 đổi sau khi G1 chốt thì xác nhận G1
    hết hiệu lực. Đề tài đã tự ghi đủ ở G1 ⇒ {} ⇒ dấu vân tay KHÔNG đổi (không hạ cấp xác nhận cũ)."""
    ra: Dict[str, Any] = {}
    # Chỉ trường BẮT BUỘC của G1-HUMAN-02/03/04 (thẩm định #268): research_question/secondary_outcomes không bắt buộc ⇒
    # kế thừa để HIỂN THỊ nhưng không làm đổi dấu xác nhận.
    for k in ("population", "intervention_or_exposure", "comparator"):
        v, nguon = gia_tri(meta, k)
        if nguon == "G0":
            ra[k] = v
    kc = ket_cuc_chinh(meta)
    for k, nguon in kc["nguon"].items():
        if nguon == "G0":
            ra[f"primary_outcome.{k}"] = kc[k]
    return ra


MOC_LUAT = "2026-11-15"


def xac_nhan_truoc_moc(reviewed_at: Any) -> bool:
    """reviewed_at (ISO) TRƯỚC mốc luật kế thừa — xác nhận G1 cũ giữ dấu vân tay cách tính cũ.

    Không parse được ⇒ False (dùng cách tính mới)."""
    from datetime import datetime  # noqa: PLC0415

    try:
        luc = datetime.fromisoformat(str(reviewed_at or "").strip().replace("Z", "+00:00"))
    except ValueError:
        return False
    if luc.tzinfo is None:
        luc = luc.replace(tzinfo=datetime.fromisoformat(MOC_LUAT + "T00:00:00+07:00").tzinfo)
    return luc < datetime.fromisoformat(MOC_LUAT + "T00:00:00+07:00")


def nhan_nguon(nguon: Optional[str]) -> str:
    return " *(kế thừa G0 đã chốt — PI sửa ở gate_params.G1 nếu cần)*" if nguon == "G0" else ""


def danh_sach(v: Any) -> List[str]:
    if isinstance(v, (list, tuple)):
        return [str(x).strip() for x in v if _co(x)]
    return [str(v).strip()] if _co(v) else []
