#!/usr/bin/env python3
"""Căn cứ đạo đức/pháp lý dùng CHUNG cho đề nghị miễn thủ tục đồng thuận tham gia nghiên cứu.

Vì sao có tệp này (19/11/2026): hai bộ sinh `tools/run_g2_auto.py` (TÀI LIỆU 9 của gói G2) và
`tools/ho_so_hdd_bvqy175.py` (Đơn đề nghị miễn đồng thuận nộp Hội đồng Đạo đức BVQY175) cùng ghi cứng một căn cứ
SAI: «TT43/2024/TT-BYT Điều 15 · Helsinki (WMA, bản sửa 2024) §29». Đối chiếu nguồn chính thức cho thấy Điều 15
là chuyên gia tư vấn độc lập và §29 là sự ưng thuận (assent) của người không đủ năng lực — không điều nào nói về
miễn chấp thuận. Hai bộ sinh nay đọc CÙNG một hằng số ở đây, sửa một nơi là đúng cả hai.

Đã tự đối chiếu ngày 19/11/2026 (đọc trực tiếp, không trích từ trí nhớ):

- Tuyên bố Helsinki, bản thông qua tại Đại hội đồng WMA lần thứ 75, Helsinki, tháng 10/2024 — trang chính thức
  https://www.wma.net/policies-post/wma-declaration-of-helsinki/ :
  §24 (mục «Privacy and Confidentiality») — mọi biện pháp bảo vệ riêng tư và bảo mật thông tin cá nhân của người
  tham gia; §32 (mục «Free and Informed Consent») — chấp thuận cho việc thu thập, lưu trữ, sử dụng lại dữ liệu và
  vật liệu sinh học xác định được; khi chấp thuận là không thể hoặc không thực tế (impossible or impracticable)
  thì chỉ được tiến hành sau khi hội đồng đạo đức xem xét và chấp thuận. Chỉ §32 chứa cụm này.
  §29 — sự ưng thuận của người không đủ năng lực (KHÔNG phải căn cứ miễn).
- CIOMS 2016, «International Ethical Guidelines for Health-related Research Involving Humans» — bản PDF chính thức
  https://cioms.ch/wp-content/uploads/2017/01/WEB-CIOMS-EthicalGuidelines.pdf :
  Hướng dẫn 10 «Modifications and waivers of informed consent» (tr. 37–39) — hội đồng đạo đức có thể chấp thuận
  sửa đổi hoặc miễn khi đủ CẢ BA điều kiện: nghiên cứu không khả thi/không thực hiện được nếu không miễn; có giá
  trị xã hội quan trọng; nguy cơ không vượt mức tối thiểu. Hướng dẫn 12 «Collection, storage and use of data in
  health-related research» (tr. 47–52).
- Thông tư 43/2024/TT-BYT ngày 12/12/2024 (hiệu lực 01/02/2025) — nguyên văn tiếng Việt trên caselaw.vn, mã văn
  bản 413160 (https://caselaw.vn/van-ban-phap-luat/413160-thong-tu-so-43-2024-tt-byt-ngay-12-12-2024-cua-bo-truong
  -bo-y-te-quy-dinh-viec-thanh-lap-to-chuc-va-hoat-dong-cua-hoi-dong-dao-duc-trong-nghien-cuu-y-sinh-hoc — nối
  liền hai dòng), đối chiếu thêm bản dịch tiếng Anh của văn bản: Điều 7 «Quyền hạn của Hội đồng đạo đức»,
  khoản 1 điểm b — chấp thuận hoặc không chấp thuận việc miễn lấy bản cung cấp thông tin nghiên cứu và phiếu
  tình nguyện tham gia nghiên cứu; Điều 16 «Nguyên tắc hoạt động của Hội đồng đạo đức», khoản 6 — thẩm định
  theo quy trình rút gọn chỉ áp dụng cho nghiên cứu có nguy cơ tối thiểu; Điều 15 — chuyên gia tư vấn độc lập
  (KHÔNG phải căn cứ miễn).

Không tự đổi các câu dưới đây khi chưa đọc lại nguồn; văn bản hết hiệu lực/bị thay ⇒ ghi «[CẦN ĐỐI CHIẾU NGUYÊN
VĂN]» thay vì đoán số điều.
"""
from __future__ import annotations

NGAY_DOI_CHIEU = "19/11/2026"

#: Căn cứ đầy đủ — in vào Đơn đề nghị miễn thủ tục đồng thuận nộp Hội đồng.
CAN_CU_MIEN_DONG_THUAN = (
    "Tuyên bố Helsinki (Hiệp hội Y khoa Thế giới, bản sửa đổi tháng 10/2024) §32 (dữ liệu, vật liệu sinh học xác "
    "định được: khi không thể hoặc không thực tế xin chấp thuận, chỉ tiến hành sau khi hội đồng đạo đức xem xét và "
    "chấp thuận) và §24 (bảo vệ riêng tư, bảo mật thông tin cá nhân); CIOMS 2016, Hướng dẫn 10 (sửa đổi và miễn "
    "chấp thuận — đủ cả ba điều kiện) và Hướng dẫn 12 (thu thập, lưu trữ và sử dụng dữ liệu trong nghiên cứu liên "
    "quan đến sức khoẻ); Thông tư 43/2024/TT-BYT, Điều 7 khoản 1 điểm b (Hội đồng đạo đức chấp thuận việc miễn lấy "
    "bản cung cấp thông tin nghiên cứu và phiếu tình nguyện tham gia nghiên cứu)."
)

#: Cùng căn cứ cho VĂN BẢN NỘP Hội đồng (đề cương, đơn trong phụ lục): «đoạn 32» thay «§32» — luật K4 của đề cương nộp
#: coi «§» là ký hiệu nội bộ (21/11/2026; đề cương BTM viết tay theo cùng cách).
CAN_CU_MIEN_DONG_THUAN_VAN_BAN_NOP = CAN_CU_MIEN_DONG_THUAN.replace("§", "đoạn ")

#: Căn cứ rút gọn một dòng — dùng trong khối TÀI LIỆU 9 của gói G2.
CAN_CU_MIEN_DONG_THUAN_NGAN = (
    "Helsinki (WMA, bản sửa đổi 10/2024) §32 + §24 · CIOMS 2016 Hướng dẫn 10 (ba điều kiện) + Hướng dẫn 12 · "
    "TT43/2024/TT-BYT Điều 7 khoản 1 điểm b"
)

#: Thẩm định rút gọn (Phụ lục 10) — chỉ cho nghiên cứu nguy cơ tối thiểu.
CAN_CU_QUY_TRINH_RUT_GON = (
    "Thông tư 43/2024/TT-BYT, Điều 16 khoản 6: thẩm định theo quy trình rút gọn chỉ áp dụng cho nghiên cứu có nguy "
    "cơ tối thiểu"
)

#: Ba điều kiện của CIOMS 2016 Hướng dẫn 10 — (khoá JSON, nhãn in ra).
BA_DIEU_KIEN_CIOMS = (
    ("i_khong_kha_thi", "(i) Nghiên cứu không khả thi hoặc không thực hiện được nếu không miễn"),
    ("ii_gia_tri_xa_hoi", "(ii) Nghiên cứu có giá trị xã hội quan trọng"),
    ("iii_nguy_co_toi_thieu", "(iii) Nguy cơ không vượt mức tối thiểu đối với người tham gia và nhóm của họ"),
)

#: Dữ liệu xác định được KHÔNG tự động buộc lấy chấp thuận — đúng CIOMS 2016 Hướng dẫn 10 và Helsinki §32.
LUU_Y_DU_LIEU_XAC_DINH_DUOC = (
    "Có dữ liệu xác định được hoặc tái xác định được (dữ liệu giả danh hoá, còn bảng nối mã). Theo CIOMS 2016 "
    "Hướng dẫn 10 và Tuyên bố Helsinki 2024 §32, đây không phải lý do tự động buộc lấy chấp thuận: Hội đồng xét "
    "miễn theo ba điều kiện nêu trên, kèm các biện pháp bảo mật."
)

LUU_Y_TIEP_XUC_NGUOI_THAM_GIA = (
    "Có tiếp xúc trực tiếp người tham gia để thu dữ liệu mới — thông thường phải xin chấp thuận (có thể sửa đổi thủ "
    "tục); chỉ đề nghị miễn khi lập luận được điều kiện (i) — không khả thi nếu không miễn."
)

# ── Bảo vệ dữ liệu cá nhân trong kế hoạch quản lý dữ liệu (TÀI LIỆU 6 của gói G2) — 22/11/2026 ───────────────────────
# Hội đồng đề tài (vòng 22/11/2026, hai đề tài BVQY175) đọc nguyên văn:
# - Luật Bảo vệ dữ liệu cá nhân số 91/2025/QH15 (Công báo số 971+972 ngày 24/7/2025; hiệu lực 01/01/2026, Điều 38):
#   Điều 23 khoản 1 — thông báo cơ quan chuyên trách bảo vệ dữ liệu cá nhân chậm nhất 72 giờ kể từ khi phát hiện vi
#   phạm; bên xử lý báo kịp thời cho bên kiểm soát. Điều 3 khoản 3 — dữ liệu cá nhân «được lưu trữ trong khoảng thời
#   gian phù hợp với mục đích xử lý dữ liệu cá nhân, trừ trường hợp pháp luật có quy định khác» (câu chữ khoản 3 đối
#   chiếu thêm qua trích đoạn thuvienphapluat.vn ngày 22/11/2026).
# - Nghị định 356/2025/NĐ-CP (Công báo số 18 ngày 18/01/2026): Điều 28 — nội dung thông báo vi phạm.
# Khuôn cũ ghi «Theo NĐ 356/2025/NĐ-CP Điều 23: báo cáo nội bộ trong 24 giờ · thông báo cơ quan trong 72 giờ · thông
# báo người tham gia ngay» là SAI: Điều 23 của Nghị định là trách nhiệm tổ chức kinh doanh dịch vụ xử lý dữ liệu; mốc
# 72 giờ nằm ở Điều 23 khoản 1 của LUẬT; «24 giờ nội bộ» và «thông báo người tham gia ngay» không có trong hai văn bản.

#: Hạn thông báo cơ quan chuyên trách khi có vi phạm.
HAN_THONG_BAO_VI_PHAM = (
    "Thông báo cơ quan chuyên trách bảo vệ dữ liệu cá nhân chậm nhất 72 giờ kể từ khi phát hiện "
    "(Luật 91/2025/QH15, Điều 23 khoản 1)"
)
#: Nơi quy định nội dung thông báo vi phạm.
NOI_DUNG_THONG_BAO_VI_PHAM = "nội dung thông báo theo Nghị định 356/2025/NĐ-CP, Điều 28"
#: Căn cứ cho thời hạn lưu trữ đã chốt của đề tài.
CAN_CU_THOI_HAN_LUU = "chỉ lưu trong thời gian phù hợp với mục đích xử lý — Luật 91/2025/QH15, Điều 3 khoản 3"
#: Căn cứ SAI cho lưu trữ đã từng ghi cứng: Thông tư 38/2018/TT-BYT là thông tư hướng dẫn công tác thi đua, khen
#: thưởng ngành y tế (hội đồng tra ngày 22/11/2026), không quy định thời hạn lưu trữ hồ sơ hay dữ liệu nghiên cứu.
DAU_HIEU_CAN_CU_LUU_TRU_SAI = ("TT38/2018", "38/2018/TT-BYT")
#: Căn cứ SAI cho thông báo vi phạm đã từng ghi cứng (Điều 23 của Nghị định 356, không phải của Luật 91).
DAU_HIEU_CAN_CU_VI_PHAM_SAI = ("NĐ 356/2025/NĐ-CP Điều 23", "NĐ 356 Điều 23", "72 giờ theo NĐ 356")

# Chuỗi căn cứ SAI đã từng ghi cứng — dùng để nhận diện và thay khi nâng cấp hồ sơ cũ.
DAU_HIEU_CAN_CU_SAI = ("Điều 15", "§29", "§ 29")


def can_cu_sai(van_ban: str) -> bool:
    """True khi chuỗi căn cứ còn mang số điều SAI đã biết (TT43 Điều 15 hoặc Helsinki §29)."""
    return any(d in (van_ban or "") for d in DAU_HIEU_CAN_CU_SAI)


def can_cu_du_lieu_sai(van_ban: str) -> list:
    """Các căn cứ SAI đã biết về lưu trữ (TT38/2018) và thông báo vi phạm (NĐ 356 Điều 23) còn trong văn bản."""
    return [d for d in DAU_HIEU_CAN_CU_LUU_TRU_SAI + DAU_HIEU_CAN_CU_VI_PHAM_SAI if d in (van_ban or "")]
