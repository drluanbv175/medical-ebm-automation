#!/usr/bin/env python3
"""Cầu nối hook UserPromptSubmit «một cửa vào» cho phiên Claude Code mở trong repo y khoa (29/10/2026).

Vì sao có tệp này: luật «một cửa vào» (BH172, 28/10/2026) cài hook nhắc định tuyến ở `.claude/settings.json` của repo
GỐC. Claude Code chỉ đọc settings của THƯ MỤC DỰ ÁN đang mở, không đọc settings của thư mục cha ⇒ phiên mở trong
`medical-ebm-automation/` (nhóm «Nghiên cứu y khoa đăng tạp chí») hoặc một worktree của nó KHÔNG có hook — bác sĩ hỏi
chủ đề chứng cứ ở đó thì chỉ còn luật văn bản trong CLAUDE.md, đúng lỗ hổng đã làm ba phiên 28/10 đi sai đường.

Cầu nối KHÔNG chép bộ định tuyến sang đây (hai bản sẽ trôi lệch nhau): nó tìm repo gốc rồi chạy ĐÚNG
`tools/nhac_dinh_tuyen.py` của repo gốc bằng tiến trình con, chuyển nguyên dữ liệu hook vào và chuyển nguyên lời nhắc
ra.

Tìm repo gốc — thư mục có ĐỦ `tools/nhac_dinh_tuyen.py` và `tools/orchestrator/intent.py` — theo thứ tự:
  1. biến môi trường `EBM_WORKSPACE_ROOT` (cùng biến pre-commit của repo này đã dùng);
  2. đi ngược lên từ `CLAUDE_PROJECT_DIR` và từ chính repo chứa tệp này (trên OneDrive repo y khoa nằm TRONG repo gốc;
     worktree `.claude/worktrees/<tên>` nằm sâu hơn nhưng vẫn trong cây đó);
  3. worktree đặt NGOÀI cây OneDrive (vd `~/.ebm-worktrees/…`): đọc `.git` (tệp `gitdir:`) → `commondir` → checkout
     chính của repo y khoa, rồi đi ngược lên từ đó.
Không tìm thấy (phiên Cloud chỉ có repo y khoa, máy chưa có repo gốc…) ⇒ im lặng.

Mọi lỗi ⇒ im lặng và mã 0, giống hook gốc: hook nhắc không bao giờ được chặn lượt gõ của bác sĩ.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

# Hai tệp phải CÙNG có mặt thì mới là repo gốc (một tệp trùng tên lạc chỗ không đủ).
DAU_HIEU_GOC = (Path("tools") / "nhac_dinh_tuyen.py", Path("tools") / "orchestrator" / "intent.py")
HOOK_GOC = DAU_HIEU_GOC[0]
THOI_HAN_GIAY = 8  # hook khai timeout 10 giây; chừa thời gian cho cầu nối tự thoát gọn


def la_goc(thu_muc: Path) -> bool:
    """Thư mục có đủ dấu hiệu của repo gốc chưa."""
    return all((thu_muc / d).is_file() for d in DAU_HIEU_GOC)


def checkout_chinh(thu_muc: Path) -> Path | None:
    """Với worktree git (`.git` là TỆP «gitdir: …»), trả checkout chính của repo; không phải worktree ⇒ None."""
    tep_git = thu_muc / ".git"
    if not tep_git.is_file():
        return None
    noi_dung = tep_git.read_text(encoding="utf-8", errors="replace").strip()
    if not noi_dung.startswith("gitdir:"):
        return None
    gitdir = Path(noi_dung.split(":", 1)[1].strip())
    if not gitdir.is_absolute():
        gitdir = (thu_muc / gitdir).resolve()
    tep_common = gitdir / "commondir"
    if not tep_common.is_file():
        return None
    common = Path(tep_common.read_text(encoding="utf-8", errors="replace").strip())
    if not common.is_absolute():
        common = (gitdir / common).resolve()
    # commondir trỏ vào thư mục `.git` của checkout chính ⇒ checkout chính là thư mục cha của nó.
    return common.parent


def diem_xuat_phat() -> list[Path]:
    """Các thư mục để đi ngược lên tìm repo gốc, theo thứ tự ưu tiên, không trùng."""
    ung_vien: list[Path] = []
    du_an = os.environ.get("CLAUDE_PROJECT_DIR", "").strip()
    if du_an:
        ung_vien.append(Path(du_an))
    ung_vien.append(Path(__file__).resolve().parent.parent)
    for p in list(ung_vien):
        try:
            chinh = checkout_chinh(p)
        except OSError:
            chinh = None
        if chinh is not None:
            ung_vien.append(chinh)
    ket_qua: list[Path] = []
    for p in ung_vien:
        try:
            p = p.resolve()
        except OSError:
            continue
        if p not in ket_qua:
            ket_qua.append(p)
    return ket_qua


def tim_goc() -> Path | None:
    """Repo gốc chứa hook nhắc định tuyến, hoặc None khi không tìm thấy."""
    khai = os.environ.get("EBM_WORKSPACE_ROOT", "").strip()
    if khai and la_goc(Path(khai)):
        return Path(khai).resolve()
    for dau in diem_xuat_phat():
        for p in (dau, *dau.parents):
            if la_goc(p):
                return p
    return None


def main() -> int:
    try:
        goc = tim_goc()
        if goc is None:
            return 0
        hook = (goc / HOOK_GOC).resolve()
        if hook == Path(__file__).resolve():  # phòng vòng lặp nếu một ngày tệp này bị đặt nhầm làm hook gốc
            return 0
        du_lieu = sys.stdin.buffer.read()
        r = subprocess.run([sys.executable, str(hook)], input=du_lieu, capture_output=True, timeout=THOI_HAN_GIAY,
                           cwd=str(goc), env={**os.environ, "PYTHONIOENCODING": "utf-8"}, check=False)
        if r.returncode == 0 and r.stdout:
            sys.stdout.buffer.write(r.stdout)
            sys.stdout.buffer.flush()
    except Exception:  # noqa: BLE001 — hook nhắc tuyệt đối không được chặn lượt gõ
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
