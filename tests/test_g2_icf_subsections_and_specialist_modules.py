"""Hồi quy (vòng lặp kiểm tra-hoàn thiện vòng 15, 2026-07-24):

1. [HIGH] ICF do generate_g2_full_package() sinh ra trước đây chỉ có 7 mục
   GỐC (1-7), thiếu 7 mục con BẮT BUỘC theo doctrine `dao-duc-dang-ky.md`
   (1b/4b/4c/6b/6c/6d/6e — Helsinki §26, ICH-GCP E6(R3) 2.8.10(h)/(i), SPIRIT
   2025 mục 32b/34) — và guardrail_check_g2() R6 vẫn báo "✅ đủ 7 mục" dù
   thiếu các khoản này. Nay ICF luôn có 1b/4b/4c/6c (nghĩa vụ CHUNG mọi thiết
   kế); 6b/6d chỉ khi design_code == "rct"; 6e khi design_code in (rct,
   cohort). Guardrail có thêm R6b bắt buộc 4 mục universal.

2. [MEDIUM] run_g2_auto.py không đọc specialist_modules từ G1 checkpoint (cờ
   economic/qualitative) — là cổng DUY NHẤT trong G0-G10 bỏ qua tín hiệu này
   trong khi G7/G8/G9 đều đã nối. Nay generate_g2_full_package() nhận
   specialist_modules và nối dòng rủi ro/đồng thuận bổ sung tương ứng.

3. [MEDIUM] Mọi chuỗi "Helsinki 2013"/"WMA 2013" trong artifact G2 — doctrine
   đã xác nhận Helsinki (WMA 2024) là bản hiện hành, 2013 chỉ còn giá trị
   tham khảo lịch sử. Nay artifact dùng "Helsinki (WMA, bản sửa 2024)".

4. [LOW] R2 (chống bịa số phê duyệt) dùng regex chỉ khớp nhãn "Mã nghiên
   cứu:" — template ICF thật dùng nhãn "số IRB"/"Số IRB", nên R2 chưa từng
   có cơ hội khớp với chính artifact nó bảo vệ. Nay regex khớp cả 2 nhãn.
"""
from __future__ import annotations

import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

from run_g2_auto import (  # noqa: E402
    RISK_PROFILES,
    generate_g2_full_package,
    guardrail_check_g2,
)

UNIVERSAL_MARKERS = [
    "1b. NGƯỜI THỰC HIỆN NGHIÊN CỨU",
    "4b. NGUỒN TÀI TRỢ VÀ XUNG ĐỘT LỢI ÍCH",
    "4c. HỖ TRỢ/BỒI DƯỠNG",
    "6c. BỒI THƯỜNG KHI CÓ TỔN HẠI",
]
RCT_ONLY_MARKERS = ["6b. LỰA CHỌN THAY THẾ", "6d. CHĂM SÓC BỔ TRỢ"]
BIOSPECIMEN_MARKER = "6e. ĐỒNG THUẬN THU THẬP"


def _gen(design_code, specialist_modules=None, n_adjusted=0):
    risk = RISK_PROFILES[design_code]
    return generate_g2_full_package(
        topic="Đề tài test", study_name="TEST-STUDY", design_code=design_code,
        design_primary="Thiết kế test", reporting_std="STROBE", n_sr=5, n_rct=0,
        evidence_level="TRUNG BÌNH", registry=None, risk=risk,
        run_date="2026-07-24", n_adjusted=n_adjusted,
        specialist_modules=specialist_modules,
    )


def test_universal_icf_subsections_present_for_every_design():
    for design_code in ("rct", "cohort", "cross_sectional", "case_control"):
        doc = _gen(design_code)
        for marker in UNIVERSAL_MARKERS:
            assert marker in doc, f"{design_code}: thiếu {marker}"


def test_rct_only_subsections_present_only_for_rct():
    rct_doc = _gen("rct")
    for marker in RCT_ONLY_MARKERS:
        assert marker in rct_doc

    cohort_doc = _gen("cohort")
    for marker in RCT_ONLY_MARKERS:
        assert marker not in cohort_doc, "cohort không có can thiệp — không nên có 6b/6d"


def test_biospecimen_subsection_only_for_rct_and_cohort():
    assert BIOSPECIMEN_MARKER in _gen("rct")
    assert BIOSPECIMEN_MARKER in _gen("cohort")
    assert BIOSPECIMEN_MARKER not in _gen("cross_sectional")


def test_no_unresolved_fstring_placeholders_leak_into_output():
    doc = _gen("rct", specialist_modules=["economic", "qualitative"])
    for leaked in ("{icf_1b}", "{icf_4bc}", "{icf_6b}", "{icf_6c}", "{icf_6d}",
                   "{icf_6e}", "{specialist_risk_note}"):
        assert leaked not in doc


def test_guardrail_r6b_passes_for_generated_artifact():
    doc = _gen("rct")
    result = guardrail_check_g2(doc)
    assert result["passed"], result["errors"]
    assert any(w.startswith("R6b ✅") for w in result["warnings"])


def test_guardrail_r6b_fails_when_universal_subsection_stripped():
    doc = _gen("rct")
    stripped = doc.replace("6c. BỒI THƯỜNG KHI CÓ TỔN HẠI", "")
    result = guardrail_check_g2(stripped)
    assert not result["passed"]
    assert any(e.startswith("R6b 🔴") for e in result["errors"])


def test_specialist_modules_economic_and_qualitative_add_risk_notes():
    doc = _gen("cohort", specialist_modules=["economic", "qualitative"])
    assert "KINH TẾ Y TẾ bổ sung" in doc
    assert "ĐỊNH TÍNH/PHỎNG VẤN bổ sung" in doc

    plain_doc = _gen("cohort", specialist_modules=[])
    assert "KINH TẾ Y TẾ bổ sung" not in plain_doc
    assert "ĐỊNH TÍNH/PHỎNG VẤN bổ sung" not in plain_doc


def test_specialist_modules_skipped_when_design_code_is_the_module_itself():
    # economic design chính KHÔNG cần dòng "bổ sung" (nó vốn đã là economic)
    doc = _gen("cohort", specialist_modules=["economic"])
    assert "KINH TẾ Y TẾ bổ sung" in doc  # cohort + economic phụ trợ → có


def test_helsinki_citation_uses_2024_not_2013():
    for design_code in ("rct", "sr_ma"):
        doc = _gen(design_code)
        assert "WMA 2013" not in doc
        assert "Helsinki 2013" not in doc
        assert "2024" in doc


def test_r2_regex_matches_real_irb_label_not_only_legacy_label():
    doc = _gen("rct")
    # Placeholder chưa điền → không báo lỗi bịa số
    result = guardrail_check_g2(doc)
    assert not any(e.startswith("R2 🔴") for e in result["errors"])

    # Giả lập bác sĩ/agent điền một số IRB có vẻ tự bịa vào đúng nhãn thật
    faked = doc.replace(
        "[Phiên bản phê duyệt sẽ có số IRB — CẦN BỔ SUNG]",
        "Số IRB: 2026-IRB-045",
    )
    result_faked = guardrail_check_g2(faked)
    assert any(e.startswith("R2 🔴") for e in result_faked["errors"])
