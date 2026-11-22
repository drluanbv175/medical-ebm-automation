"""Chế độ AGENT của kiểm nội dung trích dẫn — không gọi Claude API (22/11/2026).

Bác sĩ 22/11/2026: «Đề cương phải được đọc từng câu từng chữ trước khi hoàn thành»; tín dụng API sắp hết. Agent đọc
nguồn, máy giữ phần khách quan: mã cặp ổn định + băm đoạn và dòng TLTK, trích ≤ 15 từ có nguyên văn trong nguồn máy có,
«ủng hộ» thì con số của đoạn phải có trong nguồn, đổi văn bản sau khi đọc ⇒ phải đọc lại.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import kiem_noi_dung_trich_dan as KND  # noqa: E402

MA = "ZZ-AGENT"
DC = """# ĐẶT VẤN ĐỀ

Tỷ lệ kiểm soát huyết áp tại chăm sóc ban đầu là 41% [1]. Thời gian chờ dài đi kèm hài lòng thấp hơn [2].

# TÀI LIỆU THAM KHẢO

1. Brodin N, Wolff M. Factors associated with blood pressure control. Scand J Prim Health Care. \
2026;44(1):1-9. PMID: 40583484.
2. Quyen BTT, Ha NT. Outpatient satisfaction in Vietnam. Health Psychol Open. 2021;8(1):1-10. PMID: 34017606.
"""
JATS = ("<article><body><p>The results showed blood pressure control in 41% of the cases among 400 patients from ten "
        "primary care centres in southern Sweden.</p></body></article>")


def _de_tai(tmp_path: Path) -> Path:
    d = tmp_path / "exports" / MA
    (d / "toan_van_oa").mkdir(parents=True)
    (d / f"DE_CUONG_NOP_HOI_DONG_{MA}.md").write_text(DC, encoding="utf-8", newline="\n")
    (d / "toan_van_oa" / "PMID-40583484_x.xml").write_text(JATS, encoding="utf-8", newline="\n")
    return d


def _tep(d: Path) -> Path:
    return d / f"DE_CUONG_NOP_HOI_DONG_{MA}.md"


def _cap(d: Path) -> dict:
    return {c["so"]: c for c in KND.cap_kiem(_tep(d).read_text(encoding="utf-8"))}


def _bg(c: dict, **kw) -> dict:
    r = {"ma": c["ma"], "bam": c["bam"], "ket_qua": "ung_ho", "nguon_doc": "toan_van", "vi_tri": "Results",
         "trich": "blood pressure control in 41% of the cases", "vai": "kiem-chung-trich-dan"}
    r.update(kw)
    return r


def test_ma_cap_on_dinh_theo_noi_dung_bam_gom_doan_va_dong_tltk(tmp_path):
    d = _de_tai(tmp_path)
    c = _cap(d)
    assert set(c) == {1, 2} and c[1]["ma"].startswith("trich:") and c[1]["ma"].endswith(":1")
    assert c[1]["so_lieu"] == ["41"]
    # câu mới CÓ trích dẫn phía trước ⇒ mã đoạn theo vị trí (C001…) dịch đi, mã theo nội dung thì không
    moi = DC.replace("# ĐẶT VẤN ĐỀ\n\n", "# ĐẶT VẤN ĐỀ\n\nCâu mới có trích dẫn [2].\n\n")
    _tep(d).write_text(moi, encoding="utf-8", newline="\n")
    assert _cap(d)[1]["ma"] == c[1]["ma"] and _cap(d)[1]["bam"] == c[1]["bam"]
    # sửa dòng TLTK ⇒ băm đổi (đọc lại), mã giữ
    _tep(d).write_text(DC.replace("2026;44(1):1-9", "2026;44(1):1-10"), encoding="utf-8", newline="\n")
    assert _cap(d)[1]["ma"] == c[1]["ma"] and _cap(d)[1]["bam"] != c[1]["bam"]
    # băm cùng thuật toán sổ đọc K21: sha256 các phần NFC + gộp khoảng trắng, nối \x1f, 16 hex
    import hashlib
    assert KND.bam_don_vi("a  b", "c") == hashlib.sha256("a b\x1fc".encode()).hexdigest()[:16]


def test_xuat_phieu_chi_dung_tep_toan_van_va_gioi_han_so_cap(tmp_path):
    d = _de_tai(tmp_path)
    kq = KND.xuat_phieu(d, MA, _tep(d), endnote=False)
    ph = json.loads(Path(kq["phieu"]).read_text(encoding="utf-8"))
    assert kq["so_cap"] == 2 and kq["co_toan_van"] == 1 and ph["schema"] == KND.SCHEMA_PHIEU
    c = {x["so"]: x for x in ph["cap"]}
    assert c[1]["toan_van"].endswith("PMID-40583484_x.xml") and c[2]["toan_van"] is None
    assert KND.xuat_phieu(d, MA, _tep(d), toi_da=1, endnote=False)["so_cap"] == 1
    assert KND.xuat_phieu(d, MA, _tep(d), chon=[c[2]["ma"]], endnote=False)["so_cap"] == 1


def test_nap_hop_le_ghi_so_va_trang_thai_bao_phu(tmp_path):
    d = _de_tai(tmp_path)
    c = _cap(d)
    nhan, tu_choi = KND.nap_ket_qua(d, MA, _tep(d), {"ban_ghi": [
        _bg(c[1]),
        _bg(c[2], ket_qua="khong_doc_duoc", nguon_doc=None, trich="", vi_tri="",
            ly_do="toàn văn SAGE không truy cập được; abstract không nêu cách đo")]}, endnote=False)
    assert (nhan, tu_choi) == (2, [])
    so = json.loads((d / KND.TEP_SO.format(study=MA)).read_text(encoding="utf-8"))
    assert so["schema"] == KND.SCHEMA_SO and so["ban_ghi"][c[1]["ma"]]["trich_doi_chieu_may"] is True
    tt = KND.trang_thai_so(d, MA, _tep(d))
    assert tt["da_phan"] == 2 and tt["ty_le_phu"] == 1.0 and tt["theo_phan_quyet"]["khong_doc_duoc"] == 1
    # sửa đoạn sau khi đọc ⇒ cặp đó thành chưa đọc (mã theo nội dung đổi)
    _tep(d).write_text(DC.replace("là 41% [1]", "là 40% [1]"), encoding="utf-8", newline="\n")
    tt = KND.trang_thai_so(d, MA, _tep(d))
    assert tt["da_phan"] == 1 and tt["chua_doc"] == 1
    # sửa DÒNG TLTK sau khi đọc ⇒ mã giữ, băm đổi ⇒ chưa đọc + «đổi sau khi đọc»
    _tep(d).write_text(DC.replace("2026;44(1):1-9", "2026;44(1):1-10"), encoding="utf-8", newline="\n")
    tt = KND.trang_thai_so(d, MA, _tep(d))
    assert tt["da_phan"] == 1 and tt["doi_sau_doc"] == [c[1]["ma"]]


def test_nap_tu_choi_dung_ly_do(tmp_path):
    d = _de_tai(tmp_path)
    c = _cap(d)
    ca = {
        "mã lạ": _bg(c[1], ma="trich:khongco:1"),
        "băm cũ": _bg(c[1], bam="0" * 16),
        "phán lạ": _bg(c[1], ket_qua="dung"),
        # 16 từ CHÉP ĐÚNG nguồn — chỉ trần 15 từ chặn được
        "trích dài": _bg(c[1], trich="blood pressure control in 41% of the cases among 400 patients from ten primary "
                                     "care centres"),
        "trích không có trong nguồn": _bg(c[1], trich="blood pressure was controlled in most cases"),
        "ủng hộ mà số không có": _bg(c[1], trich="among 400 patients"),
        "thiếu lý do": _bg(c[1], ket_qua="khong_ung_ho"),
        "thiếu vai": _bg(c[1], vai=""),
        "tương lai": _bg(c[1], thoi_diem="2999-01-01T00:00:00"),
        "thiếu vị trí": _bg(c[1], vi_tri=""),
    }
    for ten, r in ca.items():
        if ten == "ủng hộ mà số không có":
            _tep(d).write_text(DC.replace("là 41% [1]", "là 52% [1]"), encoding="utf-8", newline="\n")
            r = _bg(_cap(d)[1], trich="among 400 patients")
        nhan, tu_choi = KND.nap_ket_qua(d, MA, _tep(d), {"ban_ghi": [r]}, endnote=False)
        assert nhan == 0 and len(tu_choi) == 1, (ten, tu_choi)
        _tep(d).write_text(DC, encoding="utf-8", newline="\n")
    assert not (d / KND.TEP_SO.format(study=MA)).exists()
    # «ủng hộ một phần» kèm lý do vẫn nhận khi số của đoạn không có trong nguồn
    _tep(d).write_text(DC.replace("là 41% [1]", "là 52% [1]"), encoding="utf-8", newline="\n")
    nhan, tu_choi = KND.nap_ket_qua(d, MA, _tep(d), {"ban_ghi": [
        _bg(_cap(d)[1], ket_qua="ung_ho_mot_phan", ly_do="nguồn ghi 41%, đoạn ghi 52%")]}, endnote=False)
    assert (nhan, tu_choi) == (1, [])
    assert KND.trang_thai_so(d, MA, _tep(d))["ung_ho_mot_phan"][0]["ly_do"] == "nguồn ghi 41%, đoạn ghi 52%"


def test_abstract_trong_phieu_duoc_doi_chieu_trich(tmp_path):
    d = _de_tai(tmp_path)

    def lay_abs(tl):
        return {2: {"title": "Outpatient satisfaction in Vietnam",
                    "abstract": "Longer waiting time was associated with lower satisfaction."}}, {}

    KND.xuat_phieu(d, MA, _tep(d), lay_abs=lay_abs, endnote=False)
    c = _cap(d)
    sai = _bg(c[2], nguon_doc="abstract", vi_tri="Abstract", trich="waiting time doubled satisfaction")
    dung = _bg(c[2], nguon_doc="abstract", vi_tri="Abstract", trich="Longer waiting time was associated with lower")
    assert KND.nap_ket_qua(d, MA, _tep(d), {"ban_ghi": [sai]}, endnote=False)[0] == 0
    assert KND.nap_ket_qua(d, MA, _tep(d), {"ban_ghi": [dung]}, endnote=False) == (1, [])


def test_cli_ba_lenh_va_ma_thoat(tmp_path, capsys):
    d = _de_tai(tmp_path)
    goc = tmp_path
    assert KND.main(["xuat-phieu", "--study", MA, "--khong-endnote"], goc=goc) == 0
    ph = json.loads((d / KND.TEP_PHIEU.format(study=MA)).read_text(encoding="utf-8"))
    c = {x["so"]: x for x in ph["cap"]}
    nhap = tmp_path / "nhap.json"
    nhap.write_text(json.dumps({"ban_ghi": [_bg(c[1]), _bg(c[2], ket_qua="khong_ung_ho", nguon_doc="toan_van",
                                                           ly_do="bài không đo thời gian chờ")]}),
                    encoding="utf-8", newline="\n")
    # cặp 2 không có toàn văn trên máy ⇒ không đối chiếu được trích, vẫn nhận (ghi trich_doi_chieu_may=false)
    assert KND.main(["nap-ket-qua", "--study", MA, "--tu", str(nhap), "--khong-endnote"], goc=goc) == 0
    assert KND.main(["trang-thai", "--study", MA], goc=goc) == 1  # còn cặp «KHÔNG ủng hộ»
    assert "KHÔNG ủng hộ 1" in capsys.readouterr().out
    assert KND.main(["nap-ket-qua", "--study", MA], goc=goc) == 3
