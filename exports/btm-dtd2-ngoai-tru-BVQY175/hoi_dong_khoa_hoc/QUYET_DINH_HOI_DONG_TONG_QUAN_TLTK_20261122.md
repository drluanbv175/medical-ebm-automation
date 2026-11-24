# Sổ quyết định của hội đồng nghiên cứu — btm-dtd2-ngoai-tru-BVQY175

- Ngày: 22/11/2026
- Căn cứ giao việc: bác sĩ chủ nhiệm 22/11/2026 — hội đồng của hệ giải quyết dữ kiện/quyết định chuyên môn, quản lý xung đột lợi ích, hoàn thiện SAP; bác sĩ chốt đề tài/mục tiêu, nhập số liệu thật và ký.
- Mỗi quyết định có căn cứ kiểm được (chuẩn, nguồn PMID/DOI đã kiểm rút bài, văn bản pháp quy, hoặc dữ kiện trong hồ sơ). Thay thế chỉ áp khi đoạn cũ xuất hiện đúng một lần.

## Thành viên: `btm-dtd2-ngoai-tru-BVQY175_tong_quan_tltk.json`

### TQ-SANRA-01 — Mô tả tìm kiếm của chương tổng quan chưa đủ PRISMA-S mục 8/13 (SANRA mục 3): câu tìm rút gọn/mô tả bằng lời, ngày tra lệch hồ sơ G0, sổ đăng ký thiếu kết quả

- Quyết định: Ghi câu tìm ĐẦY ĐỦ và ngày tra lấy nguyên văn từ hồ sơ G0 (nhật ký PRISMA-S, registry_check, phiếu ICTRP); nguồn không lưu câu tìm thì ghi rõ là không lưu, không dựng lại
- Căn cứ: G0_TONG_HOP_BANG_CHUNG_btm-dtd2-ngoai-tru-BVQY175.json, khoá cach_tim của nguon_bo_sung (chuỗi tìm, tra 2026-10-25)
- Căn cứ: G0_TRA_ICTRP_20261028.md: ba lượt tra (150 bản ghi/60 thử nghiệm; 138/95; 3/3) và kết luận không trùng
- Căn cứ: G0_checkpoint.json registry_check: n_trials=0, checked_at=2026-10-25
- Căn cứ: PRISMA-S mục 1, 8, 13 (PMID 34285662); SANRA mục 3 (PMID 30962953)
- Thay ở `DE_CUONG_NOP_HOI_DONG_btm-dtd2-ngoai-tru-BVQY175.md` dòng 207
  - Cũ: Các hướng dẫn thực hành KDIGO 2022, KDIGO 2024 và ADA 2026 được tra trực tiếp theo tên.
  - Mới: Các hướng dẫn thực hành KDIGO 2022, KDIGO 2024 và ADA 2026 được tra trực tiếp theo tên. Câu tìm đầy đủ của các đường tìm bổ sung (cùng ngày 25/10/2026): đường (2), PubMed: `albuminuria testing[Title/Abstract] AND (diabetes OR hypertension) AND (underuse OR testing rates OR care gap OR low)`; đường (3), PubMed: `(Vietnam[Title/Abstract] OR Vietnamese[Title/Abstract]) AND (SGLT2 OR sodium-glucose OR albuminuria screening OR urine albumin OR UACR) AND (outpatient* OR prescribing OR testing OR guideline adherence)` và `(Vietnam OR Vietnamese) AND (chronic kidney disease OR albuminuria OR diabetic kidney disease) AND type 2 diabetes`; đường (4), Crossref, lọc bài tạp chí từ năm 2018: ba cụm đã nêu, thêm cụm “tỷ số albumin creatinin niệu xét nghiệm tầm soát bệnh thận đái tháo đường” và cụm “đái tháo đường ngoại trú SGLT2 thuốc ức chế men chuyển” giới hạn ở Tạp chí Y Dược Thực hành 175 (tiền tố DOI 10.59354). Sổ đăng ký nghiên cứu: ClinicalTrials.gov ngày 25/10/2026 theo cùng chiến lược tìm kiếm (0 hồ sơ); WHO ICTRP ngày 28/10/2026 với ba lượt tra – bệnh “diabetes” tại Việt Nam (60 thử nghiệm), tiêu đề “albuminuria” kèm bệnh “diabetes” ở mọi quốc gia (95 thử nghiệm) và nhà tài trợ chính chứa “175” tại Việt Nam (3 thử nghiệm) – không có nghiên cứu nào trùng câu hỏi của đề tài.

### TLTK-NLM-01 — Trang/mã bài của TLTK lệch hoặc thiếu so với nguồn (NLM Citing Medicine: trang rút gọn như PubMed)

- Quyết định: Ghi trang/mã bài theo PubMed (mục có PMID) hoặc Crossref (mục chỉ có DOI) — K13
- Căn cứ: PMCID PMC12113003 theo PubMed (ArticleIdList)
- Căn cứ: trang/mã bài theo PubMed «843» (PMID 40428801)
- Thay ở `DE_CUONG_NOP_HOI_DONG_btm-dtd2-ngoai-tru-BVQY175.md` dòng 837
  - Cũ: 42. Kostev K, Lang M, Tröbs SO, Urbisch S, Gabler M. The Underdiagnosis of Chronic Kidney Disease in Patients with a Documented Estimated Glomerular Filtration Rate and/or Urine Albumin-Creatinine Ratio in Germany. Medicina (Kaunas). 2025;61(5). doi:10.3390/medicina61050843. PMID: 40428801.
  - Mới: 42. Kostev K, Lang M, Tröbs SO, Urbisch S, Gabler M. The Underdiagnosis of Chronic Kidney Disease in Patients with a Documented Estimated Glomerular Filtration Rate and/or Urine Albumin-Creatinine Ratio in Germany. Medicina (Kaunas). 2025;61(5):843. doi:10.3390/medicina61050843. PMID: 40428801. PMCID: PMC12113003.

### TLTK-NLM-02 — TLTK có PMID mà PubMed có PMCID chưa ghi PMCID (bác sĩ: ghi đủ PMID/PMCID/DOI khi có)

- Quyết định: Thêm «PMCID: PMC…» lấy từ ArticleIdList của bản ghi PubMed (biên nhận A12 chạy lại 22/11/2026) — K13
- Căn cứ: PMCID PMC10212863 theo PubMed (ArticleIdList)
- Căn cứ: PMCID PMC11208975 theo PubMed (ArticleIdList)
- Căn cứ: PMCID PMC11328054 theo PubMed (ArticleIdList)
- Căn cứ: PMCID PMC11462144 theo PubMed (ArticleIdList)
- Căn cứ: PMCID PMC11538071 theo PubMed (ArticleIdList)
- Căn cứ: PMCID PMC12322385 theo PubMed (ArticleIdList)
- Căn cứ: PMCID PMC12348363 theo PubMed (ArticleIdList)
- Căn cứ: PMCID PMC12409226 theo PubMed (ArticleIdList)
- Căn cứ: PMCID PMC12690176 theo PubMed (ArticleIdList)
- Căn cứ: PMCID PMC12690183 theo PubMed (ArticleIdList)
- Căn cứ: PMCID PMC12690185 theo PubMed (ArticleIdList)
- Căn cứ: PMCID PMC12750594 theo PubMed (ArticleIdList)
- Thay ở `DE_CUONG_NOP_HOI_DONG_btm-dtd2-ngoai-tru-BVQY175.md` dòng 807
  - Cũ: 12. Albekery MA, Alhomoud IS, Alabdulathim LS, Almajed MA, Alobaid AA, Alomair MK, et al. Underutilization of albuminuria screening in adults with diabetes mellitus or hypertension: a systematic review and meta-analysis. BMC Nephrol. 2025;27(1):18. doi:10.1186/s12882-025-04672-5. PMID: 41345917.
  - Mới: 12. Albekery MA, Alhomoud IS, Alabdulathim LS, Almajed MA, Alobaid AA, Alomair MK, et al. Underutilization of albuminuria screening in adults with diabetes mellitus or hypertension: a systematic review and meta-analysis. BMC Nephrol. 2025;27(1):18. doi:10.1186/s12882-025-04672-5. PMID: 41345917. PMCID: PMC12781434.
- Thay ở `DE_CUONG_NOP_HOI_DONG_btm-dtd2-ngoai-tru-BVQY175.md` dòng 808
  - Cũ: 13. American Diabetes Association Professional Practice Committee for Diabetes. 11. Chronic Kidney Disease and Risk Management: Standards of Care in Diabetes-2026. Diabetes Care. 2026;49(Suppl 1):S246-S260. doi:10.2337/dc26-S011. PMID: 41358881.
  - Mới: 13. American Diabetes Association Professional Practice Committee for Diabetes. 11. Chronic Kidney Disease and Risk Management: Standards of Care in Diabetes-2026. Diabetes Care. 2026;49(Suppl 1):S246-S260. doi:10.2337/dc26-S011. PMID: 41358881. PMCID: PMC12690176.
- Thay ở `DE_CUONG_NOP_HOI_DONG_btm-dtd2-ngoai-tru-BVQY175.md` dòng 809
  - Cũ: 14. American Diabetes Association Professional Practice Committee for Diabetes. 2. Diagnosis and Classification of Diabetes: Standards of Care in Diabetes-2026. Diabetes Care. 2026;49(Suppl 1):S27-S49. doi:10.2337/dc26-S002. PMID: 41358893.
  - Mới: 14. American Diabetes Association Professional Practice Committee for Diabetes. 2. Diagnosis and Classification of Diabetes: Standards of Care in Diabetes-2026. Diabetes Care. 2026;49(Suppl 1):S27-S49. doi:10.2337/dc26-S002. PMID: 41358893. PMCID: PMC12690183.
- Thay ở `DE_CUONG_NOP_HOI_DONG_btm-dtd2-ngoai-tru-BVQY175.md` dòng 810
  - Cũ: 15. American Diabetes Association Professional Practice Committee for Diabetes. 9. Pharmacologic Approaches to Glycemic Treatment: Standards of Care in Diabetes-2026. Diabetes Care. 2026;49(Suppl 1):S183-S215. doi:10.2337/dc26-S009. PMID: 41358900.
  - Mới: 15. American Diabetes Association Professional Practice Committee for Diabetes. 9. Pharmacologic Approaches to Glycemic Treatment: Standards of Care in Diabetes-2026. Diabetes Care. 2026;49(Suppl 1):S183-S215. doi:10.2337/dc26-S009. PMID: 41358900. PMCID: PMC12690185.
- Thay ở `DE_CUONG_NOP_HOI_DONG_btm-dtd2-ngoai-tru-BVQY175.md` dòng 812
  - Cũ: 17. Awiphan R, Kowatcharakul W, Ruengorn C, Noppakun K, Thavorn K, Nochaiwong S. Temporal trend in quality indicators of diabetes care performance among persons with type 2 diabetes in primary care practice: a serial cross-sectional analytical study, 2013/14 to 2021/22. Front Endocrinol (Lausanne). 2024;15:1359904. doi:10.3389/fendo.2024.1359904. PMID: 39507052.
  - Mới: 17. Awiphan R, Kowatcharakul W, Ruengorn C, Noppakun K, Thavorn K, Nochaiwong S. Temporal trend in quality indicators of diabetes care performance among persons with type 2 diabetes in primary care practice: a serial cross-sectional analytical study, 2013/14 to 2021/22. Front Endocrinol (Lausanne). 2024;15:1359904. doi:10.3389/fendo.2024.1359904. PMID: 39507052. PMCID: PMC11538071.
- Thay ở `DE_CUONG_NOP_HOI_DONG_btm-dtd2-ngoai-tru-BVQY175.md` dòng 813
  - Cũ: 18. Barros AJ, Hirakata VN. Alternatives for logistic regression in cross-sectional studies: an empirical comparison of models that directly estimate the prevalence ratio. BMC Med Res Methodol. 2003;3:21. doi:10.1186/1471-2288-3-21. PMID: 14567763.
  - Mới: 18. Barros AJ, Hirakata VN. Alternatives for logistic regression in cross-sectional studies: an empirical comparison of models that directly estimate the prevalence ratio. BMC Med Res Methodol. 2003;3:21. doi:10.1186/1471-2288-3-21. PMID: 14567763. PMCID: PMC521200.
- Thay ở `DE_CUONG_NOP_HOI_DONG_btm-dtd2-ngoai-tru-BVQY175.md` dòng 814
  - Cũ: 19. Barrot-de la Puente J, Lopez Arpí C, Ramon Granes M, Escribà Planes M, Fernandez-Camins B, Vlacho B, et al. Chronic kidney disease screening in primary care: a descriptive analysis of the Girona Sud health region. BMC Prim Care. 2025;26(1):409. doi:10.1186/s12875-025-03117-0. PMID: 41276836.
  - Mới: 19. Barrot-de la Puente J, Lopez Arpí C, Ramon Granes M, Escribà Planes M, Fernandez-Camins B, Vlacho B, et al. Chronic kidney disease screening in primary care: a descriptive analysis of the Girona Sud health region. BMC Prim Care. 2025;26(1):409. doi:10.1186/s12875-025-03117-0. PMID: 41276836. PMCID: PMC12750594.
- Thay ở `DE_CUONG_NOP_HOI_DONG_btm-dtd2-ngoai-tru-BVQY175.md` dòng 815
  - Cũ: 20. Benchimol EI, Smeeth L, Guttmann A, Harron K, Moher D, Petersen I, et al.; RECORD Working Committee. The REporting of studies Conducted using Observational Routinely-collected health Data (RECORD) statement. PLoS Med. 2015;12(10):e1001885. doi:10.1371/journal.pmed.1001885. PMID: 26440803.
  - Mới: 20. Benchimol EI, Smeeth L, Guttmann A, Harron K, Moher D, Petersen I, et al.; RECORD Working Committee. The REporting of studies Conducted using Observational Routinely-collected health Data (RECORD) statement. PLoS Med. 2015;12(10):e1001885. doi:10.1371/journal.pmed.1001885. PMID: 26440803. PMCID: PMC4595218.
- Thay ở `DE_CUONG_NOP_HOI_DONG_btm-dtd2-ngoai-tru-BVQY175.md` dòng 817
  - Cũ: 22. Bui TD, Le PT, Dinh LNT, Nguyen THN, Doan TPT, Vo TTH, et al. Diagnostic Testing Patterns Influence the Detected Burden of Hypertension-Mediated Organ Damage in Hospitalized Hypertensive Patients. J Clin Hypertens (Greenwich). 2026;28(4):e70241. doi:10.1111/jch.70241. PMID: 41916900.
  - Mới: 22. Bui TD, Le PT, Dinh LNT, Nguyen THN, Doan TPT, Vo TTH, et al. Diagnostic Testing Patterns Influence the Detected Burden of Hypertension-Mediated Organ Damage in Hospitalized Hypertensive Patients. J Clin Hypertens (Greenwich). 2026;28(4):e70241. doi:10.1111/jch.70241. PMID: 41916900. PMCID: PMC13140622.
- Thay ở `DE_CUONG_NOP_HOI_DONG_btm-dtd2-ngoai-tru-BVQY175.md` dòng 822
  - Cũ: 27. Dang KD, Nguyen HMT, Phung YP, Le TQN. Optimising antidiabetic medication management for type 2 diabetes and renal dysfunction in Can Tho City, Vietnam. Prz Menopauzalny. 2024;23(2):75-82. doi:10.5114/pm.2024.141090. PMID: 39391521.
  - Mới: 27. Dang KD, Nguyen HMT, Phung YP, Le TQN. Optimising antidiabetic medication management for type 2 diabetes and renal dysfunction in Can Tho City, Vietnam. Prz Menopauzalny. 2024;23(2):75-82. doi:10.5114/pm.2024.141090. PMID: 39391521. PMCID: PMC11462144.
- Thay ở `DE_CUONG_NOP_HOI_DONG_btm-dtd2-ngoai-tru-BVQY175.md` dòng 824
  - Cũ: 29. Edmonston D, Lydon E, Mulder H, Chiswell K, Lampron Z, Marsolo K, et al. Concordance With Screening and Treatment Guidelines for Chronic Kidney Disease in Type 2 Diabetes. JAMA Netw Open. 2024;7(6):e2418808. doi:10.1001/jamanetworkopen.2024.18808. PMID: 38922613.
  - Mới: 29. Edmonston D, Lydon E, Mulder H, Chiswell K, Lampron Z, Marsolo K, et al. Concordance With Screening and Treatment Guidelines for Chronic Kidney Disease in Type 2 Diabetes. JAMA Netw Open. 2024;7(6):e2418808. doi:10.1001/jamanetworkopen.2024.18808. PMID: 38922613. PMCID: PMC11208975.
- Thay ở `DE_CUONG_NOP_HOI_DONG_btm-dtd2-ngoai-tru-BVQY175.md` dòng 826
  - Cũ: 31. Fernandez-Fernandez B, Gorriz JL, Cebrian-Cuenca A, Fácila L, Fernandez Rodriguez JM, Maraver MP, et al. From Evidence to Action: Advancing Timely Implementation of Triple Therapy in Type 2 Diabetes Mellitus and CKD. Kidney Int Rep. 2026;11(1):6-16. doi:10.1016/j.ekir.2025.09.027. PMID: 41541781.
  - Mới: 31. Fernandez-Fernandez B, Gorriz JL, Cebrian-Cuenca A, Fácila L, Fernandez Rodriguez JM, Maraver MP, et al. From Evidence to Action: Advancing Timely Implementation of Triple Therapy in Type 2 Diabetes Mellitus and CKD. Kidney Int Rep. 2026;11(1):6-16. doi:10.1016/j.ekir.2025.09.027. PMID: 41541781. PMCID: PMC12799545.
- Thay ở `DE_CUONG_NOP_HOI_DONG_btm-dtd2-ngoai-tru-BVQY175.md` dòng 830
  - Cũ: 35. Hao R, Myroniuk T, McGuckin T, Manca D, Campbell-Scherer D, Lau D, et al. Underuse of cardiorenal protective agents in high-risk diabetes patients in primary care: a cross-sectional study. BMC Prim Care. 2022;23(1):124. doi:10.1186/s12875-022-01731-w. PMID: 35606699.
  - Mới: 35. Hao R, Myroniuk T, McGuckin T, Manca D, Campbell-Scherer D, Lau D, et al. Underuse of cardiorenal protective agents in high-risk diabetes patients in primary care: a cross-sectional study. BMC Prim Care. 2022;23(1):124. doi:10.1186/s12875-022-01731-w. PMID: 35606699. PMCID: PMC9128222.
- Thay ở `DE_CUONG_NOP_HOI_DONG_btm-dtd2-ngoai-tru-BVQY175.md` dòng 831
  - Cũ: 36. Inker LA, Eneanya ND, Coresh J, Tighiouart H, Wang D, Sang Y, et al.; Chronic Kidney Disease Epidemiology Collaboration. New Creatinine- and Cystatin C-Based Equations to Estimate GFR without Race. N Engl J Med. 2021;385(19):1737-1749. doi:10.1056/NEJMoa2102953. PMID: 34554658.
  - Mới: 36. Inker LA, Eneanya ND, Coresh J, Tighiouart H, Wang D, Sang Y, et al.; Chronic Kidney Disease Epidemiology Collaboration. New Creatinine- and Cystatin C-Based Equations to Estimate GFR without Race. N Engl J Med. 2021;385(19):1737-1749. doi:10.1056/NEJMoa2102953. PMID: 34554658. PMCID: PMC8822996.
- Thay ở `DE_CUONG_NOP_HOI_DONG_btm-dtd2-ngoai-tru-BVQY175.md` dòng 832
  - Cũ: 37. Jones JL, Lumsden NG, Simons K, Ta'eed A, de Courten MP, Wijeratne T, et al. Using electronic medical record data to assess chronic kidney disease, type 2 diabetes and cardiovascular disease testing, recognition and management as documented in Australian general practice: a cross-sectional analysis. Fam Med Community Health. 2022;10(1):e001006. doi:10.1136/fmch-2021-001006. PMID: 35177470.
  - Mới: 37. Jones JL, Lumsden NG, Simons K, Ta'eed A, de Courten MP, Wijeratne T, et al. Using electronic medical record data to assess chronic kidney disease, type 2 diabetes and cardiovascular disease testing, recognition and management as documented in Australian general practice: a cross-sectional analysis. Fam Med Community Health. 2022;10(1):e001006. doi:10.1136/fmch-2021-001006. PMID: 35177470. PMCID: PMC8860071.
- Thay ở `DE_CUONG_NOP_HOI_DONG_btm-dtd2-ngoai-tru-BVQY175.md` dòng 833
  - Cũ: 38. Kam S, Angaramo S, Antoun J, Bhatta MR, Bonds PD, Cadar AG, et al. Improving annual albuminuria testing for individuals with diabetes. BMJ Open Qual. 2022;11(1):e001591. doi:10.1136/bmjoq-2021-001591. PMID: 35101868.
  - Mới: 38. Kam S, Angaramo S, Antoun J, Bhatta MR, Bonds PD, Cadar AG, et al. Improving annual albuminuria testing for individuals with diabetes. BMJ Open Qual. 2022;11(1):e001591. doi:10.1136/bmjoq-2021-001591. PMID: 35101868. PMCID: PMC8804706.
- Thay ở `DE_CUONG_NOP_HOI_DONG_btm-dtd2-ngoai-tru-BVQY175.md` dòng 836
  - Cũ: 41. Koo TK, Li MY. A Guideline of Selecting and Reporting Intraclass Correlation Coefficients for Reliability Research. J Chiropr Med. 2016;15(2):155-63. doi:10.1016/j.jcm.2016.02.012. PMID: 27330520.
  - Mới: 41. Koo TK, Li MY. A Guideline of Selecting and Reporting Intraclass Correlation Coefficients for Reliability Research. J Chiropr Med. 2016;15(2):155-63. doi:10.1016/j.jcm.2016.02.012. PMID: 27330520. PMCID: PMC4913118.
- Thay ở `DE_CUONG_NOP_HOI_DONG_btm-dtd2-ngoai-tru-BVQY175.md` dòng 840
  - Cũ: 45. Li PK, Cheung M, Chow KM, Leung MKW, Lim LL, Lui JNM, et al. Kidney Disease: Improving Global Outcomes Summit Recommendations on Implementation of Diabetes Management in CKD: From Primary to Data-Driven Collaborative Care. Kidney Int Rep. 2025;10(8):2551-2565. doi:10.1016/j.ekir.2025.06.010. PMID: 40814615.
  - Mới: 45. Li PK, Cheung M, Chow KM, Leung MKW, Lim LL, Lui JNM, et al. Kidney Disease: Improving Global Outcomes Summit Recommendations on Implementation of Diabetes Management in CKD: From Primary to Data-Driven Collaborative Care. Kidney Int Rep. 2025;10(8):2551-2565. doi:10.1016/j.ekir.2025.06.010. PMID: 40814615. PMCID: PMC12348363.
- Thay ở `DE_CUONG_NOP_HOI_DONG_btm-dtd2-ngoai-tru-BVQY175.md` dòng 841
  - Cũ: 46. Mahadevappa K, Nayak SB, Maharaj RG, Bhaktha G. Using eGFR and Albumin Creatinine Ratio as an Initial Screening Tool in Trinidadian Primary Care to Identify High-risk Population for CKD: A Cross-Sectional Study. Indian J Nephrol. 2024;34(4):332-337. doi:10.25259/ijn_451_23. PMID: 39156845.
  - Mới: 46. Mahadevappa K, Nayak SB, Maharaj RG, Bhaktha G. Using eGFR and Albumin Creatinine Ratio as an Initial Screening Tool in Trinidadian Primary Care to Identify High-risk Population for CKD: A Cross-Sectional Study. Indian J Nephrol. 2024;34(4):332-337. doi:10.25259/ijn_451_23. PMID: 39156845. PMCID: PMC11328054.
- Thay ở `DE_CUONG_NOP_HOI_DONG_btm-dtd2-ngoai-tru-BVQY175.md` dòng 842
  - Cũ: 47. Miyamoto Y, Xu F, Zaganjor I, Pavkov ME, Koyama AK, Onufrak S. Current attitudes of primary care providers toward albuminuria testing in patients with diabetes in the United States. Prev Med Rep. 2026;69:103581. doi:10.1016/j.pmedr.2026.103581. PMID: 42541306.
  - Mới: 47. Miyamoto Y, Xu F, Zaganjor I, Pavkov ME, Koyama AK, Onufrak S. Current attitudes of primary care providers toward albuminuria testing in patients with diabetes in the United States. Prev Med Rep. 2026;69:103581. doi:10.1016/j.pmedr.2026.103581. PMID: 42541306. PMCID: PMC13427520.
- Thay ở `DE_CUONG_NOP_HOI_DONG_btm-dtd2-ngoai-tru-BVQY175.md` dòng 843
  - Cũ: 48. Ogundimu EO, Altman DG, Collins GS. Adequate sample size for developing prediction models is not simply related to events per variable. J Clin Epidemiol. 2016;76:175-82. doi:10.1016/j.jclinepi.2016.02.031. PMID: 26964707.
  - Mới: 48. Ogundimu EO, Altman DG, Collins GS. Adequate sample size for developing prediction models is not simply related to events per variable. J Clin Epidemiol. 2016;76:175-82. doi:10.1016/j.jclinepi.2016.02.031. PMID: 26964707. PMCID: PMC5045274.
- Thay ở `DE_CUONG_NOP_HOI_DONG_btm-dtd2-ngoai-tru-BVQY175.md` dòng 844
  - Cũ: 49. Otieno FCF, Ogola EN, Kimando MW, Mutai K. The burden of unrecognised chronic kidney disease in patients with type 2 diabetes at a county hospital clinic in Kenya: implications to care and need for screening. BMC Nephrol. 2020;21(1):73. doi:10.1186/s12882-020-1705-3. PMID: 32111192.
  - Mới: 49. Otieno FCF, Ogola EN, Kimando MW, Mutai K. The burden of unrecognised chronic kidney disease in patients with type 2 diabetes at a county hospital clinic in Kenya: implications to care and need for screening. BMC Nephrol. 2020;21(1):73. doi:10.1186/s12882-020-1705-3. PMID: 32111192. PMCID: PMC7048110.
- Thay ở `DE_CUONG_NOP_HOI_DONG_btm-dtd2-ngoai-tru-BVQY175.md` dòng 845
  - Cũ: 50. Pasea L, Mohamed M, Dashtban A, Bhuva A, Mizani MA, Ali S, et al. Missed opportunities to manage complex comorbidity of heart failure, type 2 diabetes mellitus and chronic kidney disease: a retrospective cohort study. Heart. 2025;111(16):776-785. doi:10.1136/heartjnl-2024-325046. PMID: 40037768.
  - Mới: 50. Pasea L, Mohamed M, Dashtban A, Bhuva A, Mizani MA, Ali S, et al. Missed opportunities to manage complex comorbidity of heart failure, type 2 diabetes mellitus and chronic kidney disease: a retrospective cohort study. Heart. 2025;111(16):776-785. doi:10.1136/heartjnl-2024-325046. PMID: 40037768. PMCID: PMC12322385.
- Thay ở `DE_CUONG_NOP_HOI_DONG_btm-dtd2-ngoai-tru-BVQY175.md` dòng 849
  - Cũ: 54. Rikin S, Deccy S, Zhang C, Crandall J, Deng Y, Golestaneh L. Care Gaps in Sodium-Glucose Cotransporter-2 Inhibitor and Renin Angiotensin System Inhibitor Prescriptions for Patients with Diabetic Kidney Disease. J Gen Intern Med. 2023;38(7):1599-1605. doi:10.1007/s11606-022-07863-0. PMID: 36352203.
  - Mới: 54. Rikin S, Deccy S, Zhang C, Crandall J, Deng Y, Golestaneh L. Care Gaps in Sodium-Glucose Cotransporter-2 Inhibitor and Renin Angiotensin System Inhibitor Prescriptions for Patients with Diabetic Kidney Disease. J Gen Intern Med. 2023;38(7):1599-1605. doi:10.1007/s11606-022-07863-0. PMID: 36352203. PMCID: PMC10212863.
- Thay ở `DE_CUONG_NOP_HOI_DONG_btm-dtd2-ngoai-tru-BVQY175.md` dòng 851
  - Cũ: 56. Stefanska C, Chung R, Ramjaun S, Jin D, Doherty C, McCafferty K, et al. The SGLT2i Treatment Gap in UK Primary Care: A Cross-Sectional RWE Study of Prescribing in Clinical Practice. Diabetes Obes Metab. 2026;28(12):11278-11287. doi:10.1111/dom.71298. PMID: 42723263.
  - Mới: 56. Stefanska C, Chung R, Ramjaun S, Jin D, Doherty C, McCafferty K, et al. The SGLT2i Treatment Gap in UK Primary Care: A Cross-Sectional RWE Study of Prescribing in Clinical Practice. Diabetes Obes Metab. 2026;28(12):11278-11287. doi:10.1111/dom.71298. PMID: 42723263. PMCID: PMC13731052.
- Thay ở `DE_CUONG_NOP_HOI_DONG_btm-dtd2-ngoai-tru-BVQY175.md` dòng 852
  - Cũ: 57. Sterne JA, White IR, Carlin JB, Spratt M, Royston P, Kenward MG, et al. Multiple imputation for missing data in epidemiological and clinical research: potential and pitfalls. BMJ. 2009;338:b2393. doi:10.1136/bmj.b2393. PMID: 19564179.
  - Mới: 57. Sterne JA, White IR, Carlin JB, Spratt M, Royston P, Kenward MG, et al. Multiple imputation for missing data in epidemiological and clinical research: potential and pitfalls. BMJ. 2009;338:b2393. doi:10.1136/bmj.b2393. PMID: 19564179. PMCID: PMC2714692.
- Thay ở `DE_CUONG_NOP_HOI_DONG_btm-dtd2-ngoai-tru-BVQY175.md` dòng 854
  - Cũ: 59. van Smeden M, de Groot JA, Moons KG, Collins GS, Altman DG, Eijkemans MJ, et al. No rationale for 1 variable per 10 events criterion for binary logistic regression analysis. BMC Med Res Methodol. 2016;16(1):163. doi:10.1186/s12874-016-0267-3. PMID: 27881078.
  - Mới: 59. van Smeden M, de Groot JA, Moons KG, Collins GS, Altman DG, Eijkemans MJ, et al. No rationale for 1 variable per 10 events criterion for binary logistic regression analysis. BMC Med Res Methodol. 2016;16(1):163. doi:10.1186/s12874-016-0267-3. PMID: 27881078. PMCID: PMC5122171.
- Thay ở `DE_CUONG_NOP_HOI_DONG_btm-dtd2-ngoai-tru-BVQY175.md` dòng 855
  - Cũ: 60. Wallace H, Wick J, Neuen BL, Buizen L, Badve SV, Chalmers J, et al. Prevalence of SGLT2 inhibitor and GLP1 receptor agonist prescriptions in type 2 diabetes patients with and without chronic kidney disease: Analysis of an Australian primary care dataset. Diabetes Obes Metab. 2025;27(10):5599-5611. doi:10.1111/dom.16608. PMID: 40667713.
  - Mới: 60. Wallace H, Wick J, Neuen BL, Buizen L, Badve SV, Chalmers J, et al. Prevalence of SGLT2 inhibitor and GLP1 receptor agonist prescriptions in type 2 diabetes patients with and without chronic kidney disease: Analysis of an Australian primary care dataset. Diabetes Obes Metab. 2025;27(10):5599-5611. doi:10.1111/dom.16608. PMID: 40667713. PMCID: PMC12409226.
- Thay ở `DE_CUONG_NOP_HOI_DONG_btm-dtd2-ngoai-tru-BVQY175.md` dòng 857
  - Cũ: 62. Zahradka I, Petr V, Tichanek F, Chroma A, Neskudla T, Kahle M, et al. Prevalence, risk factors and renoprotective treatment of chronic kidney disease among internal medicine outpatients at a Central European tertiary care centre: a cross-sectional study. BMJ Open. 2026;16(10):e121190. doi:10.1136/bmjopen-2026-121190. PMID: 42838586.
  - Mới: 62. Zahradka I, Petr V, Tichanek F, Chroma A, Neskudla T, Kahle M, et al. Prevalence, risk factors and renoprotective treatment of chronic kidney disease among internal medicine outpatients at a Central European tertiary care centre: a cross-sectional study. BMJ Open. 2026;16(10):e121190. doi:10.1136/bmjopen-2026-121190. PMID: 42838586. PMCID: PMC13647024.

### TLTK-NLM-04 — Năm xuất bản của TLTK lệch nguồn đăng ký DOI

- Quyết định: Sửa năm theo bản ghi Crossref của chính DOI — K13
- Căn cứ: năm theo Crossref 2023 (DOI 10.56283/1859-0381/390)
- Thay ở `DE_CUONG_NOP_HOI_DONG_btm-dtd2-ngoai-tru-BVQY175.md` dòng 798
  - Cũ: 6. Phạm Đức Minh. Nồng độ microalbumin niệu và một số yếu tố liên quan ở bệnh nhân đái tháo đường týp 2 điều trị ngoại trú. Tạp chí Dinh dưỡng và Thực phẩm. 2022;18(5+6):55-61. doi:10.56283/1859-0381/390.
  - Mới: 6. Phạm Đức Minh. Nồng độ microalbumin niệu và một số yếu tố liên quan ở bệnh nhân đái tháo đường týp 2 điều trị ngoại trú. Tạp chí Dinh dưỡng và Thực phẩm. 2023;18(5+6):55-61. doi:10.56283/1859-0381/390.

## Tài liệu đưa vào gói ký (đã chuẩn bị theo các quyết định trên)

- Không phát sinh tài liệu ký mới.
