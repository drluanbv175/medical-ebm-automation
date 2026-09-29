#!/usr/bin/env python3
"""Quét giám sát chứng cứ + an toàn thuốc ở chế độ CHỈ BÁO CÁO (29/09/2026, bác sĩ chọn).

Vì sao: giám sát tuần (`scripts/weekly_safety.sh`) chỉ chạy qua launchd trên MacBook — Mac tắt/ngủ
là bỏ lượt. Phiên Cloud lấy được nguồn thật (canary 29/09: 4/4 nguồn + scanner PASS) nên có thể
chạy THÊM một lượt ở nơi khác, nhưng KHÔNG được thành owner thứ hai: watermark, DB, sổ cái Hub và
cảnh báo vẫn thuộc riêng lượt trên Mac.

Công cụ này vì vậy:
- trỏ DB + mọi thư mục dữ liệu (`settings.data_dir`) sang thư mục TẠM ⇒ không đụng
  `data/medical_ebm.db`, watermark, bộ đếm hạn mức của máy đang chạy;
- tắt cứng hai tầng dự phòng TÍNH PHÍ (Consensus, SerpApi) cho lượt này;
- KHÔNG gọi gửi cảnh báo (email/webhook), KHÔNG nối Hub, KHÔNG dựng Antifacts, KHÔNG ghi sổ lượt
  giám sát (`record_evidence_surveillance_run`);
- chép các báo cáo Markdown sinh ra vào `--out` kèm TOM-TAT.md + tom_tat.json nêu rõ trạng thái
  nguồn (PASS/PARTIAL/FAIL) và nhãn «chỉ báo cáo — ứng viên, cần bác sĩ duyệt».

Mã thoát: 0 = nguồn PASS · 2 = PARTIAL/FAIL (vẫn ghi báo cáo, có dải cảnh báo) · 3 = tham số sai.
Không tự áp dụng lâm sàng, không dùng dữ liệu bệnh nhân. Cần bác sĩ kiểm chứng.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, Optional

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

NHAN = "CHỈ BÁO CÁO — không phải lượt giám sát chính thức"
DISCLAIMER = ("Cần bác sĩ kiểm chứng. Đây là danh sách ỨNG VIÊN do máy quét, chưa thẩm định; "
              "không tự áp dụng lâm sàng; watermark/sổ cái/cảnh báo của lượt chính thức trên Mac KHÔNG đổi.")
# Tên cố định trong --out ⇐ khoá báo cáo của lượt quét.
TEN_BAO_CAO = {
    "alert_digest_md": "ban-tin-moi.md",
    "weekly_md": "ebm-tuan.md",
    "drug_safety_md": "an-toan-thuoc.md",
    "antibiotic_md": "khang-sinh.md",
}


def _mac_dinh_chay_pipeline(max_per_query: int, ngay: int) -> Dict[str, object]:
    from app.services.pipeline import run_pipeline
    return run_pipeline(max_results_per_query=max_per_query, incremental=True,
                        window_days=ngay, strict_source_health=True)


def _mac_dinh_xuat(ngay: int) -> Dict[str, Path]:
    from app.reports import export_antibiotic_report, export_drug_safety_report
    from app.reports.alert_digest import export_alert_digest
    from app.reports.weekly_ebm import export_weekly_ebm_markdown
    return {
        "alert_digest_md": Path(export_alert_digest(days=ngay)["markdown"]),
        "weekly_md": Path(export_weekly_ebm_markdown()),
        "drug_safety_md": Path(export_drug_safety_report()["markdown"]),
        "antibiotic_md": Path(export_antibiotic_report()["markdown"]),
    }


def _nam_trong(con: Path, cha: Path) -> bool:
    try:
        con.resolve().relative_to(cha.resolve())
        return True
    except ValueError:
        return False


def chay_bao_cao_chi_doc(out_dir: Path, ngay: int = 10, max_per_query: int = 8, *,
                         bo_bao_cao: tuple = (),
                         _chay_pipeline: Optional[Callable[[int, int], Dict[str, object]]] = None,
                         _xuat: Optional[Callable[[int], Dict[str, Path]]] = None) -> Dict[str, object]:
    """Chạy một lượt quét cô lập rồi ghi báo cáo vào `out_dir`. Trả tóm tắt (cũng ghi ra tom_tat.json).

    `bo_bao_cao`: khoá trong TEN_BAO_CAO cố ý KHÔNG chép (vd `weekly_md` ≈2 MB mà Routine Cloud không commit) —
    ghi ở `bo_co_y`, không lẫn vào `thieu_bao_cao` (thiếu thật)."""
    from app import database
    from app.config import settings, use_mock_sources_override_lock

    if _nam_trong(out_dir, settings.data_dir):
        raise ValueError(f"--out không được nằm trong thư mục dữ liệu thật ({settings.data_dir}).")
    chay = _chay_pipeline or _mac_dinh_chay_pipeline
    xuat = _xuat or _mac_dinh_xuat
    tam = Path(tempfile.mkdtemp(prefix="giam-sat-chi-doc-"))
    cu = {k: getattr(settings, k) for k in
          ("data_dir", "database_url", "use_mock_sources", "enable_consensus", "enable_serpapi_scholar")}
    cu_engine, cu_session = database._engine, database._SessionLocal
    try:
        with use_mock_sources_override_lock:
            settings.data_dir = tam / "data"
            settings.database_url = f"sqlite:///{(tam / 'giam_sat.db').as_posix()}"
            settings.use_mock_sources = False
            settings.enable_consensus = False
            settings.enable_serpapi_scholar = False
            database._engine, database._SessionLocal = None, None
            settings.ensure_dirs()
            database.init_db()
            stats = chay(max_per_query, ngay)
            bao_cao = xuat(ngay)
    finally:
        for k, v in cu.items():
            setattr(settings, k, v)
        if database._engine is not None and database._engine is not cu_engine:
            database._engine.dispose()
        database._engine, database._SessionLocal = cu_engine, cu_session

    out_dir.mkdir(parents=True, exist_ok=True)
    da_chep = {}
    for khoa, ten in TEN_BAO_CAO.items():
        if khoa in bo_bao_cao:
            continue
        nguon = bao_cao.get(khoa)
        if nguon and Path(nguon).is_file():
            shutil.copyfile(nguon, out_dir / ten)
            da_chep[khoa] = ten
    shutil.rmtree(tam, ignore_errors=True)

    sh = dict(stats.get("source_health") or {})
    trang_thai = str(sh.get("status") or "FAIL")
    tom_tat = {
        "nhan": NHAN,
        "thoi_diem_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "cua_so_ngay": ngay,
        "trang_thai_nguon": trang_thai,
        "ly_do_that_bai": list(sh.get("hard_fail_reasons") or []),
        "canh_bao_nguon": list(sh.get("warnings") or []),
        "nguon_bat_buoc_suy_giam": list(sh.get("degraded_required_sources") or []),
        "so_ban_ghi": sh.get("total_records"),
        "muc_moi": stats.get("new_items"),
        "bao_cao": da_chep,
        "thieu_bao_cao": sorted(set(TEN_BAO_CAO) - set(da_chep) - set(bo_bao_cao)),
        "bo_co_y": sorted(set(bo_bao_cao) & set(TEN_BAO_CAO)),
        "da_goi_canh_bao": False,
        "da_noi_hub": False,
        "watermark_chinh_thuc_doi": False,
        "tang_du_phong_tinh_phi": "tắt cứng",
        "disclaimer": DISCLAIMER,
    }
    (out_dir / "tom_tat.json").write_text(json.dumps(tom_tat, ensure_ascii=False, indent=2),
                                          encoding="utf-8", newline="\n")
    (out_dir / "TOM-TAT.md").write_text(_markdown(tom_tat), encoding="utf-8", newline="\n")
    return tom_tat


def _markdown(t: Dict[str, object]) -> str:
    dong = [f"# Giám sát chứng cứ — {NHAN}", "",
            f"- Thời điểm (UTC): {t['thoi_diem_utc']} · cửa sổ nhìn lùi: {t['cua_so_ngay']} ngày",
            f"- **Trạng thái nguồn: {t['trang_thai_nguon']}** · số bản ghi: {t['so_ban_ghi']}"
            f" · mục mới: {t['muc_moi']}"]
    if t["trang_thai_nguon"] != "PASS":
        dong += ["", "> ⚠ Lượt quét KHÔNG đầy đủ nguồn — danh sách dưới đây có thể thiếu; KHÔNG đọc thành "
                 "«không có chứng cứ mới»."]
        for k in ("ly_do_that_bai", "nguon_bat_buoc_suy_giam", "canh_bao_nguon"):
            if t[k]:
                dong.append(f"- {k}: {', '.join(map(str, t[k]))}")
    dong += ["", "## Báo cáo kèm theo", ""]
    dong += [f"- `{ten}`" for ten in dict(t["bao_cao"]).values()] or ["- (không sinh được báo cáo nào)"]
    if t["thieu_bao_cao"]:
        dong.append(f"- Thiếu: {', '.join(t['thieu_bao_cao'])}")
    if t.get("bo_co_y"):
        dong.append(f"- Cố ý không kèm: {', '.join(TEN_BAO_CAO[k] for k in t['bo_co_y'])}")
    dong += ["", "## Ranh giới", "",
             "- Không gửi email/webhook · không nối Hub EBM_MASTER · không dựng Antifacts · "
             "không ghi sổ lượt giám sát.",
             "- DB/watermark dùng thư mục tạm, đã xoá sau lượt chạy; "
             "tầng dự phòng tính phí (Consensus, SerpApi) tắt cứng.",
             "", DISCLAIMER, ""]
    return "\n".join(dong)


def main(argv: Optional[list] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", required=True, help="Thư mục ghi báo cáo (không nằm trong data/).")
    ap.add_argument("--ngay", type=int, default=10, help="Cửa sổ nhìn lùi (ngày), mặc định 10.")
    ap.add_argument("--max-per-query", type=int, default=8)
    ap.add_argument("--bo-ebm-tuan", action="store_true",
                    help="Không chép ebm-tuan.md (≈2 MB) — dùng cho Routine Cloud commit báo cáo vào git.")
    a = ap.parse_args(argv)
    if a.ngay < 1 or a.max_per_query < 1:
        print("--ngay và --max-per-query phải ≥ 1", file=sys.stderr)
        return 3
    try:
        t = chay_bao_cao_chi_doc(Path(a.out), a.ngay, a.max_per_query,
                                 bo_bao_cao=("weekly_md",) if a.bo_ebm_tuan else ())
    except ValueError as exc:
        print(f"Từ chối: {exc}", file=sys.stderr)
        return 3
    print(json.dumps(t, ensure_ascii=False, indent=2))
    return 0 if t["trang_thai_nguon"] == "PASS" else 2


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
