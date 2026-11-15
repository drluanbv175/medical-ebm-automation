"""Giai đoạn «Tổng quan tài liệu» thành chốt máy (15/11/2026).

Bác sĩ 15/11/2026: «… Tổng Quan Tài Liệu … Hãy đảm bảo sự đồng bộ xuyên suốt và chính xác nhất» + «mỗi vấn đề xây
dựng và hoàn thiện phải được cập nhật vào hệ thống». Đo thật: BTM — sổ chứng cứ G1 (A2b) liệt kê 19 bài chủ nhiệm đã
LOẠI khỏi danh mục trích dẫn (không công cụ nào của repo y khoa đọc `DANH_MUC_TRICH_DAN`), 28/47 trích dẫn không có
bản ghi kiểm rút bài theo từng mã; C1a — biên nhận rút bài A12 quá hạn 30 ngày, SAP dẫn nguồn phương pháp không có
trong TLTK đề cương nộp. Mỗi test khoá MỘT hành vi.
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
for _p in (str(REPO_ROOT / "tools"), str(REPO_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import danh_muc_trich_dan as DMT  # noqa: E402
import g1_quality_gate as G1Q  # noqa: E402
import kiem_rut_bai_trich_dan as KRB  # noqa: E402
import nhat_quan_xuyen_cong as NQ  # noqa: E402

S = "TQTD-THU"
DC = f"DE_CUONG_NOP_HOI_DONG_{S}.md"


def _ghi(d: Path, ten: str, noi_dung) -> None:
    (d / ten).write_text(noi_dung if isinstance(noi_dung, str) else json.dumps(noi_dung, ensure_ascii=False),
                         encoding="utf-8", newline="\n")


def _de_cuong(than: str, tltk: list) -> str:
    return ("# ĐỀ CƯƠNG\n\n# 1. ĐẶT VẤN ĐỀ\n\n" + than + "\n\n# 7. TÀI LIỆU THAM KHẢO\n\n"
            + "\n".join(f"{i}. {x}" for i, x in enumerate(tltk, 1)) + "\n\n# PHỤ LỤC A\n\nKhông trích.\n")


R1, R2, R3 = ("Tác giả A. Bài một. 2020. PMID: 11111111.", "Tác giả B. Bài hai. 2021. doi:10.1000/hai.",
              "Bộ Y tế. Quyết định 56/QĐ-BYT. 2024.")


def _sach(d: Path) -> None:
    _ghi(d, DC, _de_cuong("Mở đầu [1]. Tiếp [2, 3]. Lại [1].", [R1, R2, R3]))
    _ghi(d, "A12_RETRACTION_RECEIPT.json", {"pmids_checked": ["11111111"], "checked_at_utc": "2026-11-10T00:00:00"})
    _ghi(d, f"A12_CITATION_VERIFICATION_{S}.md", "| 10.1000/hai | ✅ tồn tại, không rút |\n")


def _truc(d: Path, meta: dict | None = None):
    return NQ._truc_trich_dan(d, S, meta or {})


def _hom_nay(monkeypatch, ngay=date(2026, 11, 15)):
    monkeypatch.setattr(NQ, "_hom_nay", lambda: ngay)


# ── ① bộ đọc dùng chung ────────────────────────────────────────────────────────────────────────────────────────────
def test_tach_tltk_va_so_trich_dan():
    muc, than = DMT.tach_tltk(_de_cuong("A [1]. B [2–4]. C [1, 5–6]. Thang [0–100]. [7](http://x)", ["a"] * 6))
    assert sorted(muc) == [1, 2, 3, 4, 5, 6] and "PHỤ LỤC A" in than and "TÀI LIỆU THAM KHẢO" not in than
    assert DMT.so_trich_dan(than) == [1, 2, 3, 4, 1, 5, 6]  # bỏ thang [0–100] và liên kết Markdown
    assert DMT.tach_tltk("# Không có mục tham khảo\n") is None


def test_dinh_danh_va_khoa_danh_muc():
    assert DMT.dinh_danh("x PMID: 12345678. doi:10.1000/ABC.") == {"pmid:12345678", "doi:10.1000/abc"}
    assert DMT.khoa_cua({"pmid": "1234567", "doi": "10.1/X"}) == {"pmid:1234567", "doi:10.1/x"}


# ── ② TLTK đề cương nộp ────────────────────────────────────────────────────────────────────────────────────────────
def test_tltk_sach_la_khop(tmp_path, monkeypatch):
    _hom_nay(monkeypatch)
    _sach(tmp_path)
    k = _truc(tmp_path)
    assert k["muc"] == NQ.MUC_KHOP, k["ghi_chu"]


def test_trich_so_khong_co_va_muc_khong_duoc_trich(tmp_path, monkeypatch):
    _hom_nay(monkeypatch)
    _sach(tmp_path)
    _ghi(tmp_path, DC, _de_cuong("Mở đầu [1]. Sau [4].", [R1, R2, R3]))
    k = _truc(tmp_path)
    assert k["muc"] == NQ.MUC_LECH_MEM
    assert "không có trong TLTK: [4]" in k["ghi_chu"] and "không được trích trong thân: [2, 3]" in k["ghi_chu"]


def test_thu_tu_vancouver(tmp_path, monkeypatch):
    _hom_nay(monkeypatch)
    _sach(tmp_path)
    _ghi(tmp_path, DC, _de_cuong("Mở đầu [2]. Sau [1, 3].", [R1, R2, R3]))
    k = _truc(tmp_path)
    assert k["muc"] == NQ.MUC_LECH_MEM and "Vancouver: [1] xuất hiện sau [2]" in k["ghi_chu"]


def test_trung_dinh_danh(tmp_path, monkeypatch):
    _hom_nay(monkeypatch)
    _sach(tmp_path)
    _ghi(tmp_path, DC, _de_cuong("A [1]. B [2]. C [3].", [R1, R2, "Bản lặp. PMID: 11111111."]))
    k = _truc(tmp_path)
    assert k["muc"] == NQ.MUC_LECH_MEM and "11111111 ở số [1, 3]" in k["ghi_chu"]


def test_muc_chua_kiem_rut_bai_la_lech_mem(tmp_path, monkeypatch):
    _hom_nay(monkeypatch)
    _sach(tmp_path)
    (tmp_path / f"A12_CITATION_VERIFICATION_{S}.md").unlink()
    k = _truc(tmp_path)
    assert k["muc"] == NQ.MUC_LECH_MEM and "chưa có bản ghi kiểm rút bài" in k["ghi_chu"] and "(số [2])" in k["ghi_chu"]


def test_ban_ghi_rut_bai_qua_30_ngay_la_can_xem_va_tep_moi_lam_tuoi(tmp_path, monkeypatch):
    _sach(tmp_path)
    _hom_nay(monkeypatch, date(2026, 12, 20))
    k = _truc(tmp_path)
    assert k["muc"] == NQ.MUC_CAN_XEM and "quá 30 ngày (số [1, 2])" in k["ghi_chu"]
    KRB.ghi(tmp_path, S, {"pmid:11111111": {"status": "ok"}, "doi:10.1000/hai": {"status": "ok"}},
            luc="2026-12-19T00:00:00+00:00")
    assert _truc(tmp_path)["muc"] == NQ.MUC_KHOP  # tệp kiểm theo từng mã làm tươi, không đụng biên nhận A12


def test_ma_khong_ket_luan_khong_tinh_la_da_kiem(tmp_path, monkeypatch):
    _hom_nay(monkeypatch)
    _sach(tmp_path)
    (tmp_path / f"A12_CITATION_VERIFICATION_{S}.md").unlink()
    KRB.ghi(tmp_path, S, {"doi:10.1000/hai": {"status": "unknown_fetch_error"}}, luc="2026-11-14T00:00:00+00:00")
    assert _truc(tmp_path)["muc"] == NQ.MUC_LECH_MEM  # «không biết» KHÔNG bao giờ là «đã kiểm»


def test_bai_da_rut_trong_tltk(tmp_path, monkeypatch):
    _hom_nay(monkeypatch)
    _sach(tmp_path)
    KRB.ghi(tmp_path, S, {"pmid:11111111": {"status": "retracted"}}, luc="2026-11-14T00:00:00+00:00")
    k = _truc(tmp_path)
    assert k["muc"] == NQ.MUC_LECH_MEM and "11111111 retracted" in k["ghi_chu"]


# ── ③ danh mục trích dẫn + quyết định loại của chủ nhiệm ──────────────────────────────────────────────────────────
def _danh_muc(d: Path, trich: list, loai: list) -> None:
    _ghi(d, DMT.TEP.format(study=S), {"trich_dan": trich, "loai_bo": loai})


LOAI = {"pmid": "99999999", "doi": None, "id": "T09", "ly_do": "không lấy được toàn văn", "ngay": "2026-10-25"}


def test_tltk_dung_bai_da_loai(tmp_path, monkeypatch):
    _hom_nay(monkeypatch)
    _sach(tmp_path)
    _danh_muc(tmp_path, [{"pmid": "11111111", "id": "T01"}], [LOAI])
    _ghi(tmp_path, DC, _de_cuong("A [1]. B [2, 3].", [R1, R2, "Bài đã loại. PMID: 99999999."]))
    _ghi(tmp_path, "A12_RETRACTION_RECEIPT.json", {"pmids_checked": ["11111111", "99999999"],
                                                     "checked_at_utc": "2026-11-10"})
    k = _truc(tmp_path)
    assert k["muc"] == NQ.MUC_LECH_MEM and "đã LOẠI khỏi danh mục" in k["ghi_chu"] and "toàn văn" in k["ghi_chu"]


def test_sap_dan_bai_da_loai_va_nguon_ngoai_tltk(tmp_path, monkeypatch):
    _hom_nay(monkeypatch)
    _sach(tmp_path)
    _danh_muc(tmp_path, [], [LOAI])
    _ghi(tmp_path, f"G4_A5_SAP_FINAL_{S}.md", "Phương pháp (PMID 99999999).\n")
    assert "SAP dẫn bài chủ nhiệm đã LOẠI" in _truc(tmp_path)["ghi_chu"]
    _ghi(tmp_path, f"G4_A5_SAP_FINAL_{S}.md", "Trọng số (Lumley 2004, doi:10.18637/jss.v009.i08).\n")
    k = _truc(tmp_path)
    assert k["muc"] == NQ.MUC_CAN_XEM and "SAP dẫn nguồn chưa có trong TLTK đề cương nộp: 10.18637/jss.v009.i08" \
        in k["ghi_chu"]


def test_so_a2b_liet_ke_bai_da_loai_la_can_xem_tru_muc_rieng(tmp_path, monkeypatch):
    _hom_nay(monkeypatch)
    _sach(tmp_path)
    _danh_muc(tmp_path, [], [LOAI])
    _ghi(tmp_path, f"G1_A2b_EVIDENCE_LEDGER_{S}.md", "## Bảng Evidence Ledger\n| PMID:99999999 | x |\n")
    k = _truc(tmp_path)
    assert k["muc"] == NQ.MUC_CAN_XEM and "A2b) còn liệt kê 1 bài đã loại" in k["ghi_chu"]
    _ghi(tmp_path, f"G1_A2b_EVIDENCE_LEDGER_{S}.md",
         "## Bảng Evidence Ledger\n| PMID:11111111 | x |\n\n## Đã loại khỏi danh mục trích dẫn của đề tài (không vào "
         "sổ)\n- PMID:99999999 — không lấy được toàn văn\n")
    assert _truc(tmp_path)["muc"] == NQ.MUC_KHOP


def test_danh_muc_khi_chua_co_de_cuong(tmp_path, monkeypatch):
    _hom_nay(monkeypatch)
    _danh_muc(tmp_path, [{"pmid": "11111111", "id": "T01"}, {"doi": "10.1/vn", "id": "T02"}], [LOAI])
    k = _truc(tmp_path)
    assert k["muc"] == NQ.MUC_CAN_XEM and "2/2 mục danh mục trích dẫn chưa có bản ghi" in k["ghi_chu"]
    KRB.ghi(tmp_path, S, {"pmid:11111111": {"status": "ok"}, "doi:10.1/vn": {"status": "ok"}},
            luc="2026-11-15T00:00:00+00:00")
    assert _truc(tmp_path)["muc"] == NQ.MUC_KHOP
    _danh_muc(tmp_path, [{"pmid": "11111111", "id": "T01"}, LOAI], [LOAI])
    assert _truc(tmp_path)["muc"] == NQ.MUC_LECH_MEM  # vừa giữ vừa loại


def test_nguon_g3_va_guideline_khoang_trong(tmp_path, monkeypatch):
    _hom_nay(monkeypatch)
    _sach(tmp_path)
    meta = {"gate_params": {"G3": {"icc_source": "Adams 2004, PMID 15485730"}}}
    assert "nguồn tham số G3 (*_source) chưa có trong TLTK" in _truc(tmp_path, meta)["ghi_chu"]
    _ghi(tmp_path, f"G0_KHOANG_TRONG_{S}.json", {"guideline_lien_quan": [
        {"ten": "KDIGO 2024", "nguon": "PMID 38490803"}, {"ten": "Văn bản trong nước", "nguon": "không chỉ mục"}]})
    g = _truc(tmp_path)["ghi_chu"]
    assert "guideline của khoảng trống «KDIGO 2024»" in g and "Văn bản trong nước" not in g
    # dòng tự khai CHƯA dùng (C1a: «PARTIAL — chưa đọc văn bản hướng dẫn quốc tế») không bị đòi trích
    _ghi(tmp_path, f"G0_KHOANG_TRONG_{S}.json", {"guideline_lien_quan": [
        {"ten": "Hướng dẫn quốc tế", "nguon": "NICE — xã luận PMID 22961881",
         "noi_dung": "PARTIAL — chưa đọc văn bản"}]})
    assert "guideline của khoảng trống" not in _truc(tmp_path)["ghi_chu"]


def test_chua_toi_giai_doan_va_truc_trong_chuoi(tmp_path):
    assert _truc(tmp_path) is None
    assert "trich_dan_tong_quan" in NQ.TRUC_CHUOI and NQ.TRUC_THEO_CONG["trich_dan_tong_quan"] == ("G0", "G1", "G10")


# ── ④ công cụ kiểm rút bài theo từng mã ───────────────────────────────────────────────────────────────────────────
class _Chuoi:
    def check(self, pmids):
        return {p: {"status": "ok" if p != "22222222" else "retracted", "source": "pubmed"} for p in pmids}


class _Crossref:
    def check(self, dois):
        return {d: {"status": "ok", "source": "crossref"} if d != "10.1/loi" else {"status": "timeout"} for d in dois}


class _RW:
    def tra_doi(self, doi):
        return {"status": "retracted", "source": "retraction_watch"} if doi == "10.1/rw" else None


def test_thu_thap_bo_trung_va_kiem_bat_doi_xung(tmp_path):
    _ghi(tmp_path, DC, _de_cuong("A [1]. B [2].", [R1, R2]))
    _danh_muc(tmp_path, [{"pmid": "11111111", "id": "T01"}, {"doi": "10.1/rw", "id": "T02"},
                         {"doi": "10.1/loi", "id": "T03"}, {"pmid": "22222222", "doi": "10.1/x", "id": "T04"}], [])
    muc = KRB.thu_thap(tmp_path, S)
    assert [m["nguon"] for m in muc] == ["TLTK số 1", "TLTK số 2", "danh mục T02", "danh mục T03", "danh mục T04"]
    kq = KRB.kiem(muc, chain=_Chuoi(), crossref=_Crossref(), rw=_RW())
    assert kq["pmid:11111111"]["status"] == "ok" and kq["pmid:22222222"]["status"] == "retracted"
    assert kq["doi:10.1/rw"]["status"] == "retracted"  # Crossref «ok» không phủ được tín hiệu dương của RW
    assert kq["doi:10.1/loi"]["status"] == "unknown_fetch_error"  # trạng thái lạ ⇒ không biết, không bao giờ «ok»
    assert "doi:10.1/x" not in kq  # mục có PMID kiểm theo PMID


def test_ghi_doc_va_ma_thoat(tmp_path, monkeypatch):
    d = tmp_path / "exports" / S
    d.mkdir(parents=True)
    assert KRB.main(["--study", S, "--repo-root", str(tmp_path)]) == 3
    _danh_muc(d, [{"pmid": "11111111", "id": "T01"}], [])
    monkeypatch.setattr(KRB, "kiem", lambda muc: {"pmid:11111111": {"status": "ok", "source": "pubmed",
                                                                     "reason": "", "nguon": "danh mục T01"}})
    assert KRB.main(["--study", S, "--repo-root", str(tmp_path)]) == 0
    assert not (d / KRB.TEP.format(study=S)).exists()  # chạy khô không ghi
    assert KRB.main(["--study", S, "--repo-root", str(tmp_path), "--ghi"]) == 0
    assert KRB.doc_ket_qua(d, S)["tong"] == {"ok": 1}
    monkeypatch.setattr(KRB, "kiem", lambda muc: {"pmid:11111111": {"status": "unknown_fetch_error", "source": None,
                                                                     "reason": "", "nguon": "danh mục T01"}})
    assert KRB.main(["--study", S, "--repo-root", str(tmp_path)]) == 2


# ── ⑤ bộ sinh sổ chứng cứ G1 (A2b) tôn trọng quyết định loại ─────────────────────────────────────────────────────
def test_a2b_tach_bai_da_loai_ra_muc_rieng(tmp_path):
    d = tmp_path / S
    d.mkdir()
    cp0 = {"study": S, "base_query": "q", "pubmed_results": {"all_pmids": ["11111111", "99999999"]}}
    _danh_muc(d, [{"pmid": "11111111", "id": "T01"}], [LOAI])
    G1Q.build_supporting_artifacts(study=S, topic="T", out_dir=d, design={"primary": "Cắt ngang"}, g0_checkpoint=cp0,
                                   effects=[{"pmid": "99999999", "type": "OR", "value": 2}],
                                   meta={"gate_params": {"G1": {}}}, generated_at="2026-11-15 10:00")
    so = (d / f"G1_A2b_EVIDENCE_LEDGER_{S}.md").read_text(encoding="utf-8")
    bang = so.split("## Đã loại khỏi danh mục")[0]
    assert "PMID:11111111" in bang and "PMID:99999999" not in bang
    assert "## Đã loại khỏi danh mục trích dẫn của đề tài (không vào sổ)" in so
    assert "- PMID:99999999 — không lấy được toàn văn (loại ngày 2026-10-25)" in so


def test_trich_bai_g0_da_sang_la_lac_de(tmp_path, monkeypatch):
    # đột biến sống sót ở lượt đầu (15/11/2026): luật «TLTK trích bài G0 sàng là lạc đề» chưa có ca kiểm
    _hom_nay(monkeypatch)
    _sach(tmp_path)
    _ghi(tmp_path, f"G0_TONG_HOP_BANG_CHUNG_{S}.json", {
        "sang_loc": [{"pmid": "11111111", "lien_quan": "khong"}],
        "sang_loc_khong_loc": [{"doi": "10.1/khonglo", "lien_quan": "khong", "ly_do": "x"}]})
    k = _truc(tmp_path)
    assert k["muc"] == NQ.MUC_CAN_XEM and "TLTK trích bài G0 đã sàng là lạc đề: 11111111" in k["ghi_chu"]
    _danh_muc(tmp_path, [{"doi": "10.1/khonglo", "id": "T05"}], [])
    assert "danh mục trích dẫn giữ bài G0 đã sàng là lạc đề: 10.1/khonglo" in _truc(tmp_path)["ghi_chu"]


def test_ket_luan_khong_doc_pass_thanh_dong_bo():
    # Bác sĩ 15/11/2026: «đã kết luận về tính hoàn thiện nhưng kiểm lại thì không đạt được sự thống nhất»
    mo = {"thong_so": [{"ma": "a", "muc": NQ.MUC_KHOP}, {"ma": "b", "muc": NQ.MUC_CAN_XEM}]}
    assert NQ.tieu_chi_g10({**mo, "thiet_ke": None})[0] != "BLOCK"
    assert NQ.ket_luan_trung_thuc(mo).startswith("Kết luận: CHƯA đồng bộ hoàn toàn — còn 1/2 trục mở (b=can_xem)")
    assert "trong PHẠM VI" in NQ.ket_luan_trung_thuc({"thong_so": [{"ma": "a", "muc": NQ.MUC_KHOP}]})
