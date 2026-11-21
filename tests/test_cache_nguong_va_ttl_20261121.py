"""Prompt caching: canh NGƯỠNG TỐI THIỂU và TTL (21/11/2026, bác sĩ: «cài lưu bộ nhớ đệm câu lệnh»).

Vì sao cần canh. Đo trên Console «Phân tích bộ nhớ đệm» (7 ngày tới 20/11/2026): Sonnet 5.5 chiếm 13 Tr token vào mà
tỷ lệ đọc cache chỉ 12,7%, khấu hao ghi 3,70× — trong khi Opus 5.5 đạt 99,2% / 16,0×. Soi mã thấy hai kiểu hở:

1. NGƯỠNG IM LẶNG. Prefix dưới ngưỡng tối thiểu của model thì API KHÔNG cache và KHÔNG tính phí ghi — không lỗi,
   không cảnh báo. `HE_THONG` của `kiem_noi_dung_trich_dan` đo được ~519-571 token, tức NẰM SÁT ngưỡng 512 của
   Sonnet 5.5: sửa vài câu chữ là rơi xuống dưới và mất cache mà không ai hay. Test ở đây chốt sàn có khoảng dự
   phòng, nên lần sửa prompt nào làm hụt sẽ ĐỎ ngay tại chỗ thay vì chỉ hiện ra ở hoá đơn cuối tháng.
2. TTL GHI SAI GIÁ. Ghi cache 5 phút tính 1,25× giá vào, 1 giờ tính 2×. Gộp một hệ số thì lượt 1h bị ghi THIẾU tiền
   vào sổ chi phí ⇒ trần tháng canh sai (fail-open về tiền). Test chốt việc tách theo `usage.cache_creation`.

Không gọi mạng, không đọc khoá thật: khách API là khách giả, sổ chi phí là tệp tạm.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))

import api_claude_nc as API  # noqa: E402
import kiem_noi_dung_trich_dan as KND  # noqa: E402
import phan_bien_may_de_cuong as PBM  # noqa: E402

from tests.test_api_claude_nghien_cuu_20261117 import KhachGia  # noqa: E402


@pytest.fixture
def so(tmp_path, monkeypatch):
    """Sổ chi phí tạm + trần mặc định (không để biến môi trường máy bác sĩ lọt vào) — khai tại chỗ cho tệp tự chứa."""
    duong = tmp_path / "so-chi-phi.json"
    monkeypatch.setattr(API, "SO_CHI_PHI", str(duong))
    monkeypatch.delenv("EBM_API_CLAUDE_TRAN_USD_THANG", raising=False)
    return duong


def _doc(duong):
    import json

    return json.loads(Path(duong).read_text(encoding="utf-8"))

# Khoảng dự phòng trên ngưỡng 512: prompt phải vượt ngưỡng ÍT NHẤT bằng mức này mới coi là an toàn. 15% là đủ để một
# lần sửa câu chữ thông thường không làm hụt, mà không buộc phải viết dài vô cớ.
DU_PHONG = 1.15

# System prompt TĨNH được gọi với `cache_he_thong=True` ⇒ phải nằm trên ngưỡng mới thật sự được cache.
# (`phan_bien_may_de_cuong.HE_THONG` CỐ Ý không cache — một lượt mỗi lần chạy — nên không có trong danh sách này;
# `test_phan_bien_mot_luot_khong_danh_dau_cache` đã chốt điều đó.)
PROMPT_CO_CACHE = {
    "kiem_noi_dung_trich_dan.HE_THONG": KND.HE_THONG,
}


def _resp_usage(**u):
    return SimpleNamespace(
        content=[SimpleNamespace(text="ok")],
        stop_reason="end_turn",
        model="claude-sonnet-5-5",
        usage=SimpleNamespace(**u),
        stop_details=None,
    )


# ── 1. Ngưỡng tối thiểu ──────────────────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("ten", sorted(PROMPT_CO_CACHE))
def test_prompt_duoc_cache_phai_vuot_nguong_co_du_phong(ten):
    """Prompt dùng với cache_he_thong=True phải vượt ngưỡng 512 token kèm dự phòng 15%.

    ĐỎ ở đây nghĩa là: prompt vừa bị sửa ngắn đi và lượt gọi sẽ ÂM THẦM không còn được cache. Cách xử lý là xem lại
    bản sửa (viết đủ lời dặn) hoặc bỏ `cache_he_thong=True` ở chỗ gọi — KHÔNG hạ `DU_PHONG` để test xanh lại."""
    nguong = API.NGUONG_CACHE_TOKEN["claude-sonnet-5-5"]
    thuc = API.uoc_token(PROMPT_CO_CACHE[ten])
    assert thuc >= nguong * DU_PHONG, (
        f"{ten}: ~{thuc} token, dưới sàn an toàn {int(nguong * DU_PHONG)} "
        f"(ngưỡng cache {nguong}) ⇒ API sẽ không cache mà không báo lỗi."
    )


def test_bang_nguong_phu_het_model_hien_hanh():
    """Mọi model trong MODEL_HIEN_HANH phải có ngưỡng đã ghi — thêm model mới mà quên ngưỡng thì test trên vô nghĩa."""
    thieu = sorted(API.MODEL_HIEN_HANH - set(API.NGUONG_CACHE_TOKEN))
    assert not thieu, f"Thiếu ngưỡng cache cho: {', '.join(thieu)}"


def test_nguong_than_trong_khong_thap_hon_moi_nguong_da_ghi():
    """Mức thận trọng dùng cho model lạ phải là mức CAO nhất, không được thấp hơn bất kỳ ngưỡng đã biết."""
    assert API.NGUONG_CACHE_THAN_TRONG >= max(API.NGUONG_CACHE_TOKEN.values())


# ── 2. TTL ───────────────────────────────────────────────────────────────────────────────────────────────────────
def test_mac_dinh_5m_khong_gui_truong_ttl():
    """TTL mặc định KHÔNG gửi `ttl` — giữ nguyên khuôn tham số của các lượt đã chạy thật trước đây."""
    p = API.tham_so("x", he_thong="vai" * 500, cache_he_thong=True)
    assert p["system"][0]["cache_control"] == {"type": "ephemeral"}


def test_ttl_1h_gui_dung_truong():
    p = API.tham_so("x", he_thong="vai" * 500, cache_he_thong=True, cache_ttl="1h")
    assert p["system"][0]["cache_control"] == {"type": "ephemeral", "ttl": "1h"}


def test_ttl_chi_co_nghia_khi_bat_cache():
    """Không bật cache thì system vẫn là chuỗi trơn, TTL không tạo ra khối lạ."""
    p = API.tham_so("x", he_thong="vai", cache_ttl="1h")
    assert p["system"] == "vai"


@pytest.mark.parametrize("xau", ["10m", "1 h", "", "2h", "1H"])
def test_ttl_la_khong_hop_le_thi_chan_truoc_khi_gui(xau):
    """TTL lạ phải chặn tại chỗ, không để API trả 400 sau khi đã tính vào trần chi phí."""
    with pytest.raises(API.LoiCucBo):
        API.tham_so("x", he_thong="vai", cache_he_thong=True, cache_ttl=xau)


# ── 3. Giá ghi cache theo TTL ────────────────────────────────────────────────────────────────────────────────────
def test_ghi_5m_tinh_1_25_lan():
    usd = API.uoc_chi_phi(0, 0, "claude-sonnet-5-5", cache_ghi=1000)
    assert usd == pytest.approx(1000 * 2.00 * 1.25 / 1e6)


def test_ghi_1h_tinh_2_lan():
    usd = API.uoc_chi_phi(0, 0, "claude-sonnet-5-5", cache_ghi=1000, cache_ghi_1h=1000)
    assert usd == pytest.approx(1000 * 2.00 * 2.00 / 1e6)


def test_ghi_tron_5m_va_1h_tinh_tach_phan():
    """cache_ghi là TỔNG; phần 1h tính 2×, phần còn lại 1,25× — không tính trùng."""
    usd = API.uoc_chi_phi(0, 0, "claude-sonnet-5-5", cache_ghi=1000, cache_ghi_1h=400)
    assert usd == pytest.approx((600 * 1.25 + 400 * 2.00) * 2.00 / 1e6)


def test_cache_ghi_1h_lon_hon_tong_thi_kep_ve_tong():
    """Số liệu `usage` lạ (1h > tổng) không được làm giá vọt lên — kẹp về tổng, không ném lỗi trên lượt ĐÃ trả tiền."""
    usd = API.uoc_chi_phi(0, 0, "claude-sonnet-5-5", cache_ghi=500, cache_ghi_1h=9000)
    assert usd == pytest.approx(500 * 2.00 * 2.00 / 1e6)


def test_doc_tach_ttl_tu_usage_va_ghi_so(so):
    """`goi` đọc `usage.cache_creation.ephemeral_1h_input_tokens` và ghi sổ theo giá 2× cho phần đó."""
    kh = KhachGia(
        lambda kw: _resp_usage(
            input_tokens=100,
            output_tokens=20,
            cache_creation_input_tokens=1000,
            cache_read_input_tokens=0,
            cache_creation=SimpleNamespace(ephemeral_5m_input_tokens=0, ephemeral_1h_input_tokens=1000),
        )
    )
    kq = API.goi("x", client=kh, nguon="kiem_noi_dung_trich_dan")
    assert kq.token_cache_ghi_1h == 1000
    d = _doc(so)
    assert d["usd"] == pytest.approx((100 * 2 + 1000 * 2 * 2.00 + 20 * 10) / 1e6)
    assert d["luot"][-1]["token"]["cache_ghi_1h"] == 1000


def test_thieu_truong_cache_creation_thi_coi_la_5m(so):
    """SDK cũ / khách giả không có `cache_creation` ⇒ 0 token 1h, khuôn sổ giữ như trước (không thêm khoá)."""
    kh = KhachGia(
        lambda kw: _resp_usage(
            input_tokens=100, output_tokens=20, cache_creation_input_tokens=800, cache_read_input_tokens=0
        )
    )
    kq = API.goi("x", client=kh, nguon="kiem_noi_dung_trich_dan")
    assert kq.token_cache_ghi_1h == 0
    assert "cache_ghi_1h" not in _doc(so)["luot"][-1]["token"]


# ── 4. Runtime agent: system prompt phải được đánh dấu cache ──────────────────────────────────────────────────────
def test_runtime_danh_dau_cache_system_mac_dinh(monkeypatch):
    """`ClaudeApiRuntime` gửi agent spec (tĩnh theo agent_id, trung bình ~5.300 token) ⇒ phải đánh dấu cache."""
    from runtime import claude_api_runtime as CAR

    monkeypatch.delenv(CAR._BIEN_TAT_CACHE, raising=False)
    s = CAR._tham_so_system("lời dặn dài")
    assert s == [{"type": "text", "text": "lời dặn dài", "cache_control": {"type": "ephemeral"}}]


@pytest.mark.parametrize("gia_tri", ["1", "true", "YES", "on"])
def test_runtime_tat_cache_bang_bien_moi_truong(monkeypatch, gia_tri):
    from runtime import claude_api_runtime as CAR

    monkeypatch.setenv(CAR._BIEN_TAT_CACHE, gia_tri)
    assert CAR._tham_so_system("lời dặn dài") == "lời dặn dài"


def test_runtime_gia_tri_la_van_coi_la_bat(monkeypatch):
    """Biến đặt giá trị lạ ⇒ KHÔNG tắt cache (mặc định an toàn về chi phí, không im lặng mất cache)."""
    from runtime import claude_api_runtime as CAR

    monkeypatch.setenv(CAR._BIEN_TAT_CACHE, "co-le")
    assert isinstance(CAR._tham_so_system("lời dặn dài"), list)


def test_agent_spec_du_nguong_cho_model_nguong_512():
    """Mọi agent spec in-repo phải vượt ngưỡng 512 token — nếu không, cache ở runtime là vô ích với model hiện hành."""
    specs = sorted((REPO / ".claude" / "agents").glob("*.md"))
    assert specs, "không thấy agent spec in-repo"
    hut = [p.name for p in specs if API.uoc_token(p.read_text(encoding="utf-8")) < 512]
    assert not hut, f"spec dưới ngưỡng 512 token: {', '.join(hut)}"


def test_phan_bien_van_khong_cache_sau_khi_them_ttl():
    """Chốt lại sau khi thêm TTL: lượt MỘT LẦN vẫn không đánh dấu cache (ghi 1,25× mà không ai đọc lại)."""
    assert "cache_he_thong=True" not in (REPO / "tools" / "phan_bien_may_de_cuong.py").read_text(encoding="utf-8")
    assert API.tham_so("x", he_thong=PBM.HE_THONG)["system"] == PBM.HE_THONG
