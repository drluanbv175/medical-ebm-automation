# Sổ quyết định của hội đồng nghiên cứu — hai-long-benh-nhan-C1a-BVQY175

- Ngày: 22/11/2026
- Căn cứ giao việc: bác sĩ chủ nhiệm 22/11/2026 — hội đồng của hệ giải quyết dữ kiện/quyết định chuyên môn, quản lý xung đột lợi ích, hoàn thiện SAP; bác sĩ chốt đề tài/mục tiêu, nhập số liệu thật và ký.
- Mỗi quyết định có căn cứ kiểm được (chuẩn, nguồn PMID/DOI đã kiểm rút bài, văn bản pháp quy, hoặc dữ kiện trong hồ sơ). Thay thế chỉ áp khi đoạn cũ xuất hiện đúng một lần.

## Thành viên: `hai-long-benh-nhan-C1a-BVQY175_g6_sap_bo_sung.json`

### G6-C0 — Ghi lịch sử phiên bản cho các sửa đổi SAP của hội đồng vai G6/G4.

- Quyết định: Thêm dòng «1.5 (sửa nháp 22/11 — đặc tả G6)». Không đổi kết cục chính, mô hình chính, tập biến hay cỡ mẫu; các sửa đổi chỉ định trước cách làm của các phân tích thăm dò/độ nhạy đã có.
- Căn cứ: SAP Phần 2 (lịch sử phiên bản)
- Thay ở `G4_A5_SAP_FINAL_hai-long-benh-nhan-C1a-BVQY175.md` dòng 40 (SỬA ĐỔI SAP)
  - Cũ: | 1.5 (sửa nháp 18/11) | 2026-11-18 | Trợ lý tự động theo lựa chọn của bác sĩ 18/11/2026 («Tỷ lệ ≥ 4/5») | §2: ghi phương pháp phân tích kết cục thứ cấp G2 (ý định quay lại) và G3 (ý định giới thiệu) — mô tả bằng phân bố 5 mức và tỷ lệ có ý định (mức 4–5, cùng ngưỡng khoá trước với G1) kèm KTC 95% Wilson hiệu chỉnh chùm theo bàn khám; không kiểm định giả thuyết. Trước đó §2 nêu G2, G3 là kết cục thứ cấp nhưng chưa định phương pháp. |
  - Mới: | 1.5 (sửa nháp 18/11) | 2026-11-18 | Trợ lý tự động theo lựa chọn của bác sĩ 18/11/2026 («Tỷ lệ ≥ 4/5») | §2: ghi phương pháp phân tích kết cục thứ cấp G2 (ý định quay lại) và G3 (ý định giới thiệu) — mô tả bằng phân bố 5 mức và tỷ lệ có ý định (mức 4–5, cùng ngưỡng khoá trước với G1) kèm KTC 95% Wilson hiệu chỉnh chùm theo bàn khám; không kiểm định giả thuyết. Trước đó §2 nêu G2, G3 là kết cục thứ cấp nhưng chưa định phương pháp. |
| 1.5 (sửa nháp 22/11 — đặc tả G6) | 2026-11-22 | Hội đồng nghiên cứu của hệ (vai G6/G4) | Đặc tả máy đọc G6 chạy được mọi phân tích, không còn mục làm tay: §4 định ngưỡng vi phạm giả định tỷ lệ odds (Brant p < 0,05) và KTC bootstrap theo cụm cho mô hình một phần; §5 phân tích trung gian thực hiện thuật toán quasi-Bayes Imai 2010 bằng mã R của hệ, định đại lượng ước lượng và cách làm phân tích độ nhạy; §9 định điểm ảnh hưởng (Cook > 4/n); §10 gói tương ứng. Không đổi kết cục chính, mô hình chính, tập biến hay cỡ mẫu. |

### G6-C1 — Phân tích trung gian thăm dò (SAP §5) ghi gói R `mediation`; máy phân tích không có gói này (đo 22/11/2026: requireNamespace("mediation") = FALSE) nên đặc tả cũ để «chờ làm tay», và SAP chưa định đại lượng ước lượng trên thang nào, mức phơi nhiễm so sánh, cách đưa biến trung gian vào mô hình kết cục, cách làm phân tích độ nhạy.

- Quyết định: Giữ phương pháp PI đã chọn (phương án A: trung gian nhân quả dựa trên hồi quy theo khung phản thực, mô phỏng quasi-Bayes Imai 2010) và thực hiện đúng thuật toán đó bằng mã R của hệ (MASS::polr, MASS::mvrnorm), không phụ thuộc cài thêm gói. Định trước: đại lượng ước lượng là chênh xác suất hài lòng (G1 ≥ 4) khi thời gian chờ tăng 15 phút so với giá trị quan sát của từng người; biến trung gian dạng số (1–5) trong mô hình kết cục; báo tác động gián tiếp, trực tiếp, tổng, tỷ lệ trung gian kèm KTC 95% bách phân vị 1.000 lần mô phỏng, hạt giống §10; độ nhạy với nhiễu không đo giữa trung gian và kết cục bằng thu nhỏ dần hệ số trung gian → kết cục (còn 75%, 50%, 25%, 0%) và tính lại tác động gián tiếp. Máy chạy: phan_tich_sap_bo_sung.py loại trung_gian.
- Căn cứ: Imai K, Keele L, Tingley D. Psychol Methods. 2010;15(4):309-34 — PMID 20954780 (đã có trong SAP §5 và danh mục TLTK [30] của đề cương)
- Căn cứ: SAP §5 nguyên văn: «(gói R `mediation`, 1.000 lần mô phỏng — đề xuất của bản nháp, thống kê viên xác nhận)»
- Căn cứ: SAP §10 nguyên văn: «`mediation` cho phân tích thăm dò trung gian §5 (PI chọn phương án A, 15/11/2026) — đề xuất của bản nháp, thống kê viên xác nhận khi ký;»
- Căn cứ: AGReMA bản ngắn (Lee 2021, PMID 34546296 — đã có trong SAP §5): báo cáo đại lượng ước lượng, mô hình, phân tích độ nhạy
- Thay ở `G4_A5_SAP_FINAL_hai-long-benh-nhan-C1a-BVQY175.md` dòng 106 (SỬA ĐỔI SAP)
  - Cũ: (gói R `mediation`, 1.000 lần mô phỏng — đề xuất của bản nháp, thống kê viên xác nhận)
  - Mới: (thuật toán mô phỏng quasi-Bayes của Imai 2010 thực hiện bằng mã R của hệ với `MASS::polr` và `MASS::mvrnorm`, 1.000 lần mô phỏng, hạt giống §10; đại lượng ước lượng là chênh xác suất hài lòng (G1 ≥ 4) khi thời gian chờ tăng 15 phút so với giá trị quan sát của từng người; biến trung gian ở dạng số 1–5 trong mô hình kết cục; báo tác động gián tiếp, trực tiếp, tổng và tỷ lệ trung gian kèm KTC 95% bách phân vị)
- Thay ở `G4_A5_SAP_FINAL_hai-long-benh-nhan-C1a-BVQY175.md` dòng 106 (SỬA ĐỔI SAP)
  - Cũ: phân tích độ nhạy với nhiễu không đo giữa biến trung gian và kết cục
  - Mới: phân tích độ nhạy với nhiễu không đo giữa biến trung gian và kết cục (thu nhỏ dần hệ số của biến trung gian trong mô hình kết cục còn 75%, 50%, 25%, 0% và tính lại tác động gián tiếp)
- Thay ở `G4_A5_SAP_FINAL_hai-long-benh-nhan-C1a-BVQY175.md` dòng 153 (SỬA ĐỔI SAP)
  - Cũ: `mediation` cho phân tích thăm dò trung gian §5 (PI chọn phương án A, 15/11/2026) — đề xuất của bản nháp, thống kê viên xác nhận khi ký;
  - Mới: `MASS` (`polr`, `mvrnorm`) cho mô phỏng quasi-Bayes của phân tích thăm dò trung gian §5 (cùng thuật toán Imai 2010 mà gói `mediation` cài đặt; PI chọn phương án A, 15/11/2026);

### G6-C2 — Kịch bản «có/không điểm ảnh hưởng» (SAP §9; đề cương (6)) không định điểm ảnh hưởng là gì — đặc tả cũ để «chờ phán đoán của thống kê viên trên chẩn đoán mô hình», tức chọn sau khi xem dữ liệu.

- Quyết định: Định trước quy tắc khách quan dựa trên đúng chẩn đoán SAP §5 đã cam kết cho nhánh tuyến tính nhạy cảm («phần dư + robust HC3 + Cook's distance (không loại tùy tiện)»): điểm ảnh hưởng là phiếu có khoảng cách Cook > 4/n trong hồi quy tuyến tính tương ứng (G1 coi liên tục, cùng bộ biến của mô hình chính); chạy lại mô hình chính không có các phiếu đó, báo số phiếu bị bỏ. Không loại phiếu khỏi phân tích chính. Máy chạy: phan_tich_sap_bo_sung.py loại thu_tu, bien_the anh_huong.
- Căn cứ: SAP §9 nguyên văn: «- Có/không điểm ảnh hưởng (không có “mô hình rút gọn”: mọi kịch bản giữ nguyên bộ biến điều chỉnh của mô hình chính sau quy tắc bỏ biến thưa §5, trừ hai kịch bản ngay dưới và kịch bản chỉ người không »
- Căn cứ: SAP §5 «Giả định»: «nhánh tuyến tính nhạy cảm: phần dư + robust HC3 + Cook's distance (không loại tùy tiện)»
- Thay ở `G4_A5_SAP_FINAL_hai-long-benh-nhan-C1a-BVQY175.md` dòng 133 (SỬA ĐỔI SAP)
  - Cũ: - Có/không điểm ảnh hưởng (không có “mô hình rút gọn”: mọi kịch bản giữ nguyên bộ biến điều chỉnh của mô hình chính sau quy tắc bỏ biến thưa §5, trừ hai kịch bản ngay dưới và kịch bản chỉ người không được hẹn trước giờ khám, nơi `co_hen_gio` là hằng số nên được bỏ)  
  - Mới: - Có/không điểm ảnh hưởng (điểm ảnh hưởng là phiếu có khoảng cách Cook > 4/n trong hồi quy tuyến tính tương ứng — G1 coi liên tục, cùng bộ biến, nhánh tuyến tính nhạy cảm §5; chạy lại mô hình chính không có các phiếu đó và báo số phiếu bị bỏ; không có “mô hình rút gọn”: mọi kịch bản giữ nguyên bộ biến điều chỉnh của mô hình chính sau quy tắc bỏ biến thưa §5, trừ hai kịch bản ngay dưới và kịch bản chỉ người không được hẹn trước giờ khám, nơi `co_hen_gio` là hằng số nên được bỏ)  
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 627
  - Cũ: (6) có và không có các quan sát có ảnh hưởng lớn;
  - Mới: (6) có và không có các quan sát có ảnh hưởng lớn (khoảng cách Cook lớn hơn 4/n trong hồi quy tuyến tính tương ứng);

### G6-C3 — SAP §4 chuyển sang mô hình tỷ số chênh tương xứng một phần «khi vi phạm» nhưng không định ngưỡng vi phạm, và mô hình có hệ số theo ngưỡng không có sai số chuẩn sandwich theo cụm (đo 22/11/2026: sandwich::vcovCL báo «estimating functions for scale regression not implemented» với ordinal::clm có nominal) trong khi SAP đòi gom cụm ở mọi kịch bản.

- Quyết định: Vi phạm = kiểm định Brant cho biến đó có p < 0,05 (α §12). Biến vi phạm có hệ số riêng từng ngưỡng (ordinal::clm với nominal), các biến khác giữ hệ số chung; KTC 95% bằng bootstrap theo cụm bàn khám (lấy lại bàn khám có hoàn lại, 1.000 lần, hạt giống §10, khoảng bách phân vị) để giữ nguyên tắc gom cụm. Không biến nào vi phạm ⇒ mô hình chính giữ nguyên. Máy chạy: phan_tich_sap_bo_sung.py loại ppo.
- Căn cứ: SAP §4 nguyên văn: «vi phạm → partial proportional odds/generalized ordered logit, báo hệ số theo từng ranh giới cắt cho biến vi phạm.»
- Căn cứ: SAP §4: «Gom cụm theo bàn khám (bắt buộc, mọi kịch bản)»
- Căn cứ: SAP §12: α = 0,05 hai phía
- Thay ở `G4_A5_SAP_FINAL_hai-long-benh-nhan-C1a-BVQY175.md` dòng 82 (SỬA ĐỔI SAP)
  - Cũ: vi phạm → partial proportional odds/generalized ordered logit, báo hệ số theo từng ranh giới cắt cho biến vi phạm.
  - Mới: vi phạm (kiểm định Brant cho biến đó có p < 0,05, α §12) → partial proportional odds/generalized ordered logit (hệ số riêng từng ngưỡng cho biến vi phạm, các biến khác giữ hệ số chung; KTC 95% bằng bootstrap theo cụm bàn khám 1.000 lần, hạt giống §10), báo hệ số theo từng ranh giới cắt cho biến vi phạm.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 615
  - Cũ: nếu vi phạm, dùng mô hình tỷ số chênh tương xứng một phần [16]
  - Mới: nếu vi phạm (kiểm định Brant cho biến đó có p < 0,05), dùng mô hình tỷ số chênh tương xứng một phần [16]

### G6-C4 — SAP §3 báo số người được chọn theo TỪNG mã kết quả (đồng ý; từ chối; không đủ tiêu chuẩn; không vào buồng khám; không gặp được) và tỷ lệ không gặp được, đáp ứng chung — nhưng khuôn sổ chỉ có so_moi, so_dong_y, so_tu_choi nên không tính được; đặc tả cũ để «chờ lập bảng tay».

- Quyết định: Dòng tong_hop của sổ (mỗi ngày × khung giờ, không định danh) thêm bốn cột đếm: so_duoc_chon, so_khong_vao_kham, so_khong_du_tieu_chuan, so_khong_gap. Khi đó mọi tỷ lệ của SAP §3 tính được bằng máy: không gặp được = so_khong_gap ÷ (so_duoc_chon − so_khong_vao_kham); đồng ý = so_dong_y ÷ so_moi; hoàn thành phiếu = số phiếu nhận lại ÷ so_dong_y; phiếu hợp lệ = PhieuHopLe ÷ phiếu nhận lại; đáp ứng chung = phiếu hợp lệ ÷ (so_moi + so_khong_gap); so sánh người từ chối (dòng tu_choi) với người tham gia theo nhóm tuổi, giới, khung giờ. Máy chạy: phan_tich_sap_bo_sung.py loại dap_ung.
- Căn cứ: SAP §3 «Đáp ứng và người từ chối» (danh sách mã kết quả và công thức đáp ứng chung)
- Căn cứ: Đề cương mục 2.5.2: «mỗi số trong danh sách số được chọn được ghi một mã kết quả: đồng ý tham gia; từ chối; không đủ tiêu chuẩn (kể cả chuyển nhập viện hoặc cấp cứu); không vào buồng khám (bỏ về trước khi khám – ngoài khung mẫu); đã hoàn thành lượt khám nhưng không gặp được để mời»
- Căn cứ: Bảng kiểm CROSS cho nghiên cứu khảo sát — đề cương TLTK [44] (đề cương mục 2.2 áp dụng CROSS; mục tỷ lệ đáp ứng)
- Thay ở `_so-chon-mau-tu-choi.csv` dòng 1
  - Cũ: loai_dong,ngay_khao_sat,khunggio_kham,ma_dieu_tra_vien,so_moi,so_dong_y,so_tu_choi,nhom_tuoi_uoc_luong,gioi,ly_do_tu_neu
  - Mới: loai_dong,ngay_khao_sat,khunggio_kham,ma_dieu_tra_vien,so_duoc_chon,so_khong_vao_kham,so_khong_du_tieu_chuan,so_khong_gap,so_moi,so_dong_y,so_tu_choi,nhom_tuoi_uoc_luong,gioi,ly_do_tu_neu
- Thay ở `_quyet-dinh-bo-bien.md` dòng 82
  - Cũ:   - `loai_dong` = `tong_hop` (mỗi ngày × khung giờ: `so_moi`, `so_dong_y`, `so_tu_choi`, `ma_dieu_tra_vien`) hoặc
  - Mới:   - `loai_dong` = `tong_hop` (mỗi ngày × khung giờ: `so_duoc_chon`, `so_khong_vao_kham`, `so_khong_du_tieu_chuan`, `so_khong_gap`, `so_moi`, `so_dong_y`, `so_tu_choi`, `ma_dieu_tra_vien` — đủ số theo từng mã kết quả của đề cương 2.5.2 cho bảng đáp ứng SAP §3) hoặc

### G6-C5 — Trọng số hậu phân tầng (SAP §4) và phân tích giới hạn cho người bỏ về (SAP §9) cần số tổng hợp HIS (Nₕ từng ô ngày × khung giờ; số lượt lấy số, lượt bỏ về, thời gian chờ nhóm bỏ về) nhưng kế hoạch quản lý dữ liệu chưa định tệp và cột để máy đọc; SAP §9 còn đòi trung vị [KTPV] thời gian chờ nhóm bỏ về trong khi đề cương 2.6.4.3 chỉ ghi «thời gian chờ trung vị».

- Quyết định: Phòng CNTT/QLCL bàn giao hai tệp tổng hợp không định danh ở thư mục đề tài: `his_tong_hop/N_tang_HIS.csv` (cột ngay_trong_tuan, khunggio_kham, N_h — số lượt khám hoàn thành của ô trong các ngày thu thập) và `his_tong_hop/bo_ve_HIS.csv` (cột luot_lay_so, luot_bo_ve, cho_trung_vi, cho_p25, cho_p75 — phút). Tên cột khớp hàm trọng số dùng chung của G6 (g6_trong_so_survey). Máy chạy: phan_tich_sap_bo_sung.py loại trong_so (che_do kich_hoat, thiet_ke, gioi_han_bo_ve).
- Căn cứ: SAP §4 «Trọng số theo thiết kế chọn mẫu» (Nₕ từ HIS) và §9 «Phân tích giới hạn cho người bỏ về» (f từ HIS; «so sánh trung vị [IQR] thời gian chờ của nhóm bỏ về với nhóm được khám»)
- Căn cứ: G5_A6 nguyên văn: «- **Ghép dữ liệu từ nguồn khác:** Mốc thời gian chờ và số liệu tổng hợp người bỏ về do Phòng CNTT/QLCL trích xuất từ HIS/eHospital, ghép với phiếu qua mã bàn khám giả danh _(nguồn: đề cương nộp 4.6.3;»
- Thay ở `G5_A6_DATA_MGMT_hai-long-benh-nhan-C1a-BVQY175.md` dòng 108
  - Cũ: - **Ghép dữ liệu từ nguồn khác:** Mốc thời gian chờ và số liệu tổng hợp người bỏ về do Phòng CNTT/QLCL trích xuất từ HIS/eHospital, ghép với phiếu qua mã bàn khám giả danh _(nguồn: đề cương nộp 4.6.3; G1 data_collection_method)_
  - Mới: - **Ghép dữ liệu từ nguồn khác:** Mốc thời gian chờ và số liệu tổng hợp người bỏ về do Phòng CNTT/QLCL trích xuất từ HIS/eHospital, ghép với phiếu qua mã bàn khám giả danh _(nguồn: đề cương nộp 4.6.3; G1 data_collection_method)_
- **Tệp số tổng hợp HIS (không định danh) cho G6:** `his_tong_hop/N_tang_HIS.csv` — cột `ngay_trong_tuan`, `khunggio_kham`, `N_h` (số lượt khám hoàn thành có giờ gọi vào buồng khám của từng ô ngày trong tuần × khung giờ trong các ngày thu thập; SAP §4); `his_tong_hop/bo_ve_HIS.csv` — một dòng, cột `luot_lay_so`, `luot_bo_ve`, `cho_trung_vi`, `cho_p25`, `cho_p75` (thời gian chờ của nhóm bỏ về trước khi vào buồng khám, phút; SAP §9). Phòng CNTT/QLCL lập từ HIS cho đúng kỳ thu thập và bàn giao cùng mốc thời gian chờ.

## Tài liệu đưa vào gói ký (đã chuẩn bị theo các quyết định trên)

- Không phát sinh tài liệu ký mới.
