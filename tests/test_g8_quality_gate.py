"""Kiểm thử hợp đồng chất lượng G8 (bình duyệt độc lập).

Trọng tâm: khoảng trống NỘI DUNG mà lớp mật mã của G8 không lấp được — artifact
bị ký là bản TỰ KIỂM do máy sinh, không phải bản nhận xét của người phản biện —
cộng với các nghĩa vụ ICMJE (bản 1/2026) ở thời điểm tiền nộp bài.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = REPO_ROOT / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import g8_quality_gate as G8Q  # noqa: E402
import run_g8_auto as G8  # noqa: E402

CLEAN_MANUSCRIPT = """# Bản thảo

## Tóm tắt
Nghiên cứu đánh giá can thiệp X.

## Phương pháp
Kết cục chính là tử vong do mọi nguyên nhân trong 12 tháng.
Nhóm nghiên cứu có sử dụng công cụ trí tuệ nhân tạo để hiệu đính ngôn ngữ.

## Kết quả
Kết quả sẽ được điền sau khi khóa dữ liệu.

## TÀI LIỆU THAM KHẢO
1. Cook JA và cs. BMJ 2018;363:k3750.
"""

SAP_TEXT = """# SAP
Kết cục chính: tử vong do mọi nguyên nhân trong 12 tháng.
"""

REVIEW_REPORT = """# NHẬN XÉT PHẢN BIỆN

## KHUYẾN NGHỊ
SỬA NHỎ

## LỖI NGHIÊM TRỌNG (phải sửa trước khi nộp)
| Vị trí | Vấn đề |
|---|---|
| Mục 3.2 | Thiếu khoảng tin cậy |

## GÓP Ý NHỎ
- Rút gọn phần mở đầu.

## CÂU HỎI CHO TÁC GIẢ
1. Vì sao chọn ngưỡng này?

## KẾT LUẬN TỔNG THỂ
Cần sửa thêm trước khi nộp.
"""


def _checkpoint(**overrides) -> dict:
    value = {
        "gate": "G8",
        "study": "TEST-G8",
        "design_code": "rct",
        "guardrail": {"passed": True},
        # SỬA 2026-07-31 (audit tautology vòng 2 — CRITICAL): khóa THẬT mà
        # run_g8_auto.py::write_g8_checkpoint() ghi là "reporting_score_pct",
        # KHÔNG PHẢI "reporting_completeness_pct" — fixture cũ dùng nhầm tên
        # khóa TRÙNG với bug trong g8_quality_gate.py (cả hai đều sai theo
        # cùng một cách), nên mọi test trong file này trước đây không hề chạy
        # qua đường đọc khóa thật, che giấu bug G8-AUTO-10 (permanent REVIEW).
        "reporting_score_pct": 82.0,
        # THÊM 2026-07-30 (audit toàn diện G0-G10 — sửa cùng lớp "tin cache
        # cũ" đã đóng ở G7-F1): G8-AUTO-00 nay chạy LẠI guardrail_g8() trên
        # presubmission_text THẬT thay vì đọc checkpoint["guardrail"]["passed"]
        # đóng băng — guardrail_g8() cần "pipeline" (rows + n_pass) để chấm R1;
        # dựng lại từ đúng 2 khóa mà write_g8_checkpoint() ghi thật.
        "pipeline_completeness": {
            f"G{i}": {"status": "PASS", "artifact": f"G{i}_ARTIFACT", "checkpoint_exists": True}
            for i in range(8)
        },
        "pipeline_pass_count": 8,
    }
    value.update(overrides)
    return value


def _meta(**g8_overrides) -> dict:
    g8 = {
        "primary_outcome": "tử vong do mọi nguyên nhân trong 12 tháng",
        "ai_use_declared": True,
        "ai_tools": "Claude Opus 5",
        "ai_purpose": "hiệu đính ngôn ngữ",
        "ai_declared_in_cover_letter": True,
        "interventional": True,
        "registration_id": "NCT01234567",
        "registration_date": "2026-01-10",
        "first_enrolment_date": "2026-02-01",
        "data_sharing_statement": (
            "Chúng tôi sẽ chia sẻ dữ liệu cá nhân đã khử định danh; dữ liệu nào: bộ "
            "biến kết cục chính; kèm đề cương và SAP; thời gian: từ 6 tháng sau công "
            "bố, không có ngày kết thúc; tiêu chí truy cập: nhà nghiên cứu có đề cương "
            "được duyệt, qua cơ chế kho dữ liệu của đơn vị."
        ),
        "cover_letter_no_duplicate_submission": True,
        "cover_letter_coi_declared": True,
        "cover_letter_all_authors_approved": True,
        "cover_letter_corresponding_contact": True,
        "cover_letter_preprint_status": True,
        "reviewer_coi_declared": True,
        "reviewer_independence_declared": True,
        "reviewer_ai_use_declared": True,
        "reviewer_confidentiality_declared": True,
    }
    g8.update(g8_overrides)
    return {"gate_params": {"G8": g8}}


def _evaluate(**overrides):
    kwargs = dict(
        study="TEST-G8",
        checkpoint=_checkpoint(),
        # SỬA 2026-07-30: fixture cũ ("# A9...\nNội dung tự kiểm.") không có
        # disclaimer/qua ngắn — vô hại khi G8-AUTO-00 chỉ đọc checkpoint cache,
        # nhưng nay guardrail_g8() chạy THẬT trên chuỗi này (R1 cần
        # pipeline["rows"] có checkpoint_exists — xem _checkpoint() ở trên;
        # R7 cần disclaimer) nên fixture phải là văn bản THỰC SỰ qua được
        # guardrail, không chỉ là placeholder rỗng.
        presubmission_text=(
            "# A9 — GÓI TIỀN NỘP BÀI\n"
            "Nội dung tự kiểm toàn bộ pipeline G0-G7.\n"
            "[CAN] Vài mục hành chính (CRediT/COI) còn chờ bác sĩ điền.\n"
            "Cần bác sĩ kiểm chứng.\n"
        ),
        manuscript_text=CLEAN_MANUSCRIPT,
        sap_text=SAP_TEXT,
        review_report_text=REVIEW_REPORT,
        g2_checkpoint={},
        meta=_meta(),
        citation_ok=True,
        citation_detail="A12 đạt",
        ledger_signed=True,
        ledger_reason="",
        signature_scope="role",
        role_key_available=True,
        cross_gate_refs={"G2": "IRB-01", "G4": "STAT-01", "G8": "REV-77", "G9": "PI-01"},
    )
    kwargs.update(overrides)
    return G8Q.evaluate_g8_quality(**kwargs)


def _row(report, criterion_id):
    for row in report["automatic_criteria"] + report["approval_criteria"]:
        if row["id"] == criterion_id:
            return row
    raise AssertionError(f"Không tìm thấy tiêu chí {criterion_id}")


# ════════════════════════════════════════════════════════════════════════════
# Hợp đồng module
# ════════════════════════════════════════════════════════════════════════════


def test_nam_trang_thai_roi_nghia():
    statuses = {
        G8Q.STATUS_BLOCKED,
        G8Q.STATUS_DRAFT,
        G8Q.STATUS_READY,
        G8Q.STATUS_PENDING,
        G8Q.STATUS_REVIEWED,
    }
    assert len(statuses) == 5


def test_trang_thai_dat_KHONG_duoc_chua_chu_doc_lap():
    """Hệ KHÔNG chứng minh được tính độc lập — nhãn không được nói quá."""
    assert "INDEPENDENT" not in G8Q.STATUS_REVIEWED.upper()
    assert "ĐỘC LẬP" not in G8Q.STATUS_REVIEWED.upper()


def test_gioi_han_phan_dinh_noi_ro_han_che_HMAC(tmp_path):
    report = _evaluate()
    scope = report["scope_statement"]
    assert "ĐỐI XỨNG" in scope
    assert "KHÔNG chứng minh được" in scope


def test_moi_chuan_nen_deu_co_dinh_danh():
    for item in G8Q.STANDARDS_BASIS:
        assert item.get("url") or item.get("doi") or item.get("pmid"), item


def test_khong_doi_ten_artifact_hop_dong_downstream():
    """Tên file là hợp đồng ba bên — đổi là phá cổng G10 và mọi chữ ký cũ."""
    assert G8Q.presubmission_artifact_name("ABC") == "G8_A9_PRESUBMISSION_ABC.md"
    assert G8Q.manuscript_artifact_name("ABC") == "G7_A8_MANUSCRIPT_ABC.md"


# ════════════════════════════════════════════════════════════════════════════
# Vệt công cụ nội bộ (doctrine xếp mức CHẶN)
# ════════════════════════════════════════════════════════════════════════════


def test_bat_nhan_can_con_sot_trong_than_bai():
    traces = G8Q.scan_internal_traces("Kết quả [CẦN BÁC SĨ ĐIỀN] rất khả quan.")
    assert traces and "CẦN" in traces[0]


def test_bat_ten_file_pipeline_trong_ban_thao():
    traces = G8Q.scan_internal_traces("Xem thêm G3_checkpoint.json để biết cỡ mẫu.")
    assert any("pipeline" in t for t in traces)


def test_bat_lua_chon_A_hay_B_con_bo_ngo():
    traces = G8Q.scan_internal_traces("Chọn (A) hay (B) tùy chủ nhiệm.")
    assert any("(A)" in t or "bỏ ngỏ" in t for t in traces)


def test_ban_thao_sach_khong_bi_bat_oan():
    assert G8Q.scan_internal_traces(CLEAN_MANUSCRIPT) == []


def test_phu_luc_noi_bo_khong_bi_tinh_la_sot(tmp_path):
    text = CLEAN_MANUSCRIPT + "\n## PHỤ LỤC\n[CẦN kiểm nội bộ]\n"
    assert G8Q.scan_internal_traces(text) == []


def test_vet_cong_cu_noi_bo_lam_CHAN_cong():
    report = _evaluate(manuscript_text="Kết quả [CẦN ĐIỀN] tốt.")
    assert _row(report, "G8-AUTO-04")["status"] == "BLOCK"
    assert report["status"] == G8Q.STATUS_BLOCKED


# ════════════════════════════════════════════════════════════════════════════
# Báo cáo kết quả chọn lọc (selective outcome reporting)
# ════════════════════════════════════════════════════════════════════════════


def test_ket_cuc_chinh_khop_ca_sap_va_ban_thao_thi_dat():
    assert _row(_evaluate(), "G8-AUTO-05")["status"] == "PASS"


def test_ket_cuc_chinh_bien_mat_khoi_ban_thao_bi_chan():
    report = _evaluate(manuscript_text="# Bản thảo\nKết cục chính là thời gian nằm viện.")
    row = _row(report, "G8-AUTO-05")
    assert row["status"] == "BLOCK"
    assert "chọn lọc" in row["evidence"]


def test_chua_khai_ket_cuc_chinh_thi_ra_soat():
    report = _evaluate(meta=_meta(primary_outcome=""))
    assert _row(report, "G8-AUTO-05")["status"] == "REVIEW"


# ════════════════════════════════════════════════════════════════════════════
# ICMJE Mục V — khai báo AI
# ════════════════════════════════════════════════════════════════════════════


def test_khong_khai_ai_la_thieu_sot():
    issues = G8Q.ai_disclosure_issues(CLEAN_MANUSCRIPT, {})
    assert issues and "misconduct" in issues[0]


def test_khai_co_dung_ai_nhung_thieu_ten_cong_cu():
    issues = G8Q.ai_disclosure_issues(
        CLEAN_MANUSCRIPT,
        {"ai_use_declared": True, "ai_purpose": "hiệu đính", "ai_declared_in_cover_letter": True},
    )
    assert any("TÊN CÔNG CỤ" in i for i in issues)


def test_thieu_khai_ai_trong_cover_letter():
    issues = G8Q.ai_disclosure_issues(
        CLEAN_MANUSCRIPT,
        {"ai_use_declared": True, "ai_tools": "X", "ai_purpose": "y"},
    )
    assert any("COVER LETTER" in i for i in issues)


def test_trich_dan_noi_dung_ai_trong_tltk_bi_bat():
    bad = CLEAN_MANUSCRIPT + "\n2. ChatGPT, OpenAI, truy cập 2026.\n"
    issues = G8Q.ai_disclosure_issues(bad, _meta()["gate_params"]["G8"])
    assert any("TRÍCH DẪN" in i for i in issues)


def test_khai_ai_day_du_thi_khong_con_van_de():
    assert G8Q.ai_disclosure_issues(CLEAN_MANUSCRIPT, _meta()["gate_params"]["G8"]) == []


# ── G8-F3: đối chiếu NGƯỢC — khai KHÔNG dùng AI nhưng bản thảo thật thừa
# nhận có dùng (trước đây nhánh declared=False không kiểm gì cả) ────────────


def test_khai_khong_dung_ai_nhung_ban_thao_that_thua_nhan_bi_bat():
    """G8-F3 (MEDIUM FABRICATION_RISK): ai_use_declared=False nhưng
    CLEAN_MANUSCRIPT thật sự có câu 'công cụ trí tuệ nhân tạo để hiệu đính
    ngôn ngữ' — đây là khai báo sai sự thật theo ICMJE Mục V.A, không phải
    thiếu sót hành chính đơn thuần."""
    issues = G8Q.ai_disclosure_issues(CLEAN_MANUSCRIPT, {"ai_use_declared": False})
    assert issues, "phải bắt được lệch — trước đây nhánh này trả rỗng vô điều kiện"
    assert any("SAI SỰ THẬT" in i for i in issues)


def test_khai_khong_dung_ai_va_ban_thao_khong_nhac_AI_thi_khong_bi_bat_oan():
    text = (
        "# Bản thảo\nKết cục chính là tử vong do mọi nguyên nhân trong 12 tháng.\n"
        "## TÀI LIỆU THAM KHẢO\n1. Cook JA và cs. BMJ 2018;363:k3750.\n"
    )
    assert G8Q.ai_disclosure_issues(text, {"ai_use_declared": False}) == []


def test_khai_khong_dung_ai_nhung_nhac_ten_cong_cu_cu_the_van_bi_bat():
    """Không chỉ khớp token 'trí tuệ nhân tạo' — tên công cụ cụ thể cũng đủ
    tín hiệu (tái dùng _AI_TOOL_NAME_RE đã có, không viết regex mới)."""
    text = "# Bản thảo\nChúng tôi đã dùng ChatGPT để soát lỗi chính tả bản thảo.\n"
    issues = G8Q.ai_disclosure_issues(text, {"ai_use_declared": False})
    assert any("SAI SỰ THẬT" in i for i in issues)


def test_chua_khai_dut_khoat_nhung_ban_thao_da_nhac_AI_them_canh_bao_cu_the():
    """declared=None: giữ nguyên cảnh báo 'chưa khai dứt khoát' (misconduct)
    NHƯNG thêm cảnh báo cụ thể khi bản thảo đã tự lộ việc dùng AI."""
    issues = G8Q.ai_disclosure_issues(CLEAN_MANUSCRIPT, {})
    assert "misconduct" in issues[0]
    assert any("CHƯA khai dứt khoát" in i for i in issues[1:])


def test_g8_auto_06_ra_soat_khi_khai_sai_su_that_qua_pipeline_that():
    """Mutation-test ở tầng tích hợp: G8-AUTO-06 phải REVIEW khi
    ai_use_declared=False nhưng manuscript_text (CLEAN_MANUSCRIPT) thật sự
    nhắc tới AI — trước khi sửa, tiêu chí này PASS sai (bug thật)."""
    report = _evaluate(meta=_meta(ai_use_declared=False))
    row = _row(report, "G8-AUTO-06")
    assert row["status"] == "REVIEW"
    assert "SAI SỰ THẬT" in row["evidence"]


# ════════════════════════════════════════════════════════════════════════════
# ICMJE — đăng ký nghiên cứu và chia sẻ dữ liệu
# ════════════════════════════════════════════════════════════════════════════


def test_thu_nghiem_thieu_ma_dang_ky_bi_ra_soat():
    status, problems = G8Q.registration_issues("rct", {"interventional": True}, {})
    assert status == "REVIEW"
    assert any("mã đăng ký" in p for p in problems)


def test_dang_ky_hoi_cuu_bi_bat():
    status, problems = G8Q.registration_issues(
        "rct",
        {
            "interventional": True,
            "registration_id": "NCT01234567",
            "registration_date": "2026-03-01",
            "first_enrolment_date": "2026-02-01",
        },
        {},
    )
    assert status == "REVIEW"
    assert any("HỒI CỨU" in p for p in problems)


def test_dung_ngay_irb_thay_ngay_dang_ky_bi_bat():
    status, problems = G8Q.registration_issues(
        "rct",
        {
            "interventional": True,
            "registration_id": "NCT01234567",
            "registration_date": "2026-01-10",
            "first_enrolment_date": "2026-02-01",
            "registration_date_is_irb_date": True,
        },
        {},
    )
    assert any("Hội đồng Đạo đức" in p for p in problems)


def test_thiet_ke_quan_sat_khong_bi_bat_oan_ve_dang_ky():
    """ICMJE chỉ KHUYẾN KHÍCH đăng ký với thiết kế quan sát — báo lỗi là sai chuẩn."""
    status, _ = G8Q.registration_issues("cohort", {}, {})
    assert status == "PASS"


def test_chia_se_du_lieu_undecided_bi_bat():
    status, problems = G8Q.data_sharing_issues(
        "rct", {"interventional": True, "data_sharing_statement": "Undecided at this time."}
    )
    assert status == "REVIEW"
    assert any("undecided" in p for p in problems)


def test_chia_se_du_lieu_khong_bat_buoc_cho_thiet_ke_quan_sat():
    status, _ = G8Q.data_sharing_issues("cohort", {})
    assert status == "PASS"


def test_chia_se_du_lieu_du_5_truong_thi_dat():
    status, problems = G8Q.data_sharing_issues("rct", _meta()["gate_params"]["G8"])
    assert status == "PASS", problems


# ════════════════════════════════════════════════════════════════════════════
# Bằng chứng bình duyệt người thật
# ════════════════════════════════════════════════════════════════════════════


def test_thieu_ban_nhan_xet_phan_bien_thi_ra_soat():
    report = _evaluate(review_report_text="")
    row = _row(report, "G8-HUMAN-01")
    assert row["status"] == "REVIEW"
    assert "chưa có bản nhận xét" in row["evidence"]


def test_ban_nhan_xet_thieu_muc_bi_bat():
    problems = G8Q.review_report_issues("# Nhận xét\n## KHUYẾN NGHỊ\nCHẤP NHẬN\n")
    assert any("LỖI NGHIÊM TRỌNG" in p for p in problems)


def test_ban_nhan_xet_du_muc_thi_khong_con_van_de():
    assert G8Q.review_report_issues(REVIEW_REPORT) == []


def test_ban_nhan_xet_thieu_khuyen_nghi_ro_muc():
    text = REVIEW_REPORT.replace("SỬA NHỎ", "xem chi tiết bên dưới")
    problems = G8Q.review_report_issues(text)
    assert any("KHUYẾN NGHỊ rõ mức" in p for p in problems)


# ════════════════════════════════════════════════════════════════════════════
# Tính độc lập và mức bảo đảm của chữ ký
# ════════════════════════════════════════════════════════════════════════════


def test_reviewer_ref_trung_cong_khac_bi_canh_bao():
    report = _evaluate(
        cross_gate_refs={"G2": "IRB-01", "G4": "PI-01", "G8": "PI-01", "G9": "PI-01"}
    )
    row = _row(report, "G8-HUMAN-04")
    assert row["status"] == "REVIEW"
    assert "TRÙNG" in row["evidence"]
    assert "G4" in row["evidence"] and "G9" in row["evidence"]


def test_reviewer_ref_rieng_biet_thi_dat():
    assert _row(_evaluate(), "G8-HUMAN-04")["status"] == "PASS"


def test_khoa_chung_bi_ha_muc_khang_dinh():
    report = _evaluate(signature_scope="shared")
    row = _row(report, "G8-HUMAN-03")
    assert row["status"] == "REVIEW"
    assert "khóa CHUNG" in row["evidence"]


def test_khoa_rieng_van_khong_khang_dinh_da_doc_lap():
    """scope='role' chỉ chứng minh một FILE tồn tại — không được nói quá."""
    row = _row(_evaluate(signature_scope="role"), "G8-HUMAN-03")
    assert row["status"] == "PASS"
    assert "không chứng minh được" in row["evidence"]


def test_thieu_khai_bao_cua_nguoi_phan_bien_bi_ra_soat():
    report = _evaluate(meta=_meta(reviewer_ai_use_declared=False))
    row = _row(report, "G8-HUMAN-05")
    assert row["status"] == "REVIEW"
    assert "AI" in row["evidence"]


# ════════════════════════════════════════════════════════════════════════════
# A12 và checklist chuẩn báo cáo
# ════════════════════════════════════════════════════════════════════════════


def test_a12_chua_dat_thi_CHAN_cong():
    """Hiện A12 chỉ là 2/30 điểm và không nằm trong điều kiện quyết định g8_status."""
    report = _evaluate(citation_ok=False, citation_detail="thiếu artifact A12")
    assert _row(report, "G8-AUTO-03")["status"] == "BLOCK"
    assert report["status"] == G8Q.STATUS_BLOCKED


def test_checklist_duoi_nguong_bi_ra_soat_kem_ghi_chu_lech_noi_bo():
    report = _evaluate(checkpoint=_checkpoint(reporting_score_pct=30.0))
    row = _row(report, "G8-AUTO-10")
    assert row["status"] == "REVIEW"
    assert "KHÔNG tính điều kiện này vào g8_status" in row["evidence"]


def test_g8_auto_10_key_mismatch_20260731():
    """Hồi quy CRITICAL (audit tautology vòng 2): G8-AUTO-10 trước đây đọc
    "reporting_completeness_pct"/"reporting_pct" — hai khóa mà
    run_g8_auto.py::write_g8_checkpoint() KHÔNG BAO GIỜ ghi (khóa thật là
    "reporting_score_pct") — khiến pct luôn None, G8-AUTO-10 luôn REVIEW, và
    MỌI đề tài thật kẹt vĩnh viễn không đạt PASS_G8_REVIEW_RECORDED."""
    # Đúng khóa thật, giá trị cao -> phải PASS (trước bản vá: luôn REVIEW).
    report = _evaluate(checkpoint=_checkpoint(reporting_score_pct=95.0))
    row = _row(report, "G8-AUTO-10")
    assert row["status"] == "PASS"
    assert "95" in row["evidence"]

    # Checkpoint CHỈ có khóa cũ (mô phỏng writer/thời điểm khác) -> vẫn đọc
    # được nhờ fallback, không phải None.
    stale = _checkpoint(reporting_score_pct=None)
    stale.pop("reporting_score_pct")
    stale["reporting_completeness_pct"] = 95.0
    report2 = _evaluate(checkpoint=stale)
    assert _row(report2, "G8-AUTO-10")["status"] == "PASS"

    # Checkpoint không có khóa nào cả -> None thật, REVIEW đúng (không phải
    # bug, không có dữ liệu để chấm).
    missing = _checkpoint()
    missing.pop("reporting_score_pct")
    report3 = _evaluate(checkpoint=missing)
    row3 = _row(report3, "G8-AUTO-10")
    assert row3["status"] == "REVIEW"
    assert "không đọc được" in row3["evidence"]


# ════════════════════════════════════════════════════════════════════════════
# G8-F5: thiết kế lệch giữa G1 và G2 (design_code có thể ảnh hưởng
# registration_issues()/data_sharing_issues()) — tiêu chí CẢNH BÁO mới,
# KHÔNG đổi design_code chính đang dùng cho các quyết định khác.
# ════════════════════════════════════════════════════════════════════════════


def test_khong_lech_thiet_ke_thi_g8_auto_11_dat():
    row = _row(_evaluate(), "G8-AUTO-11")
    assert row["status"] == "PASS"


def test_lech_thiet_ke_g1_g2_bi_canh_bao_khong_bi_chan():
    report = _evaluate(
        design_drift_warning=(
            "⚠️  THIẾT KẾ LỆCH GIỮA CÁC CỔNG: G1 suy luận 'cohort' nhưng G2 ghi 'rct'."
        )
    )
    row = _row(report, "G8-AUTO-11")
    assert row["status"] == "REVIEW"
    assert "LỆCH GIỮA CÁC CỔNG" in row["evidence"]
    # CẢNH BÁO, không phải CHẶN — hạ xuống DRAFT (auto_review) chứ không BLOCK.
    assert report["status"] == G8Q.STATUS_DRAFT


def test_evaluate_study_tich_hop_tu_tinh_lech_thiet_ke_tu_checkpoint_that(tmp_path):
    """Kiểm dây nối THẬT (không chỉ tham số truyền tay ở 2 test trên):
    evaluate_study() phải tự gọi gate_contract.resolve_design_code() để đọc
    G1_checkpoint.json/G2_checkpoint.json THẬT trên đĩa và truyền cảnh báo
    lệch vào evaluate_g8_quality() — đúng cơ chế G5/G7 đã dùng."""
    study = "G8-DESIGN-DRIFT"
    out_dir = tmp_path / "exports" / study
    out_dir.mkdir(parents=True)
    (out_dir / "G1_checkpoint.json").write_text(
        json.dumps({"design": {"internal_code": "cohort"}}), encoding="utf-8"
    )
    (out_dir / "G2_checkpoint.json").write_text(
        json.dumps({"design_code": "rct"}), encoding="utf-8"
    )
    report = G8Q.evaluate_study(study, out_dir, repo_root=tmp_path, write=False)
    row = _row(report, "G8-AUTO-11")
    assert row["status"] == "REVIEW"
    assert "LỆCH GIỮA CÁC CỔNG" in row["evidence"]


def test_evaluate_study_tich_hop_khong_lech_thi_g8_auto_11_dat(tmp_path):
    study = "G8-DESIGN-OK"
    out_dir = tmp_path / "exports" / study
    out_dir.mkdir(parents=True)
    (out_dir / "G1_checkpoint.json").write_text(
        json.dumps({"design": {"internal_code": "cohort"}}), encoding="utf-8"
    )
    (out_dir / "G2_checkpoint.json").write_text(
        json.dumps({"design_code": "cohort"}), encoding="utf-8"
    )
    report = G8Q.evaluate_study(study, out_dir, repo_root=tmp_path, write=False)
    row = _row(report, "G8-AUTO-11")
    assert row["status"] == "PASS"


# ════════════════════════════════════════════════════════════════════════════
# Bậc trạng thái và đầu ra
# ════════════════════════════════════════════════════════════════════════════


def test_du_moi_dieu_kien_thi_dat_pass_g8_review_recorded():
    report = _evaluate()
    failing = [
        row for row in report["automatic_criteria"] + report["approval_criteria"]
        if row["status"] != "PASS"
    ]
    assert not failing, failing
    assert report["status"] == G8Q.STATUS_REVIEWED


def test_goi_sach_nhung_chua_co_phan_bien_thi_o_trang_thai_san_sang():
    report = _evaluate(review_report_text="", ledger_signed=False, ledger_reason="chưa ai duyệt")
    assert report["status"] == G8Q.STATUS_READY
    assert report["package_ready_for_review"] is True


def test_da_co_nhan_xet_nhung_chua_ky_thi_cho_chu_ky():
    report = _evaluate(ledger_signed=False, ledger_reason="chưa ai duyệt")
    assert report["status"] == G8Q.STATUS_PENDING


# ── G8-F4: STATUS_PENDING không được để bác sĩ hiểu nhầm "chưa ký" khi chữ ký
# G8 THẬT SỰ đã tồn tại — evidence phải nói rõ ngữ cảnh (đã ký/chưa ký + còn
# thiếu gì cụ thể), không chỉ dựa vào tên trạng thái. ─────────────────────────


def test_status_pending_voi_ledger_da_ky_noi_ro_da_co_chu_ky_con_thieu_gi():
    """Ledger ĐÃ ký hợp lệ (ledger_signed=True) nhưng còn thiếu bằng chứng
    nội dung khác (ở đây: chưa có bản nhận xét phản biện thật) — trước khi
    sửa, bác sĩ chỉ thấy tên STATUS_PENDING và dễ hiểu lầm là 'chưa ký'."""
    report = _evaluate(review_report_text="", ledger_signed=True, signature_scope="shared")
    assert report["status"] == G8Q.STATUS_PENDING
    assert "Đã có chữ ký G8 hợp lệ" in report["status_detail"]
    assert "còn thiếu" in report["status_detail"]
    # Không được lặp lại nhầm lẫn "chưa ký" trong chính lời giải thích.
    assert "Chưa có chữ ký" not in report["status_detail"]


def test_status_pending_voi_ledger_chua_ky_noi_ro_chua_co_chu_ky():
    report = _evaluate(ledger_signed=False, ledger_reason="chưa ai duyệt")
    assert report["status"] == G8Q.STATUS_PENDING
    assert "Chưa có chữ ký G8 hợp lệ" in report["status_detail"]
    assert "chưa ai duyệt" in report["status_detail"]


def test_status_khac_pending_thi_status_detail_rong():
    report = _evaluate()  # đủ mọi điều kiện -> STATUS_REVIEWED
    assert report["status"] == G8Q.STATUS_REVIEWED
    assert report["status_detail"] == ""


def test_ghi_bao_cao_ra_ca_json_va_markdown(tmp_path):
    report = _evaluate()
    md_path = G8Q.write_quality_report("TEST-G8", tmp_path, report)
    assert md_path.exists()
    assert (tmp_path / "G8_QUALITY_REPORT.json").exists()
    text = md_path.read_text(encoding="utf-8")
    assert "Cần bác sĩ kiểm chứng" in text
    assert "G8-AUTO-05" in text


def test_cap_nhat_checkpoint_giu_nguyen_khoa_downstream(tmp_path):
    original = _checkpoint(pipeline_pass_count=7, reporting_standard="CONSORT 2025")
    (tmp_path / "G8_checkpoint.json").write_text(
        json.dumps(original, ensure_ascii=False), encoding="utf-8"
    )
    report = _evaluate()
    G8Q.refresh_checkpoint(
        study="TEST-G8", out_dir=tmp_path, report=report,
        quality_report_path=tmp_path / "G8_QUALITY_REPORT.md",
    )
    updated = json.loads((tmp_path / "G8_checkpoint.json").read_text(encoding="utf-8"))
    for key in ("pipeline_pass_count", "reporting_standard", "design_code"):
        assert updated[key] == original[key], key
    assert updated["quality_gate"]["status"] == report["status"]
    assert updated["quality_contract_version"] == G8Q.QUALITY_CONTRACT_VERSION


# ════════════════════════════════════════════════════════════════════════════
# decide_g8_status() — lệch nội bộ đã sửa: artifact tự xưng 6 điều kiện bắt
# buộc nhưng bản cũ chỉ kiểm 5, bỏ qua reporting_ok (checklist chuẩn báo cáo).
# ════════════════════════════════════════════════════════════════════════════


def _decide(**overrides):
    kwargs = dict(
        irb_ok=True, sap_ok=True, g7_ok=True, results_final=True, score_ok=True,
        reporting_ok=True, presubmission_passed=27, reporting_pct=82.0,
        reporting_standard_name="CONSORT 2025",
    )
    kwargs.update(overrides)
    return G8.decide_g8_status(**kwargs)


def test_du_ca_6_dieu_kien_thi_pass():
    assert _decide().startswith("PASS")


def test_checklist_thap_KHONG_con_duoc_pass_du_5_dieu_kien_kia_dat():
    """Bug đã sửa: checklist 30% từng vẫn cho PASS vì reporting_ok bị bỏ ngoài."""
    status = _decide(reporting_ok=False, reporting_pct=30.0)
    assert not status.startswith("PASS")
    assert status.startswith("PARTIAL")
    assert "CONSORT 2025" in status
    assert "30.0" in status


def test_diem_tu_kiem_thap_van_bi_chan_nhu_cu():
    status = _decide(score_ok=False, presubmission_passed=20)
    assert status.startswith("PARTIAL")
    assert "diem tu kiem" in status


def test_ca_diem_va_checklist_deu_thieu_liet_ke_ca_hai():
    status = _decide(score_ok=False, presubmission_passed=20, reporting_ok=False, reporting_pct=40.0)
    assert "diem tu kiem" in status and "CONSORT 2025" in status


def test_thieu_irb_van_pending_bat_ke_reporting_ok():
    status = _decide(irb_ok=False, reporting_ok=False)
    assert status.startswith("PENDING")
    assert "IRB" in status


def test_thieu_results_final_van_pending():
    status = _decide(results_final=False)
    assert status.startswith("PENDING")
    assert "phan tich THAT" in status
