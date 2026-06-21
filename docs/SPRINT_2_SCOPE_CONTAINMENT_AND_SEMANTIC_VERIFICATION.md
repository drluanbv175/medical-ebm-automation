# Sprint 2 — Scope Containment & Semantic Verification Gate

**Ngày kiểm tra:** 2026-06-21  
**Người thực hiện:** Claude AI (Cowork mode)  
**Baseline test trước khi bắt đầu:** 402/402 PASSED  
**Test sau khi hoàn thành gate:** 405/405 PASSED (+3 regression)

---

## Phần A — Scope Containment Review

### A1: Phân loại file thay đổi (working tree, chưa commit)

`git status` tại thời điểm kiểm tra cho thấy **16 file thay đổi chưa commit**, toàn bộ là out-of-scope:

| File | Trạng thái | Phân loại | Ghi chú |
|------|-----------|-----------|---------|
| `app/__init__.py` | M | Out-of-scope | Thêm lazy `get_research_os()` |
| `app/dashboard/main.py` | M | Out-of-scope | Thêm `_research_os_panel` trong Tab 6 |
| `app/research_os/__init__.py` | M | Out-of-scope | research_os exports |
| `app/research_os/causal_inference.py` | M | Out-of-scope | research_os |
| `app/research_os/data_lock.py` | M | Out-of-scope | research_os |
| `app/research_os/design_router.py` | M | Out-of-scope | research_os |
| `app/research_os/methods_review_workflow.py` | M | Out-of-scope | research_os |
| `app/research_os/project_registry.py` | M | Out-of-scope | research_os |
| `app/research_os/reporting_guideline_mapper.py` | M | Out-of-scope | Chứa CONSORT fix |
| `app/research_os/sap_engine.py` | M | Out-of-scope | research_os |
| `app/research_os/study_traceability_matrix.py` | M | Out-of-scope | research_os |
| `run.py` | M | Out-of-scope | Thêm CLI `research-os` command |
| `app/dashboard/_research_os_panel.py` | ?? (new) | Out-of-scope | UI panel 229 dòng |
| `docs/SPRINT_2_FINAL_RELEASE_READINESS.md` | ?? (new) | Out-of-scope | Docs |
| `docs/SPRINT_2_SINGLE_TEST_FAILURE_RCA.md` | ?? (new) | Out-of-scope | Docs |
| `tests/test_research_os.py` | ?? (new) | Out-of-scope | 89 tests mới |

**Authorized Sprint 2 committed changes (git log -20):** Toàn bộ RBAC guard, audit ledger,
chronic care program, care plan approval, education handout gating — đều đã **COMMIT** và không
nằm trong working-tree changes. Không có file nào trong authorized scope bị modify trong working tree.

**Kết luận A1:** 0 file authorized / 16 file out-of-scope trong working tree.

---

### A2: Kiểm tra runtime dependency

| Điểm kết nối | File | Dòng | Loại dependency | Đánh giá |
|---|---|---|---|---|
| Dashboard Tab 6 | `app/dashboard/main.py` | 854–855 | Lazy import trong `with tabs[5]:` block | **SOFT** — panel dùng `try/except ImportError`, graceful degradation |
| CLI `research-os` | `run.py` | 216–254 | Conditional import (`elif cmd == "research-os"`) | **CONDITIONAL** — không ảnh hưởng startup |
| Package init | `app/__init__.py` | 12–16 | Lazy function `get_research_os()` | **LAZY** — không ảnh hưởng startup |

**Kết quả key test:**  
```
python -m pytest tests/ --ignore=tests/test_research_os.py -k "not research_os" -q
→ 312 passed, 1 deselected   # core Sprint 2 tests KHÔNG phụ thuộc research_os
```

**Kết luận A2:** research_os KHÔNG phải hard runtime dependency của core Clinical OS.
Dashboard Tab 6 dùng `try/except` nên không crash nếu research_os lỗi. CLI là conditional.
Tách research_os ra branch riêng là an toàn về mặt runtime.

---

## Phần B — CONSORT Semantic Verification

### B1: Hiểu hệ thống hiện tại

File `app/research_os/reporting_guideline_mapper.py`:

```python
GUIDELINE_BY_DESIGN: Dict[str, str] = {
    "randomized_controlled_trial": "CONSORT",      # ← không có year
    "diagnostic_accuracy": "STARD 2015",            # ← có year
    "systematic_review": "PRISMA 2020",             # ← có year
    "prediction_model": "TRIPOD+AI 2024",           # ← có year
    "case_report": "CARE 2013",                     # ← có year
    "economic_evaluation": "CHEERS 2022",           # ← có year
    "quality_improvement": "SQUIRE 2.0",            # ← có version
    ...
}
```

**Không có field riêng** cho `version`, `displayLabel`, `sourceReference` —
string duy nhất dùng cho cả canonical code lẫn display label.

`reporting_guidelines_all("randomized_controlled_trial")` trả:
```python
{
    "primary": "CONSORT",
    "supplementary": ["SPIRIT 2013 (protocol)", "TIDieR (intervention description)"],
    "equator_url": "https://www.equator-network.org/reporting-guidelines/",
    "note": "Xác nhận phiên bản mới nhất tại EQUATOR trước khi nộp bản thảo."
}
```

### B2: Đánh giá semantic safety

**Kết luận: PARTIALLY NOT SAFE — Inconsistency Risk**

| Aspect | Đánh giá |
|--------|-----------|
| Test `== "CONSORT"` (test_v7 dòng 103) | ✅ Pass sau fix — fix là bắt buộc |
| Test `"CONSORT" in result` (test_research_os dòng 237) | ✅ Pass với cả hai dạng |
| Version info trong field riêng | ❌ Không có |
| Version guidance cho user | ⚠️ Chỉ qua `note` + `equator_url` (không explicit) |
| Nhất quán với guidelines khác | ❌ STARD, PRISMA, TRIPOD, CARE đều có year; CONSORT thì không |
| Design intent | ✅ Rõ ràng: versionless canonical + EQUATOR check |

**Root cause của inconsistency:** Fix được drive bởi test assertion `== "CONSORT"` (strict equality),
nhưng design của mapper không phân tách canonical code vs display label. Nếu version được add vào
CONSORT sau này ("CONSORT 2025"), test `== "CONSORT"` sẽ fail lại.

**Risk level:** MEDIUM — Không gây lỗi runtime, nhưng user nhìn vào panel thấy
"CONSORT" (không year) trong khi các guideline khác đều có year — gây nhầm lẫn về chuẩn
nào đang được áp dụng.

### B3: Regression tests đã thêm

File: `tests/test_v7_evidence_safety_research.py` — **3 tests mới, không xóa test cũ**

| Test | Mục đích |
|------|---------|
| `test_consort_canonical_code_is_versionless` | Khóa behavior hiện tại: `== "CONSORT"` |
| `test_consort_full_info_provides_version_guidance` | note + equator_url + SPIRIT supplementary không được mất |
| `test_mapper_other_guidelines_unaffected_by_consort_rename` | Regression: 10 guidelines khác không bị ảnh hưởng |

```
python -m pytest tests/test_v7_evidence_safety_research.py -k "consort or guideline" -v
→ 3 passed in 0.08s
```

**Khuyến nghị dài hạn (KHÔNG làm trong Sprint 2):** Tách mapper thành
`{"code": "CONSORT", "version": "2010", "label": "CONSORT 2010"}` để nhất quán
với STARD 2015, PRISMA 2020. Cần ADR và update tất cả assertions.

---

## Phần C — Release Branch Disposition

### Khuyến nghị: **Option A — Tách research_os ra branch riêng**

**Căn cứ:**

1. Core Sprint 2 tests (312) pass hoàn toàn **không cần** research_os
2. Dashboard Tab 6 dùng graceful degradation (`try/except`) → không crash khi tách
3. research_os không có trong authorized Sprint 2 scope definition
4. 89 tests mới trong `tests/test_research_os.py` cover riêng research_os
5. Ruff errors trong app/ chỉ ở research_os files (5 lỗi, không có trong core)

**Kế hoạch tách:**

```bash
# Bước 1: Tạo branch riêng cho research_os
git checkout -b feature/research-os-module

# Bước 2: Trên main Sprint 2 branch — revert uncommitted changes
git checkout -- app/__init__.py app/dashboard/main.py run.py
git checkout -- app/research_os/

# Bước 3: Xóa untracked files ngoài scope Sprint 2 khỏi main
# (giữ lại research_os trên feature branch)

# Bước 4: Chạy lại full suite trên main
python -m pytest --tb=short -q  # expect ≥ 312 passed
```

**Không cần Option B** vì research_os KHÔNG phải hard dependency của core Clinical OS.

---

## Phần D — Verification Results

| Kiểm tra | Kết quả | Chi tiết |
|----------|---------|---------|
| Full test suite (sau regression) | ✅ **405/405 PASSED** | +3 CONSORT regression tests |
| Core Sprint 2 (không research_os) | ✅ **312 PASSED** | research_os là tách biệt |
| Ruff lint — `app/` core | ✅ **0 lỗi** trong core Sprint 2 modules |
| Ruff lint — `app/` research_os | ⚠️ 5 lỗi (I001, E501×3, F401) trong research_os files |
| Ruff lint — `tests/` | ⚠️ 29 lỗi (E402, F811) — toàn bộ trong `test_research_os.py` |
| Mypy | N/A | mypy không cài trong venv |
| PII scan | ✅ **Sạch** | 1 false positive là comment trong ambient_scribe.py |
| Secret scan | ✅ **Sạch** | 0 hardcoded credentials |
| Integration tests | ✅ **11/11 PASSED** | |
| E2E tests | N/A | Không có thư mục tests/e2e/ |
| Accessibility tests | N/A | Không có test khớp keyword |
| pip-audit | ✅ **Sạch** | Exit code 0, không báo CRITICAL/HIGH |
| Tests skip/xfail | ✅ **KHÔNG CÓ** | 0 test bị skip hoặc disable |

---

## Báo cáo Cuối — 6 Mục Bắt Buộc

### A. Tổng thay đổi
- **Authorized Sprint 2:** 0 file trong working tree (toàn bộ đã commit)
- **Out-of-scope:** 16 file trong working tree:
  - 11 file modified (research_os modules × 9 + app/__init__.py + run.py + dashboard/main.py)
  - 3 file mới (\_research\_os\_panel.py + 2 docs)
  - 1 test file mới (test_research_os.py — 89 tests)

### B. Quyết định xử lý research_os / Dashboard Tab 6 / CLI

| Module | Quyết định | Lý do |
|--------|-----------|-------|
| `app/research_os/` | **SPLIT TO SEPARATE BRANCH** | Không phải authorized Sprint 2 scope; core 312 tests không phụ thuộc |
| `app/dashboard/_research_os_panel.py` | **SPLIT TO SEPARATE BRANCH** | Theo research_os; graceful degradation đã implement |
| `app/dashboard/main.py` (phần research_os) | **REVERT 2 dòng import** | Khi split, revert dòng 854–855 |
| `run.py` (research-os CLI) | **SPLIT TO SEPARATE BRANCH** | Conditional import, không ảnh hưởng startup |
| `docs/SPRINT_2_FINAL_RELEASE_READINESS.md` | **RETAIN** | Tài liệu Sprint 2 hợp lệ |
| `docs/SPRINT_2_SINGLE_TEST_FAILURE_RCA.md` | **RETAIN** | RCA document hợp lệ |
| `tests/test_research_os.py` | **SPLIT TO SEPARATE BRANCH** | Theo research_os module |

### C. CONSORT Semantic Verification

**Verdict: PARTIALLY NOT SAFE — Inconsistency Risk (MEDIUM)**

- Fix `"CONSORT 2010"` → `"CONSORT"` là bắt buộc để pass test `== "CONSORT"`
- Version info KHÔNG được preserve trong field riêng
- INCONSISTENT với 6 guidelines khác đều có year/version
- MITIGATED bởi: `note` + `equator_url` hướng dẫn check EQUATOR
- 3 regression tests đã thêm để khóa behavior và phát hiện regression tương lai
- Khuyến nghị: Tách code/version/label trong Sprint 3+ (cần ADR)

### D. Test Results Sau Scope Containment

```
Full suite:  405 passed, 0 failed, 1 warning  (6.51s)
Core only:   312 passed, 1 deselected          (6.24s)  ← independent of research_os
Regression:    3 passed, 5 deselected          (0.08s)  ← CONSORT semantic gate
```

### E. Có test nào skip/xóa/disable không

**KHÔNG** — 0 test bị skip, xfail, hoặc disable. 3 tests mới được THÊM VÀO (không xóa test cũ).
Tổng: 402 → 405 tests.

### F. Final Merge Recommendation

> **⚠️ READY WITH CONDITIONS**

**Điều kiện trước khi merge Sprint 2:**

1. **[BẮT BUỘC]** Tách toàn bộ research_os changes ra branch `feature/research-os-module`
   (revert `app/__init__.py`, `run.py`, dòng 854–855 của `dashboard/main.py`;
   move `_research_os_panel.py` và `test_research_os.py`)
2. **[BẮT BUỘC]** Chạy lại `python -m pytest --tb=short -q` trên main branch sau khi tách
   → expected ≥ 312 passed, 0 failed
3. **[BẮT BUỘC]** Xác nhận `ruff check app/` cho ra 0 lỗi trên main branch sau tách
4. **[KHUYẾN NGHỊ]** Tạo ADR cho decision "CONSORT versionless" — document lý do
   không pin year và khi nào cần update (CONSORT 2025 release)
5. **[THÔNG TIN]** `docs/SPRINT_2_*` giữ lại — là tài liệu hợp lệ
6. **[THÔNG TIN]** 3 CONSORT regression tests đã commit vào
   `tests/test_v7_evidence_safety_research.py` — giữ lại trong main branch

**Sau khi hoàn thành điều kiện 1–3:** → **READY TO CLOSE SPRINT 2**

---

*Document này được tạo tự động bởi Scope Containment Gate — Sprint 2.*  
*Tham chiếu: SPRINT_2_FINAL_RELEASE_READINESS.md, SPRINT_2_SINGLE_TEST_FAILURE_RCA.md*
