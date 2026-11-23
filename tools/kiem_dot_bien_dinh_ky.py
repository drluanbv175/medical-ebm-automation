#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""KIỂM ĐỘT BIẾN ĐỊNH KỲ — chốt nào bị làm yếu mà test vẫn xanh thì báo đỏ (23/11/2026).

VÌ SAO CÓ
=========
Bác sĩ duyệt (23/11/2026) đề xuất «kiểm đột biến chạy định kỳ để chốt không mục dần». Trước đây mỗi agent tự kiểm đột
biến bằng script tạm lúc viết chốt; sau đó không ai đo lại, nên một lần sửa test (nới điều kiện, đổi tên) có thể làm
chốt mất tác dụng mà CI vẫn xanh. Sổ `config/dot_bien_dinh_ky.json` giữ các đột biến của chốt quan trọng; công cụ này
áp từng đột biến, chạy đúng test khai báo và đòi test ĐỎ.

LÀM GÌ
======
  1. Kiểm sổ: mỗi đoạn `cu` phải xuất hiện ĐÚNG MỘT lần trong `tep` — lệch ⇒ ĐỎ (sửa chốt thì sửa sổ cùng lúc).
  2. Lượt nền: mọi test khai báo phải XANH khi chưa đột biến — nền đỏ ⇒ không đo được đột biến, báo ĐỎ.
  3. Từng đột biến: thay `cu` bằng `moi`, xoá __pycache__, chạy test; test đỏ = «bắt được», test xanh = «SỐNG SÓT» ⇒ ĐỎ.
     Tệp LUÔN được phục hồi nguyên byte (kể cả khi ngắt giữa chừng).
  Mặc định đo trên một worktree TẠM của HEAD (rồi xoá) để không làm tiến trình khác trong cùng worktree nạp nhầm
  mã đột biến; `--tai-cho` đột biến ngay trong repo — chỉ cho bản checkout dùng một lần (CI).
Mã thoát: 0 mọi đột biến bị bắt · 1 có đột biến sống sót / sổ lệch / nền đỏ · 2 không đo được (thiếu sổ, thiếu pytest).

Dùng:  python tools/kiem_dot_bien_dinh_ky.py [--chi MA[,MA…]] [--json] [--goc <thư mục repo>] [--tai-cho]
Cần bác sĩ kiểm chứng.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

GOC = Path(__file__).resolve().parents[1]
SO = "config/dot_bien_dinh_ky.json"
THOI_HAN = 900   # giây mỗi lượt pytest


def doc_so(goc: Path) -> List[Dict[str, Any]]:
    """Danh sách đột biến của sổ; thiếu khoá bắt buộc ⇒ ValueError (sổ hỏng không được coi là rỗng)."""
    du = json.loads((goc / SO).read_text(encoding="utf-8"))
    ds = du.get("dot_bien")
    if not isinstance(ds, list) or not ds:
        raise ValueError("sổ không có danh sách «dot_bien»")
    for m in ds:
        thieu = [k for k in ("ma", "tep", "cu", "moi", "test") if not isinstance(m.get(k), str) or not m.get(k)]
        if thieu:
            raise ValueError(f"mục {m.get('ma', '?')} thiếu khoá {thieu}")
        if m["cu"] == m["moi"]:
            raise ValueError(f"mục {m['ma']}: «moi» trùng «cu» — không phải đột biến")
    return ds


def kiem_so(goc: Path, ds: List[Dict[str, Any]]) -> List[str]:
    """Lỗi sổ lệch mã: tệp vắng hoặc đoạn `cu` không xuất hiện đúng một lần."""
    loi = []
    for m in ds:
        p = goc / m["tep"]
        if not p.is_file():
            loi.append(f"{m['ma']}: không có tệp {m['tep']}")
            continue
        n = p.read_text(encoding="utf-8").count(m["cu"])
        if n != 1:
            loi.append(f"{m['ma']}: đoạn «cu» xuất hiện {n} lần trong {m['tep']} (cần đúng 1) — "
                       "sửa sổ cùng lúc sửa chốt")
    return loi


def _xoa_cache(goc: Path) -> None:
    for thu_muc in ("tools", "tests", "app", "runtime", "scripts"):
        for c in (goc / thu_muc).rglob("__pycache__") if (goc / thu_muc).is_dir() else ():
            shutil.rmtree(c, ignore_errors=True)


def chay_test(goc: Path, test: str) -> int:
    """Mã thoát pytest của một đích test (tệp hoặc node)."""
    _xoa_cache(goc)
    try:
        r = subprocess.run([sys.executable, "-B", "-m", "pytest", "-x", "-q", "-p", "no:cacheprovider", test],
                           cwd=goc, capture_output=True, text=True, timeout=THOI_HAN)
        return r.returncode
    except subprocess.TimeoutExpired:
        return 124


def thu_dot_bien(goc: Path, m: Dict[str, Any]) -> Dict[str, Any]:
    """Áp một đột biến, chạy test, PHỤC HỒI tệp nguyên byte. Trả {ma, ket_qua: bat_duoc|song_sot, ma_pytest}."""
    p = goc / m["tep"]
    goc_bytes = p.read_bytes()
    try:
        p.write_bytes(goc_bytes.decode("utf-8").replace(m["cu"], m["moi"], 1).encode("utf-8"))
        rc = chay_test(goc, m["test"])
    finally:
        p.write_bytes(goc_bytes)
        _xoa_cache(goc)
    # mã 5 = pytest không thu được test nào: đích khai sai — không phải «bắt được»
    return {"ma": m["ma"], "chot": m.get("chot", ""), "ket_qua": "bat_duoc" if rc not in (0, 5) else "song_sot",
            "ma_pytest": rc}


def chay(goc: Path, chi: Optional[List[str]] = None) -> Dict[str, Any]:
    ds = doc_so(goc)
    if chi:
        ds = [m for m in ds if m["ma"] in chi]
    loi_so = kiem_so(goc, ds)
    ket: Dict[str, Any] = {"so_dot_bien": len(ds), "loi_so": loi_so, "nen_do": [], "ket_qua": []}
    if loi_so:
        return ket
    for test in dict.fromkeys(m["test"] for m in ds):
        rc = chay_test(goc, test)
        if rc != 0:
            ket["nen_do"].append(f"{test} (mã {rc})")
    if ket["nen_do"]:
        return ket
    ket["ket_qua"] = [thu_dot_bien(goc, m) for m in ds]
    return ket


def _git_ra(goc: Path, *args: str) -> str:
    try:
        r = subprocess.run(["git", "-C", str(goc), *args], capture_output=True, text=True, timeout=120)
        return r.stdout.strip() if r.returncode == 0 else ""
    except (OSError, subprocess.TimeoutExpired):
        return ""


def tao_ban_sao(goc: Path, thu_muc: Optional[Path] = None) -> Optional[Path]:
    """Worktree tách rời của HEAD ở `~/.ebm-worktrees/dot-bien-<giờ>` (ngoài OneDrive).

    None khi `goc` không phải repo git."""
    if not _git_ra(goc, "rev-parse", "--git-dir"):
        return None
    dich = (thu_muc or Path.home() / ".ebm-worktrees") / f"dot-bien-{dt.datetime.now():%Y%m%d-%H%M%S}"
    r = subprocess.run(["git", "-C", str(goc), "worktree", "add", "--detach", "-q", str(dich), "HEAD"],
                       capture_output=True, text=True)
    return dich if r.returncode == 0 else None


def ma_thoat(ket: Dict[str, Any]) -> int:
    if ket["loi_so"] or ket["nen_do"] or any(x["ket_qua"] != "bat_duoc" for x in ket["ket_qua"]):
        return 1
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Kiểm đột biến định kỳ theo sổ config/dot_bien_dinh_ky.json")
    ap.add_argument("--chi", default="", help="chỉ các mã, ngăn bằng dấu phẩy")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--goc", type=Path, default=GOC, help="thư mục repo (mặc định: repo chứa công cụ)")
    ap.add_argument("--tai-cho", action="store_true",
                    help="đột biến NGAY trong thư mục repo (chỉ dùng cho bản checkout dùng một lần như CI)")
    a = ap.parse_args(argv)
    goc = a.goc.resolve()
    if not (goc / SO).is_file():
        print(f"⚪ không có sổ {SO} — không đo được")
        return 2
    if shutil.which(sys.executable) is None:
        return 2
    chi = [x.strip() for x in a.chi.split(",") if x.strip()] or None
    noi_chay, ban_sao = goc, None
    if not a.tai_cho:
        # 23/11/2026: đột biến sửa mã TẠM THỜI — chạy tại chỗ trong worktree đang có tiến trình khác (giả lập, agent)
        # làm các tiến trình đó nạp nhầm mã đã đột biến. Mặc định đo trên worktree tạm của HEAD rồi xoá.
        ban_sao = tao_ban_sao(goc)
        if ban_sao is None:
            print("⚪ không tạo được worktree tạm (thư mục không phải repo git) — dùng --tai-cho nếu là bản checkout "
                  "dùng một lần")
            return 2
        noi_chay = ban_sao
        if _git_ra(goc, "status", "--porcelain", "--", "tools", "tests", "config"):
            print("⚠ có thay đổi chưa commit ở tools/tests/config — lượt này đo bản HEAD, không gồm thay đổi đó")
    try:
        ket = chay(noi_chay, chi)
    except (ValueError, json.JSONDecodeError) as e:
        print(f"✗ sổ đột biến hỏng: {e}")
        return 1
    finally:
        if ban_sao is not None:
            subprocess.run(["git", "-C", str(goc), "worktree", "remove", "--force", str(ban_sao)],
                           capture_output=True, text=True)
    if a.json:
        print(json.dumps(ket, ensure_ascii=False, indent=1))
        return ma_thoat(ket)
    print(f"KIỂM ĐỘT BIẾN ĐỊNH KỲ — {ket['so_dot_bien']} đột biến")
    for x in ket["loi_so"]:
        print(f"  ✗ SỔ LỆCH: {x}")
    for x in ket["nen_do"]:
        print(f"  ✗ NỀN ĐỎ (chưa đột biến mà test đã đỏ): {x}")
    for x in ket["ket_qua"]:
        dau = "✅ bắt được" if x["ket_qua"] == "bat_duoc" else "❌ SỐNG SÓT"
        print(f"  {dau} {x['ma']} — {x['chot']} (pytest mã {x['ma_pytest']})")
    ma = ma_thoat(ket)
    print("KẾT: mọi đột biến bị bắt" if ma == 0
          else "KẾT: CHỐT MỤC — sửa test/chốt tại nguồn, không xoá đột biến khỏi sổ")
    print("Cần bác sĩ kiểm chứng.")
    return ma


if __name__ == "__main__":
    raise SystemExit(main())
