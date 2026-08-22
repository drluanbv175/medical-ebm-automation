---
_harness_template: "Plans.md.template"
_harness_version: "4.3.3"
---

# medical-ebm-automation — Plans.md

> **Project**: medical-ebm-automation
> **Created**: 2026-06-07
> **Updated by**: Claude Code (harness-plan create)

Sprint mục tiêu: **Rà soát & chốt độ tin cậy của 30 thang điểm lâm sàng `verified`** —
khóa (pin) bằng test các cập nhật guideline 2024–2026 và ghi change log, để nội dung
không bị trôi/sai khi sửa về sau.

---

## Phase 0: Nền kiểm thử (chạy được trước khi sửa nội dung)

| Task | Nội dung | DoD | Depends | Status |
|------|----------|-----|---------|--------|
| 0.1 | Tạo venv **ngoài OneDrive** (`~/.ebm-venv`), cài `requirements.txt`, chạy `pytest` lấy baseline xanh/đỏ. `[tdd:skip:env-setup]` | `pytest` chạy được; ghi lại số test pass/fail hiện tại vào change log | - | cc:done (95 passed) |
| 0.2 | Thêm baseline lint (ruff) nếu repo chưa có cấu hình; chỉ cấu hình, không sửa lỗi hàng loạt. `[tdd:skip:tooling-setup]` | `ruff check` chạy được, có file cấu hình; (hoặc ghi `Spec skip reason` nếu quyết định chưa dùng) | 0.1 | cc:done (ruff.toml, baseline 189) |

---

## Phase 1: Khóa các cập nhật guideline bằng test (chống trôi nội dung)

| Task | Nội dung | DoD | Depends | Status |
|------|----------|-----|---------|--------|
| 1.1 | Test khóa **6 thang đã cập nhật**: CHA2DS2-VA (max 8, ngưỡng ≥2 không phân biệt giới), FIB-4 (<1.3 MASLD/AASLD 2023), qSOFA (SSC 2021 *mạnh chống* sàng lọc đơn lẻ), MELD 3.0 (chuẩn từ 2023), GOLD ABE 2025 (eos ≥300 cho ICS), ASCVD PCE + cảnh báo PREVENT 2023. `[tdd:required]` | `tests/test_clinical_scores_updates.py` PASS; mỗi test FAIL nếu cụm từ/ngưỡng tương ứng bị xóa khỏi `verified.py` | 0.1 | cc:done (12 test, APPROVE) |
| 1.2 | Test khóa **GAD-7 = USPSTF 2023 mức B** (sàng lọc lo âu người lớn ≤64). `[tdd:required]` | Test PASS, FAIL nếu mất tham chiếu USPSTF 2023 | 0.1 | cc:done |
| 1.3 | Đảm bảo `seed_verified_scores()` ghi **ChangeLogEntry** cho mỗi thang được cập nhật. `[tdd:required]` | Test xác nhận có change-log entry sau khi cập nhật score; không trùng lặp khi chạy lại | 0.1 | cc:done |
| 1.4 | Test **liêm chính danh mục**: số `verified` = 32 và `needs_verification` = 16 (theo doc), và không `needs_verification` nào có công thức. `[tdd:required]` | Test PASS phản ánh đúng số liệu doc; nếu lệch → cập nhật doc hoặc code cho khớp (khớp: 32/16) | 0.1 | cc:done |

---

## Phase 2: Nhất quán định danh & hồ sơ (sau khi test xanh)

| Task | Nội dung | DoD | Depends | Status |
|------|----------|-----|---------|--------|
| 2.1 | Quyết định xử lý `score_id` đã đổi tên (`cha2ds2_vasc`, `meld_na`): giữ id + alias hiển thị hay đổi id. Ghi quyết định, **không phá khóa DB**. `[tdd:skip:decision-doc]` | Quyết định ghi vào `docs/RA_SOAT_THANG_DIEM_2026-06.md` (hoặc spec); seed vẫn chạy, không mất dữ liệu cũ | 1.1, 1.4 | cc:done (kỹ thuật: mục E; lâm sàng → mục F chờ chuyên khoa) |
| 2.2 | Cập nhật Change Log + thêm mục **chờ bác sĩ chuyên khoa ký xác nhận** (doc mục D.1) vào tài liệu. `[tdd:skip:docs-only]` | Doc cập nhật, có dòng sign-off; README trỏ tới quy trình cập nhật | 2.1 | cc:done |

---

## Phase 3: Dọn lint

| Task | Nội dung | DoD | Depends | Status |
|------|----------|-----|---------|--------|
| 3.1 | Sửa lint baseline theo NHÓM an toàn: (a) auto-fix imports/f-string, (b) lỗi logic (F841/E702/E741), (c) E501. Chạy test sau mỗi nhóm. `[tdd:skip:lint-cleanup]` | `ruff check` = 0 lỗi; `pytest` vẫn 114 passed | 0.2 | cc:done (ruff 0, reviewer APPROVE) |

---

## Phase 4: Hoàn thiện toàn diện (audit-driven)

| Task | Nội dung | DoD | Depends | Status |
|------|----------|-----|---------|--------|
| 4.A1 | XXE: dùng `defusedxml` cho parse XML (pubmed, rss). `[tdd:required]` | test parse XML an toàn; pytest xanh | - | cc:done |
| 4.A2 | Rate-limit chủ động theo host trong HttpClient (NCBI etiquette). `[tdd:required]` | test throttle; pytest xanh | - | cc:done |
| 4.A3 | Xác nhận trước khi gửi email thật (notify-test/set-email) + bỏ email hardcode. `[tdd:skip:cli-io]` | có bước [y/N]; dùng settings.alert_email_to | - | cc:done |
| 4.A4 | Bắt lỗi nút "Cập nhật ngay" trên dashboard (không lộ traceback). `[tdd:skip:ui]` | try/except + st.error thân thiện | - | cc:done |
| 4.A5 | Chống CSV/Excel formula injection + xóa dead code. `[tdd:required]` | test escape `=+-@`; pytest xanh | - | cc:done (CSV guard + xóa _safe_search; gộp _clean → 4.D2) |
| 4.B1 | Cột `is_mock` cho EvidenceItem + map trong normalize + migration + banner dashboard + loại mock khỏi actionable (live). `[tdd:required]` | test mock không lẫn live; banner hiện | - | cc:done |
| 4.C1 | Regulatory-alert không tự lên Tier A từ 1 keyword. `[tdd:required]` **[đã duyệt]** | test FDA-1-dòng không actionable; pytest xanh | - | cc:done |
| 4.C2 | Bỏ heuristic cứng (large_sample token, official_org substring) + dedup version-aware. `[tdd:required]` **[đã duyệt]** | test dương-tính-giả biến mất | - | cc:done |
| 4.D1 | Batch dịch máy + phân trang/tìm kiếm dashboard. `[tdd:skip:ui]` | dịch batch/cell; ô tìm + giới hạn 300 hàng | - | cc:done |
| 4.D2 | Tách logic kháng sinh dùng chung (is_antibiotic_text) + dùng ở report & dashboard. `[tdd:required]` | logic có test; hết trùng lặp | - | cc:done (tách is_antibiotic; tách toàn bộ monolith → HOÃN, rủi ro cao trên app đang chạy) |
| 4.D3 | Thêm test cho notify/exporters/antibiotic/translate-batch. `[tdd:required]` | test mới xanh | 4.D2 | cc:done |

---

## Phase 5: Rà soát tautology guardrail G0-G10 + tích hợp MCP plugin (2026-07-29 → 2026-07-31)

> Sprint này KHÔNG được khởi tạo qua `/harness-plan` — bác sĩ yêu cầu trực tiếp qua chat ("kiểm
> tra và hoàn thiện từng cổng", sau đó "kiểm tra plugin MCP đã cài đặt có tham gia hoàn thiện hệ
> thống"). Ghi lại đây qua `/harness-sync` (2026-07-31) để Plans.md không lệch thực tế git log —
> tự phát hiện chính mình chưa dùng harness cho sprint này khi bác sĩ hỏi về plugin, và bác sĩ
> chọn "đồng bộ lại ngay" thay vì chuyển hẳn quy trình.

| Task | Nội dung | DoD | Depends | Status |
|------|----------|-----|---------|--------|
| 5.1 | G8: sửa key-mismatch NGHIÊM TRỌNG (`reporting_completeness_pct`/`reporting_pct` không khớp khóa thật `reporting_score_pct`) khiến MỌI đề tài thật kẹt vĩnh viễn không đạt PASS. `[tdd:required]` | `tests/test_g8_quality_gate.py` PASS; mutation-tested | - | cc:done (5b59c44) |
| 5.2 | G10: sửa reverse-tautology NGHIÊM TRỌNG — 6 hàm build in placeholder vô điều kiện khiến cổng khóa cuối cùng KHÔNG BAO GIỜ đạt READY/LOCKED. `[tdd:required]` | test tích hợp assemble()+evaluate_study() thật xanh | 5.1 | cc:done (085f8b5) |
| 5.3 | G0/G1/G2/G4/G5: sửa 6 reverse-tautology (chặn oan Grade A/PICO hợp lệ ở G0; chặn cứng thiết kế định tính ở G1; topic-fallback lọt qua ở G2; SAP hoàn thiện thật bị BLOCK + 2 lỗi khác ở G4; phạt khai đúng SAP version ở G5). `[tdd:required]` | mỗi gate có test hồi quy mutation-tested; full suite xanh | 5.1, 5.2 | cc:done (5b5a35e, 5073da2, 25e34a8, fc09d53, a4471df) |
| 5.4 | G3/G6/G7/G9: honest-scope comment cho luật tautology thuần (chỉ bắt tampering, không thẩm định nội dung khoa học) + G7 2 khẳng định IRB/SAP-locked chưa bảo vệ + stale design-drift cache + PII false-positive. `[tdd:required]` | comment không đổi hành vi (xác nhận bằng diff); G7 có 4 test mới mutation-tested | 5.3 | cc:done (d3518df, 1ff39c0, a8e81be, 3b0bf7b) |
| 5.5 | Audit tích hợp MCP plugin: sửa ID gia đình plugin sai (`bio-research`→`healthcare`) cho PubMed/ClinicalTrials.gov ở 8 file doctrine (agent gọi đúng chuỗi cũ sẽ lỗi); bổ sung connector MCP vào 9 agent doctrine chưa hề nhắc dù có sẵn; trỏ 2 file bản đồ sang `_CONNECTOR-CHUNG-CU.md`. `[tdd:skip:docs-only]` | grep xác nhận 0 ID sai còn sót; `sync_agents_to_codex.py --check`/`verify_claude_code_repo_alignment.py` PASS | - | cc:done (5082f26, dbb254d) |
| 5.6 | Đính chính 2 mục "chưa sửa" lỗi thời trong CLAUDE.md (G8 6-vs-5 điều kiện, nhãn ICMJE 2023 — cả hai hóa ra đã vá từ trước, chỉ tài liệu quên cập nhật) + sửa 1 `rep_evidence` string lộ thông tin sai ra báo cáo cho bác sĩ. `[tdd:required]` | test hồi quy đổi tên theo string mới; full suite xanh | 5.5 | cc:done (9aea8ce) |
| 5.7 | G9: đóng khoảng trống THẬT trong checklist "Phần 8 — Hard Gate" — NHÓM D (trưởng đơn vị/hội đồng nội bộ/nhà tài trợ) chưa có field máy đọc được. Thêm `institutional_confirmation` + `_institutional_ok()` + tiêu chí `G9-HUMAN-11`. `[tdd:required]` | 3 test mới (undetermined/required-not-confirmed/required-and-confirmed) mutation-tested; full suite xanh | 5.6 | cc:done (9aea8ce) |

---

## In Progress

| Task | Noi dung | DoD | Depends | Status |
|------|----------|-----|---------|--------|
| CCOS-05 | Chronic Care Clinic OS handoff cho Claude Code: cap nhat `CLAUDE.md`, tao handoff manifest, va bat `sync-check` kiem tra scope hien tai. `[tdd:required]` | Claude Code doc tro toi `chronic-care-clinic-os`; `pnpm sync:check`, offline tests va typecheck xanh; commit scoped | CCOS-04 | cc:done |

## Completed

- [x] Harness initialized for project `pm:approved` (2026-06-07)
- [x] CCOS-01 Command Center + care orchestration queue `cc:done`
- [x] CCOS-02 Program registry + pre-visit packet `cc:done`
- [x] CCOS-03 Care plan draft + approval guardrails `cc:done`
- [x] CCOS-04 Approved patient education handout gate `cc:done`
- [x] CCOS-05 Claude Code handoff + sync guard `cc:done`

## Sprint 6 — Hoàn thiện HAI hệ: nghiên cứu y khoa & cập nhật chứng cứ lâm sàng

> Mở 2026-08-22 theo yêu cầu của bác sĩ (`/harness-loop`). Nguồn việc: giác quan
> `tools/tu_de_xuat_viec.py`, đối chiếu bài tổng thuật, và một khoảng trống đo được —
> chuỗi cổng CHỨNG CỨ có canary đầu-cuối (`tools/thu_dau_cuoi_chung_cu.py`) còn chuỗi
> 11 cổng NGHIÊN CỨU G0–G10 thì KHÔNG có gì tương đương.
> Việc thuộc thẩm quyền bác sĩ (ký cổng cứng, đổi `decision`, IRB) KHÔNG nằm trong sprint này.

| Task | Nội dung | DoD | Depends | Status |
|---|---|---|---|---|
| 6.1 | **Canary đầu-cuối cho chuỗi cổng NGHIÊN CỨU G0–G10.** Gài N lỗi BIẾT TRƯỚC vào một đề tài tổng hợp rồi đòi các quality gate phải CHẶN. Đối xứng với `thu_dau_cuoi_chung_cu.py` bên chứng cứ. `[tdd:required]` | Chạy ngoại tuyến < 30s, không PII, không đụng đề tài thật; mỗi lỗi gài có mã + lý do lịch sử; **kiểm bằng đột biến**: tắt một luật gate ⇒ canary đỏ đúng chỗ; nối vào `chot_hoi_quy_bai_hoc.py` | — | `cc:done` [4c9ebb7] (BH72; đột biến trên đĩa: tắt G4-AUTO-03 ⇒ đỏ 7/9, exit 1) |
| 6.2 | **Quét 4 bài tổng thuật THẬT theo 3 lớp lỗi ⑨⑩⑪** (`TT_dtd2-ckd`, `TT_sglt2i-da-hong-cau`, `TT_tuyen-giap`, `TT_vkdt-tong-quan`). Đây là bài bác sĩ dùng thật, chưa từng soi; tiền lệ: 14 phát hiện / 4 bài bench | Báo cáo có trích nguyên văn cho từng phát hiện; KHÔNG tự đổi `decision`/mức khuyến cáo; mọi mục ghi rõ hướng hại | — | `cc:done` — **31 phát hiện · 15 nặng**; báo cáo `EBM-Dashboards/derivatives/QUET-LOP-LOI-MOI_BAI-THAT_2026-08-22.md` |
| 6.3 | **Thẩm định độc lập bài viêm gan B** — cả hai lượt soi vòng trước đều chết (lỗi API, giới hạn phiên) nên bài này chưa từng được soi trọn vẹn sau khi sửa 5 lỗi | Soi đủ 11 lớp lỗi; xác nhận riêng nhánh HBsAg dương/âm; nêu rõ lỗi nào do vòng sửa gây ra | 6.2 | `cc:done` — 5/5 mục sửa vòng trước ĐÚNG NGUỒN; **8 phát hiện mới** (2 do chính vòng sửa, 2 nặng có từ trước chưa ai chạm); CHƯA hội tụ |
| 6.4 | **Dựng lại chỉ mục RAG toàn văn** — chỉ mục cũ hơn kho (giác quan ⑤) | `tu_de_xuat_viec.py` hết báo mục RAG | — | `cc:done` (178 bài → 23.939 đoạn) |


## Sprint 7 — Sửa 39 phát hiện đã được bác sĩ duyệt (23/08)

> Bác sĩ duyệt toàn bộ 39 phát hiện của Sprint 6 (31 trên 4 bài thật + 8 trên bài viêm gan B)
> và giao sửa «một cách tốt nhất cho hệ thống». Luật thi công rút từ các vòng trước:
> tự xác minh NGUỒN trước khi áp từng mục · ≥2 mục cùng khối ⇒ VIẾT LẠI TRỌN KHỐI (skill v1.7)
> · sửa một mệnh đề ⇒ GREP CẢ BÀI tìm câu cùng khẳng định · sau sửa BẮT BUỘC một lượt thẩm
> định độc lập (BH66) · điều kiện dừng = không còn phát hiện nào do vòng sửa gây ra.

| Task | Nội dung | DoD | Depends | Status |
|---|---|---|---|---|
| 7.1 | Sửa 8 phát hiện + 2 quan sát bài **tuyến giáp** (nặng nhất: ngừng ATD sai cửa sổ thai kỳ; corticoid trước RAI mất nhánh yếu tố nguy cơ; AIT thiếu lối thoát cấp cứu) | cổng trích dẫn ĐẠT; changelog trong bài; mục không xác minh được thì KHÔNG áp và khai rõ | — | `cc:todo` |
| 7.2 | Sửa 9 phát hiện bài **VKDT tổng quan** (điền 4/4 ô ACR từ toàn văn tại chỗ; corticoid «cùng hướng» sai; ngoại lệ suy tim/nhiễm trùng/NTM; lối ra lao-HBV; phép hội + hút thuốc) | như 7.1 | — | `cc:todo` |
| 7.3 | Sửa 7 phát hiện bài **SGLT2i đa hồng cầu** (nguồn [4] bị đảo chiều; tách 2 danh sách nguy cơ; «đỉnh 9 tháng»; vế RCT-null; bộ loại trừ; lối ra ngừng thuốc có kiểm soát) | như 7.1; [2][3] tường phí ⇒ chỉ hedge, không khẳng định thêm | — | `cc:todo` |
| 7.4 | Sửa 7 phát hiện bài **ĐTĐ2-CKD** (1A→2B sai quần thể; Figure 48 lấy nhầm cột; RASi chỉ định vs liều; điều kiện kali finerenone; lối ra RASi; mức statin) | như 7.1 | — | `cc:todo` |
| 7.5 | Sửa 8 phát hiện bài **viêm gan B** (thống nhất «hoặc» ngưỡng EASL ở cả 3 chỗ; phanh EASL defer/other-causes; đảo lại câu phủ định về [5]; lệnh cấm ngừng ở HBeAg+; mẫu số [4]) | như 7.1 | — | `cc:todo` |
| 7.6 | **Thẩm định độc lập cả 5 bài sau sửa** — mỗi bài một agent mới; điều kiện hội tụ: không còn phát hiện nào do vòng sửa 23/08 gây ra | báo cáo hội tụ từng bài; tồn dư (nếu có) sửa tiếp rồi soi lại | 7.1–7.5 | `cc:todo` |


## Archive

---

## Status Marker Legend

| Marker | Meaning |
|--------|---------|
| `pm:requested` | PM requested work |
| `cc:todo` | Not started by Claude Code |
| `cc:wip` | Claude Code is working |
| `cc:done` | Claude Code completed, awaiting confirmation |
| `pm:approved` | PM confirmed completion |
| `blocked` | Blocked; include the reason |

TDD tags: `[tdd:required]` = viết test thất bại trước; `[tdd:skip:<lý do>]` = bỏ TDD có lý do.

---

## Last Update

- **Updated at**: 2026-08-22 (harness-loop, Sprint 6 hoàn tất 4/4)
- **Last session owner**: Claude Code
- **Branch**: feat/r1-1-2-design-gap-remediation
