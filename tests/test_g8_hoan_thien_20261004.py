# -*- coding: utf-8 -*-
"""Soát từng cổng G0–G10 (04–05/10/2026) — cổng G8 (bình duyệt độc lập trước nộp): khoá hành vi các bản vá G8-01…G8-17.

G8-01 Kết luận phản biện: khuyến nghị SỬA LỚN/TỪ CHỐI, kết luận «cần sửa thêm» hay còn lỗi nghiêm trọng ⇒ G8-HUMAN-06
      REVIEW và approve_gate từ chối ký (tiêu chí người kiểm được trước khi ký).
G8-02 Khối KHAI BÁO CỦA NGƯỜI PHẢN BIỆN trong bản nhận xét: tích «Có» xung đột lợi ích/đồng tác giả ⇒ CHẶN; câu
      chưa tích, AI «Có» thiếu chi tiết, chưa xác nhận bảo mật, thiếu khối ⇒ REVIEW.
G8-03 A9 không nhúng băm bản thảo mà có bản thảo ⇒ G8-AUTO-12 CHẶN; run_g10_assemble chặn như lệch băm.
G8-04 A9 nhúng băm BẢN NHẬN XÉT (CHUNG-E) — G8-AUTO-12b: vắng/lệch ⇒ REVIEW trước ký, CHẶN sau ký; G10 so lại.
G8-06 G8-AUTO-13 tiền đề G7 chấm sống PASS_G7_CONFIRMED; run_g8_auto đọc G2/G4/G5/G7 từ nguồn thẩm quyền (pipeline,
      «tiêu chí qua cổng», thang tự kiểm A9) — không còn «PENDING — cần IRB thật, SAP ký» khi đã ký thật.
G8-07 Đăng ký: ngày ISO, mã khớp trọn mẫu registry, attestation G2 đã ký là nguồn thẩm quyền (lệch ⇒ REVIEW).
G8-08 ai_use_declared phải là bool.  G8-09 Kết cục chính SAP §2 ↔ câu «kết cục chính» của bản thảo (đổi sang kết cục phụ
      ⇒ CHẶN).  G8-10 Thiết kế sống (resolve_design_code); không xác định ⇒ REVIEW; checkpoint ghi design_code.
G8-11 «contrast agent» không bị chặn; «agent `kiem-chung-trich-dan`» vẫn chặn.  G8-12 Mục nhận theo dòng tiêu đề; khuyến
      nghị phải có lý do; kết luận phải chọn; lỗi nghiêm trọng kèm vị trí.  G8-14 reviewer_ref chuẩn hoá trước khi so.
Lộ khi chạy chuỗi thật (05/10/2026): thang tự kiểm checklist của G8 chấm MỌI mục kết quả/bàn luận/khai báo là «☐» vô
điều kiện ⇒ đề tài thật không bao giờ vượt 60% (G8-AUTO-10) ⇒ G8 không bao giờ PASS — nay xếp theo phần bản thảo.
Chuỗi thật CHUNG-H: G0→G7 PASS → run_g8_auto → bản nhận xét thật → sinh lại A9 → ký (khoá giả, khoá riêng nhóm phản
biện) ⇒ PASS_G8_REVIEW_RECORDED cho 8 thiết kế; sửa bản thảo/bản nhận xét sau ký ⇒ CHẶN.
Mọi luồng có ký chạy trong pytest với khoá giả tạm. Không PII.
"""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
for _p in (str(REPO_ROOT / "tools"), str(REPO_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import approve_gate as AG  # noqa: E402
import cong_song as CS  # noqa: E402
import g8_quality_gate as G8Q  # noqa: E402
import gate_contract as GC  # noqa: E402
import run_g8_auto as G8A  # noqa: E402

from tests.g5_test_helpers import DANG_KY_THU_RCT, append_signed_approval  # noqa: E402
from tests.test_g7_hoan_thien_20261004 import (  # noqa: E402
    THIET_KE,
    _cham,
    _chot_g7,
    _de_tai_g7_that,
    _hoan_thien,
)
from tests.test_g8_quality_gate import CLEAN_MANUSCRIPT, REVIEW_REPORT, SAP_TEXT, _a9, _evaluate, _meta  # noqa: E402


def _ck(bao: dict, ma: str) -> dict:
    return next(r for r in bao["automatic_criteria"] + bao["approval_criteria"] if r["id"] == ma)


def _ghi(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


# ── Chuỗi THẬT G0→G8 ────────────────────────────────────────────────────────────────────────────────────────────────

def _chay_g8(goc: Path, study: str, monkeypatch) -> int:
    monkeypatch.setattr(G8A, "BASE", goc)
    monkeypatch.setattr(sys, "argv", ["run_g8_auto.py", "--study", study])
    CS.xoa_dem()
    ma = 0
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            G8A.main()
    except SystemExit as exc:
        ma = int(exc.code or 0)
    CS.xoa_dem()
    return ma


_DATA_SHARING = (
    "Chúng tôi sẽ chia sẻ dữ liệu cá nhân đã khử định danh; dữ liệu nào: bộ biến kết cục chính; kèm đề cương và SAP; "
    "thời gian: từ 6 tháng sau công bố; tiêu chí truy cập: nhà nghiên cứu có đề cương được duyệt, qua cơ chế kho dữ "
    "liệu của đơn vị.")


def _khai_g8(out: Path, ket_cuc: str) -> None:
    meta_p = out / "study_meta.json"
    meta = json.loads(meta_p.read_text(encoding="utf-8"))
    meta["gate_params"]["G8"] = {
        "primary_outcome": ket_cuc, "ai_use_declared": True, "ai_tools": "Claude (Anthropic)",
        "ai_purpose": "hỗ trợ soạn khung bản thảo", "ai_declared_in_cover_letter": True,
        # 07/10/2026: CÙNG đăng ký mà G2 (RCT) của đồ gá đã ký — G8-AUTO-07 đối chiếu với attestation G2.
        "registration_id": DANG_KY_THU_RCT["registration_id"],
        "registration_date": DANG_KY_THU_RCT["registration_date"],
        "first_enrolment_date": DANG_KY_THU_RCT["first_enrolment_date"],
        "data_sharing_statement": _DATA_SHARING,
        "cover_letter_no_duplicate_submission": True, "cover_letter_coi_declared": True,
        "cover_letter_all_authors_approved": True, "cover_letter_corresponding_contact": True,
        "cover_letter_preprint_status": True, "reviewer_coi_declared": True, "reviewer_independence_declared": True,
        "reviewer_ai_use_declared": True, "reviewer_confidentiality_declared": True}
    _ghi(meta_p, json.dumps(meta, ensure_ascii=False, indent=2))
    CS.xoa_dem()


def _de_tai_g8_that(tmp_path: Path, monkeypatch, thiet_ke: str) -> tuple[str, Path, Path]:
    """G0→G7 PASS (chuỗi thật) → tác giả nêu kết cục chính SAP §2 + khai AI trong bản thảo (xác nhận G7 lại) →
    run_g8_auto → khai gate_params.G8 → người phản biện viết bản nhận xét → run_g8_auto lần 2 (A9 nhúng 2 băm)."""
    study, out, goc, _ma = _de_tai_g7_that(tmp_path, monkeypatch, thiet_ke)
    text = _hoan_thien(study, out, goc, monkeypatch, thiet_ke)
    chinh, _phu = G8Q.ket_cuc_sap((out / f"G4_A5_SAP_FINAL_{study}.md").read_text(encoding="utf-8"))
    text = text.replace("Kết cục chính: nội dung tác giả đã soạn", f"Kết cục chính: {chinh[0]}", 1)
    khai_ai = ("Khai báo AI: nhóm tác giả dùng công cụ trí tuệ nhân tạo (Claude, Anthropic) hỗ trợ soạn khung; tác "
               "giả chịu trách nhiệm toàn bộ nội dung.")
    text = text.replace("## KHAI BÁO", f"## KHAI BÁO\n\n{khai_ai}\n", 1)
    _ghi(out / f"G7_A8_MANUSCRIPT_{study}.md", text)
    _chot_g7(out, text)
    assert _cham(study, out, goc)["status"] == "PASS_G7_CONFIRMED"
    assert _chay_g8(goc, study, monkeypatch) == 0
    _khai_g8(out, chinh[0])
    _ghi(out / G8Q.peer_review_report_name(study), REVIEW_REPORT)
    assert _chay_g8(goc, study, monkeypatch) == 0
    return study, out, goc


def _cham8(study: str, out: Path, goc: Path) -> dict:
    CS.xoa_dem()
    return G8Q.evaluate_study(study, out, repo_root=goc, write=False)


def _ky_g8(study: str, out: Path, goc: Path) -> None:
    """Người phản biện tự ký bằng khoá RIÊNG nhóm INDEPENDENT_PEER_REVIEWER (khoá giả tạm của pytest)."""
    khoa = Path(os.environ["EBM_GATE_KEY_PATH"])
    _ghi(khoa.with_name(khoa.name + "_INDEPENDENT_PEER_REVIEWER"), "khoa-gia-pytest-g8-reviewer")
    append_signed_approval(study, out / G8Q.presubmission_artifact_name(study), "G8", "INDEPENDENT_PEER_REVIEWER",
                           repo_root=goc)


@pytest.mark.parametrize("thiet_ke", THIET_KE)
def test_chung_h_dau_cuoi_g8_8_thiet_ke_toi_pass_va_rang_buoc_sau_ky(tmp_path, monkeypatch, thiet_ke):
    study, out, goc = _de_tai_g8_that(tmp_path, monkeypatch, thiet_ke)
    a9 = (out / G8Q.presubmission_artifact_name(study)).read_text(encoding="utf-8")
    bam = CS.trich_bam_a9(a9)
    assert bam["ban_thao"] and bam["bao_cao_phan_bien"], "A9 nhúng băm bản thảo VÀ bản nhận xét (CHUNG-E)"
    cp = json.loads((out / "G8_checkpoint.json").read_text(encoding="utf-8"))
    assert cp["design_code"] == thiet_ke, "G8-10: checkpoint ghi thiết kế sống"
    assert cp["gate_status"].startswith("PASS"), ("G8-06: bộ sinh đọc G2/G4/G7 từ nguồn thẩm quyền", cp["gate_status"])
    assert cp["reporting_score_pct"] >= 60, "thang tự kiểm checklist không còn chặn trên dưới 60%"
    assert all(v["status"].startswith("PASS:") for v in cp["pipeline_completeness"].values()), \
        ("G8-06: nhãn pipeline theo chấm sống", cp["pipeline_completeness"])

    bao = _cham8(study, out, goc)
    assert bao["status"] == G8Q.STATUS_PENDING, [(r["id"], r["evidence"][:120]) for r in
                                                  bao["automatic_criteria"] + bao["approval_criteria"]
                                                  if r["status"] != "PASS"]
    for ma in ("G8-AUTO-12", "G8-AUTO-12b", "G8-AUTO-13", "G8-HUMAN-01", "G8-HUMAN-05", "G8-HUMAN-06"):
        assert _ck(bao, ma)["status"] == "PASS", (ma, _ck(bao, ma)["evidence"])
    assert not AG._tieu_chi_nguoi_chua_dat("G8", bao), "approve_gate cho ký: tiêu chí người trước ký đều đạt"

    _ky_g8(study, out, goc)
    bao = _cham8(study, out, goc)
    assert bao["status"] == G8Q.STATUS_REVIEWED, [(r["id"], r["evidence"][:120]) for r in
                                                   bao["automatic_criteria"] + bao["approval_criteria"]
                                                   if r["status"] != "PASS"]

    # G8-04: tráo bản nhận xét SAU khi ký ⇒ CHẶN.
    bc = out / G8Q.peer_review_report_name(study)
    _ghi(bc, REVIEW_REPORT.replace("SỬA NHỎ", "CHẤP NHẬN"))
    sau = _cham8(study, out, goc)
    assert _ck(sau, "G8-AUTO-12b")["status"] == "BLOCK" and sau["status"] == G8Q.STATUS_BLOCKED
    _ghi(bc, REVIEW_REPORT)
    assert _cham8(study, out, goc)["status"] == G8Q.STATUS_REVIEWED

    # Sửa bản thảo SAU khi ký ⇒ CHẶN (băm A9) và G7 hết hiệu lực xác nhận (G8-AUTO-13).
    md = out / f"G7_A8_MANUSCRIPT_{study}.md"
    _ghi(md, md.read_text(encoding="utf-8") + "\nCâu thêm sau khi G8 đã ký.\n")
    sau = _cham8(study, out, goc)
    assert _ck(sau, "G8-AUTO-12")["status"] == "BLOCK" and _ck(sau, "G8-AUTO-13")["status"] != "PASS"
    assert sau["status"] == G8Q.STATUS_BLOCKED


def test_g8_04_ban_nhan_xet_viet_sau_a9_phai_sinh_lai_a9_truoc_khi_ky(tmp_path, monkeypatch):
    study, out, goc = _de_tai_g8_that(tmp_path, monkeypatch, "cohort")
    bc = out / G8Q.peer_review_report_name(study)
    _ghi(bc, REVIEW_REPORT + "\n- Góp ý thêm ở vòng sau.\n")
    bao = _cham8(study, out, goc)
    assert _ck(bao, "G8-AUTO-12b")["status"] == "REVIEW" and bao["status"] == G8Q.STATUS_DRAFT, \
        "bản nhận xét sửa sau A9 (chưa ký) ⇒ sinh lại A9 rồi mới ký — approve_gate từ chối ở DRAFT"
    assert _chay_g8(goc, study, monkeypatch) == 0
    assert _cham8(study, out, goc)["status"] == G8Q.STATUS_PENDING


def test_g8_01_phan_bien_khuyen_nghi_sua_lon_thi_khong_ky_duoc(tmp_path, monkeypatch):
    study, out, goc = _de_tai_g8_that(tmp_path, monkeypatch, "cohort")
    _ghi(out / G8Q.peer_review_report_name(study), REVIEW_REPORT.replace("SỬA NHỎ", "SỬA LỚN").replace(
        "Sẵn sàng nộp.", "Cần sửa thêm trước khi nộp."))
    assert _chay_g8(goc, study, monkeypatch) == 0
    bao = _cham8(study, out, goc)
    assert _ck(bao, "G8-HUMAN-06")["status"] == "REVIEW"
    chua = AG._tieu_chi_nguoi_chua_dat("G8", bao)
    assert any(c.startswith("G8-HUMAN-06") for c in chua), "approve_gate phải từ chối ký"


# ── G8-01: kết luận phản biện cho phép nộp ───────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("sua,ly_do", [
    (("SỬA NHỎ", "SỬA LỚN"), "sửa lớn"),
    (("SỬA NHỎ", "TỪ CHỐI"), "từ chối"),
    (("Sẵn sàng nộp.", "Cần sửa thêm trước khi nộp."), "cần sửa thêm"),
    (("Không có.", "| # | Vị trí | Vấn đề |\n|---|---|---|\n| 1 | Mục 3.2 | Thiếu khoảng tin cậy |"),
     "lỗi nghiêm trọng"),
    (("Không có.", "- Mục 3.2: thiếu khoảng tin cậy cho kết cục chính"), "lỗi nghiêm trọng"),
])
def test_g8_01_ket_luan_phan_bien_khong_cho_nop_thi_human_06_review(sua, ly_do):
    bao = _evaluate(review_report_text=REVIEW_REPORT.replace(*sua))
    row = _ck(bao, "G8-HUMAN-06")
    assert row["status"] == "REVIEW" and ly_do in row["evidence"].casefold(), row
    assert bao["status"] != G8Q.STATUS_REVIEWED
    assert any(c.startswith("G8-HUMAN-06") for c in AG._tieu_chi_nguoi_chua_dat("G8", bao))


def test_g8_01_doi_chung_ban_nhan_xet_hop_le_thi_pass():
    bao = _evaluate()
    assert _ck(bao, "G8-HUMAN-06")["status"] == "PASS" and bao["status"] == G8Q.STATUS_REVIEWED
    assert G8Q.muc_khuyen_nghi(REVIEW_REPORT) == "sửa nhỏ" and G8Q.ket_luan_tong_the(REVIEW_REPORT) == "san_sang"
    assert G8Q.loi_nghiem_trong(REVIEW_REPORT) == (0, [])


def test_g8_01_mau_binh_duyet_da_tich_doc_dung():
    mau = ("KHUYẾN NGHỊ: ☐ Chấp nhận ☐ Sửa nhỏ ☑ Sửa lớn ☐ Từ chối\nLý do: thiếu phân tích độ nhạy theo SAP.\n"
           "════════ LỖI NGHIÊM TRỌNG (phải sửa trước khi nộp) ════════\n"
           "| # | Lăng kính | Vị trí (trang/mục/dòng) | Vấn đề | Đề xuất khắc phục |\n"
           "|---|-----------|------------------------|--------|------------------|\n"
           "| 1 | Thống kê | | Thiếu KTC | Bổ sung |\n| 2 | | | | |\n"
           "Kết luận tổng thể: cần sửa thêm trước khi nộp\n")
    assert G8Q.muc_khuyen_nghi(mau) == "sửa lớn"
    assert G8Q.ket_luan_tong_the(mau) == "can_sua"
    so, thieu = G8Q.loi_nghiem_trong(mau)
    assert so == 1 and thieu, "hàng rỗng của mẫu không tính; hàng có nội dung mà trống cột vị trí bị báo (G8-12)"


# ── G8-02: khối khai báo của người phản biện ─────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("cu,moi,ly_do", [
    ("☑ Không có ☐ Có (ghi rõ):", "☐ Không có ☑ Có (ghi rõ): nhận tài trợ của nhà sản xuất", "xung đột lợi ích"),
    ("tác giả không: ☑ Không ☐ Có", "tác giả không: ☐ Không ☑ Có", "đồng tác giả"),
])
def test_g8_02_tu_khai_co_xung_dot_hoac_dong_tac_gia_thi_chan(cu, moi, ly_do):
    r = REVIEW_REPORT.replace(cu, moi)
    assert r != REVIEW_REPORT
    bao = _evaluate(review_report_text=r)
    row = _ck(bao, "G8-HUMAN-05")
    assert row["status"] == "BLOCK" and bao["status"] == G8Q.STATUS_BLOCKED and ly_do in row["evidence"], row


def test_g8_02_cau_khai_doc_theo_cau_hoi_khong_doc_chi_tiet_dong_khac():
    """Chi tiết ở dòng xung đột lợi ích nhắc «đồng tác giả» — câu khai đồng tác giả phải đọc ĐÚNG dòng của nó
    (☑ Không)."""
    r = REVIEW_REPORT.replace("☑ Không có ☐ Có (ghi rõ):", "☐ Không có ☑ Có (ghi rõ): là đồng tác giả bài trước")
    assert r != REVIEW_REPORT
    chan, xem = G8Q.khai_bao_nguoi_phan_bien(r)
    assert any("xung đột lợi ích" in c for c in chan), chan
    assert not any("đồng tác giả/cấp trên" in c for c in chan), "dòng đồng tác giả tích «Không» — không được chặn oan"
    assert not xem, xem


@pytest.mark.parametrize("cu,moi,can", [
    ("phản biện không: ☑ Không ☐ Có", "phản biện không: ☐ Không ☐ Có", "chưa tích"),
    ("phản biện không: ☑ Không ☐ Có (tên công cụ + mục đích):",
     "phản biện không: ☐ Không ☑ Có (tên công cụ + mục đích):", "thiếu tên công cụ"),
    ("cho phép: ☑ Xác nhận", "cho phép: ☐ Xác nhận", "xác nhận"),
])
def test_g8_02_khai_bao_chua_du_thi_review(cu, moi, can):
    r = REVIEW_REPORT.replace(cu, moi)
    assert r != REVIEW_REPORT
    row = _ck(_evaluate(review_report_text=r), "G8-HUMAN-05")
    assert row["status"] == "REVIEW" and can in row["evidence"].casefold(), row


def test_g8_02_thieu_khoi_khai_bao_thi_review_du_co_cac_co_gate_params():
    r = REVIEW_REPORT[:REVIEW_REPORT.index("## KHAI BÁO")] + REVIEW_REPORT[REVIEW_REPORT.index("## KẾT LUẬN"):]
    row = _ck(_evaluate(review_report_text=r), "G8-HUMAN-05")
    assert row["status"] == "REVIEW" and "thiếu khối" in row["evidence"], \
        "4 cờ boolean trong study_meta KHÔNG thay được"


# ── G8-03 / G8-04: ràng buộc băm ─────────────────────────────────────────────────────────────────────────────────────

def test_g8_03_a9_khong_nhung_bam_ban_thao_thi_chan():
    khong_bam = "# A9\nNội dung tự kiểm toàn bộ pipeline G0-G7.\nCần bác sĩ kiểm chứng.\n"
    for ky in (False, True):
        row = _ck(_evaluate(presubmission_text=khong_bam, ledger_signed=ky), "G8-AUTO-12")
        assert row["status"] == "BLOCK" and "KHÔNG ràng buộc" in row["evidence"]


def test_g8_04_bam_ban_nhan_xet_vang_hoac_lech():
    chi_ban_thao = _a9(CLEAN_MANUSCRIPT, "")
    for ky, muc in ((False, "REVIEW"), (True, "BLOCK")):
        assert _ck(_evaluate(presubmission_text=chi_ban_thao, ledger_signed=ky), "G8-AUTO-12b")["status"] == muc
        lech = _a9(CLEAN_MANUSCRIPT, REVIEW_REPORT + "\nbản cũ\n")
        assert _ck(_evaluate(presubmission_text=lech, ledger_signed=ky), "G8-AUTO-12b")["status"] == muc
    da_nhung_mat_bao_cao = _a9(CLEAN_MANUSCRIPT, REVIEW_REPORT)
    assert _ck(_evaluate(presubmission_text=da_nhung_mat_bao_cao, review_report_text=""), "G8-AUTO-12b")[
        "status"] == "BLOCK"


# ── G8-06: tiền đề G7 sống ───────────────────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("tien_de,muc", [(None, "REVIEW"), ({"status": "BLOCK", "evidence": "G7=BLOCKED"}, "BLOCK"),
                                         ({"status": "REVIEW", "evidence": "G7=DRAFT"}, "REVIEW")])
def test_g8_06_g7_chua_pass_song_thi_khong_dat(tien_de, muc):
    bao = _evaluate(tien_de_g7=tien_de)
    assert _ck(bao, "G8-AUTO-13")["status"] == muc and bao["status"] != G8Q.STATUS_REVIEWED


# ── G8-07 / G8-10: đăng ký và thiết kế ───────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("de,can", [
    ({"registration_date": "2026-03-15", "first_enrolment_date": "2026-3-1"}, "iso"),
    ({"registration_id": "xem NCT0123456789"}, "mã đăng ký"),
    ({"registration_date": "2026-03-15", "first_enrolment_date": "2026-03-01"}, "hồi cứu"),
])
def test_g8_07_dang_ky_ngay_iso_va_ma_khop_tron(de, can):
    row = _ck(_evaluate(meta=_meta(**de)), "G8-AUTO-07")
    assert row["status"] == "REVIEW" and can in row["evidence"].casefold(), row


def test_g8_07_attestation_g2_la_nguon_tham_quyen():
    att = {"registration": {"registration_id": "NCT07654321", "registration_date": "2026-01-10"},
           "first_enrolment_date": "2026-02-01"}
    row = _ck(_evaluate(attestation_g2=att), "G8-AUTO-07")
    assert row["status"] == "REVIEW" and "LỆCH attestation" in row["evidence"], "G8 khai NCT01234567 ≠ G2 đã ký"
    att["registration"]["registration_id"] = "NCT01234567"
    assert _ck(_evaluate(attestation_g2=att), "G8-AUTO-07")["status"] == "PASS"
    assert _ck(_evaluate(attestation_g2=att, meta=_meta(registration_id=None, registration_date=None,
                                                        first_enrolment_date=None)), "G8-AUTO-07")["status"] == "PASS"


_KHONG_CHIA_SE = ("Dữ liệu cá nhân của người tham gia sẽ không được chia sẻ (no individual participant data will be "
                  "shared); không có tài liệu kèm theo.")


@pytest.mark.parametrize("ipd,cau,mong", [
    (False, _KHONG_CHIA_SE, "PASS"),
    (None, _KHONG_CHIA_SE, "REVIEW"),            # không khai tường minh ⇒ vẫn đòi đủ 5 trường
    ("false", _KHONG_CHIA_SE, "REVIEW"),         # chuỗi không phải bool
    (False, "Chúng tôi sẽ chia sẻ toàn bộ dữ liệu theo yêu cầu.", "REVIEW"),  # khai false mà văn bản nói CÓ
    (False, "Chưa quyết định có chia sẻ hay không (undecided).", "REVIEW"),  # có phủ định nhưng vẫn là undecided
])
def test_g8_13_tuyen_bo_khong_chia_se_ipd_hop_le_khi_khai_tuong_minh(ipd, cau, mong):
    """ICMJE 2017 (PMID 28582414) Bảng 1 Ví dụ 4: «No» + các mục còn lại «Not applicable» là tuyên bố đạt yêu cầu."""
    bao = _evaluate(meta=_meta(data_sharing_statement=cau, ipd_sharing=ipd))
    assert _ck(bao, "G8-AUTO-08")["status"] == mong, _ck(bao, "G8-AUTO-08")


def test_g8_10_thiet_ke_khong_xac_dinh_thi_review_khong_mac_dinh_quan_sat():
    bao = _evaluate(design_code="", meta=_meta(interventional=None))
    assert _ck(bao, "G8-AUTO-07")["status"] == "REVIEW" and _ck(bao, "G8-AUTO-08")["status"] == "REVIEW"


@pytest.mark.parametrize("g8_cu", [None, "cross_sectional"])
def test_g8_10_evaluate_study_dung_thiet_ke_song(tmp_path, g8_cu):
    """Thiết kế chỉ có ở G1 (G2 chưa ghi) — resolve_design_code là nguồn; G8_checkpoint cũ ghi thiết kế KHÁC không
    thắng."""
    d = tmp_path / "exports" / "S"
    d.mkdir(parents=True)
    _ghi(d / "G1_checkpoint.json", json.dumps({"design": {"internal_code": "rct"}}))
    if g8_cu:
        _ghi(d / "G8_checkpoint.json", json.dumps({"design_code": g8_cu}))
    bao = G8Q.evaluate_study("S", d, repo_root=tmp_path, write=False)
    assert "không xác định" not in _ck(bao, "G8-AUTO-07")["evidence"]
    assert "mã đăng ký" in _ck(bao, "G8-AUTO-07")["evidence"], "RCT (G1) ⇒ bị đòi đăng ký dù G8_checkpoint ghi khác"
    assert _ck(bao, "G8-AUTO-08")["evidence"] != "không phải báo cáo kết quả thử nghiệm — ICMJE không bắt buộc"


# ── G8-06: bộ sinh đọc nguồn thẩm quyền (pipeline, checklist, thang tự kiểm, results_final) ──────────────────────────

def test_g8_06_pipeline_a9_theo_cham_song():
    gates = {f"G{i}": {"_file_exists": True, "gate": f"G{i}", "guardrail": "PASS"} for i in range(8)}
    song = {f"G{i}": {"muc": "PASS", "status": f"PASS_G{i}_SONG"} for i in range(8)}
    song["G2"] = {"muc": "DRAFT", "status": "G2 chưa ký"}
    kq = G8A.analyze_pipeline(gates, "S", song=song)
    nhan = {r["gate"]: r["status"] for r in kq["rows"]}
    assert nhan["G2"] == "DRAFT: G2 chưa ký" and nhan["G0"] == "PASS: PASS_G0_SONG", nhan
    assert kq["n_pass"] == 7


_BAN_THAO_PHAN = (
    "## TÓM TẮT\n{tt}\n## I. GIỚI THIỆU\n{gt}\n## II. PHƯƠNG PHÁP\n{pp}\n## III. KẾT QUẢ\n{kq}\n"
    "## IV. BÀN LUẬN\n{bl}\n## V. KẾT LUẬN\nKết luận.\n## KHAI BÁO\n{kb}\n## TÀI LIỆU THAM KHẢO\n1. Tài liệu.\n")
_DOAN = "Nội dung tác giả đã soạn đầy đủ cho phần này của bản thảo, có số liệu và diễn giải rõ ràng. " * 2


@pytest.mark.parametrize("g7_song,ket_qua,mong", [
    (True, _DOAN, "☑"), (False, _DOAN, "☐"), (True, "[CẦN KẾT QUẢ THẬT]", "☐"),
], ids=["g7-song-ket-qua-xong", "g7-chua-pass", "ket-qua-con-o-trong"])
def test_g8_06_muc_ket_qua_cua_checklist_doi_phan_ket_qua_va_g7_song(g7_song, ket_qua, mong):
    van_ban = _BAN_THAO_PHAN.format(tt=_DOAN, gt=_DOAN, pp=_DOAN, kq=ket_qua, bl=_DOAN, kb=_DOAN)
    gates = {f"G{i}": {"_file_exists": True} for i in range(8)}
    gates["G7"]["_g7_song_pass"] = g7_song
    assert G8A._item_auto_check("Outcome data", gates, "cohort", van_ban) == mong
    # Mục phương pháp không phụ thuộc phần kết quả.
    assert G8A._item_auto_check("Setting", gates, "cohort", van_ban) == "☑"


def test_g8_06_thang_tu_kiem_trinh_bay_theo_g7_song():
    def _tk(g7_song: bool) -> dict:
        gates = {f"G{i}": {"_file_exists": True} for i in range(8)}
        gates["G7"]["_g7_song_pass"] = g7_song
        bao = G8A.build_presubmission_checklist(
            {"n_pass": 8, "n_total": 8},
            {"standard_name": "STROBE 2007", "score_pct": 80, "checked": 18, "total": 22},
            {"passed_count": 4}, gates, [])
        return {it["description"]: it["passed"] for it in bao["items"] if it["category"] == "TRINH BAY"}
    co, khong = _tk(True), _tk(False)
    for muc in ("Tieu de bai <= 120 ky tu, chua thiet ke nghien cuu", "Tom tat co cau truc <= 250 tu",
                "Danh sach tac gia + affiliations + ORCID day du"):
        assert co[muc] is True and khong[muc] is False, muc


def test_g8_06_results_final_chuoi_khong_tinh_la_ket_qua_that(tmp_path, monkeypatch):
    """results_final phải là bool True — chuỗi «true» gõ tay không tính (G7 cũng vậy); cô lập dòng của run_g8_auto bằng
    cách giữ mọi cổng trước PASS sống."""
    study, out, goc = _de_tai_g8_that(tmp_path, monkeypatch, "cohort")
    monkeypatch.setattr(CS, "trang_thai_song", lambda gate, *_a, **_k: {"muc": "PASS", "status": f"PASS_{gate}"})
    meta_p = out / "study_meta.json"
    meta = json.loads(meta_p.read_text(encoding="utf-8"))
    for gia_tri, dat in (("true", False), (True, True)):
        meta["results_final"] = gia_tri
        _ghi(meta_p, json.dumps(meta, ensure_ascii=False, indent=2))
        assert _chay_g8(goc, study, monkeypatch) == 0
        trang_thai = json.loads((out / "G8_checkpoint.json").read_text(encoding="utf-8"))["gate_status"]
        assert trang_thai.startswith("PASS") is dat, (gia_tri, trang_thai)
        if not dat:
            assert "Ket qua phan tich THAT" in trang_thai, trang_thai


def test_g8_auto_04_khong_co_ban_thao_thi_khong_do_duoc_khong_pass():
    row = _ck(_evaluate(manuscript_text=""), "G8-AUTO-04")
    assert row["status"] == "REVIEW" and "không đo được" in row["evidence"], row
    assert _ck(_evaluate(), "G8-AUTO-04")["status"] == "PASS"


# ── G8-08 / G8-09 / G8-11 / G8-12 / G8-14 ───────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("gia_tri", ["có", "true", "false", "không", 1])
def test_g8_08_ai_use_declared_phai_la_bool(gia_tri):
    row = _ck(_evaluate(meta=_meta(ai_use_declared=gia_tri)), "G8-AUTO-06")
    assert row["status"] == "REVIEW" and "true/false" in row["evidence"]


def test_g8_09_ban_thao_neu_ket_cuc_phu_lam_ket_cuc_chinh_thi_chan():
    sap = SAP_TEXT + "Kết cục phụ 1: tái nhập viện trong 30 ngày.\n"
    ban2 = CLEAN_MANUSCRIPT.replace(
        "Kết cục chính là tử vong do mọi nguyên nhân trong 12 tháng.",
        "Kết cục chính là tái nhập viện trong 30 ngày.\nTử vong do mọi nguyên nhân trong 12 tháng là kết cục phụ.")
    row = _ck(_evaluate(sap_text=sap, manuscript_text=ban2), "G8-AUTO-05")
    assert row["status"] == "BLOCK" and "kết cục PHỤ" in row["evidence"], "bản cũ PASS (chuỗi có mặt ở đâu đó)"
    row = _ck(_evaluate(sap_text=sap, meta=_meta(primary_outcome="tái nhập viện trong 30 ngày")), "G8-AUTO-05")
    assert row["status"] == "BLOCK" and "KHÔNG phải kết cục CHÍNH" in row["evidence"]


@pytest.mark.parametrize("cau,chan", [
    ("Iodinated contrast agent was given to all patients.", False),
    ("Patients received single-agent chemotherapy.", False),
    ("An alkylating agent was used in the control arm.", False),
    ("Dùng agent `kiem-chung-trich-dan` hoặc PubMed trực tiếp.", True),
    ("Kết quả do agent tra-cuu-chung-cu tổng hợp.", True),
    ("Các agent tự động đã rà bản thảo.", True),
])
def test_g8_11_agent_chi_chan_trong_ngu_canh_noi_bo(cau, chan):
    co = any("agent" in v for v in G8Q.scan_internal_traces(CLEAN_MANUSCRIPT + "\n" + cau + "\n"))
    assert co is chan, cau


_NAM_MUC = {"KHUYẾN NGHỊ", "LỖI NGHIÊM TRỌNG", "GÓP Ý NHỎ", "CÂU HỎI CHO TÁC GIẢ", "KẾT LUẬN TỔNG THỂ"}


@pytest.mark.parametrize("bao_cao,thieu", [
    ("KHUYẾN NGHỊ MAJOR MINOR QUESTIONS FOR THE AUTHORS OVERALL ACCEPT", _NAM_MUC),
    ("Recommendation: accept. Major: none. Minor: none. Questions for the authors: none. Overall: ok.",
     _NAM_MUC - {"KHUYẾN NGHỊ"}),
    ("The majority of overall survival analyses were acceptable; minor issues remain.", _NAM_MUC),
])
def test_g8_12_ban_nhan_xet_chi_co_tu_khoa_khong_duoc_tinh(bao_cao, thieu):
    """Mục nhận theo DÒNG TIÊU ĐỀ — từ khoá trong văn xuôi («majority», «overall survival», «Major: none» giữa
    dòng) không thay được tiêu đề mục."""
    van_de = G8Q.review_report_issues(bao_cao)
    assert {m for m in _NAM_MUC if f"thiếu mục '{m}' (tiêu đề mục)" in van_de} == thieu, van_de


def test_g8_12_ket_luan_phai_duoc_chon():
    r = REVIEW_REPORT.replace("Sẵn sàng nộp.", "Đang cân nhắc thêm.")
    assert r != REVIEW_REPORT and G8Q.ket_luan_tong_the(r) is None
    assert any("chưa chọn «sẵn sàng nộp» hay «cần sửa thêm»" in v for v in G8Q.review_report_issues(r))


def test_g8_12_loi_nghiem_trong_thieu_vi_tri_bi_bao():
    r = REVIEW_REPORT.replace("Không có.", "| # | Vị trí | Vấn đề |\n|---|---|---|\n| 1 |  | Thiếu khoảng tin cậy |")
    assert r != REVIEW_REPORT
    assert any("thiếu VỊ TRÍ" in v for v in G8Q.review_report_issues(r)), G8Q.review_report_issues(r)


def test_g8_12_khuyen_nghi_phai_co_ly_do():
    r = REVIEW_REPORT.replace("Lý do: phương pháp phù hợp thiết kế, kết cục chính khớp SAP; chỉ còn góp ý trình bày "
                              "nhỏ.\n", "")
    assert r != REVIEW_REPORT
    assert any("LÝ DO" in v for v in G8Q.review_report_issues(r))


def test_g8_14_reviewer_ref_chuan_hoa_truoc_khi_so():
    bao = _evaluate(cross_gate_refs={"G2": "PI-01", "G4": "PI-01", "G8": "pi 01", "G9": "PI-01"})
    assert _ck(bao, "G8-HUMAN-04")["status"] == "REVIEW"
    assert G8Q.norm_ref("PI-01") == G8Q.norm_ref("pi.01") == G8Q.norm_ref(" Pi_01 ")


# ── run_g10_assemble so băm bản nhận xét (G8-04 phía G10) — hàm thuần ───────────────────────────────────────────────

def test_g8_04_trich_bam_a9_cung_hop_dong_voi_g10():
    a9 = _a9(CLEAN_MANUSCRIPT, REVIEW_REPORT)
    bam = CS.trich_bam_a9(a9)
    assert bam["ban_thao"] == hashlib.sha256(CLEAN_MANUSCRIPT.encode("utf-8")).hexdigest()
    assert bam["bao_cao_phan_bien"] == hashlib.sha256(REVIEW_REPORT.encode("utf-8")).hexdigest()
    assert GC.EXIT_BLOCKED == 2
