"""Chốt canh: tiến trình pytest KHÔNG được ghi vào thư mục dữ liệu THẬT của cây (`data/`).

VÌ SAO — đo 30/09/2026 trên một bản clone sạch (6.446 test): mỗi lượt `pytest` để lại trong `data/` của chính cây đang
chạy 35 payload GIẢ ở `data/raw/{core,scopus,epistemonikos}/` (test thay `client.http.get_json` bằng hàm giả nhưng
`SourceClient.save_raw()` thật vẫn chạy), 5 tệp `processed/pipeline_*.json`, 4 tệp `exports/*_<ngày>.*` (đè lên bản
xuất thật cùng ngày) và một lô `tiktok/<giờ>-tuso/`. Chạy trong cây chính (OneDrive) thì chúng lẫn vào kho
`data/raw/` mà CLAUDE.md dùng làm bằng chứng đo.

HAI LỚP, tách theo điều ĐO ĐƯỢC:
  1. `CanhGhi` + móc audit (PEP 578): ghi lại mọi lần CHÍNH tiến trình này mở tệp để ghi / đổi tên / xoá dưới thư mục
     được canh. Đây là SỰ KIỆN, không suy đoán: biết đúng test nào, đường dẫn nào, và không bị nhiễu khi một tiến
     trình khác (lượt quét thật, dashboard) cũng đang ghi vào cùng thư mục.
  2. `chup()` / `so_sanh()`: so danh sách tệp lúc đăng ký ↔ cuối phiên. Bắt được cả tiến trình CON của test, nhưng
     KHÔNG biết ai ghi — nên phần không quy được cho tiến trình này chỉ là «không quy được», không phải «test sai»
     (tests/conftest.py chỉ coi là lỗi ở chế độ kín MRAQ_OFFLINE_CI=1, nơi không có tiến trình nào khác).

Cố ý KHÔNG chặn thao tác ghi (móc chỉ ghi sổ): ném lỗi từ móc audit làm hỏng chính lời gọi đang được canh, mà mã
connector lại bọc `except Exception`/`except OSError` quanh chỗ ghi ⇒ lỗi bị nuốt, test vẫn xanh. Ghi sổ rồi để
conftest đánh ĐỎ đúng test đó lúc teardown thì không ai nuốt được.

Thuần thư viện chuẩn; chạy được trên macOS, Linux, Windows (đường dẫn so qua realpath + normcase).
"""
from __future__ import annotations

import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

NGOAI_TEST = "<ngoài test: lúc import/thu thập hoặc fixture phạm vi rộng>"

# Cờ mở tệp có nghĩa «sẽ ghi hoặc tạo». Dùng hằng os.O_* của chính nền tảng: giá trị bit khác nhau giữa macOS, Linux
# và Windows (vd 0x4 là O_NONBLOCK trên macOS — shutil.rmtree mở THƯ MỤC bằng cờ đó, không phải ghi).
_CO_GHI = os.O_WRONLY | os.O_RDWR | os.O_APPEND | os.O_CREAT | os.O_TRUNC
_CHE_DO_GHI = frozenset("wax+")

# Sự kiện audit ứng với việc TẠO / SỬA / XOÁ TỆP → các cặp (chỉ số tham số đường dẫn, chỉ số tham số dir_fd hoặc None).
# Không có os.mkdir/os.rmdir: chốt canh TỆP, và `mkdir(exist_ok=True)` trên thư mục đã có vẫn phát sự kiện dù không
# đổi gì (save_raw, ensure_dirs gọi như thế ở mọi lượt).
_SU_KIEN: Dict[str, Tuple[Tuple[int, Optional[int]], ...]] = {
    "open": ((0, None),),                # builtin open / Path.write_text / os.open — chỉ tính khi mở để GHI
    "os.rename": ((0, 2), (1, 3)),       # os.rename / os.replace; dời RA khỏi kho cũng là làm mất tệp của kho
    "os.remove": ((0, 1),),              # os.remove / os.unlink / Path.unlink
    "os.truncate": ((0, None),),
    "os.utime": ((0, 3),),               # Path.touch() trên tệp đã có
    "os.link": ((1, 3),),
    "os.symlink": ((1, 2),),
    "shutil.rmtree": ((0, 1),),          # bên trong rmtree xoá bằng dir_fd nên phải bắt ngay ở sự kiện gốc
}

# Tệp do hệ điều hành tự sinh khi người dùng mở thư mục — không phải dữ liệu, không do test ghi.
_TEP_HE_THONG = frozenset({".DS_Store", "Thumbs.db", "desktop.ini"})


@dataclass(frozen=True)
class ViPham:
    """Một lần tiến trình này ghi/đổi tên/xoá tệp dưới thư mục được canh."""

    test: str        # nodeid đang chạy lúc đó, hoặc NGOAI_TEST
    su_kien: str     # tên sự kiện audit: "open", "os.rename"…
    tuong_doi: str   # đường dẫn tương đối dưới thư mục được canh, dấu «/»; "." = chính thư mục đó


def _chuan_hoa(duong: Any, theo_lien_ket: bool) -> Optional[str]:
    """Đường dẫn tuyệt đối đã chuẩn hoá để so tiền tố; None nếu không phải đường dẫn (vd mở theo file descriptor).

    `theo_lien_ket=False` (đổi tên, xoá, tạo liên kết): thao tác tác động lên CHÍNH mục đó chứ không lên đích của
    symlink, nên chỉ giải thư mục cha — giữ nguyên tên cuối."""
    try:
        chuoi = os.fsdecode(duong)  # str | bytes | PathLike; số nguyên (file descriptor) ⇒ TypeError
        if theo_lien_ket:
            that = os.path.realpath(chuoi)
        else:
            tuyet_doi = os.path.abspath(chuoi)
            that = os.path.join(os.path.realpath(os.path.dirname(tuyet_doi)), os.path.basename(tuyet_doi))
    except (TypeError, ValueError, OSError):
        # không phải đường dẫn, có byte rỗng, hoặc thư mục hiện hành đã bị xoá — chính thao tác đó cũng sẽ thất bại
        return None
    return os.path.normcase(that)


def _mo_de_ghi(tham_so: Sequence[Any]) -> bool:
    """Sự kiện `open(path, mode, flags)`: True nếu mở để ghi/tạo. Ưu tiên `flags` (luôn có); `mode` chỉ là dự phòng."""
    co = tham_so[2] if len(tham_so) > 2 else None
    if isinstance(co, int):
        return bool(co & _CO_GHI)
    che_do = tham_so[1] if len(tham_so) > 1 else None
    return isinstance(che_do, str) and bool(_CHE_DO_GHI & set(che_do))


class CanhGhi:
    """Sổ ghi mọi lần tiến trình này ghi vào `goc`, trừ phần miễn trừ đã khai.

    `mien_tru_thu_muc` / `mien_tru_tep`: đường dẫn tương đối dưới `goc`, viết bằng dấu «/». Mỗi miễn trừ là một lỗ
    ĐÃ BIẾT — khai kèm lý do ở nơi dựng (tests/conftest.py), không thêm để «cho hết đỏ»."""

    def __init__(self, goc: Path, mien_tru_thu_muc: Iterable[str] = (), mien_tru_tep: Iterable[str] = ()) -> None:
        self.goc = Path(goc)
        self._goc = os.path.normcase(os.path.realpath(str(goc)))
        self._tien_to = self._goc + os.sep
        self._mien_thu_muc = tuple(os.path.normcase(d.replace("/", os.sep)) for d in mien_tru_thu_muc)
        self._mien_tep = frozenset(os.path.normcase(t.replace("/", os.sep)) for t in mien_tru_tep)
        self.test_dang_chay = NGOAI_TEST
        self.vi_pham: List[ViPham] = []       # toàn bộ; CHỈ nối thêm (móc audit có thể chạy ở luồng khác)
        self._da_bao: set = set()             # chỉ số trong `vi_pham` đã gắn vào báo cáo của một test
        self.loi_noi_bo = 0                   # số lần chính chốt canh gặp lỗi ⇒ «không đo được», không phải «sạch»
        self.anh_dau: Dict[str, Tuple[int, int]] = {}
        self.anh_dau_du = False

    @property
    def cho_bao(self) -> List[ViPham]:
        """Vi phạm chưa gắn vào báo cáo của test nào (lúc import/thu thập, fixture phạm vi rộng…)."""
        return [vp for i, vp in enumerate(self.vi_pham) if i not in self._da_bao]

    # ── miễn trừ ────────────────────────────────────────────────────────────
    def duoc_mien(self, tuong_doi: str) -> bool:
        td = os.path.normcase(tuong_doi.replace("/", os.sep))
        if td in self._mien_tep:
            return True
        return any(td == d or td.startswith(d + os.sep) for d in self._mien_thu_muc)

    # ── phần thuần: một sự kiện có phải là ghi vào thư mục được canh không ─────
    def tuong_doi(self, duong: Any, theo_lien_ket: bool = True, ca_thu_muc_cha: bool = False) -> Optional[str]:
        """Đường dẫn tương đối (dấu «/») nếu `duong` nằm dưới thư mục được canh và không được miễn; ngược lại None.

        `ca_thu_muc_cha=True` (xoá cả cây): xoá một thư mục CHA của thư mục được canh cũng là xoá nó ⇒ trả "."."""
        chuan = _chuan_hoa(duong, theo_lien_ket)
        if chuan is None:
            return None
        if chuan == self._goc or (ca_thu_muc_cha and self._tien_to.startswith(chuan.rstrip(os.sep) + os.sep)):
            return "."
        if not chuan.startswith(self._tien_to):
            return None
        td = chuan[len(self._tien_to):]
        if self.duoc_mien(td):
            return None
        return td.replace(os.sep, "/")

    def xet(self, su_kien: str, tham_so: Sequence[Any]) -> List[str]:
        """Các đường dẫn tương đối bị ghi/xoá theo sự kiện audit này (rỗng = không liên quan)."""
        cap = _SU_KIEN.get(su_kien)
        if cap is None:
            return []
        la_open = su_kien == "open"
        if la_open and not _mo_de_ghi(tham_so):
            return []
        ket_qua: List[str] = []
        for i_duong, i_dir_fd in cap:
            if i_duong >= len(tham_so):
                continue
            if i_dir_fd is not None and i_dir_fd < len(tham_so) and tham_so[i_dir_fd] not in (None, -1):
                continue  # đường dẫn tương đối theo dir_fd: không quy được về đường dẫn tuyệt đối
            td = self.tuong_doi(tham_so[i_duong], theo_lien_ket=la_open, ca_thu_muc_cha=(su_kien == "shutil.rmtree"))
            if td is not None:
                ket_qua.append(td)
        return ket_qua

    # ── phần ghi sổ (gọi từ móc audit) ──────────────────────────────────────
    def nhan(self, su_kien: str, tham_so: Sequence[Any]) -> None:
        """KHÔNG BAO GIỜ ném: lỗi thoát ra từ móc audit sẽ thành lỗi của chính thao tác đang được canh. Lỗi nội bộ
        được ĐẾM để cuối phiên báo «không đo được» (fail-closed) thay vì im lặng coi là sạch."""
        try:
            for td in self.xet(su_kien, tham_so):
                self.vi_pham.append(ViPham(self.test_dang_chay, su_kien, td))
        except Exception:  # noqa: BLE001
            self.loi_noi_bo += 1

    def rut_cua_test(self, nodeid: str) -> List[ViPham]:
        """Lấy (và đánh dấu đã báo) các vi phạm xảy ra trong lúc test `nodeid` chạy — mỗi vi phạm chỉ trả một lần."""
        chi_so = [i for i, vp in enumerate(self.vi_pham) if vp.test == nodeid and i not in self._da_bao]
        self._da_bao.update(chi_so)
        return [self.vi_pham[i] for i in chi_so]

    # ── lớp 2: so danh sách tệp ─────────────────────────────────────────────
    def chup_dau(self) -> None:
        self.anh_dau, self.anh_dau_du = chup(self.goc, self)

    def khac_biet_khong_quy_duoc(self) -> Tuple[Dict[str, List[str]], bool]:
        """(khác biệt của thư mục so với lúc `chup_dau()` mà móc audit KHÔNG thấy tiến trình này gây ra, đo đủ?).

        Phần móc đã thấy thì đã nằm trong `vi_pham` — không báo hai lần."""
        anh_cuoi, du = chup(self.goc, self)
        if not (du and self.anh_dau_du):
            return {"moi": [], "doi": [], "mat": []}, False
        da_thay = {vp.tuong_doi for vp in self.vi_pham}
        khac = so_sanh(self.anh_dau, anh_cuoi)
        return {loai: [p for p in ds if p not in da_thay] for loai, ds in khac.items()}, True


@dataclass
class TongKet:
    """Kết luận cuối phiên của các chốt canh."""

    do: List[str]        # dòng báo LỖI ⇒ phiên pytest phải đỏ
    ghi_chu: List[str]   # «không quy được» / «không đo được» ⇒ in ra, KHÔNG làm đỏ phiên


def dong_vi_pham(ds: Sequence[ViPham], kem_test: bool, toi_da: int = 20) -> List[str]:
    """Các dòng liệt kê vi phạm để in; quá `toi_da` thì nêu số còn lại chứ không cắt im lặng."""
    dong = [f"    • {vp.su_kien}: {vp.tuong_doi}" + (f"   ← {vp.test}" if kem_test else "") for vp in ds[:toi_da]]
    if len(ds) > toi_da:
        dong.append(f"    … và {len(ds) - toi_da} lần nữa")
    return dong


def tong_ket(cac: Iterable[CanhGhi], nghiem: bool, toi_da: int = 20) -> TongKet:
    """Gom kết luận cuối phiên.

    Đỏ khi: (a) chốt canh tự gặp lỗi (không đo được ⇒ fail-closed); (b) tiến trình này ghi vào thư mục được canh mà
    chưa test nào nhận (lúc import/thu thập, fixture phạm vi rộng). Danh sách tệp đổi mà móc audit KHÔNG thấy tiến
    trình này gây ra: `nghiem=True` (phiên kín, không có tiến trình nào khác) ⇒ đỏ; ngược lại chỉ là ghi chú vì
    không biết ai ghi — tiến trình con của một test, hay một lượt quét thật đang chạy cùng lúc."""
    kq = TongKet(do=[], ghi_chu=[])
    for canh in cac:
        if canh.loi_noi_bo:
            kq.do.append(f"{canh.goc}: chốt canh gặp lỗi nội bộ {canh.loi_noi_bo} lần — KHÔNG ĐO ĐƯỢC, "
                         "không được coi là sạch.")
        cho_bao = canh.cho_bao
        if cho_bao:
            kq.do.append(f"{canh.goc}: tiến trình pytest đã ghi/đổi tên/xoá {len(cho_bao)} lần "
                         "mà không gắn được vào một test đã báo đỏ:")
            kq.do.extend(dong_vi_pham(cho_bao, kem_test=True, toi_da=toi_da))
        khac, du = canh.khac_biet_khong_quy_duoc()
        dich = kq.do if nghiem else kq.ghi_chu
        if not du:
            dich.append(f"{canh.goc}: thiếu ảnh chụp danh sách tệp (quét vượt thời hạn) — KHÔNG so được đầu↔cuối "
                        "phiên (không đo được, khác «không có gì đổi»).")
            continue
        tat_ca = [(nhan, p) for nhan, loai in (("mới", "moi"), ("đổi", "doi"), ("mất", "mat")) for p in khac[loai]]
        if not tat_ca:
            continue
        duoi = "." if nghiem else "; phiên kín MRAQ_OFFLINE_CI=1 coi đây là lỗi."
        dich.append(f"{canh.goc}: {len(tat_ca)} tệp mới/đổi/mất so với đầu phiên mà tiến trình pytest này KHÔNG mở "
                    "để ghi — do tiến trình CON của một test, hoặc một tiến trình khác chạy cùng lúc trên cây này "
                    "(lượt quét thật, dashboard)" + duoi)
        dich.extend(f"    • {nhan}: {p}" for nhan, p in tat_ca[:toi_da])
        if len(tat_ca) > toi_da:
            dich.append(f"    … và {len(tat_ca) - toi_da} tệp nữa")
    return kq


def chup(goc: Path, canh: Optional[CanhGhi] = None, han_giay: float = 20.0) -> Tuple[Dict[str, Tuple[int, int]], bool]:
    """Ảnh chụp {đường dẫn tương đối: (kích thước, mtime_ns)} của mọi tệp dưới `goc`, bỏ phần `canh` miễn trừ.

    Trả thêm cờ `đủ`: False nếu quét quá `han_giay` (ổ mạng/OneDrive đang tải) ⇒ ảnh THIẾU, không được dùng để kết
    luận — «không đo được» khác «không có gì đổi»."""
    anh: Dict[str, Tuple[int, int]] = {}
    goc_chuoi = str(goc)
    bat_dau = time.monotonic()
    for thu_muc, _cac_con, cac_tep in os.walk(goc_chuoi):
        if time.monotonic() - bat_dau > han_giay:
            return anh, False
        tuong_doi_tm = os.path.relpath(thu_muc, goc_chuoi)
        tien_to = "" if tuong_doi_tm == os.curdir else tuong_doi_tm.replace(os.sep, "/") + "/"
        for ten in cac_tep:
            td = tien_to + ten
            if ten in _TEP_HE_THONG or (canh is not None and canh.duoc_mien(td)):
                continue
            try:
                st = os.lstat(os.path.join(thu_muc, ten))
            except OSError:
                continue
            anh[td] = (st.st_size, st.st_mtime_ns)
    return anh, True


def so_sanh(truoc: Dict[str, Tuple[int, int]], sau: Dict[str, Tuple[int, int]]) -> Dict[str, List[str]]:
    """Khác biệt giữa hai ảnh chụp: tệp `moi`, tệp `doi` (kích thước hoặc mtime), tệp `mat`."""
    return {
        "moi": sorted(p for p in sau if p not in truoc),
        "doi": sorted(p for p in sau if p in truoc and sau[p] != truoc[p]),
        "mat": sorted(p for p in truoc if p not in sau),
    }


# ── móc audit: MỘT móc cho cả tiến trình, phát cho mọi chốt đã đăng ký ─────────
_CAC_CANH: List[CanhGhi] = []
_da_gan_moc = False


def _moc_audit(su_kien: str, tham_so: Tuple[Any, ...]) -> None:
    try:
        if su_kien not in _SU_KIEN:  # đường nhanh: import, exec, socket… dừng ngay ở đây
            return
        for canh in tuple(_CAC_CANH):
            canh.nhan(su_kien, tham_so)
    except Exception:  # noqa: BLE001 — vd biến module đã bị dọn lúc trình thông dịch tắt
        return


def dang_ky(canh: CanhGhi) -> CanhGhi:
    """Bắt đầu canh: chụp ảnh đầu, đưa vào danh sách, gắn móc audit (một lần — móc audit không gỡ được)."""
    global _da_gan_moc
    canh.chup_dau()
    if not any(c is canh for c in _CAC_CANH):
        _CAC_CANH.append(canh)
    if not _da_gan_moc:
        sys.addaudithook(_moc_audit)
        _da_gan_moc = True
    return canh


def huy_dang_ky(canh: CanhGhi) -> None:
    _CAC_CANH[:] = [c for c in _CAC_CANH if c is not canh]


def cac_canh() -> Tuple[CanhGhi, ...]:
    return tuple(_CAC_CANH)
