#!/usr/bin/env python3
# sensitivity_analysis.py -- Phan tich do nhay
# De tai: hai-long-benh-nhan-C1a-BVQY175
# Bien  : exposure=exposure_var | outcome=primary_outcome | time=follow_time_months
#
# Noi dung:
#   1. Complete-case vs Multiple Imputation (mean-impute demo)
#   2. Subgroup: sex, dm, htn, age>=70
#   3. E-value (unmeasured confounding)
#
# Cach dung: python sensitivity_analysis.py --data path/to/data.csv
# Yeu cau: pandas, numpy, lifelines, scipy
import argparse, warnings
warnings.filterwarnings('ignore')
import numpy as np
import pandas as pd
try:
    from lifelines import CoxPHFitter
except ImportError:
    raise SystemExit('pip install lifelines')
try:
    from scipy import stats
except ImportError:
    raise SystemExit('pip install scipy')

def evalue_hr(hr, ci_lo):
    """E-value (VanderWeele & Ding 2017). PMID: 28693043"""
    def _ev(r):
        if r < 1.0: r = 1.0/r
        return r + (r*(r-1))**0.5
    return round(_ev(hr),2), round(_ev(max(ci_lo,1e-6)),2)

def fmt_pval(p):
    return '<0.001' if p<0.001 else f'{p:.3f}'

def _check_sap_db_locked(i_confirm_sap, i_confirm_irb=False):
    # Audit 2026-07-11: script nay chay hoi quy Cox THAT tren du lieu CSV THAT
    # (giong het run_analysis_cli.py) nhung truoc day KHONG co cong nao ca -
    # sao chep dung cung co che ledger_approved da co o CLI template chinh.
    # Va 2026-07-12 (audit toan dien): co --i-confirm-* truoc day bo qua CA
    # ledger check -- nay co CHI thay the checkpoint-file, ledger LUON bat buoc.
    import hashlib as _hashlib, json as _json, re as _re, sys as _sys
    from pathlib import Path as _Path
    _sys.path.insert(0, str(_Path(__file__).resolve().parents[3] / 'tools'))
    import gate_contract as _GC
    def _is_locked(status):
        s = str(status or '').strip().upper()
        if _re.search(r'(UN|CH[ƯU]A|KH[ÔO]NG|NOT)\s*LOCKED', s):
            return False
        return bool(_re.match(r'^LOCKED\b', s))
    def _load_cp(gate):
        p = _Path('exports') / 'hai-long-benh-nhan-C1a-BVQY175' / f'{gate}_checkpoint.json'
        if p.exists():
            try:
                return _json.loads(p.read_text(encoding='utf-8'))
            except (ValueError, OSError):
                return {}
        return {}
    g2 = _load_cp('G2'); g4 = _load_cp('G4'); g5 = _load_cp('G5')
    g2_cp = _is_locked(g2.get('g2_status', g2.get('G2_STATUS')))
    g4_cp = _is_locked(g4.get('g4_status', g4.get('G4_STATUS')))
    g5_cp = _is_locked(g5.get('g5_status', g5.get('G5_STATUS')))
    g2_ledger = _GC.ledger_approved(
        "G2", "hai-long-benh-nhan-C1a-BVQY175", _Path('exports') / 'hai-long-benh-nhan-C1a-BVQY175' / 'G2_A3_ETHICS_PACKAGE_hai-long-benh-nhan-C1a-BVQY175.md')
    g4_ledger = _GC.ledger_approved(
        "G4", "hai-long-benh-nhan-C1a-BVQY175", _Path('exports') / 'hai-long-benh-nhan-C1a-BVQY175' / 'G4_A5_SAP_FINAL_hai-long-benh-nhan-C1a-BVQY175.md')
    g5_ledger = _GC.ledger_approved(
        "G5", "hai-long-benh-nhan-C1a-BVQY175", _Path('exports') / 'hai-long-benh-nhan-C1a-BVQY175' / 'G5_checkpoint.json')
    g2_locked = (g2_cp or i_confirm_irb) and g2_ledger
    g4_locked = (g4_cp or i_confirm_sap) and g4_ledger
    g5_locked = (g5_cp or i_confirm_sap) and g5_ledger
    if not g2_locked:
        raise SystemExit('DUNG: G2 (phe duyet dao duc/IRB) chua xac nhan LOCKED bang phe duyet that (chu ky). '
                         '--i-confirm-irb-approved chi thay checkpoint-file, KHONG thay duoc ledger.')
    if not (g4_locked and g5_locked):
        raise SystemExit('DUNG: G4 (SAP) hoac G5 (khoa DB) chua xac nhan LOCKED bang phe duyet that (chu ky). '
                         '--i-confirm-sap-locked chi thay checkpoint-file, KHONG thay duoc ledger.')

def run_cox_sub(df, time_col, outcome, exposure, avail):
    cols = [time_col, outcome, exposure]+avail
    df2  = df[[c for c in cols if c in df.columns]].dropna()
    cph  = CoxPHFitter()
    cph.fit(df2, duration_col=time_col, event_col=outcome)
    s = cph.summary.loc[exposure]
    hr, clo, chi, pv = (s[k] for k in['exp(coef)','exp(coef) lower 95%','exp(coef) upper 95%','p'])
    return hr,clo,chi,pv,len(df2),int(df2[outcome].sum())

def pick_subgroup_covars(sub, outcome, avail, exclude=None):
    # Gioi han covariates theo events-per-variable (EPV>=8) de tranh
    # non-convergence khi co mau con nho hon nhieu so voi mo hinh chinh.
    events = int(sub[outcome].sum())
    max_n  = max(1, events // 8)
    pool   = [c for c in avail if c != exclude]
    return pool[:max_n]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', required=True)
    parser.add_argument('--exposure',   default='exposure_var')
    parser.add_argument('--outcome',    default='primary_outcome')
    parser.add_argument('--time',       default='follow_time_months')
    parser.add_argument('--covariates', default='age,sex,bmi,education,ethnicity,bp_sys,bp_dia,heart_rate,dm,htn,comorbid_other')
    parser.add_argument('--output-dir', default='.')
    parser.add_argument('--i-confirm-sap-locked', action='store_true')
    parser.add_argument('--i-confirm-irb-approved', action='store_true')
    args = parser.parse_args()
    _check_sap_db_locked(args.i_confirm_sap_locked, args.i_confirm_irb_approved)
    exposure   = args.exposure
    outcome    = args.outcome
    time_col   = args.time
    covariates = [c.strip() for c in args.covariates.split(',') if c.strip()]
    out_dir    = __import__('pathlib').Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(args.data, low_memory=False)
    avail = [c for c in covariates if c in df.columns]
    sens_rows = []
    # Complete-case
    try:
        hr,clo,chi,pv,n,ev = run_cox_sub(df,time_col,outcome,exposure,avail)
        sens_rows.append(dict(method='Complete-case',HR=round(hr,3),CI_lo=round(clo,3),CI_hi=round(chi,3),p=round(pv,3),N=n,Events=ev))
        print(f'   CC: HR={hr:.2f} ({clo:.2f}-{chi:.2f}), p={fmt_pval(pv)}')
    except Exception as e:
        print(f'   CC loi: {e}')
    # MI demo
    try:
        cols2 = [time_col,outcome,exposure]+avail
        df2   = df[[c for c in cols2 if c in df.columns]].copy()
        for col in avail:
            if df2[col].isna().any():
                uq = df2[col].dropna().unique()
                fill = df2[col].mode()[0] if set(uq).issubset({0,1,2,3,4,5}) else df2[col].mean()
                df2[col]=df2[col].fillna(fill)
        df2=df2.dropna()
        hr,clo,chi,pv,n,ev = run_cox_sub(df2,time_col,outcome,exposure,avail)
        sens_rows.append(dict(method='MI-demo (mean-impute; R mice m=20 for real)',HR=round(hr,3),CI_lo=round(clo,3),CI_hi=round(chi,3),p=round(pv,3),N=n,Events=ev))
        print(f'   MI: HR={hr:.2f} ({clo:.2f}-{chi:.2f}), p={fmt_pval(pv)}')
    except Exception as e:
        print(f'   MI loi: {e}')
    # Subgroup
    sub_rows = []
    for sg in ['sex','dm','htn']:
        if sg not in df.columns: continue
        for val in sorted(df[sg].dropna().unique()):
            sub = df[df[sg]==val][[c for c in [time_col,outcome,exposure]+avail if c in df.columns]].dropna()
            if len(sub)<20 or sub[outcome].sum()<5: continue
            sub_covars = pick_subgroup_covars(sub, outcome, avail, exclude=sg)
            try:
                hr,clo,chi,pv,n,ev = run_cox_sub(sub,time_col,outcome,exposure,sub_covars)
                sub_rows.append(dict(Subgroup=sg,Value=str(val),HR=round(hr,3),CI_lo=round(clo,3),CI_hi=round(chi,3),p=round(pv,3),N=n,Events=ev,Covars_used=len(sub_covars)))
                print(f'   {sg}={val}: HR={hr:.2f} ({clo:.2f}-{chi:.2f}), p={fmt_pval(pv)} [adj {len(sub_covars)} bien]')
            except Exception as e:
                try:
                    hr,clo,chi,pv,n,ev = run_cox_sub(sub,time_col,outcome,exposure,[])
                    sub_rows.append(dict(Subgroup=sg,Value=str(val),HR=round(hr,3),CI_lo=round(clo,3),CI_hi=round(chi,3),p=round(pv,3),N=n,Events=ev,Covars_used=0))
                    print(f'   {sg}={val}: HR tho={hr:.2f} ({clo:.2f}-{chi:.2f}), p={fmt_pval(pv)} [khong hoi tu voi covariates, dung mo hinh tho]')
                except Exception as e2:
                    print(f'   {sg}={val} loi: {e2}')
    if 'age' in df.columns:
        df['_ag']=df['age'].apply(lambda x:'age>=70' if x>=70 else 'age<70')
        for val in ['age<70','age>=70']:
            sub=df[df['_ag']==val][[c for c in [time_col,outcome,exposure]+avail if c in df.columns]].dropna()
            if len(sub)<20 or sub[outcome].sum()<5: continue
            sub_covars = pick_subgroup_covars(sub, outcome, avail, exclude='age')
            try:
                hr,clo,chi,pv,n,ev=run_cox_sub(sub,time_col,outcome,exposure,sub_covars)
                sub_rows.append(dict(Subgroup='age_group',Value=val,HR=round(hr,3),CI_lo=round(clo,3),CI_hi=round(chi,3),p=round(pv,3),N=n,Events=ev,Covars_used=len(sub_covars)))
            except Exception:
                try:
                    hr,clo,chi,pv,n,ev=run_cox_sub(sub,time_col,outcome,exposure,[])
                    sub_rows.append(dict(Subgroup='age_group',Value=val,HR=round(hr,3),CI_lo=round(clo,3),CI_hi=round(chi,3),p=round(pv,3),N=n,Events=ev,Covars_used=0))
                except Exception: pass
    # E-value
    if sens_rows:
        hr_main=sens_rows[0]['HR']; clo_main=sens_rows[0]['CI_lo']
        ev_pt,ev_ci=evalue_hr(hr_main,clo_main)
        print(f'   E-value: {ev_pt} (CI bound: {ev_ci})')
        print('   PMID: 28693043')
        pd.DataFrame([dict(HR=hr_main,CI_lo=clo_main,E_value_point=ev_pt,E_value_CI=ev_ci)]).to_excel(out_dir/'G6_evalue.xlsx',index=False)
    if sens_rows: pd.DataFrame(sens_rows).to_excel(out_dir/'G6_sensitivity_ccmi.xlsx',index=False)
    if sub_rows:  pd.DataFrame(sub_rows).to_excel(out_dir/'G6_subgroup.xlsx',index=False)
    print('\n⚠️  Can bac si kiem chung. MI that: dung R mice m=20.')

if __name__ == '__main__':
    main()
