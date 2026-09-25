# HỢP ĐỒNG ĐIỀU PHỐI PLUGIN — một owner, nhiều worker, không vượt cổng

> Sổ hạ tầng (`_*`), không phải agent. Nguồn máy đọc được:
> `tools/orchestrator/plugin_ownership_registry.json`. Mọi sửa đổi phải đồng thời qua
> `python tools/verify_plugin_orchestration.py` và đồng bộ Claude Code ↔ Codex.

## 1. Bất biến

1. **Mỗi capability chỉ có MỘT owner.** Owner chịu trách nhiệm chọn worker, hợp nhất kết quả,
   xử lý mâu thuẫn, gọi guardrail và quyết định trạng thái bàn giao.
2. **Plugin chỉ là worker.** Plugin không tự trở thành nhạc trưởng vì người dùng gọi tên plugin
   hoặc slash command. Đặc biệt, `/ars-full` chỉ là `stage_worker` trong G0/G1/G7/G8/G9;
   nó KHÔNG thay `dieu-phoi-nghien-cuu` và KHÔNG sở hữu G0–G10.
3. **Không biểu quyết theo đa số plugin.** Khi hai worker mâu thuẫn, owner đối chiếu nguồn,
   phương pháp, phạm vi và độ mới; chưa giải được thì ghi mâu thuẫn + PARTIAL và chuyển người duyệt.
4. **Plugin không mở cổng người.** Không plugin nào được ghi/phê duyệt Cổng A/B hoặc
   G2/G4/G5/G8/G9/G10; không được ghi vào approval ledger, seal, `study_meta.json` hay hàng
   `apply` trong EBM_MASTER.
5. **Đầu ra worker chưa phải đầu ra hệ thống.** Mọi đầu ra plugin phải có provenance, được owner
   chuẩn hóa, rồi qua `tham-dinh-dau-ra`; thiếu provenance hoặc gọi ngoài allowlist → fail-closed.
6. **Yêu cầu đích danh plugin không đổi owner.** Hệ có thể ưu tiên worker được yêu cầu nếu worker
   nằm trong allowlist của capability; ngoài allowlist thì báo bị chặn, không lặng lẽ gọi.

## 2. Quyền sở hữu canonical

| Capability | Owner duy nhất | Plugin worker tiêu biểu | Ranh giới |
|---|---|---|---|
| Vòng đời nghiên cứu G0–G10 | `dieu-phoi-nghien-cuu` + `run_pipeline.py` | ARS full/plan/outline; `nghien-cuu-y-khoa-chuan-quoc-te` | Sáu cổng cứng chỉ đóng bằng ledger + đúng role |
| Ca lâm sàng ngoại trú | `dieu-phoi-lam-sang` | `kham-ngoai-tru-ebm`, `giao-tiep-quyet-dinh-soap` | Dừng Cổng A/B; không tự áp dụng |
| Cập nhật chứng cứ | `cap-nhat-guideline` + pipeline dashboard/hub | `cap-nhat-chung-cu-y-khoa`, `quan-ly-cap-nhat-ebm`, `EBM-MASTER` | Worker chỉ dựng nháp/hàng chờ duyệt |
| Truy xuất chứng cứ | `tra-cuu-chung-cu` | `clinical-evidence-rag`, `paper-lookup`, `research-lookup` | Owner áp thứ bậc nguồn + PARTIAL |
| Thẩm định chứng cứ | `tham-dinh-grade-nnt` | `tham-dinh-chung-cu-grade-nnt`, `peer-review` | Không tự gán GRADE/khuyến cáo |
| Tìm/tổng quan y văn | `thu-thu-tai-lieu` | ARS lit-review, `literature-review` | Worker không quyết định research gap cuối |
| Liêm chính trích dẫn | `kiem-chung-trich-dan` | ARS citation-check, `citation-management` | PMID/DOI phải phân giải; kiểm rút bài |
| Thiết kế đề cương | `thiet-ke-nghien-cuu` | ARS plan/outline | Trục cổng luôn theo G0–G10 nội bộ |
| Phân tích thống kê | `phan-tich-thong-ke` + `run_stats_analysis.py` | `statistical-analysis` | Chỉ chạy trên SAP + dataset đã khóa |
| Viết bản thảo | `viet-ban-thao` | ARS abstract/revision, `scientific-writing` | Worker không xác nhận authorship/COI/AI |
| Bình duyệt | `binh-duyet` | ARS reviewer/rebuttal-audit | Worker không phải chữ ký phản biện độc lập G8 |
| An toàn kê đơn | `ke-don-an-toan` | `ke-don-an-toan-benh-man` | Dừng Cổng A; bác sĩ quyết định |
| Xây phần mềm | workflow kỹ thuật của repo | `claude-code-harness` | Worker kỹ thuật không sở hữu quyết định y khoa/nghiên cứu |
| Cỡ mẫu / power (cổng **G3**) | `co-mau-nghien-cuu` → `run_g3_auto.py` + `g3_quality_gate.py` | `calc-sample-size`, `sample-size-power-calculator`, `sample-size-and-power-planning-assistant` | **5 skill plugin tự nhận làm được.** Worker chỉ ra con số nháp; N của đề tài thật phải qua cổng G3 — effect size KHÔNG NGUỒN thì cổng chặn, đó là thiết kế |
| Nộp bài · COI · khai AI (cổng **G9**) | `nop-bai-phan-hoi` + `g9_quality_gate.py` | `fill-icmje-coi`, `find-journal`, `cover-letter-drafter`, `target-journal-matcher` | **7 skill plugin tự nhận làm được.** Worker soạn nháp; khai COI và khai dùng AI là lời TỰ KHAI có chữ ký của chủ nhiệm, worker không ký thay |
| Khử định danh · PII (cổng **G5**) | `quan-ly-du-lieu` + luật KHÔNG PII | `deidentify-a-dataset`, `deidentifying-clinical-text`, `auditing-deidentification-runs` | **6 skill plugin tự nhận làm được — nhóm nguy hiểm nhất.** Dữ liệu bệnh nhân KHÔNG được rời máy; worker chạy cục bộ thì được dùng, nhưng quyết định «đã đủ khử định danh để phát hành» thuộc chủ |

## 2b. Worker CÓ HỢP ĐỒNG bổ sung 16/08/2026 (bác sĩ duyệt phương án B — «plugin thành worker chính thức»)

Bối cảnh số đo: 846 skill plugin chỉ 53 lượt gọi/2712 phiên trong khi MCP 2528 lượt — plugin
trước nay chỉ bị CHẶN khỏi việc có cổng, chưa được DÙNG chủ động. Ba cụm dưới đây được khai
chính danh vào `plugin_ownership_registry.json`; mọi bất biến mục 1 giữ nguyên (owner hợp nhất,
đầu ra qua `tham-dinh-dau-ra`, trích dẫn từ worker PHẢI qua `check_citation_retraction` + sổ
xác minh trước khi vào kho):

| Cụm worker mới | Chủ | Phạm vi | Ghi chú |
|---|---|---|---|
| **aipoch 8 planner đặc thù** (MR · FAERS · đơn tế bào · đa omics · tái định vị thuốc · QTL · độc chất mạng · biomarker tiên lượng) | `thiet-ke-nghien-cuu` (dưới nhạc trưởng `dieu-phoi-nghien-cuu`) | G0–G1, `specialty_planning_worker` | Đây là 8 mảng hệ agent KHÔNG có; bản kế hoạch plugin trả về phải được chủ chuẩn hoá theo khung G0–G10 rồi mới thành artifact |
| **meta-pipe từng bước** (`ma-search-bibliography` · `ma-screening-quality` · `ma-meta-analysis`) | `tong-quan-y-van` / `meta-phan-tich` | SEARCH_PLAN · SCREENING_DRAFT · SYNTHESIS_DRAFT, `pipeline_step_worker` | CỐ Ý không khai `ma-end-to-end` làm worker — nó tự điều phối trọn chuỗi nên dễ tranh owner; bác sĩ gọi đích danh thì vẫn chạy DƯỚI owner, không thay owner |
| **pubmed-search MCP** (`pubmed-quick-search` · `pubmed-systematic-search`) | `tra-cuu-chung-cu` / `thu-thu-tai-lieu` | DISCOVERY · METADATA · SEARCH_PLAN | Chính danh hoá đường tra dùng nhiều nhất kho (1322 lượt); kết quả tra vẫn qua thứ bậc nguồn của owner· ĐÃ CANARY 16/08/2026: lượt unified_search thật đầu tiên (GONB-migraine-ED) trả đúng AHS 2025 đang dùng + phát hiện RCT 2025 mới (PMID 41100185) làm ứng viên — dây worker→owner→candidate hoạt động |

| Bioinformatics chuyên sâu | `specialist-escalation` | Bio Research | Ngoài vùng phủ lõi; cần chuyên gia phù hợp |

Chi tiết allowlist từng worker/stage nằm trong JSON canonical, không sao chép lại vào agent.

### 2-bis. Provider biết đến nhưng chưa bind worker (rà 2026-09-01)

Registry chỉ còn năm provider `unbound_providers`: `openmed-skills`, `medsci-project`,
`mattpocock-skills`, `humanizer`, `healthcare`. AIPOCH, Meta-pipe và PubMed đã có binding
chính danh tại mục 2b nên CẤM đồng thời nằm trong danh sách unbound; verifier phải fail khi
một provider vừa bound vừa unbound.

Provider unbound vẫn có thể hiện trong runtime nhưng không được tự chen vào capability có cổng.
Muốn dùng làm worker chính thức phải thêm binding có owner, stage và điều kiện chọn rõ ràng vào
JSON canonical, sau đó chạy `verify_plugin_orchestration.py`.

**Giới hạn thực thi:** `tools/orchestrator/` nay định tuyến phân cấp tới từng agent/bước, lọc
worker chuyên biệt bằng cue, kiểm `SKILL.md` thật và ghi `LOCAL_FALLBACK` khi thiếu plugin.
Nó vẫn không tự gọi LLM bên ngoài nếu runtime không cung cấp executor; trong Claude/Codex,
nhạc trưởng thực hiện worker qua skill/tool đang khả dụng của phiên. Không được biến plan/dry-run
thành tuyên bố "đã chạy".

## 3. Thuật toán định tuyến bắt buộc

1. Phân loại intent bằng `tools/orchestrator/intent.py`.
2. Phân giải capability bằng `PluginOwnershipRegistry.resolve_for_intent()`.
3. Tại mỗi bước/agent, phân giải capability hẹp hơn; chỉ chọn worker chuyên biệt khi cue khớp.
4. Kiểm worker thật trong đúng provider; thiếu → `LOCAL_FALLBACK`, không giả vờ đã gọi plugin.
5. Ghi checkpoint `plugin_routing`: capability, owner, worker, khả dụng, cổng và rule.
6. Owner dựng plan. Plugin chỉ được gọi ở `allowed_stages` và phải trả provenance envelope.
7. Owner hợp nhất, loại trùng, giải quyết mâu thuẫn và giữ nguyên nhãn bất định.
8. `tham-dinh-dau-ra` kiểm nguồn, PII, quyền sở hữu và cổng; lỗi sửa được re-route tối đa 3 vòng.
9. Capability không biết hoặc worker ngoài allowlist → `BLOCKED_UNKNOWN_CAPABILITY` hoặc
   `READY_WITH_BLOCKED_WORKERS`; không fallback sang pipeline plugin tự trị.

## 4. Provenance envelope tối thiểu của worker

```json
{
  "capability": "research_lifecycle",
  "owner": "dieu-phoi-nghien-cuu",
  "worker_provider": "academic-research-skills",
  "worker_unit": "source-command-ars-full",
  "stage": "G7",
  "generated_at": "ISO-8601",
  "source_ids": ["PMID/DOI/URL chính thức"],
  "limitations": [],
  "requested_human_gate_release": false
}
```

Thiếu envelope không tự biến nội dung thành sai, nhưng owner phải gắn `PROVENANCE_MISSING`,
không cho nội dung đó mở cổng hoặc trở thành kết luận độc lập.

## 5. Kiểm và vận hành

```bash
python tools/run_orchestrator.py --plugins
python tools/run_orchestrator.py --resolve-capability research_lifecycle --json
python tools/verify_plugin_orchestration.py
python tools/run_orchestrator.py --validate
python tools/sync_agents_to_codex.py --check
```

Pre-commit và `upgrade_verify.py` phải fail khi registry, doctrine, flow, mirror hoặc sáu cổng
nghiên cứu trôi lệch. Plugin có thể vắng trong một phiên; khi đó owner tiếp tục bằng agent/công cụ
nội bộ hoặc ghi PARTIAL, không đổi owner.

**Cần bác sĩ kiểm chứng.**
