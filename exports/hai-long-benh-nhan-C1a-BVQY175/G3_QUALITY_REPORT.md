# BÁO CÁO CHẤT LƯỢNG G3 (CỠ MẪU) — hai-long-benh-nhan-C1a-BVQY175

**Trạng thái:** `DRAFT_READY_NEEDS_STATISTICIAN_REVIEW`
**Phiên bản hợp đồng:** G3-2026.1

## Kiểm tự động (máy kiểm SỐ và NGUỒN)
| Mã | Tiêu chí | Trạng thái | Bằng chứng |
|---|---|---|---|
| G3-AUTO-00 | Guardrail liêm chính G3 sạch | PASS | guardrail='✅ PASS' |
| G3-AUTO-01 | Tiền đề G0/G1 có thật (thiết kế không do mặc định im lặng) | PASS | có G1_checkpoint làm nguồn thiết kế |
| G3-AUTO-02 | Mã thiết kế thuộc từ vựng canonical | PASS | design_code='cross_sectional' |
| G3-AUTO-03 | Loại effect size tương thích với thiết kế và dạng kết cục | PASS | effect_type=PREVALENCE hợp lệ cho cross_sectional |
| G3-AUTO-04 | Có giá trị cỡ mẫu dùng được (hoặc N thay thế hợp lệ) | PASS | n_adjusted=453 |
| G3-AUTO-05 | Effect size có định danh nguồn thật (PMID/DOI/MCID/pilot) | PASS | thiết kế mô tả: cỡ mẫu theo độ chính xác, không dùng effect size; nguồn tỷ lệ ước lượng p đã ghi: Quy ước thận trọng p = 0,50 — giá trị làm phương sai p(1-p) lớn nhất nên cho cỡ mẫu lớn nhất; dùng k |
| G3-AUTO-06 | Effect size không phải số THÔ chưa đọc toàn văn | PASS | effect size do bác sĩ cấp trực tiếp hoặc không áp dụng |
| G3-AUTO-07 | Alpha/power trong quy ước và đã xử lý bội/giữa kỳ | PASS | alpha=0.05, power=0.8 |
| G3-AUTO-08 | Mọi tham số phụ đưa vào công thức đều có nguồn | PASS | các tham số phụ đang dùng đều có khai nguồn |
| G3-AUTO-09 | Các con số trong artifact nhất quán với nhau | PASS | N, bảng độ nhạy và dropout khớp nhau |
| G3-AUTO-10 | Artifact nhắc đúng chuẩn báo cáo của thiết kế | PASS | tìm thấy 'STROBE' trong artifact |
| G3-AUTO-11 | Non-inferiority/equivalence: biên Δ có khung quy định, biện minh và nguồn | PASS | giả thuyết superiority |
| G3-AUTO-12 | Thiết kế theo chùm: ICC có nguồn, design effect đúng số học, đủ số chùm | PASS | không khai thiết kế theo chùm |
| G3-AUTO-16 | Hiệu chỉnh quần thể hữu hạn (FPC) chỉ dùng cho khảo sát quần thể hữu hạn | PASS | không dùng hiệu chỉnh quần thể hữu hạn |
| G3-AUTO-17 | Thiết kế không dùng power đã dùng đúng khung thay thế | PASS | thiết kế dùng công thức power thông thường |
| G3-AUTO-13 | N thực tế đã chốt đủ lực và có phương pháp | PASS | N chốt=1000 ≥ N tối thiểu=453 |
| G3-AUTO-14 | Tham số đã ghim đủ để chạy lại ra cùng một N | PASS | tham số quyết định đã ghim trong study_meta |
| G3-AUTO-15 | Khai rõ công thức đã dùng và phần mềm/phiên bản | PASS | formula=có; software=Python 3.14 (scipy.stats, statsmodels 0.14); đối chiếu chéo bằng nửa rộng KTC 95% |

## Xác nhận người thật (thống kê viên / chủ nhiệm đề tài)
| Mã | Tiêu chí | Trạng thái | Bằng chứng |
|---|---|---|---|
| G3-HUMAN-01 | Chủ nhiệm/thống kê viên xác nhận effect size và nguồn của nó | REVIEW | effect_source_confirmed=False; nguồn=thiếu |
| G3-HUMAN-02 | Đã xác nhận các giả định phụ (bỏ cuộc, tỷ lệ biến cố, SD, tỷ lệ hiện mắc) | REVIEW | assumptions_confirmed=False |
| G3-HUMAN-03 | Đã xác nhận loại giả thuyết (superiority / không thua kém / tương đương) | REVIEW | hypothesis_type=superiority (mặc định của hệ là superiority); confirmed=False |
| G3-HUMAN-04 | Cỡ mẫu được tính cho ĐÚNG kết cục chính đã chốt ở G1 | REVIEW | powered_for_outcome='Cỡ mẫu tính cho KẾT CỤC MT1: tỷ lệ hài lòng chung (G1 >= 4/5' khác kết cục chính của G1 ('G1 — mức hài lòng chung, hỏi trực tiếp (biến SHLNBChung_Truc') |
| G3-HUMAN-05 | Đã xác nhận khả thi tuyển đủ cỡ mẫu tại cơ sở | REVIEW | recruitment_feasibility_confirmed=False |
| G3-HUMAN-06 | Có vai trò (thống kê viên/chủ nhiệm) và thời điểm rà soát | REVIEW | reviewed_by_role=thiếu (nhóm=không nhận diện); reviewed_at=thiếu |
| G3-HUMAN-07 | Thử nghiệm then chốt: có nhà thống kê độc lập và lực đủ cao | PASS | không khai là thử nghiệm then chốt |

## Việc còn lại
- Đọc toàn văn nguồn rồi đặt gate_params.G3.effect_source_confirmed=true.
- Rà từng dòng bảng tham số của artifact A4 rồi đặt assumptions_confirmed=true.
- Chọn nhầm loại giả thuyết là sai toàn bộ phép tính — xác nhận rồi đặt hypothesis_confirmed=true.
- Ghi gate_params.G3.powered_for_outcome khớp
gate_params.G1.primary_outcome; nếu tính cho kết cục khác thì phải nói
rõ và biện minh.
- Đối chiếu N với lưu lượng bệnh nhân thật và thời gian thu thập, rồi xác nhận.
- Ghi reviewed_by_role (STATISTICIAN hoặc PI) và reviewed_at dạng ISO-8601; không lưu danh tính.

## Nền chuẩn
| Chuẩn | Phạm vi | PMID/DOI/URL |
|---|---|---|
| DELTA2 guidance (Cook JA và cs., 2018) | Chọn và BIỆN MINH target difference; 8 mục bắt buộc khi báo cáo phép tính cỡ mẫu của thử nghiệm ngẫu nhiên | PMID:30560792; DOI:10.1136/bmj.k3750 |
| DELTA2 — báo cáo HTA đầy đủ (2019) | Target difference phải khớp estimand chính; nêu rõ nếu dùng cách xác định cỡ mẫu không theo power quy ước | PMID:31661431; DOI:10.3310/hta23600 |
| ICH E9 §3.5 (Statistical Principles for Clinical Trials) | Đề cương phải ghi phương pháp tính cỡ mẫu, mọi đại lượng đầu vào, CƠ SỞ của từng ước lượng và một phân tích độ nhạy của cỡ mẫu | https://database.ich.org/sites/default/files/E9_Guideline.pdf |
| ICH E9(R1) §A.4 (Addendum on Estimands) | Cỡ mẫu phải xuất phát từ mô tả chính xác treatment effect quan tâm; cẩn trọng khi mượn effect size từ nghiên cứu báo cáo theo estimand khác | https://database.ich.org/sites/default/files/E9-R1_Step4_Guideline_2019_1203.pdf |
| CONSORT 2025 — mục 16a/16b | Nêu cỡ mẫu được xác định thế nào KÈM TẤT CẢ giả định chống đỡ phép tính; nêu phần mềm; nêu phân tích giữa kỳ và quy tắc dừng | DOI:10.1136/bmj-2024-081123 |
| SPIRIT 2025 — mục 19 | Đề cương phải nêu cỡ mẫu và mọi giả định; cỡ mẫu phải nhất quán với kết cục chính và với bản ghi ở cơ quan đăng ký nghiên cứu | DOI:10.1136/bmj-2024-081477 |
| Riley RD và cs., BMJ 2020 — cỡ mẫu mô hình tiên lượng | Cỡ mẫu phát triển mô hình tính theo shrinkage/R² đích, KHÔNG dùng quy tắc ngón tay EPV | PMID:32188600; DOI:10.1136/bmj.m441 |
| Riley RD, 2019 — đính chính Part II | Erratum bắt buộc đọc kèm công thức Part II (nhị phân/time-to-event) | PMID:31793031; DOI:10.1002/sim.8409 |
| van Smeden M và cs., 2016 | Bằng chứng ủng hộ ngưỡng EPV cho hồi quy logistic là YẾU — không dùng EPV làm tiêu chí quyết định cỡ mẫu | PMID:27881078; DOI:10.1186/s12874-016-0267-3 |
| Ogundimu EO và cs., 2016 | Nguồn THẬT của ngưỡng 'EPV ≥ 20' — chỉ áp cho mô hình Cox có nhiều biến tiên đoán nhị phân tỷ lệ thấp, và phải theo dữ liệu cụ thể | PMID:26964707; DOI:10.1016/j.jclinepi.2016.02.031 |
| TRIPOD+AI (2024) — mục 10 | Giải trình cỡ mẫu RIÊNG cho phát triển và cho đánh giá mô hình, kèm chi tiết phép tính; thay thế hoàn toàn TRIPOD 2015 | PMID:38626948; DOI:10.1136/bmj-2023-078378 |
| Green SB, 1991 | Quy tắc n ≥ 104 + m cho kiểm định từng hệ số hồi quy đa biến | PMID:26776715; DOI:10.1207/s15327906mbr2603_7 |
| STARD 2015 — mục 18 | Nêu cỡ mẫu DỰ KIẾN và cách xác định, cho nghiên cứu độ chính xác chẩn đoán | PMID:26511519; DOI:10.1136/bmj.h5527 |
| STARD-AI (2025) | Bản MỞ RỘNG (không thay thế STARD 2015) khi test chỉ số là mô hình AI; đòi cỡ mẫu của từng tập huấn luyện/hiệu chỉnh/kiểm định | PMID:40954311; DOI:10.1038/s41591-025-03953-8 |
| Buderer NMF, 1996 | Cỡ mẫu độ nhạy/độ đặc hiệu quy ra TỔNG N qua tỷ lệ hiện mắc (N_Se = n_Se/prev; N_Sp = n_Sp/(1−prev); lấy max) | PMID:8870764; DOI:10.1111/j.1553-2712.1996.tb03538.x |
| Connor RJ, 1987 | Cỡ mẫu so sánh hai test GHÉP CẶP trên cùng bệnh nhân (nền tảng McNemar) | PMID:3567305 |
| STROBE — mục 10 (Study size) | Nghiên cứu quan sát phải giải thích cỡ mẫu đến từ đâu: theo công thức, hoặc do ràng buộc thực tế (và nói rõ ràng buộc đó) | https://pmc.ncbi.nlm.nih.gov/articles/PMC2020496/ |
| Hajian-Tilaki K, 2011 | Cỡ mẫu ước lượng MỘT tỷ lệ theo sai số biên d; dùng p=0,5 khi chưa biết tỷ lệ thì phải ghi rõ lý do (phương sai lớn nhất) | PMID:24551434 |
| Malterud K và cs., 2016 — information power | Khung quyết định cỡ mẫu định tính theo 5 chiều, thay cho công thức power | PMID:26613970; DOI:10.1177/1049732315617444 |
| COREQ (2007) / SRQR (2014) | Chuẩn báo cáo nghiên cứu định tính — khai số người tham gia và lý lẽ | PMID:17872937; DOI:10.1093/intqhc/mzm042 |
| Wetterslev J và cs., 2017 — TSA/RIS | Tổng quan hệ thống không dùng công thức power theo nhóm; dùng required information size có hiệu chỉnh dị biệt (D²/I²) | PMID:28264661; DOI:10.1186/s12874-017-0315-7 |
| FDA Guidance — Non-Inferiority Clinical Trials (11/2016) | Tách bạch M1 (toàn bộ hiệu quả thuốc chứng, cận dưới KTC từ dữ liệu lịch sử) và M2 (chênh lệch tối đa chấp nhận được về lâm sàng) | https://www.fda.gov/media/78504/download |
| EMA/CHMP — Choice of the non-inferiority margin (EMEA/CPMP/EWP/2158/99) | Biên Δ phải biện minh trong đề cương; CẤM định nghĩa Δ như một TỶ LỆ của hiệu số thuốc chứng–giả dược, CẤM dùng effect size chuẩn hoá, CẤM nới Δ vì nghiên cứu nhỏ. (Đang có bản dự thảo thay thế EMA/301654/2025 — rà lại.) | https://www.ema.europa.eu/en/choice-non-inferiority-margin-scientific-guideline |
| CONSORT extension — non-inferiority/equivalence (Piaggio 2012) | Khai khung NI/tương đương ở tiêu đề, giả thuyết, cỡ mẫu và một/hai phía | PMID:23268518; DOI:10.1001/jama.2012.87802 |
| CONSORT extension — cluster randomised trials (2012), mục 7a | Nêu cách tính, SỐ CHÙM (và giả định cỡ chùm đều/không đều), cỡ chùm, ICC và độ bất định của ICC | PMID:22951546; DOI:10.1136/bmj.e5661 |
| CONSORT extension — stepped wedge CRT (2018) | SW-CRT KHÔNG dùng được DE = 1+(m−1)·ICC đơn giản; phải khai đủ tham số tương quan để tái lập phép tính | PMID:30413417; DOI:10.1136/bmj.k1614 |
| Kahan BC và cs., 2016 | Số chùm nhỏ làm lạm phát sai lầm loại I — cần hiệu chỉnh mẫu nhỏ (Kenward-Roger/Satterthwaite hoặc sandwich hiệu chỉnh) | PMID:27600609; DOI:10.1186/s13063-016-1571-2 |
| Eldridge SM và cs., 2006 | Cỡ chùm không đều: cần hệ số biến thiên CV; CV < 0,23 thì ảnh hưởng không đáng kể, từ 0,23 trở lên phải hiệu chỉnh | PMID:16943232; DOI:10.1093/ije/dyl129 |

## Giới hạn phán định
PASS_G3_CONFIRMED chỉ xác nhận rằng từng giả định đưa vào phép tính cỡ mẫu đã có nguồn khai báo và đã được người nhận vai trò thống kê viên/chủ nhiệm xác nhận. G3 KHÔNG phải cổng ký mật mã: chữ ký sổ cái không áp dụng cho cổng này, nên đây là lời tự khai có dấu vết, không phải bằng chứng độc lập. Hợp đồng này cũng không kiểm được tính đúng đắn lâm sàng của effect size — việc đó thuộc thống kê viên và bác sĩ.

> Cần bác sĩ kiểm chứng.
