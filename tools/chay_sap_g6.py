#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""chay_sap_g6.py — CHẠY TRỌN SAP bằng MỘT lệnh: mọi phân tích SAP đã khoá (chính · phụ · nhóm con · độ nhạy) theo
một ĐẶC TẢ MÁY ĐỌC, mỗi phân tích qua đúng run_stats_analysis.py (+ kiểm chéo SPSS/R tuỳ chọn), rồi một CHỈ MỤC kết quả.

Vì sao có tệp này (14/11/2026, soát chuỗi SPSS/R theo yêu cầu bác sĩ — «F3 Chạy trọn SAP một lệnh»): SAP thật cam kết
nhiều phân tích (C1a: tỷ lệ mục tiêu 1, mô hình thứ tự chính, logistic nhị phân, loại phiếu có hỗ trợ ghi…; BTM: tỷ lệ
kết cục chính, 3 kết cục phụ, nhóm con, Poisson PR, 9 độ nhạy) nhưng run_stats_analysis chạy MỘT đặc tả mỗi lần, gõ tay
từng bộ tham số — dễ sót, dễ lệch SAP, không có chỗ nào cho biết đã chạy hết chưa.

Đặc tả: `exports/<mã>/G6_DAC_TA_SAP.json`
  {
    "nguon_sap": "G4_A5_SAP_FINAL_<mã>.md",
    "sha256_sap": "<SHA-256 của SAP lúc soạn đặc tả>",
    "phan_tich": [
      {"id": "MT2_chinh", "vai": "chinh", "sap_muc": "§4", "mo_ta": "…",
       "tham_so": {"outcome": "g1", "group": "thoigian_cho", "covariates": ["tuoi", "khunggio_kham"],
                   "hiep_bien_phan_loai": ["khunggio_kham"], "outcome_type": "ordinal", "don_vi_phoi_nhiem": 15,
                   "cot_cum": "ma_ban_kham", "loc": "PhieuHopLe == 1"}},
      {"id": "DN_spline", "vai": "do_nhay", "sap_muc": "§9", "mo_ta": "…", "chua_tu_dong": "lý do"}
    ],
    "nguoi_duyet": "<VAI>:<tham chiếu>:<YYYY-MM-DD>:<dấu đặc tả 12 hex>"
  }
  • vai ∈ chinh (đúng MỘT, chạy với gate G6 — tệp G6_analysis_summary.json chính thức) · phu · nhom_con · do_nhay ·
    mo_ta; phân tích khác chạy với gate G6_<id> (tệp riêng, không ghi đè nhau).
  • `chua_tu_dong` = phân tích SAP cam kết mà hệ CHƯA có công cụ — liệt kê rõ trong chỉ mục, không bỏ im. Từ 22/11/2026
    mọi loại từng ghi «chờ làm tay» (spline RCS, partial PO, Firth, hệ số chặn ngẫu nhiên, trọng số hậu phân tầng,
    gộp mức, điểm ảnh hưởng, trung gian, bảng chéo, chuỗi khâu, đáp ứng, đặc tính đo lường…) đã có đường máy:
    `tham_so.loai_bo_sung` + `tham_so.cau_hinh` ⇒ phan_tich_sap_bo_sung.py (cấu hình kiểm bằng chính mô-đun đó).
  • `tham_so.bien_thua` = {bien, toi_thieu}: quy tắc bỏ biến thưa định trước của SAP — đếm trên quần thể phân tích
    trước khi gọi run_stats_analysis, biến có một nhóm dưới ngưỡng bị bỏ khỏi covariates; quyết định ghi vào chỉ mục.
  • `sha256_sap` khác SAP hiện tại ⇒ đặc tả CŨ (SAP đã sửa đổi) — từ chối chạy.
  • nguoi_duyet do THỐNG KÊ VIÊN/PI ghi kèm dấu đặc tả (lệnh `kiem` in ra) — agent soạn đặc tả, KHÔNG ghi cột duyệt;
    sửa đặc tả sau khi duyệt ⇒ hết hiệu lực. Chưa duyệt ⇒ từ chối chạy (đề tài synthetic_test: cảnh báo).

Lệnh
  kiem    --study <mã> [--json]                         đặc tả hợp lệ? dấu, trạng thái duyệt, SAP còn khớp?
  chay    --study <mã> [--chi id1,id2] [--kiem-cheo] [--khong-ve]
                                                        chạy lần lượt (dữ liệu ĐÃ KHOÁ G5 — kiểm bằng hàm của cổng);
                                                        cuối lượt tự sinh biểu đồ (hinh_g6.py) trừ khi --khong-ve
  ket-qua --study <mã> [--json]                         chỉ mục G6_SAP_ket_qua.json
  duyet   --study <mã> --vai PI|THONG_KE_VIEN --tham-chieu <mã> [--ap-dung]
                                                        THỐNG KÊ VIÊN/PI tự ghi duyệt (chạy khô mặc định)
Không bao giờ truyền cờ ghi đè cổng (--i-confirm-*). Mã thoát: 0 đạt · 1 có phân tích lỗi/lệch · 2 không đo được ·
3 từ chối (đặc tả sai/cũ/chưa duyệt, dữ liệu chưa khoá). Cần bác sĩ kiểm chứng.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

TOOLS = Path(__file__).resolve().parent
BASE = TOOLS.parent
sys.path.insert(0, str(TOOLS))
import bien_phai_sinh as BPS  # noqa: E402

TEP_DAC_TA = "G6_DAC_TA_SAP.json"
TEP_KQ_JSON, TEP_KQ_MD = "G6_SAP_ket_qua.json", "G6_SAP_ket_qua.md"
THU_MUC_NHAT_KY = "G6_SAP_nhat_ky"
VAI = ("chinh", "phu", "nhom_con", "do_nhay", "mo_ta")
CAN_KIEM = "Cần bác sĩ kiểm chứng."
THOI_HAN = 7200
# tham số đặc tả ⇒ cờ run_stats_analysis.py (kiểu: s = tên/chuỗi, ds = danh sách tên, so = số, nguyen = số nguyên)
THAM_SO = {
    "outcome": ("--outcome", "s"),
    "group": ("--group", "s"),
    "covariates": ("--covariates", "ds"),
    "hiep_bien_phan_loai": ("--hiep-bien-phan-loai", "ds"),
    "outcome_type": ("--outcome-type", "s"),
    "don_vi_phoi_nhiem": ("--don-vi-phoi-nhiem", "so"),
    "cot_cum": ("--cot-cum", "s"),
    "ty_le": ("--ty-le", "ds_rieng"),
    "nguong_ty_le": ("--nguong-ty-le", "so"),
    "vars": ("--vars", "ds"),
    "time": ("--time", "s"),
    "event": ("--event", "s"),
    "n_imputations": ("--n-imputations", "nguyen"),
    "loc": ("--loc", "bt"),
    # 16/11/2026 (giả lập 8 thiết kế): phân tích ĐẶC THÙ — chẩn đoán · dự báo · tổng quan–gộp · định tính — chạy bằng
    # phan_tich_thiet_ke_dac_thu.py (run_stats_analysis chưa có đường); cùng nhật ký/tóm tắt/kiểm chéo SPSS–R.
    "loai_dac_thu": ("--loai", "loai"),
    "tham_chieu": ("--tham-chieu", "s"),
    "chi_so": ("--chi-so", "s"),
    "nguong": ("--nguong", "so"),
    "nhan_nghien_cuu": ("--nhan-nghien-cuu", "s"),
    "su_kien_can_thiep": ("--su-kien-can-thiep", "s"),
    "n_can_thiep": ("--n-can-thiep", "s"),
    "su_kien_chung": ("--su-kien-chung", "s"),
    "n_chung": ("--n-chung", "s"),
    # 22/11/2026 (PRISMA 2020 mục 20c): phân nhóm tiền định của SAP §7 — gộp riêng từng nhóm + Q giữa nhóm
    "phan_nhom": ("--phan-nhom", "s"),
    "mo_hinh": ("--mo-hinh", "s"),  # gộp: ngau_nhien | co_dinh (độ nhạy hiệu ứng cố định)
    # 22/11/2026 (việc B): dự báo — số lần bootstrap hiệu chỉnh lạc quan của SAP §9
    "bootstrap": ("--bootstrap", "nguyen"),
    "chu_de": ("--chu-de", "s"),
    "chu_de_nguoi_2": ("--chu-de-nguoi-2", "s"),  # định tính: người mã hoá thứ hai ⇒ kappa Cohen
    # 22/11/2026: định tính — kiểm BẰNG CHỨNG THỦ TỤC của tiêu chí độ tin cậy (credibility · dependability ·
    # transferability) theo khuôn tools/bang_chung_dinh_tinh.py; kết quả DA_KIEM hoặc THIEU_BANG_CHUNG
    "bang_chung": (None, "bang_chung"),
    # 16/11/2026 (biến thể khó): đánh giá chi phí–hiệu quả đi kèm thử nghiệm — CHEERS 2022
    "nhom": ("--nhom", "s"),
    "chi_phi": ("--chi-phi", "s"),
    "hieu_qua": ("--hieu-qua", "s"),
    "nguong_wtp": ("--nguong-wtp", "so"),
    # 21/11/2026 (khoảng trống hệ nghiên cứu — C1a đề cương 4.5.3): giá trị cấu trúc bộ câu hỏi, EFA nửa 1 + CFA nửa
    # 2, chạy bằng phan_tich_nhan_to_r.py (R psych/lavaan; phương pháp đọc từ SAP đã khoá).
    "phan_tich_nhan_to": ("--phan-tich-nhan-to", "nhan_to"),
    "tang": ("--tang", "ds"),
    "thieu": ("--thieu", "thieu"),
    # 22/11/2026 (bác sĩ: «việc máy làm được thì làm trọn»): phân tích SAP trước đây «chờ làm tay» — bảng chéo, chuỗi
    # khâu, KTC hiệu chỉnh quần thể hữu hạn, đáp ứng, đặc tính đo lường, biến thể mô hình thứ tự (spline, phân vị,
    # tương tác, gộp mức, điểm ảnh hưởng, yếu tố riêng), tỷ số chênh tương xứng một phần, hệ số chặn ngẫu nhiên, Firth,
    # trọng số hậu phân tầng, trung gian — chạy bằng phan_tich_sap_bo_sung.py (cấu hình JSON kiểm bằng chính mô-đun đó).
    "loai_bo_sung": ("--loai", "bo_sung"),
    "cau_hinh": ("--cau-hinh", "cau_hinh"),
    # Quy tắc BỎ BIẾN THƯA định trước của SAP (vd C1a §5: `co_hen_gio`, `uu_tien_kham` bỏ khỏi mô hình nếu một nhóm
    # dưới 20 phiếu hợp lệ) — áp TRƯỚC khi gọi run_stats_analysis, chỉ dựa trên phân bố của chính biến; không thành cờ.
    "bien_thua": (None, "bien_thua"),
    # Quy tắc GIẢM THAM SỐ khi EPV dưới ngưỡng, theo thứ tự định trước (vd BTM §5: gộp nhóm đối tượng → gộp phòng khám →
    # bỏ số nhóm thuốc, dừng ngay khi EPV ≥ 10) — áp trước khi gọi run_stats_analysis, chỉ đếm kết cục và số tham số.
    "quy_tac_epv": (None, "quy_tac_epv"),
}
DON_VI_1SD = "1SD"  # đơn vị phơi nhiễm = 1 độ lệch chuẩn trên quần thể phân tích (tính lúc chạy)
MO_HINH_GOP = ("ngau_nhien", "co_dinh")  # gộp: ước lượng báo làm kết quả (độ nhạy SAP §9 hiệu ứng cố định)
DAC_THU = ("chan_doan", "du_bao", "gop", "dinh_tinh", "kinh_te")
NHAN_TO = ("efa_cfa",)
KHOA_NHAN_TO = ("phan_tich_nhan_to", "tang", "thieu", "loc")
LOAI_KC = ("auto", "binary", "continuous", "ordinal", "poisson_pr")
TEN_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")


class TuChoi(RuntimeError):
    pass


class KhongDoDuoc(RuntimeError):
    pass


def thu_muc(study: str) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", study or ""):
        raise TuChoi(f"mã đề tài không hợp lệ: {study!r}")
    d = BASE / "exports" / study
    if not d.is_dir():
        raise TuChoi(f"không có thư mục đề tài exports/{study}")
    return d


def sha256_tep(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def dau_dac_ta(dt: dict) -> str:
    """Dấu 12 hex của (SAP gốc, danh sách phân tích) — cột nguoi_duyet phải mang đúng dấu này."""
    goi = json.dumps([dt.get("sha256_sap"), dt.get("phan_tich")], ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(goi.encode("utf-8")).hexdigest()[:12]


def doc_dac_ta(d: Path) -> dict:
    p = d / TEP_DAC_TA
    if not p.exists():
        raise KhongDoDuoc(f"đề tài chưa có {TEP_DAC_TA}")
    try:
        dt = json.loads(p.read_text(encoding="utf-8"))
    except ValueError as e:
        raise TuChoi(f"{TEP_DAC_TA} không phải JSON hợp lệ: {e}") from e
    if not isinstance(dt, dict):
        raise TuChoi(f"{TEP_DAC_TA} phải là một đối tượng JSON")
    return dt


#: Khoảng hợp lệ của tham số số nguyên (mặc định 0–200: số bộ gán đa trị). Bootstrap hiệu chỉnh lạc quan (22/11/2026):
#: SAP thường khai 200–2.000 lần; trần 5.000 giữ thời gian chạy hữu hạn (mỗi lần khớp lại mô hình ở Python và R).
KHOANG_NGUYEN = {"bootstrap": (0, 5000)}


def _kiem_gia_tri(ten: str, kieu: str, v) -> list[str]:
    def chuoi_an_toan(x) -> bool:
        return isinstance(x, str) and x.strip() != "" and not x.strip().startswith("-") and "\n" not in x

    if kieu == "s":
        if not chuoi_an_toan(v) or (ten != "outcome_type" and not TEN_RE.match(v)):
            return [f"{ten}: cần tên cột hợp lệ"]
        if ten == "outcome_type" and v not in LOAI_KC:
            return [f"outcome_type phải thuộc {LOAI_KC}"]
        if ten == "mo_hinh" and v not in MO_HINH_GOP:
            return [f"mo_hinh phải thuộc {MO_HINH_GOP}"]
    elif kieu in ("ds", "ds_rieng"):
        if not isinstance(v, list) or not v or not all(chuoi_an_toan(x) and TEN_RE.match(x) for x in v):
            return [f"{ten}: cần danh sách tên cột hợp lệ (không rỗng)"]
    elif kieu == "so":
        # 22/11/2026: don_vi_phoi_nhiem «1SD» = hiệu ứng trên mỗi 1 độ lệch chuẩn của phơi nhiễm liên tục (định nghĩa
        # thay thế SAP §9) — SD tính trên quần thể phân tích lúc chạy, ghi vào kết quả
        if ten == "don_vi_phoi_nhiem" and v == DON_VI_1SD:
            return []
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            return [f"{ten}: cần một số"]
    elif kieu == "nguyen":
        lo, hi = KHOANG_NGUYEN.get(ten, (0, 200))
        if isinstance(v, bool) or not isinstance(v, int) or not lo <= v <= hi:
            return [f"{ten}: cần số nguyên {lo}–{hi}"]
    elif kieu == "bang_chung":
        import bang_chung_dinh_tinh as BCD  # noqa: PLC0415

        if v not in BCD.KHUON:
            return [f"{ten}: phải thuộc {sorted(BCD.KHUON)}"]
    elif kieu == "loai":
        if v not in DAC_THU:
            return [f"{ten}: phải thuộc {DAC_THU}"]
    elif kieu == "nhan_to":
        if v not in NHAN_TO:
            return [f"{ten}: phải thuộc {NHAN_TO}"]
    elif kieu == "thieu":
        if v not in ("listwise", "pairwise"):
            return [f"{ten}: phải là listwise hoặc pairwise"]
    elif kieu == "bo_sung":
        import phan_tich_sap_bo_sung as PSB  # noqa: PLC0415

        if v not in PSB.LOAI:
            return [f"{ten}: phải thuộc {sorted(PSB.LOAI)}"]
    elif kieu == "cau_hinh":
        if not isinstance(v, dict) or not v:
            return [f"{ten}: cần đối tượng JSON không rỗng"]
    elif kieu == "bien_thua":
        import phan_tich_sap_bo_sung as PSB  # noqa: PLC0415

        return PSB.kiem_bien_thua(v, ten)
    elif kieu == "quy_tac_epv":
        import phan_tich_sap_bo_sung as PSB  # noqa: PLC0415

        return PSB.kiem_quy_tac_epv(v, ten)
    elif kieu == "bt":
        if not chuoi_an_toan(v):
            return [f"{ten}: cần biểu thức (không bắt đầu bằng «-»)"]
        try:
            BPS.phan_tich(v)
        except BPS.LoiCongThuc as e:
            return [f"{ten}: {e}"]
    return []


def kiem_dac_ta(d: Path, dt: dict) -> dict:
    """Kiểm cấu trúc + SAP còn khớp + trạng thái duyệt. Trả {loi[], canh_bao[], dau, duyet, sap_khop, phan_tich[]}."""
    loi: list[str] = []
    canh_bao: list[str] = []
    sap = d / str(dt.get("nguon_sap") or "")
    sap_khop: bool | None = None
    if not dt.get("nguon_sap") or not sap.is_file():
        loi.append(f"nguon_sap không trỏ tới tệp SAP có thật trong thư mục đề tài ({dt.get('nguon_sap')!r})")
    elif not re.fullmatch(r"[0-9a-f]{64}", str(dt.get("sha256_sap") or "")):
        loi.append("sha256_sap thiếu hoặc sai dạng (64 hex)")
    else:
        sap_khop = sha256_tep(sap) == dt["sha256_sap"]
        if not sap_khop:
            loi.append("SAP đã ĐỔI sau khi soạn đặc tả (SHA-256 khác) — soạn lại theo SAP hiện tại rồi duyệt lại")
    ds = dt.get("phan_tich")
    if not isinstance(ds, list) or not ds:
        loi.append("phan_tich phải là danh sách không rỗng")
        ds = []
    ids: set[str] = set()
    so_chinh = 0
    for i, pt in enumerate(ds):
        nhan = f"phan_tich[{i}]"
        if not isinstance(pt, dict):
            loi.append(f"{nhan}: phải là đối tượng")
            continue
        pid = pt.get("id")
        if not isinstance(pid, str) or not re.fullmatch(r"[A-Za-z0-9_]{1,40}", pid):
            loi.append(f"{nhan}: id phải gồm chữ/số/_ (1–40 ký tự)")
            continue
        if pid in ids:
            loi.append(f"id trùng: {pid}")
        ids.add(pid)
        if pt.get("vai") not in VAI:
            loi.append(f"{pid}: vai phải thuộc {VAI}")
        if not pt.get("sap_muc") or not pt.get("mo_ta"):
            loi.append(f"{pid}: thiếu sap_muc hoặc mo_ta (truy nguyên về SAP)")
        if pt.get("chua_tu_dong"):
            if pt.get("tham_so"):
                loi.append(f"{pid}: đã khai chua_tu_dong thì không khai tham_so")
            if pt.get("vai") == "chinh":
                loi.append(f"{pid}: phân tích CHÍNH không được để «chưa tự động»")
            continue
        ts = pt.get("tham_so")
        if not isinstance(ts, dict) or not ts:
            loi.append(f"{pid}: thiếu tham_so (hoặc khai chua_tu_dong kèm lý do)")
            continue
        la = [k for k in ts if k not in THAM_SO]
        if la:
            loi.append(f"{pid}: tham số không hỗ trợ: {', '.join(la)}")
        for k, v in ts.items():
            if k in THAM_SO:
                loi += [f"{pid}: {x}" for x in _kiem_gia_tri(k, THAM_SO[k][1], v)]
        if ts.get("bang_chung") and len(ts) > 1:
            loi.append(f"{pid}: mục kiểm bằng chứng chỉ khai tham số bang_chung")
        if ts.get("loai_bo_sung") or ts.get("cau_hinh"):
            import phan_tich_sap_bo_sung as PSB  # noqa: PLC0415

            if not ts.get("loai_bo_sung") or not isinstance(ts.get("cau_hinh"), dict):
                loi.append(f"{pid}: loai_bo_sung và cau_hinh phải đi cùng nhau")
            else:
                loi += [f"{pid}: {x}" for x in PSB.kiem_cau_hinh(ts["loai_bo_sung"], ts["cau_hinh"])]
            thua = [x for x in ts if x not in ("loai_bo_sung", "cau_hinh", "loc")]
            if thua:
                loi.append(f"{pid}: tham số không áp dụng cho phân tích bổ sung: {', '.join(thua)}")
        elif ts.get("phan_tich_nhan_to") or ts.get("tang") or ts.get("thieu"):
            # giá trị cấu trúc (EFA/CFA): tham số khác không có nghĩa với phan_tich_nhan_to_r.py — báo ngay khi kiểm
            if not ts.get("phan_tich_nhan_to"):
                loi.append(f"{pid}: tang/thieu chỉ dùng kèm phan_tich_nhan_to")
            elif not ts.get("tang"):
                loi.append(f"{pid}: phân tích nhân tố thiếu tang (cột phân tầng khi chia nửa)")
            thua = [x for x in ts if x not in KHOA_NHAN_TO]
            if thua:
                loi.append(f"{pid}: tham số không áp dụng cho phân tích nhân tố: {', '.join(thua)}")
        elif ts.get("loai_dac_thu"):
            import phan_tich_thiet_ke_dac_thu as PTD  # noqa: PLC0415

            thieu = [x for x in PTD.LOAI.get(ts["loai_dac_thu"], ()) if ts.get(x) in (None, "", [])]
            if thieu:
                loi.append(f"{pid}: phân tích {ts['loai_dac_thu']} thiếu tham số: {', '.join(thieu)}")
            thua = [x for x in ts if x not in (*PTD.LOAI.get(ts["loai_dac_thu"], ()),
                                               *PTD.LOAI_TUY_CHON.get(ts["loai_dac_thu"], ()), "loai_dac_thu", "loc")]
            if thua:  # tham số của run_stats_analysis không có nghĩa với phân tích đặc thù — báo ngay khi kiểm
                loi.append(f"{pid}: tham số không áp dụng cho phân tích {ts['loai_dac_thu']}: {', '.join(thua)}")
        elif ts.get("bang_chung"):  # kiểm bằng chứng thủ tục định tính — không phải mô hình (kiểm ở trên)
            pass
        elif not ts.get("outcome") and not ts.get("time") and not ts.get("ty_le"):
            loi.append(f"{pid}: cần outcome, hoặc time+event, hoặc ty_le")
        if ts.get("bien_thua") and isinstance(ts["bien_thua"], dict):
            ngoai = [b for b in ts["bien_thua"].get("bien") or [] if b not in (ts.get("covariates") or [])]
            if ngoai:
                loi.append(f"{pid}: bien_thua chỉ áp cho hiệp biến của mô hình — không có trong covariates: "
                           f"{', '.join(ngoai)}")
        if ts.get("quy_tac_epv") and isinstance(ts["quy_tac_epv"], dict):
            cov = set(ts.get("covariates") or [])
            ngoai = [b for bu in ts["quy_tac_epv"].get("buoc") or [] if isinstance(bu, dict)
                     for b in [*(bu.get("thay") or {}), *(bu.get("bo") or [])] if b not in cov]
            if ngoai:
                loi.append(f"{pid}: quy_tac_epv thay/bỏ biến không có trong covariates: {', '.join(ngoai)}")
        if bool(ts.get("time")) != bool(ts.get("event")):
            loi.append(f"{pid}: time và event phải đi cùng nhau")
        if pt.get("vai") == "chinh":
            so_chinh += 1
    if so_chinh != 1:
        loi.append(f"cần ĐÚNG một phân tích vai «chinh» có tham_so (đang có {so_chinh})")
    phu: dict = {}
    if sap.is_file() and dt.get("nguon_sap"):
        phu = kiem_phu_sap(dt, sap.read_text(encoding="utf-8"))
        loi += [f"{pid}: SAP hiện tại không có cụm neo «{neo}» (sap_neo trỏ phân tích SAP không còn)"
                for pid, neo in phu["neo_thieu"]]
        loi += [f"SAP {muc} có phân tích chưa vào đặc tả: «{dong[:100]}»" for muc, dong in phu["muc_chua_phu"]]
        loi += [f"SAP {muc} có phân tích PHỤ viết trong câu chưa vào đặc tả: «{md[:140]}» — thêm mục (làm tay thì khai "
                "chua_tu_dong) có sap_neo nằm TRONG đúng mệnh đề này" for muc, md in phu["phu_chua_phu"]]
        canh_bao += [f"{pid}: chưa khai sap_neo (cụm chữ nguyên văn trong SAP) — không truy nguyên được"
                     for pid in phu["chua_neo"]]
        canh_bao += [f"{pid}: cụm neo «{neo}» chỉ nằm trong câu PHỦ ĐỊNH của SAP («{cau}») — SAP có thể đã LOẠI phân "
                     "tích này; thống kê viên xem lại: bỏ mục khỏi đặc tả, hoặc neo vào câu khẳng định"
                     for pid, neo, cau in phu["neo_phu_dinh"]]
        qt = quan_the_chinh_sap(sap.read_text(encoding="utf-8"))
        for pt in ds:
            if not qt or not isinstance(pt, dict) or not isinstance(pt.get("tham_so"), dict):
                continue
            if pt["tham_so"].get("loai_bo_sung") in _quan_the_rieng():
                continue  # loại tự khai hai quần thể trong cấu hình (vd so sánh người bị loại với mẫu)
            bien, gia = qt
            if re.search(rf"\b{re.escape(bien)}\b", str(pt["tham_so"].get("loc") or "")):
                continue
            (loi if pt.get("vai") == "chinh" else canh_bao).append(
                f"{pt.get('id')}: SAP §1 khoanh quần thể chính «`{bien}` = {gia}» nhưng tham_so.loc không lọc theo "
                f"`{bien}` — kết quả (kể cả Bảng 1) sẽ tính cả bản ghi ngoài quần thể")
    dau = dau_dac_ta(dt)
    duyet = BPS.trang_thai_duyet(str(dt.get("nguoi_duyet") or ""), dau)
    if duyet != "DA_DUYET":
        # 18/11/2026: trỏ lệnh duyệt (người duyệt tự chạy) thay vì bảo sửa tay JSON.
        canh_bao.append(f"đặc tả {duyet} — thống kê viên/PI tự chạy `chay_sap_g6.py duyet --study {d.name} "
                        "--vai PI|THONG_KE_VIEN --tham-chieu <mã người duyệt> --ap-dung` "
                        f"(ghi nguoi_duyet «<VAI>:<tham chiếu>:<YYYY-MM-DD>:{dau}»)")
    return {"loi": loi, "canh_bao": canh_bao, "dau": dau, "duyet": duyet, "sap_khop": sap_khop, "phan_tich": ds,
            "phu_sap": phu}


# ─────────── Giai đoạn 7 «Phân tích số liệu» (15/11/2026): đặc tả ↔ SAP HAI CHIỀU ───────────
# Kiểm tay: SAP C1a 1.5 thêm báo cáo đáp ứng/người từ chối, đặc tính đo lường (§3), thăm dò kỳ vọng (§5); SAP BTM thêm
# so sánh nhóm 1 lượt khám — đặc tả G6 soạn trước đó KHÔNG có, và không gì báo (chỉ có SHA lệch ⇒ «đặc tả cũ», không nói
# thiếu phân tích nào). Nay: mỗi mục đặc tả neo vào SAP bằng `sap_neo` (cụm chữ nguyên văn, nhiều cụm cách « | » hoặc
# danh sách); mọi gạch đầu dòng cấp 1 của §9 và mọi mục nhãn đậm là phân tích ở §1/§3/§5/§7 phải có ít nhất một neo.
_MUC_SAP_RE = re.compile(r"^#{2,4}\s*§\s*(\d{1,2})\b[^\n]*\n(.*?)(?=^#{2,4}\s*§\s*\d|^#{1,2}\s|\Z)", re.M | re.S)
_NHAN_PHAN_TICH = re.compile(r"phân tích|đặc tính đo lường|đáp ứng|nhóm nhỏ tiền định", re.I)


def neo_cua(pt: dict) -> list[str]:
    v = pt.get("sap_neo")
    if isinstance(v, list):
        return [str(x).strip() for x in v if str(x).strip()]
    return [x.strip() for x in str(v or "").split("|") if x.strip()]


def muc_sap_bat_buoc(sap_text: str) -> list[tuple[str, str]]:
    """Phân tích SAP mà đặc tả BẮT BUỘC phải phủ: gạch đầu dòng cấp 1 của §9; mục nhãn đậm là phân tích ở §1/§3/§5/§7
    (trừ mục ghi «KHÔNG CÓ»)."""
    import unicodedata  # noqa: PLC0415

    ra: list[tuple[str, str]] = []
    for m in _MUC_SAP_RE.finditer(unicodedata.normalize("NFC", sap_text)):
        muc, than = m.group(1), m.group(2)
        for dong in than.splitlines():
            if not dong.startswith("- "):
                continue
            if muc == "9":
                ra.append((f"§{muc}", dong.strip()))
            elif muc in ("1", "3", "5", "7"):
                nhan = re.match(r"- \*\*(.+?)\*\*", dong)
                if nhan and _NHAN_PHAN_TICH.search(nhan.group(1)) and "KHÔNG CÓ" not in dong.upper():
                    ra.append((f"§{muc}", dong.strip()))
    return ra


_BIEN_BANG_RE = re.compile(r"`([A-Za-z_][A-Za-z0-9_]*)`\s*={1,2}\s*'?([A-Za-z0-9_.-]+)'?")


def quan_the_chinh_sap(sap_text: str) -> tuple[str, str] | None:
    """(biến, giá trị) SAP §1 dùng khoanh «Quần thể chính» (vd «mọi hồ sơ có `du_tieu_chuan` = 1»); không thấy ⇒ None.

    17/11/2026 (giả lập dữ liệu trên khung BTM): bộ dữ liệu BTM ghi CẢ hồ sơ bị loại ở bước sàng lọc (phiếu phần A);
    thống kê viên mô phỏng quên `loc` ⇒ Bảng 1 tính trên 458 hồ sơ đã mở (gồm 73 hồ sơ loại và biến sàng lọc) thay vì
    385 người của quần thể phân tích, G7 chép N = 458 vào bản thảo. Hệ đã có `tham_so.loc` nhưng không gì nhắc."""
    import unicodedata  # noqa: PLC0415

    for m in _MUC_SAP_RE.finditer(unicodedata.normalize("NFC", sap_text)):
        if m.group(1) != "1":
            continue
        for dong in m.group(2).splitlines():
            if "quần thể chính" in dong.casefold():
                k = _BIEN_BANG_RE.search(dong)
                if k:
                    return k.group(1), k.group(2)
    return None


# 18/11/2026 — cụm neo nằm trong câu PHỦ ĐỊNH: đặc tả BTM giữ mục `MT1_fpc` neo «quần thể hữu hạn» trong khi SAP §4 ghi
# «Không áp hiệu chỉnh quần thể hữu hạn» (chủ nhiệm đã bỏ) — phép khớp chuỗi coi là neo hợp lệ nên `kiem` không báo, mục
# bị SAP loại vẫn sẽ chạy. Nay: MỌI lần xuất hiện của cụm neo đều đứng sau một từ phủ định trong cùng mệnh đề ⇒ CẢNH BÁO
# (không chặn — nhận diện phủ định bằng luật có thể nhầm; thống kê viên quyết).
_TU_PHU_DINH = re.compile(r"(?<!\w)(?:không|chưa|chẳng|loại bỏ|bỏ|thay vì)(?!\w)")
_RANH_GIOI_MENH_DE = re.compile(r"[.;:!?\n,()]|—|–")
CUA_SO_PHU_DINH = 50  # ký tự trước cụm neo được xét (đủ cho «Không áp hiệu chỉnh …», không với sang mệnh đề khác)


def _bi_phu_dinh(sap_cf: str, vi_tri: int) -> bool:
    """Cụm neo bắt đầu ở `vi_tri` (trong văn bản đã casefold) đứng sau một từ phủ định của CÙNG mệnh đề."""
    truoc = sap_cf[max(0, vi_tri - CUA_SO_PHU_DINH):vi_tri]
    ranh = list(_RANH_GIOI_MENH_DE.finditer(truoc))
    if ranh:
        truoc = truoc[ranh[-1].end():]
    return bool(_TU_PHU_DINH.search(truoc))


def _cau_quanh(sap: str, vi_tri: int, do_dai: int) -> str:
    """Câu (giữa hai dấu chấm/xuống dòng) chứa vị trí — để in kèm cảnh báo."""
    dau = max(sap.rfind(".", 0, vi_tri), sap.rfind("\n", 0, vi_tri)) + 1
    cuoi = [i for i in (sap.find(".", vi_tri + do_dai), sap.find("\n", vi_tri + do_dai)) if i != -1]
    return sap[dau:(min(cuoi) if cuoi else len(sap))].strip()[:160]


def neo_chi_trong_cau_phu_dinh(sap_text: str, neo: str) -> str | None:
    """Câu phủ định đầu tiên nếu MỌI lần cụm `neo` xuất hiện trong SAP đều bị phủ định.

    None nếu có ít nhất một lần khẳng định (hoặc cụm không có trong SAP — việc đó do `neo_thieu` báo)."""
    import unicodedata  # noqa: PLC0415

    sap = unicodedata.normalize("NFC", sap_text)
    sap_cf, neo_cf = sap.casefold(), unicodedata.normalize("NFC", neo).casefold()
    if not neo_cf or len(sap_cf) != len(sap):  # casefold đổi độ dài (hiếm với tiếng Việt) ⇒ không định vị được, bỏ qua
        return None
    vi_tri = [m.start() for m in re.finditer(re.escape(neo_cf), sap_cf)]
    if not vi_tri or not all(_bi_phu_dinh(sap_cf, i) for i in vi_tri):
        return None
    return _cau_quanh(sap, vi_tri[0], len(neo_cf))


# 18/11/2026 — phân tích PHỤ viết LIỀN trong câu văn: bỏ nhầm `MT1_fpc` (BTM, #313) không làm gì đỏ vì luật phủ chỉ đòi
# gạch đầu dòng §9 và mục nhãn đậm ở §1/§3/§5/§7; câu «nếu biết khung mẫu thì báo thêm KTC có hiệu chỉnh … như một thông
# tin phụ» nằm giữa gạch đầu dòng «Phương pháp» của §4 — cùng dòng với neo của phân tích CHÍNH, nên phủ theo DÒNG cũng
# không bắt được. Nay mỗi MỆNH ĐỀ (tách theo «.»/«;») mang dấu hiệu phân tích phụ phải có cụm neo NẰM TRONG chính nó.
_TU_PHAN_TICH_PHU = re.compile(r"(?<!\w)(?:báo thêm|trình bày thêm|tính thêm|ước lượng thêm|kèm thêm|chạy thêm|làm thêm"
                               r"|thông tin phụ|phân tích phụ|phân tích bổ sung)(?!\w)")


def menh_de_phan_tich_phu(sap_text: str) -> list[tuple[str, str]]:
    """Mệnh đề SAP hứa một phân tích PHỤ viết liền trong câu (ngoài §9 — §9 đã đòi phủ cả gạch đầu dòng).

    Bỏ qua: dấu hiệu bị phủ định («không báo thêm …»), dòng bảng, tiêu đề, khối mã, trích dẫn. Đo 18/11/2026: 2 SAP thật
    + 16 SAP giả lập ⇒ đúng 2 mệnh đề, cả hai là phân tích phụ thật (BTM §4 KTC hiệu chỉnh FPC, §5 mô hình biến chia
    nhóm)."""
    import unicodedata  # noqa: PLC0415

    ra: list[tuple[str, str]] = []
    for m in _MUC_SAP_RE.finditer(unicodedata.normalize("NFC", sap_text)):
        muc, than = m.group(1), m.group(2)
        if muc == "9":
            continue
        for dong in than.splitlines():
            s = dong.strip()
            if not s or s.startswith(("|", "#", "```", ">")):
                continue
            for menh_de in re.split(r"(?<=[.;])\s+", s):
                cf = menh_de.casefold()
                if any(not _bi_phu_dinh(cf, k.start()) for k in _TU_PHAN_TICH_PHU.finditer(cf)):
                    ra.append((f"§{muc}", menh_de.strip()))
    return ra


def kiem_phu_sap(dt: dict, sap_text: str) -> dict:
    """{neo_thieu: [(id, neo)], chua_neo: [id], muc_chua_phu: [(§k, dòng)], phu_chua_phu: [(§k, mệnh đề)],
    neo_phu_dinh: [(id, neo, câu)]} — đặc tả ↔ SAP hai chiều."""
    import unicodedata  # noqa: PLC0415

    sap = unicodedata.normalize("NFC", sap_text).casefold()
    ds = [pt for pt in dt.get("phan_tich") or [] if isinstance(pt, dict)]
    neo = [(str(pt.get("id")), unicodedata.normalize("NFC", n)) for pt in ds for n in neo_cua(pt)]
    phu_dinh = []
    for pt in ds:  # mục có ít nhất một neo khẳng định thì không cảnh báo (neo phụ có thể nằm trong câu loại trừ)
        cac_neo = neo_cua(pt)
        cau = [neo_chi_trong_cau_phu_dinh(sap_text, n) for n in cac_neo if n.casefold() in sap]
        if cau and all(cau):
            phu_dinh.append((str(pt.get("id")), cac_neo[0], cau[0]))
    return {"neo_thieu": [(pid, n) for pid, n in neo if n.casefold() not in sap],
            "chua_neo": [str(pt.get("id")) for pt in ds if not neo_cua(pt)],
            "muc_chua_phu": [(muc, dong) for muc, dong in muc_sap_bat_buoc(sap_text)
                             if not any(n.casefold() in dong.casefold() for _, n in neo)],
            "phu_chua_phu": [(muc, md) for muc, md in menh_de_phan_tich_phu(sap_text)
                             if not any(n.casefold() in md.casefold() for _, n in neo)],
            "neo_phu_dinh": phu_dinh}


def _quan_the_rieng() -> tuple:
    import phan_tich_sap_bo_sung as PSB  # noqa: PLC0415

    return PSB.QUAN_THE_RIENG


def gate_cua(pt: dict) -> str:
    return "G6" if pt.get("vai") == "chinh" else f"G6_{pt['id']}"


def doi_so_run_stats(pt: dict) -> list[str]:
    ds: list[str] = []
    for k, v in (pt.get("tham_so") or {}).items():
        co, kieu = THAM_SO[k]
        if co is None:  # xử lý trước khi chạy (bien_thua) — không thành cờ
            continue
        if kieu == "cau_hinh":
            ds += [co, json.dumps(v, ensure_ascii=False, sort_keys=True)]
            continue
        if kieu == "ds":
            ds += [co, ",".join(v)]
        elif kieu == "ds_rieng":
            ds += [co, *v]
        elif kieu in ("so", "nguyen"):
            ds += [co, format(v, "g") if isinstance(v, float) else str(v)]
        else:
            ds += [co, str(v)]
    if any(x.startswith("--i-confirm") for x in ds):  # rào cứng: không bao giờ ghi đè cổng
        raise TuChoi("cờ ghi đè cổng bị cấm")
    return ds


def _tom_tat_uoc_luong(tom: dict) -> dict:
    """Vài ước lượng chính của MỘT lượt (để chỉ mục đọc nhanh) — không thay bảng đầy đủ."""
    ra: dict = {"n_total": tom.get("n_total")}
    if tom.get("loc"):
        ra["loc"] = tom["loc"]
    pc = tom.get("primary_outcome") or {}
    if pc.get("or_crude") is not None:
        ra["or_tho"] = {"uoc_luong": pc["or_crude"], "ci_95": pc.get("ci_95"), "p": pc.get("p_value")}
    elif pc.get("md_crude") is not None:
        ra["md_tho"] = {"uoc_luong": pc["md_crude"], "p": pc.get("p_value")}
    nhom = (tom.get("dac_ta_phan_tich") or {}).get("group")
    for khoa, nhan in (("multivariate", "da_bien"), ("ordinal", "thu_tu"), ("poisson_pr", "poisson_pr")):
        mv = tom.get(khoa) or {}
        if mv.get("error"):
            ra[nhan] = {"loi": mv["error"]}
            continue
        for r in mv.get("results") or []:
            if r.get("variable") in (nhom, f"{nhom}_dv") or str(r.get("variable", "")).startswith(f"{nhom}"):
                ra[nhan] = {k: r.get(k) for k in ("variable", "OR_adj", "beta", "PR_adj", "OR", "CI_95", "p") if k in r}
                break
    if tom.get("ty_le"):
        # 22/11/2026: tóm tắt ghi tỷ lệ 0–1 + «CI_95» (cụm) / «CI_95_wilson_doc_lap»; chỉ mục (và
        # dinh_dang_uoc_luong) dùng PHẦN TRĂM + «ci_95». Bản cũ chép thẳng ⇒ «Tỷ lệ 0,4%» và mất KTC.
        ds_tl = []
        for x in tom["ty_le"][:6]:
            ci = x.get("CI_95") or x.get("CI_95_wilson_doc_lap")
            mot = {"cot": x.get("cot"), "n": x.get("n")}
            if x.get("ty_le") is not None:
                mot["ty_le"] = round(100 * float(x["ty_le"]), 2)
            if isinstance(ci, (list, tuple)) and len(ci) == 2 and None not in ci:
                mot["ci_95"] = [round(100 * float(v), 2) for v in ci]
            if x.get("error"):
                mot["loi"] = x["error"]
            ds_tl.append(mot)
        ra["ty_le"] = ds_tl
    if tom.get("dac_thu"):  # 16/11/2026: phân tích đặc thù — vài ước lượng chính theo loại
        dt_, loai = tom["dac_thu"], tom.get("loai_dac_thu")
        if loai == "chan_doan":
            ra["chan_doan"] = {"auc": dt_["auc"]["auc"], "ci_95": dt_["auc"]["ci_95"],
                               "do_nhay": dt_["do_nhay"]["uoc_luong"], "do_dac_hieu": dt_["do_dac_hieu"]["uoc_luong"]}
        elif loai == "du_bao":
            ra["du_bao"] = {"c_statistic": dt_["c_statistic"]["auc"], "brier": dt_["brier"]}
            bt = dt_.get("bootstrap") or {}
            if bt:  # 22/11/2026 (việc B): chỉ số hiệu chỉnh lạc quan (Python) + bản R chạy thật
                ra["du_bao"]["bootstrap"] = {k: bt.get(k) for k in ("B_hop_le", "c_hieu_chinh", "do_doc_hieu_chinh",
                                                                    "citl_hieu_chinh", "r", "kiem_cheo_r")}
        elif loai == "gop":
            # 22/11/2026: mục đặc tả mo_hinh «co_dinh» báo ước lượng nghịch đảo phương sai (độ nhạy SAP §9)
            co_dinh = (tom.get("dac_ta_phan_tich") or {}).get("mo_hinh") == "co_dinh"
            ra["gop"] = {"rr": dt_["rr_gop_co_dinh" if co_dinh else "rr_gop_ngau_nhien"],
                         "ci_95": dt_["ci_95_co_dinh" if co_dinh else "ci_95"], "i2": dt_["i2_pct"], "k": dt_["k"],
                         "mo_hinh": "co_dinh" if co_dinh else "ngau_nhien"}
            eg, pn = dt_.get("egger") or {}, dt_.get("phan_nhom") or {}
            if eg.get("da_chay"):
                ra["gop"]["egger_p"] = eg["p"]
            if pn.get("q_giua_nhom") is not None:
                ra["gop"] |= {"phan_nhom": pn["bien"], "q_giua_nhom": pn["q_giua_nhom"],
                              "p_giua_nhom": pn["p_giua_nhom"]}
        elif loai == "kinh_te":
            ra["kinh_te"] = {"icer": dt_["icer"], "delta_c": dt_["delta_c"], "delta_e": dt_["delta_e"],
                             "goc_phan_tu": dt_["goc_phan_tu"], "nmb_tai_wtp": dt_["nmb_tai_wtp"]}
        else:
            ra["dinh_tinh"] = {"so_chu_de": dt_["so_chu_de"], "n": dt_["n_ban_go_bang"]}
            if dt_.get("dong_thuan_hai_nguoi"):  # 22/11/2026: kappa hai người mã hoá (SAP §9 confirmability)
                dth = dt_["dong_thuan_hai_nguoi"]
                ra["dinh_tinh"] |= {"kappa": dth["kappa"], "n_cap": dth["n_cap"], "ty_le_trung": dth["ty_le_trung"]}
    if tom.get("nhan_to"):  # 21/11/2026: giá trị cấu trúc — số nhân tố gợi ý (nửa 1) + chỉ số phù hợp scaled (nửa 2)
        nt = tom["nhan_to"]
        efa, cfa = nt.get("efa") or {}, nt.get("cfa") or {}
        cs = cfa.get("chi_so") or {}
        ra["nhan_to"] = {"so_nhan_to_song_song": (efa.get("song_song") or {}).get("so_nhan_to"),
                         "cfa_hoi_tu": cfa.get("hoi_tu"),
                         **{k.replace(".", "_"): cs.get(k) for k in ("cfi.scaled", "tli.scaled", "rmsea.scaled",
                                                                     "srmr")},
                         "phan_loai": nt.get("phan_loai_theo_nguong_dinh_truoc")}
    if tom.get("bo_sung") is not None:  # 22/11/2026: phân tích bổ sung — khoá chính đọc nhanh; bảng đủ ở tóm tắt
        bs = tom["bo_sung"]
        ra["bo_sung"] = {"loai": tom.get("loai_bo_sung"),
                         "khoa": sorted(k for k in bs if k not in ("canh_bao", "phien_ban_goi", "phien_ban_r"))[:12]}
    sv = tom.get("survival") or {}
    if (sv.get("adjusted") or {}).get("HR") is not None:
        ra["hr_hieu_chinh"] = {k: sv["adjusted"].get(k) for k in ("HR", "CI_95", "p")}
    return ra


def _doc_json(p: Path) -> dict:
    try:
        x = json.loads(p.read_text(encoding="utf-8"))
        return x if isinstance(x, dict) else {}
    except (OSError, ValueError):
        return {}


def lenh_kiem(args) -> int:
    d = thu_muc(args.study)
    dt = doc_dac_ta(d)
    k = kiem_dac_ta(d, dt)
    if args.json:
        print(json.dumps({x: k[x] for x in ("loi", "canh_bao", "dau", "duyet", "sap_khop")} | {
            "phan_tich": [{"id": p.get("id"), "vai": p.get("vai"), "sap_muc": p.get("sap_muc"),
                           "chua_tu_dong": p.get("chua_tu_dong")} for p in k["phan_tich"] if isinstance(p, dict)]},
            ensure_ascii=False, indent=1))  # fmt: skip
    else:
        print(f"Đặc tả SAP G6 — {args.study}: {len(k['phan_tich'])} phân tích · dấu {k['dau']} · {k['duyet']}"
              f" · SAP {'khớp' if k['sap_khop'] else 'KHÔNG khớp/không đo được'}")  # fmt: skip
        for p in k["phan_tich"]:
            if isinstance(p, dict):
                tt = f"CHỜ LÀM TAY: {p['chua_tu_dong']}" if p.get("chua_tu_dong") else f"gate {gate_cua(p)}"
                print(f"  {p.get('id', '?'):24} {p.get('vai', '?'):9} {p.get('sap_muc', ''):6} {tt}")
        for x in k["loi"]:
            print(f"  ✗ {x}")
        for x in k["canh_bao"]:
            print(f"  ⚠ {x}")
        print(CAN_KIEM)
    return 1 if k["loi"] else 0


def lenh_duyet(args) -> int:
    """GHI DUYỆT đặc tả — lệnh của THỐNG KÊ VIÊN/PI tự chạy (18/11/2026).

    Bác sĩ: «Giải quyết đặc tả G6 giúp tôi». Hợp đồng giữ nguyên «agent soạn đặc tả, KHÔNG ghi nguoi_duyet»; trước đây
    người duyệt phải sửa tay JSON và chép đúng dấu 12 hex — dễ sai dạng (SAI_DANG). Lệnh này ghi
    «<VAI>:<tham chiếu>:<hôm nay>:<dấu đặc tả hiện tại>», cùng khuôn `bien_phai_sinh.py duyet`. Chạy khô mặc định —
    `--ap-dung` mới ghi; đặc tả còn lỗi hoặc SAP đã đổi so với đặc tả ⇒ từ chối (không duyệt đặc tả chưa đúng); sao lưu
    tệp trước khi ghi. Sửa đặc tả sau đó ⇒ dấu đổi ⇒ HET_HIEU_LUC (`kiem`)."""
    from datetime import date as _date  # noqa: PLC0415

    vai = (args.vai or "").strip().upper()
    ref = (args.tham_chieu or "").strip()
    if vai not in BPS.VAI_DUYET:
        raise TuChoi(f"--vai phải là một trong {', '.join(BPS.VAI_DUYET)}")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{1,40}", ref):
        raise TuChoi("--tham-chieu là mã người duyệt (chữ, số, «.», «_», «-»; không dấu «:») — vd TKV-BTM-01, "
                     "PI-BTM-01")
    d = thu_muc(args.study)
    dt = doc_dac_ta(d)
    k = kiem_dac_ta(d, dt)
    if k["loi"]:
        print("✗ Đặc tả còn lỗi — không duyệt (sửa đặc tả rồi chạy lại):")
        for x in k["loi"][:10]:
            print(f"    {x}")
        return 1
    if not k["sap_khop"]:
        raise TuChoi("SAP đã đổi so với lúc soạn đặc tả (sha256_sap lệch) — soạn lại đặc tả theo SAP hiện tại trước")
    cu = str(dt.get("nguoi_duyet") or "").strip()
    moi = f"{vai}:{ref}:{_date.today().isoformat()}:{k['dau']}"
    if BPS.trang_thai_duyet(cu, k["dau"]) == "DA_DUYET" and [x.strip() for x in cu.split(":")][:2] == [vai, ref]:
        print(f"Đặc tả SAP G6 — {args.study}: đã duyệt, còn hiệu lực ({cu}) — giữ nguyên. {CAN_KIEM}")
        return 0
    print(f"{'GHI' if args.ap_dung else 'SẼ GHI'} DUYỆT đặc tả SAP G6 — {args.study}: {len(k['phan_tich'])} phân tích")
    print(f"  nguoi_duyet: {moi}" + (f"  (thay «{cu}»)" if cu else ""))
    if not args.ap_dung:
        print("Thêm --ap-dung để ghi. Lệnh dành cho THỐNG KÊ VIÊN/PI tự chạy — agent không chạy. " + CAN_KIEM)
        return 0
    p = d / TEP_DAC_TA
    tho = p.read_text(encoding="utf-8")
    sao_luu = p.with_name(f"{p.name}.bak-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
    sao_luu.write_text(tho, encoding="utf-8", newline="\n")
    dt["nguoi_duyet"] = moi
    # Giữ định dạng tệp (đặc tả thật thụt lề 1; tệp một dòng thì ghi một dòng) — diff chỉ đúng dòng nguoi_duyet.
    dong = tho.splitlines()
    thut = (len(dong[1]) - len(dong[1].lstrip(" ")) or 2) if len(dong) > 1 else None
    p.write_text(json.dumps(dt, ensure_ascii=False, indent=thut) + "\n", encoding="utf-8", newline="\n")
    dt_sau = doc_dac_ta(d)
    sau = BPS.trang_thai_duyet(str(dt_sau.get("nguoi_duyet") or ""), dau_dac_ta(dt_sau))
    print(f"✓ Đã ghi; sao lưu {sao_luu.name}. Đo lại: đặc tả {sau}. {CAN_KIEM}")
    return 0 if sau == "DA_DUYET" else 1


def ap_bien_thua_dac_ta(study: str, pt: dict) -> tuple[dict, dict]:
    """Áp quy tắc bỏ biến thưa (tham_so.bien_thua) lên MỘT mục đặc tả: đếm phân bố của từng biến trên ĐÚNG quần thể
    phân tích (dữ liệu khoá + biến phái sinh + `loc`), biến có một nhóm dưới ngưỡng bị bỏ khỏi covariates và
    hiep_bien_phan_loai. Trả (mục đã sửa — bản sao, không đụng đặc tả trên đĩa; bảng quyết định)."""
    import phan_tich_sap_bo_sung as PSB  # noqa: PLC0415

    ts = dict(pt["tham_so"])
    bt = ts.pop("bien_thua")
    df, _csv, _man = PSB.doc_df(study, list(bt["bien"]), ts.get("loc"))
    kq = PSB.quy_tac_bien_thua(df, bt["bien"], int(bt["toi_thieu"]))
    ts = PSB.ap_bien_thua(ts, kq, "covariates", "hiep_bien_phan_loai")
    if not ts.get("hiep_bien_phan_loai"):
        ts.pop("hiep_bien_phan_loai", None)
    return dict(pt, tham_so=ts), kq


def ap_quy_tac_epv_dac_ta(study: str, pt: dict) -> tuple[dict, dict]:
    """Áp quy tắc giảm tham số theo EPV (tham_so.quy_tac_epv) lên MỘT mục: EPV đếm trên ĐÚNG quần thể phân tích.
    Trả (mục đã sửa — bản sao; nhật ký từng bước)."""
    import phan_tich_sap_bo_sung as PSB  # noqa: PLC0415

    ts = dict(pt["tham_so"])
    q = ts.pop("quy_tac_epv")
    moi = [m for b in q["buoc"] for m in (b.get("thay") or {}).values()]
    can = [ts["outcome"], ts["group"], *(ts.get("covariates") or []), *moi]
    df, _csv, _man = PSB.doc_df(study, can, ts.get("loc"))
    ts, nk = PSB.quy_tac_epv(df, ts, q)
    return dict(pt, tham_so=ts), nk


def ap_don_vi_1sd(study: str, pt: dict) -> tuple[dict, dict]:
    """don_vi_phoi_nhiem «1SD» ⇒ số: độ lệch chuẩn (ddof = 1) của phơi nhiễm trên ĐÚNG tập ca của mô hình (quần thể
    phân tích sau lọc, đủ kết cục · phơi nhiễm · hiệp biến) — cùng tập ca run_stats_analysis dùng. Trả (mục đã sửa —
    bản sao; nhật ký)."""
    import pandas as pd  # noqa: PLC0415
    import phan_tich_sap_bo_sung as PSB  # noqa: PLC0415

    ts = dict(pt["tham_so"])
    can = [c for c in (ts.get("outcome"), ts.get("group"), ts.get("time"), ts.get("event"),
                       *(ts.get("covariates") or [])) if c]
    df, _csv, _man = PSB.doc_df(study, can, ts.get("loc"))
    x = pd.to_numeric(df[ts["group"]], errors="coerce")
    o = df[can].notna().all(axis=1) & x.notna()
    sd = float(x[o].std(ddof=1)) if int(o.sum()) > 1 else float("nan")
    if not sd > 0:
        raise TuChoi(f"không tính được độ lệch chuẩn của {ts['group']} (n = {int(o.sum())})")
    nk = {"bien": ts["group"], "sd": sd, "n": int(o.sum()),
          "cach_tinh": "độ lệch chuẩn mẫu (ddof = 1) trên tập ca đủ biến của mô hình"}
    ts["don_vi_phoi_nhiem"] = sd  # run_stats_analysis + cầu nối R/SPSS chia phơi nhiễm cho 1 SD ở mọi họ mô hình
    return dict(pt, tham_so=ts), nk


def lenh_chay(args) -> int:
    d = thu_muc(args.study)
    dt = doc_dac_ta(d)
    k = kiem_dac_ta(d, dt)
    if k["loi"]:
        raise TuChoi("đặc tả không hợp lệ: " + "; ".join(k["loi"][:5]))
    gia_lap = BPS.la_de_tai_gia_lap(d)
    if k["duyet"] != "DA_DUYET" and not gia_lap:
        raise TuChoi(f"đặc tả {k['duyet']} — chỉ chạy khi thống kê viên/PI đã duyệt (dấu {k['dau']})")
    import cau_noi_spss as S  # noqa: PLC0415 — kiểm khoá G5 bằng ĐÚNG hàm của cổng

    try:
        csv_khoa, _man = S.tim_du_lieu_khoa(args.study)
    except Exception as e:  # noqa: BLE001
        raise TuChoi(f"chưa có dữ liệu ĐÃ KHOÁ (G5) dùng được: {e}") from e
    chi = {x.strip() for x in (args.chi or "").split(",") if x.strip()}
    nk = d / THU_MUC_NHAT_KY
    nk.mkdir(exist_ok=True)
    ket: list[dict] = []
    ma = 0
    for pt in k["phan_tich"]:
        if chi and pt["id"] not in chi:
            continue
        muc = {"id": pt["id"], "vai": pt["vai"], "sap_muc": pt.get("sap_muc"), "mo_ta": pt.get("mo_ta")}
        if pt.get("chua_tu_dong"):
            ket.append(muc | {"trang_thai": "CHUA_TU_DONG", "ly_do": pt["chua_tu_dong"]})
            print(f"⏸  {pt['id']}: CHỜ thống kê viên làm tay — {pt['chua_tu_dong']}")
            continue
        gate = gate_cua(pt)
        ts_pt = pt.get("tham_so") or {}
        if ts_pt.get("bang_chung"):  # định tính: kiểm bằng chứng thủ tục — không phải phép tính, không kiểm chéo
            import bang_chung_dinh_tinh as BCD  # noqa: PLC0415

            bc = BCD.kiem(d, args.study, ts_pt["bang_chung"])
            tt = "DA_KIEM" if bc["trang_thai"] == BCD.DA_KIEM else "THIEU_BANG_CHUNG"
            ket.append(muc | {"gate": gate, "trang_thai": tt, "uoc_luong": bc,
                              "ly_do": "; ".join(bc["thieu"]) or None})
            print(f"{'✓' if tt == 'DA_KIEM' else '✗'} {pt['id']}: {bc['nhan']} — {'; '.join(bc['thieu']) or 'đủ'}")
            continue
        if ts_pt.get("quy_tac_epv"):  # giảm tham số theo thứ tự định trước — chỉ đếm kết cục và cấu trúc biến
            try:
                pt, qe = ap_quy_tac_epv_dac_ta(args.study, pt)
            except Exception as e:  # noqa: BLE001
                muc |= {"gate": gate, "trang_thai": "LOI", "ly_do": f"quy tắc EPV: {e}"[:500]}
                ket.append(muc)
                ma = 1
                print(f"   ✗ lỗi quy tắc EPV — {e}")
                continue
            muc["quy_tac_epv"] = qe
            ts_pt = pt.get("tham_so") or {}
            print(f"   quy tắc EPV: áp tới bước {qe['buoc_ap']} · EPV cuối {qe['epv_cuoi']:.2f}")
        if ts_pt.get("don_vi_phoi_nhiem") == DON_VI_1SD:  # định nghĩa thay thế: phơi nhiễm liên tục, mỗi 1 SD
            try:
                pt, sd1 = ap_don_vi_1sd(args.study, pt)
            except Exception as e:  # noqa: BLE001
                muc |= {"gate": gate, "trang_thai": "LOI", "ly_do": f"đơn vị 1 SD: {e}"[:500]}
                ket.append(muc)
                ma = 1
                print(f"   ✗ lỗi đơn vị 1 SD — {e}")
                continue
            muc["don_vi_1sd"] = sd1
            ts_pt = pt.get("tham_so") or {}
            print(f"   đơn vị phơi nhiễm: 1 SD của {sd1['bien']} = {sd1['sd']:.4g} (n = {sd1['n']})")
        if ts_pt.get("bien_thua"):  # quy tắc bỏ biến thưa định trước — phân bố của chính biến, trước khi xem kết cục
            try:
                pt, bt = ap_bien_thua_dac_ta(args.study, pt)
            except Exception as e:  # noqa: BLE001
                muc |= {"gate": gate, "trang_thai": "LOI", "ly_do": f"quy tắc biến thưa: {e}"[:500]}
                ket.append(muc)
                ma = 1
                print(f"   ✗ lỗi quy tắc biến thưa — {e}")
                continue
            muc["bien_thua"] = bt
            print(f"   quy tắc biến thưa: bỏ {bt['bo'] or 'không biến nào'} (ngưỡng {bt['toi_thieu']})")
        if ts_pt.get("phan_tich_nhan_to"):  # R psych/lavaan — tự đọc bộ khoá bằng cùng hàm của cổng; không kiểm chéo
            lenh = [sys.executable, str(TOOLS / "phan_tich_nhan_to_r.py"), "chay", "--study", args.study,
                    "--gate", gate, *doi_so_run_stats(pt)]  # fmt: skip
        elif ts_pt.get("loai_bo_sung"):  # phân tích SAP bổ sung — tự đọc bộ khoá bằng cùng hàm của cổng
            lenh = [sys.executable, str(TOOLS / "phan_tich_sap_bo_sung.py"), "--study", args.study, "--gate", gate,
                    *doi_so_run_stats(pt)]  # fmt: skip
        else:
            cong_cu = "phan_tich_thiet_ke_dac_thu.py" if (pt.get("tham_so") or {}).get("loai_dac_thu") else \
                "run_stats_analysis.py"
            lenh = [sys.executable, str(TOOLS / cong_cu), "--data", str(csv_khoa), "--study", args.study,
                    "--gate", gate, *doi_so_run_stats(pt), *(["--kiem-cheo"] if args.kiem_cheo else [])]  # fmt: skip
        print(f"▶  {pt['id']} ({pt['vai']}, {pt.get('sap_muc')}) — gate {gate}", flush=True)
        try:
            r = subprocess.run(lenh, capture_output=True, text=True, encoding="utf-8", errors="replace",
                               timeout=THOI_HAN, stdin=subprocess.DEVNULL, cwd=BASE, check=False)  # fmt: skip
            ma_pt, out, err = r.returncode, r.stdout, r.stderr
        except subprocess.TimeoutExpired:
            ma_pt, out, err = None, "", f"quá thời hạn {THOI_HAN} giây"
        (nk / f"{pt['id']}.log").write_text(out + ("\n--- stderr ---\n" + err if err else ""), encoding="utf-8",
                                            newline="\n")  # fmt: skip
        tom = _doc_json(d / f"{gate}_analysis_summary.json")
        muc |= {"gate": gate, "ma_thoat": ma_pt, "nhat_ky": f"{THU_MUC_NHAT_KY}/{pt['id']}.log"}
        if ma_pt != 0 or not tom:
            dong_cuoi = [x for x in (out + "\n" + err).splitlines() if x.strip()][-3:]
            muc |= {"trang_thai": "LOI", "ly_do": " | ".join(dong_cuoi)[:500]}
            ma = 1
            print(f"   ✗ lỗi (mã {ma_pt}) — {muc['ly_do'][:200]}")
        else:
            muc |= {"trang_thai": "DA_CHAY", "uoc_luong": _tom_tat_uoc_luong(tom)}
            if args.kiem_cheo:
                kc = _doc_json(d / f"{gate}_kiem_cheo.json")
                muc["kiem_cheo"] = kc.get("trang_thai") or "KHONG_DO_DUOC"
                if muc["kiem_cheo"] in ("LECH", "LOI", "TU_CHOI"):
                    ma = max(ma, 1)
            print("   ✓ xong" + (f" · kiểm chéo {muc.get('kiem_cheo')}" if args.kiem_cheo else ""))
        ket.append(muc)
    chi_muc = {
        "study": args.study,
        "luc": datetime.now().astimezone().isoformat(timespec="seconds"),
        "dac_ta": {"tep": TEP_DAC_TA, "dau": k["dau"], "duyet": k["duyet"], "sha256_sap": dt.get("sha256_sap")},
        "du_lieu_khoa": {"tep": str(csv_khoa.relative_to(d)) if csv_khoa.is_relative_to(d) else csv_khoa.name,
                         "sha256": sha256_tep(csv_khoa)},  # fmt: skip
        "kiem_cheo": bool(args.kiem_cheo),
        "phan_tich": ket,
        # trạng thái kiểm bằng chứng định tính (DA_KIEM · THIEU_BANG_CHUNG) chỉ ghi khi có — giữ khuôn đếm cũ
        "dem": {t: n for t in ("DA_CHAY", "LOI", "CHUA_TU_DONG", "DA_KIEM", "THIEU_BANG_CHUNG")
                if (n := sum(1 for x in ket if x["trang_thai"] == t)) or t in ("DA_CHAY", "LOI", "CHUA_TU_DONG")},
        "canh_bao": (["ĐỀ TÀI GIẢ LẬP — đặc tả chưa duyệt"] if k["duyet"] != "DA_DUYET" else []),
        "disclaimer": CAN_KIEM,
    }
    md_hinh = ""
    if not getattr(args, "khong_ve", False):  # 21/11/2026: tự sinh biểu đồ kết quả theo thiết kế (hinh_g6)
        try:
            import hinh_g6 as HG6  # noqa: PLC0415

            meta = _doc_json(d / "study_meta.json")
            g1 = (meta.get("gate_params") or {}).get("G1") or {}
            hg = HG6.sinh(args.study, d, [p for p in k["phan_tich"] if not chi or p["id"] in chi], chi_muc,
                          str(g1.get("design") or meta.get("design_code") or ""))
            chi_muc["bieu_do"] = {"tep": HG6.TEP_KQ, "dem": hg["dem"],
                                  "thieu_bat_buoc": (hg.get("kiem_danh_muc") or {}).get("thieu_bat_buoc", [])}
            md_hinh = HG6.md_bieu_do(hg)
            print(f"   biểu đồ: {hg['dem']['DA_VE']} hình · {hg['dem']['LOI']} lỗi → {HG6.THU_MUC}/")
        except Exception as e:  # noqa: BLE001 — biểu đồ lỗi không đổi kết quả thống kê
            chi_muc["bieu_do"] = {"loi": f"{type(e).__name__}: {str(e)[:300]}"}
            print(f"   ⚠ biểu đồ không sinh được: {chi_muc['bieu_do']['loi']}")
    (d / TEP_KQ_JSON).write_text(json.dumps(chi_muc, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    (d / TEP_KQ_MD).write_text(md_chi_muc(chi_muc, ve_forest_g6(chi_muc, d)) + md_hinh, encoding="utf-8",
                               newline="\n")
    dm = chi_muc["dem"]
    print(f"\n══ SAP G6 — {args.study}: {dm['DA_CHAY']} đã chạy · {dm['LOI']} lỗi · "
          f"{dm['CHUA_TU_DONG']} chờ làm tay"
          + (f" · bằng chứng thủ tục: {dm.get('DA_KIEM', 0)} đủ, {dm.get('THIEU_BANG_CHUNG', 0)} thiếu"
             if dm.get("DA_KIEM") or dm.get("THIEU_BANG_CHUNG") else "") + " ══")
    print(f"✓ {d / TEP_KQ_MD}\n{CAN_KIEM}")
    return ma


def _so(x, chu_so: int = 2) -> str:
    """Số theo quy ước văn bản tiếng Việt: dấu phẩy thập phân."""
    try:
        return f"{float(x):.{chu_so}f}".replace(".", ",")
    except (TypeError, ValueError):
        return "—"


def _p(x) -> str:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return ""
    return "p < 0,001" if v < 0.001 else f"p = {_so(v, 3)}"


def _ktc(ci) -> str:
    return f" (KTC 95% {_so(ci[0])}–{_so(ci[1])})" if isinstance(ci, (list, tuple)) and len(ci) == 2 else ""


#: (khoá trong uoc_luong, nhãn thước đo, khoá ước lượng, khoá KTC) — thứ tự ưu tiên khi một lượt có nhiều mô hình
_THUOC_DO_G6 = (("poisson_pr", "PR hiệu chỉnh", "PR_adj", "CI_95"),
                ("thu_tu", "OR chung hiệu chỉnh", "OR_adj", "CI_95"),
                ("da_bien", "OR hiệu chỉnh", "OR_adj", "CI_95"), ("hr_hieu_chinh", "HR hiệu chỉnh", "HR", "CI_95"),
                ("or_tho", "OR thô", "uoc_luong", "ci_95"))


def ty_so_g6(u: dict):
    """(nhãn, ước lượng, KTC) của tỷ số chính một lượt G6 — None khi lượt không có tỷ số (tỷ lệ, AUC…)."""
    for khoa, nhan, k_ul, k_ci in _THUOC_DO_G6:
        x = u.get(khoa) or {}
        if x.get(k_ul) is not None:
            return nhan, x.get(k_ul), x.get(k_ci)
        if khoa == "da_bien" and x.get("beta") is not None:
            return "β hiệu chỉnh", x.get("beta"), x.get("CI_95")
    return None


def dinh_dang_uoc_luong(u: dict) -> str:
    """Ước lượng chính của MỘT lượt viết theo chuẩn trình bày: thước đo, ước lượng (KTC 95%), p — thay chuỗi JSON thô
    (19/11/2026, bác sĩ: «tất cả vấn đề liên quan số liệu phân tích, kết quả phân tích» phải đúng chuẩn)."""
    if not u:
        return ""
    ts = ty_so_g6(u)
    if ts:
        nhan, ul, ci = ts
        x = next((u[k] for k, *_r in _THUOC_DO_G6 if k in u), {})
        return f"{nhan} {_so(ul)}{_ktc(ci)}" + (f"; {_p(x.get('p'))}" if _p(x.get("p")) else "")
    if u.get("md_tho"):
        x = u["md_tho"]
        return f"Hiệu số trung bình {_so(x.get('uoc_luong'))}" + (f"; {_p(x.get('p'))}" if _p(x.get("p")) else "")
    if u.get("ty_le"):
        x = u["ty_le"][0]
        ci = x.get("ci_95")
        return f"Tỷ lệ {_so(x.get('ty_le'), 1)}%" + (f" (KTC 95% {_so(ci[0], 1)}–{_so(ci[1], 1)})"
                                                     if isinstance(ci, (list, tuple)) and len(ci) == 2 else "") + \
            (f"; n = {x.get('n')}" if x.get("n") is not None else "")
    if u.get("chan_doan"):
        x = u["chan_doan"]
        return (f"AUC {_so(x.get('auc'))}{_ktc(x.get('ci_95'))}; độ nhạy {_so(x.get('do_nhay'))}; "
                f"độ đặc hiệu {_so(x.get('do_dac_hieu'))}")
    if u.get("du_bao"):
        x = u["du_bao"]
        return f"Thống kê C {_so(x.get('c_statistic'))}; điểm Brier {_so(x.get('brier'), 3)}"
    if u.get("gop"):
        x = u["gop"]
        return (f"RR gộp {_so(x.get('rr'))}{_ktc(x.get('ci_95'))}; I² {_so(x.get('i2'), 1)}%; "
                f"số nghiên cứu {x.get('k')}")
    if u.get("kinh_te"):
        x = u["kinh_te"]
        return f"ICER {_so(x.get('icer'), 0)}; chênh chi phí {_so(x.get('delta_c'), 0)}; chênh hiệu quả " \
               f"{_so(x.get('delta_e'), 3)}"
    if u.get("dinh_tinh"):
        x = u["dinh_tinh"]
        return f"{x.get('so_chu_de')} chủ đề từ {x.get('n')} bản ghi"
    loi = next((v.get("loi") for v in u.values() if isinstance(v, dict) and v.get("loi")), None)
    return f"lỗi mô hình: {loi}" if loi else ""


def ve_forest_g6(cm: dict, d: Path) -> str | None:
    """Forest plot các tỷ số (phân tích chính, nhóm nhỏ, độ nhạy) có KTC 95% — từ SỐ LIỆU THẬT của lượt chạy. Dưới 2
    tỷ số hoặc thiếu matplotlib ⇒ None (chỉ mục vẫn có bảng)."""
    hang = []
    for x in cm.get("phan_tich") or []:
        ts = ty_so_g6(x.get("uoc_luong") or {})
        if ts and isinstance(ts[2], (list, tuple)) and len(ts[2]) == 2 and ts[1] is not None:
            vai = {"chinh": "Phân tích chính", "phu": "Phân tích phụ", "nhom_con": "Nhóm nhỏ",
                   "do_nhay": "Độ nhạy"}.get(x.get("vai"), x.get("vai") or "")
            mo_ta = re.sub(r"\s+", " ", str(x.get("mo_ta") or "")).split(" — ")[-1].strip()[:42]
            hang.append((f"{vai}: {mo_ta}" if mo_ta and x.get("vai") != "chinh" else vai or x["id"], float(ts[1]),
                         float(ts[2][0]), float(ts[2][1]), ts[0]))
    if len(hang) < 2:
        return None
    try:
        import khung_bieu_bang as KBB  # noqa: PLC0415

        kh = KBB.Khung("bieu_do", "", dac_ta={"kieu": "forest", "nhan": [h[0] for h in hang], "ref": 1.0,
                                              "truc_x": f"{hang[0][4]} (KTC 95%)", "log": True})
        rel = f"{KBB.THU_MUC_HINH}/g6-uoc-luong.png"
        KBB.ve_hinh(kh, d / rel, du_lieu={"uoc_luong": [h[1] for h in hang], "duoi": [h[2] for h in hang],
                                          "tren": [h[3] for h in hang]})
        return rel
    except Exception:  # noqa: BLE001 — thiếu matplotlib: chỉ mục vẫn đầy đủ dạng bảng
        return None


def md_chi_muc(cm: dict, hinh: str | None = None) -> str:
    dong = [f"# Chỉ mục kết quả SAP G6 — {cm['study']}", "",
            f"Lúc {cm['luc']} · đặc tả `{cm['dac_ta']['tep']}` dấu `{cm['dac_ta']['dau']}` ({cm['dac_ta']['duyet']}) · "
            f"dữ liệu khoá SHA-256 `{cm['du_lieu_khoa']['sha256'][:16]}…` · kiểm chéo SPSS/R: "
            f"{'có' if cm['kiem_cheo'] else 'không'}", "",
            "| id | vai | SAP | trạng thái | gate | ước lượng chính | kiểm chéo |",
            "|---|---|---|---|---|---|---|"]  # fmt: skip
    for x in cm["phan_tich"]:
        u = x.get("uoc_luong") or {}
        chinh = dinh_dang_uoc_luong(u) or x.get("ly_do") or ""
        dong.append(f"| {x['id']} | {x['vai']} | {x.get('sap_muc') or ''} | {x['trang_thai']} | {x.get('gate', '—')} | "
                    f"{str(chinh)[:160].replace('|', '/')} | {x.get('kiem_cheo', '—')} |")  # fmt: skip
    dong += ["", "*Ghi chú:* PR: tỷ số tỷ lệ hiện mắc; OR: tỷ số chênh; HR: tỷ số nguy cơ tức thời; AUC: diện tích "
             "dưới đường cong ROC; KTC: khoảng tin cậy. p ghi ba chữ số thập phân, «p < 0,001» khi nhỏ hơn."]
    if hinh:
        dong += ["", f"![Biểu đồ ước lượng]({hinh})", "",
                 "**Biểu đồ. Ước lượng của phân tích chính, phân tích nhóm nhỏ và phân tích độ nhạy kèm KTC 95%**", "",
                 "*Ghi chú:* Điểm là ước lượng, đoạn ngang là KTC 95%; đường dọc tại 1 là không có liên quan; trục "
                 "hoành theo thang log."]
    cho = [x for x in cm["phan_tich"] if x["trang_thai"] == "CHUA_TU_DONG"]
    if cho:
        dong += ["", "## Chờ thống kê viên làm tay (hệ chưa có công cụ)", ""]
        dong += [f"- **{x['id']}** ({x.get('sap_muc')}): {x.get('mo_ta')} — {x.get('ly_do')}" for x in cho]
    dong += ["", "Bảng đầy đủ của từng phân tích: các tệp `<gate>_*.txt` và `<gate>_analysis_summary.json`.", "",
             CAN_KIEM]  # fmt: skip
    return "\n".join(dong) + "\n"


def lenh_ket_qua(args) -> int:
    d = thu_muc(args.study)
    cm = _doc_json(d / TEP_KQ_JSON)
    if not cm:
        raise KhongDoDuoc(f"chưa có {TEP_KQ_JSON} — chạy `chay_sap_g6.py chay --study {args.study}`")
    if args.json:
        print(json.dumps(cm, ensure_ascii=False, indent=1))
    else:
        print(md_chi_muc(cm))
    return 1 if cm.get("dem", {}).get("LOI") else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Chạy trọn SAP G6 theo đặc tả máy đọc. " + CAN_KIEM)
    sp = ap.add_subparsers(dest="lenh", required=True)
    k = sp.add_parser("kiem")
    k.add_argument("--study", required=True)
    k.add_argument("--json", action="store_true")
    c = sp.add_parser("chay")
    c.add_argument("--study", required=True)
    c.add_argument("--chi", default="")
    c.add_argument("--kiem-cheo", action="store_true")
    c.add_argument("--khong-ve", action="store_true", help="không tự sinh biểu đồ kết quả (hinh_g6)")
    q = sp.add_parser("ket-qua")
    q.add_argument("--study", required=True)
    q.add_argument("--json", action="store_true")
    dy = sp.add_parser("duyet", help="THỐNG KÊ VIÊN/PI ghi duyệt đặc tả (chạy khô mặc định)")
    dy.add_argument("--study", required=True)
    dy.add_argument("--vai", required=True, help="PI hoặc THONG_KE_VIEN")
    dy.add_argument("--tham-chieu", required=True, help="mã người duyệt, vd PI-BTM-01")
    dy.add_argument("--ap-dung", action="store_true")
    args = ap.parse_args(argv)
    try:
        return {"kiem": lenh_kiem, "chay": lenh_chay, "ket-qua": lenh_ket_qua, "duyet": lenh_duyet}[args.lenh](args)
    except KhongDoDuoc as e:
        print(f"⚪ Không đo được: {e}", file=sys.stderr)
        return 2
    except (TuChoi, BPS.TuChoi) as e:
        print(f"✗ Từ chối: {e}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    import moi_truong_venv as _MV  # bảo đảm Python đủ thư viện: thiếu ⇒ chạy lại bằng ~/.ebm-venv (18/11/2026)
    _MV.dam_bao_moi_truong(__file__)
    sys.exit(main())
