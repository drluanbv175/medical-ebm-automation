# SOP cá nhân cho production hardening EBM

Tài liệu này là quy trình vận hành cá nhân cho bác sĩ/quản trị viên khi dùng hệ
EBM với nghiên cứu y khoa và hỗ trợ thực hành lâm sàng. Hệ thống chỉ là trợ lý
soạn thảo, kiểm chứng, thẩm định và gợi ý. Cần bác sĩ kiểm chứng trước mọi quyết
định nghiên cứu hoặc lâm sàng.

## 1. Phạm vi dùng

Áp dụng cho hai chế độ tách biệt:

- `research_mode`: dùng cho đề cương, IRB, CRF, SAP, dữ liệu nghiên cứu,
  làm sạch, khóa dữ liệu, phân tích, báo cáo và công bố.
- `clinical_support_mode`: dùng cho cập nhật chứng cứ, checklist, nhắc việc,
  bản nháp tư vấn, giáo dục người bệnh và hỗ trợ quyết định. Không tự áp dụng
  điều trị, không tự ghi EMR/HIS, không gửi tin nhắn bệnh nhân nếu chưa có
  signoff sản xuất.

Không dùng hệ thống như EMR/HIS chính thức, thiết bị y tế tự động, hệ kê đơn tự
động hoặc nguồn ra quyết định thay bác sĩ.

## 2. Dừng ngay

Dừng ngay và không chạy tiếp nếu gặp một trong các điều kiện sau:

- Có PII/PHI thật trong prompt, file, ảnh, âm thanh hoặc bảng dữ liệu chưa qua
  de-identification/pseudonymization được phép.
- Thiếu IRB/protocol/DMP cho dữ liệu nghiên cứu thật.
- Thiếu khóa SAP, thiếu data-lock hoặc còn query mở nhưng đã muốn phân tích chính.
- Có yêu cầu tự ký thay PI, IRB, thống kê viên, phản biện độc lập hoặc bác sĩ.
- Có ý định bật auto-apply, EMR write, gửi tin bệnh nhân hoặc production connector
  khi chưa có UAT, signoff bắt buộc, approval record và go-live attestation.
- Có nguồn chứng cứ không truy nguyên được PMID/DOI/URL chính thức.
- Có cảnh báo red flag/cấp cứu trong tình huống lâm sàng.

## 3. Quy trình dữ liệu thật

1. Bác sĩ/PI xác nhận study ID, protocol, IRB hoặc căn cứ miễn trừ.
2. Data manager tạo bản sao dữ liệu, không sửa raw gốc.
3. Chạy intake để chặn PII. Nếu có PII, chạy de-identification hoặc
   pseudonymization theo DMP.
4. Bảng ánh xạ pseudonymization phải nằm ngoài repo, ngoài OneDrive, trong
   thư mục bảo vệ; có retention owner và retention period.
5. Chạy cleaning trên bản đã khử định danh/pseudonymized; xử lý toàn bộ query.
6. PI/data manager ký data-lock; sau đó mới chạy phân tích chính.
7. Mọi báo cáo giữ audit trail, version, script và checksum.

## 4. Phê duyệt actor thật

- PI, IRB, thống kê viên và phản biện độc lập phải là người thật có thẩm quyền.
- Bác sĩ tự thiết lập khóa gate approval ngoài phiên agent; không nhờ agent chạy
  lệnh tạo khóa hoặc lệnh ký duyệt.
- Mỗi phê duyệt phải gắn role đúng, artifact hash, timestamp và reviewer reference
  không chứa PII đầy đủ.
- Agent không được tự tạo approval, không được tự review sản phẩm do chính nó tạo.

## 5. UAT trước khi dùng thật

Trước khi dùng với quy trình thật:

- Chạy UAT bằng dữ liệu synthetic hoặc dữ liệu đã khử định danh.
- Kiểm các vignette lâm sàng tối thiểu, red flags, thiếu dữ liệu, thuốc, chuyển
  tuyến và tình huống chứng cứ mâu thuẫn.
- Kiểm A5/PDF/handout/checklist trên thiết bị và quy trình thật.
- Bác sĩ, điều dưỡng, quản trị dữ liệu và quản trị hệ thống ký biên bản UAT.
- Nếu UAT fail, quay lại shadow/review mode.

## 6. Backup, rollback và sự cố

- Trước mỗi go-live hoặc thay đổi lớn phải có backup, checksum và kế hoạch rollback.
- Restore drill phải có kết quả thật, RPO/RTO và người xác nhận.
- Audit log phải append-only hoặc có bằng chứng chống sửa/xóa tương đương.
- Có kênh báo sự cố, người trực, mức độ ưu tiên và biên bản xử lý.
- Khi có sự cố dữ liệu, PII hoặc lâm sàng: tắt automation liên quan, bảo toàn log,
  thông báo người phụ trách và không tự xóa dấu vết.

## 7. Kiểm trước mỗi lần chạy

Chạy:

```bash
python3 tools/verify_personal_production_hardening.py
python3 tools/run_controlled_automation_cycle.py
```

Khi chuẩn bị bằng chứng production thật, sinh mẫu evidence package ngoài repo rồi
để người thật điền/duyệt:

```bash
python3 tools/verify_personal_production_hardening.py \
  --init-evidence-template /secure/path/personal-production-evidence.json
```

Sau khi đã có artefact, signoff, approval record và go-live attestation thật,
kiểm package:

```bash
python3 tools/verify_personal_production_hardening.py \
  --evidence /secure/path/personal-production-evidence.json
```

Trong evidence package, mọi `artifact_refs` chỉ được là mã/đường dẫn tương đối
an toàn tới artefact đã khử định danh và đã được duyệt. Không dùng URL ngoài,
đường dẫn tuyệt đối, `..`, `.env`, thư mục `raw`/`restricted`, raw dataset, file
PII/PHI, bảng ánh xạ pseudonymization, linkage key hoặc khóa tái định danh làm
artefact ref.

Evidence package chỉ đủ điều kiện vào thẩm định go-live khi có đủ 7 signoff
đúng role:

- `security_owner`
- `data_protection_owner`
- `legal_compliance_owner`
- `physician_lead`
- `operations_owner`
- `ai_governance_owner`
- `uat_owner`

Approval record là cổng cuối trước go-live review: approver phải là người thật
có thẩm quyền, khác mọi signer ở trên, scope phải ghi rõ production và phải dẫn
tới artefact đã duyệt. Go-live attestation sau đó phải ghi release ID, source
commit, evidence package hash, evidence dossier hash, change ticket, rollback
plan, post-deploy checklist và tách người vận hành khỏi admin approver.

Gói evidence package hợp lệ chỉ có nghĩa là **đủ cấu trúc để đưa vào thẩm định
người thật/đơn vị**. Nó không tự bật dữ liệu bệnh nhân thật, không tự thay UAT,
không tự thay bảo mật triển khai và không tự cho phép ghi EMR/HIS.

Tại thư mục gốc hệ sinh thái, chạy:

```bash
python3 tools/upgrade_verify.py
```

Kết quả hợp lệ cho sử dụng cá nhân có kiểm soát là:

- Không có `FAIL`.
- Có thể còn `HUMAN_GATE`, và khi còn `HUMAN_GATE` thì không dùng dữ liệu bệnh
  nhân thật hoặc không bật clinical production.
- `clinical_production_allowed=False` và `real_patient_data_allowed=False` cho
  tới khi có đủ phê duyệt, UAT, bảo mật, pháp lý/tuân thủ, clinical signoff,
  approval record và go-live attestation.

## 8. Trách nhiệm tối thiểu

| Vai trò | Trách nhiệm |
|---|---|
| Bác sĩ/PI | Duyệt lâm sàng, protocol, mục tiêu, data-lock, diễn giải và công bố |
| IRB/Hội đồng đạo đức | Quyết định đạo đức/pháp lý theo quy định đơn vị |
| Thống kê viên | Duyệt SAP, phân tích chính, deviation và diễn giải thống kê |
| Phản biện độc lập | Rà soát phương pháp, báo cáo, minh bạch và nguy cơ sai lệch |
| Quản trị dữ liệu | PII, pseudonymization, mapping custody, backup, retention |
| Quản trị hệ thống | RBAC, MFA, log, rollback, incident response, go-live change control |
| Pháp lý/tuân thủ | Intended use, privacy notice, consent, hợp đồng, nghĩa vụ pháp lý |
| UAT owner | Biên bản UAT, lỗi còn mở, residual risk và quyết định pass/fail |
| Admin go-live | Approval record cuối cùng, tách khỏi operator và các signer bắt buộc |

## 9. Kết luận vận hành

Hệ thống được phép tự động hóa việc chuẩn bị, kiểm tra, soạn thảo, thẩm định và
nhắc việc. Hệ thống không được tự động thay phê duyệt người thật, không được tự
áp dụng điều trị, không được tự ghi EMR/HIS và không được xử lý dữ liệu định danh
khi chưa có căn cứ hợp lệ.
