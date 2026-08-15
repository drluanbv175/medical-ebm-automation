"""Test cho tools/research_ccn_status.py.

Dùng fixture CSV/MD GIẢ LẬP nhỏ (viết ra thư mục tmp trong test), KHÔNG đọc 4
sổ thật của dự án — để test ổn định, không phụ thuộc nội dung sổ thật thay đổi
theo thời gian.
"""
from __future__ import annotations

import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE / "tools"))

import research_ccn_status as rccn  # noqa: E402

# ----------------------------------------------------------------------------
# Fixture nội dung — mô phỏng cấu trúc thật của 4 sổ nhưng với số dòng nhỏ.
# ----------------------------------------------------------------------------
FIXTURE_GAP_REGISTER_CSV = """gap_id,category,description,phase,owner,status,blocks
GAP-X1,Identity,Production SSO/IdP integration,R1.2,Institutional IT,OPEN — EXTERNAL,Authentication
GAP-X2,Ethics,Ethics/IRB approval,R3.0,Ethics committee (external),OPEN — EXTERNAL,All clinical activity
GAP-X3,Qualification,PI sign-off on qualification report,R5.0,Dr Luân,OPEN — PENDING,Pilot activation
"""

FIXTURE_OPEN_DEPS_CSV = "\n".join(
    [
        "dependency_id,dependency_name,phase_first_identified,phase_blocking,owner,status,"
        "resolution_path,last_updated",
        "DEP-X1,Institutional SSO provider,R1.2,R1.3,Dr Luân / IT,EXTERNAL — NOT PROVIDED,"
        "Institutional IT engagement required,2026-01-01",
        "DEP-X2,WORM-capable storage provider,R1.3,R1.3,Dr Luân,EXTERNAL — NOT PROVIDED,"
        "Vendor selection required (AWS S3 Object Lock / Azure WORM),2026-01-01",
        "DEP-X3,Ethics/IRB committee approval,R3.0,R3.0,Dr Luân,EXTERNAL — NOT PROVIDED,"
        "Formal IRB submission required; cannot self-approve,2026-01-01",
    ]
) + "\n"

FIXTURE_EXT_DEPS_MD = """# Fixture External Dependency Register

**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

## Category A — Identity and Authentication

| ID | Dependency | Phase | Status |
|----|-----------|-------|--------|
| DEP-Y1 | Institutional SSO/IdP (OAuth2/OIDC/SAML) | R1.2 | NOT PROVIDED |

## Category F — Qualification

| ID | Dependency | Phase | Status |
|----|-----------|-------|--------|
| DEP-Y2 | Independent qualified assessor (IQ/OQ/PQ/SQ) | R5.0 | NOT ENGAGED |

## Summary

| Category | Total | Resolved | Open |
|---------|-------|----------|------|
| A | 1 | 0 | 1 |
"""

FIXTURE_AUTO_GAP_MD = """# Fixture Automation Gap Register

## 4. Danh mục vấn đề

### P0 - Bắt buộc trước khi dùng dữ liệu thật hoặc workflow lâm sàng thật

| ID | Mảng | Vấn đề cần hoàn thiện | Rủi ro nếu chưa làm | Hành động cần thực hiện | Chủ sở hữu | Cách kiểm chứng |
|---|---|---|---|---|---|---|
| P0-01 | Security | Auth chưa production-ready | Rủi ro | Làm auth thật | Dev | test |

### P1 - Bắt buộc trước pilot nghiên cứu thật và tự động G0-G9 với dữ liệu thật

| ID | Mảng | Vấn đề cần hoàn thiện | Rủi ro nếu chưa làm | Hành động cần thực hiện | Chủ sở hữu | Cách kiểm chứng |
|---|---|---|---|---|---|---|
| P1-A1 | IRB/DMP | Dữ liệu thật cần IRB/DMP thật | Vi phạm đạo đức | Chuẩn hóa DMP | PI + IRB | ledger |
| P1-A2 | SAP/data-lock | Cần SAP thật | p-hacking | Ký SAP | Statistician + PI | checksum |
| P1-A3 | Đã có tiến độ phụ lục | Mục này sẽ bị loại vì có trong phụ lục | n/a | n/a | PI | n/a |

### P1 - Bắt buộc trước dùng lâm sàng EBM thường quy

| ID | Mảng | Vấn đề cần hoàn thiện | Rủi ro nếu chưa làm | Hành động cần thực hiện | Chủ sở hữu | Cách kiểm chứng |
|---|---|---|---|---|---|---|
| P1-B1 | Local context | Formulary chưa xong | Không khả thi | Bác sĩ điền | Bác sĩ/cơ sở | test |

### P2 - Nâng mức tự động, độ tin cậy và vận hành dài hạn

| ID | Mảng | Vấn đề cần hoàn thiện | Hành động đề xuất | Cách kiểm chứng |
|---|---|---|---|---|
| P2-A1 | Orchestrator | Chưa gọi LLM-agent thật | Cắm executor thật | e2e test |
| P2-A2 | Human evaluation | Scorecard caveat | Bác sĩ/chuyên gia đánh giá mù | Human eval report |

## 10. Phụ lục — cập nhật sau lộ trình

| ID | Trạng thái | Tiến độ thật | Còn mở |
|---|---|---|---|
| **P1-A3** | cũ | mới | vẫn mở |
"""


def _write_fixtures(tmp_path: Path):
    gap_csv = tmp_path / "gap_register.csv"
    open_csv = tmp_path / "open_deps.csv"
    ext_md = tmp_path / "ext_deps.md"
    auto_md = tmp_path / "auto_gap.md"
    gap_csv.write_text(FIXTURE_GAP_REGISTER_CSV, encoding="utf-8")
    open_csv.write_text(FIXTURE_OPEN_DEPS_CSV, encoding="utf-8")
    ext_md.write_text(FIXTURE_EXT_DEPS_MD, encoding="utf-8")
    auto_md.write_text(FIXTURE_AUTO_GAP_MD, encoding="utf-8")
    return gap_csv, open_csv, ext_md, auto_md


# ----------------------------------------------------------------------------
# Test phân loại từ khoá (classify_fields)
# ----------------------------------------------------------------------------
def test_classify_simple_owner_groups():
    assert rccn.classify_fields("Institutional IT") == [rccn.HA_TANG_NGOAI]
    assert rccn.classify_fields("Ethics committee (external)") == [rccn.IRB]
    assert rccn.classify_fields("Dr Luân") == [rccn.PI]
    assert rccn.classify_fields("Research team") == [rccn.TO_CHUC]
    assert rccn.classify_fields("Independent assessor") == [rccn.REVIEWER]
    assert rccn.classify_fields("Biostatistician + Ethics") == [rccn.THONG_KE_VIEN]


def test_classify_combo_owner_multi_label():
    groups = rccn.classify_fields("PI + IRB")
    assert rccn.PI in groups and rccn.IRB in groups


def test_classify_opendep_suffix_after_slash():
    # "Dr Luân / IT" -> chỉ phần "IT" được dùng để phân loại (Dr Luân chỉ là
    # người theo dõi sổ, không phải bên chặn thật trong sổ OPEN-DEP).
    owner = "Dr Luân / IT"
    suffix = owner.split("/", 1)[1].strip()
    assert rccn.classify_fields(suffix) == [rccn.HA_TANG_NGOAI]


def test_classify_opendep_bare_owner_falls_back_to_resolution_path():
    # owner ghi trơn "Dr Luân" (không có "/") -> phải suy từ resolution_path.
    groups = rccn.classify_fields("", "Vendor selection required (AWS S3 Object Lock / Azure WORM)")
    assert groups == [rccn.HA_TANG_NGOAI]

    groups2 = rccn.classify_fields("", "Formal IRB submission required; cannot self-approve")
    assert groups2 == [rccn.IRB]


def test_classify_unclassifiable_text_returns_khong_ro():
    assert rccn.classify_fields("Không có manh mối gì ở đây cả xyz123") == [rccn.KHONG_RO]


# ----------------------------------------------------------------------------
# Test is_closed_status — không suy diễn CLOSED từ chuỗi phủ định.
# ----------------------------------------------------------------------------
def test_is_closed_status_negative_examples_are_open():
    assert rccn.is_closed_status("OPEN — EXTERNAL") is False
    assert rccn.is_closed_status("EXTERNAL — NOT PROVIDED") is False
    assert rccn.is_closed_status("NOT DONE") is False
    assert rccn.is_closed_status("MỞ (P1 gốc)") is False
    assert rccn.is_closed_status("") is False


def test_is_closed_status_positive_example():
    assert rccn.is_closed_status("CLOSED") is True


# ----------------------------------------------------------------------------
# Test parser từng sổ trên fixture
# ----------------------------------------------------------------------------
def test_parse_gap_register(tmp_path):
    gap_csv, _, _, _ = _write_fixtures(tmp_path)
    items = rccn.parse_gap_register(gap_csv)
    assert len(items) == 3
    ids = {it.item_id for it in items}
    assert ids == {"GAP-X1", "GAP-X2", "GAP-X3"}
    by_id = {it.item_id: it for it in items}
    assert by_id["GAP-X1"].groups == [rccn.HA_TANG_NGOAI]
    assert by_id["GAP-X2"].groups == [rccn.IRB]
    assert by_id["GAP-X3"].groups == [rccn.PI]
    assert all(not it.closed for it in items)


def test_parse_open_dependencies(tmp_path):
    _, open_csv, _, _ = _write_fixtures(tmp_path)
    items = rccn.parse_open_dependencies(open_csv)
    assert len(items) == 3
    by_id = {it.item_id: it for it in items}
    assert by_id["DEP-X1"].groups == [rccn.HA_TANG_NGOAI]
    assert by_id["DEP-X2"].groups == [rccn.HA_TANG_NGOAI]
    assert by_id["DEP-X3"].groups == [rccn.IRB]


def test_parse_external_dependency_md(tmp_path):
    _, _, ext_md, _ = _write_fixtures(tmp_path)
    items = rccn.parse_external_dependency_md(ext_md)
    ids = {it.item_id for it in items}
    # Bảng "Summary" phải bị bỏ qua (không phải danh sách mục).
    assert ids == {"DEP-Y1", "DEP-Y2"}
    by_id = {it.item_id: it for it in items}
    assert by_id["DEP-Y1"].groups == [rccn.HA_TANG_NGOAI]
    assert by_id["DEP-Y2"].groups == [rccn.REVIEWER]


def test_parse_automation_gap_register_filters_research_only(tmp_path):
    _, _, _, auto_md = _write_fixtures(tmp_path)
    items = rccn.parse_automation_gap_register(auto_md)
    ids = {it.item_id for it in items}
    # P0-01 (không phải nghiên cứu) và P1-B1 (bảng lâm sàng) phải bị loại.
    assert "P0-01" not in ids
    assert "P1-B1" not in ids
    # P1-A3 nằm trong phụ lục -> phải bị loại khỏi bảng P1 nghiên cứu.
    assert "P1-A3" not in ids
    # P1-A1, P1-A2 phải còn (không có trong phụ lục).
    assert "P1-A1" in ids
    assert "P1-A2" in ids
    # P2-A1 (orchestrator, không liên quan đánh giá người) phải bị loại;
    # P2-A2 (scorecard/kappa/Likert/đánh giá mù) phải được giữ.
    assert "P2-A1" not in ids
    assert "P2-A2" in ids

    by_id = {it.item_id: it for it in items}
    assert rccn.PI in by_id["P1-A1"].groups and rccn.IRB in by_id["P1-A1"].groups
    assert rccn.THONG_KE_VIEN in by_id["P1-A2"].groups and rccn.PI in by_id["P1-A2"].groups
    assert rccn.PI in by_id["P2-A2"].groups and rccn.REVIEWER in by_id["P2-A2"].groups


# ----------------------------------------------------------------------------
# Test tổng hợp end-to-end trên fixture + đếm nhóm
# ----------------------------------------------------------------------------
def test_collect_all_items_and_report_counts(tmp_path):
    gap_csv, open_csv, ext_md, auto_md = _write_fixtures(tmp_path)
    items = rccn.collect_all_items(gap_csv, open_csv, ext_md, auto_md)

    # 3 (GAP-REG) + 3 (OPEN-DEP) + 2 (EXT-DEP, loại Summary) + 3 (AUTO-GAP:
    # P1-A1, P1-A2, P2-A2; P1-A3/P0-01/P1-B1/P2-A1 bị loại) = 11
    assert len(items) == 11

    report = rccn.build_report(items)
    assert "Tổng số mục còn mở: 11" in report
    assert "Đã đóng: 0/11 (0.0%)" in report
    assert "0 mục có trạng thái CLOSED" in report

    # Không mục fixture nào có trạng thái CLOSED thật -> phải báo đúng 0%.
    assert all(not it.closed for it in items)


def test_report_is_read_only_does_not_touch_source_files(tmp_path):
    gap_csv, open_csv, ext_md, auto_md = _write_fixtures(tmp_path)
    before = {p: p.read_text(encoding="utf-8") for p in (gap_csv, open_csv, ext_md, auto_md)}
    items = rccn.collect_all_items(gap_csv, open_csv, ext_md, auto_md)
    rccn.build_report(items)
    after = {p: p.read_text(encoding="utf-8") for p in (gap_csv, open_csv, ext_md, auto_md)}
    assert before == after
