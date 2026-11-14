"""Trình chạy NỀN của IBM SPSS Statistics — do Python ĐI KÈM SPSS thực thi (external mode), KHÔNG phải ~/.ebm-venv.

Chỉ `tools/cau_noi_spss.py` gọi tệp này (subprocess, `-I`), nên nó cố ý KHÔNG import gì của repo: Python của SPSS là
một môi trường riêng (SPSS 31: Python 3.13 x86_64). Mọi lệnh đều tắt SPSS êm (`spss.StopSPSS()`), kể cả khi lỗi.

Ba chế độ (đúng một):
  --cu-phap <tệp.sps>            INSERT FILE … ERROR=STOP; in «SO_CA=<n>» của bộ dữ liệu đang mở cuối cùng.
  --kiem <ra.xml>                SHOW LICENSE ghi qua OMS (OXML) — mô-đun nào được cấp phép; in «PHIEN_BAN=<x>».
  --tu-dien <tệp.sav> <ra.json>  từ điển biến của một tệp .sav (tên · nhãn · mức đo · định dạng · nhãn giá trị ·
                                 mã thiếu).

Mã thoát: 0 xong · 1 SPSS báo lỗi (thông điệp ở stderr, dòng «LOI_SPSS») · 2 tham số sai.
"""

import json
import sys


def _chuoi(s):
    return "'" + str(s).replace("'", "''") + "'"


def _phien_ban(spss):
    for ten in ("__GetSpssDxVersion", "GetDefaultPlugInVersion"):
        ham = getattr(spss, ten, None)
        if callable(ham):
            try:
                return str(ham())
            except Exception:  # noqa: BLE001 — chỉ để in thông tin, không quyết định gì
                continue
    return "?"


def _so_ca(spss):
    try:
        return int(spss.GetCaseCount())
    except Exception:  # noqa: BLE001 — chưa có bộ dữ liệu nào đang mở
        return -1


def main(argv):
    if len(argv) < 2 or argv[0] not in ("--cu-phap", "--kiem", "--tu-dien"):
        print(
            "dùng: spss_chay_nen.py --cu-phap <tệp.sps> | --kiem <ra.xml> | --tu-dien <tệp.sav> <ra.json>",
            file=sys.stderr,
        )
        return 2
    import spss  # chỉ có trong Python đi kèm SPSS

    try:
        print("PHIEN_BAN=" + _phien_ban(spss))
        if argv[0] == "--cu-phap":
            spss.Submit("INSERT FILE=" + _chuoi(argv[1]) + " ERROR=STOP.")
            print("SO_CA=" + str(_so_ca(spss)))
        elif argv[0] == "--kiem":
            spss.Submit(
                [
                    "OMS /SELECT TABLES /IF COMMANDS=['Show'] /DESTINATION FORMAT=OXML OUTFILE="
                    + _chuoi(argv[1])
                    + " /TAG='ebm_kiem'.",
                    "SHOW LICENSE.",
                    "OMSEND TAG='ebm_kiem'.",
                ]
            )
        else:
            if len(argv) < 3:
                print("thiếu tệp ra .json", file=sys.stderr)
                return 2
            spss.Submit("GET FILE=" + _chuoi(argv[1]) + ".")
            bien = []
            spss.StartDataStep()
            try:
                ds = spss.Dataset()
                for v in ds.varlist:
                    bien.append(
                        {
                            "ten": v.name,
                            "nhan": v.label or "",
                            "muc_do": v.measurementLevel,
                            "kieu": v.type,
                            "dinh_dang": v.format,
                            "nhan_gia_tri": {str(k): val for k, val in v.valueLabels.data.items()},
                            "thieu": list(v.missingValues),
                        }
                    )
            finally:
                spss.EndDataStep()
            with open(argv[2], "w", encoding="utf-8") as f:
                json.dump({"so_ca": _so_ca(spss), "bien": bien}, f, ensure_ascii=False, indent=1)
            print("SO_CA=" + str(_so_ca(spss)))
    except spss.SpssError as e:  # lỗi cú pháp/dữ liệu trong SPSS
        print("LOI_SPSS " + str(e), file=sys.stderr)
        spss.StopSPSS()
        return 1
    spss.StopSPSS()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
