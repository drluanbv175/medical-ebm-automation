# CƠ CHẾ KIỂM DUYỆT ĐỘC LẬP (output guardrail) — tài liệu tham chiếu dùng chung

> Mục đích: mô tả chốt **thẩm định đầu ra độc lập** chạy SAU mỗi nhạc trưởng và TRƯỚC khi trả bác sĩ, để chặn lỗi liêm chính/an toàn/định dạng trước khi phát hành.
> Agent thực thi: `tham-dinh-dau-ra.md`. Đồng bộ với `_HIEN-PHAP-LIEM-CHINH.md`, `_NGUYEN-TAC-TRUNG-THUC-BAO-MAT-PHAP-LY-LIEM-CHINH.md`, `_TU-SUA-CHUA-PROTOCOL.md`, `dieu-phoi-lam-sang.md`, `dieu-phoi-nghien-cuu.md`. Cập nhật 2026-07-11 (thêm R1b/R14 vào bảng rubric — trước đó lệch với `tham-dinh-dau-ra.md`).

## ⚠️ GIỚI HẠN BẢN CHẤT (đọc trước — KHÔNG nói quá)
- Đây là **cơ chế cấp prompt do CÙNG MỘT MÔ HÌNH thực thi trong CÙNG một phiên**. **KHÔNG** phải một tiến trình tách biệt, **KHÔNG** phải sandbox/quá trình cưỡng chế ở tầng hệ điều hành, **KHÔNG** có quyền veto kỹ thuật ngăn token phát ra ngoài ý muốn của mô hình.
- "Độc lập" ở đây nghĩa là **độc lập về VAI** (đổi tư thế sang đối kháng, soi gói như của người khác), KHÔNG phải độc lập về tiến trình. Đây là phòng vệ lớp prompt — giảm sai sót, **không** đảm bảo tuyệt đối.
- Hiệu lực phụ thuộc: (a) nhạc trưởng thật sự GỌI bước kiểm; (b) mô hình tuân thủ rubric; (c) gói đầu ra được đưa vào kiểm đầy đủ. Nếu một trong ba thiếu → chốt kiểm vô hiệu một phần. Vì vậy rào cứng cuối cùng vẫn là **bác sĩ duyệt (Cổng A/B, cổng G)**.
- Khi cần chốt kiểm mạnh hơn (đối kháng thật sự, không cùng ngữ cảnh) → xem `_LO-TRINH-HA-TANG.md` mục orchestrator/critic ngoài phiên — **[CẦN CÔNG CỤ NGOÀI]**.
- **KHỐI KẾT QUẢ LÀ BẮT BUỘC:** chốt kiểm này hiện ở dạng KHỐI BẮT BUỘC điền sẵn ("KẾT QUẢ THẨM ĐỊNH ĐẦU RA (tham-dinh-dau-ra)", Lớp 1 R1–R7 + Lớp 2 Q1–Q7 cho gói lâm sàng + ô KẾT [ĐẠT/TRẢ-VỀ-SỬA]) đặt NGAY TRƯỚC mẫu GÓI QUYẾT ĐỊNH (`dieu-phoi-lam-sang`) / mẫu bàn giao (`dieu-phoi-nghien-cuu`). Mỗi nhạc trưởng PHẢI điền khối này ở bước cuối; **CẤM phát hành/bàn giao khi khối chưa ĐẠT** (còn 🔴 → trả về agent phụ trách sửa rồi kiểm lại).
- **Chế độ tách ngữ cảnh — đã bật khi có Agent/Task tool (2026-06-14; 2026-07-11: sửa thuật ngữ "tách tiến trình"→"tách ngữ cảnh" cho khớp `tham-dinh-dau-ra.md`/`dieu-phoi-lam-sang.md`/`dieu-phoi-nghien-cuu.md` — cả 3 file đó minh thị bác bỏ "tách tiến trình/mô hình", chỉ có ngữ cảnh hội thoại mới thật sự tách; xác nhận qua tài liệu Claude Code chính thức: subagent chạy trong "fresh conversation" CÙNG tiến trình/mô hình):**
  - **Claude Code / Cowork:** nhạc trưởng spawn `tham-dinh-dau-ra` như **subagent NGỮ CẢNH MỚI** (`subagent_type: "tham-dinh-dau-ra"`, chỉ nhận gói đầu ra + nguồn) → đạt **tách ngữ cảnh thật** (không chỉ tách VAI), KHÔNG phải tách tiến trình/mô hình. Đây là chế độ **ưu tiên/mặc định** khi tool có sẵn; KHÔNG còn [CẦN MÔI TRƯỜNG HỖ TRỢ] — nhưng vẫn cần tự xác nhận không bị gọi LỒNG (xem `tham-dinh-dau-ra.md` §Giới hạn bản chất, cập nhật 2026-07-11 do Claude Code v2.1.172 đã cho phép subagent lồng subagent tới 5 cấp).
  - **Phiên không có subagent (vd launchd headless):** lùi về tự-kiểm cùng phiên (độc lập VAI) hoặc chạy tay `tools/critic/tham-dinh-dau-ra.standalone.md` ở phiên khác.
  - **Giới hạn KHÔNG đổi:** cùng họ mô hình → tách ngữ cảnh **giảm mù chung nhưng KHÔNG khử thiên lệch hệ thống**; rào cứng cuối vẫn là **bác sĩ duyệt (Cổng A/B, cổng G)**.

## RUBRIC DÙNG CHUNG — LỚP 1: LIÊM CHÍNH (7 mục R1–R7 — bản chuẩn, mọi nơi tham chiếu về đây)
| # | Tiêu chí | Lỗi đỏ (🔴) khi… |
|---|---|---|
| R1 | **Nguồn** — mọi khẳng định/số liệu có PMID/DOI (hoặc guideline+năm+mục) hoặc nhãn PARTIAL/[CẦN KIỂM CHỨNG] | khẳng định y khoa/con số không nguồn & không nhãn thiếu |
| R1b | **Chống lách nhãn** — nhãn `[CẦN…]` dùng cho chỗ thiếu THẬT, không phải để "qua cổng" hàng loạt | phần lớn (≳50%) khẳng định cốt lõi đều gắn `[CẦN…]` mà không một nguồn thật nào → CHƯA hoàn thiện |
| R2 | **PII** — không lẫn định danh BN (tên, ngày sinh, số hồ sơ/CCCD/BHYT, địa chỉ, SĐT, ảnh nhận dạng) | phát hiện bất kỳ PII nào |
| R3 | **Cổng A/B/G** — không tự "áp dụng cho BN"/"ghi EBM_MASTER đã xác minh"/vượt G2·G4·**G5 (khóa DB)**·**G8 (bình duyệt độc lập)**·liêm chính tác giả khi chưa duyệt | gói tự kết luận đã áp dụng/đã ghi/đã khóa/đã đăng ký/đã bình duyệt, hoặc **"đã phân tích" khi DB chưa khóa**, mà chưa có duyệt thật |
| R4 | **Không tự gán mức** — không tự gán GRADE/độ mạnh khuyến cáo khi nguồn không cấp (`gradeLevel:'na'`); dùng đúng công cụ RoB theo thiết kế (RoB 2 RCT · ROBINS-I V2 quan sát can thiệp · ROBINS-E phơi nhiễm · AMSTAR-2 SR · QUADAS-2 chẩn đoán) | tự dán mức không từ nguồn; sai công cụ RoB theo thiết kế |
| R5 | **Tách 2 trục** — phân biệt độ chắc chắn CHỨNG CỨ vs độ mạnh KHUYẾN CÁO | trộn hai khái niệm gây hiểu sai sức nặng |
| R6 | **Nhãn thiếu** — dùng đúng [CẦN BỔ SUNG]/[CẦN KIỂM CHỨNG]/[CẦN XÁC NHẬN TẠI ĐƠN VỊ]/[DỰ THẢO] | lấp chỗ thiếu bằng phỏng đoán như dữ kiện chắc |
| R7 | **Disclaimer** — kết "Cần bác sĩ kiểm chứng." | thiếu disclaimer cuối gói y khoa |
| R14 | **Rà an toàn kê đơn** *(HARD-RED, PHỤ LỤC CÓ ĐIỀU KIỆN — chỉ gói CÓ khuyến cáo/điều chỉnh thuốc, 2026-07-07)* | gói đề xuất/đổi thuốc mà thiếu rà tương tác/CCĐ/chỉnh liều theo eGFR-gan-tuổi → 🔴 DỪNG NGAY, giao `ke-don-an-toan` |

**Phán định Lớp 1:** còn bất kỳ 🔴 → **TRẢ-VỀ-SỬA** (CẤM phát hành). Chỉ 🟡 → ĐẠT-CÓ-LƯU-Ý. Toàn ✅ → ĐẠT. (R8 — phụ lục thống kê CÓ ĐIỀU KIỆN, chỉ gói CÓ số liệu thống kê — không liệt ở đây vì không phải cốt lõi; đặc tả đầy đủ ở `tham-dinh-dau-ra.md` §3.)

## RUBRIC DÙNG CHUNG — LỚP 2: CHẤT LƯỢNG LÂM SÀNG (7 trục Q1–Q7, Med-PaLM 2)
> CHỈ áp cho gói **lâm sàng** (đầu ra `dieu-phoi-lam-sang` + routine lâm sàng). Gói **nghiên cứu** bỏ qua Lớp 2 (dùng CONSORT/STROBE/PRISMA + `_KIEM-TOAN-DAY-DU-NGHIEN-CUU.md`). Bản chuẩn đầy đủ + xuất xứ từng trục + PMID/DOI: **`_CHUAN-CHAT-LUONG-MEDPALM.md`**.

Q1 Dễ đọc · Q2 Đúng đắn *(cần bác sĩ)* · Q3 Đầy đủ · Q4 Thiên kiến · Q5 Nguy cơ hại · Q6 Cập nhật · Q7 Thẩm quyền nguồn.

**Phán định Lớp 2:** còn 🔴 → **TRẢ-VỀ-SỬA**; **Q2/Q5 đỏ → BẮT BUỘC chuyển bác sĩ** (AI không tự chứng nhận "đúng đắn y khoa" — chỉ sàng lọc & gắn cờ). **Gói lâm sàng chỉ phát hành khi ĐẠT cả Lớp 1 lẫn Lớp 2.**

## CÁCH NỐI VÀO DÂY CHUYỀN
- `dieu-phoi-lam-sang`: sau khi soạn xong GÓI QUYẾT ĐỊNH (qua tự-rà C1–C9), **trước khi trả bác sĩ** → gọi `tham-dinh-dau-ra`. Còn 🔴 → quay lại agent phụ trách sửa rồi kiểm lại; sạch → phát hành (vẫn dừng ở Cổng A/B).
- `dieu-phoi-nghien-cuu`: sau completeness-critic (A1–A18) ở mỗi cổng, **trước khi bàn giao bác sĩ** → gọi `tham-dinh-dau-ra`. Còn 🔴 → sửa rồi kiểm lại; sạch → bàn giao (vẫn dừng ở G2/G4/liêm chính tác giả).
- Quan hệ với hai vòng tự-rà sẵn có: completeness-critic (đủ artifact) và tự-rà C1–C9 (đủ ca) trả lời "ĐỦ CHƯA"; `tham-dinh-dau-ra` trả lời "CÓ ĐƯỢC PHÁT HÀNH KHÔNG" về mặt liêm chính/an toàn/định dạng. Hai lớp bổ sung, không thay nhau.

## NGUYÊN TẮC
Kiểm đối kháng, nghiêm khắc; không "cho qua vì gần đúng"; không tạo nội dung mới; không sửa hộ (trả về agent phụ trách); KHÔNG PII. Mọi thay đổi file theo luật chung: sao lưu `.bak` trước khi sửa, ghi qua bash, đọc lại xác minh, KHÔNG bịa.

> **"Cần bác sĩ kiểm chứng."** Đây là chốt kiểm HỖ TRỢ, không thay quyết định và trách nhiệm của bác sĩ.
