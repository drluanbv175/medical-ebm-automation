# HỒ SƠ CHỜ KÝ — Đề tài hai-long-benh-nhan-C1a-BVQY175

_Tài liệu nội bộ, soạn tay 13/09/2026 theo yêu cầu "soạn sẵn tất cả nội dung để ký xác thực"._
_Mục đích: gom **782 lượt khớp "[CẦN…]"** rải khắp hồ sơ (nhiều lượt là CÙNG MỘT sự thật lặp lại
ở nhiều tài liệu) thành một danh sách **DUY NHẤT, KHÔNG LẶP**, phân đúng việc cho đúng người —
KHÔNG bịa bất kỳ nội dung khoa học/cá nhân/thể chế nào. Nơi có thể tự động đồng bộ, ghi rõ LỆNH
CHẠY thay vì bảo sửa tay từng chỗ._

---

## PHẦN A — ✅ 3/4 ĐÃ XONG (13/09/2026) — còn 1 trường

**Cập nhật 13/09/2026:** bác sĩ đã cung cấp trực tiếp 3/4 giá trị trong hội thoại. `run_g2_auto.py
--study ...` từ chối tự tái sinh toàn file (bản hiện có đã bị/được biên tập tay: 49 nhãn còn lại so
với 79 nhãn của bản mới sinh — an toàn đúng như thiết kế, tránh ghi đè phần bác sĩ đã sửa), nên đã
áp trực tiếp 3 giá trị vào đúng vị trí trong `G2_A3_ETHICS_PACKAGE...md` (Tài liệu 1, 4, 8) + lưu
vào `study_meta.json → administrative` để các lần sinh sau tự dùng đúng giá trị này.

| Trường (`administrative.*`) | Giá trị hiện tại | Cần bác sĩ điền |
|---|---|---|
| `principal_investigator` | ✅ "Nguyễn Hà Luân" | — đã có |
| `pi_unit` | ✅ "Khoa Khám bệnh C1a…" | — đã có |
| `irb_name` | ✅ "Hội đồng Y đức Bệnh viện Quân y 175" | — đã có |
| `sponsor` | ✅ "Không có tài trợ bên ngoài…" | — đã có |
| `pi_title` | ✅ "Bác sĩ Chuyên khoa I (BS.CKI)" | — đã điền 13/09 |
| `pi_phone` | ✅ đã điền | — đã điền 13/09 |
| `pi_email` | ✅ đã điền | — đã điền 13/09 |
| `irb_contact` | ❌ `null` | **Số điện thoại của Hội đồng Y đức BVQY 175** (bác sĩ tự hỏi văn thư HĐ) — còn ĐÚNG 1 vị trí "[CẦN BỔ SUNG]" trong ICF, mục 7 |

**Chỉ còn `irb_contact`** — nói số điện thoại của Hội đồng cho tôi khi có, tôi điền nốt vị trí cuối
cùng trong ICF (mục 7 "Thắc mắc về quyền của người tham gia").

---

## PHẦN B — ✅ ĐÃ SỬA (13/09/2026)

`G2_A3_ETHICS_PACKAGE...md` từng ghi nơi đăng ký nghiên cứu là "ClinicalTrials.gov hoặc WHO ICTRP
primary registry" ở 5 vị trí (giá trị mặc định viết cứng theo loại thiết kế, không khớp quyết định
đã khóa trong `_checklist-noi-bo.md`: **OSF Registries**). Đã sửa cả 5 vị trí thành "OSF Registries
(https://osf.io/registries)", kể cả định dạng mã đăng ký ở Trường 1 (WHO TRDS) — đổi từ mẫu
"NCT_______ / ANZCTR_____" (định dạng riêng của ClinicalTrials.gov/ANZCTR) sang mẫu URL của OSF.
Không sửa mã nguồn `run_g2_auto.py` (giá trị mặc định dùng chung cho mọi đề tài cắt ngang khác) —
chỉ sửa trực tiếp nội dung tài liệu của đề tài này.

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

| Ai | Việc | Trạng thái |
|---|---|---|
| **Bác sĩ** | Nói số điện thoại Hội đồng Y đức (`irb_contact`) — 1 giá trị cuối của Phần A | ⏳ còn thiếu |
| **Bác sĩ (đọc + tick, ~15–20 phút)** | 10 mục ở Phần C | ⏳ chưa làm |
| **Bác sĩ + thống kê viên** | 1 câu hỏi `chuyenkhoa` + ký G4 (Phần D) | ⏳ chưa làm |
| **Bác sĩ, ngoài hệ thống, theo tuần/tháng** | Đăng ký OSF → nộp IRB → nhận số → ký G2 (Phần E) | ⏳ chưa làm |
| ~~Phần A (4 trường hành chính)~~ | ~~Điền chức danh/điện thoại/email~~ | ✅ 3/4 xong 13/09 |
| ~~Phần B (registry)~~ | ~~Sửa OSF Registries~~ | ✅ xong 13/09 |

_Cần bác sĩ kiểm chứng toàn bộ nội dung trước khi ký/nộp. Tài liệu này chỉ tổ chức lại thông tin đã
có trong hệ thống, không thay thế việc bác sĩ tự đọc từng tài liệu gốc trước khi ký._
