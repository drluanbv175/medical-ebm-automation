#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NHẤT QUÁN XUYÊN CỔNG G0–G10 — thông số then chốt của đề tài phải mang CÙNG giá trị ở mọi cổng dùng nó (04/10/2026).

VÌ SAO CÓ. Mỗi cổng giữ bản sao RIÊNG của cùng một thông số:
  • kết cục chính: gate_params.G0 · gate_params.G1 · mục TRDS 19 của bản đăng ký G2 · §2 SAP (G4) · gate_params.G8;
  • cỡ mẫu kế hoạch: checkpoint G3 · gate_params.G3 · mục TRDS 17 · n_from_g3 của G4 · §12 SAP;
  • thiết kế: study_meta · gate_params.G1 · checkpoint G1/G2/G3/G4/… · mục TRDS 15 (Interventional/Observational).
Các phép so trước đây RẢI RÁC theo cặp (G4 so SAP với G3 và G0/G1; G8 so kết cục) — không chỗ nào nhìn CẢ chuỗi, nên
một thông số lệch giữa hồ sơ đạo đức, SAP và đề cương chỉ lộ ra khi Hội đồng hay tạp chí đọc. Bác sĩ yêu cầu
04/10/2026: các cổng phải «có sự điều phối giữa các cổng một cách thống nhất».

LÀM GÌ (CHỈ ĐỌC exports/<study>/, không sửa artifact nào, không chọn giá trị «đúng» thay chủ nhiệm):
  • Gom giá trị của từng thông số từ MỌI nơi nó xuất hiện (cổng · nơi đọc · giá trị).
  • Xếp mức:
    - LỆCH CỨNG (G10 CHẶN — phải sửa trước khi phát hành): cỡ mẫu kế hoạch · alpha · power · mã thiết kế · loại
      nghiên cứu khai ở đăng ký (Interventional/Observational) trái với thiết kế · loại giả thuyết (G0 ↔ G3 ↔ SAP §12) ·
      sai số cho phép d của thiết kế theo độ chính xác (G3 ↔ SAP §12) — hai trục cuối thêm 06/10/2026.
    - LỆCH MỀM (G10 giữ ở DRAFT — chủ nhiệm xác nhận/giải trình): kết cục chính khác nhau giữa các cổng (so theo mã
      biến/định danh trước, rồi theo độ trùng từ). Đổi kết cục chính là lỗi liêm chính kinh điển (outcome switching).
      Phép so từ CỐ Ý CHẶT («tử vong» ≠ «tử vong do tim mạch»): bỏ sót đổi kết cục nguy hơn một lần chủ nhiệm giải
      trình. Khi các mô tả thật ra là MỘT kết cục, chủ nhiệm ghi `gate_params.G10.xac_nhan_ket_cuc_chinh` gồm
      `giai_trinh` + `reviewed_at` (ISO, không ở tương lai) + `dau_van_tay` (CLI in ra) — xác nhận GẮN với đúng tập mô
      tả lúc xác nhận; mô tả đổi sau đó ⇒ xác nhận hết hiệu lực. Có xác nhận hợp lệ ⇒ hạ xuống CẦN XEM (vẫn hiện ra).
      Khi kết cục chính ĐÃ ĐỔI THẬT (06/10/2026, G10-07): chủ nhiệm khai `gate_params.G10.sua_doi_ket_cuc_chinh` (danh
      sách theo thời gian; mỗi lần: ket_cuc_cu · ket_cuc_moi · ly_do ≥ 30 ký tự · ma_sua_doi · ngay_sua_doi ·
      irb_chap_thuan · dang_ky_cap_nhat · ngay_cap_nhat_dang_ky · reviewed_by_role=PI · reviewed_at; lần cuối gắn
      dau_van_tay; tới bản thảo thì thêm cong_bo_trong_ban_thao). Hợp lệ khi: chuỗi nối tiếp, mọi nơi ghi thuộc chuỗi,
      SAP §2 và khai báo G8 là kết cục MỚI nhất (G0/G1/bản nháp đăng ký được giữ kết cục cũ — không sửa ngược hồ sơ
      cổng), sửa TRƯỚC ngày khoá dữ liệu, bản thảo có câu báo cáo thay đổi (CONSORT 2025 mục 10; SPIRIT 2025 mục 31)
      ⇒ CẦN XEM; thiếu bất kỳ điều nào ⇒ LỆCH MỀM kèm lý do.
    - CẦN XEM (chỉ báo, không đổi trạng thái cổng): quần thể diễn đạt khác xa nhau; cỡ mẫu được tính cho một kết cục
      mà G1 xếp là THỨ CẤP; thiết kế chẩn đoán khai «Interventional» ở đăng ký (cơ quan đăng ký xếp khác nhau).
  • Thông số có ở < 2 nơi ⇒ «chưa đủ để so» — KHÔNG phải «khớp». Ở G10, thông số BẮT BUỘC theo thiết kế (mã thiết kế ·
    cỡ mẫu trừ định tính/tổng quan · kết cục chính trừ định tính) mà «chưa đủ để so» ⇒ REVIEW.

Mã thoát CLI (theo trạng thái G10): 0 PASS · 1 REVIEW (lệch mềm / thông số bắt buộc chưa đủ để so) · 2 BLOCK (lệch
cứng) · 3 không đọc được đề tài hoặc bộ đối chiếu hỏng.
Cần bác sĩ kiểm chứng.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import sys
import unicodedata
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

BASE = Path(__file__).resolve().parents[1]
TOOLS = BASE / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

MUC_KHOP = "khop"
MUC_LECH_CUNG = "lech_cung"
MUC_LECH_MEM = "lech_mem"
MUC_CAN_XEM = "can_xem"
MUC_CHUA_DU = "chua_du"
_THU_TU_MUC = {MUC_LECH_CUNG: 4, MUC_LECH_MEM: 3, MUC_CAN_XEM: 2, MUC_KHOP: 1, MUC_CHUA_DU: 0}
BIEU_TUONG = {MUC_LECH_CUNG: "🔴", MUC_LECH_MEM: "🟠", MUC_CAN_XEM: "🟡", MUC_KHOP: "🟢", MUC_CHUA_DU: "⚪"}

# Loại nghiên cứu mục TRDS 15 suy từ thiết kế — chỉ hai tập CHẮC CHẮN; thiết kế khác không so (tránh lệch cứng giả).
THIET_KE_CAN_THIEP = frozenset({"rct", "non_randomized"})
THIET_KE_QUAN_SAT = frozenset({"case_control", "cohort", "cross_sectional", "case_report", "prediction"})
# Nghiên cứu độ chính xác chẩn đoán: cơ quan đăng ký xếp khi Interventional khi Observational ⇒ chỉ CẦN XEM.
THIET_KE_DANG_KY_MO_HO = frozenset({"diagnostic"})
# Thông số mà G10 đòi phải SO ĐƯỢC (≥ 2 nơi) theo thiết kế — thiếu ⇒ REVIEW, không phải PASS im lặng.
_KHONG_CO_CO_MAU = frozenset({"qualitative", "sr_ma", "systematic_review"})
_KHONG_CO_KET_CUC = frozenset({"qualitative"})
# Thông số không áp dụng theo khung §12 (g4_quality_gate.loai_muc_12): độ chính xác / SR–dự báo không có power; định
# tính không có alpha lẫn power.
_KHONG_AP_DUNG_THEO_MUC_12 = {"chinh_xac": frozenset({"power"}), "khong_power": frozenset({"power"}),
                              "dinh_tinh": frozenset({"alpha", "power"})}

_DINH_DANH = re.compile(r"\b[A-Za-z][A-Za-z0-9]*_[A-Za-z0-9_]+\b")
_TU = re.compile(r"[0-9]+/[0-9]+|>=|<=|≥|≤|\w+", re.UNICODE)
_TU_DUNG = frozenset("""của và cho theo là có các được trong khi với một những để từ này đó thì ở trên dưới bằng hay
hoặc nếu chỉ cũng như đã sẽ đang the of and for in to a an with on by or at from""".split())
_O_TRONG = re.compile(
    r"^\s*(\[\s*CẦN|\[\s*CAN\s|TBD\b|TODO\b|N/?A\b|none\b|null\b|chưa\s+(có|xác định)\b|[—–\-]+\s*$)", re.I)
# Số đầu tiên trong một chuỗi; nhận dấu phân cách nghìn kiểu Việt («1.000») lẫn kiểu Anh («1,000»), khoảng trắng mỏng.
_SO = re.compile(r"[-+]?\d+(?:[.,   ]\d{3})*(?:[.,]\d+)?")
_NGHIN = re.compile(r"^[-+]?\d{1,3}(?:[.,   ]\d{3})+$")


# ----------------------------------------------------------------------------------------------- đọc
def _doc_json(p: Path) -> Dict[str, Any]:
    try:
        v = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return v if isinstance(v, dict) else {}


def _doc_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def _co_that(v: Any) -> bool:
    """Giá trị THẬT (không rỗng, không ô mẫu «[CẦN …]», không «None»/«—»). Số 0 vẫn là giá trị thật ở tầng này —
    bộ chuẩn hoá của từng thông số tự loại số vô nghĩa (N = 0, α = 0)."""
    if v is None or isinstance(v, bool):
        return False
    if isinstance(v, (int, float)):
        return True
    if isinstance(v, (list, dict)):
        return any(_co_that(x) for x in (v.values() if isinstance(v, dict) else v))
    s = str(v).strip()
    return bool(s) and not _O_TRONG.match(s) and "[CẦN" not in s.upper()


def _van_ban(v: Any) -> str:
    """Mọi kiểu giá trị (chuỗi, dict, list, repr dict) ⇒ một chuỗi để so từ. dict/list không làm hỏng bộ so."""
    v = _mo_repr(v)
    if isinstance(v, dict):
        return "; ".join(_van_ban(x) for x in v.values() if _co_that(x))
    if isinstance(v, (list, tuple, set)):
        return "; ".join(_van_ban(x) for x in v if _co_that(x))
    return str(v).strip() if _co_that(v) else ""


def _gp(meta: Dict[str, Any], gate: str) -> Dict[str, Any]:
    gps = meta.get("gate_params")
    v = (gps if isinstance(gps, dict) else {}).get(gate) or {}
    return v if isinstance(v, dict) else {}


def _mo_repr(v: Any) -> Any:
    """Giá trị mục TRDS có thể là repr của dict/list (str(dict)) — mở an toàn bằng literal_eval, hỏng thì giữ chuỗi."""
    if isinstance(v, str) and v.strip()[:1] in "{[":
        try:
            return ast.literal_eval(v.strip())
        except (ValueError, SyntaxError, MemoryError, RecursionError):
            return v
    return v


def _ten_ket_cuc(v: Any) -> str:
    v = _mo_repr(v)
    if isinstance(v, dict):
        for k in ("name", "ten", "label", "outcome"):
            if _co_that(v.get(k)):
                return _van_ban(v[k])
        return ""
    if isinstance(v, list):
        return "; ".join(_ten_ket_cuc(x) for x in v if _co_that(x))
    return str(v).strip() if _co_that(v) else ""


def _trds(out_dir: Path, study: str) -> Dict[str, Any]:
    """{số mục TRDS: giá trị} của bản đăng ký G2 (nếu có)."""
    d = _doc_json(out_dir / f"G2_REGISTRATION_DRAFT_{study}.json")
    ra: Dict[str, Any] = {}
    items = d.get("items")
    for it in items if isinstance(items, list) else []:
        if isinstance(it, dict) and str(it.get("number", "")).strip():
            ra[str(it["number"]).strip()] = it.get("value")
    return ra


def _sap(out_dir: Path, study: str) -> Tuple[str, Dict[str, Any]]:
    """(văn bản SAP, số liệu §12 đã đọc bằng ĐÚNG bộ đọc của g4_quality_gate)."""
    try:
        import g4_quality_gate as G4Q  # noqa: PLC0415
        text = _doc_text(out_dir / G4Q.sap_artifact_name(study))
        return text, (G4Q.parse_signed_numbers(text) if text else {})
    except Exception:  # noqa: BLE001 — thiếu bộ đọc ⇒ không so nguồn SAP (vẫn so các nguồn khác)
        return "", {}


def _ket_cuc_chinh_sap(text: str) -> str:
    try:
        import g4_quality_gate as G4Q  # noqa: PLC0415
        than = G4Q._section_body(text, "§2")
    except Exception:  # noqa: BLE001
        than = ""
    m = re.search(r"\*\*Kết cục chính:\*\*\s*(.+)", than)
    return m.group(1).strip() if m else ""


# ----------------------------------------------------------------------------------------------- so
def _so_dau(v: Any) -> Optional[float]:
    """Số đầu tiên của giá trị: số thật giữ nguyên; chuỗi «N = 1.000 người» ⇒ 1000.0; «0,05» ⇒ 0.05; «80%» ⇒ 80.0."""
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    m = _SO.search(unicodedata.normalize("NFC", str(v)))
    if not m:
        return None
    t = m.group(0)
    if _NGHIN.match(t):
        t = re.sub(r"[.,   ]", "", t)
    else:
        t = t.replace(" ", "").replace(" ", "").replace(" ", "").replace(",", ".")
    try:
        return float(t)
    except ValueError:
        return None


def _so_nguyen(v: Any) -> Optional[int]:
    """Cỡ mẫu: số nguyên dương; 0/âm/không đọc được ⇒ None (không phải một giá trị để so)."""
    x = _so_dau(v)
    if x is None or x <= 0:
        return None
    return int(round(x))


def _ty_le(v: Any) -> Optional[float]:
    """alpha/power về dạng phân số (80 hoặc «80%» ⇒ 0.8). 0 hoặc > 100 ⇒ None (vô nghĩa, không đem so)."""
    x = _so_dau(v)
    if x is None or x <= 0 or x > 100:
        return None
    return round(x / 100.0, 6) if x > 1 else round(x, 6)


def _tu(s: Any) -> set:
    s = unicodedata.normalize("NFC", _van_ban(s)).lower()
    return {t for t in _TU.findall(s) if t not in _TU_DUNG and (len(t) > 1 or t.isdigit())}


def _dinh_danh(s: Any) -> set:
    return {t.lower() for t in _DINH_DANH.findall(_van_ban(s))}


def cung_ket_cuc(a: Any, b: Any) -> bool:
    """Hai mô tả có cùng chỉ MỘT kết cục? Mã biến/định danh trùng ⇒ cùng; cả hai có định danh mà rời nhau ⇒ khác; còn
    lại xét độ trùng từ (Jaccard ≥ 0,5). CỐ Ý CHẶT — xem docstring module (xác nhận của chủ nhiệm)."""
    da, db = _dinh_danh(a), _dinh_danh(b)
    if da and db:
        return bool(da & db)
    ta, tb = _tu(a), _tu(b)
    if not ta or not tb:
        return False
    return len(ta & tb) / len(ta | tb) >= 0.5


def _bao_ham(con: Any, cha: Any) -> float:
    """Tỉ lệ từ của `con` có mặt trong `cha` (độ bao hàm, dùng cho văn bản dài–ngắn lệch nhau)."""
    tc = _tu(con)
    return (len(tc & _tu(cha)) / len(tc)) if tc else 0.0


#: Ngưỡng phủ khi so quần thể theo CHIỀU CỔNG (bản trước → bản sau): dưới ngưỡng ⇒ cần xem.
NGUONG_PHU_QUAN_THE = 0.7


_NGUONG_RE = re.compile(
    r"(?:(≥|≤|>=|<=|>|<|từ|đủ|trên|dưới|ít nhất|tối thiểu|tối đa|không quá|hơn)\s*)?(\d+(?:[.,]\d+)?)\s*"
    r"(tuổi|tháng|năm|tuần|ngày|giờ|kg|mmhg|%|lần)?",
    re.IGNORECASE)


def _nguong_quan_the(s: Any) -> set:
    """Các NGƯỠNG tiêu chí chọn trong mô tả quần thể: con số đi kèm dấu so sánh («≥18», «từ 18») hoặc đơn vị
    («3 tháng», «60 tuổi»). Con số trơn (tên bệnh viện «175», số mục «4.3», mã khoa «C1») KHÔNG phải ngưỡng."""
    ra = set()
    van = unicodedata.normalize("NFC", _van_ban(s)).lower()
    for m in _NGUONG_RE.finditer(van):
        so_sanh, so, don_vi = m.group(1) or "", m.group(2), m.group(3) or ""
        # Ngày/tháng/năm («01/2026», «1/2026», «2026-01») KHÔNG phải ngưỡng tiêu chí (sửa theo thẩm định #268).
        if van[m.end(2):m.end(2) + 1] in ("/", "-") or van[max(0, m.start(2) - 1):m.start(2)] in ("/", "-"):
            continue
        if not (so_sanh or don_vi):
            continue
        so_sanh = {">=": "≥", "<=": "≤", "từ": "≥", "đủ": "≥", "ít nhất": "≥", "tối thiểu": "≥", "trên": ">",
                   "hơn": ">",
                   "dưới": "<", "tối đa": "≤", "không quá": "≤"}.get(so_sanh, so_sanh)
        ra.add(f"{so_sanh}{so.replace(',', '.')}{(' ' + don_vi) if don_vi else ''}".strip())
    return ra


def _so_quan_the_hai_chieu(nguon_qt: List[Dict[str, Any]]) -> Dict[str, Any]:
    """So quần thể THEO CẢ HAI CHIỀU (bác sĩ duyệt 15/11/2026, kiểm đồng bộ xuyên cổng).

    Bản cũ lấy max(bao_hàm(a⊂b), bao_hàm(b⊂a)) cho mỗi cặp ⇒ bản sau CHỈ cần là tập con của bản trước là «khớp 1.00»:
    G1 bỏ hẳn «đang điều trị ≥3 tháng… tại phòng khám nội tim mạch» của G0 vẫn 🟢 (đo trên giả lập
    ZZSIM-DONGBO-TUANTHU-THA-20261115). Nay xét chiều CỔNG: từ của bản TRƯỚC có còn trong bản SAU không.
      • mất NGƯỠNG SỐ (con số/so sánh ≥ ≤ của bản trước vắng ở bản sau) ⇒ LỆCH MỀM — đổi tiêu chí chọn là đổi quần thể,
        chủ nhiệm giải trình như đổi kết cục (G10-AUTO-11 giữ REVIEW);
      • phủ < NGUONG_PHU_QUAN_THE ⇒ CẦN XEM, kèm danh sách từ bị mất (không đổi trạng thái cổng — diễn đạt khác nhau tự
        nhiên).
    Nguồn đến theo thứ tự cổng (G0 → G1 → G2), nên cặp (i, j>i) đúng chiều trước → sau."""
    mat_so: List[str] = []
    ghi: List[str] = []
    thap = 1.0
    for i, a in enumerate(nguon_qt):
        for b in nguon_qt[i + 1:]:
            phu = _bao_ham(a["gia_tri"], b["gia_tri"])
            thap = min(thap, phu)
            thieu = sorted(_tu(a["gia_tri"]) - _tu(b["gia_tri"]))
            # So theo CON SỐ của ngưỡng: «≥18» (G0) và «đủ 18 tuổi» (G1) là cùng ngưỡng — diễn đạt khác không phải mất;
            # con số của ngưỡng bản trước VẮNG HẲN ở bản sau («≥3 tháng» bị bỏ) mới là mất ngưỡng.
            so_b = set(re.findall(r"\d+(?:[.,]\d+)?", _van_ban(b["gia_tri"]).replace(",", ".")))
            so_thieu = sorted(t for t in _nguong_quan_the(a["gia_tri"])
                              if (re.search(r"\d+(?:\.\d+)?", t) or [None])[0] not in so_b)
            if so_thieu:
                mat_so.append(f"{b['cong']} mất ngưỡng của {a['cong']}: {', '.join(so_thieu)}")
            if phu < NGUONG_PHU_QUAN_THE and thieu:
                ghi.append(f"{b['cong']} thiếu so với {a['cong']} (phủ {phu:.2f}): {', '.join(thieu[:12])}")
    if mat_so:
        return _ket("quan_the", "Quần thể nghiên cứu", nguon_qt, MUC_LECH_MEM,
                    "; ".join(mat_so + ghi) + " — tiêu chí chọn bị mất/đổi giữa các cổng; thống nhất tại cổng gốc "
                    "hoặc chủ nhiệm giải trình")
    if ghi:
        return _ket("quan_the", "Quần thể nghiên cứu", nguon_qt, MUC_CAN_XEM,
                    "; ".join(ghi) + " — chủ nhiệm đọc lại xem có tiêu chí nào bị mất")
    return _ket("quan_the", "Quần thể nghiên cứu", nguon_qt, MUC_KHOP,
                f"phủ theo chiều cổng thấp nhất {thap:.2f} (từ của bản trước còn trong bản sau)")


def _muc_cao_nhat(muc: Iterable[str]) -> str:
    ds = list(muc)
    return max(ds, key=lambda m: _THU_TU_MUC[m]) if ds else MUC_CHUA_DU


def _ket(ma: str, ten: str, nguon: List[Dict[str, Any]], muc: str, ghi_chu: str) -> Dict[str, Any]:
    return {"ma": ma, "ten": ten, "muc": muc, "nguon": nguon, "ghi_chu": ghi_chu}


def _so_bang_nhau(ma: str, ten: str, nguon: List[Dict[str, Any]], chuan) -> Dict[str, Any]:
    """Thông số số học: mọi nguồn có giá trị phải TRÙNG nhau sau chuẩn hoá — lệch ⇒ LỆCH CỨNG."""
    co = [n for n in nguon if chuan(n["gia_tri"]) is not None]
    if len(co) < 2:
        return _ket(ma, ten, nguon, MUC_CHUA_DU, "chỉ có ≤ 1 nơi ghi — chưa đủ để so (KHÔNG phải «khớp»)")
    khac = sorted({chuan(n["gia_tri"]) for n in co})
    if len(khac) == 1:
        return _ket(ma, ten, nguon, MUC_KHOP, f"{len(co)} nơi cùng giá trị {khac[0]}")
    return _ket(ma, ten, nguon, MUC_LECH_CUNG,
                f"{len(khac)} giá trị khác nhau {khac} — sửa về MỘT giá trị (nguồn gốc là cổng tính ra nó) rồi chạy "
                "lại các cổng sau")


def _loai_dang_ky(loai: Any) -> Optional[str]:
    """Loại nghiên cứu khai ở TRDS 15 ⇒ «interventional»/«observational»/None. So theo TỪ, không theo chuỗi con:
    «Non-interventional» là quan sát (bản cũ so chuỗi con nên «interventional» lọt qua cho thiết kế RCT)."""
    s = unicodedata.normalize("NFC", _van_ban(loai)).lower()
    s = re.sub(r"\bnon[\s\-_]*interventional\b", "observational", s)
    s = re.sub(r"\bkhông\s+can\s+thiệp\b", "quan sát", s)
    tu = set(re.findall(r"\w+", s))
    can_thiep = "interventional" in tu or "can thiệp" in s
    quan_sat = "observational" in tu or "quan sát" in s
    if can_thiep and not quan_sat:
        return "interventional"
    if quan_sat and not can_thiep:
        return "observational"
    return None


def dau_van_tay_ket_cuc(nguon_kc: List[Dict[str, Any]]) -> str:
    """Dấu vân tay của TẬP mô tả kết cục chính đang có (cổng · nơi · giá trị đã chuẩn hoá NFC + bỏ khoảng trắng thừa).
    Chủ nhiệm xác nhận «cùng một kết cục» phải chép đúng dấu này — mô tả đổi ⇒ dấu đổi ⇒ xác nhận hết hiệu lực."""
    phan = sorted(f"{n['cong']}|{n['noi']}|{' '.join(unicodedata.normalize('NFC', str(n['gia_tri'])).split())}"
                  for n in nguon_kc)
    return hashlib.sha256("\n".join(phan).encode("utf-8")).hexdigest()[:16]


def _iso_khong_tuong_lai(v: Any) -> bool:
    text = str(v or "").strip()
    if not text:
        return False
    try:
        t = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return False
    return t <= (datetime.now(tz=t.tzinfo) if t.tzinfo else datetime.now())


def _xac_nhan_ket_cuc(meta: Dict[str, Any], dau: str) -> Tuple[bool, str]:
    """(hợp lệ?, lý do) của `gate_params.G10.xac_nhan_ket_cuc_chinh` cho tập mô tả có dấu `dau`."""
    xn = _gp(meta, "G10").get("xac_nhan_ket_cuc_chinh")
    if not isinstance(xn, dict):
        return False, "chưa có xác nhận của chủ nhiệm"
    gt = str(xn.get("giai_trinh") or "").strip()
    if not _co_that(gt) or len(gt) < 15:
        return False, "xác nhận thiếu `giai_trinh` có nội dung"
    if not _iso_khong_tuong_lai(xn.get("reviewed_at")):
        return False, "xác nhận thiếu `reviewed_at` ISO hợp lệ (không ở tương lai)"
    if str(xn.get("dau_van_tay") or "").strip().lower() != dau:
        return False, f"xác nhận gắn với tập mô tả KHÁC (dấu hiện tại {dau}) — mô tả đã đổi sau khi xác nhận"
    return True, gt


# ── SỬA ĐỔI kết cục chính có kiểm chứng (06/10/2026 — bác sĩ yêu cầu giải quyết G10-07 «triệt để») ──────────────────
# Trước đây lệch kết cục chính chỉ có MỘT lối ra: chủ nhiệm xác nhận «cùng một kết cục, khác diễn đạt». Đổi kết cục THẬT
# (có lý do chính đáng) thì không có đường đi — hoặc nói dối «cùng kết cục», hoặc kẹt REVIEW mãi. Đổi kết cục chỉ chính
# đáng khi đủ: sửa đổi đề cương có MÃ + LÝ DO, Hội đồng đạo đức chấp thuận, bản đăng ký được cập nhật, bản thảo BÁO CÁO
# thay đổi — CONSORT 2025 mục 10 «Important changes to the trial after it commenced including any outcomes or analyses
# that were not prespecified, with reason» (PMID 40228477) · SPIRIT 2025 mục 31 (kế hoạch truyền đạt sửa đổi đề cương
# quan trọng; PMID 40294593) — và sửa TRƯỚC khi khoá dữ liệu (đã thấy dữ liệu ⇒ kết cục mới là HẬU KIỂM, không được
# trình bày như kết cục tiền định). Hồ sơ cổng cũ KHÔNG sửa ngược: G0/G1 và bản nháp đăng ký G2 được giữ kết cục cũ; kế
# hoạch HIỆN HÀNH — SAP §2 (G4) và khai báo bản thảo (G8) — phải là kết cục MỚI nhất của chuỗi sửa đổi.
TRUONG_SUA_DOI_KET_CUC = ("ket_cuc_cu", "ket_cuc_moi", "ly_do", "ma_sua_doi", "ngay_sua_doi", "irb_chap_thuan",
                          "dang_ky_cap_nhat", "ngay_cap_nhat_dang_ky", "reviewed_by_role", "reviewed_at")
_CONG_KE_HOACH_HIEN_HANH = frozenset({"G4", "G8"})
_LY_DO_SUA_DOI_TOI_THIEU = 30
_TU_THAY_DOI = re.compile(r"thay\s*đổi|sửa\s*đổi|điều\s*chỉnh|chang(?:e|ed|es)|amend|modif", re.IGNORECASE)


def _ngay(v: Any) -> Optional[date]:
    """Ngày từ chuỗi ISO «YYYY-MM-DD[...]»; None nếu không phải."""
    text = str(v or "").strip()
    if not re.match(r"^\d{4}-\d{2}-\d{2}", text):
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def ngay_khoa_du_lieu(out_dir: Path, meta: Dict[str, Any]) -> Optional[date]:
    """Ngày khoá dữ liệu SỚM NHẤT đã ghi (study_meta.data_lock_date · manifest khoá dữ liệu `lock_date`); None nếu
    chưa khoá."""
    rdl = meta.get("real_data_lock") if isinstance(meta.get("real_data_lock"), dict) else {}
    man = _doc_json(Path(out_dir) / (rdl.get("manifest") or "DATA_LOCK_manifest.json"))
    ung = [d for d in (_ngay(meta.get("data_lock_date")), _ngay(man.get("lock_date"))) if d]
    return min(ung) if ung else None


def danh_sach_sua_doi_ket_cuc(meta: Dict[str, Any]) -> Optional[List[Any]]:
    """Khối `gate_params.G10.sua_doi_ket_cuc_chinh` dạng danh sách (một lần sửa đổi ghi dạng dict cũng nhận); None
    nếu vắng."""
    ds = _gp(meta, "G10").get("sua_doi_ket_cuc_chinh")
    if ds is None:
        return None
    return [ds] if isinstance(ds, dict) else (ds if isinstance(ds, list) else [ds])


def _ban_thao_bao_cao_thay_doi(ban_thao: str, ket_cuc_cu: Any) -> bool:
    """Bản thảo có MỘT dòng vừa nói «thay đổi/sửa đổi/changed…» vừa nêu kết cục cũ (≥ nửa số từ) — CONSORT 2025
    mục 10."""
    return any(_TU_THAY_DOI.search(d) and _bao_ham(ket_cuc_cu, d) >= 0.5 for d in ban_thao.splitlines())


def kiem_sua_doi_ket_cuc(meta: Dict[str, Any], out_dir: Path, study: str, nguon_kc: List[Dict[str, Any]],
                         dau: str) -> Tuple[Optional[str], str]:
    """(mức, ghi chú) của chuỗi sửa đổi kết cục chính khai ở G10; (None, "") nếu không khai. CHỈ ĐỌC.

    Hợp lệ ⇒ CẦN XEM (vẫn hiện ra để Hội đồng/tạp chí thấy, không chặn). Thiếu trường / chuỗi đứt / kế hoạch hiện hành
    còn kết cục cũ / sửa SAU khi khoá dữ liệu / bản thảo không báo cáo / dấu vân tay cũ ⇒ LỆCH MỀM kèm lý do."""
    ds = danh_sach_sua_doi_ket_cuc(meta)
    if ds is None:
        return None, ""
    if not ds or not all(isinstance(x, dict) for x in ds):
        return MUC_LECH_MEM, "khối sua_doi_ket_cuc_chinh không đúng dạng (danh sách các lần sửa đổi, mỗi lần một dict)"
    loi: List[str] = []
    ngay_truoc: Optional[date] = None
    for i, sd in enumerate(ds, 1):
        thieu = [k for k in TRUONG_SUA_DOI_KET_CUC if not _co_that(sd.get(k))]
        if thieu:
            loi.append(f"lần {i} thiếu {', '.join(thieu)}")
            continue
        if len(str(sd["ly_do"]).strip()) < _LY_DO_SUA_DOI_TOI_THIEU:
            loi.append(f"lần {i}: lý do quá ngắn — CONSORT 2025 mục 10 đòi nêu lý do")
        if str(sd["reviewed_by_role"]).strip().upper() != "PI":
            loi.append(f"lần {i}: reviewed_by_role phải là PI (chủ nhiệm chịu trách nhiệm sửa đổi)")
        if not _iso_khong_tuong_lai(sd["reviewed_at"]):
            loi.append(f"lần {i}: reviewed_at không phải ISO hợp lệ hoặc ở tương lai")
        ngay_sd, ngay_dk = _ngay(sd["ngay_sua_doi"]), _ngay(sd["ngay_cap_nhat_dang_ky"])
        if ngay_sd is None or ngay_sd > date.today():
            loi.append(f"lần {i}: ngay_sua_doi không phải ngày ISO hợp lệ hoặc ở tương lai")
        if ngay_dk is None or ngay_dk > date.today():
            loi.append(f"lần {i}: ngay_cap_nhat_dang_ky không phải ngày ISO hợp lệ hoặc ở tương lai")
        if ngay_sd and ngay_truoc and ngay_sd < ngay_truoc:
            loi.append(f"lần {i}: ngày sửa đổi sớm hơn lần trước — chuỗi phải theo thời gian")
        ngay_truoc = ngay_sd or ngay_truoc
        if cung_ket_cuc(sd["ket_cuc_cu"], sd["ket_cuc_moi"]):
            loi.append(f"lần {i}: kết cục cũ và mới là MỘT kết cục — khác diễn đạt thì dùng xac_nhan_ket_cuc_chinh")
        if i > 1 and _co_that(ds[i - 2].get("ket_cuc_moi")) and not cung_ket_cuc(ds[i - 2]["ket_cuc_moi"],
                                                                                  sd["ket_cuc_cu"]):
            loi.append(f"lần {i}: ket_cuc_cu không nối tiếp ket_cuc_moi của lần {i - 1}")
    if str(ds[-1].get("dau_van_tay") or "").strip().lower() != dau:
        loi.append(f"lần sửa đổi cuối chưa gắn dấu vân tay hiện tại {dau} — mô tả kết cục đã đổi sau khi khai")
    if loi:
        return MUC_LECH_MEM, "khối sửa đổi kết cục chính CHƯA hợp lệ: " + "; ".join(loi)

    phien_ban = [ds[0]["ket_cuc_cu"], *[sd["ket_cuc_moi"] for sd in ds]]
    moi_nhat = phien_ban[-1]
    ngoai_chuoi = [n for n in nguon_kc if not any(cung_ket_cuc(n["gia_tri"], v) for v in phien_ban)]
    if ngoai_chuoi:
        return MUC_LECH_MEM, ("nơi ghi kết cục KHÔNG thuộc chuỗi sửa đổi: "
                              + ", ".join(f"{n['cong']} ({n['noi']})" for n in ngoai_chuoi))
    cu_hien_hanh = [n for n in nguon_kc if n["cong"] in _CONG_KE_HOACH_HIEN_HANH
                    and not cung_ket_cuc(n["gia_tri"], moi_nhat)]
    if cu_hien_hanh:
        return MUC_LECH_MEM, ("kế hoạch HIỆN HÀNH vẫn ghi kết cục cũ ("
                              + ", ".join(f"{n['cong']} {n['noi']}" for n in cu_hien_hanh)
                              + f") — sửa đổi phải đưa «{str(moi_nhat)[:60]}» vào SAP (SAP AMENDMENT) và khai báo "
                              "bản thảo")
    khoa = ngay_khoa_du_lieu(out_dir, meta)
    sau_khoa = [i for i, sd in enumerate(ds, 1) if khoa and _ngay(sd["ngay_sua_doi"]) >= khoa]
    if sau_khoa:
        return MUC_LECH_MEM, (f"sửa đổi lần {sau_khoa} vào/sau ngày khoá dữ liệu {khoa.isoformat()} — kết cục mới là "
                              "HẬU KIỂM: giữ kết cục tiền định làm kết cục chính, báo cáo kết cục mới như phân tích "
                              "không tiền định (CONSORT 2025 mục 10)")
    ban_thao = _doc_text(Path(out_dir) / f"G7_A8_MANUSCRIPT_{study}.md")
    if any(n["cong"] == "G8" for n in nguon_kc) or ban_thao.strip():
        thieu_cb = [i for i, sd in enumerate(ds, 1) if not _co_that(sd.get("cong_bo_trong_ban_thao"))]
        if thieu_cb:
            return MUC_LECH_MEM, (f"đã tới bản thảo nhưng lần {thieu_cb} thiếu cong_bo_trong_ban_thao (vị trí báo cáo "
                                  "thay đổi trong bài — CONSORT 2025 mục 10)")
        if ban_thao.strip():
            chua_bao = [i for i, sd in enumerate(ds, 1) if not _ban_thao_bao_cao_thay_doi(ban_thao, sd["ket_cuc_cu"])]
            if chua_bao:
                return MUC_LECH_MEM, (f"bản thảo G7 không có câu nào báo cáo thay đổi kết cục ở lần {chua_bao} (cần "
                                      "một câu nêu kết cục cũ kèm «thay đổi/sửa đổi» — CONSORT 2025 mục 10)")
    tom = "; ".join(f"«{str(sd['ket_cuc_cu'])[:50]}» → «{str(sd['ket_cuc_moi'])[:50]}» ({sd['ma_sua_doi']}, "
                    f"{sd['ngay_sua_doi']}; HĐĐĐ: {str(sd['irb_chap_thuan'])[:40]}; đăng ký: "
                    f"{str(sd['dang_ky_cap_nhat'])[:40]})" for sd in ds)
    return MUC_CAN_XEM, (f"kết cục chính ĐÃ SỬA ĐỔI có kiểm chứng: {tom} — báo cáo thay đổi kèm lý do (CONSORT 2025 "
                         "mục 10 · SPIRIT 2025 mục 31)")


def doi_chieu(out_dir: Path, study: Optional[str] = None) -> Dict[str, Any]:
    """Đối chiếu các thông số then chốt xuyên cổng của MỘT đề tài. CHỈ ĐỌC."""
    out_dir = Path(out_dir)
    study = study or out_dir.name
    meta = _doc_json(out_dir / "study_meta.json")
    cp = {g: _doc_json(out_dir / f"{g}_checkpoint.json") for g in (f"G{i}" for i in range(11))}
    trds = _trds(out_dir, study)
    sap_text, sap12 = _sap(out_dir, study)
    ket: List[Dict[str, Any]] = []

    # 1) Cỡ mẫu kế hoạch.
    g3 = cp["G3"]
    n_g3_noi, n_g3 = ("G3_checkpoint.confirmed_n", g3.get("confirmed_n"))
    if _so_nguyen(n_g3) is None:
        if _so_nguyen(g3.get("n_adjusted")) is not None:
            n_g3_noi, n_g3 = ("G3_checkpoint.n_adjusted", g3.get("n_adjusted"))
        else:
            n_g3_noi, n_g3 = ("G3_checkpoint.n_total", g3.get("n_total"))
    nguon_n = [
        {"cong": "G3", "noi": n_g3_noi, "gia_tri": n_g3},
        {"cong": "G3", "noi": "study_meta.gate_params.G3.confirmed_n", "gia_tri": _gp(meta, "G3").get("confirmed_n")},
        {"cong": "G2", "noi": "đăng ký TRDS mục 17 (Target Sample Size)", "gia_tri": trds.get("17")},
        {"cong": "G4", "noi": "G4_checkpoint.n_from_g3", "gia_tri": cp["G4"].get("n_from_g3")},
        {"cong": "G4", "noi": "SAP §12 «Cỡ mẫu: N = …»", "gia_tri": sap12.get("n")},
    ]
    ket.append(_so_bang_nhau("co_mau", "Cỡ mẫu kế hoạch (N)", [n for n in nguon_n if _co_that(n["gia_tri"])],
                             _so_nguyen))

    # 2) Alpha · power.
    for ma, ten, khoa_g3, gt_sap in (("alpha", "Alpha (α)", "alpha", sap12.get("alpha")),
                                     ("power", "Power (1−β)", "power", sap12.get("power_pct"))):
        nguon = [{"cong": "G3", "noi": f"G3_checkpoint.{khoa_g3}", "gia_tri": g3.get(khoa_g3)},
                 {"cong": "G4", "noi": f"SAP §12 {ten}", "gia_tri": gt_sap}]
        ket.append(_so_bang_nhau(ma, ten, [n for n in nguon if _co_that(n["gia_tri"])], _ty_le))

    # 3) Thiết kế.
    try:
        import skill_standards as SK  # noqa: PLC0415
        canon = SK.canonical_design_code
    except Exception:  # noqa: BLE001
        def canon(x):  # type: ignore[no-redef]
            return str(x).strip().lower() if x else None
    g1_design = cp["G1"].get("design")
    nguon_tk = [{"cong": "—", "noi": "study_meta.design_code", "gia_tri": meta.get("design_code")},
                {"cong": "G1", "noi": "study_meta.gate_params.G1.design", "gia_tri": _gp(meta, "G1").get("design")},
                {"cong": "G1", "noi": "G1_checkpoint.design.internal_code",
                 "gia_tri": g1_design.get("internal_code") if isinstance(g1_design, dict) else None}]
    for g in ("G2", "G3", "G4", "G5", "G6", "G7", "G8", "G9", "G10"):
        nguon_tk.append({"cong": g, "noi": f"{g}_checkpoint.design_code", "gia_tri": cp[g].get("design_code")})
    nguon_tk = [n for n in nguon_tk if isinstance(n["gia_tri"], str) and _co_that(n["gia_tri"])]
    ket_tk = _so_bang_nhau("thiet_ke", "Mã thiết kế", nguon_tk, lambda v: canon(v) if _co_that(v) else None)
    # Loại nghiên cứu khai ở đăng ký (TRDS 15) phải hợp với thiết kế.
    loai = _mo_repr(trds.get("15"))
    loai = (loai.get("design") or loai.get("type") if isinstance(loai, dict) else loai) or ""
    ma_tk = {canon(n["gia_tri"]) for n in nguon_tk}
    if _co_that(loai) and len(ma_tk) == 1:
        tk = next(iter(ma_tk))
        mong = "interventional" if tk in THIET_KE_CAN_THIEP else ("observational" if tk in THIET_KE_QUAN_SAT else None)
        thuc = _loai_dang_ky(loai)
        ket_tk["nguon"].append({"cong": "G2", "noi": "đăng ký TRDS mục 15 (Study Type)", "gia_tri": loai})
        if mong and thuc and mong != thuc:
            ket_tk = _ket("thiet_ke", "Mã thiết kế", ket_tk["nguon"], MUC_LECH_CUNG,
                          f"thiết kế «{tk}» nhưng đăng ký khai «{loai}» (mong đợi {mong.title()}) — sửa bản đăng ký G2")
        elif mong and not thuc:
            ket_tk = _ket("thiet_ke", "Mã thiết kế", ket_tk["nguon"], _muc_cao_nhat([ket_tk["muc"], MUC_CAN_XEM]),
                          f"{ket_tk['ghi_chu']}; không đọc được loại nghiên cứu ở đăng ký («{loai}») — chủ nhiệm "
                          "đọc lại")
        elif tk in THIET_KE_DANG_KY_MO_HO and thuc == "interventional":
            ket_tk = _ket("thiet_ke", "Mã thiết kế", ket_tk["nguon"], _muc_cao_nhat([ket_tk["muc"], MUC_CAN_XEM]),
                          f"{ket_tk['ghi_chu']}; nghiên cứu chẩn đoán khai «Interventional» ở đăng ký — đúng "
                          "khi có can thiệp theo đề cương (vd test quyết định xử trí), chủ nhiệm xác nhận")
    ket.append(ket_tk)

    # 4) Kết cục chính.
    nguon_kc = [{"cong": "G0", "noi": "study_meta.gate_params.G0.primary_outcome",
                 "gia_tri": _ten_ket_cuc(_gp(meta, "G0").get("primary_outcome"))},
                {"cong": "G1", "noi": "study_meta.gate_params.G1.primary_outcome",
                 "gia_tri": _ten_ket_cuc(_gp(meta, "G1").get("primary_outcome"))},
                {"cong": "G2", "noi": "đăng ký TRDS mục 19 (Primary Outcome)", "gia_tri": _ten_ket_cuc(trds.get("19"))},
                {"cong": "G4", "noi": "SAP §2 «Kết cục chính»", "gia_tri": _ket_cuc_chinh_sap(sap_text)},
                {"cong": "G8", "noi": "study_meta.gate_params.G8.primary_outcome",
                 "gia_tri": _ten_ket_cuc(_gp(meta, "G8").get("primary_outcome"))}]
    nguon_kc = [n for n in nguon_kc if _co_that(n["gia_tri"])]
    if len(nguon_kc) < 2:
        ket.append(_ket("ket_cuc_chinh", "Kết cục chính", nguon_kc, MUC_CHUA_DU, "chỉ có ≤ 1 nơi ghi — chưa đủ để so"))
    else:
        goc = nguon_kc[0]
        lech = [n for n in nguon_kc[1:] if not cung_ket_cuc(goc["gia_tri"], n["gia_tri"])]
        dau = dau_van_tay_ket_cuc(nguon_kc)
        muc_sd, ghi_sd = kiem_sua_doi_ket_cuc(meta, out_dir, study, nguon_kc, dau)
        if muc_sd == MUC_CAN_XEM:
            # Sửa đổi THẬT có kiểm chứng (06/10/2026, G10-07) — hiện ra cả khi mọi nơi đã thống nhất về kết cục mới.
            ket.append(_ket("ket_cuc_chinh", "Kết cục chính", nguon_kc, MUC_CAN_XEM, ghi_sd))
        elif lech:
            ok, ly_do = _xac_nhan_ket_cuc(meta, dau)
            noi_lech = ", ".join(n["cong"] + " (" + n["noi"] + ")" for n in lech)
            if ok:
                ket.append(_ket("ket_cuc_chinh", "Kết cục chính", nguon_kc, MUC_CAN_XEM,
                                f"{noi_lech} diễn đạt khác «{goc['cong']}» — chủ nhiệm ĐÃ xác nhận là cùng một kết cục "
                                f"(dấu {dau}): «{ly_do[:120]}»"))
            else:
                ket.append(_ket("ket_cuc_chinh", "Kết cục chính", nguon_kc, MUC_LECH_MEM,
                                f"{noi_lech} khác «{goc['cong']}» — đổi kết cục chính phải có chủ nhiệm giải trình "
                                "công khai (outcome switching); thống nhất về MỘT kết cục; nếu chỉ khác cách diễn đạt "
                                f"thì ghi gate_params.G10.xac_nhan_ket_cuc_chinh với dau_van_tay={dau} ({ly_do}); nếu "
                                "ĐÃ ĐỔI kết cục thật (sửa đổi đề cương có lý do, Hội đồng đạo đức chấp thuận, đăng ký "
                                "cập nhật) thì khai gate_params.G10.sua_doi_ket_cuc_chinh với dau_van_tay="
                                f"{dau}" + (f" — {ghi_sd}" if ghi_sd else "")))
        else:
            ket.append(_ket("ket_cuc_chinh", "Kết cục chính", nguon_kc, MUC_KHOP if muc_sd is None else MUC_CAN_XEM,
                            f"{len(nguon_kc)} nơi cùng chỉ một kết cục" + (f" — {ghi_sd}" if ghi_sd else "")))

    # 5) Quần thể (chỉ báo — văn bản tiêu chí dài ngắn khác nhau tự nhiên).
    tc = _mo_repr(trds.get("14"))
    tc_txt = _van_ban(tc.get("inclusion")) if isinstance(tc, dict) else _van_ban(tc)
    nguon_qt = [n for n in (
        {"cong": "G0", "noi": "study_meta.gate_params.G0.population",
         "gia_tri": _van_ban(_gp(meta, "G0").get("population"))},
        # 15/11/2026: phía G1 gồm cả tiêu chí chọn vào — G1 hay chuyển ngưỡng («≥18 tuổi») từ câu quần thể sang danh
        # sách tiêu chí; so riêng câu quần thể sẽ báo nhầm «mất ngưỡng» (phép so hai chiều).
        {"cong": "G1", "noi": "study_meta.gate_params.G1.population + inclusion_criteria",
         "gia_tri": " ".join(x for x in (_van_ban(_gp(meta, "G1").get("population")),
                                         _van_ban(_gp(meta, "G1").get("inclusion_criteria"))) if x)},
        {"cong": "G2", "noi": "đăng ký TRDS mục 14 (tiêu chí chọn)", "gia_tri": tc_txt},
    ) if _co_that(n["gia_tri"])]
    if len(nguon_qt) < 2:
        ket.append(_ket("quan_the", "Quần thể nghiên cứu", nguon_qt, MUC_CHUA_DU, "chỉ có ≤ 1 nơi ghi — chưa đủ để so"))
    else:
        ket.append(_so_quan_the_hai_chieu(nguon_qt))

    # 6) Cỡ mẫu tính cho kết cục nào (chỉ báo).
    powered = _van_ban(_gp(meta, "G3").get("powered_for_outcome"))
    chinh = next((n["gia_tri"] for n in nguon_kc if n["cong"] == "G1"), nguon_kc[0]["gia_tri"] if nguon_kc else "")
    phu = _mo_repr(_gp(meta, "G1").get("secondary_outcomes")) or _mo_repr(trds.get("20")) or []
    phu = [_van_ban(x) for x in (phu if isinstance(phu, list) else [phu]) if _co_that(x)]
    if _co_that(powered) and chinh and phu:
        d_chinh = _bao_ham(chinh, powered)
        d_phu, ket_phu = max((_bao_ham(p, powered), p) for p in phu)
        nguon_pw = [{"cong": "G3", "noi": "study_meta.gate_params.G3.powered_for_outcome", "gia_tri": powered}]
        if d_phu >= 0.4 and d_phu > d_chinh + 0.15:
            ket.append(_ket("co_mau_cho_ket_cuc", "Cỡ mẫu được tính cho kết cục nào",
                            nguon_pw + [{"cong": "G1", "noi": "kết cục chính (G1)", "gia_tri": chinh},
                                        {"cong": "G1", "noi": "kết cục thứ cấp gần nhất (G1)", "gia_tri": ket_phu}],
                            MUC_CAN_XEM,
                            f"cỡ mẫu có vẻ tính cho một kết cục G1 xếp là THỨ CẤP (độ bao hàm {d_phu:.2f} so với kết "
                            f"cục chính {d_chinh:.2f}) — chủ nhiệm xác nhận estimand/mục tiêu mà N phục vụ và cách xếp "
                            "kết cục"))
        else:
            ket.append(_ket("co_mau_cho_ket_cuc", "Cỡ mẫu được tính cho kết cục nào", nguon_pw, MUC_KHOP,
                            "kết cục mà N phục vụ khớp kết cục chính hơn các kết cục thứ cấp"))

    # 7) Loại giả thuyết (ưu thế / không kém hơn / tương đương / mô tả theo độ chính xác) — THÊM 06/10/2026 (G0-06):
    # G0 chốt loại kiểm định, G3 tính N theo nó, SAP §12 ký nó (SAP chỉ in dòng này cho không-kém-hơn/tương đương). Lệch
    # (vd G0 «không kém hơn» mà G3 tính N ưu thế) là N và phép kiểm sai cho câu hỏi đã chốt ⇒ LỆCH CỨNG. G3 chỉ là
    # nguồn khi N THẬT SỰ tính theo giả thuyết (khung §12 «power»); tính theo độ chính xác ⇒ «mô tả»; định tính /
    # tổng quan / mô hình dự báo (N theo phương pháp riêng) ⇒ hypothesis_type chỉ là mặc định của bộ tính, KHÔNG đem so.
    try:
        import skill_standards as SK2  # noqa: PLC0415
        chuan_gt = SK2.chuan_hoa_hypothesis_type
    except Exception:  # noqa: BLE001
        def chuan_gt(x):  # type: ignore[no-redef]
            return str(x).strip().lower() if x else None
    try:
        import g4_quality_gate as G4Q2  # noqa: PLC0415
        loai12 = G4Q2.loai_muc_12(next(iter(ma_tk)) if len(ma_tk) == 1 else g3.get("design_code"), g3)
    except Exception:  # noqa: BLE001 — thiếu bộ đọc ⇒ không đem G3 ra so (vẫn so G0 ↔ SAP)
        loai12 = None
    g3_gt = {"chinh_xac": "descriptive_precision", "power": g3.get("hypothesis_type")}.get(loai12)
    # 25/10/2026: thông số KHÔNG ÁP DỤNG cho cách N được quyết định (g4_quality_gate.loai_muc_12) thì SAP §12 không in
    # dòng của nó, G3 chỉ lưu mặc định của bộ tính ⇒ «⚪ chưa đủ để so» vĩnh viễn (C1a cắt ngang theo độ chính xác:
    # kiem_chi_tiet ⚪ «Power» không bao giờ hết). Bỏ trục đó khi nó «chưa đủ để so» — cùng cách trục «sai số d» chỉ
    # có ở thiết kế độ chính xác. Hai nơi ghi mà LỆCH nhau thì vẫn báo (cố ý bi quan).
    khong_ap_dung = _KHONG_AP_DUNG_THEO_MUC_12.get(loai12, frozenset())
    ket = [k for k in ket if not (k["ma"] in khong_ap_dung and k["muc"] == MUC_CHUA_DU)]
    nguon_gt = [
        {"cong": "G0", "noi": "study_meta.gate_params.G0.test_type", "gia_tri": _gp(meta, "G0").get("test_type")},
        {"cong": "G3", "noi": "G3_checkpoint.hypothesis_type" + (" (N theo độ chính xác ⇒ mô tả)"
                                                                  if loai12 == "chinh_xac" else ""),
         "gia_tri": g3_gt},
        {"cong": "G4", "noi": "SAP §12 «Loại giả thuyết»", "gia_tri": sap12.get("hypothesis_type")},
    ]
    nguon_gt = [n for n in nguon_gt if isinstance(n["gia_tri"], str) and chuan_gt(n["gia_tri"])]
    if nguon_gt:
        ket.append(_so_bang_nhau("loai_gia_thuyet", "Loại giả thuyết", nguon_gt,
                                 lambda v: chuan_gt(v) if isinstance(v, str) else None))

    # 8) Sai số cho phép d của thiết kế tính theo độ chính xác — THÊM 06/10/2026 (G4 → G10): N do d quyết định; G3 tính
    # và SAP §12 ký phải cùng một d.
    if loai12 == "chinh_xac" or sap12.get("precision") is not None:
        nguon_d = [{"cong": "G3", "noi": "G3_checkpoint.precision", "gia_tri": g3.get("precision")},
                   {"cong": "G3", "noi": "study_meta.gate_params.G3.precision",
                    "gia_tri": _gp(meta, "G3").get("precision")},
                   {"cong": "G4", "noi": "SAP §12 «Sai số tuyệt đối cho phép (d)»", "gia_tri": sap12.get("precision")}]
        ket.append(_so_bang_nhau("sai_so_d", "Sai số cho phép d", [n for n in nguon_d if _co_that(n["gia_tri"])],
                                 _ty_le))

    ket += truc_chuoi(out_dir, study, meta, sap_text)  # 15/11/2026: chuỗi đầy đủ vấn đề → … → đề cương
    tong = {m: sum(1 for k in ket if k["muc"] == m) for m in _THU_TU_MUC}
    thiet_ke = next(iter(ma_tk)) if len(ma_tk) == 1 else None
    return {"study": study, "thiet_ke": thiet_ke, "thong_so": ket, "tong": tong,
            "muc_cao_nhat": _muc_cao_nhat(k["muc"] for k in ket)}


# ─────────────── CHUỖI ĐẦY ĐỦ (15/11/2026) ───────────────
# Bác sĩ 15/11/2026: «Phải đạt sự đồng bộ giữa các cổng, từ vấn đề nghiên cứu, câu hỏi, tổng quan, mục tiêu, thiết kế,
# cỡ mẫu, chọn mẫu, biến, công cụ nghiên cứu và đề cương» — «đã có kiểm tra chéo, điều phối nhưng đã không thực hiện
# được và được báo cáo hoàn thiện». 8 trục cũ không đo biến ↔ công cụ ↔ đề cương, mục tiêu ↔ SAP, chọn mẫu chùm ↔ cỡ
# mẫu; hội đồng chấm RQ4 trên tập PMID vì không có báo cáo nào khác để chấm. Các trục dưới đây lấp đúng chỗ đó.
# Nguyên tắc mức: lệch làm SAI NHẬP LIỆU hoặc làm thiết kế không chạy được ⇒ LỆCH CỨNG; cần chủ nhiệm quyết ⇒ LỆCH MỀM;
# truy nguyên/văn phong ⇒ CẦN XEM; thiếu nguồn để so ⇒ CHƯA ĐỦ ĐỂ SO (không bao giờ là «khớp»).
TRUC_CHUOI = ("bien_de_cuong", "cong_cu_tu_dien", "muc_tieu_phan_tich", "chon_mau_co_mau", "dac_ta_cho_bo_bien",
              "tong_quan_khoang_trong", "co_mau_tinh_lai", "ky_thuat_chon_mau", "tai_lieu_nop_co_mau", "ten_de_tai",
              "cau_hoi_gia_thuyet", "trich_dan_tong_quan", "ma_tran_muc_tieu")
# Trục nào là trách nhiệm của cổng nào (hoi_dong_cong.trach_nhiem dùng — «hoàn thiện» của cổng phải qua trục của nó).
TRUC_THEO_CONG = {
    "co_mau": ("G3", "G4", "G10"), "alpha": ("G3", "G4", "G10"), "power": ("G3", "G4", "G10"),
    "sai_so_d": ("G3", "G4", "G10"), "loai_gia_thuyet": ("G0", "G3", "G4", "G10"),
    "thiet_ke": ("G1", "G2", "G3", "G4", "G10"),
    "ket_cuc_chinh": ("G0", "G1", "G4", "G8", "G10"), "quan_the": ("G0", "G1", "G2", "G10"),
    "co_mau_cho_ket_cuc": ("G3", "G4", "G10"),
    "bien_de_cuong": ("G3", "G5", "G10"), "cong_cu_tu_dien": ("G3", "G5", "G10"),
    "muc_tieu_phan_tich": ("G1", "G4", "G10"), "chon_mau_co_mau": ("G1", "G3", "G4", "G10"),
    "dac_ta_cho_bo_bien": ("G4", "G6"), "tong_quan_khoang_trong": ("G0", "G1", "G10"),
    "co_mau_tinh_lai": ("G3", "G4", "G10"), "ky_thuat_chon_mau": ("G1", "G3", "G4", "G10"),
    "tai_lieu_nop_co_mau": ("G10",), "ten_de_tai": ("G0", "G2", "G10"), "cau_hoi_gia_thuyet": ("G0", "G1", "G10"),
    "trich_dan_tong_quan": ("G0", "G1", "G10"),
    "ma_tran_muc_tieu": ("G1", "G3", "G4", "G10"),
}


def _tu_dien(out_dir: Path, study: str) -> Dict[str, Dict[str, str]]:
    import csv  # noqa: PLC0415

    for p in (out_dir / f"G5_REDCap_dictionary_{study}.csv", out_dir / "_bo-bien-rieng.csv"):
        if p.is_file():
            try:
                with open(p, encoding="utf-8-sig", newline="") as f:
                    return {(r.get("Variable / Field Name") or "").strip(): r for r in csv.DictReader(f)
                            if (r.get("Variable / Field Name") or "").strip()}
            except (OSError, ValueError):
                return {}
    return {}


def _ma_lua_chon(r: Dict[str, str]) -> List[int]:
    if (r.get("Field Type") or "").strip() in ("yesno", "truefalse"):
        return [0, 1]
    lua_chon = r.get("Choices, Calculations, OR Slider Labels") or ""
    return sorted(int(x) for x in re.findall(r"(?:^|\|)\s*(-?\d+)\s*,", lua_chon))


def _truc_bien_de_cuong(out_dir: Path, study: str) -> Dict[str, Any]:
    ten = "Biến ↔ đề cương/bộ biến đã duyệt"
    try:
        import doi_chieu_bien_de_cuong as DCB  # noqa: PLC0415

        kq = DCB.doi_chieu(out_dir, study)
    except Exception as e:  # noqa: BLE001 — thiếu bộ đối chiếu / hỏng ⇒ chưa đủ để so, không phải khớp
        return _ket("bien_de_cuong", ten, [], MUC_CHUA_DU, f"không đối chiếu được ({type(e).__name__})")
    if kq.khong_do_duoc:
        return _ket("bien_de_cuong", ten, [], MUC_CHUA_DU, kq.khong_do_duoc)
    nguon = [{"cong": "G5" if p.pham_vi == DCB.PV_NHAP else "G6", "noi": f"{p.luat} {p.bien}", "gia_tri": p.chi_tiet}
             for p in kq.phat_hien if p.muc == DCB.LECH][:12]
    nhap, pt = kq.lech(DCB.PV_NHAP), kq.lech(DCB.PV_PHAN_TICH)
    if nhap:
        return _ket("bien_de_cuong", ten, nguon, MUC_LECH_CUNG,
                    f"{len(nhap)} lệch NHẬP LIỆU (thiếu biến/sai mã/G3 ≠ G5) — mẫu nhập sẽ sai; sửa theo "
                    f"{', '.join(kq.nguon_nguoi_duyet)}")  # fmt: skip
    if pt:
        return _ket("bien_de_cuong", ten, nguon, MUC_LECH_MEM,
                    f"{len(pt)} lệch PHÂN TÍCH (biến phái sinh ngoài đề cương / calc chưa có công thức / đặc tả dùng "
                    "biến lạ) — chủ nhiệm quyết bổ sung đề cương/bộ biến; G6 tự chặn")  # fmt: skip
    return _ket("bien_de_cuong", ten, [], MUC_KHOP,
                f"{kq.so_bien_nguon} biến của {', '.join(kq.nguon_nguoi_duyet)} khớp bản máy")


def _truc_cong_cu(out_dir: Path, study: str, td: Dict[str, Dict[str, str]]) -> Dict[str, Any]:
    ten = "Công cụ thu thập ↔ từ điển nhập liệu"
    if not td:
        return _ket("cong_cu_tu_dien", ten, [], MUC_CHUA_DU, "chưa có từ điển máy")
    phieu = out_dir / f"PHIEU_THU_THAP_SO_LIEU_{study}.md"
    if phieu.is_file():
        tp = _doc_text(phieu)
        vang = [k for k in td if k != "record_id"
                and not re.search(rf"(?<![A-Za-z0-9_]){re.escape(k)}(?![A-Za-z0-9_])", tp)]
        if vang:
            return _ket("cong_cu_tu_dien", ten, [{"cong": "G3", "noi": phieu.name, "gia_tri": ", ".join(vang[:15])}],
                        MUC_LECH_CUNG, f"{len(vang)} trường của từ điển không có trên phiếu thu thập")
        return _ket("cong_cu_tu_dien", ten, [], MUC_KHOP, f"{len(td)} trường đều có trên {phieu.name}")
    dc = _doc_text(out_dir / f"DE_CUONG_NOP_HOI_DONG_{study}.md")
    a, b = dc.find("# PHỤ LỤC C"), dc.find("# PHỤ LỤC D")
    e = dc.find("# PHỤ LỤC E")
    if a < 0 or e < 0:
        return _ket("cong_cu_tu_dien", ten, [], MUC_CHUA_DU,
                    "không có phiếu thu thập (PHIEU_THU_THAP_SO_LIEU_<mã>.md) lẫn phiếu trong đề cương nộp "
                    "(Phụ lục C + bảng biến số Phụ lục E)")  # fmt: skip
    pc = dc[a:b if b > a else None]
    p1 = pc[:pc.find("PHẦN 2")] if "PHẦN 2" in pc else pc
    cau = {int(m[1]): m[2] for m in re.finditer(r"(?m)^(\d{1,2})\. (.+)$", p1)}
    thap = {k.lower(): k for k in td}
    lech, so = [], 0
    for dong in dc[e:].splitlines():
        m = re.search(r"Phiếu – câu (\d+)", dong)
        if not m:
            continue
        o = [x.strip() for x in dong.strip().strip("|").split("|")]
        k = thap.get(o[0].strip("`").lower())
        q = cau.get(int(m[1]))
        if k is None or q is None:
            ly_do = "không có trong từ điển" if k is None else "không thấy câu trên phiếu"
            lech.append(f"câu {m[1]} ({o[0]}): {ly_do}")
            continue
        if (td[k].get("Field Type") or "").strip() not in ("radio", "dropdown", "checkbox", "yesno", "truefalse"):
            continue
        so += 1
        co_so = [int(x) for x in re.findall(r"☐\s*(\d+)\b", q)]
        khong_so = q.count("☐") - len(co_so)
        ma = _ma_lua_chon(td[k])
        if set(co_so) - set(ma) or len([x for x in ma if x not in co_so]) != khong_so:
            lech.append(f"câu {m[1]} ({k}): phiếu {co_so}+{khong_so} ô không số ≠ từ điển {ma}")
    p2 = pc[pc.find("PHẦN 2"):pc.find("PHẦN 3")] if "PHẦN 2" in pc and "PHẦN 3" in pc else ""
    hdr = next((d for d in p2.splitlines() if d.startswith("|") and "KSD" in d), "")
    if hdr:
        cot = [x.strip() for x in hdr.strip().strip("|").split("|")].index("KSD")
        ksd = set()
        for dong in p2.splitlines():
            mm = re.match(r"\|\s*([A-F]\d{1,2})\b", dong)
            if mm:
                o = [x.strip() for x in dong.strip().strip("|").split("|")]
                if len(o) > cot and o[cot] not in ("", "—", "-"):
                    ksd.add(mm[1].lower())
        co7 = {k.lower() for k in td if re.fullmatch(r"[a-fA-F]\d{1,2}", k) and 7 in _ma_lua_chon(td[k])}
        if ksd != co7:
            lech.append(f"ô KSD trên phiếu {sorted(ksd)} ≠ mục có mã 7 trong từ điển {sorted(co7)}")
    if lech:
        return _ket("cong_cu_tu_dien", ten, [{"cong": "G5", "noi": "phiếu ↔ từ điển", "gia_tri": x} for x in lech[:12]],
                    MUC_LECH_CUNG, f"{len(lech)} chỗ phiếu (Phụ lục C) khác từ điển nhập liệu")
    if not so:
        return _ket("cong_cu_tu_dien", ten, [], MUC_CHUA_DU, "không đọc được câu nào của phiếu theo bảng biến số")
    return _ket("cong_cu_tu_dien", ten, [], MUC_KHOP, f"{so} câu chọn đáp án của phiếu khớp mã từ điển (kể cả ô KSD)")


def _truc_muc_tieu(meta: Dict[str, Any], sap_text: str) -> Optional[Dict[str, Any]]:
    ob = _gp(meta, "G1").get("objectives") or []
    if not ob or not sap_text:
        return None
    ten = "Mục tiêu (G1) ↔ phân tích (SAP)"
    thieu = []
    for o in ob:
        m = re.match(r"\s*(MT\s*\d+)", str(o))
        if not m:
            continue
        so = re.sub(r"\D", "", m[1])
        if not re.search(rf"(MT\s*{so}\b|Mục tiêu\s*{so}\b)", sap_text):
            thieu.append(str(o)[:90])
    if thieu:
        return _ket("muc_tieu_phan_tich", ten, [{"cong": "G1", "noi": "objectives", "gia_tri": x} for x in thieu],
                    MUC_CAN_XEM, f"{len(thieu)}/{len(ob)} mục tiêu không được SAP gọi tên — ghi rõ phân tích nào "
                    "trả lời mục tiêu nào (truy nguyên mục tiêu → phân tích)")  # fmt: skip
    return _ket("muc_tieu_phan_tich", ten, [], MUC_KHOP, f"{len(ob)}/{len(ob)} mục tiêu có trong SAP")


def _truc_chon_mau(meta: Dict[str, Any], sap_text: str, td: Dict[str, Dict[str, str]]) -> Optional[Dict[str, Any]]:
    tk = _gp(meta, "G1").get("sampling_design") or []
    tk = tk if isinstance(tk, list) else [tk]
    co_chum = "cum" in tk or bool(re.search(r"chọn mẫu (theo )?(chùm|cụm)", sap_text or "", re.I))
    if not co_chum:
        return None
    ten = "Chọn mẫu chùm ↔ cỡ mẫu ↔ biến chùm"
    g3 = _gp(meta, "G3")
    m, icc, k = _so_dau(g3.get("cluster_size")), _so_dau(g3.get("icc")), _so_dau(g3.get("n_clusters"))
    if m is None or icc is None:
        return _ket("chon_mau_co_mau", ten, [{"cong": "G1", "noi": "sampling_design", "gia_tri": tk}], MUC_LECH_CUNG,
                    "chọn mẫu theo chùm nhưng G3 không có cỡ chùm/ICC — cỡ mẫu chưa hiệu chỉnh hiệu ứng thiết kế")
    cv = _so_dau(g3.get("cluster_size_cv")) or 0.0
    de = 1 + ((cv ** 2 + 1) * m - 1) * icc
    gia_tri = f"m={m:g} CV={cv:g} ICC={icc:g} ⇒ DE={de:.2f}"
    lech, nguon = [], [{"cong": "G3", "noi": "cluster_size·cv·icc", "gia_tri": gia_tri}]
    sap_de = [float(x.replace(",", ".")) for x in re.findall(r"\bDE\s*[:=]?\s*(1[.,]\d+)", sap_text or "")]
    # 15/11/2026: MỌI giá trị DE trong SAP phải là DE chính (CV G3), DE độ nhạy CV = 1,0 hoặc DE cỡ chùm đều (CV = 0);
    # luật cũ «chỉ cần MỘT giá trị khớp» để lọt SAP vừa ghi DE đúng vừa ghi DE cũ ở chỗ khác.
    hop_le = _de_hop_le(m, icc, cv)
    la = sorted({round(x, 2) for x in sap_de if not any(abs(x - a) < 0.015 for a in hop_le)})
    if la:
        lech.append(f"SAP nêu DE {la} không thuộc DE hợp lệ từ G3 {sorted(round(a, 2) for a in hop_le)}")
    n = _so_nguyen(_gp(meta, "G3").get("confirmed_n"))
    if k and n and abs(k * m - n) > 0.5:
        nguon.append({"cong": "G3", "noi": "K×m vs N", "gia_tri": f"{k:g}×{m:g} ≠ {n}"})
        lech.append(f"số chùm × cỡ chùm {k:g}×{m:g} = {k * m:g} ≠ N đã chốt {n} (DE tính với m sai)")
    # định danh đứng sau «chùm» trong SAP: có thể là biến chùm (`ma_ban_kham`) hoặc tên hàm R (`vcovCL`) ⇒ chỉ cần MỘT
    # định danh có trong từ điển; không tên nào có ⇒ biến chùm không nhập được.
    ung_vien = sorted(set(re.findall(r"chùm\s*\(?\s*`([A-Za-z_][A-Za-z0-9_:]*)`", sap_text or "")))
    thap = {x.lower() for x in td}
    bien = [b for b in ung_vien if b.lower() in thap]
    if td and not bien:
        return _ket("chon_mau_co_mau", ten, nguon + [{"cong": "G5", "noi": "định danh sau «chùm» trong SAP",
                                                         "gia_tri": ", ".join(ung_vien) or "(không có)"}],
                    MUC_LECH_CUNG, "SAP không nêu biến chùm nào có trong từ điển — không nhập được thì không "
                    "hiệu chỉnh chùm")  # fmt: skip
    if lech:
        return _ket("chon_mau_co_mau", ten, nguon, MUC_LECH_MEM, "; ".join(lech))
    return _ket("chon_mau_co_mau", ten, nguon, MUC_KHOP, f"DE {de:.2f} khớp SAP; biến chùm {bien} có trong từ điển")


def _truc_dac_ta(out_dir: Path) -> Optional[Dict[str, Any]]:
    dt = _doc_json(out_dir / "G6_DAC_TA_SAP.json")
    cho = [p.get("id") for p in dt.get("phan_tich") or []
           if "BỔ SUNG BỘ BIẾN" in str(p.get("chua_tu_dong") or "").upper()]
    if not cho:
        return None
    return _ket("dac_ta_cho_bo_bien", "Phân tích SAP chờ bổ sung bộ biến", [{"cong": "G4", "noi": "G6_DAC_TA_SAP.json",
                "gia_tri": ", ".join(map(str, cho))}], MUC_LECH_MEM,
                f"{len(cho)} phân tích SAP cần biến mà bộ biến G3 chưa có — chủ nhiệm duyệt bổ sung "
                "bộ biến")  # fmt: skip


def _truc_tong_quan(out_dir: Path, study: str, meta: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    # Không dùng `_co_that`: câu khoảng trống hay mở bằng «Chưa có nghiên cứu …» — đúng mẫu ô trống của `_O_TRONG`.
    kg_raw = _gp(meta, "G1").get("knowledge_gap")
    kg_raw = " ".join(map(str, kg_raw)) if isinstance(kg_raw, list) else str(kg_raw or "")
    kg = (bool(re.search(r"\w{3}", kg_raw)) and "[CẦN" not in kg_raw.upper()) or (
        out_dir / f"G0_KHOANG_TRONG_{study}.json").is_file()
    dc = _doc_text(out_dir / f"DE_CUONG_NOP_HOI_DONG_{study}.md")
    ten = "Tổng quan/khoảng trống ↔ đề cương"
    if not dc:
        return _ket("tong_quan_khoang_trong", ten, [], MUC_CHUA_DU, "chưa có đề cương nộp để so")
    co = bool(re.search(r"(?im)^#+\s.*khoảng trống", dc))
    if kg and not co:
        return _ket("tong_quan_khoang_trong", ten, [], MUC_CAN_XEM,
                    "G0/G1 có khoảng trống nghiên cứu nhưng đề cương nộp không có mục «khoảng trống»")
    return _ket("tong_quan_khoang_trong", ten, [], MUC_KHOP if co else MUC_CHUA_DU,
                "đề cương có mục khoảng trống (chỉ kiểm có mặt — nội dung do hội đồng chấm RQ3/RQ4)" if co
                else "không có khoảng trống ở G0/G1 lẫn đề cương")


def _de_hop_le(m: float, icc: float, cv: float) -> List[float]:
    """DE chính (CV khai ở G3) + DE độ nhạy CV = 1,0 + DE cỡ chùm đều (CV = 0).

    Eldridge 2006, doi:10.1093/ije/dyl129."""
    return sorted({1 + ((c * c + 1) * m - 1) * icc for c in (cv, 1.0, 0.0)})


def _mau_so(n: int) -> str:
    """Mẫu nhận một số nguyên trong văn bản Việt: 1000 ⇒ «1000», «1.000», «1 000», «1,000»."""
    s = str(n)
    if n < 1000:
        return rf"(?<![\d.,]){s}(?![\d]|[.,]\d)"
    nghin = s[:-3] + r"[.,  ]?" + s[-3:]
    return rf"(?<![\d.,]){nghin}(?![\d]|[.,]\d)"


def _truc_tinh_lai_co_mau(out_dir: Path, study: str, meta: Dict[str, Any], sap_text: str) -> Optional[Dict[str, Any]]:
    """15/11/2026 (bác sĩ: «kiểm tra và đánh giá sự đồng bộ Tính Cỡ Mẫu … trung thực nhất» + «mỗi vấn đề … phải được cập
    nhật vào hệ thống»): TÍNH LẠI cỡ mẫu của nghiên cứu MÔ TẢ theo độ chính xác từ CHÍNH tham số G3 — n₀ = z²p(1−p)/d²,
    DE = 1 + ((CV²+1)·m − 1)·ICC khi có gom cụm, N cần = ⌈n₀·DE⌉ ÷ (1 − tỷ lệ không đáp ứng) — rồi so với checkpoint G3,
    «N tối thiểu» của SAP và đề cương nộp, và N đã chốt. Lệch số học ở G3 hoặc N chốt < N cần ⇒ LỆCH CỨNG; văn bản ghi N
    tối thiểu khác ⇒ LỆCH MỀM. Thiết kế khác (so sánh, chẩn đoán…) ⇒ None — công thức riêng do run_g3_auto/G3 chấm."""
    from math import ceil  # noqa: PLC0415
    from statistics import NormalDist  # noqa: PLC0415

    g3, cp = _gp(meta, "G3"), _doc_json(out_dir / "G3_checkpoint.json")
    lay = lambda *k: next((v for v in (g3.get(x, cp.get(x)) for x in k) if v not in (None, "")), None)  # noqa: E731
    if str(lay("hypothesis_type") or "") != "descriptive_precision":
        return None
    p, d = _so_dau(lay("prevalence")), _so_dau(lay("precision"))
    if p is None or d is None or p <= 0 or d <= 0:
        return None
    p, d = (p / 100 if p > 1 else p), (d / 100 if d >= 1 else d)
    alpha = _ty_le(lay("alpha")) or 0.05
    z = NormalDist().inv_cdf(1 - alpha / 2)
    n0 = ceil(z * z * p * (1 - p) / (d * d) - 1e-9)
    icc, m = _so_dau(lay("icc")), _so_dau(lay("cluster_size"))
    cv = _so_dau(lay("cluster_size_cv", "cluster_cv")) or 0.0
    de = 1 + ((cv * cv + 1) * m - 1) * icc if icc and m else 1.0
    n_de = ceil(n0 * de - 1e-9)
    drop = _so_dau(lay("dropout")) or 0.0
    drop = drop / 100 if drop >= 1 else drop
    n_can = ceil(n_de / (1 - drop) - 1e-9)
    ten = "Cỡ mẫu tính lại từ tham số G3 (mô tả theo độ chính xác)"
    tinh = f"n₀={n0} · DE={de:.3f} · ⌈n₀·DE⌉={n_de} · ÷(1−{drop:g}) ⇒ N cần {n_can}"
    nguon = [{"cong": "G3", "noi": "tính lại", "gia_tri": tinh}]
    cung, mem = [], []
    for khoa, dung, sai_so in (("n_total_truoc_de", n0, 1), ("n_total", n_de, 1), ("n_adjusted", n_can, 1)):
        v = _so_nguyen(cp.get(khoa))
        if v is not None and abs(v - dung) > sai_so:
            cung.append(f"G3_checkpoint.{khoa} = {v} ≠ tính lại {dung}")
    v = _so_dau(cp.get("design_effect"))
    if v is not None and icc and m and abs(v - de) > 0.005:
        cung.append(f"G3_checkpoint.design_effect = {v:g} ≠ tính lại {de:.4f}")
    n_chot = _so_nguyen(lay("confirmed_n"))
    if n_chot is not None and n_chot < n_can:
        (mem if _co_that(g3.get("underpowered_acceptance_justification")) else cung).append(
            f"N đã chốt {n_chot} < N cần {n_can}")
    # «N tối thiểu» trong SAP / đề cương nộp: ít nhất MỘT lần nhắc phải chứa N cần (lần khác có thể là kịch bản
    # độ nhạy).
    for ten_vb, vb in (("SAP", sap_text), ("đề cương nộp", _doc_text(out_dir / f"DE_CUONG_NOP_HOI_DONG_{study}.md"))):
        doan = [vb[x.end():x.end() + 90] for x in re.finditer(r"(?:\bN|cỡ\s+mẫu)\s+tối\s+thiểu", vb or "", re.I)]
        if doan and not any(re.search(_mau_so(n_can), t) for t in doan):
            mem.append(f"{ten_vb} ghi «N/cỡ mẫu tối thiểu» nhưng không lần nào là {n_can}")
            nguon.append({"cong": "G4" if ten_vb == "SAP" else "G10", "noi": ten_vb, "gia_tri": doan[0].strip()[:80]})
    if cung:
        return _ket("co_mau_tinh_lai", ten, nguon, MUC_LECH_CUNG, "; ".join(cung + mem))
    if mem:
        return _ket("co_mau_tinh_lai", ten, nguon, MUC_LECH_MEM, "; ".join(mem))
    return _ket("co_mau_tinh_lai", ten, nguon, MUC_KHOP,
                f"{tinh}; khớp checkpoint G3" + (f", N chốt {n_chot} ≥ N cần" if n_chot else ""))


# mã G1.sampling_design (g1_design_blocks._O_DANH_DAU) ⇒ dấu hiệu trong văn bản
_KY_THUAT = {"toan_bo": r"toàn\s+bộ", "ngau_nhien_don": r"ngẫu\s+nhiên\s+đơn",
             "he_thong": r"(?:chọn\s+mẫu|mẫu)\s+hệ\s+thống|systematic", "phan_tang": r"phân\s+tầng|stratif",
             "cum": r"chùm|cụm|cluster"}
_CUM_CHON_MAU = re.compile(r"chọn\s+mẫu\s+(ngẫu\s+nhiên\s+đơn|hệ\s+thống|phân\s+tầng|(?:theo\s+)?(?:chùm|cụm)|"
                           r"thuận\s+tiện|chủ\s+đích|toàn\s+bộ)", re.I)
_PHU_DINH = re.compile(r"(không|thay\s+vì|tránh|chứ\s+không|thay\s+cho|loại\s+bỏ)[^.;\n]{0,25}$", re.I)
_PHI_XAC_SUAT = ("thuan_tien", "chu_dich")
# câu THUẬT LẠI tài liệu khác (C1a §4.4.3: «Thuyết minh đề tài đã nộp Bệnh viện ghi phương pháp chọn mẫu là chọn mẫu
# thuận tiện…») — không phải phương pháp của văn bản này, nhưng là chênh lệch giữa hai tài liệu nộp ⇒ CẦN XEM,
# không LỆCH.
_THUAT_LAI = re.compile(r"thuyết\s+minh|bản\s+(?:cũ|trước)|phiên\s+bản\s+trước|đề\s+cương\s+(?:cũ|trước)", re.I)
# 15/11/2026: đoạn thuật lại mà CHÍNH NÓ giải trình chênh lệch (đề cương C1a §4.4.3: «… cụ thể hóa phương pháp đó … theo
# hướng chặt chẽ hơn …») là đã giải trình — không báo «cần xem» mãi. Thuật lại KHÔNG kèm câu giải trình vẫn «cần xem».
_GIAI_TRINH_DOI = re.compile(r"cụ\s+thể\s+h(?:óa|oá|oa)|thay\s+(?:bằng|thế)|điều\s+chỉnh\s+thành", re.I)
_GIAI_TRINH_LY_DO = re.compile(r"chặt\s+chẽ\s+hơn|lý\s+do|\bvì\b|bởi\s+vì|nhằm|để\s+(?:tránh|bảo\s+đảm|phủ|giảm)", re.I)


def _da_giai_trinh(doan: str) -> bool:
    """Đoạn thuật lại có câu giải trình: «giải trình», hoặc CẢ động từ thay đổi lẫn lý do (một câu cụt «Đề cương cụ thể
    hoá.» không đủ)."""
    return bool(re.search(r"giải\s+trình", doan, re.I)
                or (_GIAI_TRINH_DOI.search(doan) and _GIAI_TRINH_LY_DO.search(doan)))


def _ma_cum(t: str) -> str:
    t = unicodedata.normalize("NFC", t.lower())
    for ma, mau in (("ngau_nhien_don", "ngẫu nhiên đơn"), ("he_thong", "hệ thống"), ("phan_tang", "phân tầng"),
                    ("thuan_tien", "thuận tiện"), ("chu_dich", "chủ đích"), ("toan_bo", "toàn bộ")):
        if re.search(mau.replace(" ", r"\s+"), t):
            return ma
    return "cum"


def _truc_ky_thuat_chon_mau(out_dir: Path, study: str, meta: Dict[str, Any], sap_text: str) -> Optional[Dict[str, Any]]:
    """15/11/2026: kỹ thuật chọn mẫu G1 ↔ chiến lược tuyển chọn ↔ đề cương nộp ↔ SAP (mọi thiết kế, không chỉ chùm).
    Mỗi mã G1 phải hiện ở đề cương nộp; mã quyết định CÁCH CHỌN (toàn bộ/ngẫu nhiên đơn/hệ thống/phân tầng) phải hiện ở
    G1.recruitment_strategy; mã làm ĐỔI PHƯƠNG SAI (phân tầng, chùm) phải được SAP nhắc tới (trọng số/sai số chuẩn) —
    thiếu ⇒ CẦN XEM. Văn bản tả «chọn mẫu <cách khác mã G1>» ⇒ LỆCH MỀM; cách phi xác suất (thuận tiện, chủ đích) trong
    khi G1 chốt cách xác suất ⇒ LỆCH CỨNG (cỡ mẫu theo độ chính xác giả định mẫu xác suất). Câu phủ định («không…»,
    «thay vì …») không tính; câu thuật lại tài liệu khác (thuyết minh, bản cũ) ⇒ CẦN XEM."""
    g1 = _gp(meta, "G1")
    tk = g1.get("sampling_design") or []
    tk = [str(x) for x in (tk if isinstance(tk, list) else [tk]) if _co_that(x)]
    ma = [x for x in tk if not x.startswith("khac")]
    rs = unicodedata.normalize("NFC", str(g1.get("recruitment_strategy") or ""))
    dc = unicodedata.normalize("NFC", _doc_text(out_dir / f"DE_CUONG_NOP_HOI_DONG_{study}.md"))
    sap = unicodedata.normalize("NFC", sap_text or "")
    if not ma and not rs and not dc:
        return None
    ten = "Kỹ thuật chọn mẫu G1 ↔ tuyển chọn ↔ đề cương ↔ SAP"
    if not ma:
        return _ket("ky_thuat_chon_mau", ten, [], MUC_CHUA_DU, "G1 chưa khai sampling_design — không có chuẩn để so")
    can, cung, mem = [], [], []
    da_giai_trinh: List[str] = []
    for ten_vb, vb, can_ma in (("chiến lược tuyển chọn G1", rs, [x for x in ma if x in ("toan_bo", "ngau_nhien_don",
                                                                                     "he_thong", "phan_tang")]),
                               ("đề cương nộp", dc, ma), ("SAP", sap, [x for x in ma if x in ("phan_tang", "cum")])):
        if not vb:
            continue
        thieu = [x for x in can_ma if x in _KY_THUAT and not re.search(_KY_THUAT[x], vb, re.I)]
        if thieu:
            can.append(f"{ten_vb} không nhắc {', '.join(thieu)}")
        for mm in _CUM_CHON_MAU.finditer(vb):
            if _PHU_DINH.search(vb[max(0, mm.start() - 40):mm.start()]):
                continue
            k = _ma_cum(mm.group(1))
            if k in ma:
                continue
            dau_cau = max(vb.rfind(". ", 0, mm.start()), vb.rfind("\n", 0, mm.start())) + 1
            if _THUAT_LAI.search(vb[dau_cau:mm.start()]):
                dau_doan = vb.rfind("\n\n", 0, mm.start()) + 1
                cuoi_doan = vb.find("\n\n", mm.end())
                if _da_giai_trinh(vb[dau_doan:cuoi_doan if cuoi_doan >= 0 else len(vb)]):
                    da_giai_trinh.append(ten_vb)
                    continue
                can.append(f"{ten_vb} thuật lại tài liệu khác dùng «{mm.group(0)}» (khác mã G1 {', '.join(ma)}) — "
                           "đối chiếu và giải trình chênh lệch giữa hai tài liệu")
                continue
            if k in _PHI_XAC_SUAT:
                cung.append(f"{ten_vb} tả «{mm.group(0)}» (phi xác suất) trong khi G1 chốt {', '.join(ma)}")
            else:
                mem.append(f"{ten_vb} tả «{mm.group(0)}» — không thuộc mã G1 {', '.join(ma)}")
    nguon = [{"cong": "G1", "noi": "sampling_design", "gia_tri": ", ".join(tk)}]
    if cung:
        return _ket("ky_thuat_chon_mau", ten, nguon, MUC_LECH_CUNG, "; ".join(dict.fromkeys(cung + mem)))
    if mem:
        return _ket("ky_thuat_chon_mau", ten, nguon, MUC_LECH_MEM, "; ".join(dict.fromkeys(mem)))
    if can:
        return _ket("ky_thuat_chon_mau", ten, nguon, MUC_CAN_XEM, "; ".join(can))
    return _ket("ky_thuat_chon_mau", ten, nguon, MUC_KHOP,
                f"{', '.join(ma)} hiện đúng ở " + ", ".join(t for t, v in (("tuyển chọn G1", rs), ("đề cương nộp", dc),
                                                                         ("SAP", sap)) if v)
                + (f"; {', '.join(dict.fromkeys(da_giai_trinh))} thuật lại tài liệu khác và ĐÃ giải trình chênh lệch"
                   if da_giai_trinh else ""))


TAI_LIEU_NOP_TIEN_TO = ("DE_CUONG_NOP_HOI_DONG_", "DE_CUONG_THONG_NHAT_", "De-cuong_", "Bai-bao-giao-thuc_")
_BAN_CU = re.compile(r"BẢN\s+CŨ\s*[—–-]+\s*ĐÃ\s+THAY", re.I)


def _truc_tai_lieu_nop(out_dir: Path, study: str, meta: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """15/11/2026: mọi TÀI LIỆU NỘP có bàn về cỡ mẫu phải ghi đúng N đã chốt và — khi có gom cụm — DE hiện hành của G3.
    Bản cũ đã thay (C1a: De-cuong_ 04/10, Bai-bao-giao-thuc_ 03/08 giả định 8–20 bàn khám, DE thiếu CV) chỉ được bỏ qua
    khi đầu tệp có dấu «BẢN CŨ — ĐÃ THAY BẰNG <tệp>»; không dấu mà số lệch ⇒ LỆCH MỀM (người đọc/Hội đồng có thể cầm
    nhầm)."""
    g3 = _gp(meta, "G3")
    cp = _doc_json(out_dir / "G3_checkpoint.json")
    n = _so_nguyen(g3.get("confirmed_n")) or _so_nguyen(cp.get("confirmed_n")) or _so_nguyen(cp.get("n_adjusted"))
    icc, m = _so_dau(g3.get("icc")), _so_dau(g3.get("cluster_size"))
    cv = _so_dau(g3.get("cluster_size_cv")) or 0.0
    de = 1 + ((cv * cv + 1) * m - 1) * icc if icc and m else None
    tep = sorted({p for t in TAI_LIEU_NOP_TIEN_TO for p in out_dir.glob(f"{t}*.md")})
    if not tep or n is None:
        return None
    ten = "Tài liệu nộp ↔ cỡ mẫu và hiệu ứng thiết kế hiện hành"
    lech, cu, xet = [], [], 0
    for p in tep:
        vb = unicodedata.normalize("NFC", _doc_text(p))
        if _BAN_CU.search("\n".join(vb.splitlines()[:40])):
            cu.append(p.name)
            continue
        if not re.search(r"cỡ\s+mẫu", vb, re.I):
            continue
        xet += 1
        if not re.search(_mau_so(n), vb):
            lech.append(f"{p.name}: không ghi N đã chốt {n}")
        if de is not None and re.search(r"hiệu\s+ứng\s+thiết\s+kế|\bICC\b", vb, re.I):
            dd = f"{de:.2f}"
            if not re.search(dd.replace(".", "[.,]"), vb):
                lech.append(f"{p.name}: bàn về gom cụm nhưng không ghi DE hiện hành {dd.replace('.', ',')}")
    ghi_cu = f"; bỏ qua bản cũ đã đánh dấu: {', '.join(cu)}" if cu else ""
    nguon = [{"cong": "G10", "noi": "tài liệu nộp", "gia_tri": x} for x in lech[:8]]
    if lech:
        return _ket("tai_lieu_nop_co_mau", ten, nguon, MUC_LECH_MEM,
                    "; ".join(lech) + " — cập nhật theo đề cương nộp, hoặc đánh dấu đầu tệp «BẢN CŨ — ĐÃ THAY BẰNG …»"
                    + ghi_cu)
    if not xet:
        return _ket("tai_lieu_nop_co_mau", ten, [], MUC_CHUA_DU, "không tài liệu nộp nào bàn về cỡ mẫu" + ghi_cu)
    return _ket("tai_lieu_nop_co_mau", ten, [], MUC_KHOP,
                f"{xet} tài liệu nộp ghi đúng N {n}" + (f" và DE {de:.2f}" if de else "") + ghi_cu)


_DONG_TEN = re.compile(r"(?im)^\s*(?:\*\*)?(?:TÊN\s+ĐỀ\s+TÀI|Tên\s+đề\s+tài|Đề\s+tài)(?:\*\*)?\s*[:：]\s*"
                       r"(?:\*\*)?\s*(.+?)\s*$")


def _chuan_ten(t: str) -> str:
    # bỏ MỌI dấu câu: bộ chuẩn trình bày của G2 đổi «—» thành «,» — cùng một tên, chỉ khác dấu
    t = unicodedata.normalize("NFC", str(t or "")).lower()
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]|_", " ", t)).strip()


def _ten_trong_van_ban(vb: str, tieu_de_h2: bool = False) -> List[str]:
    dau = "\n".join((vb or "").splitlines()[:60])
    # cắt phần đuôi cùng dòng kiểu «… | Phiên bản: 1.0 | Ngày: …» (hồ sơ đạo đức C1a)
    ra = [re.split(r"\s+\|\s+", m.group(1))[0] for m in _DONG_TEN.finditer(vb or "")]
    if not ra and tieu_de_h2:
        m = re.search(r"(?m)^##\s+(.+)$", dau)
        ra = [m.group(1)] if m else []
    return ra


def _truc_ten_de_tai(out_dir: Path, study: str, meta: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """15/11/2026 (giai đoạn «Xác định vấn đề & hình thành câu hỏi nghiên cứu»): MỘT tên đề tài chính thức
    (`study_meta.title`) trên mọi văn bản. Đề cương nộp, bản đăng ký WHO TRDS mục 10 (Scientific Title — phải trùng tên
    đề cương), hồ sơ đạo đức lệch ⇒ LỆCH MỀM. Văn bản do máy sinh (SAP, đề cương thống nhất G10, G3, G5) lệch ⇒ CẦN XEM:
    bộ sinh nay in tên chính thức (tools/ten_de_tai.py) — văn bản đã ký chỉ đổi ở lượt sửa đổi/ký sau. Trước vá, các bộ
    sinh in `topic` (chuỗi chủ đề tìm y văn của G0) làm tên đề tài."""
    ten = str(meta.get("title") or "").strip()
    nguon_vb = [("đề cương nộp", f"DE_CUONG_NOP_HOI_DONG_{study}.md", True, True),
                ("hồ sơ đạo đức", f"G2_A3_ETHICS_PACKAGE_{study}.md", False, True),
                ("SAP", f"G4_A5_SAP_FINAL_{study}.md", False, False),
                ("đề cương thống nhất G10", f"DE_CUONG_THONG_NHAT_{study}.md", True, False),
                ("G3", f"G3_A4_SAMPLE_SIZE_{study}.md", False, False),
                ("G5", f"G5_A6_DATA_MGMT_{study}.md", False, False)]
    co_vb = [x for x in nguon_vb if (out_dir / x[1]).is_file()]
    reg = sorted(out_dir.glob("G2_REGISTRATION_DRAFT_*.json"))
    if not co_vb and not reg:
        return None
    ten_dt = "Tên đề tài chính thức ↔ đề cương ↔ đăng ký ↔ hồ sơ đạo đức ↔ văn bản cổng"
    if not _co_that(ten):
        return _ket("ten_de_tai", ten_dt, [], MUC_CHUA_DU, "study_meta.title chưa có — không có tên chính thức để so")
    chuan = _chuan_ten(ten)
    mem, can, nguon, so = [], [], [], 0
    for nhan, tep, h2, chinh in co_vb:
        for t in _ten_trong_van_ban(_doc_text(out_dir / tep), h2):
            so += 1
            if _chuan_ten(t) != chuan:
                (mem if chinh else can).append(f"{nhan}: «{t[:90]}»")
                nguon.append({"cong": "G10" if chinh else "—", "noi": nhan, "gia_tri": t[:120]})
    for p in reg:
        d = _doc_json(p)
        for it in d.get("items") or []:
            if isinstance(it, dict) and it.get("number") == 10:
                so += 1
                if _chuan_ten(it.get("value")) != chuan:
                    mem.append(f"bản đăng ký mục 10 (Scientific Title): «{str(it.get('value'))[:90]}»")
                    nguon.append({"cong": "G2", "noi": p.name, "gia_tri": str(it.get("value"))[:120]})
    if mem:
        return _ket("ten_de_tai", ten_dt, nguon[:10], MUC_LECH_MEM,
                    "khác tên chính thức — " + "; ".join(mem + can) + ". Sửa theo study_meta.title (G2: sinh lại bản "
                    "đăng ký; tên khoa học riêng thì khai gate_params.G2.scientific_title)")
    if can:
        return _ket("ten_de_tai", ten_dt, nguon[:10], MUC_CAN_XEM,
                    "văn bản do máy sinh còn mang tên chủ đề G0 — " + "; ".join(can)
                    + " (bộ sinh đã sửa; cập nhật ở lượt sinh/sửa đổi/ký sau)")
    if not so:
        return _ket("ten_de_tai", ten_dt, [], MUC_CHUA_DU, "không đọc được dòng tên đề tài nào trong các văn bản")
    return _ket("ten_de_tai", ten_dt, [], MUC_KHOP, f"{so} nơi ghi đúng tên chính thức")


_MUC_TIEU_PHAN_TICH = re.compile(r"yếu\s+tố|mối\s+liên\s+quan|liên\s+quan\s+(?:đến|với|giữa)|so\s+sánh|ảnh\s+hưởng|"
                                 r"hiệu\s+quả|nguy\s+cơ|tác\s+động", re.I)
_THAM_DO = re.compile(r"thăm\s+dò|không\s+kiểm\s+định|exploratory", re.I)
_LOAI_CO_GIA_THUYET = frozenset({"treatment", "diagnosis", "prognosis", "harm"})


def _truc_cau_hoi_gia_thuyet(meta: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """15/11/2026: câu hỏi nghiên cứu (G0 loại câu hỏi · G1 research_question) ↔ mục tiêu G1 ↔ giả thuyết G0.
    - Câu hỏi MÔ TẢ có mục tiêu PHÂN TÍCH (yếu tố liên quan, so sánh, ảnh hưởng…) ⇒ mục tiêu đó phải có giả thuyết định
      trước (`G0.hypothesis_secondary`) hoặc tự ghi «thăm dò / không kiểm định» — thiếu ⇒ CẦN XEM (nguy cơ diễn giải p
      như kiểm định khẳng định).
    - Câu hỏi điều trị/chẩn đoán/tiên lượng/tác hại không khai mô tả ⇒ phải có H0 và H1 — thiếu ⇒ LỆCH MỀM.
    - Mục tiêu nói «yếu tố…» mà câu hỏi nghiên cứu không hỏi ⇒ CẦN XEM (câu hỏi không phủ mục tiêu)."""
    g0, g1 = _gp(meta, "G0"), _gp(meta, "G1")
    ob = [str(x) for x in (g1.get("objectives") or []) if _co_that(x)]
    rq = str(g1.get("research_question") or "")
    if not ob and not _co_that(rq):
        return None
    ten = "Câu hỏi nghiên cứu ↔ mục tiêu ↔ giả thuyết"
    qt = str(g0.get("question_type") or "").strip().lower()
    mo_ta = str(g0.get("test_type") or "").strip().lower() in ("descriptive", "mô tả") or qt == "descriptive"
    mem, can = [], []
    if not _co_that(rq):
        can.append("G1 chưa có research_question")
    pt = [o for o in ob if _MUC_TIEU_PHAN_TICH.search(o)]
    if mo_ta and pt and not _co_that(g0.get("hypothesis_secondary")):
        thieu = [o[:70] for o in pt if not _THAM_DO.search(o)]
        if thieu:
            can.append(f"câu hỏi mô tả nhưng {len(thieu)} mục tiêu phân tích chưa có giả thuyết định trước "
                       f"(G0.hypothesis_secondary) hay ghi «thăm dò»: {'; '.join(thieu)}")
    if qt in _LOAI_CO_GIA_THUYET and not mo_ta and not (_co_that(g0.get("hypothesis_h0"))
                                                         and _co_that(g0.get("hypothesis_h1"))):
        mem.append(f"câu hỏi loại {qt} (không mô tả) nhưng G0 thiếu H0/H1")
    if _co_that(rq) and any(re.search(r"yếu\s+tố", o, re.I) for o in ob) and not re.search(r"yếu\s+tố", rq, re.I):
        can.append("mục tiêu có «yếu tố …» mà câu hỏi nghiên cứu không hỏi về yếu tố")
    nguon = [{"cong": "G0", "noi": "question_type/test_type", "gia_tri": f"{qt or '—'} / {g0.get('test_type') or '—'}"},
             {"cong": "G1", "noi": "objectives", "gia_tri": f"{len(ob)} mục tiêu, {len(pt)} phân tích"}]
    if mem:
        return _ket("cau_hoi_gia_thuyet", ten, nguon, MUC_LECH_MEM, "; ".join(mem + can))
    if can:
        return _ket("cau_hoi_gia_thuyet", ten, nguon, MUC_CAN_XEM, "; ".join(can))
    return _ket("cau_hoi_gia_thuyet", ten, nguon, MUC_KHOP,
                f"{len(ob)} mục tiêu ({len(pt)} phân tích) khớp loại câu hỏi và giả thuyết; câu hỏi nghiên cứu phủ "
                "mục tiêu")


# ── Giai đoạn «Tổng quan tài liệu» (15/11/2026) ─────────────────────────────────────────────────────────────────────
# Bác sĩ 15/11/2026: «… Tổng Quan Tài Liệu … Hãy đảm bảo sự đồng bộ xuyên suốt và chính xác nhất» + «mỗi vấn đề … phải
# được cập nhật vào hệ thống». Kiểm tay C1a: TLTK đề cương nộp sạch (52 mục, đúng Vancouver, biên nhận A12 phủ đủ 35
# PMID + 14 DOI) nhưng biên nhận rút bài đã quá hạn 30 ngày. Kiểm tay BTM: danh mục trích dẫn mà chủ nhiệm đã loại
# 19 bài (25/10) không được công cụ nào của repo y khoa đọc — sổ chứng cứ G1 (A2b, 28/10) vẫn liệt kê cả 19 bài đã
# loại; 28/47 trích dẫn không có bản ghi kiểm rút bài theo từng mã; nguồn phương pháp dẫn ở SAP/G3/G1 chưa vào danh
# mục. Trục dưới đây đo đúng các chỗ đó cho MỌI đề tài.
_VAN_BAN_CONG_TRICH = (
    ("G1", "G1_A2_PROTOCOL_DESIGN_{s}.md", "thiết kế G1 (A2)"),
    ("G3", "G3_BO_BIEN_SO_{s}.md", "bộ biến G3"),
    ("G4", "G4_A5_SAP_FINAL_{s}.md", "SAP"),
    ("G10", "DE_CUONG_THONG_NHAT_{s}.md", "đề cương thống nhất G10"),
)
HAN_RUT_BAI_NGAY = 30  # cùng hạn trạng thái rút bài của sổ xác minh nguồn (CLAUDE.md §6.4)
_MUC_A2B_NGOAI_SO = re.compile(r"^##\s*Đã (?:loại khỏi danh mục|sàng ở G0)", re.M)


def _hom_nay() -> date:
    return date.today()


def _da_kiem_rut_bai(out_dir: Path, study: str) -> Tuple[Dict[str, Optional[str]], Dict[str, str]]:
    """({khoá «pmid:/doi:» → ngày kiểm GẦN NHẤT có bản ghi theo TỪNG định danh}, {khoá → trạng thái DƯƠNG}).

    Nguồn: `KIEM_RUT_BAI_TRICH_DAN_<mã>.json` (tools/kiem_rut_bai_trich_dan.py — chỉ mã có phán quyết), biên nhận A12
    (`pmids_checked`) + bảng DOI của báo cáo A12, khoá `rut_bai` của tổng hợp G0 (chỉ mã được NÊU TÊN — câu «56 PMID
    đã kiểm» không đối chiếu được từng mã), `G0_checkpoint.pmids_verified` (bước R1C của G0)."""
    import danh_muc_trich_dan as DMT  # noqa: PLC0415
    import kiem_rut_bai_trich_dan as KRB  # noqa: PLC0415

    ngay: Dict[str, Optional[str]] = {}

    def _them(khoa: Iterable[str], luc: Optional[str]) -> None:
        for k in khoa:
            cu = ngay.get(k)
            ngay[k] = max(x for x in (cu, luc) if x) if (cu or luc) else None

    rec = _doc_json(out_dir / "A12_RETRACTION_RECEIPT.json")
    luc_a12 = str(rec.get("checked_at_utc") or "")[:10] or None
    _them({f"pmid:{str(p).strip()}" for p in rec.get("pmids_checked") or []}, luc_a12)
    _them(DMT.dinh_danh(_doc_text(out_dir / f"A12_CITATION_VERIFICATION_{study}.md")), luc_a12)
    rb = _doc_json(out_dir / f"G0_TONG_HOP_BANG_CHUNG_{study}.json").get("rut_bai")
    if isinstance(rb, dict):
        chu = json.dumps(rb, ensure_ascii=False)
        _them(DMT.dinh_danh(chu) | {f"pmid:{p}" for p in re.findall(r"(?<![\d./-])(\d{7,8})(?![\d./-])", chu)},
              str(rb.get("ngay") or "")[:10] or None)
    cp0 = _doc_json(out_dir / "G0_checkpoint.json")
    _them({f"pmid:{str(p).strip()}" for p in cp0.get("pmids_verified") or []},
          str(cp0.get("generated_at") or "")[:10] or None)
    kq = KRB.doc_ket_qua(out_dir, study)
    luc = str(kq.get("checked_at") or "")[:10] or None
    duong: Dict[str, str] = {}
    for k, v in (kq.get("ket_qua") or {}).items():
        st = str((v or {}).get("status") or "")
        if st in KRB.CO_PHAN_QUYET:
            _them({k}, luc)
        if st in KRB.DUONG_TINH:
            duong[k] = st
    return ngay, duong


def _khong_lien_quan_g0(out_dir: Path, study: str) -> set:
    """Khoá bài G0 sàng là LẠC ĐỀ (lien_quan «khong» hoặc nhánh không lọc)."""
    import danh_muc_trich_dan as DMT  # noqa: PLC0415

    th = _doc_json(out_dir / f"G0_TONG_HOP_BANG_CHUNG_{study}.json")
    ra: set = set()
    for x in th.get("sang_loc") or []:
        if isinstance(x, dict) and x.get("lien_quan") == "khong":
            ra |= DMT.khoa_cua(x)
    for x in th.get("sang_loc_khong_loc") or []:
        if isinstance(x, dict):
            ra |= DMT.khoa_cua(x)
    return ra


def _ma_ngan(khoa: Iterable[str], n: int = 8) -> str:
    ds = sorted(khoa)
    return ", ".join(k.split(":", 1)[1] for k in ds[:n]) + (f" (+{len(ds) - n})" if len(ds) > n else "")


def _truc_trich_dan(out_dir: Path, study: str, meta: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """TLTK đề cương nộp ↔ trích dẫn trong thân ↔ danh mục trích dẫn (gồm quyết định LOẠI của chủ nhiệm) ↔ văn bản
    cổng ↔ bản ghi kiểm rút bài. LỆCH MỀM: số trích thiếu mục/mục không được trích/sai thứ tự Vancouver/trùng định danh;
    dùng bài chủ nhiệm đã loại trong TLTK, danh mục hay văn bản cổng; mục TLTK có định danh mà chưa có bản ghi kiểm rút
    bài. CẦN XEM: biên nhận rút bài quá 30 ngày; trích bài G0 sàng là lạc đề; nguồn dẫn ở SAP/G3/G1/khoảng trống chưa
    vào TLTK (hay danh mục khi chưa có đề cương); sổ A2b còn liệt kê bài đã loại; mục danh mục chưa kiểm rút bài theo
    từng mã. Không có cả đề cương nộp lẫn danh mục ⇒ None (chưa tới giai đoạn này)."""
    import danh_muc_trich_dan as DMT  # noqa: PLC0415

    ten = "Tổng quan tài liệu — TLTK ↔ danh mục trích dẫn ↔ kiểm rút bài"
    dc = _doc_text(out_dir / f"DE_CUONG_NOP_HOI_DONG_{study}.md")
    tach = DMT.tach_tltk(dc) if dc else None
    td, lb = DMT.trich_dan(out_dir, study), DMT.loai_bo(out_dir, study)
    if tach is None and not td and not lb:
        return None if not dc else _ket("trich_dan_tong_quan", ten, [], MUC_CHUA_DU,
                                        "đề cương nộp không có mục TÀI LIỆU THAM KHẢO đánh số — chưa đủ để so")
    mem: List[str] = []
    can: List[str] = []
    nguon: List[Dict[str, Any]] = []
    ngay_rb, duong = _da_kiem_rut_bai(out_dir, study)
    da = set(ngay_rb)
    lac_de = _khong_lien_quan_g0(out_dir, study)

    def _ly_do_loai(k: str) -> str:
        x = lb.get(k) or {}
        return f"{k.split(':', 1)[1]} ({str(x.get('ly_do') or x.get('nhom_ly_do') or '')[:60]}; {x.get('ngay') or '?'})"

    tltk_khoa: set = set()
    if tach is not None:
        muc, than = tach
        so = DMT.so_trich_dan(than)
        thieu, khong_trich = sorted(set(so) - set(muc)), sorted(set(muc) - set(so))
        if thieu:
            mem.append(f"thân đề cương trích số không có trong TLTK: {thieu[:10]}")
        if khong_trich:
            mem.append(f"TLTK có mục không được trích trong thân: {khong_trich[:10]}")
        if sorted(muc) != list(range(1, len(muc) + 1)):
            mem.append("TLTK đánh số không liên tục")
        dau = list(dict.fromkeys(x for x in so if x in muc))
        sai = next((i for i in range(1, len(dau)) if dau[i] < dau[i - 1]), None)
        if sai is not None:
            mem.append(f"thứ tự trích lần đầu không theo Vancouver: [{dau[sai]}] xuất hiện sau [{dau[sai - 1]}]")
        theo_khoa: Dict[str, List[int]] = {}
        chua_rb: List[int] = []
        for n, dong in sorted(muc.items()):
            k = DMT.dinh_danh(dong)
            tltk_khoa |= k
            for kk in k:
                theo_khoa.setdefault(kk, []).append(n)
            if k and not (k & da):
                chua_rb.append(n)
        trung = {kk: ns for kk, ns in theo_khoa.items() if len(ns) > 1}
        if trung:
            mem.append("TLTK trùng định danh: " + "; ".join(f"{kk.split(':', 1)[1]} ở số {ns}"
                                                          for kk, ns in sorted(trung.items())[:5]))
        if tltk_khoa & set(lb):
            mem.append("TLTK dùng bài chủ nhiệm đã LOẠI khỏi danh mục trích dẫn: "
                       + "; ".join(_ly_do_loai(k) for k in sorted(tltk_khoa & set(lb))[:5]))
        if tltk_khoa & lac_de:
            can.append(f"TLTK trích bài G0 đã sàng là lạc đề: {_ma_ngan(tltk_khoa & lac_de)} — chủ nhiệm xem lại")
        if chua_rb:
            mem.append(f"{len(chua_rb)} mục TLTK có PMID/DOI mà chưa có bản ghi kiểm rút bài theo từng định danh "
                       f"(số {chua_rb[:12]}) — chạy python tools/kiem_rut_bai_trich_dan.py --study {study} --ghi")
        cu: List[int] = []
        for n, dong in sorted(muc.items()):
            k = DMT.dinh_danh(dong) & da
            luc = max((ngay_rb[x] for x in k if ngay_rb.get(x)), default=None)
            try:
                if k and (luc is None or (_hom_nay() - date.fromisoformat(luc)).days > HAN_RUT_BAI_NGAY):
                    cu.append(n)
            except ValueError:
                cu.append(n)
        if cu:
            can.append(f"{len(cu)} mục TLTK có lần kiểm rút bài gần nhất quá {HAN_RUT_BAI_NGAY} ngày (số {cu[:12]}) — "
                       f"kiểm lại trước khi nộp: python tools/kiem_rut_bai_trich_dan.py --study {study} --ghi (tệp "
                       "riêng, không ghi đè biên nhận A12 đã băm trong gói G10)")
        nguon.append({"cong": "G10", "noi": f"DE_CUONG_NOP_HOI_DONG_{study}.md — TÀI LIỆU THAM KHẢO",
                      "gia_tri": f"{len(muc)} mục, {len(so)} lượt trích, {len(tltk_khoa)} định danh"})
    if td or lb:
        n_td = len({id(v) for v in td.values()})
        n_lb = len({id(v) for v in lb.values()})
        if set(td) & set(lb):
            mem.append(f"mục vừa ở «trich_dan» vừa ở «loai_bo» của danh mục: {_ma_ngan(set(td) & set(lb))}")
        if set(td) & lac_de:
            can.append(f"danh mục trích dẫn giữ bài G0 đã sàng là lạc đề: {_ma_ngan(set(td) & lac_de)}")
        if tach is None:
            chua = {id(v): v for k, v in td.items() if not (DMT.khoa_cua(v) & da)}
            if chua:
                can.append(f"{len(chua)}/{n_td} mục danh mục trích dẫn chưa có bản ghi kiểm rút bài theo TỪNG định "
                           "danh (bản ghi G0 chỉ ghi tổng số hoặc ghi «chưa kiểm») — chạy python "
                           "tools/kiem_rut_bai_trich_dan.py "
                           f"--study {study} --ghi trước khi đưa vào TLTK: "
                           + _ma_ngan({sorted(DMT.khoa_cua(v))[0] for v in chua.values()}))
        nguon.append({"cong": "G0", "noi": DMT.TEP.format(study=study),
                      "gia_tri": f"{n_td} trích dẫn, {n_lb} đã loại"})
    rut = {k: v for k, v in duong.items() if k in tltk_khoa or k in td}
    if rut:
        mem.append("trích dẫn có tín hiệu RÚT BÀI/expression of concern (KIEM_RUT_BAI_TRICH_DAN): "
                   + "; ".join(f"{k.split(':', 1)[1]} {v}" for k, v in sorted(rut.items())[:5])
                   + " — không dựa vào bài này; cổng A12 chặn ở G10")
    tham_chieu, ten_tc = (tltk_khoa, "TLTK đề cương nộp") if tach is not None else (set(td), "danh mục trích dẫn")
    for _g, mau, nhan in _VAN_BAN_CONG_TRICH:
        k = DMT.dinh_danh(_doc_text(out_dir / mau.format(s=study)))
        if k & set(lb):
            mem.append(f"{nhan} dẫn bài chủ nhiệm đã LOẠI: "
                       + "; ".join(_ly_do_loai(x) for x in sorted(k & set(lb))[:4]))
        if tham_chieu and k - tham_chieu - set(lb):
            can.append(f"{nhan} dẫn nguồn chưa có trong {ten_tc}: {_ma_ngan(k - tham_chieu - set(lb))}")
    a2b = _doc_text(out_dir / f"G1_A2b_EVIDENCE_LEDGER_{study}.md")
    m_ngoai = _MUC_A2B_NGOAI_SO.search(a2b)
    trong_so = DMT.dinh_danh(a2b[:m_ngoai.start()] if m_ngoai else a2b) & set(lb)
    if trong_so:
        can.append(f"sổ chứng cứ G1 (A2b) còn liệt kê {len(trong_so)} bài đã loại như chứng cứ "
                   f"({_ma_ngan(trong_so, 5)}) — dựng lại: python tools/run_g1_auto.py --study {study} "
                   "--dung-lai-ho-tro")
    if tham_chieu:
        g3 = _gp(meta, "G3")
        k3 = DMT.dinh_danh(" ".join(str(v) for kk, v in g3.items() if str(kk).endswith("_source")))
        if k3 - tham_chieu:
            can.append(f"nguồn tham số G3 (*_source) chưa có trong {ten_tc}: {_ma_ngan(k3 - tham_chieu)}")
        for g in _doc_json(out_dir / f"G0_KHOANG_TRONG_{study}.json").get("guideline_lien_quan") or []:
            if not isinstance(g, dict):
                continue
            # Dòng hồ sơ khoảng trống tự khai CHƯA dùng («PARTIAL — chưa đọc văn bản …», «chưa rà») không phải guideline
            # làm căn cứ ⇒ không đòi trích (đo C1a 15/11/2026: dòng «Hướng dẫn quốc tế … PARTIAL» bị báo nhầm).
            if re.search(r"^\s*PARTIAL\b|chưa\s+(?:đọc|rà)", f"{g.get('noi_dung') or ''} {g.get('muc') or ''}", re.I):
                continue
            kg = DMT.dinh_danh(f"{g.get('nguon') or ''} {g.get('ten') or ''}")
            if kg and not (kg & tham_chieu):
                can.append(f"guideline của khoảng trống «{str(g.get('ten') or '')[:50]}» chưa có trong {ten_tc}")
    if mem:
        return _ket("trich_dan_tong_quan", ten, nguon, MUC_LECH_MEM, "; ".join(mem + can))
    if can:
        return _ket("trich_dan_tong_quan", ten, nguon, MUC_CAN_XEM, "; ".join(can))
    return _ket("trich_dan_tong_quan", ten, nguon, MUC_KHOP,
                "TLTK/danh mục khớp trích dẫn trong thân, thứ tự Vancouver, quyết định loại của chủ nhiệm và bản ghi "
                "kiểm rút bài; nguồn dẫn ở văn bản cổng đều có trong danh mục")


def _truc_ma_tran_muc_tieu(out_dir: Path, study: str, meta: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Giai đoạn «Mục tiêu» (15/11/2026): đọc kết quả `ma_tran_muc_tieu_bien.kiem` (MT-01…MT-11 — mục tiêu → biến →
    câu hỏi → phân tích SAP → bảng giả) vào cùng bảng đồng bộ. Chưa có ma trận ⇒ CHƯA ĐỦ ĐỂ SO (không bao giờ «khớp»);
    có lỗi ⇒ LỆCH MỀM; đạt nhưng còn cảnh báo (công thức biến phái sinh chưa duyệt, SAP chưa gọi đúng tên biến) ⇒ CẦN
    XEM. Chưa chốt mục tiêu ở G1 ⇒ None (chưa tới giai đoạn)."""
    import ma_tran_muc_tieu_bien as MTB  # noqa: PLC0415

    if not MTB.muc_tieu_g1(meta):
        return None
    kq = MTB.kiem(out_dir, study, meta=meta)
    ten = "Mục tiêu → biến → câu hỏi → phân tích SAP → bảng giả (ma trận MT)"
    nguon = [{"cong": "G1–G4", "noi": MTB.TEP_MA_TRAN, "gia_tri": kq.get("tom_tat") or kq.get("trang_thai")}]
    loi = [f"{x['ma']}: {x['noi_dung']}" for x in kq.get("loi") or []]
    cb = kq.get("canh_bao") or []
    if kq.get("trang_thai") == MTB.TRANG_THAI_KHONG_CO:
        return _ket("ma_tran_muc_tieu", ten, nguon, MUC_CHUA_DU, "; ".join(loi) or "chưa có ma trận mục tiêu → biến")
    if loi:
        return _ket("ma_tran_muc_tieu", ten, nguon, MUC_LECH_MEM, "; ".join(loi[:5]))
    if cb:
        dem: Dict[str, int] = {}
        for x in cb:
            dem[x["ma"]] = dem.get(x["ma"], 0) + 1
        return _ket("ma_tran_muc_tieu", ten, nguon, MUC_CAN_XEM,
                    "ma trận đạt; còn cảnh báo " + ", ".join(f"{k} ×{v}" for k, v in sorted(dem.items()))
                    + " (MT-08 = công thức biến phái sinh chờ thống kê viên/PI duyệt; MT-09 = SAP chưa gọi đúng tên "
                      "biến)")
    return _ket("ma_tran_muc_tieu", ten, nguon, MUC_KHOP, "ma trận đạt, không còn cảnh báo")


def truc_chuoi(out_dir: Path, study: str, meta: Dict[str, Any], sap_text: str) -> List[Dict[str, Any]]:
    """Các trục chuỗi đầy đủ (mỗi trục tự bắt lỗi của mình — một trục hỏng không làm mất các trục khác)."""
    td = _tu_dien(out_dir, study)
    ra: List[Dict[str, Any]] = []
    for ham in (lambda: _truc_bien_de_cuong(out_dir, study), lambda: _truc_cong_cu(out_dir, study, td),
                lambda: _truc_muc_tieu(meta, sap_text), lambda: _truc_chon_mau(meta, sap_text, td),
                lambda: _truc_dac_ta(out_dir), lambda: _truc_tong_quan(out_dir, study, meta),
                lambda: _truc_tinh_lai_co_mau(out_dir, study, meta, sap_text),
                lambda: _truc_ky_thuat_chon_mau(out_dir, study, meta, sap_text),
                lambda: _truc_tai_lieu_nop(out_dir, study, meta),
                lambda: _truc_ten_de_tai(out_dir, study, meta), lambda: _truc_cau_hoi_gia_thuyet(meta),
                lambda: _truc_trich_dan(out_dir, study, meta),
                lambda: _truc_ma_tran_muc_tieu(out_dir, study, meta)):
        try:
            k = ham()
        except Exception as e:  # noqa: BLE001
            k = _ket("chuoi_loi", "Trục chuỗi lỗi", [], MUC_CHUA_DU, f"{type(e).__name__}: {str(e)[:120]}")
        if k:
            ra.append(k)
    return ra


def thong_so_bat_buoc(thiet_ke: Optional[str]) -> List[str]:
    """Mã thông số G10 đòi SO ĐƯỢC theo thiết kế (chưa rõ thiết kế ⇒ đòi đủ cả ba — cố ý bi quan)."""
    ds = ["thiet_ke"]
    if thiet_ke not in _KHONG_CO_CO_MAU:
        ds.append("co_mau")
    if thiet_ke not in _KHONG_CO_KET_CUC:
        ds.append("ket_cuc_chinh")
    return ds


def tieu_chi_g10(ket: Dict[str, Any]) -> Tuple[str, str]:
    """(trạng thái G10 «PASS|BLOCK|REVIEW», bằng chứng ngắn) — LỆCH CỨNG chặn; LỆCH MỀM hoặc thông số BẮT BUỘC chưa đủ
    để so ⇒ giữ chờ chủ nhiệm; CẦN XEM không đổi trạng thái. Bằng chứng không chứa «|» (ô bảng Markdown)."""
    cung = [k["ten"] for k in ket["thong_so"] if k["muc"] == MUC_LECH_CUNG]
    mem = [k["ten"] for k in ket["thong_so"] if k["muc"] == MUC_LECH_MEM]
    bat_buoc = set(thong_so_bat_buoc(ket.get("thiet_ke")))
    thieu = [k["ten"] for k in ket["thong_so"] if k["ma"] in bat_buoc and k["muc"] == MUC_CHUA_DU]
    bang = "; ".join(f"{k['ma']}={k['muc']}" for k in ket["thong_so"])
    if cung:
        return "BLOCK", f"LỆCH CỨNG: {', '.join(cung)} — {bang}"
    if mem or thieu:
        phan = []
        if mem:
            phan.append(f"LỆCH MỀM (chủ nhiệm giải trình): {', '.join(mem)}")
        if thieu:
            phan.append(f"thông số bắt buộc CHƯA ĐỦ NƠI ĐỂ SO (không phải «khớp»): {', '.join(thieu)}")
        return "REVIEW", " · ".join(phan) + f" — {bang}"
    return "PASS", bang


def ket_luan_trung_thuc(ket: Dict[str, Any]) -> str:
    """Một câu kết luận KHÔNG được đọc «PASS» thành «đồng bộ hoàn toàn» (15/11/2026).

    Bác sĩ 15/11/2026: «Hệ thống … đã kết luận về tính hoàn thiện nhưng kiểm lại thì không đạt được sự thống nhất, đồng
    bộ» — G10-AUTO-11 chỉ chặn LỆCH CỨNG và giữ LỆCH MỀM; mục CẦN XEM và CHƯA ĐỦ ĐỂ SO không đổi trạng thái cổng nên
    «PASS» vẫn đi cùng việc còn mở. Câu này buộc mọi bản in nêu đúng phần còn mở."""
    mo = [k for k in ket["thong_so"] if k["muc"] in (MUC_LECH_CUNG, MUC_LECH_MEM, MUC_CAN_XEM, MUC_CHUA_DU)]
    if not mo:
        return f"Kết luận: {len(ket['thong_so'])}/{len(ket['thong_so'])} trục khớp — trong PHẠM VI các trục đã đo."
    return (f"Kết luận: CHƯA đồng bộ hoàn toàn — còn {len(mo)}/{len(ket['thong_so'])} trục mở ("
            + ", ".join(f"{k['ma']}={k['muc']}" for k in mo) + "); trạng thái cổng G10 không thay cho việc xử lý "
            "các trục này. Không báo «hoàn thiện» khi còn trục mở.")


def in_bang(ket: Dict[str, Any]) -> None:
    print(f"NHẤT QUÁN XUYÊN CỔNG — {ket['study']}")
    for k in ket["thong_so"]:
        print(f"  {BIEU_TUONG[k['muc']]} {k['ten']}: {k['ghi_chu']}")
        if k["muc"] in (MUC_LECH_CUNG, MUC_LECH_MEM, MUC_CAN_XEM):
            for n in k["nguon"]:
                print(f"      · {n['cong']:<3} {n['noi']}: {str(n['gia_tri'])[:110]}")
    t = ket["tong"]
    print(f"  Tổng: 🔴 {t[MUC_LECH_CUNG]} lệch cứng · 🟠 {t[MUC_LECH_MEM]} lệch mềm · 🟡 {t[MUC_CAN_XEM]} cần xem · "
          f"🟢 {t[MUC_KHOP]} khớp · ⚪ {t[MUC_CHUA_DU]} chưa đủ để so")
    trang_thai, _ = tieu_chi_g10(ket)
    print(f"  Áp ở G10-AUTO-11: {trang_thai}")
    print("  " + ket_luan_trung_thuc(ket))
    print("Chỉ ĐỌC và BÁO — không sửa artifact, không chọn giá trị thay chủ nhiệm. Cần bác sĩ kiểm chứng.")


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Đối chiếu thông số then chốt xuyên cổng G0–G10 (chỉ đọc)")
    ap.add_argument("--study", required=True)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    out_dir = BASE / "exports" / a.study
    if not (out_dir / "study_meta.json").is_file():
        print(f"KHÔNG ĐỌC ĐƯỢC: không có {out_dir}/study_meta.json", file=sys.stderr)
        return 3
    try:
        ket = doi_chieu(out_dir, a.study)
        trang_thai, _ = tieu_chi_g10(ket)
    except Exception as exc:  # noqa: BLE001 — hỏng ⇒ KHÔNG ĐO ĐƯỢC (mã 3), không bao giờ mã 0
        print(f"KHÔNG ĐO ĐƯỢC: bộ đối chiếu hỏng — {type(exc).__name__}: {exc}", file=sys.stderr)
        return 3
    if a.json:
        print(json.dumps(dict(ket, trang_thai_g10=trang_thai), ensure_ascii=False, indent=1, default=str))
    else:
        in_bang(ket)
    return {"BLOCK": 2, "REVIEW": 1}.get(trang_thai, 0)


if __name__ == "__main__":
    sys.exit(main())
