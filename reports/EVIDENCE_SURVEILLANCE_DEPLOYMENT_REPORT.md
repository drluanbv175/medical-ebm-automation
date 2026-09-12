# Evidence Surveillance Deployment Verification

- Generated: `2026-09-02T21:25:24+00:00`
- Deployment status: `BLOCKED_FOR_DEPLOYMENT`
- Deployment allowed: `False`
- Online canary: `True`
- Failures / human gates: `1` / `1`

| ID | Cổng | Pha | Trạng thái | Bằng chứng | Giới hạn |
|---|---|---|---|---|---|
| ESD01 | Hợp đồng triển khai | static | PASS | schema=1.0.0; missing=[]; mode=candidate_only_doctor_review_required | Contract chứng minh ranh giới và điều kiện release, không chứng minh runtime đã chạy thật. |
| ESD02 | Đồng bộ scanner skill/runtime | static | PASS | files=3/3; hashes=1; missing=[]; unreadable=[] | Hash đồng nhất không thay xác minh nguồn online. |
| ESD03 | Runtime fail-closed | static | PASS | đủ marker | Kiểm marker được bổ sung bằng test hành vi; không tự coi marker là UAT. |
| ESD04 | Pipeline Evidence Workbench offline | static | PASS | Markdown: <WORKSPACE>/reports/CLINICAL_EVIDENCE_UPDATE_PIPELINE.md / JSON: <WORKSPACE>/reports/CLINICAL_EVIDENCE_UPDATE_PIPELINE.json / Cần bác sĩ kiểm chứng. Đây là kiểm chứng kỹ thuật/offline của pipeline cập nhật chứng cứ, không thay xác minh online, rà an toàn thuốc hoặc quyết định lâm sàng. | Fixture offline không chứng minh PMID/DOI phân giải được tại thời điểm triển khai. |
| ESD05 | Scheduler launchd | static | PASS | claude_task:thu-thap-tuan-an-toan-thuoc; claude_task:cap-nhat-thang-ebm; com.medicalebm.weeklysafety:legacy_retired; com.medicalebm.monthlyupdate:legacy_retired | Đăng ký lịch (Claude task/launchd) chưa chứng minh một chu kỳ đã chạy trọn thành công. |
| ESD06 | Canary nguồn online | online | PASS | pubmed:found=True,health=ok; europepmc:found=True,health=ok; crossref:found=True,health=ok; openfda:found=True,health=ok | Canary chỉ kiểm định danh cố định; không thay rà toàn bộ nguồn của từng chủ đề. |
| ESD07 | Scanner PubMed online | online | PASS | status=PASS; topics=2; failed=0; candidates=2; errors=[] | Hai query canary không thay độ phủ toàn watchlist hoặc thẩm định Track A. |
| ESD08 | Dashboard strict source online | online | PASS | overall=PASS; online=True; dashboard_gate=PASS | Fixture online không thay double-review của mẫu nội dung lâm sàng thật. |
| ESD09 | Lịch sử runtime tuần/tháng | runtime | PASS | weekly:status=PASS,age=1.8d; monthly:status=PASS,age=1.4d | Cần ít nhất các lượt chạy thật còn mới; canary thủ công không thay lịch sử này. |
| ESD10 | Cấu hình kênh cảnh báo | runtime | FAIL | email_ready=False; webhook_ready=False | Chỉ kiểm cấu hình có mặt, UAT vẫn phải chứng minh gửi/nhận thật. |
| ESD11 | UAT và phê duyệt | human | HUMAN_GATE | valid_source_samples=0; missing=['SOURCE_SAMPLE_REVIEW', 'SCHEDULER_TRIGGER', 'ALERT_DELIVERY', 'ROLLBACK_RESTORE', 'SHADOW_RUN', 'DOCTOR_APPROVAL', 'OPERATIONS_APPROVAL'] | Đây là cổng người thật; agent chỉ kiểm bằng chứng, không tự ký hoặc tự điền PASS. |

> Cần bác sĩ kiểm chứng. Cổng này chỉ cho phép triển khai chế độ ứng viên; không tự áp dụng lâm sàng và không dùng dữ liệu bệnh nhân thật.
