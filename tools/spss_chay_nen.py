"""Trình chạy NỀN của IBM SPSS Statistics — do Python ĐI KÈM SPSS thực thi (external mode), KHÔNG phải ~/.ebm-venv.

Chỉ `tools/cau_noi_spss.py` gọi tệp này (subprocess, `-I`), nên nó cố ý KHÔNG import gì của repo: Python của SPSS là
một môi trường riêng (SPSS 31: Python 3.13 x86_64). Mọi lệnh đều tắt SPSS êm (`spss.StopSPSS()`), kể cả khi lỗi.

Bốn chế độ (đúng một):
  --cu-phap <tệp.sps>            INSERT FILE … ERROR=STOP; in «SO_CA=<n>» của bộ dữ liệu đang mở cuối cùng.
  --kiem <ra.xml>                SHOW LICENSE ghi qua OMS (OXML) — mô-đun nào được cấp phép; in «PHIEN_BAN=<x>».
  --tu-dien <tệp.sav> <ra.json>  từ điển biến của một tệp .sav (tên · nhãn · mức đo · định dạng · nhãn giá trị ·
                                 mã thiếu).
  --du-lieu <tệp.sav> <ra.json> [<tu_dien.json>]
                                 MỌI ca của tệp .sav, giá trị THÔ (spss.Cursor — KHÔNG qua định dạng hiển thị như
                                 SAVE TRANSLATE /TYPE=CSV, vốn làm tròn): số là double đủ chữ số (JSON ghi bằng repr nên
                                 đọc lại đúng từng bit), SYSMIS ⇒ null, mã thiếu do người dùng định nghĩa giữ NGUYÊN giá
                                 trị, chuỗi bỏ dấu cách đệm bên phải. Có <tu_dien.json> ⇒ ghi luôn từ điển như --tu-dien
                                 trong CÙNG phiên SPSS (đỡ một lần khởi động ~8 giây). Dùng cho phép khứ hồi từng ô của
                                 `cau_noi_spss.py xuat-sav`.

Mã thoát: 0 xong · 1 SPSS báo lỗi (thông điệp ở stderr, dòng «LOI_SPSS») · 2 tham số sai.
"""

import json
import math
import sys

for _s in (sys.stdout, sys.stderr):  # `-I` bỏ qua PYTHONIOENCODING — Windows cp1252 làm vỡ thông điệp tiếng Việt (§0.9)
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


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


def _thieu(mv):
    """missingValues của SPSS ⇒ JSON được: cận vô hạn của khoảng (LO/HI ≈ ±1,8e308) ghi thành chuỗi «LO»/«HI»."""
    ra = []
    for x in mv:
        if isinstance(x, float) and (not math.isfinite(x) or abs(x) >= 1e300):
            ra.append("LO" if x < 0 else "HI")
        else:
            ra.append(x)
    return ra


def _tu_dien(spss):
    """Từ điển biến của bộ dữ liệu đang mở (đọc trong một DataStep)."""
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
                    "thieu": _thieu(v.missingValues),
                }
            )
    finally:
        spss.EndDataStep()
    return bien


def gia_tri_tho(x):
    """Một ô từ spss.Cursor ⇒ giá trị JSON: số giữ nguyên (float, không làm tròn), SYSMIS/None ⇒ None, chuỗi bỏ dấu
    cách ĐỆM bên phải (SPSS đệm chuỗi tới độ rộng biến; dấu cách cuối không có nghĩa trong SPSS), byte ⇒ giải mã UTF-8
    thay ký tự hỏng bằng U+FFFD (để phép so phát hiện hỏng mã hoá thay vì sập)."""
    if x is None:
        return None
    if isinstance(x, (bytes, bytearray)):
        x = bytes(x).decode("utf-8", errors="replace")
    if isinstance(x, str):
        return x.rstrip(" ")
    x = float(x)
    return x if math.isfinite(x) else None


def _du_lieu(spss, ra):
    """Ghi MỌI ca của bộ dữ liệu đang mở ra JSON: {"bien": [...], "kieu": [...], "so_ca": n, "ca": [[...], ...]}.

    Ghi từng lô (fetchmany) để bộ dữ liệu lớn không phải nằm trọn trong bộ nhớ hai lần. json.dumps của float dùng repr ⇒
    đọc lại được đúng từng bit (khác SAVE TRANSLATE /TYPE=CSV, vốn ghi theo định dạng hiển thị nên làm tròn)."""
    n_bien = spss.GetVariableCount()
    ten = [spss.GetVariableName(i) for i in range(n_bien)]
    kieu = [spss.GetVariableType(i) for i in range(n_bien)]
    so_ca = _so_ca(spss)
    with open(ra, "w", encoding="utf-8") as f:
        f.write('{"bien": ' + json.dumps(ten, ensure_ascii=False) + ', "kieu": ' + json.dumps(kieu))
        f.write(', "so_ca": ' + str(so_ca) + ', "ca": [')
        da_ghi = 0
        if n_bien and so_ca > 0:
            cur = spss.Cursor(isBinary=False)
            try:
                cur.SetUserMissingInclude(True)  # mã thiếu người dùng (9, −9991…) giữ nguyên giá trị, không thành None
                while da_ghi < so_ca:
                    lo = cur.fetchmany(min(1000, so_ca - da_ghi))
                    if not lo:
                        break
                    for ca in lo:
                        dong = json.dumps([gia_tri_tho(x) for x in ca], ensure_ascii=False)
                        f.write(("," if da_ghi else "") + "\n" + dong)
                        da_ghi += 1
            finally:
                cur.close()
        f.write("\n]}\n")
    return da_ghi


def main(argv):
    if len(argv) < 2 or argv[0] not in ("--cu-phap", "--kiem", "--tu-dien", "--du-lieu"):
        print(
            "dùng: spss_chay_nen.py --cu-phap <tệp.sps> | --kiem <ra.xml> | --tu-dien <tệp.sav> <ra.json> | "
            "--du-lieu <tệp.sav> <ra.json> [<tu_dien.json>]",
            file=sys.stderr,
        )
        return 2
    if argv[0] in ("--tu-dien", "--du-lieu") and len(argv) < 3:
        print("thiếu tệp ra .json", file=sys.stderr)
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
        elif argv[0] == "--tu-dien":
            spss.Submit("GET FILE=" + _chuoi(argv[1]) + ".")
            bien = _tu_dien(spss)
            with open(argv[2], "w", encoding="utf-8") as f:
                json.dump({"so_ca": _so_ca(spss), "bien": bien}, f, ensure_ascii=False, indent=1)
            print("SO_CA=" + str(_so_ca(spss)))
        else:
            spss.Submit("GET FILE=" + _chuoi(argv[1]) + ".")
            print("SO_CA_DOC=" + str(_du_lieu(spss, argv[2])))
            if len(argv) >= 4:
                with open(argv[3], "w", encoding="utf-8") as f:
                    json.dump({"so_ca": _so_ca(spss), "bien": _tu_dien(spss)}, f, ensure_ascii=False, indent=1)
            print("SO_CA=" + str(_so_ca(spss)))
    except spss.SpssError as e:  # lỗi cú pháp/dữ liệu trong SPSS
        print("LOI_SPSS " + str(e), file=sys.stderr)
        spss.StopSPSS()
        return 1
    spss.StopSPSS()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
