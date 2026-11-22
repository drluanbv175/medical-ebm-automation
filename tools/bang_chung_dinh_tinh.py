# -*- coding: utf-8 -*-
"""Bằng chứng thủ tục cho độ tin cậy của nghiên cứu định tính (SAP §9 — trustworthiness) — 22/11/2026.

VÌ SAO: credibility, dependability, transferability (Lincoln & Guba) không phải phép tính, nên G6 từng ghi «chưa tự
động» và bỏ đó. Nhưng mỗi tiêu chí để lại BẰNG CHỨNG THỦ TỤC kiểm được bằng máy: nhật ký kiểm lại với người tham gia
(COREQ mục 28 — Tong 2007, PMID 17872937), nhật ký quyết định mã hoá (audit trail), bản mô tả dày bối cảnh và người tham
gia (SRQR mục 6, 9, 15 — O'Brien 2014, PMID 24979285). Mô-đun này định nghĩa KHUÔN của từng bằng chứng (tệp, cột/mục bắt
buộc) và kiểm: đủ ⇒ «DA_KIEM»; vắng tệp, thiếu cột/mục, chưa có dòng nào ⇒ «THIEU» kèm lý do cụ thể. Không chấm chất
lượng nội dung — đó là việc của người bình duyệt; máy chỉ xác nhận thủ tục đã được ghi lại.

Dùng: `chay_sap_g6` (tham số đặc tả `bang_chung` = credibility | dependability | transferability) và
`python3 tools/bang_chung_dinh_tinh.py mau --study <mã> [--ghi]` — ghi khuôn trống (chỉ tiêu đề cột/mục) vào thư mục đề
tài để nhóm nghiên cứu điền trong lúc thu thập và phân tích. Cần bác sĩ kiểm chứng.
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Any, Dict, List

CAN_KIEM = "Cần bác sĩ kiểm chứng."
KHUON: Dict[str, Dict[str, Any]] = {
    "credibility": {
        "nhan": "Nhật ký kiểm lại với người tham gia (member checking)",
        "tep": "G5_NHAT_KY_KIEM_LAI_{study}.csv",
        "cot": ["ma_nguoi_tham_gia", "ngay", "hinh_thuc", "noi_dung_tra_lai", "phan_hoi", "dieu_chinh"],
    },
    "dependability": {
        "nhan": "Nhật ký quyết định mã hoá (audit trail)",
        "tep": "G6_NHAT_KY_QUYET_DINH_MA_HOA_{study}.csv",
        "cot": ["ngay", "nguoi_ma_hoa", "ma", "quyet_dinh", "ly_do"],
    },
    "transferability": {
        "nhan": "Mô tả dày bối cảnh và người tham gia",
        "tep": "G6_MO_TA_BOI_CANH_{study}.md",
        "muc": ["## Bối cảnh nơi nghiên cứu", "## Đặc điểm người tham gia", "## Cách thu thập dữ liệu"],
    },
}
DA_KIEM, THIEU = "DA_KIEM", "THIEU"


def tep_cua(d: Path, study: str, loai: str) -> Path:
    return Path(d) / KHUON[loai]["tep"].format(study=study)


def kiem(d: Path, study: str, loai: str) -> Dict[str, Any]:
    """{trang_thai DA_KIEM|THIEU, loai, nhan, tep, so_dong|so_ky_tu_muc, thieu: [lý do]}."""
    if loai not in KHUON:
        raise KeyError(loai)
    k = KHUON[loai]
    p = tep_cua(d, study, loai)
    ra: Dict[str, Any] = {"loai": loai, "nhan": k["nhan"], "tep": p.name, "thieu": []}
    if not p.is_file():
        ra["thieu"].append(f"chưa có tệp {p.name}")
    elif "cot" in k:
        with p.open(encoding="utf-8-sig", newline="") as f:
            rd = csv.DictReader(f)
            cot = list(rd.fieldnames or [])
            dong = list(rd)
        vang = [c for c in k["cot"] if c not in cot]
        if vang:
            ra["thieu"].append(f"thiếu cột: {', '.join(vang)}")
        du = [r for r in dong if all(str(r.get(c) or "").strip() for c in k["cot"] if c in cot)]
        ra["so_dong"], ra["so_dong_du"] = len(dong), len(du)
        if not du:
            ra["thieu"].append("chưa có dòng nào ghi đủ các cột bắt buộc")
    else:
        t = p.read_text(encoding="utf-8")
        than: Dict[str, int] = {}
        for i, m in enumerate(k["muc"]):
            a = t.find(m)
            if a < 0:
                ra["thieu"].append(f"thiếu mục «{m.lstrip('# ')}»")
                continue
            sau = [t.find(x, a + len(m)) for x in k["muc"][i + 1:]] + [t.find("\n## ", a + len(m))]
            b = min([x for x in sau if x > a] or [len(t)])
            than[m.lstrip("# ")] = len(t[a + len(m):b].strip())
            if than[m.lstrip("# ")] == 0:
                ra["thieu"].append(f"mục «{m.lstrip('# ')}» chưa có nội dung")
        ra["so_ky_tu_muc"] = than
    ra["trang_thai"] = THIEU if ra["thieu"] else DA_KIEM
    return ra


def khuon_trong(loai: str) -> str:
    k = KHUON[loai]
    if "cot" in k:
        return ",".join(k["cot"]) + "\n"
    return f"# {k['nhan']}\n\n" + "\n\n".join(m + "\n" for m in k["muc"])


def main(argv: List[str] | None = None) -> int:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description="Khuôn và kiểm bằng chứng thủ tục độ tin cậy định tính")
    sp = ap.add_subparsers(dest="lenh", required=True)
    m = sp.add_parser("mau", help="ghi khuôn trống (chạy khô mặc định)")
    m.add_argument("--study", required=True)
    m.add_argument("--ghi", action="store_true")
    k = sp.add_parser("kiem")
    k.add_argument("--study", required=True)
    a = ap.parse_args(argv)
    import run_stats_analysis as RSA  # noqa: PLC0415

    d = Path(RSA._thu_muc_de_tai(a.study))
    if a.lenh == "mau":
        for loai in KHUON:
            p = tep_cua(d, a.study, loai)
            if p.exists():
                print(f"= {p.name} đã có — giữ nguyên")
            elif a.ghi:
                p.write_text(khuon_trong(loai), encoding="utf-8", newline="\n")
                print(f"✓ ghi khuôn {p.name}")
            else:
                print(f"· (chạy khô) sẽ ghi khuôn {p.name}")
    else:
        for loai in KHUON:
            r = kiem(d, a.study, loai)
            print(f"{'✓' if r['trang_thai'] == DA_KIEM else '✗'} {loai}: {r['tep']} — {'; '.join(r['thieu']) or 'đủ'}")
    print(CAN_KIEM)
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    raise SystemExit(main())
