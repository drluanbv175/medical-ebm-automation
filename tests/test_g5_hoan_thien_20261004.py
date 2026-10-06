# -*- coding: utf-8 -*-
"""Soát từng cổng G0–G10 (04/10/2026) — cổng G5 (khoá dữ liệu): khoá hành vi các bản vá G5-01…G5-08.

G5-01 DMP: nhãn chỉ neo ở dòng cấu trúc; DMP chưa hoàn tất ⇒ không khoá được; mục sống còn ô trống sau khoá ⇒ REVIEW
      (chặn ký); hoàn tất rồi khoá lại CÙNG dữ liệu ⇒ READY (khoá lại chấm lại tài liệu khi G5 chưa ký).
G5-02 Thứ tự thời gian: nạp dữ liệu khi SAP chưa khoá ⇒ từ chối nạp; nạp/làm sạch trước lần ký G2/G4 đầu tiên ⇒ BLOCK;
      SAP ký lại sau khi nạp mà không có SAP AMENDMENT ⇒ REVIEW; so mốc theo đúng độ chính xác của mốc nạp.
G5-03 Cột ngoài dictionary ⇒ truy vấn mở (làm sạch) và BLOCK (bộ chấm G5-AUTO-07b).
G5-04 Đóng truy vấn bằng tệp giải quyết (mã + lý do + người + thời điểm), gắn băm; «da_sua» không đóng được giá
      trị còn đó.
G5-05 Ở tests/test_g5_relock_overwrite_guard.py (T3–T5).
G5-06 Cờ «Identifier?» của bộ biến riêng tới được dictionary ⇒ G5-AUTO-02 BLOCK; danh sách định danh khớp bước nạp.
G5-07 Hồ sơ vận hành G5-OPS-2026.2: bằng chứng rỗng ⇒ lỗi; rà audit trail bắt buộc; SDV thiếu ⇒ REVIEW (chặn ký).
G5-08 Định tính: sổ bản gỡ băng (băm, khử định danh, chỉ đọc, quét mẫu PII) — khoá chặn khi chưa đạt; sửa sau khoá
      ⇒ BLOCK.
Dữ liệu tổng hợp, không PII thật, không gọi mạng; khoá ký là khoá giả tạm (EBM_GATE_KEY_PATH).
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import stat
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
for _p in (str(TOOLS_DIR), str(REPO_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import approve_gate as AG  # noqa: E402
import clean_research_dataset as CLEAN  # noqa: E402
import cong_song as CS  # noqa: E402
import g4_quality_gate as G4Q  # noqa: E402
import g5_quality_gate as G5Q  # noqa: E402
import import_real_dataset as RDI  # noqa: E402
import lock_analysis_dataset as LAD  # noqa: E402
import run_g5_auto as G5A  # noqa: E402

from tests._chuoi_da_chot import danh_dau_de_tai_thu  # noqa: E402
from tests.g5_test_helpers import (  # noqa: E402
    configure_test_signing_key,
    lock_g5_fixture,
    prepare_clean_g5_study,
    prepare_locked_g5_study,
    write_g5_toolkit,
)

_NGUON = "record_id,age,sex,exposure_var,primary_outcome\nS001,45,F,0,0\nS002,52,M,1,1\n"


def _csv(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def _cham(study: str, out_dir: Path, root: Path) -> dict:
    CS.xoa_dem()
    return G5Q.evaluate_study(study, out_dir, repo_root=root, write=False)


def _tieu_chi(report: dict, ma: str) -> dict:
    return next(c for c in report["automatic_criteria"] if c["id"] == ma)


def _chua_dat(report: dict) -> list:
    return [(c["id"], c["status"]) for c in report["automatic_criteria"] if c["status"] != "PASS"]


def _ghi_de_chi_doc(path: Path, text: str) -> None:
    """Sửa một tệp chỉ đọc như người thật (mở quyền ghi, ghi, khoá lại)."""
    if path.exists():
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
    path.write_text(text, encoding="utf-8", newline="\n")


# ── G5-01 — DMP ───────────────────────────────────────────────────────────────────────────────────────────────────────

def test_g5_01_nhan_trong_cau_van_khong_phai_neo_tieu_de_va_gach_dau_dong_dam_moi_la_neo():
    text = ("> **BẢO MẬT:** dữ liệu đã được KHỬ ĐỊNH DANH trước khi vào máy phân tích.\n"
            "- Provenance: bản khử định danh lưu riêng\n"
            "## KHỬ ĐỊNH DANH\n"
            "Bảng ánh xạ tách khỏi dữ liệu phân tích.\n"
            "- **Phân quyền:** tối thiểu cần biết\n")
    assert G5Q._dmp_neo_nhan(text, ("KHỬ ĐỊNH DANH", "PHÂN QUYỀN")) == {"KHỬ ĐỊNH DANH": 2, "PHÂN QUYỀN": 4}
    # Chỉ có trong câu văn ⇒ coi là THIẾU MỤC (bản cũ «find()» lấy câu cảnh báo làm thân mục ⇒ PASS giả).
    chi_cau_van = "> **BẢO MẬT:** dữ liệu đã KHỬ ĐỊNH DANH, bảng ánh xạ tách riêng, không PII trong dữ liệu.\n"
    assert G5Q._dmp_noi_dung_thieu_duoi_nhan(chi_cau_van, ("KHỬ ĐỊNH DANH",)) == ["KHỬ ĐỊNH DANH"]
    # «ICH E6(R3)» là nhãn tham chiếu: không neo, không đòi thân mục (vẫn phải có mặt — kiểm ở missing_dmp).
    assert "ICH E6(R3)" not in G5Q._dmp_neo_nhan("## ICH E6(R3)\nx\n", G5Q._REQUIRED_DMP_TOKENS)


def test_g5_01_dmp_nhap_cua_bo_sinh_chua_hoan_tat_cho_thoi_diem_khoa():
    rows, specialty = G5A.build_redcap_rows("cohort", "Tăng huyết áp")
    dmp = G5A.generate_artifact("G5-DMP", "Tăng huyết áp", "cohort", 200, 180, 90, "2026-10-04", rows, specialty)
    ly_do = " | ".join(G5Q.dmp_chua_hoan_tat_khi_khoa(dmp))
    assert "bản nháp" in ly_do and "ô trống" in ly_do and "chưa đánh dấu" in ly_do, ly_do
    # Văn mẫu của bộ sinh vẫn qua luật NỘI DUNG (chưa có dữ liệu thì DMP là bản nháp hợp lệ).
    assert G5Q._dmp_noi_dung_thieu_duoi_nhan(dmp, G5Q._REQUIRED_DMP_TOKENS) == []


def test_g5_01_dmp_con_draft_thi_khong_khoa_duoc(tmp_path, monkeypatch):
    configure_test_signing_key(tmp_path, monkeypatch)
    study = "G5-01-DRAFT"
    ctx = prepare_clean_g5_study(study, _csv(tmp_path / "nguon.csv", _NGUON),
                                 exports_root=tmp_path / "exports", repo_root=tmp_path)
    dmp = ctx["out_dir"] / f"G5_A6_DATA_MGMT_{study}.md"
    dmp.write_text(dmp.read_text(encoding="utf-8").replace(
        "# Kế hoạch quản lý dữ liệu kiểm thử", "# Kế hoạch quản lý dữ liệu kiểm thử (DRAFT)").replace(
        "Checklist khóa DB đã hoàn tất, có chữ ký người khóa và người chứng kiến.",
        "- [ ] Ngày khóa DB: [CẦN BÁC SĨ ĐIỀN]\n- [x] Backup kiểm tra thành công"), encoding="utf-8", newline="\n")
    manifest = lock_g5_fixture(study, ctx, exports_root=tmp_path / "exports", repo_root=tmp_path)
    assert manifest["status"] == LAD.BLOCKED_STATUS
    loi = " | ".join(b for b in manifest["blockers"] if b.startswith("dmp_not_finalized"))
    assert "bản nháp" in loi and "ô trống" in loi and "chưa đánh dấu" in loi, manifest["blockers"]


def test_g5_01_muc_song_con_o_trong_review_roi_hoan_tat_va_khoa_lai_thi_ready(tmp_path, monkeypatch):
    configure_test_signing_key(tmp_path, monkeypatch)
    study = "G5-01-SONG"
    exports_root = tmp_path / "exports"
    nhan_cu = "Thời hạn lưu trữ và hủy theo chính sách đơn vị, có ghi rõ người chịu trách nhiệm."

    def them_o_trong(out_dir: Path) -> None:
        p = out_dir / f"G5_A6_DATA_MGMT_{study}.md"
        p.write_text(p.read_text(encoding="utf-8").replace(
            nhan_cu, nhan_cu + "\nSố năm lưu trữ theo quyết định IRB: [CẦN BÁC SĨ ĐIỀN]"),
            encoding="utf-8", newline="\n")

    ctx = prepare_clean_g5_study(study, _csv(tmp_path / "nguon.csv", _NGUON),
                                 exports_root=exports_root, repo_root=tmp_path)
    out_dir = ctx["out_dir"]
    them_o_trong(out_dir)
    assert lock_g5_fixture(study, ctx, exports_root=exports_root, repo_root=tmp_path)["status"] == LAD.LOCKED_STATUS
    r = _cham(study, out_dir, tmp_path)
    assert r["status"] == G5Q.STATUS_DRAFT_REVIEW, _chua_dat(r)
    assert _tieu_chi(r, "G5-AUTO-03")["status"] == "REVIEW"

    # Người rà hoàn tất mục sống ⇒ băm DMP lệch bản khoá ⇒ BLOCK cho tới khi khoá lại.
    dmp = out_dir / f"G5_A6_DATA_MGMT_{study}.md"
    dmp.write_text(dmp.read_text(encoding="utf-8").replace("[CẦN BÁC SĨ ĐIỀN]", "10 năm sau khi kết thúc đề tài"),
                   encoding="utf-8", newline="\n")
    assert _cham(study, out_dir, tmp_path)["status"] == G5Q.STATUS_BLOCKED
    khoa_cu = json.loads((out_dir / "DATA_LOCK_manifest.json").read_text(encoding="utf-8"))

    lai = lock_g5_fixture(study, ctx, exports_root=exports_root, repo_root=tmp_path)
    assert lai["status"] == LAD.LOCKED_STATUS, lai.get("blockers")
    assert lai["sha256"] == khoa_cu["sha256"], "dữ liệu khoá giữ nguyên"
    assert lai["lan_khoa_truoc"]["dmp_sha256"] == khoa_cu["dmp_sha256"] != lai["dmp_sha256"]
    r2 = _cham(study, out_dir, tmp_path)
    assert r2["status"] == G5Q.STATUS_READY, _chua_dat(r2)


def test_g5_01_khoa_thieu_dmp_bi_tu_choi(tmp_path, monkeypatch):
    configure_test_signing_key(tmp_path, monkeypatch)
    study = "G5-01-THIEU-DMP"
    ctx = prepare_clean_g5_study(study, _csv(tmp_path / "nguon.csv", _NGUON),
                                 exports_root=tmp_path / "exports", repo_root=tmp_path)
    (ctx["out_dir"] / f"G5_A6_DATA_MGMT_{study}.md").unlink()
    manifest = lock_g5_fixture(study, ctx, exports_root=tmp_path / "exports", repo_root=tmp_path)
    assert manifest["status"] == LAD.BLOCKED_STATUS
    assert any(b.startswith("missing_dmp") for b in manifest["blockers"]), manifest["blockers"]


def test_g5_01_dmp_doi_thanh_draft_sau_khoa_thi_auto03_block(de_tai_cho_ky):
    study, out_dir, root = de_tai_cho_ky
    dmp = out_dir / f"G5_A6_DATA_MGMT_{study}.md"
    dmp.write_text(dmp.read_text(encoding="utf-8").replace(
        "# Kế hoạch quản lý dữ liệu kiểm thử", "# Kế hoạch quản lý dữ liệu kiểm thử (DRAFT)"),
        encoding="utf-8", newline="\n")
    c = _tieu_chi(_cham(study, out_dir, root), "G5-AUTO-03")
    assert c["status"] == "BLOCK" and "chưa hoàn tất" in c["evidence"], c


def test_g5_01_khoa_lai_khi_da_ky_thi_khong_doi_gi(tmp_path, monkeypatch):
    configure_test_signing_key(tmp_path, monkeypatch)
    study = "G5-01-DA-KY"
    _, report = prepare_locked_g5_study(study, _csv(tmp_path / "nguon.csv", _NGUON),
                                        exports_root=tmp_path / "exports", repo_root=tmp_path)
    assert report["status"] == G5Q.STATUS_LOCKED
    out_dir = tmp_path / "exports" / study
    truoc = (out_dir / "DATA_LOCK_manifest.json").read_bytes()
    lam_sach = json.loads((out_dir / CLEAN.REPORT_NAME).read_text(encoding="utf-8"))
    ctx = {"out_dir": out_dir, "clean_path": out_dir / lam_sach["clean_dataset_path"],
           "query_log": out_dir / lam_sach["query_log"],
           "dictionary_path": out_dir / f"G5_REDCap_dictionary_{study}.csv"}
    lock_g5_fixture(study, ctx, exports_root=tmp_path / "exports", repo_root=tmp_path)
    assert (out_dir / "DATA_LOCK_manifest.json").read_bytes() == truoc
    assert _cham(study, out_dir, tmp_path)["status"] == G5Q.STATUS_LOCKED


# ── G5-02 — thứ tự thời gian ──────────────────────────────────────────────────────────────────────────────────────────

def test_g5_02_nap_du_lieu_khi_sap_chua_khoa_bi_tu_choi_khong_sao_ban_tho(tmp_path):
    data = _csv(tmp_path / "nguon.csv", _NGUON)
    manifest = RDI.import_dataset("G5-02-CHUA-SAP", data, exports_root=tmp_path / "exports")
    assert manifest["status"] == RDI.BLOCKED_STATUS
    assert any(i["type"] == "sap_chua_khoa" for i in manifest["pii_scan"]["issues"])
    assert manifest["raw_readonly_path"] is None
    assert not (tmp_path / "exports" / "G5-02-CHUA-SAP" / "02_raw_readonly").exists()
    # Đề tài thử nghiệm tổng hợp được miễn như mọi chốt sổ cái khác.
    danh_dau_de_tai_thu(tmp_path / "exports", "G5-02-TONG-HOP")
    assert RDI.import_dataset("G5-02-TONG-HOP", data, exports_root=tmp_path / "exports")["status"] == RDI.READY_STATUS


def test_g5_02_so_moc_theo_do_chinh_xac_cua_moc_nap():
    ky = datetime(2026, 10, 5, 10, 12, 37, 500000, tzinfo=timezone.utc)
    assert G5Q._som_hon(datetime(2026, 10, 5, 10, 12, 37, tzinfo=timezone.utc), ky) is False, "cùng giây ≠ trước"
    assert G5Q._som_hon(datetime(2026, 10, 5, 10, 12, 36, tzinfo=timezone.utc), ky) is True
    assert G5Q._som_hon(datetime(2026, 10, 5, 10, 12, 37, 100000, tzinfo=timezone.utc), ky) is True
    assert G5Q._moc_utc("2026-10-05T17:12:37") is not None, "giờ địa phương không kèm múi giờ vẫn quy được về UTC"


@pytest.fixture()
def de_tai_cho_ky(tmp_path, monkeypatch):
    """Đề tài đã khoá kỹ thuật (READY), chưa ký G5."""
    configure_test_signing_key(tmp_path, monkeypatch)
    study = "G5-THU-TU"
    prepare_locked_g5_study(study, _csv(tmp_path / "nguon.csv", _NGUON), exports_root=tmp_path / "exports",
                            repo_root=tmp_path, approve_g5=False)
    return study, tmp_path / "exports" / study, tmp_path


def test_g5_02_nap_truoc_lan_ky_g2_dau_tien_thi_block(de_tai_cho_ky, monkeypatch):
    study, out_dir, root = de_tai_cho_ky
    sau = datetime.now(timezone.utc) + timedelta(hours=1)
    that = G5Q._moc_ky_so_cai
    monkeypatch.setattr(G5Q, "_moc_ky_so_cai",
                        lambda s, g, a, r: (sau, sau) if g == "G2" else that(s, g, a, r))
    r = _cham(study, out_dir, root)
    c = _tieu_chi(r, "G5-AUTO-05b")
    assert c["status"] == "BLOCK" and "TRƯỚC lần ký G2" in c["evidence"], c
    assert r["status"] == G5Q.STATUS_BLOCKED


def test_g5_02_sap_ky_lai_sau_khi_nap_thi_review_tru_khi_co_sap_amendment(de_tai_cho_ky, monkeypatch):
    study, out_dir, root = de_tai_cho_ky
    truoc = datetime.now(timezone.utc) - timedelta(days=30)
    sau = datetime.now(timezone.utc) + timedelta(hours=1)
    monkeypatch.setattr(G5Q, "_moc_ky_so_cai", lambda s, g, a, r: (truoc, sau if g == "G4" else truoc))
    r = _cham(study, out_dir, root)
    c = _tieu_chi(r, "G5-AUTO-05b")
    assert c["status"] == "REVIEW" and "SAP AMENDMENT" in c["evidence"], c
    assert r["status"] == G5Q.STATUS_DRAFT_REVIEW
    monkeypatch.setattr(G4Q, "_dong_sua_doi_sap", lambda text: ["| v1.1 | SAP AMENDMENT | đổi quần thể |"])
    assert _tieu_chi(_cham(study, out_dir, root), "G5-AUTO-05b")["status"] == "PASS"


def test_g5_02_chuoi_that_nap_sau_khi_ky_thi_pass(de_tai_cho_ky):
    study, out_dir, root = de_tai_cho_ky
    assert _tieu_chi(_cham(study, out_dir, root), "G5-AUTO-05b")["status"] == "PASS"


# ── G5-03 — cột ngoài dictionary ──────────────────────────────────────────────────────────────────────────────────────

def test_g5_03_lam_sach_cot_khong_khai_la_truy_van_mo(tmp_path):
    study = "G5-03-CLEAN"
    out_dir = tmp_path / "exports" / study
    dictionary = write_g5_toolkit(study, out_dir)
    data = _csv(tmp_path / "nguon.csv", "record_id,age,tuoi_nam\nS001,45,450\nS002,52,52\n")
    report = CLEAN.clean_dataset(study, data, dictionary_path=dictionary, exports_root=tmp_path / "exports")
    assert report["status"] != CLEAN.CLEAN_READY_STATUS
    log = (out_dir / report["query_log"]).read_text(encoding="utf-8")
    assert "undeclared_column" in log and "tuoi_nam" in log


def test_g5_03_bo_cham_cot_ngoai_dictionary_hoac_thieu_bien_bat_buoc_thi_block(de_tai_cho_ky, monkeypatch):
    study, out_dir, root = de_tai_cho_ky
    that = G5Q._doc_header_csv
    monkeypatch.setattr(G5Q, "_doc_header_csv", lambda p: [*that(p), "tuoi_nam"])
    c = _tieu_chi(_cham(study, out_dir, root), "G5-AUTO-07b")
    assert c["status"] == "BLOCK" and "tuoi_nam" in c["evidence"], c
    monkeypatch.setattr(G5Q, "_doc_header_csv", lambda p: [h for h in that(p) if h != "record_id"])
    c = _tieu_chi(_cham(study, out_dir, root), "G5-AUTO-07b")
    assert c["status"] == "BLOCK" and "record_id" in c["evidence"], c


def test_g5_03_chuoi_that_du_cot_thi_pass(de_tai_cho_ky):
    study, out_dir, root = de_tai_cho_ky
    c = _tieu_chi(_cham(study, out_dir, root), "G5-AUTO-07b")
    assert c["status"] == "PASS" and "5/5" in c["evidence"], c


# ── G5-04 — đóng truy vấn có lý do ────────────────────────────────────────────────────────────────────────────────────

_NGUON_121 = "record_id,age,sex,exposure_var,primary_outcome\nS001,45,F,0,0\nS002,121,M,1,1\n"


def _giai_quyet(path: Path, **ghi_de) -> Path:
    dong = {"issue_type": "range_high", "column": "age", "row": "2", "resolution": "xac_nhan_dung",
            "ly_do": "Đã đối chiếu hồ sơ nguồn: tuổi ghi đúng", "owner_ref": "DM-01",
            "resolved_at": datetime.now().date().isoformat()}
    dong.update(ghi_de)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(dong))
        w.writeheader()
        w.writerow(dong)
    return path


def _lam_sach(tmp_path: Path, study: str, giai_quyet=None) -> dict:
    out_dir = tmp_path / "exports" / study
    dictionary = write_g5_toolkit(study, out_dir)
    data = _csv(tmp_path / f"{study}.csv", _NGUON_121)
    return CLEAN.clean_dataset(study, data, dictionary_path=dictionary, exports_root=tmp_path / "exports",
                               query_resolutions_path=giai_quyet)


def test_g5_04_gia_tri_ngoai_khoang_khong_giai_quyet_thi_mo(tmp_path):
    report = _lam_sach(tmp_path, "G5-04-MO")
    assert report["status"] != CLEAN.CLEAN_READY_STATUS and report["open_query_count"] >= 1


@pytest.mark.parametrize(("ghi_de", "loi"), [
    ({"resolution": "da_sua"}, "da_sua_nhung_gia_tri_van_con"),
    ({"resolved_at": "2999-01-01"}, "resolved_at_khong_phai_ISO_hoac_o_tuong_lai"),
    ({"resolution": "bo_qua"}, "ma_dong_khong_hop_le"),
    ({"ly_do": "[CẦN]"}, "thieu_ly_do"),
    ({"owner_ref": ""}, "thieu_owner_ref"),
])
def test_g5_04_giai_quyet_khong_hop_le_khong_dong_duoc_truy_van(tmp_path, ghi_de, loi):
    report = _lam_sach(tmp_path, "G5-04-SAI", _giai_quyet(tmp_path / "gq.csv", **ghi_de))
    assert report["status"] != CLEAN.CLEAN_READY_STATUS and report["open_query_count"] >= 1
    assert any(loi in e for e in report["query_resolution_errors"]), report["query_resolution_errors"]


def test_g5_04_xac_nhan_dung_co_ly_do_thi_khoa_duoc_va_tep_giai_quyet_gan_bam(tmp_path, monkeypatch):
    configure_test_signing_key(tmp_path, monkeypatch)
    study = "G5-04-DONG"
    _, report = prepare_locked_g5_study(study, _csv(tmp_path / "nguon.csv", _NGUON_121),
                                        exports_root=tmp_path / "exports", repo_root=tmp_path, approve_g5=False,
                                        query_resolutions_path=_giai_quyet(tmp_path / "gq.csv"))
    assert report["status"] == G5Q.STATUS_READY
    out_dir = tmp_path / "exports" / study
    lam_sach = json.loads((out_dir / CLEAN.REPORT_NAME).read_text(encoding="utf-8"))
    manifest = json.loads((out_dir / "DATA_LOCK_manifest.json").read_text(encoding="utf-8"))
    cp = json.loads((out_dir / "G5_checkpoint.json").read_text(encoding="utf-8"))
    assert lam_sach["n_query_resolved"] == 1
    assert lam_sach["query_resolutions_sha256"] == manifest["query_resolutions_sha256"] == \
        cp["query_resolutions_sha256"] is not None
    # Sửa tệp giải quyết sau khi khoá ⇒ không còn khớp băm đã gắn ⇒ BLOCK.
    tep = out_dir / lam_sach["query_resolutions"]
    _ghi_de_chi_doc(tep, tep.read_text(encoding="utf-8").replace("DM-01", "DM-99"))
    assert _cham(study, out_dir, tmp_path)["status"] == G5Q.STATUS_BLOCKED


# ── G5-06 — cờ định danh của bộ biến riêng ───────────────────────────────────────────────────────────────────────────

def _bo_bien_rieng(out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    cot = ["Variable / Field Name", "Form Name", "Section Header", "Field Type", "Field Label",
           "Choices, Calculations, OR Slider Labels", "Field Note", "Text Validation Type OR Show Slider Number",
           "Text Validation Min", "Text Validation Max", "Identifier?", "Branching Logic (Show field only if...)",
           "Required Field?", "Custom Alignment", "Question Number (surveys only)", "Matrix Group Name",
           "Matrix Ranking?", "Field Annotation"]
    dong = [("record_id", "Mã bản ghi", "", "y"), ("ma_benh_an", "Mã bệnh án", "y", "n"),
            ("sdt", "Số điện thoại liên hệ", "y", "n"), ("tuoi", "Tuổi (năm)", "", "n")]
    p = out_dir / G5A.BO_BIEN_RIENG_TEN_FILE
    with p.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cot)
        w.writeheader()
        for ten, nhan, dinh_danh, bat_buoc in dong:
            w.writerow({"Variable / Field Name": ten, "Form Name": "main", "Field Type": "text", "Field Label": nhan,
                        "Identifier?": dinh_danh, "Required Field?": bat_buoc})
    return p


def test_g5_06_co_identifier_cua_bo_bien_rieng_toi_duoc_dictionary_va_auto02_block(tmp_path):
    out_dir = tmp_path / "G5-06"
    _bo_bien_rieng(out_dir)
    rows = G5A.nap_bo_bien_rieng(out_dir, "G5-06")
    co = {r[0]: r[12] for r in rows}
    assert co == {"record_id": "", "ma_benh_an": "y", "sdt": "y", "tuoi": ""}
    path, _ = G5A.generate_csv("G5-06", out_dir, rows)
    with path.open(encoding="utf-8", newline="") as f:
        da_ghi = {r["Variable / Field Name"]: r["Identifier?"] for r in csv.DictReader(f)}
    assert da_ghi["ma_benh_an"] == da_ghi["sdt"] == "y" and da_ghi["tuoi"] == ""
    issues = " ".join(G5Q._read_redcap_dictionary(path)["issues"])
    assert "redcap_identifier_rows" in issues and "ma_benh_an" in issues and "sdt" in issues


def test_g5_06_bundle_12_truong_van_ghi_duoc_cot_identifier_rong(tmp_path):
    rows, _ = G5A.build_redcap_rows("cohort", "Tăng huyết áp")
    path, _ = G5A.generate_csv("G5-06-B", tmp_path, rows)
    with path.open(encoding="utf-8", newline="") as f:
        assert {r["Identifier?"] for r in csv.DictReader(f)} == {""}


@pytest.mark.parametrize("ten", ["ma_benh_an", "sdt", "ten_benh_nhan", "hoten", "ma_bn", "so_dien_thoai",
                                 "initials", "dia_chi", "cccd", "email", "patient_name"])
def test_g5_06_ten_bien_dinh_danh_cua_buoc_nap_cung_bi_bo_cham_nhan(ten):
    assert RDI._header_issue(ten), "tiền đề: bước nạp coi là định danh"
    assert G5Q._la_ten_bien_dinh_danh(ten)


@pytest.mark.parametrize("ten", ["drug_name", "age", "record_id", "study_subject_id", "transcript_id"])
def test_g5_06_bien_nghien_cuu_khong_bi_coi_la_dinh_danh(ten):
    assert not G5Q._la_ten_bien_dinh_danh(ten)


# ── G5-07 — hồ sơ vận hành 2026.2 ─────────────────────────────────────────────────────────────────────────────────────

def _ho_so(tmp_path: Path) -> Path:
    write_g5_toolkit("G5-07", tmp_path / "G5-07")
    return tmp_path / "G5-07" / G5Q.OPERATIONAL_READINESS_JSON


def _sua_ho_so(path: Path, sua) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    sua(payload)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    return G5Q.evaluate_operational_readiness(path)


def test_g5_07_ho_so_hop_le_khong_canh_bao(tmp_path):
    r = G5Q.evaluate_operational_readiness(_ho_so(tmp_path))
    assert r["valid"] is True and r["issues"] == [] and r["canh_bao"] == []


@pytest.mark.parametrize(("sua", "loi"), [
    (lambda p: p["access_control_review"].update(evidence_ref=""),
     "thieu_bang_chung:access_control_review.evidence_ref"),
    (lambda p: p["backup_restore_test"].update(evidence_ref="  "), "thieu_bang_chung:backup_restore_test.evidence_ref"),
    (lambda p: p["protocol_deviations"].update(log_ref=""), "thieu_bang_chung:protocol_deviations.log_ref"),
    (lambda p: p.pop("audit_trail_review"), "audit_trail_not_reviewed"),
    (lambda p: p["audit_trail_review"].update(completed=False), "audit_trail_not_reviewed"),
    (lambda p: p["audit_trail_review"].update(evidence_ref="[CẦN MÃ]"),
     "thieu_bang_chung:audit_trail_review.evidence_ref"),
    (lambda p: p["audit_trail_review"].update(reviewed_at="2999-01-01"), "future_audit_reviewed_at"),
    (lambda p: p.update(schema_version="G5-OPS-2026.1"), "schema_version_khong_phai_G5-OPS-2026.2"),
])
def test_g5_07_bang_chung_rong_hoac_thieu_ra_audit_trail_la_loi(tmp_path, sua, loi):
    r = _sua_ho_so(_ho_so(tmp_path), sua)
    assert r["valid"] is False and loi in r["issues"], r["issues"]


def test_g5_07_sdv_thieu_chi_canh_bao_khai_khong_ap_dung_co_ly_do_thi_hop_le(tmp_path):
    path = _ho_so(tmp_path)
    r = _sua_ho_so(path, lambda p: p.pop("source_data_verification"))
    assert r["valid"] is True and r["canh_bao"] and "sdv" in r["canh_bao"][0]
    r = _sua_ho_so(path, lambda p: p.update(source_data_verification={
        "not_applicable_reason": "Dữ liệu nhập thẳng vào eCRF, không có hồ sơ nguồn giấy"}))
    assert r["valid"] is True and r["canh_bao"] == []


def test_g5_07_sdv_thieu_thi_trang_thai_review_va_approve_gate_khong_ky(tmp_path, monkeypatch):
    configure_test_signing_key(tmp_path, monkeypatch)
    study = "G5-07-SDV"

    def bo_sdv(out_dir: Path) -> None:
        _sua_ho_so(out_dir / G5Q.OPERATIONAL_READINESS_JSON, lambda p: p.pop("source_data_verification"))

    _, report = prepare_locked_g5_study(study, _csv(tmp_path / "nguon.csv", _NGUON), exports_root=tmp_path / "exports",
                                        repo_root=tmp_path, truoc_khi_khoa=bo_sdv, ky_vong=G5Q.STATUS_DRAFT_REVIEW)
    assert _tieu_chi(report, "G5-AUTO-04b")["status"] == "REVIEW"
    assert report["human_approval_valid"] is False


def test_g5_07_khoa_thieu_xac_nhan_ra_audit_trail_bi_tu_choi(tmp_path, monkeypatch):
    configure_test_signing_key(tmp_path, monkeypatch)
    study = "G5-07-AUDIT"
    ctx = prepare_clean_g5_study(study, _csv(tmp_path / "nguon.csv", _NGUON),
                                 exports_root=tmp_path / "exports", repo_root=tmp_path)
    manifest = lock_g5_fixture(study, ctx, exports_root=tmp_path / "exports", repo_root=tmp_path,
                               confirm_audit_trail_reviewed=False)
    assert manifest["status"] == LAD.BLOCKED_STATUS
    assert "missing_confirmation:audit_trail_reviewed" in manifest["blockers"]


def test_g5_07_ban_khoa_khong_ghi_xac_nhan_ra_audit_trail_thi_khong_ready(de_tai_cho_ky):
    study, out_dir, root = de_tai_cho_ky
    p = out_dir / "DATA_LOCK_manifest.json"
    manifest = json.loads(p.read_text(encoding="utf-8"))
    manifest["confirmations"]["audit_trail_reviewed"] = False
    p.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    assert _cham(study, out_dir, root)["status"] != G5Q.STATUS_READY


def test_g5_07_khuon_moi_la_2026_2_va_ho_so_cu_duoc_nang_cap_giu_nguyen_gia_tri(tmp_path):
    (tmp_path / "moi").mkdir()
    moi = G5A.write_operational_readiness_template(tmp_path / "moi")
    payload = json.loads(moi.read_text(encoding="utf-8"))
    assert payload["schema_version"] == G5Q.OPERATIONAL_SCHEMA_VERSION
    assert {"audit_trail_review", "source_data_verification"} <= set(payload)
    assert G5Q.evaluate_operational_readiness(moi)["valid"] is False, "khuôn chưa hoàn tất phải fail-closed"

    cu_dir = tmp_path / "cu"
    cu = _ho_so(tmp_path)
    payload_cu = json.loads(cu.read_text(encoding="utf-8"))
    for k in ("audit_trail_review", "source_data_verification"):
        payload_cu.pop(k)
    payload_cu["schema_version"] = "G5-OPS-2026.1"
    cu_dir.mkdir()
    (cu_dir / G5Q.OPERATIONAL_READINESS_JSON).write_text(json.dumps(payload_cu, ensure_ascii=False),
                                                       encoding="utf-8", newline="\n")
    nang = json.loads(G5A.write_operational_readiness_template(cu_dir).read_text(encoding="utf-8"))
    assert nang["schema_version"] == G5Q.OPERATIONAL_SCHEMA_VERSION
    assert nang["access_control_review"] == payload_cu["access_control_review"], "giá trị người đã điền giữ nguyên"
    assert nang["audit_trail_review"]["completed"] is False, "mục mới ở dạng khuôn chưa hoàn tất"


# ── G5-08 — bản gỡ băng (định tính) ───────────────────────────────────────────────────────────────────────────────────

_NGUON_DT = "record_id,transcript_id,age,sex\nS001,T01,45,F\nS002,T02,52,M\n"


def _ghi_ban_go_bang(out_dir: Path, noi_dung: dict, *, chi_doc: bool = True, khai=None) -> None:
    thu_muc = out_dir / "06_ban_go_bang"
    thu_muc.mkdir(parents=True, exist_ok=True)
    muc = []
    for tid, text in noi_dung.items():
        tep = thu_muc / f"{tid}.txt"
        _ghi_de_chi_doc(tep, text)
        if chi_doc:
            os.chmod(tep, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
        muc.append({"transcript_id": tid, "file": f"06_ban_go_bang/{tid}.txt",
                    "sha256": hashlib.sha256(tep.read_bytes()).hexdigest(), "deidentified": True,
                    "reviewer_ref": "QR-01"})
    if khai is not None:
        muc = khai(muc)
    (out_dir / G5Q.TRANSCRIPT_MANIFEST_JSON).write_text(
        json.dumps({"schema_version": "G5-TRANSCRIPT-2026.1", "transcripts": muc}, ensure_ascii=False),
        encoding="utf-8", newline="\n")


_SACH = {"T01": "Người tham gia T01 kể về trải nghiệm chờ khám và cách nhân viên giải thích.",
         "T02": "Người tham gia T02 mong thời gian chờ ngắn hơn và hướng dẫn rõ hơn."}


def test_g5_08_danh_gia_ban_go_bang_cac_duong_chan(tmp_path):
    out_dir = tmp_path / "dt"
    out_dir.mkdir()
    du_lieu = _csv(tmp_path / "dl.csv", _NGUON_DT)
    assert G5Q.danh_gia_transcript(out_dir, du_lieu)["issues"] == [f"thieu_{G5Q.TRANSCRIPT_MANIFEST_JSON}"]
    _ghi_ban_go_bang(out_dir, {})
    assert "manifest_khong_co_ban_go_bang" in G5Q.danh_gia_transcript(out_dir, du_lieu)["issues"]
    _ghi_ban_go_bang(out_dir, _SACH)
    assert G5Q.danh_gia_transcript(out_dir, du_lieu)["issues"] == []
    # Thiếu một bản trong sổ, bản chưa chỉ đọc, chưa khử định danh, thiếu người rà, băm lệch, còn mẫu PII.
    _ghi_ban_go_bang(out_dir, {"T01": _SACH["T01"]})
    issues = G5Q.danh_gia_transcript(out_dir, du_lieu)["issues"]
    assert any(i.startswith("transcript_chua_co_trong_manifest") for i in issues), issues
    _ghi_ban_go_bang(out_dir, _SACH, chi_doc=False)
    assert "T01:chua_chi_doc" in G5Q.danh_gia_transcript(out_dir, du_lieu)["issues"]
    _ghi_ban_go_bang(out_dir, _SACH, khai=lambda m: [{**m[0], "deidentified": False, "reviewer_ref": ""}, m[1]])
    issues = G5Q.danh_gia_transcript(out_dir, du_lieu)["issues"]
    assert "T01:chua_khu_dinh_danh" in issues and "T01:thieu_reviewer_ref" in issues
    _ghi_ban_go_bang(out_dir, _SACH, khai=lambda m: [{**m[0], "sha256": "0" * 64}, m[1]])
    assert "T01:bam_lech" in G5Q.danh_gia_transcript(out_dir, du_lieu)["issues"]
    _ghi_ban_go_bang(out_dir, {**_SACH, "T02": "Gọi lại số 0912345678 để hẹn phỏng vấn lần hai."})
    assert "T02:pii_phone_vn" in G5Q.danh_gia_transcript(out_dir, du_lieu)["issues"]
    # Dữ liệu không có cột nối với bản gỡ băng ⇒ không đối chiếu được ≠ «mọi bản đã khai».
    _ghi_ban_go_bang(out_dir, _SACH)
    khong_cot = _csv(tmp_path / "kc.csv", "record_id,age\nS001,45\n")
    assert "dataset_thieu_cot_transcript_id" in G5Q.danh_gia_transcript(out_dir, khong_cot)["issues"]


def test_g5_08_khuon_so_ban_go_bang_khong_ghi_de(tmp_path):
    p = G5A.write_transcript_manifest_template(tmp_path)
    payload = json.loads(p.read_text(encoding="utf-8"))
    assert payload["transcripts"] == [] and "[CẦN" not in p.read_text(encoding="utf-8")
    p.write_text('{"transcripts": [{"transcript_id": "T01"}]}', encoding="utf-8", newline="\n")
    G5A.write_transcript_manifest_template(tmp_path)
    assert "T01" in p.read_text(encoding="utf-8")


def _dung_dinh_tinh(tmp_path: Path, monkeypatch, study: str) -> dict:
    configure_test_signing_key(tmp_path, monkeypatch)
    out_dir = tmp_path / "exports" / study
    out_dir.mkdir(parents=True)
    (out_dir / "G1_checkpoint.json").write_text('{"design_code": "qualitative"}', encoding="utf-8", newline="\n")
    return prepare_clean_g5_study(study, _csv(tmp_path / "nguon.csv", _NGUON_DT), exports_root=tmp_path / "exports",
                                  repo_root=tmp_path, extra_text_columns=frozenset({"transcript_id"}))


def test_g5_08_dinh_tinh_khoa_bi_chan_khi_chua_co_so_ban_go_bang(tmp_path, monkeypatch):
    study = "G5-08-THIEU"
    ctx = _dung_dinh_tinh(tmp_path, monkeypatch, study)
    manifest = lock_g5_fixture(study, ctx, exports_root=tmp_path / "exports", repo_root=tmp_path)
    assert manifest["status"] == LAD.BLOCKED_STATUS
    assert f"transcript_manifest: thieu_{G5Q.TRANSCRIPT_MANIFEST_JSON}" in manifest["blockers"]


def test_g5_08_dinh_tinh_dau_cuoi_sua_ban_go_bang_sau_khoa_thi_block_khoa_lai_moi_ready(tmp_path, monkeypatch):
    study = "G5-08-DAU-CUOI"
    exports_root = tmp_path / "exports"
    ctx = _dung_dinh_tinh(tmp_path, monkeypatch, study)
    out_dir = ctx["out_dir"]
    _ghi_ban_go_bang(out_dir, _SACH)
    assert lock_g5_fixture(study, ctx, exports_root=exports_root, repo_root=tmp_path)["status"] == LAD.LOCKED_STATUS
    r = _cham(study, out_dir, tmp_path)
    assert r["status"] == G5Q.STATUS_READY, _chua_dat(r)
    assert _tieu_chi(r, "G5-AUTO-10")["status"] == "PASS"
    khoa_dau = (out_dir / "DATA_LOCK_manifest.json").read_bytes()

    # Bản gỡ băng bị thay sau khoá, lại còn số điện thoại ⇒ BLOCK; khoá lại KHÔNG đạt ⇒ bản khoá cũ giữ nguyên.
    _ghi_ban_go_bang(out_dir, {**_SACH, "T02": "Gọi lại số 0912345678 để hẹn phỏng vấn lần hai."})
    r = _cham(study, out_dir, tmp_path)
    assert r["status"] == G5Q.STATUS_BLOCKED and _tieu_chi(r, "G5-AUTO-10")["status"] == "BLOCK"
    lai = lock_g5_fixture(study, ctx, exports_root=exports_root, repo_root=tmp_path)
    assert lai["status"] == LAD.BLOCKED_STATUS
    assert lai["blockers"][0].startswith("khoa_lai_khong_dat"), lai["blockers"]
    assert "transcript_manifest: T02:pii_phone_vn" in lai["blockers"]
    assert (out_dir / "DATA_LOCK_manifest.json").read_bytes() == khoa_dau

    # Khử định danh xong: nội dung hợp lệ nhưng sổ đã khác bản khoá ⇒ vẫn BLOCK cho tới khi khoá lại.
    _ghi_ban_go_bang(out_dir, {**_SACH, "T02": "Người tham gia T02 mong được hẹn lại phỏng vấn lần hai."})
    c = _tieu_chi(_cham(study, out_dir, tmp_path), "G5-AUTO-10")
    assert c["status"] == "BLOCK" and "manifest_ban_go_bang_doi_sau_khi_khoa" in c["evidence"], c
    # Khoá lại cùng dữ liệu đạt ⇒ READY, ghi lần khoá trước.
    lai = lock_g5_fixture(study, ctx, exports_root=exports_root, repo_root=tmp_path)
    assert lai["status"] == LAD.LOCKED_STATUS, lai.get("blockers")
    assert lai["lan_khoa_truoc"]["transcript_manifest_sha256"] != lai["transcript_manifest_sha256"]
    assert _cham(study, out_dir, tmp_path)["status"] == G5Q.STATUS_READY


# ── approve_gate: trạng thái «đã khoá, còn REVIEW» liệt kê mục cần người rà ─────────────────────────────────────────

_STUDY_AG = "PYTEST-G5-HOAN-THIEN-20261004"


@pytest.fixture()
def thu_muc_ag():
    d = REPO_ROOT / "exports" / _STUDY_AG
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    try:
        yield d
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_g5_approve_gate_trang_thai_review_liet_ke_muc_can_nguoi_ra(monkeypatch, thu_muc_ag, capsys):
    cp = thu_muc_ag / "G5_checkpoint.json"
    cp.write_text('{"gate": "G5"}', encoding="utf-8", newline="\n")
    bao_cao = {"status": G5Q.STATUS_DRAFT_REVIEW, "automatic_criteria": [
        {"id": "G5-AUTO-04b", "label": "SDV", "status": "REVIEW", "evidence": "sdv_chua_khai"},
        {"id": "G5-HUMAN-01", "label": "ký", "status": "REVIEW", "evidence": "approval_ledger_G5=False"}]}
    monkeypatch.setattr(G5Q, "evaluate_study", lambda *a, **k: bao_cao)
    monkeypatch.setattr(sys, "argv", ["approve_gate.py", "--study", _STUDY_AG, "--gate", "G5", "--artifact", str(cp),
                                      "--reviewer-role", "DATA_GOVERNANCE_QA_REVIEWER", "--reviewer-ref", "DM-01"])
    assert AG.main() != 0
    out = capsys.readouterr().out
    assert "REVIEW G5-AUTO-04b" in out and "G5-HUMAN-01" not in out.split("REVIEW G5-AUTO-04b")[1], out
    assert not (thu_muc_ag / "approval_ledger.json").exists()
