#!/usr/bin/env python3
"""Đo hiệu quả PROMPT CACHING từ sổ chi phí thật — theo từng công cụ, và kết luận công cụ nào cache ĐƯỢC.

VÌ SAO CÓ TỆP NÀY (21/11/2026, bác sĩ: «giải quyết vấn đề bộ nhớ đệm một cách tốt nhất»). Trang Console
«Phân tích bộ nhớ đệm» cho con số TỔNG theo model: Sonnet 5.5 đạt 12,7% đọc cache trên 13 Tr token vào. Nhưng tổng
theo model KHÔNG nói được công cụ nào gây ra phần trượt — mà hệ này có 6 công cụ cùng gọi Sonnet 5.5. Sổ chi phí
`~/.ebm-api-claude-chi-phi.json` đã ghi `nguon` + token vào/ghi cache/đọc cache cho TỪNG lượt, nên bóc theo nguồn
được ngay, không cần gọi thêm API và không tốn tiền.

ĐIỀU QUAN TRỌNG NHẤT công cụ này trả lời: tỷ lệ đọc cache THẤP không tự động là lỗi cần sửa. Cache chỉ tiết kiệm
khi đúng những token đó DÙ SAO cũng được gửi lại. Một công cụ đọc 200 abstract khác nhau, mỗi cái đúng một lần, thì
0% cache là ĐÚNG và không có cách nào sửa — ép cache chỗ đó chỉ làm đắt thêm. Vì vậy mỗi nguồn được xếp một trong ba
nhãn: ĐÃ TỐT · CÓ THỂ CẢI THIỆN · KHÔNG CACHE ĐƯỢC (bản chất công việc).

KHÔNG gọi mạng. KHÔNG sửa sổ. Chỉ đọc.

Dùng:
    python3 tools/do_cache_api.py                      # đọc sổ mặc định
    python3 tools/do_cache_api.py --so <đường dẫn>     # đọc sổ khác
    python3 tools/do_cache_api.py --json               # xuất JSON để nạp dashboard
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

_TOOLS = Path(__file__).resolve().parent
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

import api_claude_nc as API  # noqa: E402

# Ngưỡng xếp nhãn. Chọn theo kinh tế của cache, không theo cảm tính:
# — Khấu hao ghi < 1,0× nghĩa là phần ghi cache CHƯA được đọc lại đủ một lần ⇒ đang lỗ tiền vì cache.
# — Tỷ lệ đọc ≥ 60% là mức mà phần lặp lại đã được khai thác gần hết (Opus 5.5 của hệ này đạt 99,2%).
KHAU_HAO_LO = 1.0
TY_LE_DOC_TOT = 0.60
# Dưới mức này thì phần token đi qua cache quá nhỏ để kết luận gì — tránh phán trên vài lượt lẻ.
TOI_THIEU_TOKEN = 50_000


def _gia(model: str) -> Dict[str, float]:
    return API.GIA_USD_TRIEU_TOKEN.get(model) or {}


# Hệ số đọc cache lấy từ cầu nối (`API.he_so_doc_cache`) — KHÔNG tính lại ở đây, để hai nơi không lệch nhau.


def doc_so(duong: str) -> Dict[str, Any]:
    """Đọc sổ chi phí. Thiếu tệp / JSON hỏng ⇒ ném RuntimeError với câu nói rõ phải làm gì."""
    p = Path(duong).expanduser()
    if not p.exists():
        raise RuntimeError(
            f"Không thấy sổ chi phí: {p}\n"
            "Sổ chỉ sinh ra sau khi đã có lượt gọi API thật qua tools/api_claude_nc.py. "
            "Chạy trên MÁY đã gọi API (Mac/Windows của bác sĩ), không phải trong phiên Cloud."
        )
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise RuntimeError(f"Sổ chi phí không đọc được ({type(exc).__name__}): {p}") from exc


def gop_theo_nguon(so: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Cộng token theo `nguon`. Sổ giữ 200 lượt gần nhất nên đây là ảnh của giai đoạn gần, không phải cả tháng."""
    ra: Dict[str, Dict[str, Any]] = {}
    for luot in so.get("luot") or []:
        if not isinstance(luot, dict):
            continue
        ng = str(luot.get("nguon") or "(không ghi nguồn)")
        tk = luot.get("token") or {}
        if not isinstance(tk, dict):
            continue
        m = ra.setdefault(
            ng,
            {
                "so_luot": 0,
                "vao": 0,
                "cache_ghi": 0,
                "cache_ghi_1h": 0,
                "cache_doc": 0,
                "ra": 0,
                "model": {},
                "truot": {},
            },
        )
        m["so_luot"] += 1
        for k in ("vao", "cache_ghi", "cache_ghi_1h", "cache_doc", "ra"):
            try:
                m[k] += int(tk.get(k, 0) or 0)
            except (TypeError, ValueError):
                pass
        mdl = str(luot.get("model") or "")
        if mdl:
            m["model"][mdl] = m["model"].get(mdl, 0) + 1
        ly = luot.get("truot_cache")
        if ly:
            m["truot"][str(ly)] = m["truot"].get(str(ly), 0) + 1
    return ra


def _model_chinh(m: Dict[str, Any]) -> str:
    if not m["model"]:
        return API.MODEL_MAC_DINH
    return max(m["model"].items(), key=lambda kv: kv[1])[0]


def phan_tich(m: Dict[str, Any]) -> Dict[str, Any]:
    """Chỉ số + NHÃN cho một nguồn. Nhãn là phần có giá trị nhất: nó nói nên sửa hay nên để yên."""
    tong_vao = m["vao"] + m["cache_ghi"] + m["cache_doc"]
    mdl = _model_chinh(m)
    ty_le_doc = (m["cache_doc"] / tong_vao) if tong_vao else 0.0
    khau_hao = (m["cache_doc"] / m["cache_ghi"]) if m["cache_ghi"] else None
    nguong = API.NGUONG_CACHE_TOKEN.get(mdl, API.NGUONG_CACHE_THAN_TRONG)

    # Tiền ĐANG tiêu cho phần vào, và mức sàn nếu phần lặp lại được cache hết.
    g = _gia(mdl)
    hs_doc = API.he_so_doc_cache(mdl)
    usd_vao = (
        (m["vao"] + m["cache_ghi"] * API.HE_SO_GHI_CACHE + m["cache_doc"] * hs_doc) * g["vao"] / 1e6
        if g.get("vao")
        else None
    )

    if tong_vao < TOI_THIEU_TOKEN:
        nhan, vi_sao = "CHƯA ĐỦ DỮ LIỆU", f"chỉ {tong_vao:,} token vào — cần ≥ {TOI_THIEU_TOKEN:,} mới kết luận"
    elif m["cache_ghi"] == 0 and m["cache_doc"] == 0:
        nhan, vi_sao = (
            "CHƯA BẬT CACHE",
            f"không có token cache nào; prefix tĩnh phải ≥ {nguong:,} token ({mdl}) mới cache được",
        )
    elif khau_hao is not None and khau_hao < KHAU_HAO_LO:
        nhan, vi_sao = (
            "ĐANG LỖ VÌ CACHE",
            f"khấu hao ghi {khau_hao:.2f}× — ghi cache nhiều hơn đọc lại; cân nhắc BỎ cache ở nguồn này",
        )
    elif ty_le_doc >= TY_LE_DOC_TOT:
        nhan, vi_sao = "ĐÃ TỐT", f"{ty_le_doc:.0%} token vào đến từ cache"
    else:
        nhan, vi_sao = (
            "CẦN XEM LẠI",
            f"cache có hoạt động (khấu hao {khau_hao:.2f}×) nhưng chỉ {ty_le_doc:.0%} token vào qua cache — "
            "phần lớn đầu vào là nội dung MỚI mỗi lượt",
        )
    return {
        "so_luot": m["so_luot"],
        "model": mdl,
        "tong_token_vao": tong_vao,
        "token_khong_cache": m["vao"],
        "token_cache_ghi": m["cache_ghi"],
        "token_cache_ghi_1h": m["cache_ghi_1h"],
        "token_cache_doc": m["cache_doc"],
        "ty_le_doc_cache": round(ty_le_doc, 4),
        "khau_hao_ghi": None if khau_hao is None else round(khau_hao, 2),
        "nguong_cache_model": nguong,
        "usd_phan_vao": None if usd_vao is None else round(usd_vao, 4),
        "nhan": nhan,
        "vi_sao": vi_sao,
        "ly_do_truot": dict(sorted(m["truot"].items(), key=lambda kv: -kv[1])),
    }


def bao_cao(so: Dict[str, Any]) -> Dict[str, Any]:
    nguon = {k: phan_tich(v) for k, v in gop_theo_nguon(so).items()}
    tong = {
        "thang": so.get("thang"),
        "usd_da_ghi": so.get("usd"),
        "so_luot_trong_so": len(so.get("luot") or []),
        "tong_token_vao": sum(v["tong_token_vao"] for v in nguon.values()),
        "tong_cache_doc": sum(v["token_cache_doc"] for v in nguon.values()),
    }
    tong["ty_le_doc_cache"] = (
        round(tong["tong_cache_doc"] / tong["tong_token_vao"], 4) if tong["tong_token_vao"] else 0.0
    )
    return {"tong": tong, "theo_nguon": dict(sorted(nguon.items(), key=lambda kv: -kv[1]["tong_token_vao"]))}


def in_bang(bc: Dict[str, Any]) -> None:
    t = bc["tong"]
    print("═" * 100)
    print(f"HIỆU QUẢ PROMPT CACHING — sổ tháng {t['thang']} · {t['so_luot_trong_so']} lượt gần nhất")
    print("═" * 100)
    print(f"Tổng token vào: {t['tong_token_vao']:,} · đọc từ cache: {t['tong_cache_doc']:,} "
          f"({t['ty_le_doc_cache']:.1%}) · USD đã ghi trong tháng: {t['usd_da_ghi']}")
    if not bc["theo_nguon"]:
        print("\nSổ chưa có lượt nào ghi `token` — chưa đo được.")
        return
    print()
    print(f"{'NGUỒN':<32} {'LƯỢT':>5} {'TOKEN VÀO':>12} {'ĐỌC':>7} {'KHẤU HAO':>9}  NHÃN")
    print("─" * 100)
    for ten, v in bc["theo_nguon"].items():
        kh = "—" if v["khau_hao_ghi"] is None else f"{v['khau_hao_ghi']:.2f}×"
        print(f"{ten[:32]:<32} {v['so_luot']:>5} {v['tong_token_vao']:>12,} "
              f"{v['ty_le_doc_cache']:>6.1%} {kh:>9}  {v['nhan']}")
    print("─" * 100)
    print("\nCHI TIẾT")
    for ten, v in bc["theo_nguon"].items():
        print(f"\n• {ten}  [{v['nhan']}]")
        print(f"    {v['vi_sao']}")
        print(f"    model {v['model']} · ngưỡng cache {v['nguong_cache_model']:,} token"
              + (f" · phần vào ≈ {v['usd_phan_vao']} USD" if v["usd_phan_vao"] is not None else ""))
        if v["token_cache_ghi_1h"]:
            print(f"    ghi TTL 1h: {v['token_cache_ghi_1h']:,} token (tính {API.HE_SO_GHI_CACHE_1H}× giá vào)")
        if v["ly_do_truot"]:
            ds = " · ".join(f"{k}×{n}" for k, n in v["ly_do_truot"].items())
            print(f"    lý do trượt (từ chẩn đoán): {ds}")
        else:
            print(f"    lý do trượt: chưa có — bật {API.BIEN_CHAN_DOAN_CACHE}=1 rồi chạy lại để máy chủ chỉ ra")
    print("\n" + "─" * 100)
    print("ĐỌC NHÃN THẾ NÀO")
    print("  ĐÃ TỐT            — phần lặp lại đã khai thác gần hết, để yên.")
    print("  CẦN XEM LẠI       — cache chạy nhưng phần lớn đầu vào là nội dung MỚI mỗi lượt. Kiểm xem nội dung đó")
    print("                      CÓ THẬT bị gửi lặp lại không; nếu không, 0% là đúng và KHÔNG nên ép cache.")
    print("  ĐANG LỖ VÌ CACHE  — ghi cache mà không đọc lại đủ một lần. Bỏ cache_he_thong ở nguồn này.")
    print("  CHƯA BẬT CACHE    — không có token cache; chỉ đáng bật nếu prefix tĩnh vượt ngưỡng của model.")
    print("\nCẠM BẪY: đừng phình prefix ra cho «cache được». Cache chỉ lợi khi đúng token đó DÙ SAO cũng gửi lại;")
    print("đọc lại n lần tốn n × hệ số đọc, nên dồn nội dung dùng-một-lần vào prefix chung luôn ĐẮT HƠN.")


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Đo hiệu quả prompt caching theo từng công cụ, từ sổ chi phí thật.")
    ap.add_argument("--so", default=os.environ.get("EBM_SO_CHI_PHI") or API.SO_CHI_PHI, help="đường dẫn sổ chi phí")
    ap.add_argument("--json", action="store_true", help="xuất JSON thay vì bảng")
    a = ap.parse_args(argv)
    try:
        so = doc_so(a.so)
    except RuntimeError as exc:
        print(f"⚠️  {exc}", file=sys.stderr)
        return 2
    bc = bao_cao(so)
    if a.json:
        print(json.dumps(bc, ensure_ascii=False, indent=2))
    else:
        in_bang(bc)
    return 0


if __name__ == "__main__":  # pragma: no cover - lớp CLI mỏng
    raise SystemExit(main())
