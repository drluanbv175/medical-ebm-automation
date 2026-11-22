# Biên bản hiệu chuẩn Hội đồng Khoa học máy — QC-HDKH-4.0 (chế độ kết hợp)

- Ngày đo: 22/11/2026 · Quy chế: QC-HDKH-4.0 · SHA-256 quy chế: `2d9b45215b23f2a9154120c694d1ded088cdfb724e379a7cfb71705032d1f4b3`
- Chế độ: kết hợp. API (claude-opus-5-5, Batch) họp thẩm định độc lập một lần cho mỗi bản. Agent Claude Code thẩm định
  từng nhận xét. Agent `trong-tai-tranh-bien` đo báo nhầm: nhận bản sao tài liệu tên trung tính, phiếu không đặt cạnh
  đáp án.
- Loại tài liệu đã hiệu chuẩn: **chỉ đề cương** (`de_cuong`). SAP, bản thảo bài báo và báo cáo tổng hợp kết quả
  (nghiệm thu) **CHƯA hiệu chuẩn** dưới quy chế này. Kết luận của hội đồng máy trên ba loại đó chưa có hiệu lực.
- Ngưỡng của quy chế:
  - độ nhạy ≥ 0,8333 trên ≥ 5 lỗi cài;
  - phải bắt được lỗi đặc thù thiết kế;
  - trọng tài phán đúng ≥ 90% đối chứng;
  - độ chính xác nhận xét ≥ 0,80;
  - tỷ lệ «không rõ» ≤ 50%.

  Ngưỡng độ chính xác là ngưỡng vận hành của hệ, không phải chuẩn quốc tế.

## 1. Hai đề tài thật (bản sao cài lỗi của đề cương)

| Đề tài | Độ nhạy | Lỗi đặc thù | Độ chính xác nhận xét | Hiệu lực |
|---|---|---|---|---|
| btm-dtd2-ngoai-tru-BVQY175 (cắt ngang) | 7/7 | bắt được | 1,000 | có |
| hai-long-benh-nhan-C1a-BVQY175 (cắt ngang, chọn mẫu cụm) | 7/7 | bắt được | 0,923 | có |

## 2. Tám thiết kế (đề tài giả lập ZZCANARY, hộp cát đủ hồ sơ cổng)

| Thiết kế | Đề tài giả lập | Độ nhạy | Lỗi đặc thù | Nhận xét được phán (đúng/sai/không rõ) | Độ chính xác (KTC 95% Wilson) | Đối chứng trọng tài | Hiệu lực |
|---|---|---|---|---|---|---|---|
| RCT | ZZCANARY-RCT-NHI-PHAN | 7/7 | bắt được | 32 / 0 / 0 | 1,000 (0,893–1,000) | 11/11 | có |
| Thuần tập | ZZCANARY-THUAN-TAP | 7/7 | bắt được | 28 / 0 / 1 | 1,000 (0,879–1,000) | 11/11 | có |
| Bệnh–chứng | ZZCANARY-BENH-CHUNG | 7/7 | bắt được | 33 / 0 / 0 | 1,000 (0,896–1,000) | 11/11 | có |
| Cắt ngang | ZZCANARY-CAT-NGANG-MO-TA | 7/7 | bắt được | 28 / 1 / 1 | 0,966 (0,828–0,994) | 11/11 | có |
| Chẩn đoán | ZZCANARY-CHAN-DOAN | 7/7 | bắt được | 33 / 0 / 0 | 1,000 (0,896–1,000) | 11/11 | có |
| Dự báo | ZZCANARY-DU-BAO | 7/7 | bắt được | 32 / 0 / 0 | 1,000 (0,893–1,000) | 11/11 | có |
| Tổng quan gộp | ZZCANARY-TONG-QUAN-GOP | 6/6 | bắt được | 21 / 0 / 4 | 1,000 (0,845–1,000) | 10/10 | có |
| Định tính | ZZCANARY-DINH-TINH | 7/7 | bắt được | 30 / 0 / 0 | 1,000 (0,886–1,000) | 11/11 | có |

Gộp cả 8 thiết kế: 237 nhận xét đúng, 1 sai. Độ chính xác 0,996 (KTC 95% Wilson 0,977–0,999). Tỷ lệ «không rõ» cao
nhất ở tổng quan gộp (4/25 = 16%), dưới trần 50%. Bản cài lỗi của tổng quan gộp chỉ có 6 lỗi, vì lỗi cài về quyền rút
lui của người tham gia không áp được: tổng quan gộp không tuyển người tham gia.

## 3. Giới hạn

- Trọng tài đo báo nhầm là agent chạy cùng model với hội đồng. Tính độc lập dựa vào ngữ cảnh mới và làm mù (không
  biết ai nêu nhận xét, không thấy đáp án), không dựa vào khác model. Đối chứng dương và âm đạt 11/11 (10/10) ở mọi
  thiết kế, nên trọng tài phân biệt được nhận xét đúng với nhận xét do máy dựng sai.
- Lỗi cài là lỗi do máy dựng theo mẫu. Hội đồng bắt được chúng chưa chứng minh nó bắt được mọi lỗi tinh vi của tài liệu
  thật.
- Mỗi đề tài giả lập chỉ có một bản cài lỗi. Kết quả là một lần đo cho mỗi thiết kế, không phải ước lượng lặp lại.
- Mọi hiệu chuẩn hết hiệu lực khi quy chế đổi (SHA khác).
- **Lỗi làm mù phát hiện sau khi đo.** Ở mọi lượt hiệu chuẩn trong biên bản này (hai đề tài thật và 8 thiết kế), khối
  tài liệu gửi hội đồng API mang tên tệp «BAN_CAI_LOI_<mã>_de_cuong.md». Hội đồng vì vậy có thể biết đang đọc bản cài
  lỗi. Trả lời của hội đồng ở cả 8 lượt thiết kế không nhắc tới tên này (0 lần), nhưng không loại trừ được việc độ
  nhạy bị nâng lên. Đã vá trong mã cùng ngày (`ten_cho_hoi_dong`, tên trung tính `TAI_LIEU_<sha8>`); SHA quy chế không
  đổi. Không đo lại, vì tín dụng API sắp hết. Độ nhạy ở bảng trên vì vậy là **cận trên**.

## 4. Chi phí thật (sổ `~/.ebm-api-claude-chi-phi.json`, theo id batch)

- Hiệu chuẩn hai đề tài thật, chế độ kết hợp: 2,16 USD.
- Họp thẩm định vòng 1 trên hai đề cương thật (vòng kín): 2,87 USD. Các vòng thẩm tra sau do agent làm, không gọi API.
- Hiệu chuẩn 8 thiết kế: 9,67 USD, gồm hội đồng 8 × 0,87–1,08 = 7,59 USD và chủ tịch 8 × 0,23–0,29 = 2,08 USD. Chi
  phí do khoảng 80 nghìn token đầu ra mỗi phiên họp quyết định, không phụ thuộc độ dài tài liệu.
- Cả ngày 22/11/2026: 89,54 USD trong 169 lượt, toàn bộ từ `tools/hoi_dong_khoa_hoc.py`; ngày 21/11 là 2,09 USD. Phần
  lớn tốn vì quy chế đổi 6 lần trong ngày (1.0 → 4.0), mỗi lần đổi phải họp lại.

## 5. Kết quả vòng kín trên hai đề cương thật

- btm-dtd2-ngoai-tru-BVQY175: thông qua phần thuộc thẩm quyền nhóm soạn thảo ở vòng 4; chốt cuối `tham-dinh-dau-ra`
  ĐẠT. Yêu cầu còn lại N2_01 (quy tắc xác nhận bệnh thận mạn, vùng SAP đã chốt) đã được chủ nhiệm duyệt nguyên văn
  bốn đoạn thay thế; đã áp vào đề cương (dòng 359, 398, 399) và SAP (dòng 61); chốt cuối kiểm lại bốn dòng: ĐẠT.
- hai-long-benh-nhan-C1a-BVQY175: thông qua phần thuộc thẩm quyền nhóm soạn thảo ở vòng 4; chốt cuối ĐẠT. Còn 14
  dữ kiện/quyết định của chủ nhiệm và thống kê viên, liệt kê trong biên bản vòng 4.

## 6. SAP, bản thảo và báo cáo nghiệm thu — chốt bằng công cụ tất định, không họp

Bác sĩ chủ nhiệm (22/11/2026): không dùng API nữa; không lập thêm kế hoạch họp. Ba loại tài liệu này **không** được
hội đồng máy hiệu chuẩn. Chất lượng của chúng dựa vào các công cụ tất định đã có của hệ:

- SAP: cổng G4 (`g4_quality_gate.py`) cùng chốt nhất quán xuyên cổng (`nhat_quan_xuyen_cong.py`).
- Bản thảo: cổng G7 và G8.
- Cả hai được chạy đầu–cuối trong 24 kịch bản giả lập của CI (`gia-lap-16.yml`, đủ 8 thiết kế): mỗi kịch bản
  phải khoá được gói G10 với 0 ô lỗi máy (`tools/kiem_gia_lap_16.py`). Cả 24 đều xanh trên PR #416.
- Báo cáo tổng hợp kết quả: bộ sinh `tools/bao_cao_tong_hop.py`. Báo cáo của 8 thiết kế giả lập đều đạt kiểm cấu trúc
  theo hướng dẫn chung mục III, không thiếu tài liệu tham khảo (đo 22/11/2026, 0 API).
- Vòng kín của hội đồng máy chỉ áp cho đề cương.

Hội đồng MÁY — TƯ VẤN: không thay Hội đồng Khoa học hay Hội đồng Đạo đức thật. Cần bác sĩ kiểm chứng.
