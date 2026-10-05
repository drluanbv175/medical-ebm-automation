#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CHỐT KHOÁ DỮ LIỆU TRƯỚC KHI CHẠY PHÂN TÍCH — dùng chung cho script R (00_setup.R gọi qua system2) và mọi caller.

VÌ SAO CÓ (soát từng cổng G6, 04/10/2026 — G6-02): bốn khuôn Python CLI của run_g6_auto đã tự chặn (sổ cái + chất
lượng G2/G4/G5, checksum dataset khoá — gate_contract.locked_analysis_dataset_blockers), nhưng ĐƯỜNG R (00–03 .R) —
chính là đường phân tích CHÍNH đúng SAP cho cắt ngang/chẩn đoán/tiên lượng/tổng quan/kết cục liên tục — không có chốt
nào: đọc data/raw chung của repo, làm sạch lại, chạy được khi G4/G5 chưa ký. Công cụ này gói ĐÚNG hợp đồng mà khuôn
Python dùng để R gọi được, không viết lại logic.

Điều kiện được chạy (cả bốn):
  1. G2 (IRB): chữ ký sổ cái khớp gói đạo đức hiện tại VÀ hợp đồng chất lượng G2 đạt.
  2. G4 (SAP): chữ ký sổ cái khớp SAP hiện tại VÀ G4 chấm trực tiếp là PASS_G4_SAP_LOCKED.
  3. G5 (khoá dữ liệu): chữ ký sổ cái khớp G5_checkpoint hiện tại VÀ G5 chấm trực tiếp là PASS_G5_DATA_LOCKED.
  4. Dataset dùng để phân tích là ĐÚNG tệp khoá trong DATA_LOCK_manifest và khớp sha256.

Dùng:  python3 tools/kiem_khoa_phan_tich.py --study <mã> [--data <csv>] [--repo-root <gốc>]
Mã thoát: 0 = được chạy (hai dòng cuối: «LOCKED_DATA=<đường dẫn tuyệt đối>», «SHA256=<…>»); 3 = chặn (in lý do).
Chỉ đọc — không ghi gì.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional, Tuple

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

BASE = Path(__file__).resolve().parents[1]
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

import gate_contract as GC  # noqa: E402

MA_CHAN = 3


def _doc_json(path: Path) -> dict:
    try:
        du_lieu = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return du_lieu if isinstance(du_lieu, dict) else {}


def kiem(study: str, data: Optional[str] = None,
         repo_root: Optional[Path] = None) -> Tuple[list, Optional[Path], Optional[str]]:
    """(lý do chặn, đường dẫn dataset khoá, sha256) — lý do rỗng nghĩa là được chạy phân tích."""
    root = Path(repo_root) if repo_root else BASE
    out = root / "exports" / study
    ly_do: list = []
    if not out.is_dir():
        return [f"khong_co_thu_muc_de_tai:{out}"], None, None
    meta = GC.load_study_meta(out)

    if not GC.ledger_approved("G2", study, out / f"G2_A3_ETHICS_PACKAGE_{study}.md", repo_root=root):
        ly_do.append("G2_chua_co_chu_ky_hop_le (IRB)")
    elif not GC.g2_quality_contract_satisfied(_doc_json(out / "G2_checkpoint.json"), meta, study=study, out_dir=out):
        ly_do.append("G2_hop_dong_chat_luong_chua_dat")
    if not GC.ledger_approved("G4", study, out / f"G4_A5_SAP_FINAL_{study}.md", repo_root=root):
        ly_do.append("G4_chua_co_chu_ky_hop_le (SAP)")
    elif not GC.g4_quality_contract_satisfied(study, repo_root=root):
        ly_do.append("G4_chua_PASS_G4_SAP_LOCKED")
    if not GC.ledger_approved("G5", study, out / "G5_checkpoint.json", repo_root=root):
        ly_do.append("G5_chua_co_chu_ky_hop_le (khoá dữ liệu)")
    elif not GC.g5_quality_contract_satisfied(study, repo_root=root):
        ly_do.append("G5_chua_PASS_G5_DATA_LOCKED")

    # Dataset: mặc định là tệp khoá do manifest chỉ định (tôn trọng override real_data_lock.manifest của study_meta).
    _, manifest = GC.locked_analysis_dataset_blockers(study, "", repo_root=root)
    tep_khoa = out / manifest["locked_dataset_path"] if manifest.get("locked_dataset_path") else None
    du_lieu = data or (str(tep_khoa) if tep_khoa else "")
    chan_du_lieu, manifest = GC.locked_analysis_dataset_blockers(study, du_lieu, repo_root=root)
    ly_do.extend(chan_du_lieu)
    return ly_do, (tep_khoa.resolve() if tep_khoa and tep_khoa.exists() else None), manifest.get("sha256")


def main() -> int:
    ap = argparse.ArgumentParser(description="Chốt khoá dữ liệu trước khi chạy phân tích (G2/G4/G5 + checksum).")
    ap.add_argument("--study", required=True, help="Mã đề tài (thư mục exports/<mã>)")
    ap.add_argument("--data", default=None, help="Tệp dữ liệu định phân tích (mặc định: tệp khoá trong manifest)")
    ap.add_argument("--repo-root", default=None, help="Gốc repo (mặc định: thư mục cha của tools/)")
    a = ap.parse_args()
    ly_do, tep, sha = kiem(a.study, a.data, Path(a.repo_root) if a.repo_root else None)
    if ly_do:
        print(f"✗ DỪNG — đề tài {a.study} CHƯA được phép chạy phân tích xác nhận:")
        for x in ly_do:
            print(f"   - {x}")
        print("   Ký/khoá thật bằng tools/approve_gate.py (G2, G4, G5) và tools/lock_analysis_dataset.py — agent không "
              "ký hộ. Cần bác sĩ kiểm chứng.")
        return MA_CHAN
    print("✓ DATA LOCK: G2/G4/G5 đã ký hợp lệ; dataset khớp checksum bản khoá.")
    print(f"LOCKED_DATA={tep}")
    print(f"SHA256={sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
