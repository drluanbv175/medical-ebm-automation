# Gói quyết định hoàn thiện đề cương — hai-long-benh-nhan-C1a-BVQY175

**Mức hiện tại:** STRUCTURE_COMPLETE_WITH_OPEN_DECISIONS.  
**Bao phủ protocol:** 1/20 thành phần đủ dữ liệu dự thảo.

## Quyết định khoa học/hành chính còn thiếu

| Mã | Nội dung cần xác nhận | Trường còn thiếu | Người quyết định | Hành động |
|---|---|---|---|---|
| D02 | Câu hỏi nghiên cứu | `question.text` | Chủ nhiệm đề tài | Bổ sung/xác nhận trong study_meta.json rồi chạy lại G10. |
| D03 | Mục tiêu chính/cụ thể | `objectives.general | objectives.specific` | Chủ nhiệm đề tài | Bổ sung/xác nhận trong study_meta.json rồi chạy lại G10. |
| D05 | Bối cảnh và thời gian | `design.setting, design.period` | Chủ nhiệm/đơn vị | Bổ sung/xác nhận trong study_meta.json rồi chạy lại G10. |
| D06 | Quần thể và tiêu chuẩn chọn/loại | `population.description, population.inclusion, population.exclusion` | Chủ nhiệm đề tài | Bổ sung/xác nhận trong study_meta.json rồi chạy lại G10. |
| D07 | Phương pháp chọn mẫu/tuyển mẫu | `population.sampling | population.recruitment` | Chủ nhiệm đề tài | Bổ sung/xác nhận trong study_meta.json rồi chạy lại G10. |
| D08 | Kết cục chính có định nghĩa, nguồn và thời điểm đo | `outcomes.primary.name, outcomes.primary.definition, outcomes.primary.source, outcomes.primary.timepoint` | Chủ nhiệm + thống kê viên | Bổ sung/xác nhận trong study_meta.json rồi chạy lại G10. |
| D10 | Nguồn giả định cỡ mẫu | `sample_size.assumptions_source | sample_size.sampling_sufficiency` | Thống kê viên/chủ nhiệm | Bổ sung/xác nhận trong study_meta.json rồi chạy lại G10. |
| D11 | Công cụ hoặc nguồn dữ liệu | `data_collection.instrument.name | data_collection.source` | Chủ nhiệm + quản lý dữ liệu | Bổ sung/xác nhận trong study_meta.json rồi chạy lại G10. |
| D12 | Phân tích chính định trước | `analysis.primary_method` | Thống kê viên | Bổ sung/xác nhận trong study_meta.json rồi chạy lại G10. |
| D13 | Kế hoạch xử lý dữ liệu thiếu | `analysis.missing_data | data_governance.missing_data` | Thống kê viên | Bổ sung/xác nhận trong study_meta.json rồi chạy lại G10. |
| D14 | Sai lệch và biện pháp giảm thiểu | `bias.risks, bias.mitigations` | Chủ nhiệm + phương pháp | Bổ sung/xác nhận trong study_meta.json rồi chạy lại G10. |
| D15 | Consent, lợi ích-nguy cơ và bảo mật | `ethics.consent | population.consent, ethics.benefit_risk, ethics.privacy` | Chủ nhiệm + Hội đồng đạo đức | Bổ sung/xác nhận trong study_meta.json rồi chạy lại G10. |
| D16 | Tiến độ, nhân lực và kinh phí | `resources.timeline, resources.team, resources.budget` | Chủ nhiệm/đơn vị | Bổ sung/xác nhận trong study_meta.json rồi chạy lại G10. |

## Vấn đề ngữ nghĩa

| Mức | Mã | Vị trí | Vấn đề |
|---|---|---|---|
| — | — | — | Chưa phát hiện mâu thuẫn có cấu trúc. |

## Checklist đặc thù thiết kế

- Khung chọn mẫu và xử lý không đáp ứng
- Công cụ khảo sát/PROM, bản quyền và quy tắc chấm điểm khi áp dụng
- STROBE; CROSS/COSMIN/RECORD khi phù hợp

> Hệ thống không tự điền IRB, chữ ký, giả định cỡ mẫu, bản quyền công cụ hoặc quyết định của chủ nhiệm. Cần bác sĩ kiểm chứng.
