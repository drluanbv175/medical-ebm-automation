"""Hoàn thiện kết nối Claude API cho hệ nghiên cứu (18/11/2026, bác sĩ chọn cả bốn mục).

- Trần chi phí tháng + sổ chi phí: chặn TRƯỚC khi gửi, ghi số tiêu THẬT (gồm token cache), fail-closed khi sổ hỏng.
- Prompt caching: system prompt lặp lại được đánh dấu `cache_control`; lượt một lần thì không.
- Hội đồng batch `--chi-lay`: chỉ lấy kết quả đã trả phí, không tự nộp batch kế tiếp.
- Báo cáo A12/phản biện máy mang mã băm đề cương để biết khi nào báo cáo đã cũ.

Không gọi mạng, không đọc khoá thật: mọi khách API là khách giả; sổ chi phí là tệp tạm.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))

import api_claude_nc as API  # noqa: E402
import kiem_noi_dung_trich_dan as KND  # noqa: E402
import phan_bien_may_de_cuong as PBM  # noqa: E402

from tests.test_api_claude_nghien_cuu_20261117 import (  # noqa: E402
    ABS,
    VAN_PB,
    KhachBatch,
    KhachGia,
    _chay,
    _chuan_bi,
    _goc_tam,
    _resp,
    _tra_knd,
)


@pytest.fixture
def so(tmp_path, monkeypatch):
    """Sổ chi phí tạm + trần mặc định (không để biến môi trường máy bác sĩ lọt vào)."""
    duong = tmp_path / "so-chi-phi.json"
    monkeypatch.setattr(API, "SO_CHI_PHI", str(duong))
    monkeypatch.delenv("EBM_API_CLAUDE_TRAN_USD_THANG", raising=False)
    return duong


def _doc(duong):
    return json.loads(Path(duong).read_text(encoding="utf-8"))


def _ghi_so(duong, usd, thang=None):
    Path(duong).write_text(
        json.dumps({"thang": thang or API._thang_nay(), "usd": usd, "luot": [], "batch_da_ghi": []}),
        encoding="utf-8",
        newline="\n",
    )


def _resp_cache(stop="end_turn"):
    r = _resp('{"ok": 1}', stop=stop)
    r.usage = SimpleNamespace(
        input_tokens=100, output_tokens=20, cache_creation_input_tokens=1000, cache_read_input_tokens=2000
    )
    return r


# ── Trần chi phí tháng ───────────────────────────────────────────────────────────────────────────────────────────
def test_vuot_tran_khong_gui(so, monkeypatch):
    monkeypatch.setenv("EBM_API_CLAUDE_TRAN_USD_THANG", "1")
    _ghi_so(so, 0.99)
    kh = KhachGia("ok")
    with pytest.raises(API.HetNganSach, match="vượt trần"):
        API.goi("x", client=kh, max_tokens=16000, nguon="kiem")  # ước tối đa 0,16 USD + 0,99 > 1
    assert kh.messages.goi == []


@pytest.mark.parametrize("gia_tri", ["0", "-5", "khong-phai-so"])
def test_tran_khoa_hay_khong_doc_duoc_la_chan(so, monkeypatch, gia_tri):
    monkeypatch.setenv("EBM_API_CLAUDE_TRAN_USD_THANG", gia_tri)
    kh = KhachGia("ok")
    with pytest.raises(API.HetNganSach, match="khoá hẳn"):  # thông điệp riêng — không lẫn với «vượt trần»
        API.goi("x", client=kh)
    assert kh.messages.goi == []


def test_tran_chap_nhan_dau_phay_thap_phan(monkeypatch):
    monkeypatch.setenv("EBM_API_CLAUDE_TRAN_USD_THANG", "7,5")
    assert API.tran_usd_thang() == pytest.approx(7.5)


def test_model_chua_ghi_gia_la_chan(so):
    kh = KhachGia("ok")
    with pytest.raises(API.HetNganSach, match="Chưa ghi giá"):
        API.goi("x", model="claude-moi-chua-co-gia", client=kh)
    assert kh.messages.goi == []


def test_so_hong_thi_chan_va_khong_ghi_de(so):
    so.write_text("{hỏng", encoding="utf-8", newline="\n")
    kh = KhachGia("ok")
    with pytest.raises(API.HetNganSach, match="không đọc được"):
        API.goi("x", client=kh)
    API.ghi_chi_phi(1.0, "x", "claude-sonnet-5-5", {"vao": 1})
    assert so.read_text(encoding="utf-8") == "{hỏng" and kh.messages.goi == []


def test_so_sai_khuon_thi_chan(so):
    so.write_text(json.dumps({"thang": API._thang_nay(), "usd": "nhiều"}), encoding="utf-8", newline="\n")
    with pytest.raises(API.HetNganSach, match="sai khuôn"):
        API.goi("x", client=KhachGia("ok"))


def test_sang_thang_moi_dem_lai_tu_dau(so):
    _ghi_so(so, 19.9, thang="2000-01")
    API.goi("x", client=KhachGia("ok"), nguon="kiem")
    d = _doc(so)
    assert d["thang"] == API._thang_nay() and d["usd"] < 1
    assert d["thang_truoc"] == {"thang": "2000-01", "usd": 19.9}


def test_ghi_so_tien_that_gom_token_cache(so):
    kh = KhachGia(lambda kw: _resp_cache())
    kq = API.goi("x", client=kh, nguon="kiem_noi_dung_trich_dan")
    assert (kq.token_cache_ghi, kq.token_cache_doc) == (1000, 2000)
    d = _doc(so)
    # Sonnet 5.5: 100×2 + 1000×2×1,25 + 2000×0,10 + 20×10 (USD/triệu token)
    assert d["usd"] == pytest.approx((100 * 2 + 1000 * 2 * 1.25 + 2000 * 0.10 + 20 * 10) / 1e6)
    assert d["luot"][-1]["nguon"] == "kiem_noi_dung_trich_dan"
    assert d["luot"][-1]["token"] == {"vao": 100, "ra": 20, "cache_ghi": 1000, "cache_doc": 2000}


@pytest.mark.parametrize("stop", ["max_tokens", "refusal"])
def test_luot_hong_van_tinh_tien(so, stop):
    with pytest.raises(API.KetQuaHong):
        API.goi("x", client=KhachGia(lambda kw: _resp_cache(stop=stop)))
    assert _doc(so)["usd"] > 0  # API đã tính phí lượt này dù câu trả lời không dùng được


def test_khong_dung_so_that_duoi_pytest(monkeypatch):
    monkeypatch.setattr(API, "SO_CHI_PHI", API._SO_CP_THAT)
    monkeypatch.delenv("EBM_KIEM_API_THAT", raising=False)
    so = API.doc_so_chi_phi()
    assert so.get("_khong_ghi") is True and so["usd"] == 0.0


def test_uoc_toi_da_tinh_ca_anh_va_toan_bo_max_tokens():
    p = API.tham_so([{"type": "image"}, {"type": "text", "text": "abc"}], he_thong="xyz", max_tokens=1000)
    vao = API.uoc_token("xyz\nabc") + API.TOKEN_UOC_MOI_ANH
    assert API.uoc_toi_da(p) == pytest.approx((vao * 2 + 1000 * 10) / 1e6)
    assert API.uoc_toi_da(p, batch=True) == pytest.approx(API.uoc_toi_da(p) / 2)


# ── Batch: trần lúc nộp, ghi sổ một lần lúc lấy ─────────────────────────────────────────────────────────────────
def test_nop_batch_vuot_tran_khong_gui(so, monkeypatch):
    monkeypatch.setenv("EBM_API_CLAUDE_TRAN_USD_THANG", "0.01")
    kh = KhachBatch()
    yc = [(f"cm_{i:03d}", API.tham_so("x" * 3000, he_thong="vai", max_tokens=16000)) for i in range(3)]
    with pytest.raises(API.HetNganSach):
        API.nop_batch(yc, kh, nguon="hoi_dong")
    assert kh.lo == {}


def test_ket_qua_batch_ghi_so_mot_lan_theo_id(so):
    kh = KhachBatch()
    bid = API.nop_batch([("cm_000", API.tham_so("x", he_thong="vai"))], kh, nguon="hoi_dong")
    API.doc_ket_qua_batch(bid, kh, nguon="hoi_dong")
    lan_1 = _doc(so)["usd"]
    API.doc_ket_qua_batch(bid, kh, nguon="hoi_dong")  # đọc lại cùng batch ⇒ không cộng hai lần
    d = _doc(so)
    assert d["usd"] == lan_1 == pytest.approx((1000 * 2 + 200 * 10) * 0.5 / 1e6)  # giá Batch = 50%
    assert d["batch_da_ghi"] == [bid]


# ── Prompt caching ───────────────────────────────────────────────────────────────────────────────────────────────
def test_cache_he_thong_chi_khi_yeu_cau():
    assert API.tham_so("x", he_thong="vai")["system"] == "vai"
    p = API.tham_so("x", he_thong="vai", cache_he_thong=True)
    assert p["system"] == [{"type": "text", "text": "vai", "cache_control": {"type": "ephemeral"}}]
    assert API.van_ban_he_thong(p) == "vai"


def test_kiem_a12_danh_dau_cache_moi_lo(tmp_path, so):
    goc = _goc_tam(tmp_path)
    kh = KhachGia(_tra_knd)
    KND.main(["--study", "S1", "--goi-api", "--lo", "1"], client=kh, lay=lambda p: ABS, goc=goc)
    assert len(kh.messages.goi) >= 2  # nhiều lô cùng lời dặn
    assert all(g["system"][0]["cache_control"] == {"type": "ephemeral"} for g in kh.messages.goi)


def test_phan_bien_mot_luot_khong_danh_dau_cache(tmp_path, so):
    goc = _goc_tam(tmp_path, VAN_PB)
    kh = KhachGia(json.dumps({"phat_hien": []}))
    PBM.main(["--study", "S1", "--goi-api"], client=kh, goc=goc)
    assert isinstance(kh.messages.goi[0]["system"], str)  # một lượt duy nhất ⇒ ghi cache chỉ tốn thêm


# ── Công cụ dừng cả lượt khi chạm trần ───────────────────────────────────────────────────────────────────────────
def test_a12_cham_tran_dung_ca_luot_khong_ghi_bao_cao(tmp_path, so, monkeypatch, capsys):
    monkeypatch.setenv("EBM_API_CLAUDE_TRAN_USD_THANG", "0.000001")
    goc = _goc_tam(tmp_path)
    kh = KhachGia(_tra_knd)
    ma = KND.main(["--study", "S1", "--goi-api", "--lo", "1"], client=kh, lay=lambda p: ABS, goc=goc)
    assert ma == 2 and kh.messages.goi == [] and "⛔" in capsys.readouterr().out
    assert not (goc / "exports" / "S1" / "kiem_may_api" / "A12_KIEM_NOI_DUNG_S1.json").exists()


def test_phan_bien_cham_tran_la_ma_2(tmp_path, so, monkeypatch):
    monkeypatch.setenv("EBM_API_CLAUDE_TRAN_USD_THANG", "0")
    goc = _goc_tam(tmp_path, VAN_PB)
    kh = KhachGia(json.dumps({"phat_hien": []}))
    assert PBM.main(["--study", "S1", "--goi-api"], client=kh, goc=goc) == 2 and kh.messages.goi == []


# ── Mã băm đề cương trong báo cáo ────────────────────────────────────────────────────────────────────────────────
def test_bao_cao_mang_ma_bam_de_cuong(tmp_path, so):
    import hashlib

    goc = _goc_tam(tmp_path)
    KND.main(["--study", "S1", "--goi-api"], client=KhachGia(_tra_knd), lay=lambda p: ABS, goc=goc)
    tep = goc / "exports" / "S1" / "DE_CUONG_NOP_HOI_DONG_S1.md"
    bam = hashlib.sha256(tep.read_text(encoding="utf-8").encode("utf-8")).hexdigest()
    js = json.loads((goc / "exports" / "S1" / "kiem_may_api" / "A12_KIEM_NOI_DUNG_S1.json").read_text(encoding="utf-8"))
    assert js["tep_sha256"] == bam

    goc2 = _goc_tam(tmp_path / "pb", VAN_PB)
    PBM.main(["--study", "S1", "--goi-api"], client=KhachGia(json.dumps({"phat_hien": []})), goc=goc2)
    pb = json.loads((goc2 / "exports" / "S1" / "kiem_may_api" / "PHAN_BIEN_MAY_S1.json").read_text(encoding="utf-8"))
    assert pb["tep_sha256"] == hashlib.sha256(VAN_PB.encode("utf-8")).hexdigest()


# ── Hội đồng batch --chi-lay ─────────────────────────────────────────────────────────────────────────────────────
def test_chi_lay_khong_nop_batch_ke_tiep(tmp_path, so, capsys):
    goc, out = _chuan_bi(tmp_path)
    kh = KhachBatch()
    assert _chay(goc, kh, "buoc", "--goi-api") == 0 and len(kh.lo) == 1  # nộp batch chấm
    capsys.readouterr()
    assert _chay(goc, kh, "buoc", "--goi-api", "--chi-lay") == 0
    assert len(kh.lo) == 1  # lấy kết quả, KHÔNG nộp batch phản biện
    ra = capsys.readouterr().out
    assert "📥" in ra and "KHÔNG nộp batch kế tiếp" in ra and "đọc cache" in ra
    st = json.loads((out / "kiem_may_api" / "hoi_dong_G3.json").read_text(encoding="utf-8"))
    assert st["batch"] is None and st["lich_su"][-1]["batch_id"] == "msgbatch_0"
    assert "token_cache_doc" in st["lich_su"][-1]
    assert _doc(so)["batch_da_ghi"] == ["msgbatch_0"]


def test_chi_lay_khi_khong_co_batch_cho_thi_khong_nop(tmp_path, so, capsys):
    goc, _ = _chuan_bi(tmp_path)
    kh = KhachBatch()
    assert _chay(goc, kh, "buoc", "--goi-api", "--chi-lay") == 0
    assert kh.lo == {} and "không nộp gì" in capsys.readouterr().out


def test_chi_lay_bao_phan_bi_chan_vi_tai_lieu_doi(tmp_path, so, capsys):
    """Đo thật 18/11/2026 (BTM G3): đề cương sinh lại sau khi khởi tạo ⇒ phần dùng nó bị chặn — `--chi-lay` phải nói
    rõ, không được in «không còn gì» rồi mã 0."""
    from tests.test_api_claude_nghien_cuu_20261117 import TEP

    goc, out = _chuan_bi(tmp_path)
    kh = KhachBatch()
    _chay(goc, kh, "buoc", "--goi-api")
    tep = out / TEP
    tep.write_text(tep.read_text(encoding="utf-8") + "\nsửa sau khi khởi tạo\n", encoding="utf-8", newline="\n")
    capsys.readouterr()
    assert _chay(goc, kh, "buoc", "--goi-api", "--chi-lay") == 1
    ra = capsys.readouterr().out
    assert "KHÔNG đi tiếp được" in ra and "tài liệu đổi" in ra and len(kh.lo) == 1


# ── Duyệt kiểm máy: báo cáo cũ · phiếu · nhãn từ lời bác sĩ · tỷ lệ đúng ─────────────────────────────────────────
import duyet_kiem_may_api as DKM  # noqa: E402


def _de_tai_co_bao_cao(tmp_path, so):
    """Đề tài tạm có đủ hai báo cáo do chính công cụ kiểm sinh ra (khách giả)."""
    goc = _goc_tam(tmp_path, DE_CUONG_DKM)

    def tra_knd(kw):
        dl = json.loads(_tra_knd(kw))
        dl["ket_qua"][0]["tham_chieu"][0].update({"muc": "khong_ho_tro"})  # ⇒ 1 cặp A12 cần duyệt
        return json.dumps(dl)

    KND.main(["--study", "S1", "--goi-api"], client=KhachGia(tra_knd), lay=lambda p: ABS, goc=goc)
    tra_pb = json.dumps(
        {
            "phat_hien": [
                {"loai": "cau_cut", "muc": "vua", "dong": 3, "trich": "Bệnh thận mạn thường gặp ở người ĐTĐ típ 2",
                 "van_de": "câu cụt", "goi_y": "viết lại"},
                {"loai": "cau_cut", "muc": "cao", "dong": 5, "trich": "Ba nghiên cứu cùng chiều",
                 "van_de": "khẳng định thiếu căn cứ", "goi_y": "nêu từng nghiên cứu"},
            ]
        }
    )
    PBM.main(["--study", "S1", "--goi-api"], client=KhachGia(tra_pb), goc=goc)
    return goc


from tests.test_api_claude_nghien_cuu_20261117 import DE_CUONG as DE_CUONG_DKM  # noqa: E402


def test_tinh_trang_moi_chay_la_con_hieu_luc_va_chua_duyet(tmp_path, so):
    goc = _de_tai_co_bao_cao(tmp_path, so)
    t = DKM.tinh_trang("S1", goc)
    b = {x["loai"]: x for x in t["bao_cao"]}
    assert t["do_duoc"] and b["A12"]["cu"] is False and b["PHAN_BIEN"]["cu"] is False
    assert b["A12"]["can_duyet"] >= 1 and b["PHAN_BIEN"]["can_duyet"] == 2
    assert DKM.ma_thoat([t]) == 1  # còn mục chưa duyệt


def test_de_cuong_doi_thi_bao_cao_cu(tmp_path, so):
    goc = _de_tai_co_bao_cao(tmp_path, so)
    tep = goc / "exports" / "S1" / "DE_CUONG_NOP_HOI_DONG_S1.md"
    tep.write_text(tep.read_text(encoding="utf-8") + "\nsửa sau lượt kiểm\n", encoding="utf-8", newline="\n")
    b = {x["loai"]: x for x in DKM.tinh_trang("S1", goc)["bao_cao"]}
    assert b["A12"]["cu"] is True and b["PHAN_BIEN"]["cu"] is True and "mã băm khác" in b["A12"]["ly_do"]


def test_bao_cao_cu_chua_co_ma_bam_suy_theo_thoi_diem(tmp_path, so):
    import os

    goc = _de_tai_co_bao_cao(tmp_path, so)
    p = goc / "exports" / "S1" / "kiem_may_api" / "A12_KIEM_NOI_DUNG_S1.json"
    bc = json.loads(p.read_text(encoding="utf-8"))
    bc.pop("tep_sha256")
    bc["luc"] = "2000-01-01T00:00:00"  # lượt kiểm rất cũ, tệp sửa sau đó
    p.write_text(json.dumps(bc), encoding="utf-8", newline="\n")
    cu, ly_do = DKM.hieu_luc(bc, "S1", goc)
    assert cu is True and "chưa có mã băm" in ly_do
    bc["luc"] = "2999-01-01T00:00:00"  # tệp không sửa sau lượt kiểm ⇒ vẫn KHÔNG khẳng định còn hiệu lực
    assert DKM.hieu_luc(bc, "S1", goc)[0] is None
    assert os.path.exists(p)


def test_doc_loi_bac_si():
    assert DKM.doc_loi("1-3 đúng, 4 sai; 5,7 không rõ", 7) == {
        1: "dung", 2: "dung", 3: "dung", 4: "sai", 5: "khong_ro", 7: "khong_ro"
    }
    assert DKM.doc_loi("2: sai 1 đúng", 2) == {2: "sai", 1: "dung"}


@pytest.mark.parametrize("loi", ["9 đúng", "1 đúng 1 sai", "3-1 đúng", "duyệt hết", ""])
def test_doc_loi_tu_choi_khong_doan(loi):
    with pytest.raises(ValueError):
        DKM.doc_loi(loi, 5)


def test_phieu_ghi_nhan_va_do_ty_le_dung(tmp_path, so):
    goc = _de_tai_co_bao_cao(tmp_path, so)
    md, _, n = DKM.dung_phieu("S1", goc)
    noi_dung = md.read_text(encoding="utf-8")
    assert n == 3 and "**1.**" in noi_dung and "**3.**" in noi_dung and "Máy KHÔNG tự gắn nhãn" in noi_dung
    kq = DKM.ghi_nhan("S1", "1 đúng, 2 đúng, 3 sai", ap_dung=False, goc=goc)
    assert kq["da_ghi"] is False and not DKM.tep_duyet("S1", goc).exists()  # chạy khô không ghi
    DKM.ghi_nhan("S1", "1 đúng, 2 đúng, 3 sai", ap_dung=True, goc=goc)
    d = json.loads(DKM.tep_duyet("S1", goc).read_text(encoding="utf-8"))
    assert d["lan_ghi"][-1]["loi_nguyen_van"] == "1 đúng, 2 đúng, 3 sai"
    t = DKM.tinh_trang("S1", goc)
    assert t["do_dung"]["tong"]["ty_le_dung"] == 0.667  # làm tròn 3 chữ số
    assert DKM.ma_thoat([t]) == 0  # còn hiệu lực + duyệt hết


def test_khong_ro_khong_tinh_vao_mau_so(tmp_path, so):
    goc = _de_tai_co_bao_cao(tmp_path, so)
    DKM.dung_phieu("S1", goc)
    DKM.ghi_nhan("S1", "1 đúng, 2 không rõ", ap_dung=True, goc=goc)
    tong = DKM.tinh_trang("S1", goc)["do_dung"]["tong"]
    assert tong["ty_le_dung"] == 1.0 and tong["khong_ro"] == 1 and tong["chua_duyet"] == 1


def test_bao_cao_chay_lai_sau_phieu_thi_tu_choi_ghi(tmp_path, so):
    goc = _de_tai_co_bao_cao(tmp_path, so)
    DKM.dung_phieu("S1", goc)
    PBM.main(["--study", "S1", "--goi-api"], client=KhachGia(json.dumps({"phat_hien": []})), goc=goc)  # chạy lại
    with pytest.raises(ValueError, match="đổi sau khi dựng phiếu"):
        DKM.ghi_nhan("S1", "1 đúng", ap_dung=True, goc=goc)


def test_bao_cao_hong_va_khong_co_bao_cao(tmp_path, so):
    goc = _de_tai_co_bao_cao(tmp_path, so)
    pb = goc / "exports" / "S1" / "kiem_may_api" / "PHAN_BIEN_MAY_S1.json"
    pb.write_text("{hỏng", encoding="utf-8", newline="\n")
    t = DKM.tinh_trang("S1", goc)
    assert any(b.get("hong") for b in t["bao_cao"]) and DKM.ma_thoat([t]) == 1
    (goc / "exports" / "S2" / "kiem_may_api").mkdir(parents=True)
    assert DKM.tinh_trang("S2", goc)["do_duoc"] is False


def test_tat_ca_bo_de_tai_gia_lap(tmp_path, so):
    goc = _de_tai_co_bao_cao(tmp_path, so)
    (goc / "exports" / "ZZCANARY-X" / "kiem_may_api").mkdir(parents=True)
    assert [t["study"] for t in DKM.tinh_trang_tat_ca(goc)] == ["S1"]
    assert DKM.main(["tinh-trang", "--tat-ca", "--json"], goc=goc) == 1


def test_a12_so_khong_thay_trong_abstract_la_muc_can_duyet():
    """Ca thật BTM 17/11/2026: máy phán «hỗ trợ» nhưng số 15,32/31,1 không có trong abstract ⇒ vẫn phải vào phiếu."""
    bc = {
        "cau": [{"id": "C007", "cau": "Tỷ lệ 15,32–31,1% [12]"}],
        "ket_qua": [
            {"id": "C007", "so": 12, "muc": "ho_tro", "ly_do": "khớp", "trich": "", "co": ["so_khong_thay:15.32,31.1"]},
            {"id": "C008", "so": 3, "muc": "ho_tro", "ly_do": "khớp", "trich": "", "co": []},
        ],
    }
    muc = DKM.muc_can_duyet("A12", bc)
    assert [m["khoa"] for m in muc] == ["A12|C007|12"] and "15,32" in muc[0]["chi_tiet"][0]


def test_tran_doc_tu_kho_bi_mat_khi_moi_truong_trong(tmp_path, monkeypatch):
    """18/11/2026: bác sĩ đặt trần trong kho bí mật — bản đầu chỉ đọc biến môi trường nên lặng lẽ dùng 20 USD."""
    kho = tmp_path / "kho.env"
    kho.write_text(
        "EBM_API_CLAUDE_TRAN_USD_THANG=5\nEBM_API_CLAUDE_TRAN_USD_THANG=7,5\n", encoding="utf-8", newline="\n"
    )
    monkeypatch.delenv("EBM_API_CLAUDE_TRAN_USD_THANG", raising=False)
    assert API.tran_usd_thang_nguon(str(kho)) == (7.5, "kho bí mật")  # dòng cuối thắng
    monkeypatch.setenv("EBM_API_CLAUDE_TRAN_USD_THANG", "3")
    assert API.tran_usd_thang_nguon(str(kho)) == (3.0, "biến môi trường")  # biến môi trường đè kho
    monkeypatch.delenv("EBM_API_CLAUDE_TRAN_USD_THANG")
    assert API.tran_usd_thang_nguon(str(tmp_path / "khong-co.env")) == (API.TRAN_USD_THANG_MAC_DINH, "mặc định")


def test_tran_khong_doc_kho_that_duoi_pytest(monkeypatch):
    monkeypatch.delenv("EBM_API_CLAUDE_TRAN_USD_THANG", raising=False)
    monkeypatch.delenv("EBM_KIEM_API_THAT", raising=False)
    assert API.tran_usd_thang_nguon() == (API.TRAN_USD_THANG_MAC_DINH, "mặc định")
