"""Hội đồng Khoa học máy cấp đề tài (bác sĩ 22/11/2026): thành viên chấm độc lập, mọi nhận xét phải trích nguyên văn
(máy kiểm), chủ tịch chỉ được hạ/loại, kết luận theo luật tất định, hiệu chuẩn bằng lỗi cài sẵn. Khách API giả — không
gọi mạng, không tính phí."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import api_claude_nc as API  # noqa: E402
import hoi_dong_khoa_hoc as H  # noqa: E402

STUDY = "ZZHDKH"
DE_CUONG = """# ĐẶT VẤN ĐỀ
Tăng huyết áp là bệnh mạn tính phổ biến [1].
## MỤC TIÊU NGHIÊN CỨU
1. Xác định tỷ lệ kiểm soát huyết áp ở người bệnh ngoại trú.
### 2.1.2. Tiêu chuẩn loại trừ
- Người bệnh không đồng ý tham gia.
### 2.6.5. Xử lý và phân tích số liệu
Tỷ lệ được ước lượng kèm khoảng tin cậy 95% theo Wilson.
# CHƯƠNG 3. DỰ KIẾN KẾT QUẢ VÀ BÀN LUẬN
Dự kiến tỷ lệ kiểm soát khoảng 50%.
**Tự nguyện và đồng ý tham gia.** Người bệnh được giải thích đầy đủ trước khi ký.
"""


def _tv(diem=4, phat_hien=None, ket_luan="thong_qua_co_sua"):
    return {"diem": {k: diem for k in H.MUC_PHIEU}, "ly_do_diem": {k: "…" for k in H.MUC_PHIEU},
            "phat_hien": phat_hien or [], "diem_manh": ["mục tiêu rõ"], "ket_luan": ket_luan}


PH_DUNG = {"muc_phieu": "2", "muc_do": "can_sua", "dong": 8, "trich": "theo Wilson",
           "van_de": "chưa nêu cách xử lý dữ liệu thiếu", "chuan": "STROBE 12c",
           "de_xuat": "thêm kế hoạch dữ liệu thiếu"}
PH_BIA = {"muc_phieu": "1", "muc_do": "nghiem_trong", "dong": 2, "trich": "câu không hề có trong đề cương",
          "van_de": "x", "de_xuat": "y", "chuan": ""}


# ── xác minh ────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_trich_nguyen_van_dung_cua_so_moi_duoc_tinh():
    kq = H.xac_minh_thanh_vien("pb1", _tv(phat_hien=[PH_DUNG, PH_BIA]), DE_CUONG, ["STROBE", "Việt Nam"])
    assert [f["dong"] for f in kq["dat"]] == [8]
    assert kq["khong_xac_minh"][0]["ly_do_loai"].startswith("trích không có nguyên văn")
    sai_dong = dict(PH_DUNG, dong=1)  # trích có thật nhưng cách dòng nêu > 3 dòng ⇒ không nhận
    assert H.xac_minh_thanh_vien("pb1", _tv(phat_hien=[sai_dong]), DE_CUONG, ["STROBE"])["dat"] == []


@pytest.mark.parametrize("diem", [0, 6, "6", "4.5", 4.5, "", None, True])
def test_diem_sai_khuon_la_ket_qua_hong(diem):
    dl = _tv()
    dl["diem"]["2"] = diem
    with pytest.raises(API.KetQuaHong):
        H.xac_minh_thanh_vien("pb1", dl, DE_CUONG, [])


def test_diem_dang_chuoi_mot_chu_so_duoc_nhan():
    """Lượt thật 22/11: model trả «"3"» theo khuôn cũ ⇒ 9/10 bản chấm bị loại. Chuỗi một chữ số 1–5 được nhận."""
    dl = _tv()
    dl["diem"] = {"1": "3", "2": " 4 ", "3": 5, "4": "2"}
    dl["phat_hien"] = [dict(PH_DUNG, muc_phieu="4")]
    assert H.xac_minh_thanh_vien("pb1", dl, DE_CUONG, ["STROBE"])["diem"] == {"1": 3, "2": 4, "3": 5, "4": 2}


def test_diem_thap_khong_can_cu_va_chuan_ngoai_danh_muc_bi_canh_bao():
    kq = H.xac_minh_thanh_vien("uv_tk", _tv(diem=2), DE_CUONG, ["STROBE"])
    assert sum("không có nhận xét" in x for x in kq["canh_bao"]) == 4
    ph = dict(PH_DUNG, chuan="Tiêu chuẩn tự đặt 9.9")
    kq = H.xac_minh_thanh_vien("uv_tk", _tv(phat_hien=[ph]), DE_CUONG, ["STROBE"])
    assert kq["dat"][0]["chuan"] == "" and kq["dat"][0]["chuan_goc"] == "Tiêu chuẩn tự đặt 9.9"
    assert any("ngoài danh mục" in x for x in kq["canh_bao"])
    kq = H.xac_minh_thanh_vien("uv_tk", _tv(diem=5, phat_hien=[PH_DUNG]), DE_CUONG, ["STROBE"])
    assert any("điểm 5 mục 2" in x for x in kq["canh_bao"])


def test_nhan_xet_co_so_dien_thoai_khong_vao_bien_ban():
    ph = dict(PH_DUNG, de_xuat="gọi 0912345678 để hỏi")
    assert H.xac_minh_thanh_vien("uv_dd", _tv(phat_hien=[ph]), DE_CUONG, [])["dat"] == []


# ── chủ tịch & kết luận ─────────────────────────────────────────────────────────────────────────────────────────────
def _ds():
    return [dict(PH_DUNG, id="F01", thanh_vien="pb1"),
            dict(PH_DUNG, id="F02", thanh_vien="uv_tk", muc_do="nghiem_trong"),
            dict(PH_DUNG, id="F03", thanh_vien="pb2", muc_do="goi_y")]


def test_chu_tich_chi_ha_khong_nang_loai_phai_co_ly_do_thieu_phan_quyet_thi_giu():
    dl = {"phan_quyet": [{"id": "F01", "quyet": "ha_muc", "muc_do_moi": "nghiem_trong"},   # nâng ⇒ bỏ qua
                         {"id": "F02", "quyet": "ha_muc", "muc_do_moi": "can_sua", "ly_do": "đã có ở dòng 8"},
                         {"id": "F03", "quyet": "loai"},                                    # loại không lý do ⇒ giữ
                         {"id": "F99", "quyet": "giu"}],
          "gop": [["F01", "F02"]], "nhan_xet_chung": "ổn", "yeu_cau_chinh_sua": ["thêm dữ liệu thiếu"]}
    kq = H.ap_phan_quyet(_ds(), dl)
    muc = {f["id"]: f["muc_do"] for f in kq["giu"]}
    assert muc == {"F01": "can_sua", "F02": "can_sua", "F03": "goi_y"} and kq["loai"] == []
    assert len(kq["canh_bao"]) == 3 and kq["gop"] == [["F01", "F02"]]
    kq = H.ap_phan_quyet(_ds(), {"phan_quyet": [{"id": "F03", "quyet": "loai", "ly_do": "đề cương đã có ở dòng 8"}]})
    assert [f["id"] for f in kq["loai"]] == ["F03"] and len(kq["giu"]) == 2


@pytest.mark.parametrize("van_de, trung_vi, mong", [
    ([{"muc_do": "nghiem_trong"}] * 3, {"1": 4, "2": 4, "3": 4, "4": 4}, "khong_thong_qua"),
    ([], {"1": 4, "2": 2, "3": 4, "4": 4}, "khong_thong_qua"),
    ([{"muc_do": "can_sua"}], {"1": 4, "2": 4, "3": 4, "4": 4}, "thong_qua_co_sua"),
    ([], {"1": 4, "2": 4, "3": 3, "4": 4}, "thong_qua_co_sua"),
    ([{"muc_do": "goi_y"}], {"1": 4, "2": 5, "3": 4, "4": 4}, "thong_qua"),
])
def test_ket_luan_theo_luat_co_dinh(van_de, trung_vi, mong):
    assert H.ket_luan_tat_dinh(van_de, trung_vi)[0] == mong


# ── trọn quy trình với Batch giả ────────────────────────────────────────────────────────────────────────────────────
class KhachBatch:
    def __init__(self, tra, hong=()):
        self.tra, self.hong, self.lo, self.yc = tra, set(hong), {}, {}
        self.messages = SimpleNamespace(batches=self)

    def create(self, requests):
        bid = f"msgbatch_{len(self.lo)}"
        self.lo[bid] = [r["custom_id"] for r in requests]
        for r in requests:
            assert API._CUSTOM_ID.match(r["custom_id"])
            self.yc[r["custom_id"]] = r["params"]
        return SimpleNamespace(id=bid)

    def retrieve(self, bid):
        return SimpleNamespace(processing_status="ended", request_counts=SimpleNamespace(
            processing=0, succeeded=len(self.lo[bid]), errored=0, expired=0, canceled=0))

    def results(self, bid):
        for cid in self.lo[bid]:
            ma = cid.rsplit("_", 1)[0]
            text = "không phải json" if ma in self.hong else json.dumps(self.tra[ma], ensure_ascii=False)
            msg = SimpleNamespace(stop_reason="end_turn", stop_details=None, model="claude-opus-5-5",
                                  content=[SimpleNamespace(text=text)],
                                  usage=SimpleNamespace(input_tokens=1000, output_tokens=200))
            yield SimpleNamespace(custom_id=cid, result=SimpleNamespace(type="succeeded", message=msg))


def _goc(tmp_path):
    out = tmp_path / "exports" / STUDY
    out.mkdir(parents=True)
    (out / f"DE_CUONG_NOP_HOI_DONG_{STUDY}.md").write_text(DE_CUONG, encoding="utf-8", newline="\n")
    (out / "study_meta.json").write_text(json.dumps({"gate_params": {"G1": {"design": "cross_sectional"}}}),
                                         encoding="utf-8", newline="\n")
    return tmp_path


TRA = {"pb1": _tv(phat_hien=[PH_DUNG, PH_BIA]), "pb2": _tv(diem=5), "uv_tk": _tv(phat_hien=[PH_DUNG]),
       "uv_dd": _tv(diem=4), "uv_tl": _tv(diem=3, phat_hien=[dict(PH_DUNG, muc_phieu="4", muc_do="goi_y")]),
       "ct": {"phan_quyet": [{"id": "F02", "quyet": "loai", "ly_do": "trùng F01"}], "gop": [],
              "nhan_xet_chung": "Đề cương rõ, cần bổ sung xử lý dữ liệu thiếu.",
              "yeu_cau_chinh_sua": ["dữ liệu thiếu"]}}


def test_tron_quy_trinh_hai_buoc_va_bien_ban(tmp_path):
    goc, kh = _goc(tmp_path), KhachBatch(TRA)
    assert H.main(["hop", "--study", STUDY], client=kh, goc=goc) == 0 and kh.lo == {}   # chạy khô: không nộp
    assert H.main(["hop", "--study", STUDY, "--goi-api"], client=kh, goc=goc) == 4       # nộp batch thành viên
    p_tv = [kh.yc[c] for c in kh.lo["msgbatch_0"]]
    assert len(p_tv) == 5 and len({json.dumps(p["system"], ensure_ascii=False) for p in p_tv}) == 1  # tiền tố chung
    assert p_tv[0]["system"][0]["cache_control"]["type"] == "ephemeral"
    assert p_tv[0]["model"] == "claude-opus-5-5" and p_tv[0]["thinking"] == {"type": "adaptive"}
    assert all("Chấm ĐỘC LẬP" in p["messages"][0]["content"] for p in p_tv)
    assert H.main(["hop", "--study", STUDY, "--goi-api"], client=kh, goc=goc) == 0       # lấy kết quả thành viên
    assert H.main(["hop", "--study", STUDY, "--goi-api"], client=kh, goc=goc) == 4       # nộp chủ tịch
    p_ct = kh.yc[kh.lo["msgbatch_1"][0]]
    assert p_ct["system"] == p_tv[0]["system"]                                           # chủ tịch dùng lại cache
    assert "câu không hề có" not in p_ct["messages"][0]["content"]   # chủ tịch không thấy nhận xét bịa
    assert H.main(["hop", "--study", STUDY, "--goi-api"], client=kh, goc=goc) == 0
    assert H.main(["bien-ban", "--study", STUDY, "--ap-dung"], client=kh, goc=goc) == 0
    bb = next((goc / "exports" / STUDY / H.THU_MUC).glob("BIEN_BAN_HDKH_*.md")).read_text(encoding="utf-8")
    assert "Thông qua sau khi chỉnh sửa" in bb and "Trung vị" in bb
    assert "Nhận xét máy KHÔNG xác minh được" in bb and "câu không hề có" not in bb.split("KHÔNG xác minh")[0]
    assert "trùng F01" in bb and "Cần bác sĩ kiểm chứng" in bb
    js = json.loads(next((goc / "exports" / STUDY / H.THU_MUC).glob("BIEN_BAN_HDKH_*.json")).read_text("utf-8"))
    assert js["tong_hop"]["ket_luan"] == "thong_qua_co_sua" and js["tong_hop"]["trung_vi"]["1"] == 4


def test_duoi_ba_ban_cham_hop_le_khong_du_tuc_so(tmp_path):
    goc, kh = _goc(tmp_path), KhachBatch(TRA, hong={"pb1", "pb2", "uv_tk"})
    H.main(["hop", "--study", STUDY, "--goi-api"], client=kh, goc=goc)
    assert H.main(["hop", "--study", STUDY, "--goi-api"], client=kh, goc=goc) == 1
    st = H._doc_st(next((goc / "exports" / STUDY / H.THU_MUC).glob("trang_thai_*.json")))
    assert st["buoc"] == "thanh_vien" and "chu_tich" not in st["batch"]   # không sang bước chủ tịch khi thiếu túc số


def test_chu_tich_hong_thi_giu_moi_nhan_xet_da_xac_minh(tmp_path):
    goc, kh = _goc(tmp_path), KhachBatch(TRA, hong={"ct"})
    for _ in range(4):
        H.main(["hop", "--study", STUDY, "--goi-api"], client=kh, goc=goc)
    st = H._doc_st(next((goc / "exports" / STUDY / H.THU_MUC).glob("trang_thai_*.json")))
    assert st["buoc"] == "xong" and len(st["chu_tich"]["giu"]) == len(st["ds_xac_minh"]) == 3
    assert "chủ tịch không trả lời hợp lệ" in st["chu_tich"]["canh_bao"][0]


def test_tai_lieu_doi_thi_hop_lai_tu_dau(tmp_path):
    goc, kh = _goc(tmp_path), KhachBatch(TRA)
    H.main(["hop", "--study", STUDY, "--goi-api"], client=kh, goc=goc)
    p = goc / "exports" / STUDY / f"DE_CUONG_NOP_HOI_DONG_{STUDY}.md"
    p.write_text(DE_CUONG + "Thêm một dòng.\n", encoding="utf-8", newline="\n")
    assert H.main(["hop", "--study", STUDY, "--goi-api"], client=kh, goc=goc) == 4 and len(kh.lo) == 2


def test_uoc_tinh_khong_goi_api(tmp_path, capsys):
    goc, kh = _goc(tmp_path), KhachBatch(TRA)
    assert H.main(["uoc-tinh", "--study", STUDY], client=kh, goc=goc) == 0 and kh.lo == {}
    assert "0 gọi API" in capsys.readouterr().out


# ── hiệu chuẩn ──────────────────────────────────────────────────────────────────────────────────────────────────────
def test_cai_loi_dap_an_dung_so_dong_va_chi_bam_de_muc():
    moi, da = H.cai_loi(DE_CUONG)
    dong = moi.splitlines()
    assert {a["ma"] for a in da} == {m for m, *_ in H.LOI_CAI}
    for a in da:
        assert dong[a["dong"] - 1] == a["cau"]
        assert dong[a["dong"] - 2].startswith(("#", "**")), a       # ngay sau một đề mục thật
    assert "- PHỤ LỤC" not in "\n".join(dong[a["dong"] - 2] for a in da)


def test_cham_hieu_chuan_do_nhay(tmp_path):
    goc = _goc(tmp_path)
    moi, da = H.cai_loi(DE_CUONG)
    gan = da[0]["dong"]
    st = {"thanh_vien": {"pb1": {"diem": {k: 3 for k in H.MUC_PHIEU}}},
          "chu_tich": {"giu": [{"id": "F01", "thanh_vien": "pb1", "muc_do": "nghiem_trong", "muc_phieu": "1",
                                "dong": gan + 2}, {"id": "F02", "thanh_vien": "pb1", "muc_do": "goi_y",
                                                   "muc_phieu": "4", "dong": 999}], "gop": []}}
    kq = H.cham_hieu_chuan(da, st)
    assert kq["bat"] == 1 and kq["so_loi_cai"] == len(da) and kq["van_de_ngoai_loi_cai"] == 1
    assert H.main(["hieu-chuan", "--study", STUDY, "--tao"], goc=goc) == 0
    assert json.loads((goc / "exports" / STUDY / H.THU_MUC / "hieu_chuan" / "dap_an.json").read_text("utf-8"))["dap_an"]


# ── vòng kín: biên tập có rào liêm chính → họp lại tới khi thông qua (bác sĩ 22/11/2026) ─────────────────────────────
@pytest.mark.parametrize("th, ly", [
    ({"dong": 8, "cu": "theo Wilson", "moi": "theo Wilson; dữ liệu thiếu xử lý bằng phân tích ca đầy đủ"}, None),
    ({"dong": 8, "cu": "theo Wilson", "moi": "theo Wilson, tỷ lệ thiếu dự kiến 12%"}, "số mới"),
    ({"dong": 2, "cu": "phổ biến [1]", "moi": "phổ biến [1, 7]"}, "trích dẫn mới"),
    ({"dong": 8, "cu": "khoảng tin cậy", "moi": "KTC"}, None),
    ({"dong": 4, "cu": "huyết áp", "moi": "HA"}, "xuất hiện"),
    ({"dong": 2, "cu": "theo Wilson", "moi": "theo Wilson."}, None),   # QC 1.1: dòng chỉ để tham chiếu
    ({"dong": 8, "cu": "theo Wilson", "moi": "theo Wilson [CẦN bổ sung]"}, "dấu vết máy"),
    ({"dong": 8, "cu": "theo Wilson", "moi": "x" * 3100}, "dài"),
])
def test_rao_liem_chinh_cua_tung_thay_the(th, ly):
    loi = H.kiem_thay(th, DE_CUONG)
    assert (loi is None) if ly is None else (loi and ly in loi), loi


def test_ap_bien_tap_ghi_nhat_ky_day_du():
    dl = {"sua": [{"id": "F01", "hanh_dong": "sua", "thay": [
        {"dong": 8, "cu": "theo Wilson", "moi": "theo Wilson; dữ liệu thiếu xử lý bằng phân tích ca đầy đủ"},
        {"dong": 8, "cu": "đoạn không có trong văn bản", "moi": "…"}]},   # đoạn cũ không có ⇒ loại
        {"id": "F02", "hanh_dong": "khong_sua", "ly_do": "đã có ở dòng 8"},
        {"id": "F03", "hanh_dong": "vuot_tham_quyen", "ly_do": "cần kinh phí thật"}]}
    van, nk = H.ap_bien_tap(dl, DE_CUONG)
    assert "phân tích ca đầy đủ" in van and len(nk["nhan"]) == 1 and len(nk["loai"]) == 1
    assert nk["khong_sua"][0]["id"] == "F02" and nk["vuot_tham_quyen"][0]["id"] == "F03"


SUA = {"sua": [{"id": "F01", "hanh_dong": "sua", "thay": [
    {"dong": 8, "cu": "theo Wilson", "moi": "theo Wilson; dữ liệu thiếu xử lý bằng phân tích ca đầy đủ"}]}]}
TT_DAT = {"tham_tra": [{"id": "F01", "ket_qua": "da_giai_quyet", "dong": 8,
                       "trich": "dữ liệu thiếu xử lý bằng phân tích ca đầy đủ", "ly_do": ""}], "loi_moi": []}
SACH = {**{m: _tv(diem=5) for m in ("pb1", "pb2", "uv_tk", "uv_dd", "uv_tl")},
        "ct": {"phan_quyet": [], "gop": [], "nhan_xet_chung": "Đạt.", "yeu_cau_chinh_sua": []}}


def _hieu_chuan_dat(goc, do_nhay=1.0):
    """Kết quả hiệu chuẩn HỢP LỆ dưới quy chế hiện hành (điều kiện tiên quyết của vòng kín)."""
    H._ghi_json(goc / "exports" / STUDY / H.THU_MUC / "hieu_chuan" / "ket_qua.json",
                {"sha_quy_che": H.sha_ke_hoach(), "do_nhay": do_nhay, "bat": round(6 * do_nhay), "so_loi_cai": 6})


def _vong(goc, kh, n=12):
    ma = None
    for _ in range(n):
        ma = H.main(["vong-kin", "--study", STUDY, "--goi-api", "--ap-dung"], client=kh, goc=goc)
        out = goc / "exports" / STUDY / H.THU_MUC
        if any((H._doc_st(p) or {}).get("buoc") == "dat" for p in out.glob("trang_thai_*.json")):
            return ma
    return ma


def test_vong_kin_sua_roi_hop_lai_toi_khi_dat(tmp_path):
    goc = _goc(tmp_path)
    _hieu_chuan_dat(goc)
    kh = KhachBatch({**TRA, "bt0": SUA})
    p = goc / "exports" / STUDY / f"DE_CUONG_NOP_HOI_DONG_{STUDY}.md"
    for _ in range(6):                                   # vòng 1: họp → còn «cần sửa» → biên tập → áp
        H.main(["vong-kin", "--study", STUDY, "--goi-api", "--ap-dung"], client=kh, goc=goc)
        if "phân tích ca đầy đủ" in p.read_text(encoding="utf-8"):
            break
    assert "phân tích ca đầy đủ" in p.read_text(encoding="utf-8")
    out = goc / "exports" / STUDY / H.THU_MUC
    assert list(out.glob("sao_luu_*.md")) and list(out.glob("BIEN_BAN_HDKH_*.md"))   # sao lưu + biên bản vòng 1
    kh.tra = {**kh.tra, "tt_pb1": TT_DAT}                  # vòng 2: THẨM TRA — F01 đã giải quyết
    assert _vong(goc, kh) == 0
    st = [H._doc_st(x) for x in out.glob("trang_thai_*.json")]
    dat = [s for s in st if s.get("buoc") == "dat"]
    assert len(dat) == 1 and dat[0]["vong"] == 2 and dat[0]["ban_truoc"]
    assert dat[0]["che_do"] == "tham_tra" and dat[0]["ket_luan_cuoi"] == "thong_qua"
    assert [f["id"] for f in dat[0]["ds_yeu_cau"]] == ["F01"]        # chỉ thẩm tra yêu cầu nghiêm trọng/cần sửa


def test_vong_kin_hoan_nguyen_khi_ban_sua_lam_chuan_xau_di(tmp_path, monkeypatch):
    goc = _goc(tmp_path)
    _hieu_chuan_dat(goc)
    kh = KhachBatch({**TRA, "bt0": SUA})
    p = goc / "exports" / STUDY / f"DE_CUONG_NOP_HOI_DONG_{STUDY}.md"
    goc_van = p.read_text(encoding="utf-8")
    that = H._do_chuan

    def do_gia(van, study, out_dir, la_chinh):
        r = that(van, study, out_dir, la_chinh)
        if la_chinh and "phân tích ca đầy đủ" in van:
            r["lech"] = (r.get("lech") or 0) + 1        # giả lập: bản sửa làm lệch xuyên cổng tăng
        return r

    monkeypatch.setattr(H, "_do_chuan", do_gia)
    ma = [H.main(["vong-kin", "--study", STUDY, "--goi-api", "--ap-dung"], client=kh, goc=goc) for _ in range(6)]
    assert 1 in ma and p.read_text(encoding="utf-8") == goc_van  # đã hoàn nguyên, không để bản xấu đi


def test_vong_kin_dung_sau_so_vong_toi_da(tmp_path, monkeypatch):
    goc, kh = _goc(tmp_path), KhachBatch({**TRA, "bt0": SUA})
    monkeypatch.setattr(H, "SO_VONG_TOI_DA", 1)
    _hieu_chuan_dat(goc)   # hiệu chuẩn tính dưới quy chế ĐÃ đổi số vòng — SHA phải tính sau khi vá
    # 4 lượt họp (nộp/lấy thành viên, nộp/lấy chủ tịch) + lượt 5 xét điều kiện dừng ở «xong»
    ma = [H.main(["vong-kin", "--study", STUDY, "--goi-api", "--ap-dung"], client=kh, goc=goc) for _ in range(5)]
    assert ma[-1] == 1 and "phân tích ca đầy đủ" not in (goc / "exports" / STUDY /
                                                        f"DE_CUONG_NOP_HOI_DONG_{STUDY}.md").read_text("utf-8")


# ── quy chế khoá trước khi họp (bác sĩ 22/11/2026: quy trình khoa học nghiêm ngặt, kế hoạch từ đầu, trung thực) ─────
def test_van_ban_quy_che_trong_repo_khop_sha_cua_ma():
    """Văn bản quy chế lưu trong repo phải sinh từ ĐÚNG dữ liệu khoá — sửa lời dặn/luật mà không sinh lại ⇒ đỏ."""
    vb = (ROOT / H.TEP_QUY_CHE).read_text(encoding="utf-8")
    assert H.sha_ke_hoach() in vb and vb == H.van_ban_quy_che()


@pytest.mark.parametrize("ten, gia_tri", [("MOC_DIEM", "khác"), ("CUA_SO_DONG", 5), ("SO_VONG_TOI_DA", 9),
                                          ("DO_NHAY_TOI_THIEU", 0.5), ("EFFORT", "low"),
                                          ("loi_nhan_chu_tich", lambda *a: "lời dặn khác"),   # chỉ đổi LỜI DẶN
                                          ("loi_nhan_bien_tap", lambda *a: "lời dặn khác")])
def test_doi_bat_ky_luat_nao_la_doi_sha_quy_che(monkeypatch, ten, gia_tri):
    goc = H.sha_ke_hoach()
    monkeypatch.setattr(H, ten, gia_tri)
    assert H.sha_ke_hoach() != goc


def test_phien_khoi_tao_duoi_quy_che_khac_het_hieu_luc(tmp_path, monkeypatch):
    goc, kh = _goc(tmp_path), KhachBatch(TRA)
    assert H.main(["hop", "--study", STUDY, "--goi-api"], client=kh, goc=goc) == 4
    monkeypatch.setattr(H, "MOC_DIEM", H.MOC_DIEM + " ")           # quy chế đổi giữa phiên
    assert H.main(["hop", "--study", STUDY, "--goi-api"], client=kh, goc=goc) == 1
    assert H.main(["hop", "--study", STUDY, "--goi-api", "--lam-lai"], client=kh, goc=goc) == 4  # họp lại từ đầu


def test_vong_kin_tu_choi_khi_chua_hieu_chuan_dat(tmp_path, capsys):
    goc, kh = _goc(tmp_path), KhachBatch({**TRA, "bt0": SUA})
    assert H.main(["vong-kin", "--study", STUDY, "--goi-api", "--ap-dung"], client=kh, goc=goc) == 3 and kh.lo == {}
    _hieu_chuan_dat(goc, do_nhay=4 / 6)                            # dưới ngưỡng 5/6
    assert H.main(["vong-kin", "--study", STUDY, "--goi-api", "--ap-dung"], client=kh, goc=goc) == 3 and kh.lo == {}
    assert "< ngưỡng" in capsys.readouterr().err
    _hieu_chuan_dat(goc)
    assert H.main(["vong-kin", "--study", STUDY, "--goi-api", "--ap-dung"], client=kh, goc=goc) == 4


def test_bien_ban_ghi_quy_che_va_hieu_luc(tmp_path):
    goc, kh = _goc(tmp_path), KhachBatch(TRA)
    for _ in range(4):
        H.main(["hop", "--study", STUDY, "--goi-api"], client=kh, goc=goc)
    H.main(["bien-ban", "--study", STUDY, "--ap-dung"], client=kh, goc=goc)
    bb = next((goc / "exports" / STUDY / H.THU_MUC).glob("BIEN_BAN_HDKH_*.md")).read_text(encoding="utf-8")
    assert H.PHIEN_BAN_QUY_CHE in bb and "Hiệu lực kết luận: CHƯA" in bb
    _hieu_chuan_dat(goc)
    H.main(["bien-ban", "--study", STUDY, "--ap-dung"], client=kh, goc=goc)
    bb = next((goc / "exports" / STUDY / H.THU_MUC).glob("BIEN_BAN_HDKH_*.md")).read_text(encoding="utf-8")
    assert "Hiệu lực kết luận: CÓ" in bb


def test_hieu_chuan_cham_tu_choi_khi_quy_che_doi(tmp_path, monkeypatch):
    goc, kh = _goc(tmp_path), KhachBatch(TRA)
    assert H.main(["hieu-chuan", "--study", STUDY, "--tao"], goc=goc) == 0
    ban = goc / "exports" / STUDY / H.THU_MUC / "hieu_chuan" / f"BAN_CAI_LOI_{STUDY}.md"
    for _ in range(4):
        H.main(["hop", "--study", STUDY, "--tep", str(ban), "--goi-api"], client=kh, goc=goc)
    monkeypatch.setattr(H, "CUA_SO_DONG", 4)
    assert H.main(["hieu-chuan", "--study", STUDY, "--cham"], goc=goc) == 1
    assert not (goc / "exports" / STUDY / H.THU_MUC / "hieu_chuan" / "ket_qua.json").exists()  # không ghi kết quả


def test_bien_tap_chia_nhom_va_nop_lai_khi_hong_het(tmp_path, monkeypatch):
    """22/11: một yêu cầu gom 14–20 vấn đề bị cắt cụt ⇒ chia nhóm ≤ 6; hỏng hết ⇒ ghi lỗi, nộp lại, tối đa 2 lần."""
    monkeypatch.setattr(H, "VAN_DE_MOI_YEU_CAU", 1)          # 2 vấn đề còn giữ ⇒ 2 yêu cầu
    goc = _goc(tmp_path)
    _hieu_chuan_dat(goc)
    kh = KhachBatch(TRA, hong={"bt0", "bt1"})
    goi = lambda: H.main(["vong-kin", "--study", STUDY, "--goi-api", "--ap-dung"], client=kh, goc=goc)  # noqa: E731
    ma = [goi() for _ in range(6)]
    assert ma[-2:] == [4, 1]                                  # nộp biên tập → hỏng hết ⇒ mã 1, lần hỏng thứ 1
    assert len(kh.lo[sorted(kh.lo)[-1]]) == 2
    st = H._doc_st(next((goc / "exports" / STUDY / H.THU_MUC).glob("trang_thai_*.json")))
    assert st["so_lan_hong_bien_tap"] == 1 and len(st["loi_bien_tap"]) == 2 and "bien_tap" not in st["batch"]
    assert [goi(), goi(), goi(), goi()] == [4, 1, 4, 1]       # nộp lại lần 1, 2 — đều hỏng
    assert goi() == 1 and len(kh.lo) == 5                     # 3 lần hỏng > 1 + 2 ⇒ dừng, không nộp thêm


def test_chon_loc_giu_thay_the_tot_loai_thay_the_lam_xau(tmp_path, monkeypatch):
    """22/11 (đo thật): hoàn nguyên cả lượt vì vài thay thế xấu đã bỏ luôn thay thế tốt ⇒ chọn lọc từng thay thế."""
    goc = _goc(tmp_path)
    _hieu_chuan_dat(goc)
    hai = {"sua": [{"id": "F01", "hanh_dong": "sua", "thay": [
        {"dong": 8, "cu": "theo Wilson", "moi": "theo Wilson; dữ liệu thiếu xử lý bằng phân tích ca đầy đủ"},
        {"dong": 10, "cu": "khoảng 50%.", "moi": "khoảng 50% (DẤU XẤU)."}]}]}
    kh = KhachBatch({**TRA, "bt0": hai})
    that = H._do_chuan

    def do_gia(van, study, out_dir, la_chinh):
        r = that(van, study, out_dir, la_chinh)
        if la_chinh and "DẤU XẤU" in van:
            r["lech"] = (r.get("lech") or 0) + 1
        return r

    monkeypatch.setattr(H, "_do_chuan", do_gia)
    p = goc / "exports" / STUDY / f"DE_CUONG_NOP_HOI_DONG_{STUDY}.md"
    for _ in range(6):
        H.main(["vong-kin", "--study", STUDY, "--goi-api", "--ap-dung"], client=kh, goc=goc)
        if "phân tích ca đầy đủ" in p.read_text(encoding="utf-8"):
            break
    van = p.read_text(encoding="utf-8")
    assert "phân tích ca đầy đủ" in van and "DẤU XẤU" not in van        # giữ tốt, loại xấu
    st = [H._doc_st(x) for x in (goc / "exports" / STUDY / H.THU_MUC).glob("trang_thai_*.json")]
    bt = next(s["bien_tap"] for s in st if s.get("bien_tap"))
    assert len(bt["nhan"]) == 1 and len(bt["loai_chon_loc"]) == 1 and "xấu đi" in bt["loai_chon_loc"][0]["ly_do_loai"]
    kh.tra = {**kh.tra, "tt_pb1": TT_DAT}
    assert _vong(goc, kh) == 0                                            # vòng 2 thông qua


# ── QC-HDKH-2.0: thẩm tra chỉnh sửa như hội đồng thật (bác sĩ 22/11/2026) ────────────────────────────────────────────
def test_khoang_sua_danh_dau_dong_doi_trong_ban_moi():
    cu = "a\nb\nc\nd\n"
    assert H.khoang_sua(cu, "a\nB\nc\nd\n") == [[2, 2]]
    assert H.khoang_sua(cu, "a\nb\nX\nY\nc\nd\n") == [[3, 4]]
    assert H.khoang_sua(cu, "a\nb\nd\n") == [[2, 2]]               # xoá dòng ⇒ dòng kề trong bản mới


def test_xac_minh_tham_tra_ba_luat_va_pham_vi_loi_moi():
    ds = [dict(PH_DUNG, id=f"F0{i}", thanh_vien="pb1") for i in range(1, 5)]
    dl = {"tham_tra": [
        {"id": "F01", "ket_qua": "da_giai_quyet", "dong": 8, "trich": "theo Wilson"},
        {"id": "F02", "ket_qua": "da_giai_quyet", "dong": 8, "trich": "câu không có trong bản đã sửa"},
        {"id": "F03", "ket_qua": "can_du_kien", "ly_do": "cần kinh phí thật"}],          # F04: không phán quyết
        "loi_moi": [{"muc_phieu": "2", "muc_do": "can_sua", "dong": 8, "trich": "theo Wilson", "van_de": "x",
                     "de_xuat": "y"},
                    {"muc_phieu": "1", "muc_do": "can_sua", "dong": 2, "trich": "phổ biến [1]", "van_de": "x",
                     "de_xuat": "y"}]}
    kq = H.xac_minh_tham_tra("pb1", dl, ds, DE_CUONG, [[7, 8]], vtq_ids=[])
    assert {k: v["ket_qua"] for k, v in kq["ket"].items()} == {
        "F01": "da_giai_quyet", "F02": "chua_giai_quyet", "F03": "chua_giai_quyet", "F04": "chua_giai_quyet"}
    assert len(kq["loi_moi"]) == 1 and "ngoài các đoạn vừa sửa" in kq["loai"][0]["ly_do_loai"]
    kq = H.xac_minh_tham_tra("pb1", dl, ds, DE_CUONG, [[7, 8]], vtq_ids=["F03"])
    assert kq["ket"]["F03"]["ket_qua"] == "can_du_kien"


@pytest.mark.parametrize("tt, mong", [
    ({"chua_giai_quyet": [{}], "loi_moi": [], "can_du_kien": []}, "chua_dat"),
    ({"chua_giai_quyet": [], "loi_moi": [{}], "can_du_kien": []}, "chua_dat"),
    ({"chua_giai_quyet": [], "loi_moi": [], "can_du_kien": [{}]}, "thong_qua_cho_du_kien"),
    ({"chua_giai_quyet": [], "loi_moi": [], "can_du_kien": []}, "thong_qua"),
])
def test_ket_luan_tham_tra_luat_co_dinh(tt, mong):
    assert H.ket_luan_tham_tra(tt)[0] == mong


def test_vong_kin_chua_giai_quyet_thi_sua_tiep_roi_tham_tra_lai(tmp_path):
    goc = _goc(tmp_path)
    _hieu_chuan_dat(goc)
    tt_chua = {"tham_tra": [{"id": "F01", "ket_qua": "chua_giai_quyet", "ly_do": "chưa có phân tích độ nhạy"}],
               "loi_moi": []}
    sua2 = {"sua": [{"id": "F01", "hanh_dong": "sua", "thay": [
        {"dong": 8, "cu": "phân tích ca đầy đủ", "moi": "phân tích ca đầy đủ, kèm phân tích độ nhạy gán đa trị"}]}]}
    kh = KhachBatch({**TRA, "bt0": SUA, "tt_pb1": tt_chua})
    p = goc / "exports" / STUDY / f"DE_CUONG_NOP_HOI_DONG_{STUDY}.md"
    goi = lambda: H.main(["vong-kin", "--study", STUDY, "--goi-api", "--ap-dung"], client=kh, goc=goc)  # noqa: E731
    assert [goi() for _ in range(6)] == [4, 0, 4, 0, 4, 0] and "phân tích ca đầy đủ" in p.read_text("utf-8")
    kh.tra["bt0"] = sua2
    assert [goi() for _ in range(4)] == [4, 0, 4, 0]          # thẩm tra: CHƯA giải quyết ⇒ biên tập lần 2
    assert "gán đa trị" in p.read_text(encoding="utf-8")
    kh.tra["tt_pb1"] = {"tham_tra": [{"id": "F01", "ket_qua": "da_giai_quyet", "dong": 8,
                                      "trich": "kèm phân tích độ nhạy gán đa trị"}], "loi_moi": []}
    assert _vong(goc, kh) == 0
    dat = [s for s in (H._doc_st(x) for x in (goc / "exports" / STUDY / H.THU_MUC).glob("trang_thai_*.json"))
           if s.get("buoc") == "dat"]
    assert len(dat) == 1 and dat[0]["vong"] == 3 and dat[0]["ket_luan_cuoi"] == "thong_qua"


def test_vong_kin_can_du_kien_thong_qua_kem_danh_sach(tmp_path):
    goc = _goc(tmp_path)
    _hieu_chuan_dat(goc)
    sua_vtq = {"sua": [{"id": "F01", "hanh_dong": "vuot_tham_quyen", "ly_do": "cần quyết định của thống kê viên"},
                       {"id": "F03", "hanh_dong": "sua", "thay": [
                           {"dong": 8, "cu": "theo Wilson", "moi": "theo Wilson (khoảng tin cậy hai phía)"}]}]}
    tt_dk = {"tham_tra": [{"id": "F01", "ket_qua": "can_du_kien", "ly_do": "thống kê viên quyết cách xử lý thiếu"}],
             "loi_moi": []}
    kh = KhachBatch({**TRA, "bt0": sua_vtq, "tt_pb1": tt_dk})
    assert _vong(goc, kh) == 0
    out = goc / "exports" / STUDY / H.THU_MUC
    dat = [s for s in (H._doc_st(x) for x in out.glob("trang_thai_*.json")) if s.get("buoc") == "dat"][0]
    assert dat["ket_luan_cuoi"] == "thong_qua_cho_du_kien"
    bb = H.bien_ban_md(dat)
    assert "Thông qua phần thuộc thẩm quyền" in bb and "Cần dữ kiện" in bb and "thống kê viên" in bb
    assert "Kết quả thẩm tra từng yêu cầu" in bb and "| F01" in bb


def test_ket_luan_cong_don_can_du_kien_cua_vong_truoc():
    # Vòng 2: F01 cần dữ kiện, F03 chưa giải quyết ⇒ vòng 3 chỉ thẩm tra F03; F03 giải quyết xong KHÔNG được thành
    # «thông qua» trơn — F01 vẫn chờ dữ kiện của người có thẩm quyền.
    st = {"che_do": "tham_tra", "can_du_kien_truoc": [dict(PH_DUNG, id="F01")],
          "tham_tra": {"da_giai_quyet": [dict(PH_DUNG, id="F03")], "chua_giai_quyet": [], "can_du_kien": [],
                       "loi_moi": [], "loai": []}}
    assert H.ket_luan_tham_tra(H.tham_tra_cong_don(st))[0] == "thong_qua_cho_du_kien"
    st["can_du_kien_truoc"] = []
    assert H.ket_luan_tham_tra(H.tham_tra_cong_don(st))[0] == "thong_qua"


def test_tham_tra_loai_loi_moi_co_pii():
    ds = [dict(PH_DUNG, id="F01", thanh_vien="pb1")]
    dl = {"tham_tra": [], "loi_moi": [{"muc_phieu": "2", "muc_do": "can_sua", "dong": 8, "trich": "theo Wilson",
                                       "van_de": "gọi 0912345678 để hỏi", "de_xuat": "y"}]}
    kq = H.xac_minh_tham_tra("pb1", dl, ds, DE_CUONG, [[7, 8]], vtq_ids=[])
    assert not kq["loi_moi"] and "PII" in kq["loai"][0]["ly_do_loai"]


# ── QC-HDKH-2.1 (22/11/2026, đo thật dưới 2.0) ────────────────────────────────────────────────────────────────────────
def _buoc(goc, kh):
    return H.main(["vong-kin", "--study", STUDY, "--goi-api", "--ap-dung"], client=kh, goc=goc)


def _cac_st(goc):
    return [H._doc_st(x) for x in (goc / "exports" / STUDY / H.THU_MUC).glob("trang_thai_*.json")]


def test_phan_hoi_tham_tra_hong_thi_nop_lai_khong_tinh_la_phan_quyet(tmp_path):
    goc = _goc(tmp_path)
    _hieu_chuan_dat(goc)
    kh = KhachBatch({**TRA, "bt0": SUA, "tt_pb1": TT_DAT})
    assert [_buoc(goc, kh) for _ in range(6)] == [4, 0, 4, 0, 4, 0]
    kh.hong = {"tt_pb1"}
    assert _buoc(goc, kh) == 4                      # nộp batch thẩm tra
    assert _buoc(goc, kh) == 4                      # phản hồi hỏng ⇒ NỘP LẠI riêng pb1, không ra phán quyết
    assert kh.lo[max(kh.lo, key=lambda b: int(b.split("_")[1]))] == [c for c in kh.yc if c.startswith("tt_pb1_")]
    kh.hong = set()
    assert _vong(goc, kh) == 0
    dat = [s for s in _cac_st(goc) if s.get("buoc") == "dat"][0]
    assert dat["ket_luan_cuoi"] == "thong_qua" and dat["so_lan_nop_lai_tt"] == 1 and len(dat["loi_tham_tra"]) == 1


def test_phan_hoi_tham_tra_hong_qua_so_lan_thi_fail_safe(tmp_path):
    goc = _goc(tmp_path)
    _hieu_chuan_dat(goc)
    kh = KhachBatch({**TRA, "bt0": SUA, "tt_pb1": TT_DAT}, hong={"tt_pb1"})
    assert [_buoc(goc, kh) for _ in range(6)] == [4, 0, 4, 0, 4, 0]
    assert [_buoc(goc, kh) for _ in range(4)] == [4, 4, 4, 0]   # nộp · nộp lại 1 · nộp lại 2 · hết lượt ⇒ fail-safe
    st = [s for s in _cac_st(goc) if s.get("che_do") == "tham_tra"][0]
    chua = st["tham_tra"]["chua_giai_quyet"]
    assert [f["id"] for f in chua] == ["F01"] and "thẩm tra hỏng" in chua[0]["ly_do_tham_tra"]


def test_ly_do_rao_loai_va_ly_do_tham_tra_toi_bien_tap_vien(tmp_path):
    goc = _goc(tmp_path)
    _hieu_chuan_dat(goc)
    sua = {"sua": [{"id": "F01", "hanh_dong": "sua", "thay": [
        SUA["sua"][0]["thay"][0],
        {"dong": 5, "cu": "Người bệnh không đồng ý tham gia.", "moi": "Người bệnh không đồng ý tham gia (37%)."}]}]}
    kh = KhachBatch({**TRA, "bt0": sua,
                     "tt_pb1": {"tham_tra": [{"id": "F01", "ket_qua": "chua_giai_quyet",
                                              "ly_do": "chưa nêu cách xử lý dữ liệu thiếu ở biến phụ"}],
                                "loi_moi": []}})
    assert [_buoc(goc, kh) for _ in range(6)] == [4, 0, 4, 0, 4, 0]
    st = [s for s in _cac_st(goc) if s.get("che_do") == "tham_tra"][0]
    f01 = [f for f in st["ds_yeu_cau"] if f["id"] == "F01"][0]
    assert f01["rao_loai"] and "số mới" in f01["rao_loai"][0]
    assert [_buoc(goc, kh) for _ in range(3)] == [4, 0, 4]       # thẩm tra · đọc · nộp biên tập lần 2
    loi = json.dumps(kh.yc[[c for c in kh.yc if c.startswith("bt0_")][-1]], ensure_ascii=False)
    assert "rao_loai" in loi and "số mới" in loi and "chưa nêu cách xử lý dữ liệu thiếu ở biến phụ" in loi


def test_nop_lai_chi_thanh_vien_hong_giu_ket_qua_nguoi_da_doc_duoc(tmp_path):
    goc = _goc(tmp_path)
    _hieu_chuan_dat(goc)
    ct = {"phan_quyet": [], "gop": [], "nhan_xet_chung": "Cần bổ sung.", "yeu_cau_chinh_sua": ["dữ liệu thiếu"]}
    sua = {"sua": [SUA["sua"][0], {"id": "F02", "hanh_dong": "sua", "thay": [
        {"dong": 5, "cu": "Người bệnh không đồng ý tham gia.",
         "moi": "Người bệnh không đồng ý tham gia; người thiếu dữ liệu kết cục được mô tả riêng."}]}]}
    tt2 = {"tham_tra": [{"id": "F02", "ket_qua": "da_giai_quyet", "dong": 5,
                         "trich": "người thiếu dữ liệu kết cục được mô tả riêng"}], "loi_moi": []}
    kh = KhachBatch({**TRA, "ct": ct, "bt0": sua, "tt_pb1": TT_DAT, "tt_uv_tk": tt2})
    assert [_buoc(goc, kh) for _ in range(6)] == [4, 0, 4, 0, 4, 0]
    kh.hong = {"tt_uv_tk"}
    assert [_buoc(goc, kh) for _ in range(2)] == [4, 4]          # nộp · uv_tk hỏng ⇒ nộp lại riêng uv_tk
    kh.hong = set()
    assert _vong(goc, kh) == 0
    dat = [s for s in _cac_st(goc) if s.get("buoc") == "dat"][0]
    assert dat["ket_luan_cuoi"] == "thong_qua"
    assert sorted(f["id"] for f in dat["tham_tra"]["da_giai_quyet"]) == ["F01", "F02"]
