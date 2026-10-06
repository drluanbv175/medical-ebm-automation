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
from datetime import datetime
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
        if lech:
            dau = dau_van_tay_ket_cuc(nguon_kc)
            ok, ly_do = _xac_nhan_ket_cuc(meta, dau)
            noi_lech = ", ".join(n["cong"] + " (" + n["noi"] + ")" for n in lech)
            if ok:
                ket.append(_ket("ket_cuc_chinh", "Kết cục chính", nguon_kc, MUC_CAN_XEM,
                                f"{noi_lech} diễn đạt khác «{goc['cong']}» — chủ nhiệm ĐÃ xác nhận là cùng một kết cục "
                                f"(dấu {dau}): «{ly_do[:120]}»"))
            else:
                ket.append(_ket("ket_cuc_chinh", "Kết cục chính", nguon_kc, MUC_LECH_MEM,
                                f"{noi_lech} khác «{goc['cong']}» — đổi kết cục chính phải có chủ nhiệm giải trình "
                                "công khai (outcome switching); thống nhất về MỘT kết cục, hoặc nếu chỉ khác cách "
                                f"diễn đạt thì ghi gate_params.G10.xac_nhan_ket_cuc_chinh với dau_van_tay={dau} "
                                f"({ly_do})"))
        else:
            ket.append(_ket("ket_cuc_chinh", "Kết cục chính", nguon_kc, MUC_KHOP,
                            f"{len(nguon_kc)} nơi cùng chỉ một kết cục"))

    # 5) Quần thể (chỉ báo — văn bản tiêu chí dài ngắn khác nhau tự nhiên).
    tc = _mo_repr(trds.get("14"))
    tc_txt = _van_ban(tc.get("inclusion")) if isinstance(tc, dict) else _van_ban(tc)
    nguon_qt = [n for n in (
        {"cong": "G0", "noi": "study_meta.gate_params.G0.population",
         "gia_tri": _van_ban(_gp(meta, "G0").get("population"))},
        {"cong": "G1", "noi": "study_meta.gate_params.G1.population",
         "gia_tri": _van_ban(_gp(meta, "G1").get("population"))},
        {"cong": "G2", "noi": "đăng ký TRDS mục 14 (tiêu chí chọn)", "gia_tri": tc_txt},
    ) if _co_that(n["gia_tri"])]
    if len(nguon_qt) < 2:
        ket.append(_ket("quan_the", "Quần thể nghiên cứu", nguon_qt, MUC_CHUA_DU, "chỉ có ≤ 1 nơi ghi — chưa đủ để so"))
    else:
        thap = min(max(_bao_ham(a["gia_tri"], b["gia_tri"]), _bao_ham(b["gia_tri"], a["gia_tri"]))
                   for i, a in enumerate(nguon_qt) for b in nguon_qt[i + 1:])
        ket.append(_ket("quan_the", "Quần thể nghiên cứu", nguon_qt, MUC_KHOP if thap >= 0.5 else MUC_CAN_XEM,
                        f"độ bao hàm thấp nhất giữa các bản {thap:.2f}" + ("" if thap >= 0.5 else
                        " — các bản mô tả quần thể khác xa nhau, chủ nhiệm đọc lại cho thống nhất")))

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

    tong = {m: sum(1 for k in ket if k["muc"] == m) for m in _THU_TU_MUC}
    thiet_ke = next(iter(ma_tk)) if len(ma_tk) == 1 else None
    return {"study": study, "thiet_ke": thiet_ke, "thong_so": ket, "tong": tong,
            "muc_cao_nhat": _muc_cao_nhat(k["muc"] for k in ket)}


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
