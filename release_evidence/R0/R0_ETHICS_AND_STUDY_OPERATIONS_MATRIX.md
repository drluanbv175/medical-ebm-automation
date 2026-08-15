# R0 Ethics and Study Operations Matrix

**Document:** R0_ETHICS_AND_STUDY_OPERATIONS_MATRIX.md  
**Date:** 2026-06-28  
**Status:** DRAFT — REQUIRE HUMAN REVIEW  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

## Tuyên bố bắt buộc

> Applicable institutional, Ministry of Health, ethics committee and legal requirements
> must be confirmed by the institution before study activation.

Ma trận này **không** xác định quy định pháp lý cụ thể của Việt Nam hay bất kỳ quốc gia nào.
Mọi nội dung mang tính khung tổng quát theo chuẩn ICH-GCP, Helsinki và CIOMS.
Tổ chức phải tự xác nhận với hội đồng đạo đức, Bộ Y tế và cơ quan có thẩm quyền.

---

## 1. Retrospective De-identified Study (LEVEL_A)

### 1.1 Protocol Requirement

| Yếu tố | Mô tả |
|--------|-------|
| Protocol document | Phải có protocol mô tả câu hỏi nghiên cứu, nguồn dữ liệu, phương pháp phân tích, thời gian, đối tượng |
| Protocol version control | Mỗi sửa đổi phải có version mới với lý do thay đổi |
| Protocol registration | Thường không bắt buộc cho hồi cứu — xác nhận với tạp chí đích và hội đồng đạo đức |
| Statistical Analysis Plan | SAP phải được khóa trước khi xem dữ liệu |

### 1.2 Consent or Waiver Assessment

| Yếu tố | Mô tả |
|--------|-------|
| Consent requirement | Thường có thể xin waiver nếu dữ liệu đã khử định danh và rủi ro tối thiểu |
| Waiver conditions | Dữ liệu khử định danh hoàn toàn; rủi ro không đáng kể; không thực tế để xin consent hồi cứu |
| Ethics committee decision | Hội đồng đạo đức quyết định — không phải hệ thống AI |
| Re-identification risk | Phải được đánh giá và document trước khi xin waiver |

### 1.3 Participant Information Requirement

| Yếu tố | Mô tả |
|--------|-------|
| Individual notification | Không bắt buộc nếu waiver được cấp |
| Public disclosure | Có thể cần thông báo công khai về việc sử dụng dữ liệu hồi cứu — xác nhận với hội đồng |
| Privacy notice | Cần có chính sách quyền riêng tư của tổ chức |

### 1.4 Data Access Authorization

| Yếu tố | Mô tả |
|--------|-------|
| Authorization required | Data access agreement với nguồn dữ liệu (bệnh viện, khoa lâm sàng) |
| Field list approval | Danh mục field truy xuất phải được phê duyệt bởi data custodian |
| De-identification verification | PI hoặc data privacy expert phải verify trước khi nhập vào hệ thống |

### 1.5 PI Responsibility

| Yếu tố | Mô tả |
|--------|-------|
| Protocol accuracy | PI chịu trách nhiệm đảm bảo protocol đúng và được hội đồng phê duyệt |
| Data governance | PI chịu trách nhiệm giám sát việc sử dụng dữ liệu |
| AI output review | PI phải review mọi AI output trước khi dùng trong nghiên cứu |
| Publication | PI chịu trách nhiệm tuân thủ ICMJE authorship và khai báo COI |

### 1.6 Co-investigator Delegation

| Yếu tố | Mô tả |
|--------|-------|
| Delegation log | Phải có delegation log ký tên trước khi Co-I thực hiện bất kỳ nhiệm vụ nào |
| Role-specific delegation | Mỗi nhiệm vụ phải được ủy quyền cụ thể — không ủy quyền chung chung |

### 1.7 Ethics Committee Interaction

| Yếu tố | Mô tả |
|--------|-------|
| Initial submission | Protocol + waiver request + de-identification protocol |
| Response to queries | PI phải trả lời query của hội đồng trong thời hạn |
| Annual renewal | Tùy theo yêu cầu hội đồng |
| Substantial amendment | Bất kỳ thay đổi protocol quan trọng nào phải nộp lại |

### 1.8 Safety and Deviation

| Yếu tố | Mô tả |
|--------|-------|
| Safety reporting | Thường không áp dụng (không can thiệp) |
| Protocol deviation | Ghi nhận và báo cáo cho hội đồng nếu yêu cầu |

### 1.9 Registration

| Yếu tố | Mô tả |
|--------|-------|
| Prospective registration | Thường không bắt buộc cho hồi cứu — xác nhận với tạp chí |
| Retrospective registration | Một số tạp chí yêu cầu — kiểm tra author guidelines |

### 1.10 Publication and Dissemination

| Yếu tố | Mô tả |
|--------|-------|
| STROBE reporting | Nghiên cứu quan sát hồi cứu thường theo STROBE |
| Authorship | Per ICMJE — AI không được liệt kê là tác giả |
| COI declaration | Tất cả tác giả phải khai báo |
| Data sharing | Theo chính sách tạp chí và institutional policy |

---

## 2. Prospective Observational Study (LEVEL_B)

### 2.1 Protocol Requirement

| Yếu tố | Mô tả |
|--------|-------|
| Protocol | Đầy đủ per STROBE/protocol standards — PECO, inclusion/exclusion, outcome, timeline |
| SAP | Phải khóa TRƯỚC khi thu thập dữ liệu đầu tiên |
| Monitoring plan | Phải có và được PI + ethics committee phê duyệt |
| Registration | Bắt buộc trước khi tuyển dụng người tham gia đầu tiên |

### 2.2 Consent or Waiver

| Yếu tố | Mô tả |
|--------|-------|
| Informed consent | BẮT BUỘC — không được waiver trừ trường hợp đặc biệt hội đồng phê duyệt |
| ICF content | Mục đích nghiên cứu; rủi ro; quyền rút lui; bảo mật dữ liệu; contact thông tin |
| ICF approval | Phiên bản ICF phải được ethics committee phê duyệt trước khi sử dụng |
| Re-consent | Cần re-consent nếu có thay đổi protocol quan trọng |

### 2.3 Participant Information

| Yếu tố | Mô tả |
|--------|-------|
| Information sheet | Bản thông tin cho người tham gia — ngôn ngữ dễ hiểu |
| Consent form | Tách với information sheet; chữ ký người tham gia + ngày |
| Copy for participant | Người tham gia phải nhận bản sao |

### 2.4 Data Access Authorization

| Yếu tố | Mô tả |
|--------|-------|
| Ethics approval | Xác định scope dữ liệu được phép thu thập |
| Data custodian agreement | Cần nếu truy cập eHospital |
| Pseudonymization | Dữ liệu phải pseudonymized trước khi vào Research OS |

### 2.5 PI Responsibility

| Yếu tố | Mô tả |
|--------|-------|
| Study oversight | PI chịu trách nhiệm toàn diện về an toàn người tham gia và tính chính trực dữ liệu |
| SAE reporting | PI phải đảm bảo SAE được báo cáo trong thời hạn |
| Protocol adherence | PI chịu trách nhiệm giám sát tuân thủ protocol |

### 2.6 Co-investigator Delegation

| Yếu tố | Mô tả |
|--------|-------|
| Specific task delegation | Mỗi Co-I có nhiệm vụ cụ thể trong delegation log |
| Training verification | Co-I phải hoàn thành training trước khi thực hiện nhiệm vụ |

### 2.7 Ethics Committee Interaction

| Yếu tố | Mô tả |
|--------|-------|
| Full submission | Protocol + ICF + monitoring plan + insurance (nếu yêu cầu) |
| Annual progress report | Bắt buộc |
| SAE reporting to committee | Theo timeline của hội đồng |
| Substantial amendment | Phê duyệt trước khi implement |
| Final report | Sau khi kết thúc nghiên cứu |

### 2.8 Safety and Deviation

| Yếu tố | Mô tả |
|--------|-------|
| SAE definition and reporting | Per protocol — timeline thường 24h cho unexpected SAE |
| Protocol deviation log | Ghi nhận, phân loại, báo cáo cho hội đồng nếu significant |
| Monitoring reports | Periodic site monitoring reports |

### 2.9 Registration

| Yếu tố | Mô tả |
|--------|-------|
| Prospective registration | BẮT BUỘC trước tuyển dụng — ClinicalTrials.gov hoặc ICTRP hoặc national registry |

### 2.10 Publication

| Yếu tố | Mô tả |
|--------|-------|
| STROBE reporting | Bắt buộc |
| Registration number | Phải nêu trong bài báo |
| Authorship | Per ICMJE |

---

## 3. Interventional Clinical Trial (LEVEL_C)

### 3.1 Protocol Requirement

| Yếu tố | Mô tả |
|--------|-------|
| Protocol | Per SPIRIT 2013 — đầy đủ mọi yếu tố thiết kế, ngẫu nhiên hóa, mù, kết cục |
| SAP | Khóa TRƯỚC khi unbind/unblind |
| Monitoring plan | DSMB charter + site monitoring plan |
| IB (Investigator Brochure) | Nếu có investigational product |
| Regulatory notification | Xác nhận với Bộ Y tế và cơ quan quản lý liên quan |

### 3.2 Consent or Waiver

| Yếu tố | Mô tả |
|--------|-------|
| Informed consent | BẮT BUỘC; KHÔNG waiver; phải trước mọi thủ thuật nghiên cứu |
| Re-consent | Bắt buộc khi có thay đổi quan trọng về rủi ro hoặc procedure |
| Vulnerable populations | Yêu cầu bổ sung — LAR, assent, vv. |

### 3.3 Participant Information

| Yếu tố | Mô tả |
|--------|-------|
| Full ICF | Ngôn ngữ rõ ràng; rủi ro đầy đủ; quyền rút lui không ảnh hưởng điều trị |
| Witnessed consent | Trong một số trường hợp — xác nhận với hội đồng |

### 3.4 Data Access

| Yếu tố | Mô tả |
|--------|-------|
| GCP-compliant data management | Audit trail, direct access cho monitor/auditor |
| Source data verification | Monitor phải có quyền so sánh source với EDC |

### 3.5 PI Responsibility (GCP)

| Yếu tố | Mô tả |
|--------|-------|
| GCP training | PI và mọi nghiên cứu viên phải có GCP certificate còn hiệu lực |
| Delegation | Delegation log GCP; chỉ ủy quyền nhiệm vụ phù hợp với training |
| Safety responsibility | PI chịu trách nhiệm an toàn người tham gia tại site |
| Regulatory submission | PI chịu trách nhiệm nộp đúng hạn cho cơ quan quản lý |

### 3.6 Co-investigator Delegation

| Yếu tố | Mô tả |
|--------|-------|
| GCP training required | Tất cả Co-I và coordinator |
| Task-specific delegation | Delegation log GCP chuẩn |

### 3.7 Ethics Committee Interaction

| Yếu tố | Mô tả |
|--------|-------|
| Initial approval | Protocol + ICF + IB + insurance + site feasibility |
| SUSAR reporting | Trong timeline theo GCP |
| Annual safety report | DSURs (Development Safety Update Reports) nếu áp dụng |
| Substantial amendment | Phê duyệt TRƯỚC khi implement |
| End of trial notification | |
| Final clinical study report | |

### 3.8 Safety and Deviation (GCP)

| Yếu tố | Mô tả |
|--------|-------|
| AE/SAE definition | Per protocol và ICH E2A |
| SAE reporting timeline | 24h cho unexpected fatal/life-threatening SAE |
| SUSAR reporting | Expedited to ethics + regulatory |
| DSMB/DMC | Độc lập; interim analysis; stopping rules |
| Protocol deviation | Major/minor classification; CAPA |

### 3.9 Registration

| Yếu tố | Mô tả |
|--------|-------|
| Prospective registration | BẮT BUỘC trước tuyển dụng người tham gia đầu tiên |
| WHO ICTRP compliant registry | |

### 3.10 Publication

| Yếu tố | Mô tả |
|--------|-------|
| CONSORT reporting | Bắt buộc |
| Protocol publication | Khuyến nghị per SPIRIT |
| Registration number | Bắt buộc trong bài báo |
| Results disclosure | Một số registry bắt buộc đăng kết quả |

---

## Tóm tắt bắt buộc

| Yêu cầu | LEVEL_A | LEVEL_B | LEVEL_C |
|---------|---------|---------|---------|
| Ethics committee interaction | Waiver/exemption | Full + annual | Full + SUSAR + DSURs |
| Informed consent | Không bắt buộc | Bắt buộc | Bắt buộc |
| Protocol registration | Không thường xuyên | Bắt buộc | Bắt buộc (pre-enroll) |
| Safety reporting | N/A | SAE | SAE + SUSAR + DSMB |
| GCP training | Không bắt buộc | Khuyến nghị | Bắt buộc |
| Monitoring | Data quality only | Site monitoring | Site + central + DSMB |

---

*Applicable institutional, Ministry of Health, ethics committee and legal requirements
must be confirmed by the institution before study activation.*

*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*
