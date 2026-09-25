#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""KIỂM CHUẨN VÀNG GUIDELINE — engine có trả được guideline hiện hành MẠNH NHẤT không (25/09/2026).

Vì sao có: đo sống 24/09/2026 cho thấy `PubMedClient.search()` trả «10 bài MỚI NHẤT» thay vì «10 bài
MẠNH NHẤT» — 0/15 guideline chuẩn 2023–2026 lọt vào kết quả của 6 bệnh ngoại trú, và không chốt nào
bắt được vì mọi bài trả về đều là bài THẬT (không mock, có PMID). Lỗi loại này chỉ lộ ra khi đối chiếu
với một đáp án biết trước. Công cụ này là đáp án đó: đọc `config/chuan_vang_guideline.json`, gọi engine
đúng đường mặc định, và báo nhóm guideline nào KHÔNG lọt top N.

Mã thoát: 0 = mọi nhóm đạt · 1 = có nhóm trượt (đọc danh sách) · 2 = KHÔNG ĐO ĐƯỢC (mock, thiếu
NCBI_EMAIL, lỗi mạng) — không bao giờ đọc «không đo được» thành «đạt».
Chỉ ĐO và BÁO; không sửa engine, không đổi chuẩn vàng (danh sách do bác sĩ duyệt).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

GOC = Path(__file__).resolve().parents[1]
if str(GOC) not in sys.path:
    sys.path.insert(0, str(GOC))

TEP_CHUAN = GOC / "config" / "chuan_vang_guideline.json"


def cham(chuan: dict, tim) -> dict:
    """Chấm một chuẩn vàng bằng hàm `tim(truy_van, n) -> list[pmid]`. Không gọi mạng trực tiếp
    (tiêm `tim` để test ngoại tuyến được). Lỗi của `tim` ⇒ chủ đề đó «khong_do_duoc»."""
    n = int(chuan.get("top_n") or 10)
    kq = {"top_n": n, "chu_de": [], "dat": 0, "truot": 0, "khong_do_duoc": 0}
    for cd in chuan.get("chu_de") or []:
        muc = {"chu_de": cd["chu_de"], "truy_van": cd["truy_van"], "nhom": []}
        try:
            pmids = [str(p) for p in (tim(cd["truy_van"], n) or [])][:n]
        except Exception as exc:  # noqa: BLE001 — lỗi mạng/engine: KHÔNG đo được, không phải «trượt»
            muc["loi"] = f"{type(exc).__name__}: {exc}"
            kq["khong_do_duoc"] += len(cd.get("nhom") or [])
            kq["chu_de"].append(muc)
            continue
        for nh in cd.get("nhom") or []:
            vi_tri = next((i + 1 for i, p in enumerate(pmids) if p in {str(x) for x in nh["pmid"]}), None)
            muc["nhom"].append({"ten": nh["ten"], "vi_tri": vi_tri,
                                "bac_si_duyet": nh.get("bac_si_duyet")})
            kq["dat" if vi_tri else "truot"] += 1
        kq["chu_de"].append(muc)
    return kq


def _tim_that(truy_van: str, n: int):
    from app.config import settings
    from app.sources.pubmed import PubMedClient
    c = PubMedClient()
    if c.use_mock or not settings.ncbi_email:
        raise RuntimeError("engine đang MOCK hoặc thiếu NCBI_EMAIL — không đo được")
    truoc = dict(c.http.health_snapshot())
    ban_ghi = c.search(truy_van, max_results=n)   # search() nuốt lỗi mạng thành [] — phải soi bộ đếm
    sau = dict(c.http.health_snapshot())
    if sau.get("failure_count", 0) > truoc.get("failure_count", 0):
        raise RuntimeError(f"PubMed lỗi: {sau.get('last_error') or 'HTTP thất bại'}")
    return [r.pmid for r in ban_ghi]


def in_bao_cao(kq: dict) -> None:
    for cd in kq["chu_de"]:
        print(f"\n## {cd['chu_de']}  («{cd['truy_van']}», top {kq['top_n']})")
        if cd.get("loi"):
            print(f"   ⚪ KHÔNG ĐO ĐƯỢC — {cd['loi']}")
            continue
        for nh in cd["nhom"]:
            duyet = "" if nh["bac_si_duyet"] else "  [chưa bác sĩ duyệt]"
            dau = f"🟢 hạng {nh['vi_tri']}" if nh["vi_tri"] else "🔴 KHÔNG lọt top"
            print(f"   {dau} — {nh['ten']}{duyet}")
    print(f"\nTổng: {kq['dat']} đạt · {kq['truot']} trượt · {kq['khong_do_duoc']} không đo được")
    if any(not nh["bac_si_duyet"] for cd in kq["chu_de"] for nh in cd.get("nhom", [])):
        print("Lưu ý: chuẩn vàng CHƯA được bác sĩ duyệt hết — kết quả là máy tự chấm theo danh sách máy soạn.")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json", action="store_true", help="in kết quả dạng JSON")
    ap.add_argument("--tep", default=str(TEP_CHUAN))
    a = ap.parse_args()
    chuan = json.loads(Path(a.tep).read_text(encoding="utf-8"))
    kq = cham(chuan, _tim_that)
    if a.json:
        print(json.dumps(kq, ensure_ascii=False, indent=2))
    else:
        in_bao_cao(kq)
    if kq["khong_do_duoc"] and not kq["dat"] and not kq["truot"]:
        return 2
    return 1 if (kq["truot"] or kq["khong_do_duoc"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
