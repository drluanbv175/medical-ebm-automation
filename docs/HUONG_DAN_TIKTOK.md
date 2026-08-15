# Hướng dẫn: Tạo nội dung TikTok từ chứng cứ EBM

Hệ thống tự biến các chứng cứ trong kho thành **gói bài đăng TikTok**
(slideshow ảnh dọc + caption + hashtag) để bác sĩ **DUYỆT rồi tự đăng**.
Không dùng TikTok API, không tự đăng — luôn có người kiểm trước khi public.

## Cách dùng nhanh nhất (qua Dashboard)

1. Mở app **Dashboard EBM** (hoặc `~/.ebm-venv/bin/python run.py dashboard`).
2. Vào tab **📱 10. TikTok**.
3. Chọn số bài → bấm **🎬 Tạo gói nội dung TikTok**.
4. Mỗi bài hiện ra: ảnh slide đầu + ô **caption** (bấm góc phải để sao chép) +
   nút **⬇️ tải từng ảnh**.
5. Trên điện thoại: mở TikTok → **đăng ảnh (photo mode)** → chọn các ảnh đã tải
   theo thứ tự slide_01, 02, 03… → dán caption → đăng.

> ⚠️ **Hãy đọc kỹ và tự chịu trách nhiệm chuyên môn trước khi đăng.** Nội dung là
> bản nháp tự sinh từ chứng cứ, mang tính tham khảo.

## Video có giọng đọc tiếng Việt (tuỳ chọn)

Ngoài slideshow ảnh, hệ thống có thể dựng luôn **video dọc 1080×1920 có giọng
đọc tiếng Việt** (mỗi slide hiện đúng lúc đọc). Dùng:
- **Dashboard**: tích ô **🎬 Tạo cả video (giọng đọc)** trước khi bấm tạo. Sau đó
  trong mỗi bài có sẵn trình phát + nút **⬇️ Tải video.mp4** để đăng thẳng lên TikTok.
- **Dòng lệnh**: `~/.ebm-venv/bin/python run.py tiktok-video 5`

Công cụ dùng đều **offline, không cần cài thêm gì**:
- Giọng đọc: giọng **Linh (vi_VN)** có sẵn trong macOS (`say`).
- Ghép video: `ffmpeg` đi kèm trong gói `imageio-ffmpeg` (đã cài trong môi trường).

Nếu chạy trên máy không phải macOS (thiếu giọng `say`) thì ô video sẽ tự khoá và
hệ thống vẫn xuất slideshow + caption bình thường.

## Phong cách "bảng trắng viết tay" + giọng mềm

Có 2 phong cách (chọn ở ô **Phong cách** trong dashboard, hoặc lệnh riêng):
- **Lâm sàng (nền tối)** — gọn, chuyên nghiệp (mặc định).
- **Bảng trắng viết tay (giọng mềm)** — nền giấy trắng, chữ viết tay (Brush Script +
  Chalkboard), nét vẽ tay (gạch chân lượn sóng, bút dạ quang, mũi tên), video có
  **chuyển động mềm** (zoom chậm + mờ dần) và **giọng nữ HoaiMy** dịu, tự nhiên.

```bash
~/.ebm-venv/bin/python run.py tiktok-whiteboard 3   # video bảng trắng + giọng mềm
```

> Giọng mềm (HoaiMy) dùng **edge-tts** nên **cần mạng** lúc dựng. Mất mạng sẽ tự lùi
> về giọng máy Linh (offline). Đổi giọng/tốc độ trong `.env`:
> `TIKTOK_EDGE_VOICE=vi-VN-NamMinhNeural` (nam), `TIKTOK_EDGE_RATE=-12%` (chậm hơn).

**Doodle y khoa tự chèn:** hệ thống có sẵn ~24 hình vẽ tay (tim, ECG, thận, phổi,
não, gan, xương, viên thuốc, ống tiêm, vi khuẩn, ống nghe, biểu đồ, kính lúp, dấu
hỏi, cảnh báo, checklist, đồng hồ, khiên, bóng đèn, lịch…) và **tự chọn 1–2 hình
hợp chủ đề** (theo chuyên khoa + từ khoá tiêu đề) chèn lên slide. Ví dụ "Tim mạch"
→ tim + nhịp ECG; tiêu đề có "chi phí" → biểu đồ cột; "nguy cơ" → tam giác cảnh báo.

## ✍️ Tự soạn nội dung → XEM TRƯỚC → sửa → tạo video

Trong tab 📱 10. TikTok có mục **"Tự soạn nội dung → XEM TRƯỚC rồi tạo video"**,
làm theo **2 bước** (xem trước trước khi tạo):
1. Nhập **Tiêu đề**, chọn **Chuyên khoa** (để chọn doodle), gõ **Nội dung**, chọn
   phong cách → bấm **👁️ Xem trước (ảnh + lời đọc)**.
   - Quy ước nội dung: **một dòng trống = sang slide mới**; trong mỗi đoạn, **dòng
     đầu là tiêu đề slide**, các dòng sau là các ý.
2. Xem **ảnh slide** + **lời đọc từng slide** hệ thống đề xuất. **Sửa lời đọc** cho
   suôn/ngắt nghỉ đúng ý (mỗi dấu chấm = một nhịp nghỉ). Muốn đổi slide thì sửa nội
   dung ở trên rồi bấm *Xem trước* lại.
3. Bấm **🎥 Tạo video** → xem trước video, tải về đăng.

**Giọng đọc đã được làm suôn hơn:** mỗi ý là một câu có dấu chấm để giọng neural
ngắt nghỉ tự nhiên; tự đọc "135/85" thành "135 trên 85", bỏ ký hiệu khó đọc.

Ví dụ nội dung:
```
Vì sao đo huyết áp tại nhà?
Phản ánh đúng huyết áp thường ngày
Tránh tăng huyết áp áo choàng trắng

Đo thế nào cho đúng?
Ngồi nghỉ 5 phút trước khi đo
Đo 2 lần cách nhau 1-2 phút, lấy trung bình
```
> Nội dung tự soạn do bác tự chịu trách nhiệm chuyên môn (hệ thống không kiểm chứng).

## ✍️ Hiệu ứng "vẽ tay" (draw-on) — whiteboard thật

Bật ô **"Hiệu ứng vẽ tay (draw-on)"** (có ở cả khu tạo tự động lẫn khu tự soạn, chỉ
bật được khi chọn **Bảng trắng + có video**): chữ sẽ **hiện dần trái→phải như đang
viết**, có **cây bút chạy theo nét**; doodle cũng được vẽ dần. Cuối mỗi slide giữ
hình đầy đủ một nhịp rồi sang slide sau (khớp giọng đọc).

Dòng lệnh: `run.py tiktok-whiteboard N` đã bật sẵn hiệu ứng vẽ tay.

> Hiệu ứng này **chậm hơn** (dựng từng khung hình) nên video mất thêm thời gian.
> Cách làm tự chứa: hệ thống dò vùng "mực" trên slide rồi lộ dần + chèn cây bút —
> không cần phần mềm ngoài.

## Cách dùng bằng dòng lệnh

```bash
~/.ebm-venv/bin/python run.py tiktok 5            # 5 bài slideshow (chứng cứ ĐỦ MẠNH)
~/.ebm-venv/bin/python run.py tiktok-watch 5      # gồm cả "tin nhanh – chưa kết luận"
~/.ebm-venv/bin/python run.py tiktok-video 5      # 5 bài + video giọng đọc (nền tối)
~/.ebm-venv/bin/python run.py tiktok-whiteboard 3 # video bảng trắng viết tay + giọng mềm
```

Kết quả nằm ở `data/tiktok/<ngày-giờ>/` — mở `index.html` để xem trước cả lô.

## Tự chọn chủ đề (hàng đợi)

Trong tab TikTok có ô **Hàng đợi chủ đề**, hoặc sửa file `data/tiktok/queue.txt`,
mỗi dòng là **id bản ghi** (xem ở tab Executive) hoặc **một phần tiêu đề**:

```
49
atrial fibrillation
KDIGO
```

Lần tạo lô sau sẽ ưu tiên các chủ đề này.

## Nguyên tắc an toàn (đã cài sẵn)

- **Không bịa số liệu**: mọi "điểm chính" là câu **trích nguyên văn** từ abstract,
  có kèm bản dịch tiếng Việt tham khảo và giữ nguyên văn tiếng Anh để truy vết.
- **Gác độ tin cậy**: chỉ guideline / tổng quan hệ thống / RCT / cảnh báo chính
  thức (tier A/B) được trình bày dạng "CẬP NHẬT CHỨNG CỨ". Chứng cứ yếu chỉ ở dạng
  "TIN NHANH – CHƯA KẾT LUẬN" và **không đăng mặc định**.
- Mỗi bài luôn có **dòng nguồn** (DOI/PMID/URL) + **khuyến cáo** "tham khảo, không
  thay khám bệnh".

## Sắp tới (khi cần)

- **Tự động đăng**: đẩy bản nháp / đăng thẳng lên TikTok qua Content Posting API
  (cần đăng ký TikTok developer + duyệt). Hiện khâu đăng làm thủ công cho an toàn —
  khi cần tự động sẽ bổ sung.
