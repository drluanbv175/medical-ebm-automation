# Clinical Production Control Plane

- Generated: `2026-08-13T07:40:57+00:00`
- Overall status: `CONTROLLED_AUTOMATION_READY_WITH_HUMAN_GATES`
- Fail count: `0`
- Human gates: `2`
- Offline controlled automation available: `True`
- Clinical production allowed: `False`
- Real patient data allowed: `False`
- Auto-apply allowed: `False`

| Check | Status | Proves | Limitation | Human action |
|---|---|---|---|---|
| CP1 Tự sửa chữa có trần và fail-closed | PASS | Retry loop phân loại lỗi tự sửa/leo thang/chờ input thật, không vòng lặp vô hạn. | Không tự sửa lỗi cần người thật như PII, sai guideline nguy hiểm, IRB, SAP hoặc dữ liệu thật. | Bác sĩ/phụ trách phải xử lý các lỗi ESCALATE_HARD và WAIT_INPUT. |
| CP2 Tự sinh agent có duyệt | HUMAN_GATE | Agent sinh tự động luôn có nhãn PROPOSED, guardrail, PMID/DOI rule và disclaimer. | Agent mới chỉ là bản đề xuất; không tự thành agent production hoặc tự vượt Cổng A/B/G. | Bác sĩ duyệt nội dung/nguồn trước khi bỏ nhãn PROPOSED hoặc dùng chính thức. |
| CP3 Điều phối lâm sàng EBM có checkpoint và guardrail cuối | PASS | Nhạc trưởng lâm sàng có Cổng A/B, completeness C1-C9 và máy kiểm không cho qua cổng khi còn lỗi đỏ. | Không thay bác sĩ đánh giá ca bệnh thật; chỉ kiểm khung điều phối và checkpoint. | Bác sĩ vẫn phải duyệt Cổng A trước khi áp dụng cho bệnh nhân và Cổng B trước khi ghi sổ cái. |
| CP4 Pipeline cập nhật chứng cứ lâm sàng được nối vào kiểm toàn hệ | PASS | Dashboard Evidence Workbench, thư viện, phái sinh và sync hub có verifier trong upgrade cycle. | Dashboard thật vẫn cần verify online, rà nguồn, an toàn thuốc và bác sĩ duyệt trước khi áp dụng. | Bác sĩ duyệt nguồn/khuyến cáo trước khi chuyển thẻ sang áp dụng. |
| CP5 Ranh giới production và dữ liệu thật vẫn fail-closed | HUMAN_GATE | Control-plane có thể tự động hóa việc chuẩn bị/kiểm tra nhưng không tự bật dữ liệu bệnh nhân thật. | Production thật cần UAT, security/legal review, backup/restore drill, actor thật và go-live signoff. | Hoàn tất evidence package và phê duyệt thật trước bất kỳ dữ liệu bệnh nhân thật nào. |

Cần bác sĩ kiểm chứng. Đây là kiểm control-plane kỹ thuật/offline; không thay UAT, phê duyệt bảo mật/pháp lý, thẩm định lâm sàng hoặc quyết định điều trị.
