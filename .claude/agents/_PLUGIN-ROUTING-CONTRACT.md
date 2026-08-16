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
| **pubmed-search MCP** (`pubmed-quick-search` · `pubmed-systematic-search`) | `tra-cuu-chung-cu` / `thu-thu-tai-lieu` | DISCOVERY · METADATA · SEARCH_PLAN | Chính danh hoá đường tra dùng nhiều nhất kho (1322 lượt); kết quả tra vẫn qua thứ bậc nguồn của owner |

| Bioinformatics chuyên sâu | `specialist-escalation` | Bio Research | Ngoài vùng phủ lõi; cần chuyên gia phù hợp |

Chi tiết allowlist từng worker/stage nằm trong JSON canonical, không sao chép lại vào agent.

### 2-bis. Provider ĐƯỢC BIẾT nhưng KHÔNG bind worker (rà 2026-08-10)

Registry khai `unbound_providers`: `aipoch-medical-research`, `openmed-skills`, `medsci-project`,
`meta-pipe`, `pubmed-search`, `mattpocock-skills`, `humanizer`, `healthcare`. Chúng **đang bật**
trong `~/.claude/settings.json` nên vẫn hiện trong danh sách skill mỗi phiên, nhưng **không được
bind vào bất kỳ capability nào** ⇒ `resolve()` trả `blocked_requests`, kể cả khi bị gọi đích danh.

Lý do khai tường minh thay vì để "tên lạ → chặn": các plugin này chiếm phần lớn bề mặt ứng cử
(riêng `aipoch` đóng góp 47/53 công cụ mang chữ "thiết kế nghiên cứu", 21/25 "viết bản thảo",
15/21 "chọn tạp chí"). Quét 2712 transcript cho thấy **0 lượt gọi** cho aipoch, openmed,
medsci-project, mattpocock, pubmed-search — tính đến nay chúng làm tăng bề mặt ứng cử mà chưa
tạo ra đóng góp đo được. `healthcare` là ngoại lệ về mặt dữ liệu: MCP PubMed của nó có 310 lượt
gọi thật, nhưng đó là **truy cập dữ liệu**, không phải worker của capability có cổng.

⚠️ **"0 lượt gọi" nói về TẦN SUẤT DÙNG, KHÔNG nói plugin hỏng.** Đã kiểm ngược lại 10/08:
aipoch có 605/605 SKILL.md hợp lệ, manifest khai đủ, nạp bình thường mỗi phiên — **đang chạy
tốt**. Không-bind ở đây là quyết định ĐIỀU PHỐI (giữ việc có cổng cho chủ duy nhất), không phải
phán quyết về chất lượng plugin. Một plugin có thể chưa được gọi chỉ vì khó tìm giữa 846 skill.

Muốn dùng một plugin trong nhóm này cho việc có cổng: bác sĩ phải **thêm binding có chủ đích**
vào JSON canonical rồi chạy lại `verify_plugin_orchestration.py`. Không tự động, không ngầm định.

⚠️ **Giới hạn phải nhớ:** cơ chế `resolve()` ở đây chỉ chạy trong `tools/orchestrator/` — vốn
**tách rời khỏi luồng agent thật**. Luật ràng buộc luồng thật nằm ở bảng định tuyến trong
`CLAUDE.md` (mục "Định tuyến khi nhiều công cụ cùng nhận một việc"). Sửa một nơi phải sửa cả hai.

## 3. Thuật toán định tuyến bắt buộc

1. Phân loại intent bằng `tools/orchestrator/intent.py`.
2. Phân giải capability bằng `PluginOwnershipRegistry.resolve_for_intent()`.
3. Ghi checkpoint `plugin_routing`: capability, owner, worker được phép, cổng và rule.
4. Owner dựng plan. Plugin chỉ được gọi ở `allowed_stages` và phải trả provenance envelope.
5. Owner hợp nhất, loại trùng, giải quyết mâu thuẫn và giữ nguyên nhãn bất định.
6. `tham-dinh-dau-ra` kiểm nguồn, PII, quyền sở hữu và cổng; sau đó mới bàn giao.
7. Capability không biết hoặc worker ngoài allowlist → `BLOCKED_UNKNOWN_CAPABILITY` hoặc
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
