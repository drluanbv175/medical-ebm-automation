"""Bộ test KHÔNG được chạm khoá ký thật ở `~/.ebm-secrets` — 05/10/2026.

Đo trước khi vá (bộ test đầy đủ ở 6503375 trên Mac của bác sĩ; đầu dò móc audit chặn TRƯỚC khi mở nên không byte nào
được đọc): 78 test / 22 tệp mở khoá HMAC chung `gate_approval_key` (555 lần) và khoá riêng Ed25519 của cả 5 vai
(`gate_ed25519_<VAI>.key`, 10 lần) để ký sổ cái tạm — 71 test ngay trong tiến trình pytest, 7 test qua tiến trình con
`approve_gate.py` / `run_g9_auto.py` / `g4_quality_gate.py`. Gốc: `gate_contract._base_key_path()` và
`_ed_private_dir()` rơi về `~/.ebm-secrets` khi EBM_GATE_KEY_PATH vắng, mà tests/conftest.py không đặt biến đó.

Ba lớp kiểm ở đây:
(1) khoá GIẢ (tests/conftest.py): mặc định cả phiên đặt lúc import + khoá mới cho từng test; gate_contract — kể cả
    trong tiến trình con — dùng khoá giả, khoá vai trò/Ed25519 nằm cạnh khoá giả; tên/thư mục khớp gate_contract và
    app/config (lệch là chốt canh nhìn sai chỗ);
(2) `CanhBiMat` (tests/canh_bi_mat_that.py) trên một thư mục TẠM đóng vai thư mục bí mật: chặn + ghi sổ mọi kiểu chạm
    (đọc, ghi, xoá, đổi tên, liệt kê, sao chép, liên kết…), miễn trừ chỉ cho ĐỌC, mã nuốt OSError vẫn bị ghi sổ;
(3) canary đầu–cuối: phiên pytest CON nạp conftest thật — test chạm thư mục được canh phải ĐỎ ở chính test đó, chạm
    lúc import phải làm phiên đỏ. Thư mục được canh trong canary là thư mục tạm: không test nào ở đây mở khoá thật.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import tests.conftest as C
from tests import canh_bi_mat_that as CBM
from tests.canh_ghi_du_lieu_that import NGOAI_TEST

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "tools"))

import gate_contract as GC  # noqa: E402

GHI = os.O_WRONLY | os.O_CREAT | os.O_TRUNC


# ════════════════════════════════════════════════════════════════════════════
# (1) Khoá GIẢ của conftest
# ════════════════════════════════════════════════════════════════════════════

def _khoa_hien_tai() -> Path:
    return Path(os.environ[C.KHOA_ENV])


def test_bien_moi_truong_khop_gate_contract():
    assert C.KHOA_ENV == GC._SIGNING_KEY_ENV == "EBM_GATE_KEY_PATH"


def test_moi_test_co_khoa_gia_rieng_ngoai_thu_muc_bi_mat():
    khoa = _khoa_hien_tai()
    assert khoa.is_file() and khoa.name == CBM.TEN_KHOA_GIA
    assert khoa.read_text(encoding="utf-8").startswith("pytest-khoa-gia-khong-phai-khoa-that-")
    assert khoa != C.KHOA_GIA_PHIEN, "fixture từng test phải thay khoá mặc định của phiên"
    assert C._CANH_BI_MAT_THAT.tuong_doi(khoa) is None, "khoá giả không được nằm trong thư mục bí mật thật"
    assert GC._base_key_path() == khoa
    assert GC._ed_private_dir() == khoa.parent, "khoá riêng Ed25519 phải được tìm CẠNH khoá giả"
    assert GC.signing_key_path("STATISTICIAN") == khoa, "chưa có khoá vai trò ⇒ khoá chung giả, không phải khoá thật"


def test_khoa_mac_dinh_cua_phien_dat_luc_import():
    assert C.KHOA_GIA_PHIEN.is_file() and C.KHOA_GIA_PHIEN.name == CBM.TEN_KHOA_GIA
    assert C._CANH_BI_MAT_THAT.tuong_doi(C.KHOA_GIA_PHIEN) is None


def test_khoa_vai_tro_nam_canh_khoa_gia_ky_pham_vi_role():
    """Đúng quy ước test G4/G5 (tests/g5_test_helpers.py): khoá vai trò `<khoá>_STATISTICIAN` đặt cạnh khoá giả."""
    khoa = _khoa_hien_tai()
    vai = khoa.with_name(f"{khoa.name}_STATISTICIAN")
    vai.write_text("khoa-vai-tro-gia", encoding="utf-8", newline="\n")
    assert GC.signing_key_path("STATISTICIAN") == vai
    assert GC.per_role_key_available("STATISTICIAN") is True
    chu_ky = GC.sign_approval("G4", "PYTEST-KHOA-GIA", "a" * 64, "2026-10-05T00:00:00+00:00",
                              reviewer_role="METHODS_STATISTICS_REVIEWER", reviewer_ref="REF-KHOA-GIA",
                              decision="APPROVED")
    assert chu_ky is not None and chu_ky.startswith("v4:role:"), chu_ky


def test_tien_trinh_con_ke_thua_khoa_gia():
    """7 test cũ chạm khoá thật QUA TIẾN TRÌNH CON: con kế thừa os.environ (khoá giả + PYTEST_CURRENT_TEST)."""
    ma = ("import sys; sys.path.insert(0, sys.argv[1]); import gate_contract as GC; "
          "print(GC._base_key_path()); print(GC._ed_private_dir())")
    kq = subprocess.run([sys.executable, "-c", ma, str(REPO_ROOT / "tools")], cwd=REPO_ROOT,
                        capture_output=True, text=True, timeout=120)
    assert kq.returncode == 0, kq.stderr
    dong = kq.stdout.strip().splitlines()
    khoa = _khoa_hien_tai()
    assert dong[-2:] == [str(khoa), str(khoa.parent)], kq.stdout


def test_ten_va_thu_muc_khop_gate_contract():
    """Chốt canh nhìn đúng thư mục mà gate_contract rơi về khi thiếu biến — lệch là canh sai chỗ, im lặng."""
    assert GC._DEFAULT_KEY_PATH == CBM.THU_MUC_BI_MAT_THAT / CBM.TEN_KHOA_GIA
    assert GC._ED_PRIVATE_DIR == CBM.THU_MUC_BI_MAT_THAT
    assert C._CANH_BI_MAT_THAT.goc == CBM.THU_MUC_BI_MAT_THAT
    # chỉ tính đường dẫn (thuần chuỗi) — không mở, không liệt kê gì
    assert C._CANH_BI_MAT_THAT.xet("open", (str(GC._DEFAULT_KEY_PATH), "r", os.O_RDONLY)) == [CBM.TEN_KHOA_GIA]
    ed = str(GC._ED_PRIVATE_DIR / "gate_ed25519_IRB.key")
    # Chốt canh trả đường dẫn tương đối ĐÃ normcase (Windows: chữ thường — hệ tệp không phân biệt hoa thường) ⇒ so
    # cùng phép chuẩn hoá. CI Windows 05/10/2026 đỏ: ['gate_ed25519_irb.key'] == ['gate_ed25519_IRB.key'].
    assert C._CANH_BI_MAT_THAT.xet("open", (ed, "rb", os.O_RDONLY)) == [os.path.normcase("gate_ed25519_IRB.key")]


def test_mien_tru_khop_app_config_va_chi_cho_doc():
    from app.config import _SECRETS_ENV

    assert _SECRETS_ENV.parent == CBM.THU_MUC_BI_MAT_THAT
    assert _SECRETS_ENV.name == C.TEP_ENV_APP_CONFIG
    assert C._CANH_BI_MAT_THAT.xet("open", (str(_SECRETS_ENV), "r", os.O_RDONLY)) == []
    assert C._CANH_BI_MAT_THAT.xet("open", (str(_SECRETS_ENV), "w", GHI)) == [C.TEP_ENV_APP_CONFIG]
    assert C._CANH_BI_MAT_THAT.xet("os.remove", (str(_SECRETS_ENV), None)) == [C.TEP_ENV_APP_CONFIG]


def test_chot_that_dang_ky_dung_mot_lan():
    cac = [c for c in CBM.cac_canh() if c.goc == CBM.THU_MUC_BI_MAT_THAT]
    assert len(cac) == 1 and cac[0] is C._CANH_BI_MAT_THAT
    assert CBM._da_gan_moc is True


def test_hook_logstart_logfinish_gan_nhan_cho_chot_bi_mat(request):
    try:
        C.pytest_runtest_logstart("tep_gia.py::test_gia", None)
        assert C._CANH_BI_MAT_THAT.test_dang_chay == "tep_gia.py::test_gia"
        C.pytest_runtest_logfinish("tep_gia.py::test_gia", None)
        assert C._CANH_BI_MAT_THAT.test_dang_chay == NGOAI_TEST
    finally:
        C.pytest_runtest_logstart(request.node.nodeid, None)   # trả nhãn của chính test này cho chốt thật


def test_tao_khoa_gia_ngau_nhien_va_khong_ghi_de(tmp_path):
    a = CBM.tao_khoa_gia(tmp_path / "a")
    b = CBM.tao_khoa_gia(tmp_path / "b")
    assert a.read_text(encoding="utf-8") != b.read_text(encoding="utf-8")
    if os.name == "posix":
        assert (a.stat().st_mode & 0o777) == 0o600
    with pytest.raises(FileExistsError):
        CBM.tao_khoa_gia(tmp_path / "a")


# ════════════════════════════════════════════════════════════════════════════
# (2) CanhBiMat trên một thư mục TẠM đóng vai thư mục bí mật
# ════════════════════════════════════════════════════════════════════════════

@pytest.fixture()
def kho(tmp_path):
    goc = tmp_path / "cha" / "bi_mat"
    goc.mkdir(parents=True)
    (goc / "gate_approval_key").write_text("khoa-trong-kho-duoc-canh", encoding="utf-8", newline="\n")
    (goc / "app.env").write_text("TEN=gia\n", encoding="utf-8", newline="\n")
    return goc


@pytest.fixture()
def canh(kho, request):
    """Chốt tạm đăng ký vào móc audit thật; gỡ ở finalizer — TRƯỚC báo cáo teardown — nên conftest không gán các lần
    chạm cố ý ở đây thành lỗi của test."""
    c = CBM.dang_ky(CBM.CanhBiMat(kho, mien_tru_doc=("app.env",)))
    c.test_dang_chay = request.node.nodeid
    try:
        yield c
    finally:
        CBM.huy_dang_ky(c)


def _cac_su_kien(canh: CBM.CanhBiMat):
    return [(vp.su_kien, vp.tuong_doi) for vp in canh.vi_pham]


def test_chan_doc_khoa_va_ghi_so_dung_test(canh, kho, request):
    with pytest.raises(CBM.ChanBiMat):
        (kho / "gate_approval_key").read_text(encoding="utf-8")
    with pytest.raises(PermissionError):   # ChanBiMat LÀ PermissionError ⇒ mã bắt OSError xử như máy chưa có khoá
        open(kho / "gate_approval_key", "rb")
    assert _cac_su_kien(canh) == [("open (đọc)", "gate_approval_key")] * 2
    assert {vp.test for vp in canh.vi_pham} == {request.node.nodeid}


def test_ma_nuot_oserror_van_bi_ghi_so(canh, kho):
    """Đúng đường đã gặp: gate_contract._read_key bọc `except OSError` ⇒ lỗi chặn bị nuốt, ký trả None, test vẫn xanh.
    Vì vậy móc PHẢI ghi sổ trước khi ném — conftest đánh đỏ theo sổ, không theo ngoại lệ."""
    assert GC._read_key(kho / "gate_approval_key") is None
    assert _cac_su_kien(canh) == [("open (đọc)", "gate_approval_key")]


def test_chan_moi_kieu_cham_va_khoa_con_nguyen(canh, kho, tmp_path):
    khoa = kho / "gate_approval_key"
    truoc = khoa.stat()
    thao_tac = {
        "ghi tệp mới": lambda: (kho / "moi.txt").write_text("x", encoding="utf-8", newline="\n"),
        "mở r+": lambda: open(khoa, "r+", encoding="utf-8"),
        "os.open đọc": lambda: os.open(khoa, os.O_RDONLY),
        "xoá": khoa.unlink,
        "đổi tên ra ngoài": lambda: os.rename(khoa, tmp_path / "ra_ngoai"),
        "liệt kê": lambda: os.listdir(kho),
        "sao chép": lambda: shutil.copyfile(khoa, tmp_path / "ban_sao"),
        "liên kết cứng ra ngoài": lambda: os.link(khoa, tmp_path / "lien_ket_cung"),
        "symlink vào trong": lambda: os.symlink(tmp_path / "dau_do", kho / "lien_ket"),
        "mkdir": lambda: os.mkdir(kho / "con"),
        "chmod": lambda: os.chmod(khoa, 0o644),
        "touch": lambda: os.utime(khoa),
        "truncate": lambda: os.truncate(khoa, 0),
        "rmtree chính nó": lambda: shutil.rmtree(kho),
        "rmtree thư mục CHA": lambda: shutil.rmtree(kho.parent),
    }
    lot = [ten for ten, lam in thao_tac.items() if not _bi_chan(lam)]
    assert lot == [], f"các thao tác này KHÔNG bị chặn: {lot}"
    # Path.glob/rglob NUỐT OSError khi quét thư mục (coi như thư mục không đọc được) ⇒ không ném, nhưng lần quét đã bị
    # chặn (không lộ tên tệp nào) và vẫn được ghi sổ — đúng lý do móc phải ghi sổ trước khi ném.
    da_ghi = len(canh.vi_pham)
    assert list(kho.glob("gate_*")) == [] and list(kho.rglob("*")) == []
    quet = [vp.su_kien for vp in canh.vi_pham[da_ghi:]]
    assert quet and set(quet) == {"os.scandir"}, quet
    sau = khoa.stat()   # stat không phải sự kiện audit ⇒ không bị chặn
    assert (sau.st_size, sau.st_mtime_ns) == (truoc.st_size, truoc.st_mtime_ns)
    for ten in ("moi.txt", "con", "lien_ket"):
        assert not os.path.lexists(kho / ten)
    for ten in ("ra_ngoai", "ban_sao", "lien_ket_cung"):
        assert not os.path.lexists(tmp_path / ten)
    su_kien = {sk for sk, _td in _cac_su_kien(canh)}
    for can in ("open (ghi)", "open (đọc)", "os.remove", "os.rename", "shutil.copyfile", "os.link", "os.symlink",
                "os.mkdir", "os.chmod", "os.utime", "os.truncate", "shutil.rmtree"):
        assert can in su_kien, (can, su_kien)
    assert su_kien & {"os.listdir", "os.scandir"}, su_kien
    assert ("shutil.rmtree", ".") in _cac_su_kien(canh), "xoá thư mục CHA phải được tính là xoá thư mục bí mật"


def _bi_chan(lam) -> bool:
    try:
        kq = lam()
    except CBM.ChanBiMat:
        return True
    if isinstance(kq, int):
        os.close(kq)
    elif hasattr(kq, "close"):
        kq.close()
    return False


def test_mien_tru_chi_cho_doc(canh, kho):
    assert (kho / "app.env").read_text(encoding="utf-8") == "TEN=gia\n"
    assert canh.vi_pham == []
    with pytest.raises(CBM.ChanBiMat):
        (kho / "app.env").write_text("TEN=khac\n", encoding="utf-8", newline="\n")
    with pytest.raises(CBM.ChanBiMat):
        open(kho / "app.env", "a", encoding="utf-8")
    assert _cac_su_kien(canh) == [("open (ghi)", "app.env")] * 2


def test_duong_dan_tuong_doi_va_vong_ve_van_bi_bat(canh, kho, monkeypatch):
    monkeypatch.chdir(kho.parent)
    with pytest.raises(CBM.ChanBiMat):
        open(os.path.join("bi_mat", "gate_approval_key"), encoding="utf-8")
    with pytest.raises(CBM.ChanBiMat):
        open(kho.parent / "khac" / ".." / "bi_mat" / "gate_approval_key", encoding="utf-8")
    assert _cac_su_kien(canh) == [("open (đọc)", "gate_approval_key")] * 2


def test_thu_muc_ten_giong_khong_bi_va_lay(canh, kho):
    """Ranh giới thư mục: `bi_mat_khac/` có cùng tiền tố chuỗi với `bi_mat` nhưng KHÔNG nằm trong nó."""
    ben_canh = kho.parent / "bi_mat_khac"
    ben_canh.mkdir()
    (ben_canh / "gate_approval_key").write_text("khong-lien-quan", encoding="utf-8", newline="\n")
    assert (ben_canh / "gate_approval_key").read_text(encoding="utf-8") == "khong-lien-quan"
    assert sorted(os.listdir(ben_canh)) == ["gate_approval_key"]
    assert canh.vi_pham == []


def test_goc_la_symlink_bat_ca_hai_dang_duong_dan(tmp_path):
    that = tmp_path / "that"
    that.mkdir()
    (that / "gate_approval_key").write_text("khoa", encoding="utf-8", newline="\n")
    lien_ket = tmp_path / "lien_ket"
    try:
        os.symlink(that, lien_ket, target_is_directory=True)
    except (OSError, NotImplementedError) as loi:
        pytest.skip(f"máy không cho tạo symlink: {loi}")
    c = CBM.dang_ky(CBM.CanhBiMat(lien_ket))
    try:
        for duong in (lien_ket / "gate_approval_key", that / "gate_approval_key"):
            with pytest.raises(CBM.ChanBiMat):
                open(duong, encoding="utf-8")
    finally:
        CBM.huy_dang_ky(c)
    assert [vp.tuong_doi for vp in c.vi_pham] == ["gate_approval_key"] * 2


def test_moc_khong_nem_khi_trang_thai_module_hong(monkeypatch):
    """Móc audit gắn cho CẢ tiến trình và không gỡ được: chỉ được ném ChanBiMat, không bao giờ lỗi nội bộ."""
    monkeypatch.setattr(CBM, "_SU_KIEN", None)   # giả lập biến module bị dọn lúc trình thông dịch tắt
    CBM._moc_audit("open", ("bat_ky.json", "r", os.O_RDONLY))


def test_loi_noi_bo_duoc_dem_va_lam_tong_ket_do(kho, monkeypatch):
    c = CBM.CanhBiMat(kho)

    def _hong(*_a, **_k):
        raise RuntimeError("giả lập hỏng")

    monkeypatch.setattr(c, "xet", _hong)
    assert c.nhan("open", (str(kho / "gate_approval_key"), "r", os.O_RDONLY)) is False
    assert c.loi_noi_bo == 1
    assert any("KHÔNG ĐO ĐƯỢC" in d for d in CBM.tong_ket([c]))


def test_tong_ket_va_rut_cua_test(kho):
    c = CBM.CanhBiMat(kho)
    assert CBM.tong_ket([c]) == []
    c.test_dang_chay = "tep.py::test_mot"
    assert c.nhan("open", (str(kho / "gate_approval_key"), "r", os.O_RDONLY)) is True
    c.test_dang_chay = NGOAI_TEST
    assert c.nhan("os.listdir", (str(kho),)) is True
    assert c.nhan("open", (str(kho.parent / "ngoai.txt"), "r", os.O_RDONLY)) is False
    assert [vp.tuong_doi for vp in c.rut_cua_test("tep.py::test_mot")] == ["gate_approval_key"]
    assert c.rut_cua_test("tep.py::test_mot") == [], "mỗi lần chạm chỉ được báo một lần"
    van_ban = "\n".join(CBM.tong_ket([c]))
    assert "1 lần" in van_ban and "os.listdir: ." in van_ban and NGOAI_TEST in van_ban, van_ban


# ════════════════════════════════════════════════════════════════════════════
# (3) Canary đầu–cuối: phiên pytest CON, conftest thật, thư mục được canh là thư mục TẠM
# ════════════════════════════════════════════════════════════════════════════

_DAU_TEP_CON = '''
import json
import os
import sys
from pathlib import Path

from tests import canh_bi_mat_that as CBM

TAM = Path(__file__).resolve().parent
KHO = TAM / "kho_bi_mat"
KHO.mkdir()
(KHO / "gate_approval_key").write_text("khoa-trong-kho-duoc-canh", encoding="utf-8")
CANH = CBM.dang_ky(CBM.CanhBiMat(KHO))
SO = TAM / "so_khoa.jsonl"


def _ghi(nhan):
    p = os.environ.get("EBM_GATE_KEY_PATH")
    with open(SO, "a", encoding="utf-8") as fh:
        fh.write(json.dumps({"nhan": nhan, "khoa": p, "co_tep": bool(p) and Path(p).is_file()}) + "\\n")


_ghi("import")
'''


def _chay_pytest_con(tmp_path, than_tep: str, them=()) -> subprocess.CompletedProcess:
    """Một phiên pytest con trên MỘT tệp test tạm, nạp tests/conftest.py thật làm plugin."""
    tep = tmp_path / "test_con.py"
    tep.write_text(_DAU_TEP_CON + than_tep, encoding="utf-8", newline="\n")
    env = {k: v for k, v in os.environ.items() if k != "MRAQ_OFFLINE_CI"}
    env.update(PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    return subprocess.run(
        [sys.executable, "-B", "-m", "pytest", "-p", "tests.conftest", "-p", "no:cacheprovider", "-q",
         "--basetemp", str(tmp_path / "bt"), *them, str(tep)],
        cwd=REPO_ROOT, env=env, capture_output=True, text=True, timeout=300,
    )


def _dong_thong_ke(kq: subprocess.CompletedProcess) -> str:
    cac_dong = [d for d in kq.stdout.splitlines() if re.search(r"\b\d+ (passed|failed|error)", d) and " in " in d]
    assert cac_dong, f"không thấy dòng thống kê của pytest:\n{kq.stdout}\n{kq.stderr}"
    return cac_dong[-1]


def test_canary_khoa_gia_va_test_cham_bi_mat_thi_do(tmp_path):
    khoa_cha = os.environ[C.KHOA_ENV]
    kq = _chay_pytest_con(tmp_path, '''
sys.path.insert(0, str(Path.cwd() / "tools"))
import gate_contract as GC


def test_a():
    _ghi("a")


def test_b():
    _ghi("b")


def test_cham_kho_ma_nuot_loi():
    assert GC._read_key(KHO / "gate_approval_key") is None


def test_sach():
    assert KHO.name == "kho_bi_mat"
''')
    ra = kq.stdout + kq.stderr
    assert kq.returncode == 1, ra
    thong_ke = _dong_thong_ke(kq)
    assert re.search(r"\b4 passed\b", thong_ke) and re.search(r"\b1 error\b", thong_ke) and "failed" not in thong_ke, \
        f"đúng MỘT test chạm thư mục được canh phải lỗi ở teardown, test sạch không bị vạ lây: {thong_ke}\n{ra}"
    assert "CHỐT CANH BÍ MẬT THẬT" in ra and "open (đọc): gate_approval_key" in ra, ra
    assert re.search(r"^ERROR \S*::test_cham_kho_ma_nuot_loi(?:\s|$)", kq.stdout, re.M), ra
    assert not re.search(r"^(?:ERROR|FAILED) \S*::test_(?:a|b|sach)(?:\s|$)", kq.stdout, re.M), ra

    so = {d["nhan"]: d for d in map(json.loads, (tmp_path / "so_khoa.jsonl").read_text(encoding="utf-8").splitlines())}
    assert set(so) == {"import", "a", "b"}, so
    assert all(d["co_tep"] for d in so.values()), so
    luc_import, a, b = so["import"]["khoa"], so["a"]["khoa"], so["b"]["khoa"]
    assert luc_import != khoa_cha, "conftest phải ÉP khoá mặc định của phiên, không nhận biến kế thừa từ ngoài"
    assert len({luc_import, a, b}) == 3, f"mỗi test một khoá giả mới, khác khoá mặc định của phiên: {so}"
    for p in (luc_import, a, b):
        assert C._CANH_BI_MAT_THAT.tuong_doi(p) is None, p


def test_canary_cham_bi_mat_luc_import_lam_phien_do(tmp_path):
    kq = _chay_pytest_con(tmp_path, '''
try:
    (KHO / "gate_approval_key").read_text(encoding="utf-8")
except PermissionError:
    pass


def test_sach():
    assert True
''')
    ra = kq.stdout + kq.stderr
    assert kq.returncode == 1, f"không test nào đỏ nhưng phiên vẫn phải thoát khác 0:\n{ra}"
    thong_ke = _dong_thong_ke(kq)
    assert re.search(r"\b1 passed\b", thong_ke) and "error" not in thong_ke and "failed" not in thong_ke, thong_ke
    assert "chốt canh thư mục bí mật thật" in kq.stdout and "open (đọc): gate_approval_key" in kq.stdout, ra
    assert NGOAI_TEST in kq.stdout, ra


def test_canary_no_summary_van_noi_vi_sao_do(tmp_path):
    kq = _chay_pytest_con(tmp_path, '''
try:
    (KHO / "gate_approval_key").read_text(encoding="utf-8")
except PermissionError:
    pass


def test_sach():
    assert True
''', them=("--no-summary",))
    assert kq.returncode == 1, kq.stdout + kq.stderr
    assert "CHỐT CANH THƯ MỤC BÍ MẬT THẬT — LỖI" in kq.stderr and "gate_approval_key" in kq.stderr, kq.stderr
