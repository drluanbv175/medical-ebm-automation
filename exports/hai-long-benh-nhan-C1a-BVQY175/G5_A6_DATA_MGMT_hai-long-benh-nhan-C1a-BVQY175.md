# A6 — KẾ HOẠCH QUẢN LÝ DỮ LIỆU (DRAFT)
**Đề tài:** Sự hài lòng của bệnh nhân trong hoạt động khám chữa bệnh tại Khoa Khám bệnh theo yêu cầu, bệnh viện quân y tuyến cuối  
**Mã:** hai-long-benh-nhan-C1a-BVQY175 | **Ngày:** 2026-10-24 | **Thiết kế:** cross_sectional | **N dự kiến:** 1000 (cỡ mẫu kế hoạch, G3 confirmed_n; tối thiểu theo thống kê 808)  
**Trạng thái:** DRAFT — CHỜ BÁC SĨ ĐIỀN CÁC [CẦN...] VÀ XÁC NHẬN

> **BẢO MẬT:** KHÔNG đưa PII vào pipeline. Chỉ xử lý bản đã khử định danh trong môi trường cục bộ được đơn vị cho phép; dữ liệu không được gửi tới mô hình AI.
> Tham chiếu: ICH E6(R3) Data Governance; FDA Electronic Records 2024; CDISC CDASH; FAIR Principles (PMID: 26978244; DOI: 10.1038/sdata.2016.18).

> ℹ️ Chuyên khoa nhận diện từ chủ đề: **BỘ BIẾN RIÊNG của đề tài (_bo-bien-rieng.csv — không dùng bundle)** — CRF dưới đây đã chọn field lâm sàng/thuốc/kết cục phù hợp chuyên khoa này. Vẫn cần bác sĩ xác nhận từng biến khớp đúng với PICO/SAP thực tế, đặc biệt khi đề tài có yếu tố khác biệt.

---

## PHẦN 1 — CẤU TRÚC CRF (Case Report Form)

Thiết kế: **cross_sectional** | Chuyên khoa: **BỘ BIẾN RIÊNG của đề tài (_bo-bien-rieng.csv — không dùng bundle)** | Tổng biến CRF: **71 dòng** | N dự kiến: **1000 (cỡ mẫu kế hoạch, G3 confirmed_n; tối thiểu theo thống kê 808)**

### Nhóm: phieu_khao_sat (64 biến)

| Biến | Loại | Nhãn | Bắt buộc | Phạm vi |
|------|------|------|----------|---------|
| `record_id` | text | Mã số phiếu (mã nghiên cứu) | ✓ | — |
| `mode_tra_loi` | radio | Câu 1. Cách hoàn thành phiếu | ✓ | — |
| `tuoi` | text | Câu 2. Tuổi (năm) | ✓ | 18–120 |
| `gioitinh` | radio | Câu 3. Giới tính | ✓ | — |
| `trinhdohocvan` | dropdown | Câu 4. Trình độ học vấn |  | — |
| `nghenghiep` | dropdown | Câu 5. Nghề nghiệp |  | — |
| `nghenghiepkhac` | text | Câu 5. Nghề nghiệp — ghi rõ nếu chọn Khác |  | — |
| `tinhtranghonnhan` | radio | Câu 6. Tình trạng hôn nhân |  | — |
| `noicutru` | radio | Câu 7. Nơi cư trú | ✓ | — |
| `khoangcachnhabv` | radio | Câu 20. Khoảng cách nhà–viện |  | — |
| `thunhaphogd` | dropdown | Câu 8. Thu nhập hộ gia đình/tháng |  | — |
| `cobhyt` | radio | Câu 9. Có thẻ BHYT còn hiệu lực | ✓ | — |
| `lydokham` | dropdown | Câu 10. Lý do khám lần này | ✓ | — |
| `lydokhamkhac` | text | Câu 10. Lý do khám — ghi rõ nếu chọn Khác |  | — |
| `solankham12thang` | radio | Câu 19. Số lần khám tại khoa trong 12 tháng qua |  | — |
| `phuongtiendichuyen` | dropdown | Câu 21. Phương tiện di chuyển đến viện |  | — |
| `phuongtiendichuyenkhac` | text | Câu 21. Phương tiện di chuyển — ghi rõ nếu chọn Kh |  | — |
| `nguonthongtinbv` | dropdown | Câu 22. Nguồn thông tin biết đến viện |  | — |
| `nguonthongtinbvkhac` | text | Câu 22. Nguồn thông tin biết đến viện — ghi rõ nếu |  | — |
| `kyvong_thoigiancho` | text | Câu 11. Trước khi đến khám, Ông/Bà nghĩ mình sẽ ph |  | 0–600 |
| `xacnhan_kyvong` | radio | Câu 12. So với mong đợi trước khi đến, dịch vụ hôm |  | — |
| `lydo_chon_theoyeucau` | checkbox | Câu 13. Lý do chính chọn khám theo yêu cầu (chọn t |  | — |
| `lydo_chon_khac` | text | Câu 13. Lý do chọn khám theo yêu cầu — ghi rõ nếu  |  | — |
| `co_yeucau_bacsi` | radio | Câu 14. Có yêu cầu khám với một bác sĩ cụ thể khôn |  | — |
| `duoc_dung_bacsi` | radio | Câu 15. Được khám đúng bác sĩ đã yêu cầu | ✓ | — |
| `kenh_datlich` | dropdown | Câu 16. Kênh đăng ký khám |  | — |
| `co_goikham` | radio | Câu 17. Sử dụng gói khám |  | — |
| `rieng_tu` | radio | Câu 18. Mức riêng tư khi trao đổi với bác sĩ |  | — |
| `suckhoe_tudanhgia` | radio | Câu 23. Tự đánh giá sức khỏe hiện tại | ✓ | — |
| `hoan_vi_chiphi` | radio | Câu 24. Hoãn/không làm dịch vụ được chỉ định vì ch |  | — |
| `a1` | radio | A1. Thời gian chờ đợi để làm thủ tục đăng ký khám |  | — |
| `a2` | radio | A2. Thời gian chờ đợi để được vào gặp bác sĩ khám |  | — |
| `a3` | radio | A3. Thời gian chờ đợi để thực hiện các dịch vụ cận |  | — |
| `a4` | radio | A4. Thời gian chờ đợi để nhận kết quả cận lâm sàng |  | — |
| `a5` | radio | A5. Sự dễ dàng và thuận tiện của thủ tục đăng ký k |  | — |
| `a6` | radio | A6. Sự rõ ràng và đầy đủ của việc được hướng dẫn v |  | — |
| `b1` | radio | B1. Sự sạch sẽ, vệ sinh của khu vực chờ khám |  | — |
| `b2` | radio | B2. Sự sạch sẽ, vệ sinh của phòng khám bác sĩ |  | — |
| `b3` | radio | B3. Sự sạch sẽ, vệ sinh của nhà vệ sinh dành cho n |  | — |
| `b4` | radio | B4. Sự đầy đủ và tiện nghi của ghế ngồi chờ |  | — |
| `b5` | radio | B5. Điều kiện không khí tại khu vực chờ |  | — |
| `b6` | radio | B6. Sự sẵn có của nước uống phục vụ người bệnh |  | — |
| `b7` | radio | B7. Sự rõ ràng, dễ thấy của biển báo, sơ đồ chỉ dẫ |  | — |
| `b8` | radio | B8. Cảm nhận về sự hiện đại, đầy đủ của trang thiế |  | — |
| `c1` | radio | C1. Thái độ ân cần, tôn trọng, lịch sự của bác sĩ |  | — |
| `c2` | radio | C2. Sự giải thích của bác sĩ về tình trạng bệnh |  | — |
| `c3` | radio | C3. Sự giải thích của bác sĩ về phương pháp điều t |  | — |
| `c4` | radio | C4. Thời gian bác sĩ dành để khám và tư vấn |  | — |
| `c5` | radio | C5. Sự tin tưởng vào năng lực chuyên môn của bác s |  | — |
| `c6` | radio | C6. Thái độ niềm nở, nhiệt tình, sẵn sàng giúp đỡ  |  | — |
| `c7` | radio | C7. Sự hướng dẫn rõ ràng, cụ thể về các thủ tục |  | — |
| `c8` | radio | C8. Sự cẩn thận, nhẹ nhàng và tôn trọng sự riêng t |  | — |
| `c9` | radio | C9. Thái độ lịch sự, thân thiện của nhân viên bảo  |  | — |
| `c10` | radio | C10. Sự sẵn sàng chỉ dẫn, giúp đỡ khi cần |  | — |
| `d1` | radio | D1. Sự công khai, rõ ràng về giá các dịch vụ y tế |  | — |
| `d2` | radio | D2. Sự giải thích về các khoản chi phí phải trả |  | — |
| `d3` | radio | D3. Sự hướng dẫn rõ ràng, đầy đủ về cách sử dụng t |  | — |
| `e1` | radio | E1. Mức độ đáp ứng nhu cầu khám chữa bệnh |  | — |
| `e2` | radio | E2. Sự tin tưởng vào kết quả chẩn đoán và điều trị |  | — |
| `f1` | radio | F1. Sự phù hợp của chi phí khám chữa bệnh so với c |  | — |
| `g1` | radio | G1. Nói chung, Ông/Bà hài lòng ở mức độ nào với tấ | ✓ | — |
| `g2` | radio | G2. Ý định quay lại khoa khám |  | — |
| `g3` | radio | G3. Ý định giới thiệu cho người thân/bạn bè |  | — |
| `ykiendonggop` | notes | Ý kiến đóng góp khác |  | — |

### Nhóm: lop_his (7 biến)

| Biến | Loại | Nhãn | Bắt buộc | Phạm vi |
|------|------|------|----------|---------|
| `thoigian_cho` | text | Thời gian chờ khám (phút) | ✓ | 0–1440 |
| `khunggio_kham` | radio | Khung giờ khám | ✓ | — |
| `ngay_trong_tuan` | radio | Ngày trong tuần khám | ✓ | — |
| `co_cls` | radio | Có làm cận lâm sàng |  | — |
| `so_quay_buoc` | text | Số bước/quầy phải qua |  | 0–30 |
| `ma_ban_kham` | text | Mã bàn khám/bác sĩ khám (đã giả danh) | ✓ | — |
| `trang_thai_ghep_his` | radio | Trạng thái ghép dữ liệu HIS | ✓ | — |

---

## PHẦN 2 — REDCAP DATA DICTIONARY

File CSV: `G5_REDCap_dictionary_hai-long-benh-nhan-C1a-BVQY175.csv` (**71 dòng**)
Biến số (numeric): 4
Biến ngày: 0
Biến bắt buộc: 15

Tóm tắt 10 biến đầu:
| Variable | Form | Type | Label | Bắt buộc |
|----------|------|------|-------|----------|
| `record_id` | phieu_khao_sat | text | Mã số phiếu (mã nghiên cứu) | ✓ |
| `mode_tra_loi` | phieu_khao_sat | radio | Câu 1. Cách hoàn thành phiếu | ✓ |
| `tuoi` | phieu_khao_sat | text | Câu 2. Tuổi (năm) | ✓ |
| `gioitinh` | phieu_khao_sat | radio | Câu 3. Giới tính | ✓ |
| `trinhdohocvan` | phieu_khao_sat | dropdown | Câu 4. Trình độ học vấn |  |
| `nghenghiep` | phieu_khao_sat | dropdown | Câu 5. Nghề nghiệp |  |
| `nghenghiepkhac` | phieu_khao_sat | text | Câu 5. Nghề nghiệp — ghi rõ nếu chọn Khác |  |
| `tinhtranghonnhan` | phieu_khao_sat | radio | Câu 6. Tình trạng hôn nhân |  |
| `noicutru` | phieu_khao_sat | radio | Câu 7. Nơi cư trú | ✓ |
| `khoangcachnhabv` | phieu_khao_sat | radio | Câu 20. Khoảng cách nhà–viện |  |
| ... | ... | ... | ... | ... |
| *(+61 dòng — xem file CSV)* | | | | |

---

## PHẦN 3 — LUẬT KIỂM TRA DỮ LIỆU (Validation Rules)

Dựng từ CHÍNH từ điển REDCap của đề tài — đúng các ràng buộc công cụ làm sạch áp khi khoá dữ liệu.

| Biến | Loại | Phạm vi | Quy tắc | Hành động |
|------|------|---------|---------|-----------|
| `record_id` | text | — | Mã số phiếu (mã nghiên cứu); bắt buộc | query nếu trống; Báo lỗi trùng ID — hệ thống REDCap tự phát hiện |
| `mode_tra_loi` | radio | mã 1, 2, 3 | Câu 1. Cách hoàn thành phiếu; bắt buộc | query nếu mã ngoài danh sách; query nếu trống |
| `tuoi` | integer | 18–120 | Câu 2. Tuổi (năm); bắt buộc | query nếu ngoài phạm vi; query nếu trống |
| `gioitinh` | radio | mã 1, 2 | Câu 3. Giới tính; bắt buộc | query nếu mã ngoài danh sách; query nếu trống |
| `trinhdohocvan` | dropdown | mã 1, 2, 3, 4, 5, 6, 7 | Câu 4. Trình độ học vấn | query nếu mã ngoài danh sách |
| `nghenghiep` | dropdown | mã 1, 2, 3, 4, 5, 6, 7, 8, 9 | Câu 5. Nghề nghiệp | query nếu mã ngoài danh sách |
| `tinhtranghonnhan` | radio | mã 1, 2, 3, 4 | Câu 6. Tình trạng hôn nhân | query nếu mã ngoài danh sách |
| `noicutru` | radio | mã 1, 2 | Câu 7. Nơi cư trú; bắt buộc | query nếu mã ngoài danh sách; query nếu trống |
| `khoangcachnhabv` | radio | mã 1, 2, 3 | Câu 20. Khoảng cách nhà–viện | query nếu mã ngoài danh sách |
| `thunhaphogd` | dropdown | mã 1, 2, 3, 4 | Câu 8. Thu nhập hộ gia đình/tháng | query nếu mã ngoài danh sách |
| `cobhyt` | radio | mã 1, 2 | Câu 9. Có thẻ BHYT còn hiệu lực; bắt buộc | query nếu mã ngoài danh sách; query nếu trống |
| `lydokham` | dropdown | mã 1, 2, 3, 4, 5 | Câu 10. Lý do khám lần này; bắt buộc | query nếu mã ngoài danh sách; query nếu trống |
| `solankham12thang` | radio | mã 1, 2, 3 | Câu 19. Số lần khám tại khoa trong 12 tháng qua | query nếu mã ngoài danh sách |
| `phuongtiendichuyen` | dropdown | mã 1, 2, 3, 4, 5, 6 | Câu 21. Phương tiện di chuyển đến viện | query nếu mã ngoài danh sách |
| `nguonthongtinbv` | dropdown | mã 1, 2, 3, 4, 5, 6 | Câu 22. Nguồn thông tin biết đến viện | query nếu mã ngoài danh sách |
| `kyvong_thoigiancho` | integer | 0–600 | Câu 11. Trước khi đến khám, Ông/Bà nghĩ mình sẽ phải chờ khoảng bao lâ | query nếu ngoài phạm vi |
| `xacnhan_kyvong` | radio | mã 1, 2, 3, 4, 5 | Câu 12. So với mong đợi trước khi đến, dịch vụ hôm nay như thế nào? | query nếu mã ngoài danh sách |
| `lydo_chon_theoyeucau` | checkbox | 0/1 mỗi cột `lydo_chon_theoyeucau___<mã>` (mã 1, 2, 3, 4, 5, 6, 7, 8) | Câu 13. Lý do chính chọn khám theo yêu cầu (chọn tối đa 2) | query nếu khác 0/1 |
| `co_yeucau_bacsi` | radio | mã 1, 2 | Câu 14. Có yêu cầu khám với một bác sĩ cụ thể không? | query nếu mã ngoài danh sách |
| `duoc_dung_bacsi` | radio | mã 1, 2, 7 | Câu 15. Được khám đúng bác sĩ đã yêu cầu; bắt buộc | query nếu mã ngoài danh sách; query nếu trống |
| `kenh_datlich` | dropdown | mã 1, 2, 3, 4, 8 | Câu 16. Kênh đăng ký khám | query nếu mã ngoài danh sách |
| `co_goikham` | radio | mã 1, 2, 8 | Câu 17. Sử dụng gói khám | query nếu mã ngoài danh sách |
| `rieng_tu` | radio | mã 1, 2, 3, 4, 5 | Câu 18. Mức riêng tư khi trao đổi với bác sĩ | query nếu mã ngoài danh sách |
| `suckhoe_tudanhgia` | radio | mã 1, 2, 3, 4, 5 | Câu 23. Tự đánh giá sức khỏe hiện tại; bắt buộc | query nếu mã ngoài danh sách; query nếu trống |
| `hoan_vi_chiphi` | radio | mã 1, 2, 8, 9 | Câu 24. Hoãn/không làm dịch vụ được chỉ định vì chi phí | query nếu mã ngoài danh sách |
| `a1` | radio | mã 1, 2, 3, 4, 5, 8, 9 | A1. Thời gian chờ đợi để làm thủ tục đăng ký khám | query nếu mã ngoài danh sách |
| `a2` | radio | mã 1, 2, 3, 4, 5, 8, 9 | A2. Thời gian chờ đợi để được vào gặp bác sĩ khám | query nếu mã ngoài danh sách |
| `a3` | radio | mã 1, 2, 3, 4, 5, 7, 8, 9 | A3. Thời gian chờ đợi để thực hiện các dịch vụ cận lâm sàng | query nếu mã ngoài danh sách |
| `a4` | radio | mã 1, 2, 3, 4, 5, 7, 8, 9 | A4. Thời gian chờ đợi để nhận kết quả cận lâm sàng | query nếu mã ngoài danh sách |
| `a5` | radio | mã 1, 2, 3, 4, 5, 8, 9 | A5. Sự dễ dàng và thuận tiện của thủ tục đăng ký khám bệnh | query nếu mã ngoài danh sách |
| `a6` | radio | mã 1, 2, 3, 4, 5, 8, 9 | A6. Sự rõ ràng và đầy đủ của việc được hướng dẫn về quy trình khám bện | query nếu mã ngoài danh sách |
| `b1` | radio | mã 1, 2, 3, 4, 5, 8, 9 | B1. Sự sạch sẽ, vệ sinh của khu vực chờ khám | query nếu mã ngoài danh sách |
| `b2` | radio | mã 1, 2, 3, 4, 5, 8, 9 | B2. Sự sạch sẽ, vệ sinh của phòng khám bác sĩ | query nếu mã ngoài danh sách |
| `b3` | radio | mã 1, 2, 3, 4, 5, 8, 9 | B3. Sự sạch sẽ, vệ sinh của nhà vệ sinh dành cho người bệnh | query nếu mã ngoài danh sách |
| `b4` | radio | mã 1, 2, 3, 4, 5, 8, 9 | B4. Sự đầy đủ và tiện nghi của ghế ngồi chờ | query nếu mã ngoài danh sách |
| `b5` | radio | mã 1, 2, 3, 4, 5, 8, 9 | B5. Điều kiện không khí tại khu vực chờ | query nếu mã ngoài danh sách |
| `b6` | radio | mã 1, 2, 3, 4, 5, 8, 9 | B6. Sự sẵn có của nước uống phục vụ người bệnh | query nếu mã ngoài danh sách |
| `b7` | radio | mã 1, 2, 3, 4, 5, 8, 9 | B7. Sự rõ ràng, dễ thấy của biển báo, sơ đồ chỉ dẫn trong khoa | query nếu mã ngoài danh sách |
| `b8` | radio | mã 1, 2, 3, 4, 5, 8, 9 | B8. Cảm nhận về sự hiện đại, đầy đủ của trang thiết bị y tế được sử dụ | query nếu mã ngoài danh sách |
| `c1` | radio | mã 1, 2, 3, 4, 5, 8, 9 | C1. Thái độ ân cần, tôn trọng, lịch sự của bác sĩ | query nếu mã ngoài danh sách |
| `c2` | radio | mã 1, 2, 3, 4, 5, 8, 9 | C2. Sự giải thích của bác sĩ về tình trạng bệnh | query nếu mã ngoài danh sách |
| `c3` | radio | mã 1, 2, 3, 4, 5, 8, 9 | C3. Sự giải thích của bác sĩ về phương pháp điều trị/xét nghiệm | query nếu mã ngoài danh sách |
| `c4` | radio | mã 1, 2, 3, 4, 5, 8, 9 | C4. Thời gian bác sĩ dành để khám và tư vấn | query nếu mã ngoài danh sách |
| `c5` | radio | mã 1, 2, 3, 4, 5, 8, 9 | C5. Sự tin tưởng vào năng lực chuyên môn của bác sĩ | query nếu mã ngoài danh sách |
| `c6` | radio | mã 1, 2, 3, 4, 5, 8, 9 | C6. Thái độ niềm nở, nhiệt tình, sẵn sàng giúp đỡ của điều dưỡng/kỹ th | query nếu mã ngoài danh sách |
| `c7` | radio | mã 1, 2, 3, 4, 5, 8, 9 | C7. Sự hướng dẫn rõ ràng, cụ thể về các thủ tục | query nếu mã ngoài danh sách |
| `c8` | radio | mã 1, 2, 3, 4, 5, 7, 8, 9 | C8. Sự cẩn thận, nhẹ nhàng và tôn trọng sự riêng tư của nhân viên khi  | query nếu mã ngoài danh sách |
| `c9` | radio | mã 1, 2, 3, 4, 5, 8, 9 | C9. Thái độ lịch sự, thân thiện của nhân viên bảo vệ/hướng dẫn/tiếp đó | query nếu mã ngoài danh sách |
| `c10` | radio | mã 1, 2, 3, 4, 5, 8, 9 | C10. Sự sẵn sàng chỉ dẫn, giúp đỡ khi cần | query nếu mã ngoài danh sách |
| `d1` | radio | mã 1, 2, 3, 4, 5, 8, 9 | D1. Sự công khai, rõ ràng về giá các dịch vụ y tế | query nếu mã ngoài danh sách |
| `d2` | radio | mã 1, 2, 3, 4, 5, 7, 8, 9 | D2. Sự giải thích về các khoản chi phí phải trả | query nếu mã ngoài danh sách |
| `d3` | radio | mã 1, 2, 3, 4, 5, 7, 8, 9 | D3. Sự hướng dẫn rõ ràng, đầy đủ về cách sử dụng thuốc | query nếu mã ngoài danh sách |
| `e1` | radio | mã 1, 2, 3, 4, 5, 8, 9 | E1. Mức độ đáp ứng nhu cầu khám chữa bệnh | query nếu mã ngoài danh sách |
| `e2` | radio | mã 1, 2, 3, 4, 5, 8, 9 | E2. Sự tin tưởng vào kết quả chẩn đoán và điều trị tại khoa | query nếu mã ngoài danh sách |
| `f1` | radio | mã 1, 2, 3, 4, 5, 8, 9 | F1. Sự phù hợp của chi phí khám chữa bệnh so với chất lượng dịch vụ nh | query nếu mã ngoài danh sách |
| `g1` | radio | mã 1, 2, 3, 4, 5 | G1. Nói chung, Ông/Bà hài lòng ở mức độ nào với tất cả các dịch vụ đã ; bắt buộc | query nếu mã ngoài danh sách; query nếu trống |
| `g2` | radio | mã 1, 2, 3, 4, 5 | G2. Ý định quay lại khoa khám | query nếu mã ngoài danh sách |
| `g3` | radio | mã 1, 2, 3, 4, 5 | G3. Ý định giới thiệu cho người thân/bạn bè | query nếu mã ngoài danh sách |
| `thoigian_cho` | number | 0–1440 | Thời gian chờ khám (phút); bắt buộc | query nếu ngoài phạm vi; query nếu trống |
| `khunggio_kham` | radio | mã 1, 2, 3, 4 | Khung giờ khám; bắt buộc | query nếu mã ngoài danh sách; query nếu trống |
| `ngay_trong_tuan` | radio | mã 1, 2, 3, 4, 5, 6, 7 | Ngày trong tuần khám; bắt buộc | query nếu mã ngoài danh sách; query nếu trống |
| `co_cls` | radio | mã 1, 0 | Có làm cận lâm sàng | query nếu mã ngoài danh sách |
| `so_quay_buoc` | integer | 0–30 | Số bước/quầy phải qua | query nếu ngoài phạm vi |
| `ma_ban_kham` | text | — | Mã bàn khám/bác sĩ khám (đã giả danh); bắt buộc | query nếu trống |
| `trang_thai_ghep_his` | radio | mã 1, 2 | Trạng thái ghép dữ liệu HIS; bắt buộc | query nếu mã ngoài danh sách; query nếu trống |

6 biến văn bản tự do không có ràng buộc phạm vi/mã — kiểm PII ở bước khử định danh.

---

## PHẦN 4 — SƠ ĐỒ THAM GIA NGHIÊN CỨU (STROBE/CONSORT Flowchart)

```
┌─────────────────────────────────────────────────────────────────┐
│        BIỂU ĐỒ THAM GIA NGHIÊN CỨU (STROBE Flowchart)         │
│                      Đề tài: hai-long-benh-nhan-C1a-BVQY175     │
└─────────────────────────────────────────────────────────────────┘

  ┌──────────────────────────────────────────┐
  │  Đánh giá đủ tiêu chuẩn (Assessed):     │
  │  N = [CẦN — BÁC SĨ ĐIỀN từ sổ bệnh]   │
  └────────────────┬─────────────────────────┘
                   │
        ┌──────────▼──────────────────┐
        │  Loại trừ (Excluded):        │
        │  N = [CẦN]                   │
  │  • [CẦN — tiêu chí loại trừ theo PICO/SAP thật]  │
        │  • Không đồng thuận          │
        │  • [CẦN thêm lý do cụ thể]  │
        └─────────────────────────────┘
                   │
  ┌────────────────▼─────────────────────────┐
  │  TUYỂN VÀO (Enrolled):                   │
  │  N = 1000 (cỡ mẫu kế hoạch, tối thiểu theo thống kê 808)│
  └────────────────┬─────────────────────────┘
                   │
        ┌──────────┴──────────────────┐
        │                             │
        ▼                             ▼
  ┌───────────────┐           ┌───────────────┐
  │  CÓ PHƠI      │           │  KHÔNG PHƠI   │
  │  NHIỄM [CẦN — tên biến phơi nhiễm/can thiệp theo PICO]│          │  NHIỄM        │
  │  N ≈ [CẦN]        │           │  N ≈ [CẦN]        │
  └───────┬───────┘           └───────┬───────┘
          │                           │
          ▼                           ▼
  ┌──────────────────────────────────────────┐
  │  ĐO ĐỒNG THỜI (cross-sectional):        │
  │  Phơi nhiễm + kết cục đo cùng 1 thời điểm│
  │  Không có giai đoạn theo dõi dọc.       │
  └────────────────┬─────────────────────────┘
                   │
  ┌────────────────▼─────────────────────────┐
  │  PHÂN TÍCH (Analysed):                   │
  │  N = 1000 → [CẦN điều chỉnh thực tế]│
  │  Phân tích chính: N = [CẦN — sau loại trừ] (cần tối thiểu 686 theo G3)│
  └──────────────────────────────────────────┘

  Ghi chú: Điền N=[CẦN] SAU khi thu thập dữ liệu thật.
  Tham chiếu: STROBE 2007 (PMID: 18064739). Cần bác sĩ kiểm chứng.

```

---

## PHẦN 5 — SCRIPTS TỰ ĐỘNG (Sinh từ CRF Dictionary)

**Thư mục:** `exports/hai-long-benh-nhan-C1a-BVQY175/scripts/`

| Script | Mô tả | Đầu vào | Đầu ra |
|--------|-------|---------|--------|
| `data_cleaning.py` | Làm sạch REDCap export; ép kiểu; kiểm range | `data/raw/redcap_export.csv` | `data/processed/df_clean.csv` |
| `data_quality_report.py` | Báo cáo N, % complete, vi phạm, trùng ID | `data/processed/df_clean.csv` | `data_quality_report.txt` |

Chạy theo thứ tự:
```bash
cd exports/hai-long-benh-nhan-C1a-BVQY175/
python scripts/data_cleaning.py --input data/raw/redcap_export.csv
python scripts/data_quality_report.py --input data/processed/df_clean.csv
```

---

## PHẦN 6 — QUẢN TRỊ DỮ LIỆU THIẾU VÀ SAI LỆCH

- G5 chỉ lập hồ sơ mức độ/mẫu hình thiếu và mở query; **không tự nội suy**.
- Phương pháp complete-case, multiple imputation hoặc phân tích nhạy cảm phải được định trước ở SAP G4 theo cơ chế thiếu và estimand.
- Mọi loại trừ người tham gia/điểm dữ liệu và protocol deviation phải có lý do, người xác nhận, thời điểm và audit trail.
- [CẦN ĐỐI CHIẾU] Ngưỡng cảnh báo thiếu cho từng biến trọng yếu theo protocol/SAP.

---

## PHẦN 7 — CẤU TRÚC GÓI TÁI LẶP

```
exports/hai-long-benh-nhan-C1a-BVQY175/
├── data/             # KHÔNG commit — chứa dữ liệu thật
│   ├── raw/          # dữ liệu thô từ REDCap export
│   └── processed/    # df_clean.csv + data_quality_report.txt
├── scripts/          # Python scripts tự động — có thể commit
│   ├── data_cleaning.py        # làm sạch REDCap export
│   └── data_quality_report.py  # báo cáo chất lượng
├── output/           # bảng kết quả, hình (generate — không commit binary)
├── docs/             # SAP, đề cương, các artifact G0-G4
│   ├── G4_A5_SAP_FINAL_hai-long-benh-nhan-C1a-BVQY175.md
│   └── G2_A3_ETHICS_PACKAGE_hai-long-benh-nhan-C1a-BVQY175.md
└── README.md         # Hướng dẫn tái lặp đầy đủ
```

**`.gitignore` bắt buộc:**
```
data/raw/
data/processed/
*.csv
*.xlsx
.env
```

---

## PHẦN 7B — VÒNG ĐỜI, BẢO MẬT VÀ AUDIT TRAIL

- **Provenance:** bản raw đã khử định danh được copy chỉ đọc, gắn SHA-256; mọi bản clean phải truy ngược được về raw và đúng phiên bản dictionary.
- **Audit trail/correction:** lưu giá trị ban đầu, thay đổi, lý do, thời điểm và vai trò thực hiện; không sửa/xóa giá trị lâm sàng chỉ vì nằm ngoài khoảng.
- **Khử định danh:** tách bảng ánh xạ khỏi dataset phân tích; không đưa họ tên, ngày sinh đầy đủ, số hồ sơ, điện thoại, địa chỉ hoặc mã định danh trực tiếp vào G5.
- **Phân quyền:** least privilege theo vai trò; rà quyền định kỳ; người phân tích chỉ nhận dataset đã khóa và không nhận bảng ánh xạ.
- **Sao lưu:** backup mã hóa theo quy định đơn vị và phải có bằng chứng thử phục hồi.
- **Lưu trữ/hủy:** thời hạn, nơi lưu, quyền truy cập và thủ tục hủy theo IRB, pháp luật và chính sách tài trợ/đơn vị; không dùng một thời hạn cứng cho mọi đề tài.
- **Sự cố:** ghi nhận vi phạm bảo mật, đánh giá ảnh hưởng và báo bên có thẩm quyền.

Tham chiếu: ICH E6(R3) §4.2–4.3; FDA Electronic Systems/Records/Signatures 2024.

---

## PHẦN 7C — CHIA SẺ DỮ LIỆU VÀ METADATA

- Xác định dữ liệu/metadata/code được chia sẻ, thời điểm, repository, thời hạn bảo tồn và người giám sát theo DMP/IRB/consent.
- Dữ liệu người tham gia chỉ chia sẻ khi quyền riêng tư, phạm vi đồng thuận và kiểm soát truy cập phù hợp; ghi rõ lý do đạo đức/pháp lý/kỹ thuật nếu hạn chế.
- Kèm protocol, data dictionary, README, mã phân tích và điều kiện tái sử dụng để hỗ trợ FAIR, nhưng FAIR không đồng nghĩa dữ liệu nhạy cảm phải mở công khai.

---

## PHẦN 8 — CHECKLIST KHÓA CƠ SỞ DỮ LIỆU

Thực hiện TRƯỚC khi chạy phân tích chính (G6):
- [ ] Tất cả data queries đã được giải quyết (trả lời đủ)
- [ ] Mức thiếu và protocol deviation đã đối chiếu theo SAP, không dùng ngưỡng chung tùy tiện
- [ ] Audit trail REDCap đầy đủ (không có chỉnh sửa không có lý do)
- [ ] Backup database kiểm tra thành công (restore test OK)
- [ ] Dual-entry hoặc 10% spot-check xác nhận
- [ ] Script `data_quality_report.py` chạy PASS (không có lỗi đỏ)
- [ ] Ngày khóa DB: [CẦN BÁC SĨ ĐIỀN]
- [ ] Người khóa DB (chữ ký): [CẦN]
- [ ] Người chứng kiến (chữ ký): [CẦN]

---

## PHẦN 9 — TIÊU CHÍ QUA CỔNG G5

- [ ] **[CẦN BÁC SĨ]** Điền tất cả [CẦN...] trong CRF (biến phơi nhiễm/kết cục cụ thể)
- [ ] **[CẦN BÁC SĨ]** Import REDCap dictionary CSV vào REDCap cơ sở
- [ ] **[CẦN BÁC SĨ + ĐỘI NC]** Thu thập dữ liệu thật (chỉ sau G2 = LOCKED)
- [ ] **[CẦN BÁC SĨ]** Spot-check 10% phiếu CRF
- [ ] **[CẦN BÁC SĨ]** Chạy `data_cleaning.py` + `data_quality_report.py` → PASS
- [ ] **[CẦN BÁC SĨ]** Ký biên bản khóa DB

---

*Cần bác sĩ kiểm chứng. KHÔNG đưa PII vào hệ thống.*
*Chỉ chạy pipeline dữ liệu thật khử định danh trong môi trường cục bộ được đơn vị cho phép.*