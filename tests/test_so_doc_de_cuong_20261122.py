"""Sổ đọc đề cương từng đơn vị (K21) — `tools/so_doc_de_cuong.py` (22/11/2026).

Ngoại tuyến, fixture tự dựng. Ba phép đột biến bắt buộc của điều phối phải làm đỏ đúng ca: bỏ so băm (bản ghi «dat»
cũ vẫn tính là đã đọc), bỏ đơn vị bảng, bỏ băm ảnh (đổi ảnh mà đơn vị hình không đổi)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import kiem_de_cuong_nop_hoi_dong as KDN  # noqa: E402
import so_doc_de_cuong as SD  # noqa: E402

MA = "ZZTEST-SODOC"
DE_CUONG = """# ĐỀ CƯƠNG NGHIÊN CỨU

# ĐẶT VẤN ĐỀ

Tỷ lệ hài lòng là 0,78 theo TS. Nguyễn V. A. và cs. trong nghiên cứu năm 2020 [1]. Thời gian chờ tr. 12 là chỉ báo \
quan trọng. Câu thứ ba ngắn.

## 2.5.1. Cỡ mẫu

n₀ = Z²₁₋α/₂ × p × (1 − p) / d²

**Bảng 2.1. Nửa độ rộng khoảng tin cậy**

| ICC | CV = 0 |
|---|---|
| 0,01 | ±3,4% |
| 0,02 | ±3,6% |

![Hình 1.1](bieu-bang/hinh-1.png)

**Hình 1.1. Khung lý thuyết**

- Câu hỏi 3: 1. Có ☐ 2. Không ☐

# TÀI LIỆU THAM KHẢO

1. Tác giả A. Tiêu đề. Tạp chí. 2026. PMID: 11111111.
2. Tác giả B. Tiêu đề khác. Tạp chí. 2025.
"""


def _de_tai(tmp_path: Path, md: str = DE_CUONG) -> Path:
    d = tmp_path / "exports" / MA
    (d / "bieu-bang").mkdir(parents=True)
    (d / "bieu-bang" / "hinh-1.png").write_bytes(b"\x89PNG anh goc")
    (d / f"DE_CUONG_NOP_HOI_DONG_{MA}.md").write_text(md, encoding="utf-8", newline="\n")
    return d


def _dv(d: Path) -> dict:
    return {x.ma: x for x in SD.tach_don_vi((d / f"DE_CUONG_NOP_HOI_DONG_{MA}.md").read_text(encoding="utf-8"), d)}


# ───────────────────────────────────────── tách câu
@pytest.mark.parametrize("van, so", [
    ("Tỷ lệ là 0,78 và 1.000 người. Câu hai.", 2),
    ("Theo TS. Nguyễn V. A. và cs. năm 2020. Kết thúc.", 2),
    ("Xem tr. 12 của tài liệu. Hết.", 2),
    ("1. Có ☐ 2. Không ☐", 1),
    ("Smith et al. Báo cáo. Câu hai!", 2),
    ("Một câu không chấm cuối", 1),
])
def test_tach_cau_tieng_viet(van, so):
    assert len(SD.tach_cau(van)) == so, SD.tach_cau(van)


# ───────────────────────────────────────── tách đơn vị
def test_tach_don_vi_du_loai(tmp_path):
    d = _de_tai(tmp_path)
    dv = list(_dv(d).values())
    dem = {lo: sum(1 for x in dv if x.loai == lo) for lo in SD.LOAI}
    assert dem["hang_bang"] == 3  # hàng tiêu đề cột + 2 hàng
    assert dem["hinh"] == 1 and dem["cong_thuc"] == 1 and dem["tltk"] == 2 and dem["tieu_de"] == 4
    assert dem["cau"] == 5  # ba câu đặt vấn đề + tên bảng + dòng lựa chọn (chú thích hình gộp vào đơn vị hình)
    assert len({x.ma for x in dv}) == len(dv)
    assert {"tltk:1", "tltk:2", "hang_bang:2.5.1:1:0", "hang_bang:2.5.1:1:2", "hinh:2.5.1:1"} <= {x.ma for x in dv}


def test_bam_hang_bang_gom_ten_bang_va_chi_hang_do_doi(tmp_path):
    d = _de_tai(tmp_path / "a")
    goc = _dv(d)
    d2 = _de_tai(tmp_path / "b", DE_CUONG.replace("| 0,02 | ±3,6% |", "| 0,02 | ±3,7% |"))
    moi = _dv(d2)
    assert goc["hang_bang:2.5.1:1:2"].bam != moi["hang_bang:2.5.1:1:2"].bam
    assert goc["hang_bang:2.5.1:1:1"].bam == moi["hang_bang:2.5.1:1:1"].bam
    d3 = _de_tai(tmp_path / "c", DE_CUONG.replace("Nửa độ rộng khoảng tin cậy", "Độ rộng"))
    assert _dv(d3)["hang_bang:2.5.1:1:1"].bam != goc["hang_bang:2.5.1:1:1"].bam  # đổi tên bảng ⇒ đổi mọi hàng


def test_bam_hinh_gom_bam_tep_anh(tmp_path):
    d = _de_tai(tmp_path)
    truoc = _dv(d)["hinh:2.5.1:1"].bam
    (d / "bieu-bang" / "hinh-1.png").write_bytes(b"\x89PNG anh da sua")
    assert _dv(d)["hinh:2.5.1:1"].bam != truoc
    (d / "bieu-bang" / "hinh-1.json").write_text("{}", encoding="utf-8", newline="\n")  # dữ liệu vẽ cũng vào băm
    assert _dv(d)["hinh:2.5.1:1"].bam not in (truoc,)


# ───────────────────────────────────────── ghi và trạng thái
def _ban_ghi(dv, ket_qua="dat", **them) -> dict:
    return {"ma": dv.ma, "bam": dv.bam, "ket_qua": ket_qua, "can_cu": "đối chiếu nguồn [1]", "vai": "tham-dinh-dau-ra",
            "thoi_diem": "2026-11-22T10:00:00", **them}


def test_ghi_tu_choi_bam_sai_tuong_lai_ket_qua_la(tmp_path):
    d = _de_tai(tmp_path)
    x = _dv(d)["tltk:1"]
    nhan, tu_choi = SD.ghi(d, MA, {"ban_ghi": [
        _ban_ghi(x, bam="0" * 16), _ban_ghi(x, thoi_diem="2099-01-01T00:00:00"), _ban_ghi(x, ket_qua="ok"),
        _ban_ghi(x, can_cu=""), {"ma": "khong-co", "bam": "x"}]})
    assert nhan == 0 and len(tu_choi) == 5
    assert not SD.tep_so(d, MA).exists()


def test_doc_du_roi_sua_mot_don_vi_thi_thanh_chua_doc(tmp_path):
    d = _de_tai(tmp_path)
    dv = _dv(d)
    nhan, tu_choi = SD.ghi(d, MA, {"ban_ghi": [_ban_ghi(x) for x in dv.values()]})
    assert (nhan, tu_choi) == (len(dv), [])
    tt = SD.trang_thai(d, MA)
    assert tt["da_doc"] == tt["tong"] and tt["ty_le_phu"] == 1.0
    # sửa MỘT câu sau khi đọc ⇒ bản ghi «dat» mang băm cũ = chưa đọc
    p = d / f"DE_CUONG_NOP_HOI_DONG_{MA}.md"
    p.write_text(DE_CUONG.replace("Câu thứ ba ngắn.", "Câu thứ ba đã sửa."), encoding="utf-8", newline="\n")
    tt2 = SD.trang_thai(d, MA)
    assert (tt2["chua_doc"], tt2["doi_sau_doc"], tt2["da_doc"]) == (1, 1, tt["tong"] - 1)


def test_sua_chua_xu_ly_va_sau_khi_sua(tmp_path):
    d = _de_tai(tmp_path)
    x = _dv(d)["tltk:2"]
    SD.ghi(d, MA, {"ban_ghi": [_ban_ghi(x, "sua")]})
    assert SD.trang_thai(d, MA)["can_sua"] == 1
    p = d / f"DE_CUONG_NOP_HOI_DONG_{MA}.md"
    p.write_text(DE_CUONG.replace("Tiêu đề khác. Tạp chí. 2025.", "Tiêu đề khác. Tạp chí. 2025;1(2):3-4."),
                 encoding="utf-8", newline="\n")
    tt = SD.trang_thai(d, MA)
    assert tt["can_sua"] == 0 and any(y["ma"] == "tltk:2" for y in tt["ds_chua_doc"])


# ───────────────────────────────────────── K21
def test_k21_chan_khi_dang_trinh_ma_chua_doc_du(tmp_path, monkeypatch):
    d = _de_tai(tmp_path)
    monkeypatch.setattr(SD, "dang_trinh", lambda o, s: (True, "G10 chấm sống READY"))
    assert SD.loi_k21(d, MA) and SD.loi_k21(d, MA)[0].startswith("K21")
    dv = _dv(d)
    SD.ghi(d, MA, {"ban_ghi": [_ban_ghi(x) for x in dv.values()]})
    assert SD.loi_k21(d, MA) == []
    SD.ghi(d, MA, {"ban_ghi": [_ban_ghi(dv["tltk:1"], "sua")]})
    assert any("«sua»" in x for x in SD.loi_k21(d, MA))
    assert SD.canh_bao_k21(d, MA) == []


def test_k21_chua_trinh_chi_bao_ty_le(tmp_path):
    d = _de_tai(tmp_path)
    assert SD.dang_trinh(d, MA)[0] is False  # chưa có G10_checkpoint.json
    assert SD.loi_k21(d, MA) == []
    assert "phủ 0/" in SD.canh_bao_k21(d, MA)[0]


def test_k21_noi_vao_kiem_de_cuong(tmp_path, monkeypatch):
    d = _de_tai(tmp_path)
    monkeypatch.setattr(SD, "dang_trinh", lambda o, s: (True, "G10 chấm sống PASS"))
    assert any(x.startswith("K21") for x in KDN.kiem(d, MA))
    monkeypatch.setattr(SD, "dang_trinh", lambda o, s: (False, "chưa trình"))
    assert not any(x.startswith("K21") for x in KDN.kiem(d, MA))
    assert any(x.startswith("K21") for x in KDN.canh_bao_k20_k21(d, MA))


def test_cli(tmp_path, capsys):
    d = _de_tai(tmp_path)
    assert SD.main(["tach", "--study", MA, "--goc", str(tmp_path)]) == 0
    assert SD.main(["trang-thai", "--study", MA, "--goc", str(tmp_path)]) == 1
    assert SD.main(["tach", "--study", "../x", "--goc", str(tmp_path)]) == 3
    assert SD.main(["tach", "--study", "KHONG-CO", "--goc", str(tmp_path)]) == 2
    tep = tmp_path / "ghi.json"
    tep.write_text(json.dumps({"ban_ghi": [_ban_ghi(x) for x in _dv(d).values()]}), encoding="utf-8", newline="\n")
    assert SD.main(["ghi", "--study", MA, "--goc", str(tmp_path), "--tu", str(tep)]) == 0
    assert SD.main(["trang-thai", "--study", MA, "--goc", str(tmp_path)]) == 0
