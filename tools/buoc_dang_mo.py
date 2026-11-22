#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""buoc_dang_mo.py — ĐỀ TÀI ĐANG MỞ Ở KHÂU NÀO? (CHỈ ĐỌC — 22/11/2026)

NGUYÊN TẮC TỔNG (bác sĩ 22/11/2026, nguyên văn): «Mỗi quyết định trong nghiên cứu phải dựa trên bằng chứng khoa học,
được thực hiện một cách đạo đức, được kiểm chứng khách quan, và chỉ được chuyển sang bước tiếp theo khi bước hiện tại đã
đạt chuẩn xác định trước.» Công cụ này đo vế cuối: bước nào đã đạt chuẩn và khoá, bước nào đang mở.

VÌ SAO CÓ. Chỉ thị của bác sĩ cùng ngày: «Khi phát hiện một vấn đề không đúng trong quy trình thực hiện nghiên
cứu thì hệ thống phải quay lại bước đó để sửa, kiểm tra lại, sau khi đạt chuẩn thì "khóa" bước đó và mới cho phép
chuyển sang bước tiếp theo. Chứ cứ làm hoài và mãi luôn phải chỉnh sửa hoài». Trước công cụ này không lệnh nào trả lời
gọn «khâu nào đang mở, được sửa ở đâu, cổng nào chỉ còn chờ ký» — agent sửa văn bản ở khâu sau trong khi lỗi nằm ở
khâu trước, rồi phải sửa lại mãi.

LUẬT VẬN HÀNH (doctrine `dieu-phoi-nghien-cuu`, `_HOI-DONG-CONG.md`, `dieu-phoi-g0…g10`):
  1. Lỗi thuộc khâu (cổng) nào thì sửa ở NGUỒN của khâu đó (`study_meta.json → gate_params`, bộ biến G3, SAP G4…),
     không vá tay văn bản ở khâu sau.
  2. Kiểm lại khâu đó bằng chốt của CHÍNH nó: `tools/gN_quality_gate.py --study <mã> --no-write`, chấm sống
     `cong_song.trang_thai_song`, `tools/nhat_quan_xuyen_cong.py --study <mã>`.
  3. Đạt chuẩn thì KHOÁ (cổng thường: người có vai xác nhận gắn dấu vân tay nội dung; cổng cứng: chữ ký sổ cái qua
     `approve_gate.py`). Chỉ khi đó mới sinh lại và làm khâu kế tiếp, đúng thứ tự G0→G10.
  4. Đề tài thật: hệ đưa từng khâu tới đạt chuẩn rồi trình bác sĩ MỘT danh sách khoá theo thứ tự để ký một lượt.
  5. (Chỉ thị thứ hai cùng ngày) Đầu ra nói về SẢN PHẨM — đã giao gì, đạt chuẩn nào, khâu nào đã khoá; không chia
     «phần của máy / phần của bác sĩ». Chữ ký pháp lý không giả được, nên nó xuất hiện như GÓI KÝ ĐÃ CHUẨN BỊ, không
     phải danh sách việc treo. Khoá máy-đọc (`ket_luan` của bảng trách nhiệm…) giữ nguyên, chỉ đổi lời trình bày.

CÔNG CỤ ĐO GÌ (duyệt G0→G10 theo thứ tự SỐ, chấm sống từng cổng):
  • Mức của cổng: PASS · READY · DRAFT · BLOCKED · KHONG_DO_DUOC (của `cong_song.muc_cua_trang_thai`) · CHUA_CHAY
    (chưa có checkpoint lẫn tài liệu nào của cổng — không gọi bộ chấm).
  • ĐÃ KHOÁ: cổng thường và cổng cứng = chấm sống PASS (bộ chấm cổng cứng G4/G5/G8/G9/G10 đã gồm kiểm sổ cái; cổng
    thường PASS chỉ khi xác nhận gắn đúng dấu vân tay nội dung hiện tại). RIÊNG G2 = `g7_quality_gate.g2_da_duyet`
    (chữ ký sổ cái khớp gói đạo đức hiện tại + hợp đồng chất lượng — CÙNG nghĩa «G2 đã duyệt» mà G5–G10 và
    study_readiness dùng). READY KHÔNG BAO GIỜ là khoá; «không đo được» KHÔNG BAO GIỜ là khoá.
  • (a) KHÂU ĐANG MỞ = cổng ĐẦU TIÊN chưa khoá.
  • (c) DANH SÁCH KHOÁ THEO THỨ TỰ (gói ký đã chuẩn bị): từ khâu đang mở đi tiếp, gom các cổng ĐẠT CHUẨN ĐỂ KHOÁ — chỉ
    còn chữ ký/xác nhận của vai có thẩm quyền —, dừng ở cổng đầu tiên chưa đạt (cổng đã khoá xen giữa thì bỏ qua).
    «Đạt chuẩn để khoá» = cổng cứng ở mức READY; cổng thường ở mức READY hoặc trạng thái «DRAFT_READY_…» — VÀ bảng
    trách nhiệm `hoi_dong_cong.trach_nhiem` kết luận DAT_TIEU_CHI/AGENT_XONG_CHO_NGUOI (mã 0: hệ đã hoàn thiện mọi
    tiêu chí không cần chữ ký). Vai ký của cổng cứng lấy từ `gate_contract._GATE_REQUIRED_STAKEHOLDERS`; vai chốt của
    cổng thường lấy từ các tiêu chí xác nhận trong bảng trách nhiệm.
  • KHÂU CẦN HOÀN THIỆN = cổng nơi danh sách dừng (bằng khâu đang mở khi khâu mở chưa đạt chuẩn) — CHỖ DUY NHẤT được
    sửa lúc này; kèm mục chưa đạt và cổng trước nó phụ thuộc (nếu có).
  • (b) Cổng SAU khâu cần hoàn thiện mà đã có tài liệu: «chưa được làm tiếp — sinh lại sau khi khâu mở được khoá»;
    cổng sau đã khoá từ trước (khoá ngoài thứ tự): giữ nguyên, sửa khâu trước làm đổi nguồn của nó thì dấu/chữ ký tự
    mất hiệu lực ⇒ kiểm và khoá lại theo thứ tự.

MÃ THOÁT: 0 mọi khâu đã khoá · 1 có khâu mở · 2 không đo được (trên đường quyết định có cổng/chữ ký/bảng trách nhiệm
không đo được) · 3 tham số sai (thiếu/sai mã đề tài, thư mục không có).

Chỉ đọc: không ghi tệp, không ký, không đổi cờ, không xác nhận thay. Cần bác sĩ kiểm chứng.

Dùng:
    python tools/buoc_dang_mo.py --study hai-long-benh-nhan-C1a-BVQY175
    python tools/buoc_dang_mo.py --study btm-dtd2-ngoai-tru-BVQY175 --json
    python tools/buoc_dang_mo.py --study <mã> --goc <thư mục chứa exports/>   # đo một bản chép chỉ đọc
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

for _luong in (sys.stdout, sys.stderr):  # Windows cp1252 làm hỏng print() tiếng Việt — ép UTF-8 (BH55/R4)
    try:
        _luong.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

BASE = Path(__file__).resolve().parents[1]
for _p in (str(BASE / "tools"), str(BASE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import cong_song as CS  # noqa: E402
import gate_contract as GC  # noqa: E402

SCHEMA = "buoc_dang_mo/v1"
# Thứ tự SỐ G0→G10 — tuyệt đối không sắp theo chữ (sắp chữ đặt G10 trước G2).
CONG: Tuple[str, ...] = tuple(f"G{i}" for i in range(11))
CHUA_CHAY = "CHUA_CHAY"
_MUC_HOP_LE = ("PASS", "READY", "DRAFT", "BLOCKED", CS.KHONG_DO_DUOC, CHUA_CHAY)
# Kết luận của hoi_dong_cong.trach_nhiem có mã 0 (mọi tiêu chí không cần chữ ký đã đạt) — khoá máy-đọc, giữ nguyên.
_HOAN_THIEN_MA_0 = ("DAT_TIEU_CHI", "AGENT_XONG_CHO_NGUOI")
_MA_DE_TAI = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")

# Vị trí của một cổng trong chuỗi khoá.
DA_KHOA = "DA_KHOA"                          # đã khoá, nằm trước khâu đang mở
CHO_KY = "CHO_KY"                            # đạt chuẩn để khoá — gói ký đã chuẩn bị (thuộc danh sách khoá)
KHAU_CAN_HOAN_THIEN = "KHAU_CAN_HOAN_THIEN"  # cổng đầu tiên chưa đạt — chỗ duy nhất được sửa lúc này
KHOA_NGOAI_THU_TU = "KHOA_NGOAI_THU_TU"      # đã khoá nhưng nằm sau khâu đang mở
CHUA_LAM_TIEP = "CHUA_LAM_TIEP"              # sau khâu cần hoàn thiện, đã có tài liệu, chưa khoá
CHUA_TOI_LUOT = "CHUA_TOI_LUOT"              # sau khâu cần hoàn thiện, chưa có tài liệu
GHI_CHU_CHUA_LAM_TIEP = "chưa được làm tiếp — sinh lại sau khi khâu mở được khoá"
GHI_CHU_KHOA_NGOAI_THU_TU = ("đã khoá trước khi khâu trước nó được khoá — giữ nguyên; sửa khâu trước làm đổi nguồn của "
                             "cổng này thì dấu/chữ ký tự mất hiệu lực ⇒ kiểm và khoá lại theo thứ tự")

Cham = Callable[[str, str, Path], Dict[str, Any]]
KhoaG2 = Callable[[str, Path], Tuple[bool, str]]
TrachNhiem = Callable[[str, str, Path], Dict[str, Any]]


def cong_cung() -> Tuple[str, ...]:
    """Cổng cứng theo NGUỒN SỰ THẬT DUY NHẤT gate_contract._GATE_REQUIRED_STAKEHOLDERS, đúng thứ tự G0→G10."""
    return tuple(g for g in CONG if g in GC._GATE_REQUIRED_STAKEHOLDERS)


def co_tai_lieu(out_dir: Path, gate: str) -> bool:
    """Cổng đã có checkpoint hoặc ít nhất một tệp `<GN>_…` trong thư mục đề tài («G1_*» không khớp «G10_…»)."""
    if (out_dir / f"{gate}_checkpoint.json").is_file():
        return True
    return any(p.is_file() for mau in (f"{gate}_*", f"{gate.lower()}_*") for p in out_dir.glob(mau))


# ───────────────────────────────────────────────────────────────────────────── bộ đo mặc định (thật)
def _cham_that(gate: str, study: str, out_dir: Path) -> Dict[str, Any]:
    # repo_root suy từ <gốc>/exports/<mã> — cùng quy ước cong_song/hoi_dong_cong (đệm chấm sống dùng chung).
    return CS.trang_thai_song(gate, study, out_dir, repo_root=out_dir.parent.parent)


def _khoa_g2_that(study: str, out_dir: Path) -> Tuple[bool, str]:
    import g7_quality_gate as G7Q  # noqa: PLC0415 — import lười

    return G7Q.g2_da_duyet(study, out_dir, repo_root=out_dir.parent.parent)


def _trach_nhiem_that(study: str, gate: str, out_dir: Path) -> Dict[str, Any]:
    import hoi_dong_cong as HD  # noqa: PLC0415 — import lười (mô-đun lớn)

    return HD.trach_nhiem(study, gate, out_dir)


# ───────────────────────────────────────────────────────────────────────────── phân tích
def _muc_chuan(song: Dict[str, Any]) -> str:
    muc = str(song.get("muc") or CS.KHONG_DO_DUOC)
    return muc if muc in _MUC_HOP_LE else CS.KHONG_DO_DUOC


def _da_khoa(gate: str, muc: str, study: str, out_dir: Path, khoa_g2: KhoaG2) -> Tuple[Optional[bool], str]:
    """(đã khoá? — None = không đo được, lý do). READY không bao giờ là khoá; không đo được không bao giờ là khoá."""
    if muc == CHUA_CHAY:
        return False, "chưa chạy — chưa có tài liệu của cổng"
    if gate == "G2":
        try:
            ok, ly = khoa_g2(study, out_dir)
        except Exception as exc:  # noqa: BLE001 — không đo được ≠ đã khoá
            return None, f"không đo được chữ ký G2: {type(exc).__name__}: {str(exc)[:120]}"
        return ok is True, f"g2_da_duyet: {ly}"
    if muc == CS.KHONG_DO_DUOC:
        return None, "không đo được — KHÔNG BAO GIỜ là đã khoá"
    if muc == "PASS":
        if gate in cong_cung():
            return True, "chấm sống PASS (bộ chấm cổng cứng đã gồm chữ ký sổ cái)"
        return True, "chấm sống PASS (xác nhận gắn dấu vân tay nội dung hiện tại)"
    if muc == "READY" and gate in cong_cung():
        return False, "READY — đạt chuẩn để ký nhưng CHƯA ký (READY không phải khoá)"
    return False, f"chấm sống {muc}"


def _muc_cho_phep_khoa(gate: str, muc: str, status: str) -> Tuple[bool, str]:
    """Mức chấm sống đã tới bước khoá (ký/chốt) chưa — chưa xét bảng trách nhiệm."""
    if gate in cong_cung():
        if muc == "READY":
            return True, "cổng cứng READY"
        return False, f"cổng cứng ở mức {muc} — chưa READY để ký"
    if muc == "READY" or status.upper().startswith("DRAFT_READY_"):
        return True, "cổng thường ở bước chốt"
    return False, f"cổng thường ở mức {muc} ({status}) — chưa tới bước chốt"


def _tom_hoan_thien(phan: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Rút gọn bảng trách nhiệm thành độ hoàn thiện của SẢN PHẨM cổng: kết luận · mục ký/xác nhận (kèm vai) · việc hệ
    còn phải làm · cổng trước phụ thuộc. Không chép cả bảng."""
    if phan is None:
        return None
    vai: List[str] = []
    for m in phan.get("cho_nguoi") or []:
        v = str(m.get("vai") or "").strip()
        if v and v not in vai:
            vai.append(v)
    cong_truoc: List[str] = []
    for m in phan.get("cho_cong_truoc") or []:
        for g in m.get("cong") or []:
            if g not in cong_truoc:
                cong_truoc.append(str(g))
    return {
        "ket_luan": phan.get("ket_luan") or CS.KHONG_DO_DUOC,
        "vai": vai,
        "muc_ky": [str(m.get("id")) for m in phan.get("cho_nguoi") or []][:12],
        "viec_he_lam_tiep": [f"{m.get('id')}: {str(m.get('viec') or '')[:140]}"
                             for m in phan.get("agent_con_viec") or []][:8],
        "so_viec_he_lam_tiep": len(phan.get("agent_con_viec") or []),
        "cho_cong": cong_truoc,
        "ly_do": phan.get("ly_do_khong_do") if phan.get("ket_luan") == "KHONG_DO_DUOC" else None,
    }


def viec_tai_khau(gate: str, muc: str, tom: Optional[Dict[str, Any]]) -> str:
    """Một câu về SẢN PHẨM của khâu cần hoàn thiện: chưa đạt chuẩn ở đâu và hoàn thiện thế nào (không chia phần)."""
    if muc == CHUA_CHAY:
        lenh = "run_g10_assemble.py" if gate == "G10" else f"run_{gate.lower()}_auto.py"
        return f"chưa có sản phẩm — sinh bằng tools/{lenh} (các khâu trước đã khoá hoặc đã có gói ký)"
    if muc == CS.KHONG_DO_DUOC or tom is None:
        return "KHÔNG ĐO ĐƯỢC — đo lại trước khi sửa bất cứ gì"
    ket = tom["ket_luan"]
    if ket == "CHO_CONG_TRUOC":
        cho = tom.get("cho_cong_chua_khoa") or tom["cho_cong"]
        return (f"phụ thuộc cổng trước chưa khoá ({', '.join(cho) or '?'}) — khoá cổng đó theo gói ký trước, rồi "
                "hoàn thiện khâu này")
    if ket == "AGENT_XONG_CHO_NGUOI":
        nguon = f" (nguồn dữ kiện: {', '.join(tom['vai'])})" if tom["vai"] else ""
        return (f"chưa đạt chuẩn: mục {', '.join(tom['muc_ky']) or '?'} còn thiếu dữ kiện thật{nguon} — điền ở NGUỒN "
                f"của {gate} rồi kiểm lại; không sửa tài liệu của khâu sau")
    if ket == "KHONG_DO_DUOC":
        return "KHÔNG ĐO ĐƯỢC bảng trách nhiệm — đo lại trước khi sửa"
    return (f"chưa đạt chuẩn ({ket}, {tom['so_viec_he_lam_tiep']} việc) — hoàn thiện tại NGUỒN của {gate}; chỗ DUY "
            "NHẤT được sửa lúc này")


def _goi_trach_nhiem(trach_nhiem: TrachNhiem, study: str, gate: str, out_dir: Path) -> Dict[str, Any]:
    try:
        kq = trach_nhiem(study, gate, out_dir)
    except Exception as exc:  # noqa: BLE001 — không đo được bảng trách nhiệm ⇒ không bao giờ «đạt chuẩn để khoá»
        return {"ket_luan": CS.KHONG_DO_DUOC, "cho_nguoi": [], "agent_con_viec": [], "cho_cong_truoc": [],
                "ly_do_khong_do": f"{type(exc).__name__}: {str(exc)[:120]}"}
    return kq if isinstance(kq, dict) else {"ket_luan": CS.KHONG_DO_DUOC, "ly_do_khong_do": "không trả bảng"}


def _muc_khoa(gate: str, r: Dict[str, Any], tom: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Một dòng của gói ký: cổng · loại (ký/chốt) · vai · mục ký · cách khoá."""
    muc_ky = (tom or {}).get("muc_ky", [])
    if gate in cong_cung():
        nhom = list(GC._GATE_REQUIRED_STAKEHOLDERS[gate])
        goi_y = GC.required_reviewer_role_hint(gate)
        return {"gate": gate, "loai": "ky", "vai": nhom, "goi_y_vai": goi_y, "status": r["status"], "muc_ky": muc_ky,
                "cach_khoa": (f"chữ ký pháp lý của vai {'/'.join(nhom)} qua tools/approve_gate.py — không giả được; "
                              "agent không ký")}
    vai = (tom or {}).get("vai") or ["vai có thẩm quyền chốt (xem báo cáo cổng)"]
    return {"gate": gate, "loai": "chot", "vai": vai, "goi_y_vai": " / ".join(vai), "status": r["status"],
            "muc_ky": muc_ky,
            "cach_khoa": (f"xác nhận của vai {'/'.join(vai)} ở study_meta.json → gate_params.{gate} gắn dau_van_tay "
                          "nội dung hiện tại — agent không xác nhận thay")}


def phan_tich(study: str, out_dir: Path, *, cham: Optional[Cham] = None, khoa_g2: Optional[KhoaG2] = None,
              trach_nhiem: Optional[TrachNhiem] = None) -> Dict[str, Any]:
    """Phân tích chuỗi khoá G0→G10 của một đề tài (chỉ đọc). Ba bộ đo tiêm được để kiểm thử; mặc định là bộ đo thật."""
    cham = cham or _cham_that
    khoa_g2 = khoa_g2 or _khoa_g2_that
    trach_nhiem = trach_nhiem or _trach_nhiem_that
    out_dir = Path(out_dir)
    hang: List[Dict[str, Any]] = []
    for gate in CONG:  # thứ tự SỐ — mọi kết luận phía dưới dựa vào thứ tự này
        co = co_tai_lieu(out_dir, gate)
        if not co:
            song: Dict[str, Any] = {"muc": CHUA_CHAY, "status": CHUA_CHAY, "nguon": None,
                                    "ly_do": "chưa có checkpoint lẫn tài liệu của cổng"}
        else:
            try:
                song = cham(gate, study, out_dir) or {}
            except Exception as exc:  # noqa: BLE001
                song = {"muc": CS.KHONG_DO_DUOC, "status": CS.KHONG_DO_DUOC, "nguon": CS.NGUON_LOI,
                        "ly_do": f"chấm sống hỏng: {type(exc).__name__}: {str(exc)[:120]}"}
        muc = CHUA_CHAY if not co else _muc_chuan(song)
        khoa, ly_khoa = _da_khoa(gate, muc, study, out_dir, khoa_g2)
        hang.append({"gate": gate, "cung": gate in cong_cung(), "muc": muc,
                     "status": str(song.get("status") or muc), "nguon": song.get("nguon"),
                     "ly_do_cham": song.get("ly_do"), "co_tai_lieu": co, "da_khoa": khoa, "ly_do_khoa": ly_khoa,
                     "khong_do": muc == CS.KHONG_DO_DUOC or khoa is None, "vi_tri": None, "ghi_chu": None,
                     "hoan_thien": None})

    i_mo = next((i for i, r in enumerate(hang) if r["da_khoa"] is not True), None)
    for r in hang[: i_mo if i_mo is not None else len(hang)]:
        r["vi_tri"] = DA_KHOA
    danh_sach: List[Dict[str, Any]] = []
    i_chan: Optional[int] = None
    if i_mo is not None:
        for i in range(i_mo, len(hang)):
            r = hang[i]
            if r["da_khoa"] is True:
                r["vi_tri"] = KHOA_NGOAI_THU_TU
                r["ghi_chu"] = GHI_CHU_KHOA_NGOAI_THU_TU
                continue
            dat_muc, ly_muc = _muc_cho_phep_khoa(r["gate"], r["muc"], r["status"])
            tom = None
            if r["muc"] not in (CHUA_CHAY, CS.KHONG_DO_DUOC):
                tom = _tom_hoan_thien(_goi_trach_nhiem(trach_nhiem, study, r["gate"], out_dir))
                r["hoan_thien"] = tom
            if dat_muc and tom is not None and tom["ket_luan"] == CS.KHONG_DO_DUOC:
                r["khong_do"] = True  # đúng mức để khoá mà không đo được bảng trách nhiệm ⇒ không tuyên «đạt chuẩn»
            if dat_muc and tom is not None and tom["ket_luan"] in _HOAN_THIEN_MA_0:
                r["vi_tri"] = CHO_KY
                r["ghi_chu"] = f"đạt chuẩn để khoá ({ly_muc}; {tom['ket_luan']}) — gói ký đã chuẩn bị"
                danh_sach.append({"thu_tu": len(danh_sach) + 1, **_muc_khoa(r["gate"], r, tom)})
                continue
            i_chan = i
            r["vi_tri"] = KHAU_CAN_HOAN_THIEN
            if tom is not None:
                tom["cho_cong_chua_khoa"] = [g for g in tom["cho_cong"]
                                             if not any(x["gate"] == g and x["da_khoa"] is True for x in hang)]
            r["ghi_chu"] = f"{ly_muc} — {viec_tai_khau(r['gate'], r['muc'], tom)}"
            break
    if i_chan is not None:
        for r in hang[i_chan + 1:]:
            if r["da_khoa"] is True:
                r["vi_tri"] = KHOA_NGOAI_THU_TU
                r["ghi_chu"] = GHI_CHU_KHOA_NGOAI_THU_TU
            elif r["co_tai_lieu"]:
                r["vi_tri"] = CHUA_LAM_TIEP
                r["ghi_chu"] = GHI_CHU_CHUA_LAM_TIEP
            else:
                r["vi_tri"] = CHUA_TOI_LUOT
                r["ghi_chu"] = "chưa tới lượt — chưa có tài liệu"

    cuoi = i_chan if i_chan is not None else (len(hang) - 1)
    duong_quyet_dinh = hang[: cuoi + 1] if i_mo is not None else []
    if i_mo is None:
        ma = 0
    elif any(r["khong_do"] for r in duong_quyet_dinh):
        ma = 2
    else:
        ma = 1
    khau_mo = hang[i_mo]["gate"] if i_mo is not None else None
    khau_ht = hang[i_chan] if i_chan is not None else None
    return {
        "schema": SCHEMA, "study": study, "thu_muc": str(out_dir),
        "khau_dang_mo": khau_mo,
        "khau_can_hoan_thien": khau_ht["gate"] if khau_ht else None,
        "danh_sach_khoa": danh_sach,
        "khoa_ngoai_thu_tu": [r["gate"] for r in hang if r["vi_tri"] == KHOA_NGOAI_THU_TU],
        "chua_lam_tiep": [r["gate"] for r in hang if r["vi_tri"] == CHUA_LAM_TIEP],
        "cong_cung": list(cong_cung()),
        "cong": hang,
        "ma_thoat": ma,
        "ket_luan": _ket_luan(ma, khau_mo, khau_ht, danh_sach),
        "luu_y": "Chỉ đọc — không ghi tệp, không ký, không đổi cờ. Cần bác sĩ kiểm chứng.",
    }


def _ket_luan(ma: int, khau_mo: Optional[str], khau_ht: Optional[Dict[str, Any]],
              danh_sach: List[Dict[str, Any]]) -> str:
    if ma == 0:
        return "Mọi khâu G0→G10 đã khoá."
    phan = []
    if khau_mo:
        phan.append(f"Khâu đang mở: {khau_mo}.")
    if danh_sach:
        phan.append("Gói ký — khoá theo thứ tự: " + " → ".join(m["gate"] for m in danh_sach) + ".")
    if khau_ht:
        phan.append(f"Khâu cần hoàn thiện (chỗ duy nhất được sửa): {khau_ht['gate']} ({khau_ht['status']}).")
    if ma == 2:
        phan.append("CÓ chỗ KHÔNG ĐO ĐƯỢC trên đường quyết định — không phải «đã khoá».")
    return " ".join(phan)


# ───────────────────────────────────────────────────────────────────────────── trình bày
_NHAN_VI_TRI = {
    DA_KHOA: "✅ đã khoá",
    CHO_KY: "🟢 đạt chuẩn — gói ký đã chuẩn bị",
    KHAU_CAN_HOAN_THIEN: "🛠 KHÂU CẦN HOÀN THIỆN",
    KHOA_NGOAI_THU_TU: "🔒 đã khoá ngoài thứ tự",
    CHUA_LAM_TIEP: f"⏸ {GHI_CHU_CHUA_LAM_TIEP}",
    CHUA_TOI_LUOT: "· chưa tới lượt (chưa có tài liệu)",
}


def in_bao_cao(kq: Dict[str, Any]) -> str:
    """Bản người đọc (tiếng Việt)."""
    study = kq["study"]
    dong = [f"KHÂU ĐANG MỞ — {study}", "(chỉ đọc · chấm sống G0→G10 bằng cong_song.trang_thai_song · không ghi, "
            "không ký, không đổi cờ)", ""]
    for r in kq["cong"]:
        nhan = _NHAN_VI_TRI.get(r["vi_tri"], "?")
        if r["gate"] == kq["khau_dang_mo"]:
            nhan = f"🔓 KHÂU ĐANG MỞ · {nhan}"
        cung = " [cứng]" if r["cung"] else ""
        them = f" — {r['ghi_chu']}" if r["ghi_chu"] and r["vi_tri"] in (CHO_KY, KHAU_CAN_HOAN_THIEN) else ""
        if r["khong_do"]:
            them += f" — ⚪ KHÔNG ĐO ĐƯỢC: {r['ly_do_khoa'] if r['da_khoa'] is None else r['ly_do_cham']}"
        dong.append(f"  {r['gate']:<4}{cung:<8} {nhan} · {r['status']}{them}")
    dong.append("")
    if kq["ma_thoat"] == 0:
        dong.append("Mọi khâu đã khoá.")
    else:
        dong.append(f"KHÂU ĐANG MỞ: {kq['khau_dang_mo']}")
        if kq["danh_sach_khoa"]:
            dong.append("GÓI KÝ ĐÃ CHUẨN BỊ — DANH SÁCH KHOÁ THEO THỨ TỰ (ký/chốt một lượt, đúng thứ tự):")
            for m in kq["danh_sach_khoa"]:
                loai = "KÝ" if m["loai"] == "ky" else "CHỐT"
                muc = f" · mục ký: {', '.join(m['muc_ky'])}" if m["muc_ky"] else ""
                dong.append(f"  {m['thu_tu']}. {m['gate']} — {loai} · vai: {m['goi_y_vai']} · {m['status']}{muc}")
                dong.append(f"     cách khoá: {m['cach_khoa']}")
        else:
            dong.append("GÓI KÝ: chưa có — chưa cổng nào ở khâu mở đạt chuẩn để khoá; hoàn thiện khâu dưới đây trước.")
        ht = next((r for r in kq["cong"] if r["vi_tri"] == KHAU_CAN_HOAN_THIEN), None)
        if ht:
            g = ht["gate"]
            pa = ht.get("hoan_thien")
            dong.append(f"KHÂU CẦN HOÀN THIỆN: {g} ({ht['status']}) — {viec_tai_khau(g, ht['muc'], pa)}.")
            if pa:
                cho = pa.get("cho_cong_chua_khoa", pa["cho_cong"])
                dong.append(f"  độ hoàn thiện: {pa['ket_luan']}"
                            + (f" · phụ thuộc cổng chưa khoá: {', '.join(cho)}" if cho else ""))
                for v in pa["viec_he_lam_tiep"][:5]:
                    dong.append(f"    · {v}")
            if not pa or pa["ket_luan"] != "CHO_CONG_TRUOC":
                dong.append(f"  sửa/điền tại NGUỒN của {g} → kiểm: python tools/{g.lower()}_quality_gate.py --study "
                            f"{study} --no-write · python tools/nhat_quan_xuyen_cong.py --study {study} → khoá → mới "
                            "làm khâu sau.")
        if kq["chua_lam_tiep"]:
            dong.append(f"CHƯA ĐƯỢC LÀM TIẾP: {', '.join(kq['chua_lam_tiep'])} — {GHI_CHU_CHUA_LAM_TIEP}.")
        if kq["khoa_ngoai_thu_tu"]:
            dong.append(f"ĐÃ KHOÁ NGOÀI THỨ TỰ: {', '.join(kq['khoa_ngoai_thu_tu'])} — giữ nguyên; sửa khâu trước "
                        "làm đổi nguồn thì phải kiểm và khoá lại.")
        if kq["ma_thoat"] == 2:
            dong.append("⚪ CÓ CHỖ KHÔNG ĐO ĐƯỢC trên đường quyết định — «không đo được» KHÔNG phải «đã khoá».")
    dong += ["", "Nguyên tắc: chỉ chuyển sang bước tiếp theo khi bước hiện tại đã đạt chuẩn xác định trước — lỗi ở "
             "khâu nào sửa ở NGUỒN của khâu đó → kiểm bằng chốt của chính nó → khoá → mới sinh lại khâu sau.",
             "Cần bác sĩ kiểm chứng."]
    return "\n".join(dong)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Khâu nào của đề tài đang mở (chỉ đọc) — chuỗi khoá G0→G10.")
    ap.add_argument("--study", required=True, help="mã đề tài (thư mục exports/<mã>)")
    ap.add_argument("--json", action="store_true", help="in JSON máy đọc")
    ap.add_argument("--goc", default=None, help="thư mục chứa exports/ (mặc định: gốc repo này)")
    try:
        args = ap.parse_args(argv)
    except SystemExit as exc:
        return 0 if exc.code == 0 else 3
    if not _MA_DE_TAI.match(args.study or ""):
        print(f"❌ mã đề tài không hợp lệ: {args.study!r}", file=sys.stderr)
        return 3
    goc = Path(args.goc).expanduser().resolve() if args.goc else BASE
    out_dir = goc / "exports" / args.study
    if not out_dir.is_dir():
        print(f"❌ không thấy thư mục đề tài: {out_dir}", file=sys.stderr)
        return 3
    kq = phan_tich(args.study, out_dir)
    if args.json:
        print(json.dumps(kq, ensure_ascii=False, indent=2, default=str))
    else:
        print(in_bao_cao(kq))
    return int(kq["ma_thoat"])


if __name__ == "__main__":
    import moi_truong_venv as _MV  # bảo đảm Python đủ thư viện: thiếu ⇒ chạy lại bằng ~/.ebm-venv

    _MV.dam_bao_moi_truong(__file__)
    sys.exit(main())
