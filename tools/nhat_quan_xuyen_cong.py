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
