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
  vẻ đúng thực tế (G2/G4/G9 quả thật CHƯA ĐÓNG). **ĐÍNH CHÍNH 02/09/2026** (bản
  ghi chú đầu tiên viết SAI ở đây): bộ sinh THẬT SỰ CÒN TỒN TẠI —
  `gen_research_docx.py::_gen_readiness()` (khoá `readiness` trong `ARTIFACT_MAP`,
  cổng "G9") sinh đúng tên file `G9_READINESS_<mã>.docx`. Grep lần đầu bị trượt vì
  tìm nhầm tiêu đề IN HOA (`"BÁO CÁO SẴN SÀNG NGHIỆM THU"`) trong khi mã nguồn
  lưu tiêu đề dạng chữ thường có hoa đầu câu. **Vấn đề thật, sau khi đọc hàm:**
  `_gen_readiness()` nhận tham số `content: dict` từ NGƯỜI GỌI — khi gọi mà KHÔNG
  truyền `dod`/`gaps`/`g2_status`/`g4_status`/`g9_status` thì nó tự rơi về mặc
  định `"NOT READY"` + `"🔴 CHƯA ĐÓNG"` cho cả ba cổng. Đã grep toàn repo: **không
  nơi nào tính các giá trị đó từ checkpoint/ledger thật rồi truyền vào** — tức
  file trên đĩa là kết quả của một lượt gọi KHÔNG kèm dữ liệu thật, không phải
  một bản đánh giá đã tính toán. Trùng hợp là mặc định đó khớp thực tế HÔM NAY,
  nhưng không có gì buộc nó cập nhật khi G2/G4/G9 đổi trạng thái — đây mới là lý
  do thật cần dời file, không phải vì "công cụ sinh nó đã biến mất".

**Không xoá — giữ truy vết** (cùng nguyên tắc `.bak-*` đã dùng cho rào chống đè
G0/G2/G4). Thư mục mang tiền tố `_` — quy ước NỘI BỘ mà `verify_exports_integrity.py`
(`INTERNAL_PREFIX`) đã dùng để loại file/khu vực này khỏi phạm vi kiểm tài liệu
nghiên cứu chính thức.

**Khi G6 chạy THẬT** (sau khi G5 khoá dữ liệu), gọi lại
`gen_research_docx.py --artifact analysis/interpretation/clinical-guideline
--content <file JSON có số liệu thật>` sẽ tạo bản MỚI đúng vị trí
`exports/hai-long-benh-nhan-C1a-BVQY175/` — không cần phục hồi các file ở đây.

**Riêng G9_READINESS: ĐÍNH CHÍNH thêm.** Cổng G9 THẬT (`run_g9_auto.py` →
`g9_quality_gate.write_readiness_template`) **KHÔNG** sinh file `.docx` này —
nó ghi `G9_PUBLICATION_READINESS.json` (tên hoàn toàn khác). File `.docx` chỉ
ra đời khi có người gọi TAY `gen_research_docx.py --artifact readiness`, và
KHÔNG công cụ nào trong repo tính sẵn `dod`/`gaps`/`g2_status`/`g4_status`/
`g9_status` từ checkpoint/ledger thật để truyền vào — đó là khoảng trống CHƯA
LẤP, ghi lại ở đây để không lặp lại việc tạo file rỗng như lần này. Muốn có
bản readiness `.docx` đáng tin, phải tự tính các giá trị đó (từ
`audit_research_gates.py`/`gate_contract.ledger_approved`) rồi truyền qua
`--content` — chưa có cầu nối tự động cho việc này.

Cần bác sĩ kiểm chứng.
