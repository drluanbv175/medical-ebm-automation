#!/usr/bin/env python3
"""tra_thuoc_quoc_te.py — Tra cứu thuốc quốc tế cho agent `ke-don-an-toan` (thêm 20/09/2026).

Hai việc, đều gọi THẲNG API công khai chính thức (không khoá, không chạy mã bên thứ ba):
  chuan-hoa <tên>   RxNorm (NLM): tên thuốc/biệt dược → mã RxCUI + hoạt chất. KHÔNG kiểm tương tác/liều.
  ema <hoạt chất>   EMA: trạng thái cấp phép TẬP TRUNG tại EU (Authorised/Withdrawn/…), giám sát bổ sung,
                    cấp phép có điều kiện.

Nguồn gốc lựa chọn: đánh giá `JamesANZ/medical-mcp` — xem `.claude/agents/_CONNECTOR-CHUNG-CU.md` §1ter.

Dùng:
    python3 medical-ebm-automation/tools/tra_thuoc_quoc_te.py chuan-hoa "Glucophage"
    python3 medical-ebm-automation/tools/tra_thuoc_quoc_te.py ema "rosiglitazone" --json

Mã thoát: 0 = có kết quả · 1 = không thấy (hợp lệ, KHÔNG có nghĩa «không tồn tại» — đọc cảnh báo) ·
          2 = LỖI/KHÔNG BIẾT (mạng, dữ liệu, đầu vào bị từ chối) — không được đọc thành «không thấy».
Mọi kết quả kèm nguồn; chỉ là dữ liệu tra cứu, cần bác sĩ kiểm chứng.

Dòng miễn trừ của NLM (điều khoản RxNav, đọc 30/09/2026): `chuan-hoa` LUÔN kèm dòng đó NGUYÊN VĂN tiếng Anh — trường
`mien_tru_nlm` trong JSON, một dòng riêng dưới dòng «Nguồn» ở bản đọc. `ema` không dùng dữ liệu NLM nên KHÔNG kèm.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.sources.ema_medicines import EmaMedicinesClient  # noqa: E402
from app.sources.rxnorm import MIEN_TRU_NLM, RxNormClient  # noqa: E402
from app.utils.console import configure_unicode_console  # noqa: E402

DISCLAIMER = "Cần bác sĩ kiểm chứng."
_CO_HOAT_CHAT = ("IN", "MIN", "PIN")


def ma_thoat(kq: Dict[str, Any]) -> int:
    tt = kq.get("trang_thai")
    if tt in ("khop_chinh_xac", "gan_dung", "co_ket_qua"):
        return 0
    if tt == "khong_thay":
        return 1
    return 2


def _dong_chuan_hoa(r: Dict[str, Any]) -> str:
    ten, tty = r["ten"] or "(không rõ tên)", r["tty"] or "?"
    if not r.get("hieu_luc", True):
        return (f"  • RxCUI {r['rxcui']} · {ten} [{tty}] — MÃ ĐÃ NGỪNG ({r.get('trang_thai_rxcui')}), "
                "không có hoạt chất để đối chiếu")
    hc = ", ".join(f"{h['ten']} (RxCUI {h['rxcui']})" for h in r.get("hoat_chat", []))
    if not hc and r.get("tty") in _CO_HOAT_CHAT:
        hc = "(chính là hoạt chất)"
    diem = f" · điểm {r['diem']}" if r.get("diem") else ""
    return f"  • RxCUI {r['rxcui']} · {ten} [{tty}]{diem} → hoạt chất: {hc}"


def _in_chuan_hoa(kq: Dict[str, Any]) -> None:
    print(f"RxNorm — «{kq['ten_nhap']}» → {kq['trang_thai']}")
    for r in kq["ket_qua"]:
        print(_dong_chuan_hoa(r))
    if kq.get("ly_do"):
        print("  Lý do:", kq["ly_do"])


def _dong_ema(b: Dict[str, Any]) -> str:
    co = []
    if b["additional_monitoring"] == "Yes":
        co.append("GIÁM SÁT BỔ SUNG")
    if b["conditional_approval"] == "Yes":
        co.append("cấp phép có điều kiện")
    if b["patient_safety"] == "Yes":
        co.append("patient_safety")
    ket_thuc = (b["withdrawal_expiry_revocation_lapse_of_marketing_authorisation_date"]
                or b["withdrawal_of_application_date"] or b["refusal_of_marketing_authorisation_date"])
    dong = f"  • {b['name_of_medicine']} — {b['medicine_status']}"
    if co:
        dong += f" ({', '.join(co)})"
    dong += f" · hoạt chất: {b['active_substance']} · ATC {b['atc_code_human'] or '—'}"
    if ket_thuc:
        dong += f" · kết thúc/rút: {ket_thuc}"
    return dong + f" · cập nhật {b['last_updated_date'] or '—'} · {b['medicine_url']}"


def _in_ema(kq: Dict[str, Any]) -> None:
    print(f"EMA — «{kq['tu_khoa']}» → {kq['trang_thai']}")
    if kq.get("du_phong") and kq["trang_thai"] in ("co_ket_qua", "khong_thay"):
        # 01/10/2026: EMA bị chặn trên đường mạng (vd VPN) ⇒ kết quả từ Sổ đăng ký Liên minh của Uỷ ban châu Âu.
        print(f"  ⚠ DỰ PHÒNG sổ EC (EMA không tới được: {str(kq['du_phong'].get('ly_do_ema'))[:120]}) · "
              f"{kq.get('tong_bai_ghi_du_phong')} bản ghi sổ EC · khớp {kq.get('so_khop')} · "
              f"theo trạng thái {kq.get('theo_trang_thai')}")
    elif kq["trang_thai"] in ("co_ket_qua", "khong_thay"):
        print(f"  Dữ liệu lúc {kq.get('du_lieu_luc') or '?'} · {kq.get('tong_bai_ghi_ema')} bản ghi EMA · "
              f"khớp {kq.get('so_khop')} · theo trạng thái {kq.get('theo_trang_thai')}")
    for b in kq["ket_qua"]:
        print(_dong_ema(b))
    if kq.get("bi_cat_bot"):
        print(f"  … còn {kq['bi_cat_bot']} bản ghi nữa (dùng --toi-da để xem thêm)")
    if kq.get("ly_do"):
        print("  Lý do:", kq["ly_do"])


def main(argv: Optional[list] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="lenh", required=True)
    a = sub.add_parser("chuan-hoa", help="RxNorm: chuẩn hoá tên thuốc")
    a.add_argument("ten")
    b = sub.add_parser("ema", help="EMA: trạng thái cấp phép tập trung tại EU")
    b.add_argument("tu_khoa")
    b.add_argument("--ca-thu-y", action="store_true", help="gồm cả thuốc thú y (mặc định chỉ thuốc người)")
    b.add_argument("--toi-da", type=int, default=25)
    for p in (a, b):
        p.add_argument("--json", action="store_true", help="in JSON máy đọc")
    args = ap.parse_args(argv)

    if args.lenh == "chuan-hoa":
        kq = RxNormClient().chuan_hoa(args.ten)
        # Điều khoản RxNav đề nghị ứng dụng dùng dữ liệu NLM kèm dòng miễn trừ NGUYÊN VĂN; hệ này coi là bắt buộc.
        # Client đã gắn sẵn; GÁN LẠI ở đây để lệnh không bao giờ in thiếu (hay in một bản đã bị sửa/dịch) dù client bị
        # thay hoặc đổi về sau.
        kq["mien_tru_nlm"] = MIEN_TRU_NLM
    else:
        # EMA không phải dữ liệu NLM — cố ý KHÔNG gắn dòng miễn trừ của NLM vào đây.
        kq = EmaMedicinesClient().tra(args.tu_khoa, ca_thu_y=args.ca_thu_y, toi_da=args.toi_da)
    if args.json:
        print(json.dumps(kq, ensure_ascii=False, indent=2))
    else:
        (_in_chuan_hoa if args.lenh == "chuan-hoa" else _in_ema)(kq)
        for c in kq.get("canh_bao", []):
            print("  ⚠", c)
        print(f"  Nguồn: {kq.get('nguon')}. {DISCLAIMER}")
        if kq.get("mien_tru_nlm"):
            print("  Miễn trừ của nguồn dữ liệu (nguyên văn tiếng Anh, không dịch):")
            print(f"  {kq['mien_tru_nlm']}")
    return ma_thoat(kq)


def chay_cli(argv: Optional[list] = None) -> int:
    """Điểm vào dòng lệnh: ép console UTF-8 TRƯỚC mọi print, và mọi ngoại lệ bất ngờ ⇒ mã 2 (KHÔNG BIẾT).

    Trên Windows (cp1252), print tiếng Việt/biểu tượng từng ném UnicodeEncodeError ⇒ traceback thoát mã 1,
    trùng mã «không thấy / không khớp» — tín hiệu lỗi bị đọc thành kết quả hợp lệ. Ngoại lệ lạ cũng vậy.
    KeyboardInterrupt/SystemExit (vd argparse) được ném lại nguyên vẹn.
    """
    configure_unicode_console()
    try:
        return main(argv)
    except (KeyboardInterrupt, SystemExit):
        raise
    except Exception as exc:  # noqa: BLE001 — mọi lỗi lạ đều là «KHÔNG BIẾT», không phải «không thấy»
        # Bản thân dòng báo lỗi cũng có thể không encode được (stream không có reconfigure) —
        # khi đó vẫn phải trả mã KHÔNG BIẾT, không để traceback thoát mã 1.
        try:
            print(f"LỖI/KHÔNG BIẾT (tra_thuoc_quoc_te): ngoại lệ bất ngờ {type(exc).__name__}: {exc} — "
                  f"KHÔNG được đọc thành «không thấy». {DISCLAIMER}", file=sys.stderr)
        except Exception:  # noqa: BLE001
            print("LOI/KHONG BIET (tra_thuoc_quoc_te): ngoai le bat ngo " + type(exc).__name__, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(chay_cli())
