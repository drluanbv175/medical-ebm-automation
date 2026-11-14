# -*- coding: utf-8 -*-
"""Luật LẮP MỚI G10 (14/11/2026, bác sĩ duyệt nâng cảnh báo B3 của PR #221 thành luật).

Mô tả A12 (`A12_CITATION_VERIFICATION_<mã>.md`, mục «Bằng chứng máy-kiểm») khai số PMID / thời điểm / all_clean LỆCH
biên nhận máy-kiểm (A12_RETRACTION_RECEIPT / A12_METADATA_RECEIPT) ⇒ run_g10_assemble.main() CHẶN lắp mới (mã 2,
needs_input `REASON_A12_DESCRIPTION_MISMATCH`, lệnh `kiem_a12_khop_bien_nhan.py --goi-y`, biểu ngữ BẢN NHÁP).
KHÔNG ĐO ĐƯỢC ⇒ không chặn ở luật này. Cờ --i-know-citations-not-verified bỏ qua được, có ghi bypass_notes.

Ràng buộc bác sĩ đặt: phép chấm SỐNG không đổi — `citation_verification_ok` (G10-AUTO-05 của g10_quality_gate) vẫn
PASS khi chỉ có mô tả lệch, và nhánh «G10 đã khoá hợp lệ» trả về TRƯỚC khi luật mới chạy (C1a đang LOCKED với mô tả
lệch 9 PMID/14-10 so với biên nhận 35/15-10 — không được đổi trạng thái).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import gate_contract as GC  # noqa: E402
import kiem_a12_khop_bien_nhan as KA12  # noqa: E402
import kiem_chi_tiet_he_nghien_cuu as K  # noqa: E402
import run_g10_assemble as G10  # noqa: E402

from tests.test_g10_assemble import _write_cross_sectional_fixture  # noqa: E402
from tests.test_g10_submission_gate_required import (  # noqa: E402
    _configure_test_signing_key,
    _read_g10_needs_input,
    _rmtree_retry,
    _run_main,
    _study_dir,
    _write_clean_citation_artifact,
    _write_ledger_approval,
)


def _ky_g8_g9(d: Path, study: str) -> None:
    """Ký G8 + G9 hợp lệ để cô lập đúng biến đang kiểm (luật mô tả A12)."""
    g8 = "PRESUBMISSION REVIEW — nội dung giả lập test"
    g9 = "AUTHOR INTEGRITY — nội dung giả lập test"
    (d / f"G8_A9_PRESUBMISSION_{study}.md").write_text(g8, encoding="utf-8", newline="\n")
    (d / f"G9_A10_AUTHOR_INTEGRITY_{study}.md").write_text(g9, encoding="utf-8", newline="\n")
    _write_ledger_approval(d, "G8", g8, "PHAN_BIEN_DOC_LAP")
    _write_ledger_approval(d, "G9", g9, "PI_PROJECT_OWNER")


def _so_pmid_bien_nhan(d: Path) -> int:
    return len(json.loads((d / "A12_RETRACTION_RECEIPT.json").read_text(encoding="utf-8"))["pmids_checked"])


def _chen_muc_bang_chung(d: Path, study: str, dong: str) -> None:
    """Chèn mục «1. Bằng chứng máy-kiểm» (bảng như agent viết) với dòng `dong` lên đầu mô tả A12 sạch."""
    p = d / f"A12_CITATION_VERIFICATION_{study}.md"
    p.write_text(
        "## 1. Bằng chứng máy-kiểm\n\n| Bước | Công cụ | Kết quả |\n|---|---|---|\n"
        f"{dong}\n\n## 2. Đối chiếu nội dung\n\n" + p.read_text(encoding="utf-8"),
        encoding="utf-8", newline="\n")


def _khai_bang_chung(d: Path, study: str, so_khai: int) -> None:
    """Mục bằng chứng khai `so_khai` PMID (đúng khuôn agent viết)."""
    _chen_muc_bang_chung(d, study, f"| Rút bài + metadata {so_khai} PMID | `tools/check_citations.py --study {study}` "
                                   "| all_clean=true |")


def _de_tai(tmp_path, monkeypatch, study: str, *, lech: bool | None) -> Path:
    """lech=True: mô tả khai sai số PMID · False: khai đúng · None: không khai (KHÔNG ĐO ĐƯỢC)."""
    d = _study_dir(study)
    _configure_test_signing_key(tmp_path, monkeypatch)
    _write_cross_sectional_fixture(d)
    _write_clean_citation_artifact(d, study)
    _ky_g8_g9(d, study)
    if lech is not None:
        n = _so_pmid_bien_nhan(d)
        _khai_bang_chung(d, study, n + 7 if lech else n)
    return d


def test_ma_ly_do_moi_rieng_biet_va_la_viec_may_lam_duoc():
    ma = GC.REASON_A12_DESCRIPTION_MISMATCH
    cac_ma = {v for k, v in vars(GC).items() if k.startswith("REASON_") and k != "REASON_A12_DESCRIPTION_MISMATCH"}
    assert ma == "A12_DESCRIPTION_MISMATCH_RECEIPT" and ma not in cac_ma, "mã lý do mới phải riêng biệt"
    assert ma not in K.LY_DO_CHO_NGUOI, "máy sửa được bằng --goi-y ⇒ không được tô vàng «chờ người»"


def test_lap_moi_mo_ta_lech_bi_chan_co_needs_input_va_bieu_ngu(tmp_path, monkeypatch):
    study = "PYTEST-A12LAP-LECH"
    d = _de_tai(tmp_path, monkeypatch, study, lech=True)
    try:
        assert KA12.doi_chieu(study, d)["trang_thai"] == "LECH"
        rc = _run_main(study)
        assert rc == GC.EXIT_BLOCKED
        ni = _read_g10_needs_input(d)
        assert ni["reason_code"] == GC.REASON_A12_DESCRIPTION_MISMATCH
        assert ni["remediation"]["command"] == f"python tools/kiem_a12_khop_bien_nhan.py --study {study} --goi-y"
        assert "PMID" in ni["human_message"]
        md = (d / f"DE_CUONG_THONG_NHAT_{study}.md").read_text(encoding="utf-8")
        assert md.startswith("> 🚧 **BẢN NHÁP — CHƯA SẴN SÀNG NỘP.** Mô tả A12 lệch biên nhận")
    finally:
        _rmtree_retry(d)


def test_lap_moi_mo_ta_khop_khong_bi_chan(tmp_path, monkeypatch):
    study = "PYTEST-A12LAP-KHOP"
    d = _de_tai(tmp_path, monkeypatch, study, lech=False)
    try:
        assert KA12.doi_chieu(study, d)["trang_thai"] == "KHOP"
        assert _run_main(study) == 0
    finally:
        _rmtree_retry(d)


def test_khong_do_duoc_khong_chan_o_luat_nay(tmp_path, monkeypatch, capsys):
    study = "PYTEST-A12LAP-KDD"
    d = _de_tai(tmp_path, monkeypatch, study, lech=None)
    try:
        assert KA12.doi_chieu(study, d)["trang_thai"] == "KHONG_DO_DUOC"
        assert _run_main(study) == 0
        assert "Không đo được mô tả A12" in capsys.readouterr().out, "«không đo được» phải được in, không im lặng"
    finally:
        _rmtree_retry(d)


def test_co_bo_qua_cho_lap_nhap_va_ghi_bypass_notes(tmp_path, monkeypatch):
    study = "PYTEST-A12LAP-BOQUA"
    d = _de_tai(tmp_path, monkeypatch, study, lech=True)
    try:
        rc = _run_main(study, ["--i-know-citations-not-verified"])
        assert rc == GC.EXIT_GUARDRAIL_FAIL, "bị bỏ qua bằng cờ xem-trước ⇒ mã 3, không phải 0"
        md = (d / f"DE_CUONG_THONG_NHAT_{study}.md").read_text(encoding="utf-8")
        assert "Luật mô tả A12 ↔ biên nhận bị BỎ QUA bằng --i-know-citations-not-verified" in md
    finally:
        _rmtree_retry(d)


def test_cham_song_khong_doi_citation_verification_ok_van_dat_khi_chi_lech_mo_ta(tmp_path, monkeypatch):
    """G10-AUTO-05 (g10_quality_gate) gọi citation_verification_ok — luật mới KHÔNG được len vào phép chấm sống."""
    study = "PYTEST-A12LAP-SONG"
    d = _de_tai(tmp_path, monkeypatch, study, lech=True)
    try:
        assert KA12.doi_chieu(study, d)["trang_thai"] == "LECH"
        ok, ly_do = G10.citation_verification_ok(study, d)
        assert ok is True, ly_do
    finally:
        _rmtree_retry(d)


def test_g10_da_khoa_tra_ve_truoc_luat_moi(tmp_path, monkeypatch):
    """Gói đã khoá hợp lệ (như C1a) trả EXIT_OK ở nhánh sớm — không lắp lại, luật mô tả A12 không chạy tới."""
    study = "PYTEST-A12LAP-KHOA"
    d = _de_tai(tmp_path, monkeypatch, study, lech=True)
    try:
        (d / G10.G10Q.CHECKPOINT_JSON).write_text("{}", encoding="utf-8", newline="\n")
        monkeypatch.setattr(G10.GC, "ledger_approved", lambda gate, *a, **k: gate == "G10")
        monkeypatch.setattr(G10.G10Q, "evaluate_study",
                            lambda *a, **k: {"status": G10.G10Q.STATUS_LOCKED, "package_sha256": "x"})

        def _cam_lap(*_a, **_k):
            raise AssertionError("gói đã khoá không được lắp lại")

        monkeypatch.setattr(G10, "assemble", _cam_lap)
        monkeypatch.setattr(G10, "luat_mo_ta_a12_khi_lap", _cam_lap)
        assert _run_main(study) == GC.EXIT_OK
    finally:
        _rmtree_retry(d)


def test_thu_muc_trong_la_khong_do_duoc_khong_phai_khop(tmp_path):
    d = tmp_path / "ZZ"
    d.mkdir()
    trang_thai, dong, _ = G10.luat_mo_ta_a12_khi_lap("ZZ", d)
    assert trang_thai == "KHONG_DO_DUOC" and dong and dong[0].startswith("ℹ️")


# ── Sửa theo bình duyệt PR #227 (14/11/2026) ───────────────────────────────────────────────────────────────────────
# (1) Thiếu số PMID tách được KHÔNG được làm bỏ qua phép so thời điểm/all_clean (bản cũ trả KHÔNG ĐO ĐƯỢC sớm ⇒ lọt).
# (2) «PMIDs» (số nhiều) phải được nhận là lời khai số PMID.
# (3) Số PMID CHỈ đọc ở ô tên bước — ghi chú «0 PMID bị rút», «Ghi chú metadata: 2 PMID có erratum» không phải lời khai.

_MOC_BN = "2026-10-15T14:00:46.390410+00:00"


def _a12_tay(tmp_path: Path, muc_bang_chung: str, n_bien_nhan: int = 35, all_clean: bool = True) -> Path:
    """Thư mục đề tài giả (không chữ ký) chỉ để đo `KA12.doi_chieu`: mục 1 = `muc_bang_chung`, biên nhận 35 PMID."""
    d = tmp_path / "ZZ"
    d.mkdir(parents=True)
    (d / "A12_CITATION_VERIFICATION_ZZ.md").write_text(
        "# A12 — ZZ\n\n## 1. Bằng chứng máy-kiểm\n\n| Bước | Công cụ | Kết quả |\n|---|---|---|\n"
        f"{muc_bang_chung}\n\n## 2. Đối chiếu nội dung\n\n| PMID | Bài |\n|---|---|\n| 12345678 | 7 PMID ở mục 2 |\n",
        encoding="utf-8", newline="\n")
    pm = [str(10000000 + i) for i in range(n_bien_nhan)]
    (d / "A12_RETRACTION_RECEIPT.json").write_text(
        json.dumps({"study": "ZZ", "checked_at_utc": _MOC_BN, "pmids_checked": pm, "all_clean": all_clean}),
        encoding="utf-8", newline="\n")
    (d / "A12_METADATA_RECEIPT.json").write_text(
        json.dumps({"study": "ZZ", "checked_at_utc": _MOC_BN, "pmids_checked": pm, "all_resolved": True}),
        encoding="utf-8", newline="\n")
    return d


def test_khong_khai_so_pmid_nhung_thoi_diem_sai_la_lech(tmp_path):
    for i, dong in enumerate(("| Rút bài + metadata 9 bài | x | all_clean=true (2026-10-14T13:42:42Z) |",
                              "| Retraction check | x | all_clean=true (2026-10-14T13:42Z) |",
                              "| Kiểm trích dẫn | `check_citations.py` 9 PMID | (2026-10-14T13:42Z) |")):
        d = _a12_tay(tmp_path / str(i), dong)
        kq = KA12.doi_chieu("ZZ", d)
        assert kq["trang_thai"] == "LECH", (dong, kq)
        assert any("2026-10-14T13:42" in x for x in kq["chi_tiet"]), kq
        assert "so_pmid" not in kq["da_doi_chieu"] and "thoi_diem" in kq["da_doi_chieu"], kq


def test_khong_khai_so_pmid_nhung_all_clean_sai_la_lech(tmp_path):
    d = _a12_tay(tmp_path, "| Rút bài | x | all_clean=true |", all_clean=False)
    kq = KA12.doi_chieu("ZZ", d)
    assert kq["trang_thai"] == "LECH" and kq["da_doi_chieu"] == ["all_clean"], kq


def test_so_nhieu_pmids_duoc_nhan_la_loi_khai(tmp_path):
    d = _a12_tay(tmp_path, "| Rút bài + metadata 9 PMIDs | x | all_clean=true (2026-10-15T14:00Z) |")
    kq = KA12.doi_chieu("ZZ", d)
    assert kq["trang_thai"] == "LECH" and kq["chi_tiet"] == ["mô tả khai 9 PMID, biên nhận rút bài kiểm 35"], kq


def test_ghi_chu_o_khac_hoac_van_xuoi_khong_phai_loi_khai_so_pmid(tmp_path):
    for i, muc in enumerate((
        "| Rút bài + metadata 35 PMID | x | all_clean=true (2026-10-15T14:00Z); 0 PMID bị rút |",
        "| Rút bài + metadata 35 PMID | x | all_clean=true (2026-10-15T14:00Z) |\n\n"
        "Ghi chú metadata: 2 PMID có erratum (không phải rút bài).",
    )):
        d = _a12_tay(tmp_path / str(i), muc)
        kq = KA12.doi_chieu("ZZ", d)
        assert kq["trang_thai"] == "KHOP", (muc, kq)
        assert kq["da_doi_chieu"] == ["so_pmid", "thoi_diem", "all_clean"], kq


def test_o_ten_buoc_khong_co_so_thi_so_o_o_khac_khong_tinh(tmp_path):
    """Ô tên bước không ghi số ⇒ «0 PMID bị rút» ở ô kết quả KHÔNG thành lời khai «0 PMID đã kiểm»."""
    d = _a12_tay(tmp_path, "| Rút bài + metadata | x | all_clean=true (2026-10-15T14:00Z); 0 PMID bị rút |")
    kq = KA12.doi_chieu("ZZ", d)
    assert kq["trang_thai"] == "KHOP" and kq["da_doi_chieu"] == ["thoi_diem", "all_clean"], kq


def test_khai_sai_so_o_o_ten_buoc_van_bi_bat_du_co_ghi_chu(tmp_path):
    d = _a12_tay(tmp_path, "| Rút bài + metadata 9 PMID | x | all_clean=true (2026-10-15T14:00Z); 0 PMID bị rút |")
    kq = KA12.doi_chieu("ZZ", d)
    assert kq["trang_thai"] == "LECH" and kq["chi_tiet"] == ["mô tả khai 9 PMID, biên nhận rút bài kiểm 35"], kq


def test_dong_goi_y_dan_vao_la_khop(tmp_path):
    d = _a12_tay(tmp_path, "| Rút bài + metadata 9 PMID | x | all_clean=true (2026-10-14T13:42Z) |")
    assert KA12.doi_chieu("ZZ", d)["trang_thai"] == "LECH"
    _a12 = d / "A12_CITATION_VERIFICATION_ZZ.md"
    cu = _a12.read_text(encoding="utf-8")
    _a12.write_text(cu.replace("| Rút bài + metadata 9 PMID | x | all_clean=true (2026-10-14T13:42Z) |",
                               KA12.goi_y("ZZ", d)), encoding="utf-8", newline="\n")
    kq = KA12.doi_chieu("ZZ", d)
    assert kq["trang_thai"] == "KHOP" and kq["da_doi_chieu"] == ["so_pmid", "thoi_diem", "all_clean"], kq


def test_khong_co_loi_khai_nao_kiem_duoc_la_khong_do_duoc(tmp_path):
    d = _a12_tay(tmp_path, "| Kiểm trích dẫn | `check_citations.py` | mã 0 |")
    kq = KA12.doi_chieu("ZZ", d)
    assert kq["trang_thai"] == "KHONG_DO_DUOC" and kq["da_doi_chieu"] == [], kq


def test_lap_moi_khong_khai_so_pmid_thoi_diem_sai_bi_chan(tmp_path, monkeypatch):
    """Ca bình duyệt PR #227 nêu: «9 PMIDs»/«9 bài» kèm thời điểm sai từng ra KHÔNG ĐO ĐƯỢC ⇒ main() trả 0."""
    study = "PYTEST-A12LAP-MOC"
    d = _de_tai(tmp_path, monkeypatch, study, lech=None)
    try:
        _chen_muc_bang_chung(d, study, "| Rút bài + metadata 9 bài | `tools/check_citations.py` | "
                                       "all_clean=true (2026-10-14T13:42:42Z) |")
        assert KA12.doi_chieu(study, d)["trang_thai"] == "LECH"
        assert _run_main(study) == GC.EXIT_BLOCKED
        ni = _read_g10_needs_input(d)
        assert ni["reason_code"] == GC.REASON_A12_DESCRIPTION_MISMATCH
        assert "2026-10-14T13:42" in ni["human_message"]
    finally:
        _rmtree_retry(d)


def test_lap_moi_khai_dung_kem_ghi_chu_khong_bi_chan(tmp_path, monkeypatch):
    """Mô tả khai ĐÚNG số PMID kèm ghi chú «0 PMID bị rút» không được chặn lắp (bản cũ chặn sai, mã 2)."""
    study = "PYTEST-A12LAP-GHICHU"
    d = _de_tai(tmp_path, monkeypatch, study, lech=None)
    try:
        n = _so_pmid_bien_nhan(d)
        _chen_muc_bang_chung(d, study, f"| Rút bài + metadata {n} PMID | `tools/check_citations.py` | "
                                       "all_clean=true; 0 PMID bị rút |\n\nGhi chú metadata: 2 PMID có erratum.")
        assert KA12.doi_chieu(study, d)["trang_thai"] == "KHOP"
        assert _run_main(study) == 0
    finally:
        _rmtree_retry(d)
