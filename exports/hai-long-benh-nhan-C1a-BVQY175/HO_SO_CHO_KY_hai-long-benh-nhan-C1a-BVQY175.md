# HỒ SƠ CHỜ KÝ — Đề tài hai-long-benh-nhan-C1a-BVQY175

_Tài liệu nội bộ, soạn tay 13/09/2026 theo yêu cầu "soạn sẵn tất cả nội dung để ký xác thực"._
_Mục đích: gom **782 lượt khớp "[CẦN…]"** rải khắp hồ sơ (nhiều lượt là CÙNG MỘT sự thật lặp lại
ở nhiều tài liệu) thành một danh sách **DUY NHẤT, KHÔNG LẶP**, phân đúng việc cho đúng người —
KHÔNG bịa bất kỳ nội dung khoa học/cá nhân/thể chế nào. Nơi có thể tự động đồng bộ, ghi rõ LỆNH
CHẠY thay vì bảo sửa tay từng chỗ._

---

## PHẦN A — 4 sự thật hành chính còn thiếu (điền 1 LẦN, tự lan ra ~15 chỗ)

**Phát hiện quan trọng:** phần lớn nhãn "[CẦN BỔ SUNG]" về chức vụ/điện thoại/email trong
`G2_A3_ETHICS_PACKAGE...md` (44 lượt khớp) **không cần sửa tay từng dòng** — `run_g2_auto.py` đọc
các trường này từ **`study_meta.json → administrative`**. Hiện trạng đo được:

| Trường (`administrative.*`) | Giá trị hiện tại | Cần bác sĩ điền |
|---|---|---|
| `principal_investigator` | ✅ "Nguyễn Hà Luân" | — đã có |
| `pi_unit` | ✅ "Khoa Khám bệnh C1a…" | — đã có |
| `irb_name` | ✅ "Hội đồng Y đức Bệnh viện Quân y 175" | — đã có |
| `sponsor` | ✅ "Không có tài trợ bên ngoài…" | — đã có |
| `pi_title` | ❌ `null` | **Chức danh/học hàm của bác sĩ** (vd "Bác sĩ CKII", "Thạc sĩ Y học"…) |
| `pi_phone` | ❌ `null` | **Số điện thoại liên hệ** của bác sĩ (dùng trong đơn IRB + ICF) |
| `pi_email` | ❌ `null` | **Email liên hệ** của bác sĩ |
| `irb_contact` | ❌ `null` | **Số điện thoại của Hội đồng Y đức BVQY 175** (bác sĩ tự hỏi văn thư HĐ) |

**Cách điền — 1 trong 2 cách:**
1. Mở `study_meta.json` (Edit tool hoặc tự mở), sửa 4 giá trị `null` ở trên thành chuỗi thật.
2. Hoặc nói trực tiếp 4 giá trị cho tôi trong hội thoại, tôi điền hộ (đây là **sự thật khách quan**
   bác sĩ tự cung cấp — không phải nội dung tôi tự suy luận/bịa, nên tôi có thể gõ hộ).

**Sau khi điền xong, chạy:**
```bash
python tools/run_g2_auto.py --study hai-long-benh-nhan-C1a-BVQY175
```
→ toàn bộ ~15 chỗ "[CẦN BỔ SUNG]" liên quan 4 trường này trong `G2_A3_ETHICS_PACKAGE...md` (Tài
liệu 1, 4, 5, 7) tự cập nhật đồng loạt — không phải sửa tay từng dòng.

---

## PHẦN B — 1 chỗ lệch cần TỰ SỬA TAY sau khi sinh lại (không tự động đồng bộ được)

`G2_A3_ETHICS_PACKAGE...md` dòng 15, 48, 539, 705 ghi nơi đăng ký nghiên cứu là
**"ClinicalTrials.gov hoặc WHO ICTRP primary registry"** — đây là giá trị MẶC ĐỊNH viết cứng
trong `run_g2_auto.py` theo LOẠI THIẾT KẾ (cross-sectional), không đọc từ `study_meta.json` nên
**không tự đồng bộ được** dù chạy lại lệnh ở Phần A.

Nhưng `_checklist-noi-bo.md` (mục "Quyết định đã KHÓA") đã chốt từ trước:
> "Đăng ký nghiên cứu trên **OSF Registries** (không phải 'WHO ICTRP hoặc cổng phù hợp' — ICTRP là
> cổng tổng hợp, không phải nơi đăng ký trực tiếp)."

**→ Việc cần làm:** sau khi chạy lại `run_g2_auto.py` ở Phần A, tự thay 4 chỗ nêu trên (tìm chuỗi
"ClinicalTrials.gov hoặc WHO ICTRP") thành **"OSF Registries (https://osf.io/registries)"** trước
khi nộp. Đây KHÔNG phải lỗi khoa học — chỉ là tài liệu IRB chưa bắt kịp quyết định đã chốt ở nơi
khác; tôi không tự sửa mã nguồn `run_g2_auto.py` vì giá trị đó là mặc định DÙNG CHUNG cho mọi đề
tài cắt ngang khác, không riêng đề tài này — sửa chung có thể ảnh hưởng đề tài khác chưa rà.

---

## PHẦN C — Quyết định/nội dung CẦN BÁC SĨ TỰ QUYẾT (không thể tự động, không thể tôi bịa)

Mỗi mục dưới đây tôi đã trích **nguyên văn ngữ cảnh + phương án đề xuất sẵn có trong chính tài
liệu** để bác sĩ chỉ cần XÁC NHẬN hoặc CHỌN, không phải soạn từ đầu.

| # | Mục | Ngữ cảnh / phương án đã có sẵn trong hồ sơ | Việc bác sĩ cần làm |
|---|---|---|---|
| C1 | COI tài chính/phi tài chính (Tài liệu 8, mục A–B) | Mặc định trong mẫu: "☐ Không có" | Tick "Không có" nếu đúng, hoặc khai chi tiết nếu có |
| C2 | Vai trò nhà tài trợ (Tài liệu 8, mục D) | Không áp dụng vì "không có tài trợ ngoài" | Tick 3 dòng "☐ Không" |
| C3 | Người kiểm tra đầu ra AI (Tài liệu 8, mục E) | — | Ghi tên người (thường là chính chủ nhiệm) đã đọc lại toàn bộ nội dung AI hỗ trợ |
| C4 | Bảng rủi ro–lợi ích có phù hợp thật không (Tài liệu 3) | 2 rủi ro đã liệt kê: rò rỉ thông tin, gánh nặng thời gian | Xác nhận ĐÚNG hoặc bổ sung rủi ro khác nếu có |
| C5 | Đủ điều kiện miễn ICF? (Tài liệu 9) | Hệ thống tự đánh giá ĐỦ điều kiện (khảo sát nặc danh, không can thiệp) — nhưng **luật bắt buộc bác sĩ tự xác nhận**, không được suy từ thiết kế | Trả lời CÓ/KHÔNG — nếu KHÔNG thì phải dùng ICF đầy đủ (Tài liệu 4/5) thay vì miễn |
| C6 | Nơi lưu dữ liệu mã hóa (DMP mục 4) | Gợi ý: "máy chủ nội bộ / OneDrive institutional / ổ cứng mã hóa" | Chọn 1 phương án thật đang dùng tại khoa |
| C7 | Tần suất sao lưu (DMP mục 4) | — | Vd "hàng tuần, 2 bản độc lập" — điền số thật |
| C8 | Chia sẻ/mở dữ liệu sau nghiên cứu (DMP mục 5) | 3 lựa chọn có sẵn: không chia sẻ / chia sẻ theo yêu cầu (DTA) / mở hoàn toàn (OSF/Zenodo) | Chọn 1 + lý do ngắn |
| C9 | Bồi thường khi có tổn hại (ICF mục 6c) | Gợi ý rút gọn: "không phát sinh thủ thuật/can thiệp ngoài thường quy" (vì nguy cơ tối thiểu, không can thiệp) | Xác nhận câu rút gọn này ĐÚNG, hoặc mô tả chính sách khác |
| C10 | Hỗ trợ/bồi dưỡng người tham gia (ICF mục 4c) | Mặc định "☐ Không có hỗ trợ nào ngoài chăm sóc thường quy" | Tick đúng lựa chọn |

---

## PHẦN D — Cổng G4 (SAP): ĐÚNG 1 câu hỏi khoa học còn treo

Từ `_checklist-noi-bo.md` (nhật ký 30/08/2026) — đây là **[CẦN]** DUY NHẤT còn lại ở §5 SAP:

> **`chuyenkhoa`: Khoa C1a có vận hành phân biệt được theo chuyên khoa/phòng khám hay không?**
> - Nếu **CÓ** → giữ biến `chuyenkhoa` trong tập biến điều chỉnh bắt buộc (forced-in) của mô hình
>   hồi quy logistic thứ tự.
> - Nếu **KHÔNG** (C1a vận hành như phòng khám tổng quát, không tách chuyên khoa) → loại biến này
>   khỏi tập forced-in, mô hình chính hiệu chỉnh theo các biến còn lại (mục 4.6.2 đề cương).

Trả lời xong, các bước còn lại đã có sẵn lệnh (không cần soạn thêm nội dung):
1. Chốt phương án mã hóa `lydo_chon_theoyeucau`: (a) 2 cột hay (b) 8 cột nhị phân — xem
   `_bo-sung-codebook_12-bien.md` để so 2 phương án.
2. Thêm 12 biến vào file `.sav` theo bản đặc tả (thao tác trên máy có SPSS).
3. Xác nhận/đổi seed thống kê khi ký (mặc định đề xuất: `20260830`).
4. Điền `gate_params.G4` trong `study_meta.json`:
   - `epv_vif_reviewed`: `true` **CHỈ SAU KHI** bác sĩ/thống kê viên đã thật sự rà EPV/VIF.
   - `missing_data_mechanism_confirmed`: `true` **CHỈ SAU KHI** đã xác nhận cơ chế dữ liệu thiếu.
   - `subgroup_multiplicity_predefined_confirmed`: `true` **CHỈ SAU KHI** đã xác nhận không thêm
     phân nhóm ngoài dự kiến.
   - `reviewed_by_role`: `"STATISTICIAN"` hoặc `"PI"` (vai trò người ký thật).
   - `reviewed_at`: ngày thật (`YYYY-MM-DD`).
5. Ký thật bằng khóa vai trò đã phát (xem `HUONG-DAN-PHAT-KHOA-ED25519.md`):
   ```bash
   python tools/approve_gate.py --gate G4 --study hai-long-benh-nhan-C1a-BVQY175 --role STATISTICIAN
   ```

**⚠️ Tôi KHÔNG tự đặt bất kỳ cờ `true` nào ở bước 4 — đó là lời tự khai đã-rà-soát-thật, chỉ người
thật mới được ghi.**

---

## PHẦN E — Trình tự hành động THẬT (không phải nội dung soạn, mà là việc phải làm ngoài đời)

Thứ tự này khớp đúng "CƠ CHẾ MỞ KHÓA G2" đã ghi trong `G2_A3_ETHICS_PACKAGE...md` — làm sai thứ tự
sẽ phải làm lại:

1. Hoàn tất Phần A + B + C ở trên (nội dung giấy tờ).
2. **Đăng ký trên OSF Registries** (https://osf.io/registries) — TRƯỚC người tham gia đầu tiên,
   theo đúng quyết định đã khóa. Nhận mã đăng ký + ngày đăng ký.
3. In hồ sơ (8 tài liệu Tài liệu 1–8 + đề cương đầy đủ + CV) → **nộp Hội đồng Y đức BVQY 175**.
4. Chờ quyết định (lộ trình đề nghị: EXPEDITED, thường 2–4 tuần).
5. Nhận **số phê duyệt IRB + ngày phê duyệt + ngày hết hạn (hoặc xác nhận không ghi hạn)**.
6. Điền số/ngày đó vào `study_meta.json` (`gate_params.G2`) — tôi hỗ trợ điền nếu bác sĩ đọc số
   cho tôi, nhưng **không tự bịa hoặc suy đoán** số này.
7. Người có thẩm quyền IRB tự ghi ledger phê duyệt (không phải tôi, không phải bác sĩ gõ hộ vai
   trò IRB nếu bác sĩ không phải là người của Hội đồng).
8. Ký G2 thật:
   ```bash
   python tools/approve_gate.py --gate G2 --study hai-long-benh-nhan-C1a-BVQY175 --role IRB
   ```
9. Chỉ SAU KHI G2 khóa (`G2_STATUS: LOCKED`) mới được bắt đầu thu thập dữ liệu thật.

---

## Tổng kết — việc gì thuộc về ai

| Ai | Việc |
|---|---|
| **Bác sĩ (5 phút)** | Đọc và điền/nói 4 giá trị ở Phần A |
| **Tôi (ngay sau khi có Phần A)** | Chạy `run_g2_auto.py`, sửa 4 chỗ registry ở Phần B, chuẩn bị lại phiếu cho bác sĩ đọc |
| **Bác sĩ (đọc + tick, ~15–20 phút)** | 10 mục ở Phần C |
| **Bác sĩ + thống kê viên** | 1 câu hỏi `chuyenkhoa` + ký G4 (Phần D) |
| **Bác sĩ, ngoài hệ thống, theo tuần/tháng** | Đăng ký OSF → nộp IRB → nhận số → ký G2 (Phần E) |

_Cần bác sĩ kiểm chứng toàn bộ nội dung trước khi ký/nộp. Tài liệu này chỉ tổ chức lại thông tin đã
có trong hệ thống, không thay thế việc bác sĩ tự đọc từng tài liệu gốc trước khi ký._
