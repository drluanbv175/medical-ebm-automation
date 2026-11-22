#!/usr/bin/env python3
"""Giả lập ĐỊNH KỲ hệ nghiên cứu G0→G10 — canary tháng (R9, bác sĩ giao 14/11/2026).

VÌ SAO CÓ
---------
Hai lượt giả lập đề tài RCT (13–14/11/2026) chạy TAY tìm ra 17 + 16 khiếm khuyết (K1–K17, N1–N16, báo cáo
`KET-QUA-GIA-LAP/BAO-CAO-GIA-LAP-CHI-TIET-20261114.md` của worktree giả lập). Chạy tay thì chỉ chạy khi có người nhớ;
bản sửa sau này có thể làm hỏng lại một chỗ đã sửa mà không ai thấy. Công cụ này biến lượt giả lập thành phép đo
lặp lại được, chạy mỗi tháng trong tác vụ `kiem-tra-hoan-thien-he-thong-thang`, và chỉ báo khi có khiếm khuyết MỚI so
với lần trước.

LÀM GÌ (chỉ đo và báo)
----------------------
A. DÂY CHUYỀN THẬT TRÊN BẢN SAO TẠM. Chép `tools/ app/ config/ templates/` của repo vào một thư mục tạm, tạo `exports/`
   rỗng ở đó rồi chạy `run_pipeline.py` của BẢN SAO. `run_pipeline` neo `exports/` theo vị trí tệp của chính nó, nên
   mọi đầu ra nằm trong thư mục tạm; `exports/` thật không bị đụng (cuối lượt còn kiểm lại: thư mục `ZZCANARY-*` mới
   xuất hiện trong `exports/` thật là khiếm khuyết `he:ro_ri_exports_that`).
   Mỗi KỊCH BẢN là một đề tài tổng hợp cho một thiết kế chính (`KICH_BAN`: RCT kết cục nhị phân, cắt ngang mô tả
   và từ 15/11/2026 sáu thiết kế còn lại ở `gia_lap_kich_ban_them.py`; thêm thiết kế = thêm một mục).
   Một «PI GIẢ LẬP» làm đúng việc PI làm: đọc cổng đang chờ gì, điền nội dung
   kịch bản vào `study_meta.json → gate_params`, chép dấu vân tay cổng in ra, chạy lại. Mỗi lần như vậy là một «can
   thiệp như PI». Can thiệp ĐÚNG THIẾT KẾ là điền nội dung và xác nhận dấu vân tay của G0/G1/G3, mỗi loại một lần.
   Mọi can thiệp khác (khai `query_en` vì máy dịch lạc đề — K4; tự chạy cổng vì pipeline không chạy lại — N4; điền
   lặp lại) là khiếm khuyết của máy.
   Đo: số can thiệp, cổng dừng (đúng thiết kế là G5: chờ ký SAP), cổng cứng có bị «đạt» khi chưa ký không, thiết kế
   máy tự suy ở G1 (K1), crash (traceback, mã thoát lạ), và bảng `kiem_chi_tiet_he_nghien_cuu` của đề tài tạm.
   Trước mỗi lượt PI, mtime mọi tệp đề tài tạm lùi 600 s (giữ thứ tự): PI thật không làm lượt kế trong vòng 2 phút, còn
   độ tươi của pipeline có dung sai «cùng đợt» 120 s — không lùi thì số đo phụ thuộc tốc độ máy (N5).
B. TEST ĐẦU–CUỐI SẴN CÓ (pytest, khoá GIẢ của conftest, thư mục tmp của pytest): chuỗi G0→G9 → G10 khoá cho đủ 8
   thiết kế (`test_chung_h_dau_cuoi_g10_toi_ready_khoa_va_rang_buoc`) và gói trình Hội đồng trước IRB (G10-09).
   Diễn tập G2→G7 kèm nhập kép/SPSS/R của lượt 14/11 chưa tách được thành test commit (phụ thuộc bản chụp Phần A,
   SPSS, R): danh sách `KIEM_PYTEST` để thêm khi có.
C. SO VỚI LẦN TRƯỚC. Mỗi khiếm khuyết là một KHOÁ ổn định (vd `rct_nhi_phan:can_thiep_do_may:G3:tu_chay_cong`). So với
   tập khoá của lần trước CÙNG CHẾ ĐỘ (trực tuyến / ngoại tuyến) trong `state/gia-lap-dinh-ky-gan-nhat.json`. Phần
   không đo được lượt này giữ nguyên khoá cũ (không coi là «đã hết»): cả kịch bản (kể cả kịch bản không chạy vì
   `--kich-ban` chọn tập con, hoặc lỗi nội bộ canary giữa chừng), pytest, hoặc chỉ phần phụ thuộc G0 khi G0 dùng nền cũ
   (vd K4 `…:G0:khai_query_en`). Lần đầu chưa có mốc thì mọi khiếm khuyết đang có đều là MỚI.

G0 VÀ MẠNG
----------
Mặc định NGOẠI TUYẾN: `USE_MOCK_SOURCES=true` cho mọi tiến trình con. Ở chế độ đó `run_g0_auto` trả bản ghi giả lập và
guardrail R1B chặn G0 (đúng luật: dữ liệu giả không được qua cổng) ⇒ «G0 không đo được ngoại tuyến». Để vẫn đo được
G1–G4, công cụ nạp NỀN G0 lưu từ lượt TRỰC TUYẾN gần nhất (`state/gia-lap-dinh-ky/nen-g0/<kịch bản>/`: tệp G0_* sau
khi PI đã khai query_en, đúng trạng thái «chờ PICO»); pipeline khi đó chỉ chấm lại G0 từ tệp, không tra PubMed. Chưa
có nền ⇒ kịch bản đó «không đo được ngoại tuyến». `--truc-tuyen` cho G0 tra PubMed/ClinicalTrials.gov thật và lưu nền
mới; mạng hỏng giữa chừng ⇒ dùng nền cũ và ghi «G0 không đo được (mạng)». Ngoại tuyến thì phần tra cứu của G1/G2
cũng dùng nguồn giả lập, nên số đo ngoại tuyến chỉ so với lượt ngoại tuyến trước (state tách theo chế độ).

RANH GIỚI
---------
Không ký gì (không gọi approve_gate*/mark_study_synthetic); pytest dùng khoá giả của conftest. Không đọc hay sửa
`exports/` thật, `~/.ebm-secrets`, `.env`. Không sửa mã hệ thống. Nội dung PI trong kịch bản là dữ liệu TỔNG HỢP có
nhãn GIẢ LẬP, không PII; số và PMID của kịch bản RCT lấy từ lượt giả lập 14/11 (đã kiểm qua PubMed lúc đó).

MÃ THOÁT
--------
0 = đo đủ và không có khiếm khuyết mới · 1 = có khiếm khuyết MỚI (ưu tiên hơn 2) · 2 = có phần không đo được (vd G0
ngoại tuyến, không chạy được pytest, kịch bản không chạy lượt này, lỗi nội bộ của canary) mà không có khiếm khuyết mới
— «không đo được» không bao giờ là «ổn». Lỗi nội bộ chưa bắt của canary cũng trả 2 (`chay_an_toan`), không bao giờ 1.

Dùng (từ thư mục repo y khoa hoặc gốc workspace):
    python3 tools/gia_lap_dinh_ky.py [--truc-tuyen] [--kich-ban rct_nhi_phan ...] [--bo-pytest] [--khong-ghi]
                                     [--giu-thu-muc] [--json]
Cần bác sĩ kiểm chứng.
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import importlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS = REPO_ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from gia_lap_kich_ban_them import SAI_LECH_PI, bien_so_them, ho_so_tron_vong, kich_ban_them  # noqa: E402

PHIEN_BAN = 1
STATE_PATH = REPO_ROOT / "state" / "gia-lap-dinh-ky-gan-nhat.json"
# 17/11/2026 (đưa 16 kịch bản vào CI): CI không tra PubMed được ⇒ nền G0 đã lưu được commit ở tests/fixtures/
# gia_lap_nen_g0/ và trỏ tới bằng GIA_LAP_NEN_G0_DIR. Vắng biến ⇒ thư mục state như cũ.
NEN_G0_DIR = (Path(os.environ["GIA_LAP_NEN_G0_DIR"]) if os.environ.get("GIA_LAP_NEN_G0_DIR")
              else REPO_ROOT / "state" / "gia-lap-dinh-ky" / "nen-g0")
# Thư mục chép sang bản sao tạm — đủ cho chuỗi G0→G5 của run_pipeline (đo 14/11/2026).
THU_MUC_CHEP = ("tools", "app", "config", "templates")
BO_QUA_KHI_CHEP = shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store", "._*")
SO_VONG_TOI_DA = 14
# PI thật mất hàng phút tới hàng ngày giữa hai lượt; máy chạy canary chỉ mất vài giây. Độ tươi của run_pipeline đo bằng
# mtime với dung sai «cùng đợt» 120 s (pipeline_freshness.SAME_RUN_TOLERANCE_S) ⇒ không mô phỏng thời gian trôi thì số
# đo phụ thuộc tốc độ máy (N5 của giả lập 14/11) và đổi giữa các lần chạy. Trước mỗi lượt PI, lùi mtime MỌI tệp đề tài
# tạm đúng số giây này (giữ nguyên thứ tự) — lớn hơn hẳn dung sai.
GIAY_GIUA_HAI_LUOT_PI = 600
TIEN_TO_DE_TAI = "ZZCANARY-"  # đề tài tạm luôn mang tiền tố này — dùng cho chốt rò rỉ sang exports/ thật
CONG_MEM = ("G0", "G1", "G3")  # cổng PI xác nhận bằng dấu vân tay (không ký sổ cái)
CONG_CUNG_TRUOC_G5 = ("G2", "G4")  # cổng cứng chuỗi đi qua trước G5 — chưa ký thì KHÔNG được «đạt»
TRANG_THAI_DUNG_PIPELINE = ("blocked_missing_input", "chan_song", "dung_lech_xuyen_cong", "dung_nen_bi_chan",
                            "failed")
# 15/11/2026 (đồng bộ xuyên cổng, PR y khoa #268): G3-T2 — agent bien-so-nghien-cuu dựng `_bo-bien-rieng.csv` +
# `_ma-tran-muc-tieu-bien.csv` (G3-AUTO-19) là việc ĐÚNG THIẾT KẾ của quy trình, không phải máy hỏng.
# 15/11/2026 (bác sĩ chọn G3-T2 thêm bảng .md): agent soạn `G3_BO_BIEN_SO_<mã>.md` (tools/bang_bien_g3.py) rồi PI đọc
# và ghi gate_params.G3.bo_bien_so_duyet — cũng là bước ĐÚNG THIẾT KẾ (nguồn người duyệt của G5-AUTO-11).
CAN_THIEP_DUNG_THIET_KE = ("dien_noi_dung", "xac_nhan_dau_van_tay", "dung_bo_bien_ma_tran", "soan_bang_bien_g3",
                           "duyet_bang_bien_g3", "soan_van_ban_g0")
# PI tự chạy cổng mà tiêu chí máy chưa đạt KHÔNG đổi (15/11/2026, giả lập 8 thiết kế: G3-AUTO-19 thiếu bộ biến làm
# canary đếm «tự chạy G3» thành lỗi N4 ở 4/6 thiết kế): chạy lại không giúp gì ⇒ pipeline không có lỗi «không chạy
# lại»; tiêu chí còn kẹt mới là khiếm khuyết và đã có khoá `ket:` riêng. Ghi lại để thấy, không tính là can thiệp
# do máy.
CAN_THIEP_KHONG_DO_MAY = ("tu_chay_cong_khong_doi",)
COT_BO_BIEN = ("Variable / Field Name", "Form Name", "Section Header", "Field Type", "Field Label",
               "Choices, Calculations, OR Slider Labels", "Field Note", "Text Validation Type OR Show Slider Number",
               "Text Validation Min", "Text Validation Max", "Identifier?", "Branching Logic (Show field only if...)",
               "Required Field?", "Custom Alignment", "Question Number (surveys only)", "Matrix Group Name",
               "Matrix Ranking?", "Field Annotation")
COT_MA_TRAN = ("muc_tieu", "khai_niem", "vai_tro", "bien", "kieu", "cau_hoi", "cong_cu", "phan_tich_sap", "ghi_chu")
NHAN = "GIẢ LẬP CANARY — dữ liệu tổng hợp, không PII"
_DAU_VAN_TAY_RE = re.compile(r'dau_van_tay_chot="([0-9a-f]{8,64})"')
_TRACEBACK = "Traceback (most recent call last)"

# Test đầu–cuối sẵn có (khoá giả conftest, tmp_path). Thêm test diễn tập khác vào đây khi đã tách thành test commit.
KIEM_PYTEST = (
    "tests/test_g10_hoan_thien_20261005.py::test_chung_h_dau_cuoi_g10_toi_ready_khoa_va_rang_buoc",
    "tests/test_g10_hoan_thien_20261005.py::test_g10_09_goi_trinh_hoi_dong_truoc_irb_toi_ready_va_khoa",
)
THIET_KE_TAM = ("rct", "cohort", "case_control", "cross_sectional", "diagnostic", "prediction", "qualitative", "sr_ma")


# ══════════════════════════════════════════════════════════════════════════════════════════════ kịch bản
def _vi(s: str) -> str:
    """Nội dung PI điền (16/11/2026: KHÔNG còn nối hậu tố NHAN vào từng câu — văn bản đề cương/phiếu
    đồng ý đọc như văn bản lỗi; tính tổng hợp của đề tài đã ghi ở mã ZZCANARY, study_kind=synthetic_test và
    sổ `gia_lap_pi_dien` mang NHAN cho từng trường)."""
    return s


_G0_FINER = {
    "finer_feasible": _vi("Đạt — phòng khám ngoại trú có lượng bệnh nhân tăng huyết áp lớn"),
    "finer_interesting": _vi("Đạt — kiểm soát huyết áp ngoại trú là vấn đề thực hành thường gặp"),
    "finer_novel": _vi("Đạt — dữ liệu trong bối cảnh ngoại trú Việt Nam còn ít (theo nền bằng chứng G0)"),
    "finer_ethical": _vi("Đạt — nguy cơ tối thiểu cho người tham gia"),
    "finer_relevant": _vi("Đạt — kết quả áp dụng trực tiếp cho quản lý tăng huyết áp ngoại trú"),
}

# Mỗi kịch bản: chủ đề + query_en PI khai (K4) + nội dung PI theo cổng + phần xác nhận (dấu vân tay điền lúc chạy).
# «<HOM_NAY>» thay bằng ngày chạy. Thêm thiết kế: thêm một mục, đặt `thiet_ke` đúng mã 8 thiết kế của hệ.
KICH_BAN: Dict[str, Dict[str, Any]] = {
    "rct_nhi_phan": {
        "study": f"{TIEN_TO_DE_TAI}RCT-NHI-PHAN",
        "thiet_ke": "rct",
        "mo_ta": "RCT song song 2 nhánh, kết cục nhị phân (tái hiện giả lập 14/11/2026)",
        "topic": ("Hiệu quả của tin nhắn nhắc uống thuốc so với chăm sóc thường quy lên tỷ lệ kiểm soát huyết áp sau "
                  "6 tháng ở người tăng huyết áp điều trị ngoại trú: thử nghiệm lâm sàng ngẫu nhiên có đối chứng"),
        "query_en": ('("text messaging"[tiab] OR "text message"[tiab] OR SMS[tiab] OR "short message"[tiab] OR '
                     '"Text Messaging"[MeSH]) AND (hypertension[MeSH] OR hypertension[tiab] OR hypertensive[tiab]) '
                     'AND (adherence[tiab] OR "Medication Adherence"[MeSH] OR "blood pressure control"[tiab] OR '
                     '"blood pressure"[tiab])'),
        "cong_dung_mong_doi": "G5",
        # G3-T2 (agent bien-so-nghien-cuu): (tên, loại, nhãn, lựa chọn, kiểm, min, max) + ma trận mục tiêu–biến
        "bien_so": {
            "bo_bien": [
                ("record_id", "text", "Mã nghiên cứu", "", "", "", ""),
                ("ngay_ngau_nhien", "text", "Ngày ngẫu nhiên hoá", "", "date_dmy", "", ""),
                ("nhom", "radio", "Nhóm phân bổ", "1, Tin nhắn SMS | 0, Chăm sóc thường quy", "", "", ""),
                ("tuoi", "text", "Tuổi (năm)", "", "integer", "18", "100"),
                ("gioi", "radio", "Giới", "1, Nam | 2, Nữ", "", "", ""),
                ("ha_tt_t6", "text", "Huyết áp tâm thu tháng 6 (mmHg)", "", "integer", "60", "260"),
                ("kiem_soat_t6", "radio", "Kiểm soát huyết áp tháng 6 (<140/90)", "0, Không | 1, Có", "", "", ""),
                # 22/11/2026 (CONSORT 2025 mục 27/29): tổn hại theo ĐÚNG định nghĩa SAP §15 của hồ sơ — trước đây RCT
                # giả lập không có biến tổn hại nào nên bản thảo không thể báo tác hại theo nhóm.
                ("bien_co_bat_loi", "radio", "Có biến cố bất lợi trong 6 tháng (phàn nàn, lo âu do tin nhắn hoặc cơn "
                 "tăng huyết áp)", "0, Không | 1, Có", "", "", ""),
                ("bien_co_nghiem_trong", "radio", "Có biến cố bất lợi nghiêm trọng trong 6 tháng (cơn tăng huyết áp "
                 "≥ 180/110 mmHg phải xử trí hoặc nhập viện)", "0, Không | 1, Có", "", "", ""),
            ],
            "ma_tran": [
                ("1", "tỷ lệ kiểm soát huyết áp tại tháng 6", "ket_cuc_chinh", "kiem_soat_t6", "nhi_phan", "C1",
                 "đo huyết áp chuẩn hoá", "SAP §4 kết cục chính"),
                ("1", "nhóm nhận tin nhắn SMS", "phoi_nhiem", "nhom", "nhi_phan", "R1", "danh sách ngẫu nhiên",
                 "SAP §4 nhóm so sánh"),
                ("1", "tuổi", "hiep_bien", "tuoi", "lien_tuc", "A1", "phiếu", "SAP §5 hiệp biến"),
                ("1", "giới", "hiep_bien", "gioi", "nhi_phan", "A2", "phiếu", "SAP §5 hiệp biến"),
                ("1", "biến cố bất lợi (tổn hại)", "mo_ta", "bien_co_bat_loi", "nhi_phan", "S1", "phiếu biến cố",
                 "SAP §15 tổn hại"),
                ("1", "biến cố bất lợi nghiêm trọng (tổn hại)", "mo_ta", "bien_co_nghiem_trong", "nhi_phan", "S2",
                 "phiếu biến cố", "SAP §15 tổn hại"),
            ],
        },
        "pi": {
            "G0": {
                "population": ("Người trưởng thành ≥18 tuổi tăng huyết áp đang dùng thuốc hạ áp, quản lý ngoại trú, "
                                  "có điện thoại di động nhận tin nhắn"),
                "intervention": ("Tin nhắn SMS tự động nhắc uống thuốc hạ áp hằng ngày kèm chăm sóc thường quy trong "
                                 "6 tháng"),
                "comparison": "Chăm sóc thường quy (không nhận tin nhắn nhắc)",
                "outcomes": ["Tỷ lệ kiểm soát huyết áp (<140/90 mmHg) tại tháng 6",
                             "Thay đổi huyết áp tâm thu so với ban đầu", "Tuân thủ dùng thuốc tự báo cáo"],
                "primary_outcome": "Tỷ lệ người bệnh đạt kiểm soát huyết áp",
                "primary_outcome_measure": "Huyết áp phòng khám trung bình 2 lần đo <140/90 mmHg",
                "primary_outcome_timepoint": "Tháng thứ 6 sau ngẫu nhiên hoá",
                "hypothesis_h0": "Tỷ lệ kiểm soát huyết áp ở nhóm tin nhắn bằng nhóm chăm sóc thường quy",
                "hypothesis_h1": "Tỷ lệ kiểm soát huyết áp ở nhóm tin nhắn khác nhóm chăm sóc thường quy",
                "expected_direction": "Nhóm tin nhắn có tỷ lệ kiểm soát cao hơn",
                "test_type": "superiority",
                "question_type": "treatment",
                **_G0_FINER,
                "evidence_reviewed_confirmed": True,
                "novelty_justification": _vi("Các SR/MA hiện có (PMID 36828607, 35014147) báo hiệu quả SMS không đồng "
                                             "nhất; thiếu RCT tại Việt Nam với kết cục tỷ lệ kiểm soát 6 tháng"),
                "registry_manual_checked": {"ictrp": "<HOM_NAY>", "prospero": None},
                "registry_overlap_assessment": _vi("Đã tra WHO ICTRP và ClinicalTrials.gov: có thử "
                                                   "nghiệm SMS/THA ở quần thể và bối cảnh khác"),
            },
            "G1": {
                "protocol_version": "1.0",
                "design": "rct", "design_confirmed": True,
                "design_rationale": _vi("Câu hỏi điều trị (G0 treatment/superiority) — RCT song song 2 nhánh, "
                                        "tỷ lệ 1:1"),
                "objectives": ["So sánh tỷ lệ kiểm soát huyết áp tại tháng 6 giữa nhóm nhận tin nhắn SMS nhắc uống "
                               "thuốc và nhóm chăm sóc thường quy"],
                "research_question": ("Ở người tăng huyết áp điều trị ngoại trú, tin nhắn nhắc uống thuốc có làm tăng "
                                      "tỷ lệ kiểm soát huyết áp sau 6 tháng so với chăm sóc thường quy không?"),
                "primary_outcome": {"name": "Tỷ lệ người bệnh đạt kiểm soát huyết áp",
                                    "measure": "Huyết áp phòng khám trung bình 2 lần đo <140/90 mmHg",
                                    "timepoint": "Tháng thứ 6 sau ngẫu nhiên hoá", "type": "nhị phân"},
                "secondary_outcomes": ["Thay đổi huyết áp tâm thu tại tháng 6",
                                       "Tuân thủ dùng thuốc tự báo cáo tại tháng 6"],
                "population": ("Người trưởng thành ≥18 tuổi tăng huyết áp đang dùng thuốc hạ áp, quản lý ngoại trú, "
                                  "có điện thoại di động"),
                "inclusion_criteria": ["Tuổi ≥18", "Chẩn đoán tăng huyết áp, đang dùng ≥1 thuốc hạ áp",
                                       "Có điện thoại di động nhận được tin nhắn"],
                "exclusion_criteria": ["Không đọc được tin nhắn", "Đang mang thai",
                                       "Dự kiến chuyển nơi điều trị trong 6 tháng"],
                "setting": "Phòng khám ngoại trú bệnh viện",
                "study_period": "2027-03 đến 2028-03",
                "intervention_or_exposure": ("Tin nhắn SMS tự động nhắc uống thuốc hạ áp mỗi ngày trong 6 tháng, kèm "
                                             "chăm sóc thường quy"),
                "comparator": "Chăm sóc thường quy (không tin nhắn nhắc)",
                "recruitment_strategy": "Tuyển liên tiếp người bệnh đủ tiêu chuẩn tại phòng khám ngoại trú",
                "follow_up_schedule": "Ban đầu, tháng 3 và tháng 6",
                "estimand": {
                    "population": "Người tăng huyết áp điều trị ngoại trú đủ tiêu chuẩn",
                    "treatment_condition": "Tin nhắn SMS nhắc uống thuốc so với chăm sóc thường quy",
                    "variable": "Đạt kiểm soát huyết áp (<140/90 mmHg) tại tháng 6",
                    "intercurrent_events_strategy": "Treatment-policy cho ngừng nhận tin nhắn hoặc đổi thuốc",
                    "population_summary_measure": "Hiệu số tỷ lệ (risk difference)",
                },
                "team_roles": _vi("Chủ nhiệm (PI), nhà phương pháp, thống kê viên, quản lý dữ liệu — vai trò, không "
                                  "ghi danh tính"),
                "background_problem": _vi("Tỷ lệ kiểm soát huyết áp ở người tăng huyết áp điều trị ngoại trú còn thấp, "
                                          "một phần do quên uống thuốc"),
                "evidence_summary": _vi("Tổng quan hệ thống (PMID 36828607) cho thấy can thiệp số giảm HA tâm thu so "
                                        "với chăm sóc thường quy, bằng chứng mức thấp; TEXT4BP (PMID 35342691) báo tỷ "
                                        "lệ đạt đích HA 70% so với 48% sau 3 tháng"),
                "knowledge_gap": _vi("Thiếu RCT tại Việt Nam với kết cục tỷ lệ kiểm soát huyết áp sau 6 tháng"),
                "benefit_risk_rationale": _vi("Can thiệp nguy cơ tối thiểu, lợi ích tiềm năng tăng tuân thủ"),
                "study_schema_timeline": "Sàng lọc → ngẫu nhiên hoá → can thiệp 6 tháng → đánh giá tháng 3 và tháng 6",
                "intervention_dose_adherence": ("1 tin nhắn/ngày trong 6 tháng; tuân thủ đo bằng tỷ lệ tin nhắn đã gửi "
                                                "thành công"),
                "stopping_rescue_rules": ("Ngừng tin nhắn khi người tham gia yêu cầu; huyết áp ≥180/110 mmHg chuyển "
                                          "xử trí theo phác đồ"),
                "critical_to_quality": _vi("Đo huyết áp chuẩn hoá (máy đã hiệu chuẩn, 2 lần đo); mất theo dõi <20%"),
                "monitoring_plan": _vi("Giám sát an toàn định kỳ 3 tháng"),
                "randomisation": _vi("Danh sách ngẫu nhiên khối hoán vị cỡ 4–6 sinh bằng phần mềm, tỷ lệ 1:1"),
                "allocation_concealment": ("Phân bổ trung tâm qua phong bì đánh số kín do người không tham gia "
                                           "tuyển giữ"),
                "blinding": "Người đo huyết áp và thống kê viên được làm mù; người tham gia không làm mù được",
                "risk_register": [], "budget": [],
                "annex2": {"applicable": False, "methodologies": []},
                "bias_controls_confirmed": True, "protocol_core_confirmed": True,
                "feasibility_confirmed": True, "evidence_review_confirmed": True,
            },
            "G3": {
                "effect_size": 1.4583, "effect_type": "RR", "dropout": 0.2, "p0": 0.48,
                "alpha": 0.05, "power": 0.8, "hypothesis_type": "superiority",
                "effect_source": ("PMID: 35342691 (TEXT4BP) — tỷ lệ đạt đích HA 70% so với 48% sau 3 tháng ⇒ "
                                  "RR≈1,458 (số liệu lấy từ tóm tắt bài báo, đã đối chiếu trên PubMed)"),
                "p0_source": "PMID: 35342691 — tỷ lệ đạt đích HA nhóm chứng 48% sau 3 tháng",
                "dropout_source": _vi("Giả định thận trọng 20% — chưa có nguồn y văn"),
                "effect_source_confirmed": True, "assumptions_confirmed": True, "hypothesis_confirmed": True,
                "powered_for_outcome": "Tỷ lệ người bệnh đạt kiểm soát huyết áp",
                "recruitment_feasibility_confirmed": True,
                "software": "run_g3_auto.py (two-proportion z-test)",
            },
        },
        "xac_nhan": {
            "G0": {"pico_confirmed": True, "reviewed_by_role": "PI"},
            "G1": {"reviewed_by_role": "methodologist"},
            "G3": {"reviewed_by_role": "STATISTICIAN"},
        },
    },
    "cat_ngang_mo_ta": {
        "study": f"{TIEN_TO_DE_TAI}CAT-NGANG-MO-TA",
        "thiet_ke": "cross_sectional",
        "mo_ta": "Cắt ngang mô tả, ước lượng một tỷ lệ theo độ chính xác",
        "topic": ("Tỷ lệ kiểm soát huyết áp và các yếu tố liên quan ở người tăng huyết áp điều trị ngoại trú: "
                  "nghiên cứu cắt ngang mô tả"),
        "query_en": ('(hypertension[MeSH] OR hypertension[tiab]) AND ("blood pressure control"[tiab] OR "controlled '
                     'hypertension"[tiab] OR "hypertension control"[tiab]) AND (outpatient*[tiab] OR "primary '
                     'care"[tiab]) AND (prevalence[tiab] OR "cross-sectional"[tiab])'),
        "cong_dung_mong_doi": "G5",
        "bien_so": {
            "bo_bien": [
                ("record_id", "text", "Mã nghiên cứu", "", "", "", ""),
                ("ngay_kham", "text", "Ngày khám khảo sát", "", "date_dmy", "", ""),
                ("tuoi", "text", "Tuổi (năm)", "", "integer", "18", "110"),
                ("gioi", "radio", "Giới", "1, Nam | 2, Nữ", "", "", ""),
                ("so_thuoc", "text", "Số thuốc hạ áp đang dùng", "", "integer", "0", "10"),
                ("ha_tt_tb", "text", "Huyết áp tâm thu trung bình 2 lần đo (mmHg)", "", "integer", "60", "260"),
                ("kiem_soat_ha", "radio", "Đạt kiểm soát huyết áp (<140/90)", "0, Không | 1, Có", "", "", ""),
                ("thuoc_khac", "text", "Thuốc khác đang dùng, ghi rõ", "", "", "", ""),
            ],
            "ma_tran": [
                ("1", "tỷ lệ kiểm soát huyết áp", "ket_cuc_chinh", "kiem_soat_ha", "nhi_phan", "C1",
                 "đo huyết áp chuẩn hoá", "SAP §4 tỷ lệ + KTC 95%"),
                ("1", "tuổi", "mo_ta", "tuoi", "lien_tuc", "A1", "phiếu", "SAP §3 mô tả"),
                ("1", "giới", "mo_ta", "gioi", "nhi_phan", "A2", "phiếu", "SAP §3 mô tả"),
                ("1", "số thuốc hạ áp", "mo_ta", "so_thuoc", "dem", "B1", "hồ sơ", "SAP §3 mô tả"),
            ],
        },
        "pi": {
            "G0": {
                "population": ("Người trưởng thành ≥18 tuổi tăng huyết áp đang điều trị ngoại trú"),
                "intervention": "Không áp dụng — nghiên cứu mô tả (yếu tố khảo sát: đặc điểm điều trị hiện tại)",
                "comparison": "Không áp dụng — nghiên cứu mô tả một nhóm",
                "outcomes": ["Tỷ lệ kiểm soát huyết áp (<140/90 mmHg) tại thời điểm khảo sát",
                             "Đặc điểm điều trị hạ áp hiện tại"],
                "primary_outcome": "Tỷ lệ người bệnh đạt kiểm soát huyết áp",
                "primary_outcome_measure": "Huyết áp phòng khám trung bình 2 lần đo <140/90 mmHg",
                "primary_outcome_timepoint": "Tại lần khám khảo sát",
                "hypothesis_h0": "Không áp dụng — nghiên cứu mô tả, không kiểm định giả thuyết",
                "hypothesis_h1": "Không áp dụng — nghiên cứu mô tả, không kiểm định giả thuyết",
                "expected_direction": "Không áp dụng — ước lượng tỷ lệ kèm khoảng tin cậy 95%",
                "test_type": "descriptive",
                "question_type": "descriptive",
                "descriptive_justification": _vi("Mục tiêu là ước lượng tỷ lệ kiểm soát huyết áp hiện tại để làm nền "
                                                 "cho can thiệp sau; không so sánh nhóm"),
                **_G0_FINER,
                "evidence_reviewed_confirmed": True,
                "novelty_justification": _vi("Chưa có số liệu tỷ lệ kiểm soát huyết áp cập nhật cho phòng khám ngoại "
                                             "trú này"),
                "registry_manual_checked": {"ictrp": "<HOM_NAY>", "prospero": None},
                "registry_overlap_assessment": _vi("Đã tra WHO ICTRP và ClinicalTrials.gov, không thấy đề tài trùng; "
                                                   "nghiên cứu mô tả tại một cơ sở"),
            },
            "G1": {
                "protocol_version": "1.0",
                "design": "cross_sectional", "design_confirmed": True,
                "design_rationale": _vi("Câu hỏi mô tả (G0 descriptive) — cắt ngang tại một thời điểm"),
                "objectives": ["Xác định tỷ lệ kiểm soát huyết áp ở người tăng huyết áp điều trị ngoại trú"],
                "research_question": ("Tỷ lệ người tăng huyết áp điều trị ngoại trú đạt kiểm soát huyết áp là bao "
                                      "nhiêu?"),
                "primary_outcome": {"name": "Tỷ lệ người bệnh đạt kiểm soát huyết áp",
                                    "measure": "Huyết áp phòng khám trung bình 2 lần đo <140/90 mmHg",
                                    "timepoint": "Tại lần khám khảo sát", "type": "nhị phân"},
                "secondary_outcomes": ["Đặc điểm điều trị hạ áp hiện tại"],
                "population": ("Người trưởng thành ≥18 tuổi tăng huyết áp đang điều trị ngoại trú"),
                "inclusion_criteria": ["Tuổi ≥18", "Chẩn đoán tăng huyết áp, đang điều trị ngoại trú ≥3 tháng"],
                "exclusion_criteria": ["Đang mang thai", "Không đồng ý tham gia"],
                "setting": "Phòng khám ngoại trú bệnh viện",
                "study_period": "2027-03 đến 2027-09",
                "intervention_or_exposure": "Không áp dụng — mô tả đặc điểm điều trị hiện tại",
                "comparator": "Không áp dụng",
                "recruitment_strategy": "Chọn mẫu liên tiếp người bệnh đủ tiêu chuẩn đến khám",
                "follow_up_schedule": "Không theo dõi — một lần khảo sát",
                "estimand": {
                    "population": "Người tăng huyết áp điều trị ngoại trú đủ tiêu chuẩn",
                    "treatment_condition": "Không áp dụng (mô tả)",
                    "variable": "Đạt kiểm soát huyết áp (<140/90 mmHg) tại lần khảo sát",
                    "intercurrent_events_strategy": "Không áp dụng (một lần đo)",
                    "population_summary_measure": "Tỷ lệ kèm khoảng tin cậy 95%",
                },
                "team_roles": _vi("Chủ nhiệm (PI), thống kê viên, quản lý dữ liệu — vai trò, không ghi danh tính"),
                "background_problem": _vi("Kiểm soát huyết áp ở người điều trị ngoại trú chưa được đo định kỳ"),
                "evidence_summary": _vi("Nền bằng chứng G0 cho thấy tỷ lệ kiểm soát khác nhau nhiều giữa cơ sở"),
                "knowledge_gap": _vi("Thiếu số liệu tỷ lệ kiểm soát cập nhật tại cơ sở này"),
                "benefit_risk_rationale": _vi("Không can thiệp, nguy cơ tối thiểu (chỉ đo huyết áp và hỏi thông tin)"),
                "study_schema_timeline": "Sàng lọc → đồng ý tham gia → đo huyết áp và phỏng vấn một lần tại lần khám",
                "intervention_dose_adherence": ("N/A — nghiên cứu mô tả, không có can thiệp; đặc điểm điều trị hiện "
                                                "tại ghi từ hồ sơ khám"),
                "stopping_rescue_rules": ("N/A — không can thiệp; huyết áp ≥180/110 mmHg chuyển bác sĩ điều trị xử trí "
                                          "theo phác đồ"),
                "critical_to_quality": _vi("Đo huyết áp chuẩn hoá (máy đã hiệu chuẩn, 2 lần đo)"),
                "monitoring_plan": _vi("Giám sát chất lượng dữ liệu hằng tháng"),
                # 21/11/2026 (K17 STROBE 9/19): sổ sai lệch riêng của đề tài, có chiều ảnh hưởng dự kiến
                "bias_controls": SAI_LECH_PI["cross_sectional"],
                "risk_register": [], "budget": [],
                "annex2": {"applicable": False, "methodologies": []},
                "bias_controls_confirmed": True, "protocol_core_confirmed": True,
                "feasibility_confirmed": True, "evidence_review_confirmed": True,
            },
            "G3": {
                "prevalence": 0.5, "precision": 0.05, "dropout": 0.1, "alpha": 0.05,
                "hypothesis_type": "descriptive_precision",
                "prevalence_source": _vi("Giả định p = 0,5 cho cỡ mẫu lớn nhất khi chưa có ước tính tại cơ sở"),
                "dropout_source": _vi("Giả định 10% phiếu không dùng được — chưa có nguồn y văn"),
                "effect_source_confirmed": True, "assumptions_confirmed": True, "hypothesis_confirmed": True,
                "powered_for_outcome": "Tỷ lệ người bệnh đạt kiểm soát huyết áp",
                "recruitment_feasibility_confirmed": True,
                "software": "run_g3_auto.py (ước lượng một tỷ lệ theo độ chính xác)",
            },
        },
        "xac_nhan": {
            "G0": {"pico_confirmed": True, "reviewed_by_role": "PI"},
            "G1": {"reviewed_by_role": "methodologist"},
            "G3": {"reviewed_by_role": "STATISTICIAN"},
        },
    },
}


# Sáu thiết kế còn lại (thuần tập, bệnh–chứng, chẩn đoán, dự báo, tổng quan/gộp, định tính) — 15/11/2026: canary phủ đủ
# 8 thiết kế (bác sĩ: «giả lập hoàn thiện chi tiết 8 loại thiết kế rồi vá»). Nội dung + nguồn số ở
# gia_lap_kich_ban_them; bộ biến + ma trận theo cùng khuôn `bien_so` (G3-T2) của hai kịch bản đầu.
KICH_BAN.update(kich_ban_them(_vi, TIEN_TO_DE_TAI))
for _ma, _bs in bien_so_them().items():
    KICH_BAN.get(_ma, {}).setdefault("bien_so", _bs)
for _ma, _hs in ho_so_tron_vong().items():
    if _ma in KICH_BAN:
        KICH_BAN[_ma]["ho_so_tron_vong"] = _hs
# 17/11/2026: kỹ thuật chọn mẫu PI khai ở G1 (mã g1_design_blocks hoặc «khac:<mô tả>») — trục ky_thuat_chon_mau của
# nhat_quan_xuyen_cong báo «chưa đủ» ở cả 16 kịch bản vì không kịch bản nào khai. Khai đúng cách tuyển đã viết.
_CHON_MAU = {"rct_nhi_phan": ["khac:chọn mẫu liên tiếp"], "cat_ngang_mo_ta": ["khac:chọn mẫu liên tiếp"],
             "thuan_tap_phoi_nhiem": ["toan_bo"], "benh_chung": ["khac:chọn mẫu liên tiếp"],
             "chan_doan": ["khac:chọn mẫu liên tiếp"], "mo_hinh_du_bao": ["khac:chọn mẫu liên tiếp"],
             "tong_quan_gop": ["khac:không áp dụng — tổng quan dùng dữ liệu đã công bố"],
             "dinh_tinh": ["khac:chọn mẫu có chủ đích"]}
for _ma, _cm in _CHON_MAU.items():
    if _ma in KICH_BAN:
        KICH_BAN[_ma]["pi"]["G1"].setdefault("sampling_design", _cm)
# 17/11/2026: cách thu thập PI chốt ở G1 (bật trục quy_trinh_du_lieu như đề tài thật BTM); tổng quan dùng dữ liệu đã
# công bố — không có quy trình thu thập trên người tham gia.
_THU_THAP = {
    "rct_nhi_phan": "Nghiên cứu viên đo huyết áp chuẩn hoá và ghi phiếu thu thập tại các lần khám theo lịch",
    "cat_ngang_mo_ta": "Phỏng vấn và đo huyết áp một lần tại phòng khám, ghi vào phiếu thu thập",
    "thuan_tap_phoi_nhiem": "Trích hồ sơ bệnh án điện tử theo phiếu trích dựng từ từ điển dữ liệu",
    # ba kịch bản dưới tuyển MỚI có phiếu đồng ý (G2 PROSPECTIVE_NEW_PARTICIPANTS) ⇒ khai theo quy ước «Thu mới: …» như
    # đề tài thật; bản đầu ghi «trích hồ sơ bệnh án» ⇒ trục mo_ta_thiet_ke TK-02 bắt đúng «sai lộ trình đồng thuận».
    "benh_chung": "Thu mới: phỏng vấn trực tiếp tiền sử dùng thuốc theo bộ câu hỏi chuẩn hoá cho cả nhóm bệnh và nhóm "
                  "chứng",
    "chan_doan": "Thu mới: người tham gia được lấy máu xét nghiệm AST, ALT, tiểu cầu và đo độ đàn hồi gan trong cùng "
                 "lần khám; nghiên cứu viên ghi phiếu thu thập",
    "mo_hinh_du_bao": "Thu mới: phỏng vấn và khám lúc vào nghiên cứu theo phiếu thu thập; theo dõi kết cục 12 tháng "
                      "qua các lần tái khám định kỳ",
}
for _ma, _tt in _THU_THAP.items():
    if _ma in KICH_BAN:
        KICH_BAN[_ma]["pi"]["G1"].setdefault("data_collection_method", _tt)


# ══════════════════════════════════════════════════════════════════════════════════════════════ tiện ích
def _bay_gio() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _doc_json(p: Path) -> Dict[str, Any]:
    try:
        v = json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return v if isinstance(v, dict) else {}


def _ghi_json(p: Path, obj: Any) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    tam = p.with_name(p.name + ".tam")
    tam.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    os.replace(tam, p)


def _thay_hom_nay(v: Any) -> Any:
    """Thay «<HOM_NAY>» bằng ngày chạy (ISO) trong cấu trúc lồng."""
    if isinstance(v, str):
        return datetime.now().date().isoformat() if v == "<HOM_NAY>" else v
    if isinstance(v, dict):
        return {k: _thay_hom_nay(x) for k, x in v.items()}
    if isinstance(v, list):
        return [_thay_hom_nay(x) for x in v]
    return v


def moi_truong(truc_tuyen: bool) -> Dict[str, str]:
    """Biến môi trường cho tiến trình con: UTF-8, không ghi __pycache__; ngoại tuyến thì bật nguồn giả lập."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("PYTEST_")}
    env.update({"PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1"})
    if truc_tuyen:
        env.pop("USE_MOCK_SOURCES", None)
    else:
        env["USE_MOCK_SOURCES"] = "true"
    return env


def chay_lenh(cmd: List[str], cwd: Path, env: Dict[str, str], timeout: int = 900) -> Dict[str, Any]:
    """Chạy một lệnh; trả {ma, ra, crash}. Crash = traceback trong đầu ra hoặc hết giờ/không chạy được."""
    try:
        p = subprocess.run(cmd, cwd=str(cwd), env=env, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"ma": 124, "ra": f"HẾT GIỜ > {timeout} s", "crash": True}
    except OSError as exc:
        return {"ma": 127, "ra": f"không chạy được: {exc}", "crash": True}
    ra = (p.stdout or "") + "\n" + (p.stderr or "")
    return {"ma": p.returncode, "ra": ra, "crash": _TRACEBACK in ra}


def dung_ban_sao(goc: Path, dich: Path) -> Path:
    """Chép phần mã cần cho run_pipeline sang `dich/repo` (không __pycache__) + `exports/` rỗng; trả gốc bản sao.

    Chép THẬT, không symlink: `run_pipeline.BASE = Path(__file__).resolve().parents[1]` — symlink bị resolve về repo
    thật thì mọi đầu ra rơi vào `exports/` thật."""
    repo = Path(dich) / "repo"
    repo.mkdir(parents=True, exist_ok=False)
    for ten in THU_MUC_CHEP:
        nguon = Path(goc) / ten
        if nguon.is_dir():
            shutil.copytree(nguon, repo / ten, ignore=BO_QUA_KHI_CHEP, symlinks=False)
    (repo / "exports").mkdir()
    if (repo / "tools" / "run_pipeline.py").resolve().parents[1] != repo.resolve():
        raise RuntimeError("bản sao không tách khỏi repo thật — dừng để không ghi vào exports/ thật")
    return repo


def lui_thoi_gian(thu_muc: Path, giay: float = GIAY_GIUA_HAI_LUOT_PI) -> int:
    """Lùi mtime (và atime) MỌI tệp trong `thu_muc` đúng `giay` giây, giữ nguyên thứ tự — mô phỏng thời gian trôi giữa
    hai lượt PI. Chỉ dùng cho đề tài TẠM của canary. Trả số tệp đã lùi."""
    n = 0
    goc = Path(thu_muc)
    if not goc.is_dir():
        return 0
    for p in goc.rglob("*"):
        if p.is_file() and not p.is_symlink():
            st = p.stat()
            os.utime(p, (st.st_atime - giay, st.st_mtime - giay))
            n += 1
    return n


def _de_tai_canary_trong_exports(goc: Path) -> List[str]:
    d = Path(goc) / "exports"
    if not d.is_dir():
        return []
    return sorted(p.name for p in d.iterdir() if p.name.startswith(TIEN_TO_DE_TAI))


# ══════════════════════════════════════════════════════════════════════════════════════════════ chấm sống
def cham_song(gate: str, study: str, out_dir: Path, repo_root: Path) -> Dict[str, Any]:
    """Chấm SỐNG một cổng (write=False) bằng bộ chấm của repo; trả báo cáo đủ tiêu chí, hoặc {"status": "LOI"}."""
    try:
        cs = importlib.import_module("cong_song")
        cs.xoa_dem()
        mod = importlib.import_module(f"{gate.lower()}_quality_gate")
        fn = getattr(mod, "evaluate_study")
        import inspect
        tham = inspect.signature(fn).parameters
        kw: Dict[str, Any] = {}
        if "out_dir" in tham:
            kw["out_dir"] = Path(out_dir)
        if "write" in tham:
            kw["write"] = False
        if "repo_root" in tham:
            kw["repo_root"] = Path(repo_root)
        with contextlib.redirect_stdout(io.StringIO()):
            bao = fn(study, **kw)
        return bao if isinstance(bao, dict) else {"status": "LOI", "ly_do": "bộ chấm không trả dict"}
    except Exception as exc:  # noqa: BLE001 — không chấm được ⇒ «LOI», không bao giờ là đạt
        return {"status": "LOI", "ly_do": f"{type(exc).__name__}: {str(exc)[:200]}"}


def _muc(status: Any) -> str:
    s = str(status or "").upper()
    if s.startswith("PASS"):
        return "PASS"
    if "BLOCK" in s:
        return "BLOCKED"
    if s.startswith("READY"):
        return "READY"
    if s.startswith("DRAFT"):
        return "DRAFT"
    return "KHONG_DO_DUOC"


def _tieu_chi(bao: Dict[str, Any], nhom: str) -> List[Dict[str, Any]]:
    v = bao.get(nhom)
    return [x for x in v if isinstance(x, dict)] if isinstance(v, list) else []


def _dau_van_tay_yeu_cau(bao: Dict[str, Any]) -> Optional[str]:
    """Dấu vân tay mà bộ chấm đòi PI chép (trong lời dặn của tiêu chí xác nhận chưa đạt)."""
    for row in _tieu_chi(bao, "human_criteria") + _tieu_chi(bao, "automatic_criteria"):
        if row.get("status") == "PASS":
            continue
        m = _DAU_VAN_TAY_RE.search(f"{row.get('action') or ''} {row.get('evidence') or ''}")
        if m:
            return m.group(1)
    return None


# ══════════════════════════════════════════════════════════════════════════════════════════════ PI giả lập
class GiaLap:
    """Chạy MỘT kịch bản trên bản sao tạm. `chay` và `cham` tiêm được để test không cần cổng thật."""

    def __init__(self, ma: str, kb: Dict[str, Any], repo: Path, truc_tuyen: bool, *,
                 chay: Callable[..., Dict[str, Any]] = chay_lenh,
                 cham: Callable[..., Dict[str, Any]] = cham_song,
                 nen_g0_dir: Path = NEN_G0_DIR):
        self.ma, self.kb, self.repo, self.truc_tuyen = ma, kb, Path(repo), truc_tuyen
        self.study = kb["study"]
        self.out = self.repo / "exports" / self.study
        self.chay, self.cham, self.nen_g0_dir = chay, cham, Path(nen_g0_dir)
        self.env = moi_truong(truc_tuyen)
        self.can_thiep: List[Dict[str, Any]] = []
        self.buoc: List[Dict[str, Any]] = []
        self.crash: List[str] = []
        self.ket: Optional[str] = None
        self.thiet_ke_may_suy: Optional[str] = None
        self.g0_do_duoc = False
        self.ghi_chu: List[str] = []
        self._da_tu_chay: set = set()
        self._da_soan_g0: set = set()

    # ── tiện ích tệp đề tài tạm
    def _meta(self) -> Dict[str, Any]:
        return _doc_json(self.out / "study_meta.json")

    def _ghi_meta(self, meta: Dict[str, Any]) -> None:
        _ghi_json(self.out / "study_meta.json", meta)

    def _cp(self, gate: str) -> Dict[str, Any]:
        return _doc_json(self.out / f"{gate}_checkpoint.json")

    def _ghi_can_thiep(self, cong: str, loai: str, ghi_chu: str) -> None:
        self.can_thiep.append({"vong": len(self.buoc), "cong": cong, "loai": loai,
                               "do_may": loai not in CAN_THIEP_DUNG_THIET_KE + CAN_THIEP_KHONG_DO_MAY,
                               "ghi_chu": ghi_chu})

    def _lenh(self, ten: str, *tham: str) -> List[str]:
        return [sys.executable, "-B", str(self.repo / "tools" / ten), *tham]

    def _chay(self, ten_buoc: str, cmd: List[str]) -> Dict[str, Any]:
        kq = self.chay(cmd, self.repo, self.env)
        dong = [x for x in str(kq.get("ra") or "").splitlines() if x.strip()]
        self.buoc.append({"buoc": ten_buoc, "ma": kq.get("ma"), "cuoi": dong[-4:]})
        if kq.get("crash"):
            self.crash.append(ten_buoc)
        return kq

    def chay_pipeline(self, topic: Optional[str] = None) -> Dict[str, Any]:
        tham = ["--study", self.study] + (["--topic", topic] if topic else [])
        kq = self._chay(f"pipeline#{len(self.buoc) + 1}", self._lenh("run_pipeline.py", *tham))
        if kq.get("ma") not in (0, 1) and not kq.get("crash"):
            self.crash.append(f"pipeline#{len(self.buoc)}:ma_thoat_{kq.get('ma')}")
        return kq

    # ── G0: tra mạng thật, hoặc nạp nền đã lưu
    def _g0_bi_chan_vi_nguon(self) -> bool:
        """G0 không dùng được vì NGUỒN (giả lập/mất mạng): guardrail R1B hoặc 0 PMID kèm lỗi truy vấn."""
        cp = self._cp("G0")
        loi = " ".join(str(x) for x in ((cp.get("guardrail") or {}).get("errors") or []))
        return "R1B" in loi or (not cp.get("n_pmids") and bool(cp.get("query_errors")))

    def _nen_g0(self) -> Path:
        """Nền G0 đã lưu của kịch bản. Kịch bản KẾ THỪA cùng đề tài/truy vấn (khoá `nen_g0_tu`, vd kịch bản chân thực)
        dùng lại nền của kịch bản gốc khi chưa có nền riêng — G0 không đổi vì chỉ phiếu thu thập thay."""
        rieng = self.nen_g0_dir / self.ma
        tu = self.kb.get("nen_g0_tu")
        return self.nen_g0_dir / str(tu) if tu and not rieng.is_dir() else rieng

    def luu_nen_g0(self) -> None:
        """Lưu tệp G0_* + topic/query_en (trạng thái «chờ PICO» sau khi đã khai query_en) để lượt ngoại tuyến dùng."""
        if self.kb.get("nen_g0_tu"):
            return  # kịch bản kế thừa dùng nền của kịch bản gốc — không ghi nền riêng (tránh thư mục trùng lặp)
        cp = self._cp("G0")
        if not cp.get("n_pmids") or self._g0_bi_chan_vi_nguon():
            return
        dich = self._nen_g0()
        if dich.exists():
            shutil.rmtree(dich)
        dich.mkdir(parents=True)
        # 19/11/2026: hai tệp do AGENT soạn (G0-T3/T4) không phải nền tra cứu — lượt sau soạn lại từ nền.
        cua_agent = {f"G0_TONG_HOP_BANG_CHUNG_{self.study}.json", f"G0_KHOANG_TRONG_{self.study}.json"}
        for p in self.out.iterdir():
            if p.is_file() and p.name.startswith("G0_") and p.name not in cua_agent:
                shutil.copy2(p, dich / p.name)
        meta = self._meta()
        self._luu_nhanh_day_du()
        _ghi_json(dich / "_nen.json", {"luc": _bay_gio(), "study": self.study, "topic": meta.get("topic"),
                                       "query_en": meta.get("query_en"), "base_query": cp.get("base_query")})

    def _luu_nhanh_day_du(self) -> None:
        """Trực tuyến: nhánh KHÔNG lọc vượt trần ⇒ tải đủ bản ghi cho agent G0-T3 (gia_lap_van_ban_tac_tu). Lỗi mạng
        chỉ ghi chú — tệp cũ giữ nguyên, lượt ngoại tuyến sau sẽ báo thiếu nếu không còn khớp."""
        import gia_lap_van_ban_tac_tu as VB  # noqa: PLC0415

        kl = VB.nhanh_khong_loc(_doc_json(self.out / "G0_pubmed_raw.json"))
        q, so_hit = str(kl.get("truy_van") or ""), kl.get("so_hit_that")
        if not q or not isinstance(so_hit, int) or so_hit <= int(kl.get("so_bai_lay_ve") or 0):
            return
        try:
            VB._ghi_json(VB.tep_day_du(self.nen_g0_dir, q), VB.tai_nhanh_day_du(q))
        except Exception as exc:  # noqa: BLE001 — mạng hỏng không được thành dữ kiện
            self.ghi_chu.append(f"chưa tải được nhánh không lọc đầy đủ ({type(exc).__name__})")

    def nap_nen_g0(self) -> bool:
        nen = self._nen_g0()
        thong_tin = _doc_json(nen / "_nen.json")
        if not thong_tin or thong_tin.get("study") != self.study:
            return False
        self.out.mkdir(parents=True, exist_ok=True)
        for p in self.out.iterdir():
            if p.is_file() and p.name.startswith("G0_"):
                p.unlink()
        for p in nen.iterdir():
            if p.is_file() and p.name.startswith("G0_"):
                shutil.copy2(p, self.out / p.name)
        meta = self._meta()
        meta.update({"title": thong_tin.get("topic"), "topic": thong_tin.get("topic"),
                     "query_en": thong_tin.get("query_en")})
        self._ghi_meta(meta)
        self.ghi_chu.append(f"G0 dùng nền lưu lúc {thong_tin.get('luc')} — tra PubMed KHÔNG đo lượt này")
        return True

    def khoi_dong(self) -> bool:
        """Lượt đầu: chủ đề → G0. Trả False nếu không có nền G0 dùng được (kịch bản không đo được)."""
        if self.truc_tuyen:
            self.chay_pipeline(self.kb["topic"])
            if not self._g0_bi_chan_vi_nguon():
                self.g0_do_duoc = True
                return True
            self.ghi_chu.append("G0 không đo được (mạng/nguồn lỗi lượt này)")
        else:
            self.ghi_chu.append("G0 không đo được ngoại tuyến (nguồn giả lập bị guardrail R1B chặn — đúng luật)")
        if not self.nap_nen_g0():
            self.ghi_chu.append("chưa có nền G0 từ lượt trực tuyến ⇒ G1–G4 không đo được")
            return False
        self.chay_pipeline()
        return True

    # ── một bước PI
    def _noi_dung_da_dien(self, gate: str) -> bool:
        gp = (self._meta().get("gate_params") or {}).get(gate) or {}
        mong = _thay_hom_nay(self.kb["pi"].get(gate) or {})
        return all(gp.get(k) == v for k, v in mong.items())

    def _dien_noi_dung(self, gate: str) -> None:
        meta = self._meta()
        gp = meta.setdefault("gate_params", {}).setdefault(gate, {})
        gp.update(copy.deepcopy(_thay_hom_nay(self.kb["pi"][gate])))
        meta.setdefault("gia_lap_pi_dien", []).append({"luc": _bay_gio(), "cong": gate, "loai": "dien_noi_dung",
                                                       "nhan": NHAN})
        self._ghi_meta(meta)

    def _xac_nhan(self, gate: str, dau: str) -> None:
        meta = self._meta()
        gp = meta.setdefault("gate_params", {}).setdefault(gate, {})
        gp.update(copy.deepcopy(self.kb["xac_nhan"].get(gate) or {}))
        gp.update({"reviewed_at": _bay_gio(), "dau_van_tay_chot": dau})
        meta.setdefault("gia_lap_pi_dien", []).append({"luc": _bay_gio(), "cong": gate,
                                                       "loai": "xac_nhan_dau_van_tay", "nhan": NHAN})
        self._ghi_meta(meta)

    def _tu_chay_cong(self, gate: str) -> None:
        """PI tự chạy cổng (pipeline không chạy lại dù đầu vào đổi — loại N4) với tham số khôi phục như pipeline."""
        rp = importlib.import_module("run_pipeline")
        tham = rp._recover_params(gate, self.out, self._meta())
        self._chay(f"tu_chay_{gate}", self._lenh(f"run_{gate.lower()}_auto.py", "--study", self.study, *tham))

    def mot_buoc_pi(self) -> Optional[str]:
        """PI xử lý cổng mềm đầu tiên chưa đạt. Trả mã cổng vừa xử lý; None nếu cổng mềm đã đạt hết; đặt self.ket nếu
        PI không còn việc nào làm được (kẹt)."""
        cp0 = self._cp("G0")
        q_pi = self.kb.get("query_en")
        if q_pi and cp0 and str(cp0.get("base_query") or "").strip() != q_pi.strip():
            meta = self._meta()
            if meta.get("query_en") != q_pi:
                meta["query_en"] = q_pi
                self._ghi_meta(meta)
                self._ghi_can_thiep("G0", "khai_query_en", "máy dịch chủ đề tiếng Việt thành truy vấn lạc đề (K4)")
                return "G0"
        if cp0 and cp0.get("n_pmids") and self._soan_van_ban_g0():
            return "G0"
        for gate in CONG_MEM:
            if gate not in self.kb["pi"]:
                continue
            if gate == "G3" and self.kb.get("bien_so") and self._cp("G3"):
                if not ((self.out / "_bo-bien-rieng.csv").exists()
                        and (self.out / "_ma-tran-muc-tieu-bien.csv").exists()):
                    self._dung_bo_bien_ma_tran()
                    self._ghi_can_thiep("G3", "dung_bo_bien_ma_tran", "G3-T2: agent bien-so-nghien-cuu dựng bộ biến "
                                        "+ ma trận mục tiêu–biến (G3-AUTO-19)")
                    return "G3"
                if not (self.out / f"G3_BO_BIEN_SO_{self.study}.md").exists():
                    self._chay("soan_bang_bien_g3", self._lenh("bang_bien_g3.py", "soan", "--study", self.study,
                                                               "--ghi"))
                    self._ghi_can_thiep("G3", "soan_bang_bien_g3", "G3-T2: agent bien-so-nghien-cuu soạn "
                                        "G3_BO_BIEN_SO_<mã>.md cho PI duyệt (tools/bang_bien_g3.py)")
                    return "G3"
                if self._duyet_bang_bien_g3():
                    return "G3"
            bao = self.cham(gate, self.study, self.out, self.repo)
            muc = _muc(bao.get("status"))
            if gate == "G1" and self.thiet_ke_may_suy is None and self._cp("G1"):
                d = self._cp("G1").get("design")
                self.thiet_ke_may_suy = (d.get("internal_code") if isinstance(d, dict) else d) or "?"
            if muc == "PASS":
                continue
            if not self._cp(gate) and gate != "G0":
                self.ket = f"{gate}:chua_chay"  # cổng mềm chưa từng chạy — pipeline dừng sớm hơn
                return None
            if muc == "BLOCKED" and bao.get("status") != "LOI" and self._noi_dung_da_dien(gate) and \
                    gate in self._da_tu_chay:
                self.ket = f"{gate}:{','.join(self._chua_dat(bao))}"
                return None
            if not self._noi_dung_da_dien(gate):
                lan = sum(1 for c in self.can_thiep if c["cong"] == gate and c["loai"] == "dien_noi_dung")
                self._dien_noi_dung(gate)
                self._ghi_can_thiep(gate, "dien_noi_dung", "nội dung kịch bản" + (" (điền LẠI)" if lan else ""))
                return gate
            auto_chua_dat = [r["id"] for r in _tieu_chi(bao, "automatic_criteria") if r.get("status") != "PASS"]
            if auto_chua_dat and gate != "G0" and gate not in self._da_tu_chay:
                self._da_tu_chay.add(gate)
                self._tu_chay_cong(gate)
                sau = [r["id"] for r in _tieu_chi(self.cham(gate, self.study, self.out, self.repo),
                                                  "automatic_criteria") if r.get("status") != "PASS"]
                if sorted(sau) != sorted(auto_chua_dat):
                    self._ghi_can_thiep(gate, "tu_chay_cong", "pipeline không chạy lại cổng dù đầu vào đã đổi; tiêu "
                                        f"chí máy chưa đạt: {', '.join(auto_chua_dat[:4])}")
                else:
                    self._ghi_can_thiep(gate, "tu_chay_cong_khong_doi", "tự chạy cổng KHÔNG đổi tiêu chí máy chưa "
                                        f"đạt ({', '.join(auto_chua_dat[:4])}) — không phải lỗi «không chạy lại»")
                return gate
            dau = _dau_van_tay_yeu_cau(bao)
            gp = (self._meta().get("gate_params") or {}).get(gate) or {}
            if dau and dau != gp.get("dau_van_tay_chot"):
                self._xac_nhan(gate, dau)
                self._ghi_can_thiep(gate, "xac_nhan_dau_van_tay", f"chép dấu {dau} cổng in ra")
                return gate
            self.ket = f"{gate}:{','.join(self._chua_dat(bao)) or bao.get('status')}"
            return None
        return None

    def _soan_van_ban_g0(self) -> bool:
        """G0-T3 `tong-quan-y-van` + G0-T4 `khoang-trong-nghien-cuu` (19/11/2026): soạn hai tệp đề xuất từ nền G0 hiện
        hành (`gia_lap_van_ban_tac_tu`) rồi dựng lại A1 không tra lại PubMed — như đề tài thật: agent soạn TRƯỚC khi PI
        chốt G0 (danh mục đọc bổ sung vào dấu vân tay G0). Chỉ soạn khi tệp vắng hoặc không còn đạt bộ kiem của hệ; mỗi
        tập PMID nền soạn MỘT lần — soạn xong vẫn lỗi là khiếm khuyết thật, không lặp vô hạn. True khi vừa soạn."""
        import g0_tong_hop as GT  # noqa: PLC0415
        import gia_lap_van_ban_tac_tu as VB  # noqa: PLC0415

        cp = self._cp("G0")
        pr = cp.get("pubmed_results") if isinstance(cp.get("pubmed_results"), dict) else {}
        nen = sorted(str(p) for p in pr.get("all_pmids") or cp.get("pmids_verified") or [])
        khoa = (str(cp.get("base_query") or ""), tuple(nen))
        if khoa in self._da_soan_g0:
            return False
        kl = VB.nhanh_khong_loc(_doc_json(self.out / "G0_pubmed_raw.json"))
        th, loi_th = GT.doc(self.out, GT.TEP_TONG_HOP, self.study)
        kt, loi_kt = GT.doc(self.out, GT.TEP_KHOANG_TRONG, self.study)
        can_th = th is None or bool(loi_th) or bool(GT.kiem_tong_hop(th, nen, kl or None))
        can_kt = kt is None or bool(loi_kt) or bool(GT.kiem_khoang_trong(kt))
        if not (can_th or can_kt):
            return False
        self._da_soan_g0.add(khoa)
        hom_nay = datetime.now().date()
        kho = os.environ.get("GIA_LAP_A12_KHO", "").strip()
        if can_th:
            _ghi_json(self.out / GT.TEP_TONG_HOP.format(study=self.study),
                      VB.soan_tong_hop(self.out, self.study, self.nen_g0_dir, hom_nay, Path(kho) if kho else None,
                                       VB.pmid_trong(self.kb.get("pi"), self._meta().get("gate_params"))))
        if can_kt:
            g0 = {**(self.kb.get("pi", {}).get("G0") or {}),
                  **((self._meta().get("gate_params") or {}).get("G0") or {})}
            _ghi_json(self.out / GT.TEP_KHOANG_TRONG.format(study=self.study),
                      VB.soan_khoang_trong(self.out, self.study, {"gate_params": {"G0": g0}}, hom_nay))
        self._chay("dung_lai_a1", self._lenh("run_g0_auto.py", "--study", self.study, "--dung-lai-a1"))
        self._ghi_can_thiep("G0", "soan_van_ban_g0", "G0-T3/T4: agent tong-quan-y-van + khoang-trong-nghien-cuu soạn "
                            "tổng hợp bằng chứng và khoảng trống (gia_lap_van_ban_tac_tu) rồi dựng lại A1")
        return True

    def _duyet_bang_bien_g3(self) -> bool:
        """PI GIẢ LẬP (đề tài tạm ZZCANARY-) đọc bảng G3 rồi ghi xác nhận gắn dấu nội dung — True khi vừa ghi."""
        import bang_bien_g3 as BB  # noqa: PLC0415

        st = BB.trang_thai(self.out, self.study, self._meta())
        if st["la_nguon_nguoi_duyet"] or not st["dau_hien_tai"]:
            return False
        meta = self._meta()
        meta.setdefault("gate_params", {}).setdefault("G3", {})[BB.KHOA_DUYET] = {
            "reviewed_at": _bay_gio(), "dau_van_tay": st["dau_hien_tai"]}
        meta.setdefault("gia_lap_pi_dien", []).append({"luc": _bay_gio(), "cong": "G3", "loai": "duyet_bang_bien_g3",
                                                       "nhan": NHAN})
        self._ghi_meta(meta)
        self._ghi_can_thiep("G3", "duyet_bang_bien_g3", f"PI đọc G3_BO_BIEN_SO và ghi dấu {st['dau_hien_tai']}")
        return True

    def _dung_bo_bien_ma_tran(self) -> None:
        """Ghi `_bo-bien-rieng.csv` (REDCap 18 cột) + `_ma-tran-muc-tieu-bien.csv` của kịch bản vào đề tài TẠM."""
        import csv  # noqa: PLC0415

        bs = self.kb["bien_so"]
        # 17/11/2026 (kịch bản chân thực): `meta_bien` = {tên: {form, nhanh, bat_buoc, ghi_chu, phan}} — phiếu nhiều
        # biểu mẫu, logic nhánh, câu không bắt buộc (calc), tiêu đề phần như từ điển REDCap của đề tài thật. Vắng ⇒
        # một biểu mẫu «phieu», mọi câu bắt buộc như cũ.
        meta_bien = bs.get("meta_bien") or {}
        with (self.out / "_bo-bien-rieng.csv").open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(COT_BO_BIEN), lineterminator="\n")
            w.writeheader()
            for ten, loai, nhan, lua, kt, lo, hi in bs["bo_bien"]:
                m = meta_bien.get(ten) or {}
                w.writerow({"Variable / Field Name": ten, "Form Name": m.get("form") or "phieu",
                            "Section Header": m.get("phan") or "", "Field Type": loai, "Field Label": nhan,
                            "Choices, Calculations, OR Slider Labels": lua, "Field Note": m.get("ghi_chu") or "",
                            "Text Validation Type OR Show Slider Number": kt, "Text Validation Min": lo,
                            "Text Validation Max": hi, "Branching Logic (Show field only if...)": m.get("nhanh") or "",
                            "Required Field?": "y" if m.get("bat_buoc", True) else "n"})
        with (self.out / "_ma-tran-muc-tieu-bien.csv").open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(list(COT_MA_TRAN))
            for r in bs["ma_tran"]:
                w.writerow([*r, NHAN])

    @staticmethod
    def _chua_dat(bao: Dict[str, Any]) -> List[str]:
        return [r["id"] for r in _tieu_chi(bao, "automatic_criteria") + _tieu_chi(bao, "human_criteria")
                if r.get("status") != "PASS" and r.get("id")][:6]

    # ── đo cuối kịch bản
    def cong_dung(self) -> Tuple[Optional[str], Dict[str, str]]:
        """(cổng pipeline dừng, trạng thái cuối từng cổng theo báo cáo pipeline lượt cuối)."""
        bc = _doc_json(self.out / "pipeline_run_report.json")
        cuoi: Dict[str, str] = {}
        for r in bc.get("gate_results") or []:
            if isinstance(r, dict) and r.get("gate"):
                cuoi[str(r["gate"])] = str(r.get("status"))
        for g in sorted(cuoi, key=lambda x: int(x[1:]) if x[1:].isdigit() else 99):
            if cuoi[g] in TRANG_THAI_DUNG_PIPELINE:
                return g, cuoi
        return None, cuoi

    def kiem_chi_tiet(self) -> Dict[str, Any]:
        kq = self._chay("kiem_chi_tiet", self._lenh("kiem_chi_tiet_he_nghien_cuu.py", "--study", self.study,
                                                    "--khong-canary"))
        bao = _doc_json(self.out / "KIEM_CHI_TIET_report.json")
        if not bao:
            return {"do_duoc": False, "ma": kq.get("ma")}
        return {"do_duoc": True, "ma": kq.get("ma"), **dem_kiem_chi_tiet(bao)}

    def _luu_nen_neu_dung_luc(self) -> None:
        """Trực tuyến: lưu nền G0 khi G0 đã tra bằng đúng truy vấn PI khai (hoặc kịch bản không cần query_en)."""
        if not (self.truc_tuyen and self.g0_do_duoc):
            return
        q_pi = (self.kb.get("query_en") or "").strip()
        if not q_pi or str(self._cp("G0").get("base_query") or "").strip() == q_pi:
            self.luu_nen_g0()

    def chay_kich_ban(self) -> Dict[str, Any]:
        if not self.khoi_dong():
            return self.ket_qua(do_duoc=False)
        self._luu_nen_neu_dung_luc()
        for _ in range(SO_VONG_TOI_DA):
            if self.crash:
                break
            lui_thoi_gian(self.out)  # PI thật không làm lượt kế tiếp trong vòng 120 s (xem GIAY_GIUA_HAI_LUOT_PI)
            cong = self.mot_buoc_pi()
            if cong is None:
                break
            self.chay_pipeline()
            if self.can_thiep and self.can_thiep[-1]["loai"] == "khai_query_en":
                if self.truc_tuyen and self._g0_bi_chan_vi_nguon():
                    # Tra lần đầu được nhưng tra LẠI theo query_en hỏng (NCBI chặn/mất mạng giữa chừng) — lỗi mạng
                    # không được thành «khiếm khuyết mới»: G0 không đo được, dùng nền cũ như lượt ngoại tuyến.
                    self.g0_do_duoc = False
                    self.ghi_chu.append("G0 không đo được (mạng/nguồn lỗi khi tra lại theo query_en PI khai)")
                    if not self.nap_nen_g0():
                        self.ghi_chu.append("chưa có nền G0 từ lượt trực tuyến ⇒ G1–G4 không đo được")
                        return self.ket_qua(do_duoc=False)
                    self.chay_pipeline()
                    continue
                self._luu_nen_neu_dung_luc()
        else:
            self.ket = self.ket or f"qua_{SO_VONG_TOI_DA}_vong"
        if self.truc_tuyen and self.g0_do_duoc and not (self._nen_g0() / "_nen.json").is_file():
            self.ghi_chu.append("chưa lưu được nền G0 (G0 chưa tới trạng thái chờ PICO sau query_en)")
        return self.ket_qua(do_duoc=True)

    def ket_qua(self, do_duoc: bool) -> Dict[str, Any]:
        song = {g: _muc(self.cham(g, self.study, self.out, self.repo).get("status"))
                for g in ("G0", "G1", "G2", "G3", "G4")} if do_duoc and self.out.is_dir() else {}
        dung, cuoi = self.cong_dung() if do_duoc else (None, {})
        kct = self.kiem_chi_tiet() if do_duoc and self.out.is_dir() else {"do_duoc": False}
        kq = {
            "ma": self.ma, "study": self.study, "thiet_ke": self.kb["thiet_ke"], "mo_ta": self.kb.get("mo_ta"),
            "do_duoc": do_duoc, "g0_do_duoc": self.g0_do_duoc, "ghi_chu": self.ghi_chu,
            "can_thiep": self.can_thiep, "so_can_thiep": len(self.can_thiep),
            "so_can_thiep_do_may": sum(1 for c in self.can_thiep if c["do_may"]),
            "cong_dung": dung, "cong_dung_mong_doi": self.kb.get("cong_dung_mong_doi"),
            "trang_thai_pipeline_cuoi": cuoi, "cham_song_cuoi": song, "thiet_ke_may_suy": self.thiet_ke_may_suy,
            "ket": self.ket, "crash": self.crash, "kiem_chi_tiet": kct, "buoc": self.buoc,
        }
        kq["khiem_khuyet"] = khiem_khuyet_kich_ban(kq)
        return kq


def dem_kiem_chi_tiet(bao: Dict[str, Any]) -> Dict[str, Any]:
    """Đếm 🟢/🟡/🔴/⚪ của KIEM_CHI_TIET_report.json (khoá `tong`) và liệt kê ô đỏ dạng «cổng/trục» (khoá `muc`)."""
    ky = {"🟢": "xanh", "🟡": "vang", "🔴": "do", "⚪": "trang"}
    muc = [m for m in (bao.get("muc") or []) if isinstance(m, dict)]
    tong = bao.get("tong") if isinstance(bao.get("tong"), dict) else {}
    if tong:
        dem = {k: int(tong.get(k) or 0) for k in ky.values()}
    else:
        dem = {k: sum(1 for m in muc if ky.get(str(m.get("muc"))) == k) for k in ky.values()}
    o_do = sorted({f"{m.get('cong')}/{m.get('truc')}" for m in muc if m.get("muc") == "🔴"})
    return {**dem, "o_do": o_do}


def khiem_khuyet_kich_ban(kq: Dict[str, Any]) -> List[str]:
    """Khoá khiếm khuyết ổn định của một kịch bản (so được giữa các lần chạy)."""
    if not kq.get("do_duoc"):
        return []
    ma, ds = kq["ma"], set()
    for c in kq.get("can_thiep") or []:
        if c.get("do_may"):
            ds.add(f"{ma}:can_thiep_do_may:{c['cong']}:{c['loai']}")
    dem: Dict[Tuple[str, str], int] = {}
    for c in kq.get("can_thiep") or []:
        if not c.get("do_may"):
            dem[(c["cong"], c["loai"])] = dem.get((c["cong"], c["loai"]), 0) + 1
    for (cong, loai), n in dem.items():
        if n > 1:
            ds.add(f"{ma}:can_thiep_lap:{cong}:{loai}")
    for b in kq.get("crash") or []:
        buoc = re.sub(r"#\d+", "", str(b))  # bỏ số thứ tự lượt để khoá ổn định giữa các lần chạy
        ds.add(f"{ma}:crash:{buoc}")
    if kq.get("ket"):
        ds.add(f"{ma}:ket:{kq['ket']}")
    if kq.get("cong_dung") != kq.get("cong_dung_mong_doi"):
        ds.add(f"{ma}:dung_sai:{kq.get('cong_dung') or 'khong_dung'}")
    tk = kq.get("thiet_ke_may_suy")
    if tk and tk != kq.get("thiet_ke"):
        ds.add(f"{ma}:thiet_ke_may_suy_sai:{tk}")
    for g in CONG_CUNG_TRUOC_G5:
        if (kq.get("cham_song_cuoi") or {}).get(g) == "PASS":
            ds.add(f"{ma}:cong_cung_dat_khi_chua_ky:{g}")
    for g in CONG_MEM:
        if (kq.get("cham_song_cuoi") or {}).get(g) not in ("PASS", None):
            ds.add(f"{ma}:cong_mem_chua_dat:{g}")
    for o in (kq.get("kiem_chi_tiet") or {}).get("o_do") or []:
        ds.add(f"{ma}:kiem_chi_tiet_do:{o}")
    return sorted(ds)


# ══════════════════════════════════════════════════════════════════════════════════════════════ pytest
def chay_pytest(goc: Path, thu_muc_tam: Path, *, chay: Callable[..., Dict[str, Any]] = chay_lenh,
                muc_tieu: Tuple[str, ...] = KIEM_PYTEST) -> Dict[str, Any]:
    """Chạy test đầu–cuối sẵn có (khoá giả conftest); đọc kết quả từng test từ junit XML."""
    junit = Path(thu_muc_tam) / "junit-gia-lap.xml"
    env = moi_truong(truc_tuyen=False)
    env.pop("USE_MOCK_SOURCES", None)  # để conftest tự quyết như lượt pytest thường
    cmd = [sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", *muc_tieu,
           f"--junitxml={junit}"]
    kq = chay(cmd, Path(goc), env, 3600)
    if not junit.is_file():
        return {"do_duoc": False, "ly_do": f"không có junit (mã {kq.get('ma')})", "khiem_khuyet": []}
    try:
        goc_xml = ET.parse(junit).getroot()
    except ET.ParseError as exc:
        return {"do_duoc": False, "ly_do": f"junit hỏng: {exc}", "khiem_khuyet": []}
    dat, hong, bo_qua = [], [], []
    for tc in goc_xml.iter("testcase"):
        ten = tc.get("name") or "?"
        if tc.find("failure") is not None or tc.find("error") is not None:
            hong.append(ten)
        elif tc.find("skipped") is not None:
            bo_qua.append(ten)
        else:
            dat.append(ten)
    do_duoc = bool(dat or hong)
    return {"do_duoc": do_duoc, "ma": kq.get("ma"), "dat": len(dat), "hong": hong, "bo_qua": bo_qua,
            "ly_do": None if do_duoc else "mọi test bị bỏ qua",
            "khiem_khuyet": sorted(f"pytest:hong:{t}" for t in hong)}


# ══════════════════════════════════════════════════════════════════════════════════════════════ so sánh + state
def thuoc_phan(khoa: str, phan: str) -> bool:
    """Khoá khiếm khuyết `khoa` có thuộc phần `phan` (một mục của «không đo được») không.

    `phan` có hai dạng:
    - «<kịch bản>» hoặc «pytest» — cả phần: mọi khoá bắt đầu bằng «<phan>:».
    - «<kịch bản>.<cổng>» (vd «rct_nhi_phan.G0») — chỉ khoá của kịch bản đó PHỤ THUỘC cổng: có đoạn «:<cổng>:» hoặc
      «:<cổng>/», hoặc kết thúc bằng «:<cổng>» (vd «…:can_thiep_do_may:G0:khai_query_en», «…:kiem_chi_tiet_do:G0/①»,
      «…:cong_mem_chua_dat:G0»). Lượt G0 dùng nền cũ thì K4 không thể xuất hiện — vắng K4 không phải bằng chứng đã sửa.
    """
    if "." in phan:
        ma, cong = phan.split(".", 1)
        return khoa.startswith(f"{ma}:") and (f":{cong}:" in khoa or f":{cong}/" in khoa or khoa.endswith(f":{cong}"))
    return khoa.startswith(f"{phan}:")


def so_sanh(hien_tai: List[str], truoc: Optional[List[str]], khong_do: List[str]) -> Dict[str, List[str]]:
    """moi = có bây giờ mà lần trước không có; da_het = lần trước có, nay không có VÀ phần đó đo được lượt này.
    Khoá của phần không đo được lượt này (cả kịch bản, pytest, hoặc phần phụ thuộc một cổng — xem `thuoc_phan`) được
    giữ lại cho lần sau (`giu_lai`), không bao giờ báo «đã hết» (§0.2: «không đo được» ≠ «ổn»)."""
    truoc_set = set(truoc or [])
    hien = set(hien_tai)

    def _thuoc_phan_khong_do(k: str) -> bool:
        return any(thuoc_phan(k, p) for p in khong_do)

    giu_lai = sorted(k for k in truoc_set if _thuoc_phan_khong_do(k))
    return {"moi": sorted(hien - truoc_set), "da_het": sorted(k for k in truoc_set - hien
                                                              if not _thuoc_phan_khong_do(k)),
            "giu_lai": giu_lai}


def doc_state(p: Path) -> Tuple[Dict[str, Any], Optional[str]]:
    """(state, lỗi). Tệp vắng = state rỗng hợp lệ; tệp hỏng ⇒ lỗi (không ghi đè — dời sang .hong-<thời điểm>)."""
    if not Path(p).exists():
        return {}, None
    try:
        v = json.loads(Path(p).read_text(encoding="utf-8"))
        if not isinstance(v, dict):
            raise ValueError("không phải object")
        return v, None
    except (OSError, ValueError) as exc:
        return {}, f"không đọc được mốc lần trước ({type(exc).__name__}: {str(exc)[:120]})"


def ma_thoat(moi: List[str], khong_do: List[str]) -> int:
    if moi:
        return 1
    if khong_do:
        return 2
    return 0


def tong_hop(kich_ban: Dict[str, Dict[str, Any]], pytest_kq: Optional[Dict[str, Any]], state_cu: Dict[str, Any],
             che_do: str, loi_state: Optional[str], ro_ri: List[str],
             du_kien: Optional[List[str]] = None) -> Dict[str, Any]:
    """Gộp kết quả lượt này, so với mốc cùng chế độ, tính mã thoát.

    `du_kien` = mọi kịch bản LẼ RA phải đo (mặc định: cả `KICH_BAN`). Kịch bản không chạy lượt này (`--kich-ban` chọn
    tập con) là «không đo được»: khoá cũ của nó được giữ, mã thoát là 2 chứ không phải 0 (không báo «đã hết» giả)."""
    khiem: List[str] = []
    khong_do: List[str] = []
    khong_chay = [ma for ma in (list(KICH_BAN) if du_kien is None else du_kien) if ma not in kich_ban]
    khong_do += khong_chay
    for ma, kq in kich_ban.items():
        if not kq.get("do_duoc"):
            khong_do.append(ma)
        else:
            khiem += kq.get("khiem_khuyet") or []
            if not kq.get("g0_do_duoc"):
                khong_do.append(f"{ma}.G0")
    if pytest_kq is None:
        khong_do.append("pytest")
    elif not pytest_kq.get("do_duoc"):
        khong_do.append("pytest")
    else:
        khiem += pytest_kq.get("khiem_khuyet") or []
    for d in ro_ri:
        khiem.append(f"he:ro_ri_exports_that:{d}")
    khiem = sorted(set(khiem))
    truoc = ((state_cu.get("theo_che_do") or {}).get(che_do) or {}).get("khiem_khuyet")
    # «rct_nhi_phan» không đo được ⇒ giữ mọi khoá của kịch bản; «rct_nhi_phan.G0» ⇒ chỉ giữ khoá phụ thuộc G0 (K4…),
    # khoá G1–G4 của kịch bản vẫn so bình thường vì phần đó đo được.
    ss = so_sanh(khiem, truoc, khong_do)
    theo_che_do = dict(state_cu.get("theo_che_do") or {})
    theo_che_do[che_do] = {"luc": _bay_gio(), "khiem_khuyet": sorted(set(khiem) | set(ss["giu_lai"]))}
    ma = ma_thoat(ss["moi"], khong_do)
    return {
        "phien_ban": PHIEN_BAN, "luc": _bay_gio(), "che_do": che_do, "ma_thoat": ma,
        "lan_dau": truoc is None, "loi_moc": loi_state,
        "khiem_khuyet": khiem, "moi": ss["moi"], "da_het": ss["da_het"], "khong_do_duoc": khong_do,
        "giu_lai": ss["giu_lai"], "khong_chay_luot_nay": khong_chay,
        "kich_ban": {k: {x: v for x, v in kq.items() if x != "buoc"} for k, kq in kich_ban.items()},
        "chi_tiet_buoc": {k: kq.get("buoc") for k, kq in kich_ban.items()},
        "pytest": pytest_kq,
        "phu_thiet_ke": {"pipeline": sorted({kq.get("thiet_ke") for kq in kich_ban.values() if kq.get("do_duoc")}),
                         "pytest_g10": list(THIET_KE_TAM) if pytest_kq and pytest_kq.get("do_duoc") else []},
        "theo_che_do": theo_che_do,
        "disclaimer": "Chỉ đo và báo trên đề tài TỔNG HỢP trong thư mục tạm. Cần bác sĩ kiểm chứng.",
    }


# ══════════════════════════════════════════════════════════════════════════════════════════════ in + main
def _mo_ta_loi(exc: BaseException) -> str:
    return f"({type(exc).__name__}: {str(exc)[:200]})"


def kich_ban_loi_noi_bo(ma: str, exc: BaseException) -> Dict[str, Any]:
    """Kết quả của kịch bản bị lỗi nội bộ canary giữa chừng: «không đo được» (khoá cũ giữ nguyên), không sinh khoá."""
    kb = KICH_BAN.get(ma) or {}
    return {"ma": ma, "study": kb.get("study"), "thiet_ke": kb.get("thiet_ke"), "mo_ta": kb.get("mo_ta"),
            "do_duoc": False, "g0_do_duoc": False, "khiem_khuyet": [], "loi_noi_bo": _mo_ta_loi(exc),
            "ghi_chu": [f"lỗi nội bộ của canary {_mo_ta_loi(exc)} — không phải khiếm khuyết của hệ; sửa canary"],
            "buoc": []}


def in_tom_tat(bc: Dict[str, Any]) -> None:
    nhan_ma = {0: "🟢 không có khiếm khuyết mới", 1: "🔴 CÓ KHIẾM KHUYẾT MỚI", 2: "⚪ có phần KHÔNG ĐO ĐƯỢC"}
    print(f"\n🧪 GIẢ LẬP ĐỊNH KỲ hệ nghiên cứu — chế độ {bc['che_do']} — {bc['luc']}")
    for ma, kq in bc["kich_ban"].items():
        if not kq.get("do_duoc"):
            print(f"  ⚪ {ma} ({kq.get('thiet_ke')}): KHÔNG ĐO ĐƯỢC — {'; '.join(kq.get('ghi_chu') or [])}")
            continue
        dung = kq.get("cong_dung")
        dau = "✅" if dung == kq.get("cong_dung_mong_doi") else "❌"
        kct = kq.get("kiem_chi_tiet") or {}
        print(f"  • {ma} ({kq.get('thiet_ke')}; máy suy: {kq.get('thiet_ke_may_suy') or '—'}): "
              f"{kq['so_can_thiep']} can thiệp như PI ({kq['so_can_thiep_do_may']} do máy) · dừng ở {dung or '—'} "
              f"{dau} (đúng thiết kế: {kq.get('cong_dung_mong_doi')}) · crash {len(kq.get('crash') or [])}"
              + (f" · kiem_chi_tiet 🟢{kct.get('xanh')} 🟡{kct.get('vang')} 🔴{kct.get('do')}"
                 if kct.get("do_duoc") else " · kiem_chi_tiet ⚪"))
        for c in kq.get("can_thiep") or []:
            print(f"      {'🤖' if c['do_may'] else '👤'} {c['cong']} {c['loai']} — {c['ghi_chu']}")
        for g in kq.get("ghi_chu") or []:
            print(f"      ⚪ {g}")
        if kq.get("ket"):
            print(f"      ⛔ PI kẹt: {kq['ket']}")
    pk = bc.get("pytest")
    if pk is None:
        print("  ⚪ pytest đầu–cuối: bỏ qua (--bo-pytest)")
    elif not pk.get("do_duoc"):
        print(f"  ⚪ pytest đầu–cuối: KHÔNG ĐO ĐƯỢC — {pk.get('ly_do')}")
    else:
        print(f"  • pytest đầu–cuối (khoá giả): {pk['dat']} đạt · {len(pk['hong'])} hỏng"
              + (f" — {', '.join(pk['hong'])}" if pk["hong"] else ""))
    if bc.get("loi_moc"):
        print(f"  🟠 {bc['loi_moc']} — tệp cũ đã dời sang .hong-*; lượt này coi như chưa có mốc")
    if bc.get("lan_dau"):
        print("  ℹ️ Lần đầu ở chế độ này: chưa có mốc — mọi khiếm khuyết đang có tính là MỚI.")
    for k in bc["moi"]:
        print(f"  🆕 {k}")
    for k in bc["da_het"]:
        print(f"  ✔️ đã hết: {k}")
    if bc["khong_do_duoc"]:
        kc = set(bc.get("khong_chay_luot_nay") or [])
        nhan = [f"{k} (không chạy lượt này)" if k in kc else k for k in bc["khong_do_duoc"]]
        print(f"  ⚪ không đo được: {', '.join(nhan)}")
    if bc.get("giu_lai"):
        print(f"  ⏸ giữ nguyên {len(bc['giu_lai'])} khoá cũ của phần không đo được (không tính «đã hết»)")
    print(f"  → {nhan_ma[bc['ma_thoat']]} (mã {bc['ma_thoat']}). {bc['disclaimer']}")


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Giả lập định kỳ hệ nghiên cứu G0→G10 (canary tháng) — chỉ đo và báo.")
    ap.add_argument("--truc-tuyen", action="store_true",
                    help="G0 tra PubMed/ClinicalTrials.gov thật (mặc định ngoại tuyến: dùng nền G0 đã lưu)")
    ap.add_argument("--kich-ban", action="append", choices=sorted(KICH_BAN),
                    help="Chỉ chạy kịch bản này (lặp được); mặc định chạy hết")
    ap.add_argument("--bo-pytest", action="store_true", help="Bỏ phần test đầu–cuối pytest (≈2 phút)")
    ap.add_argument("--khong-ghi", action="store_true", help="Không ghi state (chỉ in)")
    ap.add_argument("--state", default=str(STATE_PATH), help="Tệp state (mặc định state/gia-lap-dinh-ky-gan-nhat.json)")
    ap.add_argument("--giu-thu-muc", action="store_true", help="Giữ thư mục tạm để xem đầu ra (in đường dẫn)")
    ap.add_argument("--json", action="store_true", help="In báo cáo JSON thay bảng tóm tắt")
    args = ap.parse_args(argv)

    state_path = Path(args.state)
    che_do = "truc_tuyen" if args.truc_tuyen else "ngoai_tuyen"
    state_cu, loi_state = doc_state(state_path)
    truoc_ro_ri = set(_de_tai_canary_trong_exports(REPO_ROOT))
    tam = Path(tempfile.mkdtemp(prefix="gia-lap-dinh-ky-"))
    kich_ban: Dict[str, Dict[str, Any]] = {}
    pytest_kq: Optional[Dict[str, Any]] = None
    try:
        try:
            repo = dung_ban_sao(REPO_ROOT, tam)
        except (OSError, RuntimeError) as exc:
            print(f"⚪ KHÔNG ĐO ĐƯỢC: không dựng được bản sao tạm — {exc}")
            return 2
        for ma in (args.kich_ban or list(KICH_BAN)):
            try:
                kich_ban[ma] = GiaLap(ma, KICH_BAN[ma], repo, args.truc_tuyen).chay_kich_ban()
            except Exception as exc:  # noqa: BLE001 — lỗi của CANARY (vd hàm nội bộ đổi chữ ký) ≠ khiếm khuyết của hệ
                kich_ban[ma] = kich_ban_loi_noi_bo(ma, exc)
                print(f"⚪ KHÔNG ĐO ĐƯỢC: {ma} — lỗi nội bộ của canary {_mo_ta_loi(exc)}")
        if not args.bo_pytest:
            try:
                pytest_kq = chay_pytest(REPO_ROOT, tam)
            except Exception as exc:  # noqa: BLE001
                pytest_kq = {"do_duoc": False, "ly_do": f"lỗi nội bộ của canary {_mo_ta_loi(exc)}",
                             "khiem_khuyet": []}
    finally:
        if args.giu_thu_muc:
            print(f"📁 Giữ thư mục tạm: {tam.as_posix()}")
        else:
            shutil.rmtree(tam, ignore_errors=True)
    ro_ri = sorted(set(_de_tai_canary_trong_exports(REPO_ROOT)) - truoc_ro_ri)
    bc = tong_hop(kich_ban, pytest_kq, state_cu, che_do, loi_state, ro_ri, du_kien=list(KICH_BAN))
    if not args.khong_ghi:
        if loi_state and state_path.exists():
            os.replace(state_path, state_path.with_name(f"{state_path.stem}.hong-{datetime.now():%Y%m%d%H%M%S}.json"))
        _ghi_json(state_path, bc)
    if args.json:
        print(json.dumps(bc, ensure_ascii=False, indent=2))
    else:
        in_tom_tat(bc)
    return bc["ma_thoat"]


def chay_an_toan(argv: Optional[List[str]] = None) -> int:
    """Điểm vào dòng lệnh: lỗi nội bộ chưa bắt của canary trả mã 2 («không đo được»), KHÔNG để Python thoát mã 1 mặc
    định — mã 1 nghĩa là «có khiếm khuyết MỚI» và sinh việc 🛎 trong tác vụ tháng."""
    try:
        return main(argv)
    except Exception as exc:  # noqa: BLE001
        print(f"⚪ KHÔNG ĐO ĐƯỢC: lỗi nội bộ của canary {_mo_ta_loi(exc)} — không phải khiếm khuyết của hệ; "
              "sửa canary trong phiên có người")
        return 2


if __name__ == "__main__":
    raise SystemExit(chay_an_toan())
