"""Hồi quy cổng G0 — đợt hoàn thiện 2026-07-28.

Bối cảnh: G0 là cổng ĐẦU của chuỗi G0–G10 và cũng là cổng DUY NHẤT chưa có hợp
đồng chất lượng riêng. Một vòng soi độc lập 7 trục (2026-07-28) trả về 56 phát
hiện thô; sau khi tự kiểm chứng lại trên code thật, các lỗi dưới đây được xác
nhận và vá. Mỗi test ở đây neo vào MỘT lỗi cụ thể đã tái hiện được.

Nguyên tắc viết test của file này (rút từ điểm yếu của file hồi quy trước):
KIỂM HÀNH VI, không grep chuỗi trong mã nguồn. Một test grep vẫn xanh khi tính
năng bị xoá mà chuỗi còn nằm trong comment, và vỡ oan khi chuỗi được sinh động.
Không test nào ở đây gọi mạng.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
for _p in (str(REPO_ROOT), str(TOOLS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import g0_quality_gate as G0Q  # noqa: E402
import gate_contract as GC  # noqa: E402
import run_g0_auto as G0  # noqa: E402

PYTHON = sys.executable


class _Rec:
    """Bản ghi PubMed tối thiểu (đủ thuộc tính G0 đọc)."""

    def __init__(self, pmid="30000001", title="T", publication_date="2025"):
        self.pmid = pmid
        self.title = title
        self.publication_date = publication_date
        self.journal_or_organization = "J Test"
        self.authors = "Author A"
        self.url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"


def _results(**over):
    base = {
        "sr_ma": [_Rec("30000001")], "rct": [_Rec("30000002")],
        "guideline": [_Rec("30000003")], "observational": [_Rec("30000004")],
        "recent": [_Rec("30000005")],
        "all_pmids": ["30000001", "30000002", "30000003", "30000004", "30000005"],
        "total": 5,
        "true_counts": {"sr_ma": 5, "rct": 9, "guideline": 2,
                        "observational": 40, "recent": 12},
        "query_errors": {},
    }
    base.update(over)
    return base


def _confirmed_g0_meta() -> dict:
    """Khối gate_params.G0 đã được bác sĩ điền đủ (dùng cho đường PASS)."""
    return {
        "population": "Bệnh nhân ≥18 tuổi suy tim EF bảo tồn, ngoại trú",
        "intervention": "Dapagliflozin 10 mg/ngày trong 12 tháng",
        "comparison": "Giả dược trên nền điều trị chuẩn",
        "outcomes": ["Tử vong tim mạch hoặc nhập viện vì suy tim"],
        "primary_outcome": "Gộp tử vong tim mạch hoặc nhập viện vì suy tim",
        "primary_outcome_measure": "Tỷ lệ biến cố (%)",
        "primary_outcome_timepoint": "12 tháng",
        "hypothesis_h0": "Không khác biệt so với giả dược",
        "hypothesis_h1": "Giảm kết cục gộp so với giả dược",
        "expected_direction": "giảm",
        "test_type": "superiority",
        "question_type": "therapy",
        "finer_feasible": "Đủ 320 BN/năm",
        "finer_interesting": "Ưu tiên của khoa",
        "finer_novel": "Chưa có dữ liệu Việt Nam",
        "finer_ethical": "Nguy cơ tối thiểu, có ICF",
        "finer_relevant": "Có thể đổi phác đồ",
        "evidence_reviewed_confirmed": True,
        "novelty_justification": "Đã đọc 62 SR/MA và 16 hồ sơ đang tuyển",
        "pico_confirmed": True,
        "reviewed_by_role": "PI",
        "reviewed_at": "2026-07-28T09:00:00",
    }


def _checkpoint(**over) -> dict:
    """Checkpoint G0 hợp lệ tối thiểu (đủ mọi khoá hợp đồng)."""
    cp = {
        "study": "S", "gate": "G0", "topic": "heart failure",
        "base_query": "heart failure",
        "evidence_level": "MẠNH — có SR/MA", "research_gaps": ["g"],
        "design_suggestion": "RCT ngẫu nhiên có đối chứng HOẶC Cohort tiến cứu",
        "pubmed_results": {
            "total_found": 5, "n_pmids": 5, "all_pmids": ["30000001"],
            "n_sr": 5, "n_rct": 9, "n_guideline": 2, "n_observational": 40,
            "n_recent": 12, "counts_are_real": True, "counts_unavailable": [],
        },
        "guardrail": {"passed": True, "n_errors": 0, "errors": []},
        "artifacts": {"A1_markdown": "x.md", "A1_docx": None},
        "registry_check": {"checked": True, "n_trials": 46, "n_active": 16},
    }
    cp.update(over)
    return cp


def _artifact_text() -> str:
    """Artifact A1 thật (sinh offline) — dùng cho tiêu chí AUTO-05."""
    res = _results()
    gaps = G0.analyze_evidence_gaps(res, "heart failure")
    return G0.generate_a1_artifact("heart failure", "S", {"base": "heart failure"},
                                   res, gaps, "2026-07-28 09:00")


# ════════════════════════════════════════════════════════════════════════════
# 1. HỢP ĐỒNG TRẠNG THÁI — lỗi trung tâm: cổng khởi đầu báo "HOÀN THÀNH" khi
#    câu hỏi nghiên cứu chưa tồn tại
# ════════════════════════════════════════════════════════════════════════════

def test_g0_khong_bao_pass_khi_pico_chua_duoc_bac_si_chot():
    """Trước bản vá: G0 in "✅ G0 HOÀN THÀNH" + exit 0 dù mọi ô P/I/C/O còn là
    placeholder. Nay phải là DRAFT_READY (chờ người thật), không phải PASS."""
    report = G0Q.evaluate_g0_quality(
        checkpoint=_checkpoint(), meta={}, artifact_text=_artifact_text(),
        registry_check={"checked": True, "n_trials": 46, "n_active": 16},
    )
    assert report["status"] == G0Q.STATUS_DRAFT_READY
    assert report["human_confirmation_complete"] is False
    assert report["automated_checks_passed"] is True, \
        "phần máy làm được vẫn phải được ghi nhận là đạt"


def test_g0_pass_khi_bac_si_da_chot_du_quyet_dinh():
    """Đường PASS phải ĐẠT ĐƯỢC — một cổng không bao giờ qua nổi cũng vô dụng
    như một cổng luôn qua."""
    meta = {"gate_params": {"G0": _confirmed_g0_meta()}}
    report = G0Q.evaluate_g0_quality(
        checkpoint=_checkpoint(), meta=meta, artifact_text=_artifact_text(),
        registry_check={"checked": True, "n_trials": 46, "n_active": 16},
    )
    assert report["status"] == G0Q.STATUS_CONFIRMED, report["pending_actions"]
    assert report["pending_actions"] == []


def test_g0_dung_reason_missing_pico_lan_dau_tien():
    """GC.REASON_MISSING_PICO đã nằm trong gate_contract.py từ đầu nhưng CHƯA
    TỪNG có dòng code nào dùng — hằng số chết đúng chỗ cần nó nhất."""
    report = G0Q.evaluate_g0_quality(
        checkpoint=_checkpoint(), meta={}, artifact_text=_artifact_text(),
        registry_check={"checked": True, "n_trials": 1, "n_active": 0},
    )
    ni = report.get("needs_input")
    assert ni and ni["blocked"] is True
    assert ni["reason_code"] == GC.REASON_MISSING_PICO
    assert "PICO" in ni["remediation"]["must_not_fabricate"]


def test_g0_block_khi_khong_co_bang_chung_that():
    cp = _checkpoint()
    cp["pubmed_results"]["n_pmids"] = 0
    report = G0Q.evaluate_g0_quality(checkpoint=cp, meta={}, artifact_text=_artifact_text())
    assert report["status"] == G0Q.STATUS_BLOCKED
    assert report["automated_checks_passed"] is False


def test_g0_block_khi_checkpoint_thieu_truong_hop_dong():
    """Checkpoint khuyết = cổng sau đọc hụt trong im lặng. Phải chặn tại G0."""
    cp = _checkpoint()
    del cp["pubmed_results"]["all_pmids"]
    report = G0Q.evaluate_g0_quality(checkpoint=cp, meta={}, artifact_text=_artifact_text())
    assert report["status"] == G0Q.STATUS_BLOCKED
    row = next(r for r in report["automatic_criteria"] if r["id"] == "G0-AUTO-04")
    assert "all_pmids" in row["evidence"]


def test_ket_cuc_chinh_phai_duy_nhat():
    """Doctrine: kết cục CHÍNH duy nhất. Khai 2 kết cục chính → chưa được PASS."""
    g0 = _confirmed_g0_meta()
    g0["primary_outcome"] = ["Tử vong do mọi nguyên nhân", "Nhập viện vì suy tim"]
    report = G0Q.evaluate_g0_quality(
        checkpoint=_checkpoint(), meta={"gate_params": {"G0": g0}},
        artifact_text=_artifact_text(),
        registry_check={"checked": True, "n_trials": 1, "n_active": 0},
    )
    row = next(r for r in report["human_criteria"] if r["id"] == "G0-HUMAN-02")
    assert row["status"] == "REVIEW"
    assert "DUY NHẤT" in row["evidence"]


def test_nghien_cuu_mo_ta_khong_bi_ep_bia_gia_thuyet():
    """Ép nghiên cứu MÔ TẢ phải có H0/H1 sẽ đẩy bác sĩ đến chỗ bịa giả thuyết."""
    g0 = _confirmed_g0_meta()
    g0.update({"test_type": "descriptive", "question_type": "descriptive",
               "hypothesis_h0": None, "hypothesis_h1": None,
               "expected_direction": None})
    report = G0Q.evaluate_g0_quality(
        checkpoint=_checkpoint(), meta={"gate_params": {"G0": g0}},
        artifact_text=_artifact_text(),
        registry_check={"checked": True, "n_trials": 1, "n_active": 0},
    )
    row = next(r for r in report["human_criteria"] if r["id"] == "G0-HUMAN-03")
    assert row["status"] == "PASS"


def test_placeholder_khong_duoc_tinh_la_da_dien():
    """Dán "[CẦN BÁC SĨ ẤN ĐỊNH]" vào ô PICO không phải là đã điền."""
    g0 = _confirmed_g0_meta()
    g0["population"] = "[CẦN BÁC SĨ XÁC NHẬN]"
    report = G0Q.evaluate_g0_quality(
        checkpoint=_checkpoint(), meta={"gate_params": {"G0": g0}},
        artifact_text=_artifact_text(),
        registry_check={"checked": True, "n_trials": 1, "n_active": 0},
    )
    row = next(r for r in report["human_criteria"] if r["id"] == "G0-HUMAN-01")
    assert row["status"] == "REVIEW" and "population" in row["evidence"]


# ════════════════════════════════════════════════════════════════════════════
# 2. MÃ THOÁT — G0 từng là cổng DUY NHẤT không có EXIT_GUARDRAIL_FAIL
# ════════════════════════════════════════════════════════════════════════════

def test_gate_params_co_khoi_G0():
    """Bác sĩ phải có CHỖ CHUẨN để pin quyết định; trước đây G0 là cổng duy nhất
    không có khối gate_params nào."""
    meta = GC._GATE_PARAMS_SKELETON
    assert "G0" in meta
    for key in ("population", "primary_outcome", "hypothesis_h0", "test_type",
                "question_type", "finer_feasible", "pico_confirmed",
                "reviewed_by_role", "reviewed_at"):
        assert key in meta["G0"], f"skeleton G0 thiếu {key}"
    assert meta["G0"]["pico_confirmed"] is False, "hệ KHÔNG được tự bật cờ xác nhận"


def test_ensure_study_meta_tao_khoi_G0(tmp_path):
    GC.ensure_study_meta(tmp_path, seed={"topic": "x"})
    meta = json.loads((tmp_path / "study_meta.json").read_text(encoding="utf-8"))
    assert "G0" in meta["gate_params"]
    assert meta["gate_params"]["G0"]["pico_confirmed"] is False


def test_topic_rong_van_ghi_checkpoint_va_needs_input(tmp_path):
    """Hợp đồng gate_contract: BLOCKED = ĐÃ ghi checkpoint + needs_input. Trước
    bản vá, topic rỗng thoát mã 2 nhưng KHÔNG để lại gì cho pipeline chẩn đoán."""
    env = dict(os.environ, USE_MOCK_SOURCES="true", PYTHONUTF8="1")
    proc = subprocess.run(
        [PYTHON, str(TOOLS_DIR / "run_g0_auto.py"), "--study", "ZZ-EMPTY", "--topic", "   "],
        cwd=tmp_path, env=env, capture_output=True, text=True, timeout=180,
    )
    assert proc.returncode == GC.EXIT_BLOCKED, proc.stdout[-500:]
    cp_path = tmp_path / "exports" / "ZZ-EMPTY" / "G0_checkpoint.json"
    assert cp_path.exists(), "BLOCKED mà không ghi checkpoint = pipeline không chẩn đoán được"
    cp = json.loads(cp_path.read_text(encoding="utf-8"))
    assert GC.is_blocked(cp) is True
    assert cp["guardrail"]["passed"] is False


# ════════════════════════════════════════════════════════════════════════════
# 3. SỐ HIT THẬT — số 0 BỊA không được dán nhãn "THẬT"
# ════════════════════════════════════════════════════════════════════════════

def test_counts_are_real_bat_ca_nhanh_VANG_MAT():
    """Bản vá trước dùng all() trên `true_counts.values()` — nên nhánh VẮNG MẶT
    (khi client.search ném exception, khóa không bao giờ được gán) vẫn cho
    counts_are_real=True, và _n('sr_ma') lùi về len([])=0. Tức đúng con số 0 bịa
    lại được dán nhãn "số hit THẬT" — nguyên văn lỗi mà bản vá định đóng.
    Test cũ chỉ phủ biến thể giá trị None, không phủ biến thể thiếu khóa."""
    res = _results(true_counts={"rct": 9, "guideline": 2,
                                "observational": 40, "recent": 12})  # thiếu sr_ma
    gaps = G0.analyze_evidence_gaps(res, "x")
    assert gaps["counts_are_real"] is False, "nhánh vắng mặt vẫn bị dán nhãn 'số hit THẬT'"
    assert "sr_ma" in gaps["counts_unavailable"]


def test_counts_are_real_van_bat_bien_the_None():
    res = _results(true_counts={"sr_ma": None, "rct": 9, "guideline": 2,
                                "observational": 40, "recent": 12})
    gaps = G0.analyze_evidence_gaps(res, "x")
    assert gaps["counts_are_real"] is False
    assert "sr_ma" in gaps["counts_unavailable"]


def test_nhanh_chet_duoc_ghi_nhan_r1b():
    """PubMedClient.search() tự nuốt mọi exception rồi trả [] — nên khối except
    trong run_pubmed_searches là MÃ CHẾT trên đường lỗi mạng, và guardrail R1B in
    "✅ Không có truy vấn PubMed nào lỗi" ngay giữa sự cố mất mạng. Dấu hiệu thật
    của nhánh hỏng: 0 bài lấy về VÀ không tra được số hit."""
    res = _results(sr_ma=[], true_counts={"sr_ma": None, "rct": 9, "guideline": 2,
                                          "observational": 40, "recent": 12},
                   query_errors={"sr_ma": "0 bài lấy về VÀ không tra được số hit"})
    gaps = G0.analyze_evidence_gaps(res, "x")
    guard = G0.guardrail_check_g0(
        G0.generate_a1_artifact("x", "S", {"base": "x"}, res, gaps, "2026-07-28 09:00"),
        res,
    )
    assert guard["passed"] is False
    assert any("R1B" in e for e in guard["errors"])


# ════════════════════════════════════════════════════════════════════════════
# 4. KHÔNG BỊA KHOẢNG TRỐNG, KHÔNG DÁN NHÃN SAI PHẠM VI
# ════════════════════════════════════════════════════════════════════════════

def test_khong_bia_khoang_trong_viet_nam():
    """Khi mọi nhánh đều có bằng chứng, hệ từng in "Có thể còn khoảng trống về
    quần thể đặc thù (Việt Nam, khu vực châu Á)" dưới tiêu đề "tự động từ
    evidence thật" — một khoảng trống BỊA: hệ không tra gì về Việt Nam."""
    gaps = G0.analyze_evidence_gaps(_results(), "x")
    joined = " ".join(gaps["gaps"])
    assert "Việt Nam" not in joined and "châu Á" not in joined
    assert "[CẦN BÁC SĨ" in joined, "phải gắn nhãn cần người thật thay vì tự bịa"


def test_nhan_nghien_cuu_gan_day_noi_dung_pham_vi():
    """Nhánh 'recent' chạy với bộ lọc SR/MA·RCT·guideline, nên câu "Không có
    nghiên cứu mới trong 5 năm gần đây" là khẳng định SAI về toàn bộ y văn."""
    res = _results(true_counts={"sr_ma": 5, "rct": 9, "guideline": 2,
                                "observational": 40, "recent": 0})
    gaps = G0.analyze_evidence_gaps(res, "x")
    recent_gap = [g for g in gaps["gaps"] if "5 năm" in g]
    assert recent_gap, "mất hẳn cảnh báo về bằng chứng gần đây"
    assert "SR/MA" in recent_gap[0] and "quan sát" in recent_gap[0]


def test_tieu_de_muc_tach_so_hit_khoi_so_bai_hien_thi():
    """§3.1 từng lấy SỐ HIT (vd 203) làm tiêu đề cho danh sách ≤15 bài kèm dòng
    "... và 10 bài khác" — hai con số mâu thuẫn trong cùng một mục."""
    res = _results(true_counts={"sr_ma": 203, "rct": 9, "guideline": 2,
                                "observational": 40, "recent": 12})
    gaps = G0.analyze_evidence_gaps(res, "x")
    art = G0.generate_a1_artifact("x", "S", {"base": "x"}, res, gaps, "2026-07-28 09:00")
    assert "~203 hit" in art and "hiển thị" in art


# ════════════════════════════════════════════════════════════════════════════
# 5. TRÙNG LẶP NGHIÊN CỨU — "chưa công bố" KHÁC "chưa ai làm"
# ════════════════════════════════════════════════════════════════════════════

def test_canh_bao_khi_co_nghien_cuu_dang_tuyen():
    """PubMed chỉ biết cái ĐÃ CÔNG BỐ. Một chủ đề 0 RCT đã công bố nhưng 17 thử
    nghiệm đang tuyển bệnh từng bị gọi thẳng là "THIẾU — chưa có RCT/SR" kèm gợi
    ý làm RCT mới — tức khuyên bác sĩ khởi động một đề tài trùng."""
    res = _results(sr_ma=[], rct=[], true_counts={"sr_ma": 0, "rct": 0, "guideline": 2,
                                                  "observational": 3, "recent": 1})
    registry = {"checked": True, "n_trials": 46, "n_active": 17, "trials": []}
    gaps = G0.analyze_evidence_gaps(res, "x", registry=registry)
    assert any("đang/sắp tuyển" in g for g in gaps["gaps"])
    assert gaps["n_registered_active"] == 17
    assert "RCT" in gaps["design_hint"] and "trùng" in gaps["design_hint"], \
        "vẫn khuyên làm RCT mới mà không cảnh báo nguy cơ trùng"


def test_chua_tra_duoc_dang_ky_khong_bi_doc_thanh_khong_co_ai_lam():
    """Tra thất bại (mất mạng) phải hiển thị KHÁC HẲN với "đã tra, không có"."""
    registry = {"checked": False, "error": "timeout", "n_trials": None,
                "n_active": None, "trials": []}
    gaps = G0.analyze_evidence_gaps(_results(), "x", registry=registry)
    assert gaps["registry_checked"] is False
    assert "CHƯA TRA ĐƯỢC" in (gaps["registry_note"] or "")
    art = G0.generate_a1_artifact("x", "S", {"base": "x"}, _results(), gaps,
                                  "2026-07-28 09:00", registry=registry)
    assert "CHƯA TRA ĐƯỢC" in art
    assert "PROSPERO" in art and "ICTRP" in art, \
        "phải nói rõ hai nguồn hệ KHÔNG tra để bác sĩ tự tra"


def test_check_trial_registry_khong_bia_khi_loi(monkeypatch):
    """Mọi lỗi phải thành checked=False, không bao giờ thành 'n_trials = 0'."""
    # settings đọc env một lần lúc import, nên phải patch trực tiếp thuộc tính.
    from app.config import settings
    monkeypatch.setattr(settings, "use_mock_sources", False, raising=False)

    class _Boom:
        def get_json(self, *a, **k):
            raise RuntimeError("mạng hỏng")

    import app.utils.http as http_mod
    monkeypatch.setattr(http_mod, "HttpClient", lambda *a, **k: _Boom())
    out = G0.check_trial_registry("heart failure")
    assert out["checked"] is False
    assert out["n_trials"] is None, "lỗi mạng KHÔNG được biến thành số 0"
    assert "mạng hỏng" in (out["error"] or "")


def test_registry_bo_qua_o_che_do_mock(monkeypatch):
    monkeypatch.setenv("USE_MOCK_SOURCES", "true")
    from app.config import settings
    monkeypatch.setattr(settings, "use_mock_sources", True, raising=False)
    out = G0.check_trial_registry("heart failure")
    assert out["checked"] is False and "mock" in (out["error"] or "").lower()


# ════════════════════════════════════════════════════════════════════════════
# 6. GUARDRAIL R1–R7
# ════════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("chuoi_pii", [
    "Bệnh nhân sinh 03/11/1958 vào viện",
    "Liên hệ 0912345678 để tái khám",
    "Số căn cước 001058012345 của người bệnh",
    "Gửi kết quả về nguyenvana@example.com",
])
def test_r2_bat_hinh_dang_du_lieu_dinh_danh(chuoi_pii):
    """R2 cũ chỉ dò 5 chuỗi NHÃN tiếng Việt ("họ tên", "ngày sinh"…), nên dữ liệu
    định danh THẬT — ngày sinh, số điện thoại, số căn cước, email — đi thẳng qua
    guardrail và được ghi vào exports/ nếu bác sĩ lỡ dán bệnh cảnh thật vào
    --topic. Bất biến số 4 của dự án: KHÔNG lưu PII."""
    art = f"# A1\nCần bác sĩ kiểm chứng. [BẢN NHÁP TỰ ĐỘNG] [CẦN BÁC SĨ XÁC NHẬN]\n{chuoi_pii}\n"
    guard = G0.guardrail_check_g0(art, _results())
    assert guard["passed"] is False
    assert any("R2" in e for e in guard["errors"]), guard["errors"]


def test_r2_khong_bao_dong_gia_tren_artifact_that():
    """Artifact G0 thật (đầy PMID, URL, năm, NCT) không được kích hoạt R2."""
    guard = G0.guardrail_check_g0(_artifact_text(), _results())
    assert guard["passed"] is True, guard["errors"]


def test_r3_r4_khong_phan_biet_hoa_thuong():
    """Bản cũ so khớp đúng một cách viết hoa duy nhất nên "g1_status = pass" lọt."""
    art = ("# A1\nCần bác sĩ kiểm chứng. [BẢN NHÁP TỰ ĐỘNG] [CẦN BÁC SĨ XÁC NHẬN]\n"
           "g1_status = pass\n")
    guard = G0.guardrail_check_g0(art, _results())
    assert any("R3" in e for e in guard["errors"])


def test_r5_chan_khuyen_cao_lam_sang_trong_cong_nghien_cuu():
    """R5 (tách 2 trục) vắng mặt hoàn toàn ở G0 dù CLAUDE.md liệt kê R1–R7.
    G0 đặt câu hỏi nghiên cứu — không phải cổng kê đơn."""
    art = ("# A1\nCần bác sĩ kiểm chứng. [BẢN NHÁP TỰ ĐỘNG] [CẦN BÁC SĨ XÁC NHẬN]\n"
           "Kết luận: nên kê dapagliflozin cho bệnh nhân suy tim EF bảo tồn.\n")
    guard = G0.guardrail_check_g0(art, _results())
    assert guard["passed"] is False
    assert any("R5" in e for e in guard["errors"]), guard["errors"]


# ════════════════════════════════════════════════════════════════════════════
# 7. HỢP ĐỒNG CHECKPOINT VỚI CÁC CỔNG SAU
# ════════════════════════════════════════════════════════════════════════════

def test_checkpoint_du_truong_cho_cong_sau(tmp_path):
    """Ba lệch hợp đồng THẬT đã tái hiện được:
    · run_g9_auto.py:578 đọc g0["n_sr"] TOP-LEVEL → thư gửi tổng biên tập tạp chí
      in "0 systematic review(s) and 0 randomized controlled trial(s)".
    · run_pipeline_integrated.py đọc pmids_verified/n_pmids/evidence_note TOP-LEVEL
      → đề cương trình Hội đồng Đạo đức tự khai 0 PMID.
    · g1_quality_gate tìm pubmed_results.all_pmids → không có, phải lùi về regex
      trên file .md đã bị cắt còn 5 bài mỗi mục."""
    res = _results()
    gaps = G0.analyze_evidence_gaps(res, "x")
    guard = {"passed": True, "errors": []}
    cp_path = G0.write_checkpoint("S", tmp_path, res, gaps, guard,
                                  tmp_path / "a.md", None, topic="x", base_query="x",
                                  registry={"checked": True, "n_trials": 3, "n_active": 1})
    cp = json.loads(cp_path.read_text(encoding="utf-8"))

    assert cp["n_sr"] == gaps["n_sr"] and cp["n_rct"] == gaps["n_rct"], "G9 đọc top-level"
    assert cp["n_pmids"] == 5 and cp["pmids_verified"] == res["all_pmids"]
    assert cp["evidence_note"], "run_pipeline_integrated đọc khóa này"
    assert cp["pubmed_results"]["all_pmids"] == res["all_pmids"], "g1_quality_gate đọc khóa này"
    assert cp["pubmed_results"]["counts_are_real"] is True
    assert "counts_unavailable" in cp["pubmed_results"]
    assert cp["pubmed_results"]["n_observational"] == gaps["n_observational"]
    assert cp["registry_check"]["checked"] is True


def test_gate_status_noi_that_khi_bi_chan(tmp_path):
    """gate_status từng là hằng số "DRAFT — CHỜ BÁC SĨ XÁC NHẬN PICO" kể cả khi
    cổng BỊ CHẶN, nên study_readiness.py/list_studies.py đều báo "✅ có checkpoint"."""
    res = _results(all_pmids=[], total=0)
    gaps = G0.analyze_evidence_gaps(res, "x")
    cp_path = G0.write_checkpoint("S", tmp_path, res, gaps,
                                  {"passed": True, "errors": []},
                                  tmp_path / "a.md", None, blocked=True)
    cp = json.loads(cp_path.read_text(encoding="utf-8"))
    assert "BLOCKED" in cp["gate_status"]

    cp_path = G0.write_checkpoint("S", tmp_path, res, gaps,
                                  {"passed": False, "errors": ["R2 🔴 PII"]},
                                  tmp_path / "a.md", None, blocked=False)
    cp = json.loads(cp_path.read_text(encoding="utf-8"))
    assert "BLOCKED" in cp["gate_status"] and "guardrail" in cp["gate_status"].lower()


# ════════════════════════════════════════════════════════════════════════════
# 8. NỘI DUNG ARTIFACT A1 THEO DOCTRINE (6 thành phần)
# ════════════════════════════════════════════════════════════════════════════

def test_a1_co_du_6_thanh_phan_doctrine():
    art = _artifact_text()
    for section in G0Q.REQUIRED_A1_SECTIONS:
        assert section.casefold() in art.casefold(), f"A1 thiếu mục: {section}"


def test_a1_co_gia_thuyet_h0_h1():
    """THÀNH PHẦN 3 của doctrine (giả thuyết H0/H1 + chiều kỳ vọng) THIẾU HẲN
    khỏi artifact trước bản vá."""
    art = _artifact_text()
    assert "H0" in art and "H1" in art and "Chiều kỳ vọng" in art


def test_a1_co_o_dinh_nghia_va_thoi_diem_do_ket_cuc_chinh():
    """G1 chặn vì thiếu primary_outcome_measure/_timepoint, nhưng A1 không có ô
    nào để bác sĩ ghi hai thứ đó."""
    art = _artifact_text()
    assert "Định nghĩa/công cụ đo" in art and "Thời điểm đo" in art


def test_a1_khong_con_noi_sai_ve_viec_he_lam():
    """Dòng "XÁC NHẬN hoặc CHỈNH PICO (không điền lại từ đầu)" mô tả sai việc hệ
    thật sự làm — docstring đã tuyên bố câu đó SAI nhưng đầu ra vẫn in nó."""
    art = _artifact_text()
    assert "không điền lại từ đầu" not in art
    assert "Hệ KHÔNG suy ra PICO" in art


def test_a1_neu_chuan_bao_cao_du_kien():
    art = _artifact_text()
    assert "Chuẩn báo cáo DỰ KIẾN" in art


def test_che_do_mock_khong_duoc_trinh_bay_la_bang_chung_that(monkeypatch):
    """USE_MOCK_SOURCES=true trả bản ghi FIXTURE (thường lạc đề), nhưng artifact
    vẫn in "BẰNG CHỨNG HIỆN CÓ (THẬT — từ PubMed)" và "PMIDs đã được xác minh".
    Một file A1 sinh lúc thử nghiệm mà lọt vào hồ sơ đề tài sẽ đọc y hệt file thật."""
    from app.config import settings

    monkeypatch.setattr(settings, "use_mock_sources", False, raising=False)
    art_real = _artifact_text()
    assert "THẬT — từ PubMed" in art_real and "GIẢ LẬP" not in art_real

    monkeypatch.setattr(settings, "use_mock_sources", True, raising=False)
    art_mock = _artifact_text()
    assert "DỮ LIỆU GIẢ LẬP" in art_mock
    assert "USE_MOCK_SOURCES=true" in art_mock, "phải nói rõ cách chạy lại cho đúng"


def test_docstring_khong_hua_ghi_so_cai():
    """Docstring từng khai "8. Ghi vào sổ cái (so-cai-ghi-nho trigger)" trong danh
    sách việc hệ tự động làm, trong khi script không đọc cũng không ghi sổ cái nào."""
    doc = G0.__doc__ or ""
    steps = [ln.strip() for ln in doc.split("\n") if ln.strip()[:2] in
             {"1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9."}]
    assert steps, "không đọc được danh sách bước trong docstring"
    assert not any("sổ cái" in s for s in steps), \
        f"docstring vẫn hứa ghi sổ cái trong danh sách việc tự động: {steps}"
    # và phải nói rõ vì sao đã bỏ, để lần đọc sau không thêm lại
    assert "KHÔNG CÓ dòng code nào làm việc đó" in doc


@pytest.mark.parametrize("hint,expected", [
    ("SR/Meta-analysis (tổng hợp RCT hiện có)", "sr_ma"),
    ("RCT ngẫu nhiên có đối chứng HOẶC Cohort tiến cứu", "rct"),
    ("Nghiên cứu cắt ngang mô tả", "cross_sectional"),
    ("một gợi ý không rõ ràng", None),
])
def test_suy_ma_thiet_ke_tu_goi_y(hint, expected):
    """Suy sai mã thiết kế kéo theo chọn sai chuẩn báo cáo — nên thà trả None."""
    assert G0Q.infer_design_code_from_hint(hint) == expected


def test_chuan_bao_cao_khop_thiet_ke():
    std = G0Q.expected_reporting_standard("RCT ngẫu nhiên có đối chứng")
    assert std["design_code"] == "rct"
    assert "CONSORT" in std["primary"]


# ════════════════════════════════════════════════════════════════════════════
# 9. BÁO CÁO CHẤT LƯỢNG GHI RA ĐƯỢC
# ════════════════════════════════════════════════════════════════════════════

def test_write_quality_report_sinh_ca_json_va_markdown(tmp_path):
    report = G0Q.evaluate_g0_quality(
        checkpoint=_checkpoint(), meta={}, artifact_text=_artifact_text())
    md = G0Q.write_quality_report("S", tmp_path, report)
    assert md.exists() and (tmp_path / "G0_QUALITY_REPORT.json").exists()
    text = md.read_text(encoding="utf-8")
    assert "Cần bác sĩ kiểm chứng" in text
    assert "Giới hạn phán định" in text
    assert "G0-AUTO-00" in text and "G0-HUMAN-01" in text
    data = json.loads((tmp_path / "G0_QUALITY_REPORT.json").read_text(encoding="utf-8"))
    assert data["contract_version"] == G0Q.QUALITY_CONTRACT_VERSION
