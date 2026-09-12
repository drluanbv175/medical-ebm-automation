r"""Hồi quy phát hiện #2 (MEDIUM-HIGH) của audit đa-agent 2026-09-06 (vòng 31)
trong tools/verify_clinical_evidence_agent_standards.py — 6/12 "cổng kiểm"
(EAS7-EAS12) chỉ tự đối chiếu với chính literal Python trong CÙNG FILE, nên
KHÔNG BAO GIỜ phát hiện được nếu tài liệu doctrine thật (SKILL.md/references)
mất nội dung về các chuẩn quốc tế/nguồn thẩm quyền/độ mới/khung câu hỏi/xung
đột chứng cứ/ranh giới production.

CƠ CHẾ LỖI (TRƯỚC bản vá) — mẫu lặp lại ở cả 6 hàm _check_*:
    def _check_international_standard_profile():
        profile = build_international_standard_profile()          # literal Python
        profile_text = json.dumps(asdict(profile), ...)
        required_tokens = ["RIGHT", "CONSORT", ...]                # literal Python
                                                                    # (CÙNG FILE, không đọc gì)
        missing = [t for t in required_tokens if t not in profile_text]
        ...

`build_international_standard_profile()` và `required_tokens` đều là literal
Python trong CÙNG hàm/module — `missing` chỉ khác rỗng khi có lỗi GÕ giữa hai
đoạn code, KHÔNG BAO GIỜ phản ánh nội dung THẬT của tài liệu doctrine trên
đĩa (SKILL.md, references/*.md) mà `evidence=[...]` của mỗi StandardCheck
liệt kê. Khác hẳn EAS1/EAS2 (`_check_agents`/`_check_skill_mirror`) — các
hàm đó dùng `_missing_files()`/`_missing_tokens()` đọc THẬT file .md.

Xác nhận thực nghiệm (không phải suy đoán): chạy thật
`python3 tools/verify_clinical_evidence_agent_standards.py --json` trong
checkout đơn-repo (thiếu `sync/`, `EBM-Dashboards/`, v.v. ở workspace gốc) —
EAS2-EAS6 (đọc file thật) FAIL đúng vì thiếu file, nhưng EAS7-EAS12 vẫn PASS
dù toàn bộ hạ tầng nơi các file "evidence" của chúng được liệt kê hoàn toàn
không tồn tại trên máy này.

BẢN VÁ: thêm `_missing_tokens()` (helper THẬT đã có sẵn, cùng cơ chế
`_check_agents()` dùng) đọc file doctrine THẬT tương ứng cho mỗi trong 6
policy — tokens đã xác minh TRỰC TIẾP đang tồn tại trong tài liệu thật lúc
vá (không suy đoán):
  EAS7  → references/02-cong-cu-tham-dinh-va-grade.md   (AGREE II, AMSTAR 2, RoB 2)
  EAS8  → references/01-nguon-va-xac-minh.md             (Cochrane, USPSTF, NICE, Consensus)
  EAS9  → SKILL.md                                       (verify_dashboard.py --online
                                                            --strict-sources, PARTIAL)
  EAS10 → references/07-mo-hinh-cau-hoi-va-khung-thay-the.md (PICO(T)(S), PECO, SPIDER,
                                                                ECLIPSE, CoCoPop)
  EAS11 → SKILL.md                                       (nêu cả hai chiều)
  EAS12 → tools/verify_clinical_production_control_plane.py (production, real patient
                                                               data — CÙNG REPO qua REPO,
                                                               KHÔNG dùng tools/upgrade_verify.py
                                                               vì file đó ở workspace GỐC,
                                                               một repo Git riêng — cùng giới
                                                               hạn "ban_sao_tran.py chưa nhận
                                                               diện sibling checkout trên
                                                               phiên cloud")

Nguyên tắc viết test: KHÔNG phụ thuộc workspace thật (module test hiện có,
tests/test_clinical_evidence_agent_standards.py, bị skip toàn bộ trên phiên
này vì thiếu `.claude/agents` ở thư mục MẸ — xác nhận qua đọc file). Thay vào
đó, monkeypatch module-level SKILL_ROOT/REPO trỏ vào tmp_path với nội dung
TỰ TẠO, để test chạy được và có ý nghĩa BẤT KỂ môi trường (cloud hay máy
bác sĩ). Với mỗi trong 6 check: (a) file THẬT vắng mặt → FAIL với lý do
missing_file (b) file THẬT tồn tại nhưng THIẾU đúng token cần → FAIL với lý
do gắn rõ tên file/token (c) file THẬT có đủ token → PASS (khớp hành vi
tautology cũ, vì bản vá KHÔNG đổi phần tự-đối-chiếu nội bộ)."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import verify_clinical_evidence_agent_standards as V  # noqa: E402

# (tên hàm check, đường dẫn tương đối tới SKILL_ROOT hoặc REPO, có dùng SKILL_ROOT
#  hay REPO, các token bắt buộc phải có trong file thật)
_CASES = [
    (
        "_check_international_standard_profile",
        ("references", "02-cong-cu-tham-dinh-va-grade.md"),
        "skill",
        ("AGREE II", "AMSTAR 2", "RoB 2"),
    ),
    (
        "_check_source_authority_registry",
        ("references", "01-nguon-va-xac-minh.md"),
        "skill",
        ("Cochrane", "USPSTF", "NICE", "Consensus"),
    ),
    (
        "_check_evidence_currency_policy",
        ("SKILL.md",),
        "skill",
        ("verify_dashboard.py --online --strict-sources", "PARTIAL"),
    ),
    (
        "_check_question_frame_policy",
        ("references", "07-mo-hinh-cau-hoi-va-khung-thay-the.md"),
        "skill",
        ("PICO(T)(S)", "PECO", "SPIDER", "ECLIPSE", "CoCoPop"),
    ),
    (
        "_check_conflicting_evidence_policy",
        ("SKILL.md",),
        "skill",
        ("nêu cả hai chiều",),
    ),
    (
        "_check_operational_completeness_policy",
        ("tools", "verify_clinical_production_control_plane.py"),
        "repo",
        ("production", "real patient data"),
    ),
]


def _target_path(tmp_path, rel_parts, root_kind):
    base = tmp_path / "skill" if root_kind == "skill" else tmp_path / "repo"
    return base.joinpath(*rel_parts)


def _patch_roots(monkeypatch, tmp_path):
    monkeypatch.setattr(V, "SKILL_ROOT", tmp_path / "skill")
    monkeypatch.setattr(V, "REPO", tmp_path / "repo")


class TestFileThatVangMatBiChanCung:
    """★★★ Ca chính — file doctrine THẬT vắng mặt phải làm check FAIL với lý
    do missing_file (TRƯỚC bản vá: các check này không hề nhìn tới file này
    nên PASS vô điều kiện dù thiếu toàn bộ hạ tầng doctrine)."""

    def test_moi_check_fail_khi_thieu_file_that(self, tmp_path, monkeypatch):
        _patch_roots(monkeypatch, tmp_path)
        for fn_name, _rel, _root, _tokens in _CASES:
            check = getattr(V, fn_name)()
            assert check.status == V.FAIL, (
                f"{fn_name}: file doctrine thật vắng mặt phải làm FAIL — "
                f"TRƯỚC bản vá thì PASS vô điều kiện vì không đọc file nào."
            )
            assert any("missing_file:" in m for m in check.missing), (
                f"{fn_name}: missing phải nêu rõ missing_file, có: {check.missing}"
            )


class TestFileThatThieuTokenBiChanCung:
    """★★★ Ca chính — file doctrine THẬT tồn tại nhưng THIẾU đúng token cần
    (mô phỏng doctrine bị xóa/sửa mất nội dung chuẩn) phải làm check FAIL,
    với lý do gắn rõ TÊN FILE (không phải chỉ literal Python nội bộ)."""

    def test_moi_check_fail_khi_file_that_thieu_token(self, tmp_path, monkeypatch):
        _patch_roots(monkeypatch, tmp_path)
        for fn_name, rel_parts, root_kind, tokens in _CASES:
            path = _target_path(tmp_path, rel_parts, root_kind)
            path.parent.mkdir(parents=True, exist_ok=True)
            # Viết file THẬT nhưng CỐ Ý bỏ token đầu tiên trong danh sách cần.
            noi_dung = "Tài liệu doctrine không còn nhắc " + ", ".join(tokens[1:])
            path.write_text(noi_dung, encoding="utf-8", newline="\n")

            check = getattr(V, fn_name)()

            assert check.status == V.FAIL, (
                f"{fn_name}: file thật thiếu token '{tokens[0]}' phải làm FAIL — "
                f"TRƯỚC bản vá luôn PASS vì không đọc nội dung file này."
            )
            rel_str = str(Path(*rel_parts))
            assert any(rel_str in m and "missing token" in m for m in check.missing), (
                f"{fn_name}: missing phải gắn rõ tên file '{rel_str}' + 'missing token', "
                f"có: {check.missing}"
            )


class TestFileThatDuTokenThiPass:
    """Đối chứng — file doctrine THẬT có ĐỦ mọi token cần thì check PASS,
    khớp đúng hành vi cũ (phần tự-đối-chiếu nội bộ vẫn giữ nguyên, không bị
    bản vá phá vỡ)."""

    def test_moi_check_pass_khi_file_that_du_token(self, tmp_path, monkeypatch):
        _patch_roots(monkeypatch, tmp_path)
        for fn_name, rel_parts, root_kind, tokens in _CASES:
            path = _target_path(tmp_path, rel_parts, root_kind)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("Tài liệu doctrine đủ nội dung: " + " · ".join(tokens),
                             encoding="utf-8", newline="\n")

            check = getattr(V, fn_name)()

            assert check.status == V.PASS, (
                f"{fn_name}: file thật có đủ token phải PASS như hành vi cũ — "
                f"có: {check.missing}"
            )
