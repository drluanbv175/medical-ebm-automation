"""Hồi quy (audit toàn diện G0-G10, 2026-07-29):

G10-01 (CRITICAL) — 4 nơi độc lập (g9_quality_gate.py::G9-AUTO-03,
g10_quality_gate.py::G10-AUTO-04, lock_analysis_dataset.py::
_upstream_approval_report, g5_quality_gate.py::G5-AUTO-05) từng kiểm "G4 đã
khóa" bằng ``_status_locked(g4.get("g4_status"))`` — một chuỗi mà
run_g4_auto.py KHÔNG BAO GIỜ ghi "LOCKED" vào (chỉ "PENDING"/"BLOCKED — ...").
Hệ quả: g4_ok vĩnh viễn False cho MỌI đề tài thật, dù chữ ký ledger G4 hợp lệ.
Vá bằng cách gọi thẳng gate_contract.g4_quality_contract_satisfied() (mirror
g5_ok/g9_ok đã đúng từ đầu).

G10-02 (CRITICAL, "tautology ngược") — build_front_note()/build_document_
control() trong run_g10_assemble.py từng nội suy trực tiếp chuỗi tag
"[CẦN ...]" NGOÀI NGỮ CẢNH (chú giải quy ước, không phải placeholder thật) vào
MỌI văn bản lắp ráp — khiến g10_quality_gate._documents_clean() (quét đúng
_PLACEHOLDER_RE) LUÔN thấy "còn placeholder" dù 100% dữ liệu đã điền đủ.
G10-AUTO-09 vì vậy không bao giờ PASS được qua pipeline thật.
"""

from __future__ import annotations

import inspect
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import g5_quality_gate as G5Q  # noqa: E402
import g9_quality_gate as G9Q  # noqa: E402
import g10_quality_gate as G10Q  # noqa: E402
import lock_analysis_dataset as LAD  # noqa: E402
import run_g10_assemble as G10  # noqa: E402

# ════════════════════════════════════════════════════════════════════════════
# G10-01 — 4 điểm nối phải dùng g4_quality_contract_satisfied(), không phải
# _status_locked()/_status_is_locked() text-check trên g4_status.
# ════════════════════════════════════════════════════════════════════════════


def _code_without_comments(src: str) -> str:
    """Bỏ mọi dòng chú thích (bắt đầu bằng '#' sau khi lstrip) — tránh việc chuỗi
    tên hàm chỉ xuất hiện trong COMMENT giải thích bug cũ đánh lừa bài test
    (đã tự bắt được lỗi này khi mutation-test lần đầu: comment trong bản vá tự
    nhắc tên hàm đúng, khiến kiểm substring ngây thơ luôn pass dù logic bị gỡ)."""
    return "\n".join(
        line for line in src.splitlines() if not line.lstrip().startswith("#")
    )


def _assert_uses_real_g4_contract(func, label: str) -> None:
    src = _code_without_comments(inspect.getsource(func))
    assert re.search(r"g4_quality_contract_satisfied\s*\(", src), (
        f"{label}: phải GỌI gate_contract.g4_quality_contract_satisfied() để chấm G4 "
        "— nếu test này fail nghĩa là bug 'g4_status không bao giờ = LOCKED' đã hồi quy."
    )
    # Không được còn kiểm text "g4_status"/"G4_STATUS" LÀM ĐIỀU KIỆN g4_ok (dấu hiệu
    # tautology cũ) — cho phép các usage khác (vd đọc metadata hiển thị) nhưng không
    # phải một phần biểu thức boolean quyết định "G4 đã khóa".
    assert 'get("g4_status")' not in src.replace(" ", ""), (
        f"{label}: vẫn còn đọc g4_status trực tiếp để quyết định g4_ok — "
        "run_g4_auto.py không bao giờ ghi 'LOCKED' vào trường này."
    )


def test_g9_auto_03_dung_ham_hop_dong_g4_that():
    _assert_uses_real_g4_contract(G9Q.evaluate_study, "g9_quality_gate.evaluate_study")


def test_g10_auto_04_dung_ham_hop_dong_g4_that():
    _assert_uses_real_g4_contract(G10Q.evaluate_study, "g10_quality_gate.evaluate_study")


def test_lock_analysis_dataset_upstream_report_dung_ham_hop_dong_g4_that():
    _assert_uses_real_g4_contract(
        LAD._upstream_approval_report, "lock_analysis_dataset._upstream_approval_report"
    )


def test_g5_auto_05_dung_ham_hop_dong_g4_that():
    _assert_uses_real_g4_contract(G5Q.evaluate_study, "g5_quality_gate.evaluate_study")


# ════════════════════════════════════════════════════════════════════════════
# G10-02 — chú giải nhãn quy ước không được tự kích hoạt _PLACEHOLDER_RE.
# ════════════════════════════════════════════════════════════════════════════


def test_front_note_khong_bao_gio_trung_placeholder_regex():
    """build_front_note() không có trường dữ liệu nào phụ thuộc input — phải
    LUÔN sạch, bất kể cps/meta rỗng hay đầy đủ."""
    cps_empty = {f"G{i}": {} for i in range(10)}
    note_empty = G10.build_front_note("TEST", cps_empty, {})
    assert not G10Q._PLACEHOLDER_RE.search(note_empty), note_empty

    cps_full = dict(cps_empty)
    cps_full["G7"] = {"n_pmids": 12}
    note_full = G10.build_front_note("TEST", cps_full, {"anything": "filled"})
    assert not G10Q._PLACEHOLDER_RE.search(note_full), note_full


def test_document_control_chi_bao_placeholder_that_khong_phai_chu_giai_co_dinh():
    """Khi TẤT CẢ trường thật đã điền, build_document_control() không được tự
    kích hoạt _PLACEHOLDER_RE qua câu chú giải cố định (đúng lỗi G10-02)."""
    cps_full = {f"G{i}": {} for i in range(10)}
    cps_full["G4"] = {"g4_sap_version": "1.0"}
    meta_filled = {
        "document_version": "1.0",
        "document_date": "2026-07-30",
        "prepared_by": "BS. Nguyen Van A",
        "approved_by": "PGS.TS. Tran Van B",
    }
    dc = G10.build_document_control("TEST", cps_full, meta_filled)
    match = G10Q._PLACEHOLDER_RE.search(dc)
    assert not match, f"placeholder giả trong văn bản đã điền đủ: {match.group(0) if match else None!r}"


def test_document_control_van_bao_placeholder_that_khi_chua_dien():
    """Đối chứng: khi approved_by THẬT SỰ chưa điền, phải VẪN flag đúng — vá
    G10-02 không được biến thành tautology ngược chiều (luôn PASS)."""
    cps_empty = {f"G{i}": {} for i in range(10)}
    dc = G10.build_document_control("TEST", cps_empty, {})
    assert G10Q._PLACEHOLDER_RE.search(dc), (
        "Khi approved_by/prepared_by/sap_version thật sự chưa có, văn bản PHẢI "
        "còn mang placeholder thật — nếu không, kiểm tra completeness bị vô hiệu.")
