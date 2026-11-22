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


#: Sổ nợ chuẩn báo cáo theo mục (K18) của bản thảo và báo cáo tổng hợp — BÁNH CÓC (22/11/2026): mục còn thiếu đã
#: biết, có lý do; mục MỚI thiếu ⇒ CI đỏ (lùi chuẩn); mục trong sổ mà nay đạt ⇒ CI đỏ, đòi rút khỏi sổ (sổ chỉ giảm).
#: Kịch bản không có trong sổ thì chỉ in số đo, chưa phán.
SO_NO_K18 = REPO / "tests" / "fixtures" / "gia_lap_k18_so_no.json"


def _doc_so_no() -> Dict[str, Any]:
    try:
        return json.loads(SO_NO_K18.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def kiem_chuan_bao_cao(ten_bao_cao: str, j: Dict[str, Any], so_no: Optional[Dict[str, Any]] = None) -> List[str]:
    """Lý do trượt về chuẩn báo cáo theo mục (K18) của bản thảo + báo cáo tổng hợp so với sổ nợ bánh cóc."""
    so_no = _doc_so_no() if so_no is None else so_no
    no = (so_no.get("kich_ban") or {}).get(ten_bao_cao)
    if no is None:
        return []
    cb = j.get("chuan_bao_cao")
    if not isinstance(cb, dict) or cb.get("loi") or "bao_cao_thieu" not in cb:
        return [f"chuẩn báo cáo theo mục CHƯA ĐO: {(cb or {}).get('loi') if isinstance(cb, dict) else 'thiếu khoá'}"]
    loi = []
    for loai, ten in (("ban_thao", "bản thảo"), ("bao_cao", "báo cáo tổng hợp")):
        do, cho = set(cb.get(f"{loai}_thieu") or []), set(no.get(loai) or [])
        if do - cho:
            loi.append(f"{ten} LÙI chuẩn — mục mới thiếu: {', '.join(sorted(do - cho))}")
        if cho - do:
            loi.append(f"{ten} đã đạt thêm {', '.join(sorted(cho - do))} — rút khỏi sổ nợ {SO_NO_K18.name}")
    if cb.get("bao_cao_cau_truc"):
        loi.append(f"cấu trúc báo cáo tổng hợp: {'; '.join(map(str, cb['bao_cao_cau_truc']))[:200]}")
    return loi


def ghi_so_no(thu_muc: Path, ten: Sequence[str], cho_them: bool = False) -> int:
    """Ghi lại sổ nợ K18 từ báo cáo kịch bản vừa chạy. Mục MỚI chỉ được thêm khi ``cho_them`` (mặc định từ chối)."""
    so = _doc_so_no() or {"kich_ban": {}}
    kb = so.setdefault("kich_ban", {})
    them_moi: List[str] = []
    for t in ten:
        bang = {**KICH_BAN, **CHAN_THUC}
        if t not in bang:
            print(f"❌ kịch bản lạ: {t}")
            return 3
        try:
            cb = json.loads((thu_muc / f"{bang[t]}.json").read_text(encoding="utf-8")).get("chuan_bao_cao") or {}
        except (OSError, ValueError) as exc:
            print(f"❌ {t}: không đọc được báo cáo ({exc})")
            return 1
        if cb.get("loi") or "bao_cao_thieu" not in cb:
            print(f"❌ {t}: chuẩn báo cáo chưa đo — {cb.get('loi')}")
            return 1
        moi = {"ban_thao": sorted(cb.get("ban_thao_thieu") or []), "bao_cao": sorted(cb.get("bao_cao_thieu") or [])}
        cu = kb.get(bang[t])
        if cu is not None:
            them_moi += [f"{t}/{loai}: {m}" for loai in moi for m in set(moi[loai]) - set(cu.get(loai) or [])]
        kb[bang[t]] = moi
    if them_moi and not cho_them:
        print("❌ sổ nợ chỉ được GIẢM — mục mới thiếu:\n  " + "\n  ".join(them_moi)
              + "\n(dùng --cho-them nếu có lý do)")
        return 1
    tam = SO_NO_K18.with_suffix(".tam")
    tam.write_text(json.dumps(so, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    tam.replace(SO_NO_K18)
    print(f"✅ đã ghi sổ nợ {SO_NO_K18.name} cho {len(ten)} kịch bản.")
    return 0


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
    loi += kiem_chuan_bao_cao(p.stem, j)
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
    ap.add_argument("--ghi-so-no", action="store_true",
                    help="ghi số đo chuẩn báo cáo theo mục hiện tại vào sổ nợ (chỉ được GIẢM; thêm mục cần --cho-them)")
    ap.add_argument("--cho-them", action="store_true", help="cho phép sổ nợ THÊM mục (phải nêu lý do trong commit)")
    a = ap.parse_args(argv)
    if a.ghi_so_no:
        return ghi_so_no(Path(a.thu_muc), a.kich_ban or list(KICH_BAN), cho_them=a.cho_them)
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
