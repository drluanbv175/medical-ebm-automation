"""Kết nối Claude API cho hệ nghiên cứu (17/11/2026): mô-đun dùng chung + ba công cụ tư vấn.

Không gọi API/NCBI thật: mọi lời gọi đi qua khách giả tiêm vào; dưới pytest mô-đun tự từ chối dựng khách thật, đọc kho
khoá thật hay ghi nhật ký sức khoẻ thật.
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
import hoi_dong_cong as HDC  # noqa: E402
import hoi_dong_cong_batch as HB  # noqa: E402
import kiem_noi_dung_trich_dan as KND  # noqa: E402
import phan_bien_may_de_cuong as PBM  # noqa: E402


# ── Khách giả ────────────────────────────────────────────────────────────────────────────────────────────────────
def _resp(text, stop="end_turn", model="claude-sonnet-5-5"):
    return SimpleNamespace(
        content=[SimpleNamespace(text=text)],
        stop_reason=stop,
        model=model,
        usage=SimpleNamespace(input_tokens=100, output_tokens=20),
        stop_details=None,
    )


class _Msgs:
    def __init__(self, tra):
        self.tra, self.goi = tra, []

    def create(self, **kw):
        self.goi.append(kw)
        r = self.tra(kw) if callable(self.tra) else self.tra
        return r if hasattr(r, "content") else _resp(r)


class KhachGia:
    def __init__(self, tra):
        self.messages = _Msgs(tra)
        self.beta = SimpleNamespace(messages=self.messages)


# ── Mô-đun dùng chung ────────────────────────────────────────────────────────────────────────────────────────────
def test_khoa_moi_truong_bi_bo_qua_duoi_pytest(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-gia")  # bimat-mien: khoá giả trong test
    monkeypatch.delenv("EBM_KIEM_API_THAT", raising=False)
    assert API.khoa_api() == ""


def test_khoa_tu_kho_tam_dong_cuoi_thang(tmp_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    kho = tmp_path / "kho.env"
    kho.write_text("ANTHROPIC_API_KEY=cu\n# ghi chú\nANTHROPIC_API_KEY='moi'\n", encoding="utf-8", newline="\n")
    assert API.khoa_api(kho=str(kho)) == "moi"


def test_khong_doc_kho_that_duoi_pytest(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("EBM_KIEM_API_THAT", raising=False)
    assert API.khoa_api(kho=API._KHO_THAT) == ""


def test_khong_dung_khach_that_duoi_pytest(monkeypatch):
    monkeypatch.delenv("EBM_KIEM_API_THAT", raising=False)
    with pytest.raises(API.LoiApi, match="pytest"):
        API.tao_client(None)


def test_goi_model_hien_hanh_qua_beta_du_phong():
    kh = KhachGia('{"a": 1}')
    kq = API.goi("x", he_thong="vai", client=kh, effort="medium")
    goi = kh.messages.goi[0]
    assert kq.van_ban == '{"a": 1}' and kq.token_vao == 100
    assert goi["fallbacks"] == "default" and goi["output_config"] == {"effort": "medium"} and goi["system"] == "vai"


def test_goi_model_khac_khong_them_tham_so_moi(monkeypatch):
    monkeypatch.setitem(API.GIA_USD_TRIEU_TOKEN, "claude-cu-1", {"vao": 1.0, "ra": 1.0})  # có giá ⇒ qua trần
    kh = KhachGia("ok")
    API.goi("x", model="claude-cu-1", client=kh)
    assert "output_config" not in kh.messages.goi[0] and "fallbacks" not in kh.messages.goi[0]


@pytest.mark.parametrize("stop", ["max_tokens", "refusal"])
def test_cat_cut_hay_tu_choi_la_hong(stop):
    with pytest.raises(API.KetQuaHong):
        API.goi("x", client=KhachGia(_resp('{"a":', stop=stop)))


def test_loi_sdk_thanh_loi_api():
    def no(kw):
        raise RuntimeError("401 khoá hỏng")

    with pytest.raises(API.LoiApi, match="RuntimeError"):
        API.goi("x", client=KhachGia(no))


def test_doc_json_chiu_rao_va_loi_binh():
    assert API.doc_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert API.doc_json('Đây: {"a": 2} — xong') == {"a": 2}
    with pytest.raises(API.KetQuaHong):
        API.doc_json("không có json")


def test_nhat_ky_khong_ghi_tep_that_duoi_pytest(tmp_path, monkeypatch):
    monkeypatch.delenv("EBM_KIEM_API_THAT", raising=False)
    goc = Path(API._NK_THAT)
    truoc = goc.read_bytes() if goc.is_file() else None
    API.ghi_nhat_ky_api("ok", "", 1, "kiem")
    assert (goc.read_bytes() if goc.is_file() else None) == truoc
    tam = tmp_path / "nk.json"
    API.ghi_nhat_ky_api("error", "x" * 500, 3, "kiem_noi_dung_trich_dan", tep=str(tam))
    d = json.loads(tam.read_text(encoding="utf-8"))
    assert d["trang_thai"] == "error" and len(d["ly_do"]) == 200 and d["nguon"] == "kiem_noi_dung_trich_dan"


def test_batch_tu_choi_custom_id_sai_hoac_trung():
    with pytest.raises(API.LoiApi):
        API.nop_batch([("có dấu", {})], client=object())
    with pytest.raises(API.LoiApi):
        API.nop_batch([("a1", {}), ("a1", {})], client=object())


def test_van_ban_ket_qua_batch_kiem_loai_va_stop():
    with pytest.raises(API.KetQuaHong):
        API.van_ban_ket_qua_batch({"loai": "errored", "loi": "overloaded"})
    with pytest.raises(API.KetQuaHong):
        API.van_ban_ket_qua_batch({"loai": "succeeded", "stop_reason": "max_tokens", "text": "{"})
    assert API.van_ban_ket_qua_batch({"loai": "succeeded", "stop_reason": "end_turn", "text": "ok"}) == "ok"


def test_co_nguyen_van_chuan_hoa():
    assert API.co_nguyen_van("prevalence  was 24.9%", "Overall, Prevalence was 24.9%.")
    assert not API.co_nguyen_van("prevalence was 30%", "Prevalence was 24.9%.")
    assert not API.co_nguyen_van("", "abc")


def test_chi_phi_chi_cho_model_da_ghi_gia():
    assert API.uoc_chi_phi(1_000_000, 0, "claude-sonnet-5-5", batch=True) == pytest.approx(1.0)
    assert API.uoc_chi_phi(1_000_000, 1_000_000, "claude-opus-5-5") == pytest.approx(24.0)
    assert API.uoc_chi_phi(1, 1, "claude-chua-co-gia") is None


# ── Kiểm nội dung trích dẫn ──────────────────────────────────────────────────────────────────────────────────────
DE_CUONG = """# ĐỀ CƯƠNG
# 1. ĐẶT VẤN ĐỀ
Bệnh thận mạn thường gặp ở người ĐTĐ típ 2 [1]. Xét nghiệm: chỉ 24,9% được làm UACR [2]; creatinin 84,8% [3].
| Tác giả [2] | 2025 | Tổng quan hệ thống |
Ba nghiên cứu cùng chiều [1–3].
# 7. TÀI LIỆU THAM KHẢO
1. Tac A. Bai mot. J. 2020. doi:10.1/a1. PMID: 1001.
2. Tac B. Bai hai. J. 2021. PMID: 1002.
3. Tac C. Bai ba. J. 2022.
"""

ABS = {
    "1001": {
        "status": "resolved",
        "title": "CKD in type 2 diabetes",
        "abstract": "Chronic kidney disease is common in people with type 2 diabetes.",
        "publication_types": ["Journal Article"],
    },
    "1002": {
        "status": "resolved",
        "title": "Testing gaps",
        "abstract": "RESULTS: Only 24.9% of patients had UACR testing.",
        "publication_types": ["Review"],
    },
}


def test_tach_tltk_va_cau():
    tl = KND.tach_tltk(DE_CUONG)
    assert tl[1].pmid == "1001" and tl[1].doi == "10.1/a1" and tl[3].pmid is None
    cau = KND.tach_cau_khang_dinh(DE_CUONG)
    assert [c.so for c in cau] == [[1], [2], [3], [2], [1, 2, 3]]
    assert cau[1].doan.startswith("Xét nghiệm") and "84,8" not in cau[1].doan  # số của [3] không lẫn sang [2]
    assert cau[2].doan.startswith("creatinin")
    assert all("TÀI LIỆU" not in c.vi_tri for c in cau)


def test_mo_rong_dau_va_so_lieu():
    assert KND.mo_rong_dau("5–7, 9") == [5, 6, 7, 9]
    assert KND.mo_rong_dau("9-2") == [9, 2]
    assert KND.so_lieu("chỉ 24,9% và 3,5 mg [2]") == ["24.9", "3.5"]
    assert KND.so_co_trong("24.9", "Only 24.9% had") and not KND.so_co_trong("4.9", "Only 24.9% had")


def _lo_test():
    tl = KND.tach_tltk(DE_CUONG)
    cau = KND.tach_cau_khang_dinh(DE_CUONG)
    tai_lieu = {n: {**ABS[t.pmid], "pmid": t.pmid} for n, t in tl.items() if t.pmid in ABS}
    return tl, cau, tai_lieu


def test_may_ha_muc_khi_trich_khong_co_nguyen_van():
    _, cau, tl = _lo_test()
    dl = {
        "ket_qua": [
            {"id": "C001", "tham_chieu": [{"so": 1, "muc": "ho_tro", "trich": "CKD affects everyone", "ly_do": "x"}]}
        ]
    }
    k = KND.kiem_tra_tra_loi([cau[0]], dl, tl)[0]
    assert k.muc == "can_xem" and "can_cu_khong_khop" in k.co


def test_may_co_so_lieu_khong_thay():
    _, cau, tl = _lo_test()
    c = KND.Cau("C9", "x", "Tỷ lệ 31,2% [2]", "Tỷ lệ 31,2% [2]", [2])
    dl = {
        "ket_qua": [
            {"id": "C9", "tham_chieu": [{"so": 2, "muc": "ho_tro", "trich": "Only 24.9% of patients", "ly_do": "x"}]}
        ]
    }
    k = KND.kiem_tra_tra_loi([c], dl, tl)[0]
    assert k.muc == "ho_tro" and k.co == ["so_khong_thay:31.2"] and KND.can_xem(k)


def test_cap_thieu_hay_muc_la_la_khong_kiem_duoc():
    _, cau, tl = _lo_test()
    ks = KND.kiem_tra_tra_loi(
        [cau[0], cau[1]], {"ket_qua": [{"id": "C002", "tham_chieu": [{"so": 2, "muc": "dung_roi", "trich": ""}]}]}, tl
    )
    assert [k.muc for k in ks] == ["khong_kiem_duoc", "khong_kiem_duoc"]


def _goc_tam(tmp_path, van=DE_CUONG, ma="S1"):
    d = tmp_path / "exports" / ma
    d.mkdir(parents=True)
    (d / f"DE_CUONG_NOP_HOI_DONG_{ma}.md").write_text(van, encoding="utf-8", newline="\n")
    return tmp_path


def test_kiem_trich_dan_chay_kho_khong_mang_khong_ghi(tmp_path, capsys):
    goc = _goc_tam(tmp_path)

    def cam(_):
        raise AssertionError("chạy khô không được gọi mạng")

    assert KND.main(["--study", "S1"], client=object(), lay=cam, goc=goc) == 0
    assert not (goc / "exports" / "S1" / "kiem_may_api").exists()
    assert "CHẠY KHÔ" in capsys.readouterr().out


def _tra_knd(kw):
    nd = kw["messages"][0]["content"]
    cau = json.loads(nd.split("CÂU KHẲNG ĐỊNH CẦN KIỂM:\n", 1)[1])
    ra = []
    for c in cau:
        tc = []
        for n in c["giao_tham_chieu"]:
            tc.append(
                {"so": n, "muc": "ho_tro", "trich": "Chronic kidney disease is common", "ly_do": "khớp"}
                if n == 1
                else {"so": n, "muc": "ho_tro", "trich": "Only 24.9% of patients had UACR testing", "ly_do": "khớp"}
            )
        ra.append({"id": c["id"], "tham_chieu": tc})
    return json.dumps({"ket_qua": ra})


def test_kiem_trich_dan_goi_api_ghi_bao_cao(tmp_path):
    goc = _goc_tam(tmp_path)
    ma = KND.main(["--study", "S1", "--goi-api"], client=KhachGia(_tra_knd), lay=lambda p: ABS, goc=goc)
    md = (goc / "exports" / "S1" / "kiem_may_api" / "A12_KIEM_NOI_DUNG_S1.md").read_text(encoding="utf-8")
    js = json.loads((goc / "exports" / "S1" / "kiem_may_api" / "A12_KIEM_NOI_DUNG_S1.json").read_text(encoding="utf-8"))
    muc = {(k["id"], k["so"]): k["muc"] for k in js["ket_qua"]}
    assert muc[("C001", 1)] == "ho_tro" and muc[("C002", 2)] == "ho_tro"
    assert muc[("C003", 3)] == "khong_kiem_duoc"  # [3] không có PMID ⇒ máy không gửi API
    assert ma == 0 and "Cần bác sĩ kiểm chứng" in md


def test_kiem_trich_dan_khong_ho_tro_thi_ma_1(tmp_path):
    goc = _goc_tam(tmp_path)

    def tra(kw):
        dl = json.loads(_tra_knd(kw))
        dl["ket_qua"][0]["tham_chieu"][0].update({"muc": "khong_ho_tro"})
        return json.dumps(dl)

    assert KND.main(["--study", "S1", "--goi-api"], client=KhachGia(tra), lay=lambda p: ABS, goc=goc) == 1


def test_kiem_trich_dan_khong_khach_that_duoi_pytest_la_ma_2(tmp_path, monkeypatch):
    monkeypatch.delenv("EBM_KIEM_API_THAT", raising=False)
    goc = _goc_tam(tmp_path)
    assert KND.main(["--study", "S1", "--goi-api"], client=None, lay=lambda p: ABS, goc=goc) == 2


# ── Phản biện máy ────────────────────────────────────────────────────────────────────────────────────────────────
def test_trich_dan_tat_dinh():
    van = (
        "# 1. A\nCâu [2]. Câu [1]. Câu [4].\n# 7. TÀI LIỆU THAM KHẢO\n1. A. PMID: 1.\n2. B. PMID: 2.\n3. C. PMID: 3.\n"
    )
    vd = [p["van_de"] for p in PBM.kiem_trich_dan_tat_dinh(van)]
    assert any("[4]" in v for v in vd) and any("[3]" in v for v in vd) and any("Vancouver" in v for v in vd)


VAN_PB = "# 4. PHƯƠNG PHÁP\nCỡ mẫu tối thiểu là 420 người.\n# 6. KẾ HOẠCH\nTổng cỡ mẫu dự kiến 380 người.\n"


def test_phan_bien_chi_trinh_phat_hien_co_nguyen_van():
    dl = {
        "phat_hien": [
            {
                "loai": "mau_thuan_so",
                "muc": "cao",
                "dong": 4,
                "trich": "Cỡ mẫu tối thiểu là 420 người",
                "doi_chieu": {"dong": 4, "trich": "4| Tổng cỡ mẫu dự kiến 380 người"},
                "van_de": "lệch N",
                "goi_y": "thống nhất",
            },
            {"loai": "cau_cut", "muc": "vua", "dong": 2, "trich": "câu không hề có", "van_de": "x", "goi_y": "y"},
            {
                "loai": "mau_thuan_noi_dung",
                "muc": "vua",
                "dong": 2,
                "trich": "Cỡ mẫu tối thiểu",
                "van_de": "x",
                "goi_y": "y",
            },
        ]
    }
    dat, khong = PBM.kiem_phat_hien(dl, VAN_PB)
    assert len(dat) == 1 and dat[0]["dong"] == 2 and dat[0]["doi_chieu"]["trich"] == "Tổng cỡ mẫu dự kiến 380 người"
    assert [k["ly_do_khong_xac_minh"] for k in khong] == [
        "trích không có nguyên văn trong đề cương",
        "mâu thuẫn mà không nêu chỗ đối chiếu",
    ]


def test_phan_bien_goi_api_ghi_bao_cao(tmp_path):
    goc = _goc_tam(tmp_path, VAN_PB)
    tra = json.dumps(
        {
            "phat_hien": [
                {
                    "loai": "mau_thuan_so",
                    "muc": "cao",
                    "dong": 2,
                    "trich": "Cỡ mẫu tối thiểu là 420",
                    "doi_chieu": {"dong": 4, "trich": "Tổng cỡ mẫu dự kiến 380"},
                    "van_de": "lệch N",
                    "goi_y": "thống nhất N",
                }
            ]
        }
    )
    assert PBM.main(["--study", "S1", "--goi-api"], client=KhachGia(tra), goc=goc) == 1
    md = (goc / "exports" / "S1" / "kiem_may_api" / "PHAN_BIEN_MAY_S1.md").read_text(encoding="utf-8")
    assert "Cỡ mẫu tối thiểu là 420" in md and "Cần bác sĩ kiểm chứng" in md


def test_phan_bien_chay_kho_khong_goi(tmp_path):
    goc = _goc_tam(tmp_path, VAN_PB)

    def cam(kw):
        raise AssertionError("chạy khô không được gọi API")

    assert PBM.main(["--study", "S1"], client=KhachGia(cam), goc=goc) == 0
    assert not (goc / "exports" / "S1" / "kiem_may_api").exists()


# ── Hội đồng cổng qua Batch API ──────────────────────────────────────────────────────────────────────────────────
NV = HDC.NHIEM_VU["G3"][0]
DP = HDC.DIEM_QUYET_DINH["G3"][0]
TEP = NV["dau_ra"][0].replace("<mã>", "S1")


def _st(out_dir):
    (out_dir / TEP).write_text("# Cỡ mẫu\nN = 420\nAlpha 0,05\n", encoding="utf-8", newline="\n")
    return {
        "schema": HB.SCHEMA,
        "study": "S1",
        "gate": "G3",
        "model": "claude-sonnet-5-5",
        "tao_luc": "x",
        "trang_thai_song": "READY",
        "khuyen_nghi": "hop_duoc",
        "nhat_quan": [],
        "sha": {TEP: HB._sha(out_dir / TEP)},
        "cham": {
            NV["ma"]: {
                "tac_gia": NV["agent"],
                "chuyen_mon": NV["cham_chuyen_mon"][0],
                "tai_lieu": [TEP],
                "ket": {"chuyen_mon": None, "giam_khao": None},
                "loi": [],
            }
        },
        "tranh": {
            DP["ma"]: {
                "cau_hoi": DP["cau_hoi"],
                "tham_quyen": DP["tham_quyen"],
                "tai_lieu_xet": [TEP],
                "buoc": "de_xuat",
                "loi": [],
            }
        },
        "batch": None,
        "lich_su": [],
    }


CC = [{"loai": "tep", "gia_tri": f"{TEP}:2"}]
TRA = {
    "cm": {
        "tieu_chi": [{"ma": m, "muc": "dat", "nhan_xet": "ổn"} for m in HDC.RUBRIC],
        "ket_luan": "dat",
        "bai_hoc_he_thong": [],
    },
    "de": {
        "ket_luan_de_xuat": "N = 420 đủ cho kết cục chính (đề xuất cho thống kê viên).",
        "luan_diem": [{"ma": "L1", "noi_dung": "N ghi ở dòng 2", "can_cu": CC}],
    },
    "ph": {"luan_diem": [{"ma": "P1", "phan_doi": "L1", "noi_dung": "Không có phản đối có căn cứ", "nhuong": True}]},
    "tr": {
        "tung_luan_diem": [{"ma": "P1", "ket": "bac", "ly_do": "phản biện đã nhường"}],
        "ket_qua": "giu_ket_luan",
        "ket_luan_cuoi": "Giữ đề xuất N = 420 để thống kê viên xem.",
        "viec_sua": [],
        "chuyen_bac_si": [],
        "giai_phap_tot_nhat": {"phuong_an": "Thống kê viên đối chiếu N với tham số nguồn.", "can_cu": CC},
    },
}
TRA["gk"] = TRA["cm"]


class KhachBatch:
    """Batch giả: nộp ⇒ id; retrieve ⇒ ended; results ⇒ JSON theo tiền tố custom_id."""

    def __init__(self, hong=(), sai_khuon=()):
        self.lo, self.hong, self.batches = {}, set(hong), self
        self.sai_khuon = set(sai_khuon)
        self.messages = SimpleNamespace(batches=self)

    def create(self, requests):
        bid = f"msgbatch_{len(self.lo)}"
        self.lo[bid] = [r["custom_id"] for r in requests]
        for r in requests:
            assert API._CUSTOM_ID.match(r["custom_id"]) and r["params"]["system"]
        return SimpleNamespace(id=bid)

    def retrieve(self, bid):
        return SimpleNamespace(
            processing_status="ended",
            request_counts=SimpleNamespace(processing=0, succeeded=len(self.lo[bid]), errored=0, expired=0, canceled=0),
        )

    def results(self, bid):
        for cid in self.lo[bid]:
            if cid in self.hong:
                text = "không phải json"
            elif cid in self.sai_khuon:
                text = json.dumps({"ket_luan": "tuyet_voi"})  # JSON đúng cú pháp, sai khuôn bản chấm
            else:
                text = json.dumps(TRA[cid[:2]], ensure_ascii=False)
            msg = SimpleNamespace(
                stop_reason="end_turn",
                stop_details=None,
                content=[SimpleNamespace(text=text)],
                usage=SimpleNamespace(input_tokens=1000, output_tokens=200),
            )
            yield SimpleNamespace(custom_id=cid, result=SimpleNamespace(type="succeeded", message=msg))


def _chuan_bi(tmp_path):
    out = tmp_path / "exports" / "S1"
    out.mkdir(parents=True)
    st = _st(out)
    HB._ghi_st(HB.tep_trang_thai(out, "G3"), st)
    return tmp_path, out


def _chay(goc, kh, *lenh):
    return HB.main([lenh[0], "--study", "S1", "--gate", "G3", *lenh[1:]], client=kh, goc=goc)


def test_yeu_cau_dung_vai_he_thong_va_tep_danh_so(tmp_path):
    out = tmp_path / "exports" / "S1"
    out.mkdir(parents=True)
    yc = HB.yeu_cau_tiep(_st(out), out, REPO)
    nhan = sorted((n["loai"], n.get("vai") or n.get("buoc")) for _, _, n in yc)
    assert nhan == [("cham", "chuyen_mon"), ("cham", "giam_khao"), ("tranh", "de_xuat")]
    p = next(p for c, p, _ in yc if c.startswith("gk"))
    he = API.van_ban_he_thong(p)
    assert "CHẾ ĐỘ BATCH API" in he and "RQ1" in he
    assert p["system"][0]["cache_control"] == {"type": "ephemeral"}  # tệp agent lặp lại ⇒ đánh dấu cache
    assert f"### TỆP: {TEP} (3 dòng)\n1| # Cỡ mẫu\n2| N = 420" in p["messages"][0]["content"]


def test_tai_lieu_doi_thi_khong_dung_yeu_cau(tmp_path):
    out = tmp_path / "exports" / "S1"
    out.mkdir(parents=True)
    st = _st(out)
    (out / TEP).write_text("đã sửa\n", encoding="utf-8", newline="\n")
    assert HB.yeu_cau_tiep(st, out, REPO) == []
    assert "đổi sau khi khởi tạo" in st["cham"][NV["ma"]]["loi"][0]


def test_vong_batch_dau_cuoi_ghi_bien_ban_hop_le(tmp_path):
    goc, out = _chuan_bi(tmp_path)
    kh = KhachBatch()
    assert _chay(goc, kh, "buoc") == 0 and not kh.lo  # chạy khô: không nộp
    for _ in range(4):  # chấm+đề xuất → phản biện → trọng tài
        assert _chay(goc, kh, "buoc", "--goi-api") in (0,)
    assert len(kh.lo) == 3
    assert _chay(goc, kh, "ghi") == 0 and not (out / "hoi_dong").exists()  # ghi chạy khô: chỉ kiểm luật
    assert _chay(goc, kh, "ghi", "--ap-dung") == 0
    bb = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((out / "hoi_dong" / "G3").glob("*.json"))]
    loai = sorted(b["loai"] for b in bb)
    assert loai == ["danh_gia_cheo", "tranh_bien"]
    tb = next(b for b in bb if b["loai"] == "tranh_bien")
    assert tb["che_do"] == "batch_api" and tb["nguon_may"]["batch"] == ["msgbatch_0", "msgbatch_1", "msgbatch_2"]
    assert "Claude API" in (out / "hoi_dong" / "G3" / f"{tb['id']}.md").read_text(encoding="utf-8")
    assert _chay(goc, kh, "ghi", "--ap-dung") == 0  # không ghi lặp


def test_ket_qua_hong_ghi_loi_khong_doan(tmp_path):
    goc, out = _chuan_bi(tmp_path)
    kh = KhachBatch(hong={"gk_000"})
    _chay(goc, kh, "buoc", "--goi-api")
    _chay(goc, kh, "buoc", "--goi-api")
    st = json.loads(HB.tep_trang_thai(out, "G3").read_text(encoding="utf-8"))
    c = st["cham"][NV["ma"]]
    assert c["ket"]["giam_khao"] is None and "gk_000" in c["loi"][0]
    assert not [x for x in HB.ban_nhap(st) if x[0] == "danh_gia_cheo"]


def test_hai_nguoi_cham_khac_phia_sinh_tranh_bien_bat_dong(tmp_path):
    out = tmp_path / "exports" / "S1"
    out.mkdir(parents=True)
    st = _st(out)
    st["batch"] = {
        "id": "b",
        "nop_luc": "x",
        "yeu_cau": {
            "cm_000": {"loai": "cham", "ma": NV["ma"], "vai": "chuyen_mon"},
            "gk_000": {"loai": "cham", "ma": NV["ma"], "vai": "giam_khao"},
        },
    }
    tra_ve = {**TRA["gk"], "ket_luan": "tra_ve_sua"}
    ket = {
        "cm_000": {"loai": "succeeded", "stop_reason": "end_turn", "text": json.dumps(TRA["cm"])},
        "gk_000": {"loai": "succeeded", "stop_reason": "end_turn", "text": json.dumps(tra_ve)},
    }
    HB.ap_ket_qua(st, ket)
    assert st["tranh"][f"BD-{NV['ma']}"]["buoc"] == "de_xuat"


def test_ghi_tu_choi_khi_tai_lieu_doi_sau_cham(tmp_path):
    goc, out = _chuan_bi(tmp_path)
    kh = KhachBatch()
    for _ in range(4):
        _chay(goc, kh, "buoc", "--goi-api")
    (out / TEP).write_text("sửa sau khi chấm\n", encoding="utf-8", newline="\n")
    assert _chay(goc, kh, "ghi", "--ap-dung") == 1
    assert not (out / "hoi_dong").exists()


def test_ban_cham_sai_khuon_khong_vao_so(tmp_path):
    goc, out = _chuan_bi(tmp_path)
    kh = KhachBatch(sai_khuon={"cm_000"})
    _chay(goc, kh, "buoc", "--goi-api")
    _chay(goc, kh, "buoc", "--goi-api")
    st = json.loads(HB.tep_trang_thai(out, "G3").read_text(encoding="utf-8"))
    c = st["cham"][NV["ma"]]
    assert c["ket"]["chuyen_mon"] is None and "sai khuôn" in c["loi"][0]


# ── 18/11/2026 (BTM thật): một lô trả JSON sai cú pháp ⇒ 12/51 cặp «không kiểm được»; nay gửi lại đúng lô đó MỘT lần ─
def test_kiem_trich_dan_json_hong_thi_gui_lai_mot_lan(tmp_path):
    goc = _goc_tam(tmp_path)
    dem = {"n": 0}

    def tra(kw):
        dem["n"] += 1
        return '{"ket_qua": [ {"id": "C001" "hỏng"' if dem["n"] == 1 else _tra_knd(kw)

    kh = KhachGia(tra)
    ma = KND.main(["--study", "S1", "--goi-api"], client=kh, lay=lambda p: ABS, goc=goc)
    js = json.loads((goc / "exports" / "S1" / "kiem_may_api" / "A12_KIEM_NOI_DUNG_S1.json").read_text(encoding="utf-8"))
    muc = {(k["id"], k["so"]): k["muc"] for k in js["ket_qua"]}
    assert ma == 0 and len(kh.messages.goi) == 2 and muc[("C001", 1)] == "ho_tro" and js["loi"] == []


def test_kiem_trich_dan_json_hong_hai_lan_thi_khong_kiem_duoc_khong_doan(tmp_path):
    goc = _goc_tam(tmp_path)
    kh = KhachGia('{"ket_qua": [ {"id": "C001" "hỏng"')
    KND.main(["--study", "S1", "--goi-api"], client=kh, lay=lambda p: ABS, goc=goc)
    js = json.loads((goc / "exports" / "S1" / "kiem_may_api" / "A12_KIEM_NOI_DUNG_S1.json").read_text(encoding="utf-8"))
    assert len(kh.messages.goi) == 2  # gửi đầu + đúng MỘT lần gửi lại, không lặp
    assert {k["muc"] for k in js["ket_qua"]} == {"khong_kiem_duoc"} and "JSON hỏng" in js["loi"][0]


def test_kiem_trich_dan_cat_cut_khong_gui_lai(tmp_path):
    """Cắt cụt (max_tokens) gửi lại cũng cụt ⇒ không tốn thêm lượt."""
    goc = _goc_tam(tmp_path)
    kh = KhachGia(lambda kw: _resp('{"ket_qua": [', stop="max_tokens"))
    KND.main(["--study", "S1", "--goi-api"], client=kh, lay=lambda p: ABS, goc=goc)
    assert len(kh.messages.goi) == 1


def test_kiem_trich_dan_json_tot_khong_gui_them(tmp_path):
    """Câu trả lời đọc được ⇒ mỗi lô đúng một lượt gọi (thử lại không được tốn tiền khi không cần)."""
    goc = _goc_tam(tmp_path)
    kh = KhachGia(_tra_knd)
    KND.main(["--study", "S1", "--goi-api"], client=kh, lay=lambda p: ABS, goc=goc)
    assert len(kh.messages.goi) == 1


def test_so_de_muc_khong_phai_so_lieu():
    """18/11/2026 (BTM C022): «mục 4.9» bị gắn cờ «số không thấy: 4.9» dù câu trích đúng — số đề mục bị bỏ qua."""
    assert KND.so_lieu("kế hoạch giảm tham số ở mục 4.9 dùng mức này [38]") == []
    assert KND.so_lieu("xem Bảng 5.2 và Phụ lục 3,1; §4.10") == []
    assert KND.so_lieu("tỷ lệ 31,2% ở mục 4.9; HR 0,74 [2]") == ["31.2", "0.74"]
    assert KND.so_lieu("đo 4.9 mmol/L [2]") == ["4.9"]
