# Sổ quyết định của hội đồng nghiên cứu — hai-long-benh-nhan-C1a-BVQY175

- Ngày: 22/11/2026
- Căn cứ giao việc: bác sĩ chủ nhiệm 22/11/2026 — hội đồng của hệ giải quyết dữ kiện/quyết định chuyên môn, quản lý xung đột lợi ích, hoàn thiện SAP; bác sĩ chốt đề tài/mục tiêu, nhập số liệu thật và ký.
- Mỗi quyết định có căn cứ kiểm được (chuẩn, nguồn PMID/DOI đã kiểm rút bài, văn bản pháp quy, hoặc dữ kiện trong hồ sơ). Thay thế chỉ áp khi đoạn cũ xuất hiện đúng một lần.

## Thành viên: `hai-long-benh-nhan-C1a-BVQY175_tong_quan_tltk.json`

### TQ-SANRA-01 — Mô tả tìm kiếm của chương tổng quan chưa đủ PRISMA-S mục 8/13 (SANRA mục 3): câu tìm rút gọn/mô tả bằng lời, ngày tra lệch hồ sơ G0, sổ đăng ký thiếu kết quả

- Quyết định: Ghi câu tìm ĐẦY ĐỦ và ngày tra lấy nguyên văn từ hồ sơ G0 (nhật ký PRISMA-S, registry_check, phiếu ICTRP); nguồn không lưu câu tìm thì ghi rõ là không lưu, không dựng lại
- Căn cứ: G0_TIM_BO_SUNG_PRISMA_S_hai-long-benh-nhan-C1a-BVQY175.md dòng 80: chuỗi nhánh C ngày 2026-10-17, 31 hit
- Căn cứ: G0_checkpoint.json registry_check: query_gui_ctgov, n_trials=5, n_active=3, checked_at=2026-10-14T18:22:26
- Căn cứ: PRISMA-S mục 13 (ngày tra)
- Căn cứ: PRISMA-S mục 8
- Căn cứ: PRISMA-S mục 8 (chiến lược tìm đầy đủ, PMID 34285662); SANRA mục 3 (PMID 30962953)
- Căn cứ: study_meta.json gate_params.G0.registry_manual_checked: ictrp=2026-10-17, ictrp_ket_qua «không thấy nghiên cứu trùng»
- Căn cứ: study_meta.json gate_params.G0.registry_overlap_assessment
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 268
  - Cũ: | PubMed/MEDLINE | `("intraclass correlation"[tiab] OR ICC[tiab] OR multilevel[tiab] OR hierarchical[tiab] OR "Multilevel Analysis"[Mesh] OR clustering[tiab]) AND ("Patient Satisfaction"[Mesh] OR satisf*[tiab]) AND ("Vietnam"[Mesh] OR vietnam[tiab])` (chuỗi đầy đủ lưu trong hồ sơ tra cứu) | 17/10/2026 | 31 kết quả; tìm nhắm đúng hệ số tương quan nội cụm và phân tích đa mức |
  - Mới: | PubMed/MEDLINE | `("intraclass correlation"[tiab] OR "intra-class correlation"[tiab] OR ICC[tiab] OR multilevel[tiab] OR "multi-level"[tiab] OR hierarchical[tiab] OR "Multilevel Analysis"[Mesh] OR clustering[tiab]) AND ("Patient Satisfaction"[Mesh] OR satisf*[tiab] OR "patient experience"[tiab]) AND ("Vietnam"[Mesh] OR vietnam[tiab] OR "viet nam"[tiab])` | 17/10/2026 | 31 kết quả; tìm nhắm đúng hệ số tương quan nội cụm và phân tích đa mức |
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 271
  - Cũ: | ClinicalTrials.gov | Hài lòng người bệnh ngoại trú tại Việt Nam | 14/10/2026 | Không có nghiên cứu đăng ký trùng câu hỏi |
  - Mới: | ClinicalTrials.gov | `("Patient Satisfaction" OR satisf* OR "patient experience" ) AND ("Outpatients" OR "Ambulatory Care" OR outpatient* OR ambulatory ) AND ("Vietnam" OR vietnam* OR "viet nam" )` | 14/10/2026 | 5 hồ sơ, 3 đang hoặc sắp tuyển; theo tiêu đề và bệnh/tình trạng đăng ký, không hồ sơ nào trùng câu hỏi |
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 272
  - Cũ: | WHO ICTRP | Tra thủ công | 11/10/2026 | Không thấy nghiên cứu trùng |
  - Mới: | WHO ICTRP | Tra thủ công trên cổng tìm kiếm ICTRP; câu tìm không được lưu khi tra | 17/10/2026 | Không thấy nghiên cứu trùng |

### TLTK-NLM-01 — Trang/mã bài của TLTK lệch hoặc thiếu so với nguồn (NLM Citing Medicine: trang rút gọn như PubMed)

- Quyết định: Ghi trang/mã bài theo PubMed (mục có PMID) hoặc Crossref (mục chỉ có DOI) — K13
- Căn cứ: trang/mã bài theo PubMed «1373-9» (PMID 8970487)
- Căn cứ: trang/mã bài theo PubMed «2257-71» (PMID 8134732)
- Căn cứ: trang/mã bài theo PubMed «2409-19» (PMID 12210625)
- Căn cứ: trang/mã bài theo PubMed «344-9» (PMID 18313558)
- Căn cứ: trang/mã bài theo PubMed «459-67» (PMID 17654487)
- Căn cứ: trang/mã bài theo PubMed «737-45» (PMID 20494804)
- Căn cứ: trang/mã bài theo PubMed «785-94» (PMID 15485730)
- Căn cứ: trang/mã bài theo PubMed «809-16» (PMID 9762873)
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 1030
  - Cũ: 13. Adams G, Gulliford MC, Ukoumunne OC, Eldridge S, Chinn S, Campbell MJ. Patterns of intra-cluster correlation from primary care research to inform study design and analysis. J Clin Epidemiol. 2004;57(8):785-794. doi:10.1016/j.jclinepi.2003.12.013. PMID: 15485730.
  - Mới: 13. Adams G, Gulliford MC, Ukoumunne OC, Eldridge S, Chinn S, Campbell MJ. Patterns of intra-cluster correlation from primary care research to inform study design and analysis. J Clin Epidemiol. 2004;57(8):785-94. doi:10.1016/j.jclinepi.2003.12.013. PMID: 15485730.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 1033
  - Cũ: 16. Bender R, Grouven U. Using binary logistic regression models for ordinal data with non-proportional odds. J Clin Epidemiol. 1998;51(10):809-816. doi:10.1016/s0895-4356(98)00066-3. PMID: 9762873.
  - Mới: 16. Bender R, Grouven U. Using binary logistic regression models for ordinal data with non-proportional odds. J Clin Epidemiol. 1998;51(10):809-16. doi:10.1016/s0895-4356(98)00066-3. PMID: 9762873.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 1043
  - Cũ: 26. Heinze G, Schemper M. A solution to the problem of separation in logistic regression. Stat Med. 2002;21(16):2409-2419. doi:10.1002/sim.1047. PMID: 12210625.
  - Mới: 26. Heinze G, Schemper M. A solution to the problem of separation in logistic regression. Stat Med. 2002;21(16):2409-19. doi:10.1002/sim.1047. PMID: 12210625.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 1054
  - Cũ: 37. Mokkink LB, Terwee CB, Patrick DL, Alonso J, Stratford PW, Knol DL, et al. The COSMIN study reached international consensus on taxonomy, terminology, and definitions of measurement properties for health-related patient-reported outcomes. J Clin Epidemiol. 2010;63(7):737-745. doi:10.1016/j.jclinepi.2010.02.006. PMID: 20494804.
  - Mới: 37. Mokkink LB, Terwee CB, Patrick DL, Alonso J, Stratford PW, Knol DL, et al. The COSMIN study reached international consensus on taxonomy, terminology, and definitions of measurement properties for health-related patient-reported outcomes. J Clin Epidemiol. 2010;63(7):737-45. doi:10.1016/j.jclinepi.2010.02.006. PMID: 20494804.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 1057
  - Cũ: 40. Peduzzi P, Concato J, Kemper E, Holford TR, Feinstein AR. A simulation study of the number of events per variable in logistic regression analysis. J Clin Epidemiol. 1996;49(12):1373-1379. doi:10.1016/s0895-4356(96)00236-3. PMID: 8970487.
  - Mới: 40. Peduzzi P, Concato J, Kemper E, Holford TR, Feinstein AR. A simulation study of the number of events per variable in logistic regression analysis. J Clin Epidemiol. 1996;49(12):1373-9. doi:10.1016/s0895-4356(96)00236-3. PMID: 8970487.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 1058
  - Cũ: 41. Polit DF, Beck CT, Owen SV. Is the CVI an acceptable indicator of content validity? Appraisal and recommendations. Res Nurs Health. 2007;30(4):459-467. doi:10.1002/nur.20199. PMID: 17654487.
  - Mới: 41. Polit DF, Beck CT, Owen SV. Is the CVI an acceptable indicator of content validity? Appraisal and recommendations. Res Nurs Health. 2007;30(4):459-67. doi:10.1002/nur.20199. PMID: 17654487.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 1075
  - Cũ: 58. von Elm E, Altman DG, Egger M, Pocock SJ, Gøtzsche PC, Vandenbroucke JP; STROBE Initiative. The Strengthening the Reporting of Observational Studies in Epidemiology (STROBE) statement: guidelines for reporting observational studies. J Clin Epidemiol. 2008;61(4):344-349. doi:10.1016/j.jclinepi.2007.11.008. PMID: 18313558.
  - Mới: 58. von Elm E, Altman DG, Egger M, Pocock SJ, Gøtzsche PC, Vandenbroucke JP; STROBE Initiative. The Strengthening the Reporting of Observational Studies in Epidemiology (STROBE) statement: guidelines for reporting observational studies. J Clin Epidemiol. 2008;61(4):344-9. doi:10.1016/j.jclinepi.2007.11.008. PMID: 18313558.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 1076
  - Cũ: 59. Whitehead J. Sample size calculations for ordered categorical data. Stat Med. 1993;12(24):2257-2271. doi:10.1002/sim.4780122404. PMID: 8134732.
  - Mới: 59. Whitehead J. Sample size calculations for ordered categorical data. Stat Med. 1993;12(24):2257-71. doi:10.1002/sim.4780122404. PMID: 8134732.

### TLTK-NLM-02 — TLTK có PMID mà PubMed có PMCID chưa ghi PMCID (bác sĩ: ghi đủ PMID/PMCID/DOI khi có)

- Quyết định: Thêm «PMCID: PMC…» lấy từ ArticleIdList của bản ghi PubMed (biên nhận A12 chạy lại 22/11/2026) — K13
- Căn cứ: PMCID PMC11821282 theo PubMed (ArticleIdList)
- Căn cứ: PMCID PMC12039015 theo PubMed (ArticleIdList)
- Căn cứ: PMCID PMC12106881 theo PubMed (ArticleIdList)
- Căn cứ: PMCID PMC12464433 theo PubMed (ArticleIdList)
- Căn cứ: PMCID PMC13458290 theo PubMed (ArticleIdList)
- Căn cứ: PMCID PMC13490074 theo PubMed (ArticleIdList)
- Căn cứ: PMCID PMC2714692 theo PubMed (ArticleIdList)
- Căn cứ: PMCID PMC3722414 theo PubMed (ArticleIdList)
- Căn cứ: PMCID PMC4595218 theo PubMed (ArticleIdList)
- Căn cứ: PMCID PMC4837507 theo PubMed (ArticleIdList)
- Căn cứ: PMCID PMC5122171 theo PubMed (ArticleIdList)
- Căn cứ: PMCID PMC5482327 theo PubMed (ArticleIdList)
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 1029
  - Cũ: 12. Abma IL, Rovers M, van der Wees PJ. Appraising convergent validity of patient-reported outcome measures in systematic reviews: constructing hypotheses and interpreting outcomes. BMC Res Notes. 2016;9:226. doi:10.1186/s13104-016-2034-2. PMID: 27094345.
  - Mới: 12. Abma IL, Rovers M, van der Wees PJ. Appraising convergent validity of patient-reported outcome measures in systematic reviews: constructing hypotheses and interpreting outcomes. BMC Res Notes. 2016;9:226. doi:10.1186/s13104-016-2034-2. PMID: 27094345. PMCID: PMC4837507.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 1031
  - Cũ: 14. Badejo MA, Ramtin S, Rossano A, Ring D, Koenig K, Crijns TJ. Does adjusting for social desirability reduce ceiling effects and increase variation of patient-reported experience measures? J Patient Exp. 2022;9:23743735221079144. doi:10.1177/23743735221079144. PMID: 35155757.
  - Mới: 14. Badejo MA, Ramtin S, Rossano A, Ring D, Koenig K, Crijns TJ. Does adjusting for social desirability reduce ceiling effects and increase variation of patient-reported experience measures? J Patient Exp. 2022;9:23743735221079144. doi:10.1177/23743735221079144. PMID: 35155757. PMCID: PMC8829720.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 1032
  - Cũ: 15. Benchimol EI, Smeeth L, Guttmann A, Harron K, Moher D, Petersen I, et al.; RECORD Working Committee. The REporting of studies Conducted using Observational Routinely-collected health Data (RECORD) statement. PLoS Med. 2015;12(10):e1001885. doi:10.1371/journal.pmed.1001885. PMID: 26440803.
  - Mới: 15. Benchimol EI, Smeeth L, Guttmann A, Harron K, Moher D, Petersen I, et al.; RECORD Working Committee. The REporting of studies Conducted using Observational Routinely-collected health Data (RECORD) statement. PLoS Med. 2015;12(10):e1001885. doi:10.1371/journal.pmed.1001885. PMID: 26440803. PMCID: PMC4595218.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 1036
  - Cũ: 19. Bull C, Byrnes J, Hettiarachchi R, Downes M. A systematic review of the validity and reliability of patient-reported experience measures. Health Serv Res. 2019;54(5):1023-1035. doi:10.1111/1475-6773.13187. PMID: 31218671.
  - Mới: 19. Bull C, Byrnes J, Hettiarachchi R, Downes M. A systematic review of the validity and reliability of patient-reported experience measures. Health Serv Res. 2019;54(5):1023-1035. doi:10.1111/1475-6773.13187. PMID: 31218671. PMCID: PMC6736915.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 1038
  - Cũ: 21. Dang KT, Quang NA, Nguyen MH, Huynh NB, Nguyen NT, Pham TT, et al. Outpatient satisfaction assessed using a nationally standardized questionnaire: a survey of five health care facilities in Vietnam. Front Health Serv. 2026;6:1844842. doi:10.3389/frhs.2026.1844842. PMID: 42625778.
  - Mới: 21. Dang KT, Quang NA, Nguyen MH, Huynh NB, Nguyen NT, Pham TT, et al. Outpatient satisfaction assessed using a nationally standardized questionnaire: a survey of five health care facilities in Vietnam. Front Health Serv. 2026;6:1844842. doi:10.3389/frhs.2026.1844842. PMID: 42625778. PMCID: PMC13490074.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 1039
  - Cũ: 22. Dibba Y, Boima F, Jerome JG, Watson SI, Chery L, Higgins J, et al. Patient satisfaction and its associated factors in selected primary healthcare facilities in Kono District, Sierra Leone: a cross-sectional study. BMJ Open. 2025;15(4):e093501. doi:10.1136/bmjopen-2024-093501. PMID: 40295132.
  - Mới: 22. Dibba Y, Boima F, Jerome JG, Watson SI, Chery L, Higgins J, et al. Patient satisfaction and its associated factors in selected primary healthcare facilities in Kono District, Sierra Leone: a cross-sectional study. BMJ Open. 2025;15(4):e093501. doi:10.1136/bmjopen-2024-093501. PMID: 40295132. PMCID: PMC12039015.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 1040
  - Cũ: 23. Duc Thanh N, My Anh BT, Xiem CH, Quynh Anh P, Tien PH, Thi Phuong Thanh N, et al. Patient satisfaction with healthcare service quality and its associated factors at one polyclinic in Hanoi, Vietnam. Int J Public Health. 2022;67:1605055. doi:10.3389/ijph.2022.1605055. PMID: 36439278.
  - Mới: 23. Duc Thanh N, My Anh BT, Xiem CH, Quynh Anh P, Tien PH, Thi Phuong Thanh N, et al. Patient satisfaction with healthcare service quality and its associated factors at one polyclinic in Hanoi, Vietnam. Int J Public Health. 2022;67:1605055. doi:10.3389/ijph.2022.1605055. PMID: 36439278. PMCID: PMC9684178.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 1045
  - Cũ: 28. Hwang J, Vu GT, Tran BX, Nguyen THT, Nguyen BV, Nguyen LH, et al. Measuring satisfaction with health care services for Vietnamese patients with cardiovascular diseases. PLoS One. 2020;15(6):e0235333. doi:10.1371/journal.pone.0235333. PMID: 32584904.
  - Mới: 28. Hwang J, Vu GT, Tran BX, Nguyen THT, Nguyen BV, Nguyen LH, et al. Measuring satisfaction with health care services for Vietnamese patients with cardiovascular diseases. PLoS One. 2020;15(6):e0235333. doi:10.1371/journal.pone.0235333. PMID: 32584904. PMCID: PMC7316281.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 1048
  - Cũ: 31. Lee H, Cashin AG, Lamb SE, Hopewell S, Vansteelandt S, VanderWeele TJ, et al.; AGReMA group. A guideline for reporting mediation analyses of randomized trials and observational studies: the AGReMA statement. JAMA. 2021;326(11):1045-1056. doi:10.1001/jama.2021.14075. PMID: 34546296.
  - Mới: 31. Lee H, Cashin AG, Lamb SE, Hopewell S, Vansteelandt S, VanderWeele TJ, et al.; AGReMA group. A guideline for reporting mediation analyses of randomized trials and observational studies: the AGReMA statement. JAMA. 2021;326(11):1045-1056. doi:10.1001/jama.2021.14075. PMID: 34546296. PMCID: PMC8974292.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 1049
  - Cũ: 32. Li Y, Gong W, Kong X, Mueller O, Lu G. Factors associated with outpatient satisfaction in tertiary hospitals in China: a systematic review. Int J Environ Res Public Health. 2020;17(19):7070. doi:10.3390/ijerph17197070. PMID: 32992600.
  - Mới: 32. Li Y, Gong W, Kong X, Mueller O, Lu G. Factors associated with outpatient satisfaction in tertiary hospitals in China: a systematic review. Int J Environ Res Public Health. 2020;17(19):7070. doi:10.3390/ijerph17197070. PMID: 32992600. PMCID: PMC7579147.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 1052
  - Cũ: 35. Mahajan P, Anand A, Hossain S, Vishwakarma M. Exploring patient satisfaction and determinants in outpatient services: a cross-sectional study. Cureus. 2025;17(1):e77345. doi:10.7759/cureus.77345. PMID: 39944421.
  - Mới: 35. Mahajan P, Anand A, Hossain S, Vishwakarma M. Exploring patient satisfaction and determinants in outpatient services: a cross-sectional study. Cureus. 2025;17(1):e77345. doi:10.7759/cureus.77345. PMID: 39944421. PMCID: PMC11821282.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 1055
  - Cũ: 38. Nguyen BQ, Nguyen CTT. An assessment of outpatient satisfaction with hospital pharmacy quality and influential factors in the context of the COVID-19 pandemic. Healthcare (Basel). 2022;10(10):1945. doi:10.3390/healthcare10101945. PMID: 36292392.
  - Mới: 38. Nguyen BQ, Nguyen CTT. An assessment of outpatient satisfaction with hospital pharmacy quality and influential factors in the context of the COVID-19 pandemic. Healthcare (Basel). 2022;10(10):1945. doi:10.3390/healthcare10101945. PMID: 36292392. PMCID: PMC9601799.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 1056
  - Cũ: 39. Nguyen T, Nguyen H, Dang A. Determinants of patient satisfaction: lessons from large-scale inpatient interviews in Vietnam. PLoS One. 2020;15(9):e0239306. doi:10.1371/journal.pone.0239306. PMID: 32946537.
  - Mới: 39. Nguyen T, Nguyen H, Dang A. Determinants of patient satisfaction: lessons from large-scale inpatient interviews in Vietnam. PLoS One. 2020;15(9):e0239306. doi:10.1371/journal.pone.0239306. PMID: 32946537. PMCID: PMC7500619.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 1059
  - Cũ: 42. Quyen BTT, Ha NT, Van Minh H. Outpatient satisfaction with primary health care services in Vietnam: multilevel analysis results from The Vietnam Health Facilities Assessment 2015. Health Psychol Open. 2021;8(1):20551029211015117. doi:10.1177/20551029211015117. PMID: 34017606.
  - Mới: 42. Quyen BTT, Ha NT, Van Minh H. Outpatient satisfaction with primary health care services in Vietnam: multilevel analysis results from The Vietnam Health Facilities Assessment 2015. Health Psychol Open. 2021;8(1):20551029211015117. doi:10.1177/20551029211015117. PMID: 34017606. PMCID: PMC8114273.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 1061
  - Cũ: 44. Sharma A, Minh Duc NT, Luu Lam Thang T, Nam NH, Ng SJ, Abbas KS, et al. A Consensus-Based Checklist for Reporting of Survey Studies (CROSS). J Gen Intern Med. 2021;36(10):3179-3187. doi:10.1007/s11606-021-06737-1. PMID: 33886027.
  - Mới: 44. Sharma A, Minh Duc NT, Luu Lam Thang T, Nam NH, Ng SJ, Abbas KS, et al. A Consensus-Based Checklist for Reporting of Survey Studies (CROSS). J Gen Intern Med. 2021;36(10):3179-3187. doi:10.1007/s11606-021-06737-1. PMID: 33886027. PMCID: PMC8481359.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 1063
  - Cũ: 46. Sterne JA, White IR, Carlin JB, Spratt M, Royston P, Kenward MG, et al. Multiple imputation for missing data in epidemiological and clinical research: potential and pitfalls. BMJ. 2009;338:b2393. doi:10.1136/bmj.b2393. PMID: 19564179.
  - Mới: 46. Sterne JA, White IR, Carlin JB, Spratt M, Royston P, Kenward MG, et al. Multiple imputation for missing data in epidemiological and clinical research: potential and pitfalls. BMJ. 2009;338:b2393. doi:10.1136/bmj.b2393. PMID: 19564179. PMCID: PMC2714692.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 1065
  - Cũ: 48. Terwee CB, Prinsen CAC, Chiarotto A, Westerman MJ, Patrick DL, Alonso J, et al. COSMIN methodology for evaluating the content validity of patient-reported outcome measures: a Delphi study. Qual Life Res. 2018;27(5):1159-1170. doi:10.1007/s11136-018-1829-0. PMID: 29550964.
  - Mới: 48. Terwee CB, Prinsen CAC, Chiarotto A, Westerman MJ, Patrick DL, Alonso J, et al. COSMIN methodology for evaluating the content validity of patient-reported outcome measures: a Delphi study. Qual Life Res. 2018;27(5):1159-1170. doi:10.1007/s11136-018-1829-0. PMID: 29550964. PMCID: PMC5891557.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 1067
  - Cũ: 50. Thang DX, Tuan HA, Nguyen CTT, Phuong DT, Thuy LT, Duc TN. A cross-sectional study of patients satisfaction with the pharmacy services at the 108 Military Central Hospital: determinants and implications. Health Sci Rep. 2025;8(5):e70868. doi:10.1002/hsr2.70868. PMID: 40432693.
  - Mới: 50. Thang DX, Tuan HA, Nguyen CTT, Phuong DT, Thuy LT, Duc TN. A cross-sectional study of patients satisfaction with the pharmacy services at the 108 Military Central Hospital: determinants and implications. Health Sci Rep. 2025;8(5):e70868. doi:10.1002/hsr2.70868. PMID: 40432693. PMCID: PMC12106881.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 1068
  - Cũ: 51. Thanh ND, Thanh TC, Nguyet HTM, Xiem CH. Perceived healthcare service quality of patients in the post COVID-19 pandemic: a cross-sectional study at a public district hospital in Vietnam. Health Sci Rep. 2026;9(8):e73018. doi:10.1002/hsr2.73018. PMID: 42582692.
  - Mới: 51. Thanh ND, Thanh TC, Nguyet HTM, Xiem CH. Perceived healthcare service quality of patients in the post COVID-19 pandemic: a cross-sectional study at a public district hospital in Vietnam. Health Sci Rep. 2026;9(8):e73018. doi:10.1002/hsr2.73018. PMID: 42582692. PMCID: PMC13458290.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 1069
  - Cũ: 52. Thayaparan AJ, Mahdi E. The Patient Satisfaction Questionnaire Short Form (PSQ-18) as an adaptable, reliable, and validated tool for use in various settings. Med Educ Online. 2013;18:21747. doi:10.3402/meo.v18i0.21747. PMID: 23883565.
  - Mới: 52. Thayaparan AJ, Mahdi E. The Patient Satisfaction Questionnaire Short Form (PSQ-18) as an adaptable, reliable, and validated tool for use in various settings. Med Educ Online. 2013;18:21747. doi:10.3402/meo.v18i0.21747. PMID: 23883565. PMCID: PMC3722414.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 1070
  - Cũ: 53. Tran BX, Dang AK, Vu GT, Tran TT, Latkin CA, Ho CSH, et al. Patient satisfaction with HIV services in Vietnam: status, service models and association with treatment outcome. PLoS One. 2019;14(11):e0223723. doi:10.1371/journal.pone.0223723. PMID: 31703089.
  - Mới: 53. Tran BX, Dang AK, Vu GT, Tran TT, Latkin CA, Ho CSH, et al. Patient satisfaction with HIV services in Vietnam: status, service models and association with treatment outcome. PLoS One. 2019;14(11):e0223723. doi:10.1371/journal.pone.0223723. PMID: 31703089. PMCID: PMC6839840.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 1071
  - Cũ: 54. Tran TD, Nguyen UV, Minh Nong V, Tran BX. Patient waiting time in the outpatient clinic at a central surgical hospital of Vietnam: implications for resource allocation. F1000Res. 2017;6:454. doi:10.12688/f1000research.11045.3. PMID: 28690831.
  - Mới: 54. Tran TD, Nguyen UV, Minh Nong V, Tran BX. Patient waiting time in the outpatient clinic at a central surgical hospital of Vietnam: implications for resource allocation. F1000Res. 2017;6:454. doi:10.12688/f1000research.11045.3. PMID: 28690831. PMCID: PMC5482327.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 1072
  - Cũ: 55. Tura MR, Amena N, Wondie WT, Olkaba BF, Egu LM, Tadesse B, et al. Patient satisfaction with outpatient department health service and associated factors at public hospitals in Ethiopia. Inquiry. 2025;62:469580251371387. doi:10.1177/00469580251371387. PMID: 40995744.
  - Mới: 55. Tura MR, Amena N, Wondie WT, Olkaba BF, Egu LM, Tadesse B, et al. Patient satisfaction with outpatient department health service and associated factors at public hospitals in Ethiopia. Inquiry. 2025;62:469580251371387. doi:10.1177/00469580251371387. PMID: 40995744. PMCID: PMC12464433.
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 1074
  - Cũ: 57. van Smeden M, de Groot JA, Moons KG, Collins GS, Altman DG, Eijkemans MJ, et al. No rationale for 1 variable per 10 events criterion for binary logistic regression analysis. BMC Med Res Methodol. 2016;16(1):163. doi:10.1186/s12874-016-0267-3. PMID: 27881078.
  - Mới: 57. van Smeden M, de Groot JA, Moons KG, Collins GS, Altman DG, Eijkemans MJ, et al. No rationale for 1 variable per 10 events criterion for binary logistic regression analysis. BMC Med Res Methodol. 2016;16(1):163. doi:10.1186/s12874-016-0267-3. PMID: 27881078. PMCID: PMC5122171.

### TLTK-NLM-03 — TLTK 24 có DOI nhưng thiếu PMID dù PubMed có bản ghi

- Quyết định: Thêm PMID 16943232 (DOI trên PubMed trùng DOI của TLTK; không rút bài) và trang theo PubMed
- Căn cứ: PubMed PMID 16943232: DOI 10.1093/ije/dyl129 trùng DOI của TLTK, Int J Epidemiol 2006;35(5):1292-300
- Căn cứ: check_citation_retraction.py --pmid 16943232: không rút bài (22/11/2026)
- Căn cứ: nap_endnote_de_tai.py (chạy khô): DOI 10.1093/ije/dyl129 → PMID 16943232
- Thay ở `DE_CUONG_NOP_HOI_DONG_hai-long-benh-nhan-C1a-BVQY175.md` dòng 1041
  - Cũ: 24. Eldridge SM, Ashby D, Kerry S. Sample size for cluster randomized trials: effect of coefficient of variation of cluster size and analysis method. Int J Epidemiol. 2006;35(5):1292-1300. doi:10.1093/ije/dyl129.
  - Mới: 24. Eldridge SM, Ashby D, Kerry S. Sample size for cluster randomized trials: effect of coefficient of variation of cluster size and analysis method. Int J Epidemiol. 2006;35(5):1292-300. doi:10.1093/ije/dyl129. PMID: 16943232.

## Tài liệu đưa vào gói ký (đã chuẩn bị theo các quyết định trên)

- Không phát sinh tài liệu ký mới.
