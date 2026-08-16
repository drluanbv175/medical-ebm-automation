"""Hồi quy (audit vòng 3, 2026-07-19, D1_qual_mixed_gate_coverage — NGHIÊM TRỌNG):
pipeline G0-G10 hoàn toàn KHÔNG có nhánh nào cho thiết kế định tính/hỗn hợp —
infer_study_design() không bao giờ trả internal_code="qualitative" (mọi đề tài định
tính bị gán nhầm rct/diagnostic/descriptive), kéo theo G3 áp công thức power/effect
size (sai phương pháp luận — định tính dùng bão hòa dữ liệu), G4 hard-block SAP với
thông báo sai, G7 gán checklist STROBE/CONSORT thay COREQ/SRQR.

Đã vá:
- run_g1_auto.py: SPECIALIST_MODULE_KEYWORDS["qualitative"] thêm "trải nghiệm/ý
  nghĩa/rào cản" (đúng doctrine nghien-cuu-dinh-tinh.md); DESIGN_KEYWORD_HINTS +
  infer_study_design() thêm nhánh "qualitative" (đặt SỚM — trước "diagnosis" — vì
  marker paradigm mạnh hơn marker domain, vd "Ý nghĩa của chẩn đoán ung thư..." vẫn
  phải là định tính dù chứa chữ "chẩn đoán"); BIAS_CONTROLS["qualitative"] dùng khung
  trustworthiness (credibility/transferability/dependability/confirmability) thay vì
  bias định lượng.
- run_g3_auto.py: nhánh "qualitative" (N=0 có chủ đích, giải thích bão hòa dữ liệu).
  SỬA CẤU TRÚC sâu hơn: is_empty/needs_input trước đây KHÔNG phân biệt "N=0 vì thiếu
  effect size" (lỗi thật) với "N=0 CÓ CHỦ ĐÍCH vì thiết kế không dùng power" (sr_ma/
  prediction/qualitative — bug có sẵn từ 2026-07-06/07-17, không chỉ riêng
  qualitative) — G3 từng hard-block CẢ sr_ma với thông báo SAI "thiếu effect size".
  Nay: N_NOT_APPLICABLE_DESIGNS={"sr_ma","prediction","qualitative"} — thiếu
  --confirmed-n vẫn BLOCKED (giữ nguyên chủ đích "liêm chính > tiến độ" của 2 test
  cũ test_gate_prediction_design_coverage.py) nhưng thông báo ĐÚNG + hướng dẫn cụ thể
  (RIS/TSA, pmsampsize, bão hòa dữ liệu); có --confirmed-n → PASS dùng N đã chốt.
- run_g4_auto.py: đọc confirmed_n từ G3 checkpoint làm N hiệu lực cho 3 thiết kế
  N_NOT_APPLICABLE (trước đây --confirmed-n KHÔNG có tác dụng cho chúng).
- run_g7_auto.py: REPORTING_CHECKLISTS/CHECKLIST_ITEMS thêm "qualitative" (SRQR 2014,
  21 mục, tất cả auto_filled=False); flow_label không còn rơi nhầm "PRISMA flow
  diagram".
"""
from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
PYTHON = sys.executable

sys.path.insert(0, str(TOOLS_DIR))
import gate_contract as GC  # noqa: E402

EXIT_OK = GC.EXIT_OK
EXIT_BLOCKED = GC.EXIT_BLOCKED


def _load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, TOOLS_DIR / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


G1 = _load_module("g1_qual", "run_g1_auto.py")
G7 = _load_module("g7_qual", "run_g7_auto.py")


def _run(script: str, study: str, extra=None):
    args = [PYTHON, str(TOOLS_DIR / script), "--study", study]
    if extra:
        args += extra
    return subprocess.run(args, cwd=REPO_ROOT, capture_output=True, text=True, timeout=120)


def _load(study_dir: Path, gate: str) -> dict:
    return json.loads((study_dir / f"{gate}_checkpoint.json").read_text(encoding="utf-8"))


def _rmtree_retry(d: Path, attempts: int = 5, delay_s: float = 0.2) -> None:
    for _ in range(attempts):
        if not d.exists():
            return
        shutil.rmtree(d, ignore_errors=True)
        if not d.exists():
            return
        time.sleep(delay_s)


@pytest.fixture
def study_dir(request):
    name = f"PYTEST-QUAL-{request.node.name[-24:].replace('[', '').replace(']', '')}"
    d = REPO_ROOT / "exports" / name
    _rmtree_retry(d)
    d.mkdir(parents=True, exist_ok=True)
    try:
        yield d
    finally:
        _rmtree_retry(d)


def _mk_upstream(study_dir: Path):
    study_dir.mkdir(parents=True, exist_ok=True)
    (study_dir / "G0_checkpoint.json").write_text(json.dumps({
        "study": study_dir.name, "gate": "G0",
        "topic": "Tìm hiểu rào cản tuân thủ thuốc ở bệnh nhân mạn tính",
    }, ensure_ascii=False), encoding="utf-8", newline="\n")
    (study_dir / "G1_checkpoint.json").write_text(json.dumps({
        "study": study_dir.name, "gate": "G1",
        "design": {"internal_code": "qualitative", "primary": "Nghiên cứu Định tính (Qualitative Research)",
                   "reporting_standard": "COREQ (phỏng vấn/nhóm tiêu điểm) / SRQR (định tính nói chung)"},
    }, ensure_ascii=False), encoding="utf-8", newline="\n")


# ── G1: infer_study_design() — paradigm marker phải thắng domain marker ──────────

class TestG1QualitativeInference:
    def test_doctrine_example_phrase_maps_to_qualitative(self):
        """Đúng ví dụ mẫu nghien-cuu-dinh-tinh.md tự dùng."""
        r = G1.infer_study_design("treatment", {"n_sr": 0, "n_rct": 0, "research_gaps": []},
                                   "Tìm hiểu rào cản tuân thủ thuốc ở bệnh nhân mạn tính.")
        assert r["internal_code"] == "qualitative"
        assert r["reporting_standard"].startswith("COREQ")

    def test_paradigm_marker_beats_domain_keyword_diagnosis(self):
        """Hồi quy cụ thể: 'Ý nghĩa của chẩn đoán...' PHẢI là định tính dù chứa chữ
        'chẩn đoán' (domain keyword của nhánh 'diagnosis') — marker phương pháp luận
        'ý nghĩa' đặc hiệu hơn và phải thắng."""
        r = G1.infer_study_design("treatment", {"n_sr": 0, "n_rct": 0, "research_gaps": []},
                                   "Ý nghĩa của chẩn đoán ung thư đối với người bệnh trẻ tuổi.")
        assert r["internal_code"] == "qualitative"

    def test_trai_nghiem_keyword(self):
        r = G1.infer_study_design("treatment", {"n_sr": 0, "n_rct": 0, "research_gaps": []},
                                   "Trải nghiệm của bệnh nhân ĐTĐ2 khi tự quản lý bệnh tại nhà.")
        assert r["internal_code"] == "qualitative"

    def test_detect_specialist_modules_catches_doctrine_markers(self):
        for topic in ["rào cản tuân thủ thuốc", "trải nghiệm sống chung với bệnh",
                      "ý nghĩa của việc mắc bệnh mạn tính"]:
            assert "qualitative" in G1.detect_specialist_modules(topic), topic

    def test_bias_controls_use_trustworthiness_not_quantitative_bias(self):
        r = G1.infer_study_design("treatment", {"n_sr": 0, "n_rct": 0, "research_gaps": []},
                                   "Trải nghiệm của bệnh nhân về chăm sóc giảm nhẹ.")
        labels = [b[0] for b in r["bias_controls"]]
        assert any("Credibility" in label for label in labels)
        assert not any("Confounding" in label or "Selection bias" == label for label in labels)

    @pytest.mark.parametrize("topic,expected", [
        ("Hiệu quả metformin lên HbA1c ở bệnh nhân ĐTĐ2.", "rct"),
        ("Tổng quan hệ thống về statin và biến cố tim mạch.", "sr_ma"),
        ("Độ nhạy độ đặc hiệu của test nhanh chẩn đoán sốt xuất huyết.", "diagnostic"),
        ("Xây dựng mô hình tiên lượng nguy cơ tái nhập viện suy tim.", "prediction"),
        ("Tiên lượng tử vong ở bệnh nhân xơ gan mất bù.", "cohort"),
        ("Yếu tố nguy cơ ung thư phổi: nghiên cứu bệnh chứng.", "case_control"),
        ("Tỷ lệ hài lòng của bệnh nhân ngoại trú.", "cross_sectional"),
    ])
    def test_other_designs_not_overridden_by_qualitative_branch(self, topic, expected):
        """Đối chứng: thêm nhánh 'qualitative' KHÔNG được đè lên 6 thiết kế còn lại."""
        r = G1.infer_study_design("treatment", {"n_sr": 0, "n_rct": 0, "research_gaps": []}, topic)
        assert r["internal_code"] == expected, f"{topic!r} -> {r['internal_code']} (kỳ vọng {expected})"


# ── G3/G4: N=0 có chủ đích — BLOCKED đúng thông báo khi thiếu --confirmed-n, ─────
#          PASS khi đã chốt (đối xứng sr_ma/prediction) ──────────────────────────

class TestG3G4QualitativeSampleSize:
    def test_g3_no_confirmed_n_blocks_with_correct_message_not_missing_effect_size(self, study_dir):
        _mk_upstream(study_dir)
        res = _run("run_g3_auto.py", study_dir.name)
        assert res.returncode == EXIT_BLOCKED
        cp = _load(study_dir, "G3")
        msg = cp["needs_input"]["human_message"]
        assert "bão hòa dữ liệu" in msg or "bao hoa du lieu" in msg.lower() or "saturation" in msg.lower() or \
            "bão hòa" in msg
        assert "THIẾU effect size" not in msg, (
            "Hồi quy: thông báo phải KHÔNG nói 'thiếu effect size' cho qualitative "
            "— effect size không áp dụng cho thiết kế này"
        )
        assert "--confirmed-n" in cp["needs_input"]["remediation"]["command"]

    def test_g3_with_confirmed_n_passes(self, study_dir):
        _mk_upstream(study_dir)
        res = _run("run_g3_auto.py", study_dir.name, ["--confirmed-n", "20"])
        assert res.returncode == EXIT_OK
        cp = _load(study_dir, "G3")
        assert cp["core_value"]["is_empty"] is False
        assert cp["confirmed_n"] == 20

    def test_g4_with_confirmed_n_passes_and_shows_real_n(self, study_dir):
        _mk_upstream(study_dir)
        res3 = _run("run_g3_auto.py", study_dir.name, ["--confirmed-n", "20"])
        assert res3.returncode == EXIT_OK
        res4 = _run("run_g4_auto.py", study_dir.name)
        assert res4.returncode == EXIT_OK, res4.stdout[-1000:]
        artifact = (study_dir / f"G4_A5_SAP_FINAL_{study_dir.name}.md").read_text(encoding="utf-8")
        assert "N = 20" in artifact
        assert "N/A" not in artifact.split("PHẦN 3")[1][:500]

    def test_g4_without_confirmed_n_still_blocks(self, study_dir):
        """Đối chứng: G4 vẫn chặn đúng khi G3 cũng chưa có N (không nới lỏng cổng)."""
        _mk_upstream(study_dir)
        res3 = _run("run_g3_auto.py", study_dir.name)
        assert res3.returncode == EXIT_BLOCKED
        res4 = _run("run_g4_auto.py", study_dir.name)
        assert res4.returncode == EXIT_BLOCKED

    def test_g4_sap_uses_coreq_srqr_sections_not_quantitative_stats(self, study_dir):
        """Hồi quy (vòng lặp kiểm tra-hoàn thiện, 2026-07-20, audit đối kháng):
        trước khi vá, §5-§9 của SAP Final là văn bản cố định Multiple
        Imputation/Bonferroni/subgroup-interaction cho MỌI design_code kể cả
        "qualitative" — bác sĩ ký SAP Lock Certificate cho đề tài định tính sẽ
        vô tình xác nhận một kế hoạch thống kê định lượng vô nghĩa. G3 (bão
        hòa) và G7 (SRQR) đã có nhánh riêng từ 2026-07-19; G4 là gate cuối
        cùng còn thiếu, nay đã vá bằng khung COREQ/SRQR (mã hóa/bão hòa/chọn
        mẫu đa dạng/trustworthiness)."""
        _mk_upstream(study_dir)
        res3 = _run("run_g3_auto.py", study_dir.name, ["--confirmed-n", "20"])
        assert res3.returncode == EXIT_OK
        res4 = _run("run_g4_auto.py", study_dir.name)
        assert res4.returncode == EXIT_OK, res4.stdout[-1000:]
        artifact = (study_dir / f"G4_A5_SAP_FINAL_{study_dir.name}.md").read_text(encoding="utf-8")

        assert "Multiple Imputation" not in artifact
        assert "Bonferroni" not in artifact
        assert "stepwise" not in artifact.lower()
        assert "interaction term" not in artifact

        assert "TRUSTWORTHINESS" in artifact
        assert "Credibility" in artifact
        assert "BÃO HÒA DỮ LIỆU" in artifact
        assert "CHIẾN LƯỢC MÃ HÓA" in artifact
        assert "mã hóa chủ đề" in artifact.lower() or "thematic" in artifact.lower()


# ── G7: checklist SRQR (không fallback STROBE/cohort) ────────────────────────────

class TestG7QualitativeChecklist:
    def test_reporting_checklist_is_srqr_not_strobe(self):
        std, n_items = G7.REPORTING_CHECKLISTS["qualitative"]
        # SỬA 2026-07-30 (G7-F5): nhãn nay làm rõ SRQR là chuẩn ĐỊNH TÍNH NÓI
        # CHUNG (COREQ hẹp hơn — phỏng vấn/nhóm tiêu điểm) thay vì chỉ "SRQR
        # 2014" trần trụi — kiểm bằng startswith thay vì so khớp tuyệt đối.
        assert std.startswith("SRQR 2014")
        assert "STROBE" not in std and "CONSORT" not in std
        assert n_items == 21

    def test_checklist_items_full_21_and_all_manual(self):
        items = G7.CHECKLIST_ITEMS["qualitative"]
        assert len(items) == 21
        assert all(auto_filled is False for _, _, auto_filled in items), (
            "Mọi mục SRQR phải auto_filled=False — dữ liệu định tính (quote/chủ đề) "
            "chỉ tồn tại SAU khi thu thập thật, không được tự điền từ checkpoint"
        )

    def test_generate_checklist_header_has_srqr_not_strobe_or_consort(self):
        out = G7.generate_checklist("qualitative", "SRQR 2014", 21, "IRB-001", "N/A", 0, 0.05, 0.80)
        assert "SRQR" in out
        assert "STROBE" not in out
        assert "CONSORT" not in out

    def test_qualitative_does_not_fallback_to_cohort_checklist(self):
        """Hồi quy trực tiếp: trước bản vá, .get(design_code, .get('cohort')) rơi
        fallback vì 'qualitative' không có key riêng."""
        items = G7.CHECKLIST_ITEMS.get("qualitative", G7.CHECKLIST_ITEMS.get("cohort", []))
        cohort_items = G7.CHECKLIST_ITEMS["cohort"]
        assert items != cohort_items

    def test_render_checklist_block_does_not_false_flip_manual_items_to_auto(self):
        """Hồi quy G7-F3 (audit toàn diện G0-G10, 2026-07-30): trước bản vá,
        _render_checklist_block() ép is_auto=True cho bất kỳ mục nào có MÔ TẢ
        TĨNH tình cờ chứa từ khóa chung chung ("thiết kế", "irb"...), bất kể
        auto_filled thật của mục đó. Mục 9 của checklist SRQR (auto_filled=
        False — "Vấn đề đạo đức — chấp thuận IRB...") từng bị hiển thị nhầm
        thành "☑ Auto" chỉ vì mô tả chứa chữ "irb"/"đạo đức"; mục 1a của
        checklist STROBE cohort (auto_filled=False — nhắc tới "thiết kế
        cohort") cũng bị flip tương tự. Kiểm cả 2 design_code."""
        md_qual, auto_count_qual, _ = G7._render_checklist_block(
            G7.CHECKLIST_ITEMS["qualitative"], "SRQR 2014", 21
        )
        assert auto_count_qual == 0, (
            "Mọi mục SRQR có auto_filled=False — không mục nào được hiện ☑ Auto"
        )
        for line in md_qual.splitlines():
            if line.startswith("| 9 |"):
                assert "☐ [CẦN]" in line and "☑ Auto" not in line
                break
        else:
            raise AssertionError("Không tìm thấy dòng mục 9 trong bảng checklist")

        md_cohort, _auto_count_cohort, _ = G7._render_checklist_block(
            G7.CHECKLIST_ITEMS["cohort"], "STROBE 2007", 22
        )
        for line in md_cohort.splitlines():
            if line.startswith("| 1a |"):
                assert "☐ [CẦN]" in line and "☑ Auto" not in line
                break
        else:
            raise AssertionError("Không tìm thấy dòng mục 1a trong bảng checklist")
