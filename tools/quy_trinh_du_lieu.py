#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""QUY TRÌNH THU THẬP · NHẬP LIỆU · LƯU TRỮ đã chốt ↔ đề cương ↔ hồ sơ đạo đức (G2) ↔ kế hoạch quản lý dữ liệu (G5).

Vì sao (giai đoạn 5 «Công cụ & phương pháp thu thập», bác sĩ 15/11/2026: «đảm bảo sự đồng bộ xuyên suốt và chính xác
nhất»): kiểm tay C1a — đề cương nộp và phiếu thông tin/đồng thuận G2 đã chốt «lưu 2 năm rồi hủy», «bảng đối chiếu HIS
hủy trong 30 ngày», «nhập kép toàn bộ phiếu», «hai người ngoài khoa mã hoá câu hỏi mở», nhưng kế hoạch quản lý dữ
liệu G5
(tài liệu VẬN HÀNH lúc thu thập và khoá dữ liệu) chỉ có khuôn chung — kể cả câu «không dùng một thời hạn cứng cho mọi đề
tài». Không công cụ nào nối quy trình đã hứa với người tham gia/Hội đồng với tài liệu người làm dữ liệu cầm.

Tệp `exports/<mã>/_quy-trinh-du-lieu.csv` (UTF-8, có/không BOM), mỗi dòng một quyết định đã chốt:

  muc            thu_thap · an_danh · nhap_lieu · kiem_chung · ghep_du_lieu · huy_bang_noi · luu_tru · huy_du_lieu ·
                 ma_hoa_cau_mo · khac
  gia_tri        quyết định (câu ngắn); chưa có quyết định ⇒ «[CẦN PI QUYẾT …]» — máy KHÔNG điền thay
  nguon          nơi quyết định được chốt (vd «đề cương nộp 6.5», «G1 data_collection_method», «SOP trích hồ sơ §7»)
  neo_de_cuong   cụm chữ NGUYÊN VĂN trong đề cương nộp (bỏ trống ⇒ không đòi)
  neo_g2         cụm chữ NGUYÊN VĂN trong gói đạo đức G2 (bỏ trống ⇒ không đòi, TRỪ mục hứa với người tham gia)
  ghi_chu        tự do

Luật (`loi` ⇒ trục `quy_trinh_du_lieu` LỆCH MỀM; `mau_thuan` ⇒ LỆCH CỨNG; `canh_bao` ⇒ CẦN XEM; không có tệp ⇒ CHƯA ĐỦ):
  QT-01 thiếu cột · QT-02 thiếu mục bắt buộc / mục lạ · QT-03 (cảnh báo) quyết định còn «[CẦN …]»
  QT-04 neo đề cương không có trong đề cương nộp · QT-05 neo G2 không có trong gói G2, hoặc mục hứa với người tham gia
  (ẩn danh, lưu trữ, huỷ bảng nối) thiếu neo G2 khi đã có gói G2 · QT-06 DMP G5 đã có mà không mang quyết định
(`gia_tri`)
  QT-07 (mâu thuẫn) số năm lưu trữ / số ngày huỷ bảng nối ở đề cương, G2 hoặc G5 khác quyết định đã chốt
Chỉ ĐỌC và BÁO; `khoi_dmp`/`dong_luu_tru` để run_g5_auto in đúng quy trình của đề tài vào DMP.

Lệnh:
  python tools/quy_trinh_du_lieu.py kiem --study <mã> [--json]   mã 0 ĐẠT · 1 CHƯA ĐẠT/MÂU THUẪN · 2 KHÔNG CÓ

Cần bác sĩ kiểm chứng.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

try:  # stdout UTF-8 trên Windows
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
except (AttributeError, ValueError):
    pass

BASE = Path(__file__).resolve().parent.parent

TEP = "_quy-trinh-du-lieu.csv"
COT = ("muc", "gia_tri", "nguon", "neo_de_cuong", "neo_g2", "ghi_chu")
COT_BAT_BUOC = ("muc", "gia_tri", "nguon")
NHAN = {"thu_thap": "Cách thu thập", "an_danh": "Ẩn danh / định danh", "nhap_lieu": "Nhập liệu",
        "kiem_chung": "Kiểm chứng chất lượng thu thập", "ghep_du_lieu": "Ghép dữ liệu từ nguồn khác",
        "huy_bang_noi": "Bảng nối / đối chiếu mã", "luu_tru": "Thời hạn lưu trữ", "huy_du_lieu": "Hủy dữ liệu",
        "ma_hoa_cau_mo": "Mã hoá câu hỏi mở", "khac": "Khác"}
MUC_BAT_BUOC = ("thu_thap", "an_danh", "nhap_lieu", "luu_tru", "huy_du_lieu")
HUA_NGUOI_THAM_GIA = ("an_danh", "luu_tru", "huy_bang_noi")

TRANG_THAI_DAT = "DAT"
TRANG_THAI_CHUA_DAT = "CHUA_DAT"
TRANG_THAI_KHONG_CO = "KHONG_CO"

_CAN = re.compile(r"\[\s*C[ẦA]N", re.I)
_NAM = re.compile(r"l[ưu]u(?:\s+trữ|\s+giữ)?[^.\n]{0,40}?(\d+)\s*năm", re.I)
_NGAY_HUY = re.compile(r"b[ảa]ng\s+(?:đối chiếu|đ[ốo]i\s+chi[ếe]u|n[ốo]i|gh[ée]p)[^.\n]{0,80}?(\d+)\s*ngày", re.I)


def _nfc(s: Any) -> str:
    return unicodedata.normalize("NFC", str(s or "")).strip()


def doc_bang(out_dir: Path) -> Tuple[Optional[List[Dict[str, str]]], Optional[List[str]], Optional[str]]:
    p = out_dir / TEP
    if not p.is_file():
        return None, None, None
    try:
        with p.open(encoding="utf-8-sig", newline="") as f:
            r = csv.DictReader(f)
            return [{k: _nfc(v) for k, v in row.items() if k} for row in r], list(r.fieldnames or []), None
    except (OSError, csv.Error, UnicodeDecodeError) as e:
        return None, None, f"{type(e).__name__}: {e}"


def _van_ban(p: Path) -> Optional[str]:
    try:
        return unicodedata.normalize("NFC", p.read_text(encoding="utf-8"))
    except OSError:
        return None


def theo_muc(dong: Sequence[Mapping[str, str]]) -> Dict[str, List[Mapping[str, str]]]:
    ra: Dict[str, List[Mapping[str, str]]] = {}
    for r in dong:
        ra.setdefault(r.get("muc", ""), []).append(r)
    return ra


def khoi_dmp(dong: Sequence[Mapping[str, str]]) -> List[str]:
    """Khối «PHẦN 1B» của DMP G5 — in NGUYÊN quyết định đã chốt (QT-06 đối chiếu đúng chuỗi này)."""
    ra = ["## PHẦN 1B — QUY TRÌNH THU THẬP, NHẬP LIỆU VÀ LƯU TRỮ (đã chốt — `_quy-trinh-du-lieu.csv`)", "",
          "> Lấy nguyên văn quyết định đã chốt ở đề cương/G1/SOP; sửa quy trình thì sửa nguồn rồi sửa bảng, không sửa "
          "tay khối này.", ""]
    for muc in NHAN:
        for r in dong:
            if r.get("muc") == muc:
                ra.append(f"- **{NHAN[muc]}:** {r.get('gia_tri', '')} _(nguồn: {r.get('nguon', '') or '—'})_")
    return ra + ["", "---", ""]


def dong_luu_tru(dong: Sequence[Mapping[str, str]]) -> Optional[str]:
    """Dòng «Lưu trữ/hủy» của PHẦN 7B khi đã chốt (None ⇒ bộ sinh giữ câu khuôn chung)."""
    m = theo_muc(dong)
    luu = [r["gia_tri"] for r in m.get("luu_tru", []) if r.get("gia_tri") and not _CAN.search(r["gia_tri"])]
    huy = [r["gia_tri"] for r in m.get("huy_du_lieu", []) if r.get("gia_tri") and not _CAN.search(r["gia_tri"])]
    if not luu:
        return None
    return "- **Lưu trữ/hủy (đã chốt — `_quy-trinh-du-lieu.csv`):** " + "; ".join(luu + huy) + "."


def _vd(ma: str, muc: str, noi_dung: str) -> Dict[str, str]:
    return {"ma": ma, "muc": muc, "noi_dung": noi_dung}


def kiem(out_dir: Path, study: str, *, meta: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    """Chấm bảng quy trình. Trả {trang_thai, tom_tat, loi[], canh_bao[], mau_thuan[], so_dong}."""
    dong, cot, loi_doc = doc_bang(out_dir)
    if loi_doc:
        return {"trang_thai": TRANG_THAI_KHONG_CO, "tom_tat": f"không đọc được {TEP}: {loi_doc}",
                "loi": [_vd("QT-01", "loi", loi_doc)], "canh_bao": [], "mau_thuan": [], "so_dong": 0}
    if dong is None:
        return {"trang_thai": TRANG_THAI_KHONG_CO, "tom_tat": f"chưa có {TEP}", "loi": [], "canh_bao": [],
                "mau_thuan": [], "so_dong": 0}
    loi: List[Dict[str, str]] = []
    cb: List[Dict[str, str]] = []
    mt: List[Dict[str, str]] = []
    thieu_cot = [c for c in COT_BAT_BUOC if c not in (cot or [])]
    if thieu_cot:
        return _ket([_vd("QT-01", "loi", f"thiếu cột {', '.join(thieu_cot)}")], cb, mt, dong)
    m = theo_muc(dong)
    for muc in sorted(set(m) - set(NHAN)):
        loi.append(_vd("QT-02", "loi", f"mục lạ «{muc}» (hợp lệ: {', '.join(NHAN)})"))
    for muc in MUC_BAT_BUOC:
        if muc not in m:
            loi.append(_vd("QT-02", "loi", f"thiếu mục bắt buộc «{muc}» ({NHAN[muc]})"))
    dc = _van_ban(out_dir / f"DE_CUONG_NOP_HOI_DONG_{study}.md")
    g2 = _van_ban(out_dir / f"G2_A3_ETHICS_PACKAGE_{study}.md")
    g5 = _van_ban(out_dir / f"G5_A6_DATA_MGMT_{study}.md")
    for r in dong:
        muc, gt = r.get("muc", ""), r.get("gia_tri", "")
        if not gt or _CAN.search(gt):
            cb.append(_vd("QT-03", "canh_bao", f"«{muc}»: chưa có quyết định ({gt or 'trống'}) — PI chốt"))
            continue
        neo_dc, neo_g2 = r.get("neo_de_cuong", ""), r.get("neo_g2", "")
        if neo_dc and dc is not None and neo_dc.casefold() not in dc.casefold():
            loi.append(_vd("QT-04", "loi", f"«{muc}»: đề cương nộp không có «{neo_dc}»"))
        if g2 is not None:
            if neo_g2 and neo_g2.casefold() not in g2.casefold():
                loi.append(_vd("QT-05", "loi", f"«{muc}»: gói đạo đức G2 không có «{neo_g2}»"))
            elif not neo_g2 and muc in HUA_NGUOI_THAM_GIA:
                loi.append(_vd("QT-05", "loi", f"«{muc}» là điều hứa với người tham gia nhưng chưa khai neo trong gói "
                                               "G2 (neo_g2)"))
        if g5 is not None and gt.casefold() not in g5.casefold():
            loi.append(_vd("QT-06", "loi", f"«{muc}»: kế hoạch quản lý dữ liệu G5 chưa mang quyết định «{gt[:80]}»"))
    # QT-07 — số năm lưu trữ, số ngày hủy bảng nối mâu thuẫn giữa các tài liệu
    for muc, rx, don_vi in (("luu_tru", _NAM, "năm"), ("huy_bang_noi", _NGAY_HUY, "ngày")):
        so_chot = {s for r in m.get(muc, []) for s in rx.findall(r.get("gia_tri", ""))}
        if len(so_chot) != 1:
            continue
        chot = next(iter(so_chot))
        for ten, vb in (("đề cương nộp", dc), ("gói đạo đức G2", g2), ("kế hoạch quản lý dữ liệu G5", g5)):
            khac = sorted({s for s in rx.findall(vb or "") if s != chot})
            if khac:
                mt.append(_vd("QT-07", "mau_thuan", f"{ten} ghi {', '.join(khac)} {don_vi} cho «{NHAN[muc]}» — đã "
                                                     f"chốt {chot} {don_vi}"))
    return _ket(loi, cb, mt, dong, thieu_tai_lieu=[t for t, v in (("đề cương nộp", dc), ("gói G2", g2),
                                                                     ("DMP G5", g5)) if v is None])


def _ket(loi, cb, mt, dong, thieu_tai_lieu=()) -> Dict[str, Any]:
    tt = TRANG_THAI_CHUA_DAT if (loi or mt) else TRANG_THAI_DAT
    tom = (f"{len(dong)} quyết định · {len(mt)} mâu thuẫn · {len(loi)} lỗi · {len(cb)} chờ PI"
           + (f" · chưa có {', '.join(thieu_tai_lieu)} (không so phần đó)" if thieu_tai_lieu else ""))
    return {"trang_thai": tt, "tom_tat": tom, "loi": loi, "canh_bao": cb, "mau_thuan": mt, "so_dong": len(dong)}


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Quy trình thu thập/nhập liệu/lưu trữ ↔ đề cương ↔ G2 ↔ G5 (chỉ đọc)")
    sp = ap.add_subparsers(dest="lenh", required=True)
    a1 = sp.add_parser("kiem")
    a1.add_argument("--study", required=True)
    a1.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    out_dir = BASE / "exports" / a.study
    if not (out_dir / "study_meta.json").is_file():
        print(f"KHÔNG ĐỌC ĐƯỢC: không có {out_dir}/study_meta.json", file=sys.stderr)
        return 2
    kq = kiem(out_dir, a.study)
    if a.json:
        print(json.dumps(kq, ensure_ascii=False, indent=2))
    else:
        print(f"QUY TRÌNH DỮ LIỆU — {a.study}: {kq['trang_thai']} — {kq['tom_tat']}")
        for x in kq["mau_thuan"] + kq["loi"] + kq["canh_bao"]:
            print(f"  {'🔴' if x['muc'] == 'mau_thuan' else '🟠' if x['muc'] == 'loi' else '🟡'} {x['ma']}: "
                  f"{x['noi_dung']}")
        print("Chỉ ĐỌC và BÁO. Cần bác sĩ kiểm chứng.")
    return {TRANG_THAI_DAT: 0, TRANG_THAI_CHUA_DAT: 1}.get(kq["trang_thai"], 2)


if __name__ == "__main__":
    sys.exit(main())
