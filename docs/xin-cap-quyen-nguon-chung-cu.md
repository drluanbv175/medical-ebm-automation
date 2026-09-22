# Xin cấp quyền / gỡ chặn cho các nguồn chứng cứ — soạn 20/09/2026

> **Đây là BẢN NHÁP để bác sĩ tự đọc, sửa và tự gửi.** Hệ thống KHÔNG gửi thư hộ. Thông tin đo được ghi kèm
> ngày đo; mục nào chưa xác minh thì ghi rõ.

## 0. Tóm tắt nhanh

| Nguồn | Trạng thái đo 20/09/2026 | Việc của bác sĩ |
|---|---|---|
| **CORE** (core.ac.uk) | Chạy được KHÔNG khoá (test-live: 3 kết quả thật) | Chỉ cần bật: nút `Bat Tat SerpApi Du Phong.command` → gõ `bo`. Khoá (chỉ cần email) chỉ tăng nhịp |
| **Epistemonikos** | Cần token, không tự đăng ký được | Gửi thư mục 1 |
| **NICE Syndication API** | Chỉ cấp cho **tổ chức** (không cấp cá nhân), có duyệt + giấy phép + phí quốc tế, tổ chức phải có chứng nhận an ninh mạng | Xem mục 2 — nhiều khả năng KHÔNG khả thi cho cá nhân |
| **NCBI/PubMed** | Bị chặn "misuse" theo IP mạng này (esearch/esummary/efetch đều 302) | Mục 3: gỡ chặn qua email, hoặc VPN (bác sĩ tự bật) |

## 1. Epistemonikos — xin token API

Nguồn: tài liệu chính thức https://api.epistemonikos.org/ ghi nguyên văn hướng đăng ký app là liên hệ dev@epistemonikos.org; API beta chỉ
cho client đã đăng ký, mỗi client nhận một token riêng đặt trong header `Authorization`.

**Gửi tới:** dev@epistemonikos.org — **Tiêu đề:** Request for API access token (non-commercial clinical evidence surveillance)

```
Dear Epistemonikos team,

I am a practising physician (outpatient internal medicine, Vietnam) and I maintain a small, non-commercial tool that
helps me keep my clinical practice up to date with peer-reviewed evidence. I would like to request an API access token
for the Epistemonikos API.

Intended use:
- weekly/monthly read-only searches of systematic reviews and overviews on a fixed list of clinical topics,
  for personal clinical decision support and for my own research work;
- results are used only as a discovery/cross-check layer; every record is verified against Crossref/PubMed before use,
  and Epistemonikos is credited as the source;
- low volume (a few dozen queries per week), no redistribution of your data, no commercial use, no patient data sent
  to your service.

Please let me know if you need further details or if there are usage terms I should follow.

Thank you very much,
[Họ tên] — [chức danh, cơ quan] — [email] — [số điện thoại tuỳ chọn]
```

Có token → bấm `Nhap Khoa Epistemonikos.command` (ô nhập ẩn) → bật bằng nút bật/tắt, gõ `be` → thử `python run.py test-live epistemonikos "heart failure"`.

## 2. NICE — nói thẳng: nhiều khả năng không khả thi cho cá nhân

Nguồn: https://www.nice.org.uk/reusing-our-content/nice-syndication-api (đọc 20/09/2026). NICE API dành cho **công ty/tổ chức, không
dành cho cá nhân**; truy cập trong nước và quốc tế đều qua **duyệt + giấy phép + phí (dùng quốc tế)**; tổ chức phải có **chứng nhận
an ninh mạng**; đơn gửi syndication@nice.org.uk, xét theo tháng; hỏi thêm: reuseofcontent@nice.org.uk.

Trang guidance của NICE cũng chặn truy cập tự động (HTTP 403, đo 13/08/2026), nên không có đường "lách" hợp lệ bằng cách đọc web.

**Khuyến nghị:** không chờ NICE API. Phủ NICE bằng: (a) agent tra trang NICE thủ công theo `_NGUON-GUIDELINE-TU-DONG.md`, (b) nhập tay
metadata guideline bằng `app/sources/guidelines.py::manual_import()` kèm trạng thái xác minh, (c) bài đăng lại/tóm tắt của NICE trong
các tạp chí (BMJ…).

⛔ **ĐÍNH CHÍNH 22/09/2026 — câu "(c)... đã nằm trong lane tạp chí Crossref" ở trên SAI, đối
chiếu trực tiếp `feeds.py::_HIEP_HOI_TREN_TAP_CHI` (21 hiệp hội) xác nhận NICE KHÔNG có mặt.**
Đã ĐÓNG khoảng trống (c) thật sự — nhưng bằng lane KHÁC: `epmc_nice` (Europe PMC, không phải
Crossref-title), lọc AFF="National Institute for Health and Care Excellence" AND
PUB_TYPE="Practice Guideline". Đăng ký `SRC-037` trong `data/sources.json`, kiểm sống 5 bản ghi
PMID thật (xem CLAUDE.md gốc mục "LANE guideline nối trực tiếp"). Nếu bệnh viện/cơ quan của bác
sĩ đủ điều kiện tổ chức và vẫn muốn NICE Syndication API CHÍNH THỨC (toàn văn, không chỉ tín
hiệu qua tóm tắt), có thể hỏi trước:

**Gửi tới:** reuseofcontent@nice.org.uk — **Tiêu đề:** Enquiry: eligibility for NICE syndication API (hospital, Vietnam)

```
Dear NICE re-use of content team,

I work at [tên bệnh viện/cơ quan], a hospital in Vietnam. We would like to understand whether an organisation like ours
could apply for the NICE syndication API for non-commercial, internal clinical decision-support use (weekly discovery of
newly published and updated guidance titles and links, no republication of content).

Could you please tell us: (1) whether international non-commercial hospital use is eligible; (2) the fee and licence
terms for that case; (3) whether the cyber-security certification requirement can be met by other evidence; and (4) the
application process and timescale.

Kind regards,
[Họ tên] — [chức danh] — [email]
```

Chỉ khi có API key do NICE cấp mới bấm `Nhap Khoa NICE.command` rồi bật bằng `bn`.

## 2bis. USPSTF — API chính thức (miễn phí nhưng phải xin duyệt)

Nguồn: https://www.uspreventiveservicestaskforce.org/apps/api.jsp (đọc 20/09/2026): muốn dùng Prevention TaskForce API phải gửi email
xin duyệt tới uspstfpda@ahrq.gov kèm thông tin liên hệ và mô tả mục đích. Điều kiện ghi rõ: khi hiển thị khuyến cáo phải **giữ nguyên văn,
không sửa, và ghi nguồn**. Tài liệu kỹ thuật (endpoint, trường JSON) nằm trong file PDF hướng dẫn trên trang đó, chỉ có sau khi được cấp.

Trong lúc chờ: hệ đã có lane `epmc_uspstf` (Recommendation Statement của USPSTF trong MEDLINE qua Europe PMC, có PMID) — không cần khoá.
Đo 20/09/2026: 0 bài trong 365 ngày, 6 bài trong 730 ngày (USPSTF ra rất ít gần đây).

**Gửi tới:** uspstfpda@ahrq.gov — **Tiêu đề:** Request for Prevention TaskForce API access (non-commercial clinical decision support)

```
Dear USPSTF / AHRQ team,

I am a practising physician (outpatient internal medicine, Vietnam). I would like to request access to the Prevention
TaskForce API for a personal, non-commercial clinical evidence-surveillance tool.

Intended use: a scheduled, read-only check (about weekly) for new or updated USPSTF recommendations, so that my
practice guidance stays current. Recommendation text will only be shown verbatim, unmodified and with a clear
citation to USPSTF as the source; no patient data will be sent to your service; no redistribution or commercial use.

Contact: [Họ tên], [chức danh, cơ quan], [email].

Thank you,
[Họ tên]
```

## 3. NCBI/PubMed bị chặn "misuse"

Đo 20/09/2026: cả `esearch`, `esummary`, `efetch` của `eutils.ncbi.nlm.nih.gov` đều trả HTTP 302 sang trang
`misuse.ncbi.nlm.nih.gov/error/abuse.shtml` từ IP mạng này. Thêm `NCBI_API_KEY` **không** gỡ được (chặn theo IP, phía máy chủ NCBI).
Hệ vẫn chạy nhờ Europe PMC (bản sao MEDLINE) + Crossref, nhưng PubMed trực tiếp không dùng được.

**Cách 1 — đổi IP thoát bằng VPN (bác sĩ tự bật; agent không được đổi cài đặt mạng của máy):**
1. Mở ứng dụng **Kaspersky VPN** (Kaspersky Secure Connection) → chọn vị trí → Kết nối.
2. **Lưu ý Scopus — ĐÃ KIỂM 20/09/2026, cách ép card KHÔNG hiệu quả với Kaspersky VPN:** Scopus bị Cloudflare chặn theo IP của VPN.
   Đặt `SCOPUS_BIND_INTERFACE=en1` (card vật lý của máy này) vẫn bị 403, vì địa chỉ nguồn của kết nối vẫn là địa chỉ đường hầm VPN
   (`172.21.39.127`, không phải `192.168.1.11` của en1) — bằng chứng và hệ quả ở `CLAUDE.md` mục Scopus. Nên: **chạy Scopus lúc VPN tắt**, hoặc
   ~~thêm `api.elsevier.com` vào danh sách loại trừ~~ — **đã kiểm 20/09/2026: không làm được.** Kaspersky VPN cho Mac chỉ có «Phân tách kênh
   truyền tải» theo **ứng dụng** và **đảo chiều** (tick «Chỉ bật VPN cho các ứng dụng được chọn»: ứng dụng trong danh sách đi qua VPN, còn lại
   đi thẳng), không có ô tên miền/IP, chỉ có ở bản Unlimited và chỉ với ứng dụng trong thư mục Applications
   ([trang chính thức](https://support.kaspersky.com/us/ksec-for-mac/240287)). Scopus và PubMed chạy chung một tiến trình Python nên không tách được.
3. Nhắn Claude "đã bật VPN" → Claude kiểm `esearch` PubMed và chạy lại các test nguồn. **Kết quả đo 20/09/2026 với VPN bật:** PubMed HTTP 200
   (hết chặn), Scopus vẫn 403, 33/33 lane guideline chạy, SerpApi + Consensus chạy thật.

**Cách 2 — xin gỡ chặn (lâu dài, không phụ thuộc VPN).** Gửi tới **info@ncbi.nlm.nih.gov**:

```
Subject: Request to lift a "misuse" block on E-utilities for our IP address

Hello NCBI team,

Requests from our network to eutils.ncbi.nlm.nih.gov (esearch/esummary/efetch) are redirected to
misuse.ncbi.nlm.nih.gov/error/abuse.shtml. Our IP address (as seen by NCBI) is: [chạy: curl -s https://api.ipify.org].
Contact: [Họ tên], [email], tool name: medical-ebm-automation (personal clinical literature surveillance).

We are a small non-commercial clinical tool: a few dozen requests per week, always with tool/email parameters and
an API key [đã đăng ký: có/không], respecting the 3 requests/second limit (10/s with a key). The network is a
shared hospital connection, so other users behind the same address may have triggered the block. Could you please
review the block and lift it, or advise how we can register to avoid it?

Thank you,
[Họ tên]
```
