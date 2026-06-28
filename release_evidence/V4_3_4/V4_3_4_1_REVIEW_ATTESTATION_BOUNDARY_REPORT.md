# V4.3.4.1 — Review Attestation Boundary Report

**Version:** 4.3.4.1  
**Date:** 2026-06-28  
**Status:** DRAFT — REQUIRE HUMAN REVIEW  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

> **Mục đích tài liệu này:** Làm rõ ranh giới kỹ thuật của hệ thống review attestation.
> Tài liệu này là kết quả của V4.3.4.1 evidence truthfulness pass — sửa mọi tuyên bố
> không chính xác từ V4.3.4 về năng lực kỹ thuật của hệ thống.

---

## 1. Hệ thống đảm bảo kỹ thuật gì

### 1.1 AutoReviewForbidden — chặn automation-originated record

```python
def record_decision(..., automation_caller: bool = False) -> ReviewRecord:
    if automation_caller:
        raise AutoReviewForbidden(
            "Automation không được phép ghi review record. "
            "Phải do con người nhập trực tiếp qua CLI."
        )
```

**Điều kiện kích hoạt:** `automation_caller=True` được truyền vào.  
**Điều kiện KHÔNG kích hoạt:** Caller không truyền flag này, hoặc truyền `False`.  
**Giới hạn:** Đây là cờ Python — hệ thống không thể phân biệt người gọi
thực sự từ con người vs automation nếu automation không truyền `automation_caller=True`.

### 1.2 ForbiddenReviewMode — chặn mode string bị cấm

```python
FORBIDDEN_MODES = {
    "INDEPENDENT_REVIEW_APPROVED",
    "ETHICS_APPROVED",
    "PI_APPROVED",
    "FINAL_APPROVED",
}

def append(self, record: ReviewRecord) -> None:
    if record.review_mode.value in FORBIDDEN_MODES:
        raise ForbiddenReviewMode(...)
```

**Điều kiện kích hoạt:** Mode string khớp chính xác với set cấm.  
**Giới hạn:** Enum `ReviewMode` chỉ có 2 giá trị hợp lệ. Code tốt không thể
tạo ForbiddenReviewMode nếu không dùng `object.__setattr__` để bypass validation.
Đây là guard belt-and-suspenders, không phải cơ chế xác thực identity.

### 1.3 Append-only ledger

```python
class ReviewLedger:
    def append(self, record: ReviewRecord) -> None: ...
    def read_all(self) -> List[ReviewRecord]: ...
    # Không có: delete(), update(), overwrite()
```

**Bảo đảm:** File `review_ledger.jsonl` chỉ được ghi thêm, không bao giờ sửa/xóa
record cũ trong vòng đời của `ReviewLedger` object.  
**Giới hạn kỹ thuật:** Hệ thống không ngăn được thao tác tay trực tiếp vào file
(xóa dòng, sửa nội dung). Đây là audit trail, không phải immutable blockchain.

### 1.4 Draft-only invariant

- `final_released_submitted_count` trong `get_review_status()` luôn = 0
- D-R11 gate kiểm tra không có từ RELEASED/FINAL/SUBMITTED trong artifact text
- D-R13 gate kiểm tra không có external action thật

**Bảo đảm:** Artifact không thể có trạng thái final/released trong vòng đời tự động.  
**Giới hạn:** Hệ thống không ngăn được PI tay sửa file artifact sang "FINAL".

### 1.5 No-PII guard

- `list_review_queue()` lọc PII trước khi trả về
- `record_decision()` có guard check PII trong `reason` field

**Bảo đảm:** Output tự động không chứa pattern PII đã biết.  
**Giới hạn:** Là pattern matching (regex/keyword), không phải semantic NLP check.
Không phát hiện được PII ẩn trong code hoặc ký hiệu viết tắt.

---

## 2. Hệ thống KHÔNG đảm bảo gì

### 2.1 Xác thực danh tính reviewer — KHÔNG

| Khía cạnh | Thực tế |
|-----------|---------|
| Ai ghi record | Bất kỳ ai có quyền truy cập CLI và project dir |
| Role có được xác thực không | Không — role là free-choice enum |
| Hệ thống có biết PI thật là ai không | Không — `human_owner` trong config là string tùy điền |
| Có thể giả mạo role không | Có — reviewer tự khai role |

**Ví dụ:** `--role PI_PROJECT_OWNER` chỉ là string label trong ReviewRecord.
Không có authentication, không có digital signature, không có access control theo role.

### 2.2 Tính độc lập reviewer — KHÔNG

| Khía cạnh | Thực tế |
|-----------|---------|
| Conflict of interest check | Không có |
| Ngăn PI tự review artifact của mình | Không ngăn |
| Verify reviewer là người độc lập | Không verify |
| Mode `HUMAN_REVIEW_INDEPENDENCE_NOT_ESTABLISHED` | Chỉ là string label, không xác minh |

**Ý nghĩa của mode mặc định:** Tên mode `HUMAN_REVIEW_INDEPENDENCE_NOT_ESTABLISHED`
là tuyên bố trung thực rằng hệ thống BIẾT mình không xác lập được independence.
Đây không phải cơ chế ngăn chặn — là nhãn cảnh báo.

### 2.3 Ethics approval — KHÔNG

| Khía cạnh | Thực tế |
|-----------|---------|
| Hệ thống có ethics board integration không | Không |
| ReviewRecord có tương đương IRB approval không | Không |
| `ACCEPT_DRAFT_FOR_NEXT_INTERNAL_STAGE` có nghĩa ethics cleared không | Không |

**Nghĩa đúng của ACCEPT_DRAFT:** Người ghi record chấp nhận artifact đủ để
chuyển bước nội bộ tiếp theo. Không có nghĩa là ethics-cleared, IRB-approved, hay PI-signed.

### 2.4 PI approval chính thức — KHÔNG

| Khía cạnh | Thực tế |
|-----------|---------|
| Có chữ ký điện tử không | Không |
| Có pháp lý tương đương không | Không |
| Có thể dùng làm bằng chứng audit trail công thức không | Không khuyến nghị |

### 2.5 Chất lượng nội dung review — KHÔNG

| Khía cạnh | Thực tế |
|-----------|---------|
| Reviewer có thực sự đọc artifact không | Hệ thống không track |
| `reason` field có hợp lý không | Là free-text, không validate |
| Counters phản ánh chất lượng review không | Chỉ phản ánh số lần ghi record |

---

## 3. Tại sao không cho phép tuyên bố "independent review"

### 3.1 Tuyên bố sai về mặt kỹ thuật

Tuyên bố `INDEPENDENT_REVIEW_APPROVED` yêu cầu:
1. Reviewer độc lập với artifact (không có COI)
2. Reviewer có chuyên môn xác nhận được
3. Quá trình review có thể audit

Hệ thống này không xác minh được bất kỳ điểm nào trong 3 điểm trên.

### 3.2 Cơ chế chặn (`ForbiddenReviewMode`)

Mode bị cấm gồm: `INDEPENDENT_REVIEW_APPROVED`, `ETHICS_APPROVED`, `PI_APPROVED`, `FINAL_APPROVED`.

Đây là danh sách tường minh các mode hệ thống BIẾT mình không thể đảm bảo.
Thiết kế có chủ đích: thà lỗi rõ ràng (ForbiddenReviewMode) còn hơn ghi record
ám chỉ sự đảm bảo không có.

### 3.3 Ý nghĩa thiết kế của `ReviewMode.SELF_REVIEW`

Hệ thống cho phép `SELF_REVIEW` vì đây là tuyên bố TRUNG THỰC: PI tự review
draft của mình, không có independence. Đây không phải sự chấp thuận — là ghi nhận
thực tế để audit trail.

---

## 4. Yêu cầu governance bên ngoài hệ thống

Để đạt được những gì hệ thống hiện không đảm bảo, tổ chức phải triển khai
**ngoài hệ thống này** (không phải V4.3.4 cung cấp):

| Yêu cầu | Giải pháp ngoài hệ thống |
|---------|-------------------------|
| Xác thực danh tính reviewer | Identity provider (SSO, LDAP, OAuth2) |
| Role-based access control | RBAC layer trước CLI access |
| Digital signature cho review | E-signature platform (DocuSign, ADSS) |
| Ethics board integration | IRB workflow system |
| Conflict-of-interest check | COI declaration workflow |
| Immutable audit trail | Blockchain or certified timestamp authority |
| Independent reviewer verification | External review coordinator |

---

## 5. Tóm tắt ranh giới

| Câu hỏi | Câu trả lời chính xác |
|---------|----------------------|
| Hệ thống có ngăn automation tự ghi review record không? | **CÓ** — qua `AutoReviewForbidden` (khi `automation_caller=True`) |
| Hệ thống có xác thực danh tính reviewer không? | **KHÔNG** |
| Hệ thống có xác minh tính độc lập reviewer không? | **KHÔNG** |
| Hệ thống có đảm bảo ethics/PI/final approval không? | **KHÔNG** |
| ReviewRecord có phải manual attestation không? | **CÓ** — ghi nhận rằng người dùng CLI đã ghi record |
| ReviewRecord có thay thế ethics approval không? | **KHÔNG** |
| Hệ thống có đủ điều kiện dùng cho workflow nghiên cứu thật không? | **KHÔNG — NO-GO** |

---

## 6. Điều kiện để nâng cấp qualification

Để nâng qualification từ NO-GO, cần triển khai BÊN NGOÀI hệ thống này:

1. Authentication layer xác thực reviewer identity
2. RBAC ngăn self-review trên artifact chính
3. COI declaration workflow
4. IRB/ethics board integration
5. Audit trail được certified bởi bên thứ ba độc lập
6. Quy trình nghiệm thu độc lập bởi tổ chức có thẩm quyền

---

*Manual review record does not constitute ethics, PI, final, or independent approval.*  
*Cần bác sĩ / PI kiểm chứng. Đây là bản DRAFT tự động — KHÔNG thực thi thật.*
