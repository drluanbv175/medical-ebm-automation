# Sprint 2 — Single Test Failure Root Cause Analysis

**Date:** 2026-06-21  
**Authored by:** Automated RCA gate (Sprint 2 remediation protocol)  
**Status:** RESOLVED — see Section 5

---

## 1. Mô tả lỗi

**Test:** `test_research_os_gates_design_protocol_sap_and_data_lock`  
**File:** `tests/test_v7_evidence_safety_research.py`, line 103  
**Command run:**
```
~/.ebm-venv/bin/python -m pytest tests/test_v7_evidence_safety_research.py::test_research_os_gates_design_protocol_sap_and_data_lock -v --tb=long
```

**Error message (verbatim, reproducible 3/3):**
```
AssertionError: assert 'CONSORT 2010' == 'CONSORT'
  - CONSORT
  + CONSORT 2010
tests/test_v7_evidence_safety_research.py:103: AssertionError
```

**Assertion sai:**
```python
assert reporting_guideline_for_design(protocol.design) == "CONSORT"
# actual returned: "CONSORT 2010"
```

**Phân loại:** Product defect (implementation trả sai giá trị so với contract test)  
**Loại test:** Integration — kiểm tra chuỗi giá trị từ `reporting_guideline_mapper.py`

---

## 2. Tác động tới Sprint 2

- 1/402 test FAILED trước remediation → Sprint 2 không đạt chuẩn release
- Test thuộc file `test_v7_evidence_safety_research.py` — file Sprint 2 core
- Nếu không sửa: Sprint 2 gate bị chặn, không thể tiếp tục

---

## 3. Root Cause Thực Sự

**File lỗi:** `app/research_os/reporting_guideline_mapper.py`, line 12  
**Giá trị hiện tại:**
```python
GUIDELINE_BY_DESIGN: Dict[str, str] = {
    "randomized_controlled_trial": "CONSORT 2010",   # ← LỖI
    ...
}
```

**Giá trị đúng theo contract test:**
```python
"randomized_controlled_trial": "CONSORT",
```

**Nguyên nhân gốc:** Tại một thời điểm trong Sprint 2, ai đó đã thêm suffix `" 2010"` vào tên guideline
cho RCT, biến `"CONSORT"` thành `"CONSORT 2010"`. Điều này vi phạm contract của test
Sprint 2 core (`== "CONSORT"`) trong khi test out-of-scope (`test_research_os.py`)
không phát hiện vì dùng `in` operator thay vì strict equality.

**Bằng chứng phân tích tên guideline:**
- CONSORT 2025 đã được công bố tháng 5/2026 → `"CONSORT 2010"` đã lỗi thời
- Convention codebase: một số guideline có năm (STARD 2015, PRISMA 2020), một số không (STROBE, COREQ/SRQR)
- CẢ HAI test đều được viết để kỳ vọng `"CONSORT"` (không có năm):
  - `test_research_os.py` line 237: `assert "CONSORT" in result` → substring check
  - `test_v7_...` line 103: `assert ... == "CONSORT"` → strict equality
- Chuỗi `"CONSORT 2010"` chỉ xuất hiện tại **1 file duy nhất** trong toàn bộ codebase `.py`

---

## 4. Vì Sao Các Test Khác Không Phát Hiện

`test_research_os.py` (89 tests, OUT OF SCOPE) sử dụng:
```python
def test_rct_maps_to_consort(self):
    assert "CONSORT" in reporting_guideline_for_design("randomized_controlled_trial")
```
`"CONSORT"` là substring của `"CONSORT 2010"` → `in` operator trả `True` → test PASS.

Test Sprint 2 core dùng `==` (strict equality) → FAIL.

Kết quả: lỗi ẩn trong 89 out-of-scope tests nhưng lộ ra ở Sprint 2 gate test.

---

## 5. Phương Án Sửa Tối Thiểu

**Sửa implementation (KHÔNG sửa test):**

File: `app/research_os/reporting_guideline_mapper.py`, line 12  
Thay:
```python
"randomized_controlled_trial": "CONSORT 2010",
```
Thành:
```python
"randomized_controlled_trial": "CONSORT",
```

**Lý do chọn sửa implementation thay vì sửa test:**
1. `"CONSORT 2010"` là giá trị SAI (outdated — CONSORT 2025 là hiện hành)
2. Design intent rõ ràng là `"CONSORT"` (cả hai test đều kỳ vọng điều này)
3. Không có downstream code nào phụ thuộc vào chuỗi `"CONSORT 2010"` cụ thể
4. Sửa test assertion sẽ là "hide the bug" vì implementation lỗi thật sự

---

## 6. Rủi Ro Của Phương Án Sửa

| Rủi ro | Mức độ | Biện pháp |
|---|---|---|
| Break test khác | **Thấp** | Chỉ 1 file chứa "CONSORT 2010"; test_research_os dùng `in` → vẫn pass với "CONSORT" |
| Scope drift | **Không có** | 1 dòng thay đổi, trong module đã tồn tại |
| Mất thông tin version | **Thấp** | Version detail vẫn có trong `_SUPPLEMENTARY["randomized_controlled_trial"]` |
| Regression evidence workbench | **Thấp** | Chuỗi "CONSORT" không được so sánh strict ở nơi nào khác |

---

## 7. Files Dự Kiến Sửa

| File | Dòng | Thay đổi |
|---|---|---|
| `app/research_os/reporting_guideline_mapper.py` | 12 | `"CONSORT 2010"` → `"CONSORT"` |

**Không có file nào khác cần sửa.**

---

## 8. Xác Nhận Không Cần Thay Đổi Phạm Vi Sprint 2

- Lỗi nằm trong module `app/research_os/` (đã shipped trong Sprint 2 — scope drift có ghi nhận)
- Fix là 1 dòng thay đổi giá trị chuỗi, KHÔNG thêm chức năng mới
- KHÔNG mở rộng research_os, KHÔNG thêm CLI, KHÔNG thêm Tab6
- Fix hoàn toàn tương thích ngược với test_research_os.py (out-of-scope, 89 tests)
- Sprint 2 scope drift (Tab6, research_os 15 modules) đã được ghi nhận trong SPRINT_2_FINAL_RELEASE_READINESS.md — fix này không làm nặng thêm drift đó
