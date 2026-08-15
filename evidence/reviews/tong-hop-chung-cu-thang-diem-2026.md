# Tổng hợp chứng cứ — thang điểm lâm sàng (RAG, có trích dẫn)

> **32 thang điểm** đã xác minh công thức + nguồn. Mỗi mục NEO vào nguồn gốc (không bịa); 🆕 = đã cập nhật theo guideline 2024–2026.
> Sinh tự động từ `app/clinical_scores/verified.py` bằng `scripts/gen_evidence_brief.py`. Quy ước trích dẫn: `evidence/citation-format.md`.

> ⚠️ Công cụ **HỖ TRỢ**, KHÔNG thay phán đoán lâm sàng. Kiểm chứng nguồn gốc + đối chiếu bối cảnh bệnh nhân trước khi áp dụng.


## Cấp cứu ban đầu

### NEWS2 (National Early Warning Score 2)

- **Tình huống:** Theo dõi sinh hiệu – cảnh báo sớm xấu đi (người lớn cấp tính)
- **Ngưỡng hành động:** 0: theo dõi tối thiểu 12h. 1–4: thấp (đánh giá điều dưỡng). 3 ở 1 thông số đơn: xem xét leo thang. 5–6: trung bình (đánh giá khẩn cấp). ≥7: cao (đánh giá cấp cứu/đe dọa tính mạng).
- **Diễn giải:** Tổng phản ánh mức độ nặng cấp tính & tần suất theo dõi.
- **Lưu ý/giới hạn:** Không thay đánh giá lâm sàng; thận trọng nhóm giữ CO2 mạn.
- ✅ **Nguồn:** Royal College of Physicians. NEWS2, 2017.
- 📘 **Guideline:** RCP NEWS2; NICE NG51 sepsis.

### qSOFA (Quick SOFA) 🆕 CẬP NHẬT

- **Tình huống:** Nghi nhiễm khuẩn ngoài ICU – sàng lọc nguy cơ diễn tiến nặng
- **Ngưỡng hành động:** ≥2: đánh giá rối loạn chức năng cơ quan (SOFA), lactate, cấy máu, hồi sức sớm/chuyển tuyến.
- **Diễn giải:** ≥2: nguy cơ kết cục xấu cao hơn; gợi ý đánh giá nhiễm khuẩn huyết.
- **Lưu ý/giới hạn:** Độ nhạy THẤP (~46%). LƯU Ý: Surviving Sepsis 2021 khuyến cáo MẠNH CHỐNG dùng qSOFA làm CÔNG CỤ SÀNG LỌC ĐƠN LẺ; nên ưu tiên SIRS/NEWS/MEWS + lactate để sàng lọc. qSOFA chỉ hữu ích để TIÊN LƯỢNG nguy cơ xấu, không phải để loại trừ sepsis.
- ✅ **Nguồn:** Singer M, et al. (Sepsis-3) JAMA 2016;315:801-810; Evans L, et al. Surviving Sepsis 2021, Crit Care Med 2021.
- 📘 **Guideline:** Surviving Sepsis Campaign 2021 (khuyến cáo mạnh chống dùng qSOFA đơn lẻ).


## Hô hấp

### CURB-65

- **Tình huống:** Viêm phổi cộng đồng (CAP) – phân tầng mức độ nặng & nơi điều trị
- **Ngưỡng hành động:** 0–1: cân nhắc điều trị ngoại trú. 2: nhập viện ngắn ngày/theo dõi sát. ≥3: nhập viện, cân nhắc ICU nếu 4–5.
- **Diễn giải:** Tử vong 30 ngày tăng theo điểm: 0–1 thấp, 2 trung bình, 3–5 cao.
- **Lưu ý/giới hạn:** Không thay thế đánh giá lâm sàng; ít nhạy ở người trẻ/suy giảm miễn dịch.
- ✅ **Nguồn:** Lim WS, et al. Thorax 2003;58:377-382.
- 📘 **Guideline:** BTS/NICE CAP; IDSA/ATS CAP guideline.

### GOLD ABE Assessment (2023+) 🆕 CẬP NHẬT

- **Tình huống:** COPD ổn định – phân nhóm định hướng điều trị khởi đầu
- **Ngưỡng hành động:** A: 1 thuốc giãn phế quản. B: LABA+LAMA. E: LABA+LAMA; có thể bắt đầu BỘ BA LABA+LAMA+ICS ngay nếu eosinophil ≥300 (GOLD 2025). Theo dõi: leo thang ICS nếu eos ≥100; cân nhắc dupilumab nếu eos ≥300 + viêm phế quản mạn còn đợt cấp.
- **Diễn giải:** A: ít triệu chứng (mMRC 0–1 / CAT<10) & ≤1 đợt cấp nhẹ. B: nhiều triệu chứng (mMRC≥2 / CAT≥10) & ≤1 đợt cấp nhẹ. E: ≥2 đợt cấp vừa hoặc ≥1 đợt nhập viện (bất kể triệu chứng).
- **Lưu ý/giới hạn:** Phân nhóm phục vụ điều trị KHỞI ĐẦU, không thay theo dõi cá thể hóa.
- ✅ **Nguồn:** GOLD Report 2025.
- 📘 **Guideline:** GOLD 2025 (eosinophil ≥300 cho ICS; ABE).

### PERC Rule

- **Tình huống:** Nghi PE ở nhóm xác suất lâm sàng THẤP
- **Ngưỡng hành động:** PERC âm + pretest thấp → dừng truy tìm PE. Bất kỳ tiêu chí dương → D-dimer/CTPA.
- **Diễn giải:** Nếu xác suất thấp + PERC âm: nguy cơ PE <2%, không cần xét nghiệm thêm.
- **Lưu ý/giới hạn:** Không dùng khi xác suất trung bình/cao.
- ✅ **Nguồn:** Kline JA, et al. J Thromb Haemost 2004;2:1247-1255.
- 📘 **Guideline:** ACEP clinical policy PE.

### Wells score – PE

- **Tình huống:** Nghi thuyên tắc phổi
- **Ngưỡng hành động:** ≤4: D-dimer (cân nhắc PERC/ age-adjusted); âm tính → loại trừ. >4: CTPA.
- **Diễn giải:** 2 mức: ≤4 = PE unlikely, >4 = PE likely. 3 mức: <2 thấp, 2–6 trung bình, >6 cao.
- **Lưu ý/giới hạn:** Phụ thuộc đánh giá chủ quan 'PE khả dĩ nhất'.
- ✅ **Nguồn:** Wells PS, et al. Thromb Haemost 2000;83:416-420.
- 📘 **Guideline:** ESC 2019 Pulmonary Embolism.


## Khác

### AUDIT-C

- **Tình huống:** Sàng lọc sử dụng rượu có hại
- **Ngưỡng hành động:** ≥4 (nam) / ≥3 (nữ): dương tính, tư vấn ngắn/đánh giá thêm (AUDIT đầy đủ).
- **Diễn giải:** Điểm cao → khả năng uống rượu nguy cơ cao hơn.
- **Lưu ý/giới hạn:** Tự khai báo có thể thấp hơn thực tế.
- ✅ **Nguồn:** Bush K, et al. Arch Intern Med 1998;158:1789-1795.
- 📘 **Guideline:** USPSTF unhealthy alcohol use.

### GAD-7 🆕 CẬP NHẬT

- **Tình huống:** Sàng lọc & theo dõi rối loạn lo âu
- **Ngưỡng hành động:** ≥10: ngưỡng gợi ý cần đánh giá/điều trị thêm.
- **Diễn giải:** 0–4 tối thiểu, 5–9 nhẹ, 10–14 trung bình, 15–21 nặng.
- **Lưu ý/giới hạn:** Công cụ sàng lọc, không thay chẩn đoán.
- ✅ **Nguồn:** Spitzer RL, et al. Arch Intern Med 2006;166:1092-1097.
- 📘 **Guideline:** USPSTF 2023: khuyến cáo MỚI (mức B) sàng lọc rối loạn lo âu ở người lớn ≤64 tuổi (gồm thai kỳ/hậu sản); NICE anxiety. Ngưỡng ≥10 xác nhận lại bởi meta-analysis 2023.

### PHQ-9

- **Tình huống:** Sàng lọc & theo dõi mức độ trầm cảm
- **Ngưỡng hành động:** ≥10: cân nhắc trầm cảm nặng cần điều trị. Mục 9 (ý tưởng tự sát) dương → đánh giá nguy cơ ngay.
- **Diễn giải:** 0–4 tối thiểu, 5–9 nhẹ, 10–14 trung bình, 15–19 trung bình-nặng, 20–27 nặng.
- **Lưu ý/giới hạn:** Là công cụ sàng lọc, không thay chẩn đoán lâm sàng.
- ✅ **Nguồn:** Kroenke K, Spitzer RL, Williams JBW. J Gen Intern Med 2001;16:606-613.
- 📘 **Guideline:** USPSTF depression screening.


## Lão khoa - Đa bệnh lý

### AGS Beers Criteria® 2023

- **Tình huống:** Rà soát thuốc ở người cao tuổi (≥65) – thuốc có thể không phù hợp (PIM)
- **Ngưỡng hành động:** Khi gặp thuốc nằm trong danh mục → đánh giá lại chỉ định, cân nhắc deprescribing/thay thế, ghi lý do nếu vẫn tiếp tục. 2023 cập nhật phần KHÁNG ĐÔNG và estrogen sau mãn kinh.
- **Diễn giải:** Bao gồm hơn 3 chục thuốc/nhóm cần tránh + 40+ thuốc cần thận trọng theo bệnh kèm.
- **Lưu ý/giới hạn:** Là công cụ HỖ TRỢ, không thay phán đoán lâm sàng; chủ yếu chuẩn hoá theo Hoa Kỳ.
- ✅ **Nguồn:** By the 2023 AGS Beers Criteria Update Expert Panel. J Am Geriatr Soc 2023;71:2052-2081 (doi:10.1111/jgs.18372).
- 📘 **Guideline:** AGS 2023 Beers Criteria® (bản chính thức – cần tra danh mục đầy đủ).

### FRAIL Scale

- **Tình huống:** Sàng lọc suy yếu (frailty) nhanh ngoại trú
- **Ngưỡng hành động:** ≥3: đánh giá lão khoa toàn diện (CGA), rà soát đa thuốc, té ngã, dinh dưỡng.
- **Diễn giải:** 0: khỏe (robust). 1–2: tiền suy yếu. 3–5: suy yếu (frail).
- **Lưu ý/giới hạn:** Là công cụ sàng lọc, không thay CGA.
- ✅ **Nguồn:** Morley JE, et al. J Nutr Health Aging 2012;16:601-608.
- 📘 **Guideline:** —

### STOPP/START phiên bản 3 (2023)

- **Tình huống:** Rà soát kê đơn không phù hợp (STOPP) và thiếu sót điều trị (START) ở người cao tuổi
- **Ngưỡng hành động:** Khi một đơn thuốc khớp tiêu chí STOPP → cân nhắc ngưng/giảm; khớp START → cân nhắc bổ sung. Luôn cá thể hoá theo mục tiêu điều trị & kỳ vọng sống.
- **Diễn giải:** Mỗi tiêu chí mô tả tình huống kê đơn cần xem lại (STOPP) hoặc cần bổ sung (START).
- **Lưu ý/giới hạn:** Hỗ trợ ra quyết định, không thay phán đoán; cần bản đầy đủ để áp dụng đúng.
- ✅ **Nguồn:** O'Mahony D, et al. STOPP/START criteria version 3. Eur Geriatr Med 2023;14:625-632 (doi:10.1007/s41999-023-00777-y).
- 📘 **Guideline:** STOPP/START v3 (2023) – bản chính thức.


## Nhiễm khuẩn

### Centor / McIsaac (modified)

- **Tình huống:** Viêm họng cấp – xác suất nhiễm liên cầu nhóm A (GAS)
- **Ngưỡng hành động:** ≤0–1: không xét nghiệm/không kháng sinh. 2–3: xét nghiệm nhanh GAS (RADT). ≥4: xét nghiệm; điều trị nếu dương (KHÔNG khuyến cáo kháng sinh theo kinh nghiệm thường quy).
- **Diễn giải:** Điểm cao → khả năng GAS cao hơn.
- **Lưu ý/giới hạn:** Không phân biệt người lành mang GAS; dịch tễ địa phương ảnh hưởng.
- ✅ **Nguồn:** McIsaac WJ, et al. CMAJ 1998;158:75-83; Centor RM 1981.
- 📘 **Guideline:** IDSA pharyngitis; NICE sore throat (FeverPAIN là lựa chọn thay thế).


## Nội tiết - Chuyển hóa

### FINDRISC

- **Tình huống:** Sàng lọc nguy cơ đái tháo đường típ 2 (không xâm lấn)
- **Ngưỡng hành động:** ≥15: nguy cơ cao → xét nghiệm đường huyết/HbA1c, tư vấn lối sống.
- **Diễn giải:** Điểm càng cao nguy cơ 10 năm càng cao.
- **Lưu ý/giới hạn:** Hiệu chỉnh theo quần thể; cần xác nhận bằng xét nghiệm.
- ✅ **Nguồn:** Lindström J, Tuomilehto J. Diabetes Care 2003;26:725-731.
- 📘 **Guideline:** ADA Standards of Care; IDF.

### HOMA-IR

- **Tình huống:** Đánh giá đề kháng insulin
- **Ngưỡng hành động:** Diễn giải theo khoảng tham chiếu địa phương; không có cut-off chẩn đoán phổ quát.
- **Diễn giải:** Giá trị cao → đề kháng insulin nhiều hơn (ngưỡng phụ thuộc quần thể).
- **Lưu ý/giới hạn:** Không dùng khi đang điều trị insulin; biến thiên giữa các xét nghiệm insulin.
- ✅ **Nguồn:** Matthews DR, et al. Diabetologia 1985;28:412-419.
- 📘 **Guideline:** —

### SCORE2-Diabetes (ESC 2023)

- **Tình huống:** Đái tháo đường típ 2 chưa có ASCVD – ước tính nguy cơ tim mạch 10 năm
- **Ngưỡng hành động:** Theo ngưỡng nguy cơ của ESC 2023 (thấp-TB/cao/rất cao) để định hướng đích LDL, statin, và cân nhắc SGLT2i/GLP-1 RA có lợi ích tim mạch.
- **Diễn giải:** Phân tầng nguy cơ tim mạch 10 năm ở bệnh nhân ĐTĐ típ 2 (theo ngưỡng tuổi ESC).
- **Lưu ý/giới hạn:** Hiệu chỉnh cho quần thể châu Âu; chỉ dùng khi CHƯA có ASCVD/tổn thương cơ quan đích nặng.
- ✅ **Nguồn:** SCORE2-Diabetes Working Group & ESC CVD Risk Collaboration. Eur Heart J 2023;44:2544-2556.
- 📘 **Guideline:** ESC 2023 CVD trong ĐTĐ (Eur Heart J 2023;44:4043).


## Thận

### Anion Gap (khoảng trống anion)

- **Tình huống:** Rối loạn toan-kiềm chuyển hóa
- **Ngưỡng hành động:** AG cao: nghĩ MUDPILES (toan ceton, toan lactic, ngộ độc, suy thận...). AG bình thường: mất HCO3 (tiêu chảy, RTA).
- **Diễn giải:** Bình thường ~8–12 mmol/L (tùy phòng xét nghiệm).
- **Lưu ý/giới hạn:** Khoảng tham chiếu phụ thuộc phương pháp đo điện giải.
- ✅ **Nguồn:** Kraut JA, Madias NE. Clin J Am Soc Nephrol 2007;2:162-174.
- 📘 **Guideline:** —

### CKD-EPI 2021 (eGFR) & phân giai đoạn KDIGO

- **Tình huống:** Đánh giá & phân giai đoạn bệnh thận mạn
- **Ngưỡng hành động:** G3b–G5 hoặc A3: chuyển/nhắc chuyên khoa thận tùy bối cảnh; rà soát hiệu chỉnh liều thuốc theo eGFR.
- **Diễn giải:** Giai đoạn G: G1 ≥90, G2 60–89, G3a 45–59, G3b 30–44, G4 15–29, G5 <15 (mL/phút/1.73m²). Albumin niệu A1 <30, A2 30–300, A3 >300 mg/g.
- **Lưu ý/giới hạn:** eGFR ước tính kém chính xác ở khối cơ bất thường/cấp tính.
- ✅ **Nguồn:** Inker LA, et al. N Engl J Med 2021;385:1737-1749.
- 📘 **Guideline:** KDIGO 2024 CKD.

### KDIGO CKD Risk Grid (heat map)

- **Tình huống:** Phân tầng nguy cơ tiến triển CKD
- **Ngưỡng hành động:** Cam/Đỏ: tăng tần suất theo dõi, tối ưu kiểm soát nguyên nhân, cân nhắc SGLT2i/RAASi nếu phù hợp, xem xét chuyển chuyên khoa.
- **Diễn giải:** Xanh: nguy cơ thấp. Vàng: trung bình. Cam: cao. Đỏ: rất cao.
- **Lưu ý/giới hạn:** Là khung nguy cơ chung, cần cá thể hóa.
- ✅ **Nguồn:** KDIGO 2024 CKD Guideline (heat map).
- 📘 **Guideline:** KDIGO 2024 CKD.


## Tim mạch

### ASCVD Risk (Pooled Cohort Equations) 🆕 CẬP NHẬT

- **Tình huống:** Dự phòng tim mạch nguyên phát (40–79 tuổi)
- **Ngưỡng hành động:** ≥7.5%: thảo luận statin (cân nhắc yếu tố tăng nặng risk-enhancers, CAC nếu chưa chắc). ≥20%: statin cường độ cao.
- **Diễn giải:** Phân tầng nguy cơ 10 năm: <5% thấp, 5–<7.5% giới hạn, 7.5–<20% trung bình, ≥20% cao.
- **Lưu ý/giới hạn:** PCE có thể ước tính LỆCH (thường cao) ở quần thể hiện đại; cần công cụ chính thức. CẬP NHẬT: AHA công bố phương trình PREVENT (2023) – bỏ chủng tộc, cho nguy cơ 10 & 30 năm, thường ước tính THẤP HƠN PCE; PREVENT chưa được mandate thay thế PCE trong guideline statin hiện hành nhưng đang được áp dụng tăng dần. Đối chiếu công cụ cơ sở đang dùng (PCE vs PREVENT).
- ✅ **Nguồn:** Goff DC, et al. Circulation 2014;129(25 Suppl 2):S49-73; Khan SS, et al. AHA PREVENT, Circulation 2023.
- 📘 **Guideline:** 2018 ACC/AHA Cholesterol; 2019 Primary Prevention; AHA PREVENT 2023 (mới).

### CHA2DS2-VA (ESC 2024) / CHA2DS2-VASc 🆕 CẬP NHẬT

- **Tình huống:** Rung nhĩ không do bệnh van – nguy cơ huyết khối/đột quỵ
- **Ngưỡng hành động:** ESC 2024 (CHA2DS2-VA, không phân biệt giới): ≥2 khuyến cáo kháng đông đường uống (ưu tiên DOAC); =1 cân nhắc (IIa); =0 thường không cần. Bản CHA2DS2-VASc cũ: nam ≥2 / nữ ≥3 khuyến cáo kháng đông.
- **Diễn giải:** Nguy cơ đột quỵ/năm tăng theo điểm; áp dụng KHÔNG phụ thuộc giới (VA).
- **Lưu ý/giới hạn:** Không áp dụng cho rung nhĩ do van/cơ học. LƯU Ý CẬP NHẬT: ESC 2024 đã thay CHA2DS2-VASc bằng CHA2DS2-VA (bỏ giới, tối đa 8 điểm).
- ✅ **Nguồn:** Lip GYH, et al. Chest 2010;137:263-272 (VASc gốc); ESC 2024 AF Guideline (Eur Heart J 2024) – CHA2DS2-VA.
- 📘 **Guideline:** ESC 2024 AF (AF-CARE, CHA2DS2-VA) – cập nhật; ESC 2020 AF (VASc).

### HAS-BLED

- **Tình huống:** Bệnh nhân rung nhĩ cân nhắc/đang dùng kháng đông
- **Ngưỡng hành động:** ≥3: KHÔNG dùng để chống chỉ định kháng đông; dùng để tối ưu hóa yếu tố nguy cơ (HA, INR, thuốc, rượu) và lịch theo dõi.
- **Diễn giải:** ≥3 = nguy cơ chảy máu cao, cần theo dõi sát và xử lý yếu tố điều chỉnh được.
- **Lưu ý/giới hạn:** Không dùng để từ chối kháng đông ở bệnh nhân có chỉ định.
- ✅ **Nguồn:** Pisters R, et al. Chest 2010;138:1093-1100.
- 📘 **Guideline:** ESC 2020/2024 AF.

### NYHA Functional Classification

- **Tình huống:** Suy tim – phân độ chức năng theo triệu chứng
- **Ngưỡng hành động:** Class II–IV: tối ưu điều trị nền tảng suy tim (GDMT). Class III–IV dai dẳng: cân nhắc thiết bị/chuyển chuyên khoa.
- **Diễn giải:** I: không hạn chế hoạt động. II: hạn chế nhẹ, triệu chứng khi gắng sức thường. III: hạn chế rõ, triệu chứng khi gắng sức nhẹ. IV: triệu chứng khi nghỉ.
- **Lưu ý/giới hạn:** Chủ quan, biến thiên giữa người đánh giá.
- ✅ **Nguồn:** The Criteria Committee of the NYHA, 1994 (9th ed).
- 📘 **Guideline:** ESC 2021 HF; ACC/AHA/HFSA 2022 HF.

### SCORE2 / SCORE2-OP

- **Tình huống:** Dự phòng tim mạch nguyên phát (mô hình châu Âu)
- **Ngưỡng hành động:** Theo ngưỡng tuổi của ESC 2021: vd <50t: <2.5% thấp-TB, 2.5–<7.5% cao, ≥7.5% rất cao.
- **Diễn giải:** Ngưỡng nguy cơ thay đổi theo nhóm tuổi (ESC 2021).
- **Lưu ý/giới hạn:** Hiệu chỉnh cho quần thể châu Âu; áp dụng ngoài châu Âu cần thận trọng.
- ✅ **Nguồn:** SCORE2 working group & ESC CVD risk collaboration. Eur Heart J 2021;42:2439-2454.
- 📘 **Guideline:** ESC 2021 CVD prevention.

### TIMI Risk Score (UA/NSTEMI)

- **Tình huống:** Hội chứng vành cấp không ST chênh lên
- **Ngưỡng hành động:** Điểm cao (≥3) gợi ý chiến lược can thiệp xâm lấn sớm; luôn kết hợp lâm sàng + ECG + troponin.
- **Diễn giải:** Điểm cao → nguy cơ tử vong/NMCT/tái thông khẩn cao hơn.
- **Lưu ý/giới hạn:** Đơn giản hóa; GRACE phân biệt tốt hơn ở một số nhóm.
- ✅ **Nguồn:** Antman EM, et al. JAMA 2000;284:835-842.
- 📘 **Guideline:** ESC 2023 ACS; ACC/AHA.

### Wells score – DVT

- **Tình huống:** Nghi huyết khối tĩnh mạch sâu chi dưới
- **Ngưỡng hành động:** ≤1: D-dimer; âm tính → loại trừ. ≥2 (hoặc D-dimer dương): siêu âm ép tĩnh mạch.
- **Diễn giải:** ≤1: ít khả năng (DVT unlikely). ≥2: nhiều khả năng (DVT likely).
- **Lưu ý/giới hạn:** Độ chính xác giảm ở bệnh nhân nội trú/ung thư.
- ✅ **Nguồn:** Wells PS, et al. N Engl J Med 2003;349:1227-1235.
- 📘 **Guideline:** NICE NG158; ACCP/ASH VTE.


## Tiêu hóa - Gan mật

### APRI (AST to Platelet Ratio Index)

- **Tình huống:** Bệnh gan mạn – ước tính xơ hóa/xơ gan
- **Ngưỡng hành động:** WHO: >0.5 gợi ý xơ hóa đáng kể; >1.0 gợi ý xơ gan (cân nhắc theo bối cảnh).
- **Diễn giải:** Điểm cao gợi ý xơ hóa đáng kể/xơ gan.
- **Lưu ý/giới hạn:** Độ chính xác trung bình; phụ thuộc ULN của phòng xét nghiệm.
- ✅ **Nguồn:** Wai CT, et al. Hepatology 2003;38:518-526.
- 📘 **Guideline:** WHO hepatitis B/C guidelines.

### Child-Pugh

- **Tình huống:** Xơ gan – phân độ chức năng gan & tiên lượng
- **Ngưỡng hành động:** Class B/C: thận trọng thuốc chuyển hóa gan; cân nhắc chuyển chuyên khoa/ghép gan.
- **Diễn giải:** A: 5–6 (còn bù). B: 7–9 (suy chức năng có ý nghĩa). C: 10–15 (mất bù).
- **Lưu ý/giới hạn:** Hai biến chủ quan (cổ trướng, bệnh não gan).
- ✅ **Nguồn:** Pugh RNH, et al. Br J Surg 1973;60:646-649.
- 📘 **Guideline:** AASLD/EASL cirrhosis.

### FIB-4 Index 🆕 CẬP NHẬT

- **Tình huống:** Bệnh gan mạn (viêm gan virus, MASLD/NAFLD) – ước tính xơ hóa
- **Ngưỡng hành động:** MASLD/NAFLD (AASLD 2023, chăm sóc ban đầu): <1.3 nguy cơ THẤP (không cần thêm); ≥1.3 cần đánh giá bước 2 (đàn hồi gan/ELF); ở người >65 tuổi dùng ngưỡng >2.0; >2.67 nhiều khả năng xơ hóa tiến triển. Bản gốc viêm gan C (Sterling 2006): <1.45 và >3.25.
- **Diễn giải:** Phản ánh khả năng xơ hóa tiến triển (F3–F4). Ngưỡng KHÁC NHAU theo bối cảnh.
- **Lưu ý/giới hạn:** Kém chính xác ở <35 và >65 tuổi (cần ngưỡng tuổi cao hơn); ảnh hưởng bởi nguyên nhân thay đổi men gan/tiểu cầu.
- ✅ **Nguồn:** Sterling RK, et al. Hepatology 2006;43:1317-1325; AASLD MASLD Practice Guidance 2023 (Rinella, Hepatology 2023).
- 📘 **Guideline:** AASLD 2023 MASLD Practice Guidance (ngưỡng <1.3); EASL.

### Glasgow-Blatchford Score (GBS)

- **Tình huống:** Xuất huyết tiêu hóa trên – phân tầng cần can thiệp
- **Ngưỡng hành động:** GBS = 0: cân nhắc xuất viện/nội soi ngoại trú. ≥1: nhập viện đánh giá nội soi.
- **Diễn giải:** GBS = 0 (hoặc ≤1 theo một số ngưỡng): nguy cơ rất thấp.
- **Lưu ý/giới hạn:** Đánh giá nhu cầu can thiệp, không tiên lượng tử vong như Rockall.
- ✅ **Nguồn:** Blatchford O, et al. Lancet 2000;356:1318-1321.
- 📘 **Guideline:** NICE CG141; ESGE UGIB.

### MELD-Na 🆕 CẬP NHẬT

- **Tình huống:** Bệnh gan tiến triển – tiên lượng/ưu tiên ghép gan
- **Ngưỡng hành động:** Theo ngưỡng phân bổ ghép của trung tâm/quốc gia hiện hành.
- **Diễn giải:** Điểm cao → tử vong 90 ngày cao hơn.
- **Lưu ý/giới hạn:** Bị ảnh hưởng bởi nguyên nhân tăng creatinine/INR ngoài gan.
- ✅ **Nguồn:** Kim WR, et al. N Engl J Med 2008;359:1018-1026 (MELD-Na); Kim WR, et al. Gastroenterology 2021 (MELD 3.0).
- 📘 **Guideline:** OPTN/UNOS policy 2023 (MELD 3.0 là chuẩn hiện hành); AASLD.

### Maddrey Discriminant Function (mDF)

- **Tình huống:** Viêm gan do rượu – đánh giá mức độ nặng
- **Ngưỡng hành động:** ≥32: cân nhắc corticosteroid nếu không chống chỉ định; đánh giá đáp ứng bằng Lille sau 7 ngày.
- **Diễn giải:** ≥32: viêm gan rượu NẶNG (tiên lượng tử vong ngắn hạn cao).
- **Lưu ý/giới hạn:** Phụ thuộc chuẩn hóa PT của phòng xét nghiệm.
- ✅ **Nguồn:** Maddrey WC, et al. Gastroenterology 1978;75:193-199.
- 📘 **Guideline:** AASLD/EASL alcohol-associated liver disease.


---
*Kết luận: Hãy kiểm chứng nguồn gốc và đối chiếu bối cảnh bệnh nhân cụ thể trước khi áp dụng.*
