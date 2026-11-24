# Sổ quyết định của hội đồng nghiên cứu — hai-long-benh-nhan-C1a-BVQY175

- Ngày: 22/11/2026
- Căn cứ giao việc: bác sĩ chủ nhiệm 22/11/2026 — hội đồng của hệ giải quyết dữ kiện/quyết định chuyên môn, quản lý xung đột lợi ích, hoàn thiện SAP; bác sĩ chốt đề tài/mục tiêu, nhập số liệu thật và ký.
- Mỗi quyết định có căn cứ kiểm được (chuẩn, nguồn PMID/DOI đã kiểm rút bài, văn bản pháp quy, hoặc dữ kiện trong hồ sơ). Thay thế chỉ áp khi đoạn cũ xuất hiện đúng một lần.

## Thành viên: `hai-long-benh-nhan-C1a-BVQY175_tam_nguyen_tac.json`

### TNT-QC-04 — Ma trận 8 nguyên tắc (K20) — ô «Tiến độ và nguồn lực × Kiểm soát chất lượng liên tục» đỏ: sổ rủi ro máy đọc (gate_params.G1.risk_register) còn ô xác suất «[CẦN]» ở cả 9 rủi ro R1–R9, nên đánh giá rủi ro chưa hoàn tất (thiếu một trong hai chiều xác suất × tác động).

- Quyết định: Điền mức xác suất cho từng rủi ro: rủi ro đã có căn cứ trong hồ sơ thì xếp mức kèm căn cứ (R2, R6, R9); rủi ro phụ thuộc dữ kiện thực địa chưa có thì KHÔNG đoán mà ghi quy tắc xếp mức bằng chỉ số đo được ở buổi chạy thử/HIS và thời điểm cập nhật sổ (R1, R3, R4, R5, R7, R8). Sau khi áp, chạy lại G1 để sinh lại G1_A13b_RISK_REGISTER từ study_meta (tệp .md được sinh lại).
- Căn cứ: ICH E6(R3) — quản lý chất lượng dựa trên rủi ro: đánh giá rủi ro theo khả năng xảy ra và tác động, rà lại định kỳ tại các mốc
- Căn cứ: Đề cương nộp, Bảng 2.3 «Tiêu chí khả thi của buổi chạy thử» (tiêu chí 2: tỷ lệ đồng ý < 60%; tiêu chí 3: ghép HIS < 90%) — dòng 412–423
- Căn cứ: study_meta.gate_params.G0.finer_feasible: nhân lực ngoài khoa chưa ấn định; lưu lượng/hệ số biến thiên theo tầng từ HIS chưa có
- Căn cứ: G3_checkpoint.json: dropout 0,15 (mức dự phòng đã dùng khi tính cỡ mẫu)
- Căn cứ: Đề cương nộp, Bảng F.4 «Rủi ro dự kiến và biện pháp xử lý» (R6, R9) và mục 2.1, 2.7
- Căn cứ: Luật chung hội đồng, mục 2: dữ kiện thực địa chưa biết thì không đoán, sửa cách làm để đúng dù thực tế thế nào
- Thay ở `study_meta.json` dòng 134
  - Cũ: "rui_ro": "Tỷ lệ từ chối cao (nếu tỷ lệ đồng ý chỉ khoảng 60% – ngưỡng tối thiểu của buổi chạy thử – cần khoảng 1.700 lượt mời)",
          "xac_suat": "[CẦN]",
  - Mới: "rui_ro": "Tỷ lệ từ chối cao (nếu tỷ lệ đồng ý chỉ khoảng 60% – ngưỡng tối thiểu của buổi chạy thử – cần khoảng 1.700 lượt mời)",
          "xac_suat": "Chưa ước lượng được trước buổi chạy thử; xếp mức theo tiêu chí 2 của Bảng 2.3 (tỷ lệ đồng ý dưới 60% số người được mời là không khả thi) và cập nhật sổ tại mốc rà ngay sau buổi chạy thử",
- Thay ở `study_meta.json` dòng 145
  - Cũ: "rui_ro": "Thiếu điều tra viên",
          "xac_suat": "[CẦN]",
  - Mới: "rui_ro": "Thiếu điều tra viên",
          "xac_suat": "Cao cho tới khi danh sách điều tra viên ngoài khoa và người dự phòng được ấn định (nhân lực ngoài khoa chưa ấn định ở thời điểm lập đề cương); hạ mức khi đủ người trước buổi chạy thử",
- Thay ở `study_meta.json` dòng 156
  - Cũ: "rui_ro": "Lưu lượng người bệnh biến động theo mùa",
          "xac_suat": "[CẦN]",
  - Mới: "rui_ro": "Lưu lượng người bệnh biến động theo mùa",
          "xac_suat": "Chưa ước lượng được; xếp mức theo hệ số biến thiên lưu lượng theo tầng ngày trong tuần × khung giờ lấy từ HIS 12 tháng gần nhất, cập nhật sổ trước khi lập kế hoạch phân bổ mẫu",
- Thay ở `study_meta.json` dòng 167
  - Cũ: "rui_ro": "Sai lệch do mong muốn xã hội, hiệu ứng trần",
          "xac_suat": "[CẦN]",
  - Mới: "rui_ro": "Sai lệch do mong muốn xã hội, hiệu ứng trần",
          "xac_suat": "Chưa ước lượng được trước buổi chạy thử; xếp mức theo tỷ lệ phiếu đạt điểm tối đa ở câu hài lòng chung G1 trong buổi chạy thử và cập nhật sổ tại mốc rà ngay sau buổi chạy thử",
- Thay ở `study_meta.json` dòng 178
  - Cũ: "rui_ro": "Thời gian chờ phê duyệt kéo dài",
          "xac_suat": "[CẦN]",
  - Mới: "rui_ro": "Thời gian chờ phê duyệt kéo dài",
          "xac_suat": "Xếp mức theo quy trình thẩm định Hội đồng Đạo đức chấp nhận khi nộp (rút gọn hoặc phiên toàn thể) và cập nhật sổ khi có lịch họp",
- Thay ở `study_meta.json` dòng 189
  - Cũ: "rui_ro": "Lộ thông tin cá nhân",
          "xac_suat": "[CẦN]",
  - Mới: "rui_ro": "Lộ thông tin cá nhân",
          "xac_suat": "Thấp — phiếu khuyết danh, phiếu đồng ý lưu riêng, ghép thời gian chờ HIS bằng quy trình giả danh hóa có kiểm soát (Bảng F.4, mục 2.7)",
- Thay ở `study_meta.json` dòng 200
  - Cũ: "rui_ro": "Không trích xuất được thời gian chờ từ HIS",
          "xac_suat": "[CẦN]",
  - Mới: "rui_ro": "Không trích xuất được thời gian chờ từ HIS",
          "xac_suat": "Chưa ước lượng được trước buổi chạy thử; xếp mức theo tiêu chí 3 của Bảng 2.3 (ghép được thời gian chờ từ HIS dưới 90% số phiếu là không khả thi) và cập nhật sổ tại mốc rà ngay sau buổi chạy thử",
- Thay ở `study_meta.json` dòng 211
  - Cũ: "rui_ro": "Dữ liệu thiếu",
          "xac_suat": "[CẦN]",
  - Mới: "rui_ro": "Dữ liệu thiếu",
          "xac_suat": "Chưa ước lượng được trước buổi chạy thử; xếp mức theo tỷ lệ phiếu không hợp lệ ở buổi chạy thử so với mức dự phòng 15% đã dùng khi tính cỡ mẫu và cập nhật sổ tại mốc rà ngay sau buổi chạy thử",
- Thay ở `study_meta.json` dòng 222
  - Cũ: "rui_ro": "Người bệnh tham gia trùng lặp",
          "xac_suat": "[CẦN]",
  - Mới: "rui_ro": "Người bệnh tham gia trùng lặp",
          "xac_suat": "Thấp — mỗi người bệnh chỉ tham gia một lần, có câu hỏi chống trùng trước khi mời và loại bản ghi trùng khi làm sạch số liệu (mục 2.1, Bảng F.4)",

### TNT-PHAI-SINH — Ma trận 8 nguyên tắc — ô «Biến số và kết cục × Tính tái lập» đỏ: công thức biến phái sinh PhieuHopLe đã đổi theo quyết định hội đồng 22/11/2026 nên dòng duyệt của thống kê viên (dấu 04199f7fda85) không còn khớp công thức hiện hành (dấu 1034d6d3d6f3) — bien_phai_sinh.py kiem báo HET_HIEU_LUC.

- Quyết định: Không sửa công thức (công thức mới là quyết định đã áp của hội đồng). Đưa dòng duyệt lại công thức PhieuHopLe vào gói ký của thống kê viên; cột nguoi_duyet chỉ người duyệt ghi.
- Căn cứ: tools/bien_phai_sinh.py — hợp đồng cột nguoi_duyet «<VAI>:<tham chiếu>:<YYYY-MM-DD>:<dấu>»; sửa công thức sau khi duyệt ⇒ hết hiệu lực; agent không ghi cột này
- Căn cứ: exports/hai-long-benh-nhan-C1a-BVQY175/_bien-phai-sinh.csv dòng 11 (PhieuHopLe)

## Tài liệu đưa vào gói ký (đã chuẩn bị theo các quyết định trên)

1. Thống kê viên ký duyệt lại công thức PhieuHopLe với dấu 1034d6d3d6f3 (tools/bien_phai_sinh.py kiem in dấu; ghi cột nguoi_duyet). (căn cứ: TNT-PHAI-SINH)
