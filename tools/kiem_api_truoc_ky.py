#!/usr/bin/env python3
"""MỘT lệnh kiểm bằng Claude API TRƯỚC KHI KÝ/NỘP — gộp phản biện máy (có thẩm tra), kiểm nội dung trích dẫn A12 và
tình trạng hội đồng cổng thành MỘT phiếu.

VÌ SAO (21/11/2026, bác sĩ chọn «B — một lệnh kiểm API trước khi ký/nộp»): trước khi PI ký G10 C1a phải nhớ chạy ba
công cụ riêng, tự xem báo cáo nào đã CŨ (đề cương sửa sau lượt kiểm), tự cộng chi phí và tự đọc ba báo cáo. Lệnh này:
1. đọc báo cáo hiện có, xét hiệu lực bằng mã băm tệp đã kiểm (`duyet_kiem_may_api.hieu_luc`);
2. chạy khô (mặc định): ước chi phí CHỈ cho phần thiếu/cũ — không gọi API (21/11/2026: dùng theo tín dụng tài khoản,
   không trần tự đặt; hết tín dụng ⇒ cầu nối tự dừng);
3. `--goi-api`: chạy lại ĐÚNG phần thiếu/cũ (phản biện máy, kiểm nội dung trích dẫn), chặn trước nếu tổng ước vượt
   trần (chỉ khi biến môi trường OS đặt trần) hoặc tài khoản vừa báo hết tín dụng; báo cáo còn hiệu lực thì dùng lại,
   không trả tiền lần hai;
4. ghi phiếu `exports/<mã>/kiem_may_api/PHIEU_KIEM_API_TRUOC_KY_<mã>.md/.json`.
Hội đồng cổng (Batch API, nhiều lượt, có thể vài giờ) KHÔNG chạy trong lệnh này — phiếu chỉ báo trạng thái và in lệnh.

Ranh giới: TƯ VẤN — không sửa đề cương, không mở/chặn cổng, không ký, không ghi nhãn đúng/sai thay bác sĩ. «Không còn
việc kiểm máy» KHÔNG có nghĩa là đề cương đạt — chỉ là các lượt máy đã chạy trên đúng bản hiện hành và không còn phát
hiện mức cao/vừa chưa xem.

Dùng: kiem_api_truoc_ky.py --study <mã> [--gate G10] [--goi-api] [--json]
Mã thoát: 0 không còn việc kiểm máy · 1 còn việc (thiếu/cũ, phát hiện cần xem, hội đồng chưa đồng thuận, mục chưa
duyệt) · 2 không kiểm được (thiếu khoá, hết tín dụng, lỗi API) · 3 tham số sai.
"""

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import io
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

REPO = Path(__file__).resolve().parents[1]
for _d in (REPO, REPO / "tools"):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

import api_claude_nc as API  # noqa: E402
import duyet_kiem_may_api as DK  # noqa: E402
import hoi_dong_cong as HDC  # noqa: E402
import kiem_noi_dung_trich_dan as KND  # noqa: E402
import phan_bien_may_de_cuong as PBM  # noqa: E402

TEN_PHIEU = "PHIEU_KIEM_API_TRUOC_KY_{s}"
CONG_CU = "kiem_api_truoc_ky"
# Hai phần chạy đồng bộ được trong lệnh: (khoá báo cáo ở duyet_kiem_may_api, mô-đun, tên người đọc)
PHAN = (("PHAN_BIEN", PBM, "phản biện máy đề cương (có thẩm tra)"), ("A12", KND, "kiểm nội dung trích dẫn A12"))
HOI_DONG_XONG = ("ĐỒNG THUẬN",)


def _chay_im(ham: Callable[..., int], argv: List[str], **kw: Any) -> tuple:
    """Chạy `main` của một công cụ, bắt stdout (để đọc JSON chạy khô). Trả (mã thoát, chữ in ra)."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        ma = ham(argv, **kw)
    return ma, buf.getvalue()


def _doc_json_in(chu: str) -> Optional[Dict[str, Any]]:
    """Khối JSON đầu tiên trong chữ in ra (công cụ có thể in dòng cảnh báo trước)."""
    i = chu.find("{")
    if i < 0:
        return None
    try:
        dl = json.JSONDecoder().raw_decode(chu[i:])[0]
    except json.JSONDecodeError:
        return None
    return dl if isinstance(dl, dict) else None


def uoc_phan(khoa: str, mod: Any, study: str, goc: Path, client: Any = None) -> Dict[str, Any]:
    """Ước chi phí MỘT phần bằng chính phần chạy khô của công cụ (không gọi API, không ghi tệp)."""
    ma, chu = _chay_im(mod.main, ["--study", study, "--json"], client=client, goc=goc)
    dl = _doc_json_in(chu) if ma == 0 else None
    if dl is None:
        return {"uoc_usd": None, "loi": f"chạy khô mã {ma}: {chu.strip()[:200]}"}
    usd = dl.get("uoc_usd")
    if khoa == "PHAN_BIEN" and dl.get("uoc_usd_tham_tra") is not None and usd is not None:
        usd += dl["uoc_usd_tham_tra"]
    return {"uoc_usd": usd, "uoc_tinh": dl.get("uoc_tinh"), "loi": None}


def tinh_trang_phan(study: str, goc: Path) -> Dict[str, Dict[str, Any]]:
    """Mỗi phần: có báo cáo không, còn hiệu lực không (mã băm tệp đã kiểm), số mục cần xem."""
    bcs = DK.doc_bao_cao(study, goc)
    ra: Dict[str, Dict[str, Any]] = {}
    for khoa, _mod, ten in PHAN:
        x = bcs.get(khoa)
        if x is None:
            ra[khoa] = {"ten": ten, "co": False, "cu": None, "ly_do": "chưa có báo cáo"}
            continue
        if x.get("hong"):
            ra[khoa] = {"ten": ten, "co": False, "cu": None, "ly_do": "báo cáo hỏng — chạy lại"}
            continue
        cu, ly_do = DK.hieu_luc(x["bc"], study, goc)
        ra[khoa] = {"ten": ten, "co": True, "cu": cu, "ly_do": ly_do, "bc": x["bc"], "muc": x["muc"]}
    return ra


def can_chay(t: Dict[str, Any]) -> bool:
    """Phần phải chạy (lại): chưa có/hỏng, CŨ, hoặc không khẳng định được còn hiệu lực (fail-safe)."""
    return not t["co"] or t["cu"] is not False


def tom_tat_phan_bien(bc: Dict[str, Any]) -> Dict[str, Any]:
    ph = bc.get("phat_hien") or []
    tt = bc.get("tham_tra") or {}
    return {
        "cao_vua": [p for p in ph if p.get("muc") in ("cao", "vua")],
        "thap": sum(1 for p in ph if p.get("muc") == "thap"),
        "tham_tra_loai": len(bc.get("loai_sau_tham_tra") or []),
        "tham_tra": ("lỗi — giữ nguyên mọi phát hiện" if tt.get("loi") else tt.get("model")) if tt else "không chạy",
        "khong_xac_minh": len(bc.get("khong_xac_minh") or []),
        "trich_dan_tat_dinh": bc.get("trich_dan_tat_dinh") or [],
    }


def tom_tat_a12(bc: Dict[str, Any]) -> Dict[str, Any]:
    kq = bc.get("ket_qua") or []
    can = [k for k in kq if k.get("muc") in DK.MUC_A12_CAN_XEM or any(
        str(x).startswith("so_khong_thay") for x in (k.get("co") or []))]
    return {"so_cap": len(kq), "can_xem": can, "loi": bc.get("loi") or []}


def phieu(study: str, gate: str, goc: Path, chay: Dict[str, Any]) -> Dict[str, Any]:
    """Dựng phiếu từ báo cáo HIỆN CÓ (sau khi đã chạy lại phần cần chạy)."""
    out_dir = goc / "exports" / study
    tt = tinh_trang_phan(study, goc)
    viec: List[str] = []
    ds: Dict[str, Any] = {}
    for khoa, _mod, ten in PHAN:
        t = tt[khoa]
        muc: Dict[str, Any] = {"ten": ten, "co": t["co"], "cu": t["cu"], "ly_do": t["ly_do"],
                               "chay_luot_nay": chay.get(khoa)}
        if can_chay(t):
            viec.append(f"{ten}: {t['ly_do']} — chạy lại (`--goi-api`)")
        elif khoa == "PHAN_BIEN":
            s = tom_tat_phan_bien(t["bc"])
            muc.update(s)
            if s["cao_vua"]:
                viec.append(f"{ten}: {len(s['cao_vua'])} phát hiện mức cao/vừa cần bác sĩ xem")
            if s["trich_dan_tat_dinh"]:
                viec.append(f"{ten}: {len(s['trich_dan_tat_dinh'])} vấn đề trích dẫn tất định")
        else:
            s = tom_tat_a12(t["bc"])
            muc.update(s)
            if s["can_xem"]:
                viec.append(f"{ten}: {len(s['can_xem'])} cặp (đoạn, tài liệu) cần bác sĩ xem")
            if s["loi"]:
                viec.append(f"{ten}: lượt kiểm có {len(s['loi'])} lỗi — một phần không kiểm được")
        ds[khoa] = muc
    try:
        hd = HDC.tom_tat_cong(gate, out_dir, goc)
    except Exception as exc:  # hồ sơ hội đồng hỏng/thiếu — không đo được, không phải «đạt»
        hd = {"trang_thai": "KHÔNG ĐO ĐƯỢC", "ly_do": [f"{type(exc).__name__}: {exc}"]}
    if hd.get("trang_thai") not in HOI_DONG_XONG:
        viec.append(f"hội đồng {gate}: {hd.get('trang_thai')} — "
                    f"`python3 tools/hoi_dong_cong_batch.py uoc-tinh --study {study} --gate {gate}`")
    dt_dk = DK.tinh_trang(study, goc)
    chua = (dt_dk.get("do_dung") or {}).get("tong", {}).get("chua_duyet") if dt_dk.get("do_dung") else None
    if chua:
        viec.append(f"duyệt kiểm máy: {chua} mục chưa có nhãn của bác sĩ — `python3 tools/duyet_kiem_may_api.py "
                    f"phieu --study {study}` (để đo tỷ lệ đúng; không chặn ký)")
    tep = out_dir / f"DE_CUONG_NOP_HOI_DONG_{study}.md"
    return {
        "schema": "kiem_api_truoc_ky/v1",
        "study": study,
        "gate": gate,
        "luc": dt.datetime.now().isoformat(timespec="seconds"),
        "tep": tep.name,
        "tep_sha256": DK._sha_tep(tep) if tep.is_file() else None,
        "phan": ds,
        "hoi_dong": {k: hd.get(k) for k in ("trang_thai", "ly_do", "so_bien_ban_hieu_luc", "cu")},
        "chua_duyet": chua,
        "viec": viec,
    }


def _tran_chu(tran: Any) -> str:
    return "theo tín dụng tài khoản (không trần tự đặt)" if tran is None else f"trần tháng {tran} USD"


def _o(s: Any) -> str:
    return str(s if s is not None else "").replace("|", "/").replace("\n", " ").strip()


def phieu_md(p: Dict[str, Any], uoc: Dict[str, Any]) -> str:
    pb, a12, hd = p["phan"].get("PHAN_BIEN", {}), p["phan"].get("A12", {}), p["hoi_dong"]

    def hl(m: Dict[str, Any]) -> str:
        if not m.get("co"):
            return "chưa có"
        return {False: "còn hiệu lực", True: "CŨ"}.get(m.get("cu"), "không khẳng định được") + f" ({m.get('ly_do')})"

    dong = [
        f"# Phiếu kiểm bằng Claude API trước khi ký/nộp — {p['study']}",
        "",
        f"- Tệp: `{p['tep']}` · SHA-256 `{str(p['tep_sha256'])[:12]}…` · lúc {p['luc']} · cổng hội đồng {p['gate']}",
        "- TƯ VẤN của máy: không sửa đề cương, không mở/chặn cổng, không thay phản biện người hay chữ ký PI.",
        "",
        "| Phần | Báo cáo | Kết quả | Chạy lượt này |",
        "|---|---|---|---|",
    ]
    if pb.get("co") and pb.get("cu") is False:
        kq_pb = (f"{len(pb.get('cao_vua') or [])} mức cao/vừa · {pb.get('thap', 0)} mức thấp · thẩm tra "
                 f"{pb.get('tham_tra')} loại {pb.get('tham_tra_loai', 0)} · "
                 f"{pb.get('khong_xac_minh', 0)} không xác minh")
    else:
        kq_pb = "—"
    if a12.get("co") and a12.get("cu") is False:
        kq_a12 = (f"{a12.get('so_cap', 0)} cặp · {len(a12.get('can_xem') or [])} cần xem · "
                  f"{len(a12.get('loi') or [])} lỗi")
    else:
        kq_a12 = "—"
    dong += [
        f"| {_o(pb.get('ten'))} | {_o(hl(pb))} | {_o(kq_pb)} | {_o(pb.get('chay_luot_nay') or 'không')} |",
        f"| {_o(a12.get('ten'))} | {_o(hl(a12))} | {_o(kq_a12)} | {_o(a12.get('chay_luot_nay') or 'không')} |",
        f"| hội đồng {p['gate']} | {_o(hd.get('trang_thai'))} | {hd.get('so_bien_ban_hieu_luc') or 0} biên bản còn "
        f"hiệu lực | không (Batch API nhiều lượt — chạy riêng) |",
        "",
    ]
    if uoc:
        dong += [f"Chi phí: ước {uoc.get('tong_uoc_usd')} USD cho phần cần chạy · {_tran_chu(uoc.get('tran'))} · "
                 f"đã tiêu {uoc.get('da_tieu')} USD.", ""]
    if pb.get("cao_vua"):
        dong += ["## Phát hiện mức cao/vừa của phản biện máy (sau thẩm tra)", "",
                 "| Mức | Dòng | Trích | Vấn đề |", "|---|---|---|---|"]
        dong += [f"| {x.get('muc')} | {x.get('dong') or ''} | {_o(x.get('trich'))[:120]} | "
                 f"{_o(x.get('van_de'))[:200]} |"
                 for x in pb["cao_vua"]]
        dong.append("")
    if a12.get("can_xem"):
        dong += ["## Cặp trích dẫn cần xem (A12)", "", "| Đoạn | Tài liệu | Mức |", "|---|---|---|"]
        dong += [f"| {_o(k.get('id'))} | [{_o(k.get('so'))}] | {_o(k.get('muc'))} |" for k in a12["can_xem"][:40]]
        dong.append("")
    dong += ["## Việc còn lại", ""]
    dong += [f"- {v}" for v in p["viec"]] or ["- Không còn việc kiểm máy trên bản hiện hành (không có nghĩa đề cương "
                                              "đạt — vẫn cần bác sĩ, Hội đồng và PI)."]
    dong += ["", "Cần bác sĩ kiểm chứng.", ""]
    return "\n".join(dong)


def _ghi(p: Path, chu: str) -> None:
    tmp = p.with_suffix(p.suffix + ".tam")
    tmp.write_text(chu, encoding="utf-8", newline="\n")
    os.replace(tmp, p)


def main(argv: Optional[Sequence[str]] = None, client: Any = None, goc: Path = REPO) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--study", required=True)
    ap.add_argument("--gate", default="G10", choices=HDC.CONG, help="cổng hội đồng cần đọc trạng thái (mặc định G10)")
    ap.add_argument("--goi-api", action="store_true", help="chạy lại phần thiếu/cũ (TÍNH PHÍ) rồi ghi phiếu")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if not re.fullmatch(r"[A-Za-z0-9._-]+", a.study):
        print("❌ --study chỉ nhận chữ/số/._-")
        return 3
    out_dir = goc / "exports" / a.study
    if not (out_dir / f"DE_CUONG_NOP_HOI_DONG_{a.study}.md").is_file():
        print(f"❌ Không thấy đề cương nộp của {a.study}")
        return 3
    tt = tinh_trang_phan(a.study, goc)
    can = [(k, m, ten) for k, m, ten in PHAN if can_chay(tt[k])]
    uoc_ds = {k: uoc_phan(k, m, a.study, goc, client) for k, m, _ in can}
    tong = None if any(u["uoc_usd"] is None for u in uoc_ds.values()) else round(
        sum(u["uoc_usd"] for u in uoc_ds.values()), 4)
    try:
        da_tieu: Optional[float] = round(float(API.doc_so_chi_phi().get("usd") or 0), 2)
    except API.LoiApi:  # sổ hỏng ⇒ không đoán còn tiền; `--goi-api` sẽ bị `kiem_ngan_sach` chặn
        da_tieu = None
    tran, _nguon = API.tran_usd_thang_nguon()
    uoc = {"phan": {k: u.get("uoc_tinh") or u.get("loi") for k, u in uoc_ds.items()}, "tong_uoc_usd": tong,
           "tran": tran, "da_tieu": da_tieu}
    chay: Dict[str, Any] = {}
    if not a.goi_api:
        if can:
            print(f"CHẠY KHÔ — {a.study}: cần chạy lại {', '.join(ten for _, _, ten in can)} · ước "
                  f"{tong if tong is not None else '?'} USD ({_tran_chu(tran)}, đã tiêu {uoc['da_tieu']} USD). "
                  "Gọi thật: thêm --goi-api (tính phí).")
        p = phieu(a.study, a.gate, goc, chay)
        if a.json:
            print(json.dumps({"chay_kho": True, "uoc": uoc, **p}, ensure_ascii=False, indent=1, default=str))
        else:
            for v in p["viec"]:
                print(f"  · {v}")
            if not p["viec"]:
                print("🟢 Không còn việc kiểm máy trên bản hiện hành.")
        return 1 if p["viec"] else 0
    if can:
        if tong is None:
            print("⚪ Không ước được chi phí phần cần chạy — không gọi API: "
                  + "; ".join(f"{k}: {u.get('loi')}" for k, u in uoc_ds.items() if u["uoc_usd"] is None))
            return 2
        try:
            API.kiem_ngan_sach(tong, "claude-sonnet-5-5", CONG_CU)
        except API.LoiApi as exc:
            print(f"⛔ {exc} — không chạy phần nào.")
            return 2
        for k, m, ten in can:
            ma, chu = _chay_im(m.main, ["--study", a.study, "--goi-api"], client=client, goc=goc)
            dong_cuoi = [x for x in chu.strip().splitlines() if x.strip()][-1:] or [""]
            chay[k] = f"mã {ma}: {dong_cuoi[0][:160]}"
            print(f"▶ {ten}: {chay[k]}")
            if ma == 2:
                print(f"⚪ {ten} không kiểm được — dừng, phiếu ghi phần đã có.")
                break
    p = phieu(a.study, a.gate, goc, chay)
    ra = out_dir / "kiem_may_api"
    ra.mkdir(parents=True, exist_ok=True)
    ten = TEN_PHIEU.format(s=a.study)
    _ghi(ra / f"{ten}.md", phieu_md(p, uoc))
    _ghi(ra / f"{ten}.json", json.dumps({**p, "uoc": uoc}, ensure_ascii=False, indent=1, default=str) + "\n")
    if a.json:
        print(json.dumps({**p, "uoc": uoc}, ensure_ascii=False, indent=1, default=str))
    else:
        print(("🟠 " + f"{len(p['viec'])} việc còn lại" if p["viec"] else "🟢 Không còn việc kiểm máy")
              + f" · phiếu {ra / (ten + '.md')}")
    if any(str(v).startswith("mã 2") for v in chay.values()):
        return 2
    return 1 if p["viec"] else 0


if __name__ == "__main__":
    sys.exit(main())
