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


# ── 5. Luật hoà vốn `nen_cache` ──────────────────────────────────────────────────────────────────────────────────
def test_khong_tai_dung_thi_khong_nen_cache():
    """Gửi một lần rồi thôi ⇒ ghi cache là tiền bỏ đi (đúng quyết định đã có ở phan_bien_may_de_cuong)."""
    assert API.nen_cache(0) is False


def test_tai_dung_mot_lan_da_nen_cache_voi_ttl_5m():
    """Sonnet 5.5: đọc 0,05× ⇒ 1,25 + 0,05 = 1,30 < 2,00 ⇒ lợi ngay từ lần tái dùng đầu."""
    assert API.nen_cache(1, ttl="5m", model="claude-sonnet-5-5") is True


def test_ttl_1h_can_nhieu_lan_tai_dung_hon_5m():
    """Ghi 1h tốn 2× nên hoà vốn muộn hơn: 1 lần tái dùng chưa đủ, 2 lần thì đủ."""
    assert API.nen_cache(1, ttl="1h", model="claude-sonnet-5-5") is False
    assert API.nen_cache(2, ttl="1h", model="claude-sonnet-5-5") is True


def test_nen_cache_dung_he_so_doc_cua_tung_model():
    """Model có giá đọc cache cao hơn thì hoà vốn chậm hơn — không dùng một hệ số chung cho mọi model."""
    # claude-fable-5: doc_cache 1.00 / vao 10.00 = 0,10× ; claude-sonnet-5-5 = 0,05×
    assert API.he_so_doc_cache("claude-sonnet-5-5") == pytest.approx(0.05)
    assert API.he_so_doc_cache("claude-fable-5") == pytest.approx(0.10)


def test_nen_cache_khong_bien_minh_viec_phinh_prefix():
    """Chốt bằng SỐ cạm bẫy đã ghi trong docstring: dồn corpus dùng-một-lần vào prefix chung thì LỖ.

    34 lô × 6 tài liệu × 1.000 token gửi thẳng = 204.000. Dồn cả corpus 100 tài liệu vào prefix cache =
    100.000×1,25 + 33×100.000×0,05 = 290.000. Cache ĐẮT HƠN 1,42× — nên `nen_cache` không được dùng để biện minh."""
    gui_thang = 34 * 6 * 1000
    corpus = 100 * 1000
    qua_cache = corpus * API.HE_SO_GHI_CACHE + 33 * corpus * API.he_so_doc_cache("claude-sonnet-5-5")
    assert qua_cache > gui_thang


# ── 6. Chẩn đoán cache ───────────────────────────────────────────────────────────────────────────────────────────
def test_chan_doan_mac_dinh_tat(monkeypatch):
    """Mặc định TẮT ⇒ request giữ đúng khuôn các lượt đã chạy thật, không có khoá `diagnostics`."""
    monkeypatch.delenv(API.BIEN_CHAN_DOAN_CACHE, raising=False)
    assert API.chan_doan_cache_bat() is False
    kh = KhachGia("ok")
    API.goi("x", client=kh, nguon="t")
    assert "diagnostics" not in kh.messages.goi[-1]


def test_chan_doan_bat_thi_luot_dau_gui_none(monkeypatch, so):
    """Lượt đầu của một nguồn: `previous_message_id=None` = khai báo tham gia, chưa có gì để so."""
    monkeypatch.setenv(API.BIEN_CHAN_DOAN_CACHE, "1")
    monkeypatch.setattr(API, "_ID_LUOT_TRUOC", {}, raising=False)
    kh = KhachGia(lambda kw: _resp_usage(input_tokens=10, output_tokens=5))
    API.goi("x", client=kh, nguon="nguon_a")
    assert kh.messages.goi[-1]["diagnostics"] == {"previous_message_id": None}


def test_chan_doan_noi_chuoi_theo_tung_nguon(monkeypatch, so):
    """Chuỗi phải so hai lượt LIÊN TIẾP của CÙNG công cụ — trộn các công cụ thì chẩn đoán vô nghĩa."""
    monkeypatch.setenv(API.BIEN_CHAN_DOAN_CACHE, "1")
    monkeypatch.setattr(API, "_ID_LUOT_TRUOC", {}, raising=False)

    def tra(kw):
        r = _resp_usage(input_tokens=10, output_tokens=5)
        r.id = "msg_a1" if kw.get("diagnostics", {}).get("previous_message_id") is None else "msg_a2"
        return r

    kh = KhachGia(tra)
    API.goi("x", client=kh, nguon="nguon_a")          # lượt 1 nguồn A -> id msg_a1
    API.goi("y", client=kh, nguon="nguon_b")          # nguồn B: chuỗi RIÊNG, vẫn phải là None
    assert kh.messages.goi[-1]["diagnostics"] == {"previous_message_id": None}
    API.goi("z", client=kh, nguon="nguon_a")          # lượt 2 nguồn A -> phải nối vào msg_a1
    assert kh.messages.goi[-1]["diagnostics"] == {"previous_message_id": "msg_a1"}


def test_doc_ly_do_truot_va_ghi_vao_so(monkeypatch, so):
    monkeypatch.setenv(API.BIEN_CHAN_DOAN_CACHE, "1")
    monkeypatch.setattr(API, "_ID_LUOT_TRUOC", {}, raising=False)
    r = _resp_usage(input_tokens=10, output_tokens=5)
    r.diagnostics = {"cache_miss_reason": {"type": "system_changed", "cache_missed_input_tokens": 41850}}
    kq = API.goi("x", client=KhachGia(lambda kw: r), nguon="nguon_a")
    assert (kq.ly_do_truot_cache, kq.token_truot_cache) == ("system_changed", 41850)
    assert _doc(so)["luot"][-1]["token"] is not None
    assert _doc(so)["luot"][-1]["truot_cache"] == "system_changed"


def test_so_sanh_chua_xong_khong_doc_thanh_da_khop(so):
    """`cache_miss_reason: None` = so sánh CHƯA xong (vô định) — không được hiểu là «prefix đã khớp»."""
    r = _resp_usage(input_tokens=10, output_tokens=5)
    r.diagnostics = {"cache_miss_reason": None}
    kq = API.goi("x", client=KhachGia(lambda kw: r), nguon="nguon_a")
    assert kq.ly_do_truot_cache is None
    assert "truot_cache" not in _doc(so)["luot"][-1]


def test_chan_doan_khong_lam_hong_luot_goi_khi_sdk_cu(monkeypatch, so, capsys):
    """SDK chưa biết `diagnostics` ⇒ gọi lại KHÔNG chẩn đoán, lượt vẫn thành công (best-effort, không chặn)."""
    monkeypatch.setenv(API.BIEN_CHAN_DOAN_CACHE, "1")
    monkeypatch.setattr(API, "_ID_LUOT_TRUOC", {}, raising=False)

    def tra(kw):
        if "diagnostics" in kw:
            raise TypeError("create() got an unexpected keyword argument 'diagnostics'")
        return _resp_usage(input_tokens=10, output_tokens=5)

    kq = API.goi("x", client=KhachGia(tra), nguon="nguon_a")
    assert kq.van_ban == "ok"
    assert "bỏ chẩn đoán cache" in capsys.readouterr().out


def test_loi_type_error_that_van_bao_loi_khi_chan_doan_tat(monkeypatch, so):
    """Khi chẩn đoán TẮT, TypeError là lỗi thật của tham số ⇒ phải ném LoiApi, không được nuốt."""
    monkeypatch.delenv(API.BIEN_CHAN_DOAN_CACHE, raising=False)

    def tra(kw):
        raise TypeError("tham số sai thật")

    with pytest.raises(API.LoiApi):
        API.goi("x", client=KhachGia(tra), nguon="nguon_a")


# ── 7. Công cụ đo hiệu quả cache ─────────────────────────────────────────────────────────────────────────────────
def _so_gia(luot):
    return {"thang": "2026-11", "usd": 1.0, "luot": luot, "batch_da_ghi": []}


def _luot(nguon, vao, ghi, doc, model="claude-sonnet-5-5", **extra):
    t = {"vao": vao, "ra": 100, "cache_ghi": ghi, "cache_doc": doc}
    return {"luc": "2026-11-20T10:00:00", "nguon": nguon, "model": model, "usd": 0.01, "batch": None,
            "token": t, **extra}


def test_do_cache_xep_nhan_dang_lo_khi_ghi_nhieu_hon_doc():
    import do_cache_api as DO

    bc = DO.bao_cao(_so_gia([_luot("x", 20000, 15000, 2000) for _ in range(4)]))
    assert bc["theo_nguon"]["x"]["nhan"] == "ĐANG LỖ VÌ CACHE"


def test_do_cache_xep_nhan_da_tot_khi_ty_le_doc_cao():
    import do_cache_api as DO

    bc = DO.bao_cao(_so_gia([_luot("x", 400, 0, 50000) for _ in range(3)]))
    assert bc["theo_nguon"]["x"]["nhan"] == "ĐÃ TỐT"


def test_do_cache_xep_nhan_chua_bat_khi_khong_co_token_cache():
    import do_cache_api as DO

    bc = DO.bao_cao(_so_gia([_luot("x", 80000, 0, 0)]))
    assert bc["theo_nguon"]["x"]["nhan"] == "CHƯA BẬT CACHE"


def test_do_cache_khong_phan_khi_qua_it_du_lieu():
    """Vài lượt lẻ không đủ để kết luận — phải nói rõ «chưa đủ dữ liệu», không phán bừa."""
    import do_cache_api as DO

    bc = DO.bao_cao(_so_gia([_luot("x", 100, 0, 0)]))
    assert bc["theo_nguon"]["x"]["nhan"] == "CHƯA ĐỦ DỮ LIỆU"


def test_do_cache_tai_hien_dung_buc_tranh_console_cua_a12():
    """Mô phỏng đúng A12 thật: system 591 token cached + abstract MỚI mỗi lô ⇒ khấu hao cao mà tỷ lệ đọc thấp.

    Đây chính là hình dạng Console báo cho Sonnet 5.5 (12,7% đọc / 3,70× khấu hao) — nhãn phải là CẦN XEM LẠI,
    KHÔNG phải ĐANG LỖ, vì cache đang hoạt động đúng; vấn đề là phần đầu vào mới mỗi lượt."""
    import do_cache_api as DO

    luot = [_luot("a12", 6000, 591 if i == 0 else 0, 0 if i == 0 else 591) for i in range(34)]
    v = DO.bao_cao(_so_gia(luot))["theo_nguon"]["a12"]
    assert v["nhan"] == "CẦN XEM LẠI"
    assert v["khau_hao_ghi"] > 1.0
    assert v["ty_le_doc_cache"] < 0.15


def test_do_cache_gop_ly_do_truot_tu_so():
    import do_cache_api as DO

    luot = [_luot("x", 60000, 0, 0, truot_cache="system_changed") for _ in range(3)]
    luot.append(_luot("x", 60000, 0, 0, truot_cache="tools_changed"))
    v = DO.bao_cao(_so_gia(luot))["theo_nguon"]["x"]
    assert v["ly_do_truot"] == {"system_changed": 3, "tools_changed": 1}


def test_do_cache_thieu_so_thi_bao_ro_phai_lam_gi(tmp_path):
    import do_cache_api as DO

    with pytest.raises(RuntimeError, match="Không thấy sổ chi phí"):
        DO.doc_so(str(tmp_path / "khong-co.json"))


def test_do_cache_so_hong_khong_sap(tmp_path):
    import do_cache_api as DO

    p = tmp_path / "so.json"
    p.write_text("{khong phai json", encoding="utf-8")
    with pytest.raises(RuntimeError, match="không đọc được"):
        DO.doc_so(str(p))


def test_do_cache_bo_qua_luot_khuon_la():
    """Sổ có lượt thiếu `token` hoặc kiểu lạ ⇒ bỏ qua, không sập (sổ là tệp lưu lâu dài, khuôn có thể cũ)."""
    import do_cache_api as DO

    bc = DO.bao_cao(_so_gia(["chuỗi lạ", {"nguon": "x"}, {"nguon": "y", "token": "không phải dict"},
                             _luot("z", 60000, 0, 0)]))
    assert "z" in bc["theo_nguon"]
