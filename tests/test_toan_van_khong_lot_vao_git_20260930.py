"""Toàn văn CÓ BẢN QUYỀN tải về không được rơi vào chỗ git nhìn thấy — chốt 30/09/2026.

Repo này CÔNG KHAI. Đo 30/09/2026: `WileyTdmClient` tải PDF thật vào thư mục mặc định
`downloads_wiley_tdm/` (tương đối so với thư mục đang đứng) mà `.gitignore` không có luật
nào bắt — `git status` hiện `?? downloads_wiley_tdm/`, một lần `git add -A` là đưa PDF của
nhà xuất bản vào lịch sử công khai. Tệp này canh ba việc:

  1. Thư mục tải mặc định của Wiley TDM bị `.gitignore` bắt ở MỌI cấp thư mục — đọc tên
     thư mục từ chính hằng số mà mã dùng, hỏi `git check-ignore`, rồi tải thử bằng thư
     viện `wiley-tdm` THẬT (chỉ thay biên mạng) và xem git có thấy tệp PDF không.
  2. Cache HTTP — nơi DUY NHẤT nội dung toàn văn của các connector guideline chạm đĩa
     (toàn văn PMC và trang mục lục đi qua `HttpClient.get_text`) — cũng bị bắt.
  3. Bốn connector guideline (GOLD · GINA · BTS · PMC) và module dùng chung KHÔNG tự ghi
     tệp: PDF đi qua `get_bytes` chỉ nằm trong bộ nhớ. Thêm lời gọi ghi đĩa vào đó thì
     ca kiểm cuối tệp đỏ, buộc người sửa xét nơi ghi có nằm ngoài tầm nhìn của git không.

Bổ sung cùng ngày — bốn lỗ mà ba việc trên chưa rào (đo ngoại tuyến với wiley-tdm 1.2.0):

  4. Hàm hỏi git dùng chung `app/utils/tam_nhin_git.py`: ngoài cây git · bị ignore · git thấy ·
     không đo được. Chỉ luật đi theo KHO được tính; luật ignore riêng của máy thì không.
  5. Thư mục tải Wiley TỰ ĐẶT (`WILEY_TDM_DOWNLOAD_DIR`, `download_dir=`) nằm ở chỗ git thấy thì
     `WileyTdmClient` từ chối — xét thư mục THẬT mà thư viện ghi, vì thư viện đổi tên có dấu chấm
     («wiley.pdfs») thành thư mục MẸ.
  6. Đứt mạng giữa chừng để lại tệp ghi dở: lượt sau thư viện trả `EXISTING_FILE` mà không gọi
     mạng; kết quả của ta không được báo «thành công» cho một PDF cụt.
  7. Rào `tools/toan_van_guideline.py --luu` so DANH TÍNH thư mục chứ không so chuỗi (trên macOS
     «/users/…» và «/Users/…» là một), và từ chối cả đích nằm trong cây git khác mà git thấy.

Mục 5–6 chạy hai lần: với thư viện `wiley-tdm` THẬT (máy có cài; chỉ thay biên mạng) và với một
bản giả tối thiểu (CI không cài thư viện). Bản giả trôi khỏi thư viện thì một trong hai đỏ.

Luật ignore được đo trong một kho git TẠM chỉ mang đúng `.gitignore` của dự án, với cấu
hình git cô lập khỏi máy: luật ignore riêng của máy (`core.excludesFile`,
`~/.config/git/ignore`) không thể làm xanh giả khi `.gitignore` của dự án thiếu luật.
Không gọi mạng, không tải thật.
"""
from __future__ import annotations

import ast
import json
import os
import shutil
import subprocess
import sys
import types
from pathlib import Path
from typing import List, Optional
from urllib.parse import quote

import pytest
import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.config import BASE_DIR, settings  # noqa: E402
from app.sources.wiley_tdm import THU_MUC_TAI_MAC_DINH, WileyTdmClient  # noqa: E402
from app.utils import http as http_mod  # noqa: E402
from app.utils import tam_nhin_git as tng  # noqa: E402
from tools import toan_van_guideline as T  # noqa: E402

# Chụp lúc NẠP module (trước mọi monkeypatch): nhiều test khác vá `_CACHE_DIR` sang tmp_path.
_CACHE_DIR_THAT = http_mod._CACHE_DIR

_DOI = "10.1002/jcsm.70385"
_TEN_TEP_PDF = "10.1002-jcsm.70385.pdf"  # thư viện đổi «/» trong DOI thành «-»
_TOKEN_GIA = "00000000-0000-4000-8000-000000000000"  # đúng khuôn UUID mà thư viện đòi, không phải token thật


def _pdf_tron_ven(so_byte: int) -> bytes:
    """Nội dung dài đúng `so_byte` byte mang hai dấu mà mọi PDF trọn vẹn đều có: chữ ký «%PDF-» ở
    đầu và «%%EOF» ở cuối (đo 30/09/2026 trên 109 PDF thật có sẵn trên máy: cả 109 đều vậy, dấu
    «%%EOF» nằm trong 7 byte cuối). Nội dung tự chế, không phải bài báo nào."""
    dau, cuoi = b"%PDF-1.7\n", b"\nstartxref\n9\n%%EOF\n"
    assert so_byte >= len(dau) + len(cuoi)
    return dau + b"x" * (so_byte - len(dau) - len(cuoi)) + cuoi


def _khong_do_duoc(ly_do: str) -> None:
    """«Không đo được» không phải «đạt». Máy riêng: bỏ qua kèm lý do. Trên CI (luôn có git) thì
    là lỗi, để chốt không lặng lẽ biến mất."""
    if os.environ.get("GITHUB_ACTIONS") == "true" or os.environ.get("CI", "").lower() in ("true", "1"):
        pytest.fail(ly_do)
    pytest.skip(ly_do)


class _KhoGit:
    """Kho git tạm + môi trường git đã cô lập. Mọi câu hỏi «git có thấy không» đi qua đây."""

    def __init__(self, thu_muc: Path, env: dict) -> None:
        self.thu_muc = thu_muc
        self._env = env

    def _git(self, *doi_so: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", "-C", str(self.thu_muc), *doi_so],
            capture_output=True, text=True, env=self._env, timeout=60,
        )

    def bi_ignore(self, duong: str) -> bool:
        """`git check-ignore -q`: mã 0 = có luật ignore bắt, 1 = không luật nào bắt. Mã khác là
        phép đo hỏng — nổ ngay, không đọc thành «không bị ignore» hay «bị ignore».

        Cố ý không lấy mã thoát của `-v`: với luật phủ định («!mẫu») `-v` vẫn trả 0."""
        kq = self._git("check-ignore", "-q", "--no-index", "--", duong)
        assert kq.returncode in (0, 1), f"git check-ignore hỏng (mã {kq.returncode}): {kq.stderr}"
        return kq.returncode == 0

    def luat_khop(self, duong: str) -> str:
        """Dòng luật khớp (chỉ để đưa vào thông điệp khi ca kiểm đỏ)."""
        return self._git("check-ignore", "-v", "--no-index", "--", duong).stdout.strip() or "<không luật nào>"

    def tep_git_thay(self) -> List[str]:
        """Tệp chưa theo dõi mà KHÔNG bị ignore — đúng thứ `git add -A` sẽ cuốn vào."""
        kq = self._git("ls-files", "--others", "--exclude-standard")
        assert kq.returncode == 0, f"git ls-files hỏng (mã {kq.returncode}): {kq.stderr}"
        return sorted(kq.stdout.split())

    def tao_kho_khac(self, thu_muc: Path, luat_rieng_cua_kho: str = "") -> Path:
        """Một kho git tạm KHÁC, cùng môi trường cô lập. `luat_rieng_cua_kho` ghi vào
        `.git/info/exclude` của kho đó (luật không nằm trong cây làm việc)."""
        _khoi_tao_kho(thu_muc, self._env, luat_rieng_cua_kho)
        return thu_muc


def _khoi_tao_kho(thu_muc: Path, env: dict, luat_rieng_cua_kho: str = "") -> None:
    thu_muc.mkdir()
    kq = subprocess.run(["git", "init", "-q", str(thu_muc)], capture_output=True, text=True, env=env, timeout=60)
    assert kq.returncode == 0, f"git init hỏng: {kq.stderr}"
    # Kho mới sinh có thể nhận `info/exclude` từ thư mục mẫu của máy — ghi đè cho chắc.
    thong_tin = thu_muc / ".git" / "info"
    thong_tin.mkdir(exist_ok=True)
    (thong_tin / "exclude").write_text(luat_rieng_cua_kho, encoding="utf-8", newline="\n")


@pytest.fixture
def kho_git(tmp_path) -> _KhoGit:
    if shutil.which("git") is None:
        _khong_do_duoc("không có lệnh `git` — không đo được luật ignore")
    trong = tmp_path / "gitconfig-trong"
    trong.write_text("", encoding="utf-8", newline="\n")
    nha = tmp_path / "nha"
    nha.mkdir()
    # Bỏ mọi biến GIT_* thừa hưởng: chạy trong hook git thì GIT_DIR/GIT_INDEX_FILE trỏ vào kho
    # THẬT, và lệnh git bên dưới sẽ thao tác nhầm lên kho đó.
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith("GIT_")}
    env.update({
        "GIT_CONFIG_GLOBAL": str(trong), "GIT_CONFIG_SYSTEM": str(trong), "GIT_CONFIG_NOSYSTEM": "1",
        "HOME": str(nha), "USERPROFILE": str(nha), "XDG_CONFIG_HOME": str(nha / "xdg"),
        "GIT_TERMINAL_PROMPT": "0",
    })
    thu_muc = tmp_path / "kho"
    _khoi_tao_kho(thu_muc, env)
    shutil.copyfile(REPO_ROOT / ".gitignore", thu_muc / ".gitignore")
    return _KhoGit(thu_muc, env)


# ════════════════════════════════════════════════════════════════════════════
# 0. Đối chứng cho chính phép đo
# ════════════════════════════════════════════════════════════════════════════

def _ket_cuc_khi_khong_do_duoc() -> str:
    """Bắt tường minh cả hai ngoại lệ: để `Skipped` thoát ra ngoài thì chính ca kiểm gọi hàm này
    bị pytest ghi là «bỏ qua», và một lỗi ở `_khong_do_duoc` sẽ trôi qua mà không đỏ."""
    try:
        _khong_do_duoc("thử")
    except pytest.fail.Exception:
        return "do"
    except pytest.skip.Exception:
        return "bo_qua"
    return "khong_nem_gi"


def test_khong_co_git_thi_tren_ci_la_do_con_may_rieng_moi_bo_qua(monkeypatch):
    """Nhánh «không đo được» không được thành cửa thoát trên CI: ở đó luôn có git, thiếu git mà
    bỏ qua thì cả tệp chốt này lặng lẽ không chạy."""
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.delenv("CI", raising=False)
    assert _ket_cuc_khi_khong_do_duoc() == "do"
    monkeypatch.delenv("GITHUB_ACTIONS")
    monkeypatch.setenv("CI", "true")
    assert _ket_cuc_khi_khong_do_duoc() == "do"
    monkeypatch.delenv("CI")
    assert _ket_cuc_khi_khong_do_duoc() == "bo_qua"


def test_doi_chung_phep_do_phan_biet_duoc_tep_bi_ignore_va_khong(kho_git):
    """Nếu `bi_ignore` trả True với mọi đường dẫn thì các ca bên dưới xanh vô nghĩa. Mã nguồn
    connector KHÔNG bị ignore; `.env` thì có."""
    assert not kho_git.bi_ignore("app/sources/wiley_tdm.py")
    assert kho_git.bi_ignore(".env")


@pytest.fixture
def may_co_luat_ignore_rieng(monkeypatch, tmp_path) -> Path:
    """Giả một máy có luật ignore TOÀN CỤC bắt đúng thư mục tải, qua cả hai đường git nhận:
    `core.excludesFile` trong cấu hình toàn cục và `$XDG_CONFIG_HOME/git/ignore`."""
    may = tmp_path / "may-co-luat-rieng"
    (may / "xdg" / "git").mkdir(parents=True)
    luat = f"{THU_MUC_TAI_MAC_DINH}/\n"
    (may / "xdg" / "git" / "ignore").write_text(luat, encoding="utf-8", newline="\n")
    (may / "ignore-toan-cuc").write_text(luat, encoding="utf-8", newline="\n")
    (may / ".gitconfig").write_text(
        f"[core]\n\texcludesFile = {(may / 'ignore-toan-cuc').as_posix()}\n", encoding="utf-8", newline="\n")
    for bien in ("HOME", "USERPROFILE"):
        monkeypatch.setenv(bien, str(may))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(may / "xdg"))
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(may / ".gitconfig"))
    return may


def test_luat_ignore_rieng_cua_may_khong_lam_xanh_gia(may_co_luat_ignore_rieng, kho_git):
    """Máy có luật ignore toàn cục bắt `downloads_wiley_tdm/` thì phép đo vẫn chỉ đọc
    `.gitignore` của DỰ ÁN: bỏ luật của dự án đi là phải thấy «không bị ignore» ngay."""
    duong = f"{THU_MUC_TAI_MAC_DINH}/{_TEN_TEP_PDF}"
    (kho_git.thu_muc / ".gitignore").write_text("# dự án không có luật nào\n", encoding="utf-8", newline="\n")
    # Bẫy có gài thật: cùng kho đó, git chạy với môi trường của «máy» thì coi đường dẫn là bị ignore.
    env_may = {k: v for k, v in os.environ.items()
               if not k.upper().startswith("GIT_") or k.upper() == "GIT_CONFIG_GLOBAL"}
    theo_may = subprocess.run(
        ["git", "-C", str(kho_git.thu_muc), "check-ignore", "-q", "--no-index", "--", duong],
        capture_output=True, text=True, env=env_may, timeout=60,
    )
    assert theo_may.returncode == 0, f"bẫy chưa gài được (mã {theo_may.returncode}): {theo_may.stderr}"
    assert not kho_git.bi_ignore(duong), "phép đo bị luật ignore riêng của máy làm xanh giả"


# ════════════════════════════════════════════════════════════════════════════
# 1. Thư mục tải mặc định của Wiley TDM
# ════════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("cap", ["", "tools/", "scripts/", "app/sources/", "a/b/c/"])
def test_thu_muc_tai_wiley_mac_dinh_bi_gitignore_bat_o_moi_cap(kho_git, cap):
    """Thư viện tạo thư mục tải TƯƠNG ĐỐI so với thư mục đang đứng: chạy từ gốc repo, từ
    `tools/` hay từ `scripts/` đều phải bị bắt — luật neo gốc («/downloads_wiley_tdm/») là chưa đủ."""
    duong = f"{cap}{THU_MUC_TAI_MAC_DINH}/{_TEN_TEP_PDF}"
    assert kho_git.bi_ignore(duong), (
        f"`.gitignore` KHÔNG bắt {duong} (luật khớp: {kho_git.luat_khop(duong)}) — PDF toàn văn "
        "Wiley tải về sẽ hiện trong `git status` của repo công khai. Thư mục mặc định là "
        "app/sources/wiley_tdm.py::THU_MUC_TAI_MAC_DINH; luật ignore phải cùng tên và KHÔNG neo gốc."
    )


class _PhanHoiWileyGia:
    """Phản hồi 200 của `api.wiley.com` — đủ những gì `TDMClient._download_pdf` đọc.

    `dut_sau=N`: đường truyền đứt sau đúng N byte — `iter_content` ném `ChunkedEncodingError`
    như `requests` thật làm khi máy chủ ngắt giữa chừng."""

    status_code = 200
    text = ""

    def __init__(self, noi_dung: bytes, dut_sau: Optional[int] = None) -> None:
        self._noi_dung = noi_dung
        self._dut_sau = dut_sau
        self.headers: dict = {}

    def iter_content(self, chunk_size: int = 8192):
        da_gui = 0
        for dau in range(0, len(self._noi_dung), chunk_size):
            khuc = self._noi_dung[dau:dau + chunk_size]
            if self._dut_sau is not None and da_gui + len(khuc) > self._dut_sau:
                yield khuc[:self._dut_sau - da_gui]
                raise requests.exceptions.ChunkedEncodingError("Connection broken: IncompleteRead")
            da_gui += len(khuc)
            yield khuc


class _PhienWileyGia:
    """Thay `TDMClient._api_session` — biên mạng DUY NHẤT của thư viện bị thay trong ca tải thử."""

    def __init__(self, noi_dung: bytes, dut_sau: Optional[int] = None) -> None:
        self._noi_dung = noi_dung
        self.dut_sau = dut_sau
        self.cac_url: List[str] = []

    def get(self, url, **_):
        self.cac_url.append(url)
        return _PhanHoiWileyGia(self._noi_dung, self.dut_sau)


def _cam_goi_mang(self, request, **_):
    raise AssertionError(f"ca kiểm gọi mạng thật: {request.url}")


def test_tai_bang_thu_vien_wiley_that_vao_thu_muc_mac_dinh_thi_git_khong_thay(kho_git, monkeypatch):
    """Đi trọn đường thật: `WileyTdmClient()` không cấu hình gì, thư viện `wiley-tdm` THẬT tự
    tạo thư mục, tự đặt tên tệp và ghi PDF xuống đĩa; chỉ biên mạng bị thay. Sau đó hỏi git
    đúng câu mà `git add -A` hỏi: có tệp mới nào không bị ignore?"""
    pytest.importorskip("wiley_tdm")
    from wiley_tdm.doi_utils import DOIUtils
    from wiley_tdm.ip_utils import IPUtils

    # Khoá mạng: thư viện dò IP công khai lúc dựng client và hỏi doi.org trước khi tải.
    monkeypatch.setattr(requests.Session, "send", _cam_goi_mang)
    monkeypatch.setattr(IPUtils, "get_ip_address", staticmethod(lambda: None))
    monkeypatch.setattr(DOIUtils, "is_valid", staticmethod(DOIUtils.check_format))
    monkeypatch.setattr(settings, "enable_wiley_tdm", True)
    monkeypatch.setattr(settings, "wiley_tdm_api_token", _TOKEN_GIA)
    monkeypatch.setattr(settings, "wiley_tdm_download_dir", "")
    monkeypatch.setattr(settings, "wiley_tdm_rate_limit_seconds", 10.0)
    monkeypatch.chdir(kho_git.thu_muc)
    assert kho_git.tep_git_thay() == [".gitignore"]

    noi_dung = _pdf_tron_ven(20_000)  # thư viện báo round(20000 / 1024) = 20
    client = WileyTdmClient()
    thu_vien = client._client
    assert hasattr(thu_vien, "_api_session"), "thư viện wiley-tdm đổi tên phiên HTTP — sửa ca kiểm này"
    phien = _PhienWileyGia(noi_dung)
    thu_vien._api_session = phien

    kq = client.download_pdf(_DOI)

    assert len(phien.cac_url) == 1 and phien.cac_url[0].startswith("https://api.wiley.com/")
    assert (kq.trang_thai, kq.thanh_cong) == ("SUCCESS", True)
    assert Path(kq.duong_dan).as_posix() == f"{THU_MUC_TAI_MAC_DINH}/{_TEN_TEP_PDF}"
    tep = kho_git.thu_muc / THU_MUC_TAI_MAC_DINH / _TEN_TEP_PDF
    assert tep.read_bytes() == noi_dung, "PDF phải nằm thật trên đĩa, trong kho git, thì ca này mới có nghĩa"
    assert kq.kich_thuoc_byte == 20_000, "byte thật trên đĩa, không phải số KiB (20) thư viện báo"
    assert kho_git.tep_git_thay() == [".gitignore"], (
        "git THẤY tệp PDF vừa tải vào thư mục mặc định — `.gitignore` thiếu luật cho "
        f"{THU_MUC_TAI_MAC_DINH}/"
    )

    # Tải lại: thư viện thật trả EXISTING_FILE không kèm `size`; ta vẫn đo được byte từ đĩa.
    lan_hai = client.download_pdf(_DOI)
    assert (lan_hai.trang_thai, lan_hai.thanh_cong, lan_hai.kich_thuoc_byte) == ("EXISTING_FILE", True, 20_000)
    assert len(phien.cac_url) == 1, "tệp đã có thì không gọi mạng lần nữa"

    # Đối chứng: cùng phép đo đó THẤY một tệp nằm ngoài luật ignore.
    doi_chung = kho_git.thu_muc / "doi_chung_khong_bi_ignore.py"
    doi_chung.write_text("# đối chứng\n", encoding="utf-8", newline="\n")
    assert kho_git.tep_git_thay() == [".gitignore", "doi_chung_khong_bi_ignore.py"]


# ════════════════════════════════════════════════════════════════════════════
# 2. Cache HTTP — nơi toàn văn PMC và trang mục lục chạm đĩa
# ════════════════════════════════════════════════════════════════════════════

def test_cache_http_noi_toan_van_cham_dia_bi_gitignore_bat(kho_git):
    """`PmcGuidelineFullTextClient` lấy toàn văn bằng `get_text`, mà `get_text` ghi nguyên nội
    dung xuống `_CACHE_DIR` (xem ca kế). Vị trí THẬT của cache phải nằm ngoài tầm nhìn của git."""
    try:
        tuong_doi = _CACHE_DIR_THAT.resolve().relative_to(BASE_DIR.resolve())
    except ValueError:
        return  # cache nằm ngoài cây repo: git không thấy, không có gì để canh
    duong = f"{tuong_doi.as_posix()}/0123abcd.json"
    assert kho_git.bi_ignore(duong), (
        f"`.gitignore` KHÔNG bắt {duong} — cache HTTP giữ toàn văn PMC đã tải (chỉ được dùng "
        "làm nguồn tham chiếu nội bộ) sẽ hiện trong `git status` của repo công khai."
    )


class _PhanHoiHttpGia:
    status_code = 200

    def __init__(self, url: str, than: bytes) -> None:
        self.url = url
        self.content = than
        self.text = than.decode("utf-8", errors="replace")
        self.headers: dict = {}

    def raise_for_status(self) -> None:
        return None

    def json(self):
        return json.loads(self.text)


class _PhienHttpGia:
    def __init__(self, than_theo_url: dict) -> None:
        self._than = than_theo_url

    def request(self, method, url, params=None, timeout=None, **_):
        return _PhanHoiHttpGia(url, self._than[url])


def test_get_text_ghi_toan_van_xuong_cache_con_get_bytes_khong_ghi_gi(monkeypatch, tmp_path):
    """Hai dữ kiện mà kết luận rà soát 30/09/2026 dựa vào, đo bằng `HttpClient` THẬT (phiên giả):
    `get_text` (đường toàn văn PMC, trang mục lục GOLD/GINA/BTS) ghi nội dung xuống
    `_CACHE_DIR`; `get_bytes` (đường PDF của GOLD/GINA/BTS) không ghi gì xuống đĩa.

    `get_bytes` mà bắt đầu ghi đĩa thì ca này đỏ: khi đó PDF có bản quyền nằm lại trên đĩa, phải
    chắc nơi ghi được `.gitignore` bắt (ca trên) rồi mới sửa ca này."""
    cache = tmp_path / "http_cache"
    cache.mkdir()
    monkeypatch.setattr(http_mod, "_CACHE_DIR", cache)
    monkeypatch.setattr(http_mod, "_throttle", lambda url, min_interval: 0.0)
    url_pdf = "https://example.invalid/bao-cao.pdf"
    url_txt = "https://example.invalid/PMC1.1/PMC1.1.txt"
    toan_van = "TOAN VAN PMC GIA " + "x" * 200
    client = http_mod.HttpClient(cache_ttl=3600)
    client.session = _PhienHttpGia({url_pdf: b"%PDF-1.7 gia", url_txt: toan_van.encode("utf-8")})

    assert client.get_bytes(url_pdf) == b"%PDF-1.7 gia"
    assert list(cache.iterdir()) == [], "get_bytes nay ghi đĩa — xem docstring của ca này"

    assert client.get_text(url_txt) == toan_van
    tep_cache = list(cache.iterdir())
    assert len(tep_cache) == 1
    assert json.loads(tep_cache[0].read_text(encoding="utf-8"))["text"] == toan_van


# ════════════════════════════════════════════════════════════════════════════
# 3. Connector guideline không tự ghi tệp
# ════════════════════════════════════════════════════════════════════════════

_CONNECTOR_KHONG_GHI_DIA = (
    "gold_copd.py", "gina_asthma.py", "bts_guidelines.py", "pmc_guideline_fulltext.py",
    "guideline_fulltext_common.py",
)
# Lời gọi ghi/tạo tệp (tên hàm hoặc tên phương thức) và module chuyên ghi tệp.
_LOI_GOI_GHI_DIA = frozenset({
    "open", "write", "write_bytes", "write_text", "writelines", "mkdir", "makedirs", "touch", "dump",
    "to_csv", "save_raw", "copyfile", "copy2", "copytree", "move", "NamedTemporaryFile", "mkstemp", "mkdtemp",
})
_MODULE_GHI_DIA = frozenset({"shutil", "tempfile"})


def _loi_goi_ghi_dia(ma_nguon: str) -> List[str]:
    """Các lời gọi ghi đĩa trong MÃ THI HÀNH (duyệt cây cú pháp: chữ trong chú thích hay
    docstring không tính)."""
    thay: List[tuple] = []
    for nut in ast.walk(ast.parse(ma_nguon)):
        ten: Optional[str] = None
        if isinstance(nut, ast.Call):
            ham = nut.func
            ten_goi = ham.id if isinstance(ham, ast.Name) else ham.attr if isinstance(ham, ast.Attribute) else None
            if ten_goi in _LOI_GOI_GHI_DIA:
                ten = f"{ten_goi}(...)"
        elif isinstance(nut, ast.Import):
            trung = [a.name for a in nut.names if a.name.split(".")[0] in _MODULE_GHI_DIA]
            ten = f"import {', '.join(trung)}" if trung else None
        elif isinstance(nut, ast.ImportFrom):
            if (nut.module or "").split(".")[0] in _MODULE_GHI_DIA:
                ten = f"from {nut.module} import ..."
        if ten:
            thay.append((nut.lineno, ten))
    # `ast.walk` duyệt theo bề rộng, không theo thứ tự dòng — sắp lại cho thông điệp dễ đọc và ổn định.
    return [f"dòng {dong}: {ten}" for dong, ten in sorted(thay)]


def test_bo_do_loi_goi_ghi_dia_bat_duoc_ma_mau():
    """Đối chứng cho bộ dò: bắt lời gọi ghi đĩa thật, bỏ qua chữ trong chú thích và docstring."""
    co_ghi = (
        "from pathlib import Path\nimport shutil\n"
        "def luu(b):\n    Path('x.pdf').write_bytes(b)\n    with open('y', 'wb') as f:\n        f.write(b)\n"
    )
    assert _loi_goi_ghi_dia(co_ghi) == [
        "dòng 2: import shutil", "dòng 4: write_bytes(...)", "dòng 5: open(...)", "dòng 6: write(...)",
    ]
    chi_noi_den = '"""Không gọi open() hay write_bytes() ở đây."""\n# tep.write_text("x")\nx = "mkdir"\n'
    assert _loi_goi_ghi_dia(chi_noi_den) == []


@pytest.mark.parametrize("ten_tep", _CONNECTOR_KHONG_GHI_DIA)
def test_connector_guideline_khong_tu_ghi_tep(ten_tep):
    """Rà soát 30/09/2026 (đọc mã): các connector này không ghi tệp nào — PDF qua `get_bytes`
    chỉ nằm trong bộ nhớ, phần chạm đĩa duy nhất là cache HTTP (đã canh ở mục 2)."""
    ma_nguon = (REPO_ROOT / "app" / "sources" / ten_tep).read_text(encoding="utf-8")
    thay = _loi_goi_ghi_dia(ma_nguon)
    assert thay == [], (
        f"app/sources/{ten_tep} nay có lời gọi ghi đĩa: {thay}. Nội dung guideline có bản quyền "
        "(ranh giới ghi ở app/sources/guideline_fulltext_common.py) mà repo này công khai: nơi ghi "
        "phải nằm NGOÀI repo hoặc được `.gitignore` bắt. Thêm ca `bi_ignore` cho đường dẫn mới ở tệp "
        "này rồi mới nới ca kiểm này."
    )


# ════════════════════════════════════════════════════════════════════════════
# 4. Hàm hỏi git dùng chung — app/utils/tam_nhin_git.py
# ════════════════════════════════════════════════════════════════════════════

def _ngoai_moi_cay_git(thu_muc: Path) -> Path:
    """Các ca «ngoài cây git» chỉ có nghĩa khi thư mục tạm của pytest thật sự nằm ngoài mọi cây
    git (đặt `--basetemp` vào trong một repo thì không còn đúng). Dò độc lập với mã đang kiểm."""
    for cap in (thu_muc, *thu_muc.parents):
        if (cap / ".git").exists():
            _khong_do_duoc(f"thư mục tạm {thu_muc} nằm trong cây git {cap} — không dựng được ca «ngoài cây git»")
    return thu_muc


def _git_tran(thu_muc: Path, duong: str) -> int:
    """`git check-ignore` gọi TRẦN — đúng môi trường hiện tại của tiến trình, không cô lập gì. Dùng
    để chứng minh bẫy đã gài thật trước khi hỏi hàm đang kiểm."""
    kq = subprocess.run(
        ["git", "-C", str(thu_muc), "check-ignore", "-q", "--no-index", "--", duong],
        capture_output=True, text=True, timeout=60,
    )
    return kq.returncode


def test_tam_nhin_git_phan_biet_ngoai_cay_bi_ignore_va_git_thay(kho_git, tmp_path):
    """Đối chiếu từng đường dẫn với phép đo độc lập của tệp này (`kho_git.bi_ignore`)."""
    kho = kho_git.thu_muc
    for tuong_doi in (
        f"pdfs/{_TEN_TEP_PDF}", f"data/wiley/{_TEN_TEP_PDF}", _TEN_TEP_PDF, f"a/b/c/{_TEN_TEP_PDF}",
        f"{THU_MUC_TAI_MAC_DINH}/{_TEN_TEP_PDF}", f"tools/{THU_MUC_TAI_MAC_DINH}/{_TEN_TEP_PDF}",
        f"data/raw/wiley/{_TEN_TEP_PDF}",
    ):
        ket_luan = tng.tam_nhin_git(kho / tuong_doi)
        mong_doi = tng.BI_IGNORE if kho_git.bi_ignore(tuong_doi) else tng.GIT_THAY
        assert ket_luan.trang_thai == mong_doi, tuong_doi
        assert ket_luan.goc_cay.samefile(kho), tuong_doi
    # Cả hai kết luận phải thật sự xuất hiện, không thì vòng lặp trên xanh vô nghĩa.
    assert tng.tam_nhin_git(kho / "pdfs" / _TEN_TEP_PDF).trang_thai == tng.GIT_THAY
    assert tng.tam_nhin_git(kho / THU_MUC_TAI_MAC_DINH / _TEN_TEP_PDF).trang_thai == tng.BI_IGNORE
    ngoai = tng.tam_nhin_git(_ngoai_moi_cay_git(tmp_path) / "ngoai" / "pdfs" / _TEN_TEP_PDF)
    assert (ngoai.trang_thai, ngoai.goc_cay, ngoai.ly_do) == (tng.NGOAI_CAY_GIT, None, "")


def test_tam_nhin_git_duong_tuong_doi_tinh_theo_thu_muc_dang_dung(kho_git, monkeypatch):
    """Thư viện Wiley ghi theo đường TƯƠNG ĐỐI so với thư mục đang đứng — hàm hỏi git cũng phải vậy."""
    (kho_git.thu_muc / "tools").mkdir()
    monkeypatch.chdir(kho_git.thu_muc)
    assert tng.tam_nhin_git(Path("pdfs") / _TEN_TEP_PDF).trang_thai == tng.GIT_THAY
    assert tng.tam_nhin_git(f"{THU_MUC_TAI_MAC_DINH}/{_TEN_TEP_PDF}").trang_thai == tng.BI_IGNORE
    monkeypatch.chdir(kho_git.thu_muc / "tools")
    assert tng.tam_nhin_git(_TEN_TEP_PDF).trang_thai == tng.GIT_THAY
    assert tng.tam_nhin_git(f"{THU_MUC_TAI_MAC_DINH}/{_TEN_TEP_PDF}").trang_thai == tng.BI_IGNORE


def test_tam_nhin_git_hieu_ten_tep_dung_tung_chu(kho_git):
    """Tên có ký tự mà git coi là đặc biệt vẫn phải ra «bị ignore»/«git thấy», không ra «không đo
    được». Đo 30/09/2026: hỏi trần «:(glob)x.pdf» thì git thoát mã 128 (pathspec magic)."""
    ten_la = ["tên tiếng Việt có dấu cách.pdf", "x[1]*.pdf"]
    if os.name != "nt":  # Windows không cho «:» trong tên tệp
        ten_la.append(":(glob)x.pdf")
    for ten in ten_la:
        assert tng.tam_nhin_git(kho_git.thu_muc / "pdfs" / ten).trang_thai == tng.GIT_THAY, ten
        assert tng.tam_nhin_git(kho_git.thu_muc / THU_MUC_TAI_MAC_DINH / ten).trang_thai == tng.BI_IGNORE, ten
        assert tng.tam_nhin_git(kho_git.thu_muc / ten).trang_thai == tng.GIT_THAY, ten


def test_tam_nhin_git_luat_phu_dinh_la_git_thay(kho_git):
    """Luật phủ định («!mẫu») thả tệp ra khỏi vùng ignore: git THẤY tệp đó. `check-ignore -v` trả
    mã 0 cho cả hai tệp dưới đây, nên chỉ mã thoát của `-q` mới phân biệt được."""
    (kho_git.thu_muc / ".gitignore").write_text("tha/*\n!tha/giu.pdf\n", encoding="utf-8", newline="\n")
    assert tng.tam_nhin_git(kho_git.thu_muc / "tha" / "khac.pdf").trang_thai == tng.BI_IGNORE
    assert tng.tam_nhin_git(kho_git.thu_muc / "tha" / "giu.pdf").trang_thai == tng.GIT_THAY


@pytest.fixture(params=["core.excludesFile", "xdg"])
def may_ignore_thu_muc_pdfs(request, monkeypatch, tmp_path) -> str:
    """Một «máy» có luật ignore RIÊNG bắt `pdfs/`, gài qua hai đường git tự tìm mà không cần biến
    GIT_* nào: `~/.gitconfig` khai `core.excludesFile`, hoặc `$XDG_CONFIG_HOME/git/ignore`."""
    may = tmp_path / "may-co-luat-rieng"
    (may / "xdg" / "git").mkdir(parents=True)
    if request.param == "xdg":
        (may / "xdg" / "git" / "ignore").write_text("pdfs/\n", encoding="utf-8", newline="\n")
    else:
        (may / "ignore-rieng").write_text("pdfs/\n", encoding="utf-8", newline="\n")
        (may / ".gitconfig").write_text(
            f"[core]\n\texcludesFile = {(may / 'ignore-rieng').as_posix()}\n", encoding="utf-8", newline="\n")
    for bien in ("HOME", "USERPROFILE"):
        monkeypatch.setenv(bien, str(may))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(may / "xdg"))
    for bien in [b for b in os.environ if b.upper().startswith("GIT_")]:
        monkeypatch.delenv(bien)
    return request.param


def test_tam_nhin_git_khong_tinh_luat_ignore_rieng_cua_may(may_ignore_thu_muc_pdfs, kho_git):
    """Cây làm việc đồng bộ qua OneDrive sang máy khác, nơi luật ignore riêng của máy này không tồn
    tại: tệp mà CHỈ luật riêng của máy che thì vẫn là «git thấy»."""
    duong = f"pdfs/{_TEN_TEP_PDF}"
    assert _git_tran(kho_git.thu_muc, duong) == 0, f"bẫy chưa gài được ({may_ignore_thu_muc_pdfs})"
    assert not kho_git.bi_ignore(duong), "`.gitignore` của dự án không có luật nào cho pdfs/"
    assert tng.tam_nhin_git(kho_git.thu_muc / "pdfs" / _TEN_TEP_PDF).trang_thai == tng.GIT_THAY


def test_tam_nhin_git_khong_de_bien_git_dir_ro_ri_doi_kho_duoc_hoi(kho_git, tmp_path, monkeypatch):
    """Trong hook git (pre-commit chạy pytest), `GIT_DIR` trỏ vào kho đang commit. Để nguyên biến
    đó thì git áp `info/exclude` của kho KIA lên thư mục đang hỏi."""
    kho_khac = kho_git.tao_kho_khac(tmp_path / "kho-khac", luat_rieng_cua_kho="pdfs/\n")
    duong = f"pdfs/{_TEN_TEP_PDF}"
    monkeypatch.setenv("GIT_DIR", str(kho_khac / ".git"))
    assert _git_tran(kho_git.thu_muc, duong) == 0, "bẫy chưa gài được: GIT_DIR rò rỉ phải làm git trần trả «bị ignore»"
    assert not kho_git.bi_ignore(duong)
    assert tng.tam_nhin_git(kho_git.thu_muc / "pdfs" / _TEN_TEP_PDF).trang_thai == tng.GIT_THAY


def test_tam_nhin_git_tinh_luat_rieng_di_theo_kho(kho_git, tmp_path):
    """`.git/info/exclude` nằm trong kho và đồng bộ cùng kho (khác luật riêng của máy): được tính."""
    kho_khac = kho_git.tao_kho_khac(tmp_path / "kho-co-luat-rieng", luat_rieng_cua_kho="pdfs/\n")
    assert tng.tam_nhin_git(kho_khac / "pdfs" / _TEN_TEP_PDF).trang_thai == tng.BI_IGNORE
    assert tng.tam_nhin_git(kho_khac / "khac" / _TEN_TEP_PDF).trang_thai == tng.GIT_THAY


def test_tam_nhin_git_may_khong_co_git(kho_git, tmp_path, monkeypatch):
    """Không có lệnh git: TRONG một cây git là «không đo được» — không phải «ngoài cây git», cũng
    không phải «bị ignore». NGOÀI mọi cây git thì vẫn kết luận được, vì không cần hỏi git."""
    monkeypatch.setattr(tng, "_LENH_GIT", "git-khong-co-tren-may-nay")
    trong = tng.tam_nhin_git(kho_git.thu_muc / THU_MUC_TAI_MAC_DINH / _TEN_TEP_PDF)
    assert trong.trang_thai == tng.KHONG_DO_DUOC
    assert trong.goc_cay.samefile(kho_git.thu_muc)
    assert "không có lệnh" in trong.ly_do
    ngoai = tng.tam_nhin_git(_ngoai_moi_cay_git(tmp_path) / "ngoai" / _TEN_TEP_PDF)
    assert ngoai.trang_thai == tng.NGOAI_CAY_GIT


def test_tam_nhin_git_git_tu_choi_tra_loi_la_khong_do_duoc(kho_git):
    """Git trả mã khác 0/1 (ở đây: hỏi về một tệp nằm ngay trong `.git`, git báo «phải chạy trong
    cây làm việc») là phép đo hỏng — không được đọc thành «git thấy» hay «bị ignore»."""
    ket_luan = tng.tam_nhin_git(kho_git.thu_muc / ".git" / _TEN_TEP_PDF)
    assert ket_luan.trang_thai == tng.KHONG_DO_DUOC
    assert "trả mã" in ket_luan.ly_do


def test_tam_nhin_git_git_khong_tra_loi_kip_la_khong_do_duoc(kho_git, monkeypatch):
    """Git treo (ổ mạng, OneDrive đang tải `.gitignore` về) thì hết hạn chờ: cũng là «không đo được»."""
    monkeypatch.setattr(tng, "_HAN_GIAY", 1e-6)
    ket_luan = tng.tam_nhin_git(kho_git.thu_muc / THU_MUC_TAI_MAC_DINH / _TEN_TEP_PDF)
    assert ket_luan.trang_thai == tng.KHONG_DO_DUOC
    assert ket_luan.goc_cay.samefile(kho_git.thu_muc)
    assert "không trả lời" in ket_luan.ly_do


def test_tam_nhin_git_co_tep_ten_git_ma_khong_chay_duoc_la_khong_do_duoc(kho_git, tmp_path, monkeypatch):
    """Lệnh git có đó nhưng hệ điều hành không chạy được nó (không có quyền thực thi, không phải
    chương trình): lỗi khác với «không có lệnh», vẫn phải ra «không đo được» chứ không nổ."""
    gia = tmp_path / "git-khong-chay-duoc"
    gia.write_text("day khong phai chuong trinh\n", encoding="utf-8", newline="\n")
    gia.chmod(0o644)
    monkeypatch.setattr(tng, "_LENH_GIT", str(gia))
    ket_luan = tng.tam_nhin_git(kho_git.thu_muc / THU_MUC_TAI_MAC_DINH / _TEN_TEP_PDF)
    assert ket_luan.trang_thai == tng.KHONG_DO_DUOC
    assert "không chạy được git" in ket_luan.ly_do


def _cac_bi_danh(thu_muc: Path, noi_dat: Path) -> List[Path]:
    """Những TÊN KHÁC của cùng một thư mục dựng được trên máy này: sai chữ hoa/thường (hệ tệp
    không phân biệt hoa/thường — macOS, Windows) và symlink (Linux, macOS; Windows khi có quyền).
    Mỗi bí danh đã được `samefile` xác nhận là chính thư mục đó."""
    bi_danh: List[Path] = []
    doi_hoa = thu_muc.with_name(thu_muc.name.swapcase())
    if doi_hoa.name != thu_muc.name and doi_hoa.exists() and doi_hoa.samefile(thu_muc):
        bi_danh.append(doi_hoa)
    lien_ket = noi_dat / f"lien-ket-toi-{thu_muc.name}"
    try:
        os.symlink(thu_muc, lien_ket, target_is_directory=True)
    except (OSError, NotImplementedError):
        pass
    else:
        bi_danh.append(lien_ket)
    if not bi_danh:
        _khong_do_duoc("máy này không dựng được bí danh nào cho thư mục (không symlink, hệ tệp phân biệt hoa/thường)")
    return bi_danh


def test_tam_nhin_git_qua_ten_khac_cua_cung_thu_muc(kho_git, tmp_path):
    """Gọi thư mục bằng tên khác (sai chữ hoa/thường, symlink) không đổi câu trả lời của git."""
    for bi_danh in _cac_bi_danh(kho_git.thu_muc, tmp_path):
        thay = tng.tam_nhin_git(bi_danh / "pdfs" / _TEN_TEP_PDF)
        assert thay.trang_thai == tng.GIT_THAY, bi_danh
        assert thay.goc_cay.samefile(kho_git.thu_muc), bi_danh
        assert tng.tam_nhin_git(bi_danh / THU_MUC_TAI_MAC_DINH / _TEN_TEP_PDF).trang_thai == tng.BI_IGNORE, bi_danh


def test_nam_trong_thu_muc_so_danh_tinh_khong_so_chuoi(tmp_path):
    goc = tmp_path / "Goc-Thu-Muc"
    (goc / "con").mkdir(parents=True)
    (tmp_path / "Goc-Thu-Muc-khac").mkdir()
    assert tng.nam_trong_thu_muc(goc / "x.txt", goc)
    assert tng.nam_trong_thu_muc(goc / "con" / "x.txt", goc)
    assert tng.nam_trong_thu_muc(goc / "chua" / "co" / "x.txt", goc), "thư mục cha chưa tồn tại vẫn xét được"
    assert not tng.nam_trong_thu_muc(tmp_path / "x.txt", goc)
    trung_tien_to = tmp_path / "Goc-Thu-Muc-khac" / "x.txt"
    assert not tng.nam_trong_thu_muc(trung_tien_to, goc), "trùng tiền tố tên không phải «nằm trong»"
    assert not tng.nam_trong_thu_muc(goc / "x.txt", tmp_path / "khong-ton-tai")
    for bi_danh in _cac_bi_danh(goc, tmp_path):
        assert tng.nam_trong_thu_muc(bi_danh / "con" / "x.txt", goc), bi_danh
        assert tng.nam_trong_thu_muc(goc / "con" / "x.txt", bi_danh), bi_danh


# ════════════════════════════════════════════════════════════════════════════
# 5. Thư mục tải Wiley TỰ ĐẶT — xét thư mục THẬT mà thư viện ghi
# ════════════════════════════════════════════════════════════════════════════

class _TrangThaiGia:
    def __init__(self, name: str) -> None:
        self.name = name


class _KetQuaTaiGia:
    def __init__(self, doi, ten_trang_thai, comment=None, path=None, size=None, api_status=None) -> None:
        self.doi = doi
        self.status = _TrangThaiGia(ten_trang_thai)
        self.comment = comment
        self.path = path
        self.size = size
        self.api_status = api_status


class _TDMClientGia:
    """Bản giả TỐI THIỂU của `wiley_tdm.TDMClient` 1.2.0, cho CI (nơi không cài thư viện). Chép
    đúng những hành vi mà mục 5–6 dựa vào; chính các ca đó chạy lại trên thư viện THẬT ở máy có
    cài, nên bản giả trôi khỏi thư viện là một trong hai biến thể đỏ:

      * dựng client là tạo thư mục tải; tên có đuôi (`Path.suffix`) bị coi là tên TỆP ⇒ lùi về
        thư mục mẹ (`FileUtils.create_directory`);
      * tệp đã có trên đĩa ⇒ `EXISTING_FILE`, không gọi mạng;
      * `IOError` lúc ghi — kể cả đứt mạng giữa chừng, vì `RequestException` là lớp con của
        `IOError` — ⇒ `STORAGE_ERROR`, tệp ghi dở nằm lại trên đĩa (`TDMClient._save_pdf`)."""

    API_URL = "https://api.wiley.com/onlinelibrary/tdm/v1/articles/"

    def __init__(self, api_token=None, download_dir="downloads") -> None:
        self._download_dir = self._tao_thu_muc(Path(str(download_dir)))
        if not api_token:
            raise ValueError("TDM_API_TOKEN environment variable not set")
        self.api_rate_limit = 5.0
        self.skip_existing_files = True
        self._api_session = None

    @staticmethod
    def _tao_thu_muc(duong: Path) -> Path:
        if duong.suffix:
            duong = duong.parent
        duong.mkdir(parents=True, exist_ok=True)
        return duong

    @property
    def download_dir(self) -> Path:
        return self._download_dir

    def download_pdf(self, doi: str) -> _KetQuaTaiGia:
        tep = self._download_dir / (doi.replace("/", "-") + ".pdf")
        if self.skip_existing_files and tep.exists():
            return _KetQuaTaiGia(doi, "EXISTING_FILE", "", tep)
        phan_hoi = self._api_session.get(self.API_URL + quote(doi, safe=""), stream=True)
        try:
            self._tao_thu_muc(tep.parent)
            with tep.open("wb") as dau_ra:
                for khuc in phan_hoi.iter_content(chunk_size=8192):
                    dau_ra.write(khuc)
        except IOError as exc:
            return _KetQuaTaiGia(doi, "STORAGE_ERROR", str(exc), tep)
        return _KetQuaTaiGia(doi, "SUCCESS", "", tep, round(tep.stat().st_size / 1024), 200)

    def download_pdfs(self, dois, on_result=None):
        ket_qua = []
        for doi in dois:
            mot = self.download_pdf(doi)
            ket_qua.append(mot)
            if on_result:
                on_result(mot)
        return ket_qua


@pytest.fixture(params=["thu_vien_that", "ban_gia"])
def wiley_bat(request, monkeypatch) -> str:
    """Bật Wiley TDM với token giả, khoá mọi biên mạng. Biến thể «thu_vien_that» dùng gói
    `wiley-tdm` đang cài (bỏ qua nếu máy không có); «ban_gia» cấy `_TDMClientGia`."""
    monkeypatch.setattr(requests.Session, "send", _cam_goi_mang)
    monkeypatch.setattr(settings, "enable_wiley_tdm", True)
    monkeypatch.setattr(settings, "wiley_tdm_api_token", _TOKEN_GIA)
    monkeypatch.setattr(settings, "wiley_tdm_download_dir", "")
    monkeypatch.setattr(settings, "wiley_tdm_rate_limit_seconds", 10.0)
    if request.param == "thu_vien_that":
        pytest.importorskip("wiley_tdm")
        from wiley_tdm.doi_utils import DOIUtils
        from wiley_tdm.ip_utils import IPUtils

        monkeypatch.setattr(IPUtils, "get_ip_address", staticmethod(lambda: None))
        monkeypatch.setattr(DOIUtils, "is_valid", staticmethod(DOIUtils.check_format))
    else:
        gia = types.ModuleType("wiley_tdm")
        gia.TDMClient = _TDMClientGia
        monkeypatch.setitem(sys.modules, "wiley_tdm", gia)
    return request.param


def _gan_phien(client: WileyTdmClient, noi_dung: bytes, dut_sau: Optional[int] = None) -> _PhienWileyGia:
    assert hasattr(client._client, "_api_session"), "thư viện wiley-tdm đổi tên phiên HTTP — sửa các ca ở mục 5–6"
    phien = _PhienWileyGia(noi_dung, dut_sau)
    client._client._api_session = phien
    return phien


@pytest.mark.parametrize("cach_dat, thu_muc", [
    ("bien_moi_truong", "pdfs"), ("tham_so", "data/wiley"), ("tham_so", "tools/pdfs"),
])
def test_thu_muc_tai_tu_dat_o_cho_git_thay_thi_bi_tu_choi(kho_git, wiley_bat, monkeypatch, cach_dat, thu_muc):
    """(A) Đo 30/09/2026: `WILEY_TDM_DOWNLOAD_DIR=pdfs` hay `download_dir="data/wiley"` ⇒ PDF có bản
    quyền rơi vào chỗ `git status` thấy. Nay dựng client là bị từ chối, kèm cách sửa."""
    monkeypatch.chdir(kho_git.thu_muc)
    assert not kho_git.bi_ignore(f"{thu_muc}/{_TEN_TEP_PDF}"), "ca này cần một thư mục mà dự án KHÔNG ignore"
    with pytest.raises(RuntimeError) as loi:
        if cach_dat == "bien_moi_truong":
            monkeypatch.setattr(settings, "wiley_tdm_download_dir", thu_muc)
            WileyTdmClient()
        else:
            WileyTdmClient(download_dir=thu_muc)
    thong_diep = str(loi.value)
    assert "cây git" in thong_diep and "bản quyền" in thong_diep
    assert Path(thu_muc).name in thong_diep, "thông điệp phải nêu thư mục bị từ chối"
    assert "WILEY_TDM_DOWNLOAD_DIR" in thong_diep and THU_MUC_TAI_MAC_DINH in thong_diep, "thông điệp phải nêu cách sửa"
    assert kho_git.tep_git_thay() == [".gitignore"]


def test_thu_muc_co_dau_cham_bi_thu_vien_doi_thanh_thu_muc_me(kho_git, wiley_bat, monkeypatch):
    """(B) Đo 30/09/2026: `TDMClient(download_dir="wiley.pdfs").download_dir` là «.» — thư viện coi
    tên có đuôi là tên TỆP và lùi về thư mục mẹ, tức gốc kho nếu đang đứng ở đó."""
    monkeypatch.chdir(kho_git.thu_muc)
    with pytest.raises(RuntimeError) as loi:
        WileyTdmClient(download_dir="wiley.pdfs")
    thong_diep = str(loi.value)
    assert "wiley.pdfs" in thong_diep and "thư mục mẹ" in thong_diep, "phải giải thích vì sao nơi ghi khác cấu hình"
    assert not (kho_git.thu_muc / "wiley.pdfs").exists(), "thư viện không hề tạo thư mục mang tên đã cấu hình"
    assert kho_git.tep_git_thay() == [".gitignore"]


def test_xet_thu_muc_that_cua_thu_vien_chu_khong_xet_chuoi_cau_hinh(kho_git, wiley_bat, monkeypatch):
    """Chuỗi cấu hình «wiley.db» TRÔNG như an toàn: luật `*.db` của dự án bắt mọi thứ tên *.db, kể
    cả thư mục. Nhưng thư viện lùi về thư mục mẹ — gốc kho, nơi git thấy. Hỏi git về chuỗi cấu
    hình thì lọt; hỏi về `client.download_dir` mới bắt được."""
    assert kho_git.bi_ignore(f"wiley.db/{_TEN_TEP_PDF}"), "chuỗi cấu hình phải trông như bị ignore thì ca mới có nghĩa"
    assert not kho_git.bi_ignore(_TEN_TEP_PDF), "nơi ghi thật (gốc kho) phải là chỗ git thấy"
    monkeypatch.chdir(kho_git.thu_muc)
    with pytest.raises(RuntimeError, match="cây git"):
        WileyTdmClient(download_dir="wiley.db")


def test_thu_vien_lui_ve_thu_muc_me_da_bi_ignore_thi_cho_tai_kem_canh_bao(kho_git, wiley_bat, monkeypatch, caplog):
    """Chiều ngược lại: nơi ghi THẬT đã bị ignore thì không có lý do từ chối — nhưng PDF không nằm
    ở nơi người dùng tưởng, nên phải có một dòng cảnh báo."""
    caplog.set_level("WARNING")
    monkeypatch.chdir(kho_git.thu_muc)
    client = WileyTdmClient(download_dir=f"{THU_MUC_TAI_MAC_DINH}/lo.2026")
    assert Path(client.download_dir).as_posix() == THU_MUC_TAI_MAC_DINH
    assert "lo.2026" in caplog.text and "thư mục mẹ" in caplog.text
    _gan_phien(client, _pdf_tron_ven(20_000))
    kq = client.download_pdf(_DOI)
    assert (kq.trang_thai, kq.thanh_cong) == ("SUCCESS", True)
    assert Path(kq.duong_dan).as_posix() == f"{THU_MUC_TAI_MAC_DINH}/{_TEN_TEP_PDF}"
    assert kho_git.tep_git_thay() == [".gitignore"]


@pytest.mark.parametrize("noi_tai", ["mac_dinh", "trong_kho_da_bi_ignore", "ngoai_moi_cay_git"])
def test_thu_muc_tai_git_khong_thay_thi_tai_binh_thuong(kho_git, wiley_bat, monkeypatch, tmp_path, caplog, noi_tai):
    """Rào chỉ chặn chỗ git THẤY: thư mục mặc định, thư mục tự đặt đã bị ignore, và thư mục ngoài
    mọi cây git đều tải như cũ, không kèm cảnh báo nào về thư mục."""
    caplog.set_level("WARNING")
    monkeypatch.chdir(kho_git.thu_muc)
    thu_muc = {
        "mac_dinh": None, "trong_kho_da_bi_ignore": "data/raw/wiley",
        "ngoai_moi_cay_git": str(_ngoai_moi_cay_git(tmp_path) / "ngoai" / "wiley"),
    }[noi_tai]
    client = WileyTdmClient(download_dir=thu_muc)
    _gan_phien(client, _pdf_tron_ven(20_000))
    kq = client.download_pdf(_DOI)
    assert (kq.trang_thai, kq.thanh_cong, kq.kich_thuoc_byte) == ("SUCCESS", True, 20_000)
    assert Path(kq.duong_dan).read_bytes() == _pdf_tron_ven(20_000)
    assert kho_git.tep_git_thay() == [".gitignore"]
    assert "thư mục mẹ" not in caplog.text


def test_kho_chi_ignore_tep_pdf_trong_thu_muc_tai_thi_van_duoc_tai(kho_git, wiley_bat, monkeypatch):
    """Thư viện chỉ ghi tệp «.pdf» vào thư mục tải, nên câu hỏi gửi git là về một tệp «.pdf» nằm trong
    đó. Kho chỉ ignore `bai-bao/*.pdf` — không ignore cả thư mục — thì PDF tải về vẫn ngoài tầm nhìn."""
    with (kho_git.thu_muc / ".gitignore").open("a", encoding="utf-8", newline="\n") as tep_luat:
        tep_luat.write("\nbai-bao/*.pdf\n")
    assert kho_git.bi_ignore(f"bai-bao/{_TEN_TEP_PDF}") and not kho_git.bi_ignore("bai-bao/ghi-chu.txt")
    monkeypatch.chdir(kho_git.thu_muc)
    client = WileyTdmClient(download_dir="bai-bao")
    _gan_phien(client, _pdf_tron_ven(20_000))
    assert client.download_pdf(_DOI).thanh_cong is True
    assert kho_git.tep_git_thay() == [".gitignore"]


def test_khong_do_duoc_git_thi_thu_muc_tai_trong_cay_git_bi_tu_choi(kho_git, wiley_bat, monkeypatch, tmp_path):
    """Máy không có git mà thư mục tải nằm TRONG một cây git: không đo được luật ignore. «Không đo
    được» không phải «an toàn» — cây làm việc còn đồng bộ sang máy có git — nên từ chối, kể cả thư
    mục mặc định. Thư mục NGOÀI mọi cây git thì không cần git, vẫn tải được."""
    monkeypatch.setattr(tng, "_LENH_GIT", "git-khong-co-tren-may-nay")
    monkeypatch.chdir(kho_git.thu_muc)
    with pytest.raises(RuntimeError) as loi:
        WileyTdmClient()
    thong_diep = str(loi.value)
    assert "không đo được" in thong_diep and "không có lệnh" in thong_diep, "phải nói rõ vì sao không đo được"
    assert "NGOÀI mọi cây git" in thong_diep, "phải chỉ ra lối thoát không cần git"
    client = WileyTdmClient(download_dir=str(_ngoai_moi_cay_git(tmp_path) / "ngoai" / "wiley"))
    _gan_phien(client, _pdf_tron_ven(20_000))
    assert client.download_pdf(_DOI).thanh_cong is True


def test_dau_nga_trong_thu_muc_tai_la_thu_muc_nha_khong_phai_thu_muc_ten_nga(kho_git, wiley_bat, monkeypatch, tmp_path):
    """Thông điệp từ chối gợi ý «~/wiley_tdm_pdf». Thư viện không giải «~»: để nguyên thì nó tạo một
    thư mục tên «~» ngay trong thư mục đang đứng — lại nằm trong repo."""
    nha = _ngoai_moi_cay_git(tmp_path) / "nha-nguoi-dung"
    nha.mkdir()
    for bien in ("HOME", "USERPROFILE"):
        monkeypatch.setenv(bien, str(nha))
    monkeypatch.chdir(kho_git.thu_muc)
    client = WileyTdmClient(download_dir="~/wiley_tdm_pdf")
    assert Path(client.download_dir).samefile(nha / "wiley_tdm_pdf")
    assert not (kho_git.thu_muc / "~").exists()


def test_doi_thu_muc_dang_dung_sau_khi_dung_client_thi_kiem_lai_truoc_khi_tai(
        kho_git, wiley_bat, monkeypatch, tmp_path):
    """Thư mục tải tương đối được tính theo thư mục đang đứng LÚC GHI, không phải lúc dựng client:
    dựng ở ngoài repo rồi chuyển vào repo thì PDF rơi vào repo."""
    ngoai = _ngoai_moi_cay_git(tmp_path) / "ngoai"
    ngoai.mkdir()
    monkeypatch.chdir(ngoai)
    client = WileyTdmClient(download_dir="pdfs")
    phien = _gan_phien(client, _pdf_tron_ven(20_000))
    monkeypatch.chdir(kho_git.thu_muc)
    with pytest.raises(RuntimeError, match="cây git"):
        client.download_pdf(_DOI)
    with pytest.raises(RuntimeError, match="cây git"):
        client.download_pdfs([_DOI])
    assert phien.cac_url == [], "bị từ chối thì không gọi mạng"
    assert kho_git.tep_git_thay() == [".gitignore"]
    # Quay lại chỗ cũ thì tải được như thường.
    monkeypatch.chdir(ngoai)
    assert client.download_pdf(_DOI).thanh_cong is True
    assert (ngoai / "pdfs" / _TEN_TEP_PDF).is_file()


# ════════════════════════════════════════════════════════════════════════════
# 6. Tệp ghi dở không được báo «thành công»
# ════════════════════════════════════════════════════════════════════════════

def test_dut_mang_giua_chung_thi_luot_sau_khong_bao_thanh_cong_cho_tep_cut(kho_git, wiley_bat, monkeypatch):
    """(C) Đo 30/09/2026: đứt mạng giữa chừng ⇒ thư viện trả `STORAGE_ERROR` và để lại tệp ghi dở
    (4.009 byte); lượt sau trả `EXISTING_FILE` mà KHÔNG gọi mạng. Trước bản vá, kết quả của ta là
    `thanh_cong=True` cho PDF cụt đó, mãi tới khi có người xoá tệp."""
    monkeypatch.chdir(kho_git.thu_muc)
    client = WileyTdmClient()
    phien = _gan_phien(client, _pdf_tron_ven(20_000), dut_sau=4009)
    tep = kho_git.thu_muc / THU_MUC_TAI_MAC_DINH / _TEN_TEP_PDF

    lan_mot = client.download_pdf(_DOI)
    assert (lan_mot.trang_thai, lan_mot.thanh_cong, lan_mot.kich_thuoc_byte) == ("STORAGE_ERROR", False, None)
    assert tep.stat().st_size == 4009, "tệp ghi dở phải nằm thật trên đĩa thì ca này mới có nghĩa"
    assert "ghi dở" in lan_mot.ghi_chu and _TEN_TEP_PDF in lan_mot.ghi_chu, "phải chỉ ra tệp dở để người xoá"

    lan_hai = client.download_pdf(_DOI)
    assert len(phien.cac_url) == 1, "thư viện thấy tệp đã có nên không gọi mạng lần nữa"
    assert lan_hai.trang_thai == "EXISTING_FILE"
    assert lan_hai.thanh_cong is False, "PDF cụt 4.009/20.000 byte bị báo «thành công»"
    assert lan_hai.kich_thuoc_byte is None, "kích thước tệp dở không phải kích thước PDF đã tải"
    assert "ghi dở" in lan_hai.ghi_chu and _TEN_TEP_PDF in lan_hai.ghi_chu

    # Người xoá tệp dở, mạng hết đứt: tải lại ra PDF trọn vẹn.
    tep.unlink()
    phien.dut_sau = None
    lan_ba = client.download_pdf(_DOI)
    assert (lan_ba.trang_thai, lan_ba.thanh_cong, lan_ba.kich_thuoc_byte) == ("SUCCESS", True, 20_000)
    assert len(phien.cac_url) == 2
    lan_bon = client.download_pdf(_DOI)
    assert (lan_bon.trang_thai, lan_bon.thanh_cong, lan_bon.kich_thuoc_byte) == ("EXISTING_FILE", True, 20_000)
    assert kho_git.tep_git_thay() == [".gitignore"]


def test_may_chu_tra_200_ma_khong_phai_pdf_thi_khong_bao_thanh_cong(kho_git, wiley_bat, monkeypatch):
    """Thư viện lưu nguyên thân phản hồi 200 thành «.pdf» và báo `SUCCESS`, kể cả khi thân đó là
    một trang HTML báo lỗi. Cùng một phép kiểm cho `SUCCESS` và `EXISTING_FILE`: lượt đầu và lượt
    sau không được nói ngược nhau về cùng một tệp."""
    monkeypatch.chdir(kho_git.thu_muc)
    client = WileyTdmClient()
    _gan_phien(client, b"<html><body>Service temporarily unavailable</body></html>\n" * 40)
    lan_mot = client.download_pdf(_DOI)
    lan_hai = client.download_pdf(_DOI)
    assert (lan_mot.trang_thai, lan_mot.thanh_cong) == ("SUCCESS", False)
    assert (lan_hai.trang_thai, lan_hai.thanh_cong) == ("EXISTING_FILE", False)
    assert "%PDF" in lan_mot.ghi_chu and "%PDF" in lan_hai.ghi_chu


# ════════════════════════════════════════════════════════════════════════════
# 7. Rào `--luu` của tools/toan_van_guideline.py
# ════════════════════════════════════════════════════════════════════════════

def test_luu_vao_repo_qua_ten_khac_cua_cung_thu_muc_van_bi_tu_choi(tmp_path, monkeypatch):
    """(D) Đo 30/09/2026 trên macOS: `kiem_duong_luu("/users/…/<repo>/reports/x.txt")` trả None dù
    `samefile` xác nhận đó là thư mục trong repo — rào cũ so CHUỖI sau `Path.resolve()`, mà
    `resolve()` không đổi chữ hoa/thường. Trên hệ tệp phân biệt hoa/thường, bí danh là symlink."""
    goc = _ngoai_moi_cay_git(tmp_path) / "Repo-Gia"
    (goc / "reports").mkdir(parents=True)
    monkeypatch.setattr(T, "REPO", goc)
    assert T.kiem_duong_luu(str(goc / "reports" / "x.txt")) is not None, "đối chứng: đúng tên thì bị từ chối"
    assert T.kiem_duong_luu(str(tmp_path / "ngoai" / "x.txt")) is None, "đối chứng: ngoài repo thì được"
    for bi_danh in _cac_bi_danh(goc, tmp_path):
        assert T.kiem_duong_luu(str(bi_danh / "reports" / "x.txt")) is not None, f"lọt qua tên khác: {bi_danh}"
        chua_co = str(bi_danh / "chua-co" / "x.txt")
        assert T.kiem_duong_luu(chua_co) is not None, f"lọt khi chưa có thư mục cha: {bi_danh}"
        # Chiều ngược: chính REPO mang tên khác, đích mang tên thật.
        monkeypatch.setattr(T, "REPO", bi_danh)
        assert T.kiem_duong_luu(str(goc / "reports" / "x.txt")) is not None, f"lọt khi REPO là bí danh: {bi_danh}"
        monkeypatch.setattr(T, "REPO", goc)


def test_luu_vao_repo_chua_cong_cu_bi_tu_choi_ke_ca_cho_da_ignore():
    """Rào thứ nhất giữ nguyên độ chặt cũ: trong repo chứa công cụ thì cả chỗ `.gitignore` đã bắt
    cũng bị từ chối. Chỉ hỏi, không ghi gì vào repo."""
    for duong in (T.REPO / "reports" / "x.txt", T.REPO / "data" / "raw" / "x.txt",
                  T.REPO / THU_MUC_TAI_MAC_DINH / "x.txt", T.REPO / "chua" / "co" / "x.txt"):
        ly_do = T.kiem_duong_luu(str(duong))
        assert ly_do is not None and "trong repo" in ly_do, duong


def test_luu_vao_cay_git_khac_ma_git_thay_thi_bi_tu_choi(kho_git, tmp_path):
    """`REPO` chỉ là cây chứa công cụ. Đích nằm trong một cây git KHÁC (worktree khác, repo khác)
    mà git của cây đó thấy thì `git add -A` ở đó cũng cuốn toàn văn vào."""
    kho = kho_git.thu_muc
    assert not tng.nam_trong_thu_muc(kho / "reports" / "x.txt", T.REPO), "ca này cần một cây git KHÁC repo chứa công cụ"
    ly_do = T.kiem_duong_luu(str(kho / "reports" / "x.txt"))
    assert ly_do is not None and "cây git" in ly_do
    assert T.kiem_duong_luu(str(kho / THU_MUC_TAI_MAC_DINH / "x.txt")) is None, "chỗ cây đó đã ignore thì được"
    assert T.kiem_duong_luu(str(_ngoai_moi_cay_git(tmp_path) / "ngoai" / "x.txt")) is None


def test_khong_do_duoc_git_thi_luu_vao_cay_git_khac_bi_tu_choi(kho_git, tmp_path, monkeypatch):
    """Cùng luật với thư mục tải Wiley: đích trong một cây git mà không hỏi được git thì từ chối.
    Rào thứ nhất (repo chứa công cụ) và đích ngoài mọi cây git đều không cần git."""
    monkeypatch.setattr(tng, "_LENH_GIT", "git-khong-co-tren-may-nay")
    ly_do = T.kiem_duong_luu(str(kho_git.thu_muc / THU_MUC_TAI_MAC_DINH / "x.txt"))
    assert ly_do is not None and "không đo được" in ly_do and "không có lệnh" in ly_do
    assert T.kiem_duong_luu(str(_ngoai_moi_cay_git(tmp_path) / "ngoai" / "x.txt")) is None
    assert "trong repo" in T.kiem_duong_luu(str(T.REPO / "reports" / "x.txt"))


def test_lenh_luu_vao_cay_git_khac_tra_ma_tu_choi_va_khong_tai_khong_ghi(kho_git, monkeypatch, capsys):
    monkeypatch.setattr(T, "tai", lambda *a, **k: pytest.fail("bị từ chối thì không được tải"))
    dich = kho_git.thu_muc / "reports" / "x.txt"
    assert T.main(["pmc", "PMC1", "--luu", str(dich)]) == T.MA_TU_CHOI
    assert "TỪ CHỐI" in capsys.readouterr().out
    assert not dich.exists()
    assert kho_git.tep_git_thay() == [".gitignore"]
