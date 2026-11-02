"""Expand the compact table with every modern hour, preserving the13row option.

Fixed acceptance: all ten 2026 bins, same population moments and predictions;
all compared values agree within1e-10; unfavorable rows remain; source files
and the original13row proposal remain byte-unchanged. No model fit/raw retrieval.
"""
from pathlib import Path
import hashlib,json,sys
import numpy as np,pandas as pd

ROOT=Path('/Users/apple/Downloads/RS revision 1/continuation_20261029/release/downstream-measurand-aware-lst-harmonization-2.1.0-r1')
E=ROOT/'02_EVIDENCE';O=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
protected={str(p):sha(p) for p in [O/'diagnostic_table_S5.json',O/'diagnostic_table_S5_numeric.json']}
sources={}
def inp(rel):
 p=E/rel;sources[str(p)]=sha(p);return p
f=pd.read_parquet(inp('analysis_outputs/goes18_goes19_metric_harmonization/validation_2026_hourly_predictions.parquet'))
expected=pd.read_csv(inp('diagnostics/repaired_hour_diagnostics.csv'))
checks=[];modern=[]
def ck(label,a,b):
 diff=float(abs(a-b));passed=diff<=1e-10
 checks.append(dict(check=label,value=float(a),expected=float(b),absolute_difference=diff,passed=passed));assert passed,(label,a,b)
for hour,g in f.groupby('target_hour_from_sunset'):
 a=np.asarray(g.source_core-g.target_core,float);b=np.asarray(g.source_ring-g.target_ring,float)
 c=np.asarray(g.pred_core-g.target_core,float);d=np.asarray(g.pred_ring-g.target_ring,float)
 mean=lambda x:float(np.mean(x));var=lambda x:mean((x-mean(x))**2)
 cov=lambda x,y:mean((x-mean(x))*(y-mean(y)))
 vg=var(a)+var(b)-var(c)-var(d)
 bg=(mean(a)-mean(b))**2-(mean(c)-mean(d))**2
 penalty=2*(cov(a,b)-cov(c,d));raw=mean((a-b)**2);corr=mean((c-d)**2)
 z=dict(label='2026 h='+('+' if hour>0 else '')+str(hour),n=len(g),cities=g.uc_id.nunique(),intervals=g.event_time_id.nunique(),
  raw_contrast_rmse_K=np.sqrt(raw),corrected_contrast_rmse_K=np.sqrt(corr),variance_gain_K2=vg,bias_gain_K2=bg,
  covariance_penalty_K2=penalty,gross_gain_K2=vg+bg,net_MSE_gain_K2=raw-corr,
  raw_covariance_K2=cov(a,b),corrected_covariance_K2=cov(c,d))
 er=expected[expected.year.eq(2026)&expected.hour.eq(hour)].iloc[0]
 for col in ['n','cities','intervals','raw_contrast_rmse_K','corrected_contrast_rmse_K','variance_gain_K2','bias_gain_K2','covariance_penalty_K2','net_MSE_gain_K2','raw_covariance_K2','corrected_covariance_K2']:ck(z['label']+' '+col,z[col],er[col])
 ck(z['label']+' closure',vg+bg-penalty,raw-corr)
 modern.append(z)
assert len(modern)==10 and sum(z['n'] for z in modern)==5716
assert sum(z['net_MSE_gain_K2']<0 for z in modern)==8
old=json.loads((O/'diagnostic_table_S5_numeric.json').read_text());new=old[:11]+modern+old[11:]
assert len(new)==23
def fmt(v,d=4):
 if abs(v)<5*10**(-d-1):v=0.
 return f'{v:.{d}f}'.replace('-','−')
rows=[[z['label'],f"{z['n']:,} / {z['cities']}",fmt(z['raw_contrast_rmse_K'],3)+' / '+fmt(z['corrected_contrast_rmse_K'],3),fmt(z['gross_gain_K2']),fmt(z['covariance_penalty_K2']),fmt(z['net_MSE_gain_K2'])] for z in new]
proposal=json.loads((O/'diagnostic_table_S5.json').read_text());proposal['rows']=rows
proposal['caption']=('Table S5. Hourly contrast diagnostics on unchanged paired support. '
 'n counts city–interval–hour means; the next count is cities. '
 'The 2021 pool and ten hours use four intervals and fixed hour offsets; the ten 2026 hours and two VZA groups use eight intervals and unchanged component models. '
 'G18 VZA is the GOES-18 reference view-zenith angle; bins are lower-inclusive and upper-exclusive. '
 'Gross gain = component-variance + differential-bias gain; net gain = gross gain − covariance-loss penalty (K²); positive net gain favors correction. '
 'Rounding can affect closure. Fixed 2021 hour offsets preserve centered within-hour covariance; pooled covariance also includes between-hour variation. '
 'VZA groups contain different cities and do not isolate angular causes.')
(O/'diagnostic_table_S5_all_hours.json').write_text(json.dumps(proposal,indent=2,ensure_ascii=False)+'\n')
(O/'diagnostic_table_S5_all_hours_numeric.json').write_text(json.dumps(new,indent=2,ensure_ascii=False)+'\n')
for p,h in {**sources,**protected}.items():assert sha(Path(p))==h
out=dict(status='PASS',command=[sys.executable,str(Path(__file__).resolve())],checks=checks,check_count=len(checks),
 max_absolute_difference=max(z['absolute_difference'] for z in checks),fixed_tolerance=1e-10,
 expanded_rows=23,new_modern_hour_rows=10,unfavorable_modern_hours=8,modern_hour_n_sum=5716,
 sources=sources,original13row_proposal_unchanged=protected,
 scope='Independent scalar reconstruction from retained2026predictionrows; no fitting, raw retrieval or scientific rerun. The earlier180checkverification supplies unchangedhistoricalpool/hour and referenceVZA rows.')
(O/'diagnostic_access_verification_all_hours.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n')
print(json.dumps({k:v for k,v in out.items() if k not in ['checks','sources','original13row_proposal_unchanged']},indent=2))
