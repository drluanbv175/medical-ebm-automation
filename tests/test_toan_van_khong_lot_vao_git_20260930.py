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

`tools/toan_van_guideline.py --luu` đã có ca riêng (từ chối đường dẫn trong repo) ở
tests/test_toan_van_guideline_cli_20260924.py.

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
from pathlib import Path
from typing import List, Optional

import pytest
import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.config import BASE_DIR, settings  # noqa: E402
from app.sources.wiley_tdm import THU_MUC_TAI_MAC_DINH, WileyTdmClient  # noqa: E402
from app.utils import http as http_mod  # noqa: E402

# Chụp lúc NẠP module (trước mọi monkeypatch): nhiều test khác vá `_CACHE_DIR` sang tmp_path.
_CACHE_DIR_THAT = http_mod._CACHE_DIR

_DOI = "10.1002/jcsm.70385"
_TEN_TEP_PDF = "10.1002-jcsm.70385.pdf"  # thư viện đổi «/» trong DOI thành «-»
_TOKEN_GIA = "00000000-0000-4000-8000-000000000000"  # đúng khuôn UUID mà thư viện đòi, không phải token thật


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
    thu_muc.mkdir()
    kq = subprocess.run(["git", "init", "-q", str(thu_muc)], capture_output=True, text=True, env=env, timeout=60)
    assert kq.returncode == 0, f"git init hỏng: {kq.stderr}"
    # Kho mới sinh có thể nhận `info/exclude` từ thư mục mẫu của máy — dọn cho chắc.
    thong_tin = thu_muc / ".git" / "info"
    thong_tin.mkdir(exist_ok=True)
    (thong_tin / "exclude").write_text("", encoding="utf-8", newline="\n")
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
    """Phản hồi 200 của `api.wiley.com` — đủ những gì `TDMClient._download_pdf` đọc."""

    status_code = 200
    text = ""

    def __init__(self, noi_dung: bytes) -> None:
        self._noi_dung = noi_dung
        self.headers: dict = {}

    def iter_content(self, chunk_size: int = 8192):
        for dau in range(0, len(self._noi_dung), chunk_size):
            yield self._noi_dung[dau:dau + chunk_size]


class _PhienWileyGia:
    """Thay `TDMClient._api_session` — biên mạng DUY NHẤT của thư viện bị thay trong ca tải thử."""

    def __init__(self, noi_dung: bytes) -> None:
        self._noi_dung = noi_dung
        self.cac_url: List[str] = []

    def get(self, url, **_):
        self.cac_url.append(url)
        return _PhanHoiWileyGia(self._noi_dung)


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

    noi_dung = b"%PDF-1.7\n" + b"x" * 19_991  # 20.000 byte; thư viện báo round(20000 / 1024) = 20
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
