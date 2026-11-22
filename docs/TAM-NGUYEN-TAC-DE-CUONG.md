# Ma trận 8 nguyên tắc của đề cương (K20), trục tổng 5 tiêu chí và sổ đọc từng đơn vị (K21)

Ngày: 22/11/2026. Công cụ: `tools/tam_nguyen_tac_de_cuong.py` (ma trận, trục tổng, K20) và `tools/so_doc_de_cuong.py`
(sổ đọc, K21). Cả hai nối vào `tools/kiem_de_cuong_nop_hoi_dong.py` bằng hook tối thiểu.

## 1. Vì sao

Bác sĩ chủ nhiệm (22/11/2026): «Đề cương nghiên cứu theo từng tiêu chuẩn và từng tiêu chuẩn trong từng cấu trúc đề cương
nghiên cứu phải Tính trung thực và minh bạch (Integrity), Tính khoa học (Scientific Validity), Tính đạo đức (Ethical
Conduct), Tính khách quan (Objectivity), Tính tái lập (Reproducibility), Tính hợp lệ và tin cậy (Validity &
Reliability), Tôn trọng đối tượng nghiên cứu, Kiểm soát chất lượng liên tục». Nguyên tắc tổng: «Mỗi quyết định trong
nghiên cứu phải dựa trên bằng chứng khoa học, được thực hiện một cách đạo đức, được kiểm chứng khách quan, và chỉ được
chuyển sang bước tiếp theo khi bước hiện tại đã đạt chuẩn xác định trước.» Thêm hai luật cùng ngày: trục tổng 5 tiêu
chí («Một đề cương nghiên cứu y khoa tốt phải trả lời được một câu hỏi có giá trị bằng phương pháp khoa học phù hợp, khả
thi về triển khai, tuân thủ đạo đức và tạo ra kết quả có thể kiểm chứng.») và đọc từng đơn vị trước khi giao («Đề cương
phải được đọc từng câu từng chữ trước khi hoàn thành đưa cho tôi»).

## 2. Tám nguyên tắc — định nghĩa vận hành và nguồn

Nguồn có PMID đã tra PubMed và kiểm rút bài bằng `tools/check_citation_retraction.py` ngày 22/11/2026 (8/8 sạch ở tầng
PubMed). Số đoạn Tuyên bố Helsinki 2024 đối chiếu trang chính thức WMA ngày 22/11/2026. Văn bản quy phạm ghi tên, phiên
bản, năm, không gán định danh.

| Khoá | Nguyên tắc | Định nghĩa vận hành | Nguồn |
|---|---|---|---|
| `trung_thuc` | Tính trung thực và minh bạch (Integrity) | Mọi khẳng định và con số có nguồn thật truy được; một thông số mang cùng giá trị ở mọi hồ sơ; khai kinh phí, xung đột lợi ích, đăng ký; không dẫn bài đã rút | Singapore Statement on Research Integrity 2010 (PMID 21390871); Tuyên bố Helsinki 2024 §22, §35, §36 (PMID 39425955); TOP 2025 (PMID 42557573) |
| `khoa_hoc` | Tính khoa học (Scientific Validity) | Câu hỏi dựa trên hiểu biết đầy đủ y văn và khoảng trống thật; thiết kế, cỡ mẫu, phân tích hợp mục tiêu; đủ mục chuẩn báo cáo theo thiết kế | Helsinki 2024 §21; CIOMS 2016 |
| `dao_duc` | Tính đạo đức (Ethical Conduct) | Chỉ tiến hành sau khi Hội đồng Đạo đức chấp thuận; nguy cơ–gánh nặng cân với lợi ích; nhóm dễ tổn thương được bảo vệ; kế hoạch an toàn tương xứng | Helsinki 2024 §16–18, §19–20, §23; CIOMS 2016; Thông tư 43/2024/TT-BYT; ICH E6(R3) |
| `khach_quan` | Tính khách quan (Objectivity) | Quyết định phân tích và kết cục định trước, khoá trước dữ liệu, không đổi; kiểm soát sai lệch có phân tích tương ứng; vai trò độc lập; không khái quát quá chứng cứ | ICH E9 và E9(R1); TOP 2025; Singapore Statement |
| `tai_lap` | Tính tái lập (Reproducibility) | Người khác làm lại được: từ điển biến, công thức phái sinh đã duyệt, đặc tả phân tích máy đọc, phần mềm và hạt giống, DMP, tham số cỡ mẫu, lượt tìm y văn | TOP 2015 (PMID 26113702); TOP 2025; ICH E6(R3); PRISMA-S (PMID 34285662) |
| `hop_le_tin_cay` | Tính hợp lệ và tin cậy (Validity & Reliability) | Biến định nghĩa và đo đúng khái niệm, ổn định; công cụ có đặc tính đo lường; biến khớp công cụ và từ điển | COSMIN taxonomy 2010 (PMID 20494804); COSMIN checklist 2010 (PMID 20169472) |
| `ton_trong` | Tôn trọng đối tượng nghiên cứu | Đồng thuận tự nguyện hoặc căn cứ miễn hợp pháp; quyền từ chối/rút lui không ảnh hưởng chăm sóc; khử định danh; bảo vệ dữ liệu cá nhân | Helsinki 2024 §24, §26; CIOMS 2016 Hướng dẫn 10, 12; Thông tư 43/2024/TT-BYT; Luật 91/2025/QH15 |
| `kiem_soat_cl` | Kiểm soát chất lượng liên tục | Chất lượng theo thiết kế: yếu tố trọng yếu chất lượng, kế hoạch giám sát, sổ rủi ro có CAPA và người chịu trách nhiệm, luật kiểm dữ liệu, rà lại định kỳ | ICH E6(R3) |

Nguồn của phép đo trích hồ sơ: Gilbert EH và cs. Ann Emerg Med 1996;27(3):305-8 (PMID 8599488) — độ tin cậy giữa người
trích hồ sơ.

## 3. Cách đọc ma trận

- **Hàng** = 18 phần đề cương theo khoá bền `skill_standards.DE_CUONG_SECTION_KEYS` (tiêu đề lấy qua
  `de_cuong_section`). Dòng văn bản được gán phần theo tiêu đề sâu nhất chứa nó (`phan_theo_dong`): khuôn 18 mục, khuôn
  BVQY175 và bản cũ đều nhận được; tiêu đề con của Đặt vấn đề/Tổng quan mang phần của chương (trừ «MỤC TIÊU»), tiêu đề
  con của chương Dự kiến kết quả mang phần của chương (trừ «Hạn chế»).
- **Cột** = 8 nguyên tắc.
- **Ô**: 🔴 có phép đo đỏ · 🟢 mọi phép đo áp dụng đều xanh · ⚪ không có phép đo, hoặc còn phép đo «chưa đo được» (kể
  cả khi phép đo khác xanh — không bao giờ báo xanh khi một phần chưa đo) · — không áp dụng theo điều kiện của hệ
  (`nhat_quan_xuyen_cong.thong_so_bat_buoc` cho phần Cỡ mẫu; `kiem_chuan_de_cuong_theo_muc._KHONG_NGUOI_THAM_GIA` và
  `kiem_de_cuong_nop_hoi_dong.KHONG_CAN_DONG_Y` cho cột Tôn trọng đối tượng).
- **Trạng thái từng loại phép đo**: luật K theo dòng (lỗi «dòng N» rơi vào phần chứa dòng N); mục K17 đạt/thiếu ⇒
  xanh/đỏ, «cảnh báo» và «chưa đo» ⇒ ⚪ (mục thiếu của chuẩn K17 còn chỉ cảnh báo vẫn đỏ trong ma trận — đó là mục chuẩn
  còn thiếu thật); trục nhất quán khớp ⇒ xanh, lệch cứng/lệch mềm ⇒ đỏ, cần xem/chưa đủ để so ⇒ ⚪, trục vắng ⇒ không áp
  dụng (trừ thông số bắt buộc theo thiết kế ⇒ ⚪); tiêu chí cổng chấm sống PASS ⇒ xanh, BLOCK ⇒ đỏ, REVIEW ⇒ ⚪, cổng
  chưa có checkpoint ⇒ ⚪ (khâu sau chưa tới không làm đỏ đề cương).
- **Lệnh**: `python3 tools/tam_nguyen_tac_de_cuong.py --study <mã> [--goc <thư mục chứa exports/>] [--json] [--ghi]`;
  mã thoát 0 không 🔴 không ⚪ · 1 có 🔴 · 2 chỉ còn ⚪ · 3 tham số sai.

## 4. K20 — chặn gì, báo gì

- Ô 🔴 do phép đo NGOÀI K1–K19 ⇒ lỗi K20, CHẶN. Lỗi của chính K1–K19 đã được luật đó báo tại chỗ, K20 không nhân đôi;
  hai trục nhất quán đo lại đúng điều của luật K (`tai_lieu_nop_co_mau` ≈ K5, `trich_dan_tong_quan` ≈ K6/K12) cũng
  không chặn lần hai (`NQ_TRUNG_K`).
- Ô ⚪ chỉ BÁO kèm số lượng, CHƯA chặn — chặn ⚪ khi phép đo chưa xây là làm đỏ giả.
- Cảnh báo in TRỤC TỔNG 5 tiêu chí đầu tiên.
- Chốt chống gọi vòng: trong lúc dựng ma trận, mọi lời gọi `kiem()` lồng bên trong trả K20 rỗng (`_DANG_TINH`).

## 5. Trục tổng 5 tiêu chí

| Tiêu chí | Thành phần trong ma trận (bộ lọc) | Chốt hệ ngoài ma trận |
|---|---|---|
| Câu hỏi có giá trị | NQ:tong_quan_khoang_trong; G0-AUTO-02/03/06; TN-TL-01; K10 ở Đặt vấn đề/Tổng quan; mục K17 của Đặt vấn đề/Tổng quan; HĐKH mục phiếu 1 | FINER «thú vị», «mới», «phù hợp» (G0); G0 chấm sống |
| Phương pháp khoa học phù hợp | mọi mục K17; mọi trục nhất quán; tiêu chí G1/G3/G4; sai lệch ↔ SAP, ma trận mục tiêu–biến, biến ↔ đề cương; HĐKH mục phiếu 2 | G3, G4 chấm sống |
| Khả thi về triển khai | K3 chương kế hoạch thực hiện; TN-QC-02/03/04/06 | FINER «khả thi»; G3.recruitment_feasibility_confirmed; G1-AUTO-05 (A13/A13b) |
| Tuân thủ đạo đức | mọi phép đo cột Đạo đức và Tôn trọng đối tượng; TN-TT-01, TN-KQ-04 | FINER «đạo đức»; G2 chấm sống |
| Kết quả kiểm chứng được | TN-KQ-01; NQ:ket_cuc_chinh, NQ:thoi_diem_ket_cuc; G4-AUTO-06/07/11; phép đo «Biến số × Hợp lệ–tin cậy»; mọi phép đo cột Tái lập | — |

FINER đọc nguyên văn G0: «ĐẠT» ⇒ xanh, «ĐẠT CÓ ĐIỀU KIỆN» ⇒ ⚪ (điều kiện còn mở), «KHÔNG ĐẠT/CHƯA ĐẠT» ⇒ đỏ. Cổng chấm
sống PASS/READY ⇒ xanh, BLOCKED ⇒ đỏ, còn lại ⇒ ⚪. Trục tổng chỉ báo; chặn vẫn theo ô.

«Cỡ mẫu so khung mẫu» chưa có phép đo số: hệ chưa lưu cỡ khung mẫu máy đọc (G3_checkpoint của hai đề tài thật không có
trường này); thành phần khả thi hiện dựa vào xác nhận khả năng tuyển G3 và FINER khả thi.

## 6. Phép đo mới (mã `TN-…`)

| Mã | Ô | Đỏ khi | ⚪ khi | Nguồn dữ kiện |
|---|---|---|---|---|
| TN-TON-01 | Đạo đức × Tôn trọng | phần đạo đức nói khác G2 về miễn đồng thuận; lấy đồng thuận mà không có bản thông tin/phiếu đồng ý | G2 chưa khai `icf_waiver_requested` | study_meta G2 + văn bản |
| TN-TON-02 | Đạo đức × Tôn trọng | lấy đồng thuận mà không nêu quyền từ chối/rút lui hoặc không nêu «không ảnh hưởng» | G2 chưa khai | văn bản phần đạo đức + phụ lục phiếu đồng ý |
| TN-TON-03 | Quản trị dữ liệu × Tôn trọng | `data_governance` thiếu một trong 4 lớp (khử định danh, truy cập, lưu trữ, sự cố) hoặc còn ô [CẦN…] | chưa có `data_governance` | study_meta |
| TN-TON-05 | Công cụ × Tôn trọng | phiếu có ô định danh trực tiếp mà không nêu tách riêng/giả danh hoá | không có phần công cụ | văn bản |
| TN-DD-01 | Đạo đức × Đạo đức | `benefit_risk_rationale` trống/[CẦN…] | G1 chưa có trường | study_meta G1 |
| TN-DD-02 | Đối tượng × Đạo đức | tiêu chuẩn chọn có nhóm dễ tổn thương mà phần đạo đức thiếu biện pháp đúng loại | không xác định được | văn bản |
| TN-TT-01 | Đạo đức × Trung thực | G2.coi thiếu tóm tắt hoặc đề cương không nêu xung đột lợi ích | G2 chưa có coi | study_meta + văn bản |
| TN-KQ-04 | Đạo đức × Khách quan | có xung đột cơ cấu mà quản lý không giao người độc lập | — | study_meta + văn bản |
| TN-TT-02 | Tiến độ × Trung thực | đề cương không nêu nguồn kinh phí hoặc nói khác G2 | G2 chưa khai `external_funding` | study_meta + văn bản |
| TN-KQ-01 | SAP × Khách quan | có dữ liệu mà SAP chưa khoá hoặc khoá sau dữ liệu | chưa có dữ liệu và SAP chưa khoá | study_meta, G4 chấm sống, G5 |
| TN-KQ-02 | Công cụ × Khách quan | trích hồ sơ không có trích lại độc lập kèm hệ số đồng thuận; tổng quan không có hai người độc lập | — (không áp dụng nếu không trích tay) | văn bản |
| TN-KQ-03 | Tiến độ × Khách quan | không bao giờ đỏ | chưa nêu người kiểm tra độc lập | study_meta G1 |
| TN-QC-01/02 | Thiết kế/Tiến độ × KSCL | thiết kế can thiệp mà CTQ/kế hoạch giám sát trống | thiết kế quan sát chưa khai | study_meta G1 |
| TN-QC-03/04 | Tiến độ × KSCL | sổ rủi ro đã dựng mà thiếu biện pháp/CAPA/người chịu trách nhiệm, hoặc xác suất/tác động trống/[CẦN…] | sổ chưa dựng | study_meta G1.risk_register |
| TN-QC-05 | Quản trị dữ liệu × KSCL | `_luat-dq.csv` trỏ biến không có trong bộ biến | chưa có tệp luật | `_luat-dq.csv`, bộ biến |
| TN-QC-06/07/08 | Công cụ/Đối tượng/SAP × KSCL | không bao giờ đỏ (phép đo có mặt) | đề cương chưa nêu chạy thử / nhật ký tuyển chọn / kiểm tra chéo phân tích | văn bản |
| TN-TL-01 | Tổng quan × Tái lập | `search_provenance` thiếu cơ sở dữ liệu, ngày tra hoặc truy vấn | chưa có G0_pubmed_raw.json | G0 |
| HDKH:1–4 | (xem bảng ánh xạ) | biên bản còn hiệu lực có nhận xét nghiêm trọng/cần sửa ở phần đó | không có biên bản có SHA trùng bản đề cương | `hoi_dong_khoa_hoc/BIEN_BAN_HDKH_*.json` |

## 7. Sổ đọc từng đơn vị (K21)

- Đơn vị: câu (tách câu tiếng Việt, không cắt ở số thập phân, viết tắt, chữ cái đầu tên, số thứ tự lựa chọn, số hiệu
  mục), tiêu đề, hàng bảng (băm gồm tên bảng + hàng tiêu đề cột + hàng), hình (băm gồm chú thích, đường dẫn, băm tệp
  ảnh, băm tệp dữ liệu vẽ cùng tên nếu có), công thức, mục tài liệu tham khảo (`tltk:<số>`).
- Mã ổn định: loại + mục + thứ tự; mã băm nội dung 16 hex. Bản ghi `dat` mang băm khác băm hiện hành ⇒ chưa đọc.
- K21: có `G10_checkpoint.json` và G10 chấm sống READY/PASS mà phủ < 100% hoặc còn đơn vị «sua» ⇒ CHẶN; chưa trình ⇒
  chỉ báo tỷ lệ phủ.
- Lệnh: `so_doc_de_cuong.py tach|trang-thai|ghi --study <mã> [--goc …] [--tu <json>]`; sổ
  `SO_DOC_DE_CUONG_<mã>.json`.

## 8. Bảng ánh xạ phép đo → ô (sinh từ `bang_anh_xa()`)

| Phép đo | Nguồn | Phần | Nguyên tắc | Lý do |
|---|---|---|---|---|
| K10 | Số liệu kiểu kết quả có trích dẫn trong cùng mệnh đề | Đặt vấn đề | Tính trung thực và minh bạch | con số không nguồn là khẳng định không truy được (Singapore: trung thực; bác sĩ 20/11/2026) |
| K10 | Số liệu kiểu kết quả có trích dẫn trong cùng mệnh đề | Tổng quan tài liệu và khung lý thuyết | Tính trung thực và minh bạch | con số không nguồn là khẳng định không truy được (Singapore: trung thực; bác sĩ 20/11/2026) |
| K10 | Số liệu kiểu kết quả có trích dẫn trong cùng mệnh đề | Dự kiến kết quả và khung bảng trống | Tính trung thực và minh bạch | con số không nguồn là khẳng định không truy được (Singapore: trung thực; bác sĩ 20/11/2026) |
| K12 | Mỗi tài liệu tham khảo đỡ một câu cụ thể, không trích gộp | Đặt vấn đề | Tính trung thực và minh bạch | trích gộp/không trích làm mất truy nguyên từng khẳng định |
| K12 | Mỗi tài liệu tham khảo đỡ một câu cụ thể, không trích gộp | Tổng quan tài liệu và khung lý thuyết | Tính trung thực và minh bạch | trích gộp/không trích làm mất truy nguyên từng khẳng định |
| K12 | Mỗi tài liệu tham khảo đỡ một câu cụ thể, không trích gộp | Dự kiến kết quả và khung bảng trống | Tính trung thực và minh bạch | trích gộp/không trích làm mất truy nguyên từng khẳng định |
| K12 | Mỗi tài liệu tham khảo đỡ một câu cụ thể, không trích gộp | Tài liệu tham khảo Vancouver/NLM | Tính trung thực và minh bạch | trích gộp/không trích làm mất truy nguyên từng khẳng định |
| K15 | Khẳng định khái quát/định lượng mơ hồ có trích dẫn | Đặt vấn đề | Tính khách quan | «đa số», «đã được chứng minh» không nguồn là khái quát vượt chứng cứ |
| K15 | Khẳng định khái quát/định lượng mơ hồ có trích dẫn | Tổng quan tài liệu và khung lý thuyết | Tính khách quan | «đa số», «đã được chứng minh» không nguồn là khái quát vượt chứng cứ |
| K15 | Khẳng định khái quát/định lượng mơ hồ có trích dẫn | Dự kiến kết quả và khung bảng trống | Tính khách quan | «đa số», «đã được chứng minh» không nguồn là khái quát vượt chứng cứ |
| K16 | Câu nêu đã tra nguồn khớp nhật ký PRISMA-S | Tổng quan tài liệu và khung lý thuyết | Tính trung thực và minh bạch | khai đã tra một nguồn mà nhật ký không ghi là khai sai quá trình tìm |
| K3 | Có chương «đặt vấn đề» | Đặt vấn đề | Tính khoa học | thiếu chương thì Hội đồng không thẩm định được nội dung đó |
| K3 | Có chương «mục tiêu nghiên cứu» | Mục tiêu | Tính khoa học | thiếu chương thì Hội đồng không thẩm định được nội dung đó |
| K3 | Có chương «tổng quan tài liệu» | Tổng quan tài liệu và khung lý thuyết | Tính khoa học | thiếu chương thì Hội đồng không thẩm định được nội dung đó |
| K3 | Có chương «đối tượng và phương pháp» | Thiết kế và bối cảnh | Tính khoa học | thiếu chương thì Hội đồng không thẩm định được nội dung đó |
| K3 | Có chương «đạo đức nghiên cứu» | Đạo đức nghiên cứu | Tính đạo đức | thiếu chương thì Hội đồng không thẩm định được nội dung đó |
| K3 | Có chương «dự kiến kết quả» | Dự kiến kết quả và khung bảng trống | Tính khoa học | thiếu chương thì Hội đồng không thẩm định được nội dung đó |
| K3 | Có chương «kế hoạch thực hiện» | Tiến độ và nguồn lực | Tính khoa học | thiếu chương thì Hội đồng không thẩm định được nội dung đó |
| K3 | Có chương «tài liệu tham khảo» | Tài liệu tham khảo Vancouver/NLM | Tính trung thực và minh bạch | thiếu chương thì Hội đồng không thẩm định được nội dung đó |
| K3 | Có chương «phụ lục bản thông tin/phiếu đồng ý» | Đạo đức nghiên cứu | Tôn trọng đối tượng nghiên cứu | thiếu chương thì Hội đồng không thẩm định được nội dung đó |
| K3 | Có chương «phụ lục công cụ thu thập» | Công cụ và quy trình thu thập | Tính tái lập | thiếu chương thì Hội đồng không thẩm định được nội dung đó |
| K5 | Cỡ mẫu, hiệu ứng thiết kế đã chốt ở G3 có trong đề cương | Cỡ mẫu | Tính trung thực và minh bạch | con số trình Hội đồng phải là con số đã tính và chốt |
| K6 | Mọi PMID nằm trong biên nhận rút bài A12 sạch | Tài liệu tham khảo Vancouver/NLM | Tính trung thực và minh bạch | không dẫn bài đã rút |
| K9 | Biểu bảng dự kiến đúng chuẩn, mỗi mục tiêu có bảng/biểu, ước lượng kèm KTC 95% | Dự kiến kết quả và khung bảng trống | Tính khoa học | kết quả dự kiến phải trả lời từng mục tiêu bằng ước lượng có độ chính xác |
| K13 | Tài liệu có PMID đúng Vancouver/NLM theo biên nhận A12 | Tài liệu tham khảo Vancouver/NLM | Tính tái lập | trích dẫn đúng định danh để người đọc tìm lại được nguồn |
| K17 (mục có phần «bia») | mục chuẩn theo thiết kế | Tóm tắt | Tính trung thực và minh bạch | thông tin nhận diện đề tài, đăng ký, nhà tài trợ |
| K17 (mục có phần «dau») | mục chuẩn theo thiết kế | Tóm tắt | Tính trung thực và minh bạch | tên đề tài nêu đúng thiết kế |
| K17 (mục có phần «tom_tat») | mục chuẩn theo thiết kế | Tóm tắt | Tính trung thực và minh bạch | tóm tắt nêu đúng thiết kế và nội dung |
| K17 (mục có phần «dat_van_de») | mục chuẩn theo thiết kế | Đặt vấn đề | Tính khoa học | lý do khoa học của đề tài |
| K17 (mục có phần «tong_quan») | mục chuẩn theo thiết kế | Tổng quan tài liệu và khung lý thuyết | Tính khoa học | nền y văn và khoảng trống |
| K17 (mục có phần «cau_hoi») | mục chuẩn theo thiết kế | Câu hỏi nghiên cứu và giả thuyết | Tính khoa học | câu hỏi/giả thuyết định trước |
| K17 (mục có phần «muc_tieu») | mục chuẩn theo thiết kế | Mục tiêu | Tính khoa học | mục tiêu cụ thể đo được |
| K17 (mục có phần «thiet_ke») | mục chuẩn theo thiết kế | Thiết kế và bối cảnh | Tính khoa học | thiết kế hợp câu hỏi |
| K17 (mục có phần «dia_diem») | mục chuẩn theo thiết kế | Thiết kế và bối cảnh | Tính tái lập | bối cảnh, thời gian đủ để làm lại |
| K17 (mục có phần «ngau_nhien») | mục chuẩn theo thiết kế | Thiết kế và bối cảnh | Tính khách quan | ngẫu nhiên hoá/giấu phân bổ/làm mù chống sai lệch |
| K17 (mục có phần «can_thiep») | mục chuẩn theo thiết kế | Thiết kế và bối cảnh | Tính tái lập | can thiệp mô tả đủ để lặp lại |
| K17 (mục có phần «tiep_can») | mục chuẩn theo thiết kế | Thiết kế và bối cảnh | Tính khoa học | cách tiếp cận định tính hợp câu hỏi |
| K17 (mục có phần «nhom_nc») | mục chuẩn theo thiết kế | Thiết kế và bối cảnh | Tính khách quan | phản tư/vai trò người thu thập định tính |
| K17 (mục có phần «doi_tuong») | mục chuẩn theo thiết kế | Đối tượng nghiên cứu | Tính khoa học | tiêu chuẩn chọn/loại định nghĩa đúng quần thể |
| K17 (mục có phần «chon_mau») | mục chuẩn theo thiết kế | Đối tượng nghiên cứu | Tính khách quan | quy trình chọn mẫu chống sai lệch chọn |
| K17 (mục có phần «chon_nc») | mục chuẩn theo thiết kế | Đối tượng nghiên cứu | Tính khách quan | quy trình chọn nghiên cứu chống sai lệch chọn |
| K17 (mục có phần «trinh_bay_ca») | mục chuẩn theo thiết kế | Đối tượng nghiên cứu | Tính khoa học | mô tả ca đủ thông tin lâm sàng |
| K17 (mục có phần «co_mau») | mục chuẩn theo thiết kế | Cỡ mẫu | Tính khoa học | cỡ mẫu có cơ sở |
| K17 (mục có phần «bien_so») | mục chuẩn theo thiết kế | Biến số và kết cục | Tính hợp lệ và tin cậy | biến định nghĩa và đo đúng khái niệm |
| K17 (mục có phần «phoi_nhiem») | mục chuẩn theo thiết kế | Biến số và kết cục | Tính hợp lệ và tin cậy | phơi nhiễm định nghĩa và đo đúng |
| K17 (mục có phần «du_bao») | mục chuẩn theo thiết kế | Biến số và kết cục | Tính hợp lệ và tin cậy | biến dự báo/kết cục dự báo định nghĩa đúng |
| K17 (mục có phần «xet_nghiem») | mục chuẩn theo thiết kế | Biến số và kết cục | Tính hợp lệ và tin cậy | xét nghiệm và chuẩn tham chiếu đo đúng |
| K17 (mục có phần «bang_bien») | mục chuẩn theo thiết kế | Biến số và kết cục | Tính tái lập | bảng biến/mã hoá đủ để nhập và phân tích lại |
| K17 (mục có phần «danh_muc_ma») | mục chuẩn theo thiết kế | Biến số và kết cục | Tính tái lập | danh mục mã đủ để làm lại |
| K17 (mục có phần «cong_cu») | mục chuẩn theo thiết kế | Công cụ và quy trình thu thập | Tính hợp lệ và tin cậy | công cụ đo có đặc tính đo lường |
| K17 (mục có phần «phieu») | mục chuẩn theo thiết kế | Công cụ và quy trình thu thập | Tính tái lập | phiếu thu thập đính kèm để lặp lại |
| K17 (mục có phần «quy_trinh») | mục chuẩn theo thiết kế | Công cụ và quy trình thu thập | Tính tái lập | quy trình thu thập mô tả đủ |
| K17 (mục có phần «trich_xuat») | mục chuẩn theo thiết kế | Công cụ và quy trình thu thập | Tính tái lập | quy trình trích xuất mô tả đủ |
| K17 (mục có phần «tim_kiem») | mục chuẩn theo thiết kế | Công cụ và quy trình thu thập | Tính tái lập | chiến lược tìm tái lập được |
| K17 (mục có phần «phu_luc_tim») | mục chuẩn theo thiết kế | Công cụ và quy trình thu thập | Tính tái lập | chuỗi tìm đầy đủ trong phụ lục |
| K17 (mục có phần «quan_ly_dl») | mục chuẩn theo thiết kế | Quản trị dữ liệu và bảo mật | Tính tái lập | quản lý dữ liệu đủ để truy vết |
| K17 (mục có phần «phan_tich») | mục chuẩn theo thiết kế | Kế hoạch phân tích thống kê | Tính khoa học | phương pháp phân tích hợp mục tiêu |
| K17 (mục có phần «tong_hop») | mục chuẩn theo thiết kế | Kế hoạch phân tích thống kê | Tính khoa học | phương pháp tổng hợp hợp câu hỏi |
| K17 (mục có phần «kinh_te») | mục chuẩn theo thiết kế | Kế hoạch phân tích thống kê | Tính khoa học | phương pháp đánh giá kinh tế |
| K17 (mục có phần «du_kien_kq») | mục chuẩn theo thiết kế | Dự kiến kết quả và khung bảng trống | Tính khoa học | kết quả dự kiến theo mục tiêu |
| K17 (mục có phần «ban_luan») | mục chuẩn theo thiết kế | Dự kiến kết quả và khung bảng trống | Tính khách quan | bàn luận không vượt chứng cứ |
| K17 (mục có phần «sai_so») | mục chuẩn theo thiết kế | Sai lệch, hạn chế và kiểm soát | Tính khách quan | nhận diện và khống chế sai lệch |
| K17 (mục có phần «nguy_co») | mục chuẩn theo thiết kế | Sai lệch, hạn chế và kiểm soát | Tính khách quan | đánh giá nguy cơ sai lệch |
| K17 (mục có phần «han_che») | mục chuẩn theo thiết kế | Sai lệch, hạn chế và kiểm soát | Tính trung thực và minh bạch | nêu thẳng hạn chế |
| K17 (mục có phần «dao_duc») | mục chuẩn theo thiết kế | Đạo đức nghiên cứu | Tính đạo đức | chấp thuận và nội dung đạo đức |
| K17 (mục có phần «giam_sat») | mục chuẩn theo thiết kế | Đạo đức nghiên cứu | Kiểm soát chất lượng liên tục | giám sát an toàn/biến cố |
| K17 (mục có phần «pho_bien») | mục chuẩn theo thiết kế | Kế hoạch phổ biến kết quả/ứng dụng | Tính trung thực và minh bạch | đăng ký và phổ biến minh bạch |
| K17 (mục có phần «kinh_phi») | mục chuẩn theo thiết kế | Tiến độ và nguồn lực | Tính trung thực và minh bạch | khai nguồn kinh phí |
| K17 (mục có phần «nhan_luc») | mục chuẩn theo thiết kế | Tiến độ và nguồn lực | Kiểm soát chất lượng liên tục | phân công trách nhiệm thực hiện |
| K17 (mục có phần «tien_do») | mục chuẩn theo thiết kế | Tiến độ và nguồn lực | Kiểm soát chất lượng liên tục | tiến độ theo mốc |
| K17 (ghi đè theo chủ đề) | chủ đề khớp /consent|đồng (ý|thuận)|privacy|confidential|riêng …/ | (phần của mục) | Tôn trọng đối tượng nghiên cứu | đồng thuận/riêng tư của người tham gia |
| K17 (ghi đè theo chủ đề) | chủ đề khớp /conflict|competing|xung đột lợi ích|fund|tài trợ|k…/ | (phần của mục) | Tính trung thực và minh bạch | khai kinh phí/xung đột lợi ích/đăng ký |
| NQ:co_mau | nhat_quan_xuyen_cong | Cỡ mẫu | Tính trung thực và minh bạch | cỡ mẫu cùng một giá trị ở G3, đăng ký, SAP |
| NQ:alpha | nhat_quan_xuyen_cong | Cỡ mẫu | Tính trung thực và minh bạch | alpha cùng giá trị ở G3 và SAP |
| NQ:power | nhat_quan_xuyen_cong | Cỡ mẫu | Tính trung thực và minh bạch | lực mẫu cùng giá trị ở G3 và SAP |
| NQ:sai_so_d | nhat_quan_xuyen_cong | Cỡ mẫu | Tính trung thực và minh bạch | sai số cho phép cùng giá trị ở G3 và SAP |
| NQ:co_mau_tinh_lai | nhat_quan_xuyen_cong | Cỡ mẫu | Tính tái lập | tính lại từ tham số đã ghim ra đúng cỡ mẫu |
| NQ:co_mau_cho_ket_cuc | nhat_quan_xuyen_cong | Cỡ mẫu | Tính khoa học | cỡ mẫu được tính cho kết cục chính |
| NQ:tai_lieu_nop_co_mau | nhat_quan_xuyen_cong | Cỡ mẫu | Tính trung thực và minh bạch | mọi tài liệu nộp ghi đúng cỡ mẫu |
| NQ:chon_mau_co_mau | nhat_quan_xuyen_cong | Đối tượng nghiên cứu | Tính khoa học | chọn mẫu cụm khớp hiệu ứng thiết kế của cỡ mẫu |
| NQ:ky_thuat_chon_mau | nhat_quan_xuyen_cong | Đối tượng nghiên cứu | Tính trung thực và minh bạch | kỹ thuật chọn mẫu mô tả giống nhau ở mọi hồ sơ |
| NQ:thiet_ke | nhat_quan_xuyen_cong | Thiết kế và bối cảnh | Tính trung thực và minh bạch | mã thiết kế cùng giá trị ở mọi cổng và đăng ký |
| NQ:mo_ta_thiet_ke | nhat_quan_xuyen_cong | Thiết kế và bối cảnh | Tính trung thực và minh bạch | thiết kế, tuyển mẫu, phiên bản SAP mô tả nhất quán |
| NQ:chuan_bao_cao | nhat_quan_xuyen_cong | Thiết kế và bối cảnh | Tính tái lập | cùng bộ chuẩn báo cáo ở mọi hồ sơ |
| NQ:quan_the | nhat_quan_xuyen_cong | Đối tượng nghiên cứu | Tính trung thực và minh bạch | quần thể diễn đạt nhất quán giữa các cổng |
| NQ:ket_cuc_chinh | nhat_quan_xuyen_cong | Biến số và kết cục | Tính khách quan | kết cục chính không đổi giữa các cổng (chống đổi kết cục) |
| NQ:thoi_diem_ket_cuc | nhat_quan_xuyen_cong | Biến số và kết cục | Tính khách quan | thời điểm đo kết cục chính không đổi |
| NQ:loai_gia_thuyet | nhat_quan_xuyen_cong | Câu hỏi nghiên cứu và giả thuyết | Tính khách quan | loại giả thuyết định trước, cùng ở G0, G3, SAP |
| NQ:cau_hoi_gia_thuyet | nhat_quan_xuyen_cong | Câu hỏi nghiên cứu và giả thuyết | Tính khoa học | câu hỏi/giả thuyết phủ mục tiêu |
| NQ:muc_tieu_phan_tich | nhat_quan_xuyen_cong | Kế hoạch phân tích thống kê | Tính khoa học | mỗi mục tiêu có phân tích trong SAP |
| NQ:muc_tieu_ho_so_g2 | nhat_quan_xuyen_cong | Mục tiêu | Tính trung thực và minh bạch | mục tiêu trình Hội đồng Đạo đức giống mục tiêu đã chốt |
| NQ:tong_quan_khoang_trong | nhat_quan_xuyen_cong | Tổng quan tài liệu và khung lý thuyết | Tính khoa học | có khoảng trống nghiên cứu |
| NQ:trich_dan_tong_quan | nhat_quan_xuyen_cong | Tổng quan tài liệu và khung lý thuyết | Tính trung thực và minh bạch | danh mục tài liệu khớp trích dẫn trong thân |
| NQ:ten_de_tai | nhat_quan_xuyen_cong | Tóm tắt | Tính trung thực và minh bạch | tên đề tài giống nhau ở mọi nơi |
| NQ:cong_cu_tu_dien | nhat_quan_xuyen_cong | Công cụ và quy trình thu thập | Tính hợp lệ và tin cậy | mã đáp án của phiếu khớp từ điển nhập liệu |
| NQ:cong_cu_do_luong | nhat_quan_xuyen_cong | Công cụ và quy trình thu thập | Tính hợp lệ và tin cậy | đặc tính đo lường của công cụ truy nguyên được |
| NQ:quy_trinh_du_lieu | nhat_quan_xuyen_cong | Quản trị dữ liệu và bảo mật | Kiểm soát chất lượng liên tục | quyết định quy trình dữ liệu không mâu thuẫn |
| NQ:de_cuong_nop | nhat_quan_xuyen_cong | Tóm tắt | Tính trung thực và minh bạch | phiên bản, kế hoạch phân tích, phiếu đồng ý, kinh phí khớp hồ sơ |
| NQ:dac_ta_cho_bo_bien | nhat_quan_xuyen_cong | Kế hoạch phân tích thống kê | Tính tái lập | đặc tả phân tích dùng đúng bộ biến |
| NQ:dac_ta_phan_tich | nhat_quan_xuyen_cong | Kế hoạch phân tích thống kê | Tính tái lập | đặc tả phân tích máy đọc chạy được |
| G0-AUTO-02 | tiêu chí cổng (chấm sống) | Đặt vấn đề | Tính trung thực và minh bạch | nền bằng chứng là PMID thật từ PubMed |
| G0-AUTO-03 | tiêu chí cổng (chấm sống) | Tổng quan tài liệu và khung lý thuyết | Tính trung thực và minh bạch | số kết quả tìm dùng để kết luận khoảng trống là số thật |
| G0-AUTO-06 | tiêu chí cổng (chấm sống) | Tổng quan tài liệu và khung lý thuyết | Tính khoa học | đã tra sổ đăng ký thử nghiệm trước khi khẳng định tính mới |
| G1-AUTO-02d | tiêu chí cổng (chấm sống) | Thiết kế và bối cảnh | Tính khoa học | thiết kế hợp loại câu hỏi đã chốt |
| G1-AUTO-02b | tiêu chí cổng (chấm sống) | Thiết kế và bối cảnh | Kiểm soát chất lượng liên tục | ICH E6(R3) Annex 2: phù hợp mục đích và giám sát |
| G1-AUTO-03 | tiêu chí cổng (chấm sống) | Thiết kế và bối cảnh | Tính khoa học | chuẩn báo cáo khớp thiết kế |
| G1-AUTO-03b | tiêu chí cổng (chấm sống) | Thiết kế và bối cảnh | Tính khoa học | chuẩn đề cương khớp thiết kế |
| G1-AUTO-04b | tiêu chí cổng (chấm sống) | Sai lệch, hạn chế và kiểm soát | Tính khách quan | so sánh phương án và kiểm soát đủ nhóm sai lệch |
| G1-AUTO-06 | tiêu chí cổng (chấm sống) | Tổng quan tài liệu và khung lý thuyết | Tính trung thực và minh bạch | bằng chứng trong sổ chứng cứ có PMID/DOI |
| G2-AUTO-01 | tiêu chí cổng (chấm sống) | Đạo đức nghiên cứu | Tính trung thực và minh bạch | hồ sơ không tự gán số phê duyệt, không PII, không tự xưng đã khoá |
| G2-AUTO-02b | tiêu chí cổng (chấm sống) | Đạo đức nghiên cứu | Tính đạo đức | Annex 2: hội đồng đạo đức, đồng thuận, riêng tư, quản trị dữ liệu |
| G2-AUTO-03 | tiêu chí cổng (chấm sống) | Đạo đức nghiên cứu | Tôn trọng đối tượng nghiên cứu | bộ hồ sơ có phiếu đồng ý đủ mục theo thiết kế |
| G2-AUTO-04 | tiêu chí cổng (chấm sống) | Kế hoạch phổ biến kết quả/ứng dụng | Tính trung thực và minh bạch | WHO TRDS đủ 24 mục |
| G2-AUTO-07 | tiêu chí cổng (chấm sống) | Đạo đức nghiên cứu | Tính đạo đức | kế hoạch an toàn tương xứng thiết kế |
| G2-AUTO-08 | tiêu chí cổng (chấm sống) | Kế hoạch phổ biến kết quả/ứng dụng | Tính trung thực và minh bạch | mục khoa học của đăng ký có nội dung thật |
| G2-AUTO-11 | tiêu chí cổng (chấm sống) | Kế hoạch phổ biến kết quả/ứng dụng | Tính trung thực và minh bạch | quyết định đăng ký khớp nghĩa vụ đăng ký (Helsinki §35) |
| G3-AUTO-05 | tiêu chí cổng (chấm sống) | Cỡ mẫu | Tính trung thực và minh bạch | effect size có định danh nguồn thật |
| G3-AUTO-06 | tiêu chí cổng (chấm sống) | Cỡ mẫu | Tính khoa học | effect size đọc từ toàn văn, không phải số thô |
| G3-AUTO-07 | tiêu chí cổng (chấm sống) | Cỡ mẫu | Tính khoa học | alpha/power theo quy ước, đã xử lý đa so sánh |
| G3-AUTO-08 | tiêu chí cổng (chấm sống) | Cỡ mẫu | Tính trung thực và minh bạch | tham số phụ của công thức có nguồn |
| G3-AUTO-12 | tiêu chí cổng (chấm sống) | Cỡ mẫu | Tính hợp lệ và tin cậy | thiết kế chùm: ICC có nguồn, hiệu ứng thiết kế đúng số học |
| G3-AUTO-13 | tiêu chí cổng (chấm sống) | Cỡ mẫu | Tính khoa học | cỡ mẫu chốt đủ lực, có phương pháp |
| G3-AUTO-14 | tiêu chí cổng (chấm sống) | Cỡ mẫu | Tính tái lập | tham số đã ghim đủ để chạy lại ra cùng cỡ mẫu |
| G3-AUTO-15 | tiêu chí cổng (chấm sống) | Cỡ mẫu | Tính tái lập | khai công thức và phần mềm/phiên bản |
| G4-AUTO-03 | tiêu chí cổng (chấm sống) | Kế hoạch phân tích thống kê | Tính trung thực và minh bạch | số liệu SAP khớp G3 hiện tại |
| G4-AUTO-04 | tiêu chí cổng (chấm sống) | Kế hoạch phân tích thống kê | Tính hợp lệ và tin cậy | phân tích đa biến có EPV/VIF |
| G4-AUTO-05 | tiêu chí cổng (chấm sống) | Kế hoạch phân tích thống kê | Tính khoa học | xử lý dữ liệu thiếu có nội dung thật |
| G4-AUTO-06 | tiêu chí cổng (chấm sống) | Kế hoạch phân tích thống kê | Tính khách quan | đa so sánh định trước |
| G4-AUTO-07 | tiêu chí cổng (chấm sống) | Kế hoạch phân tích thống kê | Tính khách quan | phân nhóm nhỏ định trước (chống HARKing) |
| G4-AUTO-08 | tiêu chí cổng (chấm sống) | Kế hoạch phân tích thống kê | Tính tái lập | phần mềm và hạt giống cụ thể |
| G4-AUTO-11 | tiêu chí cổng (chấm sống) | Kế hoạch phân tích thống kê | Tính khách quan | kết cục chính của SAP khớp câu hỏi đã chốt |
| G5-AUTO-01 | tiêu chí cổng (chấm sống) | Quản trị dữ liệu và bảo mật | Tính tái lập | có DMP, từ điển dữ liệu, mã làm sạch/kiểm chất lượng |
| G5-AUTO-02 | tiêu chí cổng (chấm sống) | Quản trị dữ liệu và bảo mật | Tôn trọng đối tượng nghiên cứu | từ điển dữ liệu không có định danh trực tiếp |
| G5-AUTO-03 | tiêu chí cổng (chấm sống) | Quản trị dữ liệu và bảo mật | Kiểm soát chất lượng liên tục | DMP phủ vòng đời dữ liệu theo ICH E6(R3) |
| G5-AUTO-11 | tiêu chí cổng (chấm sống) | Biến số và kết cục | Tính hợp lệ và tin cậy | từ điển nhập liệu ↔ đề cương ↔ phiếu đồng bộ |
| G5-AUTO-12 | tiêu chí cổng (chấm sống) | Biến số và kết cục | Tính tái lập | từ điển dựng từ bộ biến riêng, phủ ma trận mục tiêu–biến |
| G5-AUTO-13 | tiêu chí cổng (chấm sống) | Công cụ và quy trình thu thập | Tính trung thực và minh bạch | phiếu trình Hội đồng Đạo đức khớp câu hỏi dùng để nhập liệu |
| DC-SAI-LECH | bộ đối chiếu | Sai lệch, hạn chế và kiểm soát | Tính khách quan | biện pháp khống chế sai lệch có phân tích SAP |
| DC-BIEN | bộ đối chiếu | Biến số và kết cục | Tính hợp lệ và tin cậy | biến đo đúng như đề cương đã duyệt |
| DC-MA-TRAN | bộ đối chiếu | Mục tiêu | Tính khoa học | mỗi yếu tố của mục tiêu có biến và phân tích |
| DC-PHAI-SINH | bộ đối chiếu | Biến số và kết cục | Tính tái lập | công thức phái sinh hợp lệ, đã duyệt đúng dấu |
| DC-SO-LIEU-TOAN-VAN | bộ đối chiếu | Tổng quan tài liệu và khung lý thuyết | Tính trung thực và minh bạch | con số dẫn có trong toàn văn nguồn |
| HDKH:1 | biên bản Hội đồng Khoa học còn hiệu lực | Đặt vấn đề | Tính khoa học | phán đoán của hội đồng — mục phiếu 1 |
| HDKH:1 | biên bản Hội đồng Khoa học còn hiệu lực | Tổng quan tài liệu và khung lý thuyết | Tính khoa học | phán đoán của hội đồng — mục phiếu 1 |
| HDKH:2 | biên bản Hội đồng Khoa học còn hiệu lực | Mục tiêu | Tính khoa học | phán đoán của hội đồng — mục phiếu 2 |
| HDKH:2 | biên bản Hội đồng Khoa học còn hiệu lực | Thiết kế và bối cảnh | Tính khoa học | phán đoán của hội đồng — mục phiếu 2 |
| HDKH:2 | biên bản Hội đồng Khoa học còn hiệu lực | Kế hoạch phân tích thống kê | Tính khoa học | phán đoán của hội đồng — mục phiếu 2 |
| HDKH:3 | biên bản Hội đồng Khoa học còn hiệu lực | Dự kiến kết quả và khung bảng trống | Tính khoa học | phán đoán của hội đồng — mục phiếu 3 |
| HDKH:4 | biên bản Hội đồng Khoa học còn hiệu lực | Tài liệu tham khảo Vancouver/NLM | Tính trung thực và minh bạch | phán đoán của hội đồng — mục phiếu 4 |

## 9. Kết quả đo ngày 22/11/2026

Hai đề tài thật đo ở `~/.ebm-worktrees/hdkh-du-lieu-20261122` (chỉ đọc); tám đề cương giả lập ở
`~/.ebm-worktrees/gia-lap-hop-20261122/<kịch bản>/repo`.

| Đề tài | 🟢 | 🔴 | ⚪ | — | Trục tổng (giá trị · phương pháp · khả thi · đạo đức · kiểm chứng) | Lỗi K20 |
|---|---|---|---|---|---|---|
| C1a (cắt ngang) | 45 | 3 | 96 | 0 | ⚪ · 🔴 · 🔴 · ⚪ · 🔴 | 3 |
| BTM (cắt ngang hồi cứu) | 41 | 1 | 102 | 0 | ⚪ · 🔴 · ⚪ · ⚪ · 🔴 | 1 |
| Bệnh chứng | 38 | 0 | 106 | 0 | ⚪ cả 5 | 0 |
| Cắt ngang mô tả | 38 | 0 | 106 | 0 | ⚪ cả 5 | 0 |
| Chẩn đoán | 39 | 3 | 102 | 0 | 🔴 · 🔴 · ⚪ · ⚪ · 🔴 | 0 |
| Định tính | 33 | 0 | 103 | 8 | ⚪ cả 5 | 0 |
| Dự báo | 32 | 6 | 106 | 0 | 🔴 · 🔴 · ⚪ · 🔴 · 🔴 | 0 |
| RCT | 36 | 8 | 100 | 0 | 🔴 · 🔴 · ⚪ · 🔴 · ⚪ | 0 |
| Thuần tập | 39 | 0 | 105 | 0 | ⚪ cả 5 | 0 |
| Tổng quan–gộp | 28 | 6 | 85 | 25 | ⚪ · 🔴 · ⚪ · ⚪ · 🔴 | 0 |

- Ô 🔴 của tám giả lập đều do mục chuẩn K17 còn chỉ cảnh báo (`CHUAN_CHO_BO_SINH`: STARD, TRIPOD+AI, SPIRIT, PRISMA-P)
  — mục chuẩn còn thiếu thật của bộ sinh; K20 không chặn lần hai vì K17 đã báo. Không ô đỏ nào của giả lập đến từ phép
  đo ngoài K1–K19.
- C1a: (1) TN-QC-04 — 9 rủi ro R1–R9 của sổ rủi ro máy đọc còn ô xác suất «[CẦN]»; (2) DC-PHAI-SINH — công thức
  PhieuHopLe đổi theo quyết định hội đồng 22/11 nên dòng duyệt thống kê viên hết hiệu lực; (3) NQ:dac_ta_phan_tich — đặc
  tả G6 có 70 «tham số không hỗ trợ». Thay thế cho (1) và gói ký cho (2): `scratchpad/hoi_dong_de_tai/
  hai-long-benh-nhan-C1a-BVQY175_tam_nguyen_tac.json` (chạy khô `ap_hoi_dong.py`: 9 thay thế áp được, 0 hỏng; thử trên
  bản sao: ô chuyển xanh). (3) đang do phiên khác sửa (G6_DAC_TA_SAP.json và run_stats_analysis.py).
- BTM: NQ:dac_ta_phan_tich (41 lỗi cùng loại, cùng nguyên nhân với C1a (3)).
- Sổ đọc: C1a 1.545 đơn vị (842 câu · 67 tiêu đề · 570 hàng bảng · 4 hình · 3 công thức · 59 tài liệu tham khảo); BTM
  1.087 đơn vị (498 câu · 56 tiêu đề · 466 hàng bảng · 5 hình · 0 công thức tách dòng riêng — công thức cỡ mẫu nằm trong
  câu · 62 tài liệu tham khảo). Cả hai chưa ở trạng thái trình (C1a: G10 chấm sống BLOCKED; BTM: chưa có G10) nên K21
  chỉ báo tỷ lệ phủ 0%.

## 10. Ô ⚪ còn lại và phép đo cần xây

Trên C1a có 96 ô ⚪: 85 ô chưa có phép đo nào, 11 ô có phép đo nhưng chưa đo được.

**11 ô có phép đo nhưng chưa đo được** (lý do kỹ thuật):
- 8 ô HDKH (Đặt vấn đề, Tổng quan, Mục tiêu, Thiết kế, SAP, Dự kiến kết quả × Khoa học; Tài liệu tham khảo × Trung
  thực): chưa có biên bản Hội đồng Khoa học máy (`BIEN_BAN_HDKH_*.json`) có SHA trùng bản đề cương hiện hành.
- Tổng quan × Trung thực (DC-SO-LIEU-TOAN-VAN): 0/26 tài liệu được dẫn có toàn văn trên máy ở thư mục đề tài; công cụ
  không đọc EndNote khi đo ma trận (phép đo tất định trên tệp đề tài).
- Biến số × Hợp lệ–tin cậy (DC-BIEN): một phát hiện «cần xem» của `doi_chieu_bien_de_cuong`.
- SAP × Khách quan (TN-KQ-01): chưa có dữ liệu và G4 chấm sống READY_FOR_SIGNATURE (SAP sửa đổi chờ ký) — chưa tới mốc so.
- SAP × KSCL (TN-QC-08): đề cương chưa nêu kiểm tra chéo kết quả phân tích.

**85 ô chưa có phép đo** (64 ô trong đó không có phép đo ở cả 10 đề cương). Nhóm theo nguyên tắc, kèm hướng xây:
- Đạo đức (16 ô: mọi phần trừ Đối tượng, Đạo đức): cần phép đo «nội dung đạo đức của phần này khớp hồ sơ G2 cùng phiên
  bản» — hồ sơ G2 chưa có cấu trúc máy đọc theo phần đề cương, nên chưa đối chiếu từng phần được.
- Hợp lệ–tin cậy (14 ô): chỉ Biến số, Công cụ, Cỡ mẫu, SAP có dữ kiện đo lường máy đọc; các phần văn xuôi (Tóm tắt, Đặt
  vấn đề, Tổng quan…) cần định nghĩa vận hành «hợp lệ» riêng cho văn bản — chưa có chuẩn máy kiểm.
- Tôn trọng đối tượng (15 ô): ngoài Đạo đức, Quản trị dữ liệu, Công cụ chưa có dữ kiện máy đọc gắn với phần.
- KSCL (12 ô), Tái lập (10 ô), Khách quan (8 ô), Khoa học (7 ô), Trung thực (3 ô: Câu hỏi, Biến số, Quản trị dữ liệu):
  hướng xây chung — đối chiếu phần đó với nguồn có định danh hoặc với cùng thông số ở hồ sơ khác (trung thực), định trước
  và không đổi giữa hồ sơ (khách quan), khai đủ tham số máy đọc (tái lập), luật kiểm và giới hạn chấp nhận (KSCL).
- Ô cần PHÁN ĐOÁN của người (ý nghĩa khoa học, tính hợp lý của lựa chọn phương pháp ở từng phần) đo bằng biên bản Hội
  đồng Khoa học còn hiệu lực: mở rộng `ANH_XA_HDKH` khi phiếu nhận xét có mục chấm theo phần.
