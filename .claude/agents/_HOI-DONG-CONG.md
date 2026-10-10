# HỘI ĐỒNG CỔNG G0–G10 — điều phối tổng · điều phối cổng · agent nhiệm vụ · đánh giá chéo · tranh biện

> Tài sản hạ tầng `_*` — KHÔNG tính vào bộ đếm agent. Tạo 06/10/2026 theo yêu cầu của bác sĩ: «mỗi cổng có các Agent
> thực hiện từng nhiệm vụ cụ thể, mỗi cổng có điều phối và có điều phối tổng; có cơ chế đánh giá chất lượng đầu ra
> giữa các Agent; có cơ chế tranh biện trước khi đưa ra kết luận cuối cùng».
> Tầng máy-kiểm-được: `medical-ebm-automation/tools/hoi_dong_cong.py` — **nguồn sự thật DUY NHẤT** của danh mục
> nhiệm vụ, ma trận đánh giá chéo và điểm quyết định (DP); test `tests/test_hoi_dong_cong_20261006.py` đối chiếu bảng
> trong từng `dieu-phoi-gN.md` với danh mục đó (lệch ⇒ đỏ). In danh mục: `python3 tools/hoi_dong_cong.py danh-muc`.

## 1. Ba tầng — một chủ sở hữu

```
dieu-phoi-nghien-cuu  (ĐIỀU PHỐI TỔNG — owner DUY NHẤT của G0–G10, giữ hợp đồng plugin MỘT OWNER)
   ├── dieu-phoi-g0 … dieu-phoi-g10   (ĐIỀU PHỐI CỔNG — CHỊU TRÁCH NHIỆM kết quả nhiệm vụ của đúng MỘT cổng, §1b)
   │      ├── agent nhiệm vụ chuyên trách (cau-hoi-nghien-cuu, thiet-ke-nghien-cuu, co-mau-nghien-cuu, …)
   │      ├── giam-khao-cong            (GIÁM KHẢO độc lập — chấm đầu ra theo rubric RQ1–RQ8)
   │      ├── phan-bien-tranh-bien      (PHẢN BIỆN trong tranh biện — cố bác kết luận dự kiến bằng căn cứ)
   │      └── trong-tai-tranh-bien      (TRỌNG TÀI — phán từng phản đối, ra kết luận tranh biện)
   └── tham-dinh-dau-ra                 (chốt liêm chính R1–R7 cuối cùng — giữ nguyên, chạy SAU tranh biện)
```

- **Điều phối tổng** quyết định cổng nào làm tiếp (chấm sống), triệu tập hội đồng cổng nào (theo §5 chi phí — hỏi
  bác sĩ trước), gom kết luận các cổng, bàn giao bác sĩ. Không ký, không bật cờ, không ghi xác nhận người.
- **Điều phối cổng** chịu trách nhiệm kết quả thực hiện mọi nhiệm vụ của cổng mình (§1b); chạy 8 bước của §2; là bên
  ĐỀ XUẤT trong tranh biện; KHÔNG chấm đầu ra của chính nhiệm vụ mình làm (G10-T1).
- **Agent nhiệm vụ** làm đúng nhiệm vụ trong danh mục; đầu ra là artifact/khoá thật của cổng (tên artifact là HỢP
  ĐỒNG — không đổi). Agent nhiệm vụ cũng là **người chấm chuyên môn** cho nhiệm vụ KHÁC theo ma trận (§3).
- Plugin vẫn chỉ là worker theo `_PLUGIN-ROUTING-CONTRACT.md`; không làm giám khảo/phản biện/trọng tài, không mở cổng.

## 1b. Trách nhiệm hoàn chỉnh của điều phối cổng (09/10/2026)

Bác sĩ giao: «Từng cổng hãy đảm bảo với các Agent thực hiện một cách hoàn chỉnh các vấn đề của cổng đó và điều phối của
cổng đó chịu trách nhiệm về kết quả thực hiện nhiệm vụ của chính cổng đó».

1. **Mọi vấn đề của cổng có chủ:** từng tiêu chí AUTO/HUMAN của `g<N>_quality_gate.py` (203 tiêu chí, 11 cổng) gán ĐÚNG
   MỘT bên ở `hoi_dong_cong.PHAN_CONG`: nhiệm vụ agent (`G3-T1`) · vai NGƯỜI quyết/ký kèm nhiệm vụ agent phải chuẩn bị hồ
   sơ + lệnh (`STATISTICIAN@G3-T1`) · cổng tiền đề (`^G0,G1`). Test đối chiếu bảng với tập mã bộ chấm phát ra (cây cú
   pháp) và với mục 4b của từng `dieu-phoi-gN.md` — thêm tiêu chí mà quên gán ⇒ đỏ.
2. **Chuỗi trách nhiệm:** agent nhiệm vụ → điều phối cổng → điều phối tổng. Điều phối cổng giao việc, đòi làm lại tới khi
   tiêu chí của agent đạt, bảo đảm người có thẩm quyền nhận đủ hồ sơ + lệnh, báo cổng tiền đề khi bị chặn từ trước.
3. **Thước đo duy nhất (chỉ đọc, không tốn agent):** `python3 tools/hoi_dong_cong.py trach-nhiem --study <mã> --gate
   G<N> [--ghi]` — kết luận `DAT_TIEU_CHI` · `AGENT_XONG_CHO_NGUOI` (mã 0 = phần agent HOÀN CHỈNH) · `AGENT_CON_VIEC` ·
   `CHO_CONG_TRUOC` · `CHUA_PHAN_CONG` (mã 1) · `KHONG_DO_DUOC` (mã 2). Không tự khai «hoàn chỉnh». `--ghi` lưu bảng lúc
   bàn giao ở `hoi_dong/G<N>/trach_nhiem/TN-<mốc>.json` kèm SHA-256 hồ sơ `G<N>_*`. Toàn đề tài cho điều phối
   tổng: `--gate ALL` (bảng 11 cổng + cổng GIAO TRƯỚC; mã 1 nếu còn cổng có việc agent).
4. **Không đổi ranh giới:** trách nhiệm hoàn chỉnh KHÔNG cho phép ký, bật cờ, ghi xác nhận/dấu vân tay thay người, hay sửa
   artifact của cổng khác để «xanh» tiêu chí tiền đề; cũng KHÔNG đòi triệu tập hội đồng nhiều agent (§5).
5. Điều phối tổng chỉ nhận «phần agent của cổng hoàn chỉnh» khi bảng ra mã 0; mã 1 ⇒ trả về đúng điều phối cổng đó.
6. **Từng agent (10/10/2026, bác sĩ giao «hoàn thiện từng cổng, từng Agent, từng điều phối»):** mỗi agent làm/chấm chéo
   nhiệm vụ cổng có khối «Trách nhiệm trong hội đồng cổng» (nhiệm vụ nó làm · đầu ra · tiêu chí nó phải đưa tới ĐẠT · hồ
   sơ nó chuẩn bị cho người · đầu ra nó chấm chéo); mục 4b của điều phối và khối này SINH từ `hoi_dong_cong` bằng
   `python3 tools/sinh_tai_lieu_trach_nhiem.py --ghi --agents-dir <gốc>/.claude/agents` (không sửa tay; test báo lệch).
7. **Đánh giá chéo nằm trong trách nhiệm:** biên bản «trả về sửa» còn hiệu lực ⇒ `AGENT_CON_VIEC`; nhiệm vụ KHÔNG có tiêu
   chí máy (vd G3-T2 biến số, G3-T3 CRF, G6-T3 diễn giải) chỉ được bảo đảm bằng đánh giá chéo — chưa đánh giá ⇒ bảng ghi
   «chất lượng chưa được bảo đảm» và khối bàn giao phải nói thật (không đổi kết luận máy; triệu tập vẫn hỏi bác sĩ §5).
   Nhiệm vụ có tệp hợp đồng thì được thêm **kiểm máy cấp nhiệm vụ** (`hoi_dong_cong.KIEM_NHIEM_VU`, chỉ CẤU TRÚC, không
   phải tiêu chí cổng): G3-T2/G3-T3 — `_bo-bien-rieng.csv` nạp được bằng đúng hàm G5 dùng, không biến định danh, CRF có
   luật kiểm tra; G1-T5 (chỉ RCT) — hai dòng an toàn của đề cương lõi (lợi ích–nguy cơ · dừng/chuyển/cứu hộ) đã điền,
   đếm bằng đúng bộ đếm ô trống của G1-AUTO-07; G4-T2 (chỉ khi thiết kế chắc là RCT) — SAP §13 giữa kỳ/dừng · §14 DMC
   · §15 tổn hại đã điền theo đúng hàm bước ký G4 dùng; lỗi ⇒ `AGENT_CON_VIEC` của đúng agent. Mục «Tiền đề» §2 của
   mỗi điều phối có dòng tiêu chí tiền đề SINH từ `PHAN_CONG` (không còn văn xuôi lệch mã). Ô có điều kiện theo thiết
   kế: G2-AUTO-07 «G2-T2|G2-T1» (RCT ⇒ an toàn) và G6-AUTO-09 «G6-T2|G6-T1» (tổng quan hệ thống có gộp ⇒
   `meta-phan-tich` chịu mô hình phân tích chính ↔ SAP §4; thiết kế khác ⇒ `phan-tich-thong-ke`).
8. **Lệnh trong tài liệu agent phải chạy được:** test `tests/test_lenh_trong_tai_lieu_agent_20261010.py` (repo y khoa)
   đối chiếu mọi cờ của lệnh `python3 tools/…` trong `.claude/agents/*.md` với argparse của công cụ.
9. **Nhiệm vụ có điều kiện máy không suy được — điều phối KHAI bằng máy** (10/10/2026): điều kiện RCT/SR suy từ thiết
   kế đã chốt do máy quyết; điều kiện khác (G1-T4 công cụ đo lường «khi đề tài phát triển, sửa đổi hoặc dịch–thích nghi
   bộ câu hỏi/thang đo»; G7-T2 hiệu đính song ngữ «nộp tạp chí tiếng Anh») trước chỉ được dặn «khai trong khối bàn
   giao» — không máy nào đọc lại nên nhiệm vụ mãi «chưa xác định» và đầu ra không bao giờ bị đòi. Nay:
   `python3 tools/hoi_dong_cong.py khai-ap-dung --study <mã> --gate G<N> --nhiem-vu <NV> --ap-dung co|khong --ly-do "…"`
   ghi `hoi_dong/G<N>/ap_dung_nhiem_vu.json` (lý do ≥ 10 ký tự, không PII; từ chối nhiệm vụ không điều kiện hoặc điều
   kiện thiết kế). Khai «co» ⇒ bảng trách nhiệm đòi đầu ra + kiểm máy của nhiệm vụ: G1-T4 đòi
   `pha_cong_cu/phieu_cvi.csv` + `pha_cong_cu/nhat_ky_phong_van_nhan_thuc.csv` dựng bằng
   `tools/pha_phat_trien_cong_cu.py mau` (phiếu CVI đúng cấu trúc, ≥ 3 chuyên gia, điểm 1–4; nhật ký đủ cột — ô chưa
   chấm/I-CVI thấp là việc của hội đồng chuyên gia, không phải lỗi agent). Khai không phải xác nhận của người: PI bác
   được bằng cách yêu cầu khai lại.
10. **Mỗi agent có nhiệm vụ rõ ràng và có điều phối kiểm soát** (10/10/2026, bác sĩ giao): đo 10/10 có 4 agent nghiên cứu
    không thuộc nhiệm vụ cổng nào (`mo-hinh-tien-luong`, `nghien-cuu-dinh-tinh`, `kinh-te-y-te`, `trich-xuat-y-van`) ⇒ nay
    G1-T6/G6-T4 (prediction), G1-T7/G6-T5 (qualitative), G1-T8 (khai: có cấu phần kinh tế), G5-T2 (SR/MA — bảng
    `06_phan_tich_R/study_level_extraction.csv` mà script gộp đọc); `huong-dan-lam-sang` chấm chéo G6-T3; G6-AUTO-09
    «G6-T2|G6-T4|G6-T5|G6-T1». Bên lâm sàng: hai bảng của `dieu-phoi-lam-sang` sinh khối «Nhiệm vụ & kiểm soát trong
    ca lâm sàng» cho từng agent; thêm C8c (`ket-qua-hoc-tap` + `cap-nhat-guideline` trước đó không có hạng mục
    tự-rà). Test `tests/test_agent_co_dieu_phoi_20261010.py` (repo y khoa) chặn agent mồ côi.

## 2. Tám bước của một hội đồng cổng (`dieu-phoi-gN`)

1. **Chấm sống tiền đề + cổng hiện tại** — `python3 tools/g<N>_quality_gate.py --study <mã>` (và cổng trước qua
   bộ chấm của nó); «không đo được» KHÔNG phải «đạt».
2. **Giao nhiệm vụ** — mỗi nhiệm vụ trong danh mục (bỏ nhiệm vụ có điều kiện không áp dụng, ghi lý do) cho đúng
   agent chuyên trách; agent dùng công cụ THẬT của cổng (`run_g<N>_auto.py`…), không chép tay artifact.
3. **Đánh giá chéo** (§3) — mỗi đầu ra: ≥1 người chấm chuyên môn theo ma trận + `giam-khao-cong`; tác giả không tự
   chấm. Ghi biên bản `danh_gia_cheo`.
4. **Tranh biện** (§4) — các DP của cổng (DP «bắt buộc» ở 6 cổng cứng G2/G4/G5/G8/G9/G10) + mọi đầu ra mà người chấm
   bất đồng. Ghi biên bản `tranh_bien` (trỏ `nguon_bat_dong` khi xử lý bất đồng).
5. **Kết luận dự kiến của cổng** — một trong: `DE_XUAT_TRINH_NGUOI_CO_THAM_QUYEN` · `TRA_VE_SUA` (kèm việc sửa +
   agent sửa) · `CHO_DU_LIEU_THAT` · `CHUYEN_BAC_SI_QUYET` (vấn đề + vì sao thuộc thẩm quyền người). Không bao giờ
   «đã qua cổng/đã ký».
6. **`tham-dinh-dau-ra`** — chốt liêm chính R1–R7 trên gói bàn giao (giữ nguyên `_KIEM-DUYET-DOC-LAP.md`).
7. **Ghi biên bản** — `python3 tools/hoi_dong_cong.py ghi --study <mã> --gate G<N> --tep <nháp.json>` (khuôn:
   `… mau --loai danh_gia_cheo|tranh_bien --gate G<N>`); vi phạm luật ⇒ công cụ KHÔNG ghi (mã 3) — sửa nháp, không
   lách. Tóm tắt: `python3 tools/hoi_dong_cong.py tom-tat --study <mã>`.
8. **Bàn giao điều phối tổng** — khối «KẾT LUẬN HỘI ĐỒNG CỔNG G<N>» (§6).

## 3. Đánh giá chéo — rubric RQ1–RQ8 (bản chuẩn trong `hoi_dong_cong.RUBRIC`)

| Mã | Trục | Lỗi đỏ (🔴) khi… |
|---|---|---|
| RQ1 | Đúng hợp đồng cổng | thiếu tiêu chí AUTO/HUMAN liên quan, sai công cụ, sai tên artifact |
| RQ2 | Đúng phương pháp theo thiết kế | sai công thức/công cụ RoB/chuẩn báo cáo cho thiết kế |
| RQ3 | Truy nguyên nguồn | số liệu/PMID/DOI không truy được, lệch nguồn, nghi bịa — **tầng 0** |
| RQ4 | Nhất quán xuyên cổng | mâu thuẫn quyết định đã chốt (N, α, thiết kế, kết cục chính…; `nhat_quan_xuyen_cong.py`) |
| RQ5 | Đầy đủ | ô trống ngoài nhãn hợp lệ; thiếu artifact theo thiết kế (`_KIEM-TOAN-DAY-DU-NGHIEN-CUU.md`) |
| RQ6 | Ranh giới thẩm quyền | tự ký/xác nhận/bật cờ, vượt cổng — **tầng 0** |
| RQ7 | Không PII / an toàn dữ liệu | có định danh — **tầng 0** |
| RQ8 | Rõ ràng cho người ký | người có thẩm quyền không biết phải làm gì/ký gì |

Mức mỗi trục: `dat` · `can_sua` · `loi_do` · `khong_ap_dung` (phải nêu lý do). Kết luận người chấm: `dat` ·
`dat_co_luu_y` · `tra_ve_sua`. Luật công cụ kiểm: đủ 8 trục; `can_sua`/`loi_do` phải có nhận xét + căn cứ; lỗi đỏ tầng
0 ⇒ bắt buộc `tra_ve_sua`; còn mục cần sửa/lỗi đỏ thì không được `dat`. **Đồng thuận** = mọi người chấm cùng phía
(qua: `dat`/`dat_co_luu_y` · không qua: `tra_ve_sua`); khác phía ⇒ **bất đồng ⇒ phải tranh biện**.

**Căn cứ kiểm được** (mọi nhận xét đòi sửa và mọi luận điểm tranh biện): `tep` (đường dẫn tương đối thư mục đề tài/
repo, có thể `:dòng` hoặc `:dòng-dòng`) · `tieu_chi` (`G4-AUTO-09`, `G4-HUMAN-04`…) · `pmid` · `doi` · `lenh` (câu
lệnh + đoạn `ket_qua`). Lời nói không kèm căn cứ KHÔNG phải căn cứ.

## 4. Tranh biện — trước mọi kết luận của cổng

- **Vai (ba agent khác nhau):** ĐỀ XUẤT = `dieu-phoi-gN` (trình kết luận dự kiến + căn cứ) · PHẢN BIỆN =
  `phan-bien-tranh-bien` (tìm phản đối MẠNH NHẤT có căn cứ; không tìm được thì ghi `nhuong=true` — không bịa phản đối
  cho có) · TRỌNG TÀI = `trong-tai-tranh-bien` (ngữ cảnh mới, không tham gia soạn; chế độ `codex` ⇒
  `codex:trong-tai-tranh-bien` chạy ở phiên Codex tách biệt — khác họ mô hình).
- **Vòng:** mỗi vòng ĐỀ XUẤT rồi PHẢN BIỆN; tối đa **2 vòng** (trần chi phí, chống cãi vòng) rồi trọng tài phán.
- **Phán quyết:** từng phản đối `chap_nhan` · `bac` · `chua_du_can_cu` (kèm lý do); kết quả `giu_ket_luan` ·
  `sua_ket_luan` (kèm `viec_sua`) · `chuyen_bac_si` (kèm vấn đề + vì sao thuộc thẩm quyền người). Đã chấp nhận một
  phản đối thì KHÔNG được giữ nguyên kết luận.
- **Giải pháp tốt nhất — BẮT BUỘC (bác sĩ quyết 06/10/2026: hội đồng giữ vai TƯ VẤN và ĐƯA RA GIẢI PHÁP TỐT NHẤT,
  không chặn cổng):** mọi phán quyết kèm `giai_phap_tot_nhat` = phương án khuyến nghị CỤ THỂ + căn cứ kiểm được;
  `sua_ket_luan`/`chuyen_bac_si` thêm ≥ 1 phương án khác đã cân nhắc + lý do không chọn. Công cụ (`hoi_dong_cong.py`,
  biên bản v2) từ chối ghi khi thiếu, thiếu căn cứ, có PII hoặc viết như trạng thái cổng. Người có thẩm quyền chọn và ký.
- **Thẩm quyền:** trọng tài phân xử LẬP LUẬN, không phân xử thay người có thẩm quyền. Tranh chấp về phán đoán lâm
  sàng/đạo đức/thống kê thuộc vai ký của cổng (`tham_quyen` của DP: PI · IRB · STATISTICIAN · DATA_MANAGER ·
  INDEPENDENT_PEER_REVIEWER) ⇒ `chuyen_bac_si`. Kết luận tranh biện KHÔNG BAO GIỜ được viết như trạng thái cổng
  («đã ký», «đã duyệt», «PASS_…», «…_LOCKED») — công cụ từ chối ghi.

## 5. Chính sách chi phí — hỏi bác sĩ trước khi triệu tập

Đo 06/10/2026: mỗi subagent mới mang ~250 nghìn token nền (danh sách skill, công cụ, CLAUDE.md) TRƯỚC khi đọc tài
liệu đề tài. **Đo thật 07/10/2026** (họp thí điểm G0 của C1a: 4 nhiệm vụ, 2 DP, 2 bất đồng, 16 agent): ≈ **6,1 triệu
token** (~380 nghìn/agent — agent đọc hồ sơ, chạy chấm sống, tra PubMed); cổng nhiều nhiệm vụ hay nhiều bất đồng có thể
vượt mức này. Ước lượng cũ «1–3 triệu/cổng» là THẤP. Tiếp tục (resume) một lượt workflow chỉ dùng lại ĐOẠN ĐẦU không đổi
của chuỗi lời gọi — lượt song song gần như chạy lại hết (07/10: thêm ~3,6 triệu) ⇒ đừng resume để «vá» một bước. Vì vậy
(đúng `CLAUDE.md` §0.6 — không tự mở nhiều agent):

| Chế độ | Khi nào | Độc lập | Chi phí |
|---|---|---|---|
| **Hội đồng đầy đủ** (`subagent`) | bác sĩ đồng ý; khuyến nghị cho DP **bắt buộc** ở 6 cổng cứng và mọi bất đồng | ngữ cảnh mới từng vai | cao |
| **Trọng tài Codex** (`codex`) | máy có Codex CLI; muốn trọng tài khác họ mô hình | khác họ mô hình | Codex chịu phần trọng tài |
| **Cùng phiên** (`cung_phien`) | bác sĩ chọn tiết kiệm / phiên không có subagent / Codex | chỉ độc lập VAI (ghi rõ trên biên bản) | thấp |

**Chạy chế độ `codex` (07/10/2026):** workflow `hoi-dong-cong.js` với `args.trong_tai: "codex"` — vai trọng tài KHÔNG tự
phán mà chạy `python3 tools/trong_tai_codex.py --study <mã> --gate G<N> --tep <nháp.json> --json` rồi trả nguyên văn
phán quyết; chạy tay thêm `--chay-thu` (xem prompt, không gọi Codex) hoặc `--ghi`. Trình chạy gọi Codex CLI ở sandbox
CHỈ-ĐỌC, phiên tạm, môi trường đã lọc, đầu ra ép schema, rồi kiểm bằng CHÍNH luật biên bản (vi phạm ⇒ mã 3, không ghi).
Chế độ này GỬI tới dịch vụ Codex (OpenAI): doctrine trọng tài, bản nháp tranh biện, trạng thái cổng và trích đoạn tệp căn
cứ CẤP ĐẦU thư mục đề tài — không tệp ẩn/khoá/`.env`, không dữ liệu hay bản gỡ băng ở thư mục con. Bác sĩ chọn chế độ khi
triệu tập.

Điều phối tổng/cổng LUÔN hỏi bác sĩ (kèm ước lượng) trước khi mở hội đồng `subagent`; mặc định gom MỘT giám khảo cho
nhiều đầu ra cùng cổng khi được. Workflow Claude Code (`.claude/workflows/hoi-dong-cong.js`) chạy đúng 8 bước với trần
vòng và trần số agent — chỉ chạy khi bác sĩ gọi.

## 6. Khối bàn giao (bắt buộc ở cuối mỗi hội đồng cổng)

```
KẾT LUẬN HỘI ĐỒNG CỔNG G<N> — <mã đề tài> (TƯ VẤN — không mở, không chặn cổng)
- Trạng thái chấm sống cổng: <mã trạng thái từ g<N>_quality_gate.py>
- Nhiệm vụ: <mã: agent → artifact · đánh giá chéo: đồng thuận/bất đồng>
- Tranh biện: <DP: giữ/sửa/chuyển bác sĩ — id biên bản>
- Kết luận dự kiến: DE_XUAT_TRINH_NGUOI_CO_THAM_QUYEN | TRA_VE_SUA | CHO_DU_LIEU_THAT | CHUYEN_BAC_SI_QUYET
- Giải pháp tốt nhất: <từng điểm quyết định: phương án khuyến nghị — căn cứ; phương án khác đã cân nhắc — vì sao không chọn>
- Việc của người có thẩm quyền: <ai — làm gì — lệnh/khoá nào>
- tham-dinh-dau-ra: ĐẠT | TRẢ-VỀ-SỬA
- Trách nhiệm cổng (§1b): <ket_luan của `trach-nhiem --ghi`> — agent còn việc <n> · chờ người <n> · chờ cổng trước <n> — <tệp TN-…json>
- Tóm tắt hội đồng: python3 tools/hoi_dong_cong.py tom-tat --study <mã>
Cần bác sĩ kiểm chứng.
```

## 7. Bất biến (không được phá)

1. Hội đồng là TƯ VẤN: không ghi `approval_ledger`, không gọi `approve_gate.py`, không ghi `gate_params.Gx` xác nhận/
   dấu vân tay thay người, không đổi `study_meta` ngoài nội dung nhiệm vụ của agent chuyên trách.
2. Cổng chỉ qua khi BỘ CHẤM của cổng nói qua và người có thẩm quyền ký (6 cổng cứng) — biên bản đồng thuận không
   thay được điều đó; biên bản «ĐỒNG THUẬN» cũng không phải «ĐẠT CỔNG».
3. Biên bản gắn SHA-256 tài liệu được xét — sửa tài liệu sau đó ⇒ biên bản CŨ, phải họp lại cho bản mới.
4. Không PII trong biên bản (công cụ quét SĐT/CCCD/email); dùng mã tham chiếu.
5. Cùng họ mô hình ⇒ tách ngữ cảnh giảm mù chung nhưng KHÔNG khử thiên lệch hệ thống; rào cuối vẫn là người.

Cần bác sĩ kiểm chứng.
