# _CAU-HOI-AN-TOAN-BAT-BUOC — Bảng câu hỏi an toàn BẮT BUỘC theo bối cảnh

> **Nguồn chung (single source of truth)** cho vòng tự sửa "thiếu câu hỏi an toàn".
> Được đọc bởi (vòng thực thi chính): `sang-loc-co-do` (HỎI ở Bước 0) · `ke-don-an-toan` (CHẶN kê khi chưa hỏi) ·
> `tham-dinh-dau-ra` (KIỂM gói đã hỏi chưa → 🔴 TRẢ-VỀ-SỬA nếu thiếu).
> Tham chiếu thêm (nhánh chuyên biệt tự nối `sang-loc-co-do`/`tham-dinh-dau-ra` + tài liệu taxonomy/rubric
> đồng bộ CLIN-SAFETYQ từ bảng này): `dau-man-tinh` · `quan-ly-khang-dong` · `tram-cam-lo-au` ·
> `dieu-phoi-lam-sang` · `so-cai-ghi-nho` · `_LESSONS-LEDGER-TAXONOMY.md` · `_RUBRIC-EVALUATE-CUNG-QA-GATE.md`.
> Danh sách tay — LUÔN xác nhận bằng `grep -l _CAU-HOI-AN-TOAN-BAT-BUOC *.md` trước khi sửa dòng kích hoạt,
> đừng chỉ tin danh sách này (đã lệch thực tế một lần, vá 2026-07-11).
> Cập nhật 2026-07-11. Mở rộng = thêm DÒNG vào bảng (không sửa cấu trúc agent).

## Nguyên tắc
- Khi **bệnh cảnh của ca khớp một DÒNG KÍCH HOẠT**, hệ thống PHẢI hỏi & ghi nhận **câu hỏi an toàn tương ứng** **TRƯỚC KHI kê đơn / kết luận áp dụng**.
- Thiếu → guardrail `tham-dinh-dau-ra` chấm **🔴** (gắn vào Q3 Đầy đủ và/hoặc Q5 Nguy cơ hại) → **TRẢ-VỀ-SỬA**, kèm dòng `INSTRUCTION BỔ SUNG → …` để nhạc trưởng chèn vào prompt chạy lại sub-agent.
- KHÔNG bịa ngưỡng/thang điểm — chỉ dùng công cụ đã công nhận, ghi nguồn khi có. KHÔNG PII.
- Đây là bước AN TOÀN, **không thay khám chuyên khoa**; rào cứng cuối vẫn là bác sĩ duyệt (Cổng A).

## Bảng kích hoạt → câu hỏi an toàn bắt buộc

| # | Dòng KÍCH HOẠT (bệnh cảnh/yêu cầu) | CÂU HỎI AN TOÀN BẮT BUỘC (trước khi kê/kết luận) | Nếu DƯƠNG TÍNH → |
|---|---|---|---|
| S1 | **Mất ngủ** · cảm giác **thất bại/vô vọng** · **yêu cầu thuốc ngủ mạnh** (benzodiazepine, "Z-drug" liều cao) | **HỎI Ý TƯỞNG TỰ SÁT** (PHQ-9 mục 9 / C-SSRS rút gọn: ý tưởng → ý định → kế hoạch → phương tiện) | KHÔNG kê benzo/Z-drug **số lượng lớn**; chuyển/hội chẩn **tâm thần**; hạn chế tiếp cận phương tiện; nếu buộc dùng thì kê **lượng nhỏ**, hẹn theo dõi gần. |
| S2 | **Kê thuốc nhóm GÂY QUÁI THAI/ĐỘC THAI** cho **phụ nữ tuổi sinh đẻ / không loại trừ mang thai** (nhóm điển hình: ACEi/ARB · valproate & nhiều thuốc chống động kinh · isotretinoin/retinoid · warfarin · methotrexate · mycophenolate · thalidomide · lithium · misoprostol · methimazole · tetracycline · NSAID tam cá nguyệt 3 — danh mục+nguồn ở `ke-don-an-toan.md` mục thai kỳ) | **HỎI & GHI NHẬN khả năng có thai + biện pháp tránh thai** trước khi kê (kỳ kinh cuối · đang tránh thai? · cần thử thai?) | **KHÔNG kê** thuốc nhóm đó nếu có thai/không loại trừ → **thay thế an toàn có nguồn**, hoặc **hoãn + xác nhận (thử thai)**; thuốc có chương trình bắt buộc (isotretinoin/thalidomide) → **tránh thai kép + thử thai định kỳ**. Mức nguy cơ/thay thế CHỈ nêu khi có nguồn (FDA-PLLR·ACOG·guideline từng thuốc); chưa chắc → `[CẦN KIỂM CHỨNG]`. |

> **Khung mở rộng (chờ bác sĩ thêm dòng — KHÔNG tự bịa):** ví dụ có thể bổ sung khi bác sĩ xác nhận —
> đau ngực/khó thở cấp → hỏi **yếu tố nguy cơ ACS/thuyên tắc phổi**; v.v.
> *(Chỉ thêm dòng có cơ sở guideline; ghi nguồn. S1 (tự sát) chốt 2026-06-14; **S2 (thai kỳ + thuốc gây quái thai) bổ sung 2026-06-20** theo cho phép của bác sĩ — neo FDA-PLLR/ACOG/guideline từng thuốc.)*

## Liên kết
- Quy tắc gốc: bộ nhớ `feedback-mat-ngu-sang-loc-tu-sat`.
- Guardrail 2 lớp: `tham-dinh-dau-ra.md` (Q3/Q5) + `_CHUAN-CHAT-LUONG-MEDPALM.md`.
- Học bền (Tầng 2): `so-cai-ghi-nho` append `LEDGER_LESSONS.jsonl` mã `CLIN-SAFETYQ` khi guardrail
  bắt được lỗi loại này (cơ chế cụ thể: `_LESSONS-LEDGER-TAXONOMY.md` §2 + `so-cai-ghi-nho.md` §3c,
  vá 2026-07-08).
