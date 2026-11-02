"""Independent NumPy city/interval weighted-moment resampling from final rows.

No project analysis module is imported; no fitted object is loaded or modified.
"""
from pathlib import Path
import hashlib,json,sys
import numpy as np,pandas as pd
B=Path('/Users/apple/Downloads/RS revision 1/repair_20261029');S=B/'pipeline/repaired/outputs/grl_deepening_2026';O=Path('/Users/apple/Downloads/RS revision 1/continuation_20261029/science/claims_audit')
sources={};checks=[];rows=[]
def load(p):
 sources[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
 return pd.read_parquet(p) if p.suffix=='.parquet' else pd.read_csv(p)
def matrix(f,cities,events,suffix=''):
 e=np.column_stack([f['source_core'+suffix]-f['target_core'+suffix],f['source_ring'+suffix]-f['target_ring'+suffix],f['pred_core'+suffix]-f['target_core'+suffix],f['pred_ring'+suffix]-f['target_ring'+suffix]])
 v=np.column_stack([np.ones(len(e)),e,e*e,e[:,0]*e[:,1],e[:,2]*e[:,3]])
 c=np.array([cities.index(str(x)) for x in f.uc_id]);t=np.array([events.index(int(x)) for x in f.event_time_id]);A=np.zeros((len(cities),len(events),11));np.add.at(A,(c,t),v)
 return A.reshape(-1,11)
def summary(v):
 n=v[0];mu=v[1:5]/n;ms=v[5:9]/n;cross=v[9:11]/n;var=ms-mu*mu;cov=cross-np.array([mu[0]*mu[1],mu[2]*mu[3]])
 raw=ms[0]+ms[1]-2*cross[0];harm=ms[2]+ms[3]-2*cross[1];vg=var[0]+var[1]-var[2]-var[3];bg=(mu[0]-mu[1])**2-(mu[2]-mu[3])**2;cp=2*(cov[0]-cov[1]);gain=raw-harm
 assert abs(vg+bg-cp-gain)<1e-10
 return dict(component_variance_gain_k2=vg,differential_bias_gain_k2=bg,covariance_loss_penalty_k2=cp,net_downstream_mse_gain_k2=gain,net_downstream_mse_gain_fraction=gain/raw,core_rmse_reduction_fraction=1-np.sqrt(ms[2]/ms[0]),ring_rmse_reduction_fraction=1-np.sqrt(ms[3]/ms[1]),anomaly_rmse_reduction_fraction=1-np.sqrt(harm/raw),corrected_contrast_rmse_K=np.sqrt(harm),net_contrast_mse_gain_K2=gain)

for year,sub,hn,tn,sn in [(2026,'goes18_goes19_metric_harmonization','validation_2026_hourly_predictions.parquet','validation_2026_transition_predictions.parquet','downstream_metric_framework/mse_budget_2026_bootstrap_summary.csv'),(2021,'goes17_goes16_external_metric','validation_2021_hourly_predictions.parquet','validation_2021_transition_predictions.parquet','goes17_goes16_external_metric/validation_2021_bootstrap_summary.csv')]:
 h=load(S/sub/hn);t=load(S/sub/tn);expected=load(S/sn);cities=sorted(str(x) for x in h.uc_id.unique());events=sorted(int(x) for x in h.event_time_id.unique())
 frames={'hourly':matrix(h,cities,events),'transition':matrix(t,cities,events,'_transition')};draws={k:[] for k in frames};rng=np.random.default_rng(20260810)
 for i in range(5000):
  # Integer indices preserve the original random uniform choices while giving an
  # independent explicit multiplicity representation and moment implementation.
  cw=np.bincount(rng.choice(len(cities),len(cities),replace=True),minlength=len(cities));ew=np.bincount(rng.choice(len(events),len(events),replace=True),minlength=len(events));w=np.outer(cw,ew).ravel()
  for scope,A in frames.items():draws[scope].append(summary(w@A))
 for scope,dd in draws.items():
  dd=pd.DataFrame(dd)
  for metric in dd:
   e=expected[expected.scope.eq(scope)&expected.metric.eq(metric)]
   if e.empty:continue
   e=e.iloc[0];a=np.array([dd[metric].mean(),*np.quantile(dd[metric],[.025,.975])]);b=np.array([e.estimate,e.ci95_low,e.ci95_high]);ok=np.allclose(a,b,atol=1e-10,rtol=1e-10)
   checks.append(dict(name=f'{year}/{scope}/{metric}',passed=bool(ok),max_abs_difference=float(abs(a-b).max())))
   rows.append(dict(year=year,scope=scope,metric=metric,bootstrap_mean=float(a[0]),ci95_low=float(a[1]),ci95_high=float(a[2]),draws=5000))
 # RMSE interval is directly evaluated per draw, distinct from MSE-gain percent.
 for scope,dd in draws.items():
  a=np.quantile(pd.DataFrame(dd).anomaly_rmse_reduction_fraction,[.025,.975]);rows.append(dict(year=year,scope=scope,metric='derived_RMSE_reduction_percent',bootstrap_mean=float(pd.DataFrame(dd).anomaly_rmse_reduction_fraction.mean()*100),ci95_low=float(a[0]*100),ci95_high=float(a[1]*100),draws=5000))

Q=B/'auxiliary/quality/results';rec=load(Q/'recommended_common_daily_hourly.parquet');strict=load(Q/'strict_common_daily_hourly.parquet');expected=load(Q/'paired_crossed_bootstrap_comparison_summary.csv');cities=sorted(str(x) for x in rec.uc_id.unique());events=sorted(int(x) for x in rec.event_time_id.unique());A=matrix(rec,cities,events);C=matrix(strict,cities,events);rng=np.random.default_rng(20260810);diff=[]
for i in range(5000):
 cw=rng.multinomial(len(cities),np.full(len(cities),1/len(cities)));ew=rng.multinomial(len(events),np.full(len(events),1/len(events)));w=np.outer(cw,ew).ravel();a=summary(w@A);c=summary(w@C);diff.append({m:c[m]-a[m] for m in ['corrected_contrast_rmse_K','net_contrast_mse_gain_K2']})
dd=pd.DataFrame(diff)
for metric in dd:
 e=expected[expected.level.eq('hourly')&expected.comparison.eq('quality_on_common_daily_support')&expected.metric.eq(metric)].iloc[0];a=np.quantile(dd[metric],[.025,.975]);b=np.array([e.lower_95,e.upper_95]);checks.append(dict(name='paired quality/'+metric,passed=bool(np.allclose(a,b,atol=1e-10,rtol=1e-10)),max_abs_difference=float(abs(a-b).max())));rows.append(dict(year=2026,scope='quality_common_daily_three_cities',metric=metric,bootstrap_mean=float(dd[metric].mean()),ci95_low=float(a[0]),ci95_high=float(a[1]),draws=5000))
out=dict(status='PASS' if all(x['passed'] for x in checks) else 'FAIL',checks=checks,input_hashes=sources,command='/usr/bin/python3 '+str(Path(__file__)),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='10,000 independently regenerated main crossed city-interval draws (5,000 each year, both hourly/transition moments) and5,000 independently regenerated paired strict-quality draws; fitted models held fixed; corrected predictions retained as inputs.',limitations='No native re-extraction, model refitting or model-selection uncertainty is included.')
(O/'independent_bootstrap_results.json').write_text(json.dumps(out,indent=2));pd.DataFrame(rows).to_csv(O/'independent_bootstrap_summary.csv',index=False);print(json.dumps(out,indent=2));
if out['status']!='PASS':raise SystemExit(1)
