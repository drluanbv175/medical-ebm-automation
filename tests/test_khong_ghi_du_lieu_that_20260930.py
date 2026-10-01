"""Bộ test KHÔNG được ghi vào thư mục dữ liệu thật của cây (`data/`) — 30/09/2026.

Đo trước khi vá (bản clone sạch, 6.446 test): mỗi lượt pytest để lại 35 payload GIẢ trong `data/raw/` (5 tệp test
gọi `search()` live với `get_json` giả mà `save_raw()` thật vẫn chạy), 5 tệp `processed/pipeline_*.json`, 4 tệp
`exports/` và một lô `tiktok/`. Ba lớp kiểm ở đây:

(1) fixture `_du_lieu_test_vao_thu_muc_tam` (tests/conftest.py): `settings.data_dir` và các hằng module chốt đường
    dẫn lúc import đều trỏ sang thư mục tạm; connector chạy live với `get_json` giả ghi payload vào ĐÓ;
(2) `CanhGhi` (tests/canh_ghi_du_lieu_that.py): nhận đúng sự kiện ghi/đổi tên/xoá, đúng miễn trừ, không ném lỗi,
    fail-closed khi tự hỏng; so danh sách tệp đầu↔cuối phiên;
(3) canary đầu–cuối: một phiên pytest CON có test cố ý ghi vào thư mục được canh phải ĐỎ — chứng minh chốt BẮT được,
    không chỉ «có mặt». Thư mục được canh trong canary là thư mục tạm: canary không bao giờ ghi vào `data/` thật.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import app.services.translate as translate_mod
import app.social.package as tiktok_mod
import app.utils.http as http_mod
import tests.conftest as C
from app.config import BASE_DIR, settings
from app.sources.core_api import CoreClient
from tests.canh_ghi_du_lieu_that import (
    NGOAI_TEST,
    CanhGhi,
    ViPham,
    cac_canh,
    chup,
    dang_ky,
    huy_dang_ky,
    so_sanh,
    tong_ket,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
GHI = os.O_WRONLY | os.O_CREAT | os.O_TRUNC


def _nam_duoi(con: Path, cha: Path) -> bool:
    con, cha = Path(os.path.realpath(con)), Path(os.path.realpath(cha))
    return con == cha or cha in con.parents


# ════════════════════════════════════════════════════════════════════════════
# (1) Fixture chuyển hướng thư mục dữ liệu
# ════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="session", autouse=True)
def _data_dir_luc_fixture_session_chay():
    """Fixture phạm vi SESSION của một tệp test được dựng trước mọi fixture phạm vi module/function — phải thấy thư
    mục tạm rồi. `autouse` để nó được dựng ngay ở test ĐẦU TIÊN của tệp: fixture chuyển hướng mà bị hạ xuống phạm vi
    hẹp hơn thì lúc đó chưa kịp chạy, và fixture này sẽ thấy `data/` thật."""
    return Path(settings.data_dir)


def test_thu_muc_du_lieu_that_duoc_chot_dung_cho():
    assert C._DU_LIEU_THAT == BASE_DIR / "data"
    assert C._CANH_DU_LIEU_THAT.goc == BASE_DIR / "data"
    assert any(c is C._CANH_DU_LIEU_THAT for c in cac_canh()), "chốt canh thư mục dữ liệu thật chưa được đăng ký"


def test_settings_data_dir_la_thu_muc_tam_co_du_thu_muc_con():
    assert not _nam_duoi(settings.data_dir, C._DU_LIEU_THAT), f"data_dir vẫn là dữ liệu thật: {settings.data_dir}"
    for thu_muc in (settings.raw_dir, settings.processed_dir, settings.reports_dir, settings.exports_dir,
                    settings.archive_dir):
        assert thu_muc.is_dir() and not _nam_duoi(thu_muc, C._DU_LIEU_THAT), thu_muc


def test_chuyen_huong_co_hieu_luc_tu_truoc_fixture_pham_vi_rong_cua_tep_test(_data_dir_luc_fixture_session_chay):
    assert not _nam_duoi(_data_dir_luc_fixture_session_chay, C._DU_LIEU_THAT)
    assert _data_dir_luc_fixture_session_chay == settings.data_dir, "cả phiên dùng MỘT thư mục tạm"


def test_hang_chot_luc_import_tro_sang_thu_muc_tam():
    """Ba module này được import ở ĐẦU tệp test (lúc thu thập, trước fixture) ⇒ hằng của chúng chốt theo `data/`
    thật; fixture phải vá từng cái. `_CACHE_DIR` còn phải TỒN TẠI: `_write_cache` nuốt OSError nên thiếu thư mục
    là mất cache im lặng."""
    assert http_mod._CACHE_DIR == settings.raw_dir / "_http_cache" and http_mod._CACHE_DIR.is_dir()
    assert tiktok_mod.TIKTOK_DIR == settings.data_dir / "tiktok"
    assert tiktok_mod.QUEUE_PATH == settings.data_dir / "tiktok" / "queue.txt"
    assert translate_mod._CACHE_PATH == settings.processed_dir / "_translations_vi.json"
    for ten_module, ten_hang, _ in C._HANG_CHOT_LUC_IMPORT:
        gia_tri = getattr(sys.modules[ten_module], ten_hang)
        assert not _nam_duoi(gia_tri, C._DU_LIEU_THAT), f"{ten_module}.{ten_hang} vẫn trỏ vào dữ liệu thật: {gia_tri}"


def test_phan_data_trong_git_co_mat_trong_thu_muc_tam():
    """Thư mục tạm phải giống một bản checkout sạch: `data/reference/` (nằm trong git) có đủ, đúng nội dung."""
    that = C._DU_LIEU_THAT / "reference"
    cac_tep = [p for p in that.rglob("*") if p.is_file()]
    assert cac_tep, "data/reference/ của cây trống — tệp tham chiếu 45 thang điểm nằm trong git"
    for tep in cac_tep:
        ban_sao = settings.data_dir / "reference" / tep.relative_to(that)
        assert ban_sao.is_file() and ban_sao.read_bytes() == tep.read_bytes(), ban_sao


def test_connector_live_voi_get_json_gia_ghi_payload_vao_thu_muc_tam(monkeypatch):
    """Đúng lỗi đã đo: test thay `get_json` bằng hàm giả, `save_raw()` thật vẫn chạy. Payload phải nằm ở thư mục tạm
    và tiến trình này không được mở tệp nào để ghi dưới `data/` thật."""
    monkeypatch.setattr(settings, "core_api_key", "KHOA_GIA")
    client = CoreClient()
    client.use_mock = False
    monkeypatch.setattr(client.http, "get_json", lambda url, params=None, **kw: {"totalHits": 0, "results": []})
    thu_muc = settings.raw_dir / "core"
    truoc = set(thu_muc.glob("*.json")) if thu_muc.is_dir() else set()
    so_vi_pham_truoc = len(C._CANH_DU_LIEU_THAT.vi_pham)

    assert client.search("truy van canh du lieu that") == []

    moi = set(thu_muc.glob("*.json")) - truoc
    assert len(moi) == 1, f"save_raw() phải ghi đúng một payload vào {thu_muc}, thấy: {sorted(moi)}"
    (tep,) = moi
    assert tep.name.endswith("_truy_van_canh_du_lieu_that.json") and not _nam_duoi(tep, C._DU_LIEU_THAT)
    assert C._CANH_DU_LIEU_THAT.vi_pham[so_vi_pham_truoc:] == []


def test_mien_tru_cua_chot_canh_that_chi_gom_hai_lo_da_biet():
    """Khoá danh sách miễn trừ: thêm một miễn trừ là nới chốt — phải sửa cả test này, để người duyệt PR thấy."""
    canh = C._CANH_DU_LIEU_THAT
    assert canh.duoc_mien("archive/app.log") and canh.duoc_mien("archive")
    assert canh.duoc_mien("processed/chronic_care_phase_3a_audit.jsonl")
    for bi_canh in ("raw/core/x.json", "raw/_http_cache/ab.json", "raw/_state/serpapi_usage.json",
                    "processed/pipeline_20260930T132226.json", "processed/_translations_vi.json",
                    "reports/x.md", "exports/dashboard_master_ebm_20260930.xlsx", "tiktok/20260930-2025-tuso/a.png",
                    "reference/clinical_scores_45.json", "retraction_watch/retraction_watch.csv", "medical_ebm.db",
                    "archive_khac/app.log", "processed/chronic_care_phase_3a_audit.jsonl.bak"):
        assert not canh.duoc_mien(bi_canh), bi_canh
    goc = C._DU_LIEU_THAT
    assert canh.xet("open", (str(goc / "raw" / "core" / "x.json"), "w", GHI)) == ["raw/core/x.json"]
    assert canh.xet("open", (str(goc / "archive" / "app.log"), "a", GHI | os.O_APPEND)) == []
    assert canh.xet("open", (str(goc / "raw" / "core" / "x.json"), "r", os.O_RDONLY)) == []


# ════════════════════════════════════════════════════════════════════════════
# (2) CanhGhi — phần thuần: một sự kiện audit có phải là ghi vào thư mục được canh không
# ════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def kho(tmp_path):
    goc = tmp_path / "kho"
    (goc / "raw" / "core").mkdir(parents=True)
    (goc / "archive").mkdir()
    (goc / "processed").mkdir()
    return goc


@pytest.fixture
def canh(kho):
    return CanhGhi(kho, mien_tru_thu_muc=("archive",), mien_tru_tep=("processed/lo_da_biet.jsonl",))


def test_open_chi_tinh_khi_mo_de_ghi(canh, kho, tmp_path):
    tep = str(kho / "raw" / "core" / "a.json")
    for che_do, co in (("w", GHI), ("a", os.O_WRONLY | os.O_CREAT | os.O_APPEND), ("x", GHI | os.O_EXCL),
                       ("r+", os.O_RDWR), (None, os.O_WRONLY | os.O_CREAT), ("w", None), ("rb+", None)):
        assert canh.xet("open", (tep, che_do, co)) == ["raw/core/a.json"], (che_do, co)
    for che_do, co in (("r", os.O_RDONLY), ("rb", os.O_RDONLY), (None, os.O_RDONLY), ("r", None), (None, None)):
        assert canh.xet("open", (tep, che_do, co)) == [], (che_do, co)
    # cờ không phải «ghi» (O_NONBLOCK: shutil.rmtree mở THƯ MỤC bằng cờ này trên macOS) không được tính
    assert canh.xet("open", (str(kho / "raw"), None, os.O_RDONLY | getattr(os, "O_NONBLOCK", 0))) == []
    assert canh.xet("open", (str(tmp_path / "ngoai.json"), "w", GHI)) == []          # ngoài thư mục được canh
    assert canh.xet("open", (str(kho) + "_khac/raw/a.json", "w", GHI)) == []         # chung tiền tố tên, khác thư mục
    assert canh.xet("open", (7, "w", GHI)) == []                                     # mở theo file descriptor
    assert canh.xet("open", ()) == [] and canh.xet("su.kien.la", (tep, "w", GHI)) == []


def test_open_nhan_bytes_pathlike_va_duong_dan_tuong_doi(canh, kho, monkeypatch):
    tep = kho / "raw" / "core" / "a.json"
    assert canh.xet("open", (os.fsencode(str(tep)), "w", GHI)) == ["raw/core/a.json"]
    assert canh.xet("open", (tep, "w", GHI)) == ["raw/core/a.json"]
    monkeypatch.chdir(kho.parent)
    assert canh.xet("open", ("kho/raw/core/a.json", "w", GHI)) == ["raw/core/a.json"]
    assert canh.xet("open", ("kho/raw/../raw/core/a.json", "w", GHI)) == ["raw/core/a.json"]
    monkeypatch.chdir(kho / "raw")
    assert canh.xet("open", ("core/a.json", "w", GHI)) == ["raw/core/a.json"]


def test_doi_ten_xoa_cat_cham_lien_ket(canh, kho, tmp_path):
    trong, ngoai = str(kho / "raw" / "a.json"), str(tmp_path / "ngoai.json")
    assert canh.xet("os.rename", (ngoai, trong, -1, -1)) == ["raw/a.json"]           # dời VÀO kho
    assert canh.xet("os.rename", (trong, ngoai, -1, -1)) == ["raw/a.json"]           # dời RA: kho mất tệp
    assert canh.xet("os.rename", (trong, str(kho / "raw" / "b.json"), -1, -1)) == ["raw/a.json", "raw/b.json"]
    assert canh.xet("os.rename", (ngoai, ngoai + ".2", -1, -1)) == []
    assert canh.xet("os.remove", (trong, -1)) == ["raw/a.json"]
    assert canh.xet("os.truncate", (trong, 0)) == ["raw/a.json"] and canh.xet("os.truncate", (5, 0)) == []
    assert canh.xet("os.utime", (trong, None, None, -1)) == ["raw/a.json"]
    assert canh.xet("os.link", (ngoai, trong, -1, -1)) == ["raw/a.json"]
    assert canh.xet("os.link", (trong, ngoai, -1, -1)) == []                         # liên kết mới nằm NGOÀI kho
    assert canh.xet("os.symlink", (ngoai, trong, -1)) == ["raw/a.json"]
    assert canh.xet("os.symlink", (trong, ngoai, -1)) == []


def test_duong_dan_tuong_doi_theo_dir_fd_khong_quy_duoc_thi_bo_qua(canh, kho, monkeypatch):
    """Bên trong shutil.rmtree xoá bằng `os.unlink(tên, dir_fd=fd)`: tên tương đối theo fd, không theo thư mục hiện
    hành ⇒ không được quy bừa (sự kiện gốc `shutil.rmtree` mới là chỗ bắt)."""
    monkeypatch.chdir(kho / "raw")
    assert canh.xet("os.remove", ("core", 3)) == []
    assert canh.xet("os.remove", ("core", -1)) == ["raw/core"]
    assert canh.xet("os.rename", ("a", str(kho / "raw" / "b"), 3, -1)) == ["raw/b"]
    assert canh.xet("os.utime", ("core", None, None, 3)) == []
    assert canh.xet("shutil.rmtree", ("core", 3)) == []


def test_rmtree_trong_kho_chinh_kho_va_thu_muc_cha(canh, kho, tmp_path):
    assert canh.xet("shutil.rmtree", (kho / "raw" / "core", None)) == ["raw/core"]
    assert canh.xet("shutil.rmtree", (str(kho), None)) == ["."]
    assert canh.xet("shutil.rmtree", (str(kho.parent), None)) == ["."]              # xoá thư mục CHA là xoá cả kho
    assert canh.xet("shutil.rmtree", (str(tmp_path / "cho_khac"), None)) == []
    assert canh.xet("os.remove", (str(kho.parent), -1)) == []                        # chỉ rmtree mới xét thư mục cha
    assert canh.xet("os.rename", (str(kho), str(tmp_path / "doi_di"), -1, -1)) == ["."]   # dời cả kho đi nơi khác


def test_mien_tru_dung_pham_vi(canh, kho):
    assert canh.xet("open", (str(kho / "archive" / "app.log"), "a", GHI)) == []
    assert canh.xet("open", (str(kho / "archive" / "sau" / "hon.log"), "a", GHI)) == []
    assert canh.xet("shutil.rmtree", (str(kho / "archive"), None)) == []
    assert canh.xet("open", (str(kho / "processed" / "lo_da_biet.jsonl"), "a", GHI)) == []
    # KHÔNG miễn: tên chỉ chung tiền tố, tệp khác cùng thư mục, thư mục chứa tệp được miễn
    assert canh.xet("open", (str(kho / "archive_2" / "app.log"), "a", GHI)) == ["archive_2/app.log"]
    assert canh.xet("open", (str(kho / "processed" / "lo_da_biet.jsonl.bak"), "w", GHI)) \
        == ["processed/lo_da_biet.jsonl.bak"]
    assert canh.xet("open", (str(kho / "processed" / "pipeline.json"), "w", GHI)) == ["processed/pipeline.json"]
    assert canh.xet("shutil.rmtree", (str(kho / "processed"), None)) == ["processed"]
    assert canh.duoc_mien("archive") and canh.duoc_mien("archive/a/b") and not canh.duoc_mien("raw")


def test_lien_ket_tuong_trung(canh, kho, tmp_path):
    ngoai = tmp_path / "ngoai"
    ngoai.mkdir()
    try:
        (tmp_path / "loi_tat").symlink_to(kho / "raw", target_is_directory=True)   # ngoài kho → trỏ VÀO kho
        (kho / "raw" / "tro_ra").symlink_to(ngoai, target_is_directory=True)        # trong kho → trỏ RA ngoài
    except OSError:
        pytest.skip("hệ thống không cho tạo symlink (Windows không có quyền)")
    # ghi qua lối tắt là ghi vào kho; ghi qua liên kết trỏ ra ngoài thì kho không đổi
    assert canh.xet("open", (str(tmp_path / "loi_tat" / "a.json"), "w", GHI)) == ["raw/a.json"]
    assert canh.xet("open", (str(kho / "raw" / "tro_ra" / "a.json"), "w", GHI)) == []
    # xoá/đổi tên tác động lên CHÍNH liên kết (một mục của kho), không lên đích của nó
    assert canh.xet("os.remove", (str(kho / "raw" / "tro_ra"), -1)) == ["raw/tro_ra"]
    assert canh.xet("os.rename", (str(kho / "raw" / "tro_ra"), str(ngoai / "x"), -1, -1)) == ["raw/tro_ra"]
    # chốt được DỰNG qua một đường dẫn là symlink vẫn phải nhận ra lần ghi đi bằng đường dẫn thật
    (tmp_path / "kho_qua_lien_ket").symlink_to(kho, target_is_directory=True)
    canh_qua_lien_ket = CanhGhi(tmp_path / "kho_qua_lien_ket")
    assert canh_qua_lien_ket.xet("open", (str(kho / "raw" / "a.json"), "w", GHI)) == ["raw/a.json"]
    assert canh_qua_lien_ket.xet("os.remove", (str(kho / "raw" / "a.json"), -1)) == ["raw/a.json"]


def test_tham_so_khong_phai_duong_dan_thi_bo_qua_khong_nem(canh):
    """Sự kiện audit có thể mang bất cứ thứ gì; `xet()` không được ném (lỗi ở đây là lỗi của chính chốt canh)."""
    for la in (object(), None, 3.5, "co\x00byte_rong", b"co\x00byte_rong", True):
        assert canh.xet("open", (la, "w", GHI)) == [], repr(la)
        assert canh.xet("os.remove", (la, -1)) == [], repr(la)
    assert canh.loi_noi_bo == 0


def test_nhan_khong_bao_gio_nem_va_dem_loi_noi_bo(canh, kho, monkeypatch):
    canh.test_dang_chay = "tep.py::test_a"
    canh.nhan("open", (str(kho / "raw" / "a.json"), "w", GHI))
    canh.nhan("open", (str(kho / "raw" / "a.json"), "r", os.O_RDONLY))
    assert canh.vi_pham == [ViPham("tep.py::test_a", "open", "raw/a.json")] == canh.cho_bao
    assert canh.loi_noi_bo == 0

    def _hong(su_kien, tham_so):
        raise RuntimeError("chốt canh tự hỏng")

    monkeypatch.setattr(canh, "xet", _hong)
    canh.nhan("open", (str(kho / "raw" / "b.json"), "w", GHI))   # không được ném
    assert canh.loi_noi_bo == 1 and len(canh.vi_pham) == 1
    tk = tong_ket([canh], nghiem=False)
    assert any("KHÔNG ĐO ĐƯỢC" in d for d in tk.do), "chốt canh tự hỏng phải là ĐỎ (fail-closed), không phải im lặng"


def test_rut_cua_test_chi_lay_dung_test_do_va_chi_mot_lan(canh, kho):
    for ten, tep in (("t.py::a", "a.json"), ("t.py::b", "b.json"), (NGOAI_TEST, "c.json"), ("t.py::a", "d.json")):
        canh.test_dang_chay = ten
        canh.nhan("open", (str(kho / "raw" / tep), "w", GHI))
    assert [vp.tuong_doi for vp in canh.rut_cua_test("t.py::a")] == ["raw/a.json", "raw/d.json"]
    assert canh.rut_cua_test("t.py::a") == []
    assert [vp.test for vp in canh.cho_bao] == ["t.py::b", NGOAI_TEST]
    assert len(canh.vi_pham) == 4, "sổ đầy đủ không bị rút bớt"


# ════════════════════════════════════════════════════════════════════════════
# (2b) Móc audit thật: thao tác tệp thật trên một thư mục tạm được đăng ký canh
# ════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def canh_dang_ky(canh):
    """Đăng ký rồi GỠ trước khi test kết thúc — chốt tạm không được lọt vào kết luận cuối phiên của pytest."""
    dang_ky(canh)
    try:
        yield canh
    finally:
        huy_dang_ky(canh)


def test_moc_audit_bat_thao_tac_tep_that(canh_dang_ky, kho, tmp_path):
    canh = canh_dang_ky
    a = kho / "raw" / "core" / "a.json"
    a.write_text("{}", encoding="utf-8", newline="\n")                                    # open(w)
    os.close(os.open(kho / "raw" / "b.bin", os.O_CREAT | os.O_WRONLY))      # os.open
    with open(a, "a", encoding="utf-8") as fh:                              # open(a)
        fh.write("\n")
    os.replace(kho / "raw" / "b.bin", kho / "raw" / "c.bin")                # os.rename
    a.touch()                                                               # os.utime
    shutil.copyfile(a, kho / "raw" / "d.json")                              # open(w) đích
    (kho / "raw" / "c.bin").unlink()                                        # os.remove
    shutil.rmtree(kho / "raw" / "core")                                     # shutil.rmtree
    tat_ca = [(vp.su_kien, vp.tuong_doi) for vp in canh.vi_pham]
    # Gộp sự kiện lặp LIỀN NHAU: một thao tác có thể phát hơn một sự kiện tuỳ bản Python (Path.write_text của
    # Python ≤ 3.9 mở qua `opener` ⇒ hai sự kiện `open`) — điều cần khoá là thao tác nào cũng được ghi sổ, đúng thứ tự.
    da_thay = [x for i, x in enumerate(tat_ca) if i == 0 or x != tat_ca[i - 1]]
    assert da_thay[:9] == [
        ("open", "raw/core/a.json"), ("open", "raw/b.bin"), ("open", "raw/core/a.json"),
        ("os.rename", "raw/b.bin"), ("os.rename", "raw/c.bin"), ("os.utime", "raw/core/a.json"),
        ("open", "raw/d.json"), ("os.remove", "raw/c.bin"), ("shutil.rmtree", "raw/core"),
    ], da_thay
    # Nơi rmtree không xoá qua dir_fd (Windows) thì từng tệp bên trong hiện thêm một os.remove đường dẫn đầy đủ.
    assert all(sk == "os.remove" and td.startswith("raw/core/") for sk, td in da_thay[9:]), da_thay
    assert all(vp.test == NGOAI_TEST for vp in canh.vi_pham), "chốt đăng ký giữa chừng chưa được gán test đang chạy"


def test_moc_audit_khong_tinh_doc_tao_thu_muc_mien_tru_va_ngoai_kho(canh_dang_ky, kho, tmp_path):
    canh = canh_dang_ky
    (kho / "raw" / "d.json").write_text("{}", encoding="utf-8", newline="\n")
    so_truoc = len(canh.vi_pham)
    assert (kho / "raw" / "d.json").read_text(encoding="utf-8") == "{}"    # đọc
    assert sorted(p.name for p in (kho / "raw").iterdir()) == ["core", "d.json"]
    (kho / "raw" / "core").mkdir(parents=True, exist_ok=True)               # mkdir trên thư mục đã có
    (kho / "raw" / "moi").mkdir()                                           # tạo thư mục (không phải tệp)
    (kho / "archive" / "app.log").write_text("nhật ký", encoding="utf-8", newline="\n")   # miễn trừ theo thư mục
    (kho / "processed" / "lo_da_biet.jsonl").write_text("{}", encoding="utf-8", newline="\n")  # miễn trừ theo tệp
    (tmp_path / "ngoai.json").write_text("{}", encoding="utf-8", newline="\n")            # ngoài kho
    assert canh.vi_pham[so_truoc:] == []


def test_dang_ky_hai_lan_khong_ghi_doi_va_huy_dang_ky_thi_thoi_canh(canh, kho):
    dang_ky(canh)
    dang_ky(canh)
    try:
        assert sum(c is canh for c in cac_canh()) == 1
        with open(kho / "raw" / "mot_lan.json", "w", encoding="utf-8") as fh:
            fh.write("{}")
        assert [vp.tuong_doi for vp in canh.vi_pham] == ["raw/mot_lan.json"], "đăng ký hai lần không được ghi sổ đôi"
    finally:
        huy_dang_ky(canh)
    assert not any(c is canh for c in cac_canh())
    (kho / "raw" / "sau_khi_go.json").write_text("{}", encoding="utf-8", newline="\n")
    assert [vp.tuong_doi for vp in canh.vi_pham] == ["raw/mot_lan.json"]


def test_moc_audit_khong_nem_ke_ca_khi_trang_thai_module_hong(monkeypatch):
    """Móc audit gắn cho CẢ tiến trình và không gỡ được: lỗi thoát ra từ nó sẽ thành lỗi của mọi lời gọi open()."""
    import tests.canh_ghi_du_lieu_that as M

    monkeypatch.setattr(M, "_SU_KIEN", None)   # giả lập biến module bị dọn lúc trình thông dịch tắt
    M._moc_audit("open", ("bat_ky.json", "w", GHI))
    M._moc_audit("os.remove", ("bat_ky.json", -1))


def test_hook_logstart_logfinish_gan_nhan_test_cho_moi_chot(canh_dang_ky, request):
    canh = canh_dang_ky
    try:
        C.pytest_runtest_logstart("tep_gia.py::test_gia", None)
        assert canh.test_dang_chay == "tep_gia.py::test_gia" == C._CANH_DU_LIEU_THAT.test_dang_chay
        C.pytest_runtest_logfinish("tep_gia.py::test_gia", None)
        assert canh.test_dang_chay == NGOAI_TEST == C._CANH_DU_LIEU_THAT.test_dang_chay
    finally:
        C.pytest_runtest_logstart(request.node.nodeid, None)   # trả nhãn của chính test này cho chốt thật


# ════════════════════════════════════════════════════════════════════════════
# (2c) So danh sách tệp đầu↔cuối phiên + kết luận cuối phiên
# ════════════════════════════════════════════════════════════════════════════

def test_chup_va_so_sanh(canh, kho):
    (kho / "raw" / "giu.json").write_text("1", encoding="utf-8", newline="\n")
    (kho / "raw" / "sua.json").write_text("1", encoding="utf-8", newline="\n")
    (kho / "raw" / "xoa.json").write_text("1", encoding="utf-8", newline="\n")
    (kho / "archive" / "app.log").write_text("1", encoding="utf-8", newline="\n")
    truoc, du = chup(kho, canh)
    assert du and sorted(truoc) == ["raw/giu.json", "raw/sua.json", "raw/xoa.json"], truoc

    (kho / "raw" / "sua.json").write_text("dài hơn", encoding="utf-8", newline="\n")
    (kho / "raw" / "xoa.json").unlink()
    (kho / "raw" / "core" / "moi.json").write_text("1", encoding="utf-8", newline="\n")
    (kho / "archive" / "app.log").write_text("nhật ký dài thêm", encoding="utf-8", newline="\n")  # miễn trừ thư mục
    (kho / "processed" / "lo_da_biet.jsonl").write_text("1", encoding="utf-8", newline="\n")      # miễn trừ tệp
    for ten_he_thong in (".DS_Store", "Thumbs.db", "desktop.ini"):                                # tệp hệ điều hành
        (kho / "raw" / ten_he_thong).write_text("1", encoding="utf-8", newline="\n")
    sau, du = chup(kho, canh)
    assert du
    assert so_sanh(truoc, sau) == {"moi": ["raw/core/moi.json"], "doi": ["raw/sua.json"], "mat": ["raw/xoa.json"]}
    assert so_sanh(sau, sau) == {"moi": [], "doi": [], "mat": []}
    # không truyền chốt ⇒ không miễn trừ gì (chỉ bỏ tệp hệ điều hành)
    khong_mien = chup(kho)[0]
    assert "archive/app.log" in khong_mien and "processed/lo_da_biet.jsonl" in khong_mien
    assert not [p for p in khong_mien if p.rsplit("/", 1)[-1] in (".DS_Store", "Thumbs.db", "desktop.ini")]


def test_chup_qua_han_thi_bao_khong_du(canh, kho):
    (kho / "raw" / "a.json").write_text("1", encoding="utf-8", newline="\n")
    anh, du = chup(kho, canh, han_giay=-1.0)
    assert du is False and anh == {}, "quá hạn phải báo KHÔNG ĐỦ, không được trả ảnh thiếu như thể đã quét xong"


def test_tong_ket_sach_thi_khong_co_dong_nao(canh):
    canh.chup_dau()
    for nghiem in (False, True):
        tk = tong_ket([canh], nghiem=nghiem)
        assert tk.do == [] and tk.ghi_chu == []


def test_tong_ket_ghi_trong_tien_trinh_chua_test_nao_nhan_thi_do(canh, kho):
    canh.chup_dau()
    canh.nhan("open", (str(kho / "raw" / "luc_import.json"), "w", GHI))
    (kho / "raw" / "luc_import.json").write_text("{}", encoding="utf-8", newline="\n")
    for nghiem in (False, True):
        tk = tong_ket([canh], nghiem=nghiem)
        assert any("raw/luc_import.json" in d and NGOAI_TEST in d for d in tk.do), tk
        # tệp đó móc audit ĐÃ thấy ⇒ không báo lần hai ở phần «không quy được»
        assert tk.ghi_chu == [] and sum("raw/luc_import.json" in d for d in tk.do) == 1, tk


def test_tong_ket_tep_doi_khong_quy_duoc_chi_do_o_phien_kin(canh, kho):
    (kho / "raw" / "cu.json").write_text("1", encoding="utf-8", newline="\n")
    (kho / "raw" / "se_mat.json").write_text("1", encoding="utf-8", newline="\n")
    canh.chup_dau()
    # tiến trình KHÁC ghi (móc audit của chốt này không thấy vì chưa đăng ký): mới + đổi + mất
    (kho / "raw" / "core" / "cua_tien_trinh_khac.json").write_text("{}", encoding="utf-8", newline="\n")
    (kho / "raw" / "cu.json").write_text("đã đổi", encoding="utf-8", newline="\n")
    (kho / "raw" / "se_mat.json").unlink()
    (kho / "archive" / "app.log").write_text("miễn trừ", encoding="utf-8", newline="\n")

    long = tong_ket([canh], nghiem=False)
    assert long.do == [], "không biết ai ghi ⇒ KHÔNG được báo đỏ ở phiên thường"
    van_ban = "\n".join(long.ghi_chu)
    assert "3 tệp mới/đổi/mất" in van_ban and "MRAQ_OFFLINE_CI=1" in van_ban
    for dong in ("mới: raw/core/cua_tien_trinh_khac.json", "đổi: raw/cu.json", "mất: raw/se_mat.json"):
        assert dong in van_ban, van_ban
    assert "app.log" not in van_ban

    kin = tong_ket([canh], nghiem=True)
    assert kin.ghi_chu == [] and "raw/core/cua_tien_trinh_khac.json" in "\n".join(kin.do)


def test_tong_ket_khong_quet_duoc_thi_noi_khong_do_duoc(canh, kho, monkeypatch):
    import tests.canh_ghi_du_lieu_that as M

    canh.chup_dau()
    (kho / "raw" / "moi.json").write_text("{}", encoding="utf-8", newline="\n")
    monkeypatch.setattr(M, "chup", lambda goc, canh=None, han_giay=20.0: ({}, False))
    long = tong_ket([canh], nghiem=False)
    assert long.do == [] and any("KHÔNG so được" in d for d in long.ghi_chu), long
    assert not any("moi.json" in d for d in long.ghi_chu), "ảnh thiếu thì không được suy ra danh sách tệp"
    kin = tong_ket([canh], nghiem=True)
    assert any("KHÔNG so được" in d for d in kin.do) and kin.ghi_chu == []


def test_tong_ket_liet_ke_co_tran_va_noi_ro_phan_con_lai(canh, kho):
    canh.chup_dau()
    for i in range(7):
        (kho / "raw" / f"t{i}.json").write_text("{}", encoding="utf-8", newline="\n")
        canh.nhan("open", (str(kho / "raw" / f"n{i}.json"), "w", GHI))
    tk = tong_ket([canh], nghiem=True, toi_da=3)
    van_ban = "\n".join(tk.do)
    assert "… và 4 lần nữa" in van_ban and "… và 4 tệp nữa" in van_ban, van_ban


# ════════════════════════════════════════════════════════════════════════════
# (3) Canary đầu–cuối: phiên pytest CON, conftest thật, thư mục được canh là thư mục tạm
# ════════════════════════════════════════════════════════════════════════════

_DAU_TEP_CON = '''
from pathlib import Path
from tests.canh_ghi_du_lieu_that import CanhGhi, dang_ky

KHO = Path(__file__).resolve().parent / "kho_duoc_canh"
(KHO / "raw").mkdir(parents=True)
dang_ky(CanhGhi(KHO))
'''


def _chay_pytest_con(tmp_path, than_tep: str, kin: bool = False, them=()) -> subprocess.CompletedProcess:
    """Chạy một phiên pytest con trên MỘT tệp test tạm, nạp tests/conftest.py thật làm plugin."""
    tep = tmp_path / "test_con.py"
    tep.write_text(_DAU_TEP_CON + than_tep, encoding="utf-8", newline="\n")
    env = {k: v for k, v in os.environ.items() if k != "MRAQ_OFFLINE_CI"}
    env.update(PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    if kin:
        env.update(MRAQ_OFFLINE_CI="1", ANTHROPIC_API_KEY="", OPENAI_API_KEY="")
    return subprocess.run(
        [sys.executable, "-B", "-m", "pytest", "-p", "tests.conftest", "-p", "no:cacheprovider", "-q",
         "--basetemp", str(tmp_path / "bt"), *them, str(tep)],
        cwd=REPO_ROOT, env=env, capture_output=True, text=True, timeout=300,
    )


def _dong_thong_ke(kq: subprocess.CompletedProcess) -> str:
    """Dòng thống kê cuối của pytest («2 passed, 1 error in 0.5s») — chỉ lấy ở stdout (stderr có nhật ký của app)."""
    cac_dong = [d for d in kq.stdout.splitlines() if re.search(r"\b\d+ (passed|failed|error)", d) and " in " in d]
    assert cac_dong, f"không thấy dòng thống kê của pytest:\n{kq.stdout}\n{kq.stderr}"
    return cac_dong[-1]


def test_canary_test_ghi_vao_thu_muc_duoc_canh_thi_chinh_test_do_do(tmp_path):
    kq = _chay_pytest_con(tmp_path, '''
import pytest


def test_ghi_vao_kho():
    (KHO / "raw" / "gia.json").write_text("{}", encoding="utf-8")


def test_sach():
    assert (KHO / "raw").is_dir()


@pytest.fixture
def teardown_hong():
    yield
    raise RuntimeError("teardown của fixture hỏng vì lý do khác")


def test_ghi_vao_kho_ma_teardown_da_do_san(teardown_hong):
    (KHO / "raw" / "gia_2.json").write_text("{}", encoding="utf-8")
''')
    ra = kq.stdout + kq.stderr
    assert kq.returncode == 1, ra
    assert "CHỐT CANH DỮ LIỆU THẬT" in ra and "open: raw/gia.json" in ra, ra
    thong_ke = _dong_thong_ke(kq)
    assert re.search(r"\b3 passed\b", thong_ke) and re.search(r"\b2 errors\b", thong_ke) and "failed" not in thong_ke, \
        f"đúng HAI test ghi phải lỗi ở teardown, test sạch không bị vạ lây: {thong_ke}\n{ra}"
    # Phần đường dẫn của nodeid KHÔNG cố định: pytest con chạy một tệp nằm NGOÀI rootdir; trên runner Windows tệp tạm ở
    # ổ C: còn repo ở ổ D: nên pytest in «ERROR ::test_ghi_vao_kho …» (phần tệp RỖNG), trên Linux/cùng ổ thì in
    # «ERROR ../../tmp/…/test_con.py::test_ghi_vao_kho …». Chỉ khẳng định phần tên test, `\S*` nhận cả hai dạng.
    assert re.search(r"^ERROR \S*::test_ghi_vao_kho(?:\s|$)", kq.stdout, re.M), ra
    assert not re.search(r"^(?:ERROR|FAILED) \S*::test_sach(?:\s|$)", kq.stdout, re.M), ra
    # teardown đã đỏ sẵn vì lý do khác: giữ nguyên lỗi đó, và VẪN nói rõ test đã ghi vào thư mục được canh
    assert "teardown của fixture hỏng vì lý do khác" in ra and "open: raw/gia_2.json" in ra, ra


_THAN_GHI_LUC_IMPORT = '''
(KHO / "raw" / "luc_import.json").write_text("{}", encoding="utf-8")


def test_sach():
    assert True
'''


def test_canary_ghi_luc_import_khong_thuoc_test_nao_van_lam_phien_do(tmp_path):
    kq = _chay_pytest_con(tmp_path, _THAN_GHI_LUC_IMPORT)
    ra = kq.stdout + kq.stderr
    assert kq.returncode == 1, f"không test nào đỏ nhưng phiên vẫn phải thoát khác 0:\n{ra}"
    thong_ke = _dong_thong_ke(kq)
    assert re.search(r"\b1 passed\b", thong_ke) and "error" not in thong_ke and "failed" not in thong_ke, thong_ke
    assert "chốt canh thư mục dữ liệu thật" in kq.stdout and "open: raw/luc_import.json" in kq.stdout, ra


def test_canary_no_summary_van_noi_vi_sao_do(tmp_path):
    """`--no-summary` tắt mục tổng kết của pytest — mã thoát khác 0 mà không một dòng giải thích là đỏ «câm»."""
    kq = _chay_pytest_con(tmp_path, _THAN_GHI_LUC_IMPORT, them=("--no-summary",))
    assert kq.returncode == 1, kq.stdout + kq.stderr
    assert "open: raw/luc_import.json" not in kq.stdout, "tiền đề của test: --no-summary phải tắt mục tổng kết"
    assert "CHỐT CANH THƯ MỤC DỮ LIỆU THẬT — LỖI" in kq.stderr and "open: raw/luc_import.json" in kq.stderr, kq.stderr


_THAN_TIEN_TRINH_CON = '''
import subprocess
import sys


def test_tien_trinh_con_ghi():
    subprocess.run([sys.executable, "-c", "import pathlib, sys; pathlib.Path(sys.argv[1]).write_text('x')",
                    str(KHO / "raw" / "cua_tien_trinh_con.json")], check=True)
'''


def test_canary_tien_trinh_con_ghi_phien_thuong_chi_ghi_chu(tmp_path):
    kq = _chay_pytest_con(tmp_path, _THAN_TIEN_TRINH_CON, kin=False)
    ra = kq.stdout + kq.stderr
    assert kq.returncode == 0, f"không biết ai ghi ⇒ phiên thường KHÔNG được đỏ:\n{ra}"
    assert "mới: raw/cua_tien_trinh_con.json" in ra and "KHÔNG mở để ghi" in ra, ra


def test_canary_tien_trinh_con_ghi_phien_kin_thi_do(tmp_path):
    kq = _chay_pytest_con(tmp_path, _THAN_TIEN_TRINH_CON, kin=True)
    ra = kq.stdout + kq.stderr
    assert kq.returncode == 1, f"phiên kín (CI) không có tiến trình nào khác ⇒ tệp lạ là LỖI:\n{ra}"
    thong_ke = _dong_thong_ke(kq)
    assert re.search(r"\b1 passed\b", thong_ke) and "error" not in thong_ke and "failed" not in thong_ke, thong_ke
    assert "mới: raw/cua_tien_trinh_con.json" in ra, ra
