"""Chốt canh: tiến trình pytest KHÔNG được chạm thư mục bí mật THẬT của máy (`~/.ebm-secrets`) — kèm khoá ký GIẢ.

VÌ SAO — đo 05/10/2026 trên Mac của bác sĩ (bộ test đầy đủ ở 6503375; đầu dò móc audit CHẶN trước khi mở nên không
byte nào của khoá được đọc): `tools/gate_contract.py::_base_key_path()` rơi về `~/.ebm-secrets/gate_approval_key`
(HMAC) và `_ed_private_dir()` rơi về `~/.ebm-secrets/` (khoá riêng Ed25519 `gate_ed25519_<VAI>.key`) khi biến
EBM_GATE_KEY_PATH không được đặt — mà trước bản vá này tests/conftest.py không đặt. Hệ quả: mỗi lượt pytest trên máy
có khoá đọc khoá riêng THẬT của bác sĩ để ký sổ cái tổng hợp tạm của test. CLAUDE.md §0.5: agent không đọc/chép khoá
riêng. Số đo chi tiết: audit/nhat-ky/ của repo gốc.

HAI LỚP:
  1. Chữa gốc — `tao_khoa_gia()`: tests/conftest.py đặt EBM_GATE_KEY_PATH trỏ khoá GIẢ trong thư mục tạm cho cả phiên
     (lúc import, trước khi thu thập test, tiến trình con kế thừa) và một khoá giả MỚI cho từng test (không lây khoá
     vai trò/Ed25519 do test trước tạo cạnh khoá giả). Khoá vai trò `<khoá>_<NHÓM>` và khoá Ed25519 nằm CẠNH khoá giả
     (gate_contract tự suy ra như vậy) nên test nào tạo khoá vai trò thì tạo trong thư mục tạm.
  2. Lưới đỡ — `CanhBiMat` + móc audit (PEP 578): lần sau mã hay test đi vòng (đường dẫn viết cứng
     `Path.home() / ".ebm-secrets"`, xoá biến môi trường…) thì test đó ĐỎ, và khoá thật vẫn KHÔNG bị đọc.

KHÁC chốt canh dữ liệu thật (canh_ghi_du_lieu_that.py) ở hai điểm, có chủ ý:
  • Canh cả ĐỌC: mở tệp ở mọi chế độ, liệt kê, sao chép — không chỉ ghi/đổi tên/xoá.
  • CHẶN, không chỉ ghi sổ: móc ném `ChanBiMat` (một PermissionError) TRƯỚC khi hệ điều hành mở tệp. Mã ký bọc
    `except OSError` (vd gate_contract._read_key) sẽ nuốt lỗi đó rồi chạy tiếp như máy chưa có khoá — nên móc VẪN ghi
    sổ trước khi ném, và conftest đánh ĐỎ đúng test lúc teardown: nuốt lỗi không làm mất dấu.

Miễn trừ là lỗ ĐÃ BIẾT, khai ở tests/conftest.py kèm lý do (hiện chỉ có: ĐỌC tệp biến môi trường app/config.py nạp
lúc import). Miễn trừ chỉ áp cho ĐỌC — ghi/xoá/đổi tên tệp đó vẫn bị chặn.

Giới hạn (nói thẳng): móc audit chỉ thấy CHÍNH tiến trình pytest. Tiến trình con được che bằng EBM_GATE_KEY_PATH kế
thừa từ os.environ, không bằng móc — con dựng `env=` từ đầu mà bỏ biến đó (và PYTEST_CURRENT_TEST) thì gate_contract
trong con dùng khoá thật mà chốt này không thấy. So đường dẫn bằng abspath, không theo symlink: một symlink trỏ vào
thư mục bí mật thì không thấy. Mục tiêu là bắt lỗi VÔ Ý, không phải chống cố ý (agent có quyền đọc mọi tệp).

Thuần thư viện chuẩn; chạy được trên macOS, Linux, Windows.
"""
from __future__ import annotations

import os
import secrets
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from tests.canh_ghi_du_lieu_that import NGOAI_TEST, ViPham, _mo_de_ghi, dong_vi_pham

# Chốt NGAY lúc import (tests/conftest.py import module này trước khi thu thập test), nên test nào sau đó đổi HOME
# cũng không kéo chốt đi chỗ khác.
THU_MUC_BI_MAT_THAT = Path.home() / ".ebm-secrets"

# Tên tệp khoá chung — khớp `tools/gate_contract.py::_DEFAULT_KEY_PATH.name` (test canh gác đối chiếu).
TEN_KHOA_GIA = "gate_approval_key"

# Sự kiện audit → các cặp (chỉ số tham số đường dẫn, chỉ số tham số dir_fd hoặc None). Đường dẫn tương đối theo
# dir_fd thì không quy được — nhưng muốn có dir_fd của thư mục bí mật phải MỞ nó trước, và lần mở đó đã bị bắt.
_SU_KIEN: Dict[str, Tuple[Tuple[int, Optional[int]], ...]] = {
    "open": ((0, None),),                       # builtin open / Path.read_text / os.open — MỌI chế độ, kể cả đọc
    "os.listdir": ((0, None),),
    "os.scandir": ((0, None),),                 # cả Path.glob / glob.glob / os.walk
    "shutil.copyfile": ((0, None), (1, None)),
    "shutil.copytree": ((0, None), (1, None)),
    "os.rename": ((0, 2), (1, 3)),              # os.rename / os.replace
    "os.remove": ((0, 1),),                     # os.remove / os.unlink / Path.unlink
    "os.truncate": ((0, None),),
    "os.utime": ((0, 3),),
    "os.link": ((0, 2), (1, 3)),                # liên kết cứng TỪ một khoá ra ngoài cũng là làm lộ khoá
    "os.symlink": ((1, 2),),
    "os.chmod": ((0, 2),),
    "os.chown": ((0, 3),),
    "os.mkdir": ((0, 2),),
    "os.rmdir": ((0, 1),),
    "shutil.rmtree": ((0, 1),),                 # xoá một thư mục CHA (vd HOME) cũng là xoá thư mục bí mật
}


class ChanBiMat(PermissionError):
    """Móc audit ném lỗi này để CHẶN một thao tác chạm thư mục bí mật thật, trước khi hệ điều hành kịp làm."""


def tao_khoa_gia(thu_muc: Path) -> Path:
    """Tạo khoá ký HMAC GIẢ `<thu_muc>/gate_approval_key` (ngẫu nhiên, quyền 600) và trả đường dẫn.

    Ngẫu nhiên MỖI lần: chữ ký của test này không bao giờ xác minh được bằng khoá của test khác. Không ghi đè tệp đã
    có (O_EXCL) — gọi nhầm vào một thư mục khoá thật thì nổ, không đè."""
    thu_muc.mkdir(parents=True, exist_ok=True)
    khoa = thu_muc / TEN_KHOA_GIA
    fd = os.open(khoa, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(f"pytest-khoa-gia-khong-phai-khoa-that-{secrets.token_hex(16)}\n")
    return khoa


class CanhBiMat:
    """Sổ ghi (và chặn) mọi lần tiến trình này chạm `goc`, trừ phần ĐỌC đã khai miễn trừ.

    `mien_tru_doc`: đường dẫn tương đối dưới `goc`, dấu «/». Mỗi miễn trừ là một lỗ ĐÃ BIẾT — khai kèm lý do ở nơi
    dựng (tests/conftest.py), không thêm để «cho hết đỏ»."""

    def __init__(self, goc: Path, mien_tru_doc: Iterable[str] = ()) -> None:
        self.goc = Path(goc)
        chuoi = str(goc)
        # Cả dạng viết (HOME/.ebm-secrets) lẫn dạng đã giải symlink (thư mục bí mật có thể là symlink sang ổ khác).
        self._cac_goc = tuple(dict.fromkeys(
            os.path.normcase(p) for p in (os.path.abspath(chuoi), os.path.realpath(chuoi))))
        self._mien_doc = frozenset(os.path.normcase(t.replace("/", os.sep)) for t in mien_tru_doc)
        self.test_dang_chay = NGOAI_TEST
        self.vi_pham: List[ViPham] = []       # toàn bộ; CHỈ nối thêm (móc audit có thể chạy ở luồng khác)
        self._da_bao: set = set()             # chỉ số trong `vi_pham` đã gắn vào báo cáo của một test
        self.loi_noi_bo = 0                   # số lần chính chốt canh gặp lỗi ⇒ «không đo được», không phải «sạch»

    @property
    def cho_bao(self) -> List[ViPham]:
        """Lần chạm chưa gắn vào báo cáo của test nào (lúc import/thu thập, fixture phạm vi rộng…)."""
        return [vp for i, vp in enumerate(self.vi_pham) if i not in self._da_bao]

    # ── phần thuần: một sự kiện có chạm thư mục bí mật không ──────────────────────
    def tuong_doi(self, duong: Any, ca_thu_muc_cha: bool = False) -> Optional[str]:
        """Đường dẫn tương đối (dấu «/», "." = chính thư mục) nếu `duong` nằm dưới thư mục được canh; ngược lại None."""
        try:
            tuyet_doi = os.path.normcase(os.path.abspath(os.fsdecode(duong)))
        except (TypeError, ValueError, OSError):
            return None   # file descriptor, byte rỗng, thư mục hiện hành đã bị xoá — không phải đường dẫn quy được
        for goc in self._cac_goc:
            if tuyet_doi == goc:
                return "."
            if tuyet_doi.startswith(goc + os.sep):
                return tuyet_doi[len(goc) + 1:].replace(os.sep, "/")
            if ca_thu_muc_cha and (goc + os.sep).startswith(tuyet_doi.rstrip(os.sep) + os.sep):
                return "."
        return None

    def xet(self, su_kien: str, tham_so: Sequence[Any]) -> List[str]:
        """Các đường dẫn tương đối bị chạm theo sự kiện audit này (rỗng = không liên quan hoặc được miễn)."""
        cap = _SU_KIEN.get(su_kien)
        if cap is None:
            return []
        ket_qua: List[str] = []
        for i_duong, i_dir_fd in cap:
            if i_duong >= len(tham_so):
                continue
            if i_dir_fd is not None and i_dir_fd < len(tham_so) and tham_so[i_dir_fd] not in (None, -1):
                continue
            td = self.tuong_doi(tham_so[i_duong], ca_thu_muc_cha=(su_kien == "shutil.rmtree"))
            if td is None:
                continue
            # Miễn trừ chỉ cho ĐỌC thuần (xét chế độ mở sau cùng: phần lớn sự kiện open nằm ngoài thư mục canh).
            if (su_kien == "open" and not _mo_de_ghi(tham_so)
                    and os.path.normcase(td.replace("/", os.sep)) in self._mien_doc):
                continue
            ket_qua.append(td)
        return ket_qua

    # ── phần ghi sổ (gọi từ móc audit) ──────────────────────────────────────
    def nhan(self, su_kien: str, tham_so: Sequence[Any]) -> bool:
        """Ghi sổ; True nếu thao tác phải bị CHẶN. Không bao giờ ném — lỗi nội bộ được ĐẾM để cuối phiên báo «không
        đo được» (đỏ) thay vì im lặng coi là sạch."""
        try:
            cac = self.xet(su_kien, tham_so)
            if not cac:
                return False
            nhan_su_kien = f"open ({'ghi' if _mo_de_ghi(tham_so) else 'đọc'})" if su_kien == "open" else su_kien
            for td in cac:
                self.vi_pham.append(ViPham(self.test_dang_chay, nhan_su_kien, td))
            return True
        except Exception:  # noqa: BLE001
            self.loi_noi_bo += 1
            return False

    def rut_cua_test(self, nodeid: str) -> List[ViPham]:
        """Lấy (và đánh dấu đã báo) các lần chạm xảy ra trong lúc test `nodeid` chạy — mỗi lần chỉ trả một lần."""
        chi_so = [i for i, vp in enumerate(self.vi_pham) if vp.test == nodeid and i not in self._da_bao]
        self._da_bao.update(chi_so)
        return [self.vi_pham[i] for i in chi_so]


def tong_ket(cac: Iterable[CanhBiMat], toi_da: int = 20) -> List[str]:
    """Dòng LỖI cuối phiên (rỗng = sạch): chốt tự gặp lỗi (không đo được ⇒ fail-closed) hoặc có lần chạm mà chưa gắn
    được vào một test đã báo đỏ (lúc import/thu thập, fixture phạm vi rộng)."""
    do: List[str] = []
    for canh in cac:
        if canh.loi_noi_bo:
            do.append(f"{canh.goc}: chốt canh bí mật gặp lỗi nội bộ {canh.loi_noi_bo} lần — KHÔNG ĐO ĐƯỢC, "
                      "không được coi là sạch.")
        cho_bao = canh.cho_bao
        if cho_bao:
            do.append(f"{canh.goc}: tiến trình pytest đã chạm thư mục bí mật {len(cho_bao)} lần (đã CHẶN) mà không "
                      "gắn được vào một test đã báo đỏ:")
            do.extend(dong_vi_pham(cho_bao, kem_test=True, toi_da=toi_da))
    return do


# ── móc audit: MỘT móc cho cả tiến trình, phát cho mọi chốt đã đăng ký ─────────
_CAC_CANH: List[CanhBiMat] = []
_da_gan_moc = False


def _moc_audit(su_kien: str, tham_so: Tuple[Any, ...]) -> None:
    chan = False
    try:
        if su_kien not in _SU_KIEN:  # đường nhanh: import, exec, socket… dừng ngay ở đây
            return
        for canh in tuple(_CAC_CANH):
            if canh.nhan(su_kien, tham_so):
                chan = True
    except Exception:  # noqa: BLE001 — vd biến module đã bị dọn lúc trình thông dịch tắt
        return
    if chan:
        raise ChanBiMat(
            f"chốt canh bí mật: CHẶN «{su_kien}» dưới thư mục bí mật thật — bộ test chỉ được dùng khoá GIẢ "
            "(EBM_GATE_KEY_PATH do tests/conftest.py đặt). Xem tests/canh_bi_mat_that.py.")


def dang_ky(canh: CanhBiMat) -> CanhBiMat:
    """Bắt đầu canh: đưa vào danh sách, gắn móc audit (một lần — móc audit không gỡ được)."""
    global _da_gan_moc
    if not any(c is canh for c in _CAC_CANH):
        _CAC_CANH.append(canh)
    if not _da_gan_moc:
        sys.addaudithook(_moc_audit)
        _da_gan_moc = True
    return canh


def huy_dang_ky(canh: CanhBiMat) -> None:
    _CAC_CANH[:] = [c for c in _CAC_CANH if c is not canh]


def cac_canh() -> Tuple[CanhBiMat, ...]:
    return tuple(_CAC_CANH)
