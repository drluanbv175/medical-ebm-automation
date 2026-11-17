#!/usr/bin/env python3
"""Cổng CI của giả lập trọn vòng 16 kịch bản: mỗi kịch bản phải khoá được gói G10, 0 ô lỗi máy, đề cương nộp đạt.

VÌ SAO (17/11/2026, bác sĩ: «đưa 16 kịch bản vào CI»): bài kiểm `test_gia_lap_tron_vong*` là bài MÔ TẢ — nó «passed» cả
khi G10 bị chặn (nó ghi báo cáo cho người đọc, không phán). Trước đây «16/16 khoá gói G10» chỉ là con số đọc tay sau mỗi
lượt chạy; một thay đổi mã làm vỡ một kịch bản vẫn qua CI xanh. Công cụ này đọc báo cáo
`state/gia-lap-tron-vong/<kịch bản>.json` và trả mã khác 0 khi bất kỳ kịch bản nào trượt — để CI đỏ đúng chỗ.

Mã thoát: 0 mọi kịch bản đạt · 1 có kịch bản trượt/thiếu báo cáo · 3 tham số sai.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

REPO = Path(__file__).resolve().parents[1]
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# tên nút kiểm thử (đối số của chay_8_thiet_ke) → tên tệp báo cáo
KICH_BAN = {
    "rct": "rct_nhi_phan", "cross_sectional": "cat_ngang_mo_ta", "cohort": "thuan_tap_phoi_nhiem",
    "case_control": "benh_chung", "diagnostic": "chan_doan", "prediction": "mo_hinh_du_bao", "sr_ma": "tong_quan_gop",
    "qualitative": "dinh_tinh", "rct_ni": "rct_khong_kem", "rct_cum": "rct_cum", "cohort_cox": "thuan_tap_song_con",
    "cohort_mi": "thuan_tap_mi", "rct_rut_bai": "rct_rut_bai", "cohort_vong_sua": "thuan_tap_vong_sua",
    "rct_kinh_te": "rct_kinh_te", "rct_hon_hop": "rct_hon_hop",
}
# 17/11/2026 — kịch bản CHÂN THỰC (gia_lap_chan_thuc): cùng cổng phán + ước lượng chính phải tìm lại tham số thật.
CHAN_THUC = {f"{t}_chan_thuc": f"{t}_chan_thuc" for t in ("rct", "cross_sectional", "cohort", "case_control",
                                                          "diagnostic", "prediction", "sr_ma", "qualitative")}


def kiem_mot(p: Path) -> List[str]:
    """Lý do trượt của MỘT báo cáo (rỗng = đạt)."""
    if not p.is_file():
        return ["thiếu báo cáo (kịch bản không chạy tới cuối)"]
    try:
        j: Dict[str, Any] = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return [f"báo cáo hỏng: {exc}"]
    loi = []
    g10 = ((j.get("cong") or {}).get("G10") or {})
    if not str(g10.get("trang_thai") or "").startswith("PASS_G10"):
        loi.append(f"G10 = {g10.get('trang_thai')} {g10.get('chua_dat') or ''}".strip())
    if j.get("so_o_loi_may") not in (0, None) or j.get("so_o_loi_may") is None:
        loi.append(f"ô lỗi máy = {j.get('so_o_loi_may')}")
    dc = ((j.get("du_lieu") or {}).get("de_cuong_nop") or {})
    if dc.get("ma") != 0:
        loi.append(f"đề cương nộp mã {dc.get('ma')}: {'; '.join(map(str, dc.get('loi') or []))[:200]}")
    cx = j.get("chinh_xac") or {}
    if cx.get("ket") in ("SAI", "CHUA_DO"):  # CHUA_DO chỉ xảy ra khi kịch bản có khai phép kiểm mà không đo được
        loi.append(f"độ chính xác {cx.get('ket')}: {cx.get('lay')} thật {cx.get('that')} · ước lượng {cx.get('uoc')} "
                   f"KTC {cx.get('ci_95')} {cx.get('loi') or ''}".strip())
    return loi


def _cx(p: Path) -> str:
    try:
        cx = json.loads(p.read_text(encoding="utf-8")).get("chinh_xac") or {}
    except (OSError, ValueError):
        return ""
    if cx.get("ket") in (None, "KHONG_AP_DUNG"):
        return ""
    return (f" · chính xác {cx['ket']} ({cx.get('lay')}: thật {cx.get('that')}, ước lượng {cx.get('uoc')} "
            f"{cx.get('ci_95')})")


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--thu-muc", default=str(REPO / "state" / "gia-lap-tron-vong"))
    ap.add_argument("--kich-ban", nargs="*", help="tên nút (vd rct cohort); mặc định cả 16")
    ap.add_argument("--chan-thuc", action="store_true", help="phán 8 kịch bản chân thực thay cho 16 kịch bản")
    a = ap.parse_args(argv)
    bang = CHAN_THUC if a.chan_thuc else {**KICH_BAN, **CHAN_THUC}
    ten = a.kich_ban or list(CHAN_THUC if a.chan_thuc else KICH_BAN)
    la = [t for t in ten if t not in bang]
    if la:
        print(f"❌ kịch bản lạ: {la}")
        return 3
    truot = 0
    for t in ten:
        loi = kiem_mot(Path(a.thu_muc) / f"{bang[t]}.json")
        truot += bool(loi)
        tep = Path(a.thu_muc) / f"{bang[t]}.json"
        ket = "; ".join(loi) if loi else "khoá gói G10 · 0 ô lỗi máy · đề cương nộp đạt" + _cx(tep)
        print(f"{'✅' if not loi else '⛔'} {t:16} {ket}")
    print(f"KẾT: {len(ten) - truot}/{len(ten)} kịch bản đạt.")
    return 1 if truot else 0


if __name__ == "__main__":
    sys.exit(main())
