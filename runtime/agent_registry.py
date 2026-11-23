"""
Agent Registry — liên kết agent source với offline runtime.

V4.1: Hai mode tường minh, fail-closed trong FULL_SCOPE_A.

  BUNDLE_RUNTIME_ONLY:
    Registry disabled. Không có agent source, không có hash claim.
    make_trace() bị cấm — không được tuyên bố agent-source hash binding
    khi không có thực thể agent nào được nạp.

  FULL_SCOPE_A:
    Yêu cầu .claude/agents/ và manifest phải tồn tại.
    Fail hard khi bất kỳ điều kiện nào sau đây không đạt:
      - manifest missing
      - agents dir missing
      - count < MINIMUM_AGENT_COUNT
      - required agents missing
      - bất kỳ agent hash None
      - bất kỳ agent hash mismatch với manifest
    make_trace() chỉ hoạt động trong FULL_SCOPE_A với hash thật.

Tuyên bố bắt buộc (chỉ dùng được trong FULL_SCOPE_A):
  Agent source referenced and hash-bound in offline simulation.
  Live Agent execution not verified.
"""

import csv
import dataclasses
import enum
import hashlib
import pathlib
from typing import Dict, List, Optional

BASE_DIR = pathlib.Path(__file__).parent.parent  # medical-ebm-automation/
# V4.3.2.1 (reproducibility): ưu tiên agent source VENDORED trong repo (để
# `git archive` tự-chứa); fallback về cây OneDrive-root khi chạy ngoài archive.
# CHỈ là path resolution — KHÔNG đổi logic nạp/verify (vẫn hash-verify theo manifest).
_IN_REPO_AGENTS_DIR = BASE_DIR / ".claude" / "agents"
_PARENT_AGENTS_DIR = BASE_DIR.parent / ".claude" / "agents"
AGENTS_DIR = _IN_REPO_AGENTS_DIR if _IN_REPO_AGENTS_DIR.exists() else _PARENT_AGENTS_DIR

# V4.2.1 (GAP-009): manifest hiệu lực được đưa VÀO repo/version control.
# Registry KHÔNG còn phụ thuộc manifest ở thư mục OneDrive ngoài repo.
IN_REPO_MANIFEST_PATH = BASE_DIR / "runtime" / "manifests" / "agent_source_manifest.csv"
SCOPE_A_MANIFEST_PATH = IN_REPO_MANIFEST_PATH  # tương thích tên cũ; trỏ manifest in-repo

# Self-check: SHA-256 của CHÍNH file manifest in-repo (chống sửa lén manifest).
# Cập nhật giá trị này khi tái sinh manifest có chủ đích (baseline đã khóa V4.2.1).
# Tái sinh 2026-07-05 (lần 2): nội dung theo-doi-benh-man.md cập nhật guideline
# THA/lipid (2017/2018/2019 → 2025 AHA/ACC + bản hiện hành) → hash trôi lại dù
# số agent (50) không đổi. BÀI HỌC: manifest phải tái sinh sau MỌI lần sửa NỘI
# DUNG agent, không chỉ khi số lượng đổi → chạy
# `scripts/regenerate_agent_manifest.py --write` rồi dán giá trị self-check mới
# vào đây MỖI LẦN sync agent .md đã sửa sang medical-ebm-automation/.claude/agents/.
# Tái khóa 2026-09-03: 6 agent được nâng ICH E6(R3) Annex 2/QUADAS-3 v1.2
# và hợp đồng điều phối khép kín; số lượng vẫn giữ nguyên 50.
# Tái khóa 2026-09-20: `ke-don-an-toan` (mục 8 chuẩn hoá tên thuốc RxNorm + trạng thái EMA) và
# `khoang-trong-nghien-cuu` (mục 5 bối cảnh WHO GHO); số lượng vẫn giữ nguyên 50.
# Tái khóa 2026-09-26: `tra-cuu-chung-cu` + `huong-dan-lam-sang` nối lệnh đọc toàn văn guideline
# (tools/toan_van_guideline.py); số lượng vẫn giữ nguyên 50.
# Tái khóa 2026-09-28: `cong-cu-do-luong` nối lệnh độ tin cậy thang đo trên dữ liệu pilot
# (tools/kiem_tin_cay_thang_do.py) + lệnh CVI/phỏng vấn nhận thức (tools/pha_phat_trien_cong_cu.py);
# số lượng vẫn giữ nguyên 50.
# Tái khóa 2026-10-01: `ke-don-an-toan` (mục 8 dạy in một lần, nguyên văn dòng `mien_tru_nlm` của NLM khi trình
# kết quả `chuan-hoa` — trỏ `_CONNECTOR-CHUNG-CU.md` §1ter luật 5); số lượng vẫn giữ nguyên 50.
# Tái khóa 2026-10-03: `tham-dinh-dau-ra` (R6 dạy ô mẫu khuôn sinh không nhãn + §6bis biên nhận máy, gốc 21d95d1),
# `dao-duc-dang-ky` (đính chính Annex 2 lạc hậu), `dieu-phoi-nghien-cuu`, `viet-ban-thao` (bản cặp y hệt gốc); vẫn 50.
# Tái khóa 2026-10-04: `dieu-phoi-nghien-cuu` (điều phối thống nhất xuyên cổng · G10-AUTO-11 · G1-AUTO-02c · SAP
# §4/§9) + `thiet-ke-nghien-cuu` (khoá SAP đòi §4/§9) + README/_BAN-DO-KET-NOI/_SO-DO-PIPELINE-HOP-NHAT (G0–G10) — bản
# cặp y hệt gốc; vẫn 50.
# Tái khóa 2026-10-06 (soát từng cổng — doctrine CHUNG-I): 11 agent nghiên cứu (dieu-phoi-nghien-cuu,
# cau-hoi-nghien-cuu, thiet-ke-nghien-cuu, ke-hoach-trien-khai, dao-duc-dang-ky, co-mau-nghien-cuu, quan-ly-du-lieu,
# phan-tich-thong-ke,
# viet-ban-thao, binh-duyet, nop-bai-phan-hoi) bỏ chỉ dẫn «agent ghi Gx_STATUS=LOCKED», tiền đề chấm sống, hợp đồng
# hiện hành từng cổng — bản cặp y hệt gốc; vẫn 50.
# 06/10/2026 (sửa đổi kết cục chính G10-07 · SAP định tính · hội đồng đưa ra giải pháp tốt nhất): 8 agent cập nhật
# doctrine (trong-tai-tranh-bien, _HOI-DONG-CONG, dieu-phoi-nghien-cuu, dieu-phoi-g10, viet-ban-thao, dao-duc-dang-ky,
# thiet-ke-nghien-cuu, nghien-cuu-dinh-tinh) — bản cặp y hệt gốc; vẫn 64.
# 07/10/2026 (thu hẹp nhánh tương thích G2 kiểu cũ): 2 agent (dao-duc-dang-ky, dieu-phoi-g2) dạy luật mới — bản cặp
# y hệt gốc; vẫn 64.
# 07/10/2026 (trọng tài Codex — tools/trong_tai_codex.py): _HOI-DONG-CONG, dieu-phoi-nghien-cuu, trong-tai-tranh-bien
# dạy cách chạy chế độ codex — bản cặp y hệt gốc; vẫn 64. 19/11/2026: chế độ Codex GỠ (bác sĩ không còn dùng); vẫn 64.
# 09/10/2026 (G0 chấm lại ≠ dựng lại — hội đồng BD-G0-T1/T2): dieu-phoi-g0 dạy hành vi mới của run_pipeline — bản cặp
# y hệt gốc; vẫn 64.
# 09/10/2026 (trách nhiệm cổng — bác sĩ giao điều phối cổng chịu trách nhiệm kết quả cổng): 11 dieu-phoi-gN thêm mục 4b
# + _HOI-DONG-CONG §1b + dieu-phoi-nghien-cuu «giao cổng — nhận cổng» — bản cặp y hệt gốc; vẫn 64.
# 10/10/2026 (trách nhiệm TỪNG agent — tools/sinh_tai_lieu_trach_nhiem.py): 23 agent làm/chấm chéo nhiệm vụ cổng thêm
# khối «Trách nhiệm trong hội đồng cổng», 11 dieu-phoi-gN mục 4b sinh lại, quan-ly-du-lieu sửa lệnh khoá dữ liệu —
# bản cặp y hệt gốc; vẫn 64.
# 10/10/2026 (hợp đồng bộ biến G3 — _bo-bien-rieng.csv): bien-so-nghien-cuu, quan-ly-du-lieu, dieu-phoi-g3 dạy tệp hợp
# đồng + kiểm máy cấp nhiệm vụ; dieu-phoi-nghien-cuu dạy `trach-nhiem --gate ALL` — bản cặp y hệt gốc; vẫn 64.
# 10/10/2026 (tiền đề §2 sinh từ PHAN_CONG + kiểm máy G4-T2): 11 dieu-phoi-gN, an-toan-nghien-cuu — bản cặp y hệt gốc;
# vẫn 64.
# 10/10/2026 (G1-T4 hợp đồng pha_cong_cu + `khai-ap-dung`): 11 dieu-phoi-gN mục 4b quy tắc 5, cong-cu-do-luong,
# _HOI-DONG-CONG §1b mục 9 — bản cặp y hệt gốc; vẫn 64.
# 10/10/2026 (kiểm máy G1-T5 — hai dòng an toàn đề cương lõi RCT): an-toan-nghien-cuu, dieu-phoi-g1, _HOI-DONG-CONG §1b
# mục 7 — bản cặp y hệt gốc; vẫn 64.
# 10/10/2026 (G6-AUTO-09 có chủ theo thiết kế «G6-T2|G6-T1»): meta-phan-tich, phan-tich-thong-ke, dieu-phoi-g6,
# _HOI-DONG-CONG §1b — bản cặp y hệt gốc; vẫn 64.
# 10/10/2026 (mỗi agent có nhiệm vụ + điều phối kiểm soát): 4 agent mồ côi vào nhiệm vụ cổng (G1-T6/T7/T8, G5-T2,
# G6-T4/T5), 21 agent lâm sàng thêm khối «Nhiệm vụ & kiểm soát trong ca lâm sàng» sinh từ bảng dieu-phoi-lam-sang
# (thêm C8c) — bản cặp y hệt gốc; vẫn 64.
# 10/10/2026 (bác sĩ quyết G6-T3 + G10-T3): dien-giai-ket-qua dạy G6_DIEN_GIAI_<mã>.md, so-cai-ghi-nho/
# dieu-phoi-nghien-cuu dạy sổ trạng thái RIÊNG mỗi đề tài — bản cặp y hệt gốc; vẫn 64.
# 10/10/2026 (tiêu chuẩn hoàn thiện agent/điều phối): kinh-te-y-te (G1_KINH_TE_Y_TE), hieu-dinh-song-ngu
# (G7_A8_MANUSCRIPT_EN), dieu-phoi-g1/g7 §3, _HOI-DONG-CONG §1b mục 12 — bản cặp y hệt gốc; vẫn 64.
# 10/10/2026 (hội đồng G0, DG G0-T3/T4): tong-quan-y-van (G0_TONG_HOP_BANG_CHUNG), khoang-trong-nghien-cuu
# (G0_KHOANG_TRONG), dieu-phoi-g0 (--dung-lai-a1) — hợp đồng đầu ra + khối trách nhiệm hiện kiểm máy cấp nhiệm vụ;
# bản cặp y hệt gốc; vẫn 64.
# 10/10/2026 (A7 giao nhiệm vụ + tiêu chí kết quả): giam-khao-cong, phan-bien-tranh-bien, trong-tai-tranh-bien nói rõ
# đầu ra bị kiểm bằng `hoi_dong_cong.py ghi`; bản cặp y hệt gốc; vẫn 64.
# 11/10/2026 (bác sĩ quyết — dấu vân tay G0 băm danh mục đọc bổ sung): dieu-phoi-g0 sửa câu «dựng lại A1 không đổi dấu»
# ⇒ danh mục đổi thì PI chốt lại; bản cặp y hệt gốc; vẫn 64.
# 11/10/2026 (G10 trước dữ liệu — y khoa #122): dieu-phoi-g2/g4 dạy «chạy lại khi bản đã biên tập ⇒ giữ nguyên,
# làm tươi checkpoint, mã 2 là đúng»; dieu-phoi-g10 dạy thứ tự gói ETHICS_SUBMISSION; bản cặp y hệt gốc; vẫn 64.
# 13/10/2026 (diễn tập đường PI C1a): dao-duc-dang-ky thêm 4e «ghép từ hệ thống ngoài phải nói ra ở ICF + DMP» +
# khối trách nhiệm sinh lại (kiểm máy G2-T1); dieu-phoi-g2 §7 thêm dòng tương ứng; bản cặp y hệt gốc; vẫn 64.
# 15/10/2026 (rà làn Chrome/EndNote): cap-nhat-guideline mã 1 của doc_toan_van_pmc đi theo điều khoản NXB
# (§2septies) thay cho «đọc trên trang tạp chí qua quyền truy cập của bác sĩ»; bản cặp y hệt gốc; vẫn 64.
# 15/10/2026 (bản đề cương nộp Hội đồng): dieu-phoi-g10 thêm mục 5 — DE_CUONG_NOP_HOI_DONG vào manifest G10 và phạm vi
# A12; bản cặp y hệt gốc; vẫn 64. Cùng ngày: nhiệm vụ G10-T4 (viet-ban-thao soạn đề cương nộp Hội đồng) — sinh lại khối
# trách nhiệm của dieu-phoi-g10/viet-ban-thao/tham-dinh-dau-ra/kiem-chung-trich-dan; vẫn 64.
# 17/10/2026 (hội đồng G0 C1a, G0-T3): tong-quan-y-van thêm hợp đồng nhánh KHÔNG lọc + mức bằng chứng sau sàng lọc;
# bản cặp y hệt gốc; vẫn 64.
# 24/10/2026 (bác sĩ gỡ plugin aipoch): dieu-phoi-nghien-cuu + _PLUGIN-ROUTING-CONTRACT bỏ worker aipoch; bản cặp y hệt
# gốc; vẫn 64.
# 12/11/2026: thang-diem-nguy-co chép bản chuẩn của repo gốc (#316, 08/11 — 7 máy tính lý do khám ngoại trú); vẫn 64.
# 14/11/2026: sinh lại khối TRÁCH NHIỆM (máy sinh) của dieu-phoi-g6 + phan-tich-thong-ke cho G6-AUTO-11; vẫn 64.
# 14/11/2026 (lượt 2): phan-tich-thong-ke thêm BƯỚC 0c — kiểm chéo bằng SPSS (tools/cau_noi_spss.py), chép bản chuẩn của
# repo gốc; vẫn 64.
# 14/11/2026 (lượt 3): phan-tich-thong-ke — luật đọc đối chiếu SPSS theo ngưỡng mới (SE, thang log, p khác phía 0,05,
# chốt SHA/đặc tả) + đồng bộ đoạn G6-AUTO-11 đã có ở repo gốc; vẫn 64.
# 14/11/2026 (gộp #230): bản cặp A12/G6-AUTO-11/bình duyệt độc lập từ nhánh nền + luật đọc SPSS mới; vẫn 64.
# 14/11/2026 (lượt 4): phan-tich-thong-ke — đọc dòng đối chiếu phân tích SPSS bổ sung (GENLINMIXED, Complex
# Samples, RELIABILITY, OR từng ngưỡng) + .sps xem trước ở run_g6_auto; vẫn 64.
# 14/11/2026 (lượt 3, #236): phan-tich-thong-ke thêm BƯỚC 0d — kiểm chéo bằng R (tools/cau_noi_r.py), cặp y hệt repo
# gốc; vẫn 64.
# 14/11/2026 (gộp #236 vào #234/#237): phan-tich-thong-ke = bản master repo gốc (0c SPSS + bổ sung + 0d R); vẫn 64.
# 14/11/2026 (gói tự động hoá A–D): dieu-phoi-g6 + phan-tich-thong-ke — lệnh kiểm chéo một cửa kiem_cheo_g6.py;
# vẫn 64.
# 14/11/2026 (tầng 5, việc N): trich-xuat-y-van + tham-dinh-dau-ra — dạy đọc 🟠 kiểm chéo ngữ nghĩa ④-bis/④-ter
# (K1–K4 + K3b/K4b, CẢNH BÁO), cặp y hệt repo gốc; vẫn 64.
# 15/11/2026 (R10, việc D): dạy 6 agent luật mới của giả lập RCT (G1 thứ tự ưu tiên thiết kế + 02d, G4-HUMAN-03
# theo vai, G6 nhận G4 sống — N1, khuôn theo SAP §5 — N6, Branching Logic khi làm sạch — N2) + bắt kịp
# bien-so-nghien-cuu/phan-tich-thong-ke/quan-ly-du-lieu của gốc #372/#375; cặp y hệt repo gốc; vẫn 64.
# 15/11/2026: dieu-phoi-g5 + quan-ly-du-lieu (G5-AUTO-11 vào bảng trách nhiệm) · giam-khao-cong + _HOI-DONG-CONG (RQ4
# chấm trên số đo nhat_quan_xuyen_cong) — cặp y hệt repo gốc #376; vẫn 64.
# 15/11/2026: co-mau-nghien-cuu + dieu-phoi-g3 + thiet-ke-nghien-cuu (đồng bộ cỡ mẫu & kỹ thuật chọn mẫu — 4 trục
# nhat_quan_xuyen_cong) — cặp y hệt repo gốc #378; vẫn 64.
# 15/11/2026: cau-hoi-nghien-cuu + dao-duc-dang-ky + dieu-phoi-g0 (đồng bộ vấn đề · câu hỏi · tên đề tài — trục
# ten_de_tai, cau_hoi_gia_thuyet) — cặp y hệt repo gốc nhánh claude/van-de-cau-hoi-20261115; vẫn 64.
# 15/11/2026: thu-thu-tai-lieu + kiem-chung-trich-dan + dieu-phoi-g0/g1 + dieu-phoi-nghien-cuu (đồng bộ tổng quan
# tài liệu — trục trich_dan_tong_quan) — cặp y hệt repo gốc nhánh claude/tong-quan-tai-lieu-20261115; vẫn 64.
# 15/11/2026: bien-so-nghien-cuu + thiet-ke-nghien-cuu + dieu-phoi-g1/g4 (đồng bộ giai đoạn mục tiêu — trục
# ma_tran_muc_tieu, MT-11) — cặp y hệt repo gốc nhánh claude/muc-tieu-20261115; vẫn 64.
# 15/11/2026: dieu-phoi-g0/g1/g7 + thu-thu-tai-lieu + phan-tich-thong-ke + viet-ban-thao (R10 — K4 khái niệm chuẩn
# G0, N4-G1, G7 Kết quả từ G6) — cặp y hệt repo gốc nhánh claude/r10-day-agent-20261115; vẫn 64.
# 15/11/2026: dieu-phoi-g1 + dieu-phoi-g2 + thiet-ke-nghien-cuu (ghim thiết kế cần dấu người, G2 thôi gieo
# design_code — thẩm định #277/#281) — dòng y hệt repo gốc nhánh claude/ghim-thiet-ke-dau-nguoi-20261115; vẫn 64.
# 15/11/2026: CẢ 64 agent — luật chung «Ô QUYẾT ĐỊNH CỦA NGƯỜI — máy KHÔNG gieo» trong khối guardrail cuối (cặp
# OLD_KET_THUC/NEW_KET_THUC của enforce_agent_guardrails.py repo gốc, nhánh claude/day-agent-sau-tham-dinh-277-281).
# 15/11/2026: bien-so-nghien-cuu + quan-ly-du-lieu + dieu-phoi-g3/g5 (hoàn thiện hệ thống SPSS/R: soan-tu-calc,
# dien_tap_spss_r) — dòng y hệt repo gốc nhánh claude/day-agent-sau-tham-dinh-277-281; vẫn 64.
# 17/11/2026: viet-ban-thao, kiem-chung-trich-dan, bien-so-nghien-cuu, thiet-ke-nghien-cuu, co-mau-nghien-cuu,
# dao-duc-dang-ky (trục xuyên cổng sau giả lập 16 đề tài) — y hệt repo gốc nhánh
# claude/truc-xuyen-cong-sau-gia-lap-20261117; vẫn 64.
# 17/11/2026 (chiều): viet-ban-thao, dao-duc-dang-ky (bản vá đo trên đề cương BTM thật) — y hệt repo gốc nhánh
# claude/de-cuong-btm-sau-a12-20261117; vẫn 64.
# 17/11/2026 (tối): kiem-chung-trich-dan, binh-duyet, _HOI-DONG-CONG (kết nối Claude API: ba công cụ tư vấn) — y hệt
# repo gốc nhánh claude/api-claude-nghien-cuu-20261117; vẫn 64.
# 17/11/2026 (khuya): viet-ban-thao, thiet-ke-nghien-cuu (dấu vết máy lộ khi phản biện máy Claude API đọc đề cương
# BTM) — y hệt repo gốc nhánh claude/de-cuong-dau-vet-api-20261117; vẫn 64.
# 18/11/2026: kiem-chung-trich-dan, thu-thu-tai-lieu, dieu-phoi-g10 (trích dẫn đề tài phải có toàn văn — G10-AUTO-12)
# — y hệt repo gốc nhánh claude/bien-nhan-toan-van-tltk-20261118; vẫn 64.
# 18/11/2026 (chiều): ba agent trên thêm bước 5 «giữ trích dẫn đạt chuẩn» (bác sĩ cho riêng C1a) — vẫn 64.
# 19/11/2026: tong-quan-y-van — `rut_bai.pmid_da_kiem`/`doi_da_kiem` có cấu trúc (bộ đối chiếu xuyên cổng không đọc
# câu văn nữa) — y hệt repo gốc nhánh claude/rut-bai-g0-co-cau-truc-20261119; + kiem-chung-trich-dan (câu văn báo
# cáo A12 không còn tính là đã kiểm rút bài) — y hệt repo gốc nhánh claude/a12-khong-doc-cau-van-20261119; vẫn 64.
# 19/11/2026: dạy `dao-duc-dang-ky` dùng `tools/ho_so_hdd_bvqy175.py` khi nộp Hội đồng Đạo đức BVQY175 — vẫn 64.
# 19/11/2026 (chiều): `dao-duc-dang-ky` sửa căn cứ miễn đồng thuận (Helsinki §32 · CIOMS HD10 · TT43 Điều 7 khoản 1
# điểm b, thay «TT43 Điều 15 · §29» sai) và bỏ cờ «dữ liệu nhận dạng được → ICF bắt buộc» — vẫn 64.
# 19/11/2026 (tối): dạy `viet-ban-thao` + `phan-tich-thong-ke` biểu bảng chuẩn (khung_bieu_bang, K9, trình bày kết quả
# G6) — vẫn 64.
# 20/11/2026: bản sao `cap-nhat-guideline` đồng bộ với nguồn gốc (gốc #447 thêm mục «apply KHÔNG có PMID» — bằng chứng
# đã đọc nguồn chính thức) — vẫn 64.
# 20/11/2026 (chiều): dạy `viet-ban-thao` + `kiem-chung-trich-dan` luật «số liệu phải có chứng cứ thực» (bác sĩ: «Không
# có số liệu thực, chứng cứ thực hãy loại bỏ»), chốt máy K10 — vẫn 64.
# 20/11/2026 (tối): dạy `viet-ban-thao`, `thiet-ke-nghien-cuu`, `dieu-phoi-g10` chuẩn trình bày văn bản nộp (K11, K9
# «mỗi mức một dòng») — vẫn 64.
# 20/11/2026 (tối, lượt 2): dạy `co-mau-nghien-cuu` đo lại chi tiết con số phụ của cỡ mẫu — vẫn 64.
# 20/11/2026 (tối, lượt 3): bản sao `cap-nhat-guideline` (gốc #454 — cổng «đọc nguồn chính thức» nay CHẶN, có sổ nợ)
# và `_CONNECTOR-CHUNG-CU.md` (gốc #456 — thêm ASM vào bảng điều khoản NXB) đồng bộ với nguồn gốc — vẫn 64.
# 20/11/2026 (tổng quan tài liệu): bản sao `viet-ban-thao`, `dieu-phoi-g10`, `kiem-chung-trich-dan`, `thu-thu-tai-lieu`
# học K12 (mỗi tài liệu đỡ một câu), K13 (TLTK Vancouver theo metadata A12) và `kiem_so_lieu_toan_van.py` — vẫn 64.
# 21/11/2026: đồng bộ bản sao _HOI-DONG-CONG.md, kiem-chung-trich-dan.md với nguồn gốc (tools/dong_bo_agent_y_khoa.py).
# 21/11/2026: đồng bộ bản sao thu-thu-tai-lieu.md, tong-quan-y-van.md với nguồn gốc (tools/dong_bo_agent_y_khoa.py).
# 21/11/2026: dạy `thang-diem-nguy-co` 12 bộ tính mới + luật gọi bộ tính (bảng BO_TINH_THEO_SCORE_ID) — vẫn 64.
# 21/11/2026 (hồ sơ DTCS): `ke-hoach-trien-khai` + `dieu-phoi-g1` học `tools/ho_so_dtcs_bvqy175.py` (#379) — vẫn 64.
# 21/11/2026: đồng bộ bản sao cong-cu-do-luong.md, kinh-te-y-te.md, meta-phan-tich.md, mo-hinh-tien-luong.md,
# phan-tich-thong-ke.md, tham-dinh-do-chinh-xac-chan-doan.md, viet-ban-thao.md với nguồn gốc
# (tools/dong_bo_agent_y_khoa.py).
# 21/11/2026: bản sao `cong-cu-do-luong`, `phan-tich-thong-ke` học dùng `tools/phan_tich_nhan_to_r.py` (EFA nửa 1 + CFA
# nửa 2, PR y khoa #384) thay vì tự viết script R — chỉ phần đoạn mới; mục «Biểu đồ» đi theo PR #383 — vẫn 64.
# 21/11/2026 (khuôn hướng dẫn chung BVQY175): bản sao `dieu-phoi-g10`, `kiem-chung-trich-dan`, `viet-ban-thao` học
# khuôn đề cương + K14 (cặp của gốc #473) — vẫn 64.
# 21/11/2026: kiem-chung-trich-dan + binh-duyet — phát hiện máy do hệ tự phân xử (PR cặp gốc #476).
# 21/11/2026 (b): kiem-chung-trich-dan — sửa câu tỷ lệ bệnh ghi đúng tiêu chuẩn của nguồn (PR cặp gốc #476).
# 21/11/2026 (c): viet-ban-thao + kiem-chung-trich-dan — K15 khẳng định mơ hồ không nguồn (PR cặp gốc #476).
# 21/11/2026 (d): tong-quan-y-van — xếp mức liên quan G0 đúng thang + nguyên tắc áp dụng (PR cặp gốc #476).
# 21/11/2026 (e): kiem-chung-trich-dan + viet-ban-thao — K16 phạm vi tìm khớp nhật ký PRISMA-S (PR cặp gốc #476).
# 21/11/2026: gỡ dòng ⚠️ «#384 CHƯA gộp» đã lỗi thời ở bản sao `cong-cu-do-luong`, `phan-tich-thong-ke` (đồng bộ nguồn
# gốc) — vẫn 64.
# 21/11/2026 (f): viet-ban-thao + thiet-ke-nghien-cuu — K17 đủ từng mục chuẩn của thiết kế (PR cặp gốc #476).
# 21/11/2026 (h): 7 agent — K17 mở rộng 12 chuẩn (viet-ban-thao, thiet-ke-nghien-cuu, tong-quan-y-van,
# mo-hinh-tien-luong, tham-dinh-do-chinh-xac-chan-doan, nghien-cuu-dinh-tinh, kinh-te-y-te) — vẫn 64.
# 22/11/2026: 2 agent — kiểm toàn hệ 11 khâu, luật khâu 9–10 (dien-giai-ket-qua, viet-ban-thao) — vẫn 64.
# 22/11/2026 (K18): 4 agent — bản thảo đạt từng mục chuẩn báo cáo (viet-ban-thao, binh-duyet, nop-bai-phan-hoi,
# dieu-phoi-g7; PR cặp gốc #481) — vẫn 64.
# 22/11/2026 (K18 PRISMA): 5 agent — PRISMA 2020 theo từng mục cho bản thảo tổng quan (viet-ban-thao, binh-duyet,
# dieu-phoi-g7, tong-quan-y-van, meta-phan-tich; PR #409, cặp gốc #484 — đã gộp) — vẫn 64; 6 agent K18 khớp từng
# byte origin/master của repo gốc.
# 22/11/2026 (K19 + khối ký bìa phụ): 3 agent — dieu-phoi-g10, viet-ban-thao, tham-dinh-dau-ra học chốt K19 và luật
# khối ký thứ ba theo đơn vị ngay trên Khoa (mã ở PR #419; cặp gốc EBM-drluanbv175#490) — vẫn 64.
# 22/11/2026 (sổ phân công công cụ C1–C6): 23 agent nhận dòng «Công cụ `tools/x.py` (chủ|kiểm|dùng phụ)» theo
# config/phan_cong_cong_cu.json, chép từ nhánh gốc claude/phan-cong-goc-20261122 — vẫn 64.
# 23/11/2026: chép 2 agent từ nguồn gốc (tools/dong_bo_agent_y_khoa.py --vao).
# 23/11/2026: chép 4 agent từ nguồn gốc (tools/dong_bo_agent_y_khoa.py --vao).
# 23/11/2026: thêm dòng doctrine hệ nhập liệu cục bộ (tools/nhap_lieu_cuc_bo.py) vào quan-ly-du-lieu + dieu-phoi-g5.
MANIFEST_SELF_CHECK_SHA256 = (
    "14b35ffd0ba36a02a1288d3a7e2f7a4c53ccd58c5174bb5cbbe11fe7633cf72e"
)

MINIMUM_AGENT_COUNT = 64
# V4.2.1 (GAP-001): hard-enforce đủ 4 agent trọng yếu (2 nhạc trưởng + guardrail
# chốt kiểm cuối + sổ cái). Thiếu bất kỳ agent nào → registry fail-closed.
REQUIRED_AGENTS = frozenset({
    "dieu-phoi-nghien-cuu",
    "dieu-phoi-lam-sang",
    "tham-dinh-dau-ra",
    "so-cai-ghi-nho",
})


class AgentManifestSelfCheckError(AssertionError):
    """Manifest in-repo bị sửa đổi: SHA-256 không khớp giá trị khóa baseline."""

_POLICY_DEPS_MAP: Dict[str, List[str]] = {
    "dieu-phoi-lam-sang":     ["GATE_A", "GATE_B", "PII_EGRESS", "G9"],
    "dieu-phoi-nghien-cuu":   ["G2", "G4", "G9", "GATE_B"],
    "tham-dinh-dau-ra":       ["PII_EGRESS", "AUTO_SUBMIT", "RAW_DATA_WRITE"],
    "dao-duc-dang-ky":        ["G2"],
    "thiet-ke-nghien-cuu":    ["G4"],
    "phan-tich-thong-ke":     ["G4", "G9"],
    "ke-don-an-toan":         ["GATE_A", "PII_EGRESS"],
    "so-cai-ghi-nho":         ["GATE_B"],
    "an-toan-nghien-cuu":     ["G2", "GATE_B"],
    "quan-ly-du-lieu":        ["G4", "G5", "PII_EGRESS", "RAW_DATA_WRITE"],
    "kiem-chung-trich-dan":   ["GATE_B"],
    "viet-ban-thao":          ["G9", "GATE_B"],
    "nop-bai-phan-hoi":       ["G9", "AUTO_SUBMIT"],
}
_DEFAULT_POLICY_DEPS = ["PII_EGRESS"]


class RegistryMode(enum.Enum):
    """Hai mode tường minh của AgentRegistry."""
    BUNDLE_RUNTIME_ONLY = "BUNDLE_RUNTIME_ONLY"
    FULL_SCOPE_A = "FULL_SCOPE_A"


def _compute_sha256(path: pathlib.Path) -> Optional[str]:
    """Tính SHA256 của file. Trả None nếu không tồn tại."""
    if not path.exists():
        return None
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


@dataclasses.dataclass
class AgentRegistryEntry:
    """Thông tin đăng ký của một agent trong phạm vi offline."""
    agent_id: str
    agent_path: str
    agent_source_hash: Optional[str]
    policy_dependencies: List[str]
    allowed_runtime: str
    source_file_exists: bool
    hash_verified: bool


class AgentRegistryDisabledError(RuntimeError):
    """Gọi make_trace() trong BUNDLE_RUNTIME_ONLY mode."""


class AgentRegistryIntegrityError(AssertionError):
    """Lỗi tính toàn vẹn trong FULL_SCOPE_A mode."""


class AgentRegistry:
    """
    Registry liên kết agent source với offline runtime.

    TUYÊN BỐ BẮT BUỘC (chỉ áp dụng khi mode=FULL_SCOPE_A):
      Agent source referenced and hash-bound in offline simulation.
      Live Agent execution not verified.
    """

    EXECUTION_STATEMENT = (
        "Agent source referenced and hash-bound in offline simulation. "
        "Live Agent execution not verified."
    )

    def __init__(self, mode: RegistryMode = RegistryMode.BUNDLE_RUNTIME_ONLY):
        self._mode = mode
        self._entries: Dict[str, AgentRegistryEntry] = {}
        self._manifest_sha256_map: Dict[str, str] = {}

        if mode == RegistryMode.BUNDLE_RUNTIME_ONLY:
            # Registry disabled — không nạp agents, không có hash claim.
            pass
        elif mode == RegistryMode.FULL_SCOPE_A:
            self._load_manifest_hashes_strict()
            self._load_from_agents_dir_strict()
            self._validate_full_scope_a()

    # ── BUNDLE_RUNTIME_ONLY: không làm gì thêm ────────────────────────────────

    # ── FULL_SCOPE_A: load và validate ────────────────────────────────────────

    def _load_manifest_hashes_strict(self) -> None:
        """Nạp SHA256 từ manifest in-repo; fail hard nếu thiếu hoặc self-check sai."""
        if not SCOPE_A_MANIFEST_PATH.exists():
            raise AgentRegistryIntegrityError(
                f"FULL_SCOPE_A mode: in-repo manifest required but missing: "
                f"{SCOPE_A_MANIFEST_PATH}"
            )
        # V4.2.1 (GAP-009): self-check hash của chính file manifest trước khi tin.
        manifest_bytes = SCOPE_A_MANIFEST_PATH.read_bytes()
        actual_self = hashlib.sha256(manifest_bytes).hexdigest()
        if actual_self != MANIFEST_SELF_CHECK_SHA256:
            raise AgentManifestSelfCheckError(
                "FULL_SCOPE_A mode: manifest self-check FAILED. "
                f"Expected {MANIFEST_SELF_CHECK_SHA256[:16]}…, got {actual_self[:16]}…. "
                "Manifest in-repo có thể đã bị sửa đổi — fail-closed."
            )
        with open(SCOPE_A_MANIFEST_PATH, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                path_key = row.get("path", "")
                sha = row.get("sha256", "")
                if path_key and sha and ".claude/agents/" in path_key:
                    agent_id = pathlib.Path(path_key).stem
                    self._manifest_sha256_map[agent_id] = sha

    def _load_from_agents_dir_strict(self) -> None:
        """Nạp registry từ .claude/agents/; fail hard nếu thư mục không tồn tại."""
        if not AGENTS_DIR.exists():
            raise AgentRegistryIntegrityError(
                f"FULL_SCOPE_A mode: agents dir required but missing: {AGENTS_DIR}"
            )
        for md_file in sorted(AGENTS_DIR.glob("*.md")):
            agent_id = md_file.stem
            if agent_id.startswith("_") or agent_id == "README":
                continue
            source_hash = _compute_sha256(md_file)
            manifest_hash = self._manifest_sha256_map.get(agent_id)
            hash_verified = (
                source_hash is not None
                and manifest_hash is not None
                and source_hash == manifest_hash
            )
            entry = AgentRegistryEntry(
                agent_id=agent_id,
                agent_path=str(md_file).replace(str(BASE_DIR.parent) + "/", ""),
                agent_source_hash=source_hash,
                policy_dependencies=_POLICY_DEPS_MAP.get(agent_id, _DEFAULT_POLICY_DEPS),
                allowed_runtime="MOCK_ONLY",
                source_file_exists=True,
                hash_verified=hash_verified,
            )
            self._entries[agent_id] = entry

    def _validate_full_scope_a(self) -> None:
        """Kiểm tra toàn vẹn: fail hard với thông điệp rõ ràng."""
        if self.count() < MINIMUM_AGENT_COUNT:
            raise AgentRegistryIntegrityError(
                f"FULL_SCOPE_A: expected >= {MINIMUM_AGENT_COUNT} agents, "
                f"found {self.count()}. Check .claude/agents/ completeness."
            )
        for required_id in REQUIRED_AGENTS:
            if required_id not in self._entries:
                raise AgentRegistryIntegrityError(
                    f"FULL_SCOPE_A: required agent missing: {required_id}"
                )
        for agent_id, entry in self._entries.items():
            if entry.agent_source_hash is None:
                raise AgentRegistryIntegrityError(
                    f"FULL_SCOPE_A: agent source hash is None: {agent_id}. "
                    "File may be unreadable."
                )
            if not entry.hash_verified:
                raise AgentRegistryIntegrityError(
                    f"FULL_SCOPE_A: agent hash mismatch: {agent_id}. "
                    f"Source hash {entry.agent_source_hash!r} does not match manifest."
                )

    # ── Public API ─────────────────────────────────────────────────────────────

    @property
    def mode(self) -> RegistryMode:
        return self._mode

    def get(self, agent_id: str) -> Optional[AgentRegistryEntry]:
        """Tra cứu entry theo agent_id (None nếu không tìm thấy hoặc BUNDLE mode)."""
        return self._entries.get(agent_id)

    def all_agents(self) -> List[AgentRegistryEntry]:
        return list(self._entries.values())

    def count(self) -> int:
        return len(self._entries)

    def verify_hash(self, agent_id: str) -> bool:
        """Xác minh SHA256 hiện tại của file khớp với lúc nạp (FULL_SCOPE_A only)."""
        if self._mode == RegistryMode.BUNDLE_RUNTIME_ONLY:
            return False
        entry = self.get(agent_id)
        if entry is None or not entry.source_file_exists:
            return False
        current_hash = _compute_sha256(AGENTS_DIR / f"{agent_id}.md")
        return current_hash == entry.agent_source_hash

    def make_trace(
        self,
        *,
        agent_id: str,
        fixture_id: str,
        policy_decision: str,
        state_transition: Optional[str] = None,
        approval_reference: Optional[str] = None,
        audit_event_id: Optional[str] = None,
    ) -> dict:
        """
        Tổng hợp trace đầy đủ cho một lần chạy offline (FULL_SCOPE_A only).

        BUNDLE_RUNTIME_ONLY: raise AgentRegistryDisabledError — không được dùng
        fixture-only trace để tuyên bố agent-source hash binding.

        Trace chứng minh chuỗi:
          agent_id → agent_source_hash → fixture_id → policy_decision
          → state_transition → approval_reference → audit_event_id
        """
        if self._mode == RegistryMode.BUNDLE_RUNTIME_ONLY:
            raise AgentRegistryDisabledError(
                "make_trace() requires FULL_SCOPE_A mode. "
                "BUNDLE_RUNTIME_ONLY does not support agent-source hash binding claims. "
                "To trace with real agent hashes, use AgentRegistry(mode=RegistryMode.FULL_SCOPE_A)."
            )
        entry = self.get(agent_id)
        return {
            "agent_id": agent_id,
            "agent_source_hash": entry.agent_source_hash if entry else None,
            "agent_found_in_registry": entry is not None,
            "agent_hash_verified": entry.hash_verified if entry else False,
            "fixture_id": fixture_id,
            "policy_decision": policy_decision,
            "state_transition": state_transition,
            "approval_reference": approval_reference,
            "audit_event_id": audit_event_id,
            "allowed_runtime": entry.allowed_runtime if entry else None,
            "live_execution_verified": False,
            "execution_statement": self.EXECUTION_STATEMENT,
            "registry_mode": self._mode.value,
        }


# ── Singleton helpers ──────────────────────────────────────────────────────────

_REGISTRY_BUNDLE: Optional[AgentRegistry] = None
_REGISTRY_FULL: Optional[AgentRegistry] = None


def get_registry(mode: RegistryMode = RegistryMode.BUNDLE_RUNTIME_ONLY) -> AgentRegistry:
    """Singleton per mode. BUNDLE_RUNTIME_ONLY mặc định (safe)."""
    global _REGISTRY_BUNDLE, _REGISTRY_FULL
    if mode == RegistryMode.BUNDLE_RUNTIME_ONLY:
        if _REGISTRY_BUNDLE is None:
            _REGISTRY_BUNDLE = AgentRegistry(mode=RegistryMode.BUNDLE_RUNTIME_ONLY)
        return _REGISTRY_BUNDLE
    else:
        if _REGISTRY_FULL is None:
            _REGISTRY_FULL = AgentRegistry(mode=RegistryMode.FULL_SCOPE_A)
        return _REGISTRY_FULL


def reset_registry() -> None:
    """Xóa singleton cache — dùng trong tests."""
    global _REGISTRY_BUNDLE, _REGISTRY_FULL
    _REGISTRY_BUNDLE = None
    _REGISTRY_FULL = None


def from_entries_for_testing(
    entries: list[AgentRegistryEntry],
) -> AgentRegistry:
    """
    Tạo AgentRegistry giả từ danh sách entries — CHỈ DÙNG TRONG TESTS.

    Bypass disk I/O và manifest check để test có thể kiểm soát registry state
    mà không cần .claude/agents/ thật. Mode luôn là BUNDLE_RUNTIME_ONLY
    (fail-closed), không claim FULL_SCOPE_A.
    """
    registry = AgentRegistry.__new__(AgentRegistry)
    registry._mode = RegistryMode.BUNDLE_RUNTIME_ONLY
    registry._entries = {e.agent_id: e for e in entries}
    registry._manifest_sha256_map = {}
    return registry
