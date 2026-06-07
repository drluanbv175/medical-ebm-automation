"""Tự động hoá nội dung mạng xã hội (TikTok) từ pipeline EBM.

Mục tiêu: biến chứng cứ "mới/đáng tin" trong kho thành GÓI NỘI DUNG TikTok
(slideshow ảnh + caption + hashtag) để bác sĩ DUYỆT rồi tự đăng.

NGUYÊN TẮC LIÊM CHÍNH (bắt buộc, kế thừa từ pipeline):
- KHÔNG bịa số liệu, KHÔNG biến preprint/FAERS/nghiên cứu nhỏ thành khuyến cáo.
- Mọi "điểm chính" trên slide đều TRÍCH NGUYÊN VĂN từ abstract (qua extraction.py);
  bản tiếng Việt chỉ là DỊCH MÁY THAM KHẢO, luôn giữ kèm nguyên văn.
- Chỉ tài liệu đủ độ tin (tier A/B hoặc guideline/SR/RCT/cảnh báo chính thức) mới
  được dựng dưới dạng "khuyến cáo/cập nhật"; tài liệu yếu chỉ ở dạng "tin nhanh –
  chưa kết luận" và KHÔNG đăng mặc định.
- Mỗi bài luôn có dòng nguồn truy vết + khuyến cáo "tham khảo, không thay khám bệnh".
"""
from app.social.content import (build_manual_post, build_post,  # noqa: F401
                                eligible_for_post, POST_DISCLAIMER)
from app.social.package import (create_manual_video,  # noqa: F401
                                generate_manual_post, generate_tiktok_batch,
                                preview_manual)
