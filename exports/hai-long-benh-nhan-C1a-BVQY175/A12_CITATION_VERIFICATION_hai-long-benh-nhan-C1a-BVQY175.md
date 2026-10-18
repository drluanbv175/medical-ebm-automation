# A12 — Kiểm chứng trích dẫn — hai-long-benh-nhan-C1a-BVQY175

> Phạm vi: mọi PMID và DOI trong `DE_CUONG_THONG_NHAT_hai-long-benh-nhan-C1a-BVQY175.md` (bản lắp G10 ngày 2026-10-14, mục đích ETHICS_SUBMISSION).
> Người kiểm: Claude (agent, vai kiem-chung-trich-dan, làm trực tiếp trong phiên) — ngày 2026-10-14. Không thay đọc toàn văn của PI.

## 1. Bằng chứng máy-kiểm

| Bước | Công cụ | Kết quả |
|---|---|---|
| Rút bài + metadata 9 PMID | `tools/check_citations.py --study hai-long-benh-nhan-C1a-BVQY175` (PubMed efetch) | mã 0; `A12_RETRACTION_RECEIPT.json` all_clean=true (2026-10-14T13:42:42Z); `A12_METADATA_RECEIPT.json` all_resolved=true |
| 9 DOI tạp chí trong nước (không có PMID) | `app.sources.crossref_retraction.CrossrefRetraction.check` (Crossref) | 9/9 tồn tại, trạng thái ok — không có quan hệ rút/đính chính (updated-by) |

Retraction Watch ngoại tuyến không được nạp trên máy ở lượt này; lượt kiểm 2026-10-11 (tổng hợp G0-T3) đã ghi 9/9 DOI không có bản ghi Retraction Watch.

## 2. Đối chiếu nội dung — PMID (đọc tiêu đề + tóm tắt, chưa đọc toàn văn)

| PMID | Bài (metadata PubMed) | Câu dẫn trong đề cương | Đối chiếu |
|---|---|---|---|
| 28690831 | Thời gian chờ ngoại trú tại một bệnh viện ngoại khoa trung ương, dữ liệu phần mềm quản lý bệnh viện | Thời gian chờ đo từ phần mềm quản lý bệnh viện ở quy mô lớn (danh mục tham khảo) | ✅ khớp |
| 31703089 | Hài lòng với dịch vụ HIV ngoại trú tại Việt Nam (n=1133) | Thời gian chờ và thủ tục lặp lại là lĩnh vực hài lòng thấp nhất | ✅ khớp (lĩnh vực chất lượng–thuận tiện: chờ, thủ tục — tỷ lệ hoàn toàn hài lòng thấp nhất) |
| 32584904 | Hài lòng người bệnh tim mạch, Bệnh viện Tim Hà Nội (n=600) | Thời gian chờ là lĩnh vực thấp nhất; chiều BHYT ngược với 36439278 và 42625778 | ✅ khớp (ngoại trú: «thời gian chờ» điểm thấp nhất; không BHYT hài lòng cao hơn) |
| 34017606 | Hài lòng ngoại trú tuyến cơ sở, khảo sát quốc gia 2015 (n=4372) | Thời gian chờ dài hơn đi kèm hài lòng thấp hơn | ✅ khớp (đã hiệu chỉnh, chờ lâu hơn ít khả năng hài lòng hơn) |
| 34445940 | Hài lòng tại 3 bệnh viện Hà Nội (n=108) | Người ở tỉnh khác và nhóm dùng dịch vụ theo yêu cầu có xu hướng hài lòng thấp hơn | ✅ khớp (đề cương đã nêu mẫu nhỏ) |
| 36439278 | Hài lòng tại một phòng khám đa khoa Hà Nội (n=301) | Chiều liên quan của BHYT không nhất quán | ✅ khớp (có BHYT hài lòng cao hơn, OR 3,5) |
| 39944421 | Hài lòng ngoại trú tại bệnh viện tuyến ba, Andaman và Nicobar (n=1298) | Thời gian chờ dài hơn đi kèm hài lòng thấp hơn, khá nhất quán | 🟠 ủng hộ một phần — tóm tắt có kiểm định chi bình phương giữa hài lòng và thời gian chờ, kết luận thời gian chờ là điểm cần cải thiện, nhưng KHÔNG nêu chiều/độ lớn của liên quan; bối cảnh khác (Ấn Độ). Đề nghị PI: giữ kèm nhãn bối cảnh, hoặc chuyển bài này sang câu «thời gian chờ là điểm cần cải thiện» |
| 40295132 | Hài lòng tại 5 cơ sở chăm sóc ban đầu, Sierra Leone (n=290) | Thời gian chờ liên quan nghịch với hài lòng; học vấn AOR 0,53 (KTC 95% 0,28–0,98) | ✅ khớp (số chép đúng tóm tắt: học vấn AOR 0,53; thời gian chờ AOR 0,41) |
| 42625778 | Bộ phiếu chuẩn quốc gia 2024, 5 cơ sở (n=2500) | Có BHYT, cư trú nông thôn, tái khám nhiều lần đi kèm hài lòng cao hơn | ✅ khớp |

## 3. Đối chiếu — DOI tạp chí trong nước (Crossref 2026-10-14)

| DOI | Tiêu đề (Crossref, rút gọn) | Trạng thái |
|---|---|---|
| 10.38148/jhds.0706skpt23-064 | Đánh giá sự hài lòng của người bệnh khám ngoại trú tại khoa khám bệnh… | ✅ tồn tại, không rút |
| 10.51298/vmj.v540i1.10302 | Một số yếu tố liên quan đến sự hài lòng của người bệnh về dịch vụ khám… | ✅ tồn tại, không rút |
| 10.51298/vmj.v549i2.13771 | Khảo sát sự hài lòng người bệnh ngoại trú tại khu khám bệnh AB… | ✅ tồn tại, không rút |
| 10.51403/0868-2836/2021/78 | Sự hài lòng của người bệnh về chất lượng dịch vụ y tế tại Khoa Y học cổ truyền… | ✅ tồn tại, không rút |
| 10.52163/yhc.v64i1.573 | Sự hài lòng và mối liên quan của người bệnh đến khám bệnh tại khoa khám… | ✅ tồn tại, không rút |
| 10.52163/yhc.v64i6.841 | Sự hài lòng của người bệnh với chất lượng dịch vụ theo yêu cầu… | ✅ tồn tại, không rút |
| 10.52163/yhc.v66i1.1940 | Hài lòng người bệnh về dịch vụ đông y tại Khoa Y học cổ truyền… | ✅ tồn tại, không rút |
| 10.52163/yhc.v67i7.5934 | Thực trạng thời gian chờ khám bệnh và sự hài lòng của người bệnh… | ✅ tồn tại, không rút |
| 10.52163/yhc.v67icd5.5018 | Đánh giá hiệu quả của hệ thống đăng ký khám bệnh trực tuyến… | ✅ tồn tại, không rút |

Nội dung các DOI trong nước đã được đối chiếu ở tổng hợp G0-T3 (2026-10-11, tiêu đề + tóm tắt Crossref).

## 3b. Kiểm rút bài qua DOI không có PMID (Crossref `updated-by` + Retraction Watch ngoại tuyến, 2026-10-17)

Bộ kiểm rút bài máy-kiểm (`check_citation_retraction.py`) chỉ nhận PMID; cảnh báo cổng A12 đòi tra riêng các DOI không có
PMID song song. Đã tra bằng `app/sources/crossref_retraction.CrossrefRetraction` (siêu dữ liệu nhà xuất bản, quan hệ
`updated-by`) và chỉ mục Retraction Watch ngoại tuyến (62.707 DOI có phán quyết).

| DOI | Tiêu đề (Crossref, rút gọn) | Dùng ở | Crossref | Retraction Watch |
|---|---|---|---|---|
| 10.1002/9780470316696 | Multiple Imputation for Nonresponse in Surveys… | đề cương TLTK 49 (sách) | tồn tại, không có thông báo rút | không có bản ghi |
| 10.1093/ije/dyl129 | Sample size for cluster randomized trials: effect of coefficient of va… | G3, SAP §3/§12, đề cương 4.4 | tồn tại, không có thông báo rút | không có bản ghi |
| 10.1093/jssam/smv024 | Evaluating Confidence Interval Methods for Binomial Proportions in Clu… | SAP §3 | tồn tại, không có thông báo rút | không có bản ghi |
| 10.18637/jss.v009.i08 | Analysis of Complex Survey Samples… | SAP §4 | tồn tại, không có thông báo rút | không có bản ghi |
| 10.3368/jhr.50.2.301 | What Are We Weighting For?… | SAP §4 | tồn tại, không có thông báo rút | không có bản ghi |
| 10.38148/jhds.0706skpt23-064 | Đánh giá sự hài lòng của người bệnh khám ngoại trú tại khoa khám bệnh… | đề cương TLTK (tạp chí trong nước) | tồn tại, không có thông báo rút | không có bản ghi |
| 10.51298/vmj.v540i1.10302 | MỘT SỐ YẾU TỐ LIÊN QUAN ĐẾN SỰ HÀI LÒNG CỦA NGƯỜI BỆNH VỀ DỊCH VỤ KHÁM… | đề cương TLTK (tạp chí trong nước) | tồn tại, không có thông báo rút | không có bản ghi |
| 10.51298/vmj.v549i2.13771 | KHẢO SÁT SỰ HÀI LÒNG NGƯỜI BỆNH NGOẠI TRÚ TẠI KHU KHÁM BỆNH AB – KHOA… | đề cương TLTK (tạp chí trong nước) | tồn tại, không có thông báo rút | không có bản ghi |
| 10.51403/0868-2836/2021/78 | Sự hài lòng của người bệnh về chất lượng dịch vụ y tế tại Khoa Y học c… | đề cương TLTK (tạp chí trong nước) | tồn tại, không có thông báo rút | không có bản ghi |
| 10.52163/yhc.v64i1.573 | SỰ HÀI LÒNG VÀ MỐI LIÊN QUAN CỦA NGƯỜI BỆNH ĐẾN KHÁM BỆNH TẠI KHOA KHÁ… | đề cương TLTK (tạp chí trong nước) | tồn tại, không có thông báo rút | không có bản ghi |
| 10.52163/yhc.v64i6.841 | SỰ HÀI LÒNG CỦA NGƯỜI BỆNH VỚI CHẤT LƯỢNG DỊCH VỤ THEO YÊU CẦU TẠI KHO… | đề cương TLTK (tạp chí trong nước) | tồn tại, không có thông báo rút | không có bản ghi |
| 10.52163/yhc.v66i1.1940 | 36. HÀI LÒNG NGƯỜI BỆNH VỀ DỊCH VỤ ĐÔNG Y TẠI KHOA Y HỌC CỔ TRUYỀN BỆ… | đề cương TLTK (tạp chí trong nước) | tồn tại, không có thông báo rút | không có bản ghi |
| 10.52163/yhc.v67i7.5934 | THỰC TRẠNG THỜI GIAN CHỜ KHÁM BỆNH VÀ SỰ HÀI LÒNG CỦA NGƯỜI BỆNH TẠI K… | đề cương TLTK (tạp chí trong nước) | tồn tại, không có thông báo rút | không có bản ghi |
| 10.52163/yhc.v67icd5.5018 | ĐÁNH GIÁ HIỆU QUẢ CỦA HỆ THỐNG ĐĂNG KÝ KHÁM BỆNH TRỰC TUYẾN TẠI KHOA K… | đề cương TLTK (tạp chí trong nước) | tồn tại, không có thông báo rút | không có bản ghi |
| 10.1080/10705519909540118 | Cutoff criteria for fit indexes in covariance structure analysis… | đề cương 4.5.3 mục 4 (ngưỡng CFA), TLTK 45 | tồn tại, không có thông báo rút | không có bản ghi |
| 10.1037/0033-2909.88.3.588 | Significance tests and goodness of fit in the analysis of covariance structures | đề cương 4.5.3 mục 4 (ngưỡng CFA), TLTK 46 | tồn tại, không có thông báo rút | không có bản ghi |
| 10.1177/0049124192021002005 | Alternative Ways of Assessing Model Fit | đề cương 4.5.3 mục 4 (ngưỡng CFA), TLTK 47 | tồn tại, không có thông báo rút | không có bản ghi |

Ba DOI mới của SAP 1.2 đã được thẩm định độc lập (`tham-dinh-dau-ra`, 17/10/2026) đối chiếu nội dung: mỗi nguồn
ủng hộ đúng mệnh đề gắn với nó (Dean & Pagano qua tóm tắt; Lumley 2004 qua toàn văn mục 2.3, 3, 5.1.2; Solon và cộng
sự 2015 qua tóm tắt).

Ba DOI ngưỡng CFA (TLTK 45–47, thêm vào đề cương nộp ngày 18/10/2026 theo góp ý hội đồng G10) tra ngày 18/10/2026 theo tranh biện `G10-TB-20261018T074752-4af4efab` (việc 5): Crossref `updated-by` trả «ok» cho cả ba, chỉ mục Retraction Watch ngoại tuyến (tải 27 ngày trước, 62.707 DOI) không có bản ghi; bộ chuyển định danh NCBI không trả PMID nên chúng nằm ở bảng này. Tiêu đề Crossref khớp tiêu đề trong danh mục TLTK. Nội dung: mệnh đề gắn với nguồn là các ngưỡng phù hợp mô hình — chưa đối chiếu toàn văn, cần bác sĩ kiểm chứng.

## 4. Việc còn lại cho PI (không chặn A12)

- 🟡 Danh mục tài liệu tham khảo của đề cương thống nhất còn ghi «[CẦN BỔ SUNG] (định dạng Vancouver đầy đủ)» ở các mục PMID — metadata đầy đủ đã có trong `A12_METADATA_RECEIPT.json`; định dạng Vancouver là việc trình bày, không phải tính có thật của trích dẫn.
- 🟠 PMID 39944421 — xem mục 2.

KẾT QUẢ CỔNG A12: ĐÃ XÁC MINH TOÀN BỘ TRÍCH DẪN

Cần bác sĩ kiểm chứng.
