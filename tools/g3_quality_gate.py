#!/usr/bin/env python3
"""Hợp đồng chất lượng G3: cỡ mẫu, lực thống kê và NGUỒN của từng giả định.

Vì sao module này tồn tại
─────────────────────────
`run_g3_auto.py` đã có lớp CÔNG THỨC rất chín (đã qua nhiều vòng audit: hệ số 4
của Schoenfeld, hiệu chỉnh liên tục Fleiss, NI một phía, FPC + design effect
cụm). Nhưng lớp guardrail của nó (`guardrail_check`) chỉ soi VĂN BẢN do chính
`generate_artifact()` vừa sinh ra, nên phần lớn luật là TỰ ĐÚNG: R3/R4/R5/R6/R7
kiểm sự hiện diện của những câu in cứng trong template (chữ "DRAFT", tiêu đề
"PHÂN TÍCH ĐỘ NHẠY", ba nhãn "[CẦN BÁC SĨ]", dòng disclaimer) nên không bao giờ
fail được; R1 còn là mã chết vì artifact không bao giờ in PMID thật.

Hệ quả thực tế: "G3 ✅ PASS" hôm nay chỉ có nghĩa "hàm sinh artifact đã chạy
xong", KHÔNG có nghĩa "cỡ mẫu này đáng tin". Một đề tài có thể đi qua G3 với:

- effect size lấy tự động từ abstract, KHÔNG kèm PMID/DOI nào (luật nền của
  doctrine là "KHÔNG bịa effect size — phải từ pilot/y văn có nguồn hoặc MCID",
  nhưng không có chỗ nào chứa nguồn để mà kiểm);
- một OR của y văn bị dùng làm "tỷ lệ hiện mắc" cho nghiên cứu cắt ngang;
- AUC mặc định 0.75 do hệ tự đặt cho nhánh chẩn đoán;
- N do chủ nhiệm chốt THẤP HƠN N tối thiểu (tự khai thiếu lực) vẫn exit 0;
- thiết kế mà G1 đánh dấu `ambiguous=True` (chưa ai chốt) vẫn cho ra N,
  rồi N đó bị G4 KHÓA vào SAP Lock Certificate.

Module này là lớp BỔ SUNG (không thay) hợp đồng dừng của `gate_contract`: nó
kiểm CON SỐ và NGUỒN thay vì kiểm chữ, và tách rời hai sự kiện khác nhau:

1. Máy đã tính được một cỡ mẫu.
2. Người có thẩm quyền (thống kê viên / chủ nhiệm đề tài) đã xác nhận rằng
   TỪNG GIẢ ĐỊNH đưa vào phép tính là có thật và phù hợp.

Chỉ sự kiện thứ hai mới nhận ``PASS_G3_CONFIRMED``.

Giới hạn đã biết (ghi rõ để không ai đọc nhầm)
─────────────────────────────────────────────
G3 KHÔNG phải cổng ký: `gate_contract._GATE_REQUIRED_STAKEHOLDERS` không khai
stakeholder cho G3, nên `approve_gate.py` không ký G3 được và một chữ ký (nếu
có) cũng KHÔNG chứng minh được người ký là thống kê viên. Vì vậy tầng xác nhận
người thật ở đây đi qua `study_meta.json` (giống G1), và `PASS_G3_CONFIRMED`
chỉ có nghĩa "đã có người khai nhận vai trò và xác nhận từng giả định", KHÔNG
phải một bảo đảm mật mã.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

import gate_contract as GC
import skill_standards as S

STATUS_BLOCKED = "BLOCKED"
STATUS_DRAFT_PARAMS = "DRAFT_NEEDS_HUMAN_PARAMETERS"
STATUS_DRAFT_REVIEW = "DRAFT_READY_NEEDS_STATISTICIAN_REVIEW"
STATUS_CONFIRMED = "PASS_G3_CONFIRMED"

QUALITY_CONTRACT_VERSION = "G3-2026.1"

# Ba thiết kế KHÔNG dùng công thức power/effect size truyền thống — n_adjusted=0
# là CÓ CHỦ ĐÍCH (giá trị thật nằm ở confirmed_n, tính bằng RIS/TSA, pmsampsize
# hoặc bão hòa dữ liệu). Phải khớp `run_g3_auto.N_NOT_APPLICABLE_DESIGNS`;
# tests/test_g3_quality_gate.py có kiểm hồi quy chống lệch hai bản.
N_NOT_APPLICABLE_DESIGNS = frozenset({"sr_ma", "prediction", "qualitative"})

# Thiết kế KHÔNG chia hai nhóm — với chúng `n_per_group == n_total` là ĐÚNG,
# nên không được báo lỗi "n_per_group × 2 ≠ n_total".
ONE_GROUP_DESIGNS = frozenset(
    {"cross_sectional", "diagnostic", "prediction", "qualitative", "sr_ma"}
)

CANONICAL_DESIGNS = frozenset(
    {
        "rct",
        "cohort",
        "case_control",
        "cross_sectional",
        "diagnostic",
        "prediction",
        "qualitative",
        "sr_ma",
    }
)

# Loại effect size HỢP LỆ theo thiết kế. Bảng này đóng đúng hai lỗ hổng đã xác
# nhận bằng cách đọc `run_g3_auto.main()`:
#   - `cross_sectional` dùng `effect_val` TRỰC TIẾP làm tỷ lệ hiện mắc p, nên
#     một OR = 0.75 của y văn biến thành "tỷ lệ hiện mắc 75%" mà không cảnh báo;
#   - `diagnostic` thay MỌI effect_type khác AUC bằng hằng 0.75 không nguồn.
# Với hai thiết kế đó, con số đưa vào công thức phải là THAM SỐ RIÊNG có nguồn
# (prevalence / AUC), không phải thước đo liên hệ mượn tạm.
EFFECT_TYPES_BY_DESIGN: Mapping[str, frozenset[str]] = {
    "rct": frozenset({"HR", "OR", "RR", "ARR%", "MD"}),
    "cohort": frozenset({"HR", "OR", "RR", "ARR%", "MD"}),
    "case_control": frozenset({"OR", "RR", "ARR%"}),
    "cross_sectional": frozenset({"PREVALENCE"}),
    "diagnostic": frozenset({"AUC"}),
    "prediction": frozenset(),
    "qualitative": frozenset(),
    "sr_ma": frozenset(),
}

# Thước đo LIÊN HỆ (association) — không bao giờ là một tỷ lệ/xác suất tuyệt đối.
ASSOCIATION_EFFECT_TYPES = frozenset({"HR", "OR", "RR"})

ALPHA_CONVENTIONAL_MAX = 0.05
POWER_CONVENTIONAL_MIN = 0.80
POWER_PIVOTAL_RECOMMENDED = 0.90

_PLACEHOLDER_MARKERS = ("[CẦN", "[REQUIRE_HUMAN", "CHƯA XÁC NHẬN", "<CẦN")

# Định dạng nguồn được chấp nhận cho một giả định: PMID, DOI, mã đăng ký, hoặc
# tuyên bố MCID/pilot do chủ nhiệm ấn định. Cố ý KHÔNG chấp nhận văn bản trống
# hoặc chuỗi chỉ chứa nhãn [CẦN…] — doctrine `tham-dinh-dau-ra` R1b coi việc dán
# nhãn tràn lan là lách nhãn, không phải bằng chứng.
_PMID_RE = re.compile(r"\bPMID[:\s]*([0-9]{1,9})\b", re.IGNORECASE)
_DOI_RE = re.compile(r"\b10\.\d{4,9}/\S+", re.IGNORECASE)
_MCID_RE = re.compile(r"\b(MCID|MID|ngưỡng lâm sàng tối thiểu)\b", re.IGNORECASE)
_PILOT_RE = re.compile(r"\b(pilot|nghiên cứu thử|tiền khả thi)\b", re.IGNORECASE)

STANDARDS_BASIS: Sequence[Mapping[str, str]] = (
    {
        "standard": "DELTA2 guidance (Cook JA và cs., 2018)",
        "scope": (
            "Chọn và BIỆN MINH target difference; 8 mục bắt buộc khi báo cáo "
            "phép tính cỡ mẫu của thử nghiệm ngẫu nhiên"
        ),
        "pmid": "30560792",
        "doi": "10.1136/bmj.k3750",
    },
    {
        "standard": "DELTA2 — báo cáo HTA đầy đủ (2019)",
        "scope": (
            "Target difference phải khớp estimand chính; nêu rõ nếu dùng cách "
            "xác định cỡ mẫu không theo power quy ước"
        ),
        "pmid": "31661431",
        "doi": "10.3310/hta23600",
    },
    {
        "standard": "ICH E9 §3.5 (Statistical Principles for Clinical Trials)",
        "scope": (
            "Đề cương phải ghi phương pháp tính cỡ mẫu, mọi đại lượng đầu vào, "
            "CƠ SỞ của từng ước lượng và một phân tích độ nhạy của cỡ mẫu"
        ),
        "url": "https://database.ich.org/sites/default/files/E9_Guideline.pdf",
    },
    {
        "standard": "ICH E9(R1) §A.4 (Addendum on Estimands)",
        "scope": (
            "Cỡ mẫu phải xuất phát từ mô tả chính xác treatment effect quan tâm; "
            "cẩn trọng khi mượn effect size từ nghiên cứu báo cáo theo estimand khác"
        ),
        "url": (
            "https://database.ich.org/sites/default/files/"
            "E9-R1_Step4_Guideline_2019_1203.pdf"
        ),
    },
    {
        "standard": "CONSORT 2025 — mục 16a/16b",
        "scope": (
            "Nêu cỡ mẫu được xác định thế nào KÈM TẤT CẢ giả định chống đỡ phép "
            "tính; nêu phần mềm; nêu phân tích giữa kỳ và quy tắc dừng"
        ),
        "doi": "10.1136/bmj-2024-081123",
    },
    {
        "standard": "SPIRIT 2025 — mục 19",
        "scope": (
            "Đề cương phải nêu cỡ mẫu và mọi giả định; cỡ mẫu phải nhất quán với "
            "kết cục chính và với bản ghi ở cơ quan đăng ký nghiên cứu"
        ),
        "doi": "10.1136/bmj-2024-081477",
    },
    {
        "standard": "Riley RD và cs., BMJ 2020 — cỡ mẫu mô hình tiên lượng",
        "scope": (
            "Cỡ mẫu phát triển mô hình tính theo shrinkage/R² đích, KHÔNG dùng "
            "quy tắc ngón tay EPV"
        ),
        "pmid": "32188600",
        "doi": "10.1136/bmj.m441",
    },
    {
        "standard": "Riley RD, 2019 — đính chính Part II",
        "scope": "Erratum bắt buộc đọc kèm công thức Part II (nhị phân/time-to-event)",
        "pmid": "31793031",
        "doi": "10.1002/sim.8409",
    },
    {
        "standard": "van Smeden M và cs., 2016",
        "scope": (
            "Bằng chứng ủng hộ ngưỡng EPV cho hồi quy logistic là YẾU — không "
            "dùng EPV làm tiêu chí quyết định cỡ mẫu"
        ),
        "pmid": "27881078",
        "doi": "10.1186/s12874-016-0267-3",
    },
    {
        "standard": "Ogundimu EO và cs., 2016",
        "scope": (
            "Nguồn THẬT của ngưỡng 'EPV ≥ 20' — chỉ áp cho mô hình Cox có nhiều "
            "biến tiên đoán nhị phân tỷ lệ thấp, và phải theo dữ liệu cụ thể"
        ),
        "pmid": "26964707",
        "doi": "10.1016/j.jclinepi.2016.02.031",
    },
    {
        "standard": "TRIPOD+AI (2024) — mục 10",
        "scope": (
            "Giải trình cỡ mẫu RIÊNG cho phát triển và cho đánh giá mô hình, kèm "
            "chi tiết phép tính; thay thế hoàn toàn TRIPOD 2015"
        ),
        "pmid": "38626948",
        "doi": "10.1136/bmj-2023-078378",
    },
    {
        "standard": "Green SB, 1991",
        "scope": "Quy tắc n ≥ 104 + m cho kiểm định từng hệ số hồi quy đa biến",
        "pmid": "26776715",
        "doi": "10.1207/s15327906mbr2603_7",
    },
    {
        "standard": "STARD 2015 — mục 18",
        "scope": "Nêu cỡ mẫu DỰ KIẾN và cách xác định, cho nghiên cứu độ chính xác chẩn đoán",
        "pmid": "26511519",
        "doi": "10.1136/bmj.h5527",
    },
    {
        "standard": "STARD-AI (2025)",
        "scope": (
            "Bản MỞ RỘNG (không thay thế STARD 2015) khi test chỉ số là mô hình AI; "
            "đòi cỡ mẫu của từng tập huấn luyện/hiệu chỉnh/kiểm định"
        ),
        "pmid": "40954311",
        "doi": "10.1038/s41591-025-03953-8",
    },
    {
        "standard": "Buderer NMF, 1996",
        "scope": (
            "Cỡ mẫu độ nhạy/độ đặc hiệu quy ra TỔNG N qua tỷ lệ hiện mắc "
            "(N_Se = n_Se/prev; N_Sp = n_Sp/(1−prev); lấy max)"
        ),
        "pmid": "8870764",
        "doi": "10.1111/j.1553-2712.1996.tb03538.x",
    },
    {
        "standard": "Connor RJ, 1987",
        "scope": "Cỡ mẫu so sánh hai test GHÉP CẶP trên cùng bệnh nhân (nền tảng McNemar)",
        "pmid": "3567305",
    },
    {
        "standard": "STROBE — mục 10 (Study size)",
        "scope": (
            "Nghiên cứu quan sát phải giải thích cỡ mẫu đến từ đâu: theo công thức, "
            "hoặc do ràng buộc thực tế (và nói rõ ràng buộc đó)"
        ),
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC2020496/",
    },
    {
        "standard": "Hajian-Tilaki K, 2011",
        "scope": (
            "Cỡ mẫu ước lượng MỘT tỷ lệ theo sai số biên d; dùng p=0,5 khi chưa biết "
            "tỷ lệ thì phải ghi rõ lý do (phương sai lớn nhất)"
        ),
        "pmid": "24551434",
    },
    {
        "standard": "Malterud K và cs., 2016 — information power",
        "scope": "Khung quyết định cỡ mẫu định tính theo 5 chiều, thay cho công thức power",
        "pmid": "26613970",
        "doi": "10.1177/1049732315617444",
    },
    {
        "standard": "COREQ (2007) / SRQR (2014)",
        "scope": "Chuẩn báo cáo nghiên cứu định tính — khai số người tham gia và lý lẽ",
        "pmid": "17872937",
        "doi": "10.1093/intqhc/mzm042",
    },
    {
        "standard": "Wetterslev J và cs., 2017 — TSA/RIS",
        "scope": (
            "Tổng quan hệ thống không dùng công thức power theo nhóm; dùng required "
            "information size có hiệu chỉnh dị biệt (D²/I²)"
        ),
        "pmid": "28264661",
        "doi": "10.1186/s12874-017-0315-7",
    },
    {
        "standard": "FDA Guidance — Non-Inferiority Clinical Trials (11/2016)",
        "scope": (
            "Tách bạch M1 (toàn bộ hiệu quả thuốc chứng, cận dưới KTC từ dữ liệu lịch "
            "sử) và M2 (chênh lệch tối đa chấp nhận được về lâm sàng)"
        ),
        "url": "https://www.fda.gov/media/78504/download",
    },
    {
        "standard": "EMA/CHMP — Choice of the non-inferiority margin (EMEA/CPMP/EWP/2158/99)",
        "scope": (
            "Biên Δ phải biện minh trong đề cương; CẤM định nghĩa Δ như một TỶ LỆ của "
            "hiệu số thuốc chứng–giả dược, CẤM dùng effect size chuẩn hoá, CẤM nới Δ "
            "vì nghiên cứu nhỏ. (Đang có bản dự thảo thay thế EMA/301654/2025 — rà lại.)"
        ),
        "url": (
            "https://www.ema.europa.eu/en/choice-non-inferiority-margin-scientific-guideline"
        ),
    },
    {
        "standard": "CONSORT extension — non-inferiority/equivalence (Piaggio 2012)",
        "scope": "Khai khung NI/tương đương ở tiêu đề, giả thuyết, cỡ mẫu và một/hai phía",
        "pmid": "23268518",
        "doi": "10.1001/jama.2012.87802",
    },
    {
        "standard": "CONSORT extension — cluster randomised trials (2012), mục 7a",
        "scope": (
            "Nêu cách tính, SỐ CHÙM (và giả định cỡ chùm đều/không đều), cỡ chùm, ICC "
            "và độ bất định của ICC"
        ),
        "pmid": "22951546",
        "doi": "10.1136/bmj.e5661",
    },
    {
        "standard": "CONSORT extension — stepped wedge CRT (2018)",
        "scope": (
            "SW-CRT KHÔNG dùng được DE = 1+(m−1)·ICC đơn giản; phải khai đủ tham số "
            "tương quan để tái lập phép tính"
        ),
        "pmid": "30413417",
        "doi": "10.1136/bmj.k1614",
    },
    {
        "standard": "Kahan BC và cs., 2016",
        "scope": (
            "Số chùm nhỏ làm lạm phát sai lầm loại I — cần hiệu chỉnh mẫu nhỏ "
            "(Kenward-Roger/Satterthwaite hoặc sandwich hiệu chỉnh)"
        ),
        "pmid": "27600609",
        "doi": "10.1186/s13063-016-1571-2",
    },
    {
        "standard": "Eldridge SM và cs., 2006",
        "scope": (
            "Cỡ chùm không đều: cần hệ số biến thiên CV; CV < 0,23 thì ảnh hưởng "
            "không đáng kể, từ 0,23 trở lên phải hiệu chỉnh"
        ),
        "pmid": "16943232",
        "doi": "10.1093/ije/dyl129",
    },
)

# Ngưỡng lấy từ chuẩn đã xác minh — đặt tên để không rải "số ma" trong code.
CLUSTER_SMALL_SAMPLE_THRESHOLD = 40  # Kahan 2016: dưới mức này phải hiệu chỉnh mẫu nhỏ
CLUSTER_CV_NEGLIGIBLE = 0.23  # Eldridge 2006: dưới mức này bỏ qua được
DESIGN_EFFECT_TOLERANCE = 0.01  # dung sai khi đối chiếu DE tự khai với DE tính lại

# Ba kiểu biện minh biên Δ mà EMA nói rõ là KHÔNG phù hợp. Đây là kiểm VĂN BẢN
# trên chính lời biện minh do bác sĩ viết, không phải kiểm artifact do máy sinh.
_EMA_FORBIDDEN_MARGIN_PATTERNS = (
    (
        re.compile(
            r"(tỷ lệ|phần trăm|proportion|%)\s*(của|of)?\s*(hiệu số|difference|hiệu quả)",
            re.IGNORECASE,
        ),
        "định nghĩa Δ như một TỶ LỆ của hiệu số thuốc chứng–giả dược",
    ),
    (
        re.compile(r"(effect size|cohen'?s d|độ lệch chuẩn chuẩn hoá|standardi[sz]ed)", re.IGNORECASE),
        "dùng effect size chuẩn hoá để biện minh Δ",
    ),
    (
        re.compile(r"(nghiên cứu nhỏ|cỡ mẫu nhỏ|small study|hạn chế nguồn lực)", re.IGNORECASE),
        "nới Δ vì nghiên cứu nhỏ / thiếu nguồn lực",
    ),
)

_NI_FRAMEWORKS = frozenset({"FDA", "EMA", "OTHER"})

# Ngôn ngữ KIỂM ĐỊNH POWER không được xuất hiện trong khối cỡ mẫu của một đề tài
# định tính. Cố ý KHÔNG bắt chữ "Effect size" chung chung: tiêu đề bảng độ nhạy
# do template in cứng cho MỌI thiết kế ("Power × Effect size → N tổng"), bắt ở đó
# là bắt lỗi template chứ không phải lỗi của nhà nghiên cứu.
_POWER_LANGUAGE = re.compile(r"(lực thống kê|power\s*=|1\s*[-−]\s*β|α\s*=)", re.IGNORECASE)


def _protocol_block(artifact_text: str) -> str:
    """Khối "PHẦN 4 — KHỐI CỠ MẪU" — đoạn bác sĩ thật sự dán vào đề cương."""
    start = artifact_text.find("PHẦN 4")
    if start < 0:
        return ""
    block = artifact_text[start:]
    end = block.find("## PHẦN 5")
    return block[:end] if end > 0 else block


# ════════════════════════════════════════════════════════════════════════════
# Tiện ích nhỏ
# ════════════════════════════════════════════════════════════════════════════


def _criterion(
    criterion_id: str,
    label: str,
    status: str,
    evidence: str,
    action: str = "",
) -> dict[str, str]:
    """Một dòng tiêu chí — cùng hình dạng với g1/g2_quality_gate."""
    return {
        "id": criterion_id,
        "label": label,
        "status": status,
        "evidence": evidence,
        "action": action,
    }


def _read_json(path: Path) -> dict[str, Any]:
    """Đọc JSON, trả dict rỗng khi thiếu/hỏng (không ném lỗi lên cổng)."""
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _present(value: Any) -> bool:
    """Giá trị có nội dung THẬT không (chuỗi chỉ chứa nhãn [CẦN…] là KHÔNG)."""
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return True
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return False
        upper = text.upper()
        return not any(marker in upper for marker in _PLACEHOLDER_MARKERS)
    if isinstance(value, Mapping):
        return any(_present(v) for v in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_present(v) for v in value)
    return True


def _g3_meta(meta: Mapping[str, Any]) -> Mapping[str, Any]:
    """Khối `gate_params.G3` của study_meta.json (nơi bác sĩ ghim xác nhận)."""
    params = meta.get("gate_params")
    if not isinstance(params, Mapping):
        return {}
    value = params.get("G3")
    return value if isinstance(value, Mapping) else {}


def _g1_meta(meta: Mapping[str, Any]) -> Mapping[str, Any]:
    params = meta.get("gate_params")
    if not isinstance(params, Mapping):
        return {}
    value = params.get("G1")
    return value if isinstance(value, Mapping) else {}


def _as_float(value: Any) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_int(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def source_kind(value: Any) -> Optional[str]:
    """Phân loại một khai báo nguồn: PMID / DOI / MCID / PILOT, hoặc None.

    Cố ý KHẮT KHE: một chuỗi chỉ chứa "[CẦN PMID/DOI]" KHÔNG phải nguồn — đó
    chính là mẫu "lách nhãn" mà rubric R1b của `tham-dinh-dau-ra` cấm.
    """
    if not _present(value):
        return None
    text = str(value)
    if _PMID_RE.search(text):
        return "PMID"
    if _DOI_RE.search(text):
        return "DOI"
    if _MCID_RE.search(text):
        return "MCID"
    if _PILOT_RE.search(text):
        return "PILOT"
    return None


def _valid_iso_time(value: Any) -> bool:
    """`reviewed_at` phải là ISO-8601 thật và không nằm ở tương lai."""
    text = str(value or "").strip()
    if not text:
        return False
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return False
    reference = datetime.now(tz=parsed.tzinfo) if parsed.tzinfo else datetime.now()
    return parsed <= reference


def _guardrail_ok(checkpoint: Mapping[str, Any]) -> bool:
    """G3 ghi `guardrail` là CHUỖI ("✅ PASS"), khác G1/G2 dùng dict.

    Bẫy tích hợp thật: sao chép `guardrail.get("passed")` từ g2_quality_gate
    sang đây sẽ luôn cho False. Dùng bộ đọc dùng chung của skill_standards, có
    lối lùi cho cả hai dạng.
    """
    try:
        return bool(S._guardrail_passed(dict(checkpoint)))
    except Exception:  # pragma: no cover - lưới an toàn, không để cổng chết
        raw = checkpoint.get("guardrail")
        if isinstance(raw, Mapping):
            return raw.get("passed") is True
        return "PASS" in str(raw or "").upper() and "FAIL" not in str(raw or "").upper()


# ════════════════════════════════════════════════════════════════════════════
# Đọc bảng phân tích độ nhạy trong artifact A4
# ════════════════════════════════════════════════════════════════════════════


def parse_sensitivity_table(artifact_text: str) -> dict[str, Any]:
    """Bóc bảng PHẦN 3 để kiểm NHẤT QUÁN NỘI BỘ bằng số.

    Trả về: số ô, số ô "N/A", ô cơ sở (power cơ sở × ES ×1.00) và tỷ lệ dropout
    mà TIÊU ĐỀ bảng tự khai. Dùng để bắt hai lỗi đã xác nhận bằng cách chạy
    thật: (1) tiêu đề ghi "điều chỉnh X% dropout" nhưng các ô KHÔNG áp dropout;
    (2) bảng được tính TRƯỚC khi áp FPC/cluster design effect nên lệch khỏi N
    chính ở PHẦN 2.
    """
    result: dict[str, Any] = {
        "found": False,
        "cells_total": 0,
        "cells_na": 0,
        "rows": {},
        "header_dropout_pct": None,
    }
    if not artifact_text:
        return result
    marker = artifact_text.find("PHÂN TÍCH ĐỘ NHẠY")
    if marker < 0:
        return result
    section = artifact_text[marker:]
    end = section.find("## PHẦN 4")
    if end > 0:
        section = section[:end]

    header = re.search(r"điều chỉnh\s+(\d+)%\s+dropout", section)
    if header:
        result["header_dropout_pct"] = int(header.group(1))

    for line in section.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if len(cells) < 4:
            continue
        power_match = re.fullmatch(r"(\d+)%", cells[0])
        if not power_match:
            continue
        result["found"] = True
        values: list[Optional[int]] = []
        for cell in cells[1:4]:
            number = re.fullmatch(r"\*{0,2}(\d+)\*{0,2}\**", cell)
            if number:
                values.append(int(number.group(1)))
            else:
                values.append(None)
                result["cells_na"] += 1
            result["cells_total"] += 1
        result["rows"][int(power_match.group(1))] = values
    return result


def sensitivity_base_cell(
    table: Mapping[str, Any], power: Optional[float]
) -> Optional[int]:
    """Ô cơ sở = hàng ứng với power đang dùng, cột ES × 1.00 (cột giữa)."""
    rows = table.get("rows") or {}
    if not rows:
        return None
    key = None
    if power is not None:
        key = int(round(power * 100))
    if key not in rows:
        return None
    values = rows[key]
    return values[1] if len(values) > 1 else None


# ════════════════════════════════════════════════════════════════════════════
# Lõi đánh giá
# ════════════════════════════════════════════════════════════════════════════


def evaluate_g3_quality(
    *,
    study: str,
    checkpoint: Mapping[str, Any],
    artifact_path: Path,
    g0_checkpoint: Mapping[str, Any],
    g1_checkpoint: Mapping[str, Any],
    meta: Mapping[str, Any],
) -> dict[str, Any]:
    """Chấm G3 theo hai tầng: máy kiểm SỐ, rồi người thật xác nhận GIẢ ĐỊNH."""
    artifact_path = Path(artifact_path)
    artifact_text = (
        artifact_path.read_text(encoding="utf-8") if artifact_path.exists() else ""
    )
    g3 = _g3_meta(meta)
    g1_params = _g1_meta(meta)

    design_code = str(checkpoint.get("design_code") or "")
    design_ambiguous = bool(checkpoint.get("design_ambiguous"))
    effect_val = _as_float(checkpoint.get("effect_val"))
    effect_type = checkpoint.get("effect_type")
    effect_type = str(effect_type).strip() if effect_type else ""
    effect_quality = checkpoint.get("effect_quality")
    alpha = _as_float(checkpoint.get("alpha"))
    power = _as_float(checkpoint.get("power"))
    dropout = _as_float(checkpoint.get("dropout"))
    n_total = _as_int(checkpoint.get("n_total")) or 0
    n_per_group = _as_int(checkpoint.get("n_per_group")) or 0
    n_adjusted = _as_int(checkpoint.get("n_adjusted")) or 0
    confirmed_n = _as_int(checkpoint.get("confirmed_n"))
    hypothesis_type = str(checkpoint.get("hypothesis_type") or "superiority")
    margin = _as_float(checkpoint.get("margin"))
    formula_used = str(checkpoint.get("formula_used") or "")

    n_not_applicable = design_code in N_NOT_APPLICABLE_DESIGNS
    table = parse_sensitivity_table(artifact_text)

    automatic: list[dict[str, str]] = []
    human: list[dict[str, str]] = []

    # ── G3-AUTO-00 — liêm chính nền ────────────────────────────────────────
    guardrail_passed = _guardrail_ok(checkpoint)
    automatic.append(
        _criterion(
            "G3-AUTO-00",
            "Guardrail liêm chính G3 sạch",
            "PASS" if guardrail_passed else "BLOCK",
            f"guardrail={checkpoint.get('guardrail')!r}",
            "Sửa lỗi liêm chính (nguồn, PII, tự claim đã duyệt) trước khi chấm chất lượng.",
        )
    )

    # ── G3-AUTO-01 — tiền đề G0/G1 ─────────────────────────────────────────
    # `resolve_design_code()` rơi về "cohort" IM LẶNG khi không có G0 lẫn G1,
    # nên `run_g3_auto.py --study X --effect-size 0.7 --effect-type HR` trên
    # thư mục trống vẫn tính N như thể là cohort rồi exit 0.
    has_g1 = bool(g1_checkpoint)
    has_g0 = bool(g0_checkpoint)
    if has_g1 and design_ambiguous:
        # G1 tự đánh dấu thiết kế chỉ là placeholder tạm (bác sĩ CHƯA xác nhận
        # khoảng trống thật). N tính ra đúng công thức cho mã thiết kế đó, nhưng
        # đổi thiết kế thường đổi luôn công thức — nên không được để trôi xuống
        # G4 rồi bị khóa vào SAP.
        premise_status = "REVIEW"
        premise_evidence = (
            "G1 gắn cờ design.ambiguous=true — thiết kế mới là placeholder tạm, "
            "chưa được người thật chốt"
        )
    elif has_g1:
        premise_status, premise_evidence = "PASS", "có G1_checkpoint làm nguồn thiết kế"
    elif has_g0:
        premise_status = "REVIEW"
        premise_evidence = "có G0 nhưng THIẾU G1 — thiết kế chưa qua bước chốt"
    else:
        premise_status = "BLOCK"
        premise_evidence = (
            "KHÔNG có G0 lẫn G1 — design_code là giá trị mặc định im lặng, "
            "không phải thiết kế của đề tài"
        )
    automatic.append(
        _criterion(
            "G3-AUTO-01",
            "Tiền đề G0/G1 có thật (thiết kế không do mặc định im lặng)",
            premise_status,
            premise_evidence,
            "Chạy G0/G1 trước; không tính cỡ mẫu trên thiết kế mặc định.",
        )
    )

    # ── G3-AUTO-02 — mã thiết kế canonical ─────────────────────────────────
    automatic.append(
        _criterion(
            "G3-AUTO-02",
            "Mã thiết kế thuộc từ vựng canonical",
            "PASS" if design_code in CANONICAL_DESIGNS else "BLOCK",
            f"design_code={design_code!r}",
            "Chốt lại thiết kế ở G1; công thức cỡ mẫu chọn theo thiết kế.",
        )
    )

    # ── G3-AUTO-03 — loại effect size phải TƯƠNG THÍCH thiết kế ────────────
    allowed = EFFECT_TYPES_BY_DESIGN.get(design_code, frozenset())
    if not effect_type:
        compat_status = "PASS" if (n_not_applicable or n_adjusted == 0) else "REVIEW"
        compat_evidence = "chưa có effect_type"
    elif design_code == "cross_sectional" and effect_type in ASSOCIATION_EFFECT_TYPES:
        compat_status = "BLOCK"
        compat_evidence = (
            f"design=cross_sectional nhưng effect_type={effect_type} — "
            f"{effect_type} là thước đo LIÊN HỆ, bị nhánh cắt ngang dùng thẳng "
            "làm TỶ LỆ HIỆN MẮC p (sai bản chất tham số)"
        )
    elif design_code == "diagnostic" and effect_type != "AUC":
        compat_status = "BLOCK"
        compat_evidence = (
            f"design=diagnostic nhưng effect_type={effect_type} — nhánh chẩn đoán "
            "thay mọi loại khác bằng hằng AUC=0.75 không nguồn"
        )
    elif allowed and effect_type in allowed:
        compat_status = "PASS"
        compat_evidence = f"effect_type={effect_type} hợp lệ cho {design_code}"
    elif not allowed:
        compat_status = "PASS" if n_not_applicable else "REVIEW"
        compat_evidence = (
            f"thiết kế {design_code} không dùng effect size kiểu so sánh 2 nhóm"
        )
    else:
        compat_status = "REVIEW"
        compat_evidence = (
            f"effect_type={effect_type} không nằm trong tập hợp lệ của "
            f"{design_code} ({', '.join(sorted(allowed))})"
        )
    automatic.append(
        _criterion(
            "G3-AUTO-03",
            "Loại effect size tương thích với thiết kế và dạng kết cục",
            compat_status,
            compat_evidence,
            "Cấp tham số ĐÚNG loại (tỷ lệ hiện mắc cho cắt ngang, AUC cho chẩn đoán) kèm nguồn.",
        )
    )

    # ── G3-AUTO-04 — giá trị lõi ───────────────────────────────────────────
    if n_adjusted > 0:
        core_status = "PASS"
        core_evidence = f"n_adjusted={n_adjusted}"
    elif n_not_applicable and confirmed_n and confirmed_n > 0:
        core_status = "PASS"
        core_evidence = (
            f"thiết kế {design_code} không dùng công thức power; "
            f"N thực tế = {confirmed_n}"
        )
    else:
        core_status = "BLOCK"
        core_evidence = (
            f"chưa có cỡ mẫu dùng được (n_adjusted={n_adjusted}, "
            f"confirmed_n={confirmed_n})"
        )
    automatic.append(
        _criterion(
            "G3-AUTO-04",
            "Có giá trị cỡ mẫu dùng được (hoặc N thay thế hợp lệ)",
            core_status,
            core_evidence,
            "Cấp effect size có nguồn, hoặc N tính bằng phương pháp thay thế của thiết kế.",
        )
    )

    # ── G3-AUTO-05 — NGUỒN của effect size (luật nền của doctrine) ─────────
    effect_source = g3.get("effect_source") or g3.get("effect_size_source")
    kind = source_kind(effect_source)
    needs_effect = bool(effect_val) or (effect_type and not n_not_applicable)
    if not needs_effect:
        source_status = "PASS"
        source_evidence = "thiết kế không dùng effect size kiểu này"
    elif kind:
        source_status = "PASS"
        source_evidence = f"nguồn loại {kind}: {str(effect_source)[:120]}"
    else:
        source_status = "REVIEW"
        source_evidence = (
            "KHÔNG có PMID/DOI/MCID/pilot cho effect size — "
            f"gate_params.G3.effect_source={effect_source!r}"
        )
    automatic.append(
        _criterion(
            "G3-AUTO-05",
            "Effect size có định danh nguồn thật (PMID/DOI/MCID/pilot)",
            source_status,
            source_evidence,
            "Ghi gate_params.G3.effect_source = PMID/DOI của y văn, hoặc tuyên bố\n"
            "MCID do chủ nhiệm ấn định.",
        )
    )

    # ── G3-AUTO-06 — chất lượng effect size ────────────────────────────────
    if effect_quality == "crude":
        quality_status = "REVIEW"
        quality_evidence = (
            "effect_quality='crude' — số thô trích từ abstract, không kèm 95%CI, "
            "có thể lẫn ARR%/RR"
        )
    elif effect_quality == "labeled":
        quality_status = "PASS"
        quality_evidence = "effect_quality='labeled' (trích kèm 95%CI)"
    else:
        quality_status = "PASS"
        quality_evidence = "effect size do bác sĩ cấp trực tiếp hoặc không áp dụng"
    automatic.append(
        _criterion(
            "G3-AUTO-06",
            "Effect size không phải số THÔ chưa đọc toàn văn",
            quality_status,
            quality_evidence,
            "Đọc toàn văn nguồn, lấy ước lượng kèm 95%CI; cân nhắc dùng CẬN DƯỚI CI thay điểm ước lượng.",
        )
    )

    # ── G3-AUTO-07 — alpha / power ─────────────────────────────────────────
    alpha_issues: list[str] = []
    if alpha is None:
        alpha_issues.append("thiếu alpha")
    elif alpha > ALPHA_CONVENTIONAL_MAX:
        alpha_issues.append(f"alpha={alpha} > {ALPHA_CONVENTIONAL_MAX} (quy ước)")
    if power is None:
        alpha_issues.append("thiếu power")
    elif power < POWER_CONVENTIONAL_MIN:
        alpha_issues.append(f"power={power} < {POWER_CONVENTIONAL_MIN} (quy ước)")
    multiplicity = g3.get("multiplicity_strategy")
    primary_outcome_count = _as_int(g3.get("primary_outcome_count")) or 1
    interim_planned = bool(g3.get("interim_analysis_planned"))
    if (primary_outcome_count > 1 or interim_planned) and not _present(multiplicity):
        alpha_issues.append(
            "có nhiều kết cục chính hoặc phân tích giữa kỳ nhưng chưa khai "
            "chiến lược alpha (Bonferroni/Holm/alpha-spending)"
        )
    automatic.append(
        _criterion(
            "G3-AUTO-07",
            "Alpha/power trong quy ước và đã xử lý bội/giữa kỳ",
            "REVIEW" if alpha_issues else "PASS",
            "; ".join(alpha_issues) if alpha_issues else f"alpha={alpha}, power={power}",
            "Biện minh alpha/power ngoài quy ước; khai chiến lược alpha khi đa kết cục hoặc có giữa kỳ.",
        )
    )

    # ── G3-AUTO-08 — nguồn của các tham số nuisance ĐANG ĐƯỢC DÙNG ─────────
    # Chỉ đòi nguồn cho tham số THỰC SỰ vào công thức của thiết kế này, để
    # không bắt lỗi oan.
    nuisance_missing: list[str] = []
    if effect_type == "HR" and not _present(g3.get("p_event_source")):
        nuisance_missing.append("p_event (tỷ lệ biến cố nền cho log-rank)")
    if effect_type == "MD" and not _present(g3.get("sd_source")):
        nuisance_missing.append("SD (độ lệch chuẩn kết cục liên tục)")
    if effect_type in {"OR", "RR", "ARR%"} and not _present(g3.get("p0_source")):
        nuisance_missing.append("p0 (tỷ lệ biến cố nhóm chứng)")
    if design_code == "cross_sectional" and not _present(g3.get("prevalence_source")):
        nuisance_missing.append("tỷ lệ hiện mắc p (quy ước thận trọng là p=0,5)")
    if design_code == "diagnostic" and not _present(g3.get("prevalence_source")):
        nuisance_missing.append("tỷ lệ hiện mắc để quy Se/Sp ra tổng N")
    # Chỉ đòi nguồn cho dropout khi nó THỰC SỰ được áp (n_adjusted suy từ
    # n_total). Với sr_ma/prediction/qualitative, n_total=0 nên giá trị dropout
    # mặc định nằm trong checkpoint mà không vào phép tính nào — bắt lỗi ở đây
    # là bắt oan.
    if (
        n_total > 0
        and dropout is not None
        and dropout > 0
        and not _present(g3.get("dropout_source"))
    ):
        nuisance_missing.append("tỷ lệ bỏ cuộc dự kiến")
    automatic.append(
        _criterion(
            "G3-AUTO-08",
            "Mọi tham số phụ đưa vào công thức đều có nguồn",
            "REVIEW" if nuisance_missing else "PASS",
            (
                "thiếu nguồn: " + "; ".join(nuisance_missing)
                if nuisance_missing
                else "các tham số phụ đang dùng đều có khai nguồn"
            ),
            "Ghi <tên>_source trong gate_params.G3 (vd p_event_source,\n"
            "dropout_source) kèm PMID/DOI hoặc cơ sở.",
        )
    )

    # ── G3-AUTO-09 — nhất quán nội bộ bằng SỐ ──────────────────────────────
    consistency: list[str] = []
    if n_total and n_per_group and design_code not in ONE_GROUP_DESIGNS:
        if abs(n_per_group * 2 - n_total) > 1:
            consistency.append(
                f"n_per_group×2={n_per_group * 2} ≠ n_total={n_total}"
            )
    if n_total and n_per_group and design_code in ONE_GROUP_DESIGNS:
        if n_per_group not in (n_total, 0):
            consistency.append(
                f"thiết kế một nhóm nhưng n_per_group={n_per_group} ≠ n_total={n_total}"
            )
    if n_total and n_adjusted and dropout is not None and dropout > 0:
        if n_adjusted < n_total:
            consistency.append(
                f"n_adjusted={n_adjusted} < n_total={n_total} dù có dropout"
            )
    if table.get("found"):
        base = sensitivity_base_cell(table, power)
        if table.get("cells_na"):
            consistency.append(
                f"bảng độ nhạy có {table['cells_na']}/{table['cells_total']} ô N/A "
                "không nêu lý do"
            )
        if base is not None and n_total and base != n_total and base != n_adjusted:
            consistency.append(
                f"ô cơ sở bảng độ nhạy={base} không khớp n_total={n_total} "
                f"hay n_adjusted={n_adjusted}"
            )
        header_pct = table.get("header_dropout_pct")
        if (
            base is not None
            and header_pct
            and n_total
            and base == n_total
            and n_adjusted != n_total
        ):
            consistency.append(
                f"tiêu đề bảng tự khai 'điều chỉnh {header_pct}% dropout' nhưng ô "
                "cơ sở là N TRƯỚC dropout"
            )
    elif n_adjusted > 0:
        consistency.append("không đọc được bảng phân tích độ nhạy trong artifact")
    automatic.append(
        _criterion(
            "G3-AUTO-09",
            "Các con số trong artifact nhất quán với nhau",
            "REVIEW" if consistency else "PASS",
            "; ".join(consistency) if consistency else "N, bảng độ nhạy và dropout khớp nhau",
            "Sinh lại artifact sau khi sửa; bảng độ nhạy phải neo vào chính N đã kết luận.",
        )
    )

    # ── G3-AUTO-10 — chuẩn báo cáo theo thiết kế ───────────────────────────
    standards = S.reporting_standards_for(design_code) if design_code else {}
    primary_standard = str(standards.get("primary") or "")
    token = primary_standard.split("(")[0].split("—")[0].strip()
    reporting_ok = bool(token) and token.casefold() in artifact_text.casefold()
    automatic.append(
        _criterion(
            "G3-AUTO-10",
            "Artifact nhắc đúng chuẩn báo cáo của thiết kế",
            "PASS" if reporting_ok else "REVIEW",
            (
                f"tìm thấy {token!r} trong artifact"
                if reporting_ok
                else f"artifact không nhắc {token!r} (chuẩn: {primary_standard!r})"
            ),
            "Thêm khối cỡ mẫu theo văn phong chuẩn báo cáo (CONSORT 2025 mục 16a /\n"
            "SPIRIT 2025 mục 19 / STROBE mục 10 / STARD 2015 mục 18 / TRIPOD+AI mục 10).",
        )
    )

    # ── G3-AUTO-11 — non-inferiority / equivalence ─────────────────────────
    # FDA và EMA MÂU THUẪN nhau ở đây: FDA coi "M2 = 50% của M1" là thông lệ, còn
    # EMA nói rõ KHÔNG phù hợp khi định nghĩa Δ như một tỷ lệ của hiệu số thuốc
    # chứng–giả dược. Vì vậy cổng KHÔNG đứng về một phía — nó buộc đề tài KHAI
    # khung quy định đang theo, rồi mới áp bộ kiểm tương ứng.
    justification = str(g3.get("margin_justification") or "")
    framework = str(g3.get("ni_regulatory_framework") or "").strip().upper()
    if hypothesis_type == "superiority":
        ni_status, ni_evidence = "PASS", "giả thuyết superiority"
    else:
        ni_problems: list[str] = []
        if margin is None or margin <= 0:
            ni_problems.append("thiếu biên Δ hợp lệ")
        if not _present(justification):
            ni_problems.append("thiếu BIỆN MINH LÂM SÀNG cho biên Δ")
        if not source_kind(g3.get("margin_source")):
            ni_problems.append("thiếu nguồn (PMID/DOI) cho biên Δ")
        if framework not in _NI_FRAMEWORKS:
            ni_problems.append(
                "chưa khai khung quy định cho biên Δ (FDA/EMA/OTHER) — hai khung "
                "mâu thuẫn nhau nên phải nói rõ đang theo khung nào"
            )
        if framework == "EMA" and _present(justification):
            for pattern, label in _EMA_FORBIDDEN_MARGIN_PATTERNS:
                if pattern.search(justification):
                    ni_problems.append(f"biện minh rơi vào dạng EMA nói rõ là KHÔNG phù hợp: {label}")
        if framework == "FDA" and _present(justification):
            if not re.search(r"\bM1\b", justification) or not re.search(r"\bM2\b", justification):
                ni_problems.append(
                    "theo khung FDA nhưng biện minh không tách bạch M1 và M2"
                )
        ni_status = "BLOCK" if (margin is None or margin <= 0) else "REVIEW"
        ni_status = "PASS" if not ni_problems else ni_status
        ni_evidence = (
            "; ".join(ni_problems)
            if ni_problems
            else f"hypothesis_type={hypothesis_type}, margin={margin}, khung={framework}"
        )
    automatic.append(
        _criterion(
            "G3-AUTO-11",
            "Non-inferiority/equivalence: biên Δ có khung quy định, biện minh và nguồn",
            ni_status,
            ni_evidence,
            "Khai ni_regulatory_framework (FDA/EMA) + margin_justification +\n"
            "margin_source; biên Δ quá rộng làm kết luận 'không kém hơn' quá dễ đạt.",
        )
    )

    # ── G3-AUTO-12 — thiết kế theo chùm ────────────────────────────────────
    icc = _as_float(g3.get("icc"))
    cluster_size = _as_int(g3.get("cluster_size"))
    is_cluster = bool(g3.get("cluster_randomised")) or icc is not None
    if not is_cluster:
        cluster_status, cluster_evidence = "PASS", "không khai thiết kế theo chùm"
    else:
        cluster_problems = []
        if icc is None:
            cluster_problems.append("thiếu ICC")
        elif not source_kind(g3.get("icc_source")):
            cluster_problems.append("thiếu NGUỒN của ICC")
        if not cluster_size:
            cluster_problems.append("thiếu cỡ chùm trung bình m")

        # Kiểm SỐ HỌC design effect thay vì tin con số tự khai (CONSORT cluster
        # extension mục 7a đòi nêu cách tính; ở đây ta tính lại và đối chiếu).
        declared_de = _as_float(g3.get("design_effect"))
        if declared_de is not None and icc is not None and cluster_size:
            expected_de = 1 + (cluster_size - 1) * icc
            if abs(declared_de - expected_de) > DESIGN_EFFECT_TOLERANCE:
                cluster_problems.append(
                    f"design_effect tự khai={declared_de} nhưng 1+(m−1)·ICC="
                    f"{expected_de:.3f}"
                )

        # Số chùm là thứ chi phối lực của thử nghiệm theo chùm, không phải tổng N.
        n_clusters = _as_int(g3.get("n_clusters"))
        if n_clusters is None and cluster_size and n_total:
            n_clusters = -(-n_total // cluster_size)  # làm tròn lên
        if n_clusters is None:
            cluster_problems.append("thiếu SỐ CHÙM (không suy ra được)")
        elif n_clusters < CLUSTER_SMALL_SAMPLE_THRESHOLD and not _present(
            g3.get("small_sample_correction")
        ):
            cluster_problems.append(
                f"số chùm={n_clusters} < {CLUSTER_SMALL_SAMPLE_THRESHOLD} nhưng chưa "
                "khai hiệu chỉnh mẫu nhỏ (Kenward-Roger/Satterthwaite hoặc sandwich)"
            )

        # Cỡ chùm không đều làm N thay đổi đáng kể khi CV ≥ 0,23.
        if g3.get("equal_cluster_sizes") is not True:
            cv = _as_float(g3.get("cluster_size_cv"))
            if cv is None:
                cluster_problems.append(
                    "cỡ chùm không khẳng định là đều nhưng thiếu hệ số biến thiên CV"
                )
            elif cv >= CLUSTER_CV_NEGLIGIBLE and not _present(
                g3.get("unequal_cluster_adjustment")
            ):
                cluster_problems.append(
                    f"CV cỡ chùm={cv} ≥ {CLUSTER_CV_NEGLIGIBLE} nhưng chưa khai hiệu chỉnh"
                )

        cluster_status = "REVIEW" if cluster_problems else "PASS"
        cluster_evidence = (
            "; ".join(cluster_problems)
            if cluster_problems
            else f"ICC={icc} có nguồn, m={cluster_size}, số chùm={n_clusters}"
        )
    automatic.append(
        _criterion(
            "G3-AUTO-12",
            "Thiết kế theo chùm: ICC có nguồn, design effect đúng số học, đủ số chùm",
            cluster_status,
            cluster_evidence,
            "Khai icc/icc_source/cluster_size/n_clusters; số chùm nhỏ phải khai hiệu chỉnh mẫu nhỏ.",
        )
    )

    # ── G3-AUTO-16 — hiệu chỉnh quần thể hữu hạn dùng ĐÚNG CHỖ ─────────────
    # FPC chỉ đúng khi chọn mẫu không hoàn lại từ một quần thể HỮU HẠN đếm được
    # và suy luận nhắm vào chính quần thể đó (khảo sát cắt ngang/mô tả). Với
    # thử nghiệm ngẫu nhiên, suy luận nhắm vào quá trình sinh dữ liệu, nên FPC
    # chỉ làm N NHỎ ĐI một cách sai lầm → thiếu lực.
    population_n = _as_int(g3.get("population_n"))
    if population_n is None:
        fpc_status, fpc_evidence = "PASS", "không dùng hiệu chỉnh quần thể hữu hạn"
    elif design_code == "rct" or is_cluster:
        fpc_status = "BLOCK"
        fpc_evidence = (
            f"dùng FPC (population_n={population_n}) cho thử nghiệm ngẫu nhiên — "
            "FPC chỉ đúng cho khảo sát trên quần thể hữu hạn, ở đây nó làm N nhỏ "
            "đi một cách sai lầm"
        )
    elif design_code in {"cross_sectional", "cohort", "case_control"}:
        if not _present(g3.get("population_n_source")):
            fpc_status = "REVIEW"
            fpc_evidence = f"có population_n={population_n} nhưng thiếu nguồn của quần thể"
        else:
            fpc_status = "PASS"
            fpc_evidence = f"FPC trên quần thể hữu hạn N={population_n} có nguồn"
    else:
        fpc_status = "REVIEW"
        fpc_evidence = (
            f"dùng FPC với thiết kế {design_code} — cần thống kê viên xác nhận là phù hợp"
        )
    automatic.append(
        _criterion(
            "G3-AUTO-16",
            "Hiệu chỉnh quần thể hữu hạn (FPC) chỉ dùng cho khảo sát quần thể hữu hạn",
            fpc_status,
            fpc_evidence,
            "Bỏ --population-n với thử nghiệm ngẫu nhiên; với khảo sát thì ghi population_n_source.",
        )
    )

    # ── G3-AUTO-17 — thiết kế không dùng power phải dùng ĐÚNG khung thay thế ─
    if design_code == "qualitative":
        alt_problems = []
        if _POWER_LANGUAGE.search(_protocol_block(artifact_text)):
            alt_problems.append(
                "khối cỡ mẫu dán vào đề cương của đề tài ĐỊNH TÍNH lại chứa ngôn ngữ "
                "kiểm định power/alpha — sai khung"
            )
        if not _present(g3.get("saturation_stopping_rule")) and not _present(
            g3.get("information_power_rationale")
        ):
            alt_problems.append(
                "thiếu QUY TẮC DỪNG bão hòa kiểm chứng được hoặc lý lẽ information power"
            )
        alt_status = "REVIEW" if alt_problems else "PASS"
        alt_evidence = "; ".join(alt_problems) or "có khung cỡ mẫu định tính hợp lệ"
    elif design_code == "sr_ma":
        # SỬA 2026-07-29 (phát hiện qua kiểm định độc lập, HIGH — tautology):
        # bản cũ tìm "RIS/TSA" trong CẢ `artifact_text` — nhưng formula_used
        # của nhánh sr_ma LUÔN tự in sẵn câu "[CẦN — Tổng quan hệ thống dùng
        # RIS/TSA, không dùng công thức power]" một cách VÔ ĐIỀU KIỆN (xem
        # generate_artifact()), nên artifact_text luôn chứa chữ "RIS"/"TSA"
        # bất kể ai đã thực sự tính RIS/TSA hay chưa — tiêu chí không bao giờ
        # có thể REVIEW. Nay CHỈ chấp nhận giá trị THẬT do người điền ở
        # gate_params.G3.confirmed_n_method (cùng nguồn mà G3-AUTO-13 đã dùng
        # cho tiêu chí "N chốt có phương pháp"), không soi lại chuỗi tự sinh.
        method_text = str(g3.get("confirmed_n_method") or "")
        has_ris = bool(
            re.search(r"\b(RIS|required information size|TSA|trial sequential)\b",
                      method_text, re.IGNORECASE)
        )
        alt_status = "PASS" if has_ris else "REVIEW"
        alt_evidence = (
            f"phương pháp: {method_text[:80]}"
            if has_ris
            else "tổng quan hệ thống nhưng gate_params.G3.confirmed_n_method chưa "
                 "nhắc required information size / TSA"
        )
    elif design_code == "prediction":
        alt_status = "PASS" if _present(g3.get("confirmed_n_method")) else "REVIEW"
        alt_evidence = (
            f"phương pháp: {str(g3.get('confirmed_n_method'))[:80]}"
            if _present(g3.get("confirmed_n_method"))
            else "mô hình tiên lượng nhưng chưa khai phương pháp (pmsampsize/Riley)"
        )
    else:
        alt_status, alt_evidence = "PASS", "thiết kế dùng công thức power thông thường"
    automatic.append(
        _criterion(
            "G3-AUTO-17",
            "Thiết kế không dùng power đã dùng đúng khung thay thế",
            alt_status,
            alt_evidence,
            "Định tính: quy tắc dừng bão hòa/information power. SR-MA: RIS + TSA\n"
            "có hiệu chỉnh dị biệt. Tiên lượng: pmsampsize theo Riley.",
        )
    )

    # ── G3-AUTO-13 — N chốt có đủ lực không ────────────────────────────────
    if confirmed_n is None:
        confirmed_status = "PASS"
        confirmed_evidence = "chưa chốt N thực tế"
    elif n_adjusted > 0 and confirmed_n < n_adjusted:
        confirmed_status = "REVIEW"
        confirmed_evidence = (
            f"N chốt={confirmed_n} THẤP HƠN N tối thiểu={n_adjusted} — "
            "đề tài tự khai thiếu lực thống kê"
        )
    elif n_not_applicable and not _present(g3.get("confirmed_n_method")):
        confirmed_status = "REVIEW"
        confirmed_evidence = (
            f"N chốt={confirmed_n} cho thiết kế {design_code} nhưng chưa ghi "
            "phương pháp tính (RIS/TSA, pmsampsize, bão hòa dữ liệu)"
        )
    else:
        confirmed_status = "PASS"
        confirmed_evidence = f"N chốt={confirmed_n} ≥ N tối thiểu={n_adjusted}"
    automatic.append(
        _criterion(
            "G3-AUTO-13",
            "N thực tế đã chốt đủ lực và có phương pháp",
            confirmed_status,
            confirmed_evidence,
            "Nâng N, hoặc ghi rõ chấp nhận giảm lực kèm hệ quả; ghi confirmed_n_method cho thiết kế không dùng power.",
        )
    )

    # ── G3-AUTO-14 — tái lập được ──────────────────────────────────────────
    # audit_research_gates coi gate_params.G3.effect_size + p_event là metadata
    # BẮT BUỘC để chạy lại; nhưng run_g3_auto chỉ ghim khi bác sĩ truyền cả
    # effect_size lẫn effect_type qua CLI, và KHÔNG bao giờ đọc lại p_event.
    pin_missing = [
        key
        for key in ("effect_size", "effect_type")
        if needs_effect and not _present(g3.get(key))
    ]
    automatic.append(
        _criterion(
            "G3-AUTO-14",
            "Tham số đã ghim đủ để chạy lại ra cùng một N",
            "REVIEW" if pin_missing else "PASS",
            (
                "chưa ghim: " + ", ".join(pin_missing)
                if pin_missing
                else "tham số quyết định đã ghim trong study_meta"
            ),
            # SỬA 2026-07-30 (audit toàn diện G0-G10, G3-QG-06 — LOW, đã biết):
            # action text cũ hứa kiểm "p_event, dropout…" nhưng pin_missing ở
            # trên CHỈ kiểm 2 khóa (effect_size/effect_type) — run_g3_auto.py
            # chưa bao giờ ghim p_event/dropout vào gate_params.G3 nên mở rộng
            # check sẽ khiến tiêu chí này REVIEW vĩnh viễn cho thiết kế cần
            # p_event (case_control/cross_sectional/diagnostic) thay vì đóng
            # đúng khoảng trống — sửa CÂU CHỮ khớp với những gì thật sự kiểm.
            "Ghim gate_params.G3 (effect_size, effect_type) để chạy lại không trôi giá trị.",
        )
    )

    # ── G3-AUTO-15 — công thức và phần mềm ─────────────────────────────────
    # `formula_used` của các thiết kế không dùng power là một CÂU GIẢI THÍCH
    # phương pháp thay thế (bắt đầu bằng "[CẦN — Mô hình tiên lượng…") — đó là
    # khai báo phương pháp hợp lệ, không phải ô trống. Chỉ ba mẫu dưới đây mới
    # thật sự nghĩa là "chưa có công thức".
    _NO_FORMULA_PREFIXES = ("[CẦN EFFECT SIZE", "[CẦN CÔNG THỨC", "[LỖI")
    formula_text = formula_used.strip()
    formula_ok = bool(formula_text) and not formula_text.upper().startswith(
        tuple(prefix.upper() for prefix in _NO_FORMULA_PREFIXES)
    )
    software_ok = _present(g3.get("software"))
    automatic.append(
        _criterion(
            "G3-AUTO-15",
            "Khai rõ công thức đã dùng và phần mềm/phiên bản",
            "PASS" if (formula_ok and software_ok) else "REVIEW",
            (
                f"formula={'có' if formula_ok else 'thiếu'}; "
                f"software={g3.get('software') or 'thiếu'}"
            ),
            "Ghi gate_params.G3.software (vd 'run_g3_auto.py + scipy 1.18.0',\n"
            "G*Power 3.1, R pwr, pmsampsize 1.1.3).",
        )
    )

    # ── Tầng NGƯỜI THẬT ────────────────────────────────────────────────────
    human.append(
        _criterion(
            "G3-HUMAN-01",
            "Chủ nhiệm/thống kê viên xác nhận effect size và nguồn của nó",
            "PASS" if (g3.get("effect_source_confirmed") is True and kind) else "REVIEW",
            (
                f"effect_source_confirmed={g3.get('effect_source_confirmed') is True}; "
                f"nguồn={kind or 'thiếu'}"
            ),
            "Đọc toàn văn nguồn rồi đặt gate_params.G3.effect_source_confirmed=true.",
        )
    )
    human.append(
        _criterion(
            "G3-HUMAN-02",
            "Đã xác nhận các giả định phụ (bỏ cuộc, tỷ lệ biến cố, SD, tỷ lệ hiện mắc)",
            "PASS" if g3.get("assumptions_confirmed") is True else "REVIEW",
            f"assumptions_confirmed={g3.get('assumptions_confirmed') is True}",
            "Rà từng dòng bảng tham số của artifact A4 rồi đặt assumptions_confirmed=true.",
        )
    )
    hypothesis_confirmed = g3.get("hypothesis_confirmed") is True
    human.append(
        _criterion(
            "G3-HUMAN-03",
            "Đã xác nhận loại giả thuyết (superiority / không thua kém / tương đương)",
            "PASS" if hypothesis_confirmed else "REVIEW",
            (
                f"hypothesis_type={hypothesis_type} "
                f"(mặc định của hệ là superiority); confirmed={hypothesis_confirmed}"
            ),
            "Chọn nhầm loại giả thuyết là sai toàn bộ phép tính — xác nhận rồi đặt hypothesis_confirmed=true.",
        )
    )
    powered_for = g3.get("powered_for_outcome")
    primary_outcome = g1_params.get("primary_outcome") or g1_params.get("primary_endpoint")
    if not _present(powered_for):
        outcome_status = "REVIEW"
        outcome_evidence = "chưa ghi N này được tính cho KẾT CỤC nào"
    elif _present(primary_outcome) and str(powered_for).strip().casefold() != str(
        primary_outcome
    ).strip().casefold():
        outcome_status = "REVIEW"
        outcome_evidence = (
            f"powered_for_outcome={str(powered_for)[:60]!r} khác kết cục chính "
            f"của G1 ({str(primary_outcome)[:60]!r})"
        )
    else:
        outcome_status = "PASS"
        outcome_evidence = f"N tính cho kết cục: {str(powered_for)[:80]}"
    human.append(
        _criterion(
            "G3-HUMAN-04",
            "Cỡ mẫu được tính cho ĐÚNG kết cục chính đã chốt ở G1",
            outcome_status,
            outcome_evidence,
            "Ghi gate_params.G3.powered_for_outcome khớp\n"
            "gate_params.G1.primary_outcome; nếu tính cho kết cục khác thì phải nói\n"
            "rõ và biện minh.",
        )
    )
    human.append(
        _criterion(
            "G3-HUMAN-05",
            "Đã xác nhận khả thi tuyển đủ cỡ mẫu tại cơ sở",
            "PASS" if g3.get("recruitment_feasibility_confirmed") is True else "REVIEW",
            (
                "recruitment_feasibility_confirmed="
                f"{g3.get('recruitment_feasibility_confirmed') is True}"
            ),
            "Đối chiếu N với lưu lượng bệnh nhân thật và thời gian thu thập, rồi xác nhận.",
        )
    )
    role_raw = str(g3.get("reviewed_by_role") or "")
    role_group = GC.role_group_for(role_raw) if role_raw else None
    review_ok = role_group in {"STATISTICIAN", "PI"} and _valid_iso_time(
        g3.get("reviewed_at")
    )
    human.append(
        _criterion(
            "G3-HUMAN-06",
            "Có vai trò (thống kê viên/chủ nhiệm) và thời điểm rà soát",
            "PASS" if review_ok else "REVIEW",
            (
                f"reviewed_by_role={role_raw or 'thiếu'} (nhóm={role_group or 'không nhận diện'}); "
                f"reviewed_at={g3.get('reviewed_at') or 'thiếu'}"
            ),
            "Ghi reviewed_by_role (STATISTICIAN hoặc PI) và reviewed_at dạng ISO-8601; không lưu danh tính.",
        )
    )
    if g3.get("pivotal_trial") is True:
        pivotal_problems = []
        if g3.get("independent_statistician_confirmed") is not True:
            pivotal_problems.append("chưa có xác nhận nhà thống kê ĐỘC LẬP")
        if power is not None and power < POWER_PIVOTAL_RECOMMENDED:
            pivotal_problems.append(
                f"power={power} < {POWER_PIVOTAL_RECOMMENDED} (khuyến nghị cho thử nghiệm then chốt)"
            )
        pivotal_status = "REVIEW" if pivotal_problems else "PASS"
        pivotal_evidence = "; ".join(pivotal_problems) or "đủ điều kiện cho thử nghiệm then chốt"
    else:
        pivotal_status = "PASS"
        pivotal_evidence = "không khai là thử nghiệm then chốt"
    human.append(
        _criterion(
            "G3-HUMAN-07",
            "Thử nghiệm then chốt: có nhà thống kê độc lập và lực đủ cao",
            pivotal_status,
            pivotal_evidence,
            "Với thử nghiệm quyết định, mời nhà thống kê độc lập xác nhận và cân nhắc power 90%.",
        )
    )

    # ── Tổng hợp ───────────────────────────────────────────────────────────
    auto_blocked = any(row["status"] == "BLOCK" for row in automatic)
    auto_review = any(row["status"] == "REVIEW" for row in automatic)
    human_complete = all(row["status"] == "PASS" for row in human)

    if auto_blocked:
        status = STATUS_BLOCKED
    elif auto_review:
        status = STATUS_DRAFT_PARAMS
    elif not human_complete:
        status = STATUS_DRAFT_REVIEW
    else:
        status = STATUS_CONFIRMED

    pending = [
        row["action"]
        for row in automatic + human
        if row["status"] != "PASS" and row.get("action")
    ]

    artifact_manifest: dict[str, dict[str, str]] = {}
    if artifact_path.exists():
        artifact_manifest["A4_SAMPLE_SIZE"] = {
            "path": str(artifact_path),
            "sha256": hashlib.sha256(artifact_path.read_bytes()).hexdigest(),
        }

    return {
        "schema_version": "1.0",
        "contract_version": QUALITY_CONTRACT_VERSION,
        "study": study,
        "gate": "G3",
        "status": status,
        "automated_checks_passed": not auto_blocked,
        "parameters_ready_for_review": not auto_blocked and not auto_review,
        "human_confirmation_complete": human_complete,
        "automatic_criteria": automatic,
        "human_criteria": human,
        "pending_actions": list(dict.fromkeys(pending)),
        "artifact_manifest": artifact_manifest,
        "sensitivity_table": {
            "found": table.get("found"),
            "cells_total": table.get("cells_total"),
            "cells_na": table.get("cells_na"),
            "base_cell": sensitivity_base_cell(table, power),
        },
        "standards_basis": [dict(item) for item in STANDARDS_BASIS],
        "scope_statement": (
            "PASS_G3_CONFIRMED chỉ xác nhận rằng từng giả định đưa vào phép tính "
            "cỡ mẫu đã có nguồn khai báo và đã được người nhận vai trò thống kê "
            "viên/chủ nhiệm xác nhận. G3 KHÔNG phải cổng ký mật mã: chữ ký sổ cái "
            "không áp dụng cho cổng này, nên đây là lời tự khai có dấu vết, không "
            "phải bằng chứng độc lập. Hợp đồng này cũng không kiểm được tính đúng "
            "đắn lâm sàng của effect size — việc đó thuộc thống kê viên và bác sĩ."
        ),
        "disclaimer": "Cần bác sĩ kiểm chứng.",
    }


# ════════════════════════════════════════════════════════════════════════════
# Xuất báo cáo và cập nhật checkpoint
# ════════════════════════════════════════════════════════════════════════════


def write_quality_report(study: str, out_dir: Path, report: Mapping[str, Any]) -> Path:
    """Ghi song song bản máy đọc (.json) và bản bác sĩ rà (.md)."""
    out_dir = Path(out_dir)
    json_path = out_dir / "G3_QUALITY_REPORT.json"
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    lines = [
        f"# BÁO CÁO CHẤT LƯỢNG G3 (CỠ MẪU) — {study}",
        "",
        f"**Trạng thái:** `{report.get('status')}`",
        f"**Phiên bản hợp đồng:** {report.get('contract_version')}",
        "",
        "## Kiểm tự động (máy kiểm SỐ và NGUỒN)",
        "| Mã | Tiêu chí | Trạng thái | Bằng chứng |",
        "|---|---|---|---|",
    ]
    for row in report.get("automatic_criteria", []):
        evidence = str(row.get("evidence") or "").replace("|", "/")
        lines.append(f"| {row['id']} | {row['label']} | {row['status']} | {evidence} |")

    lines.extend(
        [
            "",
            "## Xác nhận người thật (thống kê viên / chủ nhiệm đề tài)",
            "| Mã | Tiêu chí | Trạng thái | Bằng chứng |",
            "|---|---|---|---|",
        ]
    )
    for row in report.get("human_criteria", []):
        evidence = str(row.get("evidence") or "").replace("|", "/")
        lines.append(f"| {row['id']} | {row['label']} | {row['status']} | {evidence} |")

    lines.extend(["", "## Việc còn lại"])
    pending = report.get("pending_actions") or []
    lines.extend(f"- {item}" for item in pending)
    if not pending:
        lines.append("- Không còn mục chờ trong hợp đồng G3.")

    lines.extend(
        [
            "",
            "## Nền chuẩn",
            "| Chuẩn | Phạm vi | PMID/DOI/URL |",
            "|---|---|---|",
        ]
    )
    for item in report.get("standards_basis", []):
        parts = []
        if item.get("pmid"):
            parts.append(f"PMID:{item['pmid']}")
        if item.get("doi"):
            parts.append(f"DOI:{item['doi']}")
        if item.get("url"):
            parts.append(str(item["url"]))
        source = "; ".join(parts).replace("|", "/")
        lines.append(
            f"| {item.get('standard')} | {item.get('scope')} | {source} |"
        )

    lines.extend(
        [
            "",
            "## Giới hạn phán định",
            str(report.get("scope_statement") or ""),
            "",
            "> Cần bác sĩ kiểm chứng.",
        ]
    )
    md_path = out_dir / "G3_QUALITY_REPORT.md"
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return md_path


def refresh_checkpoint(
    *,
    study: str,
    out_dir: Path,
    report: Mapping[str, Any],
    quality_report_path: Path,
) -> Path:
    """Gắn kết quả chất lượng vào G3_checkpoint mà KHÔNG đụng khóa downstream.

    Cố ý giữ nguyên n_adjusted/confirmed_n/alpha/power/effect_*/hypothesis_type/
    margin: `run_g4_auto.py` đọc đúng những khóa này để dựng SAP, đổi tên hay
    đổi ngữ nghĩa sẽ phá cổng kế tiếp.
    """
    out_dir = Path(out_dir)
    checkpoint_path = out_dir / "G3_checkpoint.json"
    checkpoint = _read_json(checkpoint_path)
    checkpoint.update(
        {
            "study": study,
            "gate": "G3",
            "quality_contract_version": QUALITY_CONTRACT_VERSION,
            "quality_gate": dict(report),
        }
    )
    merged = list(checkpoint.get("pending_doctor_actions") or [])
    for action in report.get("pending_actions") or []:
        if action not in merged:
            merged.append(action)
    checkpoint["pending_doctor_actions"] = merged
    artifacts = checkpoint.get("artifacts")
    if not isinstance(artifacts, dict):
        artifacts = {}
        checkpoint["artifacts"] = artifacts
    artifacts["quality_report"] = str(quality_report_path)
    checkpoint["disclaimer"] = "Cần bác sĩ kiểm chứng."
    checkpoint_path.write_text(
        json.dumps(checkpoint, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return checkpoint_path


def evaluate_study(
    study: str,
    out_dir: Path,
    *,
    write: bool = True,
) -> dict[str, Any]:
    """Chấm lại G3 từ artifact đã có; KHÔNG tính lại cỡ mẫu, KHÔNG tự xác nhận."""
    out_dir = Path(out_dir)
    checkpoint = _read_json(out_dir / "G3_checkpoint.json")
    report = evaluate_g3_quality(
        study=study,
        checkpoint=checkpoint,
        artifact_path=out_dir / f"G3_A4_SAMPLE_SIZE_{study}.md",
        g0_checkpoint=_read_json(out_dir / "G0_checkpoint.json"),
        g1_checkpoint=_read_json(out_dir / "G1_checkpoint.json"),
        meta=GC.load_study_meta(out_dir),
    )
    if write:
        report_path = write_quality_report(study, out_dir, report)
        refresh_checkpoint(
            study=study,
            out_dir=out_dir,
            report=report,
            quality_report_path=report_path,
        )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Chấm lại hợp đồng chất lượng G3; không tính lại cỡ mẫu, không tự xác nhận."
    )
    parser.add_argument("--study", required=True)
    args = parser.parse_args()
    GC.ensure_utf8_stdout()
    repo_root = Path(__file__).resolve().parents[1]
    study = re.sub(r"[^\w\-]", "_", args.study.strip().replace(" ", "-"))
    out_dir = repo_root / "exports" / study
    report = evaluate_study(study, out_dir, write=True)
    print(f"G3 quality status: {report['status']}")
    for row in report["automatic_criteria"] + report["human_criteria"]:
        if row["status"] != "PASS":
            print(f"  {row['status']:6} {row['id']} — {row['label']}")
            print(f"         ↳ {row['evidence']}")
    print(f"Báo cáo: {out_dir / 'G3_QUALITY_REPORT.md'}")
    print("Cần bác sĩ kiểm chứng.")
    return 0 if report["status"] != STATUS_BLOCKED else GC.EXIT_GUARDRAIL_FAIL


if __name__ == "__main__":
    raise SystemExit(main())
