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


@pytest.mark.parametrize("diem", [0, 6, "4", None, True])
def test_diem_sai_khuon_la_ket_qua_hong(diem):
    dl = _tv()
    dl["diem"]["2"] = diem
    with pytest.raises(API.KetQuaHong):
        H.xac_minh_thanh_vien("pb1", dl, DE_CUONG, [])


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
