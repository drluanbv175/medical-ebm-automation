# Sổ thay đổi theo quyết định chủ nhiệm — yêu cầu N2_01 (quy tắc xác nhận bệnh thận mạn)

- Ngày: 22/11/2026
- Quyết định: bác sĩ chủ nhiệm duyệt áp NGUYÊN VĂN bốn đoạn thay thế, trả lời trong phiên Claude Code: «Áp cả 4 chỗ (Khuyến nghị)».
- Lý do: Hội đồng Khoa học máy (QC-HDKH-4.0, vòng 4) xếp N2_01 là «cần dữ kiện» vì dòng 359/398 nằm trong vùng SAP đã chốt. Câu chữ ở đó cho phép eGFR và UACR bất thường ở hai lần đo khác nhau, lệch với biến phái sinh `phan_loai_btm`/`egfr_thap_xn`/`alb_xn` chủ nhiệm duyệt 15/11/2026 và với Bảng 2.1. KDIGO 2024 (PMID 38490803), Bảng 1: tiêu chí «tồn tại tối thiểu 3 tháng»; Practice Point 1.1.3.2: không coi là mạn chỉ dựa vào một lần bất thường.
- Không đổi quyết định nào, không thêm số liệu hay trích dẫn. SAP chưa ký (G4 READY_FOR_SIGNATURE) nên đây là chỉnh câu chữ trước khi ký, không phải sửa đổi SAP sau ký.

## `DE_CUONG_NOP_HOI_DONG_btm-dtd2-ngoai-tru-BVQY175.md`

- SHA-256 trước: `2e30d9e31bfce1343d3714fd4578697107b68efa7d552c0aded4587496375b55`
- SHA-256 sau: `a85576f03972769e60042dc884cde8bfba7c7aafbd8a6593064679afb81c22f6`

### Dòng 359 (359a)

- Cũ: eGFR < 60 mL/phút/1,73 m² và/hoặc UACR ≥ 30 mg/g (3 mg/mmol), bất thường ở 2 lần đo cách nhau ít nhất 90 ngày; người chỉ có 1 lần bất thường được xếp nhóm “nghi bệnh thận mạn” và báo cáo riêng.
- Mới: có 2 kết quả eGFR < 60 mL/phút/1,73 m², hoặc 2 kết quả UACR ≥ 30 mg/g (3 mg/mmol), cách nhau ít nhất 90 ngày; hai lần bất thường phải cùng một dấu ấn. Người có ít nhất 1 kết quả bất thường nhưng chưa thoả điều kiện này, kể cả khi eGFR và UACR bất thường ở hai lần đo khác nhau, được xếp nhóm “nghi bệnh thận mạn” và báo cáo riêng.

### Dòng 359 (359b)

- Cũ: Mẫu số là người có đủ xét nghiệm để phân loại;
- Mới: Mẫu số là người có đủ xét nghiệm để phân loại, tức nhóm (1) đến (3) của quy tắc xếp nhóm ở Bảng 2.1 (mục 2.6.4);

### Dòng 398 (398)

- Cũ: người có đủ xét nghiệm để phân loại bệnh thận mạn.
- Mới: người có đủ xét nghiệm để phân loại bệnh thận mạn, tức nhóm (1) đến (3) của quy tắc xếp nhóm ở Bảng 2.1.

### Dòng 399 (399)

- Cũ: người có bệnh thận mạn theo xét nghiệm (đã xác nhận ở 2 lần đo).
- Mới: người có bệnh thận mạn xác nhận theo xét nghiệm, tức nhóm (1) của quy tắc xếp nhóm ở Bảng 2.1.

## `G4_A5_SAP_FINAL_btm-dtd2-ngoai-tru-BVQY175.md`

- SHA-256 trước: `48dd980381ed205feb489384d33f31a7dd239032f3c738d269e7a634284eb72e`
- SHA-256 sau: `55635964781cc824a29c6afa9db4ade15994f9e699f85f57c5c094595983c592`

### Dòng 61 (SAP61)

- Cũ: BTM xác nhận (eGFR < 60 hoặc UACR ≥ 30 mg/g ở 2 lần đo cách nhau từ 90 ngày), nghi BTM (chỉ một lần bất thường), không BTM;
- Mới: BTM xác nhận (2 kết quả eGFR < 60, hoặc 2 kết quả UACR ≥ 30 mg/g, cách nhau từ 90 ngày, tức `egfr_thap_xn` = 1 hoặc `alb_xn` = 1), nghi BTM (có ít nhất 1 kết quả eGFR < 60 hoặc UACR ≥ 30 mg/g nhưng chưa xác nhận, kể cả khi hai dấu ấn bất thường ở hai lần đo khác nhau), không BTM (đủ xét nghiệm, mọi kết quả trong giới hạn);

Cần bác sĩ kiểm chứng.
