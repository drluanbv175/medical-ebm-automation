# Cổng triển khai giám sát chứng cứ ngoại trú

Hệ thống chỉ được gắn nhãn `READY_FOR_CONTROLLED_DEPLOYMENT` khi đồng thời có:

1. Kiểm kỹ thuật offline và canary online PASS.
2. Hai lịch tuần/tháng đã chạy thật, ghi runtime status PASS và còn mới.
3. Kênh cảnh báo đã gửi thử thành công.
4. Restore từ backup đã drill và hash khớp.
5. Ít nhất hai chu kỳ shadow không lỗi, không auto-apply.
6. Bác sĩ mở nguồn và duyệt tối thiểu năm mẫu, sau đó bác sĩ và vận hành cùng phê duyệt.

Chạy cổng đầy đủ:

```bash
~/.ebm-venv/bin/python tools/verify_evidence_surveillance_deployment.py --online
```

Canary không ghi DB/Hub:

```bash
bash scripts/weekly_safety.sh --canary
bash scripts/monthly_update.sh --canary
```

`UAT_EVIDENCE.json` khởi tạo ở trạng thái `PENDING`. Agent không được tự đổi các
trường phê duyệt thành PASS. PARTIAL/FAIL phải chặn bridge sang Hub; hệ thống chỉ tạo
ứng viên để bác sĩ thẩm định, không tự đổi thực hành.

**Cần bác sĩ kiểm chứng.**
