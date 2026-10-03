#!/usr/bin/env python3
"""Chốt liên kết/EID Scopus trong `reports/` của repo y khoa (03/10/2026).

Vì sao: repo đang CÔNG KHAI; Routine Cloud commit `reports/giam-sat-cloud/<ngày>/`. Điều khoản Elsevier (điều khoản
riêng Scopus sửa 16/09/2026; API Service Agreement §2.4) cấm phát tán dữ liệu Scopus — liên kết bản ghi `scopus.com/…`
và mã EID `2-s2.0-…` không được lên git. Bộ luật nhận diện + làm sạch: `app/utils/lien_ket_scopus.py` (chỉ thư viện
chuẩn, nên chạy được bằng `python3` hệ thống trong pre-commit).

Chế độ:
  --staged            (mặc định) quét nội dung ĐÃ STAGE dưới reports/ (đọc blob trong index, không đọc cây làm việc).
  --tracked           quét mọi tệp đã track dưới reports/.
  --path P [P …]      quét tệp/thư mục chỉ định.
  --lam-sach P [P …]  làm sạch TẠI CHỖ tệp/thư mục chỉ định (URL Scopus → DOI/PubMed của cùng mục, không có thì
                      ghi chú).

Mã thoát: 0 sạch · 1 có liên kết/EID Scopus · 2 không đo được (git lỗi, đường dẫn không có).
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.utils.lien_ket_scopus import (  # noqa: E402
    lam_sach_tep,
    lam_sach_thu_muc,
    quet_thu_muc,
    tim_vi_pham,
)

THU_MUC_CHOT = "reports/"


def _git(repo: Path, *args: str) -> bytes:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, check=True).stdout


def _danh_sach_z(raw: bytes) -> List[str]:
    # -z: tên tệp không ASCII không bị git trích dẫn kiểu "\303\241" (bài học BH155).
    return [p.decode("utf-8", errors="surrogateescape") for p in raw.split(b"\0") if p]


def quet_staged(repo: Path) -> Dict[str, List[Tuple[int, str]]]:
    ten = _danh_sach_z(_git(repo, "diff", "--cached", "--name-only", "-z", "--diff-filter=ACMR", "--", THU_MUC_CHOT))
    ra: Dict[str, List[Tuple[int, str]]] = {}
    for p in ten:
        vp = tim_vi_pham(_git(repo, "show", f":{p}").decode("utf-8", errors="replace"))
        if vp:
            ra[p] = vp
    return ra


def quet_tracked(repo: Path) -> Dict[str, List[Tuple[int, str]]]:
    ra: Dict[str, List[Tuple[int, str]]] = {}
    for p in _danh_sach_z(_git(repo, "ls-files", "-z", "--", THU_MUC_CHOT)):
        tep = repo / p
        if tep.is_file():
            vp = tim_vi_pham(tep.read_bytes().decode("utf-8", errors="replace"))
            if vp:
                ra[p] = vp
    return ra


def quet_duong_dan(duong_dan: List[Path]) -> Dict[str, List[Tuple[int, str]]]:
    ra: Dict[str, List[Tuple[int, str]]] = {}
    for p in duong_dan:
        if p.is_dir():
            ra.update({f"{p.as_posix()}/{k}": v for k, v in quet_thu_muc(p).items()})
        else:
            vp = tim_vi_pham(p.read_bytes().decode("utf-8", errors="replace"))
            if vp:
                ra[p.as_posix()] = vp
    return ra


def _in_vi_pham(vi_pham: Dict[str, List[Tuple[int, str]]]) -> None:
    for tep, ds in sorted(vi_pham.items()):
        print(f"🔴 {tep}: {len(ds)} liên kết/EID Scopus", file=sys.stderr)
        for so_dong, doan in ds[:5]:
            print(f"   dòng {so_dong}: {doan[:60]}…", file=sys.stderr)
        if len(ds) > 5:
            print(f"   … và {len(ds) - 5} chỗ nữa", file=sys.stderr)


def main(argv: Optional[list] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    nhom = ap.add_mutually_exclusive_group()
    nhom.add_argument("--staged", action="store_true", help="Quét phần đã stage dưới reports/ (mặc định).")
    nhom.add_argument("--tracked", action="store_true", help="Quét mọi tệp đã track dưới reports/.")
    nhom.add_argument("--path", nargs="+", type=Path, help="Quét tệp/thư mục chỉ định.")
    nhom.add_argument("--lam-sach", nargs="+", type=Path, help="Làm sạch tại chỗ tệp/thư mục chỉ định.")
    ap.add_argument("--repo", type=Path, default=ROOT, help="Gốc repo git (mặc định: repo chứa công cụ này).")
    a = ap.parse_args(argv)

    duong_dan = a.lam_sach or a.path or []
    thieu = [str(p) for p in duong_dan if not p.exists()]
    if thieu:
        print(f"⚪ không có đường dẫn: {', '.join(thieu)} — KHÔNG đo được.", file=sys.stderr)
        return 2
    if a.lam_sach:
        tong = 0
        for p in a.lam_sach:
            if p.is_dir():
                da_thay = lam_sach_thu_muc(p)
            else:
                n_tep = lam_sach_tep(p)
                da_thay = {p.name: n_tep} if n_tep else {}
            for ten, n in sorted(da_thay.items()):
                print(f"đã gỡ {n} liên kết/EID Scopus: {ten}")
            tong += sum(da_thay.values())
        con_lai = quet_duong_dan(a.lam_sach)
        if con_lai:  # không thể xảy ra nếu bộ làm sạch đúng — vẫn báo đỏ, không im lặng
            _in_vi_pham(con_lai)
            return 1
        print(f"✅ sạch (đã gỡ {tong}).")
        return 0
    try:
        if a.path:
            vi_pham = quet_duong_dan(a.path)
        elif a.tracked:
            vi_pham = quet_tracked(a.repo)
        else:
            vi_pham = quet_staged(a.repo)
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"⚪ không đo được liên kết Scopus (git/đọc tệp lỗi: {exc}).", file=sys.stderr)
        return 2
    if vi_pham:
        _in_vi_pham(vi_pham)
        print("Repo CÔNG KHAI — điều khoản Elsevier cấm phát tán dữ liệu Scopus. Làm sạch:\n"
              "  python3 tools/kiem_lien_ket_scopus_bao_cao.py --lam-sach <tệp/thư mục> rồi git add lại.",
              file=sys.stderr)
        return 1
    print("✅ không có liên kết/EID Scopus.")
    return 0


if __name__ == "__main__":
    for luong in (sys.stdout, sys.stderr):
        if hasattr(luong, "reconfigure"):
            luong.reconfigure(encoding="utf-8")
    sys.exit(main())
