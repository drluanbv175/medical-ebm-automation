"""Tối ưu chi phí Claude API (21/11/2026 — bác sĩ: «Claude API hãy xử lí để tối ưu cho tôi»).

Đo sổ chi phí 20–21/11: kiểm trích dẫn toàn văn + kiểm nội dung trích dẫn (gọi thường, độc lập từng lô) ≈ 38% chi phí;
Batch API giảm 50% mọi token. Chế độ `--batch` phải cho KẾT QUẢ NHƯ GỌI THƯỜNG: cùng tham số, và yêu cầu nào batch trả
lỗi / bị từ chối / cụt / JSON hỏng / bị huỷ vì quá giờ thì gửi lại thường (có dự phòng khi từ chối).
Sổ chi phí cộng dồn theo công cụ cả tháng (trước chỉ giữ 200 lượt ⇒ hồ sơ chi phí chỉ phủ ~1/3 tháng).
Không gọi mạng: mọi khách API là khách giả; sổ chi phí là tệp tạm.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO = Path(__file__).resolve().parents[1]
for _d in (REPO, REPO / "tools"):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

import api_claude_nc as API  # noqa: E402
import kiem_noi_dung_trich_dan as KND  # noqa: E402
import kiem_trich_dan_toan_van as K  # noqa: E402

from tests.test_api_claude_nghien_cuu_20261117 import ABS, _goc_tam, _tra_knd  # noqa: E402
from tests.test_kiem_trich_dan_toan_van_20261121 import POLIT, S, _goc, _xml  # noqa: E402

MODEL = "claude-sonnet-5-5"


@pytest.fixture
def so(tmp_path, monkeypatch):
    duong = tmp_path / "so-chi-phi.json"
    monkeypatch.setattr(API, "SO_CHI_PHI", str(duong))
    monkeypatch.delenv("EBM_API_CLAUDE_TRAN_USD_THANG", raising=False)
    return duong


def _resp(text, stop="end_turn"):
    return SimpleNamespace(content=[SimpleNamespace(text=text)], stop_reason=stop, model=MODEL, stop_details=None,
                           usage=SimpleNamespace(input_tokens=1000, output_tokens=100))


class _Dong:
    """Gọi THƯỜNG (beta.messages.create có dự phòng) — ghi lại từng lượt."""

    def __init__(self, tra):
        self.tra, self.goi = tra, []

    def create(self, **kw):
        self.goi.append(kw)
        return _resp(self.tra(kw))


class KhachLo:
    """Khách giả có CẢ Batch lẫn gọi thường. Batch dựng câu trả lời bằng `tra(params)`; `loi[custom_id]` giả hỏng
    riêng yêu cầu đó: refusal · cut (max_tokens) · errored · json (JSON hỏng) · mat (không có kết quả)."""

    def __init__(self, tra, loi=None, lan_dang_xu_ly=0):
        self.tra, self.loi = tra, dict(loi or {})
        self.dong = _Dong(tra)
        self.lo, self.huy, self.hoi, self.lan_dang_xu_ly = {}, [], 0, lan_dang_xu_ly
        self.messages = SimpleNamespace(create=self.dong.create, batches=self)
        self.beta = SimpleNamespace(messages=self.dong)

    def create(self, requests):
        bid = f"msgbatch_{len(self.lo)}"
        self.lo[bid] = list(requests)
        return SimpleNamespace(id=bid)

    def retrieve(self, bid):
        self.hoi += 1
        xong = bid in self.huy or self.hoi > self.lan_dang_xu_ly
        return SimpleNamespace(processing_status="ended" if xong else "in_progress",
                               request_counts=SimpleNamespace(processing=0, succeeded=1, errored=0, expired=0,
                                                              canceled=0))

    def cancel(self, bid):
        self.huy.append(bid)

    def results(self, bid):
        for r in self.lo[bid]:
            cid, p = r["custom_id"], r["params"]
            kieu = self.loi.get(cid)
            if kieu == "mat":
                continue
            if kieu == "errored":
                yield SimpleNamespace(custom_id=cid, result=SimpleNamespace(
                    type="errored", error=SimpleNamespace(type="overloaded_error")))
                continue
            text = "không phải json" if kieu == "json" else self.tra(p)
            stop = {"refusal": "refusal", "cut": "max_tokens"}.get(kieu, "end_turn")
            msg = SimpleNamespace(stop_reason=stop, stop_details=None, model=MODEL,
                                  content=[SimpleNamespace(text=text)],
                                  usage=SimpleNamespace(input_tokens=1000, output_tokens=200))
            yield SimpleNamespace(custom_id=cid, result=SimpleNamespace(type="succeeded", message=msg))


def _p(noi="x"):
    return API.tham_so(noi, he_thong="hệ thống", model=MODEL, effort="low")


# ── goi_lo / cho_batch / sổ theo nguồn ────────────────────────────────────────────────────────────────────────────
def test_goi_lo_tra_tung_yeu_cau_va_ghi_mot_lan_gia_batch(so):
    kh = KhachLo(lambda p: '{"ok": 1}', loi={"b": "refusal", "c": "cut", "d": "errored", "e": "mat"})
    ra = API.goi_lo([(c, _p()) for c in "abcde"], client=kh, nguon="thu_batch", ngu=lambda s: None)
    assert isinstance(ra["a"], API.KetQuaGoi) and ra["a"].van_ban == '{"ok": 1}' and ra["a"].token_vao == 1000
    assert all(isinstance(ra[c], API.KetQuaHong) for c in "bcde")
    assert kh.dong.goi == []  # goi_lo KHÔNG tự gửi thường — việc của công cụ
    d = json.loads(so.read_text(encoding="utf-8"))
    luot = [x for x in d["luot"] if x["nguon"] == "thu_batch"]
    assert len(luot) == 1 and luot[0]["batch"] == "msgbatch_0"
    # 3 kết quả «succeeded» (a, b từ chối, c cụt) vẫn tính phí: 3000 vào × 1 USD/MTok + 600 ra × 5 USD/MTok (giá Batch)
    assert luot[0]["usd"] == pytest.approx(0.003 + 0.003)
    g = d["theo_nguon_thang"]["thu_batch"]
    assert g["luot_batch"] == 1 and g["vao"] == 3000 and g["ra"] == 600


def test_goi_lo_khong_noi_khi_vuot_tran(so, monkeypatch):
    monkeypatch.setenv("EBM_API_CLAUDE_TRAN_USD_THANG", "0.00001")
    kh = KhachLo(lambda p: "{}")
    with pytest.raises(API.HetNganSach):
        API.goi_lo([("a", _p())], client=kh, nguon="thu_batch", ngu=lambda s: None)
    assert kh.lo == {}


def test_cho_batch_qua_gio_thi_huy_roi_doc_phan_da_xong():
    kh = KhachLo(lambda p: "{}", lan_dang_xu_ly=10**6)
    gio = {"t": 0.0}

    def ngu(s):
        gio["t"] += s

    API.nop_batch([("a", _p())], kh)
    tt = API.cho_batch("msgbatch_0", kh, cho_toi_da=60, chu_ky=20, ngu=ngu, dong_ho=lambda: gio["t"])
    assert tt["het_gio"] is True and kh.huy == ["msgbatch_0"]  # huỷ đúng một lần, rồi đọc phần đã xong


def test_cho_batch_xong_som_khong_huy():
    kh = KhachLo(lambda p: "{}", lan_dang_xu_ly=2)
    API.nop_batch([("a", _p())], kh)
    tt = API.cho_batch("msgbatch_0", kh, cho_toi_da=60, chu_ky=20, ngu=lambda s: None, dong_ho=lambda: 0.0)
    assert tt["het_gio"] is False and kh.huy == [] and kh.hoi == 3


def test_so_chi_phi_cong_don_theo_nguon_ca_thang(so):
    API.ghi_chi_phi(0.01, "kiem_a", MODEL, {"vao": 100, "ra": 10, "cache_doc": 50})
    API.ghi_chi_phi(0.02, "kiem_a", MODEL, {"vao": 200, "ra": 20}, batch_id="msgbatch_x")
    API.ghi_chi_phi(0.5, "kiem_b", MODEL, {"vao": 1})
    d = json.loads(so.read_text(encoding="utf-8"))
    a = d["theo_nguon_thang"]["kiem_a"]
    assert a == {"usd": pytest.approx(0.03), "luot": 2, "luot_batch": 1, "vao": 300, "ra": 30, "cache_ghi": 0,
                 "cache_doc": 50}
    assert d["theo_nguon_thang"]["kiem_b"]["luot"] == 1


# ── kiem_trich_dan_toan_van --batch ───────────────────────────────────────────────────────────────────────────────
DOC2 = ("Patterns of intra-cluster correlation from primary care research. Adams G. J Clin Epidemiol 2004. "
        + "Background about cluster randomised trials in general practice. " * 50
        + "Most intra-cluster correlation coefficients were below 0.05 for process and outcome measures. "
        + "Further discussion of design effects. " * 30)


def _tra_tv(p):
    nd = p["messages"][0]["content"]
    if "TÀI LIỆU [2]" in nd:
        return json.dumps({"ket_qua": [{"id": "C002", "so": 2, "muc": "ho_tro", "ly_do": "có ở toàn văn",
                                        "trich": "intra-cluster correlation coefficients were below 0.05"}]})
    return json.dumps({"ket_qua": [{"id": "C001", "so": 1, "muc": "ho_tro", "ly_do": "có ở toàn văn",
                                    "trich": "an S-CVI/Ave of .90 or higher"}]})


def _goc_hai(tmp_path):
    cap = [{"id": "C001", "so": 1, "muc": "ho_tro_mot_phan", "ly_do": "", "trich": "", "co": []},
           {"id": "C002", "so": 2, "muc": "ho_tro_mot_phan", "ly_do": "", "trich": "", "co": []}]
    goc = _goc(tmp_path, cap=cap)
    _xml(goc, "17654487", POLIT)
    _xml(goc, "15485730", DOC2)
    return goc


def test_toan_van_batch_chi_gui_thuong_tai_lieu_bi_tu_choi(tmp_path, so):
    goc = _goc_hai(tmp_path)
    kh = KhachLo(_tra_tv, loi={"tl_0002": "refusal"})
    assert K.main(["--study", S, "--goi-api", "--batch"], client=kh, goc=goc, es=None) == 0
    assert len(kh.lo["msgbatch_0"]) == 2
    assert len(kh.dong.goi) == 1 and "TÀI LIỆU [2]" in kh.dong.goi[0]["messages"][0]["content"]
    bc = json.loads((goc / "exports" / S / "kiem_may_api" / f"A12_TOAN_VAN_{S}.json").read_text(encoding="utf-8"))
    assert bc["so_ho_tro"] == 2 and bc["token_batch"] == {"vao": 1000, "ra": 200} and bc["token"]["vao"] == 1000
    gia_thuong = API.uoc_chi_phi(1000, 100, MODEL)
    assert bc["usd"] == pytest.approx(gia_thuong + API.uoc_chi_phi(1000, 200, MODEL, batch=True))


def test_toan_van_tham_so_batch_trung_luot_goi_thuong(tmp_path, so):
    """Cùng lời nhắn, lời dặn, model, effort, max_tokens — Batch chỉ khác giá, không khác thứ model được hỏi."""
    goc = _goc_hai(tmp_path)
    kh = KhachLo(_tra_tv, loi={"tl_0001": "json", "tl_0002": "json"})  # ép gửi thường cả hai để so tham số
    assert K.main(["--study", S, "--goi-api", "--batch"], client=kh, goc=goc, es=None) == 0
    for r, g in zip(kh.lo["msgbatch_0"], kh.dong.goi):
        p = r["params"]
        assert {k: g[k] for k in p} == p  # gọi thường = tham số batch + dự phòng (betas/fallbacks)
        assert g.get("fallbacks") == "default" and "fallbacks" not in p


def test_toan_van_khong_batch_giu_nguyen_goi_thuong(tmp_path, so):
    goc = _goc_hai(tmp_path)
    kh = KhachLo(_tra_tv)
    assert K.main(["--study", S, "--goi-api"], client=kh, goc=goc, es=None) == 0
    assert kh.lo == {} and len(kh.dong.goi) == 2


# ── kiem_noi_dung_trich_dan --batch ───────────────────────────────────────────────────────────────────────────────
def test_noi_dung_batch_lo_hong_gui_lai_thuong(tmp_path, so):
    goc = _goc_tam(tmp_path)
    kh = KhachLo(_tra_knd, loi={"lo_0001": "json"})
    KND.main(["--study", "S1", "--goi-api", "--lo", "1", "--batch"], client=kh, lay=lambda p: ABS, goc=goc)
    so_lo = len(kh.lo["msgbatch_0"])
    assert so_lo >= 2
    assert len(kh.dong.goi) == 1  # chỉ lô hỏng được gửi lại thường
    assert kh.dong.goi[0]["messages"] == kh.lo["msgbatch_0"][1]["params"]["messages"]
    md = (goc / "exports" / "S1" / "kiem_may_api" / "A12_KIEM_NOI_DUNG_S1.md").read_text(encoding="utf-8")
    assert f"Batch (−50%): {so_lo - 1}/{so_lo} lô dùng được" in md


def test_noi_dung_ket_qua_batch_bang_goi_thuong(tmp_path, so):
    goc_a, goc_b = _goc_tam(tmp_path / "a"), _goc_tam(tmp_path / "b")
    KND.main(["--study", "S1", "--goi-api", "--lo", "1", "--batch"], client=KhachLo(_tra_knd), lay=lambda p: ABS,
             goc=goc_a)
    KND.main(["--study", "S1", "--goi-api", "--lo", "1"], client=KhachLo(_tra_knd), lay=lambda p: ABS, goc=goc_b)

    def ket(g):
        d = json.loads((g / "exports" / "S1" / "kiem_may_api" / "A12_KIEM_NOI_DUNG_S1.json").read_text(
            encoding="utf-8"))
        return [(k["id"], k["so"], k["muc"]) for k in d["ket_qua"]]

    assert ket(goc_a) == ket(goc_b) and ket(goc_a)


def test_noi_dung_qua_gio_cho_batch_huy_roi_gui_thuong_du(tmp_path, so, monkeypatch):
    """Cơ chế API khi cần giới hạn lệnh con 1.800 giây ⇒ `--cho-batch-toi-da`: quá giờ thì huỷ phần chưa xử lý (không
    tính phí) và gửi thường đủ mọi lô — không bỏ sót cặp nào."""
    monkeypatch.setattr(API, "CHU_KY_HOI_BATCH_GIAY", 0)
    goc_a, goc_b = _goc_tam(tmp_path / "a"), _goc_tam(tmp_path / "b")
    kh = KhachLo(_tra_knd, lan_dang_xu_ly=10**6, loi={f"lo_{i:04d}": "mat" for i in range(50)})
    KND.main(["--study", "S1", "--goi-api", "--lo", "1", "--batch", "--cho-batch-toi-da", "0"], client=kh,
             lay=lambda p: ABS, goc=goc_a)
    assert kh.huy == ["msgbatch_0"] and len(kh.dong.goi) == len(kh.lo["msgbatch_0"])
    KND.main(["--study", "S1", "--goi-api", "--lo", "1"], client=KhachLo(_tra_knd), lay=lambda p: ABS, goc=goc_b)

    def ket(g):
        d = json.loads((g / "exports" / "S1" / "kiem_may_api" / "A12_KIEM_NOI_DUNG_S1.json").read_text(
            encoding="utf-8"))
        return [(k["id"], k["so"], k["muc"]) for k in d["ket_qua"]]

    assert ket(goc_a) == ket(goc_b)
