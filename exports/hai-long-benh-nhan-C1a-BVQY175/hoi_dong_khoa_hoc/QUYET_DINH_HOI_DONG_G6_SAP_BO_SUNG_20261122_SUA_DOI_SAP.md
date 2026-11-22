# Bản sửa đổi kế hoạch phân tích thống kê — hai-long-benh-nhan-C1a-BVQY175 — 22/11/2026

Các thay đổi dưới đây do hội đồng nghiên cứu của hệ quyết định trước khi có số liệu, kèm căn cứ ở sổ quyết định cùng thư mục. Thống kê viên và chủ nhiệm xem và ký để khoá phiên bản SAP mới.

## 1. G6-C0 — `G4_A5_SAP_FINAL_hai-long-benh-nhan-C1a-BVQY175.md` dòng 40

- Lý do: Thêm dòng «1.5 (sửa nháp 22/11 — đặc tả G6)». Không đổi kết cục chính, mô hình chính, tập biến hay cỡ mẫu; các sửa đổi chỉ định trước cách làm của các phân tích thăm dò/độ nhạy đã có.
- Cũ: | 1.5 (sửa nháp 18/11) | 2026-11-18 | Trợ lý tự động theo lựa chọn của bác sĩ 18/11/2026 («Tỷ lệ ≥ 4/5») | §2: ghi phương pháp phân tích kết cục thứ cấp G2 (ý định quay lại) và G3 (ý định giới thiệu) — mô tả bằng phân bố 5 mức và tỷ lệ có ý định (mức 4–5, cùng ngưỡng khoá trước với G1) kèm KTC 95% Wilson hiệu chỉnh chùm theo bàn khám; không kiểm định giả thuyết. Trước đó §2 nêu G2, G3 là kết cục thứ cấp nhưng chưa định phương pháp. |
- Mới: | 1.5 (sửa nháp 18/11) | 2026-11-18 | Trợ lý tự động theo lựa chọn của bác sĩ 18/11/2026 («Tỷ lệ ≥ 4/5») | §2: ghi phương pháp phân tích kết cục thứ cấp G2 (ý định quay lại) và G3 (ý định giới thiệu) — mô tả bằng phân bố 5 mức và tỷ lệ có ý định (mức 4–5, cùng ngưỡng khoá trước với G1) kèm KTC 95% Wilson hiệu chỉnh chùm theo bàn khám; không kiểm định giả thuyết. Trước đó §2 nêu G2, G3 là kết cục thứ cấp nhưng chưa định phương pháp. |
| 1.5 (sửa nháp 22/11 — đặc tả G6) | 2026-11-22 | Hội đồng nghiên cứu của hệ (vai G6/G4) | Đặc tả máy đọc G6 chạy được mọi phân tích, không còn mục làm tay: §4 định ngưỡng vi phạm giả định tỷ lệ odds (Brant p < 0,05) và KTC bootstrap theo cụm cho mô hình một phần; §5 phân tích trung gian thực hiện thuật toán quasi-Bayes Imai 2010 bằng mã R của hệ, định đại lượng ước lượng và cách làm phân tích độ nhạy; §9 định điểm ảnh hưởng (Cook > 4/n); §10 gói tương ứng. Không đổi kết cục chính, mô hình chính, tập biến hay cỡ mẫu. |

## 2. G6-C1 — `G4_A5_SAP_FINAL_hai-long-benh-nhan-C1a-BVQY175.md` dòng 106

- Lý do: Giữ phương pháp PI đã chọn (phương án A: trung gian nhân quả dựa trên hồi quy theo khung phản thực, mô phỏng quasi-Bayes Imai 2010) và thực hiện đúng thuật toán đó bằng mã R của hệ (MASS::polr, MASS::mvrnorm), không phụ thuộc cài thêm gói. Định trước: đại lượng ước lượng là chênh xác suất hài lòng (G1 ≥ 4) khi thời gian chờ tăng 15 phút so với giá trị quan sát của từng người; biến trung gian dạng số (1–5) trong mô hình kết cục; báo tác động gián tiếp, trực tiếp, tổng, tỷ lệ trung gian kèm KTC 95% bách phân vị 1.000 lần mô phỏng, hạt giống §10; độ nhạy với nhiễu không đo giữa trung gian và kết cục bằng thu nhỏ dần hệ số trung gian → kết cục (còn 75%, 50%, 25%, 0%) và tính lại tác động gián tiếp. Máy chạy: phan_tich_sap_bo_sung.py loại trung_gian.
- Cũ: (gói R `mediation`, 1.000 lần mô phỏng — đề xuất của bản nháp, thống kê viên xác nhận)
- Mới: (thuật toán mô phỏng quasi-Bayes của Imai 2010 thực hiện bằng mã R của hệ với `MASS::polr` và `MASS::mvrnorm`, 1.000 lần mô phỏng, hạt giống §10; đại lượng ước lượng là chênh xác suất hài lòng (G1 ≥ 4) khi thời gian chờ tăng 15 phút so với giá trị quan sát của từng người; biến trung gian ở dạng số 1–5 trong mô hình kết cục; báo tác động gián tiếp, trực tiếp, tổng và tỷ lệ trung gian kèm KTC 95% bách phân vị)

## 3. G6-C1 — `G4_A5_SAP_FINAL_hai-long-benh-nhan-C1a-BVQY175.md` dòng 106

- Lý do: Giữ phương pháp PI đã chọn (phương án A: trung gian nhân quả dựa trên hồi quy theo khung phản thực, mô phỏng quasi-Bayes Imai 2010) và thực hiện đúng thuật toán đó bằng mã R của hệ (MASS::polr, MASS::mvrnorm), không phụ thuộc cài thêm gói. Định trước: đại lượng ước lượng là chênh xác suất hài lòng (G1 ≥ 4) khi thời gian chờ tăng 15 phút so với giá trị quan sát của từng người; biến trung gian dạng số (1–5) trong mô hình kết cục; báo tác động gián tiếp, trực tiếp, tổng, tỷ lệ trung gian kèm KTC 95% bách phân vị 1.000 lần mô phỏng, hạt giống §10; độ nhạy với nhiễu không đo giữa trung gian và kết cục bằng thu nhỏ dần hệ số trung gian → kết cục (còn 75%, 50%, 25%, 0%) và tính lại tác động gián tiếp. Máy chạy: phan_tich_sap_bo_sung.py loại trung_gian.
- Cũ: phân tích độ nhạy với nhiễu không đo giữa biến trung gian và kết cục
- Mới: phân tích độ nhạy với nhiễu không đo giữa biến trung gian và kết cục (thu nhỏ dần hệ số của biến trung gian trong mô hình kết cục còn 75%, 50%, 25%, 0% và tính lại tác động gián tiếp)

## 4. G6-C1 — `G4_A5_SAP_FINAL_hai-long-benh-nhan-C1a-BVQY175.md` dòng 153

- Lý do: Giữ phương pháp PI đã chọn (phương án A: trung gian nhân quả dựa trên hồi quy theo khung phản thực, mô phỏng quasi-Bayes Imai 2010) và thực hiện đúng thuật toán đó bằng mã R của hệ (MASS::polr, MASS::mvrnorm), không phụ thuộc cài thêm gói. Định trước: đại lượng ước lượng là chênh xác suất hài lòng (G1 ≥ 4) khi thời gian chờ tăng 15 phút so với giá trị quan sát của từng người; biến trung gian dạng số (1–5) trong mô hình kết cục; báo tác động gián tiếp, trực tiếp, tổng, tỷ lệ trung gian kèm KTC 95% bách phân vị 1.000 lần mô phỏng, hạt giống §10; độ nhạy với nhiễu không đo giữa trung gian và kết cục bằng thu nhỏ dần hệ số trung gian → kết cục (còn 75%, 50%, 25%, 0%) và tính lại tác động gián tiếp. Máy chạy: phan_tich_sap_bo_sung.py loại trung_gian.
- Cũ: `mediation` cho phân tích thăm dò trung gian §5 (PI chọn phương án A, 15/11/2026) — đề xuất của bản nháp, thống kê viên xác nhận khi ký;
- Mới: `MASS` (`polr`, `mvrnorm`) cho mô phỏng quasi-Bayes của phân tích thăm dò trung gian §5 (cùng thuật toán Imai 2010 mà gói `mediation` cài đặt; PI chọn phương án A, 15/11/2026);

## 5. G6-C2 — `G4_A5_SAP_FINAL_hai-long-benh-nhan-C1a-BVQY175.md` dòng 133

- Lý do: Định trước quy tắc khách quan dựa trên đúng chẩn đoán SAP §5 đã cam kết cho nhánh tuyến tính nhạy cảm («phần dư + robust HC3 + Cook's distance (không loại tùy tiện)»): điểm ảnh hưởng là phiếu có khoảng cách Cook > 4/n trong hồi quy tuyến tính tương ứng (G1 coi liên tục, cùng bộ biến của mô hình chính); chạy lại mô hình chính không có các phiếu đó, báo số phiếu bị bỏ. Không loại phiếu khỏi phân tích chính. Máy chạy: phan_tich_sap_bo_sung.py loại thu_tu, bien_the anh_huong.
- Cũ: - Có/không điểm ảnh hưởng (không có “mô hình rút gọn”: mọi kịch bản giữ nguyên bộ biến điều chỉnh của mô hình chính sau quy tắc bỏ biến thưa §5, trừ hai kịch bản ngay dưới và kịch bản chỉ người không được hẹn trước giờ khám, nơi `co_hen_gio` là hằng số nên được bỏ)  
- Mới: - Có/không điểm ảnh hưởng (điểm ảnh hưởng là phiếu có khoảng cách Cook > 4/n trong hồi quy tuyến tính tương ứng — G1 coi liên tục, cùng bộ biến, nhánh tuyến tính nhạy cảm §5; chạy lại mô hình chính không có các phiếu đó và báo số phiếu bị bỏ; không có “mô hình rút gọn”: mọi kịch bản giữ nguyên bộ biến điều chỉnh của mô hình chính sau quy tắc bỏ biến thưa §5, trừ hai kịch bản ngay dưới và kịch bản chỉ người không được hẹn trước giờ khám, nơi `co_hen_gio` là hằng số nên được bỏ)  

## 6. G6-C3 — `G4_A5_SAP_FINAL_hai-long-benh-nhan-C1a-BVQY175.md` dòng 82

- Lý do: Vi phạm = kiểm định Brant cho biến đó có p < 0,05 (α §12). Biến vi phạm có hệ số riêng từng ngưỡng (ordinal::clm với nominal), các biến khác giữ hệ số chung; KTC 95% bằng bootstrap theo cụm bàn khám (lấy lại bàn khám có hoàn lại, 1.000 lần, hạt giống §10, khoảng bách phân vị) để giữ nguyên tắc gom cụm. Không biến nào vi phạm ⇒ mô hình chính giữ nguyên. Máy chạy: phan_tich_sap_bo_sung.py loại ppo.
- Cũ: vi phạm → partial proportional odds/generalized ordered logit, báo hệ số theo từng ranh giới cắt cho biến vi phạm.
- Mới: vi phạm (kiểm định Brant cho biến đó có p < 0,05, α §12) → partial proportional odds/generalized ordered logit (hệ số riêng từng ngưỡng cho biến vi phạm, các biến khác giữ hệ số chung; KTC 95% bằng bootstrap theo cụm bàn khám 1.000 lần, hạt giống §10), báo hệ số theo từng ranh giới cắt cho biến vi phạm.
