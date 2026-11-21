"""Bước THẨM TRA phát hiện của phản biện máy đề cương — lọc báo động giả (21/11/2026).

Đo thật trên C1a (20/11): 12 phát hiện đã xác minh nguyên văn, 5 là báo động giả (chính «vấn đề» tự ghi «số khớp»,
«không mâu thuẫn»). Nay mỗi phát hiện qua một model thứ hai: chỉ được «giữ» (HẠ mức nếu cần) hoặc «loại» kèm lý do;
phát hiện bị loại vẫn hiện trong báo cáo; thẩm tra lỗi/thiếu phán quyết ⇒ GIỮ (fail-safe). Ngoại tuyến, khách giả.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

REPO = Path(__file__).resolve().parents[1]
for _d in (REPO, REPO / "tools"):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

import api_claude_nc as API  # noqa: E402
import phan_bien_may_de_cuong as PBM  # noqa: E402


def _resp(text, stop="end_turn", model="claude-opus-5-5"):
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


# Dòng 9 nằm xa mọi phát hiện ⇒ không được lọt vào lượt thẩm tra (chỉ gửi đoạn trích + ngữ cảnh ±1 dòng).
VAN = (
    "# 4. PHƯƠNG PHÁP\n"
    "Cỡ mẫu tối thiểu là 420 người.\n"
    "Lấy mẫu thuận tiện.\n"
    "Tổng cỡ mẫu dự kiến 380 người.\n"
    "# 5. ĐẠO ĐỨC\n"
    "Miễn đồng thuận.\n"
    "# 6. KẾ HOẠCH\n"
    "Tháng 1 thu thập.\n"
    "Câu-đánh-dấu-xa-không-được-gửi.\n"
)

PH_CAO = {
    "loai": "mau_thuan_so",
    "muc": "cao",
    "dong": 2,
    "trich": "Cỡ mẫu tối thiểu là 420",
    "doi_chieu": {"dong": 4, "trich": "Tổng cỡ mẫu dự kiến 380"},
    "van_de": "lệch N",
    "goi_y": "thống nhất N",
}
PH_VUA = {"loai": "cau_cut", "muc": "vua", "dong": 3, "trich": "Lấy mẫu thuận tiện", "van_de": "câu cụt", "goi_y": "x"}


def _dat():
    dat, khong = PBM.kiem_phat_hien({"phat_hien": [dict(PH_CAO), dict(PH_VUA)]}, VAN)
    assert len(dat) == 2 and not khong
    return dat


def _pq(*ds):
    return json.dumps({"phan_quyet": list(ds)}, ensure_ascii=False)


def _he_thong(kw):
    return API.van_ban_he_thong(kw)


def test_loai_bao_dong_gia_van_liet_ke_kem_ly_do():
    dat = _dat()
    tra = _pq({"id": 1, "ket_luan": "loai", "ly_do": "420 là tối thiểu, 380 là dự kiến sau loại trừ — không lệch"},
              {"id": 2, "ket_luan": "giu", "muc_moi": None, "ly_do": "câu cụt thật"})
    giu, loai, kq, loi = PBM.tham_tra(dat, VAN, "claude-opus-5-5", KhachGia(tra))
    assert loi is None and kq is not None
    assert [p["loai"] for p in loai] == ["mau_thuan_so"] and "không lệch" in loai[0]["ly_do_loai"]
    assert [p["loai"] for p in giu] == ["cau_cut"] and giu[0]["tham_tra"] == "câu cụt thật"


def test_chi_duoc_ha_muc_khong_duoc_nang():
    dat = _dat()
    tra = _pq({"id": 1, "ket_luan": "giu", "muc_moi": "thap", "ly_do": "lệch nhỏ"},
              {"id": 2, "ket_luan": "giu", "muc_moi": "cao", "ly_do": "nâng thử"})
    giu, loai, _, _ = PBM.tham_tra(dat, VAN, "claude-opus-5-5", KhachGia(tra))
    theo_loai = {p["loai"]: p for p in giu}
    assert not loai
    assert theo_loai["mau_thuan_so"]["muc"] == "thap" and theo_loai["mau_thuan_so"]["muc_truoc_tham_tra"] == "cao"
    assert theo_loai["cau_cut"]["muc"] == "vua" and "muc_truoc_tham_tra" not in theo_loai["cau_cut"]


def test_thieu_hoac_la_phan_quyet_thi_giu():
    dat = _dat()
    tra = _pq({"id": 2, "ket_luan": "co_le", "ly_do": "?"})  # id 1 vắng, id 2 kết luận lạ
    giu, loai, _, loi = PBM.tham_tra(dat, VAN, "claude-opus-5-5", KhachGia(tra))
    assert loi is None and not loai and len(giu) == 2
    assert all(p["tham_tra"].startswith("không có phán quyết hợp lệ") for p in giu)


def test_json_hong_hay_cat_cut_thi_giu_tat_ca_va_bao_loi():
    for kh in (KhachGia("không phải JSON"), KhachGia(_resp('{"phan_quyet": [', stop="max_tokens"))):
        giu, loai, kq, loi = PBM.tham_tra(_dat(), VAN, "claude-opus-5-5", kh)
        assert len(giu) == 2 and not loai and kq is None and loi


def test_loi_sdk_thi_giu_tat_ca():
    def no(kw):
        raise RuntimeError("529 quá tải")

    giu, loai, _, loi = PBM.tham_tra(_dat(), VAN, "claude-opus-5-5", KhachGia(no))
    assert len(giu) == 2 and not loai and "RuntimeError" in loi


def test_chi_gui_doan_trich_va_ngu_canh_khong_gui_toan_van():
    kh = KhachGia(_pq())
    PBM.tham_tra(_dat(), VAN, "claude-opus-5-5", kh)
    (kw,) = kh.messages.goi
    noi = json.dumps(kw["messages"], ensure_ascii=False)
    assert "Tổng cỡ mẫu dự kiến 380" in noi and "Lấy mẫu thuận tiện" in noi
    assert "Câu-đánh-dấu-xa-không-được-gửi" not in noi
    assert _he_thong(kw) == PBM.HE_THONG_THAM_TRA


def test_khong_co_phat_hien_thi_khong_goi():
    def cam(kw):
        raise AssertionError("không có phát hiện thì không gọi thẩm tra")

    assert PBM.tham_tra([], VAN, "claude-opus-5-5", KhachGia(cam)) == ([], [], None, None)


# ── main: nối dây đầu–cuối ────────────────────────────────────────────────────────────────────────────────────────
def _goc(tmp_path, ma="S1"):
    d = tmp_path / "exports" / ma
    d.mkdir(parents=True)
    (d / f"DE_CUONG_NOP_HOI_DONG_{ma}.md").write_text(VAN, encoding="utf-8", newline="\n")
    return tmp_path


def _khach_hai_luot(pq):
    phat_hien = json.dumps({"phat_hien": [PH_CAO, PH_VUA]}, ensure_ascii=False)
    return KhachGia(lambda kw: pq if _he_thong(kw) == PBM.HE_THONG_THAM_TRA else phat_hien)


def test_main_tham_tra_loai_ghi_bao_cao_va_json(tmp_path, monkeypatch):
    monkeypatch.delenv("EBM_NC_API_MODEL_THAM_TRA", raising=False)
    goc = _goc(tmp_path)
    kh = _khach_hai_luot(_pq({"id": 1, "ket_luan": "loai", "ly_do": "số khớp"},
                             {"id": 2, "ket_luan": "giu", "muc_moi": "thap", "ly_do": "lỗi nhỏ"}))
    assert PBM.main(["--study", "S1", "--goi-api"], client=kh, goc=goc) == 0  # còn lại chỉ mức thấp
    goi = kh.messages.goi
    assert len(goi) == 2 and goi[1]["model"] == PBM.MODEL_THAM_TRA_MAC_DINH == "claude-opus-5-5"
    ra = goc / "exports" / "S1" / "kiem_may_api"
    md = (ra / "PHAN_BIEN_MAY_S1.md").read_text(encoding="utf-8")
    assert "## Máy thẩm tra loại" in md and "số khớp" in md and "Cỡ mẫu tối thiểu là 420" in md
    assert "Thẩm tra phát hiện: model" in md
    dl = json.loads((ra / "PHAN_BIEN_MAY_S1.json").read_text(encoding="utf-8"))
    assert [p["loai"] for p in dl["loai_sau_tham_tra"]] == ["mau_thuan_so"]
    assert dl["tham_tra"]["so_loai"] == 1 and dl["tham_tra"]["loi"] is None


def test_main_tham_tra_loi_thi_giu_nguyen_ma_1(tmp_path):
    goc = _goc(tmp_path)
    kh = _khach_hai_luot("không phải JSON")
    assert PBM.main(["--study", "S1", "--goi-api"], client=kh, goc=goc) == 1
    md = (goc / "exports" / "S1" / "kiem_may_api" / "PHAN_BIEN_MAY_S1.md").read_text(encoding="utf-8")
    assert "Thẩm tra phát hiện: LỖI" in md and "## Máy thẩm tra loại" not in md


def test_main_khong_tham_tra_chi_mot_luot(tmp_path):
    goc = _goc(tmp_path)
    kh = _khach_hai_luot(_pq({"id": 1, "ket_luan": "loai", "ly_do": "x"}))
    assert PBM.main(["--study", "S1", "--goi-api", "--khong-tham-tra"], client=kh, goc=goc) == 1
    assert len(kh.messages.goi) == 1


def test_main_model_tham_tra_theo_co_roi_bien_moi_truong(tmp_path, monkeypatch):
    goc = _goc(tmp_path)
    monkeypatch.setenv("EBM_NC_API_MODEL_THAM_TRA", "claude-sonnet-5-5")
    kh = _khach_hai_luot(_pq())
    PBM.main(["--study", "S1", "--goi-api"], client=kh, goc=goc)
    assert kh.messages.goi[1]["model"] == "claude-sonnet-5-5"
    kh2 = _khach_hai_luot(_pq())
    PBM.main(["--study", "S1", "--goi-api", "--model-tham-tra", "claude-fable-5-2"], client=kh2, goc=goc)
    assert kh2.messages.goi[1]["model"] == "claude-fable-5-2"


def test_main_chay_kho_bao_luot_tham_tra_khong_goi(tmp_path, capsys):
    goc = _goc(tmp_path)

    def cam(kw):
        raise AssertionError("chạy khô không được gọi API")

    assert PBM.main(["--study", "S1"], client=KhachGia(cam), goc=goc) == 0
    assert "lượt thẩm tra phát hiện" in capsys.readouterr().out
