"""Hỏi git: một tệp SẮP GHI có nằm ở chỗ `git add -A` cuốn đi không — thêm 30/09/2026.

Repo này CÔNG KHAI, mà hai nơi trong mã ghi TOÀN VĂN CÓ BẢN QUYỀN xuống đĩa: `WileyTdmClient`
(PDF của nhà xuất bản) và `tools/toan_van_guideline.py --luu`. Luật `.gitignore` chỉ bắt đúng
những tên đã khai; thư mục người dùng tự đặt thì không. Module này trả lời MỘT câu cho cả hai
nơi, bằng chính git chứ không bằng so chuỗi đường dẫn:

    NGOAI_CAY_GIT  tệp không nằm trong cây làm việc git nào — git không thể thấy;
    BI_IGNORE      nằm trong một cây git và có luật ignore CỦA KHO bắt;
    GIT_THAY       nằm trong một cây git và KHÔNG luật nào bắt: `git status` hiện, `git add -A` cuốn vào;
    KHONG_DO_DUOC  nằm trong một cây git nhưng không hỏi được git (thiếu lệnh git, git lỗi, quá hạn).

Bốn điều đo ngày 30/09/2026 (git 2.54) quyết định cách hỏi:
  * Chỉ tính luật ĐI THEO KHO (`.gitignore` trong cây, `.git/info/exclude`). Luật ignore riêng của
    máy (`core.excludesFile`, `~/.config/git/ignore`) bị loại bằng `-c core.excludesFile=<os.devnull>`:
    cây làm việc đồng bộ qua OneDrive sang máy khác, nơi luật riêng đó không tồn tại.
  * Lấy mã thoát của `check-ignore -q` (0 = bị ignore, 1 = không). Không dùng `-v`: với luật phủ
    định («!mẫu») `-v` vẫn trả 0.
  * Chạy git bằng `-C <thư mục cha ĐANG TỒN TẠI gần nhất>`, phần còn lại là đường tương đối: hệ điều
    hành tự giải bí danh của thư mục (sai chữ hoa/thường trên macOS, symlink) — không so chuỗi.
  * Gỡ mọi biến `GIT_*` thừa hưởng: trong hook git, `GIT_DIR` trỏ sang kho khác làm git áp luật
    riêng (`info/exclude`) của kho KIA lên thư mục đang hỏi — cùng một đường dẫn, mã thoát đổi từ 1
    sang 0 (tests/test_toan_van_khong_lot_vao_git_20260930.py dựng lại đúng tình huống này).

«Không nằm trong cây git nào» được xác định bằng cách dò mục `.git` ở các thư mục cha, KHÔNG cần
lệnh git: máy không cài git vẫn ghi được ra ngoài repo. Mã thoát 128 của git không phân biệt
«không phải kho git» với «là kho git nhưng git từ chối trả lời» (vd `safe.directory`), nên không
dùng mã đó để kết luận «ở ngoài».
"""
from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Union

NGOAI_CAY_GIT = "ngoai_cay_git"
BI_IGNORE = "bi_ignore"
GIT_THAY = "git_thay"
KHONG_DO_DUOC = "khong_do_duoc"

# Tên lệnh git — tách thành hằng để ca kiểm dựng được «máy không có git» mà vẫn chạy đúng đường mã thật.
_LENH_GIT = "git"
_HAN_GIAY = 30.0

DuongDan = Union[str, "os.PathLike[str]"]


@dataclass(frozen=True)
class TamNhinGit:
    """Kết luận cho MỘT tệp. `goc_cay` là thư mục chứa `.git` gần nhất phía trên tệp (None khi tệp
    nằm ngoài mọi cây git); `ly_do` chỉ có khi `KHONG_DO_DUOC`."""

    trang_thai: str
    goc_cay: Optional[Path] = None
    ly_do: str = ""


def _tuyet_doi(duong: DuongDan) -> Path:
    """Đường tuyệt đối, đã giải «~», symlink và «..». Trên macOS phần chữ hoa/thường giữ nguyên như
    người gọi gõ — vì vậy mọi phép so ở dưới đều đi qua hệ điều hành, không so chuỗi."""
    return Path(duong).expanduser().resolve()


def _cha_ton_tai_gan_nhat(tep: Path) -> Optional[Path]:
    for cha in tep.parents:
        if cha.is_dir():
            return cha
    return None


def _goc_cay_git(thu_muc: Path) -> Optional[Path]:
    """Thư mục gần nhất, tính từ `thu_muc` trở lên, có mục `.git` — thư mục (kho thường) hoặc tệp
    (worktree, submodule). Không thấy ở cấp nào ⇒ None."""
    for ung_vien in (thu_muc, *thu_muc.parents):
        if os.path.lexists(ung_vien / ".git"):
            return ung_vien
    return None


def _moi_truong_git() -> Dict[str, str]:
    return {k: v for k, v in os.environ.items() if not k.upper().startswith("GIT_")}


def tam_nhin_git(tep: DuongDan) -> TamNhinGit:
    """Git có nhìn thấy `tep` không. `tep` là đường dẫn TỆP sắp ghi; tệp và các thư mục cha của nó
    chưa cần tồn tại."""
    dich = _tuyet_doi(tep)
    cha = _cha_ton_tai_gan_nhat(dich)
    goc = _goc_cay_git(cha) if cha is not None else None
    if cha is None or goc is None:
        return TamNhinGit(NGOAI_CAY_GIT)
    # Tiền tố «./»: tên bắt đầu bằng «:(» không bị git hiểu thành «pathspec magic» (đo: «:(glob)x.pdf»
    # ⇒ mã 128; «./:(glob)x.pdf» ⇒ trả lời bình thường).
    lenh = [
        _LENH_GIT, "-C", str(cha), "-c", f"core.excludesFile={os.devnull}",
        "check-ignore", "-q", "--no-index", "--", "./" + dich.relative_to(cha).as_posix(),
    ]
    try:
        kq = subprocess.run(
            lenh, capture_output=True, text=True, encoding="utf-8", errors="replace",
            env=_moi_truong_git(), timeout=_HAN_GIAY,
        )
    except FileNotFoundError:
        return TamNhinGit(KHONG_DO_DUOC, goc, f"máy không có lệnh `{_LENH_GIT}`")
    except subprocess.TimeoutExpired:
        return TamNhinGit(KHONG_DO_DUOC, goc, f"git không trả lời sau {_HAN_GIAY:g} giây")
    except OSError as exc:
        return TamNhinGit(KHONG_DO_DUOC, goc, f"không chạy được git: {exc}")
    if kq.returncode == 0:
        return TamNhinGit(BI_IGNORE, goc)
    if kq.returncode == 1:
        return TamNhinGit(GIT_THAY, goc)
    loi = " ".join((kq.stderr or "").split())[:200]
    return TamNhinGit(KHONG_DO_DUOC, goc, f"git check-ignore trả mã {kq.returncode}: {loi or 'không kèm thông báo'}")


def nam_trong_thu_muc(tep: DuongDan, thu_muc: DuongDan) -> bool:
    """`tep` có nằm trong `thu_muc` không — so DANH TÍNH thư mục (`samefile`), không so chuỗi.

    So chuỗi lọt khi cùng một thư mục có hai tên: trên macOS (hệ tệp không phân biệt hoa/thường)
    «/users/…» và «/Users/…» là một, mà `Path.resolve()` không đổi chữ hoa/thường. Thư mục cha chưa
    tồn tại (sẽ được tạo lúc ghi) thì bỏ qua, xét tiếp cấp trên."""
    goc = Path(thu_muc)
    for cha in _tuyet_doi(tep).parents:
        try:
            if cha.samefile(goc):
                return True
        except OSError:
            continue
    return False
