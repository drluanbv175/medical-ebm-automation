#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Đối chiếu BIỆN PHÁP KIỂM SOÁT SAI LỆCH (G1) ↔ PHÂN TÍCH TRONG SAP (G4) — giai đoạn 4 «Thiết kế».

Vì sao (bác sĩ 15/11/2026: «Hãy đảm bảo sự đồng bộ xuyên suốt và chính xác nhất»): kiểm tay C1a cho thấy bảng kiểm soát
sai lệch PI đã chốt ở G1 (`gate_params.G1.bias_controls`) hứa những phân tích mà SAP không có — «đo kỳ vọng và phân tích
thăm dò riêng» (đề cương 4.10 + Phụ lục D.3) và «đánh giá đặc tính đo lường trong mẫu (mục 4.5.3)» — trong khi SAP
đã ký.
Không công cụ nào nối hai bảng này: thiết kế nói «đã khống chế», kế hoạch phân tích không làm.

Tệp `exports/<mã>/_doi-chieu-sai-lech-sap.csv` (UTF-8, có/không BOM), mỗi dòng một sai lệch của G1:

  sai_lech       NGUYÊN VĂN `gate_params.G1.bias_controls[].sai_lech`
  can_phan_tich  co · khong — biện pháp có cần một PHÂN TÍCH/con số trong SAP không
  sap_muc        mục SAP chứa phân tích (vd «§9»; nhiều mục cách nhau «;») — bắt buộc khi `co`
  sap_neo        cụm chữ có NGUYÊN VĂN trong mục SAP đó (vd «ĐN4», «Phân tích giới hạn»); nhiều neo cách nhau « | »,
                 mỗi neo phải có trong ít nhất một mục đã khai — bắt buộc khi `co`
  noi_khac       khi `khong`: nơi mô tả biện pháp (vd «đề cương §4.7», «G5 DMP»)
  ghi_chu        tự do

Luật (mức `loi` ⇒ trục `kiem_soat_sai_lech` LỆCH MỀM; `canh_bao` ⇒ CẦN XEM; không có tệp ⇒ CHƯA ĐỦ ĐỂ SO):
  SL-01 thiếu cột bắt buộc · SL-02 sai lệch của G1 chưa có dòng · SL-03 dòng không khớp sai lệch nào của G1
  SL-04 `can_phan_tich` ngoài co/khong · SL-05 `co` mà mục SAP trống/không có trong SAP
  SL-06 `co` mà neo trống/không tìm thấy trong mục SAP đã khai
  SL-07 (cảnh báo) `khong` nhưng biện pháp có từ khoá phân tích · SL-08 (cảnh báo) `khong` mà `noi_khac` trống
  SL-09 (giai đoạn 8, 15/11/2026) sai lệch G1 ghi «hạn chế mở» mà đề cương nộp đã có: cột `neo_han_che` (cụm chữ
  NGUYÊN VĂN) phải nằm trong mục «Hạn chế» của đề cương — hạn chế đã biết trước phải được nêu cho Hội đồng/bàn luận
Chỉ ĐỌC và BÁO — không sửa tệp nào, trừ `mau --ghi` (dựng KHUNG khi chưa có tệp; không ghi đè).

Lệnh:
  python tools/doi_chieu_sai_lech_sap.py kiem --study <mã> [--json]   mã 0 ĐẠT · 1 CHƯA ĐẠT · 2 KHÔNG CÓ/KHÔNG ĐO ĐƯỢC
  python tools/doi_chieu_sai_lech_sap.py mau --study <mã> [--ghi]     khung từ bias_controls G1

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

TEP = "_doi-chieu-sai-lech-sap.csv"
COT = ("sai_lech", "can_phan_tich", "sap_muc", "sap_neo", "noi_khac", "ghi_chu", "neo_han_che")
COT_BAT_BUOC = ("sai_lech", "can_phan_tich", "sap_muc", "sap_neo")

TRANG_THAI_DAT = "DAT"
TRANG_THAI_CHUA_DAT = "CHUA_DAT"
TRANG_THAI_KHONG_CO = "KHONG_CO"
TRANG_THAI_KHONG_DO = "KHONG_DO"

# Biện pháp có từ khoá này thường cần một phân tích/con số trong SAP (SL-07 chỉ CẢNH BÁO — người đối chiếu quyết).
_TU_PHAN_TICH = re.compile(
    r"ph[âa]n\s+t[íi]ch|h[ồo]i\s+quy|hi[ệe]u\s+ch[ỉi]nh|sai\s+s[ốo]\s+chu[ẩa]n|\bICC\b|[đd][ộo]\s+nh[ạa]y|"
    r"tr[ọo]ng\s+s[ốo]|[đd]i[ềe]n\s+khuy[ếe]t|\bMICE\b|[đd]a\s+bi[ếe]n|SAP\s*§|b[áa]o\s+c[áa]o\s+t[ỷy]\s+l[ệe]|"
    r"[đd][ịi]nh\s+l[ưu][ợo]ng", re.I)
_MUC = re.compile(r"§\s*(\d{1,2})")
_MUC_SAP = re.compile(r"^#{2,4}\s*§\s*(\d{1,2})\b[^\n]*\n(.*?)(?=^#{2,4}\s*§\s*\d|^#{1,2}\s|\Z)", re.M | re.S)


def _nfc(s: Any) -> str:
    return unicodedata.normalize("NFC", str(s or "")).strip()


def _khoa(s: Any) -> str:
    return re.sub(r"\s+", " ", _nfc(s)).casefold()


def doc_meta(out_dir: Path) -> Dict[str, Any]:
    try:
        return json.loads((out_dir / "study_meta.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def sai_lech_g1(meta: Mapping[str, Any]) -> List[Dict[str, str]]:
    """Bảng sai lệch RIÊNG của đề tài (PI chốt ở G1). Dòng không có tên ⇒ bỏ qua."""
    g1 = ((meta.get("gate_params") or {}).get("G1") or {}) if isinstance(meta, Mapping) else {}
    ds = g1.get("bias_controls") if isinstance(g1, Mapping) else None
    ra: List[Dict[str, str]] = []
    for x in ds if isinstance(ds, list) else []:
        if isinstance(x, Mapping) and _nfc(x.get("sai_lech")):
            ra.append({"sai_lech": _nfc(x.get("sai_lech")), "bien_phap": _nfc(x.get("bien_phap")),
                       "trang_thai": _nfc(x.get("trang_thai"))})
    return ra


def muc_sap(out_dir: Path, study: str) -> Dict[str, str]:
    """{«9»: nội dung §9, …} của SAP G4; không có SAP ⇒ {}."""
    try:
        t = (out_dir / f"G4_A5_SAP_FINAL_{study}.md").read_text(encoding="utf-8")
    except OSError:
        return {}
    t = unicodedata.normalize("NFC", t)
    ra: Dict[str, str] = {}
    for m in _MUC_SAP.finditer(t):
        ra.setdefault(m.group(1), "")
        ra[m.group(1)] += m.group(2)
    return ra


def muc_han_che_de_cuong(out_dir: Path, study: str) -> Optional[str]:
    """Văn bản mục «Hạn chế…» của đề cương nộp (tới tiêu đề cùng cấp hoặc cao hơn kế tiếp); None nếu chưa có đề
    cương; chuỗi rỗng nếu đề cương CÓ nhưng không có tiêu đề nào chứa «Hạn chế» (18/11/2026: người gọi phải báo
    «thiếu mục», không báo «chưa khai neo» — đề cương BTM viết tay thiếu mục này từ 15/11 mà lỗi bị đọc thành việc
    điền bảng)."""
    try:
        dc = unicodedata.normalize("NFC", (out_dir / f"DE_CUONG_NOP_HOI_DONG_{study}.md").read_text(encoding="utf-8"))
    except OSError:
        return None
    m = re.search(r"^(#{1,4})\s[^\n]*[Hh]ạn chế[^\n]*\n", dc, re.M)
    if not m:
        return ""
    cap = len(m.group(1))
    sau = re.search(r"^#{1,%d}\s" % cap, dc[m.end():], re.M)
    return dc[m.start():m.end() + (sau.start() if sau else len(dc))]


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


def _vd(ma: str, muc: str, noi_dung: str) -> Dict[str, str]:
    return {"ma": ma, "muc": muc, "noi_dung": noi_dung}


def kiem(out_dir: Path, study: str, *, meta: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    """Chấm bảng đối chiếu. Trả {trang_thai, tom_tat, loi[], canh_bao[], so_dong, so_sai_lech}."""
    meta = meta if meta is not None else doc_meta(out_dir)
    g1 = sai_lech_g1(meta)
    if not g1:
        return {"trang_thai": TRANG_THAI_KHONG_CO, "tom_tat": "G1 chưa có bảng sai lệch riêng (bias_controls)",
                "loi": [], "canh_bao": [], "so_dong": 0, "so_sai_lech": 0, "khong_ap_dung": True}
    dong, cot, loi_doc = doc_bang(out_dir)
    if loi_doc:
        return {"trang_thai": TRANG_THAI_KHONG_DO, "tom_tat": f"không đọc được {TEP}: {loi_doc}",
                "loi": [_vd("SL-01", "loi", loi_doc)], "canh_bao": [], "so_dong": 0, "so_sai_lech": len(g1)}
    if dong is None:
        return {"trang_thai": TRANG_THAI_KHONG_CO, "tom_tat": f"chưa có {TEP} ({len(g1)} sai lệch G1 chưa đối chiếu)",
                "loi": [_vd("SL-02", "loi", f"chưa có {TEP}: {len(g1)} sai lệch của G1 chưa được nối với SAP")],
                "canh_bao": [], "so_dong": 0, "so_sai_lech": len(g1)}
    loi: List[Dict[str, str]] = []
    cb: List[Dict[str, str]] = []
    thieu_cot = [c for c in COT_BAT_BUOC if c not in (cot or [])]
    if thieu_cot:
        loi.append(_vd("SL-01", "loi", f"thiếu cột {', '.join(thieu_cot)}"))
        return _ket(loi, cb, dong, g1)
    sap = muc_sap(out_dir, study)
    if not sap:
        return {"trang_thai": TRANG_THAI_KHONG_DO, "tom_tat": "chưa có SAP G4 để đối chiếu",
                "loi": [], "canh_bao": [], "so_dong": len(dong), "so_sai_lech": len(g1)}
    theo_ten = {_khoa(x["sai_lech"]): x for x in g1}
    da_co = set()
    for i, r in enumerate(dong, start=2):
        ten = r.get("sai_lech", "")
        k = _khoa(ten)
        if k not in theo_ten:
            loi.append(_vd("SL-03", "loi", f"dòng {i} «{ten}» không khớp sai lệch nào của G1 (gõ sai hoặc G1 đã đổi)"))
            continue
        da_co.add(k)
        cpt = _khoa(r.get("can_phan_tich"))
        if cpt not in ("co", "khong"):
            loi.append(_vd("SL-04", "loi", f"dòng {i} «{ten}»: can_phan_tich «{r.get('can_phan_tich')}» ≠ co/khong"))
            continue
        if cpt == "khong":
            if _TU_PHAN_TICH.search(theo_ten[k]["bien_phap"]):
                cb.append(_vd("SL-07", "canh_bao", f"«{ten}»: biện pháp có từ khoá phân tích nhưng ghi «khong» — "
                                                   "đối chiếu lại với SAP"))
            if not r.get("noi_khac"):
                cb.append(_vd("SL-08", "canh_bao", f"«{ten}»: «khong» mà chưa ghi biện pháp mô tả ở đâu (noi_khac)"))
            continue
        muc = _MUC.findall(r.get("sap_muc", ""))
        thieu_muc = [m for m in muc if m not in sap]
        if not muc or thieu_muc:
            loi.append(_vd("SL-05", "loi", f"«{ten}»: mục SAP «{r.get('sap_muc') or 'trống'}» "
                                           + (f"không có trong SAP (§{', §'.join(thieu_muc)})" if thieu_muc
                                              else "chưa khai")))
            continue
        neo = [x.strip() for x in r.get("sap_neo", "").split("|") if x.strip()]
        if not neo:
            loi.append(_vd("SL-06", "loi", f"«{ten}»: chưa khai neo trong SAP (sap_neo)"))
            continue
        vb = "\n".join(sap[m] for m in muc).casefold()
        mat = [x for x in neo if x.casefold() not in vb]
        if mat:
            loi.append(_vd("SL-06", "loi", f"«{ten}»: SAP {', '.join('§' + m for m in muc)} không có "
                                           + "; ".join(f"«{x}»" for x in mat)
                                           + " — G1 hứa phân tích này nhưng SAP chưa có"))
    for k, x in theo_ten.items():
        if k not in da_co:
            loi.append(_vd("SL-02", "loi", f"sai lệch G1 «{x['sai_lech']}» chưa có dòng đối chiếu"))
    han_che = muc_han_che_de_cuong(out_dir, study)
    mo = [x for x in theo_ten.values() if "hạn chế mở" in x.get("trang_thai", "").casefold()]
    if han_che == "" and mo:
        # Đề cương không có mục «Hạn chế» ⇒ MỘT lỗi nói đúng việc cần làm (thêm mục), thay vì N lỗi «chưa khai neo».
        loi.append(_vd("SL-09", "loi", "đề cương nộp CHƯA CÓ mục «Hạn chế» (không tiêu đề nào chứa chữ «Hạn chế») "
                                       f"nhưng G1 có {len(mo)} hạn chế mở: "
                                       + "; ".join(f"«{x['sai_lech']}»" for x in mo)
                                       + " — thêm mục «Hạn chế của nghiên cứu» nêu các hạn chế này, rồi khai "
                                         "neo_han_che (cụm chữ nguyên văn trong mục đó)"))
    elif han_che is not None:
        theo_dong = {_khoa(r.get("sai_lech")): r for r in dong}
        for k, x in theo_ten.items():
            if "hạn chế mở" not in x.get("trang_thai", "").casefold() or k not in theo_dong:
                continue
            neo = theo_dong[k].get("neo_han_che", "")
            if not neo:
                loi.append(_vd("SL-09", "loi", f"«{x['sai_lech']}» là hạn chế mở (G1) nhưng chưa khai neo_han_che"))
            elif neo.casefold() not in han_che.casefold():
                loi.append(_vd("SL-09", "loi", f"«{x['sai_lech']}» là hạn chế mở (G1) nhưng mục «Hạn chế» của đề cương "
                                               f"nộp không có «{neo}»"))
    return _ket(loi, cb, dong, g1)


def _ket(loi: List[Dict[str, str]], cb: List[Dict[str, str]], dong: Sequence[Mapping[str, str]],
         g1: Sequence[Mapping[str, str]]) -> Dict[str, Any]:
    tt = TRANG_THAI_CHUA_DAT if loi else TRANG_THAI_DAT
    co = sum(1 for r in dong if _khoa(r.get("can_phan_tich")) == "co")
    tom = (f"{len(g1)} sai lệch G1 · {len(dong)} dòng ({co} cần phân tích SAP) · {len(loi)} lỗi · {len(cb)} cảnh báo")
    return {"trang_thai": tt, "tom_tat": tom, "loi": loi, "canh_bao": cb, "so_dong": len(dong),
            "so_sai_lech": len(g1)}


def khung(meta: Mapping[str, Any]) -> List[Dict[str, str]]:
    """Khung: mỗi sai lệch G1 một dòng, đoán sẵn can_phan_tich theo từ khoá (người đối chiếu sửa)."""
    return [{"sai_lech": x["sai_lech"], "can_phan_tich": "co" if _TU_PHAN_TICH.search(x["bien_phap"]) else "khong",
             "sap_muc": "[CẦN §]", "sap_neo": "[CẦN NEO]", "noi_khac": "", "ghi_chu": x["bien_phap"][:160]}
            for x in sai_lech_g1(meta)]


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Đối chiếu kiểm soát sai lệch G1 ↔ SAP G4 (chỉ đọc)")
    sp = ap.add_subparsers(dest="lenh", required=True)
    a1 = sp.add_parser("kiem")
    a1.add_argument("--study", required=True)
    a1.add_argument("--json", action="store_true")
    a2 = sp.add_parser("mau")
    a2.add_argument("--study", required=True)
    a2.add_argument("--ghi", action="store_true")
    a = ap.parse_args(argv)
    out_dir = BASE / "exports" / a.study
    if not (out_dir / "study_meta.json").is_file():
        print(f"KHÔNG ĐỌC ĐƯỢC: không có {out_dir}/study_meta.json", file=sys.stderr)
        return 2
    if a.lenh == "mau":
        dong = khung(doc_meta(out_dir))
        p = out_dir / TEP
        if a.ghi:
            if p.exists():
                print(f"ĐÃ CÓ {p.name} — không ghi đè.")
                return 1
            with p.open("w", encoding="utf-8", newline="") as f:
                w = csv.DictWriter(f, fieldnames=list(COT), lineterminator="\n")
                w.writeheader()
                w.writerows(dong)
            print(f"Đã dựng khung {p.name}: {len(dong)} dòng — điền sap_muc/sap_neo rồi chạy `kiem`.")
        else:
            for r in dong:
                print(f"  {r['can_phan_tich']:<5} {r['sai_lech']}")
        return 0
    kq = kiem(out_dir, a.study)
    if a.json:
        print(json.dumps(kq, ensure_ascii=False, indent=2))
    else:
        print(f"ĐỐI CHIẾU SAI LỆCH ↔ SAP — {a.study}: {kq['trang_thai']} — {kq['tom_tat']}")
        for x in kq["loi"] + kq["canh_bao"]:
            print(f"  {'🔴' if x['muc'] == 'loi' else '🟡'} {x['ma']}: {x['noi_dung']}")
        print("Chỉ ĐỌC và BÁO. Cần bác sĩ kiểm chứng.")
    return {TRANG_THAI_DAT: 0, TRANG_THAI_CHUA_DAT: 1}.get(kq["trang_thai"], 2)


if __name__ == "__main__":
    sys.exit(main())
