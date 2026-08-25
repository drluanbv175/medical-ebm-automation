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
| 7.1 | Sửa 8 phát hiện + 2 quan sát bài **tuyến giáp** (nặng nhất: ngừng ATD sai cửa sổ thai kỳ; corticoid trước RAI mất nhánh yếu tố nguy cơ; AIT thiếu lối thoát cấp cứu) | cổng trích dẫn ĐẠT; changelog trong bài; mục không xác minh được thì KHÔNG áp và khai rõ | — | `cc:done` — 8/8 + 2/2 quan sát, 0 khong_ap; cổng ĐẠT |
| 7.2 | Sửa 9 phát hiện bài **VKDT tổng quan** (điền 4/4 ô ACR từ toàn văn tại chỗ; corticoid «cùng hướng» sai; ngoại lệ suy tim/nhiễm trùng/NTM; lối ra lao-HBV; phép hội + hút thuốc) | như 7.1 | — | `cc:done` — 9/9; cổng ĐẠT |
| 7.3 | Sửa 7 phát hiện bài **SGLT2i đa hồng cầu** (nguồn [4] bị đảo chiều; tách 2 danh sách nguy cơ; «đỉnh 9 tháng»; vế RCT-null; bộ loại trừ; lối ra ngừng thuốc có kiểm soát) | như 7.1; [2][3] tường phí ⇒ chỉ hedge, không khẳng định thêm | — | `cc:done` — 7/7; cổng ĐẠT |
| 7.4 | Sửa 7 phát hiện bài **ĐTĐ2-CKD** (1A→2B sai quần thể; Figure 48 lấy nhầm cột; RASi chỉ định vs liều; điều kiện kali finerenone; lối ra RASi; mức statin) | như 7.1 | — | `cc:done` — 7/7 (session limit ngắt giữa chừng lần 1, agent thứ hai hoàn tất phần thiếu); cổng ĐẠT |
| 7.5 | Sửa 8 phát hiện bài **viêm gan B** (thống nhất «hoặc» ngưỡng EASL ở cả 3 chỗ; phanh EASL defer/other-causes; đảo lại câu phủ định về [5]; lệnh cấm ngừng ở HBeAg+; mẫu số [4]) | như 7.1 | — | `cc:done` — 8/8; 1 lỗi cổng do trích cả số trích dẫn nội bộ [59] của nguồn [5] — đã gỡ; cổng ĐẠT |
| 7.6 | **Thẩm định độc lập cả 5 bài sau sửa** — mỗi bài một agent mới; điều kiện hội tụ: không còn phát hiện nào do vòng sửa 23/08 gây ra | báo cáo hội tụ từng bài; tồn dư (nếu có) sửa tiếp rồi soi lại | 7.1–7.5 | `cc:done` — VKDT sạch ngay; tuyến giáp 2 lỗi thật (câu tự mâu thuẫn TR4/EU-TIRADS, thiếu nhánh "bệnh mắt không hoạt động"), SGLT2i 2 điểm nhẹ (trích [1] quá rộng cho "hút thuốc", gộp p-value 3 nhóm), CKD 1 khoảng hở trích trang (thiếu S158/S214) — cả 5 đã vá + verify chéo lần 2, cổng ĐẠT cả 5, hội tụ |

---

## Sprint 8 — Dọn nợ kỹ thuật nhỏ phát hiện qua audit toàn diện 23/08

> Mở 23/08/2026 theo yêu cầu bác sĩ (`/harness-plan`, sau khi `/harness-work` không có
> gì trong hàng đợi). Nguồn việc: `tools/upgrade_verify.py` (28/28 PASS) + `pytest` toàn
> repo (3136 passed, 0 fail) — hệ thống sạch, chỉ lộ ra đúng 1 nợ kỹ thuật nhẹ qua
> warning. **Spec skip reason**: không đổi hành vi người dùng thấy được, không đụng
> API/data model/quyền/billing/tích hợp ngoài — chỉ đổi lời gọi API nội bộ Pillow sang
> tên không bị deprecate, giữ nguyên đầu ra pixel. `team_validation_mode:
> not_required_lightweight` (1 file, rủi ro thấp, không ảnh hưởng product behavior).

| Task | Nội dung | DoD | Depends | Status |
|---|---|---|---|---|
| 8.1 | `[tdd:skip:api-migration-existing-tests-cover-behavior]` Đổi `src.getdata()` → `src.get_flattened_data()` tại `app/integrations/image_reading.py:74` (hàm `strip_exif`). `Image.Image.getdata` sẽ bị Pillow gỡ bỏ 2027-10-15 (`DeprecationWarning` đã thấy trong `pytest`); `get_flattened_data()` không tham số `band` trả cùng dạng tuple pixel, đã xác nhận bằng docstring + Pillow 12.2.0 cài sẵn trong venv. | `pytest tests/test_image_reading.py -q` PASS, không còn DeprecationWarning liên quan `getdata` trong output; `pytest -q` toàn repo vẫn 3136 passed, 0 fail; `ruff check .` sạch | — | `cc:done` — 9/9 test PASS kể cả với `-W error::DeprecationWarning`; ruff sạch; pytest toàn repo 3136 passed/0 fail (150s) |

---

## Sprint 9 — Audit đa-agent 5 trục theo yêu cầu bác sĩ (24/08): G0-G10 tự động · cổng tra cứu · nguồn chứng cứ · mẫu cập nhật · tầng agent

> Mở 24/08/2026 theo `/harness-loop` với mục tiêu rộng của bác sĩ: "đảm bảo hệ nghiên cứu +
> cập nhật chứng cứ đã hoàn thiện tốt nhất". Phóng 5 agent audit song song (chỉ đo lường,
> không sửa) rồi lập Sprint theo phát hiện thật, không tự bịa việc. Kết quả 5 trục:
> ① G0-G10 — 🔴 2 lỗ hổng thật (xem 9.1) · ② cổng tra cứu — 🟢 sạch ở lõi · ③ nguồn chứng cứ
> mới nhất — 🟢 tốt (0/63 quá hạn đỏ) · ④ mẫu cập nhật — 🟢 sạch ở lõi, 66/67 lệch vỏ CSS ·
> ⑤ tầng agent doctrine — 🟢 sạch, không trôi tụt (74/74 bài học BH01-74 không tái phát).

| Task | Nội dung | DoD | Depends | Status |
|---|---|---|---|---|
| 9.1 | **[NGHIÊM TRỌNG] Vá cổng G8/G2/G4 thiếu chốt chất lượng trước khi ký.** G8 (bình duyệt độc lập) KHÔNG có bất kỳ chốt nào — `g8_quality_gate.py` tồn tại, đúng logic, có test, nhưng `approve_gate.py` chưa từng import/gọi nó; ai giữ khóa vai trò PHAN_BIEN ký được "đã bình duyệt độc lập" mà không cần bản nhận xét thật, kể cả tự duyệt cho chính đề tài mình đứng tên G4. G2/G4: 24 mục WHO TRDS + 12 tiêu chí SAP chỉ chạy SAU khi đã ghi ledger (advisory). Nối `G8Q/G2Q/G4Q.evaluate_study(write=False)` vào ĐÚNG TRƯỚC bước ghi ledger, khuôn theo G5/G9/G10 đã có; G8 chấp nhận status∈{PENDING,REVIEWED}, G4 chấp nhận READY, G2 từ chối khi BLOCKED/DRAFT. `[tdd:required]` | 8 test mới `tests/test_approve_gate_quality_gate_wiring_20260824.py` PASS; **kiểm bằng đột biến**: tắt từng chốt (G8/G4/G2) ⇒ đúng test tương ứng đỏ, khôi phục ⇒ xanh lại; 2 test cũ `test_approval_ledger.py` (dùng SAP tối giản) sửa lại dùng SAP thật qua `run_g4_auto.py`; toàn repo `pytest` 3144 passed/0 fail; `ruff check` sạch | — | `cc:done` — 5 điểm sửa trong `approve_gate.py` (import G8Q; chốt trước-ký G2/G4/G8 mới; advisory report sau-ký G8); đột biến xác nhận cả 3 chốt đều bắt đúng lỗi mô phỏng |
| 9.2 | Đồng bộ vỏ CSS/HTML/JS của 66/67 dashboard (98,5%) về đúng template hiện hành — cơ chế "sửa template → chạy lại reskin" chưa thực thi sau lần sửa template gần nhất (18/08). `[tdd:skip:content-preserving-tooling-already-exists]` | `tools/reskin_dashboards.py --dry-run` báo 0/67 hoặc gần 0 cần reskin sau khi chạy thật; khối `DATA` mọi dashboard KHÔNG đổi (chỉ vỏ); `verify_dashboard.py --online` vẫn PASS trên mẫu đã kiểm ở audit trục ④ | — | `cc:done` — 67/67 reskin, backup `_reskin_backup/20260824-201603`; dry-run lại báo 0/67 cần đổi (idempotent xác nhận); script tự viết so khối DATA byte-for-byte 66/66 file trong backup khớp tuyệt đối (1 file đã chuẩn từ đầu không cần backup); `verify_dashboard.py --online --strict-sources` trên 2 mẫu cho kết quả GIỐNG HỆT bản backup (viêm gan B PASS cả hai, VKDT FAIL cả hai với cùng 1 lỗi cứng — xác nhận lỗi có SẴN TỪ TRƯỚC, không do reskin gây ra, xem 9.6 mới) |
| 9.6 | **[Phát hiện phụ, ngoài kế hoạch ban đầu — NGHIÊM TRỌNG hơn dự kiến]** Quét `--online --strict-sources` toàn kho 67 dashboard (phát hiện tình cờ khi xác minh 9.2 không ảnh hưởng nội dung) → **62 PASS · 5 FAIL · 8 lỗi cứng trích dẫn trên 5 dashboard**, đều có sẵn TỪ TRƯỚC (đã xác nhận qua đối chiếu bản backup trước-reskin, không do 9.2 gây ra). KHÔNG tự đổi `decision`/`gradeLevel`/PMID — chỉ đo diện rộng rồi báo bác sĩ. | Báo cáo số dashboard/mục bị ảnh hưởng kèm trích nguyên văn; không tự sửa nội dung y khoa | — | `cc:done` — báo cáo đầy đủ: **①** `Uptodate_W29_20260713` ITEM-01 nghi tráo PMID 41824590 (trùng 22% từ khóa, tiêu đề thật là guideline dyslipidemia ACC/AHA 2026) **②** `CAP_ATS2025_20260628` ITEM-03 nghi tráo PMID 42127879 (trùng 14%, tiêu đề thật "2025 guideline updates for CAP") **③** `COPD_TimMachNoiTiet_20260709` — NẶNG NHẤT, 4 lỗi: ITEM-02 nghi tráo PMID 38762800 (trùng 22%, thật là RCT bisoprolol BICS), ITEM-11 sai năm/phiên bản PMID 23992515 (2013 vs khai 2008–2013), ITEM-16 nghi tráo PMID 39928303 (trùng 9%, thật là bài về thuốc hạ đường huyết và COPD), ITEM-20 nghi tráo PMID 41806208 (trùng 18%, thật là GOLD 2026) **④** `MachMauNao_DongMachCanh_20260610` ITEM-13 nghi tráo PMID 34153348 (**trùng 0% từ khóa — mức nghiêm trọng nhất**, tiêu đề thật là guideline SVS về bệnh mạch máu não ngoài sọ, hoàn toàn không liên quan) **⑤** `ViemKhopDangThap_20260610` ITEM-07 sai năm/phiên bản PMID 36357155 (2023 vs khai 2025/2021, phát hiện đầu tiên). Xem Sprint 10 để xử lý — cần bác sĩ quyết vì đụng nội dung trích dẫn lâm sàng |
| 9.3 | Dựng lại `EBM-Dashboards/derivatives/DAT-CANH-CHUNG-CU-MOI_*.md` — bản hiện tại (16/08) đã lỗi thời 8 ngày, ghi 123/168 trong khi số đo thật 24/08 là 114/157. `[tdd:skip:report-regen]` | File mới sinh ra khớp số đo `kiem_chung_cu_vuot_qua.py` chạy lại; KHÔNG tự đổi `decision`/`gradeLevel` nào | — | `cc:done` — `tools/dat_canh_chung_cu_moi.py --top 20` sinh `DAT-CANH-CHUNG-CU-MOI_2026-08-24.md`; quét 157 PMID đang apply → 114 mục có nguồn mới hơn (khớp đúng số đo audit trục ③); bản 16/08 giữ nguyên làm lịch sử, không xóa |
| 9.4 | Cập nhật CLAUDE.md gốc mục "Lệnh" — tài liệu hiện chỉ liệt kê G0/G3/G4/G8/G9 có `gN_quality_gate.py` riêng, thực tế CẢ 11 cổng G0→G10 đã có (xác nhận qua audit trục ①, tài liệu lạc hậu theo hướng TỐT hơn mô tả). `[tdd:skip:docs-only]` | Đoạn "Lệnh" liệt kê đủ G0-G10; tránh lập kế hoạch trùng lặp "xây quality gate cho G1/G2/G5/G6/G7/G10" trong tương lai vì tưởng chưa có | — | `cc:done` — thêm mục "AUDIT ĐA-AGENT G0-G10 24/08/2026" vào CLAUDE.md gốc (commit `0f1fa3c`), đính chính đủ 11 cổng + ghi lại phát hiện 9.1 + tóm tắt 4 trục còn lại |
| 9.5 | (Recommended, effort cao hơn) Mở rộng canary BH72 (`thu_dau_cuoi_cong_nghien_cuu.py`) để gọi qua đúng CLI `approve_gate.py --gate G2/G4/G8` thay vì gọi thẳng `evaluate_gN_quality()` — canary hiện chứng minh "logic tính điểm đúng" nhưng KHÔNG chứng minh "dây nối vào chữ ký thật đúng" (chính là khoảng trống mà 9.1 vừa vá). `[tdd:required]` | Canary mở rộng bắt được lỗi 9.1 nếu tái diễn (kiểm bằng đột biến: revert tạm 9.1 ⇒ canary đỏ) | 9.1 | `cc:todo` |

---

## Sprint 10 — Điều tra + sửa 8 lỗi trích dẫn phát hiện ở 9.6 (24/08, bác sĩ duyệt tiếp tục)

> Mở theo chỉ thị "tiếp tục hoàn thiện" của bác sĩ sau khi Sprint 9 báo cáo 8 lỗi cứng.
> 5 agent điều tra song song (1 agent/dashboard), mỗi agent PHẢI tự tra PMID qua công cụ
> thật rồi phân loại (A) báo động giả hay (B) tráo PMID thật trước khi được phép sửa —
> không cho sửa mù quáng theo đúng số báo lỗi.

| Task | Nội dung | DoD | Depends | Status |
|---|---|---|---|---|
| 10.1 | Điều tra + xử lý 8 lỗi cứng của 9.6 trên 5 dashboard. `[tdd:skip:content-fix-not-code]` | Verify độc lập lại cả 5 (không tin lời agent) PASS 0 lỗi cứng; KHÔNG đổi `pmid`/`doi`/`decision`/`gradeLevel` nào trong mọi case (A) | 9.6 | `cc:done` — **KẾT QUẢ BẤT NGỜ: CẢ 8/8 LỖI ĐỀU LÀ (A) BÁO ĐỘNG GIẢ, 0/8 là tráo PMID thật.** Mọi PMID/DOI đã tự tra qua PubMed E-utilities thật, khớp tuyệt đối nội dung item — chỉ sửa `references[]`/`source`/`dateVersion` cho đầy đủ/đúng trình bày, KHÔNG đổi bất kỳ `pmid`/`doi`/`decision`/`gradeLevel` nào. Chi tiết: Uptodate_W29 ITEM-01 — `source` viết tắt "ACC/AHA" thiếu 9 hiệp hội đồng thuận khác trong tên guideline dài, đã bổ sung tên đầy đủ. CAP_ATS2025 ITEM-03 — `references[0]` thiếu hẳn tiêu đề bài báo (3 item khác cùng nguồn có đủ), đã bổ sung. COPD_TimMachNoiTiet — 4/4 lỗi cùng nguyên nhân (item viết tiếng Việt nên heuristic đếm từ khóa tiếng Anh trong `references` không đủ) + ITEM-11 thêm lỗi trình bày `dateVersion:"2008–2013"` (khoảng năm) bị đọc nhầm năm đầu, sửa thành "2013 (tín hiệu ban đầu 2008 đã được giải quyết)". MachMauNao_DongMachCanh ITEM-13 (mức nghi ngờ cao nhất, trùng 0% từ khóa) — vẫn là báo động giả: nội dung khớp gần nguyên văn abstract PMID 34153348, chỉ do `references` rút gọn thiếu tiêu đề. ViemKhopDangThap ITEM-07 — xác nhận độc lập đúng lỗi gõ nhầm năm "2025"→"2022". Verify chéo lần cuối (tôi tự chạy, không tin lời agent): cả 5/5 dashboard PASS 0 lỗi cứng đồng thời trong cùng 1 lượt. Đang quét lại toàn kho 67 dashboard lần 2 để xác nhận không sinh lỗi mới (xem 10.2). |
| 10.2 | **[Bác sĩ duyệt: "Đề xuất và chỉnh sửa một cách tốt nhất" — đã triển khai]** Sửa `EBM-Dashboards/tools/verify_dashboard.py` để phân biệt "references[] thiếu tiêu đề gốc" (KHÔNG đủ dữ liệu để phán, không phải bằng chứng tráo) khỏi "nghi tráo PMID thật" (entry đủ dài mà vẫn không khớp) — dùng bất biến toán học về ĐỘ DÀI (entry ngắn hơn tiêu đề thật thì CHẮC CHẮN không chứa trọn tiêu đề), không phải suy đoán. `[tdd:required]` | Test mới mutation-tested PASS; **KHÔNG nới lỏng mức chặn** — `--strict-sources` vẫn chặn ở CẢ hai nhánh, chỉ đổi thông điệp cho đúng bản chất; case biên/mơ hồ (entry dài do nhiều tác giả nhưng thực chất vẫn thiếu tiêu đề) cố ý nghiêng về AN TOÀN (giữ "nghi tráo") thay vì đoán liều | 10.1 | `cc:done` — thêm 2 hàm `_find_reference_entry_for_pmid()`/`_reference_entry_missing_title()` + tách `_title_mismatch_message()` (dễ test không cần gọi mạng) trong `verify_dashboard.py`; 10 test mới trong `tools/test_verify_dashboard_source_gate.py` (31/31 PASS cả kho); **kiểm bằng đột biến**: tắt nhánh mới ⇒ đúng test đỏ, khôi phục ⇒ xanh lại; verify chéo 5 dashboard Sprint 10 vẫn PASS 0 lỗi cứng với code mới; 1 test tự bắt được giới hạn thật của thiết kế (entry dài do nhiều tác giả/tạp chí không viết tắt có thể trùng ngẫu nhiên độ dài tiêu đề) — sửa lại TEST cho đúng hành vi AN TOÀN cố ý, không nới code. |
| 10.3 | Quét sạch toàn kho 67 dashboard lần cuối (`--online --strict-sources`), không có gì can thiệp file trong lúc chạy — xác nhận không hồi quy sau 10.1+10.2. `[tdd:skip:verification-only]` | 67/67 PASS đồng thời trong 1 lượt duy nhất | 10.1, 10.2 | `cc:done` — **67/67 PASS · 0 FAIL · 0 lỗi cứng trong toàn bộ kho.** Lượt quét đầu tiên (bxsny1t6z) bị hủy giữa chừng vì trùng thời điểm sửa/đột biến-kiểm-thử `verify_dashboard.py` cho 10.2 — không dùng kết quả đó. Lượt quét thứ hai chạy hoàn toàn sạch (xác nhận file không còn dấu vết đột biến + 31/31 test PASS trước khi chạy) — kết quả 67/67 PASS là bằng chứng cuối cùng, đáng tin cậy. Kho dashboard giờ sạch tuyệt đối qua cổng liêm chính nghiêm ngặt nhất. |

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

- **Updated at**: 2026-08-23 (harness-loop, Sprint 7 hoàn tất 6/6 + CI xanh lần đầu sau 5 lần đỏ liên tiếp)
- **Last session owner**: Claude Code
- **Branch**: feat/r1-1-2-design-gap-remediation
