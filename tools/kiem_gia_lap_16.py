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
    "rct_kinh_te": "rct_kinh_te", "rct_hon_hop": "rct_hon_hop", "case_control_ghep_cap": "benh_chung_ghep_cap",
    "case_control_ghep_cap_thieu": "benh_chung_ghep_cap_thieu",
    "case_control_ghep_cap_hiem": "benh_chung_ghep_cap_hiem",
    # 23/11/2026 — PLS-SEM: khảo sát cắt ngang có cấu trúc tiềm ẩn (seminr chính + cSEM kiểm chéo; job CI cài R)
    "cross_sectional_pls_sem": "cat_ngang_pls_sem",
}
# 17/11/2026 — kịch bản CHÂN THỰC (gia_lap_chan_thuc): cùng cổng phán + ước lượng chính phải tìm lại tham số thật.
CHAN_THUC = {f"{t}_chan_thuc": f"{t}_chan_thuc" for t in ("rct", "cross_sectional", "cohort", "case_control",
                                                          "diagnostic", "prediction", "sr_ma", "qualitative")}


def kiem_chuan_bao_cao(j: Dict[str, Any]) -> List[str]:
    """Lý do trượt về chuẩn báo cáo theo mục (K18) của bản thảo G7 và báo cáo tổng hợp nghiệm thu.

    22/11/2026 (bác sĩ: «ghi nhỏ sổ nợ sẽ không ghi sổ nợ nữa, giải quyết theo nguyên tắc»): KHÔNG có sổ nợ, miễn trừ
    hay bánh cóc. Mọi kịch bản có giả lập tới G7 phải đạt ĐỦ mục chuẩn áp dụng; thiếu bất kỳ mục nào ⇒ trượt; chưa đo
    được ⇒ trượt (không bao giờ coi «không đo được» là đạt). Mục không áp dụng cho thiết kế do điều kiện của chính
    tiêu chí K18 quyết, không do danh sách tay."""
    cb = j.get("chuan_bao_cao")
    if not isinstance(cb, dict) or cb.get("loi") or "bao_cao_thieu" not in cb or "ban_thao_thieu" not in cb:
        return [f"chuẩn báo cáo theo mục CHƯA ĐO: {(cb or {}).get('loi') if isinstance(cb, dict) else 'thiếu khoá'}"]
    loi = []
    for loai, ten in (("ban_thao", "bản thảo"), ("bao_cao", "báo cáo tổng hợp")):
        thieu = sorted(set(cb.get(f"{loai}_thieu") or []))
        if thieu:
            loi.append(f"{ten} thiếu mục chuẩn báo cáo: {', '.join(thieu)}")
    if cb.get("bao_cao_cau_truc"):
        loi.append(f"cấu trúc báo cáo tổng hợp: {'; '.join(map(str, cb['bao_cao_cau_truc']))[:200]}")
    return loi


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
    # 22/11/2026 (kiểm toàn hệ 11 khâu): khâu 9–10 trước đây không có ở cổng phán — 22/24 kịch bản thiếu hình bắt buộc
    # của chuẩn báo cáo (sơ đồ luồng) và bản diễn giải không bàn hạn chế/khái quát theo chuẩn mà CI vẫn xanh.
    g6 = ((j.get("du_lieu") or {}).get("g6") or {})
    bd = g6.get("bieu_do")
    if "khong_tu_dong" not in g6:
        if not isinstance(bd, dict) or not bd.get("co_tep"):
            loi.append("G6 không có G6_bieu_do.json — biểu đồ kết quả chưa sinh")
        else:
            if bd.get("loi"):
                loi.append(f"biểu đồ LỖI: {str(bd.get('loi'))[:200]}")
            if bd.get("thieu_bat_buoc"):
                loi.append(f"thiếu hình bắt buộc theo chuẩn báo cáo: {', '.join(map(str, bd['thieu_bat_buoc']))}")
    # 22/11/2026 (bác sĩ: «tất cả phải đúng chuẩn»): mọi văn bản đề tài đạt luật trình bày số đo K11
    sd = j.get("so_do_sai") or []
    if sd:
        loi.append(f"trình bày số đo sai chuẩn ở {len(sd)} chỗ: {' | '.join(map(str, sd[:4]))[:400]}")
    g65 = ((j.get("cong") or {}).get("G6_5") or {})
    if g65 and g65.get("trang_thai") != "DAT":
        loi.append(f"bản diễn giải G6.5 = {g65.get('trang_thai')}: {'; '.join(map(str, g65.get('loi') or []))[:200]}")
    loi += kiem_chuan_bao_cao(j)
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
