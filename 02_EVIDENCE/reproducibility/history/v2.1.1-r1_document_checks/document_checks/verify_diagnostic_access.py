"""Independently verify a compact diagnostic table and the 21-transition claim.

Acceptance conditions fixed before execution: preserve all input bytes, fixed
populations and model predictions; independently reconstruct population moments
from paired rows; require errors <=1e-10 K/K² against retained diagnostics;
include all ten historical hours and both populated reference-VZA strata;
preserve unfavorable values and disclose noncausal/conditional interpretations.
This script neither fits models nor modifies Word or the release candidate.
"""
from pathlib import Path
import csv,hashlib,json,sys
import numpy as np,pandas as pd

ROOT=Path('/Users/apple/Downloads/RS revision 1/continuation_20261029/release/downstream-measurand-aware-lst-harmonization-2.1.0-r1')
E=ROOT/'02_EVIDENCE'
OUT=Path(__file__).resolve().parent
checks=[];sources={}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def source(rel):
 p=E/rel;sources[str(p)]=sha(p);return p
def ck(name,value,expected):
 err=float(abs(value-expected));ok=err<=1e-10
 checks.append(dict(check=name,value=float(value),expected=float(expected),absolute_error=err,passed=ok));assert ok,(name,value,expected)
def budget(f):
 # This implementation does not import the production decomposition function.
 a=np.asarray(f.source_core-f.target_core,float);b=np.asarray(f.source_ring-f.target_ring,float)
 c=np.asarray(f.pred_core-f.target_core,float);d=np.asarray(f.pred_ring-f.target_ring,float)
 mean=lambda x:float(np.mean(x));var=lambda x:mean((x-mean(x))**2)
 cov=lambda x,y:mean((x-mean(x))*(y-mean(y)))
 vg=var(a)+var(b)-var(c)-var(d)
 bg=(mean(a)-mean(b))**2-(mean(c)-mean(d))**2
 penalty=2*(cov(a,b)-cov(c,d))
 raw=mean((a-b)**2);cor=mean((c-d)**2)
 ck('Budget closure',vg+bg-penalty,raw-cor)
 return dict(n=len(f),cities=f.uc_id.nunique(),intervals=f.event_time_id.nunique(),
  raw_contrast_rmse_K=np.sqrt(raw),corrected_contrast_rmse_K=np.sqrt(cor),
  variance_gain_K2=vg,bias_gain_K2=bg,covariance_penalty_K2=penalty,
  gross_gain_K2=vg+bg,net_MSE_gain_K2=raw-cor,
  raw_covariance_K2=cov(a,b),corrected_covariance_K2=cov(c,d))

hist=pd.read_parquet(source('analysis_outputs/goes17_goes16_external_metric/validation_2021_hourly_predictions.parquet'))
modern=pd.read_parquet(source('analysis_outputs/goes18_goes19_metric_harmonization/validation_2026_hourly_predictions.parquet'))
assert len(hist)==2602 and len(modern)==5716
hours=pd.read_csv(source('diagnostics/repaired_hour_diagnostics.csv'))
geo=pd.read_csv(source('diagnostics/SI_S14_all_geometry_strata.csv'))
pool=pd.read_csv(source('tables/exact_mse_budgets_with_external.csv'))
h=pool[pool['sample'].eq('2021 external GOES17/16')&pool.scope.eq('hourly')].iloc[0]
bp=budget(hist)
for k,v in [('n','n'),('cities','n_cities'),('intervals','n_events'),('variance_gain_K2','component_variance_gain_k2'),('bias_gain_K2','differential_bias_gain_k2'),('covariance_penalty_K2','covariance_loss_penalty_k2'),('net_MSE_gain_K2','net_downstream_mse_gain_k2'),('raw_contrast_rmse_K','raw_anomaly_rmse_k'),('corrected_contrast_rmse_K','harm_anomaly_rmse_k')]:ck('2021 pooled '+k,bp[k],h[v])
raw_rows=[dict(label='2021 pooled',**bp)]
for hour,f in hist.groupby('target_hour_from_sunset'):
 b=budget(f);z=hours[hours.year.eq(2021)&hours.hour.eq(hour)].iloc[0]
 for k in ['n','cities','intervals','raw_contrast_rmse_K','corrected_contrast_rmse_K','variance_gain_K2','bias_gain_K2','covariance_penalty_K2','net_MSE_gain_K2','raw_covariance_K2','corrected_covariance_K2']:ck('2021 h='+str(hour)+' '+k,b[k],z[k])
 ck('2021 hour variance invariance '+str(hour),b['variance_gain_K2'],0.)
 ck('2021 hour covariance invariance '+str(hour),b['covariance_penalty_K2'],0.)
 raw_rows.append(dict(label='2021 h='+('+' if hour>0 else '')+str(hour),**b))
for lo,hi in [(40,50),(50,60)]:
 f=modern[modern.vza_target.ge(lo)&modern.vza_target.lt(hi)]
 b=budget(f);z=geo[geo.stratum.eq('Reference ['+str(lo)+', '+str(hi)+')')].iloc[0]
 for k in ['n','cities','intervals','raw_contrast_rmse_K','corrected_contrast_rmse_K','variance_gain_K2','bias_gain_K2','covariance_penalty_K2','net_MSE_gain_K2']:ck('2026 VZA '+str(lo)+' '+k,b[k],z[k])
 raw_rows.append(dict(label='2026 G18 VZA ['+str(lo)+', '+str(hi)+')°',**b))
assert len(raw_rows)==13

# Reconstruct pre/post means from the hourly common-support values. No
# production transition helper or stored transition error is used.
quality=pd.read_csv(source('quality/full_mse_decompositions.csv'))
transition_rows=[]
for scenario in ['recommended_common_daily','strict_common_daily']:
 f=pd.read_parquet(source('quality/'+scenario+'_hourly.parquet'))
 assert len(f)==215 and f.uc_id.nunique()==3
 vals=[]
 for (city,ev),g in f.groupby(['uc_id','event_time_id']):
  pre=g[g.target_hour_from_sunset.isin([-3,-2,-1])]
  post=g[g.target_hour_from_sunset.isin([4,5,6])]
  if len(pre)<2 or len(post)<2:continue
  row=dict(uc_id=city,event_time_id=ev)
  for col in ['source_core','source_ring','target_core','target_ring','pred_core','pred_ring']:
   row[col]=post[col].mean()-pre[col].mean()
  vals.append(row)
 b=budget(pd.DataFrame(vals));z=quality[quality.scenario.eq(scenario)&quality.level.eq('transition')].iloc[0]
 for k in ['n','cities','raw_contrast_rmse_K','corrected_contrast_rmse_K']:ck('21-transition '+scenario+' '+k,b[k],z[k])
 assert b['n']==21 and b['cities']==3 and b['corrected_contrast_rmse_K']>b['raw_contrast_rmse_K']
 transition_rows.append(dict(scenario=scenario,**b))

def fmt(v,d=4):
 if abs(v)<5*10**(-d-1):v=0.
 return f'{v:.{d}f}'.replace('-','−')
rows=[]
for z in raw_rows:
 rows.append([z['label'],f"{z['n']:,} / {z['cities']}",fmt(z['raw_contrast_rmse_K'],3)+' / '+fmt(z['corrected_contrast_rmse_K'],3),fmt(z['gross_gain_K2']),fmt(z['covariance_penalty_K2']),fmt(z['net_MSE_gain_K2'])])
caption=('Table S5. Principal hourly contrast diagnostics on unchanged paired support. '
 'n counts city–interval–hour means; the next count is cities. The 2021 rows use four intervals and fixed hour offsets; the 2026 rows use eight intervals and the unchanged component models. '
 'G18 VZA is the GOES-18 reference view-zenith angle; bins are lower-inclusive and upper-exclusive. '
 'Gross gain is component-variance plus differential-bias gain; net gain = gross gain − covariance-loss penalty (all K²). '
 'Positive net gain favors component correction. Rounding accounts for small closure differences. '
 'Hour-specific centered covariance is unchanged by the 2021 additive shifts, while pooled covariance also contains between-hour variation. '
 'VZA groups contain different cities and do not isolate angular causes.')
proposal=dict(caption=caption,headers=['Stratum','n / cities','Contrast RMSE, raw / corrected (K)','Gross gain (K²)','Covariance penalty (K²)','Net gain (K²)'],rows=rows,widths=[2350,1050,2200,1100,1200,1100])
(OUT/'diagnostic_table_S5.json').write_text(json.dumps(proposal,indent=2,ensure_ascii=False)+'\n')
(OUT/'diagnostic_table_S5_numeric.json').write_text(json.dumps(raw_rows,indent=2,ensure_ascii=False)+'\n')
(OUT/'transition_quality_values.json').write_text(json.dumps(transition_rows,indent=2,ensure_ascii=False)+'\n')
for p,h in sources.items():assert sha(Path(p))==h
out=dict(status='PASS',command=[sys.executable,str(Path(__file__).resolve())],acceptance_tolerance=1e-10,
 checks=checks,check_count=len(checks),max_absolute_difference=max(x['absolute_error'] for x in checks),sources=sources,
 limitations=['No source retrieval, model fitting or new uncertainty run.',
 'Values independently reconstructed from retained corrected prediction/common-support rows.',
 'Proposed13rowtable includes all10historicalhourbins and both populated referenceVZA bins, not all modernhour/sourceVZA diagnostics.',
 'Strata share source cities/intervals; they are not independent experiments or physical interventions.'])
(OUT/'diagnostic_access_verification.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n')
print(json.dumps({k:v for k,v in out.items() if k not in ['checks','sources']},indent=2))
