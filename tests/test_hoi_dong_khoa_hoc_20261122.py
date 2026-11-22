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
       "uv_ctk": _tv(diem=4),   # QC-3.0: ghế chuyên thiết kế (đề tài mẫu là cắt ngang)
       "ct": {"phan_quyet": [{"id": "F02", "quyet": "loai", "ly_do": "trùng F01"}], "gop": [],
              "nhan_xet_chung": "Đề cương rõ, cần bổ sung xử lý dữ liệu thiếu.",
              "yeu_cau_chinh_sua": ["dữ liệu thiếu"]}}


def test_tron_quy_trinh_hai_buoc_va_bien_ban(tmp_path):
    goc, kh = _goc(tmp_path), KhachBatch(TRA)
    assert H.main(["hop", "--study", STUDY], client=kh, goc=goc) == 0 and kh.lo == {}   # chạy khô: không nộp
    assert H.main(["hop", "--study", STUDY, "--goi-api"], client=kh, goc=goc) == 4       # nộp batch thành viên
    p_tv = [kh.yc[c] for c in kh.lo["msgbatch_0"]]
    assert len(p_tv) == 6 and len({json.dumps(p["system"], ensure_ascii=False) for p in p_tv}) == 1  # 5 + ghế thiết kế
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
    hc = goc / "exports" / STUDY / H.THU_MUC / "hieu_chuan" / "de_cuong"
    assert json.loads((hc / "dap_an.json").read_text("utf-8"))["dap_an"]


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
SACH = {**{m: _tv(diem=5) for m in ("pb1", "pb2", "uv_tk", "uv_dd", "uv_tl", "uv_ctk")},
        "ct": {"phan_quyet": [], "gop": [], "nhan_xet_chung": "Đạt.", "yeu_cau_chinh_sua": []}}


def _hieu_chuan_dat(goc, do_nhay=1.0, bao_nham=True, loai="de_cuong", ket_hop=True):
    """Kết quả hiệu chuẩn HỢP LỆ dưới quy chế hiện hành (điều kiện tiên quyết của vòng kín): độ nhạy + báo nhầm."""
    hc = goc / "exports" / STUDY / H.THU_MUC / "hieu_chuan" / loai
    H._ghi_json(hc / "ket_qua.json", {"sha_quy_che": H.sha_ke_hoach(), "do_nhay": do_nhay, "bat": round(7 * do_nhay),
                                      "so_loi_cai": 7, "bat_dac_thu": True, "ket_hop": ket_hop})
    if bao_nham:
        H._ghi_json(hc / "bao_nham.json", {"sha_quy_che": H.sha_ke_hoach(), "dat": True, "do_chinh_xac": 0.9,
                                           "model_trong_tai": H.TRONG_TAI_MODEL, "doi_chung_dung": 10,
                                           "so_doi_chung": 10, "ly_do": "đạt"})


def _vong(goc, kh, n=12):
    ma = None
    for _ in range(n):
        ma = H.main(["vong-kin", "--chi-api", "--study", STUDY, "--goi-api", "--ap-dung"], client=kh, goc=goc)
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
        H.main(["vong-kin", "--chi-api", "--study", STUDY, "--goi-api", "--ap-dung"], client=kh, goc=goc)
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
    vk = ["vong-kin", "--chi-api", "--study", STUDY, "--goi-api", "--ap-dung"]
    ma = [H.main(vk, client=kh, goc=goc) for _ in range(6)]
    assert 1 in ma and p.read_text(encoding="utf-8") == goc_van  # đã hoàn nguyên, không để bản xấu đi


def test_vong_kin_dung_sau_so_vong_toi_da(tmp_path, monkeypatch):
    goc, kh = _goc(tmp_path), KhachBatch({**TRA, "bt0": SUA})
    monkeypatch.setattr(H, "SO_VONG_TOI_DA", 1)
    _hieu_chuan_dat(goc)   # hiệu chuẩn tính dưới quy chế ĐÃ đổi số vòng — SHA phải tính sau khi vá
    # 4 lượt họp (nộp/lấy thành viên, nộp/lấy chủ tịch) + lượt 5 xét điều kiện dừng ở «xong»
    vk = ["vong-kin", "--chi-api", "--study", STUDY, "--goi-api", "--ap-dung"]
    ma = [H.main(vk, client=kh, goc=goc) for _ in range(5)]
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
    assert H.main(["vong-kin", "--chi-api", "--study", STUDY, "--goi-api", "--ap-dung"],
                  client=kh, goc=goc) == 3 and kh.lo == {}
    _hieu_chuan_dat(goc, do_nhay=4 / 6)                            # dưới ngưỡng 5/6
    assert H.main(["vong-kin", "--chi-api", "--study", STUDY, "--goi-api", "--ap-dung"],
                  client=kh, goc=goc) == 3 and kh.lo == {}
    assert "< ngưỡng" in capsys.readouterr().err
    _hieu_chuan_dat(goc)
    assert H.main(["vong-kin", "--chi-api", "--study", STUDY, "--goi-api", "--ap-dung"], client=kh, goc=goc) == 4


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
    ban = goc / "exports" / STUDY / H.THU_MUC / "hieu_chuan" / "de_cuong" / f"BAN_CAI_LOI_{STUDY}_de_cuong.md"
    for _ in range(4):
        H.main(["hop", "--study", STUDY, "--tep", str(ban), "--goi-api"], client=kh, goc=goc)
    monkeypatch.setattr(H, "CUA_SO_DONG", 4)
    assert H.main(["hieu-chuan", "--study", STUDY, "--cham"], goc=goc) == 1
    assert not (ban.parent / "ket_qua.json").exists()  # không ghi kết quả


def test_bien_tap_chia_nhom_va_nop_lai_khi_hong_het(tmp_path, monkeypatch):
    """22/11: một yêu cầu gom 14–20 vấn đề bị cắt cụt ⇒ chia nhóm ≤ 6; hỏng hết ⇒ ghi lỗi, nộp lại, tối đa 2 lần."""
    monkeypatch.setattr(H, "VAN_DE_MOI_YEU_CAU", 1)          # 2 vấn đề còn giữ ⇒ 2 yêu cầu
    goc = _goc(tmp_path)
    _hieu_chuan_dat(goc)
    kh = KhachBatch(TRA, hong={"bt0", "bt1"})
    goi = lambda: H.main(["vong-kin", "--chi-api", "--study", STUDY, "--goi-api", "--ap-dung"], client=kh, goc=goc)  # noqa: E731
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
        H.main(["vong-kin", "--chi-api", "--study", STUDY, "--goi-api", "--ap-dung"], client=kh, goc=goc)
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
    goi = lambda: H.main(["vong-kin", "--chi-api", "--study", STUDY, "--goi-api", "--ap-dung"], client=kh, goc=goc)  # noqa: E731
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
    return H.main(["vong-kin", "--chi-api", "--study", STUDY, "--goi-api", "--ap-dung"], client=kh, goc=goc)


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


# ── QC-HDKH-3.0 (bác sĩ 22/11/2026 duyệt bốn việc) ───────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("tk", ["rct", "cohort", "case_control", "cross_sectional", "diagnostic", "sr_ma",
                                "prediction", "qualitative"])
def test_ghe_chuyen_thiet_ke_cho_du_tam_thiet_ke(tk):
    ds = H.thanh_phan_hoi_dong(tk, "đề cương")
    assert [t["ma"] for t in ds] == ["pb1", "pb2", "uv_tk", "uv_dd", "uv_tl", "uv_ctk"]
    assert ds[-1]["vai"] == H.GHE_THIET_KE[tk]["vai"] and H.tuc_so(len(ds)) == 4


def test_bi_danh_thiet_ke_ghe_kinh_te_va_tuc_so():
    assert H.thanh_phan_hoi_dong("diagnostic_accuracy", "")[-1]["vai"] == H.GHE_THIET_KE["diagnostic"]["vai"]
    assert [t["ma"] for t in H.thanh_phan_hoi_dong("", "")] == ["pb1", "pb2", "uv_tk", "uv_dd", "uv_tl"]
    ds = H.thanh_phan_hoi_dong("rct", "Phân tích chi phí–hiệu quả, tính ICER theo QALY.")
    assert [t["ma"] for t in ds][-2:] == ["uv_ctk", "uv_kt"] and H.tuc_so(len(ds)) == 4
    assert (H.tuc_so(5), H.tuc_so(6), H.tuc_so(7)) == (3, 4, 4)


def test_ho_so_kinh_te_them_cheers_va_noi_ro_chua_do():
    hs = H.ho_so_kiem_may("X", Path("/khong-co"), "Tính ICER và QALY.", False)
    assert "CHEERS 2022" in hs["chuan_ap_dung"] and "CHƯA đo" in hs["cheers_2022"]


SAP_MAU = """# SAP
### §1 QUẦN THỂ PHÂN TÍCH
Phân tích theo ý định điều trị.
### §2 KẾT CỤC
Kết cục chính là tỷ lệ kiểm soát huyết áp.
### §4 PHÂN TÍCH CHÍNH
Hồi quy Poisson với phương sai mạnh.
### §6 DỮ LIỆU THIẾU
Gán đa trị 20 bộ.
### §8 ĐA SO SÁNH
Holm cho kết cục phụ.
### §9 PHÂN TÍCH ĐỘ NHẠY
Phân tích ca đầy đủ.
### §10 PHẦN MỀM + SEED
R 4.4.
"""
BAN_THAO_MAU = """# Bài báo
## I. GIỚI THIỆU
Tăng huyết áp phổ biến [1].
## II. PHƯƠNG PHÁP
### Phân tích thống kê
Hồi quy Poisson.
## III. KẾT QUẢ
Có 412 người tham gia.
## IV. BÀN LUẬN
Kết quả tương tự [2].
## V. KẾT LUẬN
Can thiệp cải thiện kiểm soát huyết áp.
## KHAI BÁO
Không có xung đột lợi ích.
"""


@pytest.mark.parametrize("loai, van, so", [("sap", SAP_MAU, 6), ("ban_thao", BAN_THAO_MAU, 6),
                                          ("bao_cao", BAN_THAO_MAU, 6)])
def test_loi_cai_theo_loai_tai_lieu(loai, van, so):
    moi, da = H.cai_loi(van, loai)
    assert len(da) == so and len({d["ma"] for d in da}) == so
    dong = moi.splitlines()
    assert all(dong[d["dong"] - 1] == d["cau"] for d in da) and not any(d["dac_thu_thiet_ke"] for d in da)


def test_loi_dac_thu_thiet_ke_chi_cho_de_cuong_co_thiet_ke():
    van = DE_CUONG + "### 2.3. Phân bổ ngẫu nhiên\nKhối ngẫu nhiên kích thước 4.\n"
    moi, da = H.cai_loi(van, "de_cuong", "rct")
    dt_ = [d for d in da if d["dac_thu_thiet_ke"]]
    assert [d["ma"] for d in dt_] == ["tk_phan_bo_lo"] and moi.splitlines()[dt_[0]["dong"] - 1] == dt_[0]["cau"]
    assert not any(d["dac_thu_thiet_ke"] for d in H.cai_loi(van, "de_cuong", "")[1])
    assert not any(d["dac_thu_thiet_ke"] for d in H.cai_loi(SAP_MAU, "sap", "rct")[1])


def test_tep_mac_dinh_theo_loai():
    assert H.tep_mac_dinh("A", Path("/g"), "sap").name == "G4_A5_SAP_FINAL_A.md"
    assert H.tep_mac_dinh("A", Path("/g"), "ban_thao").name == "G7_A8_MANUSCRIPT_A.md"
    assert H.tep_mac_dinh("A", Path("/g")).name == "DE_CUONG_NOP_HOI_DONG_A.md"


def test_loi_nhan_theo_loai_dung_phieu_rieng():
    tv = H.THANH_VIEN[2]
    assert "Gamble" not in H.loi_nhan_thanh_vien(tv)
    sap = H.loi_nhan_thanh_vien(tv, "sap")
    assert H.LOAI_TAI_LIEU["sap"]["phieu"]["2"] in sap and "ĐỀ XUẤT SỬA ĐỔI SAP" in sap
    assert "  3. Kết quả" in H.loi_nhan_thanh_vien(tv, "bao_cao")


def _kq(do_nhay=1.0, so=7, dac_thu=True):
    return {"sha_quy_che": H.sha_ke_hoach(), "do_nhay": do_nhay, "bat": round(so * do_nhay), "so_loi_cai": so,
            "bat_dac_thu": dac_thu}


@pytest.mark.parametrize("kq, bn, mong", [
    (_kq(), {"dat": True}, True),
    (_kq(), None, False),                                   # chưa đo báo nhầm ⇒ chưa có hiệu lực
    (_kq(), {"dat": False, "ly_do": "x"}, False),
    (_kq(dac_thu=False), {"dat": True}, False),             # sót lỗi đặc thù thiết kế
    (_kq(so=4, do_nhay=1.0), {"dat": True}, False),         # < 5 lỗi cài ⇒ hiệu chuẩn không hợp lệ
    (_kq(do_nhay=5 / 7), {"dat": True}, False),
])
def test_hieu_luc_can_ca_do_nhay_dac_thu_va_bao_nham(tmp_path, kq, bn, mong):
    hc = tmp_path / H.THU_MUC / "hieu_chuan" / "de_cuong"
    H._ghi_json(hc / "ket_qua.json", kq)
    if bn is not None:
        H._ghi_json(hc / "bao_nham.json", {**bn, "sha_quy_che": H.sha_ke_hoach()})
    assert H.hieu_luc_hieu_chuan(tmp_path)[0] is mong


def test_doi_chung_am_chi_dung_khi_muc_co_noi_dung():
    van = "# A\n## 2.3. Cỡ mẫu\nn = 100.\nTính theo công thức một tỷ lệ.\n## 2.4. Đạo đức\n## 2.5. Biến số\nx\n"
    dc = H.doi_chung_am(van)
    assert [d["dong"] for d in dc] == [2] and "cỡ mẫu" in dc[0]["van_de"] and dc[0]["nhom"] == "kiem_soat_am"


def test_xac_minh_trong_tai_sai_phai_chung_minh():
    muc = [{"id": f"M0{i}"} for i in range(1, 6)]
    dl = {"phan_dinh": [
        {"id": "M01", "ket_qua": "sai", "co_so": "tai_lieu_da_dap_ung", "dong": 8, "trich": "theo Wilson"},
        {"id": "M02", "ket_qua": "sai", "co_so": "tai_lieu_da_dap_ung", "dong": 8, "trich": "không có câu này"},
        {"id": "M03", "ket_qua": "sai", "co_so": "chuan_khong_doi", "ly_do": ""},
        {"id": "M04", "ket_qua": "dung", "ly_do": "thiếu thật"}]}                   # M05: thiếu phán quyết
    pd = H.xac_minh_trong_tai(dl, muc, DE_CUONG)
    assert [pd[f"M0{i}"]["ket_qua"] for i in range(1, 6)] == ["sai", "khong_ro", "khong_ro", "dung", "khong_ro"]


def _muc(nhom, n):
    return [{"id": f"{nhom}{i}", "nhom": nhom} for i in range(n)]


def test_cham_bao_nham_trong_tai_hop_le_do_chinh_xac_va_khong_ro():
    muc = _muc("kiem_soat_duong", 6) + _muc("kiem_soat_am", 4) + _muc("nghi_van", 10)
    pd = {m["id"]: {"ket_qua": {"kiem_soat_duong": "dung", "kiem_soat_am": "sai", "nghi_van": "dung"}[m["nhom"]]}
          for m in muc}
    for i in range(2):
        pd[f"nghi_van{i}"]["ket_qua"] = "sai"
    kq = H.cham_bao_nham(muc, pd)
    assert kq["trong_tai_hop_le"] and kq["do_chinh_xac"] == 0.8 and kq["dat"]
    assert kq["khoang_tin_cay_95"] == H._wilson(8, 10) and len(kq["sai_chi_tiet"]) == 2
    pd["kiem_soat_am0"]["ket_qua"] = pd["kiem_soat_am1"]["ket_qua"] = "dung"   # trọng tài sai 2/10 đối chứng
    assert not H.cham_bao_nham(muc, pd)["trong_tai_hop_le"] and not H.cham_bao_nham(muc, pd)["dat"]
    pd["kiem_soat_am0"]["ket_qua"] = pd["kiem_soat_am1"]["ket_qua"] = "sai"
    for i in range(6):
        pd[f"nghi_van{i}"]["ket_qua"] = "khong_ro"
    assert not H.cham_bao_nham(muc, pd)["dat"]                                  # không rõ quá nửa ⇒ không đo được
    pd = {m["id"]: {"ket_qua": "dung" if m["nhom"] != "kiem_soat_am" else "sai"} for m in muc}
    for i in range(3):
        pd[f"nghi_van{i}"]["ket_qua"] = "sai"
    assert H.cham_bao_nham(muc, pd)["do_chinh_xac"] == 0.7 and not H.cham_bao_nham(muc, pd)["dat"]


def test_wilson():
    assert H._wilson(0, 0) is None and H._wilson(8, 10) == [0.49, 0.943]


def _hop_ban_cai_loi(goc, kh, loai="de_cuong"):
    hc = goc / "exports" / STUDY / H.THU_MUC / "hieu_chuan" / loai
    ban = hc / f"BAN_CAI_LOI_{STUDY}_{loai}.md"
    da = json.loads((hc / "dap_an.json").read_text(encoding="utf-8"))["dap_an"]
    ph = [{"muc_phieu": "2", "muc_do": "can_sua", "dong": d["dong"], "trich": d["cau"][:40], "van_de": d["mo_ta"],
           "chuan": "", "de_xuat": "sửa"} for d in da]
    dong = ban.read_text(encoding="utf-8").splitlines()
    k = next(i for i, x in enumerate(dong, 1) if x.startswith("Tăng huyết áp"))
    ph.append({"muc_phieu": "1", "muc_do": "goi_y", "dong": k, "trich": "Tăng huyết áp", "van_de": "nên dẫn số liệu "
               "trong nước", "chuan": "", "de_xuat": "thêm"})
    kh.tra.update({m: _tv(diem=3, phat_hien=ph if m == "pb1" else []) for m in
                   ("pb1", "pb2", "uv_tk", "uv_dd", "uv_tl", "uv_ctk")})
    kh.tra["ct"] = {"phan_quyet": [], "gop": [], "nhan_xet_chung": "x", "yeu_cau_chinh_sua": []}
    for _ in range(4):
        H.main(["hop", "--study", STUDY, "--loai", loai, "--tep", str(ban), "--goi-api"], client=kh, goc=goc)
    return hc


def test_do_bao_nham_dau_cuoi_roi_moi_co_hieu_luc(tmp_path):
    goc, kh = _goc(tmp_path), KhachBatch({})
    assert H.main(["hieu-chuan", "--study", STUDY, "--tao"], goc=goc) == 0
    hc = _hop_ban_cai_loi(goc, kh)
    assert H.main(["hieu-chuan", "--study", STUDY, "--cham"], goc=goc) == 0
    out = goc / "exports" / STUDY
    assert not H.hieu_luc_hieu_chuan(out)[0]                          # mới có độ nhạy, CHƯA đo báo nhầm
    assert H.main(["do-bao-nham", "--study", STUDY, "--trong-tai", "api"], client=kh, goc=goc) == 0
    assert not kh.lo.get("msgbatch_4")
    assert H.main(["do-bao-nham", "--study", STUDY, "--trong-tai", "api", "--goi-api"], client=kh, goc=goc) == 4
    tt = json.loads((hc / "bao_nham_trang_thai.json").read_text(encoding="utf-8"))
    assert {m["nhom"] for m in tt["muc"]} == {"kiem_soat_duong", "kiem_soat_am", "nghi_van"}
    p_tt = [p for c, p in kh.yc.items() if c.startswith("tt_bn_")][0]
    assert p_tt["model"] == H.TRONG_TAI_MODEL != H.MODEL_MAC_DINH
    assert "kiem_soat" not in json.dumps(p_tt, ensure_ascii=False)       # trọng tài KHÔNG thấy nhóm (mù)
    kh.tra["tt_bn"] = {"phan_dinh": [
        {"id": m["id"], "ket_qua": "sai" if m["nhom"] == "kiem_soat_am" else "dung",
         "co_so": "tai_lieu_da_dap_ung" if m["nhom"] == "kiem_soat_am" else "", "dong": m["dong"],
         "trich": m["trich"], "ly_do": "đối chiếu tài liệu"} for m in tt["muc"]]}
    assert H.main(["do-bao-nham", "--study", STUDY, "--trong-tai", "api", "--goi-api"], client=kh, goc=goc) == 0
    bn = json.loads((hc / "bao_nham.json").read_text(encoding="utf-8"))
    assert bn["dat"] and bn["trong_tai_hop_le"] and bn["do_chinh_xac"] == 1.0
    assert bn["model_trong_tai"] == "claude-fable-5-2"
    assert H.hieu_luc_hieu_chuan(out)[0]


def test_vong_kin_tu_choi_loai_khong_phai_de_cuong(tmp_path, capsys):
    goc = _goc(tmp_path)
    (goc / "exports" / STUDY / f"G4_A5_SAP_FINAL_{STUDY}.md").write_text(SAP_MAU, encoding="utf-8", newline="\n")
    _hieu_chuan_dat(goc, loai="sap")
    assert H.main(["vong-kin", "--chi-api", "--study", STUDY, "--loai", "sap", "--goi-api"],
                  client=KhachBatch({}), goc=goc) == 3
    assert "chỉ được THẨM ĐỊNH" in capsys.readouterr().err


def test_hop_sap_dung_phieu_va_chuan_sap(tmp_path):
    goc = _goc(tmp_path)
    (goc / "exports" / STUDY / f"G4_A5_SAP_FINAL_{STUDY}.md").write_text(SAP_MAU, encoding="utf-8", newline="\n")
    kh = KhachBatch(TRA)
    assert H.main(["hop", "--study", STUDY, "--loai", "sap", "--goi-api"], client=kh, goc=goc) == 4
    p = next(iter(kh.yc.values()))
    he = json.dumps(p["system"], ensure_ascii=False)
    assert "kế hoạch phân tích thống kê (SAP)" in he and "Gamble 2017" in he
    assert H.LOAI_TAI_LIEU["sap"]["phieu"]["1"] in p["messages"][0]["content"]
    st = next(H._doc_st(x) for x in (goc / "exports" / STUDY / H.THU_MUC).glob("trang_thai_*.json"))
    assert st["loai"] == "sap" and st["ho_so"]["chuan_ap_dung"][:3] == [
        "Gamble 2017 (nội dung SAP, PMID 29260229)", "ICH E9(R1)", "SAMPL"]


def test_neo_du_phong_khi_thieu_de_muc_chinh():
    van = BAN_THAO_MAU.replace("### Phân tích thống kê\n", "")
    moi, da = H.cai_loi(van, "ban_thao")
    kd = [d for d in da if d["ma"] == "kiem_dinh_sai"]
    assert kd and moi.splitlines()[kd[0]["dong"] - 2].startswith("## II. PHƯƠNG PHÁP")


def test_hieu_luc_bao_nham_duoi_quy_che_khac_khong_tinh(tmp_path):
    hc = tmp_path / H.THU_MUC / "hieu_chuan" / "de_cuong"
    H._ghi_json(hc / "ket_qua.json", _kq())
    H._ghi_json(hc / "bao_nham.json", {"dat": True, "sha_quy_che": "khac"})
    assert not H.hieu_luc_hieu_chuan(tmp_path)[0]


def test_cham_hieu_chuan_sot_loi_dac_thu(tmp_path):
    goc = _goc(tmp_path)
    p = goc / "exports" / STUDY / f"DE_CUONG_NOP_HOI_DONG_{STUDY}.md"
    p.write_text(DE_CUONG + "### 2.2. Cỡ mẫu và chọn mẫu\nChọn mẫu thuận tiện.\nCỡ mẫu 300.\n", encoding="utf-8",
                 newline="\n")
    assert H.main(["hieu-chuan", "--study", STUDY, "--tao"], goc=goc) == 0
    hc = goc / "exports" / STUDY / H.THU_MUC / "hieu_chuan" / "de_cuong"
    da = json.loads((hc / "dap_an.json").read_text(encoding="utf-8"))["dap_an"]
    assert [d["ma"] for d in da if d["dac_thu_thiet_ke"]] == ["tk_mau_lech"]       # đề tài mẫu: cắt ngang
    goc_da = [d for d in da if not d["dac_thu_thiet_ke"]]
    (hc / "dap_an.json").write_text(json.dumps({**json.loads((hc / "dap_an.json").read_text("utf-8")),
                                                "dap_an": goc_da}, ensure_ascii=False), encoding="utf-8",
                                    newline="\n")
    kh = KhachBatch({})
    _hop_ban_cai_loi(goc, kh)                       # hội đồng chỉ bắt các lỗi chung, KHÔNG bắt lỗi đặc thù
    (hc / "dap_an.json").write_text(json.dumps({**json.loads((hc / "dap_an.json").read_text("utf-8")),
                                                "dap_an": da}, ensure_ascii=False), encoding="utf-8",
                                    newline="\n")
    assert H.main(["hieu-chuan", "--study", STUDY, "--cham"], goc=goc) == 1
    kq = json.loads((hc / "ket_qua.json").read_text(encoding="utf-8"))
    assert kq["bat_dac_thu"] is False and kq["do_nhay"] >= H.DO_NHAY_TOI_THIEU and not kq["dat"]


# ── QC-HDKH-4.0: kết hợp Claude API + công cụ của hệ + agent Claude Code (bác sĩ 22/11/2026) ─────────────────────────
def test_ghe_mang_doctrine_agent_tu_ban_chup_khoa():
    ds = H.thanh_phan_hoi_dong("rct", "", "sap")
    tac = {t["ma"]: t["tac_nhan"] for t in ds}
    assert tac["uv_tk"] == ["co-mau-nghien-cuu", "phan-tich-thong-ke", "thiet-ke-nghien-cuu"]
    assert tac["uv_ctk"] == ["an-toan-nghien-cuu"] and tac["pb1"] == ["thiet-ke-nghien-cuu"]
    ln = H.loi_nhan_thanh_vien(ds[2], "sap", {"co-mau-nghien-cuu": {"doctrine": "LUẬT-RIÊNG-CỠ-MẪU"}})
    assert "LUẬT-RIÊNG-CỠ-MẪU" in ln and "KHÔNG có trong bản chụp" in ln      # agent thiếu ⇒ nói rõ, không bịa
    assert H.doc_doctrine() and all(v["doctrine"] for v in H.doc_doctrine().values())


def test_trich_doctrine_giu_luat_bo_thao_tac():
    van = ("---\nname: x\n---\n## 🤖 BƯỚC 0 — FULL AUTO\nlệnh\n## Luật nền\nKHÔNG bịa effect size.\n"
           "## Mẫu đầu ra theo tiêu chí\nkhuôn\n## Bài học giả lập\nđo thật.\n")
    d = H.trich_doctrine(van)
    assert "KHÔNG bịa effect size" in d and "đo thật" in d and "khuôn" not in d and "lệnh" not in d


def test_bang_chung_he_tu_checkpoint_va_bien_nhan(tmp_path):
    assert "không có checkpoint" in H.bang_chung_he("X", tmp_path)["ghi_chu"]
    H._ghi_json(tmp_path / "G3_checkpoint.json", {"design_code": "cross_sectional", "alpha": 0.05, "n_adjusted": 385})
    H._ghi_json(tmp_path / "A12_METADATA_RECEIPT.json", {"pmids_checked": ["1", "2"], "all_resolved": True})
    H._ghi_json(tmp_path / "A12_RETRACTION_RECEIPT.json", {"all_clean": False, "results": {
        "1": {"status": "ok"}, "2": {"status": "retracted"}}})
    bc = H.bang_chung_he("X", tmp_path)
    assert bc["co_mau_g3"]["n_adjusted"] == 385 and bc["trich_dan_a12"]["pmid_co_van_de"] == {"2": "retracted"}


def test_cau_truc_bao_cao_theo_huong_dan():
    bc = ("# Danh sách cán bộ tham gia\n# Mục lục\n# Danh mục chữ viết tắt\n# Danh mục bảng\n# ĐẶT VẤN ĐỀ\nx\n"
          "# CHƯƠNG 1. TỔNG QUAN TÀI LIỆU\n# CHƯƠNG 2. ĐỐI TƯỢNG VÀ PHƯƠNG PHÁP NGHIÊN CỨU\n# CHƯƠNG 3. KẾT QUẢ\n"
          "# CHƯƠNG 4. BÀN LUẬN\n# KẾT LUẬN\n" + "chữ " * 1000 + "\n# TÀI LIỆU THAM KHẢO\n# PHỤ LỤC\n")
    kq = H.kiem_cau_truc_bao_cao(bc)
    assert kq["thieu"] == ["Khuyến nghị"] and any("kết luận ~" in x for x in kq["canh_bao"])
    assert H.LOAI_TAI_LIEU["bao_cao"]["phieu"]["3"] == "Kết quả nghiên cứu"
    assert H.LOAI_TAI_LIEU["bao_cao"]["phieu"]["4"].startswith("Chất lượng của Báo cáo tổng hợp")


VAN_KHOA = """# ĐỀ CƯƠNG
## 2.6.5. Xử lý và phân tích số liệu
Hồi quy Poisson.
# CHƯƠNG 3. DỰ KIẾN KẾT QUẢ VÀ BÀN LUẬN
Bảng 3.1. Tỷ lệ.
## 3.2. Nhóm hai
Bảng 3.2. Hồi quy.
## 3.5. Dự kiến bàn luận
Bàn luận theo mục tiêu.
# 4. TỔ CHỨC VÀ ĐẠO ĐỨC
## 4.11. Đạo đức trong nghiên cứu
- Đăng ký nghiên cứu: không đăng ký công khai.
- Đồng ý tham gia: có phiếu.
# PHỤ LỤC A. TÓM TẮT KẾ HOẠCH PHÂN TÍCH THỐNG KÊ
SAP 1.0.
"""


def test_vung_khoa_theo_de_muc_dong_khai_va_sap():
    k = dict(zip(VAN_KHOA.splitlines(), H.vung_khoa(VAN_KHOA, sap_khoa=True)))
    assert k["Hồi quy Poisson."] and k["Bảng 3.1. Tỷ lệ."] and k["SAP 1.0."]
    assert k["Bảng 3.2. Hồi quy."]                                 # khoá qua đề mục TỔ TIÊN (chương dự kiến kết quả)
    assert k["- Đăng ký nghiên cứu: không đăng ký công khai."] and not k["- Đồng ý tham gia: có phiếu."]
    assert not k["Bàn luận theo mục tiêu."]                       # «dự kiến bàn luận» mở khoá dù chương bị khoá
    k0 = dict(zip(VAN_KHOA.splitlines(), H.vung_khoa(VAN_KHOA, sap_khoa=False)))
    assert not k0["Hồi quy Poisson."] and k0["SAP 1.0."]           # SAP chưa khoá ⇒ mục phân tích được sửa


def test_rao_khoa_loai_thay_the_cham_vung_khoa():
    dl = {"sua": [{"id": "F1", "hanh_dong": "sua", "thay": [
        {"cu": "không đăng ký công khai", "moi": "đăng ký công khai trên OSF"},
        {"cu": "Bàn luận theo mục tiêu.", "moi": "Bàn luận theo từng mục tiêu, đối chiếu y văn."},
        {"cu": "Hồi quy Poisson.", "moi": "Hồi quy logistic."}]}]}
    van, nk = H.ap_bien_tap(dl, VAN_KHOA, sap_khoa=True)
    assert "đối chiếu y văn" in van and "không đăng ký công khai" in van and "Hồi quy Poisson." in van
    assert len(nk["loai"]) == 2 and all("NỘI DUNG ĐÃ KHOÁ" in x["ly_do_loai"] for x in nk["loai"])
    van2, nk2 = H.ap_bien_tap(dl, VAN_KHOA)                        # không truyền cờ ⇒ hành vi cũ (không rào khoá)
    assert len(nk2["nhan"]) == 3


def test_hoan_nguyen_chi_khoi_vuot_quyen_va_dong_bi_neu():
    sua = (VAN_KHOA.replace("không đăng ký công khai", "đăng ký công khai")
           .replace("Bàn luận theo mục tiêu.", "Bàn luận đối chiếu y văn.")
           .replace("Bảng 3.1. Tỷ lệ.", "Bảng 3.1. Tỷ lệ %."))
    moi, nk = H.hoan_nguyen_vuot_quyen(VAN_KHOA, sua, True)
    assert "không đăng ký công khai" in moi and "Bảng 3.1. Tỷ lệ." in moi and "Bàn luận đối chiếu y văn." in moi
    assert len(nk) == 2 and all(x["ly_do"] == "chạm nội dung đã khoá" for x in nk)
    dong = sua.splitlines().index("Bàn luận đối chiếu y văn.") + 1
    moi2, nk2 = H.hoan_nguyen_vuot_quyen(VAN_KHOA, sua, True, [dong])
    assert "Bàn luận theo mục tiêu." in moi2 and any(x["ly_do"] == "dòng chốt kiểm đầu ra đã nêu" for x in nk2)


def _tra_loi(goc, loai_viec, ham):
    """Giả lập agent: với MỖI phiếu việc đang chờ của loại đó, ghi trả lời do `ham(phiếu, dữ liệu)` dựng."""
    for v in H.viec_agent_dang_cho(goc, STUDY):
        if v["loai_viec"] == loai_viec:
            du = json.loads(Path(v["tra_loi"]).with_name(Path(v["loi_nhan"]).name.replace(".md", ".json"))
                            .read_text(encoding="utf-8"))
            Path(v["tra_loi"]).write_text(json.dumps(ham(v, du), ensure_ascii=False), encoding="utf-8", newline="\n")


def _pd_dung_het(v, du, dong_am=None):
    ra = []
    for m in du["muc"]:
        am = m["van_de"].startswith("Tài liệu hoàn toàn không trình bày")
        ra.append({"id": m["id"], "ket_qua": "sai" if am else "dung", "co_so": "tai_lieu_da_dap_ung" if am else "",
                   "dong": m["dong"], "trich": m["trich"], "ly_do": "đối chiếu"})
    return {"phan_dinh": ra}


def _vk(goc, kh):
    return H.main(["vong-kin", "--study", STUDY, "--goi-api", "--ap-dung"], client=kh, goc=goc)


def _goc_ket_hop(tmp_path):
    goc = _goc(tmp_path)
    p = goc / "exports" / STUDY / f"DE_CUONG_NOP_HOI_DONG_{STUDY}.md"
    p.write_text(DE_CUONG + "### 2.6.6. Cỡ mẫu\nCỡ mẫu theo công thức một tỷ lệ.\nTính được 385.\n", encoding="utf-8",
                 newline="\n")
    _hieu_chuan_dat(goc)
    return goc, p


def test_vong_kin_ket_hop_agent_tham_dinh_bien_tap_tham_tra_chot_cuoi(tmp_path):
    goc, p = _goc_ket_hop(tmp_path)
    kh = KhachBatch(dict(TRA))
    assert [_vk(goc, kh) for _ in range(4)] == [4, 0, 4, 0]           # API: thành viên → chủ tịch (MỘT lần họp)
    assert _vk(goc, kh) == H.CHO_AGENT                                 # phiếu thẩm định cho agent sở hữu
    viec = H.viec_agent_dang_cho(goc, STUDY)
    assert {v["agent"] for v in viec} >= {"thiet-ke-nghien-cuu"} and all(v["loai_viec"] == "tham_dinh" for v in viec)
    phieu = json.loads(Path(viec[0]["loi_nhan"]).with_suffix(".json").read_text(encoding="utf-8"))
    assert "nhom" not in json.dumps(phieu) and "goc" not in phieu["muc"][0]          # phiếu MÙ
    assert H.main(["viec-agent", "--study", STUDY], goc=goc) == H.CHO_AGENT
    _tra_loi(goc, "tham_dinh", _pd_dung_het)
    assert _vk(goc, kh) == 0                                           # thẩm định xong, F01 giữ
    assert _vk(goc, kh) == H.CHO_AGENT                                 # phiếu biên tập cho agent
    _tra_loi(goc, "bien_tap", lambda v, du: SUA)
    assert _vk(goc, kh) == 0 and "phân tích ca đầy đủ" in p.read_text(encoding="utf-8")
    assert _vk(goc, kh) == H.CHO_AGENT                                 # thẩm tra bằng agent (không API)
    _tra_loi(goc, "tham_tra", lambda v, du: TT_DAT)
    assert _vk(goc, kh) == 0
    assert _vk(goc, kh) == H.CHO_AGENT                                 # chốt cuối tham-dinh-dau-ra
    _tra_loi(goc, "dau_ra", lambda v, du: {"ket_qua": "DAT", "loi": []})
    assert _vk(goc, kh) == 0
    dat = [s for s in _cac_st(goc) if s.get("buoc") == "dat"][0]
    assert dat["trinh_bac_si"] and dat["ket_hop"] and len(kh.lo) == 2   # đúng 2 batch API cho cả vòng kín


def test_bien_tap_chi_vuot_tham_quyen_van_sang_tham_tra_khong_ghi_tep(tmp_path):
    """22/11/2026 (đo thật BTM vòng 4): mọi vấn đề còn lại nằm vùng khoá ⇒ biên tập viên khai «vượt thẩm quyền»,
    0 thay thế ⇒ máy KHÔNG được dừng như thất bại mà sang thẩm tra trên chính bản này (không ghi tệp)."""
    goc, p = _goc_ket_hop(tmp_path)
    kh = KhachBatch(dict(TRA))
    assert [_vk(goc, kh) for _ in range(5)] == [4, 0, 4, 0, H.CHO_AGENT]
    _tra_loi(goc, "tham_dinh", _pd_dung_het)
    assert _vk(goc, kh) == 0 and _vk(goc, kh) == H.CHO_AGENT
    truoc = p.read_text(encoding="utf-8")
    _tra_loi(goc, "bien_tap", lambda v, du: {"sua": [
        {"id": m["id"], "hanh_dong": "vuot_tham_quyen", "ly_do": "cần thống kê viên quyết"} for m in du["van_de"]]})
    assert _vk(goc, kh) == 0                                           # không còn «⛔ … — dừng»
    assert p.read_text(encoding="utf-8") == truoc                      # không ghi tệp
    assert _vk(goc, kh) == H.CHO_AGENT                                 # sang thẩm tra bằng agent
    assert {v["loai_viec"] for v in H.viec_agent_dang_cho(goc, STUDY)} == {"tham_tra"}
    st = max(_cac_st(goc), key=lambda s: int(s.get("vong", 1)))
    assert st["che_do"] == "tham_tra" and st["vtq_ids"] and len(kh.lo) == 2    # không thêm batch API


def test_agent_phan_sai_doi_chung_thi_khong_ap_phan_quyet(tmp_path):
    goc, p = _goc_ket_hop(tmp_path)
    kh = KhachBatch(dict(TRA))
    assert [_vk(goc, kh) for _ in range(5)] == [4, 0, 4, 0, H.CHO_AGENT]

    def bac_het(v, du):     # agent bác MỌI mục kể cả đối chứng âm theo cách sai: «đúng» đối chứng âm
        return {"phan_dinh": [{"id": m["id"], "ket_qua": "dung" if m["van_de"].startswith("Tài liệu hoàn toàn")
                               else "sai", "co_so": "chuan_khong_doi", "ly_do": "x"} for m in du["muc"]]}
    _tra_loi(goc, "tham_dinh", bac_het)
    assert _vk(goc, kh) == 0
    st = [s for s in _cac_st(goc) if s.get("tham_dinh_agent")][0]
    assert not any(g["hop_le"] for g in st["tham_dinh_agent"].values()) and st["chu_tich"]["giu"]


def test_agent_bac_nhan_xet_co_chung_minh_thi_khong_phai_sua(tmp_path):
    goc, p = _goc_ket_hop(tmp_path)
    kh = KhachBatch(dict(TRA))
    assert [_vk(goc, kh) for _ in range(5)] == [4, 0, 4, 0, H.CHO_AGENT]

    def bac_F(v, du):
        ra = _pd_dung_het(v, du)
        for x, m in zip(ra["phan_dinh"], du["muc"]):
            if m["muc_do"] in ("can_sua", "nghiem_trong") and not m["van_de"].startswith("Tài liệu hoàn toàn"):
                x.update(ket_qua="sai", co_so="tai_lieu_da_dap_ung", dong=8, trich="theo Wilson")
        return ra
    _tra_loi(goc, "tham_dinh", bac_F)
    assert _vk(goc, kh) == 0
    st = [s for s in _cac_st(goc) if s.get("tham_dinh_agent")][0]
    assert st["chu_tich"]["loai_agent"] and not [f for f in st["chu_tich"]["giu"] if f["muc_do"] == "can_sua"]


def test_chot_cuoi_tra_ve_sua_thi_chua_trinh(tmp_path):
    goc, p = _goc_ket_hop(tmp_path)
    kh = KhachBatch(dict(TRA))
    seq = [_vk(goc, kh) for _ in range(5)]
    _tra_loi(goc, "tham_dinh", _pd_dung_het)
    seq += [_vk(goc, kh), _vk(goc, kh)]
    _tra_loi(goc, "bien_tap", lambda v, du: SUA)
    seq += [_vk(goc, kh), _vk(goc, kh)]
    _tra_loi(goc, "tham_tra", lambda v, du: TT_DAT)
    seq += [_vk(goc, kh), _vk(goc, kh)]
    _tra_loi(goc, "dau_ra", lambda v, du: {"ket_qua": "TRA_VE_SUA", "loi": [
        {"ma": "R3", "dong": 2, "trich": "Tăng huyết áp", "mo_ta": "sửa vượt thẩm quyền", "de_xuat": "hoàn nguyên"}]})
    assert _vk(goc, kh) == 0
    st = [s for s in _cac_st(goc) if s.get("ket_qua_dau_ra")][0]
    assert not st.get("trinh_bac_si") and st["buoc"] == "bien_tap"
    assert [x["id"] for x in st["tham_tra"]["loi_moi"]][-1].startswith("R")


def test_hieu_luc_ket_hop_doi_hieu_chuan_ket_hop(tmp_path):
    goc = _goc(tmp_path)
    _hieu_chuan_dat(goc, ket_hop=False)
    out = goc / "exports" / STUDY
    assert H.hieu_luc_hieu_chuan(out)[0] and not H.hieu_luc_hieu_chuan(out, ket_hop=True)[0]


def test_do_bao_nham_bang_trong_tai_agent_khong_ton_api(tmp_path):
    goc, kh = _goc(tmp_path), KhachBatch({})
    assert H.main(["hieu-chuan", "--study", STUDY, "--tao"], goc=goc) == 0
    hc = _hop_ban_cai_loi(goc, kh)
    assert H.main(["hieu-chuan", "--study", STUDY, "--cham"], goc=goc) == 0
    n_lo = len(kh.lo)
    assert H.main(["do-bao-nham", "--study", STUDY], client=kh, goc=goc) == H.CHO_AGENT
    viec = [v for v in H.viec_agent_dang_cho(goc, STUDY) if v["loai_viec"] == "trong_tai"]
    assert viec and viec[0]["agent"] == "trong-tai-tranh-bien"
    phieu = Path(viec[0]["loi_nhan"])
    # làm mù (22/11/2026): phiếu không nằm cạnh đáp án, không lộ tên bản cài lỗi
    assert "hieu_chuan" not in phieu.parts and not (phieu.parent / "dap_an.json").exists()
    assert "BAN_CAI_LOI" not in phieu.read_text(encoding="utf-8") and "dap_an" not in phieu.read_text(encoding="utf-8")
    tt = json.loads((hc / "bao_nham_trang_thai.json").read_text(encoding="utf-8"))
    assert "nhom" not in json.dumps(json.loads(Path(viec[0]["loi_nhan"]).with_suffix(".json").read_text("utf-8")))
    Path(viec[0]["tra_loi"]).write_text(json.dumps({"phan_dinh": [
        {"id": m["id"], "ket_qua": "sai" if m["nhom"] == "kiem_soat_am" else "dung",
         "co_so": "tai_lieu_da_dap_ung" if m["nhom"] == "kiem_soat_am" else "", "dong": m["dong"],
         "trich": m["trich"], "ly_do": "đối chiếu"} for m in tt["muc"]]}, ensure_ascii=False), encoding="utf-8",
        newline="\n")
    assert H.main(["do-bao-nham", "--study", STUDY], client=kh, goc=goc) == 0 and len(kh.lo) == n_lo
    bn = json.loads((hc / "bao_nham.json").read_text(encoding="utf-8"))
    assert bn["dat"] and bn["model_trong_tai"] == "agent:trong-tai-tranh-bien"


def test_tep_cho_agent_ban_cai_loi_thanh_ban_sao_trung_tinh(tmp_path):
    hc = tmp_path / "hoi_dong_khoa_hoc" / "hieu_chuan" / "de_cuong"
    hc.mkdir(parents=True)
    ban = hc / f"BAN_CAI_LOI_{STUDY}_de_cuong.md"
    ban.write_text(DE_CUONG, encoding="utf-8", newline="\n")
    (hc / "dap_an.json").write_text("{}", encoding="utf-8", newline="\n")
    tm = tmp_path / "hoi_dong_khoa_hoc" / "viec_agent" / "x_v1"
    p = Path(H.tep_cho_agent(str(ban), tm))
    assert p.parent == tm and p.name.startswith("TAI_LIEU_") and "CAI_LOI" not in p.name
    assert p.read_bytes() == ban.read_bytes() and not (p.parent / "dap_an.json").exists()
    assert H.tep_cho_agent(str(ban), tm) == str(p)          # gọi lại không đổi
    that = tmp_path / "DE_CUONG_NOP_HOI_DONG.md"
    that.write_text(DE_CUONG, encoding="utf-8", newline="\n")
    assert H.tep_cho_agent(str(that), tm) == str(that)      # tài liệu thật giữ nguyên đường dẫn


def test_agent_sai_theo_cong_cu_phai_co_lenh_va_ket_qua():
    muc = [{"id": "A01"}, {"id": "A02"}]
    pd = H.xac_minh_agent({"phan_dinh": [
        {"id": "A01", "ket_qua": "sai", "co_so": "cong_cu", "lenh": "check_citation_retraction.py --pmid 1",
         "ket_qua_cong_cu": "1: ok (pubmed)"},
        {"id": "A02", "ket_qua": "sai", "co_so": "cong_cu", "lenh": "", "ket_qua_cong_cu": "ok",
         "ly_do": "đã chạy công cụ"}]}, muc, DE_CUONG)
    assert pd["A01"]["ket_qua"] == "sai" and pd["A01"]["lenh"].startswith("check_citation")
    assert pd["A02"]["ket_qua"] == "khong_ro"


def test_sap_da_khoa_doc_tu_bang_chung_he():
    assert H.sap_da_khoa({"bang_chung_he": {"cong_song": {"G4": {"muc": "PASS"}}}})
    assert not H.sap_da_khoa({"bang_chung_he": {"cong_song": {"G4": {"muc": "BLOCKED"}}}})
    assert H.sap_da_khoa({"bang_chung_he": {"cong_song": {"G4": {"muc": "READY"}}}})   # SAP đã chốt, chờ ký
    assert not H.sap_da_khoa({"bang_chung_he": {"ghi_chu": "không có checkpoint"}})


# ── gom yêu cầu chạm cùng chỗ vào MỘT phiếu biên tập (đo thật vòng 2 C1a, 22/11/2026) ─────────────────────────────────
def _van_gom():
    d = ["# ĐỀ CƯƠNG"] + [f"Nội dung đệm số {i} của đề cương nghiên cứu." for i in range(2, 41)]
    d[3 - 1] = ("Điều tra viên ghi mã nghiên cứu cùng số thứ tự khám lên phiếu ghép riêng. Phòng CNTT giữ bảng đối "
                "chiếu và hủy sau 30 ngày.")
    d[7 - 1] = ("Kết quả thăm dò về vai trò trung gian của kỳ vọng được bàn luận cùng một khảo sát tại Hà Nội [49], "
                "với lưu ý về sai lệch [36].")
    d[21 - 1] = "Điều tra viên ghi mã nghiên cứu cùng số thứ tự khám lên phiếu ghép riêng."   # câu lặp ở bản thông tin
    d[26 - 1] = "Một câu khác cũng có trích dẫn [49] ở chỗ khác."
    return "\n".join(d) + "\n"


def _vd(id_, tv, dong, trich, **them):
    return {"id": id_, "thanh_vien": tv, "muc_phieu": "2", "muc_do": "can_sua", "dong": dong, "trich": trich,
            "van_de": f"vấn đề {id_}", "de_xuat": f"đề xuất {id_}", "chuan": "", **them}


VD_GOM = [
    _vd("A", "pb2", 7, "được bàn luận cùng một khảo sát tại Hà Nội [49]"),
    _vd("B", "uv_tk", 7, "Kết quả thăm dò về vai trò trung gian của kỳ vọng"),          # cùng câu, khác mảnh
    _vd("C", "uv_tl", 10, "Nội dung đệm số 10 của đề cương nghiên cứu"),              # cách A đúng 3 dòng ⇒ gom
    _vd("D", "uv_ctk", 14, "Nội dung đệm số 14 của đề cương nghiên cứu"),             # cách C 4 dòng ⇒ KHÔNG gom
    _vd("E", "pb1", 3, "Điều tra viên ghi mã nghiên cứu cùng số thứ tự khám lên phiếu ghép riêng"),
    _vd("F", "uv_dd", 21, "Điều tra viên ghi mã nghiên cứu cùng số thứ tự khám lên phiếu ghép riêng"),  # cùng câu, xa
    _vd("G", "uv_tl", 26, "[49]"),                                                  # mảnh ngắn ⇒ không phải «cùng câu»
    # vòng thẩm tra: «dong/trich» là của bản trước (đã sửa mất); người thẩm tra trích bản hiện tại mà không nêu dòng
    _vd("H", "uv_dd", 99, "câu của bản trước đã bị sửa, không còn trong tài liệu", dong_moi=0,
        trich_moi="Phòng CNTT giữ bảng đối chiếu và hủy sau 30 ngày"),
    _vd("X", "pb1", 30, "Nội dung đệm số 30 của đề cương nghiên cứu"),                # X–Y–Z bắc cầu (X–Z cách 6)
    _vd("Y", "uv_tk", 33, "Nội dung đệm số 33 của đề cương nghiên cứu"),
    _vd("Z", "uv_dd", 36, "Nội dung đệm số 36 của đề cương nghiên cứu"),
]


def test_gom_cum_cung_dong_cung_cau_bac_cau_va_bien_ba_dong():
    cum = H.gom_cum_bien_tap(VD_GOM, _van_gom())
    assert [[f["id"] for f in c] for c in cum] == [["A", "B", "C"], ["D"], ["E", "F", "H"], ["G"], ["X", "Y", "Z"]]


def test_lap_viec_bien_tap_ca_cum_vao_mot_phieu(tmp_path):
    """Trước khi chia phiếu theo agent của ghế, yêu cầu chạm cùng chỗ được gom: cả cụm vào phiếu của agent sở hữu
    nhiều yêu cầu nhất (hoà ⇒ agent của yêu cầu đứng trước). Không gom ⇒ A/B, E/F, X/Y/Z rơi vào phiếu khác nhau."""
    van = _van_gom()
    p = tmp_path / "DE_CUONG.md"
    p.write_text(van, encoding="utf-8", newline="\n")
    st = {"study": STUDY, "tep": str(p), "sha": "a" * 64, "loai": "de_cuong", "vong": 2,
          "thanh_phan": H.thanh_phan_hoi_dong("cross_sectional", van)}
    viec = H.lap_viec_bien_tap(st, VD_GOM, tmp_path)
    assert {t: v["ids"] for t, v in viec.items()} == {
        "viet-ban-thao": ["A", "B", "C", "G"], "bien-so-nghien-cuu": ["D"],
        "dao-duc-dang-ky": ["E", "F", "H"], "thiet-ke-nghien-cuu": ["X", "Y", "Z"]}
    assert viec["viet-ban-thao"]["cum"] == [["A", "B", "C"]] and viec["bien-so-nghien-cuu"]["cum"] == []
    phieu = json.loads(Path(viec["dao-duc-dang-ky"]["loi_nhan"]).with_suffix(".json").read_text(encoding="utf-8"))
    assert [f["id"] for f in phieu["van_de"]] == ["E", "F", "H"]                    # biên tập viên nhận ĐỦ cụm
    assert H.lap_viec_bien_tap(st, VD_GOM, tmp_path, van) == viec                  # văn bản truyền vào = đọc tệp


TRA_CUNG_DONG = {**{m: _tv(diem=4) for m in ("pb2", "uv_dd", "uv_tl", "uv_ctk")},
                 "pb1": _tv(phat_hien=[PH_DUNG]),
                 "uv_tk": _tv(phat_hien=[{"muc_phieu": "3", "muc_do": "can_sua", "dong": 8,
                                          "trich": "kèm khoảng tin cậy 95%", "van_de": "chưa nêu kiểm định một hay "
                                          "hai phía", "chuan": "", "de_xuat": "nêu rõ kiểm định hai phía"}]),
                 "ct": {"phan_quyet": [], "gop": [], "nhan_xet_chung": "Cần sửa mục phân tích.",
                        "yeu_cau_chinh_sua": ["dữ liệu thiếu", "kiểm định hai phía"]}}


def test_vong_kin_ket_hop_hai_ghe_cung_dong_mot_phieu_bien_tap(tmp_path, capsys):
    """Hai ghế (pb1 → thiet-ke-nghien-cuu, uv_tk → co-mau-nghien-cuu) cùng nêu dòng 8: MỘT phiếu biên tập nhận cả hai,
    một thay thế gộp qua rào; vòng sau mỗi ghế vẫn thẩm tra đúng yêu cầu của mình."""
    goc, p = _goc_ket_hop(tmp_path)
    kh = KhachBatch(dict(TRA_CUNG_DONG))
    assert [_vk(goc, kh) for _ in range(5)] == [4, 0, 4, 0, H.CHO_AGENT]
    _tra_loi(goc, "tham_dinh", _pd_dung_het)
    assert _vk(goc, kh) == 0 and _vk(goc, kh) == H.CHO_AGENT
    viec = [v for v in H.viec_agent_dang_cho(goc, STUDY) if v["loai_viec"] == "bien_tap"]
    assert len(viec) == 1 and viec[0]["agent"] == "thiet-ke-nghien-cuu"
    du = json.loads(Path(viec[0]["loi_nhan"]).with_suffix(".json").read_text(encoding="utf-8"))
    ids = [f["id"] for f in du["van_de"]]
    assert len(ids) == 2 and {f["thanh_vien"] for f in du["van_de"]} == {"pb1", "uv_tk"}
    assert "🔗 Gom yêu cầu chạm cùng chỗ" in capsys.readouterr().out
    cu = "Tỷ lệ được ước lượng kèm khoảng tin cậy 95% theo Wilson."
    _tra_loi(goc, "bien_tap", lambda v, d: {"sua": [
        {"id": ids[0], "hanh_dong": "sua", "thay": [{"dong": 8, "cu": cu, "moi": cu[:-1] + ", kiểm định hai phía; dữ "
                                                    "liệu thiếu xử lý bằng phân tích ca đầy đủ."}]},
        {"id": ids[1], "hanh_dong": "sua", "thay": [], "ly_do": "đã gộp vào thay thế của " + ids[0]}]})
    assert _vk(goc, kh) == 0 and "kiểm định hai phía" in p.read_text(encoding="utf-8")
    st1 = [s for s in _cac_st(goc) if s.get("bien_tap")][0]
    assert len(st1["bien_tap"]["nhan"]) == 1 and not st1["bien_tap"]["loai"]
    assert _vk(goc, kh) == H.CHO_AGENT
    assert {v["agent"] for v in H.viec_agent_dang_cho(goc, STUDY) if v["loai_viec"] == "tham_tra"} == {
        "pb1-thiet-ke-nghien-cuu", "uv_tk-co-mau-nghien-cuu"}
