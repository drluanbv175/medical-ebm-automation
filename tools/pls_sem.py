#!/usr/bin/env python3
"""pls_sem.py — PLS-SEM (mô hình phương trình cấu trúc bình phương tối thiểu từng phần) ĐÚNG SAP đã khoá: R `seminr`
tính CHÍNH, R `cSEM` (bản cài đặt độc lập) kiểm chéo từng đại lượng.

VÌ SAO CÓ (bác sĩ chủ nhiệm 23/11/2026 — «PLS-SEM tốt nhất, tương tự SPSS/R»): bác sĩ không có bản quyền SmartPLS;
SmartPLS 4 chỉ có giao diện, không có CLI/API công khai. Năng lực PLS-SEM của hệ đi theo đúng mô hình cầu nối SPSS ↔ R:
một phần mềm tính chính, một bản cài đặt độc lập kiểm chéo, có mốc chuẩn công khai.

BA LỚP
  1. Tính chính — seminr: PLS path modeling, chỉ báo kết quả Mode A, chỉ báo cấu tạo Mode B, sơ đồ trọng số trong theo
     đường dẫn; bootstrap đúng số lần SAP khai. Đánh giá theo Hair và cộng sự 2019 (doi:10.1108/EBR-11-2018-0203):
     tải, Cronbach α, ρA, ρC, AVE, HTMT (KTC bootstrap 90% hai phía), VIF chỉ báo cấu tạo và VIF cấu trúc, hệ số đường
     dẫn (KTC phân vị), R², f², PLSpredict khi SAP khai.
  2. Kiểm chéo — cSEM: CÙNG mô hình, CÙNG dữ liệu. Đại lượng tất định so với dung sai chặt (DUNG_SAI_TAT_DINH); đại
     lượng bootstrap so theo sai số Monte Carlo (như đối chiếu gán đa trị/bootstrap của cầu nối R); PLSpredict (chia
     phần ngẫu nhiên) so theo sai số Monte Carlo của J lượt độc lập. Khác biệt do KHÁC ĐỊNH NGHĨA (mô hình tuyến tính
     chuẩn của PLSpredict, ρA/α của chỉ báo cấu tạo/một chỉ báo) ghi «không so» kèm căn cứ tài liệu — không nới
     dung sai.
  3. Mốc chuẩn thay SmartPLS — sách truy cập mở Hair và cộng sự 2021 «PLS-SEM Using R» (doi:10.1007/978-3-030-80519-7,
     CC BY 4.0): số in trong sách là ẢNH CHỤP RStudio chạy SEMinR (chú thích hình «authors' screenshot from RStudio»),
     KHÔNG phải số SmartPLS ⇒ lệnh `chuan` chỉ khẳng định «tái lập đúng số in trong sách (tính bằng SEMinR)».

SAP LÀ NGUỒN DUY NHẤT của mô hình: công cụ ĐỌC mô hình đo lường, mô hình cấu trúc, số lần bootstrap, PLSpredict, cách
xử lý ô thiếu từ SAP §4 (khối do run_g4_auto sinh từ gate_params.G1.pls_sem) và hạt giống từ SAP §10 — không nhận mô
hình qua dòng lệnh. Ngưỡng đánh giá chỉ PHÂN LOẠI khi SAP còn ghi đủ các cụm ngưỡng định trước (CUM_NGUONG_SAP).

Lệnh
  kiem      Rscript + gói cần (jsonlite, seminr, cSEM).
  cai-goi   cài gói thiếu qua `cau_noi_r cai-goi` (chạy khô mặc định; `--ap-dung` mới cài).
  cu-phap   chuẩn bị tập phân tích + cấu hình + script R (không cần R).
  chay      cu-phap rồi Rscript ⇒ `<gate>_analysis_summary.json` (khối pls_sem) + `<gate>_ket_qua.md` +
            `<gate>_kiem_cheo.json` (seminr ↔ cSEM).
  chuan     mốc chuẩn: chạy hai mô hình corporate reputation của sách (dữ liệu có sẵn trong seminr) bằng seminr và cSEM,
            so với số in trong sách (tests/fixtures/pls_sem/hair_2021_so_in.json).

Nguồn dữ liệu: MẶC ĐỊNH bộ đã khoá G5 (`cau_noi_spss.tim_du_lieu_khoa`) + G4 khoá theo trạng thái sống
(`run_stats_analysis._g4_khoa_song`); `--data <csv> --ban-nhap --thu-muc-ra <NGOÀI repo>` cho diễn tập (bản nháp không
mang data_lock, không ghi exports/).

RANH GIỚI: không đổi trạng thái cổng, không ký, không ghi study_meta/approval_ledger/G6_DAC_TA_SAP.json; R chỉ nhận cột
chỉ báo của mô hình (cột ngoài từ điển G5 hoặc «Identifier?=y» ⇒ từ chối).

Mã thoát: 0 seminr ra kết quả và kiểm chéo khớp · 1 R lỗi, seminr lỗi hoặc kiểm chéo LỆCH · 2 không đo được (không có
R/gói, thiếu SAP/từ điển, kiểm chéo không so được) · 3 từ chối (SAP không khai PLS-SEM hoặc khai thiếu, dữ liệu/G4 chưa
khoá, PII, tham số lệch SAP). Cần bác sĩ kiểm chứng.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from datetime import datetime
from pathlib import Path

for _s in (sys.stdout, sys.stderr):  # Windows cp1252 (BH55/R4)
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import cau_noi_r as R  # noqa: E402 — tìm/chạy Rscript, chuỗi R, kịch bản R PLS-SEM (MỘT cầu nối R)
import cau_noi_spss as S  # noqa: E402 — khoá dữ liệu, từ điển G5, mã thoát
import hop_dong_sap as HD  # noqa: E402 — bộ đọc SAP DUY NHẤT (hợp đồng G4_SAP_CONTRACT_<mã>.json)
import quet_dien_sai_kieu as QDSK  # noqa: E402 — quy ước số tiếng Việt (viet_so · viet_hoa_so — K11/K22/Q3/Q4)

BASE = S.BASE
MA_OK, MA_LECH, MA_KHONG_DO, MA_TU_CHOI = S.MA_OK, S.MA_LECH, S.MA_KHONG_DO, S.MA_TU_CHOI
TuChoi, KhongDoDuoc = S.TuChoi, S.KhongDoDuoc
CAN_KIEM = S.CAN_KIEM
GATE_MAC_DINH = "G6"
THOI_HAN = 3600
LOAI_PHAN_TICH = "pls_sem"
MA_DAC_TA = "pls_pm"  # giá trị duy nhất của tham_so.pls_sem trong G6_DAC_TA_SAP.json
TEN_RE = HD.PLS_TEN_RE
TEP_SO_IN = BASE / "tests" / "fixtures" / "pls_sem" / "hair_2021_so_in.json"

# ───────────────────────────── nguồn & ngưỡng (đã kiểm) ─────────────────────────────

#: Nguồn của khuôn SAP, ngưỡng đánh giá, cỡ mẫu và hướng dẫn báo cáo. DOI đối chiếu metadata Crossref 23/11/2026; kiểm
#: rút bài 23/11/2026 (Crossref `updated-by` + Retraction Watch) — xem XAC_MINH_NGUON.
NGUON = {
    "hair2019": ("Hair JF, Risher JJ, Sarstedt M, Ringle CM. When to use and how to report the results of PLS-SEM. "
                 "Eur Bus Rev. 2019;31(1):2-24", "10.1108/EBR-11-2018-0203"),
    "henseler2015": ("Henseler J, Ringle CM, Sarstedt M. A new criterion for assessing discriminant validity in "
                     "variance-based structural equation modeling. J Acad Mark Sci. 2015;43(1):115-135",
                     "10.1007/s11747-014-0403-8"),
    "dijkstra2015": ("Dijkstra TK, Henseler J. Consistent partial least squares path modeling. MIS Q. "
                     "2015;39(2):297-316",
                     "10.25300/MISQ/2015/39.2.02"),
    "fornell1981": ("Fornell C, Larcker DF. Evaluating structural equation models with unobservable variables and "
                    "measurement error. J Mark Res. 1981;18(1):39-50", "10.2307/3151312"),
    "hair2011": ("Hair JF, Ringle CM, Sarstedt M. PLS-SEM: indeed a silver bullet. J Mark Theory Pract. "
                 "2011;19(2):139-152", "10.2753/MTP1069-6679190202"),
    "cohen1988": ("Cohen J. Statistical power analysis for the behavioral sciences. 2nd ed. New York: Routledge; 1988 "
                  "(tái bản điện tử 2013)", "10.4324/9780203771587"),
    "shmueli2019": ("Shmueli G, Sarstedt M, Hair JF, Cheah JH, Ting H, Vaithilingam S, Ringle CM. Predictive model "
                    "assessment in PLS-SEM: guidelines for using PLSpredict. Eur J Mark. 2019;53(11):2322-2347",
                    "10.1108/EJM-02-2019-0189"),
    "kock2018": ("Kock N, Hadaya P. Minimum sample size estimation in PLS-SEM: the inverse square root and "
                 "gamma-exponential methods. Inf Syst J. 2018;28(1):227-261", "10.1111/isj.12131"),
    "hair2021": ("Hair JF Jr, Hult GTM, Ringle CM, Sarstedt M, Danks NP, Ray S. Partial least squares structural "
                 "equation modeling (PLS-SEM) using R: a workbook. Cham: Springer; 2021", "10.1007/978-3-030-80519-7"),
}
XAC_MINH_NGUON = ("DOI đối chiếu metadata Crossref 23/11/2026 (tác giả, năm, tạp chí, tập, trang); kiểm rút bài "
                  "23/11/2026: Crossref không có thông báo rút/đính chính cho DOI nào, Retraction Watch (bản tải "
                  "07/11/2026) không có bản ghi. Các bài đăng ở tạp chí kinh doanh/hệ thống thông tin nên không có "
                  "PMID")


def trich(ma: str) -> str:
    t, doi = NGUON[ma]
    return f"{t}. doi:{doi}"


#: Ngưỡng ĐỊNH TRƯỚC (Hair 2019 Bảng tổng hợp + nguồn gốc của từng ngưỡng). Chỉ phân loại khi SAP còn ghi đủ cụm dưới.
NGUONG = {"tai": 0.708, "tin_cay": (0.70, 0.95), "ave": 0.50, "htmt": 0.90, "vif": (3.0, 5.0), "tai_cau_tao": 0.50,
          "r2": (0.25, 0.50, 0.75), "f2": (0.02, 0.15, 0.35)}
DONG_NGUONG_SAP = (
    ("tai", "Tải ngoài của chỉ báo kết quả ≥ 0,708", ("hair2019",)),
    ("tin_cay", "Cronbach α, ρA và ρC của cấu trúc đo lường kết quả trong khoảng 0,70–0,95",
     ("hair2019", "dijkstra2015")),
    ("ave", "AVE ≥ 0,50", ("fornell1981", "hair2019")),
    ("htmt", "HTMT < 0,90 và cận trên KTC 90% bootstrap < 0,90", ("henseler2015",)),
    ("cau_tao", "Chỉ báo cấu tạo: VIF < 3 (3–5 cần xem xét; ≥ 5 đa cộng tuyến nghiêm trọng); trọng số có KTC bootstrap "
                "không chứa 0, nếu không thì tải ≥ 0,50", ("hair2019",)),
    ("cau_truc", "Mô hình cấu trúc: VIF < 3 (3–5 cần xem xét; ≥ 5 đa cộng tuyến nghiêm trọng); hệ số đường dẫn có ý "
                 "nghĩa khi KTC phân vị bootstrap không chứa 0", ("hair2019",)),
    ("r2", "R² 0,75 / 0,50 / 0,25: mạnh / trung bình / yếu (chỉ để mô tả, tuỳ lĩnh vực)", ("hair2011",)),
    ("f2", "f² 0,02 / 0,15 / 0,35: nhỏ / trung bình / lớn", ("cohen1988",)),
    ("plspredict", "PLSpredict: Q²predict > 0; so RMSE (MAE khi sai số dự báo lệch rõ) của PLS với mô hình tuyến tính "
                   "chuẩn trên từng chỉ báo của cấu trúc đích", ("shmueli2019",)),
)
CUM_NGUONG_SAP = HD.PLS_CUM_NGUONG  # một nguồn: bộ đọc SAP dùng đúng bộ cụm này để bật phân loại

# Dung sai kiểm chéo. Hai gói lặp PLS tới hội tụ (seminr tiêu chí dừng 10⁻⁷; cSEM đặt 10⁻¹⁰) trên CÙNG dữ liệu ⇒ đại
# lượng tất định trùng tới ~10⁻⁸ (đo 23/11/2026 trên corp_rep_data). 1e-5 là dung sai chặt (đủ cho 3 chữ số báo cáo).
DUNG_SAI_TAT_DINH = 1e-5
#: Ngưỡng Monte Carlo theo HỌ phép so (Bonferroni): một lượt so hàng trăm đại lượng bootstrap ⇒ z(1 − α_họ/(2m)) với
#: α_họ = 0,01 cho cả họ — giữ xác suất báo «lệch» giả của CẢ lượt ≤ 1% (z cố định 3,29 cho 150 phép so ⇒ ~14% lượt có
#: ít nhất một lệch giả). Mốc chuẩn chương 6 có đại lượng lệch 3,8 sai số Monte Carlo ở z cố định (đo 23/11/2026).
ALPHA_HO = 0.01
Z_MC = 3.29  # z(1 − 0,001/2) — chỉ dùng cho so một số đơn lẻ với sách (doi_chieu_sach)
DAI_LUONG = ("tai", "trong_so", "tin_cay", "htmt", "vif_muc", "vif_cau_truc", "duong_dan", "r2", "hieu_ung_tong",
             "tuong_quan_tho")


# ───────────────────────────── khối G1 → khuôn SAP §4 (run_g4_auto) ─────────────────────────────


def khoi_g1(meta: dict | None) -> dict | None:
    """gate_params.G1.pls_sem (mô hình lý thuyết PI chốt ở G1) — None khi đề tài không khai PLS-SEM."""
    k = (((meta or {}).get("gate_params") or {}).get("G1") or {}).get("pls_sem")
    return k if isinstance(k, dict) and k else None


def _so_vn(n) -> str:
    """Số nguyên theo quy ước văn bản tiếng Việt — hàm chung `quet_dien_sai_kieu.viet_so` (từ 10.000 nhóm nghìn)."""
    return QDSK.viet_so(int(n))


#: câu xử lý dữ liệu thiếu (khối SAP §4 và chiến lược §6 dùng CHUNG; bộ đọc nhận «listwise»/«mean replacement»)
CAU_THIEU = {"listwise": "loại khỏi phân tích ca thiếu bất kỳ chỉ báo nào của mô hình (phân tích ca đầy đủ, listwise)",
             "trung_binh": "điền khuyết ô thiếu bằng trung bình của chỉ báo (mean replacement)"}


def dong_sap(khoi: dict) -> list[str]:
    """Dòng SAP §4 của đề tài PLS-SEM — dựng từ khối G1 đã chốt; ô thiếu ⇒ [CẦN …] (G4-AUTO-10 chặn khoá khi còn ô)."""
    def can(viec: str) -> str:
        return f"[CẦN — {viec}; khai ở gate_params.G1.pls_sem]"

    ct = [c for c in khoi.get("cau_truc") or [] if isinstance(c, dict)]
    dd = [p for p in khoi.get("duong_dan") or [] if isinstance(p, (list, tuple)) and len(p) == 2]
    L = ["- **Phương pháp:** Mô hình phương trình cấu trúc bình phương tối thiểu từng phần (PLS-SEM, PLS path "
         "modeling; "
         f"Hair và cộng sự 2021 — doi:{NGUON['hair2021'][1]}): ước lượng bằng gói seminr của R, kiểm chéo độc "
         "lập bằng gói cSEM của R; sơ đồ trọng số trong theo đường dẫn (path weighting), tối đa 300 vòng lặp, "
         "tiêu chí dừng 10⁻⁷  ",
         "- **Vì sao chọn PLS-SEM thay CB-SEM:** "
         f"{khoi.get('bien_minh') or can('biện minh chọn PLS-SEM thay CB-SEM')}  ",
         "- **Mô hình đo lường (PLS-SEM):**  "]
    if not ct:
        L.append(f"  - {can('mô hình đo lường từng cấu trúc: mã, tên, chỉ báo, Mode A/B')}  ")
    for c in ct:
        kieu = ("cấu tạo (formative, Mode B)" if str(c.get("mode")).upper() == "B"
                else "kết quả (reflective, Mode A)")
        muc = ", ".join(f"`{m}`" for m in c.get("muc") or []) or can(f"chỉ báo của {c.get('ma')}")
        L.append(f"  - `{c.get('ma')}` — {c.get('ten') or can('tên cấu trúc')} — {kieu}: {muc}  ")
    L.append("- **Mô hình cấu trúc (PLS-SEM):** " + ("; ".join(f"`{a}` → `{b}`" for a, b in dd) if dd else
                                                   can("các đường dẫn giả thuyết")) + "  ")
    b = khoi.get("bootstrap")
    L.append("- **Bootstrap (PLS-SEM):** " + (f"{_so_vn(b)} mẫu lặp" if isinstance(b, int) and not isinstance(b, bool)
                                              else can("số mẫu bootstrap (Hair 2021 khuyến nghị 10.000 cho báo cáo "
                                                       "cuối)")) +
             "; KTC phân vị 95% hai phía cho hệ số đường dẫn, trọng số, tải và hiệu ứng tổng; KTC 90% hai phía cho "
             "HTMT; hạt giống cố định ghi ở mục phần mềm của SAP  ")
    pp = khoi.get("plspredict")
    if pp is False:
        L.append("- **PLSpredict (PLS-SEM):** không thực hiện  ")
    elif isinstance(pp, dict) and pp.get("dich"):
        L.append(f"- **PLSpredict (PLS-SEM):** k = {pp.get('k', 10)} phần, {pp.get('lap', 10)} lần lặp, tiền tố trực "
                 "tiếp; cấu trúc đích " + ", ".join(f"`{x}`" for x in pp["dich"]) + "  ")
    else:
        L.append("- **PLSpredict (PLS-SEM):** "
                 f"{can('cấu trúc đích, số phần k, số lần lặp — hoặc «không thực hiện»')}  ")
    th = khoi.get("du_lieu_thieu")
    L.append("- **Dữ liệu thiếu (PLS-SEM):** " + CAU_THIEU.get(th, can("listwise hoặc trung_binh")) + "  ")
    L.append("- **Ngưỡng đánh giá định trước (PLS-SEM):**  ")
    L += [f"  - {mo_ta} — " + "; ".join(trich(m) for m in nguon) + "  " for _k, mo_ta, nguon in DONG_NGUONG_SAP]
    L += [f"- **Kiểm nguồn ngưỡng:** {XAC_MINH_NGUON}  ",
          "- **Trình bày (Hair và cộng sự 2019):** mô hình đo lường trước (tải, độ tin cậy, AVE, HTMT; chỉ báo cấu "
          "tạo: "
          "VIF, trọng số), mô hình cấu trúc sau (VIF, hệ số đường dẫn + KTC 95%, R², f², PLSpredict); không báo "
          "p-value đơn độc; không sửa mô hình sau khi xem dữ liệu rồi báo như mô hình định trước  "]
    return L


# ─────────────────────── mô hình từ HỢP ĐỒNG SAP (bộ đọc SAP duy nhất: hop_dong_sap) ───────────────────────
# 24/11/2026: khối PLS-SEM của SAP §4 được ĐỌC MỘT LẦN ở hop_dong_sap.pls_sem_sap thành trường `pls_sem` của hợp đồng
# G4_SAP_CONTRACT_<mã>.json (băm vào chứng chỉ khoá G4); mô-đun này không còn biểu thức dò chữ SAP riêng.
kiem_mo_hinh = HD.kiem_mo_hinh_pls


def _mo_hinh(khoi: dict | None) -> dict | None:
    """Trường `pls_sem` của hợp đồng ⇒ mô hình; None ⇒ SAP không khai; khai mà hỏng ⇒ TuChoi (liệt kê hết)."""
    if khoi is None:
        return None
    if not isinstance(khoi, dict) or khoi.get("loi") or not isinstance(khoi.get("mo_hinh"), dict):
        loi = (khoi or {}).get("loi") if isinstance(khoi, dict) else None
        raise TuChoi("SAP khai PLS-SEM nhưng khối mô hình chưa đủ/không hợp lệ: " + "; ".join(loi or ["khối hỏng"]))
    return khoi["mo_hinh"]


def mo_hinh_hop_dong(hd: dict | None) -> dict | None:
    """Mô hình PLS-SEM từ HỢP ĐỒNG SAP (đã kiểm hợp lệ ở nơi gọi)."""
    return _mo_hinh(HD.truong(hd, "pls_sem"))


def doc_sap(van_ban_sap: str) -> dict | None:
    """Mô hình PLS-SEM từ VĂN BẢN SAP qua đúng hàm của hợp đồng (hop_dong_sap.pls_sem_van_ban) — cho đồ gá/bản nháp
    trong bộ nhớ. None ⇒ SAP không khai PLS-SEM. Khai mà thiếu/hỏng ⇒ TuChoi."""
    return _mo_hinh(HD.pls_sem_van_ban(van_ban_sap))


def la_pls_sap(van_ban_sap: str) -> bool:
    """SAP khai PLS-SEM (có khối máy đọc ở §4) — cùng hàm của hợp đồng."""
    return HD.pls_sem_van_ban(van_ban_sap) is not None


def noi_sinh(mh: dict) -> list[str]:
    return list(dict.fromkeys(b for _a, b in mh["duong_dan"]))


# ───────────────────────────── chuẩn bị tập phân tích ─────────────────────────────


def _ngoai_repo(p: Path) -> bool:
    try:
        p.resolve().relative_to(BASE.resolve())
        return False
    except ValueError:
        return True


def _ma_hop_le(td: dict) -> list[int] | None:
    """Mã hợp lệ của chỉ báo theo từ điển G5: thang thứ bậc (mã nguyên liền nhau từ mã nhỏ nhất; mã sau khoảng trống —
    8, 9… — là mã thiếu, cùng quy tắc phan_tich_nhan_to_r.thang_hop_le). None ⇒ biến số (không có lựa chọn)."""
    import phan_tich_nhan_to_r as NT  # noqa: PLC0415 — một quy tắc thang cho mọi phân tích bộ câu hỏi

    if not S.lua_chon(td):
        return None
    return NT.thang_hop_le(td)


def bien_bang1(d: Path) -> list[str]:
    """Biến của Bảng 1 theo ma trận mục tiêu–biến G3 (vai trò mo_ta · hiep_bien · ket_cuc_chinh) — không đoán."""
    import ma_tran_muc_tieu_bien as MT  # noqa: PLC0415

    vt = MT.vai_tro_tu_dong(MT.doc_ma_tran(d)[0] or [])
    return list(dict.fromkeys([*vt.get("mo_ta", []), *vt.get("hiep_bien", []),
                               *([vt["ket_cuc"]] if vt.get("ket_cuc") else [])]))


def chuan_bi_tap(study: str, csv_p: Path, muc: list[str], td: dict[str, dict], loc: str | None,
                 thieu: str, bien_t1: list[str] | None = None) -> tuple[list[list], dict]:
    """Bộ dữ liệu ⇒ (dòng gửi R, thống kê). Biến phái sinh + lọc quần thể bằng ĐÚNG hàm run_stats_analysis dùng; giá
    trị ngoài thang ⇒ thiếu; mã thiếu cấp dự án (`_ma-thieu-theo-bien.csv`, ĐÚNG luật áp mã của cau_noi_spss — BTR,
    KDD, 9…) ⇒ thiếu, đếm RIÊNG với ngoài thang; ô thiếu xử lý ĐÚNG cách SAP khai (listwise · trung bình chỉ báo)."""
    import bien_phai_sinh as BPS  # noqa: PLC0415
    import pandas as pd  # noqa: PLC0415

    d = S.thu_muc_de_tai(study)
    df = pd.read_csv(csv_p, encoding="utf-8-sig")
    n_dau = len(df)
    try:
        cot_loc = BPS.cot_cua_cay(BPS.phan_tich(loc)) if loc else []
        df, _ps = BPS.ap_dung_cho_phan_tich(df, d, study, [*muc, *cot_loc, *(bien_t1 or [])])
        if loc:
            mat_na, _ngay = BPS.loc_python(df, d, study, loc)
            df = df[mat_na.to_numpy()].copy()
    except (BPS.TuChoi, BPS.LoiCongThuc) as e:
        raise TuChoi(f"biến phái sinh/lọc quần thể — {e}") from e
    vang = [c for c in muc if c not in df.columns]
    if vang:
        raise TuChoi(f"bộ dữ liệu không có cột chỉ báo: {', '.join(vang)}")
    if not len(df):
        raise TuChoi(f"lọc quần thể «{loc}» không còn ca nào")
    hop_le = {c: _ma_hop_le(td[c]) for c in muc}
    sai_thang = [c for c, h in hop_le.items() if h is not None and len(h) < 2]
    if sai_thang:
        raise TuChoi(f"chỉ báo không có thang đọc được từ từ điển G5: {', '.join(sai_thang)}")
    ma_khai = S.doc_ma_thieu(d / "_ma-thieu-theo-bien.csv")
    ma_cot = {c: {m["ma"] for m in ma_khai if S._ap_cho_cot(m, c, c)} for c in muc}
    gt: list[list[float | None]] = []
    ngoai_thang: dict[str, int] = {}
    co_ma: dict[str, int] = {}
    for _, h in df.iterrows():
        o: list[float | None] = []
        for c in muc:
            tho = "" if pd.isna(h[c]) else str(h[c]).strip()
            if tho and (tho in ma_cot[c] or tho.removesuffix(".0") in ma_cot[c]):
                co_ma[c] = co_ma.get(c, 0) + 1
                o.append(None)
                continue
            v = pd.to_numeric(h[c], errors="coerce")
            if pd.isna(v) or (hop_le[c] is not None and (float(v) != int(v) or int(v) not in hop_le[c])):
                if not pd.isna(v):
                    ngoai_thang[c] = ngoai_thang.get(c, 0) + 1
                o.append(None)
            else:
                o.append(float(v))
        gt.append(o)
    thieu_moi = {c: sum(1 for r in gt if r[j] is None) for j, c in enumerate(muc)}
    giu = [i for i, r in enumerate(gt) if thieu != "listwise" or all(x is not None for x in r)]
    bang1 = None
    t1 = [b for b in (bien_t1 or []) if b in df.columns]
    if t1:  # Bảng 1 trên ĐÚNG quần thể phân tích (sau lọc + xử lý thiếu) — cùng hàm Bảng 1 của run_stats_analysis
        import run_stats_analysis as RSA  # noqa: PLC0415

        try:
            dft = df.iloc[giu].assign(_nhom_bang1=RSA.NHOM_TOAN_BO)
            bang1 = RSA.bang1_cho_tom_tat(RSA.table1_descriptive(dft, "_nhom_bang1",
                                                                 RSA.bien_bang1_mo_ta(dft, t1, ())))
        except (ZeroDivisionError, ValueError) as e:
            bang1 = {"error": str(e)}
    if thieu == "listwise":
        dong = [gt[i] for i in giu]
    else:
        tb = []
        for j in range(len(muc)):
            co = [r[j] for r in gt if r[j] is not None]
            if not co:
                raise TuChoi(f"chỉ báo {muc[j]} không có giá trị hợp lệ nào — không thay trung bình được")
            tb.append(sum(co) / len(co))
        dong = [[tb[j] if x is None else x for j, x in enumerate(r)] for r in gt]
    if len(dong) < 3:
        raise TuChoi(f"sau xử lý dữ liệu thiếu ({thieu}) chỉ còn {len(dong)} ca — không ước lượng được")
    return dong, {"n_ban_dau": n_dau, "n_sau_loc": len(df), "n_phan_tich": len(dong), "thieu_theo_chi_bao": thieu_moi,
                  "ngoai_thang_theo_chi_bao": ngoai_thang, "ma_thieu_khai_theo_chi_bao": co_ma,
                  "cach_xu_ly_thieu": thieu, "table1": bang1}


def ghi_csv(p: Path, tieu_de: list[str], dong: list[list]) -> None:
    with open(p, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(tieu_de)
        w.writerows([[repr(x) if isinstance(x, float) else x for x in r] for r in dong])


def cau_hinh_r(mh: dict, sha: str, *, kiem_cheo: bool = True, luot_mc: int = 5) -> dict:
    pp = mh.get("plspredict")
    return {"sha256_du_lieu": sha, "cau_truc": [{"ma": c["ma"], "muc": c["muc"], "mode": c["mode"]}
                                                for c in mh["cau_truc"]],
            "duong_dan": mh["duong_dan"], "bootstrap": mh["bootstrap"], "seed": mh["seed"], "alpha": mh["alpha"],
            "kiem_cheo": kiem_cheo,
            "plspredict": ({"k": pp["k"], "lap": pp["lap"], "dich": pp["dich"], "luot_mc": luot_mc} if pp else None)}


def chuan_bi(args) -> dict:
    """Mọi kiểm + tập phân tích + cấu hình + script R. Trả ngữ cảnh cho `chay`."""
    d = S.thu_muc_de_tai(args.study)
    if not d.is_dir():
        raise TuChoi(f"không có thư mục đề tài exports/{args.study}")
    sap_p = d / HD.ten_sap(args.study)
    if not sap_p.is_file():
        raise KhongDoDuoc(f"không thấy SAP {sap_p.name} — không biết mô hình đã khoá")
    hd, loi_hd = HD.doc(d, args.study)  # bộ đọc SAP DUY NHẤT; hợp đồng thiếu/cũ/lệch văn bản SAP ⇒ không chạy
    if loi_hd or hd is None:
        raise TuChoi("hợp đồng SAP máy đọc không dùng được — " + " | ".join(loi_hd[:3] or ["không đọc được"]))
    mh = mo_hinh_hop_dong(hd)
    if mh is None:
        raise TuChoi("SAP §4 không khai PLS-SEM (không có khối «Mô hình đo lường (PLS-SEM)») — không chạy PLS-SEM trái "
                     "SAP")
    if getattr(args, "pls_sem", None) not in (None, MA_DAC_TA):
        raise TuChoi(f"--pls-sem phải là {MA_DAC_TA}")
    if getattr(args, "bootstrap", None) is not None and args.bootstrap != mh["bootstrap"]:
        raise TuChoi(f"--bootstrap {args.bootstrap} lệch SAP ({mh['bootstrap']} mẫu lặp) — đặc tả phải theo SAP")
    thieu_sap = mh["du_lieu_thieu"]
    if getattr(args, "du_lieu_thieu", None) and args.du_lieu_thieu != thieu_sap:
        # độ nhạy SAP §9 (chay_sap_g6 chỉ cho phân tích KHÔNG phải chính khai du_lieu_thieu khác SAP §4)
        mh = {**mh, "du_lieu_thieu": args.du_lieu_thieu}
    if args.data:
        if not args.ban_nhap:
            raise TuChoi("--data chỉ dùng kèm --ban-nhap (bản nháp, KHÔNG phải dữ liệu khoá)")
        if not args.thu_muc_ra:
            raise TuChoi("--ban-nhap cần --thu-muc-ra (thư mục NGOÀI repo) — không ghi bản nháp vào exports/")
        ra = Path(args.thu_muc_ra).expanduser()
        if not _ngoai_repo(ra):
            raise TuChoi("--thu-muc-ra phải nằm NGOÀI repo")
        csv_p = Path(args.data).expanduser()
        if not csv_p.is_file():
            raise KhongDoDuoc(f"không thấy {csv_p}")
        man: dict = {}
        ban_nhap = True
        ra_tom, ra_r = ra, ra
    else:
        if args.ban_nhap or args.thu_muc_ra:
            raise TuChoi("--ban-nhap/--thu-muc-ra chỉ dùng kèm --data")
        import run_stats_analysis as RSA  # noqa: PLC0415 — kiểm G4 bằng ĐÚNG hàm G6 dùng

        ok, ly_do = RSA._g4_khoa_song(args.study)
        if not ok:
            raise TuChoi(f"SAP (G4) chưa khoá theo trạng thái sống — {ly_do}")
        csv_p, man = S.tim_du_lieu_khoa(args.study)
        ban_nhap = False
        ra_tom, ra_r = d, d / "r" / "pls_sem" / args.gate
    td_p = Path(args.dictionary).expanduser() if args.dictionary else d / f"G5_REDCap_dictionary_{args.study}.csv"
    if not td_p.is_file():
        raise KhongDoDuoc(f"không thấy từ điển G5 ({td_p.name}) — không xác định được thang và cột định danh")
    td = S.doc_tu_dien(td_p)
    muc = [m for c in mh["cau_truc"] for m in c["muc"]]
    import phan_tich_nhan_to_r as NT  # noqa: PLC0415

    NT.kiem_pii_cot(td, muc)
    dong, tk = chuan_bi_tap(args.study, csv_p, muc, td, args.loc, mh["du_lieu_thieu"], bien_bang1(d))
    ra_r.mkdir(parents=True, exist_ok=True)
    tep_dl, tep_kq, tep_ch = ra_r / "pls_sem_du_lieu.csv", ra_r / "pls_sem_ket_qua.json", ra_r / "pls_sem_cau_hinh.json"
    ghi_csv(tep_dl, muc, dong)
    sha_dl = S.sha256_tep(tep_dl)
    ch = cau_hinh_r(mh, sha_dl, luot_mc=args.luot_mc)
    tep_ch.write_text(json.dumps(ch, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    script = ra_r / f"{args.study}_pls_sem.R"
    script.write_text(R.kich_ban_pls_sem(), encoding="utf-8", newline="\n")
    canh_bao = []
    if ban_nhap:
        canh_bao.append("BẢN NHÁP — dữ liệu KHÔNG phải bộ đã khoá G5; không dùng làm kết quả đề tài")
    if not mh["nguong_sap"]:
        canh_bao.append("SAP không còn ghi đủ cụm ngưỡng định trước — chỉ in số, không phân loại")
    if mh["du_lieu_thieu"] != thieu_sap:
        canh_bao.append(f"ĐỘ NHẠY: ô thiếu xử lý theo «{mh['du_lieu_thieu']}» thay vì «{thieu_sap}» của SAP §4")
    if tk["ngoai_thang_theo_chi_bao"]:
        canh_bao.append("giá trị NGOÀI THANG từ điển G5 (không phải mã thiếu đã khai) bị coi là thiếu: "
                        + ", ".join(f"{c} {n} ô" for c, n in tk["ngoai_thang_theo_chi_bao"].items())
                        + " — đối chiếu phiếu gốc trước khi dùng kết quả")
    n_bo = tk["n_sau_loc"] - tk["n_phan_tich"]
    if n_bo:
        canh_bao.append(f"listwise bỏ {n_bo}/{tk['n_sau_loc']} ca thiếu ít nhất một chỉ báo")
    dac = {"study": args.study, "luc": datetime.now().astimezone().isoformat(timespec="seconds"), "ban_nhap": ban_nhap,
           "du_lieu_nguon": str(csv_p), "sha256_nguon": S.sha256_tep(csv_p), "tap_phan_tich": tep_dl.name,
           "sha256_tap": sha_dl, "tu_dien": td_p.name, "sap": {"tep": sap_p.name, "sha256": S.sha256_tep(sap_p),
                                                               "hop_dong": hd.get("sha256_hop_dong")},
           "mo_hinh": mh, "loc": args.loc, "thong_ke_tap": tk, "canh_bao": canh_bao, "disclaimer": CAN_KIEM}
    (ra_r / "pls_sem_dac_ta.json").write_text(json.dumps(dac, ensure_ascii=False, indent=1), encoding="utf-8",
                                              newline="\n")
    return {"dac": dac, "script": script, "tep_dl": tep_dl, "tep_kq": tep_kq, "tep_ch": tep_ch, "ra_r": ra_r,
            "ra_tom": ra_tom, "man": man, "csv_p": csv_p}


# ───────────────────────────── chạy R ─────────────────────────────


# Phiên bản tối thiểu CÓ CĂN CỨ: seminr NEWS.md 2.6.0 — trước 2.6.0 predict_pls(reps > 1) lặp lại kiểm định chéo trên
# CÙNG các fold (PLSpredict sai). cSEM không có lỗi tương đương được ghi nhận ⇒ không đặt sàn (đã đo với 0.7.1).
PHIEN_BAN_TOI_THIEU = {"seminr": "2.6.0"}


def _ban(v: str) -> tuple[int, ...]:
    return tuple(int(x) for x in re.findall(r"\d+", v)[:3])


def kiem_goi(rscript: Path) -> dict:
    """Phiên bản gói PLS-SEM cần (một lượt Rscript); gói dưới sàn PHIEN_BAN_TOI_THIEU tính là thiếu."""
    import tempfile  # noqa: PLC0415

    vb = ("for (g in c(" + ", ".join(R.chuoi_r(g) for g in R.GOI_CAN_PLS_SEM) + ")) cat(\"GOI=\", g, \"=\", if "
          "(requireNamespace(g, quietly = TRUE)) as.character(utils::packageVersion(g)) else \"\", "
          "\"\\n\", sep = \"\")")
    with tempfile.TemporaryDirectory(prefix="ebm-r-pls-") as tam:
        p = Path(tam) / "goi.R"
        p.write_text(vb + "\n", encoding="utf-8", newline="\n")
        ma, out, err = R.chay_r(rscript, [str(p)], thu_muc=Path(tam), thoi_han=300)
    goi: dict[str, str | None] = {}
    for dong in out.splitlines():
        if dong.startswith("GOI="):
            _, ten, ver = (dong.split("=", 2) + [""])[:3]
            goi[ten] = ver.strip() or None
    cu = [f"{g} {goi[g]} < {san}" for g, san in PHIEN_BAN_TOI_THIEU.items() if goi.get(g) and _ban(goi[g]) < _ban(san)]
    return {"ma": ma, "loi": (err or "").strip()[-600:], "goi": goi, "cu": cu,
            "thieu": [g for g in R.GOI_CAN_PLS_SEM if not goi.get(g)] + cu}


def chay_r_pls(rs: Path, c: dict, thoi_han: int) -> tuple[int, dict, str]:
    c["tep_kq"].unlink(missing_ok=True)  # kết quả lượt trước không được nhận nhầm
    ma, out, err = R.chay_r(rs, [str(c["script"]), str(c["tep_dl"]), str(c["tep_kq"]), str(c["tep_ch"])],
                            thu_muc=c["ra_r"], thoi_han=thoi_han)
    (c["ra_r"] / "pls_sem.log").write_text(out + ("\n--- stderr ---\n" + err if err else ""), encoding="utf-8",
                                           newline="\n")
    try:
        kq = json.loads(c["tep_kq"].read_text(encoding="utf-8"))
    except (OSError, ValueError):
        kq = {}
    loi = (err or out or "").strip()[-400:]
    return ma, kq, loi


# ───────────────────────────── kiểm chéo seminr ↔ cSEM ─────────────────────────────


def _so(x) -> float | None:
    return float(x) if isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) else None


def _phang(khoi: dict | None, ten: str) -> dict[str, float | None]:
    """{khoá: giá trị} của một đại lượng tất định, khoá dạng «CẤU_TRÚC/chỉ_báo» hoặc «A -> B»."""
    k = (khoi or {}).get(ten)
    if not isinstance(k, dict):
        return {}
    ra: dict[str, float | None] = {}
    for a, v in k.items():
        if isinstance(v, dict):
            for b, x in v.items():
                ra[f"{a}/{b}"] = _so(x)
        else:
            ra[a] = _so(v)
    return ra


def _pham_vi(mh: dict) -> dict:
    """Đại lượng nào có nghĩa để so, theo loại cấu trúc (Hair 2019): độ tin cậy/AVE/HTMT chỉ cho cấu trúc Mode A;
    Cronbach α và ρA cần ≥ 2 chỉ báo; VIF chỉ báo chỉ cho Mode B."""
    a_nhieu = {c["ma"] for c in mh["cau_truc"] if c["mode"] == "A" and len(c["muc"]) >= 2}
    a_tat_ca = {c["ma"] for c in mh["cau_truc"] if c["mode"] == "A"}
    b = {c["ma"] for c in mh["cau_truc"] if c["mode"] == "B"}
    return {"a_nhieu": a_nhieu, "a": a_tat_ca, "b": b}


def _giu(ten: str, khoa: str, pv: dict) -> bool:
    if ten == "tin_cay":
        ct, chi_so = khoa.split("/", 1)
        if ct not in pv["a"]:
            return False
        return ct in pv["a_nhieu"] or chi_so in ("rho_c", "ave")
    if ten == "htmt":
        a, b = [x.strip() for x in khoa.split("|")]
        return a in pv["a"] and b in pv["a"]
    if ten == "vif_muc":
        return khoa.split("/", 1)[0] in pv["b"]
    return True


SAN_MC = 1e-9  # sàn tuyệt đối của dung sai Monte Carlo (đại lượng hằng như tải của cấu trúc một chỉ báo — nhiễu 1e-15)


def _mcse_ktc(sd: float, alpha: float, b: int) -> float:
    """Sai số Monte Carlo của một cận KTC phân vị khi KHÔNG có phân phối bootstrap (xấp xỉ chuẩn):
    SD·√(p(1−p)/B) / φ(z_p), p = α/2. Có phân phối ⇒ dùng độ thưa thực nghiệm (_tol_ktc)."""
    p = alpha / 2
    z = 1.959963984540054 if abs(alpha - 0.05) < 1e-12 else _z(1 - p)
    phi = math.exp(-z * z / 2) / math.sqrt(2 * math.pi)
    return sd * math.sqrt(p * (1 - p) / b) / phi


def _z(q: float) -> float:
    from statistics import NormalDist  # noqa: PLC0415

    return NormalDist().inv_cdf(q)


def z_ho(m: int) -> float:
    """z hai phía cho họ m phép so (Bonferroni, α_họ = ALPHA_HO)."""
    return _z(1 - ALPHA_HO / (2 * max(m, 1)))


def t_ho(m: int, df: int) -> float:
    """t hai phía cho họ m phép so với df bậc tự do (PLSpredict: J lượt mỗi gói ⇒ SD ước lượng từ ít lượt)."""
    try:
        from scipy import stats as st  # noqa: PLC0415

        return float(st.t.ppf(1 - ALPHA_HO / (2 * max(m, 1)), df))
    except Exception:  # noqa: BLE001 — không có scipy ⇒ chuẩn (thiên hẹp — báo lệch nhiều hơn, không bao giờ ít hơn)
        return z_ho(m)


def doi_chieu(kq: dict, mh: dict) -> dict:
    """So từng đại lượng seminr ↔ cSEM. Trả {trang_thai, dem, dong[]}. Mỗi dòng: {nhom, ten, seminr, csem, chenh,
    dung_sai, ket (KHOP · LECH · KHONG_SO), ly_do}."""
    s, c = kq.get("seminr") or {}, kq.get("csem") or {}
    dong: list[dict] = []
    if not s or not c:
        ly_do = (kq.get("loi") or {}).get("csem") if s else (kq.get("loi") or {}).get("seminr")
        return {"trang_thai": "KHONG_DO_DUOC", "dem": {}, "dong": [],
                "ly_do": f"{'cSEM' if s else 'seminr'} không ra kết quả: {ly_do or 'không rõ'}"}
    pv = _pham_vi(mh)
    for ten in DAI_LUONG:
        ps, pc = _phang(s, ten), _phang(c, ten)
        for khoa in sorted(set(ps) | set(pc)):
            if not _giu(ten, khoa, pv):
                continue
            a, b = ps.get(khoa), pc.get(khoa)
            d = {"nhom": ten, "ten": khoa, "seminr": a, "csem": b}
            if a is None or b is None:
                d |= {"ket": "KHONG_SO", "ly_do": "chỉ một gói ra số"}
            else:
                tol = DUNG_SAI_TAT_DINH * (max(1.0, abs(a)) if ten.startswith("vif") else 1.0)
                d |= {"chenh": abs(a - b), "dung_sai": tol, "ket": "KHOP" if abs(a - b) <= tol else "LECH"}
            dong.append(d)
    # bootstrap — sai số chuẩn và cận KTC theo sai số Monte Carlo (hai bộ sinh số độc lập)
    bs, bc = s.get("bootstrap") or {}, c.get("bootstrap") or {}
    mc, mcc = s.get("bootstrap_mc") or {}, c.get("bootstrap_mc") or {}
    bt_mc: list[dict] = []
    b1, b2 = _so(bs.get("B_dung")) or _so(bs.get("B_yeu_cau")), _so(bc.get("so_hop_le")) or _so(bc.get("B_yeu_cau"))
    alpha = _so(bs.get("alpha")) or 0.05
    for nhom in ("duong_dan", "trong_so", "tai", "hieu_ung_tong", "htmt_ktc90"):
        for khoa in sorted(set(bs.get(nhom) or {}) | set(bc.get(nhom) or {})):
            if nhom == "htmt_ktc90":
                a_, b_ = [x.strip() for x in khoa.split("->")]
                if not (a_ in pv["a"] and b_ in pv["a"]):
                    continue
            if nhom in ("trong_so", "tai"):
                muc_, ct_ = [x.strip() for x in khoa.split("->")]
                if (nhom == "trong_so") != (ct_ in pv["b"]):
                    continue  # trọng số chỉ cho Mode B, tải chỉ cho Mode A (Hair 2019)
            xs, xc = (bs.get(nhom) or {}).get(khoa) or {}, (bc.get(nhom) or {}).get(khoa) or {}
            sd_s = _so(xs.get("sd"))
            al = 0.10 if nhom == "htmt_ktc90" else alpha
            # HTMT của cSEM lấy mẫu lại RIÊNG (số mẫu hợp lệ riêng) — sai số Monte Carlo theo đúng số đó
            b2_ = (_so(bc.get("so_hop_le_htmt")) or b2) if nhom == "htmt_ktc90" else b2
            if not xs or not xc or not b1 or not b2_:
                dong.append({"nhom": f"bootstrap/{nhom}", "ten": khoa, "ket": "KHONG_SO", "ly_do": "chỉ một gói ra số"})
                continue
            sd_c = _so(xc.get("sd"))
            sd_ref = sd_s if sd_s is not None else None
            if sd_ref is None:  # HTMT của cSEM không trả SD ⇒ ước lượng SD từ độ rộng KTC seminr
                ks = xs.get("ktc") or [None, None]
                sd_ref = (ks[1] - ks[0]) / (2 * _z(1 - al / 2)) if None not in ks else None
            m_ = (mc.get(nhom) or {}).get(khoa)
            if m_ is None and nhom == "htmt_ktc90":  # mảng HTMT của seminr có thể giữ tam giác kia
                m_ = (mc.get(nhom) or {}).get(" -> ".join(reversed([x.strip() for x in khoa.split("->")])))
            m_c = (mcc.get(nhom) or {}).get(khoa)
            kurt = _so((m_ or {}).get("kurt_du"))
            kurt_c = _so((m_c or {}).get("kurt_du"))
            if sd_s is not None and sd_c is not None:
                # Var(SD_s − SD_c) = Var(SD_s) + Var(SD_c), Var(SD) ≈ SD²(2 + κ)/(4B) với SD và κ (độ nhọn dư) của
                # CHÍNH phân phối bootstrap từng gói — một mẫu lặp đổi dấu cấu trúc ở một gói làm κ gói đó rất lớn và SD
                # của nó kém ổn định (đo 23/11/2026, nhóm nam 144 ca: 1/5000 mẫu lặp cSEM đổi dấu TT, seminr 0)
                he_s = max(2 + (kurt if kurt is not None else 0.0), 0.0)
                he_c = max(2 + (kurt_c if kurt_c is not None else (kurt if kurt is not None else 0.0)), 0.0)
                bt_mc.append({"nhom": f"bootstrap/{nhom}", "ten": f"{khoa} · SD", "seminr": sd_s, "csem": sd_c,
                              "chenh": abs(sd_s - sd_c),
                              "mcse": math.sqrt(sd_s ** 2 * he_s / (4 * b1) + sd_c ** 2 * he_c / (4 * b2_))})
            for i, nhan in ((0, "cận dưới"), (1, "cận trên")):
                ks, kc_ = (xs.get("ktc") or [None, None]), (xc.get("ktc") or [None, None])
                if ks[i] is None or kc_[i] is None or sd_ref is None:
                    continue
                thua = _so(((m_ or {}).get("thua") or [None, None])[i])
                thua_c = _so(((m_c or {}).get("thua") or [None, None])[i])
                if thua is not None:  # MCSE phân vị = s(p)·√(p(1−p)/B) — độ thưa thực nghiệm của TỪNG gói
                    p_ = al / 2
                    tc = thua_c if thua_c is not None else thua  # HTMT: cSEM không trả mẫu lặp ⇒ cùng độ thưa
                    mcse = math.sqrt(p_ * (1 - p_) * (thua ** 2 / b1 + tc ** 2 / b2_))
                else:
                    mcse = math.sqrt(_mcse_ktc(sd_ref, al, int(b1)) ** 2 + _mcse_ktc(sd_ref, al, int(b2_)) ** 2)
                bt_mc.append({"nhom": f"bootstrap/{nhom}", "ten": f"{khoa} · KTC {nhan}", "seminr": ks[i],
                              "csem": kc_[i], "chenh": abs(ks[i] - kc_[i]), "mcse": mcse})
    zb = z_ho(len(bt_mc))
    for d in bt_mc:
        d["dung_sai"] = zb * d.pop("mcse") + SAN_MC
        d["ket"] = "KHOP" if d["chenh"] <= d["dung_sai"] else "LECH"
        d["z_ho"] = round(zb, 3)
    dong += bt_mc
    # PLSpredict — PLS RMSE/MAE (cùng định nghĩa: tiền tố trực tiếp) theo sai số Monte Carlo của J lượt độc lập
    ps_, pc_ = s.get("plspredict") or {}, c.get("plspredict") or {}
    pp_mc: list[dict] = []
    if ps_ or pc_:
        # cùng định nghĩa: lượt r = 1 (luot_doi_chieu); không có thì chỉ dùng «luot» khi SAP đặt 1 lần lặp
        def _luot(p_: dict) -> list:
            if p_.get("luot_doi_chieu"):
                return p_["luot_doi_chieu"]
            return (p_.get("luot") or []) if int(_so(p_.get("lap")) or 1) == 1 else []

        for chi_so in ("rmse_pls", "mae_pls"):
            for m in (ps_.get("muc") or pc_.get("muc") or []):
                va = [_so((l_.get(chi_so) or {}).get(m)) for l_ in _luot(ps_)]
                vb = [_so((l_.get(chi_so) or {}).get(m)) for l_ in _luot(pc_)]
                va, vb = [x for x in va if x is not None], [x for x in vb if x is not None]
                if len(va) < 2 or len(vb) < 2:
                    dong.append({"nhom": "plspredict", "ten": f"{m} · {chi_so}", "ket": "KHONG_SO",
                                 "ly_do": "cần ≥ 2 lượt độc lập CÙNG định nghĩa (1 lần lặp) mỗi gói để ước lượng sai "
                                          "số Monte Carlo — " + KHAC_DINH_NGHIA_LAP})
                    continue
                ma_, mb_ = sum(va) / len(va), sum(vb) / len(vb)
                sa = math.sqrt(sum((x - ma_) ** 2 for x in va) / (len(va) - 1))
                sb = math.sqrt(sum((x - mb_) ** 2 for x in vb) / (len(vb) - 1))
                pp_mc.append({"nhom": "plspredict", "ten": f"{m} · {chi_so}", "seminr": ma_, "csem": mb_,
                              "chenh": abs(ma_ - mb_), "mcse": math.sqrt(sa ** 2 / len(va) + sb ** 2 / len(vb)),
                              "df": len(va) + len(vb) - 2})
        for d in pp_mc:
            tq = t_ho(len(pp_mc), d.pop("df"))
            d["dung_sai"] = tq * d.pop("mcse") + SAN_MC
            d["ket"] = "KHOP" if d["chenh"] <= d["dung_sai"] else "LECH"
            d["t_ho"] = round(tq, 3)
        dong += pp_mc
        dong.append({"nhom": "plspredict", "ten": "mô hình tuyến tính chuẩn (LM) · RMSE/MAE", "ket": "KHONG_SO",
                     "ly_do": KHAC_DINH_NGHIA_LM})
        dong.append({"nhom": "plspredict", "ten": "Q²predict", "ket": "KHONG_SO", "ly_do": KHAC_DINH_NGHIA_Q2})
    dem = {k: sum(1 for x in dong if x["ket"] == k) for k in ("KHOP", "LECH", "KHONG_SO")}
    tt = "LECH" if dem["LECH"] else ("KHOP" if dem["KHOP"] else "KHONG_DO_DUOC")
    return {"trang_thai": tt, "dem": dem, "dong": dong}


KHAC_DINH_NGHIA_LM = ("khác định nghĩa — seminr hồi quy mỗi chỉ báo của cấu trúc đích trên chỉ báo của các cấu trúc "
                      "TIỀN TỐ TRỰC TIẾP (predict_DA, ?seminr::predict_pls); cSEM benchmark «lm» hồi quy trên chỉ báo "
                      "của MỌI cấu trúc ngoại sinh (?cSEM::predict) — hai mô hình chuẩn khác nhau, không so số")
KHAC_DINH_NGHIA_LAP = ("khi lặp r > 1, seminr lấy trung bình DỰ BÁO qua các lần lặp rồi tính RMSE/MAE (mean_over_reps "
                       "trong seminr::predict_pls), cSEM tính chỉ số từng lần lặp rồi lấy trung bình (cSEM::predict) — "
                       "chỉ so được ở 1 lần lặp")
KHAC_DINH_NGHIA_Q2 = ("chỉ cSEM tính Q²predict theo định nghĩa Shmueli 2019 (so với trung bình mẫu huấn luyện); seminr "
                      "2.6.0 không tính đại lượng này — không có bản thứ hai để so")


# ───────────────────────────── đánh giá theo ngưỡng định trước ─────────────────────────────


def _muc_vif(v: float | None) -> str | None:
    if v is None:
        return None
    lo, hi = NGUONG["vif"]
    return "dat" if v < lo else ("can_xem" if v < hi else "khong_dat")


def _muc_r2(v: float | None) -> str | None:
    if v is None:
        return None
    y, tb, m = NGUONG["r2"]
    return "manh" if v >= m else ("trung_binh" if v >= tb else ("yeu" if v >= y else "rat_yeu"))


def _muc_f2(v: float | None) -> str | None:
    if v is None:
        return None
    nho, tb, lon = NGUONG["f2"]
    return "lon" if v >= lon else ("trung_binh" if v >= tb else ("nho" if v >= nho else "khong_dang_ke"))


def ktc_fisher(r: float | None, n, muc: float = 0.95) -> list | None:
    """KTC của hệ số tương quan theo biến đổi Fisher z: tanh(atanh r ± z₁₋α/₂/√(n − 3)); None khi thiếu r/n hoặc
    |r| ≥ 1 hoặc n ≤ 3."""
    n = _so(n)
    if r is None or n is None or n <= 3 or abs(r) >= 1:
        return None
    h = _z(1 - (1 - muc) / 2) / math.sqrt(n - 3)
    return [math.tanh(math.atanh(r) - h), math.tanh(math.atanh(r) + h)]


def danh_gia(s: dict, mh: dict) -> dict:
    """Bảng đánh giá theo Hair 2019 trên kết quả seminr. Phân loại chỉ khi SAP ghi đủ ngưỡng (mh['nguong_sap'])."""
    pv = _pham_vi(mh)
    co_pl = bool(mh.get("nguong_sap"))
    bs = s.get("bootstrap") or {}

    def pl(x):
        return x if co_pl else None

    do_luong_a, do_luong_b, cau_truc = [], [], []
    for c in mh["cau_truc"]:
        t = c["ma"]
        tc = (s.get("tin_cay") or {}).get(t) or {}
        if c["mode"] == "A":
            for m in c["muc"]:
                tai = _so(((s.get("tai") or {}).get(t) or {}).get(m))
                ktc = ((bs.get("tai") or {}).get(f"{m} -> {t}") or {}).get("ktc")
                do_luong_a.append({"cau_truc": t, "chi_bao": m, "tai": tai, "ktc": ktc,
                                   "dat": pl(None if tai is None or len(c["muc"]) == 1 else tai >= NGUONG["tai"])})
            nhieu = t in pv["a_nhieu"]
            lo, hi = NGUONG["tin_cay"]
            muc_tc = {k: _so(tc.get(k)) for k in ("alpha", "rho_a", "rho_c", "ave")}
            do_luong_a.append({"cau_truc": t, "tong_hop": True, "mot_chi_bao": not nhieu, **muc_tc,
                               "dat_tin_cay": pl(None if not nhieu else all(
                                   v is not None and lo <= v <= hi for v in (muc_tc["alpha"], muc_tc["rho_a"],
                                                                             muc_tc["rho_c"]))),
                               "dat_ave": pl(None if not nhieu or muc_tc["ave"] is None
                                             else muc_tc["ave"] >= NGUONG["ave"])})
        else:
            for m in c["muc"]:
                w = _so(((s.get("trong_so") or {}).get(t) or {}).get(m))
                tai = _so(((s.get("tai") or {}).get(t) or {}).get(m))
                vif = _so(((s.get("vif_muc") or {}).get(t) or {}).get(m))
                ktc = ((bs.get("trong_so") or {}).get(f"{m} -> {t}") or {}).get("ktc")
                y_nghia = None if not ktc or None in ktc else not (ktc[0] <= 0 <= ktc[1])
                do_luong_b.append({"cau_truc": t, "chi_bao": m, "trong_so": w, "ktc": ktc, "y_nghia": y_nghia,
                                   "tai": tai, "vif": vif, "muc_vif": pl(_muc_vif(vif)),
                                   "giu": pl(None if y_nghia is None else (y_nghia or (tai is not None and
                                                                                   tai >= NGUONG["tai_cau_tao"])))})
    htmt = []
    for khoa, v in (s.get("htmt") or {}).items():
        a, b = [x.strip() for x in khoa.split("|")]
        if a in pv["a"] and b in pv["a"]:
            ktc = ((bs.get("htmt_ktc90") or {}).get(f"{a} -> {b}") or {}).get("ktc")
            htmt.append({"cap": [a, b], "htmt": _so(v), "ktc90": ktc,
                         "dat": pl(None if v is None else (v < NGUONG["htmt"] and (not ktc or ktc[1] is None or
                                                                                    ktc[1] < NGUONG["htmt"])))})
    for y in noi_sinh(mh):
        r2 = (s.get("r2") or {}).get(y) or {}
        for a, b in mh["duong_dan"]:
            if b != y:
                continue
            k = f"{a} -> {b}"
            bd = (bs.get("duong_dan") or {}).get(k) or {}
            ktc = bd.get("ktc")
            vif = _so(((s.get("vif_cau_truc") or {}).get(y) or {}).get(a))
            f2 = _so(((s.get("duong_dan") or {}).get(k) or {}).get("f2"))
            r_tho = _so((s.get("tuong_quan_tho") or {}).get(k))
            cau_truc.append({"duong_dan": k, "r_tho": r_tho, "ktc_r_tho": ktc_fisher(r_tho, s.get("n_phan_tich")),
                             "he_so": _so(((s.get("duong_dan") or {}).get(k) or {}).get("he_so")),
                             "sd": _so(bd.get("sd")), "t": _so(bd.get("t")), "ktc": ktc,
                             "y_nghia": None if not ktc or None in ktc else not (ktc[0] <= 0 <= ktc[1]),
                             "f2": f2, "muc_f2": pl(_muc_f2(f2)), "vif": vif, "muc_vif": pl(_muc_vif(vif)),
                             "noi_sinh": y, "r2": _so(r2.get("r2")), "r2_hc": _so(r2.get("r2_hc")),
                             "muc_r2": pl(_muc_r2(_so(r2.get("r2"))))})
    pp = s.get("plspredict")
    du_bao = None
    if isinstance(pp, dict) and pp.get("luot"):
        l0 = pp["luot"][0]
        du_bao = {"k": pp.get("k"), "lap": pp.get("lap"), "cach": pp.get("cach"), "dich": pp.get("dich"),
                  "chi_bao": [{"chi_bao": m, **{k: _so((l0.get(k) or {}).get(m)) for k in
                                                 ("rmse_pls", "rmse_lm", "mae_pls", "mae_lm")}}
                              for m in pp.get("muc") or []]}
        for x in du_bao["chi_bao"]:
            x["pls_tot_hon_lm_rmse"] = (None if None in (x["rmse_pls"], x["rmse_lm"])
                                        else x["rmse_pls"] < x["rmse_lm"])
    return {"phan_loai": co_pl, "do_luong_ket_qua": do_luong_a, "do_luong_cau_tao": do_luong_b, "htmt": htmt,
            "cau_truc": cau_truc, "plspredict": du_bao}


# ───────────────────────────── tóm tắt + báo cáo ─────────────────────────────


def so3(x) -> str:
    """Một số của bảng trình bày theo ĐÚNG cách bản thảo G7 in số G6 (`run_g7_auto.hien_so_g6` = `viet_hoa_so` trên
    repr của giá trị): dấu phẩy thập phân, tối đa 4 chữ số lẻ, số nguyên từ 5 chữ số nhóm nghìn. Vì vậy tự kiểm số của
    G7 (`kiem_so_trich_g6`) đối chiếu được từng số của bảng với GIÁ TRỊ trong tóm tắt G6 (không với chính bảng)."""
    if _so(x) is None:
        return "—"
    if isinstance(x, int):  # số đếm (n, số mẫu lặp) — JSON ghi «5000», không «5000.0»
        return QDSK.viet_so(x)
    return QDSK.viet_hoa_so(repr(float(x)))  # «1.0» ⇒ «1,0» như hien_so_g6 in giá trị JSON 1.0


def ktc3(k) -> str:
    """Khoảng tin cậy: «a–b»; có cận âm ⇒ «a đến b» (gạch khoảng đặt sát dấu trừ «-0,063–0,252» dễ đọc nhầm dấu)."""
    if not (isinstance(k, (list, tuple)) and len(k) == 2):
        return "—"
    a, b = so3(k[0]), so3(k[1])
    return f"{a} đến {b}" if a.startswith("-") or b.startswith("-") else f"{a}–{b}"


def lam_tom_tat(args, c: dict, kq: dict, ma_r: int, loi_r: str, chay_bang: str) -> tuple[dict, dict, int]:
    """(tóm tắt G6, kiểm chéo, mã thoát)."""
    dac, mh = c["dac"], c["dac"]["mo_hinh"]
    loi = dict(kq.get("loi") or {})
    if ma_r not in (0,) and not loi:
        loi["r"] = f"Rscript mã {ma_r}: {loi_r or '(không có thông điệp)'}"
    s = kq.get("seminr") or {}
    kc = doi_chieu(kq, mh) if s else {"trang_thai": "KHONG_DO_DUOC", "dem": {}, "dong": [],
                                       "ly_do": f"seminr không ra kết quả: {loi.get('seminr') or loi.get('r')}"}
    dg = danh_gia(s, mh) if s else None
    q2 = None
    pc = (kq.get("csem") or {}).get("plspredict") or {}
    if pc.get("luot"):
        q2 = (pc["luot"][0] or {}).get("q2_predict")
    luc = datetime.now().isoformat(timespec="seconds")
    dd_s = {k: v for k, v in (s.get("doi_dau_bootstrap") or {}).items() if _so(v)}
    canh_bao = list(dac["canh_bao"])
    if dd_s:  # phân tích CHÍNH (seminr) có mẫu lặp đổi dấu cấu trúc ⇒ SD/t của cấu trúc đó kém tin cậy
        canh_bao.append("bootstrap seminr: " + ", ".join(f"{k} đổi dấu {int(v)}/{mh['bootstrap']} mẫu lặp"
                                                         for k, v in dd_s.items())
                        + " — SD và t của tải/đường dẫn liên quan bị thổi phồng; ý nghĩa đọc theo KTC phân vị "
                          "bootstrap")
    pls = {"sap": {**dac["sap"], "seed": mh["seed"], "bootstrap": mh["bootstrap"], "alpha": mh["alpha"],
                   "du_lieu_thieu": mh["du_lieu_thieu"], "nguong_sap": mh["nguong_sap"]},
           "mo_hinh": {"cau_truc": mh["cau_truc"], "duong_dan": mh["duong_dan"], "plspredict": mh["plspredict"]},
           "thong_ke_tap": dac["thong_ke_tap"], "seminr": s or None, "danh_gia": dg,
           "q2_predict_csem": q2, "ghi_chu_q2": KHAC_DINH_NGHIA_Q2 if q2 else None,
           "trinh_bay_md": trinh_bay_ket_qua(dg, q2, kc),
           "phien_ban": {"r": kq.get("phien_ban_r"), **(kq.get("goi") or {})}, "chay_bang": chay_bang,
           "nguong": NGUONG if mh["nguong_sap"] else None,
           "nguon": {k: {"trich": t, "doi": d} for k, (t, d) in NGUON.items()}, "xac_minh_nguon": XAC_MINH_NGUON,
           "doi_dau_bootstrap": {"seminr": s.get("doi_dau_bootstrap"),
                                 "csem": (kq.get("csem") or {}).get("doi_dau_bootstrap")},
           # số mẫu lặp cSEM có tương quan chỉ báo ≤ 0 trong cặp HTMT — nơi định nghĩa HTMT của hai gói khác nhau
           "htmt_mau_tuong_quan_am": {k: (v or {}).get("so_mau_tuong_quan_am") for k, v in (
               ((kq.get("csem") or {}).get("bootstrap") or {}).get("htmt_ktc90") or {}).items()},
           "canh_bao_r": kq.get("canh_bao") or [], "loi": loi}
    tom = {"gate": args.gate, "study": args.study, "loai_phan_tich": LOAI_PHAN_TICH,
           "n_total": dac["thong_ke_tap"]["n_phan_tich"], "ban_nhap": dac["ban_nhap"],
           "dac_ta_phan_tich": {"pls_sem": MA_DAC_TA, "bootstrap_pls": mh["bootstrap"], "seed": mh["seed"],
                                "loc": dac["loc"], "du_lieu_thieu": mh["du_lieu_thieu"]},
           "pls_sem": pls, "kiem_cheo": {"phan_mem": "cSEM", "trang_thai": kc["trang_thai"], "dem": kc["dem"],
                                         "tep": f"{args.gate}_kiem_cheo.json"},
           "du_lieu": c["csv_p"].name, "chay_luc": luc, "generated": luc, "canh_bao": canh_bao,
           **({"table1": dac["thong_ke_tap"]["table1"]} if dac["thong_ke_tap"].get("table1") else {}),
           "disclaimer": CAN_KIEM}
    man = c["man"] or {}
    if not dac["ban_nhap"]:  # cùng khoá nguồn gốc với tóm tắt run_stats_analysis (G7 chỉ nhận tóm tắt đúng bản khoá)
        tom["data_lock"] = {"locked_dataset_path": man.get("locked_dataset_path"), "sha256": man.get("sha256"),
                            "lock_date": man.get("lock_date"), "approved_by": man.get("approved_by"),
                            "sap_version": man.get("sap_version")}
    ma = MA_OK
    if loi.get("seminr") or loi.get("du_lieu") or not s:
        ma = MA_LECH
    elif kc["trang_thai"] == "LECH":
        ma = MA_LECH
    elif kc["trang_thai"] != "KHOP":
        ma = MA_KHONG_DO
    return tom, kc, ma


def trinh_bay_ket_qua(dg: dict | None, q2: dict | None, kc: dict) -> list[str]:
    """Dòng Markdown trình bày Kết quả PLS-SEM theo thứ tự Hair và cộng sự 2019 (mô hình đo lường trước, cấu trúc sau)
    — số in bằng `so3` (đúng cách `run_g7_auto.hien_so_g6` in giá trị: dấu phẩy thập phân, tối đa 4 chữ số lẻ).
    G6 dựng MỘT lần, ghi vào tóm tắt; G7 CHÉP NGUYÊN VĂN các dòng này sau khi đối chiếu từng số ở hàng dữ liệu với
    giá trị tính của tóm tắt (`run_g7_auto._khoi_pls_sem_g6`) — không làm tròn/tính lại ở G7."""
    if not dg:
        return []
    L = [f"Trình bày theo Hair và cộng sự 2019 ({trich('hair2019')}): mô hình đo lường trước, mô hình cấu trúc sau; "
         "KTC là KTC phân vị bootstrap.", ""]
    ket = [x for x in dg["do_luong_ket_qua"] if not x.get("tong_hop")]
    tong = {x["cau_truc"]: x for x in dg["do_luong_ket_qua"] if x.get("tong_hop")}
    if ket:
        L += ["**Mô hình đo lường — chỉ báo kết quả (Mode A)**", "",
              "| Cấu trúc | Chỉ báo | Tải (KTC 95%) | Cronbach α | ρA | ρC | AVE |", "|---|---|---|---|---|---|---|"]
        da = set()
        for x in ket:
            t = tong.get(x["cau_truc"]) or {}
            dau = x["cau_truc"] not in da
            da.add(x["cau_truc"])
            mot = t.get("mot_chi_bao")
            L.append(f"| {x['cau_truc'] if dau else ''} | {x['chi_bao']} | {so3(x['tai'])} ({ktc3(x['ktc'])}) | "
                     + (" | ".join(["—" if mot else so3(t.get("alpha")), "—" if mot else so3(t.get("rho_a")),
                                    so3(t.get("rho_c")), so3(t.get("ave"))]) if dau else " |  |  | ") + " |")
        L.append("")
    if dg["htmt"]:
        L += ["**Giá trị phân biệt — HTMT**", "", "| Cặp cấu trúc | HTMT (KTC 90%) |", "|---|---|"]
        L += [f"| {x['cap'][0]} – {x['cap'][1]} | {so3(x['htmt'])} ({ktc3(x['ktc90'])}) |" for x in dg["htmt"]]
        L.append("")
    if dg["do_luong_cau_tao"]:
        L += ["**Mô hình đo lường — chỉ báo cấu tạo (Mode B)**", "",
              "| Cấu trúc | Chỉ báo | VIF | Trọng số (KTC 95%) | Tải |", "|---|---|---|---|---|"]
        L += [f"| {x['cau_truc']} | {x['chi_bao']} | {so3(x['vif'])} | {so3(x['trong_so'])} ({ktc3(x['ktc'])}) | "
              f"{so3(x['tai'])} |" for x in dg["do_luong_cau_tao"]]
        L.append("")
    L += ["**Mô hình cấu trúc** — β: hệ số đường dẫn, ước lượng hiệu chỉnh cho các cấu trúc tiền tố còn lại của cùng "
          "cấu trúc nội sinh (KTC 95% bootstrap phân vị); r: tương quan thô, chưa hiệu chỉnh, giữa điểm hai cấu trúc "
          "(KTC 95% theo biến đổi Fisher z)", "",
          "| Đường dẫn | r thô (KTC 95%) | β hiệu chỉnh (KTC 95%) | f² | VIF |", "|---|---|---|---|---|"]
    L += [f"| {x['duong_dan'].replace(' -> ', ' → ')} | {so3(x.get('r_tho'))} ({ktc3(x.get('ktc_r_tho'))}) | "
          f"{so3(x['he_so'])} ({ktc3(x['ktc'])}) | {so3(x['f2'])} | {so3(x['vif'])} |" for x in dg["cau_truc"]]
    L += ["", "| Cấu trúc nội sinh | R² | R² hiệu chỉnh |", "|---|---|---|"]
    da = set()
    for x in dg["cau_truc"]:
        if x["noi_sinh"] not in da:
            da.add(x["noi_sinh"])
            L.append(f"| {x['noi_sinh']} | {so3(x['r2'])} | {so3(x['r2_hc'])} |")
    pp = dg.get("plspredict")
    if pp:
        q2 = q2 or {}
        L += ["", f"**Khả năng dự báo ngoài mẫu — PLSpredict** (k = {pp['k']} phần, {pp['lap']} lần lặp; Shmueli và "
                  "cộng sự 2019)", "",
              "| Chỉ báo | RMSE PLS | RMSE mô hình tuyến tính | MAE PLS | MAE mô hình tuyến tính | Q²predict |",
              "|---|---|---|---|---|---|"]
        L += [f"| {x['chi_bao']} | {so3(x['rmse_pls'])} | {so3(x['rmse_lm'])} | {so3(x['mae_pls'])} | "
              f"{so3(x['mae_lm'])} | {so3(q2.get(x['chi_bao']))} |" for x in pp["chi_bao"]]
    dem = kc.get("dem") or {}
    L += ["", f"Kiểm chéo bằng cSEM (bản cài đặt độc lập): {dem.get('KHOP', 0)} đại lượng khớp, {dem.get('LECH', 0)} "
              f"lệch, {dem.get('KHONG_SO', 0)} không so (khác định nghĩa — ghi trong tệp kiểm chéo)."]
    return L


NHAN_VIF = {"dat": "< 3", "can_xem": "3–5 (cần xem xét)", "khong_dat": "≥ 5 (đa cộng tuyến)"}
NHAN_R2 = {"manh": "mạnh", "trung_binh": "trung bình", "yeu": "yếu", "rat_yeu": "dưới mức yếu"}
NHAN_F2 = {"lon": "lớn", "trung_binh": "trung bình", "nho": "nhỏ", "khong_dang_ke": "không đáng kể"}


def _co(x) -> str:
    return "—" if x is None else ("đạt" if x else "KHÔNG đạt")


def md_bao_cao(tom: dict, kc: dict) -> str:
    p = tom["pls_sem"]
    dg = p.get("danh_gia") or {}
    tk = p["thong_ke_tap"]
    L = [f"# PLS-SEM — {tom['study']} ({tom['gate']})", ""]
    if tom.get("ban_nhap"):
        L += ["> **BẢN NHÁP — dữ liệu KHÔNG phải bộ đã khoá G5. Không dùng làm kết quả đề tài.**", ""]
    pb = p.get("phien_ban") or {}
    L += [f"- Chạy lúc {tom['generated']} · {pb.get('r') or '—'} · seminr {pb.get('seminr') or '—'} (tính chính) · "
          f"cSEM {pb.get('cSEM') or '—'} (kiểm chéo)",
          f"- Mô hình đọc từ {p['sap']['tep']} (SHA-256 {p['sap']['sha256'][:12]}…): bootstrap "
          f"{_so_vn(p['sap']['bootstrap'])} mẫu lặp, hạt giống {p['sap']['seed']}, KTC phân vị "
          f"{100 - round(100 * p['sap']['alpha'])}%; ô thiếu: {p['sap']['du_lieu_thieu']}",
          f"- Quần thể: {tom['dac_ta_phan_tich'].get('loc') or 'toàn bộ'} — n phân tích {tk['n_phan_tich']} "
          f"(sau lọc {tk['n_sau_loc']}/{tk['n_ban_dau']} dòng)", ""]
    L += [f"> ⚠ {x}" for x in tom.get("canh_bao") or []]
    if not dg:
        L += ["", "## Không có kết quả seminr", ""] + [f"- {k}: {v}" for k, v in (p.get("loi") or {}).items()]
        return "\n".join(L + ["", CAN_KIEM, ""])
    L += ["", "## 1. Mô hình đo lường — chỉ báo kết quả (Mode A)", "",
          "| Cấu trúc | Chỉ báo | Tải | KTC 95% bootstrap | ≥ 0,708 |", "|---|---|---|---|---|"]
    L += [f"| {x['cau_truc']} | {x['chi_bao']} | {so3(x['tai'])} | {ktc3(x['ktc'])} | {_co(x['dat'])} |"
          for x in dg["do_luong_ket_qua"] if not x.get("tong_hop")]
    L += ["", "| Cấu trúc | Cronbach α | ρA | ρC | AVE | Tin cậy 0,70–0,95 | AVE ≥ 0,50 |",
          "|---|---|---|---|---|---|---|"]
    L += [f"| {x['cau_truc']}{' (một chỉ báo)' if x.get('mot_chi_bao') else ''} | {so3(x['alpha'])} | "
          f"{so3(x['rho_a'])} | {so3(x['rho_c'])} | {so3(x['ave'])} | {_co(x['dat_tin_cay'])} | {_co(x['dat_ave'])} |"
          for x in dg["do_luong_ket_qua"] if x.get("tong_hop")]
    if dg["htmt"]:
        L += ["", "| Cặp cấu trúc | HTMT | KTC 90% bootstrap | < 0,90 |", "|---|---|---|---|"]
        L += [f"| {a} – {b} | {so3(x['htmt'])} | {ktc3(x['ktc90'])} | {_co(x['dat'])} |"
              for x in dg["htmt"] for a, b in [x["cap"]]]
    if dg["do_luong_cau_tao"]:
        L += ["", "## 2. Mô hình đo lường — chỉ báo cấu tạo (Mode B)", "",
              "| Cấu trúc | Chỉ báo | VIF | Trọng số | KTC 95% | Có ý nghĩa | Tải | Giữ (Hair 2019) |",
              "|---|---|---|---|---|---|---|---|"]
        L += [f"| {x['cau_truc']} | {x['chi_bao']} | {so3(x['vif'])} | {so3(x['trong_so'])} | {ktc3(x['ktc'])} | "
              f"{'có' if x['y_nghia'] else ('không' if x['y_nghia'] is False else '—')} | {so3(x['tai'])} | "
              f"{_co(x['giu'])} |" for x in dg["do_luong_cau_tao"]]
    L += ["", "## 3. Mô hình cấu trúc", "",
          "β: hệ số đường dẫn (hiệu chỉnh cho các cấu trúc tiền tố còn lại của cùng cấu trúc nội sinh); r thô: tương "
          "quan chưa hiệu chỉnh giữa điểm hai cấu trúc, KTC 95% theo biến đổi Fisher z.", "",
          "| Đường dẫn | r thô (KTC 95%) | β | SD bootstrap | KTC 95% | Có ý nghĩa | f² | VIF |",
          "|---|---|---|---|---|---|---|---|"]
    L += [f"| {x['duong_dan'].replace(' -> ', ' → ')} | {so3(x.get('r_tho'))} ({ktc3(x.get('ktc_r_tho'))}) | "
          f"{so3(x['he_so'])} | {so3(x['sd'])} | {ktc3(x['ktc'])} | "
          f"{'có' if x['y_nghia'] else ('không' if x['y_nghia'] is False else '—')} | {so3(x['f2'])}"
          f"{' (' + NHAN_F2[x['muc_f2']] + ')' if x.get('muc_f2') else ''} | {so3(x['vif'])} |" for x in dg["cau_truc"]]
    da = set()
    L += ["", "| Cấu trúc nội sinh | R² | R² hiệu chỉnh |", "|---|---|---|"]
    for x in dg["cau_truc"]:
        if x["noi_sinh"] not in da:
            da.add(x["noi_sinh"])
            L.append(f"| {x['noi_sinh']} | {so3(x['r2'])}{' (' + NHAN_R2[x['muc_r2']] + ')' if x.get('muc_r2') else ''}"
                     f" | {so3(x['r2_hc'])} |")
    pp = dg.get("plspredict")
    if pp:
        q2 = p.get("q2_predict_csem") or {}
        L += ["", f"## 4. PLSpredict (k = {pp['k']}, {pp['lap']} lần lặp, tiền tố trực tiếp)", "",
              "| Chỉ báo | RMSE PLS | RMSE LM | MAE PLS | MAE LM | PLS < LM (RMSE) | Q²predict (cSEM) |",
              "|---|---|---|---|---|---|---|"]
        L += [f"| {x['chi_bao']} | {so3(x['rmse_pls'])} | {so3(x['rmse_lm'])} | {so3(x['mae_pls'])} | "
              f"{so3(x['mae_lm'])} | {'có' if x['pls_tot_hon_lm_rmse'] else 'không'} | {so3(q2.get(x['chi_bao']))} |"
              for x in pp["chi_bao"]]
        L.append(f"\n{KHAC_DINH_NGHIA_Q2}.")
    dem = kc.get("dem") or {}
    L += ["", f"## 5. Kiểm chéo seminr ↔ cSEM — {kc['trang_thai']}", "",
          f"{dem.get('KHOP', 0)} khớp · {dem.get('LECH', 0)} lệch · {dem.get('KHONG_SO', 0)} không so "
          f"(dung sai tất định {DUNG_SAI_TAT_DINH:g}; bootstrap và PLSpredict theo sai số Monte Carlo, ngưỡng "
          f"Bonferroni cho cả họ phép so, α họ = {ALPHA_HO:g})"]
    lech = [x for x in kc.get("dong") or [] if x["ket"] == "LECH"]
    L += [f"- ✗ {x['nhom']} · {x['ten']}: seminr {x.get('seminr')} · cSEM {x.get('csem')} · chênh {x.get('chenh'):.3g} "
          f"> {x.get('dung_sai'):.3g}" for x in lech[:40]]
    L += [f"- ⚪ {x['nhom']} · {x['ten']}: {x['ly_do']}" for x in kc.get("dong") or [] if x["ket"] == "KHONG_SO"][:10]
    dd = p.get("doi_dau_bootstrap") or {}
    if any(_so(v) for goi in dd.values() for v in (goi or {}).values()):
        L.append("- Mẫu lặp bootstrap đổi dấu cấu trúc (mọi tải ngược dấu ước lượng gốc): "
                 + " · ".join(f"{ten_goi} " + ", ".join(f"{k} {int(v)}" for k, v in (goi or {}).items() if _so(v))
                              for ten_goi, goi in dd.items() if any(_so(v) for v in (goi or {}).values()))
                 + " — SD của gói có mẫu đổi dấu kém ổn định; sai số Monte Carlo tính theo phân phối riêng từng gói")
    am = {k: v for k, v in (p.get("htmt_mau_tuong_quan_am") or {}).items() if _so(v)}
    L.append("- HTMT bootstrap: so theo định nghĩa seminr (trị tuyệt đối từng tương quan) trên mẫu lặp của cSEM — "
             "cSEM::calculateHTMT dùng tương quan có dấu nên hai định nghĩa chỉ trùng khi mọi tương quan dương"
             + (("; mẫu lặp có tương quan ≤ 0: " + ", ".join(f"{k} {int(v)}" for k, v in am.items())) if am else ""))
    L += ["", "## Ngưỡng định trước và nguồn", ""]
    L += [f"- {mo_ta} — " + "; ".join(trich(m) for m in nguon) for _k, mo_ta, nguon in DONG_NGUONG_SAP]
    L += [f"- {XAC_MINH_NGUON}."]
    if not dg.get("phan_loai"):
        L.append("- SAP không ghi đủ cụm ngưỡng định trước ⇒ chỉ in số, không phân loại.")
    if p.get("canh_bao_r"):
        L += ["", "## Cảnh báo của R", ""]
        L += [f"- [{w.get('khoi')}] {w.get('thong_diep')}" for w in p["canh_bao_r"][:20]]
    return "\n".join(L + ["", CAN_KIEM, ""])


def ghi_ket_qua(args, c: dict, tom: dict, kc: dict) -> tuple[Path, Path, Path]:
    import kiem_cheo_g6 as KC  # noqa: PLC0415 — cùng dấu vân tay đầu vào với kiểm chéo SPSS/R

    p_tom = c["ra_tom"] / f"{args.gate}_analysis_summary.json"
    p_md = c["ra_tom"] / f"{args.gate}_ket_qua.md"
    p_kc = c["ra_tom"] / f"{args.gate}_kiem_cheo.json"
    p_tom.write_text(json.dumps(tom, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    p_md.write_text(md_bao_cao(tom, kc), encoding="utf-8", newline="\n")
    vt = KC.van_tay(c["ra_tom"], args.gate)
    p_kc.write_text(json.dumps({"trang_thai": kc["trang_thai"], "van_tay": vt, "luc": tom["generated"],
                                "phan_mem": {"cSEM": {"trang_thai": kc["trang_thai"], "dem": kc["dem"]}},
                                "ly_do": kc.get("ly_do"), "dong": kc["dong"], "disclaimer": CAN_KIEM},
                               ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    return p_tom, p_md, p_kc


# ───────────────────────────── lệnh ─────────────────────────────


def _r_san_sang() -> tuple[Path | None, int, str]:
    try:
        rs = R.tim_r()
    except KhongDoDuoc as e:
        return None, MA_KHONG_DO, str(e)
    g = kiem_goi(rs)
    if g["ma"] != 0:
        return None, MA_LECH, f"R không chạy được: {g['loi']}"
    if g["cu"]:
        return None, MA_KHONG_DO, (f"gói R dưới phiên bản tối thiểu: {', '.join(g['cu'])} — cập nhật gói "
                                   "(install.packages) rồi chạy lại; không chạy PLSpredict bằng bản có lỗi đã biết")
    if g["thieu"]:
        return None, MA_KHONG_DO, (f"thiếu gói R: {', '.join(g['thieu'])} — `python3 tools/cau_noi_r.py cai-goi "
                                   "--ap-dung`")
    return rs, MA_OK, ""


def lenh_kiem(_args) -> int:
    rs, ma, ly_do = _r_san_sang()
    if rs is None:
        print(f"{'🔴' if ma == MA_LECH else '⚪'} {ly_do}")
        return ma
    g = kiem_goi(rs)
    print(f"• Rscript: {rs}")
    for ten in R.GOI_CAN_PLS_SEM:
        print(f"  ✓ {ten} {g['goi'].get(ten)}")
    print("✓ R sẵn sàng cho PLS-SEM (seminr tính chính, cSEM kiểm chéo).")
    return MA_OK


def lenh_cai_goi(args) -> int:
    """Cài qua ĐÚNG đường `cau_noi_r cai-goi` (seminr và cSEM đã khai trong GOI_CAN của cầu nối R)."""
    return R.main(["cai-goi", *(["--ap-dung"] if args.ap_dung else []), "--thoi-han", str(args.thoi_han)])


def lenh_cu_phap(args) -> int:
    c = chuan_bi(args)
    dac = c["dac"]
    mh = dac["mo_hinh"]
    print(f"✓ Script R: {c['script']}")
    print(f"  {len(mh['cau_truc'])} cấu trúc · {len(mh['duong_dan'])} đường dẫn · bootstrap "
          f"{_so_vn(mh['bootstrap'])} · hạt giống {mh['seed']} · n phân tích {dac['thong_ke_tap']['n_phan_tich']}")
    for x in dac["canh_bao"]:
        print(f"  ⚠ {x}")
    return MA_OK


def lenh_chay(args) -> int:
    c = chuan_bi(args)
    rs, ma, ly_do = _r_san_sang()
    if rs is None:
        print(f"{'🔴' if ma == MA_LECH else '⚪'} {ly_do}\n  Script R đã sinh: {c['script']}")
        return ma
    print(f"▶ Rscript --vanilla {c['script'].name} (seminr + cSEM; thời hạn {args.thoi_han} giây)…", flush=True)
    ma_r, kq, loi_r = chay_r_pls(rs, c, args.thoi_han)
    if ma_r == 3:
        print("🔴 R từ chối: SHA-256 tập phân tích không khớp cấu hình — dữ liệu đổi sau khi chuẩn bị")
        return MA_TU_CHOI
    tom, kc, ma = lam_tom_tat(args, c, kq, ma_r, loi_r, chay_bang=f"Rscript --vanilla ({rs})")
    p_tom, p_md, p_kc = ghi_ket_qua(args, c, tom, kc)
    dg = tom["pls_sem"].get("danh_gia") or {}
    for x in dg.get("cau_truc") or []:
        print(f"  {x['duong_dan']}: β {so3(x['he_so'])} (KTC 95% {ktc3(x['ktc'])}) · R² {x['noi_sinh']} {so3(x['r2'])}")
    dem = kc.get("dem") or {}
    print(f"• Kiểm chéo cSEM: {kc['trang_thai']} — {dem.get('KHOP', 0)} khớp · {dem.get('LECH', 0)} lệch · "
          f"{dem.get('KHONG_SO', 0)} không so{(' — ' + kc['ly_do']) if kc.get('ly_do') else ''}")
    for k, v in (tom["pls_sem"].get("loi") or {}).items():
        print(f"🔴 {k}: {v}")
    print(f"✓ {p_md}\n✓ {p_tom}\n✓ {p_kc}\n{CAN_KIEM}")
    return ma


# ───────────────────────────── mốc chuẩn: sách Hair và cộng sự 2021 ─────────────────────────────

#: Hai mô hình corporate reputation của sách (chương 4: mô hình đơn giản; chương 5–6: mô hình mở rộng) — mã cấu trúc,
#: chỉ báo, Mode và đường dẫn chép đúng mã seminr in trong sách.
MO_HINH_SACH = {
    "don_gian": {"cau_truc": [{"ma": "COMP", "muc": ["comp_1", "comp_2", "comp_3"], "mode": "A"},
                              {"ma": "LIKE", "muc": ["like_1", "like_2", "like_3"], "mode": "A"},
                              {"ma": "CUSA", "muc": ["cusa"], "mode": "A"},
                              {"ma": "CUSL", "muc": ["cusl_1", "cusl_2", "cusl_3"], "mode": "A"}],
                 "duong_dan": [["COMP", "CUSA"], ["COMP", "CUSL"], ["LIKE", "CUSA"], ["LIKE", "CUSL"],
                               ["CUSA", "CUSL"]], "plspredict": None},
    "mo_rong": {"cau_truc": [{"ma": "QUAL", "muc": [f"qual_{i}" for i in range(1, 9)], "mode": "B"},
                             {"ma": "PERF", "muc": [f"perf_{i}" for i in range(1, 6)], "mode": "B"},
                             {"ma": "CSOR", "muc": [f"csor_{i}" for i in range(1, 6)], "mode": "B"},
                             {"ma": "ATTR", "muc": [f"attr_{i}" for i in range(1, 4)], "mode": "B"},
                             {"ma": "COMP", "muc": ["comp_1", "comp_2", "comp_3"], "mode": "A"},
                             {"ma": "LIKE", "muc": ["like_1", "like_2", "like_3"], "mode": "A"},
                             {"ma": "CUSA", "muc": ["cusa"], "mode": "A"},
                             {"ma": "CUSL", "muc": ["cusl_1", "cusl_2", "cusl_3"], "mode": "A"}],
                "duong_dan": [[a, b] for a in ("QUAL", "PERF", "CSOR", "ATTR") for b in ("COMP", "LIKE")]
                + [[a, b] for a in ("COMP", "LIKE") for b in ("CUSA", "CUSL")] + [["CUSA", "CUSL"]],
                "plspredict": {"k": 10, "lap": 10, "dich": ["CUSL"]}},
}
LY_DO_LM_SACH = ("seminr 2.6.0 NEWS.md: «predict_pls(reps = k) repeated the cross-validation on the same folds» trước "
                 "2.6.0 — kết quả đổi với mọi lệnh reps > 1; sách (2021) chạy seminr trước 2.6.0, không đặt hạt "
                 "giống")


def _lay(goc: dict, duong: list):
    x = goc
    for k in duong:
        if isinstance(x, list) and isinstance(k, int) and k < len(x):
            x = x[k]
        elif isinstance(x, dict) and k in x:
            x = x[k]
        else:
            return None
    return x


def doi_chieu_sach(kq: dict[str, dict], so_in: list[dict]) -> list[dict]:
    """So seminr (và cSEM với đại lượng tất định) với số in trong sách. Số in làm tròn 3 chữ số ⇒ dung sai làm tròn
    0,0005; bootstrap không đặt hạt giống / PLSpredict ⇒ thêm sai số Monte Carlo (z = Z_MC)."""
    ra = []
    for e in so_in:
        k = kq.get(e["mo_hinh"]) or {}
        s, c = k.get("seminr") or {}, k.get("csem") or {}
        d = dict(e)
        tron = 0.0005 if isinstance(e["so_in"], float) else 0
        if e["loai"] == "plspredict":
            vals = [_so(_lay(l_, [e["duong"][1], e["duong"][2]])) for l_ in (s.get("plspredict") or {}).get("luot", [])]
            vals = [v for v in vals if v is not None]
            if len(vals) < 2:
                d |= {"ket": "KHONG_SO", "ly_do": "cần ≥ 2 lượt PLSpredict"}
                ra.append(d)
                continue
            tb = sum(vals) / len(vals)
            sd = math.sqrt(sum((v - tb) ** 2 for v in vals) / (len(vals) - 1))
            tol = Z_MC * sd + tron  # MỘT lượt của sách so với trung bình J lượt của ta
            d |= {"seminr": tb, "chenh_seminr": abs(tb - e["so_in"]), "dung_sai": tol}
            d["ket"] = "KHOP" if abs(tb - e["so_in"]) <= tol else (
                "KHAC_PHIEN_BAN" if e["duong"][1].endswith("_lm") else "LECH")
            if d["ket"] == "KHAC_PHIEN_BAN":
                d["ly_do"] = LY_DO_LM_SACH
            ra.append(d)
            continue
        vs = _so(_lay(s, e["duong"]))
        tol = tron
        if e["loai"] == "bootstrap_khong_hat_giong":
            nhom, ten = e["duong"][1], e["duong"][2]
            bt = ((s.get("bootstrap") or {}).get(nhom) or {}).get(ten) or {}
            ktc = bt.get("ktc") or [None, None]
            b = _so((s.get("bootstrap") or {}).get("B_dung")) or 1000
            sd = (ktc[1] - ktc[0]) / (2 * _z(0.95)) if None not in ktc else None
            tol = tron + (Z_MC * math.sqrt(2) * _mcse_ktc(sd, 0.10, int(b)) if sd else 0)
        d |= {"seminr": vs, "chenh_seminr": None if vs is None else abs(vs - e["so_in"]), "dung_sai": tol}
        d["ket"] = "KHONG_SO" if vs is None else ("KHOP" if abs(vs - e["so_in"]) <= tol + 1e-12 else "LECH")
        if e["loai"] == "tat_dinh" and c and e["duong"][0] != "so_vong_lap":  # số vòng lặp tuỳ tiêu chí dừng từng gói
            vc = _so(_lay(c, e["duong"]))
            d |= {"csem": vc, "chenh_csem": None if vc is None else abs(vc - e["so_in"])}
            if vc is not None and abs(vc - e["so_in"]) > tol + 1e-12 and d["ket"] == "KHOP":
                d["ket"] = "LECH_CSEM"
        ra.append(d)
    return ra


def lenh_chuan(args) -> int:
    import tempfile  # noqa: PLC0415

    rs, ma, ly_do = _r_san_sang()
    if rs is None:
        print(f"{'🔴' if ma == MA_LECH else '⚪'} {ly_do}")
        return ma
    so_in = json.loads(TEP_SO_IN.read_text(encoding="utf-8"))
    ra_dir = Path(args.thu_muc_ra).expanduser() if args.thu_muc_ra else None
    if ra_dir is not None and not _ngoai_repo(ra_dir):
        raise TuChoi("--thu-muc-ra phải nằm NGOÀI repo")
    with tempfile.TemporaryDirectory(prefix="ebm-pls-chuan-") as tam:
        tam = Path(tam)
        tho = tam / "corp_rep_data.csv"
        vb = ("suppressPackageStartupMessages(library(seminr)); d <- seminr::corp_rep_data; d[d == -99] <- NA; "
              f"utils::write.csv(d, {R.chuoi_r(str(tho))}, row.names = FALSE, na = \"\")")
        (tam / "xuat.R").write_text(vb + "\n", encoding="utf-8", newline="\n")
        ma_x, _o, err = R.chay_r(rs, [str(tam / "xuat.R")], thu_muc=tam, thoi_han=300)
        if ma_x != 0:
            print(f"🔴 không xuất được corp_rep_data: {err.strip()[-300:]}")
            return MA_LECH
        with open(tho, encoding="utf-8", newline="") as f:
            rd = list(csv.DictReader(f))
        cot = list(rd[0])
        so = {c_: [float(r[c_]) if r[c_] not in ("", "NA") else None for r in rd] for c_ in cot}
        # Như sách: seminr nhận dữ liệu có NA và tự thay trung bình (missing = mean_replacement, thay lại trong từng mẫu
        # bootstrap); cSEM nhận bản thay trung bình toàn mẫu (R làm, cờ thieu_trong_seminr)
        dl = tam / "corp_rep_na.csv"
        with open(dl, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(cot)
            for i in range(len(rd)):
                w.writerow(["NA" if so[c_][i] is None else repr(so[c_][i]) for c_ in cot])
        sha = S.sha256_tep(dl)
        # Bản đủ (thay trung bình toàn mẫu MỘT lần, như đường sản xuất): HAI gói nhận cùng ma trận ⇒ kiểm chéo đúng
        # nghĩa
        dl_du = tam / "corp_rep_du.csv"
        tb = {c_: sum(x for x in so[c_] if x is not None) / sum(1 for x in so[c_] if x is not None) for c_ in cot}
        with open(dl_du, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(cot)
            for i in range(len(rd)):
                w.writerow([repr(tb[c_] if so[c_][i] is None else so[c_][i]) for c_ in cot])
        sha_du = S.sha256_tep(dl_du)
        script = tam / "pls.R"
        script.write_text(R.kich_ban_pls_sem(), encoding="utf-8", newline="\n")
        kq_all: dict[str, dict] = {}
        for ten, mh0 in MO_HINH_SACH.items():
            mh = {**mh0, "bootstrap": args.bootstrap, "seed": 123, "alpha": 0.05}
            for kieu, tep, sha_, them in (("sach", dl, sha, {"thieu_trong_seminr": True}), ("du", dl_du, sha_du, {})):
                ch = cau_hinh_r(mh, sha_, luot_mc=args.luot_mc) | them
                p_ch, p_kq = tam / f"ch_{ten}_{kieu}.json", tam / f"kq_{ten}_{kieu}.json"
                p_ch.write_text(json.dumps(ch), encoding="utf-8", newline="\n")
                print(f"▶ mô hình {ten} — {'như sách (seminr tự thay trung bình)' if kieu == 'sach' else 'dữ liệu đủ'}"
                      f" (seminr + cSEM, bootstrap {args.bootstrap}, seed 123)…", flush=True)
                ma_r, _o, err = R.chay_r(rs, [str(script), str(tep), str(p_kq), str(p_ch)], thu_muc=tam,
                                         thoi_han=args.thoi_han)
                kq = json.loads(p_kq.read_text(encoding="utf-8")) if p_kq.is_file() else {"loi": {"r": err}}
                if kieu == "sach":
                    kq_all[ten] = kq
                else:
                    kq_all[ten]["kiem_cheo"] = doi_chieu(kq, {**mh}) if kq.get("seminr") else None
                    kq_all[ten]["du_lieu_du"] = kq
        so_sanh = doi_chieu_sach(kq_all, so_in["so_in"])
    dem: dict[str, int] = {}
    for x in so_sanh:
        dem[x["ket"]] = dem.get(x["ket"], 0) + 1
    print(f"\n══ Mốc chuẩn Hair và cộng sự 2021 — {len(so_sanh)} số in trong văn bản sách ══")
    print(f"   Phần mềm của số in: {so_in['phan_mem_cua_so_in']}")
    for x in so_sanh:
        dau = {"KHOP": "✓", "KHAC_PHIEN_BAN": "◐", "KHONG_SO": "⚪"}.get(x["ket"], "✗")
        cs = f" · cSEM {x['csem']:.4f}" if isinstance(x.get("csem"), float) else ""
        print(f" {dau} ch.{x['chuong']} {x['mo_hinh']:8} {'/'.join(map(str, x['duong'])):42} sách {x['so_in']} · "
              f"seminr {x['seminr'] if not isinstance(x.get('seminr'), float) else round(x['seminr'], 4)}{cs}"
              + (f" — {x['ly_do']}" if x.get("ly_do") else ""))
    for ten, k in kq_all.items():
        kc = k.get("kiem_cheo") or {}
        print(f"• Kiểm chéo seminr ↔ cSEM ({ten}, dữ liệu đủ): {kc.get('trang_thai')} {kc.get('dem')}")
        for x in kc.get("dong") or []:
            if x["ket"] == "LECH":
                print(f"    ✗ {x['nhom']} · {x['ten']}: seminr {x.get('seminr')} · cSEM {x.get('csem')} · chênh "
                      f"{x.get('chenh'):.3g} > {x.get('dung_sai'):.3g}")
    print(f"KẾT: {dem}")
    if ra_dir is not None:
        ra_dir.mkdir(parents=True, exist_ok=True)
        (ra_dir / "pls_sem_moc_chuan.json").write_text(json.dumps(
            {"so_sanh": so_sanh, "dem": dem, "ket_qua": kq_all, "phien_ban": {
                k: v.get("goi") for k, v in kq_all.items()}}, ensure_ascii=False, indent=1), encoding="utf-8",
            newline="\n")
        print(f"✓ {ra_dir / 'pls_sem_moc_chuan.json'}")
    xau = dem.get("LECH", 0) + dem.get("LECH_CSEM", 0)
    xau += sum(1 for k in kq_all.values() if (k.get("kiem_cheo") or {}).get("trang_thai") == "LECH")
    return MA_LECH if xau else MA_OK


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="PLS-SEM theo SAP đã khoá: seminr tính chính, cSEM kiểm chéo. " + CAN_KIEM)
    sub = ap.add_subparsers(dest="lenh", required=True)
    sub.add_parser("kiem", help="Rscript + gói jsonlite/seminr/cSEM")
    c = sub.add_parser("cai-goi", help="cài gói thiếu qua cau_noi_r cai-goi (chạy khô mặc định)")
    c.add_argument("--ap-dung", action="store_true")
    c.add_argument("--thoi-han", type=int, default=1800)
    for ten in ("cu-phap", "chay"):
        p = sub.add_parser(ten)
        p.add_argument("--study", required=True)
        p.add_argument("--gate", default=GATE_MAC_DINH)
        p.add_argument("--loc", help="lọc quần thể phân tích (cú pháp biến phái sinh) — như run_stats_analysis")
        p.add_argument("--pls-sem", choices=[MA_DAC_TA], help="khai báo loại phân tích của đặc tả G6 (kiểm khớp)")
        p.add_argument("--bootstrap", type=int, help="số mẫu bootstrap của đặc tả G6 — phải bằng SAP")
        p.add_argument("--du-lieu-thieu", choices=["listwise", "trung_binh"],
                       help="độ nhạy SAP §9: xử lý ô thiếu khác SAP §4 (phân tích chính không dùng cờ này)")
        p.add_argument("--dictionary", help="từ điển REDCap G5 (mặc định exports/<mã>/G5_REDCap_dictionary_<mã>.csv)")
        p.add_argument("--data", help="CSV khác bộ đã khoá (bắt buộc kèm --ban-nhap --thu-muc-ra)")
        p.add_argument("--ban-nhap", action="store_true")
        p.add_argument("--thu-muc-ra", help="thư mục NGOÀI repo cho bản nháp")
        p.add_argument("--luot-mc", type=int, default=5, help="số lượt PLSpredict độc lập mỗi gói (sai số Monte Carlo)")
        p.add_argument("--thoi-han", type=int, default=THOI_HAN)
    ch = sub.add_parser("chuan", help="mốc chuẩn: tái lập số in trong Hair và cộng sự 2021 (corporate reputation)")
    ch.add_argument("--bootstrap", type=int, default=1000, help="như sách: 1000")
    ch.add_argument("--luot-mc", type=int, default=5)
    ch.add_argument("--thu-muc-ra", help="ghi pls_sem_moc_chuan.json (NGOÀI repo)")
    ch.add_argument("--thoi-han", type=int, default=THOI_HAN)
    args = ap.parse_args(argv)
    if getattr(args, "luot_mc", 5) < 2:
        print("⛔ --luot-mc phải ≥ 2 (cần ít nhất hai lượt để ước lượng sai số Monte Carlo)")
        return MA_TU_CHOI
    ham = {"kiem": lenh_kiem, "cai-goi": lenh_cai_goi, "cu-phap": lenh_cu_phap, "chay": lenh_chay,
           "chuan": lenh_chuan}[args.lenh]
    try:
        return ham(args)
    except TuChoi as e:
        print(f"⛔ {e}")
        return MA_TU_CHOI
    except KhongDoDuoc as e:
        print(f"⚪ {e}")
        return MA_KHONG_DO


if __name__ == "__main__":
    sys.exit(main())
