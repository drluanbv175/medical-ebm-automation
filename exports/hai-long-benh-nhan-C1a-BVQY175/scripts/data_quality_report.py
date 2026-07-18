#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
data_quality_report.py — Bao cao chat luong du lieu cho de tai: hai-long-benh-nhan-C1a-BVQY175
Doc df_clean.csv -> kiem tra N, % complete, vi pham pham vi, trung ID.
Sinh: data_quality_report.txt

CANH BAO: Chi chay tren moi truong bao mat noi bo voi du lieu that.

Cach dung:
    python data_quality_report.py --input data/processed/df_clean.csv
"""
import argparse
import pandas as pd
from pathlib import Path
from datetime import datetime


RANGE_CHECKS = [
    ("age", 18.0, 120.0),
    ("bmi", 10.0, 60.0),
]


def generate_report(df: pd.DataFrame, study_name: str, design: str, out_path: Path) -> None:
    lines = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines += [
        "=" * 60,
        f"BAO CAO CHAT LUONG DU LIEU — {study_name}",
        f"Ngay sinh bao cao: {now}",
        f"Thiet ke: {design}",
        "=" * 60,
        "",
        "TONG QUAN",
        f"  N tong (dong): {len(df)}",
        f"  So bien      : {len(df.columns)}",
        "",
    ]

    if "record_id" in df.columns:
        n_dup = int(df["record_id"].duplicated(keep=False).sum())
        suffix = "  CANH BAO: CAN XU LY" if n_dup > 0 else "  OK"
        lines.append(f"TRUNG record_id: {n_dup} dong{suffix}")
    else:
        lines.append("TRUNG record_id: khong tim thay cot record_id")

    lines.append("")
    lines.append("% DU LIEU DAY DU (Completeness) theo bien:")
    lines.append("  " + "-" * 50)
    missing = (df.isnull().sum() / len(df) * 100).round(1)
    for varname, pct in missing.sort_values(ascending=True).items():
        complete = 100 - pct
        if pct > 30:
            flag_str = "  THIEU NHIEU"
        elif pct > 10:
            flag_str = "  CHU Y"
        else:
            flag_str = ""
        lines.append(f"  {varname:<30} {complete:5.1f}% day du{flag_str}")

    lines.append("")
    lines.append("VI PHAM PHAM VI SINH LY:")
    n_violations = 0
    for varname, lo, hi in RANGE_CHECKS:
        if varname in df.columns:
            col_num = pd.to_numeric(df[varname], errors="coerce")
            n_bad = int(((col_num < lo) | (col_num > hi)).sum())
            if n_bad > 0:
                lines.append(f"  {varname:<30} {n_bad} gia tri ngoai [{lo}, {hi}]  CANH BAO")
                n_violations += n_bad
    if n_violations == 0:
        lines.append("  Khong phat hien vi pham pham vi trong dataset nay.")

    lines += ["", "=" * 60, "KET LUAN:"]
    issues = []
    if "record_id" in df.columns and df["record_id"].duplicated(keep=False).sum() > 0:
        issues.append("Co record_id trung — can xu ly truoc khi phan tich")
    high_missing = missing[missing > 30]
    if not high_missing.empty:
        issues.append(f"{len(high_missing)} bien thieu >30%: {list(high_missing.index)}")
    if n_violations > 0:
        issues.append(f"{n_violations} gia tri vi pham pham vi — can kiem tra lai nguon")
    if issues:
        for idx, issue in enumerate(issues, 1):
            lines.append(f"  {idx}. {issue}")
    else:
        lines.append("  Khong phat hien van de chat luong nghiem trong.")

    lines += [
        "",
        "Can bac si/nha nghien cuu kiem chung bao cao nay.",
        "KHONG dung du lieu khi con van de chua giai quyet.",
        "=" * 60,
    ]
    report_text = "\n".join(lines)
    out_path.write_text(report_text, encoding="utf-8")
    print(report_text)
    print(f"\n-> Da luu bao cao: {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Bao cao chat luong du lieu — hai-long-benh-nhan-C1a-BVQY175")
    parser.add_argument("--input", default="data/processed/df_clean.csv",
                        help="Duong dan df_clean.csv")
    parser.add_argument("--out", default="data/processed/data_quality_report.txt",
                        help="Duong dan luu bao cao txt")
    args = parser.parse_args()

    df = pd.read_csv(args.input, encoding="utf-8-sig")
    generate_report(df, "hai-long-benh-nhan-C1a-BVQY175", "cross_sectional", Path(args.out))


if __name__ == "__main__":
    main()
