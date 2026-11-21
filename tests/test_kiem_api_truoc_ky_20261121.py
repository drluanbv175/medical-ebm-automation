"""Một lệnh kiểm API trước khi ký/nộp + hiệu chỉnh ước tính token tiếng Việt (21/11/2026).

(1) `kiem_api_truoc_ky`: dùng lại báo cáo còn hiệu lực (mã băm khớp), chỉ chạy lại phần thiếu/cũ, chặn trước khi vượt
trần, gom phát hiện + hội đồng + mục chưa duyệt thành một phiếu. (2) Đo thật C1a: 1,67–1,69 ký tự/token (ước cũ 3 ⇒
báo giá hội đồng 0,47 USD trong khi bước đầu tốn 0,69). Ngoại tuyến — công cụ con được thay bằng hàm giả.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
for _d in (REPO, REPO / "tools"):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

import api_claude_nc as API  # noqa: E402
import hoi_dong_cong as HDC  # noqa: E402
import hoi_dong_cong_batch as HB  # noqa: E402
import kiem_api_truoc_ky as K  # noqa: E402
import kiem_noi_dung_trich_dan as KND  # noqa: E402
import phan_bien_may_de_cuong as PBM  # noqa: E402

S = "S1"
VAN = "# ĐỀ CƯƠNG\n## DANH MỤC CHỮ VIẾT TẮT\n| OSF | Open Science Framework |\n# 4. PHƯƠNG PHÁP\nCỡ mẫu 420 [1].\n"


def _goc(tmp_path: Path) -> Path:
    d = tmp_path / "exports" / S
    (d / "kiem_may_api").mkdir(parents=True)
    (d / f"DE_CUONG_NOP_HOI_DONG_{S}.md").write_text(VAN, encoding="utf-8", newline="\n")
    return tmp_path


def _sha(goc: Path) -> str:
    return hashlib.sha256((goc / "exports" / S / f"DE_CUONG_NOP_HOI_DONG_{S}.md").read_bytes()).hexdigest()


def _bc_pb(goc: Path, cu: bool = False, phat_hien=()) -> None:
    bc = {"schema": "x", "study": S, "tep": f"DE_CUONG_NOP_HOI_DONG_{S}.md",
          "tep_sha256": "0" * 64 if cu else _sha(goc),
          "luc": "2026-11-21T08:00:00", "model": "claude-sonnet-5-5", "phat_hien": list(phat_hien),
          "khong_xac_minh": [], "tham_tra": {"model": "claude-opus-5-5", "loi": None, "so_loai": 2},
          "loai_sau_tham_tra": [{}, {}], "trich_dan_tat_dinh": []}
    p = goc / "exports" / S / "kiem_may_api" / f"PHAN_BIEN_MAY_{S}.json"
    p.write_text(json.dumps(bc), encoding="utf-8", newline="\n")


def _bc_a12(goc: Path, cu: bool = False, ket_qua=None) -> None:
    kq = ket_qua if ket_qua is not None else [{"id": "C001", "so": 1, "muc": "ho_tro", "co": []}]
    bc = {"schema": "x", "study": S, "tep": f"DE_CUONG_NOP_HOI_DONG_{S}.md",
          "tep_sha256": "0" * 64 if cu else _sha(goc),
          "luc": "2026-11-21T08:00:00", "model": "claude-sonnet-5-5", "ket_qua": kq, "loi": []}
    p = goc / "exports" / S / "kiem_may_api" / f"A12_KIEM_NOI_DUNG_{S}.json"
    p.write_text(json.dumps(bc), encoding="utf-8", newline="\n")


class Gia:
    """Thay `main` của một công cụ con: chạy khô in JSON ước; `--goi-api` ghi báo cáo mới (mã băm khớp)."""

    def __init__(self, uoc, viet=None, ma_kho=0):
        self.uoc, self.viet, self.ma_kho, self.goi = uoc, viet, ma_kho, []

    def __call__(self, argv, client=None, goc=None, **kw):
        self.goi.append(list(argv))
        if "--goi-api" in argv:
            self.viet(goc)
            return 0
        if self.ma_kho:
            print("❌ lỗi chạy khô")
            return self.ma_kho
        print(json.dumps(self.uoc))
        return 0


@pytest.fixture
def gia(monkeypatch):
    pb = Gia({"uoc_usd": 0.2, "uoc_usd_tham_tra": 0.1, "uoc_tinh": "≈ 0.20 USD"}, viet=lambda g: _bc_pb(g))
    a12 = Gia({"uoc_usd": 0.3, "uoc_tinh": "≈ 0.30 USD"}, viet=lambda g: _bc_a12(g))
    monkeypatch.setattr(PBM, "main", pb)
    monkeypatch.setattr(KND, "main", a12)
    monkeypatch.setattr(HDC, "tom_tat_cong", lambda gate, out_dir, repo_root=None: {
        "trang_thai": "ĐỒNG THUẬN", "ly_do": [], "so_bien_ban_hieu_luc": 4, "cu": []})
    return pb, a12


def _phieu(goc: Path) -> Path:
    return goc / "exports" / S / "kiem_may_api" / f"PHIEU_KIEM_API_TRUOC_KY_{S}.md"


def test_chay_kho_chi_uoc_phan_thieu_khong_goi_khong_ghi(tmp_path, gia, capsys):
    goc = _goc(tmp_path)
    assert K.main(["--study", S, "--json"], goc=goc) == 1
    out = json.loads(capsys.readouterr().out.split("\n", 1)[1])
    assert out["uoc"]["tong_uoc_usd"] == pytest.approx(0.6)  # 0,2 + 0,1 thẩm tra + 0,3
    assert all("--goi-api" not in a for g in gia for a in g.goi)
    assert not _phieu(goc).exists()


def test_bao_cao_con_hieu_luc_thi_khong_tra_tien_lan_hai(tmp_path, gia):
    goc = _goc(tmp_path)
    _bc_pb(goc)
    _bc_a12(goc)
    assert K.main(["--study", S, "--goi-api"], goc=goc) == 0
    assert all(not g.goi for g in gia)  # không cả chạy khô: không phần nào cần chạy
    md = _phieu(goc).read_text(encoding="utf-8")
    assert "Không còn việc kiểm máy" in md and "Cần bác sĩ kiểm chứng" in md
    assert json.loads(_phieu(goc).with_suffix(".json").read_text(encoding="utf-8"))["viec"] == []


def test_bao_cao_cu_chi_chay_lai_dung_phan_cu(tmp_path, gia):
    goc = _goc(tmp_path)
    _bc_pb(goc, cu=True)
    _bc_a12(goc)
    pb, a12 = gia
    assert K.main(["--study", S, "--goi-api"], goc=goc) == 0
    assert ["--study", S, "--goi-api"] in pb.goi and not a12.goi
    p = json.loads(_phieu(goc).with_suffix(".json").read_text(encoding="utf-8"))
    assert p["phan"]["PHAN_BIEN"]["cu"] is False and p["phan"]["PHAN_BIEN"]["chay_luot_nay"].startswith("mã 0")


def test_vuot_tran_thi_khong_chay_phan_nao(tmp_path, gia, monkeypatch):
    goc = _goc(tmp_path)
    monkeypatch.setenv("EBM_API_CLAUDE_TRAN_USD_THANG", "0.5")  # ước 0,6 > trần 0,5
    assert K.main(["--study", S, "--goi-api"], goc=goc) == 2
    assert all("--goi-api" not in a for g in gia for a in g.goi)


def test_khong_uoc_duoc_thi_khong_goi(tmp_path, gia, monkeypatch, capsys):
    goc = _goc(tmp_path)
    gia[1].ma_kho = 2
    assert K.main(["--study", S, "--goi-api"], goc=goc) == 2
    assert "Không ước được chi phí" in capsys.readouterr().out  # chặn ở lớp 1, không trông vào kiem_ngan_sach
    assert all("--goi-api" not in a for g in gia for a in g.goi)


def test_phat_hien_cao_vua_va_cap_can_xem_thanh_viec(tmp_path, gia):
    goc = _goc(tmp_path)
    _bc_pb(goc, phat_hien=[{"loai": "mau_thuan_so", "muc": "cao", "dong": 5, "trich": "Cỡ mẫu 420",
                            "van_de": "lệch N", "goi_y": "x"},
                           {"loai": "trinh_bay", "muc": "thap", "dong": 4, "trich": "PHƯƠNG PHÁP", "van_de": "y",
                            "goi_y": "z"}])
    _bc_a12(goc, ket_qua=[{"id": "C001", "so": 1, "muc": "khong_ho_tro", "co": []},
                          {"id": "C002", "so": 1, "muc": "ho_tro", "co": ["so_khong_thay:420"]}])
    assert K.main(["--study", S, "--goi-api"], goc=goc) == 1
    p = json.loads(_phieu(goc).with_suffix(".json").read_text(encoding="utf-8"))
    viec = " ".join(p["viec"])
    assert "1 phát hiện mức cao/vừa" in viec and "2 cặp" in viec
    md = _phieu(goc).read_text(encoding="utf-8")
    assert "lệch N" in md and "| C001 | [1] | khong_ho_tro |" in md


def test_hoi_dong_chua_dong_thuan_la_viec_kem_lenh(tmp_path, gia, monkeypatch):
    goc = _goc(tmp_path)
    _bc_pb(goc)
    _bc_a12(goc)
    monkeypatch.setattr(HDC, "tom_tat_cong", lambda gate, out_dir, repo_root=None: {
        "trang_thai": "CŨ", "ly_do": ["x"], "so_bien_ban_hieu_luc": 0, "cu": ["DG-1"]})
    assert K.main(["--study", S, "--gate", "G10", "--goi-api"], goc=goc) == 1
    p = json.loads(_phieu(goc).with_suffix(".json").read_text(encoding="utf-8"))
    assert any("hội đồng G10: CŨ" in v and "hoi_dong_cong_batch.py uoc-tinh" in v for v in p["viec"])


def test_ho_so_hoi_dong_loi_la_khong_do_duoc_khong_phai_dat(tmp_path, gia, monkeypatch):
    goc = _goc(tmp_path)
    _bc_pb(goc)
    _bc_a12(goc)

    def hong(*a, **k):
        raise ValueError("biên bản hỏng")

    monkeypatch.setattr(HDC, "tom_tat_cong", hong)
    assert K.main(["--study", S, "--goi-api"], goc=goc) == 1
    p = json.loads(_phieu(goc).with_suffix(".json").read_text(encoding="utf-8"))
    assert p["hoi_dong"]["trang_thai"] == "KHÔNG ĐO ĐƯỢC"


# ── Hiệu chỉnh ước tính (đo thật C1a 21/11/2026) ─────────────────────────────────────────────────────────────────
def test_uoc_token_theo_so_do_tieng_viet():
    assert API.uoc_token("ă" * 1600) == 1000  # 1,6 ký tự/token
    # phản biện C1a: 151.216 ký tự ⇒ thật 89.468 token; ước phải ≥ thật (phép chặn trần nghiêng về an toàn)
    assert API.uoc_token("x" * 151216) >= 89468


def test_hoi_dong_uoc_ra_theo_so_do():
    assert HB.TOKEN_RA_UOC_MOI_YEU_CAU >= 4085  # đo: 28.594 token ra / 7 yêu cầu


def test_chay_kho_hai_cong_cu_tra_usd_dang_so(tmp_path, capsys):
    goc = _goc(tmp_path)
    assert PBM.main(["--study", S, "--json"], goc=goc) == 0
    dl = json.loads(capsys.readouterr().out)
    assert isinstance(dl["uoc_usd"], float) and isinstance(dl["uoc_usd_tham_tra"], float)
    assert dl["model_tham_tra"] == PBM.MODEL_THAM_TRA_MAC_DINH
    assert KND.main(["--study", S, "--json"], goc=goc) == 0
    assert isinstance(json.loads(capsys.readouterr().out)["uoc_usd"], float)
