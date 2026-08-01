# HỢP ĐỒNG ĐIỀU PHỐI PLUGIN — một owner, nhiều worker, không vượt cổng

> Sổ hạ tầng (`_*`), không phải agent. Nguồn máy đọc được ở workspace gốc:
> `tools/orchestrator/plugin_ownership_registry.json`. Mọi sửa đổi phải đồng thời qua
> `python tools/verify_plugin_orchestration.py` và đồng bộ Claude Code ↔ Codex.

## Bất biến

1. Mỗi capability chỉ có **một owner nội bộ**. Owner chọn worker, hợp nhất kết quả, xử lý
   mâu thuẫn, gọi guardrail và quyết định trạng thái bàn giao.
2. Plugin chỉ là worker. `/ars-full` là `stage_worker`, không thay `dieu-phoi-nghien-cuu`;
   plugin lâm sàng không thay `dieu-phoi-lam-sang`.
3. Plugin không được ghi/phê duyệt Cổng A/B hoặc G2/G4/G5/G8/G9/G10; không được ghi vào
   approval ledger, seal, `study_meta.json` hay hàng `apply` trong EBM_MASTER.
4. Worker chỉ được dùng ở allowlist/stage trong registry, phải có provenance và phải qua
   `tham-dinh-dau-ra`. Worker ngoài allowlist bị chặn, không fallback sang pipeline tự trị.
5. Khi worker mâu thuẫn, owner đối chiếu nguồn/phương pháp/phạm vi/độ mới; chưa giải được
   thì ghi PARTIAL và chuyển đúng người duyệt, không biểu quyết theo đa số plugin.

## Owner canonical

| Capability | Owner duy nhất | Plugin chỉ làm gì |
|---|---|---|
| Nghiên cứu G0–G10 | `dieu-phoi-nghien-cuu` + `run_pipeline.py` | Tìm, lập dàn ý, soạn nháp, phản biện |
| Ca lâm sàng | `dieu-phoi-lam-sang` | Khung EBM, truy xuất, giao tiếp nháp |
| Cập nhật chứng cứ | `cap-nhat-guideline` + pipeline dashboard/hub | Tìm, dựng dashboard/phái sinh nháp |
| Truy xuất chứng cứ | `tra-cuu-chung-cu` | RAG/discovery/metadata |
| Thẩm định | `tham-dinh-grade-nnt` hoặc agent chuyên trách theo thiết kế | Critique/GRADE/EtD nháp |
| Trích dẫn | `kiem-chung-trich-dan` | Metadata/dedup/audit nháp |
| Thống kê | `phan-tich-thong-ke`; cỡ mẫu thuộc `co-mau-nghien-cuu` | Tính/soát nháp theo SAP |
| Bình duyệt | `binh-duyet` | Critique/rebuttal audit; không ký G8 |
| An toàn kê đơn | `ke-don-an-toan`; kháng đông thuộc `quan-ly-khang-dong` | Soát nháp; không mở Cổng A |

## Provenance envelope tối thiểu

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

Registry và verifier canonical chạy từ thư mục cha `Claude AI`:

```bash
python ../tools/verify_plugin_orchestration.py
python ../tools/run_orchestrator.py --resolve-capability research_lifecycle --json
```

**Cần bác sĩ kiểm chứng.**
