"""Hồi quy cổng G7 (BẢN THẢO) — đợt hoàn thiện 2026-07-28.

Lỗi trung tâm, TỰ TÁI HIỆN ĐƯỢC (không phải suy đoán): chạy G7 trên một đề tài chỉ
có G0 — mà G0 còn đang BLOCKED, thoát mã 2 — và không hề có G1–G6:

    python tools/run_g0_auto.py --study ZZ-G7-PROBE --topic "..." → exit 2 (BLOCKED)
    python tools/run_g7_auto.py --study ZZ-G7-PROBE
    → "✅ G7 HOÀN THÀNH", guardrail "✅ PASS", exit 0, bản thảo IMRAD 3.547 từ

G7 là cổng có đầu ra đi RA NGOÀI xa nhất (bản thảo gửi tạp chí), nên nó tuyên bố
hoàn thành một bản thảo cho đề tài chưa có câu hỏi, chưa có thiết kế, chưa qua Hội
đồng Đạo đức, chưa có dữ liệu.

Nguyên tắc viết test: KIỂM HÀNH VI, không grep chuỗi trong mã nguồn. Không gọi mạng.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
for _p in (str(REPO_ROOT), str(TOOLS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import g7_quality_gate as G7Q  # noqa: E402
import gate_contract as GC  # noqa: E402
import run_g7_auto as G7  # noqa: E402

# ════════════════════════════════════════════════════════════════════════════
# Fixture
# ════════════════════════════════════════════════════════════════════════════

def _manuscript(*, with_results: bool = False, extra: str = "") -> str:
    """Bản thảo A8 tối thiểu — đủ mục IMRAD mà g7_quality_gate yêu cầu."""
    results_block = (
        "Trong 320 người tham gia, tỷ lệ biến cố là 12,4% so với 18,9% "
        "(HR 0,64; 95%CI 0,45-0,91; p = 0,013).\n"
        if with_results else
        "[CẦN KẾT QUẢ THẬT — Bảng 2 kết cục chính]\n"
        "[CẦN KẾT QUẢ THẬT — Bảng 1 đặc điểm nền]\n"
    )
    return (
        "# BẢN THẢO DRAFT\n\n"
        "## TÓM TẮT\nNền tảng, mục tiêu, thiết kế.\n\n"
        "## I. GIỚI THIỆU\nBối cảnh nghiên cứu.\n\n"
        "## II. PHƯƠNG PHÁP\n"
        "**§5 Cỡ mẫu:** Cỡ mẫu được tính theo công thức log-rank, N = 320.\n"
        "**§7 Đạo đức và đăng ký:** [CẦN — chưa có phê duyệt đạo đức thật]\n\n"
        "## III. KẾT QUẢ\n" + results_block + "\n"
        "## IV. BÀN LUẬN\nBàn luận.\n\n"
        "## V. KẾT LUẬN\nKết luận.\n\n"
        "## TÀI LIỆU THAM KHẢO\n1. Nguyen A. PMID: 30000001\n"
        + extra
        + "\nCần bác sĩ kiểm chứng.\n"
    )


def _cps(**over) -> dict:
    """Bộ checkpoint G0–G7 đầy đủ, không cổng nào bị chặn."""
    base = {
        "G0": {"gate": "G0", "topic": "x"},
        "G1": {"gate": "G1", "design": {"internal_code": "cohort"}},
        "G2": {"gate": "G2", "g2_irb_number": "IRB-2026-001",
               "g2_registration": "NCT01234567"},
        "G3": {"gate": "G3", "n_adjusted": 320},
        "G4": {"gate": "G4", "g4_status": "LOCKED", "g4_lock_date": "2026-05-01"},
        "G5": {"gate": "G5"},
        "G6": {"gate": "G6"},
        "G7": {"gate": "G7", "guardrail": {"status": "✅ PASS", "errors": []}},
    }
    base.update(over)
    return base


def _meta_confirmed() -> dict:
    """study_meta.json với gate_params.G7 đã được tác giả chốt đủ."""
    return {
        "irb_approved": True,
        "sap_lock_date": "2026-05-01",
        "data_lock_date": "2026-06-01",
        "results_final": True,
        "gate_params": {
            "G7": {
                "title": "Hiệu quả dapagliflozin ở bệnh nhân suy tim EF bảo tồn",
                "authors": "Nguyễn Văn A (BV Quân y 175, ORCID 0000-0002-1825-0097)",
                "target_journal": "Tạp chí Y học Việt Nam",
                "author_contributions": "A: thiết kế, phân tích, viết bản thảo",
                "coi_declared": "Không có xung đột lợi ích",
                "funding_declared": "Đề tài cấp cơ sở, mã số 2026-01",
                "data_sharing_statement": "Dữ liệu khử định danh cung cấp theo yêu cầu hợp lý",
                "ai_use_declared": "Dùng EBM Copilot hỗ trợ dựng khung bản thảo; "
                                   "AI không phải tác giả (ICMJE)",
                "manuscript_reviewed_confirmed": True,
                "reviewed_by_role": "PI",
                "reviewed_at": "2026-07-28T10:00:00",
            }
        },
    }


# ════════════════════════════════════════════════════════════════════════════
# 1. LỖI TRUNG TÂM — bản thảo trên nền rỗng
# ════════════════════════════════════════════════════════════════════════════

def test_chan_khi_thieu_thiet_ke_G1():
    """Không có G1 thì run_g7_auto rơi về design_code='cohort' → chọn chuẩn báo cáo
    STROBE cho MỌI đề tài, kể cả RCT. Đó là sai nhìn thấy được từ trang đầu bản thảo."""
    report = G7Q.evaluate_g7_quality(
        manuscript_text=_manuscript(),
        checkpoints=_cps(G1={}),
        meta={},
    )
    assert report["status"] == G7Q.STATUS_BLOCKED
    row = next(r for r in report["automatic_criteria"] if r["id"] == "G7-AUTO-01")
    assert row["status"] == "BLOCK"


def test_canh_bao_khi_thieu_G0_G2_G3_G4():
    report = G7Q.evaluate_g7_quality(
        manuscript_text=_manuscript(),
        checkpoints=_cps(G2={}, G3={}),
        meta={},
    )
    row = next(r for r in report["automatic_criteria"] if r["id"] == "G7-AUTO-02")
    assert row["status"] == "REVIEW"
    assert "G2" in row["evidence"] and "G3" in row["evidence"]


def test_khong_pass_khi_chua_co_ket_qua_that():
    """Bản thảo còn ô [CẦN KẾT QUẢ THẬT] thì không bao giờ được PASS."""
    meta = _meta_confirmed()
    meta["results_final"] = False
    report = G7Q.evaluate_g7_quality(
        manuscript_text=_manuscript(with_results=False),
        checkpoints=_cps(), meta=meta, citation_verification_ok=True,
    )
    assert report["status"] == G7Q.STATUS_DRAFT_READY
    assert report["placeholder_counts"]["results"] > 0


def test_pass_khi_du_dieu_kien():
    """Đường PASS phải ĐẠT ĐƯỢC — cổng không bao giờ qua nổi cũng vô dụng như cổng
    luôn qua."""
    report = G7Q.evaluate_g7_quality(
        manuscript_text=_manuscript(with_results=True),
        checkpoints=_cps(), meta=_meta_confirmed(),
        citation_verification_ok=True,
    )
    assert report["status"] == G7Q.STATUS_CONFIRMED, report["pending_actions"]
    assert report["pending_actions"] == []


# ════════════════════════════════════════════════════════════════════════════
# 2. KHẲNG ĐỊNH VỀ VIỆC CHƯA LÀM — lớp phòng thủ cuối trước khi ra ngoài
# ════════════════════════════════════════════════════════════════════════════

def test_chan_khang_dinh_da_duoc_hoi_dong_dao_duc_phe_duyet():
    """Chạy thử thật cho thấy bản thảo in nguyên "Nghiên cứu được Hội đồng Đạo đức
    phê duyệt … Mọi người tham gia ký ICF … Thực hiện theo Helsinki" cho một đề tài
    chưa hề nộp Hội đồng. Nếu bác sĩ về sau chỉ điền số IRB mà không đọc lại cả
    đoạn, bản thảo gửi tạp chí khẳng định đã làm việc chưa hề làm."""
    text = _manuscript().replace(
        "**§7 Đạo đức và đăng ký:** [CẦN — chưa có phê duyệt đạo đức thật]",
        "**§7 Đạo đức:** Nghiên cứu được Hội đồng Đạo đức phê duyệt.",
    )
    report = G7Q.evaluate_g7_quality(
        manuscript_text=text, checkpoints=_cps(G2={}), meta={},
    )
    assert report["status"] == G7Q.STATUS_BLOCKED
    assert any("Hội đồng Đạo đức" in c for c in report["unsupported_claims"])


def test_khang_dinh_hop_le_khi_co_bang_chung_that():
    """Có G2 thật (số IRB) thì cùng câu đó là hợp lệ — không được cảnh báo oan."""
    text = _manuscript(with_results=True).replace(
        "**§7 Đạo đức và đăng ký:** [CẦN — chưa có phê duyệt đạo đức thật]",
        "**§7 Đạo đức:** Nghiên cứu được Hội đồng Đạo đức phê duyệt (IRB-2026-001).",
    )
    report = G7Q.evaluate_g7_quality(
        manuscript_text=text, checkpoints=_cps(), meta=_meta_confirmed(),
        citation_verification_ok=True,
    )
    assert report["unsupported_claims"] == []
    assert report["status"] == G7Q.STATUS_CONFIRMED


def test_loi_canh_bao_trong_nhan_CAN_khong_bi_bat_nham():
    """Nhãn [CẦN…] chứa chỉ dẫn "KHÔNG được viết 'nghiên cứu được Hội đồng Đạo đức
    phê duyệt'". Đó là CHỈ DẪN, không phải khẳng định — bản vá đầu tiên của chính
    tôi đã bắt nhầm chính lời cảnh báo này."""
    text = _manuscript().replace(
        "[CẦN — chưa có phê duyệt đạo đức thật]",
        "[CẦN — KHÔNG được viết 'nghiên cứu được Hội đồng Đạo đức phê duyệt' "
        "trước khi việc đó xảy ra thật]",
    )
    claims = G7Q.find_unsupported_claims(text, {"irb_approved": False})
    assert claims == [], f"bắt nhầm chỉ dẫn trong nhãn [CẦN…]: {claims}"


@pytest.mark.parametrize("cau,tin_hieu", [
    ("SAP đã khóa trước khi mở dữ liệu.", "sap_locked"),
    ("Cơ sở dữ liệu đã khóa ngày 01/06/2026.", "db_locked"),
    ("Nghiên cứu đã được đăng ký tại ClinicalTrials.gov.", "registered"),
])
def test_chan_cac_khang_dinh_khac(cau, tin_hieu):
    claims = G7Q.find_unsupported_claims(cau, {tin_hieu: False})
    assert claims, f"không bắt được khẳng định: {cau}"
    assert G7Q.find_unsupported_claims(cau, {tin_hieu: True}) == []


# ════════════════════════════════════════════════════════════════════════════
# 3. ĐẾM Ô TRỐNG TRÊN BẢN THẢO THẬT (đọc TỪ ĐĨA)
# ════════════════════════════════════════════════════════════════════════════

def test_dem_o_trong_theo_tung_muc():
    ph = G7Q.count_placeholders(_manuscript())
    assert ph["results"] == 2
    assert ph["results_section"] >= 2
    assert ph["total"] >= 3


def test_evaluate_study_doc_ban_thao_TU_DIA(tmp_path):
    """Điểm khác cốt lõi của G7: bác sĩ SỬA TAY bản thảo, và lần chấm sau phải
    phản ánh bản đã sửa — không phải bản khung do công cụ sinh ra."""
    study = "T-G7"
    d = tmp_path / study
    d.mkdir(parents=True)
    for gate, cp in _cps().items():
        (d / f"{gate}_checkpoint.json").write_text(
            json.dumps(cp, ensure_ascii=False), encoding="utf-8")
    (d / "study_meta.json").write_text(
        json.dumps(_meta_confirmed(), ensure_ascii=False), encoding="utf-8")
    (d / f"A12_CITATION_VERIFICATION_{study}.md").write_text(
        "Đã xác minh 10/10 PMID.", encoding="utf-8")
    md = d / f"G7_A8_MANUSCRIPT_{study}.md"

    # Lần 1 — bản khung, còn ô [CẦN KẾT QUẢ THẬT]
    md.write_text(_manuscript(with_results=False), encoding="utf-8")
    r1 = G7Q.evaluate_study(study, d)
    assert r1["status"] == G7Q.STATUS_DRAFT_READY
    assert r1["placeholder_counts"]["results"] > 0

    # Lần 2 — bác sĩ đã điền kết quả thật vào CHÍNH file đó
    md.write_text(_manuscript(with_results=True), encoding="utf-8")
    r2 = G7Q.evaluate_study(study, d)
    assert r2["status"] == G7Q.STATUS_CONFIRMED, r2["pending_actions"]
    assert r2["placeholder_counts"]["results"] == 0
    assert (d / "G7_QUALITY_REPORT.md").exists()


# ════════════════════════════════════════════════════════════════════════════
# 4. GUARDRAIL R6 — quy tắc từng có logic NGƯỢC
# ════════════════════════════════════════════════════════════════════════════

def test_r6_khong_con_phat_ban_thao_da_hoan_thien():
    """Quy tắc cũ: "can_total >= 15 → PASS, ngược lại → LỖI ĐỎ". Nghĩa là bản thảo
    ĐÃ HOÀN THIỆN (bác sĩ điền hết, sẵn sàng nộp) bị chính guardrail CHẶN vì "chỉ 3
    trường [CẦN...]". Một quy tắc liêm chính không được phạt việc hoàn thành."""
    hoan_thien = _manuscript(with_results=True)
    errors, warnings = G7.guardrail_g7(hoan_thien)
    assert not any("R6" in e for e in errors), \
        f"guardrail vẫn chặn bản thảo đã hoàn thiện: {errors}"
    assert any("R6" in w for w in warnings)


def test_r6_van_canh_bao_khi_co_so_lieu_ma_khong_qua_G6():
    """Mục Kết quả có số liệu và không còn ô [CẦN KẾT QUẢ THẬT] → phải nêu để
    g7_quality_gate đối chiếu với G6/results_final."""
    _, warnings = G7.guardrail_g7(_manuscript(with_results=True))
    assert any("đối chiếu" in w for w in warnings)


# ════════════════════════════════════════════════════════════════════════════
# 5. HỢP ĐỒNG gate_params.G7
# ════════════════════════════════════════════════════════════════════════════

def test_gate_params_co_khoi_G7():
    skel = GC._GATE_PARAMS_SKELETON
    assert "G7" in skel
    for key in ("title", "authors", "target_journal", "author_contributions",
                "coi_declared", "funding_declared", "data_sharing_statement",
                "ai_use_declared", "manuscript_reviewed_confirmed",
                "reviewed_by_role", "reviewed_at"):
        assert key in skel["G7"], f"skeleton G7 thiếu {key}"
    assert skel["G7"]["manuscript_reviewed_confirmed"] is False, \
        "hệ KHÔNG được tự bật cờ đã-đọc-lại"


def test_ensure_study_meta_tao_khoi_G7(tmp_path):
    GC.ensure_study_meta(tmp_path, seed={"topic": "x"})
    meta = json.loads((tmp_path / "study_meta.json").read_text(encoding="utf-8"))
    assert "G7" in meta["gate_params"]
    assert meta["gate_params"]["G7"]["manuscript_reviewed_confirmed"] is False


def test_thieu_khai_bao_ICMJE_khong_duoc_pass():
    meta = _meta_confirmed()
    del meta["gate_params"]["G7"]["coi_declared"]
    report = G7Q.evaluate_g7_quality(
        manuscript_text=_manuscript(with_results=True),
        checkpoints=_cps(), meta=meta, citation_verification_ok=True,
    )
    assert report["status"] == G7Q.STATUS_DRAFT_READY
    row = next(r for r in report["human_criteria"] if r["id"] == "G7-HUMAN-02")
    assert row["status"] == "REVIEW" and "Xung đột lợi ích" in row["evidence"]


def test_chua_doc_lai_toan_van_khong_duoc_pass():
    meta = _meta_confirmed()
    meta["gate_params"]["G7"]["manuscript_reviewed_confirmed"] = False
    report = G7Q.evaluate_g7_quality(
        manuscript_text=_manuscript(with_results=True),
        checkpoints=_cps(), meta=meta, citation_verification_ok=True,
    )
    assert report["status"] == G7Q.STATUS_DRAFT_READY
    row = next(r for r in report["human_criteria"] if r["id"] == "G7-HUMAN-04")
    assert row["status"] == "REVIEW"


def test_thieu_A12_kiem_chung_trich_dan_khong_duoc_pass():
    report = G7Q.evaluate_g7_quality(
        manuscript_text=_manuscript(with_results=True),
        checkpoints=_cps(), meta=_meta_confirmed(),
        citation_verification_ok=None,
    )
    assert report["status"] == G7Q.STATUS_DRAFT_READY
    row = next(r for r in report["automatic_criteria"] if r["id"] == "G7-AUTO-07")
    assert row["status"] == "REVIEW"


# ════════════════════════════════════════════════════════════════════════════
# 6. BÁO CÁO
# ════════════════════════════════════════════════════════════════════════════

def test_write_quality_report_sinh_ca_json_va_markdown(tmp_path):
    report = G7Q.evaluate_g7_quality(
        manuscript_text=_manuscript(), checkpoints=_cps(), meta={})
    md = G7Q.write_quality_report("S", tmp_path, report)
    text = md.read_text(encoding="utf-8")
    assert (tmp_path / "G7_QUALITY_REPORT.json").exists()
    assert "Cần bác sĩ kiểm chứng" in text
    assert "Giới hạn phán định" in text
    assert "G7-AUTO-00" in text and "G7-HUMAN-01" in text
    data = json.loads((tmp_path / "G7_QUALITY_REPORT.json").read_text(encoding="utf-8"))
    assert data["contract_version"] == G7Q.QUALITY_CONTRACT_VERSION


def test_scope_statement_khong_overclaim():
    """PASS_G7_CONFIRMED không được đọc thành 'bản thảo tốt/đáng đăng'."""
    report = G7Q.evaluate_g7_quality(
        manuscript_text=_manuscript(with_results=True),
        checkpoints=_cps(), meta=_meta_confirmed(), citation_verification_ok=True)
    scope = report["scope_statement"]
    assert "KHÔNG có nghĩa bản thảo tốt" in scope
    assert "G8" in scope
