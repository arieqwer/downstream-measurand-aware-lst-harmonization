from pathlib import Path
import os
PACKAGE_ROOT=Path(__file__).resolve().parents[2]
NATIVE_WORKSPACE=Path(os.environ.get("LST_NATIVE_WORKSPACE",str(PACKAGE_ROOT/"data/native_workspace"))).resolve()
import json,sys,hashlib
import numpy as np,pandas as pd,requests,xml.etree.ElementTree as ET
sys.path.insert(0,str(PACKAGE_ROOT/'scripts'))
sys.path.append(str(PACKAGE_ROOT/'scripts'))
import joblib
from train_goes18_goes19_metric_harmonization import predict_hourly
B=NATIVE_WORKSPACE/'auxiliary/native/cloud8';S=Path(os.environ.get('LST_REPRODUCTION_OUTPUT',str(PACKAGE_ROOT/'outputs/reproduced')))/'repaired'
D=pd.read_csv(B/'results/native_city_screening.csv',dtype={'uc_id':str});old=[]
K=['uc_id','event_year','event_step8','event_time_id','local_date','target_hour_from_sunset']
for label,di in [('source','goes19_2026_metric_holdout'),('target','goes18_2026_metric_holdout')]:
 d=pd.read_parquet(S/'data'/di/'goes_sunset_hourly.parquet');d.uc_id=d.uc_id.astype(str);keys=D[D.bucket.eq('noaa-goes19' if label=='source' else 'noaa-goes18')].source_key.unique();d=d[d.source_key.isin(keys)].copy();old.append(d[K+['source_key','scan_time_utc']].rename(columns={'source_key':label+'_key','scan_time_utc':label+'_scan'}))
pairs=old[0].merge(old[1],on=K,validate='one_to_one');pairs['gap_seconds']=abs(pd.to_datetime(pairs.source_scan,format='mixed',utc=True)-pd.to_datetime(pairs.target_scan,format='mixed',utc=True)).dt.total_seconds();pairs=pairs[pairs.gap_seconds<60]
pred=pd.read_parquet(S/'outputs/grl_deepening_2026/goes18_goes19_metric_harmonization/validation_2026_hourly_predictions.parquet');pred.uc_id=pred.uc_id.astype(str);GEO=['lat','lon','vza_target','vza_source','vza_difference','vza_mean'];model=joblib.load(S/'outputs/grl_deepening_2026/goes18_goes19_metric_harmonization/frozen_metric_aware_model.joblib')
A=K.copy();A.remove('local_date');pairs=pairs.merge(pred[A+GEO],on=A,validate='many_to_one');data={}
for screen in ['recommended','strict_DQF0','ACM_clear','ACM_clear_buffer1','ACM_clear_buffer2']:
 f=pairs.copy()
 for side,bucket in [('source','noaa-goes19'),('target','noaa-goes18')]:
  for unit in ['core','ring']:
   r=D[(D.screen==screen)&(D.bucket==bucket)&(D.unit==unit)][['uc_id','source_key','n','mean_K']].rename(columns={'source_key':side+'_key','n':side+'_'+unit+'_n','mean_K':side+'_'+unit})
   f=f.merge(r,on=['uc_id',side+'_key'],validate='one_to_one')
 valid=np.ones(len(f),bool)
 for side in ['source','target']:
  for u,minimum in [('core',3),('ring',10)]:valid&=f[f'{side}_{u}_n'].ge(minimum)&f[f'{side}_{u}'].between(180,380)
 f['eligible']=valid;f['source_anomaly']=f.source_core-f.source_ring;f['target_anomaly']=f.target_core-f.target_ring;f['pred_core']=predict_hourly(model['hourly']['core'],f);f['pred_ring']=predict_hourly(model['hourly']['ring'],f);data[screen]=f
pd.concat([f.assign(screen=s) for s,f in data.items()]).to_csv(B/'results/native_cloud_paired_rows.csv',index=False)

def cov(a,b):return float(np.mean((a-a.mean())*(b-b.mean())))
def stats(f):
 if len(f)<1:return {'n':0}
 a=f.source_core-f.target_core;b=f.source_ring-f.target_ring;c=f.pred_core-f.target_core;d=f.pred_ring-f.target_ring
 vg=float(a.var(ddof=0)+b.var(ddof=0)-c.var(ddof=0)-d.var(ddof=0));bg=float((a.mean()-b.mean())**2-(c.mean()-d.mean())**2);cp=2*(cov(a,b)-cov(c,d));gain=float(np.mean((a-b)**2)-np.mean((c-d)**2));assert abs(gain-vg-bg+cp)<1e-10
 return dict(n=len(f),cities=f.uc_id.nunique(),days=f.local_date.nunique(),max_gap_seconds=float(f.gap_seconds.max()),core_rmse_raw=float(np.sqrt(np.mean(a*a))),core_rmse_corrected=float(np.sqrt(np.mean(c*c))),ring_rmse_raw=float(np.sqrt(np.mean(b*b))),ring_rmse_corrected=float(np.sqrt(np.mean(d*d))),contrast_rmse_raw=float(np.sqrt(np.mean((a-b)**2))),contrast_rmse_corrected=float(np.sqrt(np.mean((c-d)**2))),variance_gain=vg,bias_gain=bg,covariance_penalty=cp,net_contrast_MSE_gain=gain)
rows=[]
for s,f in data.items():
 rows.append(dict(screen=s,support='native_screen_eligible',**stats(f[f.eligible])))
 if s!='recommended':
  common=f.loc[f.eligible,K].merge(data['recommended'].loc[data['recommended'].eligible,K],on=K,validate='one_to_one')
  for name in ['recommended',s]:
   z=data[name].merge(common,on=K,validate='one_to_one');rows.append(dict(screen=name,support='matched_to_'+s,**stats(z)))
pd.DataFrame(rows).to_csv(B/'results/native_cloud_sensitivity.csv',index=False);print(pd.DataFrame(rows).to_string(index=False))
# Metadata reasoncountsand caveats. Countsaggregated acrosscore/ringandtwotimestamps;citymasksareseparatemetrics,notindependentpixels.
q=pd.read_csv(B/'results/native_PQI_reasons.csv');r=q.groupby(['scene_label','DQF'],as_index=False).sum(numeric_only=True);r.to_csv(B/'results/native_PQI_reasons_aggregated.csv',index=False)

print("DONE_CLOUD8_QUANT",len(rows),"sensitivityrecords",flush=True)
