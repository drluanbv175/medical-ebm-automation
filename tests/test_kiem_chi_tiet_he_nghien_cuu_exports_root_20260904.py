"""Hồi quy 2 phát hiện HIGH của Workflow đối kháng đa-agent vòng 2 (2026-09-03/04)
trong tools/kiem_chi_tiet_he_nghien_cuu.py — --exports-root (cờ CLI tự khai "cho
kiểm thử") bị BỎ QUA ở hai chỗ, khiến công cụ âm thầm đọc exports/<study> THẬT của
repo thay vì thư mục đang được kiểm:

  #1 G6 chấm sống (trục ②) — `_cham_song()` chỉ truyền `out_dir` cho hàm chấm nếu
     tham số đó có trong signature của evaluate_study(). Trước bản vá,
     `g6_quality_gate.evaluate_study(study, write=True)` KHÔNG có tham số out_dir
     (hardcode `EXPORTS = HERE.parent / "exports"` ở mức module) — nên G6 là cổng
     DUY NHẤT (11 cổng) luôn đọc exports/<study> thật bất kể --exports-root, kể cả
     khi track ③ (đọc artifact qua out_dir đúng) đồng thời báo "5 luật liêm chính
     sạch" cho CHÍNH file mà track ② nói "thiếu, không có gì để đối chiếu".

  #2 Trục ⑤ (điểm dừng người — sổ cái ký) và phần đối chiếu ledger trong ② của
     G4/G5/G8/G9/G10 — `da_ky()` và nhánh kwarg `repo_root` trong `_cham_song()`
     đều hardcode `repo_root=BASE` (repo THẬT), dù `art`/`out_dir` đã đúng dùng
     --exports-root. `gate_contract.ledger_approved()` tính
     `repo_root/exports/study/approval_ledger.json` — nên một sổ cái đã ký THẬT
     nằm cạnh out_dir đang kiểm bị báo "chưa ai duyệt" vì công cụ đọc nhầm sổ cái
     ở BASE/exports/<study> (không tồn tại cho đề tài fixture).

Nguyên tắc viết test: KIỂM HÀNH VI bằng cách dựng fixture thật (kể cả chữ ký HMAC
thật qua g5_test_helpers) và gọi thẳng hàm, không grep chuỗi trong mã nguồn.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
for _p in (str(REPO_ROOT), str(TOOLS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import g6_quality_gate as G6Q  # noqa: E402
import gate_contract as GC  # noqa: E402
import kiem_chi_tiet_he_nghien_cuu as K  # noqa: E402

from tests.g5_test_helpers import append_signed_approval, configure_test_signing_key  # noqa: E402

_STUDY_G6 = "PYTEST-KCT-G6-EXPORTSROOT-20260904"
_STUDY_G4 = "PYTEST-KCT-G4-LEDGER-EXPORTSROOT-20260904"


# ════════════════════════════════════════════════════════════════════════════
# #1 HIGH — G6 chấm sống bỏ qua out_dir
# ════════════════════════════════════════════════════════════════════════════

def _g6_fixture(out_dir: Path, study: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "G6_checkpoint.json").write_text(
        '{"gate": "G6", "study": "%s", "guardrail": {"passed": true}}' % study,
        encoding="utf-8", newline="\n",
    )
    (out_dir / f"G6_A7_ANALYSIS_SCRIPTS_{study}.md").write_text(
        "# G6 Analysis Scripts\n### §7 HARKing check\nset.seed(2026)\nalpha <- 0.05\n",
        encoding="utf-8", newline="\n",
    )
    (out_dir / f"G4_A5_SAP_FINAL_{study}.md").write_text(
        "# SAP\n### §12 alpha=0.05, N=100, seed=2026\n", encoding="utf-8", newline="\n",
    )


def test_g6_evaluate_study_accepts_out_dir_param():
    """evaluate_study() giờ có tham số out_dir — điều kiện tiên quyết để
    _cham_song()'s kwarg-injection (`if "out_dir" in params`) bắt được nó."""
    import inspect
    params = inspect.signature(G6Q.evaluate_study).parameters
    assert "out_dir" in params, "G6Q.evaluate_study thiếu tham số out_dir"


def test_g6_evaluate_study_reads_custom_out_dir_not_real_exports(tmp_path):
    """★★ Ca chính của phát hiện #1: fixture CHỈ tồn tại ở out_dir tùy biến (KHÔNG
    có trong exports/ thật của repo). Trước bản vá, G6-AUTO-00 báo thiếu file dù
    file có thật — vì evaluate_study() luôn đọc EXPORTS/study (repo thật)."""
    custom_dir = tmp_path / "exports" / _STUDY_G6
    _g6_fixture(custom_dir, _STUDY_G6)
    rep = G6Q.evaluate_study(_STUDY_G6, out_dir=custom_dir, write=False)
    row = next(c for c in rep["checks"] if c["id"] == "G6-AUTO-00")
    assert row["pass"] is True, row["detail"]
    assert "thiếu" not in row["detail"].lower()


def test_g6_evaluate_study_without_out_dir_falls_back_to_real_exports(monkeypatch, tmp_path):
    """Đối chứng: KHÔNG truyền out_dir vẫn giữ hành vi cũ (fallback EXPORTS/study)
    — không phá vỡ run_g6_auto.py/main() vốn gọi evaluate_study(study) trần."""
    fake_exports = tmp_path / "exports"
    fake_exports.mkdir()
    monkeypatch.setattr(G6Q, "EXPORTS", fake_exports)
    _g6_fixture(fake_exports / _STUDY_G6, _STUDY_G6)
    rep = G6Q.evaluate_study(_STUDY_G6, write=False)  # không truyền out_dir
    row = next(c for c in rep["checks"] if c["id"] == "G6-AUTO-00")
    assert row["pass"] is True, row["detail"]


def test_kiem_chi_tiet_cham_song_g6_consistent_with_track_3(tmp_path):
    """Chạy TRỌN _cham_song() (đường công cụ kiểm thật đi) trên out_dir tùy biến
    — track ② phải KHÔNG còn báo 'thiếu G6_A7_ANALYSIS_SCRIPTS..., G4_A5_SAP_
    FINAL..., G6_checkpoint.json' khi ba file đó THẬT SỰ có mặt trong out_dir."""
    custom_dir = tmp_path / "exports" / _STUDY_G6
    _g6_fixture(custom_dir, _STUDY_G6)
    rep, ghi_chu = K._cham_song("G6", _STUDY_G6, custom_dir)
    assert rep is not None, ghi_chu
    row = next(c for c in rep["checks"] if c["id"] == "G6-AUTO-00")
    assert row["pass"] is True, row["detail"]


# ════════════════════════════════════════════════════════════════════════════
# #2 HIGH — trục ⑤ (da_ky) và repo_root trong _cham_song hardcode BASE
# ════════════════════════════════════════════════════════════════════════════

def test_cham_song_injects_repo_root_derived_from_out_dir(monkeypatch, tmp_path):
    """kw['repo_root'] không còn là BASE (hằng số module, repo THẬT) mà suy từ
    out_dir — kiểm bằng cách chặn evaluate_study của G9 (có tham số repo_root) và
    đọc giá trị thật sự được truyền vào."""
    import g9_quality_gate as G9Q

    captured = {}

    def _fake_evaluate_study(study, out_dir, *, repo_root=None, write=True):
        captured["repo_root"] = repo_root
        return {"status": "BLOCKED", "automatic_criteria": []}

    monkeypatch.setattr(G9Q, "evaluate_study", _fake_evaluate_study)
    custom_out_dir = tmp_path / "exports" / "SOME-STUDY"
    custom_out_dir.mkdir(parents=True)
    K._cham_song("G9", "SOME-STUDY", custom_out_dir)
    assert captured["repo_root"] == custom_out_dir.parent.parent
    assert captured["repo_root"] != K.BASE


def test_da_ky_reads_ledger_signed_at_custom_exports_root(monkeypatch, tmp_path):
    """★★ Ca chính của phát hiện #2: sổ cái đã ký THẬT (chữ ký HMAC hợp lệ, đúng
    con dấu) nằm cạnh out_dir trong MỘT repo fixture — không phải BASE thật. Trước
    bản vá, da_ky() báo 'chưa ai duyệt' vì đọc nhầm BASE/exports/<study>."""
    configure_test_signing_key(tmp_path, monkeypatch)
    fixture_repo = tmp_path / "fixture_repo"
    out_dir = fixture_repo / "exports" / _STUDY_G4
    out_dir.mkdir(parents=True)
    artifact = out_dir / f"G4_A5_SAP_FINAL_{_STUDY_G4}.md"
    artifact.write_text("# SAP\n### §12 alpha=0.05\n", encoding="utf-8", newline="\n")

    append_signed_approval(
        _STUDY_G4, artifact, "G4", "STATISTICIAN", repo_root=fixture_repo,
    )

    # Đối chứng: repo_root=BASE (hành vi CŨ) không thấy chữ ký này — xác nhận
    # ledger THẬT SỰ nằm ở fixture_repo, không phải trùng lặp ngẫu nhiên ở BASE.
    assert GC.ledger_approved("G4", _STUDY_G4, artifact, repo_root=K.BASE) is False

    da_ky_ket_qua, ly_do = K.da_ky("G4", _STUDY_G4, out_dir)
    assert da_ky_ket_qua is True, ly_do


def test_da_ky_still_reports_unsigned_when_no_ledger(tmp_path):
    """Đối chứng: đề tài fixture KHÔNG có sổ cái vẫn đúng báo 'chưa ai duyệt' —
    bản vá không được biến mọi đề tài thành 'đã ký' oan."""
    out_dir = tmp_path / "exports" / "KHONG-CO-SO-CAI"
    out_dir.mkdir(parents=True)
    artifact = out_dir / "G4_A5_SAP_FINAL_KHONG-CO-SO-CAI.md"
    artifact.write_text("# SAP\n", encoding="utf-8", newline="\n")
    da_ky_ket_qua, ly_do = K.da_ky("G4", "KHONG-CO-SO-CAI", out_dir)
    assert da_ky_ket_qua is False
    assert ly_do is None or "chưa" in ly_do.lower()
