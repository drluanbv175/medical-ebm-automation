#!/usr/bin/env python3
"""Tự sinh BIỂU ĐỒ KẾT QUẢ G6 theo đặc tả SAP + dữ liệu ĐÃ KHOÁ (chặng 6b chương trình biểu đồ, bác sĩ 21/11/2026:
«tất cả vấn đề trong hệ thống nghiên cứu y khoa phải đạt sự toàn diện, tự động tốt nhất»).

Chạy TỰ ĐỘNG cuối `chay_sap_g6.py chay` (bỏ bằng `--khong-ve`) hoặc độc lập:
  python3 tools/hinh_g6.py --study <mã> [--ngon-ngu vi|en] [--json]

Mỗi phân tích của đặc tả `G6_DAC_TA_SAP.json` (trừ mục «chua_tu_dong») sinh hình đúng loại kết cục × phơi nhiễm, trên
CÙNG quần thể phân tích (dữ liệu khoá + biến phái sinh đã duyệt + bộ lọc `loc` — đúng hàm `_doc_df_khoa` mà phân tích
đặc thù dùng; bỏ ca thiếu theo từng hình):
  kết cục nhị phân × nhóm phân loại      → cột tỷ lệ + KTC 95%
  kết cục nhị phân × phơi nhiễm liên tục  → spline bậc ba giới hạn (logistic, hiệu chỉnh hiệp biến)
  kết cục thứ tự × phơi nhiễm liên tục    → xác suất dự báo logistic tỷ lệ chênh
  kết cục thứ tự × nhóm phân loại         → phân bố các mức theo nhóm (thanh phân kỳ)
  kết cục liên tục × nhóm phân loại       → hộp theo nhóm; × phơi nhiễm liên tục → spline tuyến tính
  kết cục liên tục (phân tích chính)      → bốn đồ thị chẩn đoán hồi quy tuyến tính
  thời gian + biến cố                     → Kaplan–Meier (+ log(−log S) cho phân tích chính có nhóm)
  tỷ lệ mô tả (ty_le)                     → cột tỷ lệ các chỉ số
  đặc thù: chẩn đoán → ROC + phân bố + Fagan · dự báo → hiệu chuẩn + ROC + DCA · gộp → forest (+ phễu khi ≥ 10, bỏ
  từng nghiên cứu) · kinh tế → mặt phẳng CE + CEAC (CÙNG các lần lặp bootstrap, cùng hạt giống của G6)
Thêm: forest ước lượng thô/hiệu chỉnh từ chỉ mục G6; kiểu dữ liệu thiếu của các biến phân tích chính; cuối cùng kiểm
thư mục theo danh mục thiết kế (`ve_bieu_do.kiem_thu_muc`) — hình bắt buộc còn thiếu (vd sơ đồ luồng cần số sàng
lọc thật) được LIỆT KÊ, không tự bịa.

Kết quả: `exports/<mã>/bieu-bang/g6-<id>-<loại>.png|pdf|json` + `G6_bieu_do.json`. Một hình lỗi KHÔNG làm hỏng các hình
khác và không đổi kết quả thống kê. Cần bác sĩ kiểm chứng.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

THU_MUC = "bieu-bang"
TEP_KQ = "G6_bieu_do.json"
MAX_NHOM = 8
CAN_KIEM = "Cần bác sĩ kiểm chứng."


def _ten_tep(pid: str, loai: str) -> str:
    return "g6-" + re.sub(r"[^A-Za-z0-9]+", "-", f"{pid}-{loai}").strip("-").lower()


def _nap_mac_dinh(study: str, can: Sequence[str], loc: Optional[str]):
    import phan_tich_thiet_ke_dac_thu as PT  # noqa: PLC0415

    df, _csv, _man = PT._doc_df_khoa(study, list(dict.fromkeys(c for c in can if c)), loc)
    return df


def loai_bien(s) -> str:
    """nhi_phan (chỉ 0/1) · phan_loai (≤ 8 giá trị, hoặc không phải số) · lien_tuc."""
    import pandas as pd  # noqa: PLC0415

    v = s.dropna()
    so = pd.to_numeric(v, errors="coerce")
    if so.isna().any():
        return "phan_loai"
    u = set(so.unique().tolist())
    if u <= {0, 1}:
        return "nhi_phan"
    if len(u) <= MAX_NHOM and all(float(x).is_integer() for x in u):
        return "phan_loai"
    return "lien_tuc"


def _ma_tran_kem(df, cov: Sequence[str], phan_loai: Sequence[str]):
    """Hiệp biến → ma trận số: biến phân loại (khai trong hiep_bien_phan_loai hoặc không phải số) mã hoá giả, bỏ mức
    đầu (tham chiếu); trả (ma trận hoặc None, tên cột)."""
    import numpy as np  # noqa: PLC0415
    import pandas as pd  # noqa: PLC0415

    cot, ten = [], []
    for c in cov:
        s = df[c]
        if c in phan_loai or pd.to_numeric(s, errors="coerce").isna().any():
            muc = sorted(s.astype(str).unique().tolist())
            for m in muc[1:]:
                cot.append((s.astype(str) == m).astype(float).to_numpy())
                ten.append(f"{c}={m}")
        else:
            cot.append(pd.to_numeric(s).astype(float).to_numpy())
            ten.append(c)
    return (np.column_stack(cot) if cot else None), ten


def _dong(df) -> List[Dict[str, str]]:
    return [{k: ("" if (v is None or (isinstance(v, float) and v != v)) else (str(int(v)) if isinstance(v, float) and
                                                                              v.is_integer() else str(v)))
             for k, v in r.items()} for r in df.to_dict("records")]


TIEN_TO_ROB = ("rob", "quadas")   # cột đánh giá nguy cơ sai lệch trong bộ dữ liệu trích xuất của tổng quan


def _nhan_tu_dien(d: Path, study: str) -> Dict[str, Dict[str, Any]]:
    """{trường: {"nhan": nhãn, "ma": {mã: nhãn}}} từ từ điển G5 của đề tài; không có/không đọc được ⇒ {}."""
    p = Path(d) / f"G5_REDCap_dictionary_{study}.csv"
    if not p.is_file():
        return {}
    try:
        import cau_noi_spss as CN  # noqa: PLC0415

        return {ten: {"nhan": td.get("nhan") or ten, "ma": CN.lua_chon(td)} for ten, td in CN.doc_tu_dien(p).items()}
    except Exception:  # noqa: BLE001 — từ điển hỏng: dùng giá trị thô (muc_rob nhận chữ «Thấp/Cao…» nếu có)
        return {}


def _hinh_rob(study: str, df_day, df, cot_ten: str, kq_f: Dict[str, Any], thu_muc: Path, them: Callable,
              ra: List[Dict[str, Any]], ngon_ngu: str) -> None:
    """Biểu đồ nguy cơ sai lệch (traffic light + thanh tổng hợp có trọng số = trọng số forest) khi bộ dữ liệu tổng
    quan có cột RoB (`rob*`, `quadas*`); mã → nhãn theo từ điển G5. Lỗi ⇒ một dòng LỖI riêng, không làm mất forest."""
    cot = [c for c in getattr(df_day, "columns", []) if str(c).lower().startswith(TIEN_TO_ROB)]
    if not cot:
        return
    import bieu_do_bao_cao as BB  # noqa: PLC0415

    try:
        td = _nhan_tu_dien(thu_muc.parent, study)
        w = {str(x.get("nghien_cuu")): x.get("trong_so_pt") for x in kq_f.get("nghien_cuu") or []}
        dong = []
        for i in df.index:
            ten_ncuu = str(df.loc[i, cot_ten])
            r: Dict[str, str] = {"nghien_cuu": ten_ncuu}
            for c in cot:
                v = df_day.loc[i, c]
                ma = str(int(v)) if isinstance(v, float) and v == v and v.is_integer() else str(v)
                r[(td.get(c) or {}).get("nhan") or c] = ((td.get(c) or {}).get("ma") or {}).get(ma, ma)
            if w.get(ten_ncuu) is not None:
                r["trong_so"] = str(w[ten_ncuu])
            dong.append(r)
        cong_cu = "QUADAS" if any(str(c).lower().startswith("quadas") for c in cot) else (
            "RoB 2" if any(str(c).lower().startswith("rob2") for c in cot) else "")
        BB.ve_rob(dong, them("rob", "Nguy cơ sai lệch theo nghiên cứu (trọng số như forest)"), cong_cu, ngon_ngu)
    except Exception as e:  # noqa: BLE001
        ra.pop()  # bỏ bản ghi «sẽ vẽ» vừa thêm, thay bằng dòng LỖI
        ra.append({"loai": "rob", "trang_thai": "LOI", "ly_do": f"{type(e).__name__}: {str(e)[:300]}"})


def hinh_cua_phan_tich(study: str, pt: Dict[str, Any], thu_muc: Path, nap: Callable,
                       ngon_ngu: str = "vi") -> List[Dict]:
    """Sinh mọi hình của MỘT phân tích; trả danh sách {tep, loai, mo_ta} (ném lỗi nếu không vẽ được)."""
    import numpy as np  # noqa: PLC0415

    ts = pt.get("tham_so") or {}
    pid, vai = pt["id"], pt.get("vai")
    loc = ts.get("loc")
    ra: List[Dict[str, Any]] = []

    def _them(loai: str, mo_ta: str):
        ra.append({"tep": f"{THU_MUC}/{_ten_tep(pid, loai)}.png", "loai": loai, "mo_ta": mo_ta})
        return thu_muc / _ten_tep(pid, loai)

    dac_thu = ts.get("loai_dac_thu")
    if dac_thu:
        import phan_tich_thiet_ke_dac_thu as PT  # noqa: PLC0415

        if dac_thu == "chan_doan":
            import bieu_do_chan_doan as CD  # noqa: PLC0415

            y_ten, x_ten, ng = ts["tham_chieu"], ts["chi_so"], float(ts["nguong"])
            df = nap(study, [y_ten, x_ten], loc)[[y_ten, x_ten]].dropna()
            y, x = df[y_ten].astype(int).to_numpy(), df[x_ten].astype(float).to_numpy()
            CD.ve_roc(y, {x_ten: x}, _them("roc", f"ROC của {x_ten}"), ngon_ngu=ngon_ngu)
            CD.ve_phan_bo(y, x, x_ten, _them("phan-bo", f"Phân bố {x_ten} theo tình trạng bệnh"), ng, ngon_ngu)
            tp = int(((y == 1) & (x >= ng)).sum())
            fn = int(((y == 1) & (x < ng)).sum())
            fp = int(((y == 0) & (x >= ng)).sum())
            tn = int(((y == 0) & (x < ng)).sum())
            se, sp = tp / max(tp + fn, 1), tn / max(tn + fp, 1)
            if 0 < se < 1 and 0 < sp < 1:
                CD.ve_fagan(float(y.mean()), se / (1 - sp), (1 - se) / sp, _them("fagan", "Toán đồ Fagan"),
                            ngon_ngu)
        elif dac_thu == "du_bao":
            import bieu_do_chan_doan as CD  # noqa: PLC0415

            yt, cov = ts["outcome"], list(ts.get("covariates") or [])
            df = nap(study, [yt, *cov], loc)[[yt, *cov]].dropna()
            y = df[yt].astype(int).to_numpy()
            X = np.column_stack([np.ones(len(y)), df[cov].astype(float).to_numpy()])
            b, _ = CD._hoi_quy_logistic(X, y)
            p = 1 / (1 + np.exp(-(X @ b)))
            CD.ve_hieu_chuan(y, p, _them("hieu-chuan", "Đường hiệu chuẩn"), "", 10, ngon_ngu)
            CD.ve_roc(y, {"Mô hình" if ngon_ngu == "vi" else "Model": p}, _them("roc", "ROC mô hình"),
                      danh_dau_youden=False, ngon_ngu=ngon_ngu)
            hi = min(0.99, max(0.05, round(float(np.quantile(p, 0.95)), 2)))
            CD.ve_dca(y, {"Mô hình" if ngon_ngu == "vi" else "Model": p},
                      [round(0.01 * i, 2) for i in range(1, int(hi * 100) + 1)], _them("dca", "Đường cong quyết định"),
                      ngon_ngu)
        elif dac_thu == "gop":
            import bieu_do_gop as GP  # noqa: PLC0415

            cot = [ts[k] for k in ("nhan_nghien_cuu", "su_kien_can_thiep", "n_can_thiep", "su_kien_chung", "n_chung")]
            pn = ts.get("phan_nhom")  # 22/11/2026: phân nhóm tiền định SAP §7 — cùng quần thể (bỏ ca thiếu) như G6
            df = nap(study, cot + ([pn] if pn else []), loc)[cot + ([pn] if pn else [])].dropna()
            ma_nhan = ((_nhan_tu_dien(thu_muc.parent, study).get(pn) or {}).get("ma") or {}) if pn else {}
            ds = []
            for r in df.to_dict("records"):  # ĐÚNG đầu vào từng nghiên cứu của G6 (_o_rr)
                yi, vi = PT._o_rr(float(r[cot[1]]), float(r[cot[2]]), float(r[cot[3]]), float(r[cot[4]]))
                nhom = ma_nhan.get(PT._ma_nhom(r[pn]), PT._ma_nhom(r[pn])) if pn else ""
                ds.append({"nghien_cuu": str(r[cot[0]]), "nhom": nhom, "yi": yi, "vi": vi, "sei": vi ** 0.5,
                           "su_kien_1": int(r[cot[1]]), "tong_1": int(r[cot[2]]), "su_kien_2": int(r[cot[3]]),
                           "tong_2": int(r[cot[4]])})
            if pn:  # forest theo phân nhóm (kim cương từng nhóm + Q giữa nhóm như G6); phễu, bỏ từng nghiên cứu: xem
                # phân tích chính — không vẽ lại trùng lặp. Thứ tự phân nhóm theo mã, như bảng §3b của G7
                ma_cua = {PT._ma_nhom(r[pn]): None for r in df.to_dict("records")}
                thu_tu = {ma_nhan.get(m, m): i for i, m in enumerate(sorted(ma_cua, key=PT.khoa_ma_nhom))}
                ds.sort(key=lambda e: thu_tu.get(e["nhom"], len(thu_tu)))
                GP.ve_forest(ds, "RR", _them("forest-phan-nhom", f"Forest plot phân nhóm theo {pn} (DL, như G6)"),
                             "DL", ngon_ngu=ngon_ngu)
                return ra
            kq_f = GP.ve_forest(ds, "RR", _them("forest", "Forest plot gộp (DL, như G6)"), "DL", ngon_ngu=ngon_ngu)
            _hinh_rob(study, nap(study, cot, loc), df, cot[0], kq_f, thu_muc, _them, ra, ngon_ngu)
            if len(ds) >= 3:
                GP.ve_bo_tung_nc(ds, "RR", _them("bo-tung-nc", "Bỏ từng nghiên cứu"), "DL", ngon_ngu)
            if len(ds) >= PT.EGGER_K_TOI_THIEU:  # cùng ngưỡng kiểm định Egger của G6 (SAP §5)
                GP.ve_pheu(ds, "RR", _them("pheu", "Funnel plot"), "DL", True, True, ngon_ngu)
        elif dac_thu == "dinh_tinh":
            import bieu_do_bao_cao as BB  # noqa: PLC0415

            cot = ts["chu_de"]
            df = nap(study, [cot], loc)
            BB.ve_chu_de(_dong(df[[cot]]), cot, _them("chu-de", f"Tần suất chủ đề ({cot}) — mô tả, không thay phân "
                                                                "tích chủ đề"), ngon_ngu)
        elif dac_thu == "kinh_te":
            import bieu_do_bao_cao as BB  # noqa: PLC0415

            cot = [ts["nhom"], ts["chi_phi"], ts["hieu_qua"]]
            df = nap(study, cot, loc)[cot].dropna()
            kt = PT.kinh_te(df.to_dict("records"), *cot, float(ts["nguong_wtp"]), tra_lap=True)
            dc, de = [x[0] for x in kt["lap"]], [x[1] for x in kt["lap"]]
            BB.ve_ce_plane(dc, de, _them("ce-plane", "Mặt phẳng chi phí – hiệu quả (bootstrap như G6)"),
                           float(ts["nguong_wtp"]), ngon_ngu=ngon_ngu)
            BB.ve_ceac(dc, de, _them("ceac", "CEAC"), 3 * max(float(ts["nguong_wtp"]), 1.0), ngon_ngu=ngon_ngu)
        return ra

    if ts.get("time") and ts.get("event"):
        import bieu_do_song_con as SC  # noqa: PLC0415

        g = ts.get("group")
        cot = [ts["time"], ts["event"], *([g] if g else [])]
        df = nap(study, cot, loc)[cot].dropna()
        nhom = df[g].astype(str).to_numpy(dtype=object) if g and loai_bien(df[g]) != "lien_tuc" else \
            np.array([""] * len(df), dtype=object)
        t, e = df[ts["time"]].astype(float).to_numpy(), df[ts["event"]].astype(int).to_numpy()
        SC.ve_km(t, e, nhom, _them("km", "Kaplan–Meier"), ngon_ngu=ngon_ngu)
        if vai == "chinh" and len(set(nhom.tolist())) > 1:
            SC.ve_loglog(t, e, nhom, _them("loglog", "log(−log S) — giả định nguy cơ tỷ lệ"), ngon_ngu=ngon_ngu)
        return ra

    if ts.get("ty_le") and not ts.get("outcome"):
        import bieu_do_mo_ta as MT  # noqa: PLC0415

        cot = list(ts["ty_le"])
        df = nap(study, cot, loc)
        dai = [{"chi_so": c, "gia_tri": str(int(v))} for c in cot if loai_bien(df[c]) == "nhi_phan"
               for v in df[c].dropna().tolist()]
        if dai:
            MT.ve_cot_ktc(dai, "gia_tri", _them("cot-ktc", "Tỷ lệ các chỉ số"), muc="1", cot_nhom="chi_so",
                          ngon_ngu=ngon_ngu, nhan_bien="Tỷ lệ" if ngon_ngu == "vi" else "Proportion")
        return ra

    yt, g = ts.get("outcome"), ts.get("group")
    if not (yt and g):
        return ra
    cov = list(ts.get("covariates") or [])
    df = nap(study, [yt, g, *cov], loc)[[yt, g, *cov]].dropna()
    kieu = ts.get("outcome_type") or "auto"
    ly = {"binary": "nhi_phan", "poisson_pr": "nhi_phan", "ordinal": "thu_tu", "continuous": "lien_tuc"}.get(kieu) \
        or ("nhi_phan" if loai_bien(df[yt]) == "nhi_phan" else "lien_tuc")
    lg = loai_bien(df[g])
    kem, ten_kem = _ma_tran_kem(df, cov, ts.get("hiep_bien_phan_loai") or [])
    if ly == "nhi_phan" and lg != "lien_tuc":
        import bieu_do_mo_ta as MT  # noqa: PLC0415

        MT.ve_cot_ktc(_dong(df), yt, _them("cot-ktc", f"Tỷ lệ {yt} theo {g}"), muc="1", cot_nhom=g,
                      ngon_ngu=ngon_ngu)
    elif ly in ("nhi_phan", "lien_tuc") and lg == "lien_tuc":
        import bieu_do_hoi_quy as HQ  # noqa: PLC0415

        y = df[yt].astype(float).to_numpy()
        HQ.ve_spline(df[g].astype(float).to_numpy(), y if ly == "lien_tuc" else y.astype(int),
                     _them("spline", f"Đáp ứng liều {g} → {yt}"), g, kem, 4 if len(df) >= 100 else 3, None,
                     ly == "lien_tuc", ngon_ngu, ten_kem=ten_kem)
    elif ly == "thu_tu" and lg == "lien_tuc":
        import bieu_do_hoi_quy as HQ  # noqa: PLC0415

        HQ.ve_xac_suat_thu_tu([str(v) for v in df[yt].tolist()], df[g].astype(float).to_numpy(),
                              _them("xac-suat-thu-tu", f"Xác suất các mức {yt} theo {g}"), g, kem, None, ten_kem,
                              ngon_ngu)
    elif ly == "thu_tu":
        import bieu_do_mo_ta as MT  # noqa: PLC0415

        muc = sorted({str(v) for v in df[yt].tolist()}, key=lambda v: float(v) if v.replace(".", "", 1).isdigit()
                     else v)
        dong = [{f"{g} = {k}": (str(r[yt]) if str(r[g]) == k else "") for k in sorted({str(x) for x in df[g]})}
                for r in _dong(df)]
        MT.ve_likert(dong, list(dong[0]), [(m, m) for m in muc], _them("likert", f"Phân bố {yt} theo {g}"),
                     giu_thu_tu=True, ngon_ngu=ngon_ngu)
    elif ly == "lien_tuc":
        import bieu_do_mo_ta as MT  # noqa: PLC0415

        MT.ve_phan_bo(_dong(df), yt, _them("phan-bo", f"Phân bố {yt} theo {g}"), g, "hop", ngon_ngu)
    if ly == "lien_tuc" and vai == "chinh":
        import bieu_do_hoi_quy as HQ  # noqa: PLC0415

        Xg, _ = _ma_tran_kem(df, [g], [g] if lg != "lien_tuc" else [])
        X = Xg if kem is None else np.column_stack([Xg, kem])
        HQ.ve_chan_doan_lm(X, df[yt].astype(float).to_numpy(), _them("chan-doan-lm", "Chẩn đoán hồi quy tuyến tính"),
                           ngon_ngu)
    return ra


def _bang_tho_hieu_chinh(chi_muc: Dict[str, Any]) -> Dict[str, List[Dict[str, str]]]:
    """Bảng ước lượng từ chỉ mục G6 (đúng số G6 đã ghi), TÁCH theo thước đo — OR (thô + hiệu chỉnh logistic/thứ tự),
    PR (Poisson), HR (Cox) và β (hồi quy tuyến tính, trục cộng) không bao giờ chung một trục."""
    dong: Dict[str, List[Dict[str, str]]] = {"OR": [], "PR": [], "HR": [], "β": []}

    def _them(do: str, ten: str, vai: str, v: Any, ci: Any, p: Any, mo_hinh: str) -> None:
        if v is not None and isinstance(ci, (list, tuple)) and len(ci) == 2 and None not in ci:
            dong[do].append({"bien": ten, "muc": vai, "uoc_luong": str(v), "duoi": str(ci[0]), "tren": str(ci[1]),
                             "p": "" if p is None else str(p), "mo_hinh": mo_hinh})

    for x in (chi_muc or {}).get("phan_tich") or []:
        u = x.get("uoc_luong") or {}
        tho = u.get("or_tho") or {}
        hc = next((u[k] for k in ("da_bien", "thu_tu", "poisson_pr") if isinstance(u.get(k), dict)
                   and not u[k].get("loi")), {})
        ten = (x.get("mo_ta") or x["id"])[:48]
        ci_t = tho.get("ci_95") or []
        if tho.get("uoc_luong") is not None and len(ci_t) == 2:
            dong["OR"].append({"bien": ten, "muc": x.get("vai") or "", "uoc_luong": str(tho["uoc_luong"]),
                               "duoi": str(ci_t[0]),
                         "tren": str(ci_t[1]), "p": "" if tho.get("p") is None else str(tho["p"]), "mo_hinh": "Thô"})
        if hc.get("PR_adj") is not None:
            _them("PR", ten, x.get("vai") or "", hc["PR_adj"], hc.get("CI_95"), hc.get("p"), "Hiệu chỉnh")
        elif (hc.get("OR_adj") or hc.get("OR")) is not None:
            _them("OR", ten, x.get("vai") or "", hc.get("OR_adj") or hc.get("OR"), hc.get("CI_95"), hc.get("p"),
                  "Hiệu chỉnh")
        elif hc.get("beta") is not None:
            _them("β", ten, x.get("vai") or "", hc["beta"], hc.get("CI_95"), hc.get("p"), "Hiệu chỉnh")
        hr = u.get("hr_hieu_chinh") or {}
        if isinstance(hr, dict) and not hr.get("loi"):
            _them("HR", ten, x.get("vai") or "", hr.get("HR"), hr.get("CI_95"), hr.get("p"), "Hiệu chỉnh (Cox)")
    return dong


TEP_LUONG = "SO_DO_LUONG_{study}.csv"   # số THẬT từ sổ sàng lọc — nghiên cứu viên điền, máy không bao giờ điền


def _n_phan_tich_chinh(chi_muc: Optional[Dict[str, Any]]) -> Optional[int]:
    for x in (chi_muc or {}).get("phan_tich") or []:
        if x.get("vai") == "chinh" and isinstance((x.get("uoc_luong") or {}).get("n_total"), int):
            return int(x["uoc_luong"]["n_total"])
    return None


def _n_cuoi_luong(nhanh: Dict[str, List[Dict[str, Any]]]) -> int:
    """n đưa vào phân tích = hộp chính CUỐI của từng nhánh có tên (CONSORT/case–control); không nhánh ⇒ trục chung."""
    co_ten = {k: v for k, v in nhanh.items() if k}
    ds = co_ten or nhanh
    return sum(next((b["n"] for b in reversed(v) if b["loai"] == "chinh"), 0) for v in ds.values())


def _so_do_luong(study: str, d: Path, thu_muc: Path, chi_muc: Optional[Dict[str, Any]], tk: str,
                 ket: List[Dict[str, Any]], ngon_ngu: str) -> None:
    """Sơ đồ luồng từ `SO_DO_LUONG_<mã>.csv` (21/11/2026). Chưa có ⇒ tạo MẪU đúng chuẩn của thiết kế (cột n trống) và
    ghi CHUA_DU_SO; còn ô trống ⇒ CHUA_DU_SO; đủ số ⇒ kiểm số học + đối chiếu n hộp cuối với n phân tích chính của
    G6 TRƯỚC khi vẽ — lệch ⇒ LỖI (không vẽ hình nói khác số đã phân tích)."""
    import bieu_do_bao_cao as BB  # noqa: PLC0415
    import bieu_do_mo_ta as MT  # noqa: PLC0415
    import ve_bieu_do as VB  # noqa: PLC0415

    p = Path(d) / TEP_LUONG.format(study=study)
    goc = {"id": "G5", "loai": "so-do-luong"}
    if not p.is_file():
        if tk in VB.MAU_SO_DO_LUONG:
            # 22/11/2026: mẫu theo đúng cách thu thập đã chốt — hồ sơ có sẵn (miễn đồng thuận) không có bước mời/từ chối
            try:
                meta = json.loads((Path(d) / "study_meta.json").read_text(encoding="utf-8"))
            except (OSError, ValueError):
                meta = {}
            hoi_cuu = VB.la_hoi_cuu(meta if isinstance(meta, dict) else {})
            VB.ghi_mau_so_do_luong(tk, p, hoi_cuu)
            ket.append({**goc, "trang_thai": "CHUA_DU_SO", "ly_do": f"đã tạo mẫu {p.name} theo chuẩn"
                        + (" (hồ sơ có sẵn: khung mẫu → tiêu chuẩn lựa chọn → loại trừ → phân tích)" if hoi_cuu else "")
                        + " — điền cột n bằng số THẬT từ sổ sàng lọc rồi chạy lại G6"})
        return
    try:
        dong = MT.doc_csv(p)
        trong = [r["buoc"] for r in dong if not str(r.get("n", "")).strip()]
        if trong:
            ket.append({**goc, "trang_thai": "CHUA_DU_SO", "ly_do": f"{p.name}: {len(trong)} hộp chưa có số ("
                                                                    f"{', '.join(trong[:3])}…)"})
            return
        k = BB.kiem_so_hoc_luong(dong)
        if k["loi"]:
            raise BB.LoiBieuDo("số học không khớp — " + " | ".join(k["loi"]))
        n_g6, n_luong = _n_phan_tich_chinh(chi_muc), _n_cuoi_luong(k["nhanh"])
        if n_g6 is not None and n_luong != n_g6:
            raise BB.LoiBieuDo(f"hộp «đưa vào phân tích» = {n_luong} nhưng phân tích chính G6 dùng N = {n_g6}")
        BB.ve_so_do_luong(dong, thu_muc / "g6-so-do-luong", (VB.DANH_MUC.get(tk) or {}).get("chuan", ""), ngon_ngu)
        ket.append({**goc, "tep": f"{THU_MUC}/g6-so-do-luong.png", "trang_thai": "DA_VE",
                    "mo_ta": "Sơ đồ luồng người tham gia/nghiên cứu (số từ sổ sàng lọc, đã kiểm số học)"})
    except Exception as e:  # noqa: BLE001
        ket.append({**goc, "trang_thai": "LOI", "ly_do": f"{p.name}: {type(e).__name__}: {str(e)[:300]}"})


def sinh(study: str, d: Path, phan_tich: Sequence[Dict[str, Any]], chi_muc: Optional[Dict[str, Any]] = None,
         thiet_ke: Optional[str] = None, nap: Optional[Callable] = None, ngon_ngu: str = "vi") -> Dict[str, Any]:
    import bieu_do_mo_ta as MT  # noqa: PLC0415
    import ve_bieu_do as VB  # noqa: PLC0415

    nap = nap or _nap_mac_dinh
    thu_muc = Path(d) / THU_MUC
    thu_muc.mkdir(parents=True, exist_ok=True)
    ket: List[Dict[str, Any]] = []
    for pt in phan_tich:
        if pt.get("chua_tu_dong"):
            continue
        try:
            for h in hinh_cua_phan_tich(study, pt, thu_muc, nap, ngon_ngu):
                if pt.get("mo_ta") and h.get("mo_ta"):  # chú thích nói rõ hình thuộc phân tích SAP nào
                    h = {**h, "mo_ta": f"{pt['mo_ta']} — {h['mo_ta']}"}
                ket.append({"id": pt["id"], "vai": pt.get("vai"), "trang_thai": "DA_VE", **h})
        except Exception as e:  # noqa: BLE001 — một hình lỗi không làm hỏng các hình khác
            ket.append({"id": pt["id"], "vai": pt.get("vai"), "trang_thai": "LOI",
                        "ly_do": f"{type(e).__name__}: {str(e)[:300]}"})
    for do, bang in _bang_tho_hieu_chinh(chi_muc or {}).items():
        if not bang:
            continue
        ten = "g6-tho-hieu-chinh" + {"OR": "", "PR": "-pr", "HR": "-hr", "β": "-beta"}[do]
        try:
            import bieu_do_hoi_quy as HQ  # noqa: PLC0415

            HQ.ve_forest_uoc_luong(bang, do, thu_muc / ten, ngon_ngu)
            ket.append({"id": "G6", "loai": "forest-uoc-luong", "tep": f"{THU_MUC}/{ten}.png", "trang_thai": "DA_VE",
                        "mo_ta": f"Ước lượng {do} của các phân tích SAP (thô/hiệu chỉnh)"})
        except Exception as e:  # noqa: BLE001
            ket.append({"id": "G6", "loai": "forest-uoc-luong", "trang_thai": "LOI", "ly_do": str(e)[:300]})
    chinh = next((p for p in phan_tich if p.get("vai") == "chinh" and not p.get("chua_tu_dong")), None)
    if chinh:
        ts = chinh.get("tham_so") or {}
        can = [ts.get(k) for k in ("outcome", "group", "time", "event")] + list(ts.get("covariates") or []) + \
            list(ts.get("ty_le") or []) + list(ts.get("vars") or [])
        can = [c for c in can if c]
        if len(can) >= 2:
            try:
                df = nap(study, can, None)
                MT.ve_thieu(_dong(df[can]), thu_muc / "g6-du-lieu-thieu", can, ngon_ngu)
                ket.append({"id": chinh["id"], "loai": "thieu", "tep": f"{THU_MUC}/g6-du-lieu-thieu.png",
                            "mo_ta": "Kiểu dữ liệu thiếu của các biến phân tích chính", "trang_thai": "DA_VE"})
            except Exception as e:  # noqa: BLE001
                ket.append({"id": chinh["id"], "loai": "thieu", "trang_thai": "LOI", "ly_do": str(e)[:300]})
    tk = VB.BI_DANH.get(thiet_ke or "", thiet_ke or "")
    _so_do_luong(study, Path(d), thu_muc, chi_muc, tk, ket, ngon_ngu)
    kiem = VB.kiem_thu_muc(thu_muc, tk, ngon_ngu) if tk in VB.DANH_MUC else {
        "thiet_ke": thiet_ke, "ghi_chu": "thiết kế chưa có trong danh mục hình — bỏ qua kiểm"}
    kq = {"study": study, "ngon_ngu": ngon_ngu, "hinh": ket,
          "dem": {"DA_VE": sum(1 for x in ket if x["trang_thai"] == "DA_VE"),
                  "LOI": sum(1 for x in ket if x["trang_thai"] == "LOI")},
          "kiem_danh_muc": kiem, "disclaimer": CAN_KIEM}
    tam = Path(d) / (TEP_KQ + ".tam")
    tam.write_text(json.dumps(kq, ensure_ascii=False, indent=1, default=str) + "\n", encoding="utf-8", newline="\n")
    tam.replace(Path(d) / TEP_KQ)
    return kq


def md_bieu_do(kq: Dict[str, Any]) -> str:
    """Mục «Biểu đồ kết quả» cho chỉ mục G6 (markdown)."""
    import ve_bieu_do as VB  # noqa: PLC0415

    dong = ["", "## Biểu đồ kết quả (tự sinh)", "",
            f"{kq['dem']['DA_VE']} hình đã vẽ · {kq['dem']['LOI']} lỗi. Mỗi hình kèm PDF vector và JSON số liệu.", "",
            "| phân tích | loại | tệp | ghi chú |", "|---|---|---|---|"]
    for h in kq["hinh"]:
        dong.append(f"| {h['id']} | {h.get('loai', '')} | {h.get('tep', '')} | "
                    f"{h.get('mo_ta', '') if h['trang_thai'] == 'DA_VE' else 'LỖI: ' + h.get('ly_do', '')[:120]} |")
    k = kq.get("kiem_danh_muc") or {}
    if k.get("thieu_bat_buoc"):
        dong += ["", "Hình BẮT BUỘC theo chuẩn báo cáo còn thiếu (cần số liệu ngoài dữ liệu phân tích, "
                     "vd số sàng lọc):"]
        for x in k["thieu_bat_buoc"]:
            cc, lenh, mo_ta = VB.HINH[x]
            dong.append(f"- {mo_ta}: `python3 tools/{cc} {lenh} --du-lieu … --ra exports/<mã>/{THU_MUC}/…`")
    return "\n".join(dong) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--study", required=True)
    ap.add_argument("--ngon-ngu", default="vi", choices=("vi", "en"))
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    import chay_sap_g6 as CS  # noqa: PLC0415

    d = CS.thu_muc(a.study)
    dt = CS.doc_dac_ta(d)
    chi_muc = CS._doc_json(d / CS.TEP_KQ_JSON)
    meta = CS._doc_json(d / "study_meta.json")
    g1 = (meta.get("gate_params") or {}).get("G1") or {}
    kq = sinh(a.study, d, dt.get("phan_tich") or [], chi_muc, str(g1.get("design") or meta.get("design_code") or ""),
              ngon_ngu=a.ngon_ngu)
    if a.json:
        print(json.dumps(kq, ensure_ascii=False, indent=1, default=str))
    else:
        print(md_bieu_do(kq))
        print(CAN_KIEM)
    return 0 if kq["dem"]["LOI"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
