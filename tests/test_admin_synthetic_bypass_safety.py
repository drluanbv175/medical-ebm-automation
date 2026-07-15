"""Test đối kháng cho cơ chế "admin phê duyệt toàn quyền CHỈ dữ liệu tổng hợp/
thử nghiệm" (2026-07-15, theo yêu cầu bác sĩ — xem docstring tools/
mark_study_synthetic.py + tools/approve_gate_synthetic_admin.py).

Bối cảnh: bác sĩ muốn có quyền tự duyệt MỌI cổng (kể cả G2/IRB và G8/phản biện
độc lập — 2 cổng mà tools/approve_gate.py CỐ Ý không cho PI tự ký) để kiểm thử
cơ chế tự động hóa. Sau khi hỏi rõ, phạm vi được giới hạn: CHỈ áp dụng cho đề
tài tổng hợp/thử nghiệm, KHÔNG BAO GIỜ đề tài người thật. File này khóa lại
ĐÚNG ranh giới đó bằng test đối kháng — không chỉ test "đường thành công" mà
còn cố tình thử MỌI cách né tránh có thể nghĩ ra:
  T1  gate_contract.REAL_STUDY_DENYLIST chứa đúng đề tài thật đã biết (regression
      guard — nếu ai đó lỡ xóa khỏi danh sách, test này đỏ ngay)
  T2  is_real_study_denylisted() không né được bằng biến thể hoa/thường/khoảng trắng
  T3  approve_gate_synthetic_admin.py từ chối đề tài CHƯA được đánh dấu synthetic_test
  T4  approve_gate_synthetic_admin.py từ chối đề tài THẬT dù --i-confirm-... được đưa ra
  T5  approve_gate_synthetic_admin.py từ chối đề tài THẬT NGAY CẢ KHI study_meta.json
      của nó bị ép study_kind=synthetic_test bằng tay (mô phỏng nhầm lẫn/tấn công)
      — đây là bài test QUAN TRỌNG NHẤT: chứng minh denylist là lớp phòng thủ ĐỘC
      LẬP với marker, không phải chỉ kiểm tra lại cùng 1 điều kiện.
  T6  mark_study_synthetic.py từ chối đề tài THẬT dù --i-confirm-... được đưa ra
  T7  mark_study_synthetic.py từ chối khi thiếu cờ xác nhận
  T8  mark_study_synthetic.py từ chối đề tài đã có dấu hiệu tiến độ thật
      (irb_approved=true) trong study_meta.json
  T9  mark_study_synthetic.py từ chối đề tài đã có phê duyệt ledger THẬT
      (is_synthetic=false) từ trước
  T10 Đường THÀNH CÔNG đầy đủ: mark → approve-all → gate_contract.ledger_approved()
      thật trả True cho cả 4 cổng G2/G4/G8/G9 trên đề tài ĐÃ đánh dấu đúng
  T11 Mọi bản ghi ghi bởi admin-bypass mang tiền tố [ADMIN-SYNTHETIC-BYPASS] trong
      scope — không thể nhầm với phê duyệt người thật khi đọc lại ledger
  T12 study_meta.json THẬT của hai-long-benh-nhan-C1a-BVQY175 (nếu tồn tại trên máy
      chạy test) không có study_kind=synthetic_test — cảnh báo sớm nếu ai đó lỡ đặt
      nhầm field này lên đúng thư mục thật (bỏ qua nếu thư mục không tồn tại, vì đây
      là dữ liệu cục bộ của bác sĩ, không phải fixture của test)
  T13-T15 HỒI QUY lỗ hổng THẬT tự tìm ra khi kiểm định đối kháng bản vá đầu tiên:
      denylist so khớp CHUỖI --study THÔ, nhưng thao tác filesystem thật lại dùng
      đường dẫn đã CHUẨN HÓA (Path resolve "."/".."/dấu "/" cuối, và THEO SYMLINK) —
      "--study ./hai-long-benh-nhan-C1a-BVQY175" hay "hai-long-benh-nhan-C1a-BVQY175/"
      trỏ ĐÚNG thư mục thật trên đĩa nhưng KHÔNG khớp so sánh chuỗi tuyệt đối, vượt
      qua được kiểm tra denylist phiên bản đầu. Vá bằng cách kiểm denylist trên
      study_dir.resolve().name (tên SAU KHI chuẩn hóa/theo symlink) ở CẢ 2 tool.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
PYTHON = sys.executable
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import gate_contract as GC  # noqa: E402

REAL_STUDY = "hai-long-benh-nhan-C1a-BVQY175"


def _rmtree_retry(d: Path, attempts: int = 5, delay_s: float = 0.2) -> None:
    for _ in range(attempts):
        if not d.exists():
            return
        shutil.rmtree(d, ignore_errors=True)
        if not d.exists():
            return
        time.sleep(delay_s)


def _study_dir(name: str) -> Path:
    d = REPO_ROOT / "exports" / name
    _rmtree_retry(d)
    d.mkdir(parents=True, exist_ok=True)
    return d


def _configure_test_signing_key(tmp_path: Path, monkeypatch) -> None:
    key_path = tmp_path / "gate_approval_key"
    key_path.write_text("pytest-admin-bypass-key", encoding="utf-8")
    monkeypatch.setenv("EBM_GATE_KEY_PATH", str(key_path))


def _run_mark(study: str, *extra_args: str) -> subprocess.CompletedProcess:
    args = [PYTHON, str(TOOLS_DIR / "mark_study_synthetic.py"), "--study", study, *extra_args]
    return subprocess.run(args, cwd=REPO_ROOT, capture_output=True, text=True, timeout=30)


def _run_admin_approve(study: str, *extra_args: str) -> subprocess.CompletedProcess:
    args = [PYTHON, str(TOOLS_DIR / "approve_gate_synthetic_admin.py"), "--study", study, *extra_args]
    return subprocess.run(args, cwd=REPO_ROOT, capture_output=True, text=True, timeout=30)


# ── T1/T2 — bất biến denylist ──────────────────────────────────────────────

def test_real_study_denylist_contains_known_real_study():
    """T1 — regression guard: nếu ai đó lỡ xóa đề tài thật khỏi denylist khi sửa
    gate_contract.py, test này phải đỏ NGAY, không im lặng lệch."""
    assert REAL_STUDY in GC.REAL_STUDY_DENYLIST
    assert GC.is_real_study_denylisted(REAL_STUDY) is True


def test_real_study_denylist_not_evadable_by_case_or_whitespace():
    """T2 — is_real_study_denylisted() phải bắt được biến thể hoa/thường/khoảng
    trắng, không chỉ so khớp chuỗi tuyệt đối."""
    assert GC.is_real_study_denylisted(REAL_STUDY.upper()) is True
    assert GC.is_real_study_denylisted(REAL_STUDY.lower()) is True
    assert GC.is_real_study_denylisted(f"  {REAL_STUDY}  ") is True
    assert GC.is_real_study_denylisted("mot-de-tai-tong-hop-nao-do") is False


# ── T3-T5 — approve_gate_synthetic_admin.py từ chối đúng chỗ ────────────────

def test_admin_approve_refuses_study_without_synthetic_marker():
    """T3."""
    study = "PYTEST-ADMIN-BYPASS-T3"
    d = _study_dir(study)
    try:
        (d / "study_meta.json").write_text(json.dumps({"title": "demo"}), encoding="utf-8")
        res = _run_admin_approve(study, "--i-confirm-synthetic-admin-bypass")
        assert res.returncode != 0
        assert "study_kind=synthetic_test" in res.stdout
        assert not (d / "approval_ledger.json").exists()
    finally:
        _rmtree_retry(d)


def _refused_real_study_message(stdout: str) -> bool:
    """Đề tài thật bị từ chối HỢP LỆ theo 1 trong 2 cách, tùy máy chạy test có thư
    mục thật hay không (exports/ gitignore nên CI thường KHÔNG có): (a) denylist bắt
    khi thư mục tồn tại, hoặc (b) 'không thấy thư mục' khi chưa tồn tại. CẢ HAI đều
    là refusal an toàn — không bao giờ tạo/xóa thư mục tên thật trong test."""
    return ("REAL_STUDY_DENYLIST" in stdout
            or "Không thấy thư mục" in stdout
            or "không giải được" in stdout)


def test_admin_approve_refuses_real_study_even_with_confirm_flag():
    """T4 — dùng ĐÚNG tên đề tài thật; KHÔNG tạo/xóa thư mục tên thật. Refusal hợp
    lệ theo denylist (nếu thư mục tồn tại) hoặc not-found (nếu không) — xem
    _refused_real_study_message."""
    res = _run_admin_approve(REAL_STUDY, "--i-confirm-synthetic-admin-bypass")
    assert res.returncode != 0
    assert _refused_real_study_message(res.stdout)


def test_admin_approve_denylist_check_is_independent_of_marker():
    """T5 — chứng minh 2 lớp phòng thủ ĐỘC LẬP: denylist chặn TÊN đề tài thật bất
    kể study_meta.json có ép tay study_kind=synthetic_test hay không. KHÔNG tạo/xóa
    thư mục tên thật (nguy hiểm trên cây OneDrive dùng chung) — thay vào đó kiểm 2
    tính chất cấu trúc bảo đảm điều đó:
      (a) is_real_study_denylisted() là hàm THUẦN của TÊN, không đọc file/marker nào;
      (b) resolve_synthetic_study_dir() (chốt mà CẢ 2 tool gọi ĐẦU TIÊN, trước khi
          đọc marker) từ chối denylisted name — nên marker ép tay không bao giờ tới
          lượt được xét.
    Cộng với T4/T6 (CLI thật từ chối tên thật) và T16 (KKB trong denylist), đủ khóa
    bất biến mà không cần dựng thư mục tên thật."""
    # (a) hàm thuần — cùng một input tên, không phụ thuộc bất kỳ nội dung file nào.
    assert GC.is_real_study_denylisted(REAL_STUDY) is True
    assert GC.is_real_study_denylisted("KKB-HAI-LONG-2026") is True
    # (b) chốt dùng chung từ chối denylisted name NGAY cả khi thư mục tồn tại thật:
    # nếu thư mục thật có trên máy này, resolve_synthetic_study_dir phải trả lỗi
    # denylist (không phải None-thành-công); nếu không tồn tại, trả lỗi not-found —
    # cả hai đều là "không cho đi tiếp", không bao giờ trả (real_dir, None).
    real_dir, err = GC.resolve_synthetic_study_dir(REAL_STUDY, REPO_ROOT)
    assert real_dir is None and err is not None
    if (REPO_ROOT / "exports" / REAL_STUDY).exists():
        assert "REAL_STUDY_DENYLIST" in err


# ── T6-T9 — mark_study_synthetic.py từ chối đúng chỗ ────────────────────────

def test_mark_refuses_real_study_even_with_confirm_flag():
    """T6 — không tạo/xóa thư mục tên thật; refusal hợp lệ theo denylist hoặc not-found."""
    res = _run_mark(REAL_STUDY, "--i-confirm-this-is-synthetic-test-data-not-a-real-study")
    assert res.returncode != 0
    assert _refused_real_study_message(res.stdout)


def test_mark_refuses_without_confirm_flag():
    """T7."""
    study = "PYTEST-ADMIN-BYPASS-T7"
    d = _study_dir(study)
    try:
        res = _run_mark(study)
        assert res.returncode != 0
        assert "Thiếu cờ xác nhận" in res.stdout
        meta = json.loads((d / "study_meta.json").read_text(encoding="utf-8")) \
            if (d / "study_meta.json").exists() else {}
        assert meta.get("study_kind") != "synthetic_test"
    finally:
        _rmtree_retry(d)


def test_mark_refuses_study_with_real_progress_flags_already_set():
    """T8."""
    study = "PYTEST-ADMIN-BYPASS-T8"
    d = _study_dir(study)
    try:
        (d / "study_meta.json").write_text(
            json.dumps({"title": "demo", "irb_approved": True}), encoding="utf-8")
        res = _run_mark(study, "--i-confirm-this-is-synthetic-test-data-not-a-real-study")
        assert res.returncode != 0
        assert "dấu hiệu tiến độ THẬT" in res.stdout
        meta = json.loads((d / "study_meta.json").read_text(encoding="utf-8"))
        assert meta.get("study_kind") != "synthetic_test"
    finally:
        _rmtree_retry(d)


def test_mark_refuses_study_with_real_ledger_approval_already_present(tmp_path, monkeypatch):
    """T9."""
    study = "PYTEST-ADMIN-BYPASS-T9"
    d = _study_dir(study)
    try:
        _configure_test_signing_key(tmp_path, monkeypatch)
        (d / "study_meta.json").write_text(json.dumps({"title": "demo"}), encoding="utf-8")
        evidence = "ETHICS PACKAGE THẬT — đã duyệt (giả lập test)"
        import hashlib
        evidence_hash = hashlib.sha256(evidence.encode()).hexdigest()
        record = {
            "approval_id": "test-t9-001", "gate_id": "G2",
            "reviewer_role": "IRB_ETHICS_COMMITTEE", "reviewer_identity_reference": "REF-T9",
            "decision": "APPROVED", "scope": "test", "evidence_hash": evidence_hash,
            "timestamp_utc": "2026-07-15T00:00:00+00:00", "supersedes": None,
            "artifact_creator_agent": None, "reviewer_agent": None,
            "is_synthetic": False, "approver_signature": None,
        }
        (d / "approval_ledger.json").write_text(json.dumps([record]), encoding="utf-8")
        res = _run_mark(study, "--i-confirm-this-is-synthetic-test-data-not-a-real-study")
        assert res.returncode != 0
        assert "phê duyệt THẬT" in res.stdout
    finally:
        _rmtree_retry(d)


# ── T10-T11 — đường thành công đầy đủ, đúng phạm vi đã xác nhận ─────────────

def test_full_success_path_marks_and_approves_all_four_gates(tmp_path, monkeypatch):
    """T10 — end-to-end thật: mark → approve-all → gate_contract.ledger_approved()
    (hàm THẬT dùng bởi run_g9_auto.py) phải trả True cho cả 4 cổng."""
    study = "PYTEST-ADMIN-BYPASS-T10"
    d = _study_dir(study)
    try:
        _configure_test_signing_key(tmp_path, monkeypatch)
        (d / "study_meta.json").write_text(json.dumps({"title": "demo tổng hợp"}), encoding="utf-8")

        mark_res = _run_mark(study, "--i-confirm-this-is-synthetic-test-data-not-a-real-study")
        assert mark_res.returncode == 0
        meta = json.loads((d / "study_meta.json").read_text(encoding="utf-8"))
        assert meta["study_kind"] == "synthetic_test"

        approve_res = _run_admin_approve(study, "--i-confirm-synthetic-admin-bypass")
        assert approve_res.returncode == 0
        assert "4/4 cổng" in approve_res.stdout

        for gate in ("G2", "G4", "G8", "G9"):
            artifact = d / "_admin_synthetic_bypass" / f"{gate}_ADMIN_BYPASS_EVIDENCE.md"
            assert artifact.exists()
            assert GC.ledger_approved(gate, study, artifact, repo_root=REPO_ROOT) is True
    finally:
        _rmtree_retry(d)


def test_admin_bypass_records_carry_distinguishing_marker(tmp_path, monkeypatch):
    """T11 — mọi bản ghi phải mang tiền tố [ADMIN-SYNTHETIC-BYPASS] trong scope,
    không thể nhầm với phê duyệt người thật khi audit lại ledger sau này."""
    study = "PYTEST-ADMIN-BYPASS-T11"
    d = _study_dir(study)
    try:
        _configure_test_signing_key(tmp_path, monkeypatch)
        (d / "study_meta.json").write_text(json.dumps({"title": "demo"}), encoding="utf-8")
        assert _run_mark(study, "--i-confirm-this-is-synthetic-test-data-not-a-real-study").returncode == 0
        assert _run_admin_approve(study, "--gates", "G2",
                                  "--i-confirm-synthetic-admin-bypass").returncode == 0
        records = json.loads((d / "approval_ledger.json").read_text(encoding="utf-8"))
        assert len(records) == 1
        assert records[0]["scope"].startswith("[ADMIN-SYNTHETIC-BYPASS]")
        assert records[0]["reviewer_identity_reference"] == "ADMIN_SYNTHETIC_BYPASS_TOOL"
        assert records[0]["is_synthetic"] is False  # cố ý False — xem docstring tool
    finally:
        _rmtree_retry(d)


# ── T12 — cảnh báo sớm nếu study_meta.json thật trên máy bị đặt nhầm field ──

def test_real_study_local_metadata_never_marked_synthetic_if_present():
    """T12 — bỏ qua nếu thư mục đề tài thật chưa tồn tại trên máy chạy test (đây
    là dữ liệu cục bộ, không phải fixture); nếu CÓ tồn tại, study_kind tuyệt đối
    không được là 'synthetic_test'."""
    meta_path = REPO_ROOT / "exports" / REAL_STUDY / "study_meta.json"
    if not meta_path.exists():
        return
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    assert meta.get("study_kind") != "synthetic_test", (
        f"study_meta.json của đề tài THẬT '{REAL_STUDY}' bị đánh dấu synthetic_test — "
        "kiểm tra lại ngay, đây có thể là dấu hiệu nhầm lẫn/thao tác sai nghiêm trọng."
    )


# ── T13-T15 — hồi quy: chuẩn hóa đường dẫn không được né tránh denylist ─────

def test_mark_refuses_dot_slash_prefix_variant_of_real_study():
    """T13 — "./<tên thật>" phải bị chặn dù chuỗi không khớp so sánh tuyệt đối."""
    res = _run_mark(f"./{REAL_STUDY}", "--i-confirm-this-is-synthetic-test-data-not-a-real-study")
    assert res.returncode != 0
    assert _refused_real_study_message(res.stdout)


def test_admin_approve_refuses_trailing_slash_variant_of_real_study():
    """T14 — dấu "/" cuối phải bị chặn."""
    res = _run_admin_approve(f"{REAL_STUDY}/", "--i-confirm-synthetic-admin-bypass")
    assert res.returncode != 0
    assert _refused_real_study_message(res.stdout)


def test_mark_refuses_dot_dot_traversal_variant_of_real_study():
    """T15 — "<tên>/../<tên>" (đi vòng qua .. rồi quay lại) phải bị chặn."""
    res = _run_mark(f"{REAL_STUDY}/../{REAL_STUDY}",
                    "--i-confirm-this-is-synthetic-test-data-not-a-real-study")
    assert res.returncode != 0
    assert _refused_real_study_message(res.stdout)


# ── T16-T22 — HỒI QUY các lỗ hổng red-team đối kháng tái hiện được 2026-07-15 ─

def test_kkb_alias_is_denylisted():
    """T16 — KKB-HAI-LONG-2026 (bí danh cùng đề tài thật) phải trong denylist."""
    assert "KKB-HAI-LONG-2026" in GC.REAL_STUDY_DENYLIST
    assert GC.is_real_study_denylisted("KKB-HAI-LONG-2026") is True


def test_mark_refuses_absolute_path_escaping_exports(tmp_path):
    """T17 — thoát sandbox: --study đường dẫn TUYỆT ĐỐI (pathlib bỏ vế trái) phải
    bị containment chặn (thư mục giải ra không phải con trực tiếp của exports/)."""
    outside = tmp_path / "decoy-outside-exports"
    outside.mkdir()
    (outside / "study_meta.json").write_text(json.dumps({"title": "decoy"}), encoding="utf-8")
    res = _run_mark(str(outside), "--i-confirm-this-is-synthetic-test-data-not-a-real-study")
    assert res.returncode != 0
    assert "con TRỰC TIẾP của" in res.stdout
    assert not (outside / "study_meta.json").read_text(encoding="utf-8").__contains__("synthetic_test")


def test_admin_approve_refuses_absolute_path_escaping_exports(tmp_path):
    """T17b — cùng lỗ hổng, phía approve tool."""
    outside = tmp_path / "decoy-outside-exports2"
    outside.mkdir()
    (outside / "study_meta.json").write_text(
        json.dumps({"title": "decoy", "study_kind": "synthetic_test"}), encoding="utf-8")
    res = _run_admin_approve(str(outside), "--i-confirm-synthetic-admin-bypass")
    assert res.returncode != 0
    assert "con TRỰC TIẾP của" in res.stdout
    assert not (outside / "approval_ledger.json").exists()


def test_mark_refuses_empty_study_and_does_not_pollute_exports_root():
    """T18 — --study "" khiến exports/"" == exports/ gốc: phải bị chặn, và tuyệt
    đối KHÔNG tạo exports/study_meta.json (bug red-team phải tự dọn)."""
    exports_root_meta = REPO_ROOT / "exports" / "study_meta.json"
    existed_before = exports_root_meta.exists()
    res = _run_mark("", "--i-confirm-this-is-synthetic-test-data-not-a-real-study")
    assert res.returncode != 0
    assert "rỗng" in res.stdout or "con TRỰC TIẾP" in res.stdout
    if not existed_before:
        assert not exports_root_meta.exists(), (
            "mark_study_synthetic.py với --study rỗng đã ghi study_meta.json vào exports/ gốc")


def test_mark_refuses_symlink_escaping_exports(tmp_path):
    """T19 — symlink dưới exports/ trỏ RA NGOÀI exports/ phải bị containment chặn
    (resolve theo symlink → parent không phải exports/)."""
    outside = tmp_path / "symlink-target-outside"
    outside.mkdir()
    (outside / "study_meta.json").write_text(json.dumps({"title": "decoy"}), encoding="utf-8")
    link = REPO_ROOT / "exports" / "PYTEST-ADMIN-BYPASS-T19-LINK"
    if link.exists() or link.is_symlink():
        link.unlink()
    link.symlink_to(outside)
    try:
        res = _run_mark("PYTEST-ADMIN-BYPASS-T19-LINK",
                        "--i-confirm-this-is-synthetic-test-data-not-a-real-study")
        assert res.returncode != 0
        assert "con TRỰC TIẾP của" in res.stdout
        assert "synthetic_test" not in (outside / "study_meta.json").read_text(encoding="utf-8")
    finally:
        if link.exists() or link.is_symlink():
            link.unlink()


def test_mark_refuses_study_carrying_real_institution_org_lines():
    """T20 — heuristic bắt bí danh: study có org_lines (tên viện thật) không được
    gắn synthetic_test dù tên thư mục chưa vào denylist."""
    study = "PYTEST-ADMIN-BYPASS-T20"
    d = _study_dir(study)
    try:
        (d / "study_meta.json").write_text(json.dumps({
            "title": "Bí danh giả lập mang danh viện thật",
            "org_lines": ["BỆNH VIỆN QUÂN Y 175", "TRUNG TÂM KHÁM BỆNH VÀ ĐIỀU TRỊ THEO YÊU CẦU C1"],
        }, ensure_ascii=False), encoding="utf-8")
        res = _run_mark(study, "--i-confirm-this-is-synthetic-test-data-not-a-real-study")
        assert res.returncode != 0
        assert "CƠ SỞ Y TẾ THẬT" in res.stdout
        meta = json.loads((d / "study_meta.json").read_text(encoding="utf-8"))
        assert meta.get("study_kind") != "synthetic_test"
    finally:
        _rmtree_retry(d)


def test_admin_approve_refuses_artifact_outside_study_dir(tmp_path, monkeypatch):
    """T21 — --artifacts trỏ ra ngoài thư mục đề tài (vd file của đề tài khác) phải
    bị từ chối (defense-in-depth, tránh hash tài liệu đề tài khác vào ledger synthetic)."""
    study = "PYTEST-ADMIN-BYPASS-T21"
    d = _study_dir(study)
    try:
        _configure_test_signing_key(tmp_path, monkeypatch)
        (d / "study_meta.json").write_text(json.dumps({"title": "demo"}), encoding="utf-8")
        assert _run_mark(study, "--i-confirm-this-is-synthetic-test-data-not-a-real-study").returncode == 0
        outside_file = tmp_path / "other_study_artifact.md"
        outside_file.write_text("tài liệu đề tài KHÁC", encoding="utf-8")
        amap = tmp_path / "amap.json"
        amap.write_text(json.dumps({"G2": str(outside_file)}), encoding="utf-8")
        res = _run_admin_approve(study, "--gates", "G2", "--artifacts", str(amap),
                                 "--i-confirm-synthetic-admin-bypass")
        assert res.returncode != 0
        assert "nằm ngoài" in res.stdout
        assert not (d / "approval_ledger.json").exists()
    finally:
        _rmtree_retry(d)
