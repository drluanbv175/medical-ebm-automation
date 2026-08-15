# GIAO THỨC TỰ SỬA CHỮA ĐỘI AGENT (self-repair protocol)

> Tài liệu tham chiếu dùng chung. Mục đích: mọi phiên có thể **tự rà → phát hiện lệch → sửa** để giữ đội agent đồng bộ, đa kết nối, đúng liêm chính.
> Đồng bộ với `README.md` (checklist kiểm toán), `_BAN-DO-KET-NOI.md`, `_KIEM-TOAN-DAY-DU-NGHIEN-CUU.md`, `_HIEN-PHAP-LIEM-CHINH.md`, `_NGUYEN-TAC-TRUNG-THUC-BAO-MAT-PHAP-LY-LIEM-CHINH.md`. Cập nhật 2026-06-16 (sửa lệch số 38→tự-đếm-động; vá snippet zsh).

## ⚠️ GIỚI HẠN BẢN CHẤT (đọc trước — KHÔNG nói quá)
Đây là **cơ chế cấp prompt do MÔ HÌNH thực thi TRONG MỘT PHIÊN** khi được gọi (thủ công hoặc qua routine có lịch). **KHÔNG** phải phần mềm chạy nền, **KHÔNG** phải daemon/cron tự vá mã ngoài phiên, **KHÔNG** tự kích hoạt nếu không có phiên Claude chạy. Hiệu lực phụ thuộc việc mô hình tuân thủ tài liệu này. Mọi thay đổi file vẫn theo luật: **sao lưu `.bak` trước khi sửa, ghi qua bash (Edit chặn `.claude/`), đọc lại xác minh, KHÔNG bịa**.

## QUY TRÌNH 3 THÌ: RÀ → PHÁT HIỆN LỆCH → SỬA
1. **RÀ:** chạy bộ kiểm dưới (mục "Bộ kiểm tự động"). Ghi lại kết quả từng tiêu chí.
2. **PHÁT HIỆN LỆCH:** liệt kê mọi mục **🔴 (lỗi)** / **🟡 (cần xem)**; với mỗi mục nêu file + bằng chứng (dòng).
3. **SỬA:** chỉ sửa khi chắc chắn; sao lưu `.bak` → sửa qua bash/python → đọc lại xác minh. Mục không chắc → đánh dấu `[CẦN XÁC NHẬN TẠI ĐƠN VỊ]`, KHÔNG tự đoán.

## CHECKLIST ĐỒNG BỘ (điều kiện "đội agent lành mạnh")
- [ ] **Số agent khớp:** số file `*.md` (loại `README.md`, `_*.md`) — **để snippet TỰ ĐẾM `$N`, KHÔNG hardcode** — phải khớp con số ở header `README.md` = số nêu ở `CLAUDE.md`. *(Mốc tham chiếu 2026-06-16: **48** = 19 LS + 28 NC + 1 guardrail dùng chung; con số này chỉ là mốc, đừng dán cứng vào bộ kiểm.)*
- [ ] **filename == name:** mỗi agent có `name:` trùng tên file (không dấu, gạch nối).
- [ ] **Không tham chiếu treo:** mọi token kiểu tên-agent trong backtick ứng với một file agent thật; token còn lại phải là **skill/tool đã biết** (đối chiếu danh sách skill đã cài — xem `_BAN-DO-KET-NOI.md` mục skill ngoài).
- [ ] **Đồng bộ điều phối ⇄ kiểm toán ⇄ README:** agent phụ trách mỗi artifact **A1–A18** trong `_KIEM-TOAN-DAY-DU-NGHIEN-CUU.md` khớp bảng trong `dieu-phoi-nghien-cuu.md`; tên agent trong README khớp file thật.
- [ ] **Bao phủ router:** hai nhạc trưởng (`dieu-phoi-lam-sang`, `dieu-phoi-nghien-cuu`) phủ hết agent con; không agent mồ côi (in=0 và out=0).
- [ ] **Hai cổng an toàn còn nguyên:** Cổng A (quyết định lâm sàng) + Cổng B (ghi EBM_MASTER) không bị agent nào tự vượt; 6 cổng cứng nghiên cứu G2/G4/G5 khóa dữ liệu thật/G8 bình duyệt độc lập/G9 liêm chính/G10 PI khóa gói phát hành còn nguyên.
- [ ] **4 trụ cột phủ `$N/$N` (mốc 48/48):** mọi agent dẫn `_HIEN-PHAP-LIEM-CHINH.md` + `_NGUYEN-TAC-TRUNG-THUC-BAO-MAT-PHAP-LY-LIEM-CHINH.md`, kết "Cần bác sĩ kiểm chứng", dùng nhãn `[CẦN BỔ SUNG]/[CẦN KIỂM CHỨNG]/[CẦN XÁC NHẬN TẠI ĐƠN VỊ]/[DỰ THẢO]` khi thiếu, KHÔNG PII.
- [ ] **Guardrail đầu ra nối đủ:** `tham-dinh-dau-ra` được CẢ HAI nhạc trưởng + 5 routine lâm sàng (uptodate · drug-safety · giam-sat · antifacts-weekly-ebm · tong-hop-chung-cu-hang-tuan — 2026-07-12: sửa "3", 2 routine sau thêm vào wiring 2026-06-20) gọi ở BƯỚC CUỐI (trước khi trả/bàn giao bác sĩ); rubric **2 lớp** — Lớp 1 R1–R7 (`_KIEM-DUYET-DOC-LAP.md`) + Lớp 2 Q1–Q7 Med-PaLM cho gói lâm sàng (`_CHUAN-CHAT-LUONG-MEDPALM.md`); còn lỗi đỏ → TRẢ-VỀ-SỬA, không phát hành.
- [ ] **Tự-rà hai vòng còn sống:** vòng nghiên cứu có `completeness-critic` (A1–A18); vòng lâm sàng có "TỰ-RÀ HOÀN CHỈNH CA LÂM SÀNG" (C1–C9).
- [ ] **Vệ sinh thư mục — không rác `.bak`:** mọi backup `*.bak*` phải nằm trong `_archive/`, KHÔNG lẫn cạnh agent ở thư mục sống (tránh nhiễu loader + đếm sai). Soát: `ls *.bak* 2>/dev/null | wc -l` phải = 0.
- [ ] **Index sổ hạ tầng khớp:** mục "Sổ tham chiếu hạ tầng" trong `README.md` liệt kê đủ các file `_*.md` đang có (gồm `_SO-DO-PIPELINE-HOP-NHAT.md`, `_QUAN-TRI-DU-LIEU-PII.md`, `_NHAT-KY-KHAI-BAO-AI.md`). *(2026-07-12: chạy thật checklist này lần đầu — 8/32 file `_*.md` sống thiếu khỏi index, đã bổ sung đủ 32/32 trong README.md; giữ mục kiểm này để bắt drift lần sau.)*

## BỘ KIỂM TỰ ĐỘNG (dán vào bash — chạy trong `.claude/agents/`)
```bash
cd .../.claude/agents
# ⚠️ CHẠY ĐÚNG: snippet TỰ ĐẾM $N (không hardcode), AN TOÀN cả zsh lẫn bash.
# (Lỗi cũ: `for f in $ag` trong ZSH không tách từ → cả danh sách thành 1 đối số → "File name too long" → in 0/N giả.
#  Khắc phục: vòng `while read` đọc từng tên 1 dòng; mẫu số dùng biến động $N.)
N=$(ls *.md | grep -vE '^(README|_)' | wc -l | tr -d ' ')
echo "Số agent thực: $N  (đối chiếu header README.md & CLAUDE.md — phải khớp)"
c1=0; c2=0; c3=0
while IFS= read -r f; do
  grep -q 'NGUYEN-TAC-TRUNG-THUC'   "$f" && c1=$((c1+1))
  grep -q 'HIEN-PHAP-LIEM-CHINH'    "$f" && c2=$((c2+1))
  grep -q 'Cần bác sĩ kiểm chứng'   "$f" && c3=$((c3+1))
  nm=$(grep -m1 '^name:' "$f" | sed 's/^name:[[:space:]]*//')
  [ "$nm" = "${f%.md}" ] || echo "  name!=file: $f ($nm)"
done < <(ls *.md | grep -vE '^(README|_)')
echo "Liêm chính: NGUYEN-TAC $c1/$N | hiến pháp $c2/$N | disclaimer $c3/$N   (kỳ vọng $N/$N)"
echo "rác .bak ở thư mục sống: $(ls *.bak* 2>/dev/null | wc -l | tr -d ' ') (kỳ vọng 0 — backup phải ở _archive/)"
# Tham chiếu treo: token tên-agent không khớp file (đối chiếu thủ công với skill đã biết)
ls *.md | grep -vE '^(README|_)' | xargs grep -rhoE '`[a-z0-9]+(-[a-z0-9]+)+`' README.md 2>/dev/null | tr -d '`' | sort -u
```
Đối chiếu kết quả với CHECKLIST trên. Mọi 🔴 → vào "DANH SÁCH LỆCH BẮT BUỘC SỬA".

## ĐỊNH DẠNG BÁO CÁO TỰ RÀ
| Tiêu chí | Trạng thái (✅/🟡/🔴) | Bằng chứng (file/dòng) | Việc cần làm |
|---|---|---|---|
Kết thúc bằng **"DANH SÁCH 🔴 BẮT BUỘC SỬA"** + đề xuất sửa (kèm cảnh báo sao lưu trước khi ghi). Nếu sạch → ghi "Đội agent đồng bộ — không phát hiện lệch (ngày…)".

> **"Cần bác sĩ kiểm chứng."** Đây là công cụ HỖ TRỢ giữ chất lượng, không thay quyết định của bác sĩ.
