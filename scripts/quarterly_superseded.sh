#!/bin/bash
# QUÉT "CHỨNG CỨ BỊ VƯỢT QUA" theo QUÝ trên toàn kho — LÔ 4, bác sĩ duyệt Q3 15/08/2026.
#
# Vì sao có: kiem_chung_cu_vuot_qua.py trước nay chỉ chạy THEO YÊU CẦU, nên chỉ số
# "guideline đang dùng nhưng đã bị thay thế = 0" (mục 7 prompt kiện toàn) không được
# canh định kỳ. Script này là CHỦ SỞ HỮU thứ ba trong allowlist tu_khoi_dong (nhịp 92
# ngày) — cùng khuôn log BẮT ĐẦU/KẾT THÚC ... tổng thể=PASS để kiem_do_tuoi đọc được.
#
# Đầu ra: EBM-Dashboards/derivatives/CHUNG-CU-VUOT-QUA_<ngày>.txt — danh sách ĐỂ ĐỌC,
# công cụ không đổi decision nào (BH10).
set -u
HERE="$(cd "$(dirname "$0")/.." && pwd)"     # medical-ebm-automation/
HUB="$(cd "$HERE/.." && pwd)"                # Claude AI/
# SỬA 16/09/2026: xem chú thích cùng nội dung trong scripts/weekly_safety.sh —
# thiếu nhánh Windows (Scripts/python.exe) khiến script rơi về python hệ thống, thiếu thư viện.
PY="$HOME/.ebm-venv/bin/python"
[ -x "$PY" ] || PY="$HOME/.ebm-venv/Scripts/python.exe"
[ -x "$PY" ] || PY="$(command -v python3 || command -v python)"
LOG="$HERE/data/archive/quarterly_superseded.log"
mkdir -p "$(dirname "$LOG")"

echo "===== $(date '+%Y-%m-%d %H:%M:%S') : BẮT ĐẦU quét chứng cứ bị vượt qua (quý) =====" >> "$LOG"
OUT="$HUB/EBM-Dashboards/derivatives/CHUNG-CU-VUOT-QUA_$(date '+%Y%m%d').txt"
# MANIFEST JSON (21/09/2026): kết luận + phạm vi + danh sách PMID có bài mới hơn. Bên tiêu thụ (tra_diem_kham,
# provenance_ledger) đọc manifest qua kiem_chung_cu_vuot_qua.doc_bao_cao_vuot_qua() thay vì phân tích chuỗi văn bản —
# báo cáo 16/09 in 🟢 giả (bản lỗi JSON đọc thành rỗng) làm tắt mọi cờ 🟠 vì không ai phân biệt được nó với «sạch thật».
OUTJ="${OUT%.txt}.json"
# Xoá manifest cũ TRƯỚC khi chạy: lượt này chết giữa chừng thì không được để manifest hợp lệ của lượt trước ghép với báo cáo mới.
rm -f "$OUTJ"
if ! mkdir -p "$(dirname "$OUT")" 2>> "$LOG"; then
  echo "===== $(date '+%Y-%m-%d %H:%M:%S') : KẾT THÚC — không tạo được thư mục đầu ra, tổng thể=CÓ BƯỚC LỖI =====" >> "$LOG"
  exit 0
fi
"$PY" "$HUB/tools/kiem_chung_cu_vuot_qua.py" --json-ra "$OUTJ" > "$OUT" 2>> "$LOG"
rc=$?
# Kết luận thật đến từ MANIFEST, không từ mã thoát: CHUA_DO / MAU / lỗi không đọc được manifest đều KHÔNG phải «đã dò xong».
ket_luan=$("$PY" -c "import json,sys; print(json.load(open(sys.argv[1],encoding='utf-8')).get('ket_luan',''))" "$OUTJ" 2>/dev/null || echo "")
# Vá 22/09/2026 (phản biện vòng 2, review:cong-rut-bai #2): CO_BAI_MOI vẫn cho phép so_pmid_hong>0
# (một phần PMID không hỏi được, phần còn lại có dương tính thật) — trước đây tiêu chí PASS ở đây
# chỉ nhìn ket_luan, YẾU HƠN tiêu chí hợp lệ của bên tiêu thụ (doc_bao_cao_vuot_qua() đòi so_pmid_hong
# == 0 mới hop_le=True). Hệ quả: kiem_do_tuoi/tu_khoi_dong đọc "tổng thể=PASS" và reset đồng hồ 92
# ngày cho một lượt dò MỘT PHẦN, trong khi bác sĩ không hề được báo có phần chưa dò.
so_hong=$("$PY" -c "import json,sys; print(json.load(open(sys.argv[1],encoding='utf-8')).get('so_pmid_hong',0))" "$OUTJ" 2>/dev/null || echo "0")
# mã 1 = CÓ mục cần đọc lại — vẫn là một lượt quét THÀNH CÔNG; mã ≥2, kết luận khác SACH/CO_BAI_MOI,
# hoặc còn PMID chưa hỏi được (so_hong>0) đều là CHƯA đo xong.
tong="PASS"
{ [ "$rc" -ge 2 ] || { [ "$ket_luan" != "SACH" ] && [ "$ket_luan" != "CO_BAI_MOI" ]; } || [ "${so_hong:-0}" != "0" ]; } && tong="CÓ BƯỚC LỖI"
# rc=1 do lỗi ghi tệp (không phải «có phát hiện»): chỉ tin rc=1 khi manifest nói CO_BAI_MOI
[ "$rc" -eq 1 ] && [ "$ket_luan" != "CO_BAI_MOI" ] && rc=2
# Alert khi có phát hiện (mã 1): một dòng vào alerts/ để bác sĩ thấy ngay đầu phiên.
if [ "$rc" -eq 1 ]; then
  AD="$HUB/alerts"; mkdir -p "$AD"
  AF="$AD/$(date '+%Y-%m-%d').md"
  [ -f "$AF" ] || printf '# CẢNH BÁO KHẨN — %s\n\n' "$(date '+%Y-%m-%d')" >> "$AF"
  n=$(grep -c "▸ PMID" "$OUT" 2>/dev/null || echo "?")
  if [ "${so_hong:-0}" != "0" ]; then
    printf -- "- 🟠 QUÉT QUÝ: %s mục 'apply' có tổng quan/guideline MỚI HƠN — NHƯNG %s PMID KHÔNG hỏi được (lượt dò MỘT PHẦN, chưa đủ để kết luận phần còn lại «sạch») — đọc %s\n" "$n" "$so_hong" "$OUT" >> "$AF"
  else
    printf -- "- 🟠 QUÉT QUÝ: %s mục 'apply' có tổng quan/guideline MỚI HƠN — đọc %s\n" "$n" "$OUT" >> "$AF"
  fi
fi
# Mã ≥2 = KHÔNG hỏi được PubMed (hoặc lỗi): báo cáo KHÔNG dùng để kết luận «không có bài mới hơn». Trước đây chỉ vào log,
# nên bác sĩ không biết lượt quý đã hỏng — nay có một dòng ở alerts/ (cùng khuôn với nhánh mã 1).
if [ "$rc" -ge 2 ] || [ "$tong" != "PASS" ]; then
  AD="$HUB/alerts"; mkdir -p "$AD"
  AF="$AD/$(date '+%Y-%m-%d').md"
  [ -f "$AF" ] || printf '# CẢNH BÁO KHẨN — %s\n\n' "$(date '+%Y-%m-%d')" >> "$AF"
  printf -- "- 🟠 QUÉT QUÝ KHÔNG HOÀN TẤT (mã %s, kết luận %s): không dò xong toàn kho — %s KHÔNG dùng để kết luận «không có bài mới hơn»; chạy lại khi NCBI thông.\n" "$rc" "${ket_luan:-không-có-manifest}" "$OUT" >> "$AF"
fi
echo "===== $(date '+%Y-%m-%d %H:%M:%S') : KẾT THÚC — bước (1)=$rc, tổng thể=$tong =====" >> "$LOG"
exit 0
