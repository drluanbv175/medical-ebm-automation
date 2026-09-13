# Hướng dẫn tự điền UAT_EVIDENCE.json (7 mục ESD11)

> **Ai điền:** CHỈ bác sĩ (và người vận hành cho 1 mục). File này chỉ hướng dẫn —
> `UAT_EVIDENCE.json` vẫn giữ nguyên `PENDING`/`false` cho tới khi bạn tự tay sửa.
> Không nhờ Claude Code/agent nào điền PASS hộ, kể cả khi có vẻ "chỉ còn một bước".
>
> Điều kiện PASS trích NGUYÊN VĂN từ `tools/verify_evidence_surveillance_deployment.py`
> hàm `_check_uat()` (dòng 414-459) — không diễn giải lại để tránh sai lệch.

## Đã có sẵn bằng chứng — chỉ cần bạn xác nhận rồi điền

### 2. SCHEDULER_TRIGGER — có khả năng ĐÃ ĐẠT, cần bạn xác nhận

Điều kiện: `scheduler_trigger.status == "PASS"`.

Bằng chứng đã tồn tại trên đĩa:
- `data/archive/evidence_surveillance_weekly_status.json` — `status: "PASS"`, chạy
  07/09/2026, log tại `data/archive/launchd_weekly.log`.
- `data/archive/evidence_surveillance_monthly_status.json` — `status: "PASS"`, chạy
  01/09/2026, log tại `data/archive/launchd_monthly.log`.

**Việc của bạn:** mở 2 file trên (và log kèm theo), tự xác nhận đây đúng là một chu kỳ
chạy thật trọn vẹn (không phải fixture/test). Nếu đồng ý, sửa trong `UAT_EVIDENCE.json`:

```json
"scheduler_trigger": {
  "status": "PASS",
  "weekly_runtime_status_path": "data/archive/evidence_surveillance_weekly_status.json",
  "monthly_runtime_status_path": "data/archive/evidence_surveillance_monthly_status.json"
}
```

### 5. SHADOW_RUN — có thể ĐÃ ĐẠT ĐỦ 2 CHU KỲ, nhưng cần bạn quyết định có tính không

Điều kiện: `shadow_run.status == "PASS"` VÀ `cycles >= 2` VÀ `failed_cycles == 0` VÀ
`auto_apply_observed == false`.

Cả 2 lần chạy weekly (07/09) và monthly (01/09) ở trên đều có `clinical_auto_apply: false`
và `status: "PASS"` — tức về mặt SỐ LIỆU đã khớp "2 chu kỳ, 0 lỗi, không tự áp dụng".

**Nhưng đây là điểm CẦN BẠN TỰ QUYẾT, tôi không tự suy luận thay:** "shadow run" theo
thiết kế ban đầu có thể có ý nghĩa là một ĐỢT DIỄN TẬP RIÊNG (biết trước là thử nghiệm,
theo dõi sát), khác với việc "mượn" 2 lần chạy sản xuất bình thường làm bằng chứng. Nếu
bạn thấy 2 lần chạy thật đó ĐỦ đại diện cho ý nghĩa "shadow run", điền:

```json
"shadow_run": {
  "status": "PASS",
  "cycles": 2,
  "failed_cycles": 0,
  "auto_apply_observed": false,
  "evidence_paths": [
    "data/archive/evidence_surveillance_weekly_status.json",
    "data/archive/evidence_surveillance_monthly_status.json"
  ]
}
```

Nếu bạn muốn một đợt diễn tập RIÊNG, tách bạch với vận hành thường ngày, thì chạy tay
thêm 2 lần (không cần đợi đúng lịch):

```bash
bash scripts/weekly_safety.sh --canary   # không ghi DB/Hub, chỉ đo
bash scripts/monthly_update.sh --canary
```

rồi tự ghi lại kết quả 2 lần đó vào `evidence_paths`.

## Cần bạn TỰ TAY làm mới — chưa có bằng chứng sẵn

### 1. SOURCE_SAMPLE_REVIEW — chỉ bác sĩ làm được, không có đường tắt

Điều kiện: ≥5 dòng thoả ĐỒNG THỜI `source_opened: true`, `title_match: true`,
`clinical_claim_checked: true`, `reviewed_by_role: "doctor"`, và có `pmid`/`doi`/`url`.

**Việc của bạn:** mở tối thiểu 5 ứng viên chứng cứ THẬT (ví dụ trong
`EBM-Dashboards/surveillance/to-chuc-2026-09-13.md` — đã có 124 ứng viên sẵn, hoặc từ
`queue/` gói duyệt tuần), với MỖI ứng viên: mở nguồn gốc, xác nhận tiêu đề khớp, xác
nhận khẳng định lâm sàng đúng — rồi tự ghi 5 dòng như sau vào `source_sample_review`:

```json
{
  "source_opened": true,
  "title_match": true,
  "clinical_claim_checked": true,
  "reviewed_by_role": "doctor",
  "pmid": "" ,
  "doi": "",
  "url": "https://... (điền URL thật bạn vừa mở)",
  "note": "tự ghi nhận xét ngắn nếu muốn"
}
```

(chỉ cần MỘT trong ba trường `pmid`/`doi`/`url` có giá trị — không cần điền đủ cả ba).

### 3. ALERT_DELIVERY — phụ thuộc mục kênh cảnh báo (ESD10) bạn đã chọn hoãn

Điều kiện: `alert_delivery.status == "PASS"`.

Chưa làm được vì kênh cảnh báo thật (SMTP/webhook) chưa cấu hình — đây là mục bạn đã
chọn "để sau" ở bước trước. Khi nào cấu hình xong `.env`, gửi thử một cảnh báo, xác nhận
đã NHẬN được ở đầu người nhận, rồi điền:

```json
"alert_delivery": {
  "status": "PASS",
  "channel": "email" ,
  "tested_at": "<ISO timestamp thật>",
  "evidence_note": "mô tả ngắn: gửi lúc nào, nhận ở đâu, nội dung gì"
}
```

### 4. ROLLBACK_RESTORE — cần một lần diễn tập sao lưu/khôi phục thật

Điều kiện: `rollback_restore.status == "PASS"` VÀ `restore_hash_match == true`.

Chưa có script chuyên dụng cho việc này trong repo (đã rà `scripts/`, không thấy
`backup.sh`/`restore.sh` sẵn có) — cần bạn (hoặc nhờ tôi viết một script backup/restore
kèm so hash SHA-256 nếu muốn) tự làm một lần: sao lưu `EBM_MASTER.json` +
`EBM-Dashboards/`, giả lập mất dữ liệu, khôi phục lại, so hash file trước/sau khớp nhau.
Nếu muốn tôi viết script cho bước này (chỉ viết code, không tự chạy để tự ký PASS), nói
tôi biết.

## Bước ký cuối — CHỈ bác sĩ và người vận hành

### 6. DOCTOR_APPROVAL

```json
"doctor_approval": {
  "approved": true,
  "approved_by_role": "doctor",
  "approved_at": "<ISO timestamp thật, lúc bạn tự tay ký>",
  "scope": "candidate_only"
}
```

### 7. OPERATIONS_APPROVAL

Vai trò `operations` tách biệt với `doctor` theo đúng thiết kế cổng (2 người khác nhau,
hoặc bạn tự nhận cả 2 vai nếu đây là hệ thống cá nhân — nhưng phải TỰ QUYẾT ĐỊNH đó,
không phải quy tắc kỹ thuật):

```json
"operations_approval": {
  "approved": true,
  "approved_by_role": "operations",
  "approved_at": "<ISO timestamp thật>",
  "scope": "scheduler_alert_backup_rollback"
}
```

**Chỉ sau khi cả 7 mục trên đủ điều kiện**, chạy lại để xác nhận:

```bash
~/.ebm-venv/bin/python tools/verify_evidence_surveillance_deployment.py --online
```

`deployment_status` sẽ chuyển từ `CONTRACT_PASS`/`BLOCKED_FOR_DEPLOYMENT` sang
`READY_FOR_CONTROLLED_DEPLOYMENT` chỉ khi ESD10 và ESD11 đều PASS thật.
