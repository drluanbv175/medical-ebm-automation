# Gói tìm bổ sung G0 theo PRISMA-S — hai-long-benh-nhan-C1a-BVQY175

> Việc 2 của biên bản tranh biện BD-G0-T2 (hội đồng G0, `hoi_dong/G0/G0-TB-20261007T192719-bb46520a.json`).
> Agent soạn (2026-10-14), không phải tổng quan hệ thống. Chuỗi PubMed để PI CHỌN ở việc 4; agent không tự chạy lại G0.

## 1. Cơ sở dữ liệu, giao diện, ngày tra

| Nguồn | Giao diện | Ngày tra | Ghi chú |
|---|---|---|---|
| Europe PMC | REST `search` qua `app.sources.europepmc` | 2026-10-14 | 3 nhánh dưới đây |
| Crossref | REST `works` qua `app.sources.crossref` (100 bản ghi/truy vấn) | 2026-10-14 | y văn trong nước có DOI |
| PubMed | E-utilities | **KHÔNG tra được** | NCBI misuse-chặn IP mạng này (13–14/10); nhánh PubMed chạy ở việc 4 khi PI chọn chuỗi |

## 2. Chuỗi tìm và số hit (Europe PMC, không giới hạn năm, không lọc thiết kế trừ khi ghi rõ)

| Nhánh | Chuỗi | Số hit |
|---|---|---|
| EPMC-1 rộng, không lọc thiết kế | `(satisfaction OR "patient experience") AND (outpatient* OR ambulatory OR "out-patient") AND (Vietnam OR "Viet Nam")` | 1819 |
| EPMC-2 + theo yêu cầu/trả phí | EPMC-1 `AND ("on-demand" OR "on demand" OR "fee-for-service" OR "self-pay" OR "private" OR "VIP" OR "service on request")` | 1180 |
| EPMC-3 + quân y | EPMC-1 `AND ("military hospital" OR "army hospital" OR military) NOT veteran*` | 158 |

Crossref (y văn trong nước): `hài lòng người bệnh ngoại trú khám bệnh theo yêu cầu` · `sự hài lòng người bệnh bệnh viện quân y` · `patient satisfaction outpatient Vietnam on-demand`.

## 3. Recall với bài mốc (biên bản BD-G0-T2 liệt kê)

| Bài mốc | EPMC-1 | EPMC-2 | EPMC-3 | Có trong danh mục đọc G0 | Ghi chú |
|---|---|---|---|---|---|
| PMID 36292392 | ✓ | ✓ | — | có | |
| PMID 28690831 | ✓ | — | ✓ | có | |
| PMID 34017606 | ✓ | — | — | có | |
| PMID 32946537 | ✓ | ✓ | — | **chưa** | Hài lòng NỘI TRÚ toàn quốc (10.143 NB, 69 BV; PLoS One 2020) ⇒ đề xuất nhãn **gián tiếp** |
| PMID 40432693 | ✓ | ✓ | ✓ | **chưa** | Hài lòng dịch vụ DƯỢC tại BV TƯQĐ 108, có xây dựng bộ câu hỏi (2025) ⇒ đề xuất nhãn **gián tiếp** |

- Recall nhánh rộng EPMC-1: **5/5** bài mốc. Hai bài chưa có trong danh mục vì truy vấn G0 ngày 2026-07-31 chỉ nhắm NGOẠI TRÚ.
- Crossref: 3 truy vấn tìm ra **7/9** DOI trong nước của danh mục đọc; chưa thấy `10.52163/yhc.v66i1.1940` và `10.52163/yhc.v67icd5.5018` (cả hai có trong danh mục nhờ hội đồng giao) ⇒ truy vấn Crossref theo từ khoá chưa đủ, tra trong nước phải giữ bước tra tay.

## 4. Nguồn KHÔNG tra (để PI tra theo đề cương)

Thư viện luận văn/luận án trong nước, kỷ yếu hội nghị, tạp chí không có DOI, văn bản Bộ Y tế ngoài trang công khai, WHO ICTRP (PI đã tra ngày chốt G0), ProQuest/Scopus/Web of Science (điều khoản tài khoản — không cho máy tra).

## 5. Đề xuất cho PI (việc 4 — PI quyết, agent không tự chạy)

1. Thêm PMID 32946537 và 40432693 vào danh mục đọc với nhãn «gián tiếp» khi chạy lại G0.
2. Chuỗi PubMed để PI chọn (ghi vào `study_meta.query_en`, rồi chạy `run_g0_auto.py` MỘT lần khi NCBI gỡ chặn):
   `("Patient Satisfaction"[Mesh] OR satisf*[tiab] OR "patient experience"[tiab]) AND ("Outpatients"[Mesh] OR "Ambulatory Care"[Mesh] OR outpatient*[tiab] OR ambulatory[tiab]) AND ("Vietnam"[Mesh] OR vietnam*[tiab] OR "viet nam"[tiab])`
   — bộ sinh nay tự chạy thêm nhánh KHÔNG lọc thiết kế (PR #128) để đối chiếu recall.
3. Chạy lại sẽ đổi tập PMID ⇒ dấu vân tay G0 đổi ⇒ PI chốt lại G0 (nút «Chot G0 C1a», chế độ chốt lại nhanh).

Kiểm rút bài: PMID trong bảng 3 chưa kiểm lại hôm nay (NCBI chặn; bản trước đã kiểm khi lập danh mục G0) — sẽ kiểm ở A12.

Cần bác sĩ kiểm chứng.
