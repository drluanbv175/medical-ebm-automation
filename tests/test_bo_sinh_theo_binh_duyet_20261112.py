# -*- coding: utf-8 -*-
"""Sửa bộ sinh theo bình duyệt độc lập C1a 29/10/2026 (đánh giá hệ nghiên cứu 12/11 — nhóm B, B3).

(1) Mô tả A12 viết tay (9 PMID, 14/10) lệch biên nhận hiện hành (35 PMID, 15/10) mà không gì báo:
    `kiem_a12_khop_bien_nhan` đối chiếu lời khai ↔ biên nhận (chỉ đo, không đổi cổng); G10 cảnh báo khi lắp.
(2) `G10_RELEASE_READINESS.json → status` là trạng thái MẪU lúc tạo tệp (không bao giờ cập nhật) — người đọc hiểu nhầm
    là trạng thái gói: mẫu nay ghi rõ ý nghĩa + thời điểm tạo.
(3) A2 chỉ nhận khối COSMIN khi TÊN đề tài có từ khoá: đề tài có pha phát triển bộ câu hỏi (`pha_cong_cu/`) hoặc PI khai
    `gate_params.G1.mo_dun_chuyen_biet` nay cũng nhận. Không PII.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
for _p in (str(REPO_ROOT / "tools"), str(REPO_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import g10_quality_gate as G10Q  # noqa: E402
import kiem_a12_khop_bien_nhan as KA12  # noqa: E402
import run_g1_auto as G1  # noqa: E402
import run_g10_assemble as G10A  # noqa: E402

S = "ZZA12-TEST"


def _de_tai_a12(tmp_path: Path, so_khai: int, moc_khai: str, n_bien_nhan: int = 35,
                moc_bn: str = "2026-10-15T14:00:46.390410+00:00", all_clean: bool = True) -> Path:
    d = tmp_path / S
    d.mkdir()
    (d / f"A12_CITATION_VERIFICATION_{S}.md").write_text(
        f"# A12 — Kiểm chứng trích dẫn — {S}\n\n## 1. Bằng chứng máy-kiểm\n\n"
        "| Bước | Công cụ | Kết quả |\n|---|---|---|\n"
        f"| Rút bài + metadata {so_khai} PMID | `tools/check_citations.py` | mã 0; all_clean=true ({moc_khai}Z) |\n\n"
        "## 2. Đối chiếu nội dung\n\n| PMID | Bài |\n|---|---|\n| 12345678 | mẫu (5 PMID nhắc ở đây không tính) |\n",
        encoding="utf-8", newline="\n")
    pm = [str(10000000 + i) for i in range(n_bien_nhan)]
    (d / "A12_RETRACTION_RECEIPT.json").write_text(json.dumps(
        {"study": S, "checked_at_utc": moc_bn, "pmids_checked": pm, "all_clean": all_clean}),
        encoding="utf-8", newline="\n")
    (d / "A12_METADATA_RECEIPT.json").write_text(json.dumps(
        {"study": S, "checked_at_utc": moc_bn, "pmids_checked": pm, "all_resolved": True}),
        encoding="utf-8", newline="\n")
    return d


def test_a12_lech_so_pmid_va_thoi_diem_bi_bat(tmp_path):
    d = _de_tai_a12(tmp_path, 9, "2026-10-14T13:42:42")
    kq = KA12.doi_chieu(S, d)
    assert kq["trang_thai"] == "LECH"
    assert any("khai 9 PMID" in x and "kiểm 35" in x for x in kq["chi_tiet"])
    assert any("2026-10-14T13:42" in x for x in kq["chi_tiet"])
    canh_bao = G10A.canh_bao_mo_ta_a12(S, d)
    assert canh_bao and "LỆCH" in canh_bao[0] and "--goi-y" in canh_bao[1]


def test_a12_khop_thi_im_lang_va_goi_y_dung_tu_bien_nhan(tmp_path):
    d = _de_tai_a12(tmp_path, 35, "2026-10-15T14:00:46")
    assert KA12.doi_chieu(S, d)["trang_thai"] == "KHOP"
    assert G10A.canh_bao_mo_ta_a12(S, d) == []
    dong = KA12.goi_y(S, d)
    assert "35 PMID" in dong and "all_clean=true (2026-10-15T14:00Z)" in dong and "all_resolved=true" in dong


def test_a12_all_clean_lech_bi_bat(tmp_path):
    d = _de_tai_a12(tmp_path, 35, "2026-10-15T14:00:46", all_clean=False)
    kq = KA12.doi_chieu(S, d)
    assert kq["trang_thai"] == "LECH" and any("all_clean" in x for x in kq["chi_tiet"])


def test_a12_thieu_tep_la_khong_do_duoc_khong_phai_khop(tmp_path):
    d = tmp_path / S
    d.mkdir()
    assert KA12.doi_chieu(S, d)["trang_thai"] == "KHONG_DO_DUOC"
    assert G10A.canh_bao_mo_ta_a12(S, d) == []


def test_readiness_mau_ghi_ro_status_la_trang_thai_mau(tmp_path):
    mau = G10Q.build_readiness_template(S)
    assert mau["status"] == G10Q.STATUS_DRAFT
    assert "KHÔNG cập nhật" in mau["status_y_nghia"] and "Trạng thái sống" in mau["status_y_nghia"]
    assert mau["tao_luc"][:4].isdigit() and "T" in mau["tao_luc"]
    # ensure_readiness không ghi đè phiếu đã có (xác nhận đời thực của PI)
    p = tmp_path / G10Q.READINESS_JSON
    p.write_text(json.dumps({"study": S, "status": "PI_DA_DIEN"}), encoding="utf-8", newline="\n")
    G10Q.ensure_readiness(S, tmp_path)
    assert json.loads(p.read_text(encoding="utf-8"))["status"] == "PI_DA_DIEN"


def test_mo_dun_cosmin_tu_pha_cong_cu_hoac_pi_khai(tmp_path):
    ten = "Sự hài lòng của bệnh nhân tại khoa khám bệnh"
    assert G1.detect_specialist_modules(ten) == [], "tên đề tài không có từ khoá ⇒ bản cũ bỏ sót COSMIN"
    assert G1.mo_dun_chuyen_biet(ten, {}, tmp_path) == []
    (tmp_path / "pha_cong_cu").mkdir()
    assert G1.mo_dun_chuyen_biet(ten, {}, tmp_path) == ["prom_tool"]
    meta = {"gate_params": {"G1": {"mo_dun_chuyen_biet": ["economic", "khong_ton_tai"]}}}
    assert G1.mo_dun_chuyen_biet(ten, meta, tmp_path) == ["economic", "prom_tool"]
    assert G1.mo_dun_chuyen_biet("kiểm định thang đo trầm cảm", meta, None) == ["prom_tool", "economic"]


def test_a2_co_khoi_cosmin_khi_de_tai_co_pha_cong_cu(tmp_path):
    design = G1.infer_study_design("descriptive", {}, "Sự hài lòng của bệnh nhân")
    khong = G1.generate_g1_artifact("Sự hài lòng của bệnh nhân", "S", "descriptive", design, [], {}, "2026-11-12 10:00",
                                    meta={}, out_dir=tmp_path)
    assert "COSMIN" not in khong
    (tmp_path / "pha_cong_cu").mkdir()
    co = G1.generate_g1_artifact("Sự hài lòng của bệnh nhân", "S", "descriptive", design, [], {}, "2026-11-12 10:00",
                                 meta={}, out_dir=tmp_path)
    assert "Kiểm định công cụ đo lường (COSMIN)" in co and "COSMIN Reporting Guideline" in co
