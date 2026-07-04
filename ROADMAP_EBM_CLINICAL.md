# LỘ TRÌNH XÂY DỰNG HỆ THỐNG CẬP NHẬT CHỨNG CỨ LÂM SÀNG
Cập nhật: 2026-07-03 | Tác giả: EBM Copilot + Bác sĩ Luân

---

## MỤC TIÊU CUỐI CÙNG
> Khi bác sĩ bắt đầu giờ khám sáng, hệ thống đã tự động:
> 1. Tổng hợp cập nhật guideline mới nhất cho 10 bệnh lý thường gặp
> 2. Gửi bản tin EBM sáng qua Dispatch/iPhone
> 3. Tại mỗi ca khám, có thể tra cứu tức thì khuyến cáo hiện hành
> 4. Cảnh báo nếu thuốc đang dùng có cập nhật an toàn mới

---

## PHASE 1 — NỀN TẢNG KNOWLEDGE PACKS (Tuần 1-2)
**Ai thực hiện:** EBM Copilot (tôi làm ngay trong session này)

### Bước 1.1 — Knowledge packs 5 bệnh lý ưu tiên
| # | Bệnh lý | Guideline chính | Trạng thái |
|---|---------|----------------|-----------|
| 1 | Tăng huyết áp | ESC/ISH 2023, WHO 2021 | ✅ Draft có sẵn |
| 2 | Đái tháo đường type 2 | ADA 2025, IDF 2023 | 🔨 Đang xây |
| 3 | Rối loạn lipid máu | ESC/EAS 2024 | 🔨 Đang xây |
| 4 | Suy tim | ESC 2024, AHA/ACC 2022 | ⏳ Tiếp theo |
| 5 | Bệnh thận mạn | KDIGO 2024 | ⏳ Tiếp theo |
| 6 | COPD | GOLD 2025 | ⏳ Sau |
| 7 | Gout/Tăng acid uric | ACR 2024 | ⏳ Sau |
| 8 | Rung nhĩ | ESC 2024 | ⏳ Sau |
| 9 | Loãng xương | IOF 2023 | ⏳ Sau |
| 10 | Suy giáp/cường giáp | ATA 2023 | ⏳ Sau |

### Bước 1.2 — Script tổng hợp buổi sáng
- `tools/gen_morning_brief.py` — đọc tất cả knowledge packs, tổng hợp thành bản tin sáng Markdown
- Output: `exports/morning_brief/EBM_SANG_{date}.md`

### Bước 1.3 — Scheduled task sáng sớm
- Chạy `gen_morning_brief.py` lúc 06:30 mỗi ngày
- Ghi kết quả vào `results/daily_ebm_brief.md`

---

## PHASE 2 — KẾT NỐI VÀ TỰ ĐỘNG HÓA (Tuần 3-4)
**Ai thực hiện:** Bác sĩ (cần MacBook)

### Bước 2.1 — Kích hoạt scheduled tasks
```bash
# Phê duyệt trong macOS Settings > Privacy > Automation
# Kiểm tra:
python tools/gen_morning_brief.py --preview
```

### Bước 2.2 — Kết nối surveillance với knowledge packs
- Hiện tại: `mraq-guideline-surveillance` chạy Chủ nhật 20:00 nhưng output không đến đâu
- Cần: Kết quả surveillance → cập nhật knowledge pack → trigger morning brief

### Bước 2.3 — Cung cấp ANTHROPIC_API_KEY
```bash
echo "ANTHROPIC_API_KEY=sk-ant-..." >> ~/.ebm-secrets/.env
```

---

## PHASE 3 — POINT-OF-CARE INTEGRATION (Tháng 2-3)
**Ai thực hiện:** EBM Copilot + Bác sĩ duyệt

### Bước 3.1 — Kết nối chronic-care-clinic-os
- Hiện tại: Next.js app tách rời, không đọc evidence pipeline
- Cần: API endpoint từ evidence pipeline → chronic-care UI

### Bước 3.2 — Alert theo bệnh nhân
- Khi nhập mã ICD/tình trạng bệnh nhân → tự động hiển thị khuyến cáo pack tương ứng

### Bước 3.3 — Medication safety alerts
- Khi xem xét kê đơn → kiểm tra drug safety rules trong knowledge pack

---

## TRẠNG THÁI HIỆN TẠI (2026-07-03)
- ✅ G0-G9 pipeline hoàn chỉnh
- ✅ MRAQ V4.6 (82/100 B+)
- ✅ Integration layer (run_pipeline_integrated.py)
- ✅ KKB-HAI-LONG-2026 đề cương 16-mục
- 🔨 Knowledge packs: 1/10 (hypertension draft)
- ❌ Morning brief: chưa có
- ❌ Point-of-care integration: chưa có
- ❌ Surveillance → practice bridge: chưa có

---

## THƯỚC ĐO THÀNH CÔNG
| Mục tiêu | Đo bằng | Ngưỡng đạt |
|---------|---------|-----------|
| Knowledge pack coverage | Số bệnh lý có pack | ≥ 8/10 |
| Morning brief | Script chạy tự động | 5 ngày/tuần |
| Evidence currency | Guideline mới nhất trong pack | ≤ 6 tháng tuổi |
| Point-of-care latency | Thời gian tra cứu | < 10 giây |
| Bác sĩ sử dụng thực tế | Số lần tra/tuần | ≥ 5 lần/tuần |
