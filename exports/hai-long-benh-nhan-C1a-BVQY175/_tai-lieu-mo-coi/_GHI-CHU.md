# Tài liệu mồ côi — dời khỏi thư mục đề tài (02/09/2026)

Bốn file `.docx` sau được dời từ `exports/hai-long-benh-nhan-C1a-BVQY175/` vào đây,
theo phát hiện của `tools/kiem_chi_tiet_he_nghien_cuu.py` (vòng rà 4):

- `G6a_ANALYSIS_hai-long-benh-nhan-C1a-BVQY175.docx`
- `G6b_INTERPRETATION_hai-long-benh-nhan-C1a-BVQY175.docx`
- `G6d_CLINICAL-GUIDELINE_hai-long-benh-nhan-C1a-BVQY175.docx`
- `G9_READINESS_hai-long-benh-nhan-C1a-BVQY175.docx`

**Vì sao dời:** cả bốn nằm trong thư mục đề tài, mang tên trông như sản phẩm THẬT
của cổng G6/G9, nhưng **`G6_checkpoint.json` và `G9_checkpoint.json` không tồn tại** —
hai cổng đó chưa từng chạy trên đề tài này (đúng thực tế: G5 khoá dữ liệu chưa ký,
G6 phân tích không thể chạy trước khi có dữ liệu khoá). Một chủ nhiệm mở thư mục
có lý do để tin G6/G9 đã xong, trong khi:

- Ba file G6a/G6b/G6d nội dung 100% khung mẫu — không một chữ nào do người viết,
  chỉ có `[CẦN CHỦ NHIỆM XÁC NHẬN] Chủ nhiệm điền nội dung cho phần này.`
- File G9_READINESS mang kết luận **"NOT READY"** cho ba cổng cứng — nội dung có
  vẻ đúng thực tế (G2/G4/G9 quả thật CHƯA ĐÓNG) nhưng bộ sinh ra nó **không còn
  tồn tại trong repo hiện tại** (đã grep toàn bộ `tools/*.py`, không tìm thấy nơi
  nào sinh đúng tiêu đề "BÁO CÁO SẴN SÀNG NGHIỆM THU" này) — tức không tái lập
  được, không có dây kiểm liêm chính nào chạy qua nó.

**Không xoá — giữ truy vết** (cùng nguyên tắc `.bak-*` đã dùng cho rào chống đè
G0/G2/G4). Thư mục mang tiền tố `_` — quy ước NỘI BỘ mà `verify_exports_integrity.py`
(`INTERNAL_PREFIX`) đã dùng để loại file/khu vực này khỏi phạm vi kiểm tài liệu
nghiên cứu chính thức.

**Khi G6/G9 chạy THẬT** (sau khi G5 khoá dữ liệu và G8 bình duyệt), bộ sinh
`gen_research_docx.py --artifact analysis/interpretation/clinical-guideline` và
cổng G9 thật sẽ tạo bản MỚI đúng vị trí `exports/hai-long-benh-nhan-C1a-BVQY175/` —
không cần phục hồi các file trong thư mục này.

Cần bác sĩ kiểm chứng.
