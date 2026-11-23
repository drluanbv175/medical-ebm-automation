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

import re
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


# ───────────────────────────── K4 — truy vấn PubMed từ khái niệm PI khai ─────────────────────────────
_THE_PUBMED = ("[", "]", "(", ")", '"', " AND ", " OR ", " NOT ")


def _mot_thuat_ngu(t: str) -> str:
    """Một thuật ngữ trong nhóm OR: cụm nhiều từ ⇒ đặt trong ngoặc kép (PubMed tìm đúng cụm); thuật ngữ PI đã viết cú
    pháp PubMed (thẻ [mh]/[tiab], ngoặc, toán tử) ⇒ giữ NGUYÊN, bọc ngoặc đơn."""
    t = " ".join(str(t).split())
    if any(x in t for x in _THE_PUBMED):
        return f"({t})"
    return f'"{t}"' if " " in t else t


_O_MAU_KHAI_NIEM = re.compile(r"^\s*(?:<.*>|\[.*\]|n/?a|none|null|tbd|todo|chưa|—|-|\?+)\s*$", re.IGNORECASE)
_KHOA_KHAI_NIEM = {"P": "P", "I": "I", "E": "I", "O": "O"}   # PECO: E (phơi nhiễm) là khái niệm I


def _ly_do_loai_thuat_ngu(t: str) -> Optional[str]:
    """Lý do thuật ngữ PI khai KHÔNG được gửi lên PubMed/ClinicalTrials.gov (thẩm định #277, V6); None = dùng được."""
    if not _co(t) or _O_MAU_KHAI_NIEM.match(t):
        return "ô mẫu/chưa điền"
    if any(ord(c) > 127 for c in t):
        return "có ký tự ngoài ASCII — PubMed tìm theo thuật ngữ tiếng Anh"
    if t.count('"') % 2:
        return "ngoặc kép không cân"
    if t.count("(") != t.count(")") or t.count("[") != t.count("]"):
        return "ngoặc không cân"
    return None


def khai_niem_chuan(meta: Mapping[str, Any]) -> Tuple[Dict[str, List[str]], List[str]]:
    """({P|I|O: [thuật ngữ dùng được]}, [lý do loại]) từ gate_params.G0.khai_niem_tim_kiem — MỘT bộ chuẩn hoá cho cả bộ
    dựng truy vấn (truy_van_tu_khai_niem) và G0-AUTO-08 (thẩm định #277: Đ2 G0-AUTO-08 đếm khoá/giá trị bất kỳ là «PI
    viết»; V7 khai dạng chuỗi bị duyệt TỪNG KÝ TỰ; V6 ô mẫu/«N/A»/ngoặc lệch/tiếng Việt gửi thẳng lên PubMed).
    Khoá không phân biệt hoa thường; «E» là I; khoá khác (C, ghi chú…) bị bỏ kèm lý do; chuỗi tách theo «;» (không theo
    dấu phẩy — tiêu đề MeSH có dấu phẩy, vd «Heart Failure, Diastolic»)."""
    khai = _gp(meta, "G0").get("khai_niem_tim_kiem")
    if not isinstance(khai, Mapping):
        return {}, []
    nhom: Dict[str, List[str]] = {"P": [], "I": [], "O": []}
    loai: List[str] = []
    for khoa, v in khai.items():
        kk = str(khoa).strip().upper()
        dich = _KHOA_KHAI_NIEM.get(kk)
        if dich is None:
            loai.append(f"khoá «{khoa}» không dùng (chỉ P · I/E · O)")
            continue
        muc = v if isinstance(v, (list, tuple)) else [v]
        for x in muc:
            for t in str("" if x is None else x).split(";"):
                t = " ".join(t.split())
                if not t:
                    continue
                ly = _ly_do_loai_thuat_ngu(t)
                if ly:
                    loai.append(f"{kk}: «{t}» bị loại ({ly})")
                elif t not in nhom[dich]:
                    nhom[dich].append(t)
    return {k: v for k, v in nhom.items() if v}, loai


def truy_van_tu_khai_niem(meta: Mapping[str, Any]) -> Optional[str]:
    """Truy vấn PubMed dựng từ `gate_params.G0.khai_niem_tim_kiem = {"P": [...], "I": [...], "O": [...]}` (thuật ngữ
    tiếng Anh PI khai, đã qua khai_niem_chuan): trong một khái niệm nối OR (từ đồng nghĩa), giữa các khái niệm nối AND.
    None khi không còn thuật ngữ dùng được.

    K4 (giả lập lần 3, 15/11/2026): G0-AUTO-08 hướng dẫn PI «viết query_en HOẶC khai khai_niem_tim_kiem», nhưng bộ dựng
    truy vấn bỏ qua khai_niem_tim_kiem ⇒ PI khai xong G0 vẫn REVIEW (thuật ngữ PI khai không có trong truy vấn máy tự
    dịch) và PI vẫn phải tự viết cả câu truy vấn. Không cần PICO đã chốt — khái niệm tìm kiếm phục vụ chính lượt tra
    G0."""
    nhom, _loai = khai_niem_chuan(meta)
    phan = ["(" + " OR ".join(_mot_thuat_ngu(t) for t in nhom[ma]) + ")" for ma in ("P", "I", "O") if nhom.get(ma)]
    return " AND ".join(phan) or None


# ───────────────────────────── Kiểu ghép nhóm chứng của đề tài BỆNH–CHỨNG (23/11/2026) ─────────────────────────────
# Vì sao: giả lập bệnh–chứng ghi G1 «ghép theo giới và nhóm tuổi 5 năm, tỷ lệ 2 chứng : 1 ca» (không nói ghép CẶP CÁ
# THỂ hay ghép THEO TẦN SUẤT) mà biện pháp sai lệch + SAP §4 ghi «hồi quy logistic có điều kiện»; dữ liệu không có mã bộ
# ghép, G6 chạy logistic không điều kiện. Kiểu ghép quyết định họ mô hình phân tích chính (STROBE 12d): ghép cặp cá thể
# ⇒ logistic CÓ ĐIỀU KIỆN theo bộ ghép; ghép theo tần suất ⇒ logistic KHÔNG điều kiện, hiệu chỉnh theo các biến ghép;
# không ghép ⇒ logistic không điều kiện. Một hàm DÙNG CHUNG cho bộ sinh G1, cổng G1 (G1-AUTO-04c) và khuôn SAP G4.
KIEU_GHEP = {
    "ca_the": ("ghép cặp cá thể (individual matching)",
               "Hồi quy logistic có điều kiện (conditional logistic regression) theo bộ ghép (matched set) → OR "
               "(95%CI)"),
    "tan_suat": ("ghép theo tần suất (frequency matching)",
                 "Hồi quy logistic không điều kiện, hiệu chỉnh theo các biến ghép (ghép theo tần suất) → OR (95%CI)"),
    "khong_ghep": ("không ghép", "Hồi quy logistic không điều kiện → OR (95%CI)"),
}
_KIEU_GHEP_KHAI = {"individual": "ca_the", "ca_the": "ca_the", "frequency": "tan_suat", "tan_suat": "tan_suat",
                   "none": "khong_ghep", "unmatched": "khong_ghep", "khong_ghep": "khong_ghep"}
_RE_TAN_SUAT = re.compile(r"ghep\s+(?:theo\s+)?tan\s+suat|frequency[\s-]+match")
_RE_CA_THE = re.compile(r"ghep\s+cap|individual(?:ly)?[\s-]+match|pair[\s-]+match|bo\s+ghep|matched\s+set|"
                        r"ghep\s+\d+\s*[:：]\s*\d+")
_RE_PHU_DINH_CA_THE = re.compile(r"khong\s+(?:phai\s+)?ghep\s+cap(?:\s+ca\s+the)?|not\s+individual(?:ly)?[\s-]+match")
_RE_KHONG_GHEP = re.compile(r"khong\s+ghep\b|\bunmatched\b|khong\s+(?:co\s+)?(?:bat|ghep)\s+cap")
_RE_CO_GHEP = re.compile(r"ghep|\bmatch")


def _bo_dau_d(s: str) -> str:
    import unicodedata  # noqa: PLC0415

    s = unicodedata.normalize("NFD", s or "")
    return "".join(c for c in s if unicodedata.category(c) != "Mn").lower().replace("đ", "d")


def _chu_ghep(g1: Mapping[str, Any]) -> str:
    """Văn bản G1 nói về cách chọn nhóm chứng: nguồn chứng + sơ đồ thời gian + biện pháp sai lệch chọn mẫu."""
    phan = [g1.get("control_source"), g1.get("study_schema_timeline")]
    for b in g1.get("bias_controls") or []:
        if isinstance(b, Mapping):
            phan.append(b.get("bien_phap"))
    return " ".join(str(x) for x in phan if isinstance(x, str))


def kieu_ghep_benh_chung(g1: Mapping[str, Any]) -> Tuple[Optional[str], str]:
    """(kiểu ghép ∈ KIEU_GHEP hoặc None, căn cứ) của đề tài bệnh–chứng từ gate_params.G1.

    Khai tường minh `matching_type` (individual | frequency | none; nhận cả ca_the | tan_suat | khong_ghep) THẮNG. Không
    khai ⇒ đọc lời G1 (control_source, study_schema_timeline, bias_controls[].bien_phap): «ghép theo tần suất» ⇒
    tan_suat; «ghép cặp»/«bộ ghép»/«1:2» (không bị phủ định) ⇒ ca_the; cả hai ⇒ None (mâu thuẫn); «không ghép» ⇒
    khong_ghep; nhắc «ghép» mà không rõ kiểu ⇒ None (mơ hồ — G1 phải chốt); không nhắc ghép ⇒ khong_ghep."""
    g1 = g1 if isinstance(g1, Mapping) else {}
    khai = str(g1.get("matching_type") or "").strip().lower()
    if khai:
        kieu = _KIEU_GHEP_KHAI.get(khai)
        return (kieu, f"gate_params.G1.matching_type = «{khai}»") if kieu else (
            None, f"gate_params.G1.matching_type = «{khai}» không thuộc individual | frequency | none")
    bd = _bo_dau_d(_chu_ghep(g1))
    tan_suat = bool(_RE_TAN_SUAT.search(bd))
    ca_the = bool(_RE_CA_THE.search(_RE_PHU_DINH_CA_THE.sub(" ", bd)))
    if tan_suat and ca_the:
        return None, "lời G1 nói CẢ ghép theo tần suất LẪN ghép cặp cá thể — mâu thuẫn"
    if tan_suat:
        return "tan_suat", "lời G1 nêu «ghép theo tần suất»"
    if ca_the:
        return "ca_the", "lời G1 nêu ghép cặp cá thể (ghép cặp / bộ ghép / tỷ lệ ghép k:m)"
    if _RE_KHONG_GHEP.search(bd):
        return "khong_ghep", "lời G1 nêu «không ghép»"
    if _RE_CO_GHEP.search(bd):
        return None, ("lời G1 nhắc «ghép» nhưng không nói ghép cặp cá thể hay ghép theo tần suất — chưa chốt được họ "
                      "mô hình phân tích chính")
    return "khong_ghep", "lời G1 không nhắc ghép nhóm chứng"
