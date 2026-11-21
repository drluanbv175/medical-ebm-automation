"""`kiem_trich_dan_toan_van` — bật cache + chạy qua Batch API (21/11/2026, bác sĩ: «làm cả a, b và c»).

VÌ SAO. Đo trên sổ chi phí THẬT của bác sĩ ngày 21/11/2026: công cụ này 88 lượt · **726 N token vào · 0% đọc
cache** — nguồn tốn thứ hai của hệ, và thiếu đúng một cờ `cache_he_thong=True`. Hai việc ở đây:

(a) Bật cache: `HE_THONG` = 816 token (trên ngưỡng 512) và gửi Y NGUYÊN cho MỖI tài liệu ⇒ hoà vốn ngay từ tài liệu
    thứ hai. Kèm theo: báo cáo trước đây chỉ đếm `vao`/`ra` nên không cho thấy cache có chạy hay không — nay đếm cả
    `cache_ghi`/`cache_doc` và tính tiền theo chúng.
(b) Batch API: phần LỚN của 726 N là ĐOẠN TOÀN VĂN của từng tài liệu, mỗi đoạn gửi đúng một lần ⇒ không cache nào
    tiết kiệm được. Batch giảm 50% mọi khoản và cộng dồn với cache.

Bốn chốt canh dưới đây đều là rủi ro TIỀN hoặc LIÊM CHÍNH, không phải tiện dụng — và chốt về «đoạn đã gửi» ở công
cụ này MẠNH hơn ở A12: đoạn do `tim_toan_van` dựng từ thư viện EndNote/PDF của bác sĩ rồi `doan_lien_quan` cắt theo
trần ký tự, nên dựng lại có thể ra đoạn KHÁC (thư viện đổi, trần đổi, PDF khác bản) ⇒ báo cáo sẽ nói về đoạn mà
model KHÔNG đọc.

Ngoại tuyến: khách API giả, EndNote giả, XML giả — không gọi mạng, không đọc khoá thật.
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
import kiem_trich_dan_toan_van as K  # noqa: E402

from tests.test_kiem_trich_dan_toan_van_20261121 import (  # noqa: E402
    POLIT,
    EndNoteGia,
    S,
    _goc,
    _xml,
)

TRA_LOI = {
    "ket_qua": [
        {"id": "C001", "so": 1, "muc": "ho_tro", "trich": "I-CVI of .78 or higher", "ly_do": "khớp"},
    ]
}


@pytest.fixture
def so(tmp_path, monkeypatch):
    """Sổ chi phí tạm — không đụng sổ thật của bác sĩ."""
    monkeypatch.setattr(API, "SO_CHI_PHI", str(tmp_path / "so-chi-phi.json"))
    monkeypatch.delenv("EBM_API_CLAUDE_TRAN_USD_THANG", raising=False)
    return tmp_path


class KhachBatchKTV:
    """Batch giả: nộp ⇒ id; retrieve ⇒ trạng thái; results ⇒ JSON đúng khuôn của công cụ này."""

    def __init__(self, *, chua_xong=False, thieu=(), hong=()):
        self.lo, self.tham_so = {}, {}
        self.chua_xong = chua_xong
        self.thieu, self.hong = set(thieu), set(hong)
        self.messages = SimpleNamespace(batches=self)
        self.batches = self

    def create(self, requests):
        bid = f"msgbatch_ktv_{len(self.lo)}"
        self.lo[bid] = [r["custom_id"] for r in requests]
        for r in requests:
            assert API._CUSTOM_ID.match(r["custom_id"]), r["custom_id"]
            self.tham_so[r["custom_id"]] = r["params"]
        return SimpleNamespace(id=bid)

    def retrieve(self, bid):
        n = len(self.lo[bid])
        return SimpleNamespace(
            processing_status="in_progress" if self.chua_xong else "ended",
            request_counts=SimpleNamespace(
                processing=n if self.chua_xong else 0, succeeded=0 if self.chua_xong else n,
                errored=0, expired=0, canceled=0,
            ),
        )

    def results(self, bid):
        for cid in self.lo[bid]:
            if cid in self.thieu:
                continue
            text = "khong phai json" if cid in self.hong else json.dumps(TRA_LOI, ensure_ascii=False)
            yield SimpleNamespace(
                custom_id=cid,
                result=SimpleNamespace(
                    type="succeeded",
                    message=SimpleNamespace(
                        content=[SimpleNamespace(text=text)], stop_reason="end_turn", model="claude-sonnet-5-5",
                        stop_details=None,
                        usage=SimpleNamespace(
                            input_tokens=900, output_tokens=120,
                            cache_creation_input_tokens=816 if cid.endswith("00001") else 0,
                            cache_read_input_tokens=0 if cid.endswith("00001") else 816,
                        ),
                    ),
                ),
            )


@pytest.fixture
def moi_truong(tmp_path):
    """Cây repo giả + một tài liệu CÓ toàn văn (PMID 17654487 qua XML)."""
    goc = _goc(tmp_path)
    _xml(goc, "17654487", POLIT)
    es = EndNoteGia(tmp_path)
    return goc, es


def _chay(goc, es, kh, *co_them):
    return K.main(["--study", S, "--goi-api", *co_them], client=kh, goc=goc, es=es)


def _so_batch(goc):
    return goc / "exports" / S / "kiem_may_api" / f"A12_TOAN_VAN_batch_{S}.json"


def _bao_cao(goc):
    return json.loads(
        (goc / "exports" / S / "kiem_may_api" / f"A12_TOAN_VAN_{S}.json").read_text(encoding="utf-8")
    )


# ── (a) Bật cache trên đường gọi trực tiếp ───────────────────────────────────────────────────────────────────────
def test_duong_goi_truc_tiep_danh_dau_cache(moi_truong, so):
    """Chốt cờ bị thiếu đã được bật — đây chính là lỗ 0% đọc cache đo được trên sổ thật."""
    from tests.test_kiem_trich_dan_toan_van_20261121 import KhachGia

    goc, es = moi_truong
    kh = KhachGia(json.dumps(TRA_LOI, ensure_ascii=False))
    _chay(goc, es, kh)
    assert kh.goi, "không gọi API lần nào"
    p = kh.goi[-1]
    assert p["system"][0]["cache_control"] == {"type": "ephemeral"}


def test_he_thong_du_nguong_512_nen_cache_moi_co_nghia():
    """Bật cache chỉ có nghĩa khi prompt vượt ngưỡng; dưới ngưỡng thì API lặng lẽ không cache."""
    n = API.uoc_token(K.HE_THONG)
    assert n >= API.NGUONG_CACHE_TOKEN["claude-sonnet-5-5"], f"HE_THONG chỉ {n} token"


def test_bao_cao_dem_token_cache(moi_truong, so):
    """Trước 21/11/2026 báo cáo chỉ có vao/ra nên không ai thấy cache có chạy hay không."""
    from tests.test_kiem_trich_dan_toan_van_20261121 import KhachGia

    goc, es = moi_truong
    _chay(goc, es, KhachGia(json.dumps(TRA_LOI, ensure_ascii=False)))
    tok = _bao_cao(goc)["token"]
    assert "cache_ghi" in tok and "cache_doc" in tok


# ── (b) Batch ────────────────────────────────────────────────────────────────────────────────────────────────────
def test_chay_kho_batch_bao_gia_mot_nua(moi_truong, capsys):
    goc, es = moi_truong
    assert K.main(["--study", S, "--batch", "--json"], goc=goc, es=es) == 0
    b = json.loads(capsys.readouterr().out)
    assert K.main(["--study", S, "--json"], goc=goc, es=es) == 0
    t = json.loads(capsys.readouterr().out)
    assert (b["duong"], t["duong"]) == ("batch", "goi_truc_tiep")
    assert b["uoc_usd"] == pytest.approx(t["uoc_usd"] / 2)


def test_nop_ghi_so_tra_ma_4_va_giu_dung_doan_da_gui(moi_truong, so, capsys):
    goc, es = moi_truong
    kh = KhachBatchKTV()
    assert _chay(goc, es, kh, "--batch") == 4
    assert "Đã nộp batch" in capsys.readouterr().out
    st = json.loads(_so_batch(goc).read_text(encoding="utf-8"))
    assert st["cong_cu"] == "kiem_trich_dan_toan_van"
    # Đoạn toàn văn ĐÃ GỬI phải nằm trong sổ — không dò lại EndNote/PDF lúc lấy kết quả
    assert st["co_van"]["1"]["doan"]
    assert "I-CVI of .78" in st["co_van"]["1"]["doan"]
    assert st["khong"] is not None


def test_nop_co_danh_dau_cache(moi_truong, so):
    """Batch vẫn phải đánh dấu cache: 50% của Batch CỘNG DỒN với cache, không loại trừ nhau."""
    goc, es = moi_truong
    kh = KhachBatchKTV()
    _chay(goc, es, kh, "--batch")
    p = next(iter(kh.tham_so.values()))
    assert p["system"][0]["cache_control"] == {"type": "ephemeral"}


def test_lay_ket_qua_sinh_bao_cao_xoa_so_va_ghi_ro_gia_batch(moi_truong, so):
    goc, es = moi_truong
    kh = KhachBatchKTV()
    _chay(goc, es, kh, "--batch")
    _chay(goc, es, kh, "--batch", "--chi-lay")
    bc = _bao_cao(goc)
    assert bc["duong"] == "batch"
    assert bc["batch_id"] == "msgbatch_ktv_0"
    assert not _so_batch(goc).exists()  # giữ lại sẽ bị đọc là «còn batch chờ»
    md = (goc / "exports" / S / "kiem_may_api" / f"A12_TOAN_VAN_{S}.md").read_text(encoding="utf-8")
    assert "Batch API" in md


def test_chua_xong_tra_ma_4_va_giu_so(moi_truong, so):
    goc, es = moi_truong
    kh = KhachBatchKTV(chua_xong=True)
    _chay(goc, es, kh, "--batch")
    assert _chay(goc, es, kh, "--batch", "--chi-lay") == 4
    assert _so_batch(goc).is_file()


def test_khong_nop_lan_hai_khi_da_co_batch_cho(moi_truong, so):
    """Nộp lần hai là TRẢ PHÍ ĐÔI."""
    goc, es = moi_truong
    kh = KhachBatchKTV(chua_xong=True)
    _chay(goc, es, kh, "--batch")
    assert len(kh.lo) == 1
    _chay(goc, es, kh, "--batch")
    assert len(kh.lo) == 1  # KHÔNG nộp thêm


def test_chi_lay_khi_khong_co_batch_thi_khong_nop(moi_truong, so, capsys):
    goc, es = moi_truong
    kh = KhachBatchKTV()
    assert _chay(goc, es, kh, "--batch", "--chi-lay") == 0
    assert kh.lo == {}
    assert "không nộp gì" in capsys.readouterr().out


# ── Canh liêm chính ──────────────────────────────────────────────────────────────────────────────────────────────
def test_tep_doi_sau_khi_nop_thi_tu_choi_ghep(moi_truong, so, capsys):
    goc, es = moi_truong
    kh = KhachBatchKTV()
    _chay(goc, es, kh, "--batch")
    tep = goc / "exports" / S / f"DE_CUONG_NOP_HOI_DONG_{S}.md"
    tep.write_text(tep.read_text(encoding="utf-8").replace("0,78", "0,88"), encoding="utf-8", newline="\n")
    ma = _chay(goc, es, kh, "--batch", "--chi-lay")
    out = capsys.readouterr().out
    # Tệp đổi ⇒ A12 cũ hết hiệu lực (mã 2) HOẶC chốt batch chặn (mã 3) — cả hai đều là TỪ CHỐI, không được ghép
    assert ma in (2, 3), out
    assert "đã ĐỔI sau khi nộp batch" in out or "không dùng được" in out


def test_loi_dan_doi_sau_khi_nop_thi_tu_choi(moi_truong, so, monkeypatch, capsys):
    goc, es = moi_truong
    kh = KhachBatchKTV()
    _chay(goc, es, kh, "--batch")
    monkeypatch.setattr(K, "HE_THONG", K.HE_THONG + " thêm một câu dặn mới")
    assert _chay(goc, es, kh, "--batch", "--chi-lay") == 3
    assert "HE_THONG) đã đổi" in capsys.readouterr().out


def test_so_batch_hong_thi_chan_chu_khong_nop_lai(moi_truong, so, capsys):
    """Sổ hỏng có thể đang che một batch ĐÃ TRẢ PHÍ."""
    goc, es = moi_truong
    _so_batch(goc).write_text("{khong phai json", encoding="utf-8", newline="\n")
    kh = KhachBatchKTV()
    assert _chay(goc, es, kh, "--batch") == 3
    assert kh.lo == {}
    assert "không đọc được" in capsys.readouterr().out


def test_tai_lieu_thieu_ket_qua_thanh_khong_xac_minh(moi_truong, so):
    """Batch trả thiếu tài liệu ⇒ KHÔNG được đọc thành «đúng hết»."""
    goc, es = moi_truong
    kh = KhachBatchKTV()
    _chay(goc, es, kh, "--batch")
    kh.thieu = {"ktv_tl_00001"}
    _chay(goc, es, kh, "--batch", "--chi-lay")
    bc = _bao_cao(goc)
    assert all(k["muc_toan_van"] == "khong_xac_minh" for k in bc["ket_qua"])
    assert bc["loi"]


def test_json_hong_thanh_khong_xac_minh_khong_im_lang(moi_truong, so):
    """Batch không gửi lại được trong cùng lượt ⇒ phải ghi rõ lý do."""
    goc, es = moi_truong
    kh = KhachBatchKTV()
    _chay(goc, es, kh, "--batch")
    kh.hong = {"ktv_tl_00001"}
    _chay(goc, es, kh, "--batch", "--chi-lay")
    bc = _bao_cao(goc)
    assert all(k["muc_toan_van"] == "khong_xac_minh" for k in bc["ket_qua"])
    assert bc["loi"]


def test_chi_lay_khong_dung_mot_minh(moi_truong, capsys):
    goc, es = moi_truong
    assert K.main(["--study", S, "--goi-api", "--chi-lay"], goc=goc, es=es) == 3
    assert "chỉ dùng cùng --batch" in capsys.readouterr().out
