# PHẢN HỒI BÌNH DUYỆT ĐIỂM-THEO-ĐIỂM

**Đề tài:** Đánh giá sự hài lòng của bệnh nhân trong hoạt động khám chữa bệnh tại Khoa Khám bệnh C1a, Trung tâm Khám bệnh và Điều trị theo yêu cầu C1, Bệnh viện Quân y 175.

**Chủ nhiệm:** Nguyễn Hà Luân. **Hội đồng:** Hội đồng Y đức Bệnh viện Quân y 175.

**Nguồn:** `QUYET-DINH-BINH-DUYET_Hai-long-C1a.md` (quyết định biên tập ngày 31/07/2026, kết luận SỬA LỚN).

**Ngày sửa:** 02/08/2026. **Tài liệu đã sửa:** `De-cuong_Hai-long-C1a_BVQY175.md` (đề cương chi tiết) và `Bai-bao-giao-thuc_Hai-long-C1a_BVQY175.md` (bài báo giao thức).

> **Cần bác sĩ kiểm chứng.** Đây là bản ghi những gì đã sửa trong văn bản, không phải một tuyên bố rằng đề tài đã đủ điều kiện trình Hội đồng. Ba việc còn lại ở mục 3 phải do người thật làm.

---

## 1. TÓM TẮT

| Nhóm | Số mục | Đã xử lý trọn | Đã sửa nhưng còn chờ người thật | Chưa làm được |
|---|---|---|---|---|
| Ưu tiên 1 (trước khi trình Hội đồng) | 6 | 4 | 1 | 1 |
| Ưu tiên 2 (trước khi khóa công cụ) | 7 | 7 | 0 | 0 |
| Ưu tiên 3 (chỉ ở bài báo) | 4 | 4 | 0 | 0 |
| **Cộng** | **17** | **15** | **1** | **1** |

Mục còn chờ người thật là số cỡ mẫu Mục tiêu 2 (đã tính sẵn, cần thống kê viên ký). Mục chưa làm được là đối chiếu toàn văn Quyết định 56/QĐ-BYT, việc này cần bản văn bản gốc mà nhóm không có quyền truy cập.

---

## 2. ĐIỂM-THEO-ĐIỂM

### Ưu tiên 1

**1. Tính lại cỡ mẫu cho Mục tiêu 2 bằng công thức Whitehead.** ĐÃ TÍNH, CHỜ THỐNG KÊ VIÊN KÝ.

Đã áp dụng công thức Whitehead ở dạng tổng quát cho phơi nhiễm liên tục thay vì dạng hai nhóm:

n = 3(z₁₋α/₂ + z₁₋β)² / [(1 − Σpᵢ³) · β² · Var(X) · (1 − R²)]

Kết quả: ở n = 1000, α = 0,05 hai phía, power 80%, R² = 0,20, nghiên cứu phát hiện được **tỷ số chênh 1,07 đến 1,15 cho mỗi 15 phút chờ thêm** (tương đương khoảng 1,43 mỗi giờ khi độ lệch chuẩn thời gian chờ là 30 phút). Kết quả in thành Bảng 4.3 (OR nhỏ nhất phát hiện được) và Bảng 4.4 (cỡ mẫu cần theo từng mức OR) ở mục 4.4.1 đề cương.

**Câu trả lời cho câu hỏi mà phản biện đặt ra ("nếu n = 1000 không đủ, nói thẳng"):** n = 1000 **dư sức** cho Mục tiêu 2 dưới mọi kịch bản đã xét. Ràng buộc chặt hơn nằm ở Mục tiêu 1, không phải Mục tiêu 2. Đây là kết quả ngược với lo ngại ban đầu.

Ba giả định được nêu rõ ngay tại chỗ: phân bố năm mức là giả định lấy từ dải y văn chứ không từ nghiên cứu thử của khoa (kết quả rất ít nhạy với lựa chọn này, 1 − Σpᵢ³ chỉ dao động 0,844–0,898); độ lệch chuẩn thời gian chờ chưa biết và là tham số ảnh hưởng mạnh nhất, phải lấy từ HIS ở buổi chạy thử; và phép tính chưa tính hiệu ứng thiết kế do gom cụm.

**Việc còn lại:** thống kê viên chạy lại bằng `Hmisc::posamsize`/`popower` hoặc Stata và ký. Đề cương ghi rõ con số đưa vào hồ sơ Hội đồng là con số thống kê viên ký, phép tính trong đề cương là bản nháp để rút ngắn công việc đó.

**Về lập luận ±3,1%:** đã sửa. Con số này đúng nhưng **có điều kiện** là lấy mẫu ngẫu nhiên đơn giản và quan sát độc lập, mà điều kiện thứ hai không đúng ở đây. Đề cương nay in bảng độ chính xác thật theo hiệu ứng thiết kế: **±4% đến ±6%** tùy số bàn khám và ICC, và nêu rằng mức thường quy ±5% chỉ đạt được khi ICC thấp.

**Về trích dẫn Bender & Grouven:** đã sửa từ vòng trước. Tài liệu này nay chỉ được dẫn cho đúng nội dung của nó (mô hình proportional odds riêng phần khi vi phạm giả định), không còn dẫn làm căn cứ cỡ mẫu.

---

**2. Thêm biến chùm và khai báo xử lý gom cụm.** ĐÃ XỬ LÝ TRỌN.

Thêm biến `ma_ban_kham` (mã bàn khám giả danh dạng BK01, BK02… do Phòng CNTT/QLCL cấp) vào bảng biến số mục 4.6.2, đánh dấu **BẮT BUỘC thu ngay từ phiếu đầu tiên**, kèm ghi chú giải thích tại chỗ vì sao không sửa được sau khi thu thập.

Kế hoạch phân tích (mục 4.10, Phụ lục A.3): mô hình chính dùng **sai số chuẩn robust theo chùm**; phân tích nhạy cảm dùng **mô hình thứ tự có hệ số chặn ngẫu nhiên**; **báo cáo ICC** cho G1 và từng lĩnh vực A–F. Quy tắc ấn định trước: nếu số bàn khám thực tế dưới 15 thì mô hình hệ số chặn ngẫu nhiên thành phân tích chính.

Cam kết bảo vệ nhân viên (mục 4.6.2 và 4.11.1): mã giả danh, nhóm nghiên cứu không giữ bảng ghép; **cấm dùng dữ liệu để xếp hạng, thi đua hay kỷ luật cá nhân**; **không công bố số liệu cho bàn khám có dưới 10 phiếu**; không xếp thứ tự bàn khám trong bất kỳ bảng nào. Nhân viên khoa được thông báo trước ngày thu thập đầu tiên.

---

**3. Bổ sung nhóm mục còn thiếu vào phiếu.** ĐÃ XỬ LÝ TRỌN.

Thêm **12 mục**, phiếu từ 46 lên 58 mục. Toàn văn ở Phụ lục C.6; khai báo biến ở mục 4.6.2.

| Nhóm | Số mục | Mã biến |
|---|---|---|
| Kỳ vọng | 3 | `kyvong_thoigiancho`, `xacnhan_kyvong`, `lydo_chon_theoyeucau` |
| Đặc thù khám theo yêu cầu | 5 | `co_yeucau_bacsi`, `duoc_dung_bacsi`, `kenh_datlich`, `co_goikham`, `rieng_tu` |
| Tự đánh giá sức khỏe | 1 | `suckhoe_tudanhgia` |
| Ý định quay lại và giới thiệu | 2 | `G2`, `G3` |
| Rào cản tài chính trong lượt khám | 1 | `hoan_vi_chiphi` |

Hai biến được đưa thẳng vào **tập hiệu chỉnh bắt buộc** của mô hình chính: `suckhoe_tudanhgia` (biến gây nhiễu) và `duoc_dung_bacsi` (ở khối theo yêu cầu có thể là yếu tố giải thích mạnh không kém thời gian chờ). Hai biến kỳ vọng là **biến trung gian**, cố ý không hiệu chỉnh trong mô hình chính để tránh over-adjustment.

Xử lý gánh nặng trả lời: tiêu chí F4 của buổi chạy thử đặt trần trung vị 20 phút; nếu vượt, thứ tự cắt bớt mục đã định trước (bỏ `kenh_datlich` và `co_goikham` trước, giữ đến cùng ba mục kỳ vọng, `suckhoe_tudanhgia` và `duoc_dung_bacsi`).

Codebook `.sav` cần bổ sung 12 biến (63 → 75) **trước khi in phiếu chính thức**.

---

**4. Điền bốn con số đang để trống.** ĐÃ XỬ LÝ TRỌN.

| Đại lượng | Con số nay đã có | Nơi ghi |
|---|---|---|
| Ngưỡng nhị phân hóa "hài lòng" | G1 ≥ 4/5, tương đương top-two-box của chính mục G1 | 4.5.2, A.6 (đã có từ trước, xác nhận lại) |
| Ràng buộc cỡ mẫu Mục tiêu 2 | Bảng 4.3 và 4.4, OR phát hiện được 1,07–1,15 mỗi 15 phút | 4.4.1 |
| Tiêu chí "không khả thi" của buổi chạy thử | 5 tiêu chí F1–F5 có ngưỡng số, trên tối thiểu 40 lượt mời qua 4 tầng | 4.4.2 |
| Ngưỡng loại phiếu khuyết dữ liệu | 3 điều kiện: thiếu G1 · bỏ trống ≥ 7/30 mục Likert · bỏ trống trọn một lĩnh vực | 4.3.2, A.6 |

Năm tiêu chí khả thi: F1 xác định đúng người theo bước nhảy ≥ 80% lượt mời; F2 đồng ý tham gia ≥ 60%; F3 ghép được mốc HIS ≥ 90% phiếu; F4 trung vị thời gian điền ≤ 20 phút; F5 không quá 2 mục bị ≥ 20% người trả lời hiểu sai. Vi phạm F4 hoặc F5 xử lý bằng sửa công cụ rồi chạy thử lại; vi phạm F1, F2 hoặc F3 kích hoạt quy trình dừng.

---

**5. Khai và quản lý xung đột lợi ích cơ cấu.** ĐÃ XỬ LÝ TRỌN.

Thêm hẳn mục **4.11.1** vào đề cương và một đoạn tương ứng ở mục 2.9 bài báo. Khai thẳng: chủ nhiệm công tác tại chính khoa được đánh giá; đây là xung đột **không thể loại bỏ** vì hiểu biết nội bộ là điều kiện để thiết kế được nghiên cứu, chỉ có thể quản lý công khai; chiều thiên lệch cần đề phòng là kết quả hài lòng cao có lợi cho khoa và cho chính chủ nhiệm.

Bảy biện pháp khóa trước khi thu thập, trả lời đúng bốn câu hỏi phản biện đặt ra:

| Câu hỏi của phản biện | Trả lời trong đề cương |
|---|---|
| Ai mở hòm phiếu? | Tổ **hai người**: một điều tra viên ngoài khoa + một đại diện Phòng KHTH/QLCL, lập biên bản; chủ nhiệm không mở một mình |
| Ai phân tích? | Nhà thống kê, chạy theo SAP đã khóa trước khi mở dữ liệu |
| Điều tra viên thuộc đơn vị nào? | **Không thuộc Khoa C1a** (đã có từ trước, nay ghi rõ trong bảng biện pháp) |
| Ai mã hóa ý kiến mở? | **Hai người ngoài khoa** mã hóa độc lập, người thứ ba ngoài khoa phân xử; chủ nhiệm không tham gia. Đây là khâu chủ quan nhất của nghiên cứu |

Thêm điều khoản cấm dùng dữ liệu cho đánh giá hiệu suất cá nhân nhân viên, kèm quy tắc cỡ ô tối thiểu 10 phiếu. Bảng RACI mục 6.1 bổ sung bốn vai trò mới tương ứng.

Điều **không** khắc phục được, đã nêu rõ ở phần hạn chế: chủ nhiệm vẫn là người diễn giải kết quả và viết bàn luận, nên thiên lệch diễn giải không bị loại trừ hoàn toàn; cách kiểm soát còn lại là tính tiền định của kế hoạch đã khóa, thu hẹp chứ không đóng hẳn khoảng trống đó.

---

**6. Đối chiếu toàn văn Quyết định 56/QĐ-BYT và quyết định có nhúng Mẫu số 2 hay không.** CHƯA LÀM ĐƯỢC, CẦN CHỦ NHIỆM.

Việc này cần bản toàn văn của Quyết định 56/QĐ-BYT ngày 08/01/2024, tài liệu mà nhóm soạn đề cương không có quyền truy cập để đối chiếu từng mục. Đề cương giữ nguyên cách phát biểu thận trọng hiện có ("tương thích về khái niệm", không khẳng định trùng khớp từng mục) và đã bổ sung [V1], [V2] vào danh mục tài liệu bài báo.

Quyết định có nhúng nguyên văn mô-đun Mẫu số 2 vào phiếu hay không là **thay đổi phạm vi công cụ**, thuộc thẩm quyền chủ nhiệm và Hội đồng. Đề cương nay nêu rõ đánh đổi ở phần hạn chế bài báo: công cụ tự xây khiến số liệu không đối chiếu trực tiếp được với khảo sát thường quy của khoa và với mốc chuẩn quốc gia.

---

### Ưu tiên 2 — đã xử lý trọn cả bảy mục

**7. Chia đôi mẫu EFA/CFA.** Chuyển từ "ngoài phạm vi, gợi ý cho tương lai" thành **kế hoạch bắt buộc** (mục 4.5.3). Chia ngẫu nhiên 50/50 theo seed ghi trong SAP, phân tầng theo khung giờ và bàn khám; nửa A chạy EFA polychoric, nửa B chạy CFA với ước lượng WLSMV. Ngưỡng ấn định trước: CFI ≥ 0,95 · TLI ≥ 0,95 · RMSEA ≤ 0,06 · SRMR ≤ 0,08 là phù hợp tốt; CFI/TLI ≥ 0,90 và RMSEA ≤ 0,08 là chấp nhận được.

Bốn phương án định trước khi **không đạt** (phần bản trước bỏ trống): vẫn báo cáo đúng kết quả; ưu tiên trình bày ở cấp từng mục thay vì điểm gộp lĩnh vực; trình bày cấu trúc EFA tìm được như phát hiện thăm dò; và **không** chỉnh mô hình theo chỉ số hiệu chỉnh rồi báo cáo như thể đã định trước.

Lý do phải làm: bản trước sẽ **báo cáo** điểm theo sáu lĩnh vực suốt phần kết quả nhưng **không bao giờ kiểm** sáu lĩnh vực ấy có thật trong dữ liệu hay không.

**8. Câu hỏi về tính bao phủ cho hội đồng chuyên gia.** Phiếu chấm bổ sung hai câu bắt buộc, trả lời tự do, không chấm điểm: khía cạnh nào quan trọng với người bệnh mà bộ câu hỏi chưa hỏi; và nếu chỉ được thêm 3 câu thì thêm câu nào. Chủ nhiệm phải trả lời từng đề xuất, nhận hoặc từ chối kèm lý do. **S-CVI không được coi là đạt nếu thiếu phần này.** Phỏng vấn nhận thức cũng có phần khai thác mở tương tự ở cuối mỗi buổi.

Lý do: chỉ số I-CVI về nguyên tắc **không thể phát hiện mục còn thiếu** vì nó chỉ chấm những mục đã có. Đây đúng là lỗ hổng đã để lọt 12 mục ở vòng bình duyệt này.

**9. Hội đồng chuyên gia ≥ 6, có đại diện người bệnh.** Sửa từ "5–7 chuyên gia" thành **6 đến 10 thành viên**, trong đó **ít nhất 2 đại diện người bệnh** và **không quá 2 người thuộc Khoa C1a**.

Phát hiện thêm trong lúc sửa: cấu hình 5 người của bản trước sẽ khiến đề cương **dùng sai ngưỡng**. Theo tiêu chí Lynn mà Polit & Beck dẫn lại, ngưỡng I-CVI ≥ 0,78 chỉ áp dụng từ 6 chuyên gia trở lên; với 5 người trở xuống, yêu cầu là toàn bộ chuyên gia đồng thuận (I-CVI = 1,00).

**10. Quy tắc gộp mức định trước và ước lượng có phạt.** Thêm vào mục 4.10 và A.3. Mức có dưới 20 quan sát (2% của n = 1000) gộp với mức liền kề về phía trung tâm thang đo, thứ tự cố định 1→2→3, mức 5 không bao giờ gộp, không gộp xuống dưới 3 mức. Bảng phân bố năm mức gốc vẫn in đầy đủ ở Bảng 5.2; việc gộp chỉ áp dụng cho mô hình. Ước lượng có phạt (Firth) chỉ dùng khi có separation **và** còn đủ thông tin khoa học.

**11. Bỏ sàng lọc biến bằng p đơn biến.** Đã bỏ ngưỡng p < 0,20 khỏi cả mục 4.10, Phụ lục A.3, A.6 và mục 2.8 bài báo. Danh mục biến của cả mô hình chính lẫn mô hình thăm dò nay ấn định trước theo DAG. Bảng đơn biến (Bảng 5.3) giữ lại nhưng chỉ với vai trò **mô tả**, không phải bước lọc.

**12. Định lượng nhóm bỏ dở lượt khám.** Sơ đồ luồng STROBE nay có **nhánh riêng ở bước 2**, ngay sau bước lấy số: số lượt rời viện trước khi vào buồng khám, lấy từ HIS, kèm **phân bố thời gian chờ của nhóm này so với nhóm hoàn tất**. Bảng 5.6 thêm hai dòng tương ứng. Mục 4.8 thêm hẳn một nhóm sai lệch mới với tên gọi đúng bản chất là **chọn mẫu phụ thuộc phơi nhiễm**.

Đây là chiều sai lệch nguy hiểm nhất của đề tài: người chờ lâu nhất dễ bỏ về nhất và cũng dễ không hài lòng nhất, nên họ bị loại khỏi mẫu bằng chính cơ chế mà nghiên cứu muốn đo. Không lấy được ý kiến của họ, nhưng định lượng được quy mô và hướng; phần Bàn luận bắt buộc nêu rằng mối liên quan chờ–hài lòng nhiều khả năng bị **ước lượng thấp hơn thực tế**.

**13. Sổ ghi người từ chối.** Mục 4.4.2 nay quy định bốn trường quan sát được mà không cần hỏi: ngày và khung giờ; nhóm tuổi ước lượng; giới; lý do **nếu người bệnh tự nêu**, và điều tra viên **không được truy hỏi lý do**. Tuyệt đối không ghi thông tin định danh. Bảng 5.6 thêm dòng so sánh người từ chối với người tham gia trên bốn trường này.

---

### Ưu tiên 3 — đã xử lý trọn cả bốn mục, chỉ sửa ở bài báo

**14. Đường ghép dữ liệu HIS và thuật ngữ "giả danh có kiểm soát".** Mục 2.9 bài báo nay mô tả đầy đủ cơ chế bên thứ ba (bộ phận CNTT giữ bảng ghép tạm thời, chỉ bàn giao biến phái sinh đã khử định danh, hủy trong 30 ngày có nhật ký) và dùng **đúng thuật ngữ giả danh** cho bước này, không mở rộng chữ khuyết danh cho toàn bộ quy trình. Đây là mâu thuẫn mà phản biện đối kháng nêu ở vấn đề C1; đề cương gốc vốn đã đúng, chỉ bài báo thiếu.

**15. Bổ sung [V1] và [V2] vào danh mục tài liệu.** Đã thêm, tách thành nhóm "Văn bản pháp quy Việt Nam" với ghi chú không có PMID/DOI và chủ nhiệm cần đối chiếu bản còn hiệu lực trước khi nộp. Hai chỗ khẳng định về khung phiếu Bộ Y tế trong bài báo nay có trích dẫn.

**16. Chiến lược tìm y văn và hạ tuyên bố tuyệt đối.** Thêm đoạn mô tả chiến lược tìm ở phần Đặt vấn đề bài báo và một bảng thông số đầy đủ ở mục 3.5 đề cương: nguồn quốc tế, **nguồn trong nước bắt buộc** (tạp chí trong nước, thư viện luận văn các trường y, kỷ yếu hội nghị bệnh viện), từ khóa tiếng Việt và tiếng Anh, mốc thời gian từ 2015.

Tuyên bố trong Tóm tắt và Đặt vấn đề hạ từ "chưa có nghiên cứu công bố nào" xuống **"chúng tôi chưa tìm thấy"**, và nêu rõ đây là giới hạn của phạm vi tra cứu chứ không phải khẳng định rằng nghiên cứu như vậy không tồn tại. Kiểu đóng góp đổi từ "lấp khoảng trống" sang **"nhân rộng có kiểm chứng"**, kèm ba đóng góp cụ thể không phụ thuộc vào việc có hay không nghiên cứu tương tự ở nơi khác.

**17. Giới hạn bối cảnh của hai nguồn.** Phần Hạn chế bài báo nay nêu rõ nghiên cứu về nhà thuốc BHYT ngoại trú[4] thực hiện trong bối cảnh đại dịch COVID-19, và nghiên cứu về phòng khám ngoại trú HIV[5] có quần thể cùng mô hình chăm sóc rất khác khối khám theo yêu cầu; hai nguồn này được trích để minh họa mẫu hình lặp lại về thời gian chờ và thủ tục, không để suy ra mức hài lòng kỳ vọng tại địa điểm nghiên cứu.

---

## 3. BA VIỆC PHẢI DO NGƯỜI THẬT LÀM, KHÔNG THỂ SỬA BẰNG VĂN BẢN

1. **Thống kê viên chạy lại và ký cỡ mẫu Mục tiêu 2.** Phép tính đã có sẵn trong đề cương với đầy đủ công thức và tham số; việc còn lại là chạy bằng `Hmisc::posamsize`/`popower` hoặc Stata, xác nhận ba giả định, và ký. Sau đó điền vào `study_meta.json → gate_params.G3`.

2. **Chủ nhiệm đối chiếu toàn văn Quyết định 56/QĐ-BYT** và quyết định có nhúng mô-đun Mẫu số 2 vào phiếu hay không. Đây là quyết định về phạm vi công cụ, ảnh hưởng tới khả năng so sánh của toàn bộ kết quả.

3. **Chủ nhiệm cập nhật codebook `.sav`** thêm 12 biến mới (63 → 75) và in lại phiếu, **trước** khi hội đồng chuyên gia chấm. Nếu hội đồng thông qua cả đề xuất tách C6/C9 thì thành 77 biến và 32 mục Likert.

---

## 4. MỘT QUYẾT ĐỊNH CÒN TREO, THUỘC THẨM QUYỀN CHỦ NHIỆM VÀ HỘI ĐỒNG

Hai phản biện độc lập cùng đề xuất **lấy song song một mẫu ở khối khám thường** trong cùng bệnh viện, cùng thời gian, cùng công cụ. Lập luận: đề tài tự giới thiệu bằng một mệnh đề so sánh (khối theo yêu cầu hài lòng thấp hơn) nhưng thiết kế không so sánh được, nên để lại đúng câu hỏi ấy không trả lời.

Đây là **thay đổi phạm vi**, không phải một lỗi cần sửa, và thuộc thẩm quyền chủ nhiệm cùng Hội đồng. Đề tài hiện đã xử lý một phần vấn đề bằng cách khác: đo kỳ vọng trực tiếp (12 mục bổ sung) cho phép phân biệt "dịch vụ kém" với "kỳ vọng cao" ngay trong mẫu hiện tại, mà không cần nhóm so sánh. Nếu không mở rộng, phần Đặt vấn đề nên đọc nghịch lý như bối cảnh chứ không như móc treo lý luận; câu chữ hiện tại đã được điều chỉnh theo hướng này.

---

## 5. KIỂM TRA KỸ THUẬT SAU KHI SỬA

| Kiểm | Kết quả |
|---|---|
| `verify_exports_integrity.py` trên cả hai tài liệu | Không lỗi liêm chính nội dung |
| Placeholder bảng dự kiến kết quả | 278 → 311 ô, **không mất ô nào** (số tăng do các dòng mới ở Bảng 5.6 và sơ đồ luồng) |
| Gạch ngang dài dùng làm dấu ngắt câu (mẫu văn phong AI) | Đề cương 32 → **0**; bài báo 0 |
| Chốt pre-commit của repo | Đạt, cả hai commit |

Độ dài bài báo giao thức nay khoảng 8.400 từ, vượt giới hạn thường gặp của tạp chí (3.000–5.000 từ cho protocol paper). Khi chọn được tạp chí đích, cần rút gọn theo yêu cầu cụ thể; phần chi tiết đã có sẵn ở đề cương nên rút gọn bài báo không làm mất thông tin.

---

*Cần bác sĩ kiểm chứng. Tài liệu này ghi lại thay đổi văn bản, không thay thẩm định của Hội đồng Y đức, của thống kê viên hay của phản biện tạp chí.*
