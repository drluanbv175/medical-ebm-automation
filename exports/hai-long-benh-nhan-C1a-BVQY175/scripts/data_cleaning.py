#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
data_cleaning.py — Lam sach du lieu REDCap cho de tai: hai-long-benh-nhan-C1a-BVQY175
NANG CAP G5: sinh tu dong tu CRF dictionary (24 bien)
Thiet ke: cross_sectional

CANH BAO: Script nay chi xu ly file CSV cuc bo. KHONG gui du lieu ra ngoai.
Du lieu that chi xu ly tai moi truong bao mat (REDCap co so hoac server noi bo).

Cach dung:
    python data_cleaning.py --input data/raw/redcap_export.csv
"""
import argparse
import pandas as pd
from pathlib import Path
from datetime import datetime

# Danh sach bien theo CRF dictionary (sinh tu dong)
EXPECTED_COLUMNS = ['record_id', 'consent_date', 'site_id', 'visit_date', 'age', 'sex', 'bmi', 'education', 'ethnicity', 'visit_type', 'payment_type', 'wait_time_min', 'visit_freq_year', 'occupation', 'income_self_rated', 'domain_access_score', 'domain_transparency_score', 'domain_facility_score', 'domain_staff_attitude_score', 'domain_service_result_score', 'overall_satisfaction_score', 'overall_satisfaction_binary', 'willing_to_return', 'complete_flag']

# Bien so can ep kieu numeric
NUMERIC_COLS = ['age', 'bmi', 'wait_time_min', 'visit_freq_year', 'domain_access_score', 'domain_transparency_score', 'domain_facility_score', 'domain_staff_attitude_score', 'domain_service_result_score', 'overall_satisfaction_score']

# Bien ngay thang
DATE_COLS = ['consent_date', 'visit_date']

# Bien bat buoc (required)
REQUIRED_COLS = ['record_id', 'consent_date', 'site_id', 'age', 'sex', 'visit_type', 'payment_type', 'domain_access_score', 'domain_transparency_score', 'domain_facility_score', 'domain_staff_attitude_score', 'domain_service_result_score', 'overall_satisfaction_score', 'overall_satisfaction_binary']

# Kiem tra pham vi (var, min, max) — sinh tu dong tu VALIDATION_RULES
RANGE_CHECKS = [
    ('age', 18.0, 120.0),
    ('bmi', 10.0, 60.0),
]


def load_data(csv_path: str) -> pd.DataFrame:
    """Doc REDCap export CSV."""
    df = pd.read_csv(csv_path, dtype=str, encoding="utf-8-sig")
    print(f"[LOAD] {len(df)} dong, {len(df.columns)} cot")
    return df


def check_columns(df: pd.DataFrame) -> None:
    """Kiem tra cot thieu / thua so voi CRF dictionary."""
    missing = [c for c in EXPECTED_COLUMNS if c not in df.columns]
    extra   = [c for c in df.columns if c not in EXPECTED_COLUMNS]
    if missing:
        print(f"[WARN] Cot THIEU so CRF: {missing}")
    if extra:
        print(f"[INFO] Cot THEM khong trong CRF: {extra}")


def coerce_types(df: pd.DataFrame) -> pd.DataFrame:
    """Ep kieu numeric va date."""
    for col in NUMERIC_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in DATE_COLS:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce", format="%Y-%m-%d")
    return df


def check_missing(df: pd.DataFrame) -> pd.Series:
    """Tinh % thieu moi bien; in canh bao neu bien bat buoc thieu > 0."""
    missing_pct = (df.isnull().sum() / len(df) * 100).round(1)
    for varname in REQUIRED_COLS:
        if varname in df.columns and missing_pct.get(varname, 0) > 0:
            pct_val = missing_pct[varname]
            print(f"[WARN] Bien bat buoc '{varname}' thieu {pct_val:.1f}%")
    return missing_pct


def range_validation(df: pd.DataFrame) -> pd.DataFrame:
    """Gan co cac gia tri ngoai pham vi sinh ly."""
    for varname, lo, hi in RANGE_CHECKS:
        if varname in df.columns:
            flag_col = "flag_" + varname
            col_num = pd.to_numeric(df[varname], errors="coerce")
            df[flag_col] = col_num.notna() & ((col_num < lo) | (col_num > hi))
            n_flag = int(df[flag_col].sum())
            if n_flag > 0:
                print(f"[RANGE] {varname}: {n_flag} gia tri ngoai [{lo}, {hi}]")
    return df


def check_logic(df: pd.DataFrame) -> None:
    """Kiem tra logic ngay (consent <= event <= censor)."""
    date_pairs = [
        ("consent_date", "visit_date"),
    ]
    for d1, d2 in date_pairs:
        if d1 in df.columns and d2 in df.columns:
            bad = df[d2].notna() & df[d1].notna() & (df[d2] < df[d1])
            if bad.sum() > 0:
                print(f"[LOGIC] {d2} truoc {d1}: {bad.sum()} dong")


def check_duplicates(df: pd.DataFrame) -> None:
    """Phat hien record_id trung."""
    if "record_id" in df.columns:
        dups = df["record_id"].duplicated(keep=False)
        if dups.sum() > 0:
            dup_ids = df.loc[dups, "record_id"].unique()
            print(f"[ERROR] record_id TRUNG: {dup_ids}")


def save_clean(df: pd.DataFrame, out_dir: Path) -> None:
    """Luu dataset da lam sach."""
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "df_clean.csv"
    flag_cols = [c for c in df.columns if c.startswith("flag_")]
    df_clean = df.drop(columns=flag_cols, errors="ignore")
    df_clean.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"[SAVE] Dataset lam sach -> {out_path} ({len(df_clean)} dong)")
    if flag_cols:
        flag_path = out_dir / "df_flags.csv"
        df[["record_id"] + flag_cols].to_csv(flag_path, index=False, encoding="utf-8-sig")
        print(f"[SAVE] Co kiem tra -> {flag_path}")


def main():
    parser = argparse.ArgumentParser(description="Lam sach du lieu REDCap — hai-long-benh-nhan-C1a-BVQY175")
    parser.add_argument("--input", required=True, help="Duong dan REDCap export CSV")
    parser.add_argument("--out-dir", default="data/processed",
                        help="Thu muc luu dataset lam sach (mac dinh: data/processed/)")
    args = parser.parse_args()

    print("=== data_cleaning.py — hai-long-benh-nhan-C1a-BVQY175 ===")
    print(f"Thiet ke: cross_sectional | Thoi gian: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("NHAC NHO: Chay tren moi truong bao mat noi bo, KHONG upload du lieu that len cloud.")
    print()

    df = load_data(args.input)
    check_columns(df)
    df = coerce_types(df)
    check_duplicates(df)
    check_missing(df)
    df = range_validation(df)
    check_logic(df)
    save_clean(df, Path(args.out_dir))

    print()
    print("=== HOAN TAT lam sach — Kiem tra canh bao tren va xu ly truoc khi phan tich ===")
    print("Can bac si kiem chung moi gia tri bat thuong duoc gan co.")


if __name__ == "__main__":
    main()
