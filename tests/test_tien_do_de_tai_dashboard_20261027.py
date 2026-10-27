"""Tiến độ đề tài trong Dashboard EBM (tab «6. Research») — 27/10/2026.

Bác sĩ giao: tích hợp bảng tiến độ đề tài vào ứng dụng «Dashboard EBM». Mô-đun chỉ ĐỌC sổ
`exports/<mã>/tien_do/TIEN_DO_<mã>.json`; ngoại tuyến hoàn toàn, sổ giả trong thư mục tạm, `st` giả.
"""
from __future__ import annotations

import json
import re
from contextlib import contextmanager
from pathlib import Path

from app.dashboard import tien_do_de_tai as TD

ROOT = Path(__file__).resolve().parents[1]


def _so(**ghi_de) -> dict:
    so = {
        "schema": "de_tai/so_tien_do/v1",
        "study": "de-tai-gia",
        "ten_de_tai": "Đề tài giả",
        "tap_chi_dich": "Tạp chí giả",
        "cap_nhat": "2026-10-27",
        "ai": {"may": "Máy", "bs": "Bác sĩ"},
        "giai_doan": [{"id": "GĐ1", "ten": "Một", "tu": "01/11/2026", "den": "05/11/2026"},
                      {"id": "GĐ2", "ten": "Hai", "tu": "06/11/2026", "den": "10/11/2026"}],
        "viec": [
            {"id": "1.1", "gd": "GĐ1", "ten": "Đã xong", "ai": "may", "han": "01/11/2026", "trang_thai": "xong",
             "phu_thuoc": [], "do_song": ""},
            {"id": "1.2", "gd": "GĐ1", "ten": "Chờ bác sĩ", "ai": "bs", "han": "02/11/2026", "trang_thai": "cho_bs",
             "phu_thuoc": [], "do_song": ""},
            {"id": "1.3", "gd": "GĐ1", "ten": "Làm được", "ai": "may", "han": "03/11/2026", "trang_thai": "chua",
             "phu_thuoc": ["1.1"], "do_song": ""},
            {"id": "2.1", "gd": "GĐ2", "ten": "Bị chặn", "ai": "bs", "han": "07/11/2026", "trang_thai": "chua",
             "phu_thuoc": ["1.2"], "do_song": "approval_ledger G2"},
            {"id": "2.2", "gd": "GĐ2", "ten": "Đã ký", "ai": "bs", "han": "08/11/2026", "trang_thai": "xong",
             "phu_thuoc": [], "do_song": "approval_ledger G4"},
        ],
    }
    so.update(ghi_de)
    return so


def _ghi(goc: Path, ma: str, noi_dung) -> None:
    thu_muc = goc / ma / "tien_do"
    thu_muc.mkdir(parents=True)
    (thu_muc / f"TIEN_DO_{ma}.json").write_text(
        noi_dung if isinstance(noi_dung, str) else json.dumps(noi_dung, ensure_ascii=False), encoding="utf-8",
        newline="\n")


class _Cot:
    def __init__(self, ghi):
        self._ghi = ghi

    def metric(self, nhan, gia_tri, *a, **k):
        self._ghi.append(("metric", nhan, gia_tri))


class _StGia:
    """Streamlit giả: ghi lại lệnh vẽ; selectbox trả lựa chọn đầu tiên; nút không bấm."""

    def __init__(self):
        self.ghi = []

    def __getattr__(self, ten):
        def _f(*a, **k):
            self.ghi.append((ten,) + a)
        return _f

    def columns(self, n):
        return [_Cot(self.ghi) for _ in range(n)]

    def selectbox(self, nhan, lua_chon, **k):
        self.ghi.append(("selectbox", nhan, list(lua_chon)))
        return lua_chon[0]

    def button(self, *a, **k):
        self.ghi.append(("button",) + a)
        return False

    @contextmanager
    def expander(self, nhan, expanded=False):
        self.ghi.append(("expander", nhan, expanded))
        yield


def test_doc_so_tach_trang_thai_va_dem_cong_cung(tmp_path):
    _ghi(tmp_path, "de-tai-gia", _so())
    [p], canh_bao = TD.doc_so_tien_do(tmp_path)
    assert canh_bao == []
    assert {v["id"]: v["tt"] for v in p["viec"]} == {"1.1": "xong", "1.2": "cho_bs", "1.3": "san", "2.1": "khoa",
                                                     "2.2": "xong"}
    assert (p["tong"], p["xong"], p["cong_ky"], p["cong_tong"], p["gd_hien"]) == (5, 2, 1, 2, 0)
    assert [(g["xong"], g["tong"]) for g in p["giai_doan"]] == [(1, 3), (1, 2)]
    assert p["viec"][1]["ai_nhan"] == "Bác sĩ"


def test_so_hong_hoac_sai_khuon_bi_bo_kem_canh_bao(tmp_path):
    _ghi(tmp_path, "a-hong-json", "{không phải json")
    _ghi(tmp_path, "b-sai-schema", _so(schema="khac/v9"))
    sai_tt = _so()
    sai_tt["viec"][0]["trang_thai"] = "gan_xong"
    _ghi(tmp_path, "c-sai-trang-thai", sai_tt)
    sai_pt = _so()
    sai_pt["viec"][2]["phu_thuoc"] = ["9.9"]
    _ghi(tmp_path, "d-phu-thuoc-ma", sai_pt)
    _ghi(tmp_path, "e-tot", _so(study="e-tot"))
    de_tai, canh_bao = TD.doc_so_tien_do(tmp_path)
    assert [p["ma"] for p in de_tai] == ["e-tot"]
    assert len(canh_bao) == 4


def test_cau_tiep_tuc_cung_khuon_voi_antifacts():
    assert TD.cau_tiep_tuc("de-tai-gia", {"id": "1.7", "ten": "Xác nhận G0"}) == \
        "Tiếp tục mục 1.7 «Xác nhận G0» của đề tài de-tai-gia"


def test_ve_muc_tien_do_co_viec_lam_ngay_va_cau_chep(tmp_path):
    _ghi(tmp_path, "de-tai-gia", _so())
    st = _StGia()
    TD.render_tien_do_de_tai(st, tmp_path, None)
    ten = [g[0] for g in st.ghi]
    assert ("metric", "Hoàn thành", "40%") in st.ghi
    assert ("metric", "Cổng cứng đã ký", "1/2") in st.ghi
    [chon] = [g for g in st.ghi if g[0] == "selectbox"]
    # Chỉ việc CHƯA xong được chọn để làm tiếp.
    assert [x.split(" · ")[0] for x in chon[2]] == ["1.2", "1.3", "2.1"]
    assert ("code", "Tiếp tục mục 1.2 «Chờ bác sĩ» của đề tài de-tai-gia") in st.ghi
    assert ten.count("expander") == 2
    # Không có Antifacts thì không hiện nút mở.
    assert "button" not in ten


def test_khong_co_so_thi_bao_chua_co(tmp_path):
    st = _StGia()
    TD.render_tien_do_de_tai(st, tmp_path / "khong-co", tmp_path / "khong-co-antifacts.html")
    assert any(g[0] == "info" for g in st.ghi)


def test_tab_research_goi_muc_tien_do_tren_dong_thi_hanh():
    dong = [d.strip() for d in (ROOT / "app" / "dashboard" / "main.py").read_text(encoding="utf-8").splitlines()]
    thi_hanh = [d for d in dong if d and not d.startswith("#")]
    assert any(re.fullmatch(r'render_tien_do_de_tai\(st, ROOT / "exports", ROOT\.parent / "Antifacts\.html"\)', d)
               for d in thi_hanh)
