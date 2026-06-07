"""Thang điểm/công cụ lâm sàng đã XÁC MINH công thức + cut-off kèm NGUỒN gốc.

NGUYÊN TẮC: chỉ những công cụ được trích từ nguồn nguyên thủy/guideline mới được
đặt update_status="verified". Mỗi mục ghi rõ `source` (tác giả/năm) và
`guideline_reference`. Các công thức ở đây là chuẩn được công bố rộng rãi; khi
guideline thay đổi cách dùng, cập nhật và ghi vào change log.

Nếu bạn không chắc một cut-off, hãy để "needs_verification" (xem catalog.py) thay vì
điền số liệu phỏng đoán.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List

from app.database import session_scope
from app.models import ChangeLogEntry, ClinicalScore
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

_TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")


# Mỗi dict khớp score_id trong catalog.py (nếu có) để NÂNG CẤP skeleton -> verified.
VERIFIED_SCORES: List[Dict] = [
    {
        "score_id": "curb65",
        "score_name": "CURB-65",
        "clinical_area": "Hô hấp",
        "clinical_situation": "Viêm phổi cộng đồng (CAP) – phân tầng mức độ nặng & nơi điều trị",
        "purpose": "Ước tính nguy cơ tử vong 30 ngày và hỗ trợ quyết định ngoại trú vs nhập viện",
        "target_population": "Người lớn nghi/được chẩn đoán viêm phổi cộng đồng",
        "components": [
            "Confusion (lú lẫn mới khởi phát) = 1",
            "Urea > 7 mmol/L (BUN > 19 mg/dL) = 1",
            "Respiratory rate ≥ 30/phút = 1",
            "Blood pressure: SBP < 90 mmHg hoặc DBP ≤ 60 mmHg = 1",
            "Age ≥ 65 tuổi = 1",
        ],
        "calculation_method": "Tổng 5 tiêu chí, mỗi tiêu chí 1 điểm (0–5).",
        "interpretation": "Tử vong 30 ngày tăng theo điểm: 0–1 thấp, 2 trung bình, 3–5 cao.",
        "action_thresholds": "0–1: cân nhắc điều trị ngoại trú. 2: nhập viện ngắn ngày/theo dõi sát. "
                             "≥3: nhập viện, cân nhắc ICU nếu 4–5.",
        "clinical_action": "Kết hợp đánh giá lâm sàng, oxy hóa máu, bệnh nền; CRB-65 dùng khi không có ure.",
        "limitations": "Không thay thế đánh giá lâm sàng; ít nhạy ở người trẻ/suy giảm miễn dịch.",
        "source": "Lim WS, et al. Thorax 2003;58:377-382.",
        "guideline_reference": "BTS/NICE CAP; IDSA/ATS CAP guideline.",
    },
    {
        "score_id": "cha2ds2_vasc",
        "score_name": "CHA2DS2-VA (ESC 2024) / CHA2DS2-VASc",
        "clinical_area": "Tim mạch",
        "clinical_situation": "Rung nhĩ không do bệnh van – nguy cơ huyết khối/đột quỵ",
        "purpose": "Ước tính nguy cơ đột quỵ/thuyên tắc hệ thống/năm để quyết định kháng đông",
        "target_population": "Bệnh nhân rung nhĩ không do van",
        "components": [
            "Congestive HF/rối loạn chức năng thất trái = 1",
            "Hypertension = 1",
            "Age ≥ 75 = 2",
            "Diabetes = 1",
            "Stroke/TIA/thuyên tắc hệ thống = 2",
            "Vascular disease (NMCT cũ, PAD, mảng xơ ĐM chủ) = 1",
            "Age 65–74 = 1",
            "Sex category (nữ) = 1  [ĐÃ BỎ trong CHA2DS2-VA của ESC 2024]",
        ],
        "calculation_method": "CHA2DS2-VASc cũ: tổng 0–9. ESC 2024 chuyển sang CHA2DS2-VA "
                              "(BỎ yếu tố giới) → tổng tối đa 0–8.",
        "interpretation": "Nguy cơ đột quỵ/năm tăng theo điểm; áp dụng KHÔNG phụ thuộc giới (VA).",
        "action_thresholds": "ESC 2024 (CHA2DS2-VA, không phân biệt giới): ≥2 khuyến cáo kháng đông "
                             "đường uống (ưu tiên DOAC); =1 cân nhắc (IIa); =0 thường không cần. "
                             "Bản CHA2DS2-VASc cũ: nam ≥2 / nữ ≥3 khuyến cáo kháng đông.",
        "clinical_action": "Đánh giá kèm nguy cơ chảy máu (HAS-BLED) nhưng KHÔNG dùng HAS-BLED để từ chối kháng đông.",
        "limitations": "Không áp dụng cho rung nhĩ do van/cơ học. LƯU Ý CẬP NHẬT: ESC 2024 đã thay "
                       "CHA2DS2-VASc bằng CHA2DS2-VA (bỏ giới, tối đa 8 điểm).",
        "source": "Lip GYH, et al. Chest 2010;137:263-272 (VASc gốc); ESC 2024 AF Guideline (Eur Heart J 2024) – CHA2DS2-VA.",
        "guideline_reference": "ESC 2024 AF (AF-CARE, CHA2DS2-VA) – cập nhật; ESC 2020 AF (VASc).",
    },
    {
        "score_id": "has_bled",
        "score_name": "HAS-BLED",
        "clinical_area": "Tim mạch",
        "clinical_situation": "Bệnh nhân rung nhĩ cân nhắc/đang dùng kháng đông",
        "purpose": "Ước tính nguy cơ chảy máu nặng/năm; nhận diện yếu tố nguy cơ có thể điều chỉnh",
        "target_population": "Bệnh nhân rung nhĩ dùng kháng đông",
        "components": [
            "Hypertension (SBP > 160) = 1",
            "Abnormal renal function = 1; Abnormal liver function = 1",
            "Stroke = 1",
            "Bleeding (tiền sử/khuynh hướng) = 1",
            "Labile INR = 1",
            "Elderly (> 65) = 1",
            "Drugs (kháng tiểu cầu/NSAID) = 1; Alcohol = 1",
        ],
        "calculation_method": "Tổng 0–9 điểm.",
        "interpretation": "≥3 = nguy cơ chảy máu cao, cần theo dõi sát và xử lý yếu tố điều chỉnh được.",
        "action_thresholds": "≥3: KHÔNG dùng để chống chỉ định kháng đông; dùng để tối ưu hóa yếu tố nguy cơ "
                             "(HA, INR, thuốc, rượu) và lịch theo dõi.",
        "clinical_action": "Điều chỉnh yếu tố nguy cơ chảy máu thay đổi được; tái đánh giá định kỳ.",
        "limitations": "Không dùng để từ chối kháng đông ở bệnh nhân có chỉ định.",
        "source": "Pisters R, et al. Chest 2010;138:1093-1100.",
        "guideline_reference": "ESC 2020/2024 AF.",
    },
    {
        "score_id": "wells_dvt",
        "score_name": "Wells score – DVT",
        "clinical_area": "Tim mạch",
        "clinical_situation": "Nghi huyết khối tĩnh mạch sâu chi dưới",
        "purpose": "Xác suất lâm sàng DVT để định hướng D-dimer/siêu âm",
        "target_population": "Người lớn nghi DVT, ngoại trú",
        "components": [
            "Ung thư hoạt động = 1", "Liệt/bất động chi dưới = 1",
            "Nằm liệt >3 ngày hoặc phẫu thuật lớn <12 tuần = 1",
            "Đau dọc hệ tĩnh mạch sâu = 1", "Sưng toàn bộ chân = 1",
            "Bắp chân to >3 cm so với bên đối diện = 1", "Phù ấn lõm bên triệu chứng = 1",
            "Tĩnh mạch nông bàng hệ (không giãn) = 1", "Tiền sử DVT = 1",
            "Chẩn đoán khác ≥ khả năng DVT = -2",
        ],
        "calculation_method": "Tổng điểm theo mô hình 2 mức.",
        "interpretation": "≤1: ít khả năng (DVT unlikely). ≥2: nhiều khả năng (DVT likely).",
        "action_thresholds": "≤1: D-dimer; âm tính → loại trừ. ≥2 (hoặc D-dimer dương): siêu âm ép tĩnh mạch.",
        "clinical_action": "Phối hợp D-dimer độ nhạy cao ở nhóm nguy cơ thấp.",
        "limitations": "Độ chính xác giảm ở bệnh nhân nội trú/ung thư.",
        "source": "Wells PS, et al. N Engl J Med 2003;349:1227-1235.",
        "guideline_reference": "NICE NG158; ACCP/ASH VTE.",
    },
    {
        "score_id": "wells_pe",
        "score_name": "Wells score – PE",
        "clinical_area": "Hô hấp",
        "clinical_situation": "Nghi thuyên tắc phổi",
        "purpose": "Xác suất lâm sàng PE để định hướng D-dimer/CTPA",
        "target_population": "Người lớn nghi PE",
        "components": [
            "Triệu chứng/dấu hiệu DVT = 3",
            "PE là chẩn đoán khả dĩ nhất = 3",
            "Nhịp tim > 100 = 1.5", "Bất động/phẫu thuật <4 tuần = 1.5",
            "Tiền sử DVT/PE = 1.5", "Ho ra máu = 1", "Ung thư hoạt động = 1",
        ],
        "calculation_method": "Tổng điểm; có mô hình 3 mức và 2 mức.",
        "interpretation": "2 mức: ≤4 = PE unlikely, >4 = PE likely. 3 mức: <2 thấp, 2–6 trung bình, >6 cao.",
        "action_thresholds": "≤4: D-dimer (cân nhắc PERC/ age-adjusted); âm tính → loại trừ. >4: CTPA.",
        "clinical_action": "Có thể dùng kèm PERC ở nhóm xác suất rất thấp.",
        "limitations": "Phụ thuộc đánh giá chủ quan 'PE khả dĩ nhất'.",
        "source": "Wells PS, et al. Thromb Haemost 2000;83:416-420.",
        "guideline_reference": "ESC 2019 Pulmonary Embolism.",
    },
    {
        "score_id": "perc",
        "score_name": "PERC Rule",
        "clinical_area": "Hô hấp",
        "clinical_situation": "Nghi PE ở nhóm xác suất lâm sàng THẤP",
        "purpose": "Loại trừ PE mà không cần D-dimer khi đủ 8 tiêu chí âm tính",
        "target_population": "Bệnh nhân xác suất PE thấp (<15%) tại cấp cứu/ngoại trú",
        "components": [
            "Tuổi < 50", "Nhịp tim < 100", "SpO2 ≥ 95%", "Không ho ra máu",
            "Không dùng estrogen", "Không tiền sử DVT/PE",
            "Không sưng một chân", "Không phẫu thuật/chấn thương cần nhập viện <4 tuần",
        ],
        "calculation_method": "PERC âm tính = TẤT CẢ 8 tiêu chí đều âm.",
        "interpretation": "Nếu xác suất thấp + PERC âm: nguy cơ PE <2%, không cần xét nghiệm thêm.",
        "action_thresholds": "PERC âm + pretest thấp → dừng truy tìm PE. Bất kỳ tiêu chí dương → D-dimer/CTPA.",
        "clinical_action": "Chỉ áp dụng khi đã đánh giá xác suất lâm sàng THẤP từ trước.",
        "limitations": "Không dùng khi xác suất trung bình/cao.",
        "source": "Kline JA, et al. J Thromb Haemost 2004;2:1247-1255.",
        "guideline_reference": "ACEP clinical policy PE.",
    },
    {
        "score_id": "qsofa",
        "score_name": "qSOFA (Quick SOFA)",
        "clinical_area": "Cấp cứu ban đầu",
        "clinical_situation": "Nghi nhiễm khuẩn ngoài ICU – sàng lọc nguy cơ diễn tiến nặng",
        "purpose": "Nhận diện nhanh bệnh nhân nhiễm khuẩn có nguy cơ tử vong/nằm ICU kéo dài",
        "target_population": "Người lớn nghi nhiễm khuẩn, ngoài hồi sức",
        "components": [
            "Nhịp thở ≥ 22/phút = 1",
            "Thay đổi tri giác (GCS < 15) = 1",
            "Huyết áp tâm thu ≤ 100 mmHg = 1",
        ],
        "calculation_method": "Tổng 0–3 điểm.",
        "interpretation": "≥2: nguy cơ kết cục xấu cao hơn; gợi ý đánh giá nhiễm khuẩn huyết.",
        "action_thresholds": "≥2: đánh giá rối loạn chức năng cơ quan (SOFA), lactate, cấy máu, hồi sức sớm/chuyển tuyến.",
        "clinical_action": "qSOFA là công cụ CẢNH BÁO, không phải tiêu chuẩn chẩn đoán sepsis đơn độc.",
        "limitations": "Độ nhạy THẤP (~46%). LƯU Ý: Surviving Sepsis 2021 khuyến cáo MẠNH CHỐNG dùng qSOFA "
                       "làm CÔNG CỤ SÀNG LỌC ĐƠN LẺ; nên ưu tiên SIRS/NEWS/MEWS + lactate để sàng lọc. qSOFA chỉ "
                       "hữu ích để TIÊN LƯỢNG nguy cơ xấu, không phải để loại trừ sepsis.",
        "source": "Singer M, et al. (Sepsis-3) JAMA 2016;315:801-810; Evans L, et al. Surviving Sepsis 2021, Crit Care Med 2021.",
        "guideline_reference": "Surviving Sepsis Campaign 2021 (khuyến cáo mạnh chống dùng qSOFA đơn lẻ).",
    },
    {
        "score_id": "fib4",
        "score_name": "FIB-4 Index",
        "clinical_area": "Tiêu hóa - Gan mật",
        "clinical_situation": "Bệnh gan mạn (viêm gan virus, MASLD/NAFLD) – ước tính xơ hóa",
        "purpose": "Sàng lọc xơ hóa gan tiến triển không xâm lấn",
        "target_population": "Người lớn bệnh gan mạn",
        "components": ["Tuổi (năm)", "AST (U/L)", "ALT (U/L)", "Tiểu cầu (10^9/L)"],
        "calculation_method": "FIB-4 = (Tuổi × AST) / (Tiểu cầu × √ALT).",
        "interpretation": "Phản ánh khả năng xơ hóa tiến triển (F3–F4). Ngưỡng KHÁC NHAU theo bối cảnh.",
        "action_thresholds": "MASLD/NAFLD (AASLD 2023, chăm sóc ban đầu): <1.3 nguy cơ THẤP (không cần thêm); "
                             "≥1.3 cần đánh giá bước 2 (đàn hồi gan/ELF); ở người >65 tuổi dùng ngưỡng >2.0; "
                             ">2.67 nhiều khả năng xơ hóa tiến triển. "
                             "Bản gốc viêm gan C (Sterling 2006): <1.45 và >3.25.",
        "clinical_action": "Ở MASLD dùng FIB-4 là bước sàng lọc đầu tiên ngoại trú; áp ngưỡng <1.3 (AASLD 2023).",
        "limitations": "Kém chính xác ở <35 và >65 tuổi (cần ngưỡng tuổi cao hơn); ảnh hưởng bởi nguyên nhân "
                       "thay đổi men gan/tiểu cầu.",
        "source": "Sterling RK, et al. Hepatology 2006;43:1317-1325; AASLD MASLD Practice Guidance 2023 (Rinella, Hepatology 2023).",
        "guideline_reference": "AASLD 2023 MASLD Practice Guidance (ngưỡng <1.3); EASL.",
    },
    {
        "score_id": "apri",
        "score_name": "APRI (AST to Platelet Ratio Index)",
        "clinical_area": "Tiêu hóa - Gan mật",
        "clinical_situation": "Bệnh gan mạn – ước tính xơ hóa/xơ gan",
        "purpose": "Sàng lọc xơ hóa/xơ gan không xâm lấn (nhất là viêm gan C, nguồn lực hạn chế)",
        "target_population": "Người lớn bệnh gan mạn",
        "components": ["AST (U/L)", "Giới hạn trên AST (ULN)", "Tiểu cầu (10^9/L)"],
        "calculation_method": "APRI = [(AST / ULN_AST) × 100] / Tiểu cầu.",
        "interpretation": "Điểm cao gợi ý xơ hóa đáng kể/xơ gan.",
        "action_thresholds": "WHO: >0.5 gợi ý xơ hóa đáng kể; >1.0 gợi ý xơ gan (cân nhắc theo bối cảnh).",
        "clinical_action": "Dùng phối hợp FIB-4/đàn hồi gan khi có.",
        "limitations": "Độ chính xác trung bình; phụ thuộc ULN của phòng xét nghiệm.",
        "source": "Wai CT, et al. Hepatology 2003;38:518-526.",
        "guideline_reference": "WHO hepatitis B/C guidelines.",
    },
    {
        "score_id": "child_pugh",
        "score_name": "Child-Pugh",
        "clinical_area": "Tiêu hóa - Gan mật",
        "clinical_situation": "Xơ gan – phân độ chức năng gan & tiên lượng",
        "purpose": "Phân tầng mức độ suy gan, tiên lượng và hiệu chỉnh thuốc",
        "target_population": "Bệnh nhân xơ gan",
        "components": [
            "Bilirubin TP (<34 / 34–50 / >50 µmol/L = 1/2/3)",
            "Albumin (>35 / 28–35 / <28 g/L = 1/2/3)",
            "INR (<1.7 / 1.7–2.3 / >2.3 = 1/2/3)",
            "Cổ trướng (không / nhẹ-đáp ứng lợi tiểu / căng-kháng trị = 1/2/3)",
            "Bệnh não gan (không / độ 1–2 / độ 3–4 = 1/2/3)",
        ],
        "calculation_method": "Tổng 5 mục, mỗi mục 1–3 điểm (5–15).",
        "interpretation": "A: 5–6 (còn bù). B: 7–9 (suy chức năng có ý nghĩa). C: 10–15 (mất bù).",
        "action_thresholds": "Class B/C: thận trọng thuốc chuyển hóa gan; cân nhắc chuyển chuyên khoa/ghép gan.",
        "clinical_action": "Dùng cùng MELD-Na để đánh giá tiên lượng/ưu tiên ghép.",
        "limitations": "Hai biến chủ quan (cổ trướng, bệnh não gan).",
        "source": "Pugh RNH, et al. Br J Surg 1973;60:646-649.",
        "guideline_reference": "AASLD/EASL cirrhosis.",
    },
    {
        "score_id": "phq9",
        "score_name": "PHQ-9",
        "clinical_area": "Khác",
        "clinical_situation": "Sàng lọc & theo dõi mức độ trầm cảm",
        "purpose": "Đánh giá mức độ nặng trầm cảm và đáp ứng điều trị",
        "target_population": "Người lớn tại chăm sóc ban đầu",
        "components": ["9 mục theo tiêu chí trầm cảm DSM, mỗi mục 0–3 (0=không, 3=gần như mỗi ngày)"],
        "calculation_method": "Tổng 0–27.",
        "interpretation": "0–4 tối thiểu, 5–9 nhẹ, 10–14 trung bình, 15–19 trung bình-nặng, 20–27 nặng.",
        "action_thresholds": "≥10: cân nhắc trầm cảm nặng cần điều trị. Mục 9 (ý tưởng tự sát) dương → đánh giá nguy cơ ngay.",
        "clinical_action": "Dùng theo dõi đáp ứng (giảm ≥5 điểm có ý nghĩa lâm sàng).",
        "limitations": "Là công cụ sàng lọc, không thay chẩn đoán lâm sàng.",
        "source": "Kroenke K, Spitzer RL, Williams JBW. J Gen Intern Med 2001;16:606-613.",
        "guideline_reference": "USPSTF depression screening.",
    },
    {
        "score_id": "gad7",
        "score_name": "GAD-7",
        "clinical_area": "Khác",
        "clinical_situation": "Sàng lọc & theo dõi rối loạn lo âu",
        "purpose": "Đánh giá mức độ lo âu (đặc biệt rối loạn lo âu lan tỏa)",
        "target_population": "Người lớn tại chăm sóc ban đầu",
        "components": ["7 mục, mỗi mục 0–3"],
        "calculation_method": "Tổng 0–21.",
        "interpretation": "0–4 tối thiểu, 5–9 nhẹ, 10–14 trung bình, 15–21 nặng.",
        "action_thresholds": "≥10: ngưỡng gợi ý cần đánh giá/điều trị thêm.",
        "clinical_action": "Theo dõi đáp ứng điều trị theo thời gian.",
        "limitations": "Công cụ sàng lọc, không thay chẩn đoán.",
        "source": "Spitzer RL, et al. Arch Intern Med 2006;166:1092-1097.",
        "guideline_reference": "USPSTF 2023: khuyến cáo MỚI (mức B) sàng lọc rối loạn lo âu ở người lớn "
                               "≤64 tuổi (gồm thai kỳ/hậu sản); NICE anxiety. Ngưỡng ≥10 xác nhận lại bởi meta-analysis 2023.",
    },
    {
        "score_id": "centor_mcisaac",
        "score_name": "Centor / McIsaac (modified)",
        "clinical_area": "Nhiễm khuẩn",
        "clinical_situation": "Viêm họng cấp – xác suất nhiễm liên cầu nhóm A (GAS)",
        "purpose": "Hỗ trợ quyết định xét nghiệm nhanh/kháng sinh, hạn chế lạm dụng kháng sinh",
        "target_population": "Người ≥3 tuổi viêm họng cấp",
        "components": [
            "Sốt > 38°C = 1", "Không ho = 1", "Hạch cổ trước sưng đau = 1",
            "Sưng/xuất tiết amidan = 1",
            "Tuổi: 3–14 = +1; 15–44 = 0; ≥45 = -1 (hiệu chỉnh McIsaac)",
        ],
        "calculation_method": "Tổng điểm (McIsaac: -1 đến 5).",
        "interpretation": "Điểm cao → khả năng GAS cao hơn.",
        "action_thresholds": "≤0–1: không xét nghiệm/không kháng sinh. 2–3: xét nghiệm nhanh GAS (RADT). "
                             "≥4: xét nghiệm; điều trị nếu dương (KHÔNG khuyến cáo kháng sinh theo kinh nghiệm thường quy).",
        "clinical_action": "Ưu tiên xét nghiệm xác định trước khi kê kháng sinh (stewardship).",
        "limitations": "Không phân biệt người lành mang GAS; dịch tễ địa phương ảnh hưởng.",
        "source": "McIsaac WJ, et al. CMAJ 1998;158:75-83; Centor RM 1981.",
        "guideline_reference": "IDSA pharyngitis; NICE sore throat (FeverPAIN là lựa chọn thay thế).",
    },
    {
        "score_id": "anion_gap",
        "score_name": "Anion Gap (khoảng trống anion)",
        "clinical_area": "Thận",
        "clinical_situation": "Rối loạn toan-kiềm chuyển hóa",
        "purpose": "Phân loại toan chuyển hóa có/không tăng khoảng trống anion",
        "target_population": "Bệnh nhân toan chuyển hóa",
        "components": ["Na+", "Cl-", "HCO3-"],
        "calculation_method": "AG = Na+ − (Cl− + HCO3−). Hiệu chỉnh albumin: +2.5 cho mỗi 10 g/L albumin giảm dưới 40.",
        "interpretation": "Bình thường ~8–12 mmol/L (tùy phòng xét nghiệm).",
        "action_thresholds": "AG cao: nghĩ MUDPILES (toan ceton, toan lactic, ngộ độc, suy thận...). "
                             "AG bình thường: mất HCO3 (tiêu chảy, RTA).",
        "clinical_action": "Luôn hiệu chỉnh theo albumin ở bệnh nhân giảm albumin.",
        "limitations": "Khoảng tham chiếu phụ thuộc phương pháp đo điện giải.",
        "source": "Kraut JA, Madias NE. Clin J Am Soc Nephrol 2007;2:162-174.",
        "guideline_reference": "—",
    },
    # ---- Bổ sung nhóm ưu tiên ngoại trú: tim mạch / hô hấp / thận / gan / lão khoa ----
    {
        "score_id": "news2",
        "score_name": "NEWS2 (National Early Warning Score 2)",
        "clinical_area": "Cấp cứu ban đầu",
        "clinical_situation": "Theo dõi sinh hiệu – cảnh báo sớm xấu đi (người lớn cấp tính)",
        "purpose": "Phát hiện sớm bệnh nhân diễn tiến nặng/nhiễm khuẩn huyết",
        "target_population": "Người lớn (không dùng cho thai phụ; thận trọng tăng CO2 mạn ở COPD)",
        "components": [
            "Nhịp thở", "SpO2 (thang 1; thang 2 cho COPD giữ CO2)", "Khí thở/oxy bổ sung",
            "Huyết áp tâm thu", "Nhịp tim", "Mức ý thức (ACVPU)", "Nhiệt độ",
        ],
        "calculation_method": "Cộng điểm 0–3 cho mỗi thông số; SpO2 thang 2 dùng cho bệnh nhân "
                              "suy hô hấp mạn type 2 có đích SpO2 88–92%.",
        "interpretation": "Tổng phản ánh mức độ nặng cấp tính & tần suất theo dõi.",
        "action_thresholds": "0: theo dõi tối thiểu 12h. 1–4: thấp (đánh giá điều dưỡng). "
                             "3 ở 1 thông số đơn: xem xét leo thang. 5–6: trung bình (đánh giá khẩn cấp). "
                             "≥7: cao (đánh giá cấp cứu/đe dọa tính mạng).",
        "clinical_action": "Dùng để chuẩn hóa leo thang chăm sóc/chuyển tuyến.",
        "limitations": "Không thay đánh giá lâm sàng; thận trọng nhóm giữ CO2 mạn.",
        "source": "Royal College of Physicians. NEWS2, 2017.",
        "guideline_reference": "RCP NEWS2; NICE NG51 sepsis.",
    },
    {
        "score_id": "nyha",
        "score_name": "NYHA Functional Classification",
        "clinical_area": "Tim mạch",
        "clinical_situation": "Suy tim – phân độ chức năng theo triệu chứng",
        "purpose": "Phân tầng triệu chứng để định hướng điều trị & tiên lượng",
        "target_population": "Bệnh nhân suy tim",
        "components": ["Triệu chứng khó thở/mệt theo mức gắng sức"],
        "calculation_method": "Phân loại lâm sàng (không tính điểm số):",
        "interpretation": "I: không hạn chế hoạt động. II: hạn chế nhẹ, triệu chứng khi gắng sức thường. "
                          "III: hạn chế rõ, triệu chứng khi gắng sức nhẹ. IV: triệu chứng khi nghỉ.",
        "action_thresholds": "Class II–IV: tối ưu điều trị nền tảng suy tim (GDMT). "
                             "Class III–IV dai dẳng: cân nhắc thiết bị/chuyển chuyên khoa.",
        "clinical_action": "Đánh giá lại sau mỗi lần chỉnh điều trị.",
        "limitations": "Chủ quan, biến thiên giữa người đánh giá.",
        "source": "The Criteria Committee of the NYHA, 1994 (9th ed).",
        "guideline_reference": "ESC 2021 HF; ACC/AHA/HFSA 2022 HF.",
    },
    {
        "score_id": "gold_abe",
        "score_name": "GOLD ABE Assessment (2023+)",
        "clinical_area": "Hô hấp",
        "clinical_situation": "COPD ổn định – phân nhóm định hướng điều trị khởi đầu",
        "purpose": "Phân nhóm theo triệu chứng & tiền sử đợt cấp để chọn thuốc khởi đầu",
        "target_population": "Bệnh nhân COPD đã xác định bằng hô hấp ký",
        "components": [
            "Triệu chứng: mMRC và/hoặc CAT",
            "Tiền sử đợt cấp 12 tháng qua (số đợt; có nhập viện hay không)",
        ],
        "calculation_method": "Phân nhóm A/B/E (GOLD 2023 gộp C+D thành E):",
        "interpretation": "A: ít triệu chứng (mMRC 0–1 / CAT<10) & ≤1 đợt cấp nhẹ. "
                          "B: nhiều triệu chứng (mMRC≥2 / CAT≥10) & ≤1 đợt cấp nhẹ. "
                          "E: ≥2 đợt cấp vừa hoặc ≥1 đợt nhập viện (bất kể triệu chứng).",
        "action_thresholds": "A: 1 thuốc giãn phế quản. B: LABA+LAMA. "
                             "E: LABA+LAMA; có thể bắt đầu BỘ BA LABA+LAMA+ICS ngay nếu eosinophil ≥300 "
                             "(GOLD 2025). Theo dõi: leo thang ICS nếu eos ≥100; cân nhắc dupilumab nếu "
                             "eos ≥300 + viêm phế quản mạn còn đợt cấp.",
        "clinical_action": "Phân biệt phân nhóm ban đầu với theo dõi điều trị (đường follow-up khác).",
        "limitations": "Phân nhóm phục vụ điều trị KHỞI ĐẦU, không thay theo dõi cá thể hóa.",
        "source": "GOLD Report 2025.",
        "guideline_reference": "GOLD 2025 (eosinophil ≥300 cho ICS; ABE).",
    },
    {
        "score_id": "ckd_epi",
        "score_name": "CKD-EPI 2021 (eGFR) & phân giai đoạn KDIGO",
        "clinical_area": "Thận",
        "clinical_situation": "Đánh giá & phân giai đoạn bệnh thận mạn",
        "purpose": "Ước tính eGFR (creatinine, không dùng biến chủng tộc) và phân giai đoạn G/A",
        "target_population": "Người lớn",
        "components": ["Creatinine huyết thanh", "Tuổi", "Giới"],
        "calculation_method": "Dùng phương trình CKD-EPI creatinine 2021 (race-free). "
                              "KHÔNG tự nhập hệ số tay – dùng công cụ/thư viện đã thẩm định.",
        "interpretation": "Giai đoạn G: G1 ≥90, G2 60–89, G3a 45–59, G3b 30–44, G4 15–29, G5 <15 "
                          "(mL/phút/1.73m²). Albumin niệu A1 <30, A2 30–300, A3 >300 mg/g.",
        "action_thresholds": "G3b–G5 hoặc A3: chuyển/nhắc chuyên khoa thận tùy bối cảnh; "
                             "rà soát hiệu chỉnh liều thuốc theo eGFR.",
        "clinical_action": "Kết hợp eGFR + albumin niệu để định vị ô nguy cơ KDIGO (xem kdigo_grid).",
        "limitations": "eGFR ước tính kém chính xác ở khối cơ bất thường/cấp tính.",
        "source": "Inker LA, et al. N Engl J Med 2021;385:1737-1749.",
        "guideline_reference": "KDIGO 2024 CKD.",
    },
    {
        "score_id": "kdigo_grid",
        "score_name": "KDIGO CKD Risk Grid (heat map)",
        "clinical_area": "Thận",
        "clinical_situation": "Phân tầng nguy cơ tiến triển CKD",
        "purpose": "Định vị nguy cơ theo eGFR (G) × albumin niệu (A)",
        "target_population": "Bệnh nhân CKD",
        "components": ["Giai đoạn eGFR (G1–G5)", "Mức albumin niệu (A1–A3)"],
        "calculation_method": "Tra bảng ô màu: phối hợp G và A.",
        "interpretation": "Xanh: nguy cơ thấp. Vàng: trung bình. Cam: cao. Đỏ: rất cao.",
        "action_thresholds": "Cam/Đỏ: tăng tần suất theo dõi, tối ưu kiểm soát nguyên nhân, "
                             "cân nhắc SGLT2i/RAASi nếu phù hợp, xem xét chuyển chuyên khoa.",
        "clinical_action": "Dùng để thống nhất lịch theo dõi và mục tiêu điều trị.",
        "limitations": "Là khung nguy cơ chung, cần cá thể hóa.",
        "source": "KDIGO 2024 CKD Guideline (heat map).",
        "guideline_reference": "KDIGO 2024 CKD.",
    },
    {
        "score_id": "blatchford",
        "score_name": "Glasgow-Blatchford Score (GBS)",
        "clinical_area": "Tiêu hóa - Gan mật",
        "clinical_situation": "Xuất huyết tiêu hóa trên – phân tầng cần can thiệp",
        "purpose": "Xác định bệnh nhân nguy cơ rất thấp có thể xử trí ngoại trú",
        "target_population": "Người lớn nghi xuất huyết tiêu hóa trên",
        "components": ["Ure máu", "Hemoglobin", "Huyết áp tâm thu", "Mạch ≥100",
                       "Tiêu phân đen", "Ngất", "Bệnh gan", "Suy tim"],
        "calculation_method": "Tổng điểm theo thang GBS (0–23).",
        "interpretation": "GBS = 0 (hoặc ≤1 theo một số ngưỡng): nguy cơ rất thấp.",
        "action_thresholds": "GBS = 0: cân nhắc xuất viện/nội soi ngoại trú. "
                             "≥1: nhập viện đánh giá nội soi.",
        "clinical_action": "Dùng tại thời điểm tiếp nhận để quyết định nơi xử trí.",
        "limitations": "Đánh giá nhu cầu can thiệp, không tiên lượng tử vong như Rockall.",
        "source": "Blatchford O, et al. Lancet 2000;356:1318-1321.",
        "guideline_reference": "NICE CG141; ESGE UGIB.",
    },
    {
        "score_id": "meld_na",
        "score_name": "MELD-Na",
        "clinical_area": "Tiêu hóa - Gan mật",
        "clinical_situation": "Bệnh gan tiến triển – tiên lượng/ưu tiên ghép gan",
        "purpose": "Ước tính tử vong ngắn hạn; ưu tiên phân bổ ghép gan",
        "target_population": "Bệnh nhân xơ gan/bệnh gan mạn ≥12 tuổi",
        "components": ["Bilirubin", "INR", "Creatinine", "Natri máu"],
        "calculation_method": "Dùng công thức MELD-Na chuẩn (Kim 2008). LƯU Ý: từ 2016 UNOS dùng "
                              "MELD-Na; từ 2023 chuyển sang MELD 3.0 (thêm albumin & giới). "
                              "Dùng công cụ chính thức, KHÔNG tự nhập hệ số tay.",
        "interpretation": "Điểm cao → tử vong 90 ngày cao hơn.",
        "action_thresholds": "Theo ngưỡng phân bổ ghép của trung tâm/quốc gia hiện hành.",
        "clinical_action": "CẬP NHẬT: từ 2023, UNOS/OPTN (Hoa Kỳ) dùng MELD 3.0 (thêm albumin & giới) làm "
                           "CHUẨN HIỆN HÀNH thay cho MELD-Na trong phân bổ ghép. Đối chiếu phiên bản cơ sở đang dùng.",
        "limitations": "Bị ảnh hưởng bởi nguyên nhân tăng creatinine/INR ngoài gan.",
        "source": "Kim WR, et al. N Engl J Med 2008;359:1018-1026 (MELD-Na); Kim WR, et al. Gastroenterology 2021 (MELD 3.0).",
        "guideline_reference": "OPTN/UNOS policy 2023 (MELD 3.0 là chuẩn hiện hành); AASLD.",
    },
    {
        "score_id": "maddrey_df",
        "score_name": "Maddrey Discriminant Function (mDF)",
        "clinical_area": "Tiêu hóa - Gan mật",
        "clinical_situation": "Viêm gan do rượu – đánh giá mức độ nặng",
        "purpose": "Xác định viêm gan rượu nặng cần cân nhắc corticosteroid",
        "target_population": "Bệnh nhân viêm gan do rượu",
        "components": ["PT bệnh nhân (giây)", "PT chứng (giây)", "Bilirubin (mg/dL)"],
        "calculation_method": "mDF = 4.6 × (PT_bệnh nhân − PT_chứng) + Bilirubin(mg/dL).",
        "interpretation": "≥32: viêm gan rượu NẶNG (tiên lượng tử vong ngắn hạn cao).",
        "action_thresholds": "≥32: cân nhắc corticosteroid nếu không chống chỉ định; "
                             "đánh giá đáp ứng bằng Lille sau 7 ngày.",
        "clinical_action": "Loại trừ nhiễm khuẩn/XHTH trước khi dùng steroid.",
        "limitations": "Phụ thuộc chuẩn hóa PT của phòng xét nghiệm.",
        "source": "Maddrey WC, et al. Gastroenterology 1978;75:193-199.",
        "guideline_reference": "AASLD/EASL alcohol-associated liver disease.",
    },
    {
        "score_id": "frail_scale",
        "score_name": "FRAIL Scale",
        "clinical_area": "Lão khoa - Đa bệnh lý",
        "clinical_situation": "Sàng lọc suy yếu (frailty) nhanh ngoại trú",
        "purpose": "Phát hiện tiền suy yếu/suy yếu để can thiệp sớm",
        "target_population": "Người cao tuổi",
        "components": [
            "Fatigue (mệt mỏi)", "Resistance (khó leo 1 tầng cầu thang)",
            "Ambulation (khó đi bộ ~100m)", "Illnesses (>5 bệnh)",
            "Loss of weight (>5% trong năm)",
        ],
        "calculation_method": "Mỗi mục 1 điểm (0–5).",
        "interpretation": "0: khỏe (robust). 1–2: tiền suy yếu. 3–5: suy yếu (frail).",
        "action_thresholds": "≥3: đánh giá lão khoa toàn diện (CGA), rà soát đa thuốc, té ngã, dinh dưỡng.",
        "clinical_action": "Cá thể hóa mục tiêu điều trị; cân nhắc deprescribing.",
        "limitations": "Là công cụ sàng lọc, không thay CGA.",
        "source": "Morley JE, et al. J Nutr Health Aging 2012;16:601-608.",
        "guideline_reference": "—",
    },
    {
        "score_id": "audit_c",
        "score_name": "AUDIT-C",
        "clinical_area": "Khác",
        "clinical_situation": "Sàng lọc sử dụng rượu có hại",
        "purpose": "Phát hiện uống rượu nguy cơ/lệ thuộc",
        "target_population": "Người lớn",
        "components": ["Tần suất uống", "Số đơn vị mỗi lần", "Tần suất uống ≥6 đơn vị"],
        "calculation_method": "3 câu, mỗi câu 0–4 (tổng 0–12).",
        "interpretation": "Điểm cao → khả năng uống rượu nguy cơ cao hơn.",
        "action_thresholds": "≥4 (nam) / ≥3 (nữ): dương tính, tư vấn ngắn/đánh giá thêm (AUDIT đầy đủ).",
        "clinical_action": "Can thiệp ngắn (brief intervention) khi dương tính.",
        "limitations": "Tự khai báo có thể thấp hơn thực tế.",
        "source": "Bush K, et al. Arch Intern Med 1998;158:1789-1795.",
        "guideline_reference": "USPSTF unhealthy alcohol use.",
    },
    {
        "score_id": "findrisc",
        "score_name": "FINDRISC",
        "clinical_area": "Nội tiết - Chuyển hóa",
        "clinical_situation": "Sàng lọc nguy cơ đái tháo đường típ 2 (không xâm lấn)",
        "purpose": "Ước tính nguy cơ mắc ĐTĐ típ 2 trong 10 năm",
        "target_population": "Người lớn chưa chẩn đoán ĐTĐ",
        "components": ["Tuổi", "BMI", "Vòng eo", "Hoạt động thể lực", "Rau quả hằng ngày",
                       "Tiền sử thuốc hạ áp", "Tiền sử đường huyết cao", "Tiền sử gia đình ĐTĐ"],
        "calculation_method": "Tổng điểm 0–26 theo thang FINDRISC.",
        "interpretation": "Điểm càng cao nguy cơ 10 năm càng cao.",
        "action_thresholds": "≥15: nguy cơ cao → xét nghiệm đường huyết/HbA1c, tư vấn lối sống.",
        "clinical_action": "Dùng sàng lọc cộng đồng/ngoại trú trước xét nghiệm.",
        "limitations": "Hiệu chỉnh theo quần thể; cần xác nhận bằng xét nghiệm.",
        "source": "Lindström J, Tuomilehto J. Diabetes Care 2003;26:725-731.",
        "guideline_reference": "ADA Standards of Care; IDF.",
    },
    {
        "score_id": "homa_ir",
        "score_name": "HOMA-IR",
        "clinical_area": "Nội tiết - Chuyển hóa",
        "clinical_situation": "Đánh giá đề kháng insulin",
        "purpose": "Ước tính mức đề kháng insulin từ đường & insulin lúc đói",
        "target_population": "Người lớn không dùng insulin ngoại sinh",
        "components": ["Glucose lúc đói", "Insulin lúc đói"],
        "calculation_method": "HOMA-IR = (Glucose_mmol/L × Insulin_µU/mL) / 22.5 "
                              "(hoặc Glucose_mg/dL × Insulin / 405).",
        "interpretation": "Giá trị cao → đề kháng insulin nhiều hơn (ngưỡng phụ thuộc quần thể).",
        "action_thresholds": "Diễn giải theo khoảng tham chiếu địa phương; không có cut-off chẩn đoán phổ quát.",
        "clinical_action": "Hỗ trợ đánh giá hội chứng chuyển hóa/MASLD cùng bối cảnh lâm sàng.",
        "limitations": "Không dùng khi đang điều trị insulin; biến thiên giữa các xét nghiệm insulin.",
        "source": "Matthews DR, et al. Diabetologia 1985;28:412-419.",
        "guideline_reference": "—",
    },
    {
        "score_id": "timi",
        "score_name": "TIMI Risk Score (UA/NSTEMI)",
        "clinical_area": "Tim mạch",
        "clinical_situation": "Hội chứng vành cấp không ST chênh lên",
        "purpose": "Phân tầng nguy cơ biến cố 14 ngày để định hướng xử trí",
        "target_population": "Bệnh nhân UA/NSTEMI",
        "components": [
            "Tuổi ≥65", "≥3 yếu tố nguy cơ CAD", "Hẹp mạch vành đã biết ≥50%",
            "Dùng aspirin 7 ngày qua", "≥2 cơn đau ngực/24h",
            "ST thay đổi ≥0.5mm", "Tăng men tim",
        ],
        "calculation_method": "Tổng 7 tiêu chí, mỗi tiêu chí 1 điểm (0–7).",
        "interpretation": "Điểm cao → nguy cơ tử vong/NMCT/tái thông khẩn cao hơn.",
        "action_thresholds": "Điểm cao (≥3) gợi ý chiến lược can thiệp xâm lấn sớm; "
                             "luôn kết hợp lâm sàng + ECG + troponin.",
        "clinical_action": "Phối hợp đánh giá nguy cơ (vd GRACE) và bối cảnh.",
        "limitations": "Đơn giản hóa; GRACE phân biệt tốt hơn ở một số nhóm.",
        "source": "Antman EM, et al. JAMA 2000;284:835-842.",
        "guideline_reference": "ESC 2023 ACS; ACC/AHA.",
    },
    {
        "score_id": "ascvd_pce",
        "score_name": "ASCVD Risk (Pooled Cohort Equations)",
        "clinical_area": "Tim mạch",
        "clinical_situation": "Dự phòng tim mạch nguyên phát (40–79 tuổi)",
        "purpose": "Ước tính nguy cơ ASCVD 10 năm để quyết định statin",
        "target_population": "Người 40–79 tuổi chưa có ASCVD",
        "components": ["Tuổi", "Giới", "Chủng tộc", "HA tâm thu (± điều trị)",
                       "Cholesterol TP & HDL", "Hút thuốc", "ĐTĐ"],
        "calculation_method": "Dùng Pooled Cohort Equations (phương trình phức tạp) – "
                              "BẮT BUỘC dùng công cụ chính thức ACC/AHA, KHÔNG tự nhập hệ số tay.",
        "interpretation": "Phân tầng nguy cơ 10 năm: <5% thấp, 5–<7.5% giới hạn, "
                          "7.5–<20% trung bình, ≥20% cao.",
        "action_thresholds": "≥7.5%: thảo luận statin (cân nhắc yếu tố tăng nặng risk-enhancers, "
                             "CAC nếu chưa chắc). ≥20%: statin cường độ cao.",
        "clinical_action": "Ra quyết định chung với người bệnh; cá thể hóa.",
        "limitations": "PCE có thể ước tính LỆCH (thường cao) ở quần thể hiện đại; cần công cụ chính thức. "
                       "CẬP NHẬT: AHA công bố phương trình PREVENT (2023) – bỏ chủng tộc, cho nguy cơ 10 & 30 năm, "
                       "thường ước tính THẤP HƠN PCE; PREVENT chưa được mandate thay thế PCE trong guideline statin "
                       "hiện hành nhưng đang được áp dụng tăng dần. Đối chiếu công cụ cơ sở đang dùng (PCE vs PREVENT).",
        "source": "Goff DC, et al. Circulation 2014;129(25 Suppl 2):S49-73; Khan SS, et al. AHA PREVENT, Circulation 2023.",
        "guideline_reference": "2018 ACC/AHA Cholesterol; 2019 Primary Prevention; AHA PREVENT 2023 (mới).",
    },
    {
        "score_id": "score2",
        "score_name": "SCORE2 / SCORE2-OP",
        "clinical_area": "Tim mạch",
        "clinical_situation": "Dự phòng tim mạch nguyên phát (mô hình châu Âu)",
        "purpose": "Ước tính nguy cơ biến cố tim mạch tử vong + không tử vong 10 năm",
        "target_population": "SCORE2: 40–69 tuổi; SCORE2-OP: ≥70 tuổi (chưa ASCVD/ĐTĐ/CKD nặng)",
        "components": ["Tuổi", "Giới", "Hút thuốc", "HA tâm thu", "Non-HDL cholesterol",
                       "Vùng nguy cơ (calibration theo quốc gia)"],
        "calculation_method": "Dùng bảng/biểu đồ SCORE2 đã hiệu chỉnh theo vùng nguy cơ – "
                              "dùng công cụ chính thức ESC, KHÔNG tự nội suy.",
        "interpretation": "Ngưỡng nguy cơ thay đổi theo nhóm tuổi (ESC 2021).",
        "action_thresholds": "Theo ngưỡng tuổi của ESC 2021: vd <50t: <2.5% thấp-TB, 2.5–<7.5% cao, ≥7.5% rất cao.",
        "clinical_action": "Kết hợp ra quyết định chung; lưu ý hiệu chỉnh vùng nguy cơ phù hợp.",
        "limitations": "Hiệu chỉnh cho quần thể châu Âu; áp dụng ngoài châu Âu cần thận trọng.",
        "source": "SCORE2 working group & ESC CVD risk collaboration. Eur Heart J 2021;42:2439-2454.",
        "guideline_reference": "ESC 2021 CVD prevention.",
    },
    # ---- Bổ sung đợt rà soát: công cụ lão khoa/đa thuốc + nguy cơ tim mạch ĐTĐ ----
    {
        "score_id": "beers",
        "score_name": "AGS Beers Criteria® 2023",
        "clinical_area": "Lão khoa - Đa bệnh lý",
        "clinical_situation": "Rà soát thuốc ở người cao tuổi (≥65) – thuốc có thể không phù hợp (PIM)",
        "purpose": "Nhận diện thuốc cần TRÁNH hoặc DÙNG THẬN TRỌNG ở người cao tuổi để giảm hại do thuốc",
        "target_population": "Người ≥65 tuổi (ngoài chăm sóc giảm nhẹ/hospice)",
        "components": [
            "Danh mục thuốc TRÁNH ở hầu hết người cao tuổi",
            "Thuốc TRÁNH theo bệnh/tình trạng kèm theo",
            "Thuốc DÙNG THẬN TRỌNG",
            "Tương tác thuốc–thuốc quan trọng cần tránh",
            "Thuốc cần HIỆU CHỈNH/TRÁNH theo chức năng thận",
        ],
        "calculation_method": "KHÔNG phải điểm số/công thức – là DANH MỤC TIÊU CHÍ rõ ràng. "
                              "Tra cứu danh mục đầy đủ trong tài liệu gốc AGS 2023 (hệ thống KHÔNG sao chép "
                              "toàn bộ tiêu chí để tránh sai sót; dùng bản chính thức).",
        "interpretation": "Bao gồm hơn 3 chục thuốc/nhóm cần tránh + 40+ thuốc cần thận trọng theo bệnh kèm.",
        "action_thresholds": "Khi gặp thuốc nằm trong danh mục → đánh giá lại chỉ định, cân nhắc deprescribing/thay thế, "
                             "ghi lý do nếu vẫn tiếp tục. 2023 cập nhật phần KHÁNG ĐÔNG và estrogen sau mãn kinh.",
        "clinical_action": "Dùng cùng STOPP/START và đánh giá lão khoa toàn diện (CGA); không áp dụng máy móc.",
        "limitations": "Là công cụ HỖ TRỢ, không thay phán đoán lâm sàng; chủ yếu chuẩn hoá theo Hoa Kỳ.",
        "source": "By the 2023 AGS Beers Criteria Update Expert Panel. J Am Geriatr Soc 2023;71:2052-2081 (doi:10.1111/jgs.18372).",
        "guideline_reference": "AGS 2023 Beers Criteria® (bản chính thức – cần tra danh mục đầy đủ).",
    },
    {
        "score_id": "stopp_start",
        "score_name": "STOPP/START phiên bản 3 (2023)",
        "clinical_area": "Lão khoa - Đa bệnh lý",
        "clinical_situation": "Rà soát kê đơn không phù hợp (STOPP) và thiếu sót điều trị (START) ở người cao tuổi",
        "purpose": "Phát hiện thuốc nên NGƯNG (STOPP) và thuốc nên BẮT ĐẦU nhưng bị bỏ sót (START)",
        "target_population": "Người cao tuổi (thường ≥65), đặc biệt đa thuốc/đa bệnh",
        "components": [
            "STOPP: tiêu chí thuốc có thể không phù hợp cần cân nhắc ngưng",
            "START: tiêu chí thuốc nên được chỉ định nhưng đang bị bỏ sót",
            "Sắp xếp theo hệ cơ quan/nhóm thuốc",
        ],
        "calculation_method": "KHÔNG phải điểm số – là BỘ TIÊU CHÍ rõ ràng. Phiên bản 3 (2023) gồm "
                              "133 tiêu chí STOPP + 57 tiêu chí START (tổng 190). Tra danh mục đầy đủ ở tài liệu gốc.",
        "interpretation": "Mỗi tiêu chí mô tả tình huống kê đơn cần xem lại (STOPP) hoặc cần bổ sung (START).",
        "action_thresholds": "Khi một đơn thuốc khớp tiêu chí STOPP → cân nhắc ngưng/giảm; khớp START → cân nhắc bổ sung. "
                             "Luôn cá thể hoá theo mục tiêu điều trị & kỳ vọng sống.",
        "clinical_action": "Kết hợp Beers + đối chiếu thuốc (medication reconciliation) khi chuyển tiếp chăm sóc.",
        "limitations": "Hỗ trợ ra quyết định, không thay phán đoán; cần bản đầy đủ để áp dụng đúng.",
        "source": "O'Mahony D, et al. STOPP/START criteria version 3. Eur Geriatr Med 2023;14:625-632 (doi:10.1007/s41999-023-00777-y).",
        "guideline_reference": "STOPP/START v3 (2023) – bản chính thức.",
    },
    {
        "score_id": "score2_diabetes",
        "score_name": "SCORE2-Diabetes (ESC 2023)",
        "clinical_area": "Nội tiết - Chuyển hóa",
        "clinical_situation": "Đái tháo đường típ 2 chưa có ASCVD – ước tính nguy cơ tim mạch 10 năm",
        "purpose": "Ước tính nguy cơ biến cố tim mạch tử vong + không tử vong 10 năm riêng cho ĐTĐ típ 2",
        "target_population": "Người ĐTĐ típ 2, chưa có ASCVD hoặc tổn thương cơ quan đích nặng",
        "components": ["Các yếu tố của SCORE2 (tuổi, giới, hút thuốc, HA tâm thu, non-HDL)",
                       "Tuổi lúc CHẨN ĐOÁN ĐTĐ", "HbA1c", "eGFR", "Vùng nguy cơ (hiệu chỉnh)"],
        "calculation_method": "Mở rộng từ SCORE2 (thêm tuổi chẩn đoán ĐTĐ, HbA1c, eGFR) – "
                              "dùng công cụ chính thức ESC, KHÔNG tự nhập hệ số tay.",
        "interpretation": "Phân tầng nguy cơ tim mạch 10 năm ở bệnh nhân ĐTĐ típ 2 (theo ngưỡng tuổi ESC).",
        "action_thresholds": "Theo ngưỡng nguy cơ của ESC 2023 (thấp-TB/cao/rất cao) để định hướng đích LDL, statin, "
                             "và cân nhắc SGLT2i/GLP-1 RA có lợi ích tim mạch.",
        "clinical_action": "Thay cho việc mặc định coi mọi ĐTĐ là 'nguy cơ cao'; cá thể hoá điều trị.",
        "limitations": "Hiệu chỉnh cho quần thể châu Âu; chỉ dùng khi CHƯA có ASCVD/tổn thương cơ quan đích nặng.",
        "source": "SCORE2-Diabetes Working Group & ESC CVD Risk Collaboration. Eur Heart J 2023;44:2544-2556.",
        "guideline_reference": "ESC 2023 CVD trong ĐTĐ (Eur Heart J 2023;44:4043).",
    },
]


def seed_verified_scores() -> Dict[str, int]:
    """Nâng cấp các thang điểm từ skeleton -> verified (hoặc thêm mới nếu chưa có).

    Trả về {'updated': x, 'inserted': y}. Ghi change log khi đổi cách dùng.
    """
    updated = inserted = 0
    with session_scope() as s:
        for data in VERIFIED_SCORES:
            payload = dict(data)
            payload["update_status"] = "verified"
            payload["last_reviewed_date"] = _TODAY
            obj = s.query(ClinicalScore).filter_by(score_id=data["score_id"]).first()
            if obj:
                changed_status = obj.update_status != "verified"
                for k, v in payload.items():
                    if hasattr(obj, k):
                        setattr(obj, k, v)
                updated += 1
                if changed_status:
                    s.add(ChangeLogEntry(
                        change_summary=f"Thang điểm '{data['score_name']}' được xác minh công thức "
                                       f"+ nguồn ({data['source']}).",
                        source=data.get("source"), module="clinical_scores.verified",
                        created_by="seed_verified_scores"))
            else:
                s.add(ClinicalScore(**{k: v for k, v in payload.items()
                                       if hasattr(ClinicalScore, k)}))
                inserted += 1
    logger.info("Verified scores: cập nhật %d, thêm mới %d.", updated, inserted)
    return {"updated": updated, "inserted": inserted}
