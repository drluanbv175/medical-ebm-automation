"""`kiem_trich_dan_toan_van` — bật prompt caching ở CẢ HAI đường gọi (21/11/2026).

VÌ SAO. Đo trên SỔ CHI PHÍ THẬT của bác sĩ: công cụ này 88 lượt · **726 N token vào · 0% đọc cache** — nguồn tốn
thứ hai của hệ, và thiếu đúng một cờ. `HE_THONG` = 816 token (trên ngưỡng 512 của Sonnet/Opus 5.5) và được gửi
Y NGUYÊN cho MỖI tài liệu ⇒ hoà vốn ngay từ tài liệu thứ hai (xem docs/BO-NHO-DEM-API.md §1).

HAI VIỆC PHẢI ĐI CÙNG NHAU — và đây là điều các test dưới canh:
1. Bật `cache_he_thong=True` ở CẢ đường gọi trực tiếp (`kiem_tai_lieu`) LẪN đường Batch (`tham_so_tai_lieu`).
   Thiếu một bên thì nửa số lượt vẫn trả giá nguyên.
2. ĐẾM token cache và tính tiền theo chúng. `uoc_chi_phi` tính phí GHI cache riêng (1,25× giá vào), nên bật cache
   mà vẫn chỉ đếm vao/ra thì báo cáo GHI THIẾU tiền — sai theo hướng nguy hiểm (trần chi tiêu tháng canh sai).

Không gọi mạng, không đọc khoá thật.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
for _d in (REPO, REPO / "tools"):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

import api_claude_nc as API  # noqa: E402
import kiem_trich_dan_toan_van as K  # noqa: E402

CAP = [{"id": "C001", "cau": "Câu thử", "muc": "ho_tro_mot_phan", "ly_do": ""}]


def test_he_thong_vuot_nguong_cache():
    """Bật cache chỉ có nghĩa khi prompt vượt ngưỡng — dưới ngưỡng thì API LẶNG LẼ không cache, không báo lỗi."""
    n = API.uoc_token(K.HE_THONG)
    nguong = API.NGUONG_CACHE_TOKEN["claude-sonnet-5-5"]
    assert n >= nguong, f"HE_THONG chỉ {n} token, dưới ngưỡng {nguong}"


def test_duong_batch_danh_dau_cache():
    """`tham_so_tai_lieu` dựng tham số cho chế độ Batch — phải có cache_control."""
    p = K.tham_so_tai_lieu(1, CAP, "đoạn toàn văn", "claude-sonnet-5-5", "tltk")
    assert p["system"][0]["cache_control"] == {"type": "ephemeral"}


def test_duong_goi_truc_tiep_danh_dau_cache(monkeypatch):
    """`kiem_tai_lieu` gọi trực tiếp — cũng phải có cache_control. Thiếu bên này thì mọi lượt KHÔNG dùng --batch
    (mặc định) vẫn trả giá nguyên, đúng lỗ 0% đã đo."""
    ghi = {}

    def goi_gia(noi, **kw):
        ghi.update(kw)
        return API.KetQuaGoi(van_ban='{"ket_qua": []}', model="claude-sonnet-5-5", token_vao=9, token_ra=1)

    monkeypatch.setattr(API, "goi", goi_gia)
    K.kiem_tai_lieu(1, CAP, "đoạn", "claude-sonnet-5-5", None, "tltk")
    assert ghi.get("cache_he_thong") is True


def test_hai_duong_dung_CUNG_lanh_dan_va_cung_cache():
    """Hai đường phải gửi y nguyên một `he_thong`; khác nhau thì cache của đường này không dùng được cho đường kia."""
    p = K.tham_so_tai_lieu(1, CAP, "đoạn", "claude-sonnet-5-5", "tltk")
    assert API.van_ban_he_thong(p) == K.HE_THONG


# ── Tiền: bật cache thì PHẢI đếm token cache ─────────────────────────────────────────────────────────────────────
def test_gia_phai_tinh_phi_ghi_cache():
    """Ghi cache tốn 1,25× giá vào. Bỏ qua `cache_ghi` ⇒ báo cáo ghi THIẾU tiền."""
    khong_dem = API.uoc_chi_phi(1000, 100, "claude-sonnet-5-5")
    co_dem = API.uoc_chi_phi(1000, 100, "claude-sonnet-5-5", cache_ghi=816)
    assert co_dem > khong_dem


def test_gia_doc_cache_re_hon_gia_vao():
    """Đọc cache rẻ hơn hẳn: đây là chỗ tiết kiệm thật khi 87 tài liệu sau đọc lại cùng lời dặn."""
    assert API.he_so_doc_cache("claude-sonnet-5-5") == pytest.approx(0.05)
    nhu_vao = API.uoc_chi_phi(816, 0, "claude-sonnet-5-5")
    qua_cache = API.uoc_chi_phi(0, 0, "claude-sonnet-5-5", cache_doc=816)
    assert qua_cache < nhu_vao / 10


def test_hoa_von_tu_tai_lieu_thu_hai():
    """88 tài liệu dùng chung một lời dặn ⇒ `nen_cache` phải nói CÓ ngay từ lần tái dùng đầu."""
    assert API.nen_cache(1, model="claude-sonnet-5-5") is True
    assert API.nen_cache(87, model="claude-sonnet-5-5") is True


# ── Khuôn báo cáo: thêm cache mà KHÔNG phá khuôn v1 ──────────────────────────────────────────────────────────────
def test_khuon_bao_cao_v1_giu_nguyen_khi_khong_co_cache():
    """Lượt không có token cache ⇒ báo cáo JSON giữ ĐÚNG khuôn cũ (chỉ vao/ra).

    Báo cáo là tệp lưu lâu dài mang nhãn schema `kiem_trich_dan_toan_van/v1` và công cụ khác đọc theo khuôn đó —
    thêm khoá vào MỌI bản ghi là đổi khuôn không cần thiết. Test của PR #387
    (`test_toan_van_batch_chi_gui_thuong_tai_lieu_bi_tu_choi`) khẳng định `token_batch == {"vao":…, "ra":…}` đúng
    bằng, nên nếu đổi khuôn vô điều kiện thì test đó đỏ — và nó đỏ ĐÚNG."""
    assert K._tok_bc({"vao": 1000, "ra": 200, "cache_ghi": 0, "cache_doc": 0}) == {"vao": 1000, "ra": 200}


def test_khuon_bao_cao_them_cache_khi_co():
    assert K._tok_bc({"vao": 10, "ra": 2, "cache_ghi": 816, "cache_doc": 0}) == {
        "vao": 10, "ra": 2, "cache_ghi": 816,
    }
    assert K._tok_bc({"vao": 10, "ra": 2, "cache_ghi": 0, "cache_doc": 816}) == {
        "vao": 10, "ra": 2, "cache_doc": 816,
    }


def test_vao_ra_luon_co_du_bang_0():
    """`vao`/`ra` là khoá bắt buộc của khuôn — không được rụng khi bằng 0."""
    assert K._tok_bc({"vao": 0, "ra": 0, "cache_ghi": 0, "cache_doc": 0}) == {"vao": 0, "ra": 0}
