# Sổ quyết định của hội đồng nghiên cứu (căn cứ pháp quy G2, đơn vị chủ nhiệm) — btm-dtd2-ngoai-tru-BVQY175

- Ngày: 22/11/2026
- Căn cứ giao việc: bác sĩ chủ nhiệm 22/11/2026 — hội đồng của hệ giải quyết dữ kiện/quyết định chuyên môn, quản lý xung đột lợi ích, hoàn thiện SAP; bác sĩ chốt đề tài/mục tiêu, nhập số liệu thật và ký.
- Mỗi quyết định có căn cứ kiểm được (chuẩn, nguồn PMID/DOI đã kiểm rút bài, văn bản pháp quy, hoặc dữ kiện trong hồ sơ). Thay thế chỉ áp khi đoạn cũ xuất hiện đúng một lần.

## Thành viên: `btm_g2_can_cu_don_vi.json`

### G2-CAN-CU — Căn cứ pháp quy sai trong hồ sơ G2 (TT38/2018 là thông tư thi đua khen thưởng; NĐ 356 Điều 23; căn cứ miễn đồng thuận)

- Quyết định: Thay bằng căn cứ đúng đã đọc văn bản: Luật 91/2025/QH15 Điều 3 khoản 3, Điều 23 khoản 1; Nghị định 356/2025/NĐ-CP Điều 28; TT43/2024 Điều 7 khoản 1 điểm b; Helsinki 2024 đoạn 32, 24; CIOMS Hướng dẫn 10, 12. Bộ sinh G2 đã sửa cùng (tools/can_cu_dao_duc.py).
- Căn cứ: Văn bản luật và nghị định thành viên đạo đức hội đồng đã đọc (btm_dao_duc.json, khoá can_cu)
- Căn cứ: Bộ sinh G2 nhánh claude/nguon-g2-20261122 commit e5d0721b
- Thay ở `G2_A3_ETHICS_PACKAGE_btm-dtd2-ngoai-tru-BVQY175.md` dòng 207
  - Cũ:  Thời gian lưu: 2 năm sau kết thúc nghiên cứu
 (theo TT38/2018/TT-BYT về lưu trữ hồ sơ y tế)

  - Mới:  Thời gian lưu: 2 năm sau kết thúc nghiên cứu
 (thời hạn đã chốt của đề tài; chỉ lưu trong thời gian phù hợp với mục đích xử lý — Luật 91/2025/QH15,
 Điều 3 khoản 3)

- Thay ở `G2_A3_ETHICS_PACKAGE_btm-dtd2-ngoai-tru-BVQY175.md` dòng 222
  - Cũ:  Theo NĐ 356/2025/NĐ-CP Điều 23:
 ∎ Phát hiện vi phạm → báo cáo nội bộ trong 24 giờ
 ∎ Thông báo cơ quan bảo vệ dữ liệu trong 72 giờ
 ∎ Thông báo người tham gia bị ảnh hưởng ngay khi xác nhận
 ∎ Khắc phục và điều tra nguyên nhân, lưu hồ sơ xử lý

  - Mới:  ∎ Phát hiện vi phạm → người phát hiện báo ngay cho chủ nhiệm đề tài (bên kiểm soát dữ liệu)
 ∎ Thông báo cơ quan chuyên trách bảo vệ dữ liệu cá nhân chậm nhất 72 giờ kể từ khi phát hiện
 (Luật 91/2025/QH15, Điều 23 khoản 1); nội dung thông báo theo Nghị định 356/2025/NĐ-CP, Điều 28
 ∎ Khắc phục và điều tra nguyên nhân, lưu hồ sơ xử lý

- Thay ở `G2_A3_ETHICS_PACKAGE_btm-dtd2-ngoai-tru-BVQY175.md` dòng 345
  - Cũ: Căn cứ: TT43/2024/TT-BYT Điều 15 · Helsinki (WMA, bản sửa 2024) §29

  - Mới: Căn cứ: Helsinki (WMA, bản sửa đổi 10/2024) §32 + §24 · CIOMS 2016 Hướng dẫn 10 (ba điều kiện) + Hướng dẫn 12 · TT43/2024/TT-BYT Điều 7 khoản 1 điểm b

- Thay ở `G2_A3_ETHICS_PACKAGE_btm-dtd2-ngoai-tru-BVQY175.md` dòng 350
  - Cũ: CƠ SỞ XIN MIỄN (phải thỏa CẢ 4 điều kiện):

  - Mới: ĐẶC ĐIỂM DỮ LIỆU VÀ CAN THIỆP (điều kiện miễn theo CIOMS 2016 Hướng dẫn 10: đủ cả ba điều kiện, Hội đồng quyết):

- Thay ở `G2_A3_ETHICS_PACKAGE_btm-dtd2-ngoai-tru-BVQY175.md` dòng 362
  - Cũ: CỜ ĐỎ (bất kỳ → PHẢI lấy ICF đầy đủ):
☐ Có dữ liệu cá nhân nhận dạng được → ICF bắt buộc
☐ Có tiếp xúc người tham gia → ICF bắt buộc

  - Mới: LƯU Ý (CIOMS 2016 Hướng dẫn 10; Helsinki 2024 đoạn 32):
• Dữ liệu xác định được/giả danh hoá (còn bảng nối mã) không tự động buộc lấy chấp thuận;
 Hội đồng xét theo ba điều kiện của CIOMS 2016 Hướng dẫn 10, kèm biện pháp bảo mật.


### PI-DON-VI — Đơn vị công tác của chủ nhiệm trong bảng cán bộ đề cương BTM lấy nhầm nơi thực hiện đề tài

- Quyết định: Ghi đúng đơn vị công tác đã ghim của chủ nhiệm (Khoa Khám bệnh C1a, Trung tâm C1), thống nhất với hồ sơ G2 BTM và đề tài C1a; nơi thực hiện đề tài vẫn là Khoa Khám bệnh.
- Căn cứ: study_meta C1a: pi_unit do chủ nhiệm ghim
- Căn cứ: tien_do BTM 20–21/11: chủ nhiệm/đơn vị theo khuôn C1a; phiếu đề xuất BTM 3.1 — bác sĩ chọn «A — Đề xuất»
- Thay ở `DE_CUONG_NOP_HOI_DONG_btm-dtd2-ngoai-tru-BVQY175.md` dòng 45
  - Cũ: | 1 | ……… | Khoa Khám bệnh, Bệnh viện Quân y 175, Thành phố Hồ Chí Minh | Chủ nhiệm đề tài |
  - Mới: | 1 | ……… | Khoa Khám bệnh C1a, Trung tâm Khám bệnh và Điều trị theo yêu cầu C1, Bệnh viện Quân y 175, Thành phố Hồ Chí Minh | Chủ nhiệm đề tài |

## Tài liệu đưa vào gói ký (đã chuẩn bị theo các quyết định trên)

- Không phát sinh tài liệu ký mới.
