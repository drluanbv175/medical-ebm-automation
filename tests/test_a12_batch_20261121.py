"""A12 qua Batch API — giảm 50% nhưng BẤT ĐỒNG BỘ (21/11/2026, bác sĩ: «merge, rồi làm luôn Batch API cho A12»).

VÌ SAO CÓ ĐƯỜNG NÀY. `kiem_noi_dung_trich_dan` là nguồn tốn token vào lớn nhất của hệ (Console 7 ngày tới
20/11/2026: Sonnet 5.5 13 Tr token vào, 12,7% đọc cache). Phần đầu vào KHÔNG cache được vì bản chất công việc: mỗi
abstract gửi đúng một lần. Batch API giảm 50% mọi khoản và cộng dồn với cache ⇒ đòn tiết kiệm lớn hơn cache cho
đúng đường này.

RỦI RO mà các test ở đây canh — đều là rủi ro TIỀN hoặc LIÊM CHÍNH, không phải tiện dụng:
1. Nộp hai lần ⇒ trả phí đôi. Sổ batch hỏng/không đọc được PHẢI chặn, không được coi là «chưa nộp».
2. Ghép kết quả của văn bản CŨ vào văn bản MỚI ⇒ báo cáo nói về những dòng không còn tồn tại. Canh bằng SHA-256
   của tệp và của lời dặn.
3. Tra lại abstract lúc lấy kết quả ⇒ báo cáo nói về tài liệu KHÁC với tài liệu model đã đọc. Phải dùng đúng
   abstract đã gửi, lưu trong sổ.
4. Lô thiếu/hỏng bị đọc thành «đúng hết». Phải thành «không kiểm được».
5. In giá gọi trực tiếp cho lượt batch ⇒ đọc sai số tiền (batch chỉ bằng 50%).

Không gọi mạng, không đọc khoá thật: khách API là khách giả.
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

VAN = """# Đề cương

## Kết quả

Tỷ lệ hài lòng chung đạt 87,5% trong nghiên cứu trước [1]. Can thiệp giáo dục cải thiện tuân thủ [2].

## TÀI LIỆU THAM KHẢO

1. Tac Gia A. Nghien cuu mot. PMID: 11111111.
2. Tac Gia B. Nghien cuu hai. PMID: 22222222.
"""

# `lay` của A12 nhận DANH SÁCH PMID (chuỗi) và trả {pmid: bản ghi}; `status` phải là "resolved" mới dùng được.
BAN_GHI_PUBMED = {
    "11111111": {
        "status": "resolved",
        "title": "Nghien cuu mot",
        "publication_types": ["Journal Article"],
        "abstract": "Overall satisfaction reached 87,5% among outpatients in this cross-sectional survey.",
    },
    "22222222": {
        "status": "resolved",
        "title": "Nghien cuu hai",
        "publication_types": ["Randomized Controlled Trial"],
        "abstract": "An educational intervention improved adherence compared with usual care.",
    },
}


def _lay_pubmed(pmids):
    return {p: BAN_GHI_PUBMED[p] for p in pmids if p in BAN_GHI_PUBMED}


@pytest.fixture
def so(tmp_path, monkeypatch):
    """Sổ chi phí tạm — không đụng sổ thật của bác sĩ."""
    monkeypatch.setattr(API, "SO_CHI_PHI", str(tmp_path / "so-chi-phi.json"))
    monkeypatch.delenv("EBM_API_CLAUDE_TRAN_USD_THANG", raising=False)
    return tmp_path


@pytest.fixture
def goc(tmp_path):
    """Cây repo giả có đúng tệp đề cương mà A12 đi tìm."""
    d = tmp_path / "goc"
    (d / "exports" / "ST1").mkdir(parents=True)
    (d / "exports" / "ST1" / "DE_CUONG_NOP_HOI_DONG_ST1.md").write_text(VAN, encoding="utf-8", newline="\n")
    return d


# Đoạn khẳng định của VAN — tính một lần, dùng cho khách giả (trả kết quả cho MỌI đoạn; mục dư vô hại vì
# `kiem_tra_tra_loi` tra theo (id đoạn, số tài liệu)).
CAU_DS = KND.tach_cau_khang_dinh(VAN)


def _tra_loi_dung(cau_ds):
    """JSON đúng khuôn A12 — `so` là SỐ THỨ TỰ trong danh mục TLTK (1, 2), không phải PMID.

    Trích phải là NGUYÊN VĂN có trong abstract, nếu không máy sẽ hạ xuống «can_xem» (đúng thiết kế của A12)."""
    trich = {
        1: "Overall satisfaction reached 87,5%",
        2: "An educational intervention improved adherence",
    }
    return {
        "ket_qua": [
            {
                "id": c.id,
                "tham_chieu": [
                    {"so": n, "muc": "ho_tro", "ly_do": "khớp", "trich": trich.get(n, "")} for n in c.so
                ],
            }
            for c in cau_ds
        ]
    }


class KhachBatchA12:
    """Batch giả cho A12: nộp ⇒ id; retrieve ⇒ trạng thái; results ⇒ JSON đúng khuôn A12.

    `chua_xong=True` mô phỏng batch còn đang chạy. `thieu` = custom_id KHÔNG trả kết quả. `hong` = trả JSON hỏng.
    """

    def __init__(self, *, chua_xong=False, thieu=(), hong=()):
        self.lo = {}
        self.chua_xong = chua_xong
        self.thieu, self.hong = set(thieu), set(hong)
        self.tham_so = {}
        self.messages = SimpleNamespace(batches=self)
        self.batches = self

    def create(self, requests):
        bid = f"msgbatch_a12_{len(self.lo)}"
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
                processing=n if self.chua_xong else 0,
                succeeded=0 if self.chua_xong else n,
                errored=0,
                expired=0,
                canceled=0,
            ),
        )

    def results(self, bid):
        for cid in self.lo[bid]:
            if cid in self.thieu:
                continue
            text = "khong phai json" if cid in self.hong else json.dumps(_tra_loi_dung(CAU_DS), ensure_ascii=False)
            yield SimpleNamespace(
                custom_id=cid,
                result=SimpleNamespace(
                    type="succeeded",
                    message=SimpleNamespace(
                        content=[SimpleNamespace(text=text)],
                        stop_reason="end_turn",
                        model="claude-sonnet-5-5",
                        stop_details=None,
                        usage=SimpleNamespace(
                            input_tokens=500,
                            output_tokens=80,
                            cache_creation_input_tokens=591 if cid.endswith("0000") else 0,
                            cache_read_input_tokens=0 if cid.endswith("0000") else 591,
                        ),
                    ),
                ),
            )


def _lay(kh, goc, *co_them):
    return KND.main(
        ["--study", "ST1", "--goi-api", "--batch", *co_them], client=kh, goc=goc, lay=_lay_pubmed
    )


# ── 1. Chạy khô phải báo đúng giá Batch ──────────────────────────────────────────────────────────────────────────
def test_chay_kho_batch_bao_gia_mot_nua(goc, capsys):
    ma = KND.main(["--study", "ST1", "--batch", "--json"], goc=goc)
    assert ma == 0
    kh = json.loads(capsys.readouterr().out)
    assert kh["duong"] == "batch"
    thuong = json.loads(
        (lambda: (KND.main(["--study", "ST1", "--json"], goc=goc), capsys.readouterr().out)[1])()
    )
    assert thuong["duong"] == "goi_truc_tiep"
    # Batch = 50% mọi khoản ⇒ ước phải bằng đúng một nửa.
    assert kh["uoc_usd"] == pytest.approx(thuong["uoc_usd"] / 2)


# ── 2. Nộp ───────────────────────────────────────────────────────────────────────────────────────────────────────
def test_nop_ghi_so_va_tra_ma_4(goc, so, capsys):
    kh = KhachBatchA12()
    assert _lay(kh, goc) == 4  # 4 = chưa có kết quả
    out = capsys.readouterr().out
    assert "Đã nộp batch" in out and "giảm 50%" in out
    st = json.loads((goc / "exports" / "ST1" / "kiem_may_api" / "A12_batch_ST1.json").read_text(encoding="utf-8"))
    assert st["cong_cu"] == "kiem_noi_dung_trich_dan"
    assert st["batch"]["id"].startswith("msgbatch_a12_")
    assert st["tep_sha256"] == KND._bam(VAN)


def test_nop_luu_dung_abstract_da_gui(goc, so):
    """Sổ phải giữ abstract ĐÃ GỬI — nếu tra lại lúc lấy kết quả, báo cáo có thể nói về tài liệu khác."""
    kh = KhachBatchA12()
    _lay(kh, goc)
    st = json.loads((goc / "exports" / "ST1" / "kiem_may_api" / "A12_batch_ST1.json").read_text(encoding="utf-8"))
    assert set(st["tai_lieu"]) == {"1", "2"}  # khoá = SỐ THỨ TỰ trong danh mục TLTK
    assert "87,5%" in st["tai_lieu"]["1"]["abstract"]


def test_nop_co_danh_dau_cache_he_thong(goc, so):
    """Batch vẫn phải đánh dấu cache: 50% của Batch CỘNG DỒN với cache, không loại trừ nhau."""
    kh = KhachBatchA12()
    _lay(kh, goc)
    p = next(iter(kh.tham_so.values()))
    assert p["system"][0]["cache_control"] == {"type": "ephemeral"}


def test_khong_nop_khi_da_co_batch_cho(goc, so, capsys):
    """Nộp lần hai là TRẢ PHÍ ĐÔI — đã có batch chờ thì phải đi đường lấy kết quả."""
    kh = KhachBatchA12(chua_xong=True)
    assert _lay(kh, goc) == 4
    so_batch_truoc = len(kh.lo)
    assert _lay(kh, goc) == 4  # lượt hai: KHÔNG nộp thêm
    assert len(kh.lo) == so_batch_truoc
    assert "đang xử lý" in capsys.readouterr().out


# ── 3. Lấy kết quả ───────────────────────────────────────────────────────────────────────────────────────────────
def test_lay_ket_qua_sinh_bao_cao_va_xoa_so(goc, so):
    kh = KhachBatchA12()
    assert _lay(kh, goc) == 4
    kh.chua_xong = False
    assert _lay(kh, goc, "--chi-lay") == 0
    ra = goc / "exports" / "ST1" / "kiem_may_api"
    assert (ra / "A12_KIEM_NOI_DUNG_ST1.md").is_file()
    # Sổ phải bị xoá, nếu không lượt sau sẽ đọc là «còn batch chờ» và không bao giờ nộp được nữa.
    assert not (ra / "A12_batch_ST1.json").exists()


def test_bao_cao_ghi_ro_la_gia_batch(goc, so):
    kh = KhachBatchA12()
    _lay(kh, goc)
    _lay(kh, goc, "--chi-lay")
    md = (goc / "exports" / "ST1" / "kiem_may_api" / "A12_KIEM_NOI_DUNG_ST1.md").read_text(encoding="utf-8")
    assert "Batch API" in md
    assert "msgbatch_a12_0" in md


def test_chua_xong_tra_ma_4_va_giu_so(goc, so):
    kh = KhachBatchA12(chua_xong=True)
    _lay(kh, goc)
    assert _lay(kh, goc, "--chi-lay") == 4
    assert (goc / "exports" / "ST1" / "kiem_may_api" / "A12_batch_ST1.json").is_file()


def test_chi_lay_khi_khong_co_batch_thi_khong_nop(goc, so, capsys):
    kh = KhachBatchA12()
    assert _lay(kh, goc, "--chi-lay") == 0
    assert kh.lo == {}  # KHÔNG nộp gì
    assert "không nộp gì" in capsys.readouterr().out


# ── 4. Canh liêm chính ───────────────────────────────────────────────────────────────────────────────────────────
def test_tep_doi_sau_khi_nop_thi_tu_choi_ghep(goc, so, capsys):
    """Ghép kết quả của văn bản cũ vào văn bản mới ⇒ báo cáo nói về dòng không còn tồn tại. Phải TỪ CHỐI."""
    kh = KhachBatchA12()
    _lay(kh, goc)
    tep = goc / "exports" / "ST1" / "DE_CUONG_NOP_HOI_DONG_ST1.md"
    tep.write_text(VAN.replace("87,5%", "91,2%"), encoding="utf-8", newline="\n")
    assert _lay(kh, goc, "--chi-lay") == 3
    assert "đã ĐỔI sau khi nộp batch" in capsys.readouterr().out


def test_loi_dan_doi_sau_khi_nop_thi_tu_choi(goc, so, monkeypatch, capsys):
    kh = KhachBatchA12()
    _lay(kh, goc)
    monkeypatch.setattr(KND, "HE_THONG", KND.HE_THONG + " thêm một câu dặn mới")
    assert _lay(kh, goc, "--chi-lay") == 3
    assert "HE_THONG) đã đổi" in capsys.readouterr().out


def test_so_batch_hong_thi_chan_chu_khong_nop_lai(goc, so, capsys):
    """Sổ hỏng có thể đang che một batch ĐÃ TRẢ PHÍ — coi là «chưa nộp» rồi nộp lại là trả phí đôi."""
    ra = goc / "exports" / "ST1" / "kiem_may_api"
    ra.mkdir(parents=True)
    (ra / "A12_batch_ST1.json").write_text("{khong phai json", encoding="utf-8", newline="\n")
    kh = KhachBatchA12()
    assert _lay(kh, goc) == 3
    assert kh.lo == {}  # KHÔNG nộp
    assert "không đọc được" in capsys.readouterr().out


def _doc_bao_cao(goc):
    return json.loads(
        (goc / "exports" / "ST1" / "kiem_may_api" / "A12_KIEM_NOI_DUNG_ST1.json").read_text(encoding="utf-8")
    )


def test_lo_thieu_ket_qua_thanh_khong_kiem_duoc(goc, so):
    """Batch trả thiếu lô ⇒ KHÔNG được đọc thành «đúng hết».

    Tài liệu thử chỉ sinh MỘT lô, nên lô đó thiếu = TOÀN BỘ lô hỏng ⇒ mã 2 (đúng luật `het_loi` sẵn có của công cụ:
    không kiểm được lô nào thì không được trả mã thành công)."""
    kh = KhachBatchA12()
    _lay(kh, goc)
    kh.thieu = {"a12_lo_0000"}
    assert _lay(kh, goc, "--chi-lay") == 2
    dl = _doc_bao_cao(goc)
    assert [k["muc"] for k in dl["ket_qua"]] == ["khong_kiem_duoc"] * len(dl["ket_qua"])
    assert any("không trả kết quả" in x for x in dl["loi"])


def test_lo_json_hong_thanh_khong_kiem_duoc_khong_im_lang(goc, so):
    """Batch không gửi lại được trong cùng lượt ⇒ phải ghi rõ lý do, không im lặng coi như đã kiểm."""
    kh = KhachBatchA12()
    _lay(kh, goc)
    kh.hong = {"a12_lo_0000"}
    assert _lay(kh, goc, "--chi-lay") == 2
    dl = _doc_bao_cao(goc)
    assert all(k["muc"] == "khong_kiem_duoc" for k in dl["ket_qua"])
    assert dl["loi"] and any("hỏng" in x or "JSON" in x for x in dl["loi"])


def test_lo_hong_khong_lam_hong_lo_khac(goc, so):
    """Nhiều lô: lô hỏng chỉ ảnh hưởng cặp CỦA NÓ, lô khác vẫn cho kết quả (và mã KHÔNG còn là 2)."""
    kh = KhachBatchA12()
    _lay(kh, goc, "--lo", "1")  # 1 đoạn/lô ⇒ 2 lô
    assert len(kh.lo["msgbatch_a12_0"]) == 2
    kh.hong = {"a12_lo_0000"}
    assert _lay(kh, goc, "--chi-lay") != 2  # không phải «hỏng hết»
    muc = [k["muc"] for k in _doc_bao_cao(goc)["ket_qua"]]
    assert "khong_kiem_duoc" in muc and any(m != "khong_kiem_duoc" for m in muc)


# ── 5. Cờ dòng lệnh ──────────────────────────────────────────────────────────────────────────────────────────────
def test_chi_lay_khong_dung_mot_minh(goc, capsys):
    assert KND.main(["--study", "ST1", "--goi-api", "--chi-lay"], goc=goc) == 3
    assert "chỉ dùng cùng --batch" in capsys.readouterr().out


def test_duong_dong_bo_khong_doi(goc, so):
    """Không có --batch thì vẫn đi đường gọi trực tiếp như trước — đây là tính năng OPT-IN."""
    from tests.test_api_claude_nghien_cuu_20261117 import KhachGia

    kh = KhachGia(lambda kw: SimpleNamespace(
        content=[SimpleNamespace(text=json.dumps(_tra_loi_dung(CAU_DS), ensure_ascii=False))],
        stop_reason="end_turn", model="claude-sonnet-5-5", stop_details=None,
        usage=SimpleNamespace(input_tokens=500, output_tokens=80),
    ))
    ma = KND.main(["--study", "ST1", "--goi-api"], client=kh, goc=goc, lay=_lay_pubmed)
    assert ma == 0
    assert not (goc / "exports" / "ST1" / "kiem_may_api" / "A12_batch_ST1.json").exists()
